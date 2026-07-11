"""
Pricing & Promotions Tools — manages Etsy sales events, coupons, and bundle pricing.

Etsy promotions include:
  - Sales (% off or $ off, site-wide or per-listing)
  - Coupon codes (for customer retention, follow-up, abandoned carts)
  - Free shipping thresholds
  - Bundle pricing strategies (run as separate combo listings)
"""

import json
from datetime import date, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "create_promotion",
        "description": "Create a sale event or coupon code (tracked locally; also configure in Etsy Shop Manager).",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Internal name, e.g. 'Summer Sale 2026'"},
                "promo_type": {
                    "type": "string",
                    "enum": ["percentage_off", "fixed_amount_off", "free_shipping", "coupon_code"],
                },
                "discount_value": {"type": "number", "description": "Percentage (e.g. 20) or dollar amount (e.g. 5)"},
                "coupon_code": {"type": "string", "description": "Required for coupon_code type"},
                "start_date": {"type": "string", "description": "YYYY-MM-DD, defaults to today"},
                "end_date": {"type": "string", "description": "YYYY-MM-DD"},
                "applies_to": {
                    "type": "string",
                    "enum": ["all_listings", "digital_only", "physical_only", "specific_listings"],
                    "default": "all_listings",
                },
                "listing_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Required if applies_to=specific_listings",
                },
                "min_order_value": {"type": "number", "description": "Minimum cart value to qualify (optional)"},
            },
            "required": ["name", "promo_type", "discount_value", "end_date"],
        },
    },
    {
        "name": "get_active_promotions",
        "description": "List all currently active sales and coupons.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "end_promotion",
        "description": "End an active promotion early.",
        "input_schema": {
            "type": "object",
            "properties": {
                "promo_id": {"type": "string"},
                "reason": {"type": "string"},
            },
            "required": ["promo_id"],
        },
    },
    {
        "name": "calculate_sale_impact",
        "description": "Estimate the revenue and margin impact of running a percentage-off sale.",
        "input_schema": {
            "type": "object",
            "properties": {
                "discount_pct": {"type": "number", "description": "Discount percentage, e.g. 20"},
                "expected_sales_lift_pct": {
                    "type": "number",
                    "description": "Expected increase in unit sales during sale (e.g. 30 = 30% more sales)",
                    "default": 25,
                },
            },
            "required": ["discount_pct"],
        },
    },
    {
        "name": "get_promotion_calendar",
        "description": "Get the full promotional calendar: past, active, and planned promotions.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_promo_recommendations",
        "description": "Get recommended promotions based on current date, inventory, and performance.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "generate_coupon_strategy",
        "description": "Generate a coupon strategy for customer retention, win-back, or launch.",
        "input_schema": {
            "type": "object",
            "properties": {
                "goal": {
                    "type": "string",
                    "enum": ["new_customer_welcome", "repeat_buyer_reward", "abandoned_cart", "launch_buzz", "review_incentive"],
                }
            },
            "required": ["goal"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "create_promotion":
        return _create_promotion(tool_input, store)
    if tool_name == "get_active_promotions":
        return _get_active_promotions(store)
    if tool_name == "end_promotion":
        return _end_promotion(tool_input, store)
    if tool_name == "calculate_sale_impact":
        return _calculate_sale_impact(tool_input, store)
    if tool_name == "get_promotion_calendar":
        return _get_promotion_calendar(store)
    if tool_name == "get_promo_recommendations":
        return _get_promo_recommendations(store)
    if tool_name == "generate_coupon_strategy":
        return _generate_coupon_strategy(tool_input["goal"])
    return f"Unknown promotions tool: {tool_name}"


def _create_promotion(data: dict, store: DataStore) -> str:
    promos = store.get("promotions", default=[])
    promo_id = f"PROMO{len(promos) + 1:03d}"
    promo = {
        "id": promo_id,
        "name": data["name"],
        "promo_type": data["promo_type"],
        "discount_value": data["discount_value"],
        "coupon_code": data.get("coupon_code", ""),
        "start_date": data.get("start_date", str(date.today())),
        "end_date": data["end_date"],
        "applies_to": data.get("applies_to", "all_listings"),
        "listing_ids": data.get("listing_ids", []),
        "min_order_value": data.get("min_order_value", 0),
        "status": "active",
        "created_at": str(date.today()),
    }
    promos.append(promo)
    store.set(promos, "promotions")
    store.save()

    setup_steps = [
        "1. Go to Etsy Shop Manager → Marketing → Sales & Discounts",
        f"2. Create a {'coupon' if data['promo_type'] == 'coupon_code' else 'sale'} matching these settings",
        f"3. Discount: {data['discount_value']}{'%' if 'percentage' in data['promo_type'] else ' USD off'}",
        f"4. End date: {data['end_date']}",
    ]
    if data.get("coupon_code"):
        setup_steps.append(f"5. Coupon code: {data['coupon_code']}")

    return json.dumps({
        "success": True,
        "promo_id": promo_id,
        "promotion": promo,
        "etsy_setup_steps": setup_steps,
        "note": "This is tracked locally. You must also create it in Etsy Shop Manager to go live.",
    }, indent=2)


def _get_active_promotions(store: DataStore) -> str:
    promos = store.get("promotions", default=[])
    today = str(date.today())
    active = [p for p in promos if p.get("status") == "active" and p.get("end_date", "9999") >= today]
    expired = [p for p in promos if p.get("end_date", "9999") < today and p.get("status") == "active"]

    # Auto-mark expired
    for p in expired:
        p["status"] = "expired"
    if expired:
        store.set(promos, "promotions")
        store.save()

    return json.dumps({
        "active_promotions": active,
        "count": len(active),
        "recently_expired": expired[:3],
    }, indent=2)


def _end_promotion(data: dict, store: DataStore) -> str:
    promos = store.get("promotions", default=[])
    promo = next((p for p in promos if p["id"] == data["promo_id"]), None)
    if not promo:
        return json.dumps({"error": f"Promotion {data['promo_id']} not found"})
    promo["status"] = "ended_early"
    promo["end_reason"] = data.get("reason", "")
    promo["ended_at"] = str(date.today())
    store.set(promos, "promotions")
    store.save()
    return json.dumps({"success": True, "promo_id": data["promo_id"], "status": "ended_early",
                       "note": "Also end it in Etsy Shop Manager → Marketing → Sales & Discounts."}, indent=2)


def _calculate_sale_impact(data: dict, store: DataStore) -> str:
    discount = data["discount_pct"] / 100
    lift = data.get("expected_sales_lift_pct", 25) / 100
    listings = store.listings
    revenue = store.analytics.get("revenue", {})
    base_monthly = revenue.get("this_month", 0) or 500  # estimate if no data

    discounted_revenue = base_monthly * (1 - discount) * (1 + lift)
    revenue_change = discounted_revenue - base_monthly
    break_even_lift = discount / (1 - discount) * 100

    warnings = []
    if discount >= 0.30:
        warnings.append(f"30%+ discount may signal low value to buyers. Consider 15-20% max.")
    if discount > 0.50:
        warnings.append("50%+ discount rarely profitable after Etsy fees.")

    return json.dumps({
        "discount_pct": data["discount_pct"],
        "expected_sales_lift_pct": data.get("expected_sales_lift_pct", 25),
        "base_monthly_revenue_estimate": round(base_monthly, 2),
        "projected_revenue_during_sale": round(discounted_revenue, 2),
        "revenue_change": round(revenue_change, 2),
        "break_even_sales_lift_needed_pct": round(break_even_lift, 1),
        "verdict": "PROFITABLE" if revenue_change >= 0 else "LOSS",
        "warnings": warnings,
        "recommendation": (
            f"A {data['discount_pct']}% sale needs at least {round(break_even_lift, 0):.0f}% more unit sales to break even on revenue."
        ),
    }, indent=2)


def _get_promotion_calendar(store: DataStore) -> str:
    promos = store.get("promotions", default=[])
    today = str(date.today())
    return json.dumps({
        "active": [p for p in promos if p.get("status") == "active" and p.get("end_date", "") >= today],
        "upcoming": [p for p in promos if p.get("start_date", "") > today],
        "past": [p for p in promos if p.get("end_date", "") < today or p.get("status") in ("expired", "ended_early")],
        "total_promotions_created": len(promos),
    }, indent=2)


def _get_promo_recommendations(store: DataStore) -> str:
    today = date.today()
    month = today.month
    recommendations = []

    seasonal = {
        11: ("Black Friday / Cyber Monday", "20-25% off all items", "Nov 25-Dec 2"),
        12: ("Christmas Last-Minute", "Free shipping or 15% off digital", "Dec 15-23"),
        1: ("New Year Planner Sale", "20% off digital planners", "Jan 1-7"),
        2: ("Valentine's Day", "15% off gifts and wall art", "Feb 1-13"),
        5: ("Mother's Day", "20% off gift-worthy items", "May 1-10"),
    }

    if month in seasonal:
        name, offer, timing = seasonal[month]
        recommendations.append({
            "event": name,
            "suggested_offer": offer,
            "timing": timing,
            "priority": "HIGH",
            "action": f"Create promotion now for {timing}",
        })

    listings = store.listings
    no_sales = [l for l in listings if l.get("sales", 0) == 0 and l.get("views", 0) > 50]
    if no_sales:
        recommendations.append({
            "event": "Convert Browsers to Buyers",
            "suggested_offer": "10% off with coupon code NEWBUYER10",
            "applies_to": [l["id"] for l in no_sales[:5]],
            "priority": "MEDIUM",
            "action": "Listings with views but no sales need a conversion push.",
        })

    return json.dumps({
        "recommendations": recommendations,
        "current_month": today.strftime("%B %Y"),
        "tip": "Holiday sales start 2-3 weeks BEFORE the event. Don't wait.",
    }, indent=2)


def _generate_coupon_strategy(goal: str) -> str:
    strategies = {
        "new_customer_welcome": {
            "goal": "Convert first-time visitors into buyers",
            "code": "WELCOME10",
            "discount": "10% off first order",
            "how_to_share": "Add to shop announcement, Etsy receipt message, Pinterest bio",
            "expiry": "No expiry — always-on",
            "expected_conversion_lift": "15-25%",
        },
        "repeat_buyer_reward": {
            "goal": "Bring back past customers",
            "code": "THANKYOU15",
            "discount": "15% off — say thank you",
            "how_to_share": "Include in package insert for physical orders; mention in digital delivery email",
            "expiry": "30 days",
            "expected_conversion_lift": "Repeat buyers convert at 60-70% vs 2-5% for new visitors",
        },
        "abandoned_cart": {
            "goal": "Recover browsers who didn't buy",
            "code": "COMEBACK10",
            "discount": "10% off — creates urgency",
            "how_to_share": "Etsy sends abandoned cart reminders automatically. Add coupon in Shop Manager.",
            "expiry": "7 days",
            "note": "Etsy allows automatic abandoned cart coupon sending in Shop Manager → Marketing",
        },
        "launch_buzz": {
            "goal": "Drive initial sales for new listings",
            "code": "NEW20",
            "discount": "20% off new arrivals only",
            "how_to_share": "Announce on Pinterest, in shop announcement, share listing link",
            "expiry": "14 days from launch",
            "expected_effect": "Early sales = better Etsy search ranking from day one",
        },
        "review_incentive": {
            "goal": "Encourage customers to leave reviews",
            "code": "REVIEW10",
            "discount": "10% off next order",
            "how_to_share": "Include note in physical package. Add to digital delivery email.",
            "important_warning": "Do NOT offer discounts in EXCHANGE for reviews — violates Etsy policy. Offer it as a general thank-you.",
            "expiry": "60 days",
        },
    }
    strategy = strategies.get(goal, strategies["new_customer_welcome"])
    return json.dumps({"strategy": strategy, "goal": goal}, indent=2)
