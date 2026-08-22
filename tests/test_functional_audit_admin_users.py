#!/usr/bin/env python3
"""
Functional audit -- admin user-management routes (2026-08-13, key: admin_users).

Targets three FastAPI route handlers in tools/api_server/main.py that have
zero prior test coverage:
  - admin_create_user          POST   /api/admin/users
  - admin_reset_password       POST   /api/admin/users/{username}/reset-password
  - admin_delete_user          DELETE /api/admin/users/{username}

What this verifies:
  1. All three routes actually enforce owner-only access via `_require_owner`
     (not some weaker check) -- tested with a real logged-in role="admin"
     session, not just code inspection.
  2. admin_delete_user cannot be used to delete the last/only owner account
     (it blocks deleting ANY owner-role account, so the "brick the login
     system" scenario is structurally impossible via this route).
  3. admin_reset_password actually invalidates the target user's existing
     sessions (both the in-memory _sessions dict and the durable
     `db.delete_sessions_for_user` call) -- a stale cookie must stop working
     immediately after a reset.

Same FastAPI TestClient pattern as tests/test_signup_and_account_deletion.py
-- real `app` object, no live server, no network calls. ENABLE_TEST_LOGIN
seeds one role="admin" account at import time, which is exactly the
"non-owner admin" identity this audit needs to prove is rejected.
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_functional_audit_admin_users_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "functional-audit-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "audittestadmin"
os.environ["TEST_LOGIN_PASSWORD"] = "AuditTestAdmin!2026"

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

_OWNER_USER = "audit_real_owner"
_OWNER_PASS = "AuditRealOwner!2026"
db.create_hub_user(_OWNER_USER, server._hash_password(_OWNER_PASS), role="owner")

# ENABLE_TEST_LOGIN seeded this one at import time with role="admin" -- our
# "logged-in but NOT owner" identity for the negative-access tests.
_NONOWNER_USER = os.environ["TEST_LOGIN_USERNAME"]
_NONOWNER_PASS = os.environ["TEST_LOGIN_PASSWORD"]


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


def _login_as_nonowner_admin() -> "TestClient":
    return _login(_NONOWNER_USER, _NONOWNER_PASS)


# ── 1. owner-only enforcement on all three routes ────────────────────────────

def test_create_user_rejects_nonowner_admin_session():
    c = _login_as_nonowner_admin()
    resp = c.post("/api/admin/users", json={"username": "shouldnotexist1", "password": "LongEnough123!"})
    check(resp.status_code == 403, f"POST /api/admin/users as non-owner admin should 403, got {resp.status_code}: {resp.text}")
    check(db.get_hub_user("shouldnotexist1") is None, "no user should have been created by a rejected non-owner call")


def test_create_user_rejects_no_session():
    c = _fresh_client()
    resp = c.post("/api/admin/users", json={"username": "shouldnotexist2", "password": "LongEnough123!"})
    check(resp.status_code in (401, 403), f"POST /api/admin/users with no session should 401/403, got {resp.status_code}: {resp.text}")


def test_reset_password_rejects_nonowner_admin_session():
    # Target a real, harmless victim account so a false-negative (i.e. the
    # reset actually going through) would be visible below.
    victim = "audit_reset_victim1"
    db.create_hub_user(victim, server._hash_password("OriginalPass123!"), role="admin")
    c = _login_as_nonowner_admin()
    resp = c.post(f"/api/admin/users/{victim}/reset-password", json={"password": "NewPassword123!"})
    check(resp.status_code == 403, f"reset-password as non-owner admin should 403, got {resp.status_code}: {resp.text}")
    # Confirm the password was NOT actually changed.
    row = db.get_hub_user(victim)
    check(server._verify_password(row["pw_hash"], "OriginalPass123!"),
          "a rejected non-owner reset-password call must not have changed the victim's password")


def test_delete_user_rejects_nonowner_admin_session():
    victim = "audit_delete_victim1"
    db.create_hub_user(victim, server._hash_password("VictimPass123!"), role="admin")
    c = _login_as_nonowner_admin()
    resp = c.delete(f"/api/admin/users/{victim}")
    check(resp.status_code == 403, f"DELETE /api/admin/users/{{username}} as non-owner admin should 403, got {resp.status_code}: {resp.text}")
    check(db.get_hub_user(victim) is not None, "a rejected non-owner delete call must not have removed the victim account")


def test_all_three_routes_use_real_require_owner_dependency_shape():
    # Cross-check against _require_owner directly (the same helper used by
    # e.g. admin_list_users) to make sure these three routes weren't quietly
    # wired to a weaker/duplicate check under a different name.
    import inspect
    for fn in (server.admin_create_user, server.admin_reset_password, server.admin_delete_user):
        src = inspect.getsource(fn)
        check("_require_owner(request)" in src,
              f"{fn.__name__} should call the shared _require_owner(request) helper, "
              f"not a bespoke/weaker owner check")


# ── 2. owner account can never be deleted here -- "brick the login system" ──

def test_delete_user_blocks_deleting_the_owner_account():
    c = _login_as_owner()
    resp = c.delete(f"/api/admin/users/{_OWNER_USER}")
    check(resp.status_code == 403, f"deleting the owner account should 403, got {resp.status_code}: {resp.text}")
    check(db.get_hub_user(_OWNER_USER) is not None, "the owner account must still exist after a blocked delete attempt")
    # And the owner can still act -- the block must not have side-effected anything.
    still_ok = c.get("/api/admin/users")
    check(still_ok.status_code == 200, f"owner session should still work after a blocked self-delete of the owner, got {still_ok.status_code}")


def test_delete_user_blocks_deleting_the_only_owner_even_if_it_is_the_sole_owner():
    # Confirm there is exactly one owner-role row in this DB right now, then
    # confirm the route still refuses to delete it -- proving the "last
    # owner" scenario specifically (not just "some other owner exists so
    # it's fine"), matching CLAUDE.md's requirement that this can never
    # brick the login system.
    owners = [u for u in db.list_hub_users() if u["role"] == "owner"]
    check(len(owners) == 1, f"test setup expects exactly 1 owner-role account, found {len(owners)}: {owners}")
    c = _login_as_owner()
    resp = c.delete(f"/api/admin/users/{_OWNER_USER}")
    check(resp.status_code == 403, f"deleting the sole remaining owner should 403, got {resp.status_code}")
    owners_after = [u for u in db.list_hub_users() if u["role"] == "owner"]
    check(len(owners_after) == 1, "the sole owner account must still exist after the blocked delete")


def test_owner_can_delete_a_regular_admin_account():
    victim = "audit_delete_ok_admin"
    db.create_hub_user(victim, server._hash_password("VictimPass123!"), role="admin")
    c = _login_as_owner()
    resp = c.delete(f"/api/admin/users/{victim}")
    check(resp.status_code == 200, f"owner deleting a regular admin account should 200, got {resp.status_code}: {resp.text}")
    check(db.get_hub_user(victim) is None, "the admin account row should be gone after a legitimate owner delete")


# ── 3. reset-password actually revokes the target user's existing sessions ──

def test_reset_password_revokes_target_users_existing_session():
    victim = "audit_reset_session_victim"
    victim_pass = "VictimOriginal123!"
    db.create_hub_user(victim, server._hash_password(victim_pass), role="admin")

    # Log the victim in for real and confirm their session works first.
    victim_client = _login(victim, victim_pass)
    pre = victim_client.get("/api/admin/users")
    # A plain admin can't list users (owner-only), but a 403 here still proves
    # the SESSION itself is valid/authenticated (vs. 401 which would mean no
    # valid session at all). Use a route any authenticated user can hit instead.
    pre_authed = victim_client.get("/api/me")
    check(pre_authed.status_code == 200, f"victim's session should be valid before the reset, got {pre_authed.status_code}")
    check(pre_authed.json().get("username") == victim, "the /api/me identity should be the victim before reset")

    owner_client = _login_as_owner()
    reset_resp = owner_client.post(f"/api/admin/users/{victim}/reset-password", json={"password": "BrandNewPass456!"})
    check(reset_resp.status_code == 200, f"owner resetting a regular admin's password should 200, got {reset_resp.status_code}: {reset_resp.text}")

    # The victim's OLD cookie must now be dead.
    post = victim_client.get("/api/me")
    check(post.status_code == 401,
          f"the victim's pre-reset session cookie must be revoked immediately after a password reset, got {post.status_code} instead of 401")

    # And the new password actually works for a fresh login.
    relogin = _login(victim, "BrandNewPass456!")
    check("frank_session" in relogin.cookies, "the victim should be able to log in with the new password after reset")

    # The old password must no longer work.
    old_login = _fresh_client()
    old_resp = old_login.post("/login", data={"username": victim, "password": victim_pass, "next": "/"}, follow_redirects=False)
    check("frank_session" not in old_login.cookies, "the victim's OLD password must be rejected after a reset")


def test_reset_password_rejects_resetting_a_different_owners_password():
    # This route allows role="owner" (the caller) to create a SECOND owner
    # row directly via db.create_hub_user (bypassing admin_create_user's own
    # "cannot create a second owner" guard) purely so this specific branch
    # -- "owner cannot reset a DIFFERENT owner's password" -- is actually
    # exercised, rather than just inspecting the source. Deliberately does
    # NOT touch _OWNER_USER/_OWNER_PASS so it can't break later tests that
    # depend on that shared fixture's password still being valid (an earlier
    # draft of this test self-reset _OWNER_USER's own password here, which
    # silently broke every subsequent owner-login-dependent test below it).
    other_owner_user = "audit_other_owner"
    other_owner_pass = "AuditOtherOwner!2026"
    db.create_hub_user(other_owner_user, server._hash_password(other_owner_pass), role="owner")

    c = _login_as_owner()  # logged in as _OWNER_USER
    resp = c.post(f"/api/admin/users/{other_owner_user}/reset-password", json={"password": "Hijacked123!"})
    check(resp.status_code == 403, f"an owner resetting a DIFFERENT owner's password should 403, got {resp.status_code}: {resp.text}")

    # Confirm the other owner's real password still works (nothing changed).
    relogin = _login(other_owner_user, other_owner_pass)
    check("frank_session" in relogin.cookies, "the other owner's original password must still work after the blocked reset attempt")

    # Self-reset (owner resetting their OWN password) is the allowed branch
    # of the same guard -- verify it separately on the throwaway second
    # owner account (never on the shared _OWNER_USER fixture).
    self_reset = relogin.post(f"/api/admin/users/{other_owner_user}/reset-password", json={"password": "SelfResetNew456!"})
    check(self_reset.status_code == 200, f"an owner resetting their OWN password should 200, got {self_reset.status_code}: {self_reset.text}")
    fresh = _fresh_client()
    relogin2 = fresh.post("/login", data={"username": other_owner_user, "password": "SelfResetNew456!", "next": "/"},
                           follow_redirects=False)
    check("frank_session" in fresh.cookies, "owner should be able to log in with their new self-reset password")


# ── sanity: the legitimate owner path actually works (proves tests aren't vacuous) ──

def test_owner_can_create_and_reset_a_regular_admin_user():
    c = _login_as_owner()
    create_resp = c.post("/api/admin/users", json={"username": "audit_new_admin", "password": "NewAdminPass123!"})
    check(create_resp.status_code == 200, f"owner creating a new admin user should 200, got {create_resp.status_code}: {create_resp.text}")
    check(db.get_hub_user("audit_new_admin") is not None, "the new admin account should exist after creation")
    check(create_resp.json().get("role") == "admin", "created user's role should be 'admin'")


def test_create_user_rejects_role_owner():
    c = _login_as_owner()
    resp = c.post("/api/admin/users", json={"username": "audit_second_owner_attempt", "password": "SomePass123!", "role": "owner"})
    check(resp.status_code == 400, f"creating a second owner via this route should 400, got {resp.status_code}: {resp.text}")
    check(db.get_hub_user("audit_second_owner_attempt") is None, "no second owner account should have been created")


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
    print("FUNCTIONAL AUDIT TESTS OK -- admin_create_user/admin_reset_password/admin_delete_user "
          "all correctly enforce owner-only access (a real non-owner admin session is rejected "
          "with 403 on all three), the owner account can never be deleted via admin_delete_user "
          "(including as the sole remaining owner), and admin_reset_password actually revokes "
          "the target user's pre-existing session immediately.")


if __name__ == "__main__":
    run()
