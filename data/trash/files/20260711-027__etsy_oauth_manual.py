"""
Etsy OAuth 2.0 — manual callback mode.

Use when localhost:3003 is not accessible from your browser
(e.g., running on a remote server / Claude Code on the web).

Usage:
    python tools/etsy_oauth_manual.py

Steps:
    1. Script prints an authorization URL — open it in your browser
    2. Click "Allow Access" on Etsy
    3. Your browser redirects to localhost:3003/callback?code=...&state=...
       (the page won't load — that's fine)
    4. Copy the FULL URL from your browser address bar and paste it here
    5. Tokens are saved to .env automatically
"""

import os, sys, json, hashlib, base64, secrets, urllib.request, urllib.parse, urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

# Load .env
if os.path.exists(ENV_FILE):
    with open(ENV_FILE) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

CLIENT_ID     = os.environ.get("ETSY_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ETSY_CLIENT_SECRET", "")
REDIRECT_URI  = "http://localhost:3003/callback"
AUTH_URL      = "https://www.etsy.com/oauth/connect"
TOKEN_URL     = "https://api.etsy.com/v3/public/oauth/token"
SCOPES        = "shops_r shops_w listings_r listings_w transactions_r billing_r profile_r email_r feedback_r address_r"


def _pkce():
    verifier  = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


def _update_env(key: str, value: str) -> None:
    lines = []
    found = False
    if os.path.exists(ENV_FILE):
        with open(ENV_FILE) as f:
            lines = f.readlines()
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}\n"
            found = True
            break
    if not found:
        lines.append(f"{key}={value}\n")
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)


def main():
    if not CLIENT_ID:
        print("ERROR: ETSY_CLIENT_ID not set in .env")
        sys.exit(1)

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(16)

    params = urllib.parse.urlencode({
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "client_id":             CLIENT_ID,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "S256",
    })

    auth_link = f"{AUTH_URL}?{params}"

    print()
    print("=" * 60)
    print("  Etsy OAuth Setup — Manual Callback Mode")
    print("=" * 60)
    print()
    print("STEP 1 — Open this URL in your browser:")
    print()
    print(f"  {auth_link}")
    print()
    print("STEP 2 — Click 'Allow Access' on Etsy.")
    print()
    print("STEP 3 — Your browser will redirect to a page that")
    print("  won't load (localhost:3003). That's expected.")
    print("  Copy the FULL URL from your browser address bar.")
    print()
    print("STEP 4 — Paste the full URL here and press Enter:")
    print()

    try:
        callback_url = input("  Paste URL > ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nCancelled.")
        sys.exit(0)

    # Parse code and state from the pasted URL
    parsed = urllib.parse.urlparse(callback_url)
    params_received = urllib.parse.parse_qs(parsed.query)

    auth_code       = params_received.get("code",  [""])[0]
    state_received  = params_received.get("state", [""])[0]

    if not auth_code:
        # Maybe they just pasted the code directly
        if len(callback_url) > 10 and " " not in callback_url and "?" not in callback_url:
            auth_code = callback_url
            state_received = state  # trust it
        else:
            print("\nERROR: Could not find 'code' in the pasted URL.")
            print("Make sure you copied the full URL from the address bar.")
            sys.exit(1)

    if state_received != state:
        print("\nERROR: State mismatch — possible CSRF. Aborting.")
        sys.exit(1)

    print()
    print("  Exchanging code for tokens...")

    token_data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "code":          auth_code,
        "code_verifier": verifier,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"\nERROR: Token exchange failed: {body}")
        sys.exit(1)

    access_token  = tokens.get("access_token",  "")
    refresh_token = tokens.get("refresh_token", "")

    if not access_token:
        print(f"\nERROR: No access token in response: {tokens}")
        sys.exit(1)

    _update_env("ETSY_ACCESS_TOKEN",  access_token)
    _update_env("ETSY_REFRESH_TOKEN", refresh_token)

    print()
    print("=" * 60)
    print("  SUCCESS — Tokens saved to .env")
    print("=" * 60)
    print()
    print("  Your shop agents can now publish listings,")
    print("  upload files, manage orders, and more.")
    print()


if __name__ == "__main__":
    main()
