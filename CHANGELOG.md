# Changelog

Research evolution log. Each entry documents a research phase, what was tested, and the key finding.

## 2026-04-01

### Phase 19: Migration to Raspberry Pi + 51 Futures Pairs
- Migrated paper trading from US VPS (api.binance.us, spot proxy) to Raspberry Pi in Mexico (fapi.binance.com, real futures API).
- Expanded from 8 to 51 Binance USDT-M perpetual futures pairs across all liquidity tiers.
- Switched all API endpoints from `/api/v3/` (spot) to `/fapi/v1/` and `/fapi/v2/` (futures). Response formats identical, no parsing changes needed.
- **Finding:** VPS geo-blocked from fapi.binance.com. Pi in Mexico has full access to 609 futures symbols.

### Phase 18: Multi-Symbol Multi-Strategy Paper Trading
- Expanded paper trading from 1 symbol / 1 strategy to 8 symbols / 4 strategies.
- **Symbols added:** SOLUSDT, DOGEUSDT, XRPUSDT, AVAXUSDT, LINKUSDT, ADAUSDT (experimental, no backtest data).
- **Strategies deployed:**
  - Dual Thrust (8 symbols, London + NYC sessions) -- N=3, K=0.5, 1% stop, SMA200 filter
  - Asia Breakout (8 symbols, London session) -- 0.5% stop, 1:1 R:R, 07:00-10:00 entry window
  - Scale-In RSI(2) (8 symbols, daily) -- RSI(2)<10 entry, 3% stop, 10-day max hold, long-only
  - Pairs Trading (BTC/ETH only, daily) -- 30-day z-score, entry at |z|>2.0, exit at |z|<0.5
- **Architecture change:** Replaced long-polling scan with setup+tick cron pattern. Setup commands compute trigger levels at session open; tick (every 60s) checks prices against triggers and monitors positions.
- **Risk controls:** 2% per-trade risk, 20x max portfolio exposure, 30% drawdown circuit breaker, max 3 positions per symbol.
- **API finding:** VPS is US-based; `fapi.binance.com` (futures) is geo-blocked. Using `api.binance.us` spot prices as proxy (~0.1% difference from perp futures).
- **Finding:** Pairs Trading entered immediately on deployment (BTC/ETH z=-2.28, long BTC + short ETH). All other crypto assets in bear regime (below SMA200), so DT only takes shorts.

## 2026-03-25

### Phase 17: Portfolio Strategy and Paper Trading Deployment
- Tested portfolio combinations: DT only, DT+shorts, DT+NYC, DT+shorts+NYC, full portfolio with RSI2 and Pairs.
- Fixed SMA200 look-ahead bug (was using today's close, now uses prior day's close).
- **Finding:** DT+shorts+NYC is the best combo: 526 trades, +0.541% avg/trade, +35.5% annual fixed-size, 12.2% DD. Adding shorts below SMA200 and NYC session nearly triples trade frequency.
- Deployed paper trader to VPS with two sessions (London 07:00, NYC 12:00), short breakouts below SMA200, and 5 cron jobs.

### Phase 16: Dual Thrust Grid Search (41,344 combinations)
- Tested Dual Thrust breakout strategy with parameters N (lookback 1-5), K (multiplier 0.3-0.8), stops, exits, and regime filters.
- **Finding:** ETH Dual Thrust (N3 K0.5 SMA200) is the overall winner: $1,000 to $3,443, 12.4% DD, Ret/DD 19.63.

### Phase 15: Pairs Trading and Volatility Targeting (200+ configs)
- Tested BTC/ETH pairs trading, volatility targeting on existing strategies, and CUSUM filter on RSI(2).
- **Finding:** Pairs trading produces +33% annual with only 8.7% DD (safest strategy). Vol targeting is too conservative. CUSUM does not improve RSI(2) vs SMA200.

### Phase 14: Drawdown Reduction (40 configs)
- Tested SMA200 filter, SMA100, volatility targeting, circuit breakers, breakeven stops, and trailing stops.
- **Finding:** SMA200 cuts drawdown from 45% to 10-12% across all strategy types. Other techniques are approximately neutral.

### Phase 13: Channels-Alpha Batch 2 (120+ configs)
- Tested Scale-In RSI(2), candlestick patterns, SMA200 filter on Asia Breakout, Std Error Bands, Zaratini momentum.
- **Finding:** Scale-In RSI(2) produces +36.3%/yr ETH fixed-size. Scaling mechanism transforms losing RSI(2) into a winner.

### Phase 12: Channels-Alpha Batch 1 (112 configs)
- Tested IBS, RSI(2), Donchian+ADX, Williams %R, REX indicator.
- **Finding:** IBS(2) < 0.3 at +7.8%/yr ETH. RSI(2) < 10 at +6.6%/yr ETH. Williams %R fails.

## 2026-03-24

### Phase 11: Sharp Research Validation (~800 configs)
- Replicated Sharp Research strategies on crypto: RSI+BB(1 sigma), 2-sigma day mean reversion, volume forecasting.
- **Finding:** All Sharp Research strategies fail on crypto. Their thesis ("nothing on retrospective price data works in day trading") is confirmed for crypto.

### Phase 10: Quant Strategies Corrected (17 configs)
- Re-tested all Phase 9 strategies with corrected data access (no look-ahead).
- **Finding:** Every daily momentum strategy loses money on crypto after fees. BTC 20-day momentum (+10.7%) is the only marginal positive.

### Phase 9: Quant Strategies, INVALIDATED (3,584 configs)
- Tested TSMOM, EMA trend, adaptive regime, breakout, RSI momentum/reversion, calendar strategies on 6+ years.
- **Finding:** CRITICAL BUG. TSMOM_1d used today's close for yesterday's return signal. Fake 84% win rate, +380%/yr. All results invalidated.

### Phase 8: Multi-Year Validation (350 configs)
- Extended backtests from 1 year to 6.3 years. Downloaded full BTC (3.4M candles) and ETH (3.3M candles) history.
- **Finding:** Asia Breakout Sharpe degrades from 5.90 (1yr) to 0.64 (6yr). Trend filter is essential. 1-year backtests are dangerously misleading.

### Phase 7: Advanced Strategies (342 configs)
- Tested 22 new strategies from ICT, microstructure, volatility, and classical TA. 342 variations per pair.
- **Finding:** VWAP+Funding Regime (ETH Sharpe 5.19, improved in walk-forward). FVG, CVD, Wyckoff all fail. Pivot Point look-ahead bug caught and fixed.

### Phase 6: Technical Indicators (28 filters x 3 strategies x 2 pairs)
- Tested 11 indicators as standalone predictors and filters. RSI, MACD, BB, ADX, Stochastic, VWAP, OBV, EMA crosses.
- **Finding:** BB Squeeze is best for BTC (+0.50 Sharpe). Stochastic not overbought is best for ETH (+0.44). Full confluence fails.

### Phase 5: Depth and Microstructure (12 filters x 2 strategies x 2 pairs)
- Computed price impact, spread proxy, trade intensity, liquidation cascades. Tested as filters.
- **Finding:** Tight spread is the best depth filter (+0.40 Sharpe, halves drawdown on BTC).

### Phase 4: Sentiment and On-Chain (13 filters x 4 strategies x 2 pairs)
- Downloaded Fear and Greed Index, funding rate, taker buy ratio. Tested as strategy filters.
- **Finding:** Funding rate (contrarian, positive) improves BTC TREND Sharpe from 2.60 to 3.02. F&G Index has no intraday predictive power.

### Phase 3: V2 Alternative Strategies (1,188 configs)
- Tested TREND following, Asia Breakout, volatility breakout, reversal, multi-trade scalping, and more.
- **Finding:** TREND (20 EMA) is the most robust BTC approach (Sharpe 2.74). ETH Asia Breakout shows Sharpe 5.90 (later invalidated as period-dependent).

### Phase 2: V1 Grid Search (4,180 configs x 2 pairs)
- Tested 4 session variants (continuation, breakout, alignment, Judas swing) across entry times, stops, and exits.
- **Finding:** BTC session strategies fail walk-forward. ETH Variant C passes. trend_ema is the dominant single filter (+1.40 Sharpe on BTC).

### Phase 1: Session Correlation Analysis (8 tests x 2 pairs)
- Analyzed London to NYC continuation rate, move size, session alignment, day-of-week, volume, cross-pair correlation.
- **Finding:** Raw London to NYC continuation is a coin flip at ~51%, not statistically significant. Volume adds ~7% edge but is insufficient for profitable trading after fees.
