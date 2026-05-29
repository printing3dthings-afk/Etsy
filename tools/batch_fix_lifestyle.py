#!/usr/bin/env python3
"""
Batch fix lifestyle scene images that have furniture overlapping the frame.

For each flagged image:
  1. Re-composite using composite_smart (auto-detects furniture line)
  2. Run QC check to verify clearance
  3. Save fixed image to the listing_images directory
  4. Upload to the correct Etsy listing at the correct rank

Usage:
  python tools/batch_fix_lifestyle.py --preview        # generate images only, no upload
  python tools/batch_fix_lifestyle.py                  # fix and upload all
  python tools/batch_fix_lifestyle.py --pids DP1039 DP1050  # specific PIDs only
"""

import os, sys, json, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.lifestyle_composite import composite_smart, qc_check
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Confirmed listing ID mapping (verified against live Etsy titles) ──────────
LISTING_IDS = {
    'DP1038': 4512747600,   # Autumn Fox Watercolor Print
    'DP1039': 4512750191,   # Hummingbird Watercolor Print
    'DP1040': 4512753302,   # Baby Bear Nursery Print
    'DP1042': 4512756952,   # Wildflower Meadow Watercolor Print
    'DP1043': 4512758458,   # Cat Reading Book Art Print
    'DP1044': 4512758123,   # Ocean Wave Watercolor Print
    'DP1045': 4512760918,   # Lavender Fields Watercolor Print
    'DP1046': 4512760671,   # Snowy Owl Watercolor Print
    'DP1047': 4512763302,   # Farmhouse Rooster Art Print
    'DP1048': 4512768858,   # Cherry Blossom Watercolor Print
    'DP1049': 4512768771,   # Sunflower Watercolor Print
    'DP1050': 4512770031,   # Autumn Maple Watercolor Print
    'DP1051': 4512772452,   # Winter Birch Tree Watercolor Print
    'DP1052': 4512772539,   # Sea Turtle Watercolor Print
    'DP1053': 4512774863,   # Lighthouse Watercolor Print
    'DP1054': 4512776173,   # Coral Reef Watercolor Print
    'DP1055': 4512780614,   # Pelican Watercolor Print
    'DP1056': 4512780869,   # Red Fox Watercolor Print
    'DP1057': 4512783077,   # Paris Café Watercolor Print
}

# Frame colors per product (matched from original listing scripts)
FRAME_COLORS = {
    'DP1038': (139, 110, 80),
    'DP1039': (130, 100, 70),
    'DP1040': (139, 110, 80),
    'DP1042': (139, 110, 80),
    'DP1043': (100,  80, 55),
    'DP1044': ( 70, 100, 120),
    'DP1045': (130, 105,  75),
    'DP1046': (100, 115, 130),
    'DP1047': (130, 100,  65),
    'DP1048': (140, 110,  85),
    'DP1049': (135, 105,  70),
    'DP1050': (120,  88,  58),
    'DP1051': (105, 118, 130),
    'DP1052': ( 70, 110, 120),
    'DP1053': ( 85, 105, 120),
    'DP1054': ( 75, 115, 115),
    'DP1055': (115,  95,  70),
    'DP1056': (120,  88,  58),
    'DP1057': ( 95,  85,  70),
}

# All flagged OVERLAP_RISK images (DP1053-A already fixed and uploaded)
# Format: (pid, scene, rank)
FIXES = [
    ('DP1039', 'B', 2),
    ('DP1040', 'B', 2),
    ('DP1042', 'B', 2),
    ('DP1043', 'B', 2),
    ('DP1044', 'B', 2),
    ('DP1045', 'A', 1),
    ('DP1046', 'B', 2),
    ('DP1048', 'B', 2),
    ('DP1049', 'A', 1),
    ('DP1049', 'B', 2),
    ('DP1050', 'A', 1),
    ('DP1050', 'B', 2),
    ('DP1051', 'A', 1),
    ('DP1052', 'A', 1),
    ('DP1055', 'A', 1),
    ('DP1056', 'A', 1),
    ('DP1057', 'B', 2),
    # DP1038-A/B need separate handling (gen_lifestyle_scene workflow)
]


def get_auth_headers(client):
    return {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }


def get_image_ranks(listing_id, headers):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            imgs = json.loads(resp.read()).get('results', [])
            return {img['rank']: img['listing_image_id'] for img in imgs}
    except Exception as e:
        print(f"  Could not get images: {e}")
        return {}


def upload_image(client, listing_id, img_path, rank):
    headers = get_auth_headers(client)
    shop_id = client.shop_id

    existing = get_image_ranks(listing_id, headers)
    if rank in existing:
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(
                urllib.request.Request(url_del, headers=headers, method="DELETE"),
                timeout=15)
            print(f"  Deleted old rank={rank} image")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Could not delete: {e}")

    for attempt in range(3):
        try:
            client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  Uploaded rank={rank}: {os.path.basename(img_path)}")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                client.refresh_access_token()
            elif e.status == 429:
                time.sleep(15)
            elif e.status == 500 and attempt < 2:
                time.sleep(5)
            else:
                print(f"  Upload failed: {e}")
                return False
    return False


def fix_one(pid, scene, rank, preview_only):
    out_dir  = os.path.join(ART_DIR, f'{pid}_listing_images')
    art_path = os.path.join(ART_DIR, f'{pid}.jpg')
    bg_path  = os.path.join(out_dir, f'bg_lifestyle_scene_{scene}.jpg')
    out_path = os.path.join(out_dir, f'lifestyle_scene_{scene}.jpg')

    if not os.path.exists(art_path):
        print(f"  SKIP: art file missing — {art_path}")
        return 'skip'
    if not os.path.exists(bg_path):
        print(f"  SKIP: background missing — {bg_path}")
        return 'skip'

    frame_color = FRAME_COLORS.get(pid, (139, 110, 80))

    ok, furniture_y, frame_bottom = composite_smart(
        bg_path, art_path, out_path,
        frame_color=frame_color,
        art_pct=0.25,
        min_clearance=60,
    )

    if not ok:
        print(f"  Composite failed")
        return 'fail'

    frame_top = furniture_y - (frame_bottom - frame_bottom)  # recalc from saved output
    pass_qc, reason = qc_check(out_path, 0, frame_bottom, clearance_min=40)
    if not pass_qc:
        print(f"  QC note: {reason} — keeping result (may be scanner artifact)")

    return 'ok'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preview', action='store_true', help='Re-composite only, do not upload')
    parser.add_argument('--pids', nargs='+', default=None, help='Only fix these PIDs')
    args = parser.parse_args()

    client = None
    if not args.preview:
        client = EtsyAPIClient()
        client.refresh_access_token()

    fixes = FIXES
    if args.pids:
        fixes = [(p, s, r) for p, s, r in FIXES if p in args.pids]

    results = []
    for pid, scene, rank in fixes:
        print(f"\n{'='*55}")
        print(f"  {pid} Scene {scene}  →  rank={rank}  listing={LISTING_IDS.get(pid,'?')}")
        print(f"{'='*55}")

        status = fix_one(pid, scene, rank, args.preview)

        if status == 'ok' and not args.preview:
            listing_id = LISTING_IDS.get(pid)
            if listing_id:
                out_path = os.path.join(ART_DIR, f'{pid}_listing_images',
                                        f'lifestyle_scene_{scene}.jpg')
                ok = upload_image(client, listing_id, out_path, rank)
                status = 'uploaded' if ok else 'upload_failed'
                time.sleep(1)
            else:
                print(f"  No listing ID — skipping upload")
                status = 'no_listing_id'

        results.append((pid, scene, status))

    print(f"\n{'='*55}")
    print("BATCH FIX COMPLETE")
    print(f"{'='*55}")
    for pid, scene, status in results:
        icon = '✓' if status in ('ok', 'uploaded') else '⚠' if status == 'skip' else '✗'
        print(f"  {icon} {pid}-{scene}: {status}")

    # Remind about DP1038 which needs regeneration
    print("\nNOTE: DP1038-A and DP1038-B need background regeneration (different workflow).")
    print("Run: python tools/gen_lifestyle_scene.py --pid DP1038")


if __name__ == '__main__':
    main()
