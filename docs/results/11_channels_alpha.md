# Phase 12-13: Channels-Alpha Comprehensive Batch Tests

## Objective

Test 12 additional strategies from Quantified Strategies, KJ Trading, CryptoCred, and QuantPy research on 6+ years of data. 232 parameter combinations across both pairs with properly shifted signals.

## Data

- Period: 6+ years (2019 to 2026)
- Symbols: BTCUSDT, ETHUSDT
- Batch 1: 112 configurations per pair
- Batch 2: 120+ configurations per pair

## Results

### Batch 1: REX, Donchian+ADX, IBS, Williams %R, RSI(2)

| Strategy | Best Pair | Annual% | Win% | Trades | Max DD | Notes |
|----------|-----------|---------|------|--------|--------|-------|
| IBS(2) < 0.3 | ETH | +7.8% | 42.2% | 251 | 43.1% | New metric, works |
| RSI(2) < 10 | ETH | +6.6% | 50.7% | 227 | 34.0% | Short RSI outperforms RSI(14) |
| Donchian(20)+ADX<30 | BTC | +4.8% | 47.8% | 134 | 12.4% | Low DD, fewer trades |
| REX(50) | ETH | +4.7% | 42.5% | 127 | 26.2% | Crypto-specific indicator |
| Williams %R | Both | Negative | ~45% | varies | varies | Fails on crypto |

IBS (Internal Bar Strength) measures where the close sits within the day's range. Low IBS (closed near the low) indicates short-term oversold conditions.

### Batch 2: Candlestick, Scale-In, SMA200, Zaratini

| Strategy | Best Pair | Annual% | Win% | Trades | Max DD | Notes |
|----------|-----------|---------|------|--------|--------|-------|
| Scale-In RSI(2)<10 | ETH | +36.3% | 45.7% | 372 | 45.6% | Fixed-size returns |
| Scale-In RSI(2)<10 | BTC | +30.7% | 53.2% | 380 | varies | Works on both pairs |
| Asia BRK + SMA200 | ETH | +15.4% | 45.8% | 631 | 37.8% | Improved from 20 EMA |
| Std Error Bands (N50 K1.5) | ETH | +11.5% | 52.6% | 137 | 25.5% | New concept works |
| Zaratini Intraday Mom | ETH | +8.7% | 46.8% | 594 | 76.9% | High DD kills it |
| Stoch %D<20 + IBS<0.5 | ETH | +5.0% | 58.2% | 110 | 24.1% | Decent combo |
| Bearish Engulf + SMA200 | ETH | +4.1% | 57.8% | 45 | 10.9% | Too few trades |
| Williams VIX Fix | BTC | -5.1% | 48.3% | 149 | 48.3% | Fails |

### Scale-In RSI(2): The Mechanism

When RSI(2) drops below 10 (extreme oversold on a 2-day window), enter with 50% of the intended position. If the 5-day RSI drops further (>5 points), add the remaining 50%. Exit when close exceeds yesterday's high.

The non-scaled RSI(2) was negative. The scaling mechanism is the key differentiator: it improves average entry price by adding to weakness.

### Scale-In RSI(2) Yearly Breakdown: ETH (3% stop)

| Year | Return | Notes |
|------|--------|-------|
| 2019 | -9.9% | Partial year, loss |
| 2020 | +91.5% | COVID recovery |
| 2021 | +113.3% | Bull market peak |
| 2022 | +0.9% | Bear market, survived flat |
| 2023 | +6.3% | Sideways, small gain |
| 2024 | +15.9% | Recovery |
| 2025 | +53.8% | Strong |
| 2026 | +18.5% | Partial year |

5 of 7 full years profitable. 2022 bear market was flat rather than a loss. Drawdown of 45.6% is the primary concern.

### Scale-In RSI(2) Yearly Breakdown: BTC (3% stop)

| Year | Return |
|------|--------|
| 2019 | +13.2% |
| 2020 | +56.3% |
| 2021 | +89.6% |
| 2022 | +10.8% |
| 2023 | +33.0% |
| 2024 | +79.6% |
| 2025 | -24.0% |
| 2026 | -12.6% |

BTC shows recent degradation (2025-2026 negative). ETH is more consistent.

### Bearish Engulfing as Buy Signal

The bearish engulfing pattern followed by a buy entry returned +4.1% annually on ETH with SMA200 filter. The counterintuitive direction (buying after a bearish pattern) works because the pattern often marks short-term exhaustion in an uptrend.

## Key Findings

1. Scale-In RSI(2) produces +36.3%/yr on ETH (fixed-size), the highest return of any multi-year validated strategy at this point in the research.
2. The scaling mechanism transforms a losing strategy (plain RSI(2) is negative) into a winner (+36.3%/yr). Better average entry prices are the key.
3. IBS(2) < 0.3 at +7.8% annually on ETH introduces a new metric not previously tested. It outperforms Williams %R and other oscillators.
4. Donchian(20) + ADX<30 on BTC produces +4.8%/yr with only 12.4% drawdown. Low returns but very low risk.
5. Scale-In RSI(2) fixed-size returns (+36.3%) significantly overstate compounded performance (+12.7%), because drawdown compounding erodes the effective position size. See Phase 15-16 for this analysis.
6. BTC Scale-In RSI(2) shows degradation in 2025-2026 (-24%, -12.6%), raising concerns about regime dependency.
7. Williams %R and Williams VIX Fix both fail on crypto.

## Limitations

- Scale-In RSI(2) has 45.6% maximum drawdown. This is unacceptable for most live trading accounts without significant drawdown reduction measures.
- Fixed-size annual returns overstate real-world compounded performance. The +36.3% headline is misleading for a strategy with 45% drawdown.
- Bearish Engulf + SMA200 has only 45 trades over 6 years, providing minimal statistical confidence.
- All strategies in this phase are long-only or long-biased. Short-side performance was not independently evaluated.
