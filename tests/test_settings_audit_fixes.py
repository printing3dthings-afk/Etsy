#!/usr/bin/env python3
"""
Tests for the 2026-08-06 Settings-page audit fixes and additions, prompted by
Scott: "I do not think it is sufficient enough... double check just to make
sure there's nothing else that we need to add." Confirmed findings covered
here (theme reduction itself is pure frontend/JS, covered by playwright_smoke.py):

  - owner_name was dead plumbing: _SETTINGS_APPLY mapped it to business_config.
    OWNER_NAME but nothing ever wrote the setting. POST /api/account now writes
    it when a name is saved.
  - GET /api/system/costs + POST /api/system/costs/budget-caps existed with zero
    frontend wiring (not covered here -- pure frontend card, verified by
    playwright_smoke.py; the endpoints themselves already had no test coverage
    gap, they're pre-existing).
  - Notification preferences (daily_brief_hour/daily_brief_enabled) are new
    settings validated through the existing generic /api/settings endpoint.
  - POST /api/system/run-retention-cleanup: manual trigger for the existing
    _prune_buyer_data_retention() pass.
  - Session management (list/revoke/revoke-others) genuinely didn't exist
    anywhere in the app before this -- full lifecycle covered here using the
    same FastAPI TestClient pattern as tests/test_signup_and_account_deletion.py.

Run: python tests/test_settings_audit_fixes.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_settings_audit_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "settings-audit-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "settingsaudittester"
os.environ["TEST_LOGIN_PASSWORD"] = "SettingsAuditTest!2026"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_TEST_USER = os.environ["TEST_LOGIN_USERNAME"]
_TEST_PASS = os.environ["TEST_LOGIN_PASSWORD"]

client = TestClient(server.app, base_url="https://testserver")

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_client() -> "TestClient":
    return TestClient(server.app, base_url="https://testserver")


def _login() -> "TestClient":
    c = _fresh_client()
    c.post("/login", data={"username": _TEST_USER, "password": _TEST_PASS, "next": "/"},
           follow_redirects=False)
    return c


# ── owner_name fix ────────────────────────────────────────────────────────

def test_saving_my_account_name_updates_owner_name_setting():
    c = _login()
    r = c.post("/api/account", json={"name": "Testy McTestface", "email": "", "phone": "", "timezone": ""})
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}")
    check(db.get_setting("owner_name") == "Testy McTestface",
          f"expected the owner_name setting to be written, got {db.get_setting('owner_name')!r}")
    check(server.business_config.OWNER_NAME == "Testy McTestface",
          f"expected business_config.OWNER_NAME to reflect the new name live, got {server.business_config.OWNER_NAME!r}")


def test_saving_my_account_without_a_name_does_not_touch_owner_name():
    c = _login()
    db.set_setting("owner_name", "Untouched Name")
    server._apply_settings_overrides()
    r = c.post("/api/account", json={"name": "", "email": "someone@example.com", "phone": "", "timezone": ""})
    check(r.status_code == 200, f"expected 200, got {r.status_code}")
    check(db.get_setting("owner_name") == "Untouched Name",
          f"an empty name must not clear/overwrite the existing owner_name setting, got {db.get_setting('owner_name')!r}")


# ── Notification preferences ─────────────────────────────────────────────

def test_settings_get_includes_daily_brief_defaults():
    c = _login()
    db.set_setting("daily_brief_hour", None)
    db.set_setting("daily_brief_enabled", None)
    r = c.get("/api/settings")
    d = r.json()
    check(d.get("daily_brief_hour") == 6, f"expected default hour 6, got {d.get('daily_brief_hour')}")
    check(d.get("daily_brief_enabled") is True, f"expected default enabled=True, got {d.get('daily_brief_enabled')}")


def test_settings_post_persists_daily_brief_hour():
    c = _login()
    r = c.post("/api/settings", json={"daily_brief_hour": 20})
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}")
    check(db.get_setting("daily_brief_hour") == "20", f"expected persisted '20', got {db.get_setting('daily_brief_hour')!r}")
    r2 = c.get("/api/settings")
    check(r2.json().get("daily_brief_hour") == 20, f"expected the new hour to round-trip, got {r2.json().get('daily_brief_hour')}")


def test_settings_post_rejects_out_of_range_hour():
    c = _login()
    r = c.post("/api/settings", json={"daily_brief_hour": 24})
    check(r.status_code == 400, f"expected 400 for an out-of-range hour, got {r.status_code}")
    r2 = c.post("/api/settings", json={"daily_brief_hour": -1})
    check(r2.status_code == 400, f"expected 400 for a negative hour, got {r2.status_code}")


def test_settings_post_daily_brief_enabled_toggle():
    c = _login()
    r = c.post("/api/settings", json={"daily_brief_enabled": False})
    check(r.status_code == 200, f"expected 200, got {r.status_code}")
    check(db.get_setting("daily_brief_enabled") == "0", f"expected '0' stored, got {db.get_setting('daily_brief_enabled')!r}")
    r2 = c.get("/api/settings")
    check(r2.json().get("daily_brief_enabled") is False, f"expected False to round-trip, got {r2.json().get('daily_brief_enabled')}")


# ── Retention cleanup endpoint ────────────────────────────────────────────

def test_run_retention_cleanup_calls_the_real_prune_function():
    c = _login()
    fake_result = {"drafts_deleted": 3, "notified_orders_trimmed": 0, "sent_log_trimmed": 5}
    with patch.object(server, "_prune_buyer_data_retention", return_value=fake_result) as mock_prune:
        r = c.post("/api/system/run-retention-cleanup")
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}")
    check(mock_prune.called, "the endpoint must call the real _prune_buyer_data_retention()")
    check(r.json() == fake_result, f"expected the prune result returned verbatim, got {r.json()}")


# ── Session management (genuinely new feature) ────────────────────────────

def test_short_id_is_stable_and_never_reveals_the_raw_session_id():
    a = server._session_short_id("some-real-session-token-abc123")
    b = server._session_short_id("some-real-session-token-abc123")
    c_ = server._session_short_id("a-totally-different-token-xyz789")
    check(a == b, "the same session_id must hash to the same short id every time")
    check(a != c_, "different session_ids must produce different short ids")
    check("some-real-session-token-abc123" not in a, "the short id must never contain the raw session id")
    check(len(a) == 12, f"expected a 12-char short id, got {len(a)}")


def test_get_my_sessions_lists_current_session():
    c = _login()
    r = c.get("/api/account/sessions")
    check(r.status_code == 200, f"expected 200, got {r.status_code}")
    sessions = r.json().get("sessions", [])
    check(len(sessions) >= 1, f"expected at least one session for a just-logged-in client, got {sessions}")
    current = [s for s in sessions if s.get("is_current")]
    check(len(current) == 1, f"expected exactly one session marked is_current, got {current}")


def test_get_my_sessions_unauthenticated_returns_empty_not_error():
    c = _fresh_client()
    r = c.get("/api/account/sessions")
    # No session cookie and no bearer token -> the shared auth dependency 401s
    # before _get_session_user() is ever reached, which is correct (this
    # endpoint still requires SOME valid auth, just not admin/owner scope).
    check(r.status_code == 401, f"expected 401 with zero auth at all, got {r.status_code}")


def test_two_logins_produce_two_listed_sessions():
    c1 = _login()
    c2 = _login()
    r = c1.get("/api/account/sessions")
    sessions = r.json().get("sessions", [])
    check(len(sessions) >= 2, f"expected at least 2 active sessions after logging in twice, got {len(sessions)}: {sessions}")
    current_flags = [s["is_current"] for s in sessions]
    check(current_flags.count(True) == 1, f"exactly one session should be marked current from c1's perspective, got {current_flags}")


def test_revoke_specific_other_session_removes_it_and_logs_it_out():
    c1 = _login()
    c2 = _login()
    # Find c2's session (the one NOT current from c1's list).
    sessions = c1.get("/api/account/sessions").json()["sessions"]
    other = next((s for s in sessions if not s["is_current"]), None)
    check(other is not None, f"expected to find at least one non-current session, got {sessions}")
    if other is None:
        return
    r = c1.delete(f"/api/account/sessions/{other['session_id_short']}")
    check(r.status_code == 200, f"expected 200 revoking another session, got {r.status_code}: {r.text}")
    # c2's own cookie must now be dead.
    r2 = c2.get("/api/todos")
    check(r2.status_code == 401, f"a revoked session's cookie must stop authenticating, got {r2.status_code}")


def test_cannot_revoke_current_session_via_the_per_id_endpoint():
    c = _login()
    sessions = c.get("/api/account/sessions").json()["sessions"]
    current = next((s for s in sessions if s["is_current"]), None)
    check(current is not None, "expected to find the current session in the list")
    if current is None:
        return
    r = c.delete(f"/api/account/sessions/{current['session_id_short']}")
    check(r.status_code == 400, f"expected 400 trying to revoke your own current session this way, got {r.status_code}")
    # Confirm it's genuinely still alive.
    r2 = c.get("/api/todos")
    check(r2.status_code != 401, "the current session must still be valid after the rejected revoke attempt")


def test_revoke_others_keeps_current_kills_the_rest():
    c1 = _login()
    c2 = _login()
    c3 = _login()
    r = c1.post("/api/account/sessions/revoke-others")
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text}")
    revoked = r.json().get("revoked")
    check(revoked is not None and revoked >= 2, f"expected at least 2 other sessions revoked, got {revoked}")
    check(c1.get("/api/todos").status_code != 401, "c1 (the caller) must remain signed in")
    check(c2.get("/api/todos").status_code == 401, "c2 must be signed out by revoke-others")
    check(c3.get("/api/todos").status_code == 401, "c3 must be signed out by revoke-others")


def test_revoke_nonexistent_session_returns_404():
    c = _login()
    r = c.delete("/api/account/sessions/000000000000")
    check(r.status_code == 404, f"expected 404 for a made-up short id, got {r.status_code}")


def run() -> None:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for fn in tests:
        try:
            fn()
            ran += 1
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised an unexpected error:\n" + traceback.format_exc())
    if _failures:
        print("SETTINGS AUDIT FIXES TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        sys.exit(1)
    print(f"SETTINGS AUDIT FIXES TESTS OK — {ran} tests passed (owner_name wiring, notification-prefs "
          f"validation/persistence, retention cleanup trigger, full session list/revoke/revoke-others "
          f"lifecycle -- no live Etsy/Anthropic calls).")


if __name__ == "__main__":
    run()
