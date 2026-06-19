"""
FRANK Command Center — static clickable HTML/CSS/JS mockup (Build Order step 0.5).

No backend wiring. This is purely a visual sign-off artifact so Scott can react to the
look of the full landscape HUD (left nav + every panel from the reference screenshots,
rebranded FRANK) before any real engineering goes in underneath it. Served at /frank,
completely separate from the live production dashboard at / so there is zero risk to
the running Hub while this is reviewed.

Real wiring (live data, approval gate, relay, voice) is Step 1+ in the approved plan —
every nav tab/panel here is a placeholder shell with the real future data source noted
in a code comment, not invented numbers presented as fact.
"""

_FRANK_HUD_MOCKUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=1440, initial-scale=1">
<title>FRANK — Command Center (mockup)</title>
<style>
:root{
  --bg:#0a1420;--bg2:#0D1B2A;--panel:#0f1f30;--panel2:#122538;--border:#1c3349;
  --cyan:#3ad6ff;--cyan2:#7fe8ff;--gold:#C9A84C;--text:#e8edf2;--muted:#5d7891;
  --green:#4caf82;--red:#e05555;--amber:#e0a83a;
}
*{box-sizing:border-box;margin:0;padding:0}
body{
  background:radial-gradient(ellipse at 50% 0%, #0e2238 0%, var(--bg) 60%);
  color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  font-size:13px;overflow:hidden;height:100vh;width:100vw;
}
.app{display:grid;grid-template-columns:220px 1fr;grid-template-rows:56px 1fr 46px;height:100vh}
.topbar{grid-column:1/3;display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;border-bottom:1px solid var(--border);background:rgba(10,20,32,.6)}
.topbar .left{display:flex;align-items:center;gap:14px}
.brand{font-weight:800;letter-spacing:2px;color:var(--cyan2);font-size:16px;
  text-shadow:0 0 12px rgba(58,214,255,.6)}
.status-pill{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--green);
  border:1px solid rgba(76,175,130,.4);border-radius:20px;padding:4px 10px;background:rgba(76,175,130,.08)}
.status-pill .dot{width:6px;height:6px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);animation:pulse 2s infinite}
.topbar .center{flex:1;display:flex;justify-content:center}
.search{width:340px;background:var(--panel);border:1px solid var(--border);border-radius:8px;
  padding:7px 12px;color:var(--text);font-size:12px}
.topbar .right{display:flex;align-items:center;gap:16px}
.clock{text-align:right;font-size:11px;color:var(--muted)}
.clock .time{font-size:14px;color:var(--text);font-weight:600}
.icon-btn{width:32px;height:32px;border-radius:8px;border:1px solid var(--border);
  background:var(--panel);display:flex;align-items:center;justify-content:center;
  cursor:pointer;position:relative;color:var(--muted)}
.icon-btn:hover{border-color:var(--cyan);color:var(--cyan2)}
.badge{position:absolute;top:-5px;right:-5px;background:var(--cyan);color:#0a1420;
  font-size:9px;font-weight:700;border-radius:8px;min-width:16px;height:16px;
  display:flex;align-items:center;justify-content:center;padding:0 3px}
.operator{display:flex;align-items:center;gap:8px;border:1px solid var(--border);border-radius:20px;
  padding:4px 10px 4px 4px;background:var(--panel)}
.operator .av{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#8a6d2b);
  display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#0a1420}

/* ── Sidebar ── */
.sidebar{border-right:1px solid var(--border);background:rgba(10,20,32,.5);
  display:flex;flex-direction:column;padding:14px 10px;overflow-y:auto}
.nav-section{font-size:10px;letter-spacing:1.5px;color:var(--muted);margin:14px 10px 6px;text-transform:uppercase}
.nav-item{display:flex;align-items:center;gap:10px;padding:9px 12px;border-radius:8px;
  cursor:pointer;color:var(--muted);font-size:13px;margin-bottom:2px;position:relative}
.nav-item .ic{width:16px;text-align:center;font-size:14px}
.nav-item:hover{background:var(--panel);color:var(--text)}
.nav-item.active{background:linear-gradient(90deg,rgba(58,214,255,.16),transparent);
  color:var(--cyan2);border-left:2px solid var(--cyan)}
.nav-item .nbadge{margin-left:auto;background:var(--panel2);color:var(--cyan2);
  font-size:10px;font-weight:700;border-radius:9px;padding:1px 7px;border:1px solid var(--border)}
.voice-widget{margin-top:auto;border:1px solid var(--border);border-radius:12px;padding:12px;
  background:var(--panel);text-align:center}
.voice-widget .vw-title{font-size:10px;letter-spacing:1px;color:var(--muted);margin-bottom:8px}
.wave-row{display:flex;align-items:center;justify-content:center;gap:3px;height:28px;margin-bottom:8px}
.wave-row span{width:3px;background:var(--cyan);border-radius:2px;animation:wave 1.1s ease-in-out infinite}
.tap-btn{width:100%;background:linear-gradient(180deg,var(--cyan),#1b9fc9);color:#06141f;border:none;
  border-radius:8px;padding:8px;font-weight:700;font-size:11px;letter-spacing:.5px;cursor:pointer}
.focus-btn{margin-top:8px;width:100%;background:transparent;border:1px solid var(--border);
  color:var(--muted);border-radius:8px;padding:7px;font-size:11px;cursor:pointer}
.focus-btn.on{color:var(--amber);border-color:rgba(224,168,58,.5);background:rgba(224,168,58,.08)}

/* ── Main grid ── */
.main{display:grid;grid-template-columns:230px 1fr 280px;gap:14px;padding:14px;overflow:hidden}
.panel{background:var(--panel);border:1px solid var(--border);border-radius:12px;padding:14px;
  display:flex;flex-direction:column;overflow-y:auto}
.panel-title{font-size:11px;letter-spacing:1.5px;color:var(--cyan2);text-transform:uppercase;
  margin-bottom:10px;display:flex;align-items:center;justify-content:space-between}
.panel-title .src{font-size:9px;color:var(--muted);text-transform:none;letter-spacing:0;font-weight:400}

/* AI CORE OVERVIEW (left column) */
.core-row{display:flex;align-items:center;justify-content:space-between;padding:8px 0;
  border-bottom:1px solid var(--border);font-size:12px}
.core-row:last-child{border-bottom:none}
.core-row .v{color:var(--green);font-weight:600;font-size:11px}
.core-row .v.warn{color:var(--amber)}
.core-row .v.bad{color:var(--red)}

/* Center column: orb + agents + monitors */
.center-col{display:flex;flex-direction:column;gap:14px;overflow-y:auto}
.orb-stage{background:var(--panel);border:1px solid var(--border);border-radius:12px;
  display:flex;flex-direction:column;align-items:center;justify-content:center;padding:18px;
  position:relative;min-height:240px}
canvas#orb{cursor:pointer}
.orb-label{margin-top:6px;font-size:11px;color:var(--muted);letter-spacing:1px}
.orb-hint{position:absolute;bottom:10px;font-size:10px;color:var(--muted);opacity:.7}

.agents-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}
.agent-tile{background:var(--panel2);border:1px solid var(--border);border-radius:10px;
  padding:10px;font-size:11px}
.agent-tile .name{font-weight:600;color:var(--text);margin-bottom:4px}
.agent-tile .stat{color:var(--green);font-size:10px}
.agent-tile.idle .stat{color:var(--muted)}

.monitor-row{display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px}
.gauge-card{background:var(--panel2);border:1px solid var(--border);border-radius:10px;
  padding:10px;text-align:center}
.gauge-card .label{font-size:10px;color:var(--muted);margin-bottom:6px}
.gauge-card .num{font-size:18px;font-weight:700;color:var(--cyan2)}

/* Right column: intel feed, timeline, quick commands */
.feed-item{padding:7px 0;border-bottom:1px solid var(--border);font-size:11px;color:var(--text)}
.feed-item .t{color:var(--muted);font-size:9px}
.timeline-item{display:flex;gap:8px;padding:6px 0;font-size:11px}
.timeline-item .dot{width:7px;height:7px;border-radius:50%;background:var(--cyan);margin-top:4px;flex-shrink:0}
.qc-btn{display:block;width:100%;text-align:left;background:var(--panel2);border:1px solid var(--border);
  color:var(--text);border-radius:8px;padding:8px 10px;margin-bottom:6px;font-size:11px;cursor:pointer}
.qc-btn:hover{border-color:var(--cyan)}

/* Studio tab placeholder */
.studio-grid{display:grid;grid-template-columns:1fr 220px;gap:14px;height:100%}
video{width:100%;border-radius:10px;background:#000}
.studio-list-item{padding:8px;border:1px solid var(--border);border-radius:8px;margin-bottom:6px;font-size:11px}

/* Generic placeholder screen */
.placeholder-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--muted);text-align:center;gap:8px}
.placeholder-screen .big{font-size:13px;color:var(--text)}
.placeholder-screen .small{font-size:11px;max-width:420px}

/* Bottom bar */
.bottombar{grid-column:1/3;border-top:1px solid var(--border);background:rgba(10,20,32,.6);
  display:flex;align-items:center;justify-content:space-between;padding:0 20px;font-size:11px;color:var(--muted)}
.talk-pill{display:flex;align-items:center;gap:10px;background:var(--panel);border:1px solid var(--border);
  border-radius:20px;padding:5px 16px;cursor:pointer}
.talk-pill .label{color:var(--cyan2);font-weight:600;letter-spacing:1px;font-size:10px}
.mini-wave{display:flex;align-items:center;gap:2px;height:14px}
.mini-wave span{width:2px;background:var(--cyan);border-radius:1px;animation:wave 1s ease-in-out infinite}
.brief-btn{background:var(--panel);border:1px solid var(--border);color:var(--cyan2);
  border-radius:8px;padding:5px 12px;font-size:10px;cursor:pointer}

@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes wave{0%,100%{height:4px}50%{height:18px}}

.screen{display:none}
.screen.active{display:block;height:100%}
.main-grid-wrap{height:100%}
</style>
</head>
<body>
<div class="app">

  <div class="topbar">
    <div class="left">
      <div class="brand">⬡ FRANK</div>
      <div class="status-pill"><span class="dot"></span>SYSTEM STATUS ● OPTIMAL</div>
    </div>
    <div class="center">
      <input class="search" placeholder="Search listings, orders, tools, knowledge base…">
    </div>
    <div class="right">
      <div class="clock"><div class="time" id="clk">--:--</div><div id="dt">--</div></div>
      <div class="icon-btn">🔔<span class="badge">3</span></div>
      <div class="icon-btn">⚙</div>
      <div class="operator"><div class="av">S</div><span style="font-size:11px">Scott · Owner</span></div>
    </div>
  </div>

  <div class="sidebar">
    <div class="nav-section">Frank</div>
    <div class="nav-item active" data-screen="cmd"><span class="ic">⌂</span>Command Center</div>
    <div class="nav-item" data-screen="core"><span class="ic">◎</span>AI Core</div>
    <div class="nav-item" data-screen="agents"><span class="ic">⚙</span>Agents</div>
    <div class="nav-item" data-screen="tasks"><span class="ic">☑</span>Tasks<span class="nbadge">3</span></div>
    <div class="nav-item" data-screen="calendar"><span class="ic">▦</span>Calendar</div>

    <div class="nav-section">Knowledge</div>
    <div class="nav-item" data-screen="memory"><span class="ic">✦</span>Memory</div>
    <div class="nav-item" data-screen="conversations"><span class="ic">💬</span>Conversations<span class="nbadge">12</span></div>
    <div class="nav-item" data-screen="kb"><span class="ic">📚</span>Knowledge Base</div>

    <div class="nav-section">Tools</div>
    <div class="nav-item" data-screen="tools"><span class="ic">🛠</span>Tools &amp; Skills<span class="nbadge">12</span></div>
    <div class="nav-item" data-screen="workflows"><span class="ic">⇄</span>Workflows</div>
    <div class="nav-item" data-screen="studio"><span class="ic">▶</span>Studio</div>

    <div class="voice-widget">
      <div class="vw-title">VOICE STATUS</div>
      <div class="wave-row" id="sidebar-wave">
        <span style="animation-delay:0s"></span><span style="animation-delay:.1s"></span>
        <span style="animation-delay:.2s"></span><span style="animation-delay:.3s"></span>
        <span style="animation-delay:.4s"></span><span style="animation-delay:.3s"></span>
        <span style="animation-delay:.2s"></span><span style="animation-delay:.1s"></span>
      </div>
      <button class="tap-btn" id="tap-speak">🎙 TAP TO SPEAK</button>
      <button class="focus-btn" id="focus-toggle">FOCUS MODE: OFF</button>
    </div>
  </div>

  <!-- ══════════ COMMAND CENTER (home) ══════════ -->
  <div class="screen active" id="screen-cmd">
    <div class="main">
      <div class="panel">
        <div class="panel-title">AI Core Overview <span class="src">/health</span></div>
        <div class="core-row"><span>AI Core</span><span class="v">Online</span></div>
        <div class="core-row"><span>Memory</span><span class="v">Synced</span></div>
        <div class="core-row"><span>Voice</span><span class="v warn">Relay offline</span></div>
        <div class="core-row"><span>Agents</span><span class="v">5 / 5 running</span></div>
        <div class="core-row"><span>LLMs</span><span class="v">Claude · OpenAI</span></div>
        <div class="core-row"><span>System</span><span class="v">Healthy</span></div>

        <div class="panel-title" style="margin-top:18px">LLM Status <span class="src">/api/credentials/status</span></div>
        <div class="core-row"><span>Anthropic</span><span class="v">Connected</span></div>
        <div class="core-row"><span>OpenAI</span><span class="v">Connected</span></div>
        <div class="core-row"><span>Etsy API</span><span class="v">Token valid</span></div>
      </div>

      <div class="center-col">
        <div class="orb-stage">
          <canvas id="orb" width="220" height="220"></canvas>
          <div class="orb-label">FRANK · IDLE</div>
          <div class="orb-hint">click orb to preview "speaking" reaction</div>
        </div>

        <div class="panel" style="flex:none">
          <div class="panel-title">Active Agents <span class="src">live-status registry (new)</span></div>
          <div class="agents-row">
            <div class="agent-tile"><div class="name">Snapshot</div><div class="stat">● running</div></div>
            <div class="agent-tile"><div class="name">Suggestion Warmer</div><div class="stat">● running</div></div>
            <div class="agent-tile"><div class="name">Token Sync</div><div class="stat">● running</div></div>
            <div class="agent-tile"><div class="name">Quality Audit</div><div class="stat">● running</div></div>
            <div class="agent-tile"><div class="name">Autoresponder</div><div class="stat">● running</div></div>
            <div class="agent-tile idle"><div class="name">Local Relay</div><div class="stat">○ not built</div></div>
            <div class="agent-tile idle"><div class="name">Context Compactor</div><div class="stat">○ not built</div></div>
          </div>
        </div>

        <div class="panel" style="flex:none">
          <div class="panel-title">System Monitor / Memory Insights <span class="src">server stats + chat_messages + log_learning</span></div>
          <div class="monitor-row">
            <div class="gauge-card"><div class="label">CPU</div><div class="num">—</div></div>
            <div class="gauge-card"><div class="label">RAM</div><div class="num">—</div></div>
            <div class="gauge-card"><div class="label">Memories</div><div class="num">—</div></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-title">Live Intelligence Feed <span class="src">queue+audits+todos</span></div>
        <div class="feed-item">Quality audit flagged 1 listing for review<div class="t">2m ago</div></div>
        <div class="feed-item">3 actions pending approval in queue<div class="t">14m ago</div></div>
        <div class="feed-item">Token sync refreshed Etsy access token<div class="t">41m ago</div></div>

        <div class="panel-title" style="margin-top:16px">Mission Timeline <span class="src">/api/todos</span></div>
        <div class="timeline-item"><span class="dot"></span>Friday shop health review</div>
        <div class="timeline-item"><span class="dot"></span>Restock 3D print queue</div>
        <div class="timeline-item"><span class="dot"></span>Update seasonal keywords</div>

        <div class="panel-title" style="margin-top:16px">Quick Commands</div>
        <button class="qc-btn">▸ Run shop health check</button>
        <button class="qc-btn">▸ Add a todo</button>
        <button class="qc-btn">▸ Start voice session</button>
      </div>
    </div>
  </div>

  <!-- ══════════ generic placeholder screens ══════════ -->
  <div class="screen" id="screen-core"><div class="placeholder-screen"><div class="big">AI Core</div><div class="small">Real model/provider state from /api/credentials/status + build/version from /health. Wired in Step 2.</div></div></div>
  <div class="screen" id="screen-agents"><div class="placeholder-screen"><div class="big">Agents</div><div class="small">The 5 real background loops + Local Relay + Context Compactor, each reporting live status via a new registry. Wired in Step 2.</div></div></div>
  <div class="screen" id="screen-tasks"><div class="placeholder-screen"><div class="big">Tasks</div><div class="small">/api/todos — already real today. Promoted to its own full screen in Step 2.</div></div></div>
  <div class="screen" id="screen-calendar"><div class="placeholder-screen"><div class="big">Calendar</div><div class="small">Combines todo due dates + CLAUDE.md's weekly/monthly/quarterly cadence + Seasonal Keyword Calendar. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-memory"><div class="placeholder-screen"><div class="big">Memory</div><div class="small">Constellation of real chat_messages + log_learning + knowledge_base docs — counts from the DB, never invented. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-conversations"><div class="placeholder-screen"><div class="big">Conversations</div><div class="small">Searchable chat_messages history. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-kb"><div class="placeholder-screen"><div class="big">Knowledge Base</div><div class="small">Browse/search reader for the 9 real markdown docs in data/knowledge_base/. Built in Step 2.</div></div></div>
  <div class="screen" id="screen-tools"><div class="placeholder-screen"><div class="big">Tools &amp; Skills</div><div class="small">Live list of every entry in AGENT_TOOLS (currently 12), badge = len(AGENT_TOOLS). Built in Step 2.</div></div></div>
  <div class="screen" id="screen-workflows"><div class="placeholder-screen"><div class="big">Workflows</div><div class="small">Runnable workflow list — each Run stages through the existing approval gate. Built in Step 2.</div></div></div>

  <div class="screen" id="screen-studio">
    <div class="main" style="grid-template-columns:1fr">
      <div class="panel">
        <div class="panel-title">Studio — Video Preview &amp; Generation <span class="src">/api/files (new generate_listing_video tool)</span></div>
        <div class="studio-grid">
          <div>
            <video controls poster="" style="aspect-ratio:16/9"></video>
            <div style="margin-top:10px;color:var(--muted);font-size:11px">No videos generated yet. Player wired to /api/files in Step 3.</div>
          </div>
          <div>
            <div class="panel-title" style="margin-top:0">Generated Videos</div>
            <div class="studio-list-item">— none yet —</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div class="bottombar">
    <div>📍 Local · ⛅ — · 🌐 Relay: not built</div>
    <div class="talk-pill" id="talk-pill">
      <div class="mini-wave"><span></span><span></span><span></span><span></span></div>
      <span class="label">TALK TO FRANK</span>
      <div class="mini-wave"><span></span><span></span><span></span><span></span></div>
    </div>
    <button class="brief-btn">Executive Briefing</button>
  </div>

</div>

<script>
// ── Nav switching ──
document.querySelectorAll('.nav-item').forEach(item=>{
  item.addEventListener('click',()=>{
    document.querySelectorAll('.nav-item').forEach(i=>i.classList.remove('active'));
    item.classList.add('active');
    const target = item.dataset.screen;
    document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
    const el = document.getElementById('screen-'+target);
    if(el) el.classList.add('active');
  });
});

// ── Clock ──
function tick(){
  const d = new Date();
  document.getElementById('clk').textContent = d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'});
  document.getElementById('dt').textContent = d.toLocaleDateString([], {month:'short',day:'numeric',year:'numeric'});
}
tick(); setInterval(tick, 1000*30);

// ── Focus mode toggle (visual only) ──
document.getElementById('focus-toggle').addEventListener('click', function(){
  this.classList.toggle('on');
  this.textContent = this.classList.contains('on') ? 'FOCUS MODE: ON' : 'FOCUS MODE: OFF';
});

// ── Orb: idle rotating wireframe particle sphere, audio-reactive on click (demo only) ──
const canvas = document.getElementById('orb');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height, CX = W/2, CY = H/2, R = 80;
let particles = [];
const N_LAT = 10, N_LON = 14;
for(let i=0;i<=N_LAT;i++){
  const lat = Math.PI * (i/N_LAT - 0.5);
  for(let j=0;j<N_LON;j++){
    const lon = 2*Math.PI * (j/N_LON);
    particles.push({lat, lon});
  }
}
let rot = 0, speaking = false, speakT = 0;
const orbLabel = document.querySelector('.orb-label');

function frame(){
  ctx.clearRect(0,0,W,H);
  rot += speaking ? 0.03 : 0.012;
  let amp = 0;
  if(speaking){
    speakT += 0.18;
    amp = (Math.sin(speakT*3.1)*0.5+0.5) * (Math.sin(speakT*1.7)*0.3+0.7);
  }
  const glow = speaking ? 0.55 + amp*0.45 : 0.35;
  ctx.shadowBlur = 18 + amp*30;
  ctx.shadowColor = speaking ? 'rgba(122,232,255,'+glow+')' : 'rgba(58,214,255,0.35)';

  const pts = particles.map(p=>{
    const lon = p.lon + rot;
    const rr = R * (1 + (speaking ? amp*0.18*Math.sin(p.lat*4+speakT*2) : 0));
    const x = rr * Math.cos(p.lat) * Math.cos(lon);
    const y = rr * Math.sin(p.lat);
    const z = rr * Math.cos(p.lat) * Math.sin(lon);
    const scale = 220 / (220 - z);
    return {x: CX + x*scale*0.9, y: CY + y*scale*0.9, z, scale};
  });

  ctx.strokeStyle = speaking ? 'rgba(122,232,255,0.5)' : 'rgba(58,214,255,0.25)';
  ctx.lineWidth = 0.6;
  for(let i=0;i<N_LAT;i++){
    for(let j=0;j<N_LON;j++){
      const a = pts[i*N_LON+j], b = pts[i*N_LON+((j+1)%N_LON)], c = pts[(i+1)*N_LON+j];
      if(a && b){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();}
      if(a && c){ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(c.x,c.y);ctx.stroke();}
    }
  }
  pts.forEach(p=>{
    const sz = p.scale > 1 ? 1.6 : 1;
    ctx.fillStyle = speaking ? 'rgba(122,232,255,0.9)' : 'rgba(58,214,255,0.7)';
    ctx.beginPath();ctx.arc(p.x,p.y,sz,0,Math.PI*2);ctx.fill();
  });

  // core glow
  const grad = ctx.createRadialGradient(CX,CY,4,CX,CY,30+amp*20);
  grad.addColorStop(0, speaking ? 'rgba(180,240,255,'+ (0.8+amp*0.2) +')' : 'rgba(58,214,255,0.5)');
  grad.addColorStop(1, 'rgba(58,214,255,0)');
  ctx.fillStyle = grad;
  ctx.beginPath();ctx.arc(CX,CY,30+amp*20,0,Math.PI*2);ctx.fill();

  ctx.shadowBlur = 0;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

function setSpeaking(on){
  speaking = on;
  orbLabel.textContent = on ? 'FRANK · SPEAKING (demo)' : 'FRANK · IDLE';
}
canvas.addEventListener('click', ()=>{
  setSpeaking(true);
  setTimeout(()=>setSpeaking(false), 3000);
});
document.getElementById('tap-speak').addEventListener('click', ()=>{
  setSpeaking(true);
  setTimeout(()=>setSpeaking(false), 3000);
});
document.getElementById('talk-pill').addEventListener('click', ()=>{
  setSpeaking(true);
  setTimeout(()=>setSpeaking(false), 3000);
});
</script>
</body>
</html>"""
