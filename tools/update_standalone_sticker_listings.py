#!/usr/bin/env python3
"""
Update standalone sticker pack listings with new per-planner 11-sheet ZIPs.
Also updates All 4 Planners Bundle description from 300+ to 800+ stickers.
"""
import os, sys, json, urllib.request, urllib.error, time
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

# Standalone listings: (name, listing_id, zip_file)
STANDALONE = [
    ('Lavender Pack',      4512255514, 'DP1026_sticker_pack.zip'),
    ('Cotton Candy Pack',  4512254015, 'DP1027_sticker_pack.zip'),
    ('Midnight Blue Pack', 4512255536, 'DP1028_sticker_pack.zip'),
    ('Coral Peach Pack',   4512254027, 'DP1029_sticker_pack.zip'),
]

# All 4 Packs Bundle gets all 4 ZIPs
BUNDLE_LISTING = 4512254035
BUNDLE_ZIPS = [
    'DP1026_sticker_pack.zip',
    'DP1027_sticker_pack.zip',
    'DP1028_sticker_pack.zip',
    'DP1029_sticker_pack.zip',
]

# All 4 Planners Bundle — description update only (800+ stickers now)
PLANNERS_BUNDLE_LISTING = 4512188970


def refresh():
    client.refresh_access_token()
    auth_headers["Authorization"] = f"Bearer {client.access_token}"


def get_existing_files(listing_id):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get('results', [])


def delete_file(listing_id, file_id, filename):
    del_req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files/{file_id}",
        headers=auth_headers, method="DELETE")
    try:
        urllib.request.urlopen(del_req, timeout=15)
        print(f"  Deleted: {filename}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Could not delete {filename}: {e}")


def upload_zip(listing_id, zip_filename, rank=1):
    zip_path = os.path.join(ART_DIR, zip_filename)
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, zip_path, rank=rank)
            print(f"  Uploaded: {zip_filename} (file_id={result.get('listing_file_id')})")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                print(f"  Upload failed ({e.status}): {e}")
                return False
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
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                raise
    raise RuntimeError(f"Failed to patch listing {lid}")


def get_listing(lid):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{lid}",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def update_standalone(name, listing_id, zip_filename):
    print(f"\n{'='*50}")
    print(f"Updating: {name} (listing {listing_id})")

    # Delete old ZIP files
    existing = get_existing_files(listing_id)
    for f in existing:
        if f['filename'].endswith('.zip'):
            delete_file(listing_id, f['listing_file_id'], f['filename'])

    # Upload new ZIP
    upload_zip(listing_id, zip_filename, rank=1)

    # Update description: sticker count and sheet count
    l = get_listing(listing_id)
    desc = l['description']
    import re
    desc = re.sub(r'\d+\+ stickers', '200+ stickers', desc)
    desc = re.sub(r'\d+ PNG sticker sheets', '11 illustrated sticker sheets', desc)
    desc = re.sub(r'\d+ sticker sheets', '11 illustrated sticker sheets', desc)
    patch_listing(listing_id, {"description": desc})
    print(f"  Description updated: 11 sheets, 200+ stickers")


def update_bundle(listing_id, zip_files):
    print(f"\n{'='*50}")
    print(f"Updating: All 4 Packs Bundle (listing {listing_id})")

    # Delete all old files
    existing = get_existing_files(listing_id)
    for f in existing:
        if f['filename'].endswith('.zip'):
            delete_file(listing_id, f['listing_file_id'], f['filename'])

    # Upload all 4 ZIPs
    for i, zip_filename in enumerate(zip_files, 1):
        upload_zip(listing_id, zip_filename, rank=i)
        time.sleep(0.5)

    # Update description
    l = get_listing(listing_id)
    desc = l['description']
    import re
    desc = re.sub(r'\d+\+ stickers', '800+ stickers', desc)
    desc = re.sub(r'\d+ PNG sticker sheets', '44 illustrated sticker sheets', desc)
    desc = re.sub(r'\d+ sticker sheets', '44 illustrated sticker sheets', desc)
    patch_listing(listing_id, {"description": desc})
    print(f"  Description updated: 44 sheets, 800+ stickers")


def update_planners_bundle_description(listing_id):
    print(f"\n{'='*50}")
    print(f"Updating planners bundle description (listing {listing_id})")
    l = get_listing(listing_id)
    desc = l['description']
    import re
    # Update bundle sticker claims
    desc = re.sub(r'300\+ stickers', '800+ stickers', desc)
    desc = re.sub(r'20 PNG sheets', '44 illustrated sticker sheets', desc)
    desc = re.sub(r'4 × Kawaii Sticker Packs — \d+\+ stickers total \(5 sheets × 4 planners\)',
                  '4 × Kawaii Sticker Packs — 800+ stickers total (11 sheets × 4 planners)', desc)
    patch_listing(listing_id, {"description": desc})
    print(f"  Bundle description updated to 800+ stickers")


if __name__ == '__main__':
    # Update standalone pack listings
    for name, lid, zip_file in STANDALONE:
        update_standalone(name, lid, zip_file)
        time.sleep(1)

    # Update All 4 Packs Bundle listing
    update_bundle(BUNDLE_LISTING, BUNDLE_ZIPS)

    # Update All 4 Planners Bundle description
    update_planners_bundle_description(PLANNERS_BUNDLE_LISTING)

    print(f"\n{'='*50}")
    print("DONE — all standalone sticker listings updated")
    print("  Per-pack listings: 11 sheets, 200+ stickers each")
    print("  All 4 Packs Bundle: 44 sheets, 800+ stickers total")
    print("  All 4 Planners Bundle description: 800+ stickers")
