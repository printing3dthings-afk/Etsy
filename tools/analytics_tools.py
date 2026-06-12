import json
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {"name": "get_traffic_report", "description": "Get traffic statistics for a period.",
     "input_schema": {"type": "object", "properties": {"period": {"type": "string", "enum": ["this_week", "last_week", "this_month"]}}, "required": ["period"]}},
    {"name": "get_sales_report", "description": "Get sales performance report.",
     "input_schema": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "this_week", "last_week", "this_month", "last_month", "this_year"]}}, "required": ["period"]}},
    {"name": "get_top_performers", "description": "Get top performing listings by a metric.",
     "input_schema": {"type": "object", "properties": {"metric": {"type": "string", "enum": ["views", "sales", "revenue", "favorites"]}, "limit": {"type": "integer"}}, "required": ["metric"]}},
    {"name": "get_conversion_report", "description": "Get conversion rate analysis.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
    {"name": "get_full_dashboard", "description": "Get comprehensive overview of all key shop metrics.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_traffic_report":   return _get_traffic_report(tool_input["period"], store)
    if tool_name == "get_sales_report":     return _get_sales_report(tool_input["period"], store)
    if tool_name == "get_top_performers":   return _get_top_performers(tool_input["metric"], tool_input.get("limit", 5), store)
    if tool_name == "get_conversion_report":return _get_conversion_report(store)
    if tool_name == "get_full_dashboard":   return _get_full_dashboard(store)
    return f"Unknown analytics tool: {tool_name}"


def _get_traffic_report(period: str, store: DataStore) -> str:
    traffic = store.analytics.get("traffic", {}).get(period, {})
    last_period = store.analytics.get("traffic", {}).get("last_week", {})
    views = traffic.get("views", 0)
    last_views = last_period.get("views", 0)
    view_change = round((views - last_views) / last_views * 100, 1) if last_views else 0
    return json.dumps({"period": period, "total_views": views, "total_visits": traffic.get("visits", 0),
                       "view_change_vs_last_week": f"{view_change:+.1f}%",
                       "traffic_sources": {"direct": traffic.get("direct", 0), "etsy_search": traffic.get("etsy_search", 0), "social_media": traffic.get("social_media", 0)}}, indent=2)


def _get_sales_report(period: str, store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    amount = revenue.get(period, 0)
    last = revenue.get("last_week", 0) if "week" in period else revenue.get("last_month", 0)
    change = round((amount - last) / last * 100, 1) if last else 0
    orders_by_status = {}
    for order in store.orders:
        s = order["status"]
        orders_by_status[s] = orders_by_status.get(s, 0) + 1
    return json.dumps({"period": period, "revenue": amount, "change_vs_previous": f"{change:+.1f}%",
                       "orders_by_status": orders_by_status, "total_orders_in_system": len(store.orders),
                       "shop_lifetime": {"total_revenue": store.shop.get("total_revenue"), "total_sales": store.shop.get("total_sales")}}, indent=2)


def _get_top_performers(metric: str, limit: int, store: DataStore) -> str:
    if metric == "revenue":
        sorted_listings = sorted(store.listings, key=lambda l: l["price"] * l["sales"], reverse=True)
        for l in sorted_listings:
            l["estimated_revenue"] = round(l["price"] * l["sales"], 2)
    else:
        sorted_listings = sorted(store.listings, key=lambda l: l.get(metric, 0), reverse=True)
    top = sorted_listings[:limit]
    result = [{"rank": i + 1, "id": l["id"], "title": l["title"],
               metric: l.get(metric, l.get("estimated_revenue", 0)), "price": l["price"], "status": l["status"]} for i, l in enumerate(top)]
    return json.dumps({"top_performers_by": metric, "listings": result}, indent=2)


def _get_conversion_report(store: DataStore) -> str:
    conversions = store.analytics.get("conversions", {})
    traffic = store.analytics.get("traffic", {})
    return json.dumps({
        "conversion_rates": {
            "this_week": f"{conversions.get('this_week', 0) * 100:.2f}%",
            "last_week": f"{conversions.get('last_week', 0) * 100:.2f}%",
            "this_month": f"{conversions.get('this_month', 0) * 100:.2f}%",
        },
        "industry_benchmark": "2-4% is typical for Etsy shops",
        "visits_to_orders": {
            "this_week_visits": traffic.get("this_week", {}).get("visits", 0),
            "etsy_search_share": f"{traffic.get('this_week', {}).get('etsy_search', 0) / max(traffic.get('this_week', {}).get('visits', 1), 1) * 100:.0f}%",
        },
    }, indent=2)


def _get_full_dashboard(store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    traffic = store.analytics.get("traffic", {}).get("this_week", {})
    conversions = store.analytics.get("conversions", {})
    active_listings  = [l for l in store.listings if l["status"] == "active"]
    sold_out         = [l for l in store.listings if l["status"] == "sold_out"]
    pending_orders   = [o for o in store.orders   if o["status"] == "payment_complete"]
    unread_messages  = [m for m in store.messages  if m["status"] == "unread"]
    unresponded      = [r for r in store.reviews   if not r.get("responded")]
    dashboard = {
        "shop": store.shop,
        "today": {"revenue": revenue.get("today", 0), "pending_orders": len(pending_orders),
                  "unread_messages": len(unread_messages), "unresponded_reviews": len(unresponded)},
        "this_week": {"revenue": revenue.get("this_week", 0), "views": traffic.get("views", 0),
                      "visits": traffic.get("visits", 0), "conversion_rate": f"{conversions.get('this_week', 0) * 100:.2f}%"},
        "inventory": {"fulfillment_model": store.shop.get("fulfillment_model", "standard"),
                      "active_listings": len(active_listings), "sold_out_listings": len(sold_out),
                      "note": "Print-to-order: low quantity is normal. Only sold_out (0 units) needs action."},
        "alerts": _build_alerts(store),
    }
    return json.dumps(dashboard, indent=2)


def _build_alerts(store: DataStore) -> list[dict]:
    alerts = []
    is_pto = store.shop.get("fulfillment_model") == "print_to_order"
    for listing in store.listings:
        if listing["status"] == "sold_out" or listing["quantity"] == 0:
            alerts.append({"level": "critical",
                           "message": f"'{listing['title']}' is SOLD OUT. Listing is invisible in Etsy search. Add at least 1 unit."})
        elif not is_pto and listing["quantity"] <= 3:
            alerts.append({"level": "info", "message": f"'{listing['title']}' has only {listing['quantity']} units."})
    unread = [m for m in store.messages if m["status"] == "unread"]
    if unread:
        alerts.append({"level": "info", "message": f"{len(unread)} unread customer message(s) need a response."})
    unresponded = [r for r in store.reviews if not r.get("responded")]
    if unresponded:
        alerts.append({"level": "info", "message": f"{len(unresponded)} review(s) haven't been responded to."})
    if is_pto:
        alerts.append({"level": "info", "message": "Print-to-order shop: low stock counts (1-2) are normal. Only act when a listing hits 0."})
    return alerts
