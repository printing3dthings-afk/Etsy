#!/usr/bin/env python3
"""
commercial_license_tool.py

Creates "Commercial Use License" companion listings for every SVG bundle and
sticker pack. Buyers who want to use designs in products they sell need a
commercial license — they pay 8x the personal use price.

Commercial license covers:
  - Use in physical products for resale (up to 500 units/year)
  - Use in digital products for resale
  - Does NOT cover reselling the original files or sublicensing

Usage:
  python tools/commercial_license_tool.py --list        # show what would be created
  python tools/commercial_license_tool.py --create      # create draft listings on Etsy
  python tools/commercial_license_tool.py --create-one SVG_FLORAL
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

from tools.etsy_api import EtsyAPIClient, EtsyAPIError


def _parse_env() -> dict[str, str]:
    env: dict[str, str] = {}
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


def _load_catalog() -> list[dict]:
    path = BASE / "data" / "product_catalog.json"
    if not path.exists():
        return []
    data = json.loads(path.read_text())
    return data if isinstance(data, list) else data.get("products", [])


def _save_catalog(products: list[dict]) -> None:
    path = BASE / "data" / "product_catalog.json"
    path.write_text(json.dumps(products, indent=2))


COMMERCIAL_DESCRIPTION_TEMPLATE = """{hook}

🛡️ This listing is for a COMMERCIAL USE LICENSE for the {product_name}.

━━━━━━━━━━━━━━━━━━━━━━━━
📋 WHAT THIS LICENSE COVERS
━━━━━━━━━━━━━━━━━━━━━━━━
✅ Use in physical products you sell (T-shirts, mugs, tote bags, tumblers, decals, etc.)
✅ Use in digital products you sell (stickers, digital planners, printables)
✅ Use in small business marketing materials (up to 500 units/year per design)
✅ Use in your Etsy shop, craft fair booth, or small online store
✅ Multiple projects — use any design from this bundle in as many projects as you want

━━━━━━━━━━━━━━━━━━━━━━━━
❌ WHAT IS NOT INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✗ Reselling or redistributing the original design files
✗ Claiming the designs as your own original work
✗ Sublicensing to other designers
✗ Mass production over 500 units (contact us for an extended license)
✗ Use in print-on-demand platforms that resell the base design files

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
You receive the same files as the personal use listing PLUS this commercial license certificate.
{files_included}

━━━━━━━━━━━━━━━━━━━━━━━━
📥 HOW IT WORKS
━━━━━━━━━━━━━━━━━━━━━━━━
1. Purchase this commercial license listing
2. Purchase the personal use listing (linked in the description above) to receive the files
3. Your license is valid immediately — no approval process needed
4. Save your Etsy order confirmation as your license proof

━━━━━━━━━━━━━━━━━━━━━━━━
💡 DO I NEED A COMMERCIAL LICENSE?
━━━━━━━━━━━━━━━━━━━━━━━━
✅ YES if: You sell finished products (mugs, shirts, tumblers, stickers) using these designs
✅ YES if: You use these designs in digital products you sell on Etsy or your own shop
❌ NO if: You're using these designs for personal projects, gifts, or items you give away

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: Do I need to buy both this listing AND the regular listing?
A: Yes — this listing is the license only. Purchase the regular listing for the design files.

Q: Can I use this for my Etsy shop?
A: Yes! This license is perfect for small Etsy sellers selling finished products.

Q: Is there a limit to how many items I can make?
A: Up to 500 units per design per year. Need more? Message us for extended licensing.

Q: How do I prove I have a license?
A: Your Etsy order confirmation is your license proof. Save it.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Commercial license valid for buyer only. Not transferable.
"""

# Products eligible for commercial license
ELIGIBLE_CATEGORIES = {"svg_bundle", "sticker_pack"}

PRODUCT_HOOKS = {
    "svg_bundle": "Turn these SVG designs into products you sell — with the official OnBrandCraftz Commercial Use License!",
    "sticker_pack": "Use these kawaii sticker designs in products you create and sell — with full commercial licensing coverage!",
}

FILES_INCLUDED = {
    "svg_bundle": "• SVG files (Cricut/Silhouette compatible)\n• PNG files (transparent background)\n• DXF files\n• EPS files\n• All designs in the bundle",
    "sticker_pack": "• PNG sticker sheets (transparent background)\n• Individual sticker PNG files\n• GoodNotes sticker book (.goodnotes)\n• All 5 sticker sheets (200+ stickers)",
}


def get_eligible_products() -> list[dict]:
    products = _load_catalog()
    eligible = []
    for p in products:
        if p.get("category") in ELIGIBLE_CATEGORIES:
            eligible.append(p)
    return eligible


COMMERCIAL_PRICES = {
    "svg_bundle": 24.99,    # market rate: $15-35 for SVG commercial license
    "sticker_pack": 12.99,  # market rate: $8-15 for sticker commercial license
}


def build_commercial_listing(product: dict) -> dict:
    """Build listing data dict for a commercial license listing."""
    category = product.get("category", "svg_bundle")
    personal_price = float(product.get("price", 9.99))
    commercial_price = COMMERCIAL_PRICES.get(category, round(personal_price * 4, 2))
    if personal_price == 0:
        return {}  # skip free products

    product_name = product.get("name", product.get("product_id", "Design Bundle"))
    base_title = product_name.replace(" — ", " ").replace(" | ", " ")
    # Keep title under 70 chars for mobile ranking; must include "Instant Download"
    suffix = " | Instant Download"
    prefix = "Commercial License | "
    available = 70 - len(prefix) - len(suffix)
    truncated = base_title[:available] if len(base_title) > available else base_title
    title = f"{prefix}{truncated}{suffix}"

    hook = PRODUCT_HOOKS.get(category, "Use these designs commercially with full licensing coverage!")
    files = FILES_INCLUDED.get(category, "• All files from the personal use listing")

    description = COMMERCIAL_DESCRIPTION_TEMPLATE.format(
        hook=hook,
        product_name=product_name,
        files_included=files,
    )

    # Tags — no tag may duplicate title phrase, all ≤20 chars
    if category == "svg_bundle":
        tags = [
            "svg commercial use",   # 18
            "commercial svg",       # 14
            "svg license",          # 11
            "svg bundle license",   # 18
            "cricut commercial",    # 18
            "resell license",       # 15
            "commercial rights",    # 18
            "business license",     # 16
            "svg resell rights",    # 18
            "digital download",     # 16
            "commercial use svg",   # 19
            "cricut svg files",     # 16
            "craft seller",         # 13
        ]
    else:
        tags = [
            "sticker license",      # 15
            "commercial use png",   # 19
            "commercial rights",    # 18
            "resell license",       # 15
            "kawaii commercial",    # 18
            "sticker resell",       # 14
            "business license",     # 16
            "png commercial",       # 15
            "digital use rights",   # 19
            "digital download",     # 16
            "commercial sticker",   # 19
            "craft business",       # 14
            "craft seller",         # 13
        ]

    return {
        "title": title,
        "description": description,
        "price": commercial_price,
        "quantity": 999,
        "tags": tags[:13],
        "taxonomy_id": 2078,  # Digital Files
        "type": "download",
        "is_digital": True,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "_source_product_id": product.get("product_id"),
        "_source_listing_id": product.get("etsy_listing_id"),
        "_personal_price": personal_price,
        "_commercial_price": commercial_price,
    }


def list_candidates() -> None:
    products = get_eligible_products()
    print(f"\nCommercial license candidates ({len(products)} products):\n")
    print(f"{'Product ID':<20} {'Category':<15} {'Personal $':<12} {'License $':<12} {'Name'}")
    print("-" * 85)
    for p in products:
        personal = float(p.get("price", 9.99))
        cat = p.get("category", "svg_bundle")
        commercial = COMMERCIAL_PRICES.get(cat, round(personal * 4, 2)) if personal > 0 else 0
        print(f"{p.get('product_id','?'):<20} {cat:<15} ${personal:<11.2f} ${commercial:<11.2f} {p.get('name','')[:40]}")
    print(f"\nNote: Products without an Etsy listing ID (✗) will create a new draft.")


def create_license_listing(product: dict, client: EtsyAPIClient, dry_run: bool = False) -> dict | None:
    listing_data = build_commercial_listing(product)
    product_id = product.get("product_id", "?")

    print(f"\n  Creating commercial license for {product_id}...")
    print(f"  Title: {listing_data['title']}")
    print(f"  Price: ${listing_data['_commercial_price']:.2f} (personal: ${listing_data['_personal_price']:.2f})")

    if dry_run:
        print("  [DRY RUN — not submitted]")
        return listing_data

    # Remove internal _ keys before submitting
    submit_data = {k: v for k, v in listing_data.items() if not k.startswith("_")}
    submit_data["state"] = "draft"

    try:
        result = client.create_listing(submit_data)
        listing_id = result.get("listing_id")
        print(f"  ✓ Draft created: listing_id={listing_id}")

        # Record in catalog
        products = _load_catalog()
        new_entry = {
            "product_id": f"LICENSE_{product_id}",
            "name": listing_data["title"],
            "etsy_listing_id": str(listing_id) if listing_id else "",
            "price": listing_data["_commercial_price"],
            "category": f"{product.get('category','')}_license",
            "status": "draft",
            "source_product_id": product_id,
            "last_updated": str(__import__("datetime").date.today()),
        }
        products.append(new_entry)
        _save_catalog(products)
        return result

    except EtsyAPIError as e:
        print(f"  ✗ Failed: {e}")
        return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Commercial license listing creator")
    parser.add_argument("--list", action="store_true", help="Show eligible products")
    parser.add_argument("--create", action="store_true", help="Create draft listings for all eligible products")
    parser.add_argument("--create-one", metavar="PRODUCT_ID", help="Create draft for one product")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created without submitting")
    args = parser.parse_args()

    if args.list or (not args.create and not args.create_one):
        list_candidates()
        return

    client = EtsyAPIClient()
    products = get_eligible_products()

    if args.create_one:
        products = [p for p in products if p.get("product_id") == args.create_one]
        if not products:
            print(f"Product '{args.create_one}' not found or not eligible.")
            sys.exit(1)

    created = 0
    for product in products:
        if float(product.get("price", 0)) == 0:
            print(f"\n  Skipping {product.get('product_id')} — free product, no commercial license needed.")
            continue
        result = create_license_listing(product, client, dry_run=args.dry_run)
        if result:
            created += 1

    print(f"\n{'Would create' if args.dry_run else 'Created'} {created} commercial license listings.")
    if not args.dry_run and created:
        print("Listings are in DRAFT state — review in Etsy Shop Manager before publishing.")


if __name__ == "__main__":
    main()
