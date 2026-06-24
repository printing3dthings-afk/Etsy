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
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="FRANK">
<meta name="theme-color" content="#070d16">
<link rel="manifest" href="/frank-manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>FRANK — Command Center (mockup)</title>
<style>
:root{
  --bg:#070d16;--panel:#0f1f30;--panel2:#13283d;--border:#1c3349;
  --cyan:#3ad6ff;--cyan2:#8fefff;--gold:#C9A84C;--gold2:#e8c96a;--text:#e8edf2;--muted:#5d7891;
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
.drawer-toggle{display:none}
.drawer-search{display:none}
#drawer-backdrop{display:none}
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

/* ── Main content ── */
.main{grid-column:2;grid-row:2;display:flex;flex-direction:column;gap:12px;padding:12px;overflow:hidden}
.mrow{display:flex;gap:12px;min-height:0}
.mrow.rowA{flex:1}
.mrow.rowB{flex:1.25}
.mrow.rowC{flex:0.95}
.col-chat{flex:1.6 1 0;min-width:0}

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
.col-agents{flex:1.1}
.col-timeline{flex:1}

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

#toast-stack{position:fixed;top:16px;right:16px;z-index:9000;display:flex;flex-direction:column;
  gap:8px;max-width:340px;pointer-events:none}
.toast{background:var(--panel2);border:1px solid var(--border);border-radius:11px;padding:11px 14px;
  font-size:12.5px;color:var(--text);box-shadow:0 8px 24px rgba(0,0,0,.35);pointer-events:auto;
  border-left:3px solid var(--cyan);animation:toast-in .18s ease-out}
.toast.ok{border-left-color:var(--green)}
.toast.err{border-left-color:var(--red)}
.toast.info{border-left-color:var(--cyan)}
.toast.out{animation:toast-out .18s ease-in forwards}
@keyframes toast-in{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
@keyframes toast-out{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(-8px)}}

#welcome-overlay{position:fixed;inset:0;z-index:9500;background:rgba(5,9,16,.72);
  display:flex;align-items:center;justify-content:center;padding:20px}
.welcome-card{background:var(--panel);border:1px solid var(--border);border-radius:16px;
  padding:26px 28px;max-width:440px;width:100%;box-shadow:0 20px 60px rgba(0,0,0,.5)}
.welcome-title{font-size:19px;font-weight:700;color:var(--gold);margin-bottom:12px}
.welcome-body p{font-size:13px;color:var(--text);line-height:1.5;margin:0 0 10px}
.welcome-body ul{margin:0 0 12px;padding-left:18px;font-size:13px;color:var(--text);line-height:1.6}
.welcome-note{color:var(--muted)!important;font-size:12px!important}
.welcome-dismiss{width:100%;background:var(--gold);color:#0D1B2A;border:none;border-radius:10px;
  padding:11px 0;font-size:14px;font-weight:600;cursor:pointer;margin-top:6px}

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

.shop-spark-row{display:flex;gap:8px;flex:1;min-height:0;overflow:hidden}
.shop-spark-card{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:10px;
  padding:6px 8px;display:flex;flex-direction:column;gap:1px;min-height:0;overflow:hidden}
.shop-spark-card .ssc-lab{font-size:9px;color:var(--muted);letter-spacing:.4px}
.shop-spark-card .ssc-valrow{display:flex;align-items:baseline;justify-content:space-between;gap:6px}
.shop-spark-card .ssc-val{font-size:13px;font-weight:700;color:var(--cyan2)}
.shop-spark-card .ssc-delta{font-size:8.5px;flex-shrink:0}
.shop-spark-card .ssc-spark{flex:1;min-height:0}

.shop-chip-row{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:6px;flex-shrink:0}
.shop-chip{background:var(--panel2);border:1px solid var(--border);border-radius:8px;padding:5px 7px;
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

.screen{display:none;grid-column:2;grid-row:2;overflow:hidden;padding:12px}
.screen.active{display:block}

/* ── Live Chat screen — ported from the live Hub's #chat-wrap at / (main.py), same
   /ws/chat backend, same CHAT_SESSION scheme, restyled to the HUD's cyan/gold theme. ── */
#chat-msgs{flex:1;overflow-y:auto;min-height:0;padding:2px 2px 10px;display:flex;flex-direction:column;gap:10px}
.lc-bubble{max-width:78%;padding:10px 14px;border-radius:16px;font-size:13px;line-height:1.5;word-break:break-word}
.lc-bubble.user{align-self:flex-end;background:var(--gold);color:#0D1B2A;border-bottom-right-radius:4px}
.lc-bubble.bot{align-self:flex-start;background:var(--panel2);border:1px solid var(--border);border-bottom-left-radius:4px;white-space:pre-wrap;color:var(--text)}
.lc-bubble.typing{color:var(--muted);font-style:italic}
.lc-chips{display:flex;gap:8px;overflow-x:auto;padding:8px 2px;flex-shrink:0;border-top:1px solid var(--border);scrollbar-width:none}
.lc-chips::-webkit-scrollbar{display:none}
.lc-chip{flex-shrink:0;padding:7px 14px;border-radius:20px;border:1px solid var(--border);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;white-space:nowrap}
.lc-chip:active{border-color:var(--gold);color:var(--gold)}
.lc-input-row{display:flex;gap:8px;padding:10px 2px 0;border-top:1px solid var(--border);flex-shrink:0}
#chat-input{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:22px;padding:10px 16px;color:var(--text);font-size:14px;outline:none}
#chat-input:focus{border-color:var(--gold)}
#chat-send{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#chat-send svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}

/* ── Hub screens (Listings/Products/Brand Kit/Files/Connections/Security) — ported
   verbatim-in-behavior from the live Hub at / (main.py), restyled to the HUD's
   cyan/gold theme. Classes are namespaced "hub-" since the HUD already has its own
   unrelated .badge (notification dot) that would collide with the live Hub's .badge
   (listing state pill). ── */
.hub-scroll{margin-top:10px;overflow-y:auto;max-height:760px}
.hub-section-title{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin:16px 0 8px}
.hub-section-title:first-child{margin-top:0}
.hub-card{background:var(--panel2);border:1px solid var(--border);border-radius:12px;padding:14px;margin-bottom:12px}
.hub-empty{text-align:center;color:var(--muted);padding:40px 0;font-size:13px}
.hub-spinner{display:block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:hubspin .7s linear infinite;margin:40px auto}
@keyframes hubspin{to{transform:rotate(360deg)}}

.hub-toggle-row{display:flex;gap:8px;margin-bottom:12px}
.hub-toggle-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.hub-toggle-btn.active{background:var(--gold);color:#06141f;border-color:var(--gold)}
.hub-chip-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.hub-chip-btn{padding:6px 12px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
.hub-chip-btn.active{background:var(--gold);color:#06141f;border-color:var(--gold)}

.hub-listing-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.hub-listing-item:last-child{border-bottom:none}
.hub-thumb{width:52px;height:52px;border-radius:8px;object-fit:cover;background:var(--border);flex-shrink:0}
.hub-thumb-ph{width:52px;height:52px;border-radius:8px;background:var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:20px}
.hub-listing-info{flex:1;min-width:0}
.hub-listing-title{font-size:13px;font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hub-listing-meta{font-size:11px;color:var(--muted);margin-top:2px}
.hub-listing-price{font-size:14px;font-weight:700;color:var(--gold);flex-shrink:0}
.hub-lstate{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;margin-left:6px}
.hub-lstate.draft{background:#0f1f30;color:var(--muted);border:1px solid var(--border)}
.hub-lstate.active{background:#143323;color:var(--green);border:1px solid #1f4d36}

.hub-listing-detail{padding:2px 14px 12px;margin:-2px 0 10px;background:var(--panel);border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;font-size:12px}
.hub-listing-detail .hub-drow{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)}
.hub-listing-detail .hub-drow:last-child{border-bottom:none}
.hub-listing-detail .hub-drow span{color:var(--muted)}
.hub-listing-detail .hub-drow b{font-weight:600;text-align:right}

.hub-act-btn{flex:1;text-align:center;padding:7px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}

.hub-swatch{display:inline-block;width:16px;height:16px;border-radius:4px;vertical-align:middle;margin-right:4px;flex-shrink:0;border:1px solid rgba(255,255,255,.15)}
.hub-prod-card{background:var(--panel2);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}

.hub-cred-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);flex-wrap:wrap}
.hub-cred-row:last-child{border-bottom:none}
.hub-cred-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}

.hub-posture-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.hub-posture-row:last-child{border-bottom:none}

/* ── Action Center — ported from the live Hub's Action Center at / (main.py); the
   approve/reject queue is the human-in-the-loop safety gate for Etsy writes and local
   file/exec actions. Namespaced "act-" — new concept, no existing HUD equivalent. ── */
.section-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.act-card{background:var(--panel2);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.act-card.high{border-left-color:var(--red)}
.act-card.medium{border-left-color:var(--gold)}
.act-card.low{border-left-color:#4a6b8a}
.act-card.approval{border-left-color:var(--green);background:#13241c}
.act-sev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px}
.act-sev.high{background:#2d1a1a;color:#e07070}
.act-sev.medium{background:#2d2a1a;color:var(--gold2)}
.act-sev.low{background:#1a2330;color:#7ba0c2}
.act-sev.approval{background:#13241c;color:#5fcf9e;border:1px solid #2d5a44}
.act-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35;color:var(--text)}
.act-detail{font-size:12px;color:var(--muted);line-height:1.45}
.act-sug{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.act-sug b{color:var(--gold2);font-weight:600}
.act-btns{display:flex;gap:8px;margin-top:9px}
.act-btn{flex:1;text-align:center;padding:7px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}
.act-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.act-btn.approve{background:var(--green);color:#06140d;border-color:var(--green)}
.act-btn.reject{color:#e08585;border-color:#5a2d2d}
.metric{background:var(--panel2);border:1px solid var(--border);border-radius:12px;padding:14px}
.metric .value{font-size:24px;font-weight:700;color:var(--text)}
.metric .sub{font-size:11px;color:var(--muted);margin-top:2px}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}

/* ══════════ MOBILE LAYOUT — fluid stage, off-canvas drawer nav, stacked rows ══════════
   Single breakpoint, kept in sync with MOBILE_BREAKPOINT in JS. Desktop (>880px) is
   completely untouched — everything below is additive and gated behind this query. ── */
@media (max-width:880px){
  html,body{overflow-y:auto}
  #stage-wrap{position:static;display:block;height:auto;min-height:100dvh}
  #stage{
    position:static;width:100vw;min-height:100dvh;height:auto;transform:none !important;
    grid-template-columns:92px 1fr;grid-template-rows:auto auto auto;
  }

  .hdr-logo{padding:0 8px;gap:6px}
  .hdr-logo .lbl{display:none}
  .drawer-toggle{display:flex}

  .hdr-bar{padding:0 10px;gap:8px}
  .hdr-bar .search,.hdr-bar .clockwrap{display:none}

  .sidebar{
    position:fixed;top:0;left:0;bottom:0;width:78vw;max-width:320px;z-index:200;
    grid-column:unset;grid-row:unset;
    transform:translateX(-100%);transition:transform .25s ease;
    box-shadow:8px 0 24px rgba(0,0,0,.45);
    padding-top:calc(14px + env(safe-area-inset-top));
    padding-bottom:calc(14px + env(safe-area-inset-bottom));
    padding-left:calc(10px + env(safe-area-inset-left));
  }
  body.drawer-open .sidebar{transform:translateX(0)}
  .drawer-search{display:block;margin-bottom:12px;width:100%}

  #drawer-backdrop{
    display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:150;
  }
  body.drawer-open #drawer-backdrop{display:block}

  .main{grid-column:1/-1;overflow:visible !important;height:auto !important;padding:10px}
  .screen{grid-column:1/-1;height:auto;overflow:visible;padding:10px}
  .panel{overflow:visible !important}
  .panel-body{overflow:visible !important;max-height:none !important;flex:none !important}

  .mrow{flex-direction:column}
  .mrow.rowA,.mrow.rowB,.mrow.rowC{flex:none}
  .col-aicore,.col-orb,.col-feed,.col-agents,.col-chat,.col-timeline,
  .col-sysmon,.col-meminsights,.col-shop{flex:none !important;width:100% !important}

  #chat-msgs{min-height:280px;max-height:55vh;flex:none}
  .orb-hero{min-height:260px}
  .orb-hero-stage{min-height:220px}
  .mem-canvas-wrap{min-height:160px}

  .agents-grid{grid-template-columns:repeat(2,1fr)}

  #tasks-list,#actions-content,#calendar-content,#memory-content,#conversations-content,
  #kb-content,#tools-list,#workflows-content,.hub-scroll,#studio-videos-list{
    max-height:none !important;overflow:visible !important;
  }

  .nav-item{padding:12px 14px;font-size:14px}
  .icon-btn{width:40px;height:40px}
  .qc-btn{padding:12px 10px}
  #chat-send{width:44px;height:44px}
  .talk-pill{padding:10px 24px}

  .hdr-logo,.hdr-bar{padding-top:env(safe-area-inset-top)}
  .bottombar{
    flex-wrap:wrap;height:auto;padding:10px;gap:8px;
    padding-bottom:calc(10px + env(safe-area-inset-bottom));
  }

  #toast-stack{
    top:auto;right:10px;left:10px;bottom:calc(78px + env(safe-area-inset-bottom));
    max-width:none;
  }

  .act-btn{font-size:11px;padding:7px 4px}
  .studio-grid>div:last-child{flex:1 1 100%;min-width:0}
}

@media (max-width:380px){
  .agents-grid{grid-template-columns:1fr}
}
</style>
</head>
<body>
<div id="stage-wrap"><div id="stage">

  <div class="hdr-logo brk">
    <button id="hamburger-btn" class="icon-btn drawer-toggle" aria-label="Open navigation">☰</button>
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
    <input class="search drawer-search" placeholder="Search listings, orders, tools, knowledge base…">
    <div class="nav-section">Frank</div>
    <div class="nav-item active" data-screen="cmd"><span class="ic">⌂</span>Command Center</div>
    <div class="nav-item" data-screen="core"><span class="ic">◎</span>AI Core</div>
    <div class="nav-item" data-screen="agents"><span class="ic">⚙</span>Agents</div>
    <div class="nav-item" data-screen="tasks"><span class="ic">☑</span>Tasks<span class="nbadge" id="badge-tasks" style="display:none">—</span></div>
    <div class="nav-item" data-screen="actions"><span class="ic">✓</span>Action Center<span class="nbadge" id="badge-actions" style="display:none">—</span></div>
    <div class="nav-item" data-screen="calendar"><span class="ic">▦</span>Calendar<span class="nbadge" id="badge-calendar" style="display:none">—</span></div>

    <div class="nav-section">Knowledge</div>
    <div class="nav-item" data-screen="memory"><span class="ic">✦</span>Memory<span class="nbadge" id="badge-memory" style="display:none">—</span></div>
    <div class="nav-item" data-screen="conversations"><span class="ic">💬</span>Conversations<span class="nbadge" id="badge-conversations" style="display:none">—</span></div>
    <div class="nav-item" data-screen="kb"><span class="ic">📚</span>Knowledge Base<span class="nbadge" id="badge-kb" style="display:none">—</span></div>

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

    <div class="voice-widget" style="text-align:left">
      <div class="vw-title">QUICK COMMANDS</div>
      <button class="qc-btn" onclick="showScreen('tasks');document.getElementById('hud-todo-input').focus()"><span class="qic">+</span>Start New Task</button>
      <button class="qc-btn" onclick="showScreen('calendar')"><span class="qic">▦</span>Open Calendar</button>
      <button class="qc-btn" onclick="runWorkflow('shop_health_check', this, false)"><span class="qic">✓</span>Run Health Check</button>
      <button class="qc-btn" onclick="showScreen('workflows')"><span class="qic">⇄</span>Run Workflow</button>
    </div>
  </div>
  <div id="drawer-backdrop"></div>
  <div id="toast-stack"></div>
  <div id="welcome-overlay" style="display:none">
    <div class="welcome-card">
      <div class="welcome-title">Welcome to Frank</div>
      <div class="welcome-body">
        <p>Frank is organized into four groups in the sidebar:</p>
        <ul>
          <li><b>Frank</b> — chat, AI core, agents, tasks, and the Action Center</li>
          <li><b>Knowledge</b> — memory, past conversations, and the knowledge base</li>
          <li><b>Tools</b> — tools &amp; skills, workflows, and the video studio</li>
          <li><b>Shop</b> — listings, products, brand kit, files, connections, security</li>
        </ul>
        <p class="welcome-note">Nothing that changes your shop, files, or social accounts ever runs without your one-tap approval in the Action Center.</p>
      </div>
      <button class="welcome-dismiss" onclick="dismissWelcomeOverlay()">Got it</button>
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
          <div class="orb-hint">click the orb (or the talk pill) to start talking to Frank</div>
        </div>

        <div class="panel brk col-feed">
          <div class="panel-title">Live Intelligence Feed <span class="src">/api/queue</span></div>
          <div class="panel-body" id="feed-list"><div style="color:var(--muted);font-size:11px">Loading…</div></div>
        </div>
      </div>

      <div class="mrow rowB">
        <div class="panel brk col-agents">
          <div class="panel-title">Active Agents <span class="lnk" onclick="showScreen('agents')" style="cursor:pointer">View All ›</span></div>
          <div class="agents-grid" id="cmd-agents-grid">
            <div class="agent-tile idle"><div class="top"><div class="ic">⋯</div><div class="name">Loading…</div></div><div class="stat"><span class="d"></span>—</div></div>
          </div>
        </div>

        <div class="panel brk col-chat">
          <div class="panel-title">Ask Frank <span class="src">/ws/chat — live, always-on chat</span></div>
          <div id="chat-msgs"></div>
          <div class="lc-chips">
            <span class="lc-chip" onclick="sendChip(this)">What should I focus on?</span>
            <span class="lc-chip" onclick="sendChip(this)">How are sales?</span>
            <span class="lc-chip" onclick="sendChip(this)">What's my next listing?</span>
            <span class="lc-chip" onclick="sendChip(this)">Pricing advice</span>
            <span class="lc-chip" onclick="sendChip(this)">SEO tips</span>
          </div>
          <div class="lc-input-row">
            <input id="chat-input" type="text" placeholder="Ask Fucking Frank…" autocomplete="off">
            <button id="chat-send" onclick="sendMsg()">
              <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>

        <div class="panel brk col-timeline">
          <div class="panel-title">Mission Timeline <span class="src">/api/todos</span></div>
          <div class="panel-body" id="timeline-list"><div style="color:var(--muted);font-size:11px">Loading…</div></div>
          <div class="panel-title" style="margin-top:6px;margin-bottom:0"><span class="lnk" style="margin-left:auto;cursor:pointer" onclick="showScreen('tasks')">View Full Schedule ›</span></div>
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
          <div class="panel-title">Memory Insights <span class="lnk" style="cursor:pointer" onclick="showScreen('memory')">View Memory Map ›</span></div>
          <div class="mem-row">
            <div class="mem-canvas-wrap"><canvas id="mem-canvas" width="220" height="90" style="width:100%;height:100%"></canvas></div>
            <div class="mem-stats">
              <div class="mem-stat"><div class="n" id="mem-stat-memories">—</div><div class="l">MEMORIES</div></div>
              <div class="mem-stat"><div class="n" id="mem-stat-turns">—</div><div class="l">SESSION TURNS</div></div>
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
      <div style="display:flex;gap:8px;margin:14px 0">
        <input id="hud-todo-input" type="text" placeholder="Add a to-do…" onkeydown="if(event.key==='Enter')addHudTodo()"
          style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13px;color:var(--text)">
        <input id="hud-todo-due" type="date" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:9px 10px;font-size:13px;color:var(--text)">
        <button onclick="addHudTodo()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer">Add</button>
      </div>
      <div id="tasks-list" style="margin-top:10px;overflow-y:auto;max-height:700px">
        <div style="color:var(--muted);font-size:12px">Loading…</div>
      </div>
    </div>
  </div>

  <!-- ══════════ ACTION CENTER — real data: /api/queue + /api/actions — approve/reject gate ══════════ -->
  <div class="screen" id="screen-actions">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Action Center <span class="src">/api/queue + /api/actions — approve/reject staged changes</span></div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <button id="batch-tag-btn" onclick="batchStageTags(this)" style="flex:1;background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:center">⚡ Stage All Tag Fixes</button>
      </div>
      <div id="actions-content" style="overflow-y:auto;max-height:700px"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ CALENDAR — real data: /api/cadence + /api/todos — due dates, ops cadence, seasonal/tax calendar ══════════ -->
  <div class="screen" id="screen-calendar">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Calendar <span class="src">/api/cadence + /api/todos — due dates, ops cadence, seasonal keywords</span></div>
      <div id="calendar-content" style="margin-top:10px;overflow-y:auto;max-height:760px"><div class="hub-spinner"></div></div>
    </div>
  </div>
  <div class="screen" id="screen-memory">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Memory <span class="src">/api/memory — chat history + logged learnings + knowledge base, rolled up</span></div>
      <div id="memory-content" style="margin-top:10px;overflow-y:auto;max-height:760px"><div class="hub-spinner"></div></div>
    </div>
  </div>
  <div class="screen" id="screen-conversations">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Conversations <span class="src">/api/conversations — persisted chat_messages history</span></div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <input id="conv-search-input" type="text" placeholder="Search all conversations…" style="flex:1;background:var(--panel2);border:1px solid var(--border);color:var(--text);border-radius:10px;padding:10px 14px;font-size:13px">
        <button onclick="searchConversations()" style="background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer">Search</button>
      </div>
      <div id="conversations-content" style="overflow-y:auto;max-height:700px"><div class="hub-spinner"></div></div>
    </div>
  </div>
  <div class="screen" id="screen-kb">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Knowledge Base <span class="src">/api/kb — real markdown docs in data/knowledge_base/</span></div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <input id="kb-search-input" type="text" placeholder="Search all docs…" style="flex:1;background:var(--panel2);border:1px solid var(--border);color:var(--text);border-radius:10px;padding:10px 14px;font-size:13px">
        <button onclick="searchKb()" style="background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer">Search</button>
      </div>
      <div id="kb-content" style="overflow-y:auto;max-height:700px"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ TOOLS & SKILLS — real data: /api/tools/list (live AGENT_TOOLS) ══════════ -->
  <div class="screen" id="screen-tools">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Tools &amp; Skills <span class="src">/api/tools/list — live AGENT_TOOLS registry</span></div>
      <div id="tools-list" style="margin-top:10px;overflow-y:auto;max-height:760px">
        <div style="color:var(--muted);font-size:12px">Loading…</div>
      </div>
    </div>
  </div>

  <!-- ══════════ WORKFLOWS — real data: /api/workflows (live _EXEC_COMMANDS registry) ══════════ -->
  <div class="screen" id="screen-workflows">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Workflows <span class="src">/api/workflows — runnable backend scripts, gated by the same approval queue as Action Center</span></div>
      <div id="workflows-content" style="margin-top:10px;overflow-y:auto;max-height:760px"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ LISTINGS — real data: /api/listings, /api/shop-sections, /api/listings/{id}/files ══════════ -->
  <div class="screen" id="screen-listings">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Listings <span class="src">/api/listings — live Etsy listings via list_listings/get_listing</span></div>
      <div class="hub-toggle-row" style="margin-top:10px">
        <button class="hub-toggle-btn active" onclick="loadListings('active',this)">Active</button>
        <button class="hub-toggle-btn" onclick="loadListings('draft',this)">Drafts</button>
      </div>
      <div id="listings-content" class="hub-scroll"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ PRODUCTS — fully static: DP1026-1029 + theme catalog, from CLAUDE.md ══════════ -->
  <div class="screen" id="screen-products">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Products <span class="src">Static — DP1026–1029 product catalog from CLAUDE.md</span></div>
      <div id="products-content" class="hub-scroll"></div>
    </div>
  </div>

  <!-- ══════════ BRAND KIT — fully static: color palettes, listing standards, pricing tiers ══════════ -->
  <div class="screen" id="screen-brandkit">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Brand Kit <span class="src">Static — palettes, listing standards, pricing tiers from CLAUDE.md</span></div>
      <div id="brandkit-content" class="hub-scroll"></div>
    </div>
  </div>

  <!-- ══════════ FILES — real data: /api/files (data/digital_products/ + backups) ══════════ -->
  <div class="screen" id="screen-files">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Files <span class="src">/api/files — live volume listing, data/digital_products/ + backups</span></div>
      <div id="files-content" class="hub-scroll"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ CONNECTIONS — real data: /api/credentials/status + static Platform Roadmap ══════════ -->
  <div class="screen" id="screen-connections">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Connections <span class="src">/api/credentials/status — live token status + Platform Connections Roadmap</span></div>
      <div id="connections-content" class="hub-scroll"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ SECURITY — fully static: security posture checklist ══════════ -->
  <div class="screen" id="screen-security">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Security <span class="src">Static — security posture checklist + re-auth instructions</span></div>
      <div id="security-content" class="hub-scroll"></div>
    </div>
  </div>

  <div class="screen" id="screen-studio">
    <div class="panel brk" style="height:100%;overflow-y:auto">
      <div class="panel-title">Studio — Image-to-Video Generation <span class="src">/api/studio/* — generate, attach to Etsy, post to Instagram/Facebook</span></div>
      <div class="studio-grid" style="flex-wrap:wrap">
        <div style="flex:1;min-width:320px">
          <video id="studio-player" controls style="aspect-ratio:16/9"></video>
          <div id="studio-player-caption" style="margin-top:10px;color:var(--muted);font-size:11px">Select a generated video from the list to preview it here.</div>
        </div>
        <div style="flex:0 0 300px">
          <div class="panel-title" style="margin-top:0">Generated Videos</div>
          <div id="studio-videos-list" class="hub-scroll" style="max-height:420px"><div class="hub-empty">Loading…</div></div>
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Generate a New Video</div>
      <div class="hub-card">
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Upload images below, or leave images empty and enter an existing Etsy listing ID to pull its photos automatically.</div>
        <input type="file" id="studio-file-input" accept="image/*" multiple style="margin-bottom:8px;width:100%;color:var(--text);font-size:12px">
        <div id="studio-upload-status" style="font-size:11px;color:var(--muted);margin-bottom:10px"></div>
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <input id="studio-listing-id" type="number" placeholder="Etsy Listing ID (optional)" style="flex:1;min-width:140px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
          <select id="studio-style" style="flex:1;min-width:120px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
            <option value="showcase">Showcase</option>
            <option value="new-drop">New Drop</option>
            <option value="feature">Feature</option>
            <option value="minimal">Minimal</option>
          </select>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center">
          <input id="studio-title" type="text" placeholder="Title (optional)" style="flex:1;min-width:140px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
          <input id="studio-price" type="text" placeholder="Price (optional)" style="flex:0 0 110px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);white-space:nowrap"><input type="checkbox" id="studio-digital" checked> Digital</label>
        </div>
        <button class="act-btn primary" style="width:100%" onclick="studioGenerate()" id="studio-generate-btn">Generate Video</button>
        <div id="studio-generate-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>
      </div>

      <div class="hub-section-title" id="studio-actions-title" style="display:none">Actions — <span id="studio-actions-filename"></span></div>
      <div class="hub-card" id="studio-actions-card" style="display:none">
        <div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:6px">Attach to Etsy Listing</div>
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Stages the video for Scott's approval — it is only attached to the listing after approving in the Action Center.</div>
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <input id="studio-attach-listing-id" type="number" placeholder="Listing ID" style="flex:1;min-width:120px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
          <input id="studio-attach-rank" type="number" min="1" max="10" placeholder="Rank 1-10 (optional)" style="flex:0 0 160px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px">
        </div>
        <button class="act-btn" style="width:100%" onclick="studioStageToEtsy()" id="studio-stage-btn">Stage for Approval</button>
        <div id="studio-stage-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>

        <div style="font-size:12px;font-weight:600;color:var(--text);margin:18px 0 6px">Post to Instagram</div>
        <textarea id="studio-ig-caption" placeholder="Caption" style="width:100%;min-height:50px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px;margin-bottom:8px"></textarea>
        <button class="act-btn" style="width:100%" onclick="studioPostInstagram()" id="studio-ig-btn">Post to Instagram (Reel)</button>
        <div id="studio-ig-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>

        <div style="font-size:12px;font-weight:600;color:var(--text);margin:18px 0 6px">Post to Facebook</div>
        <textarea id="studio-fb-caption" placeholder="Description" style="width:100%;min-height:50px;background:var(--panel);border:1px solid var(--border);border-radius:7px;padding:8px;color:var(--text);font-size:12px;margin-bottom:8px"></textarea>
        <button class="act-btn" style="width:100%" onclick="studioPostFacebook()" id="studio-fb-btn">Post to Facebook</button>
        <div id="studio-fb-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>
      </div>
    </div>
  </div>

  <div class="bottombar">
    <div class="bb-left">
      <div class="it">📍 Local</div>
      <div class="it">⛅ —</div>
      <div class="it" id="bb-relay">🌐 Relay: —</div>
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
// ── Auto-scale the fixed 1440x900 stage to fit any viewport, desktop only — below
// MOBILE_BREAKPOINT the stage goes fluid via CSS instead (see isMobileMode()). ──
const STAGE_W = 1440, STAGE_H = 900;
const MOBILE_BREAKPOINT = 880;
const stage = document.getElementById('stage');
const mobileMQ = window.matchMedia('(max-width:' + MOBILE_BREAKPOINT + 'px)');
function isMobileMode(){ return mobileMQ.matches; }
function fitStage(){
  if (isMobileMode()){ stage.style.transform = 'none'; return; }
  const scale = Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H);
  stage.style.transform = 'scale(' + scale + ')';
}
function closeDrawer(){ document.body.classList.remove('drawer-open'); }
function toggleDrawer(){ document.body.classList.toggle('drawer-open'); }
function syncMobileClass(){
  document.body.classList.toggle('is-mobile', isMobileMode());
  if (!isMobileMode()) closeDrawer();
  fitStage();
}
window.addEventListener('resize', syncMobileClass);
mobileMQ.addEventListener('change', syncMobileClass);
syncMobileClass();
document.getElementById('hamburger-btn').addEventListener('click', toggleDrawer);
document.getElementById('drawer-backdrop').addEventListener('click', closeDrawer);
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/frank-sw.js', { scope: '/frank' }).catch(()=>{}); }

// ── Real data wiring (Step 2) — same bearer token + fetch pattern as the live
// dashboard at /, injected into this template at request time. ──
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
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
function showToast(message, type='info', ms=4500){
  const stack = document.getElementById('toast-stack');
  if (!stack) return;
  const t = document.createElement('div');
  t.className = 'toast ' + (type||'info');
  t.textContent = message;
  stack.appendChild(t);
  setTimeout(()=>{
    t.classList.add('out');
    setTimeout(()=>t.remove(), 200);
  }, ms);
}

// ── Voice: OpenAI TTS (speech-out) + Whisper (speech-in) — wired to the orb's
// setSpeaking() and the mic/talk-pill click targets further down this file. ──
let _ttsAudio = null;
// Free fallback for when OpenAI TTS is unavailable (e.g. quota exhausted) — uses the
// browser's own speechSynthesis, no API key, no cost. Works on iOS Safari/PWA (unlike
// SpeechRecognition/listening, which is why only speaking gets a fallback, not the mic).
function _speakWithBrowserFallback(text){
  if(!('speechSynthesis' in window)){ setSpeaking(false); return; }
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.onstart = () => setSpeaking(true, true);
    u.onend = () => setSpeaking(false, true);
    u.onerror = () => setSpeaking(false, true);
    window.speechSynthesis.speak(u);
  } catch(err){ setSpeaking(false); }
}
function speakText(text){
  if(!text) return;
  fetchWithTimeout(BASE+'/api/voice/speak', {
    method:'POST',
    headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
    body: JSON.stringify({text})
  }, 20000).then(r=>{
    if(!r.ok) throw new Error('speak failed: '+r.status);
    return r.blob();
  }).then(blob=>{
    if(_ttsAudio){ _ttsAudio.pause(); _ttsAudio = null; }
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    _ttsAudio = audio;
    audio.onplay = () => setSpeaking(true);
    audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
    audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
    audio.play().catch(()=>{ _speakWithBrowserFallback(text); });
  }).catch(()=>{ _speakWithBrowserFallback(text); });
}

let _voiceRecorder = null, _voiceChunks = [], _voiceRecording = false, _voiceStream = null;
// ── Auto-stop-on-silence state. We watch the mic's volume envelope with a Web Audio
// AnalyserNode and stop the RECORDER (never the stream — see beb230b) once the user has
// spoken and then gone quiet for SILENCE_MS, so they don't have to tap a second time. ──
let _audioCtx = null, _analyser = null, _analyserSource = null, _analyserStream = null;
let _silenceRAF = null, _speechSeen = false, _silenceStart = 0, _recStart = 0;
const _SPEAK_RMS = 0.025;     // above this = talking
const _SILENCE_RMS = 0.015;   // below this (after speech) = quiet
const _SILENCE_MS = 1500;     // quiet this long after speech -> auto-stop
const _MAX_REC_MS = 30000;    // hard cap so a noisy room can't record forever
// Free fallback for when OpenAI transcription is unavailable (e.g. quota exhausted).
// SpeechRecognition needs LIVE mic audio — it can't transcribe a finished recording —
// so it runs in parallel with the MediaRecorder for the same capture session, and its
// transcript is only used if the Whisper call afterward fails or returns nothing.
// Not available on iOS Safari/PWA (no webkitSpeechRecognition there) — degrades to the
// existing "could not transcribe" message on those devices, same as before this change.
let _speechRecognizer = null, _speechRecognitionText = '';
function _startSpeechRecognitionFallback(){
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  _speechRecognitionText = '';
  if(!SR){ _speechRecognizer = null; return; }
  try {
    const rec = new SR();
    rec.continuous = true;
    rec.interimResults = false;
    rec.lang = 'en-US';
    rec.onresult = (e) => {
      for(let i = e.resultIndex; i < e.results.length; i++){
        if(e.results[i].isFinal) _speechRecognitionText += e.results[i][0].transcript + ' ';
      }
    };
    rec.onerror = () => {};
    rec.start();
    _speechRecognizer = rec;
  } catch(err){ _speechRecognizer = null; }
}
function _stopSpeechRecognitionFallback(){
  if(_speechRecognizer){
    try { _speechRecognizer.stop(); } catch(err){}
    _speechRecognizer = null;
  }
}
// iOS Safari (and other WebKit) PWAs in standalone mode have a known bug: once a
// getUserMedia() stream's tracks are all stopped, a SECOND getUserMedia() call in the
// same page session can hang forever (the promise never resolves or rejects). Re-acquiring
// the mic fresh on every recording — and fully releasing it in onstop — was tripping that
// bug, which is why the talk button worked once then went dead until a full app relaunch.
// Fix: acquire the mic stream once and keep it alive for the whole page session; only a
// new MediaRecorder (cheap, single-use by design) is created per recording cycle.
// ── Silence monitor: stops the recorder hands-free once the user finishes talking. ──
async function _startSilenceMonitor(){
  try {
    const AC = window.AudioContext || window.webkitAudioContext;
    if(!AC || !_voiceStream) return;            // no Web Audio -> manual tap-to-stop only
    if(!_audioCtx) _audioCtx = new AC();
    if(_audioCtx.state === 'suspended') await _audioCtx.resume();
    // (Re)bind the analyser source if the stream was (re)acquired since last time.
    if(!_analyser || _analyserStream !== _voiceStream){
      _analyserSource = _audioCtx.createMediaStreamSource(_voiceStream);
      _analyser = _audioCtx.createAnalyser();
      _analyser.fftSize = 512;
      _analyserSource.connect(_analyser);
      _analyserStream = _voiceStream;
    }
    const buf = new Uint8Array(_analyser.fftSize);
    _speechSeen = false; _silenceStart = 0; _recStart = Date.now();
    const tick = () => {
      if(!_voiceRecording){ _silenceRAF = null; return; }
      _analyser.getByteTimeDomainData(buf);
      let sum = 0;
      for(let i=0;i<buf.length;i++){ const v = (buf[i]-128)/128; sum += v*v; }
      const rms = Math.sqrt(sum / buf.length);
      const now = Date.now();
      if(rms > _SPEAK_RMS){ _speechSeen = true; _silenceStart = 0; }
      else if(_speechSeen && rms < _SILENCE_RMS){
        if(!_silenceStart) _silenceStart = now;
        else if(now - _silenceStart >= _SILENCE_MS){ _stopRecorderAuto(); return; }
      }
      if(now - _recStart >= _MAX_REC_MS){ _stopRecorderAuto(); return; }  // hard cap
      _silenceRAF = requestAnimationFrame(tick);
    };
    _silenceRAF = requestAnimationFrame(tick);
  } catch(err){ /* analyser unavailable -> manual tap-to-stop still works */ }
}
function _stopSilenceMonitor(){
  if(_silenceRAF){ cancelAnimationFrame(_silenceRAF); _silenceRAF = null; }
  _speechSeen = false; _silenceStart = 0; _recStart = 0;
  // NOTE: deliberately do NOT close _audioCtx or stop _voiceStream tracks here —
  // the context/analyser are reused across recordings and the mic stream must stay
  // alive for the page session (see _getVoiceStream / commit beb230b).
}
function _stopRecorderAuto(){
  if(_silenceRAF){ cancelAnimationFrame(_silenceRAF); _silenceRAF = null; }
  if(_voiceRecorder && _voiceRecorder.state !== 'inactive') _voiceRecorder.stop();
}
async function _getVoiceStream(){
  if(_voiceStream && _voiceStream.getTracks().every(t => t.readyState === 'live')) return _voiceStream;
  const timeout = new Promise((_, reject) => setTimeout(() => reject(new Error('mic timeout')), 8000));
  _voiceStream = await Promise.race([navigator.mediaDevices.getUserMedia({audio:true}), timeout]);
  return _voiceStream;
}
async function toggleVoiceCapture(){
  if(_voiceRecording){
    if(_voiceRecorder && _voiceRecorder.state !== 'inactive') _voiceRecorder.stop();
    return;
  }
  if(_ttsAudio){ _ttsAudio.pause(); setSpeaking(false); }
  let stream;
  try {
    stream = await _getVoiceStream();
  } catch(err){
    addBubble('⚠️ Microphone access denied or unavailable', 'bot');
    return;
  }
  _voiceChunks = [];
  try {
    _voiceRecorder = new MediaRecorder(stream);
  } catch(err){
    addBubble('⚠️ Microphone unavailable — try again', 'bot');
    return;
  }
  _voiceRecorder.ondataavailable = e => { if(e.data.size > 0) _voiceChunks.push(e.data); };
  _voiceRecorder.onstop = () => {
    // Do NOT stop the stream's tracks here — keep the mic stream alive across
    // recordings (see _getVoiceStream above) so the next tap doesn't have to
    // re-acquire it.
    _voiceRecording = false;
    _stopSilenceMonitor();
    _setVoiceCaptureUI(false);
    _stopSpeechRecognitionFallback();
    transcribeAndSend(new Blob(_voiceChunks, {type:'audio/webm'}));
  };
  try {
    _voiceRecorder.start();
  } catch(err){
    addBubble('⚠️ Could not start recording — try again', 'bot');
    return;
  }
  _startSpeechRecognitionFallback();
  _voiceRecording = true;
  _setVoiceCaptureUI(true);
  _startSilenceMonitor();
}
function _setVoiceCaptureUI(on){
  const pill = document.getElementById('talk-pill');
  if(pill) pill.classList.toggle('live', on);
  const talkSubEl = document.getElementById('talk-sub');
  if(talkSubEl) talkSubEl.textContent = on ? 'Listening…' : 'tap to speak';
}
function _useSpeechRecognitionFallbackText(){
  const talkSubEl = document.getElementById('talk-sub');
  if(talkSubEl) talkSubEl.textContent = 'tap to speak';
  const text = _speechRecognitionText.trim();
  if(text){ document.getElementById('chat-input').value = text; sendMsg(); }
  else { addBubble('⚠️ Could not transcribe audio', 'bot'); }
}
function transcribeAndSend(blob){
  const talkSubEl = document.getElementById('talk-sub');
  if(talkSubEl) talkSubEl.textContent = 'Transcribing…';
  fetchWithTimeout(BASE+'/api/voice/transcribe', {
    method:'POST',
    headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'audio/webm'},
    body: blob
  }, 30000).then(r=>{
    if(!r.ok) throw new Error('transcribe failed: '+r.status);
    return r.json();
  }).then(d=>{
    if(talkSubEl) talkSubEl.textContent = 'tap to speak';
    const text = (d.text||'').trim();
    if(text){ document.getElementById('chat-input').value = text; sendMsg(); }
    else { _useSpeechRecognitionFallbackText(); }
  }).catch(()=>{
    _useSpeechRecognitionFallbackText();
  });
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
  if (name === 'actions') loadActions();
  if (name === 'calendar') loadCalendar();
  if (name === 'memory') loadMemory();
  if (name === 'conversations') loadConversations();
  if (name === 'kb') loadKb();
  if (name === 'workflows') loadWorkflows();
  if (isMobileMode()) closeDrawer();
}
document.querySelectorAll('.nav-item').forEach(item=>{
  item.addEventListener('click',()=>showScreen(item.dataset.screen));
});

// ── Live Chat — ported verbatim (same protocol/session scheme) from the live Hub's
// chat-wrap at / (main.py). Same /ws/chat endpoint, same CHAT_SESSION localStorage key,
// so a conversation continues seamlessly whether Scott is on / or /frank. ──
let ws = null, wsReady = false, pendingMsg = null;
let _wsHeartbeat = null, _wsReconnectTimer = null, _wsRetries = 0, _wsManualClose = false;
let _historyApplied = false;
const CHAT_SESSION = (function(){
  let s = null;
  try { s = localStorage.getItem('chatSession'); } catch(e) {}
  if (!s) {
    s = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
        : 'sess-' + Date.now() + '-' + Math.random().toString(36).slice(2);
    try { localStorage.setItem('chatSession', s); } catch(e) {}
  }
  return s;
})();
// ── First-run welcome overlay — shows once unless dismissed, degrades to
// showing every time if localStorage is unavailable (same failure mode as
// the chatSession pattern above). ──
function dismissWelcomeOverlay() {
  const el = document.getElementById('welcome-overlay');
  if (el) el.style.display = 'none';
  try { localStorage.setItem('frankWelcomeSeen', '1'); } catch(e) {}
}
(function(){
  let seen = false;
  try { seen = !!localStorage.getItem('frankWelcomeSeen'); } catch(e) {}
  if (!seen) {
    const el = document.getElementById('welcome-overlay');
    if (el) el.style.display = 'flex';
  }
})();
// ── Offline dashboard cache — stale-but-useful data when wifi drops mid-session.
// Caches raw JSON (not rendered HTML) so it stays valid across template/CSS changes.
// No write-queueing here by design — todos/approvals need a live connection. ──
function cacheSet(key, data) {
  try { localStorage.setItem('hudCache:'+key, JSON.stringify({data, ts: Date.now()})); } catch(e) {}
}
function cacheGet(key) {
  try {
    const raw = localStorage.getItem('hudCache:'+key);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || !('data' in parsed) || !parsed.ts) return null;
    return parsed;
  } catch(e) { return null; }
}
function _offlineNote(ts) {
  return '<div style="color:var(--gold);font-size:10.5px;padding:4px 0">⚠ offline — showing data from '+_timeAgo(new Date(ts).toISOString())+'</div>';
}
function _clearStreaming(fallback) {
  const s = document.getElementById('bot-streaming');
  if (!s) return;
  s.id = '';
  s.classList.remove('typing');
  if (!s.textContent.trim() && fallback) s.textContent = fallback;
}
function _stopHeartbeat() { if (_wsHeartbeat) { clearInterval(_wsHeartbeat); _wsHeartbeat = null; } }
async function initWS() {
  if (_wsReconnectTimer) { clearTimeout(_wsReconnectTimer); _wsReconnectTimer = null; }
  _wsManualClose = false;
  let ticket;
  try {
    const r = await fetchWithTimeout(BASE+'/api/ws-ticket', {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 10000);
    if (!r.ok) throw new Error('ticket request failed: '+r.status);
    ticket = (await r.json()).ticket;
  } catch(e) {
    addBubble('⚠️ Could not start chat session — reload to retry', 'bot');
    return;
  }
  ws = new WebSocket(WS_BASE + '/ws/chat?ticket=' + encodeURIComponent(ticket) + '&session=' + encodeURIComponent(CHAT_SESSION));
  ws.onopen = () => {
    wsReady = true; _wsRetries = 0;
    _stopHeartbeat();
    _wsHeartbeat = setInterval(() => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({type:'ping'})); }, 25000);
    if (pendingMsg) { ws.send(JSON.stringify({message:pendingMsg, session:CHAT_SESSION})); pendingMsg=null; }
  };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'pong') return;
    if (d.type === 'history') {
      if (!_historyApplied && Array.isArray(d.messages)) {
        const c = document.getElementById('chat-msgs'); c.innerHTML = '';
        d.messages.forEach(m => addBubble(m.content, m.role === 'user' ? 'user' : 'bot'));
        _historyApplied = true; scrollMsgs();
      }
      return;
    }
    const bot = document.getElementById('bot-streaming');
    if (d.type === 'tool' && bot) {
      bot.classList.add('typing');
      if (!bot.dataset.real) bot.textContent = '⚙ ' + d.content;
      scrollMsgs();
    } else if (d.type === 'chunk' && bot) {
      if (!bot.dataset.real) { bot.textContent = ''; bot.dataset.real = '1'; bot.classList.remove('typing'); }
      bot.textContent += d.content; scrollMsgs();
    } else if (d.type === 'done') {
      const finalText = bot ? bot.textContent.trim() : '';
      _clearStreaming(); scrollMsgs();
      if (finalText) speakText(finalText);
    }
    else if (d.type === 'error') { _clearStreaming(); addBubble('⚠️ ' + d.content, 'bot'); }
  };
  ws.onerror = () => { _clearStreaming(); };
  ws.onclose = e => {
    wsReady = false; ws = null; _stopHeartbeat();
    _clearStreaming();
    if (e.code === 4001) { addBubble('Auth failed — reload to reconnect', 'bot'); return; }
    if (!_wsManualClose) {
      _wsRetries = Math.min(_wsRetries + 1, 5);
      const delay = Math.min(1000 * Math.pow(2, _wsRetries - 1), 15000);
      _wsReconnectTimer = setTimeout(() => { if (!ws) initWS(); }, delay);
    }
  };
}
function addBubble(text, who) {
  const el = document.createElement('div');
  el.className = 'lc-bubble ' + who;
  el.textContent = text;
  document.getElementById('chat-msgs').appendChild(el);
  scrollMsgs();
  return el;
}
function scrollMsgs() { const m=document.getElementById('chat-msgs'); m.scrollTop=m.scrollHeight; }
function sendMsg() {
  const inp = document.getElementById('chat-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  addBubble(text, 'user');
  const bot = addBubble('', 'bot typing');
  bot.id = 'bot-streaming';
  bot.textContent = '';
  if (wsReady) { ws.send(JSON.stringify({message:text, session:CHAT_SESSION})); }
  else { pendingMsg = text; if(!ws) initWS(); }
}
function sendChip(el) { document.getElementById('chat-input').value = el.textContent; sendMsg(); }
document.getElementById('chat-input').addEventListener('keydown', e => { if(e.key==='Enter') sendMsg(); });
initWS();

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
    cacheSet('agents', d);
    const tiles = d.agents.map(renderAgentTile).join('');
    if(cmdGrid) cmdGrid.innerHTML = tiles;
    if(fullGrid) fullGrid.innerHTML = tiles;
    const acAgents = document.getElementById('ac-agents');
    if(acAgents) acAgents.textContent = d.running_count + '/' + d.total_count + ' running';
  }catch(e){
    const cached = cacheGet('agents');
    if(cached){
      const tiles = _offlineNote(cached.ts) + cached.data.agents.map(renderAgentTile).join('');
      if(cmdGrid) cmdGrid.innerHTML = tiles;
      if(fullGrid) fullGrid.innerHTML = tiles;
    } else {
      const msg = '<div style="color:var(--red);font-size:11px;padding:8px">Agents offline: '+escHtml(e.message)+'</div>';
      if(cmdGrid) cmdGrid.innerHTML = msg;
      if(fullGrid) fullGrid.innerHTML = msg;
    }
  }
}

// ── Bottom-bar Relay indicator — real data from /api/relay/status ──
async function loadRelayStatus(){
  const el = document.getElementById('bb-relay');
  if(!el) return;
  try{
    const r = await authGet('/api/relay/status');
    const d = await r.json();
    if(d.killed){
      el.textContent = '🌐 Relay: Killed';
      el.style.color = 'var(--red)';
    } else if(d.connected){
      el.textContent = '🌐 Relay: Connected';
      el.style.color = 'var(--green)';
    } else {
      el.textContent = '🌐 Relay: Offline';
      el.style.color = 'var(--muted)';
    }
  }catch(e){
    el.textContent = '🌐 Relay: —';
    el.style.color = 'var(--muted)';
  }
}

// ── LLM Status + AI Core — real data from /api/credentials/status + /health ──
async function loadCredentialsAndHealth(){
  let cred = null, health = null, mem = null;
  try{ const r = await authGet('/api/credentials/status'); cred = await r.json(); }catch(e){}
  try{ const r = await fetchWithTimeout(BASE+'/health', {}, 10000); health = await r.json(); }catch(e){}
  try{ const r = await authGet('/api/memory'); mem = await r.json(); }catch(e){}

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
  const voiceEl = document.getElementById('ac-voice');
  const voiceDot = document.getElementById('ac-voice-dot');
  if(health){
    if(acCore){ acCore.textContent = 'Online · build '+escHtml(health.build||'?'); acCore.className='v'; }
    if(acSystem){
      acSystem.textContent = health.persistent ? 'Persistent storage' : 'Ephemeral (volume not attached)';
      acSystem.className = 'v'+(health.persistent?'':' warn');
    }
    // Voice (mic capture + /api/voice/transcribe + /api/voice/speak) is a stateless
    // feature of this same server — it has no dependency on the local relay, so it's
    // "Online" whenever the server itself answers /health (mislabeled as relay-bound
    // "not built yet" before 2026-06-23, see ops_runbook.md).
    if(voiceEl){
      voiceEl.textContent = 'Online';
      voiceEl.className = 'v';
      if(voiceDot) voiceDot.className = 'dotc';
    }
    coreRows.unshift('<div class="core-row"><span class="lab"><span class="dotc"></span>Build</span><span class="v">'+escHtml(health.build||'?')+'</span></div>');
    coreRows.push('<div class="core-row"><span class="lab"><span class="dotc'+(health.persistent?'':' warn')+'"></span>Storage</span><span class="v'+(health.persistent?'':' warn')+'">'+(health.persistent?'Persistent volume attached':'Ephemeral — resets on redeploy')+'</span></div>');
  } else {
    if(acCore){ acCore.textContent = 'Offline'; acCore.className='v err'; }
    if(voiceEl){
      voiceEl.textContent = 'Offline';
      voiceEl.className = 'v err';
      if(voiceDot) voiceDot.className = 'dotc err';
    }
  }

  const acMemory = document.getElementById('ac-memory');
  if(acMemory){
    if(mem){
      acMemory.textContent = mem.total_sessions + ' sessions · ' + mem.learnings_count + ' learnings';
      acMemory.className = 'v';
    } else {
      acMemory.textContent = 'Unavailable';
      acMemory.className = 'v warn';
    }
  }

  const coreDetail = document.getElementById('core-detail');
  if(coreDetail){
    coreDetail.innerHTML = coreRows.length ? coreRows.join('') :
      '<div class="core-row"><span class="lab"><span class="dotc err"></span>Unavailable</span><span class="v err">Could not load</span></div>';
  }
}

// ── Shop Performance — real data from /api/analytics + /api/metrics ──
function _miniSpark(values, color){
  var h = 16;
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
function _renderShopPerf(a, m, sparkEl, chipEl, offlineNote){
  const tr = a.trends||{}, lt = a.latest||{}, del = a.delta||{};
  if(sparkEl){
    sparkEl.innerHTML = (offlineNote||'') +
      '<div class="shop-spark-card"><div class="ssc-lab">Revenue · 30d</div>'+
        '<div class="ssc-valrow"><div class="ssc-val">'+(lt.revenue_30d!=null?'$'+lt.revenue_30d.toFixed(2):'—')+'</div>'+
        '<div class="ssc-delta">'+_miniDelta(del.revenue_30d,true)+'</div></div>'+
        '<div class="ssc-spark">'+_miniSpark(tr.revenue_30d,'var(--gold)')+'</div></div>'+
      '<div class="shop-spark-card"><div class="ssc-lab">Orders · 30d</div>'+
        '<div class="ssc-valrow"><div class="ssc-val">'+(lt.orders_30d!=null?lt.orders_30d:'—')+'</div>'+
        '<div class="ssc-delta">'+_miniDelta(del.orders_30d,false)+'</div></div>'+
        '<div class="ssc-spark">'+_miniSpark(tr.orders_30d,'var(--cyan2)')+'</div></div>';
  }
  const allTimeRev = (m.orders && m.orders.all_time_revenue!=null) ? m.orders.all_time_revenue : null;
  if(chipEl){
    chipEl.innerHTML =
      '<div class="shop-chip"><div class="nm">Listings</div><div class="v">'+(lt.active_listings!=null?lt.active_listings:'—')+'</div></div>'+
      '<div class="shop-chip"><div class="nm">Total Sales</div><div class="v">'+(lt.total_sales!=null?lt.total_sales:'—')+'</div></div>'+
      '<div class="shop-chip"><div class="nm">All-Time Revenue</div><div class="v">'+(allTimeRev!=null?'$'+allTimeRev.toFixed(2):'—')+'</div></div>';
  }
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
    cacheSet('shopPerf', {a, m});
    _renderShopPerf(a, m, sparkEl, chipEl, null);
  }catch(e){
    const cached = cacheGet('shopPerf');
    if(cached){
      _renderShopPerf(cached.data.a, cached.data.m, sparkEl, chipEl, _offlineNote(cached.ts));
    } else if(sparkEl){
      sparkEl.innerHTML = '<div style="color:var(--red);font-size:11px;padding:4px">Shop data offline</div>';
    }
  }
}

function _timeAgo(iso){
  if(!iso) return '';
  const ms = Date.now() - new Date(iso).getTime();
  if(!(ms >= 0)) return '';
  const m = Math.floor(ms/60000);
  if(m < 1) return 'just now';
  if(m < 60) return m+'m ago';
  const h = Math.floor(m/60);
  if(h < 24) return h+'h ago';
  return Math.floor(h/24)+'d ago';
}

// ── Live Intelligence Feed — real data from /api/queue (pending staged actions) ──
function _renderQueue(d, list, offlineNote){
  if(list){
    const items = d.actions.slice(0, 6);
    list.innerHTML = (offlineNote||'') + (items.length ? items.map(a=>
      '<div class="feed-item"><div class="ftxt">'+escHtml(a.summary)+'<div class="t">'+_timeAgo(a.created_at)+'</div></div>'+
      '<span class="feed-tag tip">PENDING</span></div>'
    ).join('') : '<div style="color:var(--muted);font-size:12px">No pending actions — queue is clear.</div>');
  }
}
async function loadQueue(){
  const list = document.getElementById('feed-list');
  try{
    const r = await authGet('/api/queue?status=pending');
    const d = await r.json();
    cacheSet('queue', d);
    _renderQueue(d, list, null);
    // Keep the Action Center nav badge fresh on the 30s loop without re-rendering
    // the Action Center screen itself (loadActions() is intentionally NOT in loadAll()).
    setActionBadge(_actionsSummary, (d.actions||[]).length);
  }catch(e){
    const cached = cacheGet('queue');
    if(cached){
      _renderQueue(cached.data, list, _offlineNote(cached.ts));
      setActionBadge(_actionsSummary, (cached.data.actions||[]).length);
    } else if(list){
      list.innerHTML = '<div style="color:var(--red);font-size:12px">Feed offline: '+escHtml(e.message)+'</div>';
    }
  }
}

// ── Mission Timeline — real data from /api/todos (open tasks only, compact view) ──
function _renderMissionTimeline(d, list, offlineNote){
  if(list){
    const open = d.todos.filter(t=>!t.done)
      .sort((a,b)=>new Date(a.created_at)-new Date(b.created_at))
      .slice(0, 6);
    list.innerHTML = (offlineNote||'') + (open.length ? open.map(t=>{
      const day = t.created_at ? new Date(t.created_at).toLocaleDateString(undefined,{weekday:'short'}).toUpperCase() : '—';
      return '<div class="tl-item"><div class="tl-time">'+day+'</div><div class="tl-dotcol"><span class="d"></span></div>'+
        '<div class="tl-txt"><div class="ttl">'+escHtml(t.text)+'</div>'+
        '<div class="sub">added by '+escHtml(t.added_by||'scott')+'</div></div></div>';
    }).join('') : '<div style="color:var(--muted);font-size:12px">All caught up — no open tasks.</div>');
  }
}
async function loadMissionTimeline(){
  const list = document.getElementById('timeline-list');
  try{
    const r = await authGet('/api/todos');
    const d = await r.json();
    cacheSet('missionTimeline', d);
    _renderMissionTimeline(d, list, null);
  }catch(e){
    const cached = cacheGet('missionTimeline');
    if(cached){
      _renderMissionTimeline(cached.data, list, _offlineNote(cached.ts));
    } else if(list){
      list.innerHTML = '<div style="color:var(--red);font-size:12px">Timeline offline: '+escHtml(e.message)+'</div>';
    }
  }
}

// ── Tasks — real data from /api/todos ──
function _renderTasks(d, list, offlineNote){
  if(list){
    list.innerHTML = (offlineNote||'') + (d.todos.length ? d.todos.map(t=>{
      const done = !!t.done;
      const overdue = !done && t.due_date && t.due_date < new Date().toISOString().slice(0,10);
      const dueTxt = t.due_date ? ' · due '+escHtml(t.due_date)+(overdue?' ⚠':'') : '';
      return '<div class="tl-item">'+
        '<div class="tl-dotcol"><input type="checkbox" '+(done?'checked':'')+' onchange="toggleHudTodo('+t.id+',this.checked)" style="width:13px;height:13px;margin-top:2px;accent-color:var(--gold)"></div>'+
        '<div class="tl-txt"><div class="ttl"'+(done?' style="text-decoration:line-through;color:var(--muted)"':(overdue?' style="color:var(--red)"':''))+'>'+escHtml(t.text)+'</div>'+
        '<div class="sub">added by '+escHtml(t.added_by||'scott')+dueTxt+'</div></div>'+
        '<button onclick="deleteHudTodo('+t.id+')" style="background:none;border:none;color:var(--muted);font-size:13px;cursor:pointer;padding:2px 4px;flex-shrink:0">✕</button></div>';
    }).join('') : '<div style="color:var(--muted);font-size:12px">No tasks yet.</div>');
  }
}
async function loadTasks(){
  const list = document.getElementById('tasks-list');
  try{
    const r = await authGet('/api/todos');
    const d = await r.json();
    cacheSet('tasks', d);
    _renderTasks(d, list, null);
    const badge = document.getElementById('badge-tasks');
    if(badge){ badge.textContent = d.open_count; badge.style.display = d.open_count>0 ? '' : 'none'; }
  }catch(e){
    const cached = cacheGet('tasks');
    if(cached){
      _renderTasks(cached.data, list, _offlineNote(cached.ts));
      const badge = document.getElementById('badge-tasks');
      if(badge){ badge.textContent = cached.data.open_count; badge.style.display = cached.data.open_count>0 ? '' : 'none'; }
    } else if(list){
      list.innerHTML = '<div style="color:var(--red);font-size:12px">Tasks offline: '+escHtml(e.message)+'</div>';
    }
  }
}
async function addHudTodo(){
  const inp = document.getElementById('hud-todo-input');
  const dueInp = document.getElementById('hud-todo-due');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  const due = dueInp.value;
  dueInp.value = '';
  try {
    await fetchWithTimeout(BASE+'/api/todos', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({text, added_by:'scott', due_date: due || null}),
    }, 15000);
  } catch(e) {}
  loadTasks();
}
async function toggleHudTodo(id, done){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id+'/toggle', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({done}),
    }, 15000);
  } catch(e) {}
  loadTasks();
}
async function deleteHudTodo(id){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id, {method:'DELETE',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) {}
  loadTasks();
}

// ── Tools & Skills — real data from /api/tools/list (live AGENT_TOOLS registry) ──
function _renderTools(d, list, offlineNote){
  if(list){
    list.innerHTML = (offlineNote||'') + d.tools.map(t=>
      '<div style="padding:10px 0;border-bottom:1px solid var(--border)">'+
        '<div style="font-weight:600;font-size:12px;color:var(--text)">'+escHtml(t.name)+'</div>'+
        '<div style="font-size:10.5px;color:var(--muted);margin-top:3px">'+escHtml(t.description)+'</div></div>'
    ).join('');
  }
}
async function loadTools(){
  const list = document.getElementById('tools-list');
  try{
    const r = await authGet('/api/tools/list');
    const d = await r.json();
    cacheSet('tools', d);
    _renderTools(d, list, null);
    const badge = document.getElementById('badge-tools');
    if(badge){ badge.textContent = d.count; badge.style.display = ''; }
  }catch(e){
    const cached = cacheGet('tools');
    if(cached){
      _renderTools(cached.data, list, _offlineNote(cached.ts));
      const badge = document.getElementById('badge-tools');
      if(badge){ badge.textContent = cached.data.count; badge.style.display = ''; }
    } else if(list){
      list.innerHTML = '<div style="color:var(--red);font-size:12px">Tools offline: '+escHtml(e.message)+'</div>';
    }
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Action Center — ported from the live Hub's Action Center at / (main.py).
// The approve/reject queue is the human-in-the-loop safety gate for every Etsy
// write and local file/exec action — the confirm() in approveAction() below IS
// that gate and must never be removed. Same /api/queue + /api/actions endpoints,
// zero backend changes.
// ══════════════════════════════════════════════════════════════════════════
let _actions = [];
let _pendingActions = [];
let _actionsSummary = {high:0,medium:0,low:0};
let _actionFilter = null; // 'high' | 'medium' | 'low' | null (= all)
function setActionBadge(summary, pending) {
  const b = document.getElementById('badge-actions');
  if (!b) return;
  const n = ((summary && summary.high) || 0) + (pending || 0);  // urgent + awaiting approval
  if (n > 0) { b.textContent = n > 99 ? '99+' : n; b.style.display = ''; }
  else { b.style.display = 'none'; }
}
function simpleLineDiff(before, after) {
  const b = String(before == null ? '' : before).split('\\n');
  const a = String(after == null ? '' : after).split('\\n');
  const max = Math.max(b.length, a.length);
  let html = '';
  for (let i = 0; i < max; i++) {
    const bl = b[i], al = a[i];
    if (bl === al) {
      if (bl !== undefined) html += `<div style="color:var(--muted)">&nbsp;&nbsp;${escHtml(bl)}</div>`;
    } else {
      if (bl !== undefined) html += `<div style="color:var(--red)">-&nbsp;${escHtml(bl)}</div>`;
      if (al !== undefined) html += `<div style="color:var(--green)">+&nbsp;${escHtml(al)}</div>`;
    }
  }
  return html;
}
const _ACT_TYPE_GLYPH = {
  update_title: '📝', update_tags: '🏷️', publish_listing: '🏷️', deactivate_listing: '⛔',
  listing_photo: '🖼️', local_write_file: '📁', local_delete: '🗑️', local_exec: '⚙️', run_script: '⚙️'
};
function _actAgeStr(a) {
  const t = a.staged_at || a.created_at || a.decided_at;
  if (!t) return '';
  const ms = Date.now() - new Date(t).getTime();
  if (!isFinite(ms) || ms < 0) return '';
  const mins = Math.round(ms / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  return Math.round(hrs / 24) + 'd ago';
}
function _actionPreviewHtml(a) {
  const p = a.payload || {};
  if (a.type === 'update_title') return 'New title: ' + escHtml(p.title || '');
  if (a.type === 'update_tags') return 'New tags: ' + escHtml((p.tags || []).join(', '));
  if (a.type === 'listing_photo') {
    const url = BASE+'/api/files/download?root=staged_photos&path='+encodeURIComponent(p.path||'')+'&token='+encodeURIComponent(TOKEN)+'&inline=1';
    return `<img src="${url}" loading="lazy" style="max-width:260px;max-height:260px;border-radius:8px;display:block">` +
      `<div style="margin-top:6px">Listing ${escHtml(String(p.listing_id||''))} · rank ${p.rank||''} · ${escHtml(p.sku||'')}</div>`;
  }
  if (a.type === 'publish_listing') {
    const pv = p.preview || {};
    return `<div style="display:flex;gap:10px;align-items:flex-start">` +
      (pv.thumbnail_url
        ? `<img src="${escHtml(pv.thumbnail_url)}" loading="lazy" style="width:70px;height:70px;border-radius:8px;object-fit:cover;flex-shrink:0">`
        : '') +
      `<div><div>Publish draft listing ${escHtml(String(p.listing_id || ''))}</div>` +
      (pv.title ? `<div style="font-weight:600;margin-top:4px">${escHtml(pv.title)}</div>` : '') +
      (pv.price != null ? `<div>$${escHtml(String(pv.price))} · ${(pv.tags || []).length} tags · ${pv.photo_count || 0} photos</div>` : '') +
      (pv.error ? `<div style="color:var(--gold)">⚠️ Preview unavailable: ${escHtml(pv.error)}</div>` : '') +
      `</div></div>`;
  }
  if (a.type === 'local_write_file') {
    const diffHtml = simpleLineDiff(p.before, p.after);
    return `<div style="margin-bottom:6px"><strong>File:</strong> ${escHtml(p.path || '')}</div>` +
      (p.before_existed === false ? `<div style="color:var(--gold);margin-bottom:6px">⚠️ File does not currently exist — this will create it.</div>` : '') +
      `<div style="max-height:260px;overflow:auto;background:var(--bg);border-radius:8px;padding:8px;font-family:monospace;font-size:12px;white-space:pre-wrap">${diffHtml || '<span style="color:var(--muted)">No changes</span>'}</div>`;
  }
  if (a.type === 'local_delete') {
    return `<div style="color:var(--red)">⚠️ This will permanently delete:</div><div style="font-family:monospace;margin-top:4px">${escHtml(p.path || '')}</div>`;
  }
  if (a.type === 'local_exec') {
    return `<div><strong>Run:</strong> <span style="font-family:monospace">${escHtml(p.command || '')}${p.extra_args ? ' ' + escHtml(p.extra_args) : ''}</span></div>`;
  }
  if (a.type === 'run_script') {
    return `<div><strong>Run:</strong> <span style="font-family:monospace">python tools/${escHtml(p.command || '')}.py${p.extra_args ? ' ' + escHtml(p.extra_args) : ''}</span></div>` +
      `<div class="sub" style="margin-top:4px">Script output isn't previewable before approval — it will run for real on approve.</div>`;
  }
  return '';
}
function renderApproval(a) {
  const p = a.payload || {};
  let thumb;
  if (a.type === 'listing_photo') {
    const url = BASE+'/api/files/download?root=staged_photos&path='+encodeURIComponent(p.path||'')+'&token='+encodeURIComponent(TOKEN)+'&inline=1';
    thumb = `<img class="hub-thumb" src="${url}" loading="lazy">`;
  } else if (a.type === 'publish_listing' && (p.preview || {}).thumbnail_url) {
    thumb = `<img class="hub-thumb" src="${escHtml(p.preview.thumbnail_url)}" loading="lazy">`;
  } else {
    thumb = `<div class="hub-thumb-ph">${_ACT_TYPE_GLYPH[a.type] || '❓'}</div>`;
  }
  let meta = a.type.replace(/_/g, ' ');
  const age = _actAgeStr(a);
  if (age) meta += ' · ' + age;
  if (a.type === 'listing_photo') meta += ` · ${escHtml(p.sku || '')} · rank ${p.rank || ''}`;
  else if (a.type === 'publish_listing' && (p.preview || {}).price != null) {
    meta += ` · $${escHtml(String(p.preview.price))} · ${(p.preview.tags || []).length} tags · ${p.preview.photo_count || 0} photos`;
  } else if (a.type === 'update_title') meta += ` · "${escHtml(p.title || '')}"`;
  else if (a.type === 'update_tags') meta += ` · ${escHtml((p.tags || []).join(', '))}`;
  return `<div class="hub-listing-item" style="cursor:pointer" onclick="toggleActionDetail(${a.id})">
    ${thumb}
    <div class="hub-listing-info">
      <div class="hub-listing-title">${escHtml(a.summary || a.type)}</div>
      <div class="hub-listing-meta">${escHtml(meta)}</div>
    </div>
    <div class="act-btns" style="flex-shrink:0" onclick="event.stopPropagation()">
      <button class="act-btn approve" onclick="approveAction(${a.id})">Approve</button>
      ${a.type === 'publish_listing' ? `<button class="act-btn" onclick="fixDraftStage(${(p.listing_id||0)},${a.id},this)">🤖 Fix</button>` : ''}
      <button class="act-btn reject" onclick="openRejectModal(${a.id})">Reject</button>
    </div>
  </div>
  <div id="act-detail-${a.id}" class="hub-listing-detail" style="display:none"></div>
  <div id="reject-modal-${a.id}" style="display:none"></div>`;
}
function toggleActionDetail(id) {
  const panel = document.getElementById('act-detail-'+id);
  if (!panel) return;
  if (panel.style.display !== 'none') { panel.style.display = 'none'; return; }
  const a = (_pendingActions || []).find(x => x.id === id);
  if (a) panel.innerHTML = _actionPreviewHtml(a);
  panel.style.display = 'block';
}
const _APPROVE_CONFIRM_MSGS = {
  local_write_file: 'Approve and write this file on your computer now?',
  local_delete: 'Approve and PERMANENTLY DELETE this file on your computer now?',
  local_exec: 'Approve and run this command on your computer now?',
  run_script: 'Approve and run this workflow script now?'
};
async function approveAction(id) {
  const act = (_pendingActions || []).find(x => x.id === id);
  const msg = (act && _APPROVE_CONFIRM_MSGS[act.type]) || 'Approve and apply this change to your live Etsy listing now?';
  if (!confirm(msg)) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/approve', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 50000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    loadActions();
  } catch(e) { showToast('Could not apply: ' + (e.message||e), 'err', 6000); }
}
function openRejectModal(id) {
  const panel = document.getElementById('reject-modal-'+id);
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  document.querySelectorAll('[id^="reject-modal-"]').forEach(el => el.style.display = 'none');
  if (isOpen) return;
  panel.innerHTML = `<div style="padding:10px 0;border-bottom:1px solid var(--border)">
    <div class="hub-listing-meta" style="margin-bottom:6px">Why is this being rejected? A reason lets the right agent fix and re-stage it automatically.</div>
    <textarea id="reject-reason-${id}" rows="2" placeholder="e.g. shade is too dark, brighten it"
      style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);border-radius:8px;color:var(--text);padding:8px;font-size:13px;font-family:inherit"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="act-btn reject" onclick="submitRejectReason(${id})">Submit &amp; Fix</button>
      <button class="act-btn" onclick="document.getElementById('reject-modal-${id}').style.display='none'">Cancel</button>
    </div>
  </div>`;
  panel.style.display = 'block';
}
async function submitRejectReason(id) {
  const ta = document.getElementById('reject-reason-'+id);
  const reason = (ta && ta.value || '').trim();
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/reject', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({reason})
    }, 15000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (d.fix_started) {
      const panel = document.getElementById('reject-modal-'+id);
      if (panel) panel.innerHTML = '<div class="hub-listing-meta" style="padding:8px 0">🤖 Fixing — check back in a minute, the corrected version will appear as a new pending item.</div>';
    }
    loadActions();
  } catch(e) { showToast('Could not reject: ' + (e.message||e), 'err', 6000); }
}
async function fixDraftStage(listingId, actionId, btn) {
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Fixing…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/draft/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},120000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const n = d.staged_count||0;
    btn.textContent = n > 0 ? n+' fix'+(n>1?'es':'')+' staged ✅' : '⚠️ No auto-fixes';
    if (n > 0) { btn.style.background='var(--green)'; btn.style.color='#06140d'; }
    const errNote = (d.errors&&d.errors.length) ? ' Errors: '+d.errors.join(', ') : '';
    showToast('Staged '+n+' fix'+(n!==1?'es':'')+'. Approve the new fixes in Action Center, then come back to approve Publish.'+errNote, 'ok');
    loadActions();
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    showToast('Could not fix draft: '+(e.message||e), 'err', 6000);
  }
}
async function loadActions() {
  const el = document.getElementById('actions-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const [ar, qr] = await Promise.all([
      authGet('/api/actions', 25000),
      authGet('/api/queue?status=pending', 15000).catch(()=>null)
    ]);
    if (!ar.ok) { const e = await ar.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+ar.status); }
    const d = await ar.json();
    let pending = [];
    if (qr && qr.ok) { const qd = await qr.json().catch(()=>({})); pending = qd.actions || []; }
    _actions = d.actions || [];
    _pendingActions = pending;
    _actionsSummary = d.summary || {high:0,medium:0,low:0};
    setActionBadge(_actionsSummary, pending.length);
    renderActionsContent();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadActions()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setActionFilter(sev) {
  _actionFilter = (_actionFilter === sev) ? null : sev; // tap again to clear
  renderActionsContent();
}
const _SEV_COLORS = {high:'var(--red)', medium:'var(--gold)', low:'#7ba0c2'};
function renderActionsContent() {
  const el = document.getElementById('actions-content');
  if (!el) return;
  const pending = _pendingActions || [];
  const s = _actionsSummary || {high:0,medium:0,low:0};
  let html = '';
  if (pending.length) {
    html += `<div class="section-title">⏳ Awaiting your approval (${pending.length})</div>`;
    html += pending.map(renderApproval).join('');
  }
  if (!_actions.length && !pending.length) { el.innerHTML = html || '<div class="empty">✅ All clear — no action items right now.</div>'; return; }
  const sevBtn = sev => {
    const active = _actionFilter === sev;
    const c = _SEV_COLORS[sev];
    const style = active
      ? `flex:1;text-align:center;padding:10px 6px;cursor:pointer;border-color:${c};background:${c}26`
      : 'flex:1;text-align:center;padding:10px 6px;cursor:pointer';
    return `<div class="metric" style="${style}" onclick="setActionFilter('${sev}')"><div class="value" style="color:${c};font-size:20px">${s[sev]||0}</div><div class="sub">${sev}${active?' ✓':''}</div></div>`;
  };
  html += `<div class="section-title">Flagged by scan${_actionFilter?` — showing ${_actionFilter} only`:''}</div><div style="display:flex;gap:8px;margin-bottom:14px">`+
    sevBtn('high')+sevBtn('medium')+sevBtn('low')+
    `</div>`;
  const filtered = _actionFilter ? _actions.filter(a => a.severity === _actionFilter) : _actions;
  if (!filtered.length) {
    html += `<div class="empty">No ${escHtml(_actionFilter)} severity items.</div>`;
  } else {
    html += filtered.map(a => {
      const i = _actions.indexOf(a);
      return `
      <div class="act-card ${escHtml(a.severity)}">
        <span class="act-sev ${escHtml(a.severity)}">${escHtml(a.severity)}</span>
        <div class="act-title">${escHtml(a.title)}</div>
        <div class="act-detail">${escHtml(a.detail)}</div>
        <div class="act-sug"><b>💡 Fix:</b> ${escHtml(a.suggestion)}</div>
        <div class="act-btns">
          <button class="act-btn primary" onclick="askActionFix(${i})">Ask CEO</button>
          ${a.url ? `<a class="act-btn" href="${escHtml(a.url)}" target="_blank">Open on Etsy</a>` : ''}
        </div>
      </div>`;
    }).join('');
  }
  el.innerHTML = html;
}
function askActionFix(i) {
  const a = _actions[i];
  if (!a) return;
  showScreen('cmd');
  const q = 'How should I fix this? ' + a.title + ' — ' + a.detail;
  const inp = document.getElementById('chat-input');
  inp.value = q;
  sendMsg();
}
async function batchStageTags(btn) {
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '⏳ Generating…';
  showToast('Scanning active listings for tag fixes — this may take up to 2 minutes…', 'info');
  try {
    const r = await fetchWithTimeout(BASE+'/api/batch/stage-tags', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 180000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const errNote = d.errors && d.errors.length ? ` ${d.errors.length} listing(s) had tag-length issues and were skipped.` : '';
    showToast(d.message + errNote, 'ok');
    loadActions();
  } catch(e) {
    showToast('Error: ' + (e.name==='AbortError'?'Request timed out — the batch is still running server-side; check the Action Center in a moment':(e.message||e)), 'err', 6000);
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

// ── Calendar — real data from /api/cadence + /api/todos: due-dated tasks,
// recurring weekly/monthly/quarterly ops cadence, and the seasonal keyword +
// tax deadline calendar. List-based (not a grid) — same .act-card pattern as
// the Action Center, since data volume (~15-20 dated items/year) doesn't
// justify a calendar-grid widget. ──
const _CAL_URGENCY_SEV = {OVERDUE:'high', 'THIS WEEK':'high', SOON:'medium', UPCOMING:'low'};
async function loadCalendar() {
  const el = document.getElementById('calendar-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const [cr, tr] = await Promise.all([
      authGet('/api/cadence', 20000),
      authGet('/api/todos', 15000).catch(()=>null)
    ]);
    if (!cr.ok) { const e = await cr.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+cr.status); }
    const d = await cr.json();
    renderCalendarContent(d);
    const badge = document.getElementById('badge-calendar');
    if (badge) {
      const urgent = (d.seasonal||[]).concat(d.tax_deadlines||[]).filter(e=>e.urgency==='OVERDUE'||e.urgency==='THIS WEEK').length
        + (d.due_todos||[]).length;
      badge.textContent = urgent;
      badge.style.display = urgent>0 ? '' : 'none';
    }
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadCalendar()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function _calCard(sev, title, detail) {
  return `<div class="act-card ${sev}"><span class="act-sev ${sev}">${escHtml(sev)}</span><div class="act-title">${escHtml(title)}</div><div class="act-detail">${escHtml(detail)}</div></div>`;
}
function renderCalendarContent(d) {
  const el = document.getElementById('calendar-content');
  if (!el) return;
  let html = '';

  const due = d.due_todos || [];
  html += `<div class="section-title">📌 Upcoming Due Dates (${due.length})</div>`;
  html += due.length ? due.map(t => {
    const overdue = t.due_date < new Date().toISOString().slice(0,10);
    return _calCard(overdue?'high':'low', t.text, 'Due ' + t.due_date);
  }).join('') : '<div class="empty">No to-dos with a due date.</div>';

  html += `<div class="section-title">🔁 This Week's Cadence</div>`;
  const cl = d.checklists || {weekly:[],monthly:[],quarterly:[]};
  html += `<div class="act-card low" style="cursor:default">
    <div class="act-title">Weekly (Friday)</div>
    <ul style="margin:6px 0 10px 18px;padding:0;font-size:11.5px;color:var(--muted)">${cl.weekly.map(i=>`<li>${escHtml(i)}</li>`).join('')}</ul>
    <div class="act-title">Monthly (1st)</div>
    <ul style="margin:6px 0 10px 18px;padding:0;font-size:11.5px;color:var(--muted)">${cl.monthly.map(i=>`<li>${escHtml(i)}</li>`).join('')}</ul>
    <div class="act-title">Quarterly</div>
    <ul style="margin:6px 0 0 18px;padding:0;font-size:11.5px;color:var(--muted)">${cl.quarterly.map(i=>`<li>${escHtml(i)}</li>`).join('')}</ul>
  </div>`;

  const seasonal = d.seasonal || [];
  const tax = d.tax_deadlines || [];
  html += `<div class="section-title">🗓 Seasonal &amp; Tax Calendar</div>`;
  if (!seasonal.length && !tax.length) {
    html += '<div class="empty">Nothing upcoming.</div>';
  } else {
    html += seasonal.map(e => _calCard(
      _CAL_URGENCY_SEV[e.urgency]||'low',
      `${e.season} — update by ${e.update_by}`,
      `Peak ${e.peak} · ${e.urgency} · listings: ${e.listings_to_update.join(', ')}`
    )).join('');
    html += tax.map(t => _calCard(
      _CAL_URGENCY_SEV[t.urgency]||'low',
      t.event,
      `${t.date} · ${t.urgency}`
    )).join('');
  }

  el.innerHTML = html;
}

// ══════════════════════════════════════════════════════════════════════════
// Memory — real data: /api/memory — a single read-only rollup, not a third
// document/session browser (Conversations owns session drill-down, Knowledge
// Base owns the doc browser/search). Shows aggregate counts plus the one
// thing with no UI anywhere else in the app: the CEO learnings log itself.
// Also feeds the Command Center's "Memory Insights" preview widget from the
// same payload — no second request needed.
// ══════════════════════════════════════════════════════════════════════════
async function loadMemory() {
  const el = document.getElementById('memory-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/memory', 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderMemory(d);
    const badge = document.getElementById('badge-memory');
    if (badge) {
      badge.textContent = d.learnings_count > 999 ? '999+' : d.learnings_count;
      badge.style.display = d.learnings_count > 0 ? '' : 'none';
    }
    updateMemoryWidget(d);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadMemory()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderMemory(d) {
  const el = document.getElementById('memory-content');
  if (!el) return;
  let html = '<div style="display:flex;gap:8px;margin-bottom:14px">' +
    `<div class="metric" style="flex:1;text-align:center"><div class="value">${d.total_sessions}</div><div class="sub">Sessions</div></div>` +
    `<div class="metric" style="flex:1;text-align:center"><div class="value">${d.total_messages}</div><div class="sub">Messages</div></div>` +
    `<div class="metric" style="flex:1;text-align:center"><div class="value">${d.kb_doc_count}</div><div class="sub">KB Docs</div></div>` +
    `<div class="metric" style="flex:1;text-align:center"><div class="value">${d.learnings_count}</div><div class="sub">Learnings logged</div></div>` +
    '</div>';
  const oldest = _timeAgo(d.oldest_at), newest = _timeAgo(d.newest_at);
  html += `<div class="sub" style="margin-bottom:14px">` +
    (d.total_sessions ? `History spans ${escHtml(oldest||'—')} to ${escHtml(newest||'just now')} — ` : '') +
    `<a href="#" onclick="showScreen('conversations');return false" style="color:var(--cyan2)">view full history ›</a></div>`;
  html += '<div class="section-title">🧠 What Frank has logged</div>';
  if (!d.learnings.length) {
    html += '<div class="empty">No durable insights logged yet — Frank appends a line here whenever a conversation surfaces a pattern worth remembering.</div>';
  } else {
    html += d.learnings.map(l => `<div class="tl-item">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(l.note)}</div>
        <div class="sub">${escHtml(l.date)}</div>
      </div>
    </div>`).join('');
  }
  html += '<div class="section-title">📚 Knowledge Base</div>';
  html += `<div class="empty" style="padding:14px 0"><a href="#" onclick="showScreen('kb');return false" style="color:var(--cyan2)">${d.kb_doc_count} doc${d.kb_doc_count===1?'':'s'} in the knowledge base ›</a></div>`;
  el.innerHTML = html;
}

function updateMemoryWidget(d) {
  const memEl = document.getElementById('mem-stat-memories');
  const turnsEl = document.getElementById('mem-stat-turns');
  if (memEl) memEl.textContent = d.learnings_count;
  if (turnsEl) turnsEl.textContent = d.total_messages;
  drawMem(d.recent_session_sizes || []);
}

// ══════════════════════════════════════════════════════════════════════════
// Workflows — real data: /api/workflows, live off the same _EXEC_COMMANDS
// registry the execute_command chat tool already runs against. Most run
// directly and show output inline; the one mutating command
// (backup_digital_products) stages through the same action_queue Action
// Center uses, via the run_script staged-action type. Static inventory —
// loaded once at init, not on the 30s loadAll() poll.
// ══════════════════════════════════════════════════════════════════════════
async function loadWorkflows() {
  const el = document.getElementById('workflows-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/workflows', 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderWorkflows(d.workflows || []);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadWorkflows()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderWorkflows(workflows) {
  const el = document.getElementById('workflows-content');
  if (!el) return;
  if (!workflows.length) {
    el.innerHTML = '<div class="empty">No workflows registered.</div>';
    return;
  }
  el.innerHTML = workflows.map(w => {
    const badge = w.requires_approval
      ? '<span class="act-sev medium">needs approval</span>'
      : (w.long_running ? '<span class="act-sev low">background</span>' : '<span class="act-sev approval">instant</span>');
    return `<div class="act-card low">
      ${badge}
      <div class="act-title">${escHtml(w.name)}</div>
      <div class="act-detail">${escHtml(w.description)}</div>
      <div class="act-btns">
        <button class="act-btn primary" onclick="runWorkflow('${escHtml(w.id)}', this, ${w.requires_approval ? 'true' : 'false'})">▶ Run</button>
      </div>
      <div id="wf-result-${escHtml(w.id)}" style="margin-top:9px"></div>
    </div>`;
  }).join('');
}

async function runWorkflow(id, btn, requiresApproval) {
  if (!requiresApproval && !confirm('Run this workflow now?')) return;
  const resultEl = document.getElementById('wf-result-' + id);
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Running…';
  if (resultEl) resultEl.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/workflows/'+id+'/run', {method:'POST',headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},body:'{}'}, 150000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (d.staged) {
      if (resultEl) resultEl.innerHTML = `<div class="sub">Queued — <a href="#" onclick="showScreen('actions');return false" style="color:var(--cyan2)">review in Action Center ›</a></div>`;
      showToast('Queued for Action Center approval.', 'info');
      loadActions();
    } else if (d.started) {
      if (resultEl) resultEl.innerHTML = `<div class="sub">Started (PID ${escHtml(String(d.pid||''))}), running in background.</div>`;
      showToast('Started, running in background.', 'info');
    } else {
      const ok = d.success !== false;
      if (resultEl) resultEl.innerHTML = `<div class="sub" style="color:${ok?'var(--green)':'var(--red)'}">${ok?'✅ Completed':'❌ Failed'} (exit ${escHtml(String(d.returncode))})</div>` +
        (d.output ? `<pre style="margin-top:6px;max-height:220px;overflow:auto;background:var(--bg);border-radius:8px;padding:8px;font-size:12px;white-space:pre-wrap">${escHtml(d.output)}</pre>` : '');
      showToast(ok ? 'Workflow completed.' : 'Workflow failed.', ok ? 'ok' : 'err', ok ? 4500 : 6000);
    }
  } catch(e) {
    const msg = e.name==='AbortError'?'Request timed out':e.message||'Failed to run';
    if (resultEl) resultEl.innerHTML = `<div class="empty">${escHtml(msg)}</div>`;
    showToast(msg, 'err', 6000);
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

// ══════════════════════════════════════════════════════════════════════════
// Conversations — real data: /api/conversations — read-only browser + search
// for the persisted chat_messages history. Session = a long-lived per-device
// thread (one per browser localStorage), not a short discrete conversation —
// expect very few sessions, each potentially holding many messages. Two views
// inside one panel: session list (default) and a session detail/reader (drill-in).
// No writes, no approval gate — this screen is purely a reporting surface.
// ══════════════════════════════════════════════════════════════════════════
let _convSessions = [];

function _convTimeAgo(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d)) return '—';
  const mins = Math.round((Date.now() - d.getTime()) / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return mins + 'm ago';
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return hrs + 'h ago';
  const days = Math.round(hrs / 24);
  if (days < 30) return days + 'd ago';
  return d.toLocaleDateString();
}

function _convShortId(sessionId) {
  const s = sessionId || '';
  return s.length > 12 ? s.slice(0, 8) + '…' + s.slice(-4) : s;
}

async function loadConversations() {
  const el = document.getElementById('conversations-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/conversations', 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    _convSessions = d.sessions || [];
    renderConversationList();
    const badge = document.getElementById('badge-conversations');
    if (badge) {
      const total = _convSessions.reduce((sum, s) => sum + (s.message_count || 0), 0);
      badge.textContent = total > 999 ? '999+' : total;
      badge.style.display = total > 0 ? '' : 'none';
    }
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadConversations()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderConversationList() {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  if (!_convSessions.length) {
    el.innerHTML = '<div class="empty">No conversations yet — chat history will appear here once Frank has been used.</div>';
    return;
  }
  el.innerHTML = `<div class="section-title">💬 Sessions (${_convSessions.length})</div>` +
    _convSessions.map(s => `<div class="tl-item" style="cursor:pointer" onclick="openConversation('${escHtml(s.session_id)}')">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(_convShortId(s.session_id))} <span style="color:var(--muted);font-weight:400">— ${s.message_count} msg${s.message_count===1?'':'s'}</span></div>
        <div class="sub">${escHtml(s.last_role === 'user' ? 'Scott' : 'Frank')}: ${escHtml(s.last_snippet || '')} · ${_convTimeAgo(s.last_at)}</div>
      </div>
    </div>`).join('');
}

async function openConversation(sessionId) {
  const el = document.getElementById('conversations-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/conversations/' + encodeURIComponent(sessionId), 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderConversationDetail(sessionId, d);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="openConversation('${escHtml(sessionId)}')" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div><div style="text-align:center;margin-top:8px"><button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:8px 20px;font-size:13px;cursor:pointer">Back to list</button></div>`;
  }
}

function renderConversationDetail(sessionId, d) {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  const msgs = d.messages || [];
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer">‹ Back</button>
    <span style="font-size:12px;color:var(--muted)">${escHtml(_convShortId(sessionId))} · ${msgs.length} message${msgs.length===1?'':'s'}${d.truncated ? ' (showing first 500)' : ''}</span>
  </div>`;
  html += '<div style="display:flex;flex-direction:column;gap:10px">' +
    msgs.map(m => `<div class="lc-bubble ${m.role === 'user' ? 'user' : 'bot'}">${escHtml(m.content)}</div>`).join('') +
    '</div>';
  el.innerHTML = html;
}

function backToConversationList() {
  renderConversationList();
}

async function searchConversations() {
  const q = (document.getElementById('conv-search-input').value || '').trim();
  if (!q) { loadConversations(); return; }
  const el = document.getElementById('conversations-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/conversations?q=' + encodeURIComponent(q), 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderConversationSearch(q, d.results || []);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="searchConversations()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderConversationSearch(q, results) {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer">‹ Back to list</button>
    <span style="font-size:12px;color:var(--muted)">${results.length} match${results.length===1?'':'es'} for "${escHtml(q)}"</span>
  </div>`;
  html += results.length ? results.map(r => `<div class="tl-item" style="cursor:pointer" onclick="openConversation('${escHtml(r.session_id)}')">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(r.role === 'user' ? 'Scott' : 'Frank')} <span style="color:var(--muted);font-weight:400">in ${escHtml(_convShortId(r.session_id))}</span></div>
        <div class="sub">${escHtml(r.content.length > 160 ? r.content.slice(0,160)+'…' : r.content)} · ${_convTimeAgo(r.created_at)}</div>
      </div>
    </div>`).join('') : '<div class="empty">No messages match that search.</div>';
  el.innerHTML = html;
}

document.getElementById('conv-search-input').addEventListener('keydown', e => { if (e.key === 'Enter') searchConversations(); });

// ══════════════════════════════════════════════════════════════════════════
// Knowledge Base — real data: /api/kb — read-only browser + search for the
// real markdown docs in data/knowledge_base/. Docs render as raw escaped text
// in a monospace pre-wrap block (no markdown-to-HTML conversion) because these
// docs are dense with markdown tables that a partial header-only renderer would
// leave looking broken — pre-wrap monospace preserves table alignment exactly
// as authored. Three view-states inside one panel: doc list (default), doc
// reader (drill-in), search results. No writes, no approval gate.
// ══════════════════════════════════════════════════════════════════════════
let _kbDocs = [];

function _kbPre(text) {
  return `<div style="white-space:pre-wrap;font-family:ui-monospace,monospace;font-size:12.5px;line-height:1.5;color:var(--text)">${escHtml(text)}</div>`;
}

async function loadKb() {
  const el = document.getElementById('kb-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/kb', 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    _kbDocs = d.docs || [];
    renderKbList();
    const badge = document.getElementById('badge-kb');
    if (badge) {
      badge.textContent = _kbDocs.length > 999 ? '999+' : _kbDocs.length;
      badge.style.display = _kbDocs.length > 0 ? '' : 'none';
    }
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadKb()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderKbList() {
  const el = document.getElementById('kb-content');
  if (!el) return;
  if (!_kbDocs.length) {
    el.innerHTML = '<div class="empty">No knowledge base docs found in data/knowledge_base/.</div>';
    return;
  }
  el.innerHTML = `<div class="section-title">📚 Docs (${_kbDocs.length})</div>` +
    _kbDocs.map(d => `<div class="tl-item" style="cursor:pointer" onclick="openKbDoc('${escHtml(d.filename)}')">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(d.title)}</div>
        <div class="sub">${escHtml(d.filename)} · ${escHtml(d.size_human)} · ${d.word_count.toLocaleString()} words</div>
      </div>
    </div>`).join('');
}

async function openKbDoc(filename) {
  const el = document.getElementById('kb-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/kb/' + encodeURIComponent(filename), 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderKbDoc(filename, d);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="openKbDoc('${escHtml(filename)}')" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div><div style="text-align:center;margin-top:8px"><button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:8px 20px;font-size:13px;cursor:pointer">Back to list</button></div>`;
  }
}

function renderKbDoc(filename, d) {
  const el = document.getElementById('kb-content');
  if (!el) return;
  el.innerHTML = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer">‹ Back</button>
    <span style="font-size:12px;color:var(--muted)">${escHtml(d.title)} · ${escHtml(filename)}</span>
  </div>` + _kbPre(d.content);
}

function backToKbList() {
  renderKbList();
}

async function searchKb() {
  const q = (document.getElementById('kb-search-input').value || '').trim();
  if (!q) { loadKb(); return; }
  const el = document.getElementById('kb-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/kb?q=' + encodeURIComponent(q), 15000);
    if (!r.ok) { const e = await r.json().catch(()=>({})); throw new Error(e.detail||'HTTP '+r.status); }
    const d = await r.json();
    renderKbSearch(q, d.results || []);
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="searchKb()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderKbSearch(q, results) {
  const el = document.getElementById('kb-content');
  if (!el) return;
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:8px;padding:6px 14px;font-size:12px;cursor:pointer">‹ Back to list</button>
    <span style="font-size:12px;color:var(--muted)">${results.length} doc${results.length===1?'':'s'} match "${escHtml(q)}"</span>
  </div>`;
  html += results.length ? results.map(r => `<div class="tl-item" style="cursor:default">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt" style="width:100%">
        <div class="ttl" style="cursor:pointer" onclick="openKbDoc('${escHtml(r.filename)}')">${escHtml(r.title)} <span style="color:var(--muted);font-weight:400">— ${r.match_count} match${r.match_count===1?'':'es'}</span></div>
        ${r.matches.map(m => `<div class="sub" style="margin-top:6px">line ${m.line_no}</div>` + _kbPre(m.context)).join('')}
      </div>
    </div>`).join('') : '<div class="empty">No docs match that search.</div>';
  el.innerHTML = html;
}

document.getElementById('kb-search-input').addEventListener('keydown', e => { if (e.key === 'Enter') searchKb(); });

// ══════════════════════════════════════════════════════════════════════════
// Hub screens — ported from the live Hub at / (main.py): Listings, Products,
// Brand Kit, Files, Connections, Security. Same API calls, same write
// semantics (toggleListingState still confirm-gated), restyled to hub- CSS.
// ══════════════════════════════════════════════════════════════════════════

// ── Listings — real data: /api/listings, /api/shop-sections, /api/listings/{id}/files ──
let _lastListingState = 'active';
let _listings = [];
let _listingState = 'active';
let _sectionFilter = null; // null = all categories
let _sectionsMap = null;   // {shop_section_id: title}, fetched once and cached client-side
let _openDetailId = null;
async function _ensureSectionsLoaded() {
  if (_sectionsMap) return;
  try {
    const d = await (await authGet('/api/shop-sections', 15000)).json();
    _sectionsMap = {};
    (d.sections||[]).forEach(s => { _sectionsMap[s.shop_section_id] = s.title; });
  } catch(e) { _sectionsMap = {}; }
}
function _sectionLabel(id) {
  if (!id) return 'Uncategorized';
  return (_sectionsMap && _sectionsMap[id]) || ('Section '+id);
}
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('#screen-listings .hub-toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastListingState = state; _listingState = state; _sectionFilter = null; _openDetailId = null;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    await _ensureSectionsLoaded();
    const r = await authGet('/api/listings?state='+state, 20000);
    if (!r.ok) { const err = await r.json().catch(()=>({})); throw new Error(err.detail||'HTTP '+r.status); }
    const d = await r.json();
    _listings = d.listings || [];
    renderListings();
  } catch(e) {
    el.innerHTML = `<div class="hub-empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastListingState)" style="background:var(--gold);color:#06141f;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setSectionFilter(key) {
  _sectionFilter = key;
  _openDetailId = null;
  renderListings();
}
function renderListings() {
  const el = document.getElementById('listings-content');
  if (!_listings.length) { el.innerHTML = '<div class="hub-empty">No '+_listingState+' listings</div>'; return; }
  const seen = {}; const cats = [];
  _listings.forEach(l => {
    const key = String(l.shop_section_id || 'none');
    if (!seen[key]) { seen[key] = true; cats.push({key: key, label: _sectionLabel(l.shop_section_id)}); }
  });
  cats.sort((a,b) => a.label.localeCompare(b.label));
  let html = '';
  if (cats.length > 1) {
    html += '<div class="hub-chip-row">';
    html += `<button class="hub-chip-btn${_sectionFilter===null?' active':''}" onclick="setSectionFilter(null)">All (${_listings.length})</button>`;
    cats.forEach(c => {
      const n = _listings.filter(l => String(l.shop_section_id||'none')===c.key).length;
      html += `<button class="hub-chip-btn${_sectionFilter===c.key?' active':''}" onclick="setSectionFilter('${c.key}')">${escHtml(c.label)} (${n})</button>`;
    });
    html += '</div>';
  }
  const filtered = _sectionFilter===null ? _listings : _listings.filter(l => String(l.shop_section_id||'none')===_sectionFilter);
  if (!filtered.length) { html += '<div class="hub-empty">No listings in this category</div>'; el.innerHTML = html; return; }
  html += filtered.map(l => `
    <div class="hub-listing-item" style="cursor:pointer" onclick="toggleListingDetail(${l.listing_id})">
      ${l.thumbnail_url ? `<img class="hub-thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy">` : `<div class="hub-thumb-ph">🏷️</div>`}
      <div class="hub-listing-info">
        <div class="hub-listing-title">${escHtml(l.title)}</div>
        <div class="hub-listing-meta">${l.views} views · ${l.num_favorers} ♥${l.sales!=null?' · '+l.sales+' sold':''}<span id="hub-state-${l.listing_id}" class="hub-lstate ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
      </div>
      <div class="hub-listing-price">$${(+l.price||0).toFixed(2)}</div>
    </div>
    <div id="hub-detail-${l.listing_id}" class="hub-listing-detail" style="display:none"></div>`).join('');
  el.innerHTML = html;
}
async function toggleListingDetail(listingId) {
  const panel = document.getElementById('hub-detail-'+listingId);
  if (!panel) return;
  if (_openDetailId !== null && _openDetailId !== listingId) {
    const prev = document.getElementById('hub-detail-'+_openDetailId);
    if (prev) prev.style.display = 'none';
  }
  if (_openDetailId === listingId) { panel.style.display = 'none'; _openDetailId = null; return; }
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  panel.style.display = 'block';
  _openDetailId = listingId;
  panel.innerHTML =
    `<div class="hub-drow"><span>Listing ID</span><b>${listingId}</b></div>`+
    `<div class="hub-drow"><span>Category</span><b>${escHtml(_sectionLabel(l.shop_section_id))}</b></div>`+
    `<div class="hub-drow"><span>Views</span><b>${l.views}</b></div>`+
    `<div class="hub-drow"><span>Favorites</span><b>${l.num_favorers}</b></div>`+
    (l.sales!=null ? `<div class="hub-drow"><span>Sold</span><b>${l.sales}</b></div>` : '')+
    (l.conversion_pct!=null ? `<div class="hub-drow"><span>Conversion</span><b>${l.conversion_pct}%</b></div>` : '')+
    `<div class="hub-drow"><span>Price</span><b>$${(+l.price||0).toFixed(2)}</b></div>`+
    `<div id="hub-files-${listingId}"><div class="hub-drow"><span>Digital files</span><b>loading…</b></div></div>`+
    `<div style="margin-top:8px;display:flex;justify-content:flex-end;align-items:center;gap:10px">`+
    ((l.state==='active'||l.state==='inactive') ? `<button id="hub-state-btn-${listingId}" class="hub-act-btn" style="font-size:12px;padding:6px 12px" onclick="event.stopPropagation();toggleListingState(${listingId},this)">${l.state==='active'?'⏸️ Deactivate':'▶️ Activate'}</button>` : '')+
    `<a href="${escHtml(l.url)}" target="_blank" style="color:var(--gold);font-size:12px;text-decoration:none" onclick="event.stopPropagation()">Open on Etsy ↗</a>`+
    `</div>`;
  try {
    const r = await authGet('/api/listings/'+listingId+'/files', 15000);
    const slot = document.getElementById('hub-files-'+listingId);
    if (!slot) return;
    if (!r.ok) { slot.innerHTML = '<div class="hub-drow"><span>Digital files</span><b>unavailable</b></div>'; return; }
    const d = await r.json();
    const files = d.files || [];
    if (!files.length) { slot.innerHTML = '<div class="hub-drow"><span>Digital files</span><b>none attached</b></div>'; return; }
    slot.innerHTML = files.map(f => `<div class="hub-drow"><span>📄 ${escHtml(f.filename||'file')}</span><b>${escHtml(f.size_human||'')}</b></div>`).join('');
  } catch(e) {
    const slot = document.getElementById('hub-files-'+listingId);
    if (slot) slot.innerHTML = '<div class="hub-drow"><span>Digital files</span><b>failed to load</b></div>';
  }
}
async function toggleListingState(listingId, btn) {
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  const newState = l.state === 'active' ? 'inactive' : 'active';
  if (!confirm((newState==='inactive'?'Deactivate':'Activate')+' this listing on Etsy now?')) return;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Working…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/state?new_state='+newState, {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    l.state = d.state || newState;
    btn.textContent = l.state==='active' ? '⏸️ Deactivate' : '▶️ Activate';
    btn.disabled = false;
    const badge = document.getElementById('hub-state-'+listingId);
    if (badge) { badge.textContent = l.state; badge.className = 'hub-lstate ' + (l.state==='active'?'active':'draft'); }
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    showToast('Could not change listing state: ' + (e.message||e), 'err', 6000);
  }
}

// ── Products / Brand Kit — fully static, from CLAUDE.md product catalog ──
const _THEMES = [
  {id:'DP1026',name:'Lavender Dreams',primary:'#8666AA',accent:'#C4A8D4',neutral:'#FAF7FF',text:'#2C1A3A'},
  {id:'DP1027',name:'Cotton Candy',   primary:'#DE97C6',accent:'#97C6DE',neutral:'#FFF6FC',text:'#2C1A2A'},
  {id:'DP1028',name:'Midnight Blue',  primary:'#1B2568',accent:'#7BA7C2',neutral:'#F0F5FF',text:'#0D1525'},
  {id:'DP1029',name:'Coral Peach',    primary:'#FD6C49',accent:'#F5B878',neutral:'#FFF8F4',text:'#3A1A0D'}
];
const _PRODUCTS_STATIC = [
  {id:'DP1026',name:'Ultimate Life Planner',      price:'$14.99',pages:104},
  {id:'DP1027',name:'Student & School Planner',   price:'$9.99', pages:90},
  {id:'DP1028',name:'Budget & Finance Planner',   price:'$12.99',pages:102},
  {id:'DP1029',name:'Fitness & Wellness Planner', price:'$12.99',pages:91}
];
function renderProducts() {
  const el = document.getElementById('products-content');
  if (!el) return;
  let html = '<div class="hub-section-title">Core Products</div>';
  _PRODUCTS_STATIC.forEach((p,i) => {
    const t = _THEMES[i]||{};
    html += '<div class="hub-prod-card" style="border-left-color:'+(t.primary||'var(--gold)')+'">'+
      '<div style="display:flex;justify-content:space-between;align-items:flex-start">'+
        '<div><div style="font-size:11px;font-weight:700;color:var(--muted);letter-spacing:.4px">'+escHtml(p.id)+'</div>'+
        '<div style="font-size:14px;font-weight:600;margin-top:3px">'+escHtml(p.name)+'</div></div>'+
        '<div style="font-size:16px;font-weight:700;color:var(--gold)">'+escHtml(p.price)+'</div>'+
      '</div>'+
      '<div style="display:flex;gap:12px;margin-top:8px;font-size:11px;color:var(--muted)">'+
        '<span>📄 '+p.pages+' pages</span><span>🔖 13 tags</span><span>Digital Download</span>'+
      '</div>'+
    '</div>';
  });
  el.innerHTML = html;
}
function renderBrandKit() {
  const el = document.getElementById('brandkit-content');
  if (!el) return;
  let html = '<div class="hub-section-title">Product Color Palettes</div>';
  _THEMES.forEach(t => {
    html += '<div class="hub-card" style="margin-bottom:10px">';
    html += '<div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">'+escHtml(t.id)+' — '+escHtml(t.name)+'</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    [{label:'Primary',hex:t.primary},{label:'Accent',hex:t.accent},{label:'Neutral',hex:t.neutral},{label:'Text',hex:t.text}].forEach(c => {
      html += '<div style="display:flex;align-items:center;gap:5px">'+
        '<span class="hub-swatch" style="background:'+escHtml(c.hex)+'"></span>'+
        '<div style="font-size:11px"><div style="color:var(--muted)">'+escHtml(c.label)+'</div>'+
        '<div style="font-family:monospace;font-size:10px;color:var(--text)">'+escHtml(c.hex)+'</div></div>'+
        '</div>';
    });
    html += '</div></div>';
  });
  html += '<div class="hub-section-title">Listing Standards</div><div class="hub-card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['Title','≤70 chars · keyword first 40 · commas not pipes'],
   ['Tags','13 tags · each ≤20 chars · multi-word buyer phrases'],
   ['Photos','10 slots · 2400×2400px · lifestyle hero first'],
   ['Price','.99 / .97 / .49 endings — never round numbers'],
   ['AI disclosure','Required in description · who_made: i_did'],
   ['File limit','20 MB per file (PDF + ZIP · Etsy hard limit)']
  ].forEach(r => {
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:10px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted);line-height:1.4">'+escHtml(r[1])+'</td></tr>';
  });
  html += '</table></div>';
  html += '<div class="hub-section-title">Pricing Tiers</div><div class="hub-card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['DP1026 Life Planner','$14.99','104 pages + sticker pack'],
   ['DP1027 Student','$9.99','90 pages · student budget'],
   ['DP1028 Budget','$12.99','102 pages · finance niche'],
   ['DP1029 Fitness','$12.99','91 pages · wellness niche'],
   ['SVG 5-pack','$9.99','5 designs · instant DL'],
   ['SVG 10+ pack','$14.99','10+ designs · instant DL']
  ].forEach(r => {
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:8px;font-weight:600">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;padding-right:8px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[1])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted)">'+escHtml(r[2])+'</td></tr>';
  });
  html += '</table></div>';
  el.innerHTML = html;
}

// ── Files — real data: /api/files (data/digital_products/ + backups) ──
function _hubFileUrl(f, inline){
  return BASE+'/api/files/download?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&token='+encodeURIComponent(TOKEN)+(inline?'&inline=1':'');
}
function _hubZipEntryUrl(f, entryName){
  return BASE+'/api/files/zip-entry?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&entry='+encodeURIComponent(entryName)+'&token='+encodeURIComponent(TOKEN);
}
function _hubFileIcon(name){
  const n=(name||'').toLowerCase();
  if(n.match(/\.(png|jpe?g|gif|webp|svg)$/)) return '🖼️';
  if(n.endsWith('.pdf')) return '📕';
  if(n.endsWith('.zip')) return '🗂️';
  if(n.match(/\.(txt|md)$/)) return '📃';
  return '📄';
}
function toggleZip(id, btn){
  const el=document.getElementById(id);
  if(!el) return;
  const open=el.style.display==='none';
  el.style.display=open?'':'none';
  if(btn) btn.textContent=open?'▾':'▸';
}
function openFile(url){ window.open(url,'_blank'); }
async function loadFiles() {
  const el = document.getElementById('files-content');
  if (!el) return;
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/files', 20000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const groups = d.groups||[];
    if (!groups.length || groups.every(g=>!g.files.length)) {
      el.innerHTML = '<div class="hub-empty" style="line-height:1.6">'+
        escHtml(d.empty_reason||'No files yet.')+'</div>';
      return;
    }
    let html = '<div class="hub-card" style="margin-bottom:12px">'+
      '<div style="font-size:12px;color:var(--muted);line-height:1.6">The actual product files living on the server '+
      '(data/digital_products/ and data/backups/). Tap a file to open it. Tap a ZIP to expand it and open any '+
      'file inside directly — no unzipping needed.</div></div>';
    let zipIdx=0;
    groups.forEach(g => {
      if (!g.files.length) return;
      html += '<div class="hub-section-title">'+escHtml(g.label)+' ('+g.files.length+')</div><div class="hub-card">';
      g.files.forEach(f => {
        const when = new Date(f.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        if (f.is_zip) {
          const zid='hub-zip-'+(zipIdx++);
          const entries=f.entries||[];
          html += '<div class="hub-listing-item" onclick="toggleZip(\\''+zid+'\\',this.querySelector(\\'.hub-zip-caret\\'))" style="cursor:pointer">'+
            '<div class="hub-thumb-ph">🗂️</div>'+
            '<div class="hub-listing-info"><div class="hub-listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="hub-listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+' · '+entries.length+' files inside</div></div>'+
            '<div class="hub-zip-caret" style="color:var(--gold);font-size:16px">▸</div>'+
          '</div>';
          html += '<div id="'+zid+'" style="display:none;margin:0 0 6px 14px;border-left:2px solid var(--border);padding-left:8px">';
          if(!entries.length){
            html += '<div class="hub-listing-meta" style="padding:8px 0">Could not read this ZIP\\'s contents.</div>';
          }
          entries.forEach(en => {
            const eurl=_hubZipEntryUrl(f,en.name);
            html += '<div class="hub-listing-item" onclick="openFile(\\''+eurl+'\\')" style="cursor:pointer;padding:7px 4px">'+
              '<div class="hub-thumb-ph" style="font-size:16px">'+_hubFileIcon(en.name)+'</div>'+
              '<div class="hub-listing-info"><div class="hub-listing-title" style="font-size:13px">'+escHtml(en.name)+'</div>'+
              '<div class="hub-listing-meta">'+escHtml(en.size_human)+(en.inline?' · tap to open':' · tap to download')+'</div></div>'+
              '<div style="color:var(--gold);font-size:15px">'+(en.inline?'↗':'⬇')+'</div>'+
            '</div>';
          });
          html += '</div>';
        } else {
          const url=_hubFileUrl(f, f.inline?1:0);
          html += '<div class="hub-listing-item" onclick="openFile(\\''+url+'\\')" style="cursor:pointer">'+
            '<div class="hub-thumb-ph">'+_hubFileIcon(f.path)+'</div>'+
            '<div class="hub-listing-info"><div class="hub-listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="hub-listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+(f.inline?' · tap to open':' · tap to download')+'</div></div>'+
            '<div style="color:var(--gold);font-size:18px">'+(f.inline?'↗':'⬇')+'</div>'+
          '</div>';
        }
      });
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="hub-empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load files')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadFiles()" style="background:var(--gold);color:#06141f;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── Studio — real data: /api/studio/* (image-to-video generation, attach-to-Etsy
// staging, Instagram/Facebook posting). Posting always fires only on a direct button
// click — there is no automatic or scheduled trigger anywhere in this code. ──
let _studioSelectedVideo = '';
let _studioUploadedPaths = [];

function _studioVideoUrl(name, inline){
  return BASE+'/api/files/download?root=videos&path='+encodeURIComponent(name)+
    '&token='+encodeURIComponent(TOKEN)+(inline?'&inline=1':'');
}

function studioPreviewVideo(name){
  _studioSelectedVideo = name;
  const player = document.getElementById('studio-player');
  if (player) { player.src = _studioVideoUrl(name, 1); player.load(); }
  const cap = document.getElementById('studio-player-caption');
  if (cap) cap.textContent = name;
  const title = document.getElementById('studio-actions-title');
  const card = document.getElementById('studio-actions-card');
  const fn = document.getElementById('studio-actions-filename');
  if (title) title.style.display = '';
  if (card) card.style.display = '';
  if (fn) fn.textContent = name;
  ['studio-stage-status','studio-ig-status','studio-fb-status'].forEach(function(id){
    const el = document.getElementById(id);
    if (el) el.textContent = '';
  });
  document.querySelectorAll('#studio-videos-list .studio-list-item').forEach(function(row){
    row.style.borderColor = (row.getAttribute('data-path')===name) ? 'var(--gold)' : '';
  });
}

document.addEventListener('click', function(e){
  const row = e.target.closest && e.target.closest('#studio-videos-list .studio-list-item');
  if (row) studioPreviewVideo(row.getAttribute('data-path'));
});

async function loadStudioVideos() {
  const el = document.getElementById('studio-videos-list');
  if (!el) return;
  try {
    const r = await authGet('/api/studio/videos', 15000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const videos = d.videos||[];
    if (!videos.length) {
      el.innerHTML = '<div class="hub-empty">No videos generated yet.</div>';
      return;
    }
    el.innerHTML = videos.map(v => {
      const when = new Date(v.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
      const selected = v.path === _studioSelectedVideo;
      return '<div class="studio-list-item" data-path="'+escHtml(v.path)+'" '+
        'style="cursor:pointer'+(selected?';border-color:var(--gold)':'')+'">'+
        '<div style="font-weight:600">'+escHtml(v.path)+'</div>'+
        '<div style="color:var(--muted);margin-top:3px">'+escHtml(v.size_human)+' · '+escHtml(when)+'</div></div>';
    }).join('');
  } catch(e) {
    el.innerHTML = '<div class="hub-empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load videos')+'</div>';
  }
}

document.addEventListener('change', function(e){
  if (e.target && e.target.id === 'studio-file-input') studioUploadImages(e.target.files);
});

async function studioUploadImages(fileList) {
  const status = document.getElementById('studio-upload-status');
  const files = Array.from(fileList||[]);
  if (!files.length) return;
  _studioUploadedPaths = [];
  for (let i=0; i<files.length; i++) {
    const f = files[i];
    if (status) status.textContent = 'Uploading '+(i+1)+'/'+files.length+'…';
    try {
      const r = await fetchWithTimeout(
        BASE+'/api/studio/upload-image?filename='+encodeURIComponent(f.name),
        {method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body:f},
        30000
      );
      const d = await r.json().catch(()=>({}));
      if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
      _studioUploadedPaths.push(d.path);
    } catch(e) {
      if (status) status.textContent = 'Upload failed on "'+f.name+'": '+(e.message||e);
      return;
    }
  }
  if (status) status.textContent = _studioUploadedPaths.length+' image(s) ready to generate.';
}

async function studioGenerate() {
  const btn = document.getElementById('studio-generate-btn');
  const status = document.getElementById('studio-generate-status');
  const listingId = (document.getElementById('studio-listing-id').value||'').trim();
  const style = document.getElementById('studio-style').value;
  const title = document.getElementById('studio-title').value||'';
  const price = document.getElementById('studio-price').value||'';
  const digital = document.getElementById('studio-digital').checked;

  if (!listingId && !_studioUploadedPaths.length) {
    if (status) status.textContent = 'Upload images or enter a listing ID first.';
    return;
  }
  const body = {style:style, title:title, price:price, digital:digital};
  if (listingId) body.listing_id = parseInt(listingId, 10);
  else body.image_paths = _studioUploadedPaths;

  btn.disabled = true;
  btn.textContent = '⏳ Generating…';
  if (status) status.innerHTML = '<div class="hub-spinner" style="margin:10px auto"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/studio/generate', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'}, body:JSON.stringify(body)
    }, 185000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (status) status.textContent = 'Generated '+d.path+' ('+d.size_human+').';
    _studioUploadedPaths = [];
    const fi = document.getElementById('studio-file-input');
    if (fi) fi.value = '';
    const us = document.getElementById('studio-upload-status');
    if (us) us.textContent = '';
    await loadStudioVideos();
    studioPreviewVideo(d.path);
  } catch(e) {
    if (status) status.textContent = e.name==='AbortError' ? 'Generation timed out.' : (e.message||'Generation failed');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Video';
  }
}

async function studioStageToEtsy() {
  if (!_studioSelectedVideo) return;
  const btn = document.getElementById('studio-stage-btn');
  const status = document.getElementById('studio-stage-status');
  const listingId = (document.getElementById('studio-attach-listing-id').value||'').trim();
  const rank = (document.getElementById('studio-attach-rank').value||'').trim();
  if (!listingId) { if (status) status.textContent = 'Enter a listing ID first.'; return; }

  btn.disabled = true;
  btn.textContent = '⏳ Staging…';
  if (status) status.textContent = '';
  try {
    const videoResp = await fetchWithTimeout(_studioVideoUrl(_studioSelectedVideo, 0), {}, 30000);
    if (!videoResp.ok) throw new Error('Could not read video file (HTTP '+videoResp.status+')');
    const blob = await videoResp.blob();
    let url = BASE+'/api/queue/stage-video?listing_id='+encodeURIComponent(listingId)+
      '&summary='+encodeURIComponent('Studio video for listing '+listingId);
    if (rank) url += '&rank='+encodeURIComponent(rank);
    const r = await fetchWithTimeout(url, {method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body:blob}, 60000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (status) status.innerHTML = `Staged — <a href="#" onclick="showScreen('actions');return false" style="color:var(--cyan2)">review in Action Center ›</a>`;
  } catch(e) {
    if (status) status.textContent = e.message||'Staging failed';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Stage for Approval';
  }
}

async function studioPostInstagram() {
  if (!_studioSelectedVideo) return;
  const btn = document.getElementById('studio-ig-btn');
  const status = document.getElementById('studio-ig-status');
  const caption = document.getElementById('studio-ig-caption').value||'';
  if (!confirm('Post this video to Instagram now? This cannot be undone.')) return;
  btn.disabled = true;
  btn.textContent = '⏳ Posting…';
  if (status) status.textContent = '';
  try {
    const r = await fetchWithTimeout(BASE+'/api/studio/post-instagram', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},
      body: JSON.stringify({video:_studioSelectedVideo, caption:caption, is_reel:true})
    }, 120000);
    const d = await r.json().catch(()=>({}));
    if (d.error) { if (status) status.textContent = d.error+': '+(d.detail||''); return; }
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (status) status.textContent = 'Posted to Instagram.';
  } catch(e) {
    if (status) status.textContent = e.message||'Instagram post failed';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Post to Instagram (Reel)';
  }
}

async function studioPostFacebook() {
  if (!_studioSelectedVideo) return;
  const btn = document.getElementById('studio-fb-btn');
  const status = document.getElementById('studio-fb-status');
  const caption = document.getElementById('studio-fb-caption').value||'';
  if (!confirm('Post this video to Facebook now? This cannot be undone.')) return;
  btn.disabled = true;
  btn.textContent = '⏳ Posting…';
  if (status) status.textContent = '';
  try {
    const r = await fetchWithTimeout(BASE+'/api/studio/post-facebook', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},
      body: JSON.stringify({video:_studioSelectedVideo, caption:caption})
    }, 120000);
    const d = await r.json().catch(()=>({}));
    if (d.error) { if (status) status.textContent = d.error+': '+(d.detail||''); return; }
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (status) status.textContent = 'Posted to Facebook.';
  } catch(e) {
    if (status) status.textContent = e.message||'Facebook post failed';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Post to Facebook';
  }
}

// ── Connections — real data: /api/credentials/status + static Platform Roadmap ──
const _PLATFORM_ROADMAP = [
  {name:'Etsy',      icon:'🛍️', status:'live',    note:'onbrandcraftz · authorized'},
  {name:'Pinterest', icon:'📌', status:'roadmap',note:'API v5 — ready to integrate', steps:[
    'Create a Pinterest Developer app at developers.pinterest.com',
    'Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env',
    'Run: python tools/pinterest_oauth.py — authorizes and saves tokens to .env automatically',
    'Claim the Etsy shop under Pinterest "Claimed accounts" to enable Rich Pins',
    'Done — the Social Media Agent can post via tools/pinterest_api.py'
  ]},
  {name:'Instagram', icon:'📷', status:'roadmap',note:'Meta Graph API (app review needed)', steps:[
    'Create a Meta Business app at developers.facebook.com',
    'Add the "Instagram Graph API" product to the app',
    'Connect the Instagram Professional account via a Facebook Page',
    'Add INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET to .env',
    'Generate a long-lived access token (scopes: instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement)',
    'Add INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN to .env',
    'Submit the app for Meta App Review before posting publicly — tools/instagram_api.py is already built and waiting on this'
  ]},
  {name:'Facebook',  icon:'📘', status:'roadmap',note:'Same Meta app as Instagram', steps:[
    'No separate app needed — reuse the Meta app created for Instagram',
    'Add the Facebook Page and Pages API permission to that same app',
    'Generate a Page Access Token with the pages_manage_posts scope',
    'Add FACEBOOK_PAGE_ID / FACEBOOK_ACCESS_TOKEN to .env once issued'
  ]},
  {name:'TikTok',    icon:'🎵', status:'roadmap',note:'TikTok for Business API', steps:[
    'App credentials are already configured (TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET)',
    'Run: python tools/tiktok_oauth.py — log in as @onbrandcraftz and approve',
    'Tokens save to .env automatically (access token 24h, refresh token 365 days)',
    'Re-run tools/tiktok_oauth.py whenever the access token expires',
    'Done — post via tools/tiktok_poster.py'
  ]},
  {name:'OneDrive',  icon:'☁️', status:'roadmap',note:'Microsoft Graph — source file storage', steps:[
    'Not yet built — no OneDrive code exists in the repo today',
    'Register an app in the Azure Portal (Microsoft Entra ID → App registrations)',
    'Grant the Microsoft Graph "Files.ReadWrite" delegated permission',
    'Add ONEDRIVE_CLIENT_ID / ONEDRIVE_CLIENT_SECRET to .env',
    'Build tools/onedrive_oauth.py to get access/refresh tokens (does not exist yet)',
    'Use the Graph API /me/drive/root:/path:/content endpoint to sync source files for backup'
  ]}
];
function toggleCredSteps(key) {
  const panel = document.getElementById('hub-cred-steps-'+key);
  if (!panel) return;
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}
async function loadConnections() {
  const el = document.getElementById('connections-content');
  if (!el) return;
  el.innerHTML = '<div class="hub-spinner"></div>';
  try {
    const r = await authGet('/api/credentials/status', 15000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    let html = '<div class="hub-card" style="margin-bottom:12px">';
    if (d.etsy_live) {
      html += '<div style="color:var(--green);font-size:15px;font-weight:700">✅ Etsy Live</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.shop_name||'onbrandcraftz')+' · token valid</div>';
    } else {
      html += '<div style="color:var(--red);font-size:15px;font-weight:700">⚠️ Etsy Ping Failed</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.etsy_live_error||'Unknown error')+' — run python tools/etsy_oauth.py</div>';
    }
    html += '</div><div class="hub-section-title">API Credentials</div><div class="hub-card">';
    const et=d.etsy||{}, an=d.anthropic||{}, oa=d.openai||{}, sm=d.smtp||{}, pi=d.pinterest||{};
    [
      {label:'Etsy API Key',         ok:et.api_key,         note:'ETSY_API_KEY / ETSY_CLIENT_ID'},
      {label:'Etsy Access Token',    ok:et.access_token,    note:'Expires every 1 hour — auto-refreshed'},
      {label:'Etsy Refresh Token',   ok:et.refresh_token,   note:'90-day window — re-auth via etsy_oauth.py'},
      {label:'Anthropic (Claude)',   ok:an.api_key,         note:'Fucking Frank (CEO) · Conversion Doctor · tag gen'},
      {label:'OpenAI (DALL-E)',      ok:oa.api_key,         note:'gpt-image-1 listing photo generation'},
      {label:'SMTP Email',           ok:sm.user,            note:'Post-purchase digital delivery'},
      {label:'Pinterest',            ok:pi.api_key,         note:'API v5 · roadmap'}
    ].forEach(c => {
      const col = c.ok ? 'var(--green)' : 'var(--red)';
      html += '<div class="hub-cred-row">'+
        '<div class="hub-cred-dot" style="background:'+col+'"></div>'+
        '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(c.label)+'</div>'+
        '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
        '<div style="font-size:12px;font-weight:700;color:'+col+'">'+escHtml(c.ok?'Set ✓':'Not set')+'</div>'+
      '</div>';
    });
    html += '</div><div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">All tokens stored in .env — never committed to git</div>';
    html += '<div class="hub-section-title">Platform Connections</div><div class="hub-card">';
    _PLATFORM_ROADMAP.forEach(p => {
      const live = p.status==='live';
      const key = p.name.toLowerCase();
      html += '<div class="hub-cred-row">'+
        '<div style="display:flex;align-items:center;gap:10px;width:100%">'+
        '<div style="font-size:20px;flex-shrink:0;width:28px">'+p.icon+'</div>'+
        '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(p.name)+'</div>'+
        '<div style="font-size:11px;color:var(--muted)">'+escHtml(p.note)+'</div></div>'+
        (live
          ? '<div style="font-size:11px;font-weight:700;color:var(--green)">✅ Live</div>'
          : '<div style="font-size:11px;font-weight:700;color:var(--muted);cursor:pointer;white-space:nowrap" onclick="toggleCredSteps(\\''+key+'\\')">🗺️ Roadmap ›</div>')+
        '</div>'+
        (live ? '' :
          '<div id="hub-cred-steps-'+key+'" style="display:none;width:100%;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">'+
            '<div style="font-size:11px;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.4px">Steps to complete</div>'+
            '<ol style="margin:0;padding-left:18px;font-size:12px;line-height:1.6">'+
              (p.steps||[]).map(s=>'<li style="margin-bottom:4px">'+escHtml(s)+'</li>').join('')+
            '</ol>'+
          '</div>')+
        '</div>';
    });
    html += '</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="hub-empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadConnections()" style="background:var(--gold);color:#06141f;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── Security — fully static: security posture checklist ──
function renderSecurityPosture() {
  const el = document.getElementById('security-content');
  if (!el) return;
  let html = '<div class="hub-section-title">Security Posture</div><div class="hub-card">';
  [
    {ok:true, label:'.env not committed to git',           note:'Credentials stay local, never in version control'},
    {ok:true, label:'APP_SECRET_TOKEN set',                note:'Every dashboard request requires Bearer auth'},
    {ok:true, label:'Quality gate is code',                note:'Title ≤70 · tags ≤13 · validated at stage AND approve'},
    {ok:true, label:'Staged action queue',                 note:'Every Etsy change requires Scott one-tap approval'},
    {ok:null, label:'Etsy MFA enabled?',                   note:'Verify in Etsy → Account Settings → Security'},
    {ok:null, label:'Outlook 2FA active?',                 note:'Verify at account.microsoft.com → Security'},
    {ok:null, label:'Pinterest not integrated yet',        note:'No API exposure until keys are added'},
    {ok:false,label:'No per-IP rate limiting',             note:'Add nginx or Cloudflare for production hardening'},
    {ok:false,label:'Token rotation reminder needed',      note:'Etsy refresh tokens expire 90 days — set a calendar alert'}
  ].forEach(c => {
    const icon = c.ok===true?'✅':c.ok===false?'⚠️':'❓';
    const col  = c.ok===true?'var(--green)':c.ok===false?'var(--red)':'var(--muted)';
    html += '<div class="hub-posture-row">'+
      '<div style="font-size:16px;flex-shrink:0;width:24px">'+icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:'+col+'">'+escHtml(c.label)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
    '</div>';
  });
  html += '</div>';
  html += '<div class="hub-card" style="background:var(--panel);margin-top:4px">'+
    '<div style="font-size:12px;color:var(--muted);line-height:1.7">'+
    '<b style="color:var(--gold)">Re-authorize Etsy:</b> If any API call returns 401, run<br>'+
    '<code style="font-size:11px;background:var(--bg);padding:2px 8px;border-radius:4px;display:inline-block;margin-top:4px">python tools/etsy_oauth.py</code>'+
    '</div></div>';
  el.innerHTML = html;
}

function loadAll(){
  loadAgents();
  loadCredentialsAndHealth();
  loadShopPerf();
  loadQueue();
  loadMissionTimeline();
  loadTasks();
  loadTools();
  loadListings(_lastListingState);
  renderProducts();
  renderBrandKit();
  loadFiles();
  loadConnections();
  renderSecurityPosture();
  loadRelayStatus();
  loadStudioVideos();
}
loadAll();
loadActions();
loadCalendar();
loadMemory();
loadConversations();
loadKb();
loadWorkflows();
setInterval(loadAll, 30000);

// ── Clock ──
function tick(){
  const d = new Date();
  document.getElementById('clk').textContent = d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  document.getElementById('dt').textContent = d.toLocaleDateString([], {weekday:'long',month:'long',day:'numeric',year:'numeric'});
}
tick(); setInterval(tick, 1000);


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
const talkSub = document.getElementById('talk-sub');

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

function setSpeaking(on, viaFallback){
  speaking = on;
  if(orbState) orbState.textContent = on
    ? (viaFallback ? 'SPEAKING — free voice (OpenAI quota down)' : 'SPEAKING — reacting to live TTS amplitude')
    : 'IDLE — slow ambient rotation';
  if(talkSub) talkSub.textContent = on
    ? (viaFallback ? 'Frank is speaking… (free voice)' : 'Frank is speaking…')
    : 'tap to speak';
}
canvas.addEventListener('click', toggleVoiceCapture);
const talkPillEl = document.getElementById('talk-pill');
if(talkPillEl) talkPillEl.addEventListener('click', toggleVoiceCapture);

// ── Memory Insights constellation — real per-session message-count sparkline,
// fed by loadMemory() via updateMemoryWidget(). Canvas stays blank until real
// data arrives — no fake/random chart is ever drawn. ──
const mc = document.getElementById('mem-canvas');
const mctx = mc.getContext('2d');
function drawMem(points){
  mctx.clearRect(0,0,220,90);
  if (!points || !points.length) return;
  const max = Math.max(...points, 1);
  const pts = points.map((v,i) => ({
    x: points.length > 1 ? i*(220/(points.length-1)) : 110,
    y: 80 - (v/max)*70,
  }));
  mctx.strokeStyle = 'rgba(58,214,255,0.35)'; mctx.lineWidth = 1;
  mctx.beginPath();
  pts.forEach((p,i)=>{ if(i===0) mctx.moveTo(p.x,p.y); else mctx.lineTo(p.x,p.y); });
  mctx.stroke();
  pts.forEach(p=>{ mctx.fillStyle='rgba(122,232,255,0.8)'; mctx.beginPath(); mctx.arc(p.x,p.y,2,0,Math.PI*2); mctx.fill(); });
}
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
