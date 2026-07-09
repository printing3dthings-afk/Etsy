#!/usr/bin/env python3
"""Sync local product files up to the hosted dashboard's durable /data volume.

Why this exists: the phone Files area (Hub → Files) reads files off the server, but
the actual product files (PDFs, sticker ZIPs, SVG packs) live on Scott's machine in
data/digital_products/ — that directory is gitignored and Railway's filesystem is
ephemeral, so nothing ever appears there on its own. This tool walks the local
data/digital_products/ tree and POSTs every file to the server's /api/files/upload
endpoint, which stores them under the persistent /data/files volume. Once synced they
survive redeploys and open (incl. straight out of a ZIP, no unzip) from the phone.

One command:
    python tools/sync_files_to_hub.py            # sync everything new/changed
    python tools/sync_files_to_hub.py --dry-run  # show what WOULD upload, send nothing
    python tools/sync_files_to_hub.py --all       # re-upload everything (ignore skip)

Requires (in .env or the environment):
    RAILWAY_APP_URL   base URL of the live dashboard, e.g. https://onbrandcraftz.up.railway.app
    APP_SECRET_TOKEN  the same bearer token the dashboard uses (set on the Railway service)

It only uploads — it never deletes anything on the server. Files already present with
the same size are skipped, so re-running is cheap and safe (big PDFs aren't re-sent).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Guarded: only Scott's local checkout has a .env; never crash if it's absent.
_env_path = ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

SRC_DIR = ROOT / "data" / "digital_products"
MAX_UPLOAD_BYTES = 30 * 1024 * 1024  # mirrors the server cap


def _human(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def _fetch_existing(base_url: str, token: str) -> dict[str, int]:
    """Return {relative_path: size} for files already in the server's /data volume."""
    req = urllib.request.Request(
        base_url.rstrip("/") + "/api/files",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    out: dict[str, int] = {}
    for group in data.get("groups", []):
        if group.get("root") != "volume":
            continue
        for f in group.get("files", []):
            out[f["path"]] = f.get("size", -1)
    return out


def _upload(base_url: str, token: str, rel: str, content: bytes) -> None:
    url = base_url.rstrip("/") + "/api/files/upload?path=" + urllib.parse.quote(rel)
    req = urllib.request.Request(
        url,
        data=content,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        resp.read()


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync local product files to the hosted dashboard volume")
    parser.add_argument("--dry-run", action="store_true", help="Show what would upload without sending anything")
    parser.add_argument("--all", action="store_true", help="Re-upload every file even if already present")
    args = parser.parse_args()

    base_url = os.environ.get("RAILWAY_APP_URL", "").strip()
    token = os.environ.get("APP_SECRET_TOKEN", "").strip()
    if not base_url or not token:
        print(
            "ERROR: RAILWAY_APP_URL and/or APP_SECRET_TOKEN are not set.\n"
            "  Add both to your .env (or environment):\n"
            "    RAILWAY_APP_URL=https://<your-app>.up.railway.app\n"
            "    APP_SECRET_TOKEN=<same token set on the Railway service>",
            file=sys.stderr,
        )
        return 1

    if not SRC_DIR.is_dir():
        print(f"ERROR: {SRC_DIR} does not exist — nothing to sync. Run this on the machine "
              f"where the product files were generated.", file=sys.stderr)
        return 1

    local_files = [p for p in sorted(SRC_DIR.rglob("*")) if p.is_file()]
    if not local_files:
        print(f"No files found under {SRC_DIR}.")
        return 0

    try:
        existing = {} if args.all else _fetch_existing(base_url, token)
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:200]
        print(f"ERROR: could not read server file list ({e.code}): {body}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: could not reach {base_url}: {e}", file=sys.stderr)
        return 1

    uploaded = skipped = failed = 0
    total_bytes = 0
    for p in local_files:
        rel = str(p.relative_to(SRC_DIR)).replace(os.sep, "/")
        size = p.stat().st_size
        # Empty files are git placeholders (.gitkeep) or stubs — nothing to open on a
        # phone, and the server rejects empty bodies. Skip quietly, don't count failed.
        if size == 0 or p.name == ".gitkeep":
            skipped += 1
            continue
        if size > MAX_UPLOAD_BYTES:
            print(f"  SKIP (too big, {_human(size)} > {_human(MAX_UPLOAD_BYTES)}): {rel}")
            skipped += 1
            continue
        if not args.all and existing.get(rel) == size:
            skipped += 1
            continue
        if args.dry_run:
            print(f"  would upload ({_human(size)}): {rel}")
            uploaded += 1
            total_bytes += size
            continue
        try:
            _upload(base_url, token, rel, p.read_bytes())
            print(f"  ✓ {rel} ({_human(size)})")
            uploaded += 1
            total_bytes += size
        except urllib.error.HTTPError as e:
            body = e.read().decode()[:200]
            print(f"  ✗ {rel}: HTTP {e.code} {body}", file=sys.stderr)
            failed += 1
        except Exception as e:
            print(f"  ✗ {rel}: {e}", file=sys.stderr)
            failed += 1

    verb = "Would upload" if args.dry_run else "Uploaded"
    print(f"\n{verb} {uploaded} file(s) ({_human(total_bytes)}), skipped {skipped} "
          f"(already up-to-date, empty, or oversized), {failed} failed.")
    if not args.dry_run and uploaded and not failed:
        print("Done — open Hub → Files on the phone to see them.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
