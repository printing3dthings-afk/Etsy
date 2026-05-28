#!/usr/bin/env python3
"""
Upload photos and digital files to the All 4 Planners Bundle listing (4512188970).
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

LISTING_ID = 4512188970
BUNDLE_IMAGES_DIR = '/home/user/Etsy/data/digital_products/product_files/bundle_listing_images'
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

PHOTOS = [
    ('01_hero.jpg', 1),
    ('02_four_themes.jpg', 2),
    ('03_monthly_spreads.jpg', 3),
    ('04_weekly_spreads.jpg', 4),
    ('05_sticker_showcase.jpg', 5),
    ('06_savings.jpg', 6),
    ('07_app_compatibility.jpg', 7),
    ('08_whats_included.jpg', 8),
]

# Digital files to upload: 4 planner PDFs + 4 sticker ZIPs
DIGITAL_FILES = [
    ('DP1026.pdf', 1),
    ('DP1027.pdf', 2),
    ('DP1028.pdf', 3),
    ('DP1029.pdf', 4),
    ('DP1026_sticker_pack.zip', 5),
    ('DP1027_sticker_pack.zip', 6),
    ('DP1028_sticker_pack.zip', 7),
    ('DP1029_sticker_pack.zip', 8),
]


def refresh():
    client.refresh_access_token()
    auth_headers["Authorization"] = f"Bearer {client.access_token}"


def get_existing_images(listing_id):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{listing_id}/images",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get('results', [])


def delete_image(listing_id, image_id):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/images/{image_id}",
        headers=auth_headers, method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print(f"  Could not delete image {image_id}: {e}")


def get_existing_files(listing_id):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get('results', [])


def delete_file(listing_id, file_id, filename):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files/{file_id}",
        headers=auth_headers, method="DELETE")
    try:
        urllib.request.urlopen(req, timeout=15)
        print(f"  Deleted file: {filename}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Could not delete {filename}: {e}")


def upload_photo(listing_id, image_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_image(listing_id, image_path, rank=rank)
            img_id = result.get('listing_image_id')
            print(f"  Uploaded photo rank {rank}: {os.path.basename(image_path)} (id={img_id})")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                print(f"  Photo upload failed ({e.status}): {e}")
                return False
    return False


def upload_digital_file(listing_id, file_path, rank):
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, file_path, rank=rank)
            fid = result.get('listing_file_id')
            print(f"  Uploaded file rank {rank}: {os.path.basename(file_path)} (id={fid})")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                print(f"  File upload failed ({e.status}): {e}")
                return False
    return False


if __name__ == '__main__':
    print(f"Uploading bundle listing photos and files (listing {LISTING_ID})")

    # Clear existing images
    print("\nClearing existing images...")
    existing_images = get_existing_images(LISTING_ID)
    for img in existing_images:
        delete_image(LISTING_ID, img['listing_image_id'])
        time.sleep(0.3)
    if existing_images:
        print(f"  Deleted {len(existing_images)} old images")
    else:
        print("  No existing images")

    # Upload photos
    print("\nUploading listing photos...")
    for filename, rank in PHOTOS:
        path = os.path.join(BUNDLE_IMAGES_DIR, filename)
        if os.path.exists(path):
            upload_photo(LISTING_ID, path, rank)
            time.sleep(1)
        else:
            print(f"  WARNING: {filename} not found")

    # Clear existing digital files
    print("\nClearing existing digital files...")
    existing_files = get_existing_files(LISTING_ID)
    for f in existing_files:
        delete_file(LISTING_ID, f['listing_file_id'], f['filename'])

    # Upload digital files
    print("\nUploading digital files...")
    for filename, rank in DIGITAL_FILES:
        path = os.path.join(ART_DIR, filename)
        if os.path.exists(path):
            upload_digital_file(LISTING_ID, path, rank)
            time.sleep(1)
        else:
            print(f"  WARNING: {filename} not found at {path}")

    print(f"\n✓ Bundle listing (ID {LISTING_ID}) photos and files uploaded")
    print("  Next: go to Etsy Shop Manager and change the listing state to 'active'")
