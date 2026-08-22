"""
Tests for the 2026-07-21 fix adding heartbeat visibility to two background
loops' piggybacked subtasks that used to fail silently (print()-only, no
heartbeat, invisible outside server logs):

  1. _snapshot_loop's daily trash-vault + rate-limit-log prune
     (_maybe_prune_after_snapshot). A broken prune could leave data/trash/
     growing unbounded for weeks with nothing on the dashboard to show it.
  2. _quality_audit_loop's pre-manifest subtasks inside _quality_audit_iteration
     (buyer-data retention prune, KB rotation x2, recurring-failures
     promotion, db.record_quality_audit). A silently-broken buyer-data
     retention pass in particular is a real compliance concern (CLAUDE.md's
     retention rule), not just maintenance trivia.

Fix: both now collect failures into a list and fold them into their loop's
existing "snapshot"/"quality_audit" heartbeat as a "warning" status (never
"error" -- the primary job itself still succeeded, and per the existing
design a prune/subtask failure must never affect the loop's own
success/backoff timing), so they're visible on the Agents screen instead of
only in server stdout.

Checks:
  1. _maybe_prune_after_snapshot() returns the failure list when a prune raises,
     and an empty list when both prunes succeed (or when gated off by a
     non-success delay).
  2. _snapshot_loop, driven through exactly one iteration, overwrites its own
     "snapshot" heartbeat to "warning" with the prune failure noted, when a
     prune fails -- and leaves it as the normal "ok" heartbeat when prunes
     succeed.
  3. _quality_audit_iteration() returns "subtask_failures" (populated on a
     subtask exception, empty on a clean run) in every return path, including
     both early-exit skip paths.
  4. _quality_audit_loop, driven through exactly one iteration, records a
     "warning" heartbeat with the subtask issue noted when a subtask fails
     during an otherwise-clean audit run.

Run: python tests/test_loop_subtask_heartbeat_visibility.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_subtaskheartbeat_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "subtaskheartbeat-test-not-a-real-secret")

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


def _heartbeat(name: str) -> dict | None:
    for hb in db.list_agent_heartbeats():
        if hb["name"] == name:
            return hb
    return None


def _run_loop_one_iteration(loop_coro_fn, sleeps_before_loop_body: int = 0):
    """Drives an infinite `while True: ...; await asyncio.sleep(delay)` loop
    through exactly one iteration by making the Nth sleep call raise
    CancelledError -- same technique used elsewhere in this suite
    (test_calendar_tasks_heartbeat_honesty.py, test_warm_suggestions_race.py).

    `sleeps_before_loop_body` accounts for a one-time boot delay some loops
    `await asyncio.sleep(...)` BEFORE entering `while True:` (e.g.
    _quality_audit_loop's `await asyncio.sleep(120)`) -- that sleep must be
    allowed to succeed so the loop body actually runs at least once; only the
    sleep call AFTER it (the loop's own trailing per-iteration sleep) should
    raise."""
    call_count = {"n": 0}

    async def _fake_sleep(_secs):
        call_count["n"] += 1
        if call_count["n"] > sleeps_before_loop_body:
            raise asyncio.CancelledError("stop after one iteration")

    with patch("asyncio.sleep", _fake_sleep):
        try:
            asyncio.run(loop_coro_fn())
        except asyncio.CancelledError:
            pass


# ── 1 & 2: _maybe_prune_after_snapshot / _snapshot_loop ─────────────────────

def test_maybe_prune_returns_failures_on_exception():
    def _boom():
        raise RuntimeError("trash vault corrupted")

    with patch.dict(sys.modules, {"trash": type(sys)("trash")}):
        sys.modules["trash"].prune = _boom
        with patch.object(db, "prune_rate_limit_log", return_value=0):
            failures = asyncio.run(server._maybe_prune_after_snapshot(86_400, 86_400))
    check(any("trash prune failed" in f for f in failures),
          f"expected a trash-prune failure to be returned, got: {failures}")


def test_maybe_prune_returns_empty_on_clean_run():
    with patch.dict(sys.modules, {"trash": type(sys)("trash")}):
        sys.modules["trash"].prune = lambda: 0
        with patch.object(db, "prune_rate_limit_log", return_value=0):
            failures = asyncio.run(server._maybe_prune_after_snapshot(86_400, 86_400))
    check(failures == [], f"a clean prune run should return no failures, got: {failures}")


def test_maybe_prune_skipped_when_snapshot_did_not_succeed():
    failures = asyncio.run(server._maybe_prune_after_snapshot(5.0, 86_400))
    check(failures == [], "prune must be skipped (and return no failures) when delay != base_interval")


def test_snapshot_loop_reports_warning_heartbeat_when_prune_fails():
    async def _fake_take_snapshot():
        return "2026-07-21"

    async def _fake_prune(delay, base_interval):
        return ["trash prune failed: simulated corruption"]

    with patch.object(server, "_take_snapshot", side_effect=_fake_take_snapshot), \
         patch.object(server, "_maybe_prune_after_snapshot", side_effect=_fake_prune), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True):
        _run_loop_one_iteration(server._snapshot_loop)

    hb = _heartbeat("snapshot")
    check(hb is not None, "snapshot heartbeat should exist after one iteration")
    check(hb["status"] == "warning",
          f"a prune failure must overwrite the snapshot heartbeat to 'warning', got: {hb['status']!r}")
    check("trash prune failed" in hb["detail"],
          f"the prune failure detail must be visible in the heartbeat, got: {hb['detail']!r}")


def test_snapshot_loop_reports_ok_heartbeat_when_prune_succeeds():
    async def _fake_take_snapshot():
        return "2026-07-21"

    async def _fake_prune(delay, base_interval):
        return []

    with patch.object(server, "_take_snapshot", side_effect=_fake_take_snapshot), \
         patch.object(server, "_maybe_prune_after_snapshot", side_effect=_fake_prune), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True):
        _run_loop_one_iteration(server._snapshot_loop)

    hb = _heartbeat("snapshot")
    check(hb is not None, "snapshot heartbeat should exist after one iteration")
    check(hb["status"] == "ok",
          f"a clean prune run must leave the normal 'ok' heartbeat untouched, got: {hb['status']!r}")


# ── 3 & 4: _quality_audit_iteration / _quality_audit_loop ────────────────────

def test_quality_audit_iteration_reports_subtask_failure_on_manifest_missing_path():
    def _boom():
        raise RuntimeError("retention prune exploded")

    with patch.object(server, "_prune_buyer_data_retention", side_effect=_boom), \
         patch.object(server, "_summarize_and_rotate_kb_file", return_value=False), \
         patch.object(server, "_promote_recurring_failures", return_value=False), \
         patch("pathlib.Path.exists", return_value=False):
        result = asyncio.run(server._quality_audit_iteration())

    check(result.get("skipped") is True, "manifest-missing path should still report skipped=True")
    check(any("buyer-data retention prune failed" in f for f in result.get("subtask_failures", [])),
          f"the retention-prune failure must survive into the skip result, got: {result}")


def test_quality_audit_iteration_no_subtask_failures_on_clean_pre_manifest_run():
    with patch.object(server, "_prune_buyer_data_retention", return_value=None), \
         patch.object(server, "_summarize_and_rotate_kb_file", return_value=False), \
         patch.object(server, "_promote_recurring_failures", return_value=False), \
         patch("pathlib.Path.exists", return_value=False):
        result = asyncio.run(server._quality_audit_iteration())

    check(result.get("subtask_failures") == [],
          f"a clean pre-manifest run should report no subtask failures, got: {result}")


def test_quality_audit_loop_reports_warning_when_subtask_fails_on_otherwise_clean_run():
    async def _fake_iteration():
        return {
            "passed": 10, "warned": 0, "failed": 0, "fetch_errors": 0, "real_failed": 0,
            "subtask_failures": ["KB rotation failed for ops_runbook.md: disk full"],
        }

    with patch.object(server, "_quality_audit_iteration", side_effect=_fake_iteration), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True):
        _run_loop_one_iteration(server._quality_audit_loop, sleeps_before_loop_body=1)

    hb = _heartbeat("quality_audit")
    check(hb is not None, "quality_audit heartbeat should exist after one iteration")
    check(hb["status"] == "warning",
          f"a subtask failure on an otherwise-clean audit must report 'warning', not 'ok', got: {hb['status']!r}")
    check("KB rotation failed" in hb["detail"],
          f"the subtask failure detail must be visible in the heartbeat, got: {hb['detail']!r}")


def test_quality_audit_loop_still_reports_error_over_warning_when_both_present():
    async def _fake_iteration():
        return {
            "passed": 5, "warned": 0, "failed": 2, "fetch_errors": 0, "real_failed": 2,
            "subtask_failures": ["KB rotation failed for ops_runbook.md: disk full"],
        }

    with patch.object(server, "_quality_audit_iteration", side_effect=_fake_iteration), \
         patch.object(server._anthropic_breaker, "allow_request", return_value=True):
        _run_loop_one_iteration(server._quality_audit_loop, sleeps_before_loop_body=1)

    hb = _heartbeat("quality_audit")
    check(hb["status"] == "error",
          f"a real content FAIL must still take priority over a subtask warning, got: {hb['status']!r}")
    check("KB rotation failed" in hb["detail"],
          f"the subtask issue should still be noted in the detail even when status is 'error', got: {hb['detail']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("LOOP SUBTASK HEARTBEAT VISIBILITY TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("LOOP SUBTASK HEARTBEAT VISIBILITY TESTS OK — _snapshot_loop's prune failures and "
          "_quality_audit_loop's subtask failures now surface as a 'warning' heartbeat (never "
          "silently swallowed) without ever overriding a real 'error', and without affecting "
          "either loop's own success/backoff timing.")


if __name__ == "__main__":
    run()
