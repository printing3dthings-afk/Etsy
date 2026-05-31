#!/usr/bin/env python3
"""
OnBrandCraftz — Command Center
Local web app that lets you click buttons to run any shop automation script.
Live output streams back to the browser in real time.

Start it:  python command_center.py
Then open: http://localhost:5055
"""

import subprocess
import threading
import os
import sys
import json
import queue
import time
from flask import Flask, Response, request, render_template_string

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__)

# ── Command registry ──────────────────────────────────────────────────────────
# Organized by business function. Each command has:
#   id, label, cmd, description, flags (optional list of {flag, desc})

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
                "flags": []
            },
            {
                "id": "analytics",
                "label": "View Analytics Dashboard",
                "cmd": "python3 tools/analytics_tracker.py",
                "desc": "Pulls live shop stats from Etsy, stores snapshots, shows revenue trends and action items.",
                "flags": []
            },
            {
                "id": "audit_tags",
                "label": "Audit & Fix All Tags",
                "cmd": "python3 tools/audit_fix_wall_art_tags.py",
                "desc": "Scans all active wall art listings for tag violations (>20 chars, <13 tags, duplicates) and fixes them.",
                "flags": []
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
                "flags": []
            },
            {
                "id": "post_art_list",
                "label": "Art Schedule — Category List",
                "cmd": "python3 tools/post_scheduled_art.py --list",
                "desc": "Shows all 20 art categories in rotation order with subjects used per category.",
                "flags": []
            },
            {
                "id": "post_art_preview",
                "label": "Generate Next Art (Preview Only)",
                "cmd": "python3 tools/post_scheduled_art.py --preview",
                "desc": "Generates all listing images for the next category but does NOT post to Etsy. Review the output before going live.",
                "flags": []
            },
            {
                "id": "post_art_force",
                "label": "Post Next Art to Etsy NOW",
                "cmd": "python3 tools/post_scheduled_art.py --force",
                "desc": "Generates art and posts a live Etsy listing immediately, bypassing the schedule. Advances queue to next category.",
                "flags": []
            },
            {
                "id": "create_art_preview",
                "label": "Create Single Art Listing (Preview)",
                "cmd": "python3 tools/create_art_listing_new.py --preview",
                "desc": "Generates all 7 listing photos for a single new art listing. Review before posting.",
                "flags": []
            },
            {
                "id": "create_art_post",
                "label": "Create Single Art Listing (Post)",
                "cmd": "python3 tools/create_art_listing_new.py --post",
                "desc": "Generates art and photos then creates a live Etsy listing end-to-end.",
                "flags": []
            },
            {
                "id": "fetch_market",
                "label": "Refresh Market Reference Images",
                "cmd": "python3 tools/fetch_market_examples.py --refresh",
                "desc": "Re-downloads 10 reference images per category (200 total) from Etsy's live search. Updates market_references.html.",
                "flags": []
            },
            {
                "id": "upscale_art",
                "label": "Upscale Art Files",
                "cmd": "python3 tools/upscale_art.py",
                "desc": "Upscales any art file under 3000px to 4× resolution using Lanczos + sharpening. Required before listing.",
                "flags": []
            },
            {
                "id": "gen_print_sizes",
                "label": "Generate Print Size ZIPs",
                "cmd": "python3 tools/generate_print_sizes.py",
                "desc": "Creates multi-size print ZIPs (8 sizes, 300 DPI) for all art files. Upload ZIPs as Etsy digital downloads.",
                "flags": []
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
                "flags": []
            },
            {
                "id": "sticker_photos",
                "label": "Generate Sticker Pack Photos",
                "cmd": "python3 tools/gen_sticker_listing_photos.py",
                "desc": "Creates listing photos for the 6 standalone sticker pack listings using real sticker sheet images.",
                "flags": []
            },
            {
                "id": "gen_lifestyle",
                "label": "Generate Lifestyle Room Scene",
                "cmd": "python3 tools/gen_lifestyle_scene.py",
                "desc": "Generates an AI lifestyle room background then composites the real product art into it.",
                "flags": []
            },
            {
                "id": "shorten_titles",
                "label": "Shorten All Titles to ≤70 Chars",
                "cmd": "python3 tools/shorten_titles.py",
                "desc": "Trims all active listing titles to 70 characters (2026 Etsy algorithm rule — >70 chars = mobile penalty).",
                "flags": []
            },
            {
                "id": "ai_disclosure",
                "label": "Add AI Disclosure to Listings",
                "cmd": "python3 tools/add_ai_disclosure.py",
                "desc": "Adds mandatory Etsy AI disclosure text to all listings that are missing it (required since June 2025).",
                "flags": []
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
                "flags": []
            },
            {
                "id": "rebuild_sticker_pack",
                "label": "Rebuild Sticker Pack ZIP",
                "cmd": "python3 tools/rebuild_sticker_pack.py --pid DP1026",
                "desc": "Rebuilds the sticker pack ZIP for a planner and re-uploads to Etsy. Change --pid to DP1026/1027/1028/1029.",
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
                "flags": []
            },
            {
                "id": "tiktok_post",
                "label": "Post TikTok Content",
                "cmd": "python3 tools/tiktok_poster.py",
                "desc": "Posts the next scheduled video from data/tiktok_content_calendar.json to @onbrandcraftz.",
                "flags": []
            },
            {
                "id": "email_templates",
                "label": "Show Email Lead Magnet Templates",
                "cmd": "python3 tools/email_leadmagnet.py --templates",
                "desc": "Prints the welcome email sequence and lead magnet strategy for the email list.",
                "flags": []
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
                "flags": []
            },
            {
                "id": "etsy_messages",
                "label": "Show Message Templates",
                "cmd": "python3 tools/etsy_messages.py",
                "desc": "Prints the post-purchase message, thank-you coupon, and review request templates.",
                "flags": []
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
                "desc": "Re-runs the Etsy OAuth flow if the access token expires. Opens a browser for authorization.",
                "flags": []
            },
            {
                "id": "pinterest_oauth",
                "label": "Re-authorize Pinterest",
                "cmd": "python3 tools/pinterest_oauth.py",
                "desc": "Refreshes the Pinterest access token (expires daily — run this before posting to Pinterest).",
                "flags": []
            },
            {
                "id": "tiktok_oauth",
                "label": "Set Up TikTok",
                "cmd": "python3 tools/tiktok_oauth.py",
                "desc": "First-time TikTok OAuth setup. Requires browser. Gets access token for @onbrandcraftz.",
                "flags": []
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
                "desc": "Starts the OnBrandCraftz Agent Hub. All AI agents are available interactively.",
                "flags": []
            },
        ]
    },
]


# ── HTML template ─────────────────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>OnBrandCraftz — Command Center</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
         background:#f0ede9;color:#222;padding:0}
    .topbar{background:#1a1a1a;color:#fff;padding:16px 28px;display:flex;
            align-items:center;gap:14px;position:sticky;top:0;z-index:100;
            box-shadow:0 2px 8px rgba(0,0,0,.3)}
    .topbar h1{font-size:18px;font-weight:700;letter-spacing:-.3px}
    .topbar .sub{font-size:12px;color:#aaa;margin-top:2px}
    .topbar .status{margin-left:auto;font-size:12px;color:#4CAF50;
                    display:flex;align-items:center;gap:6px}
    .dot{width:8px;height:8px;border-radius:50%;background:#4CAF50;
         animation:pulse 2s infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
    .main{display:flex;min-height:calc(100vh - 56px)}
    .sidebar{width:220px;background:#fff;border-right:1px solid #e5e0da;
             padding:16px 0;flex-shrink:0;position:sticky;top:56px;
             height:calc(100vh - 56px);overflow-y:auto}
    .sidebar a{display:flex;align-items:center;gap:8px;padding:9px 18px;
               font-size:13px;color:#444;text-decoration:none;border-left:3px solid transparent;
               transition:all .15s}
    .sidebar a:hover,.sidebar a.active{background:#f7f5f2;color:#1a1a1a;
                                       border-left-color:var(--c)}
    .sidebar .icon{width:18px;text-align:center}
    .content{flex:1;padding:28px;max-width:960px}
    .section{margin-bottom:36px}
    .section-header{display:flex;align-items:center;gap:10px;margin-bottom:16px;
                    padding-bottom:10px;border-bottom:2px solid var(--c)}
    .section-header .sicon{font-size:20px}
    .section-header h2{font-size:15px;font-weight:700;color:#1a1a1a}
    .cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px}
    .card{background:#fff;border-radius:10px;padding:16px 18px;
          border:1px solid #e5e0da;
          box-shadow:0 1px 4px rgba(0,0,0,.06);transition:box-shadow .15s}
    .card:hover{box-shadow:0 3px 12px rgba(0,0,0,.12)}
    .card-label{font-size:13px;font-weight:600;color:#1a1a1a;margin-bottom:5px}
    .card-desc{font-size:12px;color:#666;line-height:1.5;margin-bottom:12px}
    .card-cmd{font-family:"Courier New",monospace;font-size:11px;
              background:#f5f3f0;border:1px solid #e5e0da;border-radius:5px;
              padding:6px 10px;color:#555;margin-bottom:10px;
              display:flex;align-items:center;gap:6px;cursor:pointer;
              user-select:all}
    .card-cmd:hover{background:#ece9e5}
    .copy-hint{font-size:10px;color:#aaa;margin-left:auto;flex-shrink:0}
    .btn-run{display:inline-flex;align-items:center;gap:6px;
             background:var(--c);color:#fff;border:none;border-radius:6px;
             padding:7px 14px;font-size:12px;font-weight:600;cursor:pointer;
             transition:filter .15s}
    .btn-run:hover{filter:brightness(1.12)}
    .btn-run:active{filter:brightness(.9)}
    .btn-run.running{background:#888;cursor:not-allowed}
    .flags{font-size:11px;color:#888;margin-top:6px}
    .flags span{background:#f0ede9;border-radius:4px;padding:2px 6px;
                margin-right:4px;font-family:monospace;font-size:10px}
    /* Output panel */
    #output-panel{position:fixed;bottom:0;left:0;right:0;
                  background:#1a1a1a;color:#e8e8e8;
                  height:0;transition:height .25s;overflow:hidden;z-index:200}
    #output-panel.open{height:300px}
    #output-header{display:flex;align-items:center;padding:8px 16px;
                   background:#111;border-top:2px solid var(--active-color,#4CAF50)}
    #output-title{font-size:13px;font-weight:600;color:#fff;flex:1}
    #btn-close{background:none;border:none;color:#aaa;font-size:18px;
               cursor:pointer;padding:0 4px}
    #btn-close:hover{color:#fff}
    #output-body{font-family:"Courier New",monospace;font-size:12px;
                 padding:12px 16px;height:calc(300px - 42px);
                 overflow-y:auto;white-space:pre-wrap;line-height:1.6}
    .out-ok{color:#81C784}
    .out-err{color:#EF9A9A}
    .out-info{color:#80DEEA}
    /* scrollbar */
    #output-body::-webkit-scrollbar{width:6px}
    #output-body::-webkit-scrollbar-track{background:#1a1a1a}
    #output-body::-webkit-scrollbar-thumb{background:#444;border-radius:3px}
  </style>
</head>
<body>

<div class="topbar">
  <div>
    <div class="h1" style="font-size:18px;font-weight:700">🏪 OnBrandCraftz Command Center</div>
    <div class="sub">Click any button to run — output streams live below</div>
  </div>
  <div class="status"><div class="dot"></div> Server running on localhost:5055</div>
</div>

<div class="main">
  <nav class="sidebar" id="sidebar">
    {% for section in commands %}
    <a href="#{{ section.id }}" style="--c:{{ section.color }}">
      <span class="icon">{{ section.icon }}</span>
      {{ section.category }}
    </a>
    {% endfor %}
  </nav>

  <div class="content">
    {% for section in commands %}
    <div class="section" id="{{ section.id }}" style="--c:{{ section.color }}">
      <div class="section-header">
        <span class="sicon">{{ section.icon }}</span>
        <h2>{{ section.category }}</h2>
      </div>
      <div class="cards">
        {% for cmd in section.commands %}
        <div class="card">
          <div class="card-label">{{ cmd.label }}</div>
          <div class="card-desc">{{ cmd.desc }}</div>
          <div class="card-cmd" onclick="copyCmd(this, '{{ cmd.cmd }}')" title="Click to copy">
            <span>{{ cmd.cmd }}</span>
            <span class="copy-hint">📋 copy</span>
          </div>
          {% if cmd.flags %}
          <div class="flags">
            Variants: {% for f in cmd.flags %}<span title="{{ f.desc }}">{{ f.flag }}</span>{% endfor %}
          </div>
          {% endif %}
          <br>
          <button class="btn-run" style="--c:{{ section.color }}"
                  onclick="runCmd('{{ cmd.id }}', '{{ cmd.cmd | replace("'", "\\'") }}', '{{ cmd.label | replace("'", "\\'") }}', '{{ section.color }}', this)">
            ▶ Run
          </button>
        </div>
        {% endfor %}
      </div>
    </div>
    {% endfor %}
  </div>
</div>

<!-- Output panel -->
<div id="output-panel">
  <div id="output-header">
    <span id="output-title">Output</span>
    <button id="btn-close" onclick="closeOutput()">✕</button>
  </div>
  <div id="output-body"></div>
</div>

<script>
let activeBtn = null;

function copyCmd(el, cmd) {
  navigator.clipboard.writeText(cmd).then(() => {
    const hint = el.querySelector('.copy-hint');
    hint.textContent = '✓ copied';
    setTimeout(() => hint.textContent = '📋 copy', 1500);
  });
}

function runCmd(id, cmd, label, color, btn) {
  const panel = document.getElementById('output-panel');
  const body = document.getElementById('output-body');
  const title = document.getElementById('output-title');
  const header = document.getElementById('output-header');

  // Reset previous button
  if (activeBtn && activeBtn !== btn) {
    activeBtn.textContent = '▶ Run';
    activeBtn.classList.remove('running');
    activeBtn.disabled = false;
  }
  activeBtn = btn;
  btn.textContent = '⏳ Running…';
  btn.classList.add('running');
  btn.disabled = true;

  body.innerHTML = '<span class="out-info">$ ' + cmd + '\\n\\n</span>';
  header.style.borderTopColor = color;
  title.textContent = label;
  panel.classList.add('open');
  body.scrollTop = 0;

  const es = new EventSource('/run?id=' + encodeURIComponent(id));
  es.onmessage = function(e) {
    const data = JSON.parse(e.data);
    if (data.done) {
      es.close();
      btn.textContent = data.ok ? '✓ Done' : '✗ Error';
      btn.classList.remove('running');
      setTimeout(() => {
        btn.textContent = '▶ Run';
        btn.disabled = false;
        activeBtn = null;
      }, 3000);
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
    btn.textContent = '▶ Run';
    btn.classList.remove('running');
    btn.disabled = false;
  };
}

function closeOutput() {
  document.getElementById('output-panel').classList.remove('open');
}

// Smooth scroll sidebar links
document.querySelectorAll('.sidebar a').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    document.querySelectorAll('.sidebar a').forEach(x => x.classList.remove('active'));
    a.classList.add('active');
    const target = document.querySelector(a.getAttribute('href'));
    if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
  });
});
</script>
</body>
</html>"""


# ── Running processes ─────────────────────────────────────────────────────────
_processes = {}


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
    return render_template_string(HTML, commands=sections)


@app.route("/run")
def run_command():
    cmd_id = request.args.get("id", "")
    cmd_def = _find_cmd(cmd_id)
    if not cmd_def:
        return Response("data: {\"done\":true,\"ok\":false}\n\n", mimetype="text/event-stream")

    cmd = cmd_def["cmd"]

    def generate():
        proc = subprocess.Popen(
            cmd,
            shell=True,
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
                for l in line.splitlines(keepends=True):
                    payload = json.dumps({"line": l, "err": is_err})
                    yield f"data: {payload}\n\n"

        proc.wait()
        ok = proc.returncode == 0
        yield f"data: {json.dumps({'done': True, 'ok': ok})}\n\n"

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


if __name__ == "__main__":
    print("\n" + "="*55)
    print("  OnBrandCraftz Command Center")
    print("  Open your browser to: http://localhost:5055")
    print("="*55 + "\n")
    app.run(host="127.0.0.1", port=5055, debug=False, threaded=True)
