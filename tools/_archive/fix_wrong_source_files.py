#!/usr/bin/env python3
"""
fix_wrong_source_files.py
Replaces digital download files on Etsy listings where the source art was saved
as a lifestyle composite instead of raw print-ready art.

Run AFTER generating correct print ZIPs for each affected DP code.
Usage:
    python tools/fix_wrong_source_files.py --preview   # show what will change
    python tools/fix_wrong_source_files.py              # apply
    python tools/fix_wrong_source_files.py --dp DP1062  # single DP code
"""
import argparse, json, sys, time
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))
from tools.etsy_api import EtsyAPIClient

# DP codes confirmed to have lifestyle composites as source art
# Map: dp_code -> listing_id(s) that need the fixed ZIP
AFFECTED = {
    'DP1062': [4509214477],  # Funny Dog (customer complaint received)
    'DP1059': [4509193237],  # Pampas Grass
    'DP1060': [4509198434],  # Boho Wildflower
    'DP1061': [4509198446],  # Eucalyptus Branch
    'DP1063': [4509258700],  # Orange Floral (shared with DP1013)
    'DP1064': [4509600086],  # Tropical Botanical (shared with DP1035)
    'DP1067': [4512768858],  # Cherry Blossom
    'DP1078': [4513713936],  # Hummingbird
}

ZIP_DIR = BASE_DIR / 'data' / 'digital_products' / 'print_zips'


def get_listing_files(api, lid):
    files = api._request("GET", f"shops/{api.shop_id}/listings/{lid}/files")
    return files.get('results', [])


def delete_listing_file(api, lid, file_id):
    api._request("DELETE", f"shops/{api.shop_id}/listings/{lid}/files/{file_id}")


def upload_listing_file(api, lid, zip_path):
    api.upload_listing_file(lid, zip_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--dp', type=str, help='Only fix this DP code (e.g. DP1062)')
    args = parser.parse_args()

    api = EtsyAPIClient()

    affected = {args.dp: AFFECTED[args.dp]} if args.dp else AFFECTED

    print(f"{'PREVIEW' if args.preview else 'APPLY'} mode — {len(affected)} DP codes\n")

    for dp_code, listing_ids in affected.items():
        zip_path = ZIP_DIR / f'{dp_code}_print_sizes.zip'
        if not zip_path.exists():
            print(f"  {dp_code}: ✗ ZIP not found at {zip_path} — SKIP (regenerate art first)")
            continue

        for lid in listing_ids:
            print(f"  {dp_code} → listing {lid}:")
            try:
                existing = get_listing_files(api, lid)
                if args.preview:
                    print(f"    Current files: {[f['filename'] for f in existing]}")
                    print(f"    Will upload: {zip_path.name} ({zip_path.stat().st_size/1024/1024:.1f}MB)")
                    continue

                # Delete old files
                for f in existing:
                    delete_listing_file(api, lid, f['listing_file_id'])
                    print(f"    Deleted: {f['filename']}")
                    time.sleep(0.5)

                # Upload correct ZIP
                upload_listing_file(api, lid, str(zip_path))
                print(f"    ✓ Uploaded: {zip_path.name}")
                time.sleep(1)

            except Exception as e:
                print(f"    ✗ Error: {e}")
            time.sleep(0.5)

    print("\nDone.")


if __name__ == '__main__':
    main()
