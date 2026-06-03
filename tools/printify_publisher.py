#!/usr/bin/env python3
"""
printify_publisher.py — Printify print-on-demand integration for OnBrandCraftz.

Connects existing wall art files to Printify for physical print-on-demand fulfillment.
Buyer orders on Etsy → Printify auto-prints and ships → Zero inventory needed.

Usage:
    python tools/printify_publisher.py --queue          # build submission queue from all art files
    python tools/printify_publisher.py --status         # check API connection and shop status
    python tools/printify_publisher.py --submit DP1000  # submit one product (needs API key)
    python tools/printify_publisher.py --submit-all     # submit all queued products (needs API key)

Output (always):
    data/printify/products_queue.json    — all art files ready for submission
    data/printify/printify_setup_guide.md — Printify account setup steps

Output (with API key):
    data/printify/submitted_products.json — record of submitted products
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
PRODUCT_FILES_DIR = BASE / "data" / "digital_products" / "product_files"
PRINTIFY_DIR = BASE / "data" / "printify"

# ---------------------------------------------------------------------------
# .env parser — never use load_dotenv()
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Printify API constants
# ---------------------------------------------------------------------------
PRINTIFY_BASE_URL = "https://api.printify.com/v1"

# Poster blueprint IDs on Printify
# Blueprint 804 = "Fine Art Posters" (Print Clever, provider 72) — verified live 2026-06-03
# Variants: 8x10=75288, 12x16=75290, 18x24=100938
BLUEPRINT_POSTER_PRODIGI = 804
BLUEPRINT_POSTER_MATTE = 282  # Matte Vertical Posters (Printify Choice)

# Standard print sizes: width_in, height_in, label, sku_suffix, sell_price, cost_est
PRINT_SIZES = [
    {"width_in": 8,  "height_in": 10, "label": "8x10 in",  "sku_suffix": "8x10",  "sell_price": 19.99, "cost_est": 8.00},
    {"width_in": 12, "height_in": 16, "label": "12x16 in", "sku_suffix": "12x16", "sell_price": 27.99, "cost_est": 12.00},
    {"width_in": 18, "height_in": 24, "label": "18x24 in", "sku_suffix": "18x24", "sell_price": 39.99, "cost_est": 18.00},
]

# DPI / resolution thresholds
MIN_RECOMMENDED_SHORT_EDGE_PX = 2400  # 8in * 300dpi = 2400px

# ---------------------------------------------------------------------------
# Optional PIL import for image inspection
# ---------------------------------------------------------------------------
try:
    from PIL import Image  # type: ignore
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


# ---------------------------------------------------------------------------
# Known product title map (populated for common IDs)
# ---------------------------------------------------------------------------
_KNOWN_TITLES: dict[str, str] = {
    "DP1000": "Boho Botanical Floral",
    "DP1001": "Minimalist Line Art",
    "DP1002": "Abstract Watercolor",
    "DP1003": "Cottagecore Botanical",
    "DP1007": "Kawaii Celestial",
    "DP1008": "Pastel Abstract",
    "DP1009": "Modern Geometric",
    "DP1010": "Watercolor Floral",
    "DP1011": "Boho Mandala",
    "DP1012": "Kawaii Character",
    "DP1013": "Tropical Botanical",
    "DP1014": "Minimalist Typography",
    "DP1015": "Abstract Landscape",
    "DP1016": "Floral Wreath",
    "DP1017": "Kawaii Stationery",
    "DP1018": "Pastel Celestial",
    "DP1019": "Modern Abstract",
    "DP1020": "Botanical Herbs",
    "DP1021": "Kawaii Animals",
    "DP1022": "Boho Dreamcatcher",
    "DP1023": "Wildflower Meadow",
    "DP1024": "Vintage Botanical",
    "DP1025": "Celestial Moon",
}


def _product_title(product_id: str) -> str:
    if product_id in _KNOWN_TITLES:
        return f"{_KNOWN_TITLES[product_id]} Art Print"
    num = product_id.replace("DP", "")
    return f"Kawaii Art Print Design {num}"


# ---------------------------------------------------------------------------
# Art file discovery
# ---------------------------------------------------------------------------
def discover_art_files() -> list[dict[str, Any]]:
    """Discover all base wall art JPG files matching DP1xxx.jpg."""
    pattern = re.compile(r"^(DP1\d+)\.jpg$", re.IGNORECASE)
    art_files = []
    for path in sorted(PRODUCT_FILES_DIR.glob("DP1*.jpg")):
        m = pattern.match(path.name)
        if m:
            art_files.append({
                "product_id": m.group(1).upper(),
                "file_path": str(path),
                "file_name": path.name,
            })
    return art_files


def inspect_image(file_path: Path) -> dict[str, Any]:
    """Inspect a wall art file for print readiness."""
    result: dict[str, Any] = {
        "file": str(file_path),
        "exists": file_path.exists(),
        "size_mb": 0.0,
        "width_px": None,
        "height_px": None,
        "mode": None,
        "ready_for_print": False,
        "needs_upscale": False,
        "pil_available": _PIL_AVAILABLE,
        "issues": [],
        "warnings": [],
    }

    if not file_path.exists():
        result["issues"].append(f"File not found: {file_path}")
        return result

    result["size_mb"] = round(file_path.stat().st_size / (1024 * 1024), 2)

    if _PIL_AVAILABLE:
        try:
            with Image.open(file_path) as img:
                result["width_px"] = img.size[0]
                result["height_px"] = img.size[1]
                result["mode"] = img.mode
                short_edge = min(img.size)
                if short_edge < MIN_RECOMMENDED_SHORT_EDGE_PX:
                    result["needs_upscale"] = True
                    result["warnings"].append(
                        f"Short edge {short_edge}px < {MIN_RECOMMENDED_SHORT_EDGE_PX}px minimum "
                        f"for 300 DPI quality. Run: python tools/upscale_art.py"
                    )
                else:
                    result["ready_for_print"] = True
                if img.mode not in ("RGB", "RGBA"):
                    result["warnings"].append(f"Color mode {img.mode} — Printify expects RGB.")
        except Exception as exc:
            result["issues"].append(f"PIL error: {exc}")
    else:
        result["warnings"].append("PIL not available — assuming print-ready.")
        result["ready_for_print"] = True

    return result


def build_printify_product(art: dict[str, Any], inspection: dict[str, Any]) -> dict[str, Any]:
    """Build a complete Printify product record for one art file."""
    product_id = art["product_id"]
    base_title = _product_title(product_id)
    etsy_title = f"{base_title} | Kawaii Wall Art Print | Multiple Sizes | Physical Print"
    if len(etsy_title) > 140:
        etsy_title = etsy_title[:137] + "..."

    variants = []
    for size in PRINT_SIZES:
        profit = round(size["sell_price"] - size["cost_est"], 2)
        variants.append({
            "size": size["label"],
            "sku": f"{product_id}-{size['sku_suffix']}",
            "list_price_usd": size["sell_price"],
            "estimated_cost_usd": size["cost_est"],
            "estimated_profit_usd": profit,
            "margin_pct": round(profit / size["sell_price"] * 100, 1),
        })

    etsy_description = (
        f"Bring this {base_title.lower()} to life on your walls!\n\n"
        "This listing is for a PHYSICAL PRINT shipped directly to you — "
        "no printing or downloading needed. Just order and it arrives at your door.\n\n"
        "Printed on premium matte paper at 300 DPI for crisp, gallery-quality results. "
        "Part of the OnBrandCraftz kawaii wall art collection.\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📐 AVAILABLE SIZES\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        + "\n".join(f"✅ {v['size']} — ${v['list_price_usd']:.2f}" for v in variants)
        + "\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🖼 PRINT DETAILS\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "• Premium matte photo paper\n"
        "• 300 DPI professional print quality\n"
        "• Ships in a sturdy protective mailer\n"
        "• No frame included — fits any standard frame\n"
        "• Printed and shipped by our certified print partner\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🤖 ABOUT THIS DESIGN\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "This design was created using AI image generation tools, with original "
        "prompts, curation, and finishing by the seller.\n\n"
        "© OnBrandCraftz. Personal use only. Not for resale or redistribution."
    )

    return {
        "product_id": product_id,
        "base_title": base_title,
        "source_file": art["file_path"],
        "source_file_name": art["file_name"],
        "image_inspection": inspection,
        "printify_blueprint_id": BLUEPRINT_POSTER_PRODIGI,
        "printify_blueprint_note": (
            f"Blueprint {BLUEPRINT_POSTER_PRODIGI} = Fine Art Posters (Print Clever, provider 72). "
            "Variants: 8x10=75288, 12x16=75290, 18x24=100938. Verified 2026-06-03."
        ),
        "variants": variants,
        "total_variants": len(variants),
        "etsy_draft_listing": {
            "title": etsy_title,
            "description": etsy_description,
            "tags": [
                "wall art print",
                "kawaii wall art",
                "printable poster",
                "boho wall decor",
                "bedroom wall art",
                "living room art",
                "gallery wall art",
                "instant download",
                "housewarming gift",
                "gift for her",
                "art print poster",
                "kawaii art print",
                "home decor print",
            ][:13],
            "who_made": "i_did",
            "is_digital": False,
        },
        "printify_api_payload_template": {
            "title": base_title,
            "description": etsy_description,
            "blueprint_id": BLUEPRINT_POSTER_PRODIGI,
            "print_provider_id": "(resolved at submission time)",
            "variants": "(resolved at submission time from Printify variant catalog)",
            "print_areas": [
                {
                    "variant_ids": "(resolved at submission time)",
                    "placeholders": [
                        {
                            "position": "front",
                            "images": [
                                {
                                    "id": "(assigned after image upload to Printify)",
                                    "x": 0.5,
                                    "y": 0.5,
                                    "scale": 1.0,
                                    "angle": 0,
                                }
                            ],
                        }
                    ],
                }
            ],
        },
        "submission_status": "queued",
        "submitted_at": None,
        "printify_product_id": None,
        "etsy_listing_id": None,
        "notes": (
            "Needs upscaling before submission — run: python tools/upscale_art.py"
            if inspection.get("needs_upscale")
            else "Ready for Printify submission."
        ),
    }


# ---------------------------------------------------------------------------
# Printify API client
# ---------------------------------------------------------------------------
class PrintifyAPIError(Exception):
    def __init__(self, status: int, message: str):
        self.status = status
        super().__init__(f"Printify API {status}: {message}")


class PrintifyClient:
    """Lightweight Printify API v1 client (stdlib only, no third-party deps)."""

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _request(self, method: str, endpoint: str, body: dict | None = None) -> Any:
        url = f"{PRINTIFY_BASE_URL}/{endpoint.lstrip('/')}"
        data = json.dumps(body).encode() if body else None
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "OnBrandCraftz/1.0 (printify_publisher.py)",
        }
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode(errors="replace")
            raise PrintifyAPIError(exc.code, body_text) from exc
        except urllib.error.URLError as exc:
            raise PrintifyAPIError(0, str(exc)) from exc

    def get_shops(self) -> list[dict]:
        return self._request("GET", "/shops.json")

    def get_blueprints(self) -> list[dict]:
        return self._request("GET", "/catalog/blueprints.json")

    def get_print_providers(self, blueprint_id: int) -> list[dict]:
        return self._request("GET", f"/catalog/blueprints/{blueprint_id}/print_providers.json")

    def get_variants(self, blueprint_id: int, print_provider_id: int) -> dict:
        return self._request(
            "GET",
            f"/catalog/blueprints/{blueprint_id}/print_providers/{print_provider_id}/variants.json",
        )

    def upload_image(self, file_name: str, file_path: Path) -> dict:
        import base64
        with open(file_path, "rb") as f:
            contents_b64 = base64.b64encode(f.read()).decode()
        return self._request("POST", "/uploads/images.json", {
            "file_name": file_name,
            "contents": contents_b64,
        })

    def create_product(self, shop_id: str, payload: dict) -> dict:
        return self._request("POST", f"/shops/{shop_id}/products.json", payload)

    def get_products(self, shop_id: str) -> dict:
        return self._request("GET", f"/shops/{shop_id}/products.json")


def _resolve_blueprint_variants(client: PrintifyClient, blueprint_id: int) -> dict[str, Any]:
    """Fetch print providers and variants for a blueprint, map to our sizes."""
    providers = client.get_print_providers(blueprint_id)
    if not providers:
        raise PrintifyAPIError(0, f"No print providers for blueprint {blueprint_id}")
    provider = providers[0]
    provider_id = provider["id"]
    print(f"    Print provider: {provider['title']} (id={provider_id})")

    variants_data = client.get_variants(blueprint_id, provider_id)
    variants = variants_data.get("variants", [])

    # Hardcoded variant IDs for blueprint 804 (Fine Art Posters, Print Clever id=72)
    # Verified 2026-06-03 via /catalog/blueprints/804/print_providers/72/variants.json
    BLUEPRINT_804_VARIANT_MAP = {
        "8x10": 75288,   # 8″ x 10″ (Vertical) / Matte
        "12x16": 75290,  # 12″ x 16″ (Vertical) / Matte
        "18x24": 100938, # 18″ x 24″ (Vertical) / Matte
    }

    size_to_variant: dict[str, int] = {}
    if blueprint_id == 804:
        size_to_variant = BLUEPRINT_804_VARIANT_MAP.copy()
    else:
        for variant in variants:
            opts = variant.get("options", {})
            size_label = opts.get("size", variant.get("title", "")).lower()
            for our_size in PRINT_SIZES:
                needle = our_size["sku_suffix"].lower()
                if needle in size_label.replace('"', "").replace(" ", "").replace("×", "x"):
                    size_to_variant[our_size["sku_suffix"]] = variant["id"]
                    break

    return {
        "provider_id": provider_id,
        "provider_title": provider["title"],
        "size_to_variant_id": size_to_variant,
        "all_variant_ids": [v["id"] for v in variants],
    }


def _submit_one(client: PrintifyClient, shop_id: str, product: dict[str, Any]) -> dict[str, Any]:
    """Upload image and create Printify product for one art file."""
    product_id = product["product_id"]
    file_path = Path(product["source_file"])

    # Prefer upscaled version
    upscaled = PRODUCT_FILES_DIR / "upscaled" / file_path.name
    if product["image_inspection"].get("needs_upscale"):
        if upscaled.exists():
            print(f"    Using upscaled version: {upscaled.name}")
            file_path = upscaled
        else:
            raise ValueError(
                f"{product_id} needs upscaling. Run: python tools/upscale_art.py  "
                f"(upscaled/{file_path.name} not found)"
            )

    # 1. Upload image
    print(f"    Uploading {file_path.name}...")
    upload = client.upload_image(file_path.name, file_path)
    image_id = upload.get("id")
    if not image_id:
        raise PrintifyAPIError(0, f"No image ID in upload response: {upload}")
    print(f"    Image ID: {image_id}")

    # 2. Resolve variants
    blueprint_id = product["printify_blueprint_id"]
    resolved = _resolve_blueprint_variants(client, blueprint_id)
    provider_id = resolved["provider_id"]
    size_to_variant = resolved["size_to_variant_id"]

    # Use matched variant IDs, fall back to first available
    variant_ids = list(size_to_variant.values())
    if not variant_ids:
        variant_ids = resolved["all_variant_ids"][:3]
        print(f"    Warning: size matching failed — using first {len(variant_ids)} variants")

    # Build pricing per variant
    variant_pricing = []
    for our_size in PRINT_SIZES:
        vid = size_to_variant.get(our_size["sku_suffix"])
        if vid:
            variant_pricing.append({
                "id": vid,
                "price": int(our_size["sell_price"] * 100),  # Printify uses cents
            })
    if not variant_pricing:
        # Fall back if no matches
        for vid in variant_ids:
            variant_pricing.append({"id": vid, "price": int(PRINT_SIZES[0]["sell_price"] * 100)})

    # 3. Create product
    payload = {
        "title": product["base_title"],
        "description": product["etsy_draft_listing"]["description"],
        "blueprint_id": blueprint_id,
        "print_provider_id": provider_id,
        "variants": variant_pricing,
        "print_areas": [
            {
                "variant_ids": variant_ids,
                "placeholders": [
                    {
                        "position": "front",
                        "images": [
                            {"id": image_id, "x": 0.5, "y": 0.5, "scale": 1.0, "angle": 0}
                        ],
                    }
                ],
            }
        ],
    }

    print(f"    Creating Printify product...")
    result = client.create_product(shop_id, payload)
    printify_id = result.get("id")
    print(f"    Printify product ID: {printify_id}")

    updated = dict(product)
    updated["submission_status"] = "submitted"
    updated["submitted_at"] = str(date.today())
    updated["printify_product_id"] = printify_id
    updated["printify_image_id"] = image_id
    updated["printify_provider_id"] = provider_id
    return updated


def _save_submitted(product: dict[str, Any]) -> None:
    submitted_path = PRINTIFY_DIR / "submitted_products.json"
    records: list[dict] = json.loads(submitted_path.read_text()) if submitted_path.exists() else []
    pid = product["product_id"]
    idx = next((i for i, r in enumerate(records) if r["product_id"] == pid), None)
    if idx is not None:
        records[idx] = product
    else:
        records.append(product)
    submitted_path.write_text(json.dumps(records, indent=2))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def cmd_queue() -> None:
    print("\nBuilding Printify submission queue...")
    art_files = discover_art_files()
    print(f"Found {len(art_files)} wall art files\n")

    products = []
    ready_count = 0
    needs_upscale_count = 0

    for art in art_files:
        insp = inspect_image(Path(art["file_path"]))
        product = build_printify_product(art, insp)
        products.append(product)
        if insp.get("needs_upscale"):
            needs_upscale_count += 1
        elif insp.get("ready_for_print"):
            ready_count += 1

    total_variants = sum(p["total_variants"] for p in products)
    total_projected_profit = sum(
        v["estimated_profit_usd"] for p in products for v in p["variants"]
    )

    queue = {
        "generated_date": str(date.today()),
        "total_products": len(products),
        "ready_for_submission": ready_count,
        "needs_upscale": needs_upscale_count,
        "total_variants": total_variants,
        "projected_profit_if_all_sold_once_usd": round(total_projected_profit, 2),
        "pricing_summary": {
            s["sku_suffix"]: {
                "size": s["label"],
                "sell_price": s["sell_price"],
                "estimated_cost": s["cost_est"],
                "estimated_profit": round(s["sell_price"] - s["cost_est"], 2),
            }
            for s in PRINT_SIZES
        },
        "blueprint_ids": {
            "prodigi_poster": BLUEPRINT_POSTER_PRODIGI,
            "enhanced_matte_poster": BLUEPRINT_POSTER_MATTE,
            "note": "Verify at https://api.printify.com/v1/catalog/blueprints.json",
        },
        "products": products,
    }

    PRINTIFY_DIR.mkdir(parents=True, exist_ok=True)
    queue_path = PRINTIFY_DIR / "products_queue.json"
    queue_path.write_text(json.dumps(queue, indent=2))
    _write_setup_guide()

    print(f"Queue summary:")
    print(f"  Total wall art files:   {len(products)}")
    print(f"  Ready to submit:        {ready_count}")
    print(f"  Need upscaling first:   {needs_upscale_count}")
    print(f"  Total variants:         {total_variants} ({len(products)} products × {len(PRINT_SIZES)} sizes)")
    print(f"\n  Per-size pricing:")
    for s in PRINT_SIZES:
        print(f"    {s['label']:10}  sell ${s['sell_price']:.2f}  cost ~${s['cost_est']:.2f}  profit ~${s['sell_price']-s['cost_est']:.2f}")
    print(f"\nSaved: {queue_path.relative_to(BASE)}")
    print(f"Saved: {(PRINTIFY_DIR / 'printify_setup_guide.md').relative_to(BASE)}")

    if needs_upscale_count > 0:
        print(f"\n  {needs_upscale_count} files need upscaling. Run: python tools/upscale_art.py")
        print(f"  Then re-run: python tools/printify_publisher.py --queue")


def cmd_status() -> None:
    env = _parse_env()
    api_key = env.get("PRINTIFY_API_KEY", "").strip()

    print("\nPrintify Connection Status")
    print("=" * 50)

    if not api_key:
        print("PRINTIFY_API_KEY: NOT SET")
        print("\nTo get your API key:")
        print("  1. Log in at https://printify.com")
        print("  2. Go to My Account → Connections → API")
        print("  3. Generate a new token")
        print("  4. Add to .env: PRINTIFY_API_KEY=your_token_here")
        print("\nRun again after adding the key.")
        return

    print(f"PRINTIFY_API_KEY: {'*' * 8}{api_key[-4:]}")
    client = PrintifyClient(api_key)
    try:
        shops = client.get_shops()
        print(f"API connection: OK")
        print(f"Shops ({len(shops)} found):")
        for shop in shops:
            print(f"  id={shop.get('id')}  title={shop.get('title')}  platform={shop.get('sales_channel')}")
        if shops:
            shop_id = str(shops[0]["id"])
            print(f"\nDefault shop ID: {shop_id}")
            print(f"Tip: Add to .env: PRINTIFY_SHOP_ID={shop_id}")
            try:
                products_data = client.get_products(shop_id)
                print(f"Existing Printify products: {products_data.get('total', '?')}")
            except PrintifyAPIError:
                pass
    except PrintifyAPIError as exc:
        print(f"API connection: FAILED — {exc}")
        if exc.status == 401:
            print("Check that PRINTIFY_API_KEY is correct and not expired.")


def cmd_submit(product_id: str) -> None:
    env = _parse_env()
    api_key = env.get("PRINTIFY_API_KEY", "").strip()
    if not api_key:
        print("ERROR: PRINTIFY_API_KEY not set in .env")
        sys.exit(1)

    queue_path = PRINTIFY_DIR / "products_queue.json"
    if not queue_path.exists():
        print("Queue not found. Run: python tools/printify_publisher.py --queue")
        sys.exit(1)

    queue = json.loads(queue_path.read_text())
    pid_upper = product_id.upper().strip()
    product = next((p for p in queue["products"] if p["product_id"] == pid_upper), None)
    if not product:
        print(f"ERROR: {pid_upper} not found in queue.")
        print(f"Available: {', '.join(p['product_id'] for p in queue['products'][:15])}")
        sys.exit(1)

    client = PrintifyClient(api_key)
    shop_id = env.get("PRINTIFY_SHOP_ID", "").strip()
    if not shop_id:
        shops = client.get_shops()
        shop_id = str(shops[0]["id"])
        print(f"Using shop: {shops[0].get('title')} (id={shop_id})")

    try:
        updated = _submit_one(client, shop_id, product)
        _save_submitted(updated)
        print(f"\n{pid_upper} submitted successfully!")
        print(f"Printify product ID: {updated['printify_product_id']}")
        print(f"\nNext: Open Printify dashboard → review product → publish to Etsy")
    except (PrintifyAPIError, ValueError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)


def cmd_submit_all() -> None:
    env = _parse_env()
    api_key = env.get("PRINTIFY_API_KEY", "").strip()
    if not api_key:
        print("ERROR: PRINTIFY_API_KEY not set in .env")
        sys.exit(1)

    queue_path = PRINTIFY_DIR / "products_queue.json"
    if not queue_path.exists():
        print("Queue not found. Run: python tools/printify_publisher.py --queue")
        sys.exit(1)

    queue = json.loads(queue_path.read_text())
    client = PrintifyClient(api_key)
    shop_id = env.get("PRINTIFY_SHOP_ID", "").strip()
    if not shop_id:
        shops = client.get_shops()
        shop_id = str(shops[0]["id"])
        print(f"Using shop: {shops[0].get('title')} (id={shop_id})")

    to_submit = [p for p in queue["products"] if p.get("submission_status") == "queued"]
    print(f"Submitting {len(to_submit)} queued products...")

    results: dict[str, str] = {}
    for i, product in enumerate(to_submit, 1):
        pid = product["product_id"]
        print(f"[{i}/{len(to_submit)}] {pid}")
        try:
            updated = _submit_one(client, shop_id, product)
            _save_submitted(updated)
            results[pid] = f"OK — printify_id={updated['printify_product_id']}"
            if i < len(to_submit):
                time.sleep(1.5)
        except (PrintifyAPIError, ValueError) as exc:
            results[pid] = f"ERROR: {exc}"
            print(f"  ERROR: {exc}")

    ok = sum(1 for v in results.values() if v.startswith("OK"))
    err = sum(1 for v in results.values() if v.startswith("ERROR"))
    print(f"\nDone. Succeeded: {ok}  Failed: {err}")


def _write_setup_guide() -> None:
    PRINTIFY_DIR.mkdir(parents=True, exist_ok=True)
    guide_path = PRINTIFY_DIR / "printify_setup_guide.md"
    content = f"""# Printify Setup Guide — OnBrandCraftz
*Generated {date.today()} by printify_publisher.py*

Printify is a free print-on-demand platform. Buyers order on Etsy, Printify prints
and ships, you keep the margin. Zero inventory, zero fulfillment overhead.

---

## How It Works

```
Buyer places Etsy order
        ↓
Etsy auto-forwards to Printify (via integration)
        ↓
Printify routes to nearest print facility
        ↓
Print ships to buyer in 5–10 business days
        ↓
You earn: Etsy sale price − Printify cost = profit
```

---

## Step 1 — Create Printify Account

1. Go to https://printify.com
2. Sign up with Printing3dthings@outlook.com
3. No monthly fee — free to use

---

## Step 2 — Connect Your Etsy Shop

1. Printify Dashboard → My stores → Add new store
2. Select Etsy from the platform list
3. Authorize Printify to access your Etsy account
4. Printify will appear in your Etsy Connected Apps

---

## Step 3 — Get Your API Key

1. Printify Dashboard → top-right avatar → My account → Connections → API
2. Generate a new token
3. Add to .env:
   ```
   PRINTIFY_API_KEY=your_token_here
   ```

---

## Step 4 — Understand Blueprints

Printify uses "blueprints" — product templates. For wall art posters:

| Blueprint | ID   | Type                  | Notes                  |
|-----------|------|-----------------------|------------------------|
| Prodigi   | {BLUEPRINT_POSTER_PRODIGI}  | Color matte poster    | Most popular for art   |
| Matte     | {BLUEPRINT_POSTER_MATTE}   | Enhanced matte poster | Printify Choice        |

Verify current IDs at: https://api.printify.com/v1/catalog/blueprints.json

---

## Step 5 — File Quality

Some wall art files are still at 1024×1536px (raw AI output).
Printify needs 300 DPI minimum — for 8×10 that means 2400×3000px.

Upscale files before submitting:
```bash
python tools/upscale_art.py
python tools/printify_publisher.py --queue   # regenerate queue with upscaled dimensions
```

The submit commands automatically use upscaled versions when available.

---

## Step 6 — Submit Products

```bash
# Verify connection
python tools/printify_publisher.py --status

# Submit one product to test
python tools/printify_publisher.py --submit DP1000

# Review in Printify dashboard, then submit all
python tools/printify_publisher.py --submit-all
```

---

## Pricing Model

| Size     | Sell Price | ~Print Cost | ~Profit | ~Margin |
|----------|------------|-------------|---------|---------|
| 8×10 in  | $19.99     | ~$8.00      | ~$9.00  | ~46%    |
| 12×16 in | $27.99     | ~$12.00     | ~$12.00 | ~46%    |
| 18×24 in | $39.99     | ~$18.00     | ~$18.00 | ~47%    |

*Actual Printify costs vary by print provider and destination.*
*Always verify costs in Printify's variant pricing screen before publishing.*

---

## After Submission

1. Open Printify Dashboard → find the new product
2. Review variants and pricing
3. Click Publish to push as a draft Etsy listing
4. In Etsy: open draft → add lifestyle photos → set tags → publish

---

## Revenue Projection (52 art files × 3 sizes)

| Monthly Orders (all sizes) | Monthly Profit | Annual    |
|---------------------------|----------------|-----------|
| 20 orders                 | ~$220          | ~$2,640   |
| 50 orders                 | ~$550          | ~$6,600   |
| 100 orders                | ~$1,100        | ~$13,200  |

**This is a second revenue stream from art already built — zero additional design work.**

---

*OnBrandCraftz — tools/printify_publisher.py*
"""
    guide_path.write_text(content)
    print(f"  Saved: {guide_path.relative_to(BASE)}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        prog="printify_publisher.py",
        description="Printify POD integration for OnBrandCraftz wall art",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--queue", action="store_true", help="Build submission queue from all art files")
    group.add_argument("--status", action="store_true", help="Check API connection and shop status")
    group.add_argument("--submit", metavar="PRODUCT_ID", help="Submit one product (requires PRINTIFY_API_KEY)")
    group.add_argument("--submit-all", action="store_true", help="Submit all queued products (requires PRINTIFY_API_KEY)")
    args = parser.parse_args()

    PRINTIFY_DIR.mkdir(parents=True, exist_ok=True)

    if args.queue:
        cmd_queue()
    elif args.status:
        cmd_status()
    elif args.submit:
        cmd_submit(args.submit)
    elif args.submit_all:
        cmd_submit_all()


if __name__ == "__main__":
    main()
