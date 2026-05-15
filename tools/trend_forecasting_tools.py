"""
Trend Forecasting Tools — spots upcoming Etsy trends 8-16 weeks before they peak.

Classifies trends as HOT (peaking now), EMERGING (4-8 weeks out), or UPCOMING (8-16 weeks out).
Flags high-confidence trends to the Art Creation Agent via the art_queue data store key.
"""

import json
from datetime import date
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_trend_radar",
        "description": (
            "Returns the current trend radar: hot niches (peaking now), emerging niches "
            "(4-8 weeks out), and upcoming niches (8-16 weeks out). Reads from data store."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_trend_signal",
        "description": "Saves a new trend signal to the trend radar data store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "signal_name": {"type": "string", "description": "Name of the trend or niche"},
                "category": {
                    "type": "string",
                    "enum": ["hot", "emerging", "upcoming"],
                    "description": "Classification: hot=peaking now, emerging=4-8 weeks, upcoming=8-16 weeks",
                },
                "evidence": {"type": "string", "description": "Supporting evidence for this trend"},
                "source": {"type": "string", "description": "Where the signal came from (Pinterest, Etsy, etc.)"},
                "confidence": {
                    "type": "integer",
                    "description": "Confidence score 1-10 (10 = highest confidence)",
                    "minimum": 1,
                    "maximum": 10,
                },
                "action_items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of concrete action items to act on this trend",
                },
            },
            "required": ["signal_name", "category", "evidence", "source", "confidence", "action_items"],
        },
    },
    {
        "name": "get_seasonal_calendar",
        "description": (
            "Returns a 12-month seasonal opportunity calendar for Etsy digital products. "
            "Includes peak_weeks_before — how many weeks ahead to create the products."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "research_trend_keywords",
        "description": (
            "Returns SEO-optimised search terms to validate a trend's size. "
            "Checks data store for saved research; if none found, returns a suggested research approach."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trend_name": {"type": "string", "description": "The trend or niche to research"},
            },
            "required": ["trend_name"],
        },
    },
    {
        "name": "flag_trend_for_art_agent",
        "description": (
            "Flags a trend for the Art Creation Agent to execute on. "
            "Saves to the art_queue in the data store with pending status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "trend_name": {"type": "string", "description": "Name of the trend to act on"},
                "art_style": {"type": "string", "description": "Describe the art style or visual direction"},
                "target_size": {
                    "type": "string",
                    "description": "Target image size",
                    "default": "1024x1536",
                },
                "priority": {
                    "type": "string",
                    "enum": ["urgent", "high", "normal"],
                    "description": "Priority level for the Art Agent",
                },
            },
            "required": ["trend_name", "art_style", "priority"],
        },
    },
    {
        "name": "get_art_queue",
        "description": (
            "Returns all items in the art queue that the Trend Agent has flagged for the Art Agent. "
            "Shows status (pending/in_progress/done) for each item."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

TOOL_NAMES: set[str] = {t["name"] for t in TOOL_DEFINITIONS}


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_trend_radar":
        return _get_trend_radar(store)
    if tool_name == "save_trend_signal":
        return _save_trend_signal(tool_input, store)
    if tool_name == "get_seasonal_calendar":
        return _get_seasonal_calendar()
    if tool_name == "research_trend_keywords":
        return _research_trend_keywords(tool_input, store)
    if tool_name == "flag_trend_for_art_agent":
        return _flag_trend_for_art_agent(tool_input, store)
    if tool_name == "get_art_queue":
        return _get_art_queue(store)
    return f"Unknown trend forecasting tool: {tool_name}"


def _get_trend_radar(store: DataStore) -> str:
    radar = store.get("trend_radar", default={"hot": [], "emerging": [], "upcoming": []})
    hot = radar.get("hot", [])
    emerging = radar.get("emerging", [])
    upcoming = radar.get("upcoming", [])
    return json.dumps(
        {
            "as_of": str(date.today()),
            "trend_radar": {
                "hot": {
                    "description": "Peaking now — create and list immediately",
                    "signals": hot,
                    "count": len(hot),
                },
                "emerging": {
                    "description": "4-8 weeks out — plan and start creating now",
                    "signals": emerging,
                    "count": len(emerging),
                },
                "upcoming": {
                    "description": "8-16 weeks out — queue for later, monitor closely",
                    "signals": upcoming,
                    "count": len(upcoming),
                },
            },
            "tip": (
                "Focus execution energy on HOT and EMERGING. "
                "Queue UPCOMING items via flag_trend_for_art_agent with priority=normal."
            ),
        },
        indent=2,
    )


def _save_trend_signal(data: dict, store: DataStore) -> str:
    radar = store.get("trend_radar", default={"hot": [], "emerging": [], "upcoming": []})
    category = data["category"]
    if category not in radar:
        radar[category] = []

    signal = {
        "signal_name": data["signal_name"],
        "evidence": data["evidence"],
        "source": data["source"],
        "confidence": data["confidence"],
        "action_items": data["action_items"],
        "saved_at": str(date.today()),
    }
    radar[category].append(signal)
    store.set(radar, "trend_radar")
    store.save()
    return json.dumps(
        {
            "success": True,
            "saved": signal,
            "category": category,
            "total_in_category": len(radar[category]),
            "next_step": (
                "Use flag_trend_for_art_agent if confidence >= 7 to queue art creation."
            ),
        },
        indent=2,
    )


def _get_seasonal_calendar() -> str:
    calendar = [
        {
            "month": 1,
            "month_name": "January",
            "theme": "New Year / Fresh Start",
            "top_niches": ["new year planners", "goal setting sheets", "habit trackers", "vision board printables"],
            "peak_weeks_before": 8,
        },
        {
            "month": 2,
            "month_name": "February",
            "theme": "Valentine's Day / Love",
            "top_niches": ["valentines prints", "love quote wall art", "heart-themed planners", "couples gift prints"],
            "peak_weeks_before": 6,
        },
        {
            "month": 3,
            "month_name": "March",
            "theme": "Spring Botanicals",
            "top_niches": ["spring botanical prints", "floral wall art", "garden watercolour", "nature printables"],
            "peak_weeks_before": 4,
        },
        {
            "month": 4,
            "month_name": "April",
            "theme": "Easter / Spring Home Decor",
            "top_niches": ["easter printables", "spring home decor prints", "pastel floral art", "bunny clipart"],
            "peak_weeks_before": 6,
        },
        {
            "month": 5,
            "month_name": "May",
            "theme": "Mother's Day / Floral",
            "top_niches": ["mothers day prints", "floral gift art", "sentimental quote prints", "flower wall art"],
            "peak_weeks_before": 8,
        },
        {
            "month": 6,
            "month_name": "June",
            "theme": "Wedding / Summer",
            "top_niches": ["wedding planners", "seating chart templates", "summer botanical prints", "beach wall art"],
            "peak_weeks_before": 10,
        },
        {
            "month": 7,
            "month_name": "July",
            "theme": "Patriotic / Summer",
            "top_niches": ["patriotic printables", "4th of july art", "summer quote prints", "americana decor"],
            "peak_weeks_before": 4,
        },
        {
            "month": 8,
            "month_name": "August",
            "theme": "Back to School / Planners",
            "top_niches": [
                "back to school planners",
                "student planner printable",
                "classroom decor",
                "study schedule template",
            ],
            "peak_weeks_before": 6,
        },
        {
            "month": 9,
            "month_name": "September",
            "theme": "Fall Botanicals / Autumn",
            "top_niches": ["fall botanical prints", "autumn wall art", "pumpkin printables", "harvest decor"],
            "peak_weeks_before": 4,
        },
        {
            "month": 10,
            "month_name": "October",
            "theme": "Halloween / Dark Moody",
            "top_niches": [
                "halloween printables",
                "dark moody wall art",
                "gothic botanical prints",
                "spooky clipart",
            ],
            "peak_weeks_before": 6,
        },
        {
            "month": 11,
            "month_name": "November",
            "theme": "Thanksgiving / Gratitude",
            "top_niches": [
                "thanksgiving printables",
                "gratitude journal pages",
                "autumn thankful prints",
                "harvest table decor",
            ],
            "peak_weeks_before": 4,
        },
        {
            "month": 12,
            "month_name": "December",
            "theme": "Christmas / Winter — BIGGEST SEASON",
            "top_niches": [
                "christmas wall art",
                "winter botanical prints",
                "gift tags printable",
                "christmas planner",
                "holiday quote prints",
            ],
            "peak_weeks_before": 12,
        },
    ]
    today = date.today()
    current_month = today.month
    # Rotate calendar so it starts from current month
    rotated = calendar[current_month - 1 :] + calendar[: current_month - 1]
    return json.dumps(
        {
            "as_of": str(today),
            "seasonal_calendar": rotated,
            "strategy": (
                "Create content peak_weeks_before the target month. "
                "Etsy needs time to index and rank new listings — don't list at the last minute."
            ),
        },
        indent=2,
    )


def _research_trend_keywords(data: dict, store: DataStore) -> str:
    trend_name = data["trend_name"]
    saved = store.get("trend_research", default={})
    key = trend_name.lower().strip()

    if key in saved:
        return json.dumps(
            {
                "trend_name": trend_name,
                "source": "data_store",
                "keywords": saved[key],
            },
            indent=2,
        )

    # Build a suggested research approach based on the trend name
    base_terms = [trend_name, f"{trend_name} printable", f"{trend_name} digital download",
                  f"{trend_name} wall art", f"{trend_name} print", f"instant download {trend_name}"]
    long_tail = [f"printable {trend_name} art", f"{trend_name} gift", f"{trend_name} home decor",
                 f"digital {trend_name} print", f"{trend_name} poster"]

    return json.dumps(
        {
            "trend_name": trend_name,
            "source": "suggested",
            "note": "No saved research found. Use these suggested keywords to validate on Etsy and Pinterest.",
            "suggested_search_terms": base_terms,
            "long_tail_variations": long_tail,
            "validation_steps": [
                f"Search '{trend_name}' on Etsy — note result count (< 1,000 = low competition)",
                f"Search '{trend_name}' on Pinterest — check if boards are growing",
                "Look at Google Trends for the past 90 days",
                "Check if top Etsy results have recent dates (< 6 months old = active niche)",
                "Count favorites on top 10 listings — high favorites = real demand",
            ],
            "save_tip": "Save confirmed research to data store under 'trend_research' key for future lookups.",
        },
        indent=2,
    )


def _flag_trend_for_art_agent(data: dict, store: DataStore) -> str:
    queue = store.get("art_queue", default=[])
    item = {
        "trend_name": data["trend_name"],
        "art_style": data["art_style"],
        "target_size": data.get("target_size", "1024x1536"),
        "priority": data["priority"],
        "status": "pending",
        "flagged_by": "TrendForecastingAgent",
        "flagged_at": str(date.today()),
    }
    queue.append(item)
    store.set(queue, "art_queue")
    store.save()
    return json.dumps(
        {
            "success": True,
            "queued_item": item,
            "queue_position": len(queue),
            "message": (
                f"Trend '{data['trend_name']}' flagged for Art Creation Agent "
                f"with priority={data['priority']}. "
                "Art Agent should pick this up on next run."
            ),
        },
        indent=2,
    )


def _get_art_queue(store: DataStore) -> str:
    queue = store.get("art_queue", default=[])
    by_status: dict = {"pending": [], "in_progress": [], "done": []}
    for item in queue:
        status = item.get("status", "pending")
        by_status.setdefault(status, []).append(item)

    return json.dumps(
        {
            "as_of": str(date.today()),
            "art_queue": {
                "pending": {"count": len(by_status["pending"]), "items": by_status["pending"]},
                "in_progress": {"count": len(by_status.get("in_progress", [])), "items": by_status.get("in_progress", [])},
                "done": {"count": len(by_status["done"]), "items": by_status["done"]},
            },
            "total_items": len(queue),
        },
        indent=2,
    )
