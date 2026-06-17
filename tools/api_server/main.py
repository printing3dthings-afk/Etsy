#!/usr/bin/env python3
"""
OnBrandCraftz Mobile API Server

FastAPI backend powering the mobile dashboard app. Read-only + streaming chat.

Start:
  pip install -r tools/api_server/requirements.txt
  uvicorn tools.api_server.main:app --host 0.0.0.0 --port 8000 --reload

Deploy to Railway / Render: set env vars + point start command to this file.
"""

from __future__ import annotations

import asyncio
import json
import os
import re as _re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))

# Load .env before importing shop tools
_env = ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic
import db  # local persistence layer (tools/api_server/db.py)
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402


def _reconcile_etsy_tokens() -> None:
    """Restore a rotated Etsy token from the durable /data DB if the env var is stale.

    Railway re-injects whatever ETSY_ACCESS_TOKEN/ETSY_REFRESH_TOKEN it has stored on
    every restart. But Etsy rotates the refresh token on every use and invalidates the
    old one — so if this server refreshed the token before a restart, the env var is
    now a dead token and the next refresh 401s with invalid_grant (diagnosed 2026-06-17,
    see ops_runbook.md). _token_sync_loop() below persists each rotation to the /data
    SQLite volume, which survives restarts; this function runs once at boot and prefers
    that row — but only when it's provably a forward rotation of the *current* env
    token (matched via parent_refresh_token lineage), so a genuine manual
    re-authorization (tools/etsy_oauth.py + a fresh dashboard update) always wins over
    a stale DB row left over from before that re-auth.
    """
    env_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
    try:
        stored = db.get_etsy_tokens()
    except Exception as exc:
        print(f"[etsy-tokens] reconcile skipped: {exc}", flush=True)
        return
    if not stored:
        return
    if env_refresh and env_refresh not in (stored.get("refresh_token"), stored.get("parent_refresh_token")):
        print("[etsy-tokens] env refresh token doesn't match stored lineage — "
              "treating env as a fresh re-authorization, leaving it in place", flush=True)
        return
    if stored.get("access_token") and stored.get("refresh_token"):
        os.environ["ETSY_ACCESS_TOKEN"] = stored["access_token"]
        os.environ["ETSY_REFRESH_TOKEN"] = stored["refresh_token"]
        print(f"[etsy-tokens] restored rotated token from {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)


_reconcile_etsy_tokens()

# ── Executable command registry (CEO agent can invoke these) ───────────────────
_EXEC_COMMANDS: dict[str, dict] = {
    "shop_health_check": {
        "script": "tools/shop_health_check.py",
        "description": "Run a live shop health snapshot — metrics, listing quality, tag audit",
        "timeout": 60,
        "long_running": False,
    },
    "generate_coloring_pages": {
        "script": "tools/generate_coloring_pages.py",
        "description": "Generate all 20 kawaii coloring pages via gpt-image-1 (takes ~15 min)",
        "timeout": 30,
        "long_running": True,
    },
    "generate_coloring_pages_preview": {
        "script": "tools/generate_coloring_pages.py",
        "args": ["--preview"],
        "description": "Preview coloring page listing JSON — no API calls, instant",
        "timeout": 30,
        "long_running": False,
    },
    "generate_coloring_pages_quick": {
        "script": "tools/generate_coloring_pages.py",
        "args": ["--themes", "3"],
        "description": "Generate first 3 coloring page themes only (~3 min)",
        "timeout": 30,
        "long_running": True,
    },
    "rebuild_sticker_pack": {
        "script": "tools/rebuild_sticker_pack.py",
        "description": "Rebuild sticker pack ZIPs for all planners from cached images",
        "timeout": 60,
        "long_running": False,
    },
    "qc_sweep": {
        "script": "tools/qc_sweep.py",
        "description": "Run quality-control sweep across all product files",
        "timeout": 90,
        "long_running": False,
    },
    "listing_integrity_check": {
        "script": "tools/listing_integrity_check.py",
        "description": (
            "Audit every live listing for truthfulness/quality violations "
            "(titles >70 chars, quantity-claim mismatches where a 'Set of N' "
            "title doesn't match the delivered files, etc.). Fast read-only mode. "
            "This is the check that surfaces 'something that needs fixing' — run it "
            "first, then stage_action the corrections for Scott's approval."
        ),
        "timeout": 180,
        "long_running": False,
    },
}

# extra_args that would let a direct command run mutate live Etsy data bypass the
# approval gate Scott requires. Frank stages listing edits for one-tap approval;
# he must never push them straight through via a CLI flag (and neither can a
# prompt-injected instruction). Any extra_arg containing one of these is refused.
_FORBIDDEN_EXEC_FLAGS = ("--fix", "--push", "--publish", "--apply", "--activate", "--delete", "--write")

# .strip() is critical: Railway env vars set via the dashboard often carry a
# trailing newline. APP_TOKEN is injected into an inline JS string literal
# (const TOKEN = '...'); a newline inside it is a fatal SyntaxError that kills
# the ENTIRE dashboard script — the page renders but no JS runs (frozen spinner).
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "changeme").strip()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
_SERVER_START = datetime.now(timezone.utc)
_BUILD_ID = "f3c8a21-v30"  # bump on each deploy to confirm Railway is using latest code

print(f"[startup] BUILD={_BUILD_ID} PORT={os.getenv('PORT','?')} TOKEN_SET={bool(os.getenv('APP_SECRET_TOKEN'))} ETSY_TOKEN={bool(os.getenv('ETSY_ACCESS_TOKEN'))} ETSY_REFRESH={bool(os.getenv('ETSY_REFRESH_TOKEN'))} ANTHROPIC={bool(ANTHROPIC_KEY)}", flush=True)

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="OnBrandCraftz Mobile API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve PWA icons (pre-generated files committed to the repo — no runtime PIL).
_STATIC_DIR = Path(__file__).parent / "static"
if _STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

security = HTTPBearer()


def _auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if credentials.credentials != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials


def _price_float(price_field) -> float:
    """Normalize Etsy price field (dict or raw float) to Python float."""
    if isinstance(price_field, dict):
        divisor = price_field.get("divisor", 100) or 100
        return price_field.get("amount", 0) / divisor
    try:
        return float(price_field)
    except (TypeError, ValueError):
        return 0.0


# ── In-process cache ───────────────────────────────────────────────────────────

_cache: dict = {}
_cache_lock = threading.Lock()

# How long the CEO diagnostic stays fresh. Shop data (listings, tags, sales)
# changes slowly, so a 30-min-old report is fine — and a background loop re-warms
# it before it expires so the dashboard practically never hits the ~60s synthesis.
_SUGGESTIONS_TTL = 1800


def _cache_get(key: str, ttl: int = 60):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < ttl:
            return entry["data"]
    return None


def _cache_set(key: str, data) -> None:
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


# ── Ops runbook (loaded fresh on every request — no redeploy needed to update) ──

_OPS_RUNBOOK_PATH = ROOT / "data" / "knowledge_base" / "ops_runbook.md"


def _ops_runbook_block() -> str:
    """Read the ops runbook so Frank can answer 'why was X broken' questions with
    grounded history instead of guessing. Append-only log lives in the repo at
    data/knowledge_base/ops_runbook.md — re-read on every call so new entries are
    picked up immediately, with no code change or redeploy required."""
    try:
        text = _OPS_RUNBOOK_PATH.read_text().strip()
    except OSError:
        return ""
    if not text:
        return ""
    if len(text) > 8000:
        text = text[-8000:]  # keep the most recent entries (file is append-only, newest at bottom)
    return (
        "\n\n── OPS RUNBOOK (real incidents Claude Code has diagnosed/fixed in this "
        "codebase — use this to answer 'why was X broken' or 'what changed' questions "
        "with grounded specifics instead of guessing) ──\n" + text
    )


# ── CEO Agent system prompt ────────────────────────────────────────────────────

_CEO_SYSTEM = """\
You are Fucking Frank, the CEO Agent for OnBrandCraftz, an Etsy shop selling kawaii
digital planners, sticker packs, and 3D-print SVG files. You are chatting with Scott,
the shop owner, via his private mobile dashboard. You are the operating brain of the
business — Scott relies on you so he does NOT have to dig through data or call in an
engineer for answers. If asked your name, you are Fucking Frank.

Your role:
- Answer questions about the business, products, listings, and growth strategy
- Give honest, direct assessments — no sugar-coating
- Recommend next actions and prioritize what matters most
- Uphold the shop's #1 rule: never lie to customers — every listing claim must be
  verifiable against the actual files delivered
- If Scott asks why something broke or what was fixed, check the OPS RUNBOOK section
  appended below before answering — it's a real log of incidents Claude Code has
  diagnosed and fixed in this exact codebase, not a guess

LIVE DATA — you can read the real shop, do not guess:
- Use the get_metrics tool for revenue (7d/30d), order counts, active listing count,
  total sales, and review rating.
- Use the list_listings tool to inspect listings (title, price, views, favorites, tags).
- ALWAYS pull the real numbers with a tool before quoting any figure. Never invent data.
  If a tool returns an error, say so plainly rather than guessing.

How you operate:
- You analyze, recommend, and can DRAFT changes (titles, tags, descriptions, photo plans,
  quality-gate checklists). You do not publish, change prices, or edit live listings
  yourself — you prepare the work and Scott approves it. Be explicit about what you'd
  change and why, so a single yes is enough to act.
- When you have a concrete fix ready (a corrected title, a full replacement tag set, or a
  draft ready to publish), use the stage_action tool to queue it for Scott's one-tap
  approval in the Action Center. ALWAYS read the listing first so the change is accurate.
  Tell Scott you've staged it and what it will do. Never claim a change is live — it only
  applies after he approves.
- You CAN execute backend commands directly using the execute_command tool. Use this when
  Scott asks you to DO something: run the listing integrity check, run a health check,
  rebuild sticker packs, regenerate files, etc. Brief Scott on what you're about to run,
  then call it. Long-running commands (image generation) launch in the background — confirm
  the PID and tell Scott where to find the output. Quick commands return full terminal
  output for you to summarize.

ACT, DON'T NARRATE — this is the most important rule about doing work:
- When a task can be done with a tool you have, CALL THE TOOL in the same turn. Never reply
  "I'll run that now" or "let me check" and then stop — that does nothing. Saying you will
  do something is not doing it. Either call the tool or say plainly you can't.
- When you spot a fixable problem (a bad title, missing tags, a draft ready to publish),
  immediately stage_action the concrete fix so it lands in Scott's Action Center for one-tap
  approval — don't just describe what should change. Read the listing first so the fix is exact.
- To find problems in the first place, run the listing_integrity_check command — it reports
  exactly which listings violate the 2026 standards. Then stage the fixes it surfaces.
- You do NOT apply listing edits, publishes, or price changes yourself — those always go
  through Scott's one-tap approval. But you DO run read-only checks and safe automations
  yourself without waiting.

Products live: DP1026 Life Planner ($14.99), DP1027 Student Planner ($9.99),
DP1028 Budget Planner ($12.99), DP1029 Fitness Planner ($12.99).
SS1001 America 250 SVG Pack ($14.99) — DRAFT, awaiting Scott's click to publish.

Quality standards:
- Every listing photo must be generated via gpt-image-1 images.edit with the real
  product file as input — never an AI stand-in
- All pre-publish quality gates must pass before any listing goes live
- Growth is urgent but quality never drops

Keep responses concise and scannable — Scott is reading on his phone.\
"""

# ── CEO agent tools (read-only live data; the agent calls these mid-conversation) ─

AGENT_TOOLS = [
    {
        "name": "get_metrics",
        "description": (
            "Live business snapshot from Etsy: revenue (7-day, 30-day), order counts, "
            "active listing count, all-time sales, and review rating. Call this before "
            "quoting any revenue, sales, or rating figure."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_listings",
        "description": (
            "List the shop's listings with title, price, views, favorites, tags, and "
            "(for active listings) real units sold and conversion_pct (sales÷views). "
            "Use to inspect what's live or in draft, find listings with traffic but no "
            "sales, find low performers, or audit SEO."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "string",
                    "enum": ["active", "draft", "inactive"],
                    "description": "Which listing state to fetch. Defaults to active.",
                }
            },
        },
    },
    {
        "name": "stage_action",
        "description": (
            "Stage a proposed change for Scott's one-tap approval. You do NOT execute "
            "it — it lands in the approval queue (Action Center) and only applies to "
            "Etsy when Scott taps Approve. Use for fixes you can fully specify: "
            "correcting a listing title, replacing its tags, or publishing a draft. "
            "Always fetch the listing first so your change is accurate."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "action_type": {
                    "type": "string",
                    "enum": ["update_tags", "update_title", "publish_listing"],
                },
                "listing_id": {"type": "integer", "description": "The listing to change."},
                "summary": {
                    "type": "string",
                    "description": "One-line human summary shown on the approval card.",
                },
                "title": {
                    "type": "string",
                    "description": "New title for update_title. Must be ≤70 characters.",
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Full replacement tag list for update_tags. Max 13, each ≤20 chars.",
                },
            },
            "required": ["action_type", "listing_id", "summary"],
        },
    },
    {
        "name": "execute_command",
        "description": (
            "Execute a backend automation command — run it NOW. Use this when Scott asks you to actually "
            "DO something: generate images, run health checks, rebuild files, etc. "
            "Quick commands return full output immediately. Long-running commands (image generation) "
            "are launched in the background and confirmed with a PID. Always tell Scott what you're "
            "about to run and what it will do before calling this.\n\n"
            "Available commands:\n"
            + "\n".join(
                f"  {k}: {v['description']}"
                for k, v in _EXEC_COMMANDS.items()
            )
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": list(_EXEC_COMMANDS.keys()),
                    "description": "Which command to run.",
                },
                "extra_args": {
                    "type": "string",
                    "description": "Optional additional CLI arguments (e.g. '--regen' to force regenerate).",
                },
            },
            "required": ["command"],
        },
    },
]


def _execute_agent_tool(name: str, tool_input: dict) -> dict:
    """Run a CEO-agent tool and return a JSON-serializable result. Read-only."""
    try:
        if name == "get_metrics":
            return _metrics_sync()
        if name == "list_listings":
            state = (tool_input or {}).get("state", "active")
            data = _listings_sync(state)
            listings = data.get("listings", [])
            if state == "active":  # attach real sales + conversion for the agent
                _enrich_sales(listings)
            # Trim payload for the model: drop thumbnail URLs, cap to 60 listings.
            slim = [
                {k: v for k, v in l.items() if k != "thumbnail_url"}
                for l in listings[:60]
            ]
            return {"count": data.get("count"), "state": data.get("state"), "listings": slim}
        if name == "stage_action":
            ti = tool_input or {}
            payload = {"listing_id": ti.get("listing_id")}
            if ti.get("title") is not None:
                payload["title"] = ti["title"]
            if ti.get("tags") is not None:
                payload["tags"] = ti["tags"]
            candidate = {"type": ti.get("action_type"), "payload": payload}
            ok, msg = _validate_staged_action(candidate)
            if not ok:
                return {"staged": False, "error": msg}
            aid = db.enqueue_action(ti.get("action_type"), ti.get("summary", ""), payload)
            return {
                "staged": True,
                "action_id": aid,
                "status": "pending",
                "note": "Queued for Scott's approval in the Action Center — not yet applied.",
            }
        if name == "execute_command":
            ti = tool_input or {}
            cmd_name = ti.get("command", "")
            extra_args = ti.get("extra_args", "").strip()
            if cmd_name not in _EXEC_COMMANDS:
                return {"error": f"Unknown command '{cmd_name}'. Available: {list(_EXEC_COMMANDS.keys())}"}
            cfg = _EXEC_COMMANDS[cmd_name]
            script = ROOT / cfg["script"]
            cmd = [sys.executable, str(script)] + cfg.get("args", [])
            if extra_args:
                parts = extra_args.split()
                bad = [p for p in parts if any(f in p.lower() for f in _FORBIDDEN_EXEC_FLAGS)]
                if bad:
                    return {
                        "error": (
                            f"Refused: extra_args {bad} would mutate live listings, which must go "
                            "through Scott's approval. Run the read-only check, then use stage_action."
                        )
                    }
                cmd.extend(parts)
            timeout = cfg.get("timeout", 60)
            if cfg.get("long_running"):
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    cwd=str(ROOT),
                )
                return {
                    "started": True,
                    "pid": proc.pid,
                    "command": cmd_name,
                    "description": cfg["description"],
                    "note": f"Running in background as PID {proc.pid}. Check the coloring_pages/ output folder when done.",
                }
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(ROOT),
            )
            out = (result.stdout + "\n" + result.stderr).strip()
            if len(out) > 2000:
                out = out[:1900] + "\n…[output truncated]"
            return {"returncode": result.returncode, "output": out, "success": result.returncode == 0}
        return {"error": f"unknown tool: {name}"}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out (>{timeout}s)"}
    except Exception as exc:
        return {"error": str(exc)}

# ── CEO Suggestions system prompt ─────────────────────────────────────────────────

_SUGGESTIONS_SYSTEM = """\
You are the CEO Agent for OnBrandCraftz running a FULL SHOP DIAGNOSTIC.

You are given the shop's real data inline in the user message: metrics (revenue,
orders, active listings, sales, rating), the full list of ACTIVE listings, and all
DRAFT listings. Analyze ALL of it carefully before answering.

Write your response as a single valid JSON object. No markdown, no prose outside
the JSON — just the object.

JSON format (follow exactly):
{
  "headline": "one-sentence summary of where the shop stands right now, citing actual numbers",
  "score": <integer 1–10 overall shop health>,
  "top_win": "the single strongest thing working in the shop right now, with specifics",
  "top_risk": "the single biggest gap or threat, with specifics",
  "suggestions": [
    {
      "priority": "critical|high|medium|low",
      "category": "seo|conversion|pricing|inventory|content|reviews|operations",
      "title": "short action title (under 60 chars)",
      "detail": "specific observation referencing actual data you just read — title, tag count, view count, revenue figure, etc.",
      "action": "exact concrete next step Scott should take",
      "impact": "what this unlocks — revenue, ranking, conversion",
      "listing_id": <listing id integer if this is about a specific listing, else null>
    }
  ]
}

Rules for suggestions:
- 5 to 8 suggestions total, ordered critical → high → medium → low
- Every detail field must reference real data you read from the tools
- No generic advice — name the specific listing, the specific tag count, the specific number
- Prioritize by revenue impact and urgency
- If a draft has been sitting unpublished, call it out specifically
- If listings have 0 views after 7+ days, identify which ones and why
- Tag gaps (<13 tags), title length violations (>70 chars), and zero-view listings are high priority
\
"""


# ── Conversion Doctor system prompt (single listing deep-dive) ────────────────────

_CONVERSION_DOCTOR_SYSTEM = """\
You are the Conversion Doctor for OnBrandCraftz, an Etsy shop. You are handed ONE
listing that gets traffic but is NOT selling. Your job: diagnose the single most
likely reason it isn't converting, then prescribe ranked, specific fixes.

You will be given the listing's real data: title, price, photo count, tag count
and the tags, views, favorites, real units sold, and the full description text.

Diagnose against Etsy's 2026 conversion standards:
- HERO PHOTO drives click-through; <10 photos is a red flag; lifestyle thumbnail
  beats flat white background. Photo problems are the #1 conversion killer.
- PRICE: psychology endings (.99/.97/.49) outperform round numbers. A price far
  from the product's tier can suppress conversion in either direction.
- TITLE: ≤70 chars, primary keyword in first 40 chars, comma separators not pipes.
- TAGS: all 13 used, multi-word buyer-intent phrases, no title duplication.
- DESCRIPTION: first 1-2 sentences must hook + carry the primary keyword (mobile
  shows only this above the fold). Needs What's Included, compatibility, FAQ.
- FAVORITES BUT NO SALES is a price/trust signal — people want it but won't buy.
- The #1 shop rule: never claim anything untrue. Never suggest a fix that would
  make the listing misrepresent the actual product.

Return ONLY a valid JSON object — no markdown, no prose outside it:
{
  "primary_issue": "the single biggest reason it isn't converting, one sentence with specifics",
  "summary": "one-line plain-English read on this listing's situation, citing its real numbers",
  "fixes": [
    {
      "area": "photos|price|title|description|tags|trust",
      "priority": "critical|high|medium|low",
      "finding": "the specific observation from THIS listing's data (cite the number/text)",
      "fix": "the exact concrete change to make",
      "impact": "what this is expected to unlock for conversion"
    }
  ]
}

Rules:
- 3 to 5 fixes, ordered critical → high → low by conversion impact.
- Every finding must cite this listing's actual data — its photo count, its price,
  its tag count, a phrase from its title or description. No generic advice.
- If the title is fine, say so and move on — do not invent problems.
- Be honest and direct; Scott reads this on his phone.
\
"""


# ── Batch tag generation (one Claude call → 13 tags for N listings) ──────────────

_BATCH_TAG_PROMPT = """\
You are the Etsy SEO specialist for OnBrandCraftz, a shop selling:
- Kawaii digital planners (fillable PDF for GoodNotes, Notability, iPad) — $9.99–$14.99
- Kawaii sticker packs (PNG sheets for GoodNotes Elements) — $4.99–$9.99
- 3D-print SVG/3MF packs (multi-color Bambu Lab files) — $9.99–$14.99
- Printable wall art & signs (instant download) — $2.99–$14.99

Generate exactly 13 Etsy search tags for each listing below.

STRICT TAG RULES (enforced by code — any violation is auto-rejected):
1. Exactly 13 tags per listing
2. Each tag: 2–4 words, MAXIMUM 20 characters including spaces
3. No special characters, symbols, or punctuation
4. Lowercase only
5. Every tag must be unique within the listing
6. Do NOT duplicate any phrase already in the listing title
7. Use multi-word buyer-intent phrases — no single-word tags
8. Cover all search angles: product type, style, app/tool, room/use case, occasion, format

CANONICAL TAG SETS (use these exactly when the listing title matches):
- Life/Ultimate planner → digital planner,goodnotes planner,notability planner,ipad planner,kawaii planner,fillable planner,2026 life planner,kawaii sticker pack,instant download,printable planner,daily planner pdf,planner bundle,habit tracker pdf
- Student/School planner → student planner,digital planner,school planner,goodnotes planner,notability planner,ipad planner,academic planner,study planner,kawaii planner,fillable planner,back to school,instant download,kawaii sticker pack
- Budget/Finance planner → budget planner,finance planner,digital planner,goodnotes planner,money planner,ipad planner,fillable planner,savings planner,debt payoff planner,kawaii planner,instant download,budget tracker,2026 budget plan
- Fitness/Wellness planner → fitness planner,wellness planner,digital planner,goodnotes planner,health planner,ipad planner,habit tracker,meal planner pdf,kawaii planner,fillable planner,instant download,self care planner,2026 fitness plan

PRODUCT-SPECIFIC GUIDANCE:
- Digital planners: always include goodnotes planner, ipad planner, fillable planner, instant download, kawaii sticker pack
- SVG packs / 3D prints: always include 3d print svg, svg cut file, digital download, bambu lab svg, multi color print + theme tags
- Printable wall art: always include printable wall art, instant download, digital download + room/style/occasion tags
- Sticker packs: always include goodnotes stickers, digital stickers, planner stickers, kawaii stickers, instant download

Respond with ONLY a valid JSON array — no markdown, no explanation, no code fences:
[{"listing_id": 123, "tags": ["tag one","tag two","tag three","tag four","tag five","tag six","tag seven","tag eight","tag nine","tag ten","tag eleven","tag twelve","tag thirteen"]}, ...]

Each tags array MUST contain exactly 13 strings. Each string MUST be 20 characters or fewer.\
"""


_TITLE_FIX_PROMPT = (
    "Generate a new Etsy listing title for OnBrandCraftz. Shop sells: kawaii digital planners "
    "(GoodNotes/iPad), sticker packs, 3D-print SVG packs, printable wall art.\n\n"
    "TITLE RULES (code-enforced — violation = rejection):\n"
    "1. Maximum 70 characters — hard limit (mobile ranking penalty above 70)\n"
    "2. First 20-30 characters = primary search keyword buyers type\n"
    "3. Comma separators only (no pipes)\n"
    "4. Include 'Instant Download' and either '2026' or 'Undated' for planners\n"
    "5. No keyword stuffing — natural buyer language\n\n"
    "Current listing:\n"
    "TITLE: {title}\n"
    "PRICE: ${price}\n"
    "TAGS: {tags}\n"
    "DESCRIPTION (first 500 chars): {desc}\n\n"
    "Return ONLY the new title string — no quotes, no explanation, no JSON. "
    "Must be 70 characters or fewer."
)


def _clean_tag(tag: str) -> str:
    """Normalise a tag: lowercase, strip special chars, collapse spaces, enforce 20-char limit."""
    tag = str(tag).strip().lower()
    tag = _re.sub(r"[^a-z0-9 ]", "", tag)
    tag = _re.sub(r" +", " ", tag).strip()
    if len(tag) > 20:
        tag = tag[:20].rsplit(" ", 1)[0] if " " in tag[:20] else tag[:20]
    return tag


def _extract_json_object(text: str) -> dict | list | None:
    """Pull a JSON object/array out of an LLM response that may have conversational
    preamble before a fenced code block (e.g. "Compiling the report now.\n\n```json\n{...}\n```").
    Tries, in order: a fenced ```json block anywhere in the text, a bare fenced block,
    then the outermost {...} span. Returns None if nothing parses."""
    text = text.strip()

    fence_match = _re.search(r"```(?:json|JSON)?\s*\n?(.*?)```", text, _re.DOTALL)
    if fence_match:
        candidate = fence_match.group(1).strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    first_brace = text.find("{")
    last_brace = text.rfind("}")
    if first_brace != -1 and last_brace > first_brace:
        candidate = text[first_brace : last_brace + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _generate_tags_for_listings(listings: list[dict]) -> list[dict]:
    """Call Claude once per batch-of-40 and return [{listing_id, tags:[13]}, ...].

    Uses a single structured prompt that outputs clean JSON — no streaming needed.
    Falls back to an empty list if no API key is set."""
    if not ANTHROPIC_KEY or not listings:
        return []

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    results: list[dict] = []
    batch_size = 40

    for start in range(0, len(listings), batch_size):
        batch = listings[start : start + batch_size]
        rows = []
        for l in batch:
            ct = ",".join(l.get("tags", [])) or "(none)"
            rows.append(
                f'ID:{l["listing_id"]} TITLE:"{(l.get("title") or "")[:80]}" '
                f'PRICE:${round(l.get("price", 0), 2)} TAGS:[{ct}]'
            )
        prompt = _BATCH_TAG_PROMPT + "\n\nListings:\n" + "\n".join(rows)

        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8000,
            messages=[{"role": "user", "content": prompt}],
        )

        raw = msg.content[0].text.strip()
        batch_results = _extract_json_object(raw)
        if batch_results is None:
            raise ValueError(f"Could not parse tag-generation response: {raw[:200]!r}")
        results.extend(batch_results)

    return results


# ── Web UI ─────────────────────────────────────────────────────────────────────

_WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="OnBrandCraftz">
<meta name="theme-color" content="#0D1B2A">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>OnBrandCraftz</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#0D1B2A;--card:#162033;--border:#1e2d42;--gold:#C9A84C;--gold2:#e8c96a;
  --text:#e8edf2;--muted:#6b7d91;--green:#4caf82;--red:#e05555;
  --hdr:calc(52px + env(safe-area-inset-top,0px));
  --nav:calc(60px + env(safe-area-inset-bottom,0px))
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
header{position:fixed;top:0;left:0;right:0;z-index:200;height:var(--hdr);background:var(--card);border-bottom:1px solid var(--border);display:flex;align-items:flex-end;justify-content:space-between;padding:0 16px 14px}
header h1{font-size:17px;font-weight:700;color:var(--gold)}
header span{font-size:12px;color:var(--muted)}
nav{position:fixed;bottom:0;left:0;right:0;z-index:200;height:var(--nav);background:var(--card);border-top:1px solid var(--border);display:flex;align-items:flex-start;padding-top:8px}
nav button{flex:1;background:none;border:none;color:var(--muted);font-size:10px;font-weight:600;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;transition:color .15s;height:44px;-webkit-tap-highlight-color:rgba(201,168,76,.15)}
nav button.active{color:var(--gold)}
nav button svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.screen{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);overflow-y:auto;-webkit-overflow-scrolling:touch;padding:16px;display:none;background:var(--bg)}
.screen.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
.card-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.metric{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px}
.metric .label{font-size:11px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px}
.metric .value{font-size:24px;font-weight:700;color:var(--text)}
.metric .sub{font-size:11px;color:var(--muted);margin-top:2px}
.metric.gold .value{color:var(--gold)}
.section-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.banner{background:#1a2d1a;border:1px solid #2d5a2d;border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:13px;color:#7ec87e}
.listing-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.listing-item:last-child{border-bottom:none}
.thumb{width:52px;height:52px;border-radius:8px;object-fit:cover;background:var(--border);flex-shrink:0}
.thumb-placeholder{width:52px;height:52px;border-radius:8px;background:var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:20px}
.listing-info{flex:1;min-width:0}
.listing-title{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.listing-meta{font-size:11px;color:var(--muted);margin-top:3px}
.listing-price{font-size:14px;font-weight:700;color:var(--gold);flex-shrink:0}
.badge{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;margin-left:6px}
.badge.draft{background:#1a2030;color:#6b8ab5;border:1px solid #2a3d5a}
.badge.active{background:#1a2d1a;color:#4caf82;border:1px solid #2d5a2d}
.nav-badge{position:absolute;top:2px;margin-left:14px;background:var(--red);color:#fff;font-size:9px;font-weight:700;min-width:15px;height:15px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px}
.act-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.act-card.high{border-left-color:var(--red)}
.act-card.medium{border-left-color:var(--gold)}
.act-card.low{border-left-color:#4a6b8a}
.act-sev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px}
.act-sev.high{background:#2d1a1a;color:#e07070}
.act-sev.medium{background:#2d2a1a;color:var(--gold2)}
.act-sev.low{background:#1a2330;color:#7ba0c2}
.act-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.act-detail{font-size:12px;color:var(--muted);line-height:1.45}
.act-sug{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.act-sug b{color:var(--gold2);font-weight:600}
.act-btns{display:flex;gap:8px;margin-top:9px}
.act-btn{flex:1;text-align:center;padding:7px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}
.act-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.act-card.approval{border-left-color:var(--green);background:#13241c}
.act-sev.approval{background:#13241c;color:#5fcf9e;border:1px solid #2d5a44}
.act-btn.approve{background:var(--green);color:#06140d;border-color:var(--green)}
.act-btn.reject{color:#e08585;border-color:#5a2d2d}
.toggle-row{display:flex;gap:8px;margin-bottom:12px}
.toggle-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.toggle-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.chip-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.chip-btn{padding:6px 12px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
.chip-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.listing-detail{padding:2px 14px 12px;margin:-2px 0 10px;background:var(--card);border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;font-size:12px}
.listing-detail .drow{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)}
.listing-detail .drow:last-child{border-bottom:none}
.listing-detail .drow span{color:var(--muted)}
.listing-detail .drow b{font-weight:600;text-align:right}
#chat-wrap{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);z-index:100;display:none;flex-direction:column;background:var(--bg)}
#chat-wrap.active{display:flex}
#msgs{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px;display:flex;flex-direction:column;gap:10px;min-height:0}
.bubble{max-width:82%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;word-break:break-word}
.bubble.user{align-self:flex-end;background:var(--gold);color:#0D1B2A;border-bottom-right-radius:4px}
.bubble.bot{align-self:flex-start;background:var(--card);border:1px solid var(--border);border-bottom-left-radius:4px;white-space:pre-wrap}
.bubble.typing{color:var(--muted);font-style:italic}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 16px;scrollbar-width:none;flex-shrink:0;border-top:1px solid var(--border)}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:7px 14px;border-radius:20px;border:1px solid var(--border);background:var(--card);color:var(--muted);font-size:12px;cursor:pointer;white-space:nowrap}
.chip:active{border-color:var(--gold);color:var(--gold)}
.input-row{display:flex;gap:8px;padding:10px 16px;border-top:1px solid var(--border);background:var(--bg);flex-shrink:0}
#msg-input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:22px;padding:10px 16px;color:var(--text);font-size:15px;outline:none}
#msg-input:focus{border-color:var(--gold)}
#send-btn{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#send-btn svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.spinner{display:block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin .7s linear infinite;margin:40px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}
.star{color:var(--gold)}
#fab-top{position:fixed;bottom:calc(var(--nav) + 16px);right:16px;width:46px;height:46px;border-radius:50%;background:var(--gold);color:#0D1B2A;border:none;font-size:20px;font-weight:700;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,.55);z-index:150;line-height:1}
#fab-top.visible{display:flex}
.sug-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.sug-card .sug-p{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px;border:1px solid currentColor;display:inline-block}
.sug-card .sug-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.sug-card .sug-detail{font-size:12px;color:var(--muted);line-height:1.45}
.sug-card .sug-action{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.sug-card .sug-impact{font-size:11px;color:var(--muted);margin-top:5px}
.ceo-btn{width:100%;background:linear-gradient(135deg,var(--card) 0%,#1a2440 100%);border:1px solid var(--gold);color:var(--gold);border-radius:12px;padding:14px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:4px}
.collapse-btn{display:block;width:100%;text-align:center;padding:7px;background:none;border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:12px;cursor:pointer;margin:6px 0 10px;transition:all .15s}
.collapse-btn:active{border-color:var(--gold);color:var(--gold)}
.hub-section-btn{flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 8px;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;text-align:center}
.hub-section-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.swatch{display:inline-block;width:16px;height:16px;border-radius:4px;vertical-align:middle;margin-right:4px;flex-shrink:0;border:1px solid rgba(255,255,255,.15)}
.cred-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}
.cred-row:last-child{border-bottom:none}
.cred-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.posture-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.posture-row:last-child{border-bottom:none}
.prod-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
</style>
</head>
<body>
  <header>
    <h1>OnBrandCraftz</h1>
    <div style="text-align:right;line-height:1.4">
      <span id="hdr-sub">Dashboard</span>
      <div style="font-size:9px;color:var(--border);margin-top:1px">""" + _BUILD_ID + """</div>
    </div>
  </header>

  <div id="screen-dash" class="screen active">
    <div style="margin-bottom:8px">
      <button id="ceo-analyze-btn" class="ceo-btn" onclick="getCeoSuggestions(false)" style="display:none">
        <span>🎯</span><span>Ask Fucking Frank to Analyze</span>
      </button>
      <div id="ceo-suggestions"><div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">Fucking Frank is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div></div>
    </div>
    <div id="dash-content"><div class="spinner"></div></div>
    <div id="conv-doctor-wrap" style="margin-top:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin:16px 0 8px">
        <div style="font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">🩺 Conversion Doctor</div>
        <button id="conv-collapse-btn" onclick="toggleConvPanel(this)" style="font-size:11px;color:var(--muted);background:none;border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer">▼ Show</button>
      </div>
      <div id="conv-doctor" style="display:none"></div>
    </div>
  </div>

  <div id="screen-actions" class="screen">
    <div style="display:flex;gap:8px;margin-bottom:14px">
      <button id="batch-tag-btn" onclick="batchStageTags(this)" style="flex:1;background:var(--card);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:center">⚡ Stage All Tag Fixes</button>
    </div>
    <div id="actions-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-listings" class="screen">
    <div class="toggle-row">
      <button class="toggle-btn active" onclick="loadListings('active',this)">Active</button>
      <button class="toggle-btn" onclick="loadListings('draft',this)">Drafts</button>
    </div>
    <div id="listings-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-analytics" class="screen">
    <div class="toggle-row" id="analytics-period-row">
      <button class="toggle-btn" onclick="loadAnalytics(7,this)">7 Days</button>
      <button class="toggle-btn active" onclick="loadAnalytics(30,this)">30 Days</button>
      <button class="toggle-btn" onclick="loadAnalytics(90,this)">90 Days</button>
    </div>
    <div id="analytics-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-hub" class="screen">
    <div style="display:flex;gap:6px;margin-bottom:14px">
      <button class="hub-section-btn active" onclick="showHubSection(&apos;brand&apos;,this)">🎨 Brand</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;products&apos;,this)">📦 Products</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;files&apos;,this)">📁 Files</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;creds&apos;,this)">🔑 Creds</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;security&apos;,this)">🛡️ Security</button>
    </div>
    <div id="hub-content"><div class="spinner"></div></div>
  </div>

  <div id="chat-wrap">
    <div id="msgs"></div>
    <div class="chips">
      <span class="chip" onclick="sendChip(this)">What should I focus on?</span>
      <span class="chip" onclick="sendChip(this)">How are sales?</span>
      <span class="chip" onclick="sendChip(this)">What's my next listing?</span>
      <span class="chip" onclick="sendChip(this)">Pricing advice</span>
      <span class="chip" onclick="sendChip(this)">SEO tips</span>
    </div>
    <div class="input-row">
      <input id="msg-input" type="text" placeholder="Ask Fucking Frank…" autocomplete="off">
      <button id="send-btn" onclick="sendMsg()">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>

  <button id="fab-top" aria-label="Back to top">↑</button>

  <nav>
    <button class="active" onclick="showTab('dash',this)">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      Dash
    </button>
    <button onclick="showTab('actions',this)">
      <svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="nav-badge" class="nav-badge" style="display:none">0</span>
      Actions
    </button>
    <button onclick="showTab('analytics',this)">
      <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
      Analytics
    </button>
    <button onclick="showTab('chat',this)">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Chat
    </button>
    <button onclick="showTab('listings',this)">
      <svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      Listings
    </button>
    <button onclick="showTab('hub',this)">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      Hub
    </button>
  </nav>

<script>
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
const TOKEN = """ + json.dumps(APP_TOKEN) + """;

let ws = null, wsReady = false, pendingMsg = null;
let _wsHeartbeat = null, _wsReconnectTimer = null, _wsRetries = 0, _wsManualClose = false;
// Stable per-device chat session so Frank's memory survives reconnects & reloads.
const CHAT_SESSION = (function(){
  let s = null;
  try { s = localStorage.getItem('chatSession'); } catch(e) {}
  if (!s) {
    s = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
        : 'sess-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    try { localStorage.setItem('chatSession', s); } catch(e) {}
  }
  return s;
})();
let _analyticsDays = 30;
let _onListings = false;

function showTab(tab, btn) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('chat-wrap').classList.remove('active');
  btn.classList.add('active');
  document.getElementById('hdr-sub').textContent = {dash:'Dashboard',actions:'Action Center',analytics:'Analytics',chat:'Chat',listings:'Listings',hub:'Hub'}[tab];
  _onListings = (tab === 'listings');
  if (!_onListings) { const fab=document.getElementById('fab-top'); if(fab)fab.classList.remove('visible'); }
  if (tab === 'chat') {
    document.getElementById('chat-wrap').classList.add('active');
    if (!ws) initWS();
  } else {
    document.getElementById('screen-' + tab).classList.add('active');
    if (tab === 'listings') loadListings('active', document.querySelector('.toggle-btn'));
    if (tab === 'actions') loadActions();
    if (tab === 'analytics') loadAnalytics(_analyticsDays);
    if (tab === 'hub') loadHub();
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fetchWithTimeout(url, opts, ms=12000){
  const c=new AbortController();
  const t=setTimeout(()=>c.abort(),ms);
  return fetch(url,{...opts,signal:c.signal}).finally(()=>clearTimeout(t));
}

// ── Action Center ────────────────────────────────────────────────────────────
let _actions = [];
let _pendingActions = [];
let _actionsSummary = {high:0,medium:0,low:0};
let _actionFilter = null; // 'high' | 'medium' | 'low' | null (= all)
function setActionBadge(summary, pending) {
  const b = document.getElementById('nav-badge');
  if (!b) return;
  const n = ((summary && summary.high) || 0) + (pending || 0);  // urgent + awaiting approval
  if (n > 0) { b.textContent = n > 99 ? '99+' : n; b.style.display = ''; }
  else { b.style.display = 'none'; }
}
function renderApproval(a) {
  const p = a.payload || {};
  let preview = '';
  if (a.type === 'update_title') preview = 'New title: ' + escHtml(p.title || '');
  else if (a.type === 'update_tags') preview = 'New tags: ' + escHtml((p.tags || []).join(', '));
  else if (a.type === 'publish_listing') preview = 'Publish draft listing ' + escHtml(String(p.listing_id || ''));
  return `<div class="act-card approval">
    <span class="act-sev approval">awaiting you</span>
    <div class="act-title">${escHtml(a.summary || a.type)}</div>
    <div class="act-detail">${preview}</div>
    <div class="act-btns">
      <button class="act-btn approve" onclick="approveAction(${a.id})">Approve &amp; Apply</button>
      ${a.type === 'publish_listing' ? `<button class="act-btn" onclick="fixDraftStage(${(p.listing_id||0)},${a.id},this)">🤖 Fix Draft</button>` : ''}
      <button class="act-btn reject" onclick="rejectAction(${a.id})">Reject</button>
    </div>
  </div>`;
}
async function approveAction(id) {
  if (!confirm('Approve and apply this change to your live Etsy listing now?')) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/approve', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 50000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    loadActions();
  } catch(e) { alert('Could not apply: ' + (e.message||e)); }
}
async function rejectAction(id) {
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/reject', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    if (!r.ok) { const d = await r.json().catch(()=>({})); throw new Error(d.detail||'HTTP '+r.status); }
    loadActions();
  } catch(e) { alert('Could not reject: ' + (e.message||e)); }
}
async function fixDraftStage(listingId, actionId, btn) {
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Fixing…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/draft/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},120000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const n = d.staged_count||0;
    btn.textContent = n > 0 ? n+' fix'+(n>1?'es':'')+' staged ✅' : '⚠️ No auto-fixes';
    if (n > 0) { btn.style.background='var(--green)'; btn.style.color='#06140d'; }
    const errNote = (d.errors&&d.errors.length) ? '\\n\\nErrors: '+d.errors.join(', ') : '';
    alert('Staged '+n+' fix'+(n!==1?'es':'')+'.\\nApprove the new fixes in Action Center, then come back to approve Publish.'+errNote);
    loadActions();
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not fix draft: '+(e.message||e));
  }
}
async function loadActions() {
  const el = document.getElementById('actions-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const [ar, qr] = await Promise.all([
      fetchWithTimeout(BASE+'/api/actions', {headers:{Authorization:'Bearer '+TOKEN}}, 25000),
      fetchWithTimeout(BASE+'/api/queue?status=pending', {headers:{Authorization:'Bearer '+TOKEN}}, 15000).catch(()=>null)
    ]);
    if (!ar.ok) { const e = await ar.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+ar.status); }
    const d = await ar.json();
    let pending = [];
    if (qr && qr.ok) { const qd = await qr.json().catch(()=>({})); pending = qd.actions || []; }
    _actions = d.actions || [];
    _pendingActions = pending;
    _actionsSummary = d.summary || {high:0,medium:0,low:0};
    setActionBadge(_actionsSummary, pending.length);
    renderActionsContent();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadActions()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setActionFilter(sev) {
  _actionFilter = (_actionFilter === sev) ? null : sev; // tap again to clear
  renderActionsContent();
}
const _SEV_COLORS = {high:'#e05555', medium:'#C9A84C', low:'#7ba0c2'};
function renderActionsContent() {
  const el = document.getElementById('actions-content');
  if (!el) return;
  const pending = _pendingActions || [];
  const s = _actionsSummary || {high:0,medium:0,low:0};
  let html = '';
  if (pending.length) {
    html += `<div class="section-title">⏳ Awaiting your approval (${pending.length})</div>`;
    html += pending.map(renderApproval).join('');
  }
  if (!_actions.length && !pending.length) { el.innerHTML = html || '<div class="empty">✅ All clear — no action items right now.</div>'; return; }
  const sevBtn = sev => {
    const active = _actionFilter === sev;
    const c = _SEV_COLORS[sev];
    const style = active
      ? `flex:1;text-align:center;padding:10px 6px;cursor:pointer;border-color:${c};background:${c}26`
      : 'flex:1;text-align:center;padding:10px 6px;cursor:pointer';
    return `<div class="metric" style="${style}" onclick="setActionFilter('${sev}')"><div class="value" style="color:${c};font-size:20px">${s[sev]||0}</div><div class="sub">${sev}${active?' ✓':''}</div></div>`;
  };
  html += `<div class="section-title">Flagged by scan${_actionFilter?` — showing ${_actionFilter} only`:''}</div><div style="display:flex;gap:8px;margin-bottom:14px">`+
    sevBtn('high')+sevBtn('medium')+sevBtn('low')+
    `</div>`;
  const filtered = _actionFilter ? _actions.filter(a => a.severity === _actionFilter) : _actions;
  if (!filtered.length) {
    html += `<div class="empty">No ${escHtml(_actionFilter)} severity items.</div>`;
  } else {
    html += filtered.map(a => {
      const i = _actions.indexOf(a);
      return `
      <div class="act-card ${escHtml(a.severity)}">
        <span class="act-sev ${escHtml(a.severity)}">${escHtml(a.severity)}</span>
        <div class="act-title">${escHtml(a.title)}</div>
        <div class="act-detail">${escHtml(a.detail)}</div>
        <div class="act-sug"><b>💡 Fix:</b> ${escHtml(a.suggestion)}</div>
        <div class="act-btns">
          <button class="act-btn primary" onclick="askActionFix(${i})">Ask CEO</button>
          ${a.url ? `<a class="act-btn" href="${escHtml(a.url)}" target="_blank">Open on Etsy</a>` : ''}
        </div>
      </div>`;
    }).join('');
  }
  el.innerHTML = html;
}
function askActionFix(i) {
  const a = _actions[i];
  if (!a) return;
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash, actions, analytics, chat, listings
  showTab('chat', chatBtn);
  const q = 'How should I fix this? ' + a.title + ' — ' + a.detail;
  const inp = document.getElementById('msg-input');
  inp.value = q;
  sendMsg();
}

// ── Dashboard ──────────────────────────────────────────────────────────────
function _dashSkeleton() {
  const hr = new Date().getHours();
  const greet = hr<12?'Good morning':hr<17?'Good afternoon':'Good evening';
  const ds = new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
  return `<div style="margin-bottom:16px"><div style="font-size:22px;font-weight:700">${greet}, Scott 👋</div><div style="color:var(--muted);font-size:13px;margin-top:4px">${ds}</div></div><div id="dash-err"></div><div class="section-title">Revenue</div><div class="card-row"><div class="metric gold"><div class="label">7-Day</div><div class="value" id="v-rev7">…</div><div class="sub" id="s-rev7">loading</div></div><div class="metric gold"><div class="label">30-Day</div><div class="value" id="v-rev30">…</div><div class="sub" id="s-rev30">loading</div></div></div><div class="section-title">Shop</div><div class="card-row"><div class="metric"><div class="label">Active</div><div class="value" id="v-active">…</div><div class="sub">listings</div></div><div class="metric"><div class="label">All-Time</div><div class="value" id="v-sales">…</div><div class="sub">sales</div></div></div><div id="m-reviews"></div><div id="dash-retry" style="display:none;text-align:center;margin-top:8px"><button onclick="fetchDashData()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
}
async function fetchDashData() {
  const setId = (id,val)=>{const e=document.getElementById(id);if(e)e.textContent=val;};
  const setErr = msg=>{const e=document.getElementById('dash-err');if(e)e.innerHTML=msg?`<div style="background:#2d1a1a;border:1px solid #5a2d2d;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:#e07070">${msg}</div>`:''};
  const showRetry = v=>{const r=document.getElementById('dash-retry');if(r)r.style.display=v?'':'none';};
  try {
    const r = await fetchWithTimeout(BASE+'/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    if (!r.ok){const err=await r.json().catch(()=>({}));throw new Error(err.detail||'HTTP '+r.status);}
    const d = await r.json();
    const o=d.orders||{},l=d.listings||{},rev=d.reviews||{},sh=d.shop||{};
    if(o.error||sh.error){setErr('⚠️ Etsy data partially unavailable');showRetry(true);}else{setErr('');showRetry(false);}
    setId('v-rev7','$'+(o.revenue_7d||0).toFixed(2));setId('s-rev7',(o.last_7_days||0)+' orders');
    setId('v-rev30','$'+(o.revenue_30d||0).toFixed(2));setId('s-rev30',(o.last_30_days||0)+' orders');
    setId('v-active',sh.active_listing_count||l.active_count||0);setId('v-sales',sh.total_sales||0);
    if(rev.avg_rating){const rEl=document.getElementById('m-reviews');if(rEl)rEl.innerHTML=`<div class="section-title">Reviews</div><div class="card"><div style="display:flex;align-items:center;gap:12px"><div style="font-size:36px;font-weight:700;color:var(--gold)">${rev.avg_rating}</div><div><div class="star">${'★'.repeat(Math.round(rev.avg_rating))}${'☆'.repeat(5-Math.round(rev.avg_rating))}</div><div style="font-size:12px;color:var(--muted);margin-top:3px">${rev.total_count||0} reviews · ${rev.five_star_pct||0}% five-star</div></div></div></div>`;}
  } catch(e) {
    setErr('⚠️ '+(e.name==='AbortError'?'Request timed out — check connection':escHtml(e.message||'Failed to load')));
    setId('v-rev7','—');setId('s-rev7','');setId('v-rev30','—');setId('s-rev30','');
    setId('v-active','—');setId('v-sales','—');
    showRetry(true);
  }
}
function loadDash() {
  document.getElementById('dash-content').innerHTML = _dashSkeleton();
  fetchDashData();
  getCeoSuggestions(false);
}

// ── Listings ───────────────────────────────────────────────────────────────
let _lastState = 'active';
let _listings = [];
let _listingState = 'active';
let _sectionFilter = null; // null = all categories
let _sectionsMap = null;   // {shop_section_id: title}, fetched once and cached client-side
let _openDetailId = null;
async function _ensureSectionsLoaded() {
  if (_sectionsMap) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/shop-sections', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const d = await r.json();
    _sectionsMap = {};
    (d.sections||[]).forEach(s => { _sectionsMap[s.shop_section_id] = s.title; });
  } catch(e) { _sectionsMap = {}; }
}
function _sectionLabel(id) {
  if (!id) return 'Uncategorized';
  return (_sectionsMap && _sectionsMap[id]) || ('Section '+id);
}
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastState = state; _listingState = state; _sectionFilter = null; _openDetailId = null;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    await _ensureSectionsLoaded();
    const r = await fetchWithTimeout(BASE+'/api/listings?state='+state, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { const err = await r.json().catch(()=>({})); throw new Error(err.detail||'HTTP '+r.status); }
    const d = await r.json();
    _listings = d.listings || [];
    renderListings();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastState)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setSectionFilter(key) {
  _sectionFilter = key;
  _openDetailId = null;
  renderListings();
}
function renderListings() {
  const el = document.getElementById('listings-content');
  if (!_listings.length) { el.innerHTML = '<div class="empty">No '+_listingState+' listings</div>'; return; }
  const seen = {}; const cats = [];
  _listings.forEach(l => {
    const key = String(l.shop_section_id || 'none');
    if (!seen[key]) { seen[key] = true; cats.push({key: key, label: _sectionLabel(l.shop_section_id)}); }
  });
  cats.sort((a,b) => a.label.localeCompare(b.label));
  let html = '';
  if (cats.length > 1) {
    html += '<div class="chip-row">';
    html += `<button class="chip-btn${_sectionFilter===null?' active':''}" onclick="setSectionFilter(null)">All (${_listings.length})</button>`;
    cats.forEach(c => {
      const n = _listings.filter(l => String(l.shop_section_id||'none')===c.key).length;
      html += `<button class="chip-btn${_sectionFilter===c.key?' active':''}" onclick="setSectionFilter('${c.key}')">${escHtml(c.label)} (${n})</button>`;
    });
    html += '</div>';
  }
  const filtered = _sectionFilter===null ? _listings : _listings.filter(l => String(l.shop_section_id||'none')===_sectionFilter);
  if (!filtered.length) { html += '<div class="empty">No listings in this category</div>'; el.innerHTML = html; return; }
  html += filtered.map(l => `
    <div class="listing-item" style="cursor:pointer" onclick="toggleListingDetail(${l.listing_id})">
      ${l.thumbnail_url ? `<img class="thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy">` : `<div class="thumb-placeholder">🏷️</div>`}
      <div class="listing-info">
        <div class="listing-title">${escHtml(l.title)}</div>
        <div class="listing-meta">${l.views} views · ${l.num_favorers} ♥${l.sales!=null?' · '+l.sales+' sold':''}<span class="badge ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
      </div>
      <div class="listing-price">$${(+l.price||0).toFixed(2)}</div>
    </div>
    <div id="detail-${l.listing_id}" class="listing-detail" style="display:none"></div>`).join('');
  el.innerHTML = html;
}
async function toggleListingDetail(listingId) {
  const panel = document.getElementById('detail-'+listingId);
  if (!panel) return;
  if (_openDetailId !== null && _openDetailId !== listingId) {
    const prev = document.getElementById('detail-'+_openDetailId);
    if (prev) prev.style.display = 'none';
  }
  if (_openDetailId === listingId) { panel.style.display = 'none'; _openDetailId = null; return; }
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  panel.style.display = 'block';
  _openDetailId = listingId;
  panel.innerHTML =
    `<div class="drow"><span>Listing ID</span><b>${listingId}</b></div>`+
    `<div class="drow"><span>Category</span><b>${escHtml(_sectionLabel(l.shop_section_id))}</b></div>`+
    `<div class="drow"><span>Views</span><b>${l.views}</b></div>`+
    `<div class="drow"><span>Favorites</span><b>${l.num_favorers}</b></div>`+
    (l.sales!=null ? `<div class="drow"><span>Sold</span><b>${l.sales}</b></div>` : '')+
    (l.conversion_pct!=null ? `<div class="drow"><span>Conversion</span><b>${l.conversion_pct}%</b></div>` : '')+
    `<div class="drow"><span>Price</span><b>$${(+l.price||0).toFixed(2)}</b></div>`+
    `<div id="files-${listingId}"><div class="drow"><span>Digital files</span><b>loading…</b></div></div>`+
    `<div style="margin-top:8px;text-align:right"><a href="${escHtml(l.url)}" target="_blank" style="color:var(--gold);font-size:12px;text-decoration:none" onclick="event.stopPropagation()">Open on Etsy ↗</a></div>`;
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/files', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const slot = document.getElementById('files-'+listingId);
    if (!slot) return;
    if (!r.ok) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>unavailable</b></div>'; return; }
    const d = await r.json();
    const files = d.files || [];
    if (!files.length) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>none attached</b></div>'; return; }
    slot.innerHTML = files.map(f => `<div class="drow"><span>📄 ${escHtml(f.filename||'file')}</span><b>${escHtml(f.size_human||'')}</b></div>`).join('');
  } catch(e) {
    const slot = document.getElementById('files-'+listingId);
    if (slot) slot.innerHTML = '<div class="drow"><span>Digital files</span><b>failed to load</b></div>';
  }
}

// ── Chat ───────────────────────────────────────────────────────────────────
function _clearStreaming(fallback) {
  const s = document.getElementById('bot-streaming');
  if (!s) return;
  s.id = '';
  s.classList.remove('typing');
  if (!s.textContent.trim() && fallback) s.textContent = fallback;
}
function _stopHeartbeat() { if (_wsHeartbeat) { clearInterval(_wsHeartbeat); _wsHeartbeat = null; } }
function initWS() {
  if (_wsReconnectTimer) { clearTimeout(_wsReconnectTimer); _wsReconnectTimer = null; }
  _wsManualClose = false;
  ws = new WebSocket(WS_BASE + '/ws/chat?token=' + TOKEN + '&session=' + encodeURIComponent(CHAT_SESSION));
  ws.onopen = () => {
    wsReady = true; _wsRetries = 0;
    // Heartbeat keeps the socket warm through mobile carrier/proxy idle timeouts
    // (otherwise an idle socket dies in ~30-60s and the next message hits a dead pipe).
    _stopHeartbeat();
    _wsHeartbeat = setInterval(() => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({type:'ping'})); }, 25000);
    if (pendingMsg) { ws.send(JSON.stringify({message:pendingMsg, session:CHAT_SESSION})); pendingMsg=null; }
  };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'pong') return;
    const bot = document.getElementById('bot-streaming');
    if (d.type === 'tool' && bot) {
      bot.classList.add('typing');
      if (!bot.dataset.real) bot.textContent = '⚙ ' + d.content;
      scrollMsgs();
    } else if (d.type === 'chunk' && bot) {
      if (!bot.dataset.real) { bot.textContent = ''; bot.dataset.real = '1'; bot.classList.remove('typing'); }
      bot.textContent += d.content; scrollMsgs();
    } else if (d.type === 'done') { _clearStreaming(); scrollMsgs(); }
    else if (d.type === 'error') { _clearStreaming(); addBubble('⚠️ ' + d.content, 'bot'); }
  };
  ws.onerror = () => { _clearStreaming(); };
  ws.onclose = e => {
    wsReady = false; ws = null; _stopHeartbeat();
    _clearStreaming();
    if (e.code === 4001) { addBubble('Auth failed — reload to reconnect', 'bot'); return; }
    // Auto-reconnect with capped backoff. Frank's memory is server-side (keyed by
    // CHAT_SESSION), so reconnecting silently resumes the same thread — no context lost.
    if (!_wsManualClose) {
      _wsRetries = Math.min(_wsRetries + 1, 5);
      const delay = Math.min(1000 * Math.pow(2, _wsRetries - 1), 15000);
      _wsReconnectTimer = setTimeout(() => { if (!ws) initWS(); }, delay);
    }
  };
}
function addBubble(text, who) {
  const el = document.createElement('div');
  el.className = 'bubble ' + who;
  el.textContent = text;
  document.getElementById('msgs').appendChild(el);
  scrollMsgs();
  return el;
}
function scrollMsgs() { const m=document.getElementById('msgs'); m.scrollTop=m.scrollHeight; }
function sendMsg() {
  const inp = document.getElementById('msg-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  addBubble(text, 'user');
  const bot = addBubble('', 'bot typing');
  bot.id = 'bot-streaming';
  bot.textContent = '';
  if (wsReady) { ws.send(JSON.stringify({message:text})); }
  else { pendingMsg = text; if(!ws) initWS(); }
}
function sendChip(el) { document.getElementById('msg-input').value = el.textContent; sendMsg(); }
document.getElementById('msg-input').addEventListener('keydown', e => { if(e.key==='Enter') sendMsg(); });

// ── Analytics ──────────────────────────────────────────────────────────────
function buildSparkline(values, color, h) {
  h = h || 64;
  values = (values || []).filter(function(v){ return v != null && !isNaN(v); });
  if (values.length < 2) return '<div style="height:'+h+'px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px">📈 Accumulating daily data…</div>';
  var W=320,H=h,mn=Math.min.apply(null,values),mx=Math.max.apply(null,values),range=mx-mn||1,pad=4;
  var pts=values.map(function(v,i){return [pad+(i/(values.length-1))*(W-pad*2), H-pad-((v-mn)/range)*(H-pad*2)];});
  var poly=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
  var area='M'+pts[0][0].toFixed(1)+','+H+' '+pts.map(function(p){return 'L'+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ')+' L'+pts[pts.length-1][0].toFixed(1)+','+H+' Z';
  var gid='sg'+Math.random().toString(36).slice(2,8);
  return '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;display:block;overflow:visible">'+
    '<defs><linearGradient id="'+gid+'" x1="0" y1="0" x2="0" y2="1">'+
    '<stop offset="0%" stop-color="'+color+'" stop-opacity="0.25"/>'+
    '<stop offset="100%" stop-color="'+color+'" stop-opacity="0"/>'+
    '</linearGradient></defs>'+
    '<path d="'+area+'" fill="url(#'+gid+')"/>'+
    '<polyline points="'+poly+'" fill="none" stroke="'+color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'+
    '<circle cx="'+pts[pts.length-1][0].toFixed(1)+'" cy="'+pts[pts.length-1][1].toFixed(1)+'" r="3.5" fill="'+color+'"/>'+
    '</svg>';
}
function _deltaSpan(val, isMoney) {
  if (val == null || val === 0) return '<span style="color:var(--muted)">— stable</span>';
  var pos=val>0, c=pos?'var(--green)':'var(--red)', a=pos?'↑':'↓';
  var n=isMoney?('$'+Math.abs(val).toFixed(2)):String(Math.round(Math.abs(val)));
  return '<span style="color:'+c+'">'+a+' '+n+'</span>';
}
function _renderAnalytics(d) {
  var tr=d.trends||{}, lt=d.latest||{}, del=d.delta||{}, days=d.days||30;
  var n=d.snapshot_count||0, top=d.top_listings||[];
  var html='';
  if (n < 3) {
    html+='<div style="background:#1a2030;border:1px solid #2a3d5a;border-radius:10px;padding:11px 14px;margin-bottom:14px;font-size:12px;color:#7ba0c2">📅 '+(n===0?'No snapshots yet — the hub records one daily snapshot at startup and midnight.':n+' day'+(n>1?'s':'')+' of history recorded. Trend charts fill in each day automatically.')+'</div>';
  }
  // Revenue
  var rev=lt.revenue_30d;
  html+='<div class="section-title">Revenue — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.revenue_30d,'var(--gold)');
  if (rev!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:var(--gold)">$'+rev.toFixed(2)+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">current 30-day window</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.revenue_30d,true)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Orders
  var ord=lt.orders_30d;
  html+='<div class="section-title">Orders — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.orders_30d,'#5ca8d4');
  if (ord!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:#5ca8d4">'+ord+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">orders in rolling 30 days</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.orders_30d,false)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Shop growth cards
  var acNow=lt.active_listings, salNow=lt.total_sales;
  if (acNow!=null||salNow!=null) {
    html+='<div class="section-title">Shop Growth</div><div class="card-row">';
    if (acNow!=null) html+='<div class="metric"><div class="label">Listings</div><div class="value">'+acNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.active_listings,false)+' in '+days+'d</div></div>';
    if (salNow!=null) html+='<div class="metric"><div class="label">Total Sales</div><div class="value">'+salNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.total_sales,false)+' in '+days+'d</div></div>';
    html+='</div>';
  }
  // Listing trend mini-sparkline
  var acTrend=(tr.active_listings||[]).filter(function(v){return v!=null;});
  if (acTrend.length>=2) {
    html+='<div class="card" style="padding:12px 14px 10px">'+buildSparkline(tr.active_listings,'var(--green)',40)+'<div style="font-size:11px;color:var(--muted);margin-top:5px">Active listings over time</div></div>';
  }
  // Top listings
  if (top.length) {
    html+='<div class="section-title">Top Listings by Views</div><div class="card" style="padding:12px 14px">';
    html+=top.map(function(l,i){
      // Real buy rate (sales÷views). Etsy avg is ~1-3%; 0% with views = a problem.
      var cp=l.conversion_pct||0, sold=l.sales||0;
      var convColor=cp>=2?'var(--green)':cp>=1?'var(--gold)':sold>0?'#7ba0c2':'var(--red)';
      return '<div class="listing-item" onclick="window.open(&apos;'+escHtml(l.url)+'&apos;,&apos;_blank&apos;)">'+
        '<div style="width:22px;font-size:12px;font-weight:700;color:var(--muted);flex-shrink:0">#'+(i+1)+'</div>'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:'+convColor+'">'+sold+' sold ('+cp+'%)</span></div>'+
        '</div>'+
        '<div class="listing-price">$'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>';
    }).join('');
    html+='</div>';
  } else {
    html+='<div class="section-title">Top Listings</div><div class="empty">View data will appear here once listings are active</div>';
  }
  // Footer
  var ts=lt.ts?new Date(lt.ts).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):null;
  html+='<div style="text-align:center;color:var(--muted);font-size:11px;padding:12px 0 4px">'+(ts?'Last snapshot: '+ts:'No snapshots yet')+' · '+n+' day'+(n!==1?'s':'')+' of history</div>';
  return html;
}
async function loadAnalytics(days, btn) {
  if (btn) { document.querySelectorAll('#analytics-period-row .toggle-btn').forEach(function(b){b.classList.remove('active');}); btn.classList.add('active'); }
  if (days) _analyticsDays = days;
  var el = document.getElementById('analytics-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/analytics?days='+_analyticsDays, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { var e=await r.json().catch(function(){return {};}); throw new Error(e.detail||'HTTP '+r.status); }
    var d = await r.json();
    el.innerHTML = _renderAnalytics(d);
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadAnalytics()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── CEO Analysis (structured suggestion report) ────────────────────────────
let _lastSuggestions = null;

// Silent background refresh — called after showing a cached report so the display
// updates to fresh data without ever showing a spinner. 30s timeout; fails silently.
async function _bgRefreshSuggestions() {
  try {
    var r = await fetchWithTimeout(BASE+'/api/suggestions',{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},30000);
    var d = await r.json().catch(function(){return {};});
    // Only update if we received a real, complete report (not a 202 warming stub)
    if (r.status===200 && d && Array.isArray(d.suggestions) && d.suggestions.length && !d.error) {
      var newer = !_lastSuggestions || (d.generated_at && d.generated_at > (_lastSuggestions.generated_at||''));
      if (newer) {
        _lastSuggestions = d;
        try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
        var el2 = document.getElementById('ceo-suggestions');
        if (el2) { el2.innerHTML = _renderSuggestions(d); updateChips(d); }
      }
    }
  } catch(e) {}
}
const _PCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2'};
const _PRANK  = {critical:0,high:1,medium:2,low:3};
function _renderSuggestions(d) {
  if (!d) return '';
  if (d.raw) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted)">'+escHtml(d.raw)+'</div>';
  const ts = d.generated_at ? new Date(d.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : '';
  const score = d.score;
  const scoreColor = score >= 7 ? 'var(--green)' : score >= 4 ? 'var(--gold)' : 'var(--red)';
  const scoreBg = score >= 7 ? '#13241c' : score >= 4 ? '#2d2a1a' : '#241313';
  let html = '<div class="card" style="margin-bottom:10px">';
  html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">';
  html += '<div style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px">CEO Report · ' + ts + '</div>';
  if (score) html += '<div style="background:'+scoreBg+';border:1px solid '+scoreColor+';border-radius:20px;padding:2px 10px;font-size:13px;font-weight:700;color:'+scoreColor+'">'+score+'/10</div>';
  html += '</div>';
  if (d.headline) html += '<div style="font-size:14px;line-height:1.5">'+escHtml(d.headline)+'</div>';
  html += '</div>';
  if (d.top_win || d.top_risk) {
    html += '<div class="card-row">';
    if (d.top_win)  html += '<div class="metric" style="background:#13241c;border-color:#2d5a44"><div class="label" style="color:#5fcf9e">✅ TOP WIN</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_win)+'</div></div>';
    if (d.top_risk) html += '<div class="metric" style="background:#241313;border-color:#5a2d2d"><div class="label" style="color:#e07070">⚠️ TOP RISK</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_risk)+'</div></div>';
    html += '</div>';
  }
  const sugs = (d.suggestions || []).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  if (sugs.length) {
    html += '<div class="section-title">Priorities</div>';
    sugs.forEach(function(s,i) {
      const pc = _PCOLOR[s.priority] || 'var(--muted)';
      html += '<div class="sug-card" style="border-left-color:'+pc+'">';
      html += '<span class="sug-p" style="color:'+pc+'">'+escHtml(s.priority||'medium')+'</span>';
      if (s.category) html += '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+escHtml(s.category)+'</span>';
      html += '<div class="sug-title">'+escHtml(s.title)+'</div>';
      html += '<div class="sug-detail">'+escHtml(s.detail)+'</div>';
      if (s.action) html += '<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(s.action)+'</div>';
      if (s.impact) html += '<div class="sug-impact">💡 '+escHtml(s.impact)+'</div>';
      html += '<div class="act-btns">';
      if (s.listing_id) html += '<a class="act-btn" href="https://www.etsy.com/listing/'+escHtml(String(s.listing_id))+'" target="_blank">Open Listing</a>';
      html += '<button class="act-btn primary" onclick="askSuggestionFix('+i+')">🤖 Fix It</button>';
      html += '</div></div>';
    });
  }
  html += '<div style="text-align:center;margin:8px 0 4px"><button onclick="getCeoSuggestions(true)" style="background:none;border:1px solid var(--border);border-radius:8px;padding:8px 20px;font-size:12px;color:var(--muted);cursor:pointer">↻ Refresh analysis</button></div>';
  return '<button class="collapse-btn" onclick="toggleCeoPanel(this)">▲ Collapse CEO Analysis</button><div id="ceo-body">'+html+'</div>';
}
function toggleCeoPanel(btn) {
  const el = document.getElementById('ceo-body');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse CEO Analysis' : '▼ Show CEO Analysis';
}
async function getCeoSuggestions(forceRefresh, _attempt) {
  const btn = document.getElementById('ceo-analyze-btn');
  const el  = document.getElementById('ceo-suggestions');
  if (!el) return;
  _attempt = _attempt || 0;
  // Show cached report immediately — no spinner. A silent background fetch
  // checks whether the server has a newer report and updates the display when
  // it arrives. This means the dashboard is instant on every page reload even
  // right after a Railway deploy (which wipes the server-side in-memory cache).
  if (_lastSuggestions && !forceRefresh && !_attempt) {
    if(btn)btn.style.display='none';
    el.innerHTML=_renderSuggestions(_lastSuggestions);
    updateChips(_lastSuggestions);
    setTimeout(_bgRefreshSuggestions, 1500); // silent background check for newer data
    return;
  }
  if (btn) btn.style.display = 'none';
  if (!_attempt) el.innerHTML = '<div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">Fucking Frank is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/suggestions', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 120000);
    const d = await r.json().catch(function(){return {};});
    // 202 = the report is still being computed (cold cache, e.g. just after an
    // update). Keep the spinner and poll — never block the request for a minute.
    if (r.status === 202 || (d && d.status === 'warming')) {
      if (_attempt >= 25) throw new Error('Analysis is taking longer than usual');
      setTimeout(function(){ getCeoSuggestions(forceRefresh, _attempt + 1); }, 4000);
      return;
    }
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _lastSuggestions = d;
    try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
    el.innerHTML = _renderSuggestions(d);
    updateChips(d);
  } catch(e) {
    const msg = e.name==='AbortError' ? 'Analysis timed out — try again' : escHtml(e.message||'Failed');
    el.innerHTML = '<div class="empty">'+msg+'</div><div style="text-align:center;margin-top:8px"><button onclick="getCeoSuggestions(true)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Try Again</button></div>';
    if (btn) btn.style.display = '';
  }
}
function updateChips(data) {
  const el = document.querySelector('.chips');
  if (!el) return;
  const sugs = ((data && data.suggestions) || [])
    .slice()
    .sort(function(a,b){ return (_PRANK[a.priority]||9) - (_PRANK[b.priority]||9); })
    .slice(0, 2);
  const chips = [];
  sugs.forEach(function(s) {
    if (s.title) chips.push('Fix: ' + (s.title.length > 30 ? s.title.slice(0,28)+'…' : s.title));
  });
  const fallbacks = ["What's my next listing?", 'How are sales?', 'Pricing advice', 'SEO tips', 'What should I focus on?'];
  fallbacks.forEach(function(f) { if (chips.length < 5) chips.push(f); });
  el.innerHTML = chips.slice(0, 5).map(function(c) {
    return '<span class="chip" onclick="sendChip(this)">'+escHtml(c)+'</span>';
  }).join('');
}
function askSuggestionFix(i) {
  if (!_lastSuggestions) return;
  const s = (_lastSuggestions.suggestions||[])[i];
  if (!s) return;
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash,actions,analytics,chat,listings
  showTab('chat', chatBtn);
  document.getElementById('msg-input').value = 'Help me fix this: '+s.title+' — '+s.detail;
  sendMsg();
}

// ── Conversion Doctor (views but no sales → ranked fixes) ───────────────────
const _DXCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2',trust:'var(--gold)'};
const _AREA_ICON = {photos:'📸',price:'💲',title:'🏷️',description:'📝',tags:'🔖',trust:'🤝'};
let _convTargets = [];
let _convDiagnoses = {};
function toggleConvPanel(btn) {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse' : '▼ Show';
}
function toggleDxBody(id, btn) {
  const el = document.getElementById('conv-dx-body-'+id);
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse Diagnosis' : '▼ Show Diagnosis';
}
async function fixStage(listingId, fixIdx, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '⏳ Staging…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/'+f.area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
    const rd = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
    btn.textContent = '✅ Staged — check Action Center';
    btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
    setTimeout(loadActions, 1500);
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not stage fix: '+(e.message||e));
  }
}
function fixChat(listingId, fixIdx) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const title = (d.stats&&d.stats.title)||'';
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix the '+f.area+' for listing "'+title+'": '+f.finding+' — '+f.fix;
  sendMsg();
}
async function fixAllStageable(listingId, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area==='tags'||f.area==='title';});
  if (!fixes.length) return;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Staging…';
  var staged = 0, failed = [];
  for (var i = 0; i < fixes.length; i++) {
    try {
      var r = await fetchWithTimeout(BASE+'/api/autofix/'+fixes[i].area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
      var rd = await r.json().catch(function(){return {};});
      if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
      staged++;
    } catch(e) {
      failed.push(fixes[i].area+': '+(e.message||e));
    }
  }
  btn.textContent = staged+'/'+fixes.length+' staged ✅';
  btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
  if (failed.length) alert('Some fixes could not be staged:\\n'+failed.join('\\n'));
  setTimeout(loadActions, 1500);
}
function fixAllInChat(listingId) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area!=='tags'&&f.area!=='title';});
  if (!fixes.length) return;
  const title = (d.stats&&d.stats.title)||('Listing '+listingId);
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix all issues for listing "'+title+'": '+fixes.map(function(f){return f.area+': '+f.finding+' → '+f.fix;}).join('; ');
  sendMsg();
}
async function loadConvTargets() {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/conversion-targets', {headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _convTargets = d.targets||[];
    if (!_convTargets.length) { el.innerHTML = '<div class="empty" style="padding:20px 0">✅ Nothing to fix — every viewed listing is selling (or has no views yet).</div>'; return; }
    el.innerHTML = _convTargets.map(function(l){
      return '<div class="card" style="padding:12px 14px;margin-bottom:8px">'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:var(--red)">0 sold</span> · $'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>'+
        '<div class="act-btns">'+
          '<button class="act-btn primary" onclick="diagnoseConv('+l.listing_id+',this)">🩺 Diagnose</button>'+
          '<a class="act-btn" href="'+escHtml(l.url)+'" target="_blank">Open on Etsy</a>'+
        '</div>'+
        '<div id="conv-dx-'+l.listing_id+'"></div>'+
      '</div>';
    }).join('');
    const cBtn = document.getElementById('conv-collapse-btn');
    if (cBtn) cBtn.style.display = '';
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadConvTargets()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:8px 20px;font-size:13px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
async function diagnoseConv(id, btn) {
  const out = document.getElementById('conv-dx-'+id);
  if (!out) return;
  if (btn) { btn.disabled = true; btn.textContent = '🩺 Diagnosing…'; }
  out.innerHTML = '<div class="card" style="text-align:center;padding:20px 12px;margin-top:8px"><div class="spinner" style="margin:0 auto 10px"></div><div style="color:var(--muted);font-size:12px">Reading title, price, photos, tags &amp; description…</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/diagnose/'+id, {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 90000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    out.innerHTML = _renderDiagnosis(d);
  } catch(e) {
    out.innerHTML = '<div class="empty" style="padding:14px 0">'+escHtml(e.name==='AbortError'?'Diagnosis timed out — try again':e.message||'Failed')+'</div>';
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🩺 Diagnose again'; }
  }
}
function _renderDiagnosis(d) {
  const listingId = d.listing_id;
  const dx = d.diagnosis||{}, st = d.stats||{};
  if (dx.raw && !(dx.fixes && dx.fixes.length)) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted);margin-top:8px">'+escHtml(dx.raw)+'</div>';
  const fixes = (dx.fixes||[]).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  _convDiagnoses[listingId] = Object.assign({},d,{_sortedFixes:fixes});
  let inner = '';
  inner += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;font-size:10px;color:var(--muted)">'+
    '<span>📸 '+(st.photo_count||0)+'/10</span><span>🔖 '+(st.tag_count||0)+'/13</span><span>🏷️ '+(st.title_length||0)+'/70</span><span>👁 '+(st.views||0)+'</span><span>♥ '+(st.favorites||0)+'</span><span style="color:var(--red)">🛒 '+(st.sales||0)+' sold</span></div>';
  if (dx.primary_issue) inner += '<div class="card" style="background:#241313;border-color:#5a2d2d;margin-bottom:8px"><div class="label" style="color:#e07070">⚠️ PRIMARY ISSUE</div><div style="font-size:13px;line-height:1.45;margin-top:4px">'+escHtml(dx.primary_issue)+'</div></div>';
  if (dx.summary) inner += '<div style="font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:8px">'+escHtml(dx.summary)+'</div>';
  var stageableCount = fixes.filter(function(f){return f.area==='tags'||f.area==='title';}).length;
  var chatCount = fixes.filter(function(f){return f.area!=='tags'&&f.area!=='title';}).length;
  if (stageableCount > 0 || chatCount > 0) {
    inner += '<div class="act-btns" style="margin-bottom:14px">';
    if (stageableCount > 0) inner += '<button class="act-btn primary" style="font-size:13px;padding:9px" onclick="fixAllStageable('+listingId+',this)">🚀 Stage All ('+stageableCount+')</button>';
    if (chatCount > 0) inner += '<button class="act-btn" style="font-size:13px;padding:9px" onclick="fixAllInChat('+listingId+')">💬 Chat Fixes ('+chatCount+')</button>';
    inner += '</div>';
  }
  fixes.forEach(function(f,fIdx){
    const pc = _DXCOLOR[f.priority]||'var(--muted)';
    const icon = _AREA_ICON[f.area]||'•';
    const canStage = f.area==='tags'||f.area==='title';
    inner += '<div class="sug-card" style="border-left-color:'+pc+'">'+
      '<span class="sug-p" style="color:'+pc+'">'+escHtml(f.priority||'medium')+'</span>'+
      '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+icon+' '+escHtml(f.area||'')+'</span>'+
      '<div class="sug-title">'+escHtml(f.finding||'')+'</div>'+
      (f.fix?'<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(f.fix)+'</div>':'')+
      (f.impact?'<div class="sug-impact">💡 '+escHtml(f.impact)+'</div>':'')+
      '<div class="act-btns" style="margin-top:8px">'+
      (canStage
        ? '<button class="act-btn primary" onclick="fixStage('+listingId+','+fIdx+',this)">⚡ Stage Fix</button>'
        : '<button class="act-btn" onclick="fixChat('+listingId+','+fIdx+')">💬 Fix in Chat</button>')+
      '</div>'+
    '</div>';
  });
  return '<div style="margin-top:8px">'+
    '<button class="collapse-btn" onclick="toggleDxBody('+listingId+',this)">▲ Collapse Diagnosis</button>'+
    '<div id="conv-dx-body-'+listingId+'">'+inner+'</div>'+
    '</div>';
}

// ── Hub (Brand Kit · Products · Creds · Security) ──────────────────────────
var _THEMES = [
  {id:'DP1026',name:'Lavender Dreams',primary:'#8666AA',accent:'#C4A8D4',neutral:'#FAF7FF',text:'#2C1A3A'},
  {id:'DP1027',name:'Cotton Candy',   primary:'#DE97C6',accent:'#97C6DE',neutral:'#FFF6FC',text:'#2C1A2A'},
  {id:'DP1028',name:'Midnight Blue',  primary:'#1B2568',accent:'#7BA7C2',neutral:'#F0F5FF',text:'#0D1525'},
  {id:'DP1029',name:'Coral Peach',    primary:'#FD6C49',accent:'#F5B878',neutral:'#FFF8F4',text:'#3A1A0D'}
];
var _PRODUCTS_STATIC = [
  {id:'DP1026',name:'Ultimate Life Planner',      price:'$14.99',pages:104},
  {id:'DP1027',name:'Student & School Planner',   price:'$9.99', pages:90},
  {id:'DP1028',name:'Budget & Finance Planner',   price:'$12.99',pages:102},
  {id:'DP1029',name:'Fitness & Wellness Planner', price:'$12.99',pages:91}
];
function _renderBrandKit() {
  var html = '<div class="section-title">Product Color Palettes</div>';
  _THEMES.forEach(function(t){
    html += '<div class="card" style="margin-bottom:10px">';
    html += '<div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">'+escHtml(t.id)+' — '+escHtml(t.name)+'</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    [{label:'Primary',hex:t.primary},{label:'Accent',hex:t.accent},{label:'Neutral',hex:t.neutral},{label:'Text',hex:t.text}].forEach(function(c){
      html += '<div style="display:flex;align-items:center;gap:5px">'+
        '<span class="swatch" style="background:'+escHtml(c.hex)+'"></span>'+
        '<div style="font-size:11px"><div style="color:var(--muted)">'+escHtml(c.label)+'</div>'+
        '<div style="font-family:monospace;font-size:10px;color:var(--text)">'+escHtml(c.hex)+'</div></div>'+
        '</div>';
    });
    html += '</div></div>';
  });
  html += '<div class="section-title">Listing Standards</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['Title','≤70 chars · keyword first 40 · commas not pipes'],
   ['Tags','13 tags · each ≤20 chars · multi-word buyer phrases'],
   ['Photos','10 slots · 2400×2400px · lifestyle hero first'],
   ['Price','.99 / .97 / .49 endings — never round numbers'],
   ['AI disclosure','Required in description · who_made: i_did'],
   ['File limit','20 MB per file (PDF + ZIP · Etsy hard limit)']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:10px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted);line-height:1.4">'+escHtml(r[1])+'</td></tr>';
  });
  html += '</table></div>';
  html += '<div class="section-title">Pricing Tiers</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['DP1026 Life Planner','$14.99','104 pages + sticker pack'],
   ['DP1027 Student','$9.99','90 pages · student budget'],
   ['DP1028 Budget','$12.99','102 pages · finance niche'],
   ['DP1029 Fitness','$12.99','91 pages · wellness niche'],
   ['SVG 5-pack','$9.99','5 designs · instant DL'],
   ['SVG 10+ pack','$14.99','10+ designs · instant DL']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:8px;font-weight:600">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;padding-right:8px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[1])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted)">'+escHtml(r[2])+'</td></tr>';
  });
  html += '</table></div>';
  return html;
}
function loadProductIndex() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Core Products</div>';
  _PRODUCTS_STATIC.forEach(function(p,i){
    var t = _THEMES[i]||{};
    html += '<div class="prod-card" style="border-left-color:'+(t.primary||'var(--gold)')+'">'+
      '<div style="display:flex;justify-content:space-between;align-items:flex-start">'+
        '<div><div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.4px">'+escHtml(p.id)+'</div>'+
        '<div style="font-size:14px;font-weight:600;margin-top:3px">'+escHtml(p.name)+'</div></div>'+
        '<div style="font-size:16px;font-weight:700;color:var(--gold)">'+escHtml(p.price)+'</div>'+
      '</div>'+
      '<div style="display:flex;gap:12px;margin-top:8px;font-size:11px;color:var(--muted)">'+
        '<span>📄 '+p.pages+' pages</span><span>🔖 13 tags</span><span>Digital Download</span>'+
      '</div>'+
    '</div>';
  });
  html += '<div class="section-title" style="margin-top:8px">Platform Connections</div><div class="card">';
  [
    {name:'Etsy',      icon:'🛍️',status:'live',    note:'onbrandcraftz · authorized'},
    {name:'Pinterest', icon:'📌',        status:'roadmap',note:'API v5 — ready to integrate'},
    {name:'Instagram', icon:'📷',        status:'roadmap',note:'Meta Graph API (app review needed)'},
    {name:'Facebook',  icon:'📘',        status:'roadmap',note:'Same Meta app as Instagram'},
    {name:'TikTok',    icon:'🎵',        status:'roadmap',note:'TikTok for Business API'},
    {name:'OneDrive',  icon:'☁️',        status:'roadmap',note:'Microsoft Graph — source file storage'}
  ].forEach(function(p){
    var live = p.status==='live';
    html += '<div class="cred-row">'+
      '<div style="font-size:20px;flex-shrink:0;width:28px">'+p.icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(p.name)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(p.note)+'</div></div>'+
      '<div style="font-size:11px;font-weight:700;color:'+(live?'var(--green)':'var(--muted)')+'">'+
        (live?'✅ Live':'🗺️ Roadmap')+
      '</div></div>';
  });
  html += '</div>';
  el.innerHTML = html;
}
async function loadCredentials() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/credentials/status',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var html = '<div class="card" style="margin-bottom:12px">';
    if (d.etsy_live) {
      html += '<div style="color:var(--green);font-size:15px;font-weight:700">✅ Etsy Live</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.shop_name||'onbrandcraftz')+' · token valid</div>';
    } else {
      html += '<div style="color:var(--red);font-size:15px;font-weight:700">⚠️ Etsy Ping Failed</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.etsy_live_error||'Unknown error')+' — run python tools/etsy_oauth.py</div>';
    }
    html += '</div><div class="section-title">API Credentials</div><div class="card">';
    var et=d.etsy||{}, an=d.anthropic||{}, oa=d.openai||{}, sm=d.smtp||{}, pi=d.pinterest||{};
    [
      {label:'Etsy API Key',         ok:et.api_key,         note:'ETSY_API_KEY / ETSY_CLIENT_ID'},
      {label:'Etsy Access Token',    ok:et.access_token,    note:'Expires every 1 hour — auto-refreshed'},
      {label:'Etsy Refresh Token',   ok:et.refresh_token,   note:'90-day window — re-auth via etsy_oauth.py'},
      {label:'Anthropic (Claude)',   ok:an.api_key,         note:'Fucking Frank (CEO) · Conversion Doctor · tag gen'},
      {label:'OpenAI (DALL-E)',      ok:oa.api_key,         note:'gpt-image-1 listing photo generation'},
      {label:'SMTP Email',           ok:sm.user,            note:'Post-purchase digital delivery'},
      {label:'Pinterest',            ok:pi.api_key,         note:'API v5 · roadmap'}
    ].forEach(function(c){
      var col = c.ok ? 'var(--green)' : 'var(--red)';
      html += '<div class="cred-row">'+
        '<div class="cred-dot" style="background:'+col+'"></div>'+
        '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(c.label)+'</div>'+
        '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
        '<div style="font-size:12px;font-weight:700;color:'+col+'">'+escHtml(c.ok?'Set ✓':'Not set')+'</div>'+
      '</div>';
    });
    html += '</div><div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">All tokens stored in .env — never committed to git</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadCredentials()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function _renderSecurityPosture() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Security Posture</div><div class="card">';
  [
    {ok:true, label:'.env not committed to git',           note:'Credentials stay local, never in version control'},
    {ok:true, label:'APP_SECRET_TOKEN set',                note:'Every dashboard request requires Bearer auth'},
    {ok:true, label:'Quality gate is code',                note:'Title ≤70 · tags ≤13 · validated at stage AND approve'},
    {ok:true, label:'Staged action queue',                 note:'Every Etsy change requires Scott one-tap approval'},
    {ok:null, label:'Etsy MFA enabled?',                   note:'Verify in Etsy → Account Settings → Security'},
    {ok:null, label:'Outlook 2FA active?',                 note:'Verify at account.microsoft.com → Security'},
    {ok:null, label:'Pinterest not integrated yet',        note:'No API exposure until keys are added'},
    {ok:false,label:'No per-IP rate limiting',             note:'Add nginx or Cloudflare for production hardening'},
    {ok:false,label:'Token rotation reminder needed',      note:'Etsy refresh tokens expire 90 days — set a calendar alert'}
  ].forEach(function(c){
    var icon = c.ok===true?'✅':c.ok===false?'⚠️':'❓';
    var col  = c.ok===true?'var(--green)':c.ok===false?'var(--red)':'var(--muted)';
    html += '<div class="posture-row">'+
      '<div style="font-size:16px;flex-shrink:0;width:24px">'+icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:'+col+'">'+escHtml(c.label)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
    '</div>';
  });
  html += '</div>';
  html += '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-top:4px">'+
    '<div style="font-size:12px;color:#7ba0c2;line-height:1.7">'+
    '<b style="color:var(--gold)">Re-authorize Etsy:</b> If any API call returns 401, run<br>'+
    '<code style="font-size:11px;background:#0d1525;padding:2px 8px;border-radius:4px;display:inline-block;margin-top:4px">python tools/etsy_oauth.py</code>'+
    '</div></div>';
  el.innerHTML = html;
}
function showHubSection(section, btn) {
  document.querySelectorAll('.hub-section-btn').forEach(function(b){b.classList.remove('active');});
  if (btn) btn.classList.add('active');
  if (section==='brand')         document.getElementById('hub-content').innerHTML = _renderBrandKit();
  else if (section==='products') loadProductIndex();
  else if (section==='files')    loadFiles();
  else if (section==='creds')    loadCredentials();
  else if (section==='security') _renderSecurityPosture();
}
async function loadFiles() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/files',{headers:{Authorization:'Bearer '+TOKEN}},20000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var groups = d.groups||[];
    if (!groups.length || groups.every(function(g){return !g.files.length;})) {
      el.innerHTML = '<div class="empty">No files yet.</div>';
      return;
    }
    var html = '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-bottom:12px">'+
      '<div style="font-size:12px;color:#7ba0c2;line-height:1.6">These are the actual product source files and backups living on the server '+
      '(data/digital_products/ and data/backups/) — they are not in git, so this is the only place to grab them. Tap a file to download.</div></div>';
    groups.forEach(function(g){
      if (!g.files.length) return;
      html += '<div class="section-title">'+escHtml(g.label)+' ('+g.files.length+')</div><div class="card">';
      g.files.forEach(function(f){
        var url = BASE+'/api/files/download?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+'&token='+encodeURIComponent(TOKEN);
        var when = new Date(f.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        html += '<div class="listing-item" onclick="window.open(&apos;'+url+'&apos;,&apos;_blank&apos;)" style="cursor:pointer">'+
          '<div class="thumb-placeholder">📄</div>'+
          '<div class="listing-info"><div class="listing-title">'+escHtml(f.path)+'</div>'+
          '<div class="listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+'</div></div>'+
          '<div style="color:var(--gold);font-size:18px">⬇</div>'+
        '</div>';
      });
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load files')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadFiles()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function loadHub() {
  var btns = document.querySelectorAll('.hub-section-btn');
  btns.forEach(function(b){b.classList.remove('active');});
  if (btns[0]) btns[0].classList.add('active');
  document.getElementById('hub-content').innerHTML = _renderBrandKit();
}

// ── Back to top (listings) ─────────────────────────────────────────────────
(function(){
  const fab = document.getElementById('fab-top');
  const screen = document.getElementById('screen-listings');
  if (!fab || !screen) return;
  screen.addEventListener('scroll', function(){ fab.classList.toggle('visible', _onListings && screen.scrollTop > 200); }, {passive:true});
  fab.addEventListener('click', function(){ screen.scrollTo({top:0,behavior:'smooth'}); });
})();

// ── Batch tag fix ──────────────────────────────────────────────────────────
async function batchStageTags(btn) {
  if (!confirm('Scan all active listings and stage tag fixes for every listing with fewer than 13 tags?\\n\\nThis may take up to 2 minutes. You review and approve each fix in this Action Center.')) return;
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '⏳ Generating…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/batch/stage-tags', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 180000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const errNote = d.errors && d.errors.length ? `\n${d.errors.length} listing(s) had tag-length issues and were skipped.` : '';
    alert('✅ ' + d.message + errNote);
    loadActions();
  } catch(e) {
    alert('Error: ' + (e.name==='AbortError'?'Request timed out — the batch is still running server-side; check the Action Center in a moment':(e.message||e)));
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
// Restore last CEO report from sessionStorage so the dashboard is instant on
// every page reload — no spinner needed when we already have recent data.
(function(){
  try {
    var _s = sessionStorage.getItem('obc_sug');
    if (_s) {
      var _p = JSON.parse(_s);
      if (_p && _p.generated_at && Array.isArray(_p.suggestions) && _p.suggestions.length && !_p.error) {
        var _age = Date.now() - new Date(_p.generated_at).getTime();
        if (_age < 4 * 3600 * 1000) _lastSuggestions = _p; // accept up to 4h old
      }
    }
  } catch(e) {}
})();
loadDash();
setTimeout(loadActions, 1200);  // populate Action Center + nav badge without being asked
setTimeout(loadConvTargets, 1800);  // Conversion Doctor worklist on the dashboard
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def web_ui():
    return HTMLResponse(
        content=_WEB_UI,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


# ── PWA: manifest + service worker (makes the hub installable to home screen) ─────

_MANIFEST = {
    "name": "OnBrandCraftz Hub",
    "short_name": "OnBrandCraftz",
    "description": "OnBrandCraftz Etsy operations hub — live metrics, action center, Fucking Frank (CEO agent).",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#0D1B2A",
    "theme_color": "#0D1B2A",
    "icons": [
        {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

# Network-first SW: always fresh online; caches the app shell for offline launch.
# Cache name keyed to BUILD_ID so each deploy gets a clean cache (no stale shell).
_SW_JS = (
    "const CACHE='obc-shell-" + _BUILD_ID + "';\n"
    "self.addEventListener('install',e=>self.skipWaiting());\n"
    "self.addEventListener('activate',e=>e.waitUntil((async()=>{\n"
    "  const keys=await caches.keys();\n"
    "  await Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)));\n"
    "  await self.clients.claim();\n"
    "})()));\n"
    "self.addEventListener('fetch',e=>{\n"
    "  const req=e.request;\n"
    "  if(req.method!=='GET') return;\n"
    "  e.respondWith(fetch(req).then(r=>{\n"
    "    if(req.mode==='navigate'){const cp=r.clone();caches.open(CACHE).then(c=>c.put('/',cp));}\n"
    "    return r;\n"
    "  }).catch(()=>caches.match(req).then(m=>m||caches.match('/'))));\n"
    "});\n"
)


@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(_MANIFEST, media_type="application/manifest+json")


@app.get("/sw.js")
def service_worker():
    return Response(
        content=_SW_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )


# ── Health / Diagnostics ───────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/ping")
def ping():
    """Public diagnostic endpoint — no auth. Visit this URL to confirm server state."""
    uptime_s = round((datetime.now(timezone.utc) - _SERVER_START).total_seconds())
    etsy_shop_test: str
    try:
        shop = EtsyAPIClient().get_shop()
        etsy_shop_test = f"ok — {shop.get('shop_name', '?')}"
    except Exception as exc:
        etsy_shop_test = f"error: {str(exc)[:120]}"
    return {
        "build": _BUILD_ID,
        "uptime_seconds": uptime_s,
        "env": {
            "APP_SECRET_TOKEN": bool(os.getenv("APP_SECRET_TOKEN")),
            "ETSY_ACCESS_TOKEN": bool(os.getenv("ETSY_ACCESS_TOKEN")),
            "ETSY_REFRESH_TOKEN": bool(os.getenv("ETSY_REFRESH_TOKEN")),
            "ETSY_API_KEY": bool(os.getenv("ETSY_API_KEY")),
            "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        },
        "etsy_shop_test": etsy_shop_test,
        "db": db.db_info(),
    }


# ── Data layer (shared by REST endpoints AND the CEO agent's tools) ──────────────


def _build_metrics(orders_r, reviews_r, shop_r) -> dict:
    """Pure transform of three raw Etsy responses into the dashboard snapshot.
    Each input may be an Exception (one call failed) — handled per-section."""
    now = int(time.time())
    day = 86_400
    out: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "listings": {},
        "orders": {},
        "reviews": {},
        "shop": {},
    }

    if isinstance(orders_r, Exception):
        out["orders"]["error"] = str(orders_r)
    else:
        orders = orders_r.get("results", [])

        def _revenue(order_list):
            total = 0.0
            for o in order_list:
                gt = o.get("grandtotal", {})
                if isinstance(gt, dict):
                    divisor = gt.get("divisor", 100) or 100
                    total += gt.get("amount", 0) / divisor
            return round(total, 2)

        o7 = [o for o in orders if o.get("create_timestamp", 0) > now - 7 * day]
        o30 = [o for o in orders if o.get("create_timestamp", 0) > now - 30 * day]
        out["orders"] = {
            "last_7_days": len(o7),
            "last_30_days": len(o30),
            "revenue_7d": _revenue(o7),
            "revenue_30d": _revenue(o30),
        }

    if isinstance(reviews_r, Exception):
        out["reviews"]["error"] = str(reviews_r)
    else:
        reviews = reviews_r.get("results", [])
        ratings = [r["rating"] for r in reviews if r.get("rating")]
        out["reviews"] = {
            "total_count": reviews_r.get("count", len(reviews)),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "five_star_pct": round(sum(1 for r in ratings if r == 5) / len(ratings) * 100) if ratings else 0,
        }

    if isinstance(shop_r, Exception):
        out["shop"]["error"] = str(shop_r)
    else:
        active_count = shop_r.get("listing_active_count", 0)
        out["shop"] = {
            "name": shop_r.get("shop_name", "OnBrandCraftz"),
            "active_listing_count": active_count,
            "total_sales": shop_r.get("transaction_sold_count", 0),
            "on_vacation": shop_r.get("is_vacation", False),
        }
        out["listings"]["active_count"] = active_count

    return out


def _metrics_sync() -> dict:
    """Cached business snapshot, blocking. Shared by the agent tool and the
    async endpoint (which warms/uses the same 'metrics' cache key)."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached
    client = EtsyAPIClient()
    orders_r = reviews_r = shop_r = None
    try:
        orders_r = client.get_orders(limit=100)
    except Exception as exc:
        orders_r = exc
    try:
        reviews_r = client.get_reviews(limit=50)
    except Exception as exc:
        reviews_r = exc
    try:
        shop_r = client.get_shop()
    except Exception as exc:
        shop_r = exc
    out = _build_metrics(orders_r, reviews_r, shop_r)
    _cache_set("metrics", out)
    return out


def _listings_sync(state: str = "active") -> dict:
    """Cached listing list (title/price/views/favorites/tags), blocking."""
    if state not in ("active", "draft", "inactive"):
        raise ValueError("state must be active, draft, or inactive")
    cache_key = f"listings_{state}"
    cached = _cache_get(cache_key, ttl=30)
    if cached is not None:
        return cached

    raw = EtsyAPIClient().get_shop_listings_all(state=state)
    listings = []
    for l in raw:
        images = l.get("images", [])
        thumb = ""
        if images:
            thumb = (
                images[0].get("url_570xN")
                or images[0].get("url_fullxfull")
                or images[0].get("url_75x75", "")
            )
        listings.append(
            {
                "listing_id": l.get("listing_id"),
                "title": l.get("title", ""),
                "price": _price_float(l.get("price")),
                "state": l.get("state", state),
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "tags": l.get("tags", [])[:13],
                "thumbnail_url": thumb,
                "url": f"https://www.etsy.com/listing/{l.get('listing_id')}",
                "created_timestamp": l.get("creation_timestamp", 0),
                "shop_section_id": l.get("shop_section_id"),
            }
        )
    result = {"listings": listings, "count": len(listings), "state": state}
    _cache_set(cache_key, result)
    return result


def _sales_by_listing_sync() -> dict:
    """Map real per-listing sales from paid order receipts → transactions.

    Etsy receipts each carry a `transactions` array where every transaction has
    a `listing_id` and `quantity`. Summing these gives true units sold per
    listing — the honest denominator for conversion (favorites are NOT sales).
    Based on the 100 most recent paid receipts; cached 2 min. Returns
    {listing_id: units_sold}."""
    cached = _cache_get("sales_by_listing", ttl=120)
    if cached is not None:
        return cached
    out: dict = {}
    try:
        orders_r = EtsyAPIClient().get_orders(limit=100)
        for receipt in orders_r.get("results", []) or []:
            for t in receipt.get("transactions", []) or []:
                lid = t.get("listing_id")
                if lid is None:
                    continue
                try:
                    qty = int(t.get("quantity", 1) or 1)
                except (TypeError, ValueError):
                    qty = 1
                out[lid] = out.get(lid, 0) + qty
    except Exception as exc:  # never let a sales lookup break a listing fetch
        print(f"[sales] receipt mapping failed: {exc}", flush=True)
    _cache_set("sales_by_listing", out)
    return out


def _enrich_sales(listings: list[dict]) -> list[dict]:
    """Attach real `sales` count and sales-based `conversion_pct` to each listing.

    conversion_pct = units sold ÷ views × 100 (the true buy rate). Falls back to
    0 when there are no views yet. Mutates in place and returns the list."""
    sales = _sales_by_listing_sync()
    for l in listings:
        s = sales.get(l.get("listing_id"), 0)
        v = l.get("views", 0) or 0
        l["sales"] = s
        l["conversion_pct"] = round(s / v * 100, 2) if v else 0.0
    return listings


# ── REST endpoints (thin async wrappers over the data layer) ─────────────────────


@app.get("/api/metrics")
async def get_metrics(_token: str = Depends(_auth)):
    """Live business snapshot. 3 Etsy calls in parallel; result cached 60 s."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached
    try:
        orders_r, reviews_r, shop_r = await asyncio.wait_for(
            asyncio.gather(
                asyncio.to_thread(lambda: EtsyAPIClient().get_orders(limit=100)),
                asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=50)),
                asyncio.to_thread(lambda: EtsyAPIClient().get_shop()),
                return_exceptions=True,
            ),
            timeout=10.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    out = _build_metrics(orders_r, reviews_r, shop_r)
    _cache_set("metrics", out)
    return out


@app.get("/api/listings")
async def get_listings(state: str = "active", _token: str = Depends(_auth)):
    """Return listings with thumbnail URLs. Result cached 30 s."""
    if state not in ("active", "draft", "inactive"):
        raise HTTPException(status_code=400, detail="state must be active, draft, or inactive")

    def _fetch():
        data = _listings_sync(state)
        if state == "active":  # drafts/inactive can't have sales
            _enrich_sales(data.get("listings", []))
        return data

    try:
        return await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")


def _shop_sections_sync() -> list[dict]:
    """Shop section (category) id → title map. Sections change rarely; cached 1h."""
    cached = _cache_get("shop_sections", ttl=3600)
    if cached is not None:
        return cached
    try:
        sections = EtsyAPIClient().get_shop_sections()
    except Exception as exc:  # never let a sections lookup break the listings view
        print(f"[sections] fetch failed: {exc}", flush=True)
        sections = []
    result = [
        {"shop_section_id": s.get("shop_section_id"), "title": s.get("title", "")}
        for s in sections
    ]
    _cache_set("shop_sections", result)
    return result


@app.get("/api/shop-sections")
async def shop_sections(_token: str = Depends(_auth)):
    """Shop sections (Etsy's listing categories) for the Listings filter chips."""
    try:
        sections = await asyncio.wait_for(asyncio.to_thread(_shop_sections_sync), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"sections": sections}


@app.get("/api/listings/{listing_id}/files")
async def listing_files(listing_id: int, _token: str = Depends(_auth)):
    """Digital files attached to a listing — powers the Listings tab expand-to-detail view."""
    cache_key = f"listing_files_{listing_id}"
    cached = _cache_get(cache_key, ttl=300)
    if cached is not None:
        return cached

    def _fetch():
        return EtsyAPIClient().get_listing_files(listing_id)

    try:
        raw = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    files = []
    for f in raw:
        size_bytes = f.get("size_bytes")
        files.append(
            {
                "file_id": f.get("listing_file_id"),
                "filename": f.get("filename", ""),
                "size_human": _human_size(size_bytes) if size_bytes else "",
                "rank": f.get("rank"),
                "create_timestamp": f.get("create_timestamp"),
            }
        )
    result = {"listing_id": listing_id, "count": len(files), "files": files}
    _cache_set(cache_key, result)
    return result


# ── Action Center (deterministic rules engine — surfaces priorities) ─────────────

# Severity ordering for sorting (lower = more urgent).
_SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}


def _compute_actions() -> dict:
    """Scan live drafts + active listings and return ranked action cards.

    Pure deterministic rules over data Etsy already gives us — no LLM, no
    guessing, so it is fast and never invents a problem. The CEO agent can be
    asked to expand on any card. Rules align with CLAUDE.md's 2026 standards.
    """
    now = int(time.time())
    day = 86_400
    cards: list[dict] = []

    def add(severity, category, title, detail, suggestion, listing=None):
        lid = listing.get("listing_id") if listing else None
        cards.append(
            {
                "id": f"{category}:{lid}" if lid else category,
                "severity": severity,
                "category": category,
                "title": title,
                "detail": detail,
                "suggestion": suggestion,
                "listing_id": lid,
                "url": listing.get("url") if listing else None,
                "impact": (listing or {}).get("views", 0),
            }
        )

    # Drafts awaiting publish — highest leverage, they earn nothing in draft.
    try:
        drafts = _listings_sync("draft").get("listings", [])
    except Exception as exc:
        drafts = []
        add("medium", "data_error",
            "Couldn't load drafts",
            f"Etsy draft fetch failed: {exc}",
            "Retry shortly; if it persists, check the Etsy connection on /api/ping.")
    for l in drafts:
        add("high", "draft_unpublished",
            f"Publish: {l['title'][:60]}" if l.get("title") else "Publish draft listing",
            "This listing is in draft and earning nothing while live.",
            "Run the pre-publish quality gate, then approve to publish.",
            l)

    # Active listings — SEO + conversion hygiene.
    try:
        active = _enrich_sales(_listings_sync("active").get("listings", []))
    except Exception as exc:
        active = []
        add("medium", "data_error",
            "Couldn't load active listings",
            f"Etsy active fetch failed: {exc}",
            "Retry shortly; if it persists, check the Etsy connection on /api/ping.")

    for l in active:
        title = l.get("title", "") or ""
        tags = l.get("tags", []) or []
        views = l.get("views", 0) or 0
        favs = l.get("num_favorers", 0) or 0
        sales = l.get("sales", 0) or 0
        created = l.get("created_timestamp", 0) or 0
        age_days = (now - created) / day if created else 0

        if len(title) > 70:
            add("high", "title_too_long",
                f"Title over 70 chars ({len(title)}): {title[:50]}",
                f"Title is {len(title)} characters. Etsy applies a mobile ranking "
                "penalty above 70, and 70%+ of traffic is mobile.",
                "Trim to ≤70 chars, keeping the primary keyword in the first 40.",
                l)

        if len(tags) < 13:
            add("medium", "tags_incomplete",
                f"Only {len(tags)}/13 tags: {title[:50]}",
                f"This listing uses {len(tags)} of 13 tag slots. Every empty slot "
                "is a missed ranking opportunity.",
                "Add multi-word buyer-intent tags to fill all 13 slots.",
                l)

        if views >= 25 and sales == 0:
            add("high", "low_conversion",
                f"{views} views, 0 sales: {title[:50]}",
                f"{views} people viewed this but nobody bought"
                + (f" ({favs} favorited it — interest is there)" if favs else "")
                + " — a photo, price, or description problem, not a traffic problem.",
                "Tap Diagnose in the Conversion Doctor for a ranked fix.",
                l)

        if views == 0 and age_days > 7:
            add("medium", "zero_views",
                f"No views in {int(age_days)} days: {title[:50]}",
                f"Live for {int(age_days)} days with 0 views — a visibility/SEO "
                "problem (tags or title not matching searches).",
                "Audit tags/title for buyer search terms; the agent can draft them.",
                l)

    cards.sort(key=lambda c: (_SEVERITY_RANK.get(c["severity"], 9), -c.get("impact", 0)))
    summary = {
        "high": sum(1 for c in cards if c["severity"] == "high"),
        "medium": sum(1 for c in cards if c["severity"] == "medium"),
        "low": sum(1 for c in cards if c["severity"] == "low"),
        "total": len(cards),
    }
    return {"summary": summary, "actions": cards, "timestamp": datetime.now(timezone.utc).isoformat()}


@app.get("/api/actions")
async def get_actions(_token: str = Depends(_auth)):
    """Ranked priorities computed from live listings. Cached 120 s."""
    cached = _cache_get("actions", ttl=120)
    if cached is not None:
        return cached
    try:
        data = await asyncio.wait_for(asyncio.to_thread(_compute_actions), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    _cache_set("actions", data)
    return data


# ── Persistence: daily snapshots + history ───────────────────────────────────────


async def _take_snapshot() -> str:
    """Capture today's metrics + active listings into the database (upsert/day)."""
    metrics = await asyncio.to_thread(_metrics_sync)
    listings = (await asyncio.to_thread(_listings_sync, "active")).get("listings", [])
    d = await asyncio.to_thread(db.record_metric_snapshot, metrics, listings)
    print(f"[snapshot] recorded {d}: {len(listings)} listings, persistent={db.is_persistent()}", flush=True)
    return d


async def _snapshot_loop() -> None:
    """Snapshot at startup, then once every 24h. Upsert-by-day means repeated
    runs on the same calendar day just refresh that day's row (no duplicates)."""
    while True:
        try:
            await _take_snapshot()
        except Exception as exc:
            print(f"[snapshot] error: {exc}", flush=True)
        await asyncio.sleep(86_400)


async def _warm_suggestions() -> None:
    """Keep the CEO diagnostic cache permanently warm. The synthesis takes ~60s and
    the in-memory cache is wiped on every redeploy, so without this the dashboard
    user stares at the 'analyzing your shop…' spinner for a full minute every time
    the cache is cold (seen 2026-06-16). We prime it ~5s after boot, then refresh a
    little before the TTL expires so a visitor practically never lands on a cold
    cache — only the one-time ~60s window right after a fresh deploy remains."""
    if not ANTHROPIC_KEY:
        return
    await asyncio.sleep(5)  # let the app finish booting first
    while True:
        try:
            res = await _compute_suggestions()
            if res.get("error") == "parse_failed":
                # Not cached (see _compute_suggestions) — retry soon, don't wait 30min.
                print("[warm] suggestions parse failed — retrying in 60s", flush=True)
                await asyncio.sleep(60)
                continue
            print("[warm] suggestions cache primed", flush=True)
        except Exception as exc:
            print(f"[warm] suggestions priming skipped: {exc}", flush=True)
            await asyncio.sleep(120)  # back off, then retry
            continue
        await asyncio.sleep(_SUGGESTIONS_TTL - 120)  # refresh just before expiry


async def _token_sync_loop() -> None:
    """Persist Etsy token rotations to the durable /data DB as they happen.

    tools/etsy_api.py's refresh_access_token() updates os.environ in-memory the
    moment it rotates, and tries to write .env — fine on Scott's machine, but
    Railway's filesystem is ephemeral so that write doesn't survive a restart.
    Polling os.environ here (instead of modifying etsy_api.py) keeps the fix
    isolated to this server and changes zero behavior for any other consumer
    (CI, Scott's local scripts) that imports etsy_api.py directly."""
    last_access = os.getenv("ETSY_ACCESS_TOKEN", "").strip()
    last_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
    while True:
        await asyncio.sleep(60)
        try:
            cur_access = os.getenv("ETSY_ACCESS_TOKEN", "").strip()
            cur_refresh = os.getenv("ETSY_REFRESH_TOKEN", "").strip()
            if cur_access and cur_refresh and (cur_access != last_access or cur_refresh != last_refresh):
                await asyncio.to_thread(db.save_etsy_tokens, cur_access, cur_refresh, last_refresh)
                print(f"[etsy-tokens] persisted rotated token to {db.DB_PATH}", flush=True)
                last_access, last_refresh = cur_access, cur_refresh
        except Exception as exc:
            print(f"[etsy-tokens] sync error: {exc}", flush=True)


@app.on_event("startup")
async def _startup() -> None:
    try:
        db.init_db()
        print(f"[db] ready at {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)
    except Exception as exc:
        print(f"[db] init failed: {exc}", flush=True)
    asyncio.create_task(_snapshot_loop())
    asyncio.create_task(_warm_suggestions())
    asyncio.create_task(_token_sync_loop())


@app.get("/api/history")
async def get_history(days: int = 30, _token: str = Depends(_auth)):
    """Daily shop snapshots (oldest-first) plus simple period deltas for trends."""
    days = max(1, min(days, 365))
    rows = await asyncio.to_thread(db.get_metric_history, days)
    delta = {}
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        for k in ("revenue_30d", "active_listings", "total_sales", "total_reviews", "avg_rating"):
            a, b = first.get(k), last.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                delta[k] = round(b - a, 2)
    return {"days": days, "count": len(rows), "delta": delta, "snapshots": rows}


@app.get("/api/analytics")
async def get_analytics(days: int = 30, _token: str = Depends(_auth)):
    """Trend data from daily snapshots + live top-listing performance.

    Returns parallel trend arrays (oldest→newest) for sparkline charting,
    period deltas (latest minus earliest in the window), and top 10 active
    listings ranked by all-time views with conversion rate.
    """
    days = max(7, min(days, 90))
    rows = await asyncio.to_thread(db.get_metric_history, days)

    trends = {
        "revenue_30d": [r.get("revenue_30d") for r in rows],
        "orders_30d": [r.get("orders_30d") for r in rows],
        "active_listings": [r.get("active_listings") for r in rows],
        "total_sales": [r.get("total_sales") for r in rows],
    }
    dates = [r.get("snapshot_date") for r in rows]

    delta: dict = {}
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        for k in ("revenue_30d", "orders_30d", "active_listings", "total_sales", "avg_rating"):
            a, b = first.get(k), last.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                delta[k] = round(b - a, 4)

    top_listings: list[dict] = []
    try:
        listing_data = await asyncio.wait_for(
            asyncio.to_thread(_listings_sync, "active"), timeout=15.0
        )
        active = _enrich_sales(listing_data.get("listings", []))
        top = sorted(active, key=lambda l: l.get("views", 0), reverse=True)[:10]
        top_listings = [
            {
                "listing_id": l["listing_id"],
                "title": (l.get("title") or "")[:60],
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "sales": l.get("sales", 0),
                "price": l.get("price", 0),
                "url": l.get("url", ""),
                # True buy rate: units sold ÷ views (not favorites).
                "conversion_pct": l.get("conversion_pct", 0.0),
            }
            for l in top
            if l.get("views", 0) > 0
        ]
    except Exception:
        pass

    return {
        "days": days,
        "snapshot_count": len(rows),
        "dates": dates,
        "trends": trends,
        "delta": delta,
        "latest": rows[-1] if rows else {},
        "top_listings": top_listings,
    }


# True while a CEO-diagnostic synthesis is in flight, so the endpoint and the warm
# loop never kick off two at once and the endpoint can answer "warming, poll again"
# instead of blocking a request for the full ~60s synthesis.
_suggestions_warming = False


async def _run_suggestions_safely() -> None:
    """Fire-and-forget wrapper: compute suggestions, swallow errors (they're logged
    elsewhere). Used to kick off a warm from the request path without blocking it."""
    try:
        await _compute_suggestions()
    except Exception as exc:  # noqa: BLE001
        print(f"[suggestions] background compute failed: {exc}", flush=True)


async def _compute_suggestions() -> dict:
    """Gather shop data + synthesise the CEO diagnostic JSON. Caches the result.
    Shared by the /api/suggestions endpoint and the startup cache-warmer so the
    dashboard never has to wait on a cold cache right after a deploy."""
    global _suggestions_warming
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")
    _suggestions_warming = True
    try:
        return await _compute_suggestions_inner()
    finally:
        _suggestions_warming = False


async def _compute_suggestions_inner() -> dict:
    """The actual data-gather + synthesis. Wrapped by _compute_suggestions which
    manages the _suggestions_warming flag."""
    # Gather the three data pulls DIRECTLY in Python instead of making the model
    # call them as tools. The old approach forced 3 sequential Claude round-trips
    # (call -> result -> call -> result -> call -> result -> synthesis) which took
    # ~80s on a cold cache — close enough to the frontend's 120s limit that the
    # dashboard spinner looked stuck, especially right after a deploy wiped the
    # cache (seen 2026-06-16, see ops runbook). We know exactly which 3 pulls we
    # need, so we run them concurrently and do ONE synthesis call — ~25s total.
    try:
        metrics, active, drafts = await asyncio.gather(
            asyncio.to_thread(_execute_agent_tool, "get_metrics", {}),
            asyncio.to_thread(_execute_agent_tool, "list_listings", {"state": "active"}),
            asyncio.to_thread(_execute_agent_tool, "list_listings", {"state": "draft"}),
        )
    except Exception as exc:  # noqa: BLE001 — surface a real message, not a bare 500
        raise HTTPException(status_code=502, detail=f"Could not gather shop data: {exc}")

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    user_payload = (
        "Here is the shop's real data. Analyze all of it and return the JSON report.\n\n"
        "=== METRICS ===\n" + json.dumps(metrics, default=str) + "\n\n"
        "=== ACTIVE LISTINGS ===\n" + json.dumps(active, default=str) + "\n\n"
        "=== DRAFT LISTINGS ===\n" + json.dumps(drafts, default=str)
    )

    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=4000,  # 8 detailed suggestions overrun 2400 and truncate
                    system=_SUGGESTIONS_SYSTEM + _ops_runbook_block(),
                    messages=[{"role": "user", "content": user_payload}],
                )
            ),
            timeout=90.0,  # single call; comfortably under the frontend's 120s
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Anthropic took too long to respond. This usually self-resolves — tap Try Again.",
        )
    except anthropic.APIError as exc:
        raise HTTPException(status_code=502, detail=f"Anthropic API error: {exc}")

    final_text = "".join(getattr(b, "text", "") for b in response.content)
    parsed = _extract_json_object(final_text)
    now = datetime.now(timezone.utc).isoformat()
    if not isinstance(parsed, dict):
        # Don't poison the 30-min cache with a broken parse (e.g. a truncated
        # response). Return the fallback to this caller but leave the cache cold
        # so the warm loop / next request recomputes instead of serving garbage.
        return {
            "headline": "Analysis complete",
            "suggestions": [],
            "raw": final_text,
            "error": "parse_failed",
            "generated_at": now,
        }

    parsed["generated_at"] = now
    _cache_set("suggestions", parsed)
    return parsed


@app.post("/api/suggestions")
async def get_suggestions(_token: str = Depends(_auth)):
    """CEO agent synthesises a structured JSON suggestion report from live shop
    data (metrics + active + draft listings). A background loop keeps the cache
    warm so this is normally an instant hit. If the cache IS cold (the ~75s window
    right after a deploy), we do NOT block the request for a full minute — that's
    what made the dashboard spinner look stuck. Instead we make sure a synthesis is
    running and return 202 'warming' immediately; the frontend polls until ready."""
    cached = _cache_get("suggestions", ttl=_SUGGESTIONS_TTL)
    if cached is not None:
        return cached

    if not _suggestions_warming:
        asyncio.create_task(_run_suggestions_safely())
    return JSONResponse(
        status_code=202,
        content={
            "status": "warming",
            "headline": "Analyzing your shop… first run after an update takes up to a minute.",
            "suggestions": [],
        },
    )


# ── Conversion Doctor: find traffic-but-no-sales listings + diagnose one ──────────


_CONV_TARGETS_TTL = 120  # 2-minute cache — fast enough to stay fresh, eliminates repeat Etsy API calls

@app.get("/api/conversion-targets")
async def conversion_targets(_token: str = Depends(_auth)):
    """Active listings getting views but no sales — the Conversion Doctor's worklist.

    Sorted by views descending (most wasted traffic first), top 10. Listings with
    favorites but zero sales rank as the strongest signal (proven interest, no buy).
    """
    cached = _cache_get("conv_targets", ttl=_CONV_TARGETS_TTL)
    if cached is not None:
        return cached

    def _fetch():
        active = _enrich_sales(_listings_sync("active").get("listings", []))
        targets = [l for l in active if (l.get("views", 0) or 0) > 0 and (l.get("sales", 0) or 0) == 0]
        targets.sort(key=lambda l: (l.get("num_favorers", 0) or 0, l.get("views", 0) or 0), reverse=True)
        return targets[:10]

    try:
        targets = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    result = {
        "count": len(targets),
        "targets": [
            {
                "listing_id": l["listing_id"],
                "title": l.get("title", ""),
                "views": l.get("views", 0),
                "num_favorers": l.get("num_favorers", 0),
                "sales": l.get("sales", 0),
                "price": l.get("price", 0),
                "url": l.get("url", ""),
                "thumbnail_url": l.get("thumbnail_url", ""),
            }
            for l in targets
        ],
    }
    _cache_set("conv_targets", result)
    return result


@app.post("/api/diagnose/{listing_id}")
async def diagnose_listing(listing_id: int, _token: str = Depends(_auth)):
    """Deep conversion diagnosis of ONE listing. Pulls full listing detail (title,
    price, description, tags) + photo count + real sales, then a single focused
    Claude call returns a structured, listing-specific diagnosis. Cached 10 min."""
    cache_key = f"diagnose_{listing_id}"
    cached = _cache_get(cache_key, ttl=600)
    if cached is not None:
        return cached

    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    def _gather() -> dict:
        client = EtsyAPIClient()
        listing = client.get_listing(listing_id)
        try:
            photo_count = len(client.get_listing_images(listing_id))
        except Exception:
            photo_count = 0
        sales = _sales_by_listing_sync().get(listing_id, 0)
        return {"listing": listing, "photo_count": photo_count, "sales": sales}

    try:
        gathered = await asyncio.wait_for(asyncio.to_thread(_gather), timeout=20.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")

    listing = gathered["listing"]
    title = listing.get("title", "") or ""
    tags = listing.get("tags", []) or []
    views = listing.get("views", 0) or 0
    favs = listing.get("num_favorers", 0) or 0
    sales = gathered["sales"]
    price = _price_float(listing.get("price"))
    desc = (listing.get("description", "") or "").strip()
    photo_count = gathered["photo_count"]

    stats = {
        "title": title,
        "title_length": len(title),
        "price": round(price, 2),
        "photo_count": photo_count,
        "tag_count": len(tags),
        "views": views,
        "favorites": favs,
        "sales": sales,
        "conversion_pct": round(sales / views * 100, 2) if views else 0.0,
    }

    user_payload = (
        "Diagnose why this listing isn't converting. Real data:\n\n"
        f"TITLE ({len(title)} chars): {title}\n"
        f"PRICE: ${price:.2f}\n"
        f"PHOTOS: {photo_count} of 10 recommended\n"
        f"TAGS ({len(tags)}/13): {', '.join(tags) if tags else '(none)'}\n"
        f"VIEWS: {views}   FAVORITES: {favs}   UNITS SOLD: {sales}\n\n"
        "FULL DESCRIPTION:\n"
        f"{desc[:6000] if desc else '(empty)'}\n"
    )

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=2000,
                    system=_CONVERSION_DOCTOR_SYSTEM,
                    messages=[{"role": "user", "content": user_payload}],
                )
            ),
            timeout=60.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Diagnosis timed out — try again")

    text = "".join(getattr(b, "text", "") for b in response.content).strip()
    diagnosis = _extract_json_object(text)
    if diagnosis is None:
        diagnosis = {"primary_issue": "Analysis complete", "fixes": [], "raw": text}

    result = {
        "listing_id": listing_id,
        "url": f"https://www.etsy.com/listing/{listing_id}",
        "stats": stats,
        "diagnosis": diagnosis,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    _cache_set(cache_key, result)
    return result


@app.post("/api/autofix/tags/{listing_id}")
async def autofix_tags(listing_id: int, _token: str = Depends(_auth)):
    """Generate 13 correct tags for one listing and stage an update_tags action.

    Calls Claude once for this specific listing, validates the tags through
    the quality gate, then enqueues the action for Scott's one-tap approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    def _fetch():
        return EtsyAPIClient().get_listing(listing_id)

    try:
        listing = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")

    listing_data = {
        "listing_id": listing_id,
        "title": listing.get("title", ""),
        "price": _price_float(listing.get("price")),
        "tags": listing.get("tags", []),
    }

    try:
        tag_results = await asyncio.wait_for(
            asyncio.to_thread(_generate_tags_for_listings, [listing_data]),
            timeout=60.0,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation failed: {exc}")

    if not tag_results:
        raise HTTPException(status_code=502, detail="Tag generation returned no results")

    raw_tags = tag_results[0].get("tags", [])
    tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
    seen: set = set()
    tags = [t for t in tags if t and not (t in seen or seen.add(t))]

    candidate = {"type": "update_tags", "payload": {"listing_id": listing_id, "tags": tags}}
    ok, msg = _validate_staged_action(candidate)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Quality gate: {msg}")

    title_short = (listing.get("title") or f"Listing {listing_id}")[:50]
    summary = f"Auto tag fix ({len(tags)}/13): {title_short}"
    action_id = db.enqueue_action("update_tags", summary, {"listing_id": listing_id, "tags": tags})

    with _cache_lock:
        _cache.pop("actions", None)

    return {"staged": True, "action_id": action_id, "tags": tags, "listing_id": listing_id}


@app.post("/api/autofix/title/{listing_id}")
async def autofix_title(listing_id: int, _token: str = Depends(_auth)):
    """Generate a corrected ≤70-char title and stage an update_title action.

    Calls Claude once with the listing's full context, validates through the
    quality gate (hard ≤70-char rule), then enqueues for Scott's approval.
    Nothing touches Etsy until Scott taps Approve in the Action Center."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    def _fetch():
        return EtsyAPIClient().get_listing(listing_id)

    try:
        listing = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")

    title = listing.get("title", "")
    tags = ", ".join(listing.get("tags", []))
    price = _price_float(listing.get("price"))
    desc = (listing.get("description", "") or "")[:500]

    prompt = _TITLE_FIX_PROMPT.format(
        title=title, price=f"{price:.2f}", tags=tags, desc=desc
    )

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
            ),
            timeout=30.0,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Title generation timed out")

    new_title = "".join(getattr(b, "text", "") for b in response.content).strip().strip('"\'')

    candidate = {"type": "update_title", "payload": {"listing_id": listing_id, "title": new_title}}
    ok, msg = _validate_staged_action(candidate)
    if not ok:
        raise HTTPException(status_code=422, detail=f"Quality gate: {msg}")

    summary = f"Auto title fix: {new_title[:50]}"
    action_id = db.enqueue_action("update_title", summary, {"listing_id": listing_id, "title": new_title})

    with _cache_lock:
        _cache.pop("actions", None)

    return {"staged": True, "action_id": action_id, "title": new_title, "listing_id": listing_id}


@app.post("/api/autofix/draft/{listing_id}")
async def autofix_draft(listing_id: int, _token: str = Depends(_auth)):
    """Auto-fix a draft listing's title and tags in one shot.

    Generates a corrected ≤70-char title AND a full 13-tag set, validates both
    through the quality gate, and enqueues them as separate pending approvals.
    Nothing touches Etsy until Scott taps Approve on each fix. After approving
    the fixes, Scott can then approve the original publish_listing action."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    def _fetch():
        return EtsyAPIClient().get_listing(listing_id)

    try:
        listing = await asyncio.wait_for(asyncio.to_thread(_fetch), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout")
    except EtsyAPIError as exc:
        raise HTTPException(status_code=502, detail=f"Etsy: {exc}")

    staged: list[dict] = []
    errors: list[str] = []
    title_short = (listing.get("title") or f"Listing {listing_id}")[:50]

    # ── 1. Fix tags ────────────────────────────────────────────────────────────
    listing_data = {
        "listing_id": listing_id,
        "title": listing.get("title", ""),
        "price": _price_float(listing.get("price")),
        "tags": listing.get("tags", []),
    }
    try:
        tag_results = await asyncio.wait_for(
            asyncio.to_thread(_generate_tags_for_listings, [listing_data]),
            timeout=60.0,
        )
        if tag_results:
            raw_tags = tag_results[0].get("tags", [])
            tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
            seen: set = set()
            tags = [t for t in tags if t and not (t in seen or seen.add(t))]
            candidate = {"type": "update_tags", "payload": {"listing_id": listing_id, "tags": tags}}
            ok, msg = _validate_staged_action(candidate)
            if ok:
                aid = db.enqueue_action(
                    "update_tags",
                    f"Draft tag fix ({len(tags)}/13): {title_short}",
                    {"listing_id": listing_id, "tags": tags},
                )
                staged.append({"type": "update_tags", "action_id": aid})
            else:
                errors.append(f"tags: {msg}")
    except Exception as exc:
        errors.append(f"tag gen failed: {str(exc)[:80]}")

    # ── 2. Fix title ───────────────────────────────────────────────────────────
    title = listing.get("title", "")
    tags_str = ", ".join(listing.get("tags", []))
    price = _price_float(listing.get("price"))
    desc = (listing.get("description", "") or "")[:500]
    prompt = _TITLE_FIX_PROMPT.format(title=title, price=f"{price:.2f}", tags=tags_str, desc=desc)

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    try:
        response = await asyncio.wait_for(
            asyncio.to_thread(
                lambda: ai_client.messages.create(
                    model="claude-sonnet-4-6",
                    max_tokens=100,
                    messages=[{"role": "user", "content": prompt}],
                )
            ),
            timeout=30.0,
        )
        new_title = "".join(getattr(b, "text", "") for b in response.content).strip().strip('"\'')
        candidate = {"type": "update_title", "payload": {"listing_id": listing_id, "title": new_title}}
        ok, msg = _validate_staged_action(candidate)
        if ok:
            aid = db.enqueue_action(
                "update_title",
                f"Draft title fix: {new_title[:50]}",
                {"listing_id": listing_id, "title": new_title},
            )
            staged.append({"type": "update_title", "action_id": aid, "title": new_title})
        else:
            errors.append(f"title: {msg}")
    except Exception as exc:
        errors.append(f"title gen failed: {str(exc)[:80]}")

    with _cache_lock:
        _cache.pop("actions", None)

    return {
        "staged": staged,
        "staged_count": len(staged),
        "errors": errors,
        "listing_id": listing_id,
    }


@app.post("/api/snapshot")
async def post_snapshot(_token: str = Depends(_auth)):
    """Force-capture a snapshot now (useful for testing / on-demand recording)."""
    try:
        d = await asyncio.wait_for(_take_snapshot(), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"recorded": d, "db": db.db_info()}


# ── Staged actions (agent prepares → Scott approves → server executes) ────────────

_STAGED_ACTION_TYPES = ("update_tags", "update_title", "publish_listing")


def _validate_staged_action(a: dict) -> tuple[bool, str]:
    """Quality gate run BOTH at stage time and again at approve time. The gate is
    code — a change that violates the 2026 standards can never be applied."""
    t = a.get("type")
    p = a.get("payload", {}) or {}
    if t not in _STAGED_ACTION_TYPES:
        return False, f"unsupported action type: {t}"
    if not p.get("listing_id"):
        return False, "missing listing_id"
    if t == "update_title":
        title = (p.get("title") or "").strip()
        if not title:
            return False, "title is empty"
        if len(title) > 70:
            return False, f"title is {len(title)} chars — max 70 (mobile ranking rule)"
    if t == "update_tags":
        tags = p.get("tags")
        if not isinstance(tags, list) or not tags:
            return False, "tags must be a non-empty list"
        if len(tags) > 13:
            return False, f"{len(tags)} tags — Etsy allows max 13"
        for tg in tags:
            if not isinstance(tg, str) or not tg.strip():
                return False, "tags contain an empty value"
            if len(tg) > 20:
                return False, f"tag '{tg}' exceeds 20 characters"
    return True, "ok"


def _execute_staged_action(a: dict) -> dict:
    """Apply an approved action to Etsy via update_listing, then bust caches."""
    t = a["type"]
    p = a.get("payload", {}) or {}
    lid = p["listing_id"]
    client = EtsyAPIClient()
    if t == "update_tags":
        res = client.update_listing(lid, {"tags": p["tags"]})
    elif t == "update_title":
        res = client.update_listing(lid, {"title": p["title"].strip()})
    elif t == "publish_listing":
        res = client.update_listing(lid, {"state": "active"})
    else:
        raise ValueError(f"unsupported type {t}")
    with _cache_lock:
        for k in ("listings_active", "listings_draft", "actions", "metrics"):
            _cache.pop(k, None)
    return {
        "listing_id": lid,
        "etsy": {
            "listing_id": res.get("listing_id"),
            "state": res.get("state"),
            "title": res.get("title"),
        },
    }


@app.get("/api/queue")
async def get_queue(status: str = "pending", _token: str = Depends(_auth)):
    """List staged actions. status=pending (default) or 'all'."""
    st = None if status == "all" else status
    actions = await asyncio.to_thread(db.list_actions, st)
    return {"actions": actions, "count": len(actions)}


@app.post("/api/queue/{action_id}/approve")
async def approve_action(action_id: int, _token: str = Depends(_auth)):
    """Run the quality gate, then apply the change to Etsy. Records the result."""
    a = await asyncio.to_thread(db.get_action, action_id)
    if not a:
        raise HTTPException(status_code=404, detail="action not found")
    if a["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"action already {a['status']}")
    ok, msg = _validate_staged_action(a)
    if not ok:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": f"gate failed: {msg}"})
        raise HTTPException(status_code=422, detail=f"quality gate failed: {msg}")
    try:
        result = await asyncio.wait_for(asyncio.to_thread(_execute_staged_action, a), timeout=45.0)
    except Exception as exc:
        await asyncio.to_thread(db.set_action_status, action_id, "failed", {"error": str(exc)})
        raise HTTPException(status_code=502, detail=f"Etsy execution failed: {exc}")
    await asyncio.to_thread(db.set_action_status, action_id, "executed", result)
    return {"status": "executed", "id": action_id, "result": result}


@app.post("/api/queue/{action_id}/reject")
async def reject_action(action_id: int, _token: str = Depends(_auth)):
    a = await asyncio.to_thread(db.get_action, action_id)
    if not a:
        raise HTTPException(status_code=404, detail="action not found")
    if a["status"] != "pending":
        raise HTTPException(status_code=409, detail=f"action already {a['status']}")
    await asyncio.to_thread(db.set_action_status, action_id, "rejected")
    return {"status": "rejected", "id": action_id}


# ── Batch tag fix (one Claude call → staged approvals for every under-tagged listing) ─


@app.post("/api/batch/stage-tags")
async def batch_stage_tags(_token: str = Depends(_auth)):
    """Stage tag-fix actions for every active listing that has fewer than 13 tags.

    Calls Claude once (per batch of 40) to generate a corrected 13-tag set for
    each listing, validates each against the 2026 quality gate, and enqueues the
    passing ones as pending approvals. Scott reviews and approves from the Action
    Center — nothing touches Etsy until he taps Approve."""
    if not ANTHROPIC_KEY:
        raise HTTPException(status_code=503, detail="ANTHROPIC_API_KEY not configured")

    # Fresh fetch — bypass cache so we see the real current state.
    with _cache_lock:
        _cache.pop("listings_active", None)

    try:
        data = await asyncio.wait_for(asyncio.to_thread(_listings_sync, "active"), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout fetching listings")

    listings = data.get("listings", [])
    to_fix = [l for l in listings if len(l.get("tags", [])) < 13]

    if not to_fix:
        return {
            "staged": 0,
            "skipped": 0,
            "total_checked": len(listings),
            "errors": [],
            "message": f"All {len(listings)} active listings already have 13 tags — nothing to fix!",
        }

    # One Claude API call per batch of 40 → structured JSON tag sets.
    try:
        tag_results = await asyncio.wait_for(
            asyncio.to_thread(_generate_tags_for_listings, to_fix),
            timeout=180.0,
        )
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation returned invalid JSON: {exc}")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Tag generation failed: {exc}")

    listing_map = {l["listing_id"]: l for l in to_fix}
    staged = 0
    skipped = 0
    errors: list[dict] = []

    for res in tag_results:
        lid = res.get("listing_id")
        raw_tags = res.get("tags", [])
        listing = listing_map.get(lid, {})
        title_short = (listing.get("title") or f"Listing {lid}")[:50]

        # Normalise every tag: lowercase, strip specials, cap at 20 chars.
        tags = [_clean_tag(t) for t in raw_tags if str(t).strip()]
        # Deduplicate while preserving order.
        seen: set[str] = set()
        tags = [t for t in tags if t and not (t in seen or seen.add(t))]

        candidate = {"type": "update_tags", "payload": {"listing_id": lid, "tags": tags}}
        ok, msg_str = _validate_staged_action(candidate)
        if not ok:
            errors.append({"listing_id": lid, "title": title_short, "error": msg_str})
            skipped += 1
            continue

        summary = f"Tag fix ({len(tags)}/13): {title_short}"
        db.enqueue_action("update_tags", summary, {"listing_id": lid, "tags": tags})
        staged += 1

    # Bust cached action list so the Action Center refreshes.
    with _cache_lock:
        _cache.pop("actions", None)

    return {
        "staged": staged,
        "skipped": skipped,
        "total_checked": len(to_fix),
        "errors": errors,
        "message": f"Staged {staged} tag fixes — check the Action Center to approve them.",
    }


@app.get("/api/credentials/status")
async def credentials_status(_token: str = Depends(_auth)):
    """Check which API credentials are configured and live-test the Etsy connection."""
    def _check() -> dict:
        env = os.environ
        status: dict = {
            "etsy": {
                "api_key": bool(env.get("ETSY_API_KEY") or env.get("ETSY_CLIENT_ID")),
                "access_token": bool(env.get("ETSY_ACCESS_TOKEN")),
                "refresh_token": bool(env.get("ETSY_REFRESH_TOKEN")),
            },
            "anthropic": {"api_key": bool(env.get("ANTHROPIC_API_KEY"))},
            "openai":    {"api_key": bool(env.get("OPENAI_API_KEY"))},
            "smtp":      {"user":    bool(env.get("SMTP_USER")), "password": bool(env.get("SMTP_PASSWORD"))},
            "pinterest": {"api_key": bool(env.get("PINTEREST_API_KEY") or env.get("PINTEREST_ACCESS_TOKEN"))},
            "etsy_live": False,
            "etsy_live_error": None,
            "shop_name": "",
        }
        try:
            shop = EtsyAPIClient().get_shop()
            status["etsy_live"] = True
            status["shop_name"] = shop.get("shop_name", "")
        except Exception as exc:
            status["etsy_live_error"] = str(exc)[:120]
        return status

    try:
        data = await asyncio.wait_for(asyncio.to_thread(_check), timeout=12.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy ping timed out")
    return data


# ── File hub (browse/download product files + backups straight from the dashboard) ─

_FILE_ROOTS = {
    "products": ROOT / "data" / "digital_products",
    "backups": ROOT / "data" / "backups",
}


def _human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


@app.get("/api/files")
async def list_files(_token: str = Depends(_auth)):
    """List every file under data/digital_products/ and data/backups/ so Scott can
    see and download product source files straight from the dashboard — these
    directories are gitignored (machine-local) and have no other UI."""
    groups = []
    for root_key, root_path in _FILE_ROOTS.items():
        if not root_path.exists():
            continue
        files = []
        for p in sorted(root_path.rglob("*")):
            if not p.is_file():
                continue
            stat = p.stat()
            files.append(
                {
                    "path": str(p.relative_to(root_path)),
                    "root": root_key,
                    "size": stat.st_size,
                    "size_human": _human_size(stat.st_size),
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )
        files.sort(key=lambda f: f["modified"], reverse=True)
        groups.append({"root": root_key, "label": "Backups" if root_key == "backups" else "Product Files", "files": files})
    return {"groups": groups}


@app.get("/api/files/download")
async def download_file(root: str, path: str, token: str = ""):
    """Stream a file from one of the allowed roots. Auth via ?token= (query param,
    not header) so this URL works as a plain browser/PWA download link."""
    if token != APP_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")
    base = _FILE_ROOTS.get(root)
    if base is None:
        raise HTTPException(status_code=404, detail="Unknown root")
    base = base.resolve()
    target = (base / path).resolve()
    if base not in target.parents and target != base:
        raise HTTPException(status_code=400, detail="Invalid path")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target, filename=target.name, media_type="application/octet-stream")


# ── WebSocket chat ─────────────────────────────────────────────────────────────


async def _run_agent_turn(websocket: WebSocket, ai_client, history: list[dict]) -> str:
    """One user turn: stream text, run any tools the model requests, repeat until
    the model is done. Tool calls let the CEO agent read live shop data.

    Returns the assistant's full visible text for the turn (so the caller can
    persist it to chat memory). Raises on a stream/API failure — the caller is
    responsible for rolling back this turn's additions to `history`."""
    assistant_text_parts: list[str] = []
    for _ in range(6):  # safety cap on tool round-trips per turn
        with ai_client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=_CEO_SYSTEM + _ops_runbook_block(),
            tools=AGENT_TOOLS,
            messages=history,
        ) as stream:
            for chunk in stream.text_stream:
                assistant_text_parts.append(chunk)
                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
            final = stream.get_final_message()

        # Record the assistant turn (text + any tool_use blocks) verbatim.
        history.append({"role": "assistant", "content": final.content})

        if final.stop_reason != "tool_use":
            await websocket.send_text(json.dumps({"type": "done"}))
            return "".join(assistant_text_parts).strip()

        # Execute every requested tool, then feed results back for the next round.
        # IMPORTANT: every tool_use block above is now committed to `history`. The
        # Anthropic API requires a matching tool_result for each one in the very next
        # message — if anything below raises (e.g. a flaky websocket send on a mobile
        # connection) before we append `tool_results`, every later turn in this
        # session 400s forever ("tool_use ids were found without tool_result blocks").
        # So nothing here is allowed to propagate without first recording a result.
        tool_results = []
        for block in final.content:
            if getattr(block, "type", None) == "tool_use":
                if block.name == "execute_command":
                    cmd = (block.input or {}).get("command", "command")
                    status_msg = f"⚙ Running {cmd}…"
                elif block.name == "stage_action":
                    status_msg = "📋 Staging action for approval…"
                else:
                    status_msg = f"📊 Reading {block.name}…"
                try:
                    await websocket.send_text(json.dumps({"type": "tool", "content": status_msg}))
                except Exception:
                    pass  # status update is best-effort; never let it block the tool result
                try:
                    result = await asyncio.to_thread(_execute_agent_tool, block.name, block.input)
                except Exception as exc:
                    result = {"error": str(exc)}
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    }
                )
        history.append({"role": "user", "content": tool_results})

    # Exhausted the round-trip cap — close out gracefully.
    await websocket.send_text(json.dumps({"type": "done"}))
    return "".join(assistant_text_parts).strip()


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """Streaming CEO agent chat with live-data tools. Auth via ?token= query param.

    `?session=<id>` ties the connection to a persisted conversation. On connect
    the prior thread is loaded from SQLite, so Frank keeps full context across
    mobile socket drops and Railway restarts instead of starting amnesiac every
    time the WebSocket reconnects. A {"type":"ping"} from the client is answered
    with a pong to keep the socket warm through carrier/proxy idle timeouts."""
    token = websocket.query_params.get("token", "")
    if token != APP_TOKEN:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    session_id = (websocket.query_params.get("session", "") or "").strip()[:64]

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    # Replay persisted text history so Frank resumes mid-thread after a reconnect.
    history: list[dict] = await asyncio.to_thread(db.load_chat_history, session_id) if session_id else []

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)

            if msg.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            user_text = msg.get("message", "").strip()
            if not user_text:
                continue

            # Snapshot length so a mid-turn failure can be rolled back cleanly.
            # Without this, a dangling user message (no assistant reply) leaves
            # the next turn sending two user turns back-to-back, which the API
            # rejects — wedging the chat until a full reload.
            base_len = len(history)
            history.append({"role": "user", "content": user_text})
            try:
                assistant_text = await _run_agent_turn(websocket, ai_client, history)
            except Exception as exc:
                del history[base_len:]  # roll back this turn's additions
                await websocket.send_text(json.dumps({"type": "error", "content": str(exc)}))
                continue

            # Persist only completed exchanges (text-only — see db.append_chat_message).
            if session_id:
                await asyncio.to_thread(db.append_chat_message, session_id, "user", user_text)
                if assistant_text:
                    await asyncio.to_thread(db.append_chat_message, session_id, "assistant", assistant_text)

    except WebSocketDisconnect:
        pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
