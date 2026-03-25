# Phase 2: V1 Strategy Grid Search

## Objective

Systematically search 4,180 parameter combinations per symbol to find profitable session-based day trading strategies.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT
- Candles: 1m
- Combinations: 4 strategy variants x 5 entry times x 11 stop types x 19 exit types = 4,180 per symbol

## Strategy Variants

- **Variant A:** London direction continuation (trade every day)
- **Variant B:** London range breakout (trade only on breakout days)
- **Variant C:** 3-session alignment (Asia + London must agree)
- **Variant D:** Judas swing reversal (fade London fakeout)

## Results

### BTC Top 5 by Sharpe

| # | Strategy | Trades | Win% | PF | Return | Sharpe | DD% |
|---|----------|--------|------|----|--------|--------|-----|
| 1 | VC 12:30 2.0% stop, 3:1 R:R | 169 | 47.3% | 1.30 | 27.5% | 1.18 | 17.5% |
| 2 | VC 14:00 2.0% stop, 3:1 R:R | 169 | 49.1% | 1.29 | 25.8% | 1.17 | 17.7% |
| 3 | VC 14:00 2.0% stop, exit 20:00 | 169 | 47.9% | 1.29 | 23.2% | 1.12 | 15.0% |
| 4 | VC 12:30 2.0% stop, exit 20:00 | 169 | 47.9% | 1.28 | 24.2% | 1.08 | 17.4% |
| 5 | VA 12:30 1.5% stop, exit 20:00 | 364 | 46.2% | 1.14 | 33.7% | 0.96 | 22.6% |

### ETH Top 5 by Sharpe

| # | Strategy | Trades | Win% | PF | Return | Sharpe | DD% |
|---|----------|--------|------|----|--------|--------|-----|
| 1 | VC 13:30 0.75% stop, exit 20:00 | 183 | 36.6% | 1.56 | 212.0% | 1.97 | 28.6% |
| 2 | VB 12:30 0.75% stop, 1.5:1 R:R | 78 | 56.4% | 1.54 | 47.4% | 1.86 | 12.9% |
| 3 | VC 13:00 1.5% stop, exit 20:00 | 183 | 44.8% | 1.44 | 93.3% | 1.85 | 17.2% |
| 4 | VC 12:30 2.0% stop, exit 20:00 | 183 | 48.1% | 1.43 | 71.9% | 1.81 | 14.6% |
| 5 | VC 14:00 ATR x 2.0 stop, 1.5:1 R:R | 183 | 51.4% | 1.29 | 70.1% | 1.79 | 18.9% |

## Walk-Forward Validation

**BTC: All top 5 failed.** Performance was driven by the Jan-Mar 2026 rally. Trained on H1 (months 1-6) showed negative returns; H2 showed positive. The strategies are not robust.

**ETH: Top 4 passed.** Strategy #1 degradation was -94% (performance improved in the test period). Consistent across both halves.

## Filter Analysis

| Filter | BTC Delta Sharpe | ETH Delta Sharpe | Notes |
|--------|-----------------|-----------------|-------|
| trend_ema | +1.40 | +0.39 to +0.84 | Best single filter |
| skip_wed (ETH) | N/A | +0.16 to +0.48 | ETH Wednesdays are adverse |
| hi_vol | +0.67 | -0.02 | Strong for BTC only |
| skip_sat | +0.20 | varies | Weekends weaker |

The trend_ema filter (trade only in the direction of the 20 EMA) was the single biggest improvement across all strategies.

## Key Findings

1. Variant C (3-session alignment) dominates both pairs, producing 4 of the top 5 on each.
2. BTC session strategies do not survive walk-forward testing on this 1-year sample.
3. ETH shows a genuine edge with Variant C and tight stops (0.75% stop produced Sharpe 1.97).
4. The trend_ema filter improves BTC Sharpe by +1.40, the largest single enhancement found in this phase.
5. ETH responds to skipping Wednesdays (+0.16 to +0.48 Sharpe), consistent with Phase 1 day-of-week findings.
6. The best BTC Sharpe of 1.18 is marginal for live trading, below the commonly used threshold of 1.5.

## Limitations

- All results are on 1 year of data. Multi-year validation (conducted in Phase 8) later showed significant degradation.
- Walk-forward uses a single 50/50 split. A k-fold approach would provide more robust estimates.
- The grid search tests 4,180 combinations, creating substantial multiple comparison risk. The best results may be partially attributable to random variation.
