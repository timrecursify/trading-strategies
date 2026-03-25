"""
Session definitions, data loading, and daily metrics computation.
All times in UTC. Crypto sessions follow traditional forex flows.
"""

import sqlite3
from datetime import datetime, timedelta, timezone, date

from config.constants import (
    DB_PATH,
    ASIA_START, ASIA_END,
    LONDON_START, LONDON_END,
    LKZ_START, LKZ_END,
    NYC_START, NYC_END,
    FUNDING_HOURS,
)


def load_candles(symbol: str, interval: str) -> list[dict]:
    """Load all candles for a symbol/interval, keyed by open_time ms."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT * FROM klines WHERE symbol=? AND interval=? ORDER BY open_time",
        (symbol, interval),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def candles_by_date(candles_1m: list[dict]) -> dict[str, list[dict]]:
    """Group 1m candles by UTC date. Returns {date_str: [candles]}."""
    grouped: dict[str, list[dict]] = {}
    for c in candles_1m:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        key = dt.strftime("%Y-%m-%d")
        grouped.setdefault(key, []).append(c)
    return grouped


def candles_in_range(
    day_candles: list[dict], hour_start: float, hour_end: float,
) -> list[dict]:
    """Filter candles within UTC hour range [start, end)."""
    out: list[dict] = []
    for c in day_candles:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        h = dt.hour + dt.minute / 60
        if hour_start <= h < hour_end:
            out.append(c)
    return out


def get_price_at(
    day_candles: list[dict], hour: int, minute: int = 0,
) -> float | None:
    """Get the open price of the candle at a specific UTC time."""
    target = hour * 60 + minute
    for c in day_candles:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        cm = dt.hour * 60 + dt.minute
        if cm == target:
            return c["open"]
    return None


def get_close_at(
    day_candles: list[dict], hour: int, minute: int = 0,
) -> float | None:
    """Get the close price of the candle at a specific UTC time."""
    target = hour * 60 + minute
    for c in day_candles:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        cm = dt.hour * 60 + dt.minute
        if cm == target:
            return c["close"]
    return None


def session_hlv(
    candles: list[dict],
) -> tuple[float | None, float | None, float]:
    """Compute high, low, total volume for a list of candles."""
    if not candles:
        return None, None, 0
    h = max(c["high"] for c in candles)
    el = min(c["low"] for c in candles)
    v = sum(c["volume"] for c in candles)
    return h, el, v


def pct_change(start: float | None, end: float | None) -> float:
    """Percentage change from start to end."""
    if start == 0 or start is None or end is None:
        return 0
    return ((end - start) / start) * 100


def compute_atr(candles_15m_day: list[dict], period: int = 14) -> float | None:
    """Compute ATR from 15m candles using last N candles of the day."""
    if len(candles_15m_day) < period + 1:
        return None
    trs: list[float] = []
    for i in range(1, len(candles_15m_day)):
        c = candles_15m_day[i]
        prev_close = candles_15m_day[i - 1]["close"]
        tr = max(
            c["high"] - c["low"],
            abs(c["high"] - prev_close),
            abs(c["low"] - prev_close),
        )
        trs.append(tr)
    if len(trs) < period:
        return sum(trs) / len(trs) if trs else None
    return sum(trs[-period:]) / period


def is_edt(d: date) -> bool:
    """Check if a date falls in EDT (2nd Sunday Mar to 1st Sunday Nov)."""
    year = d.year
    mar1 = date(year, 3, 1)
    mar_sun2 = mar1 + timedelta(days=(6 - mar1.weekday()) % 7 + 7)
    nov1 = date(year, 11, 1)
    nov_sun1 = nov1 + timedelta(days=(6 - nov1.weekday()) % 7)
    return mar_sun2 <= d < nov_sun1


def get_12pm_et_utc_hour(d: date) -> int:
    """Return UTC hour for 12pm ET on a given date."""
    return 16 if is_edt(d) else 17


def compute_daily_sessions(
    candles_1m: list[dict],
    candles_15m: list[dict],
    symbol: str,
) -> list[dict]:
    """Compute session metrics for each complete trading day."""
    by_date_1m = candles_by_date(candles_1m)
    by_date_15m = candles_by_date(candles_15m)

    days: list[dict] = []
    for date_str in sorted(by_date_1m.keys()):
        dc = by_date_1m[date_str]
        if len(dc) < 1400:
            continue

        d = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Asia session
        asia = candles_in_range(dc, ASIA_START, ASIA_END)
        asia_h, asia_l, asia_vol = session_hlv(asia)
        asia_open = get_price_at(dc, 0, 0)
        asia_close = get_close_at(dc, 6, 59)
        asia_range = asia_h - asia_l if asia_h and asia_l else 0
        asia_dir = pct_change(asia_open, asia_close)

        # London kill zone
        lkz = candles_in_range(dc, LKZ_START, LKZ_END)
        lkz_h, lkz_l, lkz_vol = session_hlv(lkz)
        lkz_mid = (lkz_h + lkz_l) / 2 if lkz_h and lkz_l else None

        # London full session metrics
        london = candles_in_range(dc, LONDON_START, NYC_START)
        _, _, london_vol = session_hlv(london)
        london_open = get_price_at(dc, 7, 0)

        # NYC prices at various times
        nyc_12 = get_price_at(dc, 12, 0)
        nyc_1230 = get_price_at(dc, 12, 30)
        nyc_13 = get_price_at(dc, 13, 0)
        nyc_1330 = get_price_at(dc, 13, 30)
        nyc_14 = get_price_at(dc, 14, 0)

        # London direction: London open to NYC open
        london_dir = pct_change(london_open, nyc_12)
        london_mag = abs(london_dir)

        # Exit prices at various times
        exit_prices: dict = {}
        for h in [14, 15, 16, 17, 18, 19, 20, 21]:
            p = get_price_at(dc, h, 0) if h < 24 else None
            exit_prices[h] = p
        et_hour = get_12pm_et_utc_hour(d)
        exit_prices["12pm_et"] = get_price_at(dc, et_hour, 0)

        # NYC session
        nyc = candles_in_range(dc, NYC_START, NYC_END)
        nyc_h, nyc_l, nyc_vol = session_hlv(nyc)

        # ATR from 15m
        dc_15m = by_date_15m.get(date_str, [])
        atr_val = compute_atr(dc_15m)

        # Full day range
        day_h = max(c["high"] for c in dc)
        day_l = min(c["low"] for c in dc)

        days.append({
            "date": date_str,
            "date_obj": d,
            "symbol": symbol,
            "asia_high": asia_h, "asia_low": asia_l,
            "asia_range": asia_range, "asia_dir": asia_dir,
            "asia_vol": asia_vol,
            "london_open": london_open,
            "lkz_high": lkz_h, "lkz_low": lkz_l, "lkz_mid": lkz_mid,
            "lkz_vol": lkz_vol, "london_vol": london_vol,
            "london_dir": london_dir, "london_mag": london_mag,
            "nyc_12": nyc_12, "nyc_1230": nyc_1230,
            "nyc_13": nyc_13, "nyc_1330": nyc_1330, "nyc_14": nyc_14,
            "exit_prices": exit_prices,
            "nyc_high": nyc_h, "nyc_low": nyc_l, "nyc_vol": nyc_vol,
            "atr": atr_val, "day_high": day_h, "day_low": day_l,
            "day_range": day_h - day_l,
            "et_exit_hour": et_hour,
        })

    return days


def compute_ema(values: list[float], period: int = 20) -> list[float]:
    """Compute EMA over a list of values. Returns list same length."""
    if not values:
        return []
    k = 2 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def add_ema_to_days(days: list[dict]) -> None:
    """Add 20-period EMA of daily close (21:00 UTC price) to each day."""
    closes: list[float] = []
    for d in days:
        c = d["exit_prices"].get(21) or d["exit_prices"].get(20)
        closes.append(c if c else closes[-1] if closes else 0)
    emas = compute_ema(closes, 20)
    for i, d in enumerate(days):
        d["ema_20"] = emas[i]
        d["daily_close"] = closes[i]


def load_all(symbol: str = "BTCUSDT") -> tuple[list[dict], list[dict]]:
    """Load and compute everything for a symbol."""
    print(f"  Loading {symbol} 1m candles...")
    c1m = load_candles(symbol, "1m")
    print(f"  Loading {symbol} 15m candles...")
    c15m = load_candles(symbol, "15m")
    print(f"  Computing daily sessions ({len(c1m)} 1m candles)...")
    days = compute_daily_sessions(c1m, c15m, symbol)
    add_ema_to_days(days)
    print(f"  {len(days)} complete trading days computed.")
    return days, c1m
