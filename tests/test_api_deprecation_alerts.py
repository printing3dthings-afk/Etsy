"""
Test for the 2026-08-15 API-shutdown-deadline dashboard alerts, added to
GET /api/alerts.

Context: OpenAI's Sora video API shuts down 2026-09-24 and gpt-image-1
shuts down 2026-10-23 -- both real, dated removals already documented in
tools/ai_video.py / tools/image_gen.py's own module comments, but neither
deadline was ever surfaced anywhere Scott would actually see it day to
day. get_alerts() now carries the same date-math + settings-flag pattern
already used for the credential-leak alerts: warning inside 75 days of the
deadline, critical inside 14 days (or once the deadline has passed),
silent otherwise, and permanently clearable via a single
db.set_setting(key, "1") call once the migration is actually confirmed
done -- not auto-cleared just because code changed, since "the veo path
exists" and "it's been proven against a live key" are different claims
(see ai_video.py's own "UNPROVEN" note).

Run: python tests/test_api_deprecation_alerts.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_api_deprecation_alerts_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "api-deprecation-alerts-test-not-a-real-secret")

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


def _get_alerts_on(today: date) -> dict:
    with patch.object(server, "_shop_today", return_value=today):
        return asyncio.run(server.get_alerts(_token="test"))


def _titles(result: dict) -> list[str]:
    return [a["title"] for a in result["alerts"]]


def test_no_alert_far_outside_the_warning_window():
    # 2026-07-01: Sora deadline is 85 days out, gpt-image-1 is 114 days out --
    # both outside the 75-day warning window, so neither should appear.
    db.set_setting("sora_migration_resolved", None)
    db.set_setting("gpt_image_1_migration_resolved", None)
    result = _get_alerts_on(date(2026, 7, 1))
    titles = " ".join(_titles(result))
    check("Sora" not in titles, f"Sora alert should not fire 85 days out: {titles}")
    check("gpt-image-1" not in titles, f"gpt-image-1 alert should not fire 114 days out: {titles}")


def test_warning_inside_75_days():
    # 2026-08-15 (the actual date this was built): Sora is 40 days out (warning),
    # gpt-image-1 is 69 days out (warning) -- both inside the 75-day window,
    # neither inside the 14-day critical window.
    result = _get_alerts_on(date(2026, 8, 15))
    sora = next((a for a in result["alerts"] if "Sora" in a["title"]), None)
    gpt = next((a for a in result["alerts"] if "gpt-image-1" in a["title"]), None)
    assert sora, f"expected a Sora deadline alert at 40 days out: {result['alerts']}"
    assert gpt, f"expected a gpt-image-1 deadline alert at 69 days out: {result['alerts']}"
    check(sora["severity"] == "warning", f"40 days out should be a warning, got {sora['severity']}")
    check(gpt["severity"] == "warning", f"69 days out should be a warning, got {gpt['severity']}")
    check("2026-09-24" in sora["title"], f"Sora alert should cite the real deadline date: {sora['title']}")
    check("2026-10-23" in gpt["title"], f"gpt-image-1 alert should cite the real deadline date: {gpt['title']}")
    check("veo" in sora["detail"], f"Sora remediation must name the veo migration path: {sora['detail']}")
    check("transparent" in gpt["detail"], f"gpt-image-1 remediation must name the transparent-bg risk: {gpt['detail']}")


def test_critical_inside_14_days_and_after_deadline_passes():
    result = _get_alerts_on(date(2026, 9, 15))  # 9 days before Sora's deadline
    sora = next((a for a in result["alerts"] if "Sora" in a["title"]), None)
    assert sora, f"expected a Sora alert 9 days out: {result['alerts']}"
    check(sora["severity"] == "critical", f"9 days out should be critical, got {sora['severity']}")

    result = _get_alerts_on(date(2026, 10, 1))  # 7 days after Sora's deadline passed
    sora = next((a for a in result["alerts"] if "Sora" in a["title"]), None)
    assert sora, f"expected the Sora alert to persist after its deadline passes: {result['alerts']}"
    check(sora["severity"] == "critical", "an alert for a deadline that already passed must be critical")
    check("ago" in sora["title"], f"a passed deadline should read as '... days ago', got: {sora['title']}")


def test_settings_flag_permanently_clears_the_alert():
    try:
        db.set_setting("sora_migration_resolved", "1")
        result = _get_alerts_on(date(2026, 9, 20))  # 4 days out -- would be critical otherwise
        titles = " ".join(_titles(result))
        check("Sora" not in titles,
              "once sora_migration_resolved is set, the alert must not fire even inside the critical window")
        # gpt-image-1's flag is independent -- clearing Sora's must not clear it too.
        gpt = next((a for a in result["alerts"] if "gpt-image-1" in a["title"]), None)
        check(gpt is not None, "clearing the Sora flag must not also silence the independent gpt-image-1 alert")
    finally:
        db.set_setting("sora_migration_resolved", None)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("API DEPRECATION ALERTS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("API DEPRECATION ALERTS TESTS OK — the Sora (2026-09-24) and gpt-image-1 (2026-10-23) "
          "shutdown deadlines now surface as dashboard alerts (silent >75 days out, warning inside "
          "75 days, critical inside 14 days or after the deadline passes), each independently "
          "clearable via its own db.set_setting() flag once the migration is actually confirmed done.")


if __name__ == "__main__":
    run()
