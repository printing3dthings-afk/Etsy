#!/usr/bin/env python3
"""
Single entry point for the whole tests/ suite (Frank upgrade Wave 1, reliability
item 7, 2026-07-17). Before this, every ops_runbook "Verified" section listed
6-9 test files run individually from memory — exactly the kind of thing that
silently skips one on a busy day. This runs every tests/test_*.py in sequence
(subprocess, so one test's crash/import error can't take down the others) and
prints a pass/fail summary.

Each test file is already independently runnable (`python tests/test_X.py`,
proper sys.exit(1) on failure) — this doesn't reimplement that, just orchestrates
calling all of them and reports what happened. APP_SECRET_TOKEN is set here (if
not already set by the caller) the same way ci-smoke.yml sets it at the job
level, since a couple of the older test files rely on that rather than
self-configuring it individually.

Usage:
    python tests/run_all.py                  # run every tests/test_*.py
    python tests/run_all.py --fail-fast       # stop at the first failure
Exit code 0 = every test passed, 1 = at least one failed.
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = Path(__file__).resolve().parent

os.environ.setdefault("APP_SECRET_TOKEN", "run-all-tests-inspection-only-not-a-secret")


def discover_tests() -> list[Path]:
    return sorted(p for p in TESTS_DIR.glob("test_*.py") if p.name != Path(__file__).name)


def run_one(path: Path) -> tuple[bool, float, str]:
    start = time.monotonic()
    result = subprocess.run(
        [sys.executable, str(path)],
        cwd=str(ROOT),
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=600,
    )
    elapsed = time.monotonic() - start
    ok = result.returncode == 0
    output = (result.stdout or "") + (result.stderr or "")
    return ok, elapsed, output


# A test must never modify a git-tracked file. The one that keeps happening here
# is data/knowledge_base/: _append_ops_runbook_entry() writes to
# _OPS_RUNBOOK_PATH, which is _volume_or_local(...) -- the mounted volume on a
# deploy, but the git-tracked repo copy when no volume exists. Three separate
# test files reached it (2026-09-05) and appended fabricated incidents
# (TESTCRASH, TESTHUNG, a "Monthly competitor research refresh" that never ran)
# straight into the document Frank quotes as ground truth when Scott asks why
# something broke.
#
# A static grep over test sources was tried first and is NOT sufficient: it only
# catches a test that NAMES the writer. test_competitor_research_refresh calls
# _run_competitor_research_refresh(), which appends internally, so the grep saw
# nothing while the write happened on every run. Hashing the real files before
# and after is the only check that cannot be evaded by a call chain.
_TRACKED_KB = ROOT / "data" / "knowledge_base"


def _kb_fingerprint() -> dict[str, str]:
    import hashlib
    out = {}
    for f in sorted(_TRACKED_KB.rglob("*")):
        if f.is_file():
            out[str(f.relative_to(ROOT))] = hashlib.md5(f.read_bytes()).hexdigest()
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fail-fast", action="store_true", help="Stop at the first failing test")
    ap.add_argument("--verbose", action="store_true", help="Print each test's full output, not just failures")
    args = ap.parse_args()

    tests = discover_tests()
    print(f"Running {len(tests)} test file(s) from {TESTS_DIR}...\n")

    kb_before = _kb_fingerprint()

    results: list[tuple[str, bool, float]] = []
    for path in tests:
        print(f"  {path.name} ... ", end="", flush=True)
        try:
            ok, elapsed, output = run_one(path)
        except subprocess.TimeoutExpired:
            ok, elapsed, output = False, 600.0, "TIMED OUT after 600s"
        results.append((path.name, ok, elapsed))
        print(f"{'PASS' if ok else 'FAIL'} ({elapsed:.1f}s)")
        if args.verbose or not ok:
            for line in output.strip().splitlines()[-40:]:  # tail -40 to keep failures scannable
                print(f"      {line}")
        if not ok and args.fail_fast:
            break

    passed = sum(1 for _, ok, _ in results if ok)
    failed = [name for name, ok, _ in results if not ok]
    total_time = sum(t for _, _, t in results)

    print(f"\n{'='*60}")
    print(f"{passed}/{len(results)} passed in {total_time:.1f}s"
          + (f" ({len(tests) - len(results)} skipped after --fail-fast)" if args.fail_fast and failed else ""))
    kb_after = _kb_fingerprint()
    touched = sorted(k for k in set(kb_before) | set(kb_after)
                     if kb_before.get(k) != kb_after.get(k))

    if failed:
        print("FAILED:")
        for name in failed:
            print(f"  - {name}")
        return 1
    if touched:
        print("FAILED: the suite modified git-tracked knowledge-base files.")
        for name in touched:
            print(f"  - {name}")
        print("A test wrote into a real doc. Repoint the path it writes to (e.g. "
              "server._OPS_RUNBOOK_PATH) at a tempfile, then `git checkout --` the "
              "file above before committing — do NOT commit the diff.")
        return 1
    print("ALL TESTS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
