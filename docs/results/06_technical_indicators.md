# Phase 6: Technical Indicator Analysis

## Objective

Evaluate 11 technical indicators as standalone predictors and as filters on winning strategies, to determine which indicators (if any) provide incremental edge on crypto futures.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT
- Timeframe: 15m for indicator computation, evaluated at NYC open (12:00 UTC)

## Indicators Tested

| Indicator | Type | Parameters |
|-----------|------|------------|
| RSI | Momentum | Period 14, Period 7 |
| MACD | Trend/Momentum | 12/26/9 |
| Bollinger Bands | Volatility | 20-period, 2 sigma |
| BB %B | Mean Reversion | Position within bands |
| BB Bandwidth | Volatility Regime | Band width as % of price |
| ADX | Trend Strength | Period 14 |
| Stochastic %K/%D | Momentum | 14/3 |
| VWAP | Fair Value | Intraday, volume-weighted |
| OBV | Volume Trend | On-Balance Volume vs 20 EMA |
| EMA Cross 9/21 | Trend | Short-term cross |
| EMA Cross 12/26 | Trend | Medium-term cross |

## Standalone Indicator Results

### RSI(14) at NYC Open

| RSI Level | BTC Up% | BTC Cont% | ETH Up% | ETH Cont% |
|-----------|---------|-----------|---------|-----------|
| Oversold (<30) | 38.5% | 61.5% | 37.5% | 62.5% |
| Weak (30 to 45) | 52.5% | 45.5% | 40.0% | 53.3% |
| Neutral (45 to 55) | 44.6% | 54.0% | 46.8% | 54.0% |
| Strong (55 to 70) | 50.0% | 48.0% | 50.5% | 45.0% |
| Overbought (>70) | 72.7% | 72.7% | 63.6% | 54.5% |

Overbought RSI on BTC is actually bullish (72.7% up), indicating momentum continuation rather than mean reversion.

### ADX (Trend Strength)

| ADX Level | BTC Cont% | ETH Cont% |
|-----------|-----------|-----------|
| No trend (<20) | 62.2% | 50.0% |
| Weak (20 to 30) | 44.5% | 42.9% |
| Strong (30 to 50) | 51.7% | 57.8% |
| Very strong (>50) | 54.8% | 52.5% |

BTC shows highest continuation in quiet markets (ADX <20, 62.2%). ETH favors trending markets (ADX 30-50, 57.8%).

### VWAP Direction

| Signal | BTC Up% | ETH Up% |
|--------|---------|---------|
| Price > VWAP | 49.2% | 46.6% |
| Price < VWAP | 48.6% | 45.7% |

VWAP alone has no directional edge on either pair.

## Indicator Filters on Winning Strategies

### BTC TREND 12:00 2.0% 3R X20 (Baseline Sharpe: 2.62)

**Top 5 filters:**

| # | Filter | Trades | Win% | PF | Return | Sharpe | DD% | Delta Sharpe |
|---|--------|--------|------|----|--------|--------|-----|--------------|
| 1 | bb_squeeze | 328 | 54.0% | 1.62 | 127.3% | 3.12 | 8.6% | +0.50 |
| 2 | adx_weak (<20) | 45 | 64.4% | 4.36 | 29.9% | 2.77 | 2.1% | +0.16 |
| 3 | bb_lower_half | 177 | 55.4% | 1.86 | 81.0% | 2.75 | 8.4% | +0.14 |
| 4 | rsi14_not_os (>30) | 350 | 53.1% | 1.48 | 108.7% | 2.67 | 10.5% | +0.05 |
| 5 | stoch_not_ob (<80) | 291 | 52.6% | 1.60 | 97.5% | 2.66 | 10.1% | +0.04 |

**Bottom 5 filters (destroy the strategy):**

| # | Filter | Sharpe | Delta Sharpe | Reason |
|---|--------|--------|--------------|--------|
| 1 | adx_strong (>35) | -0.09 | -2.70 | Trending = already moved |
| 2 | obv_up | 0.33 | -2.29 | Splits signal in half |
| 3 | bb_upper_half | 0.83 | -1.79 | Removes dip-buying opportunities |
| 4 | rsi+macd_confirms | 0.87 | -1.75 | Over-filtered |
| 5 | rsi14_strong (>55) | 1.14 | -1.48 | Too restrictive |

### ETH TREND 12:00 1.5% 3R X20 (Baseline Sharpe: 2.58)

| # | Filter | Trades | Win% | PF | Return | Sharpe | DD% | Delta Sharpe |
|---|--------|--------|------|----|--------|--------|-----|--------------|
| 1 | stoch_not_ob (<80) | 312 | 48.7% | 1.64 | 278.4% | 3.02 | 18.2% | +0.44 |
| 2 | ema9_21_confirms | 201 | 48.3% | 1.71 | 201.8% | 2.94 | 18.6% | +0.36 |
| 3 | vwap_confirms | 193 | 47.2% | 1.65 | 169.8% | 2.70 | 12.9% | +0.12 |
| 4 | obv_confirms | 175 | 50.9% | 1.84 | 144.6% | 2.67 | 20.8% | +0.09 |
| 5 | adx_weak | 38 | 68.4% | 3.19 | 50.8% | 2.60 | 8.8% | +0.02 |

### ETH TREND 12:00 2.0% 3R X20 (Baseline Sharpe: 3.21)

| # | Filter | Trades | Sharpe | Delta Sharpe |
|---|--------|--------|--------|--------------|
| 1 | stoch_not_ob | 312 | 3.53 | +0.32 |
| 2 | ema9_21_confirms | 201 | 3.28 | +0.07 |
| 3 | rsi14_not_os | 355 | 3.25 | +0.04 |

## Critical Finding: BTC and ETH Need Different Indicators

| Aspect | BTC Best Filter | ETH Best Filter |
|--------|----------------|-----------------|
| #1 indicator | BB Squeeze (+0.50) | Stoch not OB (+0.44) |
| Logic | Enter when volatility is low, ride expansion | Avoid entering when momentum is exhausted |
| #2 indicator | BB lower half (+0.14) | EMA 9/21 confirms (+0.36) |
| Logic | Buy the dip within trend | Enter with short-term momentum aligned |
| Worst filter | ADX strong (-2.70) | RSI+BB+ADX combo (-2.68) |
| Lesson | Do not chase strong trends | Do not over-filter |

## Full Confluence: Why It Fails

Testing "full confluence" (ADX trending + VWAP confirms + MACD confirms + EMA aligned):

| Pair | Trades | Sharpe | Delta Sharpe |
|------|--------|--------|--------------|
| BTC | 129 | 1.43 | -1.19 |
| ETH | 135 | 1.54 | -1.04 |

Each filter cuts approximately 50% of trades. Four filters combined reduce the sample to 1/16th of original trades, eliminating statistical significance while providing no improvement.

## Key Findings

1. BB Squeeze is the best indicator filter for BTC, improving Sharpe from 2.62 to 3.12 (+0.50) while cutting drawdown from 10.5% to 8.6%.
2. Stochastic not overbought (<80) is the best filter for ETH, improving Sharpe from 2.58 to 3.02 (+0.44).
3. BTC and ETH respond to different indicators. Applying the same indicator set to both pairs is suboptimal.
4. Full confluence (4+ indicators) fails. More filters do not equal better results; they reduce trade count below statistical significance thresholds.
5. VWAP alone has zero directional edge (49.2% vs 48.6% on BTC).
6. Overbought RSI on BTC is bullish (72.7%), not bearish. Standard mean-reversion interpretations do not apply to crypto momentum.
7. ADX strong (>35) is the worst BTC filter (Sharpe -0.09, delta -2.70), indicating that chasing established trends is counterproductive.

## Limitations

- Indicators were computed on 15m timeframe only. Different timeframes may produce different results.
- The adx_weak filter has only 45 trades, providing low statistical confidence despite a high Sharpe.
- All indicator filters are tested on 1 year of data. Multi-year robustness of these filters was not evaluated in this phase.
