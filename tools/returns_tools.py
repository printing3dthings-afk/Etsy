"""
Returns & Disputes Tools — handles refund requests, Etsy cases, and return tracking.

Etsy Buyer Protection: buyers can open a case if item not received or not as described.
Digital products policy: Etsy generally does NOT require refunds for digital downloads
unless the file is corrupt/undeliverable or significantly not as described.
"""

import json
from datetime import date, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_open_cases",
        "description": "Get all open Etsy dispute cases and return requests requiring action.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "log_return_request",
        "description": "Log a return or refund request from a customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "reason": {
                    "type": "string",
                    "enum": ["not_as_described", "item_not_received", "damaged", "wrong_item",
                             "changed_mind", "digital_file_issue", "quality_issue", "other"],
                },
                "item_type": {
                    "type": "string",
                    "enum": ["physical", "digital"],
                },
                "description": {"type": "string", "description": "Customer's full description of the issue"},
                "amount": {"type": "number", "description": "Order amount for refund calculation"},
            },
            "required": ["order_id", "reason", "item_type", "amount"],
        },
    },
    {
        "name": "get_recommended_response",
        "description": "Get a recommended resolution and draft response for a specific return/dispute case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
            },
            "required": ["case_id"],
        },
    },
    {
        "name": "process_refund",
        "description": "Log that a refund has been issued for a case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "refund_amount": {"type": "number"},
                "refund_type": {
                    "type": "string",
                    "enum": ["full_refund", "partial_refund", "replacement_sent", "resend_digital", "no_refund"],
                },
                "notes": {"type": "string"},
            },
            "required": ["case_id", "refund_amount", "refund_type"],
        },
    },
    {
        "name": "get_return_analytics",
        "description": "Get return/dispute statistics: rate by product, common reasons, financial impact.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "draft_case_response",
        "description": "Draft a professional response to an Etsy buyer protection case.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_id": {"type": "string"},
                "situation": {
                    "type": "string",
                    "enum": ["item_not_received", "not_as_described", "damaged", "digital_issue", "buyer_remorse"],
                },
                "our_position": {
                    "type": "string",
                    "enum": ["offer_full_refund", "offer_partial_refund", "offer_replacement",
                             "resend_digital_file", "dispute_claim", "no_refund_policy"],
                },
            },
            "required": ["situation", "our_position"],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_open_cases":
        return _get_open_cases(store)
    if tool_name == "log_return_request":
        return _log_return_request(tool_input, store)
    if tool_name == "get_recommended_response":
        return _get_recommended_response(tool_input["case_id"], store)
    if tool_name == "process_refund":
        return _process_refund(tool_input, store)
    if tool_name == "get_return_analytics":
        return _get_return_analytics(store)
    if tool_name == "draft_case_response":
        return _draft_case_response(tool_input)
    return f"Unknown returns tool: {tool_name}"


def _get_open_cases(store: DataStore) -> str:
    cases = store.get("cases", default=[])
    open_cases = [c for c in cases if c.get("status") == "open"]
    today = str(date.today())
    for c in open_cases:
        deadline = c.get("response_deadline", "")
        if deadline:
            days_left = (date.fromisoformat(deadline) - date.today()).days
            c["days_until_deadline"] = days_left
            c["urgency"] = "OVERDUE" if days_left < 0 else "URGENT" if days_left <= 2 else "normal"

    return json.dumps({
        "open_cases": open_cases,
        "count": len(open_cases),
        "urgent": [c for c in open_cases if c.get("urgency") in ("OVERDUE", "URGENT")],
        "note": "Etsy cases must be responded to within 3 days or Etsy may auto-refund the buyer.",
    }, indent=2)


def _log_return_request(data: dict, store: DataStore) -> str:
    cases = store.get("cases", default=[])
    case_id = f"CASE{len(cases) + 1:04d}"
    deadline = str(date.today() + timedelta(days=3))

    case = {
        "id": case_id,
        "order_id": data["order_id"],
        "customer_name": data.get("customer_name", "Customer"),
        "reason": data["reason"],
        "item_type": data["item_type"],
        "description": data.get("description", ""),
        "amount": data["amount"],
        "status": "open",
        "opened_at": str(date.today()),
        "response_deadline": deadline,
        "resolution": None,
    }
    cases.append(case)
    store.set(cases, "cases")
    store.save()

    return json.dumps({
        "success": True,
        "case_id": case_id,
        "response_deadline": deadline,
        "urgency": "You have 3 days to respond before Etsy may auto-resolve in buyer's favour.",
        "next_step": f"Use get_recommended_response with case_id='{case_id}' for resolution guidance.",
    }, indent=2)


def _get_recommended_response(case_id: str, store: DataStore) -> str:
    cases = store.get("cases", default=[])
    case = next((c for c in cases if c["id"] == case_id), None)
    if not case:
        return json.dumps({"error": f"Case {case_id} not found"})

    reason = case.get("reason", "")
    item_type = case.get("item_type", "physical")

    resolutions = {
        "not_as_described": {
            "recommendation": "Offer full refund or replacement. Do not dispute — this is the highest-risk case for seller.",
            "action": "full_refund or replacement_sent",
            "etsy_policy": "Etsy almost always sides with buyer for 'not as described' claims.",
        },
        "item_not_received": {
            "recommendation": "Check tracking. If tracking shows delivered, ask buyer to check with neighbours/post office. If not delivered, offer full refund.",
            "action": "full_refund if undelivered",
            "etsy_policy": "File a claim with carrier if item was insured.",
        },
        "damaged": {
            "recommendation": "Apologise, offer full refund or replacement. Ask for photo of damage for insurance.",
            "action": "full_refund or replacement_sent",
        },
        "digital_file_issue": {
            "recommendation": "Resend the file immediately. If file is corrupt, fix and resend. No refund needed if file is intact.",
            "action": "resend_digital_file",
            "etsy_policy": "Digital downloads are generally non-refundable if file was delivered as described.",
        },
        "changed_mind": {
            "recommendation": "Not required to refund — buyer remorse is not covered by Etsy policy. Can offer as goodwill gesture.",
            "action": "no_refund_policy (or partial_refund as goodwill)",
            "etsy_policy": "Your shop return policy applies. If no returns policy, you are not required to refund.",
        },
        "quality_issue": {
            "recommendation": "Ask for photo. Offer partial refund (10-25%) or replacement if quality clearly defective.",
            "action": "partial_refund or replacement_sent",
        },
    }

    rec = resolutions.get(reason, resolutions["quality_issue"])
    return json.dumps({"case_id": case_id, "case": case, "recommendation": rec}, indent=2)


def _process_refund(data: dict, store: DataStore) -> str:
    cases = store.get("cases", default=[])
    case = next((c for c in cases if c["id"] == data["case_id"]), None)
    if not case:
        return json.dumps({"error": f"Case {data['case_id']} not found"})

    case["status"] = "resolved"
    case["resolution"] = data["refund_type"]
    case["refund_amount"] = data["refund_amount"]
    case["resolution_notes"] = data.get("notes", "")
    case["resolved_at"] = str(date.today())
    store.set(cases, "cases")
    store.save()

    return json.dumps({
        "success": True,
        "case_id": data["case_id"],
        "refund_amount": data["refund_amount"],
        "refund_type": data["refund_type"],
        "note": "Issue refund in Etsy Shop Manager → Orders → [Order] → Issue Refund.",
    }, indent=2)


def _get_return_analytics(store: DataStore) -> str:
    cases = store.get("cases", default=[])
    orders = store.orders
    total_orders = len(orders)
    return_rate = round(len(cases) / total_orders * 100, 2) if total_orders else 0

    by_reason: dict[str, int] = {}
    by_type: dict[str, int] = {}
    total_refunded = 0.0
    for c in cases:
        r = c.get("reason", "other")
        by_reason[r] = by_reason.get(r, 0) + 1
        t = c.get("item_type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1
        if c.get("status") == "resolved":
            total_refunded += c.get("refund_amount", 0)

    return json.dumps({
        "total_cases": len(cases),
        "open_cases": sum(1 for c in cases if c.get("status") == "open"),
        "resolved_cases": sum(1 for c in cases if c.get("status") == "resolved"),
        "return_rate_pct": return_rate,
        "total_refunded_usd": round(total_refunded, 2),
        "by_reason": by_reason,
        "by_item_type": by_type,
        "benchmark": "Industry average return rate: 2-5%. Digital: under 1%.",
    }, indent=2)


def _draft_case_response(data: dict) -> str:
    situation = data["situation"]
    position = data["our_position"]

    templates = {
        ("item_not_received", "offer_full_refund"): """Hi [Customer Name],

I'm so sorry to hear your order hasn't arrived! I completely understand how frustrating this must be.

I've reviewed your order and I'd like to make this right for you immediately. I'm issuing a full refund of [AMOUNT] which should appear within 3-5 business days.

I take all delays very seriously and appreciate your patience. If your item does arrive after the refund is processed, please feel free to keep it as my apology for the inconvenience.

Thank you for being understanding. Please don't hesitate to reach out if there's anything else I can help with!

Warm regards, [Shop Name]""",

        ("not_as_described", "offer_full_refund"): """Hi [Customer Name],

Thank you for reaching out and I sincerely apologise that the item didn't meet your expectations.

I want every customer to love what they receive, and I'd like to make this right. I'm issuing a full refund of [AMOUNT].

Your feedback is valuable and helps me improve. Could you share a photo of the item? This helps me identify any quality issues going forward.

Thank you for your honesty, and I'm sorry again for the disappointment.

Warm regards, [Shop Name]""",

        ("digital_issue", "resend_digital_file"): """Hi [Customer Name],

I'm sorry you're having trouble with your download! Let me fix this right away.

I'm resending your file directly to [EMAIL]. Please check your spam folder if you don't see it within a few minutes.

If you're still having trouble, please reply with your preferred email address and I'll send it again immediately.

Thank you for your patience!

Warm regards, [Shop Name]""",

        ("buyer_remorse", "no_refund_policy"): """Hi [Customer Name],

Thank you for reaching out. I completely understand that sometimes a purchase doesn't work out as expected.

Per our shop policy, we don't offer refunds for change-of-mind purchases on digital downloads since they are immediately accessible files. However, because I want you to have a great experience, I'd be happy to offer you a 15% discount on your next order with code THANKYOU15.

I hope you find a use for your download, and please reach out if there's anything I can help clarify about the files.

Warm regards, [Shop Name]""",
    }

    key = (situation, position)
    template = templates.get(key, templates.get((situation, "offer_full_refund"),
        "Hi [Customer Name],\n\nThank you for reaching out. I'd like to resolve this for you as quickly as possible. [Describe resolution]. Please let me know if you have any questions.\n\nWarm regards, [Shop Name]"))

    return json.dumps({
        "situation": situation,
        "our_position": position,
        "draft_response": template,
        "where_to_send": "Etsy Shop Manager → Orders → [Order] → Message buyer",
        "tip": "Respond within 24 hours. Etsy monitors response times and it affects your Star Seller status.",
    }, indent=2)
