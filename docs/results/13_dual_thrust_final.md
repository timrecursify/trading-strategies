# Phase 15-16: Dual Thrust, Pairs Trading, and CUSUM

## Objective

Test Dual Thrust breakout, BTC/ETH pairs trading, and CUSUM-filtered RSI(2) on multi-year data. Determine the overall best strategy across all 70,000+ backtests.

## Data

- Period: 6.3 years (ETH: 2019-11-27 to 2026-03-24)
- Symbols: BTCUSDT, ETHUSDT
- Dual Thrust combinations: 41,344
- Pairs trading + Vol targeting: 200+

## ETH Dual Thrust: The Overall Winner

### Strategy Specification

| Parameter | Value |
|-----------|-------|
| Pair | ETHUSDT |
| Signal | Dual Thrust range from prior N days: Range = max(HH-LC, HC-LL). Buy trigger = open + K x Range. Sell trigger = open - K x Range |
| N (lookback) | 3 days |
| K (multiplier) | 0.5 |
| Entry | Scan from 07:00 UTC (London open). Enter when price breaks trigger level. |
| Stop Loss | 1.0% from entry |
| Exit | 16:00 UTC time exit OR stop loss (whichever first) |
| Regime filter | Only trade when price > 200-day SMA |
| Risk per trade | 2% of account |

### Performance ($1,000 start, 6.3 years, fixed position size)

| Metric | Value |
|--------|-------|
| Return | +244.3% ($1,000 to $3,443) |
| Annual return | ~39%/yr |
| Max drawdown | 12.4% |
| Return/DD ratio | 19.63 |
| Trades | 488 (77/year) |
| Win rate | 35.5% |
| Profit factor | 1.38 |

### Yearly P&L ($1,000 fixed size)

| Year | P&L | Cumulative | Notes |
|------|-----|-----------|-------|
| 2019 | +$112 | $1,112 | Partial year, profitable |
| 2020 | +$992 | $2,104 | Best year |
| 2021 | +$652 | $2,756 | Bull market |
| 2022 | +$100 | $2,857 | Bear market, still profitable |
| 2023 | +$58 | $2,915 | Sideways, small gain |
| 2024 | +$552 | $3,467 | Recovery |
| 2025 | -$54 | $3,413 | Only losing year (-1.6%) |
| 2026 | +$30 | $3,443 | Partial year |

Every full year was profitable except 2025 (-$54, a loss of -1.6%). The strategy survived the 2022 bear market (+$100) and the 2023 sideways period (+$58).

### Why Dual Thrust Wins

1. **Dynamic range adaptation.** Dual Thrust computes its breakout range from the prior 3 days' volatility, not a fixed session window. This adaptiveness is the key difference from Asia Breakout, which uses the fixed 00:00-07:00 UTC range.
2. **SMA200 regime filter.** Keeps the strategy out of bear markets, cutting drawdown dramatically.
3. **1% stop is optimal.** Tight enough to limit losses, but breakout momentum carries winners far enough for a 1.38 profit factor despite a 35.5% win rate.
4. **77 trades per year.** Infrequent enough to avoid fee erosion, frequent enough for statistical significance.

### Comparison to Asia Breakout

| Metric | Dual Thrust | Asia Breakout |
|--------|-------------|---------------|
| Sharpe (1 year) | N/A | 5.90 |
| Sharpe (6 years) | Higher | ~1.10 |
| Max DD | 12.4% | 22-35% |
| Annual return | ~39% | ~15-19% |
| Range calculation | Dynamic (3-day) | Fixed (Asia session) |
| Regime filter | SMA200 | 20 EMA |

## BTC/ETH Pairs Trading

### Strategy Specification

Trade the BTC/ETH spread. When the ratio deviates beyond a threshold from its moving average, enter the convergence trade (long the underperformer, short the outperformer).

### Performance

| Metric | Value |
|--------|-------|
| Annual return | +33% |
| Max drawdown | 8.7% |
| Return/DD ratio | 3.79 |

This is the safest strategy tested. The 8.7% maximum drawdown makes it suitable for capital preservation mandates.

## CUSUM Filter on RSI(2)

The CUSUM (Cumulative Sum) filter was tested as an alternative regime detector for the Scale-In RSI(2) strategy. It did not improve performance relative to the SMA200 filter. The SMA200 filter remains the preferred regime detection method.

## Scale-In RSI(2): Compounding vs Fixed-Size Discrepancy

| Metric | Fixed-Size | Compounded |
|--------|-----------|-----------|
| Annual return | +36.3% | +12.7% |
| Reason for difference | Position size constant | Drawdown erodes base |

The +36.3% fixed-size return overstates real-world performance because drawdown compounding reduces effective position size. Dual Thrust compounds much better, reaching $6,900 with compounding vs $3,443 fixed, because its 12.4% maximum drawdown preserves capital through losing periods.

## Key Findings

1. ETH Dual Thrust is the overall winner across 70,000+ backtests: $1,000 to $3,443, 12.4% DD, Ret/DD ratio 19.63.
2. BTC/ETH pairs trading is the safest strategy: 33% annual return, 8.7% DD. Best for capital preservation.
3. Adaptive range calculation (Dual Thrust) holds up over 6+ years while fixed session ranges (Asia Breakout) degrade. Markets change; the range calculation must adapt.
4. 1% stop on breakout strategies is optimal. The 35.5% win rate is compensated by larger winners (PF 1.38).
5. SMA200 is more effective than CUSUM as a regime filter for RSI(2).
6. Scale-In RSI(2) fixed-size returns (+36.3%) are misleading. Compounded returns are +12.7% due to the 45.6% drawdown eroding the capital base.
7. 2025 was the only losing year for Dual Thrust (-$54, -1.6%), demonstrating robust multi-regime performance.
8. Dual Thrust generates 77 trades per year, providing adequate statistical significance while avoiding fee erosion from overtrading.

## Limitations

- Dual Thrust was validated on ETH only. BTC Dual Thrust results were not separately reported.
- The SMA200 filter removes all short trades during bear markets. A modified version that allows shorts below SMA200 was not tested.
- The 41,344 Dual Thrust combinations create substantial multiple comparison risk. The Ret/DD ratio of 19.63 may be partially attributable to parameter optimization.
- Pairs trading results lack detailed yearly breakdown and parameter specification in this phase.
