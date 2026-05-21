"""Tools for the marketing packages client system — intake, profiles, and deliverables."""

import json
import os
import re
from datetime import datetime

CLIENTS_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "clients")


def _ensure_clients_dir() -> None:
    os.makedirs(CLIENTS_DIR, exist_ok=True)


def _client_path(client_id: str) -> str:
    return os.path.join(CLIENTS_DIR, f"{client_id}.json")


def _deliverables_dir(client_id: str) -> str:
    return os.path.join(CLIENTS_DIR, "deliverables", client_id)


def _slugify(name: str) -> str:
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:50]


# ── Tool definitions ──────────────────────────────────────────────────────────

INTAKE_TOOL_DEFINITIONS = [
    {
        "name": "save_client_profile",
        "description": (
            "Save or update a client profile after completing the intake interview. "
            "Call this once you have gathered all required information."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "business_name": {"type": "string", "description": "Full name of the business"},
                "business_type": {"type": "string", "description": "Type of business, e.g. Restaurant, Salon, Retail, Law Firm"},
                "location": {"type": "string", "description": "City and state"},
                "package": {
                    "type": "string",
                    "enum": ["starter", "growth", "pro"],
                    "description": "Marketing package tier the client is on",
                },
                "website": {"type": "string", "description": "Business website URL, or empty string if none"},
                "social_platforms": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Platforms they are active on or want to grow, e.g. ['Instagram', 'Facebook']",
                },
                "target_audience": {"type": "string", "description": "Who their ideal customer is"},
                "brand_voice": {"type": "string", "description": "Tone and personality: e.g. Friendly and casual, Professional and authoritative"},
                "top_products_or_services": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Their 3-5 most important products or services",
                },
                "competitors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Named competitors in their local market",
                },
                "goals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What they want to achieve, e.g. more foot traffic, grow Instagram, get more reviews",
                },
                "unique_selling_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "What makes them different or better than competitors",
                },
                "contact_name": {"type": "string", "description": "Owner or primary contact name"},
                "contact_email": {"type": "string", "description": "Contact email address"},
                "additional_notes": {"type": "string", "description": "Any extra context that will help with content creation"},
            },
            "required": [
                "business_name", "business_type", "location", "package",
                "social_platforms", "target_audience", "brand_voice",
                "top_products_or_services", "goals", "unique_selling_points",
                "contact_name",
            ],
        },
    },
    {
        "name": "load_client_profile",
        "description": "Load an existing client profile by their client ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "client_id": {"type": "string", "description": "The client's slug ID, e.g. 'joes-pizza-shop'"}
            },
            "required": ["client_id"],
        },
    },
    {
        "name": "list_clients",
        "description": "List all saved client profiles.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]

_LOAD_CLIENT_TOOL = {
    "name": "load_client_profile",
    "description": "Load a client profile to understand their business, goals, and package tier.",
    "input_schema": {
        "type": "object",
        "properties": {"client_id": {"type": "string", "description": "The client's slug ID"}},
        "required": ["client_id"],
    },
}

_LIST_CLIENTS_TOOL = {
    "name": "list_clients",
    "description": "List all saved client profiles.",
    "input_schema": {"type": "object", "properties": {}, "required": []},
}

_SAVE_DELIVERABLE_TOOL = {
    "name": "save_deliverable",
    "description": "Save generated content as a deliverable file for the client.",
    "input_schema": {
        "type": "object",
        "properties": {
            "client_id": {"type": "string", "description": "The client's slug ID"},
            "deliverable_type": {
                "type": "string",
                "description": (
                    "Type of content: social_posts, newsletter, ad_copy, content_calendar, "
                    "blog_outline, audit_report, seo_report, monthly_report, weekly_report"
                ),
            },
            "month": {"type": "string", "description": "Month this content is for, e.g. 'June 2026'"},
            "content": {"type": "string", "description": "The full content to save"},
        },
        "required": ["client_id", "deliverable_type", "month", "content"],
    },
}

_LIST_DELIVERABLES_TOOL = {
    "name": "list_deliverables",
    "description": "List all deliverables saved for a client.",
    "input_schema": {
        "type": "object",
        "properties": {"client_id": {"type": "string", "description": "The client's slug ID"}},
        "required": ["client_id"],
    },
}

_READ_DELIVERABLE_TOOL = {
    "name": "read_deliverable",
    "description": "Read the full contents of a specific deliverable file for a client.",
    "input_schema": {
        "type": "object",
        "properties": {
            "client_id": {"type": "string", "description": "The client's slug ID"},
            "filename": {"type": "string", "description": "The filename returned by list_deliverables"},
        },
        "required": ["client_id", "filename"],
    },
}

# Shared tool sets for each agent type
COPYWRITER_TOOL_DEFINITIONS = [
    _LOAD_CLIENT_TOOL, _LIST_CLIENTS_TOOL, _SAVE_DELIVERABLE_TOOL, _LIST_DELIVERABLES_TOOL,
]

AUDIT_TOOL_DEFINITIONS = [
    _LOAD_CLIENT_TOOL, _LIST_CLIENTS_TOOL, _SAVE_DELIVERABLE_TOOL, _LIST_DELIVERABLES_TOOL,
]

SEO_TOOL_DEFINITIONS = [
    _LOAD_CLIENT_TOOL, _LIST_CLIENTS_TOOL, _SAVE_DELIVERABLE_TOOL, _LIST_DELIVERABLES_TOOL,
]

REPORT_TOOL_DEFINITIONS = [
    _LOAD_CLIENT_TOOL, _LIST_CLIENTS_TOOL, _SAVE_DELIVERABLE_TOOL,
    _LIST_DELIVERABLES_TOOL, _READ_DELIVERABLE_TOOL,
]

MANAGER_DIRECT_TOOLS = [_LOAD_CLIENT_TOOL, _LIST_CLIENTS_TOOL]


# ── Tool implementations ───────────────────────────────────────────────────────

def execute_intake_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "save_client_profile":
        return _save_client_profile(tool_input)
    if tool_name == "load_client_profile":
        return _load_client_profile(tool_input["client_id"])
    if tool_name == "list_clients":
        return _list_clients()
    return f"Unknown intake tool: {tool_name}"


def execute_shared_tool(tool_name: str, tool_input: dict) -> str:
    """Single executor for all non-intake client agents."""
    if tool_name == "load_client_profile":
        return _load_client_profile(tool_input["client_id"])
    if tool_name == "list_clients":
        return _list_clients()
    if tool_name == "save_deliverable":
        return _save_deliverable(
            tool_input["client_id"],
            tool_input["deliverable_type"],
            tool_input["month"],
            tool_input["content"],
        )
    if tool_name == "list_deliverables":
        return _list_deliverables(tool_input["client_id"])
    if tool_name == "read_deliverable":
        return _read_deliverable(tool_input["client_id"], tool_input["filename"])
    return f"Unknown tool: {tool_name}"


def execute_copywriter_tool(tool_name: str, tool_input: dict) -> str:
    return execute_shared_tool(tool_name, tool_input)


def _save_client_profile(data: dict) -> str:
    _ensure_clients_dir()
    client_id = _slugify(data["business_name"])
    profile = {
        "id": client_id,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        **data,
    }
    path = _client_path(client_id)
    with open(path, "w") as f:
        json.dump(profile, f, indent=2)
    return json.dumps({"status": "saved", "client_id": client_id, "path": path}, indent=2)


def _load_client_profile(client_id: str) -> str:
    path = _client_path(client_id)
    if not os.path.exists(path):
        clients = _list_client_ids()
        return json.dumps({
            "error": f"Client '{client_id}' not found.",
            "available_clients": clients,
        }, indent=2)
    with open(path) as f:
        return f.read()


def _list_clients() -> str:
    _ensure_clients_dir()
    clients = []
    for fname in sorted(os.listdir(CLIENTS_DIR)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(CLIENTS_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
            clients.append({
                "client_id": data.get("id", fname[:-5]),
                "business_name": data.get("business_name", "Unknown"),
                "business_type": data.get("business_type", ""),
                "package": data.get("package", ""),
                "location": data.get("location", ""),
            })
        except (json.JSONDecodeError, OSError):
            continue
    if not clients:
        return json.dumps({"clients": [], "message": "No clients saved yet."}, indent=2)
    return json.dumps({"clients": clients, "total": len(clients)}, indent=2)


def _list_client_ids() -> list[str]:
    if not os.path.exists(CLIENTS_DIR):
        return []
    return [f[:-5] for f in os.listdir(CLIENTS_DIR) if f.endswith(".json")]


def _save_deliverable(client_id: str, deliverable_type: str, month: str, content: str) -> str:
    output_dir = _deliverables_dir(client_id)
    os.makedirs(output_dir, exist_ok=True)
    month_slug = _slugify(month)
    filename = f"{deliverable_type}_{month_slug}.txt"
    path = os.path.join(output_dir, filename)
    with open(path, "w") as f:
        f.write(f"Client: {client_id}\n")
        f.write(f"Type: {deliverable_type}\n")
        f.write(f"Month: {month}\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(content)
    return json.dumps({"status": "saved", "file": filename, "path": path}, indent=2)


def _list_deliverables(client_id: str) -> str:
    output_dir = _deliverables_dir(client_id)
    if not os.path.exists(output_dir):
        return json.dumps({"client_id": client_id, "deliverables": [], "message": "No deliverables yet."}, indent=2)
    files = sorted(os.listdir(output_dir))
    return json.dumps({"client_id": client_id, "deliverables": files, "total": len(files)}, indent=2)


def _read_deliverable(client_id: str, filename: str) -> str:
    path = os.path.join(_deliverables_dir(client_id), filename)
    if not os.path.exists(path):
        return json.dumps({"error": f"Deliverable '{filename}' not found for client '{client_id}'."}, indent=2)
    with open(path) as f:
        return f.read()
