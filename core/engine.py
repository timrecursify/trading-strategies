"""
Optimized backtest engine. Pre-computes minute-indexed price arrays once,
then all parameter combos scan compact float arrays with no datetime parsing,
no dict lookups, no re-grouping per backtest.
"""

from datetime import datetime, timezone

from config.constants import (
    TAKER_FEE, MAKER_FEE, SLIPPAGE, FUNDING_RATE,
)
from core.sessions import pct_change


def precompute_day_prices(candles_1m: list[dict]) -> dict[str, list]:
    """Convert 1m candles into {date_str: [1440 tuples of (O,H,L,C)]}."""
    day_prices: dict[str, list] = {}
    for c in candles_1m:
        ot = c["open_time"]
        dt = datetime.fromtimestamp(ot / 1000, tz=timezone.utc)
        date_str = dt.strftime("%Y-%m-%d")
        minute = dt.hour * 60 + dt.minute

        if date_str not in day_prices:
            day_prices[date_str] = [None] * 1440

        day_prices[date_str][minute] = (
            c["open"], c["high"], c["low"], c["close"],
        )

    return day_prices


def simulate_fast(
    prices: list, entry_min: int, exit_min: int,
    direction: int, stop_price: float, tp_price: float | None,
) -> tuple[float | None, str, int, int]:
    """Fast trade simulation. Returns (exit_price, reason, exit_minute, minutes_held)."""
    ep = prices[entry_min]
    if ep is None:
        return None, "no_entry", entry_min, 0
    entry_price = ep[0]

    for m in range(entry_min + 1, min(exit_min + 1, 1440)):
        bar = prices[m]
        if bar is None:
            continue
        o, h, l, cl = bar

        # Stop loss check (conservative: if both hit in same bar, stop wins)
        if direction == 1:
            if l <= stop_price:
                exit_p = min(stop_price, o)
                return exit_p, "stop", m, m - entry_min
        else:
            if h >= stop_price:
                exit_p = max(stop_price, o)
                return exit_p, "stop", m, m - entry_min

        # Take profit check
        if tp_price is not None:
            if direction == 1 and h >= tp_price:
                return tp_price, "tp", m, m - entry_min
            if direction == -1 and l <= tp_price:
                return tp_price, "tp", m, m - entry_min

    # Time exit
    bar = prices[min(exit_min, 1439)]
    if bar:
        return bar[0], "time", exit_min, exit_min - entry_min

    # Fallback: scan backward for last valid price
    for m in range(min(exit_min, 1439), entry_min, -1):
        if prices[m]:
            return prices[m][3], "time", m, m - entry_min

    return entry_price, "time", exit_min, exit_min - entry_min


def simulate_with_trailing(
    prices: list, entry_min: int, exit_min: int, direction: int,
    stop_price: float, tp_price: float | None,
    trail_atr: float | None, be_rr: float | None,
    atr_val: float | None, fee: float,
) -> tuple[float | None, str, int, int]:
    """Simulation with trailing stop and breakeven. Used for top combos only."""
    ep = prices[entry_min]
    if ep is None:
        return None, "no_entry", entry_min, 0
    entry_price = ep[0]
    current_stop = stop_price
    be_triggered = False
    risk = abs(entry_price - stop_price)

    for m in range(entry_min + 1, min(exit_min + 1, 1440)):
        bar = prices[m]
        if bar is None:
            continue
        o, h, l, cl = bar

        # Breakeven logic
        if be_rr and not be_triggered and risk > 0:
            be_target = entry_price + direction * risk * be_rr
            if (direction == 1 and h >= be_target) or (
                direction == -1 and l <= be_target
            ):
                current_stop = entry_price + direction * entry_price * fee * 2
                be_triggered = True

        # Trailing stop
        if trail_atr and atr_val and be_triggered:
            trail_d = trail_atr * atr_val
            if direction == 1:
                ns = h - trail_d
                if ns > current_stop:
                    current_stop = ns
            else:
                ns = l + trail_d
                if ns < current_stop:
                    current_stop = ns

        # Stop check
        if direction == 1 and l <= current_stop:
            return min(current_stop, o), "stop", m, m - entry_min
        if direction == -1 and h >= current_stop:
            return max(current_stop, o), "stop", m, m - entry_min

        # TP check
        if tp_price is not None:
            if direction == 1 and h >= tp_price:
                return tp_price, "tp", m, m - entry_min
            if direction == -1 and l <= tp_price:
                return tp_price, "tp", m, m - entry_min

    bar = prices[min(exit_min, 1439)]
    if bar:
        return bar[0], "time", exit_min, exit_min - entry_min
    return entry_price, "time", exit_min, 0


def compute_stop(
    entry_price: float, direction: int, stop_type: str, stop_val: float,
    lkz_h: float | None, lkz_l: float | None,
    lkz_mid: float | None, atr: float | None,
) -> float:
    """Compute stop price based on stop type and parameters."""
    if stop_type == "fixed_pct":
        return entry_price * (1 - direction * stop_val / 100)
    elif stop_type == "lkz_extreme":
        return lkz_l if direction == 1 else lkz_h
    elif stop_type == "lkz_mid":
        return lkz_mid if lkz_mid else entry_price * (1 - direction * 0.005)
    elif stop_type == "atr":
        if atr is None:
            return entry_price * (1 - direction * 0.005)
        return entry_price - direction * atr * stop_val
    return entry_price * (1 - direction * 0.005)


def compute_tp(
    entry_price: float, stop_price: float, direction: int, rr: float | None,
) -> float | None:
    """Compute take-profit price from risk-reward ratio."""
    if rr is None:
        return None
    risk = abs(entry_price - stop_price)
    return entry_price + direction * risk * rr


def get_signal(day: dict, variant: str) -> int:
    """Get trade direction for a given day and signal variant."""
    if variant == "A":
        ld = day["london_dir"]
        return 1 if ld > 0 else (-1 if ld < 0 else 0)
    elif variant == "B":
        entry = day.get("_entry_price")
        if entry is None:
            entry = day["nyc_12"]
        if entry and day["lkz_high"] and entry > day["lkz_high"]:
            return 1
        if entry and day["lkz_low"] and entry < day["lkz_low"]:
            return -1
        return 0
    elif variant == "C":
        if (day["asia_dir"] > 0) == (day["london_dir"] > 0):
            return 1 if day["london_dir"] > 0 else -1
        return 0
    elif variant == "D":
        lkz_h, lkz_l = day["lkz_high"], day["lkz_low"]
        asia_h, asia_l = day["asia_high"], day["asia_low"]
        lo = day["london_open"]
        nc = day["nyc_12"]
        if not all([lkz_h, lkz_l, asia_h, asia_l, lo, nc]):
            return 0
        ld = pct_change(lo, nc)
        if lkz_h > asia_h and ld < 0:
            return -1
        if lkz_l < asia_l and ld > 0:
            return 1
        return 0
    return 0


# Entry time to minute-of-day mapping
ENTRY_MINUTES: dict[tuple[int, int], int] = {
    (12, 0): 720, (12, 30): 750, (13, 0): 780,
    (13, 30): 810, (14, 0): 840,
}

# Entry time to day_metrics key mapping
ENTRY_KEYS: dict[tuple[int, int], str] = {
    (12, 0): "nyc_12", (12, 30): "nyc_1230", (13, 0): "nyc_13",
    (13, 30): "nyc_1330", (14, 0): "nyc_14",
}


def run_backtest(
    all_days: list[dict], day_prices: dict,
    variant: str, entry_h: int, entry_m: int,
    stop_type: str, stop_val: float, exit_type: str, exit_val: float,
    fee_mode: str = "taker", sizing_mode: str = "fixed_risk",
    risk_pct: float = 0.02, max_leverage: int = 10,
    trailing_atr: float | None = None, breakeven_rr: float | None = None,
    filters: list | None = None, start_capital: float = 100, lite: bool = True,
) -> dict:
    """Run backtest using pre-computed day_prices. lite=True skips trade storage."""
    fee = TAKER_FEE if fee_mode == "taker" else MAKER_FEE
    entry_min = ENTRY_MINUTES[(entry_h, entry_m)]
    entry_key = ENTRY_KEYS[(entry_h, entry_m)]

    capital = start_capital
    n_trades = 0
    n_wins = 0
    gross_win = 0.0
    gross_loss = 0.0
    peak = capital
    max_dd_pct = 0.0
    max_consec = 0
    cur_consec = 0
    liquidations = 0
    total_pnl = 0.0
    monthly_pnl: dict[str, float] = {}
    win_min_sum = 0
    loss_min_sum = 0
    trades = [] if not lite else None
    equity = [capital] if not lite else None
    daily_returns: list[float] = []

    for day in all_days:
        prev_cap = capital

        if filters:
            skip = False
            for f in filters:
                if not f(day):
                    skip = True
                    break
            if skip:
                daily_returns.append(0)
                if equity is not None:
                    equity.append(capital)
                continue

        direction = get_signal(day, variant)
        if direction == 0:
            daily_returns.append(0)
            if equity is not None:
                equity.append(capital)
            continue

        date_str = day["date"]
        prices = day_prices.get(date_str)
        if prices is None:
            daily_returns.append(0)
            if equity is not None:
                equity.append(capital)
            continue

        # Entry price
        entry_price = day.get(entry_key)
        if entry_price is None:
            bar = prices[entry_min]
            entry_price = bar[0] if bar else None
        if entry_price is None or capital <= 0:
            daily_returns.append(0)
            if equity is not None:
                equity.append(capital)
            continue

        # Variant B: re-check signal with actual entry price
        if variant == "B":
            day["_entry_price"] = entry_price
            direction = get_signal(day, variant)
            if direction == 0:
                daily_returns.append(0)
                if equity is not None:
                    equity.append(capital)
                continue

        # Stop
        stop_price = compute_stop(
            entry_price, direction, stop_type, stop_val,
            day["lkz_high"], day["lkz_low"], day["lkz_mid"], day["atr"],
        )
        stop_dist = abs(entry_price - stop_price) / entry_price

        # Position sizing
        if sizing_mode == "fixed_leverage":
            pos_size = capital * max_leverage
        else:
            risk_amt = capital * risk_pct
            pos_size = (
                (risk_amt / stop_dist) if stop_dist > 0
                else capital * max_leverage
            )
            if pos_size / capital > max_leverage:
                pos_size = capital * max_leverage

        lev = pos_size / capital if capital > 0 else 0

        # Exit time
        if exit_type == "rr":
            tp = compute_tp(entry_price, stop_price, direction, exit_val)
            exit_minute = 21 * 60
        elif exit_type == "time":
            tp = None
            exit_minute = exit_val * 60
        elif exit_type == "rr_or_time":
            rr, th = exit_val
            tp = compute_tp(entry_price, stop_price, direction, rr)
            exit_minute = th * 60
        elif exit_type == "12pm_et":
            tp = None
            exit_minute = day["et_exit_hour"] * 60
        elif exit_type == "rr_or_12pm_et":
            tp = compute_tp(entry_price, stop_price, direction, exit_val)
            exit_minute = day["et_exit_hour"] * 60
        else:
            tp = None
            exit_minute = 21 * 60

        # Simulate
        if trailing_atr or breakeven_rr:
            result = simulate_with_trailing(
                prices, entry_min, exit_minute, direction,
                stop_price, tp, trailing_atr, breakeven_rr,
                day["atr"], fee,
            )
        else:
            result = simulate_fast(
                prices, entry_min, exit_minute, direction,
                stop_price, tp,
            )

        exit_price, reason, exit_cm, minutes = result
        if exit_price is None:
            daily_returns.append(0)
            if equity is not None:
                equity.append(capital)
            continue

        # Liquidation check
        liq_dist = 1 / lev if lev > 0 else 1
        if direction == 1:
            liq_price = entry_price * (1 - liq_dist + fee * 2)
            got_liq = exit_price <= liq_price
        else:
            liq_price = entry_price * (1 + liq_dist - fee * 2)
            got_liq = exit_price >= liq_price

        if got_liq:
            pnl = -capital
            reason = "liq"
            liquidations += 1
        else:
            raw_pnl_pct = direction * (exit_price - entry_price) / entry_price
            costs = fee * 2 + SLIPPAGE * 2
            if entry_min < 960 <= exit_cm:
                costs += FUNDING_RATE
            pnl = pos_size * (raw_pnl_pct - costs)

        capital += pnl
        if capital < 0:
            capital = 0
        total_pnl += pnl
        n_trades += 1

        if pnl > 0:
            n_wins += 1
            gross_win += pnl
            win_min_sum += minutes
            cur_consec = 0
        else:
            gross_loss += abs(pnl)
            loss_min_sum += minutes
            cur_consec += 1
            max_consec = max(max_consec, cur_consec)

        if capital > peak:
            peak = capital
        dd_pct = (peak - capital) / peak if peak > 0 else 0
        max_dd_pct = max(max_dd_pct, dd_pct)

        month_key = date_str[:7]
        monthly_pnl[month_key] = monthly_pnl.get(month_key, 0) + pnl
        daily_returns.append(pnl / prev_cap if prev_cap > 0 else 0)

        if trades is not None:
            trades.append({
                "date": date_str, "dir": direction,
                "entry": entry_price, "exit": exit_price,
                "pnl": pnl, "reason": reason, "min": minutes,
                "lev": lev, "cap": capital,
            })
        if equity is not None:
            equity.append(capital)

    return _build_metrics(
        n_trades, n_wins, gross_win, gross_loss, total_pnl,
        max_consec, max_dd_pct, capital, start_capital,
        daily_returns, liquidations, monthly_pnl,
        win_min_sum, loss_min_sum, trades, equity,
    )


def _build_metrics(
    n_trades: int, n_wins: int, gross_win: float, gross_loss: float,
    total_pnl: float, max_consec: int, max_dd_pct: float,
    final_cap: float, start_cap: float, daily_returns: list[float],
    liqs: int, monthly_pnl: dict, win_min_sum: int, loss_min_sum: int,
    trades: list | None, equity: list | None,
) -> dict:
    """Build metrics dictionary from raw backtest results."""
    if n_trades == 0:
        return {"total_trades": 0, "valid": False}

    n_losses = n_trades - n_wins
    wr = n_wins / n_trades * 100
    avg_w = gross_win / n_wins if n_wins else 0
    avg_l = -gross_loss / n_losses if n_losses else 0
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    ev = total_pnl / n_trades
    ret = ((final_cap - start_cap) / start_cap) * 100

    # Sharpe
    if len(daily_returns) > 1:
        mean_r = sum(daily_returns) / len(daily_returns)
        var_r = sum((r - mean_r) ** 2 for r in daily_returns) / (
            len(daily_returns) - 1
        )
        std_r = var_r ** 0.5
        sharpe = (mean_r / std_r) * (365 ** 0.5) if std_r > 0 else 0
    else:
        sharpe = 0

    calmar = ret / (max_dd_pct * 100) if max_dd_pct > 0 else 0

    return {
        "total_trades": n_trades, "win_rate": wr,
        "avg_win": avg_w, "avg_loss": avg_l,
        "profit_factor": pf, "ev_per_trade": ev,
        "max_consec_losses": max_consec,
        "max_dd_pct": max_dd_pct * 100,
        "final_capital": final_cap, "total_return": ret,
        "sharpe": sharpe, "calmar": calmar,
        "liquidations": liqs,
        "avg_win_time": win_min_sum / n_wins if n_wins else 0,
        "avg_loss_time": loss_min_sum / n_losses if n_losses else 0,
        "monthly_pnl": monthly_pnl,
        "trades": trades, "equity": equity,
        "valid": True,
    }
