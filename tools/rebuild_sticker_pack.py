#!/usr/bin/env python3
"""
Rebuild Sticker Pack ZIP
=========================
Rebuilds the sticker pack ZIP for a planner product, then re-uploads the
digital file to Etsy. Wraps process_sticker_sheets.py + Etsy upload.

Usage:
  python tools/rebuild_sticker_pack.py --pid DP1026
  python tools/rebuild_sticker_pack.py --pid DP1027 --no-upload
  python tools/rebuild_sticker_pack.py --pid DP1028 --sheets 5
"""
import os, sys, argparse
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
_env_path = _ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


PLANNER_NAMES = {
    "DP1026": "Life Planner (Lavender)",
    "DP1027": "Student Planner (Cotton Candy)",
    "DP1028": "Budget Planner (Midnight Blue)",
    "DP1029": "Fitness Planner (Coral Peach)",
    "DP1030": "ADHD Planner",
    "DP1031": "Sage Garden Planner",
    "DP1032": "Midnight Kawaii Planner",
    "DP1033": "Sunflower Studio Planner",
    "DP1034": "Celestial Planner",
}


def rebuild(pid: str, max_sheets: int | None = None, upload: bool = True):
    pid = pid.strip().upper()
    name = PLANNER_NAMES.get(pid, pid)

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  Rebuild Sticker Pack — {pid}")
    print(f"  {name}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    # Step 1: Process sticker sheets (background removal + segmentation + ZIP)
    print("  [1/3] Processing sticker sheets...")
    from tools.process_sticker_sheets import process_pid, build_zip

    result = process_pid(pid, max_sheets=max_sheets, make_individual=True)
    if not result or not result.get("sheets"):
        print(f"\n  ✗ No sticker sheets found for {pid}")
        print(f"    Expected files: data/digital_products/product_files/{pid}_sticker_sheet_N.jpg")
        print(f"    Generate sheets first: python tools/gen_sticker_sheet.py --pid {pid}")
        sys.exit(1)

    # Step 2: Build ZIP
    print(f"\n  [2/3] Building sticker pack ZIP...")
    zip_path = build_zip(result)
    zip_size_mb = zip_path.stat().st_size / (1024 * 1024)

    print(f"\n  ✓ Pack rebuilt: {zip_path.name}")
    print(f"    Sheets:     {len(result['sheets'])}")
    print(f"    Stickers:   {result.get('sticker_count', 0)} individual")
    print(f"    ZIP size:   {zip_size_mb:.1f} MB")

    if zip_size_mb > 20:
        print(f"\n  ⚠ WARNING: ZIP exceeds Etsy's 20MB per-file limit!")
        print(f"    Re-run with fewer sheets or lower resolution")

    # Step 3: Upload to Etsy (optional)
    if upload:
        print(f"\n  [3/3] Uploading to Etsy...")
        _upload_to_etsy(pid, zip_path)
    else:
        print(f"\n  [3/3] Upload skipped (--no-upload)")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  ✓ Rebuild complete for {pid}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


def _upload_to_etsy(pid: str, zip_path: Path):
    """Upload the rebuilt ZIP as a digital file to the Etsy listing."""
    import json

    # Look up listing ID from dp_listing_map
    map_path = _ROOT / "data" / "dp_listing_map.json"
    if not map_path.exists():
        print(f"    ⚠ dp_listing_map.json not found — cannot auto-upload")
        print(f"    Upload manually: {zip_path}")
        return

    try:
        dp_map = json.loads(map_path.read_text())
    except Exception:
        print(f"    ⚠ Could not read dp_listing_map.json")
        return

    entry = dp_map.get(pid, {})
    listing_id = entry.get("listing_id") or entry.get("planner_listing_id")
    if not listing_id:
        print(f"    ⚠ No listing ID found for {pid} in dp_listing_map.json")
        print(f"    Upload manually: {zip_path}")
        return

    try:
        from tools.etsy_api import EtsyAPIClient
        client = EtsyAPIClient()
        if not client.refresh_access_token():
            print(f"    ⚠ Could not refresh OAuth token — upload manually")
            return

        client.upload_digital_file(listing_id, str(zip_path))
        print(f"    ✓ Uploaded to listing {listing_id}")
    except AttributeError:
        # upload_digital_file may not exist on all versions
        print(f"    ⚠ Digital file upload not available via API")
        print(f"    Upload manually to listing {listing_id}: {zip_path}")
    except Exception as e:
        print(f"    ✗ Upload failed: {e}")
        print(f"    Upload manually to listing {listing_id}: {zip_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Rebuild sticker pack ZIP and re-upload to Etsy")
    parser.add_argument('--pid', required=True,
                        help="Product ID (e.g. DP1026, DP1027, DP1028, DP1029)")
    parser.add_argument('--sheets', type=int, default=None,
                        help="Max number of sheets to process")
    parser.add_argument('--no-upload', action='store_true',
                        help="Skip uploading to Etsy")
    args = parser.parse_args()

    rebuild(args.pid, max_sheets=args.sheets, upload=not args.no_upload)


if __name__ == '__main__':
    main()
