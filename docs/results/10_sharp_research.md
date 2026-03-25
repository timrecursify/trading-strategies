# Phase 11: Sharp Research Validation

## Objective

Test strategies identified by Sharp Research (@sharp_research) as the most promising on equities, applied to crypto futures. Validate their broader claims about technical analysis and day trading.

## Data

- Period: 6+ years (2019 to 2026)
- Symbols: BTCUSDT, ETHUSDT
- Configurations: ~800 parameter combinations

## Methodology

Sharp Research conducted extensive backtesting on SPY and identified RSI + Bollinger Bands (1 sigma) as their only technical combination with a consistent upward equity curve over 5,000+ days. We replicated their exact methodology on crypto and tested variations.

## Results

### RSI + Bollinger Bands (1 Sigma)

**Rules:** RSI(14) < 30 AND close < BB(20, 1 sigma) lower band: go LONG next day. RSI > 70 AND close > BB(20, 1 sigma) upper band: go SHORT next day.

| Pair | Trades | Best Win% | Best Annual | Verdict |
|------|--------|-----------|-------------|---------|
| BTC | 598 | 47.8% | -4.9% | Fails (every configuration negative) |
| ETH | 511 | 52.3% | -1.0% | Fails (every configuration negative) |

Parameters tested: BB standard deviations 1.0, 1.5, 2.0. RSI thresholds 20/80, 25/75, 30/70, 35/65. Stops 1.5-5%. R:R 1-3. Entry hours 0, 7, 12. Exit hours 12, 20. All configurations were negative.

### 2-Sigma Day Mean Reversion

Sharp's finding on equities: after a 2-sigma negative day on SPY, the next day averages +0.4% (10x normal).

| Pair | Trades | Win% | Annual | Verdict |
|------|--------|------|--------|---------|
| BTC | 146 | 44.5% | -3.8% | Fails |
| ETH | 135 | 44.4% | -7.1% | Fails |

Crypto does not mean-revert after extreme daily moves. It trends through them.

### Optimal Holding Period Search

Exit hours 1 through 20 were tested for both signals. Every holding period lost money on BTC. ETH RSI+BB at the 2-hour exit showed +0.8%/yr, which is statistically indistinguishable from zero.

### Sharp's Key Claims: Verified on Crypto

| Claim | Our Result | Confirmed? |
|-------|-----------|------------|
| "Volume does not forecast price" | High vol day: 49.2% next up. Low vol: 49.3%. | Yes |
| "R:R does not create edge; win rate = f(R:R)" | Win rates track theoretical values closely | Yes |
| "Moving averages: every combo 3-100 fails" | All MA crossovers negative on crypto | Yes |
| "MACD loses nearly all money" | MACD filter: marginal at best | Yes |
| "Day trading destroys edge" | Most daily strategies negative after fees | Yes |
| "Nothing on retrospective price data works" | Only session microstructure shows edge | Mostly yes |

## Key Findings

1. RSI + Bollinger Bands (1 sigma) fails on crypto. Every one of 800+ parameter combinations was negative on both BTC and ETH.
2. 2-sigma day mean reversion fails on crypto (-3.8% BTC, -7.1% ETH annually). Crypto trends through extreme moves rather than reverting.
3. Volume has zero predictive power for next-day price direction: 49.2% up after high-volume days vs 49.3% after low-volume days. Confirmed on 6 years.
4. Sharp's core thesis is validated on crypto: retrospective price-based signals do not provide sustainable day trading edge.
5. R:R ratios do not create edge. Win rate is mathematically determined by R:R. Wider take-profits produce fewer wins. Net expected value is unchanged.
6. The exception to Sharp's thesis in our testing is session microstructure (Asia Breakout, Dual Thrust), which exploits structural market features rather than generic technical patterns.

## Limitations

- Sharp Research tested on SPY (equities). The failure on crypto does not invalidate their findings on equities; it confirms that crypto and equities have different microstructure.
- We tested on 6+ years of data, but this covers a limited number of independent macro regimes (1-2 full cycles).
- The "nothing works" conclusion applies to daily-frequency price-based signals. Intraday session structure and cross-market signals (funding rate, session ranges) are fundamentally different signal types.
