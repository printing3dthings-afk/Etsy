"""Tool definitions and implementations for the Analytics Agent."""

import json
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {
        "name": "get_traffic_report",
        "description": "Get detailed traffic statistics: views, visits, traffic sources.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["this_week", "last_week", "this_month"],
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_sales_report",
        "description": "Get sales performance report including revenue, order counts, and trends.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["today", "this_week", "last_week", "this_month", "last_month", "this_year"],
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "get_top_performers",
        "description": "Get the top performing listings ranked by views, sales, or revenue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "metric": {
                    "type": "string",
                    "description": "Ranking metric",
                    "enum": ["views", "sales", "revenue", "favorites"],
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of top listings to return (default 5)",
                },
            },
            "required": ["metric"],
        },
    },
    {
        "name": "get_conversion_report",
        "description": "Get conversion rate analysis and funnel metrics.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_full_dashboard",
        "description": "Get a comprehensive overview dashboard of all key shop metrics.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_traffic_report":
        return _get_traffic_report(tool_input["period"], store)
    if tool_name == "get_sales_report":
        return _get_sales_report(tool_input["period"], store)
    if tool_name == "get_top_performers":
        metric = tool_input["metric"]
        limit = tool_input.get("limit", 5)
        return _get_top_performers(metric, limit, store)
    if tool_name == "get_conversion_report":
        return _get_conversion_report(store)
    if tool_name == "get_full_dashboard":
        return _get_full_dashboard(store)
    return f"Unknown analytics tool: {tool_name}"


def _get_traffic_report(period: str, store: DataStore) -> str:
    traffic = store.analytics.get("traffic", {}).get(period, {})
    last_period = store.analytics.get("traffic", {}).get("last_week", {})

    views = traffic.get("views", 0)
    last_views = last_period.get("views", 0)
    view_change = round((views - last_views) / last_views * 100, 1) if last_views else 0

    report = {
        "period": period,
        "total_views": views,
        "total_visits": traffic.get("visits", 0),
        "view_change_vs_last_week": f"{view_change:+.1f}%",
        "traffic_sources": {
            "direct": traffic.get("direct", 0),
            "etsy_search": traffic.get("etsy_search", 0),
            "social_media": traffic.get("social_media", 0),
        },
    }
    return json.dumps(report, indent=2)


def _get_sales_report(period: str, store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    amount = revenue.get(period, 0)
    last = revenue.get("last_week", 0) if "week" in period else revenue.get("last_month", 0)
    change = round((amount - last) / last * 100, 1) if last else 0

    orders_by_status = {}
    for order in store.orders:
        s = order["status"]
        orders_by_status[s] = orders_by_status.get(s, 0) + 1

    report = {
        "period": period,
        "revenue": amount,
        "change_vs_previous": f"{change:+.1f}%",
        "orders_by_status": orders_by_status,
        "total_orders_in_system": len(store.orders),
        "shop_lifetime": {
            "total_revenue": store.shop.get("total_revenue"),
            "total_sales": store.shop.get("total_sales"),
        },
    }
    return json.dumps(report, indent=2)


def _get_top_performers(metric: str, limit: int, store: DataStore) -> str:
    if metric == "revenue":
        sorted_listings = sorted(store.listings, key=lambda l: l["price"] * l["sales"], reverse=True)
        for l in sorted_listings:
            l["estimated_revenue"] = round(l["price"] * l["sales"], 2)
    else:
        sorted_listings = sorted(store.listings, key=lambda l: l.get(metric, 0), reverse=True)

    top = sorted_listings[:limit]
    result = [
        {
            "rank": i + 1,
            "id": l["id"],
            "title": l["title"],
            metric: l.get(metric, l.get("estimated_revenue", 0)),
            "price": l["price"],
            "status": l["status"],
        }
        for i, l in enumerate(top)
    ]
    return json.dumps({"top_performers_by": metric, "listings": result}, indent=2)


def _get_conversion_report(store: DataStore) -> str:
    conversions = store.analytics.get("conversions", {})
    traffic = store.analytics.get("traffic", {})

    report = {
        "conversion_rates": {
            "this_week": f"{conversions.get('this_week', 0) * 100:.2f}%",
            "last_week": f"{conversions.get('last_week', 0) * 100:.2f}%",
            "this_month": f"{conversions.get('this_month', 0) * 100:.2f}%",
        },
        "week_over_week_change": f"{((conversions.get('this_week', 0) - conversions.get('last_week', 0)) / max(conversions.get('last_week', 0.001), 0.001)) * 100:+.1f}%",
        "industry_benchmark": "2-4% is typical for Etsy shops",
        "visits_to_orders": {
            "this_week_visits": traffic.get("this_week", {}).get("visits", 0),
            "etsy_search_share": f"{traffic.get('this_week', {}).get('etsy_search', 0) / max(traffic.get('this_week', {}).get('visits', 1), 1) * 100:.0f}%",
        },
    }
    return json.dumps(report, indent=2)


def _get_full_dashboard(store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    traffic = store.analytics.get("traffic", {}).get("this_week", {})
    conversions = store.analytics.get("conversions", {})

    active_listings = [l for l in store.listings if l["status"] == "active"]
    sold_out = [l for l in store.listings if l["status"] == "sold_out"]
    pending_orders = [o for o in store.orders if o["status"] == "payment_complete"]
    unread_messages = [m for m in store.messages if m["status"] == "unread"]
    unresponded_reviews = [r for r in store.reviews if not r.get("responded")]

    dashboard = {
        "shop": store.shop,
        "today": {
            "revenue": revenue.get("today", 0),
            "pending_orders": len(pending_orders),
            "unread_messages": len(unread_messages),
            "unresponded_reviews": len(unresponded_reviews),
        },
        "this_week": {
            "revenue": revenue.get("this_week", 0),
            "views": traffic.get("views", 0),
            "visits": traffic.get("visits", 0),
            "conversion_rate": f"{conversions.get('this_week', 0) * 100:.2f}%",
        },
        "inventory": {
            "fulfillment_model": store.shop.get("fulfillment_model", "standard"),
            "active_listings": len(active_listings),
            "sold_out_listings": len(sold_out),
            "note": "Print-to-order shop: low quantity is normal. Only sold_out (0 units) needs action.",
        },
        "alerts": _build_alerts(store),
    }
    return json.dumps(dashboard, indent=2)


def _build_alerts(store: DataStore) -> list[dict]:
    alerts = []
    is_print_to_order = store.shop.get("fulfillment_model") == "print_to_order"

    for listing in store.listings:
        if listing["status"] == "sold_out" or listing["quantity"] == 0:
            # Sold out is always critical — listing vanishes from Etsy search
            alerts.append({
                "level": "critical",
                "message": f"'{listing['title']}' is SOLD OUT (quantity=0). Listing is invisible in Etsy search. Add at least 1 unit immediately.",
            })
        elif not is_print_to_order and listing["quantity"] <= 3:
            # Low stock only matters for shops with physical inventory
            alerts.append({"level": "info", "message": f"'{listing['title']}' has only {listing['quantity']} units listed."})

    unread = [m for m in store.messages if m["status"] == "unread"]
    if unread:
        alerts.append({"level": "info", "message": f"{len(unread)} unread customer message(s) need a response."})

    unresponded = [r for r in store.reviews if not r.get("responded")]
    if unresponded:
        alerts.append({"level": "info", "message": f"{len(unresponded)} review(s) haven't been responded to yet."})

    if is_print_to_order:
        alerts.append({
            "level": "info",
            "message": "Print-to-order shop: low stock counts (1-2) are normal. Only act when a listing hits 0 and goes sold out.",
        })

    return alerts
