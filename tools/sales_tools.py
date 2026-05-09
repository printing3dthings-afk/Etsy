"""Tool definitions and implementations for the Sales Agent."""

import json
from datetime import date
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
