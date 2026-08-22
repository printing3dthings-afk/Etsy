"""
Test for the 2026-08-16 Tasks screen rebuild's frank_can_do background
queue: _attempt_frank_can_do_todo(), _frank_can_do_iteration(), and the
POST /api/todos/{id}/run-now manual-trigger endpoint.

Context: Scott's explicit ask was "background queue but make sure it gets
done" -- these tests focus on the retry/escalation guarantee specifically:
a task that Frank can't complete keeps getting real follow_up notes (never
silent), attempt_count increments on every non-completing attempt, and
needs_attention flips on once the cap is hit so a genuinely-stuck task
surfaces to Scott instead of retrying forever or silently vanishing.

_run_headless_agent_task itself is mocked here (already covered end to end
in test_headless_agent_task.py) -- these tests are about the retry/
escalation logic layered on top of it, not the underlying agent call.

Run: python tests/test_frank_can_do_loop.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_can_do_loop_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "frank-can-do-test-not-a-real-secret")

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


def _todo_row(todo_id: int) -> dict:
    return next(t for t in db.list_todos() if t["id"] == todo_id)


def test_successful_completion_records_followup_without_bumping_attempts():
    todo_id = db.add_todo("check the printer filament level", category="frank_can_do")

    async def fake_headless(prompt):
        db.set_todo_done(todo_id, True)  # simulates the model calling complete_todo
        return "Checked the printer — plenty of filament left, marked this done."

    with patch.object(server, "_run_headless_agent_task", fake_headless):
        asyncio.run(server._attempt_frank_can_do_todo(_todo_row(todo_id)))

    row = _todo_row(todo_id)
    check(row["done"] == 1, "the todo should end up done once the agent actually completed it")
    check("plenty of filament" in (row["follow_up"] or ""), f"follow_up should record what happened: {row['follow_up']!r}")
    check(row["attempt_count"] == 0, "a real completion shouldn't count as a failed attempt")


def test_attempt_without_completion_bumps_attempt_count():
    todo_id = db.add_todo("stage a price update for review", category="frank_can_do")

    async def fake_headless(prompt):
        return "Staged a price update for Scott's approval — see Approvals."

    with patch.object(server, "_run_headless_agent_task", fake_headless):
        asyncio.run(server._attempt_frank_can_do_todo(_todo_row(todo_id)))

    row = _todo_row(todo_id)
    check(row["done"] == 0, "staging an action for approval must NOT mark the todo done -- it "
          "isn't actually finished until Scott approves it")
    check("Staged a price update" in (row["follow_up"] or ""), f"got: {row['follow_up']!r}")
    check(row["attempt_count"] == 1, f"expected attempt_count == 1, got {row['attempt_count']}")
    check(row["needs_attention"] == 0, "one attempt under the cap must not escalate yet")


def test_escalates_to_needs_attention_after_max_attempts():
    todo_id = db.add_todo("something genuinely tricky", category="frank_can_do")

    async def fake_headless(prompt):
        return "Still couldn't figure this one out."

    with patch.object(server, "_run_headless_agent_task", fake_headless):
        for _ in range(server._FRANK_CAN_DO_MAX_ATTEMPTS):
            asyncio.run(server._attempt_frank_can_do_todo(_todo_row(todo_id)))

    row = _todo_row(todo_id)
    check(row["attempt_count"] == server._FRANK_CAN_DO_MAX_ATTEMPTS,
          f"expected {server._FRANK_CAN_DO_MAX_ATTEMPTS} attempts recorded, got {row['attempt_count']}")
    check(row["needs_attention"] == 1,
          "after hitting the cap without completing, needs_attention must flip on -- Scott's "
          "explicit ask was 'make sure it gets done', which means a stuck task must visibly "
          "escalate, not retry forever or silently give up")


def test_a_raised_exception_still_records_a_followup_and_bumps_attempts():
    todo_id = db.add_todo("something that errors out", category="frank_can_do")

    async def failing_headless(prompt):
        raise RuntimeError("simulated Anthropic outage")

    with patch.object(server, "_run_headless_agent_task", failing_headless):
        asyncio.run(server._attempt_frank_can_do_todo(_todo_row(todo_id)))

    row = _todo_row(todo_id)
    check("simulated Anthropic outage" in (row["follow_up"] or ""),
          f"a failure must still leave a visible trace, got: {row['follow_up']!r}")
    check(row["attempt_count"] == 1, "a failed attempt must still count toward the retry cap")


def test_iteration_processes_open_todos_and_respects_the_limit():
    for i in range(5):
        db.add_todo(f"iteration test task {i}", category="frank_can_do")

    calls = []

    async def fake_headless(prompt):
        calls.append(prompt)
        return "done looking at it"

    with patch.object(server, "_run_headless_agent_task", fake_headless):
        result = asyncio.run(server._frank_can_do_iteration())

    check(result["attempted"] <= 3, f"list_open_frank_can_do_todos caps at 3 per call, got {result}")
    check(len(calls) == result["attempted"], "the iteration must attempt exactly as many todos as it reports")


def test_run_now_endpoint_rejects_wrong_category_and_already_done():
    general_id = db.add_todo("a general task", category="general")
    try:
        asyncio.run(server.run_frank_can_do_now(general_id, _token="test"))
        check(False, "must reject a non-frank_can_do todo")
    except Exception as e:
        check(getattr(e, "status_code", None) == 400, f"expected 400, got: {e}")

    done_id = db.add_todo("already finished", category="frank_can_do")
    db.set_todo_done(done_id, True)
    try:
        asyncio.run(server.run_frank_can_do_now(done_id, _token="test"))
        check(False, "must reject an already-completed todo")
    except Exception as e:
        check(getattr(e, "status_code", None) == 409, f"expected 409, got: {e}")

    try:
        asyncio.run(server.run_frank_can_do_now(999999999, _token="test"))
        check(False, "must reject a nonexistent todo id")
    except Exception as e:
        check(getattr(e, "status_code", None) == 404, f"expected 404, got: {e}")


def test_run_now_endpoint_success_path_calls_the_real_attempt_function():
    todo_id = db.add_todo("run this on demand", category="frank_can_do")
    attempt_mock = AsyncMock()
    with patch.object(server, "_attempt_frank_can_do_todo", attempt_mock):
        result = asyncio.run(server.run_frank_can_do_now(todo_id, _token="test"))
    check(result == {"ok": True}, f"got: {result}")
    check(attempt_mock.called, "run-now must call the same _attempt_frank_can_do_todo the "
          "background loop uses -- one place this logic lives")
    check(attempt_mock.call_args.args[0]["id"] == todo_id, "must pass the real todo row")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FRANK CAN DO LOOP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FRANK CAN DO LOOP TESTS OK — real completion records a follow-up without bumping "
          "attempts, a non-completing attempt bumps attempt_count without marking done, hitting "
          "the retry cap escalates via needs_attention, a raised exception still leaves a visible "
          "follow-up trace, the iteration respects its per-run limit, and the manual run-now "
          "endpoint enforces category/done checks and reuses the exact same attempt logic.")


if __name__ == "__main__":
    run()
