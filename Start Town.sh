#!/usr/bin/env bash
# OnBrandCraftz Town - Linux Launcher
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo ""
echo "======================================================"
echo "  OnBrandCraftz Town - Starting..."
echo "======================================================"
echo ""

# 1. Pull latest code (if git is configured)
if command -v git &>/dev/null && [ -d .git ]; then
  echo "  Checking for updates..."
  if git pull --ff-only &>/dev/null; then
    echo "  Up to date."
  else
    echo "  Could not auto-update - continuing."
  fi
  echo ""
fi

# 2. Check if setup is needed
if [ ! -f .env ] || ! grep -q "ANTHROPIC_API_KEY=sk-" .env; then
  echo "  [!] Environment setup required."
  ./setup.sh
fi

# Reload env to make sure ANTHROPIC_API_KEY is available
if [ -f .env ]; then
  # Load env variables safely (skipping comments)
  set -a
  source <(grep -v '^#' .env | sed 's/\r$//')
  set +a
fi

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "  ERROR: ANTHROPIC_API_KEY not set in .env. Cannot start Town." >&2
  exit 1
fi

# 3. Port check and clean up
PORT=8080
if command -v fuser &>/dev/null; then
  PID=$(fuser "$PORT"/tcp 2>/dev/null || true)
  if [ -n "$PID" ]; then
    echo "  Stopping old server on port $PORT (PID $PID)..."
    kill -9 $PID || true
    sleep 1
  fi
elif command -v lsof &>/dev/null; then
  PID=$(lsof -t -i :"$PORT" || true)
  if [ -n "$PID" ]; then
    echo "  Stopping old server on port $PORT (PID $PID)..."
    kill -9 $PID || true
    sleep 1
  fi
fi

# 4. Ask for access mode
echo "  How do you want to access the Town?"
echo ""
echo "    [1]  Local only   (same WiFi)"
echo "    [2]  Public URL   (anywhere, free - no account needed)"
echo ""
read -rp "  Enter 1 or 2 then press Enter: " ACCESS_MODE
echo ""

if [ "${ACCESS_MODE:-1}" = "2" ]; then
  ./start.sh --tunnel
else
  ./start.sh
fi
