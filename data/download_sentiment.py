"""
Download all free sentiment/on-chain data for backtesting.
Sources: Alternative.me Fear & Greed, Binance Futures (funding, OI, LS ratio, taker vol)
"""

import sqlite3
import urllib.request
import json
import time
import sys
from datetime import datetime, timedelta, timezone

DB_PATH = "futures_data.db"
SYMBOLS = ["BTCUSDT", "ETHUSDT"]


def init_sentiment_tables(conn):
    conn.execute("""
        CREATE TABLE IF NOT EXISTS fear_greed (
            timestamp INTEGER PRIMARY KEY,
            value INTEGER NOT NULL,
            classification TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS funding_rate (
            symbol TEXT NOT NULL,
            funding_time INTEGER NOT NULL,
            funding_rate REAL NOT NULL,
            mark_price REAL,
            PRIMARY KEY (symbol, funding_time)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS open_interest (
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            open_interest REAL NOT NULL,
            open_interest_value REAL NOT NULL,
            PRIMARY KEY (symbol, timestamp)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS long_short_ratio (
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            long_account REAL NOT NULL,
            short_account REAL NOT NULL,
            long_short_ratio REAL NOT NULL,
            PRIMARY KEY (symbol, timestamp)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS taker_buy_sell (
            symbol TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            buy_vol REAL NOT NULL,
            sell_vol REAL NOT NULL,
            buy_sell_ratio REAL NOT NULL,
            PRIMARY KEY (symbol, timestamp)
        )
    """)
    conn.commit()


def fetch_json(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header("User-Agent", "Mozilla/5.0")
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2 ** (attempt + 1))
            else:
                return None


def paginate_backwards(base_url, symbol, period, limit, start_ms,
                       ts_key="timestamp"):
    """
    Paginate Binance futures data endpoints backwards using endTime.
    Returns all records from start_ms to now, sorted ascending.
    """
    all_data = []
    end_ms = None  # start from latest

    while True:
        url = f"{base_url}?symbol={symbol}&period={period}&limit={limit}"
        if end_ms is not None:
            url += f"&endTime={end_ms}"

        data = fetch_json(url)
        if data is None or len(data) == 0:
            break

        # Filter to our date range
        filtered = [d for d in data if int(d[ts_key]) >= start_ms]
        all_data.extend(filtered)

        # Get oldest timestamp for next page
        oldest_ts = int(data[0][ts_key])
        if oldest_ts <= start_ms:
            break  # reached our start date

        end_ms = oldest_ts - 1
        time.sleep(0.15)

        if len(all_data) % 2000 == 0 and len(all_data) > 0:
            sys.stdout.write(f"\r    {len(all_data)} records...")
            sys.stdout.flush()

    # Sort ascending by timestamp
    all_data.sort(key=lambda d: int(d[ts_key]))
    return all_data


# ============================================================
# 1. FEAR & GREED INDEX
# ============================================================

def download_fear_greed(conn):
    print("\n" + "=" * 60)
    print("1. FEAR & GREED INDEX (Alternative.me)")
    print("=" * 60)

    url = "https://api.alternative.me/fng/?limit=0&format=json"
    data = fetch_json(url)
    if data is None or "data" not in data:
        print("  Failed to fetch Fear & Greed data")
        return

    rows = [(int(e["timestamp"]), int(e["value"]), e["value_classification"])
            for e in data["data"]]
    conn.executemany(
        "INSERT OR IGNORE INTO fear_greed VALUES (?, ?, ?)", rows)
    conn.commit()

    now = datetime.now(timezone.utc)
    start_ts = int((now - timedelta(days=365)).timestamp())
    count = conn.execute(
        "SELECT COUNT(*) FROM fear_greed WHERE timestamp >= ?",
        (start_ts,)).fetchone()[0]
    print(f"  {len(rows)} total, {count} in last 365 days")

    # Distribution
    for cls in ["Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed"]:
        c = conn.execute(
            "SELECT COUNT(*) FROM fear_greed WHERE timestamp >= ? AND classification = ?",
            (start_ts, cls)).fetchone()[0]
        print(f"    {cls}: {c} days")


# ============================================================
# 2. FUNDING RATE
# ============================================================

def download_funding_rate(conn, symbol):
    print(f"\n  Funding Rate [{symbol}]...")
    base = "https://fapi.binance.com/fapi/v1/fundingRate"
    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=365)).timestamp() * 1000)

    all_rows = []
    current = start_ms
    while True:
        url = f"{base}?symbol={symbol}&startTime={current}&limit=1000"
        data = fetch_json(url)
        if data is None or len(data) == 0:
            break
        for e in data:
            all_rows.append((symbol, int(e["fundingTime"]),
                             float(e["fundingRate"]),
                             float(e.get("markPrice", 0))))
        current = int(data[-1]["fundingTime"]) + 1
        time.sleep(0.15)

    conn.executemany(
        "INSERT OR IGNORE INTO funding_rate VALUES (?, ?, ?, ?)", all_rows)
    conn.commit()
    print(f"    {len(all_rows)} entries")


# ============================================================
# 3. OPEN INTEREST (backward pagination)
# ============================================================

def download_open_interest(conn, symbol):
    print(f"\n  Open Interest [{symbol}]...")
    base = "https://fapi.binance.com/futures/data/openInterestHist"
    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=365)).timestamp() * 1000)

    data = paginate_backwards(base, symbol, "1h", 500, start_ms)
    rows = [(symbol, int(d["timestamp"]), float(d["sumOpenInterest"]),
             float(d["sumOpenInterestValue"])) for d in data]
    conn.executemany(
        "INSERT OR IGNORE INTO open_interest VALUES (?, ?, ?, ?)", rows)
    conn.commit()
    print(f"\r    {len(rows)} entries{'':30}")


# ============================================================
# 4. LONG/SHORT RATIO (backward pagination)
# ============================================================

def download_long_short_ratio(conn, symbol):
    print(f"\n  Long/Short Ratio [{symbol}]...")
    base = "https://fapi.binance.com/futures/data/topLongShortAccountRatio"
    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=365)).timestamp() * 1000)

    data = paginate_backwards(base, symbol, "1h", 500, start_ms)
    rows = [(symbol, int(d["timestamp"]), float(d["longAccount"]),
             float(d["shortAccount"]), float(d["longShortRatio"])) for d in data]
    conn.executemany(
        "INSERT OR IGNORE INTO long_short_ratio VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    print(f"\r    {len(rows)} entries{'':30}")


# ============================================================
# 5. TAKER BUY/SELL VOLUME (backward pagination)
# ============================================================

def download_taker_buy_sell(conn, symbol):
    print(f"\n  Taker Buy/Sell Volume [{symbol}]...")
    base = "https://fapi.binance.com/futures/data/takerlongshortRatio"
    now = datetime.now(timezone.utc)
    start_ms = int((now - timedelta(days=365)).timestamp() * 1000)

    data = paginate_backwards(base, symbol, "1h", 500, start_ms)
    rows = [(symbol, int(d["timestamp"]), float(d["buyVol"]),
             float(d["sellVol"]), float(d["buySellRatio"])) for d in data]
    conn.executemany(
        "INSERT OR IGNORE INTO taker_buy_sell VALUES (?, ?, ?, ?, ?)", rows)
    conn.commit()
    print(f"\r    {len(rows)} entries{'':30}")


# ============================================================
# SUMMARY & MAIN
# ============================================================

def print_summary(conn):
    print("\n" + "=" * 60)
    print("DATA SUMMARY")
    print("=" * 60)
    queries = [
        ("fear_greed", "SELECT COUNT(*), MIN(timestamp), MAX(timestamp) FROM fear_greed"),
    ]
    for name, q in queries:
        r = conn.execute(q).fetchone()
        if r[0] > 0:
            d1 = datetime.fromtimestamp(r[1], tz=timezone.utc)
            d2 = datetime.fromtimestamp(r[2], tz=timezone.utc)
            print(f"  {name}: {r[0]:,} rows ({d1:%Y-%m-%d} → {d2:%Y-%m-%d})")

    for table in ["funding_rate", "open_interest", "long_short_ratio", "taker_buy_sell"]:
        ts_col = "funding_time" if table == "funding_rate" else "timestamp"
        for sym in SYMBOLS:
            r = conn.execute(
                f"SELECT COUNT(*), MIN({ts_col}), MAX({ts_col}) FROM {table} WHERE symbol=?",
                (sym,)).fetchone()
            if r[0] > 0:
                d1 = datetime.fromtimestamp(r[1] / 1000, tz=timezone.utc)
                d2 = datetime.fromtimestamp(r[2] / 1000, tz=timezone.utc)
                print(f"  {table} [{sym}]: {r[0]:,} rows ({d1:%Y-%m-%d} → {d2:%Y-%m-%d})")
            else:
                print(f"  {table} [{sym}]: 0 rows")

    # DB file size
    import os
    size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
    print(f"\n  Database size: {size_mb:.1f} MB")


def main():
    print("=" * 60)
    print("DOWNLOADING SENTIMENT & ON-CHAIN DATA")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    init_sentiment_tables(conn)

    download_fear_greed(conn)

    for symbol in SYMBOLS:
        print(f"\n{'#'*60}")
        print(f"  {symbol}")
        print(f"{'#'*60}")
        download_funding_rate(conn, symbol)
        download_open_interest(conn, symbol)
        download_long_short_ratio(conn, symbol)
        download_taker_buy_sell(conn, symbol)

    print_summary(conn)
    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
