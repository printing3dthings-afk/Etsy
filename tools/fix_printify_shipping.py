#!/usr/bin/env python3
"""
fix_printify_shipping.py

Zeros out all shipping costs on Printify's "Free Standard" profile and applies it
to all 54 Printify wall art listings.  Removes the ~$19.79 shipping from Print Clever
(UK) that triggers Etsy's >$6 shipping ranking penalty.

Strategy: Etsy's standard profile creation API doesn't support "ships everywhere" for
flat-rate profiles.  Printify's own "Free Standard" profile is a flat-rate profile that
already has the right structure and is compatible with Printify listings (no item weight
required).  We zero out its destination costs and assign it to all listings.

Usage:
  python tools/fix_printify_shipping.py --dry-run   # preview without changes
  python tools/fix_printify_shipping.py --fix        # apply to Etsy
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

PRINTIFY_MARKERS = ["Art Print", "Physical Print", "Wall Art Print", "Kawaii Wall Art"]


def is_printify_listing(listing: dict) -> bool:
    title = listing.get("title", "")
    return any(m in title for m in PRINTIFY_MARKERS)


def find_printify_free_profile(client: EtsyAPIClient) -> int:
    """Find Printify's own 'Free Standard' flat-rate profile by name.
    This profile is compatible with Printify listings (no item dimensions required).
    """
    profiles = client.get_shipping_profiles()
    for p in profiles:
        name = p.get("title", "")
        if "free standard" in name.lower() and "print clever" in name.lower():
            return int(p["shipping_profile_id"])
    raise SystemExit(
        "Could not find 'Free Standard: Print Clever' shipping profile. "
        "Has Printify been connected to this shop?"
    )


def zero_out_destinations(client: EtsyAPIClient, profile_id: int, dry_run: bool) -> int:
    """Set all destination primary and secondary costs to $0. Returns count updated."""
    result = client._request(
        "GET", f"shops/{client.shop_id}/shipping-profiles/{profile_id}/destinations"
    )
    dests = result.get("results", [])
    updated = 0
    for d in dests:
        cost = d.get("primary_cost", {}).get("amount", 0)
        if cost == 0:
            continue
        dest_id = d["shipping_profile_destination_id"]
        iso = d.get("destination_country_iso") or "catch-all"
        if dry_run:
            print(f"    DRY-RUN zero dest [{dest_id}] {iso} ${cost/100:.2f} → $0")
            updated += 1
            continue
        client._request(
            "PUT",
            f"shops/{client.shop_id}/shipping-profiles/{profile_id}/destinations/{dest_id}",
            body={"primary_cost": 0.0, "secondary_cost": 0.0},
        )
        updated += 1
        time.sleep(0.25)
    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply free shipping to all Printify wall art listings"
    )
    parser.add_argument("--dry-run", action="store_true", help="Preview without making changes")
    parser.add_argument("--fix", action="store_true", help="Apply changes to Etsy")
    args = parser.parse_args()

    if not args.dry_run and not args.fix:
        parser.print_help()
        sys.exit(1)

    client = EtsyAPIClient()

    print("Refreshing access token...")
    if not client.refresh_access_token():
        print("ERROR: Could not refresh access token. Run python tools/etsy_oauth.py")
        sys.exit(1)
    print("Token OK")

    # Step 1: Find the compatible Printify flat-rate profile
    free_pid = find_printify_free_profile(client)
    print(f"\nUsing 'Free Standard: Print Clever' profile: {free_pid}")

    # Step 2: Zero out any non-zero destination costs
    print("Zeroing destination costs...")
    zeroed = zero_out_destinations(client, free_pid, dry_run=args.dry_run)
    if zeroed:
        print(f"  Zeroed {zeroed} destination costs")
    else:
        print("  All destinations already $0")

    # Step 3: Apply profile to all Printify listings
    print("\nFetching all active listings...")
    all_listings = client.get_shop_listings_all(state="active")
    printify = [l for l in all_listings if is_printify_listing(l)]
    print(f"Found {len(printify)} Printify physical print listings (of {len(all_listings)} total)")

    if not printify:
        print("No Printify listings found. Exiting.")
        sys.exit(0)

    updated = 0
    skipped = 0
    errors = 0

    for listing in printify:
        lid = listing["listing_id"]
        title = listing["title"]
        current_pid = listing.get("shipping_profile_id")

        if current_pid == free_pid:
            skipped += 1
            continue

        if args.dry_run:
            print(f"  DRY-RUN  [{lid}] {title[:60]}")
            updated += 1
            continue

        try:
            client.update_listing(lid, {"shipping_profile_id": free_pid})
            print(f"  ✓  [{lid}] {title[:60]}")
            updated += 1
            time.sleep(0.4)
        except EtsyAPIError as e:
            print(f"  ✗  [{lid}] {title[:60]}")
            print(f"     {e}")
            errors += 1
            time.sleep(1.0)

    label = "DRY RUN — " if args.dry_run else ""
    print(f"\n{label}Results: {updated} updated, {skipped} already on free profile, {errors} errors")

    if not args.dry_run and updated > 0:
        print(
            f"\nDone. All {updated} listings now show free shipping to buyers.\n"
            "Etsy ranking penalty for >$6 shipping will lift within 24-48 hours.\n"
            "Note: if Printify re-syncs a product it may reset the shipping profile.\n"
            "Re-run this script periodically or after Printify syncs."
        )


if __name__ == "__main__":
    main()
