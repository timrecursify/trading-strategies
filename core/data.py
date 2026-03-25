"""
Canonical data loading and daily OHLCV construction.
Consolidates duplicated load_1m(), group_by_date(), build_daily_ohlcv()
from across the codebase into a single import point.
"""

import sqlite3
from datetime import datetime, timezone
from collections import defaultdict

from config.constants import DB_PATH


def load_1m(symbol: str) -> list[dict]:
    """Load all 1-minute candles for a symbol from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM klines WHERE symbol=? AND interval='1m' ORDER BY open_time",
        (symbol,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def load_candles(symbol: str, interval: str) -> list[dict]:
    """Load all candles for a symbol and interval."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM klines WHERE symbol=? AND interval=? ORDER BY open_time",
        (symbol, interval),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def group_by_date(candles: list[dict]) -> dict[str, list[dict]]:
    """Group candles by UTC date string. Returns {date_str: [candles]}."""
    grouped: dict[str, list[dict]] = {}
    for c in candles:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        key = dt.strftime("%Y-%m-%d")
        grouped.setdefault(key, []).append(c)
    return grouped


def build_daily_ohlcv(by_date: dict[str, list[dict]]) -> list[dict]:
    """
    Build daily OHLCV bars from grouped 1m candles.
    Skips partial days (fewer than 1400 candles).
    """
    days_map: dict[str, dict] = defaultdict(
        lambda: {"o": None, "h": -1e18, "l": 1e18, "c": None, "v": 0.0}
    )
    for date_str, candles in by_date.items():
        if len(candles) < 1400:
            continue
        for c in candles:
            p = days_map[date_str]
            if p["o"] is None:
                p["o"] = c["open"]
            if c["high"] > p["h"]:
                p["h"] = c["high"]
            if c["low"] < p["l"]:
                p["l"] = c["low"]
            p["c"] = c["close"]
            p["v"] += c["volume"]

    result: list[dict] = []
    for d in sorted(days_map.keys()):
        p = days_map[d]
        if p["o"] is None:
            continue
        dt = datetime.strptime(d, "%Y-%m-%d")
        result.append({
            "date": d,
            "open": p["o"],
            "high": p["h"],
            "low": p["l"],
            "close": p["c"],
            "volume": p["v"],
            "dow": dt.weekday(),
            "month": d[:7],
            "year": d[:4],
            "day_of_month": dt.day,
        })
    return result


def add_common_indicators(days: list[dict]) -> None:
    """
    Add RSI(2), RSI(14), ATR(14), SMA(50), SMA(200), EMA(20) to daily bars.
    Modifies days in place.
    """
    closes = [d["close"] for d in days]
    highs = [d["high"] for d in days]
    lows = [d["low"] for d in days]
    n = len(days)

    # RSI helper (Wilder smoothing)
    def _compute_rsi(period: int) -> list[float]:
        out = [50.0] * n
        if n < period + 1:
            return out
        gains: list[float] = []
        losses_list: list[float] = []
        for i in range(1, n):
            diff = closes[i] - closes[i - 1]
            gains.append(max(diff, 0))
            losses_list.append(max(-diff, 0))
        avg_g = sum(gains[:period]) / period
        avg_l = sum(losses_list[:period]) / period
        if avg_l == 0:
            out[period] = 100.0
        else:
            out[period] = 100 - 100 / (1 + avg_g / avg_l)
        for i in range(period, len(gains)):
            avg_g = (avg_g * (period - 1) + gains[i]) / period
            avg_l = (avg_l * (period - 1) + losses_list[i]) / period
            idx = i + 1
            if avg_l == 0:
                out[idx] = 100.0
            else:
                out[idx] = 100 - 100 / (1 + avg_g / avg_l)
        return out

    rsi2 = _compute_rsi(2)
    rsi14 = _compute_rsi(14)

    # ATR(14) using Wilder EMA
    atr_vals = [highs[0] - lows[0]] if n > 0 else []
    for i in range(1, n):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        if i < 14:
            atr_vals.append(tr)
        else:
            atr_vals.append((atr_vals[-1] * 13 + tr) / 14)

    # SMA helper
    def _compute_sma(period: int) -> list[float | None]:
        out: list[float | None] = [None] * n
        for i in range(period - 1, n):
            out[i] = sum(closes[i - period + 1 : i + 1]) / period
        return out

    sma50 = _compute_sma(50)
    sma200 = _compute_sma(200)

    # EMA(20)
    ema20: list[float] = []
    k = 2 / 21
    for i in range(n):
        if i == 0:
            ema20.append(closes[0])
        else:
            ema20.append(closes[i] * k + ema20[-1] * (1 - k))

    for i in range(n):
        days[i]["rsi_2"] = rsi2[i]
        days[i]["rsi_14"] = rsi14[i]
        days[i]["atr_14"] = atr_vals[i] if i < len(atr_vals) else 0
        days[i]["sma_50"] = sma50[i]
        days[i]["sma_200"] = sma200[i]
        days[i]["ema_20"] = ema20[i]
