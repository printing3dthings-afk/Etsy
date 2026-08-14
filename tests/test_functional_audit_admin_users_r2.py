#!/usr/bin/env python3
"""
Functional audit -- admin user-management routes, ROUND 2 (2026-08-14, key: admin_users_r2).

Round 1 (tests/test_functional_audit_admin_users.py) already verified: owner-only
gating on all three routes, the owner account can never be deleted, and
admin_reset_password revokes the target user's existing session immediately.

This round targets a specific asymmetry between two sibling routes in
tools/api_server/main.py that both delete a hub_users row:

  - DELETE /api/account/{...}   (delete_my_account, self-service)   -- after
    deleting the row, explicitly clears the caller's session from the
    in-memory _sessions dict AND calls db.delete_sessions_for_user(uname).
    Its own docstring says it "mirrors the existing invariant in
    admin_delete_user".
  - DELETE /api/admin/users/{username}  (admin_delete_user, owner-initiated)
    -- deletes the hub_users row via db.delete_hub_user(uname) and returns
    {"ok": True}. It does NOT touch _sessions and does NOT call
    db.delete_sessions_for_user(uname).

_check_session()/_get_session_user() (main.py) validate a session purely by
looking up the session id in the in-memory _sessions dict (falling back to
the `sessions` DB table) -- neither ever re-checks that the underlying
hub_users row still exists. So a session created before the delete has
nothing that invalidates it when admin_delete_user runs.

Net effect: when the owner deletes another admin's account via
admin_delete_user, that admin's existing logged-in session cookie keeps
authenticating successfully (e.g. GET /api/me still returns 200 with their
username) even though db.get_hub_user() confirms the account row is gone.
A revoked/deleted user's session should die immediately, exactly like it
does for admin_reset_password and delete_my_account -- this is the
regression under test.

Same FastAPI TestClient pattern as tests/test_functional_audit_admin_users.py
and tests/test_signup_and_account_deletion.py -- real `app` object, no live
server, no network calls.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_admin_users_r2_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── fixtures ─────────────────────────────────────────────────────────────────

_OWNER_USER = "audit_r2_owner"
_OWNER_PASS = "AuditR2Owner!2026"
db.create_hub_user(_OWNER_USER, server._hash_password(_OWNER_PASS), role="owner")


def _fresh_client() -> "TestClient":
    return TestClient(server.app, base_url="https://testserver")


def _login(username: str, password: str) -> "TestClient":
    c = _fresh_client()
    resp = c.post("/login", data={"username": username, "password": password, "next": "/"},
                  follow_redirects=False)
    check("frank_session" in c.cookies, f"login as {username!r} should succeed (setup step), got {resp.status_code}")
    return c


def _login_as_owner() -> "TestClient":
    return _login(_OWNER_USER, _OWNER_PASS)


# ── main finding: admin_delete_user does not revoke the deleted user's session ──

def test_delete_user_should_revoke_target_users_existing_session_but_does_not():
    victim = "audit_r2_delete_session_victim"
    victim_pass = "VictimOriginal123!"
    db.create_hub_user(victim, server._hash_password(victim_pass), role="admin")

    # Log the victim in for real and confirm their session works first.
    victim_client = _login(victim, victim_pass)
    pre = victim_client.get("/api/me")
    check(pre.status_code == 200, f"victim's session should be valid before the delete, got {pre.status_code}")
    check(pre.json().get("username") == victim, "the /api/me identity should be the victim before delete")

    # Owner deletes the victim's account.
    owner_client = _login_as_owner()
    del_resp = owner_client.delete(f"/api/admin/users/{victim}")
    check(del_resp.status_code == 200, f"owner deleting a regular admin account should 200, got {del_resp.status_code}: {del_resp.text}")

    # The account row is genuinely gone.
    check(db.get_hub_user(victim) is None, "the victim's hub_users row should be gone after admin_delete_user")

    # BUG: the victim's pre-delete session cookie should now be dead (same
    # contract as admin_reset_password and delete_my_account), but
    # admin_delete_user never calls db.delete_sessions_for_user() or clears
    # _sessions, so the stale cookie keeps working for a deleted account.
    post = victim_client.get("/api/me")
    check(post.status_code == 401,
          f"a deleted user's pre-existing session cookie must stop authenticating immediately, "
          f"but got {post.status_code} (expected 401) -- response body: {post.text}")
    if post.status_code == 200:
        check(post.json().get("username") != victim,
              "if the deleted user's session is somehow still 200, it must not still resolve to "
              "their own (deleted) username")

    # Cross-check directly against the session machinery to make the root
    # cause unambiguous: the session id is still a live, valid session in
    # the server's own session store even though the account is deleted.
    sid = victim_client.cookies.get("frank_session")
    check(sid is not None, "test setup: victim client should still be carrying its session cookie")
    with server._sessions_lock:
        still_in_memory = sid in server._sessions
    check(not still_in_memory,
          "the deleted user's session id must have been purged from the in-memory _sessions dict "
          "by admin_delete_user (it was not)")


# ── contrast case: the sibling self-service delete path gets this right ──────
# (Proves the fix pattern already exists in this codebase -- delete_my_account
# revokes sessions on delete -- so admin_delete_user is a real asymmetry, not
# a case where "no route in this codebase does this yet".)

def test_sibling_self_service_delete_account_route_does_revoke_the_session():
    victim = "audit_r2_self_delete_victim"
    victim_pass = "SelfDeleteMe123!"
    db.create_hub_user(victim, server._hash_password(victim_pass), role="admin")

    victim_client = _login(victim, victim_pass)
    pre = victim_client.get("/api/me")
    check(pre.status_code == 200, f"victim's session should be valid before self-delete, got {pre.status_code}")

    del_resp = victim_client.delete("/api/account")
    check(del_resp.status_code == 200, f"self-service account delete should 200, got {del_resp.status_code}: {del_resp.text}")
    check(db.get_hub_user(victim) is None, "the victim's hub_users row should be gone after self-delete")

    post = victim_client.get("/api/me")
    check(post.status_code == 401,
          f"unlike admin_delete_user, DELETE /api/account correctly revokes the caller's own "
          f"session immediately -- expected 401, got {post.status_code}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FUNCTIONAL AUDIT (ROUND 2) TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FUNCTIONAL AUDIT (ROUND 2) TESTS OK -- admin_delete_user correctly revokes the "
          "deleted user's existing session immediately, matching its sibling delete_my_account route.")


if __name__ == "__main__":
    run()
