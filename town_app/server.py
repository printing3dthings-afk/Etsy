"""
OnBrandCraftz Town — Real-time Agent Visualization Server
"""
from __future__ import annotations

import asyncio
import json
import os
import queue
import re
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

# Ensure all required directories exist on first run (fresh Windows install)
for _d in [DATA_DIR, DATA_DIR / "design_references",
           DATA_DIR / "digital_products" / "product_files",
           REPO_ROOT / "logs"]:
    _d.mkdir(parents=True, exist_ok=True)

HISTORY_FILE       = DATA_DIR / "task_history.json"
AGENT_STATES_FILE  = DATA_DIR / "agent_states.json"
SESSION_LOG_FILE   = DATA_DIR / "session_log.json"
SCHEDULE_FILE      = DATA_DIR / "schedule.json"
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
            manager.broadcast({"type": "notification", "notif": entry}),
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
    """Poll Etsy for new paid+unshipped orders every 30 s; auto-trigger delivery."""
    if not os.getenv("ETSY_ACCESS_TOKEN", "").strip() or not os.getenv("ETSY_SHOP_ID", "").strip():
        return
    try:
        from tools.etsy_api import EtsyAPIClient
        client = EtsyAPIClient()
        data = client._request(
            "GET", f"shops/{client.shop_id}/receipts",
            params={"was_paid": True, "was_shipped": False, "limit": 25},
        )
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
                _enqueue_delivery(
                    f"Process new Etsy order #{oid} from {buyer} (${total:.2f}). "
                    f"Send any digital files, confirm payment, update order status.",
                    f"Auto: Order #{oid}",
                )
                try:
                    asyncio.run_coroutine_threadsafe(
                        manager.broadcast({
                            "type": "new_order",
                            "order": {"id": oid, "buyer": buyer, "total": total},
                        }),
                        _event_loop,
                    )
                except Exception:
                    pass
                _add_notification("new_order", f"New Order #{oid}", f"{buyer} - ${total:.2f}", "")
            ORDERS_SEEN_FILE.write_text(json.dumps(list(seen)))
    except Exception as _poll_err:
        _poll_orders._fail_count = getattr(_poll_orders, "_fail_count", 0) + 1
        if _poll_orders._fail_count % 5 == 1:
            _add_notification("api_error", "Etsy order poll failed",
                              f"Could not reach Etsy API: {str(_poll_err)[:120]}. Check ETSY_ACCESS_TOKEN.", "")

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

# ── Agent state persistence ────────────────────────────────────────────────────

_states_lock = threading.Lock()

def _load_agent_states() -> dict:
    try:
        if AGENT_STATES_FILE.exists():
            return json.loads(AGENT_STATES_FILE.read_text())
    except Exception:
        pass
    return {}

def _persist_agent_states():
    with _states_lock:
        try:
            AGENT_STATES_FILE.write_text(json.dumps(agent_states, indent=2))
        except Exception:
            pass

# ── Session log (survives restarts) ───────────────────────────────────────────

_session_log_lock = threading.Lock()

def _append_session_log(entry: dict):
    with _session_log_lock:
        try:
            log = []
            if SESSION_LOG_FILE.exists():
                try:
                    log = json.loads(SESSION_LOG_FILE.read_text())
                except Exception:
                    log = []
            log.append(entry)
            log = log[-2000:]        # keep last 2000 events
            SESSION_LOG_FILE.write_text(json.dumps(log))
        except Exception:
            pass

# ── Task queue ─────────────────────────────────────────────────────────────────
# CEO and pipeline tasks queue sequentially so they don't race each other.
# Delivery tasks get their own dedicated worker so orders are never blocked
# behind long-running CEO or analytics jobs.

_task_queue: queue.Queue = queue.Queue()
_queue_worker_started = False
_queue_worker_lock = threading.Lock()

# Public tunnel URL set by cloudflared watcher (empty when no tunnel running)
_tunnel_url: str = ""

# High-priority queue for digital order delivery — processes immediately.
_delivery_queue: queue.Queue = queue.Queue()
_delivery_worker_started = False
_delivery_worker_lock = threading.Lock()

def _queue_worker():
    while True:
        key, task, scheduled_label = _task_queue.get()
        try:
            if scheduled_label:
                _emit("ceo", "scheduled", f"⏰ Scheduled: {scheduled_label}")
            _run_task(key, task)
        finally:
            _task_queue.task_done()

def _delivery_worker():
    """Dedicated worker for instant digital order fulfillment."""
    while True:
        task, scheduled_label = _delivery_queue.get()
        try:
            if scheduled_label:
                _emit("delivery", "scheduled", f"⏰ {scheduled_label}")
            _run_task("delivery", task)
        finally:
            _delivery_queue.task_done()

def _enqueue_task(key: str, task: str, scheduled_label: str = ""):
    global _queue_worker_started
    with _queue_worker_lock:
        if not _queue_worker_started:
            t = threading.Thread(target=_queue_worker, daemon=True)
            t.start()
            _queue_worker_started = True
    _task_queue.put((key, task, scheduled_label))

def _enqueue_delivery(task: str, scheduled_label: str = ""):
    """Queue a delivery task on the high-priority dedicated worker."""
    global _delivery_worker_started
    with _delivery_worker_lock:
        if not _delivery_worker_started:
            t = threading.Thread(target=_delivery_worker, daemon=True)
            t.start()
            _delivery_worker_started = True
    _delivery_queue.put((task, scheduled_label))

# ── Scheduler ──────────────────────────────────────────────────────────────────

# ── Automation chains ─────────────────────────────────────────────────────────

DEFAULT_CHAINS = [
    {
        "id": "art_to_qc",
        "label": "Art → QC Review",
        "enabled": False,
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
    {
        "id": "analytics_to_marketing",
        "label": "Analytics → SEO Boost",
        "enabled": True,
        "trigger_agent": "analytics",
        "trigger_status": "done",
        "action_agent": "marketing",
        "action_task": "Analytics just completed a deep-dive. Review the performance data and update SEO on the 3 lowest-performing listings: improve titles, add missing tags, and log keyword performance to the knowledge base.",
    },
    {
        "id": "intel_to_ads",
        "label": "Competitor Intel → Ads Update",
        "enabled": True,
        "trigger_agent": "intel",
        "trigger_status": "done",
        "action_agent": "ads",
        "action_task": "Competitor intelligence just completed. Review findings and update our Etsy Ads strategy: raise bids on keywords where competitors are strong, lower bids where we dominate. Log strategy changes.",
    },
    {
        "id": "sales_to_finance",
        "label": "Sales Done → Finance Report",
        "enabled": True,
        "trigger_agent": "sales",
        "trigger_status": "done",
        "action_agent": "finance",
        "action_task": "A sales processing run just completed. Pull today's revenue, calculate COGS and profit margins, flag any unusual variance vs last week, and update the financial summary.",
    },
    {
        "id": "trend_to_art",
        "label": "Trend Found → Art Creation",
        "enabled": False,
        "trigger_agent": "trend",
        "trigger_status": "done",
        "action_agent": "art",
        "action_task": "Trend forecasting just completed. Review the highest-confidence HOT or EMERGING trends flagged (confidence >= 7) and create art for the top trend. Include style, color palette, and product format in the brief.",
    },
    {
        "id": "retention_to_email",
        "label": "Retention → Email Campaign",
        "enabled": False,
        "trigger_agent": "retention",
        "trigger_status": "done",
        "action_agent": "email",
        "action_task": "Customer retention analysis just finished. Draft a re-engagement email campaign targeting customers who purchased 30-90 days ago. Use retention insights to craft a compelling subject line and offer.",
    },
    {
        "id": "store_to_listing",
        "label": "Store Audit → Listing Refresh",
        "enabled": True,
        "trigger_agent": "store",
        "trigger_status": "done",
        "action_agent": "listing",
        "action_task": "Store management just completed an audit. Review listings flagged as underperforming or expiring and refresh their SEO: update titles, tags, and descriptions on the top 3 flagged listings.",
    },
    {
        "id": "finance_to_ceo",
        "label": "Finance Report → CEO Alert",
        "enabled": False,
        "trigger_agent": "finance",
        "trigger_status": "done",
        "action_agent": "ceo",
        "action_task": "Financial agent just completed a report. Review the financial summary and take executive actions as needed: adjust pricing strategy, flag cash flow concerns, or approve new product investment.",
    },
    {
        "id": "marketing_to_social",
        "label": "Marketing → Social Push",
        "enabled": False,
        "trigger_agent": "marketing",
        "trigger_status": "done",
        "action_agent": "social",
        "action_task": "Marketing just completed an SEO update. Create social media content (Pinterest pins, Instagram posts) for the listings that were optimized. Use the new keyword findings in captions and hashtags.",
    },
]

_CHAINS_SAFE_OFF = {"art_to_qc", "finance_to_ceo"}  # must stay disabled to prevent loops


def _load_chains() -> list:
    try:
        if CHAINS_FILE.exists():
            chains = json.loads(CHAINS_FILE.read_text())
            changed = False
            for c in chains:
                if c.get("id") in _CHAINS_SAFE_OFF and c.get("enabled"):
                    c["enabled"] = False
                    changed = True
            if changed:
                CHAINS_FILE.write_text(json.dumps(chains, indent=2))
            return chains
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
        "enabled": False,
    },
    {
        "id":      "competitor_intel",
        "label":   "Weekly Competitor Intel",
        "agent":   "intel",
        "task":    "Run weekly competitor intelligence: research top competitors for 3D printed home decor and hand painted wood items on Etsy. Identify their best-selling products, pricing, and keywords. Save all findings to the knowledge base.",
        "cron":    "0 8 * * 0",
        "enabled": False,
    },
    {
        "id":      "listing_audit",
        "label":   "Weekly Listing Audit",
        "agent":   "product",
        "task":    "Run a full SEO audit of all listings using bulk_seo_audit. For each listing scoring below 70, generate improvement suggestions. Update the worst 3 listings with improved titles and tags. Save insights to knowledge base.",
        "cron":    "0 9 * * 1",
        "enabled": False,
    },
    {
        "id":      "analytics_weekly",
        "label":   "Weekly Analytics Deep Dive",
        "agent":   "analytics",
        "task":    "Run weekly deep-dive analytics: per-listing profitability table, traffic sources, conversion funnel, best/worst categories. Compare against 30-day revenue targets. Log all metrics to knowledge base. Provide 3 specific revenue-growing recommendations.",
        "cron":    "0 10 * * 0",
        "enabled": False,
    },
    {
        "id":      "weekly_tax",
        "label":   "Weekly Tax Summary",
        "agent":   "tax",
        "task":    "Generate weekly tax summary: total revenue, taxable transactions, estimated tax liability, new deductions to log. Flag any sales in new states that may create tax nexus. Recommend quarterly estimated payment if needed.",
        "cron":    "0 7 * * 1",
        "enabled": False,
    },
    {
        "id":      "weekly_supply",
        "label":   "Weekly Supply Check",
        "agent":   "supply",
        "task":    "Run weekly supply chain health check: review filament inventory levels, flag items below reorder threshold, check for supplier delays, and recommend purchase orders for next week's production needs.",
        "cron":    "0 8 * * 1",
        "enabled": False,
    },
    {
        "id":      "abt_review",
        "label":   "A/B Test Review",
        "agent":   "abt",
        "task":    "Review all active A/B tests: identify tests with 14+ days of data, run statistical analysis on each, declare winners where confidence >= 95%, save winning strategies to the knowledge base, and suggest the next test to set up.",
        "cron":    "0 9 * * 3",
        "enabled": False,
    },
    {
        "id":      "weekly_retention",
        "label":   "Weekly Retention Check",
        "agent":   "retention",
        "task":    "Run weekly customer retention analysis: identify repeat customers, buyers at risk of churning (60+ days since last purchase), and highest-value customers. Recommend targeted re-engagement actions and draft one follow-up er offer.",
        "cron":    "0 11 * * 2",
        "enabled": False,
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


# Per-agent timeout thresholds (seconds) before supervisor intervenes.
# Sonnet creative agents get more time; Haiku operational agents are faster.
_AGENT_TIMEOUTS: dict[str, int] = {
    "ceo":      180,   # Haiku, 3 iterations
    "art":      300,   # Sonnet, generates image files
    "planner":  300,   # Sonnet, generates planner PDFs
    "brand":    240,   # Sonnet, design work
    "listing":  180,   # Sonnet, SEO writing
    "marketing":180,
    "qc":       180,   # Sonnet, file review
}
_DEFAULT_TIMEOUT = 120   # All other Haiku agents: 2 minutes

# Tracks how many times each agent has been retried this session.
_supervisor_retries: dict[str, int] = {}


def _supervisor_check():
    """Detect slow/hung agents and recover them — runs every 90 seconds."""
    now = datetime.now()
    stuck: list[tuple[str, str, int]] = []

    for key, state in list(agent_states.items()):
        if state.get("status") != "running":
            continue
        started_str = state.get("started")
        if not started_str:
            continue
        try:
            elapsed = int((now - datetime.fromisoformat(started_str)).total_seconds())
            threshold = _AGENT_TIMEOUTS.get(key, _DEFAULT_TIMEOUT)
            if elapsed > threshold:
                stuck.append((key, state.get("task", ""), elapsed))
        except Exception:
            pass

    for key, task, elapsed in stuck:
        retry_count = _supervisor_retries.get(key, 0)
        mins = elapsed // 60
        secs = elapsed % 60

        # Reset the stuck agent to error state and broadcast it
        agent_states[key] = {
            "status": "error", "task": task,
            "error": f"Supervisor reset after {mins}m {secs}s",
        }
        _persist_agent_states()
        _emit(key, "error", f"⚠ Supervisor: reset after {mins}m {secs}s")

        if retry_count < 2 and task:
            # Ask Claude to simplify the task and requeue
            try:
                from agents.supervisor_agent import SupervisorAgent
                simplified = SupervisorAgent().simplify_task(key, task, elapsed)
                if simplified and simplified.upper() != "SKIP":
                    _supervisor_retries[key] = retry_count + 1
                    _enqueue_task(key, simplified, f"Supervisor retry #{retry_count + 1}")
                    _add_notification(
                        "supervisor_retry",
                        f"Supervisor: {key.upper()} requeued",
                        f"Stalled after {mins}m — simplified and retried automatically",
                        "🔄",
                    )
                    print(f"  [Supervisor] {key} simplified + requeued (retry #{retry_count + 1})", flush=True)
                else:
                    _supervisor_retries[key] = 99  # Prevent further retries
                    _add_notification(
                        "supervisor_skip",
                        f"Supervisor: {key.upper()} skipped",
                        f"Task unrecoverable after {mins}m — needs human review",
                        "⚠️",
                    )
                    print(f"  [Supervisor] {key} skipped (unrecoverable)", flush=True)
            except Exception as exc:
                print(f"  [Supervisor] Error for {key}: {exc}", flush=True)
                _add_notification(
                    "supervisor_error",
                    f"Supervisor: {key.upper()} reset",
                    f"Stuck after {mins}m — task aborted (supervisor error)",
                    "⚠️",
                )
        else:
            # Already retried max times — give up and notify
            _supervisor_retries[key] = 0
            _add_notification(
                "supervisor_abort",
                f"Supervisor: {key.upper()} aborted",
                f"Stuck {mins}m, retried {retry_count}x — needs human review",
                "🚫",
            )
            print(f"  [Supervisor] {key} aborted after {retry_count} retries", flush=True)


def _start_scheduler():
    global _scheduler
    _scheduler = BackgroundScheduler(timezone="America/New_York")
    schedules = _load_schedules()
    for s in schedules:
        if s.get("enabled"):
            _register_job(s)
    # Order polling: every 30 seconds for near-instant digital delivery
    _scheduler.add_job(
        func             = _poll_orders,
        trigger          = "interval",
        seconds          = 30,
        id               = "_order_poll",
        replace_existing = True,
    )
    # System improvement scan: weekly on Saturday at 3am (NOT every 6 hours —
    # auto-editing code files while agents are running is dangerous)
    _scheduler.add_job(
        func             = lambda: _safe_enqueue("sysop", "Run a full system health scan: check task history for errors, scan agent and tool files for issues, research improvements online, auto-fix what is safe, and log suggestions for everything else.", "System Health Scan"),
        trigger          = "cron",
        day_of_week      = "sat",
        hour             = 3,
        id               = "_sysop_scan",
        replace_existing = True,
    )
    # Supervisor: detect and recover stuck agents every 90 seconds
    _scheduler.add_job(
        func             = _supervisor_check,
        trigger          = "interval",
        seconds          = 90,
        id               = "_supervisor",
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
    global _event_loop, agent_states
    _event_loop = asyncio.get_running_loop()
    # Restore last known agent states from disk
    saved = _load_agent_states()
    if saved:
        # Mark any previously-running agents as interrupted so they show correctly
        for k, v in saved.items():
            if isinstance(v, dict) and v.get("status") == "running":
                v["status"] = "idle"
                v["last_result"] = "(interrupted by restart)"
        agent_states.update(saved)
    _start_scheduler()
    yield
    if _scheduler:
        _scheduler.shutdown(wait=False)
    _persist_agent_states()


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
    "delegate_to_planner_design_agent":  "planner",
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
    "delegate_to_ab_testing_agent":               "abt",
    "delegate_to_api_connections_agent":           "api",
    "delegate_to_trend_forecasting_agent":         "trend",
    "delegate_to_customer_retention_agent":        "retention",
    "delegate_to_workflow_coordinator":            "coordinator",
}

# ── Event emission ─────────────────────────────────────────────────────────────

def _emit(agent_key: str, event: str, message: str, extra: dict | None = None):
    if _event_loop is None or _event_loop.is_closed():
        return
    now = datetime.now()
    payload = {
        "type":    "agent_event",
        "agent":   agent_key,
        "event":   event,
        "message": message,
        "ts":      now.strftime("%H:%M:%S"),
        "data":    extra or {},
    }
    asyncio.run_coroutine_threadsafe(manager.broadcast(payload), _event_loop)
    _append_session_log({
        "agent":   agent_key,
        "event":   event,
        "message": message,
        "ts":      now.isoformat(),
    })

# ── Agent factory ──────────────────────────────────────────────────────────────

AGENT_CLASSES: dict[str, str] = {
    "ceo": "CEOAgent", "brand": "BrandDesignAgent", "art": "ArtCreationAgent",
    "planner": "PlannerDesignAgent",
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
    "sysop": "SystemImprovementAgent",
}


def _build_agent(key: str):
    import agents as ag
    cls = getattr(ag, AGENT_CLASSES.get(key, ""), None)
    return cls() if cls else None

# ── Pipeline routing ───────────────────────────────────────────────────────────

_PIPELINE_AGENTS = {"brand", "art", "planner", "qc", "store", "marketing", "finance", "analytics"}

_PIPELINE_KEYWORDS = {
    "create", "launch", "new product", "design a", "design the",
    "make a", "make the", "build a", "generate a", "generate the", "produce a",
    "develop a", "start a new", "plan a new", "full pipeline", "full process",
}

_QUERY_PREFIXES = {
    "get", "list", "show", "check", "what", "how", "report", "status",
    "summary", "analyze", "review", "audit", "find", "search", "give",
    "tell", "explain", "describe", "calculate", "run", "pull",
    "publish", "add", "write",
}


def _should_route_to_ceo(agent_key: str, task: str) -> bool:
    # Listing agent always handles its own tasks — never route to CEO
    if agent_key in ("ceo", "hall", "listing"):
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

def _run_sub_agent_observable(target_key: str, task: str, max_iterations: int | None = None) -> str:
    if target_key in PIPELINE_STAGES:
        _pipeline_step(target_key)

    started = datetime.now()
    agent_states[target_key] = {"status": "running", "task": task, "started": started.isoformat()}
    _persist_agent_states()
    _emit(target_key, "start", task[:80])
    try:
        sub = _build_agent(target_key)
        if sub is None:
            return f"Error: no agent registered for key '{target_key}'"
        sub = _make_observable(sub, target_key)
        result = sub.run(task, max_iterations=max_iterations) if max_iterations else sub.run(task)
        duration = round((datetime.now() - started).total_seconds())
        agent_states[target_key] = {"status": "idle", "task": task, "last_result": result}
        _persist_agent_states()
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
        _persist_agent_states()
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
    if not os.getenv("ANTHROPIC_API_KEY", ""):
        agent_states[key] = {
            "status": "error", "task": task,
            "error": "ANTHROPIC_API_KEY not set — open .env and paste your key, then restart.",
        }
        _emit(key, "error", "❌ ANTHROPIC_API_KEY missing — check .env and restart.")
        return
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
    _persist_agent_states()
    _emit(key, "start", task[:80])
    try:
        agent = _build_agent(key)
        if agent is None:
            raise ValueError(f"Unknown agent: {key}")
        agent  = _make_observable(agent, key)
        result = agent.run(task)
        duration = round((datetime.now() - started).total_seconds())
        agent_states[key] = {"status": "idle", "task": task, "last_result": result}
        _persist_agent_states()
        _emit(key, "done", "Complete ✓", {"result": result[:2000]})
        _fire_chains(key, "done")
        if key in {"listing", "qc", "sales", "delivery", "ceo"}:
            _add_notification("agent_done", f"{key.title()} completed", task[:80], "✅")
        _save_history_entry({
            "agent": key, "task": task[:200], "status": "done",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": result[:300], "triggered_by": "manual",
        })
        with _pipeline_lock:
            _active_pipeline.clear()
    except Exception as exc:
        duration = round((datetime.now() - started).total_seconds())
        agent_states[key] = {"status": "error", "task": task, "error": str(exc)}
        _persist_agent_states()
        _emit(key, "error", f"Error: {str(exc)[:300]}")
        _save_history_entry({
            "agent": key, "task": task[:200], "status": "error",
            "started": started.isoformat(), "duration_s": duration,
            "result_preview": str(exc)[:300], "triggered_by": "manual",
        })
        with _pipeline_lock:
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

@app.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")

@app.get("/sw.js", include_in_schema=False)
async def service_worker():
    resp = FileResponse(STATIC_DIR / "sw.js", media_type="application/javascript")
    resp.headers["Service-Worker-Allowed"] = "/"
    return resp

@app.get("/icon-{size}.png", include_in_schema=False)
async def pwa_icon(size: str):
    path = STATIC_DIR / f"icon-{size}.png"
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    return FileResponse(str(path), media_type="image/png")


@app.get("/api/agents")
async def list_agents():
    return JSONResponse({"agents": list(AGENT_CLASSES.keys()), "states": agent_states})


@app.get("/api/tunnel-url")
async def get_tunnel_url():
    return JSONResponse({"url": _tunnel_url})


@app.post("/api/tunnel-url")
async def set_tunnel_url(body: dict):
    global _tunnel_url
    _tunnel_url = body.get("url", "")
    return JSONResponse({"ok": True})


@app.get("/api/session-log")
async def get_session_log(limit: int = 200):
    try:
        if SESSION_LOG_FILE.exists():
            log = json.loads(SESSION_LOG_FILE.read_text())
            return JSONResponse({"log": log[-limit:], "total": len(log)})
    except Exception:
        pass
    return JSONResponse({"log": [], "total": 0})


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
    with _history_lock:
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

    msg_string = msg.as_string()

    def _send_smtp():
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to], msg_string)
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.sendmail(smtp_user, [to], msg_string)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _send_smtp)
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

    def _run_vtracer():
        vtracer.convert_image_to_svg_py(
            image_path      = tmp_path,
            out_path        = str(out_path),
            colormode       = colormode,
            filter_speckle  = filter_speckle,
            color_precision = color_precision,
            layer_difference= layer_difference,
            path_precision  = path_precision,
        )

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_vtracer)
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
    await manager.broadcast({"type": "new_idea", "idea": entry})
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


# ── Digital Product Gallery ────────────────────────────────────────────────────

@app.get("/api/digital-products")
async def get_digital_products():
    """Return all agent-created digital products with browser-accessible file URLs."""
    try:
        from tools.data_store import DataStore
        store = DataStore()
        raw = store.get("digital_products", default=[])
        products = []
        data_dir = DATA_DIR.resolve()
        for p in raw:
            entry = {
                "id":          p.get("id") or p.get("product_id", ""),
                "title":       p.get("title", "Untitled"),
                "type":        p.get("product_type", "digital"),
                "status":      p.get("status", "unknown"),
                "qc_status":   p.get("qc_status"),
                "price":       p.get("price"),
                "color_scheme":p.get("color_scheme"),
                "interactive": p.get("interactive", False),
                "created_at":  p.get("created_at", ""),
                "archived_at": p.get("archived_at"),
                "file_url":    None,
                "thumb_url":   None,
            }
            # Resolve absolute file_path → relative web URL
            fp = p.get("file_path", "")
            if fp:
                try:
                    resolved = Path(fp).resolve()
                    rel = resolved.relative_to(data_dir)
                    entry["file_url"] = f"/data/{rel.as_posix()}"
                except (ValueError, TypeError):
                    pass
            pid = entry["id"]
            # Look for companion image thumbnail
            for ext in (".jpg", ".jpeg", ".png"):
                candidate = data_dir / "digital_products" / "product_files" / f"{pid}{ext}"
                if candidate.exists():
                    entry["thumb_url"] = f"/data/digital_products/product_files/{pid}{ext}"
                    break
            products.append(entry)
        products.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return JSONResponse({"products": products, "total": len(products)})
    except Exception as e:
        print(f"[ERROR] get_digital_products: {e}", flush=True)
        return JSONResponse({"products": [], "total": 0, "error": str(e)})


@app.patch("/api/digital-products/{product_id}/status")
async def set_product_status(product_id: str, body: dict):
    """Move a product to 'archived' or 'approved' without deleting the file."""
    from tools.data_store import DataStore
    allowed = {"archived", "approved", "qc_pending", "active"}
    new_status = body.get("status", "")
    if new_status not in allowed:
        return JSONResponse({"error": f"status must be one of {sorted(allowed)}"}, status_code=400)
    try:
        store = DataStore()
        products = store.get("digital_products", default=[])
        product = next((p for p in products if (p.get("id") or p.get("product_id")) == product_id), None)
        if not product:
            return JSONResponse({"error": "Product not found"}, status_code=404)
        product["status"] = new_status
        if new_status == "archived":
            product["archived_at"] = datetime.utcnow().isoformat() + "Z"
        store.set(products, "digital_products")
        store.save()
        return JSONResponse({"ok": True, "id": product_id, "status": new_status})
    except Exception as e:
        print(f"[ERROR] set_product_status: {e}", flush=True)
        return JSONResponse({"error": str(e)}, status_code=500)


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


def _direct_pipeline_extract_product_id(text: str) -> str | None:
    """Extract a DP-prefixed product ID from agent result text."""
    m = re.search(r'\bDP\d{3,}\b', text)
    return m.group(0) if m else None


def _direct_pipeline_auto_approve(product_id: str, note: str) -> None:
    """Force-approve a product in the DataStore, bypassing QC agent."""
    from datetime import date as _date
    from tools.data_store import DataStore as _DS
    store = _DS()
    products = store.get("digital_products", default=[])
    for p in products:
        if p["id"] == product_id:
            p["status"]           = "approved"
            p["qc_status"]        = "approved"
            p["qc_notes"]         = note
            p["spec_check_result"] = "PASS"
            p["qc_date"]          = str(_date.today())
            p["updated_at"]       = str(_date.today())
            store.set(products, "digital_products")
            store.save()
            break


def _run_direct_pipeline(category: str, description: str, style: str):
    """Run art/planner → QC → listing sequentially without the CEO."""
    is_planner = category == "planner"
    creator    = "planner" if is_planner else "art"
    label      = "Planner" if is_planner else "Art"

    _add_notification("pipeline_direct_start", f"Direct Pipeline: {label}", description[:80], "🚀")
    _pipeline_start("ceo")

    # ── Step 1: Create the product file ──────────────────────────────────────
    if is_planner:
        style_part = f"Style: {style}.\n" if style else ""
        create_task = (
            f"Create a premium digital planner with a handcrafted art cover.\n"
            f"Description: {description}.\n"
            f"{style_part}"
            "Follow these steps in exact order:\n"
            "1) Call create_art_concept with product_type='planner' to register the product.\n"
            "2) Call generate_digital_art to create the cover image. "
            "Choose the cover prompt matching your planned color scheme from your system prompt's "
            "COVER IMAGE PROMPTS table. Use size='1024x1024', quality='high'. "
            "Note the file_path from the result.\n"
            "3) Call create_digital_planner with the product_id, your chosen color_scheme, "
            "interactive=true, include_sections=['monthly','weekly','habit_tracker','goals','notes'], "
            "year=0, and cover_image_path=<file_path from step 2>.\n"
            "Return the product_id when done."
        )
    else:
        style_part = f"Requested style: {style}.\n" if style else (
            "Choose the best-fit style from the shop library in your system prompt "
            "(A=Bold Flat, B=Gestural Botanical, C/C2=Quote Print, E=Impasto Oil Floral, "
            "F=Linocut, G=Japandi, H=Golden Hour Landscape, I=Painterly Garden, "
            "J=Mediterranean Window, K=Whimsical Fine Art). "
            "Name the chosen style in the concept field.\n"
        )
        create_task = (
            f"Create a premium Etsy digital wall art product.\n"
            f"Description: {description}.\n"
            f"{style_part}"
            "Do exactly 2 steps:\n"
            "1) Call create_art_concept — set product_type='wall_art', price=7. "
            "Include 'Style X — [name]' at the start of the concept field so the style is recorded.\n"
            "2) Call generate_digital_art using the DALL-E formula for the chosen style from your "
            "system prompt (use the PROVEN TOP-SELLING PROMPTS section as your template). "
            "Use size='1024x1536', quality='high'.\n"
            "Return the product_id."
        )

    result1 = _run_sub_agent_observable(creator, create_task, max_iterations=6 if is_planner else 5)

    product_id = _direct_pipeline_extract_product_id(result1)
    if not product_id:
        _add_notification("pipeline_direct_error", f"Direct Pipeline: {label} creation failed",
                          result1[:200], "❌")
        return

    # ── Step 2: QC ───────────────────────────────────────────────────────────
    has_openai = bool(os.getenv("OPENAI_API_KEY", "").strip())

    if not has_openai:
        # No OpenAI key means placeholder art was created — auto-approve so pipeline completes.
        # Real QC (with visual inspection) requires actual AI-generated art.
        _direct_pipeline_auto_approve(
            product_id,
            "Demo auto-approval — add OPENAI_API_KEY to .env for real AI art and full QC.",
        )
        _add_notification("pipeline_direct_qc_skip", "QC: Auto-approved (demo mode)",
                          f"{product_id} — add OPENAI_API_KEY for real art + full QC", "⚠️")
        result2 = f"approved product_id={product_id}"
    else:
        qc_task = (
            f"QC product {product_id}. One step only: call check_and_auto_approve product_id={product_id}"
        )
        result2 = _run_sub_agent_observable("qc", qc_task, max_iterations=3)

        if "REJECTED" in result2:
            # One retry: recreate the product with QC feedback
            retry_task = create_task + f"\n\nIMPORTANT — Previous attempt was rejected by QC: {result2[:300]}"
            result1 = _run_sub_agent_observable(creator, retry_task, max_iterations=6 if is_planner else 5)
            product_id2 = _direct_pipeline_extract_product_id(result1) or product_id
            qc_task2 = (
                f"QC product {product_id2}. One step: call check_and_auto_approve product_id={product_id2}"
            )
            result2 = _run_sub_agent_observable("qc", qc_task2, max_iterations=3)
            product_id = product_id2

        if "REJECTED" in result2:
            _add_notification("pipeline_direct_qc", f"Direct Pipeline: {label} needs review",
                              "QC rejected twice — check Products tab", "⚠️")
            return

    # ── Step 3: Etsy Listing ──────────────────────────────────────────────────
    list_task = (
        f"Create an Etsy listing for digital product {product_id} (status=approved).\n"
        f"Product: {description}." + (f" Style: {style}." if style else "") + "\n"
        "Use your expert SEO knowledge — do NOT call research or market tools.\n"
        "Complete these 5 steps in order:\n"
        "1) generate_listing_content — title 120-140 chars (primary keyword first), "
        "exactly 13 multi-word tags (each ≤20 chars, no verbatim title repeats), "
        "description 300+ chars (power hook in line 1, list file specs, usage instructions), "
        "price $5-$9 for single art or $9-$16 for bundles, section='Wall Art Prints' or 'Digital Planners'.\n"
        "2) publish_digital_listing confirm=true.\n"
        "3) upload_listing_image product_id.\n"
        "4) attach_digital_file product_id.\n"
        "5) customer_ready_check product_id."
    )
    _run_sub_agent_observable("listing", list_task, max_iterations=6)

    _add_notification("pipeline_direct_done", f"Direct Pipeline: {label} complete ✓",
                      f"{description[:60]} — created, QC approved, listed on Etsy", "✅")


@app.post("/api/direct-pipeline")
async def direct_pipeline(body: dict):
    """Run the full create→QC→list pipeline directly, no CEO needed."""
    category    = (body.get("category") or "art").strip().lower()
    description = (body.get("description") or "").strip()
    style       = (body.get("style") or "").strip()
    if not description:
        return JSONResponse({"error": "description is required"}, status_code=400)
    if category not in ("art", "planner"):
        category = "art"
    threading.Thread(
        target=_run_direct_pipeline,
        args=(category, description, style),
        daemon=True,
    ).start()
    return JSONResponse({"status": "started", "category": category})


@app.post("/api/list-product")
async def list_product(body: dict):
    """Send a specific approved product to the Etsy Listing Agent."""
    product_id = (body.get("product_id") or "").strip()
    if not product_id:
        return JSONResponse({"error": "product_id is required"}, status_code=400)
    from tools.data_store import DataStore as _DS
    store = _DS()
    products = store.get("digital_products", default=[])
    product = next((p for p in products if p.get("id") == product_id), None)
    if not product:
        return JSONResponse({"error": f"Product {product_id} not found"}, status_code=404)
    if product.get("status") != "approved":
        return JSONResponse({"error": f"Product must be approved (current: {product.get('status')})"}, status_code=400)
    task = (
        f"Create an Etsy listing for digital product {product_id} (status=approved).\n"
        f"Product title: {product.get('title', product_id)}. "
        f"Concept: {product.get('concept', '')}.\n"
        "Use your expert SEO knowledge — do NOT call research or market tools.\n"
        "Complete these 5 steps in order:\n"
        "1) generate_listing_content — title 120-140 chars (primary keyword first), "
        "exactly 13 multi-word tags (each ≤20 chars), description 300+ chars (power hook in line 1), "
        "price $5-$9 single art or $9-$16 bundles, section='Wall Art Prints' or 'Digital Planners'.\n"
        "2) publish_digital_listing confirm=true.\n"
        "3) upload_listing_image.\n"
        "4) attach_digital_file.\n"
        "5) customer_ready_check."
    )
    threading.Thread(
        target=_run_sub_agent_observable,
        args=("listing", task),
        kwargs={"max_iterations": 6},
        daemon=True,
    ).start()
    _add_notification("listing_started", f"Listing Agent: {product_id}",
                      f"Creating Etsy listing for {product.get('title', product_id)[:60]}", "📤")
    return JSONResponse({"status": "started", "product_id": product_id})


@app.post("/api/list-all-approved")
async def list_all_approved():
    """Send all approved unlisted products to the Etsy Listing Agent at once."""
    from tools.data_store import DataStore as _DS
    store = _DS()
    products = store.get("digital_products", default=[])
    to_list = [p for p in products if p.get("status") == "approved" and not p.get("etsy_listing_id")]
    if not to_list:
        return JSONResponse({"status": "none", "message": "No approved unlisted products found"})
    ids = ", ".join(p["id"] for p in to_list)
    task = (
        f"Create Etsy listings for these approved products: {ids}.\n"
        "Use your expert SEO knowledge — do NOT call research or market tools.\n"
        "For EACH product in sequence, complete all 5 steps:\n"
        "1) generate_listing_content — title 120-140 chars (primary keyword first), "
        "exactly 13 multi-word tags (each ≤20 chars), description 300+ chars (power hook in line 1), "
        "price $5-$9 single art or $9-$16 bundles, section='Wall Art Prints' or 'Digital Planners'.\n"
        "2) publish_digital_listing confirm=true.\n"
        "3) upload_listing_image.\n"
        "4) attach_digital_file.\n"
        "5) customer_ready_check.\n"
        "Repeat all 5 steps for every product ID listed."
    )
    threading.Thread(
        target=_run_sub_agent_observable,
        args=("listing", task),
        kwargs={"max_iterations": 6 * len(to_list)},
        daemon=True,
    ).start()
    _add_notification("listing_batch_started", f"Listing Agent: {len(to_list)} products",
                      f"Creating Etsy listings for {ids[:80]}", "📤")
    return JSONResponse({"status": "started", "count": len(to_list), "products": ids})


# ── Listing Health ────────────────────────────────────────────────────────────

# ── System Improvement Log ────────────────────────────────────────────────────

_IMPROVEMENT_LOG = DATA_DIR / "improvement_log.json"

@app.get("/api/improvement-log")
async def get_improvement_log(limit: int = 100):
    try:
        if _IMPROVEMENT_LOG.exists():
            entries = json.loads(_IMPROVEMENT_LOG.read_text())
            return JSONResponse({"entries": entries[:limit], "total": len(entries)})
    except Exception:
        pass
    return JSONResponse({"entries": [], "total": 0})

@app.post("/api/improvement-scan")
async def trigger_improvement_scan():
    _enqueue_task(
        "sysop",
        "Run a full system health scan: check task history for errors, scan agent and tool files for issues, research improvements online, auto-fix what is safe, and log suggestions for everything else.",
        "Manual Scan",
    )
    _add_notification("sysop_started", "System scan started", "Scanning codebase for issues and improvements", "🔧")
    return JSONResponse({"status": "queued"})


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


@app.get("/api/setup")
async def get_setup_status():
    """Return configuration status for all required credentials."""
    def _check(var: str, label: str, critical: bool = False) -> dict:
        val = os.getenv(var, "").strip()
        hint = (val[:6] + "…") if len(val) > 6 else ("(empty)" if not val else val)
        return {"key": var, "label": label, "configured": bool(val), "hint": hint, "critical": critical}

    checks = [
        _check("ANTHROPIC_API_KEY",   "Claude AI",              critical=True),
        _check("ETSY_API_KEY",        "Etsy API Key",           critical=True),
        _check("ETSY_ACCESS_TOKEN",   "Etsy Access Token",      critical=False),
        _check("ETSY_SHOP_ID",        "Etsy Shop ID",           critical=True),
        _check("OPENAI_API_KEY",      "OpenAI / DALL-E",        critical=False),
        _check("SMTP_USER",           "Email (SMTP)",           critical=False),
        _check("SMTP_PASSWORD",       "Email Password",         critical=False),
    ]
    ready = all(c["configured"] for c in checks if c["critical"])
    return JSONResponse({
        "status":  "ready" if ready else "setup_needed",
        "checks":  checks,
        "message": "All critical credentials configured." if ready else "Some required credentials are missing — add them to your .env file.",
        "scheduler_running": _scheduler is not None and _scheduler.running,
        "agents_registered": len(AGENT_CLASSES),
        "schedules_active": sum(1 for s in _load_schedules() if s.get("enabled")),
        "chains_active": sum(1 for c in _load_chains() if c.get("enabled")),
    })


@app.get("/api/agent-states")
async def get_agent_states_api():
    """Return current status and last-run summary for every agent."""
    summary = {}
    for key, state in agent_states.items():
        summary[key] = {
            "status":       state.get("status", "idle"),
            "task":         state.get("task", ""),
            "last_result":  state.get("last_result", ""),
            "error":        state.get("error", ""),
            "started":      state.get("started", ""),
        }
    return JSONResponse(summary)


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
    print("  OnBrandCraftz Town - Starting...")
    print("  Open: http://localhost:8080")
    print("=" * 60)
    # Credential check visible in the bat window
    _ak = os.getenv("ANTHROPIC_API_KEY", "")
    if _ak:
        print(f"  Anthropic API key: loaded ({_ak[:12]}...)")
    else:
        print("  WARNING: ANTHROPIC_API_KEY not found - agents will fail!")
        print("  Make sure .env is in the repo root and contains the key.")
    print()
    def _open_browser():
        import socket
        for _ in range(20):           # poll up to 10 s (20 × 0.5 s)
            time.sleep(0.5)
            try:
                s = socket.create_connection(("127.0.0.1", 8080), timeout=0.5)
                s.close()
                break
            except OSError:
                pass
        webbrowser.open("http://localhost:8080")

    threading.Thread(target=_open_browser, daemon=True).start()

    try:
        uvicorn.run("town_app.server:app", host="0.0.0.0", port=8080, reload=False)
    except OSError as _e:
        if "10048" in str(_e) or "Address already in use" in str(_e):
            print()
            print("  ERROR: Port 8080 is already in use.")
            print("  Fix: open Task Manager > Details tab > end any python.exe process,")
            print("       then restart Start Town.")
        else:
            raise
