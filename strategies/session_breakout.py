"""
Session breakout strategies: Dual Thrust, Asia Range Breakout, Opening Range Breakout.
These strategies trade breakouts of price ranges established during prior sessions.
Sources: test_batch4.py (Dual Thrust), run_v2.py (Asia BRK), strats_tier2.py (ORB).
"""

from typing import Callable

from config.constants import TAKER_FEE, SLIPPAGE


COST_PCT = (TAKER_FEE + SLIPPAGE) * 2


def make_dual_thrust(
    n: int = 3,
    k: float = 0.5,
    session_start_h: int = 7,
    stop_pct: float = 0.02,
    exit_hours: int = 12,
    trend_filter: str = "none",
) -> Callable[[dict, list], list[tuple]]:
    """
    Dual Thrust breakout: compute N-day range, set triggers at
    open +/- k * range. First breakout direction wins.
    Originally a Chinese futures strategy cited by Rob Carver.
    """
    sess_min = session_start_h * 60
    exit_min = min(sess_min + exit_hours * 60, 1439)

    def signal(day: dict, prices: list) -> list[tuple]:
        prev_days = day.get("_prev_days", [])
        if len(prev_days) < n:
            return []

        # Compute range from prior N days
        hh = max(d["high"] for d in prev_days[-n:])
        hc = max(d["close"] for d in prev_days[-n:])
        lc = min(d["close"] for d in prev_days[-n:])
        ll = min(d["low"] for d in prev_days[-n:])
        rng = max(hh - lc, hc - ll)
        if rng <= 0:
            return []

        # Get session open price
        open_bar = prices[sess_min] if sess_min < 1440 else None
        if open_bar is None:
            return []
        today_open = open_bar[0]

        buy_trigger = today_open + k * rng
        sell_trigger = today_open - k * rng

        # Trend filter
        if trend_filter == "sma200":
            sma_val = day.get("sma_200")
            prev_close = day.get("prev_close", today_open)
            if sma_val is not None:
                filter_long = prev_close > sma_val
                filter_short = prev_close < sma_val
            else:
                filter_long = True
                filter_short = True
        elif trend_filter == "sma50":
            sma_val = day.get("sma_50")
            prev_close = day.get("prev_close", today_open)
            if sma_val is not None:
                filter_long = prev_close > sma_val
                filter_short = prev_close < sma_val
            else:
                filter_long = True
                filter_short = True
        else:
            filter_long = True
            filter_short = True

        # Scan for breakout
        for m in range(sess_min, min(exit_min, 1440)):
            bar = prices[m]
            if bar is None:
                continue
            o, h, l, cl = bar

            if h >= buy_trigger and filter_long:
                entry_price = max(buy_trigger, o)
                stop = entry_price * (1 - stop_pct)
                return [(1, m, stop, None, exit_min)]

            if l <= sell_trigger and filter_short:
                entry_price = min(sell_trigger, o)
                stop = entry_price * (1 + stop_pct)
                return [(-1, m, stop, None, exit_min)]

        return []

    return signal


def make_asia_breakout(
    stop_pct: float = 0.5,
    rr: float = 1.0,
    exit_h: int = 12,
    brk_start_h: int = 7,
    brk_end_h: int = 10,
    buffer_pct: float = 0.0,
    trend_filter: bool = False,
) -> Callable[[dict, list], list[tuple]]:
    """
    Asian range breakout at London open. Trade the first break
    of the Asia session high/low during the London kill zone.
    """
    exit_min = exit_h * 60
    brk_start = brk_start_h * 60
    brk_end = brk_end_h * 60

    def signal(day: dict, prices: list) -> list[tuple]:
        ah = day.get("asia_high")
        al = day.get("asia_low")
        if ah is None or al is None or ah == al:
            return []

        # Apply buffer
        ah_level = ah * (1 + buffer_pct / 100)
        al_level = al * (1 - buffer_pct / 100)

        # Trend filter
        if trend_filter:
            ema_val = day.get("ema_20")
            dc = day.get("daily_close", 0)
            if ema_val is None:
                allow_long = True
                allow_short = True
            else:
                allow_long = dc > ema_val
                allow_short = dc < ema_val
        else:
            allow_long = True
            allow_short = True

        for m in range(brk_start, min(brk_end, 1440)):
            bar = prices[m]
            if bar is None:
                continue

            if bar[1] > ah_level and allow_long:
                ep = ah_level
                stop = ep * (1 - stop_pct / 100)
                risk = abs(ep - stop)
                tp = ep + risk * rr if rr else None
                return [(1, m, stop, tp, exit_min)]

            if bar[2] < al_level and allow_short:
                ep = al_level
                stop = ep * (1 + stop_pct / 100)
                risk = abs(ep - stop)
                tp = ep - risk * rr if rr else None
                return [(-1, m, stop, tp, exit_min)]

        return []

    return signal


def make_orb(
    open_min: int = 0,
    range_minutes: int = 15,
    exit_min: int = 960,
    tp_mult: float = 1.0,
) -> Callable[[dict, list], list[tuple]]:
    """
    Opening Range Breakout: trade the first break of the first
    N minutes' high/low range. Classic intraday breakout strategy.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        rng_high = 0.0
        rng_low = 999999.0
        for m in range(open_min, open_min + range_minutes):
            bar = prices[m]
            if bar is None:
                continue
            if bar[1] > rng_high:
                rng_high = bar[1]
            if bar[2] < rng_low:
                rng_low = bar[2]

        if rng_high == 0 or rng_low == 999999:
            return []

        rng_width = rng_high - rng_low
        mid = (rng_high + rng_low) / 2
        if rng_width / mid < 0.002:
            return []

        for m in range(open_min + range_minutes, exit_min):
            bar = prices[m]
            if bar is None:
                continue

            if bar[3] > rng_high:
                ep = bar[3]
                stop = rng_low
                tp = ep + rng_width * tp_mult
                return [(1, m, stop, tp, exit_min)]

            if bar[3] < rng_low:
                ep = bar[3]
                stop = rng_high
                tp = ep - rng_width * tp_mult
                return [(-1, m, stop, tp, exit_min)]

        return []

    return signal
