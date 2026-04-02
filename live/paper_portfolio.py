"""
Portfolio state management, risk sizing, position closing, and DB logging
for the multi-symbol multi-strategy paper trading system.

Each (strategy, symbol) pair gets an isolated $1,000 allocation.
P&L is tracked per slot independently.
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
SLOT_BALANCE = 1000.0  # $1,000 per (strategy, symbol) pair
DD_CIRCUIT_BREAKER = 0.70  # stop slot entries below 70% of SLOT_BALANCE
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
    return {"allocations": _init_allocations(), "positions": {}, "pending": {}}


def _init_allocations():
    """Create $1,000 slot for every (strategy, symbol) combination."""
    from config.symbols import PAPER_SYMBOLS
    allocs = {}
    for sym in PAPER_SYMBOLS:
        allocs[f"dual_thrust_{sym}"] = SLOT_BALANCE
        allocs[f"asia_breakout_{sym}"] = SLOT_BALANCE
        allocs[f"rsi2_{sym}"] = SLOT_BALANCE
    allocs["pairs_BTCUSDT+ETHUSDT"] = SLOT_BALANCE
    return allocs


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


def _alloc_key(strategy, symbol):
    """Allocation key for a (strategy, symbol) slot."""
    return f"{strategy}_{symbol}"


def _alloc_key_from_pos(pos_key):
    """Derive allocation key from position key.
    dt_BTCUSDT_london -> dt_BTCUSDT
    ab_BTCUSDT -> ab_BTCUSDT
    rsi2_BTCUSDT -> rsi2_BTCUSDT
    pairs_BTCETH -> pairs_BTCETH
    """
    parts = pos_key.split("_")
    if parts[0] == "dt" and len(parts) == 3:
        return f"{parts[0]}_{parts[1]}"
    return pos_key


def get_slot_balance(state, strategy, symbol):
    """Get current balance for a (strategy, symbol) slot.
    Creates the slot with SLOT_BALANCE if it doesn't exist yet.
    """
    allocs = state.setdefault("allocations", {})
    key = _alloc_key(strategy, symbol)
    if key not in allocs:
        allocs[key] = SLOT_BALANCE
    return allocs[key]


def total_balance(state):
    """Sum of all slot allocations."""
    return sum(state.get("allocations", {}).values())


def total_exposure(state):
    """Sum of all open position sizes."""
    return sum(p.get("position_size", 0) for p in state["positions"].values())


def log_trade(strategy, symbol, session, direction, entry, exit_p,
              stop, pnl_pct, pnl_dollar, reason, slot_bal):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO trades (timestamp, strategy, symbol, session, direction, "
        "entry_price, exit_price, stop_price, pnl_pct, pnl_dollar, "
        "reason, balance_after) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), strategy, symbol, session,
         "LONG" if direction == 1 else "SHORT",
         entry, exit_p, stop, pnl_pct, pnl_dollar, reason, slot_bal))
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


def can_open_position(state, strategy, symbol):
    """Check if a (strategy, symbol) slot can open a position."""
    slot_bal = get_slot_balance(state, strategy, symbol)
    if slot_bal < SLOT_BALANCE * DD_CIRCUIT_BREAKER:
        ps(f"SKIP: {strategy}_{symbol} circuit breaker "
           f"(${slot_bal:.2f} < ${SLOT_BALANCE * DD_CIRCUIT_BREAKER:.0f})")
        return False
    return True


def compute_position_size(slot_balance, risk_pct, stop_pct):
    """Position size from slot balance, risk amount, and stop distance."""
    risk_amt = slot_balance * risk_pct
    size = risk_amt / (stop_pct / 100)
    max_size = slot_balance * MAX_LEVERAGE
    return min(size, max_size)


def close_position(state, pos_key, exit_price, reason):
    """Close a single-leg position and update slot allocation."""
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

    alloc_key = _alloc_key_from_pos(pos_key)
    allocs = state.setdefault("allocations", {})
    old_bal = allocs.get(alloc_key, SLOT_BALANCE)
    allocs[alloc_key] = old_bal + net_pnl
    pnl_pct = (net_pnl / old_bal * 100) if old_bal > 0 else 0

    dir_str = "LONG" if direction == 1 else "SHORT"
    ps(f"[{strategy}] CLOSED {dir_str} {symbol} {reason}: "
       f"Exit ${exit_price:.4f}, P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
       f"Slot ${allocs[alloc_key]:.2f}")

    log_trade(strategy, symbol, session, direction, entry, exit_price,
              pos.get("stop_price", 0), pnl_pct, net_pnl, reason,
              allocs[alloc_key])

    del state["positions"][pos_key]


def close_pairs_position(state, pos_key, btc_price, eth_price, reason):
    """Close a pairs trade (two legs) and update slot allocation."""
    pos = state["positions"][pos_key]
    direction = pos["direction"]
    pos_size = pos["position_size"]
    half_size = pos_size / 2

    btc_pnl_raw = direction * (btc_price - pos["btc_entry"]) / pos["btc_entry"]
    eth_pnl_raw = -direction * (eth_price - pos["eth_entry"]) / pos["eth_entry"]
    fee_cost = (TAKER_FEE + SLIPPAGE) * 2
    net_pnl = half_size * (btc_pnl_raw - fee_cost) + half_size * (eth_pnl_raw - fee_cost)

    alloc_key = _alloc_key_from_pos(pos_key)
    allocs = state.setdefault("allocations", {})
    old_bal = allocs.get(alloc_key, SLOT_BALANCE)
    allocs[alloc_key] = old_bal + net_pnl
    pnl_pct = (net_pnl / old_bal * 100) if old_bal > 0 else 0

    ps(f"[pairs] CLOSED BTC/ETH {reason}: "
       f"BTC ${btc_price:.2f} ETH ${eth_price:.2f}, "
       f"P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
       f"Slot ${allocs[alloc_key]:.2f}")

    log_trade("pairs", "BTCUSDT+ETHUSDT", "", direction,
              pos["btc_entry"], btc_price, 0,
              pnl_pct, net_pnl, reason, allocs[alloc_key])

    del state["positions"][pos_key]


def print_status(state):
    """Print full portfolio status."""
    allocs = state.get("allocations", {})
    total = sum(allocs.values()) if allocs else 0
    active_slots = len(allocs)
    ps(f"Total balance: ${total:.2f} across {active_slots} slots")
    ps(f"Open positions: {len(state['positions'])}")
    ps(f"Pending signals: {len(state.get('pending', {}))}")
    ps(f"Total exposure: ${total_exposure(state):.2f}")

    for key, pos in state["positions"].items():
        strat = pos["strategy"]
        sym = pos.get("symbol", "")
        d = "LONG" if pos.get("direction", 0) == 1 else "SHORT"
        entry = pos.get("entry_price", pos.get("btc_entry", 0))
        akey = _alloc_key_from_pos(key)
        slot_bal = allocs.get(akey, SLOT_BALANCE)
        ps(f"  [{strat}] {key}: {d} {sym} entry=${entry:.4f} "
           f"size=${pos.get('position_size', 0):.0f} "
           f"slot=${slot_bal:.2f}")

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
