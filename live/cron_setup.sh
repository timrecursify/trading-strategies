#!/bin/bash
# Cron jobs for paper trading bot
# Install: crontab -e, then paste these lines

DIR="/Users/timvoss/Projects/day_trading"
PYTHON="/opt/homebrew/bin/python3"
LOG="$DIR/paper_trader.log"

# Daily entry scan at 07:00 UTC
# (adjust for your timezone — 07:00 UTC = 02:00 EST = 01:00 CST)
echo "0 7 * * * cd $DIR && $PYTHON paper_trader.py scan >> $LOG 2>&1"

# Monitor every 5 minutes from 07:00-16:00 UTC (while potentially in position)
echo "*/5 7-15 * * * cd $DIR && $PYTHON paper_trader.py monitor >> $LOG 2>&1"

# Daily exit at 16:00 UTC
echo "0 16 * * * cd $DIR && $PYTHON paper_trader.py exit >> $LOG 2>&1"

echo ""
echo "To install, run: crontab -e"
echo "Then paste the 3 lines above (without the echo commands)."
echo ""
echo "Or to test immediately:"
echo "  python3 paper_trader.py status   — check state"
echo "  python3 paper_trader.py scan     — simulate entry scan"
echo "  python3 paper_trader.py exit     — close any position"
