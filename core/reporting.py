"""
Standardized result formatting for consistent terminal output.
Provides table printing and yearly P&L visualization.
"""


def print_results_table(
    results: list[tuple],
    sort_key: str = "sharpe",
    n: int = 25,
) -> None:
    """
    Print a formatted results table sorted by sort_key.
    Each result is a tuple of (label: str, metrics: dict).
    Metrics dict must have: total_trades, win_rate, profit_factor,
    total_return, sharpe, max_dd_pct, ev_per_trade.
    """
    valid = [
        (label, m) for label, m in results
        if m.get("valid", True) and m.get("total_trades", 0) >= 1
    ]
    valid.sort(key=lambda x: x[1].get(sort_key, 0), reverse=True)

    print(
        f"{'#':>3} {'Strategy':<45} {'Trds':>5} {'Win%':>6} {'PF':>6} "
        f"{'Ret%':>9} {'Shrp':>7} {'DD%':>6} {'EV':>8}"
    )
    print("-" * 100)

    for i, (label, m) in enumerate(valid[:n]):
        print(
            f"{i+1:>3} {label:<45} "
            f"{m.get('total_trades', 0):>5} "
            f"{m.get('win_rate', 0):>5.1f}% "
            f"{m.get('profit_factor', 0):>6.2f} "
            f"{m.get('total_return', 0):>8.1f}% "
            f"{m.get('sharpe', 0):>7.2f} "
            f"{m.get('max_dd_pct', 0):>5.1f}% "
            f"{m.get('ev_per_trade', 0):>7.2f}"
        )


def format_yearly(yearly_pnl: dict[str, float]) -> None:
    """
    Print yearly P&L with visual bars.
    yearly_pnl is {year_str: dollar_pnl}.
    """
    if not yearly_pnl:
        print("  No yearly data.")
        return

    print(f"  {'Year':<6} {'P&L':>12}  Bar")
    print(f"  {'-'*40}")
    for year in sorted(yearly_pnl.keys()):
        pnl = yearly_pnl[year]
        bar_len = min(int(abs(pnl)), 40)
        bar = ("+" * bar_len) if pnl > 0 else ("-" * bar_len)
        print(f"  {year:<6} {pnl:>+11.2f}  {bar}")
