"""
Binance Futures API (fapi.binance.com) layer for paper trading.
Uses USDT-M perpetual futures endpoints for real futures prices.
"""

import json
import urllib.request

BASE_URL = "https://fapi.binance.com"
TIMEOUT = 15


def fetch_json(url):
    """Fetch JSON from URL with timeout and user-agent."""
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return json.loads(resp.read())


def get_daily_candles(symbol, limit=210):
    """Fetch daily OHLCV candles. Returns list of dicts."""
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval=1d&limit={limit}"
    data = fetch_json(url)
    return [
        {
            "open_time": int(k[0]),
            "open": float(k[1]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
            "volume": float(k[5]),
        }
        for k in data
    ]


def get_hourly_candles(symbol, limit=7):
    """Fetch hourly candles (used for Asia session range 00:00-07:00)."""
    url = f"{BASE_URL}/fapi/v1/klines?symbol={symbol}&interval=1h&limit={limit}"
    data = fetch_json(url)
    return [
        {
            "open_time": int(k[0]),
            "high": float(k[2]),
            "low": float(k[3]),
            "close": float(k[4]),
        }
        for k in data
    ]


def get_current_price(symbol):
    """Fetch current price for a single symbol."""
    url = f"{BASE_URL}/fapi/v2/ticker/price?symbol={symbol}"
    return float(fetch_json(url)["price"])


def get_batch_prices(symbols):
    """Fetch prices for all symbols in one API call.
    Returns dict: {symbol: price} for requested symbols only.
    """
    url = f"{BASE_URL}/fapi/v2/ticker/price"
    data = fetch_json(url)
    sym_set = set(symbols)
    return {
        item["symbol"]: float(item["price"])
        for item in data
        if item["symbol"] in sym_set
    }
