#!/usr/bin/env python3
"""
SKU + category (taxonomy_id) backfill sweep tests (2026-07-26): Scott asked
for "every listing on Etsy to be categorized and have skus so we can track
everything better." Covers:

  - the new `update_sku_and_category` staged-action type: validation,
    execution (single combined update_listing PATCH), allowed-type wiring,
    and Ranking Recovery cooldown coverage (db.py)
  - `_build_sku_taxonomy_backfill_queue()` / `_run_sku_taxonomy_backfill_batch()`
    / `_mark_backfill_queue_done()` — the durable work-queue + weekly-paced
    drip loop that stages fixes for the ~170 live catalog listings
  - `stage_product_publish()` now sets sku on brand-new listings
  - `check_attributes()`'s new SKU WARN check (tools/listing_integrity_check.py)

Standard standalone harness (.claude/rules/testing.md).
Run: python tests/test_sku_category_backfill.py
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_sku_backfill_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "sku-backfill-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402
import listing_integrity_check as lic  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _use_tmp_queue_path():
    """Returns a context manager patching the backfill queue's durable path
    to a fresh temp file, so tests never touch the real repo/volume sidecar."""
    tmp_dir = tempfile.mkdtemp(prefix="frank_sku_backfill_queue_")
    return patch.object(server, "_SKU_TAXONOMY_BACKFILL_QUEUE_PATH", Path(tmp_dir) / "queue.json")


# ── update_sku_and_category: validation ───────────────────────────────────

def test_validate_rejects_when_neither_sku_nor_taxonomy_present():
    candidate = {"type": "update_sku_and_category", "payload": {"listing_id": 111}}
    ok, msg = server._validate_staged_action(candidate)
    check(not ok, "must reject a payload with neither sku nor taxonomy_id")
    check("at least one" in msg, f"got {msg!r}")


def test_validate_accepts_sku_only():
    candidate = {"type": "update_sku_and_category", "payload": {"listing_id": 111, "sku": "DP1026"}}
    ok, msg = server._validate_staged_action(candidate)
    check(ok, f"sku-only payload should validate, got {msg!r}")


def test_validate_accepts_taxonomy_only():
    candidate = {"type": "update_sku_and_category", "payload": {"listing_id": 111, "taxonomy_id": 2078}}
    ok, msg = server._validate_staged_action(candidate)
    check(ok, f"taxonomy-only payload should validate, got {msg!r}")


def test_validate_accepts_both():
    candidate = {"type": "update_sku_and_category",
                 "payload": {"listing_id": 111, "sku": "DP1026", "taxonomy_id": 2078}}
    ok, msg = server._validate_staged_action(candidate)
    check(ok, f"both-fields payload should validate, got {msg!r}")


def test_validate_rejects_empty_sku():
    candidate = {"type": "update_sku_and_category", "payload": {"listing_id": 111, "sku": "   "}}
    ok, msg = server._validate_staged_action(candidate)
    check(not ok, "an empty/whitespace sku must be rejected")


def test_validate_rejects_non_positive_taxonomy_id():
    candidate = {"type": "update_sku_and_category", "payload": {"listing_id": 111, "taxonomy_id": 0}}
    ok, msg = server._validate_staged_action(candidate)
    check(not ok, "taxonomy_id must be a positive integer")
    candidate2 = {"type": "update_sku_and_category", "payload": {"listing_id": 111, "taxonomy_id": True}}
    ok2, msg2 = server._validate_staged_action(candidate2)
    check(not ok2, "a bool must not be accepted as a valid taxonomy_id (bool is an int subclass)")


def test_validate_rejects_missing_listing_id():
    candidate = {"type": "update_sku_and_category", "payload": {"sku": "DP1026"}}
    ok, msg = server._validate_staged_action(candidate)
    check(not ok, "missing listing_id must be rejected")


# ── update_sku_and_category: execution ────────────────────────────────────

def test_execute_combines_both_fields_into_one_update_listing_call():
    with patch.object(server, "EtsyAPIClient") as MockClient:
        instance = MockClient.return_value
        instance.update_listing.return_value = {"listing_id": 222}
        server._execute_staged_action({
            "type": "update_sku_and_category",
            "payload": {"listing_id": 222, "sku": "WA1090", "taxonomy_id": 2097},
        })
    check(instance.update_listing.call_count == 1,
          f"exactly one update_listing call expected (combined PATCH), got {instance.update_listing.call_count}")
    args, _ = instance.update_listing.call_args
    check(args[0] == 222, f"got listing_id {args[0]}")
    check(args[1] == {"sku": "WA1090", "taxonomy_id": 2097}, f"got updates {args[1]}")


def test_execute_omits_absent_field_from_the_patch():
    with patch.object(server, "EtsyAPIClient") as MockClient:
        instance = MockClient.return_value
        instance.update_listing.return_value = {"listing_id": 223}
        server._execute_staged_action({
            "type": "update_sku_and_category",
            "payload": {"listing_id": 223, "sku": "WA1090"},
        })
    args, _ = instance.update_listing.call_args
    check(args[1] == {"sku": "WA1090"}, f"taxonomy_id must not appear when absent from payload, got {args[1]}")


def test_execute_notes_ranking_recovery_edit_and_marks_queue_done():
    with _use_tmp_queue_path():
        queue = {"WA1090": {"listing_id": 224, "category": "wall_art", "target_sku": "WA1090",
                             "target_taxonomy_id": 2097, "status": "staged"}}
        server._write_sku_taxonomy_backfill_queue(queue)
        with patch.object(server, "EtsyAPIClient") as MockClient, \
             patch.object(server.db, "note_listing_edited") as mock_note:
            MockClient.return_value.update_listing.return_value = {"listing_id": 224}
            server._execute_staged_action({
                "type": "update_sku_and_category",
                "payload": {"listing_id": 224, "sku": "WA1090"},
            })
        check(mock_note.called, "note_listing_edited must be called for update_sku_and_category (Ranking Recovery)")
        reloaded = server._read_sku_taxonomy_backfill_queue()
        check(reloaded["WA1090"]["status"] == "done",
              f"queue entry must be marked done after successful execution, got {reloaded['WA1090']['status']}")


# ── allowed-type wiring ────────────────────────────────────────────────────

def test_new_type_in_allowed_type_sets():
    check("update_sku_and_category" in server._ETSY_STAGED_ACTION_TYPES, "must be in _ETSY_STAGED_ACTION_TYPES")
    check("update_sku_and_category" in server._STAGED_ACTION_TYPES, "must be in _STAGED_ACTION_TYPES")
    check("update_sku_and_category" in db._RANKING_RECOVERY_TYPES, "must be in db._RANKING_RECOVERY_TYPES")


def test_enqueue_action_warns_on_compounding_edit_for_new_type():
    lid = 998877
    db.note_listing_edited(lid)
    aid = db.enqueue_action("update_sku_and_category", "test summary", {"listing_id": lid, "sku": "X"})
    actions = db.list_actions("pending")
    match = next(a for a in actions if a["id"] == aid)
    check("ranking recovery" in match["summary"].lower() or "resets its ranking" in match["summary"].lower(),
          f"expected the cooldown warning prefix on a recently-edited listing, got {match['summary']!r}")


# ── _build_sku_taxonomy_backfill_queue ─────────────────────────────────────

def test_build_queue_classifies_needs_fix_vs_ok():
    fake_catalog = json.dumps([
        {"product_id": "DP1026", "etsy_listing_id": "100", "category": "digital_planner"},
        {"product_id": "WA1090", "etsy_listing_id": "101", "category": "wall_art"},
        {"product_id": "MISC_X", "etsy_listing_id": "102", "category": "uncategorized"},
        {"product_id": "NOLISTING", "etsy_listing_id": "", "category": "wall_art"},
    ])
    live_by_id = {
        "100": {"sku": "DP1026", "taxonomy_id": 2078},   # already correct
        "101": {"sku": None, "taxonomy_id": 2078},        # wrong sku
    }
    with patch.object(Path, "read_text", return_value=fake_catalog), \
         patch.object(server, "EtsyAPIClient") as MockClient, \
         patch.object(server, "_resolve_category_taxonomy_id", side_effect=lambda c: {"digital_planner": 2078, "wall_art": 2078}.get(c)):
        MockClient.return_value.get_listing.side_effect = lambda lid: live_by_id[lid]
        queue = server._build_sku_taxonomy_backfill_queue()
    check(set(queue.keys()) == {"DP1026", "WA1090"},
          f"uncategorized and no-listing entries must be excluded, got {sorted(queue.keys())}")
    check(queue["DP1026"]["status"] == "ok", f"already-correct listing must be ok, got {queue['DP1026']}")
    check(queue["WA1090"]["status"] == "needs_fix", f"sku-mismatched listing must need a fix, got {queue['WA1090']}")
    check(queue["WA1090"]["target_sku"] == "WA1090", f"target sku must be the product_id, got {queue['WA1090']}")


def test_build_queue_skips_a_listing_whose_fetch_fails():
    fake_catalog = json.dumps([
        {"product_id": "BROKEN", "etsy_listing_id": "999", "category": "wall_art"},
    ])
    with patch.object(Path, "read_text", return_value=fake_catalog), \
         patch.object(server, "EtsyAPIClient") as MockClient, \
         patch.object(server, "_resolve_category_taxonomy_id", return_value=2078):
        MockClient.return_value.get_listing.side_effect = Exception("boom")
        queue = server._build_sku_taxonomy_backfill_queue()
    check(queue == {}, f"a listing whose fetch fails must be skipped this round, got {queue}")


# ── _run_sku_taxonomy_backfill_batch ───────────────────────────────────────

def test_batch_stages_up_to_the_batch_size_cap():
    with _use_tmp_queue_path():
        queue = {
            f"WA10{i}": {"listing_id": 3000 + i, "category": "wall_art", "target_sku": f"WA10{i}",
                          "target_taxonomy_id": 2078, "status": "needs_fix"}
            for i in range(25)
        }
        server._write_sku_taxonomy_backfill_queue(queue)
        with patch.object(server, "EtsyAPIClient") as MockClient:
            MockClient.return_value.get_listing.side_effect = lambda lid: {"sku": None, "taxonomy_id": None, "state": "active"}
            result = server._run_sku_taxonomy_backfill_batch()
        check(result["staged"] == server._BACKFILL_BATCH_SIZE,
              f"must stage exactly _BACKFILL_BATCH_SIZE ({server._BACKFILL_BATCH_SIZE}), got {result['staged']}")
        reloaded = server._read_sku_taxonomy_backfill_queue()
        staged_count = sum(1 for e in reloaded.values() if e["status"] == "staged")
        check(staged_count == server._BACKFILL_BATCH_SIZE, f"got {staged_count}")


def test_batch_skips_entries_already_pending_in_action_center():
    with _use_tmp_queue_path():
        lid = 4001
        queue = {"WA_DUP": {"listing_id": lid, "category": "wall_art", "target_sku": "WA_DUP",
                             "target_taxonomy_id": 2078, "status": "needs_fix"}}
        server._write_sku_taxonomy_backfill_queue(queue)
        db.enqueue_action("update_sku_and_category", "already pending", {"listing_id": lid, "sku": "WA_DUP"})
        with patch.object(server, "EtsyAPIClient") as MockClient:
            MockClient.return_value.get_listing.return_value = {"sku": None, "taxonomy_id": None, "state": "active"}
            result = server._run_sku_taxonomy_backfill_batch()
        check(result["staged"] == 0, f"an already-pending listing must not be staged again, got {result}")
        reloaded = server._read_sku_taxonomy_backfill_queue()
        check(reloaded["WA_DUP"]["status"] == "needs_fix",
              f"status must stay needs_fix (not falsely marked staged), got {reloaded['WA_DUP']['status']}")


def test_batch_marks_ok_when_recheck_shows_already_correct():
    with _use_tmp_queue_path():
        lid = 4002
        queue = {"WA_FIXED": {"listing_id": lid, "category": "wall_art", "target_sku": "WA_FIXED",
                               "target_taxonomy_id": 2078, "status": "needs_fix"}}
        server._write_sku_taxonomy_backfill_queue(queue)
        with patch.object(server, "EtsyAPIClient") as MockClient:
            # Someone (or a prior partial run) already fixed this on Etsy directly.
            MockClient.return_value.get_listing.return_value = {"sku": "WA_FIXED", "taxonomy_id": 2078, "state": "active"}
            result = server._run_sku_taxonomy_backfill_batch()
        check(result["staged"] == 0, f"nothing to stage when the live re-check already matches, got {result}")
        reloaded = server._read_sku_taxonomy_backfill_queue()
        check(reloaded["WA_FIXED"]["status"] == "ok", f"must reclassify as ok, got {reloaded['WA_FIXED']['status']}")


def test_batch_builds_queue_lazily_on_first_run():
    # Mocks the queue read/write helpers directly (rather than combining
    # _use_tmp_queue_path()'s real disk I/O with a global Path.read_text
    # patch for the catalog fetch) -- both the queue file and
    # product_catalog.json go through the same Path.read_text, so a global
    # patch can't distinguish which one's being read; this isolates the
    # "no queue file yet" scenario cleanly instead.
    built_queue = {"WA_LAZY": {"listing_id": "5001", "category": "wall_art", "target_sku": "WA_LAZY",
                                "target_taxonomy_id": 2078, "status": "needs_fix"}}
    written = {}
    with patch.object(server, "_read_sku_taxonomy_backfill_queue", return_value={}), \
         patch.object(server, "_build_sku_taxonomy_backfill_queue", return_value=built_queue), \
         patch.object(server, "_write_sku_taxonomy_backfill_queue", side_effect=lambda q: written.update(final=dict(q))), \
         patch.object(server, "EtsyAPIClient") as MockClient:
        MockClient.return_value.get_listing.return_value = {"sku": None, "taxonomy_id": None, "state": "active"}
        result = server._run_sku_taxonomy_backfill_batch()
    check(result["staged"] == 1, f"first-ever run must build the queue and stage the one needs_fix entry, got {result}")
    check(written.get("final", {}).get("WA_LAZY", {}).get("status") == "staged",
          f"the newly-built queue must be persisted with the staged status, got {written}")


def test_batch_reports_completion_when_nothing_needs_fixing():
    with _use_tmp_queue_path():
        server._write_sku_taxonomy_backfill_queue({
            "WA_DONE": {"listing_id": 6001, "category": "wall_art", "target_sku": "WA_DONE",
                        "target_taxonomy_id": 2078, "status": "ok"},
        })
        result = server._run_sku_taxonomy_backfill_batch()
    check(result["staged"] == 0, f"got {result}")
    check("complete" in result["detail"], f"expected a completion message, got {result['detail']!r}")


# ── _mark_backfill_queue_done ──────────────────────────────────────────────

def test_mark_backfill_queue_done_matches_by_listing_id():
    with _use_tmp_queue_path():
        server._write_sku_taxonomy_backfill_queue({
            "A": {"listing_id": 7001, "status": "staged"},
            "B": {"listing_id": 7002, "status": "staged"},
        })
        server._mark_backfill_queue_done(7002)
        reloaded = server._read_sku_taxonomy_backfill_queue()
        check(reloaded["A"]["status"] == "staged", "unrelated entry must be untouched")
        check(reloaded["B"]["status"] == "done", f"got {reloaded['B']['status']}")


def test_mark_backfill_queue_done_is_a_no_op_for_unknown_listing():
    with _use_tmp_queue_path():
        server._write_sku_taxonomy_backfill_queue({"A": {"listing_id": 7003, "status": "staged"}})
        server._mark_backfill_queue_done(999999)  # must not raise
        reloaded = server._read_sku_taxonomy_backfill_queue()
        check(reloaded["A"]["status"] == "staged", "unrelated entry must be untouched")


# ── stage_product_publish() sets sku ────────────────────────────────────────

def test_stage_product_publish_sets_sku_to_product_id():
    import asyncio
    fake_review = {
        "listing_id": "",
        "category": "wall_art",
        "has_content": True,
        "qc": {"verdict": "pass"},
        "deliverables": [{"name": "WA9999_print_sizes.zip", "rel": "WA9999_print_sizes.zip", "exists": True}],
        "photos": [],
        "content": {"title": "T", "description": "D", "tags": ["t"], "price": 6.99},
    }
    with patch.object(server, "_gather_product_review", return_value=fake_review), \
         patch.object(server, "_resolve_category_taxonomy_id", return_value=2097), \
         patch.object(server.db, "list_actions", return_value=[]), \
         patch.object(server, "_validate_staged_action", return_value=(True, "ok")), \
         patch.object(server.db, "enqueue_action", return_value=1) as mock_enqueue:
        asyncio.run(server.stage_product_publish("WA9999", _token="test"))
    payload = mock_enqueue.call_args[0][2]
    check(payload["listing_data"]["sku"] == "WA9999",
          f"listing_data must set sku to the product_id, got {payload['listing_data'].get('sku')!r}")


# ── check_attributes(): new SKU check ───────────────────────────────────────

def test_check_attributes_warns_on_sku_mismatch():
    listing = {"who_made": "i_did", "when_made": "made_to_order", "is_supply": False,
               "taxonomy_id": 2078, "sku": "WRONG"}
    issues = lic.check_attributes(listing, {}, dp_codes=["DP1026"])
    sku_issues = [i for i in issues if i["check"] == "sku"]
    check(len(sku_issues) == 1, f"expected one sku WARN, got {sku_issues}")
    check(sku_issues[0]["severity"] == "WARN", f"got {sku_issues[0]}")


def test_check_attributes_no_issue_when_sku_matches():
    listing = {"who_made": "i_did", "when_made": "made_to_order", "is_supply": False,
               "taxonomy_id": 2078, "sku": "DP1026"}
    issues = lic.check_attributes(listing, {}, dp_codes=["DP1026"])
    check(not any(i["check"] == "sku" for i in issues), f"got {issues}")


def test_check_attributes_skips_sku_check_for_zero_or_multiple_dp_codes():
    listing = {"who_made": "i_did", "when_made": "made_to_order", "is_supply": False,
               "taxonomy_id": 2078, "sku": "WRONG"}
    issues_zero = lic.check_attributes(listing, {}, dp_codes=[])
    issues_multi = lic.check_attributes(listing, {}, dp_codes=["DP1026", "DP1027"])
    issues_none = lic.check_attributes(listing, {})
    check(not any(i["check"] == "sku" for i in issues_zero), "zero dp_codes must skip the sku check")
    check(not any(i["check"] == "sku" for i in issues_multi), "multiple dp_codes must skip the sku check (ambiguous)")
    check(not any(i["check"] == "sku" for i in issues_none), "dp_codes omitted entirely must skip the sku check")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("SKU/CATEGORY BACKFILL TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("SKU/CATEGORY BACKFILL TESTS OK — update_sku_and_category staging/execution, the "
          "durable work-queue + weekly-paced batch loop, stage_product_publish's new-listing "
          "sku, and check_attributes()'s SKU WARN all verified.")


if __name__ == "__main__":
    run()
