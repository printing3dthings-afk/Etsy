"""
Backs up data/digital_products/ to a timestamped ZIP.

data/digital_products/ is intentionally gitignored (large machine-local binaries —
source art, PDFs, print-ready ZIPs for every product). That means it has no durable
backup: if the local sandbox is reset or cleaned up after files are uploaded to Etsy,
the originals are gone for good (this is what happened to DP1021's print-ready ZIP).

Run this periodically and hand the output ZIP to Scott to save in his own cloud
storage (Google Drive / OneDrive / Dropbox) — that's the actual durable copy.
"""
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

SOURCE_DIR = Path("data/digital_products")
BACKUP_DIR = Path("data/backups")


def main():
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
    return out_path


if __name__ == "__main__":
    main()
