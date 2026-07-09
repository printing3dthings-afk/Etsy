"""
TikTok OAuth 2.0 — get an access token for @onbrandcraftz

Usage:
  python tools/tiktok_oauth.py

Steps:
  1. Script opens the TikTok authorization URL in your browser
  2. Log in as @onbrandcraftz and approve the app
  3. TikTok redirects to localhost:3005/callback
  4. Script captures the code and exchanges it for tokens
  5. Tokens saved to .env automatically

Token lifetimes:
  Access token:  24 hours
  Refresh token: 365 days

Re-run this script whenever the access token expires (or run tiktok_refresh.py for silent refresh).
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
import threading
import time
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"

CLIENT_KEY    = os.getenv("TIKTOK_CLIENT_KEY", "awwqfpmeze4ksjm4")
CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "Fgq1xaYUbAUEElf2pfokELTbqnk3ylIB")
REDIRECT_URI  = "http://localhost:3005/callback"
SCOPES        = "video.publish,video.upload,user.info.basic"

AUTH_URL   = "https://www.tiktok.com/v2/auth/authorize/"
TOKEN_URL  = "https://open.tiktokapis.com/v2/oauth/token/"

_code_holder: dict = {}
_state = secrets.token_urlsafe(16)

# PKCE
_code_verifier  = secrets.token_urlsafe(64)
_code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(_code_verifier.encode()).digest()
).rstrip(b"=").decode()


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _code_holder["code"]  = params["code"][0]
            _code_holder["state"] = params.get("state", [""])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Authorization successful! Return to your terminal.</h2>")
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Error: {error}</h2>".encode())

    def log_message(self, *args):
        pass  # suppress server logs


def _start_callback_server() -> HTTPServer:
    server = HTTPServer(("localhost", 3005), _CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def _exchange_code(code: str) -> dict:
    payload = urllib.parse.urlencode({
        "client_key":     CLIENT_KEY,
        "client_secret":  CLIENT_SECRET,
        "code":           code,
        "grant_type":     "authorization_code",
        "redirect_uri":   REDIRECT_URI,
        "code_verifier":  _code_verifier,
    }).encode()
    req = urllib.request.Request(
        TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _save_tokens(data: dict) -> None:
    access_token  = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    open_id       = data.get("open_id", "")

    env_text = ENV_PATH.read_text()
    for key, val in [
        ("TIKTOK_ACCESS_TOKEN",  access_token),
        ("TIKTOK_REFRESH_TOKEN", refresh_token),
        ("TIKTOK_OPEN_ID",       open_id),
    ]:
        if f"{key}=" in env_text:
            lines = env_text.splitlines()
            new_lines = []
            for line in lines:
                if line.startswith(f"{key}="):
                    new_lines.append(f"{key}={val}")
                else:
                    new_lines.append(line)
            env_text = "\n".join(new_lines) + "\n"
        else:
            env_text += f"\n{key}={val}\n"
    ENV_PATH.write_text(env_text)
    print(f"  Saved TIKTOK_ACCESS_TOKEN  ({len(access_token)} chars)")
    print(f"  Saved TIKTOK_REFRESH_TOKEN ({len(refresh_token)} chars)")
    print(f"  Saved TIKTOK_OPEN_ID       {open_id}")


def main() -> None:
    print("=" * 60)
    print("TikTok OAuth — OnBrandCraftz")
    print("=" * 60)

    params = {
        "client_key":            CLIENT_KEY,
        "response_type":         "code",
        "scope":                 SCOPES,
        "redirect_uri":          REDIRECT_URI,
        "state":                 _state,
        "code_challenge":        _code_challenge,
        "code_challenge_method": "S256",
    }
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n1. Starting local callback server on port 3005...")
    server = _start_callback_server()

    print("2. Opening TikTok authorization page in browser...")
    print(f"\n   URL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("3. Log in as @onbrandcraftz and approve the app.")
    print("   Waiting for TikTok to redirect back...\n")

    timeout = 120
    start = time.time()
    while "code" not in _code_holder and time.time() - start < timeout:
        time.sleep(0.5)

    server.shutdown()

    if "code" not in _code_holder:
        print("ERROR: Timed out waiting for authorization code.")
        return

    if _code_holder.get("state") != _state:
        print("ERROR: State mismatch — possible CSRF. Aborting.")
        return

    code = _code_holder["code"]
    print(f"4. Got authorization code. Exchanging for tokens...")

    try:
        token_data = _exchange_code(code)
    except Exception as e:
        print(f"ERROR exchanging code: {e}")
        return

    if "access_token" not in token_data:
        print(f"ERROR: Unexpected response: {json.dumps(token_data, indent=2)}")
        return

    print("5. Tokens received! Saving to .env...")
    _save_tokens(token_data)

    expires_in = token_data.get("expires_in", 86400)
    print(f"\nSuccess! Access token expires in {expires_in // 3600} hours.")
    print("Run python tools/tiktok_poster.py to post your first video.")


if __name__ == "__main__":
    main()
