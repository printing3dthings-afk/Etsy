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
import re
import time
import random
import urllib.request
import urllib.parse
import urllib.error
import requests
from typing import Any

# Auto-load .env on import so every consumer (scripts, ad-hoc python -c, agents)
# gets credentials without copy-pasting a parser. setdefault never overrides
# values already in the environment.
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_ENV_PATH):
    with open(_ENV_PATH) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

BASE_URL = "https://openapi.etsy.com/v3/application"

# A fresh EtsyAPIClient() is instantiated at every call site in main.py (never a
# singleton), so connection reuse has to live at module scope rather than on the
# client instance -- this session outlives any individual client and eliminates a
# fresh TCP+TLS handshake (~100-300ms) from every Etsy call, the most frequently
# invoked external dependency in the app (2026-07-08 performance pass). Safe for
# concurrent use across threads (requests.Session is backed by urllib3's thread-safe
# PoolManager) as long as no caller mutates session.headers/session.cookies per-call
# -- this module never does; headers are built fresh per request in _build_request.
_session = requests.Session()

# Etsy hard limit: 20 MB per digital file
MAX_DIGITAL_FILE_BYTES = 20 * 1024 * 1024

# Magic-byte signatures used to confirm a file's real type matches its extension.
# Catches the catastrophic failure mode where a raw image (e.g. a lifestyle room
# scene) gets renamed/uploaded as the product the customer downloads.
_FILE_MAGIC = {
    ".pdf":  [b"%PDF"],
    ".zip":  [b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"],  # incl. empty/spanned
    ".jpg":  [b"\xff\xd8\xff"],
    ".jpeg": [b"\xff\xd8\xff"],
    ".png":  [b"\x89PNG\r\n\x1a\n"],
}

# A planner PDF that generates correctly is 80+ pages; anything in single digits is
# the near-empty-PDF failure (broken page routing). 10 is a safe floor for any PDF.
MIN_PDF_PAGES = 10


class EtsyAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Etsy API {status}: {message}")


# Optional circuit-breaker hook, set once at server boot via set_circuit_breaker_hook().
# Duck-typed (allow_request/record_success/record_failure) so this module never imports
# tools/api_server/resilience.py or db.py -- standalone scripts that use EtsyAPIClient
# outside the FastAPI server never call the setter, so this stays None and behavior is
# unchanged for them.
_circuit_breaker_hook = None


def set_circuit_breaker_hook(hook) -> None:
    """Route every EtsyAPIClient._request() call through `hook` for breaker
    gating/recording. Pass None to disable."""
    global _circuit_breaker_hook
    _circuit_breaker_hook = hook


# Optional rate-limit sample recorder, set once at server boot via
# set_rate_limit_sample_hook() (wired to db.record_rate_limit_sample). Same
# duck-typed/None-default pattern as the circuit-breaker hook above, for the
# same reason: standalone scripts using EtsyAPIClient outside the FastAPI
# server never call the setter, so this stays a no-op for them (2026-07-10 --
# added so "what's our real daily Etsy call volume" has a measured answer
# instead of only a code-derived estimate).
_rate_limit_sample_hook = None


def set_rate_limit_sample_hook(hook) -> None:
    """Call `hook(remaining_today, remaining_this_second, limit_per_day,
    limit_per_second)` every time a response carries rate-limit headers.
    Pass None to disable."""
    global _rate_limit_sample_hook
    _rate_limit_sample_hook = hook


# Etsy status codes that indicate the dependency itself is unhealthy (rate limit /
# server-side) -- mirrors resilience.py's _RETRYABLE_ETSY_STATUSES. A clean 4xx (400,
# 404, etc.) means Etsy responded correctly and our request was wrong, so it must not
# trip the breaker. 403 specifically means auth failure (stale OAuth token) — NOT a
# service outage, so it must NOT trip the breaker (would show Etsy as DOWN when UP).
_BREAKER_TRIP_STATUSES = {429, 500, 502, 503}


class FileContentError(Exception):
    """Raised when a digital file fails the pre-upload content gate.

    This is intentionally NOT an EtsyAPIError — it fires *before* any network
    call so a bad/empty/mislabeled file never reaches a buyer's download.
    """


def check_svg_quality(svg_text: str) -> dict:
    """Check one SVG's text for clean-vector-art quality — the single source of
    truth for the "is this a traced raster or a real vector" thresholds, used
    both by the real upload gate (_validate_svgs_in_zip below) and by the
    Studio SVG Converter tool's live pass/fail preview (tools/svg_converter.py
    callers), so the two never drift apart.

    A traced raster masquerading as an SVG has 500+ unique fill colors and 500+
    paths — it looks like an SVG but is pixel-data encoded as bezier segments.
    Such a file cannot be used for 3D printing as a clean multi-color design.

    Thresholds:
      - unique fill colors > 20  → traced raster, not a print-ready vector
      - path elements > 200      → traced raster
      - file size > 150 KB       → clean vector SVGs are typically < 50 KB
        (only flagged when combined with the above — see inline note)

    Returns {unique_fills, path_count, size_kb, passes_gate, problems: [...]}.
    """
    import re as _re
    size_kb = len(svg_text.encode()) / 1024

    # Count path elements (handle namespace prefixes like ns0:path)
    path_count = len(_re.findall(r"<(?:\w+:)?path[\s>]", svg_text))

    # Count unique hex fill colors
    fills = _re.findall(r'fill="(#[0-9a-fA-F]{3,6})"', svg_text)
    unique_fills = len(set(f for f in fills if f.lower() != "none"))

    problems = []
    if unique_fills > 20:
        problems.append(
            f"{unique_fills} unique fill colors — clean 3D-print SVGs have ≤4 discrete fills. "
            f"This is a traced raster image, not a vector design. "
            f"Buyers cannot use the Color Painting Fill tool on this file."
        )
    if path_count > 200:
        problems.append(
            f"{path_count} path elements — clean vector designs have <200. "
            f"This indicates auto-traced raster art."
        )
    # Size is only a red flag when combined with bad fills/paths.
    # Single-file multi-color SVGs (4 color layers merged) legitimately run
    # 200–400 KB; individual layer files should be <150 KB.
    is_clean = unique_fills <= 20 and path_count <= 200
    if size_kb > 500:
        problems.append(
            f"{size_kb:.0f} KB — even a multi-color single-file SVG should be <500 KB. "
            f"Likely raster-trace origin."
        )
    elif size_kb > 150 and not is_clean:
        problems.append(
            f"{size_kb:.0f} KB — oversized for a layer SVG and has other quality problems. "
            f"Likely raster-trace origin."
        )
    return {
        "unique_fills": unique_fills,
        "path_count": path_count,
        "size_kb": size_kb,
        "passes_gate": is_clean and size_kb <= 500,
        "problems": problems,
    }


def _validate_svgs_in_zip(zf, svg_names: list) -> list[str]:
    """Check each SVG in an open ZipFile for clean vector art quality —
    see check_svg_quality() for the actual thresholds."""
    errors = []
    for name in svg_names:
        try:
            content = zf.read(name).decode("utf-8", errors="replace")
        except Exception as exc:
            errors.append(f"{name}: could not read ({exc})")
            continue
        result = check_svg_quality(content)
        if result["problems"]:
            errors.append(f"{name}: " + "; ".join(result["problems"]))
    return errors


def validate_digital_file(
    file_path: str,
    expected_ext: str | None = None,
    min_pdf_pages: int = MIN_PDF_PAGES,
) -> dict:
    """Inspect a digital file before upload. Raises FileContentError on any problem.

    Checks (in order):
      1. File exists and is non-empty
      2. Size is within Etsy's 20 MB per-file limit
      3. Extension is a known digital type (and matches expected_ext if given)
      4. Magic bytes match the extension — the real content type is what it claims
      5. ZIP: opens cleanly, passes CRC, contains real content (not a lone image
         mislabeled as a pack), no path traversal entries
      6. PDF: parses and has at least `min_pdf_pages` pages (catches near-empty PDFs)

    Returns a small dict of facts about the file on success.
    """
    import zipfile

    if not os.path.exists(file_path):
        raise FileContentError(f"file does not exist: {file_path}")
    size = os.path.getsize(file_path)
    if size == 0:
        raise FileContentError(f"file is empty (0 bytes): {file_path}")
    if size > MAX_DIGITAL_FILE_BYTES:
        raise FileContentError(
            f"file is {size/1048576:.1f} MB — exceeds Etsy's 20 MB per-file limit: {file_path}"
        )

    ext = os.path.splitext(file_path)[1].lower()
    if expected_ext and ext != expected_ext.lower():
        raise FileContentError(
            f"expected a {expected_ext} file but got {ext or 'no extension'}: {file_path}"
        )
    if ext not in _FILE_MAGIC:
        raise FileContentError(
            f"unsupported digital file type '{ext or 'none'}' "
            f"(allowed: {', '.join(sorted(_FILE_MAGIC))}): {file_path}"
        )

    with open(file_path, "rb") as fh:
        head = fh.read(16)
    if not any(head.startswith(sig) for sig in _FILE_MAGIC[ext]):
        raise FileContentError(
            f"content does not match a {ext} file — header is {head[:8]!r}. "
            f"A mislabeled or corrupt file would ship the wrong product: {file_path}"
        )

    facts: dict[str, Any] = {"path": file_path, "ext": ext, "size_bytes": size}

    if ext == ".zip":
        try:
            with zipfile.ZipFile(file_path) as zf:
                bad = zf.testzip()
                if bad is not None:
                    raise FileContentError(f"ZIP failed CRC check on member '{bad}': {file_path}")
                names = [n for n in zf.namelist() if not n.endswith("/")]
                if not names:
                    raise FileContentError(f"ZIP is empty (no files inside): {file_path}")
                for n in names:
                    if n.startswith("/") or ".." in n.split("/"):
                        raise FileContentError(f"ZIP contains unsafe path '{n}': {file_path}")
                # A pack must contain real deliverables, not be a single mislabeled image
                content = [n for n in names
                           if os.path.splitext(n)[1].lower()
                           in (".png", ".jpg", ".jpeg", ".pdf", ".svg", ".txt", ".goodnotes")]
                if not content:
                    raise FileContentError(
                        f"ZIP has no recognizable product files (png/jpg/pdf/svg): {file_path}"
                    )
                facts["zip_members"] = len(names)
                # SVG pack validation — every SVG in the ZIP must be clean vector art,
                # not a traced raster. Traced rasters have hundreds of unique fills and
                # hundreds of paths; clean print-ready SVGs have very few of each.
                svg_names = [n for n in names if os.path.splitext(n)[1].lower() == ".svg"]
                if svg_names:
                    svg_errors = _validate_svgs_in_zip(zf, svg_names)
                    if svg_errors:
                        raise FileContentError(
                            f"ZIP contains SVG files that are NOT clean vector art:\n"
                            + "\n".join(f"  ✗ {e}" for e in svg_errors)
                        )
                    facts["svg_count"] = len(svg_names)
        except zipfile.BadZipFile:
            raise FileContentError(f"file is not a valid ZIP archive: {file_path}")

    elif ext == ".pdf":
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            pages = len(reader.pages)
        except FileContentError:
            raise
        except Exception as e:
            raise FileContentError(f"PDF could not be parsed ({e}): {file_path}")
        if pages < min_pdf_pages:
            raise FileContentError(
                f"PDF has only {pages} page(s) — expected at least {min_pdf_pages}. "
                f"This is the near-empty-PDF failure; do not ship it: {file_path}"
            )
        facts["pdf_pages"] = pages

    return facts


# Anchored to the exact "Pages: N" label format CLAUDE.md's own pre-written listing
# templates use in every TECHNICAL DETAILS section (e.g. "• Pages: 143 (each version)").
# Deliberately NOT a bare `\d+ pages` match -- description body copy routinely mentions
# unrelated numbers next to the word "pages" in a different sense ("365 Daily Pages" is
# a section name, not a total-page-count claim) and a loose match would false-positive
# on those.
_PAGE_CLAIM_RE = re.compile(r"pages?\s*[:\-]\s*(\d{1,4})", re.IGNORECASE)
# Looser on purpose -- see check_description_count_claims()'s docstring for why this
# one is safe as a one-directional floor check even with multiple/loose matches.
_STICKER_CLAIM_RE = re.compile(r"(\d{1,5})\+?\s*(?:individual\s+)?stickers\b", re.IGNORECASE)


def check_description_count_claims(description: str, facts: dict) -> list[str]:
    """Cross-checks numeric claims in a listing description against the real, computed
    facts of the file actually being uploaded (from validate_digital_file()). This is
    the code-level enforcement CLAUDE.md's 'NEVER LIE TO THE CUSTOMER' rule describes
    but, before this, only checked via manual review -- catches exactly the failure
    modes it calls out by name: a '200+ stickers' claim when the ZIP contains fewer, a
    page count that doesn't match the real PDF.

    Returns a list of human-readable mismatch descriptions (empty = no claims found, or
    every claim found is consistent with the facts). Never raises -- the caller decides
    whether a mismatch is a hard block or a loud warning.

    Two different check shapes, deliberately:
      - PDF page count: exact-equality against facts['pdf_pages'] via the anchored
        "Pages: N" label format. A planner's total page count is an unambiguous fact
        once the file exists, so exact match is the right bar.
      - ZIP sticker/item count: only flagged if the claimed count EXCEEDS
        facts['zip_members'] (total file count in the ZIP). A real sticker pack
        legitimately contains MORE files than its claimed sticker count (a README,
        PNG reference sheets, a GoodNotes book, individual crops) -- so this is a
        one-directional "you cannot promise more than physically exists in the box"
        floor check, not an exact-match check. Safe even if the description mentions
        stickers more than once; the largest claimed number is what's checked.
    """
    if not description:
        return []
    problems: list[str] = []

    page_matches = [int(m.group(1)) for m in _PAGE_CLAIM_RE.finditer(description)]
    if page_matches and "pdf_pages" in facts:
        real_pages = facts["pdf_pages"]
        bad = [c for c in page_matches if c != real_pages]
        if bad:
            problems.append(
                f"description claims {sorted(set(bad))} page(s) but the actual PDF has "
                f"{real_pages} page(s) — fix the description or the file before shipping"
            )

    sticker_matches = [int(m.group(1)) for m in _STICKER_CLAIM_RE.finditer(description)]
    if sticker_matches and "zip_members" in facts:
        claimed = max(sticker_matches)
        actual = facts["zip_members"]
        if claimed > actual:
            problems.append(
                f"description claims '{claimed}+ stickers' but the ZIP only contains "
                f"{actual} file(s) total — the claim cannot be true, fix the description "
                f"or regenerate the pack before shipping"
            )

    return problems


def _dp_code_listing_mismatch(listing_id: int | str, file_path: str) -> str | None:
    """Return an error message if file_path's DP code belongs to a different listing.

    Looks up dp_listing_map.json (listing_id, individual_listing_id,
    bundle_listing_id, planner_listing_id all count as ownership). If the file
    carries a DP code and the target listing is owned by a different code,
    the upload is blocked. Returns None when no conflict can be proven
    (unknown listing, no DP code in filename, or map unreadable).
    """
    import re as _re
    m = _re.search(r"((?:DP|WA)\d{4})", os.path.basename(file_path).upper())
    if not m:
        return None
    file_code = m.group(1)

    map_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "data", "dp_listing_map.json")
    try:
        with open(map_path) as fh:
            dp_map = json.load(fh)
    except Exception:
        return None

    lid = str(listing_id)
    owners = set()
    for code, entry in dp_map.items():
        if not isinstance(entry, dict):
            continue
        for key in ("listing_id", "individual_listing_id", "bundle_listing_id", "planner_listing_id"):
            if str(entry.get(key)) == lid:
                owners.add(code.upper())
    if owners and file_code not in owners:
        return (
            f"DP code mismatch: file {os.path.basename(file_path)} carries {file_code} "
            f"but listing {lid} belongs to {sorted(owners)} per dp_listing_map.json. "
            f"This is the wrong-file-shipped-to-customer failure. Fix the file or the "
            f"listing, or pass skip_validation=True after manual review."
        )
    return None


class EtsyAPIClient:
    """Lightweight Etsy Open API v3 client (no third-party dependencies)."""

    def __init__(self, api_key: str = "", access_token: str = ""):
        # .strip() every credential: Railway (and any dashboard-pasted env var)
        # can carry trailing newlines/spaces. An embedded "\n" makes urllib raise
        # "Invalid header value" and EVERY Etsy call fails. The .env parser strips
        # values, but os.environ values set by the platform do not — so strip here.
        self.api_key = (api_key or os.getenv("ETSY_API_KEY", "")).strip()
        self.client_id = (os.getenv("ETSY_CLIENT_ID") or self.api_key).strip()
        self.client_secret = os.getenv("ETSY_CLIENT_SECRET", "").strip()
        self.access_token = (access_token or os.getenv("ETSY_ACCESS_TOKEN", "")).strip()
        self.shop_id = (os.getenv("ETSY_SHOP_ID_NUMERIC") or os.getenv("ETSY_SHOP_ID", "")).strip()
        # Rate-limit state, refreshed from response headers on every call. Lets us
        # throttle BEFORE hitting 429 instead of only reacting to it.
        self.rate_limit = {
            "limit_per_second": None,
            "remaining_this_second": None,
            "limit_per_day": None,
            "remaining_today": None,
        }

    def _record_rate_limit(self, headers) -> None:
        """Capture Etsy's x-limit / x-remaining headers from a response."""
        def _int(name):
            v = headers.get(name)
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None
        rl = self.rate_limit
        rl["limit_per_second"] = _int("x-limit-per-second") or rl["limit_per_second"]
        rl["limit_per_day"] = _int("x-limit-per-day") or rl["limit_per_day"]
        sec = _int("x-remaining-this-second")
        day = _int("x-remaining-today")
        if sec is not None:
            rl["remaining_this_second"] = sec
        if day is not None:
            rl["remaining_today"] = day
        if day is not None and _rate_limit_sample_hook is not None:
            try:
                _rate_limit_sample_hook(day, sec, rl["limit_per_day"], rl["limit_per_second"])
            except Exception:
                pass  # visibility logging must never break a live Etsy call

    def _throttle_if_needed(self) -> None:
        """Pre-emptively pace requests based on the last seen rate-limit headers.

        Per CLAUDE.md: if remaining-this-second is low, sleep ~1s before the next call.
        Stops the 'death by 429' loop where a batch hammers the per-second cap.
        """
        rl = self.rate_limit
        if rl["remaining_today"] is not None and rl["remaining_today"] <= 0:
            raise EtsyAPIError(429, "daily rate limit exhausted (x-remaining-today=0)")
        sec = rl["remaining_this_second"]
        if sec is not None and sec <= 2:
            time.sleep(1.0)

    def _build_request(self, body: dict | None) -> tuple[dict, bytes | None]:
        """Returns (headers, data) for a requests.Session call -- the method/url
        no longer need to be threaded through here since the caller passes them
        directly to _session.request()."""
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
        return headers, data

    def _request(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        """Thin gate around `_request_impl` -- consults the circuit-breaker hook
        (if one was set by main.py at boot) before the call and records the
        outcome after, so a real Etsy outage shows up in /api/system/dependencies
        instead of always reporting closed/healthy."""
        cb = _circuit_breaker_hook
        if cb is not None and not cb.allow_request():
            raise EtsyAPIError(0, "circuit breaker open for etsy_api -- skipping call until cooldown elapses")
        try:
            result = self._request_impl(method, path, params, body)
        except EtsyAPIError as e:
            if cb is not None and (e.status == 0 or e.status in _BREAKER_TRIP_STATUSES):
                cb.record_failure()
            raise
        else:
            if cb is not None:
                cb.record_success()
            return result

    def _request_impl(self, method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
        """requests-based rewrite (2026-07-08 performance pass) of what was a raw
        urllib.request.urlopen() call per attempt -- now goes through the module-level
        _session so repeated calls reuse the underlying TCP+TLS connection. requests
        does not raise on 4xx/5xx like urllib.error.HTTPError did, so every branch below
        checks resp.status_code explicitly instead of catching an exception; the retry
        count, backoff/jitter, 429/503-retry, and 401-refresh-and-retry-once behavior
        are otherwise unchanged from the previous implementation."""
        url = f"{BASE_URL}/{path.lstrip('/')}"
        if params:
            url = f"{url}?{urllib.parse.urlencode(params)}"

        retryable_http = {429, 503}
        base_delays = [2, 4]  # exponential backoff base: 2s then 4s

        def _jittered(base: float) -> float:
            return base * (0.75 + random.random() * 0.5)  # ±25% jitter

        def _error_message(resp: requests.Response) -> str:
            try:
                err = resp.json()
                return err.get("error", resp.text)
            except Exception:
                return resp.text

        last_exc: Exception | None = None
        for attempt in range(3):
            if attempt > 0:
                time.sleep(_jittered(base_delays[attempt - 1]))
            self._throttle_if_needed()
            try:
                headers, data = self._build_request(body)
                resp = _session.request(method, url, data=data, headers=headers, timeout=15)
            except requests.exceptions.RequestException as e:
                last_exc = e
                continue  # retry on network errors

            self._record_rate_limit(resp.headers)
            if resp.status_code < 400:
                raw = resp.text
                return json.loads(raw) if raw.strip() else {}

            if resp.status_code == 401 and self.access_token and self.refresh_access_token():
                # Token refreshed — retry once immediately (not counted as a backoff attempt).
                # A network error here propagates uncaught, matching the prior urllib
                # behavior (the inner except only caught HTTPError, never OSError/URLError).
                headers, data = self._build_request(body)
                resp2 = _session.request(method, url, data=data, headers=headers, timeout=15)
                self._record_rate_limit(resp2.headers)
                if resp2.status_code >= 400:
                    raise EtsyAPIError(resp2.status_code, _error_message(resp2))
                raw = resp2.text
                return json.loads(raw) if raw.strip() else {}

            if resp.status_code in retryable_http:
                # Honour the server's retry-after header when present, but cap it --
                # 2026-07-10 fix: an uncapped sleep here let a single in-flight call
                # block its request thread for however long Etsy asked to wait (seen
                # live: a daily-quota 429 with no small Retry-After still let this
                # loop's own 2s/4s backoff run three full attempts before giving up,
                # and any future Retry-After response could be far larger). Backing
                # off *beyond* a few seconds is the circuit breaker's job (its own
                # cooldown_seconds), not a single HTTP call's -- see
                # resilience.CircuitBreaker for the actual multi-request backoff.
                retry_after = resp.headers.get("retry-after") or resp.headers.get("Retry-After")
                if retry_after:
                    try:
                        time.sleep(min(float(retry_after), 5.0) * (0.75 + random.random() * 0.5))
                    except ValueError:
                        pass
                last_exc = EtsyAPIError(resp.status_code, _error_message(resp))
                continue  # retry with backoff

            # Non-retryable HTTP error (including 4xx auth errors other than 401)
            raise EtsyAPIError(resp.status_code, _error_message(resp))

        # All attempts exhausted
        if isinstance(last_exc, EtsyAPIError):
            raise last_exc
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

    def send_message(self, conversation_id: int, message: str) -> dict:
        """Send a reply to a conversation. Requires OAuth access token."""
        self._require_oauth()
        return self._request(
            "POST",
            f"shops/{self.shop_id}/conversations/{conversation_id}/messages",
            body={"message": message},
        )

    def create_listing(self, listing_data: dict) -> dict:
        """Create a new listing. Requires OAuth access token.

        Automatically runs pre_publish_gate before any API call — raises EtsyAPIError(400)
        if any quality check fails. This cannot be bypassed.
        Also enforces required Etsy fields and injects AI disclosure
        (mandatory since June 10, 2025 for AI-assisted listings).
        """
        self._require_oauth()
        failures = EtsyAPIClient.pre_publish_gate(listing_data)
        if failures:
            msg = "Quality gate FAILED — listing not published:\n" + "\n".join(f"  ✗ {f}" for f in failures)
            raise EtsyAPIError(400, msg)
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

        Automatically called by create_listing() — any failures raise EtsyAPIError(400).
        Enforces OnBrandCraftz 2026 algorithm standards from CLAUDE.md.
        """
        import re as _re
        failures = []
        title = listing_data.get("title", "")
        desc  = listing_data.get("description", "")
        tags  = listing_data.get("tags", [])
        price = listing_data.get("price", 0)

        # ── Title ──────────────────────────────────────────────────────────────
        if not title:
            failures.append("TITLE: missing")
        elif len(title) > 70:
            failures.append(
                f"TITLE: {len(title)}/70 chars — Etsy 2026 algorithm penalizes titles >70 chars "
                f"on mobile (70%+ of traffic). Shorten to ≤70."
            )
        if title and len(title) < 30:
            failures.append("TITLE: under 30 chars — too few keywords, Etsy won't rank this")
        if title and "instant download" not in title.lower():
            failures.append("TITLE: missing 'Instant Download' — required phrase for digital products")

        # ── Tags ───────────────────────────────────────────────────────────────
        if len(tags) < 13:
            failures.append(f"TAGS: only {len(tags)}/13 — every empty slot is a missed ranking opportunity")
        elif len(tags) > 13:
            failures.append(f"TAGS: {len(tags)} tags provided — Etsy accepts exactly 13, remove extras")

        _SPECIAL = _re.compile(r"[,;!?@#$%^&*()\[\]{}'\"<>/\\|=+]")
        title_lower = title.lower()
        for tag in tags:
            tag = tag.strip()
            if len(tag) > 20:
                failures.append(f"TAGS: '{tag}' is {len(tag)} chars (max 20)")
            if _SPECIAL.search(tag):
                failures.append(f"TAGS: '{tag}' contains special characters — Etsy rejects these")
            # Tag must not duplicate a phrase already in the title (wastes a ranking slot)
            if len(tag.split()) >= 2 and tag.lower() in title_lower:
                failures.append(
                    f"TAGS: '{tag}' duplicates a title phrase — wasted slot. "
                    f"Use a phrase NOT in your title to cover more search queries."
                )

        # ── Description ────────────────────────────────────────────────────────
        if not desc:
            failures.append("DESC: missing description")
        elif len(desc) < 300:
            failures.append(f"DESC: {len(desc)} chars — too short (minimum 300). Add what's included, apps, FAQ.")

        # ── Price ──────────────────────────────────────────────────────────────
        price_val = float(price) if isinstance(price, (int, float)) else 0.0
        price_usd = price_val / 100 if price_val > 100 else price_val
        if price_usd and price_usd < 4.99:
            failures.append(f"PRICE: ${price_usd:.2f} is below the $4.99 floor")
        if price_usd > 0:
            cents = round((price_usd * 100) % 100)
            if cents not in (99, 97, 49):
                failures.append(
                    f"PRICE: ${price_usd:.2f} doesn't end in .99/.97/.49 — "
                    f"psychological pricing endings meaningfully improve conversion rate"
                )

        # ── Required Etsy production fields ────────────────────────────────────
        if listing_data.get("who_made", "i_did") not in ("i_did", "collective", "someone_else"):
            failures.append("FIELD: invalid who_made value")
        if listing_data.get("is_supply") is True:
            failures.append("FIELD: is_supply must be False for finished products")

        return failures

    def update_listing(self, listing_id: int | str, updates: dict) -> dict:
        """Update an existing listing. Requires OAuth access token."""
        self._require_oauth()
        return self._request("PATCH", f"shops/{self.shop_id}/listings/{listing_id}", body=updates)

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

    def upload_listing_video(self, listing_id: int | str, video_path: str, rank: int | None = None) -> dict:
        """Upload a marketing video to a listing (Etsy API v3 uploadListingVideo)."""
        self._require_oauth()
        import mimetypes

        with open(video_path, "rb") as f:
            video_data = f.read()

        mime_type = mimetypes.guess_type(video_path)[0] or "video/mp4"
        filename = os.path.basename(video_path)

        boundary = "----FormBoundary" + os.urandom(8).hex()
        body_parts = []
        if rank is not None:
            body_parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="rank"\r\n\r\n{rank}'.encode())
        body_parts.append(
            f'--{boundary}\r\nContent-Disposition: form-data; name="video"; filename="{filename}"\r\nContent-Type: {mime_type}\r\n\r\n'.encode()
            + video_data
        )
        body_parts.append(f'--{boundary}--'.encode())
        body = b'\r\n'.join(body_parts)

        url = f"{BASE_URL}/shops/{self.shop_id}/listings/{listing_id}/videos"
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

    def get_listing_images(self, listing_id: int | str) -> list[dict]:
        """Get all images for a listing. Returns list of image records with listing_image_id."""
        result = self._request("GET", f"listings/{listing_id}/images")
        return result.get("results", [])

    def get_listing_files(self, listing_id: int | str) -> list[dict]:
        """Get all digital files attached to a listing. Requires OAuth access token."""
        self._require_oauth()
        result = self._request("GET", f"shops/{self.shop_id}/listings/{listing_id}/files")
        return result.get("results", [])

    def delete_listing_image(self, listing_id: int | str, listing_image_id: int | str) -> None:
        """Delete a specific image from a listing. Requires OAuth access token."""
        self._require_oauth()
        self._request("DELETE", f"shops/{self.shop_id}/listings/{listing_id}/images/{listing_image_id}")

    # ── Digital file upload ───────────────────────────────────────────────────

    def upload_listing_file(
        self,
        listing_id: int | str,
        file_path: str,
        rank: int = 1,
        expected_ext: str | None = None,
        min_pdf_pages: int = MIN_PDF_PAGES,
        skip_validation: bool = False,
    ) -> dict:
        """Attach a digital file to a listing for instant Etsy download.

        Before uploading, the file passes through validate_digital_file() — a content
        gate that rejects empty, oversized, corrupt, mislabeled, or near-empty files so
        a buyer never downloads the wrong product. It also cross-checks the DP code in
        the filename against dp_listing_map.json: attaching DP1062's ZIP to DP1021's
        listing is blocked (the exact failure that shipped a customer the wrong art).
        Pass skip_validation=True only for a deliberate, reviewed exception.
        """
        if not skip_validation:
            facts = validate_digital_file(file_path, expected_ext=expected_ext,
                                          min_pdf_pages=min_pdf_pages)
            detail = ", ".join(f"{k}={v}" for k, v in facts.items() if k != "path")
            print(f"  ✓ content gate passed: {os.path.basename(file_path)} ({detail})")
            mismatch = _dp_code_listing_mismatch(listing_id, file_path)
            if mismatch:
                raise FileContentError(mismatch)
            # Code-level enforcement of the "never lie to the customer" rule: the
            # listing's own description claims are checked against this file's real,
            # computed facts (page count, file count) rather than resting only on the
            # AI's self-report and manual review (2026-07-08 correction pass). Fails
            # open on a fetch error -- an Etsy API hiccup here shouldn't block an
            # upload the way a genuine content mismatch should.
            try:
                live_description = self.get_listing(listing_id).get("description", "")
            except Exception as exc:
                print(f"  (description count-claim check skipped -- could not fetch listing: {exc})")
            else:
                count_problems = check_description_count_claims(live_description, facts)
                if count_problems:
                    raise FileContentError(
                        "description makes a claim the file doesn't back up:\n"
                        + "\n".join(f"  ✗ {p}" for p in count_problems)
                    )
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
        client_id = os.getenv("ETSY_CLIENT_ID", "").strip()
        refresh_token = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
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
        os.environ["ETSY_ACCESS_TOKEN"] = new_access
        if new_refresh != refresh_token:
            os.environ["ETSY_REFRESH_TOKEN"] = new_refresh

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
            # Track when tokens were issued so health_check can warn before 90-day expiry
            from datetime import date as _d
            today_str = str(_d.today())
            found_date = False
            new_lines2 = []
            for line in new_lines:
                if line.startswith("ETSY_TOKEN_ISSUED_DATE="):
                    new_lines2.append(f"ETSY_TOKEN_ISSUED_DATE={today_str}\n")
                    found_date = True
                else:
                    new_lines2.append(line)
            if not found_date:
                new_lines2.append(f"ETSY_TOKEN_ISSUED_DATE={today_str}\n")
            new_lines = new_lines2

            with open(env_path, "w") as fh:
                fh.writelines(new_lines)
        except Exception:
            # Token is still updated in memory even if file write fails
            pass

        return True

    def get_reviews(self, limit: int = 25, min_created: int | None = None) -> dict:
        """Get shop reviews/feedback. Returns dict with 'results' list and 'count'.

        Each review includes: shop_id, listing_id, transaction_id, buyer_user_id,
        rating (1-5), review (text), create_timestamp, update_timestamp. There is
        no review_id or seller_feedback field in the v3 response — verified
        2026-06-17 against a live response (the API has no review-response
        endpoint either; see create_review_response below).
        """
        self._require_oauth()
        params: dict = {"limit": min(limit, 100)}
        if min_created is not None:
            params["min_created"] = min_created
        return self._request("GET", f"shops/{self.shop_id}/reviews", params=params)

    def get_shop_listings_all(self, state: str = "active", limit: int = 100) -> list[dict]:
        """Fetch all listings for the shop (paginates automatically). Returns list of listing dicts."""
        self._require_oauth()
        results = []
        offset = 0
        while True:
            resp = self._request(
                "GET",
                f"shops/{self.shop_id}/listings",
                params={"state": state, "limit": min(limit, 100), "offset": offset, "includes": "images"},
            )
            batch = resp.get("results", [])
            results.extend(batch)
            if len(batch) < min(limit, 100):
                break
            offset += len(batch)
            if offset >= resp.get("count", 0):
                break
        return results

    def _require_oauth(self) -> None:
        if not self.access_token:
            raise EtsyAPIError(
                401,
                "This action requires OAuth. Run 'python tools/etsy_oauth.py' to authenticate your Etsy account.",
            )


def is_configured() -> bool:
    """Return True if at least an API key is present."""
    return bool(os.getenv("ETSY_API_KEY", ""))

