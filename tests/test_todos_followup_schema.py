"""
Test for the 2026-08-16 Tasks screen rebuild's new db.py schema/functions:
follow_up/follow_up_at/attempt_count/needs_attention on the todos table, and
the three new functions that manage them (set_todo_follow_up,
bump_todo_attempt, list_open_frank_can_do_todos).

Context: Scott asked for two things -- (1) answering a question-category
todo should auto-complete it but Frank should still really follow through
on the answer, and (2) frank_can_do todos should be worked by a real
background queue with retries capped and escalated to Scott rather than
silently retried forever or dropped. These columns/functions are the
durable state that makes both possible: follow_up is Frank's own summary
of what it did (shown in the UI), attempt_count/needs_attention let the
background loop cap retries and flag a stuck task.

Run: python tests/test_todos_followup_schema.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_todos_followup_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_new_columns_exist_and_default_correctly():
    todo_id = db.add_todo("test task for schema check", category="frank_can_do")
    todos = db.list_todos()
    row = next(t for t in todos if t["id"] == todo_id)
    check(row["follow_up"] is None, f"follow_up should default to NULL, got {row['follow_up']!r}")
    check(row["follow_up_at"] is None, f"follow_up_at should default to NULL, got {row['follow_up_at']!r}")
    check(row["attempt_count"] == 0, f"attempt_count should default to 0, got {row['attempt_count']!r}")
    check(row["needs_attention"] == 0, f"needs_attention should default to 0, got {row['needs_attention']!r}")


def test_set_todo_follow_up_stores_and_timestamps():
    todo_id = db.add_todo("another test task", category="question")
    ok = db.set_todo_follow_up(todo_id, "Frank checked the account and it's already fixed.")
    check(ok, "set_todo_follow_up should return True for a real todo id")
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["follow_up"] == "Frank checked the account and it's already fixed.",
          f"follow_up should be stored verbatim, got {row['follow_up']!r}")
    check(bool(row["follow_up_at"]), "follow_up_at must be set once a follow-up is recorded")
    check(db.set_todo_follow_up(999999, "x") is False, "must return False for a nonexistent todo id")


def test_bump_todo_attempt_increments_and_can_set_needs_attention():
    todo_id = db.add_todo("frank can do task", category="frank_can_do")
    db.bump_todo_attempt(todo_id)
    db.bump_todo_attempt(todo_id)
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["attempt_count"] == 2, f"expected attempt_count == 2 after two bumps, got {row['attempt_count']}")
    check(row["needs_attention"] == 0, "needs_attention should still be 0 -- never asked to set it")

    db.bump_todo_attempt(todo_id, needs_attention=True)
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["attempt_count"] == 3, f"expected attempt_count == 3, got {row['attempt_count']}")
    check(row["needs_attention"] == 1, "needs_attention must be set to 1 once the escalation call is made")

    # A later bump without needs_attention=True must not clear it back to 0 --
    # only a real completion should take a task out of the "needs attention" state.
    db.bump_todo_attempt(todo_id)
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["needs_attention"] == 1, "needs_attention must stay set once escalated, not silently clear")


def test_list_open_frank_can_do_todos_filters_correctly():
    # Fresh ids in this test to avoid interference from earlier tests' rows.
    open_low_attempts = db.add_todo("open, few attempts", category="frank_can_do")
    open_maxed_out = db.add_todo("open, maxed out attempts", category="frank_can_do")
    for _ in range(3):
        db.bump_todo_attempt(open_maxed_out)
    done_one = db.add_todo("already done", category="frank_can_do")
    db.set_todo_done(done_one, True)
    wrong_category = db.add_todo("general task, not frank_can_do", category="general")

    result_ids = {t["id"] for t in db.list_open_frank_can_do_todos(max_attempts=3, limit=50)}
    check(open_low_attempts in result_ids, "an open, under-the-cap frank_can_do todo must be included")
    check(open_maxed_out not in result_ids,
          "a frank_can_do todo already at max_attempts must be excluded -- the loop should stop "
          "retrying it automatically once escalated")
    check(done_one not in result_ids, "a completed todo must never be returned for re-processing")
    check(wrong_category not in result_ids, "a non-frank_can_do todo must never be returned")


def test_set_todo_answer_still_only_touches_answer_fields():
    # 2026-08-16: set_todo_answer's own job stays narrow (just persist the
    # answer) -- auto-completion is the caller's (the API endpoint's)
    # responsibility, not baked into this function. Regression guard against
    # accidentally re-coupling them here.
    todo_id = db.add_todo("a question", category="question")
    db.set_todo_answer(todo_id, "the real answer")
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["answer"] == "the real answer", "answer must be stored")
    check(row["done"] == 0,
          "set_todo_answer() itself must NOT mark the todo done -- that's the API endpoint's job, "
          "so calling this function directly (e.g. from a test or a future caller) can never "
          "silently auto-complete something without going through the real endpoint's full flow")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TODOS FOLLOWUP SCHEMA TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TODOS FOLLOWUP SCHEMA TESTS OK — follow_up/attempt_count/needs_attention persist and "
          "default correctly, bump_todo_attempt increments and escalates without ever silently "
          "clearing needs_attention, list_open_frank_can_do_todos correctly excludes done/maxed-out/"
          "wrong-category rows, and set_todo_answer's own scope stays narrow.")


if __name__ == "__main__":
    run()
