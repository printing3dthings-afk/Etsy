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

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

BASE_URL = "https://api.pinterest.com/v5"


class PinterestAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Pinterest API {status}: {message}")


class PinterestClient:
    """Pinterest API v5 client."""

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN", "")

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
