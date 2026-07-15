#!/usr/bin/env python3
"""
Fixture test for tools/etsy_api.py's EtsyAPIClient.upload_listing_image()
alt_text support (2026-07-15 ADA/WCAG audit fix) -- Etsy listing photos
previously carried zero screen-reader description. Confirms the multipart
body includes an alt_text form field when provided, and omits it (same
request shape as before the fix) when not -- without a real network call:
urllib.request.urlopen is monkeypatched to capture the outgoing Request
instead of sending it.

Run locally:  python tests/test_etsy_api_alt_text.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import io
import json
import sys
import tempfile
import traceback
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


def _capture_request_body(monkeypatch_target, response_payload=None):
    """Patches urllib.request.urlopen to capture the Request it was given
    instead of hitting the network, returning it as raw bytes."""
    captured = {}

    def fake_urlopen(req, timeout=None):
        captured["body"] = req.data
        captured["headers"] = dict(req.headers)
        return _FakeResponse(response_payload or {"listing_image_id": 999, "rank": 1})

    return captured, fake_urlopen


def test_alt_text_included_when_provided():
    client = _make_client()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\nfakeimagebytes")
        img_path = f.name
    captured, fake_urlopen = _capture_request_body(None)
    with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
        client.upload_listing_image(4512345678, img_path, rank=2, alt_text="Cozy desk hero photo")
    body = captured["body"]
    check(b'name="alt_text"' in body, f"alt_text form field missing from multipart body: {body[:400]!r}")
    check(b"Cozy desk hero photo" in body, f"alt_text value not found in body: {body[:400]!r}")
    check(b'name="rank"' in body, "rank field should still be present alongside alt_text")


def test_alt_text_omitted_when_not_provided():
    client = _make_client()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\nfakeimagebytes")
        img_path = f.name
    captured, fake_urlopen = _capture_request_body(None)
    with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
        client.upload_listing_image(4512345678, img_path, rank=1)
    body = captured["body"]
    check(b'name="alt_text"' not in body,
          f"alt_text field should be absent when not passed (backward-compat), got: {body[:400]!r}")


def test_alt_text_truncated_to_500_chars():
    client = _make_client()
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
        f.write(b"\x89PNG\r\n\x1a\nfakeimagebytes")
        img_path = f.name
    long_alt = "A" * 900
    captured, fake_urlopen = _capture_request_body(None)
    with mock.patch.object(urllib.request, "urlopen", fake_urlopen):
        client.upload_listing_image(4512345678, img_path, rank=1, alt_text=long_alt)
    body = captured["body"]
    check(b"A" * 500 in body, "truncated alt_text (500 chars) should be present")
    check(b"A" * 501 not in body, f"alt_text should be truncated to Etsy's 500-char max, got longer: {len(body)}")


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
        print("ETSY API ALT-TEXT TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"ETSY API ALT-TEXT TESTS OK — {ran} tests passed "
          f"(upload_listing_image()'s alt_text plumbing, no live Etsy call).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
