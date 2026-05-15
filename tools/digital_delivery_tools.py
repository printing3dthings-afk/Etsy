"""
Digital Delivery Tools — processes sales and emails digital files to customers.

Sends the purchased digital file as an email attachment via SMTP.

Required .env settings:
  SMTP_HOST       — e.g. smtp.gmail.com  OR  smtp.office365.com
  SMTP_PORT       — 587 (STARTTLS) or 465 (SSL)
  SMTP_USER       — your sending email address
  SMTP_PASSWORD   — app password (see provider notes below)
  SENDER_NAME     — e.g. OnBrandCraftz

Gmail setup:
  SMTP_HOST=smtp.gmail.com  SMTP_PORT=587
  Enable 2FA then create an App Password at myaccount.google.com/apppasswords

Outlook / Office 365 setup:
  SMTP_HOST=smtp.office365.com  SMTP_PORT=587
  Use your regular password, or an App Password if MFA is enabled on the account.
"""

import json
import os
import smtplib
from datetime import date
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tools.data_store import DataStore

TOOL_DEFINITIONS: list[dict] = [
    {
        "name": "get_unfulfilled_digital_orders",
        "description": (
            "Get all orders that contain digital products and have not yet been "
            "delivered via email. Returns order details needed for delivery."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "preview_delivery_email",
        "description": "Preview the email that will be sent to the customer before sending.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "product_id": {"type": "string", "description": "DP-prefixed digital product ID"},
            },
            "required": ["order_id", "product_id"],
        },
    },
    {
        "name": "send_delivery_email",
        "description": (
            "Send the digital product file to the customer via email. "
            "Attaches the product file and sends a branded confirmation email."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "customer_email": {"type": "string", "description": "Customer's email address"},
                "customer_name": {"type": "string", "description": "Customer's name for personalization"},
                "product_id": {"type": "string", "description": "DP-prefixed digital product ID"},
                "product_title": {"type": "string", "description": "Human-readable product name"},
            },
            "required": ["order_id", "customer_email", "product_id", "product_title"],
        },
    },
    {
        "name": "mark_order_delivered",
        "description": "Mark a digital order as delivered. Updates order status to 'complete'.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "delivery_id": {"type": "string", "description": "DEL-prefixed delivery record ID"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "get_delivery_history",
        "description": "Get the history of all digital file deliveries (sent, failed, pending).",
        "input_schema": {
            "type": "object",
            "properties": {
                "status_filter": {
                    "type": "string",
                    "enum": ["all", "sent", "failed", "pending"],
                    "default": "all",
                }
            },
            "required": [],
        },
    },
    {
        "name": "resend_delivery",
        "description": "Resend a digital product to a customer (e.g., if they didn't receive it).",
        "input_schema": {
            "type": "object",
            "properties": {
                "delivery_id": {"type": "string"},
                "reason": {"type": "string", "description": "Reason for resend (for logs)"},
            },
            "required": ["delivery_id"],
        },
    },
    {
        "name": "check_email_config",
        "description": "Verify that SMTP email settings are correctly configured.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


def execute_tool(tool_name: str, tool_input: dict, store: DataStore) -> str:
    if tool_name == "get_unfulfilled_digital_orders":
        return _get_unfulfilled_digital_orders(store)
    if tool_name == "preview_delivery_email":
        return _preview_delivery_email(tool_input, store)
    if tool_name == "send_delivery_email":
        return _send_delivery_email(tool_input, store)
    if tool_name == "mark_order_delivered":
        return _mark_order_delivered(tool_input, store)
    if tool_name == "get_delivery_history":
        return _get_delivery_history(tool_input.get("status_filter", "all"), store)
    if tool_name == "resend_delivery":
        return _resend_delivery(tool_input, store)
    if tool_name == "check_email_config":
        return _check_email_config()
    return f"Unknown digital delivery tool: {tool_name}"


# ── IMPLEMENTATIONS ───────────────────────────────────────────────────────────

def _get_unfulfilled_digital_orders(store: DataStore) -> str:
    orders = store.orders
    deliveries = store.get("digital_deliveries", default=[])
    delivered_order_ids = {d["order_id"] for d in deliveries if d.get("status") == "sent"}

    digital_product_ids = {
        p["id"] for p in store.get("digital_products", default=[])
    }
    digital_listing_ids = {
        l["id"] for l in store.listings if l.get("type") == "digital"
    }
    # Also map etsy_listing_id to product_id
    listing_to_product: dict[str, str] = {}
    for p in store.get("digital_products", default=[]):
        if p.get("etsy_listing_id"):
            listing_to_product[p["etsy_listing_id"]] = p["id"]

    unfulfilled = []
    for order in orders:
        if order["id"] in delivered_order_ids:
            continue
        if order.get("status") not in ("payment_complete", "shipped", "complete"):
            continue
        # Check if order contains a digital product
        items = order.get("items", [])
        for item in items:
            lid = item.get("listing_id", "")
            prod_id = listing_to_product.get(lid) or (lid if lid in digital_product_ids else None)
            if prod_id or item.get("type") == "digital":
                unfulfilled.append({
                    "order_id": order["id"],
                    "customer_name": order.get("buyer_name", "Customer"),
                    "customer_email": order.get("buyer_email", ""),
                    "product_id": prod_id or item.get("digital_product_id"),
                    "product_title": item.get("title", order.get("items", [{}])[0].get("title", "")),
                    "order_date": order.get("created_at", ""),
                    "amount_paid": order.get("total", 0),
                })
                break

    return json.dumps({
        "unfulfilled_digital_orders": unfulfilled,
        "count": len(unfulfilled),
        "note": (
            "Use send_delivery_email to deliver each order." if unfulfilled
            else "All digital orders have been delivered."
        ),
    }, indent=2)


def _preview_delivery_email(data: dict, store: DataStore) -> str:
    product = _find_product(data["product_id"], store)
    order = store.find_order(data["order_id"])

    customer_name = order.get("buyer_name", "Valued Customer") if order else "Valued Customer"
    product_title = product["title"] if product else data["product_id"]
    shop_name = store.shop.get("name", "OnBrandCraftz")
    file_path = product.get("file_path") if product else None

    subject, body = _build_email_content(customer_name, product_title, shop_name, data["order_id"])

    return json.dumps({
        "email_preview": {
            "to": order.get("buyer_email", "(customer email)") if order else "(customer email)",
            "subject": subject,
            "body_preview": body[:500] + "..." if len(body) > 500 else body,
            "attachment": os.path.basename(file_path) if file_path else "(no file)",
            "file_exists": os.path.exists(file_path) if file_path else False,
        },
        "smtp_configured": _is_smtp_configured(),
    }, indent=2)


def _send_delivery_email(data: dict, store: DataStore) -> str:
    if not _is_smtp_configured():
        return json.dumps({
            "error": "SMTP not configured.",
            "required_env_vars": ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD"],
            "setup_tip": "For Gmail: use smtp.gmail.com:587 and create an App Password at myaccount.google.com/apppasswords",
        })

    product = _find_product(data["product_id"], store)
    if not product:
        return json.dumps({"error": f"Digital product {data['product_id']} not found"})

    file_path = product.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return json.dumps({"error": f"Product file not found: {file_path}. Generate the file first."})

    # Verify file integrity hash if available
    expected_hash = product.get("file_hash")
    if expected_hash:
        import hashlib
        with open(file_path, "rb") as hf:
            actual_hash = hashlib.sha256(hf.read()).hexdigest()
        if actual_hash != expected_hash:
            return json.dumps({
                "error": "Delivery blocked: file integrity check failed. The file may be corrupted or replaced. Re-run QC.",
                "product_id": data["product_id"],
            })

    # Block delivery of concept cards
    if product.get("is_placeholder"):
        return json.dumps({
            "error": "Delivery blocked: this product is a concept placeholder, not real art. Cannot send to customer.",
            "product_id": data["product_id"],
        })

    shop_name = store.shop.get("name", "OnBrandCraftz")
    customer_name = data.get("customer_name", "Valued Customer")
    subject, body = _build_email_content(customer_name, data["product_title"], shop_name, data["order_id"])

    try:
        result = _smtp_send(
            to_email=data["customer_email"],
            subject=subject,
            body=body,
            attachment_path=file_path,
        )

        # Record delivery
        delivery_id = _record_delivery(data, product, "sent", store)

        return json.dumps({
            "success": True,
            "delivery_id": delivery_id,
            "sent_to": data["customer_email"],
            "product_id": data["product_id"],
            "order_id": data["order_id"],
            "attachment": os.path.basename(file_path),
            "sent_at": str(date.today()),
            "next_step": "Call mark_order_delivered to update the order status.",
        }, indent=2)

    except Exception as exc:
        delivery_id = _record_delivery(data, product, "failed", store, error=str(exc))
        return json.dumps({
            "error": f"Email send failed: {exc}",
            "delivery_id": delivery_id,
            "tip": "Check SMTP credentials and ensure your email allows SMTP access.",
        })


def _mark_order_delivered(data: dict, store: DataStore) -> str:
    order = store.find_order(data["order_id"])
    if not order:
        return json.dumps({"error": f"Order {data['order_id']} not found"})

    old_status = order["status"]
    order["status"] = "complete"
    order["digital_delivered_at"] = str(date.today())
    if data.get("delivery_id"):
        order["delivery_id"] = data["delivery_id"]
    store.save()

    return json.dumps({
        "success": True,
        "order_id": data["order_id"],
        "previous_status": old_status,
        "new_status": "complete",
        "delivered_at": str(date.today()),
    }, indent=2)


def _get_delivery_history(status_filter: str, store: DataStore) -> str:
    deliveries = store.get("digital_deliveries", default=[])
    if status_filter != "all":
        deliveries = [d for d in deliveries if d.get("status") == status_filter]

    by_status: dict[str, int] = {}
    for d in deliveries:
        s = d.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return json.dumps({
        "deliveries": deliveries,
        "count": len(deliveries),
        "by_status": by_status,
    }, indent=2)


def _resend_delivery(data: dict, store: DataStore) -> str:
    deliveries = store.get("digital_deliveries", default=[])
    delivery = next((d for d in deliveries if d["id"] == data["delivery_id"]), None)
    if not delivery:
        return json.dumps({"error": f"Delivery {data['delivery_id']} not found"})

    product = _find_product(delivery["product_id"], store)
    if not product:
        return json.dumps({"error": "Product not found for this delivery"})

    send_input = {
        "order_id": delivery["order_id"],
        "customer_email": delivery["customer_email"],
        "customer_name": delivery.get("customer_name", "Valued Customer"),
        "product_id": delivery["product_id"],
        "product_title": delivery.get("product_title", product["title"]),
    }
    result_json = _send_delivery_email(send_input, store)
    result = json.loads(result_json)
    if result.get("success"):
        result["resend_reason"] = data.get("reason", "Customer request")
        result["original_delivery_id"] = data["delivery_id"]
    return json.dumps(result, indent=2)


def _check_email_config() -> str:
    host = os.getenv("SMTP_HOST", "")
    port = os.getenv("SMTP_PORT", "")
    user = os.getenv("SMTP_USER", "")
    password = os.getenv("SMTP_PASSWORD", "")
    sender_name = os.getenv("SENDER_NAME", "")

    configured = bool(host and port and user and password)
    checks = [
        {"var": "SMTP_HOST", "value": host or "(not set)", "set": bool(host)},
        {"var": "SMTP_PORT", "value": port or "(not set)", "set": bool(port)},
        {"var": "SMTP_USER", "value": user or "(not set)", "set": bool(user)},
        {"var": "SMTP_PASSWORD", "value": "***" if password else "(not set)", "set": bool(password)},
        {"var": "SENDER_NAME", "value": sender_name or "(not set, optional)", "set": bool(sender_name)},
    ]

    return json.dumps({
        "smtp_configured": configured,
        "checks": checks,
        "status": "Ready to send emails" if configured else "Missing required SMTP settings",
        "provider_examples": {
            "gmail": {
                "SMTP_HOST": "smtp.gmail.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "your_email@gmail.com",
                "SMTP_PASSWORD": "<App Password — myaccount.google.com/apppasswords>",
                "note": "Enable 2FA on your Google account first, then create an App Password.",
            },
            "outlook_office365": {
                "SMTP_HOST": "smtp.office365.com",
                "SMTP_PORT": "587",
                "SMTP_USER": "your_email@outlook.com",
                "SMTP_PASSWORD": "<your password, or App Password if MFA is enabled>",
                "note": "Works with Outlook.com, Hotmail, and Microsoft 365 / Office 365 accounts.",
            },
        },
    }, indent=2)


# ── EMAIL HELPERS ─────────────────────────────────────────────────────────────

def _build_email_content(customer_name: str, product_title: str, shop_name: str, order_id: str) -> tuple[str, str]:
    subject = f"Your Digital Download from {shop_name} — {product_title}"
    body = f"""<html><body style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
<h2 style="color: #6B7280;">Thank you for your purchase! 🎉</h2>
<p>Hi {customer_name},</p>
<p>Your digital download is attached to this email. Here's what you ordered:</p>
<div style="background: #f9fafb; border-left: 4px solid #6B7280; padding: 12px 16px; margin: 16px 0;">
  <strong>{product_title}</strong><br>
  <small>Order #{order_id}</small>
</div>
<h3>How to use your file:</h3>
<ul>
  <li><strong>PDF Planners:</strong> Open with Adobe Reader, GoodNotes, Notability, or any PDF viewer. Print on letter or A4 paper.</li>
  <li><strong>PNG/JPEG Art:</strong> Take your file to a local print shop or upload to an online printing service (Walgreens, Costco, Canva Print, etc.).</li>
  <li><strong>Printing tip:</strong> For best results, print at 100% scale on the paper size specified in the listing.</li>
</ul>
<p>If you have any issues with your download or need a resend, simply reply to this email and we'll help right away!</p>
<p>We'd love to see your prints — tag us and leave us a review on Etsy!</p>
<hr style="border: none; border-top: 1px solid #e5e7eb; margin: 24px 0;">
<p style="color: #9ca3af; font-size: 12px;">
  {shop_name} &bull; This is an automatic delivery email.<br>
  Questions? Reply directly to this email.
</p>
</body></html>"""
    return subject, body


def _smtp_send(to_email: str, subject: str, body: str, attachment_path: str) -> dict:
    smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    sender_name = os.getenv("SENDER_NAME", "OnBrandCraftz")

    # Verify file integrity before sending
    if attachment_path and os.path.exists(attachment_path):
        if os.path.getsize(attachment_path) == 0:
            raise RuntimeError(f"Delivery blocked: file is empty (0 bytes): {attachment_path}")

    msg = MIMEMultipart()
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html"))

    if attachment_path and os.path.exists(attachment_path):
        with open(attachment_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
        encoders.encode_base64(part)
        filename = os.path.basename(attachment_path)
        part.add_header("Content-Disposition", f'attachment; filename="{filename}"')
        msg.attach(part)

    try:
        if smtp_port == 465:
            # SSL from the start (e.g. some custom SMTP servers)
            import ssl as _ssl
            ctx = _ssl.create_default_context()
            with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30, context=ctx) as server:
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
        else:
            # STARTTLS — works for Gmail (587) and Outlook/Office 365 (587)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.send_message(msg)
    except smtplib.SMTPAuthenticationError as exc:
        raise RuntimeError(
            f"SMTP authentication failed for {smtp_user} on {smtp_host}:{smtp_port}. "
            "Check SMTP_USER and SMTP_PASSWORD. For Gmail use an App Password; "
            "for Outlook use your account password (or App Password if MFA is on)."
        ) from exc
    except (smtplib.SMTPException, OSError) as exc:
        raise RuntimeError(f"SMTP error sending to {to_email}: {exc}") from exc

    return {"sent": True}


def _record_delivery(data: dict, product: dict, status: str, store: DataStore, error: str = "") -> str:
    deliveries = store.get("digital_deliveries", default=[])
    nums = [int(d["id"][3:]) for d in deliveries if d["id"].startswith("DEL") and d["id"][3:].isdigit()]
    delivery_id = f"DEL{max(nums, default=0) + 1:04d}"

    record = {
        "id": delivery_id,
        "order_id": data["order_id"],
        "product_id": data["product_id"],
        "product_title": data.get("product_title", product["title"]),
        "customer_email": data["customer_email"],
        "customer_name": data.get("customer_name", "Valued Customer"),
        "status": status,
        "sent_at": str(date.today()),
        "error": error,
    }
    deliveries.append(record)
    store.set(deliveries, "digital_deliveries")
    store.save()
    return delivery_id


def _is_smtp_configured() -> bool:
    return bool(
        os.getenv("SMTP_HOST") and
        os.getenv("SMTP_PORT") and
        os.getenv("SMTP_USER") and
        os.getenv("SMTP_PASSWORD")
    )


# ── HELPERS ───────────────────────────────────────────────────────────────────

def _find_product(product_id: str, store: DataStore) -> dict | None:
    products = store.get("digital_products", default=[])
    return next((p for p in products if p["id"] == product_id), None)
