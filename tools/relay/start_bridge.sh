#!/bin/bash
# Keeps the Bambu P1S bridge running on a Mac or Linux laptop at home (Scott, 2026-10-24).
# Fetches the latest code before every start and restarts the bridge if it stops.
cd "$(dirname "$0")/../.." || exit 1
while true; do
  git pull --ff-only
  python3 tools/relay/bambu_p1s_bridge.py
  echo "[$(date)] bridge stopped; restarting in 15 seconds"
  sleep 15
done
