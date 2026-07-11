"""Tool definitions and implementations for the Product Agent."""

import json
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {
        "name": "get_listings",
        "description": "Retrieve product listings, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by listing status: 'all', 'active', 'sold_out', 'inactive'",
                    "enum": ["all", "active", "sold_out", "inactive"],
                }
            },
            "required": ["status"],
        },
    },
    {
        "name": "get_listing_details",
        "description": "Get complete details of a specific product listing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID, e.g. L001"}
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "update_listing",
        "description": "Update fields of an existing product listing (title, price, description, tags, etc.).",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID to update"},
                "updates": {
                    "type": "object",
                    "description": "Key-value pairs of fields to update. Valid fields: title, price, description, tags, processing_days, status",
                },
            },
            "required": ["listing_id", "updates"],
        },
    },
    {
        "name": "update_inventory",
        "description": "Update the available quantity of a listing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID"},
                "quantity": {"type": "integer", "description": "New quantity in stock (0 or more)"},
            },
            "required": ["listing_id", "quantity"],
        },
    },
    {
        "name": "get_low_stock_items",
        "description": "Get listings that are sold out or have low inventory (5 or fewer units).",
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold": {
                    "type": "integer",
                    "description": "Quantity threshold to consider 'low stock' (default: 5)",
                }
            },
            "required": [],
        },
    },
    {
        "name": "create_listing",
        "description": "Create a new product listing in the shop.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "price": {"type": "number", "description": "Price in USD"},
                "quantity": {"type": "integer"},
                "description": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Up to 13 SEO tags",
                },
                "category": {"type": "string"},
                "processing_days": {"type": "integer"},
            },
            "required": ["title", "price", "quantity", "description", "tags", "category", "processing_days"],
        },
    },
    {
        "name": "score_listing_seo",
        "description": "Score a listing's SEO quality from 0-100. Returns score, per-category breakdown, and top 3 improvements.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID to score, e.g. L001"}
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_listing_performance_table",
        "description": "Returns all listings sorted by revenue efficiency (price * sales / views). Flags listings with >500 views and 0 sales as broken.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "suggest_listing_improvements",
        "description": "Generate specific, prioritised improvement recommendations for a given listing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID to analyse, e.g. L001"}
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "bulk_seo_audit",
        "description": "Run SEO scoring on ALL listings and return a report sorted worst-first, with an overall shop SEO score and top recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "clone_listing",
        "description": "Create a variation of an existing listing with field overrides applied. Useful for size variants or bundle variations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_listing_id": {"type": "string", "description": "Listing ID to copy from, e.g. L001"},
                "overrides": {
                    "type": "object",
                    "description": "Fields to override on the clone: title, price, tags, description, quantity, etc.",
                },
            },
            "required": ["source_listing_id", "overrides"],
        },
    },
    {
        "name": "get_trending_categories",
        "description": "Return curated trending Etsy categories for 3D printed home decor and hand painted wood, with avg price and competition level, plus a shop-fit recommendation.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_listings":
        return _get_listings(tool_input["status"], store)
    if tool_name == "get_listing_details":
        return _get_listing_details(tool_input["listing_id"], store)
    if tool_name == "update_listing":
        return _update_listing(tool_input["listing_id"], tool_input["updates"], store)
    if tool_name == "update_inventory":
        return _update_inventory(tool_input["listing_id"], tool_input["quantity"], store)
    if tool_name == "get_low_stock_items":
        threshold = tool_input.get("threshold", 5)
        return _get_low_stock_items(threshold, store)
    if tool_name == "create_listing":
        return _create_listing(tool_input, store)
    if tool_name == "score_listing_seo":
        return _score_listing_seo(tool_input["listing_id"], store)
    if tool_name == "get_listing_performance_table":
        return _get_listing_performance_table(store)
    if tool_name == "suggest_listing_improvements":
        return _suggest_listing_improvements(tool_input["listing_id"], store)
    if tool_name == "bulk_seo_audit":
        return _bulk_seo_audit(store)
    if tool_name == "clone_listing":
        return _clone_listing(tool_input["source_listing_id"], tool_input["overrides"], store)
    if tool_name == "get_trending_categories":
        return _get_trending_categories()
    return f"Unknown product tool: {tool_name}"


def _get_listings(status: str, store: DataStore) -> str:
    listings = store.listings if status == "all" else [l for l in store.listings if l["status"] == status]
    summary = [
        {
            "id": l["id"],
            "title": l["title"],
            "price": l["price"],
            "quantity": l["quantity"],
            "status": l["status"],
            "views": l["views"],
            "favorites": l["favorites"],
            "sales": l["sales"],
        }
        for l in listings
    ]
    return json.dumps({"listings": summary, "count": len(summary)}, indent=2)


def _get_listing_details(listing_id: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})
    return json.dumps(listing, indent=2)


def _update_listing(listing_id: str, updates: dict, store: DataStore) -> str:
    allowed = {"title", "price", "description", "tags", "processing_days", "status", "quantity"}
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    invalid = set(updates.keys()) - allowed
    if invalid:
        return json.dumps({"error": f"Invalid fields: {invalid}. Allowed: {allowed}"})

    changed = {}
    for key, value in updates.items():
        changed[key] = {"from": listing.get(key), "to": value}
        listing[key] = value

    store.save()
    return json.dumps({"success": True, "listing_id": listing_id, "changes": changed}, indent=2)


def _update_inventory(listing_id: str, quantity: int, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    old_qty = listing["quantity"]
    listing["quantity"] = quantity
    listing["status"] = "sold_out" if quantity == 0 else "active"
    store.save()
    return json.dumps(
        {
            "success": True,
            "listing_id": listing_id,
            "previous_quantity": old_qty,
            "new_quantity": quantity,
            "status": listing["status"],
        },
        indent=2,
    )


def _get_low_stock_items(threshold: int, store: DataStore) -> str:
    is_print_to_order = store.shop.get("fulfillment_model") == "print_to_order"
    if is_print_to_order:
        # For print-to-order, only sold-out listings (quantity=0) are truly urgent
        low = [l for l in store.listings if l["quantity"] == 0]
        note = "Print-to-order shop: only sold-out listings (0 units) require action. Low counts like 1-2 are normal."
    else:
        low = [l for l in store.listings if l["quantity"] <= threshold]
        note = f"Listings at or below {threshold} units."
    low.sort(key=lambda l: l["quantity"])
    result = [
        {"id": l["id"], "title": l["title"], "quantity": l["quantity"], "status": l["status"], "price": l["price"]}
        for l in low
    ]
    return json.dumps({"low_stock_items": result, "count": len(result), "fulfillment_model": store.shop.get("fulfillment_model", "standard"), "note": note}, indent=2)


def _create_listing(data: dict, store: DataStore) -> str:
    existing_ids = [l["id"] for l in store.listings]
    nums = [int(lid[1:]) for lid in existing_ids if lid.startswith("L") and lid[1:].isdigit()]
    new_id = f"L{max(nums, default=0) + 1:03d}"

    new_listing = {
        "id": new_id,
        "title": data["title"],
        "price": data["price"],
        "quantity": data["quantity"],
        "views": 0,
        "favorites": 0,
        "sales": 0,
        "tags": data["tags"][:13],
        "category": data["category"],
        "status": "active" if data["quantity"] > 0 else "sold_out",
        "processing_days": data["processing_days"],
        "description": data["description"],
        "images": 0,
    }
    store.listings.append(new_listing)
    store.save()
    return json.dumps({"success": True, "listing": new_listing}, indent=2)


# ---------------------------------------------------------------------------
# SEO & analytics helpers
# ---------------------------------------------------------------------------

def _compute_seo_score(listing: dict) -> dict:
    """Return score (0-100), per-category breakdown, and top_3_improvements for a listing."""
    score = 0
    breakdown = {}
    improvements = []

    # Title length: 70-140 chars = +20pts
    title = listing.get("title", "")
    title_len = len(title)
    if 70 <= title_len <= 140:
        breakdown["title_length"] = {"points": 20, "note": f"Title is {title_len} chars (good: 70-140)"}
        score += 20
    else:
        breakdown["title_length"] = {"points": 0, "note": f"Title is {title_len} chars (need 70-140)"}
        if title_len < 70:
            improvements.append(
                f"Expand title to at least 70 characters (currently {title_len}). "
                "Add material, use case, or style keywords."
            )
        else:
            improvements.append(
                f"Shorten title to 140 characters or fewer (currently {title_len})."
            )

    # Number of tags: 13 = +20pts, <10 = -10pts (floor at 0)
    tags = listing.get("tags", [])
    tag_count = len(tags)
    if tag_count == 13:
        breakdown["tag_count"] = {"points": 20, "note": "All 13 tags used"}
        score += 20
    elif tag_count < 10:
        breakdown["tag_count"] = {"points": 0, "note": f"Only {tag_count} tags (need 13; <10 deducts 10pts)"}
        score = max(0, score - 10)
        improvements.append(
            f"Add more tags — only {tag_count}/13 used. "
            "Fill all 13 slots with a mix of broad, specific, and long-tail phrases."
        )
    else:
        breakdown["tag_count"] = {"points": 0, "note": f"{tag_count} tags (need exactly 13 for full points)"}
        improvements.append(f"Add {13 - tag_count} more tag(s) to reach the full 13.")

    # Description length: >500 chars = +20pts
    description = listing.get("description", "")
    desc_len = len(description)
    if desc_len > 500:
        breakdown["description_length"] = {"points": 20, "note": f"Description is {desc_len} chars (good: >500)"}
        score += 20
    else:
        breakdown["description_length"] = {"points": 0, "note": f"Description is {desc_len} chars (need >500)"}
        improvements.append(
            f"Expand description beyond 500 characters (currently {desc_len}). "
            "Include materials, dimensions, use case, and a shop story."
        )

    # Keywords in title that match tags: +20pts if any overlap
    title_lower = title.lower()
    tag_words = set()
    for tag in tags:
        tag_words.update(tag.lower().split())
    title_words = set(title_lower.split())
    overlap = title_words & tag_words
    if overlap:
        breakdown["keyword_alignment"] = {
            "points": 20,
            "note": f"Title shares keywords with tags: {', '.join(sorted(overlap)[:5])}",
        }
        score += 20
    else:
        breakdown["keyword_alignment"] = {"points": 0, "note": "No overlap between title words and tag words"}
        improvements.append(
            "Align title keywords with your tags. "
            "At least one tag phrase should appear in the title."
        )

    # Price in competitive range $15-65 for digital prints: +20pts
    price = listing.get("price", 0)
    if 15 <= price <= 65:
        breakdown["price_range"] = {"points": 20, "note": f"Price ${price:.2f} is in competitive range ($15-$65)"}
        score += 20
    else:
        breakdown["price_range"] = {
            "points": 0,
            "note": f"Price ${price:.2f} is outside competitive range ($15-$65)",
        }
        if price < 15:
            improvements.append(
                f"Price ${price:.2f} is below the competitive floor of $15. "
                "Low prices signal low quality and reduce perceived value."
            )
        else:
            improvements.append(
                f"Price ${price:.2f} may be above the $65 sweet spot for most digital prints. "
                "Consider whether this category supports a premium price."
            )

    top_3 = improvements[:3]
    return {"score": score, "breakdown": breakdown, "top_3_improvements": top_3}


def _score_listing_seo(listing_id: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})
    result = _compute_seo_score(listing)
    result["listing_id"] = listing_id
    result["title"] = listing.get("title", "")
    return json.dumps(result, indent=2)


def _get_listing_performance_table(store: DataStore) -> str:
    rows = []
    for listing in store.listings:
        views = listing.get("views", 0)
        sales = listing.get("sales", 0)
        price = listing.get("price", 0)
        estimated_revenue = round(price * sales, 2)
        revenue_per_view = round(estimated_revenue / max(views, 1), 4)
        conversion_rate = round(sales / max(views, 1) * 100, 2)
        revenue_efficiency = round((price * sales) / max(views, 1), 4)
        broken = views > 500 and sales == 0

        rows.append({
            "id": listing["id"],
            "title": listing["title"][:40],
            "views": views,
            "sales": sales,
            "price": price,
            "estimated_revenue": estimated_revenue,
            "revenue_per_view": revenue_per_view,
            "conversion_rate": conversion_rate,
            "revenue_efficiency": revenue_efficiency,
            "listing_broken": broken,
        })

    rows.sort(key=lambda r: r["revenue_efficiency"], reverse=True)
    broken_count = sum(1 for r in rows if r["listing_broken"])
    return json.dumps(
        {"listings": rows, "count": len(rows), "broken_listing_count": broken_count},
        indent=2,
    )


def _suggest_listing_improvements(listing_id: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    fixes = []

    # Title too short
    title = listing.get("title", "")
    if len(title.split()) < 5:
        fixes.append({
            "field": "title",
            "priority": "high",
            "issue": f"Title has only {len(title.split())} words — too short for search visibility.",
            "example_text": (
                "3D Printed Geometric Wall Art | Modern Minimalist Home Decor | "
                "Living Room Statement Piece"
            ),
        })

    # Tags below 13
    tags = listing.get("tags", [])
    if len(tags) < 13:
        missing = 13 - len(tags)
        fixes.append({
            "field": "tags",
            "priority": "high",
            "issue": f"Only {len(tags)}/13 tags used — leaving {missing} search slots empty.",
            "example_text": (
                "Add long-tail tags such as: 'minimalist geometric wall art', "
                "'scandinavian home decor', 'modern living room art', "
                "'unique housewarming gift', 'contemporary wall hanging'"
            ),
        })

    # Description too short
    description = listing.get("description", "")
    if len(description) < 200:
        fixes.append({
            "field": "description",
            "priority": "high",
            "issue": f"Description is only {len(description)} chars — needs 500+ for SEO and buyer confidence.",
            "example_text": (
                "Open with your primary keyword, then cover: dimensions, materials used, "
                "printing/painting process, ideal room placement, care instructions, "
                "and a 2-3 sentence shop story."
            ),
        })

    # Price too low
    price = listing.get("price", 0)
    if price < 12:
        fixes.append({
            "field": "price",
            "priority": "high",
            "issue": f"Price ${price:.2f} is below the $12 floor — undervalues the product.",
            "example_text": "Set price to at least $12.00; consider $18-$25 for 3D printed items.",
        })

    # No images
    images = listing.get("images", 0)
    if images == 0:
        fixes.append({
            "field": "images",
            "priority": "medium",
            "issue": "No images on this listing — Etsy ranks listings with photos much higher.",
            "example_text": (
                "Add at least 5 photos: hero shot on white background, lifestyle context shot, "
                "close-up detail, size comparison, and packaging/gift shot."
            ),
        })

    return json.dumps(
        {
            "listing_id": listing_id,
            "title": title,
            "specific_fixes": fixes,
            "fix_count": len(fixes),
        },
        indent=2,
    )


def _bulk_seo_audit(store: DataStore) -> str:
    scored = []
    for listing in store.listings:
        result = _compute_seo_score(listing)
        scored.append({
            "listing_id": listing["id"],
            "title": listing["title"][:50],
            "score": result["score"],
            "top_3_improvements": result["top_3_improvements"],
        })

    scored.sort(key=lambda r: r["score"])

    total = sum(r["score"] for r in scored)
    overall = round(total / max(len(scored), 1), 1)
    count_below_60 = sum(1 for r in scored if r["score"] < 60)

    # Find the most common improvement hint across all listings
    all_improvements = [imp for r in scored for imp in r["top_3_improvements"]]
    top_recommendation = all_improvements[0] if all_improvements else "All listings look good!"

    return json.dumps(
        {
            "overall_shop_seo_score": overall,
            "count_below_60": count_below_60,
            "top_recommendation": top_recommendation,
            "listings": scored,
        },
        indent=2,
    )


def _clone_listing(source_id: str, overrides: dict, store: DataStore) -> str:
    source = store.find_listing(source_id)
    if not source:
        return json.dumps({"error": f"Source listing {source_id} not found"})

    existing_ids = [l["id"] for l in store.listings]
    nums = [int(lid[1:]) for lid in existing_ids if lid.startswith("L") and lid[1:].isdigit()]
    new_id = f"L{max(nums, default=0) + 1:03d}"

    clone = dict(source)
    clone["id"] = new_id
    clone["views"] = 0
    clone["favorites"] = 0
    clone["sales"] = 0

    allowed = {"title", "price", "tags", "description", "quantity", "category", "processing_days", "status"}
    invalid = set(overrides.keys()) - allowed
    if invalid:
        return json.dumps({"error": f"Invalid override fields: {invalid}. Allowed: {allowed}"})

    for key, value in overrides.items():
        clone[key] = value

    if "quantity" in overrides:
        clone["status"] = "active" if overrides["quantity"] > 0 else "sold_out"
    elif clone.get("quantity", 0) > 0:
        clone["status"] = "active"

    if "tags" in clone:
        clone["tags"] = clone["tags"][:13]

    store.listings.append(clone)
    store.save()
    return json.dumps(
        {"success": True, "source_listing_id": source_id, "new_listing": clone},
        indent=2,
    )


def _get_trending_categories() -> str:
    top_categories = [
        {"name": "Minimalist Wall Art", "trend": "↑ 23%", "avg_price": 18, "competition": "medium"},
        {"name": "Personalized Name Signs", "trend": "↑ 45%", "avg_price": 35, "competition": "high"},
        {"name": "Boho Home Decor", "trend": "↑ 18%", "avg_price": 22, "competition": "medium"},
        {"name": "Geometric Plant Holders", "trend": "↑ 31%", "avg_price": 28, "competition": "low"},
        {"name": "Custom Pet Portraits (Print)", "trend": "↑ 67%", "avg_price": 25, "competition": "high"},
    ]
    recommendation = (
        "Best fit for OnBrandCraftz: 'Geometric Plant Holders' — lowest competition, "
        "strong growth (+31%), and a natural match for 3D printing capabilities. "
        "Second choice: 'Minimalist Wall Art' for its medium competition and alignment "
        "with existing hand-painted wood inventory."
    )
    return json.dumps(
        {"top_categories": top_categories, "recommendation": recommendation},
        indent=2,
    )
