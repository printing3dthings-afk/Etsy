"""Tool definitions and implementations for the Marketing Agent."""

import json
from tools.data_store import DataStore
from tools import etsy_api
from tools.idea_tools import SUBMIT_IDEA_DEFINITION, handle_submit_idea

TOOL_DEFINITIONS = [
    {
        "name": "get_shop_stats",
        "description": "Get overall shop performance stats: views, visits, favorites, conversion rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Time period",
                    "enum": ["this_week", "last_week", "this_month"],
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "analyze_listing_seo",
        "description": "Analyze the SEO quality of a listing (title, tags, description length).",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "The listing ID to analyze"}
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_trending_keywords",
        "description": "Get the top search terms customers use to find the shop.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_pricing_analysis",
        "description": "Compare shop listing prices against competitor averages to find pricing opportunities.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_promotion_suggestions",
        "description": "Get data-driven promotion and marketing suggestions based on current shop performance.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_top_search_terms",
        "description": "Get the top search terms that bring traffic to the shop from Etsy search.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "search_competitor_prices",
        "description": "Search live Etsy listings to find real competitor prices for a given product keyword. Uses the Etsy API if configured, otherwise returns guidance.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keywords": {
                    "type": "string",
                    "description": "Product keywords to search on Etsy, e.g. '3D printed crystal glow lamp'",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of competitor listings to fetch (max 25)",
                },
            },
            "required": ["keywords"],
        },
    },
    SUBMIT_IDEA_DEFINITION,
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_shop_stats":
        return _get_shop_stats(tool_input["period"], store)
    if tool_name == "analyze_listing_seo":
        return _analyze_listing_seo(tool_input["listing_id"], store)
    if tool_name == "get_trending_keywords":
        return _get_trending_keywords(store)
    if tool_name == "get_pricing_analysis":
        return _get_pricing_analysis(store)
    if tool_name == "get_promotion_suggestions":
        return _get_promotion_suggestions(store)
    if tool_name == "get_top_search_terms":
        return _get_top_search_terms(store)
    if tool_name == "search_competitor_prices":
        return _search_competitor_prices(tool_input["keywords"], tool_input.get("limit", 10), store)
    if tool_name == "submit_idea":
        return handle_submit_idea(tool_input)
    return f"Unknown marketing tool: {tool_name}"


def _get_shop_stats(period: str, store: DataStore) -> str:
    traffic = store.analytics.get("traffic", {}).get(period, {})
    conversions = store.analytics.get("conversions", {})
    revenue = store.analytics.get("revenue", {})
    stats = {
        "period": period,
        "traffic": traffic,
        "conversion_rate": f"{conversions.get(period, 0) * 100:.1f}%",
        "revenue": revenue.get(period, 0),
        "shop_rating": store.shop.get("rating"),
        "total_reviews": store.shop.get("review_count"),
    }
    return json.dumps(stats, indent=2)


def _analyze_listing_seo(listing_id: str, store: DataStore) -> str:
    listing = store.find_listing(listing_id)
    if not listing:
        return json.dumps({"error": f"Listing {listing_id} not found"})

    title = listing.get("title", "")
    tags = listing.get("tags", [])
    description = listing.get("description", "")
    images = listing.get("images", 0)

    issues = []
    suggestions = []
    score = 100

    if len(title) < 40:
        issues.append("Title is short (under 40 chars). Etsy allows 140 chars.")
        suggestions.append("Expand title with more descriptive keywords.")
        score -= 15
    if len(tags) < 13:
        issues.append(f"Only {len(tags)} tags used. Etsy allows 13 tags.")
        suggestions.append("Add more specific and long-tail keyword tags.")
        score -= 10 * (13 - len(tags)) // 3
    if len(description) < 200:
        issues.append("Description is short. Aim for 200+ chars with keywords.")
        score -= 10
    if images < 5:
        issues.append(f"Only {images} images. Use all 10 for best visibility.")
        suggestions.append("Add more photos including lifestyle, scale reference shots.")
        score -= 10

    return json.dumps(
        {
            "listing_id": listing_id,
            "title": title,
            "tag_count": len(tags),
            "tags": tags,
            "description_length": len(description),
            "image_count": images,
            "seo_score": max(score, 0),
            "issues": issues,
            "suggestions": suggestions,
            "views": listing.get("views"),
            "favorites": listing.get("favorites"),
        },
        indent=2,
    )


def _get_trending_keywords(store: DataStore) -> str:
    terms = store.analytics.get("top_search_terms", [])
    return json.dumps({"trending_search_terms": terms, "tip": "Use these keywords prominently in titles and tags."}, indent=2)


def _get_pricing_analysis(store: DataStore) -> str:
    competitor_avgs = store.analytics.get("competitor_avg_price", {})
    analysis = []
    for listing in store.listings:
        lid = listing["id"]
        competitor_avg = competitor_avgs.get(lid)
        if competitor_avg is None:
            continue
        our_price = listing["price"]
        diff = our_price - competitor_avg
        analysis.append(
            {
                "listing_id": lid,
                "title": listing["title"],
                "our_price": our_price,
                "competitor_avg": competitor_avg,
                "difference": round(diff, 2),
                "position": "above_market" if diff > 2 else ("below_market" if diff < -2 else "at_market"),
            }
        )
    return json.dumps({"pricing_analysis": analysis}, indent=2)


def _get_promotion_suggestions(store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    week_rev = revenue.get("this_week", 0)
    last_week = revenue.get("last_week", 0)
    low_stock = [l for l in store.listings if l["quantity"] <= 5]
    high_view_low_sale = [l for l in store.listings if l["views"] > 500 and l["sales"] < 50]

    suggestions = []
    if week_rev > last_week:
        suggestions.append(
            {"type": "momentum", "suggestion": "Revenue is up week-over-week. Capitalize by running a limited-time bundle deal."}
        )
    if low_stock:
        names = [l["title"] for l in low_stock[:3]]
        suggestions.append(
            {"type": "urgency", "suggestion": f"Highlight 'Limited Stock' on: {', '.join(names)} to create urgency."}
        )
    if high_view_low_sale:
        suggestions.append(
            {"type": "conversion", "suggestion": f"'{high_view_low_sale[0]['title']}' has high views but low sales. Consider improving photos or adjusting price."}
        )
    suggestions.append(
        {"type": "seasonal", "suggestion": "May: promote Mother's Day gifts, personalized items, and spring home decor."}
    )
    suggestions.append(
        {"type": "seo", "suggestion": "Add long-tail tags like 'gift for mom 2026' and 'personalized Mother's Day gift' to listings."}
    )
    return json.dumps({"promotion_suggestions": suggestions}, indent=2)


def _get_top_search_terms(store: DataStore) -> str:
    traffic = store.analytics.get("traffic", {}).get("this_week", {})
    terms = store.analytics.get("top_search_terms", [])
    return json.dumps(
        {
            "top_search_terms": terms,
            "etsy_search_visits_this_week": traffic.get("etsy_search", 0),
            "total_visits_this_week": traffic.get("visits", 0),
            "etsy_search_share": f"{traffic.get('etsy_search', 0) / max(traffic.get('visits', 1), 1) * 100:.0f}%",
        },
        indent=2,
    )


def _search_competitor_prices(keywords: str, limit: int, store: DataStore) -> str:
    if not etsy_api.is_configured():
        return json.dumps({
            "status": "api_key_required",
            "message": "Etsy API key not configured. To enable live competitor pricing: "
                       "1) Go to https://www.etsy.com/developers/ "
                       "2) Create an app and copy your Keystring "
                       "3) Add ETSY_API_KEY=<your_key> to your .env file. "
                       "Then re-run this search for live competitor prices.",
            "keywords": keywords,
        }, indent=2)

    try:
        client = etsy_api.get_client()
        results = client.search_listings(keywords=keywords, limit=min(limit, 25))
        listings = results.get("results", [])

        if not listings:
            return json.dumps({"keywords": keywords, "results": [], "message": "No listings found."}, indent=2)

        prices = []
        for listing in listings:
            price_data = listing.get("price", {})
            amount = float(price_data.get("amount", 0)) / max(price_data.get("divisor", 100), 1)
            prices.append({
                "title": listing.get("title", "")[:80],
                "price": round(amount, 2),
                "currency": price_data.get("currency_code", "USD"),
                "shop_id": listing.get("shop_id"),
                "listing_id": listing.get("listing_id"),
                "url": f"https://www.etsy.com/listing/{listing.get('listing_id', '')}",
            })

        prices.sort(key=lambda x: x["price"])
        price_values = [p["price"] for p in prices]
        avg = round(sum(price_values) / len(price_values), 2) if price_values else 0
        low = min(price_values) if price_values else 0
        high = max(price_values) if price_values else 0

        return json.dumps({
            "keywords": keywords,
            "competitor_count": len(prices),
            "price_summary": {"min": low, "max": high, "average": avg},
            "listings": prices,
        }, indent=2)

    except etsy_api.EtsyAPIError as e:
        return json.dumps({"error": str(e), "keywords": keywords}, indent=2)
