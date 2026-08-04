"""
Calendar screen audit fixes (2026-08-04).

Covers:
- _shop_today()/_shop_now(): read Settings' user_profile.timezone and compute
  "today" in the shop's local zone, not the server's (Railway defaults to
  UTC -- no TZ env var anywhere in this repo's deploy config). Falls back to
  _SHOP_TZ_FALLBACK when unset or invalid.
- GET /api/cadence now filters tax_deadlines to today-or-later, matching the
  seasonal-keyword block's existing filter and _sync_calendar_to_google()'s
  independent filter -- previously past deadlines sat as permanent "OVERDUE"
  cards for roughly 8 of 12 months a year.

Mocks the narrowest real dependency (db.get_user_profile,
tax_compliance_tools._get_tax_calendar) so this never touches a real Etsy/
Google Calendar call. Same pattern as tests/test_workflows_screen.py.
"""
import asyncio
import json
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_calendar_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "calendar-test-not-a-real-secret")

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


def _fake_tax_calendar(dates_and_events):
    def _fn():
        return json.dumps({"tax_deadlines": [{"date": d, "event": e} for d, e in dates_and_events]})
    return _fn


def test_shop_today_uses_settings_timezone():
    db.save_user_profile(None, None, None, "America/Los_Angeles")
    result = server._shop_today()
    check(isinstance(result, date), f"expected a date, got: {result!r}")
    # America/Los_Angeles is UTC-7/8, so its local date can legitimately
    # differ from a bare UTC date.today() near the day boundary -- just
    # confirm the timezone was actually read and used, not that it produced
    # a specific value (that would be a flaky test depending on wall-clock time).
    with patch.object(db, "get_user_profile", return_value={"timezone": "America/Los_Angeles"}) as mock_profile:
        server._shop_today()
    check(mock_profile.called, "expected _shop_today to consult db.get_user_profile()")


def test_shop_today_falls_back_when_timezone_unset():
    db.save_user_profile(None, None, None, None)
    result = server._shop_today()
    check(isinstance(result, date), f"expected a fallback date, not an exception, got: {result!r}")


def test_shop_today_falls_back_when_timezone_invalid():
    db.save_user_profile(None, None, None, "Not/A/Real/Zone")
    result = server._shop_today()
    check(isinstance(result, date), f"expected graceful fallback for a garbage timezone, got: {result!r}")


def test_cadence_filters_past_tax_deadlines():
    db.save_user_profile(None, None, None, "America/New_York")
    fixed_today = date(2026, 8, 4)
    fixture = _fake_tax_calendar([
        ("Jan 15, 2026", "Q4 estimated tax payment due (from prior year)"),
        ("Jan 31, 2026", "Etsy sends 1099-K forms (if applicable)"),
        ("Apr 15, 2026", "Federal tax return due + Q1 estimated tax payment"),
        ("Jun 17, 2026", "Q2 estimated tax payment due"),
        ("Sep 16, 2026", "Q3 estimated tax payment due"),
        ("Jan 15, 2027", "Q4 estimated tax payment due"),
    ])
    with patch.object(server, "_shop_today", return_value=fixed_today), \
         patch.object(server.tax_compliance_tools, "_get_tax_calendar", side_effect=fixture):
        result = asyncio.run(server.get_cadence(_token="test"))
    dates = [t["date_iso"] for t in result["tax_deadlines"]]
    check("2026-01-15" not in dates, f"Jan 15 2026 (past) must be filtered out, got: {dates}")
    check("2026-01-31" not in dates, f"Jan 31 2026 (past) must be filtered out, got: {dates}")
    check("2026-04-15" not in dates, f"Apr 15 2026 (past) must be filtered out, got: {dates}")
    check("2026-06-17" not in dates, f"Jun 17 2026 (past) must be filtered out, got: {dates}")
    check("2026-09-16" in dates, f"Sep 16 2026 (future) must still be present, got: {dates}")
    check("2027-01-15" in dates, f"Jan 15 2027 (future) must still be present, got: {dates}")
    check(len(dates) == 2, f"expected exactly 2 future deadlines to survive filtering, got {len(dates)}: {dates}")


def test_cadence_keeps_a_deadline_due_exactly_today():
    db.save_user_profile(None, None, None, "America/New_York")
    fixed_today = date(2026, 8, 4)
    fixture = _fake_tax_calendar([("Aug 4, 2026", "Due exactly today")])
    with patch.object(server, "_shop_today", return_value=fixed_today), \
         patch.object(server.tax_compliance_tools, "_get_tax_calendar", side_effect=fixture):
        result = asyncio.run(server.get_cadence(_token="test"))
    dates = [t["date_iso"] for t in result["tax_deadlines"]]
    check("2026-08-04" in dates, f"a deadline due exactly today must not be filtered out, got: {dates}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CALENDAR SCREEN TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CALENDAR SCREEN TESTS OK — shop-timezone helper and tax-deadline "
          "past-date filtering are both verified.")


if __name__ == "__main__":
    run()
