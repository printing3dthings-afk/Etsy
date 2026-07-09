#!/usr/bin/env python3
"""
Re-upload fixed lifestyle scene images to their Etsy listings.
Replaces the specific image rank that was regenerated.
"""
import os, sys, json, urllib.request, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
shop_id = client.shop_id
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}


def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


def get_image_ranks(listing_id):
    url = f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images"
    req = urllib.request.Request(url, headers=auth_headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            imgs = json.loads(resp.read()).get('results', [])
            return {img['rank']: img['listing_image_id'] for img in imgs}
    except Exception as e:
        print(f"  Could not get existing images: {e}")
        return {}


def upload_image(listing_id, img_path, rank):
    existing = get_image_ranks(listing_id)

    if rank in existing:
        url_del = (f"https://openapi.etsy.com/v3/application/shops/{shop_id}"
                   f"/listings/{listing_id}/images/{existing[rank]}")
        try:
            urllib.request.urlopen(
                urllib.request.Request(url_del, headers=auth_headers, method="DELETE"),
                timeout=15)
            print(f"  Deleted old image at rank={rank}")
            time.sleep(0.5)
        except Exception as e:
            print(f"  Could not delete old image: {e}")

    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, img_path, rank=rank)
            print(f"  Uploaded rank={rank}: {os.path.basename(img_path)}")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            elif e.status == 500 and attempt < 2:
                time.sleep(5)
            else:
                print(f"  Upload failed (rank={rank}): {e}")
                return False
    return False


# Fixed images to re-upload
# Format: (pid, listing_id, scene_letter, rank_to_replace)
FIXES = [
    ('DP1051', 4512772452, 'B', 2),
    ('DP1053', 4512774863, 'A', 1),
    ('DP1055', 4512780614, 'B', 2),
    ('DP1056', 4512780869, 'B', 2),
]


def main():
    results = []
    for pid, listing_id, scene, rank in FIXES:
        img_path = os.path.join(ART_DIR, f'{pid}_listing_images', f'lifestyle_scene_{scene}.jpg')
        if not os.path.exists(img_path):
            print(f"\n  MISSING: {img_path}")
            results.append((pid, scene, False))
            continue

        print(f"\n{'='*50}")
        print(f"Re-uploading {pid} Scene {scene} → rank={rank} on listing {listing_id}")
        print(f"{'='*50}")

        ok = upload_image(listing_id, img_path, rank)
        results.append((pid, scene, ok))
        time.sleep(1)

    print(f"\n{'='*50}")
    print("RE-UPLOAD COMPLETE")
    print(f"{'='*50}")
    for pid, scene, ok in results:
        status = "✓" if ok else "✗ FAILED"
        print(f"  {status} {pid} Scene {scene}")


if __name__ == '__main__':
    main()
