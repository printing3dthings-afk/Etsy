#!/usr/bin/env bash
# OnBrandCraftz — Start server + Cloudflare Tunnel
# Usage:  ./start.sh           (no tunnel, local only)
#         ./start.sh --tunnel  (with public Cloudflare URL)

set -e
cd "$(dirname "$0")"

PORT=8080
TUNNEL=false
[[ "$1" == "--tunnel" ]] && TUNNEL=true

echo ""
echo "======================================================"
echo "  OnBrandCraftz — Etsy Agent Hub"
echo "======================================================"

# Load .env
[ -f .env ] && export $(grep -v '^#' .env | xargs)

# Verify API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "  ERROR: ANTHROPIC_API_KEY not set in .env"
  exit 1
fi
echo "  Anthropic API: loaded (${ANTHROPIC_API_KEY:0:12}...)"

# Start server in background
echo "  Starting server on port $PORT..."
PYTHON_CMD="python3"
if [ -d venv ]; then
  PYTHON_CMD="./venv/bin/python"
elif command -v python &>/dev/null; then
  PYTHON_CMD="python"
fi
$PYTHON_CMD town_app/server.py &
SERVER_PID=$!

# Give server a moment to bind
sleep 2

if $TUNNEL; then
  echo ""
  echo "  Starting Cloudflare Tunnel..."
  echo "  (public URL will appear below — share it or open on phone)"
  echo ""

  # Check if cloudflared is installed globally or locally
  CF_CMD="cloudflared"
  if ! command -v cloudflared &>/dev/null; then
    if [ ! -f ./cloudflared ]; then
      echo "  cloudflared not found. Downloading (~40 MB, one time)..."
      curl -L -o ./cloudflared "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
      chmod +x ./cloudflared
      echo "  cloudflared downloaded."
      echo ""
    fi
    CF_CMD="./cloudflared"
  fi

  # Run cloudflared, parse the URL from its output, post it to the server
  $CF_CMD tunnel --url "http://localhost:$PORT" --no-autoupdate 2>&1 | while IFS= read -r line; do
    echo "  [tunnel] $line"
    # cloudflared prints the URL like: https://xxxx.trycloudflare.com
    if [[ "$line" =~ (https://[a-z0-9-]+\.trycloudflare\.com) ]]; then
      URL="${BASH_REMATCH[1]}"
      echo ""
      echo "  ┌─────────────────────────────────────────────────┐"
      echo "  │  PUBLIC URL: $URL"
      echo "  │  Open this on your phone — works anywhere!      │"
      echo "  └─────────────────────────────────────────────────┘"
      echo ""
      # Post URL to server so town UI can display it
      curl -sS -X POST "http://localhost:$PORT/api/tunnel-url" \
           -H "Content-Type: application/json" \
           -d "{\"url\":\"$URL\"}" > /dev/null 2>&1 || true
    fi
  done &
  TUNNEL_PID=$!
fi

# Wait for server (Ctrl+C kills both)
cleanup() {
  echo ""
  echo "  Shutting down..."
  kill $SERVER_PID 2>/dev/null || true
  $TUNNEL && kill $TUNNEL_PID 2>/dev/null || true
  # Clear tunnel URL
  curl -sS -X POST "http://localhost:$PORT/api/tunnel-url" \
       -H "Content-Type: application/json" \
       -d '{"url":""}' > /dev/null 2>&1 || true
  exit 0
}
trap cleanup INT TERM

echo "  Local:  http://localhost:$PORT"
echo "  Press Ctrl+C to stop"
echo ""

wait $SERVER_PID
