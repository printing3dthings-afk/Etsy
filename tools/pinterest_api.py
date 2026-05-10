"""
Pinterest API v5 client — direct pin posting and board management.

Setup:
  1. https://developers.pinterest.com/ -> New App
  2. Copy App ID and App Secret to .env
  3. Run: python tools/pinterest_oauth.py
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "https://api.pinterest.com/v5"


class PinterestAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Pinterest API {status}: {message}")


class PinterestClient:
    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.getenv("PINTEREST_ACCESS_TOKEN", "")

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        if not self.access_token:
            raise PinterestAPIError(0, "No Pinterest access token. Run 'python tools/pinterest_oauth.py'.")
        headers = {"Authorization": f"Bearer {self.access_token}", "Content-Type": "application/json"}
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            try:
                msg = json.loads(body_text).get("message", body_text)
            except Exception:
                msg = body_text
            raise PinterestAPIError(e.code, msg)

    def get_boards(self) -> list[dict]:
        return self._request("GET", "boards", params={"page_size": 100}).get("items", [])

    def get_board_id(self, board_name: str) -> str | None:
        name_lower = board_name.lower()
        return next((b["id"] for b in self.get_boards() if b.get("name", "").lower() == name_lower), None)

    def create_pin(self, board_id: str, title: str, description: str,
                   image_url: str, link: str = "https://www.etsy.com/shop/onbrandcraftz") -> dict:
        return self._request("POST", "pins", body={
            "board_id": board_id,
            "title": title[:100],
            "description": description[:500],
            "link": link,
            "media_source": {"source_type": "image_url", "url": image_url},
        })

    def get_pins(self, board_id: str) -> list[dict]:
        return self._request("GET", f"boards/{board_id}/pins", params={"page_size": 25}).get("items", [])


def is_configured() -> bool:
    return bool(os.getenv("PINTEREST_ACCESS_TOKEN", ""))


def get_client() -> PinterestClient:
    return PinterestClient()
