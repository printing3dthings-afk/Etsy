import sys
import os
import json
import queue
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from tools.data_store import DataStore

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

AGENT_INFO = {
    "ceo":      {"label": "CEO",            "desc": "Orchestrates all agents — ask anything about your shop", "icon": "👑"},
    "sales":    {"label": "Sales",          "desc": "Orders, revenue, shipping queue",                        "icon": "💰"},
    "product":  {"label": "Product",        "desc": "Listings, inventory, pricing",                           "icon": "📦"},
    "marketing":{"label": "Marketing",      "desc": "SEO, competitor pricing, promotions",                    "icon": "📣"},
    "analytics":{"label": "Analytics",      "desc": "Dashboard, traffic reports, trends",                     "icon": "📊"},
    "cs":       {"label": "Customer Service","desc": "Messages, reviews, satisfaction",                       "icon": "💬"},
    "social":   {"label": "Social Media",   "desc": "Pinterest strategy, pin scheduling, content calendar",   "icon": "📌"},
}

_agent_cache: dict = {}
_stream_queues: dict = {}


def _get_agent(name: str):
    if name not in _agent_cache:
        from agents import (CEOAgent, SalesAgent, ProductAgent, MarketingAgent,
                            AnalyticsAgent, CustomerServiceAgent, SocialMediaAgent)
        factory = {
            "ceo": CEOAgent, "sales": SalesAgent, "product": ProductAgent,
            "marketing": MarketingAgent, "analytics": AnalyticsAgent,
            "cs": CustomerServiceAgent, "social": SocialMediaAgent,
        }.get(name)
        if factory:
            _agent_cache[name] = factory()
    return _agent_cache.get(name)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", agents=AGENT_INFO)


@app.route("/api/agents")
def api_agents():
    return jsonify(AGENT_INFO)


@app.route("/api/dashboard")
def api_dashboard():
    try:
        store = DataStore()
        pending_orders = [o for o in store.orders if o["status"] == "payment_complete"]
        unread_msgs    = [m for m in store.messages if m["status"] == "unread"]
        unread_reviews = [r for r in store.reviews if not r.get("responded")]
        sold_out       = [l for l in store.listings if l["quantity"] == 0]
        return jsonify({
            "shop_name":        store.shop.get("name", "OnBrandCraftz"),
            "total_listings":   len(store.listings),
            "active_listings":  len([l for l in store.listings if l["status"] == "active"]),
            "sold_out":         len(sold_out),
            "pending_orders":   len(pending_orders),
            "unread_messages":  len(unread_msgs),
            "unread_reviews":   len(unread_reviews),
            "revenue_today":    store.analytics.get("revenue", {}).get("today", 0),
            "revenue_week":     store.analytics.get("revenue", {}).get("this_week", 0),
            "rating":           store.shop.get("rating", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data       = request.get_json(force=True)
    agent_name = data.get("agent", "ceo")
    message    = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    agent = _get_agent(agent_name)
    if not agent:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 404

    session_id = data.get("session_id", "default")
    q = queue.Queue()
    _stream_queues[session_id] = q

    def run():
        try:
            # Patch print so CEO delegation notices show in stream
            original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
            import builtins
            def patched_print(*args, **kwargs):
                msg = " ".join(str(a) for a in args)
                if "[CEO]" in msg:
                    q.put({"type": "status", "text": msg.strip()})
            builtins.print = patched_print
            try:
                result = agent.run(message)
            finally:
                builtins.print = original_print
            q.put({"type": "done", "text": result})
        except Exception as exc:
            q.put({"type": "error", "text": str(exc)})

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return jsonify({"session_id": session_id, "status": "running"})


@app.route("/api/stream/<session_id>")
def api_stream(session_id):
    def generate():
        q = _stream_queues.get(session_id)
        if not q:
            yield f"data: {json.dumps({'type': 'error', 'text': 'No session found'})}\n\n"
            return
        while True:
            try:
                msg = q.get(timeout=120)
                yield f"data: {json.dumps(msg)}\n\n"
                if msg["type"] in ("done", "error"):
                    _stream_queues.pop(session_id, None)
                    break
            except queue.Empty:
                yield f"data: {json.dumps({'type': 'error', 'text': 'Timeout'})}\n\n"
                break

    return Response(stream_with_context(generate()),
                    mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.route("/api/briefing", methods=["POST"])
def api_briefing():
    data = request.get_json(force=True)
    session_id = data.get("session_id", "briefing")
    q = queue.Queue()
    _stream_queues[session_id] = q

    BRIEFING_PROMPT = """Run a complete daily briefing. Delegate to all agents and cover:
1. Revenue and pending orders (Sales Agent)
2. Inventory alerts (Product Agent)
3. Unread messages and unresponded reviews (Customer Service Agent)
4. Traffic and top listings (Analytics Agent)
5. One key marketing or Pinterest opportunity (Marketing or Social Media Agent)
Synthesize into a concise executive briefing. Lead with the most urgent items."""

    def run():
        try:
            import builtins
            original = builtins.print
            def patched(*args, **kwargs):
                msg = " ".join(str(a) for a in args)
                if "[CEO]" in msg:
                    q.put({"type": "status", "text": msg.strip()})
            builtins.print = patched
            try:
                agent = _get_agent("ceo")
                result = agent.run(BRIEFING_PROMPT)
            finally:
                builtins.print = original
            q.put({"type": "done", "text": result})
        except Exception as exc:
            q.put({"type": "error", "text": str(exc)})

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"session_id": session_id, "status": "running"})


if __name__ == "__main__":
    print("\n  OnBrandCraftz Agent Hub")
    print("  Open http://localhost:5000 in your browser\n")
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
