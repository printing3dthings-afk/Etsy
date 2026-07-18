"""
Google Calendar OAuth 2.0 — get an access token so Frank can read and write
events on your Google Calendar.

Usage:
  python tools/google_calendar_oauth.py

One-time setup (Google Cloud Console, console.cloud.google.com):
  1. Create a project (or reuse one) and enable the "Google Calendar API"
     under APIs & Services > Library.
  2. APIs & Services > OAuth consent screen: set it up (External is fine for
     a single-user shop; add your own Google account as a test user if the
     app stays in "Testing" status).
  3. APIs & Services > Credentials > Create Credentials > OAuth client ID.
     Application type: "Desktop app".
  4. Register this exact redirect URI: http://localhost:3006/callback
  5. Copy the generated Client ID / Client Secret into .env as
     GOOGLE_CALENDAR_CLIENT_ID / GOOGLE_CALENDAR_CLIENT_SECRET.

Steps this script runs:
  1. Starts a local callback server on port 3006.
  2. Opens the Google consent screen in your browser.
  3. Approve access — Google redirects back to localhost:3006/callback.
  4. Script captures the code and exchanges it for tokens.
  5. Tokens saved to .env and encrypted-at-rest in the local database.

access_type=offline + prompt=consent are required on the auth URL below --
without both, Google only issues a refresh token on a user's very FIRST
ever consent for this app, silently omitting it on every re-run after that
(a real gotcha that doesn't apply to Etsy/Pinterest/TikTok's flows).

Token lifetimes:
  Access token:  1 hour
  Refresh token: does not expire on its own (can be revoked from
                 myaccount.google.com/permissions)

Re-run this script if the refresh token is ever revoked or .env is lost.
"""
from __future__ import annotations

import json
import os
import secrets
import threading
import time
import urllib.parse
import requests
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"

# Load .env into the process environment before reading CLIENT_ID/CLIENT_SECRET
# below -- bug fixed 2026-07-18 (reproduced live): this script previously read
# straight from os.getenv() with nothing ever populating it from .env, so it
# printed "must be set in .env" and refused to start even when the values
# were genuinely present in .env, for every single run. setdefault() so a
# real shell-exported env var still wins over the file, same idiom
# tools/etsy_api.py / tools/google_calendar_api.py already use.
if ENV_PATH.exists():
    with open(ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

CLIENT_ID     = os.getenv("GOOGLE_CALENDAR_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GOOGLE_CALENDAR_CLIENT_SECRET", "")
REDIRECT_URI  = "http://localhost:3006/callback"
SCOPES        = "https://www.googleapis.com/auth/calendar"

AUTH_URL  = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"

_code_holder: dict = {}
_state = secrets.token_urlsafe(16)


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        if "code" in params:
            _code_holder["code"] = params["code"][0]
            _code_holder["state"] = params.get("state", [""])[0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Google Calendar connected! Return to your terminal.</h2>")
        else:
            error = params.get("error", ["unknown"])[0]
            self.send_response(400)
            self.end_headers()
            self.wfile.write(f"<h2>Error: {error}</h2>".encode())

    def log_message(self, *args):
        pass  # suppress server logs


def _start_callback_server() -> HTTPServer:
    server = HTTPServer(("localhost", 3006), _CallbackHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server


def _exchange_code(code: str) -> dict:
    payload = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI,
    }
    resp = requests.post(TOKEN_URL, data=payload, timeout=30)
    return resp.json()


def _save_tokens(data: dict) -> None:
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")

    env_text = ENV_PATH.read_text() if ENV_PATH.exists() else ""
    for key, val in [
        ("GOOGLE_CALENDAR_ACCESS_TOKEN", access_token),
        ("GOOGLE_CALENDAR_REFRESH_TOKEN", refresh_token),
    ]:
        if not val:
            continue  # never blank out an existing refresh token with an empty re-consent response
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
    print(f"  Saved GOOGLE_CALENDAR_ACCESS_TOKEN  ({len(access_token)} chars)")
    if refresh_token:
        print(f"  Saved GOOGLE_CALENDAR_REFRESH_TOKEN ({len(refresh_token)} chars)")
    else:
        print("  No refresh token in this response (already authorized before? "
              "Google only issues one on first consent -- revoke access at "
              "myaccount.google.com/permissions and re-run this script if you "
              "need a fresh one).")

    # Also write into the local DB (encrypted at rest, same as Etsy tokens) so
    # the running server picks it up without needing a restart to re-read .env.
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent / "api_server"))
        import db as _db
        existing = _db.get_google_calendar_tokens() or {}
        _db.save_google_calendar_tokens(
            access_token or existing.get("access_token", ""),
            refresh_token or existing.get("refresh_token", ""),
        )
        print("  Saved to local database (encrypted at rest if TOKEN_ENCRYPTION_KEY is set).")
    except Exception as exc:
        print(f"  NOTE: could not also save to the local database ({exc}) -- "
              ".env is updated, which is enough; the running server will pick "
              "it up on next restart.")


def main() -> None:
    print("=" * 60)
    print("Google Calendar OAuth — OnBrandCraftz")
    print("=" * 60)

    if not CLIENT_ID or not CLIENT_SECRET:
        print("ERROR: GOOGLE_CALENDAR_CLIENT_ID and GOOGLE_CALENDAR_CLIENT_SECRET must be set in .env")
        print("See this script's module docstring for the Google Cloud Console setup steps.")
        return

    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "scope": SCOPES,
        "redirect_uri": REDIRECT_URI,
        "state": _state,
        "access_type": "offline",
        "prompt": "consent",
    }
    auth_url = AUTH_URL + "?" + urllib.parse.urlencode(params)

    print("\n1. Starting local callback server on port 3006...")
    server = _start_callback_server()

    print("2. Opening Google's authorization page in browser...")
    print(f"\n   URL: {auth_url}\n")
    webbrowser.open(auth_url)

    print("3. Log in and approve calendar access.")
    print("   Waiting for Google to redirect back...\n")

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
    print("4. Got authorization code. Exchanging for tokens...")

    try:
        token_data = _exchange_code(code)
    except Exception as e:
        print(f"ERROR exchanging code: {e}")
        return

    if "access_token" not in token_data:
        print(f"ERROR: Unexpected response: {json.dumps(token_data, indent=2)}")
        return

    print("5. Tokens received! Saving...")
    _save_tokens(token_data)

    expires_in = token_data.get("expires_in", 3600)
    print(f"\nSuccess! Access token expires in {expires_in // 60} minutes (auto-refreshed after that).")
    print("Frank's Calendar tab will now show your upcoming Google Calendar events.")


if __name__ == "__main__":
    main()
