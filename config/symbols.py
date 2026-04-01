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
    "SOLUSDT": {
        "launch": datetime(2020, 8, 11, tzinfo=timezone.utc),
        "base": "SOL",
        "quote": "USDT",
        "tick_size": 0.01,
        "min_qty": 0.1,
    },
    "DOGEUSDT": {
        "launch": datetime(2020, 7, 10, tzinfo=timezone.utc),
        "base": "DOGE",
        "quote": "USDT",
        "tick_size": 0.00001,
        "min_qty": 1,
    },
    "XRPUSDT": {
        "launch": datetime(2020, 1, 6, tzinfo=timezone.utc),
        "base": "XRP",
        "quote": "USDT",
        "tick_size": 0.0001,
        "min_qty": 0.1,
    },
    "AVAXUSDT": {
        "launch": datetime(2020, 9, 23, tzinfo=timezone.utc),
        "base": "AVAX",
        "quote": "USDT",
        "tick_size": 0.01,
        "min_qty": 0.1,
    },
    "LINKUSDT": {
        "launch": datetime(2020, 1, 9, tzinfo=timezone.utc),
        "base": "LINK",
        "quote": "USDT",
        "tick_size": 0.001,
        "min_qty": 0.1,
    },
    "ADAUSDT": {
        "launch": datetime(2020, 1, 31, tzinfo=timezone.utc),
        "base": "ADA",
        "quote": "USDT",
        "tick_size": 0.0001,
        "min_qty": 1,
    },
}

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

PAPER_SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "SOLUSDT", "DOGEUSDT",
    "XRPUSDT", "AVAXUSDT", "LINKUSDT", "ADAUSDT",
]
