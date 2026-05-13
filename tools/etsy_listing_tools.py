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
    {
        "name": "audit_listing_seo",
        "description": (
            "Score a single digital product listing on Etsy SEO best practices. "
            "Returns a score 0–100 with per-criterion breakdown and specific improvement suggestions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "The digital product ID to audit"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "optimize_listing_content",
        "description": (
            "Generate optimized title, tags, and description improvements for an existing listing "
            "based on SEO audit results and best practices. Returns exact replacement content ready to apply."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Product ID to generate optimized content for"},
                "focus_keyword": {
                    "type": "string",
                    "description": "Primary search keyword to optimize around (e.g. 'digital planner 2026')",
                },
                "style_descriptor": {
                    "type": "string",
                    "description": "Style/aesthetic descriptor (e.g. 'minimalist', 'boho', 'farmhouse')",
                },
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "bulk_seo_audit",
        "description": (
            "Run SEO audit across ALL active digital product listings. "
            "Returns a ranked list from worst to best performing, with scores and top improvement action per listing."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
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
    if tool_name == "audit_listing_seo":
        return _audit_listing_seo(tool_input["product_id"], store)
    if tool_name == "optimize_listing_content":
        return _optimize_listing_content(tool_input, store)
    if tool_name == "bulk_seo_audit":
        return _bulk_seo_audit(store)
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


def _audit_listing_seo(product_id: str, store: DataStore) -> str:
    product = _find_product(product_id, store)
    if not product:
        return json.dumps({"error": f"Product {product_id} not found"})

    draft = product.get("listing_draft", {})
    title = draft.get("title", product.get("title", ""))
    tags = draft.get("tags", [])
    description = draft.get("description", "")
    price = draft.get("price", product.get("price", 0))
    product_type = product.get("product_type", "digital_art")

    score = 0
    breakdown = {}
    suggestions = []

    # Title: first 40 chars contain primary keyword (+20)
    if len(title) >= 40:
        first_40 = title[:40].lower()
        keyword_hints = ["digital", "planner", "art", "printable", "wall", "clipart", "download", "pdf"]
        if any(k in first_40 for k in keyword_hints):
            score += 20
            breakdown["title_keyword_first_40"] = "PASS (+20)"
        else:
            breakdown["title_keyword_first_40"] = "FAIL (0) — primary keyword not in first 40 chars"
            suggestions.append("Move your primary keyword to the very beginning of your title")
    else:
        breakdown["title_keyword_first_40"] = "FAIL (0) — title too short"
        suggestions.append("Expand title to lead with primary keyword in first 40 chars")

    # Title length 130–140 chars (+10)
    tlen = len(title)
    if 130 <= tlen <= 140:
        score += 10
        breakdown["title_length"] = f"PASS (+10) — {tlen} chars"
    elif 100 <= tlen < 130:
        score += 5
        breakdown["title_length"] = f"PARTIAL (+5) — {tlen} chars (aim for 130–140)"
        suggestions.append(f"Title is {tlen} chars — expand to 130–140 to maximize keyword coverage")
    else:
        breakdown["title_length"] = f"FAIL (0) — {tlen} chars"
        suggestions.append(f"Title is only {tlen} chars — expand to 130–140 for maximum SEO coverage")

    # All 13 tags used (+15)
    tag_count = len(tags)
    if tag_count == 13:
        score += 15
        breakdown["tag_count"] = "PASS (+15) — all 13 tags used"
    elif tag_count >= 10:
        score += 8
        breakdown["tag_count"] = f"PARTIAL (+8) — {tag_count}/13 tags used"
        suggestions.append(f"Add {13 - tag_count} more tags to fill all 13 slots")
    else:
        breakdown["tag_count"] = f"FAIL (0) — only {tag_count}/13 tags used"
        suggestions.append(f"Only {tag_count} tags — fill all 13 slots with multi-word buyer-intent phrases")

    # Tags are multi-word (+10)
    if tags:
        multi_word = sum(1 for t in tags if " " in t.strip())
        ratio = multi_word / len(tags)
        if ratio >= 0.85:
            score += 10
            breakdown["tags_multiword"] = f"PASS (+10) — {multi_word}/{len(tags)} tags are multi-word"
        elif ratio >= 0.6:
            score += 5
            breakdown["tags_multiword"] = f"PARTIAL (+5) — {multi_word}/{len(tags)} tags multi-word"
            suggestions.append("Convert single-word tags to 2–4 word buyer-intent phrases")
        else:
            breakdown["tags_multiword"] = f"FAIL (0) — {multi_word}/{len(tags)} tags multi-word"
            suggestions.append("Most tags are single words — replace all with multi-word phrases (e.g., 'digital planner' not 'planner')")
    else:
        breakdown["tags_multiword"] = "FAIL (0) — no tags"
        suggestions.append("Add 13 multi-word tags")

    # No tag duplicates title verbatim (+10)
    title_lower = title.lower()
    verbatim_dupes = [t for t in tags if t.lower() in title_lower and len(t) > 5]
    if not verbatim_dupes:
        score += 10
        breakdown["no_tag_title_dupes"] = "PASS (+10) — tags complement title without verbatim overlap"
    else:
        score += 5
        breakdown["no_tag_title_dupes"] = f"PARTIAL (+5) — {len(verbatim_dupes)} tag(s) duplicate title phrases"
        suggestions.append(f"Tags {verbatim_dupes[:3]} repeat title phrases — replace with synonym variations")

    # Description has hook in first 2 lines (+15)
    if description:
        first_lines = description[:200].strip()
        hook_words = ["transform", "beautiful", "perfect", "instant", "download", "stunning", "premium", "elevate", "create", "discover"]
        if any(w in first_lines.lower() for w in hook_words) and len(first_lines) > 40:
            score += 15
            breakdown["description_hook"] = "PASS (+15) — strong opening hook detected"
        elif len(first_lines) > 20:
            score += 7
            breakdown["description_hook"] = "PARTIAL (+7) — description exists but hook is weak"
            suggestions.append("Open description with a compelling benefit statement (what does this give the buyer?)")
        else:
            breakdown["description_hook"] = "FAIL (0) — description too short or missing hook"
            suggestions.append("Write a compelling first 2 lines: the emotional or practical benefit the buyer gets")
    else:
        breakdown["description_hook"] = "FAIL (0) — no description"
        suggestions.append("Add a full description with hook, what's included, how to use it, and FAQ")

    # Description mentions file format (+10)
    format_words = ["pdf", "png", "jpeg", "jpg", "zip", "300 dpi", "dpi", "high resolution", "file format", "instant download"]
    if description and any(w in description.lower() for w in format_words):
        score += 10
        breakdown["description_format_info"] = "PASS (+10) — file format/specs mentioned"
    else:
        breakdown["description_format_info"] = "FAIL (0) — file format not mentioned in description"
        suggestions.append("State the file format (PDF, PNG), resolution (300 DPI), and what's included in the description")

    # Price at or above market for type (+10)
    price_floors = {
        "planner": 6.0, "digital_planner": 6.0,
        "wall_art": 4.0, "digital_art": 4.0,
        "clipart": 4.0, "printable": 3.0,
    }
    floor = price_floors.get(product_type, 3.5)
    if price >= floor * 1.1:
        score += 10
        breakdown["price_positioning"] = f"PASS (+10) — ${price:.2f} is at or above market floor (${floor:.2f})"
    elif price >= floor:
        score += 5
        breakdown["price_positioning"] = f"PARTIAL (+5) — ${price:.2f} is at market floor, consider raising to signal premium quality"
        suggestions.append(f"Price ${price:.2f} is at minimum — consider raising to ${floor * 1.3:.2f} to signal quality")
    else:
        breakdown["price_positioning"] = f"FAIL (0) — ${price:.2f} is below recommended floor (${floor:.2f})"
        suggestions.append(f"Price ${price:.2f} is below the {product_type} market floor of ${floor:.2f} — raise it")

    grade = "A" if score >= 90 else "B" if score >= 80 else "C" if score >= 65 else "D" if score >= 50 else "F"

    return json.dumps({
        "product_id": product_id,
        "title": title[:60] + "..." if len(title) > 60 else title,
        "seo_score": score,
        "grade": grade,
        "needs_improvement": score < 80,
        "score_breakdown": breakdown,
        "suggestions": suggestions,
        "next_step": (
            "Use optimize_listing_content to generate improved title, tags, and description."
            if score < 80 else "Listing is well-optimized. Monitor performance."
        ),
    }, indent=2)


def _optimize_listing_content(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Product {data['product_id']} not found"})

    product_type = product.get("product_type", "digital_art")
    title_base = product.get("title", "Digital Download")
    focus_kw = data.get("focus_keyword", "")
    style = data.get("style_descriptor", "minimalist")

    type_map = {
        "planner": {
            "primary_kw": focus_kw or "Digital Planner 2026 PDF",
            "secondary": ["Printable Weekly Planner", "Undated PDF Planner", "Instant Download Planner"],
            "tags": ["digital planner", "printable planner", "pdf planner", "weekly planner",
                     "undated planner", "daily planner", "goodnotes planner", "instant download",
                     "printable organizer", "planner insert", "yearly planner", "habit tracker", "goal planner"],
            "price_rec": 8.00,
            "hook": "Stay organized all year with this beautifully designed",
        },
        "wall_art": {
            "primary_kw": focus_kw or "Printable Wall Art",
            "secondary": ["Digital Art Print", "Instant Download Art", "Home Decor Print"],
            "tags": ["printable wall art", "digital download", "instant download", "home decor print",
                     "wall art print", "digital art print", "gallery wall art", "boho wall decor",
                     "minimalist art", "art print download", "printable home decor", "bedroom wall art", "living room art"],
            "price_rec": 5.00,
            "hook": "Transform your walls with this stunning",
        },
        "clipart": {
            "primary_kw": focus_kw or "Digital Clipart PNG",
            "secondary": ["Transparent Background PNG", "Commercial Use Clipart", "Instant Download Clipart"],
            "tags": ["digital clipart", "png clipart", "transparent clipart", "commercial use",
                     "instant download", "clipart bundle", "watercolor clipart", "hand drawn clipart",
                     "printable clipart", "scrapbook clipart", "clipart set", "digital graphics", "craft clipart"],
            "price_rec": 6.00,
            "hook": "Create beautiful projects with this premium",
        },
    }

    config = type_map.get(product_type, type_map["wall_art"])
    primary_kw = config["primary_kw"]
    style_cap = style.capitalize()

    # Build optimized title (target: 130–140 chars)
    title_parts = [primary_kw, f"{style_cap} {title_base.split()[-1] if title_base else 'Design'}", "Instant Download"]
    opt_title = " | ".join(title_parts)
    if len(opt_title) < 120:
        opt_title += " | Digital File"
    opt_title = opt_title[:140]

    # Ensure all tags ≤ 20 chars
    raw_tags = config["tags"]
    clean_tags = [t[:20] for t in raw_tags][:13]

    # Build description
    hook = config["hook"]
    description = (
        f"{hook} {style} {primary_kw.lower()}. Download instantly and start using it today!\n\n"
        f"✅ WHAT'S INCLUDED:\n"
        f"• High-resolution file (300 DPI, print-ready)\n"
        f"• Instant digital download — no waiting, no shipping\n"
        f"• Personal use license included\n\n"
        f"✅ HOW TO USE:\n"
        f"• Download immediately after purchase\n"
        f"• Print at home or at your local print shop\n"
        f"• Compatible with PDF readers, GoodNotes, Notability, and Canva\n\n"
        f"✅ WHY YOU'LL LOVE IT:\n"
        f"• Premium {style} design crafted with care\n"
        f"• Clean, professional look that elevates any space or workflow\n"
        f"• Designed to the quality standard of top Etsy sellers\n\n"
        f"❓ FAQ:\n"
        f"Q: When will I receive my file? A: Immediately after purchase — it's a digital download.\n"
        f"Q: What sizes can I print this? A: Any size — 300 DPI ensures crisp results at 5x7 through 24x36.\n"
        f"Q: Is commercial use allowed? A: Personal use only. Message us for commercial licensing.\n\n"
        f"All files are for PERSONAL USE ONLY. © OnBrandCraftz"
    )

    return json.dumps({
        "product_id": data["product_id"],
        "optimized_title": opt_title,
        "title_length": len(opt_title),
        "optimized_tags": clean_tags,
        "tag_count": len(clean_tags),
        "optimized_description": description,
        "recommended_price": config["price_rec"],
        "ready_to_apply": True,
        "next_step": "Review content then call generate_listing_content with these values to save, then publish_digital_listing to go live.",
    }, indent=2)


def _bulk_seo_audit(store: DataStore) -> str:
    products = store.get("digital_products", default=[])
    active = [p for p in products if p.get("status") in ("approved", "listed")]

    if not active:
        return json.dumps({"message": "No active or approved products to audit.", "count": 0})

    results = []
    for product in active:
        audit_raw = _audit_listing_seo(product["id"], store)
        audit = json.loads(audit_raw)
        results.append({
            "product_id": product["id"],
            "title": (product.get("title", "Untitled"))[:50],
            "status": product.get("status"),
            "seo_score": audit.get("seo_score", 0),
            "grade": audit.get("grade", "F"),
            "top_suggestion": audit.get("suggestions", ["No suggestions"])[0] if audit.get("suggestions") else "Well optimized",
            "needs_improvement": audit.get("needs_improvement", True),
        })

    results.sort(key=lambda r: r["seo_score"])

    critical = [r for r in results if r["seo_score"] < 50]
    needs_work = [r for r in results if 50 <= r["seo_score"] < 80]
    good = [r for r in results if r["seo_score"] >= 80]

    return json.dumps({
        "total_audited": len(results),
        "summary": {
            "critical_f_grade": len(critical),
            "needs_improvement_c_d": len(needs_work),
            "good_a_b": len(good),
        },
        "action_required": critical + needs_work,
        "performing_well": good,
        "next_step": (
            f"{len(critical + needs_work)} listings need SEO improvement. "
            "Run optimize_listing_content on each flagged product_id."
            if critical or needs_work else "All listings are well-optimized!"
        ),
    }, indent=2)


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
