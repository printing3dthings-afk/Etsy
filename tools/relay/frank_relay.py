#!/usr/bin/env python3
"""
Frank Local Relay — Step 1 skeleton (sub-step 1c)

Connects to the Hub's /ws/relay WebSocket and executes Frank's local_* tool
calls there, returning results into the same chat turn. The relay is
intentionally "dumb" — Frank's hands/ears, not a second brain. It owns no
conversation and makes no decisions about what to run; it only executes what
the server asks, after its own independent safety checks (kill switch,
Allowed Folders realpath check).

Two supported deployment modes, same script, no code changes needed:
  1. Scott's own computer — gives Frank access to Scott's local filesystem.
     Run manually whenever Frank needs that machine's files.
  2. A dedicated always-on Railway service — gives Frank a persistent cloud
     workspace (its own Allowed Folder on its own Railway Volume) that's
     connected 24/7, independent of whether any laptop is open. See
     tools/relay/Dockerfile for the container build used by that service.

Step 1 scope: local_read_file and local_list_dir only (instant, read-only).
local_write_file / local_delete / local_exec / local_speak are added in
sub-step 1g, once the kill switch (1f) and Allowed Folders (1e) are wired up
end-to-end and proven safe.

Config (env vars, or a `.env` file next to this script):
  FRANK_RELAY_URL      e.g. wss://onbrandcraftz-hub.up.railway.app/ws/relay
                        (use ws:// for a local server, e.g. ws://localhost:8000/ws/relay)
  APP_SECRET_TOKEN      same token the mobile app / dashboard uses

Run:
  pip install websockets
  python tools/relay/frank_relay.py
"""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import asyncio

try:
    import websockets
except ImportError:
    print("Missing dependency: pip install websockets", file=sys.stderr)
    raise

# ── Config ───────────────────────────────────────────────────────────────────

_HERE = Path(__file__).resolve().parent
_env_file = _HERE / ".env"
if _env_file.exists():
    for _line in _env_file.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

RELAY_URL = os.getenv("FRANK_RELAY_URL", "ws://localhost:8000/ws/relay").strip()
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "").strip()
# The relay calls back to the same host over plain HTTP(S) for small REST
# lookups (Allowed Folders) — derived from the ws(s):// relay URL.
_API_BASE = RELAY_URL.replace("wss://", "https://").replace("ws://", "http://").rsplit("/ws/relay", 1)[0]

RECONNECT_BACKOFF_SECS = 5
HEARTBEAT_INTERVAL_SECS = 20
ALLOWED_FOLDERS_REFRESH_SECS = 30
MAX_READ_BYTES = 200_000  # cap what a single local_read_file can return

# ── Local state ──────────────────────────────────────────────────────────────

_killed = False  # set by a server "kill_switch" message; blocks everything, reads included
_allowed_roots: list[str] = []
_allowed_roots_fetched_at = 0.0


def _api_get(path: str) -> dict | None:
    req = urllib.request.Request(
        _API_BASE + path, headers={"Authorization": f"Bearer {APP_TOKEN}"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"[relay] allowed-folders fetch failed: {exc}", flush=True)
        return None


def _refresh_allowed_roots(force: bool = False) -> None:
    """Pull the current Allowed Folders list from the server. Refreshed on a
    timer (not just at startup) so folder changes take effect without
    restarting the relay process."""
    global _allowed_roots, _allowed_roots_fetched_at
    now = time.time()
    if not force and (now - _allowed_roots_fetched_at) < ALLOWED_FOLDERS_REFRESH_SECS:
        return
    data = _api_get("/api/relay/allowed-folders")
    if data is not None:
        _allowed_roots = [f["path"] for f in data.get("folders", [])]
        _allowed_roots_fetched_at = now
        for root in _allowed_roots:
            try:
                os.makedirs(root, exist_ok=True)
            except OSError as exc:
                print(f"[relay] could not create allowed folder {root}: {exc}", flush=True)


def _resolve_real(path: str) -> str:
    return os.path.realpath(os.path.abspath(os.path.expanduser(path)))


def _is_allowed(path: str) -> bool:
    """The real security boundary (the server's db.is_path_allowed is a
    best-effort UX check only — it can't see Scott's actual filesystem).
    realpath collapses both `../` traversal and symlink indirection before
    the allow-list comparison runs, so neither can escape an allowed root."""
    _refresh_allowed_roots()
    if not path:
        return False
    real = _resolve_real(path)
    for root in _allowed_roots:
        root_real = _resolve_real(root)
        if real == root_real or real.startswith(root_real + os.sep):
            return True
    return False


# ── Tool handlers (Step 1: read-only) ────────────────────────────────────────


def _handle_local_read_file(tool_input: dict) -> dict:
    path = (tool_input or {}).get("path", "")
    if not _is_allowed(path):
        return {"error": f"path not in an Allowed Folder: {path}"}
    real = _resolve_real(path)
    if not os.path.isfile(real):
        return {"error": f"not a file: {path}"}
    size = os.path.getsize(real)
    with open(real, "rb") as f:
        data = f.read(MAX_READ_BYTES)
    truncated = size > MAX_READ_BYTES
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return {"error": "file is not valid UTF-8 text (binary files are not supported in Step 1)"}
    return {"path": real, "size": size, "truncated": truncated, "content": text}


def _handle_local_list_dir(tool_input: dict) -> dict:
    path = (tool_input or {}).get("path", "")
    if not _is_allowed(path):
        return {"error": f"path not in an Allowed Folder: {path}"}
    real = _resolve_real(path)
    if not os.path.isdir(real):
        return {"error": f"not a directory: {path}"}
    entries = []
    with os.scandir(real) as it:
        for entry in it:
            try:
                stat = entry.stat()
                entries.append(
                    {
                        "name": entry.name,
                        "is_dir": entry.is_dir(),
                        "size": stat.st_size if not entry.is_dir() else None,
                    }
                )
            except OSError:
                continue
    return {"path": real, "entries": entries}


# ── Tool handlers (sub-step 1g: staged mutating tools) ───────────────────────
#
# These only ever run after Scott has approved the action in the Action Center
# — the server's _execute_local_staged_action is the only thing that sends
# these tool_requests. The server already ran its own (best-effort) checks at
# staging time; the realpath-based _is_allowed() check below is the REAL
# security boundary, since only the relay has Scott's actual filesystem to
# resolve against. Independently re-validated here, not trusted from the server.

# Step 1 scope, Scott's locked-in decision: read-only diagnostics only. This is
# a separate, hardcoded copy of the whitelist the server keeps in
# _LOCAL_EXEC_COMMANDS — the relay does not trust the server's copy, it
# re-checks against its own. No subprocess/shell involved for either command,
# so there is no shell-injection surface to whitelist flags against.
_LOCAL_EXEC_WHITELIST = {"dir_listing", "disk_usage"}


def _handle_local_write_file(tool_input: dict) -> dict:
    path = (tool_input or {}).get("path", "")
    content = (tool_input or {}).get("content")
    if not _is_allowed(path):
        return {"error": f"path not in an Allowed Folder: {path}"}
    if content is None:
        return {"error": "content is required"}
    real = _resolve_real(path)
    try:
        os.makedirs(os.path.dirname(real), exist_ok=True)
        with open(real, "w", encoding="utf-8") as f:
            f.write(content)
    except OSError as exc:
        return {"error": str(exc)}
    return {"path": real, "bytes_written": len(content.encode("utf-8"))}


def _handle_local_delete(tool_input: dict) -> dict:
    path = (tool_input or {}).get("path", "")
    if not _is_allowed(path):
        return {"error": f"path not in an Allowed Folder: {path}"}
    real = _resolve_real(path)
    if not os.path.isfile(real):
        return {"error": f"not a file: {path}"}
    try:
        os.remove(real)
    except OSError as exc:
        return {"error": str(exc)}
    return {"path": real, "deleted": True}


def _handle_local_exec(tool_input: dict) -> dict:
    command = (tool_input or {}).get("command", "")
    extra_args = ((tool_input or {}).get("extra_args") or "").strip()
    if command not in _LOCAL_EXEC_WHITELIST:
        return {"error": f"command not in the relay's whitelist: {command}"}
    if command == "dir_listing":
        path = extra_args or (_allowed_roots[0] if _allowed_roots else "")
        if not _is_allowed(path):
            return {"error": f"path not in an Allowed Folder: {path}"}
        real = _resolve_real(path)
        try:
            entries = sorted(os.listdir(real))
        except OSError as exc:
            return {"error": str(exc)}
        out = "\n".join(entries)
        return {"command": command, "path": real, "output": out[:2000]}
    if command == "disk_usage":
        target = extra_args or (_allowed_roots[0] if _allowed_roots else os.path.abspath(os.sep))
        if extra_args and not _is_allowed(target):
            return {"error": f"path not in an Allowed Folder: {target}"}
        real = _resolve_real(target)
        try:
            usage = shutil.disk_usage(real)
        except OSError as exc:
            return {"error": str(exc)}
        gb = 1_000_000_000
        return {
            "command": command,
            "path": real,
            "total_gb": round(usage.total / gb, 2),
            "used_gb": round(usage.used / gb, 2),
            "free_gb": round(usage.free / gb, 2),
        }
    return {"error": f"no handler implemented for whitelisted command: {command}"}


_TOOL_HANDLERS = {
    "local_read_file": _handle_local_read_file,
    "local_list_dir": _handle_local_list_dir,
    "local_write_file": _handle_local_write_file,
    "local_delete": _handle_local_delete,
    "local_exec": _handle_local_exec,
}


async def _handle_tool_request(ws, msg: dict) -> None:
    """Always sends back *some* tool_result — mirrors the server's own
    'never leave a tool_use without a tool_result' discipline, one hop out."""
    req_id = msg.get("id")
    tool_name = msg.get("tool")
    tool_input = msg.get("input") or {}
    if _killed:
        await ws.send(json.dumps({
            "type": "tool_result", "id": req_id, "ok": False,
            "error": "kill switch is engaged on the relay — local actions are suspended",
        }))
        return
    handler = _TOOL_HANDLERS.get(tool_name)
    if handler is None:
        await ws.send(json.dumps({
            "type": "tool_result", "id": req_id, "ok": False,
            "error": f"relay does not yet implement tool: {tool_name}",
        }))
        return
    try:
        result = await asyncio.to_thread(handler, tool_input)
    except Exception as exc:
        await ws.send(json.dumps({
            "type": "tool_result", "id": req_id, "ok": False, "error": str(exc),
        }))
        return
    ok = "error" not in result
    await ws.send(json.dumps({"type": "tool_result", "id": req_id, "ok": ok, "result": result, "error": result.get("error")}))


async def _receive_loop(ws) -> None:
    global _killed
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            continue
        mtype = msg.get("type")
        if mtype == "tool_request":
            await _handle_tool_request(ws, msg)
        elif mtype == "kill_switch":
            _killed = bool(msg.get("active"))
            print(f"[relay] kill switch {'ENGAGED' if _killed else 'released'} by server", flush=True)


async def _heartbeat_loop(ws) -> None:
    while True:
        await asyncio.sleep(HEARTBEAT_INTERVAL_SECS)
        cpu, ram_pct = _read_system_stats()
        try:
            await ws.send(json.dumps({"type": "heartbeat", "cpu": cpu, "ram_pct": ram_pct}))
        except websockets.ConnectionClosed:
            return


def _read_system_stats() -> tuple[float | None, float | None]:
    """Best-effort CPU/RAM read. psutil is optional — falls back to None,None
    if it isn't installed, since the heartbeat itself (proving the relay is
    alive) matters more than the stats payload in Step 1."""
    try:
        import psutil  # type: ignore

        return psutil.cpu_percent(interval=None), psutil.virtual_memory().percent
    except ImportError:
        return None, None


async def _run_once() -> None:
    _refresh_allowed_roots(force=True)
    # Unlike a browser/RN client, this is a plain Python websockets client, so it
    # can set a real Authorization header on the handshake instead of putting the
    # long-lived APP_TOKEN in the URL (where it'd land in server access logs).
    headers = {"Authorization": f"Bearer {APP_TOKEN}"}
    async with websockets.connect(RELAY_URL, additional_headers=headers, ping_interval=20, ping_timeout=20) as ws:
        print(f"[relay] connected to {RELAY_URL}", flush=True)
        await asyncio.gather(_receive_loop(ws), _heartbeat_loop(ws))


async def main() -> None:
    if not APP_TOKEN:
        print("FRANK_RELAY_URL / APP_SECRET_TOKEN not set — see this file's docstring.", file=sys.stderr)
        sys.exit(1)
    while True:
        try:
            await _run_once()
        except (websockets.ConnectionClosed, OSError) as exc:
            print(f"[relay] disconnected ({exc}) — retrying in {RECONNECT_BACKOFF_SECS}s", flush=True)
        except Exception as exc:  # never let an unexpected error kill the reconnect loop
            print(f"[relay] error ({exc}) — retrying in {RECONNECT_BACKOFF_SECS}s", flush=True)
        await asyncio.sleep(RECONNECT_BACKOFF_SECS)


if __name__ == "__main__":
    asyncio.run(main())
