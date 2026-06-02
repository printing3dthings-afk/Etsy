#!/usr/bin/env python3
"""
printify_publisher.py

Connects existing wall art files to Printify for physical print-on-demand.
Buyer orders on Etsy → Printify auto-prints and ships → zero inventory needed.

Setup (one time):
  1. Create free account at printify.com
  2. Go to My Profile → Connections → API → Generate Token
  3. Add to .env: PRINTIFY_API_KEY=<your_token>
  4. Run: python tools/printify_publisher.py --submit-all

Usage:
  python tools/printify_publisher.py --queue           # build/show submission queue
  python tools/printify_publisher.py --status          # check API connection
  python tools/printify_publisher.py --submit DP1000   # submit one product
  python tools/printify_publisher.py --submit-all      # submit entire queue
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE))

QUEUE_FILE = BASE / "data" / "printify" / "products_queue.json"
GUIDE_FILE = BASE / "data" / "printify" / "printify_setup_guide.md"

# Printify poster blueprint IDs (standard open-edition posters)
# Blueprint 461 = "Enhanced Matte Paper Poster" — most popular for wall art
POSTER_BLUEPRINT_ID = 461
# Print provider 99 = Printify Choice (auto-selects best available)
DEFAULT_PRINT_PROVIDER = 99

# Pricing per size (Printify cost → our Etsy price → our profit)
PRINT_SIZES = [
    {"label": '8"×10"',  "width_px": 2400, "height_px": 3000, "cost": 8.45,  "price": 19.99},
    {"label": '12"×16"', "width_px": 3600, "height_px": 4800, "cost": 12.25, "price": 27.99},
    {"label": '18"×24"', "width_px": 5400, "height_px": 7200, "cost": 17.80, "price": 39.99},
]


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


def _printify_request(
    method: str, path: str, api_key: str, body: dict | None = None
) -> dict:
    url = f"https://api.printify.com/v1/{path.lstrip('/')}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OnBrandCraftz/1.0",
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body_text = e.read().decode(errors="replace")
        raise RuntimeError(f"Printify API {e.code}: {body_text[:300]}") from e


def find_wall_art_files() -> list[dict]:
    """Scan product_files for wall art source images."""
    product_dir = BASE / "data" / "digital_products" / "product_files"
    SKIP = {"_listing", "_sticker", "_mockup", "_kawaii", "_room", "_size",
            "_detail", "_cover", "_sheet", "_preview", "_allsizes", "_upscaled"}
    results = []
    for f in sorted(product_dir.glob("DP*.jpg")) + sorted(product_dir.glob("DP*.png")):
        if any(s in f.name for s in SKIP):
            continue
        product_id = f.stem
        results.append({
            "product_id": product_id,
            "file_path": str(f),
            "file_name": f.name,
        })
    return results


def build_queue() -> list[dict]:
    """Build a submission queue from existing wall art files."""
    files = find_wall_art_files()
    queue = []
    for item in files:
        product_id = item["product_id"]
        # Build Etsy listing title
        title = f"Printable Wall Art Print — {product_id} | Physical Poster | Multiple Sizes"
        tags = [
            "wall art print",
            "physical poster",
            "wall decor",
            "printable art",
            "poster print",
            "wall hanging",
            "home decor",
            "art print gift",
            "framed wall art",
            "modern wall art",
            "gallery wall",
            "room decor",
            "art poster",
        ]
        entry = {
            "product_id": product_id,
            "file_path": item["file_path"],
            "etsy_title": title[:140],
            "etsy_tags": tags[:13],
            "variants": PRINT_SIZES,
            "blueprint_id": POSTER_BLUEPRINT_ID,
            "print_provider_id": DEFAULT_PRINT_PROVIDER,
            "status": "queued",
            "printify_product_id": None,
        }
        queue.append(entry)
    return queue


def save_queue(queue: list[dict]) -> None:
    QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_FILE.write_text(json.dumps(queue, indent=2))


def load_queue() -> list[dict]:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return build_queue()


def check_status(api_key: str) -> None:
    print("Checking Printify API connection...")
    try:
        shops = _printify_request("GET", "shops.json", api_key)
        print(f"  ✓ Connected. Shops: {[s.get('title') for s in shops]}")
    except RuntimeError as e:
        print(f"  ✗ Connection failed: {e}")


def submit_product(item: dict, shop_id: str, api_key: str) -> str | None:
    """Submit one product to Printify. Returns Printify product ID or None."""
    product_id = item["product_id"]
    file_path = item["file_path"]
    print(f"\n  Submitting {product_id} ({Path(file_path).name})...")

    # Step 1: Upload image to Printify
    try:
        import base64
        img_data = Path(file_path).read_bytes()
        encoded = base64.b64encode(img_data).decode()
        upload_resp = _printify_request(
            "POST",
            "uploads/images.json",
            api_key,
            {"file_name": Path(file_path).name, "contents": encoded},
        )
        image_id = upload_resp.get("id")
        if not image_id:
            print(f"    ✗ Image upload failed: {upload_resp}")
            return None
        print(f"    ✓ Image uploaded: {image_id}")
        time.sleep(0.5)
    except Exception as e:
        print(f"    ✗ Image upload error: {e}")
        return None

    # Step 2: Create product
    variants = []
    for size in PRINT_SIZES:
        variants.append({
            "id": size["label"],
            "price": int(size["price"] * 100),  # Printify expects cents
            "is_enabled": True,
        })

    product_body = {
        "title": item["etsy_title"],
        "description": (
            f"High-quality physical art print — {product_id}.\n\n"
            "Printed on premium enhanced matte paper. Available in multiple sizes.\n"
            "Ships within 2–5 business days. Free shipping available.\n\n"
            "Printed and fulfilled by Printify's network of professional print providers."
        ),
        "blueprint_id": item["blueprint_id"],
        "print_provider_id": item["print_provider_id"],
        "variants": variants,
        "print_areas": [
            {
                "variant_ids": [v["id"] for v in variants],
                "placeholders": [{"position": "front", "images": [{"id": image_id, "x": 0.5, "y": 0.5, "scale": 1, "angle": 0}]}],
            }
        ],
    }

    try:
        result = _printify_request(
            "POST", f"shops/{shop_id}/products.json", api_key, product_body
        )
        printify_id = result.get("id")
        print(f"    ✓ Product created: {printify_id}")
        return printify_id
    except Exception as e:
        print(f"    ✗ Product creation failed: {e}")
        return None


def write_setup_guide() -> None:
    guide = """# Printify Setup Guide — OnBrandCraftz

## Step 1: Create Your Printify Account
1. Go to printify.com
2. Click "Get started for free"
3. Sign up with your email (Printing3dthings@outlook.com)
4. Complete your profile

## Step 2: Generate Your API Key
1. Click your profile icon (top right)
2. Go to "My Profile" → "Connections"
3. Click "API" tab
4. Click "Generate new token"
5. Copy the token

## Step 3: Add API Key to .env
Open your .env file and add:
```
PRINTIFY_API_KEY=your_token_here
```

## Step 4: Connect Your Etsy Store
1. In Printify, go to "My Stores"
2. Click "Add new store"
3. Select "Etsy"
4. Authorize the connection

## Step 5: Submit Your Products
```bash
python tools/printify_publisher.py --status       # verify connection
python tools/printify_publisher.py --submit-all   # submit all 55 wall art prints
```

## What Happens When an Order Comes In
1. Customer orders on Etsy
2. Printify receives the order automatically (via Etsy integration)
3. Printify prints and ships directly to customer
4. You receive Etsy payment minus Printify cost
5. You never touch the order

## Pricing Reference
| Size | Printify Cost | Your Etsy Price | Your Profit |
|------|--------------|-----------------|-------------|
| 8×10" | $8.45 | $19.99 | ~$9.00 |
| 12×16" | $12.25 | $27.99 | ~$12.00 |
| 18×24" | $17.80 | $39.99 | ~$18.00 |

Note: Etsy also charges 6.5% transaction fee + $0.20 listing fee.
Net profit after all fees: ~$7–15 per sale depending on size.

## Products Ready to Submit
See: data/printify/products_queue.json
55 wall art files are queued and ready.
"""
    GUIDE_FILE.parent.mkdir(parents=True, exist_ok=True)
    GUIDE_FILE.write_text(guide)
    print(f"  Setup guide written: {GUIDE_FILE.relative_to(BASE)}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Printify POD integration")
    parser.add_argument("--queue", action="store_true", help="Build/show submission queue")
    parser.add_argument("--status", action="store_true", help="Check API connection")
    parser.add_argument("--submit", metavar="PRODUCT_ID", help="Submit one product")
    parser.add_argument("--submit-all", action="store_true", help="Submit all queued products")
    args = parser.parse_args()

    env = _parse_env()
    api_key = env.get("PRINTIFY_API_KEY", "")

    # Always build and save the queue
    queue = build_queue()
    save_queue(queue)
    write_setup_guide()

    if args.queue or (not args.status and not args.submit and not args.submit_all):
        print(f"\nPrintify submission queue: {len(queue)} products")
        print(f"{'Product ID':<15} {'File':<30} {'Status'}")
        print("-" * 65)
        for item in queue[:20]:
            print(f"{item['product_id']:<15} {Path(item['file_path']).name:<30} {item['status']}")
        if len(queue) > 20:
            print(f"  ... and {len(queue) - 20} more")
        print(f"\nFull queue: {QUEUE_FILE.relative_to(BASE)}")
        print(f"Setup guide: {GUIDE_FILE.relative_to(BASE)}")
        if not api_key:
            print("\n⚠️  PRINTIFY_API_KEY not set in .env")
            print("   See data/printify/printify_setup_guide.md for setup steps.")
        return

    if not api_key:
        print("ERROR: PRINTIFY_API_KEY not set in .env")
        print("See data/printify/printify_setup_guide.md for setup steps.")
        sys.exit(1)

    if args.status:
        check_status(api_key)
        return

    # Get shop ID
    try:
        shops = _printify_request("GET", "shops.json", api_key)
        if not shops:
            print("No shops found. Connect your Etsy store in Printify first.")
            sys.exit(1)
        shop_id = shops[0]["id"]
        print(f"Using shop: {shops[0].get('title')} (ID: {shop_id})")
    except RuntimeError as e:
        print(f"Failed to get shops: {e}")
        sys.exit(1)

    queue = load_queue()

    if args.submit:
        items = [i for i in queue if i["product_id"] == args.submit]
        if not items:
            print(f"Product '{args.submit}' not found in queue.")
            sys.exit(1)
        submit_product(items[0], shop_id, api_key)
        return

    if args.submit_all:
        submitted = 0
        for item in queue:
            if item["status"] == "submitted":
                print(f"  Skipping {item['product_id']} — already submitted")
                continue
            printify_id = submit_product(item, shop_id, api_key)
            if printify_id:
                item["status"] = "submitted"
                item["printify_product_id"] = printify_id
                submitted += 1
                save_queue(queue)
            time.sleep(1)  # rate limit

        print(f"\nSubmitted {submitted} products to Printify.")
        print("Log in to printify.com to publish them to your Etsy store.")


if __name__ == "__main__":
    main()
