"""
OnBrandCraftz Town — Real-time Agent Visualization Server
"""

import asyncio
import json
import os
import queue
import shutil
import smtplib
import subprocess
import sys
import tempfile
import threading
from contextlib import asynccontextmanager
from datetime import datetime, date
from pathlib import Path
from typing import Set

sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env before anything else so all os.getenv() calls see the keys
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, File, Form, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Paths ──────────────────────────────────────────────────────────────────────
STATIC_DIR   = Path(__file__).parent / "static"
DATA_DIR     = Path(__file__).parent.parent / "data"
REPO_ROOT    = Path(__file__).parent.parent
HISTORY_FILE = DATA_DIR / "task_history.json"
SCHEDULE_FILE= DATA_DIR / "schedule.json"
REFS_DIR     = DATA_DIR / "design_references"
REFS_META    = DATA_DIR / "design_refs_meta.json"
IDEAS_FILE          = DATA_DIR / "ideas.json"
PIPELINE_BOARD_FILE = DATA_DIR / "product_pipeline.json"
CHAINS_FILE         = DATA_DIR / "automation_chains.json"
ORDERS_SEEN_FILE    = DATA_DIR / "orders_seen.json"

# ── Notification system ────────────────────────────────────────────────────────
_notifications: list = []
_notif_lock = threading.Lock()

def _add_notification(notif_type: str, title: str, body: str = "", icon: str = "🔔"):
    with _notif_lock:
        entry = {
            "id": f"notif_{int(datetime.utcnow().timestamp()*1000)}",
            "type": notif_type,
            "title": title,
            "body": body,
            "icon": icon,
            "ts": datetime.utcnow().isoformat() + "Z",
            "read": False,
        }
        _notifications.insert(0, entry)
        _notifications[:] = _notifications[:100]
    try:
        asyncio.run_coroutine_threadsafe(
            manager.broadcast(json.dumps({"type": "notification", "notif": entry})),
            _event_loop,
        )
    except Exception:
        pass

# ── Auto-update state ──────────────────────────────────────────────────────────
_update_lock   = threading.Lock()
_update_state  = {
    "last_pull":   None,   # ISO timestamp
    "last_result": "never_checked",  # "up_to_date" | "updated" | "error" | "never_checked"
    "last_message": "",
    "pulling": False,
}

def _git_pull() -> dict:
    """Run git pull --ff-only and return result dict."""
    with _update_lock:
        _update_state["pulling"] = True
    try:
        result = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        now = datetime.utcnow().isoformat() + "Z"
        stdout = result.stdout.strip()
        if result.returncode != 0:
            state = "error"
            msg   = result.stderr.strip() or stdout or "git pull failed"
        elif "Already up to date" in stdout:
            state = "up_to_date"
            msg   = stdout
        else:
            state = "updated"
            msg   = stdout
        with _update_lock:
            _update_state.update({"last_pull": now, "last_result": state, "last_message": msg, "pulling": False})
        return {"result": state, "message": msg, "timestamp": now}
    except Exception as exc:
        now = datetime.utcnow().isoformat() + "Z"
        msg = str(exc)
        with _update_lock:
            _update_state.update({"last_pull": now, "last_result": "error", "last_message": msg, "pulling": False})
        return {"result": "error", "message": msg, "timestamp": now}

def _git_pull_job():
    _git_pull()

def _poll_orders():
    """Poll Etsy for new unshipped paid orders every 2 min. Auto-trigger delivery agent."""
    access_token = os.getenv("ETSY_ACCESS_TOKEN", "").strip()
    shop_id      = os.getenv("ETSY_SHOP_ID", "").strip()
    client_id    = os.getenv("ETSY_CLIENT_ID", "").strip()
    if not access_token or not shop_id:
        return
    try:
        import urllib.request as _ur
        url = (
            f"https://openapi.etsy.com/v3/application/shops/{shop_id}/receipts"
            f"?was_paid=true&was_shipped=false&limit=25"
        )
        req = _ur.Request(url, headers={
            "x-api-key": client_id,
            "Authorization": f"Bearer {access_token}",
        })
        with _ur.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
        orders = data.get("results", [])
        seen: set = set()
        try:
            if ORDERS_SEEN_FILE.exists():
                seen = set(json.loads(ORDERS_SEEN_FILE.read_text()))
        except Exception:
            pass
        new_orders = [o for o in orders if str(o.get("receipt_id", "")) not in seen]
        if new_orders:
            for order in new_orders:
                oid   = str(order.get("receipt_id", ""))
                buyer = order.get("name", "Customer")
                cents = order.get("grandtotal", {}).get("amount", 0)
                total = cents / 100.0
                seen.add(oid)
                task  = (
                    f"Process new Etsy order #{oid} from {buyer} (${total:.2f}). "
                    f"Send any digital files, confirm payment, update order status."
                )
                _enqueue_task("delivery", task, f"Auto: Order #{oid}")
                try:
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast(json.dumps({
                            "type": "new_order",
                            "order": {"id": oid, "buyer": buyer, "total": total},
                        })),
                        _event_loop,
                    )
                except Exception:
                    pass
                _add_notification("new_order", f"New Order #{oid}", f"{buyer} — ${total:.2f}", "🛒")
            ORDERS_SEEN_FILE.write_text(json.dumps(list(seen)))
    except Exception:
        pass

# ── Task history ───────────────────────────────────────────────────────────────

_history_lock = threading.Lock()

def _load_history() -> list:
    try:
        if HISTORY_FILE.exists():
            return json.loads(HISTORY_FILE.read_text())
    except Exception:
        pass
    return []

def _save_history_entry(entry: dict):
    with _history_lock:
        history = _load_history()
        history.insert(0, entry)
        history = history[:500]          # cap at 500 entries
        HISTORY_FILE.write_text(json.dumps(history, indent=2))

# ── Task queue ─────────────────────────────────────────────────────────────────
# CEO and pipeline tasks queue sequentially so they don't race each other.

_task_queue: queue.Queue = queue.Queue()
_queue_worker_started = False

def _queue_worker():
    while True:
        key, task, scheduled_label = _task_queue.get()
        try:
            if scheduled_label:
                _emit("ceo", "scheduled", f"⏰ Scheduled: {scheduled_label}")
            _run_task(key, task)
        finally:
            _task_queue.task_done()

def _enqueue_task(key: str, task: str, scheduled_label: str = ""):
    global _queue_worker_started
    if not _queue_worker_started:
        t = threading.Thread(target=_queue_worker, daemon=True)
        t.start()
        _queue_worker_started = True
    _task_queue.put((key, task, scheduled_label))

# ── Scheduler ──────────────────────────────────────────────────────────────────

# ── Automation chains ─────────────────────────────────────────────────────────

DEFAULT_CHAINS = [
    {
        "id": "art_to_qc",
        "label": "Art → QC Review",
        "enabled": True,
        "trigger_agent": "art",
        "trigger_status": "done",
        "action_agent": "qc",
        "action_task": "Review the most recently created digital product from the art agent. Check image quality, dimensions, title and description. Approve or reject with detailed feedback.",
    },
    {
        "id": "listing_to_social",
        "label": "Listing → Pinterest Pin",
        "enabled": True,
        "trigger_agent": "listing",
        "trigger_status": "done",
        "action_agent": "social",
        "action_task": "Create and schedule a Pinterest pin for the most recently published Etsy listing. Use the product title and keywords from the listing for the pin description and board selection.",
    },
    {
        "id": "qc_to_listing",
        "label": "QC Approved → Auto-List",
        "enabled": False,
        "trigger_agent": "qc",
        "trigger_status": "done",
        "action_agent": "listing",
        "action_task": "Create an optimized Etsy listing for the most recently QC-approved digital product. Apply full SEO: optimized title, 13 tags, detailed description.",
    },
    {
        "id": "analytics_to_ideas",
        "label": "Analytics → Idea Suggestions",
        "enabled": True,
        "trigger_agent": "analytics",
        "trigger_status": "done",
        "action_agent": "trend",
        "action_task": "Based on the latest analytics report, identify 2-3 product or marketing ideas that could improve performance. Submit the best one using the submit_idea tool.",
    },
]

def _load_chains() -> list:
    try:
        if CHAINS_FILE.exists():
            return json.loads(CHAINS_FILE.read_text())
    except Exception:
        pass
    CHAINS_FILE.write_text(json.dumps(DEFAULT_CHAINS, indent=2))
    return DEFAULT_CHAINS[:]

def _fire_chains(agent_key: str, status: str):
    chains = _load_chains()
    for chain in chains:
        if chain.get("enabled") and chain.get("trigger_agent") == agent_key and chain.get("trigger_status") == status:
            _enqueue_task(chain["action_agent"], chain["action_task"], f"Auto-chain: {chain['label']}")
            _add_notification("chain_fired", f"Auto: {chain['label']}", f"{chain['action_agent']} triggered automatically", "⛓️")

DEFAULT_SCHEDULES = [
    {
        "id":      "morning_briefing",
        "label":   "Morning Briefing",
        "agent":   "ceo",
        "task":    "Run the daily morning briefing: delegate to Analytics Agent for a revenue summary, Sales Agent for shipping queue check, and Customer Service Agent for unread messages. Summarize findings and flag any urgent issues.",
        "cron":    "0 9 * * 1-5",
        "enabled": True,
    },
    {
        "id":      "competitor_intel",
        "label":   "Weekly Competitor Intel",
        "agent":   "intel",
        "task":    "Run weekly competitor intelligence: research top competitors for 3D printed home decor and hand painted wood items on Etsy. Identify their best-selling products, pricing, and keywords. Save all findings to the knowledge base.",
        "cron":    "0 8 * * 0",
        "enabled": True,
    },
    {
        "id":      "listing_audit",
        "label":   "Weekly Listing Audit",
        "agent":   "product",
        "task":    "Run a full SEO audit of all listings using bulk_seo_audit. For each listing scoring below 70, generate improvement suggestions. Update the worst 3 listings with improved titles and tags. Save insights to knowledge base.",
        "cron":    "0 9 * * 1",
        "enabled": True,
    },
    {
        "id":      "analytics_weekly",
        "label":   "Weekly Analytics Deep Dive",
        "agent":   "analytics",
        "task":    "Run weekly deep-dive analytics: per-listing profitability table, traffic sources, conversion funnel, best/worst categories. Compare against 30-day revenue targets. Log all metrics to knowledge base. Provide 3 specific revenue-growing recommendations.",
        "cron":    "0 10 * * 0",
        "enabled": True,
    },
]

_scheduler: BackgroundScheduler | None = None


def _load_schedules() -> list:
    try:
        if SCHEDULE_FILE.exists():
            return json.loads(SCHEDULE_FILE.read_text())
    except Exception:
        pass
    SCHEDULE_FILE.write_text(json.dumps(DEFAULT_SCHEDULES, indent=2))
    return DEFAULT_SCHEDULES


def _save_schedules(schedules: list):
    SCHEDULE_FILE.write_text(json.dumps(schedules, indent=2))


def _start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="America/New_York")
    schedules = _load_schedules()
    for s in schedules:
        if s.get("enabled"):
            _register_job(s)
    # Auto-update: pull from git every 10 minutes
    _scheduler.add_job(
        func             = _git_pull_job,
        trigger          = "interval",
        minutes          = 10,
        id               = "_auto_git_pull",
        replace_existing = True,
    )
    # Order polling: every 2 minutes
    _scheduler.add_job(
        func             = _poll_orders,
        trigger          = "interval",
        minutes          = 2,
        id               = "_order_poll",
        replace_existing = True,
    )
    _scheduler.start()


def _safe_enqueue(key, task, label):
    try:
        _enqueue_task(key, task, label)
    except Exception as exc:
        import logging
        logging.getLogger("scheduler").error(f"Scheduled job failed to enqueue [{label}]: {exc}", exc_info=True)


def _register_job(s: dict):
    if _scheduler is None:
        return
    try:
        _scheduler.add_job(
            func    = _safe_enqueue,
            trigger = CronTrigger.from_crontab(s["cron"]),
            args    = [s["agent"], s["task"], s["label"]],
            id      = s["id"],
            replace_existing = True,
        )
    except Exception as exc:
        print(f"[scheduler] failed to register {s['id']}: {exc}")


# ── Lifespan ───────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _event_loop
    _event_loop = asyncio.get_running_loop()
    _start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)


app = FastAPI(title="OnBrandCraftz Town", lifespan=lifespan)

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


manager     = ConnectionManager()
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
    "trend": "TrendForecastingAgent", "retention": "CustomerRetentionAgent",
    "tax": "TaxComplianceAgent", "returns": "ReturnsAgent",
    "supply": "SupplyChainAgent", "email": "EmailMarketingAgent",
    "abt": "ABTestingAgent", "api": "APIConnectionsAgent",
    "coordinator": "WorkflowCoordinatorAgent",
}


def _build_agent(key: str):
    import agents as ag
    cls = getattr(ag, AGENT_CLASSES.get(key, ""), None)
    return cls() if cls else None

# ── Pipeline routing ───────────────────────────────────────────────────────────

_PIPELINE_AGENTS = {"brand", "art", "qc", "listing", "store", "marketing", "finance", "analytics"}

_PIPELINE_KEYWORDS = {
    "create", "launch", "new product", "new listing", "design a", "design the",
    "make a", "make the", "build a", "generate a", "generate the", "produce a",
    "develop a", "write a listing", "publish", "add to etsy", "add a listing",
    "start a new", "plan a new", "full pipeline", "full process",
}

_QUERY_PREFIXES = {
    "get", "list", "show", "check", "what", "how", "report", "status",
    "summary", "analyze", "review", "audit", "find", "search", "give",
    "tell", "explain", "describe", "calculate", "run", "pull",
}


def _should_route_to_ceo(agent_key: str, task: str) -> bool:
    if agent_key in ("ceo", "hall"):
        return False
    if agent_key not in _PIPELINE_AGENTS:
        return False
    first_word = task.strip().lower().split()[0] if task.strip() else ""
    if first_word in _QUERY_PREFIXES:
        return False
    return any(kw in task.lower() for kw in _PIPELINE_KEYWORDS)

# ── Pipeline stage tracking ────────────────────────────────────────────────────

PIPELINE_STAGES = ["art", "qc", "brand", "marketing", "finance", "listing"]
_active_pipeline: dict = {}   # {"stages": [...], "current": idx, "parent": "ceo"}
_pipeline_lock = threading.Lock()


def _pipeline_start(parent_key: str):
    with _pipeline_lock:
        _active_pipeline.clear()
        _active_pipeline.update({"stages": PIPELINE_STAGES[:], "completed": [], "current": None, "parent": parent_key})
    _emit(parent_key, "pipeline_start", "Pipeline started", {"stages": PIPELINE_STAGES})


def _pipeline_step(stage_key: str):
    with _pipeline_lock:
        if _active_pipeline:
            _active_pipeline["current"] = stage_key
            if stage_key not in _active_pipeline.get("completed", []):
                pass
    _emit(_active_pipeline.get("parent", "ceo"), "pipeline_step", f"Stage: {stage_key}", {"stage": stage_key})


def _pipeline_complete_step(stage_key: str):
    with _pipeline_lock:
        if _active_pipeline:
            completed = _active_pipeline.setdefault("completed", [])
            if stage_key not in completed:
                completed.append(stage_key)
    _emit(_active_pipeline.get("parent", "ceo"), "pipeline_step_done", f"Done: {stage_key}",
          {"stage": stage_key, "completed": _active_pipeline.get("completed", [])})

# ── Sub-agent runner ───────────────────────────────────────────────────────────

def _run_sub_agent_observable(target_key: str, task: str) -> str:
    if target_key in PIPELINE_STAGES:
        _pipeline_step(target_key)

    agent_states[target_key] = {"status": "running", "task": task, "started": datetime.now().isoformat()}
    _emit(target_key, "start", task[:80])
    started = datetime.now()
    try:
        sub = _build_agent(target_key)
        if sub is None:
            return f"Error: no agent registered for key '{target_key}'"
        sub = _make_observable(sub, target_key)
        result = sub.run(task)
        duration = round((datetime.now() - started).total_seconds())
        agent_states[target_key] = {"status": "idle", "task": task, "last_result": result}
        _emit(target_key, "done", "Complete ✓", {"result": result[:2000]})
        _fire_chains(target_key, "done")
        if target_key in PIPELINE_STAGES:
            _pipeline_complete_step(target_key)
        _save_history_entry({
            "agent": target_key, "task": task[:200], "status": "done",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": result[:300], "triggered_by": "pipeline",
        })
        return result
    except Exception as exc:
        duration = round((datetime.now() - started).total_seconds())
        agent_states[target_key] = {"status": "error", "task": task, "error": str(exc)}
        _emit(target_key, "error", f"Error: {str(exc)[:200]}")
        _save_history_entry({
            "agent": target_key, "task": task[:200], "status": "error",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": str(exc)[:300], "triggered_by": "pipeline",
        })
        return f"[{target_key} error] {exc}"

# ── Observable wrapper ─────────────────────────────────────────────────────────

def _make_observable(agent, key: str):
    original_call_api  = agent._call_api
    original_dispatch  = agent._dispatch_tool

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
            task = tool_input.get("task", "")
            _emit(key, "delegation", f"Delegating → {target_key}", {"to": target_key, "from": key})
            # Start pipeline tracking if CEO is kicking off pipeline agents
            if key == "ceo" and target_key == "art" and not _active_pipeline:
                _pipeline_start("ceo")
            return _run_sub_agent_observable(target_key, task)

        _emit(key, "tool_call", f"→ {tool_name}")
        result = original_dispatch(tool_name, tool_input)

        result_str = str(result)
        file_path  = None
        for ext in (".png", ".jpg", ".jpeg", ".pdf", ".svg"):
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

    agent._call_api      = patched_call_api
    agent._dispatch_tool = patched_dispatch
    return agent

# ── Task runner ────────────────────────────────────────────────────────────────

def _run_task(key: str, task: str):
    if _should_route_to_ceo(key, task):
        _emit(key, "routed", "Routing to CEO for full pipeline…", {"to": "ceo", "from": key})
        agent_name = AGENT_CLASSES.get(key, key)
        task = (
            f"Task submitted directly to {agent_name}: \"{task}\"\n\n"
            f"Orchestrate the appropriate agents in the correct order to complete this. "
            f"Follow the full pre-listing pipeline (Art → QC → Brand → Marketing → "
            f"Financial → Listing → CEO approval) as required."
        )
        key = "ceo"

    started = datetime.now()
    agent_states[key] = {"status": "running", "task": task, "started": started.isoformat()}
    _emit(key, "start", task[:80])
    try:
        agent = _build_agent(key)
        if agent is None:
            raise ValueError(f"Unknown agent: {key}")
        agent  = _make_observable(agent, key)
        result = agent.run(task)
        duration = round((datetime.now() - started).total_seconds())
        agent_states[key] = {"status": "idle", "task": task, "last_result": result}
        _emit(key, "done", "Complete ✓", {"result": result[:2000]})
        _fire_chains(key, "done")
        if key in {"listing", "qc", "sales", "delivery", "ceo"}:
            _add_notification("agent_done", f"{key.title()} completed", task[:80], "✅")
        _save_history_entry({
            "agent": key, "task": task[:200], "status": "done",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": result[:300], "triggered_by": "manual",
        })
        _active_pipeline.clear()
    except Exception as exc:
        duration = round((datetime.now() - started).total_seconds())
        agent_states[key] = {"status": "error", "task": task, "error": str(exc)}
        _emit(key, "error", f"Error: {str(exc)[:300]}")
        _save_history_entry({
            "agent": key, "task": task[:200], "status": "error",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": str(exc)[:300], "triggered_by": "manual",
        })
        _active_pipeline.clear()

# ── File helpers ───────────────────────────────────────────────────────────────

PRODUCT_FOLDERS = [
    {"key": "art_prints",    "name": "Art Prints",    "icon": "🖼️", "path": "digital_products/art_prints"},
    {"key": "wall_art",      "name": "Wall Art",      "icon": "🎨", "path": "digital_products/wall_art"},
    {"key": "planners",      "name": "Planners",      "icon": "📋", "path": "digital_products/planners"},
    {"key": "svg_files",     "name": "SVG / Clipart", "icon": "✂️", "path": "digital_products/svg_files"},
    {"key": "clipart",       "name": "Clipart Packs", "icon": "🎭", "path": "digital_products/clipart"},
    {"key": "bundles",       "name": "Bundles",       "icon": "📦", "path": "digital_products/bundles"},
    {"key": "product_files", "name": "Other Products","icon": "📁", "path": "digital_products/product_files"},
    {"key": "brand_assets",  "name": "Brand Assets",  "icon": "💎", "path": "brand/assets"},
    {"key": "logos",         "name": "Logos",         "icon": "🏷️", "path": "brand/logos"},
    {"key": "mockups",       "name": "Mockups",       "icon": "🖼️", "path": "brand/mockups"},
]

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


def _scan_folder(rel_path: str) -> list:
    d = DATA_DIR / rel_path
    if not d.exists():
        return []
    files = []
    for f in sorted(d.iterdir()):
        if f.is_file() and f.name != ".gitkeep":
            stat = f.stat()
            ext  = f.suffix.lower()
            files.append({
                "name":    f.name,
                "path":    f"data/{rel_path}/{f.name}",
                "size_kb": round(stat.st_size / 1024, 1),
                "type":    "image" if ext in _IMAGE_EXTS else "pdf" if ext == ".pdf" else "file",
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M"),
            })
    return files

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(STATIC_DIR / "favicon.png", media_type="image/png")


@app.get("/api/agents")
async def list_agents():
    return JSONResponse({"agents": list(AGENT_CLASSES.keys()), "states": agent_states})


@app.get("/api/config")
async def get_config():
    def is_set(var):
        v = os.getenv(var, "")
        return bool(v and not v.startswith("your_"))
    return JSONResponse({
        "anthropic":  is_set("ANTHROPIC_API_KEY"),
        "openai":     is_set("OPENAI_API_KEY"),
        "smtp":       is_set("SMTP_USER") and is_set("SMTP_PASSWORD"),
        "etsy_api":   is_set("ETSY_API_KEY"),
        "etsy_oauth": is_set("ETSY_ACCESS_TOKEN"),
        "pinterest":  is_set("PINTEREST_ACCESS_TOKEN"),
    })


@app.get("/data/{path:path}")
async def serve_data_file(path: str):
    target = (DATA_DIR / path).resolve()
    if DATA_DIR.resolve() not in target.parents:
        return JSONResponse({"error": "forbidden"}, status_code=403)
    if target.exists() and target.is_file():
        return FileResponse(str(target))
    return JSONResponse({"error": "not found"}, status_code=404)


@app.get("/api/files")
async def list_files():
    folders = []
    total   = 0
    for fd in PRODUCT_FOLDERS:
        files = _scan_folder(fd["path"])
        total += len(files)
        folders.append({"key": fd["key"], "name": fd["name"], "icon": fd["icon"],
                         "path": fd["path"], "files": files})
    return JSONResponse({"folders": folders, "total": total})


@app.get("/api/task-history")
async def get_task_history(limit: int = 100):
    history = _load_history()
    return JSONResponse({"history": history[:limit], "total": len(history)})


@app.get("/api/stats")
async def get_stats():
    """Revenue stats and 30-day goal progress for the Goals dashboard."""
    try:
        from tools.data_store import DataStore
        store  = DataStore()
        rev    = store.analytics.get("revenue", {})
        shop   = store.shop
        today  = datetime.now()
        # Estimate shop age from first order date or default to day 1
        day_num = 1
        orders = getattr(store, "orders", [])
        if orders:
            dates = [o.get("order_date", "") for o in orders if o.get("order_date")]
            if dates:
                from datetime import date
                earliest = min(dates)
                try:
                    d = datetime.strptime(earliest, "%Y-%m-%d")
                    day_num = max(1, (today - d).days + 1)
                except Exception:
                    pass

        week_rev  = float(rev.get("this_week", 0))
        month_rev = float(rev.get("this_month", 0))
        daily_rate = week_rev / 7 if week_rev else 0

        milestones = [
            {"day": 7,  "target": 50,   "label": "First $50"},
            {"day": 14, "target": 150,  "label": "$150 milestone"},
            {"day": 21, "target": 400,  "label": "$400 milestone"},
            {"day": 30, "target": 800,  "label": "$800/mo run-rate"},
        ]
        for m in milestones:
            m["achieved"] = month_rev >= m["target"]
            m["current"]  = round(min(month_rev, m["target"]), 2)
            m["pct"]      = round(min(100, (month_rev / m["target"]) * 100), 1) if m["target"] else 0

        return JSONResponse({
            "day_num":      day_num,
            "month_revenue":month_rev,
            "week_revenue": week_rev,
            "daily_rate":   round(daily_rate, 2),
            "total_sales":  shop.get("total_sales", 0),
            "total_listings": len(getattr(store, "listings", [])),
            "active_listings": len([l for l in getattr(store, "listings", []) if l.get("status") == "active"]),
            "milestones":   milestones,
            "on_track":     daily_rate * 30 >= 800 if daily_rate else False,
        })
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/api/schedule")
async def get_schedule():
    return JSONResponse({"schedules": _load_schedules()})


@app.post("/api/schedule/{job_id}/toggle")
async def toggle_schedule(job_id: str):
    schedules = _load_schedules()
    for s in schedules:
        if s["id"] == job_id:
            s["enabled"] = not s.get("enabled", True)
            if _scheduler:
                if s["enabled"]:
                    _register_job(s)
                else:
                    try:
                        _scheduler.remove_job(job_id)
                    except Exception:
                        pass
            _save_schedules(schedules)
            return JSONResponse({"id": job_id, "enabled": s["enabled"]})
    return JSONResponse({"error": "job not found"}, status_code=404)


@app.post("/api/schedule/{job_id}/run-now")
async def run_scheduled_now(job_id: str):
    schedules = _load_schedules()
    for s in schedules:
        if s["id"] == job_id:
            _enqueue_task(s["agent"], s["task"], s["label"] + " (manual)")
            return JSONResponse({"status": "queued", "id": job_id})
    return JSONResponse({"error": "job not found"}, status_code=404)


@app.get("/api/pipeline")
async def get_pipeline():
    with _pipeline_lock:
        return JSONResponse(dict(_active_pipeline))


@app.post("/api/test-email")
async def test_email(body: dict):
    to = body.get("to") or os.getenv("SMTP_USER", "")
    if not to:
        return JSONResponse({"error": "No recipient address — set SMTP_USER or pass 'to' in the request body."}, status_code=400)

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    subject   = "OnBrandCraftz — Email Test"
    body_html = (
        "<p>This is a test email from your OnBrandCraftz automation hub. "
        "If you received this, your email delivery is working correctly.</p>"
    )

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = smtp_user
    msg["To"]      = to
    msg.attach(MIMEText(body_html, "html"))

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to], msg.as_string())
        return JSONResponse({"success": True, "sent_to": to})
    except Exception as exc:
        return JSONResponse({"error": str(exc)})


@app.get("/api/etsy-status")
async def etsy_status():
    def _is_set(var: str) -> bool:
        v = os.getenv(var, "")
        return bool(v and not v.lower().startswith("your_"))

    api_key_set      = _is_set("ETSY_API_KEY")
    oauth_configured = _is_set("ETSY_ACCESS_TOKEN")
    shop_id          = os.getenv("ETSY_SHOP_ID", "")

    if api_key_set and oauth_configured:
        status    = "fully_connected"
        next_step = "All Etsy credentials are configured. You're ready to publish and sync orders."
    elif api_key_set:
        status    = "api_key_only"
        next_step = "Run python tools/etsy_oauth.py to enable publishing and order sync."
    else:
        status    = "not_configured"
        next_step = "Add ETSY_API_KEY (and optionally ETSY_ACCESS_TOKEN) to your .env file, then restart the server."

    return JSONResponse({
        "api_key_set":      api_key_set,
        "oauth_configured": oauth_configured,
        "shop_id":          shop_id,
        "status":           status,
        "next_step":        next_step,
    })


@app.get("/api/physical-approvals")
async def get_physical_approvals():
    shop_data_path = DATA_DIR / "shop_data.json"
    try:
        shop_data = json.loads(shop_data_path.read_text()) if shop_data_path.exists() else {}
    except Exception:
        shop_data = {}

    digital_types = {"digital_art", "planner", "clipart", "digital", "download"}
    orders = shop_data.get("orders", [])
    pending = [
        o for o in orders
        if o.get("product_type", "") not in digital_types or o.get("requires_human_approval", False)
    ]

    print_queue = shop_data.get("print_queue", [])
    queued_unapproved = [
        item for item in print_queue
        if item.get("status") == "queued" and not item.get("human_approved", False)
    ]

    all_pending = pending + queued_unapproved
    return JSONResponse({"pending_approvals": all_pending, "count": len(all_pending)})


@app.post("/api/approve-physical/{order_id}")
async def approve_physical_order(order_id: str):
    shop_data_path = DATA_DIR / "shop_data.json"
    try:
        shop_data = json.loads(shop_data_path.read_text()) if shop_data_path.exists() else {}
    except Exception:
        shop_data = {}

    orders = shop_data.get("orders", [])
    found = False
    for o in orders:
        if str(o.get("id", "")) == order_id or str(o.get("order_id", "")) == order_id:
            o["human_approved"] = True
            o["approved_at"] = str(date.today())
            found = True
            break

    if not found:
        return JSONResponse({"error": f"Order {order_id} not found"}, status_code=404)

    shop_data_path.write_text(json.dumps(shop_data, indent=2))
    return JSONResponse({"approved": True, "order_id": order_id})


_ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/gif", "image/webp", "image/bmp"}
_ALLOWED_IMAGE_EXTS  = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@app.post("/api/convert-svg")
async def convert_to_svg(
    file: UploadFile = File(...),
    colormode:        str = "color",
    filter_speckle:   int = 4,
    color_precision:  int = 6,
    layer_difference: int = 16,
    path_precision:   int = 8,
):
    import vtracer
    ext = Path(file.filename or "").suffix.lower()
    if ext not in _ALLOWED_IMAGE_EXTS:
        return JSONResponse({"error": f"Unsupported file type: {ext}"}, status_code=400)

    stem    = Path(file.filename).stem
    out_dir = DATA_DIR / "digital_products" / "svg_files"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_path = out_dir / f"{stem}.svg"
    counter  = 1
    while out_path.exists():
        out_path = out_dir / f"{stem}_{counter}.svg"
        counter += 1

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        vtracer.convert_image_to_svg_py(
            image_path      = tmp_path,
            out_path        = str(out_path),
            colormode       = colormode,
            filter_speckle  = filter_speckle,
            color_precision = color_precision,
            layer_difference= layer_difference,
            path_precision  = path_precision,
        )
    finally:
        os.unlink(tmp_path)

    rel = f"data/digital_products/svg_files/{out_path.name}"
    return JSONResponse({
        "status":   "ok",
        "filename": out_path.name,
        "path":     rel,
        "size_kb":  round(out_path.stat().st_size / 1024, 1),
    })


# ── Design References ──────────────────────────────────────────────────────────

_ALLOWED_REF_EXTS  = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}

def _load_refs_meta() -> list:
    try:
        if REFS_META.exists():
            return json.loads(REFS_META.read_text())
    except Exception:
        pass
    return []

def _save_refs_meta(meta: list):
    REFS_META.write_text(json.dumps(meta, indent=2))


@app.post("/api/upload-reference")
async def upload_reference(file: UploadFile = File(...), description: str = Form("")):
    REFS_DIR.mkdir(parents=True, exist_ok=True)
    ext = Path(file.filename or "upload").suffix.lower()
    if ext not in _ALLOWED_REF_EXTS:
        return JSONResponse({"error": f"Unsupported file type: {ext}"}, status_code=400)
    stem = Path(file.filename or "ref").stem[:40]
    out_path = REFS_DIR / f"{stem}{ext}"
    counter = 1
    while out_path.exists():
        out_path = REFS_DIR / f"{stem}_{counter}{ext}"
        counter += 1
    contents = await file.read()
    out_path.write_bytes(contents)
    ref_id = f"{out_path.stem}_{int(datetime.utcnow().timestamp())}"
    meta = _load_refs_meta()
    entry = {
        "id": ref_id,
        "filename": out_path.name,
        "path": f"data/design_references/{out_path.name}",
        "description": description,
        "uploaded_at": datetime.utcnow().isoformat() + "Z",
        "size_kb": round(len(contents) / 1024, 1),
    }
    meta.append(entry)
    _save_refs_meta(meta)
    return JSONResponse(entry)


@app.get("/api/design-references")
async def list_design_references():
    return JSONResponse(_load_refs_meta())


@app.delete("/api/design-references/{ref_id}")
async def delete_design_reference(ref_id: str):
    meta = _load_refs_meta()
    entry = next((m for m in meta if m["id"] == ref_id), None)
    if not entry:
        return JSONResponse({"error": "Not found"}, status_code=404)
    file_path = REFS_DIR / entry["filename"]
    if file_path.exists():
        file_path.unlink()
    _save_refs_meta([m for m in meta if m["id"] != ref_id])
    return JSONResponse({"deleted": True, "id": ref_id})


@app.get("/data/design_references/{filename}")
async def serve_design_reference(filename: str):
    path = REFS_DIR / filename
    if not path.exists():
        return JSONResponse({"error": "Not found"}, status_code=404)
    return FileResponse(str(path))


# ── Ideas Board ────────────────────────────────────────────────────────────────

def _load_ideas() -> list:
    try:
        if IDEAS_FILE.exists():
            return json.loads(IDEAS_FILE.read_text())
    except Exception:
        pass
    return []

def _save_ideas(ideas: list):
    IDEAS_FILE.write_text(json.dumps(ideas, indent=2))


@app.post("/api/ideas")
async def submit_idea(body: dict):
    ideas = _load_ideas()
    idea_id = f"idea_{int(datetime.utcnow().timestamp() * 1000)}"
    entry = {
        "id": idea_id,
        "agent": (body.get("agent") or "unknown")[:40],
        "title": (body.get("title") or "Untitled Idea")[:120],
        "description": (body.get("description") or "")[:800],
        "category": (body.get("category") or "general")[:40],
        "submitted_at": datetime.utcnow().isoformat() + "Z",
        "status": "pending",
    }
    ideas.append(entry)
    _save_ideas(ideas)
    await manager.broadcast(json.dumps({"type": "new_idea", "idea": entry}))
    return JSONResponse(entry, status_code=201)


@app.get("/api/ideas")
async def list_ideas():
    return JSONResponse(_load_ideas())


@app.delete("/api/ideas/{idea_id}")
async def delete_idea(idea_id: str):
    ideas = _load_ideas()
    if not any(i["id"] == idea_id for i in ideas):
        return JSONResponse({"error": "Not found"}, status_code=404)
    _save_ideas([i for i in ideas if i["id"] != idea_id])
    return JSONResponse({"deleted": True, "id": idea_id})


@app.post("/api/ideas/brainstorm")
async def start_brainstorm():
    ideas = _load_ideas()
    pending = [i for i in ideas if i.get("status") == "pending"]
    if not pending:
        return JSONResponse({"error": "No pending ideas to brainstorm"}, status_code=400)
    lines = []
    for idx, idea in enumerate(pending, 1):
        agent_label = idea["agent"].replace("_", " ").title()
        lines.append(f"{idx}. [{agent_label}] {idea['title']}\n   {idea['description']}")
    task = (
        "BRAINSTORM MEETING — The team has submitted the following ideas for strategic review. "
        "Analyse each one: assess its potential impact, feasibility, and priority. "
        "Give a concrete recommendation (pursue / park / refine) and one next action step.\n\n"
        + "\n\n".join(lines)
    )
    _enqueue_task("ceo", task)
    # Mark all as 'discussed'
    for idea in ideas:
        if idea.get("status") == "pending":
            idea["status"] = "discussed"
    _save_ideas(ideas)
    return JSONResponse({"status": "started", "idea_count": len(pending), "agent": "ceo"})


# ── Quick Stats ────────────────────────────────────────────────────────────────

@app.get("/api/quick-stats")
async def quick_stats():
    from tools.data_store import DataStore
    store = DataStore()
    today = date.today().isoformat()
    month = today[:7]
    orders = store.get("orders", default=[])
    today_rev  = sum(float(o.get("price", 0)) for o in orders if str(o.get("created_at", "")).startswith(today))
    month_rev  = sum(float(o.get("price", 0)) for o in orders if str(o.get("created_at", "")).startswith(month))
    open_cnt   = sum(1 for o in orders if o.get("status") in ("paid", "processing", "open"))
    listings   = store.get("listings", default=[])
    active_cnt = sum(1 for l in listings if l.get("status") == "active")
    running    = sum(1 for s in agent_states.values() if s.get("status") == "running")
    return JSONResponse({
        "today_revenue":  round(today_rev, 2),
        "monthly_revenue": round(month_rev, 2),
        "open_orders":    open_cnt,
        "active_listings": active_cnt,
        "running_agents": running,
        "ts": datetime.utcnow().isoformat() + "Z",
    })


# ── Notifications ──────────────────────────────────────────────────────────────

@app.get("/api/notifications")
async def list_notifications_ep():
    with _notif_lock:
        return JSONResponse(list(_notifications))

@app.post("/api/notifications/read-all")
async def mark_notifications_read():
    with _notif_lock:
        for n in _notifications:
            n["read"] = True
    return JSONResponse({"ok": True})

@app.delete("/api/notifications/{notif_id}")
async def dismiss_notification(notif_id: str):
    with _notif_lock:
        _notifications[:] = [n for n in _notifications if n["id"] != notif_id]
    return JSONResponse({"ok": True})


# ── Product Pipeline Board ─────────────────────────────────────────────────────

def _load_pipeline_board() -> list:
    try:
        if PIPELINE_BOARD_FILE.exists():
            return json.loads(PIPELINE_BOARD_FILE.read_text())
    except Exception:
        pass
    return []

def _save_pipeline_board(items: list):
    PIPELINE_BOARD_FILE.write_text(json.dumps(items, indent=2))

@app.get("/api/product-pipeline")
async def get_product_pipeline():
    return JSONResponse(_load_pipeline_board())

@app.post("/api/product-pipeline")
async def add_pipeline_item(body: dict):
    items = _load_pipeline_board()
    item_id = f"prod_{int(datetime.utcnow().timestamp()*1000)}"
    item = {
        "id": item_id,
        "title": (body.get("title") or "New Product")[:120],
        "type": body.get("type", "digital"),
        "stage": body.get("stage", "concept"),
        "notes": body.get("notes", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    items.append(item)
    _save_pipeline_board(items)
    return JSONResponse(item, status_code=201)

@app.patch("/api/product-pipeline/{item_id}")
async def update_pipeline_item(item_id: str, body: dict):
    items = _load_pipeline_board()
    item = next((i for i in items if i["id"] == item_id), None)
    if not item:
        return JSONResponse({"error": "Not found"}, status_code=404)
    for k in ("title", "type", "stage", "notes"):
        if k in body:
            item[k] = body[k]
    item["updated_at"] = datetime.utcnow().isoformat() + "Z"
    _save_pipeline_board(items)
    return JSONResponse(item)

@app.delete("/api/product-pipeline/{item_id}")
async def delete_pipeline_item(item_id: str):
    items = _load_pipeline_board()
    _save_pipeline_board([i for i in items if i["id"] != item_id])
    return JSONResponse({"ok": True})


# ── Automation Chains ─────────────────────────────────────────────────────────

@app.get("/api/chains")
async def list_chains_ep():
    return JSONResponse(_load_chains())

@app.patch("/api/chains/{chain_id}")
async def update_chain(chain_id: str, body: dict):
    chains = _load_chains()
    chain = next((c for c in chains if c["id"] == chain_id), None)
    if not chain:
        return JSONResponse({"error": "Not found"}, status_code=404)
    if "enabled" in body:
        chain["enabled"] = bool(body["enabled"])
    CHAINS_FILE.write_text(json.dumps(chains, indent=2))
    return JSONResponse(chain)

@app.post("/api/chains")
async def add_chain(body: dict):
    chains = _load_chains()
    chain_id = f"chain_{int(datetime.utcnow().timestamp()*1000)}"
    chain = {
        "id": chain_id,
        "label": (body.get("label") or "Custom Chain")[:80],
        "enabled": bool(body.get("enabled", True)),
        "trigger_agent": body.get("trigger_agent", ""),
        "trigger_status": body.get("trigger_status", "done"),
        "action_agent": body.get("action_agent", ""),
        "action_task": (body.get("action_task") or "")[:400],
    }
    chains.append(chain)
    CHAINS_FILE.write_text(json.dumps(chains, indent=2))
    return JSONResponse(chain, status_code=201)

@app.delete("/api/chains/{chain_id}")
async def delete_chain(chain_id: str):
    chains = _load_chains()
    CHAINS_FILE.write_text(json.dumps([c for c in chains if c["id"] != chain_id], indent=2))
    return JSONResponse({"ok": True})


# ── Product Creator ────────────────────────────────────────────────────────────

@app.post("/api/create-product")
async def create_product(body: dict):
    product_type = (body.get("type") or "digital art").strip()
    style        = (body.get("style") or "").strip()
    keywords     = (body.get("keywords") or "").strip()
    task = (
        f"Create a new {product_type} digital product for the Etsy shop. "
        + (f"Style: {style}. " if style else "")
        + (f"Target keywords: {keywords}. " if keywords else "")
        + "Generate the art concept, create the digital product file, and save it ready for QC review."
    )
    _enqueue_task("art", task, f"Product Creator: {product_type}")
    _add_notification("product_queued", "Product creation started", f"{product_type}" + (f" — {style}" if style else ""), "🎨")
    return JSONResponse({"status": "queued", "agent": "art", "task": task[:200]})


# ── Listing Health ────────────────────────────────────────────────────────────

@app.get("/api/listings/health")
async def listings_health():
    from tools.data_store import DataStore
    store = DataStore()
    listings = store.get("listings", default=[])
    health = []
    for lst in listings:
        views   = int(lst.get("views", 0))
        favs    = int(lst.get("favorited_by", lst.get("favorites", 0)))
        sales   = int(lst.get("quantity_sold", lst.get("sales", 0)))
        conv    = round(sales / views * 100, 1) if views > 0 else 0.0
        score   = min(100, (conv * 10) + min(views / 10, 30) + min(favs * 2, 20))
        health.append({
            "id":          lst.get("listing_id", lst.get("id", "")),
            "title":       (lst.get("title") or "")[:60],
            "price":       lst.get("price", 0),
            "views":       views,
            "favorites":   favs,
            "sales":       sales,
            "conversion":  conv,
            "score":       round(score),
            "status":      lst.get("status", "active"),
            "url":         lst.get("url", ""),
        })
    health.sort(key=lambda x: x["score"])
    return JSONResponse(health)

@app.get("/api/update-status")
async def update_status():
    with _update_lock:
        state = dict(_update_state)
    return JSONResponse(state)


@app.post("/api/apply-update")
async def apply_update():
    if _update_state.get("pulling"):
        return JSONResponse({"error": "Pull already in progress"}, status_code=409)
    threading.Thread(target=_git_pull, daemon=True).start()
    return JSONResponse({"status": "pulling", "message": "Git pull started — server will reload if files changed"})


@app.post("/api/run/{agent_key}")
async def run_agent(agent_key: str, body: dict):
    if agent_key not in AGENT_CLASSES:
        return JSONResponse({"error": f"Unknown agent: {agent_key}"}, status_code=404)
    task = body.get("task", "").strip()
    if not task:
        return JSONResponse({"error": "task is required"}, status_code=400)
    _enqueue_task(agent_key, task)
    return JSONResponse({"status": "queued", "agent": agent_key})


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
                    _enqueue_task(key, task)
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
    threading.Thread(
        target=lambda: (time.sleep(1.5), webbrowser.open("http://localhost:8080")),
        daemon=True,
    ).start()
    uvicorn.run("town_app.server:app", host="0.0.0.0", port=8080, reload=True, reload_dirs=[str(REPO_ROOT)])
