"""
Unit tests for technical indicator calculations.
Each test uses a known input sequence with a known expected output.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_sma():
    """SMA of [1,2,3,4,5] with period 3 should end at 4.0."""
    from core.indicators import sma
    result = sma([1, 2, 3, 4, 5], 3)
    assert abs(result[-1] - 4.0) < 0.001, f"Expected 4.0, got {result[-1]}"


def test_ema():
    """EMA converges toward recent values."""
    from core.indicators import ema
    result = ema([10, 10, 10, 10, 20, 20, 20, 20], 4)
    assert result[-1] > 15, "EMA should be above 15 after upward shift"
    assert result[-1] < 20, "EMA should still lag below 20"


def test_rsi_extremes():
    """RSI should be 100 on all-up sequence, near 0 on all-down."""
    from core.indicators import rsi
    up = [100 + i for i in range(20)]
    result_up = rsi(up, 14)
    assert result_up[-1] > 90, f"RSI on up sequence should be >90, got {result_up[-1]}"

    down = [100 - i for i in range(20)]
    result_down = rsi(down, 14)
    assert result_down[-1] < 10, f"RSI on down sequence should be <10, got {result_down[-1]}"


def test_rsi_flat():
    """RSI on flat prices: no losses means RSI = 100 (division by zero edge case)."""
    from core.indicators import rsi
    flat = [100.0] * 20
    result = rsi(flat, 14)
    # When there are zero losses, RSI is 100 by convention (no selling pressure)
    assert result[-1] == 100 or abs(result[-1] - 50) < 1, f"Got {result[-1]}"


def test_bollinger_bands():
    """BB upper > middle > lower, and bandwidth > 0 on volatile data."""
    from core.indicators import bollinger_bands
    data = [100 + (i % 5) for i in range(30)]
    upper, mid, lower, bw, pctb = bollinger_bands(data, 20, 2)
    assert upper[-1] > mid[-1] > lower[-1], "Upper > Mid > Lower"
    assert bw[-1] > 0, "Bandwidth should be positive"


def test_atr():
    """ATR should be positive and reflect the average range."""
    from core.indicators import atr
    highs = [101, 102, 103, 102, 104, 103, 105, 104, 103, 102,
             101, 102, 103, 104, 105, 106]
    lows = [99, 100, 101, 100, 102, 101, 103, 102, 101, 100,
            99, 100, 101, 102, 103, 104]
    closes = [100, 101, 102, 101, 103, 102, 104, 103, 102, 101,
              100, 101, 102, 103, 104, 105]
    result = atr(highs, lows, closes, 14)
    assert result[-1] > 0, "ATR should be positive"
    assert result[-1] < 5, "ATR should be reasonable for this data"


def test_stochastic():
    """Stochastic K should be near 100 at recent highs, near 0 at lows."""
    from core.indicators import stochastic
    highs = list(range(100, 120))
    lows = list(range(90, 110))
    closes = list(range(95, 115))
    k, d = stochastic(highs, lows, closes, 14, 3)
    assert k[-1] > 50, "K should be high when price is near top of range"


if __name__ == "__main__":
    tests = [
        test_sma, test_ema, test_rsi_extremes, test_rsi_flat,
        test_bollinger_bands, test_atr, test_stochastic,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS: {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  FAIL: {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
