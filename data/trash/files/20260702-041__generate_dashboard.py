#!/usr/bin/env python3
"""
generate_dashboard.py

Generates data/dashboard.html — a self-contained live dashboard for OnBrandCraftz.
Open the HTML file in any browser. No server required.

Run manually:   python tools/generate_dashboard.py
Cron (daily):   added automatically by this script
"""

from __future__ import annotations

import os
import sys
import json
from datetime import date, datetime
from pathlib import Path

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError

DASHBOARD_PATH = Path("data/dashboard.html")
REPORTS_DIR    = Path("data/reports")
HEALTH_LOG     = Path("data/health_log.json")
TODO_PATH      = Path("data/todo.md")
CATALOG_PATH   = Path("data/product_catalog.json")
SVG_DIR        = Path("data/svg_bundles")
FINANCIAL_PATH = Path("data/financial/profit_loss.md")

ETSY_FEE_RATE  = 0.125   # blended ~12.5% (6.5% txn + 3%+$0.25 payment)
MONTHLY_TARGET = 5000.0


# ── Data collection ───────────────────────────────────────────────────────────

def fetch_etsy_data() -> dict:
    client = EtsyAPIClient()
    data = {
        "listings": [], "orders": [], "draft_count": 0,
        "active_count": 0, "total_views": 0, "total_favs": 0,
        "error": None
    }
    try:
        resp = client._request("GET", f"shops/{client.shop_id}/listings",
            params={"state": "active", "limit": 100, "includes": "images"})
        listings = resp.get("results", [])
        data["listings"] = listings
        data["active_count"] = len(listings)
        data["total_views"] = sum(l.get("views", 0) for l in listings)
        data["total_favs"]  = sum(l.get("num_favorers", 0) for l in listings)

        draft_resp = client._request("GET", f"shops/{client.shop_id}/listings",
            params={"state": "draft", "limit": 25})
        data["draft_count"] = len(draft_resp.get("results", []))
        data["drafts"]      = draft_resp.get("results", [])
    except EtsyAPIError as e:
        data["error"] = str(e)

    try:
        order_resp = client.get_orders(limit=25)
        data["orders"] = order_resp.get("results", [])
    except Exception:
        pass

    return data


def load_health_log() -> dict:
    if not HEALTH_LOG.exists():
        return {}
    try:
        raw = json.loads(HEALTH_LOG.read_text())
        return raw[-1] if isinstance(raw, list) else raw
    except Exception:
        return {}


def load_catalog() -> list:
    if not CATALOG_PATH.exists():
        return []
    try:
        return json.loads(CATALOG_PATH.read_text())
    except Exception:
        return []


def load_svg_status() -> list:
    bundles = []
    if not SVG_DIR.exists():
        return bundles
    for manifest_path in sorted(SVG_DIR.glob("*/manifest.json")):
        try:
            m = json.loads(manifest_path.read_text())
            bundles.append({
                "name":    m.get("name", manifest_path.parent.name),
                "designs": len(m.get("designs", [])),
                "target":  m.get("target_count", 20),
                "status":  m.get("status", "unknown"),
            })
        except Exception:
            pass
    return bundles


def load_weekly_revenue() -> dict:
    """Pull the most recent weekly report for revenue data."""
    result = {"gross": 0, "net": 0, "orders": 0, "pace": 0}
    if not REPORTS_DIR.exists():
        return result
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    if not reports:
        return result
    try:
        text = reports[0].read_text()
        import re
        m = re.search(r"Gross revenue.*?\$([0-9.]+)", text)
        if m: result["gross"] = float(m.group(1))
        m = re.search(r"Net after Etsy fees.*?\$([0-9.]+)", text)
        if m: result["net"] = float(m.group(1))
        m = re.search(r"Orders.*?(\d+)", text)
        if m: result["orders"] = int(m.group(1))
        m = re.search(r"Monthly pace.*?\$([0-9,]+)", text)
        if m: result["pace"] = float(m.group(1).replace(",", ""))
    except Exception:
        pass
    return result


def audit_listing_issues(listings: list) -> list:
    """Return listings with issues — same logic as listing_performance_monitor."""
    import re
    SPECIAL = re.compile(r"[,;!?@#$%^&*()\[\]{}'\"<>/\\|=+]")
    DIGITAL_KW = {"planner", "sticker", "digital", "printable", "svg", "sublimation", "download"}

    flagged = []
    for l in listings:
        title  = l.get("title") or ""
        tags   = l.get("tags") or []
        images = l.get("images") or []
        issues = []

        if len(title) > 70:
            issues.append(f"Title {len(title)} chars (>70)")
        tl = title.lower()
        if any(k in tl for k in DIGITAL_KW) and "instant download" not in tl:
            issues.append("Missing 'Instant Download'")
        if len(tags) < 13:
            issues.append(f"Only {len(tags)}/13 tags")
        if isinstance(images, list) and len(images) < 5:
            issues.append(f"Only {len(images)} photos")

        if issues:
            flagged.append({"id": l.get("listing_id"), "title": title[:55],
                            "issues": issues, "views": l.get("views", 0)})
    return flagged


# ── Revenue by category ───────────────────────────────────────────────────────

def categorize_listings(listings: list) -> dict:
    cats: dict = {}
    for l in listings:
        t = l.get("title", "").lower()
        p_raw = l.get("price", {})
        price = p_raw.get("amount", 0) / max(p_raw.get("divisor", 100), 1) if isinstance(p_raw, dict) else float(p_raw or 0)

        if "planner" in t and "digital" in t:
            cat = "Digital Planners"
        elif "svg" in t or "cut file" in t:
            cat = "SVG Bundles"
        elif "sticker" in t:
            cat = "Sticker Packs"
        elif "sublimation" in t or "tumbler" in t:
            cat = "Sublimation"
        elif "3d print" in t or "koozie" in t or "vase" in t or "lamp" in t or "holder" in t or "centerpiece" in t:
            cat = "3D Printed"
        elif "printable" in t or "wall art" in t or "instant download" in t:
            cat = "Wall Art"
        else:
            cat = "Other"

        if cat not in cats:
            cats[cat] = {"count": 0, "avg_price": 0, "prices": [], "views": 0, "favs": 0}
        cats[cat]["count"]  += 1
        cats[cat]["prices"].append(price)
        cats[cat]["views"]  += l.get("views", 0)
        cats[cat]["favs"]   += l.get("num_favorers", 0)

    for cat, d in cats.items():
        d["avg_price"] = round(sum(d["prices"]) / len(d["prices"]), 2) if d["prices"] else 0
    return cats


# ── HTML generation ───────────────────────────────────────────────────────────

def status_dot(status: str) -> str:
    colors = {"OK": "#22c55e", "WARN": "#f59e0b", "CRITICAL": "#ef4444", "incomplete": "#f59e0b",
              "active": "#22c55e", "pending_generation": "#94a3b8", "unknown": "#94a3b8"}
    color = colors.get(status, "#94a3b8")
    return f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:{color};margin-right:6px"></span>'


def pct_bar(value: float, maximum: float, color: str = "#6366f1") -> str:
    pct = min(100, round((value / maximum) * 100)) if maximum else 0
    return f'''<div style="background:#1e293b;border-radius:4px;height:8px;width:100%">
      <div style="background:{color};border-radius:4px;height:8px;width:{pct}%"></div>
    </div><div style="color:#94a3b8;font-size:11px;margin-top:2px">{pct}% of target</div>'''


def kpi_card(label: str, value: str, sub: str = "", color: str = "#6366f1", icon: str = "") -> str:
    return f'''
    <div class="kpi-card">
      <div style="color:#94a3b8;font-size:12px;text-transform:uppercase;letter-spacing:.05em">{icon} {label}</div>
      <div style="color:#f1f5f9;font-size:28px;font-weight:700;margin:6px 0">{value}</div>
      <div style="color:#64748b;font-size:12px">{sub}</div>
    </div>'''


def generate_html(etsy: dict, health: dict, catalog: list, svg_status: list,
                  revenue: dict, flagged: list, cats: dict) -> str:
    now = datetime.now().strftime("%B %d, %Y at %I:%M %p")
    pace      = revenue.get("pace", 0)
    pace_pct  = round((pace / MONTHLY_TARGET) * 100)
    pace_color = "#22c55e" if pace_pct >= 80 else "#f59e0b" if pace_pct >= 40 else "#ef4444"

    # Health checks table
    health_rows = ""
    for r in health.get("results", []):
        dot = status_dot(r.get("status", "unknown"))
        detail = r.get("detail", "")[:90]
        health_rows += f"<tr><td>{dot}{r.get('name','')}</td><td style='color:#94a3b8;font-size:12px'>{detail}</td></tr>"

    # Flagged listings
    flagged_rows = ""
    for f in flagged[:15]:
        issues_html = " &nbsp;·&nbsp; ".join(f"<span style='color:#f59e0b'>{i}</span>" for i in f["issues"])
        flagged_rows += f"<tr><td style='color:#64748b;font-size:11px'>{f['id']}</td><td style='max-width:260px'>{f['title']}</td><td>{issues_html}</td><td style='color:#64748b'>{f['views']}</td></tr>"

    # SVG pipeline
    svg_rows = ""
    for b in svg_status:
        pct = round((b["designs"] / b["target"]) * 100) if b["target"] else 0
        bar_color = "#22c55e" if pct == 100 else "#6366f1" if pct > 0 else "#ef4444"
        bar = f'<div style="background:#1e293b;border-radius:3px;height:6px;width:100%;min-width:80px"><div style="background:{bar_color};border-radius:3px;height:6px;width:{pct}%"></div></div>'
        svg_rows += f"<tr><td>{b['name']}</td><td>{b['designs']}/{b['target']}</td><td style='min-width:100px'>{bar}</td><td>{status_dot(b['status'])}{b['status']}</td></tr>"

    # Category breakdown
    cat_rows = ""
    for cat, d in sorted(cats.items(), key=lambda x: -x[1]["views"]):
        cat_rows += f"<tr><td>{cat}</td><td style='text-align:center'>{d['count']}</td><td style='text-align:center'>${d['avg_price']:.2f}</td><td style='text-align:center'>{d['views']}</td><td style='text-align:center'>{d['favs']}</td></tr>"

    # Catalog status
    catalog_rows = ""
    for p in catalog:
        lid = p.get("etsy_listing_id") or "—"
        st  = p.get("status", "unknown")
        dot = status_dot(st)
        catalog_rows += f"<tr><td style='color:#64748b;font-size:11px'>{p.get('product_id','')}</td><td>{p.get('name','')[:50]}</td><td style='text-align:center'>{dot}{st}</td><td style='color:#64748b;font-size:11px'>${p.get('price',0):.2f}</td><td style='color:#64748b;font-size:11px'>{lid}</td></tr>"

    # Recent orders
    orders = etsy.get("orders", [])
    order_rows = ""
    for o in orders[:8]:
        items = o.get("transactions", []) if isinstance(o, dict) else []
        item_names = ", ".join(t.get("title", "?")[:30] for t in items[:2]) if items else "—"
        total = o.get("grandtotal", {})
        if isinstance(total, dict):
            amount = total.get("amount", 0) / max(total.get("divisor", 100), 1)
        else:
            amount = float(total or 0)
        ts = o.get("create_timestamp", "")
        order_rows += f"<tr><td style='color:#64748b;font-size:11px'>{o.get('receipt_id','')}</td><td style='font-size:12px'>{item_names}</td><td style='color:#22c55e'>${amount:.2f}</td><td style='color:#64748b;font-size:11px'>{str(ts)[:10]}</td></tr>"
    if not order_rows:
        order_rows = "<tr><td colspan='4' style='color:#64748b;text-align:center'>No recent orders fetched</td></tr>"

    overall = health.get("overall", "UNKNOWN")
    overall_color = "#22c55e" if overall == "OK" else "#f59e0b" if overall == "WARN" else "#ef4444"

    if flagged:
        flagged_section = f"""<table>
      <tr><th>ID</th><th>Title</th><th>Issues</th><th>Views</th></tr>
      {flagged_rows}
    </table>
    <div style="color:#64748b;font-size:11px;margin-top:8px">Run <code>python tools/listing_performance_monitor.py</code> for full report</div>"""
    else:
        flagged_section = "<p style=\"color:#64748b;font-size:13px\">&#10003; All listings pass quality checks.</p>"

    draft_alert = ""
    if etsy.get("draft_count", 0) > 0:
        draft_names = ", ".join(d.get("title", "?")[:40] for d in etsy.get("drafts", [])[:3])
        draft_alert = f'''<div style="background:#1e293b;border:1px solid #f59e0b;border-radius:8px;padding:12px 16px;margin-bottom:20px;color:#f59e0b">
          ⚠️ <strong>{etsy["draft_count"]} draft listing(s) awaiting your review:</strong> {draft_names}
          <br><code style="color:#94a3b8;font-size:11px">python tools/approve_listing.py --list-drafts</code>
        </div>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>OnBrandCraftz Dashboard</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0f172a; color: #e2e8f0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; font-size: 14px; line-height: 1.5; }}
    .header {{ background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #312e81; }}
    .header h1 {{ font-size: 22px; font-weight: 700; color: #f1f5f9; }}
    .header .sub {{ color: #a5b4fc; font-size: 12px; margin-top: 2px; }}
    .header .refresh {{ color: #64748b; font-size: 11px; }}
    .status-badge {{ display: inline-flex; align-items: center; background: {overall_color}22; border: 1px solid {overall_color}44; color: {overall_color}; border-radius: 20px; padding: 4px 12px; font-size: 12px; font-weight: 600; }}
    .refresh-btn {{ background: #6366f1; color: white; border: none; border-radius: 8px; padding: 8px 16px; font-size: 12px; font-weight: 600; cursor: pointer; margin-top: 8px; display: inline-block; text-decoration: none; }}
    .refresh-btn:hover {{ background: #4f46e5; }}
    .stale-banner {{ background: #451a03; border: 1px solid #f59e0b; border-radius: 8px; padding: 10px 16px; color: #fbbf24; font-size: 13px; margin-bottom: 16px; }}
    .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 32px; }}
    .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px; }}
    .kpi-card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 16px 20px; }}
    .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
    .grid-3 {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
    .card {{ background: #1e293b; border: 1px solid #334155; border-radius: 10px; padding: 20px; }}
    .card-title {{ font-size: 13px; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 16px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: .05em; padding: 6px 10px; text-align: left; border-bottom: 1px solid #334155; }}
    td {{ padding: 8px 10px; border-bottom: 1px solid #1e293b; font-size: 13px; vertical-align: middle; }}
    tr:hover td {{ background: #1a2744; }}
    .pace-bar {{ margin-top: 12px; }}
    .todo-item {{ display: flex; align-items: flex-start; gap: 10px; padding: 10px 0; border-bottom: 1px solid #1e293b; }}
    .todo-num {{ background: #ef4444; color: white; border-radius: 50%; width: 20px; height: 20px; display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0; margin-top: 1px; }}
    .todo-num.low {{ background: #334155; }}
    .todo-text {{ color: #cbd5e1; font-size: 13px; }}
    .todo-time {{ color: #64748b; font-size: 11px; }}
    code {{ background: #0f172a; color: #a5b4fc; padding: 2px 6px; border-radius: 4px; font-size: 11px; }}
    @media (max-width: 900px) {{ .grid-2, .grid-3 {{ grid-template-columns: 1fr; }} .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
  </style>
</head>
<body>

<div class="header">
  <div>
    <h1>🎀 OnBrandCraftz</h1>
    <div class="sub">Etsy Automation Dashboard · Scott</div>
  </div>
  <div style="text-align:right">
    <div class="status-badge">{status_dot(overall)}{overall}</div>
    <div class="refresh" style="margin-top:8px" id="updated-time">Last updated: {now}</div>
    <div class="refresh">Double-click <strong>OnBrandCraftz Dashboard</strong> to refresh</div>
  </div>
</div>

<script>
  // Show a banner if dashboard data is older than 26 hours
  var updated = new Date("{datetime.now().isoformat()}");
  var hours = (new Date() - updated) / 3600000;
  if (hours > 26) {{
    var banner = document.createElement("div");
    banner.className = "stale-banner";
    banner.innerHTML = "&#9888; This dashboard was last refreshed " + Math.round(hours) + " hours ago. Double-click <strong>OnBrandCraftz Dashboard</strong> on your computer to get fresh data.";
    document.querySelector(".container").insertBefore(banner, document.querySelector(".container").firstChild);
  }}
</script>

<div class="container">

  {draft_alert}

  <!-- KPI Row -->
  <div class="kpi-grid">
    {kpi_card("Monthly Pace", f"${pace:,.0f}", f"Target: $5,000 · {pace_pct}% there", pace_color, "💰")}
    {kpi_card("Active Listings", str(etsy.get("active_count", 0)), f"{etsy.get('draft_count', 0)} drafts awaiting review", "#6366f1", "🏷️")}
    {kpi_card("Total Views", f"{etsy.get('total_views', 0):,}", "All-time across all listings", "#0ea5e9", "👁️")}
    {kpi_card("Total Favorites", str(etsy.get("total_favs", 0)), "All-time shop favorites", "#ec4899", "❤️")}
    {kpi_card("Weekly Revenue", f"${revenue.get('gross', 0):.2f}", f"Net: ${revenue.get('net', 0):.2f} after fees", "#22c55e", "📈")}
    {kpi_card("Weekly Orders", str(revenue.get("orders", 0)), "Sales this week", "#f59e0b", "📦")}
  </div>

  <!-- Revenue progress bar -->
  <div class="card" style="margin-bottom:20px">
    <div class="card-title">Progress to $5,000/mo target</div>
    <div style="font-size:32px;font-weight:700;color:{pace_color};margin-bottom:8px">${pace:,.0f}<span style="font-size:16px;color:#64748b"> / $5,000</span></div>
    {pct_bar(pace, MONTHLY_TARGET, pace_color)}
    <div style="color:#64748b;font-size:12px;margin-top:8px">At {pace_pct}% — need ${MONTHLY_TARGET - pace:,.0f}/mo more. Unlock: top up OpenAI → generate SVG bundles + 2 new planners → run Etsy Ads.</div>
  </div>

  <div class="grid-2">

    <!-- Your To-Do List -->
    <div class="card">
      <div class="card-title">🔴 Your Action Items</div>
      <div class="todo-item">
        <div class="todo-num">1</div>
        <div><div class="todo-text"><strong>Top up OpenAI billing</strong></div><div class="todo-time">platform.openai.com → Billing → Add $100 · 5 min · Unblocks everything</div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num">2</div>
        <div><div class="todo-text"><strong>Add PINTEREST_CLIENT_ID to .env</strong></div><div class="todo-time">Pinterest Developer Console → App ID · 5 min</div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num">3</div>
        <div><div class="todo-text"><strong>Run Pinterest OAuth</strong> (after #2)</div><div class="todo-time"><code>python tools/pinterest_oauth.py</code> · 2 min</div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num">4</div>
        <div><div class="todo-text"><strong>Run TikTok OAuth</strong></div><div class="todo-time"><code>python tools/tiktok_oauth.py</code> · 5 min</div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num low">5</div>
        <div><div class="todo-text"><strong>Bump Etsy Ads to $5/day</strong> (when 5+ reviews)</div><div class="todo-time">Shop Manager → Marketing → Etsy Ads</div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num low">6</div>
        <div><div class="todo-text"><strong>Back-to-school keywords</strong> — by July 4</div><div class="todo-time"><code>python tools/seasonal_keywords.py --push</code></div></div>
      </div>
      <div class="todo-item">
        <div class="todo-num low">7</div>
        <div><div class="todo-text"><strong>Etsy re-auth</strong> — due ~September 1, 2026</div><div class="todo-time"><code>python tools/etsy_oauth.py</code></div></div>
      </div>
    </div>

    <!-- Shop Health -->
    <div class="card">
      <div class="card-title">🏥 Shop Health</div>
      <table>
        <tr><th>Check</th><th>Detail</th></tr>
        {health_rows if health_rows else "<tr><td colspan='2' style='color:#64748b'>No health data — run health_check.py</td></tr>"}
      </table>
    </div>

  </div>

  <div class="grid-3">

    <!-- SVG Pipeline -->
    <div class="card">
      <div class="card-title">🎨 SVG Bundle Pipeline</div>
      <table>
        <tr><th>Bundle</th><th>Designs</th><th>Progress</th><th>Status</th></tr>
        {svg_rows if svg_rows else "<tr><td colspan='4' style='color:#64748b'>No bundles found</td></tr>"}
      </table>
      <div style="color:#64748b;font-size:11px;margin-top:12px">Blocked on OpenAI billing · ~$10.57 per bundle · breaks even at 2nd sale</div>
    </div>

    <!-- Category Breakdown -->
    <div class="card">
      <div class="card-title">📊 Listings by Category</div>
      <table>
        <tr><th>Category</th><th style="text-align:center">Listings</th><th style="text-align:center">Avg Price</th><th style="text-align:center">Views</th><th style="text-align:center">Favs</th></tr>
        {cat_rows if cat_rows else "<tr><td colspan='5' style='color:#64748b'>No data</td></tr>"}
      </table>
    </div>

    <!-- Recent Orders -->
    <div class="card">
      <div class="card-title">💳 Recent Orders</div>
      <table>
        <tr><th>Order ID</th><th>Items</th><th>Total</th><th>Date</th></tr>
        {order_rows}
      </table>
    </div>

  </div>

  <!-- Flagged Listings -->
  <div class="card" style="margin-bottom:20px">
    <div class="card-title">⚠️ Listings Needing Attention ({len(flagged)})</div>
    {flagged_section}
  </div>

  <!-- Product Catalog -->
  <div class="card" style="margin-bottom:20px">
    <div class="card-title">📦 Product Catalog</div>
    <table>
      <tr><th>ID</th><th>Product</th><th style="text-align:center">Status</th><th>Price</th><th>Listing ID</th></tr>
      {catalog_rows if catalog_rows else "<tr><td colspan='5' style='color:#64748b'>No catalog data</td></tr>"}
    </table>
  </div>

  <!-- Cost reference -->
  <div class="card">
    <div class="card-title">💵 Cost Per Product (creation)</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px">
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">Digital Planner</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$2.56</div>
        <div style="color:#64748b;font-size:11px">14 API calls · breaks even sale #1</div>
      </div>
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">SVG Bundle (20 designs)</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$10.57</div>
        <div style="color:#64748b;font-size:11px">62 API calls · breaks even sale #2</div>
      </div>
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">Wall Art Listing</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$0.72</div>
        <div style="color:#64748b;font-size:11px">3 API calls · breaks even sale #1</div>
      </div>
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">Sublimation Design</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$0.47</div>
        <div style="color:#64748b;font-size:11px">1 API call · breaks even sale #1</div>
      </div>
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">Sticker Pack</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$1.39</div>
        <div style="color:#64748b;font-size:11px">7 API calls · breaks even sale #1</div>
      </div>
      <div style="background:#0f172a;border-radius:8px;padding:12px">
        <div style="color:#94a3b8;font-size:11px">3D Physical (per unit)</div>
        <div style="color:#f1f5f9;font-size:20px;font-weight:700">$7.50</div>
        <div style="color:#64748b;font-size:11px">COGS per sale · real materials</div>
      </div>
    </div>
  </div>

  <div style="text-align:center;color:#334155;font-size:11px;margin-top:32px;padding-bottom:24px">
    OnBrandCraftz Automation Dashboard · Generated {now} · <code>python tools/generate_dashboard.py</code>
  </div>

</div>
</body>
</html>'''


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Fetching Etsy data...")
    etsy     = fetch_etsy_data()
    health   = load_health_log()
    catalog  = load_catalog()
    svg      = load_svg_status()
    revenue  = load_weekly_revenue()
    cats     = categorize_listings(etsy.get("listings", []))
    flagged  = audit_listing_issues(etsy.get("listings", []))

    print(f"  {etsy['active_count']} active listings, {len(flagged)} flagged")
    print(f"  Monthly pace: ${revenue.get('pace', 0):,.0f}")

    html = generate_html(etsy, health, catalog, svg, revenue, flagged, cats)
    DASHBOARD_PATH.write_text(html)
    print(f"\n✓ Dashboard saved: {DASHBOARD_PATH.resolve()}")
    print(f"  Open in browser: file://{DASHBOARD_PATH.resolve()}")


if __name__ == "__main__":
    main()
