"""
Test for _append_ops_runbook_entry()'s same-day dedup guard (2026-07-18).

Before this fix, every health-loop failure path funneled through
_append_ops_runbook_entry() with zero dedup -- an unresolved, unchanged
failure firing every 5 minutes turned into hundreds of byte-identical
entries for a single issue (confirmed: 428/821 dated entries in the
committed ops_runbook.md were one repeated escalation before cleanup).

Checks:
  1. Calling _append_ops_runbook_entry() twice, same day, same heading,
     only writes one entry to the file.
  2. A different heading on the same day still gets its own entry (the
     guard is heading-specific, not a blanket "one entry per day" cap).
  3. The same heading on a DIFFERENT day gets a new entry (only same-day
     duplicates are suppressed -- genuine day-over-day recurrence still
     surfaces via _promote_recurring_failures()'s summary).

Run: python tests/test_ops_runbook_dedup.py
"""
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_runbookdedup_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "runbookdedup-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _heading_count(text: str, heading: str) -> int:
    return text.count(f"— {heading}\n")


def test_same_day_same_heading_dedups():
    tmp = tempfile.NamedTemporaryFile(prefix="ops_runbook_dedup_", suffix=".md", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.write_text("# Ops Runbook\n\nSeed content.\n")
    orig_path = server._OPS_RUNBOOK_PATH
    try:
        server._OPS_RUNBOOK_PATH = path
        server._append_ops_runbook_entry("Escalation — test failure X", "First occurrence.")
        server._append_ops_runbook_entry("Escalation — test failure X", "Second occurrence, unresolved.")
        server._append_ops_runbook_entry("Escalation — test failure X", "Third occurrence, still unresolved.")
        text = path.read_text()
        check(_heading_count(text, "Escalation — test failure X") == 1,
              f"expected exactly 1 entry for the repeated same-day heading, got {_heading_count(text, 'Escalation — test failure X')}\n{text}")
        check("First occurrence." in text, "the first (only kept) occurrence's body should be present")
    finally:
        server._OPS_RUNBOOK_PATH = orig_path
        path.unlink(missing_ok=True)


def test_same_day_different_heading_both_kept():
    tmp = tempfile.NamedTemporaryFile(prefix="ops_runbook_dedup_", suffix=".md", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.write_text("# Ops Runbook\n\nSeed content.\n")
    orig_path = server._OPS_RUNBOOK_PATH
    try:
        server._OPS_RUNBOOK_PATH = path
        server._append_ops_runbook_entry("Escalation — failure A", "body A")
        server._append_ops_runbook_entry("Escalation — failure B", "body B")
        text = path.read_text()
        check(_heading_count(text, "Escalation — failure A") == 1, "failure A should have its own entry")
        check(_heading_count(text, "Escalation — failure B") == 1, "failure B should have its own entry")
    finally:
        server._OPS_RUNBOOK_PATH = orig_path
        path.unlink(missing_ok=True)


def test_same_heading_different_day_gets_new_entry():
    tmp = tempfile.NamedTemporaryFile(prefix="ops_runbook_dedup_", suffix=".md", delete=False)
    tmp.close()
    path = Path(tmp.name)
    yesterday = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
    path.write_text(f"# Ops Runbook\n\n## {yesterday} — Escalation — recurring failure Y\nYesterday's body.\n")
    orig_path = server._OPS_RUNBOOK_PATH
    try:
        server._OPS_RUNBOOK_PATH = path
        server._append_ops_runbook_entry("Escalation — recurring failure Y", "Today's body, still unresolved.")
        text = path.read_text()
        check(_heading_count(text, "Escalation — recurring failure Y") == 2,
              f"a new day should get its own entry even for a recurring heading, got {_heading_count(text, 'Escalation — recurring failure Y')}\n{text}")
    finally:
        server._OPS_RUNBOOK_PATH = orig_path
        path.unlink(missing_ok=True)


def test_missing_file_creates_it():
    tmp_dir = tempfile.mkdtemp(prefix="ops_runbook_dedup_dir_")
    path = Path(tmp_dir) / "does_not_exist_yet.md"
    orig_path = server._OPS_RUNBOOK_PATH
    try:
        server._OPS_RUNBOOK_PATH = path
        server._append_ops_runbook_entry("Escalation — first ever failure", "body")
        check(path.exists(), "appending to a nonexistent runbook file should create it")
        check("Escalation — first ever failure" in path.read_text(), "the entry should be written")
    finally:
        server._OPS_RUNBOOK_PATH = orig_path


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("OPS RUNBOOK DEDUP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("OPS RUNBOOK DEDUP TESTS OK — same-day/same-heading duplicates are suppressed, "
          "different headings and different days still get their own entries, and a "
          "missing runbook file is created on first append.")


if __name__ == "__main__":
    run()
