#!/usr/bin/env bash
# Run Frank (tools/api_server/main.py) on this machine, no Railway required.
# Offline/local fallback launcher — see the plan referenced in CLAUDE.md.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

if [ ! -f .env ]; then
  echo "ERROR: .env not found in $(pwd)." >&2
  echo "Copy .env.example to .env and fill in at least ANTHROPIC_API_KEY and APP_SECRET_TOKEN." >&2
  exit 1
fi

set -a
source .env
set +a

if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ERROR: ANTHROPIC_API_KEY is not set in .env." >&2
  exit 1
fi
if [ -z "${APP_SECRET_TOKEN:-}" ]; then
  echo "ERROR: APP_SECRET_TOKEN is not set in .env." >&2
  exit 1
fi

echo "Installing/checking dependencies..."
pip install -q -r requirements.txt

export PORT="${PORT:-8011}"
echo ""
echo "Starting Frank locally at http://localhost:${PORT}/frank"
echo "(Ctrl+C to stop)"
echo ""
python tools/api_server/main.py
