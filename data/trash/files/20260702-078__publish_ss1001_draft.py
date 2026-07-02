#!/usr/bin/env python3
"""
publish_ss1001_draft.py — Create the SS1001 America 250 sign pack as an Etsy DRAFT.

Creates the listing in draft state, uploads all 10 photos and both customer ZIPs
(Vol 1 + Vol 2). NEVER activates the listing — Scott publishes from Shop Manager.

Usage:
  python tools/publish_ss1001_draft.py --dry-run   # gate check + plan, no API calls
  python tools/publish_ss1001_draft.py             # create the draft
"""

import re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

BASE     = Path("data/3d_print_signs/america_250")
PHOTO_DIR = BASE / "listing_photos" / "final_v2"
ZIP_VOL1 = BASE / "SS1001_america250_3dprint_pack_vol1.zip"
ZIP_VOL2 = BASE / "SS1001_america250_3dprint_pack_vol2.zip"

TITLE = "America 250 SVG, 10 Patriotic 3D Print Signs, Instant Download"

TAGS = [
    "patriotic svg files", "3d print svg", "250th anniversary",
    "bambu studio svg", "wall sign svg", "patriotic wall decor",
    "4th of july sign", "svg cut file", "america sign svg",
    "printable sign", "patriotic decor", "3d wall sign", "digital download",
]

PHOTOS = [PHOTO_DIR / f"photo_{str(i).zfill(2)}_{name}.jpg" for i, name in [
    (1,  "hero_gallery_wall"),
    (2,  "mantel_sign"),
    (3,  "porch_sign"),
    (4,  "tieredtray_sign"),
    (5,  "yard_sign"),
    (6,  "collection_overview"),
    (7,  "bambu_howto"),
    (8,  "detail_closeup"),
    (9,  "whats_included"),
    (10, "design_lineup"),
]]


def load_description() -> str:
    """Pull the DESCRIPTION block out of SS1001_listing_content.md."""
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
        "price": 14.99,
        "quantity": 999,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "taxonomy_id": 2078,
        "tags": TAGS,
        "materials": ["digital download", "SVG file", "3MF file"],
        "state": "draft",
        "type": "download",
    }

    # Pre-flight: all files must exist
    required = PHOTOS + [ZIP_VOL1, ZIP_VOL2]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing files:\n" + "\n".join(f"  ✗ {p}" for p in missing))

    failures = EtsyAPIClient.pre_publish_gate(listing_body)
    if failures:
        raise SystemExit("Quality gate FAILED:\n" + "\n".join(f"  ✗ {f}" for f in failures))

    print(f"✓ Quality gate passed")
    print(f"  Title: {len(TITLE)} chars | Price: $14.99 | Tags: {len(TAGS)} | "
          f"Desc: {len(description)} chars")
    print(f"  Vol 1 ZIP: {ZIP_VOL1.stat().st_size // 1024} KB")
    print(f"  Vol 2 ZIP: {ZIP_VOL2.stat().st_size // 1024} KB")

    if dry_run:
        print("\n[DRY RUN] Would create DRAFT listing:")
        print(f"  Title: {TITLE}")
        print(f"  Price: $14.99 | taxonomy 2078 | type download | state draft")
        for i, p in enumerate(PHOTOS, 1):
            print(f"  Photo {i:02d}: {p.name}")
        print(f"  Digital file 1: {ZIP_VOL1.name}")
        print(f"  Digital file 2: {ZIP_VOL2.name}")
        return

    from dotenv import load_dotenv
    load_dotenv()
    c = EtsyAPIClient()

    resp = c.create_listing(listing_body)
    lid = resp["listing_id"]
    print(f"\n✓ Draft listing created: listing_id={lid}")
    print(f"  https://www.etsy.com/listing/{lid}")

    for rank, photo in enumerate(PHOTOS, start=1):
        c.upload_listing_image(lid, str(photo), rank=rank)
        print(f"  ✓ Photo {rank:02d}/10: {photo.name}")
        time.sleep(2.0)  # avoid duplicate-rank race (CLAUDE.md API quirk)

    c.upload_listing_file(lid, str(ZIP_VOL1), rank=1)
    print(f"  ✓ Digital file 1: {ZIP_VOL1.name}")
    time.sleep(1.0)

    c.upload_listing_file(lid, str(ZIP_VOL2), rank=2)
    print(f"  ✓ Digital file 2: {ZIP_VOL2.name}")

    print(f"\nDONE — listing {lid} is in DRAFT state.")
    print("Go to: Etsy Shop Manager → Listings → Drafts → review → Publish")


if __name__ == "__main__":
    main()
