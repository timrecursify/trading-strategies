"""
Microstructure strategies: CVD Divergence, VWAP + Funding Rate Regime.
These strategies use volume delta and market microstructure signals.
Sources: strats_tier1.py (CVD, VWAP+Funding).
"""

from typing import Callable


def make_cvd_divergence(
    lookback: int = 60,
    entry_start: int = 720,
    exit_min: int = 1200,
    stop_pct: float = 0.003,
    tp_mult: float = 1.5,
) -> Callable[[dict, list], list[tuple]]:
    """
    CVD (Cumulative Volume Delta) divergence: trade when price makes
    a new high/low but CVD does not confirm. Bearish divergence = price
    higher high with CVD lower high. Bullish divergence = price lower
    low with CVD higher low. CVD approximated from candle direction.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        deltas: list[float] = []
        price_series: list[float] = []
        scan_start = max(0, entry_start - lookback - 10)
        scan_end = min(entry_start + 120, 1440)

        for m in range(scan_start, scan_end):
            bar = prices[m]
            if bar is None:
                deltas.append(0)
                price_series.append(
                    price_series[-1] if price_series else 0
                )
                continue
            rng = bar[1] - bar[2]
            if rng > 0:
                delta = (bar[3] - bar[0]) / rng
            else:
                delta = 0
            deltas.append(delta)
            price_series.append(bar[3])

        if len(deltas) < lookback:
            return []

        # Cumulative delta
        cvd: list[float] = []
        running = 0.0
        for d in deltas:
            running += d
            cvd.append(running)

        window = min(lookback, len(cvd))
        if window < 20:
            return []

        price_window = price_series[-window:]
        cvd_window = cvd[-window:]

        # Bearish divergence: price higher high, CVD lower high
        price_max_idx = price_window.index(max(price_window))
        cvd_at_price_max = cvd_window[price_max_idx]

        bearish_div = False
        for i in range(price_max_idx):
            if price_window[i] < price_window[price_max_idx] * 0.999:
                if cvd_window[i] > cvd_at_price_max * 1.1:
                    bearish_div = True
                    break

        # Bullish divergence: price lower low, CVD higher low
        price_min_idx = price_window.index(min(price_window))
        cvd_at_price_min = cvd_window[price_min_idx]
        bullish_div = False
        for i in range(price_min_idx):
            if price_window[i] > price_window[price_min_idx] * 1.001:
                if cvd_window[i] < cvd_at_price_min * 0.9:
                    bullish_div = True
                    break

        if not bearish_div and not bullish_div:
            return []

        bar = prices[entry_start]
        if bar is None:
            return []
        ep = bar[0]

        if bearish_div:
            stop = ep * (1 + stop_pct)
            risk = abs(stop - ep)
            tp = ep - risk * tp_mult
            return [(-1, entry_start, stop, tp, exit_min)]
        else:
            stop = ep * (1 - stop_pct)
            risk = abs(ep - stop)
            tp = ep + risk * tp_mult
            return [(1, entry_start, stop, tp, exit_min)]

    return signal


def make_vwap_funding(
    entry_start: int = 720,
    exit_min: int = 1200,
    stop_pct: float = 0.0025,
    tp_pct: float = 0.005,
) -> Callable[[dict, list], list[tuple]]:
    """
    VWAP cross with funding rate regime awareness.
    Positive funding (overleveraged longs): short on VWAP cross down.
    Negative funding (overleveraged shorts): long on VWAP cross up.
    Neutral funding: trade momentum direction of VWAP cross.
    """
    def signal(day: dict, prices: list) -> list[tuple]:
        funding = day.get("funding_avg", 0)

        # Calculate VWAP from midnight to entry
        cum_vol = 0.0
        cum_tp_vol = 0.0
        vwap_val = None
        for m in range(0, entry_start):
            bar = prices[m]
            if bar is None:
                continue
            tp = (bar[1] + bar[2] + bar[3]) / 3
            vol = 1.0
            cum_vol += vol
            cum_tp_vol += tp * vol
            vwap_val = cum_tp_vol / cum_vol

        if vwap_val is None:
            return []

        # Scan for VWAP cross
        prev_above: bool | None = None
        for m in range(entry_start, min(entry_start + 120, 1440)):
            bar = prices[m]
            if bar is None:
                continue
            above = bar[3] > vwap_val

            if prev_above is not None and above != prev_above:
                ep = bar[3]

                if funding > 0.0001:
                    if not above:
                        stop = ep * (1 + stop_pct)
                        tp = ep * (1 - tp_pct)
                        return [(-1, m, stop, tp, exit_min)]
                elif funding < -0.0001:
                    if above:
                        stop = ep * (1 - stop_pct)
                        tp = ep * (1 + tp_pct)
                        return [(1, m, stop, tp, exit_min)]
                else:
                    direction = 1 if above else -1
                    stop = ep * (1 - direction * stop_pct)
                    tp = ep * (1 + direction * tp_pct)
                    return [(direction, m, stop, tp, exit_min)]

            prev_above = above

        return []

    return signal
