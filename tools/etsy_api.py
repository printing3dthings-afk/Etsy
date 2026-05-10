"""
Etsy Open API v3 client.

Public endpoints (API key only): search_listings, get_listing, get_shop, get_shop_listings
OAuth-protected: get_orders, get_messages, create_listing, update_listing

Setup:
  1. https://www.etsy.com/developers/ -> Create App -> copy Keystring
  2. ETSY_API_KEY=<key> in .env
  3. For OAuth: ETSY_CLIENT_ID + ETSY_CLIENT_SECRET in .env, then run tools/etsy_oauth.py
"""

import os
import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

BASE_URL = "https://openapi.etsy.com/v3/application"


class EtsyAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Etsy API {status}: {message}")


class EtsyAPIClient:
    def __init__(self, api_key: str = "", access_token: str = ""):
        self.api_key = api_key or os.getenv("ETSY_API_KEY", "")
        self.access_token = access_token or os.getenv("ETSY_ACCESS_TOKEN", "")
        self.shop_id = os.getenv("ETSY_SHOP_ID", "")

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers["x-api-key"] = self.api_key
        else:
            raise EtsyAPIError(0, "No API key or access token. Add ETSY_API_KEY to .env.")
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            try:
                msg = json.loads(body_text).get("error", body_text)
            except Exception:
                msg = body_text
            raise EtsyAPIError(e.code, msg)

    def search_listings(self, keywords: str, limit: int = 10, sort_on: str = "score",
                        min_price: float | None = None, max_price: float | None = None) -> dict:
        params: dict[str, Any] = {"keywords": keywords, "limit": min(limit, 100), "sort_on": sort_on}
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        return self._request("GET", "listings/active", params=params)

    def get_listing(self, listing_id: int | str) -> dict:
        return self._request("GET", f"listings/{listing_id}")

    def get_shop(self, shop_id_or_name: str = "") -> dict:
        target = shop_id_or_name or self.shop_id or "onbrandcraftz"
        return self._request("GET", f"shops/{target}")

    def get_shop_listings(self, shop_id: str = "", limit: int = 25, state: str = "active") -> dict:
        target = shop_id or self.shop_id
        if not target:
            raise EtsyAPIError(0, "No shop ID. Add ETSY_SHOP_ID to .env.")
        return self._request("GET", f"shops/{target}/listings/{state}", params={"limit": limit})

    def get_orders(self, limit: int = 25) -> dict:
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/receipts", params={"limit": limit, "was_paid": True})

    def get_messages(self, limit: int = 25) -> dict:
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/conversations", params={"limit": limit})

    def create_listing(self, listing_data: dict) -> dict:
        self._require_oauth()
        return self._request("POST", f"shops/{self.shop_id}/listings", body=listing_data)

    def update_listing(self, listing_id: int | str, updates: dict) -> dict:
        self._require_oauth()
        return self._request("PATCH", f"shops/{self.shop_id}/listings/{listing_id}", body=updates)

    def _require_oauth(self) -> None:
        if not self.access_token:
            raise EtsyAPIError(401, "OAuth required. Run 'python tools/etsy_oauth.py' to authenticate.")


def is_configured() -> bool:
    return bool(os.getenv("ETSY_API_KEY", ""))


def get_client() -> EtsyAPIClient:
    return EtsyAPIClient()
