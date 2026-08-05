"""
Order Notifier for OnBrandCraftz.

Two jobs in one script:

  1. SMTP notification to the shop owner (Printing3dthings@outlook.com)
     Triggered on every new paid order — includes buyer name, product,
     order value, and the ready-to-send personalized Etsy message text.

  2. Personalized message generator
     Reads new orders, classifies the product type, and writes a warm
     personal Etsy message using the templates in etsy_messages.py.
     Output is printed / saved so the shop owner can paste into Etsy.

Usage:
  python tools/order_notifier.py          # check for new orders + send notifications
  python tools/order_notifier.py --dry    # preview only, no emails sent
  python tools/order_notifier.py --since 24h   # only orders in last 24 hours

State file:  data/notified_orders.json   (tracks which orders were already notified)

SMTP note: uses IPv4-forced socket to avoid Errno 97 on dual-stack hosts.
"""
from __future__ import annotations

import json
import os
import smtplib
import socket
import sys
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Env loading ───────────────────────────────────────────────────────────────
# Guarded: Railway has no .env file at all (env vars are injected directly by
# the platform), only Scott's local checkout does. Without this guard the
# script crashes with FileNotFoundError before it ever reaches a live Etsy
# call -- the same bug class diagnosed 2026-06-17 for etsy_autoresponder.py
# (see its own comment), found here 2026-07-17 while wiring this script in as
# an agent-callable command: order_notifier.py has run unguarded in the
# weekly monitor loop this whole time, its FileNotFoundError silently
# swallowed into that loop's generic per-script "ERROR:" line every week.
ENV_PATH = Path(__file__).parent.parent / '.env'
_env: dict[str, str] = {}
if ENV_PATH.exists():
    for _line in ENV_PATH.read_text().splitlines():
        if '=' in _line and not _line.startswith('#'):
            _k, _, _v = _line.partition('=')
            _env[_k.strip()] = _v.strip()
for _k, _v in _env.items():
    os.environ.setdefault(_k, _v)

sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient
from etsy_messages import (
    PERSONAL_MESSAGE_DIGITAL_PLANNER,
    PERSONAL_MESSAGE_WALL_ART,
    PERSONAL_MESSAGE_3D_PRINT,
    PERSONAL_MESSAGE_STICKER_PACK,
    PERSONAL_MESSAGE_GENERIC,
)

STATE_FILE = Path(__file__).parent.parent / 'data' / 'notified_orders.json'
SHOP_OWNER_EMAIL = os.environ.get('SMTP_USER', 'Printing3dthings@outlook.com')

# ── Product-type classifier ───────────────────────────────────────────────────

def _classify(title: str) -> str:
    t = title.lower()
    # 2026-08-05 (full-Etsy-audit finding): digital SVG packs use "3D Print" in
    # their own titles as a matter of shop convention (e.g. "America 250 SVG,
    # 10 Patriotic 3D Print Signs, Instant Download") -- without this check,
    # such a listing would classify as the physical '3d_print' branch below
    # and build_personal_message() would tell a buyer "I'm printing and
    # shipping this" for a product that's actually an instant digital
    # download, a direct customer-facing false statement (CLAUDE.md's NEVER
    # LIE TO THE CUSTOMER rule). Etsy's own listing `type` field is the
    # authoritative physical-vs-digital signal (see main.py's
    # classify_listings_batch()), but this classifier only ever sees a bare
    # title string -- these keywords are a title-only mitigation for the
    # collision that's actually occurred in this shop's real catalog
    # (SS_AMERICA_250_SVG), not a full replacement for a structured check.
    is_explicitly_digital = any(x in t for x in ['svg', 'instant download', 'digital download'])
    # 3D print must be checked before wall_art — "3D Printed" contains "print"
    if not is_explicitly_digital and any(x in t for x in ['3d printed', '3d print', 'koozie', 'planter', 'candle holder',
                              'tea light', 'lamp shade', 'desk organizer', 'pen holder',
                              'centerpiece', 'vase', 'filament']):
        return '3d_print'
    if any(x in t for x in ['planner', 'goodnotes', 'notability', 'fillable', 'pdf planner']):
        return 'digital_planner'
    if any(x in t for x in ['sticker', 'sticker pack', 'sticker book']):
        return 'sticker_pack'
    if 'svg' in t:
        # A digital SVG/3D-print-file pack, not physical wall art -- route to
        # the product-agnostic generic template rather than falling through
        # to the wall_art check below, whose "love it on your wall" framing
        # would itself be a smaller-but-real content mismatch for a buyer who
        # actually bought a cut file for their own 3D printer or cutting
        # machine, not framed art.
        return 'generic'
    if any(x in t for x in ['wall art', 'art print', 'botanical print', 'poster',
                              'digital download', 'printable', 'instant download',
                              'watercolor', 'illustration', 'photography print']):
        return 'wall_art'
    return 'generic'

_TEMPLATES = {
    'digital_planner': PERSONAL_MESSAGE_DIGITAL_PLANNER,
    'wall_art': PERSONAL_MESSAGE_WALL_ART,
    '3d_print': PERSONAL_MESSAGE_3D_PRINT,
    'sticker_pack': PERSONAL_MESSAGE_STICKER_PACK,
    'generic': PERSONAL_MESSAGE_GENERIC,
}

def build_personal_message(buyer_name: str, product_title: str) -> str:
    first_name = buyer_name.split()[0] if buyer_name else 'there'
    # Trim Etsy keyword-stuffed titles to the first pipe segment
    short_title = product_title.split('|')[0].strip()
    kind = _classify(product_title)
    template = _TEMPLATES[kind]
    return template.format(
        buyer_name=first_name,   # first name only in greeting
        first_name=first_name,
        product_title=short_title,
    )

# ── SMTP (IPv4-forced) ────────────────────────────────────────────────────────

def _smtp_send_owner_notification(orders: list[dict], dry_run: bool = False) -> bool:
    """Email the shop owner a digest of new orders with personal message text."""
    if not orders:
        return True

    host = os.environ.get('SMTP_HOST', 'smtp.office365.com')
    port = int(os.environ.get('SMTP_PORT', '587'))
    user = os.environ.get('SMTP_USER', '')
    password = os.environ.get('SMTP_PASSWORD', '')

    if not (host and port and user and password):
        print("  [SMTP] Not configured — skipping owner notification email.")
        return False

    # Build HTML body
    order_rows = ''
    for o in orders:
        personal_msg = o.get('personal_message', '').replace('\n', '<br>')
        order_rows += f"""
        <div style="border:1px solid #e5e7eb;border-radius:8px;padding:16px;margin:16px 0;">
          <h3 style="margin:0 0 8px;color:#374151;">
            🛍️ Order #{o['receipt_id']} — {o['buyer_name']}
          </h3>
          <table style="font-size:14px;color:#6b7280;border-collapse:collapse;width:100%">
            <tr><td style="padding:3px 12px 3px 0"><strong>Product</strong></td>
                <td>{o['product_title']}</td></tr>
            <tr><td style="padding:3px 12px 3px 0"><strong>Type</strong></td>
                <td>{o['product_type'].replace('_',' ').title()}</td></tr>
            <tr><td style="padding:3px 12px 3px 0"><strong>Total</strong></td>
                <td>${o['total']}</td></tr>
            <tr><td style="padding:3px 12px 3px 0"><strong>Ordered</strong></td>
                <td>{o['ordered_at']}</td></tr>
          </table>
          <div style="margin-top:12px;background:#f9fafb;border-left:3px solid #8666aa;
                      padding:12px 14px;border-radius:0 6px 6px 0;">
            <p style="margin:0 0 6px;font-weight:bold;color:#374151;font-size:13px;">
              ✉️ Personalized Etsy message — copy &amp; paste into Etsy:
            </p>
            <pre style="font-family:Arial,sans-serif;font-size:13px;
                        white-space:pre-wrap;margin:0;color:#374151;">{o['personal_message']}</pre>
          </div>
          <p style="margin:8px 0 0;font-size:12px;color:#9ca3af;">
            <a href="https://www.etsy.com/your/orders/{o['receipt_id']}">View order on Etsy →</a>
          </p>
        </div>"""

    subject = f"🛍️ {len(orders)} new order{'s' if len(orders)>1 else ''} — OnBrandCraftz"
    body = f"""<html><body style="font-family:Arial,sans-serif;color:#333;max-width:680px;margin:0 auto;">
      <h2 style="color:#8666aa;">New order{'s' if len(orders)>1 else ''} just came in! 🎉</h2>
      <p style="color:#6b7280;">
        {len(orders)} new paid order{'s' if len(orders)>1 else ''} on OnBrandCraftz.
        Each order below includes a ready-to-send personalized Etsy message.
      </p>
      {order_rows}
      <hr style="border:none;border-top:1px solid #e5e7eb;margin:24px 0;">
      <p style="color:#9ca3af;font-size:12px;">
        OnBrandCraftz automated order notifier •
        <a href="https://www.etsy.com/your/orders">View all orders on Etsy →</a>
      </p>
    </body></html>"""

    if dry_run:
        print(f"\n[DRY RUN] Would send owner notification to {user}")
        print(f"  Subject: {subject}")
        print(f"  Orders: {[o['receipt_id'] for o in orders]}")
        return True

    try:
        # Force IPv4 to avoid Errno 97 on dual-stack hosts
        ipv4_addr = socket.getaddrinfo(host, port, socket.AF_INET)[0][4][0]

        msg = MIMEMultipart('alternative')
        msg['From'] = f'OnBrandCraftz <{user}>'
        msg['To'] = SHOP_OWNER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP(ipv4_addr, port, timeout=20) as s:
            s.ehlo(host)
            s.starttls()
            s.ehlo(host)
            s.login(user, password)
            s.send_message(msg)

        print(f"  ✓ Owner notification sent to {SHOP_OWNER_EMAIL}")
        return True

    except Exception as exc:
        print(f"  ✗ Owner email failed: {exc}")
        return False

# ── State tracking ────────────────────────────────────────────────────────────

def _load_state() -> set[str]:
    if STATE_FILE.exists():
        data = json.loads(STATE_FILE.read_text())
        return set(data.get('notified', []))
    return set()

def _save_state(notified: set[str]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps({'notified': sorted(notified)}, indent=2))

# ── Main logic ────────────────────────────────────────────────────────────────

def check_new_orders(since_hours: int = 48, dry_run: bool = False) -> list[dict]:
    client = EtsyAPIClient()
    shop_id = os.environ.get('ETSY_SHOP_ID_NUMERIC', '65012858')

    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    cutoff_ts = int(cutoff.timestamp())

    resp = client._request('GET', f'shops/{shop_id}/receipts',
                           params={'limit': 100, 'was_paid': True, 'min_created': cutoff_ts})
    receipts = resp.get('results', [])

    already_notified = _load_state()
    new_orders: list[dict] = []

    for r in receipts:
        rid = str(r['receipt_id'])
        if rid in already_notified:
            continue

        transactions = r.get('transactions', [])
        if not transactions:
            continue

        # Use first transaction for product info
        txn = transactions[0]
        product_title = txn.get('title', 'Unknown Product')
        buyer_name = r.get('name', 'Valued Customer')
        total = r.get('grandtotal', {})
        if isinstance(total, dict):
            total_str = f"{float(total.get('amount', 0)) / total.get('divisor', 100):.2f}"
        else:
            total_str = str(total)

        ordered_at = datetime.fromtimestamp(
            r.get('created_timestamp', 0), tz=timezone.utc
        ).strftime('%b %d, %Y at %I:%M %p UTC')

        kind = _classify(product_title)
        personal_msg = build_personal_message(buyer_name, product_title)

        order = {
            'receipt_id': rid,
            'buyer_name': buyer_name,
            'buyer_user_id': r.get('buyer_user_id'),
            'product_title': product_title,
            'product_type': kind,
            'total': total_str,
            'ordered_at': ordered_at,
            'personal_message': personal_msg,
            'all_items': [t.get('title', '') for t in transactions],
        }
        new_orders.append(order)

    return new_orders, already_notified

def run(since_hours: int = 48, dry_run: bool = False) -> None:
    print(f"Checking for new orders (last {since_hours}h)...")
    new_orders, already_notified = check_new_orders(since_hours, dry_run)

    if not new_orders:
        print("  No new orders to notify.")
        return

    print(f"  Found {len(new_orders)} new order(s):")
    for o in new_orders:
        print(f"    #{o['receipt_id']} — {o['buyer_name']} — {o['product_title'][:50]}")

    # Print personalized messages to console
    print("\n" + "═" * 60)
    print("PERSONALIZED ETSY MESSAGES — copy & paste for each buyer:")
    print("═" * 60)
    for o in new_orders:
        print(f"\n── Order #{o['receipt_id']} → {o['buyer_name']} ──")
        print(f"   Product: {o['product_title']}")
        print(f"   Type: {o['product_type']}")
        print(f"\n{o['personal_message']}")
        print(f"   [Etsy link: https://www.etsy.com/your/orders/{o['receipt_id']}]")

    # Send owner notification email
    print("\nSending owner notification email...")
    _smtp_send_owner_notification(new_orders, dry_run=dry_run)

    # Mark as notified
    if not dry_run:
        for o in new_orders:
            already_notified.add(o['receipt_id'])
        _save_state(already_notified)
        print(f"\n✓ Marked {len(new_orders)} order(s) as notified.")

# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    dry = '--dry' in sys.argv
    since = 48
    for arg in sys.argv:
        if arg.startswith('--since'):
            val = arg.split()[-1] if ' ' in arg else (sys.argv[sys.argv.index(arg)+1] if sys.argv.index(arg)+1 < len(sys.argv) else '48h')
            since = int(val.replace('h','').replace('d','')) * (24 if 'd' in val else 1)

    run(since_hours=since, dry_run=dry)
