#!/usr/bin/env python3
"""
approve_listing.py

Two jobs in one tool:

1. REVIEW & PUBLISH a draft listing (runs the pre-publish quality gate, then
   activates it on Etsy).
2. LOCK IN the approved state as ground truth — captures the listing's title,
   tags, files, and a perceptual hash of every photo into
   data/listing_approvals.json. Once locked, listing_integrity_check.py will
   FAIL if any approved photo/file/title later changes. This is how "Scott said
   it's good" becomes permanent memory.

When you publish a draft with --yes (or confirm activation), the approval
snapshot is captured automatically. Use --lock to snapshot an already-active
listing without changing its state.

Usage:
  python tools/approve_listing.py --list-drafts            # show draft listings
  python tools/approve_listing.py --listing-id <ID>        # review + prompt to publish
  python tools/approve_listing.py --listing-id <ID> --yes  # publish + lock in
  python tools/approve_listing.py --lock <ID> [--notes ""] # lock an active listing
  python tools/approve_listing.py --list-approvals         # show locked approvals
  python tools/approve_listing.py --revoke <ID>            # remove an approval
"""

from __future__ import annotations

import os
import sys
import io
import json
import time
import argparse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent

# Robust .env load (no hard dependency on python-dotenv)
_env_path = BASE_DIR / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError

APPROVALS_PATH = BASE_DIR / "data" / "listing_approvals.json"
REGISTRY_PATH = BASE_DIR / "data" / "product_art_registry.json"
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"

ART_MATCH_THRESHOLD = 80   # Hamming distance; ≤ this means the art is present in a photo


# ---------------------------------------------------------------------------
# Perceptual hash helpers
# ---------------------------------------------------------------------------

def dhash16(image_bytes: bytes) -> str | None:
    if not PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    bits.append("1" if pixels[row * 17 + col] > pixels[row * 17 + col + 1] else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def hamming(a: str, b: str) -> int:
    return sum(x != y for x, y in zip(
        bin(int(a, 16))[2:].zfill(256),
        bin(int(b, 16))[2:].zfill(256)
    ))


def fetch_url(url: str) -> bytes | None:
    try:
        with urllib.request.urlopen(url, timeout=30) as resp:
            return resp.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Data helpers
# ---------------------------------------------------------------------------

def load_json(path: Path) -> dict:
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return {}


def save_approvals(approvals: dict) -> None:
    with open(APPROVALS_PATH, "w") as f:
        json.dump(approvals, f, indent=2, sort_keys=True)


def get_dp_codes_for_listing(listing_id: str) -> list[str]:
    """All DP codes whose map entry points at this listing_id (any id role)."""
    dp_map = load_json(MAP_PATH)
    if not dp_map:
        return []
    try:
        lid_int = int(listing_id)
    except (TypeError, ValueError):
        return []
    codes = []
    id_fields = ("listing_id", "kawaii_listing_id", "planner_listing_id",
                 "individual_listing_id", "secondary_listing_id")
    for dp_code, entry in dp_map.items():
        if not isinstance(entry, dict):
            continue
        for key in id_fields:
            val = entry.get(key)
            if val and int(val) == lid_int:
                codes.append(dp_code)
                break
    return codes


def verify_art(photo_hashes: dict[str, str], dp_codes: list[str],
               registry: dict) -> tuple[bool, int, str]:
    """Compare every photo hash against registered art for the dp_codes.
    Returns (verified, min_distance, matching_dp_code)."""
    if not photo_hashes or not dp_codes or not registry:
        return False, 999, ""
    best_distance, best_dp = 999, ""
    for dp_code in dp_codes:
        entry = registry.get(dp_code)
        if not entry:
            continue
        art_hash = entry.get("source_hash", "")
        if not art_hash:
            continue
        for _slot, photo_hash in photo_hashes.items():
            d = hamming(photo_hash, art_hash)
            if d < best_distance:
                best_distance, best_dp = d, dp_code
    return best_distance <= ART_MATCH_THRESHOLD, best_distance, best_dp


# ---------------------------------------------------------------------------
# Draft review / publish (original behavior)
# ---------------------------------------------------------------------------

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
    price = (price_raw.get("amount", 0) / max(price_raw.get("divisor", 100), 1)
             if isinstance(price_raw, dict) else float(price_raw or 0))
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

    failures = EtsyAPIClient.pre_publish_gate({
        "title": title, "description": desc, "tags": tags, "price": price,
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


# ---------------------------------------------------------------------------
# Lock-in approval (new behavior)
# ---------------------------------------------------------------------------

def lock_in(client: EtsyAPIClient, listing_id: str, notes: str = "") -> dict:
    """Capture the listing's current state as Scott-approved ground truth."""
    print(f"Locking in listing {listing_id} …")
    listing = client.get_listing(listing_id)
    title = listing.get("title", "")
    tags = listing.get("tags", []) or []

    # Files
    try:
        files = client._request(
            "GET", f"shops/{client.shop_id}/listings/{listing_id}/files"
        ).get("results", [])
    except Exception:
        files = []
    file_names = [f.get("filename", "") for f in files]

    # Images — download every one and hash it
    try:
        images = client._request("GET", f"listings/{listing_id}/images").get("results", [])
    except Exception:
        images = []

    photo_hashes: dict[str, str] = {}
    photo_urls: dict[str, str] = {}
    print(f"  Downloading {len(images)} photos …")
    for img in sorted(images, key=lambda x: x.get("rank", 99)):
        rank = str(img.get("rank", "?"))
        url = img.get("url_fullxfull") or img.get("url_570xN") or ""
        if not url:
            continue
        photo_urls[rank] = url
        data = fetch_url(url)
        if data:
            h = dhash16(data)
            if h:
                photo_hashes[rank] = h
        time.sleep(0.2)

    dp_codes = get_dp_codes_for_listing(listing_id)
    registry = load_json(REGISTRY_PATH)
    art_verified, art_min, art_dp = verify_art(photo_hashes, dp_codes, registry)

    record = {
        "dp_codes": dp_codes,
        "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "notes": notes,
        "title": title,
        "tags": tags,
        "file_names": file_names,
        "file_count": len(files),
        "photo_count": len(images),
        "photo_hashes": photo_hashes,
        "photo_urls": photo_urls,
        "art_verified": art_verified,
        "art_min_distance": art_min,
        "art_matching_dp": art_dp,
    }

    approvals = load_json(APPROVALS_PATH)
    approvals[str(listing_id)] = record
    save_approvals(approvals)

    dp_str = ", ".join(dp_codes) if dp_codes else "unknown"
    if not registry:
        art_str = "skipped (run build_art_registry.py first)"
    elif not dp_codes:
        art_str = "n/a (no DP code mapped — e.g. planner/sticker)"
    elif art_verified:
        art_str = f"YES (min distance {art_min} from {art_dp})"
    else:
        art_str = f"NO — art not found in any photo (min distance {art_min})"

    print(f"\n✓ Locked in listing {listing_id} ({dp_str})")
    print(f"  Title : {title}")
    print(f"  Files : {file_names}")
    print(f"  Photos: {len(images)} (hashes captured)")
    print(f"  Art verified: {art_str}")
    if notes:
        print(f"  Notes : {notes}")
    if dp_codes and registry and not art_verified:
        print("  ⚠️  WARNING: none of this listing's photos match the registered art. "
              "Verify the correct product before trusting this approval.")
    return record


def list_approvals() -> None:
    approvals = load_json(APPROVALS_PATH)
    if not approvals:
        print("No approvals on record.")
        return
    print(f"{'Listing ID':<15} {'DP Codes':<22} {'Approved At':<22} {'Art':<5} Notes")
    print("-" * 92)
    for lid, rec in sorted(approvals.items()):
        dp = ", ".join(rec.get("dp_codes", [])) or "?"
        approved_at = rec.get("approved_at", "")[:19]
        art = "YES" if rec.get("art_verified") else "NO"
        notes = (rec.get("notes", "") or "")[:30]
        print(f"{lid:<15} {dp:<22} {approved_at:<22} {art:<5} {notes}")


def revoke(listing_id: str) -> None:
    approvals = load_json(APPROVALS_PATH)
    if str(listing_id) not in approvals:
        print(f"Listing {listing_id} has no approval record.")
        sys.exit(1)
    del approvals[str(listing_id)]
    save_approvals(approvals)
    print(f"✓ Revoked approval for listing {listing_id}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Review/publish a draft listing AND lock in its approved state")
    parser.add_argument("--list-drafts", action="store_true", help="Show all draft listings")
    parser.add_argument("--listing-id", help="Listing ID to review and publish")
    parser.add_argument("--yes", action="store_true",
                        help="Skip confirmation; activate and lock in immediately")
    parser.add_argument("--lock", metavar="LISTING_ID",
                        help="Lock in an already-active listing as approved (no state change)")
    parser.add_argument("--notes", default="", help="Optional approval notes")
    parser.add_argument("--list-approvals", action="store_true", help="Show locked approvals")
    parser.add_argument("--revoke", metavar="LISTING_ID", help="Remove an approval record")
    args = parser.parse_args()

    # Pure-local actions (no API client needed)
    if args.list_approvals:
        list_approvals()
        return
    if args.revoke:
        revoke(args.revoke)
        return

    client = EtsyAPIClient()
    if not client.shop_id:
        print("ERROR: ETSY_SHOP_ID not set in .env")
        sys.exit(1)

    if args.list_drafts:
        list_drafts(client)
        return

    if not PIL_OK and (args.lock or args.listing_id):
        print("WARNING: Pillow not installed — photo hashing disabled (pip install Pillow)")

    # Lock in an existing active listing
    if args.lock:
        lock_in(client, args.lock, args.notes)
        return

    # Review + publish a draft
    if not args.listing_id:
        parser.print_help()
        sys.exit(0)

    listing = client.get_listing(args.listing_id)
    show_listing(listing)

    if listing.get("state") == "active":
        print("This listing is already active.")
        # Offer to lock it in anyway
        if args.yes or input("\nLock in this active listing as approved? [y/N]: ").strip().lower() == "y":
            lock_in(client, args.listing_id, args.notes)
        return

    if not args.yes:
        answer = input("\nActivate AND lock in this listing? [y/N]: ").strip().lower()
        if answer != "y":
            print("Cancelled.")
            return

    try:
        activate_listing(client, args.listing_id)
    except EtsyAPIError as e:
        print(f"✗ Failed to activate: {e}")
        sys.exit(1)

    # Once live, lock the approved snapshot into memory
    lock_in(client, args.listing_id, args.notes)


if __name__ == "__main__":
    main()
