# Research Methodology

## Data Sources

| Source | Data | Frequency | Coverage |
|--------|------|-----------|----------|
| Binance USDT-M Futures API | OHLCV candles (1m, 5m, 15m) | Per-candle | BTC: 2019-09 to 2026-03 (6.5yr), ETH: 2019-11 to 2026-03 (6.3yr) |
| Binance Futures API | Funding rate | 8-hourly | 365 days |
| Alternative.me API | Fear and Greed Index | Daily | 2018 to 2026 |
| Binance Futures API | Open interest, long/short ratio | 5-minute | ~28 days (limited history) |
| Derived from candle data | Taker buy ratio, volume metrics | Daily | Full candle coverage |

All data was downloaded directly from public APIs. No third-party data vendors were used. The database (futures_data.db, SQLite) contains 6.7M+ candle records across both symbols.

### Data Quality

- 1m candles were validated for gaps by checking consecutive open_time values. No significant gaps were found in the primary BTC and ETH datasets.
- Candle timestamps are in millisecond Unix epoch (UTC). All session definitions use UTC boundaries.
- Volume figures represent contract-denominated volume (USDT). Taker buy volume is reported separately by Binance.

## Backtesting Framework

### Engine Architecture

The backtest engine operates on minute-level precomputed price arrays for speed. For each trading day:

1. **Precompute:** Extract the day's 1m candle data into arrays (open, high, low, close, volume) indexed by minute offset from session start.
2. **Signal generation:** Compute entry signals using only data from prior days (shifted by one bar minimum).
3. **Simulate:** Walk through the minute arrays sequentially. Check entry conditions, then monitor for stop-loss, take-profit, or time-exit triggers at each minute.
4. **Record:** Log entry price, exit price, exit reason, P&L, and trade duration.

This architecture allows fast iteration (~1 second per 1,000 parameter combinations on a single core) while maintaining minute-level price path fidelity. The simulator does not use bar-level approximations for stop/TP detection; it checks the high and low of each 1m candle against the stop and target levels.

### Fee and Slippage Model

| Component | Rate | Applied |
|-----------|------|---------|
| Taker fee | 0.04% | On entry and exit |
| Maker fee | 0.02% | Not used (conservative: we assume taker fills) |
| Slippage estimate | 0.01% | On entry and exit |
| **Total round-trip** | **0.10%** | Per trade |

All reported returns are net of fees. The fee model is conservative (always taker) but does not account for:
- VIP tier discounts (which would improve results)
- BNB fee discounts
- Variable slippage under extreme volatility

## Look-Ahead Bias Prevention

### Signal Shift Protocol

Every signal function must use only data available at the time of trade entry. Specifically:

- `signal[t]` may access `data[t-1]`, `data[t-2]`, etc., but never `data[t]`.
- Daily indicators (SMA, EMA, RSI) are computed on the prior day's close, not the current day's close.
- Intraday indicators at entry hour H use candle data up to hour H-1 (the candle before entry, not the entry candle itself).

### The Phase 9 Incident

In Phase 9, the TSMOM_1d signal used `day["ret_1d"]`, computed as `(today's close - yesterday's close) / yesterday's close`. The field `today's close` was not available at 00:00 UTC when the trade was entered. This single bug:

- Produced an 84% win rate (real: ~50%)
- Produced +380% annual returns (real: -53%)
- Passed walk-forward validation (the bias affected both halves equally)
- Was only caught by building a second independent implementation that produced contradictory results

**Lesson:** Walk-forward validation is necessary but not sufficient. It does not detect systematic biases that affect all time periods. Independent code review and cross-implementation verification are essential.

### Current Safeguards

1. All signal functions explicitly receive `prev_days` (a list of prior day data) and may not access the current day's data.
2. The engine prints the signal value alongside the data timestamp at entry, enabling manual verification.
3. Two independent code paths were maintained for the final winning strategies.

## Walk-Forward Validation Protocol

### Standard Protocol

1. Split the data chronologically into two equal halves (50/50 split).
2. Optimize parameters on the first half (training period).
3. Run the best parameters on the second half (test period) without modification.
4. Compute Sharpe ratio on both halves.
5. Calculate degradation: `(train_sharpe - test_sharpe) / train_sharpe * 100`.

### Pass/Fail Criteria

- **PASS:** Degradation < 50% (test Sharpe is at least half of training Sharpe)
- **FAIL:** Degradation >= 50%
- **Negative degradation** (strategy improves in test): considered a strong pass, suggesting the edge is genuine and potentially growing.

### Limitations of the Protocol

- A single 50/50 split provides limited statistical power. K-fold cross-validation (not implemented) would be more robust.
- Walk-forward does not catch look-ahead bias if the bias exists in both periods (Phase 9).
- The 50% threshold is heuristic. There is no theoretical basis for this specific cutoff.

## Position Sizing Models

Three position sizing models were used across the research:

### Fixed Risk (Primary)

- Risk 2% of account per trade.
- Position size = (account * 0.02) / stop_distance.
- Maximum leverage: 10x.
- Used for most backtests and all final reported results.

### Fixed Size (For Comparison)

- Constant dollar position size regardless of account equity.
- Used to compute "fixed-size annual returns" which are comparable across strategies without compounding distortion.
- The +36.3% Scale-In RSI(2) return and +39% Dual Thrust return are fixed-size figures.

### Volatility Targeting (Tested in Phase 14)

- Target a fixed annualized volatility (e.g., 15%).
- Scale position size inversely to trailing 20-day realized volatility.
- Result: too conservative for these strategies. Did not improve risk-adjusted returns.

## What We Explicitly Do NOT Model

| Factor | Impact | Why Excluded |
|--------|--------|-------------|
| Market impact | Adverse price movement from own order | Negligible at retail size (<$10K). Would matter above $100K. |
| Partial fills | Order not fully filled | Assumed full fills. Optimistic for larger accounts. |
| Exchange outages | Binance downtime | Rare but can cause forced liquidations. Not modeled. |
| Funding rate P&L | 8-hourly funding payments | Strategies hold for hours, not days. Funding cost is small but nonzero. |
| Margin requirements | Varying margin ratios | Assumed sufficient margin at 10x leverage. |
| Network latency | Delay between signal and execution | Assumed instant execution. Real latency is 10-100ms. |
| Regulatory risk | Exchange restrictions, KYC changes | Cannot be modeled. |

## Statistical Significance

Sharpe ratios are reported without standard error bands in most phase reports. For reference, the standard error of an annualized Sharpe ratio is approximately `1 / sqrt(N_years)`. A Sharpe of 1.0 on 6 years has a standard error of ~0.41, making it marginally significant at the 95% confidence level.

The research prioritizes practical significance (is the strategy tradeable?) over statistical significance (is p < 0.05?). Many strategies with modest statistical significance may still be practically useful if their risk characteristics are acceptable.
