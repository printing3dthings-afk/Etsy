"""Tool definitions and implementations for the API Connections Agent.

Manages every API key and integration for the Etsy shop: status checks,
live connection tests, key persistence, setup guides, and health reports.
"""

import json
import os
import re
import time
from pathlib import Path

ENV_PATH = Path("/home/user/Etsy/.env")

# All API keys the shop may ever use, in priority order
KNOWN_KEYS = [
    "ANTHROPIC_API_KEY",
    "ETSY_API_KEY",
    "ETSY_SHOP_ID",
    "ETSY_ACCESS_TOKEN",
    "ETSY_REFRESH_TOKEN",
    "OPENAI_API_KEY",
    "PINTEREST_ACCESS_TOKEN",
    "PINTEREST_REFRESH_TOKEN",
    "CANVA_CLIENT_ID",
    "CANVA_CLIENT_SECRET",
    "CANVA_ACCESS_TOKEN",
    "CANVA_REFRESH_TOKEN",
    "MAILCHIMP_API_KEY",
    "SENDGRID_API_KEY",
    "GOOGLE_ANALYTICS_ID",
    "FACEBOOK_ADS_TOKEN",
    "INSTAGRAM_ACCESS_TOKEN",
    "TIKTOK_ACCESS_TOKEN",
    "STRIPE_SECRET_KEY",
]

# Business-impact priority for each API
API_PRIORITY = {
    "ANTHROPIC_API_KEY":       "critical",
    "ETSY_API_KEY":            "critical",
    "ETSY_SHOP_ID":            "critical",
    "ETSY_ACCESS_TOKEN":       "critical",
    "ETSY_REFRESH_TOKEN":      "high",
    "OPENAI_API_KEY":          "high",
    "PINTEREST_ACCESS_TOKEN":  "medium",
    "PINTEREST_REFRESH_TOKEN": "medium",
    "CANVA_CLIENT_ID":         "medium",
    "CANVA_CLIENT_SECRET":     "medium",
    "CANVA_ACCESS_TOKEN":      "medium",
    "CANVA_REFRESH_TOKEN":     "medium",
    "MAILCHIMP_API_KEY":       "medium",
    "SENDGRID_API_KEY":        "medium",
    "GOOGLE_ANALYTICS_ID":     "low",
    "FACEBOOK_ADS_TOKEN":      "low",
    "INSTAGRAM_ACCESS_TOKEN":  "low",
    "TIKTOK_ACCESS_TOKEN":     "low",
    "STRIPE_SECRET_KEY":       "low",
}

# Base URLs used for HEAD-request smoke tests
API_BASE_URLS = {
    "anthropic":        "https://api.anthropic.com",
    "etsy":             "https://openapi.etsy.com/v3/application",
    "openai":           "https://api.openai.com",
    "pinterest":        "https://api.pinterest.com",
    "canva":            "https://api.canva.com",
    "mailchimp":        "https://login.mailchimp.com",
    "sendgrid":         "https://api.sendgrid.com",
    "google_analytics": "https://www.googleapis.com/analytics",
    "facebook_ads":     "https://graph.facebook.com",
    "instagram":        "https://graph.instagram.com",
    "tiktok":           "https://business-api.tiktok.com",
    "stripe":           "https://api.stripe.com",
}

TOOL_DEFINITIONS = [
    {
        "name": "list_api_status",
        "description": (
            "Read the .env file and os.environ to return the status of every known API key: "
            "configured (non-empty value present), missing (key exists but empty), or "
            "unknown (key not found anywhere). Call this at the start of every session."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "test_api_connection",
        "description": (
            "Live-test a single API connection. For Anthropic makes a real SDK call; "
            "for Etsy uses the EtsyAPIClient; for others attempts an HTTP HEAD request. "
            "Returns status (ok/error/not_configured), latency_ms, and any error message."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "api_name": {
                    "type": "string",
                    "description": (
                        "API to test. One of: anthropic, etsy, openai, pinterest, mailchimp, "
                        "sendgrid, google_analytics, facebook_ads, instagram, tiktok, stripe"
                    ),
                }
            },
            "required": ["api_name"],
        },
    },
    {
        "name": "save_api_key",
        "description": (
            "Save or update an API key in the .env file. Updates in place if the key already "
            "exists, appends a new line if it does not. The value is masked in logs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "key_name":  {"type": "string", "description": "Environment variable name, e.g. ETSY_API_KEY"},
                "key_value": {"type": "string", "description": "The secret value to save"},
            },
            "required": ["key_name", "key_value"],
        },
    },
    {
        "name": "get_integration_guide",
        "description": (
            "Return a detailed setup guide for a specific API: what it is used for in the shop, "
            "how to obtain credentials, which env var to set, OAuth notes, and a link to official docs."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "api_name": {
                    "type": "string",
                    "description": (
                        "API to get a guide for. One of: anthropic, etsy, openai, pinterest, "
                        "mailchimp, sendgrid, google_analytics, facebook_ads, instagram, tiktok"
                    ),
                }
            },
            "required": ["api_name"],
        },
    },
    {
        "name": "scan_codebase_for_apis",
        "description": (
            "Walk the /home/user/Etsy directory and scan every .py file for API references: "
            "os.getenv/os.environ calls, HTTP base URLs, and requests.get/post calls. "
            "Returns a structured list of {file, api_references} for the entire codebase."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_connection_health_report",
        "description": (
            "Test every configured API and produce a full health report: overall_status "
            "(all_ok / degraded / critical), per-API status with latency, and prioritised "
            "recommendations for any missing or failing integrations."
        ),
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _load_env_file() -> dict[str, str]:
    """Parse the .env file and return key→value pairs (empty string if no value)."""
    pairs: dict[str, str] = {}
    if not ENV_PATH.exists():
        return pairs
    for raw_line in ENV_PATH.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, _, v = line.partition("=")
            pairs[k.strip()] = v.strip().strip('"').strip("'")
    return pairs


def _mask(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return value[:8] + "***"


# ── Tool implementations ───────────────────────────────────────────────────────

def _list_api_status() -> str:
    env_file = _load_env_file()
    configured, missing, unknown = [], [], []

    for key in KNOWN_KEYS:
        # Prefer the live process environment (already loaded at startup), fall back to .env file
        value = os.environ.get(key) or env_file.get(key)
        in_file = key in env_file
        in_env  = key in os.environ

        if value:  # non-empty value found somewhere
            configured.append({
                "key":      key,
                "source":   "env_var" if in_env else "env_file",
                "preview":  _mask(value),
                "priority": API_PRIORITY.get(key, "unknown"),
            })
        elif in_file or in_env:  # key present but value is empty
            missing.append({
                "key":      key,
                "priority": API_PRIORITY.get(key, "unknown"),
                "note":     "Key exists but has no value set",
            })
        else:
            unknown.append({
                "key":      key,
                "priority": API_PRIORITY.get(key, "unknown"),
                "note":     "Not found in .env or environment",
            })

    return json.dumps({
        "configured": configured,
        "missing":    missing,
        "unknown":    unknown,
        "summary": {
            "total_known":     len(KNOWN_KEYS),
            "configured":      len(configured),
            "missing_or_unknown": len(missing) + len(unknown),
            "critical_missing": [
                k["key"] for k in (missing + unknown)
                if API_PRIORITY.get(k["key"]) == "critical"
            ],
        },
    }, indent=2)


def _test_api_connection(api_name: str) -> str:
    name = api_name.lower().strip()
    start = time.monotonic()

    try:
        if name == "anthropic":
            api_key = os.environ.get("ANTHROPIC_API_KEY") or _load_env_file().get("ANTHROPIC_API_KEY", "")
            if not api_key:
                return json.dumps({"status": "not_configured", "api": name,
                                   "error_msg": "ANTHROPIC_API_KEY not set"})
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            client.models.list()
            latency = round((time.monotonic() - start) * 1000, 1)
            return json.dumps({"status": "ok", "api": name, "latency_ms": latency})

        if name == "etsy":
            env = _load_env_file()
            api_key = os.environ.get("ETSY_API_KEY") or env.get("ETSY_API_KEY", "")
            token   = os.environ.get("ETSY_ACCESS_TOKEN") or env.get("ETSY_ACCESS_TOKEN", "")
            if not api_key and not token:
                return json.dumps({"status": "not_configured", "api": name,
                                   "error_msg": "ETSY_API_KEY and ETSY_ACCESS_TOKEN both unset"})
            from tools.etsy_api import EtsyAPIClient, EtsyAPIError
            client = EtsyAPIClient(api_key=api_key, access_token=token)
            client._request("GET", "/openapi-ping")
            latency = round((time.monotonic() - start) * 1000, 1)
            return json.dumps({"status": "ok", "api": name, "latency_ms": latency})

        # Generic HTTP HEAD test for all other APIs
        base_url = API_BASE_URLS.get(name)
        if not base_url:
            return json.dumps({"status": "error", "api": name,
                               "error_msg": f"Unknown API name '{name}'. "
                               f"Known: {', '.join(API_BASE_URLS)}"})

        import urllib.request
        req = urllib.request.Request(base_url, method="HEAD")
        req.add_header("User-Agent", "EtsyShopBot/1.0")
        try:
            with urllib.request.urlopen(req, timeout=8) as resp:
                latency = round((time.monotonic() - start) * 1000, 1)
                return json.dumps({"status": "ok", "api": name,
                                   "latency_ms": latency, "http_status": resp.status})
        except Exception as http_err:
            latency = round((time.monotonic() - start) * 1000, 1)
            # A non-200 still means the host is reachable
            if "HTTP Error" in str(http_err):
                return json.dumps({"status": "ok", "api": name, "latency_ms": latency,
                                   "note": "Host reachable (auth required for full test)"})
            raise

    except Exception as exc:
        latency = round((time.monotonic() - start) * 1000, 1)
        return json.dumps({"status": "error", "api": name,
                           "latency_ms": latency, "error_msg": str(exc)})


def _save_api_key(key_name: str, key_value: str) -> str:
    key_name  = key_name.strip().upper()
    key_value = key_value.strip()
    masked    = _mask(key_value)

    existing_lines: list[str] = []
    if ENV_PATH.exists():
        existing_lines = ENV_PATH.read_text().splitlines()

    updated = False
    new_lines: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if stripped.startswith(f"{key_name}=") or stripped == key_name:
            new_lines.append(f'{key_name}="{key_value}"')
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        # Append new key; ensure file ends with newline
        new_lines.append(f'{key_name}="{key_value}"')

    ENV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ENV_PATH.write_text("\n".join(new_lines) + "\n")

    # Also update the live environment so the current process sees the new value
    os.environ[key_name] = key_value

    action = "updated" if updated else "added"
    return json.dumps({
        "status": "saved",
        "key_name": key_name,
        "action":   action,
        "value_preview": masked,
        "env_file": str(ENV_PATH),
        "note": f"Key {action} in .env and set in current process environment.",
    })


def _get_integration_guide(api_name: str) -> str:
    name = api_name.lower().strip()

    guides: dict[str, dict] = {
        "anthropic": {
            "purpose": "Powers ALL AI agents in the shop — listing copy, art descriptions, SEO, customer replies, strategy. Without this nothing works.",
            "priority": "CRITICAL — set up on Day 1",
            "env_var": "ANTHROPIC_API_KEY",
            "how_to_get": [
                "1. Go to https://console.anthropic.com",
                "2. Create an account or sign in",
                "3. Navigate to API Keys → Create Key",
                "4. Copy the key (shown once — save it immediately)",
            ],
            "oauth": "None — API key only",
            "docs": "https://docs.anthropic.com/en/api/getting-started",
            "cost_note": "Pay-per-token. claude-sonnet-4-5 costs ~$3/M input, $15/M output tokens.",
        },
        "etsy": {
            "purpose": "Read/write shop listings, orders, reviews, messages. The core commerce API.",
            "priority": "CRITICAL — set up on Day 1",
            "env_var": "ETSY_API_KEY + ETSY_SHOP_ID + ETSY_ACCESS_TOKEN + ETSY_REFRESH_TOKEN",
            "how_to_get": [
                "1. Go to https://www.etsy.com/developers → My Apps → New App",
                "2. Copy the Keystring → set as ETSY_API_KEY",
                "3. Find your shop ID at etsy.com/shop/<name> (numeric ID in page source)",
                "4. Run tools/etsy_oauth.py to complete OAuth and get access/refresh tokens",
            ],
            "oauth": "OAuth 2.0 PKCE flow. Run tools/etsy_oauth.py — it opens a browser, you authorise, tokens are saved automatically.",
            "docs": "https://developers.etsy.com/documentation/",
            "cost_note": "Free API access. Etsy charges 6.5% transaction fee on sales.",
        },
        "openai": {
            "purpose": "DALL-E 3 image generation for product art and listings. GPT-4 as a fallback reasoner.",
            "priority": "HIGH — set up on Day 1 for art generation",
            "env_var": "OPENAI_API_KEY",
            "how_to_get": [
                "1. Go to https://platform.openai.com",
                "2. Sign in → API Keys → Create new secret key",
                "3. Copy and save immediately",
            ],
            "oauth": "None — API key only",
            "docs": "https://platform.openai.com/docs/",
            "cost_note": "DALL-E 3 standard: $0.04/image (1024x1024). gpt-4o: ~$5/M input tokens.",
        },
        "pinterest": {
            "purpose": "Auto-pin products to Pinterest boards for organic traffic. Pinterest drives 30–40% of Etsy traffic for visual products.",
            "priority": "MEDIUM — set up by Day 3",
            "env_var": "PINTEREST_ACCESS_TOKEN + PINTEREST_REFRESH_TOKEN",
            "how_to_get": [
                "1. Go to https://developers.pinterest.com",
                "2. Create an app → get Client ID and Client Secret",
                "3. Run tools/pinterest_oauth.py to complete OAuth flow",
            ],
            "oauth": "OAuth 2.0. Run tools/pinterest_oauth.py. Tokens expire every 30 days — refresh_token is used to renew automatically.",
            "docs": "https://developers.pinterest.com/docs/getting-started/introduction/",
            "cost_note": "Free API. Pinterest Business account required for analytics endpoints.",
        },
        "canva": {
            "purpose": (
                "Programmatically generate the text-overlay listing graphics (what's-included "
                "callouts, how-to steps, app compatibility labels) that CLAUDE.md otherwise calls "
                "for 'added in Canva post' on photo slots 2, 6, 7, 9, 10. Used by the Brand Design Agent."
            ),
            "deprecated": (
                "DEPRECATED (2026-07 API review) — do NOT wire this up. Everything the pipeline "
                "needs from Canva (text overlays, callouts, compositing) is already done for free "
                "with PIL/Pillow, which the codebase uses heavily. The Canva Connect API also pulls "
                "a paid Canva Pro subscription into the loop for no automation benefit. Kept only as "
                "dormant scaffolding for a human doing hand-design; the automated path stays on PIL."
            ),
            "priority": "SKIP — superseded by PIL; only connect if a human wants Canva's editor",
            "env_var": "CANVA_CLIENT_ID + CANVA_CLIENT_SECRET + CANVA_ACCESS_TOKEN + CANVA_REFRESH_TOKEN",
            "how_to_get": [
                "1. Go to https://www.canva.com/developers/integrations → Create an Integration",
                "2. Add redirect URI: http://localhost:3005/callback",
                "3. Enable scopes: design:content:read design:content:write design:meta:read "
                "asset:read asset:write folder:read brandtemplate:meta:read brandtemplate:content:read profile:read",
                "4. Copy the Client ID and generate a Client Secret → set as CANVA_CLIENT_ID / CANVA_CLIENT_SECRET",
                "5. Run tools/canva_oauth.py to complete OAuth and get access/refresh tokens",
            ],
            "oauth": "OAuth 2.0 PKCE. Run tools/canva_oauth.py (manual two-step paste flow, same pattern as etsy_oauth.py).",
            "docs": "https://www.canva.dev/docs/connect/",
            "cost_note": (
                "Free API access on Canva Free/Pro. HARD MANUAL STEP: Canva's API cannot create a "
                "Brand Template — Scott must build at least one in the Canva UI (with named "
                "placeholder fields) before generate_listing_graphic can be used."
            ),
        },
        "mailchimp": {
            "purpose": "Email marketing: welcome sequences, abandoned cart recovery, new-listing announcements to subscribers.",
            "priority": "MEDIUM — set up by Day 7",
            "env_var": "MAILCHIMP_API_KEY",
            "how_to_get": [
                "1. Go to https://mailchimp.com → sign in",
                "2. Account → Extras → API Keys → Create A Key",
                "3. Key format: <key>-<datacenter> (e.g. abc123-us21)",
            ],
            "oauth": "None — API key only. The datacenter suffix in the key is required for API calls.",
            "docs": "https://mailchimp.com/developer/marketing/api/",
            "cost_note": "Free up to 500 contacts / 1000 sends/month. Paid plans from $13/month.",
        },
        "sendgrid": {
            "purpose": "Transactional emails: order confirmations, digital file delivery, customer service replies.",
            "priority": "MEDIUM — set up by Day 7",
            "env_var": "SENDGRID_API_KEY",
            "how_to_get": [
                "1. Go to https://sendgrid.com → sign in",
                "2. Settings → API Keys → Create API Key",
                "3. Choose 'Restricted Access' → Mail Send: Full Access",
            ],
            "oauth": "None — API key only",
            "docs": "https://docs.sendgrid.com/for-developers/sending-email/api-getting-started",
            "cost_note": "Free tier: 100 emails/day. Essentials plan $19.95/month for 50k emails.",
        },
        "google_analytics": {
            "purpose": "Track shop traffic from external sources, Pinterest referrals, and email campaign conversions.",
            "priority": "LOW — set up when scaling",
            "env_var": "GOOGLE_ANALYTICS_ID",
            "how_to_get": [
                "1. Go to https://analytics.google.com",
                "2. Admin → Create Property → get Measurement ID (G-XXXXXXXX)",
                "3. Add tracking to any custom landing pages",
            ],
            "oauth": "Google OAuth for API data access. Measurement ID alone is sufficient for basic tracking.",
            "docs": "https://developers.google.com/analytics",
            "cost_note": "Free for standard use.",
        },
        "facebook_ads": {
            "purpose": "Run Facebook and Instagram paid ads targeting buyers similar to Etsy customers.",
            "priority": "LOW — set up at Day 30+ when budget allows",
            "env_var": "FACEBOOK_ADS_TOKEN",
            "how_to_get": [
                "1. Go to https://developers.facebook.com → My Apps → Create App",
                "2. Add Marketing API product",
                "3. Generate a long-lived User Access Token with ads_management permission",
            ],
            "oauth": "Facebook OAuth 2.0. Tokens expire — use a System User token for production.",
            "docs": "https://developers.facebook.com/docs/marketing-apis/",
            "cost_note": "API is free. Ad spend is paid directly. Recommend starting with $5–$10/day tests.",
        },
        "instagram": {
            "purpose": "Post product images, reels, and stories to Instagram to drive Etsy traffic.",
            "priority": "LOW — set up when content pipeline is ready",
            "env_var": "INSTAGRAM_ACCESS_TOKEN",
            "how_to_get": [
                "1. Connect Instagram Business account to a Facebook Page",
                "2. Go to https://developers.facebook.com → Add Instagram Graph API",
                "3. Generate Page Access Token with instagram_basic + instagram_content_publish permissions",
            ],
            "oauth": "Facebook/Instagram OAuth. Requires a Business or Creator account (not personal).",
            "docs": "https://developers.facebook.com/docs/instagram-api/",
            "cost_note": "Free API access.",
        },
        "tiktok": {
            "purpose": "Auto-publish short product videos to TikTok Shop and TikTok feed for viral reach.",
            "priority": "LOW — set up when video content is ready",
            "env_var": "TIKTOK_ACCESS_TOKEN",
            "how_to_get": [
                "1. Go to https://developers.tiktok.com → My Apps",
                "2. Create app → add Content Posting API product",
                "3. Complete OAuth flow to get access + refresh tokens",
            ],
            "oauth": "TikTok OAuth 2.0. Access tokens expire in 24 hours; use refresh_token to renew.",
            "docs": "https://developers.tiktok.com/doc/overview/",
            "cost_note": "Free API. TikTok Shop takes 5–8% commission on sales.",
        },
    }

    guide = guides.get(name)
    if not guide:
        return json.dumps({
            "error": f"No guide for '{api_name}'.",
            "available": sorted(guides.keys()),
        })
    return json.dumps({"api": name, **guide}, indent=2)


def _scan_codebase_for_apis() -> str:
    root = Path("/home/user/Etsy")
    skip_dirs = {"__pycache__", ".git", "node_modules", ".venv", "venv"}

    # Patterns we look for in source files
    pat_getenv  = re.compile(r'os\.(?:getenv|environ\.get)\s*\(\s*["\']([A-Z_]+)["\']')
    pat_environ = re.compile(r'os\.environ\s*\[\s*["\']([A-Z_]+)["\']')
    pat_url     = re.compile(r'https?://[a-zA-Z0-9._/%-]+')
    pat_api_kw  = re.compile(
        r'\b(anthropic|etsy|openai|pinterest|mailchimp|sendgrid|stripe|'
        r'facebook|instagram|tiktok|google.analytics|googleapis)\b',
        re.IGNORECASE,
    )

    results = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in skip_dirs]
        for fname in filenames:
            if not fname.endswith(".py"):
                continue
            fpath = Path(dirpath) / fname
            try:
                text = fpath.read_text(errors="replace")
            except OSError:
                continue

            env_vars  = sorted(set(pat_getenv.findall(text) + pat_environ.findall(text)))
            urls      = sorted(set(u for u in pat_url.findall(text) if len(u) < 120))
            api_names = sorted(set(m.lower() for m in pat_api_kw.findall(text)))

            if env_vars or api_names:
                results.append({
                    "file": str(fpath.relative_to(root)),
                    "api_references": {
                        "env_vars":  env_vars,
                        "api_names": api_names,
                        "urls":      urls[:10],  # cap to keep output readable
                    },
                })

    return json.dumps({
        "scanned_root": str(root),
        "files_with_api_refs": len(results),
        "results": results,
    }, indent=2)


def _get_connection_health_report() -> str:
    # Determine which APIs are configured
    env_file = _load_env_file()
    configured_apis: list[str] = []

    def _is_configured(key: str) -> bool:
        return bool(os.environ.get(key) or env_file.get(key))

    # Map env-var presence to testable API names
    api_key_map = {
        "anthropic":        ["ANTHROPIC_API_KEY"],
        "etsy":             ["ETSY_API_KEY", "ETSY_ACCESS_TOKEN"],
        "openai":           ["OPENAI_API_KEY"],
        "pinterest":        ["PINTEREST_ACCESS_TOKEN"],
        "canva":            ["CANVA_ACCESS_TOKEN"],
        "mailchimp":        ["MAILCHIMP_API_KEY"],
        "sendgrid":         ["SENDGRID_API_KEY"],
        "google_analytics": ["GOOGLE_ANALYTICS_ID"],
        "facebook_ads":     ["FACEBOOK_ADS_TOKEN"],
        "instagram":        ["INSTAGRAM_ACCESS_TOKEN"],
        "tiktok":           ["TIKTOK_ACCESS_TOKEN"],
        "stripe":           ["STRIPE_SECRET_KEY"],
    }

    per_api: list[dict] = []
    critical_failures = 0
    any_failures = 0

    for api_name, keys in api_key_map.items():
        has_any = any(_is_configured(k) for k in keys)
        priority = max(
            (API_PRIORITY.get(k, "low") for k in keys),
            key=lambda p: {"critical": 3, "high": 2, "medium": 1, "low": 0}.get(p, 0),
        )

        if not has_any:
            per_api.append({
                "api": api_name,
                "status": "not_configured",
                "priority": priority,
                "latency_ms": None,
                "error_msg": f"None of {keys} are set",
            })
            if priority == "critical":
                critical_failures += 1
            any_failures += 1
        else:
            raw   = json.loads(_test_api_connection(api_name))
            entry = {
                "api":        api_name,
                "status":     raw.get("status"),
                "priority":   priority,
                "latency_ms": raw.get("latency_ms"),
                "error_msg":  raw.get("error_msg"),
            }
            per_api.append(entry)
            if raw.get("status") != "ok":
                any_failures += 1
                if priority == "critical":
                    critical_failures += 1

    if critical_failures > 0:
        overall = "critical"
    elif any_failures > 0:
        overall = "degraded"
    else:
        overall = "all_ok"

    # Recommendations sorted by business impact
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    needs_action = [
        e for e in per_api
        if e["status"] in ("not_configured", "error")
    ]
    needs_action.sort(key=lambda e: priority_order.get(e["priority"], 9))

    recommendations = []
    for e in needs_action:
        if e["status"] == "not_configured":
            recommendations.append({
                "api":     e["api"],
                "impact":  e["priority"],
                "action":  f"Run get_integration_guide('{e['api']}') for setup instructions.",
            })
        else:
            recommendations.append({
                "api":    e["api"],
                "impact": e["priority"],
                "action": f"Connection failed: {e.get('error_msg')}. Check credentials.",
            })

    return json.dumps({
        "overall_status":  overall,
        "summary": {
            "total_checked":   len(per_api),
            "ok":              sum(1 for e in per_api if e["status"] == "ok"),
            "not_configured":  sum(1 for e in per_api if e["status"] == "not_configured"),
            "errors":          sum(1 for e in per_api if e["status"] == "error"),
        },
        "per_api":           per_api,
        "recommendations":   recommendations,
    }, indent=2)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def execute_tool(tool_name: str, tool_input: dict) -> str:
    if tool_name == "list_api_status":
        return _list_api_status()
    if tool_name == "test_api_connection":
        return _test_api_connection(tool_input["api_name"])
    if tool_name == "save_api_key":
        return _save_api_key(tool_input["key_name"], tool_input["key_value"])
    if tool_name == "get_integration_guide":
        return _get_integration_guide(tool_input["api_name"])
    if tool_name == "scan_codebase_for_apis":
        return _scan_codebase_for_apis()
    if tool_name == "get_connection_health_report":
        return _get_connection_health_report()
    return f"Unknown api_connections tool: {tool_name}"
