# Phase 5: Depth and Microstructure Analysis

## Objective

Determine whether order book depth proxies, trade intensity, and liquidation cascade metrics improve day trading strategy performance.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT
- Metrics computed per session per day from 1m candle data

## Metrics Computed

| Metric | Definition |
|--------|-----------|
| Price Impact | Total abs(price change) / volume. Measures book depth. |
| Spread Proxy | Avg (high - low) / midprice per candle. Measures bid-ask tightness. |
| Trade Intensity | Trades per minute. Activity level. |
| Avg Trade Size | Volume / trades. Institutional vs retail proxy. |
| Volume Surge | First 15/30 min volume vs session average. Opening activity. |
| Liquidation Cascades | Candles with >0.3% move AND >5x avg volume. |
| Institutional Flow % | Candles where avg trade size > 2x daily average. |

## Results

### Price Impact (Book Depth)

| Book Depth | BTC Up% | BTC Cont% | ETH Up% | ETH Cont% |
|------------|---------|-----------|---------|-----------|
| Very deep | 54.9% | 49.5% | 53.8% | 54.9% |
| Deep | 58.2% | 53.8% | 40.7% | 55.6% |
| Thin | 34.1% | 50.5% | 48.4% | 45.1% |
| Very thin | 48.4% | 49.5% | 41.8% | 50.5% |

Deep book (low impact) correlates with BTC being more likely to go up. Thin book environments are more volatile and less directional.

### Trade Size (Institutional Flow)

| Order Size | BTC Up% | ETH Up% | ETH Cont% |
|------------|---------|---------|-----------|
| Small (retail) | 41.8% | 44.0% | 49.5% |
| Medium | 47.3% | 45.1% | 49.7% |
| Large (institutional) | 59.3% | 50.5% | 57.1% |

Large orders during London are a bullish signal, especially on BTC (59.3% up).

### Liquidation Cascades

Cascade days do not predict reversal. Continuation rate remains approximately 51-52% regardless of cascade count. However, cascade days exhibit much higher volatility: 2.1% average absolute move vs 0.6% on calm days.

### Volume Surge

Weak predictor overall. NYC high surge shows slightly bullish BTC (57.1% up) but not ETH.

### Depth Filters on BTC TREND Baseline (Sharpe 2.60)

| Filter | Trades | Sharpe | Return | DD% | Delta Sharpe |
|--------|--------|--------|--------|-----|--------------|
| BASELINE | 363 | 2.60 | 147.6% | 15.4% | 0 |
| tight_spread | 182 | 3.00 | 88.8% | 7.6% | +0.40 |
| has_cascades | 231 | 2.78 | 153.4% | 13.7% | +0.18 |
| thin_book | 182 | 2.30 | 84.0% | 13.2% | -0.30 |
| no_cascades | 132 | -0.15 | -2.3% | 10.9% | -2.75 |

### Depth Filters on ETH TREND Baseline (Sharpe 3.21)

| Filter | Trades | Win% | Sharpe | Return | DD% |
|--------|--------|------|--------|--------|-----|
| BASELINE | 363 | 52.3% | 3.21 | 284.9% | 19.4% |
| tight_spread | 181 | 59.1% | 3.08 | 127.0% | 8.3% |
| deep + tight | 69 | 62.3% | 2.43 | 55.8% | 9.2% |
| thin + wide + surge | 21 | 71.4% | 2.39 | 35.5% | 7.0% |

ETH baseline is strong enough that most filters reduce absolute returns by cutting trade count, even when Sharpe improves.

## Key Findings

1. Tight spread is the best depth filter: +0.40 Sharpe on BTC with drawdown cut from 15.4% to 7.6%.
2. Trading only on days with liquidation cascades (has_cascades) improves Sharpe by +0.18. Avoiding cascade-free days (no_cascades) destroys the strategy (Sharpe -0.15).
3. Large institutional orders during London predict BTC bullishness at 59.3% accuracy.
4. Liquidation cascades do not predict direction (51-52% continuation) but do predict volatility (2.1% vs 0.6% average move).
5. ETH tight_spread filter improves win rate from 52.3% to 59.1% and cuts drawdown from 19.4% to 8.3%, at the cost of halving trade count.
6. Volume surge is not a reliable predictor on either pair.

## Limitations

- Spread proxy and price impact are approximations derived from OHLCV data, not actual order book snapshots. True bid-ask spread data would provide more precise measurements.
- "Institutional flow" is proxied by average trade size exceeding 2x daily average. This heuristic may misclassify algorithmic order splitting.
- The tight_spread filter halves the number of trades, reducing statistical confidence in the filtered results.
