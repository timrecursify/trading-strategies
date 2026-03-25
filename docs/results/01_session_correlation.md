# Phase 1: Session Correlation Analysis

## Objective

Test whether London session price direction predicts NYC session direction on BTC and ETH perpetual futures.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT (Binance USDT-M Perpetual Futures)
- Candles: 1m, 5m, 15m (1,331,520 total)
- Account model: $100 starting capital, up to 10x leverage, 2% risk per trade

## Session Definitions (UTC)

| Session | UTC Hours | Role |
|---------|-----------|------|
| Asia | 00:00 to 07:00 | Range building, consolidation |
| London Kill Zone | 07:00 to 10:00 | Direction established |
| London to NYC | 07:00 to 12:00 | Directional bias period |
| NYC Open Window | 12:00 to 15:00 | Entry zone |
| NYC Full | 12:00 to 21:00 | Trade execution |

## Methodology

Six tests were conducted: raw continuation rate at multiple exit times, move-size bucketing, 3-session alignment, day-of-week analysis, volume as predictor, and BTC-ETH cross-pair correlation. Statistical significance was assessed using chi-squared tests.

## Results

### Test 1: London to NYC Continuation Rate

**BTCUSDT:**

| Exit Time (UTC) | Continue | Reverse | Continuation % | Avg Cont Move | Avg Rev Move |
|-----------------|----------|---------|-----------------|----------------|--------------|
| 14:00 | 175 | 187 | 48.3% | 0.5% | 0.4% |
| 15:00 | 189 | 171 | 52.5% | 0.7% | 0.6% |
| 16:00 | 187 | 176 | 51.5% | 0.9% | 0.7% |
| 12pm ET | 191 | 171 | 52.8% | 1.0% | 0.8% |
| 21:00 | 184 | 177 | 51.0% | 1.3% | 1.1% |

Chi-squared at 21:00: X2=0.07, p>0.05. Not statistically significant.

**ETHUSDT:** Similar results. 51.5% continuation at 21:00, p>0.05.

**Verdict:** Raw London to NYC continuation is statistically indistinguishable from a coin flip (~51%) on both pairs.

### Test 2: London Move Size and Continuation

| London Move | BTC Cont% | ETH Cont% | BTC Days | ETH Days |
|-------------|-----------|-----------|----------|----------|
| <0.25% | 54.8% | 57.3% | 129 | 83 |
| 0.25 to 0.5% | 41.5% | 46.8% | 82 | 80 |
| 0.5 to 1.0% | 50.5% | 45.8% | 103 | 96 |
| 1.0 to 2.0% | 55.3% | 53.1% | 38 | 64 |
| >2.0% | 66.7% | 60.0% | 12 | 41 |

Large moves (>2%) show higher continuation rates, but sample sizes are too small for statistical confidence (12 BTC days, 41 ETH days).

### Test 3: 3-Session Alignment

| Condition | BTC Cont% | ETH Cont% |
|-----------|-----------|-----------|
| Asia + London AGREE | 49.7% | 51.4% |
| Asia + London DISAGREE | 52.1% | 51.7% |

No improvement from session alignment. The signal is noise.

### Test 4: Day-of-Week Effects

**BTC best days:** Wednesday (57.7%), Thursday (55.8%)
**BTC worst days:** Tuesday (38.5%), Saturday (43.1%)

**ETH best days:** Friday (61.5%), Monday (56.9%)
**ETH worst days:** Wednesday (42.3%), Saturday (42.3%)

BTC and ETH show opposite day-of-week patterns, suggesting these effects are not robust.

### Test 5: Volume as Predictor

| London Volume | BTC Cont% | ETH Cont% |
|---------------|-----------|-----------|
| Above median | 54.4% | 55.0% |
| Below median | 47.5% | 48.1% |

Above-median London volume adds approximately 7 percentage points to the continuation rate. This is the strongest individual signal found in Phase 1, though still marginal for profitable trading after fees.

### Test 6: BTC-ETH Correlation

- BTC and ETH move in the same London direction 79.1% of the time.
- BTC London predicting ETH NYC: only 53.6%. Not useful as a cross-pair signal.

## Key Findings

1. Raw London to NYC continuation is a coin flip at ~51%, with no statistical significance on either pair.
2. Above-median London volume adds ~7% edge, the strongest single predictor found in this phase.
3. Session alignment (Asia + London agreement) provides zero improvement.
4. Day-of-week effects exist but are contradictory between BTC and ETH, suggesting noise rather than signal.
5. Large London moves (>2%) show higher continuation, but sample sizes of 12-41 days preclude reliable conclusions.
6. BTC-ETH intraday correlation is high (79.1% same direction), but cross-pair prediction is weak (53.6%).

## Limitations

- 364 trading days is a single market regime sample. Day-of-week effects with ~52 observations per day lack statistical power.
- Continuation rates near 51% would require thousands of samples to distinguish from random.
- No transaction costs were applied to the raw correlation tests. After fees (0.10% round-trip), most marginal edges become negative.
- Session boundaries are fixed UTC times; they do not account for daylight saving shifts in US/UK trading hours.
