"""
Symbol metadata for all traded instruments.
"""

from datetime import datetime, timezone

SYMBOLS = {
    "BTCUSDT": {
        "launch": datetime(2019, 9, 8, tzinfo=timezone.utc),
        "base": "BTC",
        "quote": "USDT",
        "tick_size": 0.1,
        "min_qty": 0.001,
    },
    "ETHUSDT": {
        "launch": datetime(2019, 11, 27, tzinfo=timezone.utc),
        "base": "ETH",
        "quote": "USDT",
        "tick_size": 0.01,
        "min_qty": 0.01,
    },
}

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]
