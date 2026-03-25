# Phase 7: Advanced Strategy Research

## Objective

Test 22 new strategies from ICT/Smart Money Concepts, market microstructure, volatility cycles, and classical technical analysis. 342 parameter variations were tested per pair.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT
- Variations: 342 per pair

## Strategies Tested

| # | Strategy | Type | Concept |
|---|----------|------|---------|
| 1 | FVG Reversion | ICT | Trade price filling Fair Value Gaps |
| 3 | Liquidity Sweep Reversal | ICT | Trade reversals after stop hunts |
| 4 | Power of 3 (AMD) | ICT | Accumulation, Manipulation, Distribution |
| 5 | Volume Profile POC | Microstructure | Mean revert to Point of Control |
| 6 | Opening Range Breakout | Classical | Trade first N-minute range breakout |
| 7 | Keltner Squeeze Breakout | Volatility | Enter when BB contracts inside KC |
| 8 | CVD Divergence | Order Flow | Price/volume delta divergence |
| 9 | Wyckoff Spring/Upthrust | Classical | Fade false breaks at range boundaries |
| 10 | Heikin Ashi Smoothed | Trend | Double-smoothed HA color changes |
| 11 | Pivot Points | S/R | Bounce off prior-day pivot levels |
| 12 | Donchian Channel Breakout | Trend | Turtle Traders adapted for crypto |
| 14 | Supertrend ATR | Trend | ATR-based trailing flip system |
| 17 | Range Compression/Expansion | Volatility | Trade expansion after ATR compression |
| 18 | Ichimoku Cloud (Fast) | Trend | Crypto-adapted TK cross above cloud |
| 20 | VWAP + Funding Regime | Hybrid | VWAP crosses with funding rate regime |
| 22 | Z-Score Mean Reversion | Mean Rev | Enter at extreme statistical deviations |

## Results

### BTC: Best Per Strategy Type

| Strategy | Trades | Win% | PF | Return | Sharpe | DD% | Walk-Fwd |
|----------|--------|------|----|--------|--------|-----|----------|
| RNGCOMP E7h P0.2 TP1.5 | 142 | 62.0% | 1.39 | 58.3% | 1.87 | 16.8% | PASS (-11%) |
| VWAP+FR E13h S0.4% T0.8% | 193 | 38.3% | 1.26 | 96.3% | 1.48 | 25.6% | Not tested |
| LIQ_SWEEP 7-12h TP1.0 T2 | 534 | 56.4% | 1.10 | 69.1% | 1.30 | 25.9% | Multi-trade |
| AMD 7-13h TP2.0 | 96 | 51.0% | 1.37 | 16.1% | 1.10 | 12.0% | Low DD |
| PIVOT (prior-day, fixed) | 230 | 23.0% | 1.03 | 9.3% | 0.45 | 58.2% | Marginal |
| ORB | 100 | 44.0% | 0.98 | -2.7% | 0.06 | 24.4% | Breakeven |

None of the new BTC strategies exceeded TREND + bb_squeeze (Sharpe 3.12 from Phase 6). Range Compression at Sharpe 1.87 was the best new finding.

### ETH: Best Per Strategy Type

| Strategy | Trades | Win% | PF | Return | Sharpe | DD% | Walk-Fwd |
|----------|--------|------|----|--------|--------|-----|----------|
| VWAP+FR E13h S0.4% T0.3% | 183 | 63.9% | 2.50 | 815.6% | 5.19 | 12.7% | PASS (-73%, improved) |
| RNGCOMP E12h P0.3 TP2.0 | 173 | 56.1% | 1.97 | 374.8% | 3.81 | 13.5% | PASS |
| ICHI E12h S0.3% | 298 | 48.3% | 1.44 | 351.5% | 2.81 | 24.4% | Not tested |
| DONCH P200 TP3.0 | 259 | 34.7% | 1.41 | 698.1% | 2.53 | 36.8% | High DD |
| PIVOT (fixed) | 208 | 33.2% | 1.51 | 285.4% | 2.07 | 23.0% | Decent |
| ORB O12h R30m TP1.0 | 353 | 51.0% | 1.15 | 110.0% | 1.61 | 30.1% | ETH-only |
| AMD 12-21h TP1.0 | 97 | 47.4% | 1.40 | 24.1% | 1.44 | 9.7% | Lowest DD |

### ETH VWAP + Funding Regime: Walk-Forward Detail

| Variant | Train Sharpe | Test Sharpe | Degradation | Verdict |
|---------|-------------|-------------|-------------|---------|
| E13h S0.4% T0.3% | 3.82 | 6.59 | -73% (improved) | PASS |
| E13h S0.3% T0.3% | 3.56 | 4.31 | -21% | PASS |
| E12h S0.4% T0.3% | 2.09 | 5.68 | -172% (improved) | PASS |

The strategy improved in the out-of-sample period, suggesting a genuine persistent edge rather than curve-fitting.

### ETH VWAP+FR Monthly P&L (E13h S0.4% T0.3%)

| Month | P&L |
|-------|-----|
| 2025-04 | +$10.96 |
| 2025-05 | +$3.15 |
| 2025-06 | +$42.39 |
| 2025-07 | -$16.36 |
| 2025-08 | +$68.08 |
| 2025-09 | +$5.71 |
| 2025-10 | +$103.95 |
| 2025-11 | +$26.17 |
| 2025-12 | +$48.26 |
| 2026-01 | +$67.88 |
| 2026-02 | +$321.35 |
| 2026-03 | +$234.10 |

11 out of 12 full months profitable. Only July was a loss.

### Strategies That Failed

| Strategy | BTC Sharpe | ETH Sharpe | Reason |
|----------|-----------|-----------|--------|
| FVG Reversion | -10.01 | -4.86 | ICT concept does not survive fees. Return: -94% |
| Keltner Squeeze | -3.39 | 0.17 | Too many false signals on 1m/5m |
| CVD Divergence | -0.60 | -2.09 | Divergences are noisy intraday |
| Wyckoff Spring | -3.17 | -1.19 | False breaks outnumber real springs |
| Heikin Ashi | -1.69 | -1.10 | Smoothing causes late entries, consuming edge |
| Z-Score Mean Rev | -4.03 | -1.57 | Extremes keep extending in crypto |
| Supertrend | -2.18 | 0.15 | Too many whipsaws on 1m |
| VPOC | -0.88 | -1.27 | Price does not revert to POC intraday |

### Bug Caught: Pivot Point Look-Ahead

The Pivot Point strategy initially showed $100 to $171,339 (Sharpe 6.71) due to look-ahead bias. It was using the current day's high/low/close to calculate pivots for trading during that same day. After fixing to use prior day's data, results dropped to Sharpe 0.45 (BTC) and 2.07 (ETH).

## Key Findings

1. ETH VWAP + Funding Regime is the best new strategy, with Sharpe 5.19, 63.9% win rate, and 12.7% drawdown. It improved during walk-forward testing.
2. Range Compression/Expansion confirms the volatility cycle edge found with BB Squeeze in Phase 6 (BTC Sharpe 1.87, ETH Sharpe 3.81).
3. ICT concepts (FVG, CVD, Wyckoff) fail backtesting. FVG Reversion lost 94% of capital. These approaches are marketed but lack quantifiable edge.
4. AMD (Power of 3) produces the lowest drawdown on ETH at 9.7%, but returns of 24.1% are modest.
5. The Pivot Point look-ahead bug reinforces the Phase 9 lesson: always validate data access timing in backtests.
6. No new BTC strategy exceeded the Phase 6 winner (TREND + bb_squeeze, Sharpe 3.12).
7. VWAP + Funding works because it combines two distinct edges: funding rate as regime detector and VWAP cross as timing mechanism.

## Limitations

- All results are on 1 year of data. Multi-year validation of VWAP+FR and Range Compression was not conducted.
- VWAP+FR performance is concentrated in late 2025 and early 2026 ($321 + $234 in the last two months). This pattern may not persist.
- The 815.6% ETH return includes compounding effects. Fixed-size returns would be substantially lower.
