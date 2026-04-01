# Strategy: BTC/ETH Pairs Trading

## Overview

Trade the BTC/ETH price ratio (spread) as a mean-reverting instrument. When the ratio deviates beyond a threshold from its moving average, enter a convergence trade: long the underperformer and short the outperformer. This is the safest strategy tested, with only 8.7% maximum drawdown.

## Concept

BTC and ETH are highly correlated (79.1% same-direction days, Phase 1). When one temporarily outperforms the other, the spread tends to revert. Pairs trading captures this reversion while being market-neutral: a crash that hits both assets equally does not affect the spread position.

## Parameters

| Parameter | Value |
|-----------|-------|
| Instruments | BTCUSDT (leg 1), ETHUSDT (leg 2) |
| Spread | BTC/ETH price ratio (or log difference) |
| Moving average | Period calibrated during backtesting |
| Entry threshold | Spread deviates beyond N standard deviations from MA |
| Exit | Spread returns to moving average (mean reversion target) |
| Position sizing | Equal dollar value in each leg (dollar-neutral) |
| Direction | Long underperformer, short outperformer |

## Entry and Exit Rules (Pseudocode)

```
# Compute spread
spread = price_BTC / price_ETH
spread_ma = SMA(spread, period=N)
spread_std = StdDev(spread, period=N)
z_score = (spread - spread_ma) / spread_std

# Entry
if z_score > threshold and no_position:
    # BTC overvalued relative to ETH
    short_BTC(size=S)
    long_ETH(size=S)  # Equal dollar value

elif z_score < -threshold and no_position:
    # ETH overvalued relative to BTC
    long_BTC(size=S)
    short_ETH(size=S)

# Exit
if position_open:
    if abs(z_score) < exit_threshold:
        close_both_legs(reason="mean_reversion")
    elif abs(z_score) > stop_threshold:
        close_both_legs(reason="stop_divergence")
```

## Performance (6+ years)

| Metric | Value |
|--------|-------|
| Annual return | +33% |
| Max drawdown | 8.7% |
| Return/DD ratio | 3.79 |

## Why This Is the Safest Strategy

1. **Market neutrality.** A broad crypto crash affects both BTC and ETH. The pairs position profits from the relative movement, not the absolute direction. This eliminates the largest source of drawdown (market direction).
2. **8.7% maximum drawdown.** The lowest of any profitable strategy tested across all 16 phases.
3. **Mean reversion is reliable for pairs.** While single-asset mean reversion fails on crypto (Phase 9-11), the BTC/ETH spread does revert because both assets share common fundamental drivers (crypto sentiment, regulation, institutional flows).
4. **No regime filter needed.** Unlike directional strategies that require SMA200 or trend filters, pairs trading works across all market regimes because it is direction-agnostic.

## Comparison to Other Strategies

| Strategy | Annual % | Max DD | Ret/DD | Direction Risk |
|----------|---------|--------|--------|---------------|
| Pairs Trading | +33% | 8.7% | 3.79 | Market-neutral |
| Dual Thrust | +39% | 12.4% | 19.63 | Directional (long-biased with SMA200) |
| Scale-In RSI(2) | +36.3% (fixed) | 45.6% | 0.80 | Long-only |

Pairs trading offers the best drawdown profile. Dual Thrust has a higher Ret/DD ratio but carries directional risk.

## Failure Modes

1. **Structural break in BTC/ETH correlation.** If the assets permanently decouple (e.g., due to a major regulatory divergence or technological change), the spread may not revert.
2. **Trending spread.** During periods when ETH significantly outperforms or underperforms BTC for fundamental reasons (e.g., the 2021 DeFi boom), the spread trends rather than reverting. Stop losses on divergence are essential.
3. **Execution complexity.** Managing two legs simultaneously requires careful position sizing and synchronized order execution. Slippage on one leg without the other creates unintended directional exposure.
4. **Funding rate mismatch.** BTC and ETH have different funding rates. A persistent funding rate differential adds a carry cost (or benefit) to the position.

## Limitations

- Yearly breakdown was not provided for this strategy.
- Execution in live markets is more complex than single-leg strategies. Two simultaneous orders, margin requirements for both positions, and potential for partial fills add operational risk.
- The strategy requires margin for both a long and a short position simultaneously, which may limit position size on accounts with low margin capacity.
- Funding rate costs are not modeled in paper trading. A 10-day hold incurs ~0.3% in funding at 0.01% per 8h.

## Paper Trading Status (as of 2026-04-01)

**Deployed** on VPS via `live/paper_main.py`.

- **Parameters:** Window=30 days, z_entry=2.0, z_exit=0.5, max_hold=10 days, 5% max loss safety cap.
- **Scan:** Daily at 00:05 UTC. Z-score and rolling stats recomputed daily.
- **First signal:** Entered on deployment day (z=-2.28, LONG BTC + SHORT ETH).
