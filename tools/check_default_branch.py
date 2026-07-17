#!/usr/bin/env python3
"""
GitHub default-branch drift check (Frank upgrade Wave 1, reliability item 8,
2026-07-17).

Why this exists: every `schedule`-triggered GitHub Action (this repo's health
watchdog, the daily listing-integrity check) resolves unqualified script refs
against the repo's GitHub-configured `default_branch` — NOT necessarily
whatever branch active development is happening on. On 2026-07-10 that setting
had silently drifted to a long-stale integration branch
(`claude/etsy-agent-hub-9nnCM`) while real work happened elsewhere, so cron
jobs executed old, broken code for an unknown period — confirmed only by
manually querying the repo API (see data/knowledge_base/ops_runbook.md).
Scott fixed it by hand (Settings -> General -> Default branch); nothing
watched for it happening again.

This check queries the live GitHub API for the repo's actual `default_branch`
and compares it against EXPECTED_DEFAULT_BRANCH below — a plain constant, not
auto-derived, because "what SHOULD be default" is a human decision (which
branch is the real active one), not something inferrable from repo state.
Update the constant deliberately when the active branch legitimately changes;
this check's job is catching an UNINTENTIONAL drift, not enforcing any one
specific branch name forever.

Usage:
    python tools/check_default_branch.py
Requires GH_TOKEN + GITHUB_REPOSITORY in the environment (both are already
present in any GitHub Actions run; GH_TOKEN can be the default GITHUB_TOKEN,
read access to a repo's own settings needs no elevated scope).
Exit code 0 = matches expected, 1 = drifted (or the API call failed).
"""
import json
import os
import sys
import urllib.error
import urllib.request

EXPECTED_DEFAULT_BRANCH = "claude/etsy-automation-agents-WFAPU"


def fetch_default_branch(repo: str, token: str) -> str:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read())
    return data["default_branch"]


def check(actual: str, expected: str = EXPECTED_DEFAULT_BRANCH) -> tuple[bool, str]:
    """Pure comparison, factored out so it's testable without a real API call."""
    if actual == expected:
        return True, f"default_branch is '{actual}', matches expected."
    return False, (
        f"DRIFT: GitHub's default_branch is '{actual}', expected '{expected}'. "
        f"Every schedule-triggered workflow (health watchdog, daily listing-integrity "
        f"check) now resolves against '{actual}' instead of the active working branch — "
        f"this is exactly the 2026-07-10 incident recurring. Fix: Settings -> General -> "
        f"Default branch (or, if '{actual}' is now genuinely the correct active branch, "
        f"update EXPECTED_DEFAULT_BRANCH in tools/check_default_branch.py to match)."
    )


def main() -> int:
    token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not token or not repo:
        print("ERROR: GH_TOKEN and GITHUB_REPOSITORY must be set.", file=sys.stderr)
        return 1
    try:
        actual = fetch_default_branch(repo, token)
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR: could not fetch default_branch: {exc}", file=sys.stderr)
        return 1
    ok, detail = check(actual)
    print(detail)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
