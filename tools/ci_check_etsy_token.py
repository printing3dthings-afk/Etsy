#!/usr/bin/env python3
"""CI-only: check Frank's Etsy connection from outside Frank, and tell Scott in
time (2026-10-23).

    python tools/ci_check_etsy_token.py

Reads GET /api/credentials/status on the live deployment (RAILWAY_APP_URL,
bearer APP_SECRET_TOKEN) and opens one GitHub issue -- GitHub emails Scott --
when any of these is true:

  - Etsy is not live (etsy_live false: the token was rejected, or worse);
  - the refresh token was last rotated WARN_DAYS or fewer days before Etsy's
    90-day limit (default 14, so from day 76);
  - the check itself cannot run (secret missing, server unreachable, 401).

Why outside Frank: the in-app warning (a Frank to-do and an alert-bell entry
at 75 days) lives inside the same server whose Etsy link it is warning about,
and only shows to someone who opens the dashboard. The connection died
silently in October 2026 with that warning in place.

While a problem lasts it comments at most once a day; when it clears it
comments "recovered" and closes the issue. The three fields Scott asks about
are also printed as run annotations, readable from the API without the log.
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

MARKER_TITLE = "Etsy connection needs attention"
LABEL = "etsy-token-watch"
LIMIT_DAYS = 90   # Etsy's refresh token dies after 90 days with no rotation


def note(level: str, msg: str) -> None:
    # a workflow annotation: one line, no secrets (the error text is Etsy's
    # message, cut to 120 characters by the server)
    print(f"::{level} title=Etsy token watch::{msg.replace(chr(10), ' ')}")


def gh(method: str, url: str, token: str, body: dict | None = None) -> dict:
    req = urllib.request.Request(
        url, data=json.dumps(body).encode() if body is not None else None, method=method,
        headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"GitHub API {method} {url} -> {e.code}: {e.read().decode()[:300]}")


def read_status(base: str, app_token: str) -> dict:
    req = urllib.request.Request(base.rstrip("/") + "/api/credentials/status",
                                 headers={"Authorization": f"Bearer {app_token}"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def assess(status: dict, now: datetime, warn_days: int) -> tuple[list[str], dict]:
    """The problems to report, and the facts behind them."""
    facts = {"etsy_live": status.get("etsy_live"), "etsy_live_error": status.get("etsy_live_error"),
             "etsy_tokens_updated_at": status.get("etsy_tokens_updated_at"), "age_days": None,
             "stale": bool(status.get("stale"))}
    problems = []
    if not facts["etsy_live"]:
        problems.append(f"Etsy is not live: {facts['etsy_live_error'] or 'no error text'}")
    updated = facts["etsy_tokens_updated_at"]
    if updated:
        try:
            t = datetime.fromisoformat(str(updated))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            facts["age_days"] = (now - t).days
        except ValueError:
            problems.append(f"etsy_tokens_updated_at is not a date: {updated!r}")
    else:
        problems.append("Frank has no record of when the Etsy token last rotated")
    age = facts["age_days"]
    if age is not None and age >= LIMIT_DAYS - warn_days:
        left = LIMIT_DAYS - age
        problems.append(
            f"the refresh token last rotated {age} days ago; Etsy drops it at {LIMIT_DAYS} days "
            + (f"({left} days left)" if left > 0 else "(already past the limit)"))
    return problems, facts


def report(repo: str, token: str, problems: list[str], facts: dict, run_url: str, now: datetime) -> None:
    try:
        gh("POST", f"https://api.github.com/repos/{repo}/labels", token,
           {"name": LABEL, "color": "d93f0b", "description": "Frank's Etsy OAuth connection"})
    except RuntimeError:
        pass   # already there
    q = f'repo:{repo} type:issue state:open label:{LABEL} in:title "{MARKER_TITLE}"'
    found = gh("GET", "https://api.github.com/search/issues?" + urllib.parse.urlencode({"q": q}), token)
    issue = (found.get("items") or [None])[0]
    today = now.strftime("%Y-%m-%d")
    if problems:
        body = (f"Checked {now:%Y-%m-%d %H:%M} UTC from GitHub Actions ({run_url}).\n\n"
                + "".join(f"- {p}\n" for p in problems)
                + f"\n`etsy_live` = {facts['etsy_live']}  \n`etsy_live_error` = {facts['etsy_live_error']}  \n"
                  f"`etsy_tokens_updated_at` = {facts['etsy_tokens_updated_at']}\n\n"
                  "**To fix:** on your own computer, `python tools/etsy_oauth.py` -> sign in to Etsy -> "
                  "Allow -> copy the new `ETSY_ACCESS_TOKEN` and `ETSY_REFRESH_TOKEN` it prints into "
                  "Railway's variables. Frank picks up a fresh manual re-auth on its next restart.\n")
        if not issue:
            made = gh("POST", f"https://api.github.com/repos/{repo}/issues", token,
                      {"title": MARKER_TITLE, "body": body, "labels": [LABEL]})
            print(f"Opened issue #{made.get('number')}")
            return
        comments = gh("GET", f"https://api.github.com/repos/{repo}/issues/{issue['number']}/comments?per_page=100", token)
        if any(str(c.get("created_at", "")).startswith(today) for c in comments) or \
                str(issue.get("created_at", "")).startswith(today):
            print(f"Issue #{issue['number']} already updated today.")
            return
        gh("POST", f"https://api.github.com/repos/{repo}/issues/{issue['number']}/comments", token, {"body": body})
        print(f"Commented on issue #{issue['number']}")
    elif issue:
        gh("POST", f"https://api.github.com/repos/{repo}/issues/{issue['number']}/comments", token,
           {"body": f"Recovered at {now:%Y-%m-%d %H:%M} UTC: Etsy is live and the token last rotated "
                    f"{facts['age_days']} days ago. Closing."})
        gh("PATCH", f"https://api.github.com/repos/{repo}/issues/{issue['number']}", token, {"state": "closed"})
        print(f"Closed issue #{issue['number']}")


def main() -> int:
    base = os.environ.get("RAILWAY_APP_URL", "").strip()
    app_token = os.environ.get("APP_SECRET_TOKEN", "").strip()
    gh_token = os.environ.get("GH_TOKEN", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    warn_days = int(os.environ.get("WARN_DAYS", "14"))
    run_url = f"{os.environ.get('GITHUB_SERVER_URL', '')}/{repo}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    now = datetime.now(timezone.utc)

    if not base or not app_token:
        problems = ["the check cannot run: RAILWAY_APP_URL and/or APP_SECRET_TOKEN are not set as "
                    "Actions secrets (Settings -> Secrets and variables -> Actions)"]
        facts = {"etsy_live": None, "etsy_live_error": None, "etsy_tokens_updated_at": None, "age_days": None}
    else:
        try:
            problems, facts = assess(read_status(base, app_token), now, warn_days)
        except Exception as e:   # unreachable, 401, bad JSON: all of them mean nobody is watching
            problems = [f"the check cannot read /api/credentials/status: {str(e)[:200]}"]
            facts = {"etsy_live": None, "etsy_live_error": None, "etsy_tokens_updated_at": None, "age_days": None}

    note("notice", f"etsy_live={facts['etsy_live']} | etsy_live_error={facts['etsy_live_error']} | "
                   f"etsy_tokens_updated_at={facts['etsy_tokens_updated_at']} | age_days={facts['age_days']}")
    for p in problems:
        note("warning", p)
    if gh_token and repo:
        report(repo, gh_token, problems, facts, run_url, now)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
