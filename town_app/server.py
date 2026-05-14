"""
OnBrandCraftz Town — Real-time Agent Visualization Server
"""

import asyncio
import json
import os
import sys
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    yield


app = FastAPI(title="OnBrandCraftz Town", lifespan=lifespan)

STATIC_DIR = Path(__file__).parent / "static"
DATA_DIR   = Path(__file__).parent.parent / "data"

# ── WebSocket manager ──────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        self._connections: Set[WebSocket] = set()
        self._lock = threading.Lock()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        with self._lock:
            self._connections.add(ws)

    def disconnect(self, ws: WebSocket):
        with self._lock:
            self._connections.discard(ws)

    async def broadcast(self, payload: dict):
        data = json.dumps(payload)
        dead = set()
        with self._lock:
            snapshot = set(self._connections)
        for ws in snapshot:
            try:
                await ws.send_text(data)
            except Exception:
                dead.add(ws)
        if dead:
            with self._lock:
                self._connections -= dead


manager = ConnectionManager()
_event_loop: asyncio.AbstractEventLoop | None = None
agent_states: dict[str, dict] = {}

# ── Delegation tool → agent key map ───────────────────────────────────────────

DELEGATION_MAP: dict[str, str] = {
    "delegate_to_brand_design_agent":    "brand",
    "delegate_to_art_creation_agent":    "art",
    "delegate_to_quality_check_agent":   "qc",
    "delegate_to_etsy_listing_agent":    "listing",
    "delegate_to_store_manager_agent":   "store",
    "delegate_to_sales_processor_agent": "delivery",
    "delegate_to_sales_agent":           "sales",
    "delegate_to_product_agent":         "product",
    "delegate_to_marketing_agent":       "marketing",
    "delegate_to_analytics_agent":       "analytics",
    "delegate_to_customer_service_agent":"cs",
    "delegate_to_social_media_agent":    "social",
    "delegate_to_financial_agent":       "finance",
    "delegate_to_print_production_agent":"print",
    "delegate_to_etsy_ads_agent":        "ads",
    "delegate_to_competitor_intel_agent":"intel",
    "delegate_to_promotions_agent":      "promos",
    "delegate_to_tax_compliance_agent":  "tax",
    "delegate_to_returns_agent":         "returns",
    "delegate_to_supply_chain_agent":    "supply",
    "delegate_to_email_marketing_agent": "email",
    "delegate_to_ab_testing_agent":      "abt",
    "delegate_to_api_connections_agent": "api",
}

# ── Event emission ─────────────────────────────────────────────────────────────

def _emit(agent_key: str, event: str, message: str, extra: dict | None = None):
    if _event_loop is None or _event_loop.is_closed():
        return
    payload = {
        "type":    "agent_event",
        "agent":   agent_key,
        "event":   event,
        "message": message,
        "ts":      datetime.now().strftime("%H:%M:%S"),
        "data":    extra or {},
    }
    asyncio.run_coroutine_threadsafe(manager.broadcast(payload), _event_loop)

# ── Agent factory ──────────────────────────────────────────────────────────────

AGENT_CLASSES: dict[str, str] = {
    "ceo": "CEOAgent", "brand": "BrandDesignAgent", "art": "ArtCreationAgent",
    "qc": "QualityCheckAgent", "listing": "EtsyListingAgent",
    "store": "StoreManagerAgent", "delivery": "SalesProcessorAgent",
    "sales": "SalesAgent", "product": "ProductAgent", "marketing": "MarketingAgent",
    "analytics": "AnalyticsAgent", "cs": "CustomerServiceAgent",
    "social": "SocialMediaAgent", "finance": "FinancialAgent",
    "print": "PrintProductionAgent", "ads": "EtsyAdsAgent",
    "intel": "CompetitorIntelAgent", "promos": "PromotionsAgent",
    "tax": "TaxComplianceAgent", "returns": "ReturnsAgent",
    "supply": "SupplyChainAgent", "email": "EmailMarketingAgent",
    "abt": "ABTestingAgent",
    "api": "APIConnectionsAgent",
}


def _build_agent(key: str):
    import agents as ag
    cls = getattr(ag, AGENT_CLASSES.get(key, ""), None)
    return cls() if cls else None

# ── Pipeline routing ───────────────────────────────────────────────────────────
# Agents that are part of multi-step product pipelines.
# Direct tasks to these agents are rerouted through CEO if they look like
# product creation / launch tasks rather than simple queries.
_PIPELINE_AGENTS = {"brand", "art", "qc", "listing", "store", "marketing", "finance", "analytics"}

# Keywords that indicate a task needs full pipeline orchestration
_PIPELINE_KEYWORDS = {
    "create", "launch", "new product", "new listing", "design a", "design the",
    "make a", "make the", "build a", "generate a", "generate the", "produce a",
    "develop a", "write a listing", "publish", "add to etsy", "add a listing",
    "start a new", "plan a new", "full pipeline", "full process",
}

# First words that indicate a simple query (should NOT be rerouted)
_QUERY_PREFIXES = {
    "get", "list", "show", "check", "what", "how", "report", "status",
    "summary", "analyze", "review", "audit", "find", "search", "give",
    "tell", "explain", "describe", "calculate", "run", "pull",
}


def _should_route_to_ceo(agent_key: str, task: str) -> bool:
    """Return True if this task should be orchestrated by CEO instead of running directly."""
    if agent_key in ("ceo", "hall"):
        return False
    if agent_key not in _PIPELINE_AGENTS:
        return False
    first_word = task.strip().lower().split()[0] if task.strip() else ""
    if first_word in _QUERY_PREFIXES:
        return False
    task_lower = task.lower()
    return any(kw in task_lower for kw in _PIPELINE_KEYWORDS)


# ── Sub-agent runner (used by CEO delegation) ──────────────────────────────────

def _run_sub_agent_observable(target_key: str, task: str) -> str:
    """Build a fresh observable sub-agent, run it, and return its result.

    Called by the CEO's patched_execute_tool when it detects a delegation
    tool call.  This ensures every sub-agent gets its own WebSocket events
    (thinking, tool_call, done) so the town UI shows the correct agent
    working, not just the CEO.
    """
    agent_states[target_key] = {"status": "running", "task": task, "started": datetime.now().isoformat()}
    _emit(target_key, "start", task[:80])
    try:
        sub = _build_agent(target_key)
        if sub is None:
            return f"Error: no agent registered for key '{target_key}'"
        sub = _make_observable(sub, target_key)
        result = sub.run(task)
        agent_states[target_key] = {"status": "idle", "task": task, "last_result": result}
        _emit(target_key, "done", "Complete ✓", {"result": result[:2000]})
        return result
    except Exception as exc:
        agent_states[target_key] = {"status": "error", "task": task, "error": str(exc)}
        _emit(target_key, "error", f"Error: {str(exc)[:200]}")
        return f"[{target_key} error] {exc}"


# ── Observable wrapper ─────────────────────────────────────────────────────────

def _make_observable(agent, key: str):
    original_call_api = agent._call_api
    # Patch _dispatch_tool so we intercept every tool call, including
    # universal web-research and learning tools, not just execute_tool.
    original_dispatch = agent._dispatch_tool

    def patched_call_api(messages):
        _emit(key, "thinking", "Thinking…")
        response = original_call_api(messages)
        tool_blocks = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        if tool_blocks:
            names = ", ".join(b.name for b in tool_blocks)
            _emit(key, "planning", f"Using: {names}")
        return response

    def patched_dispatch(tool_name, tool_input):
        target_key = DELEGATION_MAP.get(tool_name)
        if target_key:
            # CEO is delegating — run the sub-agent observably so the town
            # shows that agent as active with its own events, not just CEO.
            task = tool_input.get("task", "")
            _emit(key, "delegation", f"Delegating → {target_key}", {"to": target_key, "from": key})
            return _run_sub_agent_observable(target_key, task)

        # Emit tool call for visibility in the right panel
        _emit(key, "tool_call", f"→ {tool_name}")
        result = original_dispatch(tool_name, tool_input)

        # Detect created files for image preview
        result_str = str(result)
        file_path = None
        for ext in (".png", ".jpg", ".jpeg", ".pdf"):
            for part in result_str.split('"'):
                if part.endswith(ext) and ("digital_products" in part or "brand" in part):
                    rel = part.replace("\\", "/")
                    if "data/" in rel:
                        rel = rel[rel.index("data/"):]
                    file_path = rel
                    break

        snippet = result_str[:150].replace("\n", " ")
        _emit(key, "tool_result", f"✓ {tool_name}: {snippet}",
              {"file": file_path} if file_path else None)
        return result

    agent._call_api    = patched_call_api
    agent._dispatch_tool = patched_dispatch
    return agent

# ── Task runner ────────────────────────────────────────────────────────────────

def _run_task(key: str, task: str):
    # If a pipeline agent receives a creation/launch task, route it through
    # CEO so the full ordered pipeline fires with correct delegation.
    if _should_route_to_ceo(key, task):
        _emit(key, "routed", f"Routing to CEO for full pipeline…", {"to": "ceo", "from": key})
        agent_name = AGENT_CLASSES.get(key, key)
        ceo_task = (
            f"Task submitted directly to {agent_name}: \"{task}\"\n\n"
            f"Orchestrate the appropriate agents in the correct order to complete this. "
            f"Follow the full pre-listing pipeline (Art → QC → Brand → Marketing → "
            f"Financial → Listing → CEO approval) as required."
        )
        key  = "ceo"
        task = ceo_task

    agent_states[key] = {"status": "running", "task": task, "started": datetime.now().isoformat()}
    _emit(key, "start", task[:80])
    try:
        agent = _build_agent(key)
        if agent is None:
            raise ValueError(f"Unknown agent: {key}")
        agent  = _make_observable(agent, key)
        result = agent.run(task)
        agent_states[key] = {"status": "idle", "task": task, "last_result": result}
        _emit(key, "done", "Complete ✓", {"result": result[:2000]})
    except Exception as exc:
        agent_states[key] = {"status": "error", "task": task, "error": str(exc)}
        _emit(key, "error", f"Error: {str(exc)[:300]}")

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/agents")
async def list_agents():
    return JSONResponse({"agents": list(AGENT_CLASSES.keys()), "states": agent_states})


@app.get("/api/config")
async def get_config():
    """Return which API keys/tokens are configured (not the values)."""
    def is_set(var):
        v = os.getenv(var, "")
        return bool(v and not v.startswith("your_"))
    return JSONResponse({
        "anthropic":   is_set("ANTHROPIC_API_KEY"),
        "openai":      is_set("OPENAI_API_KEY"),
        "smtp":        is_set("SMTP_USER") and is_set("SMTP_PASSWORD"),
        "etsy_api":    is_set("ETSY_API_KEY"),
        "etsy_oauth":  is_set("ETSY_ACCESS_TOKEN"),
        "pinterest":   is_set("PINTEREST_ACCESS_TOKEN"),
    })


@app.get("/data/{path:path}")
async def serve_data_file(path: str):
    """Serve files created by agents (images, PDFs, etc)."""
    target = (DATA_DIR / path).resolve()
    if DATA_DIR.resolve() not in target.parents:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/api/files")
async def list_files():
    """List all files created by agents."""
    files = []
    for folder in ["digital_products/product_files", "brand/assets"]:
        d = DATA_DIR / folder
        if d.exists():
            for f in d.iterdir():
                if f.is_file():
                    files.append({
                        "name": f.name,
                        "path": f"data/{folder}/{f.name}",
                        "size_kb": round(f.stat().st_size / 1024, 1),
                        "type": "image" if f.suffix.lower() in (".png",".jpg",".jpeg") else
                                "pdf" if f.suffix.lower() == ".pdf" else "file",
                    })
    return JSONResponse({"files": files})


@app.post("/api/run/{agent_key}")
async def run_agent(agent_key: str, body: dict):
    if agent_key not in AGENT_CLASSES:
        return JSONResponse({"error": f"Unknown agent: {agent_key}"}, status_code=404)
    task = body.get("task", "").strip()
    if not task:
        return JSONResponse({"error": "task is required"}, status_code=400)
    threading.Thread(target=_run_task, args=(agent_key, task), daemon=True).start()
    return JSONResponse({"status": "started", "agent": agent_key})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    await ws.send_text(json.dumps({
        "type": "init", "agents": list(AGENT_CLASSES.keys()), "states": agent_states,
    }))
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "run":
                key  = msg.get("agent", "")
                task = msg.get("task", "").strip()
                if key and task:
                    threading.Thread(target=_run_task, args=(key, task), daemon=True).start()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import time, webbrowser, uvicorn
    print("\n" + "=" * 60)
    print("  OnBrandCraftz Town — Starting...")
    print("  Open: http://localhost:8080")
    print("=" * 60 + "\n")
    threading.Thread(target=lambda: (time.sleep(1.5), webbrowser.open("http://localhost:8080")), daemon=True).start()
    uvicorn.run("town_app.server:app", host="0.0.0.0", port=8080, reload=False)
