#!/usr/bin/env bash
# OnBrandCraftz — Linux Setup Script
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"

echo ""
echo "======================================================"
echo "  OnBrandCraftz — Setup (Linux)"
echo "======================================================"
echo ""

# 1. Check Python
if ! command -v python3 &>/dev/null; then
  echo "  ERROR: python3 not found. Please install Python 3 first." >&2
  exit 1
fi
echo "  Python 3 is installed: $(python3 --version)"

# 2. Check virtual environment
if [ ! -d venv ]; then
  echo "  Creating virtual environment 'venv'..."
  python3 -m venv --without-pip venv
  echo "  Installing pip inside virtual environment..."
  curl -sS https://bootstrap.pypa.io/get-pip.py | ./venv/bin/python3
fi

# 3. Install packages
echo "  Installing required packages..."
./venv/bin/pip install -r requirements.txt --quiet
echo "  Packages installed successfully."
echo ""

# 4. Setup .env file
if [ ! -f .env ]; then
  cp .env.example .env
  echo "  Created .env file from .env.example."
else
  echo "  .env file already exists."
fi

# Generate APP_SECRET_TOKEN if not set
if grep -q "APP_SECRET_TOKEN=$" .env || grep -q "APP_SECRET_TOKEN=\s*$" .env; then
  RAND_SECRET=$(./venv/bin/python3 -c "import secrets; print(secrets.token_urlsafe(32))")
  sed -i "s|^APP_SECRET_TOKEN=.*|APP_SECRET_TOKEN=$RAND_SECRET|" .env
  echo "  Generated a new random APP_SECRET_TOKEN."
fi

# Update default business fields if still default/blank
sed -i "s|^BUSINESS_NAME=.*|BUSINESS_NAME=OnBrandCraftz|" .env
sed -i "s|^OWNER_NAME=.*|OWNER_NAME=Scott|" .env
sed -i "s|^AGENT_NAME=.*|AGENT_NAME=Frank|" .env
sed -i "s|^BUSINESS_DESCRIPTION=.*|BUSINESS_DESCRIPTION=Digital planners, kawaii sticker packs, printable digital products, 3D printed physical products|" .env

# Check Anthropic API Key
if grep -q "ANTHROPIC_API_KEY=sk-" .env; then
  echo "  Anthropic API key is already configured in .env."
else
  echo "  ======================================================"
  echo "    Enter your Anthropic API key"
  echo "  ======================================================"
  echo "  Get your key at: https://console.anthropic.com"
  echo ""
  read -rp "  Paste your key (starts with sk-) and press Enter: " APIKEY
  if [ -n "$APIKEY" ]; then
    sed -i "s|^ANTHROPIC_API_KEY=.*|ANTHROPIC_API_KEY=$APIKEY|" .env
    echo "  API key saved to .env."
  else
    echo "  No key entered. You can edit .env manually later to add it."
  fi
fi

echo ""
echo "======================================================"
echo "  Setup complete!"
echo "  To launch the app:"
echo "    - Local mode:        ./start.sh"
echo "    - Cloudflare tunnel:  ./start.sh --tunnel"
echo "======================================================"
echo ""
