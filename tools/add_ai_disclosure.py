#!/usr/bin/env python3
"""
Add mandatory AI disclosure to all active listings that lack it.

Etsy's Creativity Standards (effective June 10, 2025) require sellers who
used AI tools to create or assist with product creation to disclose this in
the listing. Non-compliant listings risk automated removal.

This script:
  1. Fetches all active listings
  2. Checks each description for existing disclosure language
  3. Appends the standard disclosure block to listings that are missing it
  4. Updates via PATCH /v3/application/shops/{shop_id}/listings/{listing_id}

Usage:
  python tools/add_ai_disclosure.py --dry-run    # preview only, no changes
  python tools/add_ai_disclosure.py               # apply updates
  python tools/add_ai_disclosure.py --lid 12345   # single listing
"""

import os, sys, json, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

AI_DISCLOSURE = (
    "\n\n---\n"
    "This product was created with AI assistance (DALL-E image generation "
    "for cover/lifestyle artwork). All content has been reviewed and finalized "
    "by the seller."
)

# Keywords that indicate disclosure is already present
DISCLOSURE_MARKERS = ["AI assistance", "DALL-E", "ai-generated", "AI-generated", "artificial intelligence"]


def already_disclosed(description: str) -> bool:
    return any(marker.lower() in description.lower() for marker in DISCLOSURE_MARKERS)


def fetch_all_active(client) -> list:
    headers = {
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key": f"{client.client_id}:{client.client_secret}",
    }
    listings = []
    offset = 0
    while True:
        url = (f"https://openapi.etsy.com/v3/application/shops/{client.shop_id}"
               f"/listings/active?limit=100&offset={offset}")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
        except Exception as e:
            print(f"  Fetch error at offset={offset}: {e}")
            break
        batch = data.get('results', [])
        listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return listings


def patch_description(client, listing_id: int, new_desc: str) -> bool:
    try:
        client.update_listing(listing_id, {"description": new_desc})
        return True
    except EtsyAPIError as e:
        if e.status == 429:
            time.sleep(15)
            try:
                client.update_listing(listing_id, {"description": new_desc})
                return True
            except EtsyAPIError:
                pass
        print(f"    PATCH failed for {listing_id}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only — no changes')
    parser.add_argument('--lid', type=int, help='Target a single listing ID')
    args = parser.parse_args()

    client = EtsyAPIClient()
    client.refresh_access_token()

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  AI Disclosure Compliance Tool")
    print("  Etsy Creativity Standards (effective June 10, 2025)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

    if args.lid:
        headers = {
            "Authorization": f"Bearer {client.access_token}",
            "x-api-key": f"{client.client_id}:{client.client_secret}",
        }
        url = f"https://openapi.etsy.com/v3/application/listings/{args.lid}"
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            listing = json.loads(resp.read())
        listings = [listing]
    else:
        print("  Fetching all active listings...")
        listings = fetch_all_active(client)
        print(f"  Found {len(listings)} active listings\n")

    needs_update = []
    already_ok = []

    for lst in listings:
        lid = lst.get('listing_id')
        title = (lst.get('title') or '')[:60]
        desc = lst.get('description') or ''
        if already_disclosed(desc):
            already_ok.append(lid)
        else:
            needs_update.append(lst)

    print(f"  Compliant:     {len(already_ok)} listings (no action needed)")
    print(f"  Needs update:  {len(needs_update)} listings\n")

    if not needs_update:
        print("  ✓ All listings are compliant. Nothing to do.")
        return

    updated = 0
    failed = 0

    for lst in needs_update:
        lid = lst.get('listing_id')
        title = (lst.get('title') or '')[:70]
        desc = lst.get('description') or ''
        new_desc = desc + AI_DISCLOSURE

        if args.dry_run:
            print(f"  [DRY RUN] Would update [{lid}] {title}")
        else:
            ok = patch_description(client, lid, new_desc)
            if ok:
                print(f"  ✓ Updated [{lid}] {title}")
                updated += 1
            else:
                print(f"  ✗ Failed  [{lid}] {title}")
                failed += 1
            time.sleep(0.5)  # stay well within rate limits

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if args.dry_run:
        print(f"  DRY RUN complete — {len(needs_update)} listings would be updated")
    else:
        print(f"  Updated: {updated}   Failed: {failed}")
        if failed == 0:
            print("  ✓ All listings now compliant with Etsy AI disclosure policy")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


if __name__ == '__main__':
    main()
