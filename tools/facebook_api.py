"""
Facebook Graph API v21.0 client — Page video posting, insights, token refresh.

Modeled directly on tools/instagram_api.py (same Meta Graph API base URL, same
Page-access-token auth model, same retry/error-handling shape).

Setup (one-time):
  1. Go to https://developers.facebook.com/ and create a Meta App (type: Business) —
     this can be the SAME app used for the Instagram integration (see instagram_api.py).
  2. Add the "Facebook Pages" product to the app.
  3. Connect the OnBrandCraftz Facebook Page to the app.
  4. Copy your App ID and App Secret → add to .env:
       FACEBOOK_APP_ID=your_app_id
       FACEBOOK_APP_SECRET=your_app_secret
  5. Generate a long-lived Page Access Token with these scopes:
       pages_show_list, pages_read_engagement, pages_manage_posts,
       publish_video
  6. Find your Page ID from the Page's "About" section or:
       GET https://graph.facebook.com/v21.0/me/accounts?access_token=<user_token>
  7. Add to .env:
       FACEBOOK_PAGE_ID=your_numeric_page_id
       FACEBOOK_PAGE_ACCESS_TOKEN=your_long_lived_page_token

Token notes:
  - Short-lived tokens expire in 1 hour
  - Long-lived Page tokens expire in 60 days
  - Call refresh_token() periodically (or schedule it monthly) to keep the token alive
  - refresh_token() requires a long-lived token to exchange (not a short-lived one)

Video URL requirement:
  - Facebook's Page video endpoint accepts either a publicly accessible HTTPS URL
    (file_url) or a direct multipart file upload. This client uses file_url for
    consistency with the Instagram client and because the generated video is
    already served from this app's own public URL.
  - Local file paths cannot be passed directly to post_video() — serve the file
    first (e.g. RAILWAY_APP_URL + /api/files/...) and pass that URL.
"""
from __future__ import annotations

import os
import json
import time
import urllib.parse
import requests
from typing import Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

BASE_URL = "https://graph.facebook.com/v21.0"

# Module-level session -- same fix and same rationale as instagram_api.py's
# _session (2026-07-15): rewritten from raw urllib.request, which some
# third-party APIs (Railway confirmed, see ops_runbook.md) reject over its
# default User-Agent; requests' default isn't affected. Session reuse also
# avoids a fresh TCP+TLS handshake per call, same as etsy_api.py.
_session = requests.Session()

# Video processing on Facebook's side is asynchronous for larger files —
# poll up to 60 attempts * 3s = 3 minutes before giving up.
_VIDEO_POLL_INTERVAL = 3
_VIDEO_POLL_MAX_ATTEMPTS = 60


class FacebookAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Facebook API {status}: {message}")


class FacebookAPIClient:
    """
    Meta Facebook Graph API v21.0 client (no third-party dependencies).

    post_video() requires a publicly accessible HTTPS URL — local file paths
    cannot be used directly (same constraint as InstagramAPIClient.post_video()).
    """

    def __init__(self, page_id: str = "", access_token: str = ""):
        self.page_id = page_id or os.getenv("FACEBOOK_PAGE_ID", "")
        self.access_token = access_token or os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", "")
        self.app_id = os.getenv("FACEBOOK_APP_ID", "")
        self.app_secret = os.getenv("FACEBOOK_APP_SECRET", "")

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _update_env(self, key: str, value: str) -> None:
        """Upsert a key=value line in the project .env file."""
        lines: list[str] = []
        found = False
        if os.path.exists(ENV_FILE):
            with open(ENV_FILE) as fh:
                lines = fh.readlines()
        for i, line in enumerate(lines):
            if line.startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                found = True
                break
        if not found:
            lines.append(f"{key}={value}\n")
        with open(ENV_FILE, "w") as fh:
            fh.writelines(lines)

    def _require_auth(self) -> None:
        """Raise FacebookAPIError when essential credentials are missing."""
        if not self.access_token:
            raise FacebookAPIError(
                0,
                "No Facebook Page access token configured. Add FACEBOOK_PAGE_ACCESS_TOKEN to .env.",
            )
        if not self.page_id:
            raise FacebookAPIError(
                0,
                "No Facebook Page ID configured. Add FACEBOOK_PAGE_ID to .env.",
            )

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """
        Make an authenticated request to the Facebook Graph API.

        Handles retries on 429 (rate limit) and 503 (transient server error)
        with exponential backoff. On 190/401 (expired token) raises
        FacebookAPIError so the caller can react (e.g. call refresh_token()).

        requests-based (rewritten from raw urllib.request 2026-07-15, mirrors
        instagram_api.py's identical rewrite the same day) -- requests does
        not raise on 4xx/5xx like urllib.error.HTTPError did, so status is
        checked explicitly instead of caught; retry count, backoff, and the
        429/503-retry behavior are otherwise unchanged.
        """
        self._require_auth()

        query: dict[str, Any] = {"access_token": self.access_token}
        if params:
            query.update(params)

        url = f"{BASE_URL}/{path.lstrip('/')}"
        url = f"{url}?{urllib.parse.urlencode(query)}"

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body).encode() if body else None

        def _error_message(resp: requests.Response) -> str:
            body_text = resp.text
            try:
                err = resp.json()
                error_obj = err.get("error", {})
                if isinstance(error_obj, dict):
                    return error_obj.get("message", body_text)
                return str(error_obj) or body_text
            except Exception:
                return body_text

        retryable_http = {429, 503}
        delays = [3, 6]  # seconds between attempt 1→2 and 2→3

        last_exc: Exception | None = None
        last_resp: requests.Response | None = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(delays[attempt - 1])
            try:
                resp = _session.request(method, url, data=data, headers=headers, timeout=20)
            except requests.exceptions.RequestException as e:
                last_exc = e
                continue

            if resp.status_code < 400:
                raw = resp.text
                return json.loads(raw) if raw.strip() else {}
            if resp.status_code in retryable_http:
                last_resp = resp
                continue
            raise FacebookAPIError(resp.status_code, _error_message(resp))

        if last_resp is not None:
            raise FacebookAPIError(last_resp.status_code, _error_message(last_resp))
        raise FacebookAPIError(0, f"Network error after retries: {last_exc}")

    def _wait_for_video(self, video_id: str) -> None:
        """
        Poll a Page video's processing status until it finishes.

        Facebook processes uploaded videos asynchronously. Polling typically
        resolves within tens of seconds, but can take longer for larger files.

        Raises FacebookAPIError if processing errors out or the poll timeout
        is exceeded.
        """
        for _ in range(_VIDEO_POLL_MAX_ATTEMPTS):
            result = self._request(
                "GET",
                video_id,
                params={"fields": "status"},
            )
            status = result.get("status", {})
            video_status = status.get("video_status", "") if isinstance(status, dict) else ""
            if video_status == "ready":
                return
            if video_status == "error":
                raise FacebookAPIError(0, f"Page video processing failed: {status}")
            # processing / uploading — keep polling
            time.sleep(_VIDEO_POLL_INTERVAL)

        raise FacebookAPIError(
            0,
            f"Page video {video_id} did not finish processing within "
            f"{_VIDEO_POLL_MAX_ATTEMPTS * _VIDEO_POLL_INTERVAL}s.",
        )

    # ── Public API methods ────────────────────────────────────────────────────

    def post_video(self, video_url: str, description: str = "", title: str = "") -> dict:
        """
        Publish a video to the connected Facebook Page.

        This is a 1-step process (unlike Instagram's 2-step container flow) —
        Facebook's Page /videos endpoint accepts the source URL and description
        directly and returns a video ID immediately; the video then processes
        asynchronously, which _wait_for_video() polls for.

        Args:
            video_url: Must be a publicly accessible HTTPS URL pointing to an
                MP4 file. Facebook's servers fetch this directly — a local
                file path will fail. Serve the generated video from this
                app's own public URL (e.g. RAILWAY_APP_URL + /api/files/...).
            description: Post caption/description text.
            title: Optional video title.

        Returns:
            Dict with 'id' key containing the published video ID.

        Raises:
            FacebookAPIError: On API error, processing failure, or if
                credentials are not configured.
        """
        body: dict[str, Any] = {"file_url": video_url}
        if description:
            body["description"] = description
        if title:
            body["title"] = title

        result = self._request("POST", f"{self.page_id}/videos", body=body)
        video_id = result.get("id", "")
        if not video_id:
            raise FacebookAPIError(0, f"Page video creation returned no ID. Response: {result}")
        self._wait_for_video(video_id)
        return result

    def get_insights(self, metric: str, period: str = "day") -> dict:
        """
        Fetch Page-level insights from the Facebook Graph API.

        Args:
            metric: One or more comma-separated Page insight metric names,
                e.g. "page_impressions,page_engaged_users".
            period: Time period for the metric. One of:
                'day', 'week', 'days_28', 'lifetime'.

        Returns:
            Raw Graph API response dict containing a 'data' list of metric
            objects.

        Raises:
            FacebookAPIError: On API error or missing credentials.
        """
        return self._request(
            "GET",
            f"{self.page_id}/insights",
            params={"metric": metric, "period": period},
        )

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        """
        Fetch the most recent posts from the connected Facebook Page.

        Args:
            limit: Number of posts to return. Max 100. Defaults to 10.

        Returns:
            List of post dicts, ordered newest-first.

        Raises:
            FacebookAPIError: On API error or missing credentials.
        """
        fields = "id,message,created_time,permalink_url"
        result = self._request(
            "GET",
            f"{self.page_id}/posts",
            params={"fields": fields, "limit": min(limit, 100)},
        )
        return result.get("data", [])

    def refresh_token(self) -> bool:
        """
        Exchange the current long-lived Page access token for a fresh one.

        Meta long-lived tokens expire in 60 days. This method calls the
        token refresh endpoint to obtain a new long-lived token and
        automatically persists it to the .env file under
        FACEBOOK_PAGE_ACCESS_TOKEN.

        This method requires:
          - FACEBOOK_APP_SECRET set in .env
          - The current access_token to still be valid (not yet expired)

        Returns:
            True on success.

        Raises:
            FacebookAPIError: If FACEBOOK_APP_SECRET is missing or the
                refresh request fails.
        """
        if not self.app_secret:
            raise FacebookAPIError(0, "FACEBOOK_APP_SECRET not set in .env — cannot refresh token.")
        if not self.app_id:
            raise FacebookAPIError(0, "FACEBOOK_APP_ID not set in .env — cannot refresh token.")

        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": self.access_token,
        }
        url = f"{BASE_URL}/oauth/access_token?{urllib.parse.urlencode(params)}"
        # Deliberately narrower error handling than _request() above: only an
        # HTTP-status error is turned into FacebookAPIError (matching the
        # pre-2026-07-15 urllib version, which only caught HTTPError, not
        # OSError/URLError) -- a network-level failure (DNS, connection
        # refused, timeout) propagates uncaught here, same as before. Also
        # deliberately does NOT parse the nested {"error": {...}} object the
        # way _request()'s _error_message() does -- raises the raw body text,
        # preserving this function's pre-existing (not "fixed") inconsistency.
        resp = _session.get(url, timeout=20)
        if resp.status_code >= 400:
            raise FacebookAPIError(resp.status_code, resp.text)
        result = resp.json()

        new_token = result.get("access_token", "")
        if not new_token:
            raise FacebookAPIError(0, f"Token refresh returned no token. Response: {result}")

        self.access_token = new_token
        self._update_env("FACEBOOK_PAGE_ACCESS_TOKEN", new_token)
        return True


# ── Module-level helpers ──────────────────────────────────────────────────────


def is_configured() -> bool:
    """Return True if FACEBOOK_PAGE_ACCESS_TOKEN is set in the environment."""
    return bool(os.getenv("FACEBOOK_PAGE_ACCESS_TOKEN", ""))


def get_client() -> FacebookAPIClient:
    """Return a ready-to-use FacebookAPIClient using credentials from .env."""
    return FacebookAPIClient()
