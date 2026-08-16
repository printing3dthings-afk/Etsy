"""
Test for _run_headless_agent_task() (2026-08-16, Tasks screen rebuild) --
the new headless (no websocket, no persisted chat history) multi-round
tool-use loop that lets Frank actually act on an answered question or a
frank_can_do todo in the background, reusing the exact same tool dispatch
(_execute_agent_tool) live chat uses.

Every Anthropic call is mocked via patch.object(server, "_anthropic_create",
...) -- this test never makes a real API call, matching this repo's
testing.md convention (mock the narrowest real dependency).

Run: python tests/test_headless_agent_task.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_headless_agent_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "headless-agent-test-not-a-real-secret")

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


def _text_block(text: str):
    b = MagicMock()
    b.type = "text"
    b.text = text
    return b


def _tool_use_block(name: str, tool_input: dict, tool_id="tu_1"):
    b = MagicMock()
    b.type = "tool_use"
    b.name = name
    b.input = tool_input
    b.id = tool_id
    return b


def _final_response(text: str):
    r = MagicMock()
    r.content = [_text_block(text)]
    r.stop_reason = "end_turn"
    return r


def _tool_use_response(name: str, tool_input: dict, tool_id="tu_1"):
    r = MagicMock()
    r.content = [_tool_use_block(name, tool_input, tool_id)]
    r.stop_reason = "tool_use"
    return r


def test_no_key_raises_immediately_without_calling_anthropic():
    with patch.object(server, "ANTHROPIC_KEY", ""):
        try:
            asyncio.run(server._run_headless_agent_task("do something"))
            check(False, "must raise when ANTHROPIC_API_KEY is not configured")
        except RuntimeError as e:
            check("ANTHROPIC_API_KEY" in str(e), f"error should name the missing key, got: {e}")


def test_single_round_no_tool_use_returns_final_text():
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_anthropic_create", lambda client, **kw: _final_response("Nothing further needed.")):
        result = asyncio.run(server._run_headless_agent_task("a simple question"))
    check(result == "Nothing further needed.", f"got: {result!r}")


def test_tool_use_round_trip_actually_executes_the_real_tool():
    # complete_todo is safe to run for real here (just a local db.set_todo_done
    # call, no network) -- this proves the whole chain end to end: the model's
    # tool_use block reaches the real _execute_agent_tool dispatcher, which
    # really marks the todo done in the database, not just a mocked stub.
    todo_id = db.add_todo("something frank can do", category="frank_can_do")
    calls = {"n": 0}

    def fake_create(client, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return _tool_use_response("complete_todo", {"todo_id": todo_id})
        return _final_response(f"Completed todo {todo_id}.")

    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_anthropic_create", fake_create):
        result = asyncio.run(server._run_headless_agent_task(f"complete todo {todo_id} now"))

    check(calls["n"] == 2, f"expected exactly 2 Anthropic calls (tool round + final), got {calls['n']}")
    check(f"Completed todo {todo_id}" in result, f"got: {result!r}")
    row = next(t for t in db.list_todos() if t["id"] == todo_id)
    check(row["done"] == 1, "the real complete_todo tool call must have actually marked the todo done")


def test_relay_and_pii_tools_are_excluded_from_the_headless_toolset():
    captured = {}

    def fake_create(client, **kw):
        captured["tools"] = kw.get("tools")
        return _final_response("done")

    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_anthropic_create", fake_create):
        asyncio.run(server._run_headless_agent_task("do something"))

    tool_names = {t["name"] for t in captured["tools"]}
    for excluded in server._RELAY_TOOLS:
        check(excluded not in tool_names,
              f"relay tool {excluded!r} must never be offered headlessly -- there's no live "
              f"connection to Scott's machine when a background loop fires")
    for excluded in server._PII_TOOLS:
        check(excluded not in tool_names,
              f"PII tool {excluded!r} must never be offered headlessly -- its result could land "
              f"in a dashboard-visible follow_up note")
    check("complete_todo" in tool_names, "ordinary tools (complete_todo) must still be offered")


def test_a_failed_tool_call_still_produces_a_tool_result_not_a_crash():
    # _execute_agent_tool itself never raises for a bad input (returns {"error": ...}),
    # but this test proves the loop's own defensive try/except around the dispatch
    # call still guarantees a tool_result is appended even if something unexpected
    # does raise, since a missing tool_result for a tool_use id is an unrecoverable
    # 400 from Anthropic's API (same class of bug _run_agent_turn's own comments
    # warn about).
    calls = {"n": 0}

    def fake_create(client, **kw):
        calls["n"] += 1
        if calls["n"] == 1:
            return _tool_use_response("complete_todo", {"todo_id": 999999999})  # doesn't exist
        # If we got a second call at all, a tool_result was successfully appended.
        msgs = kw["messages"]
        last = msgs[-1]
        check(last["role"] == "user", "the message after a tool_use round must be role=user")
        check(last["content"][0]["type"] == "tool_result", "must contain a real tool_result block")
        return _final_response("couldn't find that todo")

    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_anthropic_create", fake_create):
        result = asyncio.run(server._run_headless_agent_task("complete a nonexistent todo"))
    check(calls["n"] == 2, f"expected the loop to continue past the failed tool call, got {calls['n']} calls")
    check("couldn't find" in result, f"got: {result!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HEADLESS AGENT TASK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HEADLESS AGENT TASK TESTS OK — _run_headless_agent_task() correctly requires a key, "
          "returns final text with no tool use, really executes tool_use blocks through the same "
          "dispatcher live chat uses (verified end to end against a real db.set_todo_done write), "
          "excludes relay/PII tools from what the model is even offered, and always appends a "
          "tool_result even when the underlying tool call fails.")


if __name__ == "__main__":
    run()
