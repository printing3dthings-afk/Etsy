"""The external Etsy token watch (2026-10-23).

The connection died silently in October 2026: Frank's own 75-day warning was a
to-do and an alert-bell entry nobody saw. tools/ci_check_etsy_token.py checks
from GitHub Actions and opens an issue Scott is emailed about. These pin when
it speaks: Etsy not live, 14 days before the 90-day limit, and no rotation date.
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import ci_check_etsy_token as w  # noqa: E402

_failures: list[str] = []
NOW = datetime(2026, 10, 23, 14, 5, tzinfo=timezone.utc)


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _status(age_days, live=True, err=None):
    return {"etsy_live": live, "etsy_live_error": err,
            "etsy_tokens_updated_at": (NOW - timedelta(days=age_days)).isoformat() if age_days is not None else None}


def test_quiet_while_fresh():
    problems, facts = w.assess(_status(75), NOW, 14)
    check(problems == [], f"75 days, live: expected no alert, got {problems}")
    check(facts["age_days"] == 75, f"age should be 75, got {facts['age_days']}")


def test_alerts_fourteen_days_before_the_limit():
    problems, _ = w.assess(_status(76), NOW, 14)
    check(len(problems) == 1 and "14 days left" in problems[0], f"day 76 must warn with 14 days left: {problems}")


def test_alerts_when_etsy_is_not_live_even_if_recent():
    problems, _ = w.assess(_status(3, live=False, err="401 invalid_grant"), NOW, 14)
    check(any("not live" in p and "invalid_grant" in p for p in problems), f"a dead connection must alert: {problems}")


def test_alerts_without_a_rotation_date():
    problems, _ = w.assess(_status(None), NOW, 14)
    check(any("no record" in p for p in problems), f"a missing rotation date must alert: {problems}")


def test_naive_timestamps_are_utc():
    s = _status(80)
    s["etsy_tokens_updated_at"] = s["etsy_tokens_updated_at"].replace("+00:00", "")
    problems, facts = w.assess(s, NOW, 14)
    check(facts["age_days"] == 80 and problems, f"a naive timestamp must still count: {facts} {problems}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("ETSY TOKEN WATCH TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("ETSY TOKEN WATCH TESTS OK — alerts when Etsy is down, 14 days before the 90-day limit, "
          "and when no rotation date exists; quiet otherwise.")


if __name__ == "__main__":
    run()
