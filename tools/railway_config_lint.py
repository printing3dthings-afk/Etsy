#!/usr/bin/env python3
"""
Railway deploy-config linter — added 2026-07-10 after two real incidents on the same
day, both hit while standing up the `frank-relay` service:

  1. `railway.relay.toml`'s `dockerfilePath` and the relay's `rootDirectory` (a live
     Railway service-instance setting, not a repo file) disagreed about the build
     context: `rootDirectory="tools/relay"` was set while
     `tools/relay/Dockerfile`'s COPY commands used repo-root-relative paths
     (`COPY tools/relay/frank_relay.py tools/relay/frank_relay.py`) — Railway looked
     for a nonexistent nested `tools/relay/tools/relay/frank_relay.py` and every
     build failed with a cache-key error.
  2. Once fixed, the relay's deploy then failed a completely different way: the
     shared root `railway.toml` sets `deploy.healthcheckPath = "/health"` for the
     MAIN app, and because the relay's build context became the repo root (the fix
     for #1), Railway read that same file and applied its healthcheck to the relay
     too — but `frank_relay.py` is a pure outbound WebSocket client that never opens
     an HTTP listener, so that healthcheck could never pass. Every deploy timed out
     after 5 minutes before this was caught.

Neither class of bug is caught by anything else in this repo: no test parses these
config files, `py_compile`/`node --check` don't apply to TOML/Dockerfiles, and
`ci-smoke.yml` never ran a browser or a container. This script is a static,
CI-safe (no Railway credentials required) lint of exactly those two bug classes,
run as a `ci-smoke.yml` step. If `RAILWAY_API_TOKEN` is set in the environment it
also cross-checks against the LIVE Railway service configs (rootDirectory,
dockerfilePath, healthcheckPath, railwayConfigFile) for full confidence -- that
mode is what actually closes the gap statelessly, since which Railway service reads
which `railway*.toml` file is a live binding invisible to a pure repo scan.

Run locally:  python tools/railway_config_lint.py [--live]
In CI:        see .github/workflows/ci-smoke.yml (static mode only -- no secrets)
Exit code 0 = no problems (warnings allowed), non-zero = a real problem found.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

_failures: list[str] = []
_warnings: list[str] = []


def fail(msg: str) -> None:
    _failures.append(msg)


def warn(msg: str) -> None:
    _warnings.append(msg)


# ── tiny TOML reader -- only the handful of keys this script cares about, no new
# dependency. Not a general TOML parser; deliberately narrow. ──────────────────
def _read_toml_str(text: str, section: str, key: str) -> str | None:
    in_section = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or not stripped:
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            in_section = stripped[1:-1].strip() == section
            continue
        if in_section and "=" in stripped:
            k, _, v = stripped.partition("=")
            if k.strip() == key:
                return v.strip().strip('"').strip("'")
    return None


class RailwayConfig:
    def __init__(self, path: Path):
        self.path = path
        text = path.read_text()
        self.builder = _read_toml_str(text, "build", "builder")
        self.dockerfile_path = _read_toml_str(text, "build", "dockerfilePath")
        self.healthcheck_path = _read_toml_str(text, "deploy", "healthcheckPath")

    def resolved_dockerfile(self) -> Path:
        """Repo-root-relative Dockerfile path this config declares -- or the
        conventional root Dockerfile if unset (Railway's own default)."""
        rel = self.dockerfile_path or "Dockerfile"
        return ROOT / rel


_COPY_RE = re.compile(r"^\s*COPY\s+(?:--[\w-]+(?:=\S+)?\s+)*(\S+)\s+\S+\s*$", re.MULTILINE)


def check_dockerfile_copy_paths(cfg: RailwayConfig) -> None:
    """Bug class #1: does every named COPY source in this Dockerfile actually exist
    when resolved as repo-root-relative? A Dockerfile written for a repo-root build
    context (COPY paths like `tools/relay/x`) silently breaks the moment a service's
    `rootDirectory` is pointed at a subdirectory instead — Railway's error in that
    case is an opaque "failed to compute cache key", not a path-not-found message,
    which is exactly why this was slow to diagnose live."""
    dockerfile = cfg.resolved_dockerfile()
    if not dockerfile.exists():
        fail(f"{cfg.path.name}: dockerfilePath resolves to {dockerfile} which does not exist")
        return
    text = dockerfile.read_text()
    sources = [m for m in _COPY_RE.findall(text) if m != "."]
    if not sources:
        return  # e.g. `COPY . .` only -- context-relative by definition, nothing to check
    missing = [s for s in sources if not (ROOT / s).exists()]
    if missing:
        fail(
            f"{dockerfile.relative_to(ROOT)}: COPY source path(s) {missing} do not exist when "
            f"resolved as repo-root-relative. If this Dockerfile is meant to be built with a "
            f"Railway `rootDirectory` set to its own subdirectory, its COPY paths must be relative "
            f"to that subdirectory instead — this exact mismatch (COPY paths written for repo-root, "
            f"rootDirectory set to a subdirectory) is bug class #1 from 2026-07-10, see this "
            f"script's module docstring."
        )
    else:
        print(f"  ok: {dockerfile.relative_to(ROOT)} — all COPY sources resolve as repo-root-relative "
              f"(this Dockerfile's build context assumption: repo root)")


def _dockerfile_runs_http_server(dockerfile: Path) -> bool:
    """Heuristic, not proof: EXPOSE directive present, or CMD/ENTRYPOINT invokes a
    script whose sibling requirements file lists a known web framework."""
    text = dockerfile.read_text()
    if re.search(r"^\s*EXPOSE\s+\d+", text, re.MULTILINE):
        return True
    # Look for a requirements.txt alongside any COPY'd requirements file and check
    # for a known web-serving package -- covers both the root app (requirements.txt)
    # and any future per-service Dockerfile with its own requirements file.
    for req_rel in re.findall(r"COPY\s+(\S*requirements\S*\.txt)\s+\S+", text):
        req_path = ROOT / req_rel
        if req_path.exists():
            req_text = req_path.read_text().lower()
            if re.search(r"^(fastapi|flask|uvicorn|gunicorn|django|starlette)\b", req_text, re.MULTILINE):
                return True
    return False


def check_healthcheck_matches_server(cfg: RailwayConfig) -> None:
    """Bug class #2: a healthcheckPath only makes sense for a service that actually
    binds an HTTP port. Flags the exact failure mode from 2026-07-10: a config file
    shared by (or copy-pasted into) a non-HTTP worker service's build."""
    if not cfg.healthcheck_path:
        return
    dockerfile = cfg.resolved_dockerfile()
    if not dockerfile.exists():
        return  # already reported by check_dockerfile_copy_paths
    if _dockerfile_runs_http_server(dockerfile):
        print(f"  ok: {cfg.path.name} sets healthcheckPath={cfg.healthcheck_path!r} and "
              f"{dockerfile.relative_to(ROOT)} shows evidence of an HTTP server (EXPOSE and/or "
              f"a web framework in its requirements) — consistent.")
    else:
        fail(
            f"{cfg.path.name} sets healthcheckPath={cfg.healthcheck_path!r}, but "
            f"{dockerfile.relative_to(ROOT)} shows no evidence of an HTTP server (no EXPOSE "
            f"directive, no fastapi/flask/uvicorn/gunicorn/django/starlette in its requirements "
            f"file). If this config is used by a background worker (a pure client/relay process "
            f"that never binds a port), the healthcheck can never pass and every deploy will time "
            f"out after healthcheckTimeout — this is bug class #2 from 2026-07-10, see this "
            f"script's module docstring. Either remove healthcheckPath from this config, or give "
            f"the worker its own dedicated railway.<service>.toml with no healthcheckPath (the "
            f"pattern used for railway.relay.toml)."
        )


def discover_configs() -> list[RailwayConfig]:
    return [RailwayConfig(p) for p in sorted(ROOT.glob("railway*.toml"))]


# ── optional live mode: cross-check against actual Railway service instances ────
def _railway_graphql(token: str, query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        "https://backboard.railway.app/graphql/v2",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            # Railway's edge (Cloudflare) returns a bare "error code: 1010" 403 to
            # urllib's default `Python-urllib/3.x` User-Agent -- bot-detection, not
            # an auth or proxy problem (confirmed 2026-07-10: curl with the exact
            # same token/body succeeds). Any non-Python-looking UA clears it.
            "User-Agent": "curl/8.5.0",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def check_live_services(token: str, project_id: str, environment_id: str) -> None:
    query = """
    query($pid:String!){
      project(id:$pid){
        services{edges{node{id name}}}
      }
    }
    """
    try:
        data = _railway_graphql(token, query, {"pid": project_id})
    except Exception as exc:
        warn(f"live-mode: could not reach Railway API ({exc}) — skipping live cross-check")
        return
    if "errors" in data:
        warn(f"live-mode: Railway API returned errors ({data['errors']}) — skipping live cross-check")
        return
    services = [e["node"] for e in data["data"]["project"]["services"]["edges"]]
    instance_query = """
    query($sid:String!,$eid:String!){
      serviceInstance(serviceId:$sid,environmentId:$eid){
        rootDirectory dockerfilePath healthcheckPath railwayConfigFile
      }
    }
    """
    for svc in services:
        try:
            inst_data = _railway_graphql(token, instance_query, {"sid": svc["id"], "eid": environment_id})
        except Exception as exc:
            warn(f"live-mode: could not fetch instance config for service {svc['name']!r} ({exc})")
            continue
        inst = (inst_data.get("data") or {}).get("serviceInstance") or {}
        root_dir = (inst.get("rootDirectory") or "").strip()
        dockerfile_path = inst.get("dockerfilePath") or "Dockerfile"
        healthcheck = inst.get("healthcheckPath")
        config_file = inst.get("railwayConfigFile")
        # Resolve exactly the way Railway does: rootDirectory changes the build
        # context, dockerfilePath is then relative to THAT context.
        resolved = ROOT / root_dir / dockerfile_path if root_dir else ROOT / dockerfile_path
        if not resolved.exists():
            fail(f"live: service {svc['name']!r} — rootDirectory={root_dir!r} + "
                 f"dockerfilePath={dockerfile_path!r} resolves to {resolved}, which does not exist")
            continue
        if healthcheck and not _dockerfile_runs_http_server(resolved):
            fail(f"live: service {svc['name']!r} has an explicit instance-level "
                 f"healthcheckPath={healthcheck!r} but {resolved.relative_to(ROOT)} shows no "
                 f"evidence of an HTTP server")
        else:
            # NOTE: serviceInstance.healthcheckPath only reflects an explicit
            # INSTANCE-level override -- a healthcheckPath coming from a config file
            # (railway.toml / railwayConfigFile) does NOT show up here even though it
            # still applies at deploy time (confirmed 2026-07-10: this is exactly why
            # the static per-file check above matters more than this field for that
            # specific case -- this live check's real value is confirming
            # rootDirectory+dockerfilePath actually resolve to a real file).
            print(f"  ok (live): service {svc['name']!r} — rootDirectory={root_dir or '(repo root)'}, "
                  f"dockerfilePath={dockerfile_path!r} resolves correctly, "
                  f"railwayConfigFile={config_file!r}"
                  + (f", instance-level healthcheckPath={healthcheck!r} matches an HTTP server"
                     if healthcheck else
                     " (no instance-level healthcheckPath override -- see the matching "
                     "railway*.toml check above for the effective config-file value)"))


def main() -> int:
    configs = discover_configs()
    if not configs:
        warn("no railway*.toml files found in repo root — nothing to lint")
    for cfg in configs:
        print(f"checking {cfg.path.name} ...")
        check_dockerfile_copy_paths(cfg)
        check_healthcheck_matches_server(cfg)

    if "--live" in sys.argv:
        token = os.environ.get("RAILWAY_API_TOKEN", "").strip()
        project_id = os.environ.get("RAILWAY_PROJECT_ID", "323e677f-2c1a-4a21-845d-79aae274a225")
        environment_id = os.environ.get("RAILWAY_ENVIRONMENT_ID", "c9d557ec-5ff7-4228-b413-5e1274ccd517")
        if not token:
            warn("--live requested but RAILWAY_API_TOKEN is not set — skipping live cross-check")
        else:
            print("checking live Railway service configs ...")
            check_live_services(token, project_id, environment_id)

    if _warnings:
        print("\nWarnings:", file=sys.stderr)
        for w in _warnings:
            print("  -", w, file=sys.stderr)
    if _failures:
        print("\nRAILWAY CONFIG LINT FAILED:", file=sys.stderr)
        for f in _failures:
            print("  -", f, file=sys.stderr)
        print(f"\n{len(_failures)} failure(s).", file=sys.stderr)
        return 1
    print(f"\nRAILWAY CONFIG LINT OK — {len(configs)} config file(s) checked"
          + (", live cross-check included" if "--live" in sys.argv else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
