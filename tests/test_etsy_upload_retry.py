#!/usr/bin/env python3
"""
Tests for the 2026-07-21 fix adding retry/backoff to EtsyAPIClient's three raw
multipart upload calls: upload_listing_image(), upload_listing_video(), and
upload_listing_file().

Before this fix, all three built a multipart body with urllib.request and
called urlopen() exactly ONCE -- unlike every JSON API call in this client
(_request_impl: 3-attempt exponential backoff, retries 429/503, honors a
capped Retry-After), a single transient network blip or an ordinary Etsy
429/503 failed the whole upload outright. These uploads put the actual
product photos/video/digital file live on a listing, so they deserve the
same resilience as a routine GET.

Fix: all three now route through a shared _upload_multipart_with_retry()
helper mirroring _request_impl's policy.

Checks:
  1. A transient network error (URLError) is retried and the call succeeds
     on a later attempt, for all three upload methods.
  2. A 503 HTTP error is retried and succeeds on a later attempt.
  3. A non-retryable 4xx (e.g. 400) fails fast with no retry.
  4. Retries are exhausted and the original error surfaces after all
     attempts fail.

Run: python tests/test_etsy_upload_retry.py
"""
import io
import json
import sys
import tempfile
import time
import traceback
import urllib.error
import urllib.request
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import etsy_api  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _make_client() -> "etsy_api.EtsyAPIClient":
    c = etsy_api.EtsyAPIClient(api_key="test-key", access_token="fake-token")
    c.client_id = "test-client-id"
    c.client_secret = "test-client-secret"
    c.shop_id = "12345"
    return c


class _FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode()

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def _tmp_image() -> str:
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\nfakeimagebytes")
        return f.name


def _http_error(code: int, body: bytes = b'{"error": "boom"}') -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.com", code, "err", {}, io.BytesIO(body))


def test_upload_listing_image_retries_network_error_then_succeeds():
    client = _make_client()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.URLError("simulated transient network blip")
        return _FakeResponse({"listing_image_id": 999, "rank": 1})

    with mock.patch.object(urllib.request, "urlopen", fake_urlopen), \
         mock.patch("time.sleep"):
        result = client.upload_listing_image(4512345678, _tmp_image(), rank=1)

    check(result.get("listing_image_id") == 999, f"expected success after retries, got: {result}")
    check(calls["n"] == 3, f"expected 3 attempts (2 failures + 1 success), got {calls['n']}")


def test_upload_listing_video_retries_503_then_succeeds():
    client = _make_client()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise _http_error(503)
        return _FakeResponse({"listing_video_id": 42})

    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        f.write(b"fakevideobytes")
        video_path = f.name

    with mock.patch.object(urllib.request, "urlopen", fake_urlopen), \
         mock.patch("time.sleep"):
        result = client.upload_listing_video(4512345678, video_path)

    check(result.get("listing_video_id") == 42, f"expected success after a 503 retry, got: {result}")
    check(calls["n"] == 2, f"expected 2 attempts (1 failure + 1 success), got {calls['n']}")


def test_upload_listing_file_retries_429_then_succeeds():
    client = _make_client()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 2:
            raise _http_error(429)
        return _FakeResponse({"listing_file_id": 7})

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
        f.write(b"%PDF-1.4\nfakepdfbytes")
        file_path = f.name

    with mock.patch.object(urllib.request, "urlopen", fake_urlopen), \
         mock.patch("time.sleep"):
        result = client.upload_listing_file(4512345678, file_path, skip_validation=True)

    check(result.get("listing_file_id") == 7, f"expected success after a 429 retry, got: {result}")
    check(calls["n"] == 2, f"expected 2 attempts (1 failure + 1 success), got {calls['n']}")


def test_upload_fails_fast_on_non_retryable_4xx():
    client = _make_client()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise _http_error(400, b'{"error": "bad request"}')

    with mock.patch.object(urllib.request, "urlopen", fake_urlopen), \
         mock.patch("time.sleep") as mock_sleep:
        try:
            client.upload_listing_image(4512345678, _tmp_image(), rank=1)
            check(False, "a non-retryable 4xx must raise, not swallow the error")
        except etsy_api.EtsyAPIError as e:
            check(e.status == 400, f"expected status 400 to surface, got {e.status}")

    check(calls["n"] == 1, f"a non-retryable 4xx must fail fast with exactly 1 attempt, got {calls['n']}")
    check(not mock_sleep.called, "no backoff sleep should happen on a fail-fast 4xx")


def test_upload_exhausts_retries_and_raises_last_error():
    client = _make_client()
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise _http_error(503)

    with mock.patch.object(urllib.request, "urlopen", fake_urlopen), \
         mock.patch("time.sleep"):
        try:
            client.upload_listing_image(4512345678, _tmp_image(), rank=1)
            check(False, "must raise once all retry attempts are exhausted")
        except etsy_api.EtsyAPIError as e:
            check(e.status == 503, f"expected the last 503 to surface, got {e.status}")

    check(calls["n"] == 3, f"expected exactly 3 attempts (the default retries=3), got {calls['n']}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("ETSY UPLOAD RETRY TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"ETSY UPLOAD RETRY TESTS OK — {ran} tests passed (upload_listing_image/video/file now "
          f"retry transient network errors and 429/503 with backoff, fail fast on other 4xx, and "
          f"raise the last error once retries are exhausted -- no live Etsy call).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
