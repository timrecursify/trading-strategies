"""
Strategy interface convention for the crypto futures research framework.

Every strategy module contains factory functions that return signal callables.
The convention is:

    def make_strategy_name(**params) -> Callable:
        '''Returns a signal function.'''
        def signal(day: dict, prices: list) -> list[tuple]:
            ...
        return signal

Signal function contract:
    Input:
        day: dict with daily metrics (date, session data, indicators).
        prices: list of 1440 tuples indexed by minute-of-day,
                each tuple is (open, high, low, close) or None.

    Output:
        list of trade tuples: (direction, entry_min, stop_price, tp_price, exit_min)
        direction: 1 for long, -1 for short
        entry_min: minute-of-day for entry (0-1439)
        stop_price: absolute stop loss price
        tp_price: absolute take profit price, or None for time-only exit
        exit_min: minute-of-day for time exit

        Return empty list for no trade.

Rules:
    - Signals must use only data available at decision time. No look-ahead.
    - For daily-level signals, use day[i-1] data to generate day[i] trades.
    - Factory functions accept all tunable parameters explicitly.
    - Default parameter values should match the most-tested configuration.
"""

from typing import Callable

# Type alias for the signal function signature
SignalFn = Callable[[dict, list], list[tuple]]
