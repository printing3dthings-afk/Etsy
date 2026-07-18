"""
Tests for the Google Calendar integration (2026-07-18): OAuth token storage,
the API client, and how it's wired into Frank -- /api/cadence (Calendar tab),
/api/alerts (reminders), the create_calendar_event agent tool, and the daily
auto-sync that pushes Frank's own due dates/deadlines onto the calendar.

Same monkeypatch style as tests/test_cogs_status.py -- direct swap of module
attributes/functions rather than a mocking framework, matching this repo's
established test pattern.

Run: python tests/test_google_calendar.py
"""
import io
import os
import sys
import tempfile
import traceback
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_gcal_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "gcal-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
import google_calendar_api as gcal  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── db.py: token + synced-event storage ─────────────────────────────────────
def test_google_calendar_tokens_round_trip():
    db.save_google_calendar_tokens("acc-123", "ref-456")
    row = db.get_google_calendar_tokens()
    check(row is not None, "expected a stored token row")
    check(row["access_token"] == "acc-123", f"access_token mismatch: {row}")
    check(row["refresh_token"] == "ref-456", f"refresh_token mismatch: {row}")


def test_google_calendar_tokens_missing_before_save():
    db.init_db()
    conn = db._connect()
    try:
        conn.execute("DELETE FROM google_calendar_tokens WHERE id=1")
        conn.commit()
    finally:
        conn.close()
    row = db.get_google_calendar_tokens()
    check(row is None, f"expected None with no row present, got: {row}")


def test_synced_event_dedup_storage():
    key = "todo:999"
    check(db.get_google_calendar_synced_event(key) is None, "should start unsynced")
    db.save_google_calendar_synced_event(key, "gcal-evt-abc")
    check(db.get_google_calendar_synced_event(key) == "gcal-evt-abc", "should return the saved event id")
    # Re-saving under the same key updates rather than erroring (ON CONFLICT).
    db.save_google_calendar_synced_event(key, "gcal-evt-xyz")
    check(db.get_google_calendar_synced_event(key) == "gcal-evt-xyz", "re-save should update the mapping")


# ── google_calendar_api.py: client behavior ─────────────────────────────────
def test_client_raises_not_connected_with_no_refresh_token():
    c = gcal.GoogleCalendarClient()
    c.refresh_token = ""
    try:
        c.list_upcoming_events()
        _failures.append("expected GoogleCalendarNotConnectedError")
    except gcal.GoogleCalendarNotConnectedError:
        pass


def test_create_event_all_day_vs_timed_body():
    c = gcal.GoogleCalendarClient()
    c.refresh_token = "fake"
    c.access_token = "fake-access"
    captured = {}

    def fake_request(method, url, headers=None, timeout=None, **kwargs):
        captured["kwargs"] = kwargs
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b'{"id": "evt1"}'
        resp.json.return_value = {"id": "evt1"}
        return resp

    with patch.object(gcal._session, "request", side_effect=fake_request):
        c.create_event("Tax deadline", "2026-07-25", "test")
        check(captured["kwargs"]["json"]["start"] == {"date": "2026-07-25"},
              f"all-day event should use a date field, got: {captured['kwargs']['json']}")
        c.create_event("Meeting", "2026-07-25T14:00:00-04:00", "test")
        check(captured["kwargs"]["json"]["start"] == {"dateTime": "2026-07-25T14:00:00-04:00"},
              f"timed event should use a dateTime field, got: {captured['kwargs']['json']}")


def test_refresh_access_token_updates_state_on_success():
    c = gcal.GoogleCalendarClient()
    c.client_id = "cid"
    c.client_secret = "csecret"
    c.refresh_token = "fake-refresh"

    fake_resp = MagicMock()
    fake_resp.json.return_value = {"access_token": "new-access-token"}
    with patch.object(gcal._session, "post", return_value=fake_resp), \
         patch.object(gcal, "_update_env"), \
         patch("db.save_google_calendar_tokens"):
        token = c.refresh_access_token()
        check(token == "new-access-token", f"expected the new token returned, got {token}")
        check(c.access_token == "new-access-token", "client's own access_token should update")


# ── main.py: _get_upcoming_google_calendar_events() degrade behavior ───────
def test_get_upcoming_events_degrades_when_not_connected():
    events = server._get_upcoming_google_calendar_events()
    check(events == [], f"with no credentials configured, expected [], got: {events}")


def test_get_upcoming_events_formats_real_api_shape():
    fake_items = [
        {"id": "e1", "summary": "Dentist", "start": {"dateTime": "2026-07-19T14:00:00-04:00"}, "htmlLink": "https://x"},
        {"id": "e2", "summary": "All-day thing", "start": {"date": "2026-07-20"}},
        {"id": "e3", "start": {"date": "2026-07-21"}},  # no summary at all
    ]

    class _FakeClient:
        def list_upcoming_events(self, days_ahead=14):
            return fake_items

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _FakeClient
        events = server._get_upcoming_google_calendar_events()
        check(len(events) == 3, f"expected 3 formatted events, got: {events}")
        check(events[0]["title"] == "Dentist" and events[0]["all_day"] is False, f"timed event formatting wrong: {events[0]}")
        check(events[1]["all_day"] is True, f"all-day event should be flagged, got: {events[1]}")
        check(events[2]["title"] == "(untitled event)", f"missing summary should fall back, got: {events[2]}")
    finally:
        gcal.GoogleCalendarClient = orig_cls


def test_get_upcoming_events_degrades_on_real_api_error():
    class _BoomingClient:
        def list_upcoming_events(self, days_ahead=14):
            raise gcal.GoogleCalendarError(500, "server exploded")

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _BoomingClient
        events = server._get_upcoming_google_calendar_events()
        check(events == [], f"an API error must degrade to [], not raise, got: {events}")
    finally:
        gcal.GoogleCalendarClient = orig_cls


# ── /api/cadence carries google_calendar ────────────────────────────────────
def test_cadence_endpoint_includes_google_calendar_key():
    client = TestClient(server.app, base_url="https://testserver")
    resp = client.get("/api/cadence", headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}")
    body = resp.json()
    check("google_calendar" in body, f"expected a google_calendar key in /api/cadence, got keys: {list(body.keys())}")
    check(body["google_calendar"] == [], "with no Calendar connected, expect an empty list, not an error")


# ── /api/alerts surfaces near-term events as reminders ──────────────────────
def test_alerts_endpoint_surfaces_near_term_calendar_events():
    today_str = date.today().isoformat()

    class _FakeClient:
        def list_upcoming_events(self, days_ahead=14):
            return [{"id": "e1", "summary": "Ship packages", "start": {"date": today_str}}]

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _FakeClient
        client = TestClient(server.app, base_url="https://testserver")
        resp = client.get("/api/alerts", headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"})
        check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:200]}")
        body = resp.json()
        gcal_alerts = [a for a in body["alerts"] if a.get("source") == "google_calendar"]
        check(len(gcal_alerts) == 1, f"expected 1 near-term calendar alert, got: {gcal_alerts}")
        check(gcal_alerts[0]["title"] == "Ship packages", f"unexpected alert title: {gcal_alerts[0]}")
        check("Today" in gcal_alerts[0]["detail"], f"expected 'Today' in detail, got: {gcal_alerts[0]}")
    finally:
        gcal.GoogleCalendarClient = orig_cls


def test_alerts_endpoint_ignores_far_future_events():
    far_future = (date.today() + timedelta(days=10)).isoformat()

    class _FakeClient:
        def list_upcoming_events(self, days_ahead=2):
            return [{"id": "e1", "summary": "Far away", "start": {"date": far_future}}]

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _FakeClient
        client = TestClient(server.app, base_url="https://testserver")
        resp = client.get("/api/alerts", headers={"Authorization": f"Bearer {os.environ['APP_SECRET_TOKEN']}"})
        body = resp.json()
        gcal_alerts = [a for a in body["alerts"] if a.get("source") == "google_calendar"]
        check(len(gcal_alerts) == 0, f"a 10-day-out event should not become a reminder, got: {gcal_alerts}")
    finally:
        gcal.GoogleCalendarClient = orig_cls


# ── create_calendar_event agent tool ────────────────────────────────────────
def test_create_calendar_event_tool_not_connected():
    result = server._execute_agent_tool("create_calendar_event", {"summary": "Test", "when": "2026-08-01"})
    check("error" in result, f"expected a clean error when not connected, got: {result}")
    check("not connected" in result["error"].lower(), f"error should explain not connected, got: {result}")


def test_create_calendar_event_tool_success():
    class _FakeClient:
        def create_event(self, summary, when, description=""):
            return {"id": "evt-created", "htmlLink": "https://calendar.google.com/evt-created"}

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _FakeClient
        result = server._execute_agent_tool("create_calendar_event", {"summary": "Dentist", "when": "2026-08-01"})
        check(result.get("created") is True, f"expected created=True, got: {result}")
        check(result.get("event_id") == "evt-created", f"expected the event id back, got: {result}")
    finally:
        gcal.GoogleCalendarClient = orig_cls


def test_create_calendar_event_tool_requires_summary_and_when():
    result = server._execute_agent_tool("create_calendar_event", {"summary": "", "when": ""})
    check("error" in result, f"missing required fields should error cleanly, got: {result}")


# ── _sync_calendar_to_google(): dedup ────────────────────────────────────────
def test_sync_calendar_dedups_across_runs():
    created_calls = []

    class _FakeClient:
        def __init__(self):
            self.refresh_token = "fake"

        def create_event(self, summary, when, description=""):
            created_calls.append(summary)
            return {"id": f"evt-{len(created_calls)}"}

    todo_id = db.add_todo(
        "Renew business license", added_by="scott", category="general",
        due_date=(date.today() + timedelta(days=3)).isoformat(),
    )

    orig_cls = gcal.GoogleCalendarClient
    try:
        gcal.GoogleCalendarClient = _FakeClient
        first = server._sync_calendar_to_google()
        check("synced" in first, f"first run should sync at least the new todo, got: {first}")
        first_count = len(created_calls)
        check(first_count >= 1, f"expected at least 1 event created on first sync, got {first_count}")

        second = server._sync_calendar_to_google()
        check(len(created_calls) == first_count,
              f"second run must not re-create already-synced items, "
              f"created {len(created_calls)} total after 2 runs (expected still {first_count})")
    finally:
        gcal.GoogleCalendarClient = orig_cls
        db.set_todo_done(todo_id, True)


def test_sync_calendar_not_connected_is_a_clean_noop():
    result = server._sync_calendar_to_google()
    check(result == "not connected", f"expected a clean 'not connected' status, got: {result}")


# ── weekly/monthly ops summary email ────────────────────────────────────────
def test_email_ops_summary_calls_send_brief():
    calls = []

    class _FakeDailyBrief:
        @staticmethod
        def _send_brief(subject, body):
            calls.append((subject, body))
            return True

    with patch.dict(sys.modules, {"daily_brief": _FakeDailyBrief}):
        server._email_ops_summary("Test Subject", "Test Body")
    check(len(calls) == 1, f"expected exactly 1 send, got: {calls}")
    check(calls[0] == ("Test Subject", "Test Body"), f"unexpected call args: {calls[0]}")


def test_email_ops_summary_tolerates_send_failure():
    class _BoomingDailyBrief:
        @staticmethod
        def _send_brief(subject, body):
            raise RuntimeError("SMTP exploded")

    with patch.dict(sys.modules, {"daily_brief": _BoomingDailyBrief}):
        try:
            server._email_ops_summary("Subject", "Body")
        except Exception as exc:
            _failures.append(f"_email_ops_summary must never raise, got: {exc}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("GOOGLE CALENDAR TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("GOOGLE CALENDAR TESTS OK — token/synced-event storage round-trips, the API "
          "client's not-connected/refresh/create-event behavior, /api/cadence and "
          "/api/alerts degrade cleanly and surface near-term events as reminders, "
          "the create_calendar_event tool works and errors cleanly, the daily "
          "auto-sync dedups across runs, and the ops-summary email helper calls "
          "_send_brief and tolerates a send failure.")


if __name__ == "__main__":
    run()
