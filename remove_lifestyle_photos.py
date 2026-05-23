"""
Remove lifestyle/room-setting photos from wall art listings.

Identified by visual inspection: 8 listings each have 2 room-setting mockup photos
at rank 1 and rank 2. Ranks 3+ are plain art and informational graphics — those stay.

Run AFTER completing OAuth: python tools/etsy_oauth.py
Then: python remove_lifestyle_photos.py
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore

# Exact image IDs to delete — confirmed by visual review as room-setting mockups
LIFESTYLE_IMAGES_TO_DELETE = {
    "4509597559": {  # Italian Kitchen Print
        "images": [8049205958, 8097119371],  # kitchen counter + dining room
        "keep_from_rank": 3,
    },
    "4509596017": {  # Abstract Woman Portrait Print
        "images": [8049198964, 8049199028],  # bedroom + vanity table area
        "keep_from_rank": 3,
    },
    "4509600086": {  # Tropical Leaves Print
        "images": [8097105401, 8097105501],  # living room sofa + dining room
        "keep_from_rank": 3,
    },
    "4509593697": {  # Grand Canyon Print
        "images": [8097098583, 8049185314],  # living room armchair + entryway with bench
        "keep_from_rank": 3,
    },
    "4509593623": {  # Paris Skyline Print
        "images": [8097097937, 8097098009],  # bedroom + living room with sofa
        "keep_from_rank": 3,
    },
    "4509593487": {  # Vintage Botanical Print
        "images": [8049183888, 8049184042],  # study desk + kitchen counter with recipe card
        "keep_from_rank": 3,
    },
    "4509598784": {  # Abstract Brushstroke Print
        "images": [8049183088, 8049183226],  # white sofa living room + blue sofa living room
        "keep_from_rank": 3,
    },
    "4509598660": {  # Moon Phases Print
        "images": [8049182254, 8049182388],  # dark bedroom + dark living room with candle
        "keep_from_rank": 3,
    },
}


def main():
    client = EtsyAPIClient()
    if not client.access_token:
        print("ERROR: Etsy OAuth not configured.")
        print("Run: python tools/etsy_oauth.py")
        sys.exit(1)

    store = DataStore()
    listings = store.get("listings", default=[])
    listings_by_id = {str(l.get("id")): l for l in listings}

    total_deleted = 0
    errors = []

    print(f"Removing lifestyle room-setting photos from {len(LIFESTYLE_IMAGES_TO_DELETE)} listings...\n")

    for listing_id, config in LIFESTYLE_IMAGES_TO_DELETE.items():
        title = listings_by_id.get(listing_id, {}).get("title", listing_id)[:65]
        image_ids = config["images"]

        deleted = 0
        listing_errors = []

        for img_id in image_ids:
            try:
                client.delete_listing_image(listing_id, img_id)
                deleted += 1
                print(f"  ✓ Deleted image {img_id}")
            except EtsyAPIError as e:
                listing_errors.append(str(e))
                print(f"  ✗ Error deleting {img_id}: {e}")

        # Update local data store — reduce image count
        if listing_id in listings_by_id:
            current_count = listings_by_id[listing_id].get("images", 0)
            listings_by_id[listing_id]["images"] = max(0, current_count - deleted)

        total_deleted += deleted
        if listing_errors:
            errors.extend(listing_errors)
            print(f"[{listing_id}] {deleted}/{len(image_ids)} deleted — {title}")
        else:
            print(f"[{listing_id}] {deleted}/{len(image_ids)} room-setting photos removed — {title}")
        print()

    # Save updated counts
    store.set(list(listings_by_id.values()), "listings")
    store.save()

    print(f"Done. {total_deleted} lifestyle photos deleted.")
    if errors:
        print(f"\n{len(errors)} error(s): {errors}")
    print("\nPlain art photos (rank 3+) remain on all listings.")
    print("Regenerate proper lifestyle photos with DALL-E when OpenAI billing is restored.")


if __name__ == "__main__":
    main()
