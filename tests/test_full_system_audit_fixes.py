"""
Tests for the 2026-08-06 full-system "scan Frank start to finish" audit
fixes, prompted by Scott: "Make sure everything has what it needs to
function. We need to be done with fixes and making things that are in
Frank already, work."

Confirmed findings covered here:
  1. _COMPETITOR_RESEARCH_PATH was a raw ROOT/"data" path -- the monthly
     competitor-research refresh silently vanished on every Railway
     redeploy. Now routed through db.resolve_persistent_path(), matching
     ceo_learnings.md/ops_runbook.md's own fix for the same bug class.
  2. notified_orders.json had the same problem in TWO places (main.py's
     retention-pruner and tools/order_notifier.py's own writer) -- both
     now resolve the same real path via the same volume-detection logic.
  3. The `studio` key in frank_hud_mockup.py's _SCREEN_LOADERS was dead
     code: loadStudioVideos() and its markup were relocated into the
     `create` screen (2026-07 video work), but the standalone `studio`
     loader entry was never removed and had no reachable screen/nav path.
  4. tools/tax_compliance_tools.py was imported (for its _get_tax_calendar()
     helper) but its chat-tool layer was never wired into AGENT_TOOLS -- the
     same "real module, dead chat-tool layer" bug class etsy_ads_tools.py had
     before its own 2026-07-09 fix. Only the 4 tools that never read the
     legacy DataStore's unpopulated shop_data.json analytics/listings fields
     are wired now (log_deductible_expense/get_deductions_summary/
     check_copyright_guidance/get_tax_calendar); the other 4 would silently
     report $0 revenue / zero compliance issues and stay unwired on purpose.
  5. _daily_brief_loop()/_calendar_tasks_loop() each had a small window of
     unprotected per-tick code (a plain DB read / _shop_now() call) outside
     any try/except, unlike every other step in those same functions --
     an exception there would kill the loop's asyncio.Task silently with
     no heartbeat update. Both now wrap the entire tick.

Run: python tests/test_full_system_audit_fixes.py
"""
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_fullaudit_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "fullaudit-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_competitor_research_path_uses_persistent_resolver():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text()
    check('_COMPETITOR_RESEARCH_PATH = db.resolve_persistent_path(' in src,
          "_COMPETITOR_RESEARCH_PATH must be resolved via db.resolve_persistent_path(), not a raw ROOT/'data' path")
    # No /data volume mounted in this test environment -> resolver must fall
    # back to the exact same path the old hardcoded assignment used, so this
    # is a genuine behavior-preserving fix, not a silent path change.
    expected = server.ROOT / "data" / "knowledge_base" / "competitor_research_2026.md"
    check(server._COMPETITOR_RESEARCH_PATH == expected,
          f"expected fallback {expected}, got {server._COMPETITOR_RESEARCH_PATH}")


def test_notified_orders_path_consistent_between_main_and_order_notifier():
    main_src = (ROOT / "tools" / "api_server" / "main.py").read_text()
    check('db.resolve_persistent_path(\n        "notified_orders.json"' in main_src,
          "_prune_buyer_data_retention must resolve notified_orders.json via db.resolve_persistent_path()")

    notifier_src = (ROOT / "tools" / "order_notifier.py").read_text()
    check("def _resolve_state_file()" in notifier_src,
          "order_notifier.py must have its own volume-aware resolver (can't import tools/api_server/db.py directly -- runs as a standalone subprocess)")
    check("STATE_FILE = _resolve_state_file()" in notifier_src,
          "STATE_FILE must come from the resolver, not a raw hardcoded path")

    # Both resolvers, given no /data volume (this test env), must agree on
    # the exact same real file -- otherwise main.py's pruner and
    # order_notifier.py's writer would silently operate on two different
    # files.
    sys.path.insert(0, str(ROOT / "tools"))
    import importlib
    if "order_notifier" in sys.modules:
        del sys.modules["order_notifier"]
    order_notifier = importlib.import_module("order_notifier")
    main_resolved = server.db.resolve_persistent_path(
        "notified_orders.json", fallback=server.ROOT / "data" / "notified_orders.json",
    )
    check(Path(order_notifier.STATE_FILE) == main_resolved,
          f"order_notifier.py's STATE_FILE ({order_notifier.STATE_FILE}) must match main.py's "
          f"resolved path ({main_resolved}) -- both must agree on the one real file")


def test_tax_compliance_safe_tools_wired_unsafe_tools_stay_unwired():
    names = {t["name"] for t in server.AGENT_TOOLS}
    safe = {"log_deductible_expense", "get_deductions_summary", "check_copyright_guidance", "get_tax_calendar"}
    unsafe = {"get_tax_overview", "calculate_quarterly_tax", "get_1099k_status", "check_etsy_compliance"}
    for n in safe:
        check(n in names, f"{n} should now be a real, callable chat tool")
    for n in unsafe:
        check(n not in names,
              f"{n} reads the legacy DataStore's unpopulated analytics/listings fields -- "
              f"must stay unwired until rerouted to a real data source, never silently expose fabricated $0/zero numbers")

    result = server._execute_agent_tool("get_tax_calendar", {})
    check(isinstance(result, dict) and "tax_deadlines" in result, f"got: {result}")

    result2 = server._execute_agent_tool("log_deductible_expense", {
        "amount": 12.5, "category": "materials", "description": "test",
    })
    check(result2.get("success") is True and result2.get("deduction_id"), f"got: {result2}")


def test_studio_screen_loader_orphan_removed():
    src = (ROOT / "tools" / "api_server" / "frank_hud_mockup.py").read_text()
    check("studio: [loadStudioVideos]," not in src,
          "orphaned studio: [loadStudioVideos] _SCREEN_LOADERS entry should be removed -- "
          "there is no id=\"screen-studio\" element or nav path that ever reaches it "
          "(loadStudioVideos itself is still real and used by the 'create' screen's own loader array)")
    # Confirm this isn't a false-positive removal -- loadStudioVideos must
    # still be defined and still wired into the reachable 'create' screen.
    check("function loadStudioVideos(" in src, "loadStudioVideos must still be defined (used by the create screen)")
    check("create: [loadStudioVideos," in src, "the create screen must still load studio videos")


def test_daily_brief_loop_wraps_entire_tick():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text()
    start = src.index("async def _daily_brief_loop(")
    end = src.index("\nasync def ", start + 30)
    body = src[start:end]
    check("enabled = db.get_setting(\"daily_brief_enabled\")" in body, "sanity: found the right function")
    # The whole-tick try must appear BEFORE the enabled-check line and the
    # except must appear AFTER it, i.e. that line is now inside the guard.
    try_idx = body.index("\n        try:\n")
    enabled_idx = body.index('enabled = db.get_setting("daily_brief_enabled")')
    except_idx = body.rindex("except Exception as exc:")
    check(try_idx < enabled_idx < except_idx,
          "the db.get_setting()/_shop_now() preamble must now be inside the whole-tick try/except")


def test_calendar_tasks_loop_wraps_entire_tick():
    src = (ROOT / "tools" / "api_server" / "main.py").read_text()
    start = src.index("async def _calendar_tasks_loop(")
    end = src.index("\n_AGENT_LOOP_LABELS", start)
    body = src[start:end]
    try_idx = body.index("\n        try:\n")
    now_idx = body.index("now = await asyncio.to_thread(_shop_now)")
    except_idx = body.rindex("except Exception as exc:")
    check(try_idx < now_idx < except_idx,
          "the now = await asyncio.to_thread(_shop_now) preamble must now be inside the whole-tick try/except")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("FULL SYSTEM AUDIT FIXES TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("FULL SYSTEM AUDIT FIXES TESTS OK — competitor research + notified_orders both survive a "
          "redeploy now, the orphaned studio screen loader is gone, and both calendar-gated loops "
          "guard their entire tick, not just the sub-tasks that already had try/except.")


if __name__ == "__main__":
    run()
