#!/usr/bin/env python3
"""
Voice-config regression tests — added 2026-07-16 alongside the Settings "Test
Voice" button and the Premium-voice-toggle fail-safe (frank_hud_mockup.py:
testVoicePlayback(), _verifyPremiumVoiceConfigured()). Those frontend features
key off two exact backend contracts:

  1. GET /api/credentials/status returns {"openai": {"api_key": <bool>}, ...} --
     _verifyPremiumVoiceConfigured() reads cred.openai.api_key to decide
     whether to auto-revert the Premium voice toggle.
  2. POST /api/voice/speak with no OPENAI_API_KEY configured returns 503 with
     a detail string containing "OPENAI_API_KEY" -- speakText()'s
     onPremiumNotConfigured hook fires specifically on status === 503, and the
     detail text is what a human would see if this endpoint were hit directly.

This doesn't re-verify real audio playback (that needs a real browser, see
tools/playwright_smoke.py) -- it guards the exact shapes/strings the new
frontend logic silently depends on, so a backend refactor that renames a
field or changes a status code doesn't quietly break the toggle fail-safe
without anything going red.

Same self-contained TestClient-against-the-real-app pattern as
tests/test_security_headers.py (that file's docstring explains why).

Run locally:  python tests/test_voice_config.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_voiceconfig_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "voice-config-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "voiceconfigtest"
os.environ["TEST_LOGIN_PASSWORD"] = "VoiceConfigTest!2026Only"
# This test's whole point is verifying behavior when OPENAI_API_KEY is unset --
# make that explicit and deterministic regardless of the host environment's
# real .env, rather than silently depending on it happening to be unset.
os.environ.pop("OPENAI_API_KEY", None)

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    login_resp = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(login_resp.status_code in (302, 303), f"login should redirect, got {login_resp.status_code}")
    return c


def test_credentials_status_reports_openai_key_as_bool():
    c = _logged_in_client()
    resp = c.get("/api/credentials/status")
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    data = resp.json()
    check("openai" in data, f"response missing 'openai' key entirely: {data}")
    check(isinstance(data.get("openai", {}).get("api_key"), bool),
          f"openai.api_key must be a bool -- _verifyPremiumVoiceConfigured() reads this directly, "
          f"got: {data.get('openai')}")


def test_credentials_status_openai_key_false_when_unset():
    # server.OPENAI_KEY was resolved from the environment at import time, before
    # this test file's os.environ.pop() above -- guard against that module-load
    # ordering silently making this test meaningless.
    check(not server.OPENAI_KEY,
          "server.OPENAI_KEY is truthy even though OPENAI_API_KEY was unset before importing main -- "
          "this test's premise (no key configured) doesn't hold in this run")
    c = _logged_in_client()
    resp = c.get("/api/credentials/status")
    data = resp.json()
    check(data.get("openai", {}).get("api_key") is False,
          f"expected openai.api_key False with no OPENAI_API_KEY configured, got: {data.get('openai')}")


def test_voice_speak_503s_with_openai_api_key_in_detail_when_unconfigured():
    c = _logged_in_client()
    resp = c.post("/api/voice/speak", json={"text": "hello"})
    check(resp.status_code == 503,
          f"expected 503 when OPENAI_API_KEY is unset, got {resp.status_code} (body: {resp.text[:200]!r})")
    detail = resp.json().get("detail", "")
    check("OPENAI_API_KEY" in detail,
          f"speakText()'s onPremiumNotConfigured hook fires on status===503 alone (any reason), but the "
          f"detail text is what a human sees if this endpoint is hit directly -- expected 'OPENAI_API_KEY' "
          f"in the message, got: {detail!r}")


def test_voice_speak_requires_auth():
    # Unauthenticated client, no login.
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.post("/api/voice/speak", json={"text": "hello"})
    check(resp.status_code in (401, 403, 307, 302),
          f"expected an auth failure/redirect for an unauthenticated request, got {resp.status_code}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    try:
        os.unlink(_tmp_db.name)
    except OSError:
        pass
    if _failures:
        print("VOICE CONFIG TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"VOICE CONFIG TESTS OK — {ran} tests passed "
          f"(GET /api/credentials/status openai.api_key shape, POST /api/voice/speak 503 contract).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
