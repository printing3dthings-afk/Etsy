"""
Pinterest OAuth 2.0 setup — run once to authorize pin posting.

Usage:
    python tools/pinterest_oauth.py

Requirements in .env:
    PINTEREST_APP_ID=your_app_id
    PINTEREST_APP_SECRET=your_app_secret

After completing, PINTEREST_ACCESS_TOKEN and PINTEREST_REFRESH_TOKEN
are saved to .env. The Social Media Agent can then post pins directly.
"""

import os
import sys
import json
import secrets
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

APP_ID = os.getenv("PINTEREST_APP_ID", "")
APP_SECRET = os.getenv("PINTEREST_APP_SECRET", "")
REDIRECT_URI = "http://localhost:3004/callback"
AUTH_URL = "https://www.pinterest.com/oauth/"
TOKEN_URL = "https://api.pinterest.com/v5/oauth/token"
SCOPES = "pins:write,boards:read,boards:write,user_accounts:read"

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

_auth_code = ""
_state_received = ""


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code, _state_received
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        _auth_code = params.get("code", [""])[0]
        _state_received = params.get("state", [""])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Pinterest connected! You can close this tab.</h2>")

    def log_message(self, *args):
        pass


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
    if not APP_ID or not APP_SECRET:
        print("ERROR: PINTEREST_APP_ID and PINTEREST_APP_SECRET not set in .env")
        print("Get them from https://developers.pinterest.com/ → your app")
        sys.exit(1)

    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        "client_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "state": state,
    })

    print("\n── Pinterest OAuth Setup ────────────────────────────────")
    print("Open this URL in your browser to connect your Pinterest:\n")
    print(f"{AUTH_URL}?{params}")
    print("\nWaiting for Pinterest to redirect back...")

    server = HTTPServer(("localhost", 3004), CallbackHandler)
    server.handle_request()

    if not _auth_code:
        print("ERROR: No code received.")
        sys.exit(1)
    if _state_received != state:
        print("ERROR: State mismatch. Aborting.")
        sys.exit(1)

    # Exchange code for tokens
    credentials = urllib.parse.quote(f"{APP_ID}:{APP_SECRET}")
    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": _auth_code,
        "redirect_uri": REDIRECT_URI,
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL,
        data=token_data,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: {e.read().decode()}")
        sys.exit(1)

    _update_env("PINTEREST_ACCESS_TOKEN", tokens.get("access_token", ""))
    _update_env("PINTEREST_REFRESH_TOKEN", tokens.get("refresh_token", ""))

    print("\nSuccess! Pinterest connected and tokens saved to .env")
    print("The Social Media Agent can now post pins directly.")


if __name__ == "__main__":
    main()
