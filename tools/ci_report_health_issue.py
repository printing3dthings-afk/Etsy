#!/usr/bin/env python3
"""CI-only helper: open, update, or auto-close a GitHub Issue based on the
result of the external `/health` watchdog (.github/workflows/health_watchdog.yml).

Usage:
    python tools/ci_report_health_issue.py <ok|fail> [details-text]

Reuses the same one-persistent-issue-by-marker-title pattern as
tools/ci_report_issue.py so Scott gets one running thread per incident instead
of issue spam. On recovery (status=ok with an existing open tracking issue),
comments "recovered" and closes the issue rather than leaving it open forever.
Requires GH_TOKEN in the environment (the default GITHUB_ACTIONS GITHUB_TOKEN
is sufficient as long as the workflow grants `issues: write`).
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

MARKER_TITLE = "Frank Health Watchdog — outage detected"
LABEL = "health-watchdog"
MAX_BODY_CHARS = 50000  # GitHub issue/comment body limit is ~65k chars


def gh_request(method: str, url: str, token: str, body: dict | None = None) -> dict:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {method} {url} -> {e.code}: {e.read().decode()}")


def find_open_issue(repo: str, token: str) -> dict | None:
    results = gh_request(
        "GET",
        f"https://api.github.com/search/issues?q=repo:{repo}+type:issue+state:open+label:{LABEL}+in:title+\"{MARKER_TITLE}\"",
        token,
    )
    items = results.get("items", [])
    return items[0] if items else None


def ensure_label_exists(repo: str, token: str) -> None:
    try:
        gh_request("GET", f"https://api.github.com/repos/{repo}/labels/{LABEL}", token)
    except Exception:
        try:
            gh_request(
                "POST",
                f"https://api.github.com/repos/{repo}/labels",
                token,
                body={"name": LABEL, "color": "b60205", "description": "External Frank /health watchdog outage tracking"},
            )
        except Exception:
            pass  # label creation is best-effort; issue creation still works without it


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in ("ok", "fail"):
        print("Usage: ci_report_health_issue.py <ok|fail> [details-text]", file=sys.stderr)
        return 1

    status = sys.argv[1]
    details = sys.argv[2] if len(sys.argv) > 2 else ""
    token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    run_url = os.environ.get("GITHUB_SERVER_URL", "") + "/" + repo + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    if not token or not repo:
        print("ERROR: GH_TOKEN and GITHUB_REPOSITORY must be set.", file=sys.stderr)
        return 1

    if len(details) > MAX_BODY_CHARS:
        details = details[:MAX_BODY_CHARS] + "\n\n... [truncated, see full run log for complete output]"

    ensure_label_exists(repo, token)
    existing = find_open_issue(repo, token)

    if status == "fail":
        body = (
            f"Frank's `/health` endpoint failed a check at {now}.\n\n"
            f"Workflow run: {run_url}\n\n"
            f"<details><summary>Details</summary>\n\n```\n{details}\n```\n</details>\n"
        )
        if existing:
            gh_request(
                "POST",
                f"https://api.github.com/repos/{repo}/issues/{existing['number']}/comments",
                token,
                body={"body": body},
            )
            print(f"Appended comment to existing issue #{existing['number']}.")
        else:
            created = gh_request(
                "POST",
                f"https://api.github.com/repos/{repo}/issues",
                token,
                body={"title": MARKER_TITLE, "body": body, "labels": [LABEL]},
            )
            print(f"Created new issue #{created.get('number')}.")
        return 0

    # status == "ok"
    if existing:
        gh_request(
            "POST",
            f"https://api.github.com/repos/{repo}/issues/{existing['number']}/comments",
            token,
            body={"body": f"Recovered as of {now}. `/health` is responding normally again.\n\nWorkflow run: {run_url}"},
        )
        gh_request(
            "PATCH",
            f"https://api.github.com/repos/{repo}/issues/{existing['number']}",
            token,
            body={"state": "closed"},
        )
        print(f"Closed recovered issue #{existing['number']}.")
    else:
        print("Health check OK, no open issue to close.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
