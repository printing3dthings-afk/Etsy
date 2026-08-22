"""
Test for the 2026-07-21 fix to _run_loop_iteration()'s error-path heartbeat
write.

_run_loop_iteration() is the shared retry/backoff/heartbeat helper used by
all 5 real background loops (_snapshot_loop, _warm_suggestions,
_token_sync_loop, _quality_audit_loop, _health_check_loop) -- each one calls
it as `delay = await _run_loop_iteration(...)` with NOTHING wrapping that
call. Previously, when `fn()` raised, the except branch's own
`db.set_agent_heartbeat(name, label, "error", ...)` call was itself
unguarded: if THAT write also raised (DB disk full, locked file, corrupted
db -- exactly the kind of condition likely to coincide with a real ops
incident), the exception propagated out of _run_loop_iteration uncaught,
which would kill the calling loop's asyncio task permanently -- silently,
with no heartbeat, no restart, until the whole process was restarted.

Fix: the error-path heartbeat write is now wrapped in its own try/except
that logs and swallows any failure, so a broken heartbeat write degrades to
"this iteration's status board update didn't happen" rather than "this loop
never runs again."

Checks:
  1. When fn() raises AND the heartbeat write also raises,
     _run_loop_iteration() still returns a valid backoff delay instead of
     propagating the heartbeat-write exception.
  2. The original fn() failure is still tracked (failure count increments,
     used for backoff sizing) even when the heartbeat write fails.
  3. Baseline (unchanged) behavior: when fn() raises and the heartbeat write
     succeeds normally, the heartbeat is recorded "error" as before.

Run: python tests/test_run_loop_iteration_heartbeat_resilience.py
"""
import asyncio
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_loopheartbeat_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "loopheartbeat-test-not-a-real-secret")

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


def test_returns_delay_instead_of_raising_when_heartbeat_write_also_fails():
    async def _failing_fn():
        raise RuntimeError("the actual job failed")

    server._LOOP_FAILURE_COUNTS.pop("test_loop_cascade", None)
    with patch.object(db, "set_agent_heartbeat", side_effect=RuntimeError("db is locked")):
        try:
            delay = asyncio.run(server._run_loop_iteration(
                "test_loop_cascade", "Test Loop Cascade", _failing_fn,
                base_interval=3600,
            ))
        except Exception as exc:  # noqa: BLE001
            check(False, f"_run_loop_iteration must not propagate the heartbeat-write failure, raised: {exc!r}")
            return

    check(isinstance(delay, (int, float)) and delay >= 0,
          f"expected a valid backoff delay to be returned even when the heartbeat write failed, got: {delay!r}")


def test_failure_count_still_tracked_when_heartbeat_write_fails():
    async def _failing_fn():
        raise RuntimeError("boom")

    server._LOOP_FAILURE_COUNTS.pop("test_loop_cascade2", None)
    with patch.object(db, "set_agent_heartbeat", side_effect=RuntimeError("db is locked")):
        asyncio.run(server._run_loop_iteration(
            "test_loop_cascade2", "Test Loop Cascade 2", _failing_fn, base_interval=3600,
        ))
    check(server._LOOP_FAILURE_COUNTS.get("test_loop_cascade2") == 1,
          f"the failure counter must still increment even when the heartbeat write itself fails, "
          f"got: {server._LOOP_FAILURE_COUNTS.get('test_loop_cascade2')!r}")


def test_baseline_error_heartbeat_still_recorded_when_write_succeeds():
    async def _failing_fn():
        raise RuntimeError("normal failure, heartbeat write itself is fine")

    server._LOOP_FAILURE_COUNTS.pop("test_loop_baseline", None)
    asyncio.run(server._run_loop_iteration(
        "test_loop_baseline", "Test Loop Baseline", _failing_fn, base_interval=3600,
    ))
    hb = _heartbeat("test_loop_baseline")
    check(hb is not None, "heartbeat should be recorded when the write itself succeeds")
    check(hb["status"] == "error", f"expected 'error' status, got: {hb['status'] if hb else None!r}")
    check("normal failure" in hb["detail"], f"expected the original error in the detail, got: {hb['detail']!r}")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("RUN LOOP ITERATION HEARTBEAT RESILIENCE TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("RUN LOOP ITERATION HEARTBEAT RESILIENCE TESTS OK — a heartbeat write failure on the "
          "error path no longer propagates out of _run_loop_iteration() and kill the calling "
          "loop's task; the failure counter still tracks correctly, and the normal (write-succeeds) "
          "error-heartbeat path is unchanged.")


if __name__ == "__main__":
    run()
