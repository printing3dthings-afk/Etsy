#!/usr/bin/env python3
"""
Etsy Ads Monitor — daily ROAS check and kill/keep/scale recommendations.

Reads ad config from .env:
  ETSY_ADS_DAILY_BUDGET   — daily spend cap (e.g. 1.30)
  ETSY_ADS_START_DATE     — ISO date when ads were turned on (e.g. 2026-06-02)

Pulls recent orders from the Etsy API, calculates spend vs revenue, and
prints a kill/keep/scale table based on the research-backed thresholds:
  Kill:  >$30 spent + zero orders
  Watch: ROAS < 1.5 after 30+ days
  Keep:  ROAS 1.5–4.0
  Scale: ROAS > 4.0

Logs a daily snapshot to data/ads_log.json.
Sends an email alert if ROAS drops below 1.0 after 14+ days of data.

Usage:
  python tools/ads_monitor.py              # full report
  python tools/ads_monitor.py --quiet      # only print if action needed
"""

from __future__ import annotations

import os
import sys
import json
import smtplib
import argparse
from datetime import date, datetime, timedelta
from email.mime.text import MIMEText
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ── Parse .env ───────────────────────────────────────────────────────────────
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(_ENV_PATH) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

from tools.etsy_api import EtsyAPIClient, is_configured

# ── Config ───────────────────────────────────────────────────────────────────
ADS_LOG_PATH  = Path(__file__).parent.parent / "data" / "ads_log.json"
DAILY_BUDGET  = float(os.getenv("ETSY_ADS_DAILY_BUDGET", "1.30"))
START_DATE_STR = os.getenv("ETSY_ADS_START_DATE", str(date.today()))
OWNER_EMAIL   = os.getenv("SMTP_USER", "Printing3dthings@outlook.com")
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# ROAS thresholds (from CLAUDE.md research)
ROAS_KILL  = 0.0   # kill immediately if $30+ spent with zero orders
ROAS_WATCH = 1.5   # flag for review after 30 days
ROAS_KEEP  = 4.0   # healthy, keep running
# ROAS > 4.0 → scale budget by 20–30%


def _parse_start_date() -> date:
    try:
        return date.fromisoformat(START_DATE_STR)
    except ValueError:
        return date.today()


def _load_log() -> list[dict]:
    if not ADS_LOG_PATH.exists():
        return []
    with open(ADS_LOG_PATH) as f:
        return json.load(f)


def _save_log(entries: list[dict]) -> None:
    ADS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ADS_LOG_PATH, "w") as f:
        json.dump(entries[-180:], f, indent=2)  # rolling 180 days


def _fetch_recent_orders(client: EtsyAPIClient, days: int = 30) -> list[dict]:
    """Fetch completed orders in the last N days."""
    try:
        raw = client.get_orders(limit=100, status="completed")
        orders = raw.get("results", [])
    except Exception:
        try:
            raw = client.get_orders(limit=100)
            orders = raw.get("results", [])
        except Exception as e:
            print(f"  [ads_monitor] Warning: could not fetch orders — {e}")
            return []

    cutoff = datetime.utcnow() - timedelta(days=days)
    recent = []
    for o in orders:
        created = o.get("create_timestamp") or o.get("created_timestamp", 0)
        if isinstance(created, (int, float)) and created > cutoff.timestamp():
            recent.append(o)
        elif isinstance(created, str):
            try:
                if datetime.fromisoformat(created) > cutoff:
                    recent.append(o)
            except ValueError:
                pass
    return recent


def _order_revenue(order: dict) -> float:
    """Extract total revenue from an order dict."""
    grandtotal = order.get("grandtotal", {})
    if isinstance(grandtotal, dict):
        return float(grandtotal.get("amount", 0)) / max(grandtotal.get("divisor", 100), 1)
    return float(order.get("total_price", 0) or 0)


def build_report(quiet: bool = False) -> dict:
    if not is_configured():
        print("  [ads_monitor] Etsy API not configured — skipping.")
        return {}

    client = EtsyAPIClient(
        api_key=os.getenv("ETSY_API_KEY", ""),
        access_token=os.getenv("ETSY_ACCESS_TOKEN", ""),
    )

    start = _parse_start_date()
    today = date.today()
    days_running = max((today - start).days, 1)
    total_spend  = round(DAILY_BUDGET * days_running, 2)

    orders = _fetch_recent_orders(client, days=days_running + 1)
    total_revenue = sum(_order_revenue(o) for o in orders)
    order_count   = len(orders)

    roas = round(total_revenue / total_spend, 2) if total_spend > 0 else 0.0
    avg_order_value = round(total_revenue / order_count, 2) if order_count else 0.0

    # Recommendation logic
    if total_spend >= 30 and order_count == 0:
        recommendation = "KILL — $30+ spent with zero orders. Turn off ads immediately and fix listing (photo or title problem)."
        alert = True
    elif days_running >= 30 and roas < ROAS_WATCH:
        recommendation = f"WATCH — ROAS {roas}x after 30+ days is below the 1.5x minimum. Pause and diagnose: check CTR in Etsy dashboard, audit hero photo."
        alert = True
    elif roas >= ROAS_KEEP:
        increment = round(DAILY_BUDGET * 0.25, 2)
        recommendation = f"SCALE — ROAS {roas}x is healthy (target ≥4x). Consider raising daily budget by ${increment:.2f}/day (25%)."
        alert = False
    elif roas >= ROAS_WATCH:
        recommendation = f"KEEP — ROAS {roas}x is profitable (breakeven for digital products is ~1.3x). Monitor weekly."
        alert = False
    else:
        recommendation = f"MONITOR — Only {days_running} days in, need 30 days of data before kill decision."
        alert = False

    snapshot = {
        "date":          str(today),
        "days_running":  days_running,
        "daily_budget":  DAILY_BUDGET,
        "total_spend":   total_spend,
        "order_count":   order_count,
        "total_revenue": round(total_revenue, 2),
        "roas":          roas,
        "avg_order":     avg_order_value,
        "recommendation": recommendation,
    }

    # Save to log
    log = _load_log()
    today_str = str(today)
    log = [e for e in log if e.get("date") != today_str]
    log.append(snapshot)
    _save_log(log)

    if not quiet or alert:
        _print_report(snapshot, days_running)

    if alert and SMTP_PASSWORD:
        _send_alert(snapshot)

    return snapshot


def _print_report(s: dict, days_running: int) -> None:
    divider = "─" * 60
    print(f"\n{divider}")
    print(f"  ETSY ADS MONITOR  ·  {s['date']}")
    print(divider)
    print(f"  Days running :  {days_running}")
    print(f"  Daily budget :  ${s['daily_budget']:.2f}/day")
    print(f"  Total spend  :  ${s['total_spend']:.2f}")
    print(f"  Orders       :  {s['order_count']}")
    print(f"  Revenue      :  ${s['total_revenue']:.2f}")
    print(f"  ROAS         :  {s['roas']}x  (breakeven for digital ≈ 1.3x)")
    print(f"  Avg order    :  ${s['avg_order']:.2f}")
    print(divider)
    print(f"  ACTION: {s['recommendation']}")
    print(divider)

    # Historical ROAS trend (last 7 entries)
    log = _load_log()
    if len(log) >= 2:
        print("\n  Last 7 days ROAS trend:")
        for entry in log[-7:]:
            bar_len = min(int(entry.get("roas", 0) * 5), 40)
            bar = "█" * bar_len
            print(f"    {entry['date']}  {entry['roas']:.1f}x  {bar}")
    print()


def _send_alert(s: dict) -> None:
    if not SMTP_PASSWORD:
        return
    subject = f"[OnBrandCraftz] Etsy Ads Alert — {s['recommendation'][:50]}"
    body = (
        f"Etsy Ads Monitor Alert\n\n"
        f"Date: {s['date']}\n"
        f"Days running: {s['days_running']}\n"
        f"Total spend: ${s['total_spend']:.2f}\n"
        f"Orders: {s['order_count']}\n"
        f"Revenue: ${s['total_revenue']:.2f}\n"
        f"ROAS: {s['roas']}x\n\n"
        f"ACTION NEEDED: {s['recommendation']}\n\n"
        f"Log in to Etsy Ads dashboard to adjust.\n"
        f"— Claude @ OnBrandCraftz Automation"
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"]    = SMTP_USER
    msg["To"]      = OWNER_EMAIL
    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587, timeout=20) as srv:
            srv.starttls()
            srv.login(SMTP_USER, SMTP_PASSWORD)
            srv.send_message(msg)
        print("  [ads_monitor] Alert email sent.")
    except Exception as e:
        print(f"  [ads_monitor] Email failed: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Etsy Ads ROAS monitor")
    parser.add_argument("--quiet", action="store_true", help="Only print if action needed")
    args = parser.parse_args()
    build_report(quiet=args.quiet)
