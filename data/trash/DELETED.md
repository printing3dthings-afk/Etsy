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

