#!/usr/bin/env python3
"""
Fixture test for tools/api_server/main.py's _should_persist_chat_turn()
(2026-07-15 ADA/security audit follow-up) -- the get_orders agent tool
returns a real buyer name to the model for that turn, and Scott chose
(among the options presented) that such turns should never be written to
Frank's durable, searchable chat-history DB, even though the model still
sees the name live to answer naturally.

Dependency-light: `import main as server` (same safe import
tests/test_staged_actions.py already relies on -- no server start, no
background loops, no live Anthropic/Etsy call). Exercises only the pure
routing decision, not the full websocket turn.

Run locally:  python tests/test_chat_pii_persistence.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import sys
from pathlib import Path

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
