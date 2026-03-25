"""
Technical indicator calculations from raw candle data.
All implemented from scratch with no external dependencies.
Each function includes a one-line docstring with the formula.
"""


def ema(values: list[float], period: int) -> list[float]:
    """EMA_t = price * k + EMA_{t-1} * (1-k), where k = 2/(period+1)."""
    if not values:
        return []
    k = 2 / (period + 1)
    result = [values[0]]
    for v in values[1:]:
        result.append(v * k + result[-1] * (1 - k))
    return result


def sma(values: list[float], period: int) -> list[float]:
    """SMA = sum(values[i-period+1:i+1]) / period."""
    result: list[float] = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(sum(values[: i + 1]) / (i + 1))
        else:
            result.append(sum(values[i - period + 1 : i + 1]) / period)
    return result


def rsi(closes: list[float], period: int = 14) -> list[float]:
    """RSI = 100 - 100/(1 + avg_gain/avg_loss), Wilder smoothing."""
    if len(closes) < period + 1:
        return [50.0] * len(closes)
    deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]
    gains = [max(d, 0) for d in deltas]
    losses = [max(-d, 0) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    result = [50.0] * (period + 1)
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100 - (100 / (1 + rs)))
    return result


def macd(
    closes: list[float],
    fast: int = 12,
    slow: int = 26,
    signal: int = 9,
) -> tuple[list[float], list[float], list[float]]:
    """MACD = EMA(fast) - EMA(slow), signal = EMA(MACD, signal), hist = MACD - signal."""
    ema_fast = ema(closes, fast)
    ema_slow = ema(closes, slow)
    macd_line = [f - s for f, s in zip(ema_fast, ema_slow)]
    signal_line = ema(macd_line, signal)
    histogram = [m - s for m, s in zip(macd_line, signal_line)]
    return macd_line, signal_line, histogram


def bollinger_bands(
    closes: list[float],
    period: int = 20,
    std_mult: float = 2.0,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    """BB: upper = SMA + k*std, lower = SMA - k*std, pct_b = (price-lower)/(upper-lower)."""
    mid = sma(closes, period)
    upper: list[float] = []
    lower: list[float] = []
    bandwidth: list[float] = []
    pct_b: list[float] = []
    for i in range(len(closes)):
        start = max(0, i - period + 1)
        window = closes[start : i + 1]
        if len(window) < 2:
            upper.append(mid[i])
            lower.append(mid[i])
            bandwidth.append(0)
            pct_b.append(0.5)
            continue
        mean = mid[i]
        var = sum((v - mean) ** 2 for v in window) / len(window)
        std = var ** 0.5
        u = mean + std_mult * std
        el = mean - std_mult * std
        upper.append(u)
        lower.append(el)
        bw = (u - el) / mean * 100 if mean > 0 else 0
        bandwidth.append(bw)
        pb = (closes[i] - el) / (u - el) if (u - el) > 0 else 0.5
        pct_b.append(pb)
    return upper, mid, lower, bandwidth, pct_b


def atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float]:
    """ATR = EMA(true_range, period), TR = max(H-L, |H-prevC|, |L-prevC|)."""
    if len(highs) < 2:
        return [0.0] * len(highs)
    trs = [highs[0] - lows[0]]
    for i in range(1, len(highs)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    return ema(trs, period)


def adx(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> list[float]:
    """ADX = EMA(DX, period), DX = |+DI - -DI| / (+DI + -DI) * 100."""
    if len(highs) < period + 1:
        return [25.0] * len(highs)

    plus_dm: list[float] = []
    minus_dm: list[float] = []
    for i in range(1, len(highs)):
        up = highs[i] - highs[i - 1]
        down = lows[i - 1] - lows[i]
        plus_dm.append(up if up > down and up > 0 else 0)
        minus_dm.append(down if down > up and down > 0 else 0)

    atr_vals = atr(highs, lows, closes, period)
    smooth_plus = ema(plus_dm, period)
    smooth_minus = ema(minus_dm, period)

    result = [25.0]
    for i in range(len(smooth_plus)):
        a = atr_vals[i + 1] if i + 1 < len(atr_vals) else 1
        if a == 0:
            a = 1
        di_plus = (smooth_plus[i] / a) * 100
        di_minus = (smooth_minus[i] / a) * 100
        di_sum = di_plus + di_minus
        if di_sum == 0:
            result.append(0.0)
        else:
            dx = abs(di_plus - di_minus) / di_sum * 100
            result.append(dx)

    adx_vals = ema(result, period)
    while len(adx_vals) < len(highs):
        adx_vals.insert(0, 25.0)
    return adx_vals[: len(highs)]


def vwap(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    volumes: list[float],
) -> list[float]:
    """VWAP = cumulative(TP * volume) / cumulative(volume), TP = (H+L+C)/3."""
    result: list[float] = []
    cum_vol = 0.0
    cum_tp_vol = 0.0
    for i in range(len(closes)):
        tp = (highs[i] + lows[i] + closes[i]) / 3
        cum_vol += volumes[i]
        cum_tp_vol += tp * volumes[i]
        result.append(cum_tp_vol / cum_vol if cum_vol > 0 else tp)
    return result


def obv(closes: list[float], volumes: list[float]) -> list[float]:
    """OBV += volume if close > prev_close, -= volume if close < prev_close."""
    result = [0.0]
    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            result.append(result[-1] + volumes[i])
        elif closes[i] < closes[i - 1]:
            result.append(result[-1] - volumes[i])
        else:
            result.append(result[-1])
    return result


def stochastic(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    k_period: int = 14,
    d_period: int = 3,
) -> tuple[list[float], list[float]]:
    """%K = (C - LL) / (HH - LL) * 100, %D = SMA(%K, d_period)."""
    k_vals: list[float] = []
    for i in range(len(closes)):
        start = max(0, i - k_period + 1)
        h = max(highs[start : i + 1])
        el = min(lows[start : i + 1])
        if h == el:
            k_vals.append(50.0)
        else:
            k_vals.append((closes[i] - el) / (h - el) * 100)
    d_vals = sma(k_vals, d_period)
    return k_vals, d_vals


def ema_cross(
    closes: list[float],
    fast_period: int = 9,
    slow_period: int = 21,
) -> tuple[list[int], list[float], list[float]]:
    """EMA crossover: 1 if fast > slow, -1 if fast < slow, 0 if equal."""
    fast = ema(closes, fast_period)
    slow = ema(closes, slow_period)
    signals: list[int] = []
    for i in range(len(closes)):
        if fast[i] > slow[i]:
            signals.append(1)
        elif fast[i] < slow[i]:
            signals.append(-1)
        else:
            signals.append(0)
    return signals, fast, slow
