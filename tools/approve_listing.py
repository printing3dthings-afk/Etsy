#!/usr/bin/env python3
"""
approve_listing.py

Review and publish a draft Etsy listing.

Usage:
  python tools/approve_listing.py --list-drafts
  python tools/approve_listing.py --listing-id <ID>
  python tools/approve_listing.py --listing-id <ID> --yes
"""

from __future__ import annotations

import os
import sys
import json
import argparse

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError


def list_drafts(client: EtsyAPIClient) -> None:
    resp = client._request(
        "GET",
        f"shops/{client.shop_id}/listings",
        params={"state": "draft", "limit": 25},
    )
    drafts = resp.get("results", [])
    if not drafts:
        print("No draft listings found.")
        return
    print(f"\n{'ID':<14} {'Title':<65} Tags Photos")
    print("-" * 100)
    for d in drafts:
        lid = d.get("listing_id", "?")
        title = (d.get("title") or "")[:64]
        tags = len(d.get("tags") or [])
        images = len(d.get("images") or [])
        print(f"{lid:<14} {title:<65} {tags:>4}  {images:>5}")


def show_listing(listing: dict) -> None:
    title = listing.get("title", "")
    desc = listing.get("description", "")
    tags = listing.get("tags") or []
    price_raw = listing.get("price") or {}
    price = price_raw.get("amount", 0) / max(price_raw.get("divisor", 100), 1) if isinstance(price_raw, dict) else float(price_raw or 0)
    images = listing.get("images") or []
    state = listing.get("state", "")

    print("\n" + "=" * 70)
    print(f"LISTING REVIEW — {listing.get('listing_id')}")
    print("=" * 70)
    print(f"State  : {state}")
    print(f"Title  : {title}  ({len(title)} chars)")
    print(f"Price  : ${price:.2f}")
    print(f"Tags   : {len(tags)}/13 — {tags}")
    print(f"Photos : {len(images)}")
    print(f"\nDescription (first 400 chars):\n{desc[:400]}...")

    # Run quality gate checks
    from etsy_api import EtsyAPIClient as _C
    failures = _C.pre_publish_gate({
        "title": title,
        "description": desc,
        "tags": tags,
        "price": price,
    })
    if failures:
        print("\n⚠️  QUALITY GATE ISSUES:")
        for f in failures:
            print(f"   ✗ {f}")
    else:
        print("\n✓ Quality gate: PASSED")
    print("=" * 70)


def activate_listing(client: EtsyAPIClient, listing_id: str) -> None:
    result = client.update_listing(listing_id, {"state": "active"})
    new_state = result.get("state", "unknown")
    print(f"✓ Listing {listing_id} is now: {new_state}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Review and publish a draft Etsy listing")
    parser.add_argument("--list-drafts", action="store_true", help="Show all draft listings")
    parser.add_argument("--listing-id", help="Listing ID to review and publish")
    parser.add_argument("--yes", action="store_true", help="Skip confirmation prompt and activate immediately")
    args = parser.parse_args()

    client = EtsyAPIClient()
    if not client.shop_id:
        print("ERROR: ETSY_SHOP_ID not set in .env")
        sys.exit(1)

    if args.list_drafts:
        list_drafts(client)
        return

    if not args.listing_id:
        parser.print_help()
        sys.exit(0)

    listing = client.get_listing(args.listing_id)
    show_listing(listing)

    if listing.get("state") == "active":
        print("This listing is already active.")
        return

    if not args.yes:
        answer = input("\nActivate this listing? [y/N]: ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return

    try:
        activate_listing(client, args.listing_id)
    except EtsyAPIError as e:
        print(f"✗ Failed to activate: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
