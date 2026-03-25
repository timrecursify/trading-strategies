"""
Smart money / ICT strategies: Fair Value Gap, Liquidity Sweep, Power of 3 (AMD).
These strategies model institutional order flow concepts.
Sources: strats_tier1.py (FVG, Liquidity Sweep), strats_tier2.py (Power of 3).
Note: these strategies underperformed in backtesting but are preserved
as documented research. Negative results are still results.
"""

from typing import Callable


def _find_swing_points(
    prices: list, left: int = 5, right: int = 5,
) -> tuple[list[tuple[int, float]], list[tuple[int, float]]]:
    """Find swing highs and lows from minute-indexed price array."""
    highs: list[tuple[int, float]] = []
    lows: list[tuple[int, float]] = []
    for i in range(left, 1440 - right):
        bar = prices[i]
        if bar is None:
            continue
        is_high = True
        is_low = True
        for j in range(i - left, i + right + 1):
            if j == i:
                continue
            b = prices[j]
            if b is None:
                continue
            if b[1] >= bar[1]:
                is_high = False
            if b[2] <= bar[2]:
                is_low = False
        if is_high:
            highs.append((i, bar[1]))
        if is_low:
            lows.append((i, bar[2]))
    return highs, lows


def make_fvg_reversion(
    scan_start: int = 420,
    entry_start: int = 720,
    exit_min: int = 1200,
    tp_mult: float = 1.5,
    max_fvg_age: int = 60,
) -> Callable[[dict, list], list[tuple]]:
    """
    Fair Value Gap reversion: identify 3-candle gaps on 5m data,
    then trade when price retraces into the gap. FVG = imbalance
    between candle[i-1] high and candle[i+1] low (or vice versa).
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        # Build 5m candles
        candles_5m: list[tuple] = []
        for m in range(0, 1440, 5):
            o, h, l, c = None, 0.0, 999999.0, None
            for j in range(m, min(m + 5, 1440)):
                bar = prices[j]
                if bar is None:
                    continue
                if o is None:
                    o = bar[0]
                if bar[1] > h:
                    h = bar[1]
                if bar[2] < l:
                    l = bar[2]
                c = bar[3]
            if o is not None and c is not None:
                candles_5m.append((m, o, h, l, c))

        # Find FVGs
        fvgs: list[tuple[str, float, float, int]] = []
        for i in range(1, len(candles_5m) - 1):
            t0_m, t0_o, t0_h, t0_l, t0_c = candles_5m[i - 1]
            t1_m, t1_o, t1_h, t1_l, t1_c = candles_5m[i]
            t2_m, t2_o, t2_h, t2_l, t2_c = candles_5m[i + 1]

            if t0_h < t2_l:
                fvgs.append(("bull", t2_l, t0_h, t1_m))
            if t0_l > t2_h:
                fvgs.append(("bear", t0_l, t2_h, t1_m))

        if not fvgs:
            return []

        # Look for price to retrace into FVG during entry window
        for m in range(entry_start, min(entry_start + 180, 1440)):
            bar = prices[m]
            if bar is None:
                continue

            for ftype, top, bottom, ftime in fvgs:
                if m - ftime > max_fvg_age * 5:
                    continue
                mid = (top + bottom) / 2
                gap_height = top - bottom

                if ftype == "bull" and bar[2] <= mid and bar[3] > bottom:
                    ep = mid
                    stop = bottom - gap_height * 0.1
                    tp = ep + gap_height * tp_mult
                    return [(1, m, stop, tp, exit_min)]

                if ftype == "bear" and bar[1] >= mid and bar[3] < top:
                    ep = mid
                    stop = top + gap_height * 0.1
                    tp = ep - gap_height * tp_mult
                    return [(-1, m, stop, tp, exit_min)]

        return []

    return signal


def make_liquidity_sweep(
    session_start: int = 720,
    session_end: int = 1200,
    stop_buffer: float = 0.001,
    tp_mult: float = 1.5,
    max_trades: int = 2,
) -> Callable[[dict, list], list[tuple]]:
    """
    Liquidity sweep reversal: detect stop hunts beyond swing
    highs/lows, then trade the reversal. Price sweeps a level
    and closes back inside, indicating a false breakout.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        lookback_start = max(0, session_start - 120)
        swing_h, swing_l = _find_swing_points(prices, left=5, right=5)

        recent_highs = [
            (m, p) for m, p in swing_h
            if lookback_start <= m < session_start
        ]
        recent_lows = [
            (m, p) for m, p in swing_l
            if lookback_start <= m < session_start
        ]

        if not recent_highs and not recent_lows:
            return []

        trades: list[tuple] = []
        used_levels: set[float] = set()

        for m in range(session_start, min(session_end, 1440)):
            if len(trades) >= max_trades:
                break
            bar = prices[m]
            if bar is None:
                continue

            for _, level in recent_highs:
                if level in used_levels:
                    continue
                if bar[1] > level * (1 + 0.0005):
                    if bar[3] < level:
                        entry = bar[3]
                        stop = bar[1] * (1 + stop_buffer)
                        risk = abs(stop - entry)
                        tp = entry - risk * tp_mult
                        trades.append((-1, m, stop, tp, session_end))
                        used_levels.add(level)
                        break

            for _, level in recent_lows:
                if level in used_levels:
                    continue
                if bar[2] < level * (1 - 0.0005):
                    if bar[3] > level:
                        entry = bar[3]
                        stop = bar[2] * (1 - stop_buffer)
                        risk = abs(entry - stop)
                        tp = entry + risk * tp_mult
                        trades.append((1, m, stop, tp, session_end))
                        used_levels.add(level)
                        break

        return trades

    return signal


def make_power_of_3(
    session_start: int = 720,
    session_end: int = 1200,
    accum_pct: float = 0.25,
    tp_mult: float = 1.5,
    stop_buffer: float = 0.001,
) -> Callable[[dict, list], list[tuple]]:
    """
    Power of 3 (AMD): Accumulation, Manipulation, Distribution
    within a session. Wait for range to form, then a false break
    (manipulation), then trade the real move (distribution).
    Based on ICT (Inner Circle Trader) concepts.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        session_len = session_end - session_start
        accum_end = session_start + int(session_len * accum_pct)

        acc_high = 0.0
        acc_low = 999999.0
        for m in range(session_start, accum_end):
            bar = prices[m]
            if bar is None:
                continue
            if bar[1] > acc_high:
                acc_high = bar[1]
            if bar[2] < acc_low:
                acc_low = bar[2]

        if acc_high == 0 or acc_low == 999999 or acc_high == acc_low:
            return []

        manip_dir = 0
        manip_extreme = 0.0

        for m in range(accum_end, session_end):
            bar = prices[m]
            if bar is None:
                continue

            if manip_dir == 0:
                if bar[1] > acc_high * (1 + 0.0005):
                    manip_dir = 1
                    manip_extreme = bar[1]
                elif bar[2] < acc_low * (1 - 0.0005):
                    manip_dir = -1
                    manip_extreme = bar[2]
                continue

            if manip_dir == 1 and bar[1] > manip_extreme:
                manip_extreme = bar[1]
            if manip_dir == -1 and bar[2] < manip_extreme:
                manip_extreme = bar[2]

            if manip_dir == 1 and bar[3] < acc_low:
                ep = bar[3]
                stop = manip_extreme * (1 + stop_buffer)
                risk = abs(stop - ep)
                tp = ep - risk * tp_mult
                return [(-1, m, stop, tp, session_end)]

            if manip_dir == -1 and bar[3] > acc_high:
                ep = bar[3]
                stop = manip_extreme * (1 - stop_buffer)
                risk = abs(ep - stop)
                tp = ep + risk * tp_mult
                return [(1, m, stop, tp, session_end)]

        return []

    return signal
