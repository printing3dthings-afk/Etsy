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
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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
from etsy_api import EtsyAPIClient, EtsyAPIError  # noqa: E402

APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "changeme")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

print(f"[startup] PORT={os.getenv('PORT','?')} TOKEN_SET={bool(os.getenv('APP_SECRET_TOKEN'))} ANTHROPIC_SET={bool(ANTHROPIC_KEY)}", flush=True)

# ── App setup ──────────────────────────────────────────────────────────────────

app = FastAPI(title="OnBrandCraftz Mobile API", version="1.0.0", docs_url=None, redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
via his private mobile dashboard.

Your role:
- Answer questions about the business, products, listings, and growth strategy
- Give honest, direct assessments — no sugar-coating
- Recommend next actions and prioritize what matters most
- Uphold the shop's #1 rule: never lie to customers — every listing claim must be
  verifiable against the actual files delivered

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

# ── Web UI ─────────────────────────────────────────────────────────────────────

_WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
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
    <span id="hdr-sub">Dashboard</span>
  </header>

  <div id="screen-dash" class="screen active">
    <div id="dash-content"><div class="spinner"></div></div>
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
const TOKEN = '""" + APP_TOKEN + """';

let ws = null, wsReady = false, pendingMsg = null;

function showTab(tab, btn) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('chat-wrap').classList.remove('active');
  btn.classList.add('active');
  document.getElementById('hdr-sub').textContent = {dash:'Dashboard',chat:'Chat',listings:'Listings'}[tab];
  if (tab === 'chat') {
    document.getElementById('chat-wrap').classList.add('active');
    if (!ws) initWS();
  } else {
    document.getElementById('screen-' + tab).classList.add('active');
    if (tab === 'listings') loadListings('active', document.querySelector('.toggle-btn'));
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fetchWithTimeout(url, opts, ms=12000){
  const c=new AbortController();
  const t=setTimeout(()=>c.abort(),ms);
  return fetch(url,{...opts,signal:c.signal}).finally(()=>clearTimeout(t));
}

// ── Dashboard ──────────────────────────────────────────────────────────────
async function loadDash() {
  const el = document.getElementById('dash-content');
  try {
    const r = await fetchWithTimeout(BASE + '/api/metrics', {headers:{Authorization:'Bearer '+TOKEN}});
    const d = await r.json();
    const o = d.orders || {}, l = d.listings || {}, rev = d.reviews || {}, sh = d.shop || {};
    const hr = new Date().getHours();
    const greet = hr < 12 ? 'Good morning' : hr < 17 ? 'Good afternoon' : 'Good evening';
    let html = `<div style="margin-bottom:16px"><div style="font-size:22px;font-weight:700">${greet}, Scott 👋</div><div style="color:var(--muted);font-size:13px;margin-top:4px">${new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'})}</div></div>`;
    if (l.draft_count > 0) html += `<div class="banner">📋 ${l.draft_count} draft listing${l.draft_count>1?'s':''} ready to review</div>`;
    html += `<div class="section-title">Revenue</div><div class="card-row">`;
    html += `<div class="metric gold"><div class="label">7-Day</div><div class="value">$${(o.revenue_7d||0).toFixed(2)}</div><div class="sub">${o.last_7_days||0} orders</div></div>`;
    html += `<div class="metric gold"><div class="label">30-Day</div><div class="value">$${(o.revenue_30d||0).toFixed(2)}</div><div class="sub">${o.last_30_days||0} orders</div></div></div>`;
    html += `<div class="section-title">Shop</div><div class="card-row">`;
    html += `<div class="metric"><div class="label">Active</div><div class="value">${l.active_count||0}</div><div class="sub">listings</div></div>`;
    html += `<div class="metric"><div class="label">All-Time</div><div class="value">${sh.total_sales||0}</div><div class="sub">sales</div></div></div>`;
    if (rev.avg_rating) {
      html += `<div class="section-title">Reviews</div><div class="card"><div style="display:flex;align-items:center;gap:12px"><div style="font-size:36px;font-weight:700;color:var(--gold)">${rev.avg_rating}</div><div><div class="star">${'★'.repeat(Math.round(rev.avg_rating))}${'☆'.repeat(5-Math.round(rev.avg_rating))}</div><div style="font-size:12px;color:var(--muted);margin-top:3px">${rev.total_count||0} reviews · ${rev.five_star_pct||0}% five-star</div></div></div></div>`;
    }
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = `<div class="empty">${e.name==='AbortError'?'Request timed out — try again':'Failed to load. Check connection.'}</div>`;
  }
}

// ── Listings ───────────────────────────────────────────────────────────────
let _lastState = 'active';
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastState = state;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings?state='+state, {headers:{Authorization:'Bearer '+TOKEN}});
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
    el.innerHTML = `<div class="empty">${e.name==='AbortError'?'Request timed out — try again':'Failed to load listings'}</div>`;
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
    if (d.type === 'chunk' && bot) { bot.textContent += d.content; scrollMsgs(); }
    else if (d.type === 'done') { _clearStreaming(); scrollMsgs(); }
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
loadDash();
</script>
</body>
</html>"""


@app.get("/", response_class=HTMLResponse)
def web_ui():
    return HTMLResponse(content=_WEB_UI)


# ── Health ─────────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Metrics endpoint ───────────────────────────────────────────────────────────


@app.get("/api/metrics")
async def get_metrics(_token: str = Depends(_auth)):
    """Pull live business snapshot. All 5 Etsy calls run in parallel; result cached 60 s."""
    cached = _cache_get("metrics", ttl=60)
    if cached is not None:
        return cached

    now = int(time.time())
    day = 86_400

    # Fire all five blocking calls at the same time in a thread pool
    active_r, draft_r, orders_r, reviews_r, shop_r = await asyncio.gather(
        asyncio.to_thread(lambda: EtsyAPIClient().get_shop_listings_all(state="active")),
        asyncio.to_thread(lambda: EtsyAPIClient().get_shop_listings_all(state="draft")),
        asyncio.to_thread(lambda: EtsyAPIClient().get_orders(limit=100)),
        asyncio.to_thread(lambda: EtsyAPIClient().get_reviews(limit=50)),
        asyncio.to_thread(lambda: EtsyAPIClient().get_shop()),
        return_exceptions=True,
    )

    out: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "listings": {},
        "orders": {},
        "reviews": {},
        "shop": {},
    }

    # ── Listings ────────────────────────────────────────────────────────────
    if isinstance(active_r, Exception):
        out["listings"]["active_error"] = str(active_r)
    else:
        out["listings"]["active_count"] = len(active_r)
        out["listings"]["active_titles"] = [l.get("title", "")[:45] for l in active_r[:6]]

    if isinstance(draft_r, Exception):
        out["listings"]["draft_error"] = str(draft_r)
    else:
        out["listings"]["draft_count"] = len(draft_r)
        out["listings"]["draft_titles"] = [l.get("title", "")[:45] for l in draft_r[:3]]

    # ── Orders / Revenue ─────────────────────────────────────────────────────
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

    # ── Reviews ──────────────────────────────────────────────────────────────
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

    # ── Shop ─────────────────────────────────────────────────────────────────
    if isinstance(shop_r, Exception):
        out["shop"]["error"] = str(shop_r)
    else:
        out["shop"] = {
            "name": shop_r.get("shop_name", "OnBrandCraftz"),
            "active_listing_count": shop_r.get("listing_active_count", 0),
            "total_sales": shop_r.get("transaction_sold_count", 0),
            "on_vacation": shop_r.get("is_vacation", False),
        }

    _cache_set("metrics", out)
    return out


# ── Listings browse endpoint ───────────────────────────────────────────────────


@app.get("/api/listings")
async def get_listings(state: str = "active", _token: str = Depends(_auth)):
    """Return listings with thumbnail URLs. Result cached 30 s."""
    if state not in ("active", "draft", "inactive"):
        raise HTTPException(status_code=400, detail="state must be active, draft, or inactive")

    cache_key = f"listings_{state}"
    cached = _cache_get(cache_key, ttl=30)
    if cached is not None:
        return cached

    raw = await asyncio.to_thread(lambda: EtsyAPIClient().get_shop_listings_all(state=state))

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
                "tags": l.get("tags", [])[:5],
                "thumbnail_url": thumb,
                "url": f"https://www.etsy.com/listing/{l.get('listing_id')}",
                "created_timestamp": l.get("creation_timestamp", 0),
            }
        )

    result = {"listings": listings, "count": len(listings), "state": state}
    _cache_set(cache_key, result)
    return result


# ── WebSocket chat ─────────────────────────────────────────────────────────────


@app.websocket("/ws/chat")
async def chat_ws(websocket: WebSocket):
    """Streaming CEO agent chat. Auth via ?token= query param."""
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
            full = ""

            try:
                with ai_client.messages.stream(
                    model="claude-sonnet-4-6",
                    max_tokens=1024,
                    system=_CEO_SYSTEM,
                    messages=history,
                ) as stream:
                    for chunk in stream.text_stream:
                        full += chunk
                        await websocket.send_text(json.dumps({"type": "chunk", "content": chunk}))

                history.append({"role": "assistant", "content": full})
                await websocket.send_text(json.dumps({"type": "done"}))

            except Exception as exc:
                await websocket.send_text(json.dumps({"type": "error", "content": str(exc)}))

    except WebSocketDisconnect:
        pass


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
