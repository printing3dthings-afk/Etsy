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

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, Security, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
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

APP_TOKEN = os.getenv("APP_SECRET_TOKEN", "")
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY", "")

if not APP_TOKEN:
    raise RuntimeError("APP_SECRET_TOKEN is not set in .env — add it before starting the server")

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

# ── Health ─────────────────────────────────────────────────────────────────────


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


# ── Metrics endpoint ───────────────────────────────────────────────────────────


@app.get("/api/metrics")
def get_metrics(_token: str = Depends(_auth)):
    """Pull live business snapshot from Etsy API."""
    client = EtsyAPIClient()
    now = int(time.time())
    day = 86_400

    out: dict = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "listings": {},
        "orders": {},
        "reviews": {},
        "shop": {},
    }

    # ── Listings ────────────────────────────────────────────────────────────
    try:
        active = client.get_shop_listings_all(state="active")
        out["listings"]["active_count"] = len(active)
        out["listings"]["active_titles"] = [l.get("title", "")[:45] for l in active[:6]]
    except Exception as exc:
        out["listings"]["active_error"] = str(exc)

    try:
        drafts = client.get_shop_listings_all(state="draft")
        out["listings"]["draft_count"] = len(drafts)
        out["listings"]["draft_titles"] = [l.get("title", "")[:45] for l in drafts[:3]]
    except Exception as exc:
        out["listings"]["draft_error"] = str(exc)

    # ── Orders / Revenue ─────────────────────────────────────────────────────
    try:
        resp = client.get_orders(limit=100)
        orders = resp.get("results", [])

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
    except Exception as exc:
        out["orders"]["error"] = str(exc)

    # ── Reviews ──────────────────────────────────────────────────────────────
    try:
        rev_resp = client.get_reviews(limit=50)
        reviews = rev_resp.get("results", [])
        ratings = [r["rating"] for r in reviews if r.get("rating")]
        out["reviews"] = {
            "total_count": rev_resp.get("count", len(reviews)),
            "avg_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "five_star_pct": round(sum(1 for r in ratings if r == 5) / len(ratings) * 100) if ratings else 0,
            "recent_sample": len(reviews),
        }
    except Exception as exc:
        out["reviews"]["error"] = str(exc)

    # ── Shop ─────────────────────────────────────────────────────────────────
    try:
        shop = client.get_shop()
        out["shop"] = {
            "name": shop.get("shop_name", "OnBrandCraftz"),
            "active_listing_count": shop.get("listing_active_count", 0),
            "total_sales": shop.get("transaction_sold_count", 0),
            "on_vacation": shop.get("is_vacation", False),
        }
    except Exception as exc:
        out["shop"]["error"] = str(exc)

    return out


# ── Listings browse endpoint ───────────────────────────────────────────────────


@app.get("/api/listings")
def get_listings(state: str = "active", _token: str = Depends(_auth)):
    """Return listings with thumbnail URLs for the mobile browser."""
    if state not in ("active", "draft", "inactive"):
        raise HTTPException(status_code=400, detail="state must be active, draft, or inactive")

    client = EtsyAPIClient()
    raw = client.get_shop_listings_all(state=state)

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

    return {"listings": listings, "count": len(listings), "state": state}


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
    uvicorn.run("tools.api_server.main:app", host="0.0.0.0", port=port, reload=False)
