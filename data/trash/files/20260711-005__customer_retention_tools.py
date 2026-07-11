"""
Customer Retention Tools — tracks buyer behaviour, identifies churn risk, and drives repeat purchases.

Maximises Customer Lifetime Value (CLV) through win-back campaigns and personalised follow-up.
"""

import json
from datetime import date, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_retention_report",
        "description": (
            "Returns buyer retention metrics from the data store: total buyers, repeat buyers, "
            "repeat rate %, average days between purchases, and top repeat buyers list."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "identify_at_risk_buyers",
        "description": (
            "Returns buyers who purchased 30-90 days ago but haven't returned. "
            "Shows order ID, days since purchase, items bought, and suggested win-back offer."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_winback_campaign",
        "description": (
            "Creates a win-back campaign for lapsed buyers. "
            "Saves to the winback_campaigns data store key and returns a campaign draft."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "campaign_name": {"type": "string", "description": "Name for this campaign, e.g. '60-Day Win-Back May 2026'"},
                "discount_pct": {"type": "integer", "description": "Discount percentage to offer, e.g. 15"},
                "message_template": {"type": "string", "description": "Message body template (use {name} and {discount} placeholders)"},
                "target_segment": {
                    "type": "string",
                    "enum": ["30_day", "60_day", "90_day"],
                    "description": "Which lapsed segment to target",
                },
            },
            "required": ["campaign_name", "discount_pct", "message_template", "target_segment"],
        },
    },
    {
        "name": "track_customer_lifetime_value",
        "description": (
            "Calculates CLV per buyer segment: one-time buyers (avg order value), "
            "repeat 2x (avg total spend), and loyal 3x+ (avg total spend and order frequency). "
            "Returns a comparison table."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "log_repeat_purchase",
        "description": "Logs a repeat purchase event to update buyer retention tracking in the data store.",
        "input_schema": {
            "type": "object",
            "properties": {
                "buyer_email": {"type": "string", "description": "Buyer email address"},
                "order_id": {"type": "string", "description": "New order ID"},
                "product_id": {"type": "string", "description": "Product ID purchased"},
            },
            "required": ["buyer_email", "order_id", "product_id"],
        },
    },
    {
        "name": "get_vip_buyers",
        "description": (
            "Returns the top 10 buyers by total spend. "
            "Shows masked email, order count, total spend, last purchase date, and product categories."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "draft_thank_you_sequence",
        "description": (
            "Returns a 3-email thank-you sequence tailored to a product type: "
            "day 1 (delivery confirm + tips), day 7 (check-in + invite review), "
            "day 21 (related product suggestions)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "product_type": {
                    "type": "string",
                    "description": "Type of product purchased, e.g. 'digital planner', 'wall art print', 'clipart bundle'",
                },
            },
            "required": ["product_type"],
        },
    },
]

TOOL_NAMES: set[str] = {t["name"] for t in TOOL_DEFINITIONS}


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_retention_report":
        return _get_retention_report(store)
    if tool_name == "identify_at_risk_buyers":
        return _identify_at_risk_buyers(store)
    if tool_name == "create_winback_campaign":
        return _create_winback_campaign(tool_input, store)
    if tool_name == "track_customer_lifetime_value":
        return _track_customer_lifetime_value(store)
    if tool_name == "log_repeat_purchase":
        return _log_repeat_purchase(tool_input, store)
    if tool_name == "get_vip_buyers":
        return _get_vip_buyers(store)
    if tool_name == "draft_thank_you_sequence":
        return _draft_thank_you_sequence(tool_input["product_type"])
    return f"Unknown customer retention tool: {tool_name}"


def _get_retention_report(store: DataStore) -> str:
    buyers = store.get("buyer_tracking", default={})
    total_buyers = len(buyers)
    repeat_buyers = [email for email, data in buyers.items() if data.get("order_count", 1) >= 2]
    repeat_rate = round(len(repeat_buyers) / total_buyers * 100, 1) if total_buyers else 0.0

    # Calculate average days between purchases for repeat buyers
    avg_days_between = 0
    intervals = []
    for email in repeat_buyers:
        orders = buyers[email].get("orders", [])
        if len(orders) >= 2:
            dates = sorted([o.get("date", "") for o in orders if o.get("date")])
            for i in range(1, len(dates)):
                try:
                    d1 = date.fromisoformat(dates[i - 1])
                    d2 = date.fromisoformat(dates[i])
                    intervals.append((d2 - d1).days)
                except ValueError:
                    pass
    avg_days_between = round(sum(intervals) / len(intervals), 1) if intervals else 0.0

    top_repeat = sorted(
        [{"email": _mask_email(e), "order_count": d.get("order_count", 1)} for e, d in buyers.items() if d.get("order_count", 1) >= 2],
        key=lambda x: x["order_count"],
        reverse=True,
    )[:5]

    return json.dumps(
        {
            "as_of": str(date.today()),
            "retention_metrics": {
                "total_buyers": total_buyers,
                "repeat_buyers": len(repeat_buyers),
                "repeat_rate_pct": repeat_rate,
                "avg_days_between_purchases": avg_days_between,
            },
            "top_repeat_buyers": top_repeat,
            "benchmark": "Industry benchmark: 20-30% repeat rate is healthy for digital goods on Etsy.",
        },
        indent=2,
    )


def _identify_at_risk_buyers(store: DataStore) -> str:
    buyers = store.get("buyer_tracking", default={})
    today = date.today()
    at_risk = []

    for email, data in buyers.items():
        orders = data.get("orders", [])
        if not orders:
            continue
        latest_date_str = max((o.get("date", "") for o in orders if o.get("date")), default="")
        if not latest_date_str:
            continue
        try:
            latest_date = date.fromisoformat(latest_date_str)
        except ValueError:
            continue
        days_since = (today - latest_date).days
        if 30 <= days_since <= 90:
            last_order = next((o for o in reversed(orders) if o.get("date") == latest_date_str), orders[-1])
            discount = 20 if days_since >= 60 else 10
            at_risk.append(
                {
                    "buyer_email": _mask_email(email),
                    "order_id": last_order.get("order_id", "unknown"),
                    "days_since_purchase": days_since,
                    "items_bought": last_order.get("product_id", "unknown"),
                    "suggested_win_back_offer": f"{discount}% off coupon — 'We miss you!'",
                    "urgency": "HIGH" if days_since >= 60 else "MEDIUM",
                }
            )

    at_risk.sort(key=lambda x: x["days_since_purchase"], reverse=True)
    return json.dumps(
        {
            "as_of": str(today),
            "at_risk_buyers": at_risk,
            "count": len(at_risk),
            "action": (
                "Use create_winback_campaign to send a targeted offer to the 60+ day segment first — "
                "they are highest churn risk."
            ),
        },
        indent=2,
    )


def _create_winback_campaign(data: dict, store: DataStore) -> str:
    campaigns = store.get("winback_campaigns", default=[])
    segment_labels = {"30_day": "30-day lapsed", "60_day": "60-day lapsed", "90_day": "90-day lapsed"}
    segment = data["target_segment"]
    discount = data["discount_pct"]

    subject_lines = {
        "30_day": f"We noticed you haven't been back — here's {discount}% off just for you",
        "60_day": f"It's been a while! Come back with {discount}% off your next order",
        "90_day": f"We really miss you — {discount}% off to welcome you back",
    }

    campaign = {
        "campaign_name": data["campaign_name"],
        "target_segment": segment,
        "segment_label": segment_labels.get(segment, segment),
        "discount_pct": discount,
        "message_template": data["message_template"],
        "subject_line": subject_lines.get(segment, f"{discount}% off — come back!"),
        "coupon_code": f"WINBACK{discount}",
        "created_at": str(date.today()),
        "status": "draft",
    }

    campaigns.append(campaign)
    store.set(campaigns, "winback_campaigns")
    store.save()

    return json.dumps(
        {
            "success": True,
            "campaign": campaign,
            "send_tip": (
                "Send via Etsy's message system or your email provider. "
                "Best send times: Tuesday or Thursday, 10am-12pm buyer's local time."
            ),
        },
        indent=2,
    )


def _track_customer_lifetime_value(store: DataStore) -> str:
    buyers = store.get("buyer_tracking", default={})
    one_time, repeat_2x, loyal_3x = [], [], []

    for email, data in buyers.items():
        order_count = data.get("order_count", 1)
        total_spend = data.get("total_spend", 0.0)
        orders = data.get("orders", [])
        avg_order = round(total_spend / order_count, 2) if order_count else 0

        if order_count == 1:
            one_time.append({"avg_order": avg_order})
        elif order_count == 2:
            repeat_2x.append({"total_spend": total_spend, "avg_order": avg_order})
        else:
            loyal_3x.append({"total_spend": total_spend, "order_count": order_count})

    def safe_avg(items, key):
        vals = [i[key] for i in items if key in i]
        return round(sum(vals) / len(vals), 2) if vals else 0.0

    loyal_freq = round(
        sum(i["order_count"] for i in loyal_3x) / len(loyal_3x), 1
    ) if loyal_3x else 0.0

    return json.dumps(
        {
            "as_of": str(date.today()),
            "clv_by_segment": {
                "one_time_buyers": {
                    "count": len(one_time),
                    "avg_order_value": safe_avg(one_time, "avg_order"),
                    "estimated_clv": safe_avg(one_time, "avg_order"),
                },
                "repeat_2x_buyers": {
                    "count": len(repeat_2x),
                    "avg_total_spend": safe_avg(repeat_2x, "total_spend"),
                    "estimated_clv": safe_avg(repeat_2x, "total_spend"),
                },
                "loyal_3x_plus_buyers": {
                    "count": len(loyal_3x),
                    "avg_total_spend": safe_avg(loyal_3x, "total_spend"),
                    "avg_order_frequency": loyal_freq,
                    "estimated_clv": safe_avg(loyal_3x, "total_spend"),
                },
            },
            "insight": (
                "Loyal 3x+ buyers generate the highest CLV. "
                "Prioritise converting 2x buyers into 3x with personalised follow-up."
            ),
        },
        indent=2,
    )


def _log_repeat_purchase(data: dict, store: DataStore) -> str:
    buyers = store.get("buyer_tracking", default={})
    email = data["buyer_email"]
    order_id = data["order_id"]
    product_id = data["product_id"]
    today_str = str(date.today())

    if email not in buyers:
        buyers[email] = {"order_count": 0, "total_spend": 0.0, "orders": []}

    buyers[email]["order_count"] = buyers[email].get("order_count", 0) + 1
    buyers[email].setdefault("orders", []).append(
        {"order_id": order_id, "product_id": product_id, "date": today_str}
    )

    store.set(buyers, "buyer_tracking")
    store.save()

    return json.dumps(
        {
            "success": True,
            "buyer": _mask_email(email),
            "order_id": order_id,
            "product_id": product_id,
            "total_orders_for_buyer": buyers[email]["order_count"],
            "logged_at": today_str,
        },
        indent=2,
    )


def _get_vip_buyers(store: DataStore) -> str:
    buyers = store.get("buyer_tracking", default={})
    ranked = sorted(
        [
            {
                "email_masked": _mask_email(email),
                "order_count": data.get("order_count", 1),
                "total_spend": data.get("total_spend", 0.0),
                "last_purchase": max(
                    (o.get("date", "") for o in data.get("orders", []) if o.get("date")),
                    default="unknown",
                ),
                "product_categories": list(
                    {o.get("product_id", "").split("-")[0] for o in data.get("orders", []) if o.get("product_id")}
                ),
            }
            for email, data in buyers.items()
        ],
        key=lambda x: x["total_spend"],
        reverse=True,
    )[:10]

    return json.dumps(
        {
            "as_of": str(date.today()),
            "vip_buyers": ranked,
            "count": len(ranked),
            "tip": (
                "VIP buyers (3+ orders) deserve priority support. "
                "Send them exclusive early access or a loyalty discount to keep them engaged."
            ),
        },
        indent=2,
    )


def _draft_thank_you_sequence(product_type: str) -> str:
    pt = product_type.lower()

    # Tailor tips based on product type
    if "planner" in pt:
        day1_tip = "Pro tip: print at 100% scale on US Letter paper for perfect margins. You can also use it digitally in GoodNotes or Notability!"
        day7_note = "Have you had a chance to set up your planner? We'd love to know how it's working for you."
        day21_suggestion = "You might also love our habit tracker bundle and goal-setting worksheet pack — perfect companions to your planner."
    elif "wall art" in pt or "print" in pt:
        day1_tip = "Pro tip: print at your local print shop on matte paper for a gallery-quality finish. Standard sizes (8x10, 11x14, 16x20) work perfectly."
        day7_note = "We hope your print looks amazing in your space! Sharing a photo on Pinterest or Instagram and tagging us means the world."
        day21_suggestion = "Complete the look — check out our matching art sets and gallery wall bundles designed to complement your new print."
    elif "clipart" in pt or "svg" in pt:
        day1_tip = "Pro tip: the PNG files have transparent backgrounds for easy layering. The SVG files are fully scalable for any size project."
        day7_note = "We'd love to see what you've created with the clipart! Share your project with us — we feature customer creations in our newsletter."
        day21_suggestion = "Looking for more? Our seasonal clipart bundles and matching paper texture packs are a perfect extension of what you just downloaded."
    else:
        day1_tip = "Pro tip: check the included README for usage instructions and licensing details. You can use this for personal and small commercial projects."
        day7_note = "We hope everything is working perfectly for your project. If you have any questions, just reply — we respond within 24 hours."
        day21_suggestion = "Explore our full shop for complementary products — most customers find our bundle deals save them significant time and money."

    sequence = [
        {
            "email_number": 1,
            "send_day": 1,
            "subject": f"Your {product_type} download is ready — here's how to get the best results",
            "purpose": "Delivery confirmation + usage tips",
            "body": (
                f"Hi {{name}},\n\n"
                f"Thank you so much for your purchase of our {product_type}! "
                f"Your download is ready in your Etsy account under 'Purchases and Reviews'.\n\n"
                f"{day1_tip}\n\n"
                f"If you have any trouble accessing your download, just message us and we'll sort it out right away.\n\n"
                f"With gratitude,\nThe OnBrandCraftz Team"
            ),
        },
        {
            "email_number": 2,
            "send_day": 7,
            "subject": f"How's your {product_type} working for you? + a small favour",
            "purpose": "Check-in + review invite",
            "body": (
                f"Hi {{name}},\n\n"
                f"{day7_note}\n\n"
                f"If you're happy with your purchase, leaving us a review on Etsy takes just 30 seconds "
                f"and makes an enormous difference for a small shop like ours. "
                f"Here's the link: [Etsy Review Link]\n\n"
                f"Thank you for supporting independent creators!\n\n"
                f"Warmly,\nThe OnBrandCraftz Team"
            ),
        },
        {
            "email_number": 3,
            "send_day": 21,
            "subject": f"Customers who bought {product_type} also loved these...",
            "purpose": "Related product suggestions",
            "body": (
                f"Hi {{name}},\n\n"
                f"It's been a few weeks since you downloaded your {product_type} — we hope it's been useful!\n\n"
                f"{day21_suggestion}\n\n"
                f"As a returning customer, use code THANKYOU10 for 10% off your next order.\n\n"
                f"Shop now: [Shop Link]\n\n"
                f"Thanks again for your support,\nThe OnBrandCraftz Team"
            ),
        },
    ]

    return json.dumps(
        {
            "product_type": product_type,
            "sequence_length": 3,
            "emails": sequence,
            "usage_note": (
                "Send via Etsy messages or your email provider. "
                "Personalise the {name} placeholder with the buyer's first name where possible."
            ),
        },
        indent=2,
    )


def _mask_email(email: str) -> str:
    """Returns a privacy-safe masked version of an email address."""
    if "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    masked_local = local[:2] + "***" if len(local) > 2 else "***"
    return f"{masked_local}@{domain}"
