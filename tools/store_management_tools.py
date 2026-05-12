"""
Store Management Tools — monitor and control the Etsy shop page.

Covers: shop health, listing performance, announcements, section management,
renewal alerts, pricing recommendations, and featured listings.

Live Etsy API calls (read-only) use ETSY_API_KEY.
Write operations (announcements, sections) require ETSY_ACCESS_TOKEN.
"""

import json
import os
from datetime import date, timedelta

from tools.data_store import DataStore
from tools.etsy_api import EtsyAPIClient, EtsyAPIError, is_configured

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_shop_overview",
        "description": (
            "Get a complete health overview of the shop: listing counts, revenue, ratings, "
            "stock levels, renewal alerts, and overall store health score."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_listing_performance",
        "description": "Get performance metrics (views, favorites, sales, conversion rate) for all listings, sorted by best performer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["views", "favorites", "sales", "conversion"],
                    "description": "Sort listings by this metric",
                    "default": "views",
                },
                "limit": {"type": "integer", "description": "Max results to return", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "get_renewal_alerts",
        "description": "Get listings that are expiring within the next 30 days and need renewal.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days_ahead": {
                    "type": "integer",
                    "description": "Alert window in days (default: 30)",
                    "default": 30,
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_shop_announcement",
        "description": "Get the current shop announcement text.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_shop_announcement",
        "description": "Update the shop announcement (shown at the top of your Etsy shop page).",
        "input_schema": {
            "type": "object",
            "properties": {
                "announcement": {
                    "type": "string",
                    "description": "New announcement text (max 500 chars recommended)",
                }
            },
            "required": ["announcement"],
        },
    },
    {
        "name": "get_pricing_recommendations",
        "description": "Compare current prices to competitor averages and suggest optimal pricing.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_shop_sections",
        "description": "Get all shop sections/categories and the number of listings in each.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_shop_section",
        "description": "Add a new section to the shop (e.g., 'Digital Planners', 'Digital Art').",
        "input_schema": {
            "type": "object",
            "properties": {
                "section_name": {"type": "string", "description": "Name for the new section"}
            },
            "required": ["section_name"],
        },
    },
    {
        "name": "get_live_shop_data",
        "description": "Fetch live shop data from the Etsy API (requires ETSY_API_KEY).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_shop_overview":
        return _get_shop_overview(store)
    if tool_name == "get_listing_performance":
        return _get_listing_performance(tool_input, store)
    if tool_name == "get_renewal_alerts":
        return _get_renewal_alerts(tool_input.get("days_ahead", 30), store)
    if tool_name == "get_shop_announcement":
        return _get_shop_announcement(store)
    if tool_name == "set_shop_announcement":
        return _set_shop_announcement(tool_input["announcement"], store)
    if tool_name == "get_pricing_recommendations":
        return _get_pricing_recommendations(store)
    if tool_name == "get_shop_sections":
        return _get_shop_sections(store)
    if tool_name == "add_shop_section":
        return _add_shop_section(tool_input["section_name"], store)
    if tool_name == "get_live_shop_data":
        return _get_live_shop_data(store)
    return f"Unknown store management tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _get_shop_overview(store: DataStore) -> str:
    shop = store.shop
    listings = store.listings
    orders = store.orders
    digital_products = store.get("digital_products", default=[])

    active = [l for l in listings if l.get("status") == "active"]
    sold_out = [l for l in listings if l.get("status") == "sold_out"]
    digital_listed = [p for p in digital_products if p.get("status") == "listed"]
    digital_pending = [p for p in digital_products if p.get("status") in ("approved", "qc_pending", "concept")]

    pending_orders = [o for o in orders if o.get("status") == "payment_complete"]
    today_str = str(date.today())
    overdue = [o for o in pending_orders if o.get("ship_by", "9999") < today_str]

    # Simple health score (0-100)
    score = 100
    if sold_out:
        score -= min(len(sold_out) * 10, 30)
    if overdue:
        score -= min(len(overdue) * 15, 30)
    if not shop.get("announcement"):
        score -= 5

    health = "Excellent" if score >= 90 else "Good" if score >= 75 else "Needs Attention" if score >= 60 else "Critical"

    return json.dumps({
        "shop": {
            "name": shop.get("name"),
            "url": shop.get("url"),
            "total_sales": shop.get("total_sales", 0),
            "total_revenue": shop.get("total_revenue", 0),
            "rating": shop.get("rating", 0),
            "review_count": shop.get("review_count", 0),
        },
        "listings": {
            "total": len(listings),
            "active": len(active),
            "sold_out": len(sold_out),
            "digital_live": len(digital_listed),
            "digital_pipeline": len(digital_pending),
        },
        "orders": {
            "pending_fulfillment": len(pending_orders),
            "overdue": len(overdue),
        },
        "health_score": score,
        "health_status": health,
        "alerts": (
            ([f"SOLD OUT: {l['title'][:50]}" for l in sold_out] if sold_out else []) +
            ([f"OVERDUE ORDER: {o['id']}" for o in overdue] if overdue else [])
        ),
    }, indent=2)


def _get_listing_performance(data: dict, store: DataStore) -> str:
    listings = store.listings
    sort_by = data.get("sort_by", "views")
    limit = data.get("limit", 20)

    def conversion_rate(l: dict) -> float:
        views = l.get("views", 0)
        sales = l.get("sales", 0)
        return round((sales / views * 100), 2) if views > 0 else 0.0

    rows = [
        {
            "id": l["id"],
            "title": l["title"][:60],
            "price": l.get("price", 0),
            "views": l.get("views", 0),
            "favorites": l.get("favorites", 0),
            "sales": l.get("sales", 0),
            "conversion_rate_pct": conversion_rate(l),
            "revenue": round(l.get("price", 0) * l.get("sales", 0), 2),
            "status": l.get("status"),
            "type": l.get("type", "physical"),
        }
        for l in listings
    ]

    sort_key = {
        "views": lambda r: r["views"],
        "favorites": lambda r: r["favorites"],
        "sales": lambda r: r["sales"],
        "conversion": lambda r: r["conversion_rate_pct"],
    }.get(sort_by, lambda r: r["views"])

    rows.sort(key=sort_key, reverse=True)
    rows = rows[:limit]

    total_revenue = sum(r["revenue"] for r in rows)
    return json.dumps({
        "sorted_by": sort_by,
        "listings": rows,
        "count": len(rows),
        "total_revenue_shown": round(total_revenue, 2),
    }, indent=2)


def _get_renewal_alerts(days_ahead: int, store: DataStore) -> str:
    listings = store.listings
    today = date.today()
    cutoff = today + timedelta(days=days_ahead)
    cutoff_str = str(cutoff)
    today_str = str(today)

    expiring = []
    for l in listings:
        renews = l.get("renews")
        if not renews:
            continue
        if renews <= cutoff_str:
            days_left = (date.fromisoformat(renews) - today).days
            expiring.append({
                "id": l["id"],
                "title": l["title"][:60],
                "renews": renews,
                "days_until_expiry": days_left,
                "urgency": "EXPIRED" if renews < today_str else ("URGENT" if days_left <= 7 else "UPCOMING"),
                "status": l.get("status"),
            })

    expiring.sort(key=lambda x: x["renews"])

    return json.dumps({
        "renewal_alerts": expiring,
        "count": len(expiring),
        "alert_window_days": days_ahead,
        "note": "Etsy charges $0.20 per listing renewal. Active listings auto-renew.",
    }, indent=2)


def _get_shop_announcement(store: DataStore) -> str:
    announcement = store.shop.get("announcement", "")
    return json.dumps({
        "current_announcement": announcement or "(No announcement set)",
        "char_count": len(announcement),
        "tip": "Use announcements for sales, new arrivals, or holiday closures.",
    }, indent=2)


def _set_shop_announcement(announcement: str, store: DataStore) -> str:
    # Update local data store
    store.shop["announcement"] = announcement
    store.save()

    # Try live Etsy API if configured
    if is_configured() and os.getenv("ETSY_ACCESS_TOKEN"):
        try:
            client = EtsyAPIClient()
            client._request("PUT", f"shops/{client.shop_id}", body={"announcement": announcement})
            return json.dumps({
                "success": True,
                "announcement": announcement,
                "synced_to_etsy": True,
            }, indent=2)
        except EtsyAPIError as e:
            return json.dumps({
                "success": True,
                "announcement": announcement,
                "synced_to_etsy": False,
                "etsy_error": str(e),
                "note": "Saved locally. Configure ETSY_ACCESS_TOKEN to sync to live shop.",
            }, indent=2)

    return json.dumps({
        "success": True,
        "announcement": announcement,
        "synced_to_etsy": False,
        "note": "Saved locally. Add ETSY_ACCESS_TOKEN to sync to live Etsy shop.",
    }, indent=2)


def _get_pricing_recommendations(store: DataStore) -> str:
    listings = store.listings
    competitor_prices = store.analytics.get("competitor_avg_price", {})
    competitor_notes = store.analytics.get("competitor_price_notes", {})

    recommendations = []
    for l in listings:
        lid = l["id"]
        comp_price = competitor_prices.get(lid)
        if comp_price is None:
            continue
        current = l["price"]
        gap = round(comp_price - current, 2)
        pct = round(gap / comp_price * 100, 1) if comp_price else 0
        action = "RAISE" if gap > 2 else ("LOWER" if gap < -2 else "HOLD")
        recommendations.append({
            "id": lid,
            "title": l["title"][:55],
            "current_price": current,
            "competitor_avg": comp_price,
            "gap": gap,
            "gap_pct": f"{pct:+.1f}%",
            "action": action,
            "note": competitor_notes.get(lid, ""),
        })

    recommendations.sort(key=lambda r: abs(r["gap"]), reverse=True)
    urgent = [r for r in recommendations if r["action"] != "HOLD"]

    return json.dumps({
        "pricing_recommendations": recommendations,
        "urgent_changes": urgent,
        "total_listings_analyzed": len(recommendations),
        "tip": "Raising prices on underpriced items can increase perceived value and revenue.",
    }, indent=2)


def _get_shop_sections(store: DataStore) -> str:
    sections = store.get("shop_sections", default=[])
    if not sections:
        # Build sections from listings
        by_section: dict[str, int] = {}
        for l in store.listings:
            cat = l.get("category", "Other").split(" > ")[0]
            by_section[cat] = by_section.get(cat, 0) + 1
        for dp in store.get("digital_products", default=[]):
            if dp.get("status") == "listed":
                sec = "Digital Downloads"
                by_section[sec] = by_section.get(sec, 0) + 1
        sections = [{"name": k, "listing_count": v} for k, v in by_section.items()]

    return json.dumps({
        "shop_sections": sections,
        "total_sections": len(sections),
        "tip": "Well-organized sections help buyers browse and improve shop SEO.",
    }, indent=2)


def _add_shop_section(section_name: str, store: DataStore) -> str:
    sections = store.get("shop_sections", default=[])
    exists = any(s["name"].lower() == section_name.lower() for s in sections)
    if exists:
        return json.dumps({"warning": f"Section '{section_name}' already exists."})

    sections.append({"name": section_name, "listing_count": 0, "created_at": str(date.today())})
    store.set(sections, "shop_sections")
    store.save()

    return json.dumps({
        "success": True,
        "section_added": section_name,
        "total_sections": len(sections),
        "note": "Section saved locally. Sections sync to Etsy when listings are published.",
    }, indent=2)


def _get_live_shop_data(store: DataStore) -> str:
    if not is_configured():
        return json.dumps({
            "warning": "ETSY_API_KEY not configured.",
            "action": "Add ETSY_API_KEY to .env to fetch live shop data.",
        })
    try:
        client = EtsyAPIClient()
        shop_data = client.get_shop()
        listings_data = client.get_shop_listings(limit=25)
        store.shop["live_refresh_date"] = str(date.today())
        store.save()
        return json.dumps({
            "shop": {
                "shop_id": shop_data.get("shop_id"),
                "shop_name": shop_data.get("shop_name"),
                "title": shop_data.get("title"),
                "announcement": shop_data.get("announcement"),
                "currency_code": shop_data.get("currency_code"),
                "listing_active_count": shop_data.get("listing_active_count"),
                "digital_listing_count": shop_data.get("digital_listing_count", 0),
                "favorers_count": shop_data.get("num_favorers", 0),
            },
            "active_listings_count": listings_data.get("count", 0),
        }, indent=2)
    except EtsyAPIError as e:
        return json.dumps({"error": str(e)})
