#!/usr/bin/env python3
"""
Fixture-based tests for tools/api_server/db.py's chat-history read functions
(2026-08-01, Chat History screen audit).

get_chat_session() used to do `ORDER BY id ASC LIMIT 500` -- once a
long-lived session (CHAT_SESSION is a single per-device UUID reused
indefinitely) passed 500 messages, its newest replies became permanently
unreachable on the Chat History screen, with no pagination to page forward.
Fixed to select the newest `limit` rows (DESC + reverse), same pattern
load_chat_history() already used.

search_chat_messages() used to return a bare list with no truncation
signal; the frontend guessed "truncated" from `results.length === limit`,
which can't distinguish "capped" from "exactly `limit` total matches."
Fixed to query `limit + 1` rows and return a real `truncated` flag.

Uses a throwaway temp SQLite DB (DB_PATH env var, set before importing db)
so this never touches the real dev database. No network, no live Etsy.
Follows tests/test_db_ranking_recovery.py's pattern (direct `import db`,
no FastAPI/app-layer machinery) since both functions under test are pure
db.py functions with no app-layer dependency.

Run locally:  python tests/test_chat_history_pagination.py
In CI:        see .github/workflows/ci-smoke.yml
Exit code 0 = all pass, non-zero = a regression (prints which).
"""
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_test_chat_history_", suffix=".db", delete=False)
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
        conn.execute("DELETE FROM chat_messages")
        conn.commit()
    finally:
        conn.close()


def _seed(session_id: str, count: int, prefix: str = "msg"):
    for i in range(count):
        db.append_chat_message(session_id, "user" if i % 2 == 0 else "assistant", f"{prefix} {i}")


# ── get_chat_session() ──

def test_get_chat_session_returns_newest_500_when_over_the_cap():
    _reset()
    _seed("sess-over", 520)
    result = db.get_chat_session("sess-over")
    check(result["truncated"] is True, f"expected truncated=True for 520 messages, got {result['truncated']}")
    msgs = result["messages"]
    check(len(msgs) == 500, f"expected exactly 500 messages returned, got {len(msgs)}")
    # The 520 seeded messages are "msg 0".."msg 519" -- the newest 500 are
    # "msg 20".."msg 519". If this regresses to the old ASC LIMIT 500 behavior,
    # it would instead return "msg 0".."msg 499" and this assertion catches it.
    check(msgs[0]["content"] == "msg 20",
          f"expected the OLDEST of the retained window to be 'msg 20' (the newest 500 of 520), got {msgs[0]['content']!r}")
    check(msgs[-1]["content"] == "msg 519",
          f"expected the NEWEST message to be 'msg 519', got {msgs[-1]['content']!r}")
    ids = [m["id"] for m in msgs]
    check(ids == sorted(ids), "messages must be returned in ascending (oldest-first) order for display")


def test_get_chat_session_unaffected_when_under_the_cap():
    _reset()
    _seed("sess-under", 12)
    result = db.get_chat_session("sess-under")
    check(result["truncated"] is False, f"expected truncated=False for 12 messages, got {result['truncated']}")
    msgs = result["messages"]
    check(len(msgs) == 12, f"expected all 12 messages returned, got {len(msgs)}")
    check(msgs[0]["content"] == "msg 0" and msgs[-1]["content"] == "msg 11",
          f"expected ascending order msg 0..msg 11 unchanged, got first={msgs[0]['content']!r} last={msgs[-1]['content']!r}")


def test_get_chat_session_unknown_session_returns_empty():
    _reset()
    result = db.get_chat_session("does-not-exist")
    check(result == {"messages": [], "truncated": False}, f"expected empty result for unknown session, got {result}")


# ── search_chat_messages() ──

def test_search_truncated_true_when_matches_exceed_the_cap():
    _reset()
    _seed("sess-search-many", 60, prefix="findme")
    result = db.search_chat_messages("findme", limit=50)
    check(result["truncated"] is True, f"expected truncated=True for 60 matches against a 50 cap, got {result['truncated']}")
    check(len(result["results"]) == 50, f"expected exactly 50 results returned (not 51), got {len(result['results'])}")


def test_search_truncated_false_when_matches_exactly_equal_the_cap():
    _reset()
    _seed("sess-search-exact", 50, prefix="findme")
    result = db.search_chat_messages("findme", limit=50)
    # This is the exact case the old (rejected) frontend guess
    # (results.length === limit -> truncated) got wrong: exactly 50 real
    # matches, nothing was actually capped.
    check(result["truncated"] is False,
          f"expected truncated=False when there are EXACTLY 50 total matches (nothing capped), got {result['truncated']}")
    check(len(result["results"]) == 50, f"expected all 50 results returned, got {len(result['results'])}")


def test_search_truncated_false_when_matches_under_the_cap():
    _reset()
    _seed("sess-search-few", 5, prefix="findme")
    result = db.search_chat_messages("findme", limit=50)
    check(result["truncated"] is False, f"expected truncated=False for 5 matches, got {result['truncated']}")
    check(len(result["results"]) == 5, f"expected all 5 results returned, got {len(result['results'])}")


def test_search_empty_query_returns_empty():
    _reset()
    result = db.search_chat_messages("   ")
    check(result == {"results": [], "truncated": False}, f"expected empty result for a blank query, got {result}")


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
        print("CHAT HISTORY PAGINATION TESTS FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s) across {len(tests)} tests.", file=sys.stderr)
        return 1
    print(f"CHAT HISTORY PAGINATION TESTS OK — {ran} tests passed "
          f"(get_chat_session() returns the newest N messages not the oldest, "
          f"search_chat_messages() reports real truncation not a length guess).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
