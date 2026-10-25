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
  1. GET /api/quality-audit/latest -- returns the real stored FAIL detail
     (not just the aggregate counts already on the alert card), and a clean
     "found: false" when no audit has ever run.
  2. The alert generator attaches `heartbeat_name` so the frontend can tell
     an inspectable heartbeat apart from a non-actionable one.
  3. Frontend source checks: the classifier and the sheet's primary action
     still exist, and nothing on the page calls the removed build-retry route
     or the digital-art builders (both removed 2026-10-25, along with the
     failed-build Retry and the bundle-draft button that used them).

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
    check("'quality_audit'" in src, "the Quality Audit heartbeat must still be classified")
    # the build-retry path went with the digital-art builders (2026-10-25)
    check("/api/loops/retry" not in src, "no button may call the removed /api/loops/retry route")


def test_frontend_has_no_digital_builder_calls():
    # the bundle-draft button opened the digital builders, removed 2026-10-25
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text(encoding="utf-8")
    for gone in ("phoneStartBundleDraft", "/api/produce/build-product", "/api/produce/build-planner",
                 "/api/produce/build-sticker-pack", "/api/produce/coloring-pack", "/api/produce/print-zip",
                 "/api/produce/listing-photos"):
        check(gone not in src, f"the page still references removed {gone}")


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
    print("TODAY FIX BUTTONS TESTS OK — Quality Audit 'View details' surfaces the real stored "
          "FAIL text with an honest fetch-error caveat, the classifier and sheet action are wired, "
          "and no button calls the removed digital-art builders.")


if __name__ == "__main__":
    run()
