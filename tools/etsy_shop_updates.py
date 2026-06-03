#!/usr/bin/env python3
"""
etsy_shop_updates.py

Posts Etsy Shop Updates (the social-feed feature inside Etsy) from your active listings.
Shop Updates appear to buyers who have favorited your shop — they show up as a feed
similar to Instagram Stories, driving repeat traffic at zero cost.

Etsy API endpoint: POST /v3/application/shops/{shop_id}/updates
  - image: the listing's hero image (downloaded from Etsy CDN and re-uploaded)
  - title: short caption (shown to followers)

Strategy:
  - Post 1 update every 3 days (daily = spam, monthly = forgotten)
  - Rotate through top-performing listings first, then the rest
  - Never post the same listing twice in a 30-day window

Usage:
  python tools/etsy_shop_updates.py --auto       # cron mode: post if due
  python tools/etsy_shop_updates.py --post       # post one update now
  python tools/etsy_shop_updates.py --listing 12345  # post a specific listing
  python tools/etsy_shop_updates.py --dry-run    # preview without posting
  python tools/etsy_shop_updates.py --status     # show post history
"""

from __future__ import annotations

import argparse
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

STATE_FILE     = BASE / "data" / "social" / "shop_updates_state.json"
POST_INTERVAL  = 3   # days between posts
MAX_CAPTION    = 160  # Etsy caption character limit

BASE_URL = "https://openapi.etsy.com/v3/application"

# Caption templates by product category
CAPTION_TEMPLATES = {
    "digital_planner": [
        "New in the shop: {title} 🌸 Instant download for GoodNotes & Notability",
        "Just listed: {title} ✨ Fillable PDF planner with 200+ kawaii stickers",
        "{title} — your new favorite planner 💕 Instant download",
    ],
    "svg_bundle": [
        "New SVG bundle just dropped: {title} ✂️ Cricut & Silhouette ready",
        "Fresh in the shop: {title} — instant download cut files",
        "New designs: {title} 🎨 SVG, PNG, DXF included",
    ],
    "sticker_pack": [
        "New sticker pack: {title} ✨ 200+ kawaii stickers for GoodNotes",
        "Just added: {title} 🌸 Instant download digital stickers",
        "{title} — now in the shop! Perfect for your planner 💕",
    ],
    "wall_art": [
        "New printable art: {title} 🖼️ Instant download, multiple sizes",
        "Just listed: {title} — print at home or at your local shop",
        "Fresh in the shop: {title} 🎨 Instant download wall art",
    ],
    "commercial_license": [
        "Commercial license now available for {title} 💼 Use in your business",
        "New: commercial license for {title} — perfect for Cricut sellers",
    ],
    "coloring_page": [
        "New coloring page: {title} 🖍️ Print and color instantly",
        "Just added: {title} — printable coloring page, instant download",
    ],
    "physical_print": [
        "New art print in the shop: {title} 🖼️ Ships to your door",
        "Just listed: {title} — premium printed wall art",
    ],
}

CATEGORY_KEYWORDS = {
    "digital_planner":    ["Digital Planner", "Life Planner", "Student Planner",
                           "Budget Planner", "Fitness Planner"],
    "svg_bundle":         ["SVG Bundle", "SVG Cut File", "Sublimation"],
    "sticker_pack":       ["Kawaii Sticker", "Sticker Pack", "Sticker Book"],
    "coloring_page":      ["Coloring Page", "Coloring Book"],
    "commercial_license": ["Commercial License"],
    "physical_print":     ["Physical Print", "Kawaii Wall Art Print", "Art Print | Printify"],
    "wall_art":           ["Wall Art", "Art Print", "Printable", "Wall Decor"],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def categorize(listing: dict) -> str:
    text = (listing.get("title", "") + " " + (listing.get("description") or "")).lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text for kw in kws):
            return cat
    return "wall_art"


def make_caption(listing: dict) -> str:
    cat       = categorize(listing)
    templates = CAPTION_TEMPLATES.get(cat, CAPTION_TEMPLATES["wall_art"])
    title     = (listing.get("title") or "")[:50]
    import random
    template  = templates[hash(str(listing["listing_id"])) % len(templates)]
    caption   = template.format(title=title)
    return caption[:MAX_CAPTION]


def get_hero_image_url(listing: dict) -> str:
    images = listing.get("images") or []
    if not images:
        return ""
    sorted_imgs = sorted(images, key=lambda x: x.get("rank", 99))
    return sorted_imgs[0].get("url_fullxfull", "")


def download_image(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "OnBrandCraftz/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"posts": [], "last_post_date": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def days_since_last_post(state: dict) -> int:
    last = state.get("last_post_date")
    if not last:
        return 999
    try:
        last_dt = datetime.fromisoformat(last)
        delta   = datetime.now(timezone.utc) - last_dt
        return delta.days
    except Exception:
        return 999


def recently_posted_ids(state: dict, window_days: int = 30) -> set:
    cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
    ids    = set()
    for post in state.get("posts", []):
        try:
            ts = datetime.fromisoformat(post["timestamp"])
            if ts >= cutoff:
                ids.add(post["listing_id"])
        except Exception:
            pass
    return ids


def pick_listing(listings: list[dict], state: dict) -> dict | None:
    skip = recently_posted_ids(state)
    for l in listings:
        if l["listing_id"] not in skip and get_hero_image_url(l):
            return l
    # If all listings have been posted recently, start over
    for l in listings:
        if get_hero_image_url(l):
            return l
    return None


# ── API call ──────────────────────────────────────────────────────────────────

def post_shop_update(client: EtsyAPIClient, listing: dict,
                     caption: str, dry_run: bool = False) -> bool:
    """
    Post a shop update using the listing's hero image.
    Returns True on success.

    Etsy endpoint: POST /v3/application/shops/{shop_id}/updates
    Multipart form: image (file), title (string)
    """
    image_url = get_hero_image_url(listing)
    lid       = listing["listing_id"]
    title     = (listing.get("title") or "")[:60]

    if dry_run:
        print(f"[DRY RUN] Would post shop update:")
        print(f"  Listing: [{lid}] {title}")
        print(f"  Caption: {caption}")
        print(f"  Image:   {image_url[:70]}")
        return True

    print(f"  Downloading hero image...")
    try:
        image_data = download_image(image_url)
    except Exception as e:
        print(f"  ERROR: Could not download image: {e}")
        return False

    # Build multipart body
    boundary   = "----ShopUpdateBoundary" + os.urandom(8).hex()
    body_parts = []

    # caption field
    body_parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="title"\r\n\r\n{caption}'.encode()
    )

    # image field
    body_parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="image"; filename="update.jpg"\r\nContent-Type: image/jpeg\r\n\r\n'.encode()
        + image_data
    )
    body_parts.append(f'--{boundary}--'.encode())
    body = b'\r\n'.join(body_parts)

    api_key_header = (
        f"{client.client_id}:{client.client_secret}"
        if client.client_secret else client.api_key
    )
    headers = {
        "Content-Type":  f"multipart/form-data; boundary={boundary}",
        "Authorization": f"Bearer {client.access_token}",
        "x-api-key":     api_key_header,
    }
    url = f"{BASE_URL}/shops/{client.shop_id}/updates"
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            print(f"  ✓ Shop update posted (update_id: {result.get('shop_update_id', '?')})")
            return True
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        try:
            msg = json.loads(err_body).get("error", err_body)
        except Exception:
            msg = err_body
        print(f"  ✗ API error {e.code}: {msg}")
        # Surface instructions if endpoint not found
        if e.code == 404:
            print("\n  NOTE: The Shop Updates endpoint may not be enabled for this API key.")
            print("  To enable: go to https://www.etsy.com/developers/your-apps")
            print("  and request the 'shops_w' scope with Shop Updates access.")
        return False
    except Exception as e:
        print(f"  ✗ Error posting update: {e}")
        return False


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_auto(client: EtsyAPIClient, listings: list[dict]) -> None:
    state = load_state()
    days  = days_since_last_post(state)

    if days < POST_INTERVAL:
        next_in = POST_INTERVAL - days
        print(f"[shop-updates] OK — last post {days}d ago, next post in {next_in}d")
        return

    listing = pick_listing(listings, state)
    if not listing:
        print("[shop-updates] No listings with images found to post")
        return

    caption = make_caption(listing)
    print(f"[shop-updates] Posting update for [{listing['listing_id']}] "
          f"{(listing.get('title') or '')[:55]}")

    ok = post_shop_update(client, listing, caption)
    if ok:
        state.setdefault("posts", []).append({
            "listing_id": listing["listing_id"],
            "title":      (listing.get("title") or "")[:80],
            "caption":    caption,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        })
        state["posts"]          = state["posts"][-50:]
        state["last_post_date"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
        print(f"[shop-updates] Posted. Next post in {POST_INTERVAL} days.")


def cmd_post(client: EtsyAPIClient, listings: list[dict],
             listing_id: int | None, dry_run: bool) -> None:
    if listing_id:
        match = next((l for l in listings if l["listing_id"] == listing_id), None)
        if not match:
            print(f"Listing {listing_id} not found in active listings")
            sys.exit(1)
        listing = match
    else:
        state   = load_state()
        listing = pick_listing(listings, state)
        if not listing:
            print("No suitable listing found to post")
            sys.exit(1)

    caption = make_caption(listing)
    title   = (listing.get("title") or "")[:60]
    print(f"Posting shop update for [{listing['listing_id']}] {title}")
    print(f"Caption: {caption}\n")

    ok = post_shop_update(client, listing, caption, dry_run=dry_run)

    if ok and not dry_run:
        state = load_state()
        state.setdefault("posts", []).append({
            "listing_id": listing["listing_id"],
            "title":      title,
            "caption":    caption,
            "timestamp":  datetime.now(timezone.utc).isoformat(),
        })
        state["posts"]          = state["posts"][-50:]
        state["last_post_date"] = datetime.now(timezone.utc).isoformat()
        save_state(state)


def cmd_status() -> None:
    state = load_state()
    days  = days_since_last_post(state)
    posts = state.get("posts", [])

    print(f"Total shop updates posted: {len(posts)}")
    print(f"Last post: {state.get('last_post_date', 'never')} ({days}d ago)")
    print(f"Next post due: {'now' if days >= POST_INTERVAL else f'in {POST_INTERVAL - days}d'}")

    if posts:
        print("\nRecent posts:")
        for p in posts[-10:]:
            ts = p.get("timestamp", "?")[:10]
            print(f"  {ts}  [{p['listing_id']}] {p.get('title','')[:55]}")
            print(f"         \"{p.get('caption','')[:70]}\"")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Post Etsy Shop Updates")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--auto",     action="store_true",
                       help="Cron mode: post if 3+ days since last update")
    group.add_argument("--post",     action="store_true",
                       help="Post one update now")
    group.add_argument("--dry-run",  action="store_true",
                       help="Preview without posting")
    group.add_argument("--status",   action="store_true",
                       help="Show post history")
    parser.add_argument("--listing", type=int, default=None,
                        help="Specific listing ID to post (used with --post or --dry-run)")
    args = parser.parse_args()

    if args.status:
        cmd_status()
        return

    with open(BASE / ".env") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("ERROR: Could not refresh OAuth token")
        sys.exit(1)

    listings = client.get_shop_listings_all(state="active")

    if args.auto:
        cmd_auto(client, listings)
    elif args.post or args.dry_run:
        cmd_post(client, listings, listing_id=args.listing, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
