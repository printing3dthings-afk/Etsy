"""
Tests for the 2026-07-19 fix to _run_agent_turn's tool round-trip cap.

Previously `for _ in range(6)` had nothing after it: if the 6th round's
response was ITSELF tool_use, the tools still got executed and their results
appended as a user-role message, but the loop then just ended with no further
LLM call to consume them -- history was left ending in user-role, so the
NEXT real user turn appended a SECOND consecutive user-role message on top,
which Anthropic rejects with a 400 ("roles must alternate"), permanently
wedging that session's chat until reload. This is the same failure class as
the 2026-06-17 incident (ops_runbook.md) that hardened the tool_result-append
ordering, just reachable via a different trigger that fix didn't cover.

Fix: one guaranteed extra round with no `tools` param offered at all, so the
model cannot request more tool use and must close out in plain text --
history is then guaranteed to end on an assistant-role turn no matter how the
cap is hit.

Checks:
  1. If the model keeps requesting tool_use for the full 6-round cap, a 7th
     call is made, and it does NOT include a `tools` kwarg.
  2. After the cap is exhausted, `history`'s last entry has role "assistant",
     never "user" -- the exact invariant a corrupted session would violate.
  3. A normal (non-capped) turn is unaffected: it still returns after the
     first non-tool_use response, with no extra call made.

Run: python tests/test_chat_turn_roundtrip_cap.py
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_roundtripcap_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "roundtripcap-test-not-a-real-secret")

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


def _tool_use_response(round_num: int) -> _FakeFinalMessage:
    block = _FakeBlock("tool_use", id=f"toolu_{round_num}", name="get_metrics", input={})
    return _FakeFinalMessage(content=[block], stop_reason="tool_use")


def _end_turn_response(text: str = "Here's a summary.") -> _FakeFinalMessage:
    block = _FakeBlock("text", text=text)
    return _FakeFinalMessage(content=[block], stop_reason="end_turn")


def _run_turn(responses):
    ai_client = _FakeAIClient(responses)
    ws = _FakeWebSocket()
    history = [{"role": "user", "content": "do the thing"}]
    with patch.object(server, "_execute_agent_tool", return_value={"ok": True}), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True), \
         patch.object(server._anthropic_breaker, "record_success", return_value=None):
        text, pii = asyncio.run(server._run_agent_turn(ws, ai_client, history))
    return ai_client, ws, history, text, pii


def test_cap_exhaustion_forces_a_final_no_tools_call():
    # 6 rounds of tool_use (the cap), then the 7th call (forced, no tools) also
    # happens to come back as tool_use in this test double -- doesn't matter what
    # it returns, the real API physically cannot request a tool it wasn't offered,
    # so what we're actually verifying is the CALL SHAPE (no `tools` kwarg on
    # round 7) and that the loop doesn't try to process tool_use blocks from it.
    responses = [_tool_use_response(i) for i in range(6)] + [_end_turn_response()]
    ai_client, ws, history, text, pii = _run_turn(responses)

    check(len(ai_client.messages.calls) == 7,
          f"expected exactly 7 LLM calls (6 tool rounds + 1 forced wrap-up), got {len(ai_client.messages.calls)}")
    last_call = ai_client.messages.calls[-1]
    check("tools" not in last_call,
          f"the 7th (wrap-up) call must not offer tools at all, got kwargs: {list(last_call.keys())}")
    for i, call in enumerate(ai_client.messages.calls[:-1]):
        check("tools" in call, f"round {i} (within the cap) should still offer tools: {list(call.keys())}")


def test_history_never_ends_on_user_role_after_cap_exhaustion():
    responses = [_tool_use_response(i) for i in range(6)] + [_end_turn_response()]
    ai_client, ws, history, text, pii = _run_turn(responses)
    check(history[-1]["role"] == "assistant",
          f"history must end on an assistant-role turn so the next real user message doesn't create two "
          f"consecutive user-role messages (the exact corruption this fix prevents): last entry was {history[-1]}")


def test_normal_turn_unaffected_no_extra_call():
    responses = [_end_turn_response("All done, no tools needed.")]
    ai_client, ws, history, text, pii = _run_turn(responses)
    check(len(ai_client.messages.calls) == 1, f"a turn resolved on the first response should make exactly 1 call, got {len(ai_client.messages.calls)}")
    check("tools" in ai_client.messages.calls[0], "a normal (non-final) round should still offer tools")
    check(history[-1]["role"] == "assistant", f"history should end on assistant role: {history[-1]}")
    check(text == "All done, no tools needed." or text == "", f"unexpected returned text: {text!r}")


def test_turn_resolving_within_cap_makes_no_wrapup_call():
    # 2 tool rounds then a normal close -- well within the cap, must not trigger
    # the forced-wrapup path at all.
    responses = [_tool_use_response(0), _tool_use_response(1), _end_turn_response()]
    ai_client, ws, history, text, pii = _run_turn(responses)
    check(len(ai_client.messages.calls) == 3, f"expected exactly 3 calls (2 tool rounds + 1 closing), got {len(ai_client.messages.calls)}")
    check(history[-1]["role"] == "assistant", f"history should end on assistant role: {history[-1]}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CHAT ROUND-TRIP CAP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CHAT ROUND-TRIP CAP TESTS OK — exhausting the 6-round tool cap forces one final no-tools "
          "wrap-up call, history always ends on an assistant-role turn (never the two-consecutive-"
          "user-messages corruption), and normal turns that resolve within the cap are unaffected.")


if __name__ == "__main__":
    run()
