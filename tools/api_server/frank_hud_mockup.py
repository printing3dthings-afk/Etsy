"""
FRANK Command Center — static clickable HTML/CSS/JS mockup (Build Order step 0.5).

No backend wiring. This is purely a visual sign-off artifact so Scott can react to the
look of the full landscape HUD (left nav + every panel from the reference screenshots,
rebranded FRANK) before any real engineering goes in underneath it. Served at /frank,
completely separate from the live production dashboard at / so there is zero risk to
the running Hub while this is reviewed.

The whole layout is built as a fixed 1440x900 "stage" that JS scales (and letterboxes)
to fit whatever viewport opens it — phone or desktop — so the HUD always renders at its
real proportions instead of the browser's mobile viewport squishing the columns.

Real wiring (live data, approval gate, relay, voice) is Step 1+ in the approved plan —
every nav tab/panel here is a placeholder shell with the real future data source noted
in a code comment, not invented numbers presented as fact. LLM Status only lists
providers we actually have wired (Anthropic, OpenAI, Etsy) — no fake Gemini/Groq/Ollama
tiles, per the "no fake tiles anywhere" rule in the plan.

Step 2 (in progress): wiring real data into this shell, panel by panel. The page is a
plain string template (not f-string/`.format()`, since the JS below is full of literal
`{}`) with a single `__APP_TOKEN__` placeholder substituted at request time by
`render_frank_hud()` — same bearer token used by the existing dashboard at `/`, just
injected via `str.replace()` instead of being baked in at module-import time, since this
template lives outside main.py and has no direct access to APP_TOKEN.
"""

import json

_FRANK_HUD_MOCKUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>FRANK — Command Center (mockup)</title>
<style>
:root{
  --bg:#070d16;--panel:#0f1f30;--panel2:#13283d;--border:#1c3349;
  --cyan:#3ad6ff;--cyan2:#8fefff;--gold:#C9A84C;--text:#e8edf2;--muted:#5d7891;
  --green:#4caf82;--red:#e05555;--amber:#e0a83a;
}
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;width:100%;overflow:hidden;background:var(--bg)}
body{color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:13px}

#stage-wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:var(--bg)}
#stage{
  position:relative;width:1440px;height:900px;flex-shrink:0;transform-origin:center center;
  background:radial-gradient(ellipse at 50% -10%, #0e2a44 0%, var(--bg) 55%);
  display:grid;grid-template-columns:226px 1fr;grid-template-rows:68px 1fr 54px;
}

/* ── corner brackets (sci-fi HUD accent) ── */
.brk{position:relative}
.brk::before,.brk::after{content:'';position:absolute;width:13px;height:13px;pointer-events:none;opacity:.55}
.brk::before{top:-1px;left:-1px;border-top:2px solid var(--cyan);border-left:2px solid var(--cyan);border-top-left-radius:6px}
.brk::after{bottom:-1px;right:-1px;border-bottom:2px solid var(--cyan);border-right:2px solid var(--cyan);border-bottom-right-radius:6px}

/* ── Header row ── */
.hdr-logo{grid-column:1;grid-row:1;display:flex;align-items:center;gap:10px;padding:0 16px;
  border-bottom:1px solid var(--border);border-right:1px solid var(--border);background:rgba(8,16,26,.7)}
.hdr-logo .hex{width:30px;height:30px;border:2px solid var(--cyan);border-radius:8px;display:flex;
  align-items:center;justify-content:center;color:var(--cyan2);font-size:15px;box-shadow:0 0 10px rgba(58,214,255,.5)}
.hdr-logo .lbl .l1{font-weight:800;letter-spacing:2px;color:var(--cyan2);font-size:15px;line-height:1.1;
  text-shadow:0 0 10px rgba(58,214,255,.55)}
.hdr-logo .lbl .l2{font-size:8.5px;letter-spacing:2px;color:var(--muted)}

.hdr-bar{grid-column:2;grid-row:1;display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;border-bottom:1px solid var(--border);background:rgba(8,16,26,.5)}
.status-pill{display:flex;align-items:center;gap:6px;font-size:10.5px;color:var(--green);
  border:1px solid rgba(76,175,130,.4);border-radius:20px;padding:4px 10px;background:rgba(76,175,130,.08);
  letter-spacing:.5px;white-space:nowrap}
.status-pill .dot{width:6px;height:6px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);animation:pulse 2s infinite;flex-shrink:0}
.hdr-bar .clockwrap{text-align:center}
.hdr-bar .clockwrap .d{font-size:10px;color:var(--muted);letter-spacing:.5px}
.hdr-bar .clockwrap .t{font-size:17px;color:var(--cyan2);font-weight:700;letter-spacing:1px}
.hdr-bar .right{display:flex;align-items:center;gap:10px}
.search{width:230px;background:var(--panel);border:1px solid var(--border);border-radius:8px;
  padding:6px 10px;color:var(--text);font-size:11px}
.icon-btn{width:30px;height:30px;border-radius:8px;border:1px solid var(--border);
  background:var(--panel);display:flex;align-items:center;justify-content:center;
  cursor:pointer;position:relative;color:var(--muted);font-size:13px;flex-shrink:0}
.icon-btn:hover{border-color:var(--cyan);color:var(--cyan2)}
.badge{position:absolute;top:-5px;right:-5px;background:var(--cyan);color:#06141f;
  font-size:9px;font-weight:700;border-radius:8px;min-width:15px;height:15px;
  display:flex;align-items:center;justify-content:center;padding:0 3px}
.operator{display:flex;align-items:center;gap:7px;border:1px solid var(--border);border-radius:20px;
  padding:3px 10px 3px 3px;background:var(--panel)}
.operator .av{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#8a6d2b);
  display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#0a1420;flex-shrink:0}
.operator .ol1{font-size:11px;font-weight:600;line-height:1.1}
.operator .ol2{font-size:8.5px;color:var(--muted);letter-spacing:.5px}

/* ── Sidebar ── */
.sidebar{grid-column:1;grid-row:2;border-right:1px solid var(--border);background:rgba(8,16,26,.55);
  display:flex;flex-direction:column;padding:14px 10px;overflow:hidden}
.nav-section{font-size:9.5px;letter-spacing:1.5px;color:var(--muted);margin:12px 10px 6px;text-transform:uppercase}
.nav-section:first-child{margin-top:2px}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:8px;
  cursor:pointer;color:var(--muted);font-size:12.5px;margin-bottom:2px;position:relative}
.nav-item .ic{width:16px;text-align:center;font-size:13px}
.nav-item:hover{background:var(--panel);color:var(--text)}
.nav-item.active{background:linear-gradient(90deg,rgba(58,214,255,.18),transparent);
  color:var(--cyan2);border-left:2px solid var(--cyan)}
.nav-item .nbadge{margin-left:auto;background:var(--panel2);color:var(--cyan2);
  font-size:9.5px;font-weight:700;border-radius:9px;padding:1px 7px;border:1px solid var(--border)}

.voice-widget{margin-top:auto;border:1px solid var(--border);border-radius:12px;padding:14px 10px;
  background:var(--panel);text-align:center}
.voice-widget .vw-title{font-size:9.5px;letter-spacing:1.5px;color:var(--muted);margin-bottom:8px}
.wave-row{display:flex;align-items:center;justify-content:center;gap:3px;height:22px;margin-bottom:10px}
.wave-row span{width:3px;background:var(--cyan);border-radius:2px;animation:wave 1.1s ease-in-out infinite}
.mic-circle{width:78px;height:78px;border-radius:50%;margin:0 auto 8px;display:flex;align-items:center;
  justify-content:center;cursor:pointer;background:radial-gradient(circle,rgba(58,214,255,.18),transparent 70%);
  border:2px solid rgba(58,214,255,.5);font-size:26px;color:var(--cyan2);
  box-shadow:0 0 22px rgba(58,214,255,.35), inset 0 0 18px rgba(58,214,255,.15)}
.mic-circle.live{animation:micpulse 1.2s ease-in-out infinite}
.voice-widget .vw-sub{font-size:10px;color:var(--muted);margin-bottom:2px}
.voice-widget .vw-tap{font-size:11px;color:var(--cyan2);letter-spacing:1px;font-weight:700}
.focus-btn{margin-top:12px;width:100%;background:transparent;border:1px solid var(--border);
  color:var(--muted);border-radius:20px;padding:8px;font-size:10.5px;letter-spacing:.5px;cursor:pointer}
.focus-btn.on{color:var(--amber);border-color:rgba(224,168,58,.5);background:rgba(224,168,58,.08)}

/* ── Main content ── */
.main{grid-column:2;grid-row:2;display:flex;flex-direction:column;gap:12px;padding:12px;overflow:hidden}
.mrow{display:flex;gap:12px;min-height:0}
.mrow.rowA{flex:1.25}
.mrow.rowB{flex:1}
.mrow.rowC{flex:1}

.panel{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:12px 14px;
  display:flex;flex-direction:column;overflow:hidden;min-height:0}
.panel-title{font-size:10.5px;letter-spacing:1.5px;color:var(--cyan2);text-transform:uppercase;
  margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.panel-title .src{font-size:8.5px;color:var(--muted);text-transform:none;letter-spacing:0;font-weight:400}
.panel-title .lnk{font-size:9px;color:var(--cyan);text-transform:none;letter-spacing:0;cursor:pointer}
.panel-body{overflow-y:auto;min-height:0;flex:1}

/* Row A: AI Core Overview | Orb Hero | Live Intelligence Feed */
.col-aicore{flex:0 0 218px}
.col-orb{flex:1 1 auto}
.col-feed{flex:0 0 270px}

.core-row{display:flex;align-items:center;justify-content:space-between;padding:7px 0;
  border-bottom:1px solid var(--border);font-size:11.5px}
.core-row:last-child{border-bottom:none}
.core-row .lab{display:flex;align-items:center;gap:7px;color:var(--text)}
.core-row .lab .dotc{width:6px;height:6px;border-radius:50%;background:var(--green);flex-shrink:0}
.core-row .v{color:var(--green);font-weight:600;font-size:10.5px}
.core-row .v.warn{color:var(--amber)}
.core-row .v.err{color:var(--red)}
.core-row .lab .dotc.warn{background:var(--amber)}
.core-row .lab .dotc.err{background:var(--red)}
.core-row .sub{font-size:9.5px;color:var(--muted);display:block}

.orb-hero{align-items:center;justify-content:center;position:relative;
  background:
    radial-gradient(circle at 50% 38%, rgba(58,214,255,.14), transparent 60%),
    radial-gradient(rgba(58,214,255,.10) 1px, transparent 1px);
  background-size:auto, 22px 22px;background-color:var(--panel)}
.orb-hero-stage{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;width:100%}
canvas#orb{cursor:pointer}
.orb-overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;
  pointer-events:none;width:100%}
.orb-overlay .o1{font-size:30px;font-weight:800;letter-spacing:6px;color:#eafcff;
  text-shadow:0 0 18px rgba(122,232,255,.85),0 0 40px rgba(58,214,255,.5)}
.orb-overlay .o2{font-size:11px;letter-spacing:5px;color:var(--cyan2);margin-top:2px}
.orb-overlay .o3{font-size:9px;letter-spacing:2px;color:var(--muted);margin-top:8px}
.orb-state{margin-top:8px;font-size:10.5px;color:var(--muted);letter-spacing:1px}
.orb-hint{position:absolute;bottom:8px;font-size:9.5px;color:var(--muted);opacity:.6;letter-spacing:.5px}

.feed-item{padding:7px 0;border-bottom:1px solid var(--border);font-size:11px;color:var(--text);
  display:flex;justify-content:space-between;gap:6px}
.feed-item .ftxt{flex:1}
.feed-item .t{color:var(--muted);font-size:9px;margin-top:2px}
.feed-tag{font-size:8px;font-weight:700;letter-spacing:.5px;border-radius:5px;padding:1px 5px;flex-shrink:0;height:fit-content}
.feed-tag.info{background:rgba(58,214,255,.15);color:var(--cyan2)}
.feed-tag.warn{background:rgba(224,168,58,.15);color:var(--amber)}
.feed-tag.tip{background:rgba(76,175,130,.15);color:var(--green)}

/* Row B: Active Agents | Mission Timeline | Quick Commands */
.col-agents{flex:1.5}
.col-timeline{flex:1}
.col-quick{flex:0.85}

.agents-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;flex:1}
.agent-tile{background:var(--panel2);border:1px solid var(--border);border-radius:10px;
  padding:9px 10px;font-size:10.5px;display:flex;flex-direction:column;gap:5px}
.agent-tile .top{display:flex;align-items:center;gap:6px}
.agent-tile .ic{width:20px;height:20px;border-radius:6px;background:rgba(58,214,255,.15);
  display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--cyan2);flex-shrink:0}
.agent-tile.idle .ic{background:rgba(93,120,145,.15);color:var(--muted)}
.agent-tile .name{font-weight:600;color:var(--text);font-size:10.5px;line-height:1.2}
.agent-tile .stat{color:var(--green);font-size:9.5px;display:flex;align-items:center;gap:4px}
.agent-tile .stat .d{width:5px;height:5px;border-radius:50%;background:var(--green)}
.agent-tile.idle .stat{color:var(--muted)}
.agent-tile.idle .stat .d{background:var(--muted)}

.tl-item{display:flex;gap:9px;padding:6px 0;border-bottom:1px solid var(--border);font-size:11px}
.tl-item:last-child{border-bottom:none}
.tl-time{color:var(--cyan2);font-size:9.5px;width:48px;flex-shrink:0;line-height:1.3}
.tl-dotcol{display:flex;flex-direction:column;align-items:center;flex-shrink:0}
.tl-dotcol .d{width:7px;height:7px;border-radius:50%;background:var(--cyan);margin-top:3px}
.tl-txt .ttl{color:var(--text)}
.tl-txt .sub{color:var(--muted);font-size:9.5px}

.qc-btn{display:flex;align-items:center;gap:8px;width:100%;text-align:left;background:var(--panel2);
  border:1px solid var(--border);color:var(--text);border-radius:8px;padding:8px 10px;margin-bottom:7px;
  font-size:11px;cursor:pointer}
.qc-btn:hover{border-color:var(--cyan)}
.qc-btn .qic{width:18px;height:18px;border-radius:50%;background:rgba(58,214,255,.18);color:var(--cyan2);
  display:flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0}

/* Row C: System Monitor | Memory Insights | LLM Status */
.col-sysmon{flex:1}
.col-meminsights{flex:1}
.col-shop{flex:1.3}

.gauge-row{display:flex;gap:10px;flex:1;align-items:center;justify-content:space-around}
.gauge{width:78px;height:78px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  position:relative;flex-shrink:0}
.gauge .ring{position:absolute;inset:0;border-radius:50%}
.gauge .inner{position:relative;width:56px;height:56px;border-radius:50%;background:var(--panel2);
  display:flex;flex-direction:column;align-items:center;justify-content:center}
.gauge .inner .num{font-size:13px;font-weight:700;color:var(--cyan2)}
.gauge .inner .lab{font-size:8px;color:var(--muted);letter-spacing:.5px}

.mem-row{display:flex;gap:10px;flex:1;min-height:0}
.mem-canvas-wrap{flex:1;min-height:0;border-radius:8px;background:var(--panel2);border:1px solid var(--border)}
.mem-stats{display:flex;flex-direction:column;justify-content:center;gap:6px;flex:0 0 86px}
.mem-stat .n{font-size:14px;font-weight:700;color:var(--cyan2)}
.mem-stat .l{font-size:8.5px;color:var(--muted);letter-spacing:.5px}

.shop-spark-row{display:flex;gap:8px;flex:1;min-height:0}
.shop-spark-card{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:10px;
  padding:7px 9px;display:flex;flex-direction:column;gap:2px;min-height:0;overflow:hidden}
.shop-spark-card .ssc-lab{font-size:9px;color:var(--muted);letter-spacing:.4px}
.shop-spark-card .ssc-val{font-size:14px;font-weight:700;color:var(--cyan2)}
.shop-spark-card .ssc-delta{font-size:9px;margin-top:1px}
.shop-spark-card .ssc-spark{flex:1;min-height:0}

.shop-chip-row{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:8px}
.shop-chip{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:6px 7px;
  display:flex;flex-direction:column;gap:3px;justify-content:center}
.shop-chip .nm{font-size:9px;color:var(--muted);letter-spacing:.3px}
.shop-chip .v{font-size:12.5px;font-weight:700;color:var(--text)}

/* Studio tab placeholder */
.studio-grid{display:flex;gap:14px;height:100%}
video{width:100%;border-radius:10px;background:#000;display:block}
.studio-list-item{padding:8px;border:1px solid var(--border);border-radius:8px;margin-bottom:6px;font-size:11px}

/* Generic placeholder screen */
.placeholder-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--muted);text-align:center;gap:8px}
.placeholder-screen .big{font-size:14px;color:var(--text);letter-spacing:1px}
.placeholder-screen .small{font-size:11px;max-width:440px}

/* Bottom bar */
.bottombar{grid-column:1/3;grid-row:3;border-top:1px solid var(--border);background:rgba(8,16,26,.6);
  display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-size:10.5px;color:var(--muted)}
.bb-left{display:flex;align-items:center;gap:16px}
.bb-left .it{display:flex;align-items:center;gap:5px}
.bb-center{display:flex;align-items:center;gap:14px;flex:1;justify-content:center}
.dots-line{flex:1;max-width:200px;height:1px;background:repeating-linear-gradient(90deg,var(--cyan) 0 4px,transparent 4px 9px);opacity:.5}
.talk-pill{display:flex;flex-direction:column;align-items:center;gap:2px;background:var(--panel);
  border:1px solid rgba(58,214,255,.4);border-radius:20px;padding:6px 22px;cursor:pointer;
  box-shadow:0 0 16px rgba(58,214,255,.15)}
.talk-pill .row1{display:flex;align-items:center;gap:10px}
.talk-pill .label{color:var(--cyan2);font-weight:700;letter-spacing:1.5px;font-size:11px}
.talk-pill .sub{font-size:9px;color:var(--muted);letter-spacing:.5px}
.mini-wave{display:flex;align-items:center;gap:2px;height:13px}
.mini-wave span{width:2px;background:var(--cyan);border-radius:1px;animation:wave 1s ease-in-out infinite}
.brief-btn{background:var(--panel);border:1px solid var(--border);color:var(--cyan2);
  border-radius:8px;padding:6px 14px;font-size:10.5px;cursor:pointer;white-space:nowrap}

@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes wave{0%,100%{height:4px}50%{height:16px}}
@keyframes micpulse{0%,100%{box-shadow:0 0 22px rgba(58,214,255,.35), inset 0 0 18px rgba(58,214,255,.15)}
  50%{box-shadow:0 0 34px rgba(122,232,255,.6), inset 0 0 22px rgba(122,232,255,.3)}}

.screen{display:none;grid-column:2;grid-row:2;overflow:hidden;padding:12px}
.screen.active{display:block}
</style>
</head>
<body>
<div id="stage-wrap"><div id="stage">

  <div class="hdr-logo brk">
    <div class="hex">⬡</div>
    <div class="lbl"><div class="l1">FRANK</div><div class="l2">COMMAND CENTER</div></div>
  </div>

  <div class="hdr-bar">
    <div class="status-pill"><span class="dot"></span>SYSTEM STATUS &nbsp;● OPTIMAL</div>
    <div class="clockwrap"><div class="d" id="dt">--</div><div class="t" id="clk">--:--</div></div>
    <div class="right">
      <input class="search" placeholder="Search listings, orders, tools, knowledge base…">
      <div class="icon-btn">▦</div>
      <div class="icon-btn">🔔<span class="badge">3</span></div>
      <div class="icon-btn">⚙</div>
      <div class="operator"><div class="av">S</div><div><div class="ol1">Scott</div><div class="ol2">OWNER</div></div></div>
    </div>
  </div>

  <div class="sidebar">
    <div class="nav-section">Frank</div>
    <div class="nav-item active" data-screen="cmd"><span class="ic">⌂</span>Command Center</div>
    <div class="nav-item" data-screen="core"><span class="ic">◎</span>AI Core</div>
    <div class="nav-item" data-screen="agents"><span class="ic">⚙</span>Agents</div>
    <div class="nav-item" data-screen="tasks"><span class="ic">☑</span>Tasks<span class="nbadge" id="badge-tasks" style="display:none">—</span></div>
    <div class="nav-item" data-screen="calendar"><span class="ic">▦</span>Calendar</div>

    <div class="nav-section">Knowledge</div>
    <div class="nav-item" data-screen="memory"><span class="ic">✦</span>Memory</div>
    <div class="nav-item" data-screen="conversations"><span class="ic">💬</span>Conversations<span class="nbadge">12</span></div>
    <div class="nav-item" data-screen="kb"><span class="ic">📚</span>Knowledge Base</div>

    <div class="nav-section">Tools</div>
    <div class="nav-item" data-screen="tools"><span class="ic">🛠</span>Tools &amp; Skills<span class="nbadge" id="badge-tools" style="display:none">—</span></div>
    <div class="nav-item" data-screen="workflows"><span class="ic">⇄</span>Workflows</div>
    <div class="nav-item" data-screen="studio"><span class="ic">▶</span>Studio</div>

    <div class="nav-section">Shop</div>
    <div class="nav-item" data-screen="listings"><span class="ic">🏷</span>Listings</div>
    <div class="nav-item" data-screen="products"><span class="ic">📦</span>Products</div>
    <div class="nav-item" data-screen="brandkit"><span class="ic">🎨</span>Brand Kit</div>
    <div class="nav-item" data-screen="files"><span class="ic">🗂</span>Files</div>
    <div class="nav-item" data-screen="connections"><span class="ic">🔌</span>Connections</div>
    <div class="nav-item" data-screen="security"><span class="ic">🛡</span>Security</div>

    <div class="voice-widget">
      <div class="vw-title">VOICE STATUS</div>
      <div class="wave-row" id="sidebar-wave">
        <span style="animation-delay:0s"></span><span style="animation-delay:.1s"></span>
        <span style="animation-delay:.2s"></span><span style="animation-delay:.3s"></span>
        <span style="animation-delay:.4s"></span><span style="animation-delay:.3s"></span>
        <span style="animation-delay:.2s"></span><span style="animation-delay:.1s"></span>
      </div>
      <div class="mic-circle" id="tap-speak">🎙</div>
      <div class="vw-sub" id="vw-sub-text">Tap to speak</div>
      <div class="vw-tap">FRANK</div>
      <button class="focus-btn" id="focus-toggle">FOCUS MODE: OFF</button>
    </div>
  </div>

  <!-- ══════════ COMMAND CENTER (home) ══════════ -->
  <div class="screen active" id="screen-cmd">
    <div class="main">

      <div class="mrow rowA">
        <div class="panel brk col-aicore">
          <div class="panel-title">AI Core Overview <span class="src">/health</span></div>
          <div class="panel-body">
            <div class="core-row"><span class="lab"><span class="dotc"></span>AI Core</span><span class="v" id="ac-core">—</span></div>
            <div class="core-row"><span class="lab"><span class="dotc"></span>Memory</span><span class="v" id="ac-memory">—</span></div>
            <div class="core-row" id="ac-voice-row"><span class="lab" id="ac-voice-lab"><span class="dotc" id="ac-voice-dot"></span>Voice</span><span class="v" id="ac-voice">—</span></div>
            <div class="core-row"><span class="lab"><span class="dotc"></span>Agents</span><span class="v" id="ac-agents">—</span></div>
            <div class="core-row"><span class="lab"><span class="dotc"></span>LLMs</span><span class="v" id="ac-llms">—</span></div>
            <div class="core-row"><span class="lab"><span class="dotc"></span>System</span><span class="v" id="ac-system">—</span></div>
          </div>
        </div>

        <div class="panel brk orb-hero col-orb">
          <div class="orb-hero-stage">
            <canvas id="orb" width="300" height="300"></canvas>
            <div class="orb-overlay">
              <div class="o1">FRANK</div>
              <div class="o2">COMMAND CORE</div>
              <div class="o3">v1.0.0 · MOCKUP</div>
            </div>
          </div>
          <div class="orb-state" id="orb-state">IDLE — slow ambient rotation</div>
          <div class="orb-hint">click the orb (or Tap to Speak) to preview the audio-reactive "speaking" state</div>
        </div>

        <div class="panel brk col-feed">
          <div class="panel-title">Live Intelligence Feed <span class="src">queue+audits+todos</span></div>
          <div class="panel-body">
            <div class="feed-item"><div class="ftxt">Quality audit flagged 1 listing for review<div class="t">2m ago</div></div><span class="feed-tag warn">WARN</span></div>
            <div class="feed-item"><div class="ftxt">3 actions pending approval in queue<div class="t">14m ago</div></div><span class="feed-tag tip">TIP</span></div>
            <div class="feed-item"><div class="ftxt">Token sync refreshed Etsy access token<div class="t">41m ago</div></div><span class="feed-tag info">INFO</span></div>
            <div class="feed-item"><div class="ftxt">Autoresponder cleared support queue<div class="t">1h ago</div></div><span class="feed-tag info">INFO</span></div>
          </div>
        </div>
      </div>

      <div class="mrow rowB">
        <div class="panel brk col-agents">
          <div class="panel-title">Active Agents <span class="lnk" onclick="showScreen('agents')" style="cursor:pointer">View All ›</span></div>
          <div class="agents-grid" id="cmd-agents-grid">
            <div class="agent-tile idle"><div class="top"><div class="ic">⋯</div><div class="name">Loading…</div></div><div class="stat"><span class="d"></span>—</div></div>
          </div>
        </div>

        <div class="panel brk col-timeline">
          <div class="panel-title">Mission Timeline <span class="src">/api/todos</span></div>
          <div class="panel-body">
            <div class="tl-item"><div class="tl-time">FRI</div><div class="tl-dotcol"><span class="d"></span></div><div class="tl-txt"><div class="ttl">Shop health review</div><div class="sub">weekly cadence</div></div></div>
            <div class="tl-item"><div class="tl-time">—</div><div class="tl-dotcol"><span class="d"></span></div><div class="tl-txt"><div class="ttl">Restock 3D print queue</div><div class="sub">open todo</div></div></div>
            <div class="tl-item"><div class="tl-time">JUL</div><div class="tl-dotcol"><span class="d"></span></div><div class="tl-txt"><div class="ttl">Update seasonal keywords</div><div class="sub">back to school</div></div></div>
          </div>
          <div class="panel-title" style="margin-top:6px;margin-bottom:0"><span class="lnk" style="margin-left:auto">View Full Schedule ›</span></div>
        </div>

        <div class="panel brk col-quick">
          <div class="panel-title">Quick Commands</div>
          <button class="qc-btn"><span class="qic">+</span>Start New Task</button>
          <button class="qc-btn"><span class="qic">▦</span>Open Calendar</button>
          <button class="qc-btn"><span class="qic">✓</span>Run Health Check</button>
          <button class="qc-btn"><span class="qic">⇄</span>Run Workflow</button>
        </div>
      </div>

      <div class="mrow rowC">
        <div class="panel brk col-sysmon">
          <div class="panel-title">System Monitor <span class="src">server stats</span></div>
          <div class="gauge-row">
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 22%, var(--border) 22% 100%)"></div><div class="inner"><div class="num">22%</div><div class="lab">CPU</div></div></div>
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 54%, var(--border) 54% 100%)"></div><div class="inner"><div class="num">54%</div><div class="lab">RAM</div></div></div>
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 40%, var(--border) 40% 100%)"></div><div class="inner"><div class="num">40%</div><div class="lab">DISK</div></div></div>
          </div>
        </div>

        <div class="panel brk col-meminsights">
          <div class="panel-title">Memory Insights <span class="lnk">View Memory Map ›</span></div>
          <div class="mem-row">
            <div class="mem-canvas-wrap"><canvas id="mem-canvas" width="220" height="90" style="width:100%;height:100%"></canvas></div>
            <div class="mem-stats">
              <div class="mem-stat"><div class="n">—</div><div class="l">MEMORIES</div></div>
              <div class="mem-stat"><div class="n">—</div><div class="l">SESSION TURNS</div></div>
              <div class="mem-stat"><div class="n">—</div><div class="l">TOOL CALLS</div></div>
            </div>
          </div>
        </div>

        <div class="panel brk col-shop">
          <div class="panel-title">Shop Performance <span class="src">/api/analytics + /api/metrics</span></div>
          <div class="shop-spark-row" id="shop-spark-row">
            <div class="shop-spark-card"><div class="ssc-lab">Revenue · 30d</div><div class="ssc-val">—</div></div>
            <div class="shop-spark-card"><div class="ssc-lab">Orders · 30d</div><div class="ssc-val">—</div></div>
          </div>
          <div class="shop-chip-row" id="shop-chip-row">
            <div class="shop-chip"><div class="nm">Listings</div><div class="v">—</div></div>
            <div class="shop-chip"><div class="nm">Total Sales</div><div class="v">—</div></div>
            <div class="shop-chip"><div class="nm">All-Time Revenue</div><div class="v">—</div></div>
          </div>
        </div>
      </div>

    </div>
  </div>

  <!-- ══════════ AI CORE — real data: /health + /api/credentials/status ══════════ -->
  <div class="screen" id="screen-core">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">AI Core <span class="src">/health + /api/credentials/status</span></div>
      <div class="panel-body" id="core-detail">
        <div class="core-row"><span class="lab"><span class="dotc"></span>Loading…</span><span class="v">—</span></div>
      </div>
    </div>
  </div>

  <!-- ══════════ AGENTS — real data: /api/agents/status (live-status registry) ══════════ -->
  <div class="screen" id="screen-agents">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Agents <span class="src">/api/agents/status — every tile below is a real loop or honestly marked not_built</span></div>
      <div class="agents-grid" id="agents-grid-full" style="margin-top:14px">
        <div class="agent-tile idle"><div class="top"><div class="ic">⋯</div><div class="name">Loading…</div></div><div class="stat"><span class="d"></span>—</div></div>
      </div>
    </div>
  </div>

  <!-- ══════════ TASKS — real data: /api/todos ══════════ -->
  <div class="screen" id="screen-tasks">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Tasks <span class="src">/api/todos</span></div>
      <div id="tasks-list" style="margin-top:10px;overflow-y:auto;max-height:760px">
        <div style="color:var(--muted);font-size:12px">Loading…</div>
      </div>
    </div>
  </div>

  <div class="screen" id="screen-calendar"><div class="placeholder-screen"><div class="big">CALENDAR</div><div class="small">Combines todo due dates + CLAUDE.md's weekly/monthly/quarterly cadence + Seasonal Keyword Calendar. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-memory"><div class="placeholder-screen"><div class="big">MEMORY</div><div class="small">Constellation of real chat_messages + log_learning + knowledge_base docs — counts from the DB, never invented. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-conversations"><div class="placeholder-screen"><div class="big">CONVERSATIONS</div><div class="small">Searchable chat_messages history. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-kb"><div class="placeholder-screen"><div class="big">KNOWLEDGE BASE</div><div class="small">Browse/search reader for the real markdown docs in data/knowledge_base/. Built in Step 2.</div></div></div>

  <!-- ══════════ TOOLS & SKILLS — real data: /api/tools/list (live AGENT_TOOLS) ══════════ -->
  <div class="screen" id="screen-tools">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Tools &amp; Skills <span class="src">/api/tools/list — live AGENT_TOOLS registry</span></div>
      <div id="tools-list" style="margin-top:10px;overflow-y:auto;max-height:760px">
        <div style="color:var(--muted);font-size:12px">Loading…</div>
      </div>
    </div>
  </div>

  <div class="screen" id="screen-workflows"><div class="placeholder-screen"><div class="big">WORKFLOWS</div><div class="small">Runnable workflow list — each Run stages through the existing approval gate. Built in Step 2.</div></div></div>

  <div class="screen" id="screen-listings"><div class="placeholder-screen"><div class="big">LISTINGS</div><div class="small">Carried over from the live Hub's listings browser — loadListings() in main.py:1592, real Etsy listings via list_listings/get_listing. Restyled into the HUD shell in Step 2.</div></div></div>
  <div class="screen" id="screen-products"><div class="placeholder-screen"><div class="big">PRODUCTS</div><div class="small">Carried over from the live Hub's product catalog — loadProductIndex() in main.py:2263, the DP1026–1029 etc. index. Restyled into the HUD shell in Step 2.</div></div></div>
  <div class="screen" id="screen-brandkit"><div class="placeholder-screen"><div class="big">BRAND KIT</div><div class="small">Carried over from the live Hub — _renderBrandKit() in main.py:2217, color palettes, listing standards, pricing tiers from CLAUDE.md. Restyled into the HUD shell in Step 2.</div></div></div>
  <div class="screen" id="screen-files"><div class="placeholder-screen"><div class="big">FILES</div><div class="small">Carried over from the live Hub's file browser — loadFiles() in main.py:2455, real files over data/digital_products/ and backups. Restyled into the HUD shell in Step 2.</div></div></div>
  <div class="screen" id="screen-connections"><div class="placeholder-screen"><div class="big">CONNECTIONS</div><div class="small">Carried over from the live Hub — loadCredentials() in main.py:2349, live API credential/token status, plus the Platform Connections Roadmap (Pinterest/Instagram/Facebook/TikTok/OneDrive, main.py:2280-2394) honestly marked not-yet-built. Restyled into the HUD shell in Step 2.</div></div></div>
  <div class="screen" id="screen-security"><div class="placeholder-screen"><div class="big">SECURITY</div><div class="small">Carried over from the live Hub — _renderSecurityPosture() in main.py:2391. Restyled into the HUD shell in Step 2.</div></div></div>

  <div class="screen" id="screen-studio">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Studio — Video Preview &amp; Generation <span class="src">/api/files (new generate_listing_video tool)</span></div>
      <div class="studio-grid">
        <div style="flex:1">
          <video controls poster="" style="aspect-ratio:16/9"></video>
          <div style="margin-top:10px;color:var(--muted);font-size:11px">No videos generated yet. Player wired to /api/files in Step 3.</div>
        </div>
        <div style="flex:0 0 220px">
          <div class="panel-title" style="margin-top:0">Generated Videos</div>
          <div class="studio-list-item">— none yet —</div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottombar">
    <div class="bb-left">
      <div class="it">📍 Local</div>
      <div class="it">⛅ —</div>
      <div class="it">🌐 Relay: not built</div>
    </div>
    <div class="bb-center">
      <span class="dots-line"></span>
      <div class="talk-pill" id="talk-pill">
        <div class="row1">
          <div class="mini-wave"><span></span><span></span><span></span><span></span></div>
          <span class="label">TALK TO FRANK</span>
          <div class="mini-wave"><span></span><span></span><span></span><span></span></div>
        </div>
        <div class="sub" id="talk-sub">tap to speak</div>
      </div>
      <span class="dots-line"></span>
    </div>
    <button class="brief-btn">Executive Briefing</button>
  </div>

</div></div>

<script>
// ── Auto-scale the fixed 1440x900 stage to fit any viewport (phone or desktop) ──
const STAGE_W = 1440, STAGE_H = 900;
const stage = document.getElementById('stage');
function fitStage(){
  const scale = Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H);
  stage.style.transform = 'scale(' + scale + ')';
}
window.addEventListener('resize', fitStage);
fitStage();

// ── Real data wiring (Step 2) — same bearer token + fetch pattern as the live
// dashboard at /, injected into this template at request time. ──
const BASE = location.origin;
const TOKEN = __APP_TOKEN__;
function fetchWithTimeout(url, opts, ms=12000){
  const c = new AbortController();
  const t = setTimeout(()=>c.abort(), ms);
  return fetch(url, {...opts, signal: c.signal}).finally(()=>clearTimeout(t));
}
function authGet(path, ms=15000){
  return fetchWithTimeout(BASE+path, {headers:{Authorization:'Bearer '+TOKEN}}, ms);
}
function escHtml(s){
  return String(s==null?'':s).replace(/[&<>"']/g, c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
}

// ── Nav switching — also called directly by in-panel links like
// "View All ›" / "Manage Providers ›", not just the sidebar. ──
function showScreen(name){
  document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active'));
  const navItem = document.querySelector('.nav-item[data-screen="'+name+'"]');
  if(navItem) navItem.classList.add('active');
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  const el = document.getElementById('screen-'+name);
  if(el) el.classList.add('active');
}
document.querySelectorAll('.nav-item').forEach(item=>{
  item.addEventListener('click',()=>showScreen(item.dataset.screen));
});

// ── Agents — real data from /api/agents/status (live-status registry).
// Every tile is a real loop or honestly marked not_built/offline; never invented. ──
function renderAgentTile(a){
  const ok = a.status === 'ok';
  const err = a.status === 'error';
  const cls = 'agent-tile' + (ok ? '' : ' idle');
  const dotStyle = err ? ' style="background:var(--red)"' : '';
  const statStyle = err ? ' style="color:var(--red)"' : '';
  const icon = a.built ? '⚙' : '⋯';
  return '<div class="'+cls+'"><div class="top"><div class="ic">'+icon+'</div><div class="name">'+escHtml(a.label)+'</div></div>'+
    '<div class="stat"'+statStyle+'><span class="d"'+dotStyle+'></span>'+escHtml(a.detail||a.status)+'</div></div>';
}
async function loadAgents(){
  const cmdGrid = document.getElementById('cmd-agents-grid');
  const fullGrid = document.getElementById('agents-grid-full');
  try{
    const r = await authGet('/api/agents/status');
    const d = await r.json();
    const tiles = d.agents.map(renderAgentTile).join('');
    if(cmdGrid) cmdGrid.innerHTML = tiles;
    if(fullGrid) fullGrid.innerHTML = tiles;
    const acAgents = document.getElementById('ac-agents');
    if(acAgents) acAgents.textContent = d.running_count + '/' + d.total_count + ' running';
    const relay = d.agents.find(a=>a.name==='local_relay');
    const voiceEl = document.getElementById('ac-voice');
    const voiceDot = document.getElementById('ac-voice-dot');
    if(relay && voiceEl){
      const state = relay.status==='ok' ? '' : (relay.status==='error' ? ' err' : ' warn');
      voiceEl.textContent = relay.status==='ok' ? 'Online' : (relay.status==='error' ? 'Killed' : 'Offline — not built yet');
      voiceEl.className = 'v' + state;
      if(voiceDot) voiceDot.className = 'dotc' + state;
    }
  }catch(e){
    const msg = '<div style="color:var(--red);font-size:11px;padding:8px">Agents offline: '+escHtml(e.message)+'</div>';
    if(cmdGrid) cmdGrid.innerHTML = msg;
    if(fullGrid) fullGrid.innerHTML = msg;
  }
}

// ── LLM Status + AI Core — real data from /api/credentials/status + /health ──
async function loadCredentialsAndHealth(){
  let cred = null, health = null;
  try{ const r = await authGet('/api/credentials/status'); cred = await r.json(); }catch(e){}
  try{ const r = await fetchWithTimeout(BASE+'/health', {}, 10000); health = await r.json(); }catch(e){}

  const coreRows = [];
  if(cred){
    const providers = [
      {nm:'Claude', ok: !!(cred.anthropic && cred.anthropic.api_key)},
      {nm:'OpenAI', ok: !!(cred.openai && cred.openai.api_key)},
      {nm:'Etsy API', ok: !!cred.etsy_live}
    ];
    const connectedCount = providers.filter(p=>p.ok).length;
    const acLlms = document.getElementById('ac-llms');
    if(acLlms) acLlms.textContent = connectedCount+'/'+providers.length+' connected';

    coreRows.push('<div class="core-row"><span class="lab"><span class="dotc'+(cred.etsy_live?'':' err')+'"></span>Etsy</span><span class="v'+(cred.etsy_live?'':' err')+'">'+(cred.etsy_live?('Live — '+escHtml(cred.shop_name||'onbrandcraftz')):escHtml(cred.etsy_live_error||'offline'))+'</span></div>');
    coreRows.push('<div class="core-row"><span class="lab"><span class="dotc'+((cred.anthropic&&cred.anthropic.api_key)?'':' err')+'"></span>Anthropic</span><span class="v'+((cred.anthropic&&cred.anthropic.api_key)?'':' err')+'">'+((cred.anthropic&&cred.anthropic.api_key)?'Key configured':'Missing key')+'</span></div>');
    coreRows.push('<div class="core-row"><span class="lab"><span class="dotc'+((cred.openai&&cred.openai.api_key)?'':' err')+'"></span>OpenAI</span><span class="v'+((cred.openai&&cred.openai.api_key)?'':' err')+'">'+((cred.openai&&cred.openai.api_key)?'Key configured':'Missing key')+'</span></div>');
  }
  const acCore = document.getElementById('ac-core');
  const acSystem = document.getElementById('ac-system');
  if(health){
    if(acCore){ acCore.textContent = 'Online · build '+escHtml(health.build||'?'); acCore.className='v'; }
    if(acSystem){
      acSystem.textContent = health.persistent ? 'Persistent storage' : 'Ephemeral (volume not attached)';
      acSystem.className = 'v'+(health.persistent?'':' warn');
    }
    coreRows.unshift('<div class="core-row"><span class="lab"><span class="dotc"></span>Build</span><span class="v">'+escHtml(health.build||'?')+'</span></div>');
    coreRows.push('<div class="core-row"><span class="lab"><span class="dotc'+(health.persistent?'':' warn')+'"></span>Storage</span><span class="v'+(health.persistent?'':' warn')+'">'+(health.persistent?'Persistent volume attached':'Ephemeral — resets on redeploy')+'</span></div>');
  } else if(acCore){
    acCore.textContent = 'Offline'; acCore.className='v err';
  }

  const acMemory = document.getElementById('ac-memory');
  if(acMemory){ acMemory.textContent = 'Not wired yet'; acMemory.className = 'v warn'; }

  const coreDetail = document.getElementById('core-detail');
  if(coreDetail){
    coreDetail.innerHTML = coreRows.length ? coreRows.join('') :
      '<div class="core-row"><span class="lab"><span class="dotc err"></span>Unavailable</span><span class="v err">Could not load</span></div>';
  }
}

// ── Shop Performance — real data from /api/analytics + /api/metrics ──
function _miniSpark(values, color){
  var h = 26;
  values = (values||[]).filter(function(v){ return v!=null && !isNaN(v); });
  if(values.length < 2) return '<div style="height:'+h+'px;display:flex;align-items:center;font-size:8.5px;color:var(--muted)">📈 Accumulating daily data…</div>';
  var W=140,H=h,mn=Math.min.apply(null,values),mx=Math.max.apply(null,values),range=mx-mn||1,pad=2;
  var pts=values.map(function(v,i){return [pad+(i/(values.length-1))*(W-pad*2), H-pad-((v-mn)/range)*(H-pad*2)];});
  var poly=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
  var area='M'+pts[0][0].toFixed(1)+','+H+' '+pts.map(function(p){return 'L'+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ')+' L'+pts[pts.length-1][0].toFixed(1)+','+H+' Z';
  var gid='fsg'+Math.random().toString(36).slice(2,8);
  return '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;display:block;overflow:visible">'+
    '<defs><linearGradient id="'+gid+'" x1="0" y1="0" x2="0" y2="1">'+
    '<stop offset="0%" stop-color="'+color+'" stop-opacity="0.3"/>'+
    '<stop offset="100%" stop-color="'+color+'" stop-opacity="0"/>'+
    '</linearGradient></defs>'+
    '<path d="'+area+'" fill="url(#'+gid+')"/>'+
    '<polyline points="'+poly+'" fill="none" stroke="'+color+'" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>'+
    '<circle cx="'+pts[pts.length-1][0].toFixed(1)+'" cy="'+pts[pts.length-1][1].toFixed(1)+'" r="2.5" fill="'+color+'"/>'+
    '</svg>';
}
function _miniDelta(val, isMoney){
  if(val==null || val===0) return '<span style="color:var(--muted)">— stable</span>';
  var pos=val>0, c=pos?'var(--green)':'var(--red)', a=pos?'↑':'↓';
  var n=isMoney?('$'+Math.abs(val).toFixed(2)):String(Math.round(Math.abs(val)));
  return '<span style="color:'+c+'">'+a+' '+n+'</span>';
}
async function loadShopPerf(){
  const sparkEl = document.getElementById('shop-spark-row');
  const chipEl = document.getElementById('shop-chip-row');
  try{
    const [ar, mr] = await Promise.all([
      authGet('/api/analytics?days=30'),
      authGet('/api/metrics'),
    ]);
    const a = await ar.json();
    const m = await mr.json();
    const tr = a.trends||{}, lt = a.latest||{}, del = a.delta||{};
    if(sparkEl){
      sparkEl.innerHTML =
        '<div class="shop-spark-card"><div class="ssc-lab">Revenue · 30d</div>'+
          '<div class="ssc-val">'+(lt.revenue_30d!=null?'$'+lt.revenue_30d.toFixed(2):'—')+'</div>'+
          '<div class="ssc-spark">'+_miniSpark(tr.revenue_30d,'var(--gold)')+'</div>'+
          '<div class="ssc-delta">'+_miniDelta(del.revenue_30d,true)+'</div></div>'+
        '<div class="shop-spark-card"><div class="ssc-lab">Orders · 30d</div>'+
          '<div class="ssc-val">'+(lt.orders_30d!=null?lt.orders_30d:'—')+'</div>'+
          '<div class="ssc-spark">'+_miniSpark(tr.orders_30d,'var(--cyan2)')+'</div>'+
          '<div class="ssc-delta">'+_miniDelta(del.orders_30d,false)+'</div></div>';
    }
    const allTimeRev = (m.orders && m.orders.all_time_revenue!=null) ? m.orders.all_time_revenue : null;
    if(chipEl){
      chipEl.innerHTML =
        '<div class="shop-chip"><div class="nm">Listings</div><div class="v">'+(lt.active_listings!=null?lt.active_listings:'—')+'</div></div>'+
        '<div class="shop-chip"><div class="nm">Total Sales</div><div class="v">'+(lt.total_sales!=null?lt.total_sales:'—')+'</div></div>'+
        '<div class="shop-chip"><div class="nm">All-Time Revenue</div><div class="v">'+(allTimeRev!=null?'$'+allTimeRev.toFixed(2):'—')+'</div></div>';
    }
  }catch(e){
    if(sparkEl) sparkEl.innerHTML = '<div style="color:var(--red);font-size:11px;padding:4px">Shop data offline</div>';
  }
}

// ── Tasks — real data from /api/todos ──
async function loadTasks(){
  const list = document.getElementById('tasks-list');
  try{
    const r = await authGet('/api/todos');
    const d = await r.json();
    if(list){
      list.innerHTML = d.todos.length ? d.todos.map(t=>{
        const done = !!t.done;
        return '<div class="tl-item"><div class="tl-dotcol"><span class="d"'+(done?' style="background:var(--muted)"':'')+'></span></div>'+
          '<div class="tl-txt"><div class="ttl"'+(done?' style="text-decoration:line-through;color:var(--muted)"':'')+'>'+escHtml(t.text)+'</div>'+
          '<div class="sub">added by '+escHtml(t.added_by||'scott')+'</div></div></div>';
      }).join('') : '<div style="color:var(--muted);font-size:12px">No tasks yet.</div>';
    }
    const badge = document.getElementById('badge-tasks');
    if(badge){ badge.textContent = d.open_count; badge.style.display = d.open_count>0 ? '' : 'none'; }
  }catch(e){
    if(list) list.innerHTML = '<div style="color:var(--red);font-size:12px">Tasks offline: '+escHtml(e.message)+'</div>';
  }
}

// ── Tools & Skills — real data from /api/tools/list (live AGENT_TOOLS registry) ──
async function loadTools(){
  const list = document.getElementById('tools-list');
  try{
    const r = await authGet('/api/tools/list');
    const d = await r.json();
    if(list){
      list.innerHTML = d.tools.map(t=>
        '<div style="padding:10px 0;border-bottom:1px solid var(--border)">'+
          '<div style="font-weight:600;font-size:12px;color:var(--text)">'+escHtml(t.name)+'</div>'+
          '<div style="font-size:10.5px;color:var(--muted);margin-top:3px">'+escHtml(t.description)+'</div></div>'
      ).join('');
    }
    const badge = document.getElementById('badge-tools');
    if(badge){ badge.textContent = d.count; badge.style.display = ''; }
  }catch(e){
    if(list) list.innerHTML = '<div style="color:var(--red);font-size:12px">Tools offline: '+escHtml(e.message)+'</div>';
  }
}

function loadAll(){
  loadAgents();
  loadCredentialsAndHealth();
  loadShopPerf();
  loadTasks();
  loadTools();
}
loadAll();
setInterval(loadAll, 30000);

// ── Clock ──
function tick(){
  const d = new Date();
  document.getElementById('clk').textContent = d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  document.getElementById('dt').textContent = d.toLocaleDateString([], {weekday:'long',month:'long',day:'numeric',year:'numeric'});
}
tick(); setInterval(tick, 1000);

// ── Focus mode toggle (visual only) ──
document.getElementById('focus-toggle').addEventListener('click', function(){
  this.classList.toggle('on');
  this.textContent = this.classList.contains('on') ? 'FOCUS MODE: ON' : 'FOCUS MODE: OFF';
});

// ── Orb: idle rotating wireframe particle sphere, audio-reactive on click (demo only) ──
const canvas = document.getElementById('orb');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height, CX = W/2, CY = H/2, R = 108;
let particles = [];
const N_LAT = 12, N_LON = 18;
for(let i=0;i<=N_LAT;i++){
  const lat = Math.PI * (i/N_LAT - 0.5);
  for(let j=0;j<N_LON;j++){
    const lon = 2*Math.PI * (j/N_LON);
    particles.push({lat, lon});
  }
}
let rot = 0, speaking = false, speakT = 0;
const orbState = document.getElementById('orb-state');
const vwSub = document.getElementById('vw-sub-text');
const talkSub = document.getElementById('talk-sub');
const micCircle = document.getElementById('tap-speak');

function frame(){
  ctx.clearRect(0,0,W,H);
  rot += speaking ? 0.028 : 0.010;
  let amp = 0;
  if(speaking){
    speakT += 0.18;
    amp = (Math.sin(speakT*3.1)*0.5+0.5) * (Math.sin(speakT*1.7)*0.3+0.7);
  }
  const glow = speaking ? 0.55 + amp*0.45 : 0.3;
  ctx.shadowBlur = 16 + amp*34;
  ctx.shadowColor = speaking ? 'rgba(122,232,255,'+glow+')' : 'rgba(58,214,255,0.3)';

  const pts = particles.map(p=>{
    const lon = p.lon + rot;
    const rr = R * (1 + (speaking ? amp*0.16*Math.sin(p.lat*4+speakT*2) : 0));
    const x = rr * Math.cos(p.lat) * Math.cos(lon);
    const y = rr * Math.sin(p.lat);
    const z = rr * Math.cos(p.lat) * Math.sin(lon);
    const scale = 320 / (320 - z);
    return {x: CX + x*scale*0.92, y: CY + y*scale*0.92, z, scale};
  });

  ctx.strokeStyle = speaking ? 'rgba(122,232,255,0.45)' : 'rgba(58,214,255,0.2)';
  ctx.lineWidth = 0.6;
  for(let i=0;i<N_LAT;i++){
    for(let j=0;j<N_LON;j++){
      const a = pts[i*N_LON+j], b = pts[i*N_LON+((j+1)%N_LON)], c = pts[(i+1)*N_LON+j];
      if(a && b){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}
      if(a && c){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(c.x,c.y);ctx.stroke();}
    }
  }
  pts.forEach(p=>{
    const sz = p.scale > 1 ? 1.8 : 1.1;
    ctx.fillStyle = speaking ? 'rgba(122,232,255,0.9)' : 'rgba(58,214,255,0.65)';
    ctx.beginPath();ctx.arc(p.x,p.y,sz,0,Math.PI*2);ctx.fill();
  });

  const grad = ctx.createRadialGradient(CX,CY,4,CX,CY,38+amp*24);
  grad.addColorStop(0, speaking ? 'rgba(180,240,255,'+ (0.7+amp*0.25) +')' : 'rgba(58,214,255,0.4)');
  grad.addColorStop(1, 'rgba(58,214,255,0)');
  ctx.fillStyle = grad;
  ctx.beginPath();ctx.arc(CX,CY,38+amp*24,0,Math.PI*2);ctx.fill();

  ctx.shadowBlur = 0;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

function setSpeaking(on){
  speaking = on;
  orbState.textContent = on ? 'SPEAKING — reacting to live TTS amplitude (demo)' : 'IDLE — slow ambient rotation';
  vwSub.textContent = on ? 'Speaking…' : 'Tap to speak';
  talkSub.textContent = on ? 'Frank is speaking…' : 'tap to speak';
  micCircle.classList.toggle('live', on);
}
canvas.addEventListener('click', ()=>{ setSpeaking(true); setTimeout(()=>setSpeaking(false), 3000); });
document.getElementById('tap-speak').addEventListener('click', ()=>{ setSpeaking(true); setTimeout(()=>setSpeaking(false), 3000); });
document.getElementById('talk-pill').addEventListener('click', ()=>{ setSpeaking(true); setTimeout(()=>setSpeaking(false), 3000); });

// ── Memory Insights constellation (placeholder line graph, real data wired in Step 2) ──
const mc = document.getElementById('mem-canvas');
const mctx = mc.getContext('2d');
const pts2 = [];
for(let i=0;i<14;i++){ pts2.push({x: i*(220/13), y: 20+Math.sin(i*0.9)*18+Math.random()*8}); }
function drawMem(){
  mctx.clearRect(0,0,220,90);
  mctx.strokeStyle = 'rgba(58,214,255,0.35)'; mctx.lineWidth = 1;
  mctx.beginPath();
  pts2.forEach((p,i)=>{ if(i===0) mctx.moveTo(p.x,p.y); else mctx.lineTo(p.x,p.y); });
  mctx.stroke();
  pts2.forEach(p=>{ mctx.fillStyle='rgba(122,232,255,0.8)'; mctx.beginPath(); mctx.arc(p.x,p.y,2,0,Math.PI*2); mctx.fill(); });
}
drawMem();
</script>
</body>
</html>"""


def render_frank_hud(app_token: str) -> str:
    """Substitute the real bearer token into the mockup's __APP_TOKEN__ placeholder
    at request time. The template is a plain string (not f-string/.format()) because
    its JS is full of literal {} braces, and it lives outside main.py so it has no
    direct access to APP_TOKEN at its own module-definition time — same token, same
    auth model as the live dashboard at /, just injected via str.replace() instead."""
    return _FRANK_HUD_MOCKUP.replace("__APP_TOKEN__", json.dumps(app_token))
