#!/usr/bin/env python3
"""
OnBrandCraftz — Command Center
Local or cloud web app — click buttons to run any shop automation script.
Live output streams back to the browser in real time.

Local:  python command_center.py  →  http://localhost:5055
Cloud:  deployed to Railway       →  https://your-app.up.railway.app
"""

import subprocess
import os
import json
import io
import secrets
import shlex
from flask import Flask, Response, request, render_template_string, session, redirect, jsonify

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Cloud / Railway detection ──────────────────────────────────────────────────
IS_CLOUD = bool(
    os.environ.get("RAILWAY_PROJECT_ID") or
    os.environ.get("RAILWAY_ENVIRONMENT") or
    os.environ.get("RAILWAY_SERVICE_ID")
)
PORT = int(os.environ.get("PORT", 5055))

# On Railway: write env vars to .env so all tool scripts can read them
if IS_CLOUD:
    _ENV_KEYS = [
        "ANTHROPIC_API_KEY", "OPENAI_API_KEY",
        "ETSY_API_KEY", "ETSY_CLIENT_ID", "ETSY_CLIENT_SECRET",
        "ETSY_ACCESS_TOKEN", "ETSY_REFRESH_TOKEN",
        "SMTP_USER", "SMTP_PASSWORD",
        "PINTEREST_ACCESS_TOKEN", "PINTEREST_CLIENT_ID", "PINTEREST_CLIENT_SECRET",
        "TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_ACCESS_TOKEN",
        "MAILCHIMP_SIGNUP_URL", "LEAD_MAGNET_URL",
    ]
    _env_path = os.path.join(BASE_DIR, ".env")
    with open(_env_path, "w") as _f:
        for _k in _ENV_KEYS:
            _v = os.environ.get(_k, "")
            _f.write(f'{_k}="{_v}"\n')

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", os.urandom(24).hex())
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

CENTER_PASSWORD = os.environ.get("CENTER_PASSWORD", "")
OWNER_NAME = os.environ.get("OWNER_NAME", "Scott")


def get_csrf_token():
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_hex(16)
    return session["csrf_token"]


# ── Command registry ──────────────────────────────────────────────────────────
# local_only=True  →  button disabled in cloud mode (needs local files/browser)
# local_only=False →  works in cloud (API calls, JSON reads, image generation)

COMMANDS = [
    # ── SHOP HEALTH & ANALYTICS ──────────────────────────────────────────────
    {
        "category": "Shop Health & Analytics",
        "color": "#4CAF50",
        "icon": "📊",
        "commands": [
            {
                "id": "health_check",
                "label": "Run Shop Health Check",
                "cmd": "python3 tools/shop_health_check.py",
                "desc": "Full snapshot of all listings — views, conversion rate, favorites, pricing, tag audits. Run weekly.",
            },
            {
                "id": "analytics",
                "label": "View Analytics Dashboard",
                "cmd": "python3 tools/analytics_tracker.py",
                "desc": "Pulls live shop stats from Etsy, stores snapshots, shows revenue trends and action items.",
            },
            {
                "id": "audit_tags",
                "label": "Audit & Fix All Tags",
                "cmd": "python3 tools/audit_fix_wall_art_tags.py",
                "desc": "Scans all active wall art listings for tag violations (>20 chars, <13 tags, duplicates) and fixes them.",
            },
            {
                "id": "seo_audit",
                "label": "SEO Title Audit",
                "cmd": "./venv/bin/python3 tools/seo_title_optimizer.py --fix",
                "desc": "Grades every listing title (A–F) against 2026 Etsy SEO rules and suggests buyer-intent rewrites.",
            },
            {
                "id": "seasonal_keywords",
                "label": "Seasonal Keywords Calendar",
                "cmd": "./venv/bin/python3 tools/seasonal_keywords.py --weeks 20",
                "desc": "Shows upcoming seasonal peaks, overdue keyword updates, and which listings need tag changes now.",
            },
        ]
    },
    # ── 3D PRINTING & CAD AUTOMATION ──────────────────────────────────────────
    {
        "category": "3D Printing & CAD",
        "color": "#FF9800",
        "icon": "🖨️",
        "commands": [
            {
                "id": "generate_3d_keychain",
                "label": "Generate 3D Custom STL",
                "cmd": "./venv/bin/python3 tools/3d_cad_generator.py 'OnBrandCraftz'",
                "desc": "Programmatically generates custom 3D printable SCAD/STL models for personalized Etsy orders.",
            },
        ]
    },
    # ── ART PRODUCTION ───────────────────────────────────────────────────────
    {
        "category": "Art Production",
        "color": "#9C27B0",
        "icon": "🎨",
        "commands": [
            {
                "id": "post_art_status",
                "label": "Art Schedule — Status",
                "cmd": "python3 tools/post_scheduled_art.py --status",
                "desc": "Shows the next category in the rotation, last post date, and next scheduled post date.",
            },
            {
                "id": "post_art_list",
                "label": "Art Schedule — Category List",
                "cmd": "python3 tools/post_scheduled_art.py --list",
                "desc": "Shows all 20 art categories in rotation order with subjects used per category.",
            },
            {
                "id": "post_art_preview",
                "label": "Generate Next Art (Preview Only)",
                "cmd": "python3 tools/post_scheduled_art.py --preview",
                "desc": "Generates all listing images for the next category but does NOT post to Etsy. Review the output before going live.",
            },
            {
                "id": "post_art_force",
                "label": "Post Next Art to Etsy NOW",
                "cmd": "python3 tools/post_scheduled_art.py --force",
                "desc": "Generates art and posts a live Etsy listing immediately, bypassing the schedule. Advances queue to next category.",
            },
            {
                "id": "fetch_market",
                "label": "Refresh Market Reference Images",
                "cmd": "python3 tools/fetch_market_examples.py --refresh",
                "desc": "Re-downloads 10 reference images per category (200 total) from Etsy's live search. Updates market_references.html.",
            },
            {
                "id": "upscale_art",
                "label": "Upscale Art Files",
                "cmd": "python3 tools/upscale_art.py",
                "desc": "Upscales any art file under 3000px to 4× resolution using Lanczos + sharpening. Required before listing.",
                "local_only": True,
            },
            {
                "id": "gen_print_sizes",
                "label": "Generate Print Size ZIPs",
                "cmd": "python3 tools/generate_print_sizes.py",
                "desc": "Creates multi-size print ZIPs (8 sizes, 300 DPI) for all art files. Upload ZIPs as Etsy digital downloads.",
                "local_only": True,
            },
        ]
    },
    # ── LISTING MANAGEMENT ───────────────────────────────────────────────────
    {
        "category": "Listing Management",
        "color": "#FF9800",
        "icon": "🏪",
        "commands": [
            {
                "id": "planner_photos",
                "label": "Generate Planner Listing Photos",
                "cmd": "python3 tools/gen_planner_listing_photos.py",
                "desc": "Renders real PDF pages into 10 listing photos for each of the 4 digital planners and uploads to Etsy.",
                "local_only": True,
            },
            {
                "id": "sticker_photos",
                "label": "Generate Sticker Pack Photos",
                "cmd": "python3 tools/gen_sticker_listing_photos.py",
                "desc": "Creates listing photos for the 6 standalone sticker pack listings using real sticker sheet images.",
                "local_only": True,
            },
            {
                "id": "shorten_titles",
                "label": "Shorten All Titles to ≤70 Chars",
                "cmd": "python3 tools/shorten_titles.py",
                "desc": "Trims all active listing titles to 70 characters (2026 Etsy algorithm rule — >70 chars = mobile penalty).",
            },
            {
                "id": "ai_disclosure",
                "label": "Add AI Disclosure to Listings",
                "cmd": "python3 tools/add_ai_disclosure.py",
                "desc": "Adds mandatory Etsy AI disclosure text to all listings that are missing it (required since June 2025).",
            },
        ]
    },
    # ── PLANNERS & STICKERS ──────────────────────────────────────────────────
    {
        "category": "Planners & Stickers",
        "color": "#E91E63",
        "icon": "📓",
        "commands": [
            {
                "id": "gen_sticker_sheet",
                "label": "Generate New Sticker Sheet",
                "cmd": "python3 tools/gen_sticker_sheet.py",
                "desc": "Generates a new unique illustrated sticker sheet via gpt-image-1. Shows for approval before saving.",
            },
            {
                "id": "rebuild_sticker_pack",
                "label": "Rebuild Sticker Pack ZIP",
                "cmd": "python3 tools/rebuild_sticker_pack.py --pid DP1026",
                "desc": "Rebuilds the sticker pack ZIP for a planner and re-uploads to Etsy. Change --pid to DP1026/1027/1028/1029.",
                "local_only": True,
                "flags": [
                    {"flag": "--pid DP1026", "desc": "Life Planner (Lavender)"},
                    {"flag": "--pid DP1027", "desc": "Student Planner (Cotton Candy)"},
                    {"flag": "--pid DP1028", "desc": "Budget Planner (Midnight Blue)"},
                    {"flag": "--pid DP1029", "desc": "Fitness Planner (Coral Peach)"},
                ]
            },
        ]
    },
    # ── SOCIAL MEDIA ─────────────────────────────────────────────────────────
    {
        "category": "Social Media",
        "color": "#2196F3",
        "icon": "📱",
        "commands": [
            {
                "id": "pinterest_batch",
                "label": "Post All Listings to Pinterest",
                "cmd": "python3 tools/pinterest_batch_poster.py",
                "desc": "Posts all active wall art listings to Pinterest — one pin per listing, organized by board.",
            },
            {
                "id": "tiktok_post",
                "label": "Post TikTok Content",
                "cmd": "python3 tools/tiktok_poster.py",
                "desc": "Posts the next scheduled video from data/tiktok_content_calendar.json to @onbrandcraftz.",
            },
        ]
    },
    # ── CUSTOMER & ORDERS ────────────────────────────────────────────────────
    {
        "category": "Customers & Orders",
        "color": "#00BCD4",
        "icon": "🛍️",
        "commands": [
            {
                "id": "order_notify",
                "label": "Check for New Orders",
                "cmd": "python3 tools/order_notifier.py",
                "desc": "Checks for new Etsy orders and sends email notification + auto-delivers digital products.",
            },
            {
                "id": "etsy_messages",
                "label": "Show Message Templates",
                "cmd": "python3 tools/etsy_messages.py",
                "desc": "Prints the post-purchase message, thank-you coupon, and review request templates.",
            },
        ]
    },
    # ── AUTHENTICATION ────────────────────────────────────────────────────────
    {
        "category": "Authentication & Setup",
        "color": "#607D8B",
        "icon": "🔐",
        "commands": [
            {
                "id": "etsy_oauth",
                "label": "Re-authorize Etsy",
                "cmd": "python3 tools/etsy_oauth.py",
                "desc": "Re-runs the Etsy OAuth flow if the access token expires. Requires a local browser — run on your computer.",
                "local_only": True,
            },
            {
                "id": "pinterest_oauth",
                "label": "Re-authorize Pinterest",
                "cmd": "python3 tools/pinterest_oauth.py",
                "desc": "Refreshes the Pinterest access token (expires daily). Requires a local browser — run on your computer.",
                "local_only": True,
            },
            {
                "id": "tiktok_oauth",
                "label": "Set Up TikTok",
                "cmd": "python3 tools/tiktok_oauth.py",
                "desc": "First-time TikTok OAuth setup. Requires a local browser — run on your computer.",
                "local_only": True,
            },
        ]
    },
    # ── IMAGE TOOLS ──────────────────────────────────────────────────────────
    {
        "category": "Image Tools",
        "color": "#7B1FA2",
        "icon": "🖼️",
        "commands": [
            {
                "id": "svg_converter",
                "label": "SVG Converter",
                "cmd": "",
                "tool_url": "/svg",
                "desc": "Convert any photo or image to a high-quality scalable SVG. Paste, drag & drop, or browse. Three modes: Full Color, Black & White, Silhouette (Cricut/laser cut).",
            },
        ]
    },
    # ── AI AGENTS (HUB) ───────────────────────────────────────────────────────
    {
        "category": "AI Agents (Town Hub)",
        "color": "#FF5722",
        "icon": "🤖",
        "commands": [
            {
                "id": "hub_ceo",
                "label": "Start Hub (interactive)",
                "cmd": "python3 hub.py",
                "desc": "Starts the OnBrandCraftz Agent Hub. Requires an interactive terminal — run on your local computer.",
                "local_only": True,
            },
        ]
    },
]


# ── HTML template ─────────────────────────────────────────────────────────────

LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OnBrandCraftz — Sign in</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0D1B2A;
      --surface: rgba(22, 32, 51, 0.8);
      --border: rgba(42, 64, 96, 0.5);
      --text-main: #F5EDD0;
      --text-muted: #8A9BAE;
      --accent: #C9A84C;
      --accent-hover: #E8C870;
      --accent-glow: rgba(201, 168, 76, 0.3);
      --error: #E05252;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Outfit', sans-serif; }
    body {
      background: var(--bg);
      display: flex; align-items: center; justify-content: center;
      min-height: 100vh; padding: 20px; color: var(--text-main); overflow: hidden;
    }

    .card {
      background: var(--surface); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
      border: 1px solid var(--border); border-radius: 24px; padding: 48px 40px;
      max-width: 420px; width: 100%;
      box-shadow: 0 25px 60px -12px rgba(0,0,0,0.6), 0 0 40px rgba(201,168,76,0.05);
      text-align: center; position: relative; z-index: 1;
      animation: floatIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
      background: var(--accent); opacity: 0.6; border-radius: 2px;
    }
    @keyframes floatIn { 0% { opacity:0; transform:translateY(20px) scale(0.95); } 100% { opacity:1; transform:translateY(0) scale(1); } }
    .logo { font-size: 48px; margin-bottom: 20px; filter: drop-shadow(0 0 20px var(--accent-glow)); }
    h1 { font-size: 24px; font-weight: 700; margin-bottom: 8px; letter-spacing: -0.5px; }
    p { font-size: 14px; color: var(--text-muted); margin-bottom: 32px; line-height: 1.6; }
    input {
      width: 100%; padding: 14px 16px; background: rgba(13, 27, 42, 0.6);
      border: 1px solid var(--border); border-radius: 12px; color: var(--text-main);
      font-size: 15px; outline: none; transition: all 0.3s;
    }
    input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
    input::placeholder { color: #4A6580; }
    button {
      width: 100%; margin-top: 16px; padding: 14px;
      background: var(--accent);
      color: #0D1B2A; border: none; border-radius: 12px; font-size: 15px; font-weight: 700;
      cursor: pointer; transition: all 0.3s; box-shadow: 0 4px 14px var(--accent-glow);
    }
    button:hover { background: var(--accent-hover); transform: translateY(-1px); box-shadow: 0 6px 24px rgba(201,168,76,0.5); }
    button:active { transform: translateY(1px); }
    .err { color: var(--error); font-size: 13px; margin-top: 12px; font-weight: 500; animation: shake 0.4s; }
    @keyframes shake { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-4px); } 75% { transform: translateX(4px); } }
  </style>
</head>
<body>
<div class="card">
  <div class="logo">🏪</div>
  <h1>OnBrandCraftz</h1>
  <p>Command Center — Cloud Edition<br>Enter your password to continue.</p>
  <form method="post" action="/login">
    <input type="password" name="password" placeholder="Password" autofocus>
    <button type="submit">Unlock →</button>
    {% if error %}<div class="err">Incorrect password. Try again.</div>{% endif %}
  </form>
</div>
</body>
</html>
"""

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OnBrandCraftz — Command Center</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0B1320;
      --bg-panel: rgba(13, 27, 42, 0.7);
      --surface: rgba(22, 34, 56, 0.75);
      --border: rgba(42, 64, 96, 0.5);
      --border-hover: rgba(201, 168, 76, 0.4);
      --text-main: #F5EDD0;
      --text-muted: #8A9BAE;
      --text-dim: #4A6580;
      --accent: #C9A84C;
      --accent-light: #E8C870;
      --accent-glow: rgba(201, 168, 76, 0.3);
      --navy: #1B3A68;
      --header-bg: rgba(11, 19, 32, 0.94);
      --success: #4CAF8C;
      --error: #E05252;
      --card-shadow: 0 1px 0 rgba(255,255,255,0.05) inset, 0 8px 24px rgba(0,0,0,0.35);
    }
    html.theme-warm {
      --bg: #241c2e; --surface: rgba(45, 36, 56, 0.8); --border: #3d3248; --text-main: #f5eef2;
      --text-muted: #bfa3b5; --accent: #f2a0b5; --accent-light: #f7c3d0; --accent-glow: rgba(242, 160, 181, 0.3);
      --header-bg: rgba(36, 28, 46, 0.94);
    }
    html.theme-sakura {
      --bg: #140a10; --surface: rgba(31, 15, 24, 0.8); --border: #311826; --text-main: #f5e8ee;
      --text-muted: #a4758a; --accent: #f4a7b9; --accent-light: #ffd0db; --accent-glow: rgba(244, 167, 185, 0.3);
      --header-bg: rgba(20, 10, 16, 0.94);
    }
    html.theme-matcha {
      --bg: #0b120c; --surface: rgba(18, 28, 20, 0.8); --border: #1e2e21; --text-main: #e9f2e6;
      --text-muted: #7c9172; --accent: #8bc34a; --accent-light: #bce88e; --accent-glow: rgba(139, 195, 74, 0.3);
      --header-bg: rgba(11, 18, 12, 0.94);
    }
    html.theme-ocean {
      --bg: #07120f; --surface: rgba(13, 29, 26, 0.8); --border: #16312c; --text-main: #e6f2f0;
      --text-muted: #6f948c; --accent: #3ad6c8; --accent-light: #7ceee2; --accent-glow: rgba(58, 214, 200, 0.3);
      --header-bg: rgba(7, 18, 15, 0.94);
    }
    
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Outfit', sans-serif;
      background: radial-gradient(circle at 15% 15%, rgba(27, 58, 104, 0.35) 0%, transparent 45%),
                  radial-gradient(circle at 85% 75%, rgba(201, 168, 76, 0.08) 0%, transparent 50%),
                  var(--bg);
      background-attachment: fixed;
      color: var(--text-main); padding: 0; min-height: 100vh; display: flex; flex-direction: column;
      transition: background 0.3s, color 0.3s;
    }
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: transparent; }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.25); }
    
    .topbar {
      background: var(--header-bg); backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
      padding: 16px 32px; display: flex; align-items: center; gap: 16px;
      position: sticky; top: 0; z-index: 100; border-bottom: 1px solid var(--border);
    }
    .topbar h1 { font-size: 20px; font-weight: 700; letter-spacing: -0.5px; }
    .topbar .sub { font-size: 13px; color: var(--text-muted); margin-top: 2px; font-weight: 300; }
    .topbar .status { margin-left: auto; font-size: 13px; display: flex; align-items: center; gap: 8px; font-weight: 500; background: var(--surface); padding: 6px 14px; border-radius: 20px; border: 1px solid var(--border); }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--success); box-shadow: 0 0 10px var(--success); animation: pulse 2s infinite; }
    .dot.cloud { background: var(--accent); box-shadow: 0 0 10px var(--accent); }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    
    .theme-select-wrap { display: flex; align-items: center; gap: 6px; }
    .theme-select {
      background: var(--surface); border: 1px solid var(--border); color: var(--text-main);
      padding: 5px 12px; border-radius: 20px; font-size: 12px; font-family: 'Outfit', sans-serif;
      outline: none; cursor: pointer; transition: all 0.2s;
    }
    .theme-select:hover { border-color: var(--accent); }

    {% if cloud_mode %}
    .cloud-banner {
      background: rgba(27, 58, 104, 0.35);
      backdrop-filter: blur(8px); border-bottom: 1px solid var(--border);
      color: var(--text-main); padding: 10px 32px; font-size: 13px; display: flex; align-items: center; gap: 12px;
    }
    .cloud-banner strong { color: var(--accent); }
    .cloud-badge { background: rgba(201,168,76,0.1); border-radius: 6px; padding: 3px 8px; font-size: 11px; font-weight: 600; border: 1px solid rgba(201,168,76,0.2); color: var(--accent); }
    {% endif %}

    /* Executive KPI Strip */
    .kpi-strip {
      display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;
      margin-bottom: 28px;
    }
    .kpi-card {
      background: var(--surface); backdrop-filter: blur(12px); border: 1px solid var(--border);
      border-radius: 14px; padding: 14px 18px; display: flex; align-items: center; gap: 14px;
      box-shadow: var(--card-shadow); transition: transform 0.2s, border-color 0.2s, box-shadow 0.2s;
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: var(--border-hover); box-shadow: 0 10px 30px rgba(0,0,0,0.4); }
    .kpi-icon { font-size: 24px; padding: 10px; background: rgba(255,255,255,0.03); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05); }
    .kpi-info { display: flex; flex-direction: column; }
    .kpi-label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.6px; color: var(--text-muted); font-weight: 600; }
    .kpi-val { font-size: 14px; font-weight: 700; color: var(--text-main); margin-top: 2px; }
    
    .main { display: flex; flex: 1; }
    
    .sidebar {
      width: 250px; background: rgba(11, 19, 32, 0.6); border-right: 1px solid var(--border);
      padding: 24px 16px; flex-shrink: 0; position: sticky; top: 73px;
      height: calc(100vh - 73px); overflow-y: auto; backdrop-filter: blur(12px);
    }
    .sidebar a {
      display: flex; align-items: center; gap: 12px; padding: 12px 16px;
      font-size: 14px; color: var(--text-muted); text-decoration: none; border-radius: 12px;
      transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1); margin-bottom: 4px;
      border: 1px solid transparent; border-left: 3px solid transparent;
    }
    .sidebar a:hover {
      background: var(--surface); color: var(--text-main); border-color: var(--border);
    }
    .sidebar a.active {
      background: rgba(201, 168, 76, 0.08); color: var(--accent-light);
      border-left-color: var(--accent); border-color: rgba(201, 168, 76, 0.2);
    }
    .sidebar .icon { font-size: 18px; }
    .sidebar .nav-count { margin-left: auto; font-size: 11px; background: rgba(201,168,76,0.12); color: var(--accent); padding: 2px 7px; border-radius: 8px; font-weight: 600; }
    
    .content { flex: 1; padding: 36px 40px; max-width: 1240px; margin: 0 auto; width: 100%; }

    /* Search & Filter Controls */
    .controls-bar { display: flex; flex-direction: column; gap: 16px; margin-bottom: 32px; }
    .search-wrap { position: relative; width: 100%; }
    .search-wrap svg { position: absolute; left: 16px; top: 50%; transform: translateY(-50%); color: var(--text-dim); pointer-events: none; }
    .search-wrap input {
      width: 100%; padding: 14px 100px 14px 44px; background: var(--surface);
      border: 1px solid var(--border); border-radius: 14px; color: var(--text-main);
      font-size: 15px; font-family: 'Outfit', sans-serif; outline: none; transition: all 0.3s;
    }
    .search-wrap input:focus { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-glow); }
    .search-wrap input::placeholder { color: var(--text-dim); }
    .search-badge {
      position: absolute; right: 14px; top: 50%; transform: translateY(-50%);
      font-family: 'Fira Code', monospace; font-size: 11px; color: var(--text-dim);
      background: rgba(0,0,0,0.3); border: 1px solid var(--border); border-radius: 6px; padding: 3px 8px;
      pointer-events: none;
    }

    .filter-pills { display: flex; flex-wrap: wrap; gap: 8px; }
    .filter-btn {
      background: var(--surface); border: 1px solid var(--border); color: var(--text-muted);
      padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 600; cursor: pointer;
      transition: all 0.2s; font-family: 'Outfit', sans-serif; display: flex; align-items: center; gap: 6px;
    }
    .filter-btn:hover, .filter-btn.active { background: rgba(201,168,76,0.15); color: var(--accent-light); border-color: var(--accent); }

    .section { margin-bottom: 44px; scroll-margin-top: 100px; }
    .section-header {
      display: flex; align-items: center; gap: 12px; margin-bottom: 20px;
      padding-bottom: 12px; border-bottom: 1px solid rgba(201,168,76,0.12);
    }
    .section-header h2 { font-size: 20px; font-weight: 600; color: var(--text-main); }
    .cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 20px; }
    
    /* ── Sci-Fi HUD Corner Brackets ── */
    .brk { position: relative; }
    .brk::before, .brk::after {
      content: ''; position: absolute; width: 10px; height: 10px; pointer-events: none; opacity: 0.6; transition: all 0.3s;
    }
    .brk::before {
      top: -1px; left: -1px; border-top: 2px solid var(--cat-color, var(--accent)); border-left: 2px solid var(--cat-color, var(--accent)); border-top-left-radius: 6px;
    }
    .brk::after {
      bottom: -1px; right: -1px; border-bottom: 2px solid var(--cat-color, var(--accent)); border-right: 2px solid var(--cat-color, var(--accent)); border-bottom-right-radius: 6px;
    }
    .card:hover.brk::before, .card:hover.brk::after { opacity: 1; width: 15px; height: 15px; }

    .card {
      background: var(--surface); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border); border-radius: 16px; padding: 24px;
      box-shadow: var(--card-shadow); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex; flex-direction: column; position: relative; overflow: hidden;
      animation: cardIn 0.5s cubic-bezier(0.16, 1, 0.3, 1) both;
      animation-delay: calc(var(--i, 0) * 50ms);
    }
    @keyframes cardIn { 0% { opacity: 0; transform: translateY(16px); } 100% { opacity: 1; transform: translateY(0); } }
    .card::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: var(--cat-color, var(--accent)); opacity: 0.5; transition: opacity 0.3s;
    }
    .card:hover { transform: translateY(-4px); border-color: var(--cat-color, var(--border-hover)); box-shadow: 0 20px 40px -10px rgba(0,0,0,0.4), 0 0 20px rgba(201,168,76,0.15); }
    .card:hover::before { opacity: 1; }
    .card.local-card { opacity: 0.65; }
    .card.is-executing { border-color: var(--accent) !important; box-shadow: 0 0 25px var(--accent-glow) !important; animation: cardPulse 1.5s infinite; }
    @keyframes cardPulse { 0%, 100% { border-color: var(--accent); } 50% { border-color: var(--accent-light); } }

    .card-label { font-size: 16px; font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; justify-content: space-between; color: var(--text-main); }
    .local-badge { background: rgba(232, 160, 48, 0.1); color: #E8A030; border: 1px solid rgba(232, 160, 48, 0.2); border-radius: 6px; padding: 2px 8px; font-size: 11px; font-weight: 600; }
    .card-desc { font-size: 13px; color: var(--text-muted); line-height: 1.6; margin-bottom: 20px; flex: 1; }
    
    .card-cmd {
      font-family: 'Fira Code', monospace; font-size: 11px;
      background: rgba(0, 0, 0, 0.4); border: 1px solid var(--border); border-radius: 8px;
      padding: 10px 12px; color: #cbd5e1; margin-bottom: 16px;
      display: flex; align-items: center; cursor: pointer; transition: all 0.2s;
    }
    .card-cmd span { flex: 1; overflow-x: auto; white-space: nowrap; }
    .card-cmd span::-webkit-scrollbar { display: none; }
    .card-cmd:hover { background: rgba(0, 0, 0, 0.6); border-color: var(--border-hover); }
    .copy-hint { font-family: 'Outfit', sans-serif; font-size: 10px; color: var(--text-muted); margin-left: 12px; text-transform: uppercase; font-weight: 600; letter-spacing: 0.5px; }
    
    .flags { font-size: 12px; color: var(--text-muted); margin-top: -6px; margin-bottom: 16px; display: flex; flex-wrap: wrap; gap: 6px; }
    .flag-pill {
      background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;
      padding: 3px 8px; font-family: 'Fira Code', monospace; font-size: 10px; color: var(--text-muted);
      cursor: pointer; transition: all 0.2s; outline: none;
    }
    .flag-pill:hover, .flag-pill.active { background: rgba(201,168,76,0.15); color: var(--accent-light); border-color: var(--accent); }

    .btn-run {
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      background: transparent; color: var(--accent); border: 1px solid var(--accent);
      border-radius: 10px; padding: 10px 20px; font-size: 14px; font-weight: 600; cursor: pointer;
      transition: all 0.2s; text-decoration: none; width: 100%; font-family: 'Outfit', sans-serif;
    }
    .btn-run:hover { background: var(--accent); color: #0D1B2A; box-shadow: 0 4px 15px var(--accent-glow); }
    .btn-run:active { transform: scale(0.98); }
    .btn-run.running { background: rgba(201,168,76,0.1); color: var(--text-muted); cursor: not-allowed; border-color: var(--border); box-shadow: none; pointer-events: none; }
    
    .btn-local {
      display: inline-flex; align-items: center; justify-content: center; gap: 8px;
      background: transparent; border: 1px dashed rgba(255,255,255,0.2); border-radius: 10px;
      padding: 10px 20px; font-size: 14px; font-weight: 600; color: var(--text-muted); cursor: not-allowed; width: 100%;
    }
    
    /* IDE-Grade Terminal Output panel */
    #output-panel {
      position: fixed; bottom: 24px; right: 24px; width: 640px; max-width: calc(100vw - 48px);
      background: rgba(11, 19, 32, 0.96); backdrop-filter: blur(24px); -webkit-backdrop-filter: blur(24px);
      border: 1px solid var(--border); border-radius: 16px; box-shadow: 0 30px 60px -15px rgba(0,0,0,0.7);
      transform: translateY(150%); opacity: 0; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); z-index: 200;
      display: flex; flex-direction: column; height: 420px;
    }
    #output-panel.open { transform: translateY(0); opacity: 1; }
    #output-panel.fullscreen {
      top: 0; bottom: 0; left: 0; right: 0; width: 100vw; height: 100vh; max-width: 100vw;
      border-radius: 0; border: none; transform: none !important;
    }

    #output-header {
      display: flex; align-items: center; padding: 14px 20px; gap: 12px;
      border-bottom: 1px solid var(--border); background: rgba(255,255,255,0.02);
      border-top-left-radius: 16px; border-top-right-radius: 16px; position: relative;
    }
    #output-header::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 2px;
      background: var(--accent); border-top-left-radius: 16px; border-top-right-radius: 16px;
      box-shadow: 0 0 10px var(--accent-glow);
    }
    
    .mac-dots { display: flex; gap: 6px; margin-right: 4px; }
    .mac-dot { width: 10px; height: 10px; border-radius: 50%; }
    .mac-dot.red { background: #FF5F56; }
    .mac-dot.yellow { background: #FFBD2E; }
    .mac-dot.green { background: #27C93F; }

    #output-title { font-size: 13px; font-weight: 600; color: var(--text-main); flex: 1; font-family: 'Fira Code', monospace; letter-spacing: 0.3px; }
    
    .term-controls { display: flex; align-items: center; gap: 8px; }
    .term-btn {
      background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1); border-radius: 6px;
      color: var(--text-muted); padding: 4px 10px; font-size: 11px; font-family: 'Outfit', sans-serif;
      cursor: pointer; transition: all 0.2s; display: flex; align-items: center; gap: 4px;
    }
    .term-btn:hover { background: rgba(255,255,255,0.12); color: var(--text-main); }

    #output-body {
      font-family: 'Fira Code', monospace; font-size: 12px; padding: 18px 20px; flex: 1;
      overflow-y: auto; white-space: pre-wrap; line-height: 1.6; color: #c8d6e5;
    }
    .out-ok { color: var(--success); }
    .out-err { color: var(--error); }
    .out-info { color: var(--accent); opacity: 0.9; }
    
    @keyframes spin { to { transform: rotate(360deg); } }
    
    @media(max-width: 1024px) {
      .sidebar { width: 60px; padding: 24px 8px; }
      .sidebar a { justify-content: center; padding: 12px; gap: 0; }
      .sidebar a span:not(.icon) { display: none; }
      .sidebar .nav-count { display: none; }
    }
    @media(max-width: 800px) {
      .sidebar { display: none; }
      .content { padding: 20px; }
      .cards { grid-template-columns: 1fr; }
      #output-panel { bottom: 0; right: 0; width: 100%; border-radius: 16px 16px 0 0; }
    }
  </style>
</head>
<body>

<div class="topbar">
  <div>
    <div style="font-size: 20px; font-weight: 700; display: flex; align-items: center; gap: 10px; color: var(--accent);">
      🏪 OnBrandCraftz Command Center
    </div>
    <div class="sub" id="greeting"></div>
  </div>
  <div class="theme-select-wrap" style="margin-left: auto;">
    <a href="/frank" style="background: var(--surface); border: 1px solid var(--border); color: var(--text-main); padding: 5px 12px; border-radius: 20px; font-size: 12px; text-decoration: none; display: flex; align-items: center; gap: 4px; font-weight: 500;">📱 Phone/HUD View</a>
    <select class="theme-select" onchange="setTheme(this.value)">
      <option value="navy">🌌 Deep Navy (Default)</option>
      <option value="warm">🍇 Studio Warm (Plum)</option>
      <option value="sakura">🌸 Sakura (Pink)</option>
      <option value="matcha">🍵 Matcha (Emerald)</option>
      <option value="ocean">🌊 Ocean (Teal)</option>
    </select>
  </div>
  <span id="clock" style="color: var(--text-muted); font-size: 13px; font-family: 'Fira Code', monospace;"></span>
  {% if cloud_mode %}
  <div class="status"><div class="dot cloud"></div> Cloud Connected</div>
  {% else %}
  <div class="status"><div class="dot"></div> Local Network</div>
  {% endif %}
</div>

{% if cloud_mode %}
<div class="cloud-banner">
  ☁️ <strong>Cloud Mode</strong> is active. API tasks run instantly. <span class="cloud-badge">💻 Local PC</span> tasks require the local server to be online.
</div>
{% endif %}

<div class="main">
  <nav class="sidebar" id="sidebar">
    {% for section in commands %}
    <a href="#{{ section.id }}">
      <span class="icon">{{ section.icon }}</span>
      {{ section.category }}
      <span class="nav-count">{{ section.commands|length }}</span>
    </a>
    {% endfor %}
  </nav>

  <div class="content">

    <!-- KPI Metric Strip -->
    <div class="kpi-strip">
      <div class="kpi-card brk">
        <div class="kpi-icon">📊</div>
        <div class="kpi-info">
          <span class="kpi-label">Active Catalog</span>
          <span class="kpi-val">70+ Digital Items</span>
        </div>
      </div>
      <div class="kpi-card brk">
        <div class="kpi-icon">🎯</div>
        <div class="kpi-info">
          <span class="kpi-label">Monthly Target</span>
          <span class="kpi-val">$5,000 Revenue Goal</span>
        </div>
      </div>
      <div class="kpi-card brk">
        <div class="kpi-icon">⚡</div>
        <div class="kpi-info">
          <span class="kpi-label">Automation Engine</span>
          <span class="kpi-val">100% Operational</span>
        </div>
      </div>
      <div class="kpi-card brk">
        <div class="kpi-icon">🤖</div>
        <div class="kpi-info">
          <span class="kpi-label">Agent Controller</span>
          <span class="kpi-val">Frank Ready</span>
        </div>
      </div>
    </div>

    <!-- Search & Filters -->
    <div class="controls-bar">
      <div class="search-wrap">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
        <input type="text" id="search-input" placeholder="Search commands..." oninput="filterCommands(this.value)">
        <span class="search-badge">Press / or ⌘K</span>
      </div>
      <div class="filter-pills">
        <button class="filter-btn active" onclick="filterCategory('all', this)">⚡ All</button>
        {% for section in commands %}
        <button class="filter-btn" onclick="filterCategory('{{ section.id }}', this)">{{ section.icon }} {{ section.category }}</button>
        {% endfor %}
      </div>
    </div>

    {% for section in commands %}
    <div class="section" id="{{ section.id }}" style="--cat-color: {{ section.color }};">
      <div class="section-header">
        <span class="sicon">{{ section.icon }}</span>
        <h2>{{ section.category }}</h2>
      </div>
      <div class="cards">
        {% for cmd in section.commands %}
        {% set is_local = cmd.local_only and cloud_mode %}
        <div class="card brk {% if is_local %}local-card{% endif %}" id="card-{{ cmd.id }}" data-cmd-base="{{ cmd.cmd }}" data-cmd-current="{{ cmd.cmd }}" style="--cat-color: {{ section.color }};">
          <div class="card-label">
            {{ cmd.label }}
            {% if is_local %}<span class="local-badge">💻 Local PC</span>{% endif %}
          </div>
          <div class="card-desc">{{ cmd.desc }}</div>
          
          {% if not cmd.tool_url %}
          <div class="card-cmd" id="cmd-display-{{ cmd.id }}" onclick="copyCmd(this, '{{ cmd.id }}')" title="Click to copy">
            <span>$ {{ cmd.cmd }}</span>
            <span class="copy-hint">Copy</span>
          </div>
          {% endif %}
          
          {% if cmd.flags %}
          <div class="flags">
            {% for f in cmd.flags %}
            <button type="button" class="flag-pill {% if loop.first %}active{% endif %}" onclick="selectFlag(this, '{{ cmd.id }}', '{{ f.flag }}')" title="{{ f.desc }}">
              {{ f.flag }}
            </button>
            {% endfor %}
          </div>
          {% endif %}
          
          <div style="margin-top: auto;">
            {% if cmd.tool_url %}
            <a class="btn-run" href="{{ cmd.tool_url }}" target="_blank">
              <span style="font-size: 16px;">🔗</span> Open Tool
            </a>
            {% elif is_local %}
            <button class="btn-local" disabled title="Requires local computer to be online">
              🔒 Local Only
            </button>
            {% else %}
            <button class="btn-run" id="btn-run-{{ cmd.id }}" onclick="runCmd('{{ cmd.id }}', '{{ cmd.label | replace("'", "\'") }}', '{{ section.color }}', this)">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>
              Execute
            </button>
            {% endif %}
          </div>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<div id="output-panel">
  <div id="output-header">
    <div class="mac-dots">
      <span class="mac-dot red"></span>
      <span class="mac-dot yellow"></span>
      <span class="mac-dot green"></span>
    </div>
    <span id="output-title">Terminal Output</span>
    <div class="term-controls">
      <button class="term-btn" onclick="copyOutput()">📋 Copy</button>
      <button class="term-btn" onclick="clearOutput()">🧹 Clear</button>
      <button class="term-btn" onclick="toggleFullscreen()">⤢ Expand</button>
      <button id="btn-close" onclick="closeOutput()">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
      </button>
    </div>
  </div>
  <div id="output-body"></div>
</div>

<script>
const CSRF_TOKEN = "{{ csrf_token }}";
const OWNER_NAME = "{{ owner_name }}";
let activeBtn = null;
let activeCard = null;

// Theme Switcher (Navy, Studio Warm Plum, Sakura Pink, Matcha Emerald, Ocean Teal)
function setTheme(t) {
  document.documentElement.className = t === 'navy' ? '' : 'theme-' + t;
  localStorage.setItem('command_center_theme', t);
  const select = document.querySelector('.theme-select');
  if (select) select.value = t;
}
const savedTheme = localStorage.getItem('command_center_theme') || 'navy';
setTheme(savedTheme);

// Greeting & Clock
function updateGreeting() {
  const h = new Date().getHours();
  const g = h < 12 ? 'Good morning' : h < 17 ? 'Good afternoon' : 'Good evening';
  document.getElementById('greeting').textContent = g + ', ' + OWNER_NAME + ' 👋';
}
function updateClock() {
  document.getElementById('clock').textContent = new Date().toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });
}
updateGreeting(); updateClock(); setInterval(updateClock, 60000);

// Keyboard Shortcuts (/ or Cmd+K)
document.addEventListener('keydown', e => {
  if ((e.key === '/' || (e.key === 'k' && (e.metaKey || e.ctrlKey))) && document.activeElement.tagName !== 'INPUT') {
    e.preventDefault();
    document.getElementById('search-input').focus();
  }
});

// Staggered card entrance
document.querySelectorAll('.card').forEach((c, i) => c.style.setProperty('--i', i));

// Category Filter Pills
function filterCategory(catId, btn) {
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.section').forEach(sec => {
    sec.style.display = (catId === 'all' || sec.id === catId) ? '' : 'none';
  });
}

// Search filter
function filterCommands(q) {
  const query = q.toLowerCase().trim();
  document.querySelectorAll('.card').forEach(card => {
    const text = (card.querySelector('.card-label').textContent + ' ' + card.querySelector('.card-desc').textContent).toLowerCase();
    card.style.display = (!query || text.includes(query)) ? '' : 'none';
  });
  document.querySelectorAll('.section').forEach(section => {
    const visible = section.querySelectorAll('.cards .card:not([style*="display: none"])').length;
    section.style.display = (!query || visible > 0) ? '' : 'none';
  });
}

// Interactive Flag Selection
function selectFlag(btn, cmdId, flagStr) {
  const card = document.getElementById('card-' + cmdId);
  if (!card) return;
  card.querySelectorAll('.flag-pill').forEach(p => p.classList.remove('active'));
  btn.classList.add('active');

  const baseCmd = card.getAttribute('data-cmd-base');
  // Replace existing --pid or append
  let newCmd = baseCmd;
  if (baseCmd.includes('--pid')) {
    newCmd = baseCmd.replace(/--pid\\s+\\S+/, flagStr);
  } else {
    newCmd = baseCmd + ' ' + flagStr;
  }
  card.setAttribute('data-cmd-current', newCmd);
  const displayEl = document.getElementById('cmd-display-' + cmdId);
  if (displayEl) {
    displayEl.querySelector('span').textContent = '$ ' + newCmd;
  }
}

function copyCmd(el, cmdId) {
  const card = document.getElementById('card-' + cmdId);
  const cmdText = card ? card.getAttribute('data-cmd-current') : el.querySelector('span').textContent.replace('$ ', '');
  navigator.clipboard.writeText(cmdText).then(() => {
    const hint = el.querySelector('.copy-hint');
    hint.textContent = 'Copied';
    hint.style.color = '#4CAF8C';
    setTimeout(() => { hint.textContent = 'Copy'; hint.style.color = ''; }, 2000);
  });
}

function copyOutput() {
  const body = document.getElementById('output-body');
  navigator.clipboard.writeText(body.textContent).then(() => {
    alert('Terminal output copied to clipboard!');
  });
}

function clearOutput() {
  document.getElementById('output-body').innerHTML = '<span class="out-info">Console cleared.</span>\n';
}

function toggleFullscreen() {
  const panel = document.getElementById('output-panel');
  panel.classList.toggle('fullscreen');
}

function runCmd(id, label, color, btn) {
  const panel = document.getElementById('output-panel');
  const body = document.getElementById('output-body');
  const title = document.getElementById('output-title');
  const card = document.getElementById('card-' + id);
  const cmdToRun = card ? card.getAttribute('data-cmd-current') : '';

  if (activeBtn && activeBtn !== btn) {
    activeBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Execute';
    activeBtn.classList.remove('running');
    activeBtn.disabled = false;
  }
  if (activeCard) {
    activeCard.classList.remove('is-executing');
  }

  activeBtn = btn;
  activeCard = card;
  if (card) card.classList.add('is-executing');

  btn.innerHTML = '<svg class="spinner" style="margin-right:8px; animation: spin 1s linear infinite;" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> Running...';
  btn.classList.add('running');
  btn.disabled = true;

  body.innerHTML = '<span class="out-info">🚀 Initializing task: ' + label + '\n$ ' + cmdToRun + '\n\n</span>';
  title.textContent = 'Executing: ' + label;
  panel.classList.add('open');
  body.scrollTop = 0;

  const es = new EventSource('/run?id=' + encodeURIComponent(id) + '&csrf_token=' + encodeURIComponent(CSRF_TOKEN));
  es.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.done) {
      es.close();
      if (activeCard) activeCard.classList.remove('is-executing');
      if (data.ok) {
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><path d="M20 6L9 17l-5-5"></path></svg> Success';
        btn.style.background = 'rgba(76, 175, 140, 0.15)';
        btn.style.color = '#4CAF8C';
        btn.style.borderColor = 'rgba(76, 175, 140, 0.4)';
      } else {
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Failed';
        btn.style.background = 'rgba(224, 82, 82, 0.15)';
        btn.style.color = '#E05252';
        btn.style.borderColor = 'rgba(224, 82, 82, 0.4)';
      }
      btn.classList.remove('running');
      setTimeout(() => {
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Execute';
        btn.style.background = '';
        btn.style.color = '';
        btn.style.borderColor = '';
        btn.disabled = false;
        activeBtn = null;
        activeCard = null;
      }, 4000);
    } else {
      const span = document.createElement('span');
      span.className = data.err ? 'out-err' : 'out-ok';
      span.textContent = data.line;
      body.appendChild(span);
      body.scrollTop = body.scrollHeight;
    }
  };
  es.onerror = function() {
    es.close();
    if (activeCard) activeCard.classList.remove('is-executing');
    btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Execute';
    btn.classList.remove('running');
    btn.disabled = false;
    activeBtn = null;
    activeCard = null;
  };
}

function closeOutput() {
  document.getElementById('output-panel').classList.remove('open');
}

// Sidebar active state logic
const sections = document.querySelectorAll('.section');
const navLinks = document.querySelectorAll('.sidebar a');

window.addEventListener('scroll', () => {
  let current = '';
  sections.forEach(section => {
    const sectionTop = section.offsetTop;
    if (pageYOffset >= sectionTop - 150) {
      current = section.getAttribute('id');
    }
  });
  navLinks.forEach(link => {
    link.classList.remove('active');
    if (link.getAttribute('href') === '#' + current) {
      link.classList.add('active');
    }
  });
});

navLinks.forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
  });
});
</script>
</body>
</html>
"""


# ── Auth middleware ────────────────────────────────────────────────────────────

@app.before_request
def require_auth():
    if not CENTER_PASSWORD:
        return
    if request.path in ("/login", "/favicon.ico"):
        return
    if not session.get("authenticated"):
        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    error = False
    if request.method == "POST":
        if request.form.get("password") == CENTER_PASSWORD:
            session["authenticated"] = True
            return redirect("/")
        error = True
    return render_template_string(LOGIN_HTML, error=error)


# ── Routes ─────────────────────────────────────────────────────────────────────

def _find_cmd(cmd_id):
    for section in COMMANDS:
        for cmd in section["commands"]:
            if cmd["id"] == cmd_id:
                return cmd
    return None


@app.route("/")
def index():
    sections = []
    for section in COMMANDS:
        sections.append({
            "id": section["category"].lower().replace(" ", "_").replace("&", "and"),
            "category": section["category"],
            "color": section["color"],
            "icon": section["icon"],
            "commands": section["commands"],
        })
    return render_template_string(HTML, commands=sections, cloud_mode=IS_CLOUD, csrf_token=get_csrf_token(), owner_name=OWNER_NAME)


@app.route("/run")
def run_command():
    token = request.args.get("csrf_token", "")
    if not token or token != session.get("csrf_token"):
        def _unauthorized():
            msg = json.dumps({"line": "403 Forbidden: Invalid or missing CSRF token.\n", "err": True})
            yield f"data: {msg}\n\n"
            yield f'data: {json.dumps({"done": True, "ok": False})}\n\n'
        return Response(_unauthorized(), mimetype="text/event-stream", status=403,
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    cmd_id = request.args.get("id", "")
    cmd_def = _find_cmd(cmd_id)
    if not cmd_def:
        return Response('data: {"done":true,"ok":false}\n\n', mimetype="text/event-stream")

    if IS_CLOUD and cmd_def.get("local_only"):
        def _blocked():
            msg = json.dumps({"line": "This command requires your local computer.\n", "err": True})
            yield f"data: {msg}\n\n"
            yield f'data: {json.dumps({"done": True, "ok": False})}\n\n'
        return Response(_blocked(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    cmd = cmd_def["cmd"]
    if not cmd:
        def _empty():
            msg = json.dumps({"line": "No command defined.\n", "err": True})
            yield f"data: {msg}\n\n"
            yield f'data: {json.dumps({"done": True, "ok": False})}\n\n'
        return Response(_empty(), mimetype="text/event-stream",
                        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    cmd_args = shlex.split(cmd)

    def generate():
        proc = subprocess.Popen(
            cmd_args,
            shell=False,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        import select as sel

        fds = {proc.stdout.fileno(): False, proc.stderr.fileno(): True}
        open_fds = set(fds.keys())

        while open_fds:
            readable, _, _ = sel.select(list(open_fds), [], [], 0.1)
            for fd in readable:
                is_err = fds[fd]
                line = os.read(fd, 4096).decode("utf-8", errors="replace")
                if not line:
                    open_fds.discard(fd)
                    continue
                for ln in line.splitlines(keepends=True):
                    payload = json.dumps({"line": ln, "err": is_err})
                    yield f"data: {payload}\n\n"

        proc.wait()
        ok = proc.returncode == 0
        yield f"data: {json.dumps({'done': True, 'ok': ok})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── SVG Converter page & API ──────────────────────────────────────────────────

SVG_PAGE_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>SVG Converter — OnBrandCraftz</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0D1B2A;
      --surface: rgba(22, 32, 51, 0.75);
      --border: rgba(42, 64, 96, 0.5);
      --border-hover: rgba(201, 168, 76, 0.4);
      --text-main: #F5EDD0;
      --text-muted: #8A9BAE;
      --accent: #C9A84C;
      --accent-hover: #E8C870;
      --header-bg: rgba(13, 27, 42, 0.92);
      --success: #4CAF8C;
      --error: #E05252;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Outfit', sans-serif;
      background: var(--bg);
      color: var(--text-main); min-height: 100vh;
    }
    .topbar {
      background: var(--header-bg); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
      padding: 16px 32px; display: flex; align-items: center; gap: 20px;
      position: sticky; top: 0; z-index: 100; border-bottom: 1px solid var(--border);
    }
    .back-btn {
      color: var(--text-muted); text-decoration: none; font-size: 14px; font-weight: 500;
      display: flex; align-items: center; gap: 8px; transition: all 0.2s;
      background: rgba(255,255,255,0.05); padding: 8px 16px; border-radius: 8px; border: 1px solid transparent;
    }
    .back-btn:hover { color: #fff; background: rgba(255,255,255,0.1); border-color: var(--border); transform: translateX(-2px); }
    
    .container { max-width: 1100px; margin: 0 auto; padding: 40px 24px; }
    
    .drop-zone {
      background: rgba(15, 23, 42, 0.4); border: 2px dashed rgba(56, 189, 248, 0.3);
      border-radius: 20px; padding: 60px 40px; text-align: center; cursor: pointer;
      transition: all 0.3s; margin-bottom: 24px; backdrop-filter: blur(12px);
    }
    .drop-zone:hover, .drop-zone.drag-over {
      border-color: var(--accent); background: rgba(56, 189, 248, 0.05);
      box-shadow: 0 0 30px rgba(56, 189, 248, 0.1);
    }
    .drop-zone.has-image { padding: 24px; border-style: solid; border-color: var(--accent); }
    .drop-icon { font-size: 48px; margin-bottom: 16px; display: block; filter: drop-shadow(0 0 10px rgba(56, 189, 248, 0.4)); }
    .drop-title { font-size: 20px; font-weight: 600; color: #fff; margin-bottom: 8px; }
    .drop-sub { font-size: 14px; color: var(--text-muted); line-height: 1.8; }
    .drop-sub kbd {
      background: rgba(255,255,255,0.1); border: 1px solid var(--border); border-radius: 6px;
      padding: 2px 8px; font-family: 'Fira Code', monospace; font-size: 12px; color: #fff;
    }
    
    .controls {
      background: var(--surface); border-radius: 20px; padding: 32px;
      border: 1px solid var(--border); margin-bottom: 24px; backdrop-filter: blur(12px);
      box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }
    .controls h3 { font-size: 16px; font-weight: 600; margin-bottom: 20px; color: #fff; display: flex; align-items: center; gap: 8px; }
    
    .mode-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 24px; }
    .mode-btn {
      padding: 20px 16px; border: 1px solid var(--border); border-radius: 16px;
      cursor: pointer; text-align: center; transition: all 0.2s; background: rgba(0,0,0,0.2);
      user-select: none; position: relative; overflow: hidden;
    }
    .mode-btn:hover { border-color: var(--border-hover); transform: translateY(-2px); }
    .mode-btn.active {
      border-color: var(--accent); background: rgba(56, 189, 248, 0.1);
      box-shadow: 0 4px 20px rgba(56, 189, 248, 0.15);
    }
    .mode-btn.active::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: var(--accent); box-shadow: 0 0 10px var(--accent);
    }
    .mode-icon { font-size: 28px; margin-bottom: 12px; display: block; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.3)); }
    .mode-name { font-size: 15px; font-weight: 600; color: #fff; margin-bottom: 6px; }
    .mode-desc { font-size: 12px; color: var(--text-muted); line-height: 1.5; }
    
    .btn-row { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
    
    .btn-convert {
      display: inline-flex; align-items: center; gap: 10px; background: var(--accent);
      color: #fff; border: none; border-radius: 12px; padding: 14px 32px;
      font-size: 16px; font-weight: 700; cursor: pointer; transition: all 0.2s;
      box-shadow: 0 4px 14px rgba(56, 189, 248, 0.4); font-family: 'Outfit', sans-serif;
    }
    .btn-convert:hover:not(:disabled) { background: var(--accent-hover); transform: translateY(-2px); box-shadow: 0 6px 20px rgba(56, 189, 248, 0.5); }
    .btn-convert:disabled { background: rgba(255,255,255,0.1); color: var(--text-muted); cursor: not-allowed; box-shadow: none; }
    
    .btn-download {
      display: inline-flex; align-items: center; gap: 10px; background: var(--success);
      color: #000; border: none; border-radius: 12px; padding: 14px 32px;
      font-size: 16px; font-weight: 700; cursor: pointer; text-decoration: none;
      transition: all 0.2s; box-shadow: 0 4px 14px rgba(74, 222, 128, 0.4); font-family: 'Outfit', sans-serif;
    }
    .btn-download:hover { background: #22c55e; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(74, 222, 128, 0.5); }
    
    .status-bar {
      border-radius: 12px; padding: 16px 20px; font-size: 14px; font-weight: 500;
      margin-bottom: 24px; display: none; align-items: center; gap: 12px;
    }
    .status-bar.show { display: flex; animation: floatIn 0.3s ease-out; }
    @keyframes floatIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .status-bar.loading { background: rgba(56, 189, 248, 0.1); color: var(--accent); border: 1px solid rgba(56, 189, 248, 0.2); }
    .status-bar.success { background: rgba(74, 222, 128, 0.1); color: var(--success); border: 1px solid rgba(74, 222, 128, 0.2); }
    .status-bar.error { background: rgba(248, 113, 113, 0.1); color: var(--error); border: 1px solid rgba(248, 113, 113, 0.2); }
    
    .spinner {
      width: 18px; height: 18px; border: 2.5px solid rgba(255,255,255,0.2);
      border-top-color: currentColor; border-radius: 50%; flex-shrink: 0;
      animation: spin 0.8s linear infinite;
    }
    @keyframes spin { to { transform: rotate(360deg); } }
    
    .preview-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; margin-bottom: 40px; }
    .preview-box {
      background: var(--surface); border-radius: 20px; border: 1px solid var(--border);
      overflow: hidden; backdrop-filter: blur(12px); display: flex; flex-direction: column;
      box-shadow: 0 10px 30px -10px rgba(0,0,0,0.5);
    }
    .preview-label {
      padding: 16px 20px; font-size: 14px; font-weight: 600; color: #fff;
      background: rgba(0,0,0,0.3); border-bottom: 1px solid var(--border);
      display: flex; justify-content: space-between; align-items: center;
    }
    .preview-meta { font-weight: 400; color: var(--text-muted); font-size: 12px; font-family: 'Fira Code', monospace; }
    
    .preview-content {
      display: flex; align-items: center; justify-content: center;
      min-height: 250px; padding: 24px; max-height: 500px; overflow: auto;
      background: repeating-conic-gradient(rgba(255,255,255,0.03) 0% 25%, transparent 0% 50%) 50% / 20px 20px;
      flex: 1;
    }
    .preview-content img { max-width: 100%; max-height: 400px; object-fit: contain; display: block; filter: drop-shadow(0 10px 20px rgba(0,0,0,0.3)); }
    .preview-placeholder { color: var(--text-muted); font-size: 14px; text-align: center; line-height: 1.8; }
    
    .stats { display: flex; gap: 24px; flex-wrap: wrap; margin-left: auto; background: rgba(0,0,0,0.2); padding: 10px 20px; border-radius: 12px; border: 1px solid var(--border); }
    .stat { font-size: 12px; color: var(--text-muted); }
    .stat strong { color: #fff; font-weight: 600; font-family: 'Fira Code', monospace; margin-left: 6px; }
    
    @media(max-width: 800px) {
      .preview-grid { grid-template-columns: 1fr; }
      .mode-grid { grid-template-columns: 1fr; }
      .btn-row { flex-direction: column; align-items: stretch; }
      .stats { margin-left: 0; width: 100%; justify-content: space-between; }
    }
  </style>
</head>
<body>
<div class="topbar">
  <a href="/" class="back-btn">
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
    Back to Hub
  </a>
  <div>
    <div style="font-size: 18px; font-weight: 700; color: #fff;">🖼️ High-Fidelity SVG Converter</div>
    <div style="font-size: 13px; color: var(--text-muted); margin-top: 2px;">Transform rasters into pristine vector art</div>
  </div>
</div>

<div class="container">
  <div class="drop-zone" id="drop-zone" onclick="document.getElementById('file-input').click()">
    <span class="drop-icon" id="drop-icon">✨</span>
    <div class="drop-title" id="drop-title">Drop your image here to begin</div>
    <div class="drop-sub" id="drop-sub">
      <kbd>Ctrl+V</kbd> paste from clipboard &nbsp;·&nbsp;
      Drag &amp; drop a file &nbsp;·&nbsp;
      Click to browse<br><br>
      <span style="opacity: 0.7;">Supports PNG, JPG, WEBP, BMP, GIF</span>
    </div>
    <input type="file" id="file-input" accept="image/*" style="display:none">
  </div>

  <div class="status-bar" id="status-bar">
    <div class="spinner" id="status-spinner" style="display:none"></div>
    <span id="status-text"></span>
  </div>

  <div class="controls">
    <h3>
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
      Vectorization Settings
    </h3>
    <div class="mode-grid">
      <div class="mode-btn active" onclick="setMode('color',this)">
        <span class="mode-icon">🎨</span>
        <div class="mode-name">Full Color Master</div>
        <div class="mode-desc">Maximum color fidelity. Best for photos, complex illustrations, and detailed artwork.</div>
      </div>
      <div class="mode-btn" onclick="setMode('bw',this)">
        <span class="mode-icon">◑</span>
        <div class="mode-name">Monochrome</div>
        <div class="mode-desc">Clean B&amp;W paths. Best for logos, sketches, line art, and typography.</div>
      </div>
      <div class="mode-btn" onclick="setMode('silhouette',this)">
        <span class="mode-icon">⬟</span>
        <div class="mode-name">Solid Silhouette</div>
        <div class="mode-desc">Simplified unified shape. Best for sticker cut lines, Cricut, and laser machines.</div>
      </div>
    </div>
    <div class="btn-row">
      <button class="btn-convert" id="btn-convert" onclick="doConvert()" disabled>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
        Convert to SVG
      </button>
      <a class="btn-download" id="btn-download" style="display:none" download="converted.svg">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
        Download Vector
      </a>
      <div class="stats" id="stats" style="display:none"></div>
    </div>
  </div>

  <div class="preview-grid">
    <div class="preview-box">
      <div class="preview-label">
        Source Raster
        <span class="preview-meta" id="orig-meta"></span>
      </div>
      <div class="preview-content" id="orig-preview">
        <div class="preview-placeholder">Your image will appear here</div>
      </div>
    </div>
    <div class="preview-box">
      <div class="preview-label">
        Vector Output
        <span class="preview-meta" id="svg-meta"></span>
      </div>
      <div class="preview-content" id="svg-preview">
        <div class="preview-placeholder">SVG preview will appear here<br>after conversion is complete</div>
      </div>
    </div>
  </div>
</div>

<script>
let currentMode = 'color';
let currentFile = null;

function setMode(mode, btn) {
  currentMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
}

function fmt(b) {
  if (b < 1024) return b + ' B';
  if (b < 1048576) return (b/1024).toFixed(1) + ' KB';
  return (b/1048576).toFixed(2) + ' MB';
}

function setStatus(type, text, spinner) {
  const bar = document.getElementById('status-bar');
  bar.className = 'status-bar show ' + type;
  document.getElementById('status-spinner').style.display = spinner ? 'block' : 'none';
  document.getElementById('status-text').textContent = text;
}
function clearStatus() { document.getElementById('status-bar').className = 'status-bar'; }

function loadFile(file) {
  if (!file || !file.type.startsWith('image/')) {
    setStatus('error', 'Please provide an image file (PNG, JPG, WEBP, BMP, GIF).', false);
    return;
  }
  currentFile = file;
  const reader = new FileReader();
  reader.onload = function(e) {
    const dz = document.getElementById('drop-zone');
    dz.classList.add('has-image');
    document.getElementById('drop-icon').textContent = '✓';
    document.getElementById('drop-title').textContent = file.name;
    document.getElementById('drop-sub').textContent = fmt(file.size) + ' · Click to change image';

    const img = new Image();
    img.src = e.target.result;
    img.onload = function() {
      const p = document.getElementById('orig-preview');
      p.innerHTML = '';
      p.appendChild(img);
      document.getElementById('orig-meta').textContent =
        img.naturalWidth + '×' + img.naturalHeight + ' · ' + fmt(file.size);
    };
    document.getElementById('btn-convert').disabled = false;
    document.getElementById('btn-download').style.display = 'none';
    document.getElementById('stats').style.display = 'none';
    document.getElementById('svg-meta').textContent = '';
    document.getElementById('svg-preview').innerHTML =
      '<div class="preview-placeholder">Ready for processing.<br>Click "Convert to SVG" to generate.</div>';
    clearStatus();
  };
  reader.readAsDataURL(file);
}

document.addEventListener('paste', function(e) {
  for (const item of e.clipboardData.items) {
    if (item.type.startsWith('image/')) { loadFile(item.getAsFile()); return; }
  }
});
const dz = document.getElementById('drop-zone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('drag-over');
  if (e.dataTransfer.files.length) loadFile(e.dataTransfer.files[0]);
});
document.getElementById('file-input').addEventListener('change', e => {
  if (e.target.files.length) loadFile(e.target.files[0]);
});

async function doConvert() {
  if (!currentFile) return;
  const btn = document.getElementById('btn-convert');
  btn.disabled = true;
  btn.innerHTML = '<svg class="spinner" style="margin-right:8px" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg> Rendering...';
  
  setStatus('loading', 'Vectorizing image — this usually takes 5-15 seconds for detailed art...', true);
  document.getElementById('btn-download').style.display = 'none';
  document.getElementById('stats').style.display = 'none';
  document.getElementById('svg-preview').innerHTML =
    '<div class="preview-placeholder"><svg class="spinner" style="width:30px;height:30px;color:var(--accent);margin-bottom:15px;" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"></path></svg><br>Processing layers...</div>';

  try {
    const form = new FormData();
    form.append('image', currentFile);
    form.append('mode', currentMode);
    const res = await fetch('/api/convert-svg', { method: 'POST', body: form });
    const data = await res.json();
    if (data.error) throw new Error(data.error);

    const blob = new Blob([data.svg], { type: 'image/svg+xml' });
    if (window._currentSvgUrl) { URL.revokeObjectURL(window._currentSvgUrl); }
    window._currentSvgUrl = URL.createObjectURL(blob);
    const img = new Image();
    img.src = window._currentSvgUrl;
    const svgPrev = document.getElementById('svg-preview');
    svgPrev.innerHTML = '';
    svgPrev.appendChild(img);
    document.getElementById('svg-meta').textContent = fmt(data.svg_size);

    const dlBtn = document.getElementById('btn-download');
    dlBtn.href = window._currentSvgUrl;
    dlBtn.download = currentFile.name.replace(/\.[^.]+$/, '') + '.svg';
    dlBtn.style.display = 'inline-flex';

    const statsEl = document.getElementById('stats');
    statsEl.style.display = 'flex';
    statsEl.innerHTML =
      '<div class="stat">Raster: <strong>' + fmt(data.orig_size) + '</strong></div>' +
      '<div class="stat">Vector: <strong>' + fmt(data.svg_size) + '</strong></div>' +
      '<div class="stat">Resolution: <strong>' + data.width + '×' + data.height + '</strong></div>';

    setStatus('success', '✨ Vectorization complete! The SVG is ready for download.', false);
  } catch(err) {
    setStatus('error', 'Conversion failed: ' + err.message, false);
    document.getElementById('svg-preview').innerHTML =
      '<div class="preview-placeholder" style="color:var(--error)">Conversion failed.<br>Try a different image or mode.</div>';
  }
  btn.disabled = false;
  btn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg> Convert to SVG';
}
</script>
</body>
</html>
"""


@app.route("/svg")
def svg_converter_page():
    return render_template_string(SVG_PAGE_HTML)


@app.route("/api/convert-svg", methods=["POST"])
def convert_svg():
    try:
        import vtracer
        import re as _re
        from PIL import Image, ImageFilter
        import numpy as np
    except ImportError as e:
        return jsonify({"error": f"Missing dependency: {e}. Run: pip install vtracer Pillow numpy"}), 500

    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    f = request.files["image"]
    mode = request.form.get("mode", "color")

    try:
        raw_bytes = f.read()
        img = Image.open(io.BytesIO(raw_bytes))

        # Resize large images so vtracer finishes under 5s on shared CPU
        max_side = 1200 if mode == "color" else 1600
        if max(img.size) > max_side:
            ratio = max_side / max(img.size)
            img = img.resize(
                (int(img.width * ratio), int(img.height * ratio)),
                Image.LANCZOS
            )

        width, height = img.size

        if mode == "bw":
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG")
            png_bytes = buf.getvalue()
            params = dict(
                colormode="binary", hierarchical="cutout", mode="spline",
                filter_speckle=4, color_precision=8, layer_difference=16,
                corner_threshold=60, length_threshold=4.0,
                max_iterations=10, splice_threshold=45, path_precision=8
            )
            svg_str = vtracer.convert_raw_image_to_svg(png_bytes, img_format="png", **params)

        elif mode == "silhouette":
            buf = io.BytesIO()
            img.convert("RGB").save(buf, "PNG")
            png_bytes = buf.getvalue()
            params = dict(
                colormode="binary", hierarchical="cutout", mode="spline",
                filter_speckle=16, color_precision=8, layer_difference=16,
                corner_threshold=60, length_threshold=4.0,
                max_iterations=10, splice_threshold=45, path_precision=6
            )
            svg_str = vtracer.convert_raw_image_to_svg(png_bytes, img_format="png", **params)

        else:  # color — maximum quality pipeline with 3x upscale
            # First pass: get quantized flat-color version
            buf_orig = io.BytesIO()
            img.convert("RGB").save(buf_orig, "PNG")
            png_orig = buf_orig.getvalue()

            svg_q = vtracer.convert_raw_image_to_svg(
                png_orig, img_format="png",
                colormode="color", hierarchical="stacked", mode="spline",
                filter_speckle=16, color_precision=4, layer_difference=22,
                corner_threshold=80, length_threshold=8.0,
                max_iterations=10, splice_threshold=45, path_precision=8
            )

            # Second pass: 3x upscale of a median-filtered version → smoother curves
            img_med = img.convert("RGB").filter(ImageFilter.MedianFilter(3))
            W3, H3 = width * 3, height * 3
            img_3x = img_med.resize((W3, H3), Image.NEAREST)
            buf_3x = io.BytesIO()
            img_3x.save(buf_3x, "PNG")
            png_3x = buf_3x.getvalue()

            svg_str = vtracer.convert_raw_image_to_svg(
                png_3x, img_format="png",
                colormode="color", hierarchical="stacked", mode="spline",
                filter_speckle=4, color_precision=4, layer_difference=22,
                corner_threshold=85, length_threshold=24,
                max_iterations=10, splice_threshold=45, path_precision=8
            )
            # Fix SVG dimensions: paths are in 3x space, display at original size
            svg_str = _re.sub(
                r'<svg[^>]*>',
                f'<svg version="1.1" xmlns="http://www.w3.org/2000/svg" '
                f'viewBox="0 0 {W3} {H3}" width="{width}" height="{height}">',
                svg_str, count=1
            )

        return jsonify({
            "svg": svg_str,
            "svg_size": len(svg_str.encode("utf-8")),
            "orig_size": len(raw_bytes),
            "width": width,
            "height": height,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    if IS_CLOUD:
        print(f"\n{'='*55}")
        print("  OnBrandCraftz Command Center — CLOUD MODE")
        print(f"  Running on Railway, port {PORT}")
        print(f"  Password protection: {'ON' if CENTER_PASSWORD else 'OFF — set CENTER_PASSWORD env var!'}")
        print("="*55 + "\n")
    else:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "your-computer-ip"
        print(f"\n{'='*55}")
        print("  OnBrandCraftz Command Center")
        print(f"  This computer:  http://localhost:5055")
        print(f"  Phone / tablet: http://{local_ip}:5055")
        print("  (Both devices must be on the same Wi-Fi)")
        print("="*55 + "\n")

    app.run(host="0.0.0.0", port=PORT, debug=False, threaded=True)
