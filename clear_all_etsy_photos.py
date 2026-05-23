"""
One-time script: delete all photos from every active Etsy listing.

Run this AFTER completing OAuth: python tools/etsy_oauth.py
Then: python clear_all_etsy_photos.py

Photos were removed because they were generated with incorrect artwork and need
to be regenerated with DALL-E once OpenAI billing is restored. Listings without
photos are still discoverable but show a placeholder — this is better than
displaying incorrect artwork.
"""
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore


def main():
    client = EtsyAPIClient()
    if not client.access_token:
        print("ERROR: Etsy OAuth not configured.")
        print("Run: python tools/etsy_oauth.py")
        sys.exit(1)

    store = DataStore()
    listings = store.get("listings", default=[])

    print(f"Found {len(listings)} listings to process...")
    print()

    total_deleted = 0
    errors = []

    for listing in listings:
        listing_id = str(listing.get("id", ""))
        title = listing.get("title", listing_id)[:70]

        try:
            images = client.get_listing_images(listing_id)
            if not images:
                print(f"  [{listing_id}] No photos — skipped")
                continue

            deleted = 0
            for img in images:
                img_id = img.get("listing_image_id")
                if img_id:
                    client.delete_listing_image(listing_id, img_id)
                    deleted += 1

            total_deleted += deleted
            listing["images"] = 0
            listing.pop("main_image", None)
            print(f"  [{listing_id}] Deleted {deleted} photo(s) — {title}")

        except EtsyAPIError as e:
            errors.append({"listing_id": listing_id, "title": title[:50], "error": str(e)})
            print(f"  [{listing_id}] ERROR: {e} — {title[:50]}")

    store.set(listings, "listings")
    store.save()

    print()
    print(f"Done. {total_deleted} photos deleted across {len(listings)} listings.")
    if errors:
        print(f"\n{len(errors)} error(s):")
        for e in errors:
            print(f"  {e['listing_id']}: {e['error']}")
    else:
        print("No errors.")
    print()
    print("Next step: regenerate listing photos with DALL-E when OpenAI billing is restored.")
    print("Use the Art Creation Agent or tools/gen_listing_images.py")


if __name__ == "__main__":
    main()
