"""
Backs up the digital_products tree to a timestamped ZIP, then (by default) syncs the
files up to the hosted dashboard's durable /data volume so they appear on the phone.

data/digital_products/ is intentionally gitignored (large machine-local binaries —
source art, PDFs, print-ready ZIPs for every product). That means it has no durable
backup: if the local sandbox is reset or cleaned up after files are uploaded to Etsy,
the originals are gone for good (this is what happened to DP1021's print-ready ZIP,
and again to DP1030-1034 — see ops_runbook.md 2026-07-15/16 — because this script was
only reachable via an approval-gated command, not called automatically).

Run this whenever a new product's files are generated:
  python tools/backup_digital_products.py            # backup + sync to phone
  python tools/backup_digital_products.py --no-sync  # backup ZIP only

As of 2026-07-17 this also runs AUTOMATICALLY at the end of build_product.py,
build_planner.py, and build_sticker_pack.py — see main() for the environment-aware
sync/no-sync choice.

The backup ZIP is the durable cold copy (hand it to Scott for his own cloud storage).
The sync step is what makes the actual files browsable + openable on the phone Files
area (tools/sync_files_to_hub.py). Sync is best-effort: if RAILWAY_APP_URL /
APP_SECRET_TOKEN aren't configured, or the server is unreachable, the backup still
succeeds and we just print a note — a sync hiccup never fails the backup.

Volume-aware (2026-07-17): SOURCE_DIR used to be hardcoded to the repo-relative
data/digital_products/ path, which only holds real files in a local sandbox checkout.
When the one-tap build pipelines run server-side (spawned by the live Railway
process), product files are written straight to the durable volume
(HUB_FILES_DIR / /data/files) via each builder's own resolve_dp_base()-style helper —
a plain ROOT-relative SOURCE_DIR would find nothing there and silently back up an
empty tree. This is the exact "works in sandbox, breaks in prod" bug class flagged
across qc_sweep.py/gen_planner_listing_photos.py/etc.; fixed the same way here.
"""
import argparse
import os
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Load .env (guarded — Railway has none) so the sync step can see RAILWAY_APP_URL /
# APP_SECRET_TOKEN without the caller having to export them first.
_env_path = ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())


def _resolve_dp_base() -> Path:
    """digital_products base — the durable Railway volume in production, the repo
    tree locally. Same resolution order as tools/build_sticker_pack.py /
    tools/process_sticker_sheets.py."""
    vol = os.getenv("HUB_FILES_DIR", "").strip()
    if vol and Path(vol).is_dir():
        return Path(vol)
    if Path("/data/files").is_dir():
        return Path("/data/files")
    return ROOT / "data" / "digital_products"


def running_on_volume() -> bool:
    """True when SOURCE_DIR resolved to the durable Railway volume rather than a
    local sandbox checkout — i.e. files are already durable by construction and the
    sync-to-hub step (a self-referential HTTP call in that case) would be a no-op."""
    return SOURCE_DIR != (ROOT / "data" / "digital_products")


SOURCE_DIR = _resolve_dp_base()
# Backups land inside the same durable location as their source when running against
# the volume, so the safety copy survives redeploys too; falls back to the existing
# repo-relative sandbox location otherwise (handed to Scott from chat, as before).
BACKUP_DIR = SOURCE_DIR.parent / "backups" if running_on_volume() else ROOT / "data" / "backups"


def _sync_to_hub() -> None:
    """Push the freshly-backed-up files to the durable volume so they show on the phone.

    Best-effort: skips cleanly if the dashboard URL/token aren't configured, and never
    raises (a sync problem must not undo a good backup)."""
    if not (os.environ.get("RAILWAY_APP_URL", "").strip() and os.environ.get("APP_SECRET_TOKEN", "").strip()):
        print(
            "Sync skipped: RAILWAY_APP_URL / APP_SECRET_TOKEN not set in .env, so files "
            "weren't pushed to the phone Files area. (Backup ZIP above is unaffected.)"
        )
        return
    print("\nSyncing files to the dashboard volume (phone Files area)…")
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools" / "sync_files_to_hub.py")],
            cwd=str(ROOT),
            timeout=1800,  # large product libraries can take a while on a slow uplink
        )
        if result.returncode != 0:
            print("Sync reported a problem (see output above) — backup ZIP is still good.")
    except Exception as exc:
        print(f"Sync could not run ({exc}) — backup ZIP is still good.")


def run(no_sync: bool = False) -> Path:
    """The actual backup+sync logic, callable programmatically (e.g. from the
    build pipelines' automatic post-build backup call) without touching sys.argv.
    Returns the backup ZIP path. Raises FileNotFoundError if SOURCE_DIR doesn't
    exist — callers that must never let a backup failure break a build (see
    build_product.py etc.) should catch around the call, not rely on this
    swallowing errors itself."""
    if not SOURCE_DIR.exists():
        raise FileNotFoundError(SOURCE_DIR)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = BACKUP_DIR / f"digital_products_backup_{stamp}.zip"

    files = [p for p in SOURCE_DIR.rglob("*") if p.is_file()]
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            zf.write(f, f.relative_to(SOURCE_DIR.parent))

    size_mb = out_path.stat().st_size / (1024 * 1024)
    print(f"Backed up {len(files)} files ({size_mb:.1f} MB) -> {out_path}")

    # Sync only makes sense from a local sandbox checkout pushing UP to the hub —
    # when SOURCE_DIR already IS the durable volume (server-side build), sync would
    # be a self-referential HTTP call finding everything already present. Automatic
    # callers running server-side should still pass no_sync=True explicitly (the
    # CLI default stays "sync unless told not to" for the sandbox use case).
    if not no_sync and not running_on_volume():
        _sync_to_hub()
    elif not no_sync and running_on_volume():
        print("Sync skipped: already running against the durable volume (files are already there).")

    return out_path


def main():
    parser = argparse.ArgumentParser(description="Back up digital_products/ and sync to the phone")
    parser.add_argument("--no-sync", action="store_true", help="Only make the backup ZIP; don't push to the phone")
    args = parser.parse_args()
    return run(no_sync=args.no_sync)


if __name__ == "__main__":
    main()
