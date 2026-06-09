"""
Etsy OAuth 2.0 setup — run this once to authorize shop management.

Two-step usage:
    Step 1: python tools/etsy_oauth.py
            Opens the auth URL. Click Allow on Etsy. Browser shows "can't connect" — that's fine.
            Copy the full URL from the address bar and paste it to Claude.

    Step 2: python tools/etsy_oauth.py --exchange "<full callback URL>"
            Claude runs this after you paste the URL. Saves tokens to .env.

After completing the flow, ETSY_ACCESS_TOKEN and ETSY_REFRESH_TOKEN
are written to your .env file automatically.
"""

import os
import sys
import json
import hashlib
import base64
import secrets
import urllib.request
import urllib.parse
import urllib.error
import tempfile

# Parse .env manually — never use load_dotenv()
_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

CLIENT_ID    = os.getenv("ETSY_CLIENT_ID", "")
REDIRECT_URI = "http://localhost:3003/callback"
AUTH_URL     = "https://www.etsy.com/oauth/connect"
TOKEN_URL    = "https://api.etsy.com/v3/public/oauth/token"
# NOTE: Etsy v3 has NO feedback_w scope — review responses cannot be posted via API.
# Reviews must be answered manually in Shop Manager or the Etsy Seller app.
SCOPES       = "shops_r shops_w listings_r listings_w listings_d transactions_r billing_r profile_r email_r feedback_r address_r"
ENV_FILE     = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
STATE_FILE   = os.path.join(tempfile.gettempdir(), "etsy_oauth_state.json")


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


def step1_generate_url():
    if not CLIENT_ID:
        print("ERROR: ETSY_CLIENT_ID not set in .env")
        sys.exit(1)

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(16)

    # Save verifier + state so step 2 can use them
    with open(STATE_FILE, "w") as f:
        json.dump({"verifier": verifier, "state": state}, f)

    params = urllib.parse.urlencode({
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "client_id":             CLIENT_ID,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "S256",
    })

    print("\n-- Etsy OAuth Setup ---------------------------------------------")
    print("Open this URL in your browser:\n")
    print(f"https://www.etsy.com/oauth/connect?{params}")
    print("\nClick Allow on Etsy.")
    print("Your browser will show \"can't connect\" — that's expected.")
    print("Copy the full URL from the address bar and paste it to Claude.")
    print("Claude will run:  python tools/etsy_oauth.py --exchange \"<url>\"")


def step2_exchange(callback_url: str):
    if not os.path.exists(STATE_FILE):
        print("ERROR: No OAuth state found. Run step 1 first: python tools/etsy_oauth.py")
        sys.exit(1)

    with open(STATE_FILE) as f:
        saved = json.load(f)
    verifier = saved["verifier"]
    state    = saved["state"]

    parsed         = urllib.parse.urlparse(callback_url)
    params         = urllib.parse.parse_qs(parsed.query)
    code           = params.get("code",  [""])[0]
    state_received = params.get("state", [""])[0]

    if not code:
        print("ERROR: No authorization code in URL.")
        sys.exit(1)

    if state_received != state:
        print("ERROR: State mismatch — run step 1 again to get a fresh URL.")
        sys.exit(1)

    token_data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "client_id":     CLIENT_ID,
        "redirect_uri":  REDIRECT_URI,
        "code":          code,
        "code_verifier": verifier,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=token_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tokens = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: {e.read().decode()}")
        sys.exit(1)

    _update_env("ETSY_ACCESS_TOKEN",   tokens.get("access_token", ""))
    _update_env("ETSY_REFRESH_TOKEN",  tokens.get("refresh_token", ""))
    # Track issue date so health_check.py can warn before 90-day refresh token expiry
    from datetime import date as _date
    _update_env("ETSY_TOKEN_ISSUED_DATE", str(_date.today()))

    os.remove(STATE_FILE)
    print("Success! Tokens saved to .env — Etsy API is now authorized.")
    print(f"Refresh token expires in 90 days — next re-auth needed by: {_date.today().replace(day=_date.today().day)}")


if __name__ == "__main__":
    if "--exchange" in sys.argv:
        idx = sys.argv.index("--exchange")
        if idx + 1 >= len(sys.argv):
            print("Usage: python tools/etsy_oauth.py --exchange \"<callback URL>\"")
            sys.exit(1)
        step2_exchange(sys.argv[idx + 1])
    else:
        step1_generate_url()
