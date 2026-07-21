"""
Test for the 2026-07-21 fix adding a timeout ceiling around chat tool dispatch
in _run_agent_turn.

Previously the non-relay, non-staged tool path
(`asyncio.to_thread(_execute_agent_tool, ...)`) had no timeout at all. Most
_EXEC_COMMANDS branches are bounded by their own subprocess timeout (up to
400s today), but several other _execute_agent_tool branches call external
SDKs/CLIs with zero timeout of their own (e.g. video_understanding.py's
yt-dlp download and Gemini file-upload poll loop) -- a hang there would wedge
the whole chat turn (and the shared to_thread executor pool) forever, with
no way for Scott to get a response or retry. _dispatch_to_relay already had a
15s bound and _stage_local_action's only blocking call IS _dispatch_to_relay,
so both were already safe; this closes the gap for the third path.

Fix: wrap that call in asyncio.wait_for(..., timeout=_TOOL_DISPATCH_TIMEOUT_S)
and turn a timeout into a normal {"error": ...} tool_result instead of an
unbounded hang, so the turn always completes.

Checks:
  1. A tool call that runs long past the ceiling produces a timeout error
     tool_result instead of hanging, and the turn still completes (quickly).
  2. A normal, fast tool call is completely unaffected by the ceiling.

Run: python tests/test_chat_tool_dispatch_timeout.py
"""
import asyncio
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_dispatchtimeout_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "dispatchtimeout-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


class _FakeWebSocket:
    def __init__(self):
        self.sent: list[str] = []

    async def send_text(self, s):
        self.sent.append(s)


class _FakeStreamCtx:
    def __init__(self, final_message):
        self._final = final_message

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    @property
    def text_stream(self):
        return iter(())

    def get_final_message(self):
        return self._final


class _FakeBlock:
    def __init__(self, type, **kw):  # noqa: A002 -- matches the real SDK's attribute name
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeFinalMessage:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = None


class _FakeMessagesClient:
    def __init__(self, responses):
        self._responses = responses
        self.calls: list[dict] = []

    def stream(self, **kwargs):
        self.calls.append(kwargs)
        idx = min(len(self.calls) - 1, len(self._responses) - 1)
        return _FakeStreamCtx(self._responses[idx])


class _FakeAIClient:
    def __init__(self, responses):
        self.messages = _FakeMessagesClient(responses)


def _tool_use_response() -> _FakeFinalMessage:
    block = _FakeBlock("tool_use", id="toolu_1", name="get_metrics", input={})
    return _FakeFinalMessage(content=[block], stop_reason="tool_use")


def _end_turn_response(text: str = "Here's a summary.") -> _FakeFinalMessage:
    block = _FakeBlock("text", text=text)
    return _FakeFinalMessage(content=[block], stop_reason="end_turn")


def _run_turn(responses, exec_tool_fn):
    """Runs the turn and returns (..., turn_elapsed) where turn_elapsed times only
    the _run_agent_turn() coroutine itself -- NOT the surrounding asyncio.run(),
    which (via shutdown_default_executor) blocks on process teardown until any
    still-running to_thread() worker finishes. That teardown wait is an inherent,
    already-documented Python limitation (a real OS thread can't be force-killed),
    not something the timeout ceiling fix can or should affect -- what the fix
    guarantees is that the CHAT TURN itself (the thing the user is waiting on)
    returns promptly, which is what turn_elapsed measures."""
    ai_client = _FakeAIClient(responses)
    ws = _FakeWebSocket()
    history = [{"role": "user", "content": "do the thing"}]
    timing = {}

    async def _timed():
        start = time.monotonic()
        result = await server._run_agent_turn(ws, ai_client, history)
        timing["elapsed"] = time.monotonic() - start
        return result

    with patch.object(server, "_execute_agent_tool", side_effect=exec_tool_fn), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True), \
         patch.object(server._anthropic_breaker, "record_success", return_value=None):
        text, pii = asyncio.run(_timed())
    return ai_client, ws, history, text, pii, timing["elapsed"]


def _extract_tool_result_error(history) -> str | None:
    for msg in history:
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") == "tool_result":
                payload = json.loads(block["content"])
                if "error" in payload:
                    return payload["error"]
    return None


def test_slow_tool_times_out_instead_of_hanging():
    def _slow_tool(name, tool_input):
        time.sleep(2.0)  # real blocking sleep, mimics a wedged external call
        return {"ok": True}

    responses = [_tool_use_response(), _end_turn_response()]
    with patch.object(server, "_TOOL_DISPATCH_TIMEOUT_S", 0.05):
        ai_client, ws, history, text, pii, elapsed = _run_turn(responses, _slow_tool)

    check(elapsed < 1.5,
          f"the chat turn itself must complete quickly once the ceiling trips, not wait for "
          f"the slow tool to actually finish (turn took {elapsed:.2f}s against a 2.0s-sleeping "
          f"tool and a 0.05s ceiling)")
    err = _extract_tool_result_error(history)
    check(err is not None and "did not finish" in err,
          f"expected a 'did not finish' timeout error tool_result, got: {err!r}")
    check(len(ai_client.messages.calls) == 2,
          f"the turn should still complete normally after the timeout (2 calls expected), "
          f"got {len(ai_client.messages.calls)}")


def test_fast_tool_unaffected_by_ceiling():
    def _fast_tool(name, tool_input):
        return {"ok": True, "value": 42}

    responses = [_tool_use_response(), _end_turn_response()]
    with patch.object(server, "_TOOL_DISPATCH_TIMEOUT_S", 0.05):
        ai_client, ws, history, text, pii, elapsed = _run_turn(responses, _fast_tool)

    err = _extract_tool_result_error(history)
    check(err is None, f"a fast tool call should not trip the ceiling at all, got error: {err!r}")
    check(len(ai_client.messages.calls) == 2, "turn should complete normally")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CHAT TOOL DISPATCH TIMEOUT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CHAT TOOL DISPATCH TIMEOUT TESTS OK — a tool call that runs past the ceiling now "
          "produces a timeout error tool_result and the turn completes promptly instead of "
          "hanging forever, while fast tool calls are completely unaffected.")


if __name__ == "__main__":
    run()
