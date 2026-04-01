"""
Strategy setup and tick logic for multi-symbol paper trading.

Strategies:
  1. Dual Thrust  -- session breakout (London + NYC)
  2. Asia Breakout -- Asia range breakout during London
  3. Scale-In RSI(2) -- daily mean reversion, long-only
  4. Pairs Trading -- BTC/ETH ratio mean reversion
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from live.paper_api import get_daily_candles, get_hourly_candles, get_batch_prices
from live.paper_portfolio import (
    ps, can_open_position, compute_position_size, close_position,
    close_pairs_position, log_daily, save_state, RISK_PCT,
)
from core.indicators import rsi, sma
from config.symbols import PAPER_SYMBOLS

# === Strategy Parameters ===
DT_N = 3
DT_K = 0.5
DT_STOP_PCT = 1.0
SMA_PERIOD = 200

AB_STOP_PCT = 0.5
AB_RR = 1.0

RSI2_THRESHOLD = 10
RSI2_STOP_PCT = 3.0
RSI2_MAX_HOLD = 10
RSI2_SCALE_RSI5_DROP = 5

PAIRS_WINDOW = 30
PAIRS_Z_ENTRY = 2.0
PAIRS_Z_EXIT = 0.5
PAIRS_MAX_HOLD = 10
PAIRS_MAX_LOSS_PCT = 5.0


# ============================================================
# DUAL THRUST
# ============================================================

def _dt_compute_triggers(days, n, k, session_open):
    """Compute DT buy/sell triggers from prior N days + session open."""
    if len(days) < n + 1:
        return None, None, None
    recent = days[-(n + 1):-1]
    hh = max(d["high"] for d in recent)
    hc = max(d["close"] for d in recent)
    lc = min(d["close"] for d in recent)
    ll = min(d["low"] for d in recent)
    rng = max(hh - lc, hc - ll)
    return session_open + k * rng, session_open - k * rng, rng


def setup_dual_thrust(state, session_name, prices):
    """Compute DT triggers for all symbols, store as pending signals."""
    exit_h = 16 if session_name == "london" else 20
    for symbol in PAPER_SYMBOLS:
        pos_key = f"dt_{symbol}_{session_name}"
        if pos_key in state["positions"]:
            ps(f"[DT] {symbol} {session_name}: already in position, skip")
            continue
        try:
            days = get_daily_candles(symbol, 210)
        except Exception as e:
            ps(f"[DT] {symbol}: API error fetching candles: {e}")
            continue
        if len(days) < SMA_PERIOD + DT_N:
            ps(f"[DT] {symbol}: not enough data ({len(days)} days)")
            continue

        closes = [d["close"] for d in days]
        sma_vals = sma(closes, SMA_PERIOD)
        sma200 = sma_vals[-2] if len(sma_vals) >= 2 else sma_vals[-1]
        prev_close = closes[-2]
        above_sma = prev_close > sma200

        session_open = prices.get(symbol)
        if session_open is None:
            continue
        buy_t, sell_t, rng = _dt_compute_triggers(days, DT_N, DT_K, session_open)
        if buy_t is None:
            continue

        state["pending"][pos_key] = {
            "strategy": "dual_thrust",
            "symbol": symbol,
            "session": session_name,
            "buy_trigger": buy_t,
            "sell_trigger": sell_t,
            "above_sma": above_sma,
            "sma200": sma200,
            "expires_h": exit_h,
        }
        regime = "BULL (longs)" if above_sma else "BEAR (shorts)"
        ps(f"[DT] {symbol} {session_name}: {regime} "
           f"BUY>{buy_t:.4f} SELL<{sell_t:.4f} Rng={rng:.4f} "
           f"SMA200={sma200:.4f}")
        log_daily("dual_thrust", symbol, session_name, state["balance"],
                  f"buy>{buy_t:.4f} sell<{sell_t:.4f} sma={sma200:.4f}",
                  f"SETUP_{regime.split()[0]}")


def tick_dual_thrust(state, prices):
    """Check pending DT signals against current prices."""
    now_h = datetime.now(timezone.utc).hour
    to_remove = []
    for key, sig in list(state["pending"].items()):
        if sig.get("strategy") != "dual_thrust":
            continue
        if now_h >= sig["expires_h"]:
            to_remove.append(key)
            continue
        symbol = sig["symbol"]
        price = prices.get(symbol)
        if price is None:
            continue
        if key in state["positions"]:
            to_remove.append(key)
            continue
        if not can_open_position(state, symbol):
            continue

        entered = False
        direction = 0
        trigger_price = 0
        if sig["above_sma"] and price > sig["buy_trigger"]:
            direction = 1
            trigger_price = sig["buy_trigger"]
            entered = True
        elif not sig["above_sma"] and price < sig["sell_trigger"]:
            direction = -1
            trigger_price = sig["sell_trigger"]
            entered = True

        if entered:
            stop = trigger_price * (1 - direction * DT_STOP_PCT / 100)
            pos_size = compute_position_size(
                state["balance"], RISK_PCT, DT_STOP_PCT)
            session = sig["session"]
            state["positions"][key] = {
                "strategy": "dual_thrust",
                "symbol": symbol,
                "session": session,
                "direction": direction,
                "entry_price": price,
                "stop_price": stop,
                "position_size": pos_size,
                "entry_time": datetime.now(timezone.utc).isoformat(),
            }
            to_remove.append(key)
            d = "LONG" if direction == 1 else "SHORT"
            ps(f"[DT] {d} {symbol} @ ${price:.4f} "
               f"stop=${stop:.4f} size=${pos_size:.0f}")
            log_daily("dual_thrust", symbol, session, state["balance"],
                      f"entry={price:.4f} stop={stop:.4f}",
                      f"ENTRY_{d}@{price:.4f}")

    for key in to_remove:
        state["pending"].pop(key, None)


# ============================================================
# ASIA BREAKOUT
# ============================================================

def setup_asia_breakout(state, prices):
    """Compute Asia high/low for all symbols, store as pending."""
    for symbol in PAPER_SYMBOLS:
        pos_key = f"ab_{symbol}"
        if pos_key in state["positions"]:
            continue
        try:
            candles = get_hourly_candles(symbol, 7)
        except Exception as e:
            ps(f"[AB] {symbol}: API error: {e}")
            continue
        if len(candles) < 7:
            ps(f"[AB] {symbol}: not enough hourly data")
            continue

        asia_high = max(c["high"] for c in candles)
        asia_low = min(c["low"] for c in candles)
        state["pending"][pos_key] = {
            "strategy": "asia_breakout",
            "symbol": symbol,
            "asia_high": asia_high,
            "asia_low": asia_low,
            "expires_h": 10,
        }
        ps(f"[AB] {symbol}: Asia H={asia_high:.4f} L={asia_low:.4f}")
        log_daily("asia_breakout", symbol, "london", state["balance"],
                  f"high={asia_high:.4f} low={asia_low:.4f}", "SETUP")


def tick_asia_breakout(state, prices):
    """Check pending AB signals for breakouts."""
    now_h = datetime.now(timezone.utc).hour
    to_remove = []
    for key, sig in list(state["pending"].items()):
        if sig.get("strategy") != "asia_breakout":
            continue
        if now_h >= sig["expires_h"]:
            to_remove.append(key)
            continue
        symbol = sig["symbol"]
        price = prices.get(symbol)
        if price is None:
            continue
        if key in state["positions"]:
            to_remove.append(key)
            continue
        if not can_open_position(state, symbol):
            continue

        entered = False
        direction = 0
        entry_level = 0
        if price > sig["asia_high"]:
            direction = 1
            entry_level = sig["asia_high"]
            entered = True
        elif price < sig["asia_low"]:
            direction = -1
            entry_level = sig["asia_low"]
            entered = True

        if entered:
            stop_dist = price * AB_STOP_PCT / 100
            stop = price - direction * stop_dist
            tp = price + direction * stop_dist * AB_RR
            pos_size = compute_position_size(
                state["balance"], RISK_PCT, AB_STOP_PCT)
            state["positions"][key] = {
                "strategy": "asia_breakout",
                "symbol": symbol,
                "session": "london",
                "direction": direction,
                "entry_price": price,
                "stop_price": stop,
                "tp_price": tp,
                "position_size": pos_size,
                "entry_time": datetime.now(timezone.utc).isoformat(),
            }
            to_remove.append(key)
            d = "LONG" if direction == 1 else "SHORT"
            ps(f"[AB] {d} {symbol} @ ${price:.4f} "
               f"stop=${stop:.4f} tp=${tp:.4f}")
            log_daily("asia_breakout", symbol, "london", state["balance"],
                      f"entry={price:.4f} stop={stop:.4f} tp={tp:.4f}",
                      f"ENTRY_{d}@{price:.4f}")

    for key in to_remove:
        state["pending"].pop(key, None)


# ============================================================
# SCALE-IN RSI(2)
# ============================================================

def scan_rsi2(state, prices):
    """Daily scan: enter new RSI2 positions or manage existing ones."""
    for symbol in PAPER_SYMBOLS:
        pos_key = f"rsi2_{symbol}"
        try:
            days = get_daily_candles(symbol, 10)
        except Exception as e:
            ps(f"[RSI2] {symbol}: API error: {e}")
            continue
        if len(days) < 5:
            continue
        closes = [d["close"] for d in days]
        rsi2_vals = rsi(closes, 2)
        rsi5_vals = rsi(closes, 5)
        prev_high = days[-2]["high"] if len(days) >= 2 else days[-1]["high"]
        current_rsi2 = rsi2_vals[-2] if len(rsi2_vals) >= 2 else 50
        current_rsi5 = rsi5_vals[-2] if len(rsi5_vals) >= 2 else 50

        if pos_key in state["positions"]:
            pos = state["positions"][pos_key]
            pos["prev_high"] = prev_high
            pos["entry_day"] = pos.get("entry_day", 0) + 1

            if not pos.get("scale_in_done") and current_rsi5 < pos.get("scale_in_rsi5", 100) - RSI2_SCALE_RSI5_DROP:
                price = prices.get(symbol)
                if price and price > 0:
                    old_size = pos["position_size"]
                    old_avg = pos.get("avg_entry_price", pos["entry_price"])
                    add_size = pos["intended_size"] - old_size
                    new_size = old_size + add_size
                    new_avg = (old_avg * old_size + price * add_size) / new_size
                    pos["position_size"] = new_size
                    pos["avg_entry_price"] = new_avg
                    pos["stop_price"] = new_avg * (1 - RSI2_STOP_PCT / 100)
                    pos["scale_in_done"] = True
                    ps(f"[RSI2] SCALE-IN {symbol} @ ${price:.4f} "
                       f"avg=${new_avg:.4f} size=${new_size:.0f}")
            ps(f"[RSI2] {symbol}: day {pos['entry_day']}/{RSI2_MAX_HOLD} "
               f"RSI2={current_rsi2:.1f} prevH=${prev_high:.4f}")
            continue

        if current_rsi2 >= RSI2_THRESHOLD:
            ps(f"[RSI2] {symbol}: RSI2={current_rsi2:.1f} (no signal)")
            continue
        if not can_open_position(state, symbol):
            continue
        price = prices.get(symbol)
        if not price or price <= 0:
            continue

        intended_size = compute_position_size(
            state["balance"], RISK_PCT, RSI2_STOP_PCT)
        half_size = intended_size * 0.5
        stop = price * (1 - RSI2_STOP_PCT / 100)

        state["positions"][pos_key] = {
            "strategy": "rsi2",
            "symbol": symbol,
            "direction": 1,
            "entry_price": price,
            "avg_entry_price": price,
            "stop_price": stop,
            "position_size": half_size,
            "intended_size": intended_size,
            "prev_high": prev_high,
            "entry_day": 0,
            "max_hold_days": RSI2_MAX_HOLD,
            "scale_in_done": False,
            "scale_in_rsi5": current_rsi5,
            "entry_time": datetime.now(timezone.utc).isoformat(),
        }
        ps(f"[RSI2] LONG {symbol} @ ${price:.4f} RSI2={current_rsi2:.1f} "
           f"stop=${stop:.4f} size=${half_size:.0f}/{intended_size:.0f}")
        log_daily("rsi2", symbol, "", state["balance"],
                  f"entry={price:.4f} rsi2={current_rsi2:.1f}",
                  f"ENTRY_LONG@{price:.4f}")


# ============================================================
# PAIRS TRADING
# ============================================================

def scan_pairs(state, prices):
    """Daily scan: check BTC/ETH ratio z-score for entry/update."""
    pos_key = "pairs_BTCETH"
    try:
        btc_days = get_daily_candles("BTCUSDT", 40)
        eth_days = get_daily_candles("ETHUSDT", 40)
    except Exception as e:
        ps(f"[PAIRS] API error: {e}")
        return
    if len(btc_days) < PAIRS_WINDOW + 1 or len(eth_days) < PAIRS_WINDOW + 1:
        ps(f"[PAIRS] Not enough data")
        return

    min_len = min(len(btc_days), len(eth_days))
    ratios = [
        btc_days[i]["close"] / eth_days[i]["close"]
        for i in range(min_len)
        if eth_days[i]["close"] > 0
    ]
    if len(ratios) < PAIRS_WINDOW + 1:
        return
    window = ratios[-PAIRS_WINDOW - 1:-1]
    r_mean = sum(window) / len(window)
    r_std = (sum((r - r_mean) ** 2 for r in window) / len(window)) ** 0.5
    if r_std < 1e-9:
        return
    current_ratio = ratios[-1]
    z = (current_ratio - r_mean) / r_std

    if pos_key in state["positions"]:
        pos = state["positions"][pos_key]
        pos["ratio_mean"] = r_mean
        pos["ratio_std"] = r_std
        pos["entry_day"] = pos.get("entry_day", 0) + 1
        ps(f"[PAIRS] BTC/ETH z={z:.2f} day {pos['entry_day']}/{PAIRS_MAX_HOLD} "
           f"mean={r_mean:.2f} std={r_std:.2f}")
        return

    if abs(z) <= PAIRS_Z_ENTRY:
        ps(f"[PAIRS] BTC/ETH z={z:.2f} (no signal)")
        return
    if not can_open_position(state, "BTCUSDT"):
        return

    btc_price = prices.get("BTCUSDT")
    eth_price = prices.get("ETHUSDT")
    if not btc_price or not eth_price:
        return

    direction = -1 if z > 0 else 1
    pos_size = compute_position_size(
        state["balance"], RISK_PCT, PAIRS_MAX_LOSS_PCT)

    state["positions"][pos_key] = {
        "strategy": "pairs",
        "symbol": "BTCUSDT+ETHUSDT",
        "direction": direction,
        "btc_entry": btc_price,
        "eth_entry": eth_price,
        "position_size": pos_size,
        "entry_z": z,
        "ratio_mean": r_mean,
        "ratio_std": r_std,
        "entry_day": 0,
        "max_hold_days": PAIRS_MAX_HOLD,
        "entry_time": datetime.now(timezone.utc).isoformat(),
    }
    side = "SHORT BTC + LONG ETH" if direction == -1 else "LONG BTC + SHORT ETH"
    ps(f"[PAIRS] {side} z={z:.2f} BTC=${btc_price:.2f} ETH=${eth_price:.2f} "
       f"size=${pos_size:.0f}")
    log_daily("pairs", "BTCUSDT+ETHUSDT", "", state["balance"],
              f"z={z:.2f} btc={btc_price:.2f} eth={eth_price:.2f}",
              f"ENTRY_z{z:.2f}")


# ============================================================
# MONITOR (called by tick for all open positions)
# ============================================================

def monitor_positions(state, prices):
    """Check stops, TPs, and multi-day exits for all open positions."""
    for key in list(state["positions"].keys()):
        pos = state["positions"][key]
        strategy = pos["strategy"]

        if strategy in ("dual_thrust", "asia_breakout"):
            _monitor_session_position(state, key, prices)
        elif strategy == "rsi2":
            _monitor_rsi2(state, key, prices)
        elif strategy == "pairs":
            _monitor_pairs(state, key, prices)


def _monitor_session_position(state, key, prices):
    """Monitor DT or AB position: check stop and TP."""
    pos = state["positions"][key]
    symbol = pos["symbol"]
    price = prices.get(symbol)
    if price is None:
        return
    direction = pos["direction"]
    stop = pos["stop_price"]

    if (direction == 1 and price <= stop) or (direction == -1 and price >= stop):
        close_position(state, key, price, "STOP")
        return

    tp = pos.get("tp_price")
    if tp and ((direction == 1 and price >= tp) or (direction == -1 and price <= tp)):
        close_position(state, key, price, "TP")
        return


def _monitor_rsi2(state, key, prices):
    """Monitor RSI2 position: check stop, prev_high exit, max hold."""
    pos = state["positions"][key]
    symbol = pos["symbol"]
    price = prices.get(symbol)
    if price is None:
        return

    if price <= pos["stop_price"]:
        close_position(state, key, price, "STOP")
        return
    if price >= pos.get("prev_high", float("inf")):
        close_position(state, key, price, "PREV_HIGH")
        return
    if pos.get("entry_day", 0) >= pos.get("max_hold_days", RSI2_MAX_HOLD):
        close_position(state, key, price, "MAX_HOLD")
        return


def _monitor_pairs(state, key, prices):
    """Monitor pairs position: check z-reversion, max hold, max loss."""
    pos = state["positions"][key]
    btc_price = prices.get("BTCUSDT")
    eth_price = prices.get("ETHUSDT")
    if not btc_price or not eth_price:
        return

    r_mean = pos.get("ratio_mean", 0)
    r_std = pos.get("ratio_std", 1)
    if r_std < 1e-9:
        return
    current_z = (btc_price / eth_price - r_mean) / r_std

    if abs(current_z) < PAIRS_Z_EXIT:
        close_pairs_position(state, key, btc_price, eth_price,
                             f"Z_REVERT(z={current_z:.2f})")
        return
    if pos.get("entry_day", 0) >= pos.get("max_hold_days", PAIRS_MAX_HOLD):
        close_pairs_position(state, key, btc_price, eth_price, "MAX_HOLD")
        return

    direction = pos["direction"]
    half = pos["position_size"] / 2
    btc_pnl = direction * (btc_price - pos["btc_entry"]) / pos["btc_entry"]
    eth_pnl = -direction * (eth_price - pos["eth_entry"]) / pos["eth_entry"]
    total_pnl_pct = (btc_pnl * half + eth_pnl * half) / pos["position_size"] * 100
    if total_pnl_pct < -PAIRS_MAX_LOSS_PCT:
        close_pairs_position(state, key, btc_price, eth_price,
                             f"MAX_LOSS({total_pnl_pct:.1f}%)")


# ============================================================
# TIME EXITS
# ============================================================

def exit_session_positions(state, session_name, prices):
    """Time-exit all DT positions for a session."""
    for key in list(state["positions"].keys()):
        pos = state["positions"][key]
        if pos["strategy"] != "dual_thrust":
            continue
        if pos.get("session") != session_name:
            continue
        symbol = pos["symbol"]
        price = prices.get(symbol)
        if price is None:
            price = 0
        close_position(state, key, price, "TIME_EXIT")


def exit_asia_breakout(state, prices):
    """Time-exit all Asia Breakout positions."""
    for key in list(state["positions"].keys()):
        pos = state["positions"][key]
        if pos["strategy"] != "asia_breakout":
            continue
        symbol = pos["symbol"]
        price = prices.get(symbol)
        if price is None:
            price = 0
        close_position(state, key, price, "TIME_EXIT")


# ============================================================
# PENDING CLEANUP
# ============================================================

def cleanup_expired_pending(state):
    """Remove pending signals past their expiry hour."""
    now_h = datetime.now(timezone.utc).hour
    expired = [
        k for k, v in state.get("pending", {}).items()
        if now_h >= v.get("expires_h", 24)
    ]
    for k in expired:
        del state["pending"][k]
