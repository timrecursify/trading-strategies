# Phase 3: V2 Alternative Strategies

## Objective

Test 1,188 alternative strategy combinations beyond session continuation, including reversals, pure trend following, volatility breakout, and multi-trade scalping approaches.

## Data

- Period: 2025-03-25 to 2026-03-24 (364 trading days)
- Symbols: BTCUSDT, ETHUSDT
- Combinations: 1,188 per symbol

## Strategy Types Tested

1. **REVERSAL:** Trade against London direction at NYC open
2. **TREND:** Follow daily 20 EMA direction at NYC open (ignore sessions)
3. **VOLATILITY BREAKOUT:** Enter when price breaks ATR threshold
4. **ASIA RANGE BREAKOUT:** Trade Asia high/low break at London open
5. **BIG MOVE CONTINUATION:** Only trade when London moved >X%
6. **MULTI-TRADE SCALP:** Up to 5 momentum scalps per session
7. **LONDON-NYC REVERSAL + CONTINUATION:** 2-trade reversal then continuation
8. **SESSION EMA SCALP:** Multiple trades following short-term EMA

## Results

### BTC Top 5 by Sharpe

| # | Strategy | Trades | Win% | PF | Return | Sharpe | DD% |
|---|----------|--------|------|----|--------|--------|-----|
| 1 | TREND 12:00 S1.5% R3.0 X20 | 364 | 52.5% | 1.43 | 160.7% | 2.74 | 14.2% |
| 2 | TREND 12:00 S2.0% R3.0 X20 | 364 | 53.6% | 1.47 | 114.3% | 2.74 | 11.4% |
| 3 | TREND 12:00 S2.0% R2.0 X20 | 364 | 53.6% | 1.44 | 107.3% | 2.70 | 11.4% |
| 4 | TREND 13:00 S1.5% R3.0 X20 | 364 | 50.3% | 1.41 | 141.1% | 2.59 | 14.4% |
| 5 | TREND 12:00 S2.0% R3.0 X21 | 364 | 52.7% | 1.45 | 107.8% | 2.59 | 12.4% |

### ETH Top 5 by Sharpe

| # | Strategy | Trades | Win% | PF | Return | Sharpe | DD% |
|---|----------|--------|------|----|--------|--------|-----|
| 1 | ASIA_BRK S0.5% R1.0 X12 | 216 | 62.5% | 2.35 | 1,590% | 5.90 | 14.7% |
| 2 | ASIA_BRK S0.5% R1.0 X16 | 216 | 62.5% | 2.16 | 1,464% | 5.63 | 16.2% |
| 3 | ASIA_BRK S0.5% R1.0 X18 | 216 | 62.5% | 2.15 | 1,459% | 5.60 | 16.2% |
| 4 | ASIA_BRK S0.5% R1.0 X20 | 216 | 62.5% | 2.15 | 1,458% | 5.60 | 16.2% |
| 5 | ASIA_BRK S0.5% R1.0 X14 | 216 | 62.0% | 2.12 | 1,335% | 5.49 | 17.9% |

### Walk-Forward Validation

**BTC TREND: All top 10 passed.**

| # | Strategy | Train Sharpe | Test Sharpe | Degradation | Verdict |
|---|----------|--------------|-------------|-------------|---------|
| 1 | TREND 12:00 S1.5% R3.0 X20 | 2.35 | 3.08 | -31% | PASS |
| 2 | TREND 12:00 S2.0% R3.0 X20 | 2.41 | 3.06 | -27% | PASS |
| 3 | TREND 12:00 S2.0% R2.0 X20 | 2.50 | 2.90 | -16% | PASS |
| 4 | TREND 13:00 S1.5% R3.0 X20 | 2.48 | 2.73 | -10% | PASS |

Negative degradation indicates the strategy improved in the out-of-sample period.

**ETH ASIA BREAKOUT: All top 5 passed.**

| # | Strategy | Train Sharpe | Test Sharpe | Degradation | Verdict |
|---|----------|--------------|-------------|-------------|---------|
| 1 | ASIA_BRK S0.5% R1.0 X12 | 6.64 | 5.10 | 23% | PASS |
| 2 | ASIA_BRK S0.5% R1.0 X16 | 6.12 | 5.10 | 17% | PASS |
| 3 | ASIA_BRK S0.5% R1.0 X18 | 6.04 | 5.13 | 15% | PASS |

### Strategy Types That Failed

| Strategy | BTC Best Sharpe | ETH Best Sharpe | Verdict |
|----------|-----------------|-----------------|---------|
| REVERSAL | -2.16 | -1.15 | Loses money on both |
| SCALP (multi-trade) | -4.22 | -1.92 | Destroyed by fees |
| EMA SCALP | -4.30 | -2.39 | Destroyed by fees |
| REV+CONT | -3.77 | -1.46 | Loses money |
| VOLATILITY BREAKOUT | -1.49 (BTC) | +2.74 (ETH) | ETH only, high DD |

### Best Per Strategy Type

| Type | BTC Best | ETH Best |
|------|----------|----------|
| TREND | Sharpe 2.74, Ret 161% | Sharpe 3.25, Ret 283% |
| ASIA_BRK | Sharpe -0.36 (does not work) | Sharpe 5.90, Ret 1,590% |
| BIGMV | Sharpe 1.10, Ret 25% | Sharpe 2.34, Ret 82% |
| VOLBRK | Negative | Sharpe 2.74, Ret 881% |

### Monthly P&L: ETH Asia Breakout #1

| Month | P&L |
|-------|-----|
| 2025-04 | +$46 |
| 2025-05 | +$92 |
| 2025-06 | +$117 |
| 2025-07 | +$8 |
| 2025-08 | +$180 |
| 2025-09 | -$2 |
| 2025-10 | +$134 |
| 2025-11 | +$57 |
| 2025-12 | +$185 |
| 2026-01 | +$106 |
| 2026-02 | +$357 |
| 2026-03 | +$316 |

11 out of 12 full months profitable. Average winning trade duration: 38 minutes.

## Key Findings

1. TREND following (20 EMA direction) is the most robust strategy type, with Sharpe 2.74 on BTC and all top 10 passing walk-forward.
2. ETH Asia Range Breakout produced Sharpe 5.90 with 62.5% win rate on 1 year of data. (Later invalidated as period-dependent in Phase 8.)
3. Multi-trade strategies (scalping, EMA scalp) are destroyed by fees. Sharpe ratios of -4.22 and -4.30 confirm that high-frequency approaches are unviable at retail fee levels.
4. REVERSAL strategies lose money on both pairs. Fading London direction is not a source of edge.
5. Asia Breakout does not work on BTC (Sharpe -0.36) but is the strongest ETH signal. The pairs respond to different market structures.

## Limitations

- All results are on 1 year of data. The Asia Breakout Sharpe of 5.90 was later shown to degrade to ~1.10 on 6 years (Phase 8).
- The 1,590% return on ETH Asia Breakout includes compounding effects that inflate the headline number. Fixed-size returns are more representative for strategy comparison.
- Walk-forward validation on 1 year uses only ~182 days per fold, providing limited statistical power.
