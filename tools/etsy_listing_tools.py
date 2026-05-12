"""
Etsy Listing Tools — creates and publishes digital product listings on Etsy.

Wraps the existing EtsyAPIClient (tools/etsy_api.py).
Publishing listings requires ETSY_ACCESS_TOKEN (OAuth). Run tools/etsy_oauth.py first.
Without OAuth the agent can draft listings locally and report what would be published.
"""

import json
import os
from datetime import date

from tools.data_store import DataStore
from tools.etsy_api import EtsyAPIClient, EtsyAPIError, is_configured

DIGITAL_TAXONOMY_ID = 2078  # Etsy taxonomy ID for "Digital Files" (Craft Supplies & Tools > Patterns & How To)

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_approved_unlisted_products",
        "description": "Get digital products that have passed QC but are not yet listed on Etsy.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "generate_listing_content",
        "description": (
            "Generate SEO-optimized title, description, and tags for a digital product listing. "
            "Does NOT publish — just returns the content for review before publishing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "title": {"type": "string", "description": "SEO-optimized listing title (max 140 chars)"},
                "description": {"type": "string", "description": "Full listing description with search keywords"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Up to 13 Etsy tags (each max 20 chars, no special chars)",
                },
                "price": {"type": "number", "description": "Listing price in USD"},
                "quantity": {
                    "type": "integer",
                    "description": "For digital items use 999 (unlimited)",
                    "default": 999,
                },
                "section": {
                    "type": "string",
                    "description": "Shop section name, e.g. 'Digital Planners' or 'Digital Art'",
                },
            },
            "required": ["product_id", "title", "description", "tags", "price"],
        },
    },
    {
        "name": "publish_digital_listing",
        "description": (
            "Publish a digital product listing to Etsy. "
            "Requires ETSY_ACCESS_TOKEN. Product must have listing content generated first."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "confirm": {
                    "type": "boolean",
                    "description": "Must be true to confirm publishing",
                },
            },
            "required": ["product_id", "confirm"],
        },
    },
    {
        "name": "list_digital_listings",
        "description": "List all digital products with their Etsy listing status and IDs.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_listing_seo_tips",
        "description": "Get Etsy SEO best practices and tips for digital product listings.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "enum": ["digital_art", "planner", "printable", "wall_art", "clipart"],
                }
            },
            "required": ["product_type"],
        },
    },
    {
        "name": "check_competitor_pricing",
        "description": "Search Etsy for similar digital products to inform pricing strategy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "search_query": {"type": "string", "description": "Search query, e.g. 'digital planner 2026'"},
                "limit": {"type": "integer", "default": 10, "description": "Number of results to return"},
            },
            "required": ["search_query"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_approved_unlisted_products":
        return _get_approved_unlisted(store)
    if tool_name == "generate_listing_content":
        return _generate_listing_content(tool_input, store)
    if tool_name == "publish_digital_listing":
        return _publish_digital_listing(tool_input, store)
    if tool_name == "list_digital_listings":
        return _list_digital_listings(store)
    if tool_name == "get_listing_seo_tips":
        return _get_seo_tips(tool_input["product_type"])
    if tool_name == "check_competitor_pricing":
        return _check_competitor_pricing(tool_input, store)
    return f"Unknown Etsy listing tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _get_approved_unlisted(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    unlisted = [
        p for p in products
        if p.get("status") == "approved" and not p.get("etsy_listing_id")
    ]
    summary = [
        {
            "id": p["id"],
            "title": p["title"],
            "type": p["product_type"],
            "price": p["price"],
            "file_format": p.get("file_format"),
            "file_size_kb": p.get("file_size_kb"),
            "qc_notes": p.get("qc_notes"),
        }
        for p in unlisted
    ]
    return json.dumps({
        "approved_unlisted_products": summary,
        "count": len(summary),
        "next_step": (
            "Use generate_listing_content to draft SEO content, then publish_digital_listing to go live."
            if summary else "No approved products waiting to be listed."
        ),
    }, indent=2)


def _generate_listing_content(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    tags = data["tags"][:13]
    title = data["title"][:140]

    # Validate tags
    tag_warnings = []
    clean_tags = []
    for tag in tags:
        clean = tag[:20]
        if tag != clean:
            tag_warnings.append(f"Tag '{tag}' truncated to '{clean}' (20 char limit)")
        clean_tags.append(clean)

    listing_draft = {
        "title": title,
        "description": data["description"],
        "tags": clean_tags,
        "price": data["price"],
        "quantity": data.get("quantity", 999),
        "section": data.get("section", "Digital Downloads"),
        "is_digital": True,
        "type": "download",
        "taxonomy_id": DIGITAL_TAXONOMY_ID,
    }

    product["listing_draft"] = listing_draft
    product["updated_at"] = str(date.today())
    _save_product(product, store)

    result: dict = {
        "success": True,
        "product_id": data["product_id"],
        "listing_draft": listing_draft,
        "character_counts": {
            "title": len(title),
            "description": len(data["description"]),
            "tags": len(clean_tags),
        },
        "next_step": "Review content, then call publish_digital_listing to go live on Etsy.",
    }
    if tag_warnings:
        result["warnings"] = tag_warnings
    return json.dumps(result, indent=2)


def _publish_digital_listing(data: dict, store: DataStore) -> str:
    if not data.get("confirm"):
        return json.dumps({"error": "Set confirm=true to publish the listing."})

    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    if product.get("status") not in ("approved",):
        return json.dumps({"error": f"Product must be approved before listing. Status: {product.get('status')}"})

    draft = product.get("listing_draft")
    if not draft:
        return json.dumps({"error": "No listing content found. Run generate_listing_content first."})

    if not is_configured():
        return json.dumps({
            "warning": "ETSY_API_KEY not configured.",
            "action": "Add ETSY_API_KEY (and ETSY_ACCESS_TOKEN for publishing) to .env",
            "draft_saved": True,
            "draft": draft,
        })

    client = EtsyAPIClient()
    if not client.access_token:
        return json.dumps({
            "warning": "Etsy OAuth not configured. Run: python tools/etsy_oauth.py",
            "draft_ready": True,
            "listing_draft": draft,
            "note": "Listing draft saved locally. Add ETSY_ACCESS_TOKEN to publish.",
        })

    try:
        listing_data = {
            "title": draft["title"],
            "description": draft["description"],
            "price": {"amount": int(draft["price"] * 100), "divisor": 100, "currency_code": "USD"},
            "quantity": draft["quantity"],
            "who_made": "i_did",
            "is_supply": False,
            "when_made": "made_to_order",
            "taxonomy_id": draft["taxonomy_id"],
            "tags": draft["tags"],
            "type": "download",
        }

        response = client.create_listing(listing_data)
        etsy_listing_id = str(response.get("listing_id", ""))

        product["etsy_listing_id"] = etsy_listing_id
        product["status"] = "listed"
        product["listed_at"] = str(date.today())
        product["updated_at"] = str(date.today())
        _save_product(product, store)

        # Also create a listing record in the main listings array
        _add_to_main_listings(product, draft, etsy_listing_id, store)

        return json.dumps({
            "success": True,
            "product_id": data["product_id"],
            "etsy_listing_id": etsy_listing_id,
            "etsy_url": f"https://www.etsy.com/listing/{etsy_listing_id}",
            "title": draft["title"],
            "price": draft["price"],
            "status": "listed",
        }, indent=2)

    except EtsyAPIError as e:
        return json.dumps({"error": f"Etsy API error: {e}"})
    except Exception as exc:
        return json.dumps({"error": str(exc)})


def _list_digital_listings(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    rows = [
        {
            "id": p["id"],
            "title": p["title"],
            "type": p["product_type"],
            "status": p["status"],
            "etsy_listing_id": p.get("etsy_listing_id"),
            "etsy_url": f"https://www.etsy.com/listing/{p['etsy_listing_id']}" if p.get("etsy_listing_id") else None,
            "price": p["price"],
            "listed_at": p.get("listed_at"),
        }
        for p in products
    ]
    listed = [r for r in rows if r["etsy_listing_id"]]
    return json.dumps({
        "all_digital_products": rows,
        "listed_on_etsy": len(listed),
        "not_yet_listed": len(rows) - len(listed),
    }, indent=2)


def _get_seo_tips(product_type: str) -> str:
    tips = {
        "digital_art": {
            "title_keywords": ["digital download", "printable art", "wall art print", "instant download", "home decor"],
            "description_tips": [
                "Lead with what the buyer gets: 'INSTANT DOWNLOAD - High resolution PNG...'",
                "List all file formats and sizes included",
                "Mention DPI (300 DPI for print quality)",
                "Include framing suggestions and print size options",
                "Add a FAQ section about printing and usage rights",
            ],
            "top_tags": ["digital download", "printable art", "wall decor", "instant download",
                         "home decor print", "digital print", "printable wall art", "art print"],
            "pricing_range": "$2 - $15 for single prints, $5 - $25 for bundles",
        },
        "planner": {
            "title_keywords": ["digital planner", "printable planner", "PDF planner", "2026 planner", "undated planner"],
            "description_tips": [
                "Specify the planner year or 'undated' for evergreen listings",
                "List all sections: monthly, weekly, daily, habit tracker, etc.",
                "Mention page count",
                "Clarify print vs. digital use (GoodNotes, Notability compatibility)",
                "Include what file formats are delivered",
            ],
            "top_tags": ["digital planner", "printable planner", "PDF planner", "daily planner",
                         "weekly planner", "undated planner", "goodnotes planner", "instant download"],
            "pricing_range": "$4 - $20 for individual planners, $10 - $35 for bundles",
        },
        "printable": {
            "title_keywords": ["printable", "instant download", "digital download", "print at home"],
            "description_tips": [
                "Explain exactly what is included (number of files, formats)",
                "Give recommended print sizes",
                "Add care/printing instructions",
            ],
            "top_tags": ["printable", "instant download", "digital download", "print at home"],
            "pricing_range": "$2 - $10",
        },
        "wall_art": {
            "title_keywords": ["wall art", "printable wall art", "digital wall art", "art print", "gallery wall"],
            "description_tips": [
                "Mention style (boho, minimalist, modern, etc.)",
                "List included sizes (5x7, 8x10, 11x14, etc.)",
                "Suggest frame types",
                "Describe color palette",
            ],
            "top_tags": ["wall art print", "printable wall art", "gallery wall", "digital download",
                         "home decor", "boho wall art", "minimalist art", "instant download"],
            "pricing_range": "$3 - $18",
        },
        "clipart": {
            "title_keywords": ["clipart", "digital clipart", "PNG clipart", "transparent background", "commercial use"],
            "description_tips": [
                "State clearly if commercial use is allowed",
                "List all files included (how many PNGs, sizes)",
                "Mention transparent background if applicable",
                "Describe the art style",
            ],
            "top_tags": ["clipart", "PNG clipart", "digital clipart", "commercial use", "transparent"],
            "pricing_range": "$2 - $12 per set",
        },
    }

    tip_data = tips.get(product_type, tips["digital_art"])
    return json.dumps({
        "product_type": product_type,
        "seo_tips": tip_data,
        "general_etsy_tips": [
            "Use all 13 tag slots",
            "Put your most important keyword at the START of your title",
            "Never repeat the same keyword in tags that's already in the title (Etsy counts both)",
            "Use multi-word tags (phrases rank better than single words)",
            "Update listings regularly to boost search ranking",
        ],
    }, indent=2)


def _check_competitor_pricing(data: dict, store: DataStore) -> str:
    if not is_configured():
        return json.dumps({
            "warning": "ETSY_API_KEY not configured. Cannot fetch live competitor data.",
            "action": "Add ETSY_API_KEY to .env for live competitor research.",
        })
    try:
        client = EtsyAPIClient()
        results = client.search_listings(
            keywords=data["search_query"],
            limit=data.get("limit", 10),
            sort_on="score",
        )
        listings = results.get("results", [])
        prices = [
            {
                "title": l.get("title", "")[:80],
                "price": l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1),
                "currency": l.get("price", {}).get("currency_code", "USD"),
                "views": l.get("views", 0),
                "favorites": l.get("num_favorers", 0),
            }
            for l in listings
        ]
        amounts = [p["price"] for p in prices if p["price"] > 0]
        return json.dumps({
            "query": data["search_query"],
            "results": prices,
            "count": len(prices),
            "price_stats": {
                "min": round(min(amounts), 2) if amounts else None,
                "max": round(max(amounts), 2) if amounts else None,
                "avg": round(sum(amounts) / len(amounts), 2) if amounts else None,
            },
        }, indent=2)
    except EtsyAPIError as e:
        return json.dumps({"error": str(e)})


def _add_to_main_listings(product: dict, draft: dict, etsy_listing_id: str, store: DataStore) -> None:
    listings = store.listings
    new_id = f"DL{etsy_listing_id}" if etsy_listing_id else f"DL{product['id']}"
    listings.append({
        "id": new_id,
        "etsy_listing_id": etsy_listing_id,
        "digital_product_id": product["id"],
        "title": draft["title"],
        "price": draft["price"],
        "quantity": draft["quantity"],
        "views": 0,
        "favorites": 0,
        "sales": 0,
        "tags": draft["tags"],
        "category": "Digital Downloads",
        "status": "active",
        "processing_days": 0,
        "description": draft["description"],
        "type": "digital",
        "listed_at": str(date.today()),
    })
    store.save()


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _find_product(product_id: str, store: DataStore) -> dict | None:
    products = store.get("digital_products", default=[])
    return next((p for p in products if p["id"] == product_id), None)


def _save_product(product: dict, store: DataStore) -> None:
    products = store.get("digital_products", default=[])
    for i, p in enumerate(products):
        if p["id"] == product["id"]:
            products[i] = product
            break
    store.set(products, "digital_products")
    store.save()
