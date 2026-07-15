#!/usr/bin/env python3
"""
Fixture-based test for tools/api_server/db.py's Ranking Recovery cooldown
tracker (2026-07-15) -- CLAUDE.md's Ranking Recovery Playbook warns against
editing a listing again inside its ~2-3 week ranking recovery window.
note_listing_edited() records when a content-mutating action last executed;
enqueue_action() reads it back and prepends a warning to the staged
summary if a new content-mutating action is staged too soon after.

Uses a throwaway temp SQLite DB (DB_PATH env var, set before importing db)
so this never touches the real dev database. No network, no live Etsy.

Run locally:  python tests/test_db_ranking_recovery.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_test_ranking_recovery_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name

import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _reset():
    db.init_db()
    conn = db._connect()
    try:
        conn.execute("DELETE FROM action_queue")
        conn.execute("DELETE FROM settings")
        conn.commit()
    finally:
        conn.close()
    db._settings_cache.clear()


def test_no_warning_for_a_never_edited_listing():
    _reset()
    qid = db.enqueue_action("update_title", "Update title", {"listing_id": 111, "title": "New Title"})
    row = db.get_action(qid)
    check("⚠️" not in row["summary"], f"a never-edited listing should get no cooldown warning, got: {row['summary']!r}")


def test_warning_when_edited_recently():
    _reset()
    db.note_listing_edited(222)
    qid = db.enqueue_action("update_tags", "Update tags", {"listing_id": 222, "tags": ["a", "b"]})
    row = db.get_action(qid)
    check("⚠️" in row["summary"] and "0d ago" in row["summary"],
          f"expected a same-day cooldown warning, got: {row['summary']!r}")


def test_no_warning_once_outside_cooldown_window():
    _reset()
    # Simulate an edit 30 days ago (outside the 21-day window) by writing the
    # setting directly rather than waiting -- note_listing_edited() always
    # stamps "now", so this bypasses it deliberately for the test.
    old_ts = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    db.set_setting(db._listing_last_edited_key(333), old_ts)
    qid = db.enqueue_action("update_description", "Update description", {"listing_id": 333, "description": "..."})
    row = db.get_action(qid)
    check("⚠️" not in row["summary"], f"a 30-day-old edit is outside the 21-day window, got: {row['summary']!r}")


def test_warning_right_at_the_boundary():
    _reset()
    ts_20d = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()
    db.set_setting(db._listing_last_edited_key(444), ts_20d)
    qid = db.enqueue_action("update_title", "Update title", {"listing_id": 444, "title": "X"})
    row = db.get_action(qid)
    check("⚠️" in row["summary"], f"20 days is still inside the 21-day window, expected a warning, got: {row['summary']!r}")


def test_no_cooldown_check_for_non_content_types():
    _reset()
    db.note_listing_edited(555)
    qid = db.enqueue_action("deactivate_listing", "Deactivate", {"listing_id": 555})
    row = db.get_action(qid)
    check("⚠️" not in row["summary"],
          f"deactivate_listing isn't a content edit -- no cooldown check should apply, got: {row['summary']!r}")


def test_missing_listing_id_does_not_crash():
    _reset()
    qid = db.enqueue_action("update_tags", "Update tags", {"tags": ["a"]})  # no listing_id
    row = db.get_action(qid)
    check(row is not None, "enqueue_action must not raise when payload has no listing_id")
    check("⚠️" not in row["summary"], "no listing_id -- nothing to check against, no warning expected")


def test_malformed_timestamp_does_not_crash():
    _reset()
    db.set_setting(db._listing_last_edited_key(666), "not-a-real-timestamp")
    qid = db.enqueue_action("update_title", "Update title", {"listing_id": 666, "title": "X"})
    row = db.get_action(qid)
    check(row is not None, "enqueue_action must not raise on a malformed stored timestamp")
    check("⚠️" not in row["summary"], "malformed timestamp -- fail open (no warning), not a crash")


def test_note_listing_edited_persists_across_setting_cache():
    _reset()
    db.note_listing_edited(777)
    stored = db.get_setting(db._listing_last_edited_key(777))
    check(stored is not None, "note_listing_edited should persist a value get_setting can read back")
    parsed = datetime.fromisoformat(stored)
    check((datetime.now(timezone.utc) - parsed).total_seconds() < 60,
          f"the stamped timestamp should be ~now, got {stored!r}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception:
            _failures.append(f"{t.__name__} raised an unexpected error:\n" + traceback.format_exc())
    try:
        os.unlink(_tmp_db.name)
    except OSError:
        pass
    if _failures:
        print("RANKING RECOVERY COOLDOWN TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"RANKING RECOVERY COOLDOWN TESTS OK — {ran} tests passed "
          f"(db.enqueue_action()'s cooldown-warning logic, via a throwaway temp DB).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
