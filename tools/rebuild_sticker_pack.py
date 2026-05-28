#!/usr/bin/env python3
"""
Rebuild sticker pack ZIP for a planner with all approved sheets,
replace the digital file on Etsy, and update the listing description.

Usage:
  python tools/rebuild_sticker_pack.py --pid DP1026 --sheets 11 --listing 4509179201
"""
import os, sys, json, zipfile, urllib.request, urllib.error, time, argparse, re
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

SHEET_NAMES_BASE = {
    1: 'sheet_01_functional_planning',
    2: 'sheet_02_widget_trackers',
    3: 'sheet_03_planner_stationery',
    4: 'sheet_04_cozy_lifestyle',
    5: 'sheet_05_seasonal_holiday',
}

SHEET_NAMES_BY_PID = {
    'DP1026': {
        6:  'sheet_06_self_care_wellness',
        7:  'sheet_07_affirmations_milestones',
        8:  'sheet_08_moon_celestial',
        9:  'sheet_09_plants_botanical',
        10: 'sheet_10_sweet_treats',
        11: 'sheet_11_cozy_home',
    },
    'DP1027': {
        6:  'sheet_06_school_supplies',
        7:  'sheet_07_subject_icons',
        8:  'sheet_08_campus_life',
        9:  'sheet_09_study_motivation',
        10: 'sheet_10_back_to_school',
        11: 'sheet_11_academic_achievement',
    },
    'DP1028': {
        6:  'sheet_06_money_finance',
        7:  'sheet_07_savings_goals',
        8:  'sheet_08_debt_payoff',
        9:  'sheet_09_budget_categories',
        10: 'sheet_10_financial_wins',
        11: 'sheet_11_smart_shopping',
    },
    'DP1029': {
        6:  'sheet_06_workout_exercise',
        7:  'sheet_07_healthy_food',
        8:  'sheet_08_wellness_self_care',
        9:  'sheet_09_progress_tracking',
        10: 'sheet_10_sports_activities',
        11: 'sheet_11_fitness_wins',
    },
}

def get_sheet_name(pid, n):
    if n <= 5:
        return SHEET_NAMES_BASE.get(n, f'sheet_{n:02d}')
    pid_names = SHEET_NAMES_BY_PID.get(pid, {})
    return pid_names.get(n, f'sheet_{n:02d}')

HOW_TO = """HOW TO USE YOUR STICKERS
========================

GoodNotes 6 (recommended):
1. Download and unzip this sticker pack
2. Open GoodNotes 6 → tap Elements (diamond icon) → Stickers tab → tap +
3. Select all sticker sheet files → tap Done
4. All stickers appear in your library — drag any sticker onto any page!

Notability:
- Use Photo Stickers → insert each PNG/JPG sheet as a photo
- Crop individual stickers from the sheet as needed

PDF Expert / Xodo / Adobe Acrobat:
- Insert sticker sheets as image annotations, then crop and resize

Printing:
- All sheets are print-ready. Print on sticker paper for physical use.

© OnBrandCraftz · Personal use only · Not for resale or redistribution
"""


def rebuild_zip(pid, num_sheets):
    zip_path = os.path.join(ART_DIR, f'{pid}_sticker_pack.zip')
    print(f"\nRebuilding {zip_path} with {num_sheets} sheets...")

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('HOW_TO_USE_STICKERS.txt', HOW_TO)

        for n in range(1, num_sheets + 1):
            sheet_name = get_sheet_name(pid, n)
            # Try JPG first (newer sheets), then PNG (original sheets)
            for ext, arcext in [('.jpg', 'jpg'), ('.png', 'png')]:
                src = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{n}{ext}')
                if os.path.exists(src):
                    arcname = f'{sheet_name}.{arcext}'
                    zf.write(src, arcname)
                    size = os.path.getsize(src) // 1024
                    print(f"  Added: {arcname} ({size}KB)")
                    break
            else:
                print(f"  WARNING: Sheet {n} not found for {pid}")

    zip_size = os.path.getsize(zip_path) // 1024
    print(f"  ZIP rebuilt: {zip_size}KB total")
    return zip_path


def refresh():
    client.refresh_access_token()
    auth_headers["Authorization"] = f"Bearer {client.access_token}"


def replace_digital_file(listing_id, zip_path):
    print(f"\nReplacing digital file on listing {listing_id}...")

    # Get existing files
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        existing = json.loads(resp.read()).get('results', [])

    # Delete old ZIP files
    for f in existing:
        if f['filename'].endswith('.zip') and f['filename'].startswith(os.path.basename(zip_path).split('_sticker')[0]):
            fid = f['listing_file_id']
            del_req = urllib.request.Request(
                f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files/{fid}",
                headers=auth_headers, method="DELETE")
            try:
                urllib.request.urlopen(del_req, timeout=15)
                print(f"  Deleted old file: {f['filename']}")
                time.sleep(0.5)
            except Exception as e:
                print(f"  Could not delete {f['filename']}: {e}")

    # Upload new ZIP
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, zip_path, rank=1)
            print(f"  Uploaded: {os.path.basename(zip_path)} (file_id={result.get('listing_file_id')})")
            return True
        except EtsyAPIError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: print(f"  Upload failed: {e}"); return False
    return False


def patch_listing(lid, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{lid}",
        data=data,
        headers={**auth_headers, "Content-Type": "application/json"},
        method="PATCH")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.status == 401: refresh()
            elif e.status == 429: time.sleep(15)
            else: raise
    raise RuntimeError(f"Failed to patch listing {lid}")


def update_description(listing_id, num_sheets, sticker_count_str):
    print(f"\nUpdating description for listing {listing_id}...")
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{listing_id}",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        l = json.loads(resp.read())
    desc = l['description']

    # Update sheet count
    desc = re.sub(r'\d+ PNG sticker sheets', f'{num_sheets} illustrated sticker sheets', desc)
    desc = re.sub(r'\d+ sticker sheets', f'{num_sheets} illustrated sticker sheets', desc)
    # Update sticker count
    desc = re.sub(r'\d+\+ stickers,', f'{sticker_count_str} stickers,', desc)
    desc = re.sub(r'\d+\+ stickers\b', sticker_count_str + ' stickers', desc)
    # Update import instructions
    desc = re.sub(r'import the \d+ PNG files', f'import all {num_sheets} sticker sheet files', desc)
    desc = re.sub(r'import the \d+ PNG', f'import all {num_sheets}', desc)

    patch_listing(listing_id, {"description": desc})
    print(f"  Description updated: {num_sheets} sheets, {sticker_count_str} stickers")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--pid', required=True)
    parser.add_argument('--sheets', type=int, required=True, help='Total number of sheets')
    parser.add_argument('--listing', type=int, required=True, help='Etsy listing ID')
    parser.add_argument('--count', default='200+', help='Sticker count string e.g. "200+"')
    args = parser.parse_args()

    zip_path = rebuild_zip(args.pid, args.sheets)
    replace_digital_file(args.listing, zip_path)
    update_description(args.listing, args.sheets, args.count)

    print(f"\n✓ {args.pid} sticker pack updated: {args.sheets} sheets, {args.count} stickers")
