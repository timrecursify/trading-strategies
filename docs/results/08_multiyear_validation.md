# Phase 8: Multi-Year Validation

## Objective

Extend backtests from 1 year to 6.3 years to determine which strategies survive across multiple market regimes (bull, bear, sideways).

## Data

| Symbol | 1m Candles | Period | Years |
|--------|-----------|--------|-------|
| BTCUSDT | 3,440,375 | 2019-09-08 to 2026-03-24 | 6.5 |
| ETHUSDT | 3,325,788 | 2019-11-27 to 2026-03-24 | 6.3 |

## Methodology

The top strategies from Phases 1-7 were re-run on the full 6.3-year ETH dataset. Results were compared against 1-year performance to measure period dependency. Walk-forward validation used a 50/50 chronological split on the full dataset.

## Results

### Asia Breakout: 1-Year vs 6-Year Comparison

| Metric | 1-Year (2025-2026) | 6-Year (2019-2026) | Change |
|--------|-------------------|-------------------|--------|
| Best Sharpe (no filter) | 5.90 | 0.64 | -89% |
| Best Sharpe (trend filter) | Not tested | 1.10 | N/A |
| Win rate | 62.5% | 44-47% | -15 ppt |
| Max drawdown | 14.7% | 22-35% | +50 to +140% |
| $100 final (best) | $1,690 | $549 | -67% |

The 2025-2026 period was exceptionally favorable for Asia Breakout. The strategy is real but Sharpe ~1.0 is the honest long-term expectation.

### Best Multi-Year Variants (6.3 Years, ETH)

| # | Strategy | Trades | Win% | PF | Return | Sharpe | DD% |
|---|----------|--------|------|----|--------|--------|-----|
| 1 | TREND S1.0% R3.0 X12h | 754 | 44.2% | 1.19 | 449% | 1.10 | 34.7% |
| 2 | TREND S2.0% R1.5 X12h | 754 | 47.6% | 1.23 | 164% | 1.06 | 21.4% |
| 3 | TREND S1.5% R2.0 X12h | 754 | 46.3% | 1.21 | 227% | 1.03 | 26.5% |
| 4 | TREND S2.0% R3.0 X12h | 754 | 46.6% | 1.25 | 191% | 1.02 | 22.9% |
| 5 | TREND S2.0% R2.0 X12h | 754 | 46.8% | 1.22 | 146% | 0.94 | 25.3% |

All top 5 use the trend filter (only trade breakouts in the direction of the 20 EMA). Without the trend filter, performance is substantially worse.

### Yearly Performance: TREND S2.0% R3.0 X12h

| Year | P&L | Market Regime |
|------|-----|---------------|
| 2019 | -$2.15 | Partial year |
| 2020 | +$53.90 | COVID crash + recovery |
| 2021 | +$18.29 | Bull market |
| 2022 | +$71.95 | Bear market (best year) |
| 2023 | +$4.14 | Sideways (worst) |
| 2024 | +$16.29 | Recovery |
| 2025 | +$26.19 | Bull |
| 2026 | +$2.25 | Partial year |

The strategy works in both bull and bear markets. It struggles in sideways/ranging conditions (2023).

### Walk-Forward on 6 Years

| Strategy | Train Sharpe | Test Sharpe | Degradation | Verdict |
|----------|-------------|-------------|-------------|---------|
| TREND S2.0% R2.0 X12h | 1.19 | 0.62 | 48% | PASS |
| TREND S1.0% R3.0 X12h | 1.58 | 0.47 | 70% | FAIL |
| TREND S2.0% R1.5 X12h | 1.41 | 0.59 | 58% | FAIL |

Only one variant passes the 50% degradation threshold on the full 6-year walk-forward.

## Key Findings

1. 1-year backtests are dangerously misleading. Asia Breakout Sharpe degraded from 5.90 (1 year) to 0.64 (6 years), a 89% reduction.
2. The trend filter is essential for multi-year viability. All top 5 strategies on 6.3 years require the 20 EMA trend filter.
3. Sideways markets (2023) are the hardest regime. TREND S2.0% R3.0 produced only +$4.14 in 2023 vs +$71.95 in 2022.
4. Bear market performance is strong. 2022 was the best year (+$71.95), confirming the strategy captures both long and short opportunities.
5. Walk-forward degradation is severe on 6 years: only 1 of 3 tested variants passes the 50% threshold.
6. Win rates drop by approximately 15 percentage points when moving from 1-year to 6-year evaluation.

## Limitations

- Multi-year validation was conducted on ETH only. BTC multi-year results for these specific variants were not computed in this phase.
- The trend filter itself (20 EMA) may be subject to parameter sensitivity. Alternative trend definitions (SMA, longer periods) were not tested here.
- Early data (2019) may have different liquidity characteristics than recent data, affecting fill quality assumptions.
