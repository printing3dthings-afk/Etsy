#!/usr/bin/env python3
"""CI-only helper: open or update a GitHub Issue when the daily listing
integrity check (tools/listing_integrity_check.py) finds FAIL-level issues.

Usage:
    python tools/ci_report_issue.py <path-to-integrity-output.txt>

Reuses one persistent issue (tracked by a fixed marker title + label) rather
than opening a new issue every day -- a comment is appended to the existing
issue if it's still open, so Scott gets one running thread instead of issue
spam. Requires GH_TOKEN in the environment (the default GITHUB_ACTIONS
GITHUB_TOKEN is sufficient as long as the workflow grants `issues: write`).
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

MARKER_TITLE = "Daily Listing Integrity Check — FAIL detected"
LABEL = "listing-integrity"
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
    # See tools/ci_report_health_issue.py's find_open_issue for why this must be
    # percent-encoded: MARKER_TITLE's em dash trips Python 3.11's http.client
    # control-character validator when interpolated raw into the URL.
    query = f'repo:{repo} type:issue state:open label:{LABEL} in:title "{MARKER_TITLE}"'
    results = gh_request(
        "GET",
        f"https://api.github.com/search/issues?{urllib.parse.urlencode({'q': query})}",
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
                body={"name": LABEL, "color": "d73a4a", "description": "Automated listing integrity check failures"},
            )
        except Exception:
            pass  # label creation is best-effort; issue creation still works without it


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: ci_report_issue.py <integrity-output-file>", file=sys.stderr)
        return 1

    report_path = sys.argv[1]
    token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    run_url = os.environ.get("GITHUB_SERVER_URL", "") + "/" + repo + "/actions/runs/" + os.environ.get("GITHUB_RUN_ID", "")

    if not token or not repo:
        print("ERROR: GH_TOKEN and GITHUB_REPOSITORY must be set.", file=sys.stderr)
        return 1

    with open(report_path) as fh:
        report_text = fh.read()
    if len(report_text) > MAX_BODY_CHARS:
        report_text = report_text[:MAX_BODY_CHARS] + "\n\n... [truncated, see full run log for complete output]"

    body = (
        f"The daily `listing_integrity_check.py` run found FAIL-level issues.\n\n"
        f"Workflow run: {run_url}\n\n"
        f"<details><summary>Report output</summary>\n\n```\n{report_text}\n```\n</details>\n"
    )

    ensure_label_exists(repo, token)
    existing = find_open_issue(repo, token)

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


if __name__ == "__main__":
    sys.exit(main())
