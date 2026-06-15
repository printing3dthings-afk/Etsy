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
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
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

# .strip() is critical: Railway env vars set via the dashboard often carry a
# trailing newline. APP_TOKEN is injected into an inline JS string literal
# (const TOKEN = '...'); a newline inside it is a fatal SyntaxError that kills
# the ENTIRE dashboard script — the page renders but no JS runs (frozen spinner).
APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "changeme").strip()
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
_SERVER_START = datetime.now(timezone.utc)
_BUILD_ID = "a9d62f4-v9"  # bump on each deploy to confirm Railway is using latest code

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


def _cache_get(key: str, ttl: int = 60):
    with _cache_lock:
        entry = _cache.get(key)
        if entry and time.time() - entry["ts"] < ttl:
            return entry["data"]
    return None


def _cache_set(key: str, data) -> None:
    with _cache_lock:
        _cache[key] = {"data": data, "ts": time.time()}


# ── CEO Agent system prompt ────────────────────────────────────────────────────

_CEO_SYSTEM = """\
You are the CEO Agent for OnBrandCraftz, an Etsy shop selling kawaii digital planners,
sticker packs, and 3D-print SVG files. You are chatting with Scott, the shop owner,
via his private mobile dashboard. You are the operating brain of the business — Scott
relies on you so he does NOT have to dig through data or call in an engineer for answers.

Your role:
- Answer questions about the business, products, listings, and growth strategy
- Give honest, direct assessments — no sugar-coating
- Recommend next actions and prioritize what matters most
- Uphold the shop's #1 rule: never lie to customers — every listing claim must be
  verifiable against the actual files delivered

LIVE DATA — you can read the real shop, do not guess:
- Use the get_metrics tool for revenue (7d/30d), order counts, active listing count,
  total sales, and review rating.
- Use the list_listings tool to inspect listings (title, price, views, favorites, tags).
- ALWAYS pull the real numbers with a tool before quoting any figure. Never invent data.
  If a tool returns an error, say so plainly rather than guessing.

How you operate (prepare, Scott approves):
- You analyze, recommend, and can DRAFT changes (titles, tags, descriptions, photo plans,
  quality-gate checklists). You do not publish, change prices, or edit live listings
  yourself — you prepare the work and Scott approves it. Be explicit about what you'd
  change and why, so a single yes is enough to act.

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
            "List the shop's listings with title, price, views, favorites, and tags. "
            "Use to inspect what's live or in draft, find low performers, or audit SEO."
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
]


def _execute_agent_tool(name: str, tool_input: dict) -> dict:
    """Run a CEO-agent tool and return a JSON-serializable result. Read-only."""
    try:
        if name == "get_metrics":
            return _metrics_sync()
        if name == "list_listings":
            state = (tool_input or {}).get("state", "active")
            data = _listings_sync(state)
            # Trim payload for the model: drop thumbnail URLs, cap to 60 listings.
            slim = [
                {k: v for k, v in l.items() if k != "thumbnail_url"}
                for l in data.get("listings", [])[:60]
            ]
            return {"count": data.get("count"), "state": data.get("state"), "listings": slim}
        return {"error": f"unknown tool: {name}"}
    except Exception as exc:
        return {"error": str(exc)}

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
.toggle-row{display:flex;gap:8px;margin-bottom:12px}
.toggle-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.toggle-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
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
    <div id="dash-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-actions" class="screen">
    <div id="actions-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-listings" class="screen">
    <div class="toggle-row">
      <button class="toggle-btn active" onclick="loadListings('active',this)">Active</button>
      <button class="toggle-btn" onclick="loadListings('draft',this)">Drafts</button>
    </div>
    <div id="listings-content"><div class="spinner"></div></div>
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
      <input id="msg-input" type="text" placeholder="Ask your CEO agent…" autocomplete="off">
      <button id="send-btn" onclick="sendMsg()">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>

  <nav>
    <button class="active" onclick="showTab('dash',this)">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      Dashboard
    </button>
    <button onclick="showTab('actions',this)">
      <svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="nav-badge" class="nav-badge" style="display:none">0</span>
      Actions
    </button>
    <button onclick="showTab('chat',this)">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Chat
    </button>
    <button onclick="showTab('listings',this)">
      <svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      Listings
    </button>
  </nav>

<script>
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
const TOKEN = """ + json.dumps(APP_TOKEN) + """;

let ws = null, wsReady = false, pendingMsg = null;

function showTab(tab, btn) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('chat-wrap').classList.remove('active');
  btn.classList.add('active');
  document.getElementById('hdr-sub').textContent = {dash:'Dashboard',actions:'Action Center',chat:'Chat',listings:'Listings'}[tab];
  if (tab === 'chat') {
    document.getElementById('chat-wrap').classList.add('active');
    if (!ws) initWS();
  } else {
    document.getElementById('screen-' + tab).classList.add('active');
    if (tab === 'listings') loadListings('active', document.querySelector('.toggle-btn'));
    if (tab === 'actions') loadActions();
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
function setActionBadge(summary) {
  const b = document.getElementById('nav-badge');
  if (!b) return;
  const n = (summary && summary.high) || 0;  // badge = urgent (high) items only
  if (n > 0) { b.textContent = n > 99 ? '99+' : n; b.style.display = ''; }
  else { b.style.display = 'none'; }
}
async function loadActions() {
  const el = document.getElementById('actions-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/actions', {headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    _actions = d.actions || [];
    setActionBadge(d.summary || {});
    if (!_actions.length) { el.innerHTML = '<div class="empty">✅ All clear — no action items right now.</div>'; return; }
    const s = d.summary || {high:0,medium:0,low:0};
    let html = `<div style="display:flex;gap:8px;margin-bottom:14px">`+
      `<div class="metric" style="flex:1;text-align:center;padding:10px 6px"><div class="value" style="color:var(--red);font-size:20px">${s.high}</div><div class="sub">high</div></div>`+
      `<div class="metric" style="flex:1;text-align:center;padding:10px 6px"><div class="value" style="color:var(--gold);font-size:20px">${s.medium}</div><div class="sub">medium</div></div>`+
      `<div class="metric" style="flex:1;text-align:center;padding:10px 6px"><div class="value" style="color:#7ba0c2;font-size:20px">${s.low}</div><div class="sub">low</div></div>`+
      `</div>`;
    html += _actions.map((a,i) => `
      <div class="act-card ${escHtml(a.severity)}">
        <span class="act-sev ${escHtml(a.severity)}">${escHtml(a.severity)}</span>
        <div class="act-title">${escHtml(a.title)}</div>
        <div class="act-detail">${escHtml(a.detail)}</div>
        <div class="act-sug"><b>💡 Fix:</b> ${escHtml(a.suggestion)}</div>
        <div class="act-btns">
          <button class="act-btn primary" onclick="askActionFix(${i})">Ask CEO</button>
          ${a.url ? `<a class="act-btn" href="${escHtml(a.url)}" target="_blank">Open on Etsy</a>` : ''}
        </div>
      </div>`).join('');
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadActions()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function askActionFix(i) {
  const a = _actions[i];
  if (!a) return;
  const chatBtn = document.querySelectorAll('nav button')[2]; // dash, actions, chat, listings
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
}

// ── Listings ───────────────────────────────────────────────────────────────
let _lastState = 'active';
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastState = state;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings?state='+state, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { const err = await r.json().catch(()=>({})); throw new Error(err.detail||'HTTP '+r.status); }
    const d = await r.json();
    if (!d.listings || d.listings.length === 0) { el.innerHTML = '<div class="empty">No '+state+' listings</div>'; return; }
    el.innerHTML = d.listings.map(l => `
      <div class="listing-item" onclick="window.open('${escHtml(l.url)}','_blank')">
        ${l.thumbnail_url ? `<img class="thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy">` : `<div class="thumb-placeholder">🏷️</div>`}
        <div class="listing-info">
          <div class="listing-title">${escHtml(l.title)}</div>
          <div class="listing-meta">${l.views} views · ${l.num_favorers} ♥<span class="badge ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
        </div>
        <div class="listing-price">$${(+l.price||0).toFixed(2)}</div>
      </div>`).join('');
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastState)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
function initWS() {
  ws = new WebSocket(WS_BASE + '/ws/chat?token=' + TOKEN);
  ws.onopen = () => { wsReady = true; if (pendingMsg) { ws.send(JSON.stringify({message:pendingMsg})); pendingMsg=null; } };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
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
  ws.onerror = () => { _clearStreaming('(error)'); addBubble('Connection error — please reload the page', 'bot'); };
  ws.onclose = e => {
    wsReady = false; ws = null;
    _clearStreaming('(disconnected)');
    if (e.code === 4001) addBubble('Auth failed — reload to reconnect', 'bot');
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

// ── Init ───────────────────────────────────────────────────────────────────
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
loadDash();
setTimeout(loadActions, 1200);  // populate Action Center + nav badge without being asked
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
    "description": "OnBrandCraftz Etsy operations hub — live metrics, action center, CEO agent.",
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
            }
        )
    result = {"listings": listings, "count": len(listings), "state": state}
    _cache_set(cache_key, result)
    return result


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
    try:
        return await asyncio.wait_for(asyncio.to_thread(_listings_sync, state), timeout=15.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")


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
        active = _listings_sync("active").get("listings", [])
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

        if views >= 25 and favs == 0:
            add("medium", "low_conversion",
                f"{views} views, 0 favorites: {title[:50]}",
                f"{views} people viewed this but none favorited it — a photo, "
                "price, or title problem, not a traffic problem.",
                "Review the hero photo and title; ask the CEO agent for a fix.",
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


@app.on_event("startup")
async def _startup() -> None:
    try:
        db.init_db()
        print(f"[db] ready at {db.DB_PATH} (persistent={db.is_persistent()})", flush=True)
    except Exception as exc:
        print(f"[db] init failed: {exc}", flush=True)
    asyncio.create_task(_snapshot_loop())


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


@app.post("/api/snapshot")
async def post_snapshot(_token: str = Depends(_auth)):
    """Force-capture a snapshot now (useful for testing / on-demand recording)."""
    try:
        d = await asyncio.wait_for(_take_snapshot(), timeout=25.0)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Etsy API timeout — try again")
    return {"recorded": d, "db": db.db_info()}


# ── WebSocket chat ─────────────────────────────────────────────────────────────


async def _run_agent_turn(websocket: WebSocket, ai_client, history: list[dict]) -> None:
    """One user turn: stream text, run any tools the model requests, repeat until
    the model is done. Tool calls let the CEO agent read live shop data."""
    for _ in range(6):  # safety cap on tool round-trips per turn
        with ai_client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1500,
            system=_CEO_SYSTEM,
            tools=AGENT_TOOLS,
            messages=history,
        ) as stream:
            for chunk in stream.text_stream:
                await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))
            final = stream.get_final_message()

        # Record the assistant turn (text + any tool_use blocks) verbatim.
        history.append({"role": "assistant", "content": final.content})

        if final.stop_reason != "tool_use":
            await websocket.send_text(json.dumps({"type": "done"}))
            return

        # Execute every requested tool, then feed results back for the next round.
        tool_results = []
        for block in final.content:
            if getattr(block, "type", None) == "tool_use":
                await websocket.send_text(
                    json.dumps({"type": "tool", "content": f"Reading {block.name}…"})
                )
                result = await asyncio.to_thread(_execute_agent_tool, block.name, block.input)
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


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """Streaming CEO agent chat with live-data tools. Auth via ?token= query param."""
    token = websocket.query_params.get("token", "")
    if token != APP_TOKEN:
        await websocket.close(code=4001)
        return

    await websocket.accept()

    ai_client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    history: list[dict] = []

    try:
        while True:
            raw = await websocket.receive_text()
            msg = json.loads(raw)
            user_text = msg.get("message", "").strip()
            if not user_text:
                continue

            history.append({"role": "user", "content": user_text})
            try:
                await _run_agent_turn(websocket, ai_client, history)
            except Exception as exc:
                await websocket.send_text(json.dumps({"type": "error", "content": str(exc)}))

    except WebSocketDisconnect:
        pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
