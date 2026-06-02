#!/usr/bin/env python3
"""
Seasonal Sales Scheduler — OnBrandCraftz Etsy Automation

Runs daily (via cron). Checks whether today falls inside any scheduled sale
window and, if so:
  1. Attempts to create an Etsy coupon via the API
  2. Sends an action email to Scott with exact Shop Manager steps
  3. Logs the event to data/sales_schedule.json

Usage:
  python tools/seasonal_sales_scheduler.py             # check today, trigger if needed
  python tools/seasonal_sales_scheduler.py --preview   # show next 180 days of planned sales
  python tools/seasonal_sales_scheduler.py --force HOLIDAY_NAME  # force-trigger a specific sale

Cron example (runs at 7 AM daily):
  0 7 * * * cd /home/user/Etsy && python tools/seasonal_sales_scheduler.py >> data/cron_sales.log 2>&1
"""

from __future__ import annotations

import argparse
import json
import smtplib
import sys
import os
import urllib.request
import urllib.error
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE = Path(__file__).parent.parent.resolve()
STATE_FILE = BASE / "data" / "sales_schedule.json"

# ── Env loader (never use load_dotenv) ───────────────────────────────────────

def _parse_env() -> dict:
    env: dict[str, str] = {}
    env_path = BASE / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    return env


# ── Holiday date helpers ──────────────────────────────────────────────────────

def _nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """Return the Nth occurrence of weekday (0=Mon … 6=Sun) in the given month/year.

    n=1 → first, n=2 → second, n=4 → fourth.
    """
    first_of_month = date(year, month, 1)
    # days until the first occurrence of this weekday
    offset = (weekday - first_of_month.weekday()) % 7
    first_occurrence = first_of_month + timedelta(days=offset)
    return first_occurrence + timedelta(weeks=(n - 1))


def _mothers_day(year: int) -> date:
    """2nd Sunday of May."""
    return _nth_weekday(year, 5, 6, 2)


def _black_friday(year: int) -> date:
    """4th Thursday of November + 1 day = the Friday."""
    thanksgiving = _nth_weekday(year, 11, 3, 4)  # Thursday = weekday 3
    return thanksgiving + timedelta(days=1)


# ── Sales calendar definition ─────────────────────────────────────────────────
# Each entry defines a sale by its anchor date, how many days before the anchor
# the sale starts, and how many days it runs.
#
# Sale window: [anchor - lead_days, anchor - lead_days + duration_days)
# The sale triggers on the FIRST day of the window.

class SaleDefinition:
    """Holds a single sale's parameters."""

    def __init__(
        self,
        name: str,
        slug: str,
        coupon_suffix: str,
        discount_pct: int,
        duration_days: int,
        lead_days: int,
        anchor_fn,   # callable(year) -> date  — the event date
        blurb: str,
    ):
        self.name = name
        self.slug = slug
        self.coupon_suffix = coupon_suffix   # appended to SALE to form the code
        self.discount_pct = discount_pct
        self.duration_days = duration_days
        self.lead_days = lead_days
        self.anchor_fn = anchor_fn
        self.blurb = blurb

    def start(self, year: int) -> date:
        return self.anchor_fn(year) - timedelta(days=self.lead_days)

    def end(self, year: int) -> date:
        """Last day of the sale (inclusive)."""
        return self.start(year) + timedelta(days=self.duration_days - 1)

    def coupon_code(self, year: int) -> str:
        """e.g. MOTHERSDAY25, BTS25, HALLOWEEN25"""
        return f"{self.coupon_suffix}{self.discount_pct}"


# The full sales calendar
SALES: list[SaleDefinition] = [
    SaleDefinition(
        name="Mother's Day",
        slug="mothers_day",
        coupon_suffix="MOTHERSDAY",
        discount_pct=25,
        duration_days=5,
        lead_days=14,
        anchor_fn=_mothers_day,
        blurb="One of the top gifting occasions for planners and digital products.",
    ),
    SaleDefinition(
        name="Back to School",
        slug="back_to_school",
        coupon_suffix="BTS",
        discount_pct=25,
        duration_days=10,
        lead_days=0,
        anchor_fn=lambda year: date(year, 8, 1),
        blurb="Peak season for student and life planners. Runs Aug 1–10.",
    ),
    SaleDefinition(
        name="Halloween",
        slug="halloween",
        coupon_suffix="HALLOWEEN",
        discount_pct=25,
        duration_days=10,
        lead_days=13,   # Oct 31 - 13 = Oct 18 start
        anchor_fn=lambda year: date(year, 10, 31),
        blurb="Spooky season sale — drives seasonal sticker and planner traffic.",
    ),
    SaleDefinition(
        name="Black Friday",
        slug="black_friday",
        coupon_suffix="BLACKFRIDAY",
        discount_pct=25,
        duration_days=5,
        lead_days=2,    # starts Nov 22 (2 days before BF 2026 = Nov 27 - 2 = Nov 25... corrected below)
        # Black Friday 2026: Nov 27 → start Nov 22 = lead of 5 days but spec says start Nov 22 → 5 days
        # We encode this as: anchor = Black Friday, lead = 5 days before
        anchor_fn=lambda year: _black_friday(year) + timedelta(days=0),
        blurb="Biggest sale of the year. Runs 5 days starting ~Nov 22.",
    ),
    SaleDefinition(
        name="Christmas & Holiday",
        slug="christmas",
        coupon_suffix="HOLIDAY",
        discount_pct=25,
        duration_days=10,
        lead_days=0,    # starts Dec 10 directly
        anchor_fn=lambda year: date(year, 12, 10),
        blurb="Holiday gifting season. Digital planners make perfect last-minute gifts.",
    ),
    SaleDefinition(
        name="New Year / Planner Season",
        slug="new_year",
        coupon_suffix="NEWYEAR",
        discount_pct=25,
        duration_days=10,
        lead_days=0,
        anchor_fn=lambda year: date(year, 12, 26),
        blurb="HUGE for planners — new year, new goals, highest organic planner traffic of the year.",
    ),
    SaleDefinition(
        name="Valentine's Day",
        slug="valentines_day",
        coupon_suffix="VALENTINES",
        discount_pct=25,
        duration_days=10,
        lead_days=13,   # Feb 14 - 13 = Feb 1
        anchor_fn=lambda year: date(year, 2, 14),
        blurb="Self-care, gifting, and romance planners all perform well.",
    ),
    SaleDefinition(
        name="Spring Reset",
        slug="spring_reset",
        coupon_suffix="SPRING",
        discount_pct=25,
        duration_days=7,
        lead_days=0,
        anchor_fn=lambda year: date(year, 3, 20),
        blurb="Spring equinox — fresh-start energy drives planner and wellness product sales.",
    ),
]

# Override Black Friday lead to match spec (start Nov 22 → BF is ~Nov 27-28):
# The spec says "start Nov 22, run 5 days" for Black Friday.
# Black Friday 2026 = Nov 27. start = Nov 22 → lead = 5 days.
# We set lead_days=5 for that entry:
SALES[3] = SaleDefinition(
    name="Black Friday",
    slug="black_friday",
    coupon_suffix="BLACKFRIDAY",
    discount_pct=25,
    duration_days=5,
    lead_days=5,
    anchor_fn=_black_friday,
    blurb="Biggest sale of the year. Runs 5 days starting ~Nov 22.",
)


# ── State management ──────────────────────────────────────────────────────────

def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"triggered_sales": [], "log": []}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))


def _sale_key(sale: SaleDefinition, year: int) -> str:
    return f"{sale.slug}_{year}"


def _already_triggered(state: dict, sale: SaleDefinition, year: int) -> bool:
    return _sale_key(sale, year) in state.get("triggered_sales", [])


def _mark_triggered(state: dict, sale: SaleDefinition, year: int) -> None:
    state.setdefault("triggered_sales", [])
    key = _sale_key(sale, year)
    if key not in state["triggered_sales"]:
        state["triggered_sales"].append(key)


def _log_event(state: dict, event: dict) -> None:
    state.setdefault("log", [])
    state["log"].append(event)
    # Keep last 200 log entries
    state["log"] = state["log"][-200:]


# ── Etsy coupon creation ──────────────────────────────────────────────────────

def _create_etsy_coupon(env: dict, shop_id: str, coupon_code: str, discount_pct: int) -> tuple[bool, str]:
    """Attempt to create an Etsy discount/coupon via the API.

    Returns (success, message).
    The Etsy v3 discount endpoint is not officially documented for third-party
    OAuth apps; if it fails we fall back gracefully to email-only mode.
    """
    access_token = env.get("ETSY_ACCESS_TOKEN", "")
    client_id = env.get("ETSY_CLIENT_ID", "")
    client_secret = env.get("ETSY_CLIENT_SECRET", "")

    if not access_token or not shop_id:
        return False, "No access token or shop ID — skipping API call, using email fallback."

    url = f"https://openapi.etsy.com/v3/application/shops/{shop_id}/discount"
    payload = json.dumps({
        "seller_active": True,
        "pct_discount": discount_pct,
        "coupon_code": coupon_code,
        "min_order_subtotal_amount": 0,
    }).encode()

    api_key_header = f"{client_id}:{client_secret}" if client_secret else client_id
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "x-api-key": api_key_header,
    }
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        return True, f"Coupon created via API. Response: {json.dumps(result)}"
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode()
        except Exception:
            pass
        return False, f"API returned HTTP {e.code}: {body[:300]}"
    except Exception as exc:
        return False, f"Network error: {exc}"


# ── Email notification ────────────────────────────────────────────────────────

def _build_email_body(
    sale: SaleDefinition,
    year: int,
    coupon_code: str,
    api_success: bool,
    api_message: str,
) -> tuple[str, str]:
    """Return (subject, html_body) for the sale action email."""

    start_str = sale.start(year).strftime("%B %d, %Y")
    end_str = sale.end(year).strftime("%B %d, %Y")
    discount_pct = sale.discount_pct

    api_status_line = (
        f"<p style='color:#27ae60'><strong>API Status:</strong> Coupon <code>{coupon_code}</code> "
        f"was created automatically via the Etsy API.</p>"
        if api_success
        else f"<p style='color:#c0392b'><strong>API Status:</strong> Coupon could not be created automatically "
             f"({api_message[:200]}). <strong>Please create it manually using the steps below.</strong></p>"
    )

    subject = f"\U0001f6cd️ ACTION: Start {sale.name} Sale Now — OnBrandCraftz"

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; max-width: 640px; margin: 0 auto; color: #333; }}
  h1 {{ color: #8666AA; }}
  h2 {{ color: #555; border-bottom: 2px solid #eee; padding-bottom: 6px; }}
  .sale-box {{ background: #faf7ff; border-left: 4px solid #8666AA; padding: 14px 18px;
               border-radius: 4px; margin: 16px 0; }}
  .step {{ background: #f9f9f9; border: 1px solid #ddd; border-radius: 4px;
           padding: 10px 14px; margin: 8px 0; }}
  .step strong {{ color: #8666AA; }}
  code {{ background: #f0ebff; padding: 2px 6px; border-radius: 3px; font-size: 14px;
          font-weight: bold; color: #5a3e8a; }}
  .footer {{ margin-top: 32px; font-size: 12px; color: #888; border-top: 1px solid #eee;
             padding-top: 12px; }}
  .highlight {{ background: #fff3cd; border: 1px solid #ffc107; padding: 10px 14px;
                border-radius: 4px; margin: 12px 0; }}
</style>
</head>
<body>

<h1>\U0001f6cd️ {sale.name} Sale — Time to Activate!</h1>

<div class="sale-box">
  <strong>Sale:</strong> {sale.name}<br>
  <strong>Coupon Code:</strong> <code>{coupon_code}</code><br>
  <strong>Discount:</strong> {discount_pct}% off all digital products<br>
  <strong>Sale Window:</strong> {start_str} &rarr; {end_str} ({sale.duration_days} days)<br>
  <strong>Why now:</strong> {sale.blurb}
</div>

{api_status_line}

<h2>Steps to Activate the Sale in Etsy Shop Manager</h2>

<div class="step">
  <strong>Step 1 &mdash; Open Sales &amp; Discounts</strong><br>
  Go to <a href="https://www.etsy.com/your/shop/tools/sales-and-discounts">
  Etsy Shop Manager &rarr; Marketing &rarr; Sales &amp; Discounts</a>
</div>

<div class="step">
  <strong>Step 2 &mdash; Create a New Sale</strong><br>
  Click <em>"Create a sale"</em> &rarr; choose <em>"Percentage off"</em>
</div>

<div class="step">
  <strong>Step 3 &mdash; Configure the Sale</strong><br>
  &bull; Discount amount: <code>{discount_pct}%</code><br>
  &bull; Applies to: All digital items (or select Digital Planners section)<br>
  &bull; Minimum order: None<br>
  &bull; Start date: <strong>{start_str}</strong><br>
  &bull; End date: <strong>{end_str}</strong>
</div>

<div class="step">
  <strong>Step 4 &mdash; Add a Coupon Code (optional but recommended)</strong><br>
  In the same Marketing menu, go to <em>Coupon Codes</em> &rarr; <em>Create a Coupon</em>:<br>
  &bull; Code: <code>{coupon_code}</code><br>
  &bull; Discount: <code>{discount_pct}%</code><br>
  &bull; Minimum purchase: None<br>
  &bull; Expiry: <strong>{end_str}</strong>
</div>

<div class="step">
  <strong>Step 5 &mdash; Update Shop Announcement (optional)</strong><br>
  Add to your shop announcement: <em>"&#127873; {sale.name} Sale &mdash; {discount_pct}% off with code <code>{coupon_code}</code>. Ends {end_str}!"</em>
</div>

<div class="highlight">
  <strong>&#128204; Don't forget:</strong> Pin the top-selling planner listing to the top of your
  shop during the sale window for maximum visibility.
</div>

<h2>Checklist Before Going Live</h2>
<ul>
  <li>&#9989; Sale or coupon created in Etsy Shop Manager</li>
  <li>&#9989; Shop announcement updated with sale info</li>
  <li>&#9989; (Optional) Post a &ldquo;plan with me&rdquo; TikTok or Pinterest pin linking to the shop</li>
  <li>&#9989; Monitor conversion rate daily in Etsy Analytics during the window</li>
</ul>

<div class="footer">
  Sent automatically by <strong>OnBrandCraftz Seasonal Sales Scheduler</strong><br>
  Sale slug: <code>{sale.slug}_{year}</code> &bull; Coupon: <code>{coupon_code}</code><br>
  To stop these emails, disable the cron job or comment out this sale in
  <code>tools/seasonal_sales_scheduler.py</code>.
</div>
</body>
</html>"""

    return subject, html_body


def _send_email(env: dict, to_addr: str, subject: str, html_body: str) -> tuple[bool, str]:
    """Send HTML email via smtp.office365.com:587 (STARTTLS).

    Returns (success, message).
    """
    smtp_user = env.get("SMTP_USER", "")
    smtp_pass = env.get("SMTP_PASSWORD", "")
    sender_name = env.get("SENDER_NAME", "OnBrandCraftz")

    if not smtp_user or not smtp_pass:
        return False, "SMTP_USER or SMTP_PASSWORD not set in .env — cannot send email."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{sender_name} <{smtp_user}>"
    msg["To"] = to_addr

    # Plain-text fallback (strip obvious HTML tags)
    plain = subject + "\n\nPlease view this email in an HTML-capable client for the full action steps.\n"
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP("smtp.office365.com", 587, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [to_addr], msg.as_string())
        return True, f"Email sent to {to_addr}"
    except smtplib.SMTPAuthenticationError as exc:
        return False, f"SMTP authentication failed: {exc}"
    except smtplib.SMTPException as exc:
        return False, f"SMTP error: {exc}"
    except OSError as exc:
        return False, f"Network error sending email: {exc}"


# ── Core trigger logic ────────────────────────────────────────────────────────

OWNER_EMAIL = "Printing3dthings@outlook.com"


def trigger_sale(sale: SaleDefinition, year: int, env: dict, state: dict, force: bool = False) -> dict:
    """Run the full trigger pipeline for a sale. Returns a result dict."""
    coupon_code = sale.coupon_code(year)
    shop_id = env.get("ETSY_SHOP_ID_NUMERIC") or env.get("ETSY_SHOP_ID", "onbrandcraftz")

    print(f"  [TRIGGER] {sale.name} ({year}) — coupon {coupon_code}")
    print(f"            Window: {sale.start(year)} → {sale.end(year)}")

    # 1. Try Etsy API
    print(f"  [API]     Attempting to create Etsy coupon...")
    api_success, api_message = _create_etsy_coupon(env, shop_id, coupon_code, sale.discount_pct)
    if api_success:
        print(f"  [API]     Success: {api_message[:120]}")
    else:
        print(f"  [API]     Fallback (email only): {api_message[:120]}")

    # 2. Send email
    print(f"  [EMAIL]   Sending action email to {OWNER_EMAIL}...")
    subject, html_body = _build_email_body(sale, year, coupon_code, api_success, api_message)
    email_success, email_message = _send_email(env, OWNER_EMAIL, subject, html_body)
    if email_success:
        print(f"  [EMAIL]   {email_message}")
    else:
        print(f"  [EMAIL]   FAILED: {email_message}")

    # 3. Log event
    result = {
        "sale_slug": sale.slug,
        "sale_name": sale.name,
        "year": year,
        "coupon_code": coupon_code,
        "sale_start": str(sale.start(year)),
        "sale_end": str(sale.end(year)),
        "triggered_on": str(date.today()),
        "forced": force,
        "api_success": api_success,
        "api_message": api_message[:300],
        "email_success": email_success,
        "email_message": email_message,
    }
    _log_event(state, result)
    _mark_triggered(state, sale, year)
    _save_state(state)

    print(f"  [LOG]     Event saved to {STATE_FILE.relative_to(BASE)}")
    return result


# ── Today check ───────────────────────────────────────────────────────────────

def check_today(env: dict) -> None:
    """Check whether today triggers any sale. Called by the daily cron."""
    today = date.today()
    state = _load_state()
    triggered_any = False

    print(f"[seasonal_sales_scheduler] Checking sales for {today}")

    for sale in SALES:
        # Check both current year and next year (handles Dec 26 New Year spanning calendar years)
        for year in sorted({today.year, today.year + 1}):
            try:
                start = sale.start(year)
                end = sale.end(year)
            except Exception:
                continue

            if start != today:
                continue  # Only trigger on the FIRST day of the window

            if _already_triggered(state, sale, year):
                print(f"  [SKIP]    {sale.name} {year} already triggered this cycle.")
                continue

            print(f"  [MATCH]   {sale.name} {year} starts today!")
            trigger_sale(sale, year, env, state)
            triggered_any = True

    if not triggered_any:
        print("  [OK]      No sales trigger today.")
        # Find next upcoming sale for info
        upcoming = _next_upcoming_sales(today, count=1)
        if upcoming:
            nxt = upcoming[0]
            days_away = (nxt["start"] - today).days
            print(f"  [NEXT]    {nxt['name']} starts in {days_away} day(s) on {nxt['start']}")


# ── Preview mode ──────────────────────────────────────────────────────────────

def _next_upcoming_sales(from_date: date, count: int = 20, horizon_days: int = 180) -> list[dict]:
    """Return upcoming sale windows within the next horizon_days."""
    upcoming = []
    limit = from_date + timedelta(days=horizon_days)
    seen_slugs: set[str] = set()

    for sale in SALES:
        for year in [from_date.year, from_date.year + 1]:
            try:
                start = sale.start(year)
                end = sale.end(year)
            except Exception:
                continue

            key = f"{sale.slug}_{year}"
            if key in seen_slugs:
                continue
            if start > limit:
                continue
            if end < from_date:
                continue  # already passed

            seen_slugs.add(key)
            upcoming.append({
                "name": sale.name,
                "slug": sale.slug,
                "year": year,
                "start": start,
                "end": end,
                "coupon": sale.coupon_code(year),
                "discount_pct": sale.discount_pct,
                "duration_days": sale.duration_days,
                "blurb": sale.blurb,
                "active": start <= from_date <= end,
                "days_until_start": max(0, (start - from_date).days),
            })

    upcoming.sort(key=lambda x: x["start"])
    return upcoming[:count]


def preview(horizon_days: int = 180) -> None:
    """Print the next 180 days of planned sales."""
    today = date.today()
    sales = _next_upcoming_sales(today, count=50, horizon_days=horizon_days)
    state = _load_state()

    print(f"\n{'='*70}")
    print(f"  OnBrandCraftz — Seasonal Sales Preview")
    print(f"  From: {today}  |  Horizon: {horizon_days} days")
    print(f"{'='*70}\n")

    if not sales:
        print("  No sales scheduled in this window.")
        return

    for s in sales:
        already = _already_triggered(state, _sale_by_slug(s["slug"]), s["year"])
        status = "[ACTIVE NOW]" if s["active"] else ("[TRIGGERED]" if already else "")
        days_info = (
            f"ACTIVE — ends {s['end']}"
            if s["active"]
            else f"in {s['days_until_start']} day(s)"
        )
        print(f"  {s['name']:30s}  {str(s['start']):12s} → {str(s['end']):12s}  "
              f"{s['discount_pct']}% off  |  Code: {s['coupon']:20s}  |  Starts {days_info}  {status}")
        print(f"  {'':30s}  {s['blurb']}")
        print()

    print(f"{'='*70}")
    print(f"  Total: {len(sales)} sale(s) in the next {horizon_days} days")
    print(f"  State file: {STATE_FILE}")
    print(f"{'='*70}\n")


def _sale_by_slug(slug: str) -> SaleDefinition:
    """Look up a sale by its slug. Raises ValueError if not found."""
    for s in SALES:
        if s.slug == slug:
            return s
    raise ValueError(f"No sale with slug '{slug}'")


def _sale_by_name(name: str) -> SaleDefinition:
    """Case-insensitive partial name match. Raises ValueError if not found."""
    name_lower = name.lower()
    # Exact slug match first
    for s in SALES:
        if s.slug.lower() == name_lower:
            return s
    # Partial name match
    matches = [s for s in SALES if name_lower in s.name.lower()]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        names = ", ".join(m.name for m in matches)
        raise ValueError(f"Ambiguous name '{name}' — matches: {names}. Use the full slug.")
    available = ", ".join(s.slug for s in SALES)
    raise ValueError(f"No sale named '{name}'. Available slugs: {available}")


# ── Force mode ────────────────────────────────────────────────────────────────

def force_trigger(name: str, env: dict) -> None:
    """Force-trigger a sale by name/slug regardless of date or prior trigger."""
    sale = _sale_by_name(name)
    year = date.today().year
    state = _load_state()

    print(f"\n[FORCE] Triggering '{sale.name}' ({year})")
    print(f"        Sale window: {sale.start(year)} → {sale.end(year)}")
    print(f"        Note: force mode bypasses the date check and deduplication.\n")

    result = trigger_sale(sale, year, env, state, force=True)
    print(f"\n[DONE]  Result: API={'OK' if result['api_success'] else 'FAILED (email sent)'} | "
          f"Email={'OK' if result['email_success'] else 'FAILED'}")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="OnBrandCraftz Seasonal Sales Scheduler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/seasonal_sales_scheduler.py               # daily cron check
  python tools/seasonal_sales_scheduler.py --preview     # show next 180 days
  python tools/seasonal_sales_scheduler.py --preview --days 365
  python tools/seasonal_sales_scheduler.py --force mothers_day
  python tools/seasonal_sales_scheduler.py --force "Back to School"
  python tools/seasonal_sales_scheduler.py --list        # list all sale slugs

Available sale slugs:
  """ + "  ".join(s.slug for s in SALES),
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Show upcoming sales for the next N days (default 180)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=180,
        metavar="N",
        help="Horizon for --preview in days (default 180)",
    )
    parser.add_argument(
        "--force",
        metavar="HOLIDAY_NAME",
        help="Force-trigger a sale by slug or name (case-insensitive, partial match OK)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all configured sales and their slugs",
    )
    args = parser.parse_args()

    if args.list:
        print("\nConfigured sales:\n")
        for s in SALES:
            y = date.today().year
            try:
                start = s.start(y)
                end = s.end(y)
            except Exception:
                start = end = "N/A"
            print(f"  slug={s.slug:20s}  name={s.name:25s}  {y}: {start} → {end}  code={s.coupon_code(y)}")
        print()
        return

    if args.preview:
        preview(horizon_days=args.days)
        return

    env = _parse_env()

    if args.force:
        force_trigger(args.force, env)
        return

    # Default: daily check
    check_today(env)


if __name__ == "__main__":
    main()
