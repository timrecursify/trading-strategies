"""
Core modules for the crypto futures research framework.
"""

from core.data import load_1m, group_by_date, build_daily_ohlcv, add_common_indicators
from core.engine import precompute_day_prices, simulate_fast, run_backtest
from core.sessions import load_all, pct_change
from core.statistics import sharpe_ratio, t_statistic, walk_forward_split
from core.reporting import print_results_table, format_yearly
