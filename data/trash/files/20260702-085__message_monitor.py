#!/usr/bin/env python3
"""
message_monitor.py

Checks Etsy conversations for buyer messages that have gone unanswered
for more than a configurable threshold (default 18 hours).

Star Seller requires 95%+ response rate within 24 hours.
This monitor fires at 18 hours to give a 6-hour buffer.

Usage:
  python tools/message_monitor.py              # check + email alert if needed
  python tools/message_monitor.py --status     # print status, no email
  python tools/message_monitor.py --hours 12   # custom threshold
"""

from __future__ import annotations
import argparse, json, os, smtplib, sys, time
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

STATE_FILE = BASE / "data" / "message_monitor_state.json"
ALERT_EMAIL = "Printing3dthings@outlook.com"
DEFAULT_HOURS = 18


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"alerted_thread_ids": [], "last_check": None}


def _save_state(state: dict) -> None:
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _send_alert(urgent: list[dict]) -> None:
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    if not smtp_user or not smtp_pass:
        print("  [alert] SMTP credentials not set — printing alert only")
        return

    body_lines = [
        f"OnBrandCraftz — {len(urgent)} message(s) need a reply before the 24-hour Star Seller window closes.\n",
    ]
    for m in urgent:
        hrs = m["hours_waiting"]
        remaining = 24 - hrs
        body_lines.append(
            f"  Thread {m['thread_id']}\n"
            f"    From: {m['buyer_name']}\n"
            f"    Waiting: {hrs:.1f} hours ({remaining:.1f} hours left)\n"
            f"    Last message: {m['last_message'][:120]}\n"
            f"    Reply at: https://www.etsy.com/messages/conversations/{m['thread_id']}\n"
        )
    body_lines.append("\nReply within 24 hours to maintain Star Seller status.")

    msg = EmailMessage()
    msg["Subject"] = f"[OnBrandCraftz] {len(urgent)} message(s) need reply — Star Seller window"
    msg["From"] = smtp_user
    msg["To"] = ALERT_EMAIL
    msg.set_content("\n".join(body_lines))

    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"  [alert] Email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"  [alert] Email failed: {e}")
        print("  --- ALERT BODY ---")
        print("\n".join(body_lines))


def check_messages(client: EtsyAPIClient, threshold_hours: float = DEFAULT_HOURS,
                   status_only: bool = False) -> list[dict]:
    """
    Fetch all conversations, find unanswered buyer messages older than threshold.
    Returns list of dicts with thread info for any that need replies.
    """
    now = datetime.now(timezone.utc)
    threshold_secs = threshold_hours * 3600

    try:
        resp = client._request("GET", f"shops/{client.shop_id}/conversations",
                               params={"limit": 100})
    except Exception as e:
        print(f"  [monitor] Could not fetch conversations: {e}")
        return []

    conversations = resp.get("results", []) if isinstance(resp, dict) else resp
    urgent = []

    for conv in conversations:
        thread_id = conv.get("thread_id") or conv.get("id")
        messages_raw = conv.get("messages", [])
        if not messages_raw:
            continue

        # Sort by create_timestamp descending to find the latest message
        messages_raw.sort(key=lambda m: m.get("create_timestamp", 0), reverse=True)
        latest = messages_raw[0]

        # Skip if the latest message is FROM the seller (already replied)
        if latest.get("is_seller"):
            continue

        ts = latest.get("create_timestamp", 0)
        age_secs = now.timestamp() - ts
        if age_secs < threshold_secs:
            continue

        hours_waiting = age_secs / 3600
        urgent.append({
            "thread_id": thread_id,
            "buyer_name": conv.get("buyer_name", "Unknown"),
            "hours_waiting": round(hours_waiting, 1),
            "last_message": (latest.get("message", "") or "")[:200],
            "listing_title": conv.get("listing_title", ""),
            "url": f"https://www.etsy.com/messages/conversations/{thread_id}",
        })

    return urgent


def print_report(urgent: list[dict], all_conversations: int = 0) -> None:
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    print(f"\n=== OnBrandCraftz Message Monitor — {now_str} ===")
    if not urgent:
        print("  All conversations have been replied to. Star Seller status: SAFE")
    else:
        print(f"  {len(urgent)} conversation(s) need a reply:\n")
        for m in urgent:
            remaining = 24 - m["hours_waiting"]
            status = "URGENT" if remaining < 4 else "WARNING"
            print(f"  [{status}] Thread {m['thread_id']} — {m['buyer_name']}")
            print(f"    Waiting: {m['hours_waiting']}h | {remaining:.1f}h left before 24h window")
            print(f"    Message: {m['last_message'][:100]}")
            print(f"    URL: {m['url']}")
            print()
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--hours", type=float, default=DEFAULT_HOURS,
                        help=f"Alert threshold in hours (default {DEFAULT_HOURS})")
    parser.add_argument("--status", action="store_true",
                        help="Print status without sending email alerts")
    args = parser.parse_args()

    # Load env
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

    client = EtsyAPIClient()
    if not client.refresh_access_token():
        print("[message-monitor] ERROR: Could not refresh OAuth token — aborting")
        sys.exit(1)

    state = _load_state()
    urgent = check_messages(client, threshold_hours=args.hours, status_only=args.status)
    print_report(urgent)

    if not args.status and urgent:
        # Only alert on threads we haven't already alerted about
        new_urgent = [m for m in urgent
                      if str(m["thread_id"]) not in state["alerted_thread_ids"]]
        if new_urgent:
            _send_alert(new_urgent)
            state["alerted_thread_ids"].extend(
                str(m["thread_id"]) for m in new_urgent
            )
        else:
            print("  [alert] Already alerted on all urgent threads — no new email sent")

    # Clean up alerted IDs for threads that have been replied to
    still_urgent_ids = {str(m["thread_id"]) for m in urgent}
    state["alerted_thread_ids"] = [
        tid for tid in state["alerted_thread_ids"] if tid in still_urgent_ids
    ]
    _save_state(state)


if __name__ == "__main__":
    main()
