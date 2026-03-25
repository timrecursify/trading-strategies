"""
Trend following strategies: EMA Trend, Supertrend, Donchian Channel + ADX.
These strategies trade in the direction of the prevailing trend.
Sources: strats_quant.py (EMA trend), strats_tier2.py (Supertrend, Donchian).
"""

from typing import Callable

from core.indicators import ema, atr


def make_ema_trend(
    period: int = 20,
    stop_pct: float = 2.0,
    rr: float = 2.0,
    entry_h: int = 12,
    exit_h: int = 20,
) -> Callable[[dict, list], list[tuple]]:
    """
    Simple EMA trend: long when price above EMA, short when below.
    Signal generated from daily close vs EMA on prior day.
    """
    ema_key = f"ema_{period}"
    entry_min = entry_h * 60
    exit_min = exit_h * 60

    def signal(day: dict, prices: list) -> list[tuple]:
        close = day.get("close", 0)
        ema_val = day.get(ema_key, close)
        if close == 0:
            return []

        if close > ema_val:
            direction = 1
        elif close < ema_val:
            direction = -1
        else:
            return []

        bar = prices[entry_min]
        if bar is None:
            return []
        ep = bar[0]
        if ep <= 0:
            return []

        stop = ep * (1 - direction * stop_pct / 100)
        risk = abs(ep - stop)
        tp = ep + direction * risk * rr if rr else None

        return [(direction, entry_min, stop, tp, exit_min)]

    return signal


def make_supertrend(
    atr_period: int = 7,
    multiplier: float = 2.0,
    entry_start: int = 720,
    exit_min: int = 1200,
    tp_pct: float = 0.005,
) -> Callable[[dict, list], list[tuple]]:
    """
    Supertrend: ATR-based trailing band that flips between support and resistance.
    Trade direction changes (flips) within the entry window.
    Formula: upper = HL2 + mult*ATR, lower = HL2 - mult*ATR.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        closes: list[float] = []
        highs: list[float] = []
        lows: list[float] = []
        for m in range(1440):
            bar = prices[m]
            if bar:
                closes.append(bar[3])
                highs.append(bar[1])
                lows.append(bar[2])
            else:
                closes.append(closes[-1] if closes else 0)
                highs.append(highs[-1] if highs else 0)
                lows.append(lows[-1] if lows else 0)

        atr_vals = atr(highs, lows, closes, atr_period)

        trend = [1] * len(closes)
        upper = [0.0] * len(closes)
        lower = [0.0] * len(closes)

        for i in range(1, len(closes)):
            hl2 = (highs[i] + lows[i]) / 2
            upper[i] = hl2 + multiplier * atr_vals[i]
            lower[i] = hl2 - multiplier * atr_vals[i]

            if lower[i] > lower[i - 1] or closes[i - 1] < lower[i - 1]:
                pass
            else:
                lower[i] = lower[i - 1]

            if upper[i] < upper[i - 1] or closes[i - 1] > upper[i - 1]:
                pass
            else:
                upper[i] = upper[i - 1]

            if trend[i - 1] == 1:
                trend[i] = 1 if closes[i] > lower[i] else -1
            else:
                trend[i] = -1 if closes[i] < upper[i] else 1

        # Find flip in entry window
        for m in range(entry_start, min(entry_start + 120, 1440)):
            if m < 1:
                continue
            if trend[m] != trend[m - 1]:
                bar = prices[m]
                if bar is None:
                    continue
                direction = trend[m]
                ep = bar[3]
                st_line = lower[m] if direction == 1 else upper[m]
                stop = st_line
                risk = abs(ep - stop)
                tp = ep + direction * risk * 2.0
                return [(direction, m, stop, tp, exit_min)]

        return []

    return signal


def make_donchian_adx(
    channel_period: int = 100,
    entry_start: int = 720,
    exit_min: int = 1200,
    tp_mult: float = 2.0,
) -> Callable[[dict, list], list[tuple]]:
    """
    Donchian channel breakout with trend (SMA) filter.
    Buy on new channel highs, sell on new channel lows.
    Includes a moving average filter to trade with the trend.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        if entry_start < channel_period:
            return []

        ch_high = 0.0
        ch_low = 999999.0
        for m in range(entry_start - channel_period, entry_start):
            bar = prices[m]
            if bar is None:
                continue
            if bar[1] > ch_high:
                ch_high = bar[1]
            if bar[2] < ch_low:
                ch_low = bar[2]

        if ch_high == 0 or ch_low == 999999:
            return []

        ch_mid = (ch_high + ch_low) / 2

        # SMA filter
        recent_closes: list[float] = []
        for m in range(entry_start - 100, entry_start):
            bar = prices[m]
            if bar:
                recent_closes.append(bar[3])
        if not recent_closes:
            return []
        sma_val = sum(recent_closes) / len(recent_closes)

        for m in range(entry_start, min(entry_start + 120, 1440)):
            bar = prices[m]
            if bar is None:
                continue

            if bar[3] > ch_high and bar[3] > sma_val:
                ep = bar[3]
                stop = ch_mid
                risk = abs(ep - stop)
                tp = ep + risk * tp_mult
                return [(1, m, stop, tp, exit_min)]

            if bar[3] < ch_low and bar[3] < sma_val:
                ep = bar[3]
                stop = ch_mid
                risk = abs(stop - ep)
                tp = ep - risk * tp_mult
                return [(-1, m, stop, tp, exit_min)]

        return []

    return signal
