# Data Dictionary

## Database

**File:** `futures_data.db` (SQLite3, ~1.1 GB)

All timestamps are stored as millisecond Unix epoch (UTC).

## Tables

### klines

Primary candle data for all symbols and intervals.

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading pair identifier (e.g., "BTCUSDT", "ETHUSDT") |
| interval | TEXT | Candle interval: "1m", "5m", "15m" |
| open_time | INTEGER | Candle open timestamp (ms Unix epoch, UTC) |
| open | REAL | Opening price (USDT) |
| high | REAL | Highest price during candle (USDT) |
| low | REAL | Lowest price during candle (USDT) |
| close | REAL | Closing price (USDT) |
| volume | REAL | Base asset volume traded |
| close_time | INTEGER | Candle close timestamp (ms Unix epoch, UTC) |
| quote_volume | REAL | Quote asset (USDT) volume traded |
| trades | INTEGER | Number of individual trades during candle |
| taker_buy_volume | REAL | Volume bought by takers (base asset) |
| taker_buy_quote_volume | REAL | Volume bought by takers (USDT) |

**Primary key:** (symbol, interval, open_time)
**Index:** idx_klines_lookup ON (symbol, interval, open_time)

**Source:** Binance USDT-M Futures API (`/fapi/v1/klines`)
**Frequency:** Continuous (1m, 5m, 15m candles)

**Coverage:**

| Symbol | Interval | Records | Start | End |
|--------|----------|---------|-------|-----|
| BTCUSDT | 1m | 3,440,375 | 2019-09-08 | 2026-03-24 |
| BTCUSDT | 5m | 105,120 | 2025-03-24 | 2026-03-24 |
| BTCUSDT | 15m | 35,040 | 2025-03-24 | 2026-03-24 |
| ETHUSDT | 1m | 3,325,788 | 2019-11-27 | 2026-03-24 |
| ETHUSDT | 5m | 105,120 | 2025-03-24 | 2026-03-24 |
| ETHUSDT | 15m | 35,040 | 2025-03-24 | 2026-03-24 |

Note: 5m and 15m candles cover only 1 year. The 1m candles cover the full 6+ year period and are used for all multi-year backtests.

### fear_greed

Daily Fear and Greed Index for the crypto market.

| Column | Type | Description |
|--------|------|-------------|
| timestamp | INTEGER | Date timestamp (ms Unix epoch, UTC). Primary key. |
| value | INTEGER | Index value, 0 (extreme fear) to 100 (extreme greed) |
| classification | TEXT | Human-readable label: "Extreme Fear", "Fear", "Neutral", "Greed", "Extreme Greed" |

**Source:** Alternative.me Crypto Fear and Greed Index API
**Frequency:** Daily
**Coverage:** 2,970 records (2018 to 2026)

### funding_rate

Binance perpetual futures funding rate, paid/received every 8 hours.

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading pair (e.g., "BTCUSDT") |
| funding_time | INTEGER | Funding timestamp (ms Unix epoch, UTC) |
| funding_rate | REAL | Funding rate as decimal (e.g., 0.0001 = 0.01%) |
| mark_price | REAL | Mark price at funding time (USDT). Nullable. |

**Primary key:** (symbol, funding_time)
**Source:** Binance Futures API (`/fapi/v1/fundingRate`)
**Frequency:** Every 8 hours (00:00, 08:00, 16:00 UTC)
**Coverage:** 1,095 records per symbol (365 days)

### open_interest

Aggregate open interest for perpetual futures contracts.

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading pair |
| timestamp | INTEGER | Measurement timestamp (ms Unix epoch, UTC) |
| open_interest | REAL | Open interest in contracts (base asset) |
| open_interest_value | REAL | Open interest value in USDT |

**Primary key:** (symbol, timestamp)
**Source:** Binance Futures API (`/fapi/v1/openInterest`)
**Frequency:** 5-minute snapshots
**Coverage:** ~672 records per symbol (~28 days). Limited by API history retention.

### long_short_ratio

Top trader long/short account ratio.

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading pair |
| timestamp | INTEGER | Measurement timestamp (ms Unix epoch, UTC) |
| long_account | REAL | Proportion of accounts with net long positions |
| short_account | REAL | Proportion of accounts with net short positions |
| long_short_ratio | REAL | long_account / short_account |

**Primary key:** (symbol, timestamp)
**Source:** Binance Futures API (`/futures/data/topLongShortAccountRatio`)
**Frequency:** 5-minute snapshots
**Coverage:** ~672 records per symbol (~28 days). Limited by API history retention.

### taker_buy_sell

Taker buy/sell volume ratio.

| Column | Type | Description |
|--------|------|-------------|
| symbol | TEXT | Trading pair |
| timestamp | INTEGER | Measurement timestamp (ms Unix epoch, UTC) |
| buy_vol | REAL | Taker buy volume (USDT) |
| sell_vol | REAL | Taker sell volume (USDT) |
| buy_sell_ratio | REAL | buy_vol / sell_vol |

**Primary key:** (symbol, timestamp)
**Source:** Binance Futures API (`/futures/data/takerlongshortRatio`)
**Frequency:** 5-minute snapshots
**Coverage:** ~672 records per symbol (~28 days). Limited by API history retention.

## Derived Data (Computed at Runtime)

The following fields are computed during backtesting and are not stored in the database:

| Field | Source | Computation |
|-------|--------|-------------|
| Daily OHLCV | klines (1m) | Aggregated from 1m candles: 00:00-23:59 UTC |
| Session OHLCV | klines (1m) | Aggregated by session hours (Asia, London, NYC) |
| Technical indicators | Daily/session OHLCV | RSI, EMA, SMA, BB, ADX, Stochastic, VWAP, etc. |
| Taker buy ratio (daily) | klines (1m) | sum(taker_buy_volume) / sum(volume) per day |
| Spread proxy | klines (1m) | avg((high - low) / ((high + low) / 2)) per session |
| Trade intensity | klines (1m) | sum(trades) / session_minutes |
