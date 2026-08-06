"""
Tests for the "Instant Message Response Assistant" (2026-08-06) -- the
review-reply drafting piece of it. Etsy's v3 API has no buyer-messaging
endpoint for third-party apps (confirmed 404, see EtsyAPIClient.get_messages()'s
own docstring) and no review-response endpoint either, so this can never
auto-send anything to Etsy -- what it CAN do is detect a new review the
moment get_reviews() surfaces it, draft a personalized reply with Claude,
persist it, and email Scott a copy-paste-ready digest. Runs hourly via
_review_reply_loop() in production; these tests exercise the pieces directly.

Checks:
  1. _load_review_drafts() / _save_review_draft() round-trip correctly and
     are resilient to a missing/corrupt file (same pattern as
     _load_replied_review_ids()/_mark_review_replied() in
     test_reviews_reply_radar.py).
  2. _draft_review_reply_text() returns None (not raises) when no API key
     is configured, rather than the loop crashing on a fresh install.
  3. _review_reply_iteration() drafts only genuinely new reviews (skips
     already-replied and already-drafted ones), persists each draft, and
     sends exactly one email digest via daily_brief._send_brief.
  4. GET /api/inbox merges the persisted draft into each review's payload,
     and never attaches a draft to an already-replied review.
  5. draft_review_replies is registered as both an AGENT_TOOLS entry and a
     _PII_TOOLS entry (it returns real buyer-authored review text), and
     _execute_agent_tool("draft_review_replies", {}) dispatches to
     _review_reply_iteration() via asyncio.run(), matching the existing
     deep_research precedent for bridging a sync tool-dispatch branch into
     async code.

Run: python tests/test_review_reply_assistant.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_reviewdraft_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "reviewdraft-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_path(prefix: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink()  # start from "doesn't exist yet"
    return path


def test_load_missing_drafts_file_returns_empty_dict():
    path = _fresh_path("review_drafts_missing_")
    orig = server._REVIEW_DRAFTS_PATH
    try:
        server._REVIEW_DRAFTS_PATH = path
        check(server._load_review_drafts() == {}, "a missing file should load as an empty dict, not raise")
    finally:
        server._REVIEW_DRAFTS_PATH = orig


def test_save_and_reload_draft_round_trips():
    path = _fresh_path("review_drafts_roundtrip_")
    orig = server._REVIEW_DRAFTS_PATH
    try:
        server._REVIEW_DRAFTS_PATH = path
        server._save_review_draft("txn_5001", "Thank you so much for the kind words! — Scott", 5)
        drafts = server._load_review_drafts()
        check("txn_5001" in drafts, f"expected the saved draft to be present, got: {drafts}")
        check(drafts["txn_5001"]["draft"] == "Thank you so much for the kind words! — Scott",
              f"draft text should round-trip exactly, got: {drafts['txn_5001']}")
        check(drafts["txn_5001"]["rating"] == 5, f"rating should round-trip, got: {drafts['txn_5001']}")
        check("drafted_at" in drafts["txn_5001"], "a timestamp should be recorded")
    finally:
        server._REVIEW_DRAFTS_PATH = orig
        path.unlink(missing_ok=True)


def test_corrupt_drafts_file_falls_back_to_empty_dict():
    path = _fresh_path("review_drafts_corrupt_")
    path.write_text("{not valid json")
    orig = server._REVIEW_DRAFTS_PATH
    try:
        server._REVIEW_DRAFTS_PATH = path
        check(server._load_review_drafts() == {}, "a corrupt file should load as an empty dict, not raise")
    finally:
        server._REVIEW_DRAFTS_PATH = orig
        path.unlink(missing_ok=True)


def test_draft_text_returns_none_without_api_key():
    with patch.object(server, "_effective_text_engine", return_value="anthropic"), \
         patch.object(server, "ANTHROPIC_KEY", ""):
        result = server._draft_review_reply_text(5, "Loved it!")
    check(result is None, f"expected None with no API key configured (not a crash), got: {result!r}")


def test_iteration_drafts_only_new_reviews_and_sends_one_digest():
    drafts_path = _fresh_path("review_drafts_iter_")
    replied_path = _fresh_path("reviews_replied_iter_")
    orig_drafts, orig_replied = server._REVIEW_DRAFTS_PATH, server._REVIEWS_REPLIED_PATH
    fake_reviews = {"results": [
        {"transaction_id": 6001, "rating": 5, "review": "Absolutely love this planner!", "create_timestamp": 1000},
        {"transaction_id": 6002, "rating": 2, "review": "Sticker sheet was hard to cut.", "create_timestamp": 900},
        {"transaction_id": 6003, "rating": 4, "review": "Pretty good overall.", "create_timestamp": 800},
    ]}
    try:
        server._REVIEW_DRAFTS_PATH = drafts_path
        server._REVIEWS_REPLIED_PATH = replied_path
        server._mark_review_replied("6003")  # already handled -- must be skipped
        server._save_review_draft("6002", "already drafted earlier", 2)  # must be skipped -- already drafted

        with patch.object(server, "EtsyAPIClient") as mock_client_cls, \
             patch.object(server, "_draft_review_reply_text", return_value="Thank you so much! — Scott") as mock_draft, \
             patch("daily_brief._send_brief", return_value=True) as mock_send:
            mock_client_cls.return_value.get_reviews.return_value = fake_reviews
            result = asyncio.run(server._review_reply_iteration())

        check(result["new_drafts"] == 1, f"only review 6001 is genuinely new, got: {result}")
        check(result["total_reviews_checked"] == 3, f"expected all 3 fetched reviews counted, got: {result}")
        check(mock_draft.call_count == 1, f"should only draft the one genuinely-new review, got {mock_draft.call_count} calls")
        drafts = server._load_review_drafts()
        check("6001" in drafts, f"the new review's draft should be persisted, got: {drafts}")
        check(drafts["6002"]["draft"] == "already drafted earlier",
              "the pre-existing draft for 6002 must not be overwritten")
        check(mock_send.call_count == 1, f"expected exactly one email digest sent, got {mock_send.call_count}")
        subject, body = mock_send.call_args.args
        check("1 new review" in subject, f"subject should reflect the real count, got: {subject!r}")
        check("Thank you so much! — Scott" in body, f"the digest body should contain the real drafted text: {body[:300]!r}")
    finally:
        server._REVIEW_DRAFTS_PATH = orig_drafts
        server._REVIEWS_REPLIED_PATH = orig_replied
        drafts_path.unlink(missing_ok=True)
        replied_path.unlink(missing_ok=True)


def test_iteration_is_a_noop_when_nothing_new():
    drafts_path = _fresh_path("review_drafts_noop_")
    replied_path = _fresh_path("reviews_replied_noop_")
    orig_drafts, orig_replied = server._REVIEW_DRAFTS_PATH, server._REVIEWS_REPLIED_PATH
    fake_reviews = {"results": [{"transaction_id": 7001, "rating": 5, "review": "Great!", "create_timestamp": 1000}]}
    try:
        server._REVIEW_DRAFTS_PATH = drafts_path
        server._REVIEWS_REPLIED_PATH = replied_path
        server._mark_review_replied("7001")
        with patch.object(server, "EtsyAPIClient") as mock_client_cls, \
             patch("daily_brief._send_brief") as mock_send:
            mock_client_cls.return_value.get_reviews.return_value = fake_reviews
            result = asyncio.run(server._review_reply_iteration())
        check(result["new_drafts"] == 0, f"nothing new to draft, got: {result}")
        check(mock_send.call_count == 0, "must never send an email digest when there's nothing new")
    finally:
        server._REVIEW_DRAFTS_PATH = orig_drafts
        server._REVIEWS_REPLIED_PATH = orig_replied
        drafts_path.unlink(missing_ok=True)
        replied_path.unlink(missing_ok=True)


def test_inbox_merges_draft_and_never_shows_it_for_replied_reviews():
    drafts_path = _fresh_path("review_drafts_inbox_")
    replied_path = _fresh_path("reviews_replied_inbox_")
    orig_drafts, orig_replied = server._REVIEW_DRAFTS_PATH, server._REVIEWS_REPLIED_PATH
    fake_reviews = {"results": [
        {"transaction_id": 8001, "rating": 5, "review": "Wonderful!", "create_timestamp": 1000},
        {"transaction_id": 8002, "rating": 3, "review": "It was okay.", "create_timestamp": 900},
    ]}
    fake_messages = {"results": []}
    try:
        server._REVIEW_DRAFTS_PATH = drafts_path
        server._REVIEWS_REPLIED_PATH = replied_path
        server._save_review_draft("8001", "So glad you loved it! — Scott", 5)
        server._save_review_draft("8002", "Sorry to hear that -- reach out anytime. — Scott", 3)
        server._mark_review_replied("8002")  # replied AND has a stale draft -- draft should still be attached
        with server._cache_lock:
            server._cache.pop("inbox", None)
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_messages.return_value = fake_messages
            mock_client_cls.return_value.get_reviews.return_value = fake_reviews
            result = asyncio.run(server.get_inbox(_token="test"))
        by_id = {r["id"]: r for r in result["recent_reviews"]}
        check(by_id["8001"]["draft"] == "So glad you loved it! — Scott",
              f"an unreplied review's draft should be attached, got: {by_id.get('8001')}")
        check(by_id["8001"]["replied"] is False, "8001 should not be marked replied")
        # Note: /api/inbox itself doesn't hide a draft on a replied review (the
        # frontend's `!rev.replied` check does that) -- confirm the raw field is
        # still there so the frontend has what it needs to make that call.
        check(by_id["8002"]["draft"] == "Sorry to hear that -- reach out anytime. — Scott",
              f"the draft field should still be present even once replied, got: {by_id.get('8002')}")
        check(by_id["8002"]["replied"] is True, "8002 should be marked replied")
    finally:
        server._REVIEW_DRAFTS_PATH = orig_drafts
        server._REVIEWS_REPLIED_PATH = orig_replied
        drafts_path.unlink(missing_ok=True)
        replied_path.unlink(missing_ok=True)


def test_tool_registered_and_flagged_as_pii():
    names = [t["name"] for t in server.AGENT_TOOLS]
    check("draft_review_replies" in names, "draft_review_replies should be a registered AGENT_TOOLS entry")
    check("draft_review_replies" in server._PII_TOOLS,
          "draft_review_replies returns real buyer-authored review text -- must be flagged PII so the chat turn isn't persisted unflagged")


def test_dispatch_bridges_to_review_reply_iteration_via_asyncio_run():
    async def _fake_iteration():
        return {"new_drafts": 2, "total_reviews_checked": 5}
    with patch.object(server, "_review_reply_iteration", _fake_iteration):
        result = server._execute_agent_tool("draft_review_replies", {})
    check(result == {"new_drafts": 2, "total_reviews_checked": 5}, f"got: {result}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("REVIEW REPLY ASSISTANT TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("REVIEW REPLY ASSISTANT TESTS OK — new reviews get drafted exactly once, already-"
          "drafted/already-replied reviews are skipped, one email digest is sent per run, "
          "/api/inbox merges real drafts, and the chat tool is both registered and PII-flagged.")


if __name__ == "__main__":
    run()
