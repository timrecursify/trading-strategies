"""
Download Binance USDT-M Perpetual Futures data for backtesting.
Pairs: BTCUSDT, ETHUSDT
Intervals: 1m, 5m, 15m
Period: Last 365 days
Storage: SQLite
"""

import sqlite3
import urllib.request
import json
import time
import sys
from datetime import datetime, timedelta, timezone

DB_PATH = "futures_data.db"
BASE_URL = "https://fapi.binance.com/fapi/v1/klines"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVALS = ["1m", "5m", "15m"]
LIMIT = 1500
RATE_LIMIT_PAUSE = 0.15  # seconds between requests


def init_db(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS klines (
            symbol TEXT NOT NULL,
            interval TEXT NOT NULL,
            open_time INTEGER NOT NULL,
            open REAL NOT NULL,
            high REAL NOT NULL,
            low REAL NOT NULL,
            close REAL NOT NULL,
            volume REAL NOT NULL,
            close_time INTEGER NOT NULL,
            quote_volume REAL NOT NULL,
            trades INTEGER NOT NULL,
            taker_buy_volume REAL NOT NULL,
            taker_buy_quote_volume REAL NOT NULL,
            PRIMARY KEY (symbol, interval, open_time)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_klines_lookup
        ON klines (symbol, interval, open_time)
    """)
    conn.commit()


def fetch_klines(symbol, interval, start_ms, end_ms):
    params = (
        f"?symbol={symbol}&interval={interval}"
        f"&startTime={start_ms}&endTime={end_ms}&limit={LIMIT}"
    )
    url = BASE_URL + params
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def interval_ms(interval):
    multipliers = {"1m": 60_000, "5m": 300_000, "15m": 900_000}
    return multipliers[interval]


def download_symbol_interval(conn, symbol, interval, start_ms, end_ms):
    step = interval_ms(interval) * LIMIT
    current = start_ms
    total_inserted = 0
    total_expected = (end_ms - start_ms) // interval_ms(interval)

    while current < end_ms:
        chunk_end = min(current + step - 1, end_ms)
        retries = 0
        data = None

        while retries < 5:
            try:
                data = fetch_klines(symbol, interval, current, chunk_end)
                break
            except Exception as e:
                retries += 1
                wait = 2 ** retries
                print(f"  Retry {retries}/5 ({e}), waiting {wait}s...")
                time.sleep(wait)

        if data is None:
            print(f"  FAILED chunk starting {current}, skipping...")
            current = chunk_end + 1
            continue

        if not data:
            break

        rows = []
        for k in data:
            rows.append((
                symbol, interval, int(k[0]),
                float(k[1]), float(k[2]), float(k[3]), float(k[4]),
                float(k[5]), int(k[6]), float(k[7]),
                int(k[8]), float(k[9]), float(k[10])
            ))

        conn.executemany("""
            INSERT OR IGNORE INTO klines
            (symbol, interval, open_time, open, high, low, close,
             volume, close_time, quote_volume, trades,
             taker_buy_volume, taker_buy_quote_volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        conn.commit()

        total_inserted += len(rows)
        pct = min(100, (total_inserted / total_expected) * 100)
        last_dt = datetime.fromtimestamp(rows[-1][2] / 1000, tz=timezone.utc)
        sys.stdout.write(
            f"\r  {symbol} {interval}: {total_inserted:,} candles "
            f"({pct:.1f}%) — up to {last_dt:%Y-%m-%d %H:%M}"
        )
        sys.stdout.flush()

        current = int(data[-1][0]) + interval_ms(interval)
        time.sleep(RATE_LIMIT_PAUSE)

    print()
    return total_inserted


def main():
    now = datetime.now(timezone.utc)
    end_ms = int(now.timestamp() * 1000)
    start_ms = int((now - timedelta(days=365)).timestamp() * 1000)

    print(f"Period: {datetime.fromtimestamp(start_ms/1000, tz=timezone.utc):%Y-%m-%d} "
          f"-> {datetime.fromtimestamp(end_ms/1000, tz=timezone.utc):%Y-%m-%d}")
    print(f"Pairs: {', '.join(SYMBOLS)}")
    print(f"Intervals: {', '.join(INTERVALS)}")
    print(f"Database: {DB_PATH}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    init_db(conn)

    grand_total = 0
    for symbol in SYMBOLS:
        for interval in INTERVALS:
            count = download_symbol_interval(conn, symbol, interval, start_ms, end_ms)
            grand_total += count

    print(f"\nDone! {grand_total:,} total candles saved to {DB_PATH}")

    # Summary
    cursor = conn.execute("""
        SELECT symbol, interval, COUNT(*),
               MIN(open_time), MAX(open_time)
        FROM klines GROUP BY symbol, interval
    """)
    print(f"\n{'Symbol':<10} {'Interval':<10} {'Candles':>10} {'From':>12} {'To':>12}")
    print("-" * 56)
    for row in cursor:
        from_dt = datetime.fromtimestamp(row[3] / 1000, tz=timezone.utc)
        to_dt = datetime.fromtimestamp(row[4] / 1000, tz=timezone.utc)
        print(f"{row[0]:<10} {row[1]:<10} {row[2]:>10,} {from_dt:%Y-%m-%d}   {to_dt:%Y-%m-%d}")

    conn.close()


if __name__ == "__main__":
    main()
