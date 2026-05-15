"""Shared submit_idea tool — importable by any agent tools file."""

import json
from datetime import datetime, timezone
from pathlib import Path

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


SUBMIT_IDEA_DEFINITION = {
    "name": "submit_idea",
    "description": (
        "Submit an idea to the shared Ideas Board so it can be reviewed at the next brainstorm meeting. "
        "Use this whenever you spot an opportunity, a new product concept, an improvement, or anything "
        "worth discussing with the team."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Short catchy title for the idea (max 120 chars)",
            },
            "description": {
                "type": "string",
                "description": "Why this idea matters and rough next steps (max 800 chars)",
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
}


def submit_idea(agent: str, title: str, description: str, category: str = "general") -> str:
    ideas = _read_ideas()
    now = datetime.now(timezone.utc)
    idea_id = f"idea_{int(now.timestamp() * 1000)}"
    entry = {
        "id": idea_id,
        "agent": agent[:40],
        "title": title[:120],
        "description": description[:800],
        "category": category[:40],
        "submitted_at": now.isoformat(),
        "status": "pending",
    }
    ideas.append(entry)
    _write_ideas(ideas)
    return json.dumps({"submitted": True, "id": idea_id, "title": entry["title"]})


def handle_submit_idea(tool_input: dict) -> str:
    return submit_idea(
        agent=tool_input.get("agent", "unknown"),
        title=tool_input["title"],
        description=tool_input["description"],
        category=tool_input.get("category", "general"),
    )
