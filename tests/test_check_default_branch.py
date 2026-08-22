"""
Tests for tools/check_default_branch.py (Frank upgrade Wave 1, reliability item
8, 2026-07-17) — the guardrail against GitHub's default_branch silently
drifting away from the active working branch, which caused every
schedule-triggered workflow to run old, broken code for an unknown period on
2026-07-10 before anyone noticed.

Only tests the pure check() comparison function (no live GitHub API call —
that's exercised for real by the health_watchdog.yml workflow itself, which
this test suite has no network access to call safely/deterministically). Also
confirms the current EXPECTED_DEFAULT_BRANCH constant is a non-empty,
plausible branch-name string, so an accidental blank/placeholder value would
be caught here rather than silently always "matching" nothing meaningful.

Run: python tests/test_check_default_branch.py
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import check_default_branch as cdb  # noqa: E402

_failures: list[str] = []


def check(cond: bool, msg: str) -> None:
    if not cond:
        _failures.append(msg)


def test_matching_branch_passes():
    ok, detail = cdb.check(cdb.EXPECTED_DEFAULT_BRANCH, expected=cdb.EXPECTED_DEFAULT_BRANCH)
    check(ok is True, f"an exact match should pass, got ({ok!r}, {detail!r})")
    check("matches expected" in detail, f"expected a clear ok message, got: {detail!r}")


def test_drifted_branch_fails_with_actionable_detail():
    ok, detail = cdb.check("some-stale-integration-branch", expected="claude/etsy-automation-agents-WFAPU")
    check(ok is False, f"a mismatch must fail, got ({ok!r}, {detail!r})")
    check("DRIFT" in detail, f"expected a clear DRIFT marker, got: {detail!r}")
    check("some-stale-integration-branch" in detail, "detail should name the actual (wrong) branch")
    check("claude/etsy-automation-agents-WFAPU" in detail, "detail should name the expected branch")
    check("Settings" in detail, "detail should point at the actual fix location (repo Settings)")


def test_case_sensitive_comparison():
    # Branch names are case-sensitive on GitHub -- a check that silently
    # normalized case could miss a real drift to a differently-cased branch.
    ok, _ = cdb.check("Claude/Etsy-Automation-Agents-WFAPU", expected="claude/etsy-automation-agents-WFAPU")
    check(ok is False, "branch comparison must be case-sensitive")


def test_expected_constant_is_a_plausible_branch_name():
    # Guards against an accidental blank/placeholder EXPECTED_DEFAULT_BRANCH
    # that would make every real drift silently "not match nothing" in a
    # confusing way, or make every check trivially fail.
    check(isinstance(cdb.EXPECTED_DEFAULT_BRANCH, str) and len(cdb.EXPECTED_DEFAULT_BRANCH) > 3,
          f"EXPECTED_DEFAULT_BRANCH should be a real branch name, got: {cdb.EXPECTED_DEFAULT_BRANCH!r}")
    check(" " not in cdb.EXPECTED_DEFAULT_BRANCH, "a branch name should never contain spaces")


def run() -> None:
    for fn in [v for k, v in sorted(globals().items()) if k.startswith("test_")]:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{fn.__name__} raised: {exc!r}")
    if _failures:
        print("DEFAULT-BRANCH CHECK TESTS FAILED:")
        for f in _failures:
            print(" -", f)
        sys.exit(1)
    print("DEFAULT-BRANCH CHECK TESTS OK — match/drift/case-sensitivity/constant-sanity all verified.")


if __name__ == "__main__":
    run()
