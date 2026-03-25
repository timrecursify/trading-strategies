# Phase 4: Sentiment and On-Chain Analysis

## Objective

Evaluate whether sentiment and on-chain data (Fear and Greed Index, funding rate, taker buy ratio) improve existing strategy performance as filters.

## Data

| Source | Records | Coverage | Cost |
|--------|---------|----------|------|
| Fear and Greed Index (Alternative.me) | 2,970 | 2018 to 2026 (365 days used) | Free |
| Binance Funding Rate | 1,095/symbol | 365 days | Free |
| Binance Open Interest | 672/symbol | ~28 days | Free (limited) |
| Binance Long/Short Ratio | 672/symbol | ~28 days | Free (limited) |
| Taker Buy Ratio (from candle data) | 364 days/symbol | Full period | Already collected |

## Methodology

Each sentiment indicator was tested as a standalone directional predictor and as a filter on the BTC TREND 12:00 1.5% 3:1 X20 baseline strategy (Sharpe 2.60). Filters were applied by restricting trades to days meeting the sentiment condition.

## Results

### Fear and Greed Index Distribution (365 Days)

| Classification | Days | % |
|----------------|------|---|
| Extreme Fear (0 to 24) | 117 | 32% |
| Fear (25 to 44) | 80 | 22% |
| Neutral (45 to 55) | 48 | 13% |
| Greed (56 to 74) | 118 | 32% |
| Extreme Greed (75 to 100) | 2 | 1% |

### Fear and Greed Standalone Correlations

| Signal | BTC Win% | ETH Win% | Tradeable? |
|--------|----------|----------|------------|
| Extreme Fear, buy | 47.7% | 47.7% | No |
| Fear + London DOWN, continuation | 53.5% | 57.4% | Weak edge on ETH |
| Greed + EMA bullish + Taker buy, LONG | 68.2% (22d) | 53.3% (15d) | Small sample |
| Fear + EMA bearish + Taker sell, SHORT | 48.7% (39d) | 72.4% (29d) | ETH strong, small sample |
| EMA trend direction only | 57.1% (364d) | 58.5% (364d) | Best standalone |

The Fear and Greed Index alone does not predict intraday direction. Combined with EMA trend, some edge appears on ETH, but sample sizes are insufficient.

### Funding Rate: Best Sentiment Signal

| Signal | BTC Win% | BTC Avg Move | ETH Win% | ETH Avg Move |
|--------|----------|--------------|----------|--------------|
| Very negative, LONG (contrarian) | 61.1% | +0.624% | 55.6% | +0.571% |
| Very positive, SHORT (contrarian) | 59.5% | +0.326% | 51.4% | +0.017% |
| Very positive, LONG (continuation) | 40.5% | -0.326% | 48.6% | -0.017% |
| Very negative, SHORT (continuation) | 38.9% | -0.624% | 44.4% | -0.571% |

Funding rate is a contrarian indicator. Extreme positioning predicts reversal with 61.1% accuracy on BTC (very negative funding, go long).

### Taker Buy Ratio Correlations

| London Taker Ratio | BTC NYC Up% | ETH NYC Up% |
|---------------------|-------------|-------------|
| Strong selling (<p25) | 45.1% | 42.9% |
| Mild selling (p25 to 0.5) | 48.7% | 46.0% |
| Mild buying (0.5 to p75) | 50.7% | 55.2% |
| Strong buying (>p75) | 51.6% | 44.0% |

Weak directional signal. Not strong enough to trade independently.

### Sentiment Filters on BTC TREND Baseline (Sharpe 2.60)

| Filter | Trades | Sharpe | Return | DD% | Delta Sharpe |
|--------|--------|--------|--------|-----|--------------|
| BASELINE | 363 | 2.60 | 147.6% | 15.4% | 0 |
| fund_positive | 312 | 3.02 | 169.1% | 15.3% | +0.42 |
| fund_not_extreme | 183 | 2.78 | 105.4% | 12.6% | +0.17 |
| taker_confirms_london | 180 | 2.70 | 100.5% | 12.6% | +0.10 |
| fg_fear_only | 191 | 2.21 | 91.9% | 15.4% | -0.39 |
| all_aligned | 81 | -1.04 | -15.4% | 25.7% | -3.64 |

## Key Findings

1. Funding rate (positive, contrarian) is the best sentiment filter, improving BTC TREND Sharpe from 2.60 to 3.02 (+0.42).
2. Very negative funding predicts long entries with 61.1% accuracy on BTC, the strongest standalone sentiment signal.
3. Fear and Greed Index has no intraday predictive power as a standalone indicator.
4. Combining all sentiment filters ("all_aligned") destroys the strategy (Sharpe -1.04). Over-filtering reduces trades to 81 and eliminates statistical significance.
5. Taker buy ratio provides only marginal directional information (~51% accuracy), insufficient for standalone trading.
6. EMA trend direction alone (57.1% BTC, 58.5% ETH) outperforms every sentiment indicator tested.

## Limitations

- Funding rate data covers only 365 days. Multi-year validation of the fund_positive filter was not conducted in this phase.
- Open interest and long/short ratio data are limited to ~28 days, preventing meaningful analysis.
- The contrarian funding rate signal has a small sample of extreme events, reducing confidence in the 61.1% figure.
