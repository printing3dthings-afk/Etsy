"""
Tests for the reviews-needing-reply radar (2026-07-18, implementing the
competitive-audit report's finding: the "Inbox & Reviews" card lumped unread
messages and reviews into one generic count, with no way to see which
reviews still need a seller reply -- Alura ships this as a named feature
specifically because Etsy sellers can't automate buyer messaging).

Etsy's v3 API has no seller-reply field on a review and no review-response
endpoint (EtsyAPIClient.get_reviews()'s own docstring, verified 2026-06-17),
so "replied" is tracked locally via data/reviews_replied.json (gitignored,
same buyer-adjacent-content treatment as the existing reviews_seen.json) --
this can only ever be a manual log of what Scott marks handled, never
something Frank detects automatically.

Checks:
  1. _load_replied_review_ids() / _mark_review_replied() round-trip correctly
     and are resilient to a missing/corrupt file.
  2. POST /api/reviews/{id}/mark-replied persists the mark and invalidates
     the inbox cache so the next /api/inbox call reflects it immediately.
  3. GET /api/inbox computes reviews_awaiting_reply correctly against a real
     (mocked) Etsy review response, using transaction_id as the stable id
     since the v3 API has no dedicated review_id.
  4. The frontend has the split UI (awaiting-reply badge distinct from the
     unread-messages badge) and the mark-replied button/handler.

Run: python tests/test_reviews_reply_radar.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_reviewradar_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "reviewradar-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fresh_replied_path():
    tmp = tempfile.NamedTemporaryFile(prefix="reviews_replied_", suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink()  # start from "doesn't exist yet"
    return path


def test_load_missing_file_returns_empty_set():
    path = _fresh_replied_path()
    orig = server._REVIEWS_REPLIED_PATH
    try:
        server._REVIEWS_REPLIED_PATH = path
        check(server._load_replied_review_ids() == set(), "a missing file should load as an empty set, not raise")
    finally:
        server._REVIEWS_REPLIED_PATH = orig


def test_mark_and_reload_round_trips():
    path = _fresh_replied_path()
    orig = server._REVIEWS_REPLIED_PATH
    try:
        server._REVIEWS_REPLIED_PATH = path
        server._mark_review_replied("txn_1001")
        server._mark_review_replied("txn_1002")
        ids = server._load_replied_review_ids()
        check(ids == {"txn_1001", "txn_1002"}, f"expected both marked ids, got: {ids}")
        server._mark_review_replied("txn_1001")  # marking twice should be a no-op, not an error
        check(server._load_replied_review_ids() == {"txn_1001", "txn_1002"}, "re-marking the same id should not duplicate")
    finally:
        server._REVIEWS_REPLIED_PATH = orig
        path.unlink(missing_ok=True)


def test_corrupt_file_falls_back_to_empty_set():
    path = _fresh_replied_path()
    path.write_text("{not valid json")
    orig = server._REVIEWS_REPLIED_PATH
    try:
        server._REVIEWS_REPLIED_PATH = path
        check(server._load_replied_review_ids() == set(), "a corrupt file should load as an empty set, not raise")
    finally:
        server._REVIEWS_REPLIED_PATH = orig
        path.unlink(missing_ok=True)


def test_mark_replied_endpoint_persists_and_busts_cache():
    path = _fresh_replied_path()
    orig = server._REVIEWS_REPLIED_PATH
    try:
        server._REVIEWS_REPLIED_PATH = path
        with server._cache_lock:
            server._cache["inbox"] = (server.time.monotonic(), {"stale": "should be busted"})
        result = asyncio.run(server.mark_review_replied("txn_2001", _token="test"))
        check(result == {"ok": True, "review_id": "txn_2001"}, f"got: {result}")
        check("txn_2001" in server._load_replied_review_ids(), "the id should now be persisted")
        check(server._cache_get("inbox", ttl=90) is None, "marking a review replied should invalidate the inbox cache")
    finally:
        server._REVIEWS_REPLIED_PATH = orig
        path.unlink(missing_ok=True)


def test_inbox_computes_awaiting_reply_against_real_review_shape():
    path = _fresh_replied_path()
    orig = server._REVIEWS_REPLIED_PATH
    fake_reviews = {
        "results": [
            {"transaction_id": 3001, "rating": 5, "review": "Loved it!", "create_timestamp": 1000},
            {"transaction_id": 3002, "rating": 4, "review": "Pretty good.", "create_timestamp": 900},
            {"transaction_id": 3003, "rating": 2, "review": "Meh.", "create_timestamp": 800},
        ]
    }
    fake_messages = {"results": []}
    try:
        server._REVIEWS_REPLIED_PATH = path
        server._mark_review_replied("3001")  # only this one has been replied to
        with server._cache_lock:
            server._cache.pop("inbox", None)
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.get_messages.return_value = fake_messages
            mock_client.get_reviews.return_value = fake_reviews
            result = asyncio.run(server.get_inbox(_token="test"))
        check(result["reviews_awaiting_reply"] == 2,
              f"2 of 3 reviews (3002, 3003) should be awaiting reply, got: {result}")
        by_id = {r["id"]: r for r in result["recent_reviews"]}
        check(by_id.get("3001", {}).get("replied") is True, f"3001 was marked replied, got: {result['recent_reviews']}")
        check(by_id.get("3002", {}).get("replied") is False, f"3002 was never marked, got: {result['recent_reviews']}")
    finally:
        server._REVIEWS_REPLIED_PATH = orig
        path.unlink(missing_ok=True)
        with server._cache_lock:
            server._cache.pop("inbox", None)


def test_frontend_has_split_ui_and_mark_handler():
    hud_path = ROOT / "tools" / "api_server" / "frank_hud_mockup.py"
    source = hud_path.read_text(encoding="utf-8")
    check("reviews_awaiting_reply" in source, "loadInbox() should read the new reviews_awaiting_reply field")
    check("function markReviewReplied(reviewId)" in source, "the mark-replied handler should exist")
    check("/api/reviews/" in source and "mark-replied" in source, "the handler should call the new endpoint")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("REVIEWS REPLY RADAR TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("REVIEWS REPLY RADAR TESTS OK — replied-id tracking round-trips and survives a "
          "missing/corrupt file, the mark-replied endpoint persists and busts the inbox "
          "cache, /api/inbox correctly computes reviews_awaiting_reply against real review "
          "shape, and the frontend has the split UI + handler.")


if __name__ == "__main__":
    run()
