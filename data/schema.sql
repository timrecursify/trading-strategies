-- Database schema for futures_data.db
-- Source: Binance USDT-M Perpetual Futures API
-- Coverage: BTCUSDT from 2019-09-08, ETHUSDT from 2019-11-27

CREATE TABLE IF NOT EXISTS klines (
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,          -- '1m', '5m', '15m'
    open_time INTEGER NOT NULL,      -- Unix timestamp in milliseconds
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    volume REAL NOT NULL,            -- Base asset volume
    close_time INTEGER NOT NULL,     -- Unix timestamp in milliseconds
    quote_volume REAL NOT NULL,      -- Quote asset volume (USDT)
    trades INTEGER NOT NULL,         -- Number of trades in candle
    taker_buy_volume REAL NOT NULL,  -- Taker buy base asset volume
    taker_buy_quote_volume REAL NOT NULL,
    PRIMARY KEY (symbol, interval, open_time)
);

CREATE INDEX IF NOT EXISTS idx_klines_lookup
ON klines (symbol, interval, open_time);

-- Fear and Greed Index (source: alternative.me)
-- Daily values, full history from 2018
CREATE TABLE IF NOT EXISTS fear_greed (
    timestamp INTEGER PRIMARY KEY,   -- Unix timestamp (seconds)
    value INTEGER NOT NULL,          -- 0 to 100
    classification TEXT NOT NULL     -- 'Extreme Fear', 'Fear', 'Neutral', 'Greed', 'Extreme Greed'
);

-- Binance funding rate (every 8 hours: 00:00, 08:00, 16:00 UTC)
CREATE TABLE IF NOT EXISTS funding_rate (
    symbol TEXT NOT NULL,
    funding_time INTEGER NOT NULL,   -- Unix timestamp in milliseconds
    funding_rate REAL NOT NULL,      -- Typically between -0.01 and +0.01
    mark_price REAL,
    PRIMARY KEY (symbol, funding_time)
);

-- Binance open interest (hourly, limited to ~30 days on free API)
CREATE TABLE IF NOT EXISTS open_interest (
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    open_interest REAL NOT NULL,
    open_interest_value REAL NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);

-- Binance top trader long/short ratio (hourly, limited to ~30 days)
CREATE TABLE IF NOT EXISTS long_short_ratio (
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    long_account REAL NOT NULL,
    short_account REAL NOT NULL,
    long_short_ratio REAL NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);

-- Binance taker buy/sell volume (hourly, limited to ~30 days)
CREATE TABLE IF NOT EXISTS taker_buy_sell (
    symbol TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    buy_vol REAL NOT NULL,
    sell_vol REAL NOT NULL,
    buy_sell_ratio REAL NOT NULL,
    PRIMARY KEY (symbol, timestamp)
);
