#!/usr/bin/env python3
"""
One-command Railway rollback — added 2026-07-10 as part of the "fortress" reliability
pass. Before this script, the only documented rollback procedure was manual: open the
Railway dashboard, find the last known-good deployment in the Deployments tab, click
Redeploy (see the "Manual deploy rollback procedure" entry in ops_runbook.md, now
superseded by this). No automated rollback existed, and there were zero git tags to
even identify a "known-good" checkpoint by name.

Uses the same Railway GraphQL API (backboard.railway.app/graphql/v2) and
Authorization/User-Agent pattern already proven working this session (see
tools/railway_config_lint.py's module docstring for why the User-Agent header is
required -- Railway's Cloudflare edge blocks Python's default UA with a bare
"error code: 1010" 403, unrelated to auth or proxy config).

Usage:
    python tools/rollback.py --list [--service main|relay]
        Show recent deployments for a service (or both) without changing anything.

    python tools/rollback.py --service main
        Roll back the main app to its last SUCCESS deployment before the current
        one. Prints what it's about to do and asks for confirmation unless --yes
        is passed.

    python tools/rollback.py --service relay --deployment-id <id>
        Roll back to a specific deployment ID instead of "the previous one".

    python tools/rollback.py --service main --yes
        Skip the confirmation prompt (for scripted/emergency use).

This is a real, hard-to-reverse action against production infrastructure --
confirmation is required by default, matching every other production-affecting
action taken this session.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request

RAILWAY_GRAPHQL_URL = "https://backboard.railway.app/graphql/v2"
PROJECT_ID = os.environ.get("RAILWAY_PROJECT_ID", "323e677f-2c1a-4a21-845d-79aae274a225")
ENVIRONMENT_ID = os.environ.get("RAILWAY_ENVIRONMENT_ID", "c9d557ec-5ff7-4228-b413-5e1274ccd517")
SERVICES = {
    "main": {"id": "696d3a60-2206-4b07-8ba4-de95f898eb27", "label": "Etsy (main app)"},
    "etsy": {"id": "696d3a60-2206-4b07-8ba4-de95f898eb27", "label": "Etsy (main app)"},
    "relay": {"id": "4a555898-5615-47f8-bed7-03f9ba2e44ec", "label": "frank-relay"},
}


def _gql(token: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        RAILWAY_GRAPHQL_URL,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # See tools/railway_config_lint.py's module docstring: Railway's edge
            # blocks urllib's default User-Agent with a bare 403 -- confirmed
            # unrelated to the proxy/auth, any non-Python-looking UA clears it.
            "User-Agent": "curl/8.5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read())
    if "errors" in data:
        raise RuntimeError(f"Railway API error: {data['errors']}")
    return data


def _list_deployments(token: str, service_id: str, first: int = 10) -> list[dict]:
    query = """
    query($sid:String!,$eid:String!,$first:Int!){
      deployments(input:{serviceId:$sid,environmentId:$eid},first:$first){
        edges{node{id status createdAt meta}}
      }
    }
    """
    data = _gql(token, query, {"sid": service_id, "eid": ENVIRONMENT_ID, "first": first})
    return [e["node"] for e in data["data"]["deployments"]["edges"]]


def _rollback_to(token: str, deployment_id: str) -> dict:
    mutation = "mutation($id:String!){deploymentRollback(id:$id)}"
    return _gql(token, mutation, {"id": deployment_id})


def _get_status(token: str, deployment_id: str) -> str:
    query = "query($id:String!){deployment(id:$id){status}}"
    data = _gql(token, query, {"id": deployment_id})
    return data["data"]["deployment"]["status"]


def cmd_list(token: str, service_key: str) -> None:
    svc = SERVICES[service_key]
    deployments = _list_deployments(token, svc["id"])
    print(f"\n{svc['label']} — last {len(deployments)} deployments:")
    for i, d in enumerate(deployments):
        marker = " <- current" if i == 0 else ""
        commit_msg = ((d.get("meta") or {}).get("commitMessage") or "").splitlines()[0][:70]
        print(f"  [{i}] {d['id']}  {d['status']:10s}  {d['createdAt']}  {commit_msg}{marker}")


def cmd_rollback(token: str, service_key: str, deployment_id: str | None, skip_confirm: bool) -> int:
    svc = SERVICES[service_key]
    deployments = _list_deployments(token, svc["id"])
    if not deployments:
        print(f"No deployments found for {svc['label']}.", file=sys.stderr)
        return 1

    current = deployments[0]
    if deployment_id is None:
        # Railway marks a deployment REMOVED once a newer one supersedes it -- that's
        # normal lifecycle, not a failure (confirmed 2026-07-10: every deployment
        # this session shows REMOVED except the current one, even ones that were
        # perfectly healthy at the time). Only FAILED/CRASHED are genuinely bad.
        candidates = [d for d in deployments[1:] if d["status"] in ("SUCCESS", "REMOVED")]
        if not candidates:
            print(f"No prior good deployment found for {svc['label']} in the last "
                  f"{len(deployments)} deployments — nothing safe to roll back to automatically. "
                  f"Pass --deployment-id explicitly if you know a good one further back.",
                  file=sys.stderr)
            return 1
        target = candidates[0]
    else:
        matches = [d for d in deployments if d["id"] == deployment_id]
        if not matches:
            print(f"Deployment {deployment_id!r} not found in the last {len(deployments)} "
                  f"deployments for {svc['label']}. Run --list to see available IDs.",
                  file=sys.stderr)
            return 1
        target = matches[0]

    print(f"\nService: {svc['label']}")
    print(f"Current deployment: {current['id']}  ({current['status']}, {current['createdAt']})")
    print(f"Rolling back to:    {target['id']}  ({target['status']}, {target['createdAt']})")
    if target["id"] == current["id"]:
        print("Target is already the current deployment — nothing to do.")
        return 0

    if not skip_confirm:
        answer = input("\nProceed with rollback? [y/N] ").strip().lower()
        if answer != "y":
            print("Aborted.")
            return 1

    print("Rolling back...")
    _rollback_to(token, target["id"])

    # deploymentRollback triggers a NEW deployment built from the target's snapshot
    # -- it does not reactivate the target's own (now-permanently-REMOVED) ID
    # (confirmed 2026-07-10: polling the target ID directly never leaves REMOVED).
    # Poll the service's deployment list instead, watching for a new entry to
    # appear at the front (newer createdAt than the pre-rollback current one).
    new_deployment = None
    for _ in range(20):
        time.sleep(3)
        latest = _list_deployments(token, svc["id"], first=1)
        if latest and latest[0]["id"] != current["id"]:
            new_deployment = latest[0]
            break
    if new_deployment is None:
        print("Timed out waiting for a new deployment to appear after rollback — "
              "check the Railway dashboard directly.", file=sys.stderr)
        return 1

    status = new_deployment["status"]
    for _ in range(20):
        if status in ("SUCCESS", "FAILED", "CRASHED"):
            break
        time.sleep(3)
        status = _get_status(token, new_deployment["id"])
    else:
        status = f"{status} (timed out waiting for a terminal state)"

    print(f"New deployment {new_deployment['id']} (from rollback target {target['id']}): {status}")
    if status != "SUCCESS":
        print("Rollback did not report SUCCESS — check the Railway dashboard directly.",
              file=sys.stderr)
        return 1
    print(f"{svc['label']} rolled back successfully (now running {new_deployment['id']}, "
          f"built from {target['id']}'s snapshot).")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--service", choices=sorted(set(SERVICES.keys())), default=None,
                         help="Which service to act on (main/etsy or relay). Required unless --list with no service (lists both).")
    parser.add_argument("--list", action="store_true", help="List recent deployments, don't roll back.")
    parser.add_argument("--deployment-id", default=None, help="Roll back to this specific deployment ID instead of the previous SUCCESS.")
    parser.add_argument("--yes", action="store_true", help="Skip the confirmation prompt.")
    args = parser.parse_args()

    token = os.environ.get("RAILWAY_API_TOKEN", "").strip()
    if not token:
        print("RAILWAY_API_TOKEN is not set.", file=sys.stderr)
        return 1

    if args.list:
        services_to_list = [args.service] if args.service else list(dict.fromkeys(["main", "relay"]))
        for key in services_to_list:
            cmd_list(token, key)
        return 0

    if not args.service:
        print("Specify --service main|relay (or use --list to see options).", file=sys.stderr)
        return 1

    return cmd_rollback(token, args.service, args.deployment_id, args.yes)


if __name__ == "__main__":
    sys.exit(main())
