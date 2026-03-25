"""
Phase 14: Portfolio of Uncorrelated Strategies (FIXED).

Bug fix: SMA200 regime filter now uses PRIOR day's close, not current day's.
Tests both fixed-size and compounding to separate signal quality from compounding effects.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlite3
from datetime import datetime, timezone
from core.engine import precompute_day_prices, simulate_fast
from config.constants import TAKER_FEE, SLIPPAGE, DB_PATH


def load_1m(symbol):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        'SELECT * FROM klines WHERE symbol=? AND interval="1m" ORDER BY open_time',
        (symbol,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def group_by_date(candles):
    g = {}
    for c in candles:
        dt = datetime.fromtimestamp(c["open_time"] / 1000, tz=timezone.utc)
        g.setdefault(dt.strftime("%Y-%m-%d"), []).append(c)
    return g


def build_daily(by_date):
    days = []
    for ds in sorted(by_date.keys()):
        dc = by_date[ds]
        if len(dc) < 1400:
            continue
        days.append({
            "date": ds, "open": dc[0]["open"],
            "high": max(c["high"] for c in dc),
            "low": min(c["low"] for c in dc),
            "close": dc[-1]["close"],
            "year": ds[:4],
        })
    return days


def add_indicators(days):
    closes = [d["close"] for d in days]
    for i, d in enumerate(days):
        s200 = max(0, i - 199)
        d["sma200"] = sum(closes[s200:i+1]) / (i - s200 + 1)
        s50 = max(0, i - 49)
        d["sma50"] = sum(closes[s50:i+1]) / (i - s50 + 1)
        if i < 3:
            d["rsi2"] = 50
            continue
        g = [max(closes[j] - closes[j-1], 0) for j in range(i-1, i+1)]
        l = [max(closes[j-1] - closes[j], 0) for j in range(i-1, i+1)]
        d["rsi2"] = 100 - 100 / (1 + sum(g)/2 / (sum(l)/2)) if sum(l) > 0 else 100


def dual_thrust_trades(prev_day, prices, prev_days, n, k, session_h,
                       stop_pct, exit_h, allow_short=False):
    """Dual Thrust. Uses PREV_DAY for regime check (no look-ahead)."""
    if len(prev_days) < n:
        return []
    recent = prev_days[-n:]
    hh = max(d["high"] for d in recent)
    hc = max(d["close"] for d in recent)
    lc = min(d["close"] for d in recent)
    ll = min(d["low"] for d in recent)
    rng = max(hh - lc, hc - ll)
    if rng <= 0:
        return []

    bar = prices[session_h * 60]
    if bar is None:
        return []
    today_open = bar[0]
    buy_trigger = today_open + k * rng
    sell_trigger = today_open - k * rng

    # FIXED: regime check uses PRIOR day's close vs prior day's SMA200
    above_sma = prev_day.get("close", 0) > prev_day.get("sma200", 0)

    for m in range(session_h * 60, min(exit_h * 60, 1440)):
        bar = prices[m]
        if bar is None:
            continue
        if bar[1] > buy_trigger and above_sma:
            stop = buy_trigger * (1 - stop_pct / 100)
            return [("DT", 1, m, stop, None, exit_h * 60)]
        if bar[2] < sell_trigger and allow_short and not above_sma:
            stop = sell_trigger * (1 + stop_pct / 100)
            return [("DT", -1, m, stop, None, exit_h * 60)]
    return []


def rsi2_trades(prev_day, prices, stop_pct):
    """RSI(2) mean reversion. Signal from prior day only."""
    if prev_day.get("rsi2", 50) >= 10:
        return []
    if prev_day.get("close", 0) < prev_day.get("sma50", 0):
        return []
    bar = prices[0]
    if bar is None:
        return []
    ep = bar[0]
    stop = ep * (1 - stop_pct / 100)
    # Exit: close > yesterday's high, or 20h
    exit_min = 20 * 60
    for m in range(1, min(exit_min, 1440)):
        b = prices[m]
        if b is None:
            continue
        if b[3] > prev_day["high"]:
            exit_min = m
            break
    return [("RSI2", 1, 0, stop, None, exit_min)]


def pairs_trades(prev_btc, prev_eth, btc_prices, eth_prices, window, z_entry):
    """Pairs trading on BTC/ETH ratio. Signal from prior data only."""
    min_len = min(len(prev_btc), len(prev_eth))
    if min_len < window:
        return []
    ratios = []
    for i in range(min_len - window, min_len):
        ec = prev_eth[i]["close"]
        ratios.append(prev_btc[i]["close"] / ec if ec > 0 else 0)
    if not ratios:
        return []
    mean = sum(ratios) / len(ratios)
    std = (sum((r - mean)**2 for r in ratios) / len(ratios)) ** 0.5
    if std == 0:
        return []
    ec = prev_eth[-1]["close"]
    curr = prev_btc[-1]["close"] / ec if ec > 0 else 0
    z = (curr - mean) / std

    trades = []
    if z > z_entry:
        bb = btc_prices[0]
        eb = eth_prices[0]
        if bb and eb:
            trades.append(("PAIR_BTC", -1, 0, bb[0] * 1.03, None, 20 * 60))
            trades.append(("PAIR_ETH", 1, 0, eb[0] * 0.97, None, 20 * 60))
    elif z < -z_entry:
        bb = btc_prices[0]
        eb = eth_prices[0]
        if bb and eb:
            trades.append(("PAIR_BTC", 1, 0, bb[0] * 0.97, None, 20 * 60))
            trades.append(("PAIR_ETH", -1, 0, eb[0] * 1.03, None, 20 * 60))
    return trades


def execute_trade(prices, entry_min, exit_min, direction, stop, tp):
    bar = prices[entry_min]
    if bar is None:
        return None
    ep = bar[0]
    if ep <= 0:
        return None
    exit_price, reason, _, _ = simulate_fast(
        prices, entry_min, exit_min, direction, stop, tp)
    if exit_price is None:
        return None
    raw = direction * (exit_price - ep) / ep
    costs = TAKER_FEE * 2 + SLIPPAGE * 2
    return raw - costs


def run_portfolio(eth_days, btc_days, eth_dp, btc_dp, config):
    risk_pct = config.get("risk_pct", 0.02)
    dt_stop = config.get("dt_stop", 1.0)
    dt_k = config.get("dt_k", 0.5)
    dt_n = config.get("dt_n", 3)
    allow_short = config.get("allow_short", False)
    multi_session = config.get("multi_session", False)
    use_rsi2 = config.get("use_rsi2", True)
    use_pairs = config.get("use_pairs", True)
    use_dt = config.get("use_dt", True)
    rsi_stop = config.get("rsi_stop", 3.0)
    pairs_window = config.get("pairs_window", 100)
    pairs_z = config.get("pairs_z", 2.5)

    capital = 1000.0
    peak = capital
    max_dd_pct = 0
    yearly = {}
    counts = {"DT": 0, "RSI2": 0, "PAIR": 0}
    wins = {"DT": 0, "RSI2": 0, "PAIR": 0}
    all_pnl_pcts = []  # for fixed-size calculation

    eth_by_date = {d["date"]: (i, d) for i, d in enumerate(eth_days)}
    btc_by_date = {d["date"]: (i, d) for i, d in enumerate(btc_days)}
    all_dates = sorted(set(eth_by_date.keys()) & set(btc_by_date.keys()))

    for date_str in all_dates:
        ei, eth_day = eth_by_date[date_str]
        bi, btc_day = btc_by_date[date_str]
        eth_prices = eth_dp.get(date_str)
        btc_prices = btc_dp.get(date_str)
        if eth_prices is None or btc_prices is None or capital <= 0:
            continue
        if ei < 1 or bi < 1:
            continue

        prev_eth = eth_days[:ei]
        prev_btc = btc_days[:bi]
        prev_eth_day = eth_days[ei - 1]
        prev_btc_day = btc_days[bi - 1]
        day_pnl = 0

        # DT London (07:00)
        if use_dt and ei >= dt_n:
            for name, direction, entry_m, stop, tp, exit_m in \
                    dual_thrust_trades(prev_eth_day, eth_prices, prev_eth,
                                       dt_n, dt_k, 7, dt_stop, 16, allow_short):
                pnl_pct = execute_trade(eth_prices, entry_m, exit_m,
                                        direction, stop, tp)
                if pnl_pct is not None:
                    pos = capital * risk_pct / (dt_stop / 100)
                    if pos / capital > 10:
                        pos = capital * 10
                    pnl = pos * pnl_pct
                    day_pnl += pnl
                    all_pnl_pcts.append(pnl_pct * 100)
                    counts["DT"] += 1
                    if pnl > 0:
                        wins["DT"] += 1

        # DT NYC (12:00)
        if use_dt and multi_session and ei >= dt_n:
            for name, direction, entry_m, stop, tp, exit_m in \
                    dual_thrust_trades(prev_eth_day, eth_prices, prev_eth,
                                       dt_n, dt_k, 12, dt_stop, 20, allow_short):
                pnl_pct = execute_trade(eth_prices, entry_m, exit_m,
                                        direction, stop, tp)
                if pnl_pct is not None:
                    pos = capital * risk_pct / (dt_stop / 100)
                    if pos / capital > 10:
                        pos = capital * 10
                    pnl = pos * pnl_pct
                    day_pnl += pnl
                    all_pnl_pcts.append(pnl_pct * 100)
                    counts["DT"] += 1
                    if pnl > 0:
                        wins["DT"] += 1

        # RSI2
        if use_rsi2:
            for name, direction, entry_m, stop, tp, exit_m in \
                    rsi2_trades(prev_eth_day, eth_prices, rsi_stop):
                pnl_pct = execute_trade(eth_prices, entry_m, exit_m,
                                        direction, stop, tp)
                if pnl_pct is not None:
                    pos = capital * risk_pct / (rsi_stop / 100)
                    if pos / capital > 10:
                        pos = capital * 10
                    pnl = pos * pnl_pct
                    day_pnl += pnl
                    all_pnl_pcts.append(pnl_pct * 100)
                    counts["RSI2"] += 1
                    if pnl > 0:
                        wins["RSI2"] += 1

        # Pairs
        if use_pairs and len(prev_btc) >= pairs_window and len(prev_eth) >= pairs_window:
            for name, direction, entry_m, stop, tp, exit_m in \
                    pairs_trades(prev_btc, prev_eth, btc_prices, eth_prices,
                                 pairs_window, pairs_z):
                p = btc_prices if "BTC" in name else eth_prices
                pnl_pct = execute_trade(p, entry_m, exit_m, direction, stop, tp)
                if pnl_pct is not None:
                    pos = capital * risk_pct * 0.5 / 0.03
                    if pos / capital > 5:
                        pos = capital * 5
                    pnl = pos * pnl_pct
                    day_pnl += pnl
                    all_pnl_pcts.append(pnl_pct * 100)
                    counts["PAIR"] += 1
                    if pnl > 0:
                        wins["PAIR"] += 1

        capital += day_pnl
        if capital < 0:
            capital = 0
        if capital > peak:
            peak = capital
        dd = (peak - capital) / peak * 100 if peak > 0 else 0
        max_dd_pct = max(max_dd_pct, dd)
        yr = date_str[:4]
        yearly[yr] = yearly.get(yr, 0) + day_pnl

    total_trades = sum(counts.values())
    total_wins = sum(wins.values())

    # Fixed-size stats
    fixed_total = sum(all_pnl_pcts) if all_pnl_pcts else 0
    fixed_avg = fixed_total / len(all_pnl_pcts) if all_pnl_pcts else 0
    years = len(yearly)
    fixed_annual = fixed_total / years if years else 0

    return {
        "final": capital,
        "return_compound": (capital - 1000) / 1000 * 100,
        "max_dd": max_dd_pct,
        "yearly": yearly,
        "counts": counts, "wins": wins,
        "total_trades": total_trades,
        "win_rate": total_wins / total_trades * 100 if total_trades > 0 else 0,
        "fixed_total": fixed_total,
        "fixed_avg": fixed_avg,
        "fixed_annual": fixed_annual,
    }


def main():
    print("=" * 70)
    print("PHASE 14: PORTFOLIO (FIXED, NO LOOK-AHEAD)")
    print("SMA200 check uses PRIOR day's close. Both fixed and compound.")
    print("=" * 70)

    print("\nLoading ETH...")
    eth_c = load_1m("ETHUSDT")
    eth_bd = group_by_date(eth_c)
    eth_dp = precompute_day_prices(eth_c)
    del eth_c
    eth_days = build_daily(eth_bd)
    add_indicators(eth_days)
    print(f"  {len(eth_days)} days")

    print("Loading BTC...")
    btc_c = load_1m("BTCUSDT")
    btc_bd = group_by_date(btc_c)
    btc_dp = precompute_day_prices(btc_c)
    del btc_c
    btc_days = build_daily(btc_bd)
    add_indicators(btc_days)
    print(f"  {len(btc_days)} days")

    configs = [
        ("DT only (baseline)", {
            "use_dt": True, "use_rsi2": False, "use_pairs": False,
            "allow_short": False, "multi_session": False, "risk_pct": 0.02}),
        ("DT + shorts", {
            "use_dt": True, "use_rsi2": False, "use_pairs": False,
            "allow_short": True, "multi_session": False, "risk_pct": 0.02}),
        ("DT + NYC", {
            "use_dt": True, "use_rsi2": False, "use_pairs": False,
            "allow_short": False, "multi_session": True, "risk_pct": 0.02}),
        ("DT + shorts + NYC", {
            "use_dt": True, "use_rsi2": False, "use_pairs": False,
            "allow_short": True, "multi_session": True, "risk_pct": 0.02}),
        ("Full (DT+RSI2+Pairs)", {
            "use_dt": True, "use_rsi2": True, "use_pairs": True,
            "allow_short": False, "multi_session": False, "risk_pct": 0.02}),
        ("Full + shorts + NYC", {
            "use_dt": True, "use_rsi2": True, "use_pairs": True,
            "allow_short": True, "multi_session": True, "risk_pct": 0.02}),
        ("Full+shorts+NYC 3%risk", {
            "use_dt": True, "use_rsi2": True, "use_pairs": True,
            "allow_short": True, "multi_session": True, "risk_pct": 0.03}),
        ("Full+shorts+NYC 5%risk", {
            "use_dt": True, "use_rsi2": True, "use_pairs": True,
            "allow_short": True, "multi_session": True, "risk_pct": 0.05}),
        ("Full+shorts+NYC 1%risk", {
            "use_dt": True, "use_rsi2": True, "use_pairs": True,
            "allow_short": True, "multi_session": True, "risk_pct": 0.01}),
    ]

    print(f"\nTesting {len(configs)} configs...\n")

    print(f"{'Config':<35} {'Trds':>5} {'Win%':>6} "
          f"{'FixAvg%':>8} {'FixAnn%':>8} "
          f"{'Cmp$':>10} {'CmpRet%':>9} {'DD%':>6} "
          f"{'DT':>4} {'RSI':>4} {'PR':>4}")
    print("-" * 110)

    results = []
    for label, cfg in configs:
        r = run_portfolio(eth_days, btc_days, eth_dp, btc_dp, cfg)
        results.append((label, r))
        tc = r["counts"]
        print(f"{label:<35} {r['total_trades']:>5} {r['win_rate']:>5.1f}% "
              f"{r['fixed_avg']:>+7.3f}% {r['fixed_annual']:>+7.1f}% "
              f"${r['final']:>9,.0f} {r['return_compound']:>+8.1f}% {r['max_dd']:>5.1f}% "
              f"{tc['DT']:>4} {tc['RSI2']:>4} {tc['PAIR']:>4}")

    # Yearly for top 3 by fixed annual
    results.sort(key=lambda x: x[1]["fixed_annual"], reverse=True)
    print(f"\n{'='*70}")
    print("YEARLY: TOP 3 BY FIXED-SIZE ANNUAL %")
    print(f"{'='*70}")

    for label, r in results[:3]:
        print(f"\n  {label}")
        print(f"  Trades: {r['total_trades']} | Fixed avg: {r['fixed_avg']:+.3f}%/trade "
              f"| Fixed annual: {r['fixed_annual']:+.1f}%")
        print(f"  Compounded: ${r['final']:,.0f} ({r['return_compound']:+.1f}%) | DD: {r['max_dd']:.1f}%")
        tc, tw = r["counts"], r["wins"]
        for s in ["DT", "RSI2", "PAIR"]:
            if tc[s] > 0:
                print(f"    {s}: {tc[s]} trades, {tw[s]} wins ({tw[s]/tc[s]*100:.1f}%)")
        print(f"  {'Year':<6} {'P&L$':>10} {'Cum$':>10}")
        print(f"  {'-'*28}")
        cum = 1000
        for yr in sorted(r["yearly"]):
            pnl = r["yearly"][yr]
            cum += pnl
            bar = "+" * min(int(abs(pnl)/10), 30) if pnl > 0 else "-" * min(int(abs(pnl)/10), 30)
            print(f"  {yr:<6} ${pnl:>+9,.0f} ${cum:>9,.0f} {bar}")


if __name__ == "__main__":
    main()
