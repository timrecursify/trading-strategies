"""
CLI entry point for multi-symbol multi-strategy paper trading.

Usage:
  python paper_main.py setup_dt <london|nyc>
  python paper_main.py setup_ab
  python paper_main.py scan_daily
  python paper_main.py tick
  python paper_main.py exit_session <london|nyc>
  python paper_main.py exit_ab
  python paper_main.py status
"""

import fcntl
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from live.paper_api import get_batch_prices
from live.paper_portfolio import (
    load_state, save_state, init_db, print_status, ps,
)
from live.paper_strategies import (
    setup_dual_thrust, setup_asia_breakout, scan_rsi2, scan_pairs,
    tick_dual_thrust, tick_asia_breakout, monitor_positions,
    exit_session_positions, exit_asia_breakout, cleanup_expired_pending,
)
from config.symbols import PAPER_SYMBOLS

LOCK_FILE = "paper_v2.lock"


def acquire_lock():
    """Non-blocking file lock. Returns lock fd or None if already locked."""
    fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return fd
    except BlockingIOError:
        fd.close()
        return None


def release_lock(fd):
    if fd:
        fcntl.flock(fd, fcntl.LOCK_UN)
        fd.close()


def cmd_setup_dt(session):
    init_db()
    state = load_state()
    prices = get_batch_prices(PAPER_SYMBOLS)
    setup_dual_thrust(state, session, prices)
    save_state(state)


def cmd_setup_ab():
    init_db()
    state = load_state()
    prices = get_batch_prices(PAPER_SYMBOLS)
    setup_asia_breakout(state, prices)
    save_state(state)


def cmd_scan_daily():
    init_db()
    state = load_state()
    prices = get_batch_prices(PAPER_SYMBOLS)
    scan_rsi2(state, prices)
    scan_pairs(state, prices)
    save_state(state)


def cmd_tick():
    state = load_state()
    if not state.get("pending") and not state.get("positions"):
        return
    try:
        prices = get_batch_prices(PAPER_SYMBOLS)
    except Exception as e:
        ps(f"TICK: API error, skipping: {e}")
        return
    tick_dual_thrust(state, prices)
    tick_asia_breakout(state, prices)
    monitor_positions(state, prices)
    cleanup_expired_pending(state)
    save_state(state)


def cmd_exit_session(session):
    state = load_state()
    has_dt = any(
        p["strategy"] == "dual_thrust" and p.get("session") == session
        for p in state["positions"].values()
    )
    if not has_dt:
        ps(f"[DT] No {session} positions to close.")
        return
    prices = get_batch_prices(PAPER_SYMBOLS)
    exit_session_positions(state, session, prices)
    save_state(state)


def cmd_exit_ab():
    state = load_state()
    has_ab = any(
        p["strategy"] == "asia_breakout"
        for p in state["positions"].values()
    )
    if not has_ab:
        ps(f"[AB] No positions to close.")
        return
    prices = get_batch_prices(PAPER_SYMBOLS)
    exit_asia_breakout(state, prices)
    save_state(state)


def cmd_status():
    init_db()
    state = load_state()
    print_status(state)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    action = sys.argv[1]

    if action == "status":
        cmd_status()
        return

    lock_fd = acquire_lock()
    if lock_fd is None:
        return

    try:
        if action == "setup_dt":
            session = sys.argv[2] if len(sys.argv) > 2 else None
            if session not in ("london", "nyc"):
                ps("Usage: setup_dt <london|nyc>")
                return
            cmd_setup_dt(session)
        elif action == "setup_ab":
            cmd_setup_ab()
        elif action == "scan_daily":
            cmd_scan_daily()
        elif action == "tick":
            cmd_tick()
        elif action == "exit_session":
            session = sys.argv[2] if len(sys.argv) > 2 else None
            if session not in ("london", "nyc"):
                ps("Usage: exit_session <london|nyc>")
                return
            cmd_exit_session(session)
        elif action == "exit_ab":
            cmd_exit_ab()
        else:
            ps(f"Unknown command: {action}")
    finally:
        release_lock(lock_fd)


if __name__ == "__main__":
    main()
