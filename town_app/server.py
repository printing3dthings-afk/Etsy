"""
OnBrandCraftz Town — Real-time Agent Visualization Server

Run with:
    python -m uvicorn town_app.server:app --host 0.0.0.0 --port 8080
Or:
    python town_app/server.py
"""

import asyncio
import json
import os
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="OnBrandCraftz Town")

STATIC_DIR = Path(__file__).parent / "static"

# ── WebSocket connection manager ───────────────────────────────────────────────

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

# Per-agent state visible to the frontend
agent_states: dict[str, dict] = {}


# ── Event emission ─────────────────────────────────────────────────────────────

def _emit(agent_key: str, event: str, message: str, extra: dict | None = None):
    """Thread-safe: schedule a broadcast on the asyncio event loop."""
    if _event_loop is None or _event_loop.is_closed():
        return
    payload = {
        "type": "agent_event",
        "agent": agent_key,
        "event": event,
        "message": message,
        "ts": datetime.now().strftime("%H:%M:%S"),
        "data": extra or {},
    }
    asyncio.run_coroutine_threadsafe(manager.broadcast(payload), _event_loop)


# ── Agent factory ──────────────────────────────────────────────────────────────

AGENT_CLASSES: dict[str, str] = {
    "ceo":      "CEOAgent",
    "brand":    "BrandDesignAgent",
    "art":      "ArtCreationAgent",
    "qc":       "QualityCheckAgent",
    "listing":  "EtsyListingAgent",
    "store":    "StoreManagerAgent",
    "delivery": "SalesProcessorAgent",
    "sales":    "SalesAgent",
    "product":  "ProductAgent",
    "marketing":"MarketingAgent",
    "analytics":"AnalyticsAgent",
    "cs":       "CustomerServiceAgent",
    "social":   "SocialMediaAgent",
    "finance":  "FinancialAgent",
    "print":    "PrintProductionAgent",
    "ads":      "EtsyAdsAgent",
    "intel":    "CompetitorIntelAgent",
    "promos":   "PromotionsAgent",
    "tax":      "TaxComplianceAgent",
    "returns":  "ReturnsAgent",
    "supply":   "SupplyChainAgent",
    "email":    "EmailMarketingAgent",
    "abt":      "ABTestingAgent",
}


def _build_agent(key: str):
    import agents as ag
    cls_name = AGENT_CLASSES.get(key)
    if not cls_name:
        return None
    cls = getattr(ag, cls_name, None)
    return cls() if cls else None


# ── Observable agent wrapper ───────────────────────────────────────────────────

def _make_observable(agent, key: str):
    """Monkey-patch an agent instance to emit real-time events on each step."""
    original_call_api = agent._call_api
    original_execute_tool = agent.execute_tool

    def patched_call_api(messages):
        _emit(key, "thinking", "Thinking…")
        response = original_call_api(messages)
        tool_blocks = [b for b in response.content if getattr(b, "type", "") == "tool_use"]
        if tool_blocks:
            names = ", ".join(b.name for b in tool_blocks)
            _emit(key, "planning", f"Will use: {names}")
        return response

    def patched_execute_tool(tool_name, tool_input):
        _emit(key, "tool_call", f"→ {tool_name}")
        result = original_execute_tool(tool_name, tool_input)
        # Trim result for log display
        snippet = str(result)[:120].replace("\n", " ")
        _emit(key, "tool_result", f"✓ {tool_name}: {snippet}")
        return result

    agent._call_api = patched_call_api
    agent.execute_tool = patched_execute_tool
    return agent


# ── Agent task runner (runs in a thread) ──────────────────────────────────────

def _run_task(key: str, task: str):
    agent_states[key] = {"status": "running", "task": task, "started": datetime.now().isoformat()}
    _emit(key, "start", task[:80])

    try:
        agent = _build_agent(key)
        if agent is None:
            raise ValueError(f"Unknown agent key: {key}")

        agent = _make_observable(agent, key)
        result = agent.run(task)

        agent_states[key] = {"status": "idle", "task": task, "last_result": result}
        _emit(key, "done", "Task complete ✓", {"result": result[:1000]})

    except Exception as exc:
        agent_states[key] = {"status": "error", "task": task, "error": str(exc)}
        _emit(key, "error", f"Error: {str(exc)[:200]}")


# ── FastAPI routes ─────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    global _event_loop
    _event_loop = asyncio.get_running_loop()


@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/agents")
async def list_agents():
    return JSONResponse({"agents": list(AGENT_CLASSES.keys()), "states": agent_states})


@app.post("/api/run/{agent_key}")
async def run_agent(agent_key: str, body: dict):
    if agent_key not in AGENT_CLASSES:
        return JSONResponse({"error": f"Unknown agent: {agent_key}"}, status_code=404)
    task = body.get("task", "").strip()
    if not task:
        return JSONResponse({"error": "task is required"}, status_code=400)
    thread = threading.Thread(target=_run_task, args=(agent_key, task), daemon=True)
    thread.start()
    return JSONResponse({"status": "started", "agent": agent_key, "task": task})


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await manager.connect(ws)
    # Send current state snapshot to the newly connected client
    await ws.send_text(json.dumps({
        "type": "init",
        "agents": list(AGENT_CLASSES.keys()),
        "states": agent_states,
    }))
    try:
        while True:
            raw = await ws.receive_text()
            msg = json.loads(raw)
            if msg.get("type") == "run":
                key = msg.get("agent", "")
                task = msg.get("task", "").strip()
                if key and task:
                    thread = threading.Thread(target=_run_task, args=(key, task), daemon=True)
                    thread.start()
    except WebSocketDisconnect:
        manager.disconnect(ws)
    except Exception:
        manager.disconnect(ws)


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import webbrowser
    import time
    import uvicorn

    print("\n" + "=" * 60)
    print("  OnBrandCraftz Town — Starting...")
    print("  Open: http://localhost:8080")
    print("=" * 60 + "\n")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://localhost:8080")

    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run("town_app.server:app", host="0.0.0.0", port=8080, reload=False)
