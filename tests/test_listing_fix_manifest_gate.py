"""
Tests for request_listing_fix()'s manifest-mapping gate (2026-07-22, revised
2026-08-05).

"Ask Frank to Fix" on the Listings screen tells Scott, in its own popup copy,
that Frank "will check what's wrong" before fixing anything. But the real
diagnosis (listing_integrity_check.audit_listing()) can only run for a
listing that has an entry in data/listing_manifest.json -- before the
2026-07-22 fix, an unmapped listing silently skipped the check entirely and
still staged a clean, warning-free republish action, indistinguishable from
"checked it and it's genuinely fine."

2026-08-05 revision: that fix still unconditionally generated and staged a
blind LLM title/tags rewrite for unmapped listings ("helpful default" -- see
the removed test below), reasoning only from the listing's own possibly-wrong
existing title/tags/description with zero grounding on what the product
actually is. This is exactly how 3 untracked listings (a mini cooler jug
titled "Kawaii Blue/Red Drink Koozie", and an unrelated listing titled
"Kawaii Digital Planner 2026" showing the same koozie photo) ended up with
Frank confidently proposing MORE wrong text instead of flagging that it had
no idea what the product was. Now: an unmapped listing with no Scott-supplied
instructions gets NO title/tags fix staged at all -- just the unfixable-issue
+ todo, same fail-closed philosophy listing_compliance_sweep.py already
applies shop-wide, now correctly extended to the generation step itself, not
just the diagnosis step. If Scott types instructions in the fix modal (real
human grounding), the fix still generates normally even when unmapped.

Checks:
  1. Unmapped listing, no instructions -> unfixable_issues carries a
     no_manifest_mapping entry, the staged republish action's summary
     carries the warning text, a scott_only todo is created, and NO
     title/tags fix is staged (the actual 2026-08-05 fix).
  2. Unmapped listing WITH Scott-typed instructions -> title/tags fix IS
     staged, since a human supplied real grounding.
  3. Diagnosis lookup itself failing (manifest load raises) -> same
     fail-closed skip as "unmapped", not a silent fall-through to the old
     blind-generate behavior.
  4. Mapped listing with only title/tag-fixable FAILs -> unchanged existing
     behavior: diagnosis feeds the reason, no unfixable issue, no warning.
  5. Mapped listing with a non-title/tag FAIL -> unchanged existing
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


def _fake_listing(listing_id: int, state: str = "inactive") -> dict:
    return {
        "listing_id": listing_id,
        "title": "Some Listing Title",
        "price": {"amount": 1499, "divisor": 100},
        "tags": ["a", "b"],
        "state": state,
    }


def _run_request_fix(listing_id: int, manifest: dict, audit_result: dict | None, state: str = "inactive",
                      instructions: str = "", load_json_side_effect=None):
    fake_tags = [f"tag {i}" for i in range(13)]
    load_json_kwargs = {"side_effect": load_json_side_effect} if load_json_side_effect else {"return_value": manifest}
    with patch.object(server, "ANTHROPIC_KEY", "fake-key"), \
         patch.object(server, "_generate_tags_for_listings", return_value=[{"tags": fake_tags}]), \
         patch.object(server, "_anthropic_create", return_value=_fake_anthropic_response("New Title Here")), \
         patch.object(server, "EtsyAPIClient", return_value=MagicMock(get_listing=lambda lid: _fake_listing(lid, state))), \
         patch.object(lic, "_load_json", **load_json_kwargs), \
         patch.object(lic, "audit_listing", return_value=audit_result or {}):
        return asyncio.run(server.request_listing_fix(listing_id, body={"instructions": instructions}))


def test_unmapped_listing_skips_blind_title_tags_fix():
    listing_id = 9991001
    result = _run_request_fix(listing_id, manifest={}, audit_result=None)

    check(result["staged_count"] == 1,
          f"expected only the republish staged (no blind title/tags fix), got {result['staged_count']}: {result}")
    check(len(result["unfixable_issues"]) == 1,
          f"expected exactly one unfixable issue (no_manifest_mapping), got {result['unfixable_issues']}")
    check("no record of what this product actually is" in result["unfixable_issues"][0].lower()
          or "no entry" in result["unfixable_issues"][0].lower(),
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
    check(tag_staged is None,
          "2026-08-05: tags must NOT be blind-generated for an unmapped listing -- Frank has no "
          "grounding on what the product is, so a rewrite just produces a more confident wrong tag set")
    check(title_staged is None,
          "2026-08-05: title must NOT be blind-generated for an unmapped listing -- this exact "
          "behavior produced the koozie/planner title-mismatch bug")
    check(len(result["errors"]) == 0,
          f"skipping the fix deliberately should not be reported as an error, got {result['errors']}")


def test_unmapped_listing_with_instructions_still_generates_fix():
    # A human (Scott) typing real instructions IS grounding, even without a
    # manifest entry -- the gate is "does Frank know anything real about this
    # product," not "is it in the manifest" specifically.
    listing_id = 9991005
    result = _run_request_fix(listing_id, manifest={}, audit_result=None,
                               instructions="This is actually a mini cooler jug, not a koozie -- retitle accordingly")

    check(result["staged_count"] == 3,
          f"expected tags + title + republish staged once Scott supplied real grounding, got {result['staged_count']}: {result}")
    tag_staged = next((s for s in result["staged"] if s["type"] == "update_tags"), None)
    title_staged = next((s for s in result["staged"] if s["type"] == "update_title"), None)
    check(tag_staged is not None, "tags should be staged when Scott provided instructions")
    check(title_staged is not None, "title should be staged when Scott provided instructions")


def test_diagnosis_lookup_failure_also_skips_blind_fix():
    # If Frank can't even determine whether the listing is mapped (manifest
    # load itself raises), that's the same fail-closed case as unmapped --
    # not a silent fall-through to the old blind-generate behavior.
    listing_id = 9991006
    result = _run_request_fix(listing_id, manifest={}, audit_result=None,
                               load_json_side_effect=RuntimeError("disk read failed"))

    check(result["staged_count"] == 1,
          f"expected only the republish staged when diagnosis lookup itself failed, got {result['staged_count']}: {result}")
    check(len(result["unfixable_issues"]) == 1,
          f"expected one unfixable issue (diagnosis_lookup_failed), got {result['unfixable_issues']}")
    tag_staged = next((s for s in result["staged"] if s["type"] == "update_tags"), None)
    title_staged = next((s for s in result["staged"] if s["type"] == "update_title"), None)
    check(tag_staged is None, "a failed diagnosis lookup must not fall through to a blind fix")
    check(title_staged is None, "a failed diagnosis lookup must not fall through to a blind fix")


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


def test_active_listing_skips_meaningless_republish_staging():
    # 2026-07-30: the Listings-tab "Ask Frank to Fix" button used to only
    # render for inactive/FAIL listings, so this endpoint was never reachable
    # for an already-active one. Now it's offered on every listing -- for an
    # active one, staging a "Republish..." action is a no-op PATCH
    # (client.update_listing(lid, {"state": "active"})) dressed up as a
    # meaningful approval. Confirms it's skipped entirely rather than shown.
    listing_id = 9991004
    manifest = {str(listing_id): {"dp_codes": ["DP1026"], "type": "planner"}}
    audit_result = {"issues": []}
    result = _run_request_fix(listing_id, manifest=manifest, audit_result=audit_result, state="active")

    republish = next((s for s in result["staged"] if s["type"] == "publish_listing"), None)
    check(republish is None,
          f"an already-active listing should not get a republish action staged, got {result['staged']}")
    check(result["staged_count"] == 2,
          f"expected only tags + title staged for an active listing, got {result['staged_count']}: {result}")


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
          "clean republish OR a blind title/tags rewrite; it blocks with a real warning + todo "
          "unless Scott supplies real grounding via instructions, while the mapped-listing path "
          "(both fixable and unfixable FAILs) is unchanged.")


if __name__ == "__main__":
    run()
