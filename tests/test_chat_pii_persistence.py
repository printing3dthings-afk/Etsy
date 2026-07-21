#!/usr/bin/env python3
"""
Fixture test for tools/api_server/main.py's _should_persist_chat_turn()
(2026-07-15 ADA/security audit follow-up) -- the get_orders agent tool
returns a real buyer name to the model for that turn, and Scott chose
(among the options presented) that such turns should never be written to
Frank's durable, searchable chat-history DB, even though the model still
sees the name live to answer naturally.

2026-07-19 addition: _PII_TOOLS only ever matched the top-level tool name,
but check_new_orders/send_order_notifications/check_buyer_messages are all
dispatched through the single generic "execute_command" tool -- so
block.name is always "execute_command", never matching _PII_TOOLS, and
those turns (which DO surface real buyer names/personalized messages via
order_notifier.py's stdout) were persisted unflagged. Fixed via a
"contains_pii" flag on the relevant _EXEC_COMMANDS entries, checked in
_run_agent_turn when block.name == "execute_command". Tested here at two
levels: the config flags themselves, and a full mocked-turn test that the
resulting pii_tools_used set actually gets populated.

Dependency-light: `import main as server` (same safe import
tests/test_staged_actions.py already relies on -- no server start, no
background loops, no live Anthropic/Etsy call). Exercises only the pure
routing decision, not the full websocket turn (except where noted).

Run locally:  python tests/test_chat_pii_persistence.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_persists_a_normal_turn_with_a_session():
    check(server._should_persist_chat_turn("sess-1", frozenset()) is True,
          "a turn with a session and no PII tools used should persist")


def test_skips_a_turn_that_used_get_orders():
    check(server._should_persist_chat_turn("sess-1", frozenset({"get_orders"})) is False,
          "a turn that called get_orders must not persist, even with a valid session")


def test_skips_when_no_session_regardless_of_pii():
    check(server._should_persist_chat_turn("", frozenset()) is False,
          "no session_id means no persistence, matching pre-existing behavior")
    check(server._should_persist_chat_turn("", frozenset({"get_orders"})) is False,
          "no session_id + PII tool used should still be False, not raise")


def test_pii_tools_constant_contains_get_orders():
    check("get_orders" in server._PII_TOOLS,
          f"get_orders must be in _PII_TOOLS (the only agent tool confirmed to return a buyer name), got: {server._PII_TOOLS}")
    check("get_reviews" not in server._PII_TOOLS,
          "get_reviews returns no buyer identifier (confirmed in the audit) -- must not be flagged")


def test_exec_commands_that_leak_pii_are_flagged():
    for cmd_name in ("check_new_orders", "send_order_notifications", "check_buyer_messages"):
        check(server._EXEC_COMMANDS.get(cmd_name, {}).get("contains_pii") is True,
              f"{cmd_name} returns real buyer PII in its stdout and must be flagged contains_pii: "
              f"{server._EXEC_COMMANDS.get(cmd_name)}")


def test_unrelated_exec_commands_not_flagged():
    # Spot-check a command that has nothing to do with buyer data isn't accidentally flagged.
    other = next((n for n, cfg in server._EXEC_COMMANDS.items()
                  if n not in ("check_new_orders", "send_order_notifications", "check_buyer_messages")), None)
    if other is not None:
        check(not server._EXEC_COMMANDS[other].get("contains_pii"),
              f"{other} should not be flagged contains_pii (sanity check the flag isn't blanket-applied): "
              f"{server._EXEC_COMMANDS[other]}")


class _FakeWebSocket:
    def __init__(self):
        self.sent = []

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
    def __init__(self, type, **kw):  # noqa: A002
        self.type = type
        for k, v in kw.items():
            setattr(self, k, v)


class _FakeFinalMessage:
    def __init__(self, content, stop_reason):
        self.content = content
        self.stop_reason = stop_reason
        self.usage = None


class _FakeAIClient:
    """Returns a single tool_use round requesting execute_command, then closes."""
    def __init__(self, command_name):
        self._command_name = command_name
        self.messages = self

    def stream(self, **kwargs):
        if len(getattr(self, "_calls", [])) == 0:
            self._calls = [1]
            block = _FakeBlock("tool_use", id="toolu_1", name="execute_command",
                                input={"command": self._command_name})
            return _FakeStreamCtx(_FakeFinalMessage([block], "tool_use"))
        block = _FakeBlock("text", text="Here you go.")
        return _FakeStreamCtx(_FakeFinalMessage([block], "end_turn"))


def test_execute_command_wrapped_pii_tool_flags_the_turn():
    ai_client = _FakeAIClient("check_new_orders")
    ws = _FakeWebSocket()
    history = [{"role": "user", "content": "any new orders?"}]
    with patch.object(server, "_execute_agent_tool", return_value={"ok": True}), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True), \
         patch.object(server._anthropic_breaker, "record_success", return_value=None):
        text, pii_tools_used = asyncio.run(server._run_agent_turn(ws, ai_client, history))
    check("check_new_orders" in pii_tools_used,
          f"a turn that ran check_new_orders via execute_command must be flagged as PII-touching, got: {pii_tools_used}")
    check(server._should_persist_chat_turn("sess-1", pii_tools_used) is False,
          "the resulting pii_tools_used set must block persistence, same as get_orders does")


def test_execute_command_wrapped_non_pii_tool_does_not_flag():
    ai_client = _FakeAIClient("check_new_orders")  # command overridden below via a non-PII name
    ai_client._command_name = next((n for n, cfg in server._EXEC_COMMANDS.items() if not cfg.get("contains_pii")), None)
    if ai_client._command_name is None:
        return  # no non-PII exec command exists to test against; nothing to assert
    ws = _FakeWebSocket()
    history = [{"role": "user", "content": "run a routine check"}]
    with patch.object(server, "_execute_agent_tool", return_value={"ok": True}), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True), \
         patch.object(server._anthropic_breaker, "record_success", return_value=None):
        text, pii_tools_used = asyncio.run(server._run_agent_turn(ws, ai_client, history))
    check(len(pii_tools_used) == 0,
          f"a non-PII execute_command tool must not flag the turn, got: {pii_tools_used}")


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    ran = 0
    for t in tests:
        try:
            t()
            ran += 1
        except Exception as exc:
            _failures.append(f"{t.__name__} raised an unexpected error: {exc}")
    if _failures:
        print("CHAT PII PERSISTENCE TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"CHAT PII PERSISTENCE TESTS OK — {ran} tests passed "
          f"(_should_persist_chat_turn()'s routing logic, no live Anthropic/Etsy call).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
