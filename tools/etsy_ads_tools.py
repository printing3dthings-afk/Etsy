"""
Etsy Ads Tools — manages Etsy Ads (Promoted Listings) campaigns.

Etsy Ads works on a CPC (cost-per-click) model. You set a daily budget
and Etsy automatically promotes your eligible listings. You can also
set max CPC bids per listing.

Offsite Ads: Etsy automatically promotes your listings on Google, Facebook,
Instagram, Pinterest etc. You pay 12-15% only when a sale results.

API: Etsy Ads endpoints require OAuth access token.
This module manages ad config/tracking locally with Etsy API calls where available.
"""

import json
import math
from datetime import date, timedelta
from typing import Any

from data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_ads_overview",
        "description": "Get a summary of current Etsy Ads performance: spend, clicks, revenue, ROAS.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_daily_budget",
        "description": "Set or update the daily Etsy Ads budget.",
        "input_schema": {
            "type": "object",
            "properties": {
                "daily_budget_usd": {
                    "type": "number",
                    "description": "Daily ad spend cap in USD (min $1.00)",
                }
            },
            "required": ["daily_budget_usd"],
        },
    },
    {
        "name": "get_listing_ad_performance",
        "description": "Get ad performance metrics for each listing: impressions, clicks, CTR, spend, revenue, ROAS.",
        "input_schema": {
            "type": "object",
            "properties": {
                "sort_by": {
                    "type": "string",
                    "enum": ["roas", "revenue", "clicks", "spend", "ctr"],
                    "default": "roas",
                }
            },
            "required": [],
        },
    },
    {
        "name": "recommend_ad_strategy",
        "description": "Analyse current listings and recommend which to advertise, at what budget, and which to pause.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "log_ad_spend",
        "description": "Manually log ad spend data (use when Etsy API is not connected).",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "YYYY-MM-DD"},
                "spend_usd": {"type": "number"},
                "clicks": {"type": "integer"},
                "impressions": {"type": "integer"},
                "orders_from_ads": {"type": "integer"},
                "revenue_from_ads": {"type": "number"},
            },
            "required": ["spend_usd"],
        },
    },
    {
        "name": "get_roas_report",
        "description": "Return on Ad Spend report: revenue generated per dollar spent on ads.",
        "input_schema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "enum": ["this_week", "last_week", "this_month", "all_time"],
                    "default": "this_month",
                }
            },
            "required": [],
        },
    },
    {
        "name": "toggle_listing_ad",
        "description": "Enable or disable Etsy Ads for a specific listing.",
        "input_schema": {
            "type": "object",
            "properties": {
                "listing_id": {"type": "string"},
                "enabled": {"type": "boolean"},
                "reason": {"type": "string", "description": "Why enabling/disabling this ad"},
            },
            "required": ["listing_id", "enabled"],
        },
    },
    {
        "name": "get_offsite_ads_summary",
        "description": "Summary of Offsite Ads performance (Google, Facebook, Instagram). Note: Etsy charges 12-15% only on resulting sales.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_ads_overview":
        return _get_ads_overview(store)
    if tool_name == "set_daily_budget":
        return _set_daily_budget(tool_input["daily_budget_usd"], store)
    if tool_name == "get_listing_ad_performance":
        return _get_listing_ad_performance(tool_input.get("sort_by", "roas"), store)
    if tool_name == "recommend_ad_strategy":
        return _recommend_ad_strategy(store)
    if tool_name == "log_ad_spend":
        return _log_ad_spend(tool_input, store)
    if tool_name == "get_roas_report":
        return _get_roas_report(tool_input.get("period", "this_month"), store)
    if tool_name == "toggle_listing_ad":
        return _toggle_listing_ad(tool_input, store)
    if tool_name == "get_offsite_ads_summary":
        return _get_offsite_ads_summary(store)
    return f"Unknown Etsy Ads tool: {tool_name}"


def _get_ads_overview(store: DataStore) -> str:
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    spend_log = ads_data.get("spend_log", [])
    budget = ads_data.get("daily_budget_usd", 0)

    total_spend = sum(e.get("spend_usd", 0) for e in spend_log)
    total_revenue = sum(e.get("revenue_from_ads", 0) for e in spend_log)
    total_clicks = sum(e.get("clicks", 0) for e in spend_log)
    total_impressions = sum(e.get("impressions", 0) for e in spend_log)
    roas = round(total_revenue / total_spend, 2) if total_spend > 0 else 0
    ctr = round(total_clicks / total_impressions * 100, 2) if total_impressions > 0 else 0

    return json.dumps({
        "daily_budget_usd": budget,
        "all_time_totals": {
            "spend_usd": round(total_spend, 2),
            "revenue_from_ads": round(total_revenue, 2),
            "roas": roas,
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr_pct": ctr,
        },
        "roas_benchmark": "Good ROAS for Etsy Ads is 3.0+ (spend $1, earn $3+)",
        "api_note": "Connect Etsy OAuth for live ad data. Use log_ad_spend to track manually.",
    }, indent=2)


_MAX_DAILY_BUDGET_USD = 500.0  # 2026-08-14: this shop's real ad spend is $3-5/day (CLAUDE.md's
# Etsy Ads Strategy section) scaling up gradually (20-30%/week past ROAS>4x) -- $500/day is
# generous headroom above any spend this shop would legitimately reach any time soon, while
# still catching the real failure mode (a $50.00/day budget typed as $5000/day or $50000/day).


def _set_daily_budget(budget: float, store: DataStore) -> str:
    # NaN compares False to everything, including `< 1.0` -- math.isnan() is the only
    # reliable way to catch it. Checked first since NaN would otherwise silently pass every
    # numeric comparison below it (2026-08-14, confirmed bug: a NaN budget used to persist
    # and propagate through every downstream ROAS/budget calculation as a non-JSON-standard
    # `NaN` token).
    if isinstance(budget, float) and math.isnan(budget):
        return json.dumps({"error": "Daily budget must be a real number, not NaN"})
    if budget < 1.0:
        return json.dumps({"error": "Minimum Etsy Ads daily budget is $1.00"})
    if budget > _MAX_DAILY_BUDGET_USD:
        return json.dumps({
            "error": f"Maximum Etsy Ads daily budget is ${_MAX_DAILY_BUDGET_USD:,.2f} -- "
                     f"if you genuinely need to spend more than that per day, set it directly "
                     f"in Etsy Shop Manager instead of through this tool."
        })
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    old_budget = ads_data.get("daily_budget_usd", 0)
    ads_data["daily_budget_usd"] = budget
    ads_data["budget_updated_at"] = str(date.today())
    store.set(ads_data, "etsy_ads")
    store.save()
    return json.dumps({
        "success": True,
        "previous_budget": old_budget,
        "new_daily_budget_usd": budget,
        "monthly_cap_estimate": round(budget * 30, 2),
        "note": "Update in Etsy Shop Manager → Marketing → Etsy Ads to apply the change live.",
    }, indent=2)


def _get_listing_ad_performance(sort_by: str, store: DataStore) -> str:
    listings = store.listings
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    listing_ads = ads_data.get("listing_ads", {})

    rows = []
    for l in listings:
        lid = l["id"]
        ad = listing_ads.get(lid, {})
        spend = ad.get("spend_usd", 0)
        revenue = ad.get("revenue_usd", 0)
        clicks = ad.get("clicks", 0)
        impressions = ad.get("impressions", 0)
        roas = round(revenue / spend, 2) if spend > 0 else None
        ctr = round(clicks / impressions * 100, 2) if impressions > 0 else None
        rows.append({
            "id": lid,
            "title": l["title"][:55],
            "price": l.get("price", 0),
            "ad_enabled": ad.get("enabled", False),
            "spend_usd": round(spend, 2),
            "revenue_usd": round(revenue, 2),
            "roas": roas,
            "clicks": clicks,
            "impressions": impressions,
            "ctr_pct": ctr,
        })

    sort_map = {
        "roas": lambda r: r["roas"] or 0,
        "revenue": lambda r: r["revenue_usd"],
        "clicks": lambda r: r["clicks"],
        "spend": lambda r: r["spend_usd"],
        "ctr": lambda r: r["ctr_pct"] or 0,
    }
    rows.sort(key=sort_map.get(sort_by, sort_map["roas"]), reverse=True)
    return json.dumps({"listing_ad_performance": rows, "sorted_by": sort_by,
                       "note": "Log ad spend data via log_ad_spend or connect Etsy OAuth for live data."}, indent=2)


def _recommend_ad_strategy(store: DataStore) -> str:
    listings = store.listings
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    budget = ads_data.get("daily_budget_usd", 5)

    # Score each listing for ad worthiness
    recommendations = []
    for l in listings:
        price = l.get("price", 0)
        views = l.get("views", 0)
        sales = l.get("sales", 0)
        favs = l.get("favorites", 0)
        conv = sales / views if views > 0 else 0

        score = 0
        reasons = []
        if price >= 15:
            score += 2
            reasons.append(f"Good price point (${price}) — sufficient margin to absorb ad cost")
        if conv > 0.02:
            score += 3
            reasons.append(f"Strong conversion rate ({conv:.1%}) — proven buyer interest")
        if favs > 5:
            score += 1
            reasons.append(f"{favs} favorites — social proof helps ad conversion")
        if sales == 0 and views < 50:
            score -= 1
            reasons.append("No sales yet — listing needs organic traffic first to validate")

        action = "ADVERTISE" if score >= 3 else ("TEST" if score >= 1 else "SKIP")
        recommendations.append({
            "id": l["id"],
            "title": l["title"][:50],
            "price": price,
            "action": action,
            "score": score,
            "reasons": reasons,
        })

    recommendations.sort(key=lambda r: r["score"], reverse=True)
    advertise_count = sum(1 for r in recommendations if r["action"] == "ADVERTISE")

    return json.dumps({
        "recommendations": recommendations,
        "suggested_daily_budget_usd": budget,
        "listings_to_advertise": advertise_count,
        "budget_per_listing": round(budget / max(advertise_count, 1), 2),
        "strategy_tips": [
            "Start with your highest-priced, proven-converting listings",
            "Run ads for at least 30 days before judging performance",
            "Target ROAS of 3x minimum (spend $1, earn $3)",
            "Pause listings with ROAS < 1.5 after 60 days",
            "New listings: run ads for 2 weeks to get initial views and rank signal",
        ],
    }, indent=2)


def _log_ad_spend(data: dict, store: DataStore) -> str:
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    spend_log = ads_data.get("spend_log", [])
    entry = {
        "date": data.get("date", str(date.today())),
        "spend_usd": data["spend_usd"],
        "clicks": data.get("clicks", 0),
        "impressions": data.get("impressions", 0),
        "orders_from_ads": data.get("orders_from_ads", 0),
        "revenue_from_ads": data.get("revenue_from_ads", 0),
    }
    spend_log.append(entry)
    ads_data["spend_log"] = spend_log
    store.set(ads_data, "etsy_ads")
    store.save()
    roas = round(entry["revenue_from_ads"] / entry["spend_usd"], 2) if entry["spend_usd"] > 0 else 0
    return json.dumps({"success": True, "entry": entry, "roas_this_entry": roas}, indent=2)


def _get_roas_report(period: str, store: DataStore) -> str:
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    spend_log = ads_data.get("spend_log", [])
    today = date.today()

    period_map = {
        "this_week": today - timedelta(days=7),
        "last_week": today - timedelta(days=14),
        "this_month": today.replace(day=1),
        "all_time": date(2000, 1, 1),
    }
    cutoff = period_map.get(period, date(2000, 1, 1))
    def _safe_date(s: str) -> date:
        try:
            return date.fromisoformat(s)
        except (ValueError, TypeError):
            return date(2000, 1, 1)
    filtered = [e for e in spend_log if _safe_date(e.get("date", str(today))) >= cutoff]

    total_spend = sum(e.get("spend_usd", 0) for e in filtered)
    total_revenue = sum(e.get("revenue_from_ads", 0) for e in filtered)
    roas = round(total_revenue / total_spend, 2) if total_spend > 0 else 0

    rating = "Excellent" if roas >= 5 else "Good" if roas >= 3 else "Acceptable" if roas >= 2 else "Poor"

    return json.dumps({
        "period": period,
        "total_spend_usd": round(total_spend, 2),
        "revenue_from_ads_usd": round(total_revenue, 2),
        "roas": roas,
        "roas_rating": rating,
        "net_from_ads": round(total_revenue - total_spend, 2),
        "days_tracked": len(filtered),
        "benchmark": "Target ROAS: 3.0+ | Pause campaigns under 1.5",
    }, indent=2)


def _toggle_listing_ad(data: dict, store: DataStore) -> str:
    ads_data = store.get("etsy_ads", default=_default_ads_data())
    listing_ads = ads_data.get("listing_ads", {})
    lid = data["listing_id"]
    if lid not in listing_ads:
        listing_ads[lid] = {"enabled": False, "spend_usd": 0, "revenue_usd": 0, "clicks": 0, "impressions": 0}
    listing_ads[lid]["enabled"] = data["enabled"]
    listing_ads[lid]["toggle_reason"] = data.get("reason", "")
    listing_ads[lid]["toggled_at"] = str(date.today())
    ads_data["listing_ads"] = listing_ads
    store.set(ads_data, "etsy_ads")
    store.save()
    return json.dumps({
        "success": True,
        "listing_id": lid,
        "ad_enabled": data["enabled"],
        "note": "Also update in Etsy Shop Manager → Marketing → Etsy Ads to apply live.",
    }, indent=2)


def _get_offsite_ads_summary(store: DataStore) -> str:
    revenue = store.analytics.get("revenue", {})
    gross = revenue.get("this_year", 0)
    fee_pct = 0.12 if gross >= 10000 else 0.15
    return json.dumps({
        "offsite_ads_status": "Automatic (Etsy controls placement)",
        "fee_rate": f"{fee_pct*100:.0f}%",
        "fee_applies": "Only when a sale results from an Offsite Ad click",
        "your_annual_revenue": gross,
        "fee_tier": "12% (shop > $10k/yr)" if gross >= 10000 else "15% (shop < $10k/yr)",
        "can_opt_out": gross < 10000,
        "opt_out_note": (
            "Shops under $10k/yr can opt out in Shop Manager → Settings → Offsite Ads"
            if gross < 10000 else
            "Shops over $10k/yr CANNOT opt out of Offsite Ads"
        ),
        "strategy": "Offsite Ads is generally worth it — you only pay on actual sales, and the 15% is less than most PPC costs.",
    }, indent=2)


def _default_ads_data() -> dict:
    return {
        "daily_budget_usd": 0,
        "spend_log": [],
        "listing_ads": {},
    }
