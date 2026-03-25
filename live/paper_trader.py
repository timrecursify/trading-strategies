"""
Paper Trading Bot — ETH Dual Thrust Strategy
Connects to Binance Futures Testnet for realistic paper trading.
Runs via cron: entry scan at 07:00 UTC, exit at 16:00 UTC.

Strategy: Dual Thrust N=3, K=0.5, 1% stop, SMA200 filter
"""

import json
import sqlite3
import urllib.request
import time
import os
import sys
from datetime import datetime, timezone, timedelta

# === CONFIG ===
SYMBOL = "ETHUSDT"
N_DAYS = 3           # lookback for Dual Thrust range
K_MULT = 0.5         # breakout multiplier
STOP_PCT = 1.0       # stop loss %
SMA_PERIOD = 200     # regime filter
RISK_PCT = 0.02      # 2% risk per trade
MAX_LEVERAGE = 10
SCAN_INTERVAL = 60   # check every 60 seconds during entry window
ENTRY_START_H = 7    # 07:00 UTC
EXIT_H = 16          # 16:00 UTC

# Binance API (public, no key needed for market data)
BASE_URL = "https://fapi.binance.com"

# Paper trading state file
STATE_FILE = "paper_state.json"
TRADE_LOG = "paper_trades.db"


def fetch_json(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def get_daily_candles(symbol, limit=210):
    """Fetch daily candles from Binance."""
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval=1d&limit={limit}"
    data = fetch_json(url)
    days = []
    for k in data:
        days.append({
            "open_time": int(k[0]),
            "open": float(k[1]), "high": float(k[2]),
            "low": float(k[3]), "close": float(k[4]),
            "volume": float(k[5]),
        })
    return days


def get_current_price(symbol):
    url = f"{BASE_URL}/fapi/v1/ticker/price?symbol={symbol}"
    data = fetch_json(url)
    return float(data["price"])


def compute_sma(closes, period):
    if len(closes) < period:
        return sum(closes) / len(closes)
    return sum(closes[-period:]) / period


def compute_dual_thrust_levels(days, n, k):
    """Compute buy/sell triggers from prior N days."""
    if len(days) < n + 1:
        return None, None, None

    recent = days[-(n+1):-1]  # prior N days (not including today)
    hh = max(d["high"] for d in recent)
    hc = max(d["close"] for d in recent)
    lc = min(d["close"] for d in recent)
    ll = min(d["low"] for d in recent)

    rng = max(hh - lc, hc - ll)
    today_open = days[-1]["open"]

    buy_trigger = today_open + k * rng
    sell_trigger = today_open - k * rng
    return buy_trigger, sell_trigger, rng


def init_trade_log():
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT, symbol TEXT, direction TEXT,
            entry_price REAL, exit_price REAL, stop_price REAL,
            pnl_pct REAL, reason TEXT, status TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            date TEXT PRIMARY KEY, balance REAL,
            trigger_buy REAL, trigger_sell REAL,
            sma200 REAL, price_at_check REAL,
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
        "in_position": False,
        "direction": 0,
        "entry_price": 0,
        "stop_price": 0,
        "position_size": 0,
        "entry_time": "",
    }


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def log_trade(symbol, direction, entry, exit_p, stop, pnl_pct, reason, status):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT INTO trades (timestamp, symbol, direction, entry_price, exit_price, "
        "stop_price, pnl_pct, reason, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).isoformat(), symbol,
         "LONG" if direction == 1 else "SHORT",
         entry, exit_p, stop, pnl_pct, reason, status))
    conn.commit()
    conn.close()


def log_daily(date_str, balance, buy_trig, sell_trig, sma, price, action):
    conn = sqlite3.connect(TRADE_LOG)
    conn.execute(
        "INSERT OR REPLACE INTO daily_log VALUES (?, ?, ?, ?, ?, ?, ?)",
        (date_str, balance, buy_trig, sell_trig, sma, price, action))
    conn.commit()
    conn.close()


def print_status(msg):
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"[{ts}] {msg}")
    sys.stdout.flush()


# === MAIN ACTIONS ===

def action_scan():
    """Called at 07:00 UTC. Compute levels, start scanning for entry."""
    state = load_state()

    if state["in_position"]:
        print_status("Already in position, skipping entry scan.")
        return

    # Fetch daily candles
    days = get_daily_candles(SYMBOL, 210)
    if len(days) < SMA_PERIOD + N_DAYS:
        print_status(f"Not enough data ({len(days)} days). Need {SMA_PERIOD + N_DAYS}.")
        return

    # SMA200 filter
    closes = [d["close"] for d in days]
    sma = compute_sma(closes, SMA_PERIOD)
    current_price = get_current_price(SYMBOL)

    if current_price < sma:
        print_status(f"Price ${current_price:.2f} below SMA200 ${sma:.2f}. No trade today.")
        log_daily(datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                  state["balance"], 0, 0, sma, current_price, "SKIP_SMA")
        return

    # Compute Dual Thrust levels
    buy_trig, sell_trig, rng = compute_dual_thrust_levels(days, N_DAYS, K_MULT)
    if buy_trig is None:
        print_status("Cannot compute triggers.")
        return

    print_status(f"Dual Thrust levels: BUY>{buy_trig:.2f} SELL<{sell_trig:.2f} "
                 f"Range={rng:.2f} SMA200={sma:.2f} Price={current_price:.2f}")

    # Scan for breakout until EXIT_H
    end_time = datetime.now(timezone.utc).replace(hour=EXIT_H, minute=0, second=0)
    entered = False

    while datetime.now(timezone.utc) < end_time:
        price = get_current_price(SYMBOL)

        if price > buy_trig:
            # LONG breakout
            direction = 1
            entry_price = price
            stop = entry_price * (1 - STOP_PCT / 100)
            entered = True
            print_status(f"LONG ENTRY at ${entry_price:.2f} (trigger ${buy_trig:.2f})")
            break

        if price < sell_trig:
            # SHORT breakout (only if below SMA — already checked above, so skip shorts)
            # For simplicity with SMA200 filter, we only go long
            pass

        time.sleep(SCAN_INTERVAL)

    if not entered:
        print_status("No breakout by exit time. No trade today.")
        log_daily(datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                  state["balance"], buy_trig, sell_trig, sma, current_price, "NO_BREAKOUT")
        return

    # Position sizing
    stop_dist = STOP_PCT / 100
    risk_amt = state["balance"] * RISK_PCT
    position_size = risk_amt / stop_dist
    if position_size / state["balance"] > MAX_LEVERAGE:
        position_size = state["balance"] * MAX_LEVERAGE

    state["in_position"] = True
    state["direction"] = direction
    state["entry_price"] = entry_price
    state["stop_price"] = stop
    state["position_size"] = position_size
    state["entry_time"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    log_daily(datetime.now(timezone.utc).strftime("%Y-%m-%d"),
              state["balance"], buy_trig, sell_trig, sma, entry_price,
              f"ENTRY_LONG@{entry_price:.2f}")

    print_status(f"Position: LONG ${position_size:.0f} @ ${entry_price:.2f}, "
                 f"Stop ${stop:.2f}, Risk ${risk_amt:.2f}")


def action_monitor():
    """Called periodically while in position. Check stop loss."""
    state = load_state()
    if not state["in_position"]:
        return

    price = get_current_price(SYMBOL)
    direction = state["direction"]
    stop = state["stop_price"]

    if direction == 1 and price <= stop:
        close_position(state, price, "STOP")
    elif direction == -1 and price >= stop:
        close_position(state, price, "STOP")
    else:
        pnl_pct = direction * (price - state["entry_price"]) / state["entry_price"] * 100
        print_status(f"Monitoring: Price ${price:.2f}, Entry ${state['entry_price']:.2f}, "
                     f"P&L {pnl_pct:+.2f}%, Stop ${stop:.2f}")


def action_exit():
    """Called at 16:00 UTC. Close any open position."""
    state = load_state()
    if not state["in_position"]:
        print_status("No position to close.")
        return

    price = get_current_price(SYMBOL)
    close_position(state, price, "TIME_EXIT")


def close_position(state, exit_price, reason):
    direction = state["direction"]
    entry = state["entry_price"]
    pos_size = state["position_size"]

    raw_pnl_pct = direction * (exit_price - entry) / entry
    fee_cost = 0.0004 * 2 + 0.0001 * 2  # taker + slippage
    net_pnl = pos_size * (raw_pnl_pct - fee_cost)

    state["balance"] += net_pnl
    pnl_pct = net_pnl / (state["balance"] - net_pnl) * 100

    print_status(f"CLOSED {reason}: Exit ${exit_price:.2f}, P&L ${net_pnl:+.2f} ({pnl_pct:+.2f}%), "
                 f"Balance ${state['balance']:.2f}")

    log_trade(SYMBOL, direction, entry, exit_price, state["stop_price"],
              pnl_pct, reason, "CLOSED")

    state["in_position"] = False
    state["direction"] = 0
    state["entry_price"] = 0
    state["stop_price"] = 0
    state["position_size"] = 0
    save_state(state)


def action_status():
    """Print current state."""
    state = load_state()
    print_status(f"Balance: ${state['balance']:.2f}")
    print_status(f"In position: {state['in_position']}")
    if state["in_position"]:
        price = get_current_price(SYMBOL)
        pnl = state["direction"] * (price - state["entry_price"]) / state["entry_price"] * 100
        print_status(f"Direction: {'LONG' if state['direction'] == 1 else 'SHORT'}")
        print_status(f"Entry: ${state['entry_price']:.2f}, Current: ${price:.2f}, "
                     f"P&L: {pnl:+.2f}%, Stop: ${state['stop_price']:.2f}")

    # Recent trades
    conn = sqlite3.connect(TRADE_LOG)
    trades = conn.execute(
        "SELECT timestamp, direction, entry_price, exit_price, pnl_pct, reason "
        "FROM trades ORDER BY id DESC LIMIT 10").fetchall()
    conn.close()

    if trades:
        print_status("Recent trades:")
        for t in trades:
            print(f"  {t[0][:16]} {t[1]} Entry:${t[2]:.2f} Exit:${t[3]:.2f} "
                  f"P&L:{t[4]:+.2f}% ({t[5]})")


def main():
    init_trade_log()

    if len(sys.argv) < 2:
        print("Usage: python paper_trader.py [scan|monitor|exit|status]")
        print("  scan    — Run at 07:00 UTC. Computes levels, scans for entry.")
        print("  monitor — Run every 5min while in position. Checks stop loss.")
        print("  exit    — Run at 16:00 UTC. Closes any open position.")
        print("  status  — Print current state and recent trades.")
        return

    action = sys.argv[1]
    if action == "scan":
        action_scan()
    elif action == "monitor":
        action_monitor()
    elif action == "exit":
        action_exit()
    elif action == "status":
        action_status()
    else:
        print(f"Unknown action: {action}")


if __name__ == "__main__":
    main()
