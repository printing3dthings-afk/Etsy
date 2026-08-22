#!/usr/bin/env python3
"""
Security-header regression tests — added 2026-07-10 after a real incident: the
Content-Security-Policy header shipped on 2026-07-08 (a security-hardening pass) had
no `media-src` directive, so it fell back to `default-src 'self'`, which does not
cover `blob:`/`data:` URLs. Every TTS voice reply plays audio via
`URL.createObjectURL(blob)` -- a blob: URL -- so this silently broke ALL voice output
in every browser, for every user, for about two days, with zero test coverage
catching it. CI stayed green the entire time (py_compile/node --check/the full
existing pytest suite all pass regardless of HTTP response headers) because nothing
in the test suite had ever asserted on a response header before this file.

This is a direct regression test for that exact bug class: it doesn't re-verify TTS
playback (that needs a real browser, see tools/playwright_smoke.py), it verifies the
one thing a bug like this always breaks first -- the header itself being present and
containing the schemes browsers actually require for blob:/data: media.

Same TestClient-against-the-real-app pattern as tests/test_http_routes.py (that
file's docstring explains why: FastAPI's TestClient, no live server, no network).
Deliberately NOT importing shared setup from that file -- every test file in this
repo is self-contained on purpose so `python tests/test_X.py` works standalone in
CI without file-ordering assumptions.

Run locally:  python tests/test_security_headers.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_secheaders_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "sec-headers-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "secheaderstest"
os.environ["TEST_LOGIN_PASSWORD"] = "SecHeadersTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(server.app, base_url="https://testserver")

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _parse_csp(value: str) -> dict[str, list[str]]:
    """Same parsing a browser does: split on ';', first token of each directive is
    its name, the rest are its sources."""
    directives: dict[str, list[str]] = {}
    for part in value.split(";"):
        tokens = part.strip().split()
        if not tokens:
            continue
        directives[tokens[0]] = tokens[1:]
    return directives


# ── the exact bug: media-src must exist and cover blob:/data: ──────────────────
def test_csp_header_present_on_unauthenticated_route():
    # /login is reachable pre-auth -- if the header were only set on authenticated
    # responses, an attacker's first (unauthenticated) request would be unprotected.
    resp = client.get("/login")
    check("content-security-policy" in resp.headers, "CSP header missing entirely from /login response")


def test_csp_media_src_covers_blob_and_data():
    resp = client.get("/login")
    csp = resp.headers.get("content-security-policy", "")
    directives = _parse_csp(csp)
    check("media-src" in directives, f"CSP has no media-src directive at all (full header: {csp!r})")
    sources = directives.get("media-src", [])
    check("blob:" in sources, f"media-src does not include blob: -- every TTS reply plays via "
                               f"URL.createObjectURL(blob), so this silently breaks all voice output "
                               f"(media-src sources: {sources})")
    check("data:" in sources, f"media-src does not include data: -- the audio-unlock trick in "
                               f"_primeAudioPlayback() uses a data: URI <audio> element "
                               f"(media-src sources: {sources})")


def test_csp_present_on_authenticated_frank_route():
    c = TestClient(server.app, base_url="https://testserver")
    login_resp = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(login_resp.status_code in (302, 303), f"login should redirect, got {login_resp.status_code}")
    resp = c.get("/frank")
    check(resp.status_code == 200, f"/frank should be reachable after login, got {resp.status_code}")
    check("content-security-policy" in resp.headers, "CSP header missing from authenticated /frank response")
    directives = _parse_csp(resp.headers.get("content-security-policy", ""))
    check("blob:" in directives.get("media-src", []),
          "media-src on the authenticated dashboard page (where TTS actually plays) does not include blob:")


# ── other headers this same middleware sets -- cheap to guard now that we're here ──
def test_other_security_headers_still_present():
    resp = client.get("/login")
    check(resp.headers.get("x-content-type-options") == "nosniff",
          f"X-Content-Type-Options missing/wrong, got {resp.headers.get('x-content-type-options')!r}")
    check(resp.headers.get("x-frame-options") == "DENY",
          f"X-Frame-Options missing/wrong, got {resp.headers.get('x-frame-options')!r}")
    check("strict-transport-security" in resp.headers, "Strict-Transport-Security header missing")


# ── runner ────────────────────────────────────────────────────────────────────
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
        print("SECURITY HEADER TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"SECURITY HEADER TESTS OK — {ran} tests passed "
          f"(CSP media-src covers blob:/data:, other headers present).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
