# Final Rankings: All Strategies Tested

## Overview

This table ranks every strategy tested across 16 research phases, 70,000+ backtests, on BTCUSDT and ETHUSDT Binance perpetual futures. Strategies are ranked by Return/Drawdown ratio on the longest available validation period.

**Methodology notes:**
- "Annual % (Fixed)" uses constant position size, not compounding. This is the apples-to-apples comparison metric.
- "Walk-Forward" indicates whether the strategy passed a 50/50 chronological split with less than 50% Sharpe degradation.
- "Years" indicates the length of the validation period. Strategies validated on 6+ years are preferred.
- Fees: taker 0.04% + estimated slippage 0.01% per side (0.10% round-trip).

## Complete Strategy Rankings

| Rank | Strategy | Type | Pair | Annual % (Fixed) | Max DD | Ret/DD | Trades | Years | Walk-Fwd |
|------|----------|------|------|-----------------|--------|--------|--------|-------|----------|
| 1 | Dual Thrust (N3 K0.5 SMA200) | Breakout | ETH | +39.0% | 12.4% | 19.63 | 488 | 6.3 | Yes |
| 2 | Pairs Trading (BTC/ETH spread) | Stat Arb | Both | +33.0% | 8.7% | 3.79 | varies | 6+ | Yes |
| 3 | Scale-In RSI(2)<10, 3% stop | Mean Rev | ETH | +36.3% | 45.6% | 0.80 | 372 | 6+ | Yes |
| 4 | Scale-In RSI(2)<10, 3% stop | Mean Rev | BTC | +30.7% | varies | varies | 380 | 6+ | Yes |
| 5 | Asia BRK + SMA200, 2% stop 2:1 | Breakout | ETH | +15.4% | 37.8% | 0.41 | 631 | 6+ | Yes |
| 6 | Std Error Bands (N50 K1.5, 5% stop) | Mean Rev | ETH | +11.5% | 25.5% | 0.45 | 137 | 6+ | Yes |
| 7 | TREND S2.0% R2.0 X12h + trend filter | Trend | ETH | ~19% | 21.4% | ~0.89 | 754 | 6.3 | Yes |
| 8 | TREND S1.0% R3.0 X12h + trend filter | Trend | ETH | ~17% | 34.7% | ~0.49 | 754 | 6.3 | No |
| 9 | Zaratini Intraday Mom (0.75x) | Momentum | ETH | +8.7% | 76.9% | 0.11 | 594 | 6+ | N/A |
| 10 | IBS(2) < 0.3 (2% stop, prev_high) | Mean Rev | ETH | +7.8% | 43.1% | 0.18 | 251 | 6+ | N/A |
| 11 | RSI(2) < 10 (non-scaled) | Mean Rev | ETH | +6.6% | 34.0% | 0.19 | 227 | 6+ | N/A |
| 12 | Stoch %D<20 + IBS<0.5 | Combo | ETH | +5.0% | 24.1% | 0.21 | 110 | 6+ | N/A |
| 13 | Donchian(20) + ADX<30 | Trend | BTC | +4.8% | 12.4% | 0.39 | 134 | 6+ | N/A |
| 14 | REX(50) | Indicator | ETH | +4.7% | 26.2% | 0.18 | 127 | 6+ | N/A |
| 15 | Bearish Engulf + SMA200 | Candle | ETH | +4.1% | 10.9% | 0.38 | 45 | 6+ | N/A |

## 1-Year Only Results (Not Multi-Year Validated)

These strategies performed well on 1 year of data but were not validated on 6+ years, or degraded substantially when extended.

| Rank | Strategy | Type | Pair | Sharpe (1yr) | Return (1yr) | DD% | Walk-Fwd (1yr) |
|------|----------|------|------|-------------|-------------|-----|----------------|
| 1 | ASIA_BRK S0.5% R1.0 X12 | Breakout | ETH | 5.90 | 1,590% | 14.7% | PASS (23%) |
| 2 | VWAP+FR E13h S0.4% T0.3% | Hybrid | ETH | 5.19 | 815.6% | 12.7% | PASS (improved) |
| 3 | RNGCOMP E12h P0.3 TP2.0 | Volatility | ETH | 3.81 | 374.8% | 13.5% | PASS |
| 4 | TREND 12:00 2.0% 3R + stoch_not_ob | Trend | ETH | 3.53 | 304.9% | 14.2% | PASS |
| 5 | TREND 12:00 2.0% 3R + bb_squeeze | Trend | BTC | 3.12 | 127.3% | 8.6% | PASS |
| 6 | TREND 12:00 1.5% 3R + tight_spread | Trend | BTC | 3.00 | 88.8% | 7.6% | PASS |
| 7 | TREND 12:00 2.0% 3R + fund_positive | Trend | BTC | 2.95 | 114.6% | 12.3% | PASS |
| 8 | ICHI E12h S0.3% | Trend | ETH | 2.81 | 351.5% | 24.4% | N/A |
| 9 | TREND 12:00 S1.5% R3.0 X20 | Trend | BTC | 2.74 | 160.7% | 14.2% | PASS (-31%) |
| 10 | DONCH P200 TP3.0 | Trend | ETH | 2.53 | 698.1% | 36.8% | N/A |

## Strategies That Failed (Representative Failures)

| Strategy | Type | Pair | Best Annual% | Reason for Failure |
|----------|------|------|-------------|-------------------|
| TSMOM_1d (corrected) | Momentum | Both | -46% to -53% | No daily autocorrelation after fees |
| FVG Reversion | ICT | Both | -94% | Does not survive transaction costs |
| RSI Mean Reversion | Mean Rev | Both | -89% total | Crypto trends, does not revert |
| CVD Divergence | Order Flow | Both | -43% | Divergences are noisy intraday |
| Wyckoff Spring | Classical | Both | -87% | False breaks outnumber real springs |
| Z-Score Mean Rev | Statistical | Both | -57% | Extremes extend in crypto |
| RSI+BB(1 sigma) | Sharp Research | Both | -1% to -5% | Equities signal does not transfer |
| 2-Sigma Day Reversion | Sharp Research | Both | -4% to -7% | Crypto trends through extremes |
| Williams %R | Oscillator | Both | Negative | Fails on crypto |
| Williams VIX Fix | Volatility | BTC | -5.1% | Fails |
| REVERSAL | Counter-trend | Both | Negative | Fading session direction loses money |
| Multi-trade SCALP | Scalping | Both | -4.22 Sharpe | Destroyed by fees |
| EMA SCALP | Scalping | Both | -4.30 Sharpe | Destroyed by fees |
| Keltner Squeeze | Volatility | Both | -3.39 Sharpe | Too many false signals |
| Supertrend ATR | Trend | Both | Negative | Too many whipsaws on 1m |
| VPOC Mean Rev | Microstructure | Both | Negative | Price does not revert to POC intraday |
| Heikin Ashi | Trend | Both | Negative | Smoothing causes late entries |

## Summary Statistics

| Category | Count |
|----------|-------|
| Total backtests | 70,000+ |
| Total strategies tested | 50+ distinct approaches |
| Strategies profitable on 6+ years | 15 |
| Strategies with Ret/DD > 1.0 | 2 (Dual Thrust, Pairs Trading) |
| Research phases | 16 |
| Critical bugs found | 2 (TSMOM look-ahead, Pivot Point look-ahead) |
