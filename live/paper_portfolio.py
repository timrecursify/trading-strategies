"""
Portfolio state management, risk sizing, position closing, and DB logging
for the multi-symbol multi-strategy paper trading system.
"""

import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

STATE_FILE = "paper_state_v2.json"
TRADE_LOG = "paper_trades_v2.db"

TAKER_FEE = 0.0004
SLIPPAGE = 0.0002  # conservative for altcoins
STARTING_BALANCE = 200000.0
MAX_EXPOSURE_MULT = 20
MAX_POSITIONS_PER_SYMBOL = 3
DD_CIRCUIT_BREAKER = 0.70  # stop new entries below 70% of starting balance
RISK_PCT = 0.02
MAX_LEVERAGE = 10


def ps(msg):
    """Print timestamped message and flush."""
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def load_state():
    """Load state from JSON file, or initialize fresh state."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            ps(f"ERROR: state file corrupt: {e}")
            sys.exit(1)
    return {"balance": STARTING_BALANCE, "positions": {}, "pending": {}}


def save_state(state):
    """Atomic write: write to temp file, then rename."""
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.rename(tmp, STATE_FILE)


def init_db():
    """Create trade log tables if they don't exist."""
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, strategy TEXT, symbol TEXT, session TEXT,
            direction TEXT, entry_price REAL, exit_price REAL,
            stop_price REAL, pnl_pct REAL, pnl_dollar REAL,
            reason TEXT, balance_after REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, strategy TEXT, symbol TEXT, session TEXT,
            balance REAL, detail TEXT, action TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_trade(strategy, symbol, session, direction, entry, exit_p,
              stop, pnl_pct, pnl_dollar, reason, balance):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO trades (timestamp, strategy, symbol, session, direction, "
        "entry_price, exit_price, stop_price, pnl_pct, pnl_dollar, "
        "reason, balance_after) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), strategy, symbol, session,
         "LONG" if direction == 1 else "SHORT",
         entry, exit_p, stop, pnl_pct, pnl_dollar, reason, balance))
    conn.commit()
    conn.close()


def log_daily(strategy, symbol, session, balance, detail, action):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO daily_log (timestamp, strategy, symbol, session, "
        "balance, detail, action) VALUES (?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), strategy, symbol,
         session, balance, detail, action))
    conn.commit()
    conn.close()


def total_exposure(state):
    """Sum of all open position sizes."""
    return sum(p.get("position_size", 0) for p in state["positions"].values())


def can_open_position(state, symbol):
    """Check portfolio-level and per-symbol limits."""
    if state["balance"] < STARTING_BALANCE * DD_CIRCUIT_BREAKER:
        ps(f"SKIP: circuit breaker active (balance ${state['balance']:.2f})")
        return False
    if total_exposure(state) >= state["balance"] * MAX_EXPOSURE_MULT:
        ps(f"SKIP: exposure cap reached")
        return False
    sym_count = sum(
        1 for p in state["positions"].values()
        if p.get("symbol") == symbol
    )
    if sym_count >= MAX_POSITIONS_PER_SYMBOL:
        ps(f"SKIP: max positions for {symbol}")
        return False
    return True


def compute_position_size(balance, risk_pct, stop_pct):
    """Position size from risk amount and stop distance."""
    risk_amt = balance * risk_pct
    size = risk_amt / (stop_pct / 100)
    max_size = balance * MAX_LEVERAGE
    return min(size, max_size)


def close_position(state, pos_key, exit_price, reason):
    """Close a single-leg position and update balance."""
    pos = state["positions"][pos_key]
    direction = pos["direction"]
    entry = pos.get("avg_entry_price", pos["entry_price"])
    pos_size = pos["position_size"]
    strategy = pos["strategy"]
    symbol = pos["symbol"]
    session = pos.get("session", "")

    raw_pnl_pct = direction * (exit_price - entry) / entry
    fee_cost = (TAKER_FEE + SLIPPAGE) * 2
    net_pnl = pos_size * (raw_pnl_pct - fee_cost)

    state["balance"] += net_pnl
    prev_bal = state["balance"] - net_pnl
    pnl_pct = (net_pnl / prev_bal * 100) if prev_bal > 0 else 0

    dir_str = "LONG" if direction == 1 else "SHORT"
    ps(f"[{strategy}] CLOSED {dir_str} {symbol} {reason}: "
       f"Exit ${exit_price:.4f}, P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
       f"Balance ${state['balance']:.2f}")

    log_trade(strategy, symbol, session, direction, entry, exit_price,
              pos.get("stop_price", 0), pnl_pct, net_pnl, reason,
              state["balance"])

    del state["positions"][pos_key]


def close_pairs_position(state, pos_key, btc_price, eth_price, reason):
    """Close a pairs trade (two legs) and update balance."""
    pos = state["positions"][pos_key]
    direction = pos["direction"]
    pos_size = pos["position_size"]
    half_size = pos_size / 2

    btc_pnl_raw = direction * (btc_price - pos["btc_entry"]) / pos["btc_entry"]
    eth_pnl_raw = -direction * (eth_price - pos["eth_entry"]) / pos["eth_entry"]
    fee_cost = (TAKER_FEE + SLIPPAGE) * 2
    net_pnl = half_size * (btc_pnl_raw - fee_cost) + half_size * (eth_pnl_raw - fee_cost)

    state["balance"] += net_pnl
    prev_bal = state["balance"] - net_pnl
    pnl_pct = (net_pnl / prev_bal * 100) if prev_bal > 0 else 0

    ps(f"[pairs] CLOSED BTC/ETH {reason}: "
       f"BTC ${btc_price:.2f} ETH ${eth_price:.2f}, "
       f"P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
       f"Balance ${state['balance']:.2f}")

    log_trade("pairs", "BTCUSDT+ETHUSDT", "", direction,
              pos["btc_entry"], btc_price, 0,
              pnl_pct, net_pnl, reason, state["balance"])

    del state["positions"][pos_key]


def print_status(state):
    """Print full portfolio status."""
    ps(f"Balance: ${state['balance']:.2f}")
    ps(f"Open positions: {len(state['positions'])}")
    ps(f"Pending signals: {len(state.get('pending', {}))}")
    ps(f"Total exposure: ${total_exposure(state):.2f}")

    for key, pos in state["positions"].items():
        strat = pos["strategy"]
        sym = pos.get("symbol", "")
        d = "LONG" if pos.get("direction", 0) == 1 else "SHORT"
        entry = pos.get("entry_price", pos.get("btc_entry", 0))
        ps(f"  [{strat}] {key}: {d} {sym} entry=${entry:.4f} "
           f"size=${pos.get('position_size', 0):.0f}")

    conn = sqlite3.connect(TRADE_LOG)
    try:
        trades = conn.execute(
            "SELECT timestamp, strategy, symbol, direction, entry_price, "
            "exit_price, pnl_pct, pnl_dollar, reason "
            "FROM trades ORDER BY id DESC LIMIT 10"
        ).fetchall()
    except sqlite3.OperationalError:
        trades = []
    conn.close()

    if trades:
        ps("Recent trades:")
        for t in trades:
            print(f"  {t[0][:16]} [{t[1]}] {t[2]} {t[3]} "
                  f"E:${t[4]:.4f} X:${t[5]:.4f} "
                  f"P&L:{t[6]:+.2f}% ${t[7]:+.2f} ({t[8]})")
