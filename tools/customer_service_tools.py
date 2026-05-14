"""Tool definitions and implementations for the Customer Service Agent."""

import json
from datetime import date, datetime, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {
        "name": "get_messages",
        "description": "Retrieve customer messages, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter messages by status",
                    "enum": ["all", "unread", "replied"],
                }
            },
            "required": ["status"],
        },
    },
    {
        "name": "get_message_details",
        "description": "Get the full details of a specific customer message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The message ID, e.g. M201"}
            },
            "required": ["message_id"],
        },
    },
    {
        "name": "draft_reply",
        "description": "Draft and send a reply to a customer message. Marks the message as replied.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The message ID to reply to"},
                "reply_text": {"type": "string", "description": "The reply message to send"},
            },
            "required": ["message_id", "reply_text"],
        },
    },
    {
        "name": "get_reviews",
        "description": "Retrieve customer reviews, optionally filtered by responded status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Filter reviews",
                    "enum": ["all", "unresponded", "responded"],
                }
            },
            "required": ["filter"],
        },
    },
    {
        "name": "respond_to_review",
        "description": "Post a public response to a customer review. Professional and grateful tone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "The review ID, e.g. R301"},
                "response_text": {"type": "string", "description": "The public response text"},
            },
            "required": ["review_id", "response_text"],
        },
    },
    {
        "name": "get_customer_satisfaction",
        "description": "Get an overview of customer satisfaction: ratings distribution and response rates.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_response_template",
        "description": "Returns a pre-written response template for common Etsy customer service scenarios. Templates include [PLACEHOLDERS] for buyer name, order ID, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "The CS scenario to get a template for.",
                    "enum": [
                        "order_delay",
                        "custom_request",
                        "wrong_item",
                        "refund_request",
                        "five_star_thank_you",
                        "negative_review_response",
                        "where_is_my_order",
                        "custom_order_inquiry",
                    ],
                }
            },
            "required": ["scenario"],
        },
    },
    {
        "name": "analyze_review_sentiment",
        "description": "Analyzes all reviews and returns a sentiment breakdown including praise themes, complaint patterns, NPS estimate, and trending direction.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "flag_at_risk_customers",
        "description": "Identifies customers who need proactive outreach: low-rated unresponded reviews, unread messages >24h, and overdue orders. Returns a prioritized list with reason and recommended_action.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_cs_performance_metrics",
        "description": "Returns CS team performance stats: response_rate, avg_response_time_estimate, review_response_rate, star_rating_average, open_issues_count, and at_risk_score (0-100).",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "create_saved_reply",
        "description": "Saves a custom reply template to the data store for future reuse.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "A short identifier for this saved reply, e.g. 'holiday_delay_2025'.",
                },
                "subject": {
                    "type": "string",
                    "description": "The subject line or title of the saved reply.",
                },
                "body": {
                    "type": "string",
                    "description": "The full body text of the saved reply.",
                },
            },
            "required": ["name", "subject", "body"],
        },
    },
    {
        "name": "escalate_to_ceo",
        "description": "Logs a customer issue as escalated to the CEO. Use for refund disputes, shipping losses, chargebacks, negative review crises, and repeat complaints.",
        "input_schema": {
            "type": "object",
            "properties": {
                "issue_type": {
                    "type": "string",
                    "description": "Category of the issue.",
                    "enum": [
                        "refund_dispute",
                        "negative_review_crisis",
                        "shipping_loss",
                        "product_defect",
                        "chargeback",
                        "repeat_complaint",
                    ],
                },
                "customer_name": {
                    "type": "string",
                    "description": "Name of the customer involved.",
                },
                "order_id": {
                    "type": "string",
                    "description": "The order ID related to this escalation.",
                },
                "description": {
                    "type": "string",
                    "description": "Full description of the issue.",
                },
                "severity": {
                    "type": "string",
                    "description": "Severity level of the issue.",
                    "enum": ["low", "medium", "high", "critical"],
                },
            },
            "required": ["issue_type", "customer_name", "order_id", "description", "severity"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_messages":
        return _get_messages(tool_input["status"], store)
    if tool_name == "get_message_details":
        return _get_message_details(tool_input["message_id"], store)
    if tool_name == "draft_reply":
        return _draft_reply(tool_input["message_id"], tool_input["reply_text"], store)
    if tool_name == "get_reviews":
        return _get_reviews(tool_input["filter"], store)
    if tool_name == "respond_to_review":
        return _respond_to_review(tool_input["review_id"], tool_input["response_text"], store)
    if tool_name == "get_customer_satisfaction":
        return _get_customer_satisfaction(store)
    if tool_name == "get_response_template":
        return _get_response_template(tool_input["scenario"])
    if tool_name == "analyze_review_sentiment":
        return _analyze_review_sentiment(store)
    if tool_name == "flag_at_risk_customers":
        return _flag_at_risk_customers(store)
    if tool_name == "get_cs_performance_metrics":
        return _get_cs_performance_metrics(store)
    if tool_name == "create_saved_reply":
        return _create_saved_reply(tool_input["name"], tool_input["subject"], tool_input["body"], store)
    if tool_name == "escalate_to_ceo":
        return _escalate_to_ceo(
            tool_input["issue_type"],
            tool_input["customer_name"],
            tool_input["order_id"],
            tool_input["description"],
            tool_input["severity"],
            store,
        )
    return f"Unknown customer service tool: {tool_name}"


def _get_messages(status: str, store: DataStore) -> str:
    messages = store.messages if status == "all" else [m for m in store.messages if m["status"] == status]
    return json.dumps({"messages": messages, "count": len(messages)}, indent=2)


def _get_message_details(message_id: str, store: DataStore) -> str:
    msg = store.find_message(message_id)
    if not msg:
        return json.dumps({"error": f"Message {message_id} not found"})
    return json.dumps(msg, indent=2)


def _draft_reply(message_id: str, reply_text: str, store: DataStore) -> str:
    msg = store.find_message(message_id)
    if not msg:
        return json.dumps({"error": f"Message {message_id} not found"})

    msg["status"] = "replied"
    msg["reply"] = reply_text
    msg["replied_at"] = str(date.today())
    store.save()
    return json.dumps(
        {
            "success": True,
            "message_id": message_id,
            "sent_to": msg.get("buyer_name"),
            "reply": reply_text,
            "sent_at": str(date.today()),
        },
        indent=2,
    )


def _get_reviews(filter_by: str, store: DataStore) -> str:
    if filter_by == "unresponded":
        reviews = [r for r in store.reviews if not r.get("responded")]
    elif filter_by == "responded":
        reviews = [r for r in store.reviews if r.get("responded")]
    else:
        reviews = store.reviews
    return json.dumps({"reviews": reviews, "count": len(reviews)}, indent=2)


def _respond_to_review(review_id: str, response_text: str, store: DataStore) -> str:
    review = store.find_review(review_id)
    if not review:
        return json.dumps({"error": f"Review {review_id} not found"})

    review["responded"] = True
    review["shop_response"] = response_text
    review["responded_at"] = str(date.today())
    store.save()
    return json.dumps(
        {
            "success": True,
            "review_id": review_id,
            "reviewer": review.get("buyer_name"),
            "rating": review.get("rating"),
            "response": response_text,
        },
        indent=2,
    )


def _get_customer_satisfaction(store: DataStore) -> str:
    reviews = store.reviews
    if not reviews:
        return json.dumps({"message": "No reviews yet."})

    ratings = [r["rating"] for r in reviews]
    avg = sum(ratings) / len(ratings)
    distribution = {str(i): ratings.count(i) for i in range(1, 6)}
    responded = sum(1 for r in reviews if r.get("responded"))

    return json.dumps(
        {
            "average_rating": round(avg, 2),
            "total_reviews": len(reviews),
            "rating_distribution": distribution,
            "response_rate": f"{responded / len(reviews) * 100:.0f}%",
            "responded_count": responded,
            "unresponded_count": len(reviews) - responded,
            "unread_messages": sum(1 for m in store.messages if m["status"] == "unread"),
        },
        indent=2,
    )


# ── New tool helpers ──────────────────────────────────────────────────────────

_RESPONSE_TEMPLATES = {
    "order_delay": (
        "Hi [BUYER_NAME]! 👋 Thank you so much for your patience — I wanted to reach out personally "
        "about order [ORDER_ID]. We're experiencing a slight delay due to [REASON], and your order "
        "is now expected to ship by [NEW_SHIP_DATE]. Every piece is made to order with care, and I "
        "want yours to be perfect. If this timeline doesn't work for you, please let me know and "
        "we'll find a solution together. Thank you for supporting a small maker! 🙏"
    ),
    "custom_request": (
        "Hi [BUYER_NAME]! I'd love to bring your custom idea to life! 🎨 Here's what I need to get "
        "started: [CUSTOM_DETAILS_NEEDED]. Once I have those details I can give you a firm price and "
        "turnaround time. Custom orders typically take [TURNAROUND] from approval to shipping. Feel "
        "free to message me any inspiration photos or color preferences — the more detail, the "
        "better the result. I can't wait to create something unique just for you!"
    ),
    "wrong_item": (
        "Hi [BUYER_NAME], I'm so sorry about that — you should have received [CORRECT_ITEM] and I "
        "completely understand how frustrating that is. Please don't worry; I'm going to make this "
        "right immediately. I'll ship out the correct item today at no extra cost, and you're "
        "welcome to keep the incorrect piece as a little gift from us. You'll receive a tracking "
        "number within 24 hours. Again, I sincerely apologize for the mix-up — this is not the "
        "OnBrandCraftz standard and I appreciate your grace. 💙"
    ),
    "refund_request": (
        "Hi [BUYER_NAME], thank you for reaching out about order [ORDER_ID]. I completely understand "
        "your concern and I want to make sure you're 100% happy. I'm reviewing your case right now "
        "and will get back to you within [TIMEFRAME] with a resolution. In the meantime, could you "
        "share [ADDITIONAL_INFO_NEEDED] so I can expedite this for you? Your satisfaction is my "
        "top priority and I won't rest until this is resolved. Thank you for giving me the "
        "opportunity to make it right."
    ),
    "five_star_thank_you": (
        "Thank you so much, [BUYER_NAME]! 🌟 Your kind words made our whole day — we pour so much "
        "love into every piece, and it means the world to hear that it found the perfect home with "
        "you. [PERSONALIZED_DETAIL_FROM_REVIEW]. We'd love to see you again — we add new designs "
        "regularly and offer a loyalty discount for returning customers. Welcome to the "
        "OnBrandCraftz family! 💙"
    ),
    "negative_review_response": (
        "Hi [BUYER_NAME], thank you for your honest feedback — I'm truly sorry your experience "
        "didn't meet expectations. [SPECIFIC_ACKNOWLEDGMENT_OF_ISSUE]. I've taken note of your "
        "concern and [CORRECTIVE_ACTION_TAKEN]. I'd love the chance to make this right for you — "
        "please reach out to me directly so we can find a solution that leaves you smiling. Your "
        "satisfaction genuinely matters to us. 🙏"
    ),
    "where_is_my_order": (
        "Hi [BUYER_NAME]! Great news — your order [ORDER_ID] is on its way! 📦 Here are the latest "
        "tracking details: [TRACKING_NUMBER] via [CARRIER]. Based on current estimates it should "
        "arrive by [ESTIMATED_DELIVERY]. If you don't see an update within 48 hours or have any "
        "concerns, please message me right away and I'll personally investigate. Thank you for your "
        "patience — handmade items are worth the wait! 🎉"
    ),
    "custom_order_inquiry": (
        "Hi [BUYER_NAME]! Thank you for your interest in a custom order — I love bringing unique "
        "ideas to life! 🌟 To put together an accurate quote for you, I have a few quick questions: "
        "1) What size or dimensions are you thinking? 2) Any specific colors or finishes? "
        "3) Do you have a reference image or inspiration? Custom orders start at $[BASE_PRICE] and "
        "turnaround is typically [TURNAROUND] after design approval. I'm excited to create "
        "something one-of-a-kind just for you — let's chat! 🎨"
    ),
}


def _get_response_template(scenario: str) -> str:
    template = _RESPONSE_TEMPLATES.get(scenario)
    if not template:
        return json.dumps({"error": f"No template found for scenario: {scenario}"})
    return json.dumps(
        {
            "scenario": scenario,
            "template": template,
            "note": "Replace all [PLACEHOLDER] values with the customer's specific details before sending.",
        },
        indent=2,
    )


def _analyze_review_sentiment(store: DataStore) -> str:
    reviews = store.reviews
    if not reviews:
        return json.dumps({"message": "No reviews to analyze yet."})

    positive = [r for r in reviews if r.get("rating", 0) >= 4]
    neutral = [r for r in reviews if r.get("rating", 0) == 3]
    negative = [r for r in reviews if r.get("rating", 0) <= 2]

    total = len(reviews)
    five_star_pct = sum(1 for r in reviews if r.get("rating") == 5) / total * 100
    low_star_pct = len(negative) / total * 100
    nps_estimate = round(five_star_pct - low_star_pct, 1)

    praise_keywords = ["quality", "fast", "beautiful", "perfect", "love"]
    complaint_keywords = ["slow", "damaged", "wrong", "disappointed"]

    def _extract_themes(review_list: list, keywords: list) -> list:
        found = []
        for kw in keywords:
            for r in review_list:
                body = (r.get("body") or r.get("review_text") or "").lower()
                if kw in body:
                    found.append(kw)
                    break
        return found

    common_praise = _extract_themes(positive, praise_keywords)
    common_complaints = _extract_themes(negative, complaint_keywords)

    # Trending direction: compare avg rating of most-recent half vs older half
    trending = "stable"
    if len(reviews) >= 4:
        sorted_reviews = sorted(reviews, key=lambda r: r.get("date", ""), reverse=False)
        mid = len(sorted_reviews) // 2
        older_avg = sum(r.get("rating", 0) for r in sorted_reviews[:mid]) / mid
        recent_avg = sum(r.get("rating", 0) for r in sorted_reviews[mid:]) / (len(sorted_reviews) - mid)
        if recent_avg > older_avg + 0.3:
            trending = "improving"
        elif recent_avg < older_avg - 0.3:
            trending = "declining"

    return json.dumps(
        {
            "total_reviews": total,
            "positive_count": len(positive),
            "neutral_count": len(neutral),
            "negative_count": len(negative),
            "common_praise_themes": common_praise,
            "common_complaints": common_complaints,
            "net_promoter_score_estimate": nps_estimate,
            "trending_direction": trending,
        },
        indent=2,
    )


def _flag_at_risk_customers(store: DataStore) -> str:
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    at_risk = []

    # (a) Low-rated reviews without a response in the last 30 days
    for review in store.reviews:
        rating = review.get("rating", 5)
        responded = review.get("responded", False)
        review_date_str = review.get("date") or review.get("created_at", "")
        if rating <= 3 and not responded:
            try:
                review_date = date.fromisoformat(str(review_date_str)[:10])
                if review_date >= thirty_days_ago:
                    at_risk.append(
                        {
                            "priority": "high" if rating <= 2 else "medium",
                            "type": "unresponded_negative_review",
                            "customer_name": review.get("buyer_name", "Unknown"),
                            "identifier": review.get("id"),
                            "detail": f"{rating}-star review left on {review_date_str} with no shop response",
                            "reason": f"Unanswered {rating}-star review damages brand reputation",
                            "recommended_action": "Respond publicly within 24h — apologize, take conversation private",
                        }
                    )
            except (ValueError, TypeError):
                pass

    # (b) Messages unread for >24h (approximated by status="unread")
    for msg in store.messages:
        if msg.get("status") == "unread":
            sent_date_str = msg.get("date") or msg.get("created_at", "")
            try:
                sent_date = date.fromisoformat(str(sent_date_str)[:10])
                if (today - sent_date).days >= 1:
                    at_risk.append(
                        {
                            "priority": "high",
                            "type": "unread_message_overdue",
                            "customer_name": msg.get("buyer_name", "Unknown"),
                            "identifier": msg.get("id"),
                            "detail": f"Message received {sent_date_str} is still unread",
                            "reason": "Etsy penalizes slow response rate; customer feels ignored",
                            "recommended_action": "Reply immediately — even a brief acknowledgment stops the clock",
                        }
                    )
            except (ValueError, TypeError):
                pass

    # (c) Overdue orders — ship_by date has passed and status is not shipped/completed
    active_statuses = {"processing", "in_production", "pending", "open"}
    for order in store.orders:
        status = (order.get("status") or "").lower()
        ship_by_str = order.get("ship_by") or order.get("ship_by_date", "")
        if status in active_statuses and ship_by_str:
            try:
                ship_by = date.fromisoformat(str(ship_by_str)[:10])
                if ship_by < today:
                    days_overdue = (today - ship_by).days
                    at_risk.append(
                        {
                            "priority": "critical" if days_overdue >= 3 else "high",
                            "type": "overdue_order",
                            "customer_name": order.get("buyer_name", "Unknown"),
                            "identifier": order.get("id"),
                            "detail": f"Order was due to ship by {ship_by_str} ({days_overdue} day(s) overdue)",
                            "reason": "Late shipments are the #1 cause of negative reviews",
                            "recommended_action": "Message customer proactively with updated ship date and apology",
                        }
                    )
            except (ValueError, TypeError):
                pass

    # Sort by priority: critical > high > medium > low
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    at_risk.sort(key=lambda x: priority_order.get(x["priority"], 9))

    return json.dumps(
        {
            "at_risk_count": len(at_risk),
            "at_risk_customers": at_risk,
            "summary": (
                f"{len(at_risk)} customer(s) need immediate attention."
                if at_risk
                else "No at-risk customers identified — great job staying on top of CS!"
            ),
        },
        indent=2,
    )


def _get_cs_performance_metrics(store: DataStore) -> str:
    reviews = store.reviews
    messages = store.messages
    orders = store.orders
    today = date.today()

    # Response rate for messages
    total_messages = len(messages)
    replied_messages = sum(1 for m in messages if m.get("status") == "replied")
    unread_messages = sum(1 for m in messages if m.get("status") == "unread")
    response_rate = (replied_messages / total_messages * 100) if total_messages else 100.0

    # Average response time estimate based on unread ratio
    if total_messages == 0 or unread_messages == 0:
        avg_response_time = "< 1 day"
    elif unread_messages / total_messages < 0.1:
        avg_response_time = "< 1 day"
    elif unread_messages / total_messages < 0.3:
        avg_response_time = "1-2 days"
    else:
        avg_response_time = "> 2 days"

    # Review metrics
    total_reviews = len(reviews)
    responded_reviews = sum(1 for r in reviews if r.get("responded"))
    review_response_rate = (responded_reviews / total_reviews * 100) if total_reviews else 100.0
    ratings = [r.get("rating", 0) for r in reviews]
    star_rating_average = round(sum(ratings) / len(ratings), 2) if ratings else 0.0

    # Overdue orders
    active_statuses = {"processing", "in_production", "pending", "open"}
    overdue_orders = 0
    for order in orders:
        status = (order.get("status") or "").lower()
        ship_by_str = order.get("ship_by") or order.get("ship_by_date", "")
        if status in active_statuses and ship_by_str:
            try:
                if date.fromisoformat(str(ship_by_str)[:10]) < today:
                    overdue_orders += 1
            except (ValueError, TypeError):
                pass

    unresponded_reviews = total_reviews - responded_reviews
    open_issues_count = unread_messages + unresponded_reviews + overdue_orders

    # at_risk_score: 0–100 based on open issues and rating
    issue_score = min(open_issues_count * 10, 60)
    rating_penalty = max(0, (4.5 - star_rating_average) * 20) if star_rating_average > 0 else 0
    response_penalty = max(0, (80 - response_rate) * 0.5)
    at_risk_score = min(100, round(issue_score + rating_penalty + response_penalty))

    return json.dumps(
        {
            "response_rate": f"{response_rate:.0f}%",
            "avg_response_time_estimate": avg_response_time,
            "review_response_rate": f"{review_response_rate:.0f}%",
            "star_rating_average": star_rating_average,
            "open_issues_count": open_issues_count,
            "open_issues_breakdown": {
                "unread_messages": unread_messages,
                "unresponded_reviews": unresponded_reviews,
                "overdue_orders": overdue_orders,
            },
            "at_risk_score": at_risk_score,
            "at_risk_label": (
                "healthy" if at_risk_score < 20
                else "needs attention" if at_risk_score < 50
                else "critical"
            ),
        },
        indent=2,
    )


def _create_saved_reply(name: str, subject: str, body: str, store: DataStore) -> str:
    store.shop.setdefault("saved_replies", {})[name] = {"subject": subject, "body": body}
    store.save()
    return json.dumps(
        {
            "success": True,
            "saved_reply_name": name,
            "subject": subject,
            "body_preview": body[:120] + ("..." if len(body) > 120 else ""),
            "message": f"Saved reply '{name}' stored successfully. Retrieve it any time to reuse.",
        },
        indent=2,
    )


_CEO_ACTIONS = {
    "refund_dispute": "Review order history and authorize refund amount; respond to customer within 1 hour",
    "negative_review_crisis": "Assess review content; decide whether to offer resolution or flag for Etsy if violates policy",
    "shipping_loss": "File carrier claim immediately; issue replacement or full refund; contact customer with resolution",
    "product_defect": "Pull batch records; check if systematic issue; arrange replacement and review QC process",
    "chargeback": "Gather proof of delivery and communication; submit dispute to Etsy Payments within 24 hours",
    "repeat_complaint": "Identify root cause pattern; update SOPs; personally reach out to customer with goodwill offer",
}


def _escalate_to_ceo(
    issue_type: str,
    customer_name: str,
    order_id: str,
    description: str,
    severity: str,
    store: DataStore,
) -> str:
    timestamp = datetime.utcnow().isoformat() + "Z"
    escalation = {
        "id": f"ESC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "timestamp": timestamp,
        "issue_type": issue_type,
        "customer_name": customer_name,
        "order_id": order_id,
        "description": description,
        "severity": severity,
        "status": "open",
        "recommended_ceo_action": _CEO_ACTIONS.get(issue_type, "Review and respond appropriately"),
    }
    store.shop.setdefault("escalations", []).append(escalation)
    store.save()
    return json.dumps(
        {
            "success": True,
            "escalation_id": escalation["id"],
            "severity": severity,
            "issue_type": issue_type,
            "customer_name": customer_name,
            "order_id": order_id,
            "timestamp": timestamp,
            "recommended_ceo_action": escalation["recommended_ceo_action"],
            "message": (
                f"Escalation {escalation['id']} logged as {severity.upper()}. "
                "CEO has been notified and should take action per the recommended_ceo_action above."
            ),
        },
        indent=2,
    )
