#!/usr/bin/env python3
"""CI-only helper: refresh the Etsy OAuth access token and rotate the
ETSY_ACCESS_TOKEN / ETSY_REFRESH_TOKEN GitHub Actions secrets in place.

Why this exists: Etsy's refresh endpoint returns a NEW refresh token on every
call (refresh-token rotation) and invalidates the old one. A scheduled
workflow that just reads ETSY_REFRESH_TOKEN from a secret and never writes
the rotated value back would work exactly once -- the second scheduled run
would get invalid_grant from Etsy because the secret still holds the token
that was already consumed on day 1.

`EtsyAPIClient.refresh_access_token()` (tools/etsy_api.py) already does the
token exchange, but only persists results to a local .env file -- correct
for Scott's machine, useless on an ephemeral GitHub Actions runner. This
script does the same OAuth exchange and then writes the two rotated values
back to the repo's Actions secrets via the GitHub REST API, so the next
scheduled run picks up a still-valid refresh token.

Requires:
  - ETSY_CLIENT_ID, ETSY_REFRESH_TOKEN: read from env (sourced from secrets)
  - GH_PAT_SECRETS: a fine-grained GitHub PAT scoped to this repo with
    "Secrets: Read and write" permission. The default GITHUB_TOKEN cannot
    write Actions secrets, so this must be a separate PAT added by Scott.
  - GITHUB_REPOSITORY: auto-set by GitHub Actions ("owner/repo")

Optional (recommended -- closes a real divergence bug, see below):
  - RAILWAY_APP_URL: base URL of the live dashboard server, e.g.
    https://onbrandcraftz.up.railway.app
  - APP_SECRET_TOKEN: same bearer token the dashboard/CEO agent uses
    (already exists as a Railway env var; add it as a GH secret too)

On success: prints the new access token to GITHUB_ENV (masked) so later
steps in the same job can use it immediately, and updates both secrets for
future runs.

Exits non-zero (with a clear message) if GH_PAT_SECRETS is missing rather
than silently skipping the secret rotation -- skipping would make the
workflow look like it succeeded today while guaranteeing tomorrow's run
fails on invalid_grant.

Why RAILWAY_APP_URL/APP_SECRET_TOKEN matter (diagnosed 2026-06-17, see
ops_runbook.md): the live dashboard server ALSO refreshes this same Etsy
refresh token reactively (whenever its access token has expired). Etsy
invalidates the previous refresh token on every use -- so without a shared
source of truth, this workflow and the live server independently rotate the
SAME credential and silently invalidate each other's copy. Whichever side
refreshes last wins; the other gets a hard invalid_grant on its next attempt
and needs a manual tools/etsy_oauth.py re-auth. When these two are set, this
script fetches the live server's lineage-true token before refreshing (it
may be newer than this workflow's own GH secret) and pushes the rotated
result back to the server's durable DB after refreshing, so both sides stay
on one lineage. If unset, this script falls back to GH-secrets-only rotation
exactly as before -- still functional, just not collision-proof.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

try:
    from nacl import encoding, public
except ImportError:
    print("ERROR: PyNaCl is not installed. Add 'PyNaCl>=1.5.0' to requirements.txt "
          "and `pip install -r requirements.txt` before running this script.", file=sys.stderr)
    sys.exit(1)

ETSY_TOKEN_URL = "https://api.etsy.com/v3/public/oauth/token"


def refresh_etsy_token(client_id: str, refresh_token: str) -> dict:
    payload = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "client_id": client_id,
        "refresh_token": refresh_token,
    }).encode()
    req = urllib.request.Request(
        ETSY_TOKEN_URL,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def github_api_request(method: str, url: str, token: str, body: dict | None = None) -> dict:
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


def encrypt_secret(public_key_b64: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key_b64.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return base64.b64encode(encrypted).decode("utf-8")


def update_repo_secret(repo: str, pat: str, secret_name: str, secret_value: str) -> None:
    key_info = github_api_request(
        "GET", f"https://api.github.com/repos/{repo}/actions/secrets/public-key", pat
    )
    encrypted_value = encrypt_secret(key_info["key"], secret_value)
    github_api_request(
        "PUT",
        f"https://api.github.com/repos/{repo}/actions/secrets/{secret_name}",
        pat,
        body={"encrypted_value": encrypted_value, "key_id": key_info["key_id"]},
    )


def mask_and_export(name: str, value: str) -> None:
    print(f"::add-mask::{value}")
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a") as fh:
            fh.write(f"{name}={value}\n")


def fetch_railway_tokens(base_url: str, app_token: str) -> dict | None:
    """GET the live server's current lineage-true token pair, if reachable."""
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/etsy-tokens",
        headers={"Authorization": f"Bearer {app_token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        print(f"WARNING: could not fetch live server's Etsy token state: {e}", file=sys.stderr)
        return None


def push_railway_tokens(base_url: str, app_token: str, access_token: str, refresh_token: str, parent: str) -> None:
    """POST the freshly-rotated pair back so the live server adopts the same lineage."""
    body = json.dumps({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "parent_refresh_token": parent,
    }).encode()
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/etsy-tokens",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {app_token}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        print("Pushed rotated Etsy token pair to the live server -- lineages in sync.")
    except Exception as e:
        print(f"WARNING: could not push rotated token to the live server: {e}", file=sys.stderr)


def main() -> int:
    client_id = os.environ.get("ETSY_CLIENT_ID", "").strip()
    refresh_token = os.environ.get("ETSY_REFRESH_TOKEN", "").strip()
    pat = os.environ.get("GH_PAT_SECRETS", "").strip()
    repo = os.environ.get("GITHUB_REPOSITORY", "").strip()
    railway_url = os.environ.get("RAILWAY_APP_URL", "").strip()
    app_token = os.environ.get("APP_SECRET_TOKEN", "").strip()

    if not client_id or not refresh_token:
        print("ERROR: ETSY_CLIENT_ID and/or ETSY_REFRESH_TOKEN secrets are not set.", file=sys.stderr)
        return 1

    if not pat:
        print(
            "ERROR: GH_PAT_SECRETS is not set. A fine-grained GitHub PAT with "
            "'Secrets: Read and write' permission on this repo is required so the "
            "rotated Etsy refresh token can be written back -- otherwise tomorrow's "
            "scheduled run will fail with invalid_grant. Add it as a repo secret "
            "named GH_PAT_SECRETS before enabling this workflow.",
            file=sys.stderr,
        )
        return 1

    sync_with_railway = bool(railway_url and app_token)
    if not sync_with_railway:
        print(
            "NOTE: RAILWAY_APP_URL/APP_SECRET_TOKEN not set -- rotating from this "
            "workflow's own GH secret only. This works but can silently diverge from "
            "the live server's own token rotations (see ops_runbook.md, 2026-06-17). "
            "Add both as repo secrets to close that gap.",
        )
    else:
        live = fetch_railway_tokens(railway_url, app_token)
        if live and live.get("refresh_token") and live["refresh_token"] != refresh_token:
            print("Live server has a newer refresh token than this workflow's GH secret -- using it.")
            refresh_token = live["refresh_token"]

    try:
        token_data = refresh_etsy_token(client_id, refresh_token)
    except Exception as e:
        print(f"ERROR: Etsy token refresh failed: {e}", file=sys.stderr)
        return 1

    new_access = token_data.get("access_token", "")
    new_refresh = token_data.get("refresh_token", refresh_token)
    if not new_access:
        print(f"ERROR: Etsy token refresh response had no access_token: {token_data}", file=sys.stderr)
        return 1

    mask_and_export("ETSY_ACCESS_TOKEN", new_access)

    try:
        update_repo_secret(repo, pat, "ETSY_ACCESS_TOKEN", new_access)
        update_repo_secret(repo, pat, "ETSY_REFRESH_TOKEN", new_refresh)
    except Exception as e:
        print(f"ERROR: failed to write rotated tokens back to GitHub secrets: {e}", file=sys.stderr)
        return 1

    if sync_with_railway:
        push_railway_tokens(railway_url, app_token, new_access, new_refresh, refresh_token)

    print("Etsy access token refreshed and GitHub secrets rotated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
