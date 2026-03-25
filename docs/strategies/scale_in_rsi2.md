# Strategy: Scale-In RSI(2) Mean Reversion

## Overview

Enter a long position when the 2-period RSI drops below 10 (extreme short-term oversold). Scale into the position if weakness continues. Exit when the close exceeds the prior day's high. This is a short-term mean reversion strategy that works because the scaling mechanism improves average entry price.

**Important:** Fixed-size annual returns of +36.3% significantly overstate compounded performance (+12.7%). The 45.6% maximum drawdown erodes the capital base, making fixed-size figures misleading. See the compounding discrepancy section below.

## Parameters

| Parameter | Value |
|-----------|-------|
| Pair | ETHUSDT (primary), BTCUSDT (secondary) |
| RSI period | 2 (very responsive, 2-day lookback) |
| Entry trigger | RSI(2) < 10 |
| Scale-in trigger | RSI(5) drops > 5 points further after initial entry |
| Initial position | 50% of intended size |
| Scale-in size | Remaining 50% |
| Exit | Close > yesterday's high |
| Stop loss | 3% from average entry |
| Direction | Long only |

## Entry and Exit Rules (Pseudocode)

```
# Daily signal (computed after market close)
rsi2 = RSI(close, period=2)
rsi5 = RSI(close, period=5)

# Entry
if rsi2 < 10 and no_position:
    enter_long(size=0.5 * intended_size)
    initial_rsi5 = rsi5
    stop_loss = entry_price * 0.97

# Scale-in (next day or later)
if position_open and position_size == 0.5 * intended_size:
    if rsi5 < initial_rsi5 - 5:
        add_to_position(size=0.5 * intended_size)
        # Recalculate average entry price
        stop_loss = avg_entry_price * 0.97

# Exit
if position_open:
    if close > yesterday_high:
        exit(reason="target")
    elif price <= stop_loss:
        exit(reason="stop")
```

## Performance

### ETH (3% stop, 6+ years, fixed size)

| Metric | Value |
|--------|-------|
| Annual return (fixed-size) | +36.3% |
| Annual return (compounded) | +12.7% |
| Win rate | 45.7% |
| Trades | 372 |
| Max drawdown | 45.6% |
| Ret/DD (fixed) | 0.80 |

### BTC (3% stop, 6+ years, fixed size)

| Metric | Value |
|--------|-------|
| Annual return (fixed-size) | +30.7% |
| Win rate | 53.2% |
| Trades | 380 |

### ETH Yearly Breakdown

| Year | Return | Notes |
|------|--------|-------|
| 2019 | -9.9% | Partial year, loss |
| 2020 | +91.5% | COVID recovery |
| 2021 | +113.3% | Bull market peak |
| 2022 | +0.9% | Bear market, flat |
| 2023 | +6.3% | Sideways |
| 2024 | +15.9% | Recovery |
| 2025 | +53.8% | Strong |
| 2026 | +18.5% | Partial year |

### BTC Yearly Breakdown

| Year | Return |
|------|--------|
| 2019 | +13.2% |
| 2020 | +56.3% |
| 2021 | +89.6% |
| 2022 | +10.8% |
| 2023 | +33.0% |
| 2024 | +79.6% |
| 2025 | -24.0% |
| 2026 | -12.6% |

BTC shows degradation in 2025-2026 (-24%, -12.6%). ETH is more consistent, with 5 of 7 full years profitable.

## Compounding vs Fixed-Size Discrepancy

| Metric | Fixed-Size | Compounded |
|--------|-----------|-----------|
| ETH annual return | +36.3% | +12.7% |
| Ratio | 1x | 0.35x |

The fixed-size return assumes a constant dollar position regardless of account drawdown. In reality, a 45.6% drawdown means the account is trading with 54.4% of peak capital, dramatically reducing recovery speed. Dual Thrust (+39%/yr with 12.4% DD) compounds far more effectively because its drawdowns are shallow.

## Why the Scaling Mechanism Matters

Non-scaled RSI(2) < 10 was negative on both pairs. The scaling mechanism transforms the strategy from a loser to +36.3%/yr by:

1. **Reducing average entry price.** The second entry (scale-in) occurs at a lower price, improving the breakeven level.
2. **Filtering for genuine oversold conditions.** The RSI(5) drop of >5 points confirms the move is not a false signal.
3. **Adding conviction at better prices.** Standard mean reversion enters at one price and hopes for recovery. Scale-in enters at progressively better prices.

## Failure Modes

1. **Extended downtrends.** RSI(2) can remain below 10 for multiple days during a crash, triggering repeated entries that all get stopped out.
2. **45.6% maximum drawdown.** Unacceptable for most live trading without the SMA200 filter, which reduces DD to 10-12% but also reduces returns to +15.4%.
3. **BTC regime dependency.** BTC's 2025-2026 negative performance suggests the signal may be degrading on that pair.
4. **Long-only bias.** The strategy only trades long. In sustained bear markets, it generates no trades (with SMA200 filter) or losing trades (without).

## Limitations

- The +36.3% fixed-size headline is misleading. Compounded returns are +12.7%.
- 45.6% drawdown requires the SMA200 filter for practical deployment, reducing returns substantially.
- Walk-forward results for this specific strategy variant were not independently reported in the testing document.
- The strategy is long-only. A short-side equivalent (RSI(2) > 90, short, scale in) was not tested.
