"""
Centralized constants for the crypto futures research project.
Every magic number in the codebase traces back to this file.
"""

# Database
DB_PATH = "futures_data.db"

# Trading fees (Binance Futures, standard tier)
TAKER_FEE = 0.0004       # 0.04% per side
MAKER_FEE = 0.0002       # 0.02% per side
SLIPPAGE = 0.0001         # 0.01% per side (BTC/ETH perps are liquid)
FUNDING_RATE = 0.0001     # 0.01% per 8h average

# Session boundaries (UTC hours)
ASIA_START = 0
ASIA_END = 7
LONDON_START = 7
LONDON_END = 16
LKZ_START = 7             # London Kill Zone
LKZ_END = 10
NYC_START = 12
NYC_END = 21
FUNDING_HOURS = [0, 8, 16]

# Default risk parameters
DEFAULT_RISK_PCT = 0.02   # 2% of account per trade
MAX_LEVERAGE = 10

# Statistical thresholds
MIN_TRADES_FOR_SIGNIFICANCE = 50
WALK_FORWARD_MAX_DEGRADATION = 0.50  # 50% degradation = fail

# Annualization
TRADING_DAYS_PER_YEAR = 365  # crypto trades every day
