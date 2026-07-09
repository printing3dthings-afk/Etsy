"""
Pinterest API v5 client — direct pin posting, board management.

Setup (one-time):
  1. Go to https://developers.pinterest.com/
  2. Sign in with your Pinterest account (printing3dthings)
  3. Click "New App" → fill in name/description → Submit
  4. Copy your App ID and App Secret key
  5. Add to .env:
       PINTEREST_APP_ID=your_app_id
       PINTEREST_APP_SECRET=your_app_secret
  6. Run: python tools/pinterest_oauth.py
     (opens browser, you approve, tokens saved automatically)

After setup, the Social Media Agent can post pins directly.
"""
from __future__ import annotations

import os
import json
import base64
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

BASE_URL = "https://api.pinterest.com/v5"


class PinterestAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Pinterest API {status}: {message}")


class PinterestClient:
    """Pinterest API v5 client."""

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN", "")

    def _update_env(self, key: str, value: str) -> None:
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

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the stored refresh token.

        Uses PINTEREST_APP_ID and PINTEREST_APP_SECRET from env for Basic auth.
        On success, updates self.access_token and persists both tokens to .env.
        Returns True on success, False on failure.
        """
        app_id = os.getenv("PINTEREST_APP_ID", "")
        app_secret = os.getenv("PINTEREST_APP_SECRET", "")
        refresh_token = os.getenv("PINTEREST_REFRESH_TOKEN", "")

        if not app_id or not app_secret or not refresh_token:
            return False

        credentials = base64.b64encode(f"{app_id}:{app_secret}".encode()).decode()
        token_data = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }).encode()

        req = urllib.request.Request(
            "https://api.pinterest.com/v5/oauth/token",
            data=token_data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read().decode())
        except Exception:
            return False

        new_access_token = tokens.get("access_token", "")
        new_refresh_token = tokens.get("refresh_token", "")
        if not new_access_token:
            return False

        self.access_token = new_access_token
        self._update_env("PINTEREST_ACCESS_TOKEN", new_access_token)
        if new_refresh_token:
            self._update_env("PINTEREST_REFRESH_TOKEN", new_refresh_token)
        return True

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        if not self.access_token:
            raise PinterestAPIError(
                0,
                "No Pinterest access token. Run 'python tools/pinterest_oauth.py' to connect your account.",
            )

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 401 and self.access_token:
                if self.refresh_access_token():
                    # Retry once with the new token
                    headers["Authorization"] = f"Bearer {self.access_token}"
                    req2 = urllib.request.Request(url, data=data, headers=headers, method=method)
                    try:
                        with urllib.request.urlopen(req2, timeout=15) as resp:
                            return json.loads(resp.read().decode())
                    except urllib.error.HTTPError as e2:
                        body_text = e2.read().decode()
                        try:
                            err = json.loads(body_text)
                            msg = err.get("message", body_text)
                        except Exception:
                            msg = body_text
                        raise PinterestAPIError(e2.code, msg)
            body_text = e.read().decode()
            try:
                err = json.loads(body_text)
                msg = err.get("message", body_text)
            except Exception:
                msg = body_text
            raise PinterestAPIError(e.code, msg)

    # ── Boards ───────────────────────────────────────────────────────────────

    def get_boards(self) -> list[dict]:
        """Get all boards for the authenticated user."""
        result = self._request("GET", "boards", params={"page_size": 100})
        return result.get("items", [])

    def get_board_id(self, board_name: str) -> str | None:
        """Find a board ID by name (case-insensitive)."""
        boards = self.get_boards()
        name_lower = board_name.lower()
        for board in boards:
            if board.get("name", "").lower() == name_lower:
                return board["id"]
        return None

    def create_board(self, name: str, description: str = "") -> dict:
        """Create a new public board and return the created board dict."""
        body = {
            "name": name,
            "description": description,
            "privacy": "PUBLIC",
        }
        return self._request("POST", "boards", body=body)

    # ── Pins ─────────────────────────────────────────────────────────────────

    def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        image_url: str,
        link: str = "https://www.etsy.com/shop/onbrandcraftz",
    ) -> dict:
        """Create a new pin on a board."""
        body = {
            "board_id": board_id,
            "title": title[:100],
            "description": description[:500],
            "link": link,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        return self._request("POST", "pins", body=body)

    def get_pins(self, board_id: str) -> list[dict]:
        """Get all pins on a board."""
        result = self._request("GET", f"boards/{board_id}/pins", params={"page_size": 25})
        return result.get("items", [])


def is_configured() -> bool:
    return bool(os.getenv("PINTEREST_ACCESS_TOKEN", ""))


def get_client() -> PinterestClient:
    return PinterestClient()
