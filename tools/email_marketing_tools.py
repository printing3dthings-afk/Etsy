"""
Email Marketing Tools — customer retention and communication via Etsy-permitted channels.

Etsy's rules on email marketing:
  - You CANNOT email buyers directly for marketing (Etsy owns the buyer relationship)
  - You CAN use Etsy's built-in "Message to Buyers" (appears on order receipts)
  - You CAN include package inserts with a QR code linking to a mailing list
  - You CAN send one follow-up message per order through Etsy messaging
  - You CAN use Etsy's auto "Thank You" coupon feature

For off-platform email (newsletter), buyers must have opted in voluntarily.
This module manages: receipt messages, message templates, newsletter content,
and subscriber list (for buyers who opt in via package inserts or website).
"""

import json
import os
import smtplib
from datetime import date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_receipt_message",
        "description": "Get the current Etsy order receipt message shown to all buyers after purchase.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "set_receipt_message",
        "description": "Draft an Etsy order receipt message. This appears on every buyer's receipt email.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Receipt message text (max 500 chars). Can include care instructions, social links, coupon code.",
                }
            },
            "required": ["message"],
        },
    },
    {
        "name": "create_message_template",
        "description": "Create a reusable message template for common buyer communications.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Template name, e.g. 'Shipping Confirmation'"},
                "trigger": {
                    "type": "string",
                    "enum": ["order_placed", "shipped", "delivered", "custom_request", "review_followup", "general"],
                },
                "subject": {"type": "string"},
                "body": {"type": "string"},
            },
            "required": ["name", "trigger", "body"],
        },
    },
    {
        "name": "get_message_templates",
        "description": "List all saved message templates.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "add_subscriber",
        "description": "Add a customer to the newsletter subscriber list (must have opted in).",
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "name": {"type": "string"},
                "source": {
                    "type": "string",
                    "enum": ["package_insert", "website_signup", "etsy_message", "social_media"],
                    "description": "How they subscribed — for compliance records",
                },
            },
            "required": ["email", "source"],
        },
    },
    {
        "name": "get_subscriber_list",
        "description": "Get the newsletter subscriber list with opt-in source.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "draft_newsletter",
        "description": "Draft a newsletter for subscribers: new products, promotions, tips.",
        "input_schema": {
            "type": "object",
            "properties": {
                "subject": {"type": "string"},
                "headline": {"type": "string"},
                "body": {"type": "string", "description": "Main newsletter content"},
                "cta_text": {"type": "string", "description": "Call-to-action button text, e.g. 'Shop Now'"},
                "cta_url": {"type": "string", "description": "Link for the CTA button"},
                "promo_code": {"type": "string", "description": "Optional discount code to include"},
            },
            "required": ["subject", "headline", "body"],
        },
    },
    {
        "name": "send_newsletter",
        "description": "Send a drafted newsletter to all subscribers via SMTP. Requires SMTP settings in .env.",
        "input_schema": {
            "type": "object",
            "properties": {
                "draft_id": {"type": "string"},
                "confirm": {"type": "boolean", "description": "Must be true to confirm sending"},
            },
            "required": ["draft_id", "confirm"],
        },
    },
    {
        "name": "get_email_stats",
        "description": "Get newsletter and receipt message statistics.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "create_package_insert_copy",
        "description": "Generate copy for a physical package insert card (to collect email subscribers and encourage reviews).",
        "input_schema": {
            "type": "object",
            "properties": {
                "include_coupon": {"type": "boolean", "default": True},
                "coupon_code": {"type": "string"},
                "include_review_ask": {"type": "boolean", "default": True},
                "include_social": {"type": "boolean", "default": True},
            },
            "required": [],
        },
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_receipt_message":
        return _get_receipt_message(store)
    if tool_name == "set_receipt_message":
        return _set_receipt_message(tool_input["message"], store)
    if tool_name == "create_message_template":
        return _create_message_template(tool_input, store)
    if tool_name == "get_message_templates":
        return _get_message_templates(store)
    if tool_name == "add_subscriber":
        return _add_subscriber(tool_input, store)
    if tool_name == "get_subscriber_list":
        return _get_subscriber_list(store)
    if tool_name == "draft_newsletter":
        return _draft_newsletter(tool_input, store)
    if tool_name == "send_newsletter":
        return _send_newsletter(tool_input, store)
    if tool_name == "get_email_stats":
        return _get_email_stats(store)
    if tool_name == "create_package_insert_copy":
        return _create_package_insert_copy(tool_input, store)
    return f"Unknown email marketing tool: {tool_name}"


def _get_receipt_message(store: DataStore) -> str:
    msg = store.get("receipt_message", default="")
    return json.dumps({
        "current_receipt_message": msg or "(No receipt message set)",
        "char_count": len(msg),
        "max_chars": 500,
        "where_to_set": "Etsy Shop Manager → Settings → Info & Appearance → Receipt Message",
        "tip": "Include: thank-you note, care instructions, coupon code, Pinterest/social handle.",
    }, indent=2)


def _set_receipt_message(message: str, store: DataStore) -> str:
    if len(message) > 500:
        return json.dumps({"error": f"Message too long ({len(message)} chars). Max 500 characters."})
    store.set(message, "receipt_message")
    store.save()
    return json.dumps({
        "success": True,
        "message": message,
        "char_count": len(message),
        "action_required": "Paste this into Etsy Shop Manager → Settings → Info & Appearance → Message to Buyers.",
    }, indent=2)


def _create_message_template(data: dict, store: DataStore) -> str:
    templates = store.get("message_templates", default=[])
    tmpl_id = f"TMPL{len(templates) + 1:03d}"
    template = {
        "id": tmpl_id,
        "name": data["name"],
        "trigger": data["trigger"],
        "subject": data.get("subject", ""),
        "body": data["body"],
        "created_at": str(date.today()),
    }
    templates.append(template)
    store.set(templates, "message_templates")
    store.save()
    return json.dumps({"success": True, "template_id": tmpl_id, "template": template}, indent=2)


def _get_message_templates(store: DataStore) -> str:
    templates = store.get("message_templates", default=[])
    return json.dumps({"templates": templates, "count": len(templates)}, indent=2)


def _add_subscriber(data: dict, store: DataStore) -> str:
    subscribers = store.get("email_subscribers", default=[])
    existing = next((s for s in subscribers if s["email"].lower() == data["email"].lower()), None)
    if existing:
        return json.dumps({"warning": f"{data['email']} is already subscribed.", "subscriber": existing})
    subscriber = {
        "email": data["email"].lower(),
        "name": data.get("name", ""),
        "source": data["source"],
        "subscribed_at": str(date.today()),
        "active": True,
    }
    subscribers.append(subscriber)
    store.set(subscribers, "email_subscribers")
    store.save()
    return json.dumps({"success": True, "subscriber": subscriber,
                       "total_subscribers": len(subscribers)}, indent=2)


def _get_subscriber_list(store: DataStore) -> str:
    subscribers = store.get("email_subscribers", default=[])
    active = [s for s in subscribers if s.get("active", True)]
    by_source: dict[str, int] = {}
    for s in active:
        src = s.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    return json.dumps({
        "total_subscribers": len(active),
        "subscribers": active,
        "by_source": by_source,
        "compliance_note": "Only email subscribers who explicitly opted in. Keep opt-in records.",
    }, indent=2)


def _draft_newsletter(data: dict, store: DataStore) -> str:
    drafts = store.get("newsletter_drafts", default=[])
    draft_id = f"NL{len(drafts) + 1:03d}"
    shop_name = store.shop.get("name", "OnBrandCraftz")
    shop_url = store.shop.get("url", "")

    html_body = f"""<html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #333;">
<h1 style="color: #6B7280;">{data['headline']}</h1>
<div style="font-size: 15px; line-height: 1.6;">
{data['body'].replace(chr(10), '<br>')}
</div>"""
    if data.get("promo_code"):
        html_body += f"""
<div style="background: #f3f4f6; border-left: 4px solid #6B7280; padding: 12px 16px; margin: 20px 0;">
  <strong>Your exclusive code:</strong> <span style="font-size: 18px; color: #6B7280;">{data['promo_code']}</span>
</div>"""
    if data.get("cta_text") and data.get("cta_url"):
        html_body += f"""
<div style="text-align: center; margin: 24px 0;">
  <a href="{data['cta_url']}" style="background: #6B7280; color: white; padding: 12px 28px;
     text-decoration: none; border-radius: 4px; font-weight: bold;">{data['cta_text']}</a>
</div>"""
    html_body += f"""
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
<p style="color: #9ca3af; font-size: 12px; text-align: center;">
  {shop_name} | <a href="{shop_url}">{shop_url}</a><br>
  You received this because you subscribed to our updates.
  <a href="#">Unsubscribe</a>
</p>
</body></html>"""

    draft = {
        "id": draft_id,
        "subject": data["subject"],
        "headline": data["headline"],
        "html_body": html_body,
        "promo_code": data.get("promo_code", ""),
        "status": "draft",
        "created_at": str(date.today()),
    }
    drafts.append(draft)
    store.set(drafts, "newsletter_drafts")
    store.save()
    return json.dumps({
        "success": True,
        "draft_id": draft_id,
        "subject": data["subject"],
        "preview": html_body[:300] + "...",
        "next_step": f"Use send_newsletter with draft_id='{draft_id}' and confirm=true to send.",
    }, indent=2)


def _send_newsletter(data: dict, store: DataStore) -> str:
    if not data.get("confirm"):
        return json.dumps({"error": "Set confirm=true to send the newsletter."})

    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    sender_name = os.getenv("SENDER_NAME", "OnBrandCraftz")

    if not smtp_user or not smtp_password:
        return json.dumps({"error": "SMTP_USER and SMTP_PASSWORD must be set in .env to send newsletters."})

    drafts = store.get("newsletter_drafts", default=[])
    draft = next((d for d in drafts if d["id"] == data["draft_id"]), None)
    if not draft:
        return json.dumps({"error": f"Draft {data['draft_id']} not found."})

    subscribers = [s for s in store.get("email_subscribers", default=[]) if s.get("active", True)]
    if not subscribers:
        return json.dumps({"warning": "No subscribers to send to. Add subscribers first."})

    sent = 0
    failed = 0
    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.login(smtp_user, smtp_password)
            for sub in subscribers:
                try:
                    msg = MIMEMultipart("alternative")
                    msg["From"] = f"{sender_name} <{smtp_user}>"
                    msg["To"] = sub["email"]
                    msg["Subject"] = draft["subject"]
                    msg.attach(MIMEText(draft["html_body"], "html"))
                    server.send_message(msg)
                    sent += 1
                except Exception as _e:
                    failed += 1
                    print(f"  Failed to send to {sub.get('email', '?')}: {_e}")
    except Exception as exc:
        return json.dumps({"error": f"SMTP connection failed: {exc}"})

    draft["status"] = "sent"
    draft["sent_at"] = str(date.today())
    draft["sent_count"] = sent
    draft["failed_count"] = failed
    store.set(drafts, "newsletter_drafts")
    store.save()

    return json.dumps({
        "success": True,
        "draft_id": data["draft_id"],
        "sent_to": sent,
        "failed": failed,
        "subject": draft["subject"],
    }, indent=2)


def _get_email_stats(store: DataStore) -> str:
    subscribers = store.get("email_subscribers", default=[])
    drafts = store.get("newsletter_drafts", default=[])
    sent_newsletters = [d for d in drafts if d.get("status") == "sent"]
    total_sent = sum(d.get("sent_count", 0) for d in sent_newsletters)
    return json.dumps({
        "subscribers": {
            "total_active": sum(1 for s in subscribers if s.get("active", True)),
            "total_all_time": len(subscribers),
        },
        "newsletters": {
            "total_drafted": len(drafts),
            "total_sent": len(sent_newsletters),
            "total_emails_delivered": total_sent,
        },
        "receipt_message": {
            "set": bool(store.get("receipt_message", default="")),
            "char_count": len(store.get("receipt_message", default="")),
        },
        "templates": len(store.get("message_templates", default=[])),
    }, indent=2)


def _create_package_insert_copy(data: dict, store: DataStore) -> str:
    shop_name = store.shop.get("name", "OnBrandCraftz")
    shop_url = store.shop.get("url", "https://www.etsy.com/shop/onbrandcraftz")
    coupon = data.get("coupon_code", "THANKYOU10")
    include_coupon = data.get("include_coupon", True)
    include_review = data.get("include_review_ask", True)
    include_social = data.get("include_social", True)

    front = f"""✨ Thank you for your order! ✨
We handcraft every item with love in Indiana.
Visit us again: {shop_url}"""

    back_lines = [f"— {shop_name} —", ""]
    if include_coupon:
        back_lines += [
            f"🎁 THANK YOU GIFT",
            f"Use code {coupon} for 10% off your next order.",
            "",
        ]
    if include_review:
        back_lines += [
            "⭐ LOVE YOUR ORDER?",
            "We'd be so grateful for a review on Etsy!",
            "It takes 30 seconds and means the world to a small shop.",
            "",
        ]
    if include_social:
        back_lines += [
            "📌 Follow us on Pinterest for decor inspiration:",
            "pinterest.com/printing3dthings",
            "",
        ]
    back_lines.append("Questions? Message us on Etsy — we reply within 24 hours!")
    back = "\n".join(back_lines)

    return json.dumps({
        "insert_front": front,
        "insert_back": back,
        "printing_tip": "Print on 4x6 inch card stock, cut in half for two inserts per sheet.",
        "compliance_note": "Do NOT offer the coupon in exchange for a review — it's a separate thank-you gift.",
        "qr_code_tip": "Add a QR code linking to your Etsy shop or a Mailchimp signup page.",
    }, indent=2)
