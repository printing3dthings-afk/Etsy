"""
Tests for the 2026-08-05 full-Etsy-audit fix: stage_action (the general-
purpose staging tool) and stage_batch_tag_update used to call straight
through to _validate_staged_action/db.enqueue_action for update_title/
update_tags/update_description with ZERO manifest-mapping check -- Claude
could invent plausible-sounding content for a listing Frank has no local
record of at all and stage it for Scott's approval, no different in kind
from the koozie/planner listing-mismatch bug that request_listing_fix() and
autofix_listing_tags/autofix_listing_title were already fixed for on
2026-08-05. This was actually the MORE dangerous gap of the two: stage_action
is the tool the system prompt tells Claude to reach for on ANY listing
content fix ("Use for fixes you can fully specify: correcting a listing
title, replacing its tags"), so it's the most commonly-reachable path for
this exact defect class, not a rare one.

Checks:
  1. stage_action / update_title for an unmapped listing_id with no `reason`
     -> refused, nothing staged.
  2. stage_action / update_title for an unmapped listing_id WITH a `reason`
     -> proceeds normally (real human/agent-supplied grounding).
  3. stage_action / update_title for a MAPPED listing_id with no `reason`
     -> proceeds normally (existing manifest entry is itself the grounding).
  4. stage_action / update_tags and update_description get the same gate.
  5. stage_action / toggle_listing_state (a non-content-writing type) is NOT
     gated -- this check only applies to types that write new title/tags/
     description text.
  6. stage_batch_tag_update with a mix of mapped and unmapped listing_ids ->
     only the mapped one gets tags generated/staged; the unmapped one lands
     in `errors`, not silently dropped and not silently staged.

Run: python tests/test_stage_action_grounding_gate.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_stageaction_gate_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "stageaction-gate-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _mapped_entry(_lid):
    return {"dp_codes": ["DP1026"], "type": "planner"}


def _unmapped_entry(_lid):
    return None


def test_stage_action_update_title_unmapped_no_reason_is_refused():
    with patch.object(server, "_get_manifest_entry", side_effect=_unmapped_entry):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "update_title", "listing_id": 4509179201,
            "summary": "fix title", "title": "A totally made-up title",
        })
    check("error" in result, f"expected a refusal error, got: {result}")
    check(result.get("staged") is not True, f"must not stage anything, got: {result}")
    check(str(4509179201) not in "".join(str(a) for a in server.db.list_actions("pending")),
          "no pending action should have been enqueued for the unmapped listing")


def test_stage_action_update_title_unmapped_with_reason_proceeds():
    with patch.object(server, "_get_manifest_entry", side_effect=_unmapped_entry):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "update_title", "listing_id": 4509179202,
            "summary": "fix title", "title": "Digital Budget Planner 2026, GoodNotes, Instant Download",
            "reason": "Scott said the title is missing the app name",
        })
    check(result.get("staged") is True, f"a real reason must let staging proceed, got: {result}")


def test_stage_action_update_title_mapped_no_reason_proceeds():
    with patch.object(server, "_get_manifest_entry", side_effect=_mapped_entry):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "update_title", "listing_id": 4509179203,
            "summary": "fix title", "title": "Digital Budget Planner 2026, GoodNotes, Instant Download",
        })
    check(result.get("staged") is True, f"a mapped listing needs no extra reason, got: {result}")


def test_stage_action_update_tags_and_description_also_gated():
    with patch.object(server, "_get_manifest_entry", side_effect=_unmapped_entry):
        tags_result = server._execute_agent_tool("stage_action", {
            "action_type": "update_tags", "listing_id": 4509179204,
            "summary": "fix tags", "tags": [f"tag {i}" for i in range(13)],
        })
        desc_result = server._execute_agent_tool("stage_action", {
            "action_type": "update_description", "listing_id": 4509179205,
            "summary": "fix desc", "description": "x" * 400,
        })
    check("error" in tags_result, f"update_tags must also be gated, got: {tags_result}")
    check("error" in desc_result, f"update_description must also be gated, got: {desc_result}")


def test_stage_action_non_content_type_is_not_gated():
    # toggle_listing_state doesn't write new title/tags/description text --
    # it must not be blocked just because the listing is unmapped.
    with patch.object(server, "_get_manifest_entry", side_effect=_unmapped_entry), \
         patch.object(server, "EtsyAPIClient", return_value=MagicMock(
             get_listing=lambda lid: {"listing_id": lid, "state": "inactive"})):
        result = server._execute_agent_tool("stage_action", {
            "action_type": "toggle_listing_state", "listing_id": 4509179206,
            "summary": "reactivate", "new_state": "active",
        })
    check(result.get("staged") is True, f"toggle_listing_state must not be gated, got: {result}")


def test_stage_batch_tag_update_mixed_mapped_unmapped():
    def fake_get_manifest_entry(lid):
        return {"dp_codes": ["DP1026"]} if lid == 4509179207 else None

    fake_listings = {
        4509179207: {"listing_id": 4509179207, "title": "Mapped Listing", "tags": [], "price": 12.99},
        4509179208: {"listing_id": 4509179208, "title": "Unmapped Listing", "tags": [], "price": 9.99},
    }

    def fake_get_listing(lid):
        return fake_listings[lid]

    fake_tags = [f"tag {i}" for i in range(13)]

    with patch.object(server, "_get_manifest_entry", side_effect=fake_get_manifest_entry), \
         patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=fake_get_listing)), \
         patch.object(server, "_generate_tags_for_listings",
                       return_value=[{"listing_id": 4509179207, "tags": fake_tags}]) as mock_gen:
        result = server._execute_agent_tool("stage_batch_tag_update", {
            "listing_ids": [4509179207, 4509179208],
        })

    check(result["count"] == 1, f"only the mapped listing should get tags staged, got: {result}")
    check(len(result["staged"]) == 1 and result["staged"][0]["listing_id"] == 4509179207,
          f"expected only 4509179207 staged, got: {result['staged']}")
    check(any(e.get("listing_id") == 4509179208 for e in result["errors"]),
          f"the unmapped listing must surface in errors, not silently vanish, got: {result['errors']}")
    # The unmapped listing must never even reach the tag-generation call.
    passed_listings = mock_gen.call_args[0][0]
    check(all(l["listing_id"] != 4509179208 for l in passed_listings),
          f"unmapped listing must be filtered out before tag generation, got: {passed_listings}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("STAGE-ACTION GROUNDING GATE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("STAGE-ACTION GROUNDING GATE TESTS OK — stage_action refuses blind content rewrites for "
          "unmapped listings (unless given a real reason), lets mapped listings and non-content "
          "action types through untouched, and stage_batch_tag_update filters unmapped listings "
          "out of the batch instead of silently generating tags for them.")


if __name__ == "__main__":
    run()
