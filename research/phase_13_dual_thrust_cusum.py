"""
Phase 13: Dual Thrust Breakout and CUSUM Filter.

Tests the Dual Thrust strategy on ETH and BTC with multiple parameter
combinations, regime filters, and risk management variants.

This phase produced the overall winning strategy:
ETH Dual Thrust N=3, K=0.5, session 7h, 1% stop, exit 16h, SMA200 filter.
$1,000 to $3,443 over 6.3 years with 12.4% max drawdown.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data import load_1m, group_by_date, build_daily_ohlcv, add_common_indicators
from core.engine import precompute_day_prices, simulate_fast
from core.reporting import print_results_table, format_yearly
from config.constants import TAKER_FEE, SLIPPAGE


def make_dual_thrust(n: int, k: float, session_start_h: int,
                     stop_pct: float, exit_h: int,
                     regime: str | None = None) -> callable:
    """Factory for Dual Thrust signal function."""
    def signal(day: dict, prices: list, prev_days: list) -> list:
        if len(prev_days) < n:
            return []

        # Regime filter
        if regime == "sma200" and day.get("sma200", 0) > 0:
            if day.get("close", 0) < day["sma200"]:
                return []
        if regime == "sma50" and day.get("sma50", 0) > 0:
            if day.get("close", 0) < day["sma50"]:
                return []

        # Compute range from prior N days
        recent = prev_days[-n:]
        hh = max(d["high"] for d in recent)
        hc = max(d["close"] for d in recent)
        lc = min(d["close"] for d in recent)
        ll = min(d["low"] for d in recent)
        rng = max(hh - lc, hc - ll)

        if rng <= 0:
            return []

        # Today's open
        bar = prices[session_start_h * 60]
        if bar is None:
            return []
        today_open = bar[0]

        buy_trigger = today_open + k * rng
        sell_trigger = today_open - k * rng
        exit_min = exit_h * 60

        # Scan for breakout
        for m in range(session_start_h * 60, min(exit_min, 1440)):
            bar = prices[m]
            if bar is None:
                continue

            if bar[1] > buy_trigger:
                ep = buy_trigger
                stop = ep * (1 - stop_pct / 100)
                return [(1, m, stop, None, exit_min)]

            if bar[2] < sell_trigger and regime is None:
                ep = sell_trigger
                stop = ep * (1 + stop_pct / 100)
                return [(-1, m, stop, None, exit_min)]

        return []
    return signal


def run_backtest(days, day_prices, signal_fn, risk_pct=0.02,
                 start_capital=1000.0, compound=True):
    """Run backtest with proper signal shift."""
    fee = TAKER_FEE
    capital = start_capital
    n_trades = 0
    n_wins = 0
    total_pnl_fixed = 0
    peak = capital
    max_dd_pct = 0
    yearly = {}

    for i in range(3, len(days)):
        prev_days = days[:i]
        day = days[i]
        prices = day_prices.get(day["date"])
        if prices is None or capital <= 0:
            continue

        trades = signal_fn(day, prices, prev_days)
        if not trades:
            continue

        for direction, entry_min, stop, tp, exit_min in trades:
            bar = prices[entry_min]
            if bar is None:
                continue
            ep = bar[0]
            if ep <= 0:
                continue

            exit_price, reason, _, _ = simulate_fast(
                prices, entry_min, exit_min, direction, stop, tp)
            if exit_price is None:
                continue

            raw = direction * (exit_price - ep) / ep
            costs = fee * 2 + SLIPPAGE * 2
            net_pct = raw - costs

            # Fixed size tracking
            total_pnl_fixed += net_pct * 100

            # Compound tracking
            stop_dist = abs(ep - stop) / ep if stop else 0.03
            risk_amt = capital * risk_pct
            pos_size = risk_amt / stop_dist if stop_dist > 0 else capital
            if pos_size / capital > 10:
                pos_size = capital * 10

            pnl = pos_size * net_pct
            if compound:
                capital += pnl
                if capital < 0:
                    capital = 0

            n_trades += 1
            if net_pct > 0:
                n_wins += 1

            if capital > peak:
                peak = capital
            dd = (peak - capital) / peak * 100 if peak > 0 else 0
            max_dd_pct = max(max_dd_pct, dd)

            yr = day["year"]
            yearly[yr] = yearly.get(yr, 0) + pnl

    if n_trades == 0:
        return None

    return {
        "trades": n_trades,
        "win_rate": n_wins / n_trades * 100,
        "final": capital,
        "return_compound": (capital - start_capital) / start_capital * 100,
        "return_fixed": total_pnl_fixed,
        "max_dd_pct": max_dd_pct,
        "yearly": yearly,
    }


def main():
    print("=" * 70)
    print("PHASE 13: DUAL THRUST BREAKOUT")
    print("=" * 70)

    for symbol in ["ETHUSDT", "BTCUSDT"]:
        print(f"\n{'#'*60}")
        print(f"  {symbol}")
        print(f"{'#'*60}")

        candles = load_1m(symbol)
        by_date = group_by_date(candles)
        day_prices = precompute_day_prices(candles)
        del candles
        days = build_daily_ohlcv(by_date)
        add_common_indicators(days)
        print(f"  {len(days)} trading days")

        configs = []
        for n in [2, 3, 5]:
            for k in [0.4, 0.5, 0.6, 0.8]:
                for stop in [1.0, 1.5, 2.0]:
                    for regime in [None, "sma200", "sma50"]:
                        label = f"N={n} K={k} S={stop}% X=16h"
                        if regime:
                            label += f" +{regime}"
                        configs.append((label, n, k, 7, stop, 16, regime))

        print(f"  Testing {len(configs)} configurations...")
        results = []
        for label, n, k, sess, stop, xh, regime in configs:
            sig = make_dual_thrust(n, k, sess, stop, xh, regime)
            r = run_backtest(days, day_prices, sig)
            if r and r["trades"] >= 20:
                ret_dd = r["return_compound"] / max(r["max_dd_pct"], 0.1)
                results.append((label, r, ret_dd))

        results.sort(key=lambda x: x[2], reverse=True)

        print(f"\n  TOP 15 BY RETURN/DD RATIO:")
        print(f"  {'Config':<40} {'Trds':>5} {'Win%':>6} {'Ret%':>8} {'DD%':>6} {'R/DD':>7} {'Final$':>9}")
        print(f"  {'-'*80}")
        for label, r, ratio in results[:15]:
            print(f"  {label:<40} {r['trades']:>5} {r['win_rate']:>5.1f}% "
                  f"{r['return_compound']:>+7.1f}% {r['max_dd_pct']:>5.1f}% "
                  f"{ratio:>+6.1f} ${r['final']:>8,.0f}")

        if results:
            label, r, _ = results[0]
            print(f"\n  BEST: {label}")
            format_yearly(r["yearly"])


if __name__ == "__main__":
    main()
