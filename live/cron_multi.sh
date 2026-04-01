#!/bin/bash
# Multi-Strategy Paper Trading Cron Setup
# Install: copy lines below into `crontab -e` on VPS
#
# Strategies: Dual Thrust (8 symbols x 2 sessions), Asia Breakout (8 symbols),
#             Scale-In RSI(2) (8 symbols), Pairs Trading (BTC/ETH)
#
# Before installing, back up existing crontab:
#   crontab -l > ~/crontab_backup_$(date +%Y%m%d).txt

DIR=~/projects/trading-strategies
LOG=$DIR/paper_v2.log
PY=/usr/bin/python3
MAIN=live/paper_main.py

cat << 'EOF'
# === Multi-Strategy Paper Trading ===
# Daily: RSI2 + Pairs scan (00:05 UTC)
5 0 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py scan_daily >> paper_v2.log 2>&1

# London DT setup (07:00 UTC)
0 7 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py setup_dt london >> paper_v2.log 2>&1

# Asia Breakout setup (07:02 UTC)
2 7 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py setup_ab >> paper_v2.log 2>&1

# NYC DT setup (12:00 UTC)
0 12 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py setup_dt nyc >> paper_v2.log 2>&1

# Tick: check signals + monitor (every 60s)
* * * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py tick >> paper_v2.log 2>&1

# Asia Breakout time exit (12:02 UTC)
2 12 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py exit_ab >> paper_v2.log 2>&1

# DT London time exit (16:00 UTC)
0 16 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py exit_session london >> paper_v2.log 2>&1

# DT NYC time exit (20:00 UTC)
0 20 * * * cd ~/projects/trading-strategies && /usr/bin/python3 live/paper_main.py exit_session nyc >> paper_v2.log 2>&1
EOF
