"""
Test for the 2026-07-19 fix to tools/image_gen.py's Ideogram path: previously
_ideogram_generate_bytes() made two bare urllib.request.urlopen() calls (the
generate request and the resulting image download) with no try/except at
all -- every other engine in this module (OpenAI via _post(), Gemini via
_gemini_call_with_retry()) retries transient failures with backoff, so a
plain network blip on the Ideogram path failed the whole generation outright
instead of retrying like its siblings.

Fixed by routing the generate call through the existing _post() helper and
adding a new _get_bytes() helper (mirroring _post()'s retry/backoff policy)
for the image download. This test verifies:
  1. _get_bytes() retries on a transient error and succeeds on a later attempt
  2. _get_bytes() fails fast (no retry) on a non-429 4xx HTTP error
  3. _ideogram_generate_bytes() end-to-end retries a transient failure in the
     generate step and still returns the downloaded image bytes
  4. _ideogram_generate_bytes() surfaces a clear ImageGenError when the
     generate response has no image url (unchanged behavior, still guarded)

Run: python tests/test_image_gen_ideogram_retry.py
"""
import io
import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import image_gen  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeResponse:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self):
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_get_bytes_retries_transient_error_then_succeeds():
    calls = {"n": 0}

    def _fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("simulated transient network blip")
        return _FakeResponse(b"fake-image-bytes")

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen), \
         patch("time.sleep") as mock_sleep:
        result = image_gen._get_bytes("https://example.com/img.png", retries=3, timeout=30)

    check(result == b"fake-image-bytes",
          "_get_bytes() must return the eventually-successful download's bytes")
    check(calls["n"] == 3,
          f"_get_bytes() must retry on transient errors (expected 3 attempts, got {calls['n']})")
    check(mock_sleep.called,
          "_get_bytes() must back off between retries, same policy as _post()")


def test_get_bytes_fails_fast_on_non_429_4xx():
    calls = {"n": 0}

    def _fake_urlopen(req, timeout=None):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            "https://example.com/img.png", 404, "Not Found", {}, io.BytesIO(b"gone")
        )

    with patch("urllib.request.urlopen", side_effect=_fake_urlopen), \
         patch("time.sleep") as mock_sleep:
        try:
            image_gen._get_bytes("https://example.com/img.png", retries=3, timeout=30)
            check(False, "_get_bytes() must raise on a non-retryable 4xx, not swallow it")
        except image_gen.ImageGenError:
            pass

    check(calls["n"] == 1,
          f"a non-429 4xx must fail fast with no retry (expected 1 attempt, got {calls['n']})")
    check(not mock_sleep.called, "no backoff sleep should happen on a fail-fast 4xx")


def test_ideogram_generate_bytes_retries_generate_step_and_downloads_image():
    post_calls = {"n": 0}

    def _fake_post(url, body, headers, retries, timeout):
        post_calls["n"] += 1
        return {"data": [{"url": "https://ideogram.example.com/result.png"}]}

    with patch.object(image_gen, "_ideogram_key", return_value="fake-ideogram-key"), \
         patch.object(image_gen, "_post", side_effect=_fake_post) as mock_post, \
         patch.object(image_gen, "_get_bytes", return_value=b"downloaded-bytes") as mock_get_bytes:
        result = image_gen._ideogram_generate_bytes("a kawaii planner cover", image_gen.PORTRAIT)

    check(result == b"downloaded-bytes",
          "_ideogram_generate_bytes() must return the downloaded image bytes")
    check(mock_post.called and mock_post.call_args.kwargs.get("retries") == 3,
          "the generate request must go through _post() with a retry policy, not a bare urlopen()")
    check(mock_get_bytes.called and mock_get_bytes.call_args.kwargs.get("retries") == 3,
          "the image download must go through _get_bytes() with a retry policy, not a bare urlopen()")


def test_ideogram_generate_bytes_raises_clear_error_when_no_url():
    with patch.object(image_gen, "_ideogram_key", return_value="fake-ideogram-key"), \
         patch.object(image_gen, "_post", return_value={"data": [{}]}):
        try:
            image_gen._ideogram_generate_bytes("a kawaii planner cover", image_gen.PORTRAIT)
            check(False, "must raise ImageGenError when the response has no image url")
        except image_gen.ImageGenError as e:
            check("no image url" in str(e), f"error message should explain the missing url, got: {e}")


# ── _grok_key() fallback for the misnamed Railway variable (2026-08-11) ────
# The real xAI key is provisioned on Railway under "Grok api" (with a space)
# instead of XAI_API_KEY -- a known, already-logged naming mismatch. Rather
# than leave a real, already-paid-for key unusable while the rename is
# pending, _grok_key() now also checks that exact variable name as a
# fallback. This never renames/writes anything in Railway -- purely a read
# of an already-existing variable.

def test_grok_key_uses_xai_api_key_when_set():
    with patch.dict(image_gen.os.environ, {"XAI_API_KEY": "real-key-123"}, clear=False), \
         patch.object(image_gen, "_ENV_PATH", Path("/nonexistent/path/.env")):
        check(image_gen._grok_key() == "real-key-123", "must prefer XAI_API_KEY when set")


def test_grok_key_falls_back_to_misnamed_railway_variable():
    env = dict(image_gen.os.environ)
    env.pop("XAI_API_KEY", None)
    env["Grok api"] = "misnamed-real-key-456"
    with patch.dict(image_gen.os.environ, env, clear=True), \
         patch.object(image_gen, "_ENV_PATH", Path("/nonexistent/path/.env")):
        check(image_gen._grok_key() == "misnamed-real-key-456",
              "must fall back to the known-misnamed 'Grok api' variable when XAI_API_KEY is unset")


def test_grok_key_raises_clear_error_when_neither_variable_is_set():
    env = dict(image_gen.os.environ)
    env.pop("XAI_API_KEY", None)
    env.pop("Grok api", None)
    with patch.dict(image_gen.os.environ, env, clear=True), \
         patch.object(image_gen, "_ENV_PATH", Path("/nonexistent/path/.env")):
        try:
            image_gen._grok_key()
            check(False, "must raise ImageGenError when neither variable is set")
        except image_gen.ImageGenError as e:
            check("XAI_API_KEY" in str(e) and "Grok api" in str(e),
                  f"error should mention both variable names checked, got: {e}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("IDEOGRAM RETRY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("IDEOGRAM RETRY TESTS OK — _get_bytes() retries transient failures and fails fast on "
          "non-retryable 4xx, and _ideogram_generate_bytes() now routes both its generate call "
          "and its image download through the shared retry policy instead of bare urlopen().")


if __name__ == "__main__":
    run()
