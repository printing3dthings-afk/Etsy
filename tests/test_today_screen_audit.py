"""
Today screen second-pass audit (2026-08-06), prompted by Scott: "See what
needs fixed and what can be added to make it easier and more capable. We
need to get the small details taken care of."

This screen (mobile pp-today / renderPhoneToday()) had already been through
one full audit-and-build pass earlier in the project. A second, deeper pass
found several real gaps the first pass missed -- this file covers the
backend half of those fixes (the residual UTC-vs-shop-local timezone bug in
functions that gate Today-adjacent nudges/dedup, matching the 2026-08-04
_shop_today() fix that was applied to /api/alerts but not these):

  1. _check_star_seller_status()'s weekly nudge-cooldown gate
  2. _check_ads_thresholds()'s quarterly "ads never used" nudge gate and its
     week/month spend windowing
  3. _compute_ads_status()'s week/month spend windowing (must never disagree
     with #2's windowing about what "this week" means -- see that function's
     own docstring)
  4. POST /api/calendar-tasks/run's persisted last-run date (must match
     _calendar_tasks_loop's own shop-local gate, or a near-midnight manual
     trigger can duplicate-run the same task the loop fires again the same
     day)
  5. POST /api/brief/run's persisted last-sent date (same reasoning, against
     _daily_brief_loop's gate)

The frontend half (fetch-failure honesty, badge drift, Star Seller at_risk
representation, reviews-awaiting-reply, the recently-fixed reassurance card
reaching Today, the draft_unpublished wrong-fix-action bug) is pure
JS/renderPhoneToday() and covered by tools/playwright_smoke.py instead.

Run: python tests/test_today_screen_audit.py
"""
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_today_audit_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "today-audit-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_check_star_seller_status_uses_shop_local_today():
    fixed_today = date(2026, 8, 6)
    with patch.object(server, "_shop_today", return_value=fixed_today) as mock_today, \
         patch.object(server, "_compute_star_seller_status",
                       return_value={"status": "at_risk", "orders_90d": 2, "revenue_90d": 100.0,
                                      "unread_messages": 0}):
        db.set_setting("star_seller_at_risk_nudge_date", None)
        result = server._check_star_seller_status()
    check(mock_today.called, "expected _check_star_seller_status to call _shop_today(), not bare date.today()")
    check(db.get_setting("star_seller_at_risk_nudge_date") == fixed_today.isoformat(),
          f"expected the nudge date stamped with the shop-local date, got {db.get_setting('star_seller_at_risk_nudge_date')!r}")
    check("todo added" in result, f"expected a todo to be added for a fresh at_risk status, got {result!r}")


def test_check_ads_thresholds_never_used_branch_uses_shop_local_today():
    fixed_today = date(2026, 8, 6)
    fake_store = MagicMock()
    fake_store.get.return_value = {}
    with patch.object(server, "_shop_today", return_value=fixed_today) as mock_today, \
         patch("data_store.DataStore", return_value=fake_store):
        db.set_setting("ads_never_used_nudge_date", None)
        result = server._check_ads_thresholds()
    check(mock_today.called, "expected _check_ads_thresholds to call _shop_today(), not bare date.today()")
    check(db.get_setting("ads_never_used_nudge_date") == fixed_today.isoformat(),
          f"expected the nudge date stamped with the shop-local date, got {db.get_setting('ads_never_used_nudge_date')!r}")
    check("nudge added" in result, f"expected the quarterly nudge to fire on a fresh install, got {result!r}")


def test_check_ads_thresholds_windowing_uses_shop_local_today():
    fixed_today = date(2026, 8, 6)
    fake_store = MagicMock()
    fake_store.get.return_value = {"spend_log": [
        {"date": "2026-08-05", "spend_usd": 5.0, "revenue_from_ads": 0},
    ]}
    with patch.object(server, "_shop_today", return_value=fixed_today) as mock_today, \
         patch("data_store.DataStore", return_value=fake_store):
        server._check_ads_thresholds()
    check(mock_today.called, "expected the week/month windowing branch to call _shop_today() too")


def test_compute_ads_status_uses_shop_local_today():
    fixed_today = date(2026, 8, 6)
    fake_store = MagicMock()
    fake_store.get.return_value = {"spend_log": [
        {"date": "2026-08-05", "spend_usd": 5.0, "revenue_from_ads": 10.0},
    ]}
    with patch.object(server, "_shop_today", return_value=fixed_today) as mock_today, \
         patch("data_store.DataStore", return_value=fake_store):
        out = server._compute_ads_status()
    check(mock_today.called,
          "expected _compute_ads_status to call _shop_today() -- it must never disagree with "
          "_check_ads_thresholds() about what 'this week' means (see that function's own docstring)")
    check(out.get("used") is True, f"expected a real spend_log to report used=True, got {out}")


def test_calendar_tasks_run_endpoint_persists_shop_local_date():
    import asyncio
    fixed_today = date(2026, 8, 6)
    fake_request = MagicMock()
    fake_request.headers.get.return_value = server.APP_TOKEN
    with patch.object(server, "_shop_today", return_value=fixed_today), \
         patch.object(server, "_run_weekly_monitors", return_value="ok"), \
         patch.object(server, "_run_monthly_shop_health", return_value="ok"), \
         patch.object(server, "_run_competitor_research_refresh", return_value="ok"), \
         patch.object(server, "_run_seasonal_keyword_check", return_value="ok"), \
         patch.object(server, "_check_ads_thresholds", return_value="ok"), \
         patch.object(server, "_run_scheduled_art_check", return_value="ok"), \
         patch.object(server, "_check_star_seller_status", return_value="ok"), \
         patch.object(server, "_set_calendar_task_last_run") as mock_set:
        asyncio.run(server.run_calendar_tasks_now(fake_request))
    stamped_dates = {call.args[1] for call in mock_set.call_args_list}
    check(stamped_dates == {fixed_today},
          f"expected every task's last-run date stamped with the shop-local today ({fixed_today}), got {stamped_dates}")


def test_brief_run_endpoint_persists_shop_local_date():
    import asyncio
    fixed_today = date(2026, 8, 6)
    fake_request = MagicMock()
    fake_request.headers.get.return_value = server.APP_TOKEN
    fake_daily_brief = MagicMock()
    fake_daily_brief.run_daily_brief.return_value = "sent"
    with patch.object(server, "_shop_today", return_value=fixed_today), \
         patch.dict(sys.modules, {"daily_brief": fake_daily_brief}), \
         patch.object(server, "_set_calendar_task_last_run") as mock_set:
        asyncio.run(server.run_brief_now(fake_request))
    check(mock_set.called, "expected _set_calendar_task_last_run to be called")
    stamped = mock_set.call_args.args
    check(stamped == ("daily_brief", fixed_today),
          f"expected ('daily_brief', {fixed_today}) stamped, got {stamped}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TODAY SCREEN AUDIT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TODAY SCREEN AUDIT TESTS OK — every Today-adjacent nudge/dedup gate "
          "(Star Seller cooldown, ads thresholds, ads status windowing, calendar-tasks "
          "manual trigger, daily-brief manual trigger) now reads shop-local \"today\" via "
          "_shop_today() instead of bare date.today(), matching the 2026-08-04 fix already "
          "applied to /api/alerts and _calendar_tasks_loop.")


if __name__ == "__main__":
    run()
