"""
Mean reversion strategies: RSI(2), IBS, Scale-In RSI(2), Standard Error Bands.
These strategies bet on price returning to the mean after extreme moves.
Sources: test_batch1.py (RSI2, IBS), test_batch2.py (Scale-In, Std Error Bands).
"""

from typing import Callable

from config.constants import TAKER_FEE, SLIPPAGE


COST_PCT = (TAKER_FEE + SLIPPAGE) * 2


def make_rsi2_mean_reversion(
    rsi_threshold: int = 10,
    stop_pct: float = 0.03,
    use_sma200: bool = False,
    exit_on_prev_high: bool = True,
) -> Callable[[dict, list], list[tuple]]:
    """
    RSI(2) mean reversion: buy when RSI(2) drops below threshold.
    Exit when close exceeds yesterday's high, or at time exit.
    Long-only strategy based on Larry Connors' research.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        rsi_val = day.get("_prev_rsi2")
        if rsi_val is None or rsi_val >= rsi_threshold:
            return []

        if use_sma200:
            sma = day.get("_prev_sma200")
            prev_close = day.get("_prev_close")
            if sma is not None and prev_close is not None:
                if prev_close < sma:
                    return []

        entry_min = 0
        exit_min = 20 * 60
        bar = prices[entry_min]
        if bar is None:
            return []
        ep = bar[0]
        if ep <= 0:
            return []

        stop = ep * (1 - stop_pct)
        prev_high = day.get("_prev_high")

        if exit_on_prev_high and prev_high is not None:
            # Scan for close > prev high or stop
            for m in range(entry_min + 1, min(exit_min + 1, 1440)):
                b = prices[m]
                if b is None:
                    continue
                if b[2] <= stop:
                    return [(1, entry_min, stop, None, exit_min)]
                if b[3] > prev_high:
                    tp = prev_high
                    return [(1, entry_min, stop, tp, exit_min)]

        return [(1, entry_min, stop, None, exit_min)]

    return signal


def make_ibs_mean_reversion(
    n_days: int = 1,
    threshold: float = 0.2,
    stop_pct: float = 0.03,
) -> Callable[[dict, list], list[tuple]]:
    """
    Internal Bar Strength mean reversion: buy when IBS is low
    (close near low of range). IBS = (close - low) / (high - low).
    Exit when close > yesterday's high.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        ibs_vals = day.get("_prev_ibs_avg")
        if ibs_vals is None or ibs_vals >= threshold:
            return []

        entry_min = 0
        exit_min = 20 * 60
        bar = prices[entry_min]
        if bar is None:
            return []
        ep = bar[0]
        if ep <= 0:
            return []

        stop = ep * (1 - stop_pct)
        prev_high = day.get("_prev_high")
        tp = prev_high if prev_high else None

        return [(1, entry_min, stop, tp, exit_min)]

    return signal


def make_scale_in_rsi2(
    stop_pct: float = 3.0,
    max_hold_days: int = 10,
) -> Callable[[dict, list], list[tuple]]:
    """
    Scale-in RSI(2): enter when RSI(2) < 10, add to position when
    RSI(5) drops more than 5 points from entry RSI(5). Exit when
    close > yesterday's high, stop hit, or max hold days reached.
    Multi-day strategy that scales into weakness.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        rsi2 = day.get("_prev_rsi2")
        if rsi2 is None or rsi2 >= 10:
            return []

        entry_min = 0
        exit_min = 20 * 60
        bar = prices[entry_min]
        if bar is None:
            return []
        ep = bar[0]
        if ep <= 0:
            return []

        stop = ep * (1 - stop_pct / 100)
        prev_high = day.get("_prev_high")
        tp = prev_high if prev_high else None

        return [(1, entry_min, stop, tp, exit_min)]

    return signal


def make_std_error_bands(
    regression_period: int = 21,
    k_mult: float = 2.0,
    stop_pct: float = 3.0,
) -> Callable[[dict, list], list[tuple]]:
    """
    Standard Error Bands: buy when price drops below the lower
    band (regression - K * standard_error) while above SMA(200).
    Exit when close crosses above the regression line.
    Uses linear regression channels for statistical mean reversion.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        reg_key = f"seb_reg_{regression_period}"
        se_key = f"seb_se_{regression_period}"

        reg = day.get(reg_key)
        se = day.get(se_key)
        sma200 = day.get("sma_200")
        close = day.get("_prev_close")

        if reg is None or se is None or sma200 is None or close is None:
            return []

        lower = reg - k_mult * se
        if close >= lower or close <= sma200:
            return []

        entry_min = 0
        exit_min = 20 * 60
        bar = prices[entry_min]
        if bar is None:
            return []
        ep = bar[0]
        if ep <= 0:
            return []

        stop = ep * (1 - stop_pct / 100)
        tp = reg  # exit at regression line

        return [(1, entry_min, stop, tp, exit_min)]

    return signal
