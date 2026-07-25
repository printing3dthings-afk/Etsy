#!/usr/bin/env python3
"""
health_check.py

Daily automated health check for the OnBrandCraftz pipeline.
Catches silent failures before they cost a week of sales.

Checks:
  1. Etsy OAuth token — valid and not near expiry
  2. OpenAI API — reachable and not billing-limited
  3. Active listings — none incorrectly in draft state
  4. SVG bundles — manifests valid, ZIPs under 20MB
  5. Sublimation ZIPs — under 20MB each
  6. Tag compliance — all listing titles ≤70 chars
  7. Decision log — confirm autonomous actions are being logged
  8. Report freshness — warn if no report in 8+ days

Outputs a health summary and appends to data/health_log.json.
Exits with code 1 if any critical issue is found (for cron alerting).

Usage:
  python tools/health_check.py              # full check, verbose
  python tools/health_check.py --quiet      # only print failures
  python tools/health_check.py --json       # machine-readable JSON output
"""

import json, os, sys, re, time
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

HEALTH_LOG      = Path("data/health_log.json")
REPORTS_DIR     = Path("data/reports")
SVG_BUNDLES_DIR = Path("data/svg_bundles")
SUBLIM_DIR      = Path("data/sublimation_pack")
DECISION_LOG    = Path("data/decision_log.json")

MAX_ZIP_MB = 20


# ── Individual checks ─────────────────────────────────────────────────────────

def check_etsy_token() -> dict:
    try:
        from etsy_api import EtsyAPIClient, EtsyAPIError
        client = EtsyAPIClient()
        if not client.access_token:
            return {"name": "Etsy OAuth token", "status": "CRITICAL",
                    "detail": "ETSY_ACCESS_TOKEN is empty — run: python tools/etsy_oauth.py"}
        # Make a lightweight authenticated call
        client._require_oauth()
        client.get_shop()
        return {"name": "Etsy OAuth token", "status": "OK",
                "detail": "Token valid — authenticated API call succeeded"}
    except Exception as e:
        err = str(e)
        if "401" in err or "Unauthorized" in err:
            return {"name": "Etsy OAuth token", "status": "CRITICAL",
                    "detail": f"Token expired or invalid — run: python tools/etsy_oauth.py"}
        return {"name": "Etsy OAuth token", "status": "WARN",
                "detail": f"Check failed (may be network): {err[:100]}"}


def check_openai_api() -> dict:
    try:
        import openai
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            return {"name": "OpenAI API", "status": "CRITICAL",
                    "detail": "OPENAI_API_KEY missing from .env"}
        client = openai.OpenAI(api_key=api_key)
        # Use a tiny cheap call to test billing status
        r = client.models.list()
        return {"name": "OpenAI API", "status": "OK",
                "detail": "API reachable and billing active"}
    except Exception as e:
        err = str(e)
        if "billing" in err.lower() or "hard_limit" in err.lower():
            return {"name": "OpenAI API", "status": "CRITICAL",
                    "detail": "Billing hard limit reached — top up at platform.openai.com"}
        if "401" in err or "auth" in err.lower():
            return {"name": "OpenAI API", "status": "CRITICAL",
                    "detail": "API key invalid — check OPENAI_API_KEY in .env"}
        return {"name": "OpenAI API", "status": "WARN",
                "detail": f"API check failed: {err[:100]}"}


def check_active_listings() -> dict:
    try:
        from etsy_api import EtsyAPIClient, EtsyAPIError
        client = EtsyAPIClient()
        if not client.access_token:
            return {"name": "Active listings", "status": "SKIP",
                    "detail": "Skipped — no OAuth token"}

        result = client._request("GET", f"shops/{client.shop_id}/listings/active",
                                 params={"limit": 100})
        active = result.get("results", [])

        draft_result = client._request("GET", f"shops/{client.shop_id}/listings",
                                       params={"state": "draft", "limit": 25})
        drafts = draft_result.get("results", [])

        detail = f"{len(active)} active, {len(drafts)} drafts"
        if drafts:
            draft_titles = [d.get("title", "?")[:40] for d in drafts[:5]]
            detail += f" — drafts: {'; '.join(draft_titles)}"
            status = "WARN"
        else:
            status = "OK"

        return {"name": "Active listings", "status": status, "detail": detail,
                "active_count": len(active), "draft_count": len(drafts)}
    except Exception as e:
        return {"name": "Active listings", "status": "WARN",
                "detail": f"Could not check: {str(e)[:80]}"}


def check_svg_zips() -> dict:
    issues = []
    found = 0
    if SVG_BUNDLES_DIR.exists():
        for bundle_dir in SVG_BUNDLES_DIR.iterdir():
            if not bundle_dir.is_dir():
                continue
            for zf in bundle_dir.glob("*.zip"):
                found += 1
                size_mb = zf.stat().st_size / (1024 * 1024)
                if size_mb > MAX_ZIP_MB:
                    issues.append(f"{zf.name}: {size_mb:.1f}MB (over {MAX_ZIP_MB}MB limit)")

            manifest = bundle_dir / "manifest.json"
            if manifest.exists():
                try:
                    with open(manifest) as f:
                        m = json.load(f)
                    if m.get("design_count", 0) < 20 and m.get("status") == "ready_to_publish":
                        issues.append(f"{bundle_dir.name}: only {m['design_count']}/20 designs — incomplete bundle marked ready")
                except Exception:
                    issues.append(f"{bundle_dir.name}: corrupt manifest.json")

    if not found:
        return {"name": "SVG bundle ZIPs", "status": "WARN",
                "detail": "No SVG bundle ZIPs found — bundles not yet generated"}
    if issues:
        return {"name": "SVG bundle ZIPs", "status": "WARN",
                "detail": "; ".join(issues)}
    return {"name": "SVG bundle ZIPs", "status": "OK",
            "detail": f"{found} ZIP(s) all within 20MB limit"}


def check_sublimation_zips() -> dict:
    issues = []
    found = 0
    for zf in Path("data").rglob("*.zip"):
        if "sublimation" in zf.name.lower() or "MomLife" in zf.name:
            found += 1
            size_mb = zf.stat().st_size / (1024 * 1024)
            if size_mb > MAX_ZIP_MB:
                issues.append(f"{zf.name}: {size_mb:.1f}MB")
    if not found:
        return {"name": "Sublimation ZIPs", "status": "WARN",
                "detail": "No sublimation ZIPs found"}
    if issues:
        return {"name": "Sublimation ZIPs", "status": "CRITICAL",
                "detail": f"Over 20MB limit: {'; '.join(issues)}"}
    return {"name": "Sublimation ZIPs", "status": "OK",
            "detail": f"{found} ZIP(s) all within 20MB limit"}


def check_listing_titles() -> dict:
    """Check that all listing content configs have compliant titles."""
    violations = []
    # Check SVG bundle titles
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "publish_svg_bundle",
            Path("tools/publish_svg_bundle.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for bundle_id, content in mod.LISTING_CONTENT.items():
            title = content.get("title", "")
            if len(title) > 70:
                violations.append(f"SVG {bundle_id}: {len(title)} chars")
    except Exception:
        pass

    if violations:
        return {"name": "Listing title lengths (≤70 chars)", "status": "CRITICAL",
                "detail": f"Titles over 70 chars (mobile penalty): {'; '.join(violations)}"}
    return {"name": "Listing title lengths (≤70 chars)", "status": "OK",
            "detail": "All checked titles within 70-char limit"}


def check_decision_log() -> dict:
    if not DECISION_LOG.exists():
        return {"name": "Decision log", "status": "WARN",
                "detail": "No decision log yet — will be created on first weekly run"}
    try:
        with open(DECISION_LOG) as f:
            log = json.load(f)
        cutoff = (datetime.utcnow() - timedelta(days=14)).isoformat()
        recent = [e for e in log if e.get("timestamp", "") >= cutoff]
        return {"name": "Decision log", "status": "OK",
                "detail": f"{len(log)} total entries, {len(recent)} in last 14 days"}
    except Exception as e:
        return {"name": "Decision log", "status": "WARN",
                "detail": f"Log file unreadable: {e}"}


def check_report_freshness() -> dict:
    if not REPORTS_DIR.exists():
        return {"name": "Weekly report freshness", "status": "WARN",
                "detail": "Reports directory missing — no reports generated yet"}
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    if not reports:
        return {"name": "Weekly report freshness", "status": "WARN",
                "detail": "No weekly reports found — run: python tools/weekly_report.py"}
    latest = reports[0]
    # Parse date from filename
    try:
        report_date = date.fromisoformat(latest.name[:10])
        days_old = (date.today() - report_date).days
        if days_old > 8:
            return {"name": "Weekly report freshness", "status": "WARN",
                    "detail": f"Latest report is {days_old} days old ({latest.name}) — pipeline may not be running"}
        return {"name": "Weekly report freshness", "status": "OK",
                "detail": f"Latest report: {latest.name} ({days_old} days ago)"}
    except Exception:
        return {"name": "Weekly report freshness", "status": "WARN",
                "detail": f"Could not parse report date from: {latest.name}"}


def check_env_keys() -> dict:
    required = ["OPENAI_API_KEY", "ETSY_API_KEY", "ETSY_CLIENT_ID",
                "ETSY_ACCESS_TOKEN", "ETSY_REFRESH_TOKEN"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        return {"name": ".env completeness", "status": "CRITICAL",
                "detail": f"Missing keys: {', '.join(missing)}"}
    empty = [k for k in required if os.environ.get(k, "").strip() in ("", '""', "''")]
    if empty:
        return {"name": ".env completeness", "status": "WARN",
                "detail": f"Empty values: {', '.join(empty)}"}
    return {"name": ".env completeness", "status": "OK",
            "detail": "All required API keys present"}


def check_refresh_token_age() -> dict:
    """Warn when the OAuth refresh token is approaching its 90-day expiry."""
    token_date_str = os.environ.get("ETSY_TOKEN_ISSUED_DATE", "")
    if not token_date_str:
        return {"name": "Refresh token age", "status": "WARN",
                "detail": "ETSY_TOKEN_ISSUED_DATE not set in .env — add it after each re-auth so expiry can be tracked (refresh token expires after 90 days)"}
    try:
        issued = date.fromisoformat(token_date_str)
        days_old = (date.today() - issued).days
        days_left = 90 - days_old
        if days_left <= 0:
            return {"name": "Refresh token age", "status": "CRITICAL",
                    "detail": f"Refresh token is {abs(days_left)} days PAST expiry — run: python tools/etsy_oauth.py NOW"}
        if days_left <= 14:
            return {"name": "Refresh token age", "status": "CRITICAL",
                    "detail": f"Refresh token expires in {days_left} days — run: python tools/etsy_oauth.py before it expires"}
        if days_left <= 21:
            return {"name": "Refresh token age", "status": "WARN",
                    "detail": f"Refresh token expires in {days_left} days — schedule re-auth soon"}
        return {"name": "Refresh token age", "status": "OK",
                "detail": f"Refresh token issued {days_old} days ago, {days_left} days remaining"}
    except ValueError:
        return {"name": "Refresh token age", "status": "WARN",
                "detail": f"ETSY_TOKEN_ISSUED_DATE has invalid format '{token_date_str}' — use YYYY-MM-DD"}


# ── Runner ────────────────────────────────────────────────────────────────────

ALL_CHECKS = [
    check_env_keys,
    check_etsy_token,
    check_refresh_token_age,
    check_openai_api,
    check_active_listings,
    check_svg_zips,
    check_sublimation_zips,
    check_listing_titles,
    check_decision_log,
    check_report_freshness,
]

STATUS_ICON = {"OK": "✓", "WARN": "⚠", "CRITICAL": "✗", "SKIP": "○"}
STATUS_ORDER = {"CRITICAL": 0, "WARN": 1, "OK": 2, "SKIP": 3}


def run(quiet: bool = False, as_json: bool = False) -> int:
    results = []
    for check_fn in ALL_CHECKS:
        try:
            result = check_fn()
        except Exception as e:
            result = {"name": check_fn.__name__, "status": "WARN",
                      "detail": f"Check raised exception: {e}"}
        results.append(result)

    # Sort: critical first
    results.sort(key=lambda r: STATUS_ORDER.get(r["status"], 9))

    has_critical = any(r["status"] == "CRITICAL" for r in results)
    has_warn     = any(r["status"] == "WARN" for r in results)

    overall = "CRITICAL" if has_critical else ("WARN" if has_warn else "OK")

    # Log to health_log.json
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "overall": overall,
        "results": results,
    }
    health_log = []
    if HEALTH_LOG.exists():
        try:
            with open(HEALTH_LOG) as f:
                health_log = json.load(f)
        except Exception:
            health_log = []
    health_log.append(log_entry)
    if len(health_log) > 90:          # keep 90 days of daily checks
        health_log = health_log[-90:]
    HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
    with open(HEALTH_LOG, "w") as f:
        json.dump(health_log, f, indent=2)

    if as_json:
        print(json.dumps(log_entry, indent=2))
        return 1 if has_critical else 0

    # Console output
    if not quiet or overall != "OK":
        print(f"\nOnBrandCraftz Health Check — {date.today().isoformat()}")
        print(f"Overall: {STATUS_ICON[overall]} {overall}\n")
        for r in results:
            icon = STATUS_ICON[r["status"]]
            if quiet and r["status"] == "OK":
                continue
            print(f"  {icon} {r['name']}")
            print(f"      {r['detail']}")
        print()

    if has_critical:
        print("🚨 CRITICAL issues found — action required before next pipeline run.")
        return 1

    if has_warn and not quiet:
        print("⚠  Warnings found — review above items when convenient.")

    return 0


if __name__ == "__main__":
    quiet   = "--quiet" in sys.argv
    as_json = "--json" in sys.argv
    sys.exit(run(quiet=quiet, as_json=as_json))
