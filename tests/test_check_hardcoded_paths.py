"""
Tests for tools/check_hardcoded_paths.py (Frank upgrade Wave 1, reliability item
6, 2026-07-17) — the CI guardrail against the "works in sandbox, breaks in prod"
bug class that hit 10 separate scripts before this existed. Confirms the checker
actually distinguishes a real hardcoded-path violation from legitimate docstring
documentation (crontab examples, past-fix explanations), and that the live repo
is currently clean (this test would start failing the moment someone
reintroduces the bug class, which is the whole point).

Run: python tests/test_check_hardcoded_paths.py
"""
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "tools" / "check_hardcoded_paths.py"

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CHECKER), *args], capture_output=True, text=True)


def test_real_repo_is_currently_clean():
    r = _run()
    check(r.returncode == 0, f"the real repo should currently pass clean, got rc={r.returncode}: {r.stdout}")
    check("CHECK OK" in r.stdout, f"expected an OK message, got: {r.stdout}")


def test_catches_a_real_violation():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '"""A normal docstring, no path here."""\n'
            "import sys\n"
            "sys.path.insert(0, '/home/user/Etsy')\n"
            "ART_DIR = '/home/user/Etsy/data/digital_products'\n"
        )
        tmp_path = f.name
    try:
        r = _run("--paths", tmp_path)
        check(r.returncode == 1, f"a real violation should fail (rc=1), got rc={r.returncode}: {r.stdout}")
        check("2 occurrence" in r.stdout, f"expected 2 flagged occurrences, got: {r.stdout}")
        check(tmp_path in r.stdout or Path(tmp_path).name in r.stdout,
              f"expected the violating file to be named in output, got: {r.stdout}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_exempts_docstrings_and_crontab_examples():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            '"""\n'
            "Illustrative crontab example (documentation, not live code):\n"
            "  0 8 * * * cd /home/user/Etsy && python tools/foo.py\n"
            '"""\n'
            "import sys\n"
            "print('this file has no real violation')\n"
        )
        tmp_path = f.name
    try:
        r = _run("--paths", tmp_path)
        check(r.returncode == 0, f"a docstring-only mention should pass clean, got rc={r.returncode}: {r.stdout}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def test_handles_a_path_outside_repo_root_gracefully():
    # Regression: the first version of this checker crashed (ValueError from
    # Path.relative_to()) when a --paths target lived outside ROOT, instead of
    # just printing the absolute path. Any temp file outside this repo checkout
    # exercises that path.
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write("X = '/home/user/Etsy'\n")
        tmp_path = f.name
    try:
        r = _run("--paths", tmp_path)
        check(r.returncode == 1, f"expected a violation to be caught, got rc={r.returncode}: {r.stdout}")
        check("Traceback" not in r.stdout and "Traceback" not in r.stderr,
              f"the checker should never crash, got stderr: {r.stderr}")
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised:\n{traceback.format_exc()}")
    if _failures:
        print("HARDCODED-PATH CHECKER TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("HARDCODED-PATH CHECKER TESTS OK — catches real violations, exempts "
          "docstrings/crontab examples, the live repo is currently clean, and "
          "out-of-repo paths are handled without crashing.")


if __name__ == "__main__":
    run()
