"""
Workflows screen audit fixes (2026-08-01).

Covers:
- GET /api/workflows now reports `timeout` and `running` per entry, and
  fixes acronym-unaware title-casing ("Qc Sweep" -> "QC Sweep", "Backup Hub
  Db" -> "Backup Hub DB").
- POST /api/workflows/{id}/run now uses _rate_limited_auth (generate_
  coloring_pages spends real gpt-image-1 budget per call -- every other
  paid-generation endpoint in this codebase already gates on this).
- _run_exec_command()'s long_running branch now refuses to start a second
  process for a script that's already running (checked via proc.poll(),
  not just dict membership, since finished procs sit in _LONG_RUNNING_PROCS
  unreaped for up to an hour).

Mocks the narrowest real dependency (subprocess.Popen) so this never spawns
a real gpt-image-1 generation. Same pattern as
tests/test_exec_command_output_truncation.py and
tests/test_health_check_reap.py.
"""
import asyncio
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent

_tmp_db = tempfile.NamedTemporaryFile(prefix="frank_workflows_test_", suffix=".db", delete=False)
_tmp_db.close()
os.environ["DB_PATH"] = _tmp_db.name
os.environ.setdefault("APP_SECRET_TOKEN", "workflows-test-not-a-real-secret")

for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_get_workflows_includes_timeout_and_running_fields():
    result = asyncio.run(server.get_workflows(_token="test"))
    by_id = {w["id"]: w for w in result["workflows"]}
    check("shop_health_check" in by_id, f"expected shop_health_check registered, got ids: {list(by_id)}")
    w = by_id["shop_health_check"]
    check(w.get("timeout") == 150, f"expected the real configured timeout (150), got: {w.get('timeout')}")
    check("running" in w, f"expected a running field on every entry, got: {w}")
    check(w["running"] is False, f"nothing is running in this test, expected running=False, got: {w['running']}")


def test_get_workflows_fixes_acronym_title_casing():
    result = asyncio.run(server.get_workflows(_token="test"))
    by_id = {w["id"]: w for w in result["workflows"]}
    check(by_id["qc_sweep"]["name"] == "QC Sweep", f"expected 'QC Sweep', got: {by_id['qc_sweep']['name']!r}")
    check(by_id["backup_hub_db"]["name"] == "Backup Hub DB",
          f"expected 'Backup Hub DB', got: {by_id['backup_hub_db']['name']!r}")
    # a name with no acronym in it should still title-case normally
    check(by_id["shop_health_check"]["name"] == "Shop Health Check",
          f"expected normal title-casing to still work, got: {by_id['shop_health_check']['name']!r}")


def test_get_workflows_reports_running_true_for_a_live_matching_script():
    fake_proc = MagicMock(spec=subprocess.Popen)
    fake_proc.poll.return_value = None  # still running
    server._LONG_RUNNING_PROCS[999001] = (fake_proc, "generate_coloring_pages", datetime.now(timezone.utc))
    try:
        result = asyncio.run(server.get_workflows(_token="test"))
        by_id = {w["id"]: w for w in result["workflows"]}
        check(by_id["generate_coloring_pages"]["running"] is True,
              "a live proc for this script's cmd_name should mark it running")
        # generate_coloring_pages_quick shares the same underlying script and
        # should also read as running, since a real conflict exists.
        check(by_id["generate_coloring_pages_quick"]["running"] is True,
              "a sibling registry entry using the same script should also read as running")
    finally:
        server._LONG_RUNNING_PROCS.pop(999001, None)


def test_get_workflows_reports_running_false_once_process_finished():
    fake_proc = MagicMock(spec=subprocess.Popen)
    fake_proc.poll.return_value = 0  # finished, not yet reaped
    server._LONG_RUNNING_PROCS[999002] = (fake_proc, "generate_coloring_pages", datetime.now(timezone.utc))
    try:
        result = asyncio.run(server.get_workflows(_token="test"))
        by_id = {w["id"]: w for w in result["workflows"]}
        check(by_id["generate_coloring_pages"]["running"] is False,
              "a finished (but unreaped) proc must not read as running")
    finally:
        server._LONG_RUNNING_PROCS.pop(999002, None)


def test_post_workflow_run_endpoint_uses_rate_limited_auth():
    route = next((r for r in server.app.routes
                  if getattr(r, "path", "") == "/api/workflows/{workflow_id}/run"), None)
    check(route is not None, "the workflows run route must be registered")
    if route is not None:
        deps = [d.call for d in route.dependant.dependencies]
        check(server._rate_limited_auth in deps,
              f"post_workflow_run must use _rate_limited_auth (generate_coloring_pages spends real "
              f"gpt-image-1 budget), got deps calling {deps}")


def test_run_exec_command_refuses_to_start_a_duplicate_long_running_script():
    fake_running = MagicMock(spec=subprocess.Popen)
    fake_running.poll.return_value = None  # still running
    server._LONG_RUNNING_PROCS[999003] = (fake_running, "generate_coloring_pages", datetime.now(timezone.utc))
    try:
        with patch.object(server.subprocess, "Popen") as mock_popen:
            result = server._run_exec_command("generate_coloring_pages_quick")
        check(mock_popen.called is False,
              "must not spawn a second process for the same underlying script while one is already running")
        check(result.get("started") is False, f"expected started=False, got: {result}")
        check("already running" in (result.get("error") or "").lower(), f"expected a clear error, got: {result}")
    finally:
        server._LONG_RUNNING_PROCS.pop(999003, None)


def test_run_exec_command_allows_a_second_run_once_the_first_finished():
    fake_finished = MagicMock(spec=subprocess.Popen)
    fake_finished.poll.return_value = 0  # finished, unreaped
    server._LONG_RUNNING_PROCS[999004] = (fake_finished, "generate_coloring_pages", datetime.now(timezone.utc))
    try:
        fake_new_proc = MagicMock(spec=subprocess.Popen)
        fake_new_proc.pid = 999005
        with patch.object(server.subprocess, "Popen", return_value=fake_new_proc) as mock_popen:
            result = server._run_exec_command("generate_coloring_pages_quick")
        check(mock_popen.called is True,
              "a finished-but-unreaped prior process must not block a new run of the same script")
        check(result.get("started") is True, f"expected started=True, got: {result}")
    finally:
        server._LONG_RUNNING_PROCS.pop(999004, None)
        server._LONG_RUNNING_PROCS.pop(999005, None)


def test_run_exec_command_unrelated_script_is_unaffected_by_a_running_one():
    fake_running = MagicMock(spec=subprocess.Popen)
    fake_running.poll.return_value = None
    server._LONG_RUNNING_PROCS[999006] = (fake_running, "generate_coloring_pages", datetime.now(timezone.utc))
    try:
        with patch.object(server.subprocess, "run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(args=["fake"], returncode=0, stdout="ok", stderr="")
            result = server._run_exec_command("qc_sweep")
        check(mock_run.called is True, "an unrelated non-long_running command must run normally")
        check(result.get("success") is True, f"expected a normal successful result, got: {result}")
    finally:
        server._LONG_RUNNING_PROCS.pop(999006, None)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("WORKFLOWS SCREEN TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("WORKFLOWS SCREEN TESTS OK — timeout/running fields, acronym title-casing, "
          "rate-limited run endpoint, and the already-running dedupe guard are all verified.")


if __name__ == "__main__":
    run()
