"""
Canva Connect API client — programmatic listing-graphic generation.

Replaces the manual "added in Canva post" step that CLAUDE.md calls for on
photo slots 2, 6, 7, 9, 10 (text-overlay graphics: what's-included callouts,
how-to steps, app compatibility labels, etc.) with an automated pipeline:

  1. upload_asset()            — push a gpt-image-1 background PNG to Canva
  2. create_autofill_job()     — fill a Brand Template's placeholder fields
                                  (text and/or the uploaded image) to produce
                                  a new design
  3. create_export_job()       — export that design as a flattened PNG
  4. download_export()         — pull the rendered PNG back to disk

IMPORTANT — Canva's Connect API has no generic "draw text on an arbitrary
image" endpoint. Content can only be injected via Autofill against a Brand
Template that a human creates in the Canva UI with named placeholder fields.
Scott must create at least one Brand Template manually before this pipeline
is usable. Use list_brand_templates() + get_brand_template_dataset() to
discover what placeholder keys exist on a given template.

Setup: run tools/canva_oauth.py (see that file's docstring for the full flow).
"""
from __future__ import annotations

import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
BASE_URL = "https://api.canva.com/rest/v1"
TOKEN_URL = "https://www.canva.com/api/oauth/token"


class CanvaAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Canva API {status}: {message}")


class CanvaAPIClient:
    """Canva Connect API v1 client."""

    def __init__(self, access_token: str = ""):
        self.access_token = access_token or os.getenv("CANVA_ACCESS_TOKEN", "")

    # ── env persistence ──────────────────────────────────────────────────

    def _update_env(self, key: str, value: str) -> None:
        lines: list[str] = []
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

    # ── auth ─────────────────────────────────────────────────────────────

    def refresh_access_token(self) -> bool:
        """Refresh the access token using the stored refresh token.

        Canva uses HTTP Basic auth (client_id:client_secret) for the token
        endpoint — unlike Etsy, which puts client_id in the body.
        """
        client_id     = os.getenv("CANVA_CLIENT_ID", "")
        client_secret = os.getenv("CANVA_CLIENT_SECRET", "")
        refresh_token = os.getenv("CANVA_REFRESH_TOKEN", "")

        if not client_id or not client_secret or not refresh_token:
            return False

        credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        token_data = urllib.parse.urlencode({
            "grant_type":    "refresh_token",
            "refresh_token": refresh_token,
        }).encode()

        req = urllib.request.Request(
            TOKEN_URL,
            data=token_data,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type":  "application/x-www-form-urlencoded",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                tokens = json.loads(resp.read().decode())
        except Exception:
            return False

        new_access  = tokens.get("access_token", "")
        new_refresh = tokens.get("refresh_token", "")
        if not new_access:
            return False

        self.access_token = new_access
        self._update_env("CANVA_ACCESS_TOKEN", new_access)
        if new_refresh:
            self._update_env("CANVA_REFRESH_TOKEN", new_refresh)
        return True

    # ── low-level request helpers ───────────────────────────────────────

    def _require_token(self) -> None:
        if not self.access_token:
            raise CanvaAPIError(
                0,
                "No Canva access token. Run 'python tools/canva_oauth.py' to connect Canva.",
            )

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
        raw_body: bytes | None = None,
        extra_headers: dict | None = None,
    ) -> dict:
        self._require_token()
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        headers = {"Authorization": f"Bearer {self.access_token}"}
        if extra_headers:
            headers.update(extra_headers)

        if raw_body is not None:
            data = raw_body
        elif body is not None:
            data = json.dumps(body).encode()
            headers["Content-Type"] = "application/json"
        else:
            data = None

        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as e:
            if e.code == 401 and self.refresh_access_token():
                headers["Authorization"] = f"Bearer {self.access_token}"
                req2 = urllib.request.Request(url, data=data, headers=headers, method=method)
                try:
                    with urllib.request.urlopen(req2, timeout=30) as resp:
                        raw = resp.read().decode()
                        return json.loads(raw) if raw else {}
                except urllib.error.HTTPError as e2:
                    raise CanvaAPIError(e2.code, e2.read().decode())
            raise CanvaAPIError(e.code, e.read().decode())

    def _poll(self, path: str, job_key: str = "job", interval: float = 2.0, timeout: float = 90.0) -> dict:
        """Poll an async job endpoint until status leaves 'in_progress'."""
        start = time.monotonic()
        while True:
            result = self._request("GET", path)
            job = result.get(job_key, result)
            status = job.get("status")
            if status != "in_progress":
                return result
            if time.monotonic() - start > timeout:
                raise CanvaAPIError(0, f"Timed out polling {path} after {timeout}s (last status: {status})")
            time.sleep(interval)

    # ── assets ───────────────────────────────────────────────────────────

    def upload_asset(self, file_path: str, name: str = "") -> dict:
        """Upload a local image file as a Canva asset. Returns the completed job dict.

        Rate limit: 30/min/user.
        """
        if not os.path.exists(file_path):
            raise CanvaAPIError(0, f"File not found: {file_path}")

        asset_name = name or os.path.splitext(os.path.basename(file_path))[0]
        name_b64 = base64.b64encode(asset_name[:50].encode()).decode()

        with open(file_path, "rb") as f:
            raw = f.read()

        result = self._request(
            "POST",
            "asset-uploads",
            raw_body=raw,
            extra_headers={
                "Content-Type": "application/octet-stream",
                "Asset-Upload-Metadata": json.dumps({"name_base64": name_b64}),
            },
        )
        job = result.get("job", result)
        if job.get("status") == "in_progress":
            result = self._poll(f"asset-uploads/{job['id']}")
        return result

    # ── brand templates ─────────────────────────────────────────────────

    def list_brand_templates(self) -> list[dict]:
        """List all Brand Templates Scott has created in the Canva UI."""
        result = self._request("GET", "brand-templates")
        return result.get("items", [])

    def get_brand_template_dataset(self, brand_template_id: str) -> dict:
        """Return the fillable placeholder fields for a Brand Template, e.g.
        {"callout_1": {"type": "text"}, "photo": {"type": "image"}}
        """
        result = self._request("GET", f"brand-templates/{brand_template_id}/dataset")
        return result.get("dataset", {})

    # ── autofill ─────────────────────────────────────────────────────────

    def create_autofill_job(self, brand_template_id: str, data: dict[str, dict], title: str = "") -> dict:
        """Autofill a Brand Template's placeholders to produce a new design.

        `data` maps placeholder key -> {"type": "text", "text": "..."} or
        {"type": "image", "asset_id": "..."}. Use get_brand_template_dataset()
        first to know what keys/types a template expects.

        Rate limit: 60/min/user.
        """
        body: dict[str, Any] = {
            "brand_template_id": brand_template_id,
            "data": data,
        }
        if title:
            body["title"] = title
        body["type"] = "create_from_brand_template"

        result = self._request("POST", "autofills", body=body)
        job = result.get("job", result)
        if job.get("status") == "in_progress":
            result = self._poll(f"autofills/{job['id']}")
        return result

    # ── designs (generic, non-template) ─────────────────────────────────

    def create_design(self, design_type_name: str = "doc", width: int | None = None,
                       height: int | None = None, title: str = "") -> dict:
        """Create a blank design. Mostly useful as a container; for listing
        graphics prefer create_autofill_job against a Brand Template."""
        if width and height:
            design_type = {"type": "custom", "width": width, "height": height}
        else:
            design_type = {"type": "preset", "name": design_type_name}
        body: dict[str, Any] = {"design_type": design_type}
        if title:
            body["title"] = title
        return self._request("POST", "designs", body=body)

    # ── export ───────────────────────────────────────────────────────────

    def create_export_job(self, design_id: str, fmt: str = "png", width: int = 2400,
                           height: int = 2400, transparent_background: bool = False) -> dict:
        """Export a design as a flattened image. Returns the completed job dict
        with job.urls (valid 24h) on success.
        """
        format_spec: dict[str, Any] = {"type": fmt}
        if fmt == "png":
            format_spec.update({
                "width": width,
                "height": height,
                "export_quality": "pro",
                "lossless": True,
                "transparent_background": transparent_background,
                "as_single_image": True,
            })
        body = {"design_id": design_id, "format": format_spec}
        result = self._request("POST", "exports", body=body)
        job = result.get("job", result)
        if job.get("status") == "in_progress":
            result = self._poll(f"exports/{job['id']}")
        return result

    def download_export(self, export_job_result: dict, output_path: str) -> str:
        """Download the first URL from a completed export job to output_path."""
        job = export_job_result.get("job", export_job_result)
        urls = job.get("urls") or []
        if not urls:
            raise CanvaAPIError(0, f"Export job has no URLs (status={job.get('status')}, error={job.get('error')})")
        urllib.request.urlretrieve(urls[0], output_path)
        return output_path


def is_configured() -> bool:
    return bool(os.getenv("CANVA_ACCESS_TOKEN", ""))


def get_client() -> CanvaAPIClient:
    return CanvaAPIClient()
