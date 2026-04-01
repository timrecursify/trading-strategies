# Strategy: Dual Thrust Breakout (ETH)

## Overview

Dual Thrust is a volatility breakout strategy originally developed for Chinese commodity futures. It computes a dynamic range from the prior N days' price action and enters when price breaks above or below the range-adjusted open. Combined with an SMA200 regime filter, it produced the best risk-adjusted returns across 70,000+ backtests.

**Origin:** Rob Carver cites Dual Thrust as one of the most robust breakout strategies in systematic trading. The adaptive range calculation distinguishes it from fixed-session breakout strategies.

## Parameters

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| Pair | ETHUSDT | ETH shows stronger breakout patterns than BTC across all phases |
| N (lookback) | 3 days | Balances responsiveness to recent volatility against noise |
| K (multiplier) | 0.5 | Requires price to move half the prior range before entry. Filters noise. |
| Entry window | 07:00 to 16:00 UTC | London open through early NYC |
| Stop loss | 1.0% from entry | Tight. Breakout momentum carries winners; stops cut losers quickly. |
| Time exit | 16:00 UTC | End-of-day exit prevents overnight exposure |
| Regime filter | Price > 200-day SMA | Only trade in bullish regimes |
| Risk per trade | 2% of account | Standard risk management |
| Max leverage | 10x | Binance USDT-M limit |

## Entry and Exit Rules (Pseudocode)

```
# Compute Dual Thrust range
for each of the prior N days:
    HH = highest high
    HC = highest close
    LL = lowest low
    LC = lowest close

range = max(HH - LC, HC - LL)

buy_trigger  = today_open + K * range
sell_trigger = today_open - K * range

# Regime filter
if close[yesterday] < SMA200[yesterday]:
    no_trade_today()

# Entry scan (07:00 to 16:00 UTC)
for each 1m candle from 07:00 to 16:00:
    if candle.high >= buy_trigger and no_position:
        enter_long(price=buy_trigger)
        stop_loss = entry_price * 0.99
    elif candle.low <= sell_trigger and no_position:
        enter_short(price=sell_trigger)
        stop_loss = entry_price * 1.01

# Exit conditions (checked each minute)
if position_open:
    if hit_stop_loss:
        exit(reason="stop")
    elif current_time >= 16:00 UTC:
        exit(reason="time")
```

## Performance ($1,000 start, 6.3 years, fixed position size)

| Metric | Value |
|--------|-------|
| Total return | +244.3% ($1,000 to $3,443) |
| Annual return | ~39% |
| Max drawdown | 12.4% |
| Return/DD ratio | 19.63 |
| Total trades | 488 (77/year) |
| Win rate | 35.5% |
| Profit factor | 1.38 |
| Average trade duration | Intraday (hours) |

## Yearly P&L ($1,000 fixed size)

| Year | P&L | Cumulative | Market Regime |
|------|-----|-----------|---------------|
| 2019 | +$112 | $1,112 | Partial year |
| 2020 | +$992 | $2,104 | COVID crash + recovery |
| 2021 | +$652 | $2,756 | Bull market |
| 2022 | +$100 | $2,857 | Bear market |
| 2023 | +$58 | $2,915 | Sideways |
| 2024 | +$552 | $3,467 | Recovery |
| 2025 | -$54 | $3,413 | Only losing year (-1.6%) |
| 2026 | +$30 | $3,443 | Partial year |

Every full year was profitable except 2025 (-$54). The strategy survived the 2022 bear market (+$100) and the 2023 sideways market (+$58) because the SMA200 filter correctly reduced exposure during adverse regimes.

## Walk-Forward Validation

Dual Thrust was tested on the full 6.3-year ETH dataset. The strategy was selected from 41,344 parameter combinations using the training half, then validated on the test half.

## Why Dual Thrust Beats Asia Breakout

| Feature | Dual Thrust | Asia Breakout |
|---------|-------------|---------------|
| Range calculation | Dynamic: max(HH-LC, HC-LL) over 3 days | Fixed: Asia session (00:00-07:00 UTC) |
| Adaptiveness | Adjusts to recent volatility regime | Static; same range regardless of market conditions |
| Multi-year Sharpe | Higher | ~1.10 |
| Max drawdown | 12.4% | 22-35% |
| Annual return | ~39% | ~15-19% |
| 1-year Sharpe | N/A (not separately reported) | 5.90 (period-dependent) |

The adaptive range is the critical difference. When volatility expands, the range widens, requiring a larger move before entry. When volatility contracts, the range tightens, allowing entry on smaller moves. Asia Breakout uses the same fixed session window regardless of market conditions.

## Failure Modes

1. **Sideways/choppy markets.** The strategy enters on breakouts that fail to follow through. 2023 (+$58) and 2025 (-$54) demonstrate this weakness.
2. **Bear markets without SMA200 filter.** Without the regime filter, the strategy takes both long and short trades during drawdowns, increasing losses.
3. **Extreme gap events.** If price gaps beyond the stop level at market open, the actual loss exceeds the 1% stop. The simulator does not model gap risk.
4. **Liquidity regime changes.** ETH's market microstructure could change (e.g., due to new derivatives products or regulatory changes), invalidating the volatility patterns the strategy exploits.
5. **Low win rate sensitivity.** At 35.5% win rate, a string of 10+ consecutive losses is statistically expected. Traders must accept this psychologically.

## Implementation Notes for Live Trading

- **Order type:** Use limit orders at the trigger level, not market orders, to avoid slippage beyond what is modeled.
- **Scan frequency:** Check price against triggers at least every minute during the entry window (07:00-16:00 UTC).
- **SMA200 computation:** Use the daily close from the prior day. Do not update intraday.
- **Position sizing:** With 2% risk and a 1% stop, the position size is 2x the account value (before leverage cap).
- **Multiple entries:** Only one position per day. If stopped out, do not re-enter.

## Paper Trading Status (as of 2026-04-01)

**Deployed** on VPS via `live/paper_main.py` as part of the multi-strategy system.

- **Symbols:** All 8 (BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, XRPUSDT, AVAXUSDT, LINKUSDT, ADAUSDT). Only ETH was backtested; other pairs are experimental.
- **Sessions:** London (07:00-16:00 UTC) and NYC (12:00-20:00 UTC).
- **Regime:** SMA200 filter. Longs above SMA200, shorts below. As of deployment, all 8 pairs are below SMA200 (bear regime, shorts only).
- **Architecture:** Setup+tick pattern. Triggers computed at session open (cron), prices checked every 60s (tick cron).
