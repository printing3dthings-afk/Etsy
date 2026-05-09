"""
Etsy Open API v3 client.

Public endpoints (read-only, API key only):
  - search_listings()      — competitor/market research
  - get_listing()          — single listing details
  - get_shop()             — shop info
  - get_shop_listings()    — your shop's listings

OAuth-protected endpoints (requires full OAuth flow):
  - get_orders()
  - get_messages()
  - create_listing()
  - update_listing()

To get an API key:
  1. Go to https://www.etsy.com/developers/
  2. Sign in with your Etsy account
  3. Create an app → copy the Keystring (API key)
  4. Add ETSY_API_KEY=<key> to your .env file

For OAuth (order management, listing edits):
  5. Set ETSY_CLIENT_ID and ETSY_CLIENT_SECRET in .env
  6. Run tools/etsy_oauth.py to complete the OAuth flow
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
    """Lightweight Etsy Open API v3 client (no third-party dependencies)."""

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
            raise EtsyAPIError(0, "No API key or access token configured. Add ETSY_API_KEY to your .env file.")

        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            try:
                err = json.loads(body_text)
                msg = err.get("error", body_text)
            except Exception:
                msg = body_text
            raise EtsyAPIError(e.code, msg)

    # ── Public endpoints (API key only) ──────────────────────────────────────

    def search_listings(
        self,
        keywords: str,
        limit: int = 10,
        sort_on: str = "score",
        min_price: float | None = None,
        max_price: float | None = None,
    ) -> dict:
        """Search active Etsy listings. Great for competitor research."""
        params: dict[str, Any] = {
            "keywords": keywords,
            "limit": min(limit, 100),
            "sort_on": sort_on,
        }
        if min_price is not None:
            params["min_price"] = min_price
        if max_price is not None:
            params["max_price"] = max_price
        return self._request("GET", "listings/active", params=params)

    def get_listing(self, listing_id: int | str) -> dict:
        """Get details for a single listing."""
        return self._request("GET", f"listings/{listing_id}")

    def get_shop(self, shop_id_or_name: str = "") -> dict:
        """Get shop information by shop ID or name."""
        target = shop_id_or_name or self.shop_id or "onbrandcraftz"
        return self._request("GET", f"shops/{target}")

    def get_shop_listings(self, shop_id: str = "", limit: int = 25, state: str = "active") -> dict:
        """Get listings for a shop."""
        target = shop_id or self.shop_id
        if not target:
            raise EtsyAPIError(0, "No shop ID configured. Add ETSY_SHOP_ID to .env or pass shop_id.")
        return self._request("GET", f"shops/{target}/listings/{state}", params={"limit": limit})

    # ── OAuth-protected endpoints ─────────────────────────────────────────────

    def get_orders(self, limit: int = 25, status: str = "open") -> dict:
        """Get shop orders. Requires OAuth access token."""
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/receipts", params={"limit": limit, "was_paid": True})

    def get_messages(self, limit: int = 25) -> dict:
        """Get shop conversations/messages. Requires OAuth access token."""
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/conversations", params={"limit": limit})

    def create_listing(self, listing_data: dict) -> dict:
        """Create a new listing. Requires OAuth access token."""
        self._require_oauth()
        return self._request("POST", f"shops/{self.shop_id}/listings", body=listing_data)

    def update_listing(self, listing_id: int | str, updates: dict) -> dict:
        """Update an existing listing. Requires OAuth access token."""
        self._require_oauth()
        return self._request("PATCH", f"shops/{self.shop_id}/listings/{listing_id}", body=updates)

    def update_listing_inventory(self, listing_id: int | str, quantity: int) -> dict:
        """Update listing quantity. Requires OAuth access token."""
        self._require_oauth()
        return self._request(
            "PUT",
            f"shops/{self.shop_id}/listings/{listing_id}/inventory",
            body={"products": [{"offerings": [{"quantity": quantity, "is_enabled": True}]}]},
        )

    def _require_oauth(self) -> None:
        if not self.access_token:
            raise EtsyAPIError(
                401,
                "This action requires OAuth. Run 'python tools/etsy_oauth.py' to authenticate your Etsy account.",
            )


def is_configured() -> bool:
    """Return True if at least an API key is present."""
    return bool(os.getenv("ETSY_API_KEY", ""))


def get_client() -> EtsyAPIClient:
    return EtsyAPIClient()
