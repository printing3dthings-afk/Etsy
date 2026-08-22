"""Functional audit: POST /api/core/refresh-etsy-token (core_refresh_etsy_token,
tools/api_server/main.py:15974).

Verifies the two things CLAUDE.md's Etsy-OAuth section says matter most:
  1. On a successful refresh, are BOTH the new access token and the new
     (Etsy-rotated) refresh token durably persisted -- not just left in
     process memory / a best-effort local .env write?
  2. On a failed refresh (e.g. Etsy 401s the refresh call because the
     refresh token itself is dead), does the endpoint surface a clear,
     actionable error instead of failing silently or generically?

No real network call is made anywhere in this file. The Etsy OAuth HTTP
call is mocked at its narrowest point (urllib.request.urlopen inside
tools/etsy_api.py) for the etsy_api-level tests, and the whole
EtsyAPIClient class is mocked for the route-level tests, per the audit's
instructions.
"""
import os
import sys
import json
import tempfile
import asyncio
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import etsy_api  # noqa: E402
from starlette.requests import Request  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_request() -> Request:
    # No cookies -> _get_session_user() returns "" -> treated as the
    # accepted bearer/automation path by _require_owner_or_automation().
    scope = {"type": "http", "method": "POST", "path": "/api/core/refresh-etsy-token",
              "headers": [], "query_string": b""}
    return Request(scope)


# ── Route-level: core_refresh_etsy_token() ──────────────────────────────

def test_success_persists_durably():
    """Regression test for a confirmed 2026-08-13 functional-audit bug: on a
    successful forced refresh, the endpoint used to only update os.environ
    in-memory (plus a best-effort .env write, a no-op on Railway's ephemeral
    filesystem) and never call db.save_etsy_tokens() itself -- durable
    persistence depended entirely on the separate ~60s-interval background
    `_token_sync_loop()` task. Since Etsy invalidates the OLD refresh token
    the instant a rotation succeeds, a restart/redeploy in that window would
    strand the shop on a dead refresh token with nothing durable to recover
    from. Fixed in main.py's core_refresh_etsy_token to call
    db.save_etsy_tokens() immediately, mirroring the sibling
    POST /api/etsy-tokens endpoint's existing pattern.
    """
    # Ensure a clean slate in the durable DB.
    before = server.db.get_etsy_tokens()
    check(before is None, f"expected empty DB before test, got {before!r}")

    NEW_ACCESS = "new-access-token-abc123"
    NEW_REFRESH = "new-rotated-refresh-token-xyz789"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        def refresh_access_token(self):
            # Mirrors exactly what the real etsy_api.EtsyAPIClient.refresh_access_token()
            # does on success: update os.environ in-memory and return True.
            os.environ["ETSY_ACCESS_TOKEN"] = NEW_ACCESS
            os.environ["ETSY_REFRESH_TOKEN"] = NEW_REFRESH
            return True

    with patch.object(server, "EtsyAPIClient", _FakeClient):
        result = asyncio.run(server.core_refresh_etsy_token(_fake_request(), _token="test"))

    check(result.get("ok") is True, f"expected ok=True on successful refresh, got {result!r}")
    check(os.environ.get("ETSY_ACCESS_TOKEN") == NEW_ACCESS,
          "the new access token should be live in os.environ after a successful refresh")
    check(os.environ.get("ETSY_REFRESH_TOKEN") == NEW_REFRESH,
          "the new (rotated) refresh token should be live in os.environ after a successful refresh")

    after = server.db.get_etsy_tokens()
    check(after is not None,
          "the durable DB (db.etsy_tokens) should be populated after a successful forced "
          "refresh -- core_refresh_etsy_token must persist the new rotated token pair itself, "
          "not rely solely on the separate background _token_sync_loop")
    if after is not None:
        check(after.get("access_token") == NEW_ACCESS,
              f"expected the durably-persisted access_token to be the fresh one, got {after.get('access_token')!r}")
        check(after.get("refresh_token") == NEW_REFRESH,
              f"expected the durably-persisted refresh_token to be the fresh (rotated) one, got {after.get('refresh_token')!r}")


def test_success_response_updated_at_reflects_the_fresh_rotation():
    """Direct consequence of the fix above: since the rotation is now
    durably persisted before the endpoint reads it back, the `updated_at`
    field the endpoint returns to the caller genuinely reflects this
    refresh, not None or a stale timestamp from some unrelated prior
    persistence.
    """
    NEW_ACCESS = "another-new-access-token"
    NEW_REFRESH = "another-new-refresh-token"

    class _FakeClient:
        def __init__(self, *a, **kw):
            pass

        def refresh_access_token(self):
            os.environ["ETSY_ACCESS_TOKEN"] = NEW_ACCESS
            os.environ["ETSY_REFRESH_TOKEN"] = NEW_REFRESH
            return True

    with patch.object(server, "EtsyAPIClient", _FakeClient):
        result = asyncio.run(server.core_refresh_etsy_token(_fake_request(), _token="test"))

    check(result.get("ok") is True, f"expected ok=True, got {result!r}")
    check(result.get("updated_at") is not None,
          f"expected updated_at to carry a real fresh timestamp now that the rotation is "
          f"durably persisted before being read back, got {result.get('updated_at')!r}")


def test_failure_raises_actionable_502_not_a_bare_error():
    """When the refresh genuinely fails (e.g. Etsy 401s because the
    refresh token is dead), the route must surface a clear, actionable
    HTTPException per api-conventions.md's error-handling rule -- not a
    bare 500 or a silent pass-through. This part of the function is
    correct: it raises HTTPException(502) with a detail string that
    tells the caller exactly what to do (run tools/etsy_oauth.py)."""

    class _FakeClientFails:
        def __init__(self, *a, **kw):
            pass

        def refresh_access_token(self):
            return False  # mirrors the real function's behavior on any failure, incl. 401

    from fastapi import HTTPException

    with patch.object(server, "EtsyAPIClient", _FakeClientFails):
        try:
            asyncio.run(server.core_refresh_etsy_token(_fake_request(), _token="test"))
            check(False, "expected HTTPException to be raised on refresh failure")
        except HTTPException as exc:
            check(exc.status_code == 502, f"expected 502, got {exc.status_code}")
            detail = str(exc.detail)
            check("etsy_oauth.py" in detail, f"expected actionable remediation in detail, got: {detail!r}")
            check(len(detail) > 20, f"detail message looks too generic/short: {detail!r}")


# ── etsy_api.py layer: the real refresh_access_token(), HTTP call mocked ──

def _with_isolated_env_file(tmp_dir: str):
    """Redirect etsy_api.refresh_access_token()'s hardcoded .env path
    (computed from `__file__`, normally the REAL repo .env) into a throwaway
    temp file, so this test can exercise the function's real file-write
    logic without ever touching the real credentials file. Returns a
    patch.object context manager for etsy_api.__file__."""
    fake_module_file = os.path.join(tmp_dir, "tools", "etsy_api.py")
    return patch.object(etsy_api, "__file__", fake_module_file)


def test_etsy_api_refresh_persists_both_tokens_on_success():
    """The real etsy_api.EtsyAPIClient.refresh_access_token(), with the
    Etsy OAuth HTTP call mocked entirely. Confirms it correctly persists
    BOTH the new access token and the new (rotated) refresh token to
    os.environ and to its local .env file -- the two things the audit
    target asks about at the etsy_api layer itself."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.environ["ETSY_CLIENT_ID"] = "test-client-id"
        os.environ["ETSY_REFRESH_TOKEN"] = "old-refresh-token"
        os.environ.pop("ETSY_ACCESS_TOKEN", None)

        fake_resp = MagicMock()
        fake_resp.read.return_value = json.dumps({
            "access_token": "fresh-access-token",
            "refresh_token": "fresh-rotated-refresh-token",
        }).encode()
        fake_cm = MagicMock()
        fake_cm.__enter__.return_value = fake_resp
        fake_cm.__exit__.return_value = False

        with _with_isolated_env_file(tmp_dir), \
             patch.object(etsy_api.urllib.request, "urlopen", return_value=fake_cm) as mock_urlopen:
            client = etsy_api.EtsyAPIClient(api_key="unused")
            ok = client.refresh_access_token()

        check(ok is True, "refresh_access_token() should return True on a clean success response")
        check(mock_urlopen.called, "expected the mocked urlopen to have been invoked (no real network call)")
        check(os.environ.get("ETSY_ACCESS_TOKEN") == "fresh-access-token",
              f"new access token not written to os.environ: {os.environ.get('ETSY_ACCESS_TOKEN')!r}")
        check(os.environ.get("ETSY_REFRESH_TOKEN") == "fresh-rotated-refresh-token",
              f"new rotated refresh token not written to os.environ: {os.environ.get('ETSY_REFRESH_TOKEN')!r}")
        check(client.access_token == "fresh-access-token",
              "in-memory client.access_token should also reflect the new token")

        env_path = os.path.join(tmp_dir, ".env")
        check(os.path.exists(env_path), "expected the (isolated, throwaway) .env file to have been written")
        if os.path.exists(env_path):
            with open(env_path) as fh:
                contents = fh.read()
            check("ETSY_ACCESS_TOKEN=fresh-access-token" in contents,
                  f"access token missing from persisted .env contents:\n{contents}")
            check("ETSY_REFRESH_TOKEN=fresh-rotated-refresh-token" in contents,
                  f"rotated refresh token missing from persisted .env contents:\n{contents}")


def test_etsy_api_refresh_returns_false_cleanly_on_401():
    """A 401 (e.g. invalid_grant because the refresh token already
    expired/was already rotated away) must not crash the caller with an
    unhandled exception -- it should come back as a clean `False`, exactly
    like any other failure, so the route layer's `if not ok: raise
    HTTPException(...)` handling (already verified above) can produce its
    actionable error message. This documents that the function's failure
    handling is a broad catch-all (does not distinguish 401/invalid_grant
    from a network timeout) -- both collapse to the same generic `False`
    and thus the same generic remediation message from the route."""
    os.environ["ETSY_CLIENT_ID"] = "test-client-id"
    os.environ["ETSY_REFRESH_TOKEN"] = "dead-refresh-token"

    http_error = urllib.error.HTTPError(
        url="https://api.etsy.com/v3/public/oauth/token",
        code=401,
        msg="invalid_grant",
        hdrs=None,
        fp=None,
    )

    with tempfile.TemporaryDirectory() as tmp_dir, \
         _with_isolated_env_file(tmp_dir), \
         patch.object(etsy_api.urllib.request, "urlopen", side_effect=http_error):
        client = etsy_api.EtsyAPIClient(api_key="unused")
        try:
            ok = client.refresh_access_token()
        except Exception as exc:
            check(False, f"refresh_access_token() must not raise on a 401 -- it raised {exc!r}")
            ok = None

    check(ok is False, f"expected refresh_access_token() to return False on a 401, got {ok!r}")


def test_etsy_api_refresh_missing_client_id_or_refresh_token_short_circuits():
    """Sanity check on the guard clause: with no client_id/refresh_token
    configured at all, the function must not attempt any HTTP call and
    must return False immediately."""
    saved_cid = os.environ.pop("ETSY_CLIENT_ID", None)
    saved_rt = os.environ.pop("ETSY_REFRESH_TOKEN", None)
    try:
        with patch.object(etsy_api.urllib.request, "urlopen") as mock_urlopen:
            client = etsy_api.EtsyAPIClient(api_key="")
            ok = client.refresh_access_token()
        check(ok is False, f"expected False with no client_id/refresh_token, got {ok!r}")
        check(not mock_urlopen.called, "should not attempt an HTTP call with no credentials configured")
    finally:
        if saved_cid is not None:
            os.environ["ETSY_CLIENT_ID"] = saved_cid
        if saved_rt is not None:
            os.environ["ETSY_REFRESH_TOKEN"] = saved_rt


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT TESTS OK -- core_refresh_etsy_token's 401 handling is clear and "
          "actionable, and a successful forced refresh now durably persists the newly rotated "
          "tokens to db.etsy_tokens immediately, same as its sibling POST /api/etsy-tokens.")


if __name__ == "__main__":
    run()
