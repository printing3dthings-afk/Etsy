"""
Functional audit -- POST /api/core/redeploy (core_redeploy, main.py ~16008).

Scope (per audit brief): this endpoint triggers a REAL Railway redeploy of
the live production service. Per CLAUDE.md's "hard to reverse" principle,
verify it is properly access-gated (owner-only or equivalent) and cannot be
triggered by an unauthenticated or under-privileged (non-owner admin)
caller, and that its failure paths (missing Railway config, Railway API
error, Railway API "no confirm" response) degrade to clean HTTP errors
rather than silently pretending to succeed or crashing.

Zero real network calls are made -- `server._railway_graphql` is mocked at
the narrowest point (it's the shared helper the endpoint itself calls via
`asyncio.to_thread`); the module docstring at the route confirms this is
the only place it talks to Railway's API. No real redeploy is ever
triggered by this test file.

Run: python3 tests/test_functional_audit_core_redeploy.py
"""
import os
import sys
import tempfile
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
from fastapi.testclient import TestClient  # noqa: E402

_failures = []


def check(cond, msg):
    if not cond:
        _failures.append(msg)


def _client(raise_server_exceptions=True):
    return TestClient(
        server.app, base_url="https://testserver",
        raise_server_exceptions=raise_server_exceptions,
    )


def _bearer_headers():
    return {"Authorization": f"Bearer {server.APP_TOKEN}"}


_uid_counter = [0]


def _make_session_cookie_client(role: str) -> TestClient:
    """Creates a real hub_users row with the given role and a real session
    (same _new_session() the /login route uses), returns a TestClient with
    that session cookie set -- the exact browser-auth path _require_owner_
    or_automation() is designed to distinguish between owner and admin."""
    _uid_counter[0] += 1
    username = f"audit_{role}_{_uid_counter[0]}"
    server.db.create_hub_user(username, server._hash_password("irrelevant-pw-123"), role=role)
    sid = server._new_session(username)
    c = _client()
    c.cookies.set(server.SESSION_COOKIE, sid)
    return c


_RAILWAY_ENV = {
    "RAILWAY_API_TOKEN": "fake-railway-token",
    "RAILWAY_ENVIRONMENT_ID": "env-123",
    "RAILWAY_SERVICE_ID": "svc-456",
}


# ── Unauthenticated caller ───────────────────────────────────────────────────

def test_no_credentials_at_all_is_401():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql") as mock_gql:
        c = _client()
        r = c.post("/api/core/redeploy")
        check(r.status_code == 401, f"expected 401 with no credentials, got {r.status_code}: {r.text[:200]}")
        check(mock_gql.call_count == 0, "an unauthenticated request must never reach the Railway API call")


def test_wrong_bearer_token_is_401():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql") as mock_gql:
        c = _client()
        r = c.post("/api/core/redeploy", headers={"Authorization": "Bearer not-the-real-token"})
        check(r.status_code == 401, f"expected 401 with a wrong bearer token, got {r.status_code}: {r.text[:200]}")
        check(mock_gql.call_count == 0, "a request with an invalid token must never reach the Railway API call")


# ── Under-privileged (logged-in, non-owner admin) caller ────────────────────

def test_non_owner_admin_session_is_403():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql") as mock_gql:
        c = _make_session_cookie_client("admin")
        r = c.post("/api/core/redeploy")
        check(r.status_code == 403,
              f"a logged-in non-owner admin must be rejected with 403, got {r.status_code}: {r.text[:200]}")
        check(mock_gql.call_count == 0,
              "an under-privileged admin session must never reach the real Railway API call")


# ── Owner caller -- happy path ───────────────────────────────────────────────

def test_owner_session_can_trigger_redeploy():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql", return_value={"serviceInstanceRedeploy": True}) as mock_gql, \
         patch.object(server.db, "log_activity") as mock_log:
        c = _make_session_cookie_client("owner")
        r = c.post("/api/core/redeploy")
        check(r.status_code == 200, f"expected 200 for an owner session, got {r.status_code}: {r.text[:200]}")
        check(r.json().get("ok") is True, f"expected ok:true in response body, got {r.json()}")
        check(mock_gql.call_count == 1, f"expected exactly one Railway API call, got {mock_gql.call_count}")
        # Confirm the mutation is the real serviceInstanceRedeploy mutation, scoped
        # to this deployment's own environment/service ids -- not a hand-rolled or
        # unscoped call.
        called_mutation, called_vars = mock_gql.call_args[0]
        check("serviceInstanceRedeploy" in called_mutation, "must call the serviceInstanceRedeploy mutation")
        check(called_vars == {"e": "env-123", "s": "svc-456"},
              f"must scope the redeploy to this service's own env/service id, got {called_vars}")
        check(mock_log.call_count == 1, "a successful redeploy must be logged to the activity log")


# ── Automation (bearer-only, no session cookie) caller -- documented path ──
# _require_owner_or_automation's own docstring: "A request with no session
# cookie is treated as the accepted automation path" -- this app has one
# shared APP_SECRET_TOKEN (not per-user credentials), used by CI/relay/mobile,
# never handed to a logged-in non-owner admin through any real app flow
# (confirmed: no route returns APP_TOKEN to a browser session -- grepped).
# Exercising this documented path explicitly rather than assuming it.

def test_bearer_only_automation_call_is_accepted():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql", return_value={"serviceInstanceRedeploy": True}) as mock_gql:
        c = _client()
        r = c.post("/api/core/redeploy", headers=_bearer_headers())
        check(r.status_code == 200,
              f"a bearer-only (no session cookie) call with the real shared secret should be accepted "
              f"as the automation path, got {r.status_code}: {r.text[:200]}")
        check(mock_gql.call_count == 1, "the automation path should still reach the Railway API call")


# ── Failure-path handling (owner-authenticated, so the failure itself is
# under test, not the auth gate) ─────────────────────────────────────────────

def test_missing_railway_config_returns_501_not_crash():
    # Deliberately no RAILWAY_* env vars patched in -- simulates a deployment
    # where these Railway-injected vars aren't present.
    with patch.dict(os.environ, {"RAILWAY_API_TOKEN": "", "RAILWAY_ENVIRONMENT_ID": "", "RAILWAY_SERVICE_ID": ""}), \
         patch.object(server, "_railway_graphql") as mock_gql:
        c = _make_session_cookie_client("owner")
        r = c.post("/api/core/redeploy")
        check(r.status_code == 501,
              f"missing Railway config must return a clean 501, got {r.status_code}: {r.text[:200]}")
        check(mock_gql.call_count == 0, "must not attempt the Railway API call with no config present")


def test_railway_api_exception_returns_502_not_crash():
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql", side_effect=RuntimeError("simulated network failure")):
        c = _make_session_cookie_client("owner")
        r = c.post("/api/core/redeploy")
        check(r.status_code == 502,
              f"a Railway API exception must surface as a clean 502, got {r.status_code}: {r.text[:200]}")
        check("simulated network failure" in r.text,
              f"the 502 detail should be actionable (include the underlying error), got {r.text[:300]}")


def test_railway_no_confirm_returns_502_not_silent_success():
    # Railway's mutation returned a falsy/empty result -- must NOT be reported
    # to the caller as ok:true (a redeploy that Railway never actually
    # confirmed must never look like a success).
    with patch.dict(os.environ, _RAILWAY_ENV), \
         patch.object(server, "_railway_graphql", return_value={"serviceInstanceRedeploy": False}):
        c = _make_session_cookie_client("owner")
        r = c.post("/api/core/redeploy")
        check(r.status_code == 502,
              f"an unconfirmed redeploy must return 502, not a silent success, got {r.status_code}: {r.text[:200]}")


def run():
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
    print("FUNCTIONAL AUDIT TESTS OK -- POST /api/core/redeploy is inaccessible to unauthenticated "
          "and non-owner admin callers, correctly accessible to owner sessions and the documented "
          "bearer-secret automation path, and its failure paths (missing config, Railway API error, "
          "unconfirmed redeploy) all degrade to clean, non-2xx HTTP errors -- no real Railway call ever made.")


if __name__ == "__main__":
    run()
