"""Tool definitions and implementations for the Workflow Coordinator Agent."""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from tools.data_store import DataStore

_IDEAS_FILE = Path(__file__).parent.parent / "data" / "ideas.json"

def _read_ideas() -> list:
    try:
        if _IDEAS_FILE.exists():
            return json.loads(_IDEAS_FILE.read_text())
    except Exception:
        pass
    return []

def _write_ideas(ideas: list):
    _IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _IDEAS_FILE.write_text(json.dumps(ideas, indent=2))

# ── Helpers ────────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _minutes_since(ts_str: str) -> float:
    """Return elapsed minutes between ts_str (ISO) and now. Returns 0 on parse error."""
    try:
        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        return delta.total_seconds() / 60.0
    except Exception:
        return 0.0


def _hours_since(ts_str: str) -> float:
    return _minutes_since(ts_str) / 60.0


# ── Tool definitions ───────────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "get_pipeline_health",
        "description": (
            "Returns current pipeline status: which agents are active, which tasks are stuck "
            "(running > 5 min), and which pipeline stages are completed vs. pending. "
            "Reads from the audit_log and digital_products data."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_agent_workload",
        "description": (
            "Returns a workload summary for each agent: how many tasks completed today "
            "(from audit_log), average task duration, last active time. "
            "Shows which agents are overloaded vs. idle."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "flag_bottleneck",
        "description": (
            "Flags a specific agent or pipeline stage as a bottleneck. "
            "Saves to the bottlenecks list in the data store with a timestamp."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent or pipeline stage that is bottlenecked.",
                },
                "reason": {
                    "type": "string",
                    "description": "Why this is a bottleneck (e.g. 'QC queue has 10 items, zero throughput today').",
                },
                "suggested_action": {
                    "type": "string",
                    "description": "What should be done to resolve the bottleneck.",
                },
            },
            "required": ["agent_name", "reason", "suggested_action"],
        },
    },
    {
        "name": "get_bottlenecks",
        "description": "Returns all active (unresolved) bottlenecks, newest first.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "resolve_bottleneck",
        "description": "Marks a bottleneck as resolved by its ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "bottleneck_id": {
                    "type": "string",
                    "description": "The ID of the bottleneck to resolve.",
                },
            },
            "required": ["bottleneck_id"],
        },
    },
    {
        "name": "get_digital_pipeline_status",
        "description": (
            "Returns the full digital product pipeline status: how many products at each stage "
            "(concept → qc_pending → approved → listed → delivered). "
            "Shows products stuck at each stage and how long they've been there."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_daily_ops_summary",
        "description": (
            "Returns a daily operations summary: products created today, QC pass/fail ratio, "
            "orders delivered, any errors in the audit log, bottlenecks active. "
            "The 'morning standup report' in a single call."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "prioritize_task_queue",
        "description": (
            "Takes a list of pending tasks and returns them sorted by priority (urgent first). "
            "Business logic: overdue orders > new orders > listings > analytics > other."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "tasks": {
                    "type": "array",
                    "description": "List of pending task objects to prioritize.",
                    "items": {
                        "type": "object",
                        "properties": {
                            "task": {"type": "string", "description": "Task description."},
                            "agent": {"type": "string", "description": "Agent responsible."},
                            "created_at": {"type": "string", "description": "ISO timestamp when task was created."},
                        },
                        "required": ["task", "agent", "created_at"],
                    },
                },
            },
            "required": ["tasks"],
        },
    },
    {
        "name": "submit_idea",
        "description": (
            "Submit an idea to the shared Ideas Board so it can be reviewed in the next brainstorm meeting. "
            "Use this whenever you spot an opportunity, improvement, or new product concept worth discussing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Short title for the idea (max 120 chars)",
                },
                "description": {
                    "type": "string",
                    "description": "Detailed explanation of the idea, why it matters, and rough next steps (max 800 chars)",
                },
                "category": {
                    "type": "string",
                    "enum": ["product", "marketing", "operations", "design", "pricing", "general"],
                    "description": "Category that best fits the idea",
                },
                "agent": {
                    "type": "string",
                    "description": "Your agent key (e.g. 'analytics', 'trend', 'art')",
                },
            },
            "required": ["title", "description", "agent"],
        },
    },
]

TOOL_NAMES = {t["name"] for t in TOOL_DEFINITIONS}

# ── Dispatch ───────────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_pipeline_health":
        return _get_pipeline_health(store)
    if tool_name == "get_agent_workload":
        return _get_agent_workload(store)
    if tool_name == "flag_bottleneck":
        return _flag_bottleneck(
            tool_input["agent_name"],
            tool_input["reason"],
            tool_input["suggested_action"],
            store,
        )
    if tool_name == "get_bottlenecks":
        return _get_bottlenecks(store)
    if tool_name == "resolve_bottleneck":
        return _resolve_bottleneck(tool_input["bottleneck_id"], store)
    if tool_name == "get_digital_pipeline_status":
        return _get_digital_pipeline_status(store)
    if tool_name == "get_daily_ops_summary":
        return _get_daily_ops_summary(store)
    if tool_name == "prioritize_task_queue":
        return _prioritize_task_queue(tool_input["tasks"])
    if tool_name == "submit_idea":
        return _submit_idea(
            agent=tool_input.get("agent", "unknown"),
            title=tool_input["title"],
            description=tool_input["description"],
            category=tool_input.get("category", "general"),
        )
    return f"Unknown workflow coordinator tool: {tool_name}"


# ── Implementations ────────────────────────────────────────────────────────────

def _get_pipeline_health(store: DataStore) -> str:
    audit_log = store.get_audit_log(limit=200)
    digital_products = store.get("digital_products", default=[])

    # Track last-seen activity per agent
    agent_last_seen: dict[str, str] = {}
    agent_task_counts: dict[str, int] = {}
    for entry in audit_log:
        agent = entry.get("agent", "unknown")
        ts = entry.get("ts", "")
        if agent not in agent_last_seen or ts > agent_last_seen[agent]:
            agent_last_seen[agent] = ts
        agent_task_counts[agent] = agent_task_counts.get(agent, 0) + 1

    # Identify stuck tasks: audit entries with action "started" but no matching "completed"
    in_progress: dict[str, dict] = {}
    for entry in reversed(audit_log):  # oldest first for matching
        action = entry.get("action", "")
        details = entry.get("details", {})
        task_id = details.get("task_id") or details.get("id")
        if task_id:
            if action in ("started", "begin", "processing"):
                in_progress[task_id] = entry
            elif action in ("completed", "done", "finished", "failed"):
                in_progress.pop(task_id, None)

    stuck_tasks = []
    for task_id, entry in in_progress.items():
        mins = _minutes_since(entry.get("ts", ""))
        if mins > 5:
            stuck_tasks.append({
                "task_id": task_id,
                "agent": entry.get("agent"),
                "action": entry.get("action"),
                "running_minutes": round(mins, 1),
                "started_at": entry.get("ts"),
            })

    # Pipeline stages from digital_products
    stage_counts: dict[str, int] = {}
    for product in digital_products:
        stage = product.get("stage", "unknown")
        stage_counts[stage] = stage_counts.get(stage, 0) + 1

    active_agents = [
        {"agent": a, "last_active": ts, "tasks_in_log": agent_task_counts[a]}
        for a, ts in sorted(agent_last_seen.items(), key=lambda x: x[1], reverse=True)
        if _minutes_since(ts) < 60
    ]

    result = {
        "snapshot_at": _now_iso(),
        "active_agents_last_60min": active_agents,
        "stuck_tasks_over_5min": stuck_tasks,
        "pipeline_stage_counts": stage_counts,
        "total_agents_seen_today": len(agent_last_seen),
    }
    return json.dumps(result, indent=2)


def _get_agent_workload(store: DataStore) -> str:
    audit_log = store.get_audit_log(limit=500)
    today = datetime.now(timezone.utc).date().isoformat()

    # Per-agent stats
    agent_data: dict[str, dict] = {}
    for entry in audit_log:
        agent = entry.get("agent", "unknown")
        ts = entry.get("ts", "")
        if agent not in agent_data:
            agent_data[agent] = {
                "tasks_total": 0,
                "tasks_today": 0,
                "last_active": ts,
                "durations_min": [],
            }
        ad = agent_data[agent]
        ad["tasks_total"] += 1
        if ts.startswith(today):
            ad["tasks_today"] += 1
        if ts > ad["last_active"]:
            ad["last_active"] = ts

    # Build summary
    summary = []
    for agent, ad in sorted(agent_data.items(), key=lambda x: x[1]["tasks_today"], reverse=True):
        mins_idle = _minutes_since(ad["last_active"])
        status = "active" if mins_idle < 10 else ("idle" if mins_idle < 120 else "inactive")
        summary.append({
            "agent": agent,
            "tasks_today": ad["tasks_today"],
            "tasks_total_in_log": ad["tasks_total"],
            "last_active": ad["last_active"],
            "idle_minutes": round(mins_idle, 1),
            "status": status,
        })

    result = {
        "snapshot_at": _now_iso(),
        "agent_workloads": summary,
        "overloaded_threshold": "10+ tasks today",
        "idle_threshold": "no activity in 120+ min",
    }
    return json.dumps(result, indent=2)


def _flag_bottleneck(agent_name: str, reason: str, suggested_action: str, store: DataStore) -> str:
    bottlenecks = store.get("bottlenecks", default=[])
    if not isinstance(bottlenecks, list):
        bottlenecks = []

    new_bottleneck = {
        "id": str(uuid.uuid4())[:8],
        "agent_name": agent_name,
        "reason": reason,
        "suggested_action": suggested_action,
        "status": "active",
        "flagged_at": _now_iso(),
        "resolved_at": None,
    }
    bottlenecks.append(new_bottleneck)
    store.set(bottlenecks, "bottlenecks")
    store.save()

    return json.dumps({
        "status": "flagged",
        "bottleneck_id": new_bottleneck["id"],
        "agent_name": agent_name,
        "flagged_at": new_bottleneck["flagged_at"],
    }, indent=2)


def _get_bottlenecks(store: DataStore) -> str:
    bottlenecks = store.get("bottlenecks", default=[])
    if not isinstance(bottlenecks, list):
        bottlenecks = []

    active = [b for b in bottlenecks if b.get("status") == "active"]
    # Newest first
    active_sorted = sorted(active, key=lambda b: b.get("flagged_at", ""), reverse=True)

    result = {
        "snapshot_at": _now_iso(),
        "active_bottleneck_count": len(active_sorted),
        "bottlenecks": active_sorted,
    }
    return json.dumps(result, indent=2)


def _resolve_bottleneck(bottleneck_id: str, store: DataStore) -> str:
    bottlenecks = store.get("bottlenecks", default=[])
    if not isinstance(bottlenecks, list):
        return json.dumps({"status": "error", "message": "No bottlenecks found in data store."})

    for b in bottlenecks:
        if b.get("id") == bottleneck_id:
            if b.get("status") == "resolved":
                return json.dumps({"status": "already_resolved", "bottleneck_id": bottleneck_id})
            b["status"] = "resolved"
            b["resolved_at"] = _now_iso()
            store.set(bottlenecks, "bottlenecks")
            store.save()
            return json.dumps({
                "status": "resolved",
                "bottleneck_id": bottleneck_id,
                "agent_name": b.get("agent_name"),
                "resolved_at": b["resolved_at"],
            }, indent=2)

    return json.dumps({"status": "not_found", "bottleneck_id": bottleneck_id})


def _get_digital_pipeline_status(store: DataStore) -> str:
    digital_products = store.get("digital_products", default=[])

    # Standard pipeline stages in order
    pipeline_stages = ["concept", "design_in_progress", "qc_pending", "approved", "listed", "delivered"]
    stage_data: dict[str, list] = {s: [] for s in pipeline_stages}
    other_stage_data: dict[str, list] = {}

    for product in digital_products:
        stage = product.get("stage", "unknown")
        entry = {
            "id": product.get("id"),
            "title": product.get("title", "Untitled"),
            "stage": stage,
            "updated_at": product.get("updated_at") or product.get("created_at", ""),
            "hours_at_stage": round(_hours_since(
                product.get("stage_entered_at") or product.get("updated_at") or product.get("created_at", _now_iso())
            ), 1),
        }
        if stage in stage_data:
            stage_data[stage].append(entry)
        else:
            other_stage_data.setdefault(stage, []).append(entry)

    # Build summary per stage
    stage_summary = []
    for stage in pipeline_stages:
        products_at_stage = stage_data[stage]
        stuck = [p for p in products_at_stage if p["hours_at_stage"] > 24]
        stage_summary.append({
            "stage": stage,
            "count": len(products_at_stage),
            "stuck_over_24h": len(stuck),
            "stuck_products": stuck,
        })

    # Include any non-standard stages
    for stage, products in other_stage_data.items():
        stuck = [p for p in products if p["hours_at_stage"] > 24]
        stage_summary.append({
            "stage": stage,
            "count": len(products),
            "stuck_over_24h": len(stuck),
            "stuck_products": stuck,
        })

    total_stuck = sum(s["stuck_over_24h"] for s in stage_summary)

    result = {
        "snapshot_at": _now_iso(),
        "total_digital_products": len(digital_products),
        "total_stuck_over_24h": total_stuck,
        "pipeline": stage_summary,
    }
    return json.dumps(result, indent=2)


def _get_daily_ops_summary(store: DataStore) -> str:
    today = datetime.now(timezone.utc).date().isoformat()
    audit_log = store.get_audit_log(limit=500)
    digital_products = store.get("digital_products", default=[])
    bottlenecks = store.get("bottlenecks", default=[])
    if not isinstance(bottlenecks, list):
        bottlenecks = []

    # Products created today
    products_today = [
        p for p in digital_products
        if (p.get("created_at") or "").startswith(today)
    ]

    # QC pass/fail from audit log today
    qc_pass = sum(
        1 for e in audit_log
        if e.get("ts", "").startswith(today)
        and "qc" in e.get("agent", "").lower()
        and "pass" in e.get("action", "").lower()
    )
    qc_fail = sum(
        1 for e in audit_log
        if e.get("ts", "").startswith(today)
        and "qc" in e.get("agent", "").lower()
        and "fail" in e.get("action", "").lower()
    )

    # Orders delivered today
    orders_delivered = sum(
        1 for o in store.orders
        if o.get("status") in ("completed", "delivered")
        and (o.get("completed_at") or o.get("updated_at") or "").startswith(today)
    )

    # Errors in audit log today
    errors_today = [
        e for e in audit_log
        if e.get("ts", "").startswith(today)
        and "error" in (e.get("action", "") + json.dumps(e.get("details", {}))).lower()
    ]

    # Active bottlenecks
    active_bottlenecks = [b for b in bottlenecks if b.get("status") == "active"]

    # Agent activity today
    agents_active_today = len({
        e["agent"] for e in audit_log
        if e.get("ts", "").startswith(today) and e.get("agent")
    })

    result = {
        "date": today,
        "generated_at": _now_iso(),
        "products_created_today": len(products_today),
        "qc": {
            "passed": qc_pass,
            "failed": qc_fail,
            "pass_rate": f"{qc_pass / max(qc_pass + qc_fail, 1) * 100:.0f}%",
        },
        "orders_delivered_today": orders_delivered,
        "total_orders_in_system": len(store.orders),
        "errors_today": len(errors_today),
        "error_samples": [
            {"agent": e.get("agent"), "action": e.get("action"), "ts": e.get("ts")}
            for e in errors_today[:3]
        ],
        "active_bottlenecks": len(active_bottlenecks),
        "bottleneck_summary": [
            {"id": b["id"], "agent": b["agent_name"], "reason": b["reason"]}
            for b in active_bottlenecks[:5]
        ],
        "agents_active_today": agents_active_today,
        "audit_entries_today": sum(1 for e in audit_log if e.get("ts", "").startswith(today)),
    }
    return json.dumps(result, indent=2)


def _prioritize_task_queue(tasks: list) -> str:
    """Sort tasks by business priority: overdue orders > new orders > listings > analytics > other."""

    PRIORITY_RULES = [
        ("overdue_order", 1),
        ("order", 2),
        ("listing", 3),
        ("analytics", 4),
    ]

    def _score(task: dict) -> tuple:
        task_text = (task.get("task", "") + " " + task.get("agent", "")).lower()
        age_minutes = _minutes_since(task.get("created_at", _now_iso()))

        # Base priority bucket
        bucket = 5  # "other"
        for keyword, b in PRIORITY_RULES:
            if keyword in task_text:
                bucket = b
                break

        # Overdue: any order task older than 60 minutes is escalated to bucket 1
        if bucket == 2 and age_minutes > 60:
            bucket = 1

        # Within same bucket, older tasks come first (higher age = more urgent)
        return (bucket, -age_minutes)

    sorted_tasks = sorted(tasks, key=_score)

    result = {
        "prioritized_at": _now_iso(),
        "total_tasks": len(sorted_tasks),
        "priority_logic": "overdue_orders(1) > new_orders(2) > listings(3) > analytics(4) > other(5)",
        "tasks": [
            {
                **task,
                "priority_rank": i + 1,
                "age_minutes": round(_minutes_since(task.get("created_at", _now_iso())), 1),
            }
            for i, task in enumerate(sorted_tasks)
        ],
    }
    return json.dumps(result, indent=2)


def _submit_idea(agent: str, title: str, description: str, category: str = "general") -> str:
    ideas = _read_ideas()
    idea_id = f"idea_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    entry = {
        "id": idea_id,
        "agent": agent[:40],
        "title": title[:120],
        "description": description[:800],
        "category": category[:40],
        "submitted_at": _now_iso(),
        "status": "pending",
    }
    ideas.append(entry)
    _write_ideas(ideas)
    return json.dumps({"submitted": True, "id": idea_id, "title": entry["title"]})
