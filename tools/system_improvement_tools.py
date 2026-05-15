"""Tools for the System Improvement Agent — codebase scanning, web research, auto-patching, and structured logging."""

import json
import os
import re
import subprocess
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT  = Path(__file__).parent.parent
DATA_DIR   = REPO_ROOT / "data"
LOG_FILE   = DATA_DIR / "improvement_log.json"
AGENTS_DIR = REPO_ROOT / "agents"
TOOLS_DIR  = REPO_ROOT / "tools"

# ── Log helpers ────────────────────────────────────────────────────────────────

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _read_log() -> list:
    try:
        if LOG_FILE.exists():
            return json.loads(LOG_FILE.read_text())
    except Exception:
        pass
    return []

def _append_log(entry: dict):
    log = _read_log()
    log.insert(0, entry)
    log[:] = log[:500]
    LOG_FILE.write_text(json.dumps(log, indent=2))

# ── Tool implementations ───────────────────────────────────────────────────────

def _log_action(action: str, detail: str, severity: str = "info", file_changed: str = "") -> str:
    entry = {
        "ts": _now(), "type": "action", "severity": severity,
        "action": action, "detail": detail, "file_changed": file_changed,
    }
    _append_log(entry)
    return json.dumps({"logged": True, "ts": entry["ts"]})

def _log_suggestion(title: str, description: str, priority: str = "medium", category: str = "general") -> str:
    entry = {
        "ts": _now(), "type": "suggestion", "severity": priority,
        "action": title, "detail": description, "category": category,
    }
    _append_log(entry)
    return json.dumps({"logged": True, "title": title})

def _scan_file(filepath: str) -> str:
    path = (REPO_ROOT / filepath).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        return json.dumps({"error": "Path outside repo"})
    if not path.exists():
        return json.dumps({"error": f"File not found: {filepath}"})
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        lines   = content.splitlines()
        todos   = [f"L{i+1}: {l.strip()}" for i, l in enumerate(lines) if re.search(r"TODO|FIXME|HACK|XXX", l, re.I)]
        return json.dumps({
            "filepath": filepath,
            "lines": len(lines),
            "todos": todos[:20],
            "content": content[:8000],
        })
    except Exception as exc:
        return json.dumps({"error": str(exc)})

def _list_files(directory: str = "", pattern: str = "*.py") -> str:
    base = (REPO_ROOT / directory).resolve() if directory else REPO_ROOT
    try:
        base.relative_to(REPO_ROOT)
    except ValueError:
        return json.dumps({"error": "Path outside repo"})
    try:
        files = [
            str(f.relative_to(REPO_ROOT))
            for f in base.rglob(pattern)
            if "__pycache__" not in str(f) and ".git" not in str(f)
        ]
        return json.dumps({"files": sorted(files)[:60], "count": len(files)})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

def _patch_file(filepath: str, old_text: str, new_text: str) -> str:
    path = (REPO_ROOT / filepath).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        return json.dumps({"error": "Path outside repo"})
    if not path.exists():
        return json.dumps({"error": "File not found"})
    if old_text == new_text:
        return json.dumps({"error": "old_text and new_text are identical"})
    content = path.read_text(encoding="utf-8")
    if old_text not in content:
        return json.dumps({"error": "old_text not found in file — check exact whitespace"})
    count = content.count(old_text)
    if count > 1:
        return json.dumps({"error": f"old_text appears {count} times — provide more context to make it unique"})
    path.write_text(content.replace(old_text, new_text, 1), encoding="utf-8")
    _append_log({
        "ts": _now(), "type": "fix", "severity": "info",
        "action": f"Auto-patched {filepath}",
        "detail": f"Replaced: {old_text[:120].strip()}",
        "file_changed": filepath,
    })
    return json.dumps({"patched": True, "filepath": filepath})

def _run_syntax_check(filepath: str) -> str:
    path = (REPO_ROOT / filepath).resolve()
    try:
        path.relative_to(REPO_ROOT)
    except ValueError:
        return json.dumps({"error": "Path outside repo"})
    if not path.exists():
        return json.dumps({"error": "File not found"})
    try:
        result = subprocess.run(
            ["python", "-m", "py_compile", str(path)],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            return json.dumps({"ok": True, "filepath": filepath})
        return json.dumps({"ok": False, "filepath": filepath, "error": result.stderr[:600]})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

def _read_task_history(limit: int = 100) -> str:
    history_file = DATA_DIR / "task_history.json"
    try:
        if not history_file.exists():
            return json.dumps({"error": "No task history yet"})
        history = json.loads(history_file.read_text())
        recent  = history[:limit]
        errors  = [h for h in recent if h.get("status") == "error"]
        slow    = [h for h in recent if h.get("duration_s", 0) > 90]
        agents_seen: dict = {}
        for h in recent:
            a = h.get("agent", "?")
            agents_seen[a] = agents_seen.get(a, {"runs": 0, "errors": 0})
            agents_seen[a]["runs"] += 1
            if h.get("status") == "error":
                agents_seen[a]["errors"] += 1
        return json.dumps({
            "total_recent": len(recent),
            "error_count": len(errors),
            "slow_count": len(slow),
            "agent_summary": agents_seen,
            "recent_errors": [
                {"agent": e.get("agent"), "task": e.get("task", "")[:80], "error": e.get("result_preview", "")[:200]}
                for e in errors[:8]
            ],
            "slow_tasks": [
                {"agent": s.get("agent"), "task": s.get("task", "")[:80], "duration_s": s.get("duration_s")}
                for s in slow[:5]
            ],
        })
    except Exception as exc:
        return json.dumps({"error": str(exc)})

def _check_dependencies() -> str:
    req_file = REPO_ROOT / "requirements.txt"
    if not req_file.exists():
        return json.dumps({"error": "No requirements.txt found"})
    try:
        result = subprocess.run(
            ["pip", "list", "--outdated", "--format=json"],
            capture_output=True, text=True, timeout=30,
        )
        if result.stdout.strip().startswith("["):
            outdated = json.loads(result.stdout)
            return json.dumps({"outdated_count": len(outdated), "outdated": outdated[:15]})
        return json.dumps({"outdated_count": 0, "note": result.stdout[:300]})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

def _web_search(query: str, max_results: int = 6) -> str:
    try:
        encoded = urllib.parse.quote_plus(query)
        url     = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_redirect=1&no_html=1"
        req     = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (SystemBot/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read())
        results = []
        if data.get("Abstract"):
            results.append({"type": "abstract", "text": data["Abstract"][:500], "url": data.get("AbstractURL", "")})
        for topic in data.get("RelatedTopics", []):
            if isinstance(topic, dict) and topic.get("Text"):
                results.append({"type": "topic", "text": topic["Text"][:300], "url": topic.get("FirstURL", "")})
            if len(results) >= max_results:
                break
        return json.dumps({"query": query, "results": results})
    except Exception as exc:
        return json.dumps({"query": query, "error": str(exc), "results": []})

def _fetch_url(url: str, max_chars: int = 4000) -> str:
    if not url.startswith(("https://", "http://")):
        return json.dumps({"error": "Only http/https URLs allowed"})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        text = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.I)
        text = re.sub(r"<style[^>]*>.*?</style>",  " ", text, flags=re.DOTALL | re.I)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return json.dumps({"url": url, "content": text[:max_chars]})
    except Exception as exc:
        return json.dumps({"url": url, "error": str(exc)})

def _get_improvement_log(limit: int = 50) -> str:
    log = _read_log()
    return json.dumps({"entries": log[:limit], "total": len(log)})

def _get_agent_error_patterns() -> str:
    """Analyse task history for recurring error patterns across agents."""
    history_file = DATA_DIR / "task_history.json"
    try:
        if not history_file.exists():
            return json.dumps({"patterns": []})
        history = json.loads(history_file.read_text())
        errors  = [h for h in history if h.get("status") == "error"]
        patterns: dict = {}
        for e in errors:
            preview = e.get("result_preview", "")
            # Bucket by first meaningful word of error
            key = re.split(r"[\s:'\"]", preview.strip())[0][:40] if preview else "unknown"
            patterns[key] = patterns.get(key, 0) + 1
        sorted_patterns = sorted(patterns.items(), key=lambda x: -x[1])
        return json.dumps({"total_errors": len(errors), "patterns": sorted_patterns[:15]})
    except Exception as exc:
        return json.dumps({"error": str(exc)})

# ── Tool definitions ───────────────────────────────────────────────────────────

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "log_action",
        "description": "Log an action, finding, or completed fix to the improvement log.",
        "input_schema": {
            "type": "object",
            "properties": {
                "action":  {"type": "string", "description": "Short title (e.g. 'Fixed missing timeout in analytics_tools.py')"},
                "detail":  {"type": "string", "description": "Full explanation of what was found or done"},
                "severity":{"type": "string", "enum": ["info","warning","error"], "description": "Severity level"},
                "file_changed": {"type": "string", "description": "Relative filepath if a file was changed, else empty string"},
            },
            "required": ["action", "detail"],
        },
    },
    {
        "name": "log_suggestion",
        "description": "Log a suggestion for an improvement that requires human review or is too risky to auto-apply.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title":       {"type": "string", "description": "Short actionable title"},
                "description": {"type": "string", "description": "Full explanation including WHY this matters, HOW to implement, and any code examples"},
                "priority":    {"type": "string", "enum": ["low","medium","high","critical"]},
                "category":    {"type": "string", "enum": ["performance","reliability","security","feature","integration","ux","cost"]},
            },
            "required": ["title", "description", "priority", "category"],
        },
    },
    {
        "name": "scan_file",
        "description": "Read a file from the repository for analysis. Returns content, line count, and any TODO/FIXME markers.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path relative to repo root, e.g. 'agents/analytics_agent.py'"},
            },
            "required": ["filepath"],
        },
    },
    {
        "name": "list_files",
        "description": "List files in a directory matching a pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directory": {"type": "string", "description": "Directory relative to repo root (empty = root)"},
                "pattern":   {"type": "string", "description": "Glob pattern, e.g. '*.py', '*.json'"},
            },
            "required": [],
        },
    },
    {
        "name": "patch_file",
        "description": "Apply a targeted patch to a file. old_text must appear exactly once. Always run syntax_check after patching Python files.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path relative to repo root"},
                "old_text": {"type": "string", "description": "The exact text to replace (must be unique in the file)"},
                "new_text": {"type": "string", "description": "The replacement text"},
            },
            "required": ["filepath", "old_text", "new_text"],
        },
    },
    {
        "name": "syntax_check",
        "description": "Run Python syntax check (py_compile) on a file. Always call this after patching a .py file.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "description": "Path relative to repo root"},
            },
            "required": ["filepath"],
        },
    },
    {
        "name": "read_task_history",
        "description": "Read recent task history to find agent errors, slow runs, and performance patterns.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many recent entries to analyse (default 100)"},
            },
            "required": [],
        },
    },
    {
        "name": "get_agent_error_patterns",
        "description": "Analyse task history and return a frequency table of recurring error patterns.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "check_dependencies",
        "description": "Check Python dependencies for outdated packages.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "web_search",
        "description": "Search the internet via DuckDuckGo for documentation, best practices, new techniques, or library updates relevant to this platform.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query":       {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Max results to return (default 6)"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": "Fetch and read content from a URL — GitHub, PyPI, documentation pages, changelogs, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Full https:// URL to fetch"},
            },
            "required": ["url"],
        },
    },
    {
        "name": "get_improvement_log",
        "description": "Read the improvement log to see what has already been checked or fixed in previous scans.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many recent entries to return (default 50)"},
            },
            "required": [],
        },
    },
]

TOOL_NAMES = {t["name"] for t in TOOL_DEFINITIONS}

# ── Dispatch ───────────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "log_action":
        return _log_action(
            tool_input["action"], tool_input["detail"],
            tool_input.get("severity", "info"), tool_input.get("file_changed", ""),
        )
    if tool_name == "log_suggestion":
        return _log_suggestion(
            tool_input["title"], tool_input["description"],
            tool_input.get("priority", "medium"), tool_input.get("category", "general"),
        )
    if tool_name == "scan_file":
        return _scan_file(tool_input["filepath"])
    if tool_name == "list_files":
        return _list_files(tool_input.get("directory", ""), tool_input.get("pattern", "*.py"))
    if tool_name == "patch_file":
        return _patch_file(tool_input["filepath"], tool_input["old_text"], tool_input["new_text"])
    if tool_name == "syntax_check":
        return _run_syntax_check(tool_input["filepath"])
    if tool_name == "read_task_history":
        return _read_task_history(tool_input.get("limit", 100))
    if tool_name == "get_agent_error_patterns":
        return _get_agent_error_patterns()
    if tool_name == "check_dependencies":
        return _check_dependencies()
    if tool_name == "web_search":
        return _web_search(tool_input["query"], tool_input.get("max_results", 6))
    if tool_name == "fetch_url":
        return _fetch_url(tool_input["url"])
    if tool_name == "get_improvement_log":
        return _get_improvement_log(tool_input.get("limit", 50))
    return json.dumps({"error": f"Unknown tool: {tool_name}"})
