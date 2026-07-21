"""
Tests for the 2026-07-19 fix to _calendar_tasks_loop's aggregate heartbeat and
_daily_brief_loop's/POST /api/calendar-tasks/run + /api/brief/run's persisted
last-run-date handling.

Bugs fixed:
  1. _calendar_tasks_loop's aggregate heartbeat always reported "ok" regardless
     of whether any of its 9 sub-tasks failed -- each sub-task's `last_*` var
     and its `ran.append(...)` both live inside the try block, so a failure
     left both untouched and the heartbeat couldn't distinguish "nothing was
     due today" from "the one thing due today failed." A real failure on the
     one day it mattered rendered as "ok / no scheduled task due today" on the
     dashboard, completely hiding it. Now tracks `failed` explicitly and the
     aggregate status/detail can never claim "ok" when something failed.
  2. _daily_brief_loop's last_sent_date was a plain in-memory variable (the
     exact bug class _calendar_tasks_loop's own persistence was built to fix
     elsewhere, 2026-07-18) -- reintroduced here since this loop predates that
     fix. Now persisted via the same _get_calendar_task_last_run()/
     _set_calendar_task_last_run() helpers.
  3. Neither POST /api/calendar-tasks/run nor POST /api/brief/run touched the
     persisted last-run dates, so a manual trigger on the actual due day left
     the loop's own gate untouched -- guaranteed duplicate fire later that
     same day. Both endpoints now persist the same date keys the loops check.

Run: python tests/test_calendar_tasks_heartbeat_honesty.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_calheartbeat_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "calheartbeat-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "calheartbeattest"
os.environ["TEST_LOGIN_PASSWORD"] = "CalHeartbeatTest!2026Only"

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


def _calendar_tasks_heartbeat() -> dict | None:
    for h in db.list_agent_heartbeats():
        if h.get("name") == "calendar_tasks":
            return h
    return None


def test_daily_brief_last_sent_date_is_persisted():
    server._set_calendar_task_last_run("daily_brief", date(2020, 1, 1))
    check(server._get_calendar_task_last_run("daily_brief") == date(2020, 1, 1),
          "daily_brief's last-run date must round-trip through the persisted setting")


def test_run_one_calendar_tasks_iteration_with_a_failure_reports_error_not_ok():
    # Clear any prior state for the 5 date-independent ("daily") sub-tasks so
    # they're all guaranteed "due" this iteration regardless of what day this
    # test happens to run on.
    for key in ("ads_check", "star_seller_check", "art_check", "gcal_sync", "etsy_file_inventory"):
        db.set_setting(f"calendar_task_last_{key}", None)

    call_count = {"n": 0}

    async def _fake_sleep(_secs):
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise asyncio.CancelledError("stop after one iteration")

    with patch("asyncio.sleep", _fake_sleep), \
         patch.object(server, "_run_weekly_monitors", return_value=None), \
         patch.object(server, "_run_monthly_shop_health", return_value=None), \
         patch.object(server, "_run_art_authenticity_check", return_value=None), \
         patch.object(server, "_run_competitor_research_refresh", return_value="ok"), \
         patch.object(server, "_run_seasonal_keyword_check", return_value=None), \
         patch.object(server, "_check_ads_thresholds", side_effect=RuntimeError("simulated ads-check failure")), \
         patch.object(server, "_check_star_seller_status", return_value="fine"), \
         patch.object(server, "_run_scheduled_art_check", return_value="skipped"), \
         patch.object(server, "_sync_calendar_to_google", return_value="synced"), \
         patch.object(server, "_run_etsy_file_inventory_sweep", return_value="0 listings"):
        try:
            asyncio.run(server._calendar_tasks_loop())
        except asyncio.CancelledError:
            pass

    hb = _calendar_tasks_heartbeat()
    check(hb is not None, "calendar_tasks heartbeat row should exist after one iteration")
    check(hb["status"] == "error",
          f"a heartbeat with a real sub-task failure must report status='error', not 'ok': {hb}")
    check("FAILED" in hb["detail"] and "ads-check" in hb["detail"],
          f"the failure must be named in the detail, not hidden behind a generic 'ok': {hb['detail']}")
    check("simulated ads-check failure" in hb["detail"],
          f"the actual exception message should be visible in the detail: {hb['detail']}")


def test_run_one_calendar_tasks_iteration_all_success_reports_ok():
    for key in ("ads_check", "star_seller_check", "art_check", "gcal_sync", "etsy_file_inventory"):
        db.set_setting(f"calendar_task_last_{key}", None)

    call_count = {"n": 0}

    async def _fake_sleep(_secs):
        call_count["n"] += 1
        if call_count["n"] >= 2:
            raise asyncio.CancelledError("stop after one iteration")

    with patch("asyncio.sleep", _fake_sleep), \
         patch.object(server, "_run_weekly_monitors", return_value=None), \
         patch.object(server, "_run_monthly_shop_health", return_value=None), \
         patch.object(server, "_run_art_authenticity_check", return_value=None), \
         patch.object(server, "_run_competitor_research_refresh", return_value="ok"), \
         patch.object(server, "_run_seasonal_keyword_check", return_value=None), \
         patch.object(server, "_check_ads_thresholds", return_value="fine"), \
         patch.object(server, "_check_star_seller_status", return_value="fine"), \
         patch.object(server, "_run_scheduled_art_check", return_value="skipped"), \
         patch.object(server, "_sync_calendar_to_google", return_value="synced"), \
         patch.object(server, "_run_etsy_file_inventory_sweep", return_value="0 listings"):
        try:
            asyncio.run(server._calendar_tasks_loop())
        except asyncio.CancelledError:
            pass

    hb = _calendar_tasks_heartbeat()
    check(hb is not None, "calendar_tasks heartbeat row should exist after one iteration")
    check(hb["status"] == "ok", f"an iteration with no failures must report status='ok': {hb}")
    check("FAILED" not in hb["detail"], f"detail should not mention FAILED when nothing failed: {hb['detail']}")


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(r.status_code in (302, 303), f"login should redirect, got {r.status_code}")
    return c


def test_manual_calendar_tasks_endpoint_persists_last_run_dates():
    for key in ("ads_check", "star_seller_check", "art_check"):
        db.set_setting(f"calendar_task_last_{key}", None)
    with patch.object(server, "_run_weekly_monitors", return_value="ok"), \
         patch.object(server, "_run_monthly_shop_health", return_value="ok"), \
         patch.object(server, "_run_competitor_research_refresh", return_value="ok"), \
         patch.object(server, "_run_seasonal_keyword_check", return_value="ok"), \
         patch.object(server, "_check_ads_thresholds", return_value="ok"), \
         patch.object(server, "_run_scheduled_art_check", return_value="ok"), \
         patch.object(server, "_check_star_seller_status", side_effect=RuntimeError("boom")):
        r = server.app.router  # touch to ensure app is importable; real call below
        resp = _logged_in_client().post("/api/calendar-tasks/run", headers={"X-App-Token": server.APP_TOKEN})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:300]}")
    body = resp.json()
    check(body.get("ads_threshold") == "ok", f"got: {body}")
    check(str(body.get("star_seller", "")).startswith("ERROR:"), f"got: {body}")

    today = date.today()
    check(server._get_calendar_task_last_run("ads_check") == today,
          "a successfully-triggered task must persist today's date so the loop doesn't duplicate-fire it later")
    check(server._get_calendar_task_last_run("star_seller_check") != today,
          "a task that raised must NOT have its last-run date advanced -- it didn't actually complete")


def test_manual_brief_endpoint_persists_last_sent_date():
    db.set_setting("calendar_task_last_daily_brief", None)
    with patch("daily_brief.run_daily_brief", return_value="sent"):
        resp = _logged_in_client().post("/api/brief/run", headers={"X-App-Token": server.APP_TOKEN})
    check(resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text[:300]}")
    check(server._get_calendar_task_last_run("daily_brief") == date.today(),
          "triggering the brief manually must persist today's date so the loop's own 6am check "
          "doesn't send a duplicate later the same day")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CALENDAR TASKS HEARTBEAT HONESTY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CALENDAR TASKS HEARTBEAT HONESTY TESTS OK — a sub-task failure now reports heartbeat "
          "status='error' with the failure named (never a false 'ok'), a fully-successful iteration "
          "still reports 'ok', daily_brief's last-sent-date persists across restarts, and both manual "
          "trigger endpoints (calendar-tasks/run, brief/run) correctly sync the loops' own gates so a "
          "manual test-run can't cause a same-day duplicate fire.")


if __name__ == "__main__":
    run()
