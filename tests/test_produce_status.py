"""
Tests for GET /api/produce/status (2026-07-22 Create-screen redesign) — the
endpoint that closes the biggest usability gap the old Create screen had:
tapping a build button used to give a static ack plus a dead "Check Files"
link with no way to tell whether a build was still running, had crashed, or
had actually finished. This polls _LONG_RUNNING_PROCS (the same registry the
hourly health-check loop already reaps from) and tails the build's log file.

Self-contained TestClient-against-the-real-app pattern, same as
tests/test_produce_qc.py. Run: python tests/test_produce_status.py
"""
import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_producestatus_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "produce-status-test-not-a-real-secret")
os.environ["ENABLE_TEST_LOGIN"] = "true"
os.environ["TEST_LOGIN_USERNAME"] = "producestatustest"
os.environ["TEST_LOGIN_PASSWORD"] = "ProduceStatusTest!2026Only"

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _logged_in_client() -> TestClient:
    c = TestClient(server.app, base_url="https://testserver")
    r = c.post("/login", data={
        "username": os.environ["TEST_LOGIN_USERNAME"],
        "password": os.environ["TEST_LOGIN_PASSWORD"],
        "next": "/frank",
    }, follow_redirects=False)
    check(r.status_code in (302, 303), f"login should redirect, got {r.status_code}")
    return c


def test_unknown_pid_reports_known_false():
    c = _logged_in_client()
    # A PID astronomically unlikely to be a real OS process AND not present in
    # the registry -- exercises the "already reaped" honest-report path.
    r = c.get("/api/produce/status", params={"os_pid": 999999})
    check(r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}")
    data = r.json()
    check(data.get("known") is False, f"an untracked pid must report known=false, got {data}")
    check(data.get("os_pid") == 999999, f"os_pid must be echoed back, got {data}")


def test_running_process_reports_running_true():
    # A real, still-alive subprocess registered directly into _LONG_RUNNING_PROCS,
    # bypassing the actual build pipeline (which needs product files) -- this
    # test only exercises the status-polling contract, not a real build.
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        server._LONG_RUNNING_PROCS[proc.pid] = (proc, "test_fixture_proc", datetime.now(timezone.utc))
        c = _logged_in_client()
        r = c.get("/api/produce/status", params={"os_pid": proc.pid})
        check(r.status_code == 200, f"expected 200, got {r.status_code}")
        data = r.json()
        check(data.get("known") is True, f"a registered running proc must report known=true, got {data}")
        check(data.get("running") is True, f"a still-alive proc must report running=true, got {data}")
        check(data.get("exit_code") is None, f"a running proc has no exit code yet, got {data}")
        check(isinstance(data.get("elapsed_s"), (int, float)) and data["elapsed_s"] >= 0,
              f"elapsed_s must be a non-negative number, got {data.get('elapsed_s')}")
        check(data.get("label") == "test_fixture_proc", f"label should be echoed, got {data}")
    finally:
        proc.terminate()
        proc.wait(timeout=5)
        server._LONG_RUNNING_PROCS.pop(proc.pid, None)


def test_finished_process_reports_exit_code():
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait(timeout=5)
    try:
        server._LONG_RUNNING_PROCS[proc.pid] = (proc, "test_fixture_finished", datetime.now(timezone.utc))
        c = _logged_in_client()
        r = c.get("/api/produce/status", params={"os_pid": proc.pid})
        check(r.status_code == 200, f"expected 200, got {r.status_code}")
        data = r.json()
        check(data.get("running") is False, f"a finished proc must report running=false, got {data}")
        check(data.get("exit_code") == 0, f"a clean exit must report exit_code 0, got {data}")
    finally:
        server._LONG_RUNNING_PROCS.pop(proc.pid, None)


def test_log_tail_reads_last_lines_from_product_log_dir():
    logdir = server._product_log_dir()
    name = "test_produce_status_fixture.log"
    log_path = logdir / name
    lines = [f"line {i}" for i in range(1, 61)]  # 60 lines total
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    try:
        c = _logged_in_client()
        r = c.get("/api/produce/status", params={"os_pid": 999999, "log_file": name})
        check(r.status_code == 200, f"expected 200, got {r.status_code}")
        data = r.json()
        tail = data.get("log_tail") or ""
        check("line 60" in tail, f"log tail must include the most recent line, got: {tail[-200:]}")
        # last 40 of 60 lines = lines 21-60, so line 20 (and earlier) must be dropped
        check("line 20" not in tail, f"log tail must be truncated to the last ~40 lines, got: {tail[:200]}")
    finally:
        log_path.unlink(missing_ok=True)


def test_missing_log_file_reports_none_not_error():
    c = _logged_in_client()
    r = c.get("/api/produce/status", params={"os_pid": 999999, "log_file": "does_not_exist_12345.log"})
    check(r.status_code == 200, f"a missing log file must not break the endpoint, got {r.status_code}")
    check(r.json().get("log_tail") is None, f"missing log file should report log_tail=None, got {r.json()}")


def test_log_file_path_is_sandboxed_to_basename():
    # A path-traversal attempt in log_file must not escape _product_log_dir() --
    # os.path.basename() strips any directory components before the read.
    c = _logged_in_client()
    r = c.get("/api/produce/status", params={"os_pid": 999999, "log_file": "../../etc/passwd"})
    check(r.status_code == 200, f"expected 200 (graceful non-error), got {r.status_code}")
    check(r.json().get("log_tail") is None,
          f"a traversal attempt must not read an arbitrary file, got {r.json()}")


def test_requires_auth():
    c = TestClient(server.app, base_url="https://testserver")
    r = c.get("/api/produce/status", params={"os_pid": 12345})
    check(r.status_code in (401, 403), f"unauthenticated request must be rejected, got {r.status_code}")


def _fake_popen(*_args, **_kwargs):
    proc = MagicMock()
    proc.pid = 800000 + id(proc) % 1000  # distinct-enough fake OS pid per call
    proc.poll.return_value = None
    return proc


# ── Category-misroute fix (2026-07-22) ────────────────────────────────────
# Scott reported live: opening the Coloring Pages panel, typing a new code
# ("COLOR01"), and tapping "Build these coloring pages" returned "COLOR01
# isn't a configured planner (have DP1026...)" -- a Digital Planner error on
# a Coloring Pages build. Root cause: buildProductRun() never sent `category`
# in its POST body, so _resolve_build_category() fell back to guessing from
# product_catalog.json, defaulting to "digital_planner" for any uncataloged
# pid. Fixed by having the frontend send category explicitly, and by adding
# pre-flight checks to the wall_art/coloring_pages branches (mirroring
# digital_planner's existing pattern) so a genuinely new/uncataloged pid
# fails fast with the REAL reason instead of being misrouted or spawning a
# doomed subprocess.


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("PRODUCE-STATUS TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("PRODUCE-STATUS TESTS OK — GET /api/produce/status correctly reports "
          "known/running/exit_code/elapsed_s/log_tail for tracked, finished, and "
          "already-reaped builds, sandboxes the log_file param, and requires auth.")


if __name__ == "__main__":
    run()
