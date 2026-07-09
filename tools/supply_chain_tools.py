"""
Supply Chain Tools — manages materials inventory, supplier contacts, and reorder alerts.

Tracks filament, paint, packaging, and all consumables used in production.
Separate from print_production_tools: that module tracks jobs; this one tracks stock and suppliers.
"""
from __future__ import annotations

import json
from datetime import date
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_materials_inventory",
        "description": "Get full inventory of all materials: filament, paint, packaging, tools.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["all", "filament", "paint", "packaging", "tools", "other"],
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "add_material",
        "description": "Add a new material or update an existing one in inventory.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "e.g. 'Matte Black PLA 1kg', 'Acrylic Paint White'"},
                "category": {
                    "type": "string",
                    "enum": ["filament", "paint", "packaging", "tools", "other"],
                },
                "quantity": {"type": "number", "description": "Amount in stock (grams for filament, units for others)"},
                "unit": {"type": "string", "description": "Unit of measure: 'grams', 'ml', 'units', 'rolls'"},
                "reorder_threshold": {"type": "number", "description": "Alert when stock falls below this level"},
                "reorder_quantity": {"type": "number", "description": "How much to order when restocking"},
                "cost_per_unit": {"type": "number", "description": "Cost per unit/gram in USD"},
                "supplier_id": {"type": "string", "description": "Supplier ID from the supplier list"},
                "notes": {"type": "string"},
            },
            "required": ["name", "category", "quantity", "unit"],
        },
    },
    {
        "name": "update_stock",
        "description": "Update quantity for a material (add new stock or record usage).",
        "input_schema": {
            "type": "object",
            "properties": {
                "material_name": {"type": "string"},
                "quantity_change": {"type": "number", "description": "Positive = restocking, negative = used/consumed"},
                "reason": {
                    "type": "string",
                    "enum": ["purchase", "production_use", "waste", "adjustment", "gift"],
                    "default": "production_use",
                },
                "cost": {"type": "number", "description": "Cost paid if this is a purchase"},
            },
            "required": ["material_name", "quantity_change", "reason"],
        },
    },
    {
        "name": "get_reorder_alerts",
        "description": "Get all materials that are at or below their reorder threshold.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_supplier",
        "description": "Add or update a supplier/vendor contact.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Supplier business name, e.g. 'Hatchbox', 'Amazon', 'USPS'"},
                "category": {"type": "string", "description": "What they supply, e.g. 'filament', 'packaging'"},
                "website": {"type": "string"},
                "contact_email": {"type": "string"},
                "notes": {"type": "string", "description": "Lead time, payment terms, discount codes, etc."},
                "rating": {"type": "integer", "description": "1-5 rating of reliability", "minimum": 1, "maximum": 5},
            },
            "required": ["name", "category"],
        },
    },
    {
        "name": "get_suppliers",
        "description": "List all supplier contacts by category.",
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {"type": "string", "description": "Filter by category (optional)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_materials_cost_report",
        "description": "Monthly materials spend report: what was purchased, from whom, at what cost.",
        "input_schema": {
            "type": "object",
            "properties": {
                "month": {"type": "string", "description": "YYYY-MM, defaults to current month"},
            },
            "required": [],
        },
    },
    {
        "name": "create_purchase_order",
        "description": "Create a purchase order for materials that need restocking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "material_name": {"type": "string"},
                            "quantity": {"type": "number"},
                            "estimated_cost": {"type": "number"},
                            "supplier": {"type": "string"},
                        },
                        "required": ["material_name", "quantity"],
                    },
                },
                "notes": {"type": "string"},
            },
            "required": ["items"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_materials_inventory":
        return _get_materials_inventory(tool_input.get("category", "all"), store)
    if tool_name == "add_material":
        return _add_material(tool_input, store)
    if tool_name == "update_stock":
        return _update_stock(tool_input, store)
    if tool_name == "get_reorder_alerts":
        return _get_reorder_alerts(store)
    if tool_name == "add_supplier":
        return _add_supplier(tool_input, store)
    if tool_name == "get_suppliers":
        return _get_suppliers(tool_input.get("category"), store)
    if tool_name == "get_materials_cost_report":
        return _get_materials_cost_report(tool_input.get("month"), store)
    if tool_name == "create_purchase_order":
        return _create_purchase_order(tool_input, store)
    return f"Unknown supply chain tool: {tool_name}"


def _get_materials_inventory(category: str, store: DataStore) -> str:
    materials = store.get("materials_inventory", default=[])
    if category != "all":
        materials = [m for m in materials if m.get("category") == category]

    low_stock = [m for m in materials if m.get("quantity", 0) <= m.get("reorder_threshold", 0)]
    total_value = sum(
        m.get("quantity", 0) * m.get("cost_per_unit", 0) for m in materials
    )
    return json.dumps({
        "materials": materials,
        "count": len(materials),
        "low_stock_count": len(low_stock),
        "estimated_total_value_usd": round(total_value, 2),
        "low_stock_items": [m["name"] for m in low_stock],
    }, indent=2)


def _add_material(data: dict, store: DataStore) -> str:
    materials = store.get("materials_inventory", default=[])
    existing = next((m for m in materials if m["name"].lower() == data["name"].lower()), None)
    if existing:
        existing.update({k: v for k, v in data.items() if k != "name"})
        existing["updated_at"] = str(date.today())
        store.set(materials, "materials_inventory")
        store.save()
        return json.dumps({"success": True, "action": "updated", "material": existing}, indent=2)

    material = {
        "name": data["name"],
        "category": data["category"],
        "quantity": data["quantity"],
        "unit": data["unit"],
        "reorder_threshold": data.get("reorder_threshold", 0),
        "reorder_quantity": data.get("reorder_quantity", 0),
        "cost_per_unit": data.get("cost_per_unit", 0),
        "supplier_id": data.get("supplier_id", ""),
        "notes": data.get("notes", ""),
        "added_at": str(date.today()),
        "updated_at": str(date.today()),
        "purchase_history": [],
    }
    materials.append(material)
    store.set(materials, "materials_inventory")
    store.save()
    return json.dumps({"success": True, "action": "added", "material": material}, indent=2)


def _update_stock(data: dict, store: DataStore) -> str:
    materials = store.get("materials_inventory", default=[])
    material = next((m for m in materials if m["name"].lower() == data["material_name"].lower()), None)
    if not material:
        return json.dumps({"error": f"Material '{data['material_name']}' not found. Use add_material first."})

    prev_qty = material["quantity"]
    material["quantity"] = max(0, prev_qty + data["quantity_change"])
    material["updated_at"] = str(date.today())

    if data["reason"] == "purchase" and data.get("cost"):
        history = material.get("purchase_history", [])
        history.append({
            "date": str(date.today()),
            "quantity": data["quantity_change"],
            "cost": data["cost"],
        })
        material["purchase_history"] = history

    store.set(materials, "materials_inventory")
    store.save()

    low = material["quantity"] <= material.get("reorder_threshold", 0)
    return json.dumps({
        "success": True,
        "material": material["name"],
        "previous_quantity": prev_qty,
        "quantity_change": data["quantity_change"],
        "new_quantity": material["quantity"],
        "unit": material["unit"],
        "low_stock_alert": low,
        "reorder_threshold": material.get("reorder_threshold", 0),
    }, indent=2)


def _get_reorder_alerts(store: DataStore) -> str:
    materials = store.get("materials_inventory", default=[])
    alerts = []
    for m in materials:
        qty = m.get("quantity", 0)
        threshold = m.get("reorder_threshold", 0)
        if qty <= threshold:
            alerts.append({
                "name": m["name"],
                "category": m["category"],
                "quantity_remaining": qty,
                "unit": m.get("unit", ""),
                "reorder_threshold": threshold,
                "reorder_quantity": m.get("reorder_quantity", "not set"),
                "supplier": m.get("supplier_id", "not set"),
                "urgency": "OUT OF STOCK" if qty == 0 else "LOW",
            })

    alerts.sort(key=lambda a: a["quantity_remaining"])
    return json.dumps({
        "reorder_alerts": alerts,
        "out_of_stock": sum(1 for a in alerts if a["urgency"] == "OUT OF STOCK"),
        "low_stock": sum(1 for a in alerts if a["urgency"] == "LOW"),
        "action": "Use create_purchase_order to generate a restocking order.",
    }, indent=2)


def _add_supplier(data: dict, store: DataStore) -> str:
    suppliers = store.get("supplier_contacts", default=[])
    supplier_id = f"SUP{len(suppliers) + 1:03d}"
    existing = next((s for s in suppliers if s["name"].lower() == data["name"].lower()), None)
    if existing:
        existing.update({k: v for k, v in data.items()})
        existing["updated_at"] = str(date.today())
        store.set(suppliers, "supplier_contacts")
        store.save()
        return json.dumps({"success": True, "action": "updated", "supplier": existing}, indent=2)

    supplier = {
        "id": supplier_id,
        "name": data["name"],
        "category": data["category"],
        "website": data.get("website", ""),
        "contact_email": data.get("contact_email", ""),
        "notes": data.get("notes", ""),
        "rating": data.get("rating", 0),
        "added_at": str(date.today()),
        "updated_at": str(date.today()),
    }
    suppliers.append(supplier)
    store.set(suppliers, "supplier_contacts")
    store.save()
    return json.dumps({"success": True, "action": "added", "supplier": supplier}, indent=2)


def _get_suppliers(category: str | None, store: DataStore) -> str:
    suppliers = store.get("supplier_contacts", default=[])
    if category:
        suppliers = [s for s in suppliers if category.lower() in s.get("category", "").lower()]
    return json.dumps({"suppliers": suppliers, "count": len(suppliers)}, indent=2)


def _get_materials_cost_report(month: str | None, store: DataStore) -> str:
    month = month or date.today().strftime("%Y-%m")
    materials = store.get("materials_inventory", default=[])
    report = []
    total_spend = 0.0
    for m in materials:
        purchases = [p for p in m.get("purchase_history", []) if p.get("date", "").startswith(month)]
        if purchases:
            spend = sum(p.get("cost", 0) for p in purchases)
            total_spend += spend
            report.append({
                "material": m["name"],
                "category": m["category"],
                "purchases": purchases,
                "month_spend": round(spend, 2),
            })

    return json.dumps({
        "month": month,
        "total_materials_spend": round(total_spend, 2),
        "items_purchased": report,
        "tip": "Log all purchases with update_stock reason='purchase' to populate this report.",
    }, indent=2)


def _create_purchase_order(data: dict, store: DataStore) -> str:
    purchase_orders = store.get("purchase_orders", default=[])
    po_id = f"PO{len(purchase_orders) + 1:04d}"
    total_cost = sum(item.get("estimated_cost", 0) for item in data["items"])
    po = {
        "id": po_id,
        "items": data["items"],
        "notes": data.get("notes", ""),
        "estimated_total": round(total_cost, 2),
        "status": "pending",
        "created_at": str(date.today()),
    }
    purchase_orders.append(po)
    store.set(purchase_orders, "purchase_orders")
    store.save()
    return json.dumps({
        "success": True,
        "purchase_order_id": po_id,
        "items": data["items"],
        "estimated_total_usd": round(total_cost, 2),
        "next_step": f"Place order with your suppliers. Mark received with update_stock reason='purchase'.",
    }, indent=2)
