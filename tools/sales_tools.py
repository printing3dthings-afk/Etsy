"""Tool definitions and implementations for the Sales Agent."""
from __future__ import annotations

import json
from datetime import date, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {
        "name": "get_orders",
        "description": "Retrieve orders filtered by status. Use this to see what orders need attention.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by order status: 'all', 'payment_complete' (needs fulfillment), 'shipped', 'complete'",
                    "enum": ["all", "payment_complete", "shipped", "complete"],
                }
            },
            "required": ["status"],
        },
    },
    {
        "name": "get_order_details",
        "description": "Get full details of a specific order including buyer info and customization notes.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID, e.g. O10045"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_revenue_summary",
        "description": "Get revenue and sales statistics for a time period.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "Time period for the summary",
                    "enum": ["today", "this_week", "last_week", "this_month", "last_month", "this_year"],
                }
            },
            "required": ["period"],
        },
    },
    {
        "name": "update_order_status",
        "description": "Update the status of an order (e.g., mark as shipped with tracking number).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID"},
                "new_status": {
                    "type": "string",
                    "description": "New status for the order",
                    "enum": ["payment_complete", "shipped", "complete", "cancelled"],
                },
                "tracking_number": {
                    "type": "string",
                    "description": "USPS/UPS/FedEx tracking number (required when marking as shipped)",
                },
            },
            "required": ["order_id", "new_status"],
        },
    },
    {
        "name": "get_shipping_queue",
        "description": "Get all orders that are paid and waiting to be shipped, sorted by ship-by date.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "forecast_revenue",
        "description": "Projects revenue for next 7, 14, and 30 days based on current this_week run-rate. Compares against 30-day targets and returns on_track booleans and gaps.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "analyze_sales_trends",
        "description": "Identifies top-selling product categories, best day of week, and week-over-week revenue trend from order history.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_sales_velocity",
        "description": "Calculates sales velocity (sales per day) for each listing, sorted highest first. Flags listings as hot (>5/month), steady (1-5/month), or stale (0 sales).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "log_sale",
        "description": "Records a new sale event. Increments total_sales by 1 and adds amount to today and this_week revenue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "amount": {
                    "type": "number",
                    "description": "Sale amount in USD",
                },
                "listing_id": {
                    "type": "string",
                    "description": "Optional listing ID associated with the sale",
                },
            },
            "required": ["amount"],
        },
    },
    {
        "name": "flag_overdue_orders",
        "description": "Returns all orders where ship_by date is today or earlier and status is payment_complete. Includes days_overdue, severity, and recommended_action.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_price_optimization",
        "description": "Analyzes listing prices against views and sales to detect under/overpriced items. Returns pricing_recommendations with suggested_action and reasoning.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_orders":
        return _get_orders(tool_input["status"], store)
    if tool_name == "get_order_details":
        return _get_order_details(tool_input["order_id"], store)
    if tool_name == "get_revenue_summary":
        return _get_revenue_summary(tool_input["period"], store)
    if tool_name == "update_order_status":
        return _update_order_status(tool_input, store)
    if tool_name == "get_shipping_queue":
        return _get_shipping_queue(store)
    if tool_name == "forecast_revenue":
        return _forecast_revenue(store)
    if tool_name == "analyze_sales_trends":
        return _analyze_sales_trends(store)
    if tool_name == "get_sales_velocity":
        return _get_sales_velocity(store)
    if tool_name == "log_sale":
        return _log_sale(tool_input["amount"], tool_input.get("listing_id"), store)
    if tool_name == "flag_overdue_orders":
        return _flag_overdue_orders(store)
    if tool_name == "get_price_optimization":
        return _get_price_optimization(store)
    return f"Unknown sales tool: {tool_name}"


def _get_orders(status: str, store: DataStore) -> str:
    orders = store.orders if status == "all" else [o for o in store.orders if o["status"] == status]
    if not orders:
        return json.dumps({"orders": [], "count": 0, "message": f"No orders with status '{status}'"})
    return json.dumps({"orders": orders, "count": len(orders)}, indent=2)


def _get_order_details(order_id: str, store: DataStore) -> str:
    order = store.find_order(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})
    return json.dumps(order, indent=2)


def _get_revenue_summary(period: str, store: DataStore) -> str:
    revenue_data = store.analytics.get("revenue", {})
    amount = revenue_data.get(period, 0)
    week_revenue = revenue_data.get("this_week", 0)
    last_week = revenue_data.get("last_week", 0)
    change_pct = round(((week_revenue - last_week) / last_week * 100) if last_week else 0, 1)

    completed = [o for o in store.orders if o["status"] == "complete"]
    summary = {
        "period": period,
        "revenue": amount,
        "currency": "USD",
        "total_completed_orders": len(completed),
        "week_over_week_change": f"{change_pct:+.1f}%",
        "shop_lifetime_revenue": store.shop.get("total_revenue", 0),
        "shop_lifetime_sales": store.shop.get("total_sales", 0),
    }
    return json.dumps(summary, indent=2)


def _update_order_status(tool_input: dict, store: DataStore) -> str:
    order_id = tool_input["order_id"]
    new_status = tool_input["new_status"]
    tracking = tool_input.get("tracking_number")

    order = store.find_order(order_id)
    if not order:
        return json.dumps({"error": f"Order {order_id} not found"})

    old_status = order["status"]
    order["status"] = new_status
    if tracking and new_status == "shipped":
        order["tracking"] = tracking

    store.save()
    result = {
        "success": True,
        "order_id": order_id,
        "previous_status": old_status,
        "new_status": new_status,
        "updated_at": str(date.today()),
    }
    if tracking:
        result["tracking_number"] = tracking
    return json.dumps(result, indent=2)


def _get_shipping_queue(store: DataStore) -> str:
    queue = [o for o in store.orders if o["status"] == "payment_complete"]
    queue.sort(key=lambda o: o.get("ship_by", "9999-99-99"))
    today = str(date.today())
    for order in queue:
        ship_by = order.get("ship_by", "")
        order["urgency"] = "OVERDUE" if ship_by < today else ("DUE_TODAY" if ship_by == today else "UPCOMING")
    return json.dumps({"shipping_queue": queue, "total_pending": len(queue)}, indent=2)


def _forecast_revenue(store: DataStore) -> str:
    revenue_data = store.analytics.get("revenue", {})
    this_week = revenue_data.get("this_week", 0)
    # Daily run-rate based on current week (assume 7-day week)
    daily_rate = this_week / 7.0 if this_week else 0

    targets = {
        "day7": {"target": 50, "label": "Day 7"},
        "day14": {"target": 150, "label": "Day 14"},
        "day30": {"target": 800, "label": "Day 30 (monthly run-rate)"},
    }

    forecasts = {}
    for key, meta in targets.items():
        days = int(key.replace("day", ""))
        projected = round(daily_rate * days, 2)
        gap = round(meta["target"] - projected, 2)
        forecasts[key] = {
            "label": meta["label"],
            "projected_revenue": projected,
            "target": meta["target"],
            "on_track": projected >= meta["target"],
            "gap_to_target": max(gap, 0),
        }

    return json.dumps({
        "daily_run_rate": round(daily_rate, 2),
        "this_week_revenue": this_week,
        "forecasts": forecasts,
        "summary": "On track" if all(f["on_track"] for f in forecasts.values()) else "Behind target — escalate to CEO",
    }, indent=2)


def _analyze_sales_trends(store: DataStore) -> str:
    revenue_data = store.analytics.get("revenue", {})
    this_week = revenue_data.get("this_week", 0)
    last_week = revenue_data.get("last_week", 0)

    if last_week and this_week > last_week * 1.05:
        trend = "growing"
    elif last_week and this_week < last_week * 0.95:
        trend = "declining"
    else:
        trend = "flat"

    # Tally categories from completed orders
    category_revenue: dict[str, float] = {}
    day_revenue: dict[str, float] = {}
    for order in store.orders:
        if order.get("status") in ("complete", "shipped", "payment_complete"):
            # Derive category from items if available, else fall back to listing lookup
            for item in order.get("items", []):
                listing_id = item.get("listing_id", "")
                listing = store.find_listing(listing_id)
                category = listing.get("category", "unknown") if listing else "unknown"
                amount = item.get("price", 0) * item.get("quantity", 1)
                category_revenue[category] = category_revenue.get(category, 0) + amount

            # Day-of-week breakdown
            order_date = order.get("created_at", "") or order.get("date", "")
            if order_date:
                try:
                    day_name = date.fromisoformat(order_date[:10]).strftime("%A")
                    amount = order.get("total", 0)
                    day_revenue[day_name] = day_revenue.get(day_name, 0) + amount
                except ValueError:
                    pass

    top_categories = sorted(category_revenue.items(), key=lambda x: x[1], reverse=True)
    best_day = max(day_revenue, key=day_revenue.get) if day_revenue else "insufficient data"

    return json.dumps({
        "revenue_trend": trend,
        "week_over_week": {
            "this_week": this_week,
            "last_week": last_week,
            "change_pct": round(((this_week - last_week) / last_week * 100) if last_week else 0, 1),
        },
        "top_categories": [{"category": c, "revenue": round(r, 2)} for c, r in top_categories[:5]],
        "best_day_of_week": best_day,
        "day_revenue_breakdown": {k: round(v, 2) for k, v in sorted(day_revenue.items(), key=lambda x: x[1], reverse=True)},
    }, indent=2)


def _get_sales_velocity(store: DataStore) -> str:
    results = []
    for listing in store.listings:
        sales = listing.get("sales", 0)
        days_listed = listing.get("days_listed", 30)
        if not days_listed or days_listed <= 0:
            days_listed = 30
        velocity_per_day = sales / days_listed
        velocity_per_month = velocity_per_day * 30

        if velocity_per_month > 5:
            status = "hot"
        elif velocity_per_month >= 1:
            status = "steady"
        else:
            status = "stale"

        results.append({
            "listing_id": listing.get("id"),
            "title": listing.get("title", ""),
            "price": listing.get("price", 0),
            "sales": sales,
            "days_listed": days_listed,
            "velocity_per_day": round(velocity_per_day, 4),
            "velocity_per_month": round(velocity_per_month, 2),
            "status": status,
        })

    results.sort(key=lambda x: x["velocity_per_day"], reverse=True)
    return json.dumps({
        "listings_by_velocity": results,
        "hot_count": sum(1 for r in results if r["status"] == "hot"),
        "steady_count": sum(1 for r in results if r["status"] == "steady"),
        "stale_count": sum(1 for r in results if r["status"] == "stale"),
    }, indent=2)


def _log_sale(amount: float, listing_id: str | None, store: DataStore) -> str:
    # Increment total_sales
    shop = store.shop
    shop["total_sales"] = shop.get("total_sales", 0) + 1
    shop["total_revenue"] = round(shop.get("total_revenue", 0) + amount, 2)

    # Update analytics revenue
    revenue = store.analytics.setdefault("revenue", {})
    revenue["today"] = round(revenue.get("today", 0) + amount, 2)
    revenue["this_week"] = round(revenue.get("this_week", 0) + amount, 2)
    revenue["this_month"] = round(revenue.get("this_month", 0) + amount, 2)

    store.save()
    result = {
        "success": True,
        "sale_logged": {
            "amount": amount,
            "listing_id": listing_id,
            "logged_at": str(date.today()),
        },
        "updated_totals": {
            "total_sales": shop["total_sales"],
            "total_revenue": shop["total_revenue"],
            "revenue_today": revenue["today"],
            "revenue_this_week": revenue["this_week"],
        },
    }
    return json.dumps(result, indent=2)


def _flag_overdue_orders(store: DataStore) -> str:
    today = date.today()
    today_str = str(today)
    flagged = []

    for order in store.orders:
        if order.get("status") != "payment_complete":
            continue
        ship_by = order.get("ship_by", "")
        if not ship_by or ship_by > today_str:
            continue

        try:
            ship_by_date = date.fromisoformat(ship_by)
        except ValueError:
            continue

        days_overdue = (today - ship_by_date).days

        if days_overdue > 3:
            severity = "CRITICAL"
            action = "Escalate to CEO immediately and contact buyer with update + discount offer"
        elif days_overdue >= 1:
            severity = "WARNING"
            action = "Ship today or message buyer with revised timeline"
        else:
            severity = "DUE_TODAY"
            action = "Ship by end of day"

        flagged.append({
            "order_id": order.get("id"),
            "buyer": order.get("buyer_name", ""),
            "ship_by": ship_by,
            "days_overdue": days_overdue,
            "severity": severity,
            "recommended_action": action,
            "order_total": order.get("total", 0),
        })

    flagged.sort(key=lambda x: x["days_overdue"], reverse=True)
    return json.dumps({
        "overdue_orders": flagged,
        "total_overdue": len(flagged),
        "critical_count": sum(1 for o in flagged if o["severity"] == "CRITICAL"),
        "warning_count": sum(1 for o in flagged if o["severity"] == "WARNING"),
        "due_today_count": sum(1 for o in flagged if o["severity"] == "DUE_TODAY"),
    }, indent=2)


def _get_price_optimization(store: DataStore) -> str:
    recommendations = []

    for listing in store.listings:
        views = listing.get("views", 0)
        sales = listing.get("sales", 0)
        price = listing.get("price", 0)
        title = listing.get("title", "")
        listing_id = listing.get("id")

        conversion_rate = (sales / views) if views > 0 else 0

        # High views, low sales, low-ish price → possibly underpriced (people browse but impulse to buy isn't triggered)
        # OR high views + very low conversion = other issue (photos, description)
        if views >= 50 and conversion_rate < 0.02 and price < 30:
            action = "increase_price"
            reasoning = f"High traffic ({views} views) but low conversion ({conversion_rate:.1%}); low price may signal low quality — test 15-20% price increase"
        elif views < 10 and price > 50 and sales == 0:
            action = "decrease_price"
            reasoning = f"Very low visibility ({views} views) and no sales at ${price}; reduce price to improve search ranking and competitiveness"
        elif views >= 20 and conversion_rate >= 0.05:
            action = "increase_price"
            reasoning = f"Strong conversion rate ({conversion_rate:.1%}) with {views} views — demand supports a price increase of 10-15%"
        else:
            action = "keep"
            reasoning = f"Price appears reasonable given {views} views and {sales} sales"

        recommendations.append({
            "listing_id": listing_id,
            "title": title,
            "current_price": price,
            "views": views,
            "sales": sales,
            "conversion_rate": round(conversion_rate, 4),
            "suggested_action": action,
            "reasoning": reasoning,
        })

    recommendations.sort(key=lambda x: (x["suggested_action"] != "increase_price", -x["views"]))
    return json.dumps({
        "pricing_recommendations": recommendations,
        "increase_count": sum(1 for r in recommendations if r["suggested_action"] == "increase_price"),
        "decrease_count": sum(1 for r in recommendations if r["suggested_action"] == "decrease_price"),
        "keep_count": sum(1 for r in recommendations if r["suggested_action"] == "keep"),
    }, indent=2)
