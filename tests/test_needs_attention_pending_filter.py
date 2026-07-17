#!/usr/bin/env python3
"""
Test for a 2026-07-18 UX fix: Scott reported that the mobile Today tab's
"Needs attention" list kept showing the SAME listing right after he tapped
"Let Frank fix it" and a fix was actually staged -- confusing, since it read
as still-broken even though a fix was already in flight.

_compute_actions() (the deterministic rules engine behind GET /api/actions,
which feeds the mobile Today tab's "Needs attention" list) now excludes any
card whose listing_id already has a PENDING staged action in the queue --
the signal that a fix is genuinely in flight for that listing, sourced
straight from db.list_actions("pending") rather than any new state. A
rejected (non-pending) action does NOT exclude the card, so a genuinely
unresolved problem still surfaces.

Run: python tests/test_needs_attention_pending_filter.py
"""
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_needs_attn_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "needs-attn-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _listing(listing_id, views=50, sales=0, title="A Listing With A Long Enough Title Here"):
    return {
        "listing_id": listing_id, "title": title, "tags": [f"t{i}" for i in range(13)],
        "views": views, "num_favorers": 0, "sales": sales, "created_timestamp": 0, "url": f"https://etsy.com/listing/{listing_id}",
    }


def _run_compute_actions(listings, pending_actions):
    with patch.object(server, "_listings_sync", lambda state="active": {"listings": [] if state == "draft" else []}), \
         patch.object(server, "_enrich_sales", lambda ls: listings), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: pending_actions):
        return server._compute_actions()


def test_card_excluded_once_a_pending_fix_exists_for_that_listing():
    listings = [_listing(111, views=50, sales=0)]
    result_before = _run_compute_actions(listings, pending_actions=[])
    ids_before = {c["listing_id"] for c in result_before["actions"]}
    check(111 in ids_before, f"expected listing 111's low_conversion card before any pending fix, got: {ids_before}")

    pending = [{"type": "update_title", "payload": {"listing_id": 111, "title": "New Title"}}]
    result_after = _run_compute_actions(listings, pending_actions=pending)
    ids_after = {c["listing_id"] for c in result_after["actions"]}
    check(111 not in ids_after, f"listing 111 must be excluded once a fix is pending, got: {ids_after}")


def test_unrelated_listings_unaffected():
    listings = [_listing(111, views=50, sales=0), _listing(222, views=60, sales=0)]
    pending = [{"type": "update_title", "payload": {"listing_id": 111}}]
    result = _run_compute_actions(listings, pending_actions=pending)
    ids = {c["listing_id"] for c in result["actions"]}
    check(111 not in ids, f"got: {ids}")
    check(222 in ids, f"listing 222 has no pending fix and must still show, got: {ids}")


def test_listing_id_type_mismatch_still_matches():
    """Etsy IDs sometimes travel as int vs str across different code paths --
    the comparison must be string-normalized on both sides."""
    listings = [_listing(333, views=50, sales=0)]
    pending = [{"type": "update_tags", "payload": {"listing_id": "333"}}]
    result = _run_compute_actions(listings, pending_actions=pending)
    ids = {c["listing_id"] for c in result["actions"]}
    check(333 not in ids, f"str/int listing_id mismatch must not defeat the filter, got: {ids}")


def test_no_pending_actions_is_a_no_op():
    listings = [_listing(444, views=50, sales=0)]
    result = _run_compute_actions(listings, pending_actions=[])
    ids = {c["listing_id"] for c in result["actions"]}
    check(444 in ids, f"got: {ids}")


def test_pending_action_with_no_listing_id_is_ignored_not_crashing():
    listings = [_listing(555, views=50, sales=0)]
    pending = [{"type": "post_pinterest", "payload": {"board_name": "x"}}]  # no listing_id
    result = _run_compute_actions(listings, pending_actions=pending)
    ids = {c["listing_id"] for c in result["actions"]}
    check(555 in ids, f"a pending action for something else entirely must not suppress unrelated cards: {ids}")


def test_db_failure_degrades_cleanly_to_showing_everything():
    listings = [_listing(666, views=50, sales=0)]

    def failing_list_actions(status="pending", limit=100):
        raise RuntimeError("simulated db failure")

    with patch.object(server, "_listings_sync", lambda state="active": {"listings": []}), \
         patch.object(server, "_enrich_sales", lambda ls: listings), \
         patch.object(server.db, "list_actions", failing_list_actions):
        result = server._compute_actions()
    ids = {c["listing_id"] for c in result["actions"]}
    check(666 in ids, f"a db failure while checking pending actions must not hide real findings, got: {ids}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("NEEDS-ATTENTION PENDING-ACTION FILTER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("NEEDS-ATTENTION PENDING-ACTION FILTER TESTS OK — a listing with a genuinely "
          "pending fix is excluded from Needs Attention, unrelated listings are "
          "unaffected, str/int listing_id mismatches don't defeat the filter, no "
          "pending actions is a no-op, an unrelated pending action doesn't suppress "
          "other cards, and a db failure degrades to showing everything rather than "
          "crashing or hiding real findings.")


if __name__ == "__main__":
    run()
