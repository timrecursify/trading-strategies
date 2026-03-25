"""
Strategy parameter grids used across research phases.
Centralizes all tested parameter combinations for reproducibility.
"""

# Dual Thrust (winning strategy)
DUAL_THRUST = {
    "n_days": [2, 3, 5, 7],
    "k_mult": [0.3, 0.4, 0.5, 0.6, 0.7, 0.8],
    "session_start_h": [0, 7, 12],
    "stop_pct": [1.0, 1.5, 2.0, 3.0],
    "exit_h": [8, 12, 16],
    "regime_filters": [None, "sma50", "sma200"],
    "risk_pct": [0.01, 0.02],
    # Best config: N=3, K=0.5, session=7h, stop=1%, exit=16h, sma200, risk=2%
}

# Asia Range Breakout
ASIA_BREAKOUT = {
    "stop_pct": [0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0],
    "rr": [0.5, 1.0, 1.5, 2.0, 3.0, 4.0],
    "exit_h": [9, 10, 11, 12, 14, 16, 20],
    "asia_hours": [(0, 7), (1, 7), (2, 7)],
    "breakout_hours": [(7, 8), (7, 9), (7, 10), (7, 12)],
    "risk_pct": [0.02, 0.03, 0.05],
    "buffers": [0, 0.05, 0.1],
    "min_range_pct": [0, 0.2, 0.5],
}

# Scale-In RSI(2)
SCALE_IN_RSI2 = {
    "rsi_period": [2, 3],
    "rsi_threshold": [5, 10, 15, 20],
    "scale_in_rsi_drop": [5],  # add when 5-day RSI drops by this many points
    "stop_pct": [1.5, 2.0, 3.0, 5.0],
    "risk_pct": [0.01, 0.02],
    "regime_filters": [None, "sma50", "sma200"],
    "exit_rule": ["prev_high", "time_20h"],
}

# Session-based grid (V1, Phase 2)
V1_GRID = {
    "variants": ["A", "B", "C", "D"],
    "entries": [(12, 0), (12, 30), (13, 0), (13, 30), (14, 0)],
    "stop_types": [
        ("fixed_pct", 0.25), ("fixed_pct", 0.5), ("fixed_pct", 0.75),
        ("fixed_pct", 1.0), ("fixed_pct", 1.5), ("fixed_pct", 2.0),
        ("lkz_extreme", None), ("lkz_mid", None),
        ("atr", 1.0), ("atr", 1.5), ("atr", 2.0),
    ],
    "exit_types": [
        ("rr", 1.0), ("rr", 1.5), ("rr", 2.0), ("rr", 3.0),
        ("time", 14), ("time", 15), ("time", 16), ("time", 17),
        ("time", 18), ("time", 19), ("time", 20), ("time", 21),
        ("12pm_et", None),
    ],
}

# Technical indicator filter thresholds (Phase 6)
INDICATOR_FILTERS = {
    "rsi14_thresholds": [30, 35, 45, 55, 65, 70],
    "bb_std_devs": [1.0, 1.5, 2.0],
    "adx_thresholds": [20, 25, 30, 35],
    "stochastic_thresholds": [20, 80],
}

# Pairs trading (Phase 15)
PAIRS_TRADING = {
    "windows": [20, 30, 50, 100],
    "z_entry": [1.5, 2.0, 2.5, 3.0],
    "z_exit": [0.0, 0.5, 1.0],
    "max_hold_days": [5, 10, 20],
}
