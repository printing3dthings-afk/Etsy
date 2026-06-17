"""
Backs up data/digital_products/ to a timestamped ZIP, then (by default) syncs the
files up to the hosted dashboard's durable /data volume so they appear on the phone.

data/digital_products/ is intentionally gitignored (large machine-local binaries —
source art, PDFs, print-ready ZIPs for every product). That means it has no durable
backup: if the local sandbox is reset or cleaned up after files are uploaded to Etsy,
the originals are gone for good (this is what happened to DP1021's print-ready ZIP).

Run this whenever a new product's files are generated:
  python tools/backup_digital_products.py            # backup + sync to phone
  python tools/backup_digital_products.py --no-sync  # backup ZIP only

The backup ZIP is the durable cold copy (hand it to Scott for his own cloud storage).
The sync step is what makes the actual files browsable + openable on the phone Files
area (tools/sync_files_to_hub.py). Sync is best-effort: if RAILWAY_APP_URL /
APP_SECRET_TOKEN aren't configured, or the server is unreachable, the backup still
succeeds and we just print a note — a sync hiccup never fails the backup.
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

SOURCE_DIR = ROOT / "data" / "digital_products"
BACKUP_DIR = ROOT / "data" / "backups"


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


def main():
    parser = argparse.ArgumentParser(description="Back up digital_products/ and sync to the phone")
    parser.add_argument("--no-sync", action="store_true", help="Only make the backup ZIP; don't push to the phone")
    args = parser.parse_args()

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

    if not args.no_sync:
        _sync_to_hub()

    return out_path


if __name__ == "__main__":
    main()
