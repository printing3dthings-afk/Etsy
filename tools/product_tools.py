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
    low = [l for l in store.listings if l["quantity"] <= threshold]
    low.sort(key=lambda l: l["quantity"])
    result = [
        {"id": l["id"], "title": l["title"], "quantity": l["quantity"], "status": l["status"], "price": l["price"]}
        for l in low
    ]
    return json.dumps({"low_stock_items": result, "count": len(result), "threshold": threshold}, indent=2)


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
