import json
from datetime import date
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {"name": "get_messages", "description": "Retrieve customer messages filtered by status.",
     "input_schema": {"type": "object", "properties": {"status": {"type": "string", "enum": ["all", "unread", "replied"]}}, "required": ["status"]}},
    {"name": "get_message_details", "description": "Get full details of a specific customer message.",
     "input_schema": {"type": "object", "properties": {"message_id": {"type": "string"}}, "required": ["message_id"]}},
    {"name": "draft_reply", "description": "Draft and send a reply to a customer message.",
     "input_schema": {"type": "object", "properties": {"message_id": {"type": "string"}, "reply_text": {"type": "string"}}, "required": ["message_id", "reply_text"]}},
    {"name": "get_reviews", "description": "Retrieve customer reviews.",
     "input_schema": {"type": "object", "properties": {"filter": {"type": "string", "enum": ["all", "unresponded", "responded"]}}, "required": ["filter"]}},
    {"name": "respond_to_review", "description": "Post a public response to a customer review.",
     "input_schema": {"type": "object", "properties": {"review_id": {"type": "string"}, "response_text": {"type": "string"}}, "required": ["review_id", "response_text"]}},
    {"name": "get_customer_satisfaction", "description": "Get overview of customer satisfaction.",
     "input_schema": {"type": "object", "properties": {}, "required": []}},
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_messages":            return _get_messages(tool_input["status"], store)
    if tool_name == "get_message_details":     return _get_message_details(tool_input["message_id"], store)
    if tool_name == "draft_reply":             return _draft_reply(tool_input["message_id"], tool_input["reply_text"], store)
    if tool_name == "get_reviews":             return _get_reviews(tool_input["filter"], store)
    if tool_name == "respond_to_review":       return _respond_to_review(tool_input["review_id"], tool_input["response_text"], store)
    if tool_name == "get_customer_satisfaction":return _get_customer_satisfaction(store)
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
    return json.dumps({"success": True, "message_id": message_id,
                       "sent_to": msg.get("buyer_name"), "reply": reply_text, "sent_at": str(date.today())}, indent=2)


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
    return json.dumps({"success": True, "review_id": review_id,
                       "reviewer": review.get("buyer_name"), "rating": review.get("rating"), "response": response_text}, indent=2)


def _get_customer_satisfaction(store: DataStore) -> str:
    reviews = store.reviews
    if not reviews:
        return json.dumps({"message": "No reviews yet."})
    ratings = [r["rating"] for r in reviews]
    avg = sum(ratings) / len(ratings)
    distribution = {str(i): ratings.count(i) for i in range(1, 6)}
    responded = sum(1 for r in reviews if r.get("responded"))
    return json.dumps({
        "average_rating": round(avg, 2), "total_reviews": len(reviews),
        "rating_distribution": distribution, "response_rate": f"{responded / len(reviews) * 100:.0f}%",
        "responded_count": responded, "unresponded_count": len(reviews) - responded,
        "unread_messages": sum(1 for m in store.messages if m["status"] == "unread"),
    }, indent=2)
