# Crypto Futures Day Trading Research

Systematic evaluation of 50+ day trading strategies on BTC and ETH perpetual futures, covering 70,000+ backtests across 16 research phases and 6.3 years of minute-level data.

## Key Findings

- **ETH Dual Thrust is the best strategy found:** $1,000 to $3,443 over 6.3 years, 12.4% max drawdown, return/DD ratio of 19.63.
- **Most strategies lose money.** Of 70,000+ backtests, the vast majority were negative after fees. ICT concepts (FVG, CVD, Wyckoff) failed. Daily momentum failed. Mean reversion failed on crypto.
- **A critical look-ahead bias was discovered and corrected.** Phase 9 produced a fake 84% win rate and +380% annual return from a single data access bug. The incident is documented as a cautionary reference.

## Project Structure

```
crypto-futures-research/
├── README.md
├── LICENSE
├── .gitignore
├── CHANGELOG.md
├── config/                      # Constants, symbols, parameter grids
│   ├── constants.py             # Fees, session hours, risk defaults
│   ├── parameters.py            # Strategy parameter grids
│   └── symbols.py               # 8 USDT-M pairs metadata
├── core/                        # Backtest engine, indicators, data loaders
├── strategies/                  # Strategy implementations (backtesting)
├── research/                    # Phase-specific research scripts
├── data/                        # Download scripts, schema
├── live/                        # Paper trading system
│   ├── paper_trader.py          # Legacy single-strategy paper trader (ETH DT)
│   ├── paper_main.py            # Multi-strategy CLI entry point
│   ├── paper_api.py             # Binance.us API layer
│   ├── paper_portfolio.py       # State, risk, position management
│   ├── paper_strategies.py      # 4 strategy implementations
│   └── cron_multi.sh            # Cron job setup (8 jobs)
├── tests/                       # Unit tests
├── docs/
│   ├── methodology.md           # Research methodology, bias prevention
│   ├── data_dictionary.md       # Database schema documentation
│   ├── results/                 # Per-phase result reports (15 files)
│   └── strategies/              # Strategy specifications
└── pyproject.toml               # Package metadata
```

## Quick Start

### Requirements

- Python 3.10+
- SQLite3
- No external packages required for core backtesting (stdlib only)

### Download Data

```bash
# Download 1m candles for BTC and ETH
python data/download_candles.py --symbol BTCUSDT --start 2019-09-08
python data/download_candles.py --symbol ETHUSDT --start 2019-11-27

# Download sentiment data
python data/download_sentiment.py
```

### Run Backtests

```bash
# Reproduce the Dual Thrust results (Phase 15-16)
python research/phase_13_dual_thrust_cusum.py

# Run all research phases
python research/phase_01_session_correlation.py
python research/phase_02_v1_grid_search.py
# ... (see research/ directory)
```

### Paper Trading (Multi-Strategy)

```bash
# Check portfolio status
python live/paper_main.py status

# Manual commands (normally run via cron)
python live/paper_main.py scan_daily          # RSI2 + Pairs daily scan
python live/paper_main.py setup_dt london     # Dual Thrust London triggers
python live/paper_main.py setup_dt nyc        # Dual Thrust NYC triggers
python live/paper_main.py setup_ab            # Asia Breakout levels
python live/paper_main.py tick                # Check signals + monitor
python live/paper_main.py exit_session london # Time-exit DT London
python live/paper_main.py exit_session nyc    # Time-exit DT NYC
python live/paper_main.py exit_ab             # Time-exit Asia Breakout
```

### Paper Trading (Legacy Single-Strategy)

```bash
python live/paper_trader.py status
```

## Symbols

Paper trading runs across 8 Binance USDT-M perpetual futures pairs:

| Symbol | Backtested | Paper Trading |
|--------|-----------|---------------|
| BTCUSDT | Yes (6.3 years) | All 4 strategies |
| ETHUSDT | Yes (6.3 years) | All 4 strategies |
| SOLUSDT | No | Experimental |
| DOGEUSDT | No | Experimental |
| XRPUSDT | No | Experimental |
| AVAXUSDT | No | Experimental |
| LINKUSDT | No | Experimental |
| ADAUSDT | No | Experimental |

Only BTC and ETH have full backtest validation. The other 6 pairs are experimental -- the purpose of paper trading is to evaluate whether the strategies generalize.

## Data

All data is sourced from public Binance APIs:

| Dataset | Source | Records | Coverage |
|---------|--------|---------|----------|
| BTC 1m candles | Binance Futures | 3.4M | 2019-09 to 2026-03 |
| ETH 1m candles | Binance Futures | 3.3M | 2019-11 to 2026-03 |
| Fear and Greed Index | Alternative.me | 2,970 | 2018 to 2026 |
| Funding Rate | Binance Futures | 1,095/symbol | 365 days |

The database file (`futures_data.db`, ~1.1 GB) is excluded from the repository. Use the download scripts to reproduce it.

Paper trading uses live futures prices from `fapi.binance.com` (Binance USDT-M perpetual futures API). The system runs on a Raspberry Pi with direct API access to 609 futures symbols, trading 51 pairs across 4 strategies.

## Results Summary

### Top Strategies (6+ Year Validation, Fixed Position Size)

| Strategy | Pair | Annual % | Max DD | Ret/DD | Trades |
|----------|------|---------|--------|--------|--------|
| Dual Thrust (N3 K0.5 SMA200) | ETH | +39% | 12.4% | 19.63 | 488 |
| Pairs Trading (BTC/ETH) | Both | +33% | 8.7% | 3.79 | varies |
| Scale-In RSI(2) | ETH | +36.3% | 45.6% | 0.80 | 372 |
| Asia BRK + SMA200 | ETH | +15.4% | 37.8% | 0.41 | 631 |
| Std Error Bands | ETH | +11.5% | 25.5% | 0.45 | 137 |

### Strategies That Failed

| Category | Examples | Result |
|----------|----------|--------|
| ICT/Smart Money | FVG, CVD, Wyckoff, Order Blocks | -43% to -94% |
| Daily Momentum | TSMOM, MA crossovers, MACD | Negative after fees |
| Mean Reversion | RSI contrarian, Z-Score, 2-sigma | -57% to -89% |
| Scalping | Multi-trade, EMA scalp | Destroyed by fees |

## Documentation

- [Executive Summary](docs/results/00_executive_summary.md)
- [Methodology](docs/methodology.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Final Rankings](docs/results/14_final_rankings.md)
- [Dual Thrust Strategy Spec](docs/strategies/dual_thrust.md)
- [Full Phase Reports](docs/results/)

## Fee Model

All results are net of fees: taker 0.04% + slippage 0.01% per side (0.10% round-trip). Maker fees (0.02%) are not used; we conservatively assume taker fills on all orders.

## Disclaimer

This repository is for educational and research purposes only. It is not financial advice. Past performance does not guarantee future results. Cryptocurrency futures trading involves substantial risk of loss. The strategies documented here were tested on historical data and may not perform similarly in live markets due to market impact, execution delays, liquidity changes, and other factors not modeled in backtesting. Trade at your own risk.

## License

[MIT](LICENSE)
