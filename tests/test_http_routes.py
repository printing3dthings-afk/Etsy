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


def test_toggle_todo_marks_done_then_undone():
    # 2026-07-09: the compliance-sweep work relies on todos as its review-queue
    # UI (WARN/FAIL findings become todos Scott checks off), so the toggle route
    # itself -- previously only covered by the 404 case above -- needs a
    # positive-path test proving it actually flips `done` both ways.
    c, _ = _login(_TEST_USER, _TEST_PASS)
    add_resp = c.post("/api/todos", json={"text": "toggle test marker todo", "added_by": "frank"})
    todo_id = add_resp.json()["id"]

    done_resp = c.post(f"/api/todos/{todo_id}/toggle", json={"done": True})
    check(done_resp.status_code == 200, f"toggle to done should 200, got {done_resp.status_code}")
    listed = c.get("/api/todos").json()["todos"]
    row = next((t for t in listed if t["id"] == todo_id), None)
    check(row is not None and bool(row["done"]) is True, f"todo should be done=True after toggle, got {row}")

    undone_resp = c.post(f"/api/todos/{todo_id}/toggle", json={"done": False})
    check(undone_resp.status_code == 200, f"toggle to not-done should 200, got {undone_resp.status_code}")
    listed = c.get("/api/todos").json()["todos"]
    row = next((t for t in listed if t["id"] == todo_id), None)
    check(row is not None and bool(row["done"]) is False, f"todo should be done=False after second toggle, got {row}")


# ── staged-action queue (the actual Etsy/TikTok/local write path) ──────────────
# Found in the 2026-07-09 weakness audit: ~90 HTTP routes exist but only ~7 were
# ever exercised via real HTTP (login/session/todos above). The single highest-risk
# gap was /api/queue/{id}/approve|reject -- the route that actually executes staged
# mutations -- which only had direct-function-call coverage (test_staged_actions.py
# calls _validate_staged_action() directly, never through HTTP + auth + the real
# approve/reject dispatch). These two tests close that gap using local_write_file
# (monkeypatching db.is_path_allowed + _dispatch_to_relay the same way
# test_staged_actions.py already does, so no live relay connection or real Etsy/
# TikTok call is needed) to prove: approve actually reaches execution and reject
# never does.
def test_queue_approve_executes_local_write_file_action():
    original_allowed = server.db.is_path_allowed
    original_dispatch = server._dispatch_to_relay
    calls = []

    async def _fake_dispatch(name, tool_input, timeout=15.0):
        calls.append((name, tool_input))
        return {"ok": True}

    server.db.is_path_allowed = lambda path: True
    server._dispatch_to_relay = _fake_dispatch
    try:
        action_id = server.db.enqueue_action(
            "local_write_file",
            "HTTP integration test write",
            {"path": "/data/workspace/http_test_marker.txt", "after": "hello from http test"},
        )
        c, _ = _login(_TEST_USER, _TEST_PASS)
        resp = c.post(f"/api/queue/{action_id}/approve")
        check(resp.status_code == 200, f"approve should 200, got {resp.status_code}: {resp.text}")
        check(resp.json().get("status") == "executed",
              f"approve response should report executed, got {resp.json()}")
        check(len(calls) == 1, f"approving should dispatch exactly once, got {len(calls)} calls")
        if calls:
            check(calls[0] == ("local_write_file",
                                {"path": "/data/workspace/http_test_marker.txt", "content": "hello from http test"}),
                  f"dispatch should carry the staged path/content through (payload's 'after' -> relay's "
                  f"'content'), got {calls[0]}")
        stored = server.db.get_action(action_id)
        check(stored["status"] == "executed", f"DB row should be 'executed', got {stored['status']}")
    finally:
        server.db.is_path_allowed = original_allowed
        server._dispatch_to_relay = original_dispatch


def test_queue_reject_never_executes():
    original_allowed = server.db.is_path_allowed
    original_dispatch = server._dispatch_to_relay
    calls = []

    async def _fake_dispatch(name, tool_input, timeout=15.0):
        calls.append((name, tool_input))
        return {"ok": True}

    server.db.is_path_allowed = lambda path: True
    server._dispatch_to_relay = _fake_dispatch
    try:
        action_id = server.db.enqueue_action(
            "local_write_file",
            "HTTP integration test write (should be rejected)",
            {"path": "/data/workspace/http_test_marker_rejected.txt", "after": "should never be written"},
        )
        c, _ = _login(_TEST_USER, _TEST_PASS)
        resp = c.post(f"/api/queue/{action_id}/reject")
        check(resp.status_code == 200, f"reject should 200, got {resp.status_code}: {resp.text}")
        check(resp.json().get("status") == "rejected",
              f"reject response should report rejected, got {resp.json()}")
        check(len(calls) == 0, f"rejecting must never dispatch, got {len(calls)} call(s)")
        stored = server.db.get_action(action_id)
        check(stored["status"] == "rejected", f"DB row should be 'rejected', got {stored['status']}")
    finally:
        server.db.is_path_allowed = original_allowed
        server._dispatch_to_relay = original_dispatch


def test_queue_approve_nonexistent_action_returns_404():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/queue/999999999/approve")
    check(resp.status_code == 404, f"approving a nonexistent action should 404, got {resp.status_code}")


class _FakeEtsyClient:
    """Stand-in for EtsyAPIClient used by both _validate_staged_action's
    at_approval re-fetch and _execute_staged_action's actual mutation call --
    no real Etsy credentials or network access needed. Records every
    update_listing() call so the test can assert exactly one deactivation
    happened with the right listing_id/state."""
    calls: list = []
    live_state = "active"

    def __init__(self, *a, **kw):
        pass

    def get_listing(self, listing_id):
        return {"listing_id": listing_id, "state": _FakeEtsyClient.live_state}

    def update_listing(self, listing_id, fields):
        _FakeEtsyClient.calls.append((listing_id, dict(fields)))
        return {"listing_id": listing_id, "state": fields.get("state"), "title": "Fake Listing"}


def test_queue_approve_executes_deactivate_listing_action():
    # 2026-07-09: the listing-compliance-sweep work (tools/listing_compliance_sweep.py)
    # stages `deactivate_listing` for every FAIL finding -- this is the one Etsy-write
    # staged-action type that previously had zero HTTP-level coverage (only
    # local_write_file was exercised above). Proves the full path: stage -> approve ->
    # _execute_staged_action -> EtsyAPIClient().update_listing(lid, {"state": "inactive"}).
    original_client = server.EtsyAPIClient
    _FakeEtsyClient.calls = []
    _FakeEtsyClient.live_state = "active"
    server.EtsyAPIClient = _FakeEtsyClient
    try:
        action_id = server.db.enqueue_action(
            "deactivate_listing",
            "HTTP integration test — compliance FAIL takedown",
            {"listing_id": 4520524435, "_state_at_staging": "active"},
        )
        c, _ = _login(_TEST_USER, _TEST_PASS)
        resp = c.post(f"/api/queue/{action_id}/approve")
        check(resp.status_code == 200, f"approve should 200, got {resp.status_code}: {resp.text}")
        check(resp.json().get("status") == "executed",
              f"approve response should report executed, got {resp.json()}")
        check(_FakeEtsyClient.calls == [(4520524435, {"state": "inactive"})],
              f"exactly one update_listing(lid, state=inactive) call expected, got {_FakeEtsyClient.calls}")
        stored = server.db.get_action(action_id)
        check(stored["status"] == "executed", f"DB row should be 'executed', got {stored['status']}")
    finally:
        server.EtsyAPIClient = original_client


def test_queue_approve_deactivate_listing_blocked_if_state_changed_since_staging():
    # The freshness re-check in _validate_staged_action(at_approval=True) is the
    # safety net for "Scott already handled this manually between staging and
    # approval" -- prove a live state mismatch actually blocks the deactivation
    # rather than silently applying a stale decision.
    original_client = server.EtsyAPIClient
    _FakeEtsyClient.calls = []
    _FakeEtsyClient.live_state = "inactive"  # changed since staging
    server.EtsyAPIClient = _FakeEtsyClient
    try:
        action_id = server.db.enqueue_action(
            "deactivate_listing",
            "HTTP integration test — stale takedown, listing already inactive",
            {"listing_id": 4520524436, "_state_at_staging": "active"},
        )
        c, _ = _login(_TEST_USER, _TEST_PASS)
        resp = c.post(f"/api/queue/{action_id}/approve")
        check(resp.status_code in (400, 409, 422),
              f"approving a stale takedown should be refused, got {resp.status_code}: {resp.text}")
        check(_FakeEtsyClient.calls == [], f"a blocked approval must never call update_listing, got {_FakeEtsyClient.calls}")
    finally:
        server.EtsyAPIClient = original_client


def test_queue_approve_already_executed_action_returns_409():
    original_allowed = server.db.is_path_allowed
    original_dispatch = server._dispatch_to_relay
    server.db.is_path_allowed = lambda path: True

    async def _fake_dispatch(name, tool_input, timeout=15.0):
        return {"ok": True}

    server._dispatch_to_relay = _fake_dispatch
    try:
        action_id = server.db.enqueue_action(
            "local_write_file", "double-approve probe",
            {"path": "/data/workspace/http_test_double_approve.txt", "after": "x"},
        )
        c, _ = _login(_TEST_USER, _TEST_PASS)
        first = c.post(f"/api/queue/{action_id}/approve")
        check(first.status_code == 200, f"first approve should 200, got {first.status_code}")
        second = c.post(f"/api/queue/{action_id}/approve")
        check(second.status_code == 409, f"re-approving an executed action should 409, got {second.status_code}")
    finally:
        server.db.is_path_allowed = original_allowed
        server._dispatch_to_relay = original_dispatch


# ── API Costs (Settings -> API Costs card, 2026-07-09) ──────────────────────────
def test_api_costs_reports_all_four_services_honestly():
    # No RAILWAY_PROJECT_ID in this test env, so Railway itself should come back
    # unavailable too -- proves the endpoint never fabricates a number for a
    # service it can't actually reach, matching the CARDINAL CHECK ethos applied
    # to Frank's own dashboard, not just customer-facing listings.
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.get("/api/system/costs")
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    body = resp.json()
    services = body.get("services", {})
    for svc in ("railway", "anthropic", "openai", "gemini"):
        check(svc in services, f"expected '{svc}' in services, got {list(services.keys())}")
        check("available" in services[svc], f"{svc} entry should report availability, got {services[svc]}")
        if not services[svc]["available"]:
            check(bool(services[svc].get("reason")), f"{svc} unavailable but has no reason: {services[svc]}")
        # Every service must carry a real top-up/billing deep link -- the "Top Up"
        # button in Settings needs somewhere to send Scott even when Frank can't
        # read the live cost figure for that service yet.
        check(bool(services[svc].get("dashboard_url")), f"{svc} missing dashboard_url: {services[svc]}")
    check("budget_caps" in body, f"expected budget_caps in response, got {body}")


def test_api_costs_requires_auth():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/api/system/costs")
    check(resp.status_code == 401, f"unauthenticated /api/system/costs should 401, got {resp.status_code}")


def test_budget_caps_save_and_reflect_in_costs():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/system/costs/budget-caps", json={"railway": 25, "anthropic": None})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}")
    saved = resp.json().get("saved", {})
    check(saved.get("railway") == 25.0, f"expected railway cap 25.0, got {saved}")
    check(saved.get("anthropic") is None, f"expected anthropic cap cleared, got {saved}")

    costs = c.get("/api/system/costs").json()
    check(costs["budget_caps"].get("railway") == 25.0,
          f"saved cap should be reflected on next GET, got {costs['budget_caps']}")


def test_budget_caps_rejects_non_numeric_value():
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/system/costs/budget-caps", json={"railway": "not-a-number"})
    check(resp.status_code == 400, f"non-numeric cap should 400, got {resp.status_code}")


def test_budget_caps_rejects_unknown_service_silently_ignored():
    # Unknown keys are dropped, not errored -- matches the tolerant body-parsing
    # style already used elsewhere (e.g. post_todo's added_by fallback).
    c, _ = _login(_TEST_USER, _TEST_PASS)
    resp = c.post("/api/system/costs/budget-caps", json={"not_a_real_service": 5})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    check(resp.json().get("saved") == {}, f"unknown service should not be saved, got {resp.json()}")


# ── Ask Frank to Fix (Deactivated listings tab, 2026-07-09) ─────────────────────
def test_request_listing_fix_requires_auth():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.post("/api/listings/123456789/request-fix", json={"instructions": ""})
    check(resp.status_code == 401, f"unauthenticated request-fix should 401, got {resp.status_code}")


# ── Anthropic usage logging (2026-07-10 — "what used the Anthropic money") ──────
class _FakeUsage:
    def __init__(self, input_tokens, output_tokens, cache_creation=0, cache_read=0):
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.cache_creation_input_tokens = cache_creation
        self.cache_read_input_tokens = cache_read

def test_log_anthropic_usage_then_summed_by_cost_snapshot():
    # _log_anthropic_usage is the wrapper _anthropic_create()/the chat stream path
    # both call on every real call -- this proves a logged call is actually
    # readable back out and priced, without needing a live Anthropic key.
    before = server._anthropic_cost_snapshot()
    # Large token counts (not a realistic single call) so the cost survives the
    # top-level estimate's 2-decimal rounding -- a real ~$0.003 call would round
    # to $0.00 at that precision and make this assertion flaky, even though the
    # by_model breakdown (4-decimal) would still show it correctly.
    server._log_anthropic_usage("test_caller", "claude-haiku-4-5-20251001", _FakeUsage(2_000_000, 1_000_000))
    after = server._anthropic_cost_snapshot()
    check(after["available"], f"cost snapshot should be available after logging a call, got {after}")
    check(after["call_count"] == before.get("call_count", 0) + 1,
          f"expected call_count to increase by 1, before={before}, after={after}")
    check(after["estimated_cost_usd"] > before.get("estimated_cost_usd", 0),
          f"expected estimated cost to increase, before={before}, after={after}")
    model_stats = after.get("by_model", {}).get("claude-haiku-4-5-20251001")
    check(model_stats is not None, f"expected claude-haiku-4-5-20251001 in by_model, got {after.get('by_model')}")
    check(model_stats["input_tokens"] >= 2_000_000, f"expected logged input tokens tracked, got {model_stats}")

def test_log_anthropic_usage_never_raises_on_none_usage():
    # A caught-but-swallowed edge case could pass usage=None -- must not crash the
    # real Anthropic call it wraps.
    try:
        server._log_anthropic_usage("test_caller_none", "claude-sonnet-5", None)
    except Exception as exc:
        check(False, f"_log_anthropic_usage(usage=None) should never raise, got {exc}")


# ── health endpoint (unauthenticated by design -- external watchdog hits this) ──
def test_health_endpoint_is_unauthenticated_and_reports_persistence():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/health")
    check(resp.status_code == 200, f"/health should be reachable with no auth, got {resp.status_code}")
    body = resp.json()
    check("persistent" in body, f"/health should report persistence status, got: {body}")


# ── bare-domain root (2026-07-10 incident: GET / had no route at all, so anyone
# navigating to the plain domain instead of /frank or /login got a raw
# {"detail":"Not Found"} JSON blob -- fixed by redirecting to /frank, which itself
# redirects an unauthenticated visitor on to /login) ──
def test_root_redirects_to_frank():
    c = TestClient(server.app, base_url="https://testserver")
    resp = c.get("/", follow_redirects=False)
    check(resp.status_code == 307, f"GET / should redirect (307), got {resp.status_code}")
    check(resp.headers.get("location") == "/frank",
          f"GET / should redirect to /frank, got {resp.headers.get('location')!r}")


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
