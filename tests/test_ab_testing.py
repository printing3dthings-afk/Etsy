"""
Tests for Title A/B Testing (2026-08-06, idea 3/3 of the "significantly
improve Frank" roadmap). Scope note: title only, not photo -- Etsy has no
per-photo split-test mechanism to read real results from, so a fabricated
"photo B won" verdict would violate the top-priority never-lie rule. See
main.py's module comment above _AB_TESTS_PATH for the full reasoning.

Two hard rules every test here is really checking:
  1. Nothing irreversible auto-executes -- Variant B only ever goes live
     through the normal staged-action approval queue (db.enqueue_action),
     never a direct Etsy API call from this code.
  2. Rotation windows can never be shorter than
     db._RANKING_RECOVERY_COOLDOWN_DAYS (21 days) -- a faster flip would
     compound title edits inside Etsy's own ranking-recovery period and
     hurt the listing instead of helping it (CLAUDE.md's Ranking Recovery
     Playbook).

Checks:
  1. _load_ab_tests()/_save_ab_tests() round-trip and tolerate a missing file.
  2. _start_ab_test(): happy path pulls the REAL current title from Etsy as
     Variant A (never trusts a caller-supplied value); rejects an empty or
     >140-char Variant B title; rejects rotation_days below the 21-day floor;
     rejects a non-active listing; rejects a second concurrent test on the
     same listing.
  3. _ab_test_iteration(): advances a running_a test whose window has closed
     into awaiting_approval_b (staging a real update_title action via
     db.enqueue_action, never applying it directly); advances a running_b
     test whose window has closed into completed with a computed result;
     leaves a test whose window hasn't closed untouched.
  4. _advance_ab_test(): moves awaiting_approval_b -> running_b only, is a
     no-op for any other status (so a duplicate/late call can't corrupt
     state).
  5. _cancel_ab_test_for_rejected_action(): moves awaiting_approval_b ->
     cancelled with the rejection reason attached; no-op otherwise.
  6. _compute_ab_test_comparison(): picks the higher-conversion variant when
     both windows have real views+orders data, and reports 'inconclusive'
     (never a guessed winner) when data is missing.
  7. POST /api/queue/{id}/approve calls _advance_ab_test exactly when the
     executed action's payload carries an ab_test_id; POST .../reject calls
     _cancel_ab_test_for_rejected_action the same way.
  8. start_ab_test/get_ab_tests are registered in AGENT_TOOLS and dispatch
     correctly through _execute_agent_tool.

Run: python tests/test_ab_testing.py
"""
import asyncio
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch, MagicMock

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_abtest_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "abtest-test-not-a-real-secret")

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


def _fresh_path(prefix: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix=prefix, suffix=".json", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink()
    return path


def _swap_ab_path():
    """Context-manager-free swap helper -- callers restore in `finally`."""
    orig = server._AB_TESTS_PATH
    path = _fresh_path("ab_tests_")
    server._AB_TESTS_PATH = path
    return orig, path


def test_load_missing_file_returns_empty_dict():
    orig, path = _swap_ab_path()
    try:
        check(server._load_ab_tests() == {}, "missing file should yield an empty dict, not raise")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_save_and_reload_round_trips():
    orig, path = _swap_ab_path()
    try:
        server._save_ab_tests({"1": {"id": "1", "listing_id": 999, "status": "running_a"}})
        reloaded = server._load_ab_tests()
        check(reloaded["1"]["listing_id"] == 999, f"round-trip should preserve data, got: {reloaded}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_pulls_real_title_from_etsy():
    orig, path = _swap_ab_path()
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.return_value = {
                "title": "Real Live Title From Etsy", "state": "active",
            }
            result = asyncio.run(server._start_ab_test(12345, "Proposed New Title"))
        check(result.get("ok") is True, f"expected success, got: {result}")
        test = result["test"]
        check(test["variant_a_title"] == "Real Live Title From Etsy",
              f"Variant A must be the REAL fetched title, not anything caller-supplied, got: {test}")
        check(test["variant_b_title"] == "Proposed New Title", f"got: {test}")
        check(test["status"] == "running_a", f"a fresh test should start tracking Variant A immediately, got: {test}")
        check(test["rotation_days"] == db._RANKING_RECOVERY_COOLDOWN_DAYS,
              f"default rotation should match the ranking-recovery floor, got: {test}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_rejects_empty_variant_b():
    orig, path = _swap_ab_path()
    try:
        result = asyncio.run(server._start_ab_test(1, "   "))
        check("error" in result, f"empty variant_b_title should be rejected, got: {result}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_rejects_title_over_140_chars():
    orig, path = _swap_ab_path()
    try:
        result = asyncio.run(server._start_ab_test(1, "x" * 141))
        check("error" in result and "140" in result["error"], f"expected a 140-char rejection, got: {result}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_rejects_rotation_below_ranking_recovery_floor():
    orig, path = _swap_ab_path()
    try:
        result = asyncio.run(server._start_ab_test(1, "New Title", rotation_days=7))
        check("error" in result, f"a 7-day rotation would compound edits inside Etsy's recovery window, must be rejected: {result}")
        check(str(db._RANKING_RECOVERY_COOLDOWN_DAYS) in result["error"], f"error should cite the real floor, got: {result}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_rejects_inactive_listing():
    orig, path = _swap_ab_path()
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.return_value = {"title": "Draft Thing", "state": "draft"}
            result = asyncio.run(server._start_ab_test(1, "New Title"))
        check("error" in result, f"a non-active listing can't be A/B tested, got: {result}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_start_ab_test_rejects_second_concurrent_test_same_listing():
    orig, path = _swap_ab_path()
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.return_value = {"title": "Original Title", "state": "active"}
            first = asyncio.run(server._start_ab_test(555, "First Variant B"))
            check(first.get("ok") is True, f"first test should succeed, got: {first}")
            second = asyncio.run(server._start_ab_test(555, "Second Variant B"))
        check("error" in second, f"a second concurrent test on the same listing must be rejected, got: {second}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def _make_test(status, phase_started_days_ago, **overrides):
    t = {
        "id": "1", "listing_id": 777,
        "variant_a_title": "Original Title", "variant_b_title": "New Title",
        "rotation_days": db._RANKING_RECOVERY_COOLDOWN_DAYS, "status": status,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "phase_started_at": (datetime.now(timezone.utc) - timedelta(days=phase_started_days_ago)).isoformat(),
        "variant_a_start_date": "2026-07-01", "variant_a_end_date": None,
        "variant_b_start_date": None, "variant_b_end_date": None,
        "pending_action_id": None, "result": None,
    }
    t.update(overrides)
    return t


def test_iteration_advances_running_a_past_window_by_staging_action():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("running_a", db._RANKING_RECOVERY_COOLDOWN_DAYS + 1)
        server._save_ab_tests({"1": t})
        with patch.object(db, "enqueue_action", return_value=999) as mock_enqueue:
            result = asyncio.run(server._ab_test_iteration())
        check(result["advanced"] == 1, f"expected 1 test advanced, got: {result}")
        check(mock_enqueue.call_count == 1, f"should stage exactly one action, got {mock_enqueue.call_count}")
        call_args = mock_enqueue.call_args
        check(call_args.args[0] == "update_title", f"must stage an update_title action, got: {call_args}")
        payload = call_args.args[2]
        check(payload["ab_test_id"] == "1", f"payload must carry the ab_test_id for the approval hook, got: {payload}")
        check(payload["title"] == "New Title", f"should stage Variant B's title, got: {payload}")
        updated = server._load_ab_tests()["1"]
        check(updated["status"] == "awaiting_approval_b", f"got: {updated}")
        check(updated["pending_action_id"] == 999, f"got: {updated}")
        check(updated["variant_a_end_date"] is not None, f"Variant A's window should be closed out, got: {updated}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_iteration_never_applies_title_change_directly():
    """The single most important behavior in this whole feature: the staged
    action is created via db.enqueue_action, never via a direct Etsy write."""
    orig, path = _swap_ab_path()
    try:
        t = _make_test("running_a", db._RANKING_RECOVERY_COOLDOWN_DAYS + 1)
        server._save_ab_tests({"1": t})
        with patch.object(server, "EtsyAPIClient") as mock_client_cls, \
             patch.object(db, "enqueue_action", return_value=1):
            asyncio.run(server._ab_test_iteration())
        check(mock_client_cls.return_value.update_listing.call_count == 0,
              "must never call EtsyAPIClient directly to change the title")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_iteration_leaves_test_untouched_before_window_closes():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("running_a", 3)  # far short of the 21-day floor
        server._save_ab_tests({"1": t})
        with patch.object(db, "enqueue_action") as mock_enqueue:
            result = asyncio.run(server._ab_test_iteration())
        check(result["advanced"] == 0, f"window hasn't closed yet, nothing should advance: {result}")
        check(mock_enqueue.call_count == 0, "must not stage anything before the window closes")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_iteration_completes_running_b_past_window():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("running_b", db._RANKING_RECOVERY_COOLDOWN_DAYS + 1,
                        variant_b_start_date="2026-07-22")
        server._save_ab_tests({"1": t})
        fake_result = {"verdict": "variant_b", "verdict_basis": "test"}
        with patch.object(server, "_compute_ab_test_comparison", return_value=fake_result):
            result = asyncio.run(server._ab_test_iteration())
        check(result["advanced"] == 1, f"got: {result}")
        updated = server._load_ab_tests()["1"]
        check(updated["status"] == "completed", f"got: {updated}")
        check(updated["result"] == fake_result, f"got: {updated}")
        check(updated["variant_b_end_date"] is not None, f"got: {updated}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_advance_ab_test_moves_awaiting_to_running_b():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("awaiting_approval_b", 0, pending_action_id=42)
        server._save_ab_tests({"1": t})
        server._advance_ab_test("1", "New Title")
        updated = server._load_ab_tests()["1"]
        check(updated["status"] == "running_b", f"got: {updated}")
        check(updated["variant_b_start_date"] is not None, f"got: {updated}")
        check(updated["pending_action_id"] is None, f"got: {updated}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_advance_ab_test_is_noop_for_wrong_status():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("running_a", 0)
        server._save_ab_tests({"1": t})
        server._advance_ab_test("1", "New Title")
        updated = server._load_ab_tests()["1"]
        check(updated["status"] == "running_a", f"must not advance a test that isn't awaiting approval, got: {updated}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_cancel_for_rejected_action_marks_cancelled_with_reason():
    orig, path = _swap_ab_path()
    try:
        t = _make_test("awaiting_approval_b", 0, pending_action_id=42)
        server._save_ab_tests({"1": t})
        server._cancel_ab_test_for_rejected_action("1", "not sure about this title")
        updated = server._load_ab_tests()["1"]
        check(updated["status"] == "cancelled", f"got: {updated}")
        check(updated["result"]["cancelled_reason"] == "not sure about this title", f"got: {updated}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def test_compute_comparison_picks_higher_conversion_variant():
    a_rows = [{"views": 100, "num_favorers": 5}, {"views": 300, "num_favorers": 8}]  # +200 views
    b_rows = [{"views": 100, "num_favorers": 5}, {"views": 200, "num_favorers": 8}]  # +100 views
    t = _make_test("running_b", 0, variant_a_end_date="2026-07-22", variant_b_start_date="2026-07-22", variant_b_end_date="2026-08-12")

    def fake_snapshot_history(listing_id, start, end):
        return a_rows if start == "2026-07-01" else b_rows

    _a_start_ts = int(datetime(2026, 7, 1, tzinfo=timezone.utc).timestamp())
    _b_start_ts = int(datetime(2026, 7, 22, tzinfo=timezone.utc).timestamp())

    def fake_get_orders(self, limit=100, status="paid", min_created=None, max_created=None):
        # Variant A: 4 orders over 200 views gained = 2% conversion.
        # Variant B: 6 orders over 100 views gained = 6% conversion -- B should win.
        is_b_window = min_created is not None and abs(min_created - _b_start_ts) < abs(min_created - _a_start_ts)
        n = 6 if is_b_window else 4
        return {"results": [
            {"transactions": [{"listing_id": 777, "quantity": 1, "price": {"amount": 1499, "divisor": 100}}]}
            for _ in range(n)
        ]}

    with patch.object(db, "get_listing_snapshot_history", side_effect=fake_snapshot_history), \
         patch.object(server.EtsyAPIClient, "get_orders", fake_get_orders):
        result = server._compute_ab_test_comparison(t)
    check(result["verdict"] == "variant_b", f"B has higher conversion, should win, got: {result}")
    check(result["variant_a"]["orders"] == 4, f"got: {result}")
    check(result["variant_b"]["orders"] == 6, f"got: {result}")


def test_compute_comparison_inconclusive_without_enough_data():
    t = _make_test("running_b", 0, variant_a_end_date=None, variant_b_start_date="2026-07-22", variant_b_end_date=None)
    result = server._compute_ab_test_comparison(t)
    check(result["verdict"] == "inconclusive", f"open windows must never produce a guessed winner, got: {result}")
    check(result["variant_a"]["views_gained"] is None, f"got: {result}")


def test_approve_action_calls_advance_ab_test_when_payload_tagged():
    action_id = db.enqueue_action("update_title", "test A/B swap", {"listing_id": 777, "title": "New Title", "ab_test_id": "1"})
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"ok": True}), \
         patch.object(server, "_verify_etsy_mutation", return_value=None), \
         patch.object(server, "_advance_ab_test") as mock_advance:
        asyncio.run(server.approve_action(action_id, _token="test"))
    check(mock_advance.call_count == 1, f"approve should call _advance_ab_test when payload carries ab_test_id, got {mock_advance.call_count} calls")
    check(mock_advance.call_args.args[0] == "1", f"got: {mock_advance.call_args}")


def test_approve_action_skips_advance_ab_test_for_ordinary_title_change():
    action_id = db.enqueue_action("update_title", "ordinary title fix", {"listing_id": 888, "title": "Just A Fix"})
    with patch.object(server, "_validate_staged_action", return_value=(True, "")), \
         patch.object(server, "_execute_staged_action", return_value={"ok": True}), \
         patch.object(server, "_verify_etsy_mutation", return_value=None), \
         patch.object(server, "_advance_ab_test") as mock_advance:
        asyncio.run(server.approve_action(action_id, _token="test"))
    check(mock_advance.call_count == 0, "an ordinary (non-A/B) update_title approval must not touch A/B test state")


def test_reject_action_calls_cancel_for_ab_test_payload():
    action_id = db.enqueue_action("update_title", "test A/B swap", {"listing_id": 777, "title": "New Title", "ab_test_id": "2"})
    with patch.object(server, "_cancel_ab_test_for_rejected_action") as mock_cancel:
        asyncio.run(server.reject_action(action_id, body={"reason": ""}, _token="test"))
    check(mock_cancel.call_count == 1, f"reject should call _cancel_ab_test_for_rejected_action when payload carries ab_test_id, got {mock_cancel.call_count} calls")
    check(mock_cancel.call_args.args[0] == "2", f"got: {mock_cancel.call_args}")


def test_tools_registered_and_dispatch():
    names = {t["name"] for t in server.AGENT_TOOLS}
    check("start_ab_test" in names, "start_ab_test must be registered in AGENT_TOOLS")
    check("get_ab_tests" in names, "get_ab_tests must be registered in AGENT_TOOLS")
    orig, path = _swap_ab_path()
    try:
        with patch.object(server, "EtsyAPIClient") as mock_client_cls:
            mock_client_cls.return_value.get_listing.return_value = {"title": "Real Title", "state": "active"}
            result = server._execute_agent_tool("start_ab_test", {"listing_id": 1, "variant_b_title": "New One"})
        check(result.get("ok") is True, f"got: {result}")
        result2 = server._execute_agent_tool("get_ab_tests", {})
        check(len(result2.get("tests", [])) == 1, f"got: {result2}")
    finally:
        server._AB_TESTS_PATH = orig
        path.unlink(missing_ok=True)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("A/B TESTING TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("A/B TESTING TESTS OK — title A/B testing never auto-applies a title change, "
          "always floors rotation at the ranking-recovery window, and never fabricates a winner.")


if __name__ == "__main__":
    run()
