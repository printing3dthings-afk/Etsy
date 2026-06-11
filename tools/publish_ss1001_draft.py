#!/usr/bin/env python3
"""
publish_ss1001_draft.py — Create the SS1001 America 250 sign pack as an Etsy DRAFT.

Creates the listing in draft state, uploads all 10 photos (badged lifestyle
versions for slots 1-6) and the SVG pack ZIP. NEVER activates the listing —
Scott publishes from Shop Manager after a final look.

Usage:
  python tools/publish_ss1001_draft.py --dry-run   # gate check + plan, no API calls
  python tools/publish_ss1001_draft.py             # create the draft
"""

import re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

BASE   = Path("data/3d_print_signs/america_250")
FINAL  = BASE / "listing_photos/final"
BADGED = FINAL / "badged"
ZIP    = BASE / "SS1001_america250_signs_SVG_pack.zip"

TITLE = "America 250 Sign SVG, 3D Print Patriotic Signs, Instant Download"

TAGS = [
    "patriotic svg files", "3d print svg", "250th anniversary",
    "bambu studio svg", "wall sign svg", "patriotic wall decor",
    "4th of july sign", "svg cut file", "america sign svg",
    "printable sign", "patriotic decor", "3d wall sign", "digital download",
]

PHOTOS = [
    BADGED / "photo_01_hero_gallery_wall.jpg",
    BADGED / "photo_02_porch_sign.jpg",
    BADGED / "photo_03_mantel_sign.jpg",
    BADGED / "photo_04_tieredtray_sign.jpg",
    BADGED / "photo_05_yard_sign.jpg",
    BADGED / "photo_06_collection_overview.jpg",
    FINAL  / "photo_07_bambu_howto.jpg",
    FINAL  / "photo_08_detail_closeup.jpg",
    FINAL  / "photo_09_whats_included.jpg",
    FINAL  / "photo_10_design_lineup.jpg",
]


def load_description() -> str:
    """Pull the DESCRIPTION block out of SS1001_listing_content.md (source of truth)."""
    md = (BASE / "SS1001_listing_content.md").read_text()
    m = re.search(r"### DESCRIPTION\n\n(.*?)\n---\n\n## LISTING PHOTOS PLAN", md, re.S)
    if not m:
        raise SystemExit("Could not extract DESCRIPTION from SS1001_listing_content.md")
    return m.group(1).strip()


def main():
    dry_run = "--dry-run" in sys.argv

    description = load_description()
    listing_body = {
        "title": TITLE,
        "description": description,
        "price": 9.99,
        "quantity": 999,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "taxonomy_id": 2078,
        "tags": TAGS,
        "materials": ["digital download", "SVG file"],
        "state": "draft",
        "type": "download",
    }

    # Pre-flight: files exist, gate passes
    missing = [p for p in PHOTOS + [ZIP] if not p.exists()]
    if missing:
        raise SystemExit("Missing files:\n" + "\n".join(f"  ✗ {p}" for p in missing))

    failures = EtsyAPIClient.pre_publish_gate(listing_body)
    if failures:
        raise SystemExit("Quality gate FAILED:\n" + "\n".join(f"  ✗ {f}" for f in failures))
    print(f"✓ Quality gate passed — title {len(TITLE)} chars, {len(TAGS)} tags, "
          f"desc {len(description)} chars, ZIP {ZIP.stat().st_size // 1024} KB")

    if dry_run:
        print("\n[DRY RUN] Would create DRAFT listing:")
        print(f"  Title: {TITLE}")
        print(f"  Price: $9.99 | taxonomy 2078 | type download | state draft")
        for i, p in enumerate(PHOTOS, 1):
            print(f"  Photo {i}: {p}")
        print(f"  Digital file: {ZIP}")
        return

    from dotenv import load_dotenv
    load_dotenv()
    c = EtsyAPIClient()

    resp = c.create_listing(listing_body)
    lid = resp["listing_id"]
    print(f"✓ Draft listing created: {lid}")
    print(f"  https://www.etsy.com/listing/{lid}")

    for rank, photo in enumerate(PHOTOS, start=1):
        c.upload_listing_image(lid, str(photo), rank=rank)
        print(f"  ✓ Photo {rank}/10: {photo.name}")
        time.sleep(2.0)  # avoid duplicate-rank race (CLAUDE.md API quirk)

    c.upload_listing_file(lid, str(ZIP), rank=1)
    print(f"  ✓ Digital file: {ZIP.name}")

    print(f"\nDONE — listing {lid} is in DRAFT state.")
    print("Scott: review in Shop Manager → Listings → Drafts, then click Publish.")


if __name__ == "__main__":
    main()
