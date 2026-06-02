#!/usr/bin/env python3
"""
weekly_report.py

Generates a detailed weekly business report for OnBrandCraftz.
Pulls live data from Etsy, computes revenue vs. $5K/month target,
flags problem listings, logs all autonomous decisions, and saves
a dated markdown report to data/reports/.

Run automatically every Sunday by business_pipeline.py --mode weekly
or manually at any time:
  python tools/weekly_report.py
  python tools/weekly_report.py --save-only   (no console output)
"""

import json, os, sys, re
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from etsy_api import EtsyAPIClient, EtsyAPIError

REPORTS_DIR     = Path("data/reports")
DECISION_LOG    = Path("data/decision_log.json")
PIPELINE_STATE  = Path("data/pipeline_state.json")
SVG_BUNDLES_DIR = Path("data/svg_bundles")
SUBLIM_DIR      = Path("data/sublimation_mockups")

REPORTS_DIR.mkdir(parents=True, exist_ok=True)

MONTHLY_TARGET_NET    = 5000.0
ETSY_FEE_RATE         = 0.25   # blended: 6.5% txn + 3%+$0.25 payment processing


def gross_needed(net: float) -> float:
    return net / (1 - ETSY_FEE_RATE)


# ── Decision log ──────────────────────────────────────────────────────────────

def log_decision(event_type: str, description: str, data: dict = None, outcome: str = "success"):
    """Append an entry to the decision log. Call this whenever an autonomous action is taken."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event_type": event_type,
        "description": description,
        "data": data or {},
        "outcome": outcome,
    }
    log = []
    if DECISION_LOG.exists():
        try:
            with open(DECISION_LOG) as f:
                log = json.load(f)
        except json.JSONDecodeError:
            log = []
    log.append(entry)
    # Keep last 500 entries
    if len(log) > 500:
        log = log[-500:]
    with open(DECISION_LOG, "w") as f:
        json.dump(log, f, indent=2)


def get_recent_decisions(days: int = 7) -> list[dict]:
    if not DECISION_LOG.exists():
        return []
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    try:
        with open(DECISION_LOG) as f:
            log = json.load(f)
        return [e for e in log if e.get("timestamp", "") >= cutoff]
    except Exception:
        return []


# ── Etsy data fetchers ────────────────────────────────────────────────────────

def fetch_all_listings(client: EtsyAPIClient) -> list[dict]:
    """Fetch all active listings (handles pagination)."""
    listings = []
    offset = 0
    limit = 100
    while True:
        try:
            result = client._request("GET", f"shops/{client.shop_id}/listings/active",
                                     params={"limit": limit, "offset": offset,
                                             "includes": "Images,MainImage"})
            batch = result.get("results", [])
            listings.extend(batch)
            if len(batch) < limit:
                break
            offset += limit
        except Exception:
            break
    return listings


def fetch_recent_orders(client: EtsyAPIClient, days: int = 7) -> list[dict]:
    """Fetch orders from the last N days."""
    try:
        result = client.get_orders(limit=100, status="open")
        all_orders = result.get("results", [])
        # Also fetch completed
        result2 = client._request("GET", f"shops/{client.shop_id}/receipts",
                                  params={"limit": 100, "was_paid": True})
        all_orders.extend(result2.get("results", []))
    except Exception:
        return []

    cutoff_ts = int((datetime.utcnow() - timedelta(days=days)).timestamp())
    return [o for o in all_orders if o.get("create_timestamp", 0) >= cutoff_ts]


# ── Analysis ──────────────────────────────────────────────────────────────────

def analyze_listings(listings: list[dict]) -> dict:
    """Compute per-listing health flags and aggregate stats."""
    total_favorites = 0
    total_views = 0
    flags = []
    top_performers = []

    for l in listings:
        lid   = l.get("listing_id")
        title = l.get("title", "")[:55]
        favs  = l.get("num_favorers", 0)
        views = l.get("views", 0)
        price = l.get("price", {}).get("amount", 0) / max(l.get("price", {}).get("divisor", 100), 1)

        total_favorites += favs
        total_views     += views

        # Flag: many views but very few favorites → photo or price problem
        if views > 200 and favs < 5:
            flags.append({
                "listing_id": lid, "title": title,
                "issue": f"HIGH VIEWS ({views}) / LOW FAVORITES ({favs}) → photo or price issue",
                "views": views, "favorites": favs, "severity": "high",
            })
        # Flag: listing has been up with almost no views → SEO / tag problem
        elif views < 15 and favs == 0:
            flags.append({
                "listing_id": lid, "title": title,
                "issue": f"LOW VISIBILITY ({views} views, 0 favorites) → SEO / tag issue",
                "views": views, "favorites": favs, "severity": "medium",
            })

        top_performers.append({
            "listing_id": lid, "title": title,
            "favorites": favs, "views": views, "price": price,
        })

    top_performers.sort(key=lambda x: (x["favorites"], x["views"]), reverse=True)
    flags.sort(key=lambda x: x["views"], reverse=True)

    return {
        "total_listings": len(listings),
        "total_favorites": total_favorites,
        "total_views": total_views,
        "flags": flags,
        "top_performers": top_performers[:10],
    }


def compute_revenue(orders: list[dict]) -> dict:
    """Sum revenue from recent orders."""
    gross = 0.0
    order_count = 0
    for o in orders:
        # Etsy receipt: grandtotal in cents
        amount = o.get("grandtotal", {})
        if isinstance(amount, dict):
            gross += amount.get("amount", 0) / max(amount.get("divisor", 100), 1)
        order_count += 1
    net = gross * (1 - ETSY_FEE_RATE)
    return {"gross": gross, "net": net, "order_count": order_count}


# ── Pipeline status ───────────────────────────────────────────────────────────

def get_pipeline_status() -> dict:
    """Read state files to summarize what's been done and what's pending."""
    status = {
        "svg_bundles": {},
        "sublimation_mockups": [],
        "last_weekly_run": None,
        "completed_themes": [],
    }

    # Pipeline state
    if PIPELINE_STATE.exists():
        try:
            with open(PIPELINE_STATE) as f:
                state = json.load(f)
            status["last_weekly_run"] = state.get("last_weekly_run")
            status["completed_themes"] = state.get("completed_themes", [])
        except Exception:
            pass

    # SVG bundle manifests
    if SVG_BUNDLES_DIR.exists():
        for bundle_dir in SVG_BUNDLES_DIR.iterdir():
            manifest_path = bundle_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path) as f:
                        m = json.load(f)
                    status["svg_bundles"][bundle_dir.name] = {
                        "designs": m.get("design_count", 0),
                        "status": m.get("status", "unknown"),
                        "listing_id": m.get("etsy_listing_id"),
                    }
                except Exception:
                    pass

    # Sublimation mockups
    if SUBLIM_DIR.exists():
        status["sublimation_mockups"] = [p.name for p in SUBLIM_DIR.glob("mockup_*.jpg")]

    return status


# ── Report builder ────────────────────────────────────────────────────────────

def build_report(listings_data: dict, revenue_data: dict, pipeline: dict,
                 recent_decisions: list[dict]) -> str:
    today = date.today()
    day_of_month = today.day
    monthly_pace = (revenue_data["net"] / max(day_of_month, 1)) * 30
    pct_of_target = (monthly_pace / MONTHLY_TARGET_NET) * 100
    gross_target = gross_needed(MONTHLY_TARGET_NET)

    lines = []
    lines.append(f"# OnBrandCraftz Weekly Report — {today.isoformat()}")
    lines.append(f"*Generated automatically by weekly_report.py*\n")

    # ── Revenue ──────────────────────────────────────────────────────────────
    lines.append("## Revenue (Last 7 Days)")
    lines.append(f"| Metric | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Gross revenue | ${revenue_data['gross']:,.2f} |")
    lines.append(f"| Net after Etsy fees | ${revenue_data['net']:,.2f} |")
    lines.append(f"| Orders | {revenue_data['order_count']} |")
    lines.append(f"| Monthly pace (net) | ${monthly_pace:,.0f}/mo |")
    lines.append(f"| Monthly target | ${MONTHLY_TARGET_NET:,.0f}/mo net (${gross_target:,.0f} gross) |")
    lines.append(f"| On pace | {'✓ YES' if monthly_pace >= MONTHLY_TARGET_NET else f'✗ NO — {pct_of_target:.0f}% of target'} |")

    gap = MONTHLY_TARGET_NET - monthly_pace
    if gap > 0:
        # Estimate listings needed at average $9.99/sale to close gap
        avg_sale_net = 8.50
        orders_needed = gap / avg_sale_net
        lines.append(f"\n**Gap to close:** ${gap:,.0f}/mo more net needed (~{orders_needed:.0f} more sales/month at avg $8.50 net)")

    lines.append("")

    # ── Shop overview ─────────────────────────────────────────────────────────
    lines.append("## Shop Overview")
    lines.append(f"| Stat | Value |")
    lines.append(f"|---|---|")
    lines.append(f"| Active listings | {listings_data['total_listings']} |")
    lines.append(f"| Total all-time favorites | {listings_data['total_favorites']:,} |")
    lines.append(f"| Total all-time views | {listings_data['total_views']:,} |")
    lines.append(f"| Listings needed for $5K/mo | 70+ |")
    needed = max(0, 70 - listings_data["total_listings"])
    lines.append(f"| Still to build | {needed} more listings |")
    lines.append("")

    # ── Top performers ────────────────────────────────────────────────────────
    lines.append("## Top Performers")
    lines.append("| Listing | Favorites | Views | Price |")
    lines.append("|---|---|---|---|")
    for p in listings_data["top_performers"][:8]:
        lines.append(f"| {p['title'][:45]} | {p['favorites']} ★ | {p['views']:,} | ${p['price']:.2f} |")
    lines.append("")

    # ── Problem listings ──────────────────────────────────────────────────────
    lines.append("## Problem Listings — Action Required")
    if listings_data["flags"]:
        lines.append("| Listing ID | Issue | Severity |")
        lines.append("|---|---|---|")
        for flag in listings_data["flags"][:10]:
            lines.append(f"| [{flag['listing_id']}] {flag['title'][:35]} | {flag['issue'][:60]} | {flag['severity'].upper()} |")
    else:
        lines.append("✓ No problem listings detected this week.")
    lines.append("")

    # ── Pipeline status ───────────────────────────────────────────────────────
    lines.append("## Pipeline Status")
    lines.append("\n### SVG Bundles")
    if pipeline["svg_bundles"]:
        lines.append("| Bundle | Designs | Status | Listing |")
        lines.append("|---|---|---|---|")
        bundle_target = 20
        for name, info in pipeline["svg_bundles"].items():
            pct = f"{info['designs']}/{bundle_target}"
            lid = f"[{info['listing_id']}](https://www.etsy.com/listing/{info['listing_id']})" if info.get("listing_id") else "not published"
            lines.append(f"| {name} | {pct} | {info['status']} | {lid} |")
    else:
        lines.append("No SVG bundles generated yet.")

    lines.append("\n### Sublimation Mockups")
    mockups = pipeline["sublimation_mockups"]
    if mockups:
        lines.append(f"{len(mockups)} mockup files in data/sublimation_mockups/")
        for m in sorted(mockups)[:10]:
            lines.append(f"  - {m}")
    else:
        lines.append("No mockups found.")

    lines.append(f"\n### Last Weekly Run: {pipeline['last_weekly_run'] or 'Never'}")
    lines.append(f"### Themes completed: {len(pipeline['completed_themes'])}")
    lines.append("")

    # ── Autonomous decisions ──────────────────────────────────────────────────
    lines.append("## Autonomous Decisions (Last 7 Days)")
    if recent_decisions:
        lines.append("| Time | Type | Description | Outcome |")
        lines.append("|---|---|---|---|")
        for d in recent_decisions[-20:]:
            ts = d["timestamp"][:16].replace("T", " ")
            lines.append(f"| {ts} | {d['event_type']} | {d['description'][:55]} | {d['outcome']} |")
    else:
        lines.append("No autonomous decisions logged this week.")
    lines.append("")

    # ── Recommendations ───────────────────────────────────────────────────────
    lines.append("## This Week's Priority Actions")
    priority = []

    high_sev = [f for f in listings_data["flags"] if f["severity"] == "high"]
    if high_sev:
        priority.append(f"🔴 Fix {len(high_sev)} high-priority listings (photo/price issues) — these have traffic but aren't converting")

    if pct_of_target < 50:
        priority.append(f"🔴 Revenue at {pct_of_target:.0f}% of target — publish more listings immediately")
    elif pct_of_target < 80:
        priority.append(f"🟡 Revenue at {pct_of_target:.0f}% of target — continue current pace")

    if pipeline["svg_bundles"]:
        incomplete = [(k, v) for k, v in pipeline["svg_bundles"].items() if v["designs"] < 20]
        if incomplete:
            priority.append(f"🟡 Complete {len(incomplete)} SVG bundle(s): " + ", ".join(k for k, _ in incomplete))
        unpublished = [(k, v) for k, v in pipeline["svg_bundles"].items() if not v.get("listing_id") and v["designs"] >= 20]
        if unpublished:
            priority.append(f"🟡 Publish {len(unpublished)} completed SVG bundle(s) to Etsy")

    if needed > 0:
        priority.append(f"🟡 Need {needed} more listings to reach 70-listing target for $5K/mo pace")

    if not priority:
        priority.append("✓ Everything on track — continue weekly generation cadence")

    for p in priority:
        lines.append(f"- {p}")
    lines.append("")

    # ── Projection ────────────────────────────────────────────────────────────
    lines.append("## Revenue Projection")
    lines.append(f"At current pace: **${monthly_pace:,.0f}/month net**")
    if monthly_pace < MONTHLY_TARGET_NET:
        months_to_target = 0
        projected = monthly_pace
        m = 0
        while projected < MONTHLY_TARGET_NET and m < 24:
            m += 1
            projected += (projected * 0.15)  # assume 15% MoM growth from new listings
        lines.append(f"At 15% month-over-month growth from new listings: **target in ~{m} months**")
    else:
        lines.append(f"✓ **ON TARGET** — ${monthly_pace:,.0f} projected vs. ${MONTHLY_TARGET_NET:,.0f} goal")
    lines.append("")

    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def run(save_only: bool = False) -> str:
    client = EtsyAPIClient()

    print("Pulling Etsy data...")
    listings = fetch_all_listings(client)
    orders   = fetch_recent_orders(client, days=7)

    listings_data   = analyze_listings(listings)
    revenue_data    = compute_revenue(orders)
    pipeline        = get_pipeline_status()
    recent_decisions = get_recent_decisions(days=7)

    report = build_report(listings_data, revenue_data, pipeline, recent_decisions)

    # Save dated report
    report_path = REPORTS_DIR / f"{date.today().isoformat()}_weekly_report.md"
    report_path.write_text(report)

    # Log that we ran the report
    log_decision(
        "weekly_report",
        f"Generated weekly report — {listings_data['total_listings']} listings, "
        f"${revenue_data['net']:.2f} net revenue last 7 days",
        {"report_path": str(report_path), "listing_count": listings_data["total_listings"]},
    )

    if not save_only:
        print(report)

    print(f"\n✓ Report saved: {report_path}")
    return report


if __name__ == "__main__":
    save_only = "--save-only" in sys.argv
    run(save_only=save_only)
