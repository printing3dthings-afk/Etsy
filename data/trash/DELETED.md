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

