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
from __future__ import annotations

import os
import json
import time
import random
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
        self.client_id = os.getenv("ETSY_CLIENT_ID", self.api_key)
        self.client_secret = os.getenv("ETSY_CLIENT_SECRET", "")
        self.access_token = access_token or os.getenv("ETSY_ACCESS_TOKEN", "")
        self.shop_id = os.getenv("ETSY_SHOP_ID_NUMERIC") or os.getenv("ETSY_SHOP_ID", "")

    def _build_request(self, method: str, url: str, body: dict | None) -> urllib.request.Request:
        headers = {"Content-Type": "application/json"}
        if not self.api_key and not self.access_token:
            raise EtsyAPIError(0, "No API key or access token configured. Add ETSY_API_KEY to your .env file.")
        # Etsy v3 requires x-api-key as "{client_id}:{client_secret}" for authenticated calls
        if self.access_token and self.client_secret:
            headers["x-api-key"] = f"{self.client_id}:{self.client_secret}"
        elif self.api_key:
            headers["x-api-key"] = self.api_key
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        data = json.dumps(body).encode() if body else None
        return urllib.request.Request(url, data=data, headers=headers, method=method)

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        retryable_http = {429, 503}
        base_delays = [2, 4]  # exponential backoff base: 2s then 4s

        def _jittered(base: float) -> float:
            return base * (0.75 + random.random() * 0.5)  # ±25% jitter

        last_exc: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(_jittered(base_delays[attempt - 1]))
            try:
                req = self._build_request(method, url, body)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw = resp.read().decode()
                    return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as e:
                if e.code == 401 and self.access_token and self.refresh_access_token():
                    # Token refreshed — retry once immediately (not counted as a backoff attempt)
                    try:
                        req = self._build_request(method, url, body)
                        with urllib.request.urlopen(req, timeout=15) as resp:
                            return json.loads(resp.read().decode())
                    except urllib.error.HTTPError as e2:
                        body_text = e2.read().decode()
                        try:
                            err = json.loads(body_text)
                            msg = err.get("error", body_text)
                        except Exception:
                            msg = body_text
                        raise EtsyAPIError(e2.code, msg)
                if e.code in retryable_http:
                    # Honour the server's retry-after header when present
                    retry_after = e.headers.get("retry-after") or e.headers.get("Retry-After")
                    if retry_after:
                        try:
                            time.sleep(float(retry_after) * (0.75 + random.random() * 0.5))
                        except ValueError:
                            pass
                    last_exc = e
                    continue  # retry with backoff
                # Non-retryable HTTP error (including 4xx auth errors other than 401)
                body_text = e.read().decode()
                try:
                    err = json.loads(body_text)
                    msg = err.get("error", body_text)
                except Exception:
                    msg = body_text
                raise EtsyAPIError(e.code, msg)
            except (OSError, urllib.error.URLError) as e:
                last_exc = e
                continue  # retry on network errors

        # All attempts exhausted
        if isinstance(last_exc, urllib.error.HTTPError):
            body_text = last_exc.read().decode()
            try:
                err = json.loads(body_text)
                msg = err.get("error", body_text)
            except Exception:
                msg = body_text
            raise EtsyAPIError(last_exc.code, msg)
        raise EtsyAPIError(0, f"Network error after retries: {last_exc}")

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
        target = shop_id_or_name or self.shop_id
        if not target:
            raise EtsyAPIError(0, "No shop ID configured. Add ETSY_SHOP_ID to .env or pass shop_id.")
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
        params: dict = {"limit": limit, "was_paid": True}
        if status != "open":
            params["status"] = status
        return self._request("GET", f"shops/{self.shop_id}/receipts", params=params)

    def get_messages(self, limit: int = 25) -> dict:
        """Get shop conversations/messages. Requires OAuth access token."""
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/conversations", params={"limit": limit})

    def create_listing(self, listing_data: dict) -> dict:
        """Create a new listing. Requires OAuth access token.

        Automatically enforces required Etsy fields and injects AI disclosure
        (mandatory since June 10, 2025 for AI-assisted listings).
        """
        self._require_oauth()
        data = dict(listing_data)
        # Required production fields — missing these causes Etsy moderation flags
        data.setdefault("who_made", "i_did")
        data.setdefault("when_made", "made_to_order")
        data.setdefault("is_supply", False)
        # AI disclosure — required for all listings using AI-generated imagery or copy
        desc = data.get("description", "")
        _DISCLOSURE = (
            "\n\n---\n"
            "This product was created with AI assistance (DALL-E image generation "
            "for cover/lifestyle artwork). All content has been reviewed and finalized "
            "by the seller."
        )
        if desc and "AI assistance" not in desc:
            data["description"] = desc + _DISCLOSURE
        return self._request("POST", f"shops/{self.shop_id}/listings", body=data)

    @staticmethod
    def pre_publish_gate(listing_data: dict) -> list[str]:
        """Run quality gate checks before publishing. Returns list of failure reasons (empty = pass).

        Call this before create_listing() and abort if any failures are returned.
        Enforces OnBrandCraftz quality standards per business_standards.md.
        """
        failures = []
        title = listing_data.get("title", "")
        desc = listing_data.get("description", "")
        tags = listing_data.get("tags", [])
        price = listing_data.get("price", 0)

        # Title checks
        if not title:
            failures.append("Missing title")
        elif len(title) > 70:
            failures.append(
                f"Title too long: {len(title)}/70 chars — "
                f"Etsy 2026 algorithm penalizes titles >70 chars on mobile (70%+ of traffic)"
            )
        elif len(title) < 40:
            failures.append("Title too short — lead keyword must be at least 40 chars")

        # Keyword checks in title
        if title and "instant download" not in title.lower():
            failures.append("Title missing 'Instant Download'")

        # Tags
        if len(tags) < 13:
            failures.append(f"Only {len(tags)}/13 tags — fill all 13 slots")
        for tag in tags:
            if len(tag) > 20:
                failures.append(f"Tag too long (>{len(tag)} chars): '{tag}'")

        # Description
        if not desc:
            failures.append("Missing description")
        elif len(desc) < 300:
            failures.append("Description too short — expand with what's included, apps, FAQ")

        # Price floor enforcement (price may be float dollars or int cents)
        price_val = float(price) if isinstance(price, (int, float)) else 0.0
        price_usd = price_val / 100 if price_val > 100 else price_val
        if price_usd and price_usd < 7.99:
            failures.append(f"Price ${price_usd:.2f} is below minimum floor $7.99")

        # Required Etsy production fields
        if listing_data.get("who_made", "i_did") not in ("i_did", "collective", "someone_else"):
            failures.append("Invalid who_made value")
        if listing_data.get("is_supply") is True:
            failures.append("is_supply should be False for finished products")

        return failures

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

    # ── Shop sections ─────────────────────────────────────────────────────────

    def get_shop_sections(self) -> list[dict]:
        """Get all shop sections. Returns list with id, title, rank, active_listing_count."""
        self._require_oauth()
        result = self._request("GET", f"shops/{self.shop_id}/sections")
        return result.get("results", [])

    def create_shop_section(self, title: str) -> dict:
        """Create a new shop section. Returns the created section dict including id."""
        self._require_oauth()
        return self._request("POST", f"shops/{self.shop_id}/sections", body={"title": title})

    def get_or_create_section(self, title: str) -> int:
        """Get existing section ID by title, or create it. Returns section ID (int)."""
        sections = self.get_shop_sections()
        for s in sections:
            if s.get("title", "").lower() == title.lower():
                return int(s["shop_section_id"])
        created = self.create_shop_section(title)
        return int(created["shop_section_id"])

    # ── Listing images ────────────────────────────────────────────────────────

    def upload_listing_image(self, listing_id: int | str, image_path: str, rank: int = 1) -> dict:
        """Upload an image file to a listing. rank=1 is the cover photo."""
        self._require_oauth()
        import mimetypes
        import email.mime.multipart
        import email.mime.base
        import email.generator
        import io

        with open(image_path, "rb") as f:
            image_data = f.read()

        mime_type = mimetypes.guess_type(image_path)[0] or "image/png"
        filename = os.path.basename(image_path)

        # Build multipart form body manually (no requests library)
        boundary = "----FormBoundary" + os.urandom(8).hex()
        body_parts = []
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="rank"\r\n\r\n{rank}'.encode())
        body_parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode()
            + image_data
        )
        body_parts.append(f'--{boundary}--'.encode())
        body = b'\r\n'.join(body_parts)

        url = f"{BASE_URL}/shops/{self.shop_id}/listings/{listing_id}/images"
        api_key_header = f"{self.client_id}:{self.client_secret}" if self.client_secret else self.api_key
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {self.access_token}",
            "x-api-key": api_key_header,
        }
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            try:
                err = json.loads(body_text)
                msg = err.get("error", body_text)
            except Exception:
                msg = body_text
            raise EtsyAPIError(e.code, msg)

    def get_listing_images(self, listing_id: int | str) -> list[dict]:
        """Get all images for a listing. Returns list of image records with listing_image_id."""
        result = self._request("GET", f"listings/{listing_id}/images")
        return result.get("results", [])

    def delete_listing_image(self, listing_id: int | str, listing_image_id: int | str) -> None:
        """Delete a specific image from a listing. Requires OAuth access token."""
        self._require_oauth()
        self._request("DELETE", f"shops/{self.shop_id}/listings/{listing_id}/images/{listing_image_id}")

    # ── Digital file upload ───────────────────────────────────────────────────

    def upload_listing_file(self, listing_id: int | str, file_path: str, rank: int = 1) -> dict:
        """Attach a digital file to a listing for instant Etsy download."""
        self._require_oauth()
        filename = os.path.basename(file_path)
        with open(file_path, "rb") as f:
            file_data = f.read()

        boundary = "----FormBoundary" + os.urandom(8).hex()
        body_parts = []
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="rank"\r\n\r\n{rank}'.encode())
        body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="name"\r\n\r\n{filename}'.encode())
        body_parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()
            + file_data
        )
        body_parts.append(f'--{boundary}--'.encode())
        body = b'\r\n'.join(body_parts)

        url = f"{BASE_URL}/shops/{self.shop_id}/listings/{listing_id}/files"
        api_key_header = f"{self.client_id}:{self.client_secret}" if self.client_secret else self.api_key
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {self.access_token}",
            "x-api-key": api_key_header,
        }
        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body_text = e.read().decode()
            try:
                err = json.loads(body_text)
                msg = err.get("error", body_text)
            except Exception:
                msg = body_text
            raise EtsyAPIError(e.code, msg)

    def refresh_access_token(self) -> bool:
        """Exchange ETSY_REFRESH_TOKEN for a new access token and persist it to .env.

        Returns True on success, False on any failure.
        """
        client_id = os.getenv("ETSY_CLIENT_ID", "")
        refresh_token = os.getenv("ETSY_REFRESH_TOKEN", "")
        if not client_id or not refresh_token:
            return False

        payload = urllib.parse.urlencode({
            "grant_type": "refresh_token",
            "client_id": client_id,
            "refresh_token": refresh_token,
        }).encode()
        req = urllib.request.Request(
            "https://api.etsy.com/v3/public/oauth/token",
            data=payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return False

        new_access = data.get("access_token", "")
        new_refresh = data.get("refresh_token", refresh_token)
        if not new_access:
            return False

        # Update in-memory token
        self.access_token = new_access

        # Persist to .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        try:
            if os.path.exists(env_path):
                with open(env_path, "r") as fh:
                    lines = fh.readlines()
            else:
                lines = []

            updated = {"ETSY_ACCESS_TOKEN": False, "ETSY_REFRESH_TOKEN": False}
            new_lines = []
            for line in lines:
                if line.startswith("ETSY_ACCESS_TOKEN="):
                    new_lines.append(f"ETSY_ACCESS_TOKEN={new_access}\n")
                    updated["ETSY_ACCESS_TOKEN"] = True
                elif line.startswith("ETSY_REFRESH_TOKEN="):
                    new_lines.append(f"ETSY_REFRESH_TOKEN={new_refresh}\n")
                    updated["ETSY_REFRESH_TOKEN"] = True
                else:
                    new_lines.append(line)

            # Append keys that were not already present
            if not updated["ETSY_ACCESS_TOKEN"]:
                new_lines.append(f"ETSY_ACCESS_TOKEN={new_access}\n")
            if not updated["ETSY_REFRESH_TOKEN"]:
                new_lines.append(f"ETSY_REFRESH_TOKEN={new_refresh}\n")

            with open(env_path, "w") as fh:
                fh.writelines(new_lines)
        except Exception:
            # Token is still updated in memory even if file write fails
            pass

        return True

    def sync_orders_from_etsy(self) -> list[dict]:
        """Fetch orders via OAuth and return a normalised list of order dicts.

        Each dict contains: order_id, buyer_name, buyer_email, total_price,
        items, created_date.

        Returns an empty list when OAuth is not configured or the request fails.
        """
        try:
            raw = self.get_orders()
        except EtsyAPIError:
            return []

        receipts = raw.get("results", [])
        orders = []
        for r in receipts:
            # Buyer name: prefer name field, fall back to first+last
            buyer_name = r.get("name") or (
                f"{r.get('first_line', '')} {r.get('last_line', '')}".strip()
            )
            # Items: list of transaction summaries
            items = [
                {
                    "listing_id": t.get("listing_id"),
                    "title": t.get("title", ""),
                    "quantity": t.get("quantity", 1),
                    "price": t.get("price", {}).get("amount", 0) / max(t.get("price", {}).get("divisor", 100), 1)
                    if isinstance(t.get("price"), dict)
                    else t.get("price", 0),
                }
                for t in r.get("transactions", [])
            ]
            total_raw = r.get("grandtotal") or r.get("total_price") or {}
            if isinstance(total_raw, dict):
                total_price = total_raw.get("amount", 0) / max(total_raw.get("divisor", 100), 1)
            else:
                total_price = float(total_raw or 0)

            orders.append({
                "order_id": r.get("receipt_id"),
                "buyer_name": buyer_name,
                "buyer_email": r.get("buyer_email", ""),
                "total_price": round(total_price, 2),
                "items": items,
                "created_date": r.get("create_timestamp") or r.get("created_timestamp", ""),
            })
        return orders

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
