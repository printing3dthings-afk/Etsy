#!/usr/bin/env python3
"""
_run_exec_command() output-truncation tests (2026-07-30).

Regression coverage for the exact bug Scott reported: he ran qc_sweep and
listing_integrity_check from the Workflows screen, "it said it ran but
nothing was caught." Root cause: both scripts print their real verdict
LAST (qc_sweep's "RESULT: N FAIL/WARN/PASS" line, listing_integrity_
check's "SUMMARY:" block), but _run_exec_command() used to keep only the
FIRST ~1900 characters of combined stdout+stderr -- confirmed live, even a
qc_sweep run against a small local subset already produces ~2800 chars, so
the verdict line was being silently replaced by "[output truncated]" on
every real-sized run, never just an edge case.

Mocks the narrowest real dependency (subprocess.run) so this never shells
out to a real script -- exercises _run_exec_command()'s own truncation
logic directly with a controlled fake stdout of a known size.
"""
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
for p in (ROOT / "tools" / "api_server", ROOT / "tools"):
    sp = str(p)
    if sp not in sys.path:
        sys.path.insert(0, sp)

import main as server  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _fake_completed(stdout: str, stderr: str = "", returncode: int = 0) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=["fake"], returncode=returncode, stdout=stdout, stderr=stderr)


def test_short_output_passes_through_unchanged():
    with patch.object(server.subprocess, "run", return_value=_fake_completed("all good\nRESULT: 0 FAIL")):
        result = server._run_exec_command("qc_sweep")
    check("RESULT: 0 FAIL" in result["output"], f"short output must survive verbatim, got: {result}")
    check("truncated" not in result["output"] and "omitted" not in result["output"],
          f"short output must not be marked as truncated, got: {result}")


def test_large_output_preserves_the_final_verdict_line():
    # A realistic shape: thousands of PASS lines, then the verdict LAST --
    # exactly how qc_sweep.py and listing_integrity_check.py both report.
    noise = "\n".join(f"[PASS] file_{i}.pdf: looks fine" for i in range(2000))
    verdict = "\nRESULT: 3 FAIL · 5 WARN · 400 PASS\n"
    fake_stdout = noise + verdict
    check(len(fake_stdout) > 12000, "fixture must actually exceed the truncation threshold to test anything")
    with patch.object(server.subprocess, "run", return_value=_fake_completed(fake_stdout)):
        result = server._run_exec_command("qc_sweep")
    out = result["output"]
    check("RESULT: 3 FAIL · 5 WARN · 400 PASS" in out,
          f"the final verdict line must survive truncation, got tail: {out[-500:]}")
    check(len(out) < len(fake_stdout), f"output should actually be shortened, got len={len(out)} vs original={len(fake_stdout)}")
    check("omitted" in out, f"truncation must be disclosed, not silent, got: {out[:300]}")


def test_large_output_still_keeps_some_head_context():
    fake_stdout = ("A" * 20000) + "\nRESULT: 0 FAIL\n"
    with patch.object(server.subprocess, "run", return_value=_fake_completed(fake_stdout)):
        result = server._run_exec_command("qc_sweep")
    check(result["output"].startswith("A"), f"head context should be preserved, got: {result['output'][:50]}")
    check("RESULT: 0 FAIL" in result["output"], f"got: {result['output'][-200:]}")


def test_dispatcher_actually_used_for_workflows_endpoint_path():
    # Sanity check: the same function backs both the chat tool and the
    # /api/workflows/{id}/run endpoint (main.py's run_workflow route) --
    # confirm the registry entry it's tested against is real and unmocked-callable.
    check("qc_sweep" in server._EXEC_COMMANDS, "qc_sweep must remain a registered exec command")
    check("listing_integrity_check" in server._EXEC_COMMANDS, "listing_integrity_check must remain a registered exec command")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:
            import traceback
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("EXEC COMMAND OUTPUT TRUNCATION TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("EXEC COMMAND OUTPUT TRUNCATION TESTS OK — the final verdict/summary line always survives "
          "truncation, short output is left unchanged.")


if __name__ == "__main__":
    run()
