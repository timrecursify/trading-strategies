# Strategy: Asia Range Breakout (ETH)

## Overview

Trade the breakout of the Asian session (00:00-07:00 UTC) high or low during the London session (07:00-10:00 UTC). This strategy exploits the tendency for Asian consolidation to resolve directionally when European liquidity enters the market.

**Important:** This strategy showed Sharpe 5.90 on 1 year of data (2025-2026) but degraded to Sharpe ~1.10 on 6 years (2019-2026). The 1-year results were period-dependent. Multi-year expected Sharpe is approximately 1.0. See Phase 8 for the full degradation analysis.

## Parameters

| Parameter | Value |
|-----------|-------|
| Pair | ETHUSDT |
| Asia session | 00:00 to 07:00 UTC |
| Entry window | 07:00 to 10:00 UTC (London) |
| Direction | Long if price breaks above Asia high; Short if price breaks below Asia low |
| Stop loss | 0.5% from entry |
| Take profit | 1:1 risk-reward (0.5% from entry) |
| Time exit | 12:00 UTC |
| Exit priority | TP, stop, or time exit (whichever first) |
| Regime filter | SMA200 recommended (Phase 14 finding) |
| Risk per trade | 2% of account |

## Entry and Exit Rules (Pseudocode)

```
# Compute Asia range
asia_high = max(high) for candles 00:00 to 07:00 UTC
asia_low  = min(low)  for candles 00:00 to 07:00 UTC

# Optional regime filter
if close[yesterday] < SMA200[yesterday]:
    no_trade_today()

# Entry scan (07:00 to 10:00 UTC)
for each 1m candle from 07:00 to 10:00:
    if candle.high >= asia_high and no_position:
        enter_long(price=asia_high)
        stop_loss   = entry_price * 0.995
        take_profit = entry_price * 1.005
    elif candle.low <= asia_low and no_position:
        enter_short(price=asia_low)
        stop_loss   = entry_price * 1.005
        take_profit = entry_price * 0.995

# Exit (checked each minute)
if hit_stop_loss: exit("stop")
elif hit_take_profit: exit("tp")
elif current_time >= 12:00 UTC: exit("time")
```

## Performance

### 1-Year Results (2025-2026, Period-Dependent)

| Metric | Value |
|--------|-------|
| Win rate | 62.5% |
| Profit factor | 2.35 |
| Sharpe ratio | 5.90 |
| Return | $100 to $1,690 |
| Max drawdown | 14.7% |
| Trades | 216 (0.6/day) |
| Avg win duration | 38 minutes |
| Walk-forward | PASS (23% degradation) |

### 6-Year Results (2019-2026, with trend filter)

| Metric | No Filter | SMA200 Filter |
|--------|-----------|---------------|
| Best Sharpe | 0.64 | ~1.10 |
| Win rate | 44-47% | 45.8% |
| Max drawdown | 22-35% | 37.8% |
| Annual return | varies | +15.4% |
| Trades | varies | 631 |

### Degradation Summary

| Metric | 1-Year | 6-Year | Change |
|--------|--------|--------|--------|
| Best Sharpe | 5.90 | 0.64 (no filter) | -89% |
| Win rate | 62.5% | 44-47% | -15 ppt |
| Max drawdown | 14.7% | 22-35% | +50 to +140% |

## Why It Degraded

1. **The 2025-2026 period was unusually favorable.** ETH exhibited consistent session-based volatility patterns during this period that are not representative of the full history.
2. **Fixed session range does not adapt.** Unlike Dual Thrust, Asia Breakout uses a fixed window. When ETH's volatility regime changes, the 0.5% stop may be too tight or too wide.
3. **Win rate drops significantly.** From 62.5% (1 year) to 44-47% (6 years). The tight 1:1 R:R requires >50% win rate to be profitable, which is only marginally achieved with the trend filter.

## Comparison to Dual Thrust

| Feature | Asia Breakout | Dual Thrust |
|---------|---------------|-------------|
| Range | Fixed (Asia session) | Dynamic (3-day volatility) |
| 6yr annual return | +15.4% (SMA200) | +39% |
| Max DD | 37.8% | 12.4% |
| Ret/DD | 0.41 | 19.63 |
| Adaptiveness | None | Adjusts to volatility |

Dual Thrust is strictly superior on multi-year data. Asia Breakout remains useful as a simpler alternative with fewer parameters.

## Failure Modes

1. **Ranging markets.** When ETH consolidates without clear session-based directional moves, the 0.5% stop is frequently hit.
2. **False breakouts.** Price breaks the Asia range only to reverse, triggering the stop.
3. **Bear markets without filter.** Taking both long and short breakouts during a sustained downtrend produces whipsaws.

## Limitations

- Does not work on BTC (Sharpe -0.36 on 1 year).
- Requires the SMA200 filter for multi-year viability.
- 37.8% drawdown with the filter is still higher than Dual Thrust's 12.4%.
