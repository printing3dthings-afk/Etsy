#!/usr/bin/env python3
"""
Tests for two related 2026-07-18 UX fixes to _compute_actions() (the
deterministic rules engine behind GET /api/actions, feeding the Today tab's
"Needs attention" list):

1. A card is excluded while its listing has a genuinely PENDING staged
   action in the queue -- signal sourced from db.list_actions("pending").
   A rejected (non-pending) action does NOT exclude the card, so a
   genuinely unresolved problem still surfaces.

2. Second bug report, same day: Scott approved a Conversion Doctor fix
   (title/tags/description edit) for a listing and the SAME card was back
   the instant the action left "pending" -- because none of the four
   content-fixable rules (title_too_long, tags_incomplete, low_conversion,
   zero_views) can be satisfied by a content edit; they read views/sales/
   title/tags straight from Etsy, and per CLAUDE.md's Ranking Recovery
   Playbook those numbers can't move for ~2-3 weeks while Etsy re-indexes.
   So instead of hiding the card outright (which gave Scott zero
   confirmation a fix was even applied), a listing edited within
   db._RANKING_RECOVERY_COOLDOWN_DAYS gets its card severity downgraded to
   "low" and its suggestion rewritten to confirm the fix and explain the
   wait -- reusing db.days_since_listing_edited(), built on the same
   edit-cooldown timestamp already recorded for the ranking-recovery
   compounding-edit warning.

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


def _run_compute_actions(listings, pending_actions, edited_days_by_listing=None):
    edited_days_by_listing = edited_days_by_listing or {}

    def fake_days_since_edited(listing_id):
        return edited_days_by_listing.get(listing_id)

    with patch.object(server, "_listings_sync", lambda state="active": {"listings": [] if state == "draft" else []}), \
         patch.object(server, "_enrich_sales", lambda ls: listings), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: pending_actions), \
         patch.object(server.db, "days_since_listing_edited", fake_days_since_edited):
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


def test_recently_edited_listing_card_is_downgraded_not_hidden():
    """The actual bug report: approving a Conversion Doctor fix must not make
    the identical high-severity card reappear unchanged -- but it also must
    not vanish silently (that gave Scott zero confirmation anything happened).
    Severity drops and the suggestion explains what happened and how long to wait."""
    listings = [_listing(777, views=377, sales=0, title="Dinosaur Coloring Book 20 Pages")]
    result = _run_compute_actions(listings, pending_actions=[], edited_days_by_listing={777: 0})
    cards = [c for c in result["actions"] if c["listing_id"] == 777]
    check(len(cards) == 1, f"the card must still exist (not hidden), got: {cards}")
    card = cards[0]
    check(card["severity"] == "low", f"a just-fixed listing's card must be downgraded to low severity, got: {card['severity']}")
    check("applied" in card["suggestion"].lower(), f"suggestion should confirm a fix was applied: {card['suggestion']}")
    check("0d ago" in card["suggestion"], f"suggestion should say how recently: {card['suggestion']}")
    check(card.get("recently_fixed_days_ago") == 0, f"expected recently_fixed_days_ago=0, got: {card}")


def test_edit_outside_cooldown_window_is_untouched():
    listings = [_listing(888, views=50, sales=0)]
    days_old = server.db._RANKING_RECOVERY_COOLDOWN_DAYS + 5
    result = _run_compute_actions(listings, pending_actions=[], edited_days_by_listing={888: days_old})
    cards = [c for c in result["actions"] if c["listing_id"] == 888]
    check(len(cards) == 1, f"got: {cards}")
    check(cards[0]["severity"] == "high", f"an edit from {days_old}d ago is well past the recovery window and must not be treated as recent: {cards[0]}")
    check("recently_fixed_days_ago" not in cards[0], f"got: {cards[0]}")


def test_never_edited_listing_is_untouched():
    listings = [_listing(999, views=50, sales=0)]
    result = _run_compute_actions(listings, pending_actions=[], edited_days_by_listing={})
    cards = [c for c in result["actions"] if c["listing_id"] == 999]
    check(len(cards) == 1 and cards[0]["severity"] == "high", f"got: {cards}")


def test_non_content_fixable_category_is_never_downgraded():
    """draft_unpublished isn't one of the four content-fixable categories (a
    content edit doesn't change "still sitting in draft") -- a recent
    edited-timestamp for that same listing must not downgrade its card,
    since the cooldown transform only makes sense for the four rules that
    an update_title/tags/description fix could plausibly have addressed."""
    draft_listing = {
        "listing_id": 2020, "title": "Unpublished Draft Listing", "tags": [],
        "views": 0, "num_favorers": 0, "sales": 0, "created_timestamp": 0,
        "url": "https://etsy.com/listing/2020",
    }
    with patch.object(server, "_listings_sync", lambda state="active": {"listings": [draft_listing] if state == "draft" else []}), \
         patch.object(server, "_enrich_sales", lambda ls: []), \
         patch.object(server.db, "list_actions", lambda status="pending", limit=100: []), \
         patch.object(server.db, "days_since_listing_edited", lambda listing_id: 0):
        result = server._compute_actions()
    cards = [c for c in result["actions"] if c["listing_id"] == 2020]
    check(len(cards) == 1, f"got: {cards}")
    check(cards[0]["category"] == "draft_unpublished", f"got: {cards[0]}")
    check(cards[0]["severity"] == "high", f"draft_unpublished is not content-fixable and must not be downgraded: {cards[0]}")
    check("recently_fixed_days_ago" not in cards[0], f"got: {cards[0]}")


def test_days_since_listing_edited_round_trips_through_note_listing_edited():
    """Exercise the real db.py functions (not mocked) end-to-end: never-edited
    returns None, editing now returns 0 days, a malformed stored value degrades
    to None rather than raising."""
    import db as real_db
    listing_id = "rt-test-listing-12345"
    check(real_db.days_since_listing_edited(listing_id) is None,
          "a never-edited listing must return None")
    real_db.note_listing_edited(listing_id)
    days = real_db.days_since_listing_edited(listing_id)
    check(days == 0, f"editing just now should read back as 0 days, got: {days}")
    real_db.set_setting(real_db._listing_last_edited_key("malformed-ts-listing"), "not-a-timestamp")
    check(real_db.days_since_listing_edited("malformed-ts-listing") is None,
          "a malformed stored timestamp must degrade to None, not raise")


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
    print("NEEDS-ATTENTION FILTER + RECENTLY-FIXED TRANSFORM TESTS OK — a listing with "
          "a genuinely pending fix is excluded, unrelated listings are unaffected, "
          "str/int listing_id mismatches don't defeat the filter, a db failure "
          "degrades to showing everything rather than hiding real findings, a "
          "recently content-edited listing's card is downgraded (not hidden) with a "
          "suggestion confirming the fix and wait time, an edit outside the recovery "
          "window or a non-content-fixable category is left untouched, and "
          "days_since_listing_edited round-trips through note_listing_edited "
          "including a malformed-timestamp fallback to None.")


if __name__ == "__main__":
    run()
