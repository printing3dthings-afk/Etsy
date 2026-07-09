#!/usr/bin/env python3
"""
HTTP-level integration tests — the request/response layer that, before this file,
had ZERO test coverage. `tests/smoke_test.py` only proves main.py imports without
crashing; `tests/test_quality_gates.py`/`test_resilience.py`/`test_staged_actions.py`
exercise pure functions directly, never through an actual HTTP request. None of the
89+ `@app.*` route handlers or the login/session machinery had ever been driven
end-to-end (2026-07-08 correction pass, following a full-app audit).

This file uses FastAPI's TestClient (backed by httpx, already a pinned dependency)
against the real `app` object -- no live server, no network, no Etsy/Anthropic API
calls. Covers the two highest-risk surfaces identified by the audit:
  1. The login/session flow itself (first-run setup, wrong password, session cookie
     grants access, logout actually revokes it) -- this is the single gate every
     other protected route sits behind.
  2. The todos API (list/add), both because it's a real, simple, representative
     protected route, and because it's the same surface the 2026-07-08
     seed_correction_plan_todos() work landed on -- proves that mechanism end-to-end
     through the real HTTP path, not just the direct db.py call already covered by
     the manual verification during that session.

Uses a throwaway temp SQLite DB (never the real dev DB) and the existing
ENABLE_TEST_LOGIN=true / TEST_LOGIN_USERNAME / TEST_LOGIN_PASSWORD mechanism
main.py already has for exactly this purpose -- no new test-only code path needed.

Run locally:  python tests/test_http_routes.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Must be set BEFORE importing main -- module-level code seeds accounts, reconciles
# tokens, etc. at import time (same constraint documented in smoke_test.py).
_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_http_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "http-route-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "httptest"
os.environ["TEST_LOGIN_PASSWORD"] = "HttpTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

# base_url must be https:// -- the session cookie is set with Secure=True (correct
# production behavior), and httpx's cookie jar (like a real browser) won't reattach a
# Secure cookie to requests made over plain http://, which is TestClient's default.
client = TestClient(server.app, base_url="https://testserver")

_TEST_USER = os.environ["TEST_LOGIN_USERNAME"]
_TEST_PASS = os.environ["TEST_LOGIN_PASSWORD"]

# ── tiny test harness (matches tests/test_quality_gates.py style) ──────────────
_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _login(username: str, password: str) -> "TestClient":
    """Returns a fresh client with the session cookie set on success (or unset on
    failure -- caller checks the response itself)."""
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.post("/login", data={"username": username, "password": password, "next": "/"},
                   follow_redirects=False)
    return c, resp


# ── login / session flow ────────────────────────────────────────────────────────
def test_login_page_loads():
    resp = client.get("/login")
    check(resp.status_code == 200, f"GET /login should return 200, got {resp.status_code}")


def test_login_wrong_password_redirects_with_error_not_a_500():
    c, resp = _login(_TEST_USER, "definitely-the-wrong-password")
    check(resp.status_code in (303, 302), f"wrong password should redirect, got {resp.status_code}")
    check("frank_session" not in c.cookies, "wrong password must not set a session cookie")


def test_login_correct_password_sets_session_cookie():
    c, resp = _login(_TEST_USER, _TEST_PASS)
    check(resp.status_code == 303, f"correct login should redirect (303), got {resp.status_code}")
    check("frank_session" in c.cookies, "correct login must set the session cookie")


def test_protected_route_without_auth_returns_401():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/api/todos")
    check(resp.status_code == 401, f"unauthenticated /api/todos should 401, got {resp.status_code}")


def test_protected_route_with_session_cookie_succeeds():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.get("/api/todos")
    check(resp.status_code == 200, f"authenticated /api/todos should 200, got {resp.status_code}")
    body = resp.json()
    check("todos" in body and isinstance(body["todos"], list),
          f"response should contain a 'todos' list, got: {body}")


def test_protected_route_with_bearer_token_succeeds():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/api/todos", headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"})
    check(resp.status_code == 200, f"Bearer-token auth should 200, got {resp.status_code}")


def test_protected_route_with_wrong_bearer_token_returns_401():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/api/todos", headers={"Authorization": "Bearer not-the-real-token"})
    check(resp.status_code == 401, f"a wrong Bearer token must still 401, got {resp.status_code}")


def test_logout_revokes_session():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    ok = c.get("/api/todos")
    check(ok.status_code == 200, f"session should work before logout, got {ok.status_code}")
    logout_resp = c.post("/logout")
    check(logout_resp.status_code == 200, f"POST /logout should 200, got {logout_resp.status_code}")
    after = c.get("/api/todos")
    check(after.status_code == 401, f"session must be dead after logout, got {after.status_code}")


def test_repeated_failed_logins_eventually_rate_limited():
    # Login lockout exists specifically to stop credential-stuffing (2026-07-08
    # security review, S3 in this session's history) -- prove it actually engages.
    # Uses a throwaway username (the lockout is keyed by the attempted username
    # string, not by whether an account exists) so this doesn't lock out _TEST_USER
    # and break every other test that logs in as it.
    c = TestClient(server.app, base_url="https://testserver")
    last_status = None
    for _ in range(12):
        resp = c.post("/login", data={"username": "rate-limit-probe-user", "password": "wrong-again",
                                       "next": "/"}, follow_redirects=False)
        last_status = resp.status_code
    check(last_status == 429, f"enough failed attempts should eventually 429, got {last_status}")


# ── todos API (also exercises seed_correction_plan_todos() end-to-end) ─────────
def test_seeded_correction_plan_todos_are_reachable_via_api():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.get("/api/todos")
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    texts = [t["text"] for t in resp.json()["todos"]]
    check(any("Correction plan 2026-07-08" in t for t in texts),
          "the seeded correction-plan todos should be visible through the real API, "
          f"got {len(texts)} todos with none matching")
    scott_items = [t for t in resp.json()["todos"] if t["added_by"] == "scott"
                   and "Correction plan" in t["text"]]
    frank_items = [t for t in resp.json()["todos"] if t["added_by"] == "frank"
                   and "Correction plan" in t["text"]]
    check(len(scott_items) >= 1, "at least one Scott-assigned correction-plan todo should exist")
    check(len(frank_items) >= 1, "at least one Frank-assigned correction-plan todo should exist")


def test_add_todo_via_api_then_appears_in_list():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/todos", json={"text": "HTTP integration test marker todo", "added_by": "frank"})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    todo_id = resp.json().get("id")
    check(isinstance(todo_id, int), f"response should include a new integer id, got {resp.json()}")
    listed = c.get("/api/todos").json()["todos"]
    check(any(t["id"] == todo_id and t["text"] == "HTTP integration test marker todo" for t in listed),
          "the newly-added todo should appear in the list")


def test_add_todo_without_text_returns_400():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/todos", json={"text": "   "})
    check(resp.status_code == 400, f"blank text should 400, got {resp.status_code}")


def test_toggle_nonexistent_todo_returns_404():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/todos/999999999/toggle", json={"done": True})
    check(resp.status_code == 404, f"toggling a nonexistent todo should 404, got {resp.status_code}")


# ── health endpoint (unauthenticated by design -- external watchdog hits this) ──
def test_health_endpoint_is_unauthenticated_and_reports_persistence():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/health")
    check(resp.status_code == 200, f"/health should be reachable with no auth, got {resp.status_code}")
    body = resp.json()
    check("persistent" in body, f"/health should report persistence status, got: {body}")


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
        print("HTTP ROUTE TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"HTTP ROUTE TESTS OK — {ran} tests passed (login/session/logout + todos API, "
          f"driven through real HTTP requests, not direct function calls).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
