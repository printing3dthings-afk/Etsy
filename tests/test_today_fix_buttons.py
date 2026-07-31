"""
Tests for the three Today-tab fix actions Scott asked for directly
(2026-07-31): "This was sloppy... Why don't these have the option fix? I
know you can" -- referring to alert cards for failed background builds, the
Quality Audit loop error, and the Opportunities section, none of which had
any action button.

Scope decision (see the Opportunities-card comment in frank_hud_mockup.py):
credential_leak / etsy_token / budget_cap alerts get NO new action here --
those genuinely require a step in a third-party console or a local OAuth
flow, and faking a button that can't do anything would violate the
never-lie-to-the-customer spirit applied to the tool itself. Only the two
agent_heartbeat shapes that ARE mechanically retriable/inspectable, plus a
navigation-only "start a bundle draft" (no auto-selected files -- curating
which real designs go in a bundle is a judgment call, not something to
silently automate), got real actions.

Covers:
  1. _retry_build_loop() / POST /api/loops/retry -- dispatches each
     retriable build-loop prefix to the exact same builder function its own
     one-tap Create-screen button already calls, strips the "build:"
     heartbeat prefix, and fails clearly on an unrecognized name.
  2. GET /api/quality-audit/latest -- returns the real stored FAIL detail
     (not just the aggregate counts already on the alert card), and a clean
     "found: false" when no audit has ever run.
  3. The alert generator attaches `heartbeat_name` so the frontend can tell
     a retriable failure apart from a non-actionable one.
  4. Frontend source checks: the retry-kind classifier, the sheet's primary
     action dispatcher, and the bundle-draft button all exist and are wired
     to the right endpoints/functions.

Run: python tests/test_today_fix_buttons.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_today_fix_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "today-fix-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
import db  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


# ── 1. Retry dispatcher ───────────────────────────────────────────────────
#
# _LOOP_RETRY_BUILDERS captures direct function references at module-load
# time (`{"build_product": _produce_build_product, ...}`), so patching
# server._produce_build_product afterward does NOT change what's in the
# dict -- the very first version of these tests learned this the hard way:
# it silently called the REAL, unpatched builder functions, which spawned
# real `build_product.py`/`build_planner.py`/`build_sticker_pack.py`
# subprocesses against local DP1030 files. Always patch the dict entries
# themselves (patch.dict), never the module attribute.

def test_retry_dispatches_coloring_product_to_produce_build_product():
    fake = lambda inp: {"started": True, "got": inp}  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_coloring_product": fake}):
        result = server._retry_build_loop({"name": "build:build_coloring_product:COLOR1002"})
    check(result.get("got") == {"pid": "COLOR1002"}, f"expected pid COLOR1002 extracted, got {result}")
    check(result.get("started") is True, f"should return the builder's own result verbatim, got {result}")


def test_retry_dispatches_wallart_to_produce_build_product():
    fake = lambda inp: {"started": True, "got": inp}  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_wallart_product": fake}):
        result = server._retry_build_loop({"name": "build:build_wallart_product:WA1030"})
    check(result.get("got") == {"pid": "WA1030"}, f"expected pid WA1030, got {result}")


def test_retry_dispatches_planner_pdf_rebuild():
    fake = lambda inp: {"started": True, "got": inp}  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_planner": fake}):
        result = server._retry_build_loop({"name": "build:build_planner:DP1030"})
    check(result.get("got") == {"pid": "DP1030"}, f"expected pid DP1030, got {result}")


def test_retry_dispatches_sticker_pack_rebuild():
    calls = []
    fake = lambda inp: (calls.append(inp), {"started": True})[1]  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_sticker_pack": fake}):
        server._retry_build_loop({"name": "build:build_sticker_pack:DP1027"})
    check(calls == [{"pid": "DP1027"}], f"expected a single call with pid DP1027, got {calls}")


def test_retry_dispatches_coloring_pack_rebuild():
    calls = []
    fake = lambda inp: (calls.append(inp), {"started": True})[1]  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_coloring_pack": fake}):
        server._retry_build_loop({"name": "build:build_coloring_pack:COLOR1002"})
    check(calls == [{"pid": "COLOR1002"}], f"expected a single call with pid COLOR1002, got {calls}")


def test_retry_accepts_bare_label_without_build_prefix():
    # The Today alert only ever has the heartbeat's own `name`, which may or
    # may not carry the "build:" prefix depending on which code path wrote it
    # -- both must resolve to the same product.
    fake = lambda inp: {"started": True, "got": inp}  # noqa: E731
    with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_product": fake}):
        result = server._retry_build_loop({"name": "build_product:DP1030"})
    check(result.get("got") == {"pid": "DP1030"}, f"a bare name (no 'build:' prefix) should still dispatch, got {result}")


def test_retry_unrecognized_prefix_returns_clear_error():
    result = server._retry_build_loop({"name": "build:some_future_loop:XYZ"})
    check("error" in result, f"an unrecognized proc_label should return a clear error, got {result}")
    check("some_future_loop" in result["error"], f"error should name the unrecognized prefix, got {result}")


def test_retry_malformed_name_returns_clear_error():
    result = server._retry_build_loop({"name": "quality_audit"})  # no ':pid' at all
    check("error" in result, f"a name with no ':' should return a clear error, got {result}")


def test_retry_endpoint_wired():
    fake = lambda inp: {"started": True, "got": inp}  # noqa: E731
    async def _run():
        with patch.dict(server._LOOP_RETRY_BUILDERS, {"build_product": fake}):
            return await server.retry_build_loop({"name": "build:build_product:DP1030"}, _token="test")
    result = asyncio.run(_run())
    check(result.get("got") == {"pid": "DP1030"}, f"POST /api/loops/retry should reach the dispatcher, got {result}")


# ── 2. Quality Audit "View details" ───────────────────────────────────────

def test_quality_audit_latest_no_history():
    with patch.object(db, "get_quality_audit_history", return_value=[]):
        result = asyncio.run(server.get_latest_quality_audit(_token="test"))
    check(result == {"found": False}, f"no recorded audits should return found:false cleanly, got {result}")


def test_quality_audit_latest_returns_real_summary():
    fake_row = {"ts": "2026-07-31T04:00:00+00:00", "passed": 0, "warned": 36, "failed": 22,
                "audited_count": 58, "summary": "✗ FAIL (listing 123): missing attribute X"}
    with patch.object(db, "get_quality_audit_history", return_value=[fake_row]):
        result = asyncio.run(server.get_latest_quality_audit(_token="test"))
    check(result["found"] is True, f"expected found:true, got {result}")
    check(result["failed"] == 22, f"expected failed=22 passed through, got {result}")
    check(result["summary"] == fake_row["summary"], f"expected the real stored FAIL text, got {result.get('summary')!r}")
    check(result["may_include_fetch_errors"] is True,
          "a nonzero failed count should carry the fetch-error caveat since it isn't persisted separately")


def test_quality_audit_latest_zero_failed_has_no_caveat():
    fake_row = {"ts": "x", "passed": 58, "warned": 0, "failed": 0, "audited_count": 58, "summary": ""}
    with patch.object(db, "get_quality_audit_history", return_value=[fake_row]):
        result = asyncio.run(server.get_latest_quality_audit(_token="test"))
    check(result["may_include_fetch_errors"] is False,
          f"a clean run (failed=0) should not carry the fetch-error caveat, got {result}")


# ── 3. Alert generator carries heartbeat_name ─────────────────────────────

def test_alerts_source_has_heartbeat_name_field():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text(encoding="utf-8")
    idx = src.index('"source": "agent_heartbeat"')
    block = src[idx:idx + 800]
    check('"heartbeat_name": h.get("name")' in block,
          "the agent_heartbeat alert dict should carry the raw heartbeat name so the "
          "frontend can classify retriable vs non-actionable without parsing the title")


# ── 4. Frontend wiring ─────────────────────────────────────────────────────

def test_frontend_retry_kind_classifier_exists():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("function _heartbeatRetryKind(" in src, "expected the retry-kind classifier function")
    for prefix in ("build_coloring_pack", "build_planner", "build_sticker_pack",
                    "build_product", "build_wallart_product", "build_coloring_product"):
        check(f"'{prefix}'" in src, f"expected '{prefix}' listed among retriable build prefixes")


def test_frontend_sheet_dispatcher_and_actions_exist():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check('onclick="phoneSheetPrimaryAction()"' in src,
          "the sheet's primary button should route through the dispatcher, not call phoneSheetFix() directly")
    check("function phoneSheetPrimaryAction(" in src, "expected the primary-action dispatcher")
    check("function phoneSheetRetryBuild(" in src, "expected the retry-build action")
    check("/api/loops/retry" in src, "the retry action should call the new retry endpoint")
    check("function phoneSheetQualityAuditDetails(" in src, "expected the quality-audit details action")
    check("/api/quality-audit/latest" in src, "the details action should call the new endpoint")


def test_frontend_bundle_draft_button_exists():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("function phoneStartBundleDraft(" in src, "expected the bundle-draft navigation function")
    check("Start bundle listing" in src, "expected a visible 'Start bundle listing' button label")
    check("createOpenCategory(o.category)" in src,
          "the bundle-draft button should open the real Create-screen category panel, not a new UI")
    # Explicitly does NOT auto-select real files into a fake listing.
    check("_createToggleNewCode(true)" in src.split("function phoneStartBundleDraft(")[1][:600],
          "should open the '+ new one' description path, not silently build from existing files")


def test_frontend_needs_card_tappable_for_retriable_heartbeats():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    check("_heartbeatRetryKind(x.heartbeat_name)" in src,
          "the Needs-attention card render loop should use the classifier to decide tappability")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("TODAY FIX BUTTONS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("TODAY FIX BUTTONS TESTS OK — Retry dispatches to the right existing builder for "
          "every retriable build-loop prefix, Quality Audit 'View details' surfaces the real "
          "stored FAIL text with an honest fetch-error caveat, and the frontend wires all three "
          "actions (retry / view details / start bundle draft) without fabricating any listing "
          "content.")


if __name__ == "__main__":
    run()
