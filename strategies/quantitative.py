"""
Quantitative strategies: Pairs Trading, Adaptive Regime Switching.
These use statistical methods rather than technical patterns.
Sources: test_batch3.py (Pairs Trading), strats_quant.py (Adaptive Regime).
"""

from typing import Callable


def make_pairs_trading(
    window: int = 30,
    z_entry: float = 2.0,
    z_exit: float = 0.5,
    max_hold: int = 10,
) -> Callable[[dict, list], list[tuple]]:
    """
    BTC/ETH ratio mean reversion: compute rolling z-score of the
    BTC/ETH price ratio, enter when z exceeds threshold, exit when
    z reverts toward zero. This is a market-neutral pairs trade.
    Note: requires both BTC and ETH price data simultaneously.
    The signal function here returns parameters for the pairs engine,
    not standard single-asset trades.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        z = day.get("_ratio_zscore")
        if z is None:
            return []

        # Entry: z-score exceeds threshold (from prior day)
        if z > z_entry:
            # Ratio too high: short BTC, long ETH
            return [(-1, 0, 0, 0, max_hold * 1440)]
        elif z < -z_entry:
            # Ratio too low: long BTC, short ETH
            return [(1, 0, 0, 0, max_hold * 1440)]

        return []

    return signal


def make_adaptive_regime(
    stop_pct: float = 2.0,
    rr: float = 2.0,
    entry_h: int = 12,
    exit_h: int = 20,
) -> Callable[[dict, list], list[tuple]]:
    """
    Adaptive regime switching: use ATR percentile to determine
    whether the market is in a high-vol (momentum) or low-vol
    (mean reversion) regime, then apply the appropriate strategy.
    High vol (ATR pctl > 0.7): follow 5-day momentum.
    Low vol (ATR pctl < 0.3): fade 5-day momentum.
    Neutral: follow EMA trend.
    """
    entry_min = entry_h * 60
    exit_min = exit_h * 60

    def signal(day: dict, prices: list) -> list[tuple]:
        pctl = day.get("atr_pctl", 0.5)
        ret_5 = day.get("ret_5d", 0)
        close = day.get("close", 0)
        ema_val = day.get("ema_20", close)

        if close == 0:
            return []

        if pctl > 0.7:
            direction = 1 if ret_5 > 0 else -1
        elif pctl < 0.3:
            direction = -1 if ret_5 > 0 else 1
        else:
            direction = 1 if close > ema_val else -1

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
