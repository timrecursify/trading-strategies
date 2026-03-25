"""
Statistical significance tools for strategy evaluation.
Provides Sharpe ratio with standard error, t-statistics,
walk-forward splitting, and annualized return calculation.
"""

import math

from config.constants import TRADING_DAYS_PER_YEAR


def sharpe_ratio(daily_returns: list[float]) -> tuple[float, float]:
    """
    Annualized Sharpe ratio with standard error.
    Returns (sharpe, standard_error).
    SE(Sharpe) = sqrt((1 + 0.5 * sharpe^2) / N).
    """
    n = len(daily_returns)
    if n < 2:
        return 0.0, 0.0

    mean_r = sum(daily_returns) / n
    var_r = sum((r - mean_r) ** 2 for r in daily_returns) / (n - 1)
    std_r = var_r ** 0.5

    if std_r == 0:
        return 0.0, 0.0

    daily_sharpe = mean_r / std_r
    annualized = daily_sharpe * (TRADING_DAYS_PER_YEAR ** 0.5)
    se = math.sqrt((1 + 0.5 * annualized ** 2) / n)

    return annualized, se


def t_statistic(returns: list[float]) -> tuple[float, float]:
    """
    Test whether mean return is significantly different from zero.
    Returns (t_stat, approximate_p_value).
    t = mean / (std / sqrt(N)).
    P-value approximated using normal distribution for large N.
    """
    n = len(returns)
    if n < 2:
        return 0.0, 1.0

    mean_r = sum(returns) / n
    var_r = sum((r - mean_r) ** 2 for r in returns) / (n - 1)
    std_r = var_r ** 0.5

    if std_r == 0:
        return 0.0, 1.0

    t_stat = mean_r / (std_r / math.sqrt(n))

    # Approximate two-tailed p-value using normal CDF for large N
    z = abs(t_stat)
    # Abramowitz and Stegun approximation
    b0 = 0.2316419
    b1 = 0.319381530
    b2 = -0.356563782
    b3 = 1.781477937
    b4 = -1.821255978
    b5 = 1.330274429
    t_val = 1 / (1 + b0 * z)
    poly = t_val * (b1 + t_val * (b2 + t_val * (b3 + t_val * (b4 + t_val * b5))))
    one_tail = poly * math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
    p_value = 2 * one_tail

    return t_stat, p_value


def walk_forward_split(
    items: list, ratio: float = 0.5,
) -> tuple[list, list]:
    """
    Split items into train and test sets for walk-forward validation.
    Default 50/50 split. Returns (train, test).
    """
    split_idx = int(len(items) * ratio)
    return items[:split_idx], items[split_idx:]


def annualized_return(total_return_pct: float, years: float) -> float:
    """
    Convert total return percentage to annualized (CAGR).
    Formula: (1 + total/100)^(1/years) - 1, expressed as percentage.
    """
    if years <= 0:
        return 0.0
    total_mult = 1 + total_return_pct / 100
    if total_mult <= 0:
        return -100.0
    return (total_mult ** (1 / years) - 1) * 100
