"""
Test for the 2026-08-16 change to POST /api/todos/{id}/answer: answering a
question-category todo now auto-completes it (done=True) and kicks off a
real headless agent turn so Frank actually follows through, instead of the
answer just sitting in the ops runbook waiting for Frank to notice it on
some unrelated future turn.

Reversed on Scott's explicit instruction ("auto complete but still have
Frank finish it") from the prior deliberate design (2026-07-15: "answering
informs the next step, it doesn't mean the underlying task is resolved").

The background follow-up call itself is tested separately in
test_headless_agent_task.py / test_frank_can_do_loop.py -- this file checks
that answer_todo() (a) marks the todo done, (b) still writes the ops
runbook entry (unchanged, independent delivery channel), and (c) schedules
the real follow-up task rather than either skipping it or blocking the HTTP
response on it.

Run: python tests/test_todo_question_autocomplete.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_todo_autocomplete_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "todo-autocomplete-test-not-a-real-secret")

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


def test_answering_marks_the_todo_done():
    todo_id = db.add_todo("should we raise the price on DP1026?", category="question")
    with patch.object(server, "_process_answered_question", AsyncMock()), \
         patch.object(server, "_append_ops_runbook_entry"):
        result = asyncio.run(server.answer_todo(todo_id, {"answer": "Yes, to $16.99"}, _token="test"))
    check(result == {"ok": True}, f"got: {result}")
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["done"] == 1, "answering must mark the todo done -- Scott's own part of the loop is "
          "complete the moment he answers")
    check(row["answer"] == "Yes, to $16.99", "the answer itself must still be persisted")


def test_answering_schedules_the_real_followup_task_with_correct_args():
    todo_id = db.add_todo("is the printer allowed to run overnight?", category="question")
    followup_mock = AsyncMock()
    with patch.object(server, "_process_answered_question", followup_mock), \
         patch.object(server, "_append_ops_runbook_entry"):
        asyncio.run(server.answer_todo(todo_id, {"answer": "Yes, it's fine"}, _token="test"))
        # asyncio.create_task() schedules the coroutine but doesn't run it
        # synchronously -- give the event loop one tick so it actually starts.
        asyncio.run(asyncio.sleep(0))
    # AsyncMock() called via asyncio.create_task(mock(...)) records the call
    # immediately when the coroutine object is created, regardless of whether
    # it's finished executing yet.
    check(followup_mock.called, "answer_todo() must schedule _process_answered_question()")
    call_args = followup_mock.call_args
    check(call_args.args[0] == todo_id, f"must pass the real todo id, got {call_args.args}")
    check(call_args.args[2] == "Yes, it's fine", f"must pass the real answer text, got {call_args.args}")


def test_ops_runbook_entry_still_written_independent_of_the_followup_call():
    todo_id = db.add_todo("a third question", category="question")
    runbook_mock = patch.object(server, "_append_ops_runbook_entry")
    with patch.object(server, "_process_answered_question", AsyncMock()), runbook_mock as m:
        asyncio.run(server.answer_todo(todo_id, {"answer": "an answer"}, _token="test"))
    check(m.called, "the ops runbook entry must still be written -- it's an independent delivery "
          "channel (Scott can ask Frank 'why did you answer X' later) that shouldn't depend on the "
          "live follow-up call succeeding")


def test_empty_answer_is_rejected_before_touching_the_database():
    todo_id = db.add_todo("a question nobody answers", category="question")
    try:
        asyncio.run(server.answer_todo(todo_id, {"answer": "   "}, _token="test"))
        check(False, "an empty/whitespace-only answer must raise, not silently succeed")
    except Exception as e:
        check(getattr(e, "status_code", None) == 400, f"expected a 400, got: {e}")
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["done"] == 0, "a rejected empty answer must not mark the todo done")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TODO QUESTION AUTOCOMPLETE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TODO QUESTION AUTOCOMPLETE TESTS OK — answering a question-category todo marks it done, "
          "schedules the real headless follow-up task with the correct todo id/answer, still writes "
          "the independent ops-runbook entry, and rejects an empty answer before touching the db.")


if __name__ == "__main__":
    run()
