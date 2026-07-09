"""
Instagram Graph API v21.0 client — photo posting, carousels, insights, token refresh.

Instagram handle: onbrandcraftz2026

Setup (one-time):
  1. Go to https://developers.facebook.com/ and create a Meta App (type: Business)
  2. Add the "Instagram Graph API" product to the app
  3. Connect your Instagram Professional account (Creator or Business) via Facebook Page
  4. Copy your App ID and App Secret → add to .env:
       INSTAGRAM_APP_ID=your_app_id
       INSTAGRAM_APP_SECRET=your_app_secret
  5. Generate a long-lived User Access Token with these scopes:
       instagram_basic, instagram_content_publish, instagram_manage_insights,
       pages_show_list, pages_read_engagement
  6. Find your Instagram User ID (numeric) from the Graph API Explorer or:
       GET https://graph.facebook.com/v21.0/me/accounts?access_token=<token>
       then GET /<page_id>?fields=instagram_business_account
  7. Add to .env:
       INSTAGRAM_USER_ID=your_numeric_user_id
       INSTAGRAM_ACCESS_TOKEN=your_long_lived_token

Token notes:
  - Short-lived tokens expire in 1 hour
  - Long-lived tokens expire in 60 days
  - Call refresh_token() periodically (or schedule it monthly) to keep the token alive
  - refresh_token() requires a long-lived token to exchange (not a short-lived one)

Image URL requirement:
  - Instagram Graph API ONLY accepts publicly accessible HTTPS image URLs
  - Local file paths will NOT work — use upload_to_tmphost() to get a public URL first
  - Supported formats: JPEG (recommended), PNG
  - Minimum resolution: 320×320px | Maximum resolution: 1440px wide
  - Aspect ratios: 1:1 (square), 4:5 (portrait), 1.91:1 (landscape)
"""
from __future__ import annotations

import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import Any

ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")

BASE_URL = "https://graph.facebook.com/v21.0"

# How long (seconds) to poll for a media container to finish processing
_CONTAINER_POLL_INTERVAL = 3
_CONTAINER_POLL_MAX_ATTEMPTS = 20

# Video/Reels processing is much slower than image processing — give it up to
# 60 attempts * 3s = 3 minutes before giving up (vs. ~60s for images).
_VIDEO_CONTAINER_POLL_MAX_ATTEMPTS = 60


class InstagramAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Instagram API {status}: {message}")


class InstagramAPIClient:
    """
    Meta Instagram Graph API v21.0 client (no third-party dependencies).

    All media-posting methods require that image URLs are publicly accessible
    HTTPS endpoints. Local file paths cannot be used — see upload_to_tmphost()
    for a stub that explains the hosting options available.
    """

    def __init__(self, user_id: str = "", access_token: str = ""):
        self.user_id = user_id or os.getenv("INSTAGRAM_USER_ID", "")
        self.access_token = access_token or os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
        self.app_id = os.getenv("INSTAGRAM_APP_ID", "")
        self.app_secret = os.getenv("INSTAGRAM_APP_SECRET", "")

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
        """Raise InstagramAPIError when essential credentials are missing."""
        if not self.access_token:
            raise InstagramAPIError(
                0,
                "No Instagram access token configured. Add INSTAGRAM_ACCESS_TOKEN to .env.",
            )
        if not self.user_id:
            raise InstagramAPIError(
                0,
                "No Instagram user ID configured. Add INSTAGRAM_USER_ID to .env.",
            )

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        body: dict | None = None,
    ) -> dict:
        """
        Make an authenticated request to the Instagram Graph API.

        Handles retries on 429 (rate limit) and 503 (transient server error)
        with exponential backoff. On 190/401 (expired token) raises
        InstagramAPIError so the caller can react (e.g. call refresh_token()).
        """
        self._require_auth()

        # Always inject the access token into query params (Graph API style)
        query: dict[str, Any] = {"access_token": self.access_token}
        if params:
            query.update(params)

        url = f"{BASE_URL}/{path.lstrip('/')}"
        url = f"{url}?{urllib.parse.urlencode(query)}"

        headers = {"Content-Type": "application/json"}
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        retryable_http = {429, 503}
        delays = [3, 6]  # seconds between attempt 1→2 and 2→3

        last_exc: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(delays[attempt - 1])
            try:
                req = urllib.request.Request(url, data=data, headers=headers, method=method)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    raw = resp.read().decode()
                    return json.loads(raw) if raw.strip() else {}
            except urllib.error.HTTPError as e:
                if e.code in retryable_http:
                    last_exc = e
                    continue
                body_text = e.read().decode()
                try:
                    err = json.loads(body_text)
                    # Graph API error details live under {"error": {...}}
                    error_obj = err.get("error", {})
                    if isinstance(error_obj, dict):
                        msg = error_obj.get("message", body_text)
                    else:
                        msg = str(error_obj) or body_text
                except Exception:
                    msg = body_text
                raise InstagramAPIError(e.code, msg)
            except (OSError, urllib.error.URLError) as e:
                last_exc = e
                continue

        # All attempts exhausted
        if isinstance(last_exc, urllib.error.HTTPError):
            body_text = last_exc.read().decode()
            try:
                err = json.loads(body_text)
                error_obj = err.get("error", {})
                msg = error_obj.get("message", body_text) if isinstance(error_obj, dict) else body_text
            except Exception:
                msg = body_text
            raise InstagramAPIError(last_exc.code, msg)
        raise InstagramAPIError(0, f"Network error after retries: {last_exc}")

    def _create_media_container(
        self,
        image_url: str = "",
        caption: str = "",
        is_carousel_item: bool = False,
        video_url: str = "",
        media_type: str = "",
    ) -> str:
        """
        Step 1 of 2 for photo/video posting — create a media container.

        Args:
            image_url: A publicly accessible HTTPS URL. Local paths will be
                rejected by Instagram's servers. Mutually exclusive with video_url.
            caption: Post caption (only used for non-carousel-item containers).
            is_carousel_item: When True, omits the caption and marks the
                container as a carousel child.
            video_url: A publicly accessible HTTPS URL to an MP4. Used for
                video/Reels posting instead of image_url.
            media_type: e.g. "REELS" or "VIDEO" — required when video_url is set.

        Returns:
            The container ID string.
        """
        body: dict[str, Any] = {}
        if video_url:
            body["video_url"] = video_url
            if media_type:
                body["media_type"] = media_type
        else:
            body["image_url"] = image_url

        if is_carousel_item:
            body["is_carousel_item"] = True
        else:
            if caption:
                body["caption"] = caption

        result = self._request("POST", f"{self.user_id}/media", body=body)
        container_id = result.get("id", "")
        if not container_id:
            raise InstagramAPIError(0, f"Media container creation returned no ID. Response: {result}")
        return container_id

    def _wait_for_container(self, container_id: str, max_attempts: int = _CONTAINER_POLL_MAX_ATTEMPTS) -> None:
        """
        Poll the container status field until it reaches FINISHED.

        Instagram processes uploaded images asynchronously before allowing
        publish. Polling typically resolves within 3–10 seconds for images,
        but can take much longer for video — pass a higher max_attempts for
        video/Reels containers.

        Raises InstagramAPIError if the container errors out or the poll
        timeout is exceeded.
        """
        for _ in range(max_attempts):
            result = self._request(
                "GET",
                container_id,
                params={"fields": "status_code,status"},
            )
            status_code = result.get("status_code", "")
            if status_code == "FINISHED":
                return
            if status_code == "ERROR":
                status_detail = result.get("status", "unknown error")
                raise InstagramAPIError(0, f"Media container processing failed: {status_detail}")
            # IN_PROGRESS or PUBLISHED — keep polling
            time.sleep(_CONTAINER_POLL_INTERVAL)

        raise InstagramAPIError(
            0,
            f"Media container {container_id} did not finish processing within "
            f"{max_attempts * _CONTAINER_POLL_INTERVAL}s.",
        )

    def _publish_container(self, container_id: str) -> dict:
        """
        Step 2 of 2 for photo/carousel posting — publish a finished container.

        Returns:
            The publish response dict containing the new media 'id'.
        """
        result = self._request(
            "POST",
            f"{self.user_id}/media_publish",
            body={"creation_id": container_id},
        )
        if not result.get("id"):
            raise InstagramAPIError(0, f"Media publish returned no media ID. Response: {result}")
        return result

    # ── Public API methods ────────────────────────────────────────────────────

    def post_photo(self, image_url: str, caption: str = "") -> dict:
        """
        Publish a single photo to the Instagram feed.

        This is a 2-step process:
          1. Create a media container (uploads the image reference to Meta servers)
          2. Publish the container (makes it live on the profile)

        Args:
            image_url: Must be a publicly accessible HTTPS URL. Instagram's
                servers will fetch this URL directly — local file paths and
                private URLs will fail. Use upload_to_tmphost() to get a
                public URL from a local file.
            caption: Post caption. Supports hashtags and emoji. Max 2,200 chars.

        Returns:
            Dict with 'id' key containing the published media ID.

        Raises:
            InstagramAPIError: On API error, container processing failure, or
                if credentials are not configured.
        """
        container_id = self._create_media_container(image_url, caption=caption)
        self._wait_for_container(container_id)
        return self._publish_container(container_id)

    def post_video(self, video_url: str, caption: str = "", is_reel: bool = True) -> dict:
        """
        Publish a video to Instagram as a Reel (default) or feed video.

        Same 2-step process as post_photo(), but video containers take much
        longer to process — polling uses a higher attempt ceiling
        (_VIDEO_CONTAINER_POLL_MAX_ATTEMPTS) than the image path.

        Args:
            video_url: Must be a publicly accessible HTTPS URL pointing to an
                MP4 file. Instagram's servers fetch this directly — a local
                file path will fail. Serve the generated video from this
                app's own public URL (e.g. RAILWAY_APP_URL + /api/files/...).
            caption: Post caption. Supports hashtags and emoji. Max 2,200 chars.
            is_reel: When True (default), publishes as a Reel (media_type=REELS).
                When False, publishes as a regular feed video (media_type=VIDEO).

        Returns:
            Dict with 'id' key containing the published media ID.

        Raises:
            InstagramAPIError: On API error, container processing failure, or
                if credentials are not configured.
        """
        media_type = "REELS" if is_reel else "VIDEO"
        container_id = self._create_media_container(
            video_url=video_url, caption=caption, media_type=media_type
        )
        self._wait_for_container(container_id, max_attempts=_VIDEO_CONTAINER_POLL_MAX_ATTEMPTS)
        return self._publish_container(container_id)

    def post_carousel(self, image_urls: list[str], caption: str = "") -> dict:
        """
        Publish a carousel (multi-image) post to the Instagram feed.

        Carousel posts support 2–10 images. Each image is individually
        uploaded as a carousel item container, then combined into a single
        carousel container, and finally published.

        This is a 3-step process per Instagram's API:
          1. Create one media container per image (carousel items)
          2. Create a carousel container referencing all item container IDs
          3. Publish the carousel container

        Args:
            image_urls: List of 2–10 publicly accessible HTTPS image URLs.
                All URLs must be reachable by Meta's servers. Local paths
                will not work — see upload_to_tmphost().
            caption: Caption for the carousel post. Max 2,200 chars.
                Applied to the carousel container, not individual slides.

        Returns:
            Dict with 'id' key containing the published media ID.

        Raises:
            InstagramAPIError: If fewer than 2 or more than 10 URLs are
                provided, or on any API or network error.
            ValueError: If image_urls is empty or has only 1 item.
        """
        if len(image_urls) < 2:
            raise ValueError("post_carousel requires at least 2 image URLs.")
        if len(image_urls) > 10:
            raise ValueError("post_carousel supports a maximum of 10 image URLs.")

        # Step 1 — create individual carousel item containers
        item_ids: list[str] = []
        for idx, url in enumerate(image_urls):
            container_id = self._create_media_container(url, is_carousel_item=True)
            self._wait_for_container(container_id)
            item_ids.append(container_id)

        # Step 2 — create the parent carousel container
        carousel_body: dict[str, Any] = {
            "media_type": "CAROUSEL",
            "children": ",".join(item_ids),
        }
        if caption:
            carousel_body["caption"] = caption

        result = self._request("POST", f"{self.user_id}/media", body=carousel_body)
        carousel_id = result.get("id", "")
        if not carousel_id:
            raise InstagramAPIError(0, f"Carousel container creation returned no ID. Response: {result}")

        self._wait_for_container(carousel_id)

        # Step 3 — publish
        return self._publish_container(carousel_id)

    def get_insights(self, metric: str, period: str = "day") -> dict:
        """
        Fetch account-level insights from the Instagram Graph API.

        Args:
            metric: One of: 'impressions', 'reach', 'follower_count',
                'profile_views', 'website_clicks', 'email_contacts',
                'phone_call_clicks', 'get_directions_clicks'.
                Multiple metrics can be passed as a comma-separated string,
                e.g. "impressions,reach".
            period: Time period for the metric. One of:
                'day', 'week', 'days_28', 'month', 'lifetime'.
                Not all metrics support all periods — see Meta docs.

        Returns:
            Raw Graph API response dict containing a 'data' list of metric
            objects, each with 'name', 'period', 'values', and 'title'.

        Raises:
            InstagramAPIError: On API error or missing credentials.

        Notes:
            - Requires instagram_manage_insights permission on the access token.
            - 'follower_count' only supports period='day'.
            - Insights are available for Business and Creator accounts only.
        """
        return self._request(
            "GET",
            f"{self.user_id}/insights",
            params={"metric": metric, "period": period},
        )

    def get_recent_posts(self, limit: int = 10) -> list[dict]:
        """
        Fetch the most recent media posts from the connected Instagram account.

        Args:
            limit: Number of posts to return. Max 100. Defaults to 10.

        Returns:
            List of media dicts, each containing:
                id, caption, media_type, timestamp,
                like_count, comments_count, permalink.
            List is ordered newest-first.

        Raises:
            InstagramAPIError: On API error or missing credentials.
        """
        fields = "id,caption,media_type,timestamp,like_count,comments_count,permalink"
        result = self._request(
            "GET",
            f"{self.user_id}/media",
            params={"fields": fields, "limit": min(limit, 100)},
        )
        return result.get("data", [])

    def refresh_token(self) -> bool:
        """
        Exchange the current long-lived access token for a fresh 60-day token.

        Meta long-lived tokens expire in 60 days. This method calls the
        token refresh endpoint to obtain a new 60-day token and automatically
        persists it to the .env file under INSTAGRAM_ACCESS_TOKEN.

        This method requires:
          - INSTAGRAM_APP_SECRET set in .env
          - The current access token must already be a long-lived token
            (short-lived tokens cannot be refreshed this way — they must be
            exchanged first via the full OAuth flow)

        Returns:
            True on success, False if credentials are missing or the request
            fails (does NOT raise — safe to call in background jobs).

        Usage:
            Schedule monthly (e.g. via cron or a startup hook) to prevent
            token expiry.
        """
        if not self.access_token or not self.app_secret:
            return False

        params = urllib.parse.urlencode({
            "grant_type": "ig_refresh_token",
            "access_token": self.access_token,
        })
        url = f"https://graph.instagram.com/refresh_access_token?{params}"
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
        except Exception:
            return False

        new_token = data.get("access_token", "")
        if not new_token:
            return False

        self.access_token = new_token
        self._update_env("INSTAGRAM_ACCESS_TOKEN", new_token)
        return True

    def get_account_info(self) -> dict:
        """
        Fetch basic profile information for the connected Instagram account.

        Returns:
            Dict containing:
                id           — numeric Instagram user ID
                name         — display name
                biography    — profile bio text
                username     — Instagram handle (e.g. "onbrandcraftz2026")
                followers_count — number of followers
                follows_count   — number of accounts followed
                media_count     — total posts published
                profile_picture_url — URL of the profile picture
                website      — link in bio

        Raises:
            InstagramAPIError: On API error or missing credentials.
        """
        fields = (
            "id,name,biography,username,followers_count,"
            "follows_count,media_count,profile_picture_url,website"
        )
        return self._request(
            "GET",
            self.user_id,
            params={"fields": fields},
        )


# ── Module-level helpers ──────────────────────────────────────────────────────


def is_configured() -> bool:
    """Return True if INSTAGRAM_ACCESS_TOKEN is set in the environment."""
    return bool(os.getenv("INSTAGRAM_ACCESS_TOKEN", ""))


def get_client() -> InstagramAPIClient:
    """Return a ready-to-use InstagramAPIClient using credentials from .env."""
    return InstagramAPIClient()


def upload_to_tmphost(local_path: str) -> str:
    """
    Upload a local image file to a public hosting service and return its URL.

    STUB — not yet implemented.

    Instagram's Graph API requires a publicly accessible HTTPS URL for all
    image uploads. Local file paths cannot be passed to post_photo() or
    post_carousel() directly.

    Recommended hosting options (pick one and implement here):

    Option A — Cloudinary (recommended for production):
        pip install cloudinary
        import cloudinary, cloudinary.uploader
        cloudinary.config(cloud_name=..., api_key=..., api_secret=...)
        result = cloudinary.uploader.upload(local_path)
        return result["secure_url"]
        Env vars to add: CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY,
                         CLOUDINARY_API_SECRET

    Option B — AWS S3 with a public bucket:
        pip install boto3
        import boto3
        s3 = boto3.client("s3", ...)
        bucket = os.getenv("AWS_S3_BUCKET")
        key = os.path.basename(local_path)
        s3.upload_file(local_path, bucket, key, ExtraArgs={"ACL": "public-read"})
        return f"https://{bucket}.s3.amazonaws.com/{key}"

    Option C — Etsy CDN (re-use already-uploaded listing images):
        If the image is already uploaded as an Etsy listing photo, use the
        'url_fullxfull' field from get_listing_images() as the image_url.
        This costs nothing extra and keeps all assets inside the ecosystem.

    Option D — tmpfiles.org / file.io (quick prototype only, not production):
        Files expire after a short window — suitable for testing but not for
        scheduled posts where the URL must remain valid for hours.

    Args:
        local_path: Absolute or relative path to the local image file.

    Returns:
        A publicly accessible HTTPS URL string.

    Raises:
        NotImplementedError: Always, until a hosting backend is wired up.
    """
    raise NotImplementedError(
        "upload_to_tmphost() is a stub. "
        "Choose a public hosting backend (Cloudinary, S3, or Etsy CDN) "
        "and implement it here before calling post_photo() or post_carousel() "
        "with local file paths. See the docstring for implementation options."
    )
