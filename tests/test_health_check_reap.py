"""
Tests for _health_check_iteration()'s crash/hang surfacing (Frank upgrade Wave 1,
reliability item 3, 2026-07-17). Before this, a crashed or genuinely hung tracked
background build (build_planner/build_sticker_pack/build_product) was silently
swallowed -- reaped with only a server-stdout print(), no ops_runbook entry, no
/api/alerts surfacing, and no timeout for a process that never exits at all.

Spawns real subprocesses (a quick failure, a quick success, and a "hung" one --
still running, but with its started_at backdated past the timeout ceiling so the
test doesn't actually wait 15 minutes) and confirms each path produces the right
agent_heartbeat row, which /api/alerts already knows how to surface (the same
mechanism the 5 real background loops use).

Self-contained, same pattern as tests/test_produce_qc.py. Run:
    python tests/test_health_check_reap.py
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_healthreap_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "healthreap-test-not-a-real-secret")

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


async def _run_all_checks() -> None:
    # 1) A process that exits non-zero (simulated crash).
    crash_proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(1)"])
    crash_proc.wait()
    server._LONG_RUNNING_PROCS[crash_proc.pid] = (
        crash_proc, "build_planner:TESTCRASH", datetime.now(timezone.utc) - timedelta(seconds=5)
    )

    # 2) A process that exits cleanly.
    ok_proc = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
    ok_proc.wait()
    server._LONG_RUNNING_PROCS[ok_proc.pid] = (
        ok_proc, "build_planner:TESTOK", datetime.now(timezone.utc) - timedelta(seconds=5)
    )

    # 3) A still-running process whose started_at is backdated past the timeout
    #    ceiling, simulating a genuinely hung build without an actual 15-min wait.
    hung_proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(120)"])
    server._LONG_RUNNING_PROCS[hung_proc.pid] = (
        hung_proc, "build_sticker_pack:TESTHUNG",
        datetime.now(timezone.utc) - timedelta(seconds=server._LONG_RUNNING_PROC_TIMEOUT_S + 30),
    )

    await server._health_check_iteration()

    check(crash_proc.pid not in server._LONG_RUNNING_PROCS, "crashed proc should be untracked after reap")
    check(ok_proc.pid not in server._LONG_RUNNING_PROCS, "ok proc should be untracked after reap")
    check(hung_proc.pid not in server._LONG_RUNNING_PROCS, "hung proc should be untracked after kill")
    check(hung_proc.poll() is not None, "hung proc should actually be killed (poll() != None)")

    heartbeats = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}

    crash_hb = heartbeats.get("build:build_planner:TESTCRASH")
    check(crash_hb is not None and crash_hb["status"] == "error", "crash heartbeat should be status=error")

    ok_hb = heartbeats.get("build:build_planner:TESTOK")
    check(ok_hb is not None and ok_hb["status"] == "ok", "clean-exit heartbeat should be status=ok")

    hung_hb = heartbeats.get("build:build_sticker_pack:TESTHUNG")
    check(hung_hb is not None and hung_hb["status"] == "error", "hung heartbeat should be status=error")
    check("Killed" in (hung_hb.get("detail") or ""), "hung heartbeat detail should mention it was killed")

    # 4) A later CLEAN run of the same build should self-clear the prior error
    #    heartbeat (a retry that succeeds shouldn't leave a stale alert behind).
    retry_ok = subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(0)"])
    retry_ok.wait()
    server._LONG_RUNNING_PROCS[retry_ok.pid] = (
        retry_ok, "build_planner:TESTCRASH", datetime.now(timezone.utc) - timedelta(seconds=5)
    )
    await server._health_check_iteration()
    heartbeats2 = {h["name"]: h for h in await asyncio.to_thread(db.list_agent_heartbeats)}
    retry_hb = heartbeats2.get("build:build_planner:TESTCRASH")
    check(retry_hb is not None and retry_hb["status"] == "ok",
          "a later clean run of the same build should overwrite the error heartbeat with ok")

    # 5) The crash/hung heartbeats surface through the exact same query
    #    GET /api/alerts uses (list_agent_heartbeats + filter status == "error").
    alert_worthy = [h for h in heartbeats.values() if h.get("status") == "error"]
    check(len(alert_worthy) >= 2,  # crash + hung (before the retry-clears-it step)
          f"expected at least 2 error heartbeats to be alert-worthy, got {len(alert_worthy)}")


def run() -> None:
    try:
        asyncio.run(_run_all_checks())
    except Exception:  # noqa: BLE001
        _failures.append(f"unhandled exception:\n{traceback.format_exc()}")
    if _failures:
        print("HEALTH-CHECK REAP TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HEALTH-CHECK REAP TESTS OK — crash/hang/timeout surfacing and "
          "retry-self-clear all verified against real subprocesses.")


if __name__ == "__main__":
    run()
