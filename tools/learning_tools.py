"""
Learning Tools — persistent knowledge base that makes every agent smarter over time.
Insights, strategies, keywords, and design discoveries are saved across sessions.
Agents MUST check their knowledge base before acting and save learnings after research.
"""
import json
import os
from datetime import datetime

KB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "knowledge_base")

TOOL_NAMES = {
    "save_market_insight",
    "get_market_insights",
    "save_winning_strategy",
    "get_strategies",
    "log_keyword_performance",
    "get_top_keywords",
    "log_product_performance",
    "get_performance_history",
    "save_design_discovery",
    "get_design_discoveries",
}

TOOL_DEFINITIONS = [
    {
        "name": "save_market_insight",
        "description": (
            "Save a market insight to the shared knowledge base. Call after every web research "
            "session. Insights persist across all agent sessions — the more you save, the smarter "
            "the whole team gets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Category: 'pricing', 'keywords', 'design_trends', 'competition', 'product_ideas', 'customer_behavior'",
                },
                "insight": {
                    "type": "string",
                    "description": "The specific, actionable insight to save",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["high", "medium", "low"],
                    "default": "medium",
                },
                "source": {
                    "type": "string",
                    "description": "Where this came from e.g. 'Etsy market research', 'competitor analysis', 'buyer review'",
                },
                "applicable_to": {
                    "type": "string",
                    "description": "Product types or situations this applies to",
                },
            },
            "required": ["category", "insight"],
        },
    },
    {
        "name": "get_market_insights",
        "description": (
            "Retrieve saved market insights. ALWAYS call this at the start of a session to "
            "leverage accumulated knowledge before doing new research."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Filter by category or 'all' for everything",
                    "default": "all",
                },
                "limit": {"type": "integer", "default": 25},
            },
            "required": [],
        },
    },
    {
        "name": "save_winning_strategy",
        "description": (
            "Save a proven strategy that showed measurable positive results. "
            "Future agents will use this to replicate success without starting from scratch."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "strategy_name": {"type": "string"},
                "description": {"type": "string"},
                "outcome": {"type": "string", "description": "Measured result e.g. '+23% CTR', '$45 in 3 days'"},
                "applicable_when": {"type": "string"},
            },
            "required": ["strategy_name", "description", "outcome"],
        },
    },
    {
        "name": "get_strategies",
        "description": "Retrieve all winning strategies. Check before planning any campaign or product launch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_by": {"type": "string", "description": "Optional keyword to filter"},
            },
            "required": [],
        },
    },
    {
        "name": "log_keyword_performance",
        "description": "Track how a keyword is performing over time. Call weekly for each active keyword.",
        "input_schema": {
            "type": "object",
            "properties": {
                "keyword": {"type": "string"},
                "listing_id": {"type": "string"},
                "views_generated": {"type": "integer", "default": 0},
                "sales": {"type": "integer", "default": 0},
                "notes": {"type": "string"},
            },
            "required": ["keyword"],
        },
    },
    {
        "name": "get_top_keywords",
        "description": "Get best-performing keywords from the knowledge base, ranked by sales then views.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20},
                "min_views": {"type": "integer", "default": 0},
            },
            "required": [],
        },
    },
    {
        "name": "log_product_performance",
        "description": "Log product performance to build a historical record of what sells.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string"},
                "product_name": {"type": "string"},
                "views": {"type": "integer", "default": 0},
                "favorites": {"type": "integer", "default": 0},
                "sales": {"type": "integer", "default": 0},
                "revenue": {"type": "number", "default": 0},
                "notes": {"type": "string"},
            },
            "required": ["product_id"],
        },
    },
    {
        "name": "get_performance_history",
        "description": "Get historical product performance data to identify trends and top performers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "product_id": {"type": "string", "description": "Filter to one product or omit for all"},
                "limit": {"type": "integer", "default": 30},
            },
            "required": [],
        },
    },
    {
        "name": "save_design_discovery",
        "description": "Save a design trend or style insight for future product creation decisions.",
        "input_schema": {
            "type": "object",
            "properties": {
                "style_name": {"type": "string"},
                "description": {"type": "string"},
                "target_audience": {"type": "string"},
                "color_palette": {"type": "string", "description": "Describe or list hex colors"},
                "example_products": {"type": "string"},
                "trend_strength": {
                    "type": "string",
                    "enum": ["rising", "peak", "established", "declining"],
                    "default": "established",
                },
            },
            "required": ["style_name", "description"],
        },
    },
    {
        "name": "get_design_discoveries",
        "description": "Get all saved design trends, sorted by momentum (rising first).",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter_trend_strength": {
                    "type": "string",
                    "enum": ["rising", "peak", "established", "declining", "all"],
                    "default": "all",
                },
            },
            "required": [],
        },
    },
]


# ── Storage helpers ────────────────────────────────────────────────────────────

def _path(filename: str) -> str:
    os.makedirs(KB_DIR, exist_ok=True)
    return os.path.join(KB_DIR, filename)


def _load(filename: str) -> list:
    p = _path(filename)
    if not os.path.exists(p):
        return []
    with open(p) as f:
        return json.load(f)


def _dump(filename: str, data: list) -> None:
    with open(_path(filename), "w") as f:
        json.dump(data, f, indent=2)


# ── Tool dispatcher ────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict, agent_name: str = "") -> str:
    dispatch = {
        "save_market_insight": lambda: _save_insight(tool_input, agent_name),
        "get_market_insights": lambda: _get_insights(tool_input),
        "save_winning_strategy": lambda: _save_strategy(tool_input, agent_name),
        "get_strategies": lambda: _get_strategies(tool_input),
        "log_keyword_performance": lambda: _log_keyword(tool_input, agent_name),
        "get_top_keywords": lambda: _get_keywords(tool_input),
        "log_product_performance": lambda: _log_product(tool_input, agent_name),
        "get_performance_history": lambda: _get_history(tool_input),
        "save_design_discovery": lambda: _save_design(tool_input, agent_name),
        "get_design_discoveries": lambda: _get_designs(tool_input),
    }
    fn = dispatch.get(tool_name)
    return fn() if fn else f"Unknown learning tool: {tool_name}"


# ── Implementations ────────────────────────────────────────────────────────────

def _save_insight(inp: dict, agent: str) -> str:
    data = _load("insights.json")
    entry = {
        "id": f"ins_{int(datetime.now().timestamp() * 1000)}",
        "agent": agent,
        "category": inp.get("category", "general"),
        "insight": inp.get("insight", ""),
        "confidence": inp.get("confidence", "medium"),
        "source": inp.get("source", "agent research"),
        "applicable_to": inp.get("applicable_to", ""),
        "saved_at": datetime.now().isoformat(),
    }
    data.append(entry)
    _dump("insights.json", data)
    return json.dumps({"status": "saved", "id": entry["id"], "total_insights": len(data)})


def _get_insights(inp: dict) -> str:
    data = _load("insights.json")
    cat = inp.get("category", "all")
    limit = int(inp.get("limit", 25))
    if cat != "all":
        data = [i for i in data if i.get("category") == cat]
    order = {"high": 0, "medium": 1, "low": 2}
    data.sort(key=lambda x: (order.get(x.get("confidence", "low"), 3), x.get("saved_at", "")))
    all_cats = list(set(i.get("category", "") for i in _load("insights.json")))
    return json.dumps({
        "total": len(data),
        "categories_available": all_cats,
        "insights": data[-limit:],
    }, indent=2)


def _save_strategy(inp: dict, agent: str) -> str:
    data = _load("strategies.json")
    entry = {
        "id": f"strat_{int(datetime.now().timestamp() * 1000)}",
        "agent": agent,
        "strategy_name": inp.get("strategy_name", ""),
        "description": inp.get("description", ""),
        "outcome": inp.get("outcome", ""),
        "applicable_when": inp.get("applicable_when", ""),
        "saved_at": datetime.now().isoformat(),
    }
    data.append(entry)
    _dump("strategies.json", data)
    return json.dumps({"status": "saved", "id": entry["id"]})


def _get_strategies(inp: dict) -> str:
    data = _load("strategies.json")
    kw = inp.get("filter_by", "").lower()
    if kw:
        data = [s for s in data if kw in s.get("description", "").lower() or kw in s.get("strategy_name", "").lower()]
    return json.dumps({"total": len(data), "strategies": data}, indent=2)


def _log_keyword(inp: dict, agent: str) -> str:
    data = _load("keywords.json")
    keyword = inp.get("keyword", "")
    existing = next((k for k in data if k.get("keyword") == keyword), None)
    entry = {
        "timestamp": datetime.now().isoformat(),
        "views": inp.get("views_generated", 0),
        "sales": inp.get("sales", 0),
        "listing_id": inp.get("listing_id", ""),
        "notes": inp.get("notes", ""),
        "agent": agent,
    }
    if existing:
        existing.setdefault("history", []).append(entry)
        existing["total_views"] = sum(h.get("views", 0) for h in existing["history"])
        existing["total_sales"] = sum(h.get("sales", 0) for h in existing["history"])
    else:
        data.append({
            "keyword": keyword,
            "first_tracked": datetime.now().isoformat(),
            "total_views": entry["views"],
            "total_sales": entry["sales"],
            "history": [entry],
        })
    _dump("keywords.json", data)
    return json.dumps({"status": "logged", "keyword": keyword})


def _get_keywords(inp: dict) -> str:
    data = _load("keywords.json")
    limit = int(inp.get("limit", 20))
    min_v = int(inp.get("min_views", 0))
    filtered = [k for k in data if k.get("total_views", 0) >= min_v]
    filtered.sort(key=lambda k: (k.get("total_sales", 0), k.get("total_views", 0)), reverse=True)
    return json.dumps({"total_tracked": len(data), "top_keywords": filtered[:limit]}, indent=2)


def _log_product(inp: dict, agent: str) -> str:
    data = _load("performance.json")
    data.append({
        "product_id": inp.get("product_id", ""),
        "product_name": inp.get("product_name", ""),
        "agent": agent,
        "views": inp.get("views", 0),
        "favorites": inp.get("favorites", 0),
        "sales": inp.get("sales", 0),
        "revenue": inp.get("revenue", 0),
        "notes": inp.get("notes", ""),
        "logged_at": datetime.now().isoformat(),
    })
    _dump("performance.json", data)
    return json.dumps({"status": "logged"})


def _get_history(inp: dict) -> str:
    data = _load("performance.json")
    pid = inp.get("product_id", "")
    limit = int(inp.get("limit", 30))
    if pid:
        data = [h for h in data if h.get("product_id") == pid]
    return json.dumps({"total_records": len(data), "records": data[-limit:]}, indent=2)


def _save_design(inp: dict, agent: str) -> str:
    data = _load("designs.json")
    entry = {
        "id": f"des_{int(datetime.now().timestamp() * 1000)}",
        "agent": agent,
        "style_name": inp.get("style_name", ""),
        "description": inp.get("description", ""),
        "target_audience": inp.get("target_audience", ""),
        "color_palette": inp.get("color_palette", ""),
        "example_products": inp.get("example_products", ""),
        "trend_strength": inp.get("trend_strength", "established"),
        "saved_at": datetime.now().isoformat(),
    }
    data.append(entry)
    _dump("designs.json", data)
    return json.dumps({"status": "saved", "id": entry["id"]})


def _get_designs(inp: dict) -> str:
    data = _load("designs.json")
    fs = inp.get("filter_trend_strength", "all")
    if fs != "all":
        data = [d for d in data if d.get("trend_strength") == fs]
    order = {"rising": 0, "peak": 1, "established": 2, "declining": 3}
    data.sort(key=lambda d: order.get(d.get("trend_strength", "established"), 4))
    return json.dumps({"total": len(data), "discoveries": data}, indent=2)
