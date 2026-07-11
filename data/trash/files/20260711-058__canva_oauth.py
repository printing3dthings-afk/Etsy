"""
Canva Connect API OAuth 2.0 setup — run this once to authorize design automation.

Two-step usage (same pattern as tools/etsy_oauth.py — manual paste, since this
sandbox cannot receive a localhost redirect):
    Step 1: python tools/canva_oauth.py
            Opens the auth URL. Click Allow on Canva. Browser shows "can't connect" — that's fine.
            Copy the full URL from the address bar and paste it to Claude.

    Step 2: python tools/canva_oauth.py --exchange "<full callback URL>"
            Claude runs this after you paste the URL. Saves tokens to .env.

Requirements in .env (set these first):
    CANVA_CLIENT_ID=your_canva_integration_client_id
    CANVA_CLIENT_SECRET=your_canva_integration_client_secret

Get these by registering an Integration at https://www.canva.com/developers/integrations
  1. Create an Integration (type: "Public" or "Private" — Private is fine for one shop)
  2. Add redirect URI: http://localhost:3005/callback
  3. Enable scopes: design:content:read design:content:write design:meta:read
     asset:read asset:write folder:read brandtemplate:meta:read
     brandtemplate:content:read profile:read
  4. Copy the Client ID and generate a Client Secret

IMPORTANT — Brand Templates cannot be created via the API. Before the autofill
pipeline (tools/canva_tools.py) is usable, Scott must manually create at least
one Brand Template in the Canva UI with named placeholder fields (e.g. a text
field called "callout_1", an image field called "photo"). The dataset for any
brand template can then be inspected with the get_brand_template_dataset tool.

After completing the OAuth flow, CANVA_ACCESS_TOKEN and CANVA_REFRESH_TOKEN
are written to your .env file automatically.
"""

import os
import sys
import json
import base64
import hashlib
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

CLIENT_ID     = os.getenv("CANVA_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CANVA_CLIENT_SECRET", "")
REDIRECT_URI  = "http://localhost:3005/callback"
AUTH_URL      = "https://www.canva.com/api/oauth/authorize"
TOKEN_URL     = "https://www.canva.com/api/oauth/token"
SCOPES        = (
    "design:content:read design:content:write design:meta:read "
    "asset:read asset:write folder:read "
    "brandtemplate:meta:read brandtemplate:content:read profile:read"
)
ENV_FILE   = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
STATE_FILE = os.path.join(tempfile.gettempdir(), "canva_oauth_state.json")


def _pkce():
    verifier  = base64.urlsafe_b64encode(secrets.token_bytes(48)).rstrip(b"=").decode()
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
        print("ERROR: CANVA_CLIENT_ID not set in .env")
        print("Register an Integration first: https://www.canva.com/developers/integrations")
        sys.exit(1)

    verifier, challenge = _pkce()
    state = secrets.token_urlsafe(16)

    with open(STATE_FILE, "w") as f:
        json.dump({"verifier": verifier, "state": state}, f)

    params = urllib.parse.urlencode({
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 SCOPES,
        "client_id":             CLIENT_ID,
        "state":                 state,
        "code_challenge":        challenge,
        "code_challenge_method": "s256",
    })

    print("\n-- Canva OAuth Setup --------------------------------------------")
    print("Open this URL in your browser:\n")
    print(f"{AUTH_URL}?{params}")
    print("\nClick Allow on Canva.")
    print("Your browser will show \"can't connect\" — that's expected.")
    print("Copy the full URL from the address bar and paste it to Claude.")
    print("Claude will run:  python tools/canva_oauth.py --exchange \"<url>\"")


def step2_exchange(callback_url: str):
    if not os.path.exists(STATE_FILE):
        print("ERROR: No OAuth state found. Run step 1 first: python tools/canva_oauth.py")
        sys.exit(1)
    if not CLIENT_SECRET:
        print("ERROR: CANVA_CLIENT_SECRET not set in .env")
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

    credentials = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    token_data = urllib.parse.urlencode({
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "code_verifier": verifier,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=token_data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type":  "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            tokens = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: {e.read().decode()}")
        sys.exit(1)

    _update_env("CANVA_ACCESS_TOKEN",  tokens.get("access_token", ""))
    _update_env("CANVA_REFRESH_TOKEN", tokens.get("refresh_token", ""))

    os.remove(STATE_FILE)
    print("Success! Tokens saved to .env — Canva API is now authorized.")
    print("Next: create at least one Brand Template in the Canva UI, then use")
    print("list_brand_templates / get_brand_template_dataset to discover its fields.")


if __name__ == "__main__":
    if "--exchange" in sys.argv:
        idx = sys.argv.index("--exchange")
        if idx + 1 >= len(sys.argv):
            print("Usage: python tools/canva_oauth.py --exchange \"<callback URL>\"")
            sys.exit(1)
        step2_exchange(sys.argv[idx + 1])
    else:
        step1_generate_url()
