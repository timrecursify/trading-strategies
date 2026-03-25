"""
Strategy modules for the crypto futures research framework.
Each module contains factory functions that return signal callables.
"""

from strategies.session_breakout import (
    make_dual_thrust,
    make_asia_breakout,
    make_orb,
)
from strategies.mean_reversion import (
    make_rsi2_mean_reversion,
    make_ibs_mean_reversion,
    make_scale_in_rsi2,
    make_std_error_bands,
)
from strategies.trend_following import (
    make_ema_trend,
    make_supertrend,
    make_donchian_adx,
)
from strategies.smart_money import (
    make_fvg_reversion,
    make_liquidity_sweep,
    make_power_of_3,
)
from strategies.microstructure import (
    make_cvd_divergence,
    make_vwap_funding,
)
from strategies.quantitative import (
    make_pairs_trading,
    make_adaptive_regime,
)
