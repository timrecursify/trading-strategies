"""
Unit tests for the backtest engine.
Verifies fee calculations, simulation logic, and metric computation.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_fee_constants():
    """Verify fee constants are within expected ranges."""
    from config.constants import TAKER_FEE, MAKER_FEE, SLIPPAGE
    assert 0 < TAKER_FEE < 0.01, "Taker fee should be between 0 and 1%"
    assert 0 < MAKER_FEE < TAKER_FEE, "Maker fee should be less than taker"
    assert 0 < SLIPPAGE < 0.001, "Slippage should be small"


def test_simulate_fast_basic():
    """Verify simulate_fast with a known price path."""
    from core.engine import simulate_fast

    # Create a simple price array: price goes up from 100 to 105
    prices = [None] * 1440
    for m in range(1440):
        p = 100.0 + m * 0.01
        prices[m] = (p, p + 0.1, p - 0.1, p)  # open, high, low, close

    # Long entry at minute 0, exit at minute 100, stop at 99, no TP
    exit_price, reason, exit_cm, minutes = simulate_fast(
        prices, 0, 100, 1, 99.0, None)

    assert exit_price is not None, "Should produce an exit"
    assert reason == "time", "Should exit on time"
    assert minutes == 100, "Should hold for 100 minutes"


def test_simulate_fast_stop_hit():
    """Verify stop loss triggers correctly."""
    from core.engine import simulate_fast

    # Price drops from 100 to 95
    prices = [None] * 1440
    for m in range(1440):
        p = 100.0 - m * 0.05
        prices[m] = (p, p + 0.01, p - 0.05, p)

    # Long with stop at 98
    exit_price, reason, _, _ = simulate_fast(prices, 0, 1200, 1, 98.0, None)

    assert reason == "stop", "Should hit stop loss"
    assert exit_price <= 98.0, "Exit price should be at or below stop"


def test_simulate_fast_tp_hit():
    """Verify take profit triggers correctly."""
    from core.engine import simulate_fast

    # Price rises from 100 to 200
    prices = [None] * 1440
    for m in range(1440):
        p = 100.0 + m * 0.1
        prices[m] = (p, p + 0.2, p - 0.01, p)

    # Long with TP at 105
    exit_price, reason, _, _ = simulate_fast(prices, 0, 1200, 1, 90.0, 105.0)

    assert reason == "tp", "Should hit take profit"
    assert exit_price == 105.0, "Exit should be at TP price"


def test_pnl_calculation():
    """Verify P&L math: entry 100, exit 102 on a long = +2%."""
    entry = 100.0
    exit_p = 102.0
    direction = 1
    raw_pnl_pct = direction * (exit_p - entry) / entry
    assert abs(raw_pnl_pct - 0.02) < 0.0001, "Raw PNL should be 2%"


def test_short_pnl():
    """Verify short P&L: entry 100, exit 98 on a short = +2%."""
    entry = 100.0
    exit_p = 98.0
    direction = -1
    raw_pnl_pct = direction * (exit_p - entry) / entry
    assert abs(raw_pnl_pct - 0.02) < 0.0001, "Short PNL should be 2% on drop"


if __name__ == "__main__":
    tests = [
        test_fee_constants,
        test_simulate_fast_basic,
        test_simulate_fast_stop_hit,
        test_simulate_fast_tp_hit,
        test_pnl_calculation,
        test_short_pnl,
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
