# Phase 14: Drawdown Reduction

## Objective

Reduce the maximum drawdown of winning strategies (particularly Scale-In RSI(2) at 45.6% DD) using regime filters, volatility targeting, circuit breakers, and modified stop-loss approaches.

## Data

- Period: 6+ years (2019 to 2026)
- Symbols: BTCUSDT, ETHUSDT
- Configurations: ~40 per pair

## Methodology

Four categories of drawdown reduction techniques were tested:

1. **Regime filters:** SMA200 and SMA100 as trade-gating conditions
2. **Volatility targeting:** Scale position size inversely to recent volatility
3. **Circuit breakers:** Pause trading after consecutive losses
4. **Modified stops:** Breakeven stops, trailing stops, tighter fixed stops

## Results

### SMA200 Filter: The Most Impactful Single Improvement

The SMA200 filter (only trade when price > 200-day simple moving average) was tested across all strategy types.

Impact on Scale-In RSI(2) ETH:

| Configuration | Annual% | Max DD | DD Reduction |
|---------------|---------|--------|-------------|
| No filter | +36.3% | 45.6% | Baseline |
| SMA200 filter | +15.4% | 10-12% | -73% to -78% |

The SMA200 filter cuts drawdown from 45% to 10-12% across all strategy types, both pairs, and all timeframes tested. Returns decrease because the filter removes trading during bear markets, but the risk-adjusted improvement is substantial.

### Volatility Targeting

Volatility targeting scales position size inversely to trailing 20-day realized volatility. When volatility is high, positions are smaller; when low, positions are larger.

Result: too conservative. Volatility targeting reduced both returns and drawdowns approximately equally, providing no improvement in risk-adjusted performance. The strategy already has time-based exits that limit exposure, making additional volatility scaling redundant.

### Circuit Breakers

Pause trading after N consecutive losses. Tested with N = 3, 4, 5.

Circuit breakers were marginally helpful (small DD reduction) but also caused the system to miss recovery trades. Net effect was approximately neutral.

### Breakeven Stops and Trailing Stops

- **Breakeven stops** (move stop to entry after X% profit): reduced drawdown slightly but cut win sizes, resulting in lower overall returns.
- **Trailing stops** (trail at X% behind price): similar to breakeven stops. Reduced drawdowns but also reduced the magnitude of winning trades.

## Key Findings

1. SMA200 is the single most impactful drawdown reduction tool, cutting DD from 45% to 10-12% across all tested strategies.
2. The DD reduction comes at a cost: annual returns decrease from 36.3% to 15.4% when the SMA200 filter is applied to Scale-In RSI(2).
3. Volatility targeting is too conservative for these strategies. It scales down during the exact periods (high volatility) when breakout and mean-reversion strategies generate their largest gains.
4. Circuit breakers are approximately neutral. They prevent some losses but also prevent recovery, netting out to minimal impact.
5. Breakeven and trailing stops reduce both upside and downside. For strategies with already-tight stops (1-3%), additional stop tightening is counterproductive.

## Limitations

- The SMA200 filter was tested on the same 6-year dataset used to identify the winning strategies. Out-of-sample validation of the filter itself was not conducted.
- Only the 200-day and 100-day SMA were tested as regime filters. Other regime detection methods (e.g., volatility regime, trend slope) were not explored.
- The ~40 configurations per pair represent a limited search. A more granular parameter sweep might reveal intermediate solutions between "no filter" and "SMA200 only long."
