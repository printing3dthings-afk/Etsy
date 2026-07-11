"""
3D Print Production Tools — manages the physical production workflow.

Tracks: print queue, filament inventory, print success/failure rates,
machine status, and per-order production cost.
"""

import json
from datetime import date, datetime
from typing import Any

from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_print_queue",
        "description": "Get all jobs currently in the production queue, sorted by priority.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "queued", "printing", "post_processing", "complete", "failed"],
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "add_to_print_queue",
        "description": "Add an order to the 3D print production queue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "listing_id": {"type": "string"},
                "product_name": {"type": "string"},
                "filament_color": {"type": "string", "description": "e.g. 'Matte Black PLA'"},
                "estimated_grams": {"type": "number", "description": "Estimated filament usage in grams"},
                "estimated_hours": {"type": "number", "description": "Estimated print time in hours"},
                "priority": {
                    "type": "string",
                    "enum": ["normal", "rush", "overdue"],
                    "default": "normal",
                },
                "notes": {"type": "string", "description": "Customer customisation notes or special instructions"},
            },
            "required": ["order_id", "product_name", "filament_color", "estimated_grams", "estimated_hours"],
        },
    },
    {
        "name": "update_print_status",
        "description": "Update the status of a print job (e.g., mark as printing, complete, or failed).",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["queued", "printing", "post_processing", "complete", "failed"],
                },
                "actual_grams_used": {"type": "number", "description": "Actual filament used (for complete jobs)"},
                "failure_reason": {"type": "string", "description": "Required when status=failed"},
            },
            "required": ["job_id", "status"],
        },
    },
    {
        "name": "get_filament_inventory",
        "description": "Get current filament stock levels by color and material.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "update_filament_stock",
        "description": "Update filament inventory (add new spool or record usage).",
        "input_schema": {
            "type": "object",
            "properties": {
                "material": {"type": "string", "description": "e.g. 'PLA', 'PETG', 'TPU'"},
                "color": {"type": "string", "description": "e.g. 'Matte Black', 'Galaxy Silver'"},
                "brand": {"type": "string", "description": "e.g. 'Hatchbox', 'eSUN', 'Polymaker'"},
                "grams_change": {"type": "number", "description": "Positive = adding stock, negative = using/waste"},
                "cost_per_kg": {"type": "number", "description": "Price paid per kg (for new spools)"},
                "reason": {
                    "type": "string",
                    "enum": ["new_spool", "print_usage", "waste", "adjustment"],
                    "default": "print_usage",
                },
            },
            "required": ["material", "color", "grams_change", "reason"],
        },
    },
    {
        "name": "get_reorder_alerts",
        "description": "Get filament colors/materials that are running low and need reordering.",
        "input_schema": {
            "type": "object",
            "properties": {
                "threshold_grams": {
                    "type": "number",
                    "description": "Alert when below this many grams (default: 200g)",
                    "default": 200,
                }
            },
            "required": [],
        },
    },
    {
        "name": "log_print_failure",
        "description": "Record a failed print with reason and wasted filament for cost tracking.",
        "input_schema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Print queue job ID (optional)"},
                "product_name": {"type": "string"},
                "filament_wasted_grams": {"type": "number"},
                "failure_reason": {
                    "type": "string",
                    "enum": ["layer_adhesion", "warping", "stringing", "power_failure",
                             "filament_jam", "spaghetti", "supports_failed", "other"],
                },
                "notes": {"type": "string"},
            },
            "required": ["product_name", "filament_wasted_grams", "failure_reason"],
        },
    },
    {
        "name": "get_production_stats",
        "description": "Get production statistics: success rate, average print time, waste rate, throughput.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_machine_status",
        "description": "Get or update the status of the 3D printer(s).",
        "input_schema": {
            "type": "object",
            "properties": {
                "machine_name": {"type": "string", "description": "Name/model of the printer, e.g. 'Bambu Lab A1'"},
                "status": {
                    "type": "string",
                    "enum": ["idle", "printing", "maintenance", "offline"],
                },
                "notes": {"type": "string"},
            },
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_print_queue":
        return _get_print_queue(tool_input.get("status_filter", "all"), store)
    if tool_name == "add_to_print_queue":
        return _add_to_print_queue(tool_input, store)
    if tool_name == "update_print_status":
        return _update_print_status(tool_input, store)
    if tool_name == "get_filament_inventory":
        return _get_filament_inventory(store)
    if tool_name == "update_filament_stock":
        return _update_filament_stock(tool_input, store)
    if tool_name == "get_reorder_alerts":
        return _get_reorder_alerts(tool_input.get("threshold_grams", 200), store)
    if tool_name == "log_print_failure":
        return _log_print_failure(tool_input, store)
    if tool_name == "get_production_stats":
        return _get_production_stats(store)
    if tool_name == "get_machine_status":
        return _get_machine_status(tool_input, store)
    return f"Unknown print production tool: {tool_name}"


def _get_print_queue(status_filter: str, store: DataStore) -> str:
    queue = store.get("print_queue", default=[])
    if status_filter != "all":
        queue = [j for j in queue if j.get("status") == status_filter]

    today = str(date.today())
    for job in queue:
        ship_by = store.find_order(job.get("order_id", ""))
        if ship_by:
            sb = ship_by.get("ship_by", "9999-99-99")
            job["urgency"] = "OVERDUE" if sb < today else ("DUE_TODAY" if sb == today else "upcoming")

    return json.dumps({
        "print_queue": queue,
        "total_jobs": len(queue),
        "by_status": {s: sum(1 for j in queue if j.get("status") == s)
                      for s in ("queued", "printing", "post_processing", "complete", "failed")},
    }, indent=2)


def _add_to_print_queue(data: dict, store: DataStore) -> str:
    queue = store.get("print_queue", default=[])
    job_id = f"PJ{len(queue) + 1:04d}"
    job: dict[str, Any] = {
        "id": job_id,
        "order_id": data.get("order_id", ""),
        "listing_id": data.get("listing_id", ""),
        "product_name": data["product_name"],
        "filament_color": data["filament_color"],
        "estimated_grams": data["estimated_grams"],
        "estimated_hours": data["estimated_hours"],
        "priority": data.get("priority", "normal"),
        "notes": data.get("notes", ""),
        "status": "queued",
        "added_at": str(date.today()),
        "actual_grams_used": None,
    }
    queue.append(job)
    store.set(queue, "print_queue")
    store.save()
    return json.dumps({"success": True, "job_id": job_id, "product": job["product_name"],
                       "estimated_hours": job["estimated_hours"]}, indent=2)


def _update_print_status(data: dict, store: DataStore) -> str:
    queue = store.get("print_queue", default=[])
    job = next((j for j in queue if j["id"] == data["job_id"]), None)
    if not job:
        return json.dumps({"error": f"Job {data['job_id']} not found"})

    old_status = job["status"]
    job["status"] = data["status"]
    if data.get("actual_grams_used") is not None:
        job["actual_grams_used"] = data["actual_grams_used"]
    if data.get("failure_reason"):
        job["failure_reason"] = data["failure_reason"]
    if data["status"] == "complete":
        job["completed_at"] = str(date.today())

    store.set(queue, "print_queue")
    store.save()
    return json.dumps({"success": True, "job_id": data["job_id"],
                       "previous_status": old_status, "new_status": data["status"]}, indent=2)


def _get_filament_inventory(store: DataStore) -> str:
    inventory = store.get("filament_inventory", default=[])
    if not inventory:
        return json.dumps({
            "filament_inventory": [],
            "message": "No filament inventory tracked yet. Use update_filament_stock to add spools.",
        }, indent=2)
    total_value = sum(
        (i.get("grams_remaining", 0) / 1000) * i.get("cost_per_kg", 22)
        for i in inventory
    )
    return json.dumps({
        "filament_inventory": inventory,
        "total_spools": len(inventory),
        "estimated_total_value": round(total_value, 2),
    }, indent=2)


def _update_filament_stock(data: dict, store: DataStore) -> str:
    inventory = store.get("filament_inventory", default=[])
    key = f"{data['material']}_{data['color']}".lower().replace(" ", "_")

    spool = next((i for i in inventory if i.get("key") == key), None)
    if not spool:
        spool = {
            "key": key,
            "material": data["material"],
            "color": data["color"],
            "brand": data.get("brand", "Unknown"),
            "grams_remaining": 0,
            "cost_per_kg": data.get("cost_per_kg", 22.00),
            "total_used_grams": 0,
        }
        inventory.append(spool)

    prev = spool["grams_remaining"]
    spool["grams_remaining"] = max(0, prev + data["grams_change"])
    if data["grams_change"] < 0:
        spool["total_used_grams"] = spool.get("total_used_grams", 0) + abs(data["grams_change"])
    if data.get("cost_per_kg"):
        spool["cost_per_kg"] = data["cost_per_kg"]

    store.set(inventory, "filament_inventory")
    store.save()

    return json.dumps({
        "success": True,
        "filament": f"{spool['color']} {spool['material']}",
        "previous_grams": prev,
        "grams_change": data["grams_change"],
        "grams_remaining": spool["grams_remaining"],
        "low_stock_warning": spool["grams_remaining"] < 200,
    }, indent=2)


def _get_reorder_alerts(threshold: float, store: DataStore) -> str:
    inventory = store.get("filament_inventory", default=[])
    low = [i for i in inventory if i.get("grams_remaining", 0) < threshold]
    out = [i for i in inventory if i.get("grams_remaining", 0) == 0]

    alerts = [{
        "filament": f"{i['color']} {i['material']}",
        "brand": i.get("brand", ""),
        "grams_remaining": i.get("grams_remaining", 0),
        "urgency": "OUT OF STOCK" if i["grams_remaining"] == 0 else "LOW",
    } for i in low]

    return json.dumps({
        "reorder_alerts": alerts,
        "out_of_stock": len(out),
        "low_stock": len(low) - len(out),
        "threshold_grams": threshold,
        "action": "Order more filament before these colors run out and delay orders.",
    }, indent=2)


def _log_print_failure(data: dict, store: DataStore) -> str:
    failures = store.get("print_failures", default=[])
    failure_id = f"FAIL{len(failures) + 1:04d}"
    record = {
        "id": failure_id,
        "job_id": data.get("job_id", ""),
        "product_name": data["product_name"],
        "filament_wasted_grams": data["filament_wasted_grams"],
        "failure_reason": data["failure_reason"],
        "notes": data.get("notes", ""),
        "date": str(date.today()),
        "cost_of_waste": round(data["filament_wasted_grams"] * 0.02, 2),
    }
    failures.append(record)
    store.set(failures, "print_failures")
    store.save()
    return json.dumps({"success": True, "failure_id": failure_id,
                       "wasted_grams": data["filament_wasted_grams"],
                       "estimated_waste_cost": record["cost_of_waste"]}, indent=2)


def _get_production_stats(store: DataStore) -> str:
    queue = store.get("print_queue", default=[])
    failures = store.get("print_failures", default=[])
    complete = [j for j in queue if j.get("status") == "complete"]
    failed = [j for j in queue if j.get("status") == "failed"]
    total = len(complete) + len(failed)
    success_rate = round(len(complete) / total * 100, 1) if total else 0

    avg_hours = (sum(j.get("estimated_hours", 0) for j in complete) / len(complete)) if complete else 0
    total_grams = sum(j.get("actual_grams_used") or j.get("estimated_grams", 0) for j in complete)
    waste_grams = sum(f.get("filament_wasted_grams", 0) for f in failures)

    return json.dumps({
        "total_jobs": total,
        "completed": len(complete),
        "failed": len(failed),
        "success_rate_pct": success_rate,
        "currently_printing": sum(1 for j in queue if j.get("status") == "printing"),
        "queued_pending": sum(1 for j in queue if j.get("status") == "queued"),
        "avg_print_hours": round(avg_hours, 1),
        "total_filament_used_grams": round(total_grams, 1),
        "total_waste_grams": round(waste_grams, 1),
        "waste_cost_estimate": round(waste_grams * 0.02, 2),
        "top_failure_reasons": _count_failures(failures),
    }, indent=2)


def _get_machine_status(data: dict, store: DataStore) -> str:
    machines = store.get("machines", default=[])
    if data.get("status"):
        name = data.get("machine_name", "Printer 1")
        machine = next((m for m in machines if m["name"] == name), None)
        if not machine:
            machine = {"name": name, "status": data["status"], "notes": data.get("notes", "")}
            machines.append(machine)
        else:
            machine["status"] = data["status"]
            machine["notes"] = data.get("notes", machine.get("notes", ""))
        machine["updated_at"] = str(date.today())
        store.set(machines, "machines")
        store.save()
        return json.dumps({"success": True, "machine": machine}, indent=2)

    if not machines:
        return json.dumps({"machines": [], "message": "No machines tracked. Use this tool with a status to add your printer."})
    return json.dumps({"machines": machines}, indent=2)


def _count_failures(failures: list) -> dict:
    counts: dict[str, int] = {}
    for f in failures:
        r = f.get("failure_reason", "other")
        counts[r] = counts.get(r, 0) + 1
    return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
