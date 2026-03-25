# Phase 9-10: Quantitative Strategies (Invalidated and Corrected)

## Objective

Test time-series momentum (TSMOM), EMA trend, adaptive regime, and other quantitative strategies on 6+ years of data. Phase 9 produced extraordinary results that were later invalidated by a look-ahead bias bug. Phase 10 re-tested all strategies with corrected data access.

## Data

- Period: 2019-09 to 2026-03 (BTC 6.5 years, ETH 6.3 years)
- Symbols: BTCUSDT, ETHUSDT
- Combinations: 3,584 per pair (Phase 9), 17 configurations per pair (Phase 10)

## The Look-Ahead Bias Incident

### What Happened

The TSMOM_1d signal function used `day["ret_1d"]`, computed as `(today's close - yesterday's close)`. The problem: today's close is not known at 00:00 UTC when the trade is entered. The signal was using future information to determine trade direction.

### The Fake Results (Phase 9, INVALID)

| Metric | BTC | ETH |
|--------|-----|-----|
| Win rate | 84.3% | 82.9% |
| Annual return | +380% | +405% |
| Sharpe ratio | 15.21 | 16.98 |
| Profit factor | 10.21 | 9.8+ |

These numbers appeared to show the strongest signal across 24,000+ backtests. Walk-forward "passed" because look-ahead persisted in both halves. Every year showed 400-530% returns.

### How It Was Discovered

A separate implementation of the same strategy produced opposite results. Cross-validation between two independent code paths revealed the data access timing error. The `ret_1d` field included information from the trading day itself.

### The Corrected Results (Phase 10)

After fixing the signal to use only data available at entry time (yesterday's close vs day-before-yesterday's close):

| Strategy (FIXED) | BTC Annual | ETH Annual | Verdict |
|-------------------|-----------|-----------|---------|
| 1d momentum S3% R1 | -52.9% | -46.3% | Fails |
| 3d momentum S3% R1.5 | -3.8% | -14.4% | Fails |
| 20d momentum S3% R2 | +10.7% | -17.9% | BTC marginal |
| EMA20 trend S3% R2 | +2.5% | -8.4% | BTC breakeven |

Every daily momentum strategy loses money on crypto after the correction, with the exception of BTC 20-day momentum at +10.7%/yr, which barely exceeds buy-and-hold after fees.

## Strategies Tested (Phase 9, Results Invalid)

| # | Strategy | Concept |
|---|----------|---------|
| 1 | TSMOM (1d, 3d, 5d, 10d, 20d, 50d) | Time-series momentum |
| 2 | EMA Trend (10, 20, 50) | Long above EMA, short below |
| 3 | Adaptive Regime | Switch momentum/mean-reversion based on volatility |
| 4 | Weekend/Weekday Only | Calendar-based filtering |
| 5 | Close-to-Close Momentum | Yesterday up, go long today |
| 6 | RSI Mean Reversion | Buy RSI<30, sell RSI>70 |
| 7 | RSI Momentum | Buy RSI>55, sell RSI<45 |
| 8 | Monthly Turn-of-Month | Long during last/first 3 days of month |
| 9 | Vol-Scaled Momentum | Momentum with volatility position sizing |
| 10 | Dual Momentum (Long-Only) | Long if positive return, else flat |
| 11 | N-Day Breakout | Buy new 10/20/50-day highs, sell new lows |

### Strategies That Failed Even With Look-Ahead (Phase 9)

| Strategy | Result | Reason |
|----------|--------|--------|
| RSI Mean Reversion | -89% total | Crypto does not mean-revert daily |
| Close-to-Close Momentum | -88% total | Too naive, no stop management |
| Monthly Calendar | +14% total | Marginal, not tradeable |

## Key Findings

1. Look-ahead bias is the single most dangerous bug in backtesting. One data access error produced a fake 84% win rate and +380% annual return.
2. After correction, every daily momentum strategy loses money on crypto. Daily crypto price movements do not exhibit tradeable positive autocorrelation after fees.
3. Walk-forward validation does not catch look-ahead bias if the bias exists in both the training and test periods.
4. Cross-validation between independent implementations is essential. The bug was caught only because a second code path produced contradictory results.
5. BTC 20-day momentum (+10.7%/yr) is the only marginally positive result after correction, barely exceeding buy-and-hold.
6. RSI mean reversion lost 89% of capital on 6 years of crypto data, confirming that crypto trends rather than mean-reverts at the daily timeframe.

## Lessons for Practitioners

- Always verify that `signal[t]` uses only `data[t-1]` or earlier. Print the signal alongside the data it accesses.
- If results seem too good to be true (Sharpe >10, 84% win rate on daily data), they probably are.
- Build two independent implementations and compare outputs. If they disagree, one has a bug.
- Walk-forward validation is necessary but not sufficient. It does not detect systematic biases that affect all time periods equally.

## Limitations

- Phase 10 tested only 17 configurations per pair (the most promising from Phase 9). A broader grid search with corrected data was not conducted.
- The +10.7% BTC 20-day momentum result has a wide confidence interval given the small number of independent trades over 6 years.
- This phase tested daily-frequency signals only. Intraday momentum (which proved effective in session strategies) operates on a different mechanism.
