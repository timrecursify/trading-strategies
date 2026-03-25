"""
Paper Trading Bot: ETH Dual Thrust (DT + shorts + NYC)

Two sessions per day, shorts allowed below SMA200.
London: scan 07:00, exit 16:00. NYC: scan 12:00, exit 20:00.
Strategy: Dual Thrust N=3, K=0.5, 1% stop, SMA200 regime, 2% risk.
"""

import json
import sqlite3
import urllib.request
import time
import os
import sys
from datetime import datetime, timezone

# === CONFIG ===
SYMBOL = "ETHUSDT"
N_DAYS = 3
K_MULT = 0.5
STOP_PCT = 1.0
SMA_PERIOD = 200
RISK_PCT = 0.02
MAX_LEVERAGE = 10
SCAN_INTERVAL = 60

SESSIONS = {
    "london": {"entry_h": 7, "exit_h": 16},
    "nyc":    {"entry_h": 12, "exit_h": 20},
}

BASE_URL = "https://api.binance.us"
STATE_FILE = "paper_state.json"
TRADE_LOG = "paper_trades.db"

TAKER_FEE = 0.0004
SLIPPAGE_FEE = 0.0001


def fetch_json(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_daily_candles(symbol, limit=210):
    url = f"{BASE_URL}/api/v3/klines?symbol={symbol}&interval=1d&limit={limit}"
    data = fetch_json(url)
    return [{"open_time": int(k[0]), "open": float(k[1]), "high": float(k[2]),
             "low": float(k[3]), "close": float(k[4]), "volume": float(k[5])}
            for k in data]


def get_current_price(symbol):
    url = f"{BASE_URL}/api/v3/ticker/price?symbol={symbol}"
    return float(fetch_json(url)["price"])


def compute_sma(closes, period):
    if len(closes) < period:
        return sum(closes) / len(closes)
    return sum(closes[-period:]) / period


def compute_triggers(days, n, k, session_open_price):
    """Compute buy/sell triggers from prior N days and session open."""
    if len(days) < n + 1:
        return None, None, None
    recent = days[-(n+1):-1]
    hh = max(d["high"] for d in recent)
    hc = max(d["close"] for d in recent)
    lc = min(d["close"] for d in recent)
    ll = min(d["low"] for d in recent)
    rng = max(hh - lc, hc - ll)
    buy_trigger = session_open_price + k * rng
    sell_trigger = session_open_price - k * rng
    return buy_trigger, sell_trigger, rng


def init_trade_log():
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, symbol TEXT, session TEXT, direction TEXT,
            entry_price REAL, exit_price REAL, stop_price REAL,
            pnl_pct REAL, pnl_dollar REAL, reason TEXT, balance_after REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, session TEXT, balance REAL,
            trigger_buy REAL, trigger_sell REAL,
            sma200 REAL, price_at_check REAL, above_sma INTEGER,
            action TEXT
        )
    """)
    conn.commit()
    conn.close()


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {
        "balance": 1000.0,
        "positions": {},
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_trade(symbol, session, direction, entry, exit_p, stop,
              pnl_pct, pnl_dollar, reason, balance):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO trades (timestamp, symbol, session, direction, "
        "entry_price, exit_price, stop_price, pnl_pct, pnl_dollar, "
        "reason, balance_after) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), symbol, session,
         "LONG" if direction == 1 else "SHORT",
         entry, exit_p, stop, pnl_pct, pnl_dollar, reason, balance))
    conn.commit()
    conn.close()


def log_daily(session, balance, buy_t, sell_t, sma, price, above, action):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO daily_log (timestamp, session, balance, trigger_buy, "
        "trigger_sell, sma200, price_at_check, above_sma, action) "
        "VALUES (?,?,?,?,?,?,?,?,?)",
        (datetime.now(timezone.utc).isoformat(), session, balance,
         buy_t, sell_t, sma, price, 1 if above else 0, action))
    conn.commit()
    conn.close()


def ps(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


def action_scan(session_name):
    """Scan for breakout entry in the given session."""
    if session_name not in SESSIONS:
        ps(f"Unknown session: {session_name}")
        return

    sess = SESSIONS[session_name]
    entry_h = sess["entry_h"]
    exit_h = sess["exit_h"]

    state = load_state()

    if session_name in state["positions"]:
        ps(f"Already in {session_name} position, skipping.")
        return

    days = get_daily_candles(SYMBOL, 210)
    if len(days) < SMA_PERIOD + N_DAYS:
        ps(f"Not enough data ({len(days)} days).")
        return

    # SMA200 from prior day's close (no look-ahead)
    closes = [d["close"] for d in days]
    sma = compute_sma(closes[:-1], SMA_PERIOD)
    prev_close = closes[-2] if len(closes) >= 2 else closes[-1]
    above_sma = prev_close > sma

    # Get session open price (current price at session start)
    session_open = get_current_price(SYMBOL)

    # Compute triggers using session open, not daily open
    buy_trig, sell_trig, rng = compute_triggers(days, N_DAYS, K_MULT, session_open)
    if buy_trig is None:
        ps("Cannot compute triggers.")
        return

    regime = "BULLISH (longs)" if above_sma else "BEARISH (shorts)"
    ps(f"[{session_name.upper()}] {regime} | BUY>{buy_trig:.2f} SELL<{sell_trig:.2f} "
       f"Range={rng:.2f} SMA200={sma:.2f} Open={session_open:.2f}")

    # Scan for breakout
    end_time = datetime.now(timezone.utc).replace(hour=exit_h, minute=0, second=0)
    entered = False
    direction = 0
    entry_price = 0
    trigger_price = 0

    while datetime.now(timezone.utc) < end_time:
        price = get_current_price(SYMBOL)

        # Above SMA200: long breakouts only
        if above_sma and price > buy_trig:
            direction = 1
            entry_price = price
            trigger_price = buy_trig
            entered = True
            ps(f"LONG ENTRY at ${price:.2f} (trigger ${buy_trig:.2f})")
            break

        # Below SMA200: short breakouts only
        if not above_sma and price < sell_trig:
            direction = -1
            entry_price = price
            trigger_price = sell_trig
            entered = True
            ps(f"SHORT ENTRY at ${price:.2f} (trigger ${sell_trig:.2f})")
            break

        time.sleep(SCAN_INTERVAL)

    if not entered:
        ps(f"[{session_name.upper()}] No breakout by {exit_h}:00.")
        log_daily(session_name, state["balance"], buy_trig, sell_trig,
                  sma, session_open, above_sma, "NO_BREAKOUT")
        return

    # Stop from trigger price (matches backtest)
    stop = trigger_price * (1 - direction * STOP_PCT / 100)

    # Position sizing: 2% risk, 1% stop distance
    stop_dist = STOP_PCT / 100
    risk_amt = state["balance"] * RISK_PCT
    position_size = risk_amt / stop_dist
    if position_size / state["balance"] > MAX_LEVERAGE:
        position_size = state["balance"] * MAX_LEVERAGE

    state["positions"][session_name] = {
        "direction": direction,
        "entry_price": entry_price,
        "stop_price": stop,
        "trigger_price": trigger_price,
        "position_size": position_size,
        "entry_time": datetime.now(timezone.utc).isoformat(),
        "exit_h": exit_h,
    }
    save_state(state)

    dir_str = "LONG" if direction == 1 else "SHORT"
    log_daily(session_name, state["balance"], buy_trig, sell_trig,
              sma, entry_price, above_sma, f"ENTRY_{dir_str}@{entry_price:.2f}")

    ps(f"[{session_name.upper()}] {dir_str} ${position_size:.0f} @ ${entry_price:.2f}, "
       f"Stop ${stop:.2f}, Risk ${risk_amt:.2f}")


def action_monitor():
    """Check stops on all open positions."""
    state = load_state()
    if not state["positions"]:
        return

    price = get_current_price(SYMBOL)

    for session_name in list(state["positions"].keys()):
        pos = state["positions"][session_name]
        direction = pos["direction"]
        stop = pos["stop_price"]
        entry = pos["entry_price"]

        if direction == 1 and price <= stop:
            close_position(state, session_name, price, "STOP")
        elif direction == -1 and price >= stop:
            close_position(state, session_name, price, "STOP")
        else:
            pnl = direction * (price - entry) / entry * 100
            dir_str = "LONG" if direction == 1 else "SHORT"
            ps(f"[{session_name.upper()}] {dir_str} Entry:${entry:.2f} "
               f"Now:${price:.2f} P&L:{pnl:+.2f}% Stop:${stop:.2f}")


def action_exit(session_name):
    """Time exit for a specific session."""
    state = load_state()
    if session_name not in state["positions"]:
        ps(f"[{session_name.upper()}] No position to close.")
        return

    price = get_current_price(SYMBOL)
    close_position(state, session_name, price, "TIME_EXIT")


def close_position(state, session_name, exit_price, reason):
    pos = state["positions"][session_name]
    direction = pos["direction"]
    entry = pos["entry_price"]
    pos_size = pos["position_size"]

    raw_pnl_pct = direction * (exit_price - entry) / entry
    fee_cost = TAKER_FEE * 2 + SLIPPAGE_FEE * 2
    net_pnl = pos_size * (raw_pnl_pct - fee_cost)

    state["balance"] += net_pnl
    pnl_pct = net_pnl / (state["balance"] - net_pnl) * 100 if (state["balance"] - net_pnl) > 0 else 0

    dir_str = "LONG" if direction == 1 else "SHORT"
    ps(f"[{session_name.upper()}] CLOSED {dir_str} {reason}: "
       f"Exit ${exit_price:.2f}, P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
       f"Balance ${state['balance']:.2f}")

    log_trade(SYMBOL, session_name, direction, entry, exit_price,
              pos["stop_price"], pnl_pct, net_pnl, reason, state["balance"])

    del state["positions"][session_name]
    save_state(state)


def action_status():
    state = load_state()
    ps(f"Balance: ${state['balance']:.2f}")
    ps(f"Open positions: {len(state['positions'])}")

    if state["positions"]:
        price = get_current_price(SYMBOL)
        for sess, pos in state["positions"].items():
            d = pos["direction"]
            pnl = d * (price - pos["entry_price"]) / pos["entry_price"] * 100
            dir_str = "LONG" if d == 1 else "SHORT"
            ps(f"  [{sess.upper()}] {dir_str} Entry:${pos['entry_price']:.2f} "
               f"Now:${price:.2f} P&L:{pnl:+.2f}% Stop:${pos['stop_price']:.2f}")

    conn = sqlite3.connect(TRADE_LOG)
    try:
        trades = conn.execute(
            "SELECT timestamp, session, direction, entry_price, exit_price, "
            "pnl_pct, pnl_dollar, reason FROM trades ORDER BY id DESC LIMIT 10"
        ).fetchall()
    except sqlite3.OperationalError:
        trades = []
    conn.close()

    if trades:
        ps("Recent trades:")
        for t in trades:
            print(f"  {t[0][:16]} [{t[1]}] {t[2]} "
                  f"Entry:${t[3]:.2f} Exit:${t[4]:.2f} "
                  f"P&L:{t[5]:+.2f}% ${t[6]:+.2f} ({t[7]})")


def main():
    init_trade_log()

    if len(sys.argv) < 2:
        print("Usage: python paper_trader.py [command] [session]")
        print("")
        print("Commands:")
        print("  scan london   Scan for London session entry (07:00 UTC)")
        print("  scan nyc      Scan for NYC session entry (12:00 UTC)")
        print("  monitor       Check stops on all open positions")
        print("  exit london   Time exit London position (16:00 UTC)")
        print("  exit nyc      Time exit NYC position (20:00 UTC)")
        print("  status        Print balance, positions, recent trades")
        return

    action = sys.argv[1]
    session = sys.argv[2] if len(sys.argv) > 2 else None

    if action == "scan":
        if not session:
            ps("Specify session: scan london | scan nyc")
            return
        action_scan(session)
    elif action == "monitor":
        action_monitor()
    elif action == "exit":
        if not session:
            ps("Specify session: exit london | exit nyc")
            return
        action_exit(session)
    elif action == "status":
        action_status()
    else:
        print(f"Unknown action: {action}")


if __name__ == "__main__":
    main()
