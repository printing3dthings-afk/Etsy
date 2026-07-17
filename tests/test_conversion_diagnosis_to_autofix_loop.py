"""
Tests for Frank upgrade Wave 4, item B2 (2026-07-17).

diagnose_listing_conversion (_diagnose_listing_core) already pulled real
views/favorites/sales and produced a genuine per-listing diagnosis via
Claude, but was read-only and dead-ended -- its findings never reached
_autofix_title_core/_autofix_tags_core/_autofix_description_core, even
though all three already accept a `reason` string. This adds
apply_conversion_fixes / _apply_conversion_fixes_core, which runs a fresh
diagnosis and stages a fix for every finding in a fixable area
(title/tags/description), using "finding -> fix" as the reason/corrective
guidance fed into the same already-existing, already-staging-gated autofix
functions B3 just made real for descriptions too.

Everything here still goes through the Action Center -- this connects two
already-staging-gated systems, it never bypasses staging for either.

Run: python tests/test_conversion_diagnosis_to_autofix_loop.py
"""
import asyncio
import os
import sys
import tempfile
import traceback
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_diag_loop_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "diag-loop-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


_SAMPLE_DIAGNOSIS = {
    "listing_id": 4509179201,
    "diagnosis": {
        "primary_issue": "Title doesn't lead with the primary keyword.",
        "fixes": [
            {"area": "title", "priority": "high", "finding": "Title buries the keyword",
             "fix": "Move 'digital planner' to the first 20 characters", "impact": "more clicks"},
            {"area": "tags", "priority": "medium", "finding": "Only 10/13 tags used",
             "fix": "Add 3 more buyer-intent tags", "impact": "more search coverage"},
            {"area": "description", "priority": "medium", "finding": "Hook is generic",
             "fix": "Rewrite the hook to be more specific", "impact": "better dwell time"},
            {"area": "photos", "priority": "critical", "finding": "Only 6/10 photos",
             "fix": "Generate the remaining 4 photos", "impact": "big CTR gain"},
            {"area": "price", "priority": "low", "finding": "Priced below comparable listings",
             "fix": "Consider raising price by $1", "impact": "higher perceived value"},
        ],
    },
}


def test_registered_as_agent_tool():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("apply_conversion_fixes" in names, "apply_conversion_fixes must be in AGENT_TOOLS")


def test_fix_handlers_cover_exactly_the_three_automatable_areas():
    check(set(server._CONVERSION_FIX_HANDLERS.keys()) == {"title", "tags", "description"},
          f"expected exactly title/tags/description, got: {list(server._CONVERSION_FIX_HANDLERS.keys())}")


def test_applies_fixable_areas_and_skips_unfixable_ones():
    async def fake_diagnose(listing_id):
        return dict(_SAMPLE_DIAGNOSIS)

    async def fake_title_fix(lid, listing=None, reason=""):
        return {"action_id": 111, "title": "new title", "listing_id": lid, "_reason_seen": reason}

    async def fake_tags_fix(lid, listing=None, reason=""):
        return {"action_id": 222, "tags": ["a"], "listing_id": lid, "_reason_seen": reason}

    async def fake_desc_fix(lid, listing=None, reason="", assume_wall_art=False):
        return {"action_id": 333, "new_hook": "new hook", "listing_id": lid, "_reason_seen": reason}

    with patch.object(server, "_diagnose_listing_core", fake_diagnose), \
         patch.object(server, "_autofix_title_core", fake_title_fix), \
         patch.object(server, "_autofix_tags_core", fake_tags_fix), \
         patch.object(server, "_autofix_description_core", fake_desc_fix):
        # _CONVERSION_FIX_HANDLERS captured the original functions at module-load
        # time via lambdas that call server._autofix_title_core etc by name at
        # call time (not by reference) -- confirm that's really true by checking
        # the lambdas resolve the patched versions.
        result = asyncio.run(server._apply_conversion_fixes_core(4509179201))

    applied_areas = {a["area"] for a in result["applied"]}
    check(applied_areas == {"title", "tags", "description"},
          f"expected all 3 fixable areas applied, got: {result['applied']}")
    check(len(result["applied"]) == 3, f"expected exactly 3 applied fixes, got: {result['applied']}")

    skipped_areas = {s["area"] for s in result["skipped"]}
    check(skipped_areas == {"photos", "price"},
          f"expected photos+price skipped as unfixable, got: {result['skipped']}")
    for s in result["skipped"]:
        check("no automated fix" in s["reason"], f"skip reason should explain why, got: {s}")

    check(result["errors"] == [], f"expected no errors, got: {result['errors']}")
    check(result["primary_issue"] == _SAMPLE_DIAGNOSIS["diagnosis"]["primary_issue"],
          f"expected the primary_issue surfaced, got: {result['primary_issue']}")

    title_applied = next(a for a in result["applied"] if a["area"] == "title")
    check(title_applied["finding"] == "Title buries the keyword", f"got: {title_applied}")
    check(title_applied["fix"] == "Move 'digital planner' to the first 20 characters", f"got: {title_applied}")


def test_reason_text_combines_finding_and_fix():
    captured_reasons = {}

    async def fake_diagnose(listing_id):
        return {"listing_id": listing_id, "diagnosis": {"primary_issue": "x", "fixes": [
            {"area": "title", "finding": "Finding text", "fix": "Fix text"},
        ]}}

    async def capture_title_fix(lid, listing=None, reason=""):
        captured_reasons["title"] = reason
        return {"action_id": 1, "listing_id": lid}

    with patch.object(server, "_diagnose_listing_core", fake_diagnose), \
         patch.object(server, "_autofix_title_core", capture_title_fix):
        asyncio.run(server._apply_conversion_fixes_core(123))

    check(captured_reasons.get("title") == "Finding text → Fix text",
          f"expected the combined finding+fix reason text, got: {captured_reasons.get('title')!r}")


def test_handles_errors_from_a_fix_gracefully():
    async def fake_diagnose(listing_id):
        return {"listing_id": listing_id, "diagnosis": {"primary_issue": "x", "fixes": [
            {"area": "title", "finding": "f", "fix": "x"},
            {"area": "tags", "finding": "f2", "fix": "x2"},
        ]}}

    async def failing_title_fix(lid, listing=None, reason=""):
        raise RuntimeError("simulated Etsy API failure")

    async def ok_tags_fix(lid, listing=None, reason=""):
        return {"action_id": 5, "listing_id": lid}

    with patch.object(server, "_diagnose_listing_core", fake_diagnose), \
         patch.object(server, "_autofix_title_core", failing_title_fix), \
         patch.object(server, "_autofix_tags_core", ok_tags_fix):
        result = asyncio.run(server._apply_conversion_fixes_core(123))

    check(len(result["errors"]) == 1, f"expected 1 captured error, got: {result['errors']}")
    check(result["errors"][0]["area"] == "title", f"got: {result['errors']}")
    check("simulated Etsy API failure" in result["errors"][0]["error"], f"got: {result['errors']}")
    check(len(result["applied"]) == 1 and result["applied"][0]["area"] == "tags",
          f"a failure in one area must not block the others, got: {result['applied']}")


def test_empty_diagnosis_returns_clean_no_op_message():
    async def fake_diagnose(listing_id):
        return {"listing_id": listing_id, "diagnosis": {"primary_issue": "All good", "fixes": []}}

    with patch.object(server, "_diagnose_listing_core", fake_diagnose):
        result = asyncio.run(server._apply_conversion_fixes_core(123))

    check(result["applied"] == [] and result["skipped"] == [] and result["errors"] == [],
          f"expected all-empty for a diagnosis with no fixes, got: {result}")
    check("no fixable findings" in result["message"], f"got: {result['message']!r}")


def test_agent_tool_dispatch():
    async def fake_diagnose(listing_id):
        return {"listing_id": listing_id, "diagnosis": {"primary_issue": "x", "fixes": []}}

    with patch.object(server, "_diagnose_listing_core", fake_diagnose):
        out = server._execute_agent_tool("apply_conversion_fixes", {"listing_id": 123})
    check(out.get("listing_id") == 123, f"expected dispatch to reach the real listing_id, got: {out}")

    out2 = server._execute_agent_tool("apply_conversion_fixes", {})
    check("error" in out2, f"missing listing_id must error, got: {out2}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("CONVERSION DIAGNOSIS-TO-AUTOFIX LOOP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("CONVERSION DIAGNOSIS-TO-AUTOFIX LOOP TESTS OK — tool registration, the "
          "3-area fix-handler map, fixable areas applied while photos/price are "
          "correctly surfaced-not-actioned, finding+fix reason text combination, "
          "per-area error isolation (one failure doesn't block the rest), a clean "
          "no-op message for an empty diagnosis, and agent-tool dispatch.")


if __name__ == "__main__":
    run()
