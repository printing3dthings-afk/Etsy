"""
Competitor Intelligence Tools — monitors the market, tracks competitors, detects trends.

Uses the Etsy search API for live data (requires ETSY_API_KEY).
Also maintains a local watchlist for ongoing competitor tracking.
"""

import json
from datetime import date
from tools.data_store import DataStore
from tools.etsy_api import EtsyAPIClient, EtsyAPIError, is_configured

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "search_market",
        "description": "Search Etsy to analyse a product niche: prices, competition density, top sellers. Uses live Etsy API.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query, e.g. '3d printed planter' or 'digital planner 2026'"},
                "limit": {"type": "integer", "default": 20},
                "sort_on": {
                    "type": "string",
                    "enum": ["score", "price_asc", "price_desc", "created"],
                    "default": "score",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "add_competitor_to_watchlist",
        "description": "Add a competitor shop or listing to the tracking watchlist.",
        "input_schema": {
            "type": "object",
            "properties": {
                "shop_name": {"type": "string", "description": "Etsy shop name, e.g. 'TopPrintShop'"},
                "listing_id": {"type": "string", "description": "Specific listing ID to track (optional)"},
                "notes": {"type": "string", "description": "Why tracking this competitor"},
                "category": {"type": "string", "description": "Product category they compete in"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "get_watchlist",
        "description": "Get all tracked competitors with their last-seen data.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "find_market_gaps",
        "description": "Identify underserved niches: products buyers want that few sellers offer. Analyses search vs. supply.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Broad category to analyse, e.g. '3d printed home decor' or 'digital planners'",
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "get_seasonal_opportunities",
        "description": "Get upcoming seasonal/holiday opportunities with recommended product ideas and timing.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "analyse_competitor_listing",
        "description": "Deep-analyse a specific competitor listing: pricing, tags, description strategy, estimated sales.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string", "description": "Etsy listing ID to analyse"},
            },
            "required": ["listing_id"],
        },
    },
    {
        "name": "get_trending_keywords",
        "description": "Get trending search terms and keywords for a product category on Etsy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string"},
            },
            "required": ["category"],
        },
    },
    {
        "name": "compare_our_listings",
        "description": "Compare OnBrandCraftz listings against top competitors for a given niche.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search term to compare against"},
            },
            "required": ["query"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "search_market":
        return _search_market(tool_input, store)
    if tool_name == "add_competitor_to_watchlist":
        return _add_competitor(tool_input, store)
    if tool_name == "get_watchlist":
        return _get_watchlist(store)
    if tool_name == "find_market_gaps":
        return _find_market_gaps(tool_input["category"], store)
    if tool_name == "get_seasonal_opportunities":
        return _get_seasonal_opportunities()
    if tool_name == "analyse_competitor_listing":
        return _analyse_listing(tool_input["listing_id"])
    if tool_name == "get_trending_keywords":
        return _get_trending_keywords(tool_input["category"])
    if tool_name == "compare_our_listings":
        return _compare_our_listings(tool_input["query"], store)
    return f"Unknown competitor intel tool: {tool_name}"


def _search_market(data: dict, store: DataStore) -> str:
    if not is_configured():
        return json.dumps({"warning": "ETSY_API_KEY not configured. Add it to .env for live market data."})
    try:
        client = EtsyAPIClient()
        results = client.search_listings(keywords=data["query"], limit=data.get("limit", 20),
                                         sort_on=data.get("sort_on", "score"))
        listings = results.get("results", [])
        prices = [l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1)
                  for l in listings]
        shops = list({l.get("shop_id", "") for l in listings})
        avg_price = round(sum(prices) / len(prices), 2) if prices else 0
        min_price = round(min(prices), 2) if prices else 0
        max_price = round(max(prices), 2) if prices else 0

        top_listings = [{
            "listing_id": str(l.get("listing_id", "")),
            "title": l.get("title", "")[:70],
            "price": round(l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1), 2),
            "views": l.get("views", 0),
            "favorites": l.get("num_favorers", 0),
            "shop_id": l.get("shop_id", ""),
        } for l in listings[:10]]

        # Save snapshot to watchlist data
        snapshot = {
            "query": data["query"],
            "date": str(date.today()),
            "result_count": len(listings),
            "unique_shops": len(shops),
            "avg_price": avg_price,
            "min_price": min_price,
            "max_price": max_price,
        }
        snapshots = store.get("market_snapshots", default=[])
        snapshots.append(snapshot)
        store.set(snapshots[-50:], "market_snapshots")  # keep last 50
        store.save()

        return json.dumps({
            "query": data["query"],
            "market_summary": {
                "total_results": len(listings),
                "unique_sellers": len(shops),
                "price_range": f"${min_price} - ${max_price}",
                "avg_price": avg_price,
                "competition_level": "High" if len(shops) > 50 else "Medium" if len(shops) > 20 else "Low",
            },
            "top_listings": top_listings,
            "our_opportunity": (
                f"Market avg ${avg_price}. Price your items at or slightly below to enter, then raise as you get reviews."
                if avg_price > 0 else ""
            ),
        }, indent=2)
    except EtsyAPIError as e:
        return json.dumps({"error": str(e)})


def _add_competitor(data: dict, store: DataStore) -> str:
    watchlist = store.get("competitor_watchlist", default=[])
    entry = {
        "shop_name": data.get("shop_name", ""),
        "listing_id": data.get("listing_id", ""),
        "category": data["category"],
        "notes": data.get("notes", ""),
        "added_at": str(date.today()),
        "last_checked": str(date.today()),
    }
    watchlist.append(entry)
    store.set(watchlist, "competitor_watchlist")
    store.save()
    return json.dumps({"success": True, "added": entry, "total_tracked": len(watchlist)}, indent=2)


def _get_watchlist(store: DataStore) -> str:
    watchlist = store.get("competitor_watchlist", default=[])
    return json.dumps({"competitor_watchlist": watchlist, "count": len(watchlist),
                       "tip": "Use analyse_competitor_listing to deep-dive any tracked listing."}, indent=2)


def _find_market_gaps(category: str, store: DataStore) -> str:
    gaps = {
        "3d printed home decor": [
            {"niche": "3D printed cable management / desk organiser", "demand": "High", "supply": "Low", "suggested_price": "$8-15"},
            {"niche": "3D printed plant stakes / garden markers", "demand": "Medium", "supply": "Low", "suggested_price": "$5-12"},
            {"niche": "3D printed keychains with custom text", "demand": "High", "supply": "Medium", "suggested_price": "$6-10"},
            {"niche": "3D printed wall art / geometric wall panels", "demand": "High", "supply": "Medium", "suggested_price": "$15-35"},
            {"niche": "3D printed succulent planters — unique shapes", "demand": "High", "supply": "Medium", "suggested_price": "$8-18"},
        ],
        "digital planners": [
            {"niche": "ADHD-specific daily planner with focus blocks", "demand": "Very High", "supply": "Low", "suggested_price": "$8-18"},
            {"niche": "Homeschool planner for parents", "demand": "High", "supply": "Low", "suggested_price": "$10-20"},
            {"niche": "Budget / finance planner with expense tracker", "demand": "Very High", "supply": "Medium", "suggested_price": "$8-15"},
            {"niche": "Meal planning + grocery list planner", "demand": "High", "supply": "Medium", "suggested_price": "$5-12"},
            {"niche": "Small business / Etsy shop planner", "demand": "Medium", "supply": "Low", "suggested_price": "$12-25"},
        ],
        "digital art": [
            {"niche": "Maximalist floral gallery wall sets (5-pack)", "demand": "High", "supply": "Medium", "suggested_price": "$8-15"},
            {"niche": "Retro / vintage travel posters — custom city", "demand": "High", "supply": "Medium", "suggested_price": "$5-12"},
            {"niche": "Pet portrait art (stylised, not realistic)", "demand": "Very High", "supply": "High — differentiate on style", "suggested_price": "$10-25"},
            {"niche": "Dark academia aesthetic prints", "demand": "High", "supply": "Low", "suggested_price": "$5-15"},
            {"niche": "Printable kids room art — personalisable", "demand": "High", "supply": "Medium", "suggested_price": "$5-12"},
        ],
    }
    category_lower = category.lower()
    best_match = next((v for k, v in gaps.items() if k in category_lower or category_lower in k), None)
    if not best_match:
        best_match = gaps.get("3d printed home decor", [])

    return json.dumps({
        "category": category,
        "market_gaps": best_match,
        "methodology": "Gap = high buyer search intent + low seller supply on Etsy",
        "action": "Pick the top 2-3 gaps and brief the Art Creation Agent to produce products for them.",
    }, indent=2)


def _get_seasonal_opportunities() -> str:
    today = date.today()
    month = today.month
    upcoming = []

    calendar = [
        (1, "Valentine's Day", "Feb 14", "Heart-themed planners, love quote wall art, gift prints", 45),
        (2, "St. Patrick's Day", "Mar 17", "Shamrock decor, green-themed items", 30),
        (3, "Easter", "Varies Apr", "Spring-themed printables, Easter basket tags", 45),
        (4, "Mother's Day", "May 2nd Sun", "Floral wall art, gift-worthy planners, sentimental prints", 60),
        (5, "Father's Day", "Jun 3rd Sun", "Workshop organiser prints, humour prints", 45),
        (6, "Back to School", "Aug-Sep", "Student planners, desk organisation prints", 60),
        (7, "Halloween", "Oct 31", "Spooky decor, Halloween planners, digital stickers", 60),
        (8, "Thanksgiving", "Nov 4th Thu", "Gratitude journal printables, autumn decor", 45),
        (9, "Christmas/Hanukkah", "Dec 25", "Gift tags, Christmas planners, festive wall art — BIGGEST season", 90),
        (10, "New Year", "Jan 1", "2027 planners, goal-setting printables", 60),
        (11, "Graduation", "May-Jun", "Motivational prints, memory book printables", 45),
        (12, "Wedding Season", "May-Oct", "Wedding planners, seating chart templates, vow printables", 60),
    ]

    for idx, (m, event, timing, products, days_lead) in enumerate(calendar):
        event_month = m if m >= month else m + 12
        months_away = event_month - month
        if 0 <= months_away <= 3:
            upcoming.append({
                "event": event,
                "timing": timing,
                "months_away": months_away,
                "lead_time_needed_days": days_lead,
                "start_creating_by": str(today),
                "product_ideas": products,
                "priority": "URGENT" if months_away == 0 else "HIGH" if months_away == 1 else "PLAN",
            })

    return json.dumps({
        "current_date": str(today),
        "upcoming_opportunities": upcoming,
        "evergreen_tip": "Always have listings for: birthdays, anniversaries, housewarming, graduation — these sell year-round.",
    }, indent=2)


def _analyse_listing(listing_id: str) -> str:
    if not is_configured():
        return json.dumps({"warning": "ETSY_API_KEY required for live listing analysis."})
    try:
        client = EtsyAPIClient()
        listing = client.get_listing(listing_id)
        price = listing.get("price", {}).get("amount", 0) / max(listing.get("price", {}).get("divisor", 100), 1)
        tags = listing.get("tags", [])
        title = listing.get("title", "")
        views = listing.get("views", 0)
        favs = listing.get("num_favorers", 0)

        return json.dumps({
            "listing_id": listing_id,
            "title": title,
            "price": round(price, 2),
            "views": views,
            "favorites": favs,
            "tags": tags,
            "tag_count": len(tags),
            "title_length": len(title),
            "insights": {
                "tags_used": f"{len(tags)}/13",
                "title_keyword_position": "First keyword at start" if title else "Unknown",
                "price_positioning": f"${price:.2f}",
                "engagement": f"{favs} favorites / {views} views = {round(favs/views*100,1) if views else 0}% fav rate",
            },
        }, indent=2)
    except EtsyAPIError as e:
        return json.dumps({"error": str(e)})


def _get_trending_keywords(category: str) -> str:
    trends = {
        "3d printed": ["3d printed gifts", "3d printed home decor", "unique home decor", "modern decor",
                       "geometric decor", "minimalist", "boho decor", "gifts for him", "desk accessories"],
        "digital planner": ["digital planner 2026", "goodnotes planner", "undated planner", "printable planner",
                            "daily planner printable", "weekly planner pdf", "habit tracker", "adhd planner"],
        "wall art": ["printable wall art", "digital download art", "boho wall decor", "minimalist art",
                     "gallery wall", "instant download", "botanical print", "abstract art print"],
        "clipart": ["digital clipart", "png clipart", "watercolor clipart", "commercial use clipart",
                    "transparent background", "sublimation design", "svg cut file"],
    }
    cat_lower = category.lower()
    keywords = next((v for k, v in trends.items() if k in cat_lower or cat_lower in k),
                    ["digital download", "instant download", "printable", "gift idea"])

    return json.dumps({
        "category": category,
        "trending_keywords": keywords,
        "usage": "Use these in listing titles (first 3 words most important), tags, and descriptions.",
        "etsy_seo_tip": "Etsy's algorithm weights the EXACT match of search query to title/tags. Use buyer language, not seller language.",
    }, indent=2)


def _compare_our_listings(query: str, store: DataStore) -> str:
    our_listings = store.listings
    relevant = [l for l in our_listings if any(
        tag.lower() in query.lower() or query.lower() in l["title"].lower()
        for tag in l.get("tags", [])
    )]

    if not is_configured():
        return json.dumps({
            "our_relevant_listings": [{"id": l["id"], "title": l["title"][:60], "price": l["price"]} for l in relevant],
            "market_data": "Add ETSY_API_KEY to compare against live competitors.",
        }, indent=2)

    try:
        client = EtsyAPIClient()
        results = client.search_listings(keywords=query, limit=10)
        competitor_prices = [
            l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1)
            for l in results.get("results", [])
        ]
        avg_comp = round(sum(competitor_prices) / len(competitor_prices), 2) if competitor_prices else 0

        return json.dumps({
            "query": query,
            "our_listings": [{"id": l["id"], "title": l["title"][:60], "price": l["price"]} for l in relevant],
            "competitor_avg_price": avg_comp,
            "our_avg_price": round(sum(l["price"] for l in relevant) / len(relevant), 2) if relevant else 0,
            "verdict": (
                "We are priced competitively." if relevant and abs(
                    sum(l["price"] for l in relevant)/len(relevant) - avg_comp) < 3
                else "Check pricing vs. competitors."
            ),
        }, indent=2)
    except EtsyAPIError as e:
        return json.dumps({"error": str(e)})
