# Executive Summary

## Project Overview

This repository documents a systematic evaluation of crypto futures day trading strategies on Binance USDT-M perpetual contracts (BTCUSDT, ETHUSDT). Over 70,000 backtests were conducted across 16 research phases spanning March 24-25, 2026. Data covers 6.3 to 6.5 years of 1-minute candle history (6.7M+ candles total). The research progressed from session correlation analysis through ICT concepts, quantitative momentum, mean reversion, and volatility breakout strategies. A critical look-ahead bias was discovered and corrected in Phase 9, invalidating an entire class of results. The final winner, ETH Dual Thrust with SMA200 filter, was validated on 6.3 years of data with a return-to-drawdown ratio of 19.63.

## Top 5 Strategies by Return/Drawdown Ratio (6+ Year Validation)

| Rank | Strategy | Pair | Annual % (Fixed) | Max DD | Ret/DD | Trades | Years |
|------|----------|------|-----------------|--------|--------|--------|-------|
| 1 | Dual Thrust (N3 K0.5 SMA200) | ETH | +39% | 12.4% | 19.63 | 488 | 6.3 |
| 2 | Pairs Trading (BTC/ETH) | Both | +33% | 8.7% | 3.79 | varies | 6+ |
| 3 | Scale-In RSI(2) < 10 | ETH | +36.3% | 45.6% | 0.80 | 372 | 6+ |
| 4 | Scale-In RSI(2) < 10 | BTC | +30.7% | varies | varies | 380 | 6+ |
| 5 | Asia BRK + SMA200 | ETH | +15.4% | 37.8% | 0.41 | 631 | 6+ |

## Methodology

- All backtests use minute-level simulation on Binance perpetual futures data, with taker fees of 0.04%, maker fees of 0.02%, and estimated slippage of 0.01% per side.
- Walk-forward validation uses a 50/50 chronological split; strategies with less than 50% Sharpe degradation pass. Multi-year validation on 6+ years is required for final ranking.
- Signals are shifted by one bar to prevent look-ahead bias. All indicators use only data available at the time of entry. This protocol was validated by the Phase 9 incident, where a look-ahead bug produced fake 84% win rates.

## Key Findings

1. ETH Dual Thrust is the overall winner: $1,000 to $3,443 over 6.3 years with 12.4% maximum drawdown, producing a Ret/DD ratio of 19.63.
2. BTC/ETH pairs trading is the safest strategy: 33% annual return with only 8.7% drawdown, suitable for capital preservation.
3. 1-year backtests are dangerously misleading: Asia Breakout showed Sharpe 5.90 on 1 year but degraded to 1.10 on 6 years.
4. Look-ahead bias turned a losing strategy into a fake "84% win rate, +380%/yr" result (Phase 9). One data access bug invalidated an entire research phase.
5. Daily momentum does not survive fees in crypto: after correcting for look-ahead, every daily momentum strategy lost money.
6. Mean reversion fails on crypto: RSI contrarian lost 89%, Z-Score lost 57%, and 2-sigma reversion lost 4-7% annually.
7. ICT/Smart Money concepts fail backtesting: FVG reversion lost 94%, CVD divergence lost 43%, Wyckoff springs lost 87%.
8. The SMA200 filter is the single most impactful risk management tool, cutting drawdown by 50-70% across all strategy types, both pairs, and all timeframes.
9. ETH consistently shows stronger patterns than BTC across all 16 phases. Dual Thrust, Asia Breakout, RSI(2), and IBS all perform better on ETH.
10. Fees are the primary edge killer: 0.10% round-trip cost on a 0.5% target consumes 20% of edge. Wider stops and targets survive fees.

## Known Limitations

- **No market impact modeling.** Results assume perfect fills at the simulated price. Real execution on larger position sizes would face slippage beyond what is modeled.
- **Single exchange.** All data is from Binance. Results may not transfer to other venues with different liquidity profiles.
- **No partial fills.** The simulator assumes full fills on every order, which is optimistic for larger accounts.
- **Survivorship bias in asset selection.** BTC and ETH are the two most liquid crypto assets. Strategies may not generalize to altcoins.
- **Fixed fee model.** Actual fees vary with VIP tier, BNB holdings, and market conditions.
- **Walk-forward on a single split.** A single 50/50 split provides limited statistical power compared to k-fold cross-validation.

## Detailed Phase Reports

| Phase | Report | Topic |
|-------|--------|-------|
| 1 | [Session Correlation](01_session_correlation.md) | London to NYC continuation, day-of-week, volume |
| 2 | [V1 Grid Search](02_v1_grid_search.md) | 4,180 combos, walk-forward, filter analysis |
| 3 | [Alternative Strategies](03_alternative_strategies.md) | TREND, Asia Breakout, volatility breakout |
| 4 | [Sentiment and On-Chain](04_sentiment_onchain.md) | Fear and Greed, funding rate, taker ratio |
| 5 | [Depth and Microstructure](05_depth_microstructure.md) | Spread proxy, trade intensity, liquidation cascades |
| 6 | [Technical Indicators](06_technical_indicators.md) | 11 indicators, BB Squeeze, Stochastic |
| 7 | [Advanced Strategies](07_advanced_strategies.md) | 22 strategies, VWAP+Funding, Range Compression |
| 8 | [Multi-Year Validation](08_multiyear_validation.md) | Asia BRK degradation, trend filter requirement |
| 9-10 | [Quant Invalidated](09_quant_invalidated.md) | TSMOM look-ahead bias, correction |
| 11 | [Sharp Research](10_sharp_research.md) | RSI+BB, 2-sigma reversion, volume forecasting |
| 12-13 | [Channels Alpha](11_channels_alpha.md) | IBS, RSI(2), Scale-In, candlestick patterns |
| 14 | [Drawdown Reduction](12_drawdown_reduction.md) | SMA200 filter, vol targeting, circuit breakers |
| 15-16 | [Dual Thrust Final](13_dual_thrust_final.md) | Dual Thrust, pairs trading, CUSUM |
| All | [Final Rankings](14_final_rankings.md) | Complete strategy ranking table |
