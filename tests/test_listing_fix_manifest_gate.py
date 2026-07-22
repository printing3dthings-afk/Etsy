"""
Tests for request_listing_fix()'s manifest-mapping gate (2026-07-22).

"Ask Frank to Fix" on the Listings screen tells Scott, in its own popup copy,
that Frank "will check what's wrong" before fixing anything. But the real
diagnosis (listing_integrity_check.audit_listing()) can only run for a
listing that has an entry in data/listing_manifest.json -- before this fix,
an unmapped listing silently skipped the check entirely and still staged a
clean, warning-free republish action, indistinguishable from "checked it and
it's genuinely fine." That risked one-tap-reactivating something Scott
deliberately took down for a reason the automated checks don't cover.

This mirrors the fail-closed philosophy listing_compliance_sweep.py already
applies shop-wide (_unmapped_result(): "unmapped/unresolved must block,
never silently pass") -- request_listing_fix() now does the same for the
single-listing case.

Checks:
  1. Unmapped listing -> unfixable_issues carries a no_manifest_mapping
     entry, the staged republish action's summary carries the warning text,
     a scott_only todo is created, and title/tags are still staged normally
     (never left un-actioned).
  2. Mapped listing with only title/tag-fixable FAILs -> unchanged existing
     behavior: diagnosis feeds the reason, no unfixable issue, no warning.
  3. Mapped listing with a non-title/tag FAIL -> unchanged existing
     behavior: that FAIL surfaces as an unfixable issue (regression guard
     that this change didn't alter the already-working mapped path).

Run: python tests/test_listing_fix_manifest_gate.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_listingfix_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "listingfix-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import listing_integrity_check as lic  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_anthropic_response(text: str):
    block = MagicMock()
    block.text = text
    resp = MagicMock()
    resp.content = [block]
    return resp


def _fake_listing(listing_id: int) -> dict:
    return {
        "listing_id": listing_id,
        "title": "Some Listing Title",
        "price": {"amount": 1499, "divisor": 100},
        "tags": ["a", "b"],
        "state": "inactive",
    }


def _run_request_fix(listing_id: int, manifest: dict, audit_result: dict | None):
    fake_tags = [f"tag {i}" for i in range(13)]
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_generate_tags_for_listings", return_value=[{"tags": fake_tags}]), \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response("New Title Here")), \
         patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: _fake_listing(lid))), \
         patch.object(lic, "_load_json", return_value=manifest), \
         patch.object(lic, "audit_listing", return_value=audit_result or {}):
        return asyncio.run(server.request_listing_fix(listing_id, body={"instructions": ""}))


def test_unmapped_listing_blocks_silent_republish():
    listing_id = 9991001
    result = _run_request_fix(listing_id, manifest={}, audit_result=None)

    check(result["staged_count"] == 3,
          f"expected tags + title + republish all staged, got {result['staged_count']}: {result}")
    check(len(result["unfixable_issues"]) == 1,
          f"expected exactly one unfixable issue (no_manifest_mapping), got {result['unfixable_issues']}")
    check("no manifest" in result["unfixable_issues"][0].lower() or "no entry" in result["unfixable_issues"][0].lower(),
          f"expected the no_manifest_mapping detail text, got {result['unfixable_issues'][0]!r}")

    republish = next((s for s in result["staged"] if s["type"] == "publish_listing"), None)
    check(republish is not None, "expected a publish_listing action to still be staged")
    queued = server.db.get_action(republish["action_id"])
    check("NOT fully fixed" in queued["summary"],
          f"republish summary should carry the warning, got: {queued['summary']!r}")
    check("no_manifest_mapping" in queued["summary"] or "manifest" in queued["summary"].lower(),
          f"republish summary should name the actual gap, got: {queued['summary']!r}")

    check(result["todo_id"] is not None, "expected a todo to be created for the unmapped listing")
    todos = server.db.list_todos()
    matching = [t for t in todos if t.get("id") == result["todo_id"]]
    check(len(matching) == 1, f"expected the staged todo_id to resolve to a real todo, got {matching}")
    if matching:
        check(matching[0].get("category") == "scott_only",
              f"expected a scott_only todo, got category={matching[0].get('category')!r}")

    tag_staged = next((s for s in result["staged"] if s["type"] == "update_tags"), None)
    title_staged = next((s for s in result["staged"] if s["type"] == "update_title"), None)
    check(tag_staged is not None, "tags should still be staged for an unmapped listing (helpful default)")
    check(title_staged is not None, "title should still be staged for an unmapped listing (helpful default)")


def test_mapped_listing_fixable_fail_unchanged():
    listing_id = 9991002
    manifest = {str(listing_id): {"dp_codes": ["DP1026"], "type": "planner"}}
    audit_result = {"issues": [
        {"severity": "FAIL", "check": "title_length", "detail": "Title is 82 chars, over the 70-char limit"},
    ]}
    result = _run_request_fix(listing_id, manifest=manifest, audit_result=audit_result)

    check(result["unfixable_issues"] == [],
          f"a purely title/tag-fixable FAIL should not become an unfixable issue, got {result['unfixable_issues']}")
    republish = next((s for s in result["staged"] if s["type"] == "publish_listing"), None)
    queued = server.db.get_action(republish["action_id"])
    check("NOT fully fixed" not in queued["summary"],
          f"no unfixable issue -> no warning expected in summary, got: {queued['summary']!r}")


def test_mapped_listing_unfixable_fail_unchanged():
    listing_id = 9991003
    manifest = {str(listing_id): {"dp_codes": ["DP1026"], "type": "planner"}}
    audit_result = {"issues": [
        {"severity": "FAIL", "check": "quantity_claim_mismatch",
         "detail": "Title claims quantity [4] but the listing currently has 2 file(s) attached."},
    ]}
    result = _run_request_fix(listing_id, manifest=manifest, audit_result=audit_result)

    check(len(result["unfixable_issues"]) == 1,
          f"expected the quantity_claim_mismatch FAIL to surface as unfixable, got {result['unfixable_issues']}")
    check("quantity" in result["unfixable_issues"][0].lower(),
          f"expected the real diagnosis detail preserved, got {result['unfixable_issues'][0]!r}")
    republish = next((s for s in result["staged"] if s["type"] == "publish_listing"), None)
    queued = server.db.get_action(republish["action_id"])
    check("NOT fully fixed" in queued["summary"],
          f"a real unfixable issue should still warn in the republish summary, got: {queued['summary']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("LISTING FIX MANIFEST GATE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("LISTING FIX MANIFEST GATE TESTS OK — an unmapped listing no longer silently stages a "
          "clean republish; it blocks with a real warning + todo, while the mapped-listing path "
          "(both fixable and unfixable FAILs) is unchanged.")


if __name__ == "__main__":
    run()
