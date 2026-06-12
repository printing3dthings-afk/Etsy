"""
Etsy OAuth 2.0 setup — run once to authorize shop management.
Usage: python tools/etsy_oauth.py
Requires in .env: ETSY_CLIENT_ID, ETSY_CLIENT_SECRET
Saves ETSY_ACCESS_TOKEN and ETSY_REFRESH_TOKEN to .env on success.
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
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

CLIENT_ID = os.getenv("ETSY_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("ETSY_CLIENT_SECRET", "")
REDIRECT_URI = "http://localhost:3003/callback"
AUTH_URL = "https://www.etsy.com/oauth/connect"
TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"
SCOPES = "shops_r shops_w listings_r listings_w transactions_r billing_r profile_r email_r feedback_r address_r"
ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

_auth_code = ""
_state_received = ""


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code, _state_received
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _auth_code = params.get("code", [""])[0]
        _state_received = params.get("state", [""])[0]
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"<h2>Authorization complete! You can close this tab.</h2>")

    def log_message(self, *args):
        pass


def _pkce():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
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
        "response_type": "code", "redirect_uri": REDIRECT_URI,
        "scope": SCOPES, "client_id": CLIENT_ID, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    print("\n-- Etsy OAuth Setup ---")
    print("Open this URL in your browser:\n")
    print(f"{AUTH_URL}?{params}")
    print("\nWaiting for Etsy callback...")

    HTTPServer(("localhost", 3003), CallbackHandler).handle_request()

    if not _auth_code or _state_received != state:
        print("ERROR: Auth failed.")
        sys.exit(1)

    token_data = urllib.parse.urlencode({
        "grant_type": "authorization_code", "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI, "code": _auth_code, "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=token_data,
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as resp:
            tokens = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"Token exchange failed: {e.read().decode()}")
        sys.exit(1)

    _update_env("ETSY_ACCESS_TOKEN", tokens.get("access_token", ""))
    _update_env("ETSY_REFRESH_TOKEN", tokens.get("refresh_token", ""))
    print("\nSuccess! Tokens saved to .env")


if __name__ == "__main__":
    main()
