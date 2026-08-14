# Deletion Recycle Bin

> Everything deleted by an automated edit (code blocks or whole files) is
> archived here first, kept for **30 days**, then auto-pruned. To recover
> something, run `python tools/trash.py --restore <id>` (or just copy it back
> out of the fenced block below). Byte-exact copies also live in
> `data/trash/files/`.

<!-- TRASH id=20260725-001 date=2026-07-25 kind=file source="tools/health_check.py" reason="orphaned -- zero references anywhere (not imported/subprocess-invoked by main.py or any other tools/*.py file, no CLAUDE.md mention, no CI workflow reference, no real test coverage); superseded by shop_health_check.py + main.py builtin health loop (2026-07-25 cleanup pass, verified via dedicated read-only cross-reference agent)" -->
## 20260725-001 · 2026-07-25 · file · `tools/health_check.py`
**Reason:** orphaned -- zero references anywhere (not imported/subprocess-invoked by main.py or any other tools/*.py file, no CLAUDE.md mention, no CI workflow reference, no real test coverage); superseded by shop_health_check.py + main.py builtin health loop (2026-07-25 cleanup pass, verified via dedicated read-only cross-reference agent)  
**Payload:** `data/trash/files/20260725-001__health_check.py`

```
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
  
… (truncated in ledger; full copy in payload)
```

<!-- /TRASH 20260725-001 -->
<!-- TRASH id=20260731-001 date=2026-07-31 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="More screen UX audit (2026-07-31): dead badge-conversations lookup -- no element with id='badge-conversations' exists anywhere on either platform (removed when Conversations was merged into Knowledge, task #21), the DOM lookup was never cleaned up. Guarded by if(badge), so harmless, but unfinished plumbing." -->
## 20260731-001 · 2026-07-31 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** More screen UX audit (2026-07-31): dead badge-conversations lookup -- no element with id='badge-conversations' exists anywhere on either platform (removed when Conversations was merged into Knowledge, task #21), the DOM lookup was never cleaned up. Guarded by if(badge), so harmless, but unfinished plumbing.  
**Payload:** `data/trash/files/20260731-001__snippet.txt`

```python
    const badge = document.getElementById('badge-conversations');
    if (badge) {
      const total = _convSessions.reduce((sum, s) => sum + (s.message_count || 0), 0);
      badge.textContent = total > 999 ? '999+' : total;
      badge.style.display = total > 0 ? '' : 'none';
    }
```

<!-- /TRASH 20260731-001 -->
<!-- TRASH id=20260731-002 date=2026-07-31 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="More screen UX audit (2026-07-31): vestigial CSS rule referencing a .more-row class that has never existed in the actual DOM (the real markup uses .pmore-item/.pmore-grp) -- already flagged as vestigial in the 2026-07-17 ops_runbook entry and never removed." -->
## 20260731-002 · 2026-07-31 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** More screen UX audit (2026-07-31): vestigial CSS rule referencing a .more-row class that has never existed in the actual DOM (the real markup uses .pmore-item/.pmore-grp) -- already flagged as vestigial in the 2026-07-17 ops_runbook entry and never removed.  
**Payload:** `data/trash/files/20260731-002__snippet.txt`

```python
body:not(.show-advanced) .more-row[data-tier="advanced"]{display:none}
```

<!-- /TRASH 20260731-002 -->
<!-- TRASH id=20260806-001 date=2026-08-06 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Settings audit 2026-08-06: color theme reduction 12->5 per Scott request -- removed 7 CSS theme blocks (Dark Purple, Warm Charcoal, Sakura, Matcha, Mermaid Bright, Clubroom Gold, Spring Vivid), keeping Studio Warm, Day Mode, Ocean Teal, Midnight Kawaii, Sunwashed." -->
## 20260806-001 · 2026-08-06 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Settings audit 2026-08-06: color theme reduction 12->5 per Scott request -- removed 7 CSS theme blocks (Dark Purple, Warm Charcoal, Sakura, Matcha, Mermaid Bright, Clubroom Gold, Spring Vivid), keeping Studio Warm, Day Mode, Ocean Teal, Midnight Kawaii, Sunwashed.  
**Payload:** `data/trash/files/20260806-001__snippet.txt`

```python
html.theme-purple{
  --bg:#0c0714;--panel:#160d24;--panel2:#1e1330;--panel3:#291a3e;--border:#221537;
  --cyan:#9b5de5;--cyan2:#c4a0ff;--gold:#f7b731;--gold2:#ffd166;
  --text:#ede8f5;--muted:#8679af;--green:#3dba7e;--red:#e05555;--amber:#e0a83a;
}
html.theme-charcoal{
  --bg:#13100a;--panel:#1f1b12;--panel2:#28231a;--panel3:#332c22;--border:#2e281d;
  --cyan:#e8b84a;--cyan2:#f5d47a;--gold:#85c17e;--gold2:#aae0a0;
  --text:#f0e8d0;--muted:#96896c;--green:#85c17e;--red:#d0614a;--amber:#e8b84a;
}
html.theme-sakura{
  --bg:#140a10;--panel:#1f0f18;--panel2:#2a1420;--panel3:#35192b;--border:#311826;
  --cyan:#f4a7b9;--cyan2:#ffd0db;--gold:#c4607a;--gold2:#e58aa5;
  --text:#f5e8ee;--muted:#a4758a;--green:#3dba7e;--red:#e05555;--amber:#e0a83a;
}
html.theme-matcha{
  --bg:#0b120c;--panel:#121c14;--panel2:#1a281c;--panel3:#223424;--border:#1e2e21;
  --cyan:#8bc34a;--cyan2:#bce88e;--gold:#d4a96a;--gold2:#e6c48a;
  --text:#e9f2e6;--muted:#7c9172;--green:#6bbf59;--red:#e05555;--amber:#e0a83a;
}
html.theme-mermaid{
  --bg:#f0fbfa;--panel:#ffffff;--panel2:#dff6f3;--panel3:#ffffff;--border:#bfe8e2;
  --cyan:#007d73;--cyan2:#005850;--gold:#7a45e0;--gold2:#5b2fb0;
  --text:#0b3b38;--muted:#3a736c;--green:#12814d;--red:#d6362b;--amber:#a46400;
  --card-shadow:0 1px 2px rgba(20,30,45,.06),0 4px 14px rgba(20,30,45,.08);
  --card-shadow-hover:0 2px 4px rgba(20,30,45,.08),0 10px 26px rgba(20,30,45,.14);
}
html.theme-clubroom{
  --bg:#fffdf5;--panel:#ffffff;--panel2:#f5ebd0;--panel3:#ffffff;--border:#e8d9a8;
  --cyan:#2d6cdf;--cyan2:#1e4fa8;--gold:#916c08;--gold2:#6b4f05;
  --text:#1c1608;--muted:#6b5a2e;--green:#1a8548;--red:#d53a3a;--amber:#916c08;
  --card-shadow:0 1px 2px rgba(20,30,45,.06),0 4px 14px rgba(20,30,45,.08);
  --card-shadow-hover:0 2px 4px rgba(20,30,45,.08),0 10px 26px rgba(20,30,45,.14);
}
html.theme-springvivid{
  --bg:#fbf7ff;--panel:#ffffff;--panel2:#f0e6fb;--panel3:#ffffff;--border:#dcc7f5;
  --cyan:#c4157f;--cyan2:#8e0e5c;--gold:#bc4f1b;--gold2:#8a3a13;
  --text:#241541;--muted:#6b5490;--green:#18804f;--red:#d0342a;--amber:#bc4f1b;
  --card-shadow:0 1px 2px rgba(20,30,45,.06),0 4px 14px rgba(20,30,45,.08);
  --card-shadow-hover:0 2px 4px rgba(20,30,45,.08),0 10px 26px rgba(20,30,45,.14);
}
```

<!-- /TRASH 20260806-001 -->
<!-- TRASH id=20260806-002 date=2026-08-06 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Settings audit 2026-08-06: color theme reduction 12->5 per Scott request -- removed the corresponding 7 _UI_THEMES swatch entries (same removal as the CSS blocks)." -->
## 20260806-002 · 2026-08-06 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Settings audit 2026-08-06: color theme reduction 12->5 per Scott request -- removed the corresponding 7 _UI_THEMES swatch entries (same removal as the CSS blocks).  
**Payload:** `data/trash/files/20260806-002__snippet.txt`

```python
  {name:'purple',  label:'Dark Purple',   bg:'#0c0714', accent:'#9b5de5'},
  {name:'charcoal',label:'Warm Charcoal', bg:'#13100a', accent:'#e8b84a'},
  {name:'sakura',  label:'Sakura',        bg:'#140a10', accent:'#f4a7b9'},
  {name:'matcha',  label:'Matcha',        bg:'#0b120c', accent:'#8bc34a'},
  {name:'sunwashed',   label:'Sunwashed',     bg:'#fff8f0', accent:'#ba4e36'},
  {name:'mermaid',     label:'Mermaid Bright',bg:'#f0fbfa', accent:'#007d73'},
  {name:'clubroom',    label:'Clubroom Gold', bg:'#fffdf5', accent:'#916c08'},
  {name:'springvivid', label:'Spring Vivid',  bg:'#fbf7ff', accent:'#c4157f'},
```

<!-- /TRASH 20260806-002 -->
<!-- TRASH id=20260806-003 date=2026-08-06 kind=snippet source="tools/post_scheduled_coloring.py" reason="Broken: PACKS[pack] is a plain theme list not a {themes,style} dict, and generate_pack() does not exist in generate_coloring_pages.py -- TypeError crashed every scheduled run since this script was written. Replaced with the real per-theme loop main() actually uses." -->
## 20260806-003 · 2026-08-06 · snippet · `tools/post_scheduled_coloring.py`
**Reason:** Broken: PACKS[pack] is a plain theme list not a {themes,style} dict, and generate_pack() does not exist in generate_coloring_pages.py -- TypeError crashed every scheduled run since this script was written. Replaced with the real per-theme loop main() actually uses.  
**Payload:** `data/trash/files/20260806-003__snippet.txt`

```python
    # Generate full page set
    themes = gcp.PACKS[pack]["themes"]
    style_dna = gcp.PACKS[pack]["style"]
    generated_files = gcp.generate_pack(pack, themes, style_dna=style_dna)
```

<!-- /TRASH 20260806-003 -->
<!-- TRASH id=20260806-004 date=2026-08-06 kind=file source="tools/desktop/backend.spec" reason="Desktop app moved to a thin-client architecture (2026-08-06, Option A) -- BrowserWindow loads the live Railway deployment directly instead of a locally spawned backend, so there is no backend executable left to build a PyInstaller spec for." -->
## 20260806-004 · 2026-08-06 · file · `tools/desktop/backend.spec`
**Reason:** Desktop app moved to a thin-client architecture (2026-08-06, Option A) -- BrowserWindow loads the live Railway deployment directly instead of a locally spawned backend, so there is no backend executable left to build a PyInstaller spec for.  
**Payload:** `data/trash/files/20260806-004__backend.spec`

```
# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Frank's backend (tools/api_server/main.py), bundled as a
standalone executable for the desktop app (desktop/ Electron shell spawns this as a
child process). No pre-installed Python required on the end-user machine.

Build (must run ON the target OS -- PyInstaller does not cross-compile):
  python -m PyInstaller tools/desktop/backend.spec --distpath dist/desktop-backend

Why onedir, not onefile: main.py resolves sys.path.insert(0, ROOT / "tools") at import
time and imports sibling modules (daily_brief, trash, etc.) as bare names -- that only
works if tools/ exists as real files on disk next to the executable, which onedir mode
gives for free (the datas entry below copies the whole tools/ tree into the bundle).
onefile mode self-extracts to a temp dir per launch, which would also work but adds
startup latency and an extra temp-cleanup failure mode for no benefit here.

main.py itself has a matching frozen-detection branch (search `getattr(sys, "frozen"`)
that computes ROOT as the directory containing the frozen executable instead of walking
up from __file__, since __file__ for a frozen entry script doesn't sit 3 directories
under the repo root the way it does when run from source.
"""
from pathlib import Path

REPO_ROOT = Path(SPECPATH).resolve().parent.parent  # tools/desktop -> tools -> repo root
MAIN_PY = REPO_ROOT / "tools" / "api_server" / "main.py"

a = Analysis(
    [str(MAIN_PY)],
    pathex=[str(REPO_ROOT), str(REPO_ROOT / "tools"), str(REPO_ROOT / "tools" / "api_server")],
    binaries=[],
    datas=[
        # The whole tools/ tree (incl. tools/api_server/static/'s ~34MB vendor JS) as
        # real files on disk -- see the onedir rationale above. Harmless if this also
        # duplicates main.py's own source alongside the compiled entry script.
        (str(REPO_ROOT / "tools"), "tools"),
        # Read-mostly reference docs the CEO agent reads at runtime (business_standards.md,
        # ops_runbook.md, etc.) -- NOT the rest of data/ (staged_photos, digital_products,
        # backups, trash are large/gitignored/user-specific and don't belong in an installer).
        (str(REPO_ROOT / "data" / "knowledge_base"), "data/knowledge_base"),
        (str(REPO_ROOT / "data" / "dp_listing_map.json"), "data"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="frank-backend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # keep a console window for now -- makes startup errors visible
                   # during bring-up; Electron can hide it later once this is proven stable
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="frank-backend",
)
```

<!-- /TRASH 20260806-004 -->
<!-- TRASH id=20260806-005 date=2026-08-06 kind=file source="tools/desktop/build_backend.py" reason="Same thin-client architecture change as backend.spec -- this script built the now-unused local backend executable via PyInstaller." -->
## 20260806-005 · 2026-08-06 · file · `tools/desktop/build_backend.py`
**Reason:** Same thin-client architecture change as backend.spec -- this script built the now-unused local backend executable via PyInstaller.  
**Payload:** `data/trash/files/20260806-005__build_backend.py`

```
#!/usr/bin/env python3
"""
Builds the standalone Frank backend executable for the desktop app, using
tools/desktop/backend.spec. Must run ON the target OS -- PyInstaller does not
cross-compile a Windows .exe from Linux/Mac or vice versa. In practice this means:
  - Local runs (this script) only ever produce a binary for the OS you ran it on.
  - The real Windows .exe / Mac .app come from .github/workflows/build-desktop.yml's
    matrix build on windows-latest / macos-latest GitHub-hosted runners.

Run:  python tools/desktop/build_backend.py
Output: dist/desktop-backend/frank-backend/ (a directory -- onedir mode, see the
        spec's docstring for why onedir instead of onefile).
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SPEC = REPO_ROOT / "tools" / "desktop" / "backend.spec"
DIST = REPO_ROOT / "dist" / "desktop-backend"
BUILD = REPO_ROOT / "build" / "desktop-backend"


def main() -> int:
    cmd = [
        sys.executable, "-m", "PyInstaller",
        str(SPEC),
        "--distpath", str(DIST),
        "--workpath", str(BUILD),
        "--noconfirm",
    ]
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        return result.returncode
    out_dir = DIST / "frank-backend"
    print(f"\nBuilt: {out_dir}")
    print(f"Run it directly to test: {out_dir / 'frank-backend'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

<!-- /TRASH 20260806-005 -->
<!-- TRASH id=20260814-001 date=2026-08-14 kind=snippet source="tools/api_server/frank_hud_mockup.py" reason="Replaced the flat 5-theme system (default/light/ocean/kawaii/sunwashed) with a 2-axis 3-palette x 2-mode (dark/light) system (Studio Warm / Transformative Teal / Clubroom Contrast), per Scott (2026-08-14): change the color scheme, add a dark/light setting, 3 schemes x light+dark = 6 total. Archived before removal per the standing recycle-bin rule." -->
## 20260814-001 · 2026-08-14 · snippet · `tools/api_server/frank_hud_mockup.py`
**Reason:** Replaced the flat 5-theme system (default/light/ocean/kawaii/sunwashed) with a 2-axis 3-palette x 2-mode (dark/light) system (Studio Warm / Transformative Teal / Clubroom Contrast), per Scott (2026-08-14): change the color scheme, add a dark/light setting, 3 schemes x light+dark = 6 total. Archived before removal per the standing recycle-bin rule.  
**Payload:** `data/trash/files/20260814-001__snippet.txt`

```python
  /* Studio Warm — dark warm-plum surfaces, coral + gold accents (pulls the coral
     from the existing Sakura theme's palette and the gold already used site-wide
     for primary CTAs). --cyan/--cyan2 keep their legacy names for the ~300 existing
     usages across this file but now hold coral/blush values, not cyan — they were
     always "the accent hue," never literally required to be cyan. --panel3 is a new
     4th elevation level (toasts/dropdowns/overlays sit on this, one step lighter
     than --panel2) — dark-mode surfaces need at least 4 steps to read as depth
     without relying on box-shadow, which barely shows on dark backgrounds. */
  /* Brightened 2026-07-15 (Scott: "seems a little dark throughout") -- every
     surface step lifted ~4-6% lighter and --muted brightened for readability,
     verified against tools/color_contrast_check.py's WCAG math before shipping:
     text-on-bg 14.36:1 and muted-on-bg 7.12:1, both still comfortably above the
     4.5:1 AA floor (muted actually IMPROVED from 5.77:1 -- it was brightened more
     than the background was). */
     it here, the ambient shadow is a secondary cue. Overridden per-theme below
     only where a theme's surface treatment needs it (light theme gets a real
     drop shadow since it renders well on white). */
/* ── Color themes — full bg + panel + accent swap. Fonts/radius above are
   structural (declared once on :root) and apply under every theme unchanged;
   only surface/accent colors vary per theme, including each theme's own
   --panel3 elevation step. Card-shadow tokens likewise only need a per-theme
   override for the light theme (below); every dark-surfaced theme reuses the
   :root treatment since they all share the same "shadow barely shows" constraint. ── */
html.theme-light{
  --bg:#edf1f5;--panel:#ffffff;--panel2:#dde4ec;--panel3:#ffffff;--border:#d0d9e2;
  --cyan:#0a6878;--cyan2:#084f5e;--gold:#7a5c10;--gold2:#c4a035;
  --text:#1a2332;--muted:#3a5263;--green:#2a7a50;--red:#b03030;--amber:#c07a10;
html.theme-ocean{
  --bg:#07120f;--panel:#0d1d1a;--panel2:#132a26;--panel3:#1a3934;--border:#16312c;
  --cyan:#3ad6c8;--cyan2:#7ceee2;--gold:#f5b878;--gold2:#ffd0a0;
  --text:#e6f2f0;--muted:#6f948c;--green:#3dba7e;--red:#e05555;--amber:#e0a83a;
}
html.theme-kawaii{
  --bg:#0d0a1a;--panel:#161029;--panel2:#1f1638;--panel3:#281c47;--border:#241a42;
  --cyan:#00e5ff;--cyan2:#7cf3ff;--gold:#e040fb;--gold2:#f07cff;
  --text:#f0e6ff;--muted:#897bb6;--green:#3dba7e;--red:#e05555;--amber:#e0a83a;
}
/* 2026-07-18: bright/light-surfaced theme (Scott: "brighter colors but make sure
   text is readable") -- every text/muted/accent value below is verified against
   its actual bg AND panel2 (the more saturated surface a card can sit on) with
   tools/color_contrast_check.py's real WCAG math, same discipline as the
   2026-07-15 brightening pass above; nothing here is eyeballed. Reuses the light
   theme's card-shadow (real drop shadow reads correctly on a light surface,
   unlike the dark themes' inset-highlight trick above). Originally shipped
   alongside 3 siblings (Mermaid Bright, Clubroom Gold, Spring Vivid); those were
   cut in the 2026-08-06 12->5 theme reduction -- this one survived as the kept
   warm-light alternative to Day Mode. */
html.theme-sunwashed{
  --bg:#fff8f0;--panel:#ffffff;--panel2:#ffeee0;--panel3:#ffffff;--border:#f0d5b8;
  --cyan:#ba4e36;--cyan2:#8f3a28;--gold:#a46400;--gold2:#7a4b00;
  --text:#3a2418;--muted:#82644d;--green:#19824a;--red:#d6362b;--amber:#a46400;
```

<!-- /TRASH 20260814-001 -->
