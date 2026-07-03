"""
Daily shop brief generator for OnBrandCraftz.

Collects key shop signals from Etsy + knowledge base, calls Claude to synthesize
a short plain-text brief, and emails it to the shop owner.

Standalone:  python tools/daily_brief.py
Via server:  POST /api/brief/run  (X-App-Token header required)
Scheduled:   _daily_brief_loop() background task in main.py fires at 6 AM UTC.
"""

import datetime
import os
import smtplib
import sys
from email.mime.text import MIMEText
from pathlib import Path

# Ensure repo root is on sys.path so `tools.*` imports work when run standalone
_REPO_ROOT = Path(__file__).parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import anthropic

# ── paths ────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent
_OPS_RUNBOOK = _ROOT / "data" / "knowledge_base" / "ops_runbook.md"
_CEO_LEARNINGS = _ROOT / "data" / "knowledge_base" / "ceo_learnings.md"

_OWNER_EMAIL = "printing3dthings@outlook.com"
_BUSINESS_NAME = os.getenv("BUSINESS_NAME", "OnBrandCraftz")
_OWNER_NAME = os.getenv("OWNER_NAME", "Scott")


# ── data collection ──────────────────────────────────────────────────────────

def _get_etsy_signals() -> dict:
    """Pull live shop metrics. Returns safe defaults on any failure."""
    result = {
        "unread_messages": 0,
        "oldest_unread_hours": 0,
        "active_listings": 0,
        "draft_listings": 0,
        "recent_orders": 0,
        "etsy_error": None,
    }
    try:
        from tools.etsy_api import EtsyAPIClient
        client = EtsyAPIClient()

        # Unread message count + age of oldest unread (Star Seller risk)
        try:
            convos = client.get_messages(limit=25).get("results", [])
            now_ts = datetime.datetime.utcnow().timestamp()
            unread = [c for c in convos if not c.get("last_read_timestamp") or
                      c.get("last_read_timestamp", 0) < c.get("last_message_timestamp", 0)]
            result["unread_messages"] = len(unread)
            if unread:
                oldest_ts = min(c.get("create_timestamp", now_ts) for c in unread)
                result["oldest_unread_hours"] = int((now_ts - oldest_ts) / 3600)
        except Exception as exc:
            # 404/403 = messaging_r scope not granted — expected, skip silently
            msg = str(exc)
            if "404" not in msg and "403" not in msg:
                result["etsy_error"] = f"messages: {exc}"

        # Active + draft listing counts
        try:
            active = client.get_shop_listings(limit=100, state="active")
            result["active_listings"] = active.get("count", len(active.get("results", [])))
        except Exception:
            pass
        try:
            drafts = client.get_shop_listings(limit=25, state="draft")
            result["draft_listings"] = drafts.get("count", len(drafts.get("results", [])))
        except Exception:
            pass

        # Recent orders (last 7 days — use was_paid receipts)
        try:
            cutoff = int((datetime.datetime.utcnow() - datetime.timedelta(days=7)).timestamp())
            orders = client.get_orders(limit=25).get("results", [])
            result["recent_orders"] = sum(
                1 for o in orders if o.get("create_timestamp", 0) >= cutoff
            )
        except Exception:
            pass

    except Exception as exc:
        result["etsy_error"] = str(exc)

    return result


def _get_kb_context() -> str:
    """Read recent entries from ops_runbook and ceo_learnings. Graceful on missing files."""
    parts = []
    for path, label, tail_lines in [
        (_OPS_RUNBOOK, "Recent incidents (ops_runbook)", 15),
        (_CEO_LEARNINGS, "Recent learnings (ceo_learnings)", 10),
    ]:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
            tail = "\n".join(lines[-tail_lines:]).strip()
            if tail:
                parts.append(f"=== {label} ===\n{tail}")
        except OSError:
            pass
    return "\n\n".join(parts)


# ── brief generation ──────────────────────────────────────────────────────────

def _get_due_todos(within_days: int = 14) -> list:
    """Open to-dos with a due_date within `within_days` (or already overdue),
    soonest first. Returns [(days_left, text, due_str), ...]; [] on any failure so
    the brief still sends if the DB is unavailable."""
    try:
        from tools.api_server import db
        today = datetime.date.today()
        out = []
        for t in db.list_todos(include_done=False):
            due = t.get("due_date")
            if not due:
                continue
            try:
                d = datetime.date.fromisoformat(str(due)[:10])
            except ValueError:
                continue
            days = (d - today).days
            if days <= within_days:
                out.append((days, (t.get("text") or "").strip(), str(due)[:10]))
        out.sort(key=lambda x: x[0])
        return out
    except Exception:
        return []


def _format_deadlines(due_todos: list) -> str:
    """Render the approaching-deadline to-dos as a plain-text block (empty if none)."""
    if not due_todos:
        return ""
    lines = ["", "⏰ DEADLINES APPROACHING:"]
    for days, text, _due in due_todos:
        if days < 0:
            tag = f"OVERDUE {-days}d"
        elif days == 0:
            tag = "DUE TODAY"
        else:
            tag = f"{days}d left"
        lines.append(f"  • [{tag}] {text}")
    return "\n".join(lines)


def _generate_brief(signals: dict, kb_context: str) -> str:
    """Call Claude Haiku to synthesize signals into a plain-text daily brief."""
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        return _format_brief_no_ai(signals)

    now = datetime.datetime.utcnow()
    date_str = now.strftime("%A, %B %-d %Y")
    time_str = now.strftime("%H:%M UTC")

    unread = signals["unread_messages"]
    oldest_h = signals["oldest_unread_hours"]
    star_seller_flag = ""
    if unread > 0 and oldest_h >= 20:
        star_seller_flag = f" ⚠️ OLDEST {oldest_h}h — REPLY NOW (Star Seller at risk)"
    elif unread > 0 and oldest_h >= 12:
        star_seller_flag = f" ⚠️ {oldest_h}h old — reply today"

    signals_text = (
        f"Unread messages: {unread}{star_seller_flag}\n"
        f"Active listings: {signals['active_listings']}\n"
        f"Draft listings: {signals['draft_listings']}\n"
        f"Orders last 7 days: {signals['recent_orders']}\n"
    )
    if signals.get("etsy_error"):
        signals_text += f"Etsy API note: {signals['etsy_error']}\n"
    deadlines_text = _format_deadlines(_get_due_todos())
    if deadlines_text:
        signals_text += deadlines_text + "\n"

    user_msg = (
        f"Today is {date_str} at {time_str}.\n\n"
        f"SHOP SIGNALS:\n{signals_text}\n"
        f"KNOWLEDGE BASE CONTEXT:\n{kb_context or '(no recent entries)'}\n\n"
        "Write a concise daily brief email body for the shop owner. "
        "Plain text only, no markdown, no HTML. "
        "Start with the signals block exactly as provided (preserve the ⚠️ flags and "
        "any ⏰ DEADLINES APPROACHING lines verbatim). "
        "Then add a TODAY'S FOCUS section: 1-3 sentences on the single most important "
        "thing to do today, based on the signals and any relevant KB context. "
        "Be direct and specific. End with '— Frank 🤖'."
    )

    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=(
                f"You are Frank, the AI business assistant for {_BUSINESS_NAME}, "
                f"an Etsy shop owned by {_OWNER_NAME}. "
                "You generate a short, actionable daily brief email. "
                "No fluff, no greetings, no sign-off other than '— Frank 🤖'."
            ),
            messages=[{"role": "user", "content": user_msg}],
        )
        body = msg.content[0].text.strip()
    except Exception as exc:
        body = _format_brief_no_ai(signals)
        body += f"\n\n(AI synthesis unavailable: {exc})"

    now_str = now.strftime("%A %B %-d, %Y — %H:%M UTC")
    return f"📊 {_BUSINESS_NAME} Daily Brief — {now_str}\n\n{body}"


def _format_brief_no_ai(signals: dict) -> str:
    """Fallback brief without AI synthesis."""
    now = datetime.datetime.utcnow()
    unread = signals["unread_messages"]
    oldest_h = signals["oldest_unread_hours"]
    flag = f" ⚠️ {oldest_h}h old — reply now" if (unread and oldest_h >= 12) else ""
    lines = [
        f"📊 {_BUSINESS_NAME} Daily Brief — {now.strftime('%A %B %-d, %Y — %H:%M UTC')}",
        "",
        f"MESSAGES: {unread} unread{flag}",
        f"LISTINGS: {signals['active_listings']} active | {signals['draft_listings']} drafts",
        f"ORDERS (7d): {signals['recent_orders']}",
    ]
    if signals.get("etsy_error"):
        lines.append(f"NOTE: {signals['etsy_error']}")
    deadlines_text = _format_deadlines(_get_due_todos())
    if deadlines_text:
        lines.append(deadlines_text)
    lines += ["", "— Frank 🤖"]
    return "\n".join(lines)


# ── email delivery ────────────────────────────────────────────────────────────

def _send_brief(subject: str, body: str) -> bool:
    """Send the brief via SMTP. Returns True on success, False on failure (never raises)."""
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_name = os.getenv("SENDER_NAME", _BUSINESS_NAME)
    recipient = os.getenv("BRIEF_RECIPIENT_EMAIL", _OWNER_EMAIL)

    if not smtp_user or not smtp_password:
        print("[daily_brief] SMTP not configured — skipping email send", flush=True)
        return False

    msg = MIMEText(body, "plain", "utf-8")
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = recipient
    msg["Subject"] = subject

    try:
        if smtp_port == 465:
            import ssl as _ssl
            ctx = _ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=ctx) as srv:
                srv.login(smtp_user, smtp_password)
                srv.send_message(msg)
        else:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as srv:
                srv.ehlo()
                srv.starttls()
                srv.login(smtp_user, smtp_password)
                srv.send_message(msg)
        print(f"[daily_brief] sent to {recipient}", flush=True)
        return True
    except Exception as exc:
        print(f"[daily_brief] send failed: {exc}", flush=True)
        return False


# ── orchestrator ──────────────────────────────────────────────────────────────

def run_daily_brief() -> str:
    """
    Collect signals, generate brief, email it.
    Returns a status string for logging — never raises.
    """
    try:
        signals = _get_etsy_signals()
        kb_context = _get_kb_context()
        body = _generate_brief(signals, kb_context)
        now = datetime.datetime.utcnow()
        subject = f"{_BUSINESS_NAME} Daily Brief — {now.strftime('%a %b %-d')}"
        sent = _send_brief(subject, body)
        if sent:
            return "brief sent"
        # SMTP not configured — print to stdout anyway (useful in logs)
        print(body, flush=True)
        return "brief generated (no SMTP — printed to log)"
    except Exception as exc:
        print(f"[daily_brief] unexpected error: {exc}", flush=True)
        return f"brief failed: {exc}"


if __name__ == "__main__":
    result = run_daily_brief()
    print(f"\n[result] {result}", file=sys.stderr)
