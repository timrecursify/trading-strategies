# Research Phases

Each script in this directory reproduces one phase of the backtesting research.
Scripts import from `core/` and `strategies/` and can be run independently.

**Requirements:** The `futures_data.db` database must exist in the project root.
Run `data/download_candles.py` first if the database is missing.

## Phase Index

| Script | Phase | What It Tests | Key Finding |
|--------|-------|---------------|-------------|
| phase_01_session_correlation.py | 1 | London to NYC continuation | 51%, not significant |
| phase_02_v1_grid_search.py | 2 | 4,180 session strategy combos | BTC fails walk-forward |
| phase_03_alternative_strategies.py | 3 | Trend, Asia BRK, scalping | Asia BRK Sharpe 5.90 (1yr) |
| phase_04_sentiment_onchain.py | 4 | Fear/Greed, funding rate | Funding contrarian +0.42 |
| phase_05_depth_microstructure.py | 5 | Volume impact, spread proxy | Tight spread +0.40 |
| phase_06_technical_indicators.py | 6 | 11 indicators as filters | BB Squeeze +0.50 BTC |
| phase_07_advanced_22_strategies.py | 7 | ICT, VWAP+FR, Range Comp | FVG fails, VWAP+FR works |
| phase_08_multiyear_validation.py | 8 | Asia BRK on 6.3 years | Sharpe 5.90 to 1.10 |
| phase_09_quant_invalidated.py | 9 | TSMOM look-ahead bias | Fake 84% win rate caught |
| phase_10_sharp_research.py | 10 | RSI+BB(1s), 2-sigma rev | Both fail on crypto |
| phase_11_channels_alpha.py | 11 | IBS, RSI(2), Scale-In | Scale-In RSI(2) +36% |
| phase_12_drawdown_reduction.py | 12 | SMA filters, vol targeting | SMA200 cuts DD to 10% |
| phase_13_dual_thrust_cusum.py | 13 | Dual Thrust, CUSUM, Pairs | DT $1K to $3.4K winner |

## Running

```bash
# Run a single phase
python research/phase_13_dual_thrust_cusum.py

# Run all phases sequentially
for f in research/phase_*.py; do python "$f"; done
```
