#!/usr/bin/env python3
"""
pinterest_post_queue.py

Generates a ready-to-post Pinterest queue from all active Etsy listings.
Outputs two files:
  data/social/pinterest_queue.csv   — for manual posting (copy-paste into Pinterest)
  data/social/pinterest_ready.json  — API payload for when developer app is approved

Board assignments are based on product category. Each pin gets an SEO-optimized
title, description, and hashtag set.

Usage:
  python tools/pinterest_post_queue.py              # generate full queue
  python tools/pinterest_post_queue.py --new-only   # only listings not yet in queue
  python tools/pinterest_post_queue.py --board "Digital Planners 2026"  # single board
  python tools/pinterest_post_queue.py --status     # show queue stats
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import date
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient

OUTPUT_CSV  = BASE / "data" / "social" / "pinterest_queue.csv"
OUTPUT_JSON = BASE / "data" / "social" / "pinterest_ready.json"
STATE_FILE  = BASE / "data" / "social" / "pinterest_state.json"

# Board definitions — match the boards already created on Pinterest
BOARDS = {
    "digital_planner":    "Digital Planners 2026 — Kawaii GoodNotes",
    "svg_bundle":         "SVG Cut Files — Cricut Silhouette",
    "sticker_pack":       "Kawaii Sticker Packs — GoodNotes Elements",
    "wall_art":           "Printable Wall Art — Instant Download",
    "commercial_license": "Digital Downloads — Small Business",
    "coloring_page":      "Printable Wall Art — Instant Download",
    "physical_print":     "Printable Wall Art — Instant Download",
}

CATEGORY_KEYWORDS = {
    "digital_planner":    ["Digital Planner", "Life Planner", "Student Planner",
                           "Budget Planner", "Fitness Planner", "GoodNotes"],
    "svg_bundle":         ["SVG Bundle", "SVG Cut File", "Sublimation", "Cricut"],
    "sticker_pack":       ["Kawaii Sticker", "Sticker Pack", "Sticker Book",
                           "GoodNotes Sticker"],
    "coloring_page":      ["Coloring Page", "Coloring Book", "Adult Coloring"],
    "commercial_license": ["Commercial License"],
    "physical_print":     ["Physical Print", "Kawaii Wall Art Print", "Art Print | Printify"],
    "wall_art":           ["Wall Art", "Art Print", "Printable", "Wall Decor",
                           "Gallery Wall", "Nursery"],
}

# Pinterest hashtag sets per category (max ~20 hashtags for best reach)
HASHTAGS = {
    "digital_planner": (
        "#digitalplanner #goodnotes #notabilityapp #ipadplanner #kawaiiplanner "
        "#digitaldownload #planneraddict #plannerlife #goodnotes6 #digitalplanning "
        "#kawaii #instantdownload #fillableplanner #plannerinspo"
    ),
    "svg_bundle": (
        "#svgfiles #cricutdesigns #silhouettecameo #svgbundle #cricutmaker "
        "#cricutcrafts #cutfiles #svgdesigns #instantdownload #cricutcommunity "
        "#svgcricut #diycrafts"
    ),
    "sticker_pack": (
        "#digitalstickers #goodnotesstickers #kawaiistickers #plannersstickers "
        "#goodnotesapp #digitalplanning #stickerpack #kawaii #ipadstickers "
        "#planneraddict #digitaldownload #instantdownload"
    ),
    "wall_art": (
        "#printableart #wallart #instantdownload #homedecor #gallerywall "
        "#printablewalldecor #digitaldownload #walldecor #printables "
        "#homedecorideas #artprint #bohodecor"
    ),
    "commercial_license": (
        "#commerciallicense #svglicense #smallbusiness #cricutbusiness "
        "#digitalproducts #etsynseller #craftbusiness #resellrights"
    ),
    "coloring_page": (
        "#coloringpage #adultcoloring #printablecoloring #coloringbook "
        "#instantdownload #coloringpages #coloringforadults #digitaldownload"
    ),
    "physical_print": (
        "#wallart #kawaiiart #artprint #homedecor #gallerywall "
        "#kawaii #walldecor #printedart #homedecorideas #artprints"
    ),
}

PIN_DESCRIPTIONS = {
    "digital_planner": (
        "🌸 {title} — Fillable PDF digital planner for GoodNotes 6 and Notability. "
        "Includes dated 2026 version + undated evergreen version + 200+ kawaii stickers. "
        "Works on iPad, iPhone, and Mac. Instant download from Etsy. "
        "Perfect for planner lovers who want a cute, organized life! "
        "{hashtags}"
    ),
    "svg_bundle": (
        "✂️ {title} — Ready-to-cut SVG files for Cricut, Silhouette, and all major cutting machines. "
        "Includes SVG, PNG, DXF, and EPS formats. Instant download. "
        "Perfect for DIY crafts, t-shirts, tumblers, and more! "
        "{hashtags}"
    ),
    "sticker_pack": (
        "✨ {title} — 200+ kawaii digital stickers, GoodNotes Elements ready. "
        "Includes PNG sheets + individual stickers with transparent backgrounds. "
        "Works in GoodNotes 6, Notability, PDF Expert, and Xodo. Instant download! "
        "{hashtags}"
    ),
    "wall_art": (
        "🎨 {title} — Printable wall art instant download. "
        "Multiple sizes included: 4x6, 8x10, 8x12, 16x20, A4, A3. "
        "Print at home or at any print shop. "
        "Makes a beautiful gallery wall addition! "
        "{hashtags}"
    ),
    "commercial_license": (
        "💼 {title} — Commercial license for use in your own products and resale. "
        "Use in your Cricut business, Etsy shop, or print-on-demand products. "
        "Instant download. Perfect for small business owners and crafters. "
        "{hashtags}"
    ),
    "coloring_page": (
        "🖍️ {title} — Printable coloring page for adults and kids. "
        "Instant download — print as many times as you like! "
        "Great for stress relief, mindfulness, and creative relaxation. "
        "{hashtags}"
    ),
    "physical_print": (
        "🖼️ {title} — Premium art print shipped directly to your door. "
        "Printed on high-quality paper with vibrant colors. "
        "Ready to frame — perfect for gallery walls and home decor! "
        "{hashtags}"
    ),
}

CSV_COLUMNS = [
    "listing_id", "pin_title", "pin_description", "board", "image_url",
    "etsy_url", "category", "listing_title",
]


def categorize(listing: dict) -> str:
    title = listing.get("title", "")
    desc  = (listing.get("description") or "")
    text  = (title + " " + desc).lower()
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if any(kw.lower() in text for kw in keywords):
            return cat
    return "wall_art"


def make_pin_title(listing: dict, category: str) -> str:
    title = (listing.get("title") or "")
    # Pinterest pin titles max 100 chars
    if len(title) <= 100:
        return title
    # Trim at word boundary
    trimmed = title[:97].rsplit(" ", 1)[0]
    return trimmed + "..."


def make_pin_description(listing: dict, category: str) -> str:
    template = PIN_DESCRIPTIONS.get(category, PIN_DESCRIPTIONS["wall_art"])
    title    = (listing.get("title") or "")[:80]
    hashtags = HASHTAGS.get(category, "")
    desc     = template.format(title=title, hashtags=hashtags)
    # Pinterest max 500 chars
    if len(desc) > 500:
        # trim before hashtags, re-add
        main = template.format(title=title, hashtags="").strip()
        if len(main) > 450:
            main = main[:447] + "..."
        desc = main + "\n" + hashtags
        if len(desc) > 500:
            desc = desc[:497] + "..."
    return desc


def get_best_image(listing: dict) -> str:
    images = listing.get("images") or []
    if not images:
        return ""
    # Prefer rank 1
    sorted_imgs = sorted(images, key=lambda x: x.get("rank", 99))
    return sorted_imgs[0].get("url_fullxfull", "")


def etsy_url(listing: dict) -> str:
    return f"https://www.etsy.com/listing/{listing['listing_id']}"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"queued_ids": [], "posted_ids": [], "last_generated": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def build_queue(listings: list[dict], new_only: bool = False,
                board_filter: str = "") -> list[dict]:
    state     = load_state()
    queued    = set(state.get("queued_ids", []))
    posted    = set(state.get("posted_ids", []))
    skip_ids  = queued | posted if new_only else set()

    pins = []
    for l in listings:
        lid = l["listing_id"]
        if lid in skip_ids:
            continue

        category = categorize(l)
        board    = BOARDS.get(category, "Printable Wall Art — Instant Download")

        if board_filter and board_filter.lower() not in board.lower():
            continue

        image = get_best_image(l)
        if not image:
            continue  # skip listings with no images

        pin = {
            "listing_id":    lid,
            "listing_title": (l.get("title") or "")[:80],
            "category":      category,
            "board":         board,
            "pin_title":     make_pin_title(l, category),
            "pin_description": make_pin_description(l, category),
            "image_url":     image,
            "etsy_url":      etsy_url(l),
        }
        pins.append(pin)

    return pins


def write_csv(pins: list[dict]) -> None:
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(pins)


def write_json(pins: list[dict]) -> None:
    # Format as Pinterest API v5 payloads
    api_payloads = []
    for pin in pins:
        api_payloads.append({
            "board_id":   f"<BOARD_ID_FOR: {pin['board']}>",  # fill after boards are created
            "title":      pin["pin_title"],
            "description": pin["pin_description"],
            "media_source": {
                "source_type": "image_url",
                "url":         pin["image_url"],
            },
            "link":       pin["etsy_url"],
            "_meta": {
                "listing_id":    pin["listing_id"],
                "listing_title": pin["listing_title"],
                "category":      pin["category"],
                "board_name":    pin["board"],
            },
        })
    OUTPUT_JSON.write_text(json.dumps(api_payloads, indent=2))


def cmd_status() -> None:
    state = load_state()
    print(f"Queued (not yet posted): {len(state.get('queued_ids', []))}")
    print(f"Posted:                  {len(state.get('posted_ids', []))}")
    print(f"Last generated:          {state.get('last_generated', 'never')}")

    if OUTPUT_CSV.exists():
        with open(OUTPUT_CSV) as f:
            rows = list(csv.DictReader(f))
        board_counts: dict[str, int] = {}
        for r in rows:
            board_counts[r.get("board", "?")] = board_counts.get(r.get("board", "?"), 0) + 1
        print(f"\nCurrent queue ({len(rows)} pins):")
        for board, count in sorted(board_counts.items(), key=lambda x: -x[1]):
            print(f"  {count:3d}  {board}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate Pinterest pin queue")
    parser.add_argument("--new-only", action="store_true",
                        help="Only include listings not already in queue")
    parser.add_argument("--board",    default="",
                        help="Filter to a single board name (partial match)")
    parser.add_argument("--status",   action="store_true",
                        help="Show queue statistics")
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

    print("Fetching active listings...")
    listings = client.get_shop_listings_all(state="active")
    print(f"Found {len(listings)} listings")

    pins = build_queue(listings, new_only=args.new_only, board_filter=args.board)
    print(f"Generated {len(pins)} pins\n")

    write_csv(pins)
    write_json(pins)

    # Update state
    state = load_state()
    state["queued_ids"] = list(set(state.get("queued_ids", [])) | {p["listing_id"] for p in pins})
    state["last_generated"] = date.today().isoformat()
    save_state(state)

    print(f"Saved:")
    print(f"  {OUTPUT_CSV}  ← open in Excel/Sheets for easy copy-paste posting")
    print(f"  {OUTPUT_JSON} ← API payloads ready for when Pinterest app is approved")

    # Board breakdown
    board_counts: dict[str, int] = {}
    for p in pins:
        board_counts[p["board"]] = board_counts.get(p["board"], 0) + 1
    print("\nPins by board:")
    for board, count in sorted(board_counts.items(), key=lambda x: -x[1]):
        print(f"  {count:3d}  {board}")

    print("\nNext step: go to Pinterest, open each board, and post the pins from the CSV.")
    print("Once the Pinterest developer app is approved, run tools/pinterest_api.py to post automatically.")


if __name__ == "__main__":
    main()
