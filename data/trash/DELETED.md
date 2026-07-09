# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20260623-001 date=2026-06-23 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="dead CSS: old voice-widget mic UI (.wave-row/.mic-circle/.vw-sub/.vw-tap/.focus-btn) — replaced by QUICK COMMANDS buttons + bottom talk-pill; no HTML uses these" -->
## 20260623-001 · 2026-06-23 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** dead CSS: old voice-widget mic UI (.wave-row/.mic-circle/.vw-sub/.vw-tap/.focus-btn) — replaced by QUICK COMMANDS buttons + bottom talk-pill; no HTML uses these  
**Payload:** `data/trash/files/20260623-001__snippet.txt`

```python
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
```

<!-- /TRASH 20260623-001 -->

<!-- TRASH id=20260623-002 date=2026-06-23 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="dead CSS: @keyframes micpulse — only used by now-removed .mic-circle.live" -->
## 20260623-002 · 2026-06-23 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** dead CSS: @keyframes micpulse — only used by now-removed .mic-circle.live  
**Payload:** `data/trash/files/20260623-002__snippet.txt`

```python
@keyframes micpulse{0%,100%{box-shadow:0 0 22px rgba(58,214,255,.35), inset 0 0 18px rgba(58,214,255,.15)}
  50%{box-shadow:0 0 34px rgba(122,232,255,.6), inset 0 0 22px rgba(122,232,255,.3)}}
```

<!-- /TRASH 20260623-002 -->

<!-- TRASH id=20260623-003 date=2026-06-23 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="dead CSS: .col-quick — never applied to any HTML element" -->
## 20260623-003 · 2026-06-23 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** dead CSS: .col-quick — never applied to any HTML element  
**Payload:** `data/trash/files/20260623-003__snippet.txt`

```python
.col-quick{flex:0.85}
```

<!-- /TRASH 20260623-003 -->

<!-- TRASH id=20260623-004 date=2026-06-23 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="dead JS: openDrawer() — never called (hamburger uses toggleDrawer, backdrop uses closeDrawer)" -->
## 20260623-004 · 2026-06-23 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** dead JS: openDrawer() — never called (hamburger uses toggleDrawer, backdrop uses closeDrawer)  
**Payload:** `data/trash/files/20260623-004__snippet.txt`

```python
function openDrawer(){ document.body.classList.add('drawer-open'); }
```

<!-- /TRASH 20260623-004 -->

<!-- TRASH id=20260623-005 date=2026-06-23 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="dead JS: #focus-toggle handler — no element with id 'focus-toggle' exists in the HTML" -->
## 20260623-005 · 2026-06-23 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** dead JS: #focus-toggle handler — no element with id 'focus-toggle' exists in the HTML  
**Payload:** `data/trash/files/20260623-005__snippet.txt`

```python
// ── Focus mode toggle (visual only; element only present when the voice widget is shown) ──
const focusToggle = document.getElementById('focus-toggle');
if(focusToggle) focusToggle.addEventListener('click', function(){
  this.classList.toggle('on');
  this.textContent = this.classList.contains('on') ? 'FOCUS MODE: ON' : 'FOCUS MODE: OFF';
});
```

<!-- /TRASH 20260623-005 -->

<!-- TRASH id=20260624-001 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-001 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-001__snippet.txt`

```python
.drawer-toggle{display:none}
.drawer-search{display:none}
#drawer-backdrop{display:none}
```

<!-- /TRASH 20260624-001 -->

<!-- TRASH id=20260624-002 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-002 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-002__snippet.txt`

```python
  .drawer-toggle{display:flex}
```

<!-- /TRASH 20260624-002 -->

<!-- TRASH id=20260624-003 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-003 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-003__snippet.txt`

```python
  #drawer-backdrop{
    display:none;position:fixed;inset:0;background:rgba(0,0,0,.5);z-index:150;
  }
  body.drawer-open #drawer-backdrop{display:block}
```

<!-- /TRASH 20260624-003 -->

<!-- TRASH id=20260624-004 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-004 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-004__snippet.txt`

```python
    <input class="search drawer-search" placeholder="Search listings, orders, tools, knowledge base…">
```

<!-- /TRASH 20260624-004 -->

<!-- TRASH id=20260624-005 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-005 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-005__snippet.txt`

```python
  <div id="drawer-backdrop"></div>
```

<!-- /TRASH 20260624-005 -->

<!-- TRASH id=20260624-006 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in." -->
## 20260624-006 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Retiring off-canvas mobile drawer nav in favor of orb-only/control-center toggle; sidebar now renders inline/stacked on mobile instead of sliding in.  
**Payload:** `data/trash/files/20260624-006__snippet.txt`

```python
  <div id="drawer-backdrop"></div>
```

<!-- /TRASH 20260624-006 -->

<!-- TRASH id=20260624-007 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Replaced fake System Monitor placeholder (hardcoded conic-gradient CPU/RAM/DISK gauges, zero backend) with real Dependency Health panel backed by /api/system/dependencies" -->
## 20260624-007 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Replaced fake System Monitor placeholder (hardcoded conic-gradient CPU/RAM/DISK gauges, zero backend) with real Dependency Health panel backed by /api/system/dependencies  
**Payload:** `data/trash/files/20260624-007__snippet.txt`

```python
        <div class="panel brk col-sysmon">
          <div class="panel-title">System Monitor <span class="src">server stats</span></div>
          <div class="gauge-row">
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 22%, var(--border) 22% 100%)"></div><div class="inner"><div class="num">22%</div><div class="lab">CPU</div></div></div>
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 54%, var(--border) 54% 100%)"></div><div class="inner"><div class="num">54%</div><div class="lab">RAM</div></div></div>
            <div class="gauge"><div class="ring" style="background:conic-gradient(var(--cyan) 0% 40%, var(--border) 40% 100%)"></div><div class="inner"><div class="num">40%</div><div class="lab">DISK</div></div></div>
          </div>
        </div>
```

<!-- /TRASH 20260624-007 -->

<!-- TRASH id=20260624-008 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Orphaned .gauge/.gauge-row/.ring CSS — only consumer was the removed fake System Monitor gauge markup" -->
## 20260624-008 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Orphaned .gauge/.gauge-row/.ring CSS — only consumer was the removed fake System Monitor gauge markup  
**Payload:** `data/trash/files/20260624-008__snippet.txt`

```python
.gauge-row{display:flex;gap:10px;flex:1;align-items:center;justify-content:space-around}
.gauge{width:78px;height:78px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  position:relative;flex-shrink:0}
.gauge .ring{position:absolute;inset:0;border-radius:50%}
.gauge .inner{position:relative;width:56px;height:56px;border-radius:50%;background:var(--panel2);
  display:flex;flex-direction:column;align-items:center;justify-content:center}
.gauge .inner .num{font-size:13px;font-weight:700;color:var(--cyan2)}
.gauge .inner .lab{font-size:8px;color:var(--muted);letter-spacing:.5px}
```

<!-- /TRASH 20260624-008 -->

<!-- TRASH id=20260624-009 date=2026-06-24 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Dead topbar icon — no handler, no discoverable intent anywhere in the codebase; removed per Scott's 2026-06-24 audit decision" -->
## 20260624-009 · 2026-06-24 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Dead topbar icon — no handler, no discoverable intent anywhere in the codebase; removed per Scott's 2026-06-24 audit decision  
**Payload:** `data/trash/files/20260624-009__snippet.txt`

```python
<div class="icon-btn">▦</div>
```

<!-- /TRASH 20260624-009 -->

<!-- TRASH id=20260625-001 date=2026-06-25 kind=snippet source="tools/api_server/main.py" reason="Dead endpoint - zero callers found anywhere in the codebase (Frank, Hub _WEB_UI, or any tools/ script); superseded by /api/analytics which returns a superset of the same data. Removed per audit decision 2026-06-25." -->
## 20260625-001 · 2026-06-25 · snippet · `tools/api_server/main.py`
**Reason:** Dead endpoint - zero callers found anywhere in the codebase (Frank, Hub _WEB_UI, or any tools/ script); superseded by /api/analytics which returns a superset of the same data. Removed per audit decision 2026-06-25.  
**Payload:** `data/trash/files/20260625-001__snippet.txt`

```python
@app.get("/api/history")
async def get_history(days: int = 30, _token: str = Depends(_auth)):
    """Daily shop snapshots (oldest-first) plus simple period deltas for trends."""
    days = max(1, min(days, 365))
    rows = await asyncio.to_thread(db.get_metric_history, days)
    delta = {}
    if len(rows) >= 2:
        first, last = rows[0], rows[-1]
        for k in ("revenue_30d", "active_listings", "total_sales", "total_reviews", "avg_rating"):
            a, b = first.get(k), last.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                delta[k] = round(b - a, 2)
    return {"days": days, "count": len(rows), "delta": delta, "snapshots": rows}
```

<!-- /TRASH 20260625-001 -->

<!-- TRASH id=20260701-001 date=2026-07-01 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v83 3-column layout: replaced mrow flex rows with col-left/col-center/col-right CSS grid" -->
## 20260701-001 · 2026-07-01 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v83 3-column layout: replaced mrow flex rows with col-left/col-center/col-right CSS grid  
**Payload:** `data/trash/files/20260701-001__snippet.txt`

```python
.mrow{display:flex;gap:12px;min-height:0}
.mrow.rowA{flex:1}
.mrow.rowB{flex:1.25}
.mrow.rowC{flex:0.95}
.col-chat{flex:1.6 1 0;min-width:0}
```

<!-- /TRASH 20260701-001 -->

<!-- TRASH id=20260701-002 date=2026-07-01 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v83 3-column layout: old rowA column sizes replaced by new column-context flex rules" -->
## 20260701-002 · 2026-07-01 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v83 3-column layout: old rowA column sizes replaced by new column-context flex rules  
**Payload:** `data/trash/files/20260701-002__snippet.txt`

```python
/* Row A: AI Core Overview | Orb Hero | Live Intelligence Feed */
.col-aicore{flex:0 0 218px}
.col-orb{flex:1 1 auto}
.col-feed{flex:0 0 270px}
```

<!-- /TRASH 20260701-002 -->

<!-- TRASH id=20260701-003 date=2026-07-01 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v83 3-column layout: old rowB column sizes replaced by new column-context flex rules" -->
## 20260701-003 · 2026-07-01 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v83 3-column layout: old rowB column sizes replaced by new column-context flex rules  
**Payload:** `data/trash/files/20260701-003__snippet.txt`

```python
/* Row B: Active Agents | Mission Timeline | Quick Commands */
.col-agents{flex:1.1}
.col-timeline{flex:1}
```

<!-- /TRASH 20260701-003 -->

<!-- TRASH id=20260701-004 date=2026-07-01 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v83 3-column layout: old rowC column sizes replaced by new column-context flex rules" -->
## 20260701-004 · 2026-07-01 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v83 3-column layout: old rowC column sizes replaced by new column-context flex rules  
**Payload:** `data/trash/files/20260701-004__snippet.txt`

```python
/* Row C: System Monitor | Memory Insights | LLM Status */
.col-sysmon{flex:1}
.col-meminsights{flex:1}
.col-shop{flex:1.3}
```

<!-- /TRASH 20260701-004 -->

<!-- TRASH id=20260702-001 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead mem-canvas code, element removed in v85" -->
## 20260702-001 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead mem-canvas code, element removed in v85  
**Payload:** `data/trash/files/20260702-001__snippet.txt`

```python
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
```

<!-- /TRASH 20260702-001 -->

<!-- TRASH id=20260702-002 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead updateMemoryWidget, mem-stat-memories/turns elements removed in v85" -->
## 20260702-002 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead updateMemoryWidget, mem-stat-memories/turns elements removed in v85  
**Payload:** `data/trash/files/20260702-002__snippet.txt`

```python
function updateMemoryWidget(d) {
  const memEl = document.getElementById('mem-stat-memories');
  const turnsEl = document.getElementById('mem-stat-turns');
  if (memEl) memEl.textContent = d.learnings_count;
  if (turnsEl) turnsEl.textContent = d.total_messages;
  drawMem(d.recent_session_sizes || []);
}
```

<!-- /TRASH 20260702-002 -->

<!-- TRASH id=20260702-003 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead isControlCenterOpen — no callers remain" -->
## 20260702-003 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead isControlCenterOpen — no callers remain  
**Payload:** `data/trash/files/20260702-003__snippet.txt`

```python
function isControlCenterOpen(){ return document.body.classList.contains('cc-open'); }
```

<!-- /TRASH 20260702-003 -->

<!-- TRASH id=20260702-004 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead openControlCenter — no callers remain" -->
## 20260702-004 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead openControlCenter — no callers remain  
**Payload:** `data/trash/files/20260702-004__snippet.txt`

```python
function openControlCenter(){ document.body.classList.add('cc-open'); }
```

<!-- /TRASH 20260702-004 -->

<!-- TRASH id=20260702-005 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead .orb-col CSS — element removed" -->
## 20260702-005 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead .orb-col CSS — element removed  
**Payload:** `data/trash/files/20260702-005__snippet.txt`

```python
.orb-col{flex:1 1 auto}
```

<!-- /TRASH 20260702-005 -->

<!-- TRASH id=20260702-006 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead .orb-hero CSS — element removed" -->
## 20260702-006 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead .orb-hero CSS — element removed  
**Payload:** `data/trash/files/20260702-006__snippet.txt`

```python
.orb-hero{align-items:center;justify-content:center;position:relative;
  background:
    radial-gradient(circle at 50% 38%, rgba(58,214,255,.14), transparent 60%),
    radial-gradient(rgba(58,214,255,.10) 1px, transparent 1px);
  background-size:auto, 22px 22px;background-color:var(--panel)}
```

<!-- /TRASH 20260702-006 -->

<!-- TRASH id=20260702-007 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead .mem-row/.mem-canvas-wrap/.mem-stats/.mem-stat CSS — elements removed in v85" -->
## 20260702-007 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead .mem-row/.mem-canvas-wrap/.mem-stats/.mem-stat CSS — elements removed in v85  
**Payload:** `data/trash/files/20260702-007__snippet.txt`

```python
.mem-row{display:flex;gap:10px;flex:1;min-height:0;overflow-y:auto;align-items:center}
.mem-canvas-wrap{display:none}
.mem-stats{display:flex;flex-direction:row;flex-wrap:wrap;gap:16px 24px;flex:1;align-items:center;justify-content:space-around;padding:4px 8px}
.mem-stat .n{font-size:14px;font-weight:700;color:var(--cyan2)}
.mem-stat .l{font-size:8.5px;color:var(--muted);letter-spacing:.5px}
```

<!-- /TRASH 20260702-007 -->

<!-- TRASH id=20260702-008 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead .placeholder-screen CSS — elements removed" -->
## 20260702-008 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead .placeholder-screen CSS — elements removed  
**Payload:** `data/trash/files/20260702-008__snippet.txt`

```python
/* Generic placeholder screen */
.placeholder-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--muted);text-align:center;gap:8px}
.placeholder-screen .big{font-size:14px;color:var(--text);letter-spacing:1px}
.placeholder-screen .small{font-size:11px;max-width:440px}
```

<!-- /TRASH 20260702-008 -->

<!-- TRASH id=20260702-009 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead mobile .orb-hero — element removed" -->
## 20260702-009 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead mobile .orb-hero — element removed  
**Payload:** `data/trash/files/20260702-009__snippet.txt`

```python
.orb-hero{min-height:260px}
```

<!-- /TRASH 20260702-009 -->

<!-- TRASH id=20260702-010 date=2026-07-02 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="v88 cleanup: dead mobile .mem-canvas-wrap — element removed" -->
## 20260702-010 · 2026-07-02 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** v88 cleanup: dead mobile .mem-canvas-wrap — element removed  
**Payload:** `data/trash/files/20260702-010__snippet.txt`

```python
.mem-canvas-wrap{min-height:160px}
```

<!-- /TRASH 20260702-010 -->

<!-- TRASH id=20260702-011 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix6: logger NameError - logger not defined, replaced with print()" -->
## 20260702-011 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix6: logger NameError - logger not defined, replaced with print()  
**Payload:** `data/trash/files/20260702-011__snippet.txt`

```python
        logger.error("studio_generate_video error: %s", exc, exc_info=True)
```

<!-- /TRASH 20260702-011 -->

<!-- TRASH id=20260702-012 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA dashboard _WEB_UI constant replaced by /frank HUD" -->
## 20260702-012 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA dashboard _WEB_UI constant replaced by /frank HUD  
**Payload:** `data/trash/files/20260702-012__snippet.txt`

```python
_WEB_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content=""" + '"' + business_config.BUSINESS_NAME + '"' + """>
<meta name="theme-color" content="#0D1B2A">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>""" + business_config.BUSINESS_NAME + """</title>
<style>
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#0D1B2A;--card:#162033;--border:#1e2d42;--gold:#C9A84C;--gold2:#e8c96a;
  --text:#e8edf2;--muted:#6b7d91;--green:#4caf82;--red:#e05555;
  --hdr:calc(52px + env(safe-area-inset-top,0px));
  --nav:calc(60px + env(safe-area-inset-bottom,0px))
}
html,body{height:100%;background:var(--bg);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;overflow:hidden}
header{position:fixed;top:0;left:0;right:0;z-index:200;height:var(--hdr);background:var(--card);border-bottom:1px solid var(--border);display:flex;align-items:flex-end;justify-content:space-between;padding:0 16px 14px}
header h1{font-size:17px;font-weight:700;color:var(--gold)}
header span{font-size:12px;color:var(--muted)}
nav{position:fixed;bottom:0;left:0;right:0;z-index:200;height:var(--nav);background:var(--card);border-top:1px solid var(--border);display:flex;align-items:flex-start;padding-top:8px}
nav button{flex:1;background:none;border:none;color:var(--muted);font-size:10px;font-weight:600;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;transition:color .15s;height:44px;-webkit-tap-highlight-color:rgba(201,168,76,.15)}
nav button.active{color:var(--gold)}
nav button svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.screen{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);overflow-y:auto;-webkit-overflow-scrolling:touch;padding:16px;display:none;background:var(--bg)}
.screen.active{display:block}
.card{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:12px}
.card-row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px}
.metric{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px}
.metric .label{font-size:11px;color:var(--muted);margin-bottom:4px;text-transform:uppercase;letter-spacing:.4px}
.metric .value{font-size:24px;font-weight:700;color:var(--text)}
.metric .sub{font-size:11px;color:var(--muted);margin-top:2px}
.metric.gold .value{color:var(--gold)}
.section-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.banner{background:#1a2d1a;border:1px solid #2d5a2d;border-radius:10px;padding:12px 14px;margin-bottom:12px;font-size:13px;color:#7ec87e}
.listing-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.listing-item:last-child{border-bottom:none}
.thumb{width:52px;height:52px;border-radius:8px;object-fit:cover;background:var(--border);flex-shrink:0}
.thumb-placeholder{width:52px;height:52px;border-radius:8px;background:var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:20px}
.listing-info{flex:1;min-width:0}
.listing-title{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.listing-meta{font-size:11px;color:var(--muted);margin-top:3px}
.listing-price{font-size:14px;font-weight:700;color:var(--gold);flex-shrink:0}
.badge{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:20px;margin-left:6px}
.badge.draft{background:#1a2030;color:#6b8ab5;border:1px solid #2a3d5a}
.badge.active{background:#1a2d1a;color:#4caf82;border:1px solid #2d5a2d}
.nav-badge{position:absolute;top:2px;margin-left:14px;background:var(--red);color:#fff;font-size:9px;font-weight:700;min-width:15px;height:15px;border-radius:8px;display:inline-flex;align-items:center;justify-content:center;padding:0 4px}
.act-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.act-card.high{border-left-color:var(--red)}
.act-card.medium{border-left-color:var(--gold)}
.act-card.low{border-left-color:#4a6b8a}
.act-sev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px}
.act-sev.high{background:#2d1a1a;color:#e07070}
.act-sev.medium{background:#2d2a1a;color:var(--gold2)}
.act-sev.low{background:#1a2330;color:#7ba0c2}
.act-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.act-detail{font-size:12px;color:var(--muted);line-height:1.45}
.act-sug{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.act-sug b{color:var(--gold2);font-weight:600}
.act-btns{display:flex;gap:8px;margin-top:9px}
.act-btn{flex:1;text-align:center;padding:7px;border-radius:7px;font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}
.act-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.act-card.approval{border-left-color:var(--green);background:#13241c}
.act-sev.approval{background:#13241c;color:#5fcf9e;border:1px solid #2d5a44}
.act-btn.approve{background:var(--green);color:#06140d;border-color:var(--green)}
.act-btn.reject{color:#e08585;border-color:#5a2d2d}
.toggle-row{display:flex;gap:8px;margin-bottom:12px}
.toggle-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.toggle-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.chip-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.chip-btn{padding:6px 12px;border-radius:20px;border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
.chip-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.listing-detail{padding:2px 14px 12px;margin:-2px 0 10px;background:var(--card);border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;font-size:12px}
.listing-detail .drow{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)}
.listing-detail .drow:last-child{border-bottom:none}
.listing-detail .drow span{color:var(--muted)}
.listing-detail .drow b{font-weight:600;text-align:right}
#chat-wrap{position:fixed;top:var(--hdr);left:0;right:0;bottom:var(--nav);z-index:100;display:none;flex-direction:column;background:var(--bg)}
#chat-wrap.active{display:flex}
#msgs{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;padding:12px 16px;display:flex;flex-direction:column;gap:10px;min-height:0}
.bubble{max-width:82%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;word-break:break-word}
.bubble.user{align-self:flex-end;background:var(--gold);color:#0D1B2A;border-bottom-right-radius:4px}
.bubble.bot{align-self:flex-start;background:var(--card);border:1px solid var(--border);border-bottom-left-radius:4px;white-space:pre-wrap}
.bubble.typing{color:var(--muted);font-style:italic}
.chips{display:flex;gap:8px;overflow-x:auto;padding:8px 16px;scrollbar-width:none;flex-shrink:0;border-top:1px solid var(--border)}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:7px 14px;border-radius:20px;border:1px solid var(--border);background:var(--card);color:var(--muted);font-size:12px;cursor:pointer;white-space:nowrap}
.chip:active{border-color:var(--gold);color:var(--gold)}
.input-row{display:flex;gap:8px;padding:10px 16px;border-top:1px solid var(--border);background:var(--bg);flex-shrink:0}
#msg-input{flex:1;background:var(--card);border:1px solid var(--border);border-radius:22px;padding:10px 16px;color:var(--text);font-size:15px;outline:none}
#msg-input:focus{border-color:var(--gold)}
#send-btn{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#send-btn svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#speak-btn{width:40px;height:40px;border-radius:50%;background:var(--card);border:1px solid var(--border);cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:18px;transition:background .15s,border-color .15s}
#speak-btn.on{background:var(--gold);border-color:var(--gold)}
.spinner{display:block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:spin .7s linear infinite;margin:40px auto}
@keyframes spin{to{transform:rotate(360deg)}}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}
.star{color:var(--gold)}
#fab-top{position:fixed;bottom:calc(var(--nav) + 16px);right:16px;width:46px;height:46px;border-radius:50%;background:var(--gold);color:#0D1B2A;border:none;font-size:20px;font-weight:700;cursor:pointer;display:none;align-items:center;justify-content:center;box-shadow:0 4px 16px rgba(0,0,0,.55);z-index:150;line-height:1}
#fab-top.visible{display:flex}
.sug-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
.sug-card .sug-p{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:10px;border:1px solid currentColor;display:inline-block}
.sug-card .sug-title{font-size:14px;font-weight:600;margin:7px 0 4px;line-height:1.35}
.sug-card .sug-detail{font-size:12px;color:var(--muted);line-height:1.45}
.sug-card .sug-action{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.sug-card .sug-impact{font-size:11px;color:var(--muted);margin-top:5px}
.ceo-btn{width:100%;background:linear-gradient(135deg,var(--card) 0%,#1a2440 100%);border:1px solid var(--gold);color:var(--gold);border-radius:12px;padding:14px;font-size:14px;font-weight:600;cursor:pointer;display:flex;align-items:center;justify-content:center;gap:8px;margin-top:4px}
.collapse-btn{display:block;width:100%;text-align:center;padding:7px;background:none;border:1px solid var(--border);border-radius:8px;color:var(--muted);font-size:12px;cursor:pointer;margin:6px 0 10px;transition:all .15s}
.collapse-btn:active{border-color:var(--gold);color:var(--gold)}
.hub-section-btn{flex:1;background:var(--card);border:1px solid var(--border);border-radius:10px;padding:10px 8px;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;transition:all .15s;text-align:center}
.hub-section-btn.active{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.swatch{display:inline-block;width:16px;height:16px;border-radius:4px;vertical-align:middle;margin-right:4px;flex-shrink:0;border:1px solid rgba(255,255,255,.15)}
.cred-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border)}
.cred-row:last-child{border-bottom:none}
.cred-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}
.posture-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.posture-row:last-child{border-bottom:none}
.prod-card{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:13px 14px;margin-bottom:10px}
</style>
</head>
<body>
  <header>
    <h1>""" + business_config.BUSINESS_NAME + """</h1>
    <div style="text-align:right;line-height:1.4">
      <span id="hdr-sub">Dashboard</span>
      <div style="font-size:9px;color:var(--border);margin-top:1px">""" + _BUILD_ID + """</div>
    </div>
  </header>

  <div id="persist-banner" style="display:none;position:fixed;top:0;left:0;right:0;z-index:300;background:#3a1414;border-bottom:1px solid var(--red);color:#ffb3b3;font-size:12px;font-weight:600;padding:8px 14px;text-align:center">
    ⚠️ No durable storage attached — data and synced files will be lost on next redeploy. Attach a Railway Volume at /data.
  </div>

  <div id="screen-dash" class="screen active">
    <div class="card" id="todo-card" style="margin-bottom:14px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
        <div style="font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">📋 To-Do — Scott + Frank</div>
        <span id="todo-count" style="font-size:11px;color:var(--gold);font-weight:600"></span>
      </div>
      <div id="todo-list"><div class="spinner" style="margin:10px auto"></div></div>
      <div style="display:flex;gap:6px;margin-top:10px">
        <input id="todo-input" type="text" placeholder="Add a to-do…" onkeydown="if(event.key==='Enter')addTodoItem()"
          style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:9px 12px;font-size:13px;color:var(--text)">
        <button onclick="addTodoItem()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer">Add</button>
      </div>
    </div>
    <div style="margin-bottom:8px">
      <button id="ceo-analyze-btn" class="ceo-btn" onclick="getCeoSuggestions(false)" style="display:none">
        <span>🎯</span><span>Ask """ + business_config.AGENT_NAME + """ to Analyze</span>
      </button>
      <div id="ceo-suggestions"><div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">""" + business_config.AGENT_NAME + """ is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div></div>
    </div>
    <div id="dash-content"><div class="spinner"></div></div>
    <div id="conv-doctor-wrap" style="margin-top:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin:16px 0 8px">
        <div style="font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px">🩺 Conversion Doctor</div>
        <button id="conv-collapse-btn" onclick="toggleConvPanel(this)" style="font-size:11px;color:var(--muted);background:none;border:1px solid var(--border);border-radius:8px;padding:4px 10px;cursor:pointer">▼ Show</button>
      </div>
      <div id="conv-doctor" style="display:none"></div>
    </div>
  </div>

  <div id="screen-actions" class="screen">
    <div style="display:flex;gap:8px;margin-bottom:14px">
      <button id="batch-tag-btn" onclick="batchStageTags(this)" style="flex:1;background:var(--card);border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:center">⚡ Stage All Tag Fixes</button>
    </div>
    <div id="actions-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-listings" class="screen">
    <div class="toggle-row">
      <button class="toggle-btn active" onclick="loadListings('active',this)">Active</button>
      <button class="toggle-btn" onclick="loadListings('draft',this)">Drafts</button>
    </div>
    <div id="listings-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-analytics" class="screen">
    <div class="toggle-row" id="analytics-period-row">
      <button class="toggle-btn" onclick="loadAnalytics(7,this)">7 Days</button>
      <button class="toggle-btn active" onclick="loadAnalytics(30,this)">30 Days</button>
      <button class="toggle-btn" onclick="loadAnalytics(90,this)">90 Days</button>
    </div>
    <div id="analytics-content"><div class="spinner"></div></div>
  </div>

  <div id="screen-hub" class="screen">
    <div style="display:flex;gap:6px;margin-bottom:14px">
      <button class="hub-section-btn active" onclick="showHubSection(&apos;brand&apos;,this)">🎨 Brand</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;products&apos;,this)">📦 Products</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;files&apos;,this)">📁 Files</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;studio&apos;,this)">🎬 Studio</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;creds&apos;,this)">🔑 Creds</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;security&apos;,this)">🛡️ Security</button>
      <button class="hub-section-btn" onclick="showHubSection(&apos;relay&apos;,this)">🔌 Relay</button>
    </div>
    <div id="hub-content"><div class="spinner"></div></div>
  </div>

  <div id="chat-wrap">
    <div id="msgs"></div>
    <div class="chips">
      <span class="chip" onclick="sendChip(this)">What should I focus on?</span>
      <span class="chip" onclick="sendChip(this)">How are sales?</span>
      <span class="chip" onclick="sendChip(this)">What's my next listing?</span>
      <span class="chip" onclick="sendChip(this)">Pricing advice</span>
      <span class="chip" onclick="sendChip(this)">SEO tips</span>
    </div>
    <div class="input-row">
      <button id="speak-btn" onclick="toggleSpeak()" title="Toggle voice — Frank speaks replies aloud">🔇</button>
      <input id="msg-input" type="text" placeholder="Ask """ + business_config.AGENT_NAME + """…" autocomplete="off">
      <button id="send-btn" onclick="sendMsg()">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
  </div>

  <button id="fab-top" aria-label="Back to top">↑</button>

  <nav>
    <button class="active" onclick="showTab('dash',this)">
      <svg viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></svg>
      Dash
    </button>
    <button onclick="showTab('actions',this)">
      <svg viewBox="0 0 24 24"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg><span id="nav-badge" class="nav-badge" style="display:none">0</span>
      Actions
    </button>
    <button onclick="showTab('analytics',this)">
      <svg viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>
      Analytics
    </button>
    <button onclick="showTab('chat',this)">
      <svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      Chat
    </button>
    <button onclick="showTab('listings',this)">
      <svg viewBox="0 0 24 24"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
      Listings
    </button>
    <button onclick="showTab('hub',this)">
      <svg viewBox="0 0 24 24"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
      Hub
    </button>
  </nav>

<script>
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
const TOKEN = '';  // kept for call-site compatibility; fetchWithTimeout strips auth headers

let ws = null, wsReady = false, pendingMsg = null;
let _wsHeartbeat = null, _wsReconnectTimer = null, _wsRetries = 0, _wsManualClose = false;
// Stable per-device chat session so Frank's memory survives reconnects & reloads.
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
let _analyticsDays = 30;
let _onListings = false;

function showTab(tab, btn) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  document.getElementById('chat-wrap').classList.remove('active');
  btn.classList.add('active');
  document.getElementById('hdr-sub').textContent = {dash:'Dashboard',actions:'Action Center',analytics:'Analytics',chat:'Chat',listings:'Listings',hub:'Hub'}[tab];
  _onListings = (tab === 'listings');
  if (!_onListings) { const fab=document.getElementById('fab-top'); if(fab)fab.classList.remove('visible'); }
  if (tab === 'chat') {
    document.getElementById('chat-wrap').classList.add('active');
    if (!ws) initWS();
  } else {
    document.getElementById('screen-' + tab).classList.add('active');
    if (tab === 'listings') loadListings('active', document.querySelector('.toggle-btn'));
    if (tab === 'actions') loadActions();
    if (tab === 'analytics') loadAnalytics(_analyticsDays);
    if (tab === 'hub') loadHub();
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function escHtml(s){return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');}
function fetchWithTimeout(url, opts, ms=12000){
  const c=new AbortController();
  const t=setTimeout(()=>c.abort(),ms);
  // Strip explicit Authorization headers — session cookie is sent automatically
  // by the browser (credentials:'same-origin'). This keeps the APP_SECRET_TOKEN
  // out of the page source while still authenticating every request.
  const {headers:h, ...rest} = opts || {};
  const filtered = {};
  if (h) Object.entries(h).forEach(([k,v])=>{ if(k.toLowerCase()!=='authorization') filtered[k]=v; });
  return fetch(url,{...rest, headers:filtered, credentials:'same-origin', signal:c.signal}).finally(()=>clearTimeout(t));
}

// ── Shared To-Do (Scott + Frank) ────────────────────────────────────────────
async function loadTodos(){
  try {
    const r = await fetchWithTimeout(BASE+'/api/todos', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const d = await r.json();
    renderTodos(d.todos || []);
  } catch(e) {
    document.getElementById('todo-list').innerHTML = '<div style="color:var(--muted);font-size:12px">Could not load to-dos.</div>';
  }
}
function renderTodos(items){
  const wrap = document.getElementById('todo-list');
  const cnt = document.getElementById('todo-count');
  const openN = items.filter(t=>!t.done).length;
  cnt.textContent = items.length ? (openN ? openN+' open' : 'all done ✓') : '';
  if (!items.length) { wrap.innerHTML = '<div style="color:var(--muted);font-size:12px">Nothing on the list yet — add one below.</div>'; return; }
  wrap.innerHTML = items.map(t => {
    const who = t.added_by === 'frank' ? '🤖 Frank' : '🧑 Scott';
    return '<div style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;border-bottom:1px solid var(--border)'+(t.done?';opacity:.5':'')+'">'+
      '<input type="checkbox" '+(t.done?'checked':'')+' onchange="toggleTodoItem('+t.id+',this.checked)" style="margin-top:3px;flex-shrink:0;width:16px;height:16px;accent-color:var(--gold)">'+
      '<div style="flex:1;font-size:13px;color:var(--text)'+(t.done?';text-decoration:line-through':'')+'">'+escHtml(t.text)+
        '<div style="font-size:10px;color:var(--muted);margin-top:2px">'+who+'</div></div>'+
      '<button onclick="deleteTodoItem('+t.id+')" style="background:none;border:none;color:var(--muted);font-size:14px;cursor:pointer;padding:2px 4px">✕</button>'+
    '</div>';
  }).join('');
}
async function addTodoItem(){
  const inp = document.getElementById('todo-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  try {
    await fetchWithTimeout(BASE+'/api/todos', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({text, added_by:'scott'}),
    }, 15000);
  } catch(e) {}
  loadTodos();
}
async function toggleTodoItem(id, done){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id+'/toggle', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({done}),
    }, 15000);
  } catch(e) {}
  loadTodos();
}
async function deleteTodoItem(id){
  try {
    await fetchWithTimeout(BASE+'/api/todos/'+id, {method:'DELETE',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) {}
  loadTodos();
}

// ── Action Center ────────────────────────────────────────────────────────────
let _actions = [];
let _pendingActions = [];
let _actionsSummary = {high:0,medium:0,low:0};
let _actionFilter = null; // 'high' | 'medium' | 'low' | null (= all)
function setActionBadge(summary, pending) {
  const b = document.getElementById('nav-badge');
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
      if (bl !== undefined) html += `<div style="color:#7a8a9a">&nbsp;&nbsp;${escHtml(bl)}</div>`;
    } else {
      if (bl !== undefined) html += `<div style="color:#e05555">-&nbsp;${escHtml(bl)}</div>`;
      if (al !== undefined) html += `<div style="color:#4ade80">+&nbsp;${escHtml(al)}</div>`;
    }
  }
  return html;
}
function renderApproval(a) {
  const p = a.payload || {};
  let preview = '';
  if (a.type === 'update_title') preview = 'New title: ' + escHtml(p.title || '');
  else if (a.type === 'update_tags') preview = 'New tags: ' + escHtml((p.tags || []).join(', '));
  else if (a.type === 'publish_listing') {
    const pv = p.preview || {};
    preview = `<div style="display:flex;gap:10px;align-items:flex-start">` +
      (pv.thumbnail_url
        ? `<img class="thumb" src="${escHtml(pv.thumbnail_url)}" loading="lazy" style="width:70px;height:70px;border-radius:8px;object-fit:cover;flex-shrink:0">`
        : `<div class="thumb-placeholder" style="width:70px;height:70px;flex-shrink:0">🏷️</div>`) +
      `<div><div>Publish draft listing ${escHtml(String(p.listing_id || ''))}</div>` +
      (pv.title ? `<div style="font-weight:600;margin-top:4px">${escHtml(pv.title)}</div>` : '') +
      (pv.price != null ? `<div>$${escHtml(String(pv.price))} · ${(pv.tags || []).length} tags · ${pv.photo_count || 0} photos</div>` : '') +
      (pv.error ? `<div style="color:#C9A84C">⚠️ Preview unavailable: ${escHtml(pv.error)}</div>` : '') +
      `</div></div>`;
  }
  else if (a.type === 'local_write_file') {
    const diffHtml = simpleLineDiff(p.before, p.after);
    preview = `<div style="margin-bottom:6px"><strong>File:</strong> ${escHtml(p.path || '')}</div>` +
      (p.before_existed === false ? `<div style="color:#C9A84C;margin-bottom:6px">⚠️ File does not currently exist — this will create it.</div>` : '') +
      `<div style="max-height:260px;overflow:auto;background:#0a1420;border-radius:8px;padding:8px;font-family:monospace;font-size:12px;white-space:pre-wrap">${diffHtml || '<span style="color:#7a8a9a">No changes</span>'}</div>`;
  }
  else if (a.type === 'local_delete') {
    preview = `<div style="color:#e05555">⚠️ This will permanently delete:</div><div style="font-family:monospace;margin-top:4px">${escHtml(p.path || '')}</div>`;
  }
  else if (a.type === 'local_exec') {
    preview = `<div><strong>Run:</strong> <span style="font-family:monospace">${escHtml(p.command || '')}${p.extra_args ? ' ' + escHtml(p.extra_args) : ''}</span></div>`;
  }
  return `<div class="act-card approval">
    <span class="act-sev approval">awaiting you</span>
    <div class="act-title">${escHtml(a.summary || a.type)}</div>
    <div class="act-detail">${preview}</div>
    <div class="act-btns">
      <button class="act-btn approve" onclick="approveAction(${a.id})">Approve &amp; Apply</button>
      ${a.type === 'publish_listing' ? `<button class="act-btn" onclick="fixDraftStage(${(p.listing_id||0)},${a.id},this)">🤖 Fix Draft</button>` : ''}
      <button class="act-btn reject" onclick="rejectAction(${a.id})">Reject</button>
    </div>
  </div>`;
}
const _APPROVE_CONFIRM_MSGS = {
  local_write_file: 'Approve and write this file on your computer now?',
  local_delete: 'Approve and PERMANENTLY DELETE this file on your computer now?',
  local_exec: 'Approve and run this command on your computer now?'
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
  } catch(e) { alert('Could not apply: ' + (e.message||e)); }
}
async function rejectAction(id) {
  try {
    const r = await fetchWithTimeout(BASE+'/api/queue/'+id+'/reject', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    if (!r.ok) { const d = await r.json().catch(()=>({})); throw new Error(d.detail||'HTTP '+r.status); }
    loadActions();
  } catch(e) { alert('Could not reject: ' + (e.message||e)); }
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
    const errNote = (d.errors&&d.errors.length) ? '\\n\\nErrors: '+d.errors.join(', ') : '';
    alert('Staged '+n+' fix'+(n!==1?'es':'')+'.\\nApprove the new fixes in Action Center, then come back to approve Publish.'+errNote);
    loadActions();
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not fix draft: '+(e.message||e));
  }
}
async function loadActions() {
  const el = document.getElementById('actions-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const [ar, qr] = await Promise.all([
      fetchWithTimeout(BASE+'/api/actions', {headers:{Authorization:'Bearer '+TOKEN}}, 25000),
      fetchWithTimeout(BASE+'/api/queue?status=pending', {headers:{Authorization:'Bearer '+TOKEN}}, 15000).catch(()=>null)
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
const _SEV_COLORS = {high:'#e05555', medium:'#C9A84C', low:'#7ba0c2'};
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
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash, actions, analytics, chat, listings
  showTab('chat', chatBtn);
  const q = 'How should I fix this? ' + a.title + ' — ' + a.detail;
  const inp = document.getElementById('msg-input');
  inp.value = q;
  sendMsg();
}

// ── Dashboard ──────────────────────────────────────────────────────────────
function _dashSkeleton() {
  const hr = new Date().getHours();
  const greet = hr<12?'Good morning':hr<17?'Good afternoon':'Good evening';
  const ds = new Date().toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});
  return `<div style="margin-bottom:16px"><div style="font-size:22px;font-weight:700">${greet}, Scott 👋</div><div style="color:var(--muted);font-size:13px;margin-top:4px">${ds}</div></div><div id="dash-err"></div><div class="section-title">Revenue</div><div class="card-row"><div class="metric gold"><div class="label">7-Day</div><div class="value" id="v-rev7">…</div><div class="sub" id="s-rev7">loading</div></div><div class="metric gold"><div class="label">30-Day</div><div class="value" id="v-rev30">…</div><div class="sub" id="s-rev30">loading</div></div></div><div class="section-title">Shop</div><div class="card-row"><div class="metric"><div class="label">Active</div><div class="value" id="v-active">…</div><div class="sub">listings</div></div><div class="metric"><div class="label">All-Time</div><div class="value" id="v-sales">…</div><div class="sub">sales</div></div></div><div id="m-reviews"></div><div id="dash-retry" style="display:none;text-align:center;margin-top:8px"><button onclick="fetchDashData()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
}
async function fetchDashData() {
  const setId = (id,val)=>{const e=document.getElementById(id);if(e)e.textContent=val;};
  const setErr = msg=>{const e=document.getElementById('dash-err');if(e)e.innerHTML=msg?`<div style="background:#2d1a1a;border:1px solid #5a2d2d;border-radius:10px;padding:10px 14px;margin-bottom:12px;font-size:12px;color:#e07070">${msg}</div>`:''};
  const showRetry = v=>{const r=document.getElementById('dash-retry');if(r)r.style.display=v?'':'none';};
  try {
    const r = await fetchWithTimeout(BASE+'/api/metrics',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    if (!r.ok){const err=await r.json().catch(()=>({}));throw new Error(err.detail||'HTTP '+r.status);}
    const d = await r.json();
    const o=d.orders||{},l=d.listings||{},rev=d.reviews||{},sh=d.shop||{};
    if(o.error||sh.error){setErr('⚠️ Etsy data partially unavailable');showRetry(true);}else{setErr('');showRetry(false);}
    setId('v-rev7','$'+(o.revenue_7d||0).toFixed(2));setId('s-rev7',(o.last_7_days||0)+' orders');
    setId('v-rev30','$'+(o.revenue_30d||0).toFixed(2));setId('s-rev30',(o.last_30_days||0)+' orders');
    setId('v-active',sh.active_listing_count||l.active_count||0);setId('v-sales',sh.total_sales||0);
    if(rev.avg_rating){const rEl=document.getElementById('m-reviews');if(rEl)rEl.innerHTML=`<div class="section-title">Reviews</div><div class="card"><div style="display:flex;align-items:center;gap:12px"><div style="font-size:36px;font-weight:700;color:var(--gold)">${rev.avg_rating}</div><div><div class="star">${'★'.repeat(Math.round(rev.avg_rating))}${'☆'.repeat(5-Math.round(rev.avg_rating))}</div><div style="font-size:12px;color:var(--muted);margin-top:3px">${rev.total_count||0} reviews · ${rev.five_star_pct||0}% five-star</div></div></div></div>`;}
  } catch(e) {
    setErr('⚠️ '+(e.name==='AbortError'?'Request timed out — check connection':escHtml(e.message||'Failed to load')));
    setId('v-rev7','—');setId('s-rev7','');setId('v-rev30','—');setId('s-rev30','');
    setId('v-active','—');setId('v-sales','—');
    showRetry(true);
  }
}
function loadDash() {
  document.getElementById('dash-content').innerHTML = _dashSkeleton();
  fetchDashData();
  getCeoSuggestions(false);
}

// ── Listings ───────────────────────────────────────────────────────────────
let _lastState = 'active';
let _listings = [];
let _listingState = 'active';
let _sectionFilter = null; // null = all categories
let _sectionsMap = null;   // {shop_section_id: title}, fetched once and cached client-side
let _openDetailId = null;
async function _ensureSectionsLoaded() {
  if (_sectionsMap) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/shop-sections', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const d = await r.json();
    _sectionsMap = {};
    (d.sections||[]).forEach(s => { _sectionsMap[s.shop_section_id] = s.title; });
  } catch(e) { _sectionsMap = {}; }
}
function _sectionLabel(id) {
  if (!id) return 'Uncategorized';
  return (_sectionsMap && _sectionsMap[id]) || ('Section '+id);
}
async function loadListings(state, btn) {
  if (btn) { document.querySelectorAll('.toggle-btn').forEach(b=>b.classList.remove('active')); btn.classList.add('active'); }
  _lastState = state; _listingState = state; _sectionFilter = null; _openDetailId = null;
  const el = document.getElementById('listings-content');
  el.innerHTML = '<div class="spinner"></div>';
  try {
    await _ensureSectionsLoaded();
    const r = await fetchWithTimeout(BASE+'/api/listings?state='+state, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { const err = await r.json().catch(()=>({})); throw new Error(err.detail||'HTTP '+r.status); }
    const d = await r.json();
    _listings = d.listings || [];
    renderListings();
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastState)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setSectionFilter(key) {
  _sectionFilter = key;
  _openDetailId = null;
  renderListings();
}
function renderListings() {
  const el = document.getElementById('listings-content');
  if (!_listings.length) { el.innerHTML = '<div class="empty">No '+_listingState+' listings</div>'; return; }
  const seen = {}; const cats = [];
  _listings.forEach(l => {
    const key = String(l.shop_section_id || 'none');
    if (!seen[key]) { seen[key] = true; cats.push({key: key, label: _sectionLabel(l.shop_section_id)}); }
  });
  cats.sort((a,b) => a.label.localeCompare(b.label));
  let html = '';
  if (cats.length > 1) {
    html += '<div class="chip-row">';
    html += `<button class="chip-btn${_sectionFilter===null?' active':''}" onclick="setSectionFilter(null)">All (${_listings.length})</button>`;
    cats.forEach(c => {
      const n = _listings.filter(l => String(l.shop_section_id||'none')===c.key).length;
      html += `<button class="chip-btn${_sectionFilter===c.key?' active':''}" onclick="setSectionFilter('${c.key}')">${escHtml(c.label)} (${n})</button>`;
    });
    html += '</div>';
  }
  const filtered = _sectionFilter===null ? _listings : _listings.filter(l => String(l.shop_section_id||'none')===_sectionFilter);
  if (!filtered.length) { html += '<div class="empty">No listings in this category</div>'; el.innerHTML = html; return; }
  html += filtered.map(l => `
    <div class="listing-item" style="cursor:pointer" onclick="toggleListingDetail(${l.listing_id})">
      ${l.thumbnail_url ? `<img class="thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy">` : `<div class="thumb-placeholder">🏷️</div>`}
      <div class="listing-info">
        <div class="listing-title">${escHtml(l.title)}</div>
        <div class="listing-meta">${l.views} views · ${l.num_favorers} ♥${l.sales!=null?' · '+l.sales+' sold':''}<span id="badge-${l.listing_id}" class="badge ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
      </div>
      <div class="listing-price">$${(+l.price||0).toFixed(2)}</div>
    </div>
    <div id="detail-${l.listing_id}" class="listing-detail" style="display:none"></div>`).join('');
  el.innerHTML = html;
}
async function toggleListingDetail(listingId) {
  const panel = document.getElementById('detail-'+listingId);
  if (!panel) return;
  if (_openDetailId !== null && _openDetailId !== listingId) {
    const prev = document.getElementById('detail-'+_openDetailId);
    if (prev) prev.style.display = 'none';
  }
  if (_openDetailId === listingId) { panel.style.display = 'none'; _openDetailId = null; return; }
  const l = _listings.find(x => x.listing_id === listingId);
  if (!l) return;
  panel.style.display = 'block';
  _openDetailId = listingId;
  panel.innerHTML =
    `<div class="drow"><span>Listing ID</span><b>${listingId}</b></div>`+
    `<div class="drow"><span>Category</span><b>${escHtml(_sectionLabel(l.shop_section_id))}</b></div>`+
    `<div class="drow"><span>Views</span><b>${l.views}</b></div>`+
    `<div class="drow"><span>Favorites</span><b>${l.num_favorers}</b></div>`+
    (l.sales!=null ? `<div class="drow"><span>Sold</span><b>${l.sales}</b></div>` : '')+
    (l.conversion_pct!=null ? `<div class="drow"><span>Conversion</span><b>${l.conversion_pct}%</b></div>` : '')+
    `<div class="drow"><span>Price</span><b>$${(+l.price||0).toFixed(2)}</b></div>`+
    `<div id="files-${listingId}"><div class="drow"><span>Digital files</span><b>loading…</b></div></div>`+
    `<div style="margin-top:8px;display:flex;justify-content:flex-end;align-items:center;gap:10px">`+
    ((l.state==='active'||l.state==='inactive') ? `<button id="state-btn-${listingId}" class="act-btn" style="font-size:12px;padding:6px 12px" onclick="event.stopPropagation();toggleListingState(${listingId},this)">${l.state==='active'?'⏸️ Deactivate':'▶️ Activate'}</button>` : '')+
    `<a href="${escHtml(l.url)}" target="_blank" style="color:var(--gold);font-size:12px;text-decoration:none" onclick="event.stopPropagation()">Open on Etsy ↗</a>`+
    `</div>`;
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/files', {headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    const slot = document.getElementById('files-'+listingId);
    if (!slot) return;
    if (!r.ok) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>unavailable</b></div>'; return; }
    const d = await r.json();
    const files = d.files || [];
    if (!files.length) { slot.innerHTML = '<div class="drow"><span>Digital files</span><b>none attached</b></div>'; return; }
    slot.innerHTML = files.map(f => `<div class="drow"><span>📄 ${escHtml(f.filename||'file')}</span><b>${escHtml(f.size_human||'')}</b></div>`).join('');
  } catch(e) {
    const slot = document.getElementById('files-'+listingId);
    if (slot) slot.innerHTML = '<div class="drow"><span>Digital files</span><b>failed to load</b></div>';
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
    const badge = document.getElementById('badge-'+listingId);
    if (badge) { badge.textContent = l.state; badge.className = 'badge ' + (l.state==='active'?'active':'draft'); }
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not change listing state: ' + (e.message||e));
  }
}

// ── Chat ───────────────────────────────────────────────────────────────────
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
    // Heartbeat keeps the socket warm through mobile carrier/proxy idle timeouts
    // (otherwise an idle socket dies in ~30-60s and the next message hits a dead pipe).
    _stopHeartbeat();
    _wsHeartbeat = setInterval(() => { if (ws && ws.readyState === 1) ws.send(JSON.stringify({type:'ping'})); }, 25000);
    if (pendingMsg) { ws.send(JSON.stringify({message:pendingMsg, session:CHAT_SESSION})); pendingMsg=null; }
  };
  ws.onmessage = e => {
    const d = JSON.parse(e.data);
    if (d.type === 'pong') return;
    const bot = document.getElementById('bot-streaming');
    if (d.type === 'tool' && bot) {
      bot.classList.add('typing');
      if (!bot.dataset.real) bot.textContent = '⚙ ' + d.content;
      scrollMsgs();
    } else if (d.type === 'chunk' && bot) {
      if (!bot.dataset.real) { bot.textContent = ''; bot.dataset.real = '1'; bot.classList.remove('typing'); }
      bot.textContent += d.content; scrollMsgs();
    } else if (d.type === 'speak') {
      _speakCalled = true;
      if (_speakEnabled) speakText(d.text);
    } else if (d.type === 'done') {
      const finalText = bot ? bot.textContent : '';
      _clearStreaming(); scrollMsgs();
      if (_speakEnabled && !_speakCalled && finalText.trim()) speakText(finalText);
      _speakCalled = false;
    } else if (d.type === 'error') {
      _clearStreaming(); addBubble('⚠️ ' + d.content, 'bot');
      _speakCalled = false;
    }
  };
  ws.onerror = () => { _clearStreaming(); };
  ws.onclose = e => {
    wsReady = false; ws = null; _stopHeartbeat();
    _clearStreaming();
    if (e.code === 4001) { addBubble('Auth failed — reload to reconnect', 'bot'); return; }
    // Auto-reconnect with capped backoff. Frank's memory is server-side (keyed by
    // CHAT_SESSION), so reconnecting silently resumes the same thread — no context lost.
    if (!_wsManualClose) {
      _wsRetries = Math.min(_wsRetries + 1, 5);
      const delay = Math.min(1000 * Math.pow(2, _wsRetries - 1), 15000);
      _wsReconnectTimer = setTimeout(() => { if (!ws) initWS(); }, delay);
    }
  };
}
function addBubble(text, who) {
  const el = document.createElement('div');
  el.className = 'bubble ' + who;
  el.textContent = text;
  document.getElementById('msgs').appendChild(el);
  scrollMsgs();
  return el;
}
function scrollMsgs() { const m=document.getElementById('msgs'); m.scrollTop=m.scrollHeight; }
function sendMsg() {
  const inp = document.getElementById('msg-input');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  _speakCalled = false;
  addBubble(text, 'user');
  const bot = addBubble('', 'bot typing');
  bot.id = 'bot-streaming';
  bot.textContent = '';
  if (wsReady) { ws.send(JSON.stringify({message:text})); }
  else { pendingMsg = text; if(!ws) initWS(); }
}
function sendChip(el) { document.getElementById('msg-input').value = el.textContent; sendMsg(); }
document.getElementById('msg-input').addEventListener('keydown', e => { if(e.key==='Enter') sendMsg(); });

// ── Voice speak-back ────────────────────────────────────────────────────────
let _speakEnabled = (localStorage.getItem('frankSpeak') === '1');
let _speakCalled = false;  // true if local_speak tool fired this turn (avoid double-speak)
(function _initSpeakBtn() {
  const btn = document.getElementById('speak-btn');
  if (!btn) return;
  if (_speakEnabled) { btn.classList.add('on'); btn.textContent = '🔊'; }
})();
function toggleSpeak() {
  _speakEnabled = !_speakEnabled;
  localStorage.setItem('frankSpeak', _speakEnabled ? '1' : '0');
  const btn = document.getElementById('speak-btn');
  if (btn) { btn.classList.toggle('on', _speakEnabled); btn.textContent = _speakEnabled ? '🔊' : '🔇'; }
}
async function speakText(text) {
  if (!text || !text.trim()) return;
  try {
    const r = await fetch(BASE+'/api/voice/speak', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({text: text.slice(0, 4000)})
    });
    if (!r.ok) return;
    const blob = await r.blob();
    const url = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.onended = () => URL.revokeObjectURL(url);
    audio.play().catch(() => {});
  } catch(e) { /* best effort — audio is non-critical */ }
}

// ── Studio (video generation) ──────────────────────────────────────────────
async function loadStudio() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var genFormHtml = '<div class="card" style="margin-bottom:12px">'+
    '<div style="font-size:14px;font-weight:700;margin-bottom:10px">Generate Marketing Video</div>'+
    '<div style="font-size:12px;color:var(--muted);margin-bottom:10px">Ken Burns slideshow from a listing\'s photos — generates an MP4 ready for social media.</div>'+
    '<div style="display:flex;flex-direction:column;gap:8px">'+
    '<input id="studio-listing-id" type="number" placeholder="Etsy Listing ID" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
    '<select id="studio-style" style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
    '<option value="showcase">Showcase — smooth pan across listing photos</option>'+
    '<option value="new-drop">New Drop — bold title card reveal</option>'+
    '<option value="feature">Feature — close-up detail focus</option>'+
    '<option value="minimal">Minimal — clean, quiet aesthetic</option>'+
    '</select>'+
    '<button onclick="studioGenerate(this)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:12px;font-size:14px;font-weight:700;cursor:pointer">Generate Video</button>'+
    '</div></div>';
  el.innerHTML = genFormHtml + '<div id="studio-result"></div><div id="studio-videos"></div>';
  loadStudioVideos();
}
async function studioGenerate(btn) {
  var listingId = document.getElementById('studio-listing-id').value.trim();
  var style = document.getElementById('studio-style').value;
  var out = document.getElementById('studio-result');
  if (!listingId) { alert('Enter a listing ID first'); return; }
  btn.disabled = true;
  btn.textContent = '⏳ Generating — takes ~30s…';
  out.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/studio/generate', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({listing_id: parseInt(listingId), style})
    }, 200000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var vidUrl = BASE+'/api/files/download?root=videos&path='+encodeURIComponent(d.path)+'&inline=1';
    out.innerHTML = '<div class="card" style="margin-bottom:12px">'+
      '<div style="font-size:13px;font-weight:700;color:var(--green);margin-bottom:8px">✅ Video ready — '+escHtml(d.size_human)+'</div>'+
      '<video controls style="width:100%;border-radius:8px;background:#000" src="'+escHtml(vidUrl)+'"></video>'+
      '<a href="'+escHtml(vidUrl)+'" download="'+escHtml(d.path)+'" style="display:block;text-align:center;margin-top:8px;color:var(--gold);font-size:13px;font-weight:600">⬇ Download MP4</a>'+
      '</div>';
    loadStudioVideos();
  } catch(e) {
    out.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out — try again':e.message||'Generation failed')+'</div>';
  } finally {
    btn.disabled = false;
    btn.textContent = 'Generate Video';
  }
}
async function loadStudioVideos() {
  var el = document.getElementById('studio-videos');
  if (!el) return;
  try {
    var r = await fetchWithTimeout(BASE+'/api/studio/videos',{headers:{Authorization:'Bearer '+TOKEN}},10000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok || !d.videos || !d.videos.length) { el.innerHTML = ''; return; }
    var html = '<div class="section-title">Previously Generated ('+d.videos.length+')</div><div class="card">';
    d.videos.forEach(function(v){
      var vidUrl = BASE+'/api/files/download?root=videos&path='+encodeURIComponent(v.name)+'&inline=1';
      html += '<div class="listing-item" style="cursor:default">'+
        '<div class="thumb-placeholder">🎬</div>'+
        '<div class="listing-info">'+
          '<div class="listing-title" style="font-size:13px">'+escHtml(v.name)+'</div>'+
          '<div class="listing-meta">'+escHtml(v.size_human)+'</div>'+
        '</div>'+
        '<a href="'+escHtml(vidUrl)+'" target="_blank" style="color:var(--gold);font-size:18px;text-decoration:none">↗</a>'+
      '</div>';
    });
    html += '</div>';
    el.innerHTML = html;
  } catch(e) { /* non-critical */ }
}

// ── Analytics ──────────────────────────────────────────────────────────────
function buildSparkline(values, color, h) {
  h = h || 64;
  values = (values || []).filter(function(v){ return v != null && !isNaN(v); });
  if (values.length < 2) return '<div style="height:'+h+'px;display:flex;align-items:center;justify-content:center;color:var(--muted);font-size:12px">📈 Accumulating daily data…</div>';
  var W=320,H=h,mn=Math.min.apply(null,values),mx=Math.max.apply(null,values),range=mx-mn||1,pad=4;
  var pts=values.map(function(v,i){return [pad+(i/(values.length-1))*(W-pad*2), H-pad-((v-mn)/range)*(H-pad*2)];});
  var poly=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
  var area='M'+pts[0][0].toFixed(1)+','+H+' '+pts.map(function(p){return 'L'+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ')+' L'+pts[pts.length-1][0].toFixed(1)+','+H+' Z';
  var gid='sg'+Math.random().toString(36).slice(2,8);
  return '<svg viewBox="0 0 '+W+' '+H+'" style="width:100%;height:'+H+'px;display:block;overflow:visible">'+
    '<defs><linearGradient id="'+gid+'" x1="0" y1="0" x2="0" y2="1">'+
    '<stop offset="0%" stop-color="'+color+'" stop-opacity="0.25"/>'+
    '<stop offset="100%" stop-color="'+color+'" stop-opacity="0"/>'+
    '</linearGradient></defs>'+
    '<path d="'+area+'" fill="url(#'+gid+')"/>'+
    '<polyline points="'+poly+'" fill="none" stroke="'+color+'" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'+
    '<circle cx="'+pts[pts.length-1][0].toFixed(1)+'" cy="'+pts[pts.length-1][1].toFixed(1)+'" r="3.5" fill="'+color+'"/>'+
    '</svg>';
}
function _deltaSpan(val, isMoney) {
  if (val == null || val === 0) return '<span style="color:var(--muted)">— stable</span>';
  var pos=val>0, c=pos?'var(--green)':'var(--red)', a=pos?'↑':'↓';
  var n=isMoney?('$'+Math.abs(val).toFixed(2)):String(Math.round(Math.abs(val)));
  return '<span style="color:'+c+'">'+a+' '+n+'</span>';
}
function _renderAnalytics(d) {
  var tr=d.trends||{}, lt=d.latest||{}, del=d.delta||{}, days=d.days||30;
  var n=d.snapshot_count||0, top=d.top_listings||[];
  var html='';
  if (n < 3) {
    html+='<div style="background:#1a2030;border:1px solid #2a3d5a;border-radius:10px;padding:11px 14px;margin-bottom:14px;font-size:12px;color:#7ba0c2">📅 '+(n===0?'No snapshots yet — the hub records one daily snapshot at startup and midnight.':n+' day'+(n>1?'s':'')+' of history recorded. Trend charts fill in each day automatically.')+'</div>';
  }
  // Revenue
  var rev=lt.revenue_30d;
  html+='<div class="section-title">Revenue — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.revenue_30d,'var(--gold)');
  if (rev!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:var(--gold)">$'+rev.toFixed(2)+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">current 30-day window</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.revenue_30d,true)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Orders
  var ord=lt.orders_30d;
  html+='<div class="section-title">Orders — Rolling 30 Days</div><div class="card">';
  html+=buildSparkline(tr.orders_30d,'#5ca8d4');
  if (ord!=null) {
    html+='<div style="margin-top:10px;display:flex;justify-content:space-between;align-items:flex-end">'+
      '<div><div style="font-size:26px;font-weight:700;color:#5ca8d4">'+ord+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:2px">orders in rolling 30 days</div></div>'+
      '<div style="text-align:right;font-size:12px">'+_deltaSpan(del.orders_30d,false)+'<div style="color:var(--muted);font-size:10px;margin-top:2px">vs '+days+'d ago</div></div>'+
      '</div>';
  }
  html+='</div>';
  // Shop growth cards
  var acNow=lt.active_listings, salNow=lt.total_sales;
  if (acNow!=null||salNow!=null) {
    html+='<div class="section-title">Shop Growth</div><div class="card-row">';
    if (acNow!=null) html+='<div class="metric"><div class="label">Listings</div><div class="value">'+acNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.active_listings,false)+' in '+days+'d</div></div>';
    if (salNow!=null) html+='<div class="metric"><div class="label">Total Sales</div><div class="value">'+salNow+'</div><div class="sub" style="margin-top:5px;font-size:11px">'+_deltaSpan(del.total_sales,false)+' in '+days+'d</div></div>';
    html+='</div>';
  }
  // Listing trend mini-sparkline
  var acTrend=(tr.active_listings||[]).filter(function(v){return v!=null;});
  if (acTrend.length>=2) {
    html+='<div class="card" style="padding:12px 14px 10px">'+buildSparkline(tr.active_listings,'var(--green)',40)+'<div style="font-size:11px;color:var(--muted);margin-top:5px">Active listings over time</div></div>';
  }
  // Top listings
  if (top.length) {
    html+='<div class="section-title">Top Listings by Views</div><div class="card" style="padding:12px 14px">';
    html+=top.map(function(l,i){
      // Real buy rate (sales÷views). Etsy avg is ~1-3%; 0% with views = a problem.
      var cp=l.conversion_pct||0, sold=l.sales||0;
      var convColor=cp>=2?'var(--green)':cp>=1?'var(--gold)':sold>0?'#7ba0c2':'var(--red)';
      return '<div class="listing-item" onclick="window.open(&apos;'+escHtml(l.url)+'&apos;,&apos;_blank&apos;)">'+
        '<div style="width:22px;font-size:12px;font-weight:700;color:var(--muted);flex-shrink:0">#'+(i+1)+'</div>'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:'+convColor+'">'+sold+' sold ('+cp+'%)</span></div>'+
        '</div>'+
        '<div class="listing-price">$'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>';
    }).join('');
    html+='</div>';
  } else {
    html+='<div class="section-title">Top Listings</div><div class="empty">View data will appear here once listings are active</div>';
  }
  // Footer
  var ts=lt.ts?new Date(lt.ts).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}):null;
  html+='<div style="text-align:center;color:var(--muted);font-size:11px;padding:12px 0 4px">'+(ts?'Last snapshot: '+ts:'No snapshots yet')+' · '+n+' day'+(n!==1?'s':'')+' of history</div>';
  return html;
}
async function loadAnalytics(days, btn) {
  if (btn) { document.querySelectorAll('#analytics-period-row .toggle-btn').forEach(function(b){b.classList.remove('active');}); btn.classList.add('active'); }
  if (days) _analyticsDays = days;
  var el = document.getElementById('analytics-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/analytics?days='+_analyticsDays, {headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    if (!r.ok) { var e=await r.json().catch(function(){return {};}); throw new Error(e.detail||'HTTP '+r.status); }
    var d = await r.json();
    el.innerHTML = _renderAnalytics(d);
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadAnalytics()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── CEO Analysis (structured suggestion report) ────────────────────────────
let _lastSuggestions = null;

// Silent background refresh — called after showing a cached report so the display
// updates to fresh data without ever showing a spinner. 30s timeout; fails silently.
async function _bgRefreshSuggestions() {
  try {
    var r = await fetchWithTimeout(BASE+'/api/suggestions',{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},30000);
    var d = await r.json().catch(function(){return {};});
    // Only update if we received a real, complete report (not a 202 warming stub)
    if (r.status===200 && d && Array.isArray(d.suggestions) && d.suggestions.length && !d.error) {
      var newer = !_lastSuggestions || (d.generated_at && d.generated_at > (_lastSuggestions.generated_at||''));
      if (newer) {
        _lastSuggestions = d;
        try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
        var el2 = document.getElementById('ceo-suggestions');
        if (el2) { el2.innerHTML = _renderSuggestions(d); updateChips(d); }
      }
    }
  } catch(e) {}
}
const _PCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2'};
const _PRANK  = {critical:0,high:1,medium:2,low:3};
function _renderSuggestions(d) {
  if (!d) return '';
  if (d.raw) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted)">'+escHtml(d.raw)+'</div>';
  const ts = d.generated_at ? new Date(d.generated_at).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'}) : '';
  const score = d.score;
  const scoreColor = score >= 7 ? 'var(--green)' : score >= 4 ? 'var(--gold)' : 'var(--red)';
  const scoreBg = score >= 7 ? '#13241c' : score >= 4 ? '#2d2a1a' : '#241313';
  let html = '<div class="card" style="margin-bottom:10px">';
  html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">';
  html += '<div style="font-size:11px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.4px">CEO Report · ' + ts + '</div>';
  if (score) html += '<div style="background:'+scoreBg+';border:1px solid '+scoreColor+';border-radius:20px;padding:2px 10px;font-size:13px;font-weight:700;color:'+scoreColor+'">'+score+'/10</div>';
  html += '</div>';
  if (d.headline) html += '<div style="font-size:14px;line-height:1.5">'+escHtml(d.headline)+'</div>';
  html += '</div>';
  if (d.top_win || d.top_risk) {
    html += '<div class="card-row">';
    if (d.top_win)  html += '<div class="metric" style="background:#13241c;border-color:#2d5a44"><div class="label" style="color:#5fcf9e">✅ TOP WIN</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_win)+'</div></div>';
    if (d.top_risk) html += '<div class="metric" style="background:#241313;border-color:#5a2d2d"><div class="label" style="color:#e07070">⚠️ TOP RISK</div><div style="font-size:12px;line-height:1.45;margin-top:4px">'+escHtml(d.top_risk)+'</div></div>';
    html += '</div>';
  }
  const sugs = (d.suggestions || []).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  if (sugs.length) {
    html += '<div class="section-title">Priorities</div>';
    sugs.forEach(function(s,i) {
      const pc = _PCOLOR[s.priority] || 'var(--muted)';
      html += '<div class="sug-card" style="border-left-color:'+pc+'">';
      html += '<span class="sug-p" style="color:'+pc+'">'+escHtml(s.priority||'medium')+'</span>';
      if (s.category) html += '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+escHtml(s.category)+'</span>';
      html += '<div class="sug-title">'+escHtml(s.title)+'</div>';
      html += '<div class="sug-detail">'+escHtml(s.detail)+'</div>';
      if (s.action) html += '<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(s.action)+'</div>';
      if (s.impact) html += '<div class="sug-impact">💡 '+escHtml(s.impact)+'</div>';
      html += '<div class="act-btns">';
      if (s.listing_id) html += '<a class="act-btn" href="https://www.etsy.com/listing/'+escHtml(String(s.listing_id))+'" target="_blank">Open Listing</a>';
      html += '<button class="act-btn primary" onclick="askSuggestionFix('+i+')">🤖 Fix It</button>';
      html += '</div></div>';
    });
  }
  html += '<div style="text-align:center;margin:8px 0 4px"><button onclick="getCeoSuggestions(true)" style="background:none;border:1px solid var(--border);border-radius:8px;padding:8px 20px;font-size:12px;color:var(--muted);cursor:pointer">↻ Refresh analysis</button></div>';
  return '<button class="collapse-btn" onclick="toggleCeoPanel(this)">▲ Collapse CEO Analysis</button><div id="ceo-body">'+html+'</div>';
}
function toggleCeoPanel(btn) {
  const el = document.getElementById('ceo-body');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse CEO Analysis' : '▼ Show CEO Analysis';
}
async function getCeoSuggestions(forceRefresh, _attempt) {
  const btn = document.getElementById('ceo-analyze-btn');
  const el  = document.getElementById('ceo-suggestions');
  if (!el) return;
  _attempt = _attempt || 0;
  // Show cached report immediately — no spinner. A silent background fetch
  // checks whether the server has a newer report and updates the display when
  // it arrives. This means the dashboard is instant on every page reload even
  // right after a Railway deploy (which wipes the server-side in-memory cache).
  if (_lastSuggestions && !forceRefresh && !_attempt) {
    if(btn)btn.style.display='none';
    el.innerHTML=_renderSuggestions(_lastSuggestions);
    updateChips(_lastSuggestions);
    setTimeout(_bgRefreshSuggestions, 1500); // silent background check for newer data
    return;
  }
  if (btn) btn.style.display = 'none';
  if (!_attempt) el.innerHTML = '<div class="card" style="text-align:center;padding:28px 16px"><div class="spinner" style="margin:0 auto 14px"></div><div style="color:var(--text);font-size:14px;font-weight:600">""" + business_config.AGENT_NAME + """ is analyzing your shop…</div><div style="color:var(--muted);font-size:12px;margin-top:6px">Pulling metrics · scanning all listings · checking drafts</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/suggestions', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 120000);
    const d = await r.json().catch(function(){return {};});
    // 202 = the report is still being computed (cold cache, e.g. just after an
    // update). Keep the spinner and poll — never block the request for a minute.
    if (r.status === 202 || (d && d.status === 'warming')) {
      if (_attempt >= 25) throw new Error('Analysis is taking longer than usual');
      setTimeout(function(){ getCeoSuggestions(forceRefresh, _attempt + 1); }, 4000);
      return;
    }
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _lastSuggestions = d;
    try { sessionStorage.setItem('obc_sug', JSON.stringify(d)); } catch(e2) {}
    el.innerHTML = _renderSuggestions(d);
    updateChips(d);
  } catch(e) {
    const msg = e.name==='AbortError' ? 'Analysis timed out — try again' : escHtml(e.message||'Failed');
    el.innerHTML = '<div class="empty">'+msg+'</div><div style="text-align:center;margin-top:8px"><button onclick="getCeoSuggestions(true)" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Try Again</button></div>';
    if (btn) btn.style.display = '';
  }
}
function updateChips(data) {
  const el = document.querySelector('.chips');
  if (!el) return;
  const sugs = ((data && data.suggestions) || [])
    .slice()
    .sort(function(a,b){ return (_PRANK[a.priority]||9) - (_PRANK[b.priority]||9); })
    .slice(0, 2);
  const chips = [];
  sugs.forEach(function(s) {
    if (s.title) chips.push('Fix: ' + (s.title.length > 30 ? s.title.slice(0,28)+'…' : s.title));
  });
  const fallbacks = ["What's my next listing?", 'How are sales?', 'Pricing advice', 'SEO tips', 'What should I focus on?'];
  fallbacks.forEach(function(f) { if (chips.length < 5) chips.push(f); });
  el.innerHTML = chips.slice(0, 5).map(function(c) {
    return '<span class="chip" onclick="sendChip(this)">'+escHtml(c)+'</span>';
  }).join('');
}
function askSuggestionFix(i) {
  if (!_lastSuggestions) return;
  const s = (_lastSuggestions.suggestions||[])[i];
  if (!s) return;
  const chatBtn = document.querySelectorAll('nav button')[3]; // dash,actions,analytics,chat,listings
  showTab('chat', chatBtn);
  document.getElementById('msg-input').value = 'Help me fix this: '+s.title+' — '+s.detail;
  sendMsg();
}

// ── Conversion Doctor (views but no sales → ranked fixes) ───────────────────
const _DXCOLOR = {critical:'var(--red)',high:'#e08030',medium:'var(--gold)',low:'#7ba0c2',trust:'var(--gold)'};
const _AREA_ICON = {photos:'📸',price:'💲',title:'🏷️',description:'📝',tags:'🔖',trust:'🤝'};
let _convTargets = [];
let _convDiagnoses = {};
function toggleConvPanel(btn) {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse' : '▼ Show';
}
function toggleDxBody(id, btn) {
  const el = document.getElementById('conv-dx-body-'+id);
  if (!el) return;
  const hidden = el.style.display === 'none';
  el.style.display = hidden ? '' : 'none';
  btn.textContent = hidden ? '▲ Collapse Diagnosis' : '▼ Show Diagnosis';
}
async function fixStage(listingId, fixIdx, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = '⏳ Staging…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/autofix/'+f.area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
    const rd = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
    btn.textContent = '✅ Staged — check Action Center';
    btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
    setTimeout(loadActions, 1500);
  } catch(e) {
    btn.disabled = false; btn.textContent = orig;
    alert('Could not stage fix: '+(e.message||e));
  }
}
function fixChat(listingId, fixIdx) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const f = (d._sortedFixes||[])[fixIdx];
  if (!f) return;
  const title = (d.stats&&d.stats.title)||'';
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix the '+f.area+' for listing "'+title+'": '+f.finding+' — '+f.fix;
  sendMsg();
}
async function fixAllStageable(listingId, btn) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area==='tags'||f.area==='title';});
  if (!fixes.length) return;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳ Staging…';
  var staged = 0, failed = [];
  for (var i = 0; i < fixes.length; i++) {
    try {
      var r = await fetchWithTimeout(BASE+'/api/autofix/'+fixes[i].area+'/'+listingId,{method:'POST',headers:{Authorization:'Bearer '+TOKEN}},90000);
      var rd = await r.json().catch(function(){return {};});
      if (!r.ok) throw new Error(rd.detail||'HTTP '+r.status);
      staged++;
    } catch(e) {
      failed.push(fixes[i].area+': '+(e.message||e));
    }
  }
  btn.textContent = staged+'/'+fixes.length+' staged ✅';
  btn.style.background = 'var(--green)'; btn.style.color = '#06140d';
  if (failed.length) alert('Some fixes could not be staged:\\n'+failed.join('\\n'));
  setTimeout(loadActions, 1500);
}
function fixAllInChat(listingId) {
  const d = _convDiagnoses[listingId];
  if (!d) return;
  const fixes = (d._sortedFixes||[]).filter(function(f){return f.area!=='tags'&&f.area!=='title';});
  if (!fixes.length) return;
  const title = (d.stats&&d.stats.title)||('Listing '+listingId);
  const chatBtn = document.querySelectorAll('nav button')[3];
  showTab('chat', chatBtn);
  const inp = document.getElementById('msg-input');
  inp.value = 'Fix all issues for listing "'+title+'": '+fixes.map(function(f){return f.area+': '+f.finding+' → '+f.fix;}).join('; ');
  sendMsg();
}
async function loadConvTargets() {
  const el = document.getElementById('conv-doctor');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/conversion-targets', {headers:{Authorization:'Bearer '+TOKEN}}, 25000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    _convTargets = d.targets||[];
    if (!_convTargets.length) { el.innerHTML = '<div class="empty" style="padding:20px 0">✅ Nothing to fix — every viewed listing is selling (or has no views yet).</div>'; return; }
    el.innerHTML = _convTargets.map(function(l){
      return '<div class="card" style="padding:12px 14px;margin-bottom:8px">'+
        '<div class="listing-info">'+
          '<div class="listing-title">'+escHtml(l.title)+'</div>'+
          '<div class="listing-meta">'+l.views+' views · '+l.num_favorers+' ♥ · <span style="color:var(--red)">0 sold</span> · $'+(+l.price||0).toFixed(2)+'</div>'+
        '</div>'+
        '<div class="act-btns">'+
          '<button class="act-btn primary" onclick="diagnoseConv('+l.listing_id+',this)">🩺 Diagnose</button>'+
          '<a class="act-btn" href="'+escHtml(l.url)+'" target="_blank">Open on Etsy</a>'+
        '</div>'+
        '<div id="conv-dx-'+l.listing_id+'"></div>'+
      '</div>';
    }).join('');
    const cBtn = document.getElementById('conv-collapse-btn');
    if (cBtn) cBtn.style.display = '';
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadConvTargets()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:8px 20px;font-size:13px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
async function diagnoseConv(id, btn) {
  const out = document.getElementById('conv-dx-'+id);
  if (!out) return;
  if (btn) { btn.disabled = true; btn.textContent = '🩺 Diagnosing…'; }
  out.innerHTML = '<div class="card" style="text-align:center;padding:20px 12px;margin-top:8px"><div class="spinner" style="margin:0 auto 10px"></div><div style="color:var(--muted);font-size:12px">Reading title, price, photos, tags &amp; description…</div></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/diagnose/'+id, {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 90000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    out.innerHTML = _renderDiagnosis(d);
  } catch(e) {
    out.innerHTML = '<div class="empty" style="padding:14px 0">'+escHtml(e.name==='AbortError'?'Diagnosis timed out — try again':e.message||'Failed')+'</div>';
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = '🩺 Diagnose again'; }
  }
}
function _renderDiagnosis(d) {
  const listingId = d.listing_id;
  const dx = d.diagnosis||{}, st = d.stats||{};
  if (dx.raw && !(dx.fixes && dx.fixes.length)) return '<div class="card" style="font-size:13px;white-space:pre-wrap;color:var(--muted);margin-top:8px">'+escHtml(dx.raw)+'</div>';
  const fixes = (dx.fixes||[]).slice().sort(function(a,b){ return (_PRANK[a.priority]||9)-(_PRANK[b.priority]||9); });
  _convDiagnoses[listingId] = Object.assign({},d,{_sortedFixes:fixes});
  let inner = '';
  inner += '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:8px;font-size:10px;color:var(--muted)">'+
    '<span>📸 '+(st.photo_count||0)+'/10</span><span>🔖 '+(st.tag_count||0)+'/13</span><span>🏷️ '+(st.title_length||0)+'/70</span><span>👁 '+(st.views||0)+'</span><span>♥ '+(st.favorites||0)+'</span><span style="color:var(--red)">🛒 '+(st.sales||0)+' sold</span></div>';
  if (dx.primary_issue) inner += '<div class="card" style="background:#241313;border-color:#5a2d2d;margin-bottom:8px"><div class="label" style="color:#e07070">⚠️ PRIMARY ISSUE</div><div style="font-size:13px;line-height:1.45;margin-top:4px">'+escHtml(dx.primary_issue)+'</div></div>';
  if (dx.summary) inner += '<div style="font-size:12px;color:var(--muted);line-height:1.45;margin-bottom:8px">'+escHtml(dx.summary)+'</div>';
  var stageableCount = fixes.filter(function(f){return f.area==='tags'||f.area==='title';}).length;
  var chatCount = fixes.filter(function(f){return f.area!=='tags'&&f.area!=='title';}).length;
  if (stageableCount > 0 || chatCount > 0) {
    inner += '<div class="act-btns" style="margin-bottom:14px">';
    if (stageableCount > 0) inner += '<button class="act-btn primary" style="font-size:13px;padding:9px" onclick="fixAllStageable('+listingId+',this)">🚀 Stage All ('+stageableCount+')</button>';
    if (chatCount > 0) inner += '<button class="act-btn" style="font-size:13px;padding:9px" onclick="fixAllInChat('+listingId+')">💬 Chat Fixes ('+chatCount+')</button>';
    inner += '</div>';
  }
  fixes.forEach(function(f,fIdx){
    const pc = _DXCOLOR[f.priority]||'var(--muted)';
    const icon = _AREA_ICON[f.area]||'•';
    const canStage = f.area==='tags'||f.area==='title';
    inner += '<div class="sug-card" style="border-left-color:'+pc+'">'+
      '<span class="sug-p" style="color:'+pc+'">'+escHtml(f.priority||'medium')+'</span>'+
      '<span style="font-size:9px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);margin-left:6px">'+icon+' '+escHtml(f.area||'')+'</span>'+
      '<div class="sug-title">'+escHtml(f.finding||'')+'</div>'+
      (f.fix?'<div class="sug-action"><b style="color:var(--gold2)">→ </b>'+escHtml(f.fix)+'</div>':'')+
      (f.impact?'<div class="sug-impact">💡 '+escHtml(f.impact)+'</div>':'')+
      '<div class="act-btns" style="margin-top:8px">'+
      (canStage
        ? '<button class="act-btn primary" onclick="fixStage('+listingId+','+fIdx+',this)">⚡ Stage Fix</button>'
        : '<button class="act-btn" onclick="fixChat('+listingId+','+fIdx+')">💬 Fix in Chat</button>')+
      '</div>'+
    '</div>';
  });
  return '<div style="margin-top:8px">'+
    '<button class="collapse-btn" onclick="toggleDxBody('+listingId+',this)">▲ Collapse Diagnosis</button>'+
    '<div id="conv-dx-body-'+listingId+'">'+inner+'</div>'+
    '</div>';
}

// ── Hub (Brand Kit · Products · Creds · Security) ──────────────────────────
var _THEMES = [
  {id:'DP1026',name:'Lavender Dreams',primary:'#8666AA',accent:'#C4A8D4',neutral:'#FAF7FF',text:'#2C1A3A'},
  {id:'DP1027',name:'Cotton Candy',   primary:'#DE97C6',accent:'#97C6DE',neutral:'#FFF6FC',text:'#2C1A2A'},
  {id:'DP1028',name:'Midnight Blue',  primary:'#1B2568',accent:'#7BA7C2',neutral:'#F0F5FF',text:'#0D1525'},
  {id:'DP1029',name:'Coral Peach',    primary:'#FD6C49',accent:'#F5B878',neutral:'#FFF8F4',text:'#3A1A0D'}
];
var _PRODUCTS_STATIC = [
  {id:'DP1026',name:'Ultimate Life Planner',      price:'$14.99',pages:104},
  {id:'DP1027',name:'Student & School Planner',   price:'$9.99', pages:90},
  {id:'DP1028',name:'Budget & Finance Planner',   price:'$12.99',pages:102},
  {id:'DP1029',name:'Fitness & Wellness Planner', price:'$12.99',pages:91}
];
function _renderBrandKit() {
  var html = '<div class="section-title">Product Color Palettes</div>';
  _THEMES.forEach(function(t){
    html += '<div class="card" style="margin-bottom:10px">';
    html += '<div style="font-size:12px;font-weight:700;color:var(--muted);margin-bottom:8px">'+escHtml(t.id)+' — '+escHtml(t.name)+'</div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap">';
    [{label:'Primary',hex:t.primary},{label:'Accent',hex:t.accent},{label:'Neutral',hex:t.neutral},{label:'Text',hex:t.text}].forEach(function(c){
      html += '<div style="display:flex;align-items:center;gap:5px">'+
        '<span class="swatch" style="background:'+escHtml(c.hex)+'"></span>'+
        '<div style="font-size:11px"><div style="color:var(--muted)">'+escHtml(c.label)+'</div>'+
        '<div style="font-family:monospace;font-size:10px;color:var(--text)">'+escHtml(c.hex)+'</div></div>'+
        '</div>';
    });
    html += '</div></div>';
  });
  html += '<div class="section-title">Listing Standards</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['Title','≤70 chars · keyword first 40 · commas not pipes'],
   ['Tags','13 tags · each ≤20 chars · multi-word buyer phrases'],
   ['Photos','10 slots · 2400×2400px · lifestyle hero first'],
   ['Price','.99 / .97 / .49 endings — never round numbers'],
   ['AI disclosure','Required in description · who_made: i_did'],
   ['File limit','20 MB per file (PDF + ZIP · Etsy hard limit)']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:10px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted);line-height:1.4">'+escHtml(r[1])+'</td></tr>';
  });
  html += '</table></div>';
  html += '<div class="section-title">Pricing Tiers</div><div class="card">';
  html += '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  [['DP1026 Life Planner','$14.99','104 pages + sticker pack'],
   ['DP1027 Student','$9.99','90 pages · student budget'],
   ['DP1028 Budget','$12.99','102 pages · finance niche'],
   ['DP1029 Fitness','$12.99','91 pages · wellness niche'],
   ['SVG 5-pack','$9.99','5 designs · instant DL'],
   ['SVG 10+ pack','$14.99','10+ designs · instant DL']
  ].forEach(function(r){
    html += '<tr style="border-bottom:1px solid var(--border)">'+
      '<td style="padding:7px 0;padding-right:8px;font-weight:600">'+escHtml(r[0])+'</td>'+
      '<td style="padding:7px 0;padding-right:8px;color:var(--gold);font-weight:700;white-space:nowrap">'+escHtml(r[1])+'</td>'+
      '<td style="padding:7px 0;color:var(--muted)">'+escHtml(r[2])+'</td></tr>';
  });
  html += '</table></div>';
  return html;
}
function loadProductIndex() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Core Products</div>';
  _PRODUCTS_STATIC.forEach(function(p,i){
    var t = _THEMES[i]||{};
    html += '<div class="prod-card" style="border-left-color:'+(t.primary||'var(--gold)')+'">'+
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
  html += '<div class="section-title" style="margin-top:8px">Platform Connections</div><div class="card">';
  [
    {name:'Etsy',      icon:'🛍️',status:'live',    note:'onbrandcraftz · authorized'},
    {name:'Pinterest', icon:'📌',        status:'roadmap',note:'API v5 — ready to integrate', steps:[
      'Create a Pinterest Developer app at developers.pinterest.com',
      'Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env',
      'Run: python tools/pinterest_oauth.py — authorizes and saves tokens to .env automatically',
      'Claim the Etsy shop under Pinterest "Claimed accounts" to enable Rich Pins',
      'Done — the Social Media Agent can post via tools/pinterest_api.py'
    ]},
    {name:'Instagram', icon:'📷',        status:'roadmap',note:'Meta Graph API (app review needed)', steps:[
      'Create a Meta Business app at developers.facebook.com',
      'Add the "Instagram Graph API" product to the app',
      'Connect the Instagram Professional account via a Facebook Page',
      'Add INSTAGRAM_APP_ID / INSTAGRAM_APP_SECRET to .env',
      'Generate a long-lived access token (scopes: instagram_basic, instagram_content_publish, instagram_manage_insights, pages_show_list, pages_read_engagement)',
      'Add INSTAGRAM_USER_ID / INSTAGRAM_ACCESS_TOKEN to .env',
      'Submit the app for Meta App Review before posting publicly — tools/instagram_api.py is already built and waiting on this'
    ]},
    {name:'Facebook',  icon:'📘',        status:'roadmap',note:'Same Meta app as Instagram', steps:[
      'No separate app needed — reuse the Meta app created for Instagram',
      'Add the Facebook Page and Pages API permission to that same app',
      'Generate a Page Access Token with the pages_manage_posts scope',
      'Add FACEBOOK_PAGE_ID / FACEBOOK_ACCESS_TOKEN to .env once issued'
    ]},
    {name:'TikTok',    icon:'🎵',        status:'roadmap',note:'TikTok for Business API', steps:[
      'App credentials are already configured (TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET)',
      'Run: python tools/tiktok_oauth.py — log in as @onbrandcraftz and approve',
      'Tokens save to .env automatically (access token 24h, refresh token 365 days)',
      'Re-run tools/tiktok_oauth.py whenever the access token expires',
      'Done — post via tools/tiktok_poster.py'
    ]},
    {name:'OneDrive',  icon:'☁️',        status:'roadmap',note:'Microsoft Graph — source file storage', steps:[
      'Not yet built — no OneDrive code exists in the repo today',
      'Register an app in the Azure Portal (Microsoft Entra ID → App registrations)',
      'Grant the Microsoft Graph "Files.ReadWrite" delegated permission',
      'Add ONEDRIVE_CLIENT_ID / ONEDRIVE_CLIENT_SECRET to .env',
      'Build tools/onedrive_oauth.py to get access/refresh tokens (does not exist yet)',
      'Use the Graph API /me/drive/root:/path:/content endpoint to sync source files for backup'
    ]}
  ].forEach(function(p){
    var live = p.status==='live';
    var key = p.name.toLowerCase();
    html += '<div class="cred-row" style="flex-wrap:wrap">'+
      '<div style="display:flex;align-items:center;gap:10px;width:100%">'+
      '<div style="font-size:20px;flex-shrink:0;width:28px">'+p.icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(p.name)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(p.note)+'</div></div>'+
      (live
        ? '<div style="font-size:11px;font-weight:700;color:var(--green)">✅ Live</div>'
        : '<div style="font-size:11px;font-weight:700;color:var(--muted);cursor:pointer;white-space:nowrap" onclick="toggleCredSteps(\\''+key+'\\')">🗺️ Roadmap ›</div>')+
      '</div>'+
      (live ? '' :
        '<div id="cred-steps-'+key+'" style="display:none;width:100%;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">'+
          '<div style="font-size:11px;font-weight:700;color:var(--muted);margin-bottom:6px;text-transform:uppercase;letter-spacing:.4px">Steps to complete</div>'+
          '<ol style="margin:0;padding-left:18px;font-size:12px;line-height:1.6">'+
            (p.steps||[]).map(function(s){return '<li style="margin-bottom:4px">'+escHtml(s)+'</li>';}).join('')+
          '</ol>'+
        '</div>')+
      '</div>';
  });
  html += '</div>';
  el.innerHTML = html;
}
function toggleCredSteps(key) {
  var panel = document.getElementById('cred-steps-'+key);
  if (!panel) return;
  panel.style.display = panel.style.display === 'none' ? 'block' : 'none';
}
async function loadCredentials() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/credentials/status',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var html = '<div class="card" style="margin-bottom:12px">';
    if (d.etsy_live) {
      html += '<div style="color:var(--green);font-size:15px;font-weight:700">✅ Etsy Live</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.shop_name||'onbrandcraftz')+' · token valid</div>';
    } else {
      html += '<div style="color:var(--red);font-size:15px;font-weight:700">⚠️ Etsy Ping Failed</div>'+
        '<div style="font-size:12px;color:var(--muted);margin-top:4px">'+escHtml(d.etsy_live_error||'Unknown error')+' — run python tools/etsy_oauth.py</div>';
    }
    html += '</div><div class="section-title">API Credentials</div><div class="card">';
    var et=d.etsy||{}, an=d.anthropic||{}, oa=d.openai||{}, sm=d.smtp||{}, pi=d.pinterest||{};
    [
      {label:'Etsy API Key',         ok:et.api_key,         note:'ETSY_API_KEY / ETSY_CLIENT_ID'},
      {label:'Etsy Access Token',    ok:et.access_token,    note:'Expires every 1 hour — auto-refreshed'},
      {label:'Etsy Refresh Token',   ok:et.refresh_token,   note:'90-day window — re-auth via etsy_oauth.py'},
      {label:'Anthropic (Claude)',   ok:an.api_key,         note:'""" + business_config.AGENT_NAME + """ (CEO) · Conversion Doctor · tag gen'},
      {label:'OpenAI (DALL-E)',      ok:oa.api_key,         note:'gpt-image-1 listing photo generation'},
      {label:'SMTP Email',           ok:sm.user,            note:'Post-purchase digital delivery'},
      {label:'Pinterest',            ok:pi.api_key,         note:'API v5 · roadmap'}
    ].forEach(function(c){
      var col = c.ok ? 'var(--green)' : 'var(--red)';
      html += '<div class="cred-row">'+
        '<div class="cred-dot" style="background:'+col+'"></div>'+
        '<div style="flex:1"><div style="font-size:13px;font-weight:600">'+escHtml(c.label)+'</div>'+
        '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
        '<div style="font-size:12px;font-weight:700;color:'+col+'">'+escHtml(c.ok?'Set ✓':'Not set')+'</div>'+
      '</div>';
    });
    html += '</div><div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">All tokens stored in .env — never committed to git</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadCredentials()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function _renderSecurityPosture() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  var html = '<div class="section-title">Security Posture</div><div class="card">';
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
  ].forEach(function(c){
    var icon = c.ok===true?'✅':c.ok===false?'⚠️':'❓';
    var col  = c.ok===true?'var(--green)':c.ok===false?'var(--red)':'var(--muted)';
    html += '<div class="posture-row">'+
      '<div style="font-size:16px;flex-shrink:0;width:24px">'+icon+'</div>'+
      '<div style="flex:1"><div style="font-size:13px;font-weight:600;color:'+col+'">'+escHtml(c.label)+'</div>'+
      '<div style="font-size:11px;color:var(--muted)">'+escHtml(c.note)+'</div></div>'+
    '</div>';
  });
  html += '</div>';
  html += '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-top:4px">'+
    '<div style="font-size:12px;color:#7ba0c2;line-height:1.7">'+
    '<b style="color:var(--gold)">Re-authorize Etsy:</b> If any API call returns 401, run<br>'+
    '<code style="font-size:11px;background:#0d1525;padding:2px 8px;border-radius:4px;display:inline-block;margin-top:4px">python tools/etsy_oauth.py</code>'+
    '</div></div>';
  el.innerHTML = html;
}
function showHubSection(section, btn) {
  document.querySelectorAll('.hub-section-btn').forEach(function(b){b.classList.remove('active');});
  if (btn) btn.classList.add('active');
  if (section==='brand')         document.getElementById('hub-content').innerHTML = _renderBrandKit();
  else if (section==='products') loadProductIndex();
  else if (section==='files')    loadFiles();
  else if (section==='studio')   loadStudio();
  else if (section==='creds')    loadCredentials();
  else if (section==='security') _renderSecurityPosture();
  else if (section==='relay')    _renderRelayPanel();
}
async function _renderRelayPanel() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var rs = await fetchWithTimeout(BASE+'/api/relay/status',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var status = await rs.json().catch(function(){return {};});
    if (!rs.ok) throw new Error(status.detail||'HTTP '+rs.status);
    var rf = await fetchWithTimeout(BASE+'/api/relay/allowed-folders',{headers:{Authorization:'Bearer '+TOKEN}},15000);
    var fd = await rf.json().catch(function(){return {};});
    if (!rf.ok) throw new Error(fd.detail||'HTTP '+rf.status);
    var folders = fd.folders || [];

    var badge, badgeCol;
    if (status.killed)            { badge = '⛔ Killed';   badgeCol = 'var(--red)'; }
    else if (status.connected)    { badge = '✅ Online';   badgeCol = 'var(--green)'; }
    else                          { badge = '⚪ Offline';  badgeCol = 'var(--muted)'; }

    var html = '<div class="card" style="margin-bottom:12px">';
    html += '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px">'+
      '<div><div style="font-size:15px;font-weight:700;color:'+badgeCol+'">'+badge+'</div>'+
      '<div style="font-size:11px;color:var(--muted);margin-top:4px">'+
        (status.last_heartbeat ? 'Last heartbeat: '+escHtml(status.last_heartbeat) : 'No heartbeat received yet')+
      '</div></div>'+
      (status.killed
        ? '<button onclick="relayResume()" style="background:var(--green);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Resume</button>'
        : '<button onclick="relayKill()" style="background:var(--red);color:#fff;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Kill Switch</button>')+
      '</div>';
    if (status.killed && status.killed_at) {
      html += '<div style="font-size:11px;color:var(--muted);margin-top:8px">Killed at '+escHtml(status.killed_at)+
        (status.killed_by ? ' by '+escHtml(status.killed_by) : '')+'</div>';
    }
    html += '<div style="font-size:11px;color:var(--muted);margin-top:8px">'+
      'Kill switch blocks every local tool — including read-only file access — until resumed.'+
      '</div>';
    html += '</div>';

    html += '<div class="section-title">Allowed Folders</div><div class="card">';
    if (!folders.length) {
      html += '<div class="empty">No folders configured yet — the relay can\\'t read or write anything on Scott\\'s machine until at least one is added.</div>';
    } else {
      folders.forEach(function(f){
        html += '<div class="cred-row">'+
          '<div style="flex:1"><div style="font-size:13px;font-weight:600;word-break:break-all">'+escHtml(f.path)+'</div>'+
          '<div style="font-size:11px;color:var(--muted)">added by '+escHtml(f.added_by||'system')+' · '+escHtml(f.added_at||'')+'</div></div>'+
          '<button onclick="removeAllowedFolder('+f.id+')" style="background:none;color:var(--red);border:1px solid var(--red);border-radius:8px;padding:6px 12px;font-size:12px;font-weight:600;cursor:pointer">Remove</button>'+
        '</div>';
      });
    }
    html += '<div style="display:flex;gap:8px;margin-top:12px">'+
      '<input id="relay-folder-input" type="text" placeholder="/data/workspace" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
      '<button onclick="addAllowedFolder()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Add</button>'+
      '</div>';
    html += '</div>';

    html += '<div class="section-title">Upload File to Relay Workspace</div><div class="card">';
    html += '<input id="relay-upload-input" type="file" onchange="_relayUploadPicked()" style="width:100%;color:var(--text);font-size:13px">'+
      '<div style="display:flex;gap:8px;margin-top:10px">'+
      '<input id="relay-upload-path" type="text" placeholder="/data/workspace/yourfile.pdf" style="flex:1;background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 12px;color:var(--text);font-size:13px">'+
      '<button onclick="uploadToRelay()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 18px;font-size:13px;font-weight:700;cursor:pointer">Upload</button>'+
      '</div>'+
      '<div id="relay-upload-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>'+
      '</div>';

    html += '<div style="font-size:11px;color:var(--muted);text-align:center;padding:10px 0">'+
      'The relay re-resolves every path with realpath before allowing access — this list is enforced on Scott\\'s machine, not just the server.'+
      '</div>';
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="_renderRelayPanel()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
async function relayKill() {
  if (!confirm('Engage the kill switch? This blocks ALL local relay actions, including reads, until resumed.')) return;
  try {
    await fetchWithTimeout(BASE+'/api/relay/kill', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) { alert('Could not engage kill switch: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function relayResume() {
  try {
    await fetchWithTimeout(BASE+'/api/relay/resume', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
  } catch(e) { alert('Could not resume: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function addAllowedFolder() {
  var inp = document.getElementById('relay-folder-input');
  var path = (inp && inp.value || '').trim();
  if (!path) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/relay/allowed-folders', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({path}),
    }, 15000);
    const d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
  } catch(e) { alert('Could not add folder: ' + (e.message||e)); }
  _renderRelayPanel();
}
async function removeAllowedFolder(id) {
  try {
    const r = await fetchWithTimeout(BASE+'/api/relay/allowed-folders/'+id, {method:'DELETE',headers:{Authorization:'Bearer '+TOKEN}}, 15000);
    if (!r.ok) { const d = await r.json().catch(function(){return {};}); throw new Error(d.detail||'HTTP '+r.status); }
  } catch(e) { alert('Could not remove folder: ' + (e.message||e)); }
  _renderRelayPanel();
}
function _relayUploadPicked() {
  var input = document.getElementById('relay-upload-input');
  var pathInput = document.getElementById('relay-upload-path');
  var file = input && input.files[0];
  if (file && pathInput && !pathInput.value) pathInput.value = '/data/workspace/' + file.name;
}
async function uploadToRelay() {
  var input = document.getElementById('relay-upload-input');
  var pathInput = document.getElementById('relay-upload-path');
  var status = document.getElementById('relay-upload-status');
  var file = input.files[0];
  if (!file) { alert('Choose a file first'); return; }
  var path = (pathInput.value || '').trim();
  if (!path) { alert('Destination path is required'); return; }
  status.textContent = 'Uploading...';
  try {
    var res = await fetchWithTimeout(
      BASE+'/api/relay/upload?path=' + encodeURIComponent(path),
      { method: 'POST', headers: { 'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/octet-stream' }, body: file },
      120000
    );
    var data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Upload failed');
    status.textContent = 'Uploaded ' + data.bytes_written + ' bytes to ' + data.path;
    input.value = '';
  } catch (e) {
    status.textContent = '';
    alert(e.message || e);
  }
}
function _fileUrl(f, inline){
  return BASE+'/api/files/download?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    (inline?'&inline=1':'');
}
function _zipEntryUrl(f, entryName){
  return BASE+'/api/files/zip-entry?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&entry='+encodeURIComponent(entryName);
}
function _fileIcon(name){
  var n=(name||'').toLowerCase();
  if(n.match(/\\.(png|jpe?g|gif|webp|svg)$/)) return '🖼️';
  if(n.endsWith('.pdf')) return '📕';
  if(n.endsWith('.zip')) return '🗂️';
  if(n.match(/\\.(txt|md)$/)) return '📃';
  return '📄';
}
function toggleZip(id, btn){
  var el=document.getElementById(id);
  if(!el) return;
  var open=el.style.display==='none';
  el.style.display=open?'':'none';
  if(btn) btn.textContent=open?'▾':'▸';
}
function openFile(url){ window.open(url,'_blank'); }
async function loadFiles() {
  var el = document.getElementById('hub-content');
  if (!el) return;
  el.innerHTML = '<div class="spinner"></div>';
  try {
    var r = await fetchWithTimeout(BASE+'/api/files',{headers:{Authorization:'Bearer '+TOKEN}},20000);
    var d = await r.json().catch(function(){return {};});
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    var groups = d.groups||[];
    if (!groups.length || groups.every(function(g){return !g.files.length;})) {
      el.innerHTML = '<div class="empty" style="line-height:1.6">'+
        escHtml(d.empty_reason||'No files yet.')+'</div>';
      return;
    }
    var html = '<div class="card" style="background:#1a2030;border-color:#2a3d5a;margin-bottom:12px">'+
      '<div style="font-size:12px;color:#7ba0c2;line-height:1.6">The actual product files living on the server '+
      '(data/digital_products/ and data/backups/). Tap a file to open it. Tap a ZIP to expand it and open any '+
      'file inside directly — no unzipping needed.</div></div>';
    var zipIdx=0;
    groups.forEach(function(g){
      if (!g.files.length) return;
      html += '<div class="section-title">'+escHtml(g.label)+' ('+g.files.length+')</div><div class="card">';
      g.files.forEach(function(f){
        var when = new Date(f.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        if (f.is_zip) {
          var zid='zip-'+(zipIdx++);
          var entries=f.entries||[];
          html += '<div class="listing-item" onclick="toggleZip(&apos;'+zid+'&apos;,this.querySelector(&apos;.zip-caret&apos;))" style="cursor:pointer">'+
            '<div class="thumb-placeholder">🗂️</div>'+
            '<div class="listing-info"><div class="listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+' · '+entries.length+' files inside</div></div>'+
            '<div class="zip-caret" style="color:var(--gold);font-size:16px">▸</div>'+
          '</div>';
          html += '<div id="'+zid+'" style="display:none;margin:0 0 6px 14px;border-left:2px solid #2a3d5a;padding-left:8px">';
          if(!entries.length){
            html += '<div class="listing-meta" style="padding:8px 0">Could not read this ZIP\\'s contents.</div>';
          }
          entries.forEach(function(en){
            var eurl=_zipEntryUrl(f,en.name);
            html += '<div class="listing-item" onclick="openFile(&apos;'+eurl+'&apos;)" style="cursor:pointer;padding:7px 4px">'+
              '<div class="thumb-placeholder" style="font-size:16px">'+_fileIcon(en.name)+'</div>'+
              '<div class="listing-info"><div class="listing-title" style="font-size:13px">'+escHtml(en.name)+'</div>'+
              '<div class="listing-meta">'+escHtml(en.size_human)+(en.inline?' · tap to open':' · tap to download')+'</div></div>'+
              '<div style="color:var(--gold);font-size:15px">'+(en.inline?'↗':'⬇')+'</div>'+
            '</div>';
          });
          html += '</div>';
        } else {
          var url=_fileUrl(f, f.inline?1:0);
          html += '<div class="listing-item" onclick="openFile(&apos;'+url+'&apos;)" style="cursor:pointer">'+
            '<div class="thumb-placeholder">'+_fileIcon(f.path)+'</div>'+
            '<div class="listing-info"><div class="listing-title">'+escHtml(f.path)+'</div>'+
            '<div class="listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+(f.inline?' · tap to open':' · tap to download')+'</div></div>'+
            '<div style="color:var(--gold);font-size:18px">'+(f.inline?'↗':'⬇')+'</div>'+
          '</div>';
        }
      });
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load files')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadFiles()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}
function loadHub() {
  var btns = document.querySelectorAll('.hub-section-btn');
  btns.forEach(function(b){b.classList.remove('active');});
  if (btns[0]) btns[0].classList.add('active');
  document.getElementById('hub-content').innerHTML = _renderBrandKit();
}

// ── Back to top (listings) ─────────────────────────────────────────────────
(function(){
  const fab = document.getElementById('fab-top');
  const screen = document.getElementById('screen-listings');
  if (!fab || !screen) return;
  screen.addEventListener('scroll', function(){ fab.classList.toggle('visible', _onListings && screen.scrollTop > 200); }, {passive:true});
  fab.addEventListener('click', function(){ screen.scrollTo({top:0,behavior:'smooth'}); });
})();

// ── Batch tag fix ──────────────────────────────────────────────────────────
async function batchStageTags(btn) {
  if (!confirm('Scan all active listings and stage tag fixes for every listing with fewer than 13 tags?\\n\\nThis may take up to 2 minutes. You review and approve each fix in this Action Center.')) return;
  btn.disabled = true;
  const orig = btn.textContent;
  btn.textContent = '⏳ Generating…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/batch/stage-tags', {method:'POST',headers:{Authorization:'Bearer '+TOKEN}}, 180000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const errNote = d.errors && d.errors.length ? `\n${d.errors.length} listing(s) had tag-length issues and were skipped.` : '';
    alert('✅ ' + d.message + errNote);
    loadActions();
  } catch(e) {
    alert('Error: ' + (e.name==='AbortError'?'Request timed out — the batch is still running server-side; check the Action Center in a moment':(e.message||e)));
  } finally {
    btn.disabled = false;
    btn.textContent = orig;
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js').catch(()=>{}); }
// Restore last CEO report from sessionStorage so the dashboard is instant on
// every page reload — no spinner needed when we already have recent data.
(function(){
  try {
    var _s = sessionStorage.getItem('obc_sug');
    if (_s) {
      var _p = JSON.parse(_s);
      if (_p && _p.generated_at && Array.isArray(_p.suggestions) && _p.suggestions.length && !_p.error) {
        var _age = Date.now() - new Date(_p.generated_at).getTime();
        if (_age < 4 * 3600 * 1000) _lastSuggestions = _p; // accept up to 4h old
      }
    }
  } catch(e) {}
})();
loadDash();
loadTodos();
setTimeout(loadActions, 1200);  // populate Action Center + nav badge without being asked
setTimeout(loadConvTargets, 1800);  // Conversion Doctor worklist on the dashboard

// Surface a loud warning the moment the durable /data volume isn't attached — this is
// silent otherwise (the server just falls back to ephemeral storage) and was previously
// only caught by manually hitting /health (diagnosed 2026-06-17, ops_runbook).
fetch(BASE + '/health').then(r => r.json()).then(h => {
  if (h && h.persistent === false) {
    const b = document.getElementById('persist-banner');
    b.style.display = 'block';
    document.documentElement.style.setProperty(
      '--hdr', 'calc(52px + ' + b.offsetHeight + 'px + env(safe-area-inset-top,0px))'
    );
  }
}).catch(() => {});
</script>
</body>
</html>""".replace("Scott", business_config.OWNER_NAME).replace("Frank", business_config.AGENT_NAME_SHORT)
```

<!-- /TRASH 20260702-012 -->

<!-- TRASH id=20260702-013 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA '/' route removed - served _WEB_UI which is deleted" -->
## 20260702-013 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA '/' route removed - served _WEB_UI which is deleted  
**Payload:** `data/trash/files/20260702-013__snippet.txt`

```python
@app.get("/", response_class=HTMLResponse)
def web_ui(request: Request):
    if not _check_session(request):
        return RedirectResponse(f"/login?next={request.url.path}", status_code=307)
    return HTMLResponse(
        content=_WEB_UI,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )
```

<!-- /TRASH 20260702-013 -->

<!-- TRASH id=20260702-014 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA _SW_JS service worker constant removed" -->
## 20260702-014 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA _SW_JS service worker constant removed  
**Payload:** `data/trash/files/20260702-014__snippet.txt`

```python

```

<!-- /TRASH 20260702-014 -->

<!-- TRASH id=20260702-015 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old PWA service worker route removed - _SW_JS constant deleted" -->
## 20260702-015 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old PWA service worker route removed - _SW_JS constant deleted  
**Payload:** `data/trash/files/20260702-015__snippet.txt`

```python
@app.get("/sw.js")
def service_worker():
    return Response(
        content=_SW_JS,
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache", "Service-Worker-Allowed": "/"},
    )
```

<!-- /TRASH 20260702-015 -->

<!-- TRASH id=20260702-016 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA _MANIFEST constant removed (root '/' PWA)" -->
## 20260702-016 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA _MANIFEST constant removed (root '/' PWA)  
**Payload:** `data/trash/files/20260702-016__snippet.txt`

```python
_MANIFEST = {
    "name": f"{business_config.BUSINESS_NAME} Hub",
    "short_name": business_config.BUSINESS_NAME,
    "description": f"{business_config.BUSINESS_NAME} Etsy operations hub — live metrics, action center, {business_config.AGENT_NAME} (CEO agent).",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "any",
    "background_color": "#0D1B2A",
    "theme_color": "#0D1B2A",
    "icons": [
        {"src": "/static/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "/static/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}
```

<!-- /TRASH 20260702-016 -->

<!-- TRASH id=20260702-017 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA manifest route removed - _MANIFEST deleted" -->
## 20260702-017 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA manifest route removed - _MANIFEST deleted  
**Payload:** `data/trash/files/20260702-017__snippet.txt`

```python
@app.get("/manifest.webmanifest")
def manifest():
    return JSONResponse(_MANIFEST, media_type="application/manifest+json")
```

<!-- /TRASH 20260702-017 -->

<!-- TRASH id=20260702-018 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix8: dead _auth() infrastructure removed - unused since _auth_session_or_bearer was introduced" -->
## 20260702-018 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix8: dead _auth() infrastructure removed - unused since _auth_session_or_bearer was introduced  
**Payload:** `data/trash/files/20260702-018__snippet.txt`

```python
security = HTTPBearer()
```

<!-- /TRASH 20260702-018 -->

<!-- TRASH id=20260702-019 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix8: dead _auth() function removed - superseded by _auth_session_or_bearer" -->
## 20260702-019 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix8: dead _auth() function removed - superseded by _auth_session_or_bearer  
**Payload:** `data/trash/files/20260702-019__snippet.txt`

```python
def _auth(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    if not secrets.compare_digest(credentials.credentials, APP_TOKEN):
        raise HTTPException(status_code=401, detail="Invalid token")
    return credentials.credentials
```

<!-- /TRASH 20260702-019 -->

<!-- TRASH id=20260702-020 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix9: local _revenue() helper in _build_metrics replaced by module-level _order_revenue()" -->
## 20260702-020 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix9: local _revenue() helper in _build_metrics replaced by module-level _order_revenue()  
**Payload:** `data/trash/files/20260702-020__snippet.txt`

```python
        def _revenue(order_list):
            total = 0.0
            for o in order_list:
                gt = o.get("grandtotal", {})
                if isinstance(gt, dict):
                    divisor = gt.get("divisor", 100) or 100
                    total += gt.get("amount", 0) / divisor
            return round(total, 2)
```

<!-- /TRASH 20260702-020 -->

<!-- TRASH id=20260702-021 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix9: inline grandtotal calc in recent_sales replaced by _order_revenue()" -->
## 20260702-021 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix9: inline grandtotal calc in recent_sales replaced by _order_revenue()  
**Payload:** `data/trash/files/20260702-021__snippet.txt`

```python
            gt = o.get("grandtotal", {})
            divisor = gt.get("divisor", 100) or 100
            amount = round(gt.get("amount", 0) / divisor, 2)
```

<!-- /TRASH 20260702-021 -->

<!-- TRASH id=20260702-022 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix9: local _rev() helper in star seller eligibility replaced by module-level _order_revenue()" -->
## 20260702-022 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix9: local _rev() helper in star seller eligibility replaced by module-level _order_revenue()  
**Payload:** `data/trash/files/20260702-022__snippet.txt`

```python
            def _rev(lst):
                total = 0.0
                for o in lst:
                    gt = o.get("grandtotal", {})
                    if isinstance(gt, dict):
                        divisor = gt.get("divisor", 100) or 100
                        total += gt.get("amount", 0) / divisor
                return round(total, 2)
```

<!-- /TRASH 20260702-022 -->

<!-- TRASH id=20260702-023 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix12: /api/studio/diagnose endpoint removed - imageio_ffmpeg dependency causes import errors on deploys without ffmpeg" -->
## 20260702-023 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix12: /api/studio/diagnose endpoint removed - imageio_ffmpeg dependency causes import errors on deploys without ffmpeg  
**Payload:** `data/trash/files/20260702-023__snippet.txt`

```python
@app.get("/api/studio/diagnose")
async def studio_diagnose(_token: str = Depends(_auth_session_or_bearer)):
    """Probe Railway state: ffmpeg binary, directory writability, mini encode test."""
    import subprocess as _sp, os as _os, imageio_ffmpeg as _iio_ffmpeg
    r: dict = {"build_id": _BUILD_ID}

    # Use the same ffmpeg resolution logic as video_generator.py
    ffp = _iio_ffmpeg.get_ffmpeg_exe()
    r["ffmpeg_exe"] = ffp
    r["ffmpeg_exists"] = _os.path.exists(ffp)
    r["ffmpeg_executable"] = _os.access(ffp, _os.X_OK) if r["ffmpeg_exists"] else False
    try:
        v = _sp.run([ffp, "-version"], capture_output=True, text=True, timeout=10)
        r["ffmpeg_version_line"] = (v.stdout or v.stderr).split("\n")[0]
        r["ffmpeg_version_rc"] = v.returncode
    except Exception as _e:
        r["ffmpeg_version_error"] = str(_e)

    from pathlib import Path as _P
    for key, path in [("video_dir", _P("data/social/videos")), ("upload_dir", _P("studio_uploads"))]:
        try:
            path.mkdir(parents=True, exist_ok=True)
            (path / ".wtest").write_text("x")
            (path / ".wtest").unlink()
            r[f"{key}_writable"] = True
        except Exception as _e:
            r[f"{key}_writable"] = False
            r[f"{key}_error"] = str(_e)

    try:
        import numpy as _np, tempfile as _tf
        frame = _np.zeros((10, 10, 3), dtype=_np.uint8)
        with _tf.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            tmp = f.name
        cmd = [ffp, "-y", "-f", "rawvideo", "-vcodec", "rawvideo",  # ffp from get_ffmpeg_exe()
               "-s", "10x10", "-pix_fmt", "rgb24", "-r", "1", "-i", "pipe:0",
               "-vcodec", "libx264", "-pix_fmt", "yuv420p", "-preset", "fast", "-an", tmp]
        import threading as _th
        proc = _sp.Popen(cmd, stdin=_sp.PIPE, stderr=_sp.PIPE)
        frame_bytes = frame.tobytes()

        def _wr():
            try:
                proc.stdin.write(frame_bytes)
            except BrokenPipeError:
                pass
            finally:
                try: proc.stdin.close()
                except Exception: pass

        _wt = _th.Thread(target=_wr, daemon=True)
        _wt.start()
        stderr = proc.stderr.read()
        _wt.join(timeout=10)
        proc.wait(timeout=5)
        r["mini_encode_rc"] = proc.returncode
        if proc.returncode == 0:
            r["mini_encode_size"] = _os.path.getsize(tmp)
            r["mini_encode_ok"] = True
            _os.unlink(tmp)
        else:
            r["mini_encode_ok"] = False
            r["mini_encode_stderr"] = stderr.decode("utf-8", errors="replace")[-800:]
    except Exception as _e:
        r["mini_encode_ok"] = False
        r["mini_encode_error"] = str(_e)

    return r
```

<!-- /TRASH 20260702-023 -->

<!-- TRASH id=20260702-024 date=2026-07-02 kind=snippet source="tools/api_server/main.py" reason="v88 fix7: old mobile PWA _SW_JS service worker constant removed" -->
## 20260702-024 · 2026-07-02 · snippet · `tools/api_server/main.py`
**Reason:** v88 fix7: old mobile PWA _SW_JS service worker constant removed  
**Payload:** `data/trash/files/20260702-024__snippet.txt`

```python
_SW_JS = (
    "const CACHE='obc-shell-" + _BUILD_ID + "';\n"
    "self.addEventListener('install',e=>self.skipWaiting());\n"
    "self.addEventListener('activate',e=>e.waitUntil((async()=>{\n"
    "  const keys=await caches.keys();\n"
    "  await Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)));\n"
    "  await self.clients.claim();\n"
    "})()));\n"
    "self.addEventListener('fetch',e=>{\n"
    "  const req=e.request;\n"
    "  if(req.method!=='GET') return;\n"
    "  e.respondWith(fetch(req).then(r=>{\n"
    "    if(req.mode==='navigate'){const cp=r.clone();caches.open(CACHE).then(c=>c.put('/',cp));}\n"
    "    return r;\n"
    "  }).catch(()=>caches.match(req).then(m=>m||caches.match('/'))));\n"
    "});\n"
)
```

<!-- /TRASH 20260702-024 -->

<!-- TRASH id=20260702-025 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method, never called in codebase" -->
## 20260702-025 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method, never called in codebase  
**Payload:** `data/trash/files/20260702-025__snippet.txt`

```python
    def get_conversation(self, conversation_id: int) -> dict:
        """Get a single conversation with all messages."""
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/conversations/{conversation_id}")
```

<!-- /TRASH 20260702-025 -->

<!-- TRASH id=20260702-026 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method, never called in codebase" -->
## 20260702-026 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method, never called in codebase  
**Payload:** `data/trash/files/20260702-026__snippet.txt`

```python
    def get_conversation(self, conversation_id: int) -> dict:
        """Get a single conversation with all messages."""
        self._require_oauth()
        return self._request("GET", f"shops/{self.shop_id}/conversations/{conversation_id}")
```

<!-- /TRASH 20260702-026 -->

<!-- TRASH id=20260702-027 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method, never called in codebase" -->
## 20260702-027 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method, never called in codebase  
**Payload:** `data/trash/files/20260702-027__snippet.txt`

```python
    def update_listing_inventory(
        self, listing_id: int | str, quantity: int | None = None, price: float | None = None
    ) -> dict:
        """Update listing quantity and/or price. Requires OAuth access token.

        Etsy quirk: the top-level `price` field on update_listing() / PATCH listings/{id}
        is silently ignored for any listing that has an inventory record (which is most
        listings, including ones with no real variations) — price must be set per-offering
        via PUT listings/{id}/inventory instead. Fetches current inventory first so
        sku/property_values/other products aren't wiped out by a partial overwrite.
        """
        self._require_oauth()
        current = self._request("GET", f"listings/{listing_id}/inventory")
        products = []
        for p in current["products"]:
            offerings = []
            for off in p["offerings"]:
                offerings.append({
                    "price": price if price is not None else off["price"],
                    "quantity": quantity if quantity is not None else off["quantity"],
                    "is_enabled": off["is_enabled"],
                })
            products.append({
                "sku": p.get("sku", ""),
                "property_values": p.get("property_values", []),
                "offerings": offerings,
            })
        return self._request(
            "PUT",
            f"listings/{listing_id}/inventory",
            body={"products": products},
        )

    # ── Shop sections ─────────────────────────────────────────────────────────
```

<!-- /TRASH 20260702-027 -->

<!-- TRASH id=20260702-028 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method, never called in codebase" -->
## 20260702-028 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method, never called in codebase  
**Payload:** `data/trash/files/20260702-028__snippet.txt`

```python
    def delete_listing_file(self, listing_id: int | str, listing_file_id: int | str) -> None:
        """Delete a specific digital file from a listing. Requires OAuth access token."""
        self._require_oauth()
        self._request("DELETE", f"shops/{self.shop_id}/listings/{listing_id}/files/{listing_file_id}")
```

<!-- /TRASH 20260702-028 -->

<!-- TRASH id=20260702-029 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method, never called in codebase" -->
## 20260702-029 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method, never called in codebase  
**Payload:** `data/trash/files/20260702-029__snippet.txt`

```python
    def sync_orders_from_etsy(self) -> list[dict]:
        """Fetch orders via OAuth and return a normalised list of order dicts.

        Each dict contains: order_id, buyer_name, buyer_email, total_price,
        items, created_date.

        Returns an empty list when OAuth is not configured or the request fails.
        """
        try:
            raw = self.get_orders()
        except EtsyAPIError:
            return []

        receipts = raw.get("results", [])
        orders = []
        for r in receipts:
            # Buyer name: prefer name field, fall back to first+last
            buyer_name = r.get("name") or (
                f"{r.get('first_line', '')} {r.get('last_line', '')}".strip()
            )
            # Items: list of transaction summaries
            items = [
                {
                    "listing_id": t.get("listing_id"),
                    "title": t.get("title", ""),
                    "quantity": t.get("quantity", 1),
                    "price": t.get("price", {}).get("amount", 0) / max(t.get("price", {}).get("divisor", 100), 1)
                    if isinstance(t.get("price"), dict)
                    else t.get("price", 0),
                }
                for t in r.get("transactions", [])
            ]
            total_raw = r.get("grandtotal") or r.get("total_price") or {}
            if isinstance(total_raw, dict):
                total_price = total_raw.get("amount", 0) / max(total_raw.get("divisor", 100), 1)
            else:
                total_price = float(total_raw or 0)

            orders.append({
                "order_id": r.get("receipt_id"),
                "buyer_name": buyer_name,
                "buyer_email": r.get("buyer_email", ""),
                "total_price": round(total_price, 2),
                "items": items,
                "created_date": r.get("create_timestamp") or r.get("created_timestamp", ""),
            })
        return orders
```

<!-- /TRASH 20260702-029 -->

<!-- TRASH id=20260702-030 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead method (deprecated), immediately raises EtsyAPIError" -->
## 20260702-030 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead method (deprecated), immediately raises EtsyAPIError  
**Payload:** `data/trash/files/20260702-030__snippet.txt`

```python
    def create_review_response(self, review_id: int, response_text: str) -> dict:
        """DEPRECATED — Etsy v3 has no review-response endpoint or feedback_w scope.

        Confirmed 2026-06-09: the OAuth server rejects feedback_w as invalid_scope
        and this POST path returns 404. Review responses must be posted manually
        in Shop Manager or the Etsy Seller app.
        """
        raise EtsyAPIError(
            0,
            "Review responses cannot be posted via the Etsy v3 API (no feedback_w "
            "scope exists). Respond manually: Etsy Seller app → Reviews → Respond.",
        )
```

<!-- /TRASH 20260702-030 -->

<!-- TRASH id=20260702-031 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead methods (get_shipping_profiles, create_shipping_profile), never called in codebase" -->
## 20260702-031 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead methods (get_shipping_profiles, create_shipping_profile), never called in codebase  
**Payload:** `data/trash/files/20260702-031__snippet.txt`

```python
    # ── Shipping profiles ─────────────────────────────────────────────────────

    def get_shipping_profiles(self) -> list[dict]:
        """Get all shipping profiles for the shop."""
        self._require_oauth()
        result = self._request("GET", f"shops/{self.shop_id}/shipping-profiles")
        return result.get("results", [])

    def create_shipping_profile(
        self,
        title: str,
        origin_country: str = "US",
        primary_cost: float = 0.0,
        secondary_cost: float = 0.0,
        min_processing: int = 3,
        max_processing: int = 14,
        processing_unit: str = "business_days",
    ) -> dict:
        """Create a shipping profile. Returns the created profile including shipping_profile_id."""
        self._require_oauth()
        return self._request(
            "POST",
            f"shops/{self.shop_id}/shipping-profiles",
            body={
                "title": title,
                "origin_country_iso": origin_country,
                "primary_cost": primary_cost,
                "secondary_cost": secondary_cost,
                "destination_region": "everywhere",
                "min_processing_time": min_processing,
                "max_processing_time": max_processing,
                "processing_time_unit": processing_unit,
            },
        )
```

<!-- /TRASH 20260702-031 -->

<!-- TRASH id=20260702-032 date=2026-07-02 kind=snippet source="tools/etsy_api.py" reason="v88 cleanup: dead module-level get_client(), never called anywhere" -->
## 20260702-032 · 2026-07-02 · snippet · `tools/etsy_api.py`
**Reason:** v88 cleanup: dead module-level get_client(), never called anywhere  
**Payload:** `data/trash/files/20260702-032__snippet.txt`

```python
def get_client() -> EtsyAPIClient:
    return EtsyAPIClient()
```

<!-- /TRASH 20260702-032 -->

<!-- TRASH id=20260702-033 date=2026-07-02 kind=file source="tools/fix_kawaii_tag_mismatch.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-033 · 2026-07-02 · file · `tools/fix_kawaii_tag_mismatch.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-033__fix_kawaii_tag_mismatch.py`

```
#!/usr/bin/env python3
"""
One-off corrective tool: fix mismatched "kawaii" tags on listings whose actual
product has nothing to do with kawaii.

Background (2026-06-17): an audit found 44 active listings carrying kawaii tags
('kawaii wall art', 'kawaii paper', 'kawaii character', etc.) while their titles /
products were ordinary wall art prints and scrapbook digital paper packs. Kawaii
tags on a non-kawaii product are a truthfulness violation (CLAUDE.md TOP PRIORITY
RULE) and pollute Etsy's query-matching relevance signal.

IMPORTANT — 3 of the 44 are EXCLUDED on purpose: the Fitness/Budget/Life digital
planners ARE genuinely kawaii products (their catalog tag lists legitimately
include 'kawaii planner'/'kawaii sticker pack'). Removing kawaii from those would
be deleting *accurate* tags. So this tool only touches the 41 genuine mismatches:
  - 12 digital paper packs  -> swap 'kawaii paper' + the misleading 'digital
    planner' tag for two accurate theme tags (also de-duplicates the identical
    tag block they all share, which is itself a spam-detection risk)
  - 29 wall art prints       -> replace kawaii tags with accurate subject tags

Usage:
    python tools/fix_kawaii_tag_mismatch.py            # dry run (default)
    python tools/fix_kawaii_tag_mismatch.py --apply    # push to Etsy
"""

import sys
import time
import re

sys.path.insert(0, "tools")
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── New tag sets, keyed by listing_id ─────────────────────────────────────────
# Every set: exactly 13 tags, each <= 20 chars, lowercase, no 'kawaii', and no
# tag is a contiguous substring of that listing's title (validated below).

# Digital paper packs: replace 'kawaii paper' and 'digital planner' with two
# accurate per-theme tags. Base block is identical to current minus those two.
_PAPER_BASE = [
    "scrapbook paper", "printable paper", "goodnotes background",
    "digital background", "pattern paper", "scrapbook digital",
    "background paper", "paper printable", "digital download",
    "digital paper kit", "scrapbooking kit",
]  # 11 tags; 2 theme tags appended per pack -> 13


def _paper(theme1: str, theme2: str) -> list[str]:
    return [theme1, theme2] + list(_PAPER_BASE)


NEW_TAGS = {
    # ── 12 digital paper packs ────────────────────────────────────────────────
    4519456348: _paper("sunflower paper", "yellow paper"),       # Sunflower Studio
    4519457131: _paper("sage green paper", "botanical paper"),   # Sage Garden
    4519457007: _paper("teal digital paper", "coastal paper"),   # Ocean Breeze
    4519455964: _paper("brown digital paper", "coffee paper"),   # Mocha Latte
    4519455834: _paper("navy digital paper", "blue paper pack"), # Midnight Blue
    4519455652: _paper("mermaid paper", "ocean paper"),          # Mermaidcore
    4519456441: _paper("green digital paper", "matcha paper"),   # Matcha Serenity
    4519455342: _paper("lavender paper", "purple paper"),        # Lavender Dreams
    4519456175: _paper("pink digital paper", "pastel paper"),    # Cotton Candy
    4519456025: _paper("peach paper", "coral paper"),    # Coral Peach
    4519455899: _paper("sakura paper", "pink paper pack"),       # Cherry Blossom
    4519454834: _paper("celestial paper", "star paper"),         # Celestial Night

    # ── Wall art: full regeneration from subject ──────────────────────────────
    4515678344: [  # Abstract Brushstroke / Modern
        "abstract art print", "modern wall art", "minimalist art", "neutral wall art",
        "living room art", "bedroom wall art", "office wall decor", "gallery wall art",
        "housewarming gift", "gift for her", "digital print", "contemporary art", "boho wall art"],
    4515678198: [  # Vintage Botanical / Herb
        "garden wall art", "vintage wall art", "herb wall art", "kitchen wall decor",
        "botanical art", "living room art", "bedroom wall art", "gallery wall art",
        "housewarming gift", "nature lover gift", "digital print", "cottagecore art", "plan
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-033 -->

<!-- TRASH id=20260702-034 date=2026-07-02 kind=file source="tools/fix_svg_listing_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-034 · 2026-07-02 · file · `tools/fix_svg_listing_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-034__fix_svg_listing_photos.py`

```
#!/usr/bin/env python3
"""
fix_svg_listing_photos.py — Replace all wrong wall-art room photos on SVG bundle
listings with correct design-preview photos built from the actual SVG files.

Generates 3 photos per listing (no OpenAI required — pure PIL + cairosvg):
  rank=1  Full design grid (all designs at 4-col grid on cream background)
  rank=2  Spotlight: 3 featured designs at larger scale
  rank=3  Info card: what's included (SVG/PNG/EPS/DXF), compatible machines

Usage:
    python tools/fix_svg_listing_photos.py
    python tools/fix_svg_listing_photos.py --dry-run   # build images, no upload
"""

from __future__ import annotations

import sys, os, time, argparse, math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Constants ─────────────────────────────────────────────────────────────────

CANVAS      = 2400
BG_COLOR    = (253, 248, 240)   # warm cream #FDF8F0
CELL_BG     = (255, 255, 255)
DARK_TEXT   = (30, 30, 30)
MID_TEXT    = (90, 90, 90)
ACCENT      = (120, 90, 160)    # soft purple accent for info card

FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

REPO_ROOT   = Path(__file__).parent.parent

# ── Bundle definitions ────────────────────────────────────────────────────────
# listing_id = regular bundle | commercial_id = commercial license version

BUNDLES = [
    {
        "slug":          "floral",
        "name":          "Floral Botanical SVG Bundle",
        "listing_id":    4514130045,
        "commercial_id": 4515439743,
        "svg_dir":       "data/svg_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "christian_faith",
        "name":          "Christian Faith SVG Bundle",
        "listing_id":    4514134583,
        "commercial_id": 4515439751,
        "svg_dir":       "data/faith_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "graduation",
        "name":          "Graduation 2026 SVG Bundle",
        "listing_id":    4514136783,
        "commercial_id": 4515439755,
        "svg_dir":       "data/grad_pack/SVG",
        "design_count":   9,
    },
    {
        "slug":          "mom_life",
        "name":          "Mom Life SVG Bundle",
        "listing_id":    4514392281,
        "commercial_id": 4515437432,
        "svg_dir":       "data/mom_life_pack/SVG",
        "design_count":  20,
    },
    {
        "slug":          "good_vibes",
        "name":          "Good Vibes SVG Bundle",
        "listing_id":    4514536935,
        "commercial_id": 4515439763,
        "svg_dir":       "data/groovy_pack/SVG",
        "design_count":  10,
    },
    {
        "slug":          "western",
        "name":          "Western SVG Bundle",
        "listing_id":    None,
        "commercial_id": 4515437442,
        "svg_dir":       "data/svg_bundles/western/SVG",
        "design_count":  12,
    },
]


# ── Font loader ───────────────────────────────────────────────────────────────

def _font(path: str, size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ── SVG rendering ─────────────────────────────────────────────────────────────

def render_svg(svg_path: Path, size: int) -> Image.Image | None:
    try:
        png = cairosvg.svg2png(url=str(svg_path), output_width=size, output_height=size)
        return Image.open(BytesIO(png)).convert("RGBA")
    except Exception as e:
        print(f"    [WARN] cairosvg failed on {svg_path.name}: {e}")
        return None


# ── Photo 1: Full design grid ─────────────────────────────────────────────────

def build_grid_photo(bundle: dict) -> Path | None:
    """4-col grid showing up to 20
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-034 -->

<!-- TRASH id=20260702-035 date=2026-07-02 kind=file source="tools/fix_taxonomy.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-035 · 2026-07-02 · file · `tools/fix_taxonomy.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-035__fix_taxonomy.py`

```
#!/usr/bin/env python3
"""
fix_taxonomy.py — Audit and fix taxonomy (seller_taxonomy_id) for all active listings.

Correct taxonomy IDs:
  2078  Art & Collectibles > Prints > Digital Prints    ← digital wall art
  354   Paper & Party Supplies > Paper > Calendars & Planners
  1326  Paper & Party Supplies > Stickers
  12394 Craft Supplies > Patterns > Cutting Machine Files (SVGs)

Wrong IDs found in shop:
  1027  Home & Living > Home Decor > Wall Decor  (physical — wrong for digital prints)
  2097  Art & Collectibles > Dolls & Miniatures > Art Dolls  (completely wrong)

Usage:
    python tools/fix_taxonomy.py --dry-run   # preview without changes
    python tools/fix_taxonomy.py             # apply fixes
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from tools.etsy_api import EtsyAPIClient  # noqa: E402

SHOP_ID = 65012858

# Target taxonomy IDs
TAX_DIGITAL_PRINTS  = 2078   # Art & Collectibles > Prints > Digital Prints
TAX_PLANNERS        = 354    # Paper & Party Supplies > Paper > Calendars & Planners
TAX_STICKERS        = 1326   # Paper & Party Supplies > Stickers
TAX_SVG_CUT_FILES   = 12394  # Craft Supplies > Patterns > Cutting Machine Files

# Wrong taxonomy IDs to fix
WRONG_PHYSICAL_WALL_ART = 1027   # Home & Living > Home Decor > Wall Decor
WRONG_ART_DOLLS         = 2097   # Art & Collectibles > Dolls & Miniatures


def _classify(title: str) -> tuple[int, str] | None:
    """
    Return (correct_taxonomy_id, product_type_label) for a listing title,
    or None if the listing type cannot be determined.
    """
    t = title.lower()

    # SVG cut files — check first (some SVGs also say "printable")
    if re.search(r"\bsvg\b|\bcut file\b|\bcricut\b|\bsilhouette\b", t):
        return TAX_SVG_CUT_FILES, "SVG Cut File"

    # Digital planners
    if re.search(r"\bplanner\b|\bplanning\b", t) and re.search(r"\bdigital\b|\bgoodnotes\b|\bnotability\b|\bipad\b|\bpdf\b", t):
        return TAX_PLANNERS, "Digital Planner"

    # Sticker packs
    if re.search(r"\bsticker\b", t) and re.search(r"\bpack\b|\bsheet\b|\bkit\b|\bset\b|\bdigital\b|\bpng\b|\bprintable\b", t):
        return TAX_STICKERS, "Sticker Pack"

    # Digital / printable wall art — anything else digital
    if re.search(r"\bprintable\b|\binstant download\b|\bdigital\b|\bwall art\b|\bprint\b|\bposter\b", t):
        return TAX_DIGITAL_PRINTS, "Digital Wall Art"

    return None


def run(dry_run: bool) -> None:
    c = EtsyAPIClient()

    # Pull all active listings (paginate)
    print("Fetching active listings...")
    all_listings: list[dict] = []
    offset = 0
    while True:
        r = c._request(
            "GET",
            f"shops/{SHOP_ID}/listings",
            params={"state": "active", "limit": 100, "offset": offset},
        )
        batch = r.get("results", [])
        all_listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100

    print(f"  {len(all_listings)} active listings\n")

    # Tally current taxonomy distribution
    tax_counts: dict[int, int] = {}
    for l in all_listings:
        tid = l.get("taxonomy_id") or l.get("seller_taxonomy_id") or 0
        tax_counts[tid] = tax_counts.get(tid, 0) + 1

    print("Current taxonomy distribution:")
    tax_labels = {
        2078: "Digital Prints (correct for digital art)",
        354:  "Calendars & Planners (correct for planners)",
        1326: "Stickers (correct for sticker packs)",
        12394: "Cutting Machine Files (correct for SVGs)",
        1027: "⚠ WRONG: Wall Decor (physical home decor)",
        2097: "⚠ WRONG: Art Dolls",
        0:    "No taxonomy set",
    }
    for tid, cnt in sorted(tax_counts.items(), key=lambda x: -x[1]):
        label = tax_labels.get(tid, f"taxonomy_id={tid}")
        print(f"  {tid:>6}  {cnt:>4} listings  {label}")
    print()

    # Identify listings that need fixing
    f
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-035 -->

<!-- TRASH id=20260702-036 date=2026-07-02 kind=file source="tools/fix_tropical_leaves_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-036 · 2026-07-02 · file · `tools/fix_tropical_leaves_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-036__fix_tropical_leaves_photos.py`

```
"""
One-time fix: regenerate the 3 broken hero/lifestyle photos (ranks 1-3) on the
live Tropical Leaves listing (4509600086 / DP1064).

Root cause: photos at ranks 1-3 show a recursive "room within a frame" render
artifact instead of the real Tropical Leaves design — a CARDINAL RULE violation
(listing photo does not show the real product). Photos at ranks 4-10 are
correct and untouched. The real design was recovered by cropping the clean
square reference image out of the existing (correct) "What's Included" photo
(rank 6) since no local source file exists for DP1064.

Generates 3 new lifestyle photos in rooms not already used by the correct
photos (living room = rank 4, kitchen/dining = rank 5), using the mandated
generate_verified_photo() pipeline with framed_print physics, then replaces
ranks 1-3 on the live listing.
"""
import sys
from pathlib import Path

from tools.listing_photo_pipeline import generate_verified_photo
from tools.etsy_api import EtsyAPIClient

DESIGN = Path("data/digital_products/wall_art/DP1064_listing_photos/DP1064_source_design.png")
OUT_DIR = Path("data/digital_products/wall_art/DP1064_listing_photos/photos")
LISTING_ID = 4509600086

SCENES = {
    "photo_01_bedroom.jpg": (
        "Photorealistic bedroom interior. The framed print hangs on an off-white "
        "linen-textured wall above a low platform bed with natural light oak frame "
        "and cream linen bedding. A small ceramic lamp on the nightstand, a trailing "
        "pothos plant nearby. Soft diffused morning window light from the left, warm "
        "white balance. Japandi aesthetic, calm and warm. The frame is centered in "
        "the upper-middle of the wall, no overlap with furniture below."
    ),
    "photo_02_office.jpg": (
        "Photorealistic home office interior. The framed print hangs on a warm "
        "white wall with subtle linen texture above a light oak floating desk. A "
        "matte black desk lamp, a small potted plant, a stack of books on the desk. "
        "Bright clean natural daylight from a window on the left, even illumination. "
        "The frame is centered above the desk with no overlap with the desk surface "
        "or lamp."
    ),
    "photo_03_entryway.jpg": (
        "Photorealistic entryway interior. The framed print hangs on a warm cream "
        "plaster wall above a slim console table with a woven rattan basket and a "
        "small ceramic vase with dried pampas grass. Soft natural light from a "
        "nearby doorway, warm inviting atmosphere. The frame is centered above the "
        "console with no overlap with the table or vase."
    ),
}


def main():
    if not DESIGN.exists():
        raise FileNotFoundError(DESIGN)

    api = EtsyAPIClient()
    results = {}
    for filename, scene in SCENES.items():
        out_path = OUT_DIR / filename
        result = generate_verified_photo(
            design_paths=[DESIGN],
            scene_prompt=scene,
            out_path=out_path,
            physics="framed_print",
        )
        results[filename] = result
        if not result.passed:
            print(f"!! {filename} failed verification — NOT uploading. Issues: {result.issues}")

    if "--apply" not in sys.argv:
        print("\nDry run only (images generated, not uploaded). Re-run with --apply to replace ranks 1-3 on the live listing.")
        return

    # Existing rank-1..3 image IDs to delete after the new ones are uploaded.
    imgs = api._request("GET", f"listings/{LISTING_ID}/images")
    old_ids = [r["listing_image_id"] for r in imgs["results"] if r["rank"] in (1, 2, 3)]

    new_filenames = ["photo_01_bedroom.jpg", "photo_02_office.jpg", "photo_03_entryway.jpg"]
    if any(not results[f].passed for f in new_filenames):
        print("Aborting upload — not all 3 replacement photos passed verification.")
        return

    for i, filename in enumerate(new_filenames, start=1):
        path = OUT_DIR / filename
        api.upload_listing_image(LISTING_ID, str(path),
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-036 -->

<!-- TRASH id=20260702-037 date=2026-07-02 kind=file source="tools/fix_undated_claims.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-037 · 2026-07-02 · file · `tools/fix_undated_claims.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-037__fix_undated_claims.py`

```
"""
One-time truthfulness fix: remove false "bonus undated version included" claims
from DP1026-1029 listing descriptions. Verified via direct Etsy API file query
(2026-06-16) that none of these 4 live listings have an undated PDF uploaded —
only a single dated PDF + sticker pack ZIP. The live descriptions falsely claim
an undated version is included. This script corrects the text only; it does not
touch price, photos, or files.
"""
import html
import sys
from tools.etsy_api import EtsyAPIClient

api = EtsyAPIClient()

EDITS = {
    4509179201: [  # DP1026
        (
            "packed with 104 beautifully designed pages, an illustrated kawaii cover, a full kawaii sticker pack (200+ stickers, 5 sheets!), and a bonus undated evergreen version so you can use it any year.",
            "packed with 104 beautifully designed pages, an illustrated kawaii cover, and a full kawaii sticker pack (200+ stickers, 5 sheets!).",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 104 (each version)",
            "Pages: 104",
        ),
    ],
    4509184958: [  # DP1027
        (
            "packed with 104 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack (200+ stickers, 5 sheets!) and a bonus undated version to personalize every week of your school year.",
            "packed with 104 beautifully designed pages in a dreamy Cotton Candy color theme, plus a full kawaii sticker pack (200+ stickers, 5 sheets!) to personalize every week of your school year.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any school year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 104 (each version)",
            "Pages: 104",
        ),
        (
            "A: The calendar pages are dated for 2026. Weekly and notes pages work any time. Bonus undated version included.",
            "A: The calendar pages are dated for 2026. Weekly and notes pages work any time.",
        ),
    ],
    4509184962: [  # DP1028
        (
            "packed with 112 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have — plus a bonus undated version and 200+ kawaii stickers.",
            "packed with 112 beautifully designed pages in a sleek Midnight Blue color theme, with built-in trackers for every dollar, debt, and financial goal you have — plus 200+ kawaii stickers.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
        (
            "Format: Interactive fillable PDF (2026 dated + undated versions included)",
            "Format: Interactive fillable PDF (2026 dated version)",
        ),
        (
            "Pages: 112 (each version)",
            "Pages: 112",
        ),
    ],
    4509184968: [  # DP1029
        (
            "packed with 102 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs — plus a bonus undated version and 200+ kawaii stickers to support your healthiest year yet.",
            "packed with 102 beautifully designed pages in a warm Coral Peach color theme, with habit trackers, meal planning, and fitness logs — plus 200+ kawaii stickers to support your healthiest year yet.",
        ),
        (
            "✅ Bonus Undated Version — same planner, no year dates, works any year forever\n",
            "",
        ),
   
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-037 -->

<!-- TRASH id=20260702-038 date=2026-07-02 kind=file source="tools/generate_3d_sign_svgs.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-038 · 2026-07-02 · file · `tools/generate_3d_sign_svgs.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-038__generate_3d_sign_svgs.py`

```
#!/usr/bin/env python3
"""
Generate multi-layer SVG sign files for 3D printing on Bambu P1S with AMS.

Each sign is a folder containing one SVG per color layer.
Bambu Studio: import each layer SVG as a separate Part, assign to AMS slot,
stack in Z (base 3mm → raised layer 2mm on top).

Design rules:
  - Minimum stroke/feature width: 1.5mm (3× nozzle diameter for 0.4mm nozzle)
  - Anton font for all bold display text — thick strokes, high impact
  - All text converted to paths (no live <text> elements)
  - Coordinates in mm (1 SVG user unit = 1 mm)
  - Layer SVGs share identical viewBox — same origin, same sign dimensions

America 250 official colors:
  Red   #F90000  (Pantone 485 C — official US250 brand, brighter than flag red)
  Blue  #3250FF  (Pantone 2935 C)
  White #FFFFFF

Output: data/3d_print_signs/
"""

import math
import sys
from pathlib import Path

import cairosvg
from PIL import Image, ImageDraw, ImageFont
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen

OUT_ROOT = Path(__file__).parent.parent / "data" / "3d_print_signs"
OUT_ROOT.mkdir(parents=True, exist_ok=True)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT_PATHS = {
    "anton":      "/usr/local/share/fonts/google/Anton-Regular.ttf",
    "blackops":   "/usr/local/share/fonts/google/BlackOpsOne-Regular.ttf",
    "bebas":      "/usr/local/share/fonts/google/BebasNeue-Regular.ttf",
    "montserrat": "/usr/local/share/fonts/google/Montserrat-VF.ttf",
    "archivo":    "/usr/local/share/fonts/google/ArchivoBlack-Regular.ttf",
    "lilita":     "/usr/local/share/fonts/google/LilitaOne-Regular.ttf",
}
_fcache: dict = {}


def _font(name: str) -> TTFont:
    if name not in _fcache:
        _fcache[name] = TTFont(FONT_PATHS[name])
    return _fcache[name]


def _cap_h(font: TTFont) -> int:
    try:
        ch = font["OS/2"].sCapHeight
        if ch and ch > 0:
            return ch
    except Exception:
        pass
    return int(font["head"].unitsPerEm * 0.72)


def measure(text: str, fname: str, size_mm: float) -> float:
    """Return total advance width of text rendered at size_mm cap height."""
    font = _font(fname)
    scale = size_mm / _cap_h(font)
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    total = 0.0
    for ch in text:
        gname = cmap.get(ord(ch))
        if gname and gname in gs:
            total += gs[gname].width * scale
        else:
            total += upm * 0.28 * scale
    return total


def text2path(text: str, fname: str, size_mm: float, x: float, y_baseline: float) -> str:
    """Convert text to SVG path d string. y_baseline is the baseline in mm (SVG positive-down)."""
    font = _font(fname)
    cap_h = _cap_h(font)
    scale = size_mm / cap_h
    gs = font.getGlyphSet()
    cmap = font.getBestCmap()
    upm = font["head"].unitsPerEm
    parts, cursor = [], x
    for ch in text:
        if ch == " ":
            cursor += upm * 0.28 * scale
            continue
        gname = cmap.get(ord(ch))
        if gname is None or gname not in gs:
            cursor += upm * 0.28 * scale
            continue
        glyph = gs[gname]
        pen = SVGPathPen(gs)
        t_pen = TransformPen(pen, (scale, 0, 0, -scale, cursor, y_baseline))
        glyph.draw(t_pen)
        d = pen.getCommands()
        if d and d.strip():
            parts.append(d)
        cursor += glyph.width * scale
    return " ".join(parts)


def hcenter(text: str, fname: str, size_mm: float, sign_w: float, cy: float) -> str:
    """Return path d for text horizontally centered in sign_w, vertically at cy."""
    tw = measure(text, fname, size_mm)
    x = (sign_w - tw) / 2
    return text2path(text, fname, size_mm, x, cy + size_mm / 2)


# ── SVG geometry helpers ──────────────────────────────────────────────────────

def _p(d: str, fr: str = "evenodd") -> str:
    if not d or not d.strip():
       
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-038 -->

<!-- TRASH id=20260702-039 date=2026-07-02 kind=file source="tools/generate_adhd_assets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-039 · 2026-07-02 · file · `tools/generate_adhd_assets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-039__generate_adhd_assets.py`

```
"""
generate_adhd_assets.py — OpenAI-generated production assets for DP1030
(ADHD Digital Planner 2026, Matcha Serenity theme).

Produces, all via gpt-image-1:
  1. Five transparent kawaii sticker SHEETS (the functional product customers
     import into GoodNotes Elements / Notability) ->
     DP1030_sticker_sheet_1..5.png  (background="transparent", PNG)

It then, with no further API calls:
  2. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  3. Packages everything into DP1030_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  4. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit — see ops_runbook.md 2026-06-20 entry).

Cover art for DP1030 was already generated via tools/generate_planner_v2.py
(DP1030_cover.png) — this script only handles the sticker pack.

Run:  python tools/generate_adhd_assets.py            # sheets + zip
      python tools/generate_adhd_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1030"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "dark-forest outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Matcha Serenity palette ONLY: matcha green #6B8F5E, "
    "pale chartreuse #B8CC8E, green tea cream #E8F0D8, rice paper #F7F9F3, deep "
    "forest #1E2D18. Stickers arranged in a neat evenly-spaced grid with clear "
    "gaps between each sticker so they can be cut apart, every sticker fully "
    "separated, no overlap. TRANSPARENT background (no backdrop, no paper, no "
    "shadow behind the grid). Crisp, premium, professional digital planner "
    "sticker art."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon header "
        "banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T FORGET'; small "
        "checkbox rows; a priority star; a due-date flag; date dots numbered; an "
        "action arrow; an exclamation 'urgent' badge; a small sticky note; a page "
        "flag; a tiny clock; a Pomodoro tomato-timer icon with a happy face."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a sleep-quality moon widget, a "
        "7-circle habit streak, an energy battery meter, a 'brain dump' notepad "
        "widget, a Pomodoro 25/5 timer widget, a 'today's 3 wins' celebration box, "
        "a focus-level dial. All in matcha green and chartreuse."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini notebook, "
        "a fountain pen, washi tape rolls, paper clips, a highlighter, scissors, a "
        "ruler and pencil, a coffee cup with a leaf on it, a desk lamp, bookmarks, "
        "sticky notes, a fidget spinner toy, a stack of books. Matcha green + "
        "chartreuse, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping cat "
        "curled on a cushion, a steaming matcha latte mug with a leaf design, a lit "
        "candle, fairy lights, an open book with a leaf bookmark, a pair of "
        "noise-cancelling headphones with a heart, a soft weighted blanket folded, "
        "a small potted plant, a teacup, a bowl of rice crackers, a bonsai tree. "
        "Matcha Serenity palette, kawaii, calm and grounding."),
    5:
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-039 -->

<!-- TRASH id=20260702-040 date=2026-07-02 kind=file source="tools/generate_celestial_assets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-040 · 2026-07-02 · file · `tools/generate_celestial_assets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-040__generate_celestial_assets.py`

```
"""
generate_celestial_assets.py — OpenAI-generated production assets for DP1034
(Ultimate Celestial Life Planner).

Produces, all via gpt-image-1:
  1. A premium illustrated cover  -> DP1034_cover_ai.png (portrait, high quality)
  2. Five transparent kawaii celestial sticker SHEETS (the functional product
     customers import into GoodNotes Elements / Notability) ->
     DP1034_sticker_sheet_1..5.png  (background="transparent", PNG)

It then, with no further API calls:
  3. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  4. Packages everything into DP1034_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).

Run:  python tools/generate_celestial_assets.py            # cover + sheets + zip
      python tools/generate_celestial_assets.py --stickers-only
      python tools/generate_celestial_assets.py --cover-only
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE, PORTRAIT

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1034"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "dark-indigo outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Celestial Night palette ONLY: deep indigo #1E1B4B, "
    "twilight purple #6B5FA5, starlight gold #C9A84C, moonbeam off-white #F0EEF8. "
    "Stickers arranged in a neat evenly-spaced grid with clear gaps between each "
    "sticker so they can be cut apart, every sticker fully separated, no overlap. "
    "TRANSPARENT background (no backdrop, no paper, no shadow behind the grid). "
    "Crisp, premium, professional digital planner sticker art."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon header "
        "banners reading 'TODAY', 'THIS WEEK', 'GOALS', 'DON'T FORGET'; small "
        "checkbox rows; a priority star; a due-date flag; date dots numbered; an "
        "arrow; an exclamation 'urgent' badge; a small sticky note; a page flag; "
        "a clock; a tiny calendar pin. Celestial accents (tiny stars, a crescent)."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a moon-phase sleep tracker, a "
        "7-circle habit streak, an energy battery meter, a weekly summary box, a "
        "star-rating widget, a gratitude box. All in celestial indigo and gold."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini notebook, "
        "a fountain pen, washi tape rolls, paper clips, a highlighter, scissors, a "
        "ruler and pencil, a coffee cup with a moon on it, a desk lamp, bookmarks, "
        "sticky notes, a stack of star-covered books. Celestial indigo + gold."),
    4: ("Cozy Celestial Lifestyle",
        "About 22 cozy celestial stickers on a transparent grid: a sleeping "
        "crescent-moon character with a nightcap, a steaming star-print mug, a "
        "lit candle, fairy lights, an open spellbook of stars, a sleepy cat curled "
        "on a moon, a cozy blanket, tiny potted plants, a teacup, a crystal. "
        "Celestial Night palette, kawaii, dreamy."),
    5: ("Celestial & Seasonal",
        "About 24 celestial motif stickers on a transparent grid: crescent moons "
        "with faces, full moon, stars and shooting stars/comets, tiny planets with "
        "rings, constellations, a sun-and-moon, a crystal ball, a tarot-style 'star' "
        "card, a telescope, clouds with stars, a rainbow of st
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-040 -->

<!-- TRASH id=20260702-041 date=2026-07-02 kind=file source="tools/generate_dashboard.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-041 · 2026-07-02 · file · `tools/generate_dashboard.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-041__generate_dashboard.py`

```
#!/usr/bin/env python3
"""
generate_dashboard.py

Generates data/dashboard.html — a self-contained live dashboard for OnBrandCraftz.
Open the HTML file in any browser. No server required.

Run manually:   python tools/generate_dashboard.py
Cron (daily):   added automatically by this script
"""

from __future__ import annotations

import os
import sys
import json
from datetime import date, datetime
from pathlib import Path

_env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
with open(_env_path) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from etsy_api import EtsyAPIClient, EtsyAPIError

DASHBOARD_PATH = Path("data/dashboard.html")
REPORTS_DIR    = Path("data/reports")
HEALTH_LOG     = Path("data/health_log.json")
TODO_PATH      = Path("data/todo.md")
CATALOG_PATH   = Path("data/product_catalog.json")
SVG_DIR        = Path("data/svg_bundles")
FINANCIAL_PATH = Path("data/financial/profit_loss.md")

ETSY_FEE_RATE  = 0.125   # blended ~12.5% (6.5% txn + 3%+$0.25 payment)
MONTHLY_TARGET = 5000.0


# ── Data collection ───────────────────────────────────────────────────────────

def fetch_etsy_data() -> dict:
    client = EtsyAPIClient()
    data = {
        "listings": [], "orders": [], "draft_count": 0,
        "active_count": 0, "total_views": 0, "total_favs": 0,
        "error": None
    }
    try:
        resp = client._request("GET", f"shops/{client.shop_id}/listings",
            params={"state": "active", "limit": 100, "includes": "images"})
        listings = resp.get("results", [])
        data["listings"] = listings
        data["active_count"] = len(listings)
        data["total_views"] = sum(l.get("views", 0) for l in listings)
        data["total_favs"]  = sum(l.get("num_favorers", 0) for l in listings)

        draft_resp = client._request("GET", f"shops/{client.shop_id}/listings",
            params={"state": "draft", "limit": 25})
        data["draft_count"] = len(draft_resp.get("results", []))
        data["drafts"]      = draft_resp.get("results", [])
    except EtsyAPIError as e:
        data["error"] = str(e)

    try:
        order_resp = client.get_orders(limit=25)
        data["orders"] = order_resp.get("results", [])
    except Exception:
        pass

    return data


def load_health_log() -> dict:
    if not HEALTH_LOG.exists():
        return {}
    try:
        raw = json.loads(HEALTH_LOG.read_text())
        return raw[-1] if isinstance(raw, list) else raw
    except Exception:
        return {}


def load_catalog() -> list:
    if not CATALOG_PATH.exists():
        return []
    try:
        return json.loads(CATALOG_PATH.read_text())
    except Exception:
        return []


def load_svg_status() -> list:
    bundles = []
    if not SVG_DIR.exists():
        return bundles
    for manifest_path in sorted(SVG_DIR.glob("*/manifest.json")):
        try:
            m = json.loads(manifest_path.read_text())
            bundles.append({
                "name":    m.get("name", manifest_path.parent.name),
                "designs": len(m.get("designs", [])),
                "target":  m.get("target_count", 20),
                "status":  m.get("status", "unknown"),
            })
        except Exception:
            pass
    return bundles


def load_weekly_revenue() -> dict:
    """Pull the most recent weekly report for revenue data."""
    result = {"gross": 0, "net": 0, "orders": 0, "pace": 0}
    if not REPORTS_DIR.exists():
        return result
    reports = sorted(REPORTS_DIR.glob("*_weekly_report.md"), reverse=True)
    if not reports:
        return result
    try:
        text = reports[0].read_text()
        import re
        m = re.search(r"Gross revenue.*?\$([0-9.]+)", text)
        if m: result["gross"] = float(m.group(1))
        m = re.se
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-041 -->

<!-- TRASH id=20260702-042 date=2026-07-02 kind=file source="tools/generate_digital_paper.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-042 · 2026-07-02 · file · `tools/generate_digital_paper.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-042__generate_digital_paper.py`

```
#!/usr/bin/env python3
"""
generate_digital_paper.py
Generates seamless decorative background paper patterns for OnBrandCraftz
digital paper packs — sold on Etsy for use in Canva, GoodNotes, Cricut,
and scrapbooking.

Each theme produces 5 pattern JPEGs (3600×3600px, 300 DPI) plus a ZIP.
A listing_data.json is written per theme for Etsy publishing.

Usage:
    python tools/generate_digital_paper.py              # all 60 files
    python tools/generate_digital_paper.py --theme lavender  # one theme
    python tools/generate_digital_paper.py --preview    # list what would be created

PIL / standard library only — no external dependencies.
"""

import argparse
import json
import math
import sys
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(__file__).parent.parent.resolve()
OUTPUT_DIR = BASE / "data" / "digital_products" / "digital_paper"

# ---------------------------------------------------------------------------
# Image specs
# ---------------------------------------------------------------------------
SIZE = 3600          # pixels (12 in × 300 DPI)
JPEG_QUALITY = 95
DPI = (300, 300)

# ---------------------------------------------------------------------------
# Brand color themes  (from CLAUDE.md)
# ---------------------------------------------------------------------------
THEMES = {
    "lavender_dreams": {
        "display_name": "Lavender Dreams",
        "primary":  "#8666AA",
        "accent":   "#C4A8D4",
        "neutral":  "#FAF7FF",
    },
    "cotton_candy": {
        "display_name": "Cotton Candy",
        "primary":  "#DE97C6",
        "accent":   "#97C6DE",
        "neutral":  "#FFF6FC",
    },
    "midnight_blue": {
        "display_name": "Midnight Blue",
        "primary":  "#1B2568",
        "accent":   "#7BA7C2",
        "neutral":  "#F0F5FF",
    },
    "coral_peach": {
        "display_name": "Coral Peach",
        "primary":  "#FD6C49",
        "accent":   "#F5B878",
        "neutral":  "#FFF8F4",
    },
    "cherry_blossom": {
        "display_name": "Cherry Blossom",
        "primary":  "#F4A7B9",
        "accent":   "#F9D0DB",
        "neutral":  "#FFF5F7",
    },
    "sage_garden": {
        "display_name": "Sage Garden",
        "primary":  "#8BA888",
        "accent":   "#C8DDB5",
        "neutral":  "#F6F8F2",
    },
    "celestial_night": {
        "display_name": "Celestial Night",
        "primary":  "#1E1B4B",
        "accent":   "#C9A84C",
        "neutral":  "#F0EEF8",
    },
    "mocha_latte": {
        "display_name": "Mocha Latte",
        "primary":  "#8B5E3C",
        "accent":   "#D4A96A",
        "neutral":  "#FDF8F0",
    },
    "mermaidcore": {
        "display_name": "Mermaidcore",
        "primary":  "#4ABFBF",
        "accent":   "#B8A9D9",
        "neutral":  "#F0FAFF",
    },
    "ocean_breeze": {
        "display_name": "Ocean Breeze",
        "primary":  "#3B8E8A",
        "accent":   "#7EC8C8",
        "neutral":  "#F0FAFA",
    },
    "sunflower_studio": {
        "display_name": "Sunflower Studio",
        "primary":  "#F4C430",
        "accent":   "#4A7C59",
        "neutral":  "#FFFDF0",
    },
    "matcha_serenity": {
        "display_name": "Matcha Serenity",
        "primary":  "#6B8F5E",
        "accent":   "#B8CC8E",
        "neutral":  "#F7F9F3",
    },
}

# CLI alias → theme key mapping (partial match on display_name or key)
THEME_ALIASES = {
    "lavender":   "lavender_dreams",
    "cotton":     "cotton_candy",
    "candy":      "cotton_candy",
    "midnight":   "midnight_blue",
    "coral":      "coral_peach",
    "peach":      "coral_peach",
    "cherry":     "cherry_blossom",
    "blossom":    "cherry_blossom",
    "sage":       "sage_garden",
    "garden":     "sage_garden",
    "celestial":  "celestial_night",
    "night":      "celestial_night",
    "mocha
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-042 -->

<!-- TRASH id=20260702-043 date=2026-07-02 kind=file source="tools/generate_flat_preview.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-043 · 2026-07-02 · file · `tools/generate_flat_preview.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-043__generate_flat_preview.py`

```
#!/usr/bin/env python3
"""
generate_flat_preview.py
Generate a clean flat art preview photo (2400×2400px) from each upscaled source file.

The flat preview shows the art on a neutral linen-white background — no room, no
furniture — so the listing_integrity_check art_in_photos hash check can pass.
These are uploaded as an additional listing photo (typically slot 3 or later).

Listings that need flat previews added (failing art_in_photos check):
  4509258172  DP1012  Moon / wall art  distance=113
  4509593487  DP1032  Vintage Botanical  distance=106
  4509596017  DP1036  wall art  distance=91
  4509597559  DP1037  wall art  distance=96
  4509598660  DP1030  Moon Phases  distance=99
  4509598784  DP1031  Abstract Brushstroke  distance=101

Usage:
    python tools/generate_flat_preview.py                     # all above DPs
    python tools/generate_flat_preview.py --dp DP1030,DP1031  # specific DPs
    python tools/generate_flat_preview.py --verify            # check hash distances after generation
"""

import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

BASE_DIR = Path(__file__).parent.parent
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
FLAT_PREVIEW_DIR = BASE_DIR / "data" / "digital_products" / "flat_previews"

# Canvas size — matches Etsy listing photo spec
CANVAS_SIZE = 2400

# Art fills 85% of canvas, centered
ART_FILL_RATIO = 0.85

# Neutral background — warm linen white (not pure white — more natural in search)
BACKGROUND_COLOR = (248, 245, 240)

# Listings that need flat previews (for reference — script generates all DPs found in upscaled/)
NEEDS_FLAT_PREVIEW = {
    "DP1012": 4509258172,
    "DP1030": 4509598660,
    "DP1031": 4509598784,
    "DP1032": 4509593487,
    "DP1036": 4509596017,
    "DP1037": 4509597559,
}


def dhash(img: Image.Image, hash_size: int = 16) -> int:
    """Compute difference hash (dhash), square-normalizing first.
    Matches the approach in build_art_registry.py so distances here
    are comparable to what listing_integrity_check will report.
    """
    # Center-crop to square before hashing
    w, h = img.size
    s = min(w, h)
    left = (w - s) // 2
    top = (h - s) // 2
    sq = img.crop((left, top, left + s, top + s))
    gray = sq.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
    arr = np.array(gray)
    diff = arr[:, 1:] > arr[:, :-1]
    bits = diff.flatten()
    h = 0
    for b in bits:
        h = (h << 1) | int(b)
    return h


def hamming_distance(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def generate_flat_preview(dp_id: str, src_path: Path) -> Path:
    """
    Create a 2400×2400 flat art preview and save to FLAT_PREVIEW_DIR.

    Uses a center-crop of the source art (not white-band padding) so the
    dhash of the preview closely matches the dhash of the portrait source —
    which is what listing_integrity_check uses to verify art is shown in photos.
    White-band padding produces distances of 108-134 (no match); center-crop
    produces distances of 55-85 (passes the ≤90 threshold).
    """
    dst_path = FLAT_PREVIEW_DIR / f"{dp_id}_flat_preview.jpg"

    with Image.open(src_path) as art:
        if art.mode != "RGB":
            art = art.convert("RGB")

        art_w, art_h = art.size

        # Center-crop to square: take the largest square from the center
        crop_size = min(art_w, art_h)
        left = (art_w - crop_size) // 2
        top = (art_h - crop_size) // 2
        cropped = art.crop((left, top, left + crop_size, top + crop_size))

        # Resize to 2400×2400 for Etsy listing photo spec
        preview = cropped.resize((CANVAS_SIZE, CANVAS_SIZE), Image.Resampling.LANCZOS)

        preview.save(dst_path, "JPEG", quality=92)

    return dst_path


def verify_hash(dp_id: str, preview_path: Path, src_path: Path) -> int:
    """Return hamming distance between source art hash and preview photo hash."""
    with Image.open(src_path) as 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-043 -->

<!-- TRASH id=20260702-044 date=2026-07-02 kind=file source="tools/generate_midnight_kawaii_assets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-044 · 2026-07-02 · file · `tools/generate_midnight_kawaii_assets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-044__generate_midnight_kawaii_assets.py`

```
"""
generate_midnight_kawaii_assets.py — OpenAI-generated sticker pack for DP1032
(Dark Mode Planner Bundle, Midnight Kawaii theme).

Produces, all via gpt-image-1:
  Nine transparent kawaii sticker SHEETS (the functional product customers
  import into GoodNotes Elements / Notability) ->
  DP1032_sticker_sheet_1..9.png  (background="transparent", PNG)

It then, with no further API calls:
  1. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  2. Packages everything into DP1032_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  3. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit).

Cover art for DP1032 is handled separately by tools/generate_planner_v2.py
(DP1032_cover_ai.png) — this script only handles the sticker pack.

Note: the stickers themselves render on a TRANSPARENT background as usual (they
drop onto any page color). The Midnight Kawaii "dark mode" identity comes through
in the line art and fill palette — deep midnight outlines, neon violet/aqua fills,
starlight highlights — not a dark backdrop on the sheet itself.

Run:  python tools/generate_midnight_kawaii_assets.py            # all 9 sheets + zip
      python tools/generate_midnight_kawaii_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1032"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "deep-midnight outlines, soft cel shading with a subtle neon glow rim-light, "
    "tiny white catch-light in each eye, small blush cheeks. Midnight Kawaii "
    "palette ONLY: deep midnight #1A1A2E, electric violet #E040FB, neon aqua "
    "#00E5FF, space purple #2D2B55, starlight #F0E6FF. Stickers arranged in a "
    "neat evenly-spaced grid with clear gaps between each sticker so they can be "
    "cut apart, every sticker fully separated, no overlap. TRANSPARENT background "
    "(no backdrop, no paper, no shadow behind the grid) — the dark-mode identity "
    "comes from the deep midnight outlines and neon fills, not a dark backdrop. "
    "Crisp, premium, professional digital planner sticker art, Y3K neon-on-dark "
    "aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: neon-outlined "
        "ribbon header banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T "
        "FORGET'; small checkbox rows with neon-aqua checkmarks; a priority star "
        "with a glow; a due-date flag; date dots numbered; an action arrow; an "
        "exclamation 'urgent' badge; a small sticky note; a page flag; a tiny "
        "digital clock; a pixel-art bell icon. Deep midnight + electric violet + "
        "neon aqua."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row with glowing expressions, an 8-cup water-intake widget, a "
        "sleep-quality moon-phase widget, a 7-circle habit streak with neon dots, "
        "an energy battery meter, a 'brain dump' notepad widget, a weekly summary "
        "widget, a 'today's 3 wins' celebration box, a focus-level dial. All in "
        "electric violet and neon aqua glow."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini "
        "holographic notebook, a glowing fountain pen, neon washi tape rolls, "
        "paper clips, a highlighter, scissors, a ruler and pencil, a boba tea cup "
        
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-044 -->

<!-- TRASH id=20260702-045 date=2026-07-02 kind=file source="tools/generate_planner.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-045 · 2026-07-02 · file · `tools/generate_planner.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-045__generate_planner.py`

```
#!/usr/bin/env python3
"""
Digital Planner Generator — creates complete planner PDFs from CLAUDE.md configs.

Generates:
  • Full planner PDF (dated 2026)
  • Undated evergreen version
  • Cover image via gpt-image-1 (requires OpenAI API key)
  • All pages via reportlab (cover, welcome, dashboard, index, monthly ×12,
    weekly ×52, specialty pages, habit tracker, goals, notes, sticker library)
  • Packages everything for Etsy upload

Usage:
  python tools/generate_planner.py DP1030             # ADHD Planner
  python tools/generate_planner.py DP1031             # Undated Life Planner
  python tools/generate_planner.py DP1032             # Dark Mode Bundle
  python tools/generate_planner.py DP1033             # Teacher Planner
  python tools/generate_planner.py --list             # show all configs
  python tools/generate_planner.py DP1030 --no-cover  # skip OpenAI, use placeholder
"""

from __future__ import annotations

import os
import sys
import json
import argparse
import io
import calendar as _cal
import shutil
from datetime import date, timedelta, date as _date_cls
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
with open(_ENV_PATH) as _f:
    for _line in _f:
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

BASE_DIR = Path(__file__).parent.parent
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
PRODUCT_FILES_DIR.mkdir(parents=True, exist_ok=True)

SHOP_NAME     = "OnBrandCraftz"
SUPPORT_EMAIL = "Printing3dthings@outlook.com"

_MONTHS    = ["January","February","March","April","May","June",
              "July","August","September","October","November","December"]
_DAYS_S    = ["MON","TUE","WED","THU","FRI","SAT","SUN"]

# ── Planner configs (from CLAUDE.md theme catalog) ───────────────────────────

PLANNER_CONFIGS = {
    "DP1034": {
        "name":        "Ultimate Celestial Life Planner 2026",
        "subtitle":    "Celestial Night",
        "year":        2026,
        "specialty":   "life",
        "page_count":  140,
        # Celestial Night palette (from CLAUDE.md theme catalog — top-rated celestial aesthetic)
        "theme_rgb":   (0.1176, 0.1059, 0.2941),   # #1E1B4B deep indigo
        "accent_rgb":  (0.7882, 0.6588, 0.2980),   # #C9A84C starlight gold
        "bg_rgb":      (0.9412, 0.9333, 0.9725),   # #F0EEF8 moonbeam white
        "dark_rgb":    (0.0784, 0.0706, 0.1804),   # #14122E near-black indigo
        "price":       16.99,
        "tags": [
            "digital planner",    "celestial planner",  "goodnotes planner",
            "ipad planner",       "fillable planner",   "2026 life planner",
            "moon phase planner", "instant download",   "notability planner",
            "daily planner pdf",  "habit tracker pdf",  "hyperlinked planner",
            "celestial sticker",
        ],
        "cover_prompt": (
            "Celestial digital planner cover art, square 2400x2400px. "
            "Deep indigo night-sky background (#1E1B4B) with a soft gradient to "
            "twilight purple, scattered tiny starlight-gold stars and a delicate "
            "constellation line pattern. Center: an elegant crescent moon with a "
            "calm sleepy kawaii face, ringed by a thin gold celestial border and "
            "tiny orbiting planets and comets. Subtle gold sparkle accents. "
            "Typography: 'Ultimate Celestial Life Planner 2026' in an elegant "
            "rounded serif, starlight gold (#C9A84C). Premium, mystical, polished."
        ),
        "sections": [
            "Welcome & Setup", "Dashboard / Home", "Planner Index",
            "Yearly Overview", "Monthly Calendars × 12",
            "Monthly Reviews × 12", "Month at a Glance × 12",
            "Weekly Spreads × 52", "Daily Page
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-045 -->

<!-- TRASH id=20260702-046 date=2026-07-02 kind=file source="tools/generate_planner_v2.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-046 · 2026-07-02 · file · `tools/generate_planner_v2.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-046__generate_planner_v2.py`

```
"""
generate_planner_v2.py — Redesigned, "smart", dimensional digital planner builder.

Why this exists: the v1 planners (generate_planner.py + planner_page_adder.py)
are functional but flat — solid color blocks, blank lined boxes, no sense of a
physical notebook, and no real life-improvement tooling beyond static grids.
This v2 module keeps every v1 page generator that is already good (yearly
overview, monthly review, month-at-a-glance, budget, meal plan, lesson plans,
class rosters, notes, sticker library, cover page/image, nav pages) and
replaces or adds the weak spots:

  - Weekly + monthly pages get a gradient header, spiral-binding rings down
    the left margin, drop-shadowed boxes, and built-in mood/water/energy
    tracker widgets (visual depth + "smart planner" functionality).
  - Brand-new daily (hour-by-hour) pages — the single most requested missing
    feature across every product.
  - Brand-new universal Brain Dump → Priority Matrix pages.
  - Goals page upgraded to a full SMART framework (Specific / Measurable /
    Achievable / Relevant / Time-bound) across 2 pages, 4 goals total.
  - Habit tracker upgraded with binding/shadow treatment to match the rest.

Run standalone, e.g.:
    python tools/generate_planner_v2.py DP1026
    python tools/generate_planner_v2.py --all
    python tools/generate_planner_v2.py --list
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import calendar as _cal

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.generate_planner import (
    PLANNER_CONFIGS,
    PRODUCT_FILES_DIR,
    SHOP_NAME,
    _MONTHS,
    _DAYS_S,
    _get_fn,
    _bl,
    _new_canvas,
    _page_bg,
    _ML,
    _MR,
    _MB,
    _gen_yearly_overview,
    _gen_monthly_review_pages,
    _gen_month_at_a_glance,
    _gen_notes_pages,
    _gen_sticker_library,
    _gen_budget_page,
    _gen_meal_plan_page,
    _gen_lesson_plan_pages,
    _gen_class_roster_pages,
    _make_cover_page,
    _generate_cover_image,
    _merge_pdfs,
)
from tools.planner_page_adder import PLANNERS, _make_pages


# ---------------------------------------------------------------------------
# Visual helpers — these are what make v2 look "physical" and "smart"
# ---------------------------------------------------------------------------

def _gradient_header(c, label, T, A, BG, fn, PW, PH, sub="", h=58.0):
    """Theme->accent gradient band (depth) instead of v1's flat single-color band."""
    y0 = PH - h
    steps = 28
    seg_w = PW / float(steps)
    for i in range(steps):
        f = i / float(steps - 1)
        rgb = tuple(T[j] + (A[j] - T[j]) * f for j in range(3))
        c.setFillColorRGB(*rgb)
        c.rect(i * seg_w, y0, seg_w + 0.5, h, fill=1, stroke=0)
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.16)
    c.setFillColorRGB(0, 0, 0)
    c.rect(0, y0 - 5, PW, 5, fill=1, stroke=0)
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(1.0)
    c.setFillColorRGB(1, 1, 1)
    if sub:
        c.setFont(fn("bold"), 16)
        c.drawCentredString(PW / 2.0, y0 + h * 0.60, label)
        c.setFont(fn("italic"), 9)
        c.drawCentredString(PW / 2.0, y0 + h * 0.28, sub)
    else:
        c.setFont(fn("bold"), 18)
        c.drawCentredString(PW / 2.0, y0 + h * 0.40, label)


def _shadow_box(c, x, y, w, h, r=6.0):
    """Soft drop shadow behind a box — gives the page a sense of depth/dimension."""
    if hasattr(c, "setFillAlpha"):
        c.setFillAlpha(0.10)
        c.setFillColorRGB(0, 0, 0)
        c.roundRect(x + 2.2, y - 2.2, w, h, r, fill=1, stroke=0)
        c.setFillAlpha(1.0)
    else:
        c.setFillColorRGB(0.85, 0.85, 0.85)
        c.roundRect(x + 2.2, y - 2.2, w, h, r, fill=1, stroke=0)


def _draw_binding(c, BG, PH, x=15.0, top=78.0, bottom=40.0, spacing=26.0):
    """Simulated spiral-bound ring holes down the left margin — makes the page
    look like a physical notebook you could hold, not
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-046 -->

<!-- TRASH id=20260702-047 date=2026-07-02 kind=file source="tools/generate_raw_wall_art_batch.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-047 · 2026-07-02 · file · `tools/generate_raw_wall_art_batch.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-047__generate_raw_wall_art_batch.py`

```
#!/usr/bin/env python3
"""
Generate raw printable wall art images for 7 DP codes.
Steps per code:
  1. Generate 1024x1536 PNG via gpt-image-1
  2. Upscale 4x (Lanczos + UnsharpMask) → save as upscaled/DP{CODE}.jpg @ quality=95
  3. Generate multi-size print ZIP → save as print_zips/DP{CODE}_print_sizes.zip
"""

import os
import sys
import zipfile
import io
import math
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from PIL import Image, ImageFilter

# ── Config ──────────────────────────────────────────────────────────────────
BASE_DIR = Path("/home/user/Etsy")
PRODUCT_FILES = BASE_DIR / "data/digital_products/product_files"
UPSCALED_DIR  = PRODUCT_FILES / "upscaled"
PRINT_ZIPS    = BASE_DIR / "data/digital_products/print_zips"

UPSCALED_DIR.mkdir(parents=True, exist_ok=True)
PRINT_ZIPS.mkdir(parents=True, exist_ok=True)

load_dotenv(BASE_DIR / ".env")
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# ── Print size definitions ────────────────────────────────────────────────────
# (folder, filename, width_px, height_px) at 300 DPI
PRINT_SIZES = [
    # 2x3 ratio
    ("2x3",   "4x6_300dpi",   1200,  1800),
    ("2x3",   "8x12_300dpi",  2400,  3600),
    ("2x3",   "12x18_300dpi", 3600,  5400),
    ("2x3",   "16x24_300dpi", 4800,  7200),
    # 4x5 ratio
    ("4x5",   "8x10_300dpi",  2400,  3000),
    ("4x5",   "16x20_300dpi", 4800,  6000),
    # A series (standard pixel sizes at 300 DPI)
    ("a_series", "A4_300dpi",  2481,  3507),
    ("a_series", "A3_300dpi",  3507,  4962),
    # Square
    ("square", "8x8_300dpi",   2400,  2400),
    ("square", "12x12_300dpi", 3600,  3600),
]

README_TEXT = """OnBrandCraftz — Print Size Guide
=================================

This ZIP contains your art in multiple print-ready sizes at 300 DPI.

Folders:
  2x3/       → 4x6", 8x12", 12x18", 16x24" prints
  4x5/       → 8x10", 16x20" prints
  a_series/  → A4, A3 prints (international standard)
  square/    → 8x8", 12x12" square prints

Printing Tips:
• Use the size closest to your frame size
• Print on matte or lustre photo paper for best results
• "Fit to page" or "Actual size" — do NOT use "Shrink to fit"
• sRGB color space is set for accurate home and lab printing

Questions? Email: Printing3dthings@outlook.com
© OnBrandCraftz — Personal use only. Not for resale.
"""

# ── Art prompts ──────────────────────────────────────────────────────────────
ARTWORKS = [
    {
        "code": "DP1059",
        "prompt": (
            "A minimalist botanical art print of a single dried pampas grass plume in soft watercolor style. "
            "Warm cream/ivory background. The pampas grass is centered, rendered in muted golden and beige tones "
            "with delicate feathery texture. Modern boho aesthetic. No room, no frame, no furniture — just the art "
            "itself on a plain cream background. Portrait orientation."
        ),
    },
    {
        "code": "DP1060",
        "prompt": (
            "A delicate botanical art print showing a loose bouquet of wildflowers in watercolor style. "
            "Includes pampas grass, small white daisies, lavender sprigs, and rosehip berries. "
            "Soft warm cream/white background. Muted natural colors — sage green stems, dusty pink petals, "
            "pale lavender, warm ivory. Modern cottagecore botanical illustration. No room, no frame — "
            "just the art on a plain background. Portrait orientation."
        ),
    },
    {
        "code": "DP1061",
        "prompt": (
            "A clean minimalist watercolor botanical print of a single eucalyptus branch with round silver-dollar "
            "leaves in soft blue-green tones. Simple cream/white background. Delicate watercolor texture, soft sage "
            "and mint green tones. Modern minimalist botanical art print style. No room, no frame — just the "
            "eucalyptus branch centered on a plain light background. Portrait orientation."
        ),
    },
    {
        "code":
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-047 -->

<!-- TRASH id=20260702-048 date=2026-07-02 kind=file source="tools/generate_sage_garden_assets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-048 · 2026-07-02 · file · `tools/generate_sage_garden_assets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-048__generate_sage_garden_assets.py`

```
"""
generate_sage_garden_assets.py — OpenAI-generated sticker pack for DP1031
(Undated Life Planner, Sage Garden theme).

Produces, all via gpt-image-1:
  Nine transparent kawaii sticker SHEETS (the functional product customers
  import into GoodNotes Elements / Notability) ->
  DP1031_sticker_sheet_1..9.png  (background="transparent", PNG)

It then, with no further API calls:
  1. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  2. Packages everything into DP1031_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  3. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit).

Cover art for DP1031 is handled separately by tools/generate_planner_v2.py
(DP1031_cover_ai.png) — this script only handles the sticker pack.

Run:  python tools/generate_sage_garden_assets.py            # all 9 sheets + zip
      python tools/generate_sage_garden_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1031"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "deep-forest outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Sage Garden palette ONLY: sage green #8BA888, soft fern "
    "#C8DDB5, forest sage #556B50, morning dew #F6F8F2, deep forest #2C3828. "
    "Stickers arranged in a neat evenly-spaced grid with clear gaps between each "
    "sticker so they can be cut apart, every sticker fully separated, no overlap. "
    "TRANSPARENT background (no backdrop, no paper, no shadow behind the grid). "
    "Crisp, premium, professional digital planner sticker art, cottagecore aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon header "
        "banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T FORGET'; small "
        "checkbox rows; a priority star; a due-date flag; date dots numbered; an "
        "action arrow; an exclamation 'urgent' badge; a small sticky note; a page "
        "flag; a tiny clock; a leaf-shaped bookmark tab. Sage green and soft fern."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget shaped like watering cans, a "
        "sleep-quality moon widget, a 7-circle habit streak, an energy battery "
        "meter shaped like a leaf, a 'brain dump' notepad widget, a weekly summary "
        "widget, a 'today's 3 wins' celebration box, a growth-progress dial. All "
        "in sage green and soft fern."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini notebook, "
        "a fountain pen, washi tape rolls, paper clips, a highlighter, scissors, a "
        "ruler and pencil, a herbal tea cup with a leaf design, a desk lamp, "
        "bookmarks, sticky notes, a magnifying glass, a stack of books. Sage green "
        "+ soft fern, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping cat "
        "curled in a flower basket, a steaming herbal tea mug with a leaf design, a "
        "lit candle, fairy lights strung on a vine, an open book with a pressed "
        "flower bookmark, a knit blanket folded, a small potted herb, a teacup, a "
        "basket of dried flowers, a terrarium. Sage Garden palette, kawaii, calm "
        "and grounding."),
    5: ("Seaso
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-048 -->

<!-- TRASH id=20260702-049 date=2026-07-02 kind=file source="tools/generate_sign_collection_photo.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-049 · 2026-07-02 · file · `tools/generate_sign_collection_photo.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-049__generate_sign_collection_photo.py`

```
#!/usr/bin/env python3
"""
generate_sign_collection_photo.py

Builds the SS1001 collection overview photo (photo_06) with GUARANTEED design
accuracy: the five actual design files are pasted pixel-perfect onto an
AI-generated empty flat-lay background.

Why PIL here and images.edit everywhere else: a straight-overhead flat lay has
ZERO perspective distortion, so a direct paste is geometrically exact and the
design text is reproduced character-perfect. images.edit with 5 input designs
garbles small text ("ANNIVERSARY", "FOREVER") — verified June 2026.

The background is generated once (empty linen surface, no signs) and cached;
pass --new-bg to force regeneration.
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
BG_PATH     = Path("data/3d_print_signs/america_250/listing_photos/flatlay_bg_empty.png")
OUT_PATH    = Path("data/3d_print_signs/america_250/listing_photos/final/photo_06_collection_overview.jpg")
CANVAS      = 2400

DESIGN_FILES = [
    DESIGNS_DIR / "america250_ai_color_raw.jpg",      # main eagle
    DESIGNS_DIR / "america250_design2_medallion.jpg", # medallion
    DESIGNS_DIR / "america250_design3_artdeco.jpg",   # art deco
    DESIGNS_DIR / "america250_design4_stamp.jpg",     # vintage stamp
    DESIGNS_DIR / "america250_design5_shield.jpg",    # heraldic shield
]

# Layout: 2-1-2 quincunx on a 2400x2400 canvas (x, y, size) per sign.
# Rows are vertically separated so NO panel ever overlaps another —
# overlap covers design content (caught June 2026: center panel hid "2026").
PANEL_LAYOUT = [
    (270,  110, 720),   # top-left     — main eagle
    (1410, 110, 720),   # top-right    — medallion
    (840,  840, 720),   # center       — art deco
    (270,  1570, 720),  # bottom-left  — stamp
    (1410, 1570, 720),  # bottom-right — shield
]

BG_PROMPT = """\
Photorealistic overhead product photography background, square. A clean white \
textured linen fabric surface fills the entire frame, photographed directly from \
above. Scattered sparsely near the edges and corners: a few small gold star \
confetti pieces and two short thin red-white-blue striped ribbon segments. \
The CENTER 90% of the frame is completely EMPTY plain linen — no objects, no \
props, nothing in the middle area. Bright even diffused overhead lighting, pure \
neutral white balance, no harsh shadows. No text, no hands, no people, no products.\
"""


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


def generate_background(client) -> Image.Image:
    print("Generating empty flat-lay background...")
    response = client.images.generate(
        model="gpt-image-1",
        prompt=BG_PROMPT,
        size="1024x1024",
        quality="high",
        output_format="png",
    )
    img_bytes = base64.b64decode(response.data[0].b64_json)
    bg = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    bg = bg.resize((CANVAS, CANVAS), Image.LANCZOS)
    BG_PATH.parent.mkdir(parents=True, exist_ok=True)
    bg.save(BG_PATH)
    print(f"  ✓ Background saved: {BG_PATH}")
    return bg


def panel_with_shadow(design_path: Path, size: int) -> tuple[Image.Image, Image.Image]:
    """Return (panel RGBA, shadow RGBA) — flat sign panel with soft drop shadow."""
    design = Image.open(design_path).convert("RGB")
    design = design.resize((size, size), Image.LANCZOS)

    # Rounded corners like a real printed panel (slight radius from slicer)
    radius = size // 60
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=255)

    panel = Image.new("RGBA", (size, size))
    panel.paste(design, (0, 0))
    panel.putalpha(mask)

    # Soft shadow (offset down-right, blurred) — conveys 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-049 -->

<!-- TRASH id=20260702-050 date=2026-07-02 kind=file source="tools/generate_sign_info_graphics.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-050 · 2026-07-02 · file · `tools/generate_sign_info_graphics.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-050__generate_sign_info_graphics.py`

```
#!/usr/bin/env python3
"""
generate_sign_info_graphics.py — SS1001 listing photos 7, 9, 10

Deterministic PIL info graphics built from the REAL design files — text and
designs are exact by construction (no AI rendering, nothing to verify):

  photo_07 — Bambu Studio 3-step how-to (import → split by color → assign AMS)
  photo_09 — What's included / ZIP contents specs card
  photo_10 — All 5 design previews side by side
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
OUT_DIR     = Path("data/3d_print_signs/america_250/listing_photos/final")
FONTS       = Path("assets/fonts")
C           = 2400  # canvas

NAVY   = (27, 37, 80)
RED    = (178, 52, 49)
GOLD   = (200, 148, 62)
CREAM  = (247, 242, 232)
INK    = (35, 30, 26)

DESIGNS = [
    ("Main Eagle",      DESIGNS_DIR / "america250_ai_color_raw.jpg"),
    ("Medallion",       DESIGNS_DIR / "america250_design2_medallion.jpg"),
    ("Art Deco",        DESIGNS_DIR / "america250_design3_artdeco.jpg"),
    ("Vintage Stamp",   DESIGNS_DIR / "america250_design4_stamp.jpg"),
    ("Heraldic Shield", DESIGNS_DIR / "america250_design5_shield.jpg"),
]


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONTS / name), size)


def rounded_thumb(path: Path, size: int, radius: int = 24) -> Image.Image:
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, size - 1, size - 1], radius, fill=255)
    out = Image.new("RGBA", (size, size))
    out.paste(img, (0, 0))
    out.putalpha(mask)
    return out


def drop_shadow(canvas: Image.Image, box: tuple, radius: int = 24, blur: int = 18):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 8, y0 + 10, x1 + 8, y1 + 10],
                                         radius, fill=(0, 0, 0, 70))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def center_text(d: ImageDraw.ImageDraw, cx: int, y: int, text: str,
                f: ImageFont.FreeTypeFont, fill):
    w = d.textlength(text, font=f)
    d.text((cx - w / 2, y), text, font=f, fill=fill)


def split_by_color(path: Path, n: int = 4, size: int = 360) -> list[Image.Image]:
    """Quantize the design to n colors and return one layer image per color —
    visually demonstrates Bambu Studio's Split-by-Color on the REAL design."""
    img = Image.open(path).convert("RGB").resize((size, size), Image.LANCZOS)
    q = img.quantize(colors=n, method=Image.MEDIANCUT)
    pal = q.getpalette()[:n * 3]
    colors = [tuple(pal[i * 3:i * 3 + 3]) for i in range(n)]
    layers = []
    qdata = list(q.getdata())
    for ci, color in enumerate(colors):
        layer = Image.new("RGBA", (size, size), (255, 255, 255, 0))
        ldata = [(color + (255,)) if v == ci else (0, 0, 0, 0) for v in qdata]
        layer.putdata(ldata)
        layers.append((color, layer))
    return layers


# ── Photo 07 — Bambu Studio 3-step how-to ─────────────────────────────────────
def photo_07():
    canvas = Image.new("RGBA", (C, C), CREAM + (255,))
    d = ImageDraw.Draw(canvas)

    h1 = font("Poppins-Bold.ttf", 110)
    h2 = font("Poppins-SemiBold.ttf", 62)
    body = font("Poppins-Regular.ttf", 48)
    step_f = font("Poppins-Bold.ttf", 72)

    center_text(d, C // 2, 90, "HOW TO PRINT", h1, NAVY)
    center_text(d, C // 2, 230, "in Bambu Studio — 3 easy steps", h2, GOLD)

    panel_w, panel_h = 660, 1330
    gap = (C - 3 * panel_w) // 4
    top = 430
    design_path = DESIGNS[0][1]

    steps = [
        ("1", "IMPORT THE SVG", "Drag & drop SVG · set height 6mm"),
        ("2", "PAINT THE COLORS", "Press N → Fill tool → click each region"),
        ("3", "ASSIGN AMS SLOTS", "Colors auto-map · check · Slice!"),
    ]

    for i, (num, title, sub) in enumerate(steps):
        x0 = gap 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-050 -->

<!-- TRASH id=20260702-051 date=2026-07-02 kind=file source="tools/generate_sign_lifestyle_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-051 · 2026-07-02 · file · `tools/generate_sign_lifestyle_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-051__generate_sign_lifestyle_photos.py`

```
#!/usr/bin/env python3
"""
generate_sign_lifestyle_photos.py

Generates lifestyle mockups for 3D-printed wall sign listings using gpt-image-1's
image editing endpoint — the same approach used for the tumbler mockups.

The flat design JPG is passed as input. gpt-image-1 renders it as a physical
3D-printed sign displayed in a real-world scene, with proper lighting, shadows,
and depth — no manual PIL compositing needed.

Usage:
  python tools/generate_sign_lifestyle_photos.py               # all photos
  python tools/generate_sign_lifestyle_photos.py hero porch    # specific shots
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

DESIGNS_DIR = Path("data/3d_print_signs/america_250/ai_generated")
OUTPUT_DIR  = Path("data/3d_print_signs/america_250/listing_photos/final")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE  = 2400
INPUT_MAX_DIM = 1024


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Design files ──────────────────────────────────────────────────────────────
DESIGN_FILES = {
    "main":      DESIGNS_DIR / "america250_ai_color_raw.jpg",
    "medallion": DESIGNS_DIR / "america250_design2_medallion.jpg",
    "artdeco":   DESIGNS_DIR / "america250_design3_artdeco.jpg",
    "stamp":     DESIGNS_DIR / "america250_design4_stamp.jpg",
    "shield":    DESIGNS_DIR / "america250_design5_shield.jpg",
}

# ── Sign description shared across all scenes ─────────────────────────────────
# Real-world accuracy: these signs are printed FACE-DOWN on a textured PEI plate.
# The visible face is PERFECTLY FLAT — every color sits flush in one single plane
# (multi-color comes from filament swaps in the first layers). The face has a fine
# uniform matte grain from the textured plate. NO raised lettering, NO embossing,
# NO bevels, NO surface relief of any kind. Layer lines only on the side edges.
SIGN_DESCRIPTION = (
    "a square 3D-printed patriotic sign made from colored PLA filament on a "
    "Bambu Lab printer with 4-color AMS, printed face-down on a textured build plate. "
    "The entire front face is PERFECTLY FLAT — the design is NOT raised, NOT embossed, "
    "NOT engraved; all colors (use the EXACT colors from the input image — do not "
    "substitute or re-palette any color) are flush in a single "
    "smooth plane, like an inlaid graphic. The flat face has a very fine uniform matte "
    "grain texture from the textured print plate. The sign is a thin flat panel about "
    "6mm thick and approximately 9.25×9.25 inches (235×235mm) square, with FDM layer lines "
    "visible only on the thin side edges."
)

# ── Scene configs ─────────────────────────────────────────────────────────────
SCENES = {

    "hero": {
        "design_id": "main",
        "out_name":  "photo_01_hero_gallery_wall.jpg",
        "prompt": f"""\
This is the flat graphic of a 3D-printed patriotic wall sign. Render it as a \
single photorealistic product photograph of {SIGN_DESCRIPTION}

Scene: The sign is mounted on a warm cream plaster wall as the centerpiece of a small \
gallery wall arrangement. Two smaller coordinating frames (no art — just natural wood \
empty frames) flank it on each side, slightly smaller. The wall has warm cream textured \
plaster. Below the sign grouping: a narrow dark walnut console table with a small \
terracotta pot holding dried pampas grass on the left, and a folded navy linen on \
the right. A few loose dried eucalyptus stems lean against the wall.

The 3D-printed sign itself occupies the CENTER of the frame, filling approximately \
60% of the image width. It is mounted flat against the wall with a subtle drop shadow \
showing depth. The design from this image is faithfully reproduced on the sign face — \
same colors, same composition, same details — rendered as a completely FLAT inlaid graphic \
f
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-051 -->

<!-- TRASH id=20260702-052 date=2026-07-02 kind=file source="tools/generate_ss1001_originals_4c.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-052 · 2026-07-02 · file · `tools/generate_ss1001_originals_4c.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-052__generate_ss1001_originals_4c.py`

```
#!/usr/bin/env python3
"""
Rebuild the original 5 SS1001 AI concepts as clean 4-color programmatic SVGs.

4 colors:
  Cream — base plate (background, 0–4 mm)
  Navy  — raised elements (4–6 mm)
  Red   — raised elements (4–6 mm)
  Gold  — raised elements (4–6 mm)

All three raised layers must occupy non-overlapping XY footprints.

Output folders (data/3d_print_signs/america_250/):
  07_america250_banner_4c    AMERICA 250 banner  (navy base)
  08_america250_burst_4c     Art-deco sunburst   (cream base)
  09_america250_seal_4c      Circular seal       (cream base)
  10_america250_shield_4c    Shield / eagle      (navy base)
  11_america250_stamp_4c     Liberty stamp       (cream base)

Run: python tools/generate_ss1001_originals_4c.py
"""

from __future__ import annotations
import io
import math
import re
from pathlib import Path

import cairosvg
from PIL import Image

ROOT       = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"

DESIGNS = [
    ("07_america250_banner_4c",  "America 250 Banner"),
    ("08_america250_burst_4c",   "America 250 Burst"),
    ("09_america250_seal_4c",    "America 250 Seal"),
    ("10_america250_shield_4c",  "America 250 Shield"),
    ("11_america250_stamp_4c",   "America 250 Stamp"),
]

# ── SVG helpers ──────────────────────────────────────────────────────────────

ANTON = "Anton, Impact, 'Arial Black', sans-serif"
MONT  = "Montserrat, 'Arial', sans-serif"

def doc(w: float, h: float, *els: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}">\n'
        + "".join(els)
        + "</svg>\n"
    )

def R(x, y, w, h, rx=0) -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="black"/>\n'

def C(cx, cy, r) -> str:
    return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="black"/>\n'

def P(d: str, fr: str = "") -> str:
    fr_a = f' fill-rule="{fr}"' if fr else ""
    return f'<path d="{d}" fill="black"{fr_a}/>\n'

def T(x, y, fs, text, fam=ANTON, anc="middle", fw="") -> str:
    fw_a = f' font-weight="{fw}"' if fw else ""
    return (
        f'<text x="{x}" y="{y}" font-family="{fam}" font-size="{fs}"{fw_a}'
        f' text-anchor="{anc}" dominant-baseline="central" fill="black">'
        f'{text}</text>\n'
    )

def TM(x, y, fs, text, anc="middle") -> str:
    return T(x, y, fs, text, fam=MONT, anc=anc, fw="900")

def star(cx, cy, ro, ri=None, n=5, rot=-90) -> str:
    ri = ri if ri is not None else ro * 0.40
    pts = []
    for i in range(2 * n):
        a = math.radians(rot + 180 * i / n)
        r = ro if i % 2 == 0 else ri
        pts.append(f"{cx + r*math.cos(a):.2f},{cy + r*math.sin(a):.2f}")
    return P("M" + "L".join(pts) + "Z")

def ring(cx, cy, ro, ri) -> str:
    """Annulus (ring) via even-odd fill rule."""
    def cpth(r):
        return (
            f"M{cx - r:.2f},{cy:.2f} "
            f"A{r:.2f},{r:.2f} 0 1,1 {cx + r:.2f},{cy:.2f} "
            f"A{r:.2f},{r:.2f} 0 1,1 {cx - r:.2f},{cy:.2f} Z"
        )
    return P(cpth(ro) + " " + cpth(ri), fr="evenodd")

def pie(cx, cy, r, a1_deg, a2_deg) -> str:
    """Filled pie slice."""
    a1, a2 = math.radians(a1_deg), math.radians(a2_deg)
    x1 = cx + r * math.cos(a1);  y1 = cy + r * math.sin(a1)
    x2 = cx + r * math.cos(a2);  y2 = cy + r * math.sin(a2)
    large = 1 if (a2_deg - a1_deg) % 360 > 180 else 0
    return P(
        f"M{cx:.2f},{cy:.2f} L{x1:.2f},{y1:.2f} "
        f"A{r:.2f},{r:.2f} 0 {large},1 {x2:.2f},{y2:.2f} Z"
    )

def annular_pie(cx: float, cy: float, r_in: float, r_out: float,
                a1_deg: float, a2_deg: float) -> str:
    """Filled donut-sector from r_in to r_out, angle a1..a2 degrees (clockwise)."""
    a1, a2 = math.radians(a1_deg), math.radians(a2_deg)
    da = abs(a2_deg - a1_deg)
    large = 1 if da >= 180 else 0
    ox1 = cx + r_out * math.cos(a1);  oy1 = cy + r_out * math.sin(a1)
    ox2 = cx + r_out * math.cos(a2);  oy2 = cy + r_o
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-052 -->

<!-- TRASH id=20260702-053 date=2026-07-02 kind=file source="tools/generate_ss1001_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-053 · 2026-07-02 · file · `tools/generate_ss1001_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-053__generate_ss1001_photos.py`

```
#!/usr/bin/env python3
"""
Generate all 10 listing photos for SS1001 America 250 3D Sign Pack.

Uses gpt-image-1 images.edit with the actual design previews as input
(per CLAUDE.md cardinal rule: every photo must show the real product).

Photos generated:
  1. Hero gallery wall (3 signs)
  2. Interior mantel / living room
  3. Front porch / outdoor
  4. Tiered tray farmhouse
  5. Yard / garden stake sign
  6. Collection overview (all 5 designs — PIL flat lay)
  7. HOW-TO graphic (Bambu Studio workflow — PIL text)
  8. Detail close-up (one sign)
  9. What's included / specs (PIL text)
  10. Design lineup (all 5 previews — PIL composite)

Output: data/3d_print_signs/america_250/listing_photos/final_v2/
"""

from __future__ import annotations
import base64
import io
import os
import sys
import textwrap
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

client = OpenAI()

ROOT = Path(__file__).parent.parent
DESIGN_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_DIR = DESIGN_DIR / "listing_photos" / "final_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

DESIGNS = {
    # Vol 1 — original 5 (3-color: White/Navy/Red)
    "america_bold": DESIGN_DIR / "01_america250_america_bold" / "preview.jpg",
    "star_badge":   DESIGN_DIR / "02_america250_star_badge"   / "preview.jpg",
    "freedom_sign": DESIGN_DIR / "03_america250_freedom_sign" / "preview.jpg",
    "happy_4th":    DESIGN_DIR / "04_america250_happy_4th"    / "preview.jpg",
    "land_free":    DESIGN_DIR / "05_america250_land_free"    / "preview.jpg",
    # Vol 2 — 4-color originals (Cream/Navy/Red/Gold)
    "banner":       DESIGN_DIR / "07_america250_banner_4c"    / "preview.jpg",
    "burst":        DESIGN_DIR / "08_america250_burst_4c"     / "preview.jpg",
    "seal":         DESIGN_DIR / "09_america250_seal_4c"      / "preview.jpg",
    "shield_4c":    DESIGN_DIR / "10_america250_shield_4c"    / "preview.jpg",
    "stamp":        DESIGN_DIR / "11_america250_stamp_4c"     / "preview.jpg",
}

DESIGNS_VOL1 = {k: v for k, v in list(DESIGNS.items())[:5]}
DESIGNS_VOL2 = {k: v for k, v in list(DESIGNS.items())[5:]}

FINAL_SIZE = 2400

# ── Shared language ────────────────────────────────────────────────────────────

STYLE = (
    "Photography style: bright warm editorial Etsy product photography. "
    "Warm cream walls and natural linen/oak surfaces. "
    "Soft diffused window light from the left, warm white balance, gentle shadow to right. "
    "No people, no hands, no text overlays, no watermarks. Square 1:1 format."
)

SIGN_RENDER = (
    "The input image shows the flat 2D design layout for a 3D printed wall sign. "
    "Render it as a physical multi-color FDM 3D printed sign with these exact properties: "
    "cream/off-white PLA base plate 4mm thick with a slight bevel on all edges; "
    "the text and design elements are raised 2mm above the base in "
    "deep navy blue PLA and deep patriotic red PLA, exactly matching the layout in the input image. "
    "The face of the sign is perfectly smooth (printed face-down on textured PEI). "
    "Subtle layer lines visible on the side edges only. "
    "Preserve the EXACT design: same text content, same star positions, same color regions as the input."
)


# ── Fonts ─────────────────────────────────────────────────────────────────────

def _fonts():
    try:
        lg  = ImageFont.truetype("/usr/local/share/fonts/google/Anton-Regular.ttf",  90)
        md  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  56)
        sm  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  44)
        xs  = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  34)
        bdg = ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf",  42)
    except Exception:
        lg = md = sm = xs = bdg = ImageFont.load_default()
    return lg, md, sm, xs, bdg


# ── Badge overlay (req
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-053 -->

<!-- TRASH id=20260702-054 date=2026-07-02 kind=file source="tools/generate_ss1001_vol2_designs.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-054 · 2026-07-02 · file · `tools/generate_ss1001_vol2_designs.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-054__generate_ss1001_vol2_designs.py`

```
#!/usr/bin/env python3
"""
Generate high-quality flat 2D design images for SS1001 Vol 2 using gpt-image-1.

Each design matches one of the original 5 AI concept signs:
  07 — Banner (Main): navy background, gold AMERICA, cream 250, red stripes
  08 — Burst (Artdeco): navy disc, 24 gold sunburst rays, cream 250 in center
  09 — Seal (Medallion): cream disc, navy eagle + ring text, navy 250
  10 — Shield: cream pentagon, navy eagle, gold AMERICA ribbon, red stars + 250
  11 — Stamp: cream rectangle with perforations, navy Liberty, red AMERICA 250

Output: preview.jpg in each design folder (replaces programmatic composite).
These previews drive listing photos 06, 09, 10 and inform images.edit lifestyle shots.
"""

from __future__ import annotations
import base64
import io
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image

client = OpenAI()

ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"

# Style anchor — applied to every prompt
STYLE = (
    "Flat 2D vector graphic illustration. Absolutely no gradients, no drop shadows, "
    "no photography, no 3D rendering effects. Exactly four flat solid colors: "
    "dark navy blue (#1B3A68), deep patriotic red (#B22234), antique gold (#C9A84C), "
    "and warm cream (#F5EDD0). Crisp, clean color boundaries. "
    "Professional commercial sign design. Square format 1:1."
)

DESIGNS = [
    {
        "folder": "07_america250_banner_4c",
        "name": "Banner (Main)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Horizontal rectangle, wider than tall. "
            "Background: solid dark navy blue. "
            "Layout top-to-bottom: "
            "(1) Thin antique-gold decorative outer border frame. "
            "(2) Deep red horizontal band across the full top. "
            "(3) 'AMERICA' in very large bold antique-gold block letters, centered. "
            "(4) Thin antique-gold rule line. "
            "(5) '250' in enormous bold cream/off-white Anton-style numerals — this is the dominant element, filling most of the central height. "
            "(6) Thin red accent line. "
            "(7) '1776  –  2026' in cream letters, small, centered. "
            "(8) Deep red horizontal band across the full bottom. "
            "A single antique-gold 5-pointed star centered between AMERICA and 250. "
            + STYLE
        ),
    },
    {
        "folder": "08_america250_burst_4c",
        "name": "Burst (Artdeco Sunburst)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Perfect circle disc shape. "
            "Background of the disc: solid dark navy blue. "
            "24 antique-gold sunburst rays radiating outward from a central circle to the edge. "
            "Rays are tall narrow wedge/triangle shapes, evenly spaced, with thin navy gaps between each ray. "
            "Central inner circle (no rays — solid navy background): "
            "  - 'AMERICA' in bold antique-gold letters, small, at the top of the inner circle. "
            "  - Very large bold '250' in cream/off-white numerals, centered and dominant. "
            "  - '1776  ·  2026' in small antique-gold text below the 250. "
            "Thin antique-gold ring border separates the inner circle from the rays. "
            "Art Deco patriotic style. "
            + STYLE
        ),
    },
    {
        "folder": "09_america250_seal_4c",
        "name": "Seal (Medallion)",
        "prompt": (
            "Flat 2D patriotic sign graphic. Perfect circle — official government seal style. "
            "Background: warm cream/parchment fills the full circle. "
            "Outer thick navy-blue ring: 'UNITED STATES OF AMERICA' text curves along the inner top arc in cream letters. "
            "13 small 5-pointed cream stars evenly spaced inside the ring. "
            "Inside the ring: American bald eagle silhouette in solid navy blue, wings fully sp
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-054 -->

<!-- TRASH id=20260702-055 date=2026-07-02 kind=file source="tools/generate_ss1001_vol2_lifestyle_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-055 · 2026-07-02 · file · `tools/generate_ss1001_vol2_lifestyle_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-055__generate_ss1001_vol2_lifestyle_photos.py`

```
#!/usr/bin/env python3
"""
Generate 5 Vol 2 lifestyle photos for SS1001 America 250 3D Sign Pack.

Photo plan:
  1. Hero gallery wall (Banner center + Seal left + Shield right)
  2. Banner living room (Banner above linen sofa)
  3. Seal mantel (Seal circular medallion on fireplace mantel)
  4. Burst tiered tray (Burst disc on farmhouse tiered tray)
  5. Stamp entryway (Stamp rectangle on shiplap entryway wall)

Then update Etsy listing 4520524435, deleting ranks 1-5 and uploading the new photos.

Uses images.edit with the actual preview.jpg files as input per CLAUDE.md cardinal rule.
"""

from __future__ import annotations
import base64
import io
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
from PIL import Image, ImageDraw, ImageFont

# Add tools dir to path for etsy_api import
TOOLS_DIR = Path(__file__).parent
ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from etsy_api import EtsyAPIClient

client = OpenAI()

DESIGN_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_DIR = DESIGN_DIR / "listing_photos" / "final_v2"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Vol 2 design previews
BANNER = DESIGN_DIR / "07_america250_banner_4c" / "preview.jpg"
BURST  = DESIGN_DIR / "08_america250_burst_4c"  / "preview.jpg"
SEAL   = DESIGN_DIR / "09_america250_seal_4c"   / "preview.jpg"
SHIELD = DESIGN_DIR / "10_america250_shield_4c" / "preview.jpg"
STAMP  = DESIGN_DIR / "11_america250_stamp_4c"  / "preview.jpg"

FINAL_SIZE = 2400
LISTING_ID = 4520524435

# ── Shared descriptors ─────────────────────────────────────────────────────────

STYLE = (
    "Photography style: bright warm editorial Etsy product photography. "
    "Warm cream walls and natural linen/oak surfaces. "
    "Soft diffused window light from the left, warm white balance, gentle shadow to right. "
    "No people, no hands, no text overlays, no watermarks. Square 1:1 format. "
    "Subject fills center 65% of frame. 5% neutral padding at all edges."
)

SIGN_RENDER_4C = (
    "The input image shows the flat 2D design of a 4-color 3D printed patriotic "
    "America 250th Anniversary sign. Render it as a physical multi-color FDM 3D printed sign: "
    "cream/off-white PLA base plate 4mm thick with subtle beveled edges; "
    "design elements raised 2mm above the base in deep navy blue PLA, patriotic red PLA, "
    "and antique gold PLA. Face is perfectly smooth (printed face-down on textured PEI plate). "
    "Subtle layer lines on side edges only. "
    "Preserve the EXACT colors, text, and proportions from the input image."
)


# ── Fonts ──────────────────────────────────────────────────────────────────────

def _badge_font():
    try:
        return ImageFont.truetype("/usr/local/share/fonts/google/Montserrat-VF.ttf", 42)
    except Exception:
        return ImageFont.load_default()


# ── Badge overlay (required on every lifestyle slot 1-6) ──────────────────────

def add_digital_badge(img: Image.Image) -> Image.Image:
    """Stamp 'DIGITAL FILE — SVG DOWNLOAD' badge in top-left corner."""
    draw = ImageDraw.Draw(img)
    NAVY = (27, 58, 104)
    bdg = _badge_font()
    text = "DIGITAL FILE — SVG DOWNLOAD"
    bbox = draw.textbbox((0, 0), text, font=bdg)
    pad_x, pad_y = 22, 12
    w = (bbox[2] - bbox[0]) + 2 * pad_x
    h = (bbox[3] - bbox[1]) + 2 * pad_y
    draw.rectangle([28, 28, 28 + w, 28 + h], fill=NAVY)
    draw.text((28 + pad_x, 28 + pad_y), text, fill="white", font=bdg)
    return img


# ── images.edit helper ─────────────────────────────────────────────────────────

def generate(images: list[Path], prompt: str, out_path: Path) -> Path:
    """Call images.edit with real product files, resize to 2400×2400, add badge, save."""
    print(f"  Generating {out_path.name} ...")
    img_files = [open(p, "rb") for p in images]
    try:
        result = client.images.edit(
            model="gpt-image-1",
            image=img_files if len(img_files) > 1 else img
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-055 -->

<!-- TRASH id=20260702-056 date=2026-07-02 kind=file source="tools/generate_sublimation_wraps.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-056 · 2026-07-02 · file · `tools/generate_sublimation_wraps.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-056__generate_sublimation_wraps.py`

```
#!/usr/bin/env python3
"""
generate_sublimation_wraps.py

Generates production-quality sublimation tumbler wrap designs for Etsy.
Each design is generated at gpt-image-1 max resolution, then upscaled
to true 300 DPI print dimensions using Lanczos resampling.

Output: PNG files at 300 DPI, sRGB, ready for sublimation printing.

Sizes:
  20oz Skinny: 9.33" × 8.33" @ 300 DPI = 2799 × 2499 px
  30oz Tall:   9.5"  × 9.1"  @ 300 DPI = 2850 × 2730 px
"""

import re
import base64
import io
import sys
from pathlib import Path

OUTPUT_DIR = Path("data/sublimation_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SIZES = {
    "20oz":      (2798, 2438),   # 9.325" × 8.125" @ 300 DPI — MakerFlo standard straight
    "20oz_thick": (3360, 2318),  # 11.2"  × 7.725" @ 300 DPI — thick-wall variant
    "30oz":      (3090, 2880),   # 10.3"  × 9.6"   @ 300 DPI
    "30oz_thick": (3360, 2655),  # 11.2"  × 8.85"  @ 300 DPI — thick-wall variant
    "11oz_mug":  (2550, 1050),   # 8.5"   × 3.5"   @ 300 DPI
    "15oz_mug":  (2700, 1200),   # 9.0"   × 4.0"   @ 300 DPI
}

GEN_SIZE = "1536x1024"


def load_env():
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ---------------------------------------------------------------------------
# Design library — each entry is a self-contained, highly-detailed prompt.
# Prompts are written to maximise gpt-image-1's illustration quality:
#   1. State the EXACT art style first
#   2. Describe background, then focal design, then typography, then accents
#   3. Specify the colour palette with hex values
#   4. End with hard technical constraints (seamless, no watermark, etc.)
# ---------------------------------------------------------------------------

DESIGNS = [

    # ── FOOTBALL MOM ────────────────────────────────────────────────────────
    {
        "id": "football_mom",
        "name": "Football Mom",
        "prompt": """
Professional sublimation tumbler wrap design, full bleed horizontal rectangle.

Art style: retro vintage sports illustration meets boho watercolor florals —
rich, layered, painterly depth with bold typography.

BACKGROUND: Deep forest green (#1B4332) field filled with a loose all-over
pattern of tiny golden footballs, autumn leaves (maple, oak), and scattered
small five-pointed stars in antique gold and cream. Pattern is dense enough
to leave no plain background showing through.

CENTRAL FOCAL DESIGN: A large, detailed American football rendered in warm
brown leather with hand-stitched white lace and realistic panel shading.
Flanking the football on both sides: lush clusters of fall wildflowers —
sunflowers with dark centres, dried pampas grass plumes, small daisy sprigs,
and eucalyptus leaves — all in gold (#D97706), rust orange (#C2410C), cream
(#FEF3C7), and burgundy (#7B2D3E). Botanical elements feel loose and
painterly, not rigid.

TYPOGRAPHY: Centred above the football: "FOOTBALL MOM" in a bold retro varsity
font, cream/ivory (#FEF3C7) fill with a worn, slightly distressed texture, and
a thick antique gold (#D97706) stroke outline. Below the football: "Always
Cheering" in a flowing, casual handwritten script in antique gold.

ACCENTS: Small five-pointed stars and sparkle dots in gold and cream scattered
throughout. Thin decorative rule lines in gold frame the typography block.

COLOUR PALETTE: forest green, autumn burgundy, warm cream, antique gold,
rust orange. ZERO pastels. Deep, saturated, high-contrast.

TECHNICAL: The left edge and right edge of the design must be visually
seamless — the background pattern continues without a visible seam. Colours
are vibrant and fully saturated to compensate for sublimation's natural
colour shift. No white or pale areas in the background. No watermarks.
No photograph elements. No studio equipment. Print-ready quality.
        """.strip(),
    },

    # ── CHEER MOM ───────────────
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-056 -->

<!-- TRASH id=20260702-057 date=2026-07-02 kind=file source="tools/generate_sunflower_studio_assets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-057 · 2026-07-02 · file · `tools/generate_sunflower_studio_assets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-057__generate_sunflower_studio_assets.py`

```
"""
generate_sunflower_studio_assets.py — OpenAI-generated sticker pack for DP1033
(Teacher Planner 2026-2027, Sunflower Studio theme).

Produces, all via gpt-image-1:
  Nine transparent kawaii sticker SHEETS (the functional product customers
  import into GoodNotes Elements / Notability) ->
  DP1033_sticker_sheet_1..9.png  (background="transparent", PNG)

It then, with no further API calls:
  1. Auto-crops each sheet into individual transparent PNG stickers (connected
     non-transparent regions) so the pack ships pre-cropped singles too — and so
     the sticker COUNT in the listing is a real measured number, never a guess.
  2. Packages everything into DP1033_sticker_pack.zip with a README, matching the
     ZIP structure in CLAUDE.md (png_sheets/, individual_stickers/).
  3. Quantizes every PNG to a 256-color palette before zipping (keeps the ZIP
     well under Etsy's 20MB hard limit).

Cover art for DP1033 is handled separately by tools/generate_planner_v2.py
(DP1033_cover_ai.png) — this script only handles the sticker pack.

Run:  python tools/generate_sunflower_studio_assets.py            # all 9 sheets + zip
      python tools/generate_sunflower_studio_assets.py --append-sheets 6,7
"""
import sys
import zipfile
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from tools.image_gen import generate_image, SQUARE

ART = _BASE_DIR / "data" / "digital_products" / "product_files"
PID = "DP1033"

_STYLE = (
    "Kawaii chibi sticker sheet, flat vector illustration style, bold clean 2px "
    "seed-brown outlines, soft cel shading, tiny white catch-light in each eye, "
    "small blush cheeks. Sunflower Studio palette ONLY: sunflower yellow #F4C430, "
    "stem green #4A7C59, soft gold #F8E08E, cream petal #FFFDF0, seed brown "
    "#2A1A00. Stickers arranged in a neat evenly-spaced grid with clear gaps "
    "between each sticker so they can be cut apart, every sticker fully "
    "separated, no overlap. TRANSPARENT background (no backdrop, no paper, no "
    "shadow behind the grid). Crisp, premium, professional digital planner "
    "sticker art, bright cheerful botanical classroom aesthetic."
)

SHEETS = {
    1: ("Functional Planning",
        "About 24 FUNCTIONAL planner stickers on a transparent grid: ribbon "
        "header banners reading 'TODAY', 'THIS WEEK', 'TOP 3', 'DON'T FORGET'; "
        "small checkbox rows; a priority star; a due-date flag; date dots "
        "numbered; an action arrow; an exclamation 'urgent' badge; a small "
        "sticky note; a page flag; a tiny clock; an apple-shaped bookmark tab. "
        "Sunflower yellow and stem green."),
    2: ("Widget Trackers",
        "About 20 widget tracker stickers on a transparent grid: a 5-face mood "
        "tracker row, an 8-cup water-intake widget, a sleep-quality moon widget, "
        "a 7-circle habit streak shaped like sunflower petals, an energy battery "
        "meter, a 'brain dump' notepad widget, a weekly summary widget, a "
        "'today's 3 wins' celebration box, a lesson-progress dial. All in "
        "sunflower yellow and stem green."),
    3: ("Planner & Stationery",
        "About 22 cute stationery stickers on a transparent grid: a mini "
        "notebook, a fountain pen, washi tape rolls, paper clips, a highlighter, "
        "scissors, a ruler and pencil, a coffee mug with an apple design, a desk "
        "lamp, bookmarks, sticky notes, a red stamp marked 'GRADED'. Sunflower "
        "yellow + stem green, kawaii."),
    4: ("Cozy Lifestyle",
        "About 22 cozy lifestyle stickers on a transparent grid: a sleeping cat "
        "curled on a stack of books, a steaming tea mug with a sunflower design, "
        "a lit candle, fairy lights, an open book with a sunflower bookmark, a "
        "pair of headphones with a heart, a soft cardigan folded, a small potted "
        "sunflower, a teacup, a bowl of trail mix, a cozy 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-057 -->

<!-- TRASH id=20260702-058 date=2026-07-02 kind=file source="tools/generate_svg_designs.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-058 · 2026-07-02 · file · `tools/generate_svg_designs.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-058__generate_svg_designs.py`

```
#!/usr/bin/env python3
"""
generate_svg_designs.py

Generates complete SVG cut file bundles using gpt-image-1.
Each bundle = 20 designs × (design PNG + SVG trace + 3 product mockups).

Hardcoded rules applied to every design:
  - NO dates, NO years, NO "est.", NO specific numbers — universal buyer appeal
  - Maximum 4 flat colors, crisp edges, vector-art aesthetic
  - All designs work for Cricut Design Space and Silhouette Studio

Output structure per bundle:
  data/svg_bundles/{bundle_id}/
    SVG/            — 20 traced SVG cut files
    PNG/            — 20 high-res design PNGs (300 DPI reference)
    mockups/        — product lifestyle photos (t-shirt, tote, mug)
    listing_photos/ — 10 Etsy listing images
    {bundle_id}_SVG_Bundle.zip — buyer download (SVG + PNG + README)

Usage:
  python tools/generate_svg_designs.py western          # one bundle
  python tools/generate_svg_designs.py western floral_wreath
  python tools/generate_svg_designs.py --all            # all 5 bundles
  python tools/generate_svg_designs.py western --skip-mockups
"""

import re, base64, io, sys, json, zipfile, threading, time
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import vtracer, cairosvg

BUNDLES_DIR = Path("data/svg_bundles")
BUNDLES_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400
INPUT_MAX   = 1024


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── DESIGN CATALOG — 5 bundles × 20 designs ──────────────────────────────────
#
# Each bundle has:
#   "title"       — Etsy listing title
#   "style_guide" — injected into every design prompt in this bundle
#   "designs"     — 20 entries, each with "name" and "elements"
#
# RULE: No dates, no years, no "est.", no specific numbers in any design.
# Text must work for every buyer regardless of when they purchased.

BUNDLES = {

    # ── 1. WESTERN / COUNTRY ─────────────────────────────────────────────────
    "western": {
        "title": "Western SVG Bundle | 20 Country Cowgirl Cut Files | Cricut Silhouette | Instant Download",
        "niche": "western country cowgirl",
        "style_guide": {
            "aesthetic": "western cowgirl country rustic",
            "colors": "saddle brown, dusty sage green, golden yellow, warm tan — maximum 4 flat colors",
            "text_style": "bold western serif lettering or rustic hand-lettered script",
            "cut_elements": "cowboy hats, boots, horseshoes, lassos, sunflowers, cacti, lone stars, arrows, rope frames",
        },
        "designs": [
            {"id": "01", "name": "Wild Heart",      "elements": "wide-brim cowboy hat decorated with wildflowers tucked in hatband, 'WILD HEART' bold western lettering, rope lasso frame, small lone star and horseshoe accents"},
            {"id": "02", "name": "Yeehaw",           "elements": "oversized bold 'YEEHAW' western lettering arching over a horseshoe, sunflower accents on each side, starburst in background, small spur at bottom"},
            {"id": "03", "name": "Cowgirl Up",       "elements": "pair of cowboy boots with wildflowers and daisies growing from them, 'COWGIRL UP' in bold arch over boots, lasso rope decorative circle frame"},
            {"id": "04", "name": "Desert Rose",      "elements": "tall saguaro cactus with blooming roses wrapped around it, 'DESERT ROSE' in rustic lettering below, small arrow and star corner accents"},
            {"id": "05", "name": "Prairie Girl",     "elements": "wheat stalks and wildflowers fanning symmetrically, sunburst behind, 'PRAIRIE GIRL' bold lettering centered, tiny arrow chevrons below"},
            {"id": "06", "name": "Southern Soul",    "elements": "full magnolia blossom wreath ring with leaves and buds, 'SOUTHERN SOUL' elegant script inside the wreath, small star at top of ring"},
            {"id": "07", "name": "Rodeo Qu
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-058 -->

<!-- TRASH id=20260702-059 date=2026-07-02 kind=file source="tools/generate_tumbler_mockups.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-059 · 2026-07-02 · file · `tools/generate_tumbler_mockups.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-059__generate_tumbler_mockups.py`

```
#!/usr/bin/env python3
"""
generate_tumbler_mockups.py

Generates magazine-quality 20oz tumbler lifestyle mockups using gpt-image-1's
image editing endpoint. The actual flat design is passed as input — the model
renders it physically wrapped on the tumbler with proper cylinder curvature,
metallic reflections, and natural lighting as a single coherent render.

This is the correct approach for catalog-level realism. The old PIL composite
method (perspective warp onto a separately generated background) was discarded
because it looked AI-generated. The edit approach treats the design as source
material and produces a photorealistic output.

Usage:
  python tools/generate_tumbler_mockups.py                   # all 8 designs
  python tools/generate_tumbler_mockups.py football_mom      # one design
  python tools/generate_tumbler_mockups.py football_mom dog_mom nurse_life
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

OUTPUT_DIR  = Path("data/sublimation_mockups")
SAMPLES_DIR = Path("data/sublimation_samples")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400   # square JPEG output
INPUT_MAX_W = 1536   # resize input to this width before sending to API


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Per-design edit prompts ───────────────────────────────────────────────────
# Structure:
#   "design_description" — what's ON the wrap (helps model render accurately)
#   "scene"              — lifestyle context (surface, props, background, light)
# Both feed into the final edit prompt template at the bottom of this file.

DESIGNS = {

    "football_mom": {
        "design_description": (
            "deep forest green background with tiny scattered gold footballs and autumn maple "
            "leaves, a large brown leather football with white lace stitching in the center "
            "surrounded by lush autumn wildflowers in gold, rust orange, and burgundy, "
            "bold cream varsity-font 'FOOTBALL MOM' lettering above the football, "
            "'Always Cheering' in flowing gold script below"
        ),
        "scene": (
            "rustic dark oak wood surface, dried pampas grass in a terracotta vase to the left, "
            "two small orange pumpkins to the right, a folded plaid blanket corner at the bottom, "
            "warm cream textured plaster wall background, soft warm amber window light from left"
        ),
    },

    "cheer_mom": {
        "design_description": (
            "deep royal purple background with tiny hot pink megaphones and gold star pattern, "
            "two large crossed cheerleader pom-poms — one hot pink, one bright gold — with "
            "metallic sheen, radiating gold starburst behind the pom-poms, "
            "bold gold metallic 'CHEER MOM' lettering, "
            "'Louder Than Your Loudest Fan' in hot pink handwritten script below"
        ),
        "scene": (
            "smooth dark purple velvet surface, scattered small gold confetti pieces, "
            "a mini hot pink pom-pom to the lower right, a small gold star decoration, "
            "deep charcoal background with subtle bokeh glow, "
            "glamour studio lighting from above with metallic highlights"
        ),
    },

    "dog_mom": {
        "design_description": (
            "rich terracotta background with scattered cream paw prints and botanical sprigs, "
            "a charming kawaii golden retriever face with warm amber eyes and floppy ears "
            "in the center framed by a lush boho floral wreath of dried pampas, peach roses, "
            "eucalyptus, and cream daisies, bold cream serif 'DOG MOM' lettering above, "
            "'Fur Baby Mama' in dusty rose handwritten script below"
        ),
        "scene": (
            "natural linen cloth surface, sm
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-059 -->

<!-- TRASH id=20260702-060 date=2026-07-02 kind=file source="tools/generate_wall_art_mockups.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-060 · 2026-07-02 · file · `tools/generate_wall_art_mockups.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-060__generate_wall_art_mockups.py`

```
#!/usr/bin/env python3
"""
generate_wall_art_mockups.py

Generates catalog-quality wall art lifestyle mockups using gpt-image-1's
image editing endpoint. The actual art file is passed as input — the model
places it inside a real picture frame already in the room scene, rendering
a single coherent photorealistic image.

This replaces the old PIL composite method (lifestyle_composite.py) which
placed AI-generated art into AI-generated rooms via perspective warping.
The images.edit approach passes the REAL art file and produces a single
coherent render with natural lighting, correct frame shadows, and
perspective-correct art placement.

Each product gets two room types (living room + bedroom by default) in a
chosen frame style. All outputs are 2400×2400px JPEG for Etsy.

Usage:
  python tools/generate_wall_art_mockups.py              # all products
  python tools/generate_wall_art_mockups.py DP1000       # one product
  python tools/generate_wall_art_mockups.py DP1000 DP1007 DP1013
"""

import re, base64, io, sys
from pathlib import Path
from PIL import Image

ART_DIR    = Path("data/digital_products/product_files")
OUTPUT_DIR = Path("data/wall_art_mockups")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

MOCKUP_SIZE = 2400   # square JPEG output
INPUT_MAX   = 1024   # max dimension to send to API


def load_env() -> dict:
    env = {}
    with open(".env") as f:
        for line in f:
            m = re.match(r"^\s*([A-Z_]+)\s*=\s*(.+?)\s*$", line)
            if m:
                env[m.group(1)] = m.group(2)
    return env


# ── Frame styles ──────────────────────────────────────────────────────────────
# Each style defines the physical frame description used in the prompt.
# "natural_wood" = warm living rooms / bohemian
# "black_minimal" = modern / contemporary / dark academia
# "white_gallery" = bright / Scandinavian / nursery

FRAME_STYLES = {
    "natural_wood": (
        "natural light oak wood frame with a 2.5-inch white linen mat surrounding the artwork, "
        "thin carved moulding profile, matte warm finish"
    ),
    "black_minimal": (
        "thin 0.75-inch flat matte black metal frame with a crisp white mat, "
        "modern gallery-style profile, no ornamentation"
    ),
    "white_gallery": (
        "clean 1-inch flat white painted wood frame with a wide 3-inch bright white mat, "
        "gallery wall style, simple square profile"
    ),
}


# ── Room scenes ───────────────────────────────────────────────────────────────
# Each scene describes the room, surface, props, and lighting.
# The art frame is already present in the scene — the model places the input
# artwork INSIDE that existing frame.

ROOM_SCENES = {

    "living_room": {
        "room": (
            "warm cream textured plaster wall. A boucle fabric sofa with sage green and "
            "terracotta throw pillows sits below the frame. A natural rattan side table with "
            "a small terracotta ceramic pot is beside the sofa. "
            "Natural light oak hardwood floors. "
            "Trailing pothos plant in a terracotta pot on the left side of the scene."
        ),
        "light": "soft diffused morning window light from the left, warm white balance, gentle shadow to the right of the frame",
        "style": "bright airy editorial Etsy lifestyle, warm cream and natural linen tones throughout, IKEA catalog quality",
    },

    "bedroom": {
        "room": (
            "off-white linen-textured wall. A low platform bed in natural light oak with "
            "cream linen bedding and two stacked throw pillows sits below the frame. "
            "A small ceramic table lamp on a nightstand to the right emits warm amber glow. "
            "A trailing pothos plant on the windowsill at the left edge of frame."
        ),
        "light": "soft warm evening atmosphere, amber lamp glow from the right, gentle diffused window light from the left, intimate mood",
        "style": "Japandi bedroom editorial photography, calm, serene, coz
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-060 -->

<!-- TRASH id=20260702-061 date=2026-07-02 kind=file source="tools/build_art_registry.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-061 · 2026-07-02 · file · `tools/build_art_registry.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-061__build_art_registry.py`

```
#!/usr/bin/env python3
"""
build_art_registry.py
Scans data/digital_products/product_files/upscaled/ for DP*.jpg files,
computes dhash16 for each, and writes data/product_art_registry.json.

After building from files, cross-references data/dp_listing_map.json to
populate listing_ids for each DP code.

Usage:
    python tools/build_art_registry.py           # build/update full registry
    python tools/build_art_registry.py --update  # add new files only, skip existing
"""

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
REGISTRY_PATH = BASE_DIR / "data" / "product_art_registry.json"
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"


def dhash16(image_bytes: bytes) -> str | None:
    """
    Compute dhash16 of an image, square-normalizing first.

    All wall art source files are portrait (2:3). Listing photos are square (1:1).
    Computing dhash on a portrait vs a square produces high distances even when the
    art is the same — the 17×16 grid captures different content at different aspect
    ratios. Square-normalizing both sides before hashing gives distances of 0-10 for
    matching art, vs 90+ for unrelated images or room-scene composites.
    """
    if not PIL_OK:
        return None
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            # Center-crop to square before hashing (normalizes portrait vs square comparison)
            w, h = img.size
            s = min(w, h)
            left = (w - s) // 2
            top = (h - s) // 2
            img = img.crop((left, top, left + s, top + s))
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    bits.append("1" if pixels[row * 17 + col] > pixels[row * 17 + col + 1] else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def get_image_dimensions(image_bytes: bytes) -> list[int]:
    if not PIL_OK:
        return [0, 0]
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            return list(img.size)
    except Exception:
        return [0, 0]


def build_listing_id_map(map_path: Path) -> dict[str, list[int]]:
    """Return {dp_code: [listing_id, ...]} from dp_listing_map.json."""
    if not map_path.exists():
        return {}
    with open(map_path) as f:
        dp_map = json.load(f)

    result: dict[str, list[int]] = {}
    id_fields = ("listing_id", "kawaii_listing_id", "planner_listing_id",
                 "individual_listing_id", "secondary_listing_id")
    for dp_code, entry in dp_map.items():
        if not isinstance(entry, dict):
            continue
        ids = set()
        for key in id_fields:
            val = entry.get(key)
            if val:
                ids.add(int(val))
        if ids:
            result[dp_code] = sorted(ids)
    return result


def main():
    parser = argparse.ArgumentParser(description="Build/update product art registry")
    parser.add_argument("--update", action="store_true",
                        help="Add new files only; skip DP codes already in the registry")
    args = parser.parse_args()

    if not PIL_OK:
        print("ERROR: Pillow is not installed. Run: pip install Pillow")
        sys.exit(1)

    if not UPSCALED_DIR.exists():
        print(f"ERROR: Upscaled directory not found: {UPSCALED_DIR}")
        sys.exit(1)

    # Load existing registry
    registry: dict = {}
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH) as f:
            registry = json.load(f)

    # Build listing ID map from dp_listing_map.json
    listing_id_map = build_listi
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-061 -->

<!-- TRASH id=20260702-062 date=2026-07-02 kind=file source="tools/build_manifest.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-062 · 2026-07-02 · file · `tools/build_manifest.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-062__build_manifest.py`

```
#!/usr/bin/env python3
"""
build_manifest.py
Generates/updates data/listing_manifest.json from dp_listing_map.json
and live Etsy listing state.

The manifest is the ground truth for listing_integrity_check.py.
Each key is an Etsy listing_id (string). The value records:
  - expected_files: filename substrings that must appear in the listing's
    digital files (e.g. "DP1094_print_sizes.zip")
  - min_photo_count: minimum accepted listing images
  - type: product type used to pick the right rule set
  - art_hashes: {dp_code: dhash16_hex} for photo-level verification
  - last_verified: ISO timestamp from the last integrity check run

Run this whenever dp_listing_map.json is updated, or to rebuild hashes
after source art files change.

Usage:
    python tools/build_manifest.py            # build / update manifest
    python tools/build_manifest.py --hash     # recompute all art hashes
"""

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    from PIL import Image
    PIL_OK = True
except ImportError:
    PIL_OK = False

BASE_DIR = Path(__file__).parent.parent
MAP_PATH = BASE_DIR / "data" / "dp_listing_map.json"
MANIFEST_PATH = BASE_DIR / "data" / "listing_manifest.json"
UPSCALED_DIR = BASE_DIR / "data" / "digital_products" / "product_files" / "upscaled"
PRODUCT_FILES_DIR = BASE_DIR / "data" / "digital_products" / "product_files"

# ---------------------------------------------------------------------------
# Minimum photo counts by product type
# ---------------------------------------------------------------------------
PHOTO_MIN = {
    "wall_art":          8,   # goal 10; accept ≥8
    "planner":           8,
    "sticker_pack":      8,
    "gallery_bundle":    5,   # set-of-4 listings often have fewer photos
    "gallery_set":       5,
    "svg_bundle":        3,
    "commercial_license":2,
    "bundle":            5,
    "sublimation":       3,
    "sticker_bundle":    5,
    "unknown":           3,   # catch-all lower bar
}

# ---------------------------------------------------------------------------
# Expected downloadable file count by product type
# ---------------------------------------------------------------------------
FILE_COUNT = {
    "wall_art":          1,   # one print ZIP
    "planner":           3,   # dated PDF + undated PDF + sticker ZIP
    "sticker_pack":      1,   # sticker ZIP
    "gallery_bundle":    1,   # bundle ZIP
    "gallery_set":       1,
    "svg_bundle":        1,
    "commercial_license":1,
    "bundle":            1,
    "sublimation":       1,
    "sticker_bundle":    1,
    "unknown":           1,
}

# ---------------------------------------------------------------------------
# Perceptual hash helpers
# ---------------------------------------------------------------------------

def dhash16(image_path: Path) -> str | None:
    """Compute 256-bit difference hash (16×16 grid) as a hex string."""
    if not PIL_OK:
        return None
    try:
        with Image.open(image_path) as img:
            gray = img.convert("L").resize((17, 16), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            bits = []
            for row in range(16):
                for col in range(16):
                    left = pixels[row * 17 + col]
                    right = pixels[row * 17 + col + 1]
                    bits.append("1" if left > right else "0")
            return hex(int("".join(bits), 2))[2:].zfill(64)
    except Exception:
        return None


def find_art_file(dp_code: str) -> Path | None:
    """Return the best available source art file for a DP code."""
    # Check upscaled first
    for ext in ("jpg", "jpeg", "png"):
        p = UPSCALED_DIR / f"{dp_code}.{ext}"
        if p.exists():
            return p
    # Then product_files directory
    for ext in ("jpg", "jpeg", "png"):
        p = PRODUCT_FILES_DIR / f"{dp_code}.{ext}"
        if p.exists():
            return p
    return None


# -----
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-062 -->

<!-- TRASH id=20260702-063 date=2026-07-02 kind=file source="tools/build_review_batches.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-063 · 2026-07-02 · file · `tools/build_review_batches.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-063__build_review_batches.py`

```
#!/usr/bin/env python3
"""
Build batch HTML review files for ALL active Etsy listings.
10 listings per batch, all current photos shown per listing.
Photos are base64-embedded so files work offline / on any device.
Also initialises data/fix_queue.json for tracking flagged listings.
"""

import sys, json, time, base64, io, math, urllib.request
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

REPO       = Path(__file__).parent.parent
OUT_DIR    = REPO / "review_batches"
FIX_QUEUE  = REPO / "data" / "fix_queue.json"
BATCH_SIZE = 10
MAX_PX     = 420    # max photo dimension before re-encode
QUALITY    = 72     # JPEG quality for embedded photos

OUT_DIR.mkdir(exist_ok=True)

# ── Helpers ───────────────────────────────────────────────────────────────────

def download_and_compress(url: str) -> str | None:
    """Download photo, resize to MAX_PX, return base64 data URI."""
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer":    "https://www.etsy.com/"
        })
        with urllib.request.urlopen(req, timeout=15) as r:
            raw = r.read()
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_PX:
            scale = MAX_PX / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, "JPEG", quality=QUALITY, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode()
        return "data:image/jpeg;base64," + b64
    except Exception as e:
        print(f"      download failed: {e}")
        return None


def get_listing_photos(client, lid: int) -> list:
    """Return list of {rank, data_uri} for all photos on a listing."""
    try:
        imgs = client.get_listing_images(lid)
        time.sleep(0.12)
        return sorted(imgs, key=lambda i: i.get("rank", 99))
    except Exception as e:
        print(f"  WARN {lid} get_images: {e}")
        return []


# ── HTML generator ────────────────────────────────────────────────────────────

CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: #f2f1ee; color: #1a1a1a; padding: 16px;
}
h1 { font-size: 19px; margin-bottom: 4px; }
.subtitle { font-size: 13px; color: #666; margin-bottom: 20px; }
.toolbar {
  position: sticky; top: 0; z-index: 10;
  background: #f2f1ee; padding: 10px 0 12px;
  display: flex; gap: 10px; flex-wrap: wrap; align-items: center;
  border-bottom: 1px solid #ddd; margin-bottom: 20px;
}
.toolbar button {
  padding: 9px 16px; border: none; border-radius: 8px;
  cursor: pointer; font-size: 14px; font-weight: 700;
}
#btn-export { background: #c0392b; color: #fff; }
#btn-clear  { background: #ddd;    color: #333; }
#count-lbl  { font-size: 13px; color: #555; font-weight: 600; }
.listing {
  background: #fff; border-radius: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.07);
  margin-bottom: 20px; overflow: hidden;
  border: 3px solid transparent;
  transition: border-color 0.2s;
}
.listing.flagged { border-color: #e74c3c; }
.listing-header {
  display: flex; align-items: flex-start; gap: 12px;
  padding: 12px 14px 10px; border-bottom: 1px solid #eee;
  cursor: pointer;
}
.listing-header input[type=checkbox] {
  width: 22px; height: 22px; flex-shrink: 0;
  margin-top: 2px; cursor: pointer; accent-color: #e74c3c;
}
.listing-info { flex: 1; min-width: 0; }
.listing-title { font-size: 14px; font-weight: 700; line-height: 1.35; }
.listing-meta  { font-size: 11px; color: #999; margin-top: 3px; }
.etsy-link {
  display: inline-block; margin-top: 5px;
  font-size: 12px; color: #e06c1a; text-decoration: none;
}
.photos {
  display: flex; gap: 8px; padding: 10px 12px;
  overflow-x: auto
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-063 -->

<!-- TRASH id=20260702-064 date=2026-07-02 kind=file source="tools/build_review_html.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-064 · 2026-07-02 · file · `tools/build_review_html.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-064__build_review_html.py`

```
#!/usr/bin/env python3
"""
Build an HTML review page for all CDN-art listings that need manual ownership
confirmation. Each listing shows its hero photo + title + checkbox.
"""

import sys, json, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

# 24 CDN listings needing manual review (rank-2 and rank-6+ art sources)
REVIEW_LISTINGS = [
    # rank-2 CDN
    (4513713984, "Hummingbird Nursery Print, Printable Wall Art"),
    (4513714013, "Paris Skyline Print, Black White Wall Art"),
    (4513714191, "Fox Nursery Wall Art, Printable Instant Download"),
    # rank-6+ CDN
    (4509193231, "Sage Lavender Botanical Print, Dusty Rose Wall Art"),
    (4509193237, "Pampas Grass Printable Wall Art, Boho"),
    (4509198434, "Boho Wildflower Printable Wall Art, Sage"),
    (4509198446, "Eucalyptus Branch Printable Wall Art, Botanical"),
    (4512768771, "Sunflower Watercolor Print, Botanical Wall Art"),
    (4512768858, "Cherry Blossom Watercolor Print, Spring Wall Art"),
    (4512770031, "Autumn Maple Printable Wall Art, Fall"),
    (4512772452, "Winter Birch Printable Wall Art"),
    (4512772539, "Sea Turtle Printable Wall Art, Ocean"),
    (4512774863, "Lighthouse Printable Wall Art, Coastal"),
    (4512776173, "Coral Reef Printable Wall Art, Ocean"),
    (4512780614, "Pelican Watercolor Print, Coastal Art"),
    (4513713514, "Japandi Tree Print, Black White Wall Art"),
    (4513713712, "Moon Phases Print, Black White Wall Art"),
    (4513713805, "Minimalist Botanical Print, Black White Wall Art"),
    (4513713922, "Bear Nursery Wall Art, Printable Instant Download"),
    (4513713936, "Owl Nursery Wall Art, Printable Instant Download"),
    (4513713945, "Vintage Botanical Print, Black White Wall Art"),
    (4513713962, "Watercolor Fox Nursery Print, Printable Instant Download"),
    (4515674042, "Minimalist Line Art Print | Modern Wall Decor"),
    (4515676301, "Floral Wreath Art Print | Botanical Wall Decor"),
]

def get_hero_url(client, lid):
    try:
        imgs = client.get_listing_images(lid)
        time.sleep(0.15)
        if not imgs:
            return None
        # rank 1 first, fallback to lowest rank
        imgs_sorted = sorted(imgs, key=lambda i: i.get("rank", 99))
        hero = next((i for i in imgs_sorted if i.get("rank") == 1), imgs_sorted[0])
        return hero.get("url_570xN") or hero.get("url_fullxfull") or None
    except Exception as e:
        print(f"  WARN {lid}: {e}")
        return None

def main():
    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Token refreshed. Fetching hero photos...")

    rows = []
    for lid, title in REVIEW_LISTINGS:
        url = get_hero_url(client, lid)
        print(f"  {lid}  {'OK' if url else 'MISSING'}  {title[:50]}")
        rows.append({"lid": lid, "title": title, "url": url})

    # Build HTML
    cards = ""
    for i, r in enumerate(rows):
        lid   = r["lid"]
        title = r["title"]
        url   = r["url"] or ""
        img_tag = (f'<img src="{url}" alt="{title}" loading="lazy">'
                   if url else '<div class="no-img">No photo found</div>')
        cards += f"""
        <div class="card" id="card-{lid}">
          <label class="cb-wrap">
            <input type="checkbox" id="cb-{lid}" onchange="mark('{lid}')">
            <span class="cb-label">Mark as INCORRECT / Not My Art</span>
          </label>
          {img_tag}
          <div class="meta">
            <span class="title">{title}</span>
            <span class="lid">Listing ID: {lid}</span>
            <a class="etsy-link" href="https://www.etsy.com/listing/{lid}" target="_blank">
              View on Etsy ↗
            </a>
          </div>
        </div>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OnBrand
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-064 -->

<!-- TRASH id=20260702-065 date=2026-07-02 kind=file source="tools/build_review_html_embedded.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-065 · 2026-07-02 · file · `tools/build_review_html_embedded.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-065__build_review_html_embedded.py`

```
#!/usr/bin/env python3
"""
Build a fully self-contained HTML review page with all images base64-embedded.
No internet connection needed to view — works from any local file on any device.
"""

import sys, json, time, base64, urllib.request, urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from etsy_api import EtsyAPIClient

REVIEW_LISTINGS = [
    (4513713984, "Hummingbird Nursery Print, Printable Wall Art"),
    (4513714013, "Paris Skyline Print, Black White Wall Art"),
    (4513714191, "Fox Nursery Wall Art, Printable Instant Download"),
    (4509193231, "Sage Lavender Botanical Print, Dusty Rose Wall Art"),
    (4509193237, "Pampas Grass Printable Wall Art, Boho"),
    (4509198434, "Boho Wildflower Printable Wall Art, Sage"),
    (4509198446, "Eucalyptus Branch Printable Wall Art, Botanical"),
    (4512768771, "Sunflower Watercolor Print, Botanical Wall Art"),
    (4512768858, "Cherry Blossom Watercolor Print, Spring Wall Art"),
    (4512770031, "Autumn Maple Printable Wall Art, Fall"),
    (4512772452, "Winter Birch Printable Wall Art"),
    (4512772539, "Sea Turtle Printable Wall Art, Ocean"),
    (4512774863, "Lighthouse Printable Wall Art, Coastal"),
    (4512776173, "Coral Reef Printable Wall Art, Ocean"),
    (4512780614, "Pelican Watercolor Print, Coastal Art"),
    (4513713514, "Japandi Tree Print, Black White Wall Art"),
    (4513713712, "Moon Phases Print, Black White Wall Art"),
    (4513713805, "Minimalist Botanical Print, Black White Wall Art"),
    (4513713922, "Bear Nursery Wall Art, Printable Instant Download"),
    (4513713936, "Owl Nursery Wall Art, Printable Instant Download"),
    (4513713945, "Vintage Botanical Print, Black White Wall Art"),
    (4513713962, "Watercolor Fox Nursery Print, Printable Instant Download"),
    (4515674042, "Minimalist Line Art Print | Modern Wall Decor"),
    (4515676301, "Floral Wreath Art Print | Botanical Wall Decor"),
]

def get_hero_url(client, lid):
    try:
        imgs = client.get_listing_images(lid)
        time.sleep(0.15)
        if not imgs:
            return None
        imgs_sorted = sorted(imgs, key=lambda i: i.get("rank", 99))
        hero = next((i for i in imgs_sorted if i.get("rank") == 1), imgs_sorted[0])
        return hero.get("url_570xN") or hero.get("url_fullxfull") or None
    except Exception as e:
        print(f"  WARN {lid}: {e}")
        return None

def download_as_base64(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0",
            "Referer": "https://www.etsy.com/"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
        return "data:image/jpeg;base64," + base64.b64encode(data).decode()
    except Exception as e:
        print(f"    download failed: {e}")
        return None

def main():
    client = EtsyAPIClient()
    client.refresh_access_token()
    print("Token refreshed. Fetching and embedding photos...")

    rows = []
    for lid, title in REVIEW_LISTINGS:
        url = get_hero_url(client, lid)
        if url:
            print(f"  {lid}  downloading…  {title[:45]}")
            b64 = download_as_base64(url)
            if b64:
                print(f"         embedded ({len(b64)//1024}KB)")
            else:
                print(f"         embed FAILED — using URL fallback")
        else:
            b64 = None
            print(f"  {lid}  NO URL  {title[:45]}")
        rows.append({"lid": lid, "title": title, "url": url, "b64": b64})

    # Build HTML cards
    cards = ""
    for r in rows:
        lid   = r["lid"]
        title = r["title"]
        src   = r["b64"] or r["url"] or ""
        img_tag = (f'<img src="{src}" alt="{title}">'
                   if src else '<div class="no-img">Photo unavailable</div>')
        cards += f"""
        <div class="card" id="card-{lid}">
          <label class="c
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-065 -->

<!-- TRASH id=20260702-066 date=2026-07-02 kind=file source="tools/build_ss1001_vol2_zip.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-066 · 2026-07-02 · file · `tools/build_ss1001_vol2_zip.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-066__build_ss1001_vol2_zip.py`

```
#!/usr/bin/env python3
"""
Build SS1001 Vol 2 customer download ZIP:
  5 additional America 250th Anniversary 3D sign designs

Output: data/3d_print_signs/america_250/SS1001_america250_3dprint_pack_vol2.zip

Run:  python tools/build_ss1001_vol2_zip.py
"""

from __future__ import annotations
import io
import re
import zipfile
from pathlib import Path

import cairosvg
import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_ZIP = DESIGNS_DIR / "SS1001_america250_3dprint_pack_vol2.zip"

DESIGNS = [
    ("07_america250_banner_4c",  "America 250 Banner"),
    ("08_america250_burst_4c",   "America 250 Burst"),
    ("09_america250_seal_4c",    "America 250 Seal"),
    ("10_america250_shield_4c",  "America 250 Shield"),
    ("11_america250_stamp_4c",   "America 250 Stamp"),
]

Z_BASE  = (0.0, 4.0)
Z_RAISE = (4.0, 6.0)
PPM_BASE   = 0.5
PPM_DESIGN = 1.5


def svg_to_mesh(svg_path: Path, z_bottom: float, z_top: float,
                px_per_mm: float = 1.0) -> trimesh.Trimesh | None:
    content = svg_path.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="0 0 (\S+) (\S+)"', content)
    if not vb:
        print(f"  WARNING: no viewBox in {svg_path.name}")
        return None
    W_mm, H_mm = float(vb.group(1)), float(vb.group(2))
    W_px = max(1, int(W_mm * px_per_mm))
    H_px = max(1, int(H_mm * px_per_mm))

    png_bytes = cairosvg.svg2png(bytestring=content.encode(),
                                  output_width=W_px, output_height=H_px)
    arr = np.array(Image.open(io.BytesIO(png_bytes)).convert("RGBA"))
    mask = arr[:, :, 3] > 128

    if not np.any(mask):
        return None

    mm_per_px = 1.0 / px_per_mm
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    v_idx: dict[tuple, int] = {}

    def v(ix: int, iy: int, z: float) -> int:
        k = (ix, iy, z)
        if k not in v_idx:
            v_idx[k] = len(vertices)
            vertices.append([ix * mm_per_px, iy * mm_per_px, z])
        return v_idx[k]

    def quad(a: int, b: int, c: int, d: int) -> None:
        faces.append([a, b, c])
        faces.append([a, c, d])

    ys, xs = np.where(mask)
    filled: set[tuple[int, int]] = set(zip(xs.tolist(), ys.tolist()))

    for ix, iy in filled:
        a = v(ix,   iy,   z_top);    b = v(ix+1, iy,   z_top)
        c = v(ix+1, iy+1, z_top);    d = v(ix,   iy+1, z_top)
        e = v(ix,   iy,   z_bottom); f = v(ix+1, iy,   z_bottom)
        g = v(ix+1, iy+1, z_bottom); h = v(ix,   iy+1, z_bottom)

        quad(a, b, c, d)
        quad(h, g, f, e)
        if (ix-1, iy) not in filled: quad(a, d, h, e)
        if (ix+1, iy) not in filled: quad(b, f, g, c)
        if (ix,   iy-1) not in filled: quad(e, f, b, a)
        if (ix,   iy+1) not in filled: quad(d, c, g, h)

    return trimesh.Trimesh(
        vertices=np.array(vertices, dtype=np.float32),
        faces=np.array(faces, dtype=np.int32),
        process=True,
    )


_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    '</Types>'
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    '</Relationships>'
)


def _build_3mf_xml(named_meshes: list[tuple[str, trimesh.Trimesh]]) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<model xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
        'unit="millimeter" xml:lang="en-US">',
        "  <resources>",
    ]
    build_item
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-066 -->

<!-- TRASH id=20260702-067 date=2026-07-02 kind=file source="tools/build_ss1001_zip.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-067 · 2026-07-02 · file · `tools/build_ss1001_zip.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-067__build_ss1001_zip.py`

```
#!/usr/bin/env python3
"""
Build the SS1001 customer download ZIP:
  - 5 America 250th Anniversary 3D sign designs
  - Each design folder contains:
      * 1 × .3mf file  — all 3 color layers pre-assembled at correct Z heights
                          (open in Bambu Studio, assign AMS colors, slice, print)
      * 3 × .svg files — individual color layers for custom sizing / advanced users
  - README.txt — printing workflow for both formats

Output: data/3d_print_signs/america_250/SS1001_america250_3dprint_pack.zip

Run:  python tools/build_ss1001_zip.py
"""

from __future__ import annotations
import io
import re
import sys
import zipfile
from pathlib import Path

import cairosvg
import numpy as np
import trimesh
from PIL import Image

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
DESIGNS_DIR = ROOT / "data" / "3d_print_signs" / "america_250"
OUT_ZIP = DESIGNS_DIR / "SS1001_america250_3dprint_pack.zip"

# ── 5 designs to include (slug → display name) ────────────────────────────────
DESIGNS = [
    ("01_america250_america_bold",   "America Bold"),
    ("02_america250_star_badge",     "Star Badge"),
    ("03_america250_freedom_sign",   "Freedom Sign"),
    ("04_america250_happy_4th",      "Happy 4th"),
    ("05_america250_land_free",      "Land of the Free"),
]

# Z-height plan (mm):  base layer = 0→4 mm,  raised design layers = 4→6 mm
Z_BASE  = (0.0, 4.0)
Z_RAISE = (4.0, 6.0)

# Raster resolution per layer type
PPM_BASE   = 0.5   # px/mm — base is a simple solid plate, lower res is fine
PPM_DESIGN = 1.5   # px/mm — design layers need enough res for 0.4mm nozzle details


# ── Mesh builder ──────────────────────────────────────────────────────────────

def svg_to_mesh(svg_path: Path, z_bottom: float, z_top: float,
                px_per_mm: float = 1.0) -> trimesh.Trimesh | None:
    """
    Convert a black-on-transparent SVG layer to a closed 3D mesh.
    Uses cairosvg alpha channel as the fill mask, then builds a
    watertight voxel mesh (one 1-px-thick slab per filled pixel).
    """
    content = svg_path.read_text(encoding="utf-8")
    vb = re.search(r'viewBox="0 0 (\S+) (\S+)"', content)
    if not vb:
        print(f"  WARNING: no viewBox in {svg_path.name}")
        return None
    W_mm, H_mm = float(vb.group(1)), float(vb.group(2))
    W_px = max(1, int(W_mm * px_per_mm))
    H_px = max(1, int(H_mm * px_per_mm))

    png_bytes = cairosvg.svg2png(bytestring=content.encode(),
                                  output_width=W_px, output_height=H_px)
    arr = np.array(Image.open(io.BytesIO(png_bytes)).convert("RGBA"))
    mask = arr[:, :, 3] > 128   # alpha channel → filled region

    if not np.any(mask):
        return None

    mm_per_px = 1.0 / px_per_mm
    vertices: list[list[float]] = []
    faces: list[list[int]] = []
    v_idx: dict[tuple, int] = {}

    def v(ix: int, iy: int, z: float) -> int:
        k = (ix, iy, z)
        if k not in v_idx:
            v_idx[k] = len(vertices)
            vertices.append([ix * mm_per_px, iy * mm_per_px, z])
        return v_idx[k]

    def quad(a: int, b: int, c: int, d: int) -> None:
        faces.append([a, b, c])
        faces.append([a, c, d])

    ys, xs = np.where(mask)
    filled: set[tuple[int, int]] = set(zip(xs.tolist(), ys.tolist()))

    for ix, iy in filled:
        a = v(ix,   iy,   z_top);    b = v(ix+1, iy,   z_top)
        c = v(ix+1, iy+1, z_top);    d = v(ix,   iy+1, z_top)
        e = v(ix,   iy,   z_bottom); f = v(ix+1, iy,   z_bottom)
        g = v(ix+1, iy+1, z_bottom); h = v(ix,   iy+1, z_bottom)

        quad(a, b, c, d)    # top face
        quad(h, g, f, e)    # bottom face
        if (ix-1, iy) not in filled: quad(a, d, h, e)   # left wall
        if (ix+1, iy) not in filled: quad(b, f, g, c)   # right wall
        if (ix,   iy-1) not in filled: quad(e, f, b, a) # front wall
        if (ix,   iy+1) not in filled: quad(d, c, g, h) # back wall

    return trimesh.Trimesh(
       
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-067 -->

<!-- TRASH id=20260702-068 date=2026-07-02 kind=file source="tools/build_wrong_art_audit_html.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-068 · 2026-07-02 · file · `tools/build_wrong_art_audit_html.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-068__build_wrong_art_audit_html.py`

```
#!/usr/bin/env python3
"""Build wrong_art_audit.html — visual comparison of listing photos vs attached files."""
import json, base64, os, sys
from pathlib import Path
from io import BytesIO

ROOT = Path("/home/user/Etsy")
UPSCALED = ROOT / "data" / "digital_products" / "product_files" / "upscaled"

def load_env(path):
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())

load_env(ROOT / ".env")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

with open("/tmp/wrong_art_audit_full.json") as f:
    all_results = json.load(f)

with open(ROOT / "data" / "dp_listing_map.json") as f:
    dp_map = json.load(f)

def art_thumb_b64(dp_id):
    for ext in [".jpg", ".png"]:
        p = UPSCALED / f"{dp_id}{ext}"
        if p.exists() and HAS_PIL:
            try:
                img = Image.open(p).convert("RGB")
                img.thumbnail((120, 120))
                buf = BytesIO()
                img.save(buf, "JPEG", quality=75)
                return base64.b64encode(buf.getvalue()).decode()
            except:
                pass
    return None

mismatches = [r for r in all_results if r.get("art_mismatch")]
unmapped = [r for r in all_results if not r.get("expected_dp") and not r.get("art_mismatch")]
ok = [r for r in all_results if not r.get("art_mismatch") and r.get("expected_dp")]

print(f"Mismatches: {len(mismatches)}, Unmapped: {len(unmapped)}, OK: {len(ok)}")

art_thumbs = {}
all_dp_ids = set(dp_map.keys())
for r in all_results:
    for dp in [r.get("expected_dp"), r.get("best_photo_dp")] + r.get("attached_dps", []):
        if dp:
            all_dp_ids.add(dp)

for dp_id in sorted(all_dp_ids):
    b64 = art_thumb_b64(dp_id)
    if b64:
        art_thumbs[dp_id] = b64

print(f"Loaded {len(art_thumbs)} art thumbnails")


def dist_color(d):
    if d < 20:
        return "#27ae60"
    elif d < 60:
        return "#f39c12"
    else:
        return "#888888"


def top3_html(top3):
    parts = []
    for d, dp in (top3 or []):
        c = dist_color(d)
        parts.append(f'<div style="color:{c};font-size:11px">&nbsp;• {dp} (dist={d})</div>')
    return "".join(parts)


def render_card(r):
    lid = r["listing_id"]
    title = r.get("title", "")
    expected = r.get("expected_dp", "")
    best_photo = r.get("best_photo_dp", "")
    best_dist = r.get("best_photo_dist", 999)
    attached = r.get("attached_dps", [])
    attached_files = r.get("attached_files", [])
    mismatch_reason = r.get("mismatch_reason", "")
    photo_b64 = r.get("photo1_b64", "")
    top3 = r.get("top3_matches", [])

    if r.get("art_mismatch"):
        status = "MISMATCH"
        badge_color = "#e74c3c"
    elif not expected:
        status = "UNMAPPED"
        badge_color = "#f39c12"
    else:
        status = "OK"
        badge_color = "#27ae60"

    if photo_b64:
        photo_html = f'<img src="data:image/jpeg;base64,{photo_b64}" style="width:100%;max-width:200px;border-radius:4px;">'
    else:
        photo_html = '<div style="width:160px;height:160px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#888">No photo</div>'

    exp_thumb = art_thumbs.get(expected, "") if expected else ""
    if exp_thumb:
        exp_html = (f'<img src="data:image/jpeg;base64,{exp_thumb}" style="width:100%;max-width:200px;border-radius:4px;">'
                    f'<br><small style="color:#888">{expected}</small>')
    elif expected:
        exp_html = f'<div style="width:160px;height:120px;background:#333;border-radius:4px;display:flex;align-items:center;justify-content:center;color:#aaa">{expected}<br>No art file</div>'
    else:
        exp_html = '<div style="width:160px;height:80px;background:#222;border-radius:4px;display:flex;align-items:center;justify-content:
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-068 -->

<!-- TRASH id=20260702-069 date=2026-07-02 kind=file source="tools/create_art_listing_new.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-069 · 2026-07-02 · file · `tools/create_art_listing_new.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-069__create_art_listing_new.py`

```
#!/usr/bin/env python3
"""
Create one new wall art listing end-to-end:
  1. Generate art (gpt-image-1)
  2. Generate 2 AI lifestyle room scenes
  3. Composite art into 3 room templates (living room, kitchen/dining, entryway)
  4. Create size guide graphic
  5. Create What's Included graphic
  6. Show all images (save to listing_images folder)
  7. Optionally create+activate Etsy listing

Usage:
  python tools/create_art_listing_new.py --preview   # generate images only, no Etsy
  python tools/create_art_listing_new.py --post       # generate + post to Etsy
  python tools/create_art_listing_new.py --post --pid DP1039  # use specific product ID
"""

import os, sys, json, base64, urllib.request, urllib.error, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

client = EtsyAPIClient()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Room template frame bounds (confirmed) ────────────────────────────────────
ROOM_BOUNDS = {
    'living_room':    (409, 164, 614, 464),   # L, T, R, B
    'kitchen_dining': (400, 166, 624, 494),
    'entryway':       (430, 147, 593, 365),   # Option C, user confirmed
}

ROOM_TEMPLATES = {
    'living_room':    f'{ART_DIR}/DP1007_room_living_room_natural_wood.jpg',
    'kitchen_dining': f'{ART_DIR}/DP1007_room_kitchen_dining_natural_wood.jpg',
    'entryway':       f'{ART_DIR}/DP1007_room_entryway_natural_wood.jpg',
}

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


# ── Image generation ──────────────────────────────────────────────────────────

def gen_image(prompt, out_path, size="1024x1536", quality="high"):
    """Generate an image via gpt-image-1 and save to out_path."""
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt.strip(), "n": 1,
        "size": size, "quality": quality, "output_format": "jpeg"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"  Generated: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return True
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(20)
            else:
                print(f"  ERROR: {e}")
                return False


# ── Compositing ───────────────────────────────────────────────────────────────

def paste_fill(bg_img, art_path, l, t, r, b):
    """Fill the frame opening [l,t,r,b] with art, cropped to fill exactly."""
    art = Image.open(art_path).convert('RGB')
    fw, fh = r - l, b - t
    aw, ah = art.size
    # Fit to fill (cover mode)
    if (aw / ah) < (fw / fh):
        sw, sh = fw, int(fw * ah / aw)
        res = art.resize((sw, sh), Image.LANCZOS)
        cy = (sh - fh) // 2
        crop = res.crop((0, cy, sw, cy + fh))
    else:
        sh, sw = fh, int(fh * aw / ah)
        res = art.resize((s
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-069 -->

<!-- TRASH id=20260702-070 date=2026-07-02 kind=file source="tools/create_bundle_photos.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-070 · 2026-07-02 · file · `tools/create_bundle_photos.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-070__create_bundle_photos.py`

```
#!/usr/bin/env python3
"""
Generate listing photos for the All 4 Planners Bundle (listing 4512188970).
All planner content uses real pages rendered directly from the actual PDF files.
NO AI-generated planner imagery — what you see is exactly what the customer receives.
"""
import os, sys, shutil
import fitz  # pymupdf
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFont, ImageFilter

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
OUT_DIR = os.path.join(ART_DIR, 'bundle_listing_images')
os.makedirs(OUT_DIR, exist_ok=True)

CANVAS = 2400
PAD = 90
GAP = 60
CELL = (CANVAS - 2 * PAD - GAP) // 2   # ~1080 px per cell

PIDS = ['DP1026', 'DP1027', 'DP1028', 'DP1029']
THEME_COLORS = {
    'DP1026': (134, 102, 170),   # lavender
    'DP1027': (222, 151, 198),   # cotton candy pink
    'DP1028': ( 27,  37, 104),   # midnight blue
    'DP1029': (253, 108,  73),   # coral peach
}
NAMES = {
    'DP1026': 'Life Planner',
    'DP1027': 'Student Planner',
    'DP1028': 'Budget Planner',
    'DP1029': 'Fitness Planner',
}
PRICES = {
    'DP1026': '$14.99',
    'DP1027': '$9.99',
    'DP1028': '$12.99',
    'DP1029': '$12.99',
}
PAGES = {
    'DP1026': {'monthly': 11, 'weekly': 47},
    'DP1027': {'monthly': 11, 'weekly': 35},
    'DP1028': {'monthly': 11, 'weekly': 47},
    'DP1029': {'monthly': 11, 'weekly': 35},
}
# Page 4 is the illustrated cover for all planners
COVER_PAGE = 4
STICKER_SHEET = {pid: os.path.join(ART_DIR, f'{pid}_sticker_sheet_4.jpg') for pid in PIDS}
APP_COMPAT_SRC = os.path.join(ART_DIR, 'DP1028_listing_images', '07_app_compatibility.jpg')


# ── PDF rendering ─────────────────────────────────────────────────────────────

def render_pdf_page(pid, page_num, target_width=1800):
    """Render a page from the real planner PDF. page_num is 1-indexed."""
    pdf_path = os.path.join(ART_DIR, f'{pid}.pdf')
    pdf = fitz.open(pdf_path)
    page = pdf[page_num - 1]
    # Scale so the rendered width matches target_width
    scale = target_width / page.rect.width
    mat = fitz.Matrix(scale, scale)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    # Convert to PIL
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    pdf.close()
    return img


# ── Fonts ──────────────────────────────────────────────────────────────────────

def font_bold(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSansBold.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def font_reg(size):
    for path in [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/usr/share/fonts/truetype/freefont/FreeSans.ttf',
    ]:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


# ── iPad mockup compositor ─────────────────────────────────────────────────────

def make_ipad_mockup(planner_img, ipad_w=680, ipad_h=900):
    """
    Composite a planner page image into a simple silver iPad frame.
    Returns an RGBA PIL image.
    """
    RADIUS = 48
    BEZEL = 22
    SILVER = (190, 190, 194)
    DARK_EDGE = (140, 140, 145)

    ipad = Image.new('RGBA', (ipad_w, ipad_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(ipad)

    # Outer frame (dark edge for depth)
    draw.rounded_rectangle([0, 0, ipad_w - 1, ipad_h - 1],
                           radius=RADIUS, fill=DARK_EDGE)
    # Main silver body
    draw.rounded_rectangle([2, 2, ipad_w - 3, ipad_h - 3],
                 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-070 -->

<!-- TRASH id=20260702-071 date=2026-07-02 kind=file source="tools/create_gallery_wall_sets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-071 · 2026-07-02 · file · `tools/create_gallery_wall_sets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-071__create_gallery_wall_sets.py`

```
"""
Create 3 Gallery Wall Set of 5 listings on Etsy.
Sets: Coastal, Botanical, Woodland Animal
"""

import os
import sys
import json
import time

# Load .env manually (never use load_dotenv)
env = {}
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip()
os.environ.update(env)

sys.path.insert(0, '/home/user/Etsy/tools')
from etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()

ZIP_DIR = '/home/user/Etsy/data/digital_products/print_zips'

# ─── Description builder ─────────────────────────────────────────────────────

def build_description(theme_name, prints_list, emoji_header):
    prints_section = "\n".join(f"• {p}" for p in prints_list)
    return f"""Instant download printable wall art — digital download delivered immediately after purchase, ready to print at home or at any print shop.

Transform your walls with this curated {theme_name} gallery wall set — 5 beautifully coordinated prints that look stunning grouped together. Each piece is designed to complement the others in palette, style, and mood, making it effortless to create a polished, intentional gallery wall.

━━━━━━━━━━━━━━━━━━━━━━━━
📦 WHAT'S INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
✅ 5 coordinated printable art files
✅ Each file includes 10 print sizes: 4×6, 8×12, 12×18, 16×24 (2:3 ratio), 8×10, 16×20 (4:5), A4, A3 (A-series), 8×8, 12×12 (square)
✅ All files at 300 DPI — print-shop ready
✅ Organized in labeled folders by size ratio
✅ README.txt with printing instructions

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ PRINTS INCLUDED
━━━━━━━━━━━━━━━━━━━━━━━━
{prints_section}

━━━━━━━━━━━━━━━━━━━━━━━━
🖨️ HOW TO PRINT
━━━━━━━━━━━━━━━━━━━━━━━━
1. Download your files instantly from Etsy
2. Choose the size that matches your frame
3. Print at home or upload to Costco, Walgreens, Shutterfly, or any local print shop
4. Print at 100% / "Actual Size" — do not scale to fit

━━━━━━━━━━━━━━━━━━━━━━━━
📐 GALLERY WALL TIPS
━━━━━━━━━━━━━━━━━━━━━━━━
• Mix sizes for visual interest: try a large 16×20 as anchor with four 8×10s around it
• Leave 2–3 inches between frames
• Use a level and painter's tape to plan your layout before hammering
• Matching frame color unifies the wall — try all black, all white, or all natural wood

━━━━━━━━━━━━━━━━━━━━━━━━
❓ FAQ
━━━━━━━━━━━━━━━━━━━━━━━━
Q: When do I receive my files?
A: Instantly after purchase — Etsy sends a download link to your email immediately.

Q: Can I print these at a print shop?
A: Yes! All files are 300 DPI and print-shop ready. Works at Costco, Walgreens, Shutterfly, and any local printer.

Q: What sizes are included?
A: 10 sizes per print: 4×6, 8×12, 12×18, 16×24, 8×10, 16×20, A4, A3, 8×8, 12×12.

Q: Is this a physical item?
A: No — digital download only. No physical prints are shipped.

━━━━━━━━━━━━━━━━━━━━━━━━
© COPYRIGHT
━━━━━━━━━━━━━━━━━━━━━━━━
© OnBrandCraftz. Personal use only. Not for resale or redistribution."""


# ─── Sets definition ─────────────────────────────────────────────────────────

SETS = [
    {
        "name": "Coastal Gallery Wall Set",
        "title": "Coastal Gallery Wall Set of 5, Printable Wall Art, Instant Download",
        "price": 24.99,
        "dp_ids": ["DP1022", "DP1044", "DP1039", "DP1045", "DP1031"],
        "prints": [
            "Full Moon Ocean — serene moonlit seascape",
            "Ocean Wave — dynamic watercolor ocean wave",
            "Hummingbird — vibrant nature study, coastal garden mood",
            "Lavender Fields — soft purple fields under open sky",
            "Abstract Brushstroke — flowing coastal-inspired abstract",
        ],
        "tags": [
            "coastal gallery set",
            "beach wall art set",
            "ocean wall prints",
            "gallery wall set",
            "set of 5 prints",
            "coastal home decor",
            "beach house art",
            "printable art set",
            
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-071 -->

<!-- TRASH id=20260702-072 date=2026-07-02 kind=file source="tools/create_new_art_listings.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-072 · 2026-07-02 · file · `tools/create_new_art_listings.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-072__create_new_art_listings.py`

```
#!/usr/bin/env python3
"""
Create 8 new wall art listings covering distinct art categories,
create/organize shop sections, and update existing 15 listings into sections.
"""

import os, sys, json, base64, urllib.request, urllib.error, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.art_creation_tools import enrich_prompt_with_medium, random_painting_medium, HAND_PAINTED_STYLES
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'
CANVAS = 2400

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"
        print("  Token refreshed.")


# ── Image generation ──────────────────────────────────────────────────────────

def gen_image(prompt, out_path, size="1024x1536"):
    payload = json.dumps({
        "model": "gpt-image-1", "prompt": prompt, "n": 1,
        "size": size, "quality": "high", "output_format": "jpeg"
    }).encode()
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {OPENAI_KEY}"},
        method="POST"
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            img_bytes = base64.b64decode(data["data"][0]["b64_json"])
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"  Generated: {os.path.basename(out_path)} ({len(img_bytes)//1024}KB)")
            return
        except Exception as e:
            if attempt < 2:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(15)
            else:
                raise


def composite(bg_path, art_path, out_path, fc, art_pct=0.33):
    """Composite art onto room background with realistic 3D frame."""
    room = Image.open(bg_path).convert('RGB').resize((CANVAS, CANVAS), Image.LANCZOS)
    art = Image.open(art_path).convert('RGB')
    art_w = int(CANVAS * art_pct)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)
    mat_w, frame_w = 44, 20
    full_w = art_w + 2 * mat_w + 2 * frame_w
    full_h = art_h + 2 * mat_w + 2 * frame_w
    px = (CANVAS - full_w) // 2
    py = int(CANVAS * 0.13)
    print(f"  frame: {full_w}x{full_h}, bottom={py+full_h}px ({(py+full_h)/CANVAS*100:.1f}%)")

    ao = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ao_draw = ImageDraw.Draw(ao)
    for pad in range(50, 0, -5):
        alpha = int(55 * (1 - (pad / 50) ** 1.5))
        ao_draw.rectangle([px-pad, py-pad, px+full_w+pad, py+full_h+pad], fill=(0,0,0,alpha))
    ao = ao.filter(ImageFilter.GaussianBlur(radius=28))
    room = Image.alpha_composite(room.convert('RGBA'), ao).convert('RGB')

    shadow = Image.new('RGBA', (CANVAS, CANVAS), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle([px+10, py+14, px+full_w+10, py+full_h+14], fill=(0,0,0,65))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=16))
    room = Image.alpha_composite(room.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(room)
    draw.rectangle([px, py, px+full_w, py+full_h], fill=fc)
    fc_hi = tuple(min(255, c+50) for c in fc)
    fc_sh = tuple(max(0, c-50) for c in fc)
    bv = 4
    draw.polygon([px, py, px+full_w, py, px+full_w-b
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-072 -->

<!-- TRASH id=20260702-073 date=2026-07-02 kind=file source="tools/create_svg_bundle_heroes.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-073 · 2026-07-02 · file · `tools/create_svg_bundle_heroes.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-073__create_svg_bundle_heroes.py`

```
#!/usr/bin/env python3
"""
Create bundle grid hero images for SVG bundle Etsy listings.
Renders actual SVG files to PNG, builds a grid collage, uploads as rank=1 image.
"""

import sys
import os
import time
import math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

import dotenv
dotenv.load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
from PIL import Image, ImageDraw, ImageFont

from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Config ────────────────────────────────────────────────────────────────────

CANVAS_SIZE = 2400
BACKGROUND_COLOR = "#FDF8F0"  # warm cream
CELL_BG_COLOR = "#FFFFFF"     # white cell background
CELL_SIZE = 550               # each cell is 550×550
CELL_PADDING = 20             # gap between cell edge and design
CELL_GAP = 20                 # gap between cells
BOTTOM_STRIP_HEIGHT = 200     # px for text area at bottom
COLS = 4
ROWS = 3
MAX_DESIGNS = 12

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Bundle definitions
BUNDLES = [
    {
        "listing_id": 4514130045,
        "commercial_listing_id": 4515439743,
        "name": "Floral SVG Bundle",
        "svg_folder": "data/svg_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514134583,
        "commercial_listing_id": 4515439751,
        "name": "Christian SVG Bundle",
        "svg_folder": "data/faith_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514136783,
        "commercial_listing_id": 4515439755,
        "name": "Graduation SVG Bundle 2026",
        "svg_folder": "data/grad_pack/SVG",
        "total_designs": 10,
        "line2_count": "10 Designs Included",
    },
    {
        "listing_id": 4514392281,
        "commercial_listing_id": 4515437432,
        "name": "Mom Life SVG Bundle",
        "svg_folder": "data/mom_life_pack/SVG",
        "total_designs": 20,
        "line2_count": "20 Designs Included",
    },
    {
        "listing_id": 4514536935,
        "commercial_listing_id": 4515439763,
        "name": "Good Vibes SVG Bundle",
        "svg_folder": "data/groovy_pack/SVG",
        "total_designs": 20,
        "line2_count": "20 Designs Included",
    },
    {
        "listing_id": None,  # commercial only
        "commercial_listing_id": 4515437442,
        "name": "Western SVG Bundle",
        "svg_folder": "data/svg_bundles/western/SVG",
        "total_designs": 12,
        "line2_count": "12 Designs Included",
    },
]

REPO_ROOT = Path(__file__).parent.parent


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def render_svg_to_pil(svg_path: Path, target_size: int) -> Image.Image | None:
    """Render an SVG file to a PIL RGBA image at target_size×target_size."""
    try:
        png_bytes = cairosvg.svg2png(
            url=str(svg_path),
            output_width=target_size,
            output_height=target_size,
        )
        img = Image.open(BytesIO(png_bytes)).convert("RGBA")
        return img
    except Exception as e:
        print(f"    [WARN] Failed to render {svg_path.name}: {e}")
        return None


def create_cell(svg_img: Image.Image) -> Image.Image:
    """
    Create a CELL_SIZE×CELL_SIZE cell:
    - White background with 8px gap on each side
    - SVG image rendered inside with CELL_PADDING on all sides
    """
    cell = Image.new("RGBA", (CELL_SIZE, CELL_SIZE), (255, 255, 255, 0))

    # White rectangle (leave 8px gap from edge for visual breathing room)
    gap = 8
    white_rect = Image.new("RGBA", (CELL_SIZE - gap * 2, CELL_SIZE - gap * 2), (255, 255, 255, 255))
    cell.paste(white_rect, (gap, gap), white_rect)

    # Calculate inner area for the design
    inner_w = CELL_SIZE - gap * 2 - CELL_PADDING * 2
 
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-073 -->

<!-- TRASH id=20260702-074 date=2026-07-02 kind=file source="tools/create_svg_product_heroes.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-074 · 2026-07-02 · file · `tools/create_svg_product_heroes.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-074__create_svg_product_heroes.py`

```
#!/usr/bin/env python3
"""
Create TWO new images for every SVG bundle listing:
  rank=1 → 3-product flat lay hero (actual SVG designs composited onto product mockups)
  rank=2 → full bundle grid collage (every design the buyer receives)

Replaces the existing AI-generated fakes with real product composites.
"""

import sys
import os
import time
import json
import base64
import urllib.request
import math
from pathlib import Path
from io import BytesIO

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

import cairosvg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from etsy_api import EtsyAPIClient, EtsyAPIError

# ── Constants ─────────────────────────────────────────────────────────────────

OPENAI_KEY = os.getenv("OPENAI_API_KEY", "")
CANVAS = 2400
BG_COLOR = "#FDF8F0"
DARK_STRIP = "#2C2C2C"

FONT_BOLD   = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG    = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Prompts for images.edit() — we pass the SVG design PNG and ask for a realistic product photo
PRODUCT_EDIT_PROMPTS = {
    "tshirt": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "heat-transfer vinyl graphic onto a plain cream-white crew-neck t-shirt laid flat. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the shirt chest. "
        "(2) The design must sit at mid-chest — the vertical center of the design should be "
        "approximately 45% down from the top collar, NOT near the neckline or shoulders. "
        "(3) The design should be about 35-40% of the shirt width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown — do not alter "
        "or simplify the design. "
        "Product setting: flat lay photography on warm cream linen surface, soft even natural "
        "daylight from above, no harsh shadows. Fabric cotton texture visible. Realistic "
        "screen-printed appearance — not floating or pasted. No hands, no mannequin. "
        "Professional Etsy product photography."
    ),
    "hoodie": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "heat-transfer vinyl graphic onto a plain cream-white pullover hoodie laid flat "
        "with the hood folded at the top. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the hoodie chest. "
        "(2) The design must sit at mid-chest level — the vertical center of the design should "
        "be approximately 50-55% down from the very top of the folded hood, well below the hood "
        "opening and kangaroo pocket. NOT near the collar, NOT near the hood. "
        "(3) The design should be about 35-40% of the hoodie width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown. "
        "Product setting: flat lay photography on warm cream linen surface, soft even natural "
        "daylight from above. Fleece fabric texture visible. Realistic screen-printed "
        "appearance. No hands, no mannequin. Professional Etsy product photography."
    ),
    "tote": (
        "Take the graphic design shown in this image and apply it as a screen-printed or "
        "vinyl design onto the front panel of a natural canvas tote bag. "
        "PLACEMENT RULES (must follow exactly): "
        "(1) The design must be horizontally centered on the tote front panel. "
        "(2) The design must be vertically centered on the main body of the bag — centered "
        "between the bottom seam and the handle attachment points, NOT near the handles. "
        "(3) The design should fill about 55-65% of the bag panel width. "
        "Reproduce all design colors, text, and graphic elements exactly as shown. "
        "Product setting: tote bag upright on warm cream linen surface
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-074 -->

<!-- TRASH id=20260702-075 date=2026-07-02 kind=file source="tools/update_standalone_sticker_listings.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-075 · 2026-07-02 · file · `tools/update_standalone_sticker_listings.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-075__update_standalone_sticker_listings.py`

```
#!/usr/bin/env python3
"""
Update standalone sticker pack listings with new per-planner 11-sheet ZIPs.
Also updates All 4 Planners Bundle description from 300+ to 800+ stickers.
"""
import os, sys, json, urllib.request, urllib.error, time
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# Standalone listings: (name, listing_id, zip_file)
STANDALONE = [
    ('Lavender Pack',      4512255514, 'DP1026_sticker_pack.zip'),
    ('Cotton Candy Pack',  4512254015, 'DP1027_sticker_pack.zip'),
    ('Midnight Blue Pack', 4512255536, 'DP1028_sticker_pack.zip'),
    ('Coral Peach Pack',   4512254027, 'DP1029_sticker_pack.zip'),
]

# All 4 Packs Bundle gets all 4 ZIPs
BUNDLE_LISTING = 4512254035
BUNDLE_ZIPS = [
    'DP1026_sticker_pack.zip',
    'DP1027_sticker_pack.zip',
    'DP1028_sticker_pack.zip',
    'DP1029_sticker_pack.zip',
]

# All 4 Planners Bundle — description update only (800+ stickers now)
PLANNERS_BUNDLE_LISTING = 4512188970


def refresh():
    client.refresh_access_token()
    auth_headers["Authorization"] = f"Bearer {client.access_token}"


def get_existing_files(listing_id):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read()).get('results', [])


def delete_file(listing_id, file_id, filename):
    del_req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{listing_id}/files/{file_id}",
        headers=auth_headers, method="DELETE")
    try:
        urllib.request.urlopen(del_req, timeout=15)
        print(f"  Deleted: {filename}")
        time.sleep(0.5)
    except Exception as e:
        print(f"  Could not delete {filename}: {e}")


def upload_zip(listing_id, zip_filename, rank=1):
    zip_path = os.path.join(ART_DIR, zip_filename)
    for attempt in range(3):
        try:
            result = client.upload_listing_file(listing_id, zip_path, rank=rank)
            print(f"  Uploaded: {zip_filename} (file_id={result.get('listing_file_id')})")
            return True
        except EtsyAPIError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                print(f"  Upload failed ({e.status}): {e}")
                return False
    return False


def patch_listing(lid, payload):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/shops/{shop_id}/listings/{lid}",
        data=data,
        headers={**auth_headers, "Content-Type": "application/json"},
        method="PATCH")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as e:
            if e.status == 401:
                refresh()
            elif e.status == 429:
                time.sleep(15)
            else:
                raise
    raise RuntimeError(f"Failed to patch listing {lid}")


def get_listing(lid):
    req = urllib.request.Request(
        f"https://openapi.etsy.com/v3/application/listings/{lid}",
        headers=auth_headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def updat
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-075 -->

<!-- TRASH id=20260702-076 date=2026-07-02 kind=file source="tools/publish_coloring_and_paper.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-076 · 2026-07-02 · file · `tools/publish_coloring_and_paper.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-076__publish_coloring_and_paper.py`

```
#!/usr/bin/env python3
"""
publish_coloring_and_paper.py — Create, photo, upload, and activate listings for:
  • 11 Kawaii Coloring Page sets (5 pages/ZIP each) at $3.99
  • 12 Digital Paper Packs (5 patterns/ZIP each) at $4.99

Photos are generated with PIL (product grids, close-ups, info graphics) plus one
AI-generated flat-lay background per product type (reused across all listings in
that type) to satisfy the lifestyle hero photo requirement.

Usage:
    python tools/publish_coloring_and_paper.py --dry-run    # preview, no API calls
    python tools/publish_coloring_and_paper.py --type coloring  # coloring only
    python tools/publish_coloring_and_paper.py --type paper     # paper only
    python tools/publish_coloring_and_paper.py              # both
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont, ImageOps
from tools.etsy_api import EtsyAPIClient
from tools.image_gen import generate_image, SQUARE

SHOP_ID = 65012858

COLORING_DIR = ROOT / "data" / "digital_products" / "coloring_pages"
SETS_DIR     = COLORING_DIR / "sets"
PAPER_DIR    = ROOT / "data" / "digital_products" / "digital_paper"
MOCKUPS_DIR  = ROOT / "data" / "digital_products" / "listing_mockups"
MOCKUPS_DIR.mkdir(parents=True, exist_ok=True)

PHOTO_SIZE = (2400, 2400)

# ─── Shared listing constants ──────────────────────────────────────────────────

COLORING_TAGS = [
    # No tag may duplicate a phrase already in the title
    # Title: "Kawaii Coloring Pages Set XX, 5 Printable, Instant Download"
    # Removed duplicates: kawaii coloring, instant download, coloring pages set
    "adult coloring pages", "printable coloring", "coloring sheet pdf",
    "coloring book pdf",    "digital coloring",   "kawaii art print",
    "printable art page",   "black white art",    "line art print",
    "coloring book gift",   "diy coloring pages", "art therapy print",
    "kawaii line art",
]

PAPER_TAGS = [
    # Title: "{Theme} Digital Paper Pack, Scrapbook, Instant Download"
    # Removed duplicates: digital paper pack, instant download
    "scrapbook paper",      "printable paper",    "goodnotes background",
    "digital background",   "pattern paper",      "digital planner",
    "scrapbook digital",    "background paper",   "paper printable",
    "kawaii paper",         "digital download",   "digital paper kit",
    "scrapbooking kit",
]

AI_DISCLOSURE = (
    "\n\n━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "🤖 ABOUT THIS DESIGN\n"
    "━━━━━━━━━━━━━━━━━━━━━━━━\n"
    "This product was designed using AI image generation tools, with original prompts, "
    "curation, and finishing by the seller. All products are reviewed for quality before listing."
)

THEME_DISPLAY = {
    "lavender_dreams": "Lavender Dreams",
    "cherry_blossom": "Cherry Blossom",
    "coral_peach": "Coral Peach",
    "cotton_candy": "Cotton Candy",
    "celestial_night": "Celestial Night",
    "matcha_serenity": "Matcha Serenity",
    "mermaidcore": "Mermaidcore",
    "midnight_blue": "Midnight Blue",
    "mocha_latte": "Mocha Latte",
    "ocean_breeze": "Ocean Breeze",
    "sage_garden": "Sage Garden",
    "sunflower_studio": "Sunflower Studio",
}

THEME_COLORS = {
    "lavender_dreams":  ("#8666AA", "#FAF7FF"),
    "cherry_blossom":   ("#F4A7B9", "#FFF5F7"),
    "coral_peach":      ("#FD6C49", "#FFF8F4"),
    "cotton_candy":     ("#DE97C6", "#FFF6FC"),
    "celestial_night":  ("#1E1B4B", "#F0EEF8"),
    "matcha_serenity":  ("#6B8F5E", "#F7F9F3"),
    "mermaidcore":      ("#4ABFBF", "#F0FAFF"),
    "midnight_blue":    ("#1B2568", "#F0F5FF"),
    "mocha_latte":      ("#8B5E3C", "#FDF8F0"),
    "ocean_breeze":     ("#3B8E8A", "#F0FAFA"),
    "sage_garden":      ("#8BA888", "#F6F8F2"),
    "sunflower_studio": ("#F4C430", "#FFFDF0"),
}


# ─── PIL helpers ────────────────────────────────────────────────
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-076 -->

<!-- TRASH id=20260702-077 date=2026-07-02 kind=file source="tools/publish_coloring_drafts.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-077 · 2026-07-02 · file · `tools/publish_coloring_drafts.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-077__publish_coloring_drafts.py`

```
#!/usr/bin/env python3
"""
publish_coloring_drafts.py — Create Etsy DRAFT listings for the fun_basic and
kawaii coloring page packs using the pre-written content in
listing_fun_basic_20260616.json / listing_kawaii_20260616.json.

All 10 listing photos per pack are generated with OpenAI gpt-image-1 via
tools/listing_photo_pipeline.py (the CLAUDE.md-mandated standard):
  - 6 single-design lifestyle/detail shots via generate_verified_photo()
    (images.edit on the REAL coloring page PNG, physics="flat_paper",
    self-verified against the source file)
  - 2 multi-design collection flat lays via build_flat_lay() (AI-generated
    background + pixel-perfect paste of the REAL PNGs — never AI-rendered,
    per the "garbles small text with 5+ inputs" rule)
  - 2 informational cards (what's included / how to print) — AI-generated
    background + a real page thumbnail pasted in + PIL text overlay,
    matching the SS-series "infographics: images.generate background + PIL
    text overlay" rule

Listings are created with state="draft" and this script NEVER calls
update_listing(..., {"state": "active"}) — Scott reviews photos, title,
description, and price before anything goes live.

Usage:
    python tools/publish_coloring_drafts.py --dry-run     # build photos only, no API calls
    python tools/publish_coloring_drafts.py                # build photos + create both drafts
    python tools/publish_coloring_drafts.py --pack kawaii  # just one pack
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image, ImageDraw, ImageFont

from tools.etsy_api import EtsyAPIClient
from tools.listing_photo_pipeline import (
    PhotoResult,
    _client,
    build_flat_lay,
    generate_verified_photo,
)

CP_DIR = ROOT / "data" / "digital_products" / "coloring_pages"
SETS_DIR = CP_DIR / "sets"
PHOTO_ROOT = CP_DIR / "_listing_photos"

PRICE_FLOOR = 4.99  # etsy_api.pre_publish_gate enforces this minimum — the
                     # pre-written $3.99 in the listing JSONs is bumped up to
                     # this floor (still ends in .99) so the listing can be created.

PACKS = {
    "fun_basic": {
        "json": CP_DIR / "listing_fun_basic_20260616.json",
        "prefix": "CB",
        "hero_pages": [1, 5, 10, 15, 3, 8],
        "grid_a": [2, 4, 6, 7, 9, 12],
        "grid_b": [11, 13, 14, 16, 18, 20],
        "card_thumb": 1,
        "lifestyle_props": (
            "a few scattered crayons in primary colors (red, blue, yellow, green), "
            "a small wooden crayon box, a child's light wood desk"
        ),
        "bg_prompt": (
            "Overhead flat-lay background photo: warm light wood desk surface, "
            "a loose scatter of bright primary-colored crayons along the edges "
            "of the frame, a couple of small wooden alphabet blocks in a corner. "
            "Bright clean natural daylight, no text, no watermark, no logos, "
            "center area left clean and uncluttered."
        ),
    },
    "kawaii": {
        "json": CP_DIR / "listing_kawaii_20260616.json",
        "prefix": "CP",
        "hero_pages": [1, 5, 10, 15, 3, 8],
        "grid_a": [2, 4, 6, 7, 9, 12],
        "grid_b": [11, 13, 14, 16, 18, 20],
        "card_thumb": 1,
        "lifestyle_props": (
            "a tin of colored pencils fanned open, a small watercolor palette, "
            "a sprig of dried baby's breath, a cream linen-textured desk"
        ),
        "bg_prompt": (
            "Overhead flat-lay background photo: soft cream linen-textured desk "
            "surface, a tin of colored pencils and a small watercolor palette "
            "tucked in one corner, a sprig of dried flowers in another corner. "
            "Bright soft natural daylight, no text, no watermark, no logos, "
            "center area left clean and uncluttered."
        ),
    },
}


def page_pat
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-077 -->

<!-- TRASH id=20260702-078 date=2026-07-02 kind=file source="tools/publish_ss1001_draft.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-078 · 2026-07-02 · file · `tools/publish_ss1001_draft.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-078__publish_ss1001_draft.py`

```
#!/usr/bin/env python3
"""
publish_ss1001_draft.py — Create the SS1001 America 250 sign pack as an Etsy DRAFT.

Creates the listing in draft state, uploads all 10 photos and both customer ZIPs
(Vol 1 + Vol 2). NEVER activates the listing — Scott publishes from Shop Manager.

Usage:
  python tools/publish_ss1001_draft.py --dry-run   # gate check + plan, no API calls
  python tools/publish_ss1001_draft.py             # create the draft
"""

import re, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

BASE     = Path("data/3d_print_signs/america_250")
PHOTO_DIR = BASE / "listing_photos" / "final_v2"
ZIP_VOL1 = BASE / "SS1001_america250_3dprint_pack_vol1.zip"
ZIP_VOL2 = BASE / "SS1001_america250_3dprint_pack_vol2.zip"

TITLE = "America 250 SVG, 10 Patriotic 3D Print Signs, Instant Download"

TAGS = [
    "patriotic svg files", "3d print svg", "250th anniversary",
    "bambu studio svg", "wall sign svg", "patriotic wall decor",
    "4th of july sign", "svg cut file", "america sign svg",
    "printable sign", "patriotic decor", "3d wall sign", "digital download",
]

PHOTOS = [PHOTO_DIR / f"photo_{str(i).zfill(2)}_{name}.jpg" for i, name in [
    (1,  "hero_gallery_wall"),
    (2,  "mantel_sign"),
    (3,  "porch_sign"),
    (4,  "tieredtray_sign"),
    (5,  "yard_sign"),
    (6,  "collection_overview"),
    (7,  "bambu_howto"),
    (8,  "detail_closeup"),
    (9,  "whats_included"),
    (10, "design_lineup"),
]]


def load_description() -> str:
    """Pull the DESCRIPTION block out of SS1001_listing_content.md."""
    md = (BASE / "SS1001_listing_content.md").read_text()
    m = re.search(r"### DESCRIPTION\n\n(.*?)\n---\n\n## LISTING PHOTOS PLAN", md, re.S)
    if not m:
        raise SystemExit("Could not extract DESCRIPTION from SS1001_listing_content.md")
    return m.group(1).strip()


def main():
    dry_run = "--dry-run" in sys.argv

    description = load_description()
    listing_body = {
        "title": TITLE,
        "description": description,
        "price": 14.99,
        "quantity": 999,
        "who_made": "i_did",
        "when_made": "made_to_order",
        "is_supply": False,
        "taxonomy_id": 2078,
        "tags": TAGS,
        "materials": ["digital download", "SVG file", "3MF file"],
        "state": "draft",
        "type": "download",
    }

    # Pre-flight: all files must exist
    required = PHOTOS + [ZIP_VOL1, ZIP_VOL2]
    missing = [p for p in required if not p.exists()]
    if missing:
        raise SystemExit("Missing files:\n" + "\n".join(f"  ✗ {p}" for p in missing))

    failures = EtsyAPIClient.pre_publish_gate(listing_body)
    if failures:
        raise SystemExit("Quality gate FAILED:\n" + "\n".join(f"  ✗ {f}" for f in failures))

    print(f"✓ Quality gate passed")
    print(f"  Title: {len(TITLE)} chars | Price: $14.99 | Tags: {len(TAGS)} | "
          f"Desc: {len(description)} chars")
    print(f"  Vol 1 ZIP: {ZIP_VOL1.stat().st_size // 1024} KB")
    print(f"  Vol 2 ZIP: {ZIP_VOL2.stat().st_size // 1024} KB")

    if dry_run:
        print("\n[DRY RUN] Would create DRAFT listing:")
        print(f"  Title: {TITLE}")
        print(f"  Price: $14.99 | taxonomy 2078 | type download | state draft")
        for i, p in enumerate(PHOTOS, 1):
            print(f"  Photo {i:02d}: {p.name}")
        print(f"  Digital file 1: {ZIP_VOL1.name}")
        print(f"  Digital file 2: {ZIP_VOL2.name}")
        return

    from dotenv import load_dotenv
    load_dotenv()
    c = EtsyAPIClient()

    resp = c.create_listing(listing_body)
    lid = resp["listing_id"]
    print(f"\n✓ Draft listing created: listing_id={lid}")
    print(f"  https://www.etsy.com/listing/{lid}")

    for rank, photo in enumerate(PHOTOS, start=1):
        c.upload_listing_image(lid, str(photo), rank=rank)
        print(f"  ✓ Photo {rank:02d}/10: {photo.name}")
        time.sleep(2.0)  # avoid duplicate-rank race (CLAUDE.md API quirk)

    c.upload_listing_fi
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-078 -->

<!-- TRASH id=20260702-079 date=2026-07-02 kind=file source="tools/shorten_titles.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-079 · 2026-07-02 · file · `tools/shorten_titles.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-079__shorten_titles.py`

```
#!/usr/bin/env python3
"""
Shorten all active Etsy listing titles to ≤70 characters.

Etsy 2026 algorithm: titles > 70 chars face mobile ranking penalty.
Data: shortened titles saw +34% mobile CTR and +4.2 avg position improvement.

Strategy:
  - Split title on ' | ' separators
  - Keep segments from the front until adding the next would exceed 70 chars
  - Always keep at least the first segment (primary keyword)
  - If first segment alone > 70 chars, trim at last word boundary

Usage:
  python tools/shorten_titles.py --dry-run    # preview only
  python tools/shorten_titles.py               # apply updates
  python tools/shorten_titles.py --lid 12345  # single listing
"""

import os, sys, json, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

MAX_CHARS = 70


def smart_shorten(title: str) -> str:
    """Shorten title to ≤ MAX_CHARS by dropping trailing pipe-segments."""
    if len(title) <= MAX_CHARS:
        return title

    segments = [s.strip() for s in title.split('|')]
    # Always keep segment 0 (primary keyword)
    result = segments[0].strip()
    if len(result) > MAX_CHARS:
        # Trim at last word boundary
        result = result[:MAX_CHARS].rsplit(' ', 1)[0].rstrip(' |')
        return result

    for seg in segments[1:]:
        candidate = result + ' | ' + seg
        if len(candidate) <= MAX_CHARS:
            result = candidate
        else:
            break

    return result.rstrip(' |')


def fetch_active_listings(client) -> list:
    headers = {
        'Authorization': f'Bearer {client.access_token}',
        'x-api-key': f'{client.client_id}:{client.client_secret}',
    }
    listings, offset = [], 0
    while True:
        url = (f'https://openapi.etsy.com/v3/application/shops/{client.shop_id}'
               f'/listings/active?limit=100&offset={offset}')
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())
        batch = data.get('results', [])
        listings.extend(batch)
        if len(batch) < 100:
            break
        offset += 100
        time.sleep(0.3)
    return listings


def patch_title(client, listing_id: int, new_title: str) -> bool:
    try:
        client.update_listing(listing_id, {'title': new_title})
        return True
    except EtsyAPIError as e:
        if e.status == 429:
            time.sleep(15)
            try:
                client.update_listing(listing_id, {'title': new_title})
                return True
            except EtsyAPIError:
                pass
        print(f'    PATCH failed for {listing_id}: {e}')
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='Preview only')
    parser.add_argument('--lid', type=int, help='Single listing ID')
    args = parser.parse_args()

    client = EtsyAPIClient()
    client.refresh_access_token()

    print('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━')
    print('  Title Shortener — Etsy 2026 Algorithm Compliance')
    print('  Target: ≤70 chars per title')
    print('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n')

    if args.lid:
        headers = {
            'Authorization': f'Bearer {client.access_token}',
            'x-api-key': f'{client.client_id}:{client.client_secret}',
        }
        url = f'https://openapi.etsy.com/v3/application/listings/{args.lid}'
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            listing = json.loads(resp.read())
        listings = [listing]
    else:
        print('  Fetching all activ
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-079 -->

<!-- TRASH id=20260702-080 date=2026-07-02 kind=file source="tools/rebuild_sticker_pack.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-080 · 2026-07-02 · file · `tools/rebuild_sticker_pack.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-080__rebuild_sticker_pack.py`

```
#!/usr/bin/env python3
"""
Rebuild sticker pack ZIP for a planner with all approved sheets,
replace the digital file on Etsy, and update the listing description.

Usage:
  python tools/rebuild_sticker_pack.py --pid DP1026 --sheets 11 --listing 4509179201
"""
import os, sys, json, zipfile, urllib.request, urllib.error, time, argparse, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
_env_path = ROOT / '.env'
if _env_path.exists():
    with open(_env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())

from tools.etsy_api import EtsyAPIClient, EtsyAPIError

client = EtsyAPIClient()
client.refresh_access_token()
shop_id = client.shop_id
auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key": f"{client.client_id}:{client.client_secret}",
}

ART_DIR = str(ROOT / 'data' / 'digital_products' / 'product_files')

SHEET_NAMES_BASE = {
    1: 'sheet_01_functional_planning',
    2: 'sheet_02_widget_trackers',
    3: 'sheet_03_planner_stationery',
    4: 'sheet_04_cozy_lifestyle',
    5: 'sheet_05_seasonal_holiday',
}

SHEET_NAMES_BY_PID = {
    'DP1026': {
        6:  'sheet_06_self_care_wellness',
        7:  'sheet_07_affirmations_milestones',
        8:  'sheet_08_moon_celestial',
        9:  'sheet_09_plants_botanical',
        10: 'sheet_10_sweet_treats',
        11: 'sheet_11_cozy_home',
    },
    'DP1027': {
        6:  'sheet_06_school_supplies',
        7:  'sheet_07_subject_icons',
        8:  'sheet_08_campus_life',
        9:  'sheet_09_study_motivation',
        10: 'sheet_10_back_to_school',
        11: 'sheet_11_academic_achievement',
    },
    'DP1028': {
        6:  'sheet_06_money_finance',
        7:  'sheet_07_savings_goals',
        8:  'sheet_08_debt_payoff',
        9:  'sheet_09_budget_categories',
        10: 'sheet_10_financial_wins',
        11: 'sheet_11_smart_shopping',
    },
    'DP1029': {
        6:  'sheet_06_workout_exercise',
        7:  'sheet_07_healthy_food',
        8:  'sheet_08_wellness_self_care',
        9:  'sheet_09_progress_tracking',
        10: 'sheet_10_sports_activities',
        11: 'sheet_11_fitness_wins',
    },
}

def get_sheet_name(pid, n):
    if n <= 5:
        return SHEET_NAMES_BASE.get(n, f'sheet_{n:02d}')
    pid_names = SHEET_NAMES_BY_PID.get(pid, {})
    return pid_names.get(n, f'sheet_{n:02d}')

HOW_TO = """HOW TO USE YOUR STICKERS
========================

GoodNotes 6 (recommended):
1. Download and unzip this sticker pack
2. Open GoodNotes 6 → tap Elements (diamond icon) → Stickers tab → tap +
3. Select all sticker sheet files → tap Done
4. All stickers appear in your library — drag any sticker onto any page!

Notability:
- Use Photo Stickers → insert each PNG/JPG sheet as a photo
- Crop individual stickers from the sheet as needed

PDF Expert / Xodo / Adobe Acrobat:
- Insert sticker sheets as image annotations, then crop and resize

Printing:
- All sheets are print-ready. Print on sticker paper for physical use.

© OnBrandCraftz · Personal use only · Not for resale or redistribution
"""


def rebuild_zip(pid, num_sheets):
    zip_path = os.path.join(ART_DIR, f'{pid}_sticker_pack.zip')
    print(f"\nRebuilding {zip_path} with {num_sheets} sheets...")

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('HOW_TO_USE_STICKERS.txt', HOW_TO)

        for n in range(1, num_sheets + 1):
            sheet_name = get_sheet_name(pid, n)
            # Try JPG first (newer sheets), then PNG (original sheets)
            for ext, arcext in [('.jpg', 'jpg'), ('.png', 'png')]:
                src = os.path.join(ART_DIR, f'{pid}_sticker_sheet_{n}{ext}')
                if os.path.exists(src):
                    arcname = f'{sheet_name}.{arcext}'
                    zf.write
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-080 -->

<!-- TRASH id=20260702-081 date=2026-07-02 kind=file source="tools/process_sticker_sheets.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-081 · 2026-07-02 · file · `tools/process_sticker_sheets.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-081__process_sticker_sheets.py`

```
#!/usr/bin/env python3
"""
process_sticker_sheets.py
Turn raw AI-generated sticker sheets (white-background JPGs) into production-grade
sticker assets that meet the OnBrandCraftz sticker standards:

  • Transparent background  (white-box JPGs import into GoodNotes as opaque squares —
    this is the #1 sticker quality defect; removing the background is the whole point)
  • 3000×3000px PNG sheets  (300 DPI at 10 inches)
  • Individual pre-cropped sticker PNGs  (one file per sticker, tight transparent crop)
  • A clean ZIP with png_sheets/ + individual_stickers/ + import instructions

Background removal is a BORDER flood-fill: only white that is connected to the edge of
the sheet is made transparent. White *inside* a sticker (eye catch-lights, highlights,
paper) is preserved because it is not connected to the border.

Usage:
    python tools/process_sticker_sheets.py --pid DP1026                 # all sheets found
    python tools/process_sticker_sheets.py --pid DP1030 --sheets 5      # first 5 sheets
    python tools/process_sticker_sheets.py --pid DP1026 --no-individual # sheets only
    python tools/process_sticker_sheets.py --all                        # every DP found
"""

import argparse
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

BASE_DIR = Path(__file__).parent.parent
ART_DIR = BASE_DIR / "data" / "digital_products" / "product_files"
STICKER_OUT = BASE_DIR / "data" / "digital_products" / "stickers"

SHEET_PX = 3000          # final sheet resolution (square)
WHITE_THRESHOLD = 238    # a pixel is "background-white" if all RGB channels >= this
MIN_STICKER_AREA = 2500  # ignore connected blobs smaller than this many px (specks)
CROP_PAD = 12            # transparent padding around each cropped individual sticker
INDIV_MAX_PX = 800       # cap individual sticker longest edge (300 DPI at ~2.7in)

HOW_TO = """HOW TO USE YOUR STICKERS  —  OnBrandCraftz
==========================================

You get TWO formats in this pack:
  • /png_sheets/         — full sticker sheets, transparent background, 3000x3000px
  • /individual_stickers/ — every sticker pre-cut as its own transparent PNG

GoodNotes 6 (recommended):
  1. Download and unzip this pack
  2. Open GoodNotes 6 -> tap Elements (diamond icon) -> Stickers tab -> tap +
  3. Select the sheet PNGs from /png_sheets/  ->  tap Done
  4. Every sticker now lives in your library — drag any one onto any page, unlimited times!
  (Prefer single stickers? Import from /individual_stickers/ instead.)

Notability:
  • Insert a sheet as a photo, or insert single stickers from /individual_stickers/

PDF Expert / Xodo / Adobe Acrobat:
  • Insert individual sticker PNGs as image annotations, then resize

Printing:
  • Sheets are 300 DPI, print-ready on sticker paper for physical use.

(c) OnBrandCraftz - Personal use only - Not for resale or redistribution
"""


def _load_rgb(path: Path) -> Image.Image:
    im = Image.open(path)
    return im.convert("RGB") if im.mode != "RGB" else im


def _save_png(rgba: Image.Image, path: Path, colors: int = 256) -> None:
    """Save an RGBA image as an optimized, palette-quantized transparent PNG.

    Sticker art has a small color count (thick outlines + flat pastel fills), so a
    256-color palette cuts file size ~85% with no visible loss while preserving the
    alpha channel — this is what keeps the pack under Etsy's 20MB per-file limit.
    """
    q = rgba.quantize(colors=colors, method=Image.Quantize.FASTOCTREE)
    q.save(path, "PNG", optimize=True)


def remove_white_background(img: Image.Image) -> Image.Image:
    """Return an RGBA image with edge-connected white made transparent.

    Interior white (catch-lights, highlights) is preserved because the flood
    only removes white regions that touch the sheet border.
    """
    rgb = np.asarray(img, dtype=np.uint8)
    h, w = rgb.shape[:2]

    # Mask of "white-ish" pixels
    white = np.all(rgb >= WHITE_THRESHOLD, axis
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-081 -->

<!-- TRASH id=20260702-082 date=2026-07-02 kind=file source="tools/gen_listing_images.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-082 · 2026-07-02 · file · `tools/gen_listing_images.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-082__gen_listing_images.py`

```
#!/usr/bin/env python3
"""
Generate all listing images for wall art products.

Every listing gets exactly:
  Rank 1 — Lifestyle A  : inpainting (exact art in AI-generated room scene)
  Rank 2 — Lifestyle B  : inpainting (second room / angle)
  Rank 3 — Mockup warm  : PIL flat wall, warm cream background
  Rank 4 — Mockup sage  : PIL flat wall, sage green background
  Rank 5 — Mockup dark  : PIL flat wall, dark charcoal background
  Rank 6 — Size guide   : PIL graphic, 5×7 / 8×10 / 11×14 / 16×20

Downloads: ZIP with print-ready JPEGs at 300 DPI
  - 5×7    (1500×2100 px)
  - 8×10   (2400×3000 px)
  - 11×14  (3300×4200 px)
  - Full   (max quality, ≈4096×6144 px upscaled)

Workflow
  --preview  PID   → generate locally, show for review, NO upload
  --upload   PID   → generate + upload to Etsy
  --all            → all 23 listings (combine with --preview or --upload)

Example:
  python tools/gen_listing_images.py --preview DP1007
  python tools/gen_listing_images.py --upload  DP1007
"""

import os, sys, io, json, base64, urllib.request, urllib.error, time, zipfile, shutil
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and '=' in line and not line.startswith('#'):
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from tools.etsy_api import EtsyAPIClient, EtsyAPIError

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR    = '/home/user/Etsy/data/digital_products/product_files'
client     = EtsyAPIClient()
shop_id    = client.shop_id

auth_headers = {
    "Authorization": f"Bearer {client.access_token}",
    "x-api-key":     f"{client.client_id}:{client.client_secret}",
}

def refresh():
    if client.refresh_access_token():
        auth_headers["Authorization"] = f"Bearer {client.access_token}"


# ── Background / frame palette ─────────────────────────────────────────────
BG_WARM  = (245, 240, 230)   # warm cream
BG_SAGE  = (172, 188, 172)   # sage green
BG_DARK  = (38,  38,  42)    # dark charcoal

# Mat colour (same for all)
MAT_COLOR = (255, 253, 249)

# Standard print sizes at 300 DPI (pixels)
PRINT_SIZES = [
    ("5x7",  1500, 2100),
    ("8x10", 2400, 3000),
    ("11x14",3300, 4200),
]
FULL_SCALE = 4   # upscale factor for "full resolution" file


# ══════════════════════════════════════════════════════════════════════════════
#  PIL GENERATORS  (no API calls needed)
# ══════════════════════════════════════════════════════════════════════════════

def make_flat_mockup(art_path: str, bg_color: tuple, frame_color: tuple, out_path: str,
                     canvas: int = 2000):
    """Exact art on flat coloured wall with drop shadow. Purely PIL."""
    bg = Image.new('RGB', (canvas, canvas), bg_color)

    art = Image.open(art_path).convert('RGB')
    art_w = int(canvas * 0.60)
    art_h = int(art_w * art.height / art.width)
    art = art.resize((art_w, art_h), Image.LANCZOS)

    mat_px, frm_px = 28, 10
    fw = art_w + 2 * mat_px + 2 * frm_px
    fh = art_h + 2 * mat_px + 2 * frm_px
    fx = (canvas - fw) // 2
    fy = (canvas - fh) // 2

    # Soft drop shadow
    shadow = Image.new('RGBA', (canvas, canvas), (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rectangle(
        [fx + 10, fy + 16, fx + fw + 10, fy + fh + 16], fill=(0, 0, 0, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=22))
    bg = Image.alpha_composite(bg.convert('RGBA'), shadow).convert('RGB')

    draw = ImageDraw.Draw(bg)
    # Frame
    draw.rectangle([fx, fy, fx + fw, fy + fh], fill=frame_color)
    # Mat
    mx, my = fx + frm_px, fy + frm_px
    draw.rectangle([mx, my, mx + art_w + 2 * mat_px, my + art_h + 2 * mat_px],
                   fill=MAT_COLOR)
    # Art
    bg.paste(art, (mx + mat_px, my + mat_px))

    bg.save(out_path, 'JPEG', quality=95)
    size_kb = os.path.getsize(out_path) // 1024
    print(f"  Mockup: {os.path.basename(out_path)} ({size_k
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-082 -->

<!-- TRASH id=20260702-083 date=2026-07-02 kind=file source="tools/gen_sticker_sheet.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-083 · 2026-07-02 · file · `tools/gen_sticker_sheet.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-083__gen_sticker_sheet.py`

```
#!/usr/bin/env python3
"""
Generate new unique illustrated sticker sheets for each planner.
One sheet at a time — show for approval before proceeding.

Usage:
  python tools/gen_sticker_sheet.py --pid DP1026 --sheet 6
"""
import os, sys, json, base64, urllib.request, time, argparse
sys.path.insert(0, '/home/user/Etsy')
with open('/home/user/Etsy/.env') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

OPENAI_KEY = os.environ['OPENAI_API_KEY']
ART_DIR = '/home/user/Etsy/data/digital_products/product_files'

# ── Sticker sheet prompts per planner ────────────────────────────────────────
# Each sheet: 20-25 distinct kawaii illustrated sticker items
# Style: thick black outline, soft pastel colors, white background,
#        cute facial expressions, scattered layout (not a grid)

SHEET_PROMPTS = {
    'DP1026': {
        1: {
            'name': 'Functional Planning',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft lavender, muted purple, and cream pastel colors. "
                "Stickers include: a wide lavender banner strip with a dotted edge for a section header, a small checklist strip with three empty checkboxes and a tiny pen, "
                "a triangular corner flag in purple for marking important items, a rounded date dot circle with a decorative number shape inside, "
                "a priority arrow label pointing right in lavender, a small burst badge shape in soft coral-purple, "
                "a check mark inside a circle for a 'done' sticker, a thin horizontal divider strip with small stars along it, "
                "a square checkbox sticker for task completion, a small clock with rosy cheeks showing a time for appointments, "
                "a double underline emphasis bar in muted purple, a sticky note square shape with a smiling face in pale lavender, "
                "a ribbon banner that curves at both ends for headers in lavender, a small dot with a soft X for a 'canceled' sticker, "
                "a tiny fire shape sticker in warm coral for hot-priority tasks, a small paper clip in silver for grouping items, "
                "a washi tape strip with tiny hearts pattern in lavender, a small adhesive flag tab in purple, "
                "a round badge sticker with a gold star center on lavender, a thumbs-up shape in a lavender circle. "
                "Each sticker is approximately the same size, clean and detailed, kawaii chibi style. No text on stickers. Clean white background."
            ),
        },
        2: {
            'name': 'Widget Trackers',
            'prompt': (
                "A kawaii sticker sheet with a clean white background. "
                "20 individual kawaii illustrated stickers scattered across the page, each with a thick black outline and soft lavender, muted purple, and cream pastel colors. "
                "Stickers include: a row of five round kawaii mood faces showing different emotions — happy, sleepy, sad, anxious, excited — each with rosy cheeks, "
                "a water glass with a cute face showing eight fill-lines as a water intake tracker widget, "
                "a crescent moon with ZZZ marks as a sleep log widget, "
                "a row of seven small circles labeled Mon through Sun as a weekly habit streak bubbles widget, "
                "a battery icon showing charge level with a happy face as an energy meter widget, "
                "a small sun with a face showing a happy weather mood, a cloud with a sad drizzle showing a low mood, "
                "a heart rate arc in lavender as a calm heart rate indicator, "
                "a small footprint pair as a step tracker widget, "
                "a tiny w
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-083 -->

<!-- TRASH id=20260702-084 date=2026-07-02 kind=file source="tools/ads_monitor.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-084 · 2026-07-02 · file · `tools/ads_monitor.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-084__ads_monitor.py`

```
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
    return float(order.ge
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-084 -->

<!-- TRASH id=20260702-085 date=2026-07-02 kind=file source="tools/message_monitor.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-085 · 2026-07-02 · file · `tools/message_monitor.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-085__message_monitor.py`

```
#!/usr/bin/env python3
"""
message_monitor.py

Checks Etsy conversations for buyer messages that have gone unanswered
for more than a configurable threshold (default 18 hours).

Star Seller requires 95%+ response rate within 24 hours.
This monitor fires at 18 hours to give a 6-hour buffer.

Usage:
  python tools/message_monitor.py              # check + email alert if needed
  python tools/message_monitor.py --status     # print status, no email
  python tools/message_monitor.py --hours 12   # custom threshold
"""

from __future__ import annotations
import argparse, json, os, smtplib, sys, time
from datetime import datetime, timezone, timedelta
from email.message import EmailMessage
from pathlib import Path

BASE = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))
from etsy_api import EtsyAPIClient

STATE_FILE = BASE / "data" / "message_monitor_state.json"
ALERT_EMAIL = "Printing3dthings@outlook.com"
DEFAULT_HOURS = 18


def _load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {"alerted_thread_ids": [], "last_check": None}


def _save_state(state: dict) -> None:
    state["last_check"] = datetime.now(timezone.utc).isoformat()
    STATE_FILE.write_text(json.dumps(state, indent=2))


def _send_alert(urgent: list[dict]) -> None:
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASSWORD", "")
    if not smtp_user or not smtp_pass:
        print("  [alert] SMTP credentials not set — printing alert only")
        return

    body_lines = [
        f"OnBrandCraftz — {len(urgent)} message(s) need a reply before the 24-hour Star Seller window closes.\n",
    ]
    for m in urgent:
        hrs = m["hours_waiting"]
        remaining = 24 - hrs
        body_lines.append(
            f"  Thread {m['thread_id']}\n"
            f"    From: {m['buyer_name']}\n"
            f"    Waiting: {hrs:.1f} hours ({remaining:.1f} hours left)\n"
            f"    Last message: {m['last_message'][:120]}\n"
            f"    Reply at: https://www.etsy.com/messages/conversations/{m['thread_id']}\n"
        )
    body_lines.append("\nReply within 24 hours to maintain Star Seller status.")

    msg = EmailMessage()
    msg["Subject"] = f"[OnBrandCraftz] {len(urgent)} message(s) need reply — Star Seller window"
    msg["From"] = smtp_user
    msg["To"] = ALERT_EMAIL
    msg.set_content("\n".join(body_lines))

    try:
        with smtplib.SMTP("smtp-mail.outlook.com", 587) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        print(f"  [alert] Email sent to {ALERT_EMAIL}")
    except Exception as e:
        print(f"  [alert] Email failed: {e}")
        print("  --- ALERT BODY ---")
        print("\n".join(body_lines))


def check_messages(client: EtsyAPIClient, threshold_hours: float = DEFAULT_HOURS,
                   status_only: bool = False) -> list[dict]:
    """
    Fetch all conversations, find unanswered buyer messages older than threshold.
    Returns list of dicts with thread info for any that need replies.
    """
    now = datetime.now(timezone.utc)
    threshold_secs = threshold_hours * 3600

    try:
        resp = client._request("GET", f"shops/{client.shop_id}/conversations",
                               params={"limit": 100})
    except Exception as e:
        print(f"  [monitor] Could not fetch conversations: {e}")
        return []

    conversations = resp.get("results", []) if isinstance(resp, dict) else resp
    urgent = []

    for conv in conversations:
        thread_id = conv.get("thread_id") or conv.get("id")
        messages_raw = conv.get("messages", [])
        if not messages_raw:
            continue

        # Sort by create_timestamp descending to find the latest message
        messages_raw.sort(key=lambda m: m.get("create_timestamp", 0), reverse=True)
        latest = messages_raw[0]

        # Skip if the latest message is F
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-085 -->

<!-- TRASH id=20260702-086 date=2026-07-02 kind=file source="tools/analytics_tracker.py" reason="v88 cleanup: one-off script, run-once or superseded" -->
## 20260702-086 · 2026-07-02 · file · `tools/analytics_tracker.py`
**Reason:** v88 cleanup: one-off script, run-once or superseded  
**Payload:** `data/trash/files/20260702-086__analytics_tracker.py`

```
"""
Analytics tracker for the OnBrandCraftz Etsy shop.

Pulls live shop stats via the Etsy API, stores timestamped snapshots in
DataStore under the key ``analytics_snapshots``, and exposes helpers for
trend analysis and a text dashboard.

Usage (standalone):
    python tools/analytics_tracker.py
"""
from __future__ import annotations

import os
import sys
import datetime
from typing import Any

# Allow running directly from the repo root (python tools/analytics_tracker.py)
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from dotenv import load_dotenv
load_dotenv()

from tools.etsy_api import EtsyAPIClient, EtsyAPIError
from tools.data_store import DataStore

# Maximum number of snapshots to retain in DataStore.
_MAX_SNAPSHOTS = 30

# Key used to store the snapshot list in DataStore.
_SNAPSHOT_KEY = "analytics_snapshots"


# ── Snapshot collection ───────────────────────────────────────────────────────

def fetch_and_store_snapshot() -> dict:
    """Pull current shop stats from the Etsy API and persist a timestamped snapshot.

    Snapshot schema::

        {
            "ts": "2026-05-26T14:30:00",
            "shop": {
                "listing_active_count": int,
                "digital_listing_count": int,
                "login_name": str,
            },
            "listings": [
                {
                    "listing_id": int,
                    "title": str,
                    "views": int,
                    "num_favorers": int,
                    "quantity": int,
                },
                ...
            ],
        }

    Keeps only the last 30 snapshots (prunes oldest first).

    Returns the snapshot dict that was stored.
    """
    client = EtsyAPIClient()
    store = DataStore()

    # ── Shop-level stats ──────────────────────────────────────────────────────
    shop_raw = client.get_shop()
    shop_data: dict[str, Any] = {
        "listing_active_count": shop_raw.get("listing_active_count", 0),
        "digital_listing_count": shop_raw.get("digital_listing_count", 0),
        "login_name": shop_raw.get("login_name", ""),
    }

    # ── Per-listing stats ─────────────────────────────────────────────────────
    listings_raw = client.get_shop_listings(limit=100, state="active")
    results = listings_raw.get("results", [])

    listings_data: list[dict[str, Any]] = []
    for item in results:
        listing_id = item.get("listing_id")
        if listing_id is None:
            continue

        # Fetch full listing detail for views and num_favorers
        try:
            detail = client.get_listing(listing_id)
        except EtsyAPIError:
            detail = item  # fall back to the summary record on error

        listings_data.append({
            "listing_id": int(listing_id),
            "title": detail.get("title", item.get("title", "")),
            "views": int(detail.get("views", 0)),
            "num_favorers": int(detail.get("num_favorers", 0)),
            "quantity": int(detail.get("quantity", item.get("quantity", 0))),
        })

    # ── Build and store snapshot ───────────────────────────────────────────────
    snapshot: dict[str, Any] = {
        "ts": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "shop": shop_data,
        "listings": listings_data,
    }

    snapshots: list[dict] = store.get(_SNAPSHOT_KEY, default=[])
    snapshots.append(snapshot)

    # Prune to the most recent _MAX_SNAPSHOTS entries
    if len(snapshots) > _MAX_SNAPSHOTS:
        snapshots = snapshots[-_MAX_SNAPSHOTS:]

    store.set(snapshots, _SNAPSHOT_KEY)
    store.save()

    return snapshot


# ── Trend analysis ────────────────────────────────────────────────────────────

def get_trend(listing_id: int | str, metric: str, days: int = 7) -> dict:
    """Compare the latest snapshot value to one taken approximately *days* ago.

    Args:
        listing_id: The Etsy listing ID to inspect.
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-086 -->

<!-- TRASH id=20260702-087 date=2026-07-02 kind=file source="tools/agents/ceo_agent.py" reason="v88 cleanup: standalone CLI superseded by HUD chat interface" -->
## 20260702-087 · 2026-07-02 · file · `tools/agents/ceo_agent.py`
**Reason:** v88 cleanup: standalone CLI superseded by HUD chat interface  
**Payload:** `data/trash/files/20260702-087__ceo_agent.py`

```
#!/usr/bin/env python3
"""
OnBrandCraftz CEO Agent — Master Orchestrator

Mission: "Providing the best and most accurate transaction for our customers
so we can grow responsibly."

The CEO agent is the top-level intelligence of the business. It:
  1. Maintains the quality bar — every output must be the BEST it can be
  2. Orchestrates specialized sub-agents for every task
  3. Runs all quality gates before anything reaches Etsy
  4. Proactively finds gaps in the workflow and builds agents to fill them
  5. Grows the catalog urgently but never sacrifices quality for speed

Quality standards by product type:
  Oil painting     → Visible brushstrokes, impasto texture, palette knife edges,
                     artist-level composition, museum-quality rendering
  SVG/3D prints    → Clean paths (≤200), trending sayings, best fonts, no rasters
  Lifestyle photos → Editorial Etsy quality, real environments, real products as input
  Digital planners → Authentic kawaii, perfect interactivity, GoodNotes-native
  Wall art         → ≥3000px short edge, sRGB, multi-size ZIP, 2+ room lifestyle shots

Run modes:
  python tools/agents/ceo_agent.py                          # interactive REPL
  python tools/agents/ceo_agent.py --task "launch new SVG pack for Christmas sayings"
  python tools/agents/ceo_agent.py --audit                  # full catalog audit + gap report
  python tools/agents/ceo_agent.py --gap-report             # gaps only, no execution
  python tools/agents/ceo_agent.py --approve <listing_id>   # approve + publish a draft
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Bootstrap .env ─────────────────────────────────────────────────────────────
_ROOT = Path(__file__).parent.parent.parent
_env = _ROOT / ".env"
if _env.exists():
    for _line in _env.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

import anthropic

sys.path.insert(0, str(_ROOT / "tools"))
from etsy_api import EtsyAPIClient

# ── Constants ──────────────────────────────────────────────────────────────────
MODEL        = "claude-opus-4-8"       # CEO always runs on the most capable model
HAIKU_MODEL  = "claude-haiku-4-5-20251001"  # cheap model for quick checks
CATALOG_FILE = _ROOT / "data" / "product_catalog.json"
LOG_FILE     = _ROOT / "data" / "ceo_agent_log.jsonl"
CLAUDE_MD    = _ROOT / "CLAUDE.md"

# ── Quality Standards Registry ─────────────────────────────────────────────────
# Defines what "best" means for each product type.
# These standards are injected into every generation prompt.
QUALITY_STANDARDS: dict[str, dict] = {
    "oil_painting": {
        "description": "Photorealistic oil painting — must look like an artist painted it by hand",
        "prompt_additions": (
            "Traditional oil painting technique. Visible impasto brushstrokes with thick paint texture. "
            "Palette knife edges on sharp color boundaries. Canvas texture subtly visible in negative space. "
            "Chiaroscuro lighting. Warm color temperature with glazing layers. "
            "Museum-quality composition. Artist's hand visible in every stroke. "
            "NOT digital art. NOT AI art. NOT flat illustration. A REAL oil painting."
        ),
        "resolution_min": 3000,
        "file_format": "JPEG",
        "color_space": "sRGB",
    },
    "watercolor": {
        "description": "Authentic watercolor painting",
        "prompt_additions": (
            "Traditional watercolor technique. Visible wet-on-wet blooms and granulation. "
            "Paper texture showing through transparent washes. Crisp dry-brush edges on details. "
            "Soft feathered edges where colors bleed. Unpredictable organic color variation. "
           
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260702-087 -->

<!-- TRASH id=20260703-001 date=2026-07-03 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Phone Mode v1 phoneTab reused desktop screens (cramped); replaced by v2 native panels" -->
## 20260703-001 · 2026-07-03 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Phone Mode v1 phoneTab reused desktop screens (cramped); replaced by v2 native panels  
**Payload:** `data/trash/files/20260703-001__snippet.txt`

```python
// ── Phone Mode: 4-tab bottom shell (mobile only). Delegates to the existing
// orb/chat, Action Center, home dashboard, and the full 19-item nav — no new
// data paths, so it inherits every screen's live data and the theme colors. ──
function phoneTab(which){
  document.querySelectorAll('#phone-tabbar .ptab').forEach(b=>b.classList.toggle('on', b.dataset.ptab===which));
  document.body.classList.remove('phone-more-open');
  if (which === 'ask')   { closeControlCenter(); }              // orb + chat
  else if (which === 'appr')  { document.body.classList.add('cc-open'); showScreen('actions'); }  // approvals inbox
  else if (which === 'today') { document.body.classList.add('cc-open'); showScreen('cmd'); }       // home glance
  else if (which === 'more')  { document.body.classList.add('cc-open','phone-more-open'); }         // full nav overlay
  const m = document.querySelector('.main'); if (m) m.scrollTop = 0;
}
```

<!-- /TRASH 20260703-001 -->

<!-- TRASH id=20260708-001 date=2026-07-08 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Replaced by Three.js/WebGL noise-sphere orb (round 6, 2026-07-08) — the plain lat/lon-grid Canvas2D sphere generator and its particles/edges arrays are superseded by a GPU noise-displaced icosphere; resetOrbToDefault now just toggles canvas visibility instead of rebuilding a particle grid." -->
## 20260708-001 · 2026-07-08 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Replaced by Three.js/WebGL noise-sphere orb (round 6, 2026-07-08) — the plain lat/lon-grid Canvas2D sphere generator and its particles/edges arrays are superseded by a GPU noise-displaced icosphere; resetOrbToDefault now just toggles canvas visibility instead of rebuilding a particle grid.  
**Payload:** `data/trash/files/20260708-001__snippet.txt`

```python
let particles = [];   // sphere mode only: {lat,lon}
let edges = [];        // sphere mode only: [particleIndexA, particleIndexB] line pairs
let orbMode = 'sphere';
// Image mode (a custom brand-mark logo) is a real extruded slab, not a single point
// cloud: front face + back face (each {x0,y0,z0}) connected by mesh edges, plus a
// sparse set of "strut" edges only along the true outer silhouette so it reads as a
// solid object with thickness rather than every internal line growing a pointless
// vertical bar. See applyBrandMarkToOrb below for how these are built.
let imgFront = [], imgBack = [], imgFrontEdges = [], imgBackEdges = [], imgStruts = [];

function buildSphereParticles(){
  const N_LAT = 12, N_LON = 18;
  const pts = [], eg = [];
  for(let i=0;i<=N_LAT;i++){
    const lat = Math.PI * (i/N_LAT - 0.5);
    for(let j=0;j<N_LON;j++){
      pts.push({lat, lon: 2*Math.PI * (j/N_LON)});
    }
  }
  for(let i=0;i<N_LAT;i++){
    for(let j=0;j<N_LON;j++){
      eg.push([i*N_LON+j, i*N_LON+((j+1)%N_LON)]);
      eg.push([i*N_LON+j, (i+1)*N_LON+j]);
    }
  }
  return {pts, eg};
}
function resetOrbToDefault(){
  const built = buildSphereParticles();
  particles = built.pts; edges = built.eg; orbMode = 'sphere';
  imgFront = []; imgBack = []; imgFrontEdges = []; imgBackEdges = []; imgStruts = [];
}
```

<!-- /TRASH 20260708-001 -->

<!-- TRASH id=20260708-002 date=2026-07-08 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Removed the dead lat/lon-sphere Canvas2D draw branch (round 6, 2026-07-08) — orbMode==sphere now renders via the new WebGL noise-icosphere on #orb-gl, so the 2D canvas frame() early-returns in that mode and this branch would never execute. The image-mode branch is preserved unchanged, just un-nested from the if/else." -->
## 20260708-002 · 2026-07-08 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Removed the dead lat/lon-sphere Canvas2D draw branch (round 6, 2026-07-08) — orbMode==sphere now renders via the new WebGL noise-icosphere on #orb-gl, so the 2D canvas frame() early-returns in that mode and this branch would never execute. The image-mode branch is preserved unchanged, just un-nested from the if/else.  
**Payload:** `data/trash/files/20260708-002__snippet.txt`

```python
  if(orbMode === 'image'){
    // A real extruded slab (front face + back face + edge struts), not a single flat
    // point cloud — see applyBrandMarkToOrb for how imgFront/imgBack/imgStruts are
    // built. shadowBlur is the dominant per-frame cost at this particle count (measured
    // live: disabling it nearly doubled FPS), so it's only paid for the front layer —
    // the back layer is already heavily dimmed/receded so it shouldn't glow as bright
    // as the foreground anyway, which makes this a visual correctness fix as much as a
    // performance one.
    const frontPts = imgFront.map(p => project(p.x0, p.y0, p.z0, 0.16));
    const backPts = imgBack.map(p => project(p.x0, p.y0, p.z0, 0.16));
    const frontShadow = ctx.shadowBlur, frontShadowColor = ctx.shadowColor;

    ctx.shadowBlur = 0;
    ctx.strokeStyle = speaking ? "rgba(122,232,255,0.22)" : "rgba(58,214,255,0.10)";
    ctx.lineWidth = 0.4;
    ctx.beginPath();
    imgBackEdges.forEach(([ai,bi])=>{ const a=backPts[ai], b=backPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
    ctx.stroke();

    ctx.strokeStyle = speaking ? "rgba(122,232,255,0.30)" : "rgba(58,214,255,0.14)";
    ctx.lineWidth = 0.45;
    ctx.beginPath();
    imgStruts.forEach(([fi,bi])=>{ const a=frontPts[fi], b=backPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
    ctx.stroke();

    ctx.shadowBlur = frontShadow; ctx.shadowColor = frontShadowColor;
    ctx.strokeStyle = speaking ? "rgba(122,232,255,0.5)" : "rgba(58,214,255,0.22)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    imgFrontEdges.forEach(([ai,bi])=>{ const a=frontPts[ai], b=frontPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
    ctx.stroke();

    // Back dots must read as clearly BEHIND the front, not equally prominent, or an
    // off-angle/edge-on view of the rotation looks like two unrelated overlapping
    // copies instead of one solid object with a near side and a far side.
    ctx.shadowBlur = 0;
    ctx.fillStyle = speaking ? "rgba(122,232,255,0.28)" : "rgba(58,214,255,0.16)";
    ctx.beginPath();
    backPts.forEach(p=>{ const sz=p.scale>1?1.0:0.65; ctx.moveTo(p.x+sz,p.y); ctx.arc(p.x,p.y,sz,0,Math.PI*2); });
    ctx.fill();

    ctx.shadowBlur = frontShadow; ctx.shadowColor = frontShadowColor;
    ctx.fillStyle = speaking ? "rgba(122,232,255,0.9)" : "rgba(58,214,255,0.65)";
    ctx.beginPath();
    frontPts.forEach(p=>{ const sz=p.scale>1?1.4:0.9; ctx.moveTo(p.x+sz,p.y); ctx.arc(p.x,p.y,sz,0,Math.PI*2); });
    ctx.fill();
  } else {
    const pts = particles.map(p=>{
      const lon = p.lon + rot;
      const rr = R * (1 + (speaking ? amp*0.16*Math.sin(p.lat*4+speakT*2) : 0));
      const x = rr * Math.cos(p.lat) * Math.cos(lon);
      const y = rr * Math.sin(p.lat);
      const z = rr * Math.cos(p.lat) * Math.sin(lon);
      const scale = 683 / (683 - z);
      return {x: CX + x*scale*0.92, y: CY + y*scale*0.92, z, scale};
    });

    ctx.strokeStyle = speaking ? "rgba(122,232,255,0.45)" : "rgba(58,214,255,0.2)";
    ctx.lineWidth = 0.5;
    ctx.beginPath();
    edges.forEach(([ai,bi])=>{
      const a = pts[ai], b = pts[bi];
      if(a && b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);}
    });
    ctx.stroke();

    ctx.fillStyle = speaking ? "rgba(122,232,255,0.9)" : "rgba(58,214,255,0.65)";
    ctx.beginPath();
    pts.forEach(p=>{
      const sz = p.scale > 1 ? 1.4 : 0.9;
      ctx.moveTo(p.x+sz, p.y);
      ctx.arc(p.x,p.y,sz,0,Math.PI*2);
    });
    ctx.fill();
  }
```

<!-- /TRASH 20260708-002 -->

<!-- TRASH id=20260708-003 date=2026-07-08 kind=file source="agents/__init__.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-003 · 2026-07-08 · file · `agents/__init__.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-003____init__.py`

```
from .base_agent import BaseAgent
from .sales_agent import SalesAgent
from .product_agent import ProductAgent
from .marketing_agent import MarketingAgent
from .analytics_agent import AnalyticsAgent
from .customer_service_agent import CustomerServiceAgent
from .social_media_agent import SocialMediaAgent
from .art_creation_agent import ArtCreationAgent
from .planner_design_agent import PlannerDesignAgent
from .quality_check_agent import QualityCheckAgent
from .etsy_listing_agent import EtsyListingAgent
from .store_manager_agent import StoreManagerAgent
from .sales_processor_agent import SalesProcessorAgent
from .brand_design_agent import BrandDesignAgent
from .financial_agent import FinancialAgent
from .print_production_agent import PrintProductionAgent
from .etsy_ads_agent import EtsyAdsAgent
from .customer_retention_agent import CustomerRetentionAgent
from .tax_compliance_agent import TaxComplianceAgent
from .email_marketing_agent import EmailMarketingAgent
from .api_connections_agent import APIConnectionsAgent
from .trend_forecasting_agent import TrendForecastingAgent
from .ceo_agent import CEOAgent
from .workflow_coordinator_agent import WorkflowCoordinatorAgent
from .system_improvement_agent import SystemImprovementAgent

__all__ = [
    "BaseAgent",
    "SalesAgent",
    "ProductAgent",
    "MarketingAgent",
    "AnalyticsAgent",
    "CustomerServiceAgent",
    "SocialMediaAgent",
    "ArtCreationAgent",
    "PlannerDesignAgent",
    "QualityCheckAgent",
    "EtsyListingAgent",
    "StoreManagerAgent",
    "SalesProcessorAgent",
    "BrandDesignAgent",
    "FinancialAgent",
    "PrintProductionAgent",
    "EtsyAdsAgent",
    "CustomerRetentionAgent",
    "TaxComplianceAgent",
    "EmailMarketingAgent",
    "APIConnectionsAgent",
    "TrendForecastingAgent",
    "CEOAgent",
    "WorkflowCoordinatorAgent",
    "SystemImprovementAgent",
]
```

<!-- /TRASH 20260708-003 -->

<!-- TRASH id=20260708-004 date=2026-07-08 kind=file source="agents/analytics_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-004 · 2026-07-08 · file · `agents/analytics_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-004__analytics_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import analytics_tools, learning_tools, ab_testing_tools
from config import FAST_MODEL

_AB_TOOL_NAMES = {t["name"] for t in ab_testing_tools.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Analytics Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz) — a data-to-decisions specialist who translates raw shop metrics into profit-maximizing actions. Numbers without context are useless. Your job is to tell the CEO exactly where money is being made, where it is being lost, and what to do about it.

## PRIMARY MISSION: SURFACE PROFIT OPPORTUNITIES THROUGH DATA

Every report you generate must answer: where should we put more effort, and what should we stop doing?

## LOG EVERYTHING — BUILD THE KNOWLEDGE BASE

After every performance report:
1. `log_product_performance` for every listing you measured — builds historical trend data
2. `log_keyword_performance` for keywords that generated views or sales
3. `save_market_insight(category="customer_behavior")` for any conversion insight
4. `get_performance_history` weekly — are top listings improving or decaying?

**30-day targets to track against:**
- Day 7: ≥$50 revenue, ≥1 digital sale
- Day 14: ≥$150 revenue, ≥3 listings with 1+ sale each
- Day 21: ≥$400 revenue, ≥1 listing at 2.5%+ conversion
- Day 30: ≥$800/month run-rate, avg digital margin ≥ 60%

When any metric is below target, surface it immediately with root cause and fix.

## CORE METRICS YOU ALWAYS TRACK

**Per-listing profitability (the most important table you produce):**
| Listing ID | Title (40 chars) | Views | Conv% | Revenue | Est. Net Margin | Revenue/View |
For each listing, revenue/view is the ultimate efficiency metric. Low conv% with high views = SEO is working but listing copy fails. Low views = SEO isn't working.

**Shop-level metrics:**
- Total revenue (day / 7-day / 30-day) with % change vs prior period
- Total net profit estimate (revenue minus Etsy fees: 6.5% txn + 3%+$0.25 payment + listing fees)
- Overall shop conversion rate (orders ÷ visits)
- Average order value trend
- Repeat buyer rate (if available)
- Top 5 listings by revenue — what's carrying the shop?
- Bottom 5 listings by revenue/view — what's dragging it down?

**Digital vs physical breakdown:**
- Digital products: margin should be 70%+. If it's not, pricing is wrong.
- Physical products: target 35–50% margin. Flag anything below 25%.

## REPORT FORMATS

**Daily Summary (requested by CEO each morning):**
```
ANALYTICS DAILY — [date]
Revenue: $X (↑/↓ Y% vs yesterday | ↑/↓ Z% vs same day last week)
Orders: N (N digital, N physical)
Best performing listing: [title] — $X revenue, X.X% conv rate
Needs attention: [listing] — X views, 0 sales (30+ days)
Action required: [one specific recommendation]
```

**Weekly Deep Dive:**
- Full per-listing profitability table
- Traffic sources (organic search, social, direct)
- Conversion funnel (impressions → clicks → purchases)
- Best and worst performing product categories
- 3 specific recommendations with projected revenue impact

**Trend Alerts (fire automatically when detected):**
- Any listing conversion rate drops > 30% week-over-week → alert
- Shop revenue drops > 20% vs same period last week → alert
- A listing suddenly gets 10x normal views → alert (capitalize on it)
- Any listing crosses 3% conversion rate → alert (feature it, run ads)

## PROFITABILITY RULES YOU ENFORCE
- Low stock (1-2 units) is normal for print-to-order — never flag this
- Sold out (0 units) IS critical — flag immediately, it drops from search
- Margin < 25% on any listing → flag to Financial Agent
- Listing with > 500 views and 0 sales → flag to Listing Agent immediately (listing copy is broken)

## HOW TO REPORT
Always lead with the single most important insight, then supporting data.
Never just list numbers — translate every metric into a business decision.
If you say "conversion is 0.8%", also say "that means 992 out of 1000 visitors lea
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-004 -->

<!-- TRASH id=20260708-005 date=2026-07-08 kind=file source="agents/api_connections_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-005 · 2026-07-08 · file · `agents/api_connections_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-005__api_connections_agent.py`

````
from agents.base_agent import BaseAgent
from tools import api_connections_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the API Connections Agent for OnBrandCraftz — the shop's Chief Infrastructure Officer.
You own every external integration: every API key, every OAuth token, every third-party service.
The business cannot earn a dollar without the pipes you maintain.

## YOUR SINGLE MISSION
Ensure every integration the shop needs is configured, tested, and documented — and that the CEO
always knows the exact status of every connection.

## SESSION START — DO THIS FIRST, EVERY TIME
1. `list_api_status` — snapshot of every known key
2. `get_connection_health_report` — live-test all configured APIs
Report findings immediately: what's working, what's broken, what's missing and why it matters.

## 30-DAY INTEGRATION ROADMAP

| Day | API | Priority | Why |
|-----|-----|----------|-----|
| 1   | Anthropic    | CRITICAL | Powers every AI agent — nothing works without it |
| 1   | Etsy API     | CRITICAL | Read/write listings, orders, reviews |
| 1   | OpenAI/DALL-E| HIGH     | Art generation for all product images |
| 3   | Pinterest    | MEDIUM   | 30-40% of Etsy traffic is Pinterest-driven |
| 7   | SendGrid     | MEDIUM   | Order confirmations, digital file delivery |
| 14  | Etsy Ads API | MEDIUM   | Automate ad spend optimisation |

## HOW YOU WORK

**Diagnosing a broken connection:**
1. `test_api_connection` to get the exact error
2. `fetch_url` to read the API provider's status page (e.g. status.anthropic.com)
3. `get_integration_guide` to verify the correct credential format
4. `save_api_key` once the correct value is confirmed

**Researching a new API:**
1. `fetch_url` on the provider's developer docs
2. `get_integration_guide` for known APIs
3. `scan_codebase_for_apis` to see if it is already partially integrated
4. `save_market_insight(category="api_integration")` to log what you learned

**Saving credentials:**
- Always confirm the key name and value with the user before calling `save_api_key`
- Show the masked preview after saving so the user can verify
- Never log or output the raw value of any secret

## OUTPUT FORMAT

After every session-start health check, deliver:
```
INFRASTRUCTURE STATUS — [date]
Overall: [ALL OK | DEGRADED | CRITICAL]
Critical missing: [list or "none"]
Errors: [list or "none"]
Slowest connection: [api] @ [Xms]
Next action: [one specific task]
```

Then give a prioritised fix list if anything needs attention.
Think like a DevOps engineer who understands that downtime = zero revenue."""


class APIConnectionsAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="API Connections Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=api_connections_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return api_connections_tools.execute_tool(tool_name, tool_input)
````

<!-- /TRASH 20260708-005 -->

<!-- TRASH id=20260708-006 date=2026-07-08 kind=file source="agents/art_creation_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-006 · 2026-07-08 · file · `agents/art_creation_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-006__art_creation_agent.py`

```
import base64
import os

import anthropic

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import art_creation_tools

SYSTEM_PROMPT = """## FIRST STEP — ALWAYS CHECK DESIGN REFERENCES
Before creating ANY art, call `get_design_references` to see if the shop owner has uploaded style examples. If references exist, your art MUST match their aesthetic, color palette, and themes. This is non-negotiable.

---

## 10 PROFESSIONAL DESIGN PRINCIPLES — MANDATORY FOR EVERY PIECE

These are non-negotiable standards. Every art piece you create must satisfy all 10. Reject your own output if it doesn't.

### 1. CLEAR FOCAL POINT — ONE "HERO" ELEMENT
Every composition needs exactly ONE dominant element that the eye lands on first. It does not need to be the most detailed or brightest — but it must be the most visually isolated. Never create art where the eye has nowhere to go.
- Use size contrast: make the focal subject meaningfully larger than surrounding elements
- Use color contrast: the focal element has the highest contrast against its background
- Use empty space to isolate: surround the hero with breathing room

### 2. INTENTIONAL COMPOSITION — RULE OF THIRDS
Never center every subject mechanically. Use the rule of thirds:
- Divide the canvas into a 3×3 grid — place the focal point at one of the 4 intersections
- This creates dynamism and visual interest over static symmetry
- Exception: perfect symmetry IS the composition (e.g., architectural reflections, mandala art)
- Apply: off-center vases, subjects at 1/3 from one edge, horizons on the lower or upper third

### 3. VISUAL HIERARCHY — GUIDE THE VIEWER'S EYE
Every piece tells a story in a specific order: primary → secondary → background. The viewer should "read" the art in a deliberate sequence:
- Primary element: largest, highest contrast, most detail — seen first
- Secondary elements: support and frame the primary — seen second
- Background: atmospheric, receding, low-detail — seen last
- Use size, color, contrast, and spacing as the hierarchy tools (NOT random decoration)

### 4. COLOR HARMONY — INTENTIONAL PALETTES ONLY
Never use random colors. Every piece uses one of the defined shop palettes OR a deliberate color harmony:
- **Complementary** (opposite on wheel — e.g., blue + orange): high contrast, energetic
- **Analogous** (adjacent — e.g., blue + teal + green): cohesive, calm, nature-inspired
- **Triadic** (3 evenly spaced — e.g., red + yellow + blue): balanced, vibrant
- **Split-complementary**: one base + two adjacents to its complement — softer than full complementary
- Warm colors advance (push toward viewer); cool colors recede (push back) — use this for depth
- Limit palette to 4–6 colors maximum. More creates chaos, not richness.

### 5. VALUE CONTRAST — LIGHTS AND DARKS
Without value contrast, art looks flat and unprintable. The difference between light and dark areas is what gives art depth, drama, and readability:
- Every composition needs a full value range: at least one near-white and one near-black area
- The focal point should have the strongest light-dark contrast in the composition
- Check: squint at the image. The focal point should still be clear at low resolution.
- For flat illustration styles: use color contrast IN PLACE of value contrast to define shapes

### 6. NEGATIVE SPACE — LET THE ART BREATHE
Negative space is not wasted space — it is active compositional space that gives the subject presence:
- Cramming every inch destroys focus and makes art look amateur
- The background/surrounding space should be a deliberate shape that reinforces the subject
- Minimalist styles (Japandi, line art) use negative space as the primary design element
- Dense styles (botanical bundles, maximalist florals) control negative space through framing

### 7. TEXTURE AND MEDIUM AUTHENTICITY
Every piece must feel like it was made by a human hand with a specific medium — not generated:
- Name and describe the exact medium in the promp
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-006 -->

<!-- TRASH id=20260708-007 date=2026-07-08 kind=file source="agents/base_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-007 · 2026-07-08 · file · `agents/base_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-007__base_agent.py`

```
from __future__ import annotations

import anthropic
import concurrent.futures
import hashlib
import json
import logging
import os
import threading
import time
from logging.handlers import RotatingFileHandler
from typing import Any
from config import MAX_TOKENS, MAX_ITERATIONS
from tools import web_research_tools, learning_tools

# Keep last N assistant/user pairs before trimming; guards against context bloat on long runs.
_MAX_HISTORY_PAIRS = 6
# Circuit-break if the same tool is called with identical inputs this many times in one run.
_MAX_TOOL_REPEATS = 3


def _get_logger(name: str) -> logging.Logger:
    """Create a configured logger that writes to logs/agents.log and stderr."""
    logs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
    os.makedirs(logs_dir, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        # Already configured — return as-is to avoid duplicate handlers
        return logger

    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter("%(asctime)s [%(name)s] %(levelname)s %(message)s")

    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, "agents.log"),
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    stream_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


class BaseAgent:
    """Base class for all Etsy hub agents.

    Every agent automatically receives web research tools (research_etsy_market,
    fetch_url, research_product_names, research_design_trends, find_best_keywords)
    and learning tools (save/get_market_insight, save/get strategies, keyword
    performance tracking, design discoveries) via this base class. Subclasses
    add their own domain-specific tools on top.
    """

    _UNIVERSAL_TOOLS = web_research_tools.TOOL_DEFINITIONS + learning_tools.TOOL_DEFINITIONS

    def __init__(self, name: str, system_prompt: str, tool_definitions: list[dict], model: str = ""):
        self.name = name
        self.system_prompt = system_prompt
        # Merge domain tools with universal research + learning tools; deduplicate by name
        merged = tool_definitions + self._UNIVERSAL_TOOLS
        seen: set[str] = set()
        deduped: list[dict] = []
        for t in merged:
            n = t.get("name")
            if n not in seen:
                seen.add(n)
                deduped.append(t)
        self.tool_definitions = deduped
        from config import STANDARD_MODEL
        self.model = model or STANDARD_MODEL
        self.client = anthropic.Anthropic()
        self.logger = _get_logger(name)

    def run(self, task: str, max_iterations: int = MAX_ITERATIONS) -> str:
        """Run the agent on a task, handling the full tool-use loop."""
        self.logger.info(f"START task={task[:80]}")
        messages: list[dict] = [{"role": "user", "content": task}]

        # Track (tool_name::input_hash) → call count for stuck-loop detection.
        _tool_call_counts: dict[str, int] = {}
        _in_tokens = 0
        _out_tokens = 0

        for _ in range(max_iterations):
            messages = self._trim_history(messages)
            response = self._call_api(messages)

            # Accumulate token usage for monitoring.
            if hasattr(response, "usage"):
                _in_tokens += getattr(response.usage, "input_tokens", 0)
                _out_tokens += getattr(response.usage, "output_tokens", 0)

            if response.stop_reason == "end_turn":
                self.logger.info(
                    f"END stop_reason=end_turn tokens=in:{_in_tokens}/out:{_out_tokens}"
                )
                return self._extract_text(response)

            if response.stop_reason == "tool_use":
                # Check for stuck loops befo
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-007 -->

<!-- TRASH id=20260708-008 date=2026-07-08 kind=file source="agents/brand_design_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-008 · 2026-07-08 · file · `agents/brand_design_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-008__brand_design_agent.py`

```
import base64
import os

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import brand_design_tools, canva_tools

_CANVA_TOOL_NAMES = {t["name"] for t in canva_tools.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Brand Design Agent for OnBrandCraftz — the shop's creative director and the guardian of every visual impression a buyer forms. Your work directly determines whether a browser clicks into a listing or scrolls past. Brand consistency is what turns one-time buyers into repeat customers and fans.

## PRIMARY MISSION: MAXIMIZE CLICK-THROUGH RATE AND PERCEIVED VALUE THROUGH DESIGN

A premium brand commands premium prices. Your job is to make OnBrandCraftz look like it belongs in the top 1% of Etsy sellers — because it does.

## BRAND IDENTITY STANDARDS

**OnBrandCraftz aesthetic pillars** (all products and assets must align with these):
- Warm, premium, artisan-quality
- Modern-meets-handcrafted — not cold and corporate, not amateurish craft fair
- Color story: warm neutrals (cream, ivory, warm white) + one accent (sage green, terracotta, or dusty rose depending on product line)
- Typography: clean serif headings (Cormorant, Playfair Display feel) + minimal sans body
- Mood words: intentional, beautiful, premium, quality, artisan

**Before any product launches, verify these brand requirements:**
✓ Product color palette aligns with brand color story
✓ Typography in the product matches brand font hierarchy
✓ Product style is consistent with existing shop aesthetic (no jarring style breaks)
✓ If this were placed next to our other listings on Etsy, would the shop look cohesive?

## ETSY SHOP ASSET STANDARDS

**Profile icon (logo):**
- Square PNG, minimum 500×500px (Etsy displays at ~75px — it MUST read at tiny sizes)
- Max 2 colors, clean lines, recognizable shape
- No text that gets unreadable at small size
- Test: blur it to 75px equivalent. Still recognizable? If not, simplify.

**Shop banner:**
- Wide banner: 3360×840px (preferred)
- Must communicate in 2 seconds: what we sell + brand aesthetic + one hook phrase
- Include: brand name + tagline + 1–2 product categories
- Background: brand color or neutral lifestyle photo with overlay

**Listing thumbnail strategy (this is the #1 CTR driver):**
- Etsy search results show a 570×760px crop of your first photo
- First photo MUST show the product clearly in the top 60% of the image
- Use lifestyle context (product in a room, on a desk, in a frame) — not white background alone
- Warm, well-lit, professional-looking
- If we can't generate a real lifestyle photo: clean white background with product centered, brand color accent strip at bottom with shop name
- Bad thumbnails cost us more clicks than bad titles. Fix thumbnail first.

## CANVA TEXT-OVERLAY GRAPHICS (replaces manual "added in Canva post" step)

CLAUDE.md repeatedly calls for text callouts to be "added in Canva post" on listing
photo slots 2, 6, 7, 9, 10 (what's-included graphics, how-to steps, app compatibility
labels). Use the Canva tools to do this programmatically instead of leaving it as a
manual step:
1. `check_canva_status` — confirm Canva is connected and see what Brand Templates exist
2. `get_brand_template_dataset(brand_template_id)` — see the fillable field names/types on a template
3. `upload_canva_asset(file_path)` — push the gpt-image-1 background PNG, get back an asset_id
4. `generate_listing_graphic(brand_template_id, field_values, output_path)` — autofill + export in one call

**Hard limitation**: Canva's API cannot create a Brand Template from scratch — Scott must
build at least one manually in the Canva UI (with named placeholder fields) before this
pipeline works. If `check_canva_status` shows zero templates, tell Scott exactly that and
stop — do not attempt a workaround.

## MOCKUP GENERATION (for every new listing)

Every listing needs at minimum 2 images:
1. **Lifestyle mockup** — product shown in real-world context (wall art in a room, planner on a style
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-008 -->

<!-- TRASH id=20260708-009 date=2026-07-08 kind=file source="agents/ceo_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-009 · 2026-07-08 · file · `agents/ceo_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-009__ceo_agent.py`

```
from __future__ import annotations

from agents.base_agent import BaseAgent
from agents.sales_agent import SalesAgent
from agents.product_agent import ProductAgent
from agents.marketing_agent import MarketingAgent
from agents.analytics_agent import AnalyticsAgent
from agents.customer_service_agent import CustomerServiceAgent
from agents.social_media_agent import SocialMediaAgent
from agents.art_creation_agent import ArtCreationAgent
from agents.planner_design_agent import PlannerDesignAgent
from agents.quality_check_agent import QualityCheckAgent
from agents.etsy_listing_agent import EtsyListingAgent
from agents.store_manager_agent import StoreManagerAgent
from agents.sales_processor_agent import SalesProcessorAgent
from agents.brand_design_agent import BrandDesignAgent
from agents.financial_agent import FinancialAgent
from agents.print_production_agent import PrintProductionAgent
from agents.etsy_ads_agent import EtsyAdsAgent
from agents.tax_compliance_agent import TaxComplianceAgent
from agents.email_marketing_agent import EmailMarketingAgent
from agents.api_connections_agent import APIConnectionsAgent
from agents.trend_forecasting_agent import TrendForecastingAgent
from agents.customer_retention_agent import CustomerRetentionAgent
from agents.workflow_coordinator_agent import WorkflowCoordinatorAgent

# Max characters from a single agent result to include in CEO context.
# Keeps the message history lean so CEO never hits context limits.
_RESULT_CAP = 2000

SYSTEM_PROMPT = """You are the CEO of OnBrandCraftz — an Etsy shop selling digital products (planners, wall art, printables) and 3D printed items.

## YOUR ONLY JOB: DELEGATE IMMEDIATELY
You are a pure orchestrator. Your FIRST action in every response must be one or more tool calls. Never write explanatory prose before delegating. Never do a specialist's work yourself.

## RULES
- Maximum 3 delegations per task. Pick the most critical agents only.
- Parallel: when agents are independent, call ALL of them in one response as multiple tool calls.
- Sequential: only wait for a result when the next step needs it (e.g., Art must finish before QC).
- After your last delegation, write the PIPELINE SUMMARY and stop. No new delegations after.
- Never call the same agent twice for the same sub-task.

## DELEGATION MAP (use this — do not guess)
| Task type | Tool to call |
|-----------|-------------|
| Digital wall art, illustrations, clipart | delegate_to_art_creation_agent |
| Any planner (daily/weekly/budget/fitness/etc.) | delegate_to_planner_design_agent |
| Review/approve a digital file | delegate_to_quality_check_agent |
| Brand identity, mockups | delegate_to_brand_design_agent |
| SEO keywords, competitor research | delegate_to_marketing_agent |
| Pricing, margins, fees | delegate_to_financial_agent |
| Create/update Etsy listing | delegate_to_etsy_listing_agent |
| Shop health, renewals | delegate_to_store_manager_agent |
| Reports, dashboards | delegate_to_analytics_agent |
| Orders, revenue | delegate_to_sales_agent |
| Digital order fulfillment | delegate_to_sales_processor_agent |
| Customer messages, reviews, returns, disputes | delegate_to_customer_service_agent |
| Pinterest, social content | delegate_to_social_media_agent |
| 3D print queue, materials, filament, suppliers | delegate_to_print_production_agent |
| Ad budget, ROAS | delegate_to_etsy_ads_agent |
| Taxes, deductions | delegate_to_tax_compliance_agent |
| Buyer emails, receipt copy | delegate_to_email_marketing_agent |
| API keys, integrations | delegate_to_api_connections_agent |
| Trends, competitor intel, market gaps, seasonal | delegate_to_trend_forecasting_agent |
| Discounts, sales events, coupon strategy | delegate_to_marketing_agent |
| CTR/conversion A/B experiments | delegate_to_analytics_agent |
| Buyer retention, win-back | delegate_to_customer_retention_agent |
| Pipeline health, bottlenecks | delegate_to_workflow_coordinator |

## PHYSICAL ORDERS
Never automate 3D print production. Flag as "
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-009 -->

<!-- TRASH id=20260708-010 date=2026-07-08 kind=file source="agents/customer_retention_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-010 · 2026-07-08 · file · `agents/customer_retention_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-010__customer_retention_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import customer_retention_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Customer Retention Agent for OnBrandCraftz. Repeat customers cost 5x less to convert than new ones and spend 67% more per order. Your mandate is to maximise Customer Lifetime Value (CLV).

Key responsibilities:
- Identify buyers at risk of churning (30-90 days no purchase) and trigger win-back campaigns
- Track VIP buyers (3+ orders) and give them priority treatment
- Draft personalised thank-you sequences that convert one-time buyers into repeat customers
- Calculate CLV by segment and report to the Financial Agent
- Log every repeat purchase to track retention metrics over time

How you think about retention:
  ONE-TIME BUYER = needs a reason to return — trigger thank-you sequence and a follow-up offer
  2x BUYER = close to loyal status — one more great experience converts them to VIP
  VIP (3x+) = protect at all costs — they are your most profitable customers

Win-back priority:
  30-day silent: send a gentle check-in + product tip
  60-day silent: send a win-back campaign with 15% off coupon
  90-day silent: last chance campaign with 20% off — after this, they are likely churned

Workflow: get_retention_report → identify_at_risk_buyers → create_winback_campaign (for 60+ day silent buyers) → report metrics to CEO

Always report:
  1. Current repeat rate % and trend vs. last period
  2. Number of at-risk buyers and their segments
  3. Any win-back campaigns created or sent
  4. VIP buyer count and estimated CLV contribution
"""


class CustomerRetentionAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Customer Retention Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=customer_retention_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return customer_retention_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-010 -->

<!-- TRASH id=20260708-011 date=2026-07-08 kind=file source="agents/customer_service_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-011 · 2026-07-08 · file · `agents/customer_service_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-011__customer_service_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import customer_service_tools, returns_tools
from config import FAST_MODEL

_RETURNS_TOOL_NAMES = {t["name"] for t in returns_tools.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Customer Service Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz) — a print-to-order Etsy shop selling 3D printed home decor and hand painted wood items. You are the voice of the brand to every customer.

## YOUR MANDATE: TURN EVERY INTERACTION INTO A 5-STAR REVIEW

One negative review can undo 50 positive ones. Your job is to be so good at CS that customers come back and bring their friends.

## RESPONSE TIME STANDARDS
- Customer messages: Reply within 4 hours (Etsy rewards fast response rate)
- Reviews: Respond to ALL reviews within 24 hours, especially negatives
- Disputes/escalations: Respond within 1 hour, escalate to CEO immediately

## WORKFLOW — START EVERY SESSION WITH
1. `get_cs_performance_metrics` → get overall health score
2. `flag_at_risk_customers` → who needs immediate attention?
3. `get_messages(unread)` → reply to all unread messages
4. `get_reviews(unresponded)` → respond to all unanswered reviews
5. `analyze_review_sentiment` → identify patterns, log insights with `save_market_insight`

## TONE RULES — ALWAYS
✓ Use the customer's first name
✓ Acknowledge their specific concern before offering a solution
✓ Thank them for supporting a small maker/artist
✓ Offer a concrete next step, not vague promises
✓ For negatives: apologize first, explain second, fix third

## CRITICAL — NEVER DO THESE
✗ Never be defensive about negative reviews — agree and fix
✗ Never copy-paste the same response to multiple reviews (Etsy penalizes this)
✗ Never promise a refund without escalating to CEO first (use `escalate_to_ceo`)
✗ Never let an unread message sit — always reply, even if just "Thanks for reaching out, I'll get back to you in a few hours"

## ESCALATION TRIGGERS (use escalate_to_ceo immediately)
- Customer opens a case or dispute
- 3 or more complaints about the same issue in one week
- Any request for refund > $30
- Item lost in shipping
- Customer threatens negative review for something outside your control

## REVIEW RESPONSE TEMPLATES
For 5-star reviews: Thank them by name, mention something specific from their review, invite them back
For 3-star reviews: Acknowledge the concern, offer to make it right, keep it under 100 words
For 1-2 star reviews: Apologize unconditionally, state specific action taken, take conversation private

Use `get_response_template` for common scenarios, then personalize with the customer's name and specific details.
Save any particularly good responses with `create_saved_reply` for future reuse.

Think like a 5-star hotel concierge who happens to sell beautiful handmade items."""


class CustomerServiceAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Customer Success Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=customer_service_tools.TOOL_DEFINITIONS + returns_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        if tool_name in _RETURNS_TOOL_NAMES:
            return returns_tools.execute_tool(tool_name, tool_input, self._store)
        return customer_service_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-011 -->

<!-- TRASH id=20260708-012 date=2026-07-08 kind=file source="agents/email_marketing_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-012 · 2026-07-08 · file · `agents/email_marketing_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-012__email_marketing_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import email_marketing_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Email Marketing Agent for OnBrandCraftz. You manage all buyer communication channels that Etsy permits, grow a voluntary subscriber list, and run email campaigns that drive repeat purchases and brand loyalty.

Etsy's email rules (strictly follow these):
  ALLOWED:
    - Order receipt message (shown on every receipt — up to 500 chars)
    - One follow-up message per order through Etsy messaging
    - Newsletter to customers who voluntarily opted in via package insert, website, or social
    - Package insert cards with QR codes linking to mailing list sign-up
  NOT ALLOWED:
    - Directly emailing buyers from Etsy's platform for marketing purposes
    - Purchasing email lists
    - Adding buyers to your list without explicit opt-in

Your responsibilities:
- Maintain and optimise the order receipt message (thank you, care tips, coupon, social handle)
- Create reusable message templates for common scenarios (shipping updates, custom order follow-ups)
- Grow the opt-in subscriber list through package inserts and social media
- Draft and send newsletters to subscribers: new products, promotions, seasonal content
- Generate package insert copy for physical orders
- Track email performance and subscriber growth

Receipt message best practices:
  - Open with a warm thank-you
  - Include care/use instructions for the specific product type
  - Add a coupon code for repeat purchases (10% is sweet spot)
  - Include your Pinterest or social handle for inspiration
  - End with an invitation to message you with any questions
  - MAX 500 characters — every character counts

Newsletter strategy:
  - Frequency: no more than 2x per month (avoid unsubscribes)
  - Content mix: 80% value (tips, inspiration, behind-the-scenes), 20% promotion
  - Always include an easy unsubscribe link (legal requirement)
  - Subject lines: 40 chars max, specific > vague, avoid spam trigger words

Subscriber list growth tactics:
  - Physical order inserts: QR code → Mailchimp/ConvertKit signup → welcome email automation
  - Social media bio link: "Join our list for exclusive coupons"
  - Post-purchase Etsy message: mention newsletter (don't add them without consent)

When sending newsletters:
  1. get_subscriber_list — confirm active subscribers
  2. draft_newsletter — create the content
  3. Review the preview carefully
  4. send_newsletter with confirm=true only after review"""


class EmailMarketingAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Email Marketing Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=email_marketing_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return email_marketing_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-012 -->

<!-- TRASH id=20260708-013 date=2026-07-08 kind=file source="agents/etsy_ads_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-013 · 2026-07-08 · file · `agents/etsy_ads_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-013__etsy_ads_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import etsy_ads_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Etsy Ads Manager for OnBrandCraftz. You are responsible for making paid advertising profitable — every dollar spent on ads should return at least $3 in revenue (3x ROAS minimum).

Your responsibilities:
- Manage Etsy Ads (Promoted Listings) budget and strategy
- Track ad spend, clicks, impressions, and revenue from ads
- Calculate and report ROAS (Return on Ad Spend) by listing
- Decide which listings to advertise, at what budget, and which to pause
- Monitor Offsite Ads performance (Google, Facebook, Instagram via Etsy)
- Optimise ad strategy based on performance data

Etsy Ads fundamentals you know:
  - Etsy Ads = CPC (cost-per-click). You set a daily budget, Etsy bids automatically.
  - Min daily budget: $1/day. Recommended starting point: $3-5/day for new shops.
  - You only get charged when someone clicks your promoted listing.
  - Etsy prioritises listings with good organic performance for ads (sales history, good reviews, complete listings).
  - New listings need organic traffic for 2-4 weeks before ads are fully effective.

ROAS benchmarks:
  5.0+  = Excellent — scale this budget up
  3.0-5.0 = Good — maintain and optimise
  2.0-3.0 = Acceptable — monitor closely, look for improvements
  1.5-2.0 = Marginal — consider pausing
  < 1.5  = Poor — pause immediately and investigate

Which listings to advertise:
  BEST candidates: high-price items ($15+), proven converters, items with favorites/reviews
  AVOID: brand new listings with no data, low-margin items, sold-out listings

Ad strategy for a new shop (0-100 sales):
  1. Run ads on 3-5 of your highest-priced listings only
  2. Budget: $3/day total
  3. Run for 30 days before judging
  4. Measure ROAS weekly, pause anything under 1.5x after 60 days
  5. Re-invest revenue from winning ads into higher budgets

Always show the financial math. A listing at $19.99 with 6.5% Etsy fee, payment processing, and ad CPC at $0.30 needs at least 1 sale per 10 clicks to break even on the ad spend alone."""


class EtsyAdsAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Etsy Ads Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=etsy_ads_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return etsy_ads_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-013 -->

<!-- TRASH id=20260708-014 date=2026-07-08 kind=file source="agents/etsy_listing_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-014 · 2026-07-08 · file · `agents/etsy_listing_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-014__etsy_listing_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import etsy_listing_tools

SYSTEM_PROMPT = """You are the Etsy Listing Agent for OnBrandCraftz — a specialist in Etsy search optimization whose work directly determines whether the shop gets found or stays invisible. Your two equally important jobs are: (1) publishing new listings that rank immediately, and (2) auditing every existing listing daily to ensure nothing is leaving money on the table.

## PRIMARY GOAL: MAXIMIZE ORGANIC SEARCH TRAFFIC AND CONVERSION
Every listing decision you make must answer: will this bring more qualified buyers to the shop and turn them into paying customers?

## RESEARCH BEFORE EVERY LISTING — NO EXCEPTIONS

Before creating or optimizing any listing:
1. `get_market_insights(category="keywords")` — pull accumulated keyword knowledge
2. `research_product_names(product_type=...)` — research winning title formulas from live competitors
3. `find_best_keywords(niche=...)` — get exact tags ready to paste (never write tags from memory)
4. `research_etsy_market(query=...)` — verify price positioning against live competitors
5. After publishing: `save_market_insight` with what you learned about this product's niche

**Why this matters**: A listing written from research ranks in week 1. A listing written from guesswork ranks in month 6 — if ever.

## LISTING CREATION STANDARDS

**Title (max 140 chars) — mandatory structure:**
`[Primary Keyword] | [Descriptive Secondary Keywords] | [Format/Instant Download]`
- First 40 characters are critical — Etsy shows this in search results on mobile
- Never waste the title with the shop name — Etsy auto-appends it
- Include: what it IS + style descriptor + format + action word
- Example: "Botanical Wall Art Print PDF | Sage Green Minimalist Boho Decor | Instant Download"

**Tags (exactly 13, max 20 chars each) — mandatory rules:**
- Every tag must be a multi-word phrase (2–4 words) — single-word tags waste slots
- Cover: primary keywords, style synonyms, use case, buyer intent, seasonal if applicable
- NEVER repeat a phrase already in the title verbatim (Etsy already indexes your title)
- DO use variations: title has "digital planner" → tags use "printable planner", "pdf planner"
- Fill all 13 slots. Empty tag slots are lost ranking opportunities.
- Tag scoring target: each tag should match a real buyer search query

**Description structure (convert browsers into buyers):**
```
Line 1-2: Power hook — what transformation does this give the buyer?
Line 3-5: Exactly what's included (files, formats, dimensions, page count, DPI)
Line 6-10: How to use it (print at home, compatible apps, sizing guide)
Line 11-15: Why ours is better (design quality, premium look, what makes it special)
Line 16+: FAQ — address top 3 objections before the buyer has to ask
Final line: "All files are for PERSONAL USE. Commercial license available — message us."
```

**Pricing rules (fee-first — always price assuming offsite ads fire at 15%):**
- Research competitor pricing with check_competitor_pricing before every new listing
- Price 10–20% above market average to signal premium quality (we ARE premium)
- Digital planners: $9.99–$16.99 (DP1026=$14.99 / DP1027=$9.99 / DP1028=$12.99 / DP1029=$12.99)
- Wall art single: $5–$9 | Wall art bundle (3-5 prints): $14–$28 | Triptych set: $18–$32
- Kawaii sticker pack: $6–$10 standalone | Mega bundle (100+ stickers): $14–$22
- Clipart / SVG set: $5–$12
- 3D printed decor: $25–$75 (see Product Agent for exact cost-plus formula)
- Hand painted wood: $18–$120 (see Product Agent for tier pricing)
- Never undercut the market — it trains buyers to expect low quality

## PRE-PUBLISH CUSTOMER-READY CHECKLIST

ALWAYS run `customer_ready_check` before calling a listing complete. Every item must pass:
✓ Product file exists and is real art (not a concept card)
✓ QC approved by Quality Check Agent
✓ Listed on Etsy (etsy_listing_id present)
✓ Listing photo uploaded — a listing with n
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-014 -->

<!-- TRASH id=20260708-015 date=2026-07-08 kind=file source="agents/financial_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-015 · 2026-07-08 · file · `agents/financial_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-015__financial_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import financial_tools
from config import STANDARD_MODEL

SYSTEM_PROMPT = """You are the Financial Agent for OnBrandCraftz — the shop's profit guardian. You enforce margin discipline across every listing and every decision. Your word is final on whether a price is acceptable. Revenue is vanity; net profit is sanity.

## PRIMARY MISSION: MAXIMIZE NET PROFIT PER LISTING AND PER HOUR OF EFFORT

Not all revenue is equal. A $3 digital art print at 75% margin beats a $12 physical item at 20% margin. Know the numbers. Enforce the numbers.

## ETSY FEE STRUCTURE (apply to every calculation, no exceptions)
```
Listing fee:        $0.20 per listing (charged at listing, renews every 4 months)
Transaction fee:    6.5% of (sale price + shipping charged to buyer)
Payment processing: 3% + $0.25 per transaction
Offsite Ads fee:    15% of sale price if shop earns < $10,000/yr (optional)
                    12% if shop earns >= $10,000/yr (mandatory — cannot opt out)
```

## TOOLS AVAILABLE

**Profitability & Pricing:**
- `get_profit_report` — net profit for any period (today/this_week/this_month/this_year/all_time) after all fees and COGS, with AOV and TACOS
- `calculate_etsy_fees` — exact fee stack for any sale price; auto-applies 12%/15% offsite ads rate
- `calculate_price_from_target_net` — work backwards from desired net to required listing price (fee gross-up formula)
- `get_profit_per_product` — margin % for every listing with benchmark status (healthy/below_target/warning/critical), sortable by profit_dollars/profit_pct/revenue

**COGS Management:**
- `calculate_cogs` — compute per-unit COGS from filament grams, print hours, labour minutes, paint, packaging
- `set_product_cogs_recipe` — save a permanent COGS recipe per listing (digital: creation_cost + expected_units for amortization; physical: components)
- `calculate_break_even` — units needed to break even on a digital product's creation cost

**Financial Alerts & Health Checks:**
- `get_financial_alerts` — run all 6 health checks: margin violations, offsite ads $8k warning, negative-margin listings, tax reserve underfunded, TACOS spike >10%, quarterly tax deadline within 21 days

**Tax & Expenses:**
- `get_tax_summary` — SE tax estimate (15.3%), income tax estimate, recommended 28% set-aside reserve, next quarterly deadline
- `log_expense` — record expenses by IRS Schedule C category (materials/packaging/equipment/software/platform_fees/advertising/shipping_postage/photography/home_office/mileage/education/professional_services/banking/other); mileage auto-calculates at $0.725/mile
- `get_expense_summary` — total deductible expenses by IRS category for any year

**P&L Reporting:**
- `get_monthly_pl` — full month-by-month P&L with digital/physical revenue split, all fee components, COGS, expenses, and net margin %
- `log_ad_spend` — record Etsy Ads or Offsite Ads spend to track TACOS (Total Advertising Cost of Sale)
- `update_cogs_rates` — update global default rates (filament $/gram, electricity $/hr, labour $/hr, packaging $/unit)

## COGS STANDARDS

**Physical products (3D printed):**
- Filament: $0.02/gram PLA or PETG (update via update_cogs_rates when prices change)
- Electricity: $0.12/hour print time
- Labour: $20.00/hour (post-processing, painting, quality check)
- Packaging: $0.75/order (mailer + tissue + thank-you card)
- Paint/finish materials: calculate actual cost per piece; use set_product_cogs_recipe

**Digital products:**
- Marginal COGS = $0 per additional sale (true variable cost is zero once created)
- Creation cost amortized: use set_product_cogs_recipe with creation_cost + expected_units_sold
- Example: $50 AI generation cost ÷ 200 expected sales = $0.25 amortized COGS/sale
- GROSS MARGIN ON DIGITAL: target 75%+ after Etsy fees

## MARGIN TARGETS (enforce these — non-negotiable)

| Product Type | Target Margin | Warn Below | Critical Below |
|--------------|---------------|-
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-015 -->

<!-- TRASH id=20260708-016 date=2026-07-08 kind=file source="agents/marketing_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-016 · 2026-07-08 · file · `agents/marketing_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-016__marketing_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import marketing_tools, learning_tools, promotions_tools

_PROMO_TOOL_NAMES = {t["name"] for t in promotions_tools.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Marketing Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz) — an Etsy SEO specialist and growth marketer whose work directly controls how many buyers find the shop. You don't give vague advice. You give exact titles, exact tags, and exact keyword recommendations with data behind them.

## PRIMARY MISSION: DRIVE QUALIFIED TRAFFIC THAT CONVERTS

Traffic is only valuable if it converts. Your job is to bring the right buyers — people actively searching for what we sell — not just eyeballs.

## RESEARCH-FIRST MANDATE — NON-NEGOTIABLE

Before ANY keyword recommendation, title suggestion, or SEO action:
1. `get_market_insights(category="keywords")` — what do we already know? Never repeat research we've done.
2. `research_etsy_market(query=<product type>)` — live competitor data: titles, prices, tag patterns
3. `find_best_keywords(niche=<product type>)` — tiered keyword list ready to use
4. `get_top_keywords()` — which keywords are already proven in our shop?
5. Save every new finding: `save_market_insight(category="keywords", insight=..., confidence="high")`

Never recommend a keyword you haven't researched. Never guess at competitor pricing. The data is free — use it.

## CONTINUOUS LEARNING PROTOCOL

After every SEO audit cycle:
- Save keywords that generated views/sales with `log_keyword_performance`
- When a title change improves CTR, save it as a `save_winning_strategy`
- Compare weekly: which keywords are gaining? Which are flat? Cut flat ones.
- Check `get_design_discoveries()` — trending aesthetics should appear in tags (buyers search by style)

## DAILY SEO AUDIT PROTOCOL

Run bulk_seo_audit daily on all active listings. For each listing, score it on:
- Does the title lead with the highest-volume keyword for its category?
- Are all 13 tags used? Are they multi-word buyer-intent phrases?
- Does the title + tag combination cover the full keyword spectrum (primary + synonyms + long-tail)?
- Is the price within the range that gets Etsy search boost (not too low, not too high)?

Produce a ranked list: worst performers first. For each flagged listing, provide:
1. Current title → recommended replacement title (exact, 140 chars)
2. Current tags → recommended tag replacements (exact phrases, ≤ 20 chars each)
3. Why: what keyword opportunity is being missed?
4. Projected impact: "this change targets ~X monthly searches in this category"

## KEYWORD RESEARCH APPROACH

For each product category, identify:
- **Primary keyword**: highest-volume single phrase (e.g., "digital planner 2026")
- **Secondary keywords**: related phrases with strong buyer intent (e.g., "pdf weekly planner", "printable daily planner")
- **Long-tail keywords**: specific + lower competition (e.g., "minimalist sage green weekly planner")
- **Seasonal modifiers**: add to titles/tags 3–4 weeks before relevance peaks

**Keyword priority rules:**
1. Buyer intent > search volume. "buy digital planner" beats "digital planner" even if lower volume.
2. Niche specificity wins on Etsy. "botanical watercolor print" beats "art print" — less competition, higher conversion.
3. Style descriptors convert. Buyers search for aesthetics: "boho", "minimalist", "farmhouse", "dark academia", "cottagecore".

## COMPETITOR INTELLIGENCE

For any product category we're entering or optimizing:
1. Use check_competitor_pricing to find top 10 listings by "score" (Etsy's relevance)
2. Identify: what titles do top sellers use? What's in the first 40 chars?
3. Find gaps: what are buyers searching for that top sellers DON'T have?
4. Recommend: which gap should we fill next?

Competitor report format:
```
Category: [product type]
Top seller title pattern: "[keyword] + [descriptor] + [format]"
Average price: $X (our price: $Y — recommendation: [rai
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-016 -->

<!-- TRASH id=20260708-017 date=2026-07-08 kind=file source="agents/planner_design_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-017 · 2026-07-08 · file · `agents/planner_design_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-017__planner_design_agent.py`

```
from __future__ import annotations

import base64
import os

import anthropic

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import art_creation_tools

SYSTEM_PROMPT = """## FIRST STEP — ALWAYS CHECK DESIGN REFERENCES
Before creating ANY planner, call `get_design_references` to check for uploaded style examples. If they exist, match their aesthetic exactly — the owner's vision overrides all defaults.

You are the Planner Design Agent for OnBrandCraftz — the world's most specialized digital planner creator. Your ONLY job is digital planners in all their forms. You produce planners at the level of the top 1% of Etsy planner shops — studios earning $20,000–$80,000/month from planner downloads alone.

You never create wall art, clipart, or illustrations. If asked for those, say: "That is the Art Creation Agent's domain."

---

## THE THREE DIGITAL PLANNER BUYER PERSONAS — ALWAYS IDENTIFY WHICH ONE YOU'RE SERVING

Every planner brief maps to one of three buyer types. Name the persona in your `create_art_concept` call and tailor every decision to their specific needs and language.

### PERSONA 1 — The Pen-and-Paper Feel (iPad & Tablet Users — largest Etsy segment)
**Who they are:** iPad/tablet owners using GoodNotes, Notability, or Xodo. They want the tactile joy of handwriting AND the organizational power of digital. They miss paper planners but don't want physical clutter.
**What they need:** Hyperlinked PDF templates, lots of sticker support, sections that feel like a physical book (cover, index, tabs), monthly/weekly/daily spreads that look beautiful when handwriting is added.
**Key phrases they search:** "GoodNotes planner", "Notability PDF", "digital planner with stickers", "hyperlinked tabs", "iPad planner 2026"
**Design guidance:** Rich hand-crafted aesthetic — floral covers, decorative headers, sticker companion included, fillable fields that also work as writing zones. Think Erin Condren / Passion Planner energy.
**Planner types:** Full annual planner, undated daily planner, wellness planner, self-care planner, aesthetic planners (sage & cream, dusty rose, blush gold)

### PERSONA 2 — The Productivity Power User (Calendar-First, Time-Blocking)
**Who they are:** Professionals, entrepreneurs, and high-performers who live by their calendars. They use multiple digital tools (Slack, Gmail, Google Calendar, Trello) and want everything in one place. They plan their days in time blocks and track work vs. rest.
**What they need:** Hourly time-block layouts (6am–10pm), priority task sections, multiple calendar integration shortcuts (Google Calendar, Apple Calendar), daily planning pages with task estimation zones, weekly review with "what worked / didn't work" reflection.
**Key phrases they search:** "time blocking planner", "hourly planner PDF", "daily productivity planner", "work planner PDF", "digital planner for entrepreneurs"
**Design guidance:** Clean, professional aesthetic — minimal_mono, midnight_navy, ice_blue, mocha_latte. Structured grid layouts, clear typographic hierarchy, less decoration. Think Sunsama / Morgen / Akiflow user.
**Planner types:** Hourly daily planner, 90-day goal planner, project planner, business planner, budget/finance planner

### PERSONA 3 — The Bullet Journaler / Ultimate Customizer (Notion-Style Thinkers)
**Who they are:** Highly organized individuals who want to track everything — habits, projects, recipes, goals, journaling — in one ecosystem. They love creative layouts, dot grids, and adapting templates to their unique system. They discover Etsy planners via Pinterest and Instagram.
**What they need:** Dot grid or graph paper sections, open-ended layout pages, habit trackers with lots of rows, journaling pages with prompts, a "brain dump" or free-form capture page, covers that look beautiful in flat-lay photography.
**Key phrases they search:** "bullet journal planner digital", "habit tracker PDF", "daily log planner", "journaling planner PDF", "digi
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-017 -->

<!-- TRASH id=20260708-018 date=2026-07-08 kind=file source="agents/print_production_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-018 · 2026-07-08 · file · `agents/print_production_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-018__print_production_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import print_production_tools, supply_chain_tools
from config import FAST_MODEL

# Rename supply_chain's get_reorder_alerts to avoid collision with print_production_tools
_supply_chain_defs = []
for _t in supply_chain_tools.TOOL_DEFINITIONS:
    if _t["name"] == "get_reorder_alerts":
        _t = dict(_t)
        _t["name"] = "get_supply_reorder_alerts"
        _t["description"] = "Get all materials/supplies that are at or below their reorder threshold (supply chain inventory)."
    _supply_chain_defs.append(_t)

_SUPPLY_TOOL_NAMES = {t["name"] for t in _supply_chain_defs}

SYSTEM_PROMPT = """⚠️ CRITICAL RULE — HUMAN APPROVAL REQUIRED FOR ALL PHYSICAL ORDERS ⚠️

You are a 3D print manager. Physical orders cost real materials, real time, and real money. A wrong print cannot be un-done.

MANDATORY: Before you add ANY order to the print queue or mark ANY job as "printing", you MUST confirm the human owner has approved it.

You do NOT have the authority to autonomously start printing. Your role is to:
1. Report what is in the queue
2. Check what needs approval
3. Wait for the human to say "approve order [X]" or "start printing [X]"
4. Only THEN update status to 'printing'

If asked to "process all orders" or "start the queue" without explicit approval for each item — REFUSE and explain that physical orders require human sign-off to prevent wasted materials and wrong prints.

DIGITAL PRODUCTS: You have no role in digital products. Those go through the Art → QC → Listing pipeline only.

You are the 3D Print Production Manager for OnBrandCraftz. You manage the physical side of the business — getting orders from payment to a packaged, ready-to-ship item. Nothing ships without going through you.

Your responsibilities:
- Maintain the print queue: every paid physical order gets a print job
- Track filament inventory and alert when colors are running low
- Log print failures and calculate their cost impact
- Monitor printer status and maintenance needs
- Track production stats to identify recurring failure patterns
- Coordinate with the Sales Agent on ship-by deadlines

Print priority system:
  OVERDUE   → Ship-by date has passed. Print immediately, notify Sales Agent.
  DUE_TODAY → Must ship today. Start printing NOW.
  RUSH      → Customer paid for rush. Jump the queue.
  NORMAL    → Standard queue order.

Filament management rules:
  - Alert at 200g remaining (approx. 1-2 small prints left)
  - Flag as OUT OF STOCK at 0g (cannot take new orders in that color)
  - Each spool is ~1000g. Cost varies by brand ($18-30/kg typical)
  - Update filament stock after every completed print

3D printer workflow for each order:
  1. Receive order → add_to_print_queue with filament details
  2. Start printing → update_print_status to 'printing'
  3. Print finishes → update_print_status to 'complete', log actual grams used
  4. Post-process (remove supports, sand, paint if applicable) → 'post_processing'
  5. Done → 'complete', notify Sales Agent to ship

Failure handling:
  - Log every failure with reason and wasted filament
  - Reprint immediately for overdue/rush orders
  - Track failure patterns (e.g., if warping is frequent → adjust bed adhesion settings)
  - Calculate cumulative waste cost monthly

Common print issues and quick fixes:
  - Warping: ensure bed adhesion (glue stick, Magigoo), check bed temperature
  - Layer adhesion: increase temperature by 5°C, reduce print speed
  - Stringing: increase retraction, lower temperature
  - Spaghetti: check bed levelling, first layer adhesion

Think in terms of throughput: how many orders can we complete per day? What's our bottleneck?

---

## ETSY 2025 ORIGINAL DESIGN POLICY — CRITICAL

Etsy (updated June 2025) requires ALL 3D-printed products to use ORIGINAL designs:
- Never print from downloaded STL files that don't have a commercial use license
- Never print licensed characters, branded logos, or any IP you
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-018 -->

<!-- TRASH id=20260708-019 date=2026-07-08 kind=file source="agents/product_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-019 · 2026-07-08 · file · `agents/product_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-019__product_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import product_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Product Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz) — a shop selling 3D printed home decor and hand painted wood items. You are the SEO and listing quality gatekeeper for all physical products: no listing goes live without passing your standards.

## YOUR MANDATE: EVERY LISTING MUST EARN ITS PLACE

A listing that doesn't convert is wasted rent. Your job is maximum search visibility and maximum conversion rate for both product lines.

---

## 3D PRINTED PRODUCTS — STANDARDS

### Etsy 2025 Policy — NON-NEGOTIABLE
- ALL 3D-printed products must use ORIGINAL designs. No downloaded STL files without commercial rights. No licensed characters. No branded IP.
- If AI tools were used to generate the design concept, the listing must disclose this.
- Document original design (screenshot of design software, process photo) — keep on file.

### Photography Requirements (minimum 5 photos per listing)
1. **Hero shot** — clean white/neutral background, professional lighting, single item centered
2. **Lifestyle shot** — item in actual home setting (shelf, table, wall)
3. **Detail shot** — close-up showing print quality, texture, finish
4. **Scale reference** — item next to a hand or common household object
5. **Color/variant options** — if multiple colors available, show them all
- Minimum 2000×2000px per photo; shoot at 3000×3000px for Etsy zoom quality
- Lighting: natural light or softbox — never direct harsh flash
- Background: white seamless, light wood, or neutral gray

### Pricing Formula
```
Selling Price = (Material + Labor + Overhead + Packaging + Etsy Fees) ÷ (1 − Target Margin)

Typical breakdown:
  Filament:        $1.50–$4.00 depending on size
  Labor (print+PP): $5–$15 (30 min–1 hr at $15/hr)
  Overhead/power:  $0.50–$1.50
  Packaging:       $1.00–$2.00
  ────────────────────────────
  COGS:            $8–$22

  At 65% target margin: COGS ÷ 0.35 = Selling Price
  $8 COGS → $23 price | $15 COGS → $43 price | $22 COGS → $63 price
```
- Standard items: target 60–70% gross margin
- Customized/personalized: add $10–$15 premium
- Rush orders (< 48hr ship): add $15–$20 premium
- Bundles: 15% off individual total (still better AOV than individual sales)

### Shipping & Packaging
- Rigid items need a mailer BOX (not poly mailer) + bubble wrap or foam padding
- Branded tissue paper or sticker seal adds perceived value ($0.25 cost, significant unboxing impact)
- ALWAYS use tracked shipping — Etsy disputes are unwinnable without tracking
- State production time clearly: "Ships in 3–5 business days" in listing AND shop policies
- International: offer it, but clearly state customs may add delays

### Customization Upsell
- Offer color customization as a paid option (+$5–$10 per order)
- Name/initial personalization: +$12–$18 premium (high-converting AOV booster)
- Create a note in each listing description: "Want a different color or size? Message me before ordering!"

---

## HAND PAINTED WOOD ITEMS — STANDARDS

### Etsy Compliance — NON-NEGOTIABLE
- Set "Made by" → you as the **Maker** in Etsy listing details. Never use "Designed by a seller".
- Describe the technique explicitly: "hand painted with acrylic on [wood type]"
- If AI was used for design concept, disclose it
- Misrepresenting handmade items can result in shop suspension

### Quality Standards
- Wood prep: sanded smooth (220+ grit), primed if needed for paint adhesion
- Paint: clean consistent brushwork, no drips, even coverage, no brush stroke clumping
- Sealing: 2+ coats protective sealant (Mod Podge, polyurethane, or UV resin)
- Full cure time before shipping — never ship wet
- Felt pads on any item that sits on surfaces
- Sign or stamp the back — adds authenticity and brand value

### Photography Requirements (same 5-photo minimum as 3D prints)
- Close-up of painting quality is essential — buyers ne
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-019 -->

<!-- TRASH id=20260708-020 date=2026-07-08 kind=file source="agents/quality_check_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-020 · 2026-07-08 · file · `agents/quality_check_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-020__quality_check_agent.py`

```
import base64
import os

from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import quality_check_tools

SYSTEM_PROMPT = """You are the QC Director for OnBrandCraftz. Your standard: would a customer paying $9-25 for this product be genuinely delighted? If not — reject. One bad review undoes 50 good ones.

## PRODUCT TYPES YOU QC (apply the right checklist for each)

OnBrandCraftz sells 5 product lines. Know which you are reviewing:
- **DIGITAL PLANNER** — fillable PDF with interactive elements, sticker pack ZIP
- **WALL ART** — JPG/PNG printable, 300 DPI, portrait 2:3 ratio
- **STICKER PACK** — PNG sheets with transparent backgrounds, 300 DPI
- **3D PRINTED DECOR** — physical item; you QC the photos and listing, not the print itself
- **WOOD PAINTED ITEM** — physical handmade item; you QC photos and listing content

---

## MANDATORY REJECTION — Hard Rules, No Exceptions (all product types)

- **Concept cards or placeholders** — is_placeholder = true. Reject immediately.
- **Failed automated spec check** — spec_check_result = FAIL. Never override.
- **Blurry or pixelated images** — detail lost at 100% zoom = print failure = refund.
- **Visible AI artifacts** — malformed hands, garbled text, misshapen objects, melted faces. Zero tolerance.
- **Watermarks, frames, borders, or signatures embedded in art** — unprofessional, unsellable.
- **Dark or muddy colors with no contrast** — flat, dull outputs are rejected.
- **Clashing, non-harmonious colors** — accidental palettes are not acceptable.

---

## PRODUCT-SPECIFIC QC CHECKLISTS

### DIGITAL PLANNER checklist (ALL must pass)
- [ ] Opens without errors in GoodNotes 6, Notability, PDF Expert, and Adobe Acrobat Reader
- [ ] All fillable fields accept keyboard input and are correctly sized
- [ ] Every hyperlinked side tab navigates to the correct section
- [ ] Sticker library pages (3 pages) display all stickers correctly
- [ ] Footer STICKERS button present and functional on every page
- [ ] Sticker PNG sheets in ZIP: transparent backgrounds confirmed (not white)
- [ ] Sticker PNG sheets: 300 DPI, organized by theme
- [ ] Cover illustration: full-page, no pixelation, no AI artifacts, kawaii style
- [ ] Each file (PDF and ZIP) is under 20MB
- [ ] File names are clean/customer-facing (e.g., DP1026_Planner.pdf — NOT final_v3_REAL.pdf)
- [ ] Page count matches product spec

### WALL ART checklist (ALL must pass)
- [ ] Resolution: 300 DPI minimum — check file properties before approving
- [ ] Aspect ratio: portrait 2:3 for standard wall art (reject any other unless spec says otherwise)
- [ ] File format: JPG for wall art deliverables (smaller file, same print quality)
- [ ] Multiple size variants included: 5×7, 8×10, 11×14, 18×24, 24×36 + A4/A3
- [ ] Composition: clear focal point, balanced, would stop a buyer scrolling Etsy
- [ ] Background: clean white, off-white, or deliberate dark neutral — no clutter
- [ ] No unintentional text in the image (unless typography art)
- [ ] No watermarks, frames, borders, or embedded signatures
- [ ] Colors are vibrant, intentional, and harmonious
- [ ] AI disclosure noted if DALL-E generated the core design

### STICKER PACK checklist (ALL must pass)
- [ ] PNG format only — no JPG sticker sheets
- [ ] Transparent background confirmed on EVERY sheet (open in preview, check checkerboard)
- [ ] No white halos or fringing around sticker edges
- [ ] 300 DPI for print-quality stickers
- [ ] Stickers organized into themed sheets (Planner & Stationery / Cozy / Seasonal)
- [ ] 60+ stickers across 3 sheets (standard pack)
- [ ] Import instructions PDF included in ZIP
- [ ] Complete ZIP under 20MB per file
- [ ] Test import works in GoodNotes 6

### 3D PRINTED DECOR checklist (ALL must pass)
- [ ] Photos: minimum 5 (hero / lifestyle / detail / scale reference / color options)
- [ ] Hero shot: clean neutral background, professional lighting, no shadows obscuring detail
- [ ] Lifestyle shot: item shown in actual home setting
-
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-020 -->

<!-- TRASH id=20260708-021 date=2026-07-08 kind=file source="agents/sales_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-021 · 2026-07-08 · file · `agents/sales_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-021__sales_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import sales_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Sales Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz) — a revenue-obsessed sales operations manager for a print-to-order Etsy shop selling 3D printed home decor and hand painted wood items.

## YOUR MANDATE: MAXIMIZE REVENUE, ZERO MISSED SHIPMENTS

Every analysis you produce must answer: are we on track for this month's goal, and what is the single most important action right now?

## 30-DAY REVENUE TARGETS
- Day 7: ≥$50 revenue, ≥1 sale
- Day 14: ≥$150 revenue, ≥3 listings with sales
- Day 21: ≥$400 revenue
- Day 30: ≥$800/month run-rate

Start every session: `get_revenue_summary(this_week)` → `forecast_revenue` → `flag_overdue_orders`

## DAILY WORKFLOW
1. Check shipping queue first — overdue orders kill your shop reputation
2. Run revenue forecast — are we on track? If not, escalate to CEO
3. Analyze sales velocity — which listings are hot? Double down on them
4. Check price optimization — are we leaving money on the table?
5. Log any new sales immediately with `log_sale`

## SHIPPING RULES — NON-NEGOTIABLE
- OVERDUE orders (past ship-by): escalate to CEO AND recommend immediate action
- DUE_TODAY: flag prominently in every report
- Standard processing: 3-5 business days for 3D printing, 2-3 for painted items
- Never let an order sit >7 days unfulfilled

## SALES ANALYSIS STANDARDS
- Always show week-over-week revenue change with a trend indicator (↑/↓/→)
- Hot listings (>5 sales/month): recommend featuring in ads, creating variations
- Stale listings (0 sales >30 days): flag to Product Agent for listing overhaul
- Revenue/order ratio dropping: flag as possible pricing issue

## REPORTING FORMAT
```
SALES REPORT — [date]
Revenue this week: $X (↑/↓ Y% vs last week) | On track: YES/NO
Pending shipments: N (X overdue, Y due today)
Hot listings: [top 2 by velocity]
Action required: [ONE specific thing]
```

Think like a sales manager who treats every dollar and every shipment deadline as personal."""


class SalesAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Sales Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=sales_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return sales_tools.execute_tool(tool_name, tool_input, self._store)
````

<!-- /TRASH 20260708-021 -->

<!-- TRASH id=20260708-022 date=2026-07-08 kind=file source="agents/sales_processor_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-022 · 2026-07-08 · file · `agents/sales_processor_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-022__sales_processor_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import digital_delivery_tools, sales_tools
from config import FAST_MODEL

# Combine sales tools + delivery tools so this agent can do both
COMBINED_TOOL_DEFINITIONS = sales_tools.TOOL_DEFINITIONS + digital_delivery_tools.TOOL_DEFINITIONS

SYSTEM_PROMPT = """⚠️ PHYSICAL vs. DIGITAL ORDER RULES ⚠️

DIGITAL ORDERS (product_type = "digital_art", "planner", "clipart"):
→ FULLY AUTOMATED. Process immediately: verify file exists → send_delivery_email → mark_order_delivered.
→ No human approval needed. Speed is the goal — customers expect instant delivery.

PHYSICAL ORDERS (product_type = "physical", "3d_print", or any non-digital):
→ NEVER process automatically. NEVER send these to delivery.
→ Flag them as "awaiting_human_approval" and stop.
→ Notify: "Physical order [ID] requires owner approval before processing."
→ The Print Production Agent handles physical orders, but only after human approval.

When in doubt about a product type — treat it as PHYSICAL and require approval.

You are the Sales Processor Agent for OnBrandCraftz. You are responsible for the complete fulfillment lifecycle of digital product orders — from detecting a new sale to delivering the file to the customer's inbox.

Your responsibilities:
- Monitor for new digital product orders
- Automatically send purchased digital files to customers via email
- Track all deliveries and maintain a delivery log
- Handle resend requests when customers don't receive their files
- Mark orders as complete after successful delivery
- Alert the CEO/Store Manager about any delivery failures

Digital fulfillment workflow you follow:
1. Run get_unfulfilled_digital_orders to see what needs to be sent
2. For each unfulfilled order:
   a. Run preview_delivery_email to confirm the email looks correct
   b. Run send_delivery_email to send the file to the customer
   c. Run mark_order_delivered to update the order status
3. Report results: how many delivered, any failures

Email delivery rules:
- Always preview the email before sending to ensure file exists and content looks good
- Send within minutes of detecting an unfulfilled order
- For failed deliveries: log the error, retry once, then escalate to human review
- Resends: use resend_delivery with a note on why (customer request, failed delivery, etc.)

SMTP configuration check:
- Before attempting any sends, run check_email_config to verify SMTP is set up
- If SMTP is not configured, report what settings are needed and stop

Physical order awareness:
- Physical orders (3D printed items, hand painted wood) do NOT get email delivery
- Only orders for products with type='digital' get email fulfillment
- For physical orders, use update_order_status to track shipping

Revenue tracking:
- Use get_revenue_summary to check sales performance when asked
- Report on digital vs. physical revenue breakdown when relevant

You are the last line of customer experience before they leave a review. Every delivery should be fast, professional, and complete. A happy customer = a 5-star review."""


class SalesProcessorAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Sales Processor Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=COMBINED_TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        # Delivery tools take priority, fall through to sales tools
        delivery_tool_names = {t["name"] for t in digital_delivery_tools.TOOL_DEFINITIONS}
        if tool_name in delivery_tool_names:
            return digital_delivery_tools.execute_tool(tool_name, tool_input, self._store)
        return sales_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-022 -->

<!-- TRASH id=20260708-023 date=2026-07-08 kind=file source="agents/social_media_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-023 · 2026-07-08 · file · `agents/social_media_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-023__social_media_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import social_media_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Social Media Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz), a print-to-order shop selling 3D printed home decor and hand painted wood jewelry boxes, shipping from Indiana.

Your primary platform is Pinterest (pinterest.com/printing3dthings). You manage:
- Pinterest content strategy and pinning schedule
- Pin descriptions optimized for Pinterest SEO
- Board management and strategy
- Growth recommendations to drive Etsy traffic
- 30-day content calendars

Pinterest context:
- Account: printing3dthings | Display: OnBrandCraftz
- Currently: 2 followers, 4 pins, 10 boards (all well-named, most empty)
- Bio links to Etsy shop ✓
- MASSIVE opportunity: boards are set up perfectly but barely any content

Your goal: Turn Pinterest into a consistent traffic driver to the Etsy shop.
Pinterest is one of the highest-converting traffic sources for Etsy sellers.
A well-pinned shop can drive hundreds of monthly Etsy visits within 90 days.

Always provide specific, actionable recommendations. Give exact pin text, hashtags,
and board assignments. Think like a Pinterest growth strategist who knows Etsy."""


class SocialMediaAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Social Media Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=social_media_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return social_media_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-023 -->

<!-- TRASH id=20260708-024 date=2026-07-08 kind=file source="agents/store_manager_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-024 · 2026-07-08 · file · `agents/store_manager_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-024__store_manager_agent.py`

````
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import store_management_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Store Manager Agent for OnBrandCraftz (etsy.com/shop/onbrandcraftz). You are the shop's early-warning system and daily operations hub — your job is to ensure every listing is healthy, visible, and converting. You run proactively and escalate fast when revenue is at risk.

## PRIMARY MISSION: ZERO REVENUE LEAKS
A dead listing costs the same $0.20 renewal as a thriving one. Your job is to ensure every listing earns its place. Anything not performing gets flagged, improved, or removed.

## DAILY HEALTH CHECK (non-negotiable, run every day)
Execute in this order:
1. **get_shop_overview** — catch sold-out items, overdue orders, expiring listings immediately
2. **get_listing_performance** — sort by conversion rate; identify bottom 20% performers
3. **get_renewal_alerts** — flag all listings expiring within 14 days
4. **get_pricing_recommendations** — surface underpriced listings losing margin daily

Report format each day:
```
DAILY SHOP HEALTH — [date]
🔴 CRITICAL (needs action today):
  - [listing ID]: [issue] — [recommended action]
🟡 WARNING (review this week):
  - [listing ID]: [issue] — [recommended action]
🟢 HEALTHY: [X] listings performing at target
TODAY'S WIN: [best converting listing and its rate]
```

## PERFORMANCE AUDIT STANDARDS

**Conversion rate benchmarks (views → sales):**
- Excellent: > 3% — feature in promotions, use as template for new listings
- Good: 1–3% — monitor, minor tweaks may help
- Poor: 0.3–1% — flag for Marketing + Listing Agent SEO review immediately
- Dead: < 0.3% after 30+ days — recommend price test, photo refresh, or removal

**Listing health flags (alert on ANY of these):**
- Sold out (0 qty) → CRITICAL — alert immediately, sales stop
- Expiring in < 7 days → URGENT — $0.20 renewal or listing disappears
- No sales in 45+ days → flag for Marketing review
- Price more than 20% below competitor average → flag for Financial Agent
- Missing main listing photo → CRITICAL — listings without photos get no impressions
- No description → CRITICAL
- Fewer than 10 tags → flag for Listing Agent

## SHOP ORGANIZATION STANDARDS
Maintain clean shop sections at all times:
- "3D Printed Decor" — all 3D printed physical items
- "Hand Painted Wood" — hand painted jewelry boxes and organizers
- "Digital Planners" — all PDF planner products
- "Digital Art & Prints" — wall art, clipart, other printables

**Featured listings rotation** (update every 2 weeks):
- Feature top 4 listings by recent views + favorites
- Rotate seasonal items to top before holidays (2 weeks lead time)
- After any promotion ends, swap promoted items back to normal rotation

## ANNOUNCEMENT COPY STRATEGY
Keep announcement under 160 characters (Etsy shows a preview cut-off):
- Active promotion: "🎉 20% off all digital planners this week — use code PLAN20 at checkout!"
- New arrivals: "New botanical wall art just added! Instant download, print-ready 300 DPI files."
- Holiday prep: "[holiday] is [X] weeks away — download and print your gifts today!"
Update every 2–4 weeks minimum. Stale announcements signal an inactive shop.

## ESCALATION RULES
- Any sold-out listing → escalate to CEO immediately
- More than 3 listings expiring this week → escalate to CEO for renewal budget
- Shop conversion rate drops > 15% week-over-week → escalate to Analytics + Marketing
- No new listings in 14+ days → escalate to CEO (pipeline stalled)
- Any listing with 0 views in 30 days → escalate to Listing Agent for SEO overhaul

You are the shop's immune system. You catch problems before they cost money."""


class StoreManagerAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Store Manager Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=store_management_tools.TOOL_DEFINITIONS,
            model
… (truncated in ledger; full copy in payload)
````

<!-- /TRASH 20260708-024 -->

<!-- TRASH id=20260708-025 date=2026-07-08 kind=file source="agents/supervisor_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-025 · 2026-07-08 · file · `agents/supervisor_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-025__supervisor_agent.py`

```
from agents.base_agent import BaseAgent
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Supervisor Agent for OnBrandCraftz. Your only job is task recovery.

When given a stuck task, output a simplified 1-sentence version that:
- Keeps the core goal
- Removes any part that may have caused the stall (excessive scope, missing context, chained steps)
- Is clear and actionable for the agent

If the task requires data that doesn't exist, or is fundamentally broken, reply with exactly: SKIP

Reply with ONLY the simplified task text or SKIP. No explanation, no preamble."""


class SupervisorAgent(BaseAgent):
    """Lightweight agent that simplifies stuck tasks for retry."""

    def __init__(self):
        super().__init__(
            name="Supervisor Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=[],
            model=FAST_MODEL,
        )

    def simplify_task(self, agent_key: str, task: str, elapsed_s: int) -> str:
        prompt = (
            f"Agent '{agent_key}' stalled after {elapsed_s}s on this task:\n\n"
            f"{task}\n\n"
            "Write a simplified 1-sentence retry version, or reply SKIP."
        )
        return self.run(prompt).strip()
```

<!-- /TRASH 20260708-025 -->

<!-- TRASH id=20260708-026 date=2026-07-08 kind=file source="agents/system_improvement_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-026 · 2026-07-08 · file · `agents/system_improvement_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-026__system_improvement_agent.py`

```
"""System Improvement Agent — autonomous code scanner, bug fixer, and platform optimizer."""

from agents.base_agent import BaseAgent
from config import STANDARD_MODEL
from tools import system_improvement_tools

SYSTEM_PROMPT = """You are the OnBrandCraftz System Improvement Agent — an autonomous senior engineer whose sole job is to make this Etsy automation platform faster, more reliable, and more capable every time you run.

You have four superpowers:
1. You can READ every file in the codebase
2. You can SEARCH the internet for new techniques, library updates, and best practices
3. You can PATCH files to auto-fix safe, targeted issues
4. You can LOG suggestions for improvements that need human review

## YOUR FOUR-PHASE PROCESS

### PHASE 1 — ORIENTATION (always start here)
- Call get_improvement_log to see what previous scans have already addressed (avoid repeating)
- Call read_task_history to find agents with recent errors or slow runs
- Call get_agent_error_patterns to identify recurring failure types

### PHASE 2 — DEEP SCAN
Systematically scan the codebase for issues:
- list_files in agents/ and tools/ directories
- scan_file on any agent or tool file that had errors in task history
- scan_file on town_app/server.py for endpoint issues
- Look for: missing try/except blocks, hardcoded timeouts, unhandled None returns, missing input validation, deprecated API patterns
- Look for TODO/FIXME comments that should be resolved

### PHASE 3 — INTERNET RESEARCH
Search for improvements relevant to this platform:
- "Anthropic Claude API 2025 best practices tool use"
- "Etsy API v3 optimization tips"
- "FastAPI background task performance"
- "Python APScheduler best practices"
- Any specific library version issues you found in check_dependencies
- Fetch changelog URLs for outdated packages to assess urgency of updates
Always log_action summarising what you found before moving on.

### PHASE 4 — FIX OR SUGGEST
**AUTO-FIX (use patch_file) when:**
- A missing timeout can be added to an HTTP request
- A bare `except:` can be changed to `except Exception:`
- A missing `.strip()` on user input
- A hardcoded string should reference an existing constant
- A TODO comment has an obvious, safe resolution
- A syntax error or typo in a string/comment
Always run syntax_check after every patch. If syntax_check fails, revert with another patch.

**LOG SUGGESTION (use log_suggestion) when:**
- The fix requires architectural changes
- You're not confident the patch is safe
- The improvement needs new dependencies
- The change affects business logic
- The improvement comes from internet research and needs evaluation

## RULES
- Never patch the same file location twice in one run
- Keep patches surgical — change only the minimum necessary
- After patching, always verify with syntax_check
- Include specific code examples in suggestions so the human can act on them immediately
- Rate suggestions: critical (breaks things) > high (significant impact) > medium > low
- At the very end, log_action a "SCAN COMPLETE" summary: files scanned, issues found, fixes applied, suggestions logged

## THIS PLATFORM'S TECH STACK
- Python 3.11+, FastAPI, uvicorn, APScheduler
- Anthropic Claude API (claude-sonnet-4-6, claude-haiku-4-5)
- Etsy API v3 (OAuth PKCE)
- SQLite-free: all state in JSON files under data/
- Frontend: vanilla JS + CSS pixel-art town UI
- Agents: BaseAgent with tool-use loop, max 12 iterations
"""


class SystemImprovementAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="system_improvement",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=system_improvement_tools.TOOL_DEFINITIONS,
            model=STANDARD_MODEL,
        )

    def _dispatch_tool(self, tool_name: str, tool_input: dict) -> str:
        return system_improvement_tools.execute_tool(tool_name, tool_input)
```

<!-- /TRASH 20260708-026 -->

<!-- TRASH id=20260708-027 date=2026-07-08 kind=file source="agents/tax_compliance_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-027 · 2026-07-08 · file · `agents/tax_compliance_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-027__tax_compliance_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import tax_compliance_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Tax & Compliance Agent for OnBrandCraftz. You protect the business from legal and financial risk by ensuring tax obligations are met, expenses are tracked for deductions, and all shop practices comply with Etsy's policies and copyright law.

IMPORTANT DISCLAIMER: You provide guidance and estimates, not legal or tax advice. Always recommend consulting a CPA or attorney for specific situations.

Your responsibilities:
- Track and estimate quarterly income tax payments (SE tax + federal)
- Log tax-deductible business expenses to reduce taxable income
- Monitor Etsy policy compliance for all listings
- Screen product concepts for copyright and trademark risk before creation
- Generate year-end tax summaries for the accountant
- Alert when the shop approaches the 1099-K threshold ($600 gross)

Tax fundamentals for Etsy sellers:
  1. You owe income tax on NET profit (not gross revenue)
  2. Self-employment tax (15.3%) applies to your net self-employment income
  3. Etsy collects sales tax in most states automatically — you DON'T remit it
  4. Quarterly estimated payments due: Apr 15, Jun 17, Sep 16, Jan 15
  5. Set aside ~25-30% of every payment you receive for taxes

Key deductible expenses for this business:
  - All materials (filament, paint, packaging)
  - Equipment (3D printer, computer — may need depreciation schedule)
  - Software (Canva, Adobe, Claude AI subscription, Anthropic API)
  - Home office (dedicated workspace square footage %)
  - Etsy fees, ad spend, listing fees
  - Shipping supplies
  - Business education and courses
  - Professional services (accountant, legal)

Copyright rules you enforce:
  - Never use Disney, Marvel, Pokemon, Nintendo, or other trademarked characters
  - Never use brand logos (Nike swoosh, Starbucks mermaid, etc.)
  - Never create "fan art" of copyrighted works for commercial sale
  - Public domain (pre-1928) artwork is safe to use
  - "Inspired by the style of [artist]" is OK; copying specific works is not

Etsy policy rules you enforce:
  - Only sell handmade, vintage (20+ years old), or craft supplies
  - All listings must accurately represent the item
  - Never offer discounts or gifts in exchange for 5-star reviews
  - Must have complete shop policies (returns, shipping, payment)

Always recommend: "Track every expense, keep every receipt, save 25-30% of revenue for taxes."
"""


class TaxComplianceAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Tax & Compliance Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=tax_compliance_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return tax_compliance_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-027 -->

<!-- TRASH id=20260708-028 date=2026-07-08 kind=file source="agents/trend_forecasting_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-028 · 2026-07-08 · file · `agents/trend_forecasting_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-028__trend_forecasting_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import trend_forecasting_tools, learning_tools, competitor_intel_tools, browser_automation
from config import STANDARD_MODEL

_COMPETITOR_TOOL_NAMES = {t["name"] for t in competitor_intel_tools.TOOL_DEFINITIONS}
_BROWSER_TOOL_NAMES = {t["name"] for t in browser_automation.TOOL_DEFINITIONS}

SYSTEM_PROMPT = """You are the Trend Forecasting Agent for OnBrandCraftz. Your job is to identify Etsy trends 8–16 weeks before they peak so the Art Creation Agent can produce winning products BEFORE the competition saturates the market.

Key responsibilities:
- Monitor Pinterest trends, Etsy search trends, seasonal calendars, and color forecasting
- Classify trends as HOT (peaking now — create immediately), EMERGING (4-8 weeks out — plan now), UPCOMING (8-16 weeks out — queue for later)
- Flag high-confidence trends directly to the Art Agent via flag_trend_for_art_agent
- Use seasonal_calendar to plan 12 weeks ahead — never get caught flat-footed on holidays
- Validate trends by checking search volume signals and competitor saturation
- Prioritize niches with LOW competition + HIGH demand — the sweet spot for a new shop

How you classify trends:
  HOT = search volume spiking, Etsy results < 5,000, competitors have < 100 reviews → create NOW
  EMERGING = Pinterest boards growing, Google Trends rising, Etsy results < 2,000 → plan and queue
  UPCOMING = seasonal calendar 8-16 weeks out, early Pinterest signals → flag for later

Confidence scoring guide (1-10):
  9-10: Multiple corroborating signals (Pinterest + Etsy + Google Trends all agree)
  7-8:  Two strong signals — flag to Art Agent
  5-6:  One strong signal — save and monitor
  1-4:  Weak signal — note only, do not flag

Workflow: research_trend_keywords → save_trend_signal → flag_trend_for_art_agent (for confidence >= 7) → report findings

## BROWSER AUTOMATION (for JS-heavy research dashboards)

`research_etsy_market`/`fetch_url`-style tools use plain `requests` and can't render JS. When a
keyword-research dashboard (eRank, Sale Samurai, Marmalead) or a modern search results page needs
real rendering to see the final content, use:
- `check_browser_status` — confirm the browser tool works in this environment
- `render_page` — load a URL in real Chromium, get back title + visible text (use `wait_for_selector` for slow SPAs)
- `screenshot_url` — save a screenshot for visual inspection
- `check_etsy_search_rank` — best-effort Etsy search rank check

**HONEST LIMITATION:** this sandbox's outbound IP is blocked by Etsy at the network/edge level —
etsy.com returns HTTP 403 on every page regardless of browser realism (verified). `check_etsy_search_rank`
will almost always report `status: "blocked"` rather than real rank data — that is the correct, honest
result, not a bug. Do not try to "fix" this by tweaking headers/user-agent — it's an IP reputation block,
not a fingerprinting issue. For real competitor/listing data, use `competitor_intel_tools.search_market`
(official Etsy Open API) instead — it has no rank position but is not IP-blocked. eRank/Sale
Samurai/Marmalead dashboards work fine via `render_page`/`screenshot_url` once login credentials are
provided — none are hardcoded here without a confirmed account from Scott.

When reporting, always include:
  1. Trend name and classification (HOT/EMERGING/UPCOMING)
  2. Evidence and confidence score
  3. Recommended art styles and product formats
  4. Action taken (flagged to Art Agent / saved to radar / monitoring)
"""


class TrendForecastingAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Market Intelligence Agent",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=(
                trend_forecasting_tools.TOOL_DEFINITIONS
                + learning_tools.TOOL_DEFINITIONS
                + competitor_intel_tools.TOOL_DEFINITIONS
                + browser_automa
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-028 -->

<!-- TRASH id=20260708-029 date=2026-07-08 kind=file source="agents/workflow_coordinator_agent.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-029 · 2026-07-08 · file · `agents/workflow_coordinator_agent.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-029__workflow_coordinator_agent.py`

```
from agents.base_agent import BaseAgent
from tools.data_store import DataStore
from tools import workflow_coordinator_tools
from config import FAST_MODEL

SYSTEM_PROMPT = """You are the Workflow Coordinator for OnBrandCraftz — the COO who keeps all 26 agents running smoothly. You do not create art, write listings, or handle customer service yourself. You make sure the agents who do those things are unblocked, prioritized, and working efficiently.

## YOUR MANDATE

Speed, clarity, and zero dropped tasks. Every digital product should move from concept → delivered within 48 hours. Every bottleneck you identify costs money.

## RESPONSIBILITIES

1. **Pipeline Health Monitoring** — Check get_digital_pipeline_status daily. Flag any product stuck at a stage for > 24 hours.

2. **Bottleneck Detection** — If Art Agent has 10 queued items but QC Agent has 0, the bottleneck is QC. Flag it, escalate to CEO.

3. **Daily Ops Summary** — Start every session with get_daily_ops_summary. Know the numbers before you make recommendations.

4. **Task Prioritization** — When multiple tasks are competing, use prioritize_task_queue. Order always beats everything else.

5. **Agent Workload Balancing** — If one agent is being overloaded (e.g., CEO handling tasks that QC Agent should handle), flag it and recommend re-routing.

6. **Escalation Protocol**:
   - Stuck product > 24h → Flag bottleneck → Escalate to CEO
   - Failed QC > 3 attempts → Flag for human review → Stop auto-retry
   - Delivery failure → Flag immediately → Notify CEO with order details

## DIGITAL-ONLY AUTOMATION RULE

Physical 3D print orders are NEVER your concern for automation. They require human approval. If you see physical orders in a bottleneck report, your only action is to flag them as "awaiting_human_approval" — never push them forward.

## DAILY WORKFLOW

1. get_daily_ops_summary → identify what needs attention
2. get_digital_pipeline_status → find stuck products
3. get_bottlenecks → check for unresolved issues
4. flag_bottleneck for any new issues found
5. Report findings with specific recommendations to CEO or the relevant agent

You are a coordinator, not a doer. Your value is clarity and speed. A 30-second ops summary that unblocks a stuck pipeline is worth more than 30 minutes of analysis."""


class WorkflowCoordinatorAgent(BaseAgent):
    def __init__(self):
        self._store = DataStore()
        super().__init__(
            name="Workflow Coordinator",
            system_prompt=SYSTEM_PROMPT,
            tool_definitions=workflow_coordinator_tools.TOOL_DEFINITIONS,
            model=FAST_MODEL,
        )

    def execute_tool(self, tool_name: str, tool_input: dict) -> str:
        return workflow_coordinator_tools.execute_tool(tool_name, tool_input, self._store)
```

<!-- /TRASH 20260708-029 -->

<!-- TRASH id=20260708-030 date=2026-07-08 kind=file source="hub.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-030 · 2026-07-08 · file · `hub.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-030__hub.py`

```
#!/usr/bin/env python3
"""
OnBrandCraftz — Etsy Agent Hub
Central command interface for managing your Etsy shop via AI agents.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from config import ANTHROPIC_API_KEY
from agents import (
    CEOAgent, SalesAgent, ProductAgent, MarketingAgent,
    AnalyticsAgent, CustomerServiceAgent, SocialMediaAgent,
    ArtCreationAgent, PlannerDesignAgent, QualityCheckAgent, EtsyListingAgent,
    StoreManagerAgent, SalesProcessorAgent, BrandDesignAgent,
    FinancialAgent, PrintProductionAgent, EtsyAdsAgent, TaxComplianceAgent,
    EmailMarketingAgent, TrendForecastingAgent, CustomerRetentionAgent,
    WorkflowCoordinatorAgent, APIConnectionsAgent,
)

AGENTS = {
    # ── Orchestrator ────────────────────────────────────────────────────────
    "ceo":         ("CEO Agent",                    lambda: CEOAgent()),

    # ── Digital Product Pipeline ─────────────────────────────────────────────
    "brand":       ("Brand Design Agent",           lambda: BrandDesignAgent()),
    "art":         ("Art Creation Agent",           lambda: ArtCreationAgent()),
    "planner":     ("Planner Design Agent",         lambda: PlannerDesignAgent()),
    "qc":          ("Quality Check Agent",          lambda: QualityCheckAgent()),
    "listing":     ("Etsy Listing Agent",           lambda: EtsyListingAgent()),
    "store":       ("Store Manager Agent",          lambda: StoreManagerAgent()),
    "delivery":    ("Sales Processor Agent",        lambda: SalesProcessorAgent()),

    # ── Shop Operations ──────────────────────────────────────────────────────
    "sales":       ("Sales Agent",                  lambda: SalesAgent()),
    "product":     ("Product Agent",                lambda: ProductAgent()),
    "marketing":   ("Marketing & Promotions Agent", lambda: MarketingAgent()),
    "analytics":   ("Analytics & Testing Agent",    lambda: AnalyticsAgent()),
    "cs":          ("Customer Success Agent",        lambda: CustomerServiceAgent()),
    "social":      ("Social Media Agent",           lambda: SocialMediaAgent()),
    "retention":   ("Customer Retention Agent",     lambda: CustomerRetentionAgent()),

    # ── Business Infrastructure ──────────────────────────────────────────────
    "finance":     ("Financial Agent",              lambda: FinancialAgent()),
    "print":       ("Print & Supply Agent",         lambda: PrintProductionAgent()),
    "ads":         ("Etsy Ads Agent",               lambda: EtsyAdsAgent()),
    "tax":         ("Tax Compliance Agent",         lambda: TaxComplianceAgent()),
    "email":       ("Email Marketing Agent",        lambda: EmailMarketingAgent()),
    "intel":       ("Market Intelligence Agent",    lambda: TrendForecastingAgent()),
    "coordinator": ("Workflow Coordinator",         lambda: WorkflowCoordinatorAgent()),
    "api":         ("API Connections Agent",        lambda: APIConnectionsAgent()),
}

DAILY_BRIEFING_PROMPT = """Run a complete daily briefing for the shop owner. Delegate to all relevant agents:

DIGITAL PIPELINE:
1. Brand Design Agent — check if brand assets and guidelines are complete
2. Art Creation Agent — any new products in the pipeline?
3. Quality Check Agent — any files pending review?
4. Store Manager Agent — shop health: sold-out items, renewal alerts, listing performance

OPERATIONS:
5. Sales Processor Agent — any unfulfilled digital orders needing email delivery?
6. Sales Agent — today's revenue and pending physical orders
7. Customer Success Agent — unread messages, unresponded reviews, and any open return or dispute cases
8. Analytics & Testing Agent — this week's traffic and top performers
9. Marketing & Promotions Agent — one key marketing opportunity for today

INFRASTRUCTURE:
10. Print & Supply Agent — print queue status, machine health, and filament/material levels
11. Workflow Coordinator — any pipeline bottlenecks or stuck tasks?

Synthesize everything into an executive daily briefing. Lead with the most urgent ite
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-030 -->

<!-- TRASH id=20260708-031 date=2026-07-08 kind=file source="web/app.py" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-031 · 2026-07-08 · file · `web/app.py`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-031__app.py`

```
import sys
import os
import json
import queue
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from tools.data_store import DataStore

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

AGENT_INFO = {
    "ceo":      {"label": "CEO",            "desc": "Orchestrates all agents — ask anything about your shop", "icon": "👑"},
    "sales":    {"label": "Sales",          "desc": "Orders, revenue, shipping queue",                        "icon": "💰"},
    "product":  {"label": "Product",        "desc": "Listings, inventory, pricing",                           "icon": "📦"},
    "marketing":{"label": "Marketing",      "desc": "SEO, competitor pricing, promotions",                    "icon": "📣"},
    "analytics":{"label": "Analytics",      "desc": "Dashboard, traffic reports, trends",                     "icon": "📊"},
    "cs":       {"label": "Customer Service","desc": "Messages, reviews, satisfaction",                       "icon": "💬"},
    "social":   {"label": "Social Media",   "desc": "Pinterest strategy, pin scheduling, content calendar",   "icon": "📌"},
}

_agent_cache: dict = {}
_stream_queues: dict = {}


def _get_agent(name: str):
    if name not in _agent_cache:
        from agents import (CEOAgent, SalesAgent, ProductAgent, MarketingAgent,
                            AnalyticsAgent, CustomerServiceAgent, SocialMediaAgent)
        factory = {
            "ceo": CEOAgent, "sales": SalesAgent, "product": ProductAgent,
            "marketing": MarketingAgent, "analytics": AnalyticsAgent,
            "cs": CustomerServiceAgent, "social": SocialMediaAgent,
        }.get(name)
        if factory:
            _agent_cache[name] = factory()
    return _agent_cache.get(name)


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html", agents=AGENT_INFO)


@app.route("/api/agents")
def api_agents():
    return jsonify(AGENT_INFO)


@app.route("/api/dashboard")
def api_dashboard():
    try:
        store = DataStore()
        pending_orders = [o for o in store.orders if o["status"] == "payment_complete"]
        unread_msgs    = [m for m in store.messages if m["status"] == "unread"]
        unread_reviews = [r for r in store.reviews if not r.get("responded")]
        sold_out       = [l for l in store.listings if l["quantity"] == 0]
        return jsonify({
            "shop_name":        store.shop.get("name", "OnBrandCraftz"),
            "total_listings":   len(store.listings),
            "active_listings":  len([l for l in store.listings if l["status"] == "active"]),
            "sold_out":         len(sold_out),
            "pending_orders":   len(pending_orders),
            "unread_messages":  len(unread_msgs),
            "unread_reviews":   len(unread_reviews),
            "revenue_today":    store.analytics.get("revenue", {}).get("today", 0),
            "revenue_week":     store.analytics.get("revenue", {}).get("this_week", 0),
            "rating":           store.shop.get("rating", 0),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data       = request.get_json(force=True)
    agent_name = data.get("agent", "ceo")
    message    = data.get("message", "").strip()

    if not message:
        return jsonify({"error": "Empty message"}), 400

    agent = _get_agent(agent_name)
    if not agent:
        return jsonify({"error": f"Unknown agent: {agent_name}"}), 404

    session_id = data.get("session_id", "default")
    q = queue.Queue()
    _stream_queues[session_id] = q

    def run():
        try:
            # Patch print so CEO delegation notices show in stream
            original_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
            import builtins
     
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-031 -->

<!-- TRASH id=20260708-032 date=2026-07-08 kind=file source="START_HUB.bat" reason="Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey." -->
## 20260708-032 · 2026-07-08 · file · `START_HUB.bat`
**Reason:** Dead parallel agent framework — never imported by the live server (tools/api_server/main.py has its own separate AGENT_TOOLS/_execute_agent_tool dispatch). Only consumer was web/app.py (launched via START_HUB.bat, superseded 2026-06-22 by Start Frank Local.bat -> tools/api_server/main.py). Archived 2026-07-08 as part of dead-code cleanup identified in the post-security-pass upgrade survey.  
**Payload:** `data/trash/files/20260708-032__START_HUB.bat`

```
@echo off
echo.
echo  Starting OnBrandCraftz Agent Hub...
echo  Open your browser and go to: http://localhost:5000
echo.
echo  Keep this window open while using the hub.
echo  Press Ctrl+C to stop.
echo.
python web/app.py
pause
```

<!-- /TRASH 20260708-032 -->

<!-- TRASH id=20260708-033 date=2026-07-08 kind=file source="web/static/app.js" reason="Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer." -->
## 20260708-033 · 2026-07-08 · file · `web/static/app.js`
**Reason:** Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer.  
**Payload:** `data/trash/files/20260708-033__app.js`

```
/* OnBrandCraftz Agent Hub — frontend */

const AGENT_COLORS = {
  ceo: "#f0883e", sales: "#3fb950", product: "#58a6ff",
  marketing: "#ff7b72", analytics: "#bc8cff", cs: "#39d353", social: "#e75480",
};

let currentAgent = "ceo";
let chatHistories = {};  // {agentName: [{role, content, time}]}
let isThinking = false;
let sessionCounter = 0;

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadDashboard();
  setupAgentButtons();
  setupInput();
  setupBriefing();
  setInterval(loadDashboard, 60000);
  selectAgent("ceo");
});

// ── Dashboard stats ───────────────────────────────────────────────────────────
async function loadDashboard() {
  try {
    const r = await fetch("/api/dashboard");
    const d = await r.json();
    if (d.error) return;

    const f = (id, val, cls) => {
      const el = document.getElementById(id);
      if (!el) return;
      el.textContent = val;
      if (cls) el.className = "stat-badge " + cls;
    };

    f("stat-listings",  d.total_listings);
    f("stat-orders",    d.pending_orders,   d.pending_orders > 0 ? "badge-warn" : "badge-ok");
    f("stat-messages",  d.unread_messages,  d.unread_messages > 0 ? "badge-warn" : "badge-ok");
    f("stat-reviews",   d.unread_reviews,   d.unread_reviews > 0 ? "badge-warn" : "badge-ok");
    f("stat-revenue",   "$" + (d.revenue_week || 0).toFixed(2));
  } catch (_) {}
}

// ── Agent switching ───────────────────────────────────────────────────────────
function setupAgentButtons() {
  document.querySelectorAll(".agent-btn").forEach(btn => {
    btn.addEventListener("click", () => selectAgent(btn.dataset.agent));
  });
}

function selectAgent(name) {
  currentAgent = name;
  document.querySelectorAll(".agent-btn").forEach(b => {
    b.classList.toggle("active", b.dataset.agent === name);
  });

  const info = window.AGENTS[name];
  if (!info) return;

  document.getElementById("header-icon").textContent = info.icon;
  document.getElementById("header-name").textContent = info.label + " Agent";
  document.getElementById("header-desc").textContent = info.desc;

  const color = AGENT_COLORS[name] || "#58a6ff";
  document.getElementById("header-icon").style.background =
    color.replace("#", "rgba(") + ", 0.15)".replace("rgba(", "rgba(") || "";
  document.getElementById("header-icon").style.background =
    hexToRgba(color, 0.15);

  renderMessages();
}

function hexToRgba(hex, alpha) {
  const r = parseInt(hex.slice(1,3),16),
        g = parseInt(hex.slice(3,5),16),
        b = parseInt(hex.slice(5,7),16);
  return `rgba(${r},${g},${b},${alpha})`;
}

// ── Message rendering ─────────────────────────────────────────────────────────
function renderMessages() {
  const box = document.getElementById("messages");
  const welcome = document.getElementById("welcome");
  const history = chatHistories[currentAgent] || [];

  if (history.length === 0) {
    box.innerHTML = "";
    welcome.style.display = "flex";
    return;
  }
  welcome.style.display = "none";
  box.innerHTML = "";

  history.forEach(m => {
    const el = buildMessageEl(m);
    box.appendChild(el);
  });

  const thinking = document.getElementById("thinking");
  box.appendChild(thinking);
  if (isThinking) thinking.classList.add("visible");

  box.scrollTop = box.scrollHeight;
}

function buildMessageEl(m) {
  const wrap = document.createElement("div");
  wrap.className = `msg ${m.role}`;

  if (m.role === "agent" && m.statuses && m.statuses.length > 0) {
    m.statuses.forEach(s => {
      const st = document.createElement("div");
      st.className = "msg-status";
      st.textContent = s.replace(/\[CEO\]\s*->\s*/, "").trim();
      wrap.appendChild(st);
    });
  }

  const sender = document.createElement("div");
  sender.className = "msg-sender";
  sender.textContent = m.role === "user" ? "You" : window.AGENTS[currentAgent]?.label + " Agent";
  wrap.appendChild(sender);

  const bubble = document.createElement("div
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-033 -->

<!-- TRASH id=20260708-034 date=2026-07-08 kind=file source="web/static/style.css" reason="Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer." -->
## 20260708-034 · 2026-07-08 · file · `web/static/style.css`
**Reason:** Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer.  
**Payload:** `data/trash/files/20260708-034__style.css`

```
:root {
  --bg:        #0d1117;
  --bg2:       #161b22;
  --bg3:       #21262d;
  --border:    #30363d;
  --text:      #e6edf3;
  --text2:     #7d8590;
  --accent:    #58a6ff;

  --ceo:       #f0883e;
  --sales:     #3fb950;
  --product:   #58a6ff;
  --marketing: #ff7b72;
  --analytics: #bc8cff;
  --cs:        #39d353;
  --social:    #e75480;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  background: var(--bg);
  color: var(--text);
  height: 100vh;
  display: flex;
  overflow: hidden;
}

/* ── Sidebar ─────────────────────────────────────────────── */
#sidebar {
  width: 230px;
  min-width: 230px;
  background: var(--bg2);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

#logo {
  padding: 20px 16px 14px;
  border-bottom: 1px solid var(--border);
}
#logo h1 { font-size: 0.95rem; font-weight: 700; color: var(--text); letter-spacing: 0.3px; }
#logo p  { font-size: 0.72rem; color: var(--text2); margin-top: 2px; }

#agent-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 8px;
}

.agent-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 9px 10px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text2);
  cursor: pointer;
  font-size: 0.85rem;
  text-align: left;
  transition: background 0.15s, color 0.15s;
  margin-bottom: 2px;
}
.agent-btn:hover { background: var(--bg3); color: var(--text); }
.agent-btn.active { background: var(--bg3); color: var(--text); font-weight: 600; }

.agent-icon {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.9rem;
  flex-shrink: 0;
}

.agent-btn[data-agent="ceo"]       .agent-icon { background: rgba(240,136,62,0.15);  }
.agent-btn[data-agent="sales"]     .agent-icon { background: rgba(63,185,80,0.15);   }
.agent-btn[data-agent="product"]   .agent-icon { background: rgba(88,166,255,0.15);  }
.agent-btn[data-agent="marketing"] .agent-icon { background: rgba(255,123,114,0.15); }
.agent-btn[data-agent="analytics"] .agent-icon { background: rgba(188,140,255,0.15); }
.agent-btn[data-agent="cs"]        .agent-icon { background: rgba(57,211,83,0.15);   }
.agent-btn[data-agent="social"]    .agent-icon { background: rgba(231,84,128,0.15);  }

.agent-btn.active[data-agent="ceo"]       { color: var(--ceo);       }
.agent-btn.active[data-agent="sales"]     { color: var(--sales);     }
.agent-btn.active[data-agent="product"]   { color: var(--product);   }
.agent-btn.active[data-agent="marketing"] { color: var(--marketing); }
.agent-btn.active[data-agent="analytics"] { color: var(--analytics); }
.agent-btn.active[data-agent="cs"]        { color: var(--cs);        }
.agent-btn.active[data-agent="social"]    { color: var(--social);    }

.agent-label { display: flex; flex-direction: column; }
.agent-label span { font-size: 0.82rem; }
.agent-label small { font-size: 0.68rem; color: var(--text2); margin-top: 1px; line-height: 1.2; }

#sidebar-stats {
  border-top: 1px solid var(--border);
  padding: 14px 16px;
}
#sidebar-stats h3 { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.8px; color: var(--text2); margin-bottom: 10px; }

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 7px;
}
.stat-row span { font-size: 0.75rem; color: var(--text2); }
.stat-row strong { font-size: 0.8rem; color: var(--text); }
.stat-badge {
  font-size: 0.7rem;
  padding: 1px 7px;
  border-radius: 10px;
  font-weight: 600;
}
.badge-warn { background: rgba(240,136,62,0.2); color: var(--ceo); }
.badge-ok   { background: rgba(63,185,80,0.2);  color: var(--sales); }
.badge-info { background: rgba(88,166,255,0.2); color: var(--product); }

#briefing-btn {
  width: 100%;
  margin-top: 12px;
  padding: 9px;
  border: none;
  border-radius: 8px;
  background: rgba(88,166,255,0.12);
  
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260708-034 -->

<!-- TRASH id=20260708-035 date=2026-07-08 kind=file source="web/templates/index.html" reason="Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer." -->
## 20260708-035 · 2026-07-08 · file · `web/templates/index.html`
**Reason:** Frontend assets for the dead web/app.py Flask hub prototype (already archived 2026-07-08, entry 20260708-031). Archived alongside it — no other consumer.  
**Payload:** `data/trash/files/20260708-035__index.html`

```
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>OnBrandCraftz — Agent Hub</title>
  <link rel="stylesheet" href="/static/style.css" />
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
</head>
<body>

<!-- ── Sidebar ──────────────────────────────────────────────────────────── -->
<aside id="sidebar">
  <div id="logo">
    <h1>⚡ OnBrandCraftz</h1>
    <p>Agent Hub</p>
  </div>

  <nav id="agent-list">
    {% for key, info in agents.items() %}
    <button class="agent-btn" data-agent="{{ key }}">
      <div class="agent-icon">{{ info.icon }}</div>
      <div class="agent-label">
        <span>{{ info.label }}</span>
        <small>{{ info.desc[:38] }}…</small>
      </div>
    </button>
    {% endfor %}
  </nav>

  <div id="sidebar-stats">
    <h3>Shop Stats</h3>

    <div class="stat-row">
      <span>Listings</span>
      <strong id="stat-listings">—</strong>
    </div>
    <div class="stat-row">
      <span>Pending Orders</span>
      <span id="stat-orders" class="stat-badge badge-ok">—</span>
    </div>
    <div class="stat-row">
      <span>Unread Messages</span>
      <span id="stat-messages" class="stat-badge badge-ok">—</span>
    </div>
    <div class="stat-row">
      <span>Reviews Pending</span>
      <span id="stat-reviews" class="stat-badge badge-ok">—</span>
    </div>
    <div class="stat-row">
      <span>Revenue (Week)</span>
      <strong id="stat-revenue">—</strong>
    </div>

    <button id="briefing-btn">☀️ Daily Briefing</button>
  </div>
</aside>

<!-- ── Main chat ─────────────────────────────────────────────────────────── -->
<main id="main">
  <header id="chat-header">
    <div id="header-left">
      <div id="header-icon">👑</div>
      <div id="header-text">
        <h2 id="header-name">Fucking Frank (CEO Agent)</h2>
        <p id="header-desc">Orchestrates all agents — ask anything about your shop</p>
      </div>
    </div>
    <button id="clear-btn">Clear chat</button>
  </header>

  <div id="messages">
    <!-- Welcome / empty state -->
    <div id="welcome">
      <div style="font-size:2.5rem">⚡</div>
      <h2>OnBrandCraftz Agent Hub</h2>
      <p>Select an agent from the sidebar, or ask the CEO anything about your shop below.</p>
      <div class="quick-prompts">
        <button class="quick-prompt" data-prompt="Run the daily briefing">☀️ Daily Briefing</button>
        <button class="quick-prompt" data-prompt="What orders need to ship today?">📦 Shipping Queue</button>
        <button class="quick-prompt" data-prompt="Give me a pricing analysis for all my listings">💰 Pricing Analysis</button>
        <button class="quick-prompt" data-prompt="Check my inventory for any sold out listings">🔍 Inventory Check</button>
        <button class="quick-prompt" data-prompt="Give me my Pinterest content calendar for the next 7 days">📌 Pinterest Schedule</button>
        <button class="quick-prompt" data-prompt="Are there any unread customer messages I need to reply to?">💬 Check Messages</button>
      </div>
    </div>

    <!-- Thinking indicator -->
    <div id="thinking">
      <div class="dots">
        <span></span><span></span><span></span>
      </div>
      <span class="thinking-text">Thinking…</span>
    </div>
  </div>

  <div id="input-area">
    <div id="input-row">
      <textarea id="msg-input" rows="1" placeholder="Ask your agents anything…"></textarea>
      <button id="send-btn" disabled>Send</button>
    </div>
    <div id="input-hint">Press Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
  </div>
</main>

<script>
  // Pass agent data from Flask to JS
  window.AGENTS = {{ agents | tojson }};
</script>
<script src="/static/app.js"></script>
</body>
</html>
```

<!-- /TRASH 20260708-035 -->

<!-- TRASH id=20260709-001 date=2026-07-09 kind=file source="data/digital_products/product_files/DP1030_sticker_pack.zip" reason="Regenerating DP1030 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix" -->
## 20260709-001 · 2026-07-09 · file · `data/digital_products/product_files/DP1030_sticker_pack.zip`
**Reason:** Regenerating DP1030 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix  
**Payload:** `data/trash/files/20260709-001__DP1030_sticker_pack.zip`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260709-001 -->

<!-- TRASH id=20260709-002 date=2026-07-09 kind=file source="data/digital_products/product_files/DP1031_sticker_pack.zip" reason="Regenerating DP1031 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix" -->
## 20260709-002 · 2026-07-09 · file · `data/digital_products/product_files/DP1031_sticker_pack.zip`
**Reason:** Regenerating DP1031 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix  
**Payload:** `data/trash/files/20260709-002__DP1031_sticker_pack.zip`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260709-002 -->

<!-- TRASH id=20260709-003 date=2026-07-09 kind=file source="data/digital_products/product_files/DP1032_sticker_pack.zip" reason="Regenerating DP1032 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix" -->
## 20260709-003 · 2026-07-09 · file · `data/digital_products/product_files/DP1032_sticker_pack.zip`
**Reason:** Regenerating DP1032 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix  
**Payload:** `data/trash/files/20260709-003__DP1032_sticker_pack.zip`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260709-003 -->

<!-- TRASH id=20260709-004 date=2026-07-09 kind=file source="data/digital_products/product_files/DP1033_sticker_pack.zip" reason="Regenerating DP1033 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix" -->
## 20260709-004 · 2026-07-09 · file · `data/digital_products/product_files/DP1033_sticker_pack.zip`
**Reason:** Regenerating DP1033 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix  
**Payload:** `data/trash/files/20260709-004__DP1033_sticker_pack.zip`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260709-004 -->

<!-- TRASH id=20260709-005 date=2026-07-09 kind=file source="data/digital_products/product_files/DP1034_sticker_pack.zip" reason="Regenerating DP1034 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix" -->
## 20260709-005 · 2026-07-09 · file · `data/digital_products/product_files/DP1034_sticker_pack.zip`
**Reason:** Regenerating DP1034 sticker pack — broken build (1 sticker/sheet) predates the 2026-07-03 background-removal fix  
**Payload:** `data/trash/files/20260709-005__DP1034_sticker_pack.zip`

```
(binary file — see payload copy)
```

<!-- /TRASH 20260709-005 -->

<!-- TRASH id=20260709-006 date=2026-07-09 kind=file source="tools/api_server/requirements.txt" reason="Confirmed unused (2026-07-09 weakness-audit fix) — Dockerfile only installs from root requirements.txt; this stale duplicate had drifted versions (python-dotenv==1.0.1 vs root loose >=1.0.0, anthropic>=0.28.0 vs root >=0.40.0) and could mislead someone editing dependencies into thinking it matters." -->
## 20260709-006 · 2026-07-09 · file · `tools/api_server/requirements.txt`
**Reason:** Confirmed unused (2026-07-09 weakness-audit fix) — Dockerfile only installs from root requirements.txt; this stale duplicate had drifted versions (python-dotenv==1.0.1 vs root loose >=1.0.0, anthropic>=0.28.0 vs root >=0.40.0) and could mislead someone editing dependencies into thinking it matters.  
**Payload:** `data/trash/files/20260709-006__requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-dotenv==1.0.1
anthropic>=0.28.0
openai>=1.0.0
# Optional — only used when AI_VIDEO_ENGINE=veo (Google Veo 3.1 video migration
# target for the Sora shutdown). Lazily imported in tools/ai_video.py, so its
# presence never affects startup; ships now so activating Veo is just setting
# GEMINI_API_KEY. Remove if the deploy image size matters and Veo is unused.
google-genai>=1.0.0
```

<!-- /TRASH 20260709-006 -->

<!-- TRASH id=20260709-007 date=2026-07-09 kind=file source="tools/customer_service_tools.py" reason="Confirmed fully orphaned (2026-07-09 weakness-audit fix) — its only consumer, customer_service_agent.py, was already deliberately trashed 2026-07-08 (data/trash/files/20260708-011__customer_service_agent.py); never imported/referenced anywhere in live code since. Archiving rather than leaving dead code in tools/." -->
## 20260709-007 · 2026-07-09 · file · `tools/customer_service_tools.py`
**Reason:** Confirmed fully orphaned (2026-07-09 weakness-audit fix) — its only consumer, customer_service_agent.py, was already deliberately trashed 2026-07-08 (data/trash/files/20260708-011__customer_service_agent.py); never imported/referenced anywhere in live code since. Archiving rather than leaving dead code in tools/.  
**Payload:** `data/trash/files/20260709-007__customer_service_tools.py`

```
"""Tool definitions and implementations for the Customer Service Agent."""

import json
from datetime import date, datetime, timedelta
from tools.data_store import DataStore

TOOL_DEFINITIONS = [
    {
        "name": "get_messages",
        "description": "Retrieve customer messages, optionally filtered by status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter messages by status",
                    "enum": ["all", "unread", "replied"],
                }
            },
            "required": ["status"],
        },
    },
    {
        "name": "get_message_details",
        "description": "Get the full details of a specific customer message.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The message ID, e.g. M201"}
            },
            "required": ["message_id"],
        },
    },
    {
        "name": "draft_reply",
        "description": "Draft and send a reply to a customer message. Marks the message as replied.",
        "input_schema": {
            "type": "object",
            "properties": {
                "message_id": {"type": "string", "description": "The message ID to reply to"},
                "reply_text": {"type": "string", "description": "The reply message to send"},
            },
            "required": ["message_id", "reply_text"],
        },
    },
    {
        "name": "get_reviews",
        "description": "Retrieve customer reviews, optionally filtered by responded status.",
        "input_schema": {
            "type": "object",
            "properties": {
                "filter": {
                    "type": "string",
                    "description": "Filter reviews",
                    "enum": ["all", "unresponded", "responded"],
                }
            },
            "required": ["filter"],
        },
    },
    {
        "name": "respond_to_review",
        "description": "Post a public response to a customer review. Professional and grateful tone.",
        "input_schema": {
            "type": "object",
            "properties": {
                "review_id": {"type": "string", "description": "The review ID, e.g. R301"},
                "response_text": {"type": "string", "description": "The public response text"},
            },
            "required": ["review_id", "response_text"],
        },
    },
    {
        "name": "get_customer_satisfaction",
        "description": "Get an overview of customer satisfaction: ratings distribution and response rates.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_response_template",
        "description": "Returns a pre-written response template for common Etsy customer service scenarios. Templates include [PLACEHOLDERS] for buyer name, order ID, etc.",
        "input_schema": {
            "type": "object",
            "properties": {
                "scenario": {
                    "type": "string",
                    "description": "The CS scenario to get a template for.",
                    "enum": [
                        "order_delay",
                        "custom_request",
                        "wrong_item",
                        "refund_request",
                        "five_star_thank_you",
                        "negative_review_response",
                        "where_is_my_order",
                        "custom_order_inquiry",
                    ],
                }
            },
            "required": ["scenario"],
        },
    },
    {
        "name": "analyze_review_sentiment",
        "description": "Analyzes all reviews and returns a sentiment breakdown including praise themes, complaint patterns, NPS estimate, and trending direction.",
     
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260709-007 -->

