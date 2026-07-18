#!/usr/bin/env python3
"""
Tests for self-service signup (/signup) and self-service account deletion
(DELETE /api/account), added 2026-07-18 per Scott: testers he sent Frank to
were hitting an existing-login-only wall with no way to create their own
account (the only signup path, _SETUP_PAGE, is a strict one-time "create the
owner account" flow gated on hub_users being empty — see main.py's
login_page()/login_submit()). Also covers the account-deletion self-service
endpoint requested alongside it (a GDPR/CCPA-style right-to-erasure feature,
not an ADA one — see data/knowledge_base/compliance_notes.md).

Same FastAPI TestClient pattern as tests/test_http_routes.py (real `app`
object, no live server, no network calls) — ENABLE_TEST_LOGIN seeds one
owner-role account at import time, so hub_users is non-empty for every test
here, matching the realistic "signup after an owner already exists" case.

Run locally:  python tests/test_signup_and_account_deletion.py
In CI:        see .github/workflows/ci-smoke.yml
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_signup_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "signup-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "signuptestowner"
os.environ["TEST_LOGIN_PASSWORD"] = "SignupTestOwner!2026"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(server.app, base_url="https://testserver")

# ENABLE_TEST_LOGIN seeds TEST_LOGIN_USERNAME with role="admin" ("full admin
# access" per its own startup log line) -- NOT "owner" -- so it can't be used to
# test the owner-block path on DELETE /api/account (self-deleting an admin
# account is supposed to succeed). A separate, dedicated role="owner" account is
# created directly here so that test never touches the shared seeded account
# other tests rely on staying present (hub_users must never go empty mid-suite,
# or /signup's own "no owner yet, redirect to /login" guard kicks in and every
# subsequent signup test fails with a confusing cascade of unrelated 303s).
_REAL_OWNER_USER = "signuprealowner"
_REAL_OWNER_PASS = "SignupRealOwner!2026"
db.create_hub_user(_REAL_OWNER_USER, server._hash_password(_REAL_OWNER_PASS), role="owner")

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_client() -> "TestClient":
    return TestClient(server.app, base_url="https://testserver")


def _signup(**overrides) -> "tuple[TestClient, object]":
    c = _fresh_client()
    payload = {
        "email": "tester1@example.com",
        "display_name": "Test Tester",
        "username": "testertester",
        "password": "SignupPass!2026",
        "confirm_password": "SignupPass!2026",
        "next": "/",
    }
    payload.update(overrides)
    resp = c.post("/signup", data=payload, follow_redirects=False)
    return c, resp


def _login_as_real_owner() -> "TestClient":
    c = _fresh_client()
    c.post("/login", data={"username": _REAL_OWNER_USER, "password": _REAL_OWNER_PASS, "next": "/"},
           follow_redirects=False)
    return c


# ── /signup availability ─────────────────────────────────────────────────────

def test_signup_page_loads_when_hub_users_non_empty():
    resp = client.get("/signup")
    check(resp.status_code == 200, f"GET /signup should 200 once an owner exists, got {resp.status_code}")
    check("Create an account" in resp.text, "the signup page should render its own form, not the login form")


def test_login_page_always_offers_a_signup_link_once_an_owner_exists():
    resp = client.get("/login")
    check("/signup" in resp.text,
          "GET /login should always link to /signup once hub_users is non-empty -- "
          "this was the actual bug Scott's testers hit (dead-end existing-login-only screen)")


# ── successful signup ────────────────────────────────────────────────────────

def test_signup_creates_admin_account_with_email_and_name():
    username = "newsignupuser1"
    c, resp = _signup(username=username, email="new1@example.com", display_name="New Signup User")
    check(resp.status_code == 200, f"a successful signup should render the recovery-code page (200), got {resp.status_code}")
    check("frank_session" in c.cookies, "a successful signup should log the new user in immediately")

    row = db.get_hub_user(username)
    assert row, "the new account should exist in hub_users"
    check(row["role"] == "admin", f"self-signup accounts should get role='admin' (full access), got: {row['role']}")
    check(row["email"] == "new1@example.com", f"email should be persisted, got: {row.get('email')}")
    check(row["display_name"] == "New Signup User", f"display_name should be persisted, got: {row.get('display_name')}")
    check(row["recovery_code_hash"], "a signup account should get a recovery code, same as owner/admin-panel accounts")


def test_signup_account_can_immediately_use_a_protected_route():
    username = "newsignupuser2"
    c, resp = _signup(username=username, email="new2@example.com")
    check(resp.status_code == 200, f"signup should succeed, got {resp.status_code}")
    ok = c.get("/api/todos")
    check(ok.status_code == 200, f"the new session cookie should already work on a protected route, got {ok.status_code}")


def test_me_endpoint_returns_email_and_display_name_for_a_signup_account():
    username = "newsignupuser3"
    c, resp = _signup(username=username, email="new3@example.com", display_name="Three Tester")
    check(resp.status_code == 200, f"signup should succeed, got {resp.status_code}")
    me = c.get("/api/me")
    check(me.status_code == 200, f"GET /api/me should 200, got {me.status_code}")
    body = me.json()
    check(body.get("email") == "new3@example.com", f"expected email in /api/me, got: {body}")
    check(body.get("display_name") == "Three Tester", f"expected display_name in /api/me, got: {body}")
    check(body.get("role") == "admin", f"expected role=admin, got: {body}")


# ── validation ────────────────────────────────────────────────────────────────

def test_signup_rejects_invalid_email():
    _, resp = _signup(username="badmail1", email="not-an-email")
    check(resp.status_code == 303, f"invalid email should redirect back with an error, got {resp.status_code}")
    check(not db.get_hub_user("badmail1"), "no account should be created on an invalid email")


def test_signup_rejects_missing_display_name():
    _, resp = _signup(username="badname1", display_name="")
    check(resp.status_code == 303, f"missing name should redirect back with an error, got {resp.status_code}")
    check(not db.get_hub_user("badname1"), "no account should be created without a name")


def test_signup_rejects_password_mismatch():
    _, resp = _signup(username="badpw1", password="Something!2026", confirm_password="Different!2026")
    check(resp.status_code == 303, f"mismatched passwords should redirect back with an error, got {resp.status_code}")
    check(not db.get_hub_user("badpw1"), "no account should be created on a password mismatch")


def test_signup_rejects_short_password():
    _, resp = _signup(username="badpw2", password="short", confirm_password="short")
    check(resp.status_code == 303, f"a too-short password should redirect back with an error, got {resp.status_code}")
    check(not db.get_hub_user("badpw2"), "no account should be created with a too-short password")


def test_signup_rejects_duplicate_username():
    username = "dupeuser1"
    c1, resp1 = _signup(username=username, email="dupe-a@example.com")
    check(resp1.status_code == 200, f"first signup with this username should succeed, got {resp1.status_code}")
    c2, resp2 = _signup(username=username, email="dupe-b@example.com")
    check(resp2.status_code == 303, f"a duplicate username should redirect back with an error, got {resp2.status_code}")
    row = db.get_hub_user(username)
    check(row["email"] == "dupe-a@example.com", "the original account must not be overwritten by the rejected duplicate signup")


# ── DELETE /api/account (self-service deletion) ─────────────────────────────

def test_delete_account_requires_auth():
    c = _fresh_client()
    resp = c.delete("/api/account")
    check(resp.status_code == 401, f"unauthenticated DELETE /api/account should 401, got {resp.status_code}")


def test_delete_account_removes_a_self_signed_up_account_and_revokes_session():
    username = "deleteme1"
    c, resp = _signup(username=username, email="deleteme1@example.com")
    check(resp.status_code == 200, f"signup should succeed, got {resp.status_code}")
    check(db.get_hub_user(username) is not None, "account should exist before deletion")

    del_resp = c.delete("/api/account")
    check(del_resp.status_code == 200, f"DELETE /api/account should 200 for a non-owner account, got {del_resp.status_code}: {del_resp.text}")
    check(db.get_hub_user(username) is None, "the account row should be gone after deletion")

    after = c.get("/api/todos")
    check(after.status_code == 401, f"the session should be revoked immediately after self-deletion, got {after.status_code}")


def test_delete_account_blocks_the_owner_account():
    c = _login_as_real_owner()
    check("frank_session" in c.cookies, "owner login should succeed as test setup")
    resp = c.delete("/api/account")
    check(resp.status_code == 403, f"the owner account must not be self-deletable, got {resp.status_code}")
    check(db.get_hub_user(_REAL_OWNER_USER) is not None, "the owner account must still exist after a blocked deletion attempt")
    # And the owner's session should still work -- a blocked deletion must not have
    # side-effected the session away.
    still_ok = c.get("/api/todos")
    check(still_ok.status_code == 200, f"the owner's session should still be valid after a blocked self-delete attempt, got {still_ok.status_code}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SIGNUP / ACCOUNT DELETION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SIGNUP / ACCOUNT DELETION TESTS OK — self-service signup creates full-access "
          "admin accounts with email/name persisted, validates all fields, the login page "
          "always offers a way in, and self-service account deletion works for regular "
          "accounts while the owner account stays protected.")


if __name__ == "__main__":
    run()
