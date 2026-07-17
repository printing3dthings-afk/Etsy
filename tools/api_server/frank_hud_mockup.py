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
`{}`) rendered by `render_frank_hud()` which substitutes business-identity placeholders
(%%AGENT_NAME%%/%%AGENT_SHORT%%/%%OWNER%%) at startup. Auth uses session cookies — the
APP_SECRET_TOKEN is never injected into the page source.
"""

import json

import business_config

_FRANK_HUD_MOCKUP = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<!-- maximum-scale=1/user-scalable=no removed 2026-07-08 (accessibility review, WCAG 1.4.4/1.4.10):
     blocking pinch/browser zoom locks out low-vision users entirely. fitStage() below no longer
     fights a deliberate zoom either — see the isMobileMode()/devicePixelRatio guard there. -->
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="%%AGENT_SHORT%%">
<meta name="theme-color" content="#070d16">
<link rel="manifest" href="/frank-manifest.webmanifest">
<link rel="apple-touch-icon" href="/static/apple-touch-icon.png">
<link rel="icon" type="image/png" href="/static/icon-192.png">
<title>%%AGENT_SHORT%% — Command Center</title>
<script type="importmap">
{"imports": {
  "onnxruntime-web": "/static/vendor/onnxruntime-web/ort.wasm.bundle.min.mjs",
  "three": "/static/vendor/three/build/three.module.js"
}}
</script>
<!-- Orb load speed (Scott, 2026-07-10): the default sphere's WebGL setup only
     starts fetching three.module.js (1.3MB) once the giant inline script below has
     been fully downloaded, parsed, and run down to resetOrbToDefault() -- on a real
     mobile connection that serializes ~2s of avoidable wait after tapping the Ask
     tab, even though the same file gets a 7-day Cache-Control (see _CachedStaticFiles
     in main.py) so this cost only applies to a cold cache. modulepreload starts the
     fetch in the background as soon as the HTML head parses, in parallel with
     everything else on the page, so most/all of it is already done by the time the
     user actually opens the orb screen. Three.js is loaded for every visit, not just
     phone (desktop shows the same default sphere), so this isn't scoped to mobile. -->
<link rel="modulepreload" href="/static/vendor/three/build/three.module.js">
<style>
/* ── Self-hosted display/body fonts (Studio Warm direction, 2026-07-09 visual
   upgrade). Latin-subset static WOFF2s, ~68KB total for all 4 files — served from
   /static/vendor/fonts/ with the existing vendor cache headers, not inlined, so
   this costs nothing on repeat visits. Fraunces is a headline/display face only
   (brand wordmark, panel/card titles) — deliberately NOT used for numbers, since
   its default figures are proportional oldstyle and won't line up in columns.
   Manrope carries everything else, including all numeric displays, which get
   font-variant-numeric:tabular-nums explicitly below. ──*/
@font-face{font-family:'Fraunces';font-weight:600;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/Fraunces-600.woff2') format('woff2')}
@font-face{font-family:'Manrope';font-weight:400;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/Manrope-400.woff2') format('woff2')}
@font-face{font-family:'Manrope';font-weight:600;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/Manrope-600.woff2') format('woff2')}
@font-face{font-family:'Manrope';font-weight:700;font-style:normal;font-display:swap;
  src:url('/static/vendor/fonts/Manrope-700.woff2') format('woff2')}

:root{
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
  --bg:#241c2e;--panel:#2d2438;--panel2:#372c42;--panel3:#42354e;--border:#3d3248;
  --cyan:#f2a0b5;--cyan2:#f7c3d0;--gold:#e4b155;--gold2:#f2cb8f;--text:#f5eef2;--muted:#bfa3b5;
  --green:#5cc48a;--red:#e2685f;--amber:#e8b868;

  --font-display:'Fraunces',Georgia,serif;
  --font-body:'Manrope',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  --r-sm:8px;--r-md:12px;--r-lg:16px;--r-pill:999px;

  /* Soft-depth card shadows (2026-07-17, Scott: "too many hard lines" — Phase 2).
     A dual highlight+shadow (the neumorphism technique) reads as a raised surface
     even on dark backgrounds, where a plain drop-shadow "barely shows" (see the
     --panel3 comment above) — the inset top highlight is what actually carries
     it here, the ambient shadow is a secondary cue. Overridden per-theme below
     only where a theme's surface treatment needs it (light theme gets a real
     drop shadow since it renders well on white). */
  --card-shadow:0 1px 0 rgba(255,255,255,.03) inset,0 2px 10px rgba(0,0,0,.16);
  --card-shadow-hover:0 1px 0 rgba(255,255,255,.05) inset,0 6px 18px rgba(0,0,0,.28);
}
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
  --card-shadow:0 1px 2px rgba(20,30,45,.06),0 4px 14px rgba(20,30,45,.08);
  --card-shadow-hover:0 2px 4px rgba(20,30,45,.08),0 10px 26px rgba(20,30,45,.14);
}
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
*{box-sizing:border-box;margin:0;padding:0}
/* Form-field focus glow (2026-07-17 Phase 3: "too many hard lines... make it flow
   more"). No global input/select/textarea rule existed at all — every field is
   styled ad hoc via inline style="" (border/radius/padding), so focus previously
   fell back to either the bare browser default outline or nothing. This is a
   plain low-specificity element selector: it only ADDS border-color/box-shadow/
   transition, properties none of the scattered inline styles already declare, so
   it layers on top of every existing field without fighting inline specificity
   or needing to touch any of them. Uses --gold2 (every theme's existing lighter/
   hover accent variant, already used for exactly this "softer highlight" role
   elsewhere e.g. .act-btn.primary:hover) as a SOLID ring color rather than a
   translucent color-mix() blend — verified live that color-mix(in srgb, var(--x)
   %, transparent) resolves to fully-transparent oklab(0 0 0/0) in this app's
   Chromium build (a real var()-inside-color-mix() interop bug, not a syntax
   error the browser reports), so a solid --gold2 ring is the correct, bulletproof
   choice here rather than debugging that further. The 3 pre-existing #chat-input-
   style ID rules (border-color:var(--gold) only, no glow) still apply too — same
   accent, this just adds the ring + smoothing everywhere else. */
input:focus,select:focus,textarea:focus{
  border-color:var(--gold);
  box-shadow:0 0 0 2px var(--gold2);
  transition:border-color .15s ease,box-shadow .15s ease;
  outline:none;
}
/* overflow:auto (not hidden) — at 105-145% browser zoom on a desktop-width window,
   the fixed 1440x900 stage's scale() can exceed the shrunk viewport before the
   880px mobile breakpoint kicks in; overflow:hidden clipped that content with no
   way to reach it. auto only shows scrollbars when something actually overflows,
   so normal (non-zoomed) rendering is unchanged (2026-07-08 accessibility review,
   WCAG 1.4.10 Reflow). */
html,body{height:100%;width:100%;overflow:auto;background:var(--bg)}
body{color:var(--text);font-family:var(--font-body);font-size:13px}

#stage-wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center;background:var(--bg)}
#stage{
  position:relative;width:1440px;height:900px;flex-shrink:0;transform-origin:center center;
  background:radial-gradient(ellipse at 50% -10%, #3d2a42 0%, var(--bg) 55%);
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
.hdr-logo .hex{width:30px;height:30px;border:2px solid var(--cyan);border-radius:var(--r-sm);display:flex;
  align-items:center;justify-content:center;color:var(--cyan2);font-size:15px;box-shadow:0 0 10px rgba(242,160,181,.5)}
.hdr-logo .lbl .l1{font-family:var(--font-display);font-weight:600;letter-spacing:1px;color:var(--cyan2);font-size:16px;line-height:1.1;
  text-shadow:0 0 10px rgba(242,160,181,.55)}
.hdr-logo .lbl .l2{font-size:8.5px;letter-spacing:2px;color:var(--muted)}

.hdr-bar{grid-column:2;grid-row:1;display:flex;align-items:center;justify-content:space-between;
  padding:0 20px;border-bottom:1px solid var(--border);background:rgba(8,16,26,.5)}
.status-pill{display:flex;align-items:center;gap:6px;font-size:10.5px;color:var(--green);
  border:1px solid rgba(76,175,130,.4);border-radius:var(--r-pill);padding:4px 10px;background:rgba(76,175,130,.08);
  letter-spacing:.5px;white-space:nowrap}
.status-pill .dot{width:6px;height:6px;border-radius:50%;background:var(--green);
  box-shadow:0 0 8px var(--green);animation:pulse 2s infinite;flex-shrink:0}
.status-pill.degraded{color:var(--amber);border-color:rgba(224,168,58,.4);background:rgba(224,168,58,.08)}
.status-pill.degraded .dot{background:var(--amber);box-shadow:0 0 8px var(--amber)}
.status-pill.error{color:var(--red);border-color:rgba(224,85,85,.4);background:rgba(224,85,85,.08)}
.status-pill.error .dot{background:var(--red);box-shadow:0 0 8px var(--red)}
.hdr-bar .clockwrap{text-align:center}
.hdr-bar .clockwrap .d{font-size:10px;color:var(--muted);letter-spacing:.5px}
.hdr-bar .clockwrap .t{font-size:17px;color:var(--cyan2);font-weight:700;letter-spacing:1px;font-variant-numeric:tabular-nums}
.hdr-bar .right{display:flex;align-items:center;gap:10px}
.search{width:230px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:6px 10px;color:var(--text);font-size:11px}
.hamburger-fixed{
  position:absolute;top:14px;left:14px;z-index:500;
  width:34px;height:34px;border-radius:var(--r-sm);border:1px solid var(--border);
  background:rgba(15,31,48,.85);color:var(--cyan2);font-size:15px;
  display:none;align-items:center;justify-content:center;cursor:pointer;
}
.hamburger-fixed:hover{border-color:var(--cyan)}
#orb-desktop-btn{color:var(--cyan2);border-color:rgba(242,160,181,.35);background:rgba(242,160,181,.06)}
#orb-desktop-btn:hover{border-color:var(--cyan);background:rgba(242,160,181,.14)}
.icon-btn{width:30px;height:30px;border-radius:var(--r-sm);border:1px solid var(--border);
  background:var(--panel);display:flex;align-items:center;justify-content:center;
  cursor:pointer;position:relative;color:var(--muted);font-size:13px;flex-shrink:0}
.icon-btn:hover{border-color:var(--cyan);color:var(--cyan2)}
.icon-btn:focus-visible,.operator:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.act-btn:focus-visible,.qc-btn:focus-visible,.hub-toggle-btn:focus-visible,.psheet-btn:focus-visible,
.hub-chip-btn:focus-visible,.lc-chip:focus-visible,[role="button"]:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.badge{position:absolute;top:-5px;right:-5px;background:var(--cyan);color:#06141f;
  font-size:9px;font-weight:700;border-radius:var(--r-sm);min-width:15px;height:15px;
  display:flex;align-items:center;justify-content:center;padding:0 3px}
.operator{display:flex;align-items:center;gap:7px;border:1px solid var(--border);border-radius:var(--r-pill);
  padding:3px 10px 3px 3px;background:var(--panel)}
.operator .av{width:24px;height:24px;border-radius:50%;background:linear-gradient(135deg,var(--gold),#8a6d2b);
  display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:700;color:#0a1420;flex-shrink:0}
.operator .ol1{font-size:11px;font-weight:600;line-height:1.1}
.operator .ol2{font-size:8.5px;color:var(--muted);letter-spacing:.5px}

/* ── Sidebar ── */
.sidebar{grid-column:1;grid-row:2;border-right:1px solid var(--border);background:rgba(8,16,26,.55);
  display:flex;flex-direction:column;padding:14px 10px;overflow-y:auto;
  scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.nav-section{font-size:9.5px;letter-spacing:1.5px;color:var(--muted);margin:12px 10px 6px;text-transform:uppercase}
.nav-section:first-child{margin-top:2px}
.nav-item{display:flex;align-items:center;gap:10px;padding:8px 12px;border-radius:var(--r-sm);
  cursor:pointer;color:var(--muted);font-size:12.5px;margin-bottom:2px;position:relative;
  transition:background .18s ease,color .18s ease,border-color .18s ease,transform .1s ease}
.nav-item .ic{width:16px;text-align:center;font-size:13px}
.nav-item:hover{background:var(--panel);color:var(--text)}
.nav-item:active{transform:scale(.98)}
.nav-item.active{background:linear-gradient(90deg,rgba(242,160,181,.18),transparent);
  color:var(--cyan2);border-left:2px solid var(--cyan)}
.nav-item .nbadge{margin-left:auto;background:var(--panel2);color:var(--cyan2);
  font-size:9.5px;font-weight:700;border-radius:var(--r-sm);padding:1px 7px;border:1px solid var(--border)}
.nav-item:focus-visible{outline:2px solid var(--cyan);outline-offset:-2px}
/* Real heading elements (2026-07-08 accessibility review) reuse the exact same visual
   rules as before — this reset stops browser default h1/h2 margin+size from touching
   layout. The tag changed, the look didn't. */
h1.hdr-title-h1{margin:0;font:inherit}
h2.nav-section-h2{margin:12px 10px 6px;font-size:9.5px;letter-spacing:1.5px;color:var(--muted);
  text-transform:uppercase;font-weight:400}

.voice-widget{margin-top:auto;border:1px solid var(--border);border-radius:var(--r-md);padding:14px 10px;
  background:var(--panel);text-align:center}
.voice-widget .vw-title{font-size:9.5px;letter-spacing:1.5px;color:var(--muted);margin-bottom:8px}

/* ── Main content — 3-column CSS grid (left 290px | chat 1fr | right 310px) ── */
.main{grid-column:2;grid-row:2;display:grid;grid-template-columns:290px 1fr 310px;gap:12px;padding:12px;overflow:hidden}
.col-left,.col-right{display:flex;flex-direction:column;gap:12px;min-height:0;overflow:hidden}
.col-center{display:flex;flex-direction:column;min-height:0;overflow:hidden}
.col-aicore{flex:0 0 auto}
.col-sysmon{flex:1;min-height:0}
.col-timeline{flex:0 0 auto;min-height:0}
.col-chat{flex:1;min-height:0;display:flex;flex-direction:column}
.col-shop{flex:0 0 auto}
.col-meminsights{flex:0 0 auto}
.col-agents{flex:1;min-height:0}
.col-feed{flex:1;min-height:0}

.panel{background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 14px;
  display:flex;flex-direction:column;overflow:hidden;min-height:0;
  box-shadow:var(--card-shadow);transition:box-shadow .2s ease}
.panel-title{font-size:10.5px;letter-spacing:1.5px;color:var(--cyan2);text-transform:uppercase;
  margin-bottom:8px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.panel-title .src{font-size:8.5px;color:var(--muted);text-transform:none;letter-spacing:0;font-weight:400}
.panel-title .lnk{font-size:9px;color:var(--cyan);text-transform:none;letter-spacing:0;cursor:pointer}
/* ── First-time-user simplification (2026-07-11): keep engineering/infra surfaces
   out of the everyday view. Nothing here is DELETED — it is CSS-hidden and fully
   reversible. A developer reveals it all with localStorage.frankDevMode='1', which
   adds .show-plumbing + .show-advanced to <body> (see the init by the welcome gate).
   IMPORTANT: .col-feed (Live Intelligence Feed) is only visually hidden, never
   removed from the DOM, because loadQueue() renders it AND drives the Approvals
   badge via setActionBadge(); removing it would break the approval count. Nav/mobile
   rows tagged data-tier="advanced" collapse under the Advanced disclosure. ── */
body:not(.show-plumbing) .panel-title .src{display:none}
body:not(.show-plumbing) #persist-warning{display:none !important}
body:not(.show-plumbing) #bb-relay,
body:not(.show-plumbing) .brief-wrap,
body:not(.show-plumbing) .col-aicore,
body:not(.show-plumbing) .col-sysmon,
body:not(.show-plumbing) .col-timeline,
body:not(.show-plumbing) .col-feed,
body:not(.show-plumbing) #orb-build-ver,
body:not(.show-plumbing) #settings-build-ver,
body:not(.show-plumbing) #studio-build-ver,
body:not(.show-plumbing) #system-status-pill{display:none}
body:not(.show-advanced) .nav-item[data-tier="advanced"],
body:not(.show-advanced) .more-row[data-tier="advanced"]{display:none}
.panel-body{overflow-y:auto;min-height:0;flex:1}


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

.orb-hero-stage{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;flex:1;width:100%}
canvas#orb{cursor:pointer}
/* canvas#orb-gl: the directly-visible WebGL sphere layer (2026-07-15, native-alpha
   rewrite). History of what NOT to retry here, condensed from 3 failed attempts:
   (1) A CSS mask-image alone only softens the canvas's outer square edge -- it can't
   fix an opaque interior (UnrealBloomPass's additive compositing doesn't preserve
   real per-pixel alpha to the final output, so a transparent clear still rendered
   fully opaque black).
   (2) Painting the theme's real --bg color into the WebGL clear color crossed
   UnrealBloomPass's bright-pass threshold (0.12) and blew the whole frame to white
   on any theme whose background luminance neared or exceeded that -- guaranteed on
   the light "Day Mode" theme (~0.9), borderline on the dark default theme (~0.12).
   (3) A JS luminance-key compositing hack (render offscreen, drawImage() it onto a
   second visible 2D canvas, then fake alpha via getImageData/putImageData) looked
   correct in local headless-Chromium screenshots but rendered as a torn/half-cut
   buffer on a real device -- the WebGLRenderer was never created with
   preserveDrawingBuffer:true, so a drawImage() read outside the render loop is not
   guaranteed to see a complete frame.
   ROOT FIX (this rewrite): all three trace back to EffectComposer/UnrealBloomPass's
   render-to-texture-then-composite pipeline, which does not preserve true per-pixel
   alpha to the final canvas -- a documented Three.js limitation, not something
   tunable away. initOrbGL() now does a single native glRenderer.render(glScene,
   glCamera) pass with a real transparent clear and no offscreen buffer, no readback,
   no second canvas. Native forward rendering with alpha:true correctly preserves
   real alpha straight to the canvas element -- it is specifically post-processing
   render-to-texture compositing that breaks it. Glow comes only from the CSS
   drop-shadow filter below, which traces this canvas's real alpha silhouette and was
   never implicated in any of the 3 failures above. Do not reintroduce
   EffectComposer/UnrealBloomPass for this element without addressing why it was
   removed here. */
canvas#orb-gl{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);cursor:pointer;display:none;
  -webkit-mask-image:radial-gradient(circle closest-side at 50% 50%,#000 88%,rgba(0,0,0,.45) 95%,transparent 100%);
  mask-image:radial-gradient(circle closest-side at 50% 50%,#000 88%,rgba(0,0,0,.45) 95%,transparent 100%);
}
.orb-overlay{position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);text-align:center;
  pointer-events:none;width:100%}
.orb-overlay .o1{font-family:var(--font-display);font-size:30px;font-weight:600;letter-spacing:6px;color:#fce9ee;
  text-shadow:0 0 18px rgba(247,195,208,.85),0 0 40px rgba(242,160,181,.5)}
.orb-overlay .o2{font-size:11px;letter-spacing:5px;color:var(--cyan2);margin-top:2px}
.orb-overlay .o3{font-size:9px;letter-spacing:2px;color:var(--muted);margin-top:8px}
.orb-state{margin-top:8px;font-size:10.5px;color:var(--muted);letter-spacing:1px}
.orb-hint{position:absolute;bottom:8px;font-size:9.5px;color:var(--muted);opacity:.6;letter-spacing:.5px}

#orb-view{
  position:absolute;inset:0;z-index:50;
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:radial-gradient(ellipse at 50% 40%, rgba(242,160,181,.10), transparent 60%);
}
/* Bumped 85vw->92vw to partly compensate for the camera pull-back (z=6.5) that now
   frames the full silhouette with margin: a slightly larger canvas keeps the on-screen
   orb from feeling small while still showing the whole uncut wavy edge. */
#orb-view canvas#orb,#orb-view canvas#orb-gl{width:min(92vw,660px);height:min(92vw,660px)}
/* Two stacked drop-shadows (tight bright core + wide soft diffusion) hugging the
   canvas's own alpha silhouette -- unlike a page-level background gradient, this
   halo follows the actual rendered sphere shape frame to frame, which is what
   makes it read as a glowing object floating in dark space (reference GIFs)
   rather than a flat sphere sitting on a colored page background. canvas#orb-gl
   now carries real native per-pixel alpha (2026-07-15 native-alpha rewrite), so
   this drop-shadow traces the actual wireframe silhouette directly. */
#orb-view canvas#orb-gl{filter:drop-shadow(0 0 46px rgba(96,220,255,.5)) drop-shadow(0 0 120px rgba(96,220,255,.22))}
#orb-view .orb-overlay .o1{font-size:36px}
#orb-view .orb-hint{position:static;margin-top:14px;opacity:.5}
#orb-view .orb-state{margin-top:10px}

body.cc-open #orb-view{display:none}
body:not(.cc-open) .hdr-logo,
body:not(.cc-open) .hdr-bar,
body:not(.cc-open) .sidebar,
body:not(.cc-open) .screen,
body:not(.cc-open) .bottombar{display:none}
body:not(.cc-open) .hamburger-fixed{display:flex !important;position:fixed;z-index:600}

.feed-item{padding:7px 0;border-bottom:1px solid var(--border);font-size:11px;color:var(--text);
  display:flex;justify-content:space-between;gap:6px}
.feed-item .ftxt{flex:1}
.feed-item .t{color:var(--muted);font-size:9px;margin-top:2px}
.feed-tag{font-size:8px;font-weight:700;letter-spacing:.5px;border-radius:5px;padding:1px 5px;flex-shrink:0;height:fit-content}
.feed-tag.info{background:rgba(242,160,181,.15);color:var(--cyan2)}
.feed-tag.warn{background:rgba(224,168,58,.15);color:var(--amber)}
.feed-tag.tip{background:rgba(76,175,130,.15);color:var(--green)}

.agents-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;flex:1}
.agent-tile{background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);
  padding:9px 10px;font-size:10.5px;display:flex;flex-direction:column;gap:5px}
.agent-tile .top{display:flex;align-items:center;gap:6px}
.agent-tile .ic{width:20px;height:20px;border-radius:6px;background:rgba(242,160,181,.15);
  display:flex;align-items:center;justify-content:center;font-size:11px;color:var(--cyan2);flex-shrink:0}
.agent-tile.idle .ic{background:rgba(93,120,145,.15);color:var(--muted)}
.agent-tile .name{font-weight:600;color:var(--text);font-size:10.5px;line-height:1.2}
.agent-tile .stat{color:var(--green);font-size:9.5px;display:flex;align-items:center;gap:4px}
.agent-tile .stat .d{width:5px;height:5px;border-radius:50%;background:var(--green)}
.agent-tile.idle .stat{color:var(--muted)}
.agent-tile.idle .stat .d{background:var(--muted)}

.inbox-msg-bar{display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid rgba(255,255,255,.05)}
.inbox-unread-badge{font-size:18px;font-weight:700;color:var(--cyan2);min-width:28px}
.inbox-unread-badge.urgent{color:var(--red)}
.inbox-msg-meta{font-size:11px;color:var(--muted);line-height:1.5}
.inbox-review{padding:7px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:11px}
.inbox-review:last-child{border-bottom:none}
.inbox-review-stars{color:var(--gold);letter-spacing:1px;font-size:13px}
.inbox-review-text{color:var(--muted);margin-top:2px;line-height:1.4}

.tl-item{display:flex;gap:9px;padding:6px 0;border-bottom:1px solid var(--border);font-size:11px}
.tl-item:last-child{border-bottom:none}
.tl-time{color:var(--cyan2);font-size:9.5px;width:48px;flex-shrink:0;line-height:1.3}
.tl-dotcol{display:flex;flex-direction:column;align-items:center;flex-shrink:0}
.tl-dotcol .d{width:7px;height:7px;border-radius:50%;background:var(--cyan);margin-top:3px}
.tl-txt .ttl{color:var(--text)}
.tl-txt .sub{color:var(--muted);font-size:9.5px}

.qc-btn{display:flex;align-items:center;gap:8px;width:100%;text-align:left;background:var(--panel2);
  border:1px solid var(--border);color:var(--text);border-radius:var(--r-sm);padding:8px 10px;margin-bottom:7px;
  font-size:11px;cursor:pointer}
.qc-btn:hover{border-color:var(--cyan)}
.qc-btn .qic{width:18px;height:18px;border-radius:50%;background:rgba(242,160,181,.18);color:var(--cyan2);
  display:flex;align-items:center;justify-content:center;font-size:10px;flex-shrink:0}

#toast-stack{position:fixed;top:16px;right:16px;z-index:9000;display:flex;flex-direction:column;
  gap:8px;max-width:340px;pointer-events:none}
.toast{background:var(--panel3);border:1px solid var(--border);border-radius:var(--r-md);padding:11px 14px;
  font-size:12.5px;color:var(--text);box-shadow:0 10px 28px rgba(0,0,0,.4);pointer-events:auto;
  border-left:3px solid var(--cyan);animation:toast-in .18s ease-out}
.toast.ok{border-left-color:var(--green)}
.toast.err{border-left-color:var(--red)}
.toast.info{border-left-color:var(--cyan)}
.toast.out{animation:toast-out .18s ease-in forwards}
@keyframes toast-in{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}
@keyframes toast-out{from{opacity:1;transform:translateY(0)}to{opacity:0;transform:translateY(-8px)}}

.alert-dropdown{position:absolute;top:38px;right:0;width:280px;max-width:calc(100vw - 24px);max-height:320px;overflow-y:auto;
  background:var(--panel3);border:1px solid var(--border);border-radius:var(--r-md);
  box-shadow:0 10px 28px rgba(0,0,0,.4);z-index:600;padding:8px;cursor:default;text-align:left}
/* 2026-07-15: max-width above was a defense-in-depth pass after the FIRST
   cc-open leak (syncMobileClass()'s resize/matchMedia race). Scott reported
   the dropdown "still not visible" after that shipped -- a SECOND,
   independent cc-open leak (phoneOpenScreen(), used by every mobile "More"
   list item and the "Create" tab) was still reachable. That leak is a
   legitimate part of how mobile views full desktop screens (Settings,
   Knowledge, etc. via More) though -- cc-open there also drives the actual
   .screen content becoming visible, so guarding it away entirely on mobile
   would break that navigation, not just hide the header bar. And even with
   max-width capping the BOX width, right:0 still anchors it to #bell-btn's
   own position, which sits wherever it lands in a cramped ~6-icon mobile
   header row -- capping width alone doesn't stop the box from starting past
   the left edge of the viewport if that anchor point is itself off-center.
   Fixed at the actual point of failure instead: on mobile, this dropdown is
   never positioned relative to the icon that opened it at all -- it's
   pinned directly to the viewport (below). */
body.is-mobile #alert-dropdown{
  position:fixed;top:calc(56px + env(safe-area-inset-top));
  left:8px;right:8px;width:auto;max-width:none;z-index:750;
}
.alert-dropdown-title{font-size:10.5px;letter-spacing:1.2px;color:var(--cyan2);text-transform:uppercase;
  padding:4px 6px 8px}
.alert-row{display:flex;flex-direction:column;gap:2px;padding:8px 9px;border-radius:var(--r-sm);
  background:var(--panel);border-left:3px solid var(--cyan);margin-bottom:6px;font-size:11.5px;
  color:var(--text);font-weight:400;text-transform:none;letter-spacing:normal}
.alert-row.critical{border-left-color:var(--red)}
.alert-row.warning{border-left-color:var(--amber)}
.alert-row .at{font-size:9px;color:var(--muted);margin-top:2px}

/* ── First-login spotlight tour — a scrim (#tour-click-catcher) blocks clicks
   outside the tour, #tour-spot is a zero-content box whose huge box-shadow both
   dims everything else on screen AND punches a "cutout" ring around the real
   target element (or, for target:null intro/outro steps, sits at 0x0 in the
   viewport center so the shadow just dims uniformly — same element, no branching
   markup). #tour-tooltip is the floating card with copy + controls. All three
   live inside #tour-root so one display toggle shows/hides the whole tour. ── */
#tour-root{display:none}
#tour-click-catcher{position:fixed;inset:0;z-index:9599;background:transparent}
#tour-spot{position:fixed;z-index:9600;border-radius:10px;pointer-events:none;
  box-shadow:0 0 0 9999px rgba(5,9,16,.82),0 0 0 2px var(--gold);
  transition:left .3s ease,top .3s ease,width .3s ease,height .3s ease}
#tour-tooltip{position:fixed;z-index:9601;background:var(--panel);border:1px solid var(--border);
  border-radius:var(--r-lg);padding:18px 20px;width:320px;max-width:calc(100vw - 32px);
  box-shadow:0 20px 60px rgba(0,0,0,.5);transition:left .3s ease,top .3s ease}
.tour-step-title{font-size:15px;font-weight:700;color:var(--gold);margin-bottom:8px}
.tour-step-body{font-size:12.5px;color:var(--text);line-height:1.5;margin-bottom:12px}
.tour-step-body p{margin:0 0 8px}
.tour-step-body p:last-child{margin-bottom:0}
.tour-dots{display:flex;gap:5px;margin-bottom:12px}
.tour-dots .dot{width:6px;height:6px;border-radius:50%;background:var(--border)}
.tour-dots .dot.active{background:var(--gold)}
.tour-controls{display:flex;align-items:center;justify-content:space-between;gap:8px}
.tour-controls .tour-skip{background:none;border:none;color:var(--muted);font-size:12px;cursor:pointer;padding:6px 4px}
.tour-controls .tour-btns{display:flex;gap:8px}
.tour-controls button.tour-nav-btn{background:var(--panel2);color:var(--text);border:1px solid var(--border);
  border-radius:var(--r-md);padding:8px 14px;font-size:12.5px;font-weight:600;cursor:pointer}
.tour-controls button.tour-nav-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.tour-controls button.tour-nav-btn:disabled{opacity:.35;cursor:default}

.dep-pill-row{display:flex;flex-direction:column;gap:8px;flex:1;min-height:0;overflow-y:auto;justify-content:flex-start}
.dep-pill{display:flex;align-items:center;gap:8px;background:var(--panel2);border:1px solid var(--border);
  border-radius:var(--r-sm);padding:7px 10px}
.dep-pill .dep-dot{width:8px;height:8px;border-radius:50%;flex-shrink:0;background:var(--green);
  box-shadow:0 0 6px var(--green)}
.dep-pill.open .dep-dot{background:var(--red);box-shadow:0 0 6px var(--red)}
.dep-pill.half_open .dep-dot{background:var(--amber);box-shadow:0 0 6px var(--amber)}
.dep-pill .dep-name{font-size:11px;color:var(--text);flex:1}
.dep-pill .dep-state{font-size:9.5px;color:var(--green);letter-spacing:.4px;text-transform:uppercase}
.dep-pill.open .dep-state{color:var(--red)}
.dep-pill.half_open .dep-state{color:var(--amber)}
.dep-pill .dep-fail{font-size:9px;color:var(--muted)}


.ss-status{font-size:11px;font-weight:700;letter-spacing:.04em;padding:3px 8px;border-radius:var(--r-md);display:inline-block;margin-bottom:8px}
.ss-status.on_track{background:rgba(42,170,100,.18);color:var(--green)}
.ss-status.building{background:rgba(196,160,53,.18);color:var(--gold)}
.ss-status.at_risk{background:rgba(200,60,60,.18);color:var(--red)}
.ss-row{display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:11px}
.ss-row:last-child{border-bottom:none}
.ss-label{color:var(--muted)}
.ss-val{font-weight:600;color:var(--text);font-variant-numeric:tabular-nums}
.ss-bar-wrap{height:4px;background:var(--panel2);border-radius:2px;flex:1;margin:0 8px;min-width:40px}
.ss-bar{height:4px;border-radius:2px;background:var(--green);transition:width .4s}
.ss-bar.warn{background:var(--amber)}
.ss-bar.bad{background:var(--red)}

.shop-spark-row{display:flex;gap:8px;flex:1;min-height:0;overflow-y:auto;flex-wrap:wrap}
.shop-spark-card{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);
  padding:6px 8px;display:flex;flex-direction:column;gap:1px;min-height:0;overflow:hidden}
.shop-spark-card .ssc-lab{font-size:9px;color:var(--muted);letter-spacing:.4px}
.shop-spark-card .ssc-valrow{display:flex;align-items:baseline;justify-content:space-between;gap:6px}
.shop-spark-card .ssc-val{font-size:13px;font-weight:700;color:var(--cyan2)}
.shop-spark-card .ssc-delta{font-size:8.5px;flex-shrink:0}
.shop-spark-card .ssc-spark{flex:1;min-height:0}

.shop-chip-row{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:6px;flex-shrink:0}
.shop-chip{background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-sm);padding:5px 7px;
  display:flex;flex-direction:column;gap:3px;justify-content:center}
.shop-chip .nm{font-size:9px;color:var(--muted);letter-spacing:.3px}
.shop-chip .v{font-size:12.5px;font-weight:700;color:var(--text)}

.recent-sale-row{display:flex;justify-content:space-between;align-items:center;padding:4px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:11px}
.recent-sale-row:last-child{border-bottom:none}
.recent-sale-amt{color:var(--green);font-weight:600}
.recent-sale-date{color:var(--muted);font-size:10px}

/* Studio tab placeholder */
.studio-grid{display:flex;gap:14px;height:100%}
video{width:100%;border-radius:var(--r-md);background:#000;display:block}
.studio-list-item{padding:8px;border:1px solid var(--border);border-radius:var(--r-sm);margin-bottom:6px;font-size:11px}


/* Bottom bar */
.bottombar{grid-column:1/3;grid-row:3;border-top:1px solid var(--border);background:rgba(8,16,26,.6);
  display:flex;align-items:center;justify-content:space-between;padding:0 18px;font-size:10.5px;color:var(--muted)}
.bb-left{display:flex;align-items:center;gap:16px}
.bb-left .it{display:flex;align-items:center;gap:5px}
.bb-center{display:flex;align-items:center;gap:14px;flex:1;justify-content:center}
.dots-line{flex:1;max-width:200px;height:1px;background:repeating-linear-gradient(90deg,var(--cyan) 0 4px,transparent 4px 9px);opacity:.5}
.talk-pill{display:flex;flex-direction:column;align-items:center;gap:2px;background:var(--panel);
  border:1px solid rgba(242,160,181,.4);border-radius:var(--r-pill);padding:6px 22px;cursor:pointer;
  box-shadow:0 0 16px rgba(242,160,181,.15)}
.talk-pill .row1{display:flex;align-items:center;gap:10px}
.talk-pill .label{color:var(--cyan2);font-weight:700;letter-spacing:1.5px;font-size:11px}
.talk-pill .sub{font-size:9px;color:var(--muted);letter-spacing:.5px}
.mini-wave{display:flex;align-items:center;gap:2px;height:13px}
.mini-wave span{width:2px;background:var(--cyan);border-radius:1px;animation:wave 1s ease-in-out infinite}
.brief-btn{background:var(--panel);border:1px solid var(--border);color:var(--cyan2);
  border-radius:var(--r-sm);padding:6px 14px;font-size:10.5px;cursor:pointer;white-space:nowrap}

@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
@keyframes wave{0%,100%{height:4px}50%{height:16px}}

.screen{display:none;grid-column:2;grid-row:2;overflow:hidden;padding:12px}
/* Screen-switch motion (2026-07-17, Scott: "too many hard lines... make it flow
   more"). Was a bare display:none->block cut with zero animation anywhere in the
   switch path (showScreen()/phoneOpenScreen() just toggle .active) -- the single
   biggest reason navigating Frank felt abrupt rather than fluid. `animation`
   (not `transition`) is required here: transitions can't interpolate from
   display:none since there's no starting frame to animate from, but a
   newly-applied @keyframes animation fires correctly the instant an element
   goes from none->block. Fires once per screen switch (only when .active is
   freshly added to a *different* element), not on resize/reflow. Silenced
   under reduced motion below alongside the other decorative animations. */
@keyframes screen-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}
.screen.active{display:block;animation:screen-in .26s cubic-bezier(.22,1,.36,1) both}

/* ── Live Chat screen — ported from the live Hub's #chat-wrap at / (main.py), same
   /ws/chat backend, same CHAT_SESSION scheme, restyled to the HUD's cyan/gold theme. ── */
#chat-msgs{flex:1;overflow-y:auto;min-height:0;padding:2px 2px 10px;display:flex;flex-direction:column;gap:10px}
.lc-bubble{max-width:78%;padding:10px 14px;border-radius:var(--r-lg);font-size:13px;line-height:1.5;word-break:break-word}
.lc-bubble.user{align-self:flex-end;background:var(--gold);color:#0D1B2A;border-bottom-right-radius:4px}
.lc-bubble.bot{align-self:flex-start;background:var(--panel2);border:1px solid var(--border);border-bottom-left-radius:4px;white-space:pre-wrap;color:var(--text)}
.lc-bubble.typing{color:var(--muted);font-style:italic}
.lc-chips{display:flex;gap:8px;flex-wrap:wrap;padding:8px 2px;flex-shrink:0;border-top:1px solid var(--border)}
.lc-chip{padding:7px 14px;border-radius:var(--r-pill);border:1px solid var(--border);background:var(--panel2);color:var(--muted);font-size:12px;cursor:pointer;white-space:nowrap}
.lc-chip:active{border-color:var(--gold);color:var(--gold)}
.lc-input-row{display:flex;gap:8px;padding:10px 2px 0;border-top:1px solid var(--border);flex-shrink:0}
#chat-input{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-pill);padding:10px 16px;color:var(--text);font-size:14px;outline:none}
#chat-input:focus{border-color:var(--gold)}
#chat-send{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#chat-send svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
/* Phone "Ask" tab (#orb-view) has no chat transcript, just the orb -- so Scott can
   still type to %%AGENT_SHORT%% even when voice isn't practical (loud room, no mic
   permission, etc). Same #chat-input/#chat-send visual treatment, own IDs since a
   duplicate #chat-input would break every getElementById('chat-input') call above. */
.orb-input-row{display:flex;gap:8px;width:min(85vw,420px);margin-top:14px}
#orb-chat-input{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-pill);padding:10px 16px;color:var(--text);font-size:14px;outline:none}
#orb-chat-input:focus{border-color:var(--gold)}
#orb-chat-send{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
#orb-chat-send svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
/* One-tap route from the Ask/orb view into the full chat transcript (the page Scott
   wanted directly reachable). Mobile affordance only — on desktop the Home screen
   already IS the chat, so it's hidden there. Stays visible inside the mobile
   "Talk to Frank" popup (unlike .orb-input-row, which the popup hides). */
.orb-open-chat{margin-top:16px;background:linear-gradient(90deg,rgba(242,160,181,.22),rgba(96,220,255,.14));border:1px solid var(--border);color:var(--text);border-radius:var(--r-pill);padding:12px 26px;font-size:14px;font-weight:600;cursor:pointer;letter-spacing:.3px}
.orb-open-chat:hover{filter:brightness(1.14)}
.orb-open-chat:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
body:not(.is-mobile) .orb-open-chat{display:none}

/* ── Hub screens (Listings/Products/Brand Kit/Files/Connections/Security) — ported
   verbatim-in-behavior from the live Hub at / (main.py), restyled to the HUD's
   cyan/gold theme. Classes are namespaced "hub-" since the HUD already has its own
   unrelated .badge (notification dot) that would collide with the live Hub's .badge
   (listing state pill). ── */
.hub-scroll{margin-top:10px;overflow-y:auto;max-height:760px}
.hub-section-title{font-size:11px;font-weight:700;color:var(--muted);text-transform:uppercase;letter-spacing:.8px;margin:16px 0 8px}
.hub-section-title:first-child{margin-top:0}
.hub-card{background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:14px;margin-bottom:12px;
  box-shadow:var(--card-shadow);transition:box-shadow .2s ease}
.hub-card:hover{box-shadow:var(--card-shadow-hover)}
/* .create-choice has no base rule of its own — every use sets background/border/
   radius/padding inline (Create screen tile grid), so this ADDS the soft-depth
   treatment on top without touching ~19 existing inline attributes: box-shadow
   and transform are properties none of those inline styles declare, so nothing
   here gets overridden by the higher-specificity inline style. The lift-on-hover
   (this is the one card class marked role="button") affirms it's tappable —
   the same "press responds" language as Phase 1's nav tap feedback. */
.create-choice{box-shadow:var(--card-shadow);
  transition:box-shadow .2s ease,transform .15s cubic-bezier(.22,1,.36,1)}
.create-choice:hover{box-shadow:var(--card-shadow-hover);transform:translateY(-2px)}
.create-choice:active{transform:translateY(0) scale(.98)}
.hub-empty{text-align:center;color:var(--muted);padding:40px 0;font-size:13px}
.hub-spinner{display:block;width:20px;height:20px;border:2px solid var(--border);border-top-color:var(--gold);border-radius:50%;animation:hubspin .7s linear infinite;margin:40px auto}
@keyframes hubspin{to{transform:rotate(360deg)}}

.hub-toggle-row{display:flex;gap:8px;margin-bottom:12px}
.hub-toggle-btn{flex:1;padding:8px;border-radius:var(--r-sm);border:1px solid var(--border);background:none;color:var(--muted);font-size:13px;font-weight:600;cursor:pointer;transition:all .15s}
.hub-toggle-btn.active{background:var(--gold);color:#06141f;border-color:var(--gold)}
.hub-chip-row{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap}
.hub-chip-btn{padding:6px 12px;border-radius:var(--r-pill);border:1px solid var(--border);background:none;color:var(--muted);font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap}
.hub-chip-btn.active{background:var(--gold);color:#06141f;border-color:var(--gold)}

.hub-listing-item{display:flex;align-items:center;gap:12px;padding:12px 0;border-bottom:1px solid var(--border);
  transition:background-color .15s ease}
.hub-listing-item:last-child{border-bottom:none}
/* 59 uses, virtually all role="button" + onclick (toggle detail, open file, expand
   a ZIP group) — but had zero hover/press feedback at all (2026-07-17 Phase 3:
   "too many hard lines... make it flow more"). Edge-to-edge tint, no radius —
   these rows are stacked flush against a straight border-bottom divider, so a
   rounded corner would cut oddly against that line; edge-to-edge is also the
   native list-row convention (iOS/Android settings rows highlight this way). */
.hub-listing-item:hover{background:var(--panel3)}
.hub-listing-item:active{background:var(--panel3)}
.hub-thumb{width:52px;height:52px;border-radius:var(--r-sm);object-fit:cover;background:var(--border);flex-shrink:0}
.hub-thumb-ph{width:52px;height:52px;border-radius:var(--r-sm);background:var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:20px}
.hub-listing-info{flex:1;min-width:0}
.hub-listing-title{font-family:var(--font-display);font-size:14px;font-weight:600;color:var(--text);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.hub-listing-meta{font-size:11px;color:var(--muted);margin-top:2px}
.hub-listing-price{font-size:14px;font-weight:700;color:var(--gold);flex-shrink:0}
.hub-lstate{display:inline-block;font-size:10px;font-weight:600;padding:2px 7px;border-radius:var(--r-pill);margin-left:6px}
.hub-lstate.draft{background:#0f1f30;color:var(--muted);border:1px solid var(--border)}
.hub-lstate.active{background:#143323;color:var(--green);border:1px solid #1f4d36}

.hub-listing-detail{padding:2px 14px 12px;margin:-2px 0 10px;background:var(--panel);border:1px solid var(--border);border-top:none;border-radius:0 0 10px 10px;font-size:12px}
.hub-listing-detail .hub-drow{display:flex;justify-content:space-between;gap:10px;padding:6px 0;border-bottom:1px solid var(--border)}
.hub-listing-detail .hub-drow:last-child{border-bottom:none}
.hub-listing-detail .hub-drow span{color:var(--muted)}
.hub-listing-detail .hub-drow b{font-weight:600;text-align:right}

.hub-act-btn{flex:1;text-align:center;padding:7px;border-radius:var(--r-sm);font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}

.hub-swatch{display:inline-block;width:16px;height:16px;border-radius:4px;vertical-align:middle;margin-right:4px;flex-shrink:0;border:1px solid rgba(255,255,255,.15)}
.hub-prod-card{background:var(--panel2);border:1px solid var(--border);border-left-width:4px;border-radius:var(--r-md);padding:13px 14px;margin-bottom:10px}

.hub-cred-row{display:flex;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid var(--border);flex-wrap:wrap}
.hub-cred-row:last-child{border-bottom:none}
.hub-cred-dot{width:10px;height:10px;border-radius:50%;flex-shrink:0}

.hub-posture-row{display:flex;align-items:center;gap:10px;padding:9px 0;border-bottom:1px solid var(--border)}
.hub-posture-row:last-child{border-bottom:none}

/* ── Action Center — ported from the live Hub's Action Center at / (main.py); the
   approve/reject queue is the human-in-the-loop safety gate for Etsy writes and local
   file/exec actions. Namespaced "act-" — new concept, no existing HUD equivalent. ── */
.section-title{font-size:13px;font-weight:600;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;margin:16px 0 8px}
.act-card{background:var(--panel2);border:1px solid var(--border);border-left-width:4px;border-radius:var(--r-md);padding:13px 14px;margin-bottom:10px;
  box-shadow:var(--card-shadow);transition:box-shadow .2s ease}
.act-card:hover{box-shadow:var(--card-shadow-hover)}
.act-card.high{border-left-color:var(--red)}
.act-card.medium{border-left-color:var(--gold)}
.act-card.low{border-left-color:#4a6b8a}
.act-card.approval{border-left-color:var(--green);background:#13241c}
.act-sev{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;padding:2px 7px;border-radius:var(--r-md)}
.act-sev.high{background:#2d1a1a;color:#e07070}
.act-sev.medium{background:#2d2a1a;color:var(--gold2)}
.act-sev.low{background:#1a2330;color:#7ba0c2}
.act-sev.approval{background:#13241c;color:#5fcf9e;border:1px solid #2d5a44}
.act-title{font-family:var(--font-display);font-size:15px;font-weight:600;margin:7px 0 4px;line-height:1.35;color:var(--text)}
.act-detail{font-size:12px;color:var(--muted);line-height:1.45}
.act-sug{font-size:12px;color:var(--text);margin-top:7px;padding-top:7px;border-top:1px solid var(--border)}
.act-sug b{color:var(--gold2);font-weight:600}
.act-btns{display:flex;gap:8px;margin-top:9px}
/* ── Button hierarchy (2026-07-09 visual upgrade): .act-btn/.hub-act-btn's bare
   form is now explicitly the TERTIARY/ghost tier (Cancel, secondary nav links).
   .primary = the one filled CTA per panel (Save/Add/Upload/Download/Post — the
   action that commits something). .secondary = soft-filled, one step up from
   ghost, for supporting-but-real actions (toggle state, view details, retry).
   .danger = destructive actions, red-tinted, secondary weight (never filled —
   destructive + primary-filled together reads as "encouraged," which delete
   actions should never be). .approve/.reject predate this pass and already
   nail the semantic-color pattern for the one place it was already correct
   (the staged-action review flow) — left as-is. ──*/
.act-btn,.hub-act-btn{transition:background-color .15s ease,border-color .15s ease,color .15s ease,transform .1s ease}
.act-btn:active,.hub-act-btn:active{transform:scale(.97)}
.act-btn{flex:1;text-align:center;padding:7px;border-radius:var(--r-sm);font-size:12px;font-weight:600;cursor:pointer;border:1px solid var(--border);background:none;color:var(--muted);text-decoration:none}
.act-btn.primary,.hub-act-btn.primary{background:var(--gold);color:#0D1B2A;border-color:var(--gold)}
.act-btn.primary:hover,.hub-act-btn.primary:hover{background:var(--gold2);border-color:var(--gold2)}
.act-btn.secondary,.hub-act-btn.secondary{background:var(--panel2);border-color:var(--cyan);color:var(--cyan2)}
.act-btn.secondary:hover,.hub-act-btn.secondary:hover{background:var(--panel3)}
.act-btn.danger,.hub-act-btn.danger{background:none;border-color:#5a2d3a;color:#e0808f}
.act-btn.danger:hover,.hub-act-btn.danger:hover{background:rgba(224,104,95,.12)}
.act-btn.approve{background:var(--green);color:#06140d;border-color:var(--green)}
.act-btn.reject{color:#e08585;border-color:#5a2d2d}
.metric{background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:14px}
.metric .value{font-size:24px;font-weight:700;color:var(--text);font-variant-numeric:tabular-nums}
.metric .sub{font-size:11px;color:var(--muted);margin-top:2px}
.empty{text-align:center;color:var(--muted);padding:40px 0;font-size:14px}

/* ══════════ MOBILE LAYOUT — fluid stage, stacked inline sidebar nav, stacked rows ══════════
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
  .hamburger-fixed{
    display:flex;
    position:fixed;
    top:calc(10px + env(safe-area-inset-top));
    left:calc(10px + env(safe-area-inset-left));
  }
  #orb-desktop-btn{display:none}

  .hdr-bar{padding:0 10px;gap:8px}
  .hdr-bar .search,.hdr-bar .clockwrap{display:none}

  .sidebar{
    position:static;width:100%;max-width:none;z-index:auto;
    grid-column:1/-1;grid-row:auto;
    transform:none;transition:none;box-shadow:none;
    padding:10px;
    padding-top:calc(10px + env(safe-area-inset-top));
  }

  .main{grid-column:1/-1;display:flex;flex-direction:column;grid-template-columns:none;overflow:visible !important;height:auto !important;padding:10px}
  .screen{grid-column:1/-1;height:auto;overflow:visible;padding:10px}
  .panel{overflow:visible !important}
  .panel-body{overflow:visible !important;max-height:none !important;flex:none !important}

  .col-left,.col-center,.col-right{overflow:visible;gap:10px}
  .col-center{order:-1}
  .col-left{order:0}
  .col-right{order:1}
  .col-left .panel,.col-right .panel{overflow:visible}
  .col-left .panel-body,.col-right .panel-body,.dep-pill-row,.shop-spark-row{
    overflow:visible;max-height:none;flex:none
  }
  .col-aicore,.col-sysmon,.col-timeline,.col-chat,.col-shop,.col-meminsights,.col-agents,.col-feed{
    flex:none !important;width:100% !important
  }

  #chat-msgs{min-height:280px;max-height:60vh;flex:none}
  .orb-hero-stage{min-height:220px}

  .agents-grid{grid-template-columns:repeat(2,1fr)}

  #tasks-list,#actions-content,#calendar-content,#memory-content,#conversations-content,
  #kb-content,#tools-list,#workflows-content,.hub-scroll,#studio-videos-list{
    max-height:none !important;overflow:visible !important;
  }

  .nav-item{padding:14px;font-size:14px}
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
#persist-warning{position:fixed;top:0;left:0;right:0;z-index:99999;display:none;
  background:#7a1a00;color:#ffd9c2;font-size:13px;font-weight:600;line-height:1.4;
  padding:9px 16px;padding-top:calc(9px + env(safe-area-inset-top));text-align:center;border-bottom:2px solid #ff5a1f;
  box-shadow:0 2px 12px rgba(0,0,0,.5);font-family:var(--font-body)}
#persist-warning b{color:#fff}
#persist-warning.show{display:flex;align-items:flex-start;gap:10px}
#persist-warning .pw-txt{flex:1}
#persist-warning-x{flex:none;background:rgba(255,255,255,.15);border:none;color:#fff;
  font-size:15px;line-height:1;width:28px;height:28px;border-radius:50%;cursor:pointer;
  display:grid;place-items:center;margin-top:-2px}
#persist-warning-x:active{background:rgba(255,255,255,.3)}

/* ══ Phone Mode — dedicated 4-tab bottom shell (mobile only; desktop untouched) ══
   Everything is gated behind body.is-mobile and styled through the existing theme
   custom properties (--panel/--border/--cyan2/--red/--muted…) so the user's chosen
   color theme (light/purple/charcoal/sakura/matcha/ocean/kawaii) recolors it too. */
#phone-tabbar{display:none}
body.is-mobile #phone-tabbar{
  display:flex;position:fixed;left:0;right:0;bottom:0;z-index:700;
  background:var(--panel);border-top:1px solid var(--border);
  padding:6px 4px calc(6px + env(safe-area-inset-bottom));
}
body.is-mobile #phone-tabbar .ptab{
  flex:1;background:none;border:none;cursor:pointer;color:var(--muted);font-family:inherit;
  display:flex;flex-direction:column;align-items:center;gap:3px;
  font-size:10.5px;font-weight:600;padding:6px 2px;position:relative;
  transition:color .18s ease,transform .1s ease;
}
body.is-mobile #phone-tabbar .ptab:active{transform:scale(.92)}
body.is-mobile #phone-tabbar .ptab .pti{font-size:19px;line-height:1;display:inline-block;
  transition:transform .22s cubic-bezier(.34,1.56,.64,1)}
body.is-mobile #phone-tabbar .ptab.on{color:var(--cyan2)}
body.is-mobile #phone-tabbar .ptab.on .pti{transform:scale(1.14)}
body.is-mobile #phone-tabbar .ptab:focus-visible{outline:2px solid var(--cyan);outline-offset:2px;border-radius:var(--r-sm)}
body.is-mobile #phone-tabbar .ptab .pcnt{
  position:absolute;top:-1px;right:calc(50% - 20px);background:var(--red);color:#fff;
  font-size:9.5px;font-weight:800;min-width:15px;height:15px;border-radius:var(--r-sm);
  display:none;align-items:center;justify-content:center;padding:0 4px;
}
/* the floating hamburger + desktop bottom bar are replaced by the tab bar on phone */
body.is-mobile .hamburger-fixed{display:none !important}
body.is-mobile .bottombar{display:none}
/* leave room so the fixed tab bar never covers content — must exceed the bar height
   (58px + safe-area). The last control (e.g. Studio's Generate Video button) has to be
   able to scroll fully above the bar to be tappable. */
body.is-mobile .main,body.is-mobile .screen{padding-bottom:calc(80px + env(safe-area-inset-bottom)) !important}
/* Floating "back to top" — 2026-07-15: any page/panel long enough to scroll (the
   176-product Products list, a long Listings/Approvals queue, etc.) gets this once
   scrolled past a threshold. Sits just above the phone tab bar (58px + safe-area,
   see above) so it never overlaps it. Naturally never appears on desktop without any
   extra gating: the fixed 1440x900 stage there uses per-panel internal scrolling
   (.screen{overflow:hidden}), so neither of the two real scroll sources below ever
   fires there — see the JS logic further down for exactly what those two sources
   are (document.body, not window -- a same-day live-confirmed fix, see its comment
   for why). */
#back-to-top-btn{display:none;position:fixed;z-index:750;
  right:calc(14px + env(safe-area-inset-right));
  bottom:calc(74px + env(safe-area-inset-bottom));
  width:42px;height:42px;border-radius:50%;align-items:center;justify-content:center;
  background:var(--gold);color:#0D1B2A;border:none;font-size:18px;font-weight:700;
  cursor:pointer;box-shadow:0 4px 14px rgba(0,0,0,.35)}
#back-to-top-btn.show{display:flex}
#back-to-top-btn:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
/* "Talk to Frank" popup (mobile only) — #orb-view is no longer permanent Ask-tab
   content, it's a dedicated full-screen popup toggled by body.frank-popup-open,
   opened by the Ask tab only (see phoneTab()/openFrankPopup() in the script —
   the top-right hamburger opens a separate, much smaller text-only popup below,
   2026-07-10 correction). Deliberately decoupled from the desktop body.cc-open
   control-center toggle so phone popup state never fights desktop control-center
   state. */
body.is-mobile #orb-view{display:none}
body.is-mobile.frank-popup-open #orb-view{
  display:flex !important;position:fixed;inset:0;z-index:750;
  /* Bumped from 24px (Scott, 2026-07-10): the tab bar is visible again over the
     bottom of this screen -- needs the same ~80px clearance other phone panels use
     (see .main,.screen rule above) so centered orb content doesn't sit under it. */
  padding-bottom:calc(84px + env(safe-area-inset-bottom));
  padding-top:env(safe-area-inset-top);
  /* #orb-view's own background (further up this file) is a translucent radial
     gradient designed for the desktop view, where it always sits over the fixed
     1440x900 stage -- on phone it let the tab bar visibly bleed through underneath
     (z-index alone doesn't hide a transparent element's background). Solid here so
     "full-screen overlay" (Scott's choice) actually reads as full-screen. */
  background:var(--bg);
  /* "Lock in position" (Scott, 2026-07-10): the orb's own idle animation should
     keep running, but the screen itself must not scroll or rubber-band -- iOS
     Safari/PWA can still pan a position:fixed element's underlying page via touch
     even though the element itself never "scrolls" in the CSS sense. touch-action
     is pinch-zoom (not none, Scott 2026-07-10 follow-up) so the pinch gesture still
     works -- pinch-zoom explicitly enables zooming while still blocking panning. */
  overflow:hidden;overscroll-behavior:none;touch-action:pinch-zoom;
}
/* Declutter (Scott, 2026-07-10): keep just the orb + "Frank / COMMAND CENTER" on
   the phone popup -- the build version and the "IDLE…"/hint technical text go.
   Desktop is untouched (no body.is-mobile scoping there). */
body.is-mobile.frank-popup-open #orb-build-ver,
body.is-mobile.frank-popup-open .orb-state,
body.is-mobile.frank-popup-open .orb-hint{display:none}
/* Second chat field removed (Scott, 2026-07-10): the orb screen's own input row
   duplicated the hamburger's quick-chat popup -- on phone, the hamburger popup is
   the only text entry point. Desktop keeps .orb-input-row (no quick-chat-popup there). */
body.is-mobile.frank-popup-open .orb-input-row{display:none}
/* Tab bar stays visible and reachable while the orb popup is open (Scott, 2026-07-10)
   -- previously force-hidden here, which left no way off the orb screen except the
   hamburger's small text popup. Stacked above #orb-view (z-index 750) so it's both
   visible and tappable; phoneTab() below closes the popup when a non-ask tab is tapped. */
body.is-mobile.frank-popup-open #phone-tabbar{display:flex;z-index:761}
.frank-popup-fixed{display:none}
body.is-mobile .frank-popup-fixed{
  display:flex;position:fixed;z-index:760;
  top:calc(10px + env(safe-area-inset-top));
  right:calc(10px + env(safe-area-inset-right));
  width:34px;height:34px;border-radius:var(--r-sm);border:1px solid var(--border);
  background:rgba(15,31,48,.85);color:var(--cyan2);font-size:15px;
  align-items:center;justify-content:center;cursor:pointer;
}
body.is-mobile .frank-popup-fixed:hover{border-color:var(--cyan)}
/* Quick-text popup (mobile only) — the hamburger's actual job: just an input +
   send button, no orb, floating below the hamburger. Hidden by default, shown
   via .open (toggled by toggleQuickChatPopup() in the script). */
#quick-chat-popup{display:none}
body.is-mobile #quick-chat-popup.open{
  display:block;position:fixed;z-index:770;
  top:calc(50px + env(safe-area-inset-top));
  right:calc(10px + env(safe-area-inset-right));
  left:calc(10px + env(safe-area-inset-left));
  max-width:420px;margin-left:auto;
  background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);
  padding:10px;box-shadow:0 8px 30px rgba(0,0,0,.4);
}
#quick-chat-popup .qcp-row{display:flex;gap:8px}
#quick-chat-input{flex:1;background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-pill);
  padding:10px 16px;color:var(--text);font-size:14px;outline:none}
#quick-chat-input:focus{border-color:var(--gold)}
#quick-chat-send{width:40px;height:40px;border-radius:50%;background:var(--gold);border:none;cursor:pointer;
  display:flex;align-items:center;justify-content:center;flex-shrink:0}
#quick-chat-send svg{width:18px;height:18px;stroke:#0D1B2A;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
#quick-chat-status{font-size:11px;color:var(--muted);margin-top:8px}
/* the 19-item sidebar is hidden by default on phone and revealed on demand via "More" */
body.is-mobile .sidebar{display:none}
body.is-mobile.phone-more-open .sidebar{
  display:block;position:fixed;left:0;right:0;top:0;bottom:58px;z-index:690;
  overflow-y:auto;background:var(--bg);padding:14px;
  padding-top:calc(14px + env(safe-area-inset-top));
}

/* ══ Phone Mode v2 — dedicated native panels (own classes → immune to the desktop
   @media !important overrides that broke v1's reuse; real internal scroll). ══ */
#phone-body{display:none}
body.is-mobile.phone-panel #phone-body{
  display:block;position:fixed;left:0;right:0;top:0;bottom:58px;z-index:680;
  background:var(--bg);overflow-y:auto;-webkit-overflow-scrolling:touch;
  padding:14px 13px calc(20px + env(safe-area-inset-bottom));
  padding-top:calc(14px + env(safe-area-inset-top));
}
/* when a native panel is up, hide the desktop content + header behind it */
body.is-mobile.phone-panel .main,
body.is-mobile.phone-panel .hdr-logo,
body.is-mobile.phone-panel .hdr-bar{display:none !important}
.pp{display:none}
.pp.on{display:block}
.pp-h{font-size:12px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);margin:2px 2px 12px}
.pcard{background:var(--panel);border:1px solid var(--border);border-radius:var(--r-lg);padding:13px;margin-bottom:10px}
.pcard .pt{font-weight:700;font-size:14px;color:var(--text);margin-bottom:3px;line-height:1.35}
.pcard .pm{font-size:12px;color:var(--muted);word-break:break-word}
.pp-acts{display:flex;gap:8px;margin-top:11px}
.pp-btn{flex:1;border:1px solid transparent;border-radius:var(--r-md);padding:11px;font-size:13px;font-weight:700;cursor:pointer;font-family:inherit}
.pp-btn.ok{background:var(--cyan);color:#04121b}
.pp-btn.no{background:transparent;color:var(--muted);border-color:var(--border)}
.pp-empty{text-align:center;color:var(--muted);font-size:13px;padding:34px 10px;line-height:1.5}
.ptiles{display:grid;grid-template-columns:repeat(3,1fr);gap:9px;margin-bottom:14px}
.ptile{background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 8px;text-align:center}
.ptile .n{font-size:20px;font-weight:800;color:var(--text)}
.ptile .l{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.05em;margin-top:3px}
.palert{display:flex;gap:10px;align-items:flex-start;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:11px;margin-bottom:8px;font-size:12.5px;color:var(--text);line-height:1.4}
.palert .pdot{width:8px;height:8px;border-radius:50%;margin-top:5px;flex:none;background:var(--muted)}
.palert.warn .pdot{background:var(--amber)}
.palert.crit .pdot{background:var(--red)}
.palert.good .pdot{background:var(--green)}
.pmore-grp{font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:14px 2px 7px}
.pmore-item{display:flex;align-items:center;gap:12px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:13px;font-size:14px;font-weight:600;color:var(--text);cursor:pointer;margin-bottom:8px}
.pmore-item:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
.pmore-item .pmi{width:24px;text-align:center;font-size:16px}
.pmore-item .pmc{margin-left:auto;color:var(--muted)}
/* tappable needs-attention cards */
.palert.tappable{cursor:pointer}
.palert.tappable:active{background:var(--panel2)}
.palert .pchev{margin-left:auto;color:var(--muted);flex:none;align-self:center}
/* phone action sheet */
#phone-sheet-backdrop{display:none;position:fixed;inset:0;z-index:900;background:rgba(0,0,0,.55)}
#phone-sheet{display:none;position:fixed;left:0;right:0;bottom:0;z-index:901;
  background:var(--panel);border-top:1px solid var(--border);border-radius:18px 18px 0 0;
  padding:18px 16px calc(16px + env(safe-area-inset-bottom));flex-direction:column;gap:9px}
body.phone-sheet-open #phone-sheet-backdrop{display:block}
body.phone-sheet-open #phone-sheet{display:flex}
#phone-sheet-title{font-weight:700;font-size:14.5px;color:var(--text);line-height:1.4}
#phone-sheet-sub{font-size:12px;color:var(--muted);margin-bottom:5px;line-height:1.4}
.psheet-btn{border:1px solid var(--border);border-radius:var(--r-md);padding:15px 13px;font-size:14px;
  font-weight:700;cursor:pointer;font-family:inherit;background:var(--panel2);color:var(--text)}
.psheet-btn.primary{background:var(--cyan);border-color:transparent;color:#04121b}
.psheet-btn.cancel{background:transparent;color:var(--muted)}

/* ══ Phone Mode v3 — fit the desktop screens to the phone width (no sideways scroll) ══
   The 19 desktop screens use inline `grid-template-columns:1fr 1fr` blocks that never
   collapse on a phone (Phone|Timezone, Username|Password, Revenue|Orders, button pairs),
   pushing content off-screen. Collapse them to one column + hard overflow guard. All
   mobile-gated; desktop untouched. Compact phone panels use CLASS grids, so unaffected. */
body.is-mobile{overflow-x:hidden}
body.is-mobile #stage-wrap,body.is-mobile #stage,body.is-mobile .main,
body.is-mobile .screen,body.is-mobile .panel{max-width:100vw;overflow-x:hidden}
/* an !important stylesheet rule beats a non-important inline style → 2-/3-col → 1-col */
body.is-mobile .screen [style*="1fr 1fr"],
body.is-mobile .main [style*="1fr 1fr"]{grid-template-columns:1fr !important}
body.is-mobile .screen input,body.is-mobile .screen textarea,
body.is-mobile .screen select,body.is-mobile .screen button,
body.is-mobile .screen .hub-thumb,body.is-mobile .screen img{max-width:100%;box-sizing:border-box}

/* ── Respect prefers-reduced-motion — none of the continuous decorative
   animations (status pulse, mini-wave, spinner) served any functional purpose
   that requires motion; stop them for users who've asked the OS not to
   animate (2026-07-08 accessibility review). The orb's own idle rotation is
   gated in JS (see applyReducedMotion()) since it's a canvas render loop, not
   CSS. Voice-reactive motion while %%AGENT_SHORT%% is actually speaking stays
   on regardless — that's functional feedback, not decoration. ──*/
@media (prefers-reduced-motion: reduce){
  .status-pill .dot{animation:none}
  .mini-wave span{animation:none;height:10px}
  .hub-spinner{animation:none}
  .screen.active{animation:none}
  .nav-item,body.is-mobile #phone-tabbar .ptab,body.is-mobile #phone-tabbar .ptab .pti{transition:none}
  .nav-item:active,body.is-mobile #phone-tabbar .ptab:active{transform:none}
  .create-choice{transition:none}
  .create-choice:hover,.create-choice:active{transform:none}
  /* .act-btn's press-scale predates this file's reduced-motion pass (pre-existing
     gap, fixed in passing here since Phase 3 already touches this selector). */
  .act-btn:active,.hub-act-btn:active{transform:none}
}
</style>
</head>
<body>
<div id="persist-warning"><span class="pw-txt">⚠️ <b>DATA IS NOT BEING SAVED.</b> Every change resets when the server restarts. Attach a Railway Volume mounted at <b>/data</b> to make data persist.</span><button id="persist-warning-x" aria-label="Dismiss" onclick="dismissPersistWarning()">✕</button></div>
<div id="stage-wrap"><div id="stage">

  <button id="hamburger-btn" class="hamburger-fixed" aria-label="Toggle control center">☰</button>
  <button id="frank-popup-btn" class="frank-popup-fixed" aria-label="Quick message to %%AGENT_SHORT%%" onclick="toggleQuickChatPopup()">💬</button>

  <div id="quick-chat-popup">
    <div class="qcp-row">
      <input id="quick-chat-input" type="text" placeholder="Type to %%AGENT_NAME%%…" autocomplete="off" aria-label="Type a message">
      <button id="quick-chat-send" onclick="sendQuickChat()" aria-label="Send message">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
    <div id="quick-chat-status" style="display:none"></div>
  </div>

  <div id="orb-view">
    <div class="orb-hero-stage">
      <canvas id="orb" width="640" height="640"></canvas>
      <canvas id="orb-gl" width="640" height="640"></canvas>
      <div class="orb-overlay">
        <div class="o1">%%AGENT_SHORT%%</div>
        <div class="o2">SHOP ASSISTANT</div>
        <div class="o3" id="orb-build-ver">Build —</div>
      </div>
    </div>
    <div class="orb-state" id="orb-state">IDLE — slow ambient rotation</div>
    <div class="orb-hint">click the orb (or the talk pill) to start talking to %%AGENT_SHORT%%</div>
    <div class="orb-input-row">
      <input id="orb-chat-input" type="text" placeholder="Or type to %%AGENT_NAME%%…" autocomplete="off" aria-label="Type a message">
      <button id="orb-chat-send" onclick="sendMsg('orb-chat-input')" aria-label="Send message">
        <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
      </button>
    </div>
    <button class="orb-open-chat" onclick="openFullChat()" role="button" tabindex="0" aria-label="Open the full chat conversation">💬 Open full chat</button>
  </div>

  <div class="hdr-logo brk">
    <div class="hex" aria-hidden="true">⬡</div>
    <div class="lbl"><h1 class="l1 hdr-title-h1">%%AGENT_SHORT%%</h1><div class="l2">SHOP ASSISTANT</div></div>
  </div>

  <div class="hdr-bar">
    <div class="status-pill" id="system-status-pill"><span class="dot"></span>SYSTEM STATUS &nbsp;● <span id="system-status-label">OPTIMAL</span></div>
    <div class="clockwrap"><div class="d" id="dt">--</div><div class="t" id="clk">--:--</div></div>
    <div class="right">
      <input class="search" id="global-search" aria-label="Search listings, orders, tools, knowledge base" placeholder="Search listings, orders, tools, knowledge base…" onkeydown="if(event.key==='Enter')runGlobalSearch(this.value)">
      <div class="icon-btn" id="orb-desktop-btn" onclick="closeControlCenter()" title="Switch to %%AGENT_SHORT%% Orb" aria-label="Switch to %%AGENT_SHORT%% Orb" role="button" tabindex="0" style="font-size:16px">⬡</div>
      <div class="icon-btn" id="bell-btn" onclick="event.stopPropagation();toggleAlertDropdown()" aria-label="Alerts" aria-haspopup="true" aria-expanded="false" role="button" tabindex="0">🔔<span class="badge" id="bell-badge" style="display:none" aria-live="polite" aria-atomic="true">0</span>
        <div id="alert-dropdown" class="alert-dropdown" style="display:none" onclick="event.stopPropagation()">
          <div class="alert-dropdown-title">Alerts</div>
          <div id="alert-dropdown-list"><div style="color:var(--muted);font-size:11px;padding:8px">Loading…</div></div>
        </div>
      </div>
      <div class="icon-btn" onclick="startTour()" title="Replay tutorial" aria-label="Replay tutorial" role="button" tabindex="0">?</div>
      <div class="icon-btn" onclick="showScreen('settings')" aria-label="Settings" role="button" tabindex="0">⚙</div>
      <div class="operator" id="operator-chip" title="Click to log out" onclick="doLogout()" style="cursor:pointer" role="button" tabindex="0" aria-label="Log out"><div class="av" id="op-av">…</div><div><div class="ol1" id="op-name">…</div><div class="ol2" id="op-role">…</div></div></div>
    </div>
  </div>

  <div class="sidebar" role="navigation" aria-label="Primary">
    <h2 class="nav-section nav-section-h2" id="nav-heading-frank">%%AGENT_SHORT%%</h2>
    <div class="nav-item active" data-screen="cmd" role="button" tabindex="0" aria-current="page"><span class="ic" aria-hidden="true">⌂</span>Home</div>
    <div class="nav-item" data-screen="actions" role="button" tabindex="0"><span class="ic" aria-hidden="true">✓</span>Approvals<span class="nbadge" id="badge-actions" style="display:none">—</span></div>
    <div class="nav-item" data-screen="create" role="button" tabindex="0"><span class="ic" aria-hidden="true">✚</span>Create</div>
    <div class="nav-item" data-screen="listings" role="button" tabindex="0"><span class="ic" aria-hidden="true">🏷</span>Your listings</div>
    <div class="nav-item" data-screen="knowledge" role="button" tabindex="0"><span class="ic" aria-hidden="true">✦</span>Knowledge</div>
    <div class="nav-item" data-screen="conversations" role="button" tabindex="0"><span class="ic" aria-hidden="true">💬</span>Chat History</div>

    <h2 class="nav-section nav-section-h2">Shop</h2>
    <div class="nav-item" data-screen="products" role="button" tabindex="0"><span class="ic" aria-hidden="true">📦</span>Products</div>
    <div class="nav-item" data-screen="brandkit" role="button" tabindex="0"><span class="ic" aria-hidden="true">🎨</span>Brand Kit</div>
    <div class="nav-item" data-screen="files" role="button" tabindex="0"><span class="ic" aria-hidden="true">🗂</span>Files</div>
    <div class="nav-item" data-screen="connections" role="button" tabindex="0"><span class="ic" aria-hidden="true">🔌</span>Connections</div>
    <!-- 2026-07-17 (Wave 3 usability): Settings holds only everyday, non-technical
         preferences (Voice/Appearance/Branding) -- moved out of the Advanced
         disclosure below, which is for genuinely engineering-level screens. Was
         already one click away via the header gear icon; this fixes the sidebar
         browse path to match. -->
    <div class="nav-item" data-screen="settings" role="button" tabindex="0"><span class="ic" aria-hidden="true">⚙</span>Settings</div>

    <h2 class="nav-section nav-section-h2 nav-advanced-toggle" id="nav-advanced-toggle" role="button" tabindex="0" aria-expanded="false" aria-controls="nav-advanced-items">Advanced <span id="nav-advanced-caret" aria-hidden="true">▸</span></h2>
    <div id="nav-advanced-items">
    <div class="nav-item" data-tier="advanced" data-screen="tasks" role="button" tabindex="0"><span class="ic" aria-hidden="true">☑</span>Tasks<span class="nbadge" id="badge-tasks" style="display:none">—</span></div>
    <div class="nav-item" data-tier="advanced" data-screen="calendar" role="button" tabindex="0"><span class="ic" aria-hidden="true">▦</span>Calendar<span class="nbadge" id="badge-calendar" style="display:none">—</span></div>
    <div class="nav-item" data-tier="advanced" data-screen="tools" role="button" tabindex="0"><span class="ic" aria-hidden="true">🛠</span>Tools &amp; Skills<span class="nbadge" id="badge-tools" style="display:none">—</span></div>
    <div class="nav-item" data-tier="advanced" data-screen="workflows" role="button" tabindex="0"><span class="ic" aria-hidden="true">⇄</span>Workflows</div>
    <div class="nav-item" data-tier="advanced" data-screen="security" role="button" tabindex="0"><span class="ic" aria-hidden="true">🛡</span>Security</div>
    <div class="nav-item" data-tier="advanced" data-screen="core" role="button" tabindex="0"><span class="ic" aria-hidden="true">◎</span>AI Core</div>
    <div class="nav-item" data-tier="advanced" data-screen="agents" role="button" tabindex="0"><span class="ic" aria-hidden="true">⚙</span>Agents</div>
    </div>

    <div class="voice-widget" style="text-align:left">
      <div class="vw-title">QUICK COMMANDS</div>
      <button class="qc-btn" onclick="showScreen('tasks');document.getElementById('hud-todo-input').focus()"><span class="qic">+</span>Start New Task</button>
      <button class="qc-btn" onclick="showScreen('calendar')"><span class="qic">▦</span>Open Calendar</button>
      <button class="qc-btn" onclick="runWorkflow('shop_health_check', this, false)"><span class="qic">✓</span>Run Health Check</button>
      <button class="qc-btn" onclick="showScreen('workflows')"><span class="qic">⇄</span>Run Workflow</button>
    </div>
  </div>
  <div id="toast-stack" aria-live="polite" aria-atomic="false"></div>

  <!-- First-login spotlight tour — see startTour()/renderTourStep() below. Desktop
       spotlights the sidebar (TOUR_STEPS); mobile spotlights #phone-tabbar's 5 tabs
       (MOBILE_TOUR_STEPS) since it has no sidebar. Replayable anytime via the '?'
       icon in the header (desktop) or More → Replay Tutorial (mobile,
       renderPhoneMore()) — both just call startTour(). -->
  <div id="tour-root">
    <div id="tour-click-catcher" onclick="tourSkip()"></div>
    <div id="tour-spot"></div>
    <div id="tour-tooltip" role="dialog" aria-modal="true" aria-labelledby="tour-step-title">
      <div class="tour-dots" id="tour-dots"></div>
      <div class="tour-step-title" id="tour-step-title"></div>
      <div class="tour-step-body" id="tour-step-body"></div>
      <div class="tour-controls">
        <button class="tour-skip" onclick="tourSkip()">Skip tour</button>
        <div class="tour-btns">
          <button class="tour-nav-btn" id="tour-back-btn" onclick="tourBack()">Back</button>
          <button class="tour-nav-btn primary" id="tour-next-btn" onclick="tourNext()">Next</button>
        </div>
      </div>
    </div>
  </div>

  <!-- ══════════ COMMAND CENTER (home) ══════════ -->
  <div class="screen active" id="screen-cmd">
    <div class="main" role="main">

      <!-- LEFT: system state -->
      <div class="col-left">
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

        <div class="panel brk col-sysmon">
          <div class="panel-title">Dependency Health <span class="lnk" id="recheck-creds-btn" onclick="recheckCredentials()" role="button" tabindex="0">Recheck now</span></div>
          <div class="dep-pill-row" id="dep-pill-row"><div style="color:var(--muted);font-size:11px">Loading…</div></div>
        </div>

        <div class="panel brk col-timeline">
          <div class="panel-title">Mission Timeline <span class="src">/api/todos</span></div>
          <div class="panel-body" id="timeline-list"><div style="color:var(--muted);font-size:11px">Loading…</div></div>
          <div class="panel-title" style="margin-top:6px;margin-bottom:0"><span class="lnk" style="margin-left:auto;cursor:pointer" onclick="showScreen('tasks')" role="button" tabindex="0">View Full Schedule ›</span></div>
        </div>
      </div>

      <!-- CENTER: primary interaction -->
      <div class="col-center">
        <div class="panel brk col-chat">
          <div class="panel-title">Ask %%AGENT_SHORT%% <span class="src">/ws/chat — live, always-on chat</span></div>
          <div id="chat-msgs" aria-live="polite"></div>
          <div class="lc-chips">
            <span class="lc-chip" onclick="sendChip(this)" role="button" tabindex="0">What should I focus on?</span>
            <span class="lc-chip" onclick="sendChip(this)" role="button" tabindex="0">How are sales?</span>
            <span class="lc-chip" onclick="sendChip(this)" role="button" tabindex="0">What's my next listing?</span>
            <span class="lc-chip" onclick="sendChip(this)" role="button" tabindex="0">Pricing advice</span>
            <span class="lc-chip" onclick="sendChip(this)" role="button" tabindex="0">SEO tips</span>
          </div>
          <div class="lc-input-row">
            <input id="chat-input" type="text" placeholder="Ask %%AGENT_NAME%%…" autocomplete="off" aria-label="Message">
            <button id="chat-send" onclick="sendMsg()" aria-label="Send message">
              <svg viewBox="0 0 24 24"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
            </button>
          </div>
        </div>
      </div>

      <!-- RIGHT: business data + activity -->
      <div class="col-right">
        <div class="panel brk col-shop">
          <div class="panel-title" style="cursor:pointer;user-select:none" onclick="toggleShopExpand()" id="shop-perf-title" role="button" tabindex="0">
            Shop Performance
            <span style="font-size:10px;opacity:.5;margin-left:4px" id="shop-expand-arrow">▼ expand</span>
            <span class="src">/api/analytics + /api/metrics</span>
          </div>
          <div class="shop-spark-row" id="shop-spark-row">
            <div class="shop-spark-card"><div class="ssc-lab">Revenue · 30d</div><div class="ssc-val" id="shop-rev-30d">—</div></div>
            <div class="shop-spark-card"><div class="ssc-lab">Orders · 30d</div><div class="ssc-val" id="shop-ord-30d">—</div></div>
          </div>
          <div class="shop-chip-row" id="shop-chip-row">
            <div class="shop-chip"><div class="nm">Listings</div><div class="v" id="shop-listings">—</div></div>
            <div class="shop-chip"><div class="nm">Total Sales</div><div class="v" id="shop-total-sales">—</div></div>
            <div class="shop-chip"><div class="nm">All-Time Revenue</div><div class="v" id="shop-alltime-rev">—</div></div>
          </div>
          <div id="shop-expanded" style="display:none;margin-top:10px;border-top:1px solid var(--border);padding-top:10px">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px">
              <div class="shop-chip"><div class="nm">Revenue · 7d</div><div class="v" id="shop-rev-7d">—</div></div>
              <div class="shop-chip"><div class="nm">Orders · 7d</div><div class="v" id="shop-ord-7d">—</div></div>
              <div class="shop-chip"><div class="nm">Revenue · Today</div><div class="v" id="shop-rev-today">—</div></div>
              <div class="shop-chip"><div class="nm">Orders · Today</div><div class="v" id="shop-ord-today">—</div></div>
              <div class="shop-chip"><div class="nm">Avg Order Value</div><div class="v" id="shop-aov">—</div></div>
              <div class="shop-chip"><div class="nm">Active Listings</div><div class="v" id="shop-active">—</div></div>
            </div>
            <div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px">Recent Sales</div>
            <div id="shop-recent-sales" style="font-size:11px">—</div>
          </div>
        </div>

        <div class="panel brk col-meminsights">
          <div class="panel-title">Star Seller Status <span class="src">/api/star-seller</span></div>
          <div id="star-seller-body" style="padding:4px 0">
            <div style="color:var(--muted);font-size:11px">Loading…</div>
          </div>
        </div>

        <div class="panel brk col-meminsights">
          <div class="panel-title">Ads &amp; ROAS <span class="src">/api/ads-status</span></div>
          <div id="ads-status-body" style="padding:4px 0">
            <div style="color:var(--muted);font-size:11px">Loading…</div>
          </div>
        </div>

        <div class="panel brk col-meminsights">
          <div class="panel-title">COGS &amp; Profit (est.) <span class="src">/api/cogs-status</span></div>
          <div id="cogs-status-body" style="padding:4px 0">
            <div style="color:var(--muted);font-size:11px">Loading…</div>
          </div>
        </div>

        <div class="panel brk col-agents">
          <div class="panel-title">Inbox &amp; Reviews <span class="src">/api/inbox</span></div>
          <div id="inbox-body">
            <div style="color:var(--muted);font-size:11px">Loading…</div>
          </div>
        </div>

        <div class="panel brk col-feed">
          <div class="panel-title">Live Intelligence Feed <span class="src">/api/queue</span></div>
          <div class="panel-body" id="feed-list"><div style="color:var(--muted);font-size:11px">Loading…</div></div>
        </div>
      </div>

    </div>
  </div>

  <!-- ══════════ AI CORE — real data: /health + /api/credentials/status ══════════ -->
  <div class="screen" id="screen-core">
    <div class="panel brk" style="height:100%;overflow-y:auto">
      <div class="panel-title">AI Core <span class="src">/health + /api/credentials/status</span></div>
      <div class="panel-body" id="core-detail">
        <div class="core-row"><span class="lab"><span class="dotc"></span>Loading…</span><span class="v">—</span></div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Actions</div>
      <div class="hub-card" style="display:flex;flex-direction:column;gap:8px;padding:12px">
        <button onclick="coreRefreshEtsyToken()" id="core-btn-refresh-token" style="background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:var(--r-sm);padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:left">🔄 Refresh Etsy Token Now</button>
        <button onclick="showScreen('files')" style="background:var(--bg);color:var(--text);border:1px solid var(--border);border-radius:var(--r-sm);padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:left">🗂 Backups &amp; Files →</button>
        <button onclick="coreRedeploy()" id="core-btn-redeploy" style="background:var(--bg);color:var(--red);border:1px solid var(--red);border-radius:var(--r-sm);padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:left">⟳ Redeploy Server</button>
        <div style="font-size:11px;color:var(--muted);line-height:1.5;padding:0 2px">Redeploy causes a brief real outage (~30-60s) while the server restarts. Only use it if something's actually stuck.</div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Recent Errors <span class="src">/api/core/recent-errors</span></div>
      <div id="core-errors" class="hub-card" style="padding:12px"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ AGENTS — real data: /api/agents/status (live-status registry) ══════════ -->
  <div class="screen" id="screen-agents">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Agents <span class="src">/api/agents/status — every tile below is a real running loop</span></div>
      <div class="agents-grid" id="agents-grid-full" style="margin-top:14px">
        <div class="agent-tile idle"><div class="top"><div class="ic">⋯</div><div class="name">Loading…</div></div><div class="stat"><span class="d"></span>—</div></div>
      </div>
    </div>
  </div>

  <!-- ══════════ TASKS — real data: /api/todos ══════════ -->
  <div class="screen" id="screen-tasks">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Tasks <span class="src">/api/todos</span></div>
      <div style="display:flex;gap:8px;margin:14px 0;flex-wrap:wrap">
        <input id="hud-todo-input" type="text" placeholder="Add a to-do…" onkeydown="if(event.key==='Enter')addHudTodo()"
          aria-label="New to-do"
          style="flex:1;min-width:160px;background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);padding:9px 12px;font-size:13px;color:var(--text)">
        <select id="hud-todo-category" aria-label="Category" style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);padding:9px 8px;font-size:13px;color:var(--text)">
          <option value="general">General</option>
          <option value="question">Question</option>
          <option value="scott_only">Only You</option>
          <option value="frank_can_do">Frank Can Do</option>
        </select>
        <input id="hud-todo-due" type="date" aria-label="Due date" style="background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);padding:9px 10px;font-size:13px;color:var(--text)">
        <button onclick="addHudTodo()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:9px 16px;font-size:13px;font-weight:600;cursor:pointer">Add</button>
      </div>
      <div id="tasks-list" style="margin-top:10px;overflow-y:auto;max-height:700px">
        <div style="color:var(--muted);font-size:12px">Loading…</div>
      </div>
    </div>
  </div>

  <!-- ══════════ ACTION CENTER — real data: /api/queue + /api/actions — approve/reject gate ══════════ -->
  <div class="screen" id="screen-actions">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Approvals <span class="src">/api/queue + /api/actions — approve/reject staged changes</span></div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <button id="batch-tag-btn" onclick="batchStageTags(this)" style="flex:1;background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:var(--r-md);padding:11px 14px;font-size:13px;font-weight:600;cursor:pointer;text-align:center">⚡ Stage All Tag Fixes</button>
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
  <!-- Merged "Knowledge" screen — everything Frank remembers, in one place.
       Keeps the original content IDs (#memory-content, #kb-content) + search
       inputs so loadMemory/loadKb and searchKb() work unchanged. "Past
       conversations" moved out to its own #screen-conversations (2026-07-15,
       Scott: "I need a option on the list to see the chat box from ask Frank
       to see his responses" -- it was previously reachable only by scrolling
       past this section on desktop; on mobile there was no path to it at
       all). #conversations-content etc. now live only in that one screen. -->
  <div class="screen" id="screen-knowledge">
    <div class="panel brk" style="margin-bottom:14px">
      <div class="panel-title">What Frank remembers</div>
      <div id="memory-content" style="margin-top:10px;overflow-y:auto;max-height:320px"><div class="hub-spinner"></div></div>
    </div>
    <div class="panel brk">
      <div class="panel-title">Knowledge base</div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <input id="kb-search-input" type="text" placeholder="Search all docs…" aria-label="Search all knowledge base docs" style="flex:1;background:var(--panel2);border:1px solid var(--border);color:var(--text);border-radius:var(--r-md);padding:10px 14px;font-size:13px">
        <button onclick="searchKb()" style="background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:var(--r-md);padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer">Search</button>
      </div>
      <div id="kb-content" style="overflow-y:auto;max-height:340px"><div class="hub-spinner"></div></div>
    </div>
  </div>

  <!-- ══════════ CHAT HISTORY — Frank's replies as text, not just spoken.
       Reuses the exact loadConversations/renderConversationList/openConversation/
       renderConversationDetail/searchConversations functions that used to live
       inside #screen-knowledge -- same #conversations-content id, same API
       calls, just its own directly-reachable screen now. ══════════ -->
  <div class="screen" id="screen-conversations">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Chat History <span class="src">/api/conversations — every past reply, in writing</span></div>
      <div style="display:flex;gap:8px;margin:14px 0">
        <input id="conv-search-input" type="text" placeholder="Search all conversations…" aria-label="Search all conversations" style="flex:1;background:var(--panel2);border:1px solid var(--border);color:var(--text);border-radius:var(--r-md);padding:10px 14px;font-size:13px">
        <button onclick="searchConversations()" style="background:var(--panel2);border:1px solid var(--gold);color:var(--gold);border-radius:var(--r-md);padding:10px 16px;font-size:13px;font-weight:600;cursor:pointer">Search</button>
      </div>
      <div id="conversations-content" style="margin-top:10px;overflow-y:auto;max-height:700px"><div class="hub-spinner"></div></div>
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
        <button class="hub-toggle-btn" onclick="loadListings('inactive',this)">Deactivated</button>
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

  <!-- ══════════ BRAND KIT — fully static: shop identity, 16 color themes, listing standards for
       all 3 product lines, pricing, sticker system, typography, brand mark, photography style —
       everything that makes OnBrandCraftz look and sound like OnBrandCraftz, from CLAUDE.md ══════════ -->
  <div class="screen" id="screen-brandkit">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Brand Kit <span class="src">Static — expanded brand system from CLAUDE.md: identity, 16 color themes, listing standards, pricing, sticker system, typography, brand mark, photography style</span></div>
      <div style="font-size:12px;color:var(--muted);margin:6px 0 14px">Everything that makes OnBrandCraftz look and sound like OnBrandCraftz. Jump to a section:</div>
      <div id="brandkit-chooser" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:14px">
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-identity')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">🏷️</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Shop Identity</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-themes')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">🎨</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Color Themes</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-color-rules')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">📐</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Color Rules</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-stickers')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">✨</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Stickers</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-listing-standards')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">📋</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Listing Rules</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-pricing')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">💲</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Pricing</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-typography')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">🔤</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Typography</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-brandmark')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">⬡</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Brand Mark</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('bk-photography')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:12px 6px;cursor:pointer;text-align:center">
          <div style="font-size:20px" aria-hidden="true">📷</div><div style="font-weight:600;margin-top:4px;font-size:11.5px">Photography</div></div>
      </div>
      <div id="brandkit-content" class="hub-scroll"></div>
    </div>
  </div>

  <!-- ══════════ FILES — real data: /api/files (data/digital_products/ + backups) ══════════ -->
  <div class="screen" id="screen-files">
    <div class="panel brk" style="height:100%">
      <div class="panel-title">Files <span class="src">/api/files — live volume listing, data/digital_products/ + backups</span></div>
      <div class="hub-card" style="margin-bottom:12px">
        <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
          <div style="font-size:12px;color:var(--muted);line-height:1.5">Docs, catalog data, and Frank's database snapshot — as one ZIP you can save on your own computer.</div>
          <button onclick="downloadFullBackup()" style="background:var(--gold);color:#06141f;border:none;border-radius:var(--r-sm);padding:10px 18px;font-size:13px;font-weight:600;cursor:pointer;white-space:nowrap;flex-shrink:0">⬇ Download Backup</button>
        </div>
        <div style="font-size:12px;color:var(--muted);line-height:1.5;margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">
          The actual product files (SVG/sublimation/planner assets, ~350MB) don't live on this server — they're kept in the GitHub repo so deploys stay fast.
          <a href="https://github.com/printing3dthings-afk/Etsy/archive/refs/heads/claude/etsy-automation-agents-WFAPU.zip" target="_blank" style="color:var(--gold)">Download everything from GitHub →</a>
        </div>
      </div>
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

  <!-- ══════════ SETTINGS — voice prefs (localStorage) + connections summary + about ══════════ -->
  <div class="screen" id="screen-settings">
    <div class="panel brk" style="height:100%;overflow-y:auto">
      <div class="panel-title">Settings <span class="src">Voice prefs + theme (localStorage) + /api/account + /api/credentials/status + /api/etsy-tokens</span></div>

      <div class="hub-section-title">Voice</div>
      <div class="hub-card">
        <label style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;cursor:pointer">
          <input type="checkbox" class="premium-voice-cb"> Premium voice (OpenAI Whisper + TTS)
        </label>
        <div style="font-size:11px;color:var(--muted);margin-top:8px;line-height:1.5">
          When off (default), %%AGENT_SHORT%% uses local offline voice engines — Whisper.wasm for speech-to-text and Piper
          for text-to-speech — which are free, private, and work without an internet connection. Turning this on
          routes voice through OpenAI's paid Whisper transcription and TTS endpoints instead: it sounds more
          natural but costs API credits per use and requires internet. This toggle is shared with the one next to
          "Talk to %%AGENT_SHORT%%" in the bottom bar — changing either updates both.
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px;flex-wrap:wrap">
          <button class="act-btn secondary" id="voice-test-btn" onclick="testVoicePlayback()">🔊 Test Voice</button>
          <div id="voice-test-status" style="font-size:11px;color:var(--muted)">Plays a short phrase through %%AGENT_SHORT%%'s real voice engine, right now, on this device.</div>
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Appearance</div>
      <div class="hub-card">
        <div style="font-size:13px;font-weight:600;margin-bottom:10px">Color theme</div>
        <div id="theme-swatch-row" style="display:flex;gap:10px;flex-wrap:wrap"></div>
        <div style="font-size:11px;color:var(--muted);margin-top:10px">
          Saved to this device only — every screen repaints instantly, no reload needed.
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Branding</div>
      <div class="hub-card">
        <label for="setting-agent-name" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Agent name</label>
        <input type="text" id="setting-agent-name" class="search" style="width:100%" maxlength="40" placeholder="%%AGENT_SHORT%%">
        <div style="font-size:11px;color:var(--muted);margin-top:8px">
          Renames the agent everywhere — the dashboard, the app name, and how the
          agent refers to itself. Applies on your next page load.
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
          <button class="act-btn primary" onclick="saveBranding()">Save name</button>
          <div id="branding-status" style="font-size:11px;color:var(--muted)"></div>
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Orb / Brand Mark</div>
      <div class="hub-card">
        <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">
          <canvas id="brand-mark-preview" class="brand-mark-canvas" width="64" height="64" style="border-radius:var(--r-md);background:var(--panel2);border:1px solid var(--border)"></canvas>
          <div style="flex:1;min-width:200px">
            <label for="brand-mark-file" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Custom orb image</label>
            <input type="file" id="brand-mark-file" accept="image/png,image/jpeg,image/webp" style="width:100%;color:var(--text);font-size:12px">
          </div>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:8px;line-height:1.5">
          Upload a logo (transparent PNG works best) and the orb rebuilds itself from its shape —
          same glow, rotation, and audio-reactive pulse the default orb already has, just a
          different form. Applies on your next page load.
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px;flex-wrap:wrap">
          <button class="act-btn primary" onclick="uploadBrandMark()">Upload</button>
          <button class="act-btn secondary" onclick="resetBrandMark()">Reset to default orb</button>
          <div id="brand-mark-status" style="font-size:11px;color:var(--muted)"></div>
        </div>
      </div>

      <!-- Model/engine picker removed 2026-07-11: the generation engine is now chosen
           automatically by the backend (env/db defaults) so a shop owner never has to
           think about models or provider keys. loadRuntimeSettings() already
           null-guards the removed selects; saveEngines() is retained but unused. -->

      <div class="hub-section-title" style="margin-top:18px">My Account</div>
      <div class="hub-card">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div>
            <label for="account-name" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Name</label>
            <input type="text" id="account-name" class="search" style="width:100%" placeholder="%%OWNER%%">
          </div>
          <div>
            <label for="account-email" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Email</label>
            <input type="email" id="account-email" class="search" style="width:100%" placeholder="you@example.com">
          </div>
          <div>
            <label for="account-phone" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Phone</label>
            <input type="text" id="account-phone" class="search" style="width:100%" placeholder="(555) 555-5555">
          </div>
          <div>
            <label for="account-timezone" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Timezone</label>
            <input type="text" id="account-timezone" class="search" style="width:100%" placeholder="America/New_York">
          </div>
        </div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
          <button class="act-btn primary" onclick="saveAccountSettings()">Save</button>
          <div id="account-save-status" style="font-size:11px;color:var(--muted)"></div>
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Password</div>
      <div class="hub-card">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div>
            <label for="pw-current" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Current password</label>
            <input type="password" id="pw-current" class="search" style="width:100%" autocomplete="current-password">
          </div>
          <div></div>
          <div>
            <label for="pw-new" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">New password</label>
            <input type="password" id="pw-new" class="search" style="width:100%" autocomplete="new-password">
          </div>
          <div>
            <label for="pw-confirm" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Confirm new password</label>
            <input type="password" id="pw-confirm" class="search" style="width:100%" autocomplete="new-password">
          </div>
        </div>
        <div style="font-size:11px;color:var(--muted);margin-top:8px">At least 8 characters. Changing your password signs you out everywhere — you'll need to log back in.</div>
        <div style="display:flex;align-items:center;gap:10px;margin-top:12px">
          <button class="act-btn primary" onclick="changeMyPassword()">Change password</button>
          <div id="pw-change-status" style="font-size:11px;color:var(--muted)"></div>
        </div>
      </div>

      <div class="hub-section-title" style="margin-top:18px">Connections</div>
      <div class="hub-card" id="settings-connections-summary"><div class="hub-spinner"></div></div>
      <div style="display:flex;gap:10px;margin-top:8px;flex-wrap:wrap">
        <button class="act-btn secondary" onclick="showScreen('connections')">View full Connections ›</button>
        <button class="act-btn secondary" onclick="showScreen('security')">View Security ›</button>
      </div>

      <!-- Multi-admin section removed 2026-07-11: this is a solo shop, so adding
           extra admins (with full owner-level API access) was dead weight. The
           owner-reveal block in loadOperatorChip() was updated to stop referencing
           the removed elements. -->

      <div class="hub-section-title" style="margin-top:18px">About</div>
      <div class="hub-card">
        <div style="font-size:13px;font-weight:600">%%AGENT_SHORT%% HUD</div>
        <div style="font-size:11px;color:var(--muted);margin-top:4px" id="settings-build-ver">Build —</div>
      </div>
    </div>
  </div>

  <!-- ══════════ CREATE — the one place to make what goes on a listing. This is the
       former "Studio" screen, reframed for a first-timer: a plain-language chooser up
       top scrolls to each tool; every original ID/handler is unchanged so
       studioGenerate/svgcConvert/lsgGenerate/studioStageToEtsy/studioPostInstagram/
       Facebook keep working. AI engine is auto-picked by the backend — no model knobs. ══════════ -->
  <div class="screen" id="screen-create">
    <div class="panel brk" style="height:100%;overflow-y:auto">
      <div class="panel-title">Create</div>
      <div style="font-size:12px;color:var(--muted);margin:6px 0 14px">What would you like to make? Frank builds it, you review it, then you approve it before anything goes live.</div>
      <div id="create-chooser" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:16px">
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-buildproduct')" style="background:linear-gradient(135deg,var(--accent,#7c5cbf),var(--panel2));border:1px solid var(--accent,#7c5cbf);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center;grid-column:1/-1">
          <div style="font-size:26px" aria-hidden="true">📦</div><div style="font-weight:700;margin-top:6px">Build whole product</div><div style="font-size:10.5px;color:var(--text);opacity:.85;margin-top:2px">One tap: stickers → planner → 10 photos → Quality Check</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-photos')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">🖼️</div><div style="font-weight:600;margin-top:6px">Listing photos</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Photorealistic mockups from your real file</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-svg')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">✂️</div><div style="font-weight:600;margin-top:6px">SVG file</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Trace a photo into a cut/print vector</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-video')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">🎬</div><div style="font-weight:600;margin-top:6px">Product video</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">A short clip from your product photos</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-social')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">📣</div><div style="font-weight:600;margin-top:6px">Social post</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Share a video to Instagram / Facebook</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-qc')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">✅</div><div style="font-weight:600;margin-top:6px">Quality Check</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Verify a product is publish-ready — free, instant</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-photoset')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">📸</div><div style="font-weight:600;margin-top:6px">Photo set (10)</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Build all 10 listing photos from a planner's PDF</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-printzip')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">🖨️</div><div style="font-weight:600;margin-top:6px">Print sizes</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Wall-art multi-size print ZIP (300dpi, sRGB)</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-buildplanner')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">🗓️</div><div style="font-weight:600;margin-top:6px">Build planner</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">Full PDF + cover + nav + stickers (uses AI)</div></div>
        <div class="create-choice" role="button" tabindex="0" onclick="createGoto('create-stickerpack')" style="background:var(--panel2);border:1px solid var(--border);border-radius:var(--r-md);padding:16px;cursor:pointer;text-align:center">
          <div style="font-size:26px" aria-hidden="true">🌈</div><div style="font-weight:600;margin-top:6px">Sticker pack</div><div style="font-size:10.5px;color:var(--muted);margin-top:2px">9 themed sheets → transparent ZIP (uses AI)</div></div>
      </div>

      <div class="hub-section-title" id="create-buildproduct" style="margin-top:18px">Build whole product — one tap, end to end</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          The full pipeline in one tap, in the right order: <b>sticker pack → planner PDFs (with the sheets embedded) → all 10 listing photos → Quality Check</b>. Runs in the background (~6–10 min) — each deliverable shows in Files as it finishes, and <b>&lt;code&gt;_product_build.log</b> carries the live log and the final QC verdict. <b>The cover + sticker sheets are the paid AI step.</b> Configured codes: DP1030–DP1034. <b style="color:var(--warn,#d98a00)">⚠ Nothing is published</b> — eyeball the sheets + photos for garbled text, then publishing is your call.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="bx-pid" type="text" placeholder="Planner code, e.g. DP1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <select id="bx-engine" title="Art engine for cover + sticker sheets"
            style="padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px">
            <option value="gemini" selected>Gemini art</option>
            <option value="openai">gpt-image-1</option>
            <option value="gpt-image-2">gpt-image-2</option>
          </select>
          <button class="act-btn primary" onclick="buildProductRun()" id="bx-run-btn" style="white-space:nowrap">Build everything</button>
        </div>
        <div id="bx-result" style="margin-top:12px"></div>
      </div>

      <div class="hub-section-title" id="create-buildplanner" style="margin-top:18px">Build planner — full PDF from scratch</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          Builds the whole planner: dated + undated PDFs, an AI kawaii cover, hyperlinked navigation, a TOC, fillable fields, and embedded sticker sheets. Runs in the background (~2–4 min) — the finished files land in your product folder and show in Files. <b>The cover art is the only paid AI step (~a cent);</b> everything else is free. Configured codes: DP1030–DP1034.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="bp-pid" type="text" placeholder="Planner code, e.g. DP1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <select id="bp-engine" title="Art engine for the cover"
            style="padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px">
            <option value="gemini" selected>Gemini art</option>
            <option value="openai">gpt-image-1</option>
            <option value="gpt-image-2">gpt-image-2</option>
          </select>
          <button class="act-btn primary" onclick="buildPlannerRun()" id="bp-run-btn" style="white-space:nowrap">Build planner</button>
        </div>
        <div id="bp-result" style="margin-top:12px"></div>
      </div>

      <div class="hub-section-title" id="create-stickerpack" style="margin-top:18px">Sticker pack — themed sheets → transparent ZIP</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          Builds the whole kawaii sticker pack: 9 themed sheets in the planner's palette, backgrounds stripped to transparent, every sticker cut into its own PNG, packaged into <b>&lt;code&gt;_sticker_pack.zip</b>. Runs in the background (~2–4 min) — the ZIP lands in your product folder and shows in Files. <b>The sheet art is the paid AI step.</b> Reports a real measured sticker count. Configured codes: DP1030–DP1034. <b style="color:var(--warn,#d98a00)">⚠ Eyeball the sheets for garbled text before the count goes on a live listing</b> — the top rule is never lie to the customer, and no file check catches misspelled in-image words.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="sp-pid" type="text" placeholder="Planner code, e.g. DP1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <select id="sp-engine" title="Art engine for the sheets"
            style="padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px">
            <option value="gemini" selected>Gemini art</option>
            <option value="openai">gpt-image-1</option>
            <option value="gpt-image-2">gpt-image-2</option>
          </select>
          <button class="act-btn primary" onclick="stickerPackRun()" id="sp-run-btn" style="white-space:nowrap">Build pack</button>
        </div>
        <div id="sp-result" style="margin-top:12px"></div>
      </div>

      <div class="hub-section-title" id="create-printzip" style="margin-top:18px">Print sizes — multi-size ZIP for a wall-art listing</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          Builds every print size a buyer expects — 4×6 / 8×12 / 12×18 / 16×24, 8×10 / 16×20, A4 / A3, and square — all 300 DPI, sRGB, under Etsy's 20 MB limit, with a README. Local resize, no cost. Needs the raw art JPG on file (not a room mockup).
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="pz-pid" type="text" placeholder="Wall-art code, e.g. WA1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <button class="act-btn primary" onclick="printZipRun()" id="pz-run-btn" style="white-space:nowrap">Build ZIP</button>
        </div>
        <div id="pz-result" style="margin-top:12px"></div>
      </div>

      <div class="hub-section-title" id="create-photoset" style="margin-top:18px">Listing photo set — 10 photos from a planner's real pages</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          Renders the full 10-photo Etsy set straight from the planner's built PDF — real pages in device mockups, no AI stand-ins. Runs on the server (~20–40s); photos land in the product's folder and show up in Files.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="ps-pid" type="text" placeholder="Planner code, e.g. DP1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <select id="ps-engine" title="Art engine for photo 7 if it must be generated"
            style="padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px">
            <option value="gemini" selected>Gemini art</option>
            <option value="openai">gpt-image-1</option>
            <option value="gpt-image-2">gpt-image-2</option>
          </select>
          <button class="act-btn primary" onclick="photoSetRun()" id="ps-run-btn" style="white-space:nowrap">Generate</button>
        </div>
        <div id="ps-result" style="margin-top:12px"></div>
      </div>

      <div class="hub-section-title" id="create-qc" style="margin-top:18px">Quality Check — verify a product is publish-ready</div>
      <div class="hub-card">
        <div style="font-size:12px;color:var(--muted);line-height:1.6;margin-bottom:10px">
          Runs the same pre-publish gates Frank checks before anything goes live — PDF page counts, sticker-pack transparency &amp; sticker count, ZIP integrity, and print-size folders. Runs entirely on the server, no AI and no cost.
        </div>
        <div style="display:flex;gap:8px;flex-wrap:wrap;align-items:center">
          <input id="qc-pid" type="text" placeholder="Product code, e.g. DP1030" autocapitalize="characters"
            style="flex:1;min-width:180px;padding:10px;border:1px solid var(--border);border-radius:var(--r-sm);background:var(--panel2);color:var(--text);font-size:14px" />
          <button class="act-btn primary" onclick="qcRunCheck()" id="qc-run-btn" style="white-space:nowrap">Run Check</button>
        </div>
        <div id="qc-result" style="margin-top:12px"></div>
      </div>
      <div class="studio-grid" style="flex-wrap:wrap">
        <div style="flex:1;min-width:320px">
          <video id="studio-player" controls style="aspect-ratio:16/9"></video>
          <div id="studio-player-caption" style="margin-top:10px;color:var(--muted);font-size:11px">Select a video from the list to preview it here.</div>
        </div>
        <div style="flex:0 0 300px">
          <div class="panel-title" style="margin-top:0">Your videos</div>
          <div id="studio-videos-list" class="hub-scroll" style="max-height:420px"><div class="hub-empty">Loading…</div></div>
        </div>
      </div>

      <div class="hub-section-title" id="create-video" style="margin-top:18px">Product video</div>
      <div class="hub-card">
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Upload images below, or leave images empty and enter an existing Etsy listing ID to pull its photos automatically.</div>
        <input type="file" id="studio-file-input" accept="image/*" multiple aria-label="Source images for video" style="margin-bottom:8px;width:100%;color:var(--text);font-size:12px">
        <div id="studio-upload-status" style="font-size:11px;color:var(--muted);margin-bottom:10px"></div>
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <input id="studio-listing-id" type="number" placeholder="Etsy Listing ID (optional)" aria-label="Etsy Listing ID (optional)" style="flex:1;min-width:140px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <select id="studio-style" aria-label="Video style" style="flex:1;min-width:120px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
            <option value="showcase">Showcase</option>
            <option value="new-drop">New Drop</option>
            <option value="feature">Feature</option>
            <option value="minimal">Minimal</option>
            <option value="ai-scene">✨ AI Scene (cinematic)</option>
          </select>
        </div>
        <div id="studio-ai-fields" style="display:none;margin-bottom:8px">
          <textarea id="studio-scene-prompt" rows="3"
            placeholder="Scene description — auto-filled from title, edit before generating"
            aria-label="Scene description"
            style="width:100%;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px;resize:vertical;box-sizing:border-box;margin-bottom:6px"></textarea>
          <select id="studio-aspect-ratio" aria-label="Video aspect ratio" style="width:100%;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
            <option value="9:16">9:16 Vertical — TikTok / Reels / Stories</option>
            <option value="16:9">16:9 Horizontal — YouTube / Facebook</option>
          </select>
        </div>
        <div style="display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center">
          <input id="studio-title" type="text" placeholder="Title (optional)" aria-label="Title (optional)" style="flex:1;min-width:140px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <input id="studio-price" type="text" placeholder="Price (optional)" aria-label="Price (optional)" style="flex:0 0 110px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);white-space:nowrap"><input type="checkbox" id="studio-digital" checked> Digital</label>
        </div>
        <label for="setting-video-engine" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Video engine</label>
        <select id="setting-video-engine" aria-label="Video engine" onchange="saveEngines()" style="width:100%;margin-bottom:10px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <option value="sora">Sora (default)</option>
          <option value="veo">Veo (needs Google/Gemini key)</option>
        </select>
        <button class="act-btn primary" style="width:100%" onclick="studioGenerate()" id="studio-generate-btn">Generate Video</button>
        <div id="studio-generate-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>
      </div>

      <div class="hub-section-title" id="create-social" style="margin-top:18px">Post to social</div>
      <div class="hub-card" style="margin-bottom:6px"><div style="font-size:11px;color:var(--muted)">Make or pick a video above first — then Instagram / Facebook options appear right below.</div></div>
      <div class="hub-section-title" id="studio-actions-title" style="display:none">Actions — <span id="studio-actions-filename"></span></div>
      <div class="hub-card" id="studio-actions-card" style="display:none">
        <div style="font-size:12px;font-weight:600;color:var(--text);margin-bottom:6px">Attach to Etsy Listing</div>
        <div style="font-size:11px;color:var(--muted);margin-bottom:8px">Stages the video for %%OWNER%%'s approval — it is only attached to the listing after you approve it in Approvals.</div>
        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <input id="studio-attach-listing-id" type="number" placeholder="Listing ID" aria-label="Listing ID to attach video to" style="flex:1;min-width:120px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <input id="studio-attach-rank" type="number" min="1" max="10" placeholder="Rank 1-10 (optional)" aria-label="Photo rank 1-10 (optional)" style="flex:0 0 160px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
        </div>
        <button class="act-btn primary" style="width:100%" onclick="studioStageToEtsy()" id="studio-stage-btn">Stage for Approval</button>
        <div id="studio-stage-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>

        <div style="font-size:12px;font-weight:600;color:var(--text);margin:18px 0 6px">Post to Instagram</div>
        <textarea id="studio-ig-caption" placeholder="Caption" aria-label="Instagram caption" style="width:100%;min-height:50px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px;margin-bottom:8px"></textarea>
        <button class="act-btn primary" style="width:100%" onclick="studioPostInstagram()" id="studio-ig-btn">Post to Instagram (Reel)</button>
        <div id="studio-ig-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>

        <div style="font-size:12px;font-weight:600;color:var(--text);margin:18px 0 6px">Post to Facebook</div>
        <textarea id="studio-fb-caption" placeholder="Description" aria-label="Facebook description" style="width:100%;min-height:50px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px;margin-bottom:8px"></textarea>
        <button class="act-btn primary" style="width:100%" onclick="studioPostFacebook()" id="studio-fb-btn">Post to Facebook</button>
        <div id="studio-fb-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>
      </div>

      <div class="hub-section-title" id="create-svg" style="margin-top:18px">SVG file — trace a photo to vector</div>
      <div class="hub-card">
        <div style="font-size:11px;color:var(--muted);margin-bottom:10px">Drop a reference photo below to trace it into an SVG — a photo you took, a screenshot, something you found on Pinterest.</div>

        <div id="svgc-dropzone" onclick="document.getElementById('svgc-file-input').click()"
          role="button" tabindex="0" aria-label="Upload reference photo"
          style="border:2px dashed var(--border);border-radius:var(--r-md);padding:28px 14px;text-align:center;cursor:pointer;color:var(--muted);font-size:12px;margin-bottom:12px;transition:border-color .15s,background .15s">
          <div style="font-size:22px;margin-bottom:6px" aria-hidden="true">📥</div>
          Drop a reference photo here, or click to browse
        </div>
        <input type="file" id="svgc-file-input" accept="image/*" style="display:none" aria-label="Reference photo file">

        <div style="display:flex;gap:8px;margin-bottom:8px;flex-wrap:wrap">
          <select id="svgc-target" aria-label="What's this SVG for?" style="flex:1;min-width:160px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
            <option value="3dprint">3D-Print Sign (SS-series)</option>
            <option value="wallart">Wall Art</option>
            <option value="sticker">Sticker Pack Source Art</option>
            <option value="planner">Planner Cover Art</option>
            <option value="none">Just give me an SVG</option>
          </select>
          <select id="svgc-mode" aria-label="Conversion mode" style="flex:1;min-width:140px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
            <option value="silhouette">Silhouette (single shape, cleanest)</option>
            <option value="bw">Black &amp; White (line art)</option>
            <option value="color">Full Color</option>
          </select>
        </div>
        <div id="svgc-hint" style="font-size:11px;color:var(--muted);margin-bottom:10px"></div>
        <div id="svgc-status" style="font-size:11px;color:var(--muted);margin-bottom:10px"></div>

        <div id="svgc-result" style="display:none">
          <div style="background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:14px;margin-bottom:10px;text-align:center">
            <img id="svgc-preview" style="max-width:100%;max-height:280px;background:#fff;border-radius:6px" alt="Converted SVG preview">
          </div>
          <div id="svgc-quality" style="font-size:12px;margin-bottom:10px"></div>
          <a id="svgc-download" class="act-btn primary" style="width:100%;display:block;text-align:center;text-decoration:none;box-sizing:border-box" download>Download SVG</a>
        </div>
      </div>

      <div class="hub-section-title" id="create-photos" style="margin-top:18px">Listing photo — from your real product file</div>
      <div class="hub-card">
        <div style="font-size:11px;color:var(--muted);margin-bottom:10px">Upload the REAL product file(s) — the actual thing being sold, never a stand-in — and generate a photorealistic lifestyle photo. Self-verified against your file; if a render doesn't actually match it, it retries automatically instead of handing you something wrong.</div>

        <input type="file" id="lsg-file-input" accept="image/*,.pdf,.svg" multiple aria-label="Real product file(s)" style="margin-bottom:8px;width:100%;color:var(--text);font-size:12px">
        <div id="lsg-upload-status" style="font-size:11px;color:var(--muted);margin-bottom:10px"></div>

        <select id="lsg-category" aria-label="Product category" style="width:100%;margin-bottom:8px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <option value="sign_flat">3D-Print Sign (flat face)</option>
          <option value="tumbler_wrap">Tumbler / Koozie Wrap</option>
          <option value="framed_print">Framed Wall Art</option>
          <option value="flat_paper">Flat Printed Paper / Card</option>
          <option value="ipad_lifestyle">iPad / Digital Planner Screen</option>
          <option value="sticker_sheet_flat">Sticker Sheet (overhead flat lay)</option>
          <option value="3d_print_lamp">3D-Print Lamp (lit)</option>
          <option value="3d_print_vase">3D-Print Vase</option>
          <option value="3d_print_holder">3D-Print Holder</option>
          <option value="3d_print_planter">3D-Print Planter</option>
        </select>

        <textarea id="lsg-scene-prompt" rows="3"
          placeholder="Scene description — auto-filled below, edit before generating"
          aria-label="Scene description"
          style="width:100%;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px;resize:vertical;box-sizing:border-box;margin-bottom:8px"></textarea>

        <div style="font-size:10.5px;color:var(--muted);margin-bottom:10px">Each attempt calls the real image-generation API — real cost per click — up to 2 tries if the first doesn't verify against your source file.</div>

        <label for="setting-image-engine" style="font-size:11px;color:var(--muted);display:block;margin-bottom:4px">Image engine</label>
        <select id="setting-image-engine" aria-label="Image engine" onchange="saveEngines()" style="width:100%;margin-bottom:6px;background:var(--panel);border:1px solid var(--border);border-radius:var(--r-sm);padding:8px;color:var(--text);font-size:12px">
          <option value="openai">OpenAI gpt-image-1 (default · only one with transparent background)</option>
          <option value="gpt-image-2">OpenAI gpt-image-2 (sharper text)</option>
          <option value="gemini">Gemini — Nano Banana (best product consistency across photos)</option>
          <option value="ideogram">Ideogram (best in-image text · generate-only)</option>
        </select>
        <div style="font-size:10px;color:var(--muted);margin-bottom:10px">Gemini &amp; Ideogram need their API key set in .env — Frank tells you if a key is missing when you generate. <span id="engines-status"></span></div>

        <button class="act-btn primary" style="width:100%" onclick="lsgGenerate()" id="lsg-generate-btn">Generate Lifestyle Photo</button>
        <div id="lsg-status" style="font-size:11px;color:var(--muted);margin-top:8px"></div>

        <div id="lsg-result" style="display:none;margin-top:10px">
          <div id="lsg-preview-wrap" style="background:var(--panel);border:1px solid var(--border);border-radius:var(--r-md);padding:14px;margin-bottom:10px;text-align:center">
            <img id="lsg-preview" style="max-width:100%;max-height:320px;border-radius:6px" alt="Generated lifestyle photo">
          </div>
          <div id="lsg-outcome" style="font-size:12px;margin-bottom:10px"></div>
          <a id="lsg-download" class="act-btn primary" style="width:100%;display:block;text-align:center;text-decoration:none;box-sizing:border-box" download>Download Photo</a>
        </div>
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
          <span class="label">TALK TO %%AGENT_SHORT%%</span>
          <div class="mini-wave"><span></span><span></span><span></span><span></span></div>
        </div>
        <div class="sub" id="talk-sub">tap to speak</div>
      </div>
      <label style="display:flex;align-items:center;gap:6px;font-size:12px;color:var(--muted);white-space:nowrap"><input type="checkbox" id="premium-voice-toggle" class="premium-voice-cb"> Premium voice</label>
      <span class="dots-line"></span>
    </div>
    <div class="brief-wrap" style="position:relative">
      <button class="brief-btn" onclick="event.stopPropagation();toggleBriefingPanel()">Executive Briefing</button>
      <div id="brief-panel" class="alert-dropdown" style="display:none;bottom:42px;top:auto" onclick="event.stopPropagation()">
        <div class="alert-dropdown-title">Executive Briefing</div>
        <div id="brief-panel-body"><div style="color:var(--muted);font-size:11px;padding:8px">Loading…</div></div>
      </div>
    </div>
  </div>

  <!-- ══ Phone Mode v2 — native panels (mobile only). Own classes so the desktop
       @media !important rules never touch them; scrolls internally. ══ -->
  <div id="phone-body">
    <section class="pp" id="pp-appr"><div class="pp-h">Waiting on you</div><div id="pp-appr-body"></div></section>
    <section class="pp" id="pp-today"><div class="pp-h">Today</div><div id="pp-today-body"></div></section>
    <section class="pp" id="pp-more"><div class="pp-h">All screens</div><div id="pp-more-body"></div></section>
  </div>

  <!-- ══ Phone action sheet — tap a Needs-attention card → fix-it / view-on-Etsy ══ -->
  <div id="phone-sheet-backdrop" onclick="phoneSheetClose()"></div>
  <div id="phone-sheet" role="dialog" aria-modal="true">
    <div id="phone-sheet-title"></div>
    <div id="phone-sheet-sub"></div>
    <button class="psheet-btn primary" id="phone-sheet-fix" onclick="phoneSheetFix()">🤖 Let Frank fix it</button>
    <button class="psheet-btn" id="phone-sheet-view" onclick="phoneSheetView()">🏷 View listing on Etsy</button>
    <button class="psheet-btn cancel" onclick="phoneSheetClose()">Cancel</button>
  </div>

  <!-- ══ Phone Mode bottom tab bar — mobile only (hidden on desktop via CSS) ══ -->
  <nav id="phone-tabbar" aria-label="Phone navigation">
    <button class="ptab" data-ptab="ask" onclick="phoneTab('ask')" aria-label="Ask Frank"><span class="pti" aria-hidden="true">◉</span>Ask</button>
    <button class="ptab" data-ptab="appr" onclick="phoneTab('appr')" aria-label="Approvals"><span class="pti" aria-hidden="true">✓</span>Approvals<span class="pcnt" id="ptab-badge">0</span></button>
    <button class="ptab on" data-ptab="today" onclick="phoneTab('today')" aria-label="Today"><span class="pti" aria-hidden="true">▤</span>Today<span class="pcnt" id="ptab-today-badge">0</span></button>
    <button class="ptab" data-ptab="create" onclick="phoneTab('create')" aria-label="Create"><span class="pti" aria-hidden="true">✚</span>Create</button>
    <button class="ptab" data-ptab="more" onclick="phoneTab('more')" aria-label="More screens"><span class="pti" aria-hidden="true">⋯</span>More</button>
  </nav>

  <button id="back-to-top-btn" onclick="backToTop()" aria-label="Back to top" title="Back to top">⬆</button>

</div></div>

<script>
// Users who've asked their OS not to animate — gates the orb's idle rotation
// (CSS keyframe animations are gated directly via @media in <style> above). Voice-
// reactive motion while actually speaking stays on; that's functional feedback,
// not decoration (2026-07-08 accessibility review).
const _reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// ── Auto-scale the fixed 1440x900 stage to fit any viewport, desktop only — below
// MOBILE_BREAKPOINT the stage goes fluid via CSS instead (see isMobileMode()). ──
const STAGE_W = 1440, STAGE_H = 900;
const MOBILE_BREAKPOINT = 880;
const stage = document.getElementById('stage');
const mobileMQ = window.matchMedia('(max-width:' + MOBILE_BREAKPOINT + 'px)');
function isMobileMode(){ return mobileMQ.matches; }
// devicePixelRatio changes when the user zooms (in or out); a plain window resize
// (dragging the window edge, rotating a device) leaves it unchanged. Re-fitting on
// every resize is correct — re-fitting on a ZOOM just cancels the zoom the user
// asked for, which is what used to happen here (2026-07-08 accessibility review,
// WCAG 1.4.4/1.4.10: browser zoom was silently neutralized). Skip the re-fit when
// the ratio changed so a real zoom actually enlarges the content instead.
let _lastDPR = window.devicePixelRatio;
function fitStage(){
  if (isMobileMode()){ stage.style.transform = 'none'; return; }
  const dprChanged = window.devicePixelRatio !== _lastDPR;
  _lastDPR = window.devicePixelRatio;
  if (dprChanged) return;
  const scale = Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H);
  stage.style.transform = 'scale(' + scale + ')';
}
function closeControlCenter(){ document.body.classList.remove('cc-open'); }
// openControlCenter() (2026-07-15) — the single place cc-open is ever ADDED.
// cc-open reveals the full desktop dashboard (.hdr-bar/.sidebar/.screen — see
// the body:not(.cc-open) / body.cc-open CSS rules above), including the
// position:absolute #alert-dropdown sized for a 1440px desktop stage. Two
// SEPARATE call sites were each independently found this session setting
// cc-open with no mobile check: syncMobileClass()'s resize/matchMedia-race
// path (fixed first) and phoneOpenScreen() (found after Scott reported the
// alert dropdown "still not visible" post-fix -- phoneOpenScreen() is wired
// to every mobile "More" list item AND the "Create" tab, so one tap
// permanently stuck cc-open on with is-mobile still true). Routing every
// cc-open-adding call site through this one guarded setter, instead of each
// one repeating its own isMobileMode() check (or forgetting to), is what
// actually closes off the bug class -- a third un-audited call site is far
// less likely to reintroduce this if it can only ever add cc-open by calling
// something that already refuses to on mobile.
function openControlCenter(){ if (isMobileMode()) return; document.body.classList.add('cc-open'); }
function toggleControlCenter(){
  if (document.body.classList.contains('cc-open')) closeControlCenter();
  else openControlCenter();
}
let _prevMobile = null;
function syncMobileClass(){
  const mobile = isMobileMode();
  document.body.classList.toggle('is-mobile', mobile);
  if (!mobile && (_prevMobile === null || _prevMobile === true)) {
    // First load on desktop, or transitioning mobile→desktop: open dashboard
    openControlCenter();
  } else if (mobile) {
    // 2026-07-15 (Scott: header bar + alert dropdown showing on mobile,
    // dropdown clipped off-screen): this branch used to be a no-op -- if
    // cc-open was ever added while briefly misdetected as desktop (mobile
    // Safari's matchMedia/resize events can fire spuriously during
    // address-bar show/hide), nothing ever cleared it again once mobile was
    // correctly redetected. Mobile now always wins: is-mobile and cc-open
    // can never coexist. (This only ever needed to be a removal, not a call
    // through openControlCenter() -- removal is always safe regardless of
    // viewport.)
    document.body.classList.remove('cc-open');
  }
  _prevMobile = mobile;
  fitStage();
}
window.addEventListener('resize', syncMobileClass);
mobileMQ.addEventListener('change', syncMobileClass);
syncMobileClass();
document.getElementById('hamburger-btn').addEventListener('click', toggleControlCenter);
// Default phone landing is the orb (the "Ask Frank" full-screen popup) -- Scott
// wants it to be the first thing he sees when the app opens. phoneTab('ask') ->
// openFrankPopup() shows #orb-view with the tab bar still reachable, so he can tap
// Today/Approvals/More to leave. The orb's WebGL render loop is already unpaused by
// resetOrbToDefault() at load, so it animates immediately.
// Deferred via setTimeout(0): the phone panels' renderers touch module-scope `let`
// state (e.g. _phoneNeeds) declared further down this script, so touching them THIS
// early hits the temporal dead zone (real bug caught live via Playwright, "Cannot
// access '_phoneNeeds' before initialization"). Deferring to a fresh macrotask runs
// only after the whole script has finished evaluating -- openFrankPopup() itself is
// TDZ-safe (reads DOM + _frankPopupPrevTab, both ready by then), but we keep the
// defer so the tab bar / underlying panel state is fully wired first.
if (isMobileMode()) setTimeout(() => phoneTab('ask'), 0);

// ── Phone Mode v2: 4-tab shell with dedicated NATIVE panels (mobile only).
// Approvals/Today/More render their own compact, phone-sized panels wired to the
// SAME live data + action fns (approveAction, openRejectModal, /api/metrics,
// /api/alerts, showScreen) — not the desktop screens (which were too big).
// Styled via theme vars so the color selector recolors them. ──
function phoneTab(which){
  if (which === 'ask'){ openFrankPopup(); return; }
  // Leaving the orb popup for a native panel (Scott, 2026-07-10: tab bar is now
  // reachable while the popup is open) -- same cleanup closeFrankPopup() does,
  // minus its recursive phoneTab() call since we're already switching tabs here.
  if (document.body.classList.contains('frank-popup-open')){
    document.body.classList.remove('frank-popup-open');
    document.documentElement.style.overflow = '';
    document.body.style.overflow = '';
  }
  document.querySelectorAll('#phone-tabbar .ptab').forEach(b=>b.classList.toggle('on', b.dataset.ptab===which));
  document.querySelectorAll('#phone-body .pp').forEach(p=>p.classList.remove('on'));
  document.body.classList.add('phone-panel');
  if (which === 'create'){ phoneOpenScreen('create'); return; }
  if (which === 'appr'){ document.getElementById('pp-appr').classList.add('on'); renderPhoneApprovals(); }
  else if (which === 'today'){ document.getElementById('pp-today').classList.add('on'); renderPhoneToday(); }
  else if (which === 'more'){ document.getElementById('pp-more').classList.add('on'); renderPhoneMore(); }
  const pb = document.getElementById('phone-body'); if (pb) pb.scrollTop = 0;
}
// "Talk to Frank" full-screen orb+voice popup (mobile only) — opened ONLY by the
// Ask tab now (2026-07-10: the top-right hamburger was reassigned to the much
// smaller quick-text popup below, per Scott's correction — he wanted the input
// FIELD to pop up, not the whole orb screen). Remembers whichever native panel
// was active underneath so closing returns there instead of always landing back
// on a fixed tab.
let _frankPopupPrevTab = 'today';
function openFrankPopup(){
  const activeBtn = document.querySelector('#phone-tabbar .ptab.on');
  if (activeBtn && activeBtn.dataset.ptab !== 'ask') _frankPopupPrevTab = activeBtn.dataset.ptab;
  document.body.classList.add('frank-popup-open');
  document.querySelectorAll('#phone-tabbar .ptab').forEach(b=>b.classList.toggle('on', b.dataset.ptab==='ask'));
  // Belt-and-suspenders alongside #orb-view's own overflow:hidden -- iOS Safari/PWA
  // can still rubber-band-scroll the underlying page behind a position:fixed
  // element via touch, which is what "the orb moves" looked like (Scott, 2026-07-10).
  document.documentElement.style.overflow = 'hidden';
  document.body.style.overflow = 'hidden';
}
function closeFrankPopup(){
  document.body.classList.remove('frank-popup-open');
  document.documentElement.style.overflow = '';
  document.body.style.overflow = '';
  phoneTab(_frankPopupPrevTab);
}
// Quick-text popup (mobile only) — the top-right hamburger's actual job now: a
// small popup with just an input + send button, no orb, no transcript. Reuses
// the generalized sendMsg(sourceId) (same WS pipeline as #chat-input/#orb-chat-input).
function openQuickChatPopup(){
  document.getElementById('quick-chat-popup').classList.add('open');
  const btn = document.getElementById('frank-popup-btn');
  if (btn){ btn.textContent = '✕'; btn.setAttribute('aria-label','Close'); }
  const inp = document.getElementById('quick-chat-input');
  if (inp) inp.focus();
}
function closeQuickChatPopup(){
  document.getElementById('quick-chat-popup').classList.remove('open');
  const btn = document.getElementById('frank-popup-btn');
  if (btn){ btn.textContent = '☰'; btn.setAttribute('aria-label','Talk to %%AGENT_SHORT%%'); }
}
function toggleQuickChatPopup(){
  if (document.getElementById('quick-chat-popup').classList.contains('open')) closeQuickChatPopup();
  else openQuickChatPopup();
}
function sendQuickChat(){
  const inp = document.getElementById('quick-chat-input');
  if (!inp || !inp.value.trim()) return;
  sendMsg('quick-chat-input');
  const status = document.getElementById('quick-chat-status');
  if (status){
    // Was "check the Ask tab for the full reply" (2026-07-15 correction --
    // Scott: "I need a option on the list to see the chat box... to see his
    // responses"): the Ask tab is just the orb, it never had any visible
    // transcript to check. Frank's replies are spoken via TTS; the actual
    // text now lives in More → Chat History.
    status.textContent = "Sent — Frank's replying… check More → Chat History for the full reply.";
    status.style.display = 'block';
  }
}
// Approvals — only the pending items, compact; reuses approveAction/openRejectModal.
async function renderPhoneApprovals(){
  const el = document.getElementById('pp-appr-body');
  el.innerHTML = '<div class="pp-empty">Loading…</div>';
  try {
    const r = await authGet('/api/queue?status=pending', 15000);
    const d = await r.json().catch(()=>({}));
    if (d && d.actions) _pendingActions = d.actions;
  } catch(e) {}
  const list = _pendingActions || [];
  if (!list.length){ el.innerHTML = '<div class="pp-empty">✅ All clear — nothing needs your approval.</div>'; return; }
  el.innerHTML = list.map(a=>{
    const p = a.payload || {};
    let meta = String(a.type||'').replace(/_/g,' ');
    if (a.type==='publish_listing' && (p.preview||{}).price!=null) meta += ` · $${escHtml(String(p.preview.price))} · ${(p.preview.tags||[]).length} tags`;
    else if (a.type==='update_tags') meta += ` · ${escHtml((p.tags||[]).join(', ')).slice(0,90)}`;
    else if (a.type==='update_title') meta += ` · "${escHtml(p.title||'')}"`;
    else if (a.type==='update_description') meta += ` · ${escHtml((p.description||'').slice(0,90))}…`;
    else if (a.type==='update_price') meta += ` · $${escHtml(Number(p.price||0).toFixed(2))}`;
    else if (a.type==='toggle_listing_state') meta += ` · → ${escHtml(p.new_state||'')}`;
    return `<div class="pcard"><div class="pt">${escHtml(a.summary||a.type)}</div><div class="pm">${escHtml(meta)}</div>
      <div class="pp-acts"><button class="pp-btn ok" onclick="phoneApprove(${a.id})">Approve</button>
      <button class="pp-btn no" onclick="openRejectModal(${a.id})">Reject</button></div>
      <div id="reject-modal-${a.id}" style="display:none"></div></div>`;
  }).join('');
}
async function phoneApprove(id){ await approveAction(id); renderPhoneApprovals(); }
// Today — compact tiles + alerts from the same endpoints the dashboard uses.
async function renderPhoneToday(){
  const el = document.getElementById('pp-today-body');
  el.innerHTML = '<div class="pp-empty">Loading…</div>';
  let m = {}, alerts = [];
  try { const r = await authGet('/api/metrics', 15000); m = await r.json().catch(()=>({})); } catch(e) {}
  try { const r = await authGet('/api/alerts', 15000); const d = await r.json().catch(()=>({}));
        alerts = d.alerts || d.items || (Array.isArray(d) ? d : []) || []; } catch(e) {}
  let acts = [];
  try { const r = await authGet('/api/actions', 15000); const d = await r.json().catch(()=>({}));
        acts = (d.actions||[]).filter(x=>x.severity==='high'||x.severity==='medium'); } catch(e) {}
  // Real /api/metrics shape: orders is an OBJECT ({last_7_days, revenue_7d, ...}),
  // shop.total_sales is the all-time count. (Rendering m.orders directly printed
  // "[object Object]" — caught by Scott on-device.)
  const mo = m.orders || {}, ms = m.shop || {};
  const show = v => (v==null||v==='') ? '—' : v;
  const orders7 = show(mo.last_7_days);
  const rev7 = (mo.revenue_7d != null) ? '$' + Number(mo.revenue_7d).toFixed(2) : '—';
  const totalSales = show(ms.total_sales);
  let html = `<div class="ptiles">
    <div class="ptile"><div class="n">${escHtml(String(orders7))}</div><div class="l">Orders · 7d</div></div>
    <div class="ptile"><div class="n">${escHtml(String(rev7))}</div><div class="l">Rev · 7d</div></div>
    <div class="ptile"><div class="n">${escHtml(String(totalSales))}</div><div class="l">Total sales</div></div>
  </div>`;
  const sevOf = s => { s=String(s||'').toLowerCase();
    return (s.includes('crit')||s.includes('high')||s.includes('err')) ? 'crit'
         : (s.includes('warn')||s.includes('med')) ? 'warn' : 'good'; };
  // Needs attention = Frank's ranked recommendations (with a suggested fix each) + alerts.
  // Recommendations carry listing_id/url → tappable card → action sheet (fix it / view on Etsy).
  const needs = [];
  acts.forEach(x => needs.push({sev: x.severity==='high'?'crit':'warn', title: x.title, sub: x.suggestion,
    listing_id: x.listing_id, url: x.url}));
  alerts.forEach(x => { const t = x.title||x.message||x.text||x.msg||(typeof x==='string'?x:'')||'Alert';
    needs.push({sev: sevOf(x.severity||x.level||x.sev), title: String(t), sub: ''}); });
  _phoneNeeds = needs.slice(0,20);
  if (needs.length){
    html += '<div class="pmore-grp">Needs attention</div>';
    html += _phoneNeeds.map((x,i) => {
      const tap = (x.listing_id || x.url)
        ? ` tappable" role="button" tabindex="0" onclick="phoneNeedsSheet(${i})` : '';
      return `<div class="palert ${x.sev}${tap}"><span class="pdot"></span><div>${escHtml(x.title)}` +
        (x.sub ? `<div style="color:var(--muted);margin-top:2px">${escHtml(x.sub)}</div>` : '') +
        `</div>` + ((x.listing_id || x.url) ? '<span class="pchev">›</span>' : '') + `</div>`;
    }).join('');
  } else {
    html += '<div class="pp-empty" style="padding:22px 10px">Nothing needs attention right now — you\\'re all caught up.</div>';
  }
  el.innerHTML = html;
}
// Action sheet for a tapped Needs-attention card: Frank fixes it, or open on Etsy.
let _phoneNeeds = [];
let _phoneSheetItem = null;
function phoneNeedsSheet(i){
  const it = _phoneNeeds[i];
  if (!it || (!it.listing_id && !it.url)) return;
  _phoneSheetItem = it;
  document.getElementById('phone-sheet-title').textContent = it.title || 'Listing issue';
  document.getElementById('phone-sheet-sub').textContent = it.sub || '';
  document.body.classList.add('phone-sheet-open');
}
function phoneSheetClose(){
  document.body.classList.remove('phone-sheet-open');
  _phoneSheetItem = null;
}
function phoneSheetView(){
  const it = _phoneSheetItem; if (!it) return;
  const url = it.url || (it.listing_id ? 'https://www.etsy.com/listing/' + it.listing_id : null);
  phoneSheetClose();
  if (url) window.open(url, '_blank');
}
function phoneSheetFix(){
  const it = _phoneSheetItem; if (!it) return;
  const ref = it.listing_id ? ('Etsy listing ' + it.listing_id) : 'this listing';
  const prompt = 'Diagnose and fix ' + ref + ' — issue flagged: "' + (it.title || '') + '". '
    + 'Investigate the root cause, then stage your recommended fix for my approval. '
    + 'Do not change the live listing without my approval.';
  phoneSheetClose();
  phoneOpenScreen('cmd');  // the screen that contains the chat panel, so the reply is visible
  const inp = document.getElementById('chat-input');
  if (inp) inp.value = prompt;
  if (typeof sendMsg === 'function') sendMsg();
  showToast('Sent — %%AGENT_SHORT%% is on it. His reply will appear in the chat below.', 'info', 5000);
}
// More — a scrollable launcher for the other screens (fixes v1's unscrollable overlay).
const _PHONE_MORE = [
  ['Shop', [['listings','🏷','Your listings'],['products','📦','Products'],['brandkit','🎨','Brand kit'],['connections','🔌','Connections']]],
  ['Knowledge', [['knowledge','✦','Knowledge'],['conversations','💬','Chat History']]],
  ['Advanced', [['settings','⚙','Settings'],['tasks','☑','Tasks'],['calendar','▦','Calendar'],['files','🗂','Files'],['workflows','⇄','Workflows'],['tools','🛠','Tools'],['core','◎','AI Core'],['agents','⚙','Agents'],['security','🛡','Security']]],
];
function renderPhoneMore(){
  const el = document.getElementById('pp-more-body');
  el.innerHTML = _PHONE_MORE.map(([g, items]) =>
    `<div class="pmore-grp">${g}</div>` + items.map(([s, ic, lbl]) =>
      `<div class="pmore-item" role="button" tabindex="0" onclick="phoneOpenScreen('${s}')"><span class="pmi">${ic}</span>${lbl}<span class="pmc">›</span></div>`
    ).join('')).join('')
    + `<div class="pmore-grp">Help</div>`
    + `<div class="pmore-item" role="button" tabindex="0" onclick="startTour()"><span class="pmi">?</span>Replay Tutorial<span class="pmc">›</span></div>`;
}
// Opening a screen from More exits the phone panel and shows that (desktop) screen.
function phoneOpenScreen(name){
  document.body.classList.remove('phone-panel');
  document.body.classList.add('cc-open');
  document.querySelectorAll('#phone-tabbar .ptab').forEach(b=>b.classList.remove('on'));
  document.querySelectorAll('#phone-body .pp').forEach(p=>p.classList.remove('on'));
  showScreen(name);
}
// Jump from the Ask/orb view straight into the full chat transcript (the "cmd"
// screen that holds the conversation). Closes the "Talk to Frank" popup first so
// it doesn't linger over the chat. Desktop's Home already IS the chat, so there
// it just makes sure that screen is showing.
function openFullChat(){
  document.body.classList.remove('frank-popup-open');
  document.documentElement.style.overflow = '';
  document.body.style.overflow = '';
  if (typeof isMobileMode === 'function' && isMobileMode()) {
    phoneOpenScreen('cmd');
  } else {
    showScreen('cmd');
  }
}
// Picking any screen from the "More" overlay closes it and returns to that screen.
document.querySelectorAll('.sidebar .nav-item').forEach(it=>it.addEventListener('click',()=>{
  document.body.classList.remove('phone-more-open');
}));
// Keep the Approvals tab badge in sync from the moment the phone loads.
if (isMobileMode() && typeof loadActions === 'function') { try { loadActions(); } catch(e){} }

// Update detection (2026-07-15): the service worker's own cache-invalidation
// logic (obc-frank-shell-${BUILD_ID}, see /frank-sw.js) has always been
// correct, but nothing ever told the browser to actually CHECK for a new
// worker script -- a PWA left open/backgrounded across a deploy could sit on
// a stale cached shell indefinitely with zero signal anything had changed
// (confirmed live: a shipped Fix button silently didn't appear until the app
// was force-quit and reopened). Two additions close that gap: an
// 'updatefound' listener that shows a persistent "tap to refresh" toast once
// a real update (not the first-ever install) finishes installing, and a
// visibilitychange-triggered registration.update() so resuming the app from
// background actively re-checks instead of waiting on the browser's own
// background interval.
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/frank-sw.js', { scope: '/frank' }).then(function(reg){
    if (!reg) return;
    reg.addEventListener('updatefound', function(){
      const installing = reg.installing;
      if (!installing) return;
      installing.addEventListener('statechange', function(){
        if (installing.state === 'installed' && navigator.serviceWorker.controller) {
          showToast('Update available — tap to refresh', 'info', 0);
        }
      });
    });
    document.addEventListener('visibilitychange', function(){
      if (document.visibilityState === 'visible') { reg.update().catch(function(){}); }
    });
  }).catch(function(){});
  // Persistent toasts (ms:0, per above) never auto-dismiss -- clicking one
  // reloads to pick up the new build. Delegated so it works for a toast
  // added after this listener is registered (showToast() appends dynamically).
  document.addEventListener('click', function(e){
    const t = e.target.closest && e.target.closest('.toast');
    if (t && t.textContent.indexOf('tap to refresh') !== -1) { location.reload(); }
  });
}

// ── Real data wiring (Step 2) — session-cookie auth. The browser sends the
// httpOnly session cookie automatically on every same-origin fetch(); no token
// injection into page source. fetchWithTimeout strips any Authorization header
// that call sites may supply and enables credentials:'same-origin' so the
// cookie is included. TOKEN is an empty placeholder kept for call-site compat. ──
const BASE = location.origin;
const WS_BASE = BASE.replace(/^http/, 'ws');
const TOKEN = '';  // placeholder — auth uses session cookie, never the real secret
function fetchWithTimeout(url, opts, ms=12000){
  const c = new AbortController();
  const t = setTimeout(()=>c.abort(), ms);
  const {headers:h, ...rest} = opts || {};
  const filtered = {};
  if (h) Object.entries(h).forEach(([k,v])=>{ if(k.toLowerCase()!=='authorization') filtered[k]=v; });
  return fetch(url,{...rest, headers:filtered, credentials:'same-origin', signal:c.signal}).finally(()=>clearTimeout(t));
}
function authGet(path, ms=15000){
  return fetchWithTimeout(BASE+path, {}, ms);
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
  if (ms) setTimeout(()=>{
    t.classList.add('out');
    setTimeout(()=>t.remove(), 200);
  }, ms);
}

// ── Voice: OpenAI TTS (speech-out) + Whisper (speech-in) — wired to the orb's
// setSpeaking() and the mic/talk-pill click targets further down this file. ──
let _ttsAudio = null;
let _audioUnlocked = false;
// Installed home-screen web app (iOS "Add to Home Screen"), not a Safari tab --
// this matters because of a long-standing WebKit bug (see _setupTtsAnalyser below):
// routing an <audio> element through the Web Audio graph reliably produces silent
// playback in standalone PWAs even though play()/onplay fire normally, while the
// exact same code works fine in a regular Safari tab.
const _isStandalonePWA = window.navigator.standalone === true ||
  (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches);
// iOS Safari (and most mobile browsers) only allow audio.play()/AudioContext.resume()
// to succeed when called synchronously within a real user gesture -- but Frank's TTS
// reply plays much later, after a mic tap -> recording -> STT -> WebSocket -> LLM
// streaming round trip, well outside that window. The fix is the standard mobile
// "unlock" trick: do a real (silent) play+immediate-pause from INSIDE the actual tap
// (see toggleVoiceCapture() below, called before its first await) once per page load --
// once unlocked, later programmatic audio.play() calls succeed for the rest of the
// session, even from async code far removed from any gesture.
function _primeAudioPlayback(){
  try{
    if(!_ttsAudioCtx) _ttsAudioCtx = new (window.AudioContext||window.webkitAudioContext)();
    // Always attempted, even after the first unlock (below) -- unlike a Safari tab, a
    // standalone PWA can get backgrounded/screen-locked and iOS silently re-suspends
    // the AudioContext when that happens. Resuming an already-running context is a
    // harmless no-op, so this costs nothing on the common case and fixes the
    // re-suspend case, which the one-time-only gate below can't.
    if(_ttsAudioCtx.state === 'suspended') _ttsAudioCtx.resume().catch(()=>{});
  }catch(e){}
  if(_audioUnlocked) return;
  _audioUnlocked = true;
  try{
    const unlockEl = new Audio('data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=');
    unlockEl.play().then(()=>unlockEl.pause()).catch(()=>{});
  }catch(e){}
}
// Unlock audio on the FIRST user gesture ANYWHERE — not only the orb/mic tap
// (toggleVoiceCapture) it used to be limited to. On a phone PWA, Frank's reply is
// often reached by TYPING, which never went through that tap, so audio.play() stayed
// gesture-locked and the reply was silent ("still no voice"). These capture-phase
// listeners fire on any tap/key; _primeAudioPlayback() self-guards the one-time
// unlock and, on every later gesture, also re-resumes the AudioContext that iOS
// silently suspends when a standalone PWA is backgrounded/screen-locked. Passive +
// non-once so the re-resume keeps working for the whole session.
['pointerdown','touchend','click','keydown'].forEach(function(ev){
  window.addEventListener(ev, _primeAudioPlayback, {passive:true, capture:true});
});
// Free fallback for when OpenAI TTS is unavailable (e.g. quota exhausted) — uses the
// browser's own speechSynthesis, no API key, no cost. Works on iOS Safari/PWA (unlike
// SpeechRecognition/listening, which is why only speaking gets a fallback, not the mic).
function _speakWithBrowserFallback(text, opts){
  // This is the LAST resort after both the primary TTS engine (OpenAI or local
  // Piper) and audio playback itself have already failed silently upstream — so
  // every failure branch here is the true end of the line for this reply. Toast
  // once instead of leaving the reply spoken-but-silent with zero explanation
  // (the mobile "no sound at all" symptom this was added to fix).
  // `opts` (2026-07-16, optional, additive -- see speakText()) lets a caller like
  // testVoicePlayback() observe the real terminal outcome instead of just "no
  // error was thrown"; every existing call site that omits it behaves exactly as
  // before.
  if(!('speechSynthesis' in window)){
    setSpeaking(false);
    showToast("Couldn't play voice reply — see the text above", 'err');
    if(opts && opts.onFailure) opts.onFailure('no speechSynthesis support in this browser');
    return;
  }
  try {
    window.speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(text);
    u.onstart = () => { setSpeaking(true, true); if(opts && opts.onFallbackStart) opts.onFallbackStart(); };
    u.onend = () => setSpeaking(false, true);
    u.onerror = () => {
      setSpeaking(false, true);
      showToast("Couldn't play voice reply — see the text above", 'err');
      if(opts && opts.onFailure) opts.onFailure('speechSynthesis playback error');
    };
    window.speechSynthesis.speak(u);
  } catch(err){
    setSpeaking(false);
    showToast("Couldn't play voice reply — see the text above", 'err');
    if(opts && opts.onFailure) opts.onFailure(err && err.message);
  }
}
// ── Local offline TTS (Piper-web, fully self-hosted — no CDN). This is the default
// speech-out path; OpenAI TTS only runs when the Premium voice toggle is on. ──
let _piperSessionPromise = null;
const _PIPER_VOICE_ID = 'en_US-amy-medium';
function _loadPiperSession(){
  if(_piperSessionPromise) return _piperSessionPromise;
  const talkSubEl = document.getElementById('talk-sub');
  _piperSessionPromise = import('/static/vendor/piper-tts-web/piper-tts-web.js').then(mod => {
    return mod.TtsSession.create({
      voiceId: _PIPER_VOICE_ID,
      wasmPaths: {
        onnxWasm: {
          mjs: '/static/vendor/onnxruntime-web/ort-wasm-simd-threaded.mjs',
          wasm: '/static/vendor/onnxruntime-web/ort-wasm-simd-threaded.wasm'
        },
        piperWasm: '/static/vendor/piper-wasm/piper_phonemize.wasm',
        piperData: '/static/vendor/piper-wasm/piper_phonemize.data'
      },
      progress: (p) => {
        if(!talkSubEl || !_voiceRecording) return;
        talkSubEl.textContent = 'Setting up offline voice…';
      }
    });
  });
  _piperSessionPromise.catch(() => { _piperSessionPromise = null; });
  return _piperSessionPromise;
}
async function _speakLocalPiper(text){
  const session = await _loadPiperSession();
  return await session.predict(text);
}
// ── Real audio-reactive amplitude for the orb (both TTS paths above produce a blob
// played through this function). A fresh AnalyserNode is wired per Audio element since
// createMediaElementSource() can only ever be called once per element. Mirrors the
// existing mic-input AnalyserNode pattern used for silence detection further down —
// same technique, different source. Wrapped defensively: any failure here (no
// AudioContext, called twice, autoplay-blocked) leaves _ttsAnalyser null and
// currentVoiceAmp() falls back to the old synthetic pulse — it never breaks playback
// itself, since audio.play() below doesn't depend on this succeeding. ──
let _ttsAudioCtx = null, _ttsAnalyser = null, _ttsAnalyserBuf = null;
function _setupTtsAnalyser(audioEl){
  _ttsAnalyser = null;
  // Known WebKit bug (still present in current iOS): createMediaElementSource
  // reliably produces SILENT audio in an installed standalone PWA (added to Home
  // Screen), even though audio.play()/onplay fire normally -- the exact "no error,
  // just no sound" symptom reported 2026-07-10. It's fine in a regular Safari tab.
  // Skip the Web Audio routing entirely in that mode and just let the <audio>
  // element play on its own output -- currentVoiceAmp() already falls back to a
  // synthetic pulse when _ttsAnalyser is null, so the orb still animates, it just
  // isn't driven by real amplitude in this mode. Guaranteed audible sound wins.
  if(_isStandalonePWA) return;
  try{
    if(!_ttsAudioCtx) _ttsAudioCtx = new (window.AudioContext||window.webkitAudioContext)();
    if(_ttsAudioCtx.state === 'suspended') _ttsAudioCtx.resume().catch(()=>{});
    const source = _ttsAudioCtx.createMediaElementSource(audioEl);
    const analyser = _ttsAudioCtx.createAnalyser();
    analyser.fftSize = 256;
    // Route through the analyser AND on to speakers — createMediaElementSource silently
    // reroutes ALL of this element's audio into the Web Audio graph, so skipping the
    // destination connection here would make Frank's voice go silent.
    source.connect(analyser);
    analyser.connect(_ttsAudioCtx.destination);
    _ttsAnalyser = analyser;
    _ttsAnalyserBuf = new Uint8Array(analyser.fftSize);
  }catch(e){
    _ttsAnalyser = null;
  }
}
function _playTtsBlob(blob, fallbackText, opts){
  if(_ttsAudio){ _ttsAudio.pause(); _ttsAudio = null; }
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  _ttsAudio = audio;
  _setupTtsAnalyser(audio);
  audio.onplay = () => { setSpeaking(true); if(opts && opts.onPlaying) opts.onPlaying(); };
  audio.onended = () => { setSpeaking(false); URL.revokeObjectURL(url); };
  audio.onerror = () => { setSpeaking(false); URL.revokeObjectURL(url); };
  audio.play().catch((err)=>{
    if(opts && opts.onBlocked) opts.onBlocked(err);
    _speakWithBrowserFallback(fallbackText, opts);
  });
}
// speakText(text, opts) — opts (2026-07-16, optional) is a purely-additive
// callback contract used by testVoicePlayback() (Settings "Test Voice" button)
// to observe the REAL outcome of this exact code path instead of a separate,
// fake implementation. Every existing unconditional call site (auto-speak on a
// finished chat reply, the WS 'speak' push) omits opts and behaves exactly as
// before. Contract: onPremiumNotConfigured() -- the specific 503 case;
// onEngineError(engine, err) -- Piper failed to load, or the premium POST
// itself threw/timed out; onBlocked(err) -- the browser rejected the primary
// engine's audio.play(); onPlaying()/onFallbackStart() -- terminal SUCCESS
// (primary engine or browser speechSynthesis audibly started); onFailure(reason)
// -- terminal failure, the same moment the existing generic toast already fires.
function speakText(text, opts){
  if(!text) return;
  if(_isPremiumVoice()){
    fetchWithTimeout(BASE+'/api/voice/speak', {
      method:'POST',
      headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({text})
    }, 20000).then(r=>{
      if(!r.ok){
        if(r.status === 503 && opts && opts.onPremiumNotConfigured) opts.onPremiumNotConfigured();
        throw new Error('speak failed: '+r.status);
      }
      return r.blob();
    }).then(blob=>_playTtsBlob(blob, text, opts)).catch((err)=>{
      if(opts && opts.onEngineError) opts.onEngineError('premium', err);
      _speakWithBrowserFallback(text, opts);
    });
    return;
  }
  _speakLocalPiper(text).then(blob=>_playTtsBlob(blob, text, opts)).catch((err)=>{
    if(opts && opts.onEngineError) opts.onEngineError('piper', err);
    _speakWithBrowserFallback(text, opts);
  });
}
// ── Test Voice (Settings, 2026-07-16) — exercises the EXACT speakText() path a
// real chat reply uses (same Piper/premium/browser-fallback branching via the
// opts hooks above), so a pass means "this device/browser can play audio
// through Frank's real voice pipeline right now" -- not a fake green check
// that only proves a function didn't throw. It cannot guarantee every FUTURE
// reply will work too -- iOS can silently re-suspend the AudioContext after
// the PWA is backgrounded (see _primeAudioPlayback()'s comment above), and
// server-side config (OPENAI_API_KEY) could change after this test passes if
// Premium voice gets toggled on later. Do not word this as a guarantee. ──
let _voiceTestInFlight = false;
function testVoicePlayback(){
  const btn = document.getElementById('voice-test-btn');
  const statusEl = document.getElementById('voice-test-status');
  if(!btn || !statusEl || _voiceTestInFlight) return;
  _voiceTestInFlight = true;
  btn.disabled = true;
  statusEl.style.color = 'var(--muted)';
  statusEl.textContent = 'Testing…';
  const notes = [];
  let settled = false;
  const timer = setTimeout(() => finish(false,
    'No audio started within 12s — check your volume/mute switch, or this browser may be blocking autoplay.'), 12000);
  function finish(ok, msg){
    if(settled) return;
    settled = true;
    clearTimeout(timer);
    _voiceTestInFlight = false;
    btn.disabled = false;
    statusEl.style.color = ok ? 'var(--green)' : 'var(--red)';
    statusEl.textContent = msg + (notes.length ? ' (' + notes.join('; ') + ')' : '');
  }
  _primeAudioPlayback();  // the button tap itself counts as the unlock gesture
  speakText("Voice test — if you can hear this, Frank's voice is working.", {
    onPremiumNotConfigured: () => notes.push('Premium voice is on but no OpenAI key is set up on the server'),
    onEngineError: (engine, err) => notes.push((engine==='piper' ? 'offline voice engine failed to load' : 'premium voice request failed') + (err && err.message ? ': '+err.message : '')),
    onBlocked: () => notes.push('browser blocked automatic playback of the primary voice'),
    onPlaying: () => finish(true, '✓ Played out loud just now'),
    onFallbackStart: () => finish(true, "✓ Played out loud just now (used your browser's built-in voice, not Frank's normal voice)"),
    onFailure: (reason) => finish(false, "Couldn't get any audio to play on this device/browser" + (reason ? ' — '+reason : ''))
  });
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
  // Must run synchronously here, before the first await below, so it's still inside
  // the real tap gesture -- see _primeAudioPlayback()'s comment for why.
  _primeAudioPlayback();
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
// ── Local offline STT (Transformers.js + whisper-tiny.en, fully self-hosted — no
// CDN). This is the default speech-in path; OpenAI Whisper only runs when the
// Premium voice toggle is on. ──
let _whisperPipelinePromise = null;
function _loadWhisperPipeline(){
  if(_whisperPipelinePromise) return _whisperPipelinePromise;
  const talkSubEl = document.getElementById('talk-sub');
  _whisperPipelinePromise = import('/static/vendor/transformers/transformers.min.js').then(mod => {
    mod.env.backends.onnx.wasm.wasmPaths = {
      mjs: '/static/vendor/onnxruntime-web/ort-wasm-simd-threaded.mjs',
      wasm: '/static/vendor/onnxruntime-web/ort-wasm-simd-threaded.wasm'
    };
    mod.env.backends.onnx.wasm.proxy = false;
    return mod.pipeline('automatic-speech-recognition', 'Xenova/whisper-tiny.en', {
      progress_callback: (p) => {
        if(!talkSubEl) return;
        if(p.status === 'progress' && p.total){
          talkSubEl.textContent = 'Setting up offline voice (' + Math.round((p.loaded/p.total)*100) + '%)…';
        }
      }
    });
  });
  _whisperPipelinePromise.catch(() => { _whisperPipelinePromise = null; });
  return _whisperPipelinePromise;
}
async function _decodeTo16kMono(blob){
  const arrayBuf = await blob.arrayBuffer();
  const AC = window.AudioContext || window.webkitAudioContext;
  const tmpCtx = new AC();
  const decoded = await tmpCtx.decodeAudioData(arrayBuf);
  tmpCtx.close();
  const offlineCtx = new OfflineAudioContext(1, Math.ceil(decoded.duration * 16000), 16000);
  const src = offlineCtx.createBufferSource();
  src.buffer = decoded;
  src.connect(offlineCtx.destination);
  src.start();
  const rendered = await offlineCtx.startRendering();
  return rendered.getChannelData(0);
}
async function _transcribeLocalWhisper(blob){
  const pipe = await _loadWhisperPipeline();
  const audioData = await _decodeTo16kMono(blob);
  const result = await pipe(audioData);
  return ((result && result.text) || '').trim();
}
function transcribeAndSend(blob){
  const talkSubEl = document.getElementById('talk-sub');
  if(_isPremiumVoice()){
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
    return;
  }
  if(talkSubEl) talkSubEl.textContent = 'Transcribing…';
  _transcribeLocalWhisper(blob).then(text=>{
    if(talkSubEl) talkSubEl.textContent = 'tap to speak';
    if(text){ document.getElementById('chat-input').value = text; sendMsg(); }
    else { _useSpeechRecognitionFallbackText(); }
  }).catch(()=>{
    _useSpeechRecognitionFallbackText();
  });
}

// ── Nav switching — also called directly by in-panel links like
// "View All ›" / "Manage Providers ›", not just the sidebar. ──
// Screen-scoped polling (2026-07-08 performance pass): loadAll() used to fire every
// load*/render* function in the app every 30s regardless of which of the 18 screens was
// actually open. _SCREEN_LOADERS maps each screen to the loaders that populate ONLY that
// screen's content; _GLOBAL_LOADERS covers chrome that lives outside any .screen div
// (header status pill, bottombar relay pill, alert bell) plus two dual-purpose loaders
// that must keep running everywhere: loadQueue() also sets sidebar nav badges, and
// loadShopPerf() also feeds the Executive Briefing panel's cache (reachable from any
// screen), so scoping either to a single screen would make chrome outside that screen
// go stale.
const _SCREEN_LOADERS = {
  cmd: [loadCredentialsAndHealth, loadStarSeller, loadAdsStatus, loadCogsStatus, loadInbox, loadMissionTimeline],
  core: [loadCredentialsAndHealth, loadCoreErrors],
  agents: [],  // covered by the global loadAgents() call below
  tasks: [loadTasks],
  actions: [loadActions],
  calendar: [loadCalendar],
  memory: [loadMemory],
  conversations: [loadConversations],
  kb: [loadKb],
  knowledge: [loadMemory, loadKb],  // merged "Knowledge" screen ("Past conversations" moved to its own #screen-conversations, 2026-07-15)
  tools: [loadTools],
  workflows: [loadWorkflows],
  listings: [() => loadListings(_lastListingState)],
  products: [loadProducts],
  brandkit: [renderBrandKit],
  files: [loadFiles],
  connections: [loadConnections],
  security: [renderSecurityPosture],
  settings: [loadSettingsConnectionsSummary, loadAccountSettings, loadRuntimeSettings],
  studio: [loadStudioVideos],
  create: [loadStudioVideos, loadCreateEngines],  // guided Create flow (reuses studio backends)
};
const _GLOBAL_LOADERS = [
  () => Promise.all([loadAgents(), loadDependencyHealth()]).then(updateSystemStatusPill),
  loadRelayStatus, loadAlerts, checkPersistence, loadQueue, loadShopPerf,
];
let _activeScreen = 'cmd';

// Create-screen chooser: smooth-scroll to the picked tool section (all four tools
// live stacked on the Create screen; the chooser is just friendly wayfinding).
function createGoto(id){ const el = document.getElementById(id); if(el) el.scrollIntoView({behavior:'smooth', block:'start'}); }

// One-tap Quality Check — hits POST /api/produce/qc-check (local, no AI cost) and
// renders the pass/warn/fail rows, the same gates run before publishing anything.
async function qcRunCheck(){
  const pidEl=document.getElementById('qc-pid');
  const btn=document.getElementById('qc-run-btn');
  const out=document.getElementById('qc-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a product code first (e.g. DP1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/qc-check', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid})
    }, 60000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    const s=d.summary||{};
    const badge = d.verdict==='pass' ? '<span style="color:var(--green)">✓ PUBLISH-READY</span>'
      : d.verdict==='warn' ? '<span style="color:var(--gold)">! WARNINGS</span>'
      : d.verdict==='fail' ? '<span style="color:var(--red)">✗ NOT READY</span>'
      : '<span style="color:var(--muted)">No files found</span>';
    let html='<div style="font-weight:600;margin-bottom:8px">'+escHtml(d.pid)+' — '+badge+
      ' <span style="color:var(--muted);font-weight:400;font-size:12px">('+(s.fail||0)+' fail · '+(s.warn||0)+' warn · '+(s.pass||0)+' pass)</span></div>';
    (d.rows||[]).forEach(row=>{
      const col = row.severity==='FAIL'?'var(--red)':row.severity==='WARN'?'var(--gold)':'var(--green)';
      const mark = row.severity==='FAIL'?'✗':row.severity==='WARN'?'!':'✓';
      html+='<div class="hub-listing-meta" style="padding:3px 0;line-height:1.5"><span style="color:'+col+'">'+mark+'</span> '+
        '<b>'+escHtml(row.file)+'</b> — '+escHtml(row.check)+': '+escHtml(row.detail||'')+'</div>';
    });
    out.innerHTML=html;
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Check failed')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}

// One-tap listing-photo set — hits POST /api/produce/listing-photos (local render,
// no AI cost). Renders 10 photos from the planner's real PDF pages into its folder.
async function photoSetRun(){
  const pidEl=document.getElementById('ps-pid');
  const btn=document.getElementById('ps-run-btn');
  const out=document.getElementById('ps-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  const engEl=document.getElementById('ps-engine');
  const engine=(engEl&&engEl.value)||'gemini';
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a planner code first (e.g. DP1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div><div class="hub-listing-meta" style="text-align:center;margin-top:6px">Rendering 10 photos… ~20–40s</div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/listing-photos', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid, engine})
    }, 210000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    let html='<div style="font-weight:600;margin-bottom:6px"><span style="color:var(--green)">✓</span> '+
      escHtml(d.pid)+' — generated '+(d.count||0)+' photo'+((d.count||0)!==1?'s':'')+'</div>';
    (d.photos||[]).forEach(fn=>{ html+='<div class="hub-listing-meta" style="padding:2px 0">🖼️ '+escHtml(fn)+'</div>'; });
    html+='<div style="margin-top:8px"><button class="act-btn" onclick="(typeof phoneOpenScreen===\\'function\\'?phoneOpenScreen:showScreen)(\\'files\\');loadFiles&&loadFiles()">Open in Files →</button></div>';
    out.innerHTML=html;
    showToast('Generated '+(d.count||0)+' listing photos for '+escHtml(d.pid), 'ok');
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Generation failed')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}

// One-tap wall-art print-size ZIP — POST /api/produce/print-zip (local resize, no AI cost).
async function printZipRun(){
  const pidEl=document.getElementById('pz-pid');
  const btn=document.getElementById('pz-run-btn');
  const out=document.getElementById('pz-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a wall-art code first (e.g. WA1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div><div class="hub-listing-meta" style="text-align:center;margin-top:6px">Building print sizes… ~15–40s</div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/print-zip', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid})
    }, 210000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    out.innerHTML='<div style="font-weight:600"><span style="color:var(--green)">✓</span> '+escHtml(d.pid)+
      ' — '+escHtml(d.zip||'print ZIP')+(d.size_mb!=null?(' ('+d.size_mb+' MB)'):'')+'</div>'+
      '<div style="margin-top:8px"><button class="act-btn" onclick="(typeof phoneOpenScreen===\\'function\\'?phoneOpenScreen:showScreen)(\\'files\\');loadFiles&&loadFiles()">Open in Files →</button></div>';
    showToast('Built print ZIP for '+escHtml(d.pid), 'ok');
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Build failed')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}

// One-tap full planner build — POST /api/produce/build-planner. Kicks off a
// background build (base PDFs + AI cover → finalized PDFs); returns immediately.
async function buildPlannerRun(){
  const pidEl=document.getElementById('bp-pid');
  const btn=document.getElementById('bp-run-btn');
  const out=document.getElementById('bp-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  const engEl=document.getElementById('bp-engine');
  const engine=(engEl&&engEl.value)||'gemini';
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a planner code first (e.g. DP1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/build-planner', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid, engine})
    }, 30000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    out.innerHTML='<div style="font-weight:600"><span style="color:var(--gold)">⏳</span> '+escHtml(d.pid)+' — build started</div>'+
      '<div class="hub-listing-meta" style="margin-top:4px;line-height:1.5">'+escHtml(d.message||'')+'</div>'+
      '<div style="margin-top:8px"><button class="act-btn" onclick="(typeof phoneOpenScreen===\\'function\\'?phoneOpenScreen:showScreen)(\\'files\\');loadFiles&&loadFiles()">Check Files →</button></div>';
    showToast('Building '+escHtml(d.pid)+' — check Files in a few minutes', 'ok');
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Build failed to start')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}

// One-tap full sticker-pack build — POST /api/produce/build-sticker-pack. Kicks off
// a background build (themed sheets → strip → segment → ZIP); returns immediately.
async function stickerPackRun(){
  const pidEl=document.getElementById('sp-pid');
  const btn=document.getElementById('sp-run-btn');
  const out=document.getElementById('sp-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  const engEl=document.getElementById('sp-engine');
  const engine=(engEl&&engEl.value)||'gemini';
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a planner code first (e.g. DP1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/build-sticker-pack', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid, engine})
    }, 30000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    out.innerHTML='<div style="font-weight:600"><span style="color:var(--gold)">⏳</span> '+escHtml(d.pid)+' — sticker build started</div>'+
      '<div class="hub-listing-meta" style="margin-top:4px;line-height:1.5">'+escHtml(d.message||'')+'</div>'+
      '<div style="margin-top:8px"><button class="act-btn" onclick="(typeof phoneOpenScreen===\\'function\\'?phoneOpenScreen:showScreen)(\\'files\\');loadFiles&&loadFiles()">Check Files →</button></div>';
    showToast('Building '+escHtml(d.pid)+' stickers — check Files in a few minutes', 'ok');
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Build failed to start')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}

// One-tap FULL product build — POST /api/produce/build-product. Chains
// stickers → planner → photos → QC in the background; returns immediately.
async function buildProductRun(){
  const pidEl=document.getElementById('bx-pid');
  const btn=document.getElementById('bx-run-btn');
  const out=document.getElementById('bx-result');
  const pid=((pidEl&&pidEl.value)||'').trim().toUpperCase();
  const engEl=document.getElementById('bx-engine');
  const engine=(engEl&&engEl.value)||'gemini';
  if(!pid){ if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">Enter a planner code first (e.g. DP1030).</div>'; return; }
  if(btn) btn.disabled=true;
  if(out) out.innerHTML='<div class="hub-spinner"></div>';
  try{
    const r=await fetchWithTimeout(BASE+'/api/produce/build-product', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({pid, engine})
    }, 30000);
    const d=await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail||('HTTP '+r.status));
    if(d.error){ out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(d.error)+'</div>'; return; }
    let steps='';
    (d.steps||[]).forEach((s,i)=>{ steps+='<div class="hub-listing-meta" style="padding:1px 0">'+(i+1)+'. '+escHtml(s)+'</div>'; });
    out.innerHTML='<div style="font-weight:600"><span style="color:var(--gold)">⏳</span> '+escHtml(d.pid)+' — full build started</div>'+
      steps+
      '<div class="hub-listing-meta" style="margin-top:4px;line-height:1.5">'+escHtml(d.message||'')+'</div>'+
      '<div style="margin-top:8px"><button class="act-btn" onclick="(typeof phoneOpenScreen===\\'function\\'?phoneOpenScreen:showScreen)(\\'files\\');loadFiles&&loadFiles()">Check Files →</button></div>';
    showToast('Building all of '+escHtml(d.pid)+' — check Files in a few minutes', 'ok');
  }catch(e){
    if(out) out.innerHTML='<div class="hub-listing-meta" style="color:var(--red)">'+escHtml(e.message||'Build failed to start')+'</div>';
  }finally{ if(btn) btn.disabled=false; }
}
function showScreen(name){
  document.querySelectorAll('.nav-item').forEach(i=>{i.classList.remove('active'); i.removeAttribute('aria-current');});
  const navItem = document.querySelector('.nav-item[data-screen="'+name+'"]');
  if(navItem){ navItem.classList.add('active'); navItem.setAttribute('aria-current','page'); }
  document.querySelectorAll('.screen').forEach(s=>s.classList.remove('active'));
  const el = document.getElementById('screen-'+name);
  if(el) el.classList.add('active');
  _activeScreen = name;
  (_SCREEN_LOADERS[name] || []).forEach(fn => fn());
}
document.querySelectorAll('.nav-item').forEach(item=>{
  item.addEventListener('click',()=>showScreen(item.dataset.screen));
});
// Advanced disclosure: reveals the tucked-away power/engineering screens on demand
// (they're CSS-hidden via body:not(.show-advanced) until then). Same class-toggle
// pattern as toggleControlCenter — nothing is deleted, just shown/hidden.
(function(){
  const t = document.getElementById('nav-advanced-toggle');
  if(!t) return;
  t.addEventListener('click', () => {
    const on = document.body.classList.toggle('show-advanced');
    t.setAttribute('aria-expanded', on ? 'true' : 'false');
    const caret = document.getElementById('nav-advanced-caret');
    if(caret) caret.textContent = on ? '▾' : '▸';
  });
})();
// ── Keyboard activation for every custom role="button" control (sidebar nav,
// icon buttons, quick-reply chips, phone "needs attention" rows, the More list,
// the operator/logout chip, etc.) — Enter/Space triggers .click(), matching
// native <button> behavior. One handler closes the keyboard-activation gap
// across all of them at once (2026-07-08 accessibility review: several already
// had role="button" tabindex="0" but nothing bound Enter/Space to actually
// activate them). ──
document.addEventListener('keydown', e => {
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const t = e.target;
  if (t && t.getAttribute && t.getAttribute('role') === 'button') {
    e.preventDefault();
    t.click();
  }
});

// ── Live Chat — ported verbatim (same protocol/session scheme) from the live Hub's
// chat-wrap at / (main.py). Same /ws/chat endpoint, same CHAT_SESSION localStorage key,
// so a conversation continues seamlessly whether %%OWNER%% is on / or /frank. ──
let ws = null, wsReady = false, pendingMsg = null;
let _wsHeartbeat = null, _wsReconnectTimer = null, _wsRetries = 0, _wsManualClose = false;
let _historyApplied = false;
const CHAT_SESSION = (function(){
  let s = null;
  try { s = localStorage.getItem('chatSession'); } catch(e) {}
  if (!s) {
    s = (window.crypto && crypto.randomUUID) ? crypto.randomUUID()
        : 'sess-' + Date.now() + '-' + Array.from(crypto.getRandomValues(new Uint8Array(8)), b => b.toString(16).padStart(2,'0')).join('');
    try { localStorage.setItem('chatSession', s); } catch(e) {}
  }
  return s;
})();
// ── Developer reveal: opt back into every engineering/infra surface the
// first-time-user simplification hides (see the .show-plumbing/.show-advanced CSS
// near the top). Set localStorage.frankDevMode='1' in the console to see AI Core,
// Agents, Relay/circuit-breaker readouts, API labels, build IDs, the raw activity
// feeds, and every Advanced nav item. Nothing was deleted — this just un-hides it. ──
(function(){
  try { if (localStorage.getItem('frankDevMode') === '1') document.body.classList.add('show-plumbing','show-advanced'); } catch(e) {}
})();
// ── First-login spotlight tour — walks a new user through the real nav, one
// item at a time, with a dimmed cutout ring around each target (see #tour-spot's
// box-shadow trick in the CSS above) and a floating tooltip explaining what
// lives there. target:null steps (intro/outro) reuse the same #tour-spot
// element sized to 0x0 at the viewport center, so the shadow just dims
// uniformly — no separate markup branch needed. Desktop spotlights the
// sidebar (TOUR_STEPS, via showScreen()); mobile spotlights #phone-tabbar's
// 5 tabs instead (MOBILE_TOUR_STEPS, via phoneTab()) since it has no sidebar
// — same #tour-root/#tour-spot/#tour-tooltip engine, just different step data
// and a different "go to this step's destination" call. Replayable anytime
// via the '?' icon in the header (desktop) or "Replay Tutorial" under More
// (mobile) — both just call startTour(). ──
const TOUR_STEPS = [
  { target: null, screen: null,
    title: 'Welcome to %%AGENT_SHORT%%',
    body: '<p>%%AGENT_SHORT%% helps you run your shop. This quick tour shows where everything lives — about 30 seconds.</p><p class="tour-note">Tap Next to start, or Skip to jump right in.</p>' },
  { target: '#orb-desktop-btn', screen: null,
    title: 'Talk to %%AGENT_SHORT%%',
    body: '<p>Click this anytime to open the voice &amp; chat orb — ask a question or give an instruction in plain English.</p>' },
  { target: '.nav-item[data-screen="actions"]', screen: 'actions',
    title: 'Approvals',
    body: '<p>%%AGENT_SHORT%% never changes your shop, files, or posts without your one-tap OK. Anything waiting on you shows up here.</p>' },
  { target: '.nav-item[data-screen="create"]', screen: 'create',
    title: 'Create',
    body: '<p>Generate listing photos, videos, and product files here — everything goes through your one-tap approval before it ever reaches Etsy.</p>' },
  { target: '.nav-item[data-screen="listings"]', screen: 'listings',
    title: 'Your listings',
    body: '<p>Every live Etsy listing, with a Fix button wherever %%AGENT_SHORT%% spots something that needs attention.</p>' },
  { target: '.nav-item[data-screen="knowledge"]', screen: 'knowledge',
    title: 'Knowledge',
    body: '<p>%%AGENT_SHORT%%\\'s memory, past conversations, and the shop\\'s knowledge base — what %%AGENT_SHORT%% remembers and has learned.</p>' },
  { target: '.nav-item[data-screen="products"]', screen: 'products',
    title: 'Products',
    body: '<p>Your product catalog and the status of every digital or physical file behind it.</p>' },
  { target: '.nav-item[data-screen="brandkit"]', screen: 'brandkit',
    title: 'Brand Kit',
    body: '<p>Colors, fonts, and brand assets %%AGENT_SHORT%% uses whenever it generates new content for you.</p>' },
  { target: '.nav-item[data-screen="files"]', screen: 'files',
    title: 'Files',
    body: '<p>Browse shop files, and download a full backup any time.</p>' },
  { target: '.nav-item[data-screen="connections"]', screen: 'connections',
    title: 'Connections',
    body: '<p>Etsy, social, and other integrations — connect a new one or check status here.</p>' },
  { target: '.nav-item[data-screen="settings"]', screen: 'settings',
    title: 'Settings',
    body: '<p>Voice, appearance, and branding preferences. Also one tap away anytime from the <b>⚙</b> icon in the top bar.</p>' },
  { target: '#nav-advanced-toggle', screen: null,
    title: 'Advanced',
    body: '<p>The engineering-level screens (Tasks, Workflows, AI Core, Agents, and more) live under here. Safe to ignore until you need them.</p>' },
  { target: null, screen: null,
    title: "You're all set",
    body: '<p>That\\'s everything. Replay this tour anytime from the <b>?</b> icon in the top bar.</p>' },
];
// Mobile analog — same 5 destinations #phone-tabbar always shows (visible even
// during the full-screen Ask popup), spotlighted via step.ptab + phoneTab()
// instead of step.screen + showScreen().
const MOBILE_TOUR_STEPS = [
  { target: null, ptab: null,
    title: 'Welcome to %%AGENT_SHORT%%',
    body: '<p>%%AGENT_SHORT%% helps you run your shop. This quick tour shows where everything lives — about 20 seconds.</p><p class="tour-note">Tap Next to start, or Skip to jump right in.</p>' },
  { target: '.ptab[data-ptab="ask"]', ptab: null,
    title: 'Ask',
    body: '<p>Tap here anytime to talk to %%AGENT_SHORT%% — ask a question or give an instruction in plain English.</p>' },
  { target: '.ptab[data-ptab="appr"]', ptab: 'appr',
    title: 'Approvals',
    body: '<p>%%AGENT_SHORT%% never changes your shop, files, or posts without your one-tap OK. Anything waiting on you shows up here.</p>' },
  { target: '.ptab[data-ptab="today"]', ptab: 'today',
    title: 'Today',
    body: '<p>Your sales, orders, and views at a glance.</p>' },
  { target: '.ptab[data-ptab="create"]', ptab: 'create',
    title: 'Create',
    body: '<p>Generate listing photos, videos, and product files here — everything goes through your one-tap approval before it ever reaches Etsy.</p>' },
  { target: '.ptab[data-ptab="more"]', ptab: 'more',
    title: 'More',
    body: '<p>Everything else — Your listings, Products, Brand Kit, Knowledge, and the engineering-level screens — lives under here. Safe to ignore until you need it.</p>' },
  { target: null, ptab: null,
    title: "You're all set",
    body: '<p>That\\'s everything. Replay this tour anytime from <b>More → Replay Tutorial</b>.</p>' },
];
let _tourIndex = 0;
let _activeTourSteps = TOUR_STEPS;
function _tourTargetEl(step){ return step.target ? document.querySelector(step.target) : null; }
function renderTourStep(){
  const step = _activeTourSteps[_tourIndex];
  if (!step) return;
  if (step.ptab) phoneTab(step.ptab);
  else if (step.screen) showScreen(step.screen);
  const spot = document.getElementById('tour-spot');
  const tip = document.getElementById('tour-tooltip');
  const el = _tourTargetEl(step);
  const rect = el ? el.getBoundingClientRect() : null;
  const pad = 8;
  if (rect) {
    if (rect.top < 0 || rect.bottom > window.innerHeight) el.scrollIntoView({block:'center'});
    const r2 = el.getBoundingClientRect();
    spot.style.left = (r2.left - pad) + 'px';
    spot.style.top = (r2.top - pad) + 'px';
    spot.style.width = (r2.width + pad*2) + 'px';
    spot.style.height = (r2.height + pad*2) + 'px';
  } else {
    spot.style.left = (window.innerWidth/2) + 'px';
    spot.style.top = (window.innerHeight/2) + 'px';
    spot.style.width = '0px';
    spot.style.height = '0px';
  }
  document.getElementById('tour-step-title').innerHTML = step.title;
  document.getElementById('tour-step-body').innerHTML = step.body;
  const dots = document.getElementById('tour-dots');
  dots.innerHTML = _activeTourSteps.map((_, i) => '<span class="dot' + (i === _tourIndex ? ' active' : '') + '"></span>').join('');
  document.getElementById('tour-back-btn').disabled = (_tourIndex === 0);
  document.getElementById('tour-next-btn').textContent = (_tourIndex === _activeTourSteps.length - 1) ? 'Done' : 'Next';
  // Position the tooltip relative to the (possibly re-measured) target rect —
  // prefer right, then left, then below, then above, clamped inside the viewport.
  const tipMargin = 16, viewMargin = 12, tipW = 320;
  requestAnimationFrame(() => {
    const tipH = tip.offsetHeight || 160;
    let left, top;
    const r3 = el ? el.getBoundingClientRect() : null;
    if (r3) {
      if (r3.right + tipMargin + tipW < window.innerWidth) {
        left = r3.right + tipMargin;
        top = r3.top + r3.height/2 - tipH/2;
      } else if (r3.left - tipMargin - tipW > 0) {
        left = r3.left - tipMargin - tipW;
        top = r3.top + r3.height/2 - tipH/2;
      } else if (r3.bottom + tipMargin + tipH < window.innerHeight) {
        left = r3.left;
        top = r3.bottom + tipMargin;
      } else {
        left = r3.left;
        top = r3.top - tipMargin - tipH;
      }
    } else {
      left = window.innerWidth/2 - tipW/2;
      top = window.innerHeight/2 - tipH/2;
    }
    left = Math.min(Math.max(left, viewMargin), window.innerWidth - tipW - viewMargin);
    top = Math.min(Math.max(top, viewMargin), window.innerHeight - tipH - viewMargin);
    tip.style.left = left + 'px';
    tip.style.top = top + 'px';
  });
}
function endTour(markSeen){
  const root = document.getElementById('tour-root');
  if (root) root.style.display = 'none';
  if (markSeen) { try { localStorage.setItem('frankWelcomeSeen', '1'); } catch(e) {} }
}
function tourNext(){
  if (_tourIndex >= _activeTourSteps.length - 1) { endTour(true); return; }
  _tourIndex++;
  renderTourStep();
}
function tourBack(){
  if (_tourIndex <= 0) return;
  _tourIndex--;
  renderTourStep();
}
function tourSkip(){ endTour(true); }
function startTour(){
  _activeTourSteps = isMobileMode() ? MOBILE_TOUR_STEPS : TOUR_STEPS;
  openControlCenter();
  _tourIndex = 0;
  const root = document.getElementById('tour-root');
  if (root) root.style.display = 'block';
  renderTourStep();
}
window.addEventListener('resize', () => {
  const root = document.getElementById('tour-root');
  if (root && root.style.display === 'block') renderTourStep();
});
document.addEventListener('keydown', function(e){
  const root = document.getElementById('tour-root');
  if (!root || root.style.display !== 'block') return;
  if (e.key === 'Escape') tourSkip();
  else if (e.key === 'ArrowRight') tourNext();
  else if (e.key === 'ArrowLeft') tourBack();
});
(function(){
  let seen = false;
  try { seen = !!localStorage.getItem('frankWelcomeSeen'); } catch(e) {}
  if (!seen) startTour();
})();

// ── Floating "back to top" (2026-07-15, fixed 2026-07-15) — tracks the real
// scroll sources in this app: #phone-body's own internal scroll (native phone
// panels — Today/Approvals/More), and document.body's scroll for mobile
// screens opened via More (NOT window/document.documentElement — the base
// rule `html,body{height:100%;overflow:auto}` (see CSS above) makes <html>
// exactly viewport-height with NO overflow of its own, so <body> ends up as
// its own independent scrolling box, decoupled from window.scrollY/
// window.scrollTo(). Confirmed live: window.scrollY stayed 0 through a whole
// scroll session while document.body.scrollTop moved correctly — the button
// never showed and had nothing to scroll even if clicked. This is why the
// button silently did nothing on a real device despite passing local tests
// (those only ever scrolled the phone-panel path, never a More-opened
// screen). Desktop's fixed 1440x900 stage triggers neither (each panel
// scrolls internally, .screen{overflow:hidden}), so the button naturally
// never appears there — no separate is-mobile gate needed. ──
const _BACK_TO_TOP_THRESHOLD = 400;
function _isPastBackToTopThreshold(){
  if (document.body.scrollTop > _BACK_TO_TOP_THRESHOLD) return true;
  const pb = document.getElementById('phone-body');
  return !!(pb && pb.scrollTop > _BACK_TO_TOP_THRESHOLD);
}
function _updateBackToTopVisibility(){
  const btn = document.getElementById('back-to-top-btn');
  if (btn) btn.classList.toggle('show', _isPastBackToTopThreshold());
}
function backToTop(){
  document.body.scrollTo({top: 0, behavior: 'smooth'});
  const pb = document.getElementById('phone-body');
  if (pb) pb.scrollTo({top: 0, behavior: 'smooth'});
}
document.body.addEventListener('scroll', _updateBackToTopVisibility, {passive: true});
(function(){
  const pb = document.getElementById('phone-body');
  if (pb) pb.addEventListener('scroll', _updateBackToTopVisibility, {passive: true});
})();
// Switching screens/tabs can leave a prior scroll position behind (e.g. a
// showScreen() call doesn't reset the scroll) -- re-check after any nav so
// the button doesn't linger visible-but-stale on a freshly-opened short page.
const _origShowScreen = showScreen;
showScreen = function(name){ _origShowScreen(name); _updateBackToTopVisibility(); };

// ── Premium voice toggle — OpenAI Whisper/TTS stay dormant until this is on.
// Default OFF (absent key reads as off). Local offline WASM engines are the
// default voice path; this only opts back into the paid OpenAI endpoints. ──
function _isPremiumVoice() {
  try { return localStorage.getItem('frankPremiumVoice') === '1'; } catch(e) { return false; }
}
function _setPremiumVoice(on) {
  try { localStorage.setItem('frankPremiumVoice', on ? '1' : '0'); } catch(e) {}
  document.querySelectorAll('.premium-voice-cb').forEach(cb => { cb.checked = on; });
}
(function(){
  document.querySelectorAll('.premium-voice-cb').forEach(cb => {
    cb.checked = _isPremiumVoice();
    cb.addEventListener('change', () => {
      _setPremiumVoice(cb.checked);
      if (cb.checked) _verifyPremiumVoiceConfigured();
    });
  });
})();
// _verifyPremiumVoiceConfigured() (2026-07-16) — Premium voice silently 503s
// on every reply if OPENAI_API_KEY isn't set server-side (falls through to the
// browser-speech fallback with just a generic toast, no specific reason). Runs
// right when the toggle is switched ON, and also from loadSettingsConnectionsSummary()
// on every Settings-screen open (catches a toggle already stuck ON from an
// earlier session/device, before it ever gets a chance to fail on a real reply).
// Shares the same revert-and-explain behavior as the reactive backstop wired
// into speakText()'s two automatic call sites via _autoSpeakOpts() below.
async function _verifyPremiumVoiceConfigured(cred){
  if (!_isPremiumVoice()) return;
  try{
    if (!cred) { const r = await authGet('/api/credentials/status', 8000); cred = await r.json(); }
    if (!(cred && cred.openai && cred.openai.api_key)) {
      _setPremiumVoice(false);
      showToast("Premium voice needs an OpenAI API key that isn't set up yet — turned it off, using the free built-in voice instead.", 'err', 7000);
    }
  }catch(e){ /* status check itself failed; leave the toggle as-is -- the
                reactive backstop in speakText()'s opts still protects real
                playback the next time a reply is actually spoken. */ }
}
function _autoSpeakOpts(){
  return {
    onPremiumNotConfigured: () => {
      _setPremiumVoice(false);
      showToast("Premium voice needs an OpenAI API key that isn't set up yet — turned it off, using the free built-in voice instead.", 'err', 7000);
    }
  };
}
// ── Color theme — per-device display preference, so localStorage (not the
// backend) is the right persistence layer. Default 'cyan' matches the
// original :root values, applied via no class on <html>. ──
const _UI_THEMES = [
  {name:'default', label:'Studio Warm',   bg:'#1a1420', accent:'#f2a0b5'},
  {name:'light',   label:'Day Mode',      bg:'#edf1f5', accent:'#1a8a9a'},
  {name:'purple',  label:'Dark Purple',   bg:'#0c0714', accent:'#9b5de5'},
  {name:'charcoal',label:'Warm Charcoal', bg:'#13100a', accent:'#e8b84a'},
  {name:'sakura',  label:'Sakura',        bg:'#140a10', accent:'#f4a7b9'},
  {name:'matcha',  label:'Matcha',        bg:'#0b120c', accent:'#8bc34a'},
  {name:'ocean',   label:'Ocean Teal',    bg:'#07120f', accent:'#3ad6c8'},
  {name:'kawaii',  label:'Midnight Kawaii',bg:'#0d0a1a', accent:'#00e5ff'},
];
function _getTheme() {
  try { return localStorage.getItem('frankTheme') || 'default'; } catch(e) { return 'default'; }
}
function _setTheme(name) {
  try { localStorage.setItem('frankTheme', name); } catch(e) {}
  _UI_THEMES.forEach(t => document.documentElement.classList.remove('theme-'+t.name));
  if (name !== 'default') document.documentElement.classList.add('theme-'+name);
  _renderThemeSwatches();
}
function _renderThemeSwatches() {
  const row = document.getElementById('theme-swatch-row');
  if (!row) return;
  const active = _getTheme();
  row.innerHTML = _UI_THEMES.map(t =>
    '<button class="act-btn" style="display:flex;align-items:center;gap:7px;'+
    (t.name === active ? 'border-color:var(--cyan);color:var(--cyan2)' : '')+
    '" onclick="_setTheme(\\''+t.name+'\\')">'+
    '<span style="width:20px;height:14px;border-radius:4px;flex-shrink:0;display:inline-block;overflow:hidden;border:1px solid rgba(255,255,255,.15)">'+
      '<span style="display:block;width:50%;height:100%;background:'+t.bg+';float:left"></span>'+
      '<span style="display:block;width:50%;height:100%;background:'+t.accent+';float:left"></span>'+
    '</span>'+
    t.label+(t.name === active ? ' ✓' : '')+'</button>'
  ).join('');
}
(function(){
  _setTheme(_getTheme());
})();
// ── My Account — durable across devices, so this is backed by /api/account
// (a real DB row) rather than localStorage, unlike the theme preference above. ──
async function loadAccountSettings(){
  const nameEl = document.getElementById('account-name');
  if(!nameEl) return;
  try{
    const r = await authGet('/api/account');
    const d = await r.json();
    nameEl.value = d.name || '';
    document.getElementById('account-email').value = d.email || '';
    document.getElementById('account-phone').value = d.phone || '';
    document.getElementById('account-timezone').value = d.timezone || '';
  }catch(e){
    const statusEl = document.getElementById('account-save-status');
    if(statusEl) statusEl.textContent = 'Could not load saved account info';
  }
}
async function saveAccountSettings(){
  const statusEl = document.getElementById('account-save-status');
  const payload = {
    name: document.getElementById('account-name').value,
    email: document.getElementById('account-email').value,
    phone: document.getElementById('account-phone').value,
    timezone: document.getElementById('account-timezone').value,
  };
  if(statusEl) statusEl.textContent = 'Saving…';
  try{
    const r = await fetchWithTimeout(BASE+'/api/account', {
      method:'POST',
      headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    }, 15000);
    await r.json();
    if(statusEl) statusEl.textContent = 'Saved ✓';
    showToast('Account info saved', 'ok');
  }catch(e){
    if(statusEl) statusEl.textContent = 'Save failed: '+e.message;
  }
}
async function changeMyPassword(){
  const statusEl = document.getElementById('pw-change-status');
  const cur = document.getElementById('pw-current').value;
  const pw1 = document.getElementById('pw-new').value;
  const pw2 = document.getElementById('pw-confirm').value;
  if(!cur){ if(statusEl){statusEl.style.color='var(--red)';statusEl.textContent='Enter your current password';} return; }
  if(pw1.length < 8){ if(statusEl){statusEl.style.color='var(--red)';statusEl.textContent='New password must be at least 8 characters';} return; }
  if(pw1 !== pw2){ if(statusEl){statusEl.style.color='var(--red)';statusEl.textContent='New passwords do not match';} return; }
  if(statusEl){statusEl.style.color='var(--muted)';statusEl.textContent='Changing…';}
  try{
    const r = await fetchWithTimeout(BASE+'/api/me/change-password', {
      method:'POST',
      headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({current_password: cur, new_password: pw1})
    }, 15000);
    const d = await r.json().catch(()=>({}));
    if(!r.ok){ if(statusEl){statusEl.style.color='var(--red)';statusEl.textContent = d.detail || 'Change failed';} return; }
    document.getElementById('pw-current').value = '';
    document.getElementById('pw-new').value = '';
    document.getElementById('pw-confirm').value = '';
    showToast('Password changed — signing you out…', 'ok');
    setTimeout(()=>{ window.location.href = '/login'; }, 1200);
  }catch(e){
    if(statusEl){statusEl.style.color='var(--red)';statusEl.textContent = 'Network error';}
  }
}
// ── Runtime settings — agent name + AI engines (backed by /api/settings, DB) ──
async function loadRuntimeSettings(){
  const nameEl = document.getElementById('setting-agent-name');
  if(!nameEl) return;
  try{
    const r = await authGet('/api/settings');
    const d = await r.json();
    nameEl.value = d.agent_name || '';
    const ve = document.getElementById('setting-video-engine');
    const ie = document.getElementById('setting-image-engine');
    if(ve && d.video_engine) ve.value = d.video_engine;
    if(ie && d.image_engine) ie.value = d.image_engine;
    window._brandMarkDataUrl = d.brand_mark_data_url || null;
    renderBrandMarkPreview();
    if(window._brandMarkDataUrl && typeof applyBrandMarkToOrb === 'function') applyBrandMarkToOrb(window._brandMarkDataUrl);
  }catch(e){/* leave placeholders */}
}
function renderBrandMarkPreview(){
  // Draws into every brand-mark preview canvas on the page (Settings' #brand-mark-preview
  // AND Brand Kit's #brandkit-mark-preview) -- both share the .brand-mark-canvas class so
  // this single function keeps both in sync without either screen knowing about the other.
  document.querySelectorAll('.brand-mark-canvas').forEach(_drawBrandMarkInto);
}
function _drawBrandMarkInto(cv){
  const ctx = cv.getContext('2d');
  ctx.clearRect(0,0,cv.width,cv.height);
  if(!window._brandMarkDataUrl){
    ctx.fillStyle = 'rgba(242,160,181,0.25)';
    ctx.font = '28px sans-serif'; ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText('⬡', cv.width/2, cv.height/2+2);
    return;
  }
  const img = new Image();
  img.onload = () => {
    ctx.clearRect(0,0,cv.width,cv.height);
    const s = Math.min(cv.width/img.width, cv.height/img.height);
    const w = img.width*s, h = img.height*s;
    ctx.drawImage(img, (cv.width-w)/2, (cv.height-h)/2, w, h);
  };
  img.src = window._brandMarkDataUrl;
}
async function uploadBrandMark(){
  const fileEl = document.getElementById('brand-mark-file');
  const statusEl = document.getElementById('brand-mark-status');
  const f = fileEl && fileEl.files && fileEl.files[0];
  if(!f){ if(statusEl) statusEl.textContent = 'Choose an image first'; return; }
  if(statusEl) statusEl.textContent = 'Uploading…';
  try{
    const r = await fetchWithTimeout(BASE+'/api/settings/brand-mark', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body: f
    }, 30000);
    const d = await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail || ('HTTP '+r.status));
    window._brandMarkDataUrl = d.data_url;
    renderBrandMarkPreview();
    if(typeof applyBrandMarkToOrb === 'function') applyBrandMarkToOrb(d.data_url);
    if(statusEl) statusEl.textContent = 'Uploaded ✓';
    showToast('Orb updated with your image', 'ok');
  }catch(e){
    if(statusEl) statusEl.textContent = 'Upload failed: '+e.message;
  }
}
async function resetBrandMark(){
  const ok = await _postSettings({brand_mark_data_url:null}, 'brand-mark-status', 'Orb reset to default');
  if(!ok) return;
  window._brandMarkDataUrl = null;
  renderBrandMarkPreview();
  if(typeof resetOrbToDefault === 'function') resetOrbToDefault();
}
async function _postSettings(payload, statusId, okMsg){
  const statusEl = document.getElementById(statusId);
  if(statusEl) statusEl.textContent = 'Saving…';
  try{
    const r = await fetchWithTimeout(BASE+'/api/settings', {
      method:'POST',
      headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    }, 15000);
    if(!r.ok){ const e = await r.json().catch(()=>({})); throw new Error(e.detail||('HTTP '+r.status)); }
    await r.json();
    if(statusEl) statusEl.textContent = 'Saved ✓';
    showToast(okMsg, 'ok');
    return true;
  }catch(e){
    if(statusEl) statusEl.textContent = 'Save failed: '+e.message;
    return false;
  }
}
function saveBranding(){
  const name = (document.getElementById('setting-agent-name').value||'').trim();
  if(!name){ document.getElementById('branding-status').textContent = 'Enter a name first'; return; }
  _postSettings({agent_name:name}, 'branding-status', 'Agent name saved — reload to see it everywhere');
}
function saveEngines(){
  const ve = document.getElementById('setting-video-engine');
  const ie = document.getElementById('setting-image-engine');
  if(!ve || !ie) return;  // both selects live on the Create screen; guard if absent
  _postSettings({ video_engine: ve.value, image_engine: ie.value }, 'engines-status', 'Engine updated');
}
// Populate the Create-screen engine dropdowns with the currently-saved engines.
// (loadRuntimeSettings early-returns off the Settings screen, so Create needs its
// own tiny loader — see _SCREEN_LOADERS.create.)
async function loadCreateEngines(){
  const ie = document.getElementById('setting-image-engine');
  const ve = document.getElementById('setting-video-engine');
  if(!ie && !ve) return;
  try{
    const r = await authGet('/api/settings');
    const d = await r.json();
    if(ie && d.image_engine) ie.value = d.image_engine;
    if(ve && d.video_engine) ve.value = d.video_engine;
  }catch(e){/* leave defaults */}
}
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
// ── Global topbar search — client-side lookup over data already loaded into the
// page (no new endpoint). First match wins, in listings → tasks → tools → KB
// order, and jumps straight to it. ──
function runGlobalSearch(raw) {
  const q = (raw || '').trim().toLowerCase();
  if (!q) return;
  const listing = (_listings || []).find(l => (l.title || '').toLowerCase().includes(q));
  if (listing) {
    showScreen('listings');
    toggleListingDetail(listing.listing_id);
    return;
  }
  const tasksCache = cacheGet('tasks');
  const task = ((tasksCache && tasksCache.data && tasksCache.data.todos) || [])
    .find(t => (t.text || '').toLowerCase().includes(q));
  if (task) {
    showScreen('tasks');
    return;
  }
  const toolsCache = cacheGet('tools');
  const tool = ((toolsCache && toolsCache.data && toolsCache.data.tools) || [])
    .find(t => (t.name || '').toLowerCase().includes(q) || (t.description || '').toLowerCase().includes(q));
  if (tool) {
    showScreen('tools');
    return;
  }
  const doc = (_kbDocs || []).find(d => (d.filename || '').toLowerCase().includes(q));
  if (doc) {
    showScreen('kb');
    openKbDoc(doc.filename);
    return;
  }
  showToast('No matches for "' + raw + '"', 'info');
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
      if (finalText) speakText(finalText, _autoSpeakOpts());
    }
    // Backend sends {type:'speak'} when the agent explicitly calls the local_speak
    // tool (main.py). Without this branch that audio was silently dropped -- the
    // handler only knew pong/history/tool/chunk/done/error -- so an agent-initiated
    // spoken line never played. Route it through the same TTS path as a normal reply.
    else if (d.type === 'speak') { if (d.text) speakText(d.text, _autoSpeakOpts()); }
    else if (d.type === 'error') { _clearStreaming(); addBubble('⚠️ ' + d.content, 'bot'); }
  };
  ws.onerror = () => { _clearStreaming(); };
  ws.onclose = e => {
    wsReady = false; ws = null; _stopHeartbeat();
    _clearStreaming();
    if (e.code === 4001) { addBubble('Auth failed — reload to reconnect', 'bot'); return; }
    if (!_wsManualClose) {
      _wsRetries = Math.min(_wsRetries + 1, 5);
      if (_wsRetries >= 5) {
        showToast('Connection lost. Refresh the page.', 'error', 0);
      } else {
        showToast('Reconnecting… (' + _wsRetries + '/5)', 'warn');
      }
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
function sendMsg(sourceId) {
  const inp = document.getElementById(sourceId || 'chat-input');
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
document.getElementById('orb-chat-input').addEventListener('keydown', e => { if(e.key==='Enter') sendMsg('orb-chat-input'); });
document.getElementById('quick-chat-input').addEventListener('keydown', e => { if(e.key==='Enter') sendQuickChat(); });
initWS();

// ── Agents — real data from /api/agents/status (live-status registry).
// Every tile is a real running loop; status reflects its actual last heartbeat
// (started/running/ok/error, or offline for the local relay) — never invented.
// (Corrected 2026-07-15: this used to also say "or honestly marked not_built",
// leftover from an earlier state — every tile has hardcoded built:true today.) ──
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
    if(health.build){
      const orbVer = document.getElementById('orb-build-ver');
      if(orbVer) orbVer.textContent = 'Build '+health.build;
      const setVer = document.getElementById('settings-build-ver');
      if(setVer) setVer.textContent = 'Build '+health.build;
    }
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

// ── AI Core actions — real writes to /api/core/* ──
async function coreRefreshEtsyToken(){
  const btn = document.getElementById('core-btn-refresh-token');
  if(btn){ btn.disabled = true; btn.textContent = '🔄 Refreshing…'; }
  try{
    const r = await fetchWithTimeout(BASE+'/api/core/refresh-etsy-token', {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    const d = await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail || 'HTTP '+r.status);
    showToast('Etsy token refreshed successfully.');
    loadCredentialsAndHealth();
  }catch(e){
    showToast('Refresh failed: '+(e.message||e), 'err');
  }finally{
    if(btn){ btn.disabled = false; btn.textContent = '🔄 Refresh Etsy Token Now'; }
  }
}
async function coreRedeploy(){
  if(!confirm('Redeploy the live server now? This causes a brief real outage (~30-60s) while it restarts.')) return;
  const btn = document.getElementById('core-btn-redeploy');
  if(btn){ btn.disabled = true; btn.textContent = '⟳ Redeploying…'; }
  try{
    const r = await fetchWithTimeout(BASE+'/api/core/redeploy', {method:'POST', headers:{Authorization:'Bearer '+TOKEN}}, 20000);
    const d = await r.json().catch(()=>({}));
    if(!r.ok) throw new Error(d.detail || 'HTTP '+r.status);
    showToast('Redeploy triggered — the server will be briefly unreachable while it restarts.');
  }catch(e){
    showToast('Redeploy failed: '+(e.message||e), 'err');
    if(btn){ btn.disabled = false; btn.textContent = '⟳ Redeploy Server'; }
  }
}
async function loadCoreErrors(){
  const el = document.getElementById('core-errors');
  if(!el) return;
  try{
    const r = await authGet('/api/core/recent-errors?limit=20', 15000);
    const d = await r.json();
    if(!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const errs = d.errors||[];
    if(!errs.length){
      el.innerHTML = '<div style="font-size:12px;color:var(--muted)">✅ No recent errors.</div>';
      return;
    }
    el.innerHTML = errs.map(function(e){
      const when = new Date(e.ts).toLocaleString('en-US',{month:'short',day:'numeric',hour:'numeric',minute:'2-digit'});
      return '<div style="padding:8px 0;border-bottom:1px solid var(--border)">'+
        '<div style="display:flex;justify-content:space-between;gap:8px;font-size:12px;color:var(--muted)">'+
          '<span>'+escHtml(e.actor||'')+' · '+escHtml(e.action_type||'')+'</span><span>'+escHtml(when)+'</span></div>'+
        '<div style="font-size:12px;color:var(--red);margin-top:2px">'+escHtml(String(e.outcome||''))+'</div>'+
        (e.detail?'<div style="font-size:12px;color:var(--text);margin-top:2px">'+escHtml(String(e.detail))+'</div>':'')+
      '</div>';
    }).join('');
  }catch(e){
    el.innerHTML = '<div style="font-size:12px;color:var(--muted)">Could not load: '+escHtml(e.message||'')+'</div>';
  }
}

// ── Shop Performance — real data from /api/analytics + /api/metrics ──
var _miniSparkCounter = 0; // monotonic counter for stable, unique SVG gradient IDs
function _miniSpark(values, color){
  var h = 16;
  values = (values||[]).filter(function(v){ return v!=null && !isNaN(v); });
  if(values.length < 2) return '<div style="height:'+h+'px;display:flex;align-items:center;font-size:8.5px;color:var(--muted)">📈 Accumulating daily data…</div>';
  var W=140,H=h,mn=Math.min.apply(null,values),mx=Math.max.apply(null,values),range=mx-mn||1,pad=2;
  var pts=values.map(function(v,i){return [pad+(i/(values.length-1))*(W-pad*2), H-pad-((v-mn)/range)*(H-pad*2)];});
  var poly=pts.map(function(p){return p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ');
  var area='M'+pts[0][0].toFixed(1)+','+H+' '+pts.map(function(p){return 'L'+p[0].toFixed(1)+','+p[1].toFixed(1);}).join(' ')+' L'+pts[pts.length-1][0].toFixed(1)+','+H+' Z';
  var gid='fsg'+(++_miniSparkCounter);
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
        '<div class="ssc-valrow"><div class="ssc-val" id="shop-rev-30d">'+(lt.revenue_30d!=null?'$'+lt.revenue_30d.toFixed(2):'—')+'</div>'+
        '<div class="ssc-delta">'+_miniDelta(del.revenue_30d,true)+'</div></div>'+
        '<div class="ssc-spark">'+_miniSpark(tr.revenue_30d,'var(--gold)')+'</div></div>'+
      '<div class="shop-spark-card"><div class="ssc-lab">Orders · 30d</div>'+
        '<div class="ssc-valrow"><div class="ssc-val" id="shop-ord-30d">'+(lt.orders_30d!=null?lt.orders_30d:'—')+'</div>'+
        '<div class="ssc-delta">'+_miniDelta(del.orders_30d,false)+'</div></div>'+
        '<div class="ssc-spark">'+_miniSpark(tr.orders_30d,'var(--cyan2)')+'</div></div>';
  }
  const allTimeRev = (m.orders && m.orders.all_time_revenue!=null) ? m.orders.all_time_revenue : null;
  if(chipEl){
    chipEl.innerHTML =
      '<div class="shop-chip"><div class="nm">Listings</div><div class="v" id="shop-listings">'+(lt.active_listings!=null?lt.active_listings:'—')+'</div></div>'+
      '<div class="shop-chip"><div class="nm">Total Sales</div><div class="v" id="shop-total-sales">'+(lt.total_sales!=null?lt.total_sales:'—')+'</div></div>'+
      '<div class="shop-chip"><div class="nm">All-Time Revenue</div><div class="v" id="shop-alltime-rev">'+(allTimeRev!=null?'$'+allTimeRev.toFixed(2):'—')+'</div></div>';
  }
  // Populate expanded panel IDs
  const setEl = (id, val) => { const e = document.getElementById(id); if(e) e.textContent = val; };
  const o = m.orders || {};
  setEl('shop-rev-7d', '$' + (o.revenue_7d||0).toFixed(2));
  setEl('shop-ord-7d', (o.last_7_days||0) + ' orders');
  setEl('shop-rev-today', '$' + (o.today_revenue||0).toFixed(2));
  setEl('shop-ord-today', (o.today_count||0) + ' orders');
  const aov = (o.last_30_days||0) > 0 ? ('$'+((o.revenue_30d||0)/(o.last_30_days||1)).toFixed(2)) : '—';
  setEl('shop-aov', aov);
  setEl('shop-active', (m.shop||{}).active_listing_count||'—');
  const salesEl = document.getElementById('shop-recent-sales');
  if(salesEl && o.recent_sales && o.recent_sales.length){
    salesEl.innerHTML = o.recent_sales.map(s=>{
      const dt = s.ts ? new Date(s.ts*1000).toLocaleDateString('en-US',{month:'short',day:'numeric'}) : '';
      return '<div class="recent-sale-row"><span>'+escHtml(s.title)+'</span><span><span class="recent-sale-amt">$'+s.amount.toFixed(2)+'</span> <span class="recent-sale-date">'+dt+'</span></span></div>';
    }).join('');
  } else if(salesEl){
    salesEl.textContent = 'No recent sales';
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

let _shopExpanded = false;
function toggleShopExpand(){
  _shopExpanded = !_shopExpanded;
  const exp = document.getElementById('shop-expanded');
  const arrow = document.getElementById('shop-expand-arrow');
  if(exp) exp.style.display = _shopExpanded ? 'block' : 'none';
  if(arrow) arrow.textContent = _shopExpanded ? '▲ collapse' : '▼ expand';
}

async function loadStarSeller(){
  const el = document.getElementById('star-seller-body');
  if(!el) return;
  try{
    const r = await authGet('/api/star-seller');
    const d = await r.json();
    const statusLabel = d.status==='on_track' ? 'ON TRACK' : d.status==='at_risk' ? 'AT RISK' : 'BUILDING';
    const statusClass = d.status||'building';
    const ordPct = Math.min(100, ((d.orders_90d||0)/5)*100);
    const revPct = Math.min(100, ((d.revenue_90d||0)/300)*100);
    const ratPct = d.avg_rating ? Math.min(100, ((d.avg_rating-1)/4)*100) : 0;
    const ordOk = (d.orders_90d||0)>=5;
    const revOk = (d.revenue_90d||0)>=300;
    const msgOk = (d.unread_messages||0)===0;
    el.innerHTML =
      '<div class="ss-status '+statusClass+'">'+statusLabel+'</div>'+
      '<div class="ss-row">'+
        '<span class="ss-label">Orders (90d)</span>'+
        '<div class="ss-bar-wrap"><div class="ss-bar '+(ordOk?'':'warn')+'" style="width:'+ordPct+'%"></div></div>'+
        '<span class="ss-val">'+( d.orders_90d||0)+'<span style="color:var(--muted);font-weight:400">/5</span></span>'+
      '</div>'+
      '<div class="ss-row">'+
        '<span class="ss-label">Revenue (90d)</span>'+
        '<div class="ss-bar-wrap"><div class="ss-bar '+(revOk?'':'warn')+'" style="width:'+revPct+'%"></div></div>'+
        '<span class="ss-val">$'+(d.revenue_90d||0).toFixed(0)+'<span style="color:var(--muted);font-weight:400">/$300</span></span>'+
      '</div>'+
      '<div class="ss-row">'+
        '<span class="ss-label">Avg Rating</span>'+
        '<div class="ss-bar-wrap"><div class="ss-bar" style="width:'+ratPct+'%"></div></div>'+
        '<span class="ss-val">'+(d.avg_rating||'—')+' ★</span>'+
      '</div>'+
      '<div class="ss-row">'+
        '<span class="ss-label">On-time Delivery</span>'+
        '<span class="ss-val" style="color:var(--green)">100% ✓</span>'+
      '</div>'+
      '<div class="ss-row">'+
        '<span class="ss-label">Unread Messages</span>'+
        '<span class="ss-val"'+(msgOk?'':' style="color:var(--red)"')+'>'+( d.unread_messages||0)+' '+(msgOk?'✓':'⚠')+'</span>'+
      '</div>';
  }catch(e){
    if(el) el.innerHTML='<div style="color:var(--muted);font-size:11px">⚠ '+escHtml(e.message)+'</div>';
  }
}

// 2026-07-15: Ads/ROAS state used to be indistinguishable from any other
// generic todo — this is its first dedicated read, same visual pattern as
// the Star Seller card above (.ss-status/.ss-row/.ss-bar reused, not
// duplicated). Etsy's public API has no ads-performance endpoint, so this
// only ever reflects what Scott has manually logged via _log_ad_spend.
const _ADS_STATUS_LABEL = {
  ok: 'ON TRACK', kill_signal: 'KILL SIGNAL', low_roas: 'LOW ROAS',
  scale_eligible: 'SCALE ELIGIBLE', stale_log: 'LOG IS STALE',
};
const _ADS_STATUS_CLASS = {
  ok: 'on_track', kill_signal: 'at_risk', low_roas: 'at_risk',
  scale_eligible: 'building', stale_log: 'building',
};
async function loadAdsStatus(){
  const el = document.getElementById('ads-status-body');
  if(!el) return;
  try{
    const r = await authGet('/api/ads-status');
    const d = await r.json();
    if (!d.used) {
      el.innerHTML = '<div class="ss-row"><span class="ss-label">Etsy Ads has never been used — a $3-5/day test budget is a growth lever available anytime (CLAUDE.md\\'s Ads Strategy).</span></div>';
      return;
    }
    const label = _ADS_STATUS_LABEL[d.status] || d.status;
    const cls = _ADS_STATUS_CLASS[d.status] || 'building';
    el.innerHTML =
      '<div class="ss-status '+cls+'">'+escHtml(label)+'</div>'+
      '<div class="ss-row"><span class="ss-label">Spend (7d)</span><span class="ss-val">$'+d.week_spend.toFixed(2)+'</span></div>'+
      '<div class="ss-row"><span class="ss-label">Revenue (7d)</span><span class="ss-val">$'+d.week_revenue.toFixed(2)+'</span></div>'+
      '<div class="ss-row"><span class="ss-label">ROAS (this month)</span><span class="ss-val">'+(d.have_monthly_verdict ? d.month_roas+'x' : 'building — '+d.month_roas+'x so far')+'</span></div>'+
      '<div class="ss-row"><span class="ss-label">Last logged</span><span class="ss-val"'+(d.days_since_log>=7?' style="color:var(--red)"':'')+'>'+d.days_since_log+'d ago</span></div>';
  }catch(e){
    if(el) el.innerHTML='<div style="color:var(--muted);font-size:11px">⚠ '+escHtml(e.message)+'</div>';
  }
}

// Estimate, not real accounting -- see /api/cogs-status's own "note" field
// (also surfaced below as a footer line). Digital COGS assumed $0, physical
// (3D-print) COGS a flat $7.50/unit typical guess, product type guessed from
// title keywords. Etsy fee math (6.5% + 3%+$0.25 + $0.20) is real, not a guess.
const _COGS_LOW_MARGIN_LABEL = 40;
async function loadCogsStatus(){
  const el = document.getElementById('cogs-status-body');
  if(!el) return;
  try{
    const r = await authGet('/api/cogs-status');
    const d = await r.json();
    if (!d.used) {
      el.innerHTML = '<div class="ss-row"><span class="ss-label">No active listings to estimate yet.</span></div>';
      return;
    }
    const marginCls = d.avg_margin_pct >= 60 ? 'on_track' : (d.avg_margin_pct >= 40 ? 'building' : 'at_risk');
    let html =
      '<div class="ss-row"><span class="ss-label">Avg margin (est.)</span><span class="ss-val" style="color:var(--'+(marginCls==='on_track'?'green':marginCls==='at_risk'?'red':'gold')+')">'+d.avg_margin_pct+'%</span></div>'+
      '<div class="ss-row"><span class="ss-label">Recent profit (est.)</span><span class="ss-val">$'+d.total_recent_profit_estimate.toFixed(2)+'</span></div>'+
      '<div class="ss-row"><span class="ss-label">Recent units sold</span><span class="ss-val">'+d.total_recent_units+' <span style="color:var(--muted);font-weight:400">(real, last 100 orders)</span></span></div>'+
      '<div class="ss-row"><span class="ss-label">Active listings</span><span class="ss-val">'+d.listing_count+'</span></div>';
    if ((d.flagged_low_margin||[]).length) {
      html += '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em;margin:8px 0 4px">⚠ Thin margin (est., &lt;'+_COGS_LOW_MARGIN_LABEL+'%)</div>';
      html += d.flagged_low_margin.map(function(f){
        return '<div class="ss-row"><span class="ss-label" title="'+escHtml(f.title)+'">'+escHtml(f.title.length>34?f.title.slice(0,34)+'…':f.title)+'</span><span class="ss-val" style="color:var(--red)">'+f.margin_pct+'%</span></div>';
      }).join('');
    }
    html += '<div style="font-size:10px;color:var(--muted);margin-top:8px;line-height:1.4">'+escHtml(d.note||'')+'</div>';
    el.innerHTML = html;
  }catch(e){
    if(el) el.innerHTML='<div style="color:var(--muted);font-size:11px">⚠ '+escHtml(e.message)+'</div>';
  }
}

async function loadInbox(){
  const el = document.getElementById('inbox-body');
  if(!el) return;
  try{
    const r = await authGet('/api/inbox');
    const d = await r.json();
    const unread = d.unread_count||0;
    const oldestH = d.oldest_unread_hours;
    const urgent = oldestH!=null && oldestH>20;
    let html = '<div class="inbox-msg-bar">';
    html += '<div class="inbox-unread-badge '+(urgent?'urgent':'')+'">'+unread+'</div>';
    html += '<div class="inbox-msg-meta">';
    if(unread===0){
      html += '<strong style="color:var(--green)">Inbox clear ✓</strong><br>No unread messages';
    } else {
      html += '<strong>'+unread+' unread message'+(unread>1?'s':'')+'</strong>';
      if(oldestH!=null) html += '<br><span '+(urgent?'style="color:var(--red)"':'')+'>Oldest: '+oldestH.toFixed(0)+'h ago'+(urgent?' ⚠ Star Seller risk':'')+'</span>';
    }
    html += '</div></div>';
    const reviews = d.recent_reviews||[];
    if(reviews.length){
      html += '<div style="margin-top:6px;font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.06em">Recent Reviews</div>';
      reviews.forEach(rev=>{
        const stars = '★'.repeat(rev.rating)+'☆'.repeat(5-rev.rating);
        html += '<div class="inbox-review"><div class="inbox-review-stars">'+stars+'</div>';
        if(rev.text) html += '<div class="inbox-review-text">'+escHtml(rev.text.slice(0,100))+(rev.text.length>100?'…':'')+'</div>';
        html += '</div>';
      });
    } else {
      html += '<div style="color:var(--muted);font-size:11px;margin-top:8px">No reviews yet</div>';
    }
    el.innerHTML = html;
  }catch(e){
    if(el) el.innerHTML='<div style="color:var(--muted);font-size:11px">⚠ '+escHtml(e.message)+'</div>';
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

// ── Dependency Health — real data from /api/system/dependencies (circuit breakers) ──
const _DEP_LABELS = {etsy_api:'Etsy API', anthropic_api:'Anthropic API', relay:'Local Relay'};
function _renderDependencyHealth(d, el, offlineNote){
  if(!el) return;
  const deps = d.dependencies||[];
  const depHtml = deps.map(dep=>{
    const stateClass = dep.state === 'open' ? 'open' : (dep.state === 'half_open' ? 'half_open' : '');
    const stateLabel = dep.state === 'closed' ? 'HEALTHY' : dep.state === 'half_open' ? 'TESTING' : 'DOWN';
    const failText = dep.consecutive_failures ? ' &middot; '+dep.consecutive_failures+' failures' : '';
    return '<div class="dep-pill '+stateClass+'"><span class="dep-dot"></span>'+
      '<span class="dep-name">'+escHtml(_DEP_LABELS[dep.name]||dep.name)+'</span>'+
      '<span class="dep-state">'+stateLabel+'</span>'+
      '<span class="dep-fail">'+failText+'</span></div>';
  }).join('');
  // Capabilities — optional features that need a key/connection. Green "READY" or
  // amber "NEEDS SETUP · <hint>" so setup gaps are visible, not discovered by trial.
  const caps = d.capabilities||[];
  const capHtml = caps.map(cap=>{
    const ok = !!cap.available;
    const cls = ok ? '' : 'half_open';  // amber = needs setup (not a hard outage)
    const stateLabel = ok ? 'READY' : 'NEEDS SETUP';
    const hint = (!ok && cap.hint) ? ' &middot; '+escHtml(cap.hint) : '';
    return '<div class="dep-pill '+cls+'"><span class="dep-dot"></span>'+
      '<span class="dep-name">'+escHtml(cap.label||cap.key)+'</span>'+
      '<span class="dep-state">'+stateLabel+'</span>'+
      '<span class="dep-fail">'+hint+'</span></div>';
  }).join('');
  const capHeader = caps.length ? '<div style="font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px;margin:10px 0 4px">Capabilities</div>' : '';
  el.innerHTML = (offlineNote||'') + depHtml + capHeader + capHtml;
}
async function recheckCredentials(){
  // Forces an immediate Etsy + Anthropic credential check instead of waiting up to
  // 5 minutes for the next background health-loop tick -- lets Scott confirm a
  // credential rotation actually worked right away (2026-07-08 correction pass).
  const btn = document.getElementById('recheck-creds-btn');
  const original = btn ? btn.textContent : '';
  if(btn){ btn.textContent = 'Checking…'; btn.style.pointerEvents = 'none'; }
  try{
    const r = await fetchWithTimeout(BASE+'/api/system/recheck-credentials', {
      method:'POST',
      headers:{Authorization:'Bearer '+TOKEN},
    }, 20000);
    const d = await r.json();
    showToast(d.all_ok ? 'Credentials OK ✓' : ('Still failing: '+d.detail), d.all_ok ? 'ok' : 'error', 6000);
    await loadDependencyHealth();
  }catch(e){
    showToast('Recheck failed: '+e.message, 'error');
  }finally{
    if(btn){ btn.textContent = original || 'Recheck now'; btn.style.pointerEvents = ''; }
  }
}
async function loadDependencyHealth(){
  const el = document.getElementById('dep-pill-row');
  try{
    const r = await authGet('/api/system/dependencies');
    const d = await r.json();
    cacheSet('depHealth', d);
    _renderDependencyHealth(d, el, null);
  }catch(e){
    const cached = cacheGet('depHealth');
    if(cached){
      _renderDependencyHealth(cached.data, el, _offlineNote(cached.ts));
    } else if(el){
      el.innerHTML = '<div style="color:var(--red);font-size:11px">Dependency health offline</div>';
    }
  }
}

// ── Header status pill — derived from already-fetched agents/dependency data,
// no extra network call. Mirrors the dep-pill open/half_open/closed semantics. ──
function updateSystemStatusPill(){
  const el = document.getElementById('system-status-pill');
  const labelEl = document.getElementById('system-status-label');
  if(!el || !labelEl) return;
  const agentsCached = cacheGet('agents');
  const depsCached = cacheGet('depHealth');
  const agentsData = agentsCached ? agentsCached.data : null;
  const depsData = depsCached ? depsCached.data : null;
  if(!agentsData && !depsData){
    el.className = 'status-pill';
    labelEl.textContent = 'UNKNOWN';
    return;
  }
  let state = 'optimal';
  if(depsData && depsData.dependencies.some(d => d.state === 'open')) state = 'error';
  if(agentsData && agentsData.agents.some(a => a.built && a.status === 'error')) state = 'error';
  if(state !== 'error'){
    if(depsData && depsData.dependencies.some(d => d.state === 'half_open')) state = 'degraded';
    if(agentsData && agentsData.running_count < agentsData.total_count) state = 'degraded';
  }
  el.className = 'status-pill' + (state === 'optimal' ? '' : ' '+state);
  labelEl.textContent = state.toUpperCase();
}

// ── Alert bell — real data from /api/alerts (deps + token age + agent heartbeats) ──
function toggleAlertDropdown(){
  const dd = document.getElementById('alert-dropdown');
  if(!dd) return;
  const opening = (dd.style.display === 'none' || !dd.style.display);
  dd.style.display = opening ? 'block' : 'none';
  const btn = document.getElementById('bell-btn');
  if(btn) btn.setAttribute('aria-expanded', opening ? 'true' : 'false');
}
function _renderAlerts(d, badgeEl, listEl, offlineNote){
  const alerts = (d && d.alerts) || [];
  if(badgeEl){
    if(alerts.length > 0){
      badgeEl.textContent = alerts.length > 99 ? '99+' : alerts.length;
      badgeEl.style.display = '';
    } else {
      badgeEl.style.display = 'none';
    }
  }
  if(!listEl) return;
  if(alerts.length === 0){
    listEl.innerHTML = (offlineNote||'') + '<div style="color:var(--muted);font-size:11px;padding:8px">No active alerts</div>';
    return;
  }
  listEl.innerHTML = (offlineNote||'') + alerts.map(a=>{
    const sev = a.severity || '';
    // Severity was conveyed by the left-border color alone (WCAG 1.4.1 — not color
    // alone); prefix a text label so it reads without relying on color perception.
    const sevLabel = sev === 'critical' ? 'Critical: ' : sev === 'warning' ? 'Warning: ' : '';
    return '<div class="alert-row '+escHtml(sev)+'">'+
      '<div>'+(sevLabel ? '<strong>'+sevLabel+'</strong>' : '')+escHtml(a.title||'')+'</div>'+
      (a.detail ? '<div class="at">'+escHtml(a.detail)+'</div>' : '') +
      '</div>';
  }).join('');
}
async function loadAlerts(){
  const badgeEl = document.getElementById('bell-badge');
  const listEl = document.getElementById('alert-dropdown-list');
  try{
    const r = await authGet('/api/alerts');
    const d = await r.json();
    cacheSet('alerts', d);
    _renderAlerts(d, badgeEl, listEl, null);
  }catch(e){
    const cached = cacheGet('alerts');
    if(cached){
      _renderAlerts(cached.data, badgeEl, listEl, _offlineNote(cached.ts));
    } else if(listEl){
      listEl.innerHTML = '<div style="color:var(--red);font-size:11px;padding:8px">Alerts offline</div>';
    }
  }
}
document.addEventListener('click', function(e){
  const dd = document.getElementById('alert-dropdown');
  const bellBtn = document.getElementById('bell-btn');
  if(!dd || dd.style.display === 'none' || !dd.style.display) return;
  if(bellBtn && !bellBtn.contains(e.target)){
    dd.style.display = 'none';
  }
});

// ── Executive Briefing — bottom-bar button, pure read of data already loaded by
// loadAll()'s 30s cycle (shop performance, open actions, alerts). No new fetch,
// no new endpoint — just rolls up what's already cached client-side. ──
function toggleBriefingPanel(){
  const panel = document.getElementById('brief-panel');
  if(!panel) return;
  const opening = (panel.style.display === 'none' || !panel.style.display);
  panel.style.display = opening ? 'block' : 'none';
  if(opening) renderExecutiveBriefing();
}
function renderExecutiveBriefing(){
  const body = document.getElementById('brief-panel-body');
  if(!body) return;
  const rows = [];

  const sp = cacheGet('shopPerf');
  if(sp && sp.data && sp.data.a){
    const lt = sp.data.a.latest || {}, del = sp.data.a.delta || {};
    if(lt.revenue_30d != null){
      const sign = (del.revenue_30d != null && del.revenue_30d < 0) ? '' : '+';
      rows.push('<div>Revenue (30d): $'+lt.revenue_30d.toFixed(2)+
        (del.revenue_30d != null ? ' ('+sign+del.revenue_30d.toFixed(1)+'%)' : '')+'</div>');
    } else {
      rows.push('<div style="color:var(--muted)">Shop performance: no data yet</div>');
    }
  } else {
    rows.push('<div style="color:var(--muted)">Shop performance: not yet loaded — try again in a few seconds</div>');
  }

  const pending = _pendingActions || [];
  const s = _actionsSummary || {high:0,medium:0,low:0};
  rows.push('<div>'+pending.length+' pending action'+(pending.length===1?'':'s')+
    ' ('+s.high+' high / '+s.medium+' medium / '+s.low+' low)</div>');

  const al = cacheGet('alerts');
  if(al && al.data){
    const alerts = al.data.alerts || [];
    if(alerts.length === 0){
      rows.push('<div style="color:var(--muted)">No active alerts</div>');
    } else {
      rows.push(alerts.map(a=>{
        const sev = a.severity || '';
        const sevLabel = sev === 'critical' ? 'Critical: ' : sev === 'warning' ? 'Warning: ' : '';
        return '<div class="alert-row '+escHtml(sev)+'">'+(sevLabel ? '<strong>'+sevLabel+'</strong>' : '')+escHtml(a.title||'')+'</div>';
      }).join(''));
    }
  } else {
    rows.push('<div style="color:var(--muted)">Alerts: not yet loaded — try again in a few seconds</div>');
  }

  body.innerHTML = rows.join('');
}
document.addEventListener('click', function(e){
  const panel = document.getElementById('brief-panel');
  const briefWrap = document.querySelector('.brief-wrap');
  if(!panel || panel.style.display === 'none' || !panel.style.display) return;
  if(briefWrap && !briefWrap.contains(e.target)){
    panel.style.display = 'none';
  }
});

// ── Escape-key dismissal for the alert dropdown, Executive Briefing panel, and
// phone action sheet — none of these had a keyboard way to close other than
// re-finding the trigger button (2026-07-08 accessibility review). ──
document.addEventListener('keydown', function(e){
  if(e.key !== 'Escape') return;
  const dd = document.getElementById('alert-dropdown');
  if(dd && dd.style.display !== 'none' && dd.style.display){
    dd.style.display = 'none';
    const btn = document.getElementById('bell-btn');
    if(btn){ btn.setAttribute('aria-expanded', 'false'); btn.focus(); }
  }
  const panel = document.getElementById('brief-panel');
  if(panel && panel.style.display !== 'none' && panel.style.display){
    panel.style.display = 'none';
    const briefBtn = document.querySelector('.brief-btn');
    if(briefBtn) briefBtn.focus();
  }
  if(document.body.classList.contains('phone-sheet-open')){
    phoneSheetClose();
  }
});

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
// Shared in-flight promise so loadMissionTimeline and loadTasks share one /api/todos fetch
let _todosFetchPromise = null;
function _sharedTodosFetch(){
  if(!_todosFetchPromise){
    _todosFetchPromise = authGet('/api/todos').then(function(r){ return r.json(); })
      .finally(function(){ _todosFetchPromise = null; });
  }
  return _todosFetchPromise;
}

async function loadMissionTimeline(){
  const list = document.getElementById('timeline-list');
  try{
    const d = await _sharedTodosFetch();
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
// Category filter chips + tap-to-answer for 'question' todos (2026-07-15).
// _renderMissionTimeline (above) is a fully separate function/render path for
// the Home screen's compact preview -- these changes intentionally don't
// touch it, so that surface stays exactly as simple as it is today.
let _tasksData = null;
let _taskCategoryFilter = null; // null = All
const _TASK_CATEGORY_LABELS = {
  question: '❓ Questions', scott_only: '🔒 Only You',
  frank_can_do: '🤖 Frank Can Do', general: '📋 General',
};
function setTaskCategoryFilter(key){
  _taskCategoryFilter = key;
  const list = document.getElementById('tasks-list');
  if(_tasksData) _renderTasks(_tasksData, list, null);
}
function _renderTasks(d, list, offlineNote){
  if(!list) return;
  _tasksData = d;
  const todos = d.todos || [];
  let html = offlineNote || '';
  html += '<div class="hub-chip-row">';
  html += `<button class="hub-chip-btn${_taskCategoryFilter===null?' active':''}" onclick="setTaskCategoryFilter(null)">All (${todos.length})</button>`;
  Object.keys(_TASK_CATEGORY_LABELS).forEach(key=>{
    const n = todos.filter(t=>(t.category||'general')===key).length;
    html += `<button class="hub-chip-btn${_taskCategoryFilter===key?' active':''}" onclick="setTaskCategoryFilter('${key}')">${_TASK_CATEGORY_LABELS[key]} (${n})</button>`;
  });
  html += '</div>';
  const filtered = _taskCategoryFilter===null ? todos : todos.filter(t=>(t.category||'general')===_taskCategoryFilter);
  if(!filtered.length){
    html += '<div style="color:var(--muted);font-size:12px">No tasks in this category.</div>';
    list.innerHTML = html;
    return;
  }
  html += filtered.map(t=>{
    const done = !!t.done;
    const overdue = !done && t.due_date && t.due_date < new Date().toISOString().slice(0,10);
    const dueTxt = t.due_date ? ' · due '+escHtml(t.due_date)+(overdue?' ⚠':'') : '';
    const catLabel = _TASK_CATEGORY_LABELS[t.category] || '';
    const isQuestion = t.category === 'question';
    const answered = !!t.answer;
    return '<div class="tl-item">'+
      '<div class="tl-dotcol"><input type="checkbox" '+(done?'checked':'')+' onchange="toggleHudTodo('+t.id+',this.checked)" style="width:13px;height:13px;margin-top:2px;accent-color:var(--gold)"></div>'+
      '<div class="tl-txt"><div class="ttl"'+(done?' style="text-decoration:line-through;color:var(--muted)"':(overdue?' style="color:var(--red)"':''))+'>'+escHtml(t.text)+'</div>'+
      '<div class="sub">added by '+escHtml(t.added_by||'scott')+dueTxt+(catLabel?' · '+catLabel:'')+'</div>'+
      (answered ? '<div class="sub" style="color:var(--gold);margin-top:4px">Your answer: '+escHtml(t.answer)+' <a href="#" onclick="event.preventDefault();openAnswerModal('+t.id+')" style="color:var(--muted);text-decoration:underline">✏️ edit</a></div>'
        : (isQuestion ? '<button class="hub-act-btn secondary" style="font-size:11px;padding:4px 10px;margin-top:6px" onclick="openAnswerModal('+t.id+')">💬 Answer</button>' : ''))+
      '</div>'+
      '<button onclick="deleteHudTodo('+t.id+')" style="background:none;border:none;color:var(--muted);font-size:13px;cursor:pointer;padding:2px 4px;flex-shrink:0">✕</button></div>'+
      (isQuestion ? '<div id="answer-modal-'+t.id+'" style="display:none;padding:0 4px 8px 26px"></div>' : '');
  }).join('');
  list.innerHTML = html;
}
function openAnswerModal(id) {
  const panel = document.getElementById('answer-modal-'+id);
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  document.querySelectorAll('[id^="answer-modal-"]').forEach(el => el.style.display = 'none');
  if (isOpen) return;
  const existing = (_tasksData && _tasksData.todos || []).find(t => t.id === id);
  const prevAnswer = (existing && existing.answer) || '';
  panel.innerHTML = `<div style="padding:8px 0;border-top:1px solid var(--border);margin-top:6px">
    <textarea id="answer-text-${id}" rows="2" placeholder="Type your answer…"
      aria-label="Your answer"
      style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);padding:8px;font-size:13px;font-family:inherit">${escHtml(prevAnswer)}</textarea>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="hub-act-btn primary" onclick="submitTodoAnswer(${id})">${prevAnswer ? 'Update' : 'Submit'}</button>
      <button class="hub-act-btn secondary" onclick="document.getElementById('answer-modal-${id}').style.display='none'">Cancel</button>
    </div>
  </div>`;
  panel.style.display = 'block';
}
async function submitTodoAnswer(id) {
  const ta = document.getElementById('answer-text-'+id);
  const answer = (ta && ta.value || '').trim();
  if (!answer) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/todos/'+id+'/answer', {
      method: 'POST',
      headers: {Authorization: 'Bearer '+TOKEN, 'Content-Type': 'application/json'},
      body: JSON.stringify({answer})
    }, 15000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    showToast('Answer sent to Frank.');
    loadTasks();
  } catch(e) {
    showToast('Could not submit answer: ' + (e.message||e), 'err', 6000);
  }
}
async function loadTasks(){
  const list = document.getElementById('tasks-list');
  try{
    const d = await _sharedTodosFetch();
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
  const catInp = document.getElementById('hud-todo-category');
  const text = inp.value.trim();
  if (!text) return;
  inp.value = '';
  const due = dueInp.value;
  dueInp.value = '';
  const category = catInp ? catInp.value : 'general';
  try {
    await fetchWithTimeout(BASE+'/api/todos', {
      method:'POST',
      headers:{'Content-Type':'application/json',Authorization:'Bearer '+TOKEN},
      body: JSON.stringify({text, added_by:'scott', due_date: due || null, category}),
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
  // Phone Approvals tab badge = ONLY items actually awaiting approval (the `pending`
  // count) — NOT the high-severity recommendations (those live under Today → Needs
  // attention). This keeps the badge honest: it always matches what the Approvals panel
  // shows, so a "7" never leads to an empty "All clear" panel.
  const pb = document.getElementById('ptab-badge');
  const pc = pending || 0;
  if (pb) { if (pc > 0) { pb.textContent = pc > 99 ? '99+' : pc; pb.style.display = 'flex'; } else { pb.style.display = 'none'; } }
  // The urgent-recommendations count lives on the TODAY tab now (that's where the
  // "Needs attention" items are shown) — not on Approvals.
  const tb = document.getElementById('ptab-today-badge');
  const hc = (summary && summary.high) || 0;
  if (tb) { if (hc > 0) { tb.textContent = hc > 99 ? '99+' : hc; tb.style.display = 'flex'; } else { tb.style.display = 'none'; } }
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
  update_title: '📝', update_tags: '🏷️', update_description: '📄', publish_listing: '🏷️', deactivate_listing: '⛔',
  listing_photo: '🖼️', local_write_file: '📁', local_delete: '🗑️', local_exec: '⚙️', run_script: '⚙️',
  update_price: '💲', toggle_listing_state: '🔄'
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
  if (a.type === 'update_price') {
    return `<div>New price: <strong>$${escHtml(Number(p.price||0).toFixed(2))}</strong></div>`;
  }
  if (a.type === 'toggle_listing_state') {
    const label = p.new_state === 'active' ? 'Activate (renews an expired listing)' : 'Deactivate';
    return `<div>${label} — listing ${escHtml(String(p.listing_id||''))} → <strong>${escHtml(p.new_state||'')}</strong></div>`;
  }
  if (a.type === 'update_description') {
    const diffHtml = simpleLineDiff(p.before_description, p.description);
    return `<div style="max-height:320px;overflow:auto;background:var(--bg);border-radius:var(--r-sm);padding:8px;font-family:monospace;font-size:12px;white-space:pre-wrap">${diffHtml || '<span style="color:var(--muted)">No changes</span>'}</div>`;
  }
  if (a.type === 'listing_photo') {
    const url = BASE+'/api/files/download?root=staged_photos&path='+encodeURIComponent(p.path||'')+'&inline=1';
    return `<img src="${url}" loading="lazy" alt="Staged photo for listing ${escHtml(String(p.listing_id||''))}" style="max-width:260px;max-height:260px;border-radius:var(--r-sm);display:block">` +
      `<div style="margin-top:6px">Listing ${escHtml(String(p.listing_id||''))} · rank ${p.rank||''} · ${escHtml(p.sku||'')}</div>`;
  }
  if (a.type === 'publish_listing') {
    const pv = p.preview || {};
    return `<div style="display:flex;gap:10px;align-items:flex-start">` +
      (pv.thumbnail_url
        ? `<img src="${escHtml(pv.thumbnail_url)}" loading="lazy" alt="${escHtml(pv.title||'Listing preview')}" style="width:70px;height:70px;border-radius:var(--r-sm);object-fit:cover;flex-shrink:0">`
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
      `<div style="max-height:260px;overflow:auto;background:var(--bg);border-radius:var(--r-sm);padding:8px;font-family:monospace;font-size:12px;white-space:pre-wrap">${diffHtml || '<span style="color:var(--muted)">No changes</span>'}</div>`;
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
    const url = BASE+'/api/files/download?root=staged_photos&path='+encodeURIComponent(p.path||'')+'&inline=1';
    thumb = `<img class="hub-thumb" src="${url}" loading="lazy" alt="Staged listing photo">`;
  } else if (a.type === 'publish_listing' && (p.preview || {}).thumbnail_url) {
    thumb = `<img class="hub-thumb" src="${escHtml(p.preview.thumbnail_url)}" loading="lazy" alt="${escHtml(p.preview.title||'Listing preview')}">`;
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
  else if (a.type === 'update_description') meta += ` · ${escHtml((p.description || '').slice(0, 90))}…`;
  else if (a.type === 'update_price') meta += ` · $${escHtml(Number(p.price||0).toFixed(2))}`;
  else if (a.type === 'toggle_listing_state') meta += ` · → ${escHtml(p.new_state || '')}`;
  return `<div class="hub-listing-item" style="cursor:pointer" onclick="toggleActionDetail(${a.id})" role="button" tabindex="0">
    ${thumb}
    <div class="hub-listing-info">
      <div class="hub-listing-title">${escHtml(a.summary || a.type)}</div>
      <div class="hub-listing-meta">${escHtml(meta)}</div>
    </div>
    <div class="act-btns" style="flex-shrink:0" onclick="event.stopPropagation()">
      <button class="act-btn approve" onclick="approveAction(${a.id})">Approve</button>
      ${a.type === 'publish_listing' ? `<button class="act-btn secondary" onclick="fixDraftStage(${(p.listing_id||0)},${a.id},this)">🤖 Fix</button>` : ''}
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
      aria-label="Reason for rejecting"
      style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);padding:8px;font-size:13px;font-family:inherit"></textarea>
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadActions()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}
function setActionFilter(sev) {
  _actionFilter = (_actionFilter === sev) ? null : sev; // tap again to clear
  renderActionsContent();
}
const _SEV_COLORS = {high:'var(--red)', medium:'var(--gold)', low:'#7ba0c2'};
// Same thresholds as CLAUDE.md's Autonomy Boundaries section ("any bulk edit
// touching more than 10 listings" needs confirming scope) -- surfaced here so
// Scott sees WHY a big batch deserves a closer look, not just that there's a
// big queue. 2026-07-15: previously nothing in this screen explained the
// safety rails at all.
const _APPROVAL_BATCH_LIMIT = 10;
const _APPROVAL_BATCH_TYPES = ['update_tags','update_title','update_description','publish_listing','deactivate_listing','toggle_listing_state','update_price'];
// Price changes get their own tighter rail -- CLAUDE.md's Hard Stop is "more
// than 5 listings" for price, not the general 10-item batch limit.
const _PRICE_BATCH_LIMIT = 5;
function renderActionsContent() {
  const el = document.getElementById('actions-content');
  if (!el) return;
  const pending = _pendingActions || [];
  const s = _actionsSummary || {high:0,medium:0,low:0};
  let html = `<div class="hub-listing-meta" style="margin-bottom:10px;padding:8px 10px;background:var(--panel2);border-radius:var(--r-sm)">
    %%AGENT_SHORT%% stages every listing-changing action here — nothing goes live without your tap. Extra care applies to big batches: CLAUDE.md's own safety rail flags more than ${_APPROVAL_BATCH_LIMIT} listing edits or more than 5 price changes in one sitting.
  </div>`;
  const typeCounts = {};
  pending.forEach(a => { typeCounts[a.type] = (typeCounts[a.type]||0) + 1; });
  const overLimit = _APPROVAL_BATCH_TYPES.filter(t => t !== 'update_price' && (typeCounts[t]||0) > _APPROVAL_BATCH_LIMIT);
  const priceOverLimit = (typeCounts['update_price']||0) > _PRICE_BATCH_LIMIT;
  if (overLimit.length || priceOverLimit) {
    const parts = overLimit.map(t => `${typeCounts[t]} pending ${t.replace(/_/g,' ')}`);
    if (priceOverLimit) parts.push(`${typeCounts['update_price']} pending price changes`);
    const limitNote = priceOverLimit && !overLimit.length
      ? `bigger than the ${_PRICE_BATCH_LIMIT}-listing price-change safety rail`
      : `bigger than the ${_APPROVAL_BATCH_LIMIT}-item safety rail${priceOverLimit ? ` (price changes: ${_PRICE_BATCH_LIMIT})` : ''}`;
    html += `<div class="hub-listing-meta" style="margin-bottom:10px;padding:8px 10px;background:rgba(200,60,60,.12);border-left:3px solid var(--red);border-radius:var(--r-sm)">
      ⚠️ ${parts.join(', ')} — ${limitNote}. Worth a closer look before approving all at once.
    </div>`;
  }
  if (pending.length) {
    html += `<div class="section-title">⏳ Awaiting your approval (${pending.length})</div>`;
    html += pending.map(renderApproval).join('');
  }
  if (!_actions.length && !pending.length) { el.innerHTML = html + '<div class="empty">✅ All clear — no action items right now.</div>'; return; }
  const sevBtn = sev => {
    const active = _actionFilter === sev;
    const c = _SEV_COLORS[sev];
    const style = active
      ? `flex:1;text-align:center;padding:10px 6px;cursor:pointer;border-color:${c};background:${c}26`
      : 'flex:1;text-align:center;padding:10px 6px;cursor:pointer';
    return `<div class="metric" style="${style}" onclick="setActionFilter('${sev}')" role="button" tabindex="0"><div class="value" style="color:${c};font-size:20px">${s[sev]||0}</div><div class="sub">${sev}${active?' ✓':''}</div></div>`;
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
          ${a.url ? `<a class="act-btn secondary" href="${escHtml(a.url)}" target="_blank">Open on Etsy</a>` : ''}
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadCalendar()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
  } catch(e) {
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadMemory()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
  html += '<div class="section-title">🧠 What %%AGENT_SHORT%% has logged</div>';
  if (!d.learnings.length) {
    html += '<div class="empty">No durable insights logged yet — %%AGENT_SHORT%% appends a line here whenever a conversation surfaces a pattern worth remembering.</div>';
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadWorkflows()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
        (d.output ? `<pre style="margin-top:6px;max-height:220px;overflow:auto;background:var(--bg);border-radius:var(--r-sm);padding:8px;font-size:12px;white-space:pre-wrap">${escHtml(d.output)}</pre>` : '');
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadConversations()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderConversationList() {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  if (!_convSessions.length) {
    el.innerHTML = '<div class="empty">No conversations yet — chat history will appear here once %%AGENT_SHORT%% has been used.</div>';
    return;
  }
  el.innerHTML = `<div class="section-title">💬 Sessions (${_convSessions.length})</div>` +
    _convSessions.map(s => `<div class="tl-item" style="cursor:pointer" onclick="openConversation('${escHtml(s.session_id)}')" role="button" tabindex="0">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(_convShortId(s.session_id))} <span style="color:var(--muted);font-weight:400">— ${s.message_count} msg${s.message_count===1?'':'s'}</span></div>
        <div class="sub">${escHtml(s.last_role === 'user' ? '%%OWNER%%' : '%%AGENT_SHORT%%')}: ${escHtml(s.last_snippet || '')} · ${_convTimeAgo(s.last_at)}</div>
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="openConversation('${escHtml(sessionId)}')" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div><div style="text-align:center;margin-top:8px"><button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:8px 20px;font-size:13px;cursor:pointer">Back to list</button></div>`;
  }
}

function renderConversationDetail(sessionId, d) {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  const msgs = d.messages || [];
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:6px 14px;font-size:12px;cursor:pointer">‹ Back</button>
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="searchConversations()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderConversationSearch(q, results) {
  const el = document.getElementById('conversations-content');
  if (!el) return;
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToConversationList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:6px 14px;font-size:12px;cursor:pointer">‹ Back to list</button>
    <span style="font-size:12px;color:var(--muted)">${results.length} match${results.length===1?'':'es'} for "${escHtml(q)}"</span>
  </div>`;
  html += results.length ? results.map(r => `<div class="tl-item" style="cursor:pointer" onclick="openConversation('${escHtml(r.session_id)}')" role="button" tabindex="0">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt">
        <div class="ttl">${escHtml(r.role === 'user' ? '%%OWNER%%' : '%%AGENT_SHORT%%')} <span style="color:var(--muted);font-weight:400">in ${escHtml(_convShortId(r.session_id))}</span></div>
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadKb()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
    _kbDocs.map(d => `<div class="tl-item" style="cursor:pointer" onclick="openKbDoc('${escHtml(d.filename)}')" role="button" tabindex="0">
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="openKbDoc('${escHtml(filename)}')" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div><div style="text-align:center;margin-top:8px"><button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:8px 20px;font-size:13px;cursor:pointer">Back to list</button></div>`;
  }
}

function renderKbDoc(filename, d) {
  const el = document.getElementById('kb-content');
  if (!el) return;
  el.innerHTML = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:6px 14px;font-size:12px;cursor:pointer">‹ Back</button>
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
    el.innerHTML = `<div class="empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load')}</div><div style="text-align:center;margin-top:8px"><button onclick="searchKb()" style="background:var(--gold);color:#0D1B2A;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
  }
}

function renderKbSearch(q, results) {
  const el = document.getElementById('kb-content');
  if (!el) return;
  let html = `<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px">
    <button onclick="backToKbList()" style="background:none;border:1px solid var(--border);color:var(--muted);border-radius:var(--r-sm);padding:6px 14px;font-size:12px;cursor:pointer">‹ Back to list</button>
    <span style="font-size:12px;color:var(--muted)">${results.length} doc${results.length===1?'':'s'} match "${escHtml(q)}"</span>
  </div>`;
  html += results.length ? results.map(r => `<div class="tl-item" style="cursor:default">
      <div class="tl-dotcol"><span class="d"></span></div>
      <div class="tl-txt" style="width:100%">
        <div class="ttl" style="cursor:pointer" onclick="openKbDoc('${escHtml(r.filename)}')" role="button" tabindex="0">${escHtml(r.title)} <span style="color:var(--muted);font-weight:400">— ${r.match_count} match${r.match_count===1?'':'es'}</span></div>
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
    el.innerHTML = `<div class="hub-empty">${escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load listings')}</div><div style="text-align:center;margin-top:8px"><button onclick="loadListings(_lastListingState)" style="background:var(--gold);color:#06141f;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>`;
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
    <div class="hub-listing-item" style="cursor:pointer" onclick="toggleListingDetail(${l.listing_id})" role="button" tabindex="0">
      ${l.thumbnail_url ? `<img class="hub-thumb" src="${escHtml(l.thumbnail_url)}" loading="lazy" alt="${escHtml(l.title||'Listing photo')}">` : `<div class="hub-thumb-ph" aria-hidden="true">🏷️</div>`}
      <div class="hub-listing-info">
        <div class="hub-listing-title">${escHtml(l.title)}</div>
        <div class="hub-listing-meta">${l.views} views · ${l.num_favorers} ♥${l.sales!=null?' · '+l.sales+' sold':''}<span id="hub-state-${l.listing_id}" class="hub-lstate ${l.state==='active'?'active':'draft'}">${escHtml(l.state)}</span></div>
        ${(l.state==='inactive'||l.manifest_status==='FAIL') ? `<button class="hub-act-btn secondary" style="font-size:11px;padding:4px 10px;margin-top:6px" onclick="event.stopPropagation();openFixListingModal(${l.listing_id})">🔧 Ask %%AGENT_SHORT%% to Fix</button>` : ''}
      </div>
      <div class="hub-listing-price">$${(+l.price||0).toFixed(2)}</div>
    </div>
    ${(l.state==='inactive'||l.manifest_status==='FAIL') ? `<div id="fix-modal-${l.listing_id}" style="display:none;padding:0 4px"></div>` : ''}
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
    ((l.state==='active'||l.state==='inactive') ? `<button id="hub-state-btn-${listingId}" class="hub-act-btn secondary" style="font-size:12px;padding:6px 12px" onclick="event.stopPropagation();toggleListingState(${listingId},this)">${l.state==='active'?'⏸️ Deactivate':'▶️ Activate'}</button>` : '')+
    `<a href="${escHtml(l.url)}" target="_blank" style="color:var(--gold);font-size:12px;text-decoration:none" onclick="event.stopPropagation()">Open on Etsy ↗</a>`+
    `</div>`;
  // Fix button/modal for inactive listings now lives on the compact row itself
  // (renderListings(), one tap, no need to expand this detail panel first) —
  // see the "🔧 Ask Frank to Fix" button + #fix-modal-${listingId} placeholder there.
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
function openFixListingModal(listingId) {
  const panel = document.getElementById('fix-modal-'+listingId);
  if (!panel) return;
  const isOpen = panel.style.display !== 'none';
  document.querySelectorAll('[id^="fix-modal-"]').forEach(el => el.style.display = 'none');
  if (isOpen) return;
  panel.innerHTML = `<div style="padding:10px 0;border-top:1px solid var(--border);margin-top:8px">
    <div class="hub-listing-meta" style="margin-bottom:6px">
      %%AGENT_SHORT%% will check what's wrong and fix the title/tags automatically if that's the issue.
      For missing photos or attached-file problems, he'll leave you a todo instead of guessing —
      either way, nothing goes live until you approve it in the Action Center.
    </div>
    <textarea id="fix-instructions-${listingId}" rows="2" placeholder="Optional — anything specific you want %%AGENT_SHORT%% to focus on"
      aria-label="Instructions for %%AGENT_SHORT%%"
      style="width:100%;box-sizing:border-box;background:var(--bg);border:1px solid var(--border);border-radius:var(--r-sm);color:var(--text);padding:8px;font-size:13px;font-family:inherit"></textarea>
    <div style="display:flex;gap:8px;margin-top:8px">
      <button class="hub-act-btn primary" onclick="event.stopPropagation();submitFixListing(${listingId})">Send to %%AGENT_SHORT%%</button>
      <button class="hub-act-btn secondary" onclick="event.stopPropagation();document.getElementById('fix-modal-${listingId}').style.display='none'">Cancel</button>
    </div>
    <div id="fix-result-${listingId}" style="margin-top:8px;font-size:12px"></div>
  </div>`;
  panel.style.display = 'block';
}
async function submitFixListing(listingId) {
  const ta = document.getElementById('fix-instructions-'+listingId);
  const instructions = (ta && ta.value || '').trim();
  const resultEl = document.getElementById('fix-result-'+listingId);
  resultEl.textContent = '⏳ %%AGENT_SHORT%% is working on it…';
  resultEl.style.color = 'var(--muted)';
  try {
    const r = await fetchWithTimeout(BASE+'/api/listings/'+listingId+'/request-fix', {
      method: 'POST',
      headers: {Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
      body: JSON.stringify({instructions})
    }, 60000);
    const d = await r.json().catch(()=>({}));
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    let msg = `✓ Staged ${d.staged_count} item(s) in the Action Center for your approval (fixes + a republish).`;
    if (d.unfixable_issues && d.unfixable_issues.length) {
      msg += ` ⚠️ Also found something that isn't auto-fixable: ${escHtml(d.unfixable_issues.join('; '))} — added to your todo list. Don't approve the republish until that's handled.`;
    }
    if (d.errors && d.errors.length) {
      msg += ` (${escHtml(d.errors.join('; '))})`;
    }
    resultEl.innerHTML = msg;
    resultEl.style.color = 'var(--green)';
    loadActions();
  } catch(e) {
    resultEl.textContent = 'Could not reach %%AGENT_SHORT%%: ' + (e.message||e);
    resultEl.style.color = 'var(--red)';
  }
}

// Brand Kit's full theme catalog (4 live + 12 planned). Swatch roles vary per
// theme (some have "Deep accent", one has "Pop accent" + "Text on dark") so
// `swatches` is a free-form [{label,hex}] list, not a fixed 4-slot shape.
// Live themes (DP1026-1029) only have hex roles documented in CLAUDE.md -- no
// tagline/aesthetic/motifs/buyer/trend copy exists for them, so those fields
// are left null rather than inventing marketing copy; the detail panel simply
// omits null fields.
const _BRANDKIT_THEMES = [
  {id:'DP1026', name:'Lavender Dreams', live:true, tagline:null,
    swatches:[{label:'Primary',hex:'#8666AA'},{label:'Accent',hex:'#C4A8D4'},{label:'Neutral',hex:'#FAF7FF'},{label:'Text',hex:'#2C1A3A'}],
    aesthetic:null, motifs:null, buyer:null, bestProduct:'DP1026 Ultimate Digital Life Planner', trend:null},
  {id:'DP1027', name:'Cotton Candy', live:true, tagline:null,
    swatches:[{label:'Primary',hex:'#DE97C6'},{label:'Accent',hex:'#97C6DE'},{label:'Neutral',hex:'#FFF6FC'},{label:'Text',hex:'#2C1A2A'}],
    aesthetic:null, motifs:null, buyer:null, bestProduct:'DP1027 Student & School Planner', trend:null},
  {id:'DP1028', name:'Midnight Blue', live:true, tagline:null,
    swatches:[{label:'Primary',hex:'#1B2568'},{label:'Accent',hex:'#7BA7C2'},{label:'Neutral',hex:'#F0F5FF'},{label:'Text',hex:'#0D1525'}],
    aesthetic:null, motifs:null, buyer:null, bestProduct:'DP1028 Budget & Finance Planner', trend:null},
  {id:'DP1029', name:'Coral Peach', live:true, tagline:null,
    swatches:[{label:'Primary',hex:'#FD6C49'},{label:'Accent',hex:'#F5B878'},{label:'Neutral',hex:'#FFF8F4'},{label:'Text',hex:'#3A1A0D'}],
    aesthetic:null, motifs:null, buyer:null, bestProduct:'DP1029 Fitness & Wellness Planner', trend:null},
  {id:null, name:'Cherry Blossom', live:false, tagline:'Soft as spring, organized as ever',
    swatches:[{label:'Primary',hex:'#F4A7B9'},{label:'Accent',hex:'#F9D0DB'},{label:'Deep accent',hex:'#C4607A'},{label:'Neutral',hex:'#FFF5F7'},{label:'Text',hex:'#3D1A24'}],
    aesthetic:'Japanese sakura, soft spring, feminine, delicate',
    motifs:'Cherry blossom branches, tiny petals falling, bunnies in flower fields, spring birds',
    buyer:'Women 18–30, spring new-year-fresh-start buyers, Japan-aesthetic lovers',
    bestProduct:'DP1026 Life Planner cover variant, standalone spring sticker pack',
    trend:'Seasonal spring, evergreen kawaii aesthetic'},
  {id:null, name:'Sage Garden', live:false, tagline:'Grounded. Calm. Growing.',
    swatches:[{label:'Primary',hex:'#8BA888'},{label:'Accent',hex:'#C8DDB5'},{label:'Deep accent',hex:'#556B50'},{label:'Neutral',hex:'#F6F8F2'},{label:'Text',hex:'#2C3828'}],
    aesthetic:'Cottagecore, botanical, garden, calm nature',
    motifs:'Tiny mushrooms, herb sprigs, watering cans, garden snails, flower pots, bees',
    buyer:'Cottagecore/nature lovers, wellness community, gardeners, women 25–40',
    bestProduct:'DP1029 Fitness/Wellness cover variant, DP1031 Undated Evergreen planner',
    trend:'Pantone spring palette, Deep Botanical macro trend, cottagecore Etsy niche'},
  {id:null, name:'Celestial Night', live:false, tagline:'Plan by the stars',
    swatches:[{label:'Primary',hex:'#1E1B4B'},{label:'Accent',hex:'#C9A84C'},{label:'Mid tone',hex:'#6B5FA5'},{label:'Neutral',hex:'#F0EEF8'},{label:'Text on dark',hex:'#F9F6FF'}],
    aesthetic:'Celestial, astrology, moon phases, stars, mystical kawaii',
    motifs:'Crescent moons, stars, constellations, sleeping moon faces, tiny planets, comets, crystal balls',
    buyer:'Astrology community, witchy aesthetic, Gen Z, spiritual wellness buyers',
    bestProduct:'DP1032 Dark Mode Planner (celestial variant), standalone celestial sticker pack',
    trend:'Dark mode trend, Y3K aesthetic, celestial Etsy niche (consistently top 5 planner aesthetic)'},
  {id:null, name:'Mocha Latte', live:false, tagline:'Sophisticated. Warm. Ready for anything.',
    swatches:[{label:'Primary',hex:'#8B5E3C'},{label:'Accent',hex:'#D4A96A'},{label:'Mid tone',hex:'#C8A882'},{label:'Neutral',hex:'#FDF8F0'},{label:'Text',hex:'#2C1A0E'}],
    aesthetic:'Café aesthetic, warm brown luxury, sophisticated minimalist',
    motifs:'Coffee cups with cream swirls, croissants, tiny café scenes, autumn leaves, cozy mugs',
    buyer:'Coffee lovers, women 25–40, VSCO/aesthetic crowd, mature planner buyers',
    bestProduct:'DP1026 Life Planner, DP1028 Budget Planner (premium feel)',
    trend:'2026 Warm Earth Revival macro trend — brown is having a major moment in design'},
  {id:null, name:'Mermaidcore', live:false, tagline:'Deep-sea dreams, surface-level organized',
    swatches:[{label:'Primary',hex:'#4ABFBF'},{label:'Accent',hex:'#B8A9D9'},{label:'Shimmer',hex:'#A8E6CF'},{label:'Neutral',hex:'#F0FAFF'},{label:'Text',hex:'#1A3A4A'}],
    aesthetic:'Mermaid, ocean, iridescent, fantasy kawaii',
    motifs:'Mermaid tails, shells, bubbles, starfish, pearls, seahorses, coral',
    buyer:'Fantasy/ocean lovers, Gen Z, creative dreamers, summer buyers',
    bestProduct:'DP1031 Undated Evergreen (fresh + timeless), summer seasonal release',
    trend:'Mermaidcore is one of the top 3 macro design trends for 2026 (Envato research)'},
  {id:null, name:'Dark Academia', live:false, tagline:'Knowledge is power. Plan accordingly.',
    swatches:[{label:'Primary',hex:'#3B2A1A'},{label:'Accent',hex:'#9B7D3A'},{label:'Mid tone',hex:'#7A5C3F'},{label:'Neutral',hex:'#F5EDD6'},{label:'Text',hex:'#1C1208'}],
    aesthetic:'Dark academia, vintage library, Victorian stationery, moody intellectual',
    motifs:'Tiny books, quill pens, ink bottles, hourglasses, candles, dried flowers, keys',
    buyer:'Students (especially college), book lovers, aesthetic Tumblr/Pinterest crowd, dark aesthetic buyers',
    bestProduct:'DP1027 Student Planner cover variant, DP1033 Teacher Planner',
    trend:'Top-performing Etsy aesthetic with dedicated buyer communities'},
  {id:null, name:'Tropical Hibiscus', live:false, tagline:'Bright energy. Big plans.',
    swatches:[{label:'Primary',hex:'#FF6B9D'},{label:'Accent',hex:'#FFD166'},{label:'Mid tone',hex:'#06D6A0'},{label:'Neutral',hex:'#FFFAF0'},{label:'Text',hex:'#3D0029'}],
    aesthetic:'Tropical, maximalist, Gen Z, bold & colorful (rejects minimalism)',
    motifs:'Tropical flowers, pineapples, flamingos, parrots, watermelon slices, suns',
    buyer:'Gen Z buyers, bold personality types, summer seasonal, "Play Haus" aesthetic crowd',
    bestProduct:'DP1027 Student Planner, DP1029 Fitness Planner (high-energy niche match)',
    trend:'"Play Haus" 2026 trend (Gen Z\\'s colorful rejection of minimalism), Spring Vivid Brights'},
  {id:null, name:'Rose Gold Luxe', live:false, tagline:'You deserve gold. And a good plan.',
    swatches:[{label:'Primary',hex:'#B76E79'},{label:'Accent',hex:'#D4AF7A'},{label:'Mid tone',hex:'#F2C4CE'},{label:'Neutral',hex:'#FDF8F8'},{label:'Text',hex:'#4A2030'}],
    aesthetic:'Luxury, aspirational, rose gold glam, feminine premium',
    motifs:'Tiny diamonds, hearts with crowns, champagne flutes, makeup brushes, perfume bottles, stars',
    buyer:'Women 25–40, aspirational buyers, bridal/wedding planners, hustle culture crowd',
    bestProduct:'DP1026 Ultimate Life Planner (premium tier), DP1028 Budget Planner (financial goals)',
    trend:'Rose gold is perennially strong for premium digital products, Clubroom Contrast luxury aesthetic'},
  {id:null, name:'Ocean Breeze', live:false, tagline:'Clear mind. Calm days. Clear goals.',
    swatches:[{label:'Primary',hex:'#3B8E8A'},{label:'Accent',hex:'#7EC8C8'},{label:'Mid tone',hex:'#A8D8D8'},{label:'Neutral',hex:'#F0FAFA'},{label:'Text',hex:'#0D3535'}],
    aesthetic:'Coastal, clean, fresh, calming, modern minimalist',
    motifs:'Waves, seashells, sailboats, jellyfish, sea glass, beach umbrellas, lighthouses',
    buyer:'Wellness-focused buyers, adults 30–45, productivity minimalists, coastal aesthetic',
    bestProduct:'DP1029 Wellness Planner, DP1028 Budget Planner (calm & focused)',
    trend:"WGSN's Transformative Teal is the #1 key color for 2026 — this is on-trend at the highest level"},
  {id:null, name:'Midnight Kawaii', live:false, tagline:'Cute goes dark.',
    swatches:[{label:'Primary',hex:'#1A1A2E'},{label:'Accent',hex:'#E040FB'},{label:'Pop accent',hex:'#00E5FF'},{label:'Mid tone',hex:'#2D2B55'},{label:'Text',hex:'#F0E6FF'}],
    aesthetic:'Dark kawaii, Y3K, futuristic, neon-on-dark',
    motifs:'Glowing stars, neon-outlined cats, holographic elements, pixel art kawaii, spaceship chibi',
    buyer:'Dark aesthetic Gen Z, gamers, night-owl planners, tech-forward buyers',
    bestProduct:'DP1032 Dark Mode Planner (primary), great for ADHD planner (less visual overwhelm on dark bg)',
    trend:'Dark mode is standard in competitors; "Mood Mode" / Y3K neon accents are 2026-specific'},
  {id:null, name:'Sunflower Studio', live:false, tagline:'Growth season. Every day.',
    swatches:[{label:'Primary',hex:'#F4C430'},{label:'Accent',hex:'#4A7C59'},{label:'Mid tone',hex:'#F8E08E'},{label:'Neutral',hex:'#FFFDF0'},{label:'Text',hex:'#2A1A00'}],
    aesthetic:'Bright botanical, positive, cheerful, nature + sunshine',
    motifs:'Sunflowers, bees, garden tools, butterflies, ladybugs, seeds sprouting',
    buyer:'Positive-mindset community, spring/summer buyers, gardening niche, teachers',
    bestProduct:'DP1033 Teacher Planner, DP1026 Life Planner (positivity focus)',
    trend:'Yellow is scientifically proven for optimism and serotonin, Deep Botanical trend'},
  {id:null, name:'Matcha Serenity', live:false, tagline:'Slow down. Sip. Succeed.',
    swatches:[{label:'Primary',hex:'#6B8F5E'},{label:'Accent',hex:'#B8CC8E'},{label:'Mid tone',hex:'#E8F0D8'},{label:'Neutral',hex:'#F7F9F3'},{label:'Text',hex:'#1E2D18'}],
    aesthetic:'Japanese minimalist, matcha café, slow living, mindfulness',
    motifs:'Matcha cups, bamboo, koi fish, zen stones, lotus flowers, tiny bento boxes',
    buyer:'Mindfulness/slow living community, Japan aesthetic lovers, wellness buyers, women 22–35',
    bestProduct:'DP1029 Wellness Planner, DP1030 ADHD Planner (calming tones reduce overwhelm)',
    trend:'Sage green / botanical tones are 2026 Deep Botanical macro trend, mindfulness is evergreen'},
];
const _BRANDKIT_LISTING_TYPES = [
  {key:'planners', label:'Digital Planners', icon:'📓',
    title:'≤70 chars (hard limit — mobile ranking penalty above) · lead keyword in first 20–30 chars · include year (2026) or "Undated" + app name (GoodNotes) in first 40 chars · comma separators, not pipes',
    tags:'13 tags · each ≤20 chars · no duplicate of title phrases · multi-word buyer-intent phrases',
    description:['Hook',"What's Included",'Compatible Apps','How To Use Stickers','How To Use The Planner','Sections Included','Technical Details','FAQ','Copyright'],
    photos:'10 slots · 2400×2400px square · subject centered in 70% of frame · 5% neutral padding · lifestyle hero photo first',
    category:'Craft Supplies & Tools > Patterns & How To > Digital Files (taxonomy_id 2078)'},
  {key:'wallart', label:'Wall Art', icon:'🖼️',
    title:'≤70 chars (55–70 char target) · formula "[Primary phrase] Printable Wall Art, Instant Download, [Style/room]" · must include "printable" AND "instant download" · comma separators, not pipes',
    tags:'13 tags · each ≤20 chars · zero duplicate of title phrases · must cover 6 intent categories: style, room, art medium, occasion, recipient, format',
    description:['First-sentence hook (primary keyword + states instant/digital download)',"What's Included",'Specs','FAQ'],
    photos:'10 slots · minimum 2 different room types shown · 2400×2400px · gallery wall grouping + size reference w/ furniture required',
    category:'Not pinned to one taxonomy_id in CLAUDE.md for wall art specifically — gap to confirm with Scott before next wall-art launch'},
  {key:'svg', label:'SS-Series SVG 3D-Print Packs', icon:'✂️',
    title:'≤70 chars (60–70 char target) · formula "[Design Theme] SVG, 3D Print [Type], Instant Download" · "SVG" must appear in first 30 chars · must end with "Instant Download" · comma separators, not pipes',
    tags:'13 tags exactly · each ≤20 chars · zero duplicate of title phrases · must cover design/theme, print method, slicer, use case, format, audience',
    description:['Hook','⚠ Disclaimer (digital download only — no physical item)','Pack Overview',"What's Included",'Compatible Printers & Slicers','How To Print (Bambu Studio)','Size & Scaling','Display Ideas','Technical Details','FAQ','About This Design (AI disclosure)','Copyright'],
    photos:'10 slots · 1–6 lifestyle (must carry "DIGITAL FILE — SVG DOWNLOAD" badge), 7 how-to (Color Painting Fill tool — never "Split by Color", that menu does not exist), 8 detail close-up, 9 specs/ZIP contents, 10 lineup of all designs',
    category:'Craft Supplies & Tools > Patterns & How To > Digital Files (taxonomy_id 2078)'},
];
const _BRANDKIT_PRICING = {
  endingRule:'.99 / .97 / .49 endings only — never round numbers. Applies to every price on every table below.',
  planners: [
    ['DP1026 Ultimate Life Planner','$14.99','104 pages + kawaii cover + 5-sheet sticker pack — premium'],
    ['DP1027 Student & School Planner','$9.99','Student budget — lower price point for volume'],
    ['DP1028 Budget & Finance Planner','$12.99','Niche audience, high value perception'],
    ['DP1029 Fitness & Wellness Planner','$12.99','Niche audience, wellness = premium feel'],
  ],
  wallArt: [
    ['Single print','$4.99–$7.99','Impulse tier'],
    ['Set of 3 matching','$12.99–$19.99','Most purchased bundle unit'],
    ['Gallery wall set of 5–7','$19.99–$39.99','Highest revenue per transaction'],
    ['Pick Any 3 bundle','$14.97','Highest favorites-to-views ratio'],
    ['Complete collection','$24.99','Algorithm anchor — generates catalog-wide signal'],
  ],
  svgPacks: [
    ['5-design pack','$9.99','5 designs · instant download'],
    ['10+-design pack','$14.99','10 or more designs · instant download'],
  ],
  stickerPacks: [
    ['Standalone pack','$4.99–$6.99','1 theme, 5 sheets, 200+ stickers'],
    ['Bundle (all 4 themes)','$12.99–$14.99','Implies a 55–65% discount vs. buying individually'],
    ['Mega bundle','$17.99–$19.99','All themes + bonus seasonal pack'],
  ],
};
const _PRODUCTS_STATIC = [
  {id:'DP1026',name:'Ultimate Life Planner',      price:'$14.99',pages:104},
  {id:'DP1027',name:'Student & School Planner',   price:'$9.99', pages:90},
  {id:'DP1028',name:'Budget & Finance Planner',   price:'$12.99',pages:102},
  {id:'DP1029',name:'Fitness & Wellness Planner', price:'$12.99',pages:91}
];
// ── Products — full catalog file-integrity check (2026-07-15 rebuild) ──
// Previously hardcoded to a ~5-product "Core Products" slice (DP1026-1035)
// left over from when the shop only had a handful of planners. /api/products
// now returns the real 176-product catalog across 14 categories, so this
// screen needs a category filter (same .hub-chip-row/.hub-chip-btn pattern
// already used on Listings' setSectionFilter) rather than one flat list.
let _products = [];
let _productCategoryFilter = null; // null = all categories
const _CATEGORY_LABELS = {
  digital_planner: 'Digital Planners', digital_planner_bundle: 'Planner Bundles',
  wall_art: 'Wall Art', wall_art_bundle: 'Wall Art Bundles',
  svg_bundle: 'SVG Packs', svg_bundle_license: 'SVG Commercial License',
  svg_3dprint_pack: '3D Print SVG Packs',
  sticker_pack: 'Sticker Packs', sticker_pack_license: 'Sticker Commercial License',
  coloring_pages: 'Coloring Pages', paper_pack: 'Paper Packs',
  '3d_print_physical': '3D Printed Physical', sublimation: 'Sublimation',
  uncategorized: 'Uncategorized',
};
function _categoryLabel(cat) { return _CATEGORY_LABELS[cat] || String(cat).replace(/_/g, ' '); }

async function loadProducts() {
  const el = document.getElementById('products-content');
  if (!el) return;
  el.innerHTML = '<div class="hub-spinner"></div>';
  _productCategoryFilter = null;
  try {
    const d = await authGet('/api/products').then(r => r.json());
    _products = d.products || [];
    renderProductsContent();
  } catch(e) {
    el.innerHTML = '<div class="hub-empty">' + escHtml(e.message || 'Failed to load products') + '</div>';
  }
}
function setProductCategoryFilter(key) {
  _productCategoryFilter = key;
  renderProductsContent();
}
function renderProductsContent() {
  const el = document.getElementById('products-content');
  if (!el) return;
  if (!_products.length) { el.innerHTML = '<div class="hub-empty">No products found</div>'; return; }

  const cats = {};
  _products.forEach(p => { cats[p.category] = (cats[p.category] || 0) + 1; });
  const catKeys = Object.keys(cats).sort((a, b) => _categoryLabel(a).localeCompare(_categoryLabel(b)));

  const presentCount = _products.filter(p => p.all_files_present === true).length;
  let html = '<div class="hub-section-title">Products — ' + presentCount + '/' + _products.length + ' have all files present</div>';

  html += '<div class="hub-chip-row">';
  html += '<button class="hub-chip-btn' + (_productCategoryFilter === null ? ' active' : '') + '" onclick="setProductCategoryFilter(null)">All (' + _products.length + ')</button>';
  catKeys.forEach(k => {
    html += '<button class="hub-chip-btn' + (_productCategoryFilter === k ? ' active' : '') + '" onclick="setProductCategoryFilter(\\'' + k + '\\')">' + escHtml(_categoryLabel(k)) + ' (' + cats[k] + ')</button>';
  });
  html += '</div>';

  const filtered = _productCategoryFilter === null ? _products : _products.filter(p => p.category === _productCategoryFilter);
  filtered.forEach(p => {
    const borderColor = p.all_files_present === true ? 'var(--green)' : p.all_files_present === false ? 'var(--red)' : 'var(--muted)';
    let filesLine;
    if (!p.files || !p.files.length) {
      filesLine = 'no files listed in catalog';
    } else if (p.all_files_present) {
      filesLine = '✅ all ' + p.files.length + ' file(s) present';
    } else {
      const missing = p.files.filter(f => !f.exists).map(f => f.name);
      filesLine = '❌ missing: ' + escHtml(missing.join(', '));
    }
    html += '<div class="hub-prod-card" style="border-left-color:' + borderColor + '">' +
      '<div class="hub-prod-name">' + escHtml(p.title || p.id) + '</div>' +
      '<div class="hub-prod-meta">' + escHtml(p.id) + (p.listing_id ? ' · Etsy #' + escHtml(String(p.listing_id)) : '') +
        (p.price != null ? ' · $' + escHtml(String(p.price)) : '') + ' · ' + escHtml(p.status || '') + '</div>' +
      '<div class="hub-prod-files" style="font-size:11px;opacity:0.8;margin-top:3px">' + filesLine + '</div>' +
    '</div>';
  });
  el.innerHTML = html;
}
const _STYLE_ANCHOR_TEXT = "Photography style: bright airy editorial Etsy lifestyle photography. "+
  "Warm cream and natural linen tones throughout. Soft diffused window light "+
  "from the left, warm white balance, gentle shadows to the right. "+
  "Camera at eye level, 50mm lens equivalent, slight depth of field on background. "+
  "No hands, no people, no text overlays, no studio equipment visible.";

function _bkTable(rows, cellStyles){
  let t = '<table style="width:100%;border-collapse:collapse;font-size:12px">';
  rows.forEach(r => {
    t += '<tr style="border-bottom:1px solid var(--border)">';
    r.forEach((cell,i) => { t += '<td style="'+(cellStyles[i]||'padding:7px 0')+'">'+escHtml(cell)+'</td>'; });
    t += '</tr>';
  });
  return t + '</table>';
}

function _bkSectionIdentity(){
  let html = '<div id="bk-identity">';
  html += '<div class="hub-section-title">Shop Identity</div>';
  html += '<div class="hub-card">'+
    '<div style="font-size:15px;font-weight:700">OnBrandCraftz</div>'+
    '<div style="font-size:11.5px;color:var(--muted);margin-top:2px">Owner: Scott &middot; Etsy shop ID: onbrandcraftz</div>'+
    '<div style="font-size:11.5px;color:var(--muted);margin-top:8px;line-height:1.5">'+
    '<b style="color:var(--text)">Niche:</b> Digital planners, kawaii sticker packs, printable digital products, 3D printed physical products.<br>'+
    '<b style="color:var(--text)">Brand aesthetic:</b> Kawaii illustrated, pastel colors, cute and fun but polished.</div>'+
    '</div>';
  html += '<div class="hub-card" style="border-left:3px solid var(--gold)">'+
    '<div style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;font-weight:700">Mission</div>'+
    '<div style="font-size:13px;font-style:italic;margin-top:4px">"Providing the best and most accurate transaction for our customers so we can grow responsibly."</div>'+
    '</div>';
  html += '<div class="hub-card" style="border-left:3px solid var(--red)">'+
    '<div style="font-size:11px;color:var(--red);text-transform:uppercase;letter-spacing:.5px;font-weight:700">Top rule — never lie to the customer</div>'+
    '<div style="font-size:11.5px;color:var(--muted);margin-top:6px;line-height:1.6">'+
    'Every listing photo, description claim, page count, sticker count, and compatibility statement must be verified against '+
    'the real product file before a listing goes live. This overrides every other consideration on this page.</div>'+
    '</div>';
  return html + '</div>';
}

function _bkSectionThemes(){
  let html = '<div id="bk-themes">';
  html += '<div class="hub-section-title">Color Themes (4 live &middot; 12 planned)</div>';
  html += '<div class="hub-card" style="border-left:3px solid var(--amber);font-size:11px;color:var(--muted);line-height:1.6">'+
    '&#9888; <b style="color:var(--text)">Known data conflict, flagged not resolved here:</b> the Product Roadmap table in '+
    'CLAUDE.md lists slightly different planned hex colors for DP1030 to DP1033 than the Theme Catalog entries shown below '+
    '(Sage Garden, Matcha Serenity, Midnight Kawaii, Sunflower Studio). This page shows the richer Theme Catalog values. '+
    'Reconciling CLAUDE.md itself is a separate follow-up for Scott.</div>';
  _BRANDKIT_THEMES.forEach((t,i) => {
    const detailId = 'bk-theme-detail-'+i;
    html += '<div class="hub-card" style="margin-bottom:10px;cursor:pointer" onclick="toggleZip(\\''+detailId+'\\', this.querySelector(\\'.bk-caret\\'))" role="button" tabindex="0">';
    html += '<div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">';
    html += '<div><div style="font-size:12.5px;font-weight:700">'+(t.id ? escHtml(t.id)+' — ' : '')+escHtml(t.name)+
      ' <span style="font-size:9px;font-weight:700;padding:1px 6px;border-radius:8px;margin-left:4px;'+
      (t.live ? 'background:rgba(92,196,138,.18);color:var(--green)' : 'background:rgba(232,184,104,.18);color:var(--amber)')+
      '">'+(t.live ? 'LIVE' : 'PLANNED')+'</span></div>';
    if(t.tagline) html += '<div style="font-size:11px;color:var(--muted);font-style:italic;margin-top:2px">"'+escHtml(t.tagline)+'"</div>';
    html += '</div><span class="bk-caret" style="font-size:13px;color:var(--muted);flex-shrink:0">&#9656;</span></div>';
    html += '<div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px">';
    t.swatches.forEach(c => {
      html += '<div style="display:flex;align-items:center;gap:5px">'+
        '<span class="hub-swatch" style="background:'+escHtml(c.hex)+'"></span>'+
        '<div style="font-size:11px"><div style="color:var(--muted)">'+escHtml(c.label)+'</div>'+
        '<div class="bk-hexcopy" style="font-family:monospace;font-size:10px;color:var(--text);cursor:pointer" '+
        'title="Click to copy" onclick="copyHex(\\''+c.hex+'\\', this); event.stopPropagation()">'+escHtml(c.hex)+'</div></div>'+
        '</div>';
    });
    html += '</div>';
    html += '<div id="'+detailId+'" style="display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--border);font-size:11.5px;color:var(--muted);line-height:1.6">';
    if(t.aesthetic) html += '<div><b style="color:var(--text)">Aesthetic:</b> '+escHtml(t.aesthetic)+'</div>';
    if(t.motifs) html += '<div style="margin-top:4px"><b style="color:var(--text)">Kawaii motifs:</b> '+escHtml(t.motifs)+'</div>';
    if(t.buyer) html += '<div style="margin-top:4px"><b style="color:var(--text)">Target buyer:</b> '+escHtml(t.buyer)+'</div>';
    if(t.bestProduct) html += '<div style="margin-top:4px"><b style="color:var(--text)">Best product:</b> '+escHtml(t.bestProduct)+'</div>';
    if(t.trend) html += '<div style="margin-top:4px"><b style="color:var(--text)">Trend alignment:</b> '+escHtml(t.trend)+'</div>';
    if(!t.aesthetic && !t.motifs && !t.buyer && !t.trend) html += 'No additional detail documented in CLAUDE.md beyond the palette and product mapping above.';
    html += '</div></div>';
  });
  return html + '</div>';
}

function _bkSectionColorRules(){
  let html = '<div id="bk-color-rules">';
  html += '<div class="hub-section-title">Color Design Rules — apply to every product built</div><div class="hub-card">';
  html += '<ol style="margin:0;padding-left:20px;font-size:12px;color:var(--muted);line-height:2">'+
    '<li><b style="color:var(--text)">Maximum 4 colors</b> per product — Primary + Accent + Mid-tone + Neutral, plus black for text.</li>'+
    '<li><b style="color:var(--text)">60-30-10 rule</b> — 60% neutral/background, 30% primary color, 10% accent pops.</li>'+
    '<li><b style="color:var(--text)">Minimum contrast ratio 4.5:1</b> for text on background (WCAG AA accessibility standard).</li>'+
    '<li><b style="color:var(--text)">Never pure black</b> (#000000) — use a deep tinted black matching the palette.</li>'+
    '<li><b style="color:var(--text)">Never pure white</b> (#FFFFFF) — use a cream or tinted neutral instead.</li>'+
    '<li><b style="color:var(--text)">Dark mode backgrounds</b> use #1A1A2E to #2D2D2D — never pure black.</li>'+
    '<li><b style="color:var(--text)">Tab color coding</b> — assign one hue from the palette to each section, vary by saturation.</li>'+
    '<li><b style="color:var(--text)">Weekend vs weekday</b> — weekend calendar cells are 15% lighter than weekday cells.</li>'+
    '<li><b style="color:var(--text)">Cover design rule</b> — the kawaii illustration accent color must match the primary hex exactly.</li>'+
    '<li><b style="color:var(--text)">Consistency across all 10 listing photos</b> — props, backgrounds, and accent items must match the product color theme.</li>'+
    '</ol></div>';
  return html + '</div>';
}

function _bkSectionStickers(){
  let html = '<div id="bk-stickers">';
  html += '<div class="hub-section-title">Sticker &amp; Illustration Standards</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:8px">5-Sheet System — minimum 200+ stickers per pack</div>';
  html += _bkTable([
    ['Sheet 1','Functional Planning','50+','Headers, checklists, flags, action arrows, date dots, labels'],
    ['Sheet 2','Widget Trackers','40+','Mood tracker, water intake, sleep tracker, habit tracker, weekly summary widgets'],
    ['Sheet 3','Planner & Stationery','40+','Notebooks, pens, washi tape, paper clips, sticky notes, scissors, ruler'],
    ['Sheet 4','Cozy Lifestyle','40+','Mugs, candles, books, plants, fairy lights, sleeping cat, cozy blanket'],
    ['Sheet 5','Seasonal & Holiday','40+','Cherry blossoms, sunflowers, pumpkins, snowflakes, 12 major holiday icons'],
  ], ['padding:6px 6px 6px 0;font-weight:700;color:var(--gold);white-space:nowrap','padding:6px','padding:6px;color:var(--muted)','padding:6px 0;color:var(--muted)']);
  html += '</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">14 Functional Sticker Categories</div>'+
    '<div style="font-size:11.5px;color:var(--muted);line-height:1.9">'+
    'Headers &amp; Banners &middot; Checklists &amp; To-Do Boxes &middot; Action Flags &amp; Arrows &middot; Time &amp; Appointment Icons &middot; '+
    'Mood Trackers &middot; Habit &amp; Water Trackers &middot; Date Dots &amp; Numbers &middot; Labels &amp; Category Dots &middot; '+
    'Monthly Tab Dividers &middot; Widget Stickers &middot; Sticky Notes &amp; Page Flags &middot; Motivational Banners &middot; '+
    'Seasonal Markers &middot; Washi Tape Strips</div></div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Kawaii Illustration Rules</div>'+
    '<div style="font-size:11.5px;color:var(--muted);line-height:1.7">'+
    '<b style="color:var(--text)">Proportions:</b> head-to-body ratio 1.5:1 to 2:1, oversized eyes at 40 to 50% of face height, small mouth, blush cheeks, stubby rounded limbs.<br>'+
    '<b style="color:var(--text)">Color:</b> exactly 5 colors from the product palette (primary, accent, mid-tone, neutral, text), plus one pop accent reserved for alerts only '+
    '(warm red #E84040 or amber #FFB347) — never change the base palette.<br>'+
    '<b style="color:var(--text)">Sizing at 300 DPI:</b> decorative icons 200&times;200px, header/banner stickers 800&times;200px, widget stickers 400 to 600px square, washi tape strips 2400&times;120px / 2400&times;80px.</div></div>';
  return html + '</div>';
}

function _bkSectionListingStandards(){
  let html = '<div id="bk-listing-standards">';
  html += '<div class="hub-section-title">Listing Standards by Product Type</div>';
  _BRANDKIT_LISTING_TYPES.forEach(lt => {
    const detailId = 'bk-listing-detail-'+lt.key;
    html += '<div class="hub-card" style="margin-bottom:10px;cursor:pointer" onclick="toggleZip(\\''+detailId+'\\', this.querySelector(\\'.bk-caret\\'))" role="button" tabindex="0">';
    html += '<div style="display:flex;justify-content:space-between;align-items:center">'+
      '<div style="font-size:12.5px;font-weight:700">'+escHtml(lt.icon)+' '+escHtml(lt.label)+'</div>'+
      '<span class="bk-caret" style="font-size:13px;color:var(--muted)">&#9656;</span></div>';
    html += '<div id="'+detailId+'" style="display:none;margin-top:10px;padding-top:10px;border-top:1px solid var(--border);font-size:11.5px;color:var(--muted);line-height:1.7">';
    html += '<div><b style="color:var(--text)">Title:</b> '+escHtml(lt.title)+'</div>';
    html += '<div style="margin-top:6px"><b style="color:var(--text)">Tags:</b> '+escHtml(lt.tags)+'</div>';
    html += '<div style="margin-top:6px"><b style="color:var(--text)">Description sections, in order:</b> '+escHtml(lt.description.join(' &rarr; '))+'</div>';
    html += '<div style="margin-top:6px"><b style="color:var(--text)">Photos:</b> '+escHtml(lt.photos)+'</div>';
    html += '<div style="margin-top:6px"><b style="color:var(--text)">Category:</b> '+escHtml(lt.category)+'</div>';
    html += '</div></div>';
  });
  return html + '</div>';
}

function _bkSectionPricing(){
  let html = '<div id="bk-pricing">';
  html += '<div class="hub-section-title">Pricing Reference</div>';
  html += '<div class="hub-card" style="font-size:11.5px;color:var(--muted)">'+escHtml(_BRANDKIT_PRICING.endingRule)+'</div>';
  const cells = ['padding:7px 8px 7px 0;font-weight:600','padding:7px 8px;color:var(--gold);font-weight:700;white-space:nowrap','padding:7px 0;color:var(--muted)'];
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Digital Planners</div>'+_bkTable(_BRANDKIT_PRICING.planners, cells)+'</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Wall Art</div>'+_bkTable(_BRANDKIT_PRICING.wallArt, cells)+'</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">SVG 3D-Print Packs</div>'+_bkTable(_BRANDKIT_PRICING.svgPacks, cells)+'</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Standalone Sticker Packs</div>'+_bkTable(_BRANDKIT_PRICING.stickerPacks, cells)+'</div>';
  return html + '</div>';
}

function _bkSectionTypography(){
  let html = '<div id="bk-typography">';
  html += '<div class="hub-section-title">Typography &amp; Readability</div><div class="hub-card">';
  html += '<div style="font-size:11.5px;color:var(--muted);line-height:1.8">'+
    '&middot; Minimum font size for fillable fields: 11pt (touch-friendly)<br>'+
    '&middot; Section header labels: 14 to 16pt bold<br>'+
    '&middot; Tab labels: 9 to 11pt, legible at actual iPad screen scale<br>'+
    '&middot; Minimum line height in weekly/daily boxes: 0.5 inches, for handwriting space</div>';
  html += '<div style="font-size:11px;color:var(--amber);margin-top:10px;padding-top:10px;border-top:1px solid var(--border)">'+
    'No specific brand typeface is mandated anywhere in CLAUDE.md — only the numeric legibility rules above. '+
    'Shown honestly rather than inventing a font choice that has not actually been decided.</div>';
  html += '</div>';
  return html + '</div>';
}

function _bkSectionBrandMark(){
  let html = '<div id="bk-brandmark">';
  html += '<div class="hub-section-title">Brand Mark</div><div class="hub-card">';
  html += '<div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">'+
    '<canvas id="brandkit-mark-preview" class="brand-mark-canvas" width="64" height="64" style="border-radius:var(--r-md);background:var(--panel2);border:1px solid var(--border)"></canvas>'+
    '<div style="flex:1;min-width:200px;font-size:11.5px;color:var(--muted);line-height:1.5">'+
    'The orb logo doubles as the shop brand mark. Upload or reset the image used to shape it from Settings.'+
    '</div>'+
    '<button class="act-btn secondary" onclick="showScreen(\\'settings\\')">Manage in Settings &rarr;</button>'+
    '</div></div>';
  return html + '</div>';
}

function copyStyleAnchor(btn){ copyHex(_STYLE_ANCHOR_TEXT, btn); }

function _bkSectionPhotography(){
  let html = '<div id="bk-photography">';
  html += '<div class="hub-section-title">Photography Style</div>';
  html += '<div class="hub-card">'+
    '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">'+
    '<div style="font-size:12px;font-weight:700">Style Anchor — paste identically into every prompt in a batch</div>'+
    '<button class="act-btn secondary" style="font-size:11px" onclick="copyStyleAnchor(this)">Copy</button></div>'+
    '<pre style="white-space:pre-wrap;font-size:11px;color:var(--muted);font-family:monospace;margin:0;line-height:1.6">'+escHtml(_STYLE_ANCHOR_TEXT)+'</pre>'+
    '</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Material Vocabulary</div>'+
    _bkTable([
      ['Linen','natural linen texture, visible weave pattern, slightly rumpled, warm off-white'],
      ['Rattan','natural rattan weave, warm honey-brown tones, slightly matte finish'],
      ['Ceramic','matte ceramic surface, subtle micro-texture, slightly imperfect handmade quality'],
      ['Wood (oak)','natural light oak, visible wood grain, matte satin finish, warm golden undertone'],
      ['Boucle','boucle fabric texture, looped cream-white pile, soft sculptural surface'],
      ['Terracotta','terracotta clay surface, slightly dusty matte texture, warm burnt orange tone'],
    ], ['padding:6px 8px 6px 0;font-weight:600;white-space:nowrap','padding:6px 0;color:var(--muted)'])+'</div>';
  html += '<div class="hub-card"><div style="font-size:12px;font-weight:700;margin-bottom:6px">Lighting Vocabulary</div>'+
    _bkTable([
      ['Morning lifestyle','soft diffused window light from the left, warm white balance, gentle shadow to the right'],
      ['Cozy evening','warm amber lamp glow from upper right, soft ceiling ambient light, no harsh shadows'],
      ['Clean product','bright even natural daylight, diffused overhead, cool-neutral white balance, no shadows on product'],
      ['Golden hour','golden hour backlighting, warm orange-yellow light from upper right, long soft shadows forward'],
    ], ['padding:6px 8px 6px 0;font-weight:600;white-space:nowrap','padding:6px 0;color:var(--muted)'])+'</div>';
  return html + '</div>';
}

function renderBrandKit() {
  const el = document.getElementById('brandkit-content');
  if (!el) return;
  el.innerHTML = _bkSectionIdentity() + _bkSectionThemes() + _bkSectionColorRules() +
    _bkSectionStickers() + _bkSectionListingStandards() + _bkSectionPricing() +
    _bkSectionTypography() + _bkSectionBrandMark() + _bkSectionPhotography();
  if(window._brandMarkDataUrl === undefined){
    loadRuntimeSettings();
  } else {
    renderBrandMarkPreview();
  }
}

// ── Files — real data: /api/files (data/digital_products/ + backups) ──
function _hubFileUrl(f, inline){
  return BASE+'/api/files/download?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    (inline?'&inline=1':'');
}
function _hubZipEntryUrl(f, entryName){
  return BASE+'/api/files/zip-entry?root='+encodeURIComponent(f.root)+'&path='+encodeURIComponent(f.path)+
    '&entry='+encodeURIComponent(entryName);
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
// Brand Kit: click-to-copy for hex codes (also reused as-is for the STYLE_ANCHOR text
// block in the Photography section -- it only needs a string and an element to flash
// "Copied!", nothing hex-specific despite the name). No copy-to-clipboard pattern
// existed anywhere in this file before this.
function copyHex(text, el){
  const value = String(text||'').trim();
  const finish = (ok) => {
    if(el){
      if(el.getAttribute('data-orig-text') === null) el.setAttribute('data-orig-text', el.textContent);
      el.textContent = ok ? 'Copied!' : 'Copy failed';
      clearTimeout(el._bkCopyTimer);
      el._bkCopyTimer = setTimeout(() => { el.textContent = el.getAttribute('data-orig-text'); }, 1200);
    }
    showToast(ok ? ('Copied ' + value) : 'Could not copy — select it manually', ok ? 'ok' : 'err', 2200);
  };
  if(navigator.clipboard && navigator.clipboard.writeText){
    navigator.clipboard.writeText(value).then(() => finish(true)).catch(() => finish(false));
  } else {
    try{
      const ta = document.createElement('textarea');
      ta.value = value; ta.style.position = 'fixed'; ta.style.opacity = '0';
      document.body.appendChild(ta); ta.select();
      const ok = document.execCommand('copy');
      document.body.removeChild(ta);
      finish(ok);
    } catch(e){ finish(false); }
  }
}
function openFile(url){ window.open(url,'_blank'); }
// Files screen grouping: collapse everything that belongs to one product/listing
// (all the DP1032_* files — PDFs, sticker pack, listing images, sheets) into a single
// tappable row, so a 1000+ file volume listing isn't one giant flat scroll. The key
// is the product code embedded in the path (DP1032, SS1001, WA1030, …).
let _hubZipSeq = 0, _hubGrpSeq = 0;
function _productKeyFromPath(path){
  const m = String(path||'').match(/([A-Za-z]{2,5}\\d{3,4})/);
  return m ? m[1].toUpperCase() : null;
}
function _productGroupIcon(key){
  if(/^DP/.test(key)) return '📕';   // digital planners
  if(/^SS/.test(key)) return '✂️';   // SVG cut-file packs
  if(/^WA/.test(key)) return '🖼️';   // wall art
  return '📦';
}
// Render one file (or an expandable ZIP) as a row — shared by the flat and grouped paths.
function _renderHubFileHtml(f){
  const when = new Date(f.modified).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
  if (f.is_zip) {
    const zid='hub-zip-'+(_hubZipSeq++);
    const entries=f.entries||[];
    let h='<div class="hub-listing-item" onclick="toggleZip(\\''+zid+'\\',this.querySelector(\\'.hub-zip-caret\\'))" style="cursor:pointer" role="button" tabindex="0">'+
      '<div class="hub-thumb-ph">🗂️</div>'+
      '<div class="hub-listing-info"><div class="hub-listing-title">'+escHtml(f.path)+'</div>'+
      '<div class="hub-listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+' · '+entries.length+' files inside</div></div>'+
      '<div class="hub-zip-caret" style="color:var(--gold);font-size:16px">▸</div></div>';
    h+='<div id="'+zid+'" style="display:none;margin:0 0 6px 14px;border-left:2px solid var(--border);padding-left:8px">';
    if(!entries.length) h+='<div class="hub-listing-meta" style="padding:8px 0">Could not read this ZIP\\'s contents.</div>';
    entries.forEach(en=>{
      const eurl=_hubZipEntryUrl(f,en.name);
      h+='<div class="hub-listing-item" onclick="openFile(\\''+eurl+'\\')" style="cursor:pointer;padding:7px 4px" role="button" tabindex="0">'+
        '<div class="hub-thumb-ph" style="font-size:16px">'+_hubFileIcon(en.name)+'</div>'+
        '<div class="hub-listing-info"><div class="hub-listing-title" style="font-size:13px">'+escHtml(en.name)+'</div>'+
        '<div class="hub-listing-meta">'+escHtml(en.size_human)+(en.inline?' · tap to open':' · tap to download')+'</div></div>'+
        '<div style="color:var(--gold);font-size:15px">'+(en.inline?'↗':'⬇')+'</div></div>';
    });
    h+='</div>';
    return h;
  }
  const url=_hubFileUrl(f, f.inline?1:0);
  return '<div class="hub-listing-item" onclick="openFile(\\''+url+'\\')" style="cursor:pointer" role="button" tabindex="0">'+
    '<div class="hub-thumb-ph">'+_hubFileIcon(f.path)+'</div>'+
    '<div class="hub-listing-info"><div class="hub-listing-title">'+escHtml(f.path)+'</div>'+
    '<div class="hub-listing-meta">'+escHtml(f.size_human)+' · '+escHtml(when)+(f.inline?' · tap to open':' · tap to download')+'</div></div>'+
    '<div style="color:var(--gold);font-size:18px">'+(f.inline?'↗':'⬇')+'</div></div>';
}
function downloadFullBackup(){
  window.open(BASE+'/api/backup/download-all?token='+encodeURIComponent(TOKEN), '_blank');
  showToast('Building your backup ZIP — this can take a minute for a large one.');
}
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
    _hubZipSeq = 0; _hubGrpSeq = 0;
    groups.forEach(g => {
      if (!g.files.length) return;
      html += '<div class="hub-section-title">'+escHtml(g.label)+' ('+g.files.length+')</div>';

      // Sub-group this group's files by the product/listing code in their path, so
      // all of one product's files collapse into a single tappable row.
      const sub={}, order=[];
      g.files.forEach(f => {
        const k = _productKeyFromPath(f.path) || 'Other files';
        if(!sub[k]){ sub[k]=[]; order.push(k); }
        sub[k].push(f);
      });
      const productKeys = order.filter(k=>k!=='Other files')
        .sort((a,b)=>a.localeCompare(b, undefined, {numeric:true}));

      // No product codes here (e.g. the Backups group) → keep it flat, no needless nesting.
      if (!productKeys.length) {
        html += '<div class="hub-card">';
        g.files.forEach(f => { html += _renderHubFileHtml(f); });
        html += '</div>';
        return;
      }

      const finalOrder = productKeys.concat(sub['Other files'] ? ['Other files'] : []);
      html += '<div class="hub-card">';
      finalOrder.forEach(key => {
        const files = sub[key];
        const gid = 'hub-grp-'+(_hubGrpSeq++);
        const icon = key==='Other files' ? '📄' : _productGroupIcon(key);
        html += '<div class="hub-listing-item" onclick="toggleZip(\\''+gid+'\\',this.querySelector(\\'.hub-grp-caret\\'))" style="cursor:pointer" role="button" tabindex="0">'+
          '<div class="hub-thumb-ph">'+icon+'</div>'+
          '<div class="hub-listing-info"><div class="hub-listing-title">'+escHtml(key)+'</div>'+
          '<div class="hub-listing-meta">'+files.length+' file'+(files.length!==1?'s':'')+'</div></div>'+
          '<div class="hub-grp-caret" style="color:var(--gold);font-size:16px">▸</div>'+
        '</div>';
        html += '<div id="'+gid+'" style="display:none;margin:0 0 6px 8px;border-left:2px solid var(--border);padding-left:8px">';
        files.forEach(f => { html += _renderHubFileHtml(f); });
        html += '</div>';
      });
      html += '</div>';
    });
    el.innerHTML = html;
  } catch(e) {
    el.innerHTML = '<div class="hub-empty">'+escHtml(e.name==='AbortError'?'Request timed out':e.message||'Failed to load files')+'</div>'+
      '<div style="text-align:center;margin-top:8px"><button onclick="loadFiles()" style="background:var(--gold);color:#06141f;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── Studio — real data: /api/studio/* (image-to-video generation, attach-to-Etsy
// staging, Instagram/Facebook posting). Posting always fires only on a direct button
// click — there is no automatic or scheduled trigger anywhere in this code. ──
let _studioSelectedVideo = '';
let _studioUploadedPaths = [];

function _studioVideoUrl(name, inline){
  return BASE+'/api/files/download?root=videos&path='+encodeURIComponent(name)+
    (inline?'&inline=1':'');
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
  fetch('/health').then(r=>r.json()).then(d=>{
    const v = document.getElementById('studio-build-ver');
    if (v && d.build) v.textContent = d.build;
  }).catch(()=>{});
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
  if (e.target && e.target.id === 'studio-style') {
    const isAI = e.target.value === 'ai-scene';
    const aiFields = document.getElementById('studio-ai-fields');
    if (aiFields) aiFields.style.display = isAI ? 'block' : 'none';
    if (isAI) {
      const sp = document.getElementById('studio-scene-prompt');
      if (sp && !sp.value) {
        const t = (document.getElementById('studio-title').value||'').trim();
        const p = (document.getElementById('studio-price').value||'').trim();
        sp.value = 'Cinematic product video of "' + (t||'product') + '"' +
          (p ? ' priced at '+p : '') +
          '. The product sits on a cozy desk with soft natural window light, subtle camera movement, warm ambient atmosphere. Professional product photography style.';
      }
    }
  }
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

// ── SVG Converter — Studio tool. Traces a dropped/picked reference photo into an
// SVG via /api/studio/convert-svg (vtracer under the hood). The "What's this for?"
// target selector picks a sensible default trace mode and shows one honest line of
// guidance per product line — most of our product lines are pure raster and don't
// need a vector file at all, so this never pretends otherwise. For the 3D-Print
// Sign target specifically, the real clean-vector quality gate
// (etsy_api.check_svg_quality — the same thresholds that gate real ZIP uploads)
// runs on every conversion and its actual pass/fail shows up immediately, not a
// guess. ──
const SVGC_TARGETS = {
  '3dprint': {mode:'silhouette', hint:'3D-print signs need clean vectors (≤20 colors, ≤200 paths) for multi-color AMS printing — the quality check below is the real gate, not an estimate. If it fails, try a higher-contrast source photo or Silhouette mode.'},
  'wallart': {mode:'color', hint:'Wall art doesn’t need a vector file — this SVG is just useful as illustrated source art. For the actual print-ready deliverable, run finished art through the existing upscale/print-size pipeline.'},
  'sticker': {mode:'color', hint:'The sticker pipeline works on raster PNGs, not SVGs — this is a clean-line starting point for a new design, not a drop-in replacement for that pipeline.'},
  'planner': {mode:'color', hint:'The planner pipeline is pure PDF/raster — this SVG would need to be rendered to a raster image first if you want to use it as cover art.'},
  'none': {mode:'color', hint:''},
};

function svgcUpdateHint(){
  const targetEl = document.getElementById('svgc-target');
  const modeEl = document.getElementById('svgc-mode');
  const hintEl = document.getElementById('svgc-hint');
  if (!targetEl || !modeEl || !hintEl) return;
  const cfg = SVGC_TARGETS[targetEl.value] || SVGC_TARGETS.none;
  modeEl.value = cfg.mode;
  hintEl.textContent = cfg.hint;
}

document.addEventListener('change', function(e){
  if (e.target && e.target.id === 'svgc-file-input' && e.target.files[0]) svgcConvert(e.target.files[0]);
  if (e.target && e.target.id === 'svgc-target') svgcUpdateHint();
});

(function(){
  const zone = document.getElementById('svgc-dropzone');
  if (!zone) return;
  ['dragover','dragenter'].forEach(function(evt){ zone.addEventListener(evt, function(e){
    e.preventDefault(); e.stopPropagation();
    zone.style.borderColor = 'var(--cyan)'; zone.style.background = 'rgba(242,160,181,.06)';
  }); });
  ['dragleave','dragend'].forEach(function(evt){ zone.addEventListener(evt, function(e){
    e.preventDefault(); e.stopPropagation();
    zone.style.borderColor = 'var(--border)'; zone.style.background = '';
  }); });
  zone.addEventListener('drop', function(e){
    e.preventDefault(); e.stopPropagation();
    zone.style.borderColor = 'var(--border)'; zone.style.background = '';
    const f = e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0];
    if (f) svgcConvert(f);
  });
  svgcUpdateHint();
})();

async function svgcConvert(file){
  if (!file) return;
  const status = document.getElementById('svgc-status');
  const resultEl = document.getElementById('svgc-result');
  const modeEl = document.getElementById('svgc-mode');
  const mode = modeEl ? modeEl.value : 'color';
  if (resultEl) resultEl.style.display = 'none';
  if (status) status.textContent = 'Converting "'+file.name+'"…';
  try {
    const r = await fetchWithTimeout(
      BASE+'/api/studio/convert-svg?mode='+encodeURIComponent(mode),
      {method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body:file},
      45000
    );
    const d = await r.json().catch(function(){ return {}; });
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    const dlUrl = BASE+'/api/files/download?root=svg_conversions&path='+encodeURIComponent(d.path)+'&token='+encodeURIComponent(TOKEN);
    const previewEl = document.getElementById('svgc-preview');
    const downloadEl = document.getElementById('svgc-download');
    if (previewEl) previewEl.src = dlUrl+'&inline=1';
    if (downloadEl) { downloadEl.href = dlUrl; downloadEl.setAttribute('download', d.path); }
    const q = d.quality || {};
    const qEl = document.getElementById('svgc-quality');
    if (qEl) {
      if (q.passes_gate) {
        qEl.innerHTML = '<span style="color:var(--green)">✓ '+q.unique_fills+' colors, '+q.path_count+' paths, '+Math.round(q.size_kb)+'KB — passes the 3D-print clean-vector gate</span>';
      } else {
        const firstProblem = (q.problems && q.problems[0]) ? escHtml(q.problems[0]) : '';
        qEl.innerHTML = '<span style="color:var(--red)">✗ '+q.unique_fills+' colors, '+q.path_count+' paths, '+Math.round(q.size_kb)+'KB — too complex for a color-separated 3D print.</span>'+(firstProblem?'<div style="color:var(--muted);margin-top:4px">'+firstProblem+'</div>':'');
      }
    }
    if (resultEl) resultEl.style.display = 'block';
    if (status) status.textContent = '';
  } catch(e) {
    if (status) status.textContent = 'Conversion failed: '+(e.message||e);
  }
}

// ── Lifestyle Photo Generator — Studio tool. Wraps THE STANDARD LIFESTYLE METHOD
// (tools/listing_photo_pipeline.py::generate_verified_photo, documented in CLAUDE.md):
// upload the REAL product file(s), generate a photorealistic scene, self-verify the
// render against the source, retry on mismatch. Category defaults mirror the
// PHYSICS keys in that module so the "what's this for" choice picks the right
// surface-realism template server-side. Real per-click API cost, so unlike the SVG
// converter this is deliberately capped at 2 attempts, not the pipeline's own 3. ──
const LSG_SCENE_DEFAULTS = {
  'sign_flat': 'displayed on a cozy living room wall above a console table, warm natural window light, a small potted plant and a stack of books as props',
  'tumbler_wrap': 'held on a rustic wooden outdoor table next to a folded picnic blanket, bright natural daylight',
  'framed_print': 'hung on a warm cream gallery wall above a boucle sofa, soft morning light from the left',
  'flat_paper': 'lying flat on a cream linen surface next to a cup of coffee and a small potted succulent',
  'ipad_lifestyle': 'on a cozy wooden desk at a 30-degree angle, a latte and a small succulent nearby, soft window light from the left',
  'sticker_sheet_flat': 'on a clean cream desk surface with washi tape and a pen nearby, bright even overhead light',
  '3d_print_lamp': 'on a nightstand in a softly lit bedroom in the evening, warm ambient light',
  '3d_print_vase': 'on a wooden console table with a few dried flower stems, soft daylight',
  '3d_print_holder': 'on a tidy desk beside a laptop and a cup of pens, bright clean daylight',
  '3d_print_planter': 'on a sunny windowsill, bright natural light',
};

let _lsgUploadedPaths = [];

function lsgFillDefaultPrompt(){
  const catEl = document.getElementById('lsg-category');
  const promptEl = document.getElementById('lsg-scene-prompt');
  if (!catEl || !promptEl) return;
  // Only auto-fill if the box is empty or still holds a PREVIOUS auto-fill --
  // never overwrite something the user actually typed themselves.
  if (!promptEl.value || promptEl.dataset.auto === '1') {
    promptEl.value = LSG_SCENE_DEFAULTS[catEl.value] || '';
    promptEl.dataset.auto = '1';
  }
}

document.addEventListener('change', function(e){
  if (e.target && e.target.id === 'lsg-file-input' && e.target.files.length) lsgUploadFiles(e.target.files);
  if (e.target && e.target.id === 'lsg-category') lsgFillDefaultPrompt();
});
document.addEventListener('input', function(e){
  if (e.target && e.target.id === 'lsg-scene-prompt') e.target.dataset.auto = '0';
});

async function lsgUploadFiles(fileList){
  const status = document.getElementById('lsg-upload-status');
  const files = Array.from(fileList||[]);
  if (!files.length) return;
  _lsgUploadedPaths = [];
  for (let i=0; i<files.length; i++){
    const f = files[i];
    if (status) status.textContent = 'Uploading '+(i+1)+'/'+files.length+'…';
    try {
      const r = await fetchWithTimeout(
        BASE+'/api/studio/upload-image?filename='+encodeURIComponent(f.name),
        {method:'POST', headers:{Authorization:'Bearer '+TOKEN}, body:f},
        30000
      );
      const d = await r.json().catch(function(){ return {}; });
      if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
      _lsgUploadedPaths.push(d.path);
    } catch(e) {
      if (status) status.textContent = 'Upload failed on "'+f.name+'": '+(e.message||e);
      return;
    }
  }
  if (status) status.textContent = _lsgUploadedPaths.length+' file(s) ready to generate.';
}

async function lsgGenerate(){
  const status = document.getElementById('lsg-status');
  const resultEl = document.getElementById('lsg-result');
  const previewWrap = document.getElementById('lsg-preview-wrap');
  const downloadEl = document.getElementById('lsg-download');
  const outcomeEl = document.getElementById('lsg-outcome');
  if (!_lsgUploadedPaths.length) {
    if (status) status.textContent = 'Upload at least one real product file first.';
    return;
  }
  const category = document.getElementById('lsg-category').value;
  const scenePrompt = (document.getElementById('lsg-scene-prompt').value || '').trim();
  if (!scenePrompt) {
    if (status) status.textContent = 'Scene description is required.';
    return;
  }
  if (resultEl) resultEl.style.display = 'none';
  const btn = document.getElementById('lsg-generate-btn');
  if (btn) btn.disabled = true;
  if (status) status.textContent = 'Generating — this can take up to a couple of minutes (real image generation + verification against your file)…';
  try {
    const r = await fetchWithTimeout(
      BASE+'/api/studio/generate-lifestyle-photo',
      {method:'POST', headers:{Authorization:'Bearer '+TOKEN, 'Content-Type':'application/json'},
       body: JSON.stringify({design_paths:_lsgUploadedPaths, category:category, scene_prompt:scenePrompt})},
      290000
    );
    const d = await r.json().catch(function(){ return {}; });
    if (!r.ok) throw new Error(d.detail||'HTTP '+r.status);
    if (d.ok && d.path) {
      const dlUrl = BASE+'/api/files/download?root=lifestyle_photos&path='+encodeURIComponent(d.path)+'&token='+encodeURIComponent(TOKEN);
      const previewEl = document.getElementById('lsg-preview');
      if (previewEl) previewEl.src = dlUrl+'&inline=1';
      if (downloadEl) { downloadEl.href = dlUrl; downloadEl.setAttribute('download', d.path); downloadEl.style.display = 'block'; }
      if (previewWrap) previewWrap.style.display = 'block';
      if (outcomeEl) outcomeEl.innerHTML = '<span style="color:var(--green)">✓ Passed verification (attempt '+d.attempts+') — matches your real product file.</span>';
    } else {
      if (previewWrap) previewWrap.style.display = 'none';
      if (downloadEl) downloadEl.style.display = 'none';
      const firstIssue = (d.issues && d.issues[0]) ? escHtml(d.issues[0]) : '';
      let headline;
      if (d.failure_kind === 'service_error') {
        // A transient image-service error (e.g. Gemini 500), NOT a product mismatch —
        // retrying usually clears it; nothing is wrong with the uploaded file.
        headline = '⚠ The image service had a temporary error — no problem with your file. Please try again in a moment.';
      } else {
        headline = '✗ Failed verification after '+(d.attempts||0)+' attempt(s) — the render did not reliably match your source file.';
      }
      if (outcomeEl) outcomeEl.innerHTML = '<span style="color:var(--red)">'+headline+'</span>'+(firstIssue?'<div style="color:var(--muted);margin-top:4px">'+firstIssue+'</div>':'');
    }
    if (resultEl) resultEl.style.display = 'block';
    if (status) status.textContent = '';
  } catch(e) {
    if (status) status.textContent = 'Generation failed: '+(e.message||e);
  } finally {
    if (btn) btn.disabled = false;
  }
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
  if (style === 'ai-scene') {
    body.scene_prompt = (document.getElementById('studio-scene-prompt').value||'').trim();
    body.aspect_ratio = document.getElementById('studio-aspect-ratio').value || '9:16';
  }
  const reqTimeout = style === 'ai-scene' ? 310000 : 185000;

  btn.disabled = true;
  btn.textContent = '⏳ Generating…';
  if (status) status.innerHTML = '<div class="hub-spinner" style="margin:10px auto"></div>';
  try {
    const r = await fetchWithTimeout(BASE+'/api/studio/generate', {
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'}, body:JSON.stringify(body)
    }, reqTimeout);
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
  {name:'Pinterest', icon:'📌', status:'roadmap',note:'Frank-side wiring done (2026-07-17) — only OAuth remains', steps:[
    'Create a Pinterest Developer app at developers.pinterest.com',
    'Add PINTEREST_APP_ID and PINTEREST_APP_SECRET to .env',
    'Run: python tools/pinterest_oauth.py — authorizes and saves tokens to .env automatically',
    'Claim the Etsy shop under Pinterest "Claimed accounts" to enable Rich Pins',
    'Already done: ask Frank to stage a pin (uses the listing\\'s own Etsy photo) — it queues in the Action Center for your one-tap approval, same as every other Etsy/social change'
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
  {name:'TikTok',    icon:'🎵', status:'roadmap',note:'⚠️ Credentials leaked & removed — need rotating first', steps:[
    'The old TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET were found leaked in git history and removed — TikTok will not work until these are replaced',
    'Generate a NEW Client Key + Secret at the TikTok for Developers portal (do not reuse the old ones)',
    'Add the new TIKTOK_CLIENT_KEY / TIKTOK_CLIENT_SECRET to .env and Railway',
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
      {label:'Anthropic (Claude)',   ok:an.api_key,         note:'%%AGENT_NAME%% (CEO) · Conversion Doctor · tag gen'},
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
          : '<div style="font-size:11px;font-weight:700;color:var(--muted);cursor:pointer;white-space:nowrap" onclick="toggleCredSteps(\\''+key+'\\')" role="button" tabindex="0">🗺️ Roadmap ›</div>')+
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
      '<div style="text-align:center;margin-top:8px"><button onclick="loadConnections()" style="background:var(--gold);color:#06141f;border:none;border-radius:var(--r-sm);padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer">Retry</button></div>';
  }
}

// ── Settings → Connections summary card — same data as the Connections screen, condensed ──
async function loadSettingsConnectionsSummary() {
  const el = document.getElementById('settings-connections-summary');
  if (!el) return;
  try {
    const [cr, tr] = await Promise.all([
      authGet('/api/credentials/status', 15000),
      authGet('/api/etsy-tokens', 15000)
    ]);
    const cred = await cr.json().catch(()=>({}));
    const tok = await tr.json().catch(()=>({}));
    // Reuses the `cred` this call already fetched (zero extra network cost) --
    // catches a Premium-voice toggle already stuck ON from an earlier session
    // the moment Settings is opened, before it ever gets a chance to fail
    // silently on a real reply. See _verifyPremiumVoiceConfigured() above.
    _verifyPremiumVoiceConfigured(cred);
    let ageText = 'unknown';
    if (tok.updated_at) {
      const days = Math.floor((Date.now() - new Date(tok.updated_at).getTime()) / 86400000);
      ageText = days + ' day'+(days===1?'':'s')+' old'+(days>=75?' — re-auth before day 90':'');
    }
    const ageColor = (tok.updated_at && Math.floor((Date.now() - new Date(tok.updated_at).getTime()) / 86400000) >= 75) ? 'var(--red)' : 'var(--muted)';
    el.innerHTML = (cred.etsy_live
      ? '<div style="color:var(--green);font-size:14px;font-weight:700">✅ Etsy Live</div><div style="font-size:11px;color:var(--muted);margin-top:4px">'+escHtml(cred.shop_name||'onbrandcraftz')+'</div>'
      : '<div style="color:var(--red);font-size:14px;font-weight:700">⚠️ Etsy Ping Failed</div><div style="font-size:11px;color:var(--muted);margin-top:4px">'+escHtml(cred.etsy_live_error||'Unknown error')+'</div>')
      + '<div style="font-size:11px;color:'+ageColor+';margin-top:8px">Refresh token: '+escHtml(ageText)+'</div>';
  } catch(e) {
    el.innerHTML = '<div style="color:var(--red);font-size:11px">Connections summary offline</div>';
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
    {ok:true, label:'Staged action queue',                 note:'Every Etsy change requires %%OWNER%% one-tap approval'},
    {ok:null, label:'Etsy MFA enabled?',                   note:'Verify in Etsy → Account Settings → Security'},
    {ok:null, label:'Outlook 2FA active?',                 note:'Verify at account.microsoft.com → Security'},
    {ok:null, label:'Pinterest wired, not authorized yet', note:'Frank can stage a pin already — run python tools/pinterest_oauth.py so approvals can actually post'},
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
  // Backgrounded tab: the setInterval timer below keeps firing (cheap — it's just a JS
  // timer), but every tick becomes a no-op until the tab is visible again, at which
  // point the visibilitychange listener triggers one immediate catch-up refresh
  // (2026-07-08 performance pass).
  if (document.hidden) return;
  _GLOBAL_LOADERS.forEach(fn => fn());
  (_SCREEN_LOADERS[_activeScreen] || []).forEach(fn => fn());
}
document.addEventListener('visibilitychange', () => {
  if (!document.hidden) loadAll();
});

// Storage-durability guard: /health reports whether the DB is on a durable volume.
// If not, every change resets on restart — surface a loud, un-dismissible banner so
// data loss can never happen silently (see main.py db.is_persistent()).
let _persistWarnDismissed = false;
function dismissPersistWarning(){
  _persistWarnDismissed = true;
  const el = document.getElementById('persist-warning');
  if(el) el.classList.remove('show');
}
async function checkPersistence(){
  try{
    const r = await fetch('/health', {cache:'no-store'});
    if(!r.ok) return;
    const j = await r.json();
    const el = document.getElementById('persist-warning');
    // Respect a manual dismiss — don't re-show it this session (it's ephemeral storage,
    // so it returns on a fresh reload until the /data volume is attached).
    if(el) el.classList.toggle('show', !_persistWarnDismissed && j && j.persistent === false);
  }catch(e){ /* health unreachable — don't block the HUD */ }
}
// _activeScreen defaults to 'cmd' (the screen marked active in the HTML), so this
// initial loadAll() fires the same globals + cmd-screen loaders as before. The five
// screens formerly eager-loaded here unconditionally (actions/calendar/memory/
// conversations/kb/workflows) now load on first navigation via showScreen()'s own
// dispatch instead — they show "Loading…" on first visit rather than being silently
// pre-fetched in the background (2026-07-08 performance pass).
loadAll();
setInterval(loadAll, 30000);

// ── Operator chip — load current user from /api/me ──
let _myRole = 'admin';
async function loadOperatorChip(){
  try {
    const r = await fetchWithTimeout(BASE+'/api/me',{headers:{Authorization:'Bearer '+TOKEN}},5000);
    if(!r.ok) return;
    const d = await r.json();
    const uname = d.username || '?';
    const role  = (d.role || 'admin').toUpperCase();
    _myRole = d.role || 'admin';
    document.getElementById('op-av').textContent   = uname[0].toUpperCase();
    document.getElementById('op-name').textContent = uname;
    document.getElementById('op-role').textContent = role;
    // User Management UI was removed (solo shop) — nothing owner-specific to reveal here now.
  } catch(e){ /* silent */ }
}
loadOperatorChip();

async function doLogout(){
  if(!confirm('Log out of %%AGENT_SHORT%%?')) return;
  await fetch(BASE+'/logout',{method:'POST'}).catch(()=>{});
  location.href='/login';
}

// ── User management (owner only) ──
async function loadUsers(){
  const el = document.getElementById('user-list');
  if(!el) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/admin/users',{headers:{Authorization:'Bearer '+TOKEN}},5000);
    if(!r.ok){ el.innerHTML='<div style="color:var(--muted);font-size:11px">Failed to load users</div>'; return; }
    const d = await r.json();
    if(!d.users||!d.users.length){ el.innerHTML='<div style="color:var(--muted);font-size:11px">No users yet.</div>'; return; }
    el.innerHTML = d.users.map(u=>`
      <div style="display:flex;align-items:center;justify-content:space-between;padding:7px 0;border-bottom:1px solid var(--border)">
        <div>
          <span style="font-size:12px;font-weight:600">${u.username}</span>
          <span style="font-size:10px;color:var(--muted);margin-left:6px">${u.role.toUpperCase()}</span>
          <div style="font-size:10px;color:var(--muted)">${u.created_at||''}</div>
        </div>
        <div style="display:flex;gap:6px">
          ${u.role!=='owner'?`<button class="act-btn secondary" style="font-size:10px;padding:3px 7px" onclick="resetUserPw('${u.username}')">Reset PW</button>
          <button class="act-btn danger" style="font-size:10px;padding:3px 7px" onclick="deleteUser('${u.username}')">Remove</button>`:''}
        </div>
      </div>`).join('');
  } catch(e){ el.innerHTML='<div style="color:var(--muted);font-size:11px">Error loading users</div>'; }
}

async function addUser(){
  const uname = (document.getElementById('new-user-name').value||'').trim();
  const pw    = (document.getElementById('new-user-pw').value||'').trim();
  const st    = document.getElementById('user-add-status');
  if(!uname||!pw){ st.textContent='Username and password are required.'; return; }
  st.textContent='Adding…';
  try {
    const r = await fetchWithTimeout(BASE+'/api/admin/users',{
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},
      body:JSON.stringify({username:uname,password:pw,role:'admin'})
    },8000);
    const d = await r.json();
    if(!r.ok){ st.textContent=d.detail||'Error'; return; }
    st.textContent=`✓ ${uname} added`;
    document.getElementById('new-user-name').value='';
    document.getElementById('new-user-pw').value='';
    loadUsers();
    // Blocking alert is deliberate here, not an oversight — this code is shown
    // exactly once and never stored in plaintext anywhere, so it needs to be
    // impossible to accidentally dismiss without reading (same reasoning as a
    // password manager's one-time backup-code screen).
    if (d.recovery_code) {
      alert(`Save ${uname}'s account recovery code now — it will never be shown again:\n\n${d.recovery_code}\n\nThis is what "Forgot password?" on the sign-in screen will ask for if ${uname} ever loses their password. Write it down or save it in a password manager.`);
    }
  } catch(e){ st.textContent='Network error'; }
}

async function deleteUser(uname){
  if(!confirm(`Remove user "${uname}"?`)) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/admin/users/'+uname,{
      method:'DELETE', headers:{Authorization:'Bearer '+TOKEN}
    },5000);
    const d = await r.json();
    if(!r.ok){ showToast(d.detail||'Error removing user'); return; }
    showToast(`${uname} removed`);
    loadUsers();
  } catch(e){ showToast('Network error'); }
}

async function resetUserPw(uname){
  const pw = prompt(`New password for "${uname}":`);
  if(!pw||!pw.trim()) return;
  try {
    const r = await fetchWithTimeout(BASE+'/api/admin/users/'+uname+'/reset-password',{
      method:'POST', headers:{Authorization:'Bearer '+TOKEN,'Content-Type':'application/json'},
      body:JSON.stringify({password:pw.trim()})
    },8000);
    const d = await r.json();
    if(!r.ok){ showToast(d.detail||'Error'); return; }
    showToast(`Password reset for ${uname}`);
  } catch(e){ showToast('Network error'); }
}

// ── Clock ──
function tick(){
  const d = new Date();
  document.getElementById('clk').textContent = d.toLocaleTimeString([], {hour:'2-digit',minute:'2-digit',second:'2-digit'});
  document.getElementById('dt').textContent = d.toLocaleDateString([], {weekday:'long',month:'long',day:'numeric',year:'numeric'});
}
tick(); setInterval(tick, 1000);


// ── Orb: idle rotating wireframe particle cloud, audio-reactive on click. Default
// shape is a sphere; uploading a Settings > Brand Mark image swaps the particle
// generator to sample that image's silhouette instead — the rotation/projection/
// glow/audio-reactive rendering in frame() below is shared by both and untouched. ──
const canvas = document.getElementById('orb');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height, CX = W/2, CY = H/2, R = 230;
let orbMode = 'sphere';
// Image mode (a custom brand-mark logo) is a real extruded slab, not a single point
// cloud: front face + back face (each {x0,y0,z0}) connected by mesh edges, plus a
// sparse set of "strut" edges only along the true outer silhouette so it reads as a
// solid object with thickness rather than every internal line growing a pointless
// vertical bar. See applyBrandMarkToOrb below for how these are built.
let imgFront = [], imgBack = [], imgFrontEdges = [], imgBackEdges = [], imgStruts = [];

// Default ("sphere") mode is a real Three.js/WebGL noise-displaced icosphere,
// rendered directly onto the visible #orb-gl canvas (2026-07-15 native-alpha
// rewrite — see the long CSS comment on canvas#orb-gl for the full history of
// what NOT to retry here). Two canvases live in the DOM permanently: 2D #orb
// for image mode, WebGL #orb-gl for sphere mode; only one is shown at a time,
// toggled by setOrbCanvasMode(). Image mode keeps using the #orb 2D canvas
// exactly as before — applyBrandMarkToOrb is untouched.
const orbGlCanvas = document.getElementById('orb-gl');
function setOrbCanvasMode(mode){
  orbMode = mode;
  if(mode === 'image'){
    if(orbGlCanvas) orbGlCanvas.style.display = 'none';
    canvas.style.display = '';
    orbGLPaused = true;
  } else {
    canvas.style.display = 'none';
    // CSS default for #orb-gl is display:none (so it never flashes visible
    // before JS decides the mode); 'block' is needed here, not '' — an empty
    // inline style would just fall back to that CSS default and stay hidden.
    if(orbGlCanvas){ orbGlCanvas.style.display = 'block'; initOrbGL(); orbGLPaused = false; }
  }
}
function resetOrbToDefault(){
  imgFront = []; imgBack = []; imgFrontEdges = []; imgBackEdges = []; imgStruts = [];
  setOrbCanvasMode('sphere');
}

// ── WebGL voice-reactive noise-sphere (default "sphere" mode) — Three.js, vendored
// under /static/vendor/three/ (no CDN — CSP is script-src 'self' only). A wireframe
// icosphere whose vertices are displaced along their normals by a 3D simplex noise
// field in the vertex shader (GPU-side, so it stays smooth even at high triangle
// counts). uAmp is driven by REAL TTS playback amplitude via an AnalyserNode tapped
// off the premium-voice <audio> element (see currentVoiceAmp()/_setupTtsAnalyser
// below) — the old orb-state label claimed "reacting to live TTS amplitude" while
// actually running a fake dual-sine pulse; this makes that claim true. Glow comes
// from the CSS drop-shadow filter on canvas#orb-gl, not internal bloom — see the
// CSS comment there for why UnrealBloomPass was removed outright (2026-07-15). ──
let orbGLPaused = true, orbGLReady = false, orbGLLoading = false;
let glMesh = null, glScene = null, glCamera = null, glRenderer = null, glClock = null, glUniforms = null;

const _ORB_NOISE_GLSL = `
vec3 mod289(vec3 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 mod289(vec4 x){ return x - floor(x * (1.0/289.0)) * 289.0; }
vec4 permute(vec4 x){ return mod289(((x*34.0)+1.0)*x); }
vec4 taylorInvSqrt(vec4 r){ return 1.79284291400159 - 0.85373472095314 * r; }
float snoise(vec3 v){
  const vec2 C = vec2(1.0/6.0, 1.0/3.0);
  const vec4 D = vec4(0.0, 0.5, 1.0, 2.0);
  vec3 i  = floor(v + dot(v, C.yyy));
  vec3 x0 = v - i + dot(i, C.xxx);
  vec3 g = step(x0.yzx, x0.xyz);
  vec3 l = 1.0 - g;
  vec3 i1 = min(g.xyz, l.zxy);
  vec3 i2 = max(g.xyz, l.zxy);
  vec3 x1 = x0 - i1 + C.xxx;
  vec3 x2 = x0 - i2 + C.yyy;
  vec3 x3 = x0 - D.yyy;
  i = mod289(i);
  vec4 p = permute(permute(permute(
             i.z + vec4(0.0, i1.z, i2.z, 1.0))
           + i.y + vec4(0.0, i1.y, i2.y, 1.0))
           + i.x + vec4(0.0, i1.x, i2.x, 1.0));
  float n_ = 0.142857142857;
  vec3 ns = n_ * D.wyz - D.xzx;
  vec4 j = p - 49.0 * floor(p * ns.z * ns.z);
  vec4 x_ = floor(j * ns.z);
  vec4 y_ = floor(j - 7.0 * x_);
  vec4 x = x_ * ns.x + ns.yyyy;
  vec4 y = y_ * ns.x + ns.yyyy;
  vec4 h = 1.0 - abs(x) - abs(y);
  vec4 b0 = vec4(x.xy, y.xy);
  vec4 b1 = vec4(x.zw, y.zw);
  vec4 s0 = floor(b0)*2.0 + 1.0;
  vec4 s1 = floor(b1)*2.0 + 1.0;
  vec4 sh = -step(h, vec4(0.0));
  vec4 a0 = b0.xzyw + s0.xzyw*sh.xxyy;
  vec4 a1 = b1.xzyw + s1.xzyw*sh.zzww;
  vec3 p0 = vec3(a0.xy, h.x);
  vec3 p1 = vec3(a0.zw, h.y);
  vec3 p2 = vec3(a1.xy, h.z);
  vec3 p3 = vec3(a1.zw, h.w);
  vec4 norm = taylorInvSqrt(vec4(dot(p0,p0), dot(p1,p1), dot(p2,p2), dot(p3,p3)));
  p0 *= norm.x; p1 *= norm.y; p2 *= norm.z; p3 *= norm.w;
  vec4 m = max(0.6 - vec4(dot(x0,x0), dot(x1,x1), dot(x2,x2), dot(x3,x3)), 0.0);
  m = m * m;
  return 42.0 * dot(m*m, vec4(dot(p0,x0), dot(p1,x1), dot(p2,x2), dot(p3,x3)));
}
`;

const _ORB_VERT = _ORB_NOISE_GLSL + `
uniform float uTime;
uniform float uAmp;
uniform float uFreq;
void main(){
  // Two noise octaves, not one: a LOW-frequency layer makes a handful of big, graceful
  // lobes (the "waviness" of the whole silhouette), a higher-frequency layer riding on
  // top adds the finer surface crinkle -- a single mid-frequency octave (the original
  // approach) couldn't do both at once, so the ball read as gently fuzzy rather than
  // genuinely wavy/lumpy like the reference.
  float nBig = snoise(position * (uFreq * 0.42) + vec3(0.0, 0.0, uTime * 0.7));
  float nFine = snoise(position * (uFreq * 2.2) + vec3(0.0, 0.0, uTime * 1.4));
  // uAmp's contribution bumped up (0.32->0.60, 0.10->0.24) so idle vs. actively-speaking
  // is a clear, distinct ripple rather than a subtle shift on top of the already-large
  // baseline waviness (Scott: wants "active ripples reactive to what he is saying").
  float disp = 0.20 + nBig * (0.42 + uAmp * 0.60) + nFine * (0.08 + uAmp * 0.24);
  vec3 newPos = position + normal * disp;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(newPos, 1.0);
}
`;

const _ORB_FRAG = `
uniform vec3 uColor;
uniform float uOpacity;
void main(){
  gl_FragColor = vec4(uColor, uOpacity);
}
`;

async function initOrbGL(){
  if(orbGLReady || orbGLLoading) return;
  orbGLLoading = true;
  try{
    const THREE = await import('/static/vendor/three/build/three.module.js');

    glScene = new THREE.Scene();
    glCamera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    // z was 3.4, which framed the UNDISPLACED radius-1.15 sphere nicely but ignored
    // that the vertex shader pushes peaks out to ~1.7 (idle) and ~2.15 (speaking).
    // At z=3.4 the frustum half-height is only 3.4*tan(21deg)=1.305 world units, so
    // those peaks projected to NDC>1 -- i.e. OFF the canvas entirely -- and got hard-
    // clipped by the render target before the CSS mask ever applied. That is the real
    // "outer texture cut off" bug, and why re-tuning the mask 3x (v122/v141/v143) never
    // fixed it. Pulling the camera back to 6.5 (half-height ~2.49) seats the full wavy
    // silhouette + speaking ripples inside the frame with margin, so the whole crumpled
    // edge is visible and floats, matching Scott's reference GIFs.
    glCamera.position.z = 6.5;

    glRenderer = new THREE.WebGLRenderer({canvas: orbGlCanvas, alpha:true, antialias:true});
    // Real transparent clear (2026-07-15, native-alpha rewrite). Two earlier
    // approaches operated downstream of UnrealBloomPass's render-to-texture
    // composite, which does not preserve true per-pixel alpha to the final
    // output (full history on the canvas#orb-gl CSS comment below): a
    // setClearColor(0,0) clear under bloom still came out opaque black, and
    // painting the theme's own --bg color in as an opaque clear crossed
    // bloom's brightness threshold and blew the whole frame to white. This
    // rewrite removes EffectComposer/UnrealBloomPass entirely and renders in a
    // single native pass (glRenderer.render(glScene, glCamera) in
    // orbGLFrame()) -- standard, well-trodden behavior that DOES preserve
    // real alpha straight to the canvas, no intermediate buffer or JS pixel
    // manipulation needed. Glow now comes only from the CSS drop-shadow
    // filter on canvas#orb-gl (see #orb-view canvas#orb-gl below).
    glRenderer.setClearColor(0x000000, 0);
    glRenderer.setPixelRatio(Math.min(window.devicePixelRatio||1, 2));
    glRenderer.setSize(640, 640, false);

    const geo = new THREE.IcosahedronGeometry(1.15, 16);
    glUniforms = {
      uTime: {value: 0},
      uAmp: {value: 0},
      uFreq: {value: 1.6},
      uColor: {value: new THREE.Color('rgb(242,160,181)')},
      uOpacity: {value: 0.85},
    };
    const mat = new THREE.ShaderMaterial({
      vertexShader: _ORB_VERT,
      fragmentShader: _ORB_FRAG,
      uniforms: glUniforms,
      wireframe: true,
      transparent: true,
    });
    glMesh = new THREE.Mesh(geo, mat);
    glScene.add(glMesh);

    glClock = new THREE.Clock();

    orbGLReady = true;
    orbGLLoading = false;
    requestAnimationFrame(orbGLFrame);
  }catch(e){
    orbGLLoading = false;
    console.error('[orb-gl] WebGL noise-sphere failed to initialize — orb will stay blank in sphere mode until this is fixed', e);
  }
}

// ── WebGL context loss recovery (2026-07-15) — "the orb freezes after
// switching tabs and back." Mobile Safari/Chrome aggressively lose a page's
// WebGL context when the tab/app is backgrounded, to free GPU memory under
// pressure -- a well-documented platform behavior, not a bug in this specific
// scene. Before this fix there was NO webglcontextlost/webglcontextrestored
// handling anywhere: when the context died, glRenderer/glMesh/glScene still
// held references to now-invalid GPU resources, so orbGLFrame()'s
// glRenderer.render(...) call kept "succeeding" (Three.js silently no-ops on a
// dead context) while drawing nothing new -- the canvas just froze on
// whatever the last good frame was, forever, since nothing ever told it to
// rebuild. The canvas DOM element itself survives context loss (only the GL
// context dies), so these listeners are attached once, here, not inside
// initOrbGL() (which only runs once normally due to its own orbGLReady/
// orbGLLoading guard).
if (orbGlCanvas) {
  orbGlCanvas.addEventListener('webglcontextlost', function(e){
    // preventDefault() is required for the browser to even attempt automatic
    // restoration later -- without it, the context is permanently dead and
    // no 'webglcontextrestored' event will ever fire.
    e.preventDefault();
    orbGLReady = false;
    orbGLLoading = false;
    glRenderer = null; glMesh = null; glScene = null; glCamera = null; glClock = null; glUniforms = null;
    console.warn('[orb-gl] WebGL context lost (tab backgrounded/GPU memory pressure) — will rebuild on restore');
  });
  orbGlCanvas.addEventListener('webglcontextrestored', function(){
    console.info('[orb-gl] WebGL context restored — rebuilding the noise-sphere');
    initOrbGL();
  });
}

function orbGLFrame(){
  requestAnimationFrame(orbGLFrame);
  // Skip the full Three.js render (bloom post-processing included) when the orb isn't
  // actually on screen: the tab is backgrounded, or the dashboard's Control Center is
  // open (#orb-view and the 18-screen dashboard are mutually exclusive via 'cc-open' on
  // body). Previously this ran unconditionally forever (2026-07-08 performance pass).
  if(orbGLPaused || !orbGLReady || document.hidden || document.body.classList.contains('cc-open')) return;
  const dt = glClock.getDelta();
  const amp = currentVoiceAmp();
  glUniforms.uTime.value += dt * (0.12 + amp*0.5);
  glUniforms.uAmp.value = amp;
  glUniforms.uColor.value.setRGB((58+(122-58)*amp)/255, (214+(232-214)*amp)/255, 1.0);
  glUniforms.uOpacity.value = 0.65 + amp*0.3;
  glMesh.rotation.y += (_reducedMotion ? 0 : 0.0022) + amp*0.01;
  glMesh.rotation.x += (_reducedMotion ? 0 : 0.0006) + amp*0.003;
  // Single native render pass straight to the visible canvas (2026-07-15,
  // native-alpha rewrite) -- no offscreen buffer, no readback, no per-pixel JS
  // manipulation. glRenderer was created with alpha:true and a real transparent
  // clear (see initOrbGL()), so this correctly preserves per-pixel alpha to
  // canvas#orb-gl directly; the page background shows through wherever the
  // scene is empty, with no dependency on bloom thresholds or buffer timing.
  glRenderer.render(glScene, glCamera);
}

resetOrbToDefault();

// Flood-fill the NOT-ink region starting from the grid border (4-connectivity). A kept
// ("ink") cell adjacent to a flood-reached cell touches the image's true background —
// i.e. it's on the real outer silhouette, not an inner hole (like inside an "S" loop,
// or the gap between the S and J). Used to decide which cells get a front-to-back
// "strut" edge — only the true outer edge should look like it has physical thickness;
// interior ink stays two flat parallel layers, not a forest of vertical bars.
function classifyOuterSilhouette(keep, GRID){
  const reached = new Array(GRID*GRID).fill(false);
  const stack = [];
  for(let gx=0; gx<GRID; gx++){
    if(!keep[gx]) { reached[gx]=true; stack.push([0,gx]); }
    const lastRow = (GRID-1)*GRID+gx;
    if(!keep[lastRow]) { reached[lastRow]=true; stack.push([GRID-1,gx]); }
  }
  for(let gy=0; gy<GRID; gy++){
    if(!keep[gy*GRID]) { reached[gy*GRID]=true; stack.push([gy,0]); }
    const lastCol = gy*GRID+(GRID-1);
    if(!keep[lastCol]) { reached[lastCol]=true; stack.push([gy,GRID-1]); }
  }
  while(stack.length){
    const [gy,gx] = stack.pop();
    const nbrs = [[gy-1,gx],[gy+1,gx],[gy,gx-1],[gy,gx+1]];
    for(const [ny,nx] of nbrs){
      if(ny<0||ny>=GRID||nx<0||nx>=GRID) continue;
      const idx = ny*GRID+nx;
      if(reached[idx] || keep[idx]) continue;
      reached[idx] = true;
      stack.push([ny,nx]);
    }
  }
  const outer = new Array(GRID*GRID).fill(false);
  for(let gy=0; gy<GRID; gy++){
    for(let gx=0; gx<GRID; gx++){
      if(!keep[gy*GRID+gx]) continue;
      const nbrs = [[gy-1,gx],[gy+1,gx],[gy,gx-1],[gy,gx+1]];
      for(const [ny,nx] of nbrs){
        const outOfBounds = ny<0||ny>=GRID||nx<0||nx>=GRID;
        if(outOfBounds || reached[ny*GRID+nx]){ outer[gy*GRID+gx] = true; break; }
      }
    }
  }
  return outer;
}

function rgbToHue(r,g,b){
  r/=255; g/=255; b/=255;
  const max=Math.max(r,g,b), min=Math.min(r,g,b), d=max-min;
  const sat = max===0 ? 0 : d/max;
  let h = 0;
  if(d!==0){
    if(max===r) h = ((g-b)/d) % 6;
    else if(max===g) h = (b-r)/d + 2;
    else h = (r-g)/d + 4;
    h *= 60; if(h<0) h += 360;
  }
  return {hue:h, sat};
}
// "Layered Design" made literal: a color-based depth offset added on top of the
// front/back split below, so differently-colored parts of the logo (e.g. a gold "S"
// vs a teal "J") visibly separate from each other as the slab rotates, not just from
// front to back as one flat pair of planes. Bucketed by hue so this works generically
// for any future upload, not hardcoded to this specific logo's colors. Low-saturation
// (near-black/near-white) pixels — typically body text — get no offset, sitting at
// the base depth of whichever face they're on.
function colorZOffset(data, gx, gy, GRID, magnitude){
  const idx = (gy*GRID+gx)*4;
  const {hue,sat} = rgbToHue(data[idx],data[idx+1],data[idx+2]);
  if(sat < 0.25) return 0;
  if(hue < 90) return +magnitude;
  if(hue < 180) return -magnitude;
  if(hue < 270) return -magnitude*0.4;
  return +magnitude*0.4;
}

function applyBrandMarkToOrb(dataUrl){
  const img = new Image();
  img.onload = () => {
    const GRID = 240;
    const T_SLAB = R * 0.7;       // extrusion thickness — "noticeably deeper" per Scott
    const COLOR_MAG = R * 0.25;   // secondary per-color depth offset within each face
    const MAX_PER_FACE = 2600;    // tuned against measured frame time, see comment below
    const off = document.createElement('canvas');
    off.width = GRID; off.height = GRID;
    const octx = off.getContext('2d', {willReadFrequently:true});
    const s = Math.min(GRID/img.width, GRID/img.height);
    const dw = img.width*s, dh = img.height*s;
    octx.drawImage(img, (GRID-dw)/2, (GRID-dh)/2, dw, dh);
    const data = octx.getImageData(0,0,GRID,GRID).data;
    // Detect real transparency from an INSET region only, skipping the outer few px.
    // A non-square image centered in this square grid leaves a razor-thin transparent
    // letterbox margin at the edges even when the source has no real alpha channel —
    // scanning the full grid falsely flags that margin as "has alpha", which then makes
    // the alpha-threshold path treat the whole opaque background as part of the mark
    // (reproduced live on a 312x320 flat JPEG logo — it rendered as a solid dot-filled
    // rectangle instead of the logo's actual silhouette until this inset was added).
    let hasAlpha = false;
    const inset = Math.max(2, Math.round(GRID*0.06));
    for(let gy=inset; gy<GRID-inset && !hasAlpha; gy++){
      for(let gx=inset; gx<GRID-inset; gx++){
        if(data[(gy*GRID+gx)*4+3] < 250){ hasAlpha = true; break; }
      }
    }
    const keep = new Array(GRID*GRID).fill(false);
    for(let gy=inset; gy<GRID-inset; gy++){
      for(let gx=inset; gx<GRID-inset; gx++){
        const idx = (gy*GRID+gx)*4;
        // Unpainted canvas pixels default to rgba(0,0,0,0) — fully transparent, but
        // reading as "black" (luminance 0) if alpha is ignored. Gate both branches on
        // alpha>40 so the sub-pixel letterbox margin (see the hasAlpha comment above)
        // can't masquerade as dark ink in the luminance path either.
        keep[gy*GRID+gx] = data[idx+3] > 40 && (hasAlpha || (data[idx]+data[idx+1]+data[idx+2])/3 < 235);
      }
    }
    // Cells within `inset` of the grid border are left false (never "ink"), same margin
    // as the hasAlpha check above. Reproduced live: a resize/JPEG edge artifact along the
    // image's literal last pixel row read as faint "ink" and, once misread as part of a
    // real boundary, rendered as a long stray line far from the real logo. Real logo art
    // virtually always has padding well inside this margin, so excluding it costs nothing
    // for a normal upload but closes off this whole class of edge noise.
    let keptCount = 0;
    for(let i=0;i<keep.length;i++) if(keep[i]) keptCount++;
    if(keptCount < 8) return;  // too sparse to read as a shape — keep whatever orb is active

    // Dense whole-shape dot grid (samples the FILLED mask, not just its outline) with
    // real front/back extrusion + a per-color depth offset — "more dots and more 3D...
    // I want a dot grid" plus the "Layered Design" color-separation idea, combined per
    // Scott's direction. Full density (every filled cell, both faces) measured ~26fps in
    // a worst-case headless/no-GPU render — too heavy to run continuously on a real
    // phone. A diagonal-checkerboard half-thin (keep cells where gx+gy is even) measured
    // a smooth 60fps while still landing ~20% denser than the previous outline-only
    // version — the density/smoothness trade a senior-design pass should actually make,
    // not just "more particles at any cost." Only fall back to further integer-stride
    // thinning on top of that for a logo dense enough to still exceed budget.
    const useCheckerboard = keptCount > MAX_PER_FACE;
    const halvedCount = useCheckerboard ? Math.ceil(keptCount/2) : keptCount;
    const stride = Math.max(1, Math.ceil(Math.sqrt(halvedCount/MAX_PER_FACE)));
    const outer = classifyOuterSilhouette(keep, GRID);

    const idxF = new Array(GRID*GRID).fill(-1), idxB = new Array(GRID*GRID).fill(-1);
    const front = [], back = [], struts = [];
    for(let gy=0; gy<GRID; gy++){
      for(let gx=0; gx<GRID; gx++){
        if(useCheckerboard && (gx+gy)%2!==0) continue;
        if(!keep[gy*GRID+gx] || gx%stride!==0 || gy%stride!==0) continue;
        const nx = (gx/(GRID-1))*2-1, ny = (gy/(GRID-1))*2-1;   // -1..1
        const cz = colorZOffset(data, gx, gy, GRID, COLOR_MAG);
        idxF[gy*GRID+gx] = front.length; front.push({x0:nx*R, y0:ny*R, z0:+T_SLAB/2+cz});
        idxB[gy*GRID+gx] = back.length;  back.push({x0:nx*R, y0:ny*R, z0:-T_SLAB/2+cz});
        if(outer[gy*GRID+gx]) struts.push([idxF[gy*GRID+gx], idxB[gy*GRID+gx]]);
      }
    }
    // When the checkerboard thin is active, same-parity neighbors along a row/col are 2
    // grid-steps apart (the cell in between is the opposite, filtered-out parity) — the
    // adjacency search radius has to account for that or it finds nothing and every dot
    // renders disconnected. Same flat-array bounds-check fix as before on the x-search
    // (a stray-edge bug already found and fixed once at this resolution — see the
    // 2026-07-08 v119 ops_runbook entry).
    const searchStride = stride * (useCheckerboard ? 2 : 1);
    function buildFaceEdges(idxLookup){
      const eg = [];
      for(let gy=0; gy<GRID; gy++){
        for(let gx=0; gx<GRID; gx++){
          const here = idxLookup[gy*GRID+gx];
          if(here < 0) continue;
          for(let dx=1; dx<=searchStride && gx+dx<GRID; dx++){ const r = idxLookup[gy*GRID+(gx+dx)]; if(r>=0){ eg.push([here,r]); break; } }
          for(let dy=1; dy<=searchStride; dy++){ const b = idxLookup[(gy+dy)*GRID+gx]; if(b>=0){ eg.push([here,b]); break; } }
        }
      }
      return eg;
    }
    imgFront = front; imgBack = back;
    imgFrontEdges = buildFaceEdges(idxF); imgBackEdges = buildFaceEdges(idxB);
    imgStruts = struts;
    setOrbCanvasMode('image');
  };
  img.src = dataUrl;
}

let rot = 0, speaking = false, speakT = 0;
const orbState = document.getElementById('orb-state');
const talkSub = document.getElementById('talk-sub');

// Shared amplitude source for BOTH orb render paths (2D image-mode wobble and the
// WebGL sphere's uAmp) — real RMS amplitude read off the actual TTS audio via
// _setupTtsAnalyser() below when available, falling back to the old synthetic
// dual-sine pulse only when there's no audio graph to analyze (the plain
// speechSynthesis fallback voice has no MediaElementSource to tap). speakT keeps
// advancing whenever speaking regardless of which branch supplies the amplitude, so
// the existing wobble/flow terms that key off speakT stay animated either way.
function currentVoiceAmp(){
  if(!speaking) return 0;
  speakT += 0.18;
  if(_ttsAnalyser && _ttsAnalyserBuf){
    _ttsAnalyser.getByteTimeDomainData(_ttsAnalyserBuf);
    let sumSq = 0;
    for(let i=0;i<_ttsAnalyserBuf.length;i++){ const v = (_ttsAnalyserBuf[i]-128)/128; sumSq += v*v; }
    const rms = Math.sqrt(sumSq/_ttsAnalyserBuf.length);
    // Typical speech RMS sits well under 1.0 — scale up so normal speech reads as a
    // healthy, visible pulse rather than a barely-there flicker.
    return Math.min(1, rms*3.2);
  }
  return (Math.sin(speakT*3.1)*0.5+0.5) * (Math.sin(speakT*1.7)*0.3+0.7);
}

function frame(){
  // Default ("sphere") mode renders entirely on the WebGL #orb-gl canvas now (see
  // orbGLFrame below) — this 2D canvas is hidden in that mode, so skip all 2D work
  // rather than waste CPU drawing something nobody sees.
  if(orbMode === 'sphere' || document.hidden || document.body.classList.contains('cc-open')){ requestAnimationFrame(frame); return; }
  ctx.clearRect(0,0,W,H);
  rot += speaking ? 0.028 : (_reducedMotion ? 0 : 0.010);
  const amp = currentVoiceAmp();
  const glow = speaking ? 0.55 + amp*0.45 : 0.3;
  ctx.shadowBlur = 18 + amp*36;
  ctx.shadowColor = speaking ? 'rgba(247,195,208,'+glow+')' : 'rgba(242,160,181,0.3)';

  // Batch every line/dot into a single path each (one stroke()/fill() call for the
  // whole frame) instead of a per-edge/per-dot beginPath+stroke pattern — with
  // thousands of particles at the sampling resolution used below, one beginPath+
  // stroke() PER segment would tank the frame rate; one path for all segments is the
  // standard canvas2D fix and keeps this smooth even at a few thousand points.
  function project(x0, y0, z0, wobMag){
    const wob = speaking ? amp*wobMag*Math.sin((x0+y0)*0.02 + speakT*2) : 0;
    const rx = x0*(1+wob), rz = z0*(1+wob);
    const x = rx*Math.cos(rot) - rz*Math.sin(rot);
    const z = rx*Math.sin(rot) + rz*Math.cos(rot);
    const y = y0*(1+wob);
    const scale = 683 / (683 - z);
    return {x: CX + x*scale*0.92, y: CY + y*scale*0.92, z, scale};
  }

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
  ctx.strokeStyle = speaking ? 'rgba(247,195,208,0.22)' : 'rgba(242,160,181,0.10)';
  ctx.lineWidth = 0.4;
  ctx.beginPath();
  imgBackEdges.forEach(([ai,bi])=>{ const a=backPts[ai], b=backPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
  ctx.stroke();

  ctx.strokeStyle = speaking ? 'rgba(247,195,208,0.30)' : 'rgba(242,160,181,0.14)';
  ctx.lineWidth = 0.45;
  ctx.beginPath();
  imgStruts.forEach(([fi,bi])=>{ const a=frontPts[fi], b=backPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
  ctx.stroke();

  ctx.shadowBlur = frontShadow; ctx.shadowColor = frontShadowColor;
  ctx.strokeStyle = speaking ? 'rgba(247,195,208,0.5)' : 'rgba(242,160,181,0.22)';
  ctx.lineWidth = 0.5;
  ctx.beginPath();
  imgFrontEdges.forEach(([ai,bi])=>{ const a=frontPts[ai], b=frontPts[bi]; if(a&&b){ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);} });
  ctx.stroke();

  // Back dots must read as clearly BEHIND the front, not equally prominent, or an
  // off-angle/edge-on view of the rotation looks like two unrelated overlapping
  // copies instead of one solid object with a near side and a far side.
  ctx.shadowBlur = 0;
  ctx.fillStyle = speaking ? 'rgba(247,195,208,0.28)' : 'rgba(242,160,181,0.16)';
  ctx.beginPath();
  backPts.forEach(p=>{ const sz=p.scale>1?1.0:0.65; ctx.moveTo(p.x+sz,p.y); ctx.arc(p.x,p.y,sz,0,Math.PI*2); });
  ctx.fill();

  ctx.shadowBlur = frontShadow; ctx.shadowColor = frontShadowColor;
  ctx.fillStyle = speaking ? 'rgba(247,195,208,0.9)' : 'rgba(242,160,181,0.65)';
  ctx.beginPath();
  frontPts.forEach(p=>{ const sz=p.scale>1?1.4:0.9; ctx.moveTo(p.x+sz,p.y); ctx.arc(p.x,p.y,sz,0,Math.PI*2); });
  ctx.fill();

  const grad = ctx.createRadialGradient(CX,CY,8,CX,CY,55+amp*30);
  grad.addColorStop(0, speaking ? 'rgba(255,214,224,'+ (0.7+amp*0.25) +')' : 'rgba(242,160,181,0.4)');
  grad.addColorStop(1, 'rgba(242,160,181,0)');
  ctx.fillStyle = grad;
  ctx.beginPath();ctx.arc(CX,CY,55+amp*30,0,Math.PI*2);ctx.fill();

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
    ? (viaFallback ? '%%AGENT_SHORT%% is speaking… (free voice)' : '%%AGENT_SHORT%% is speaking…')
    : 'tap to speak';
}
canvas.addEventListener('click', toggleVoiceCapture);
if(orbGlCanvas) orbGlCanvas.addEventListener('click', toggleVoiceCapture);
const talkPillEl = document.getElementById('talk-pill');
if(talkPillEl) talkPillEl.addEventListener('click', toggleVoiceCapture);

</script>
</body>
</html>"""


_frank_html_cache: str | None = None  # cached rendered HTML


def render_frank_hud() -> str:
    """Render the Frank HUD template with business-identity substitutions.
    Auth uses session cookies — APP_SECRET_TOKEN is never injected into the HTML.
    Business-identity placeholders ("Fucking Frank"/"Frank"/"Scott") are substituted
    here — longest literal first so "Fucking Frank" isn't mangled by the "Frank" pass.
    The result is cached so repeated requests don't redo the 3× str.replace() on
    the ~400 KB HTML string on every hit."""
    global _frank_html_cache
    if _frank_html_cache is not None:
        return _frank_html_cache
    html = _FRANK_HUD_MOCKUP
    html = html.replace("%%AGENT_NAME%%", business_config.AGENT_NAME)
    html = html.replace("%%AGENT_SHORT%%", business_config.AGENT_NAME_SHORT)
    html = html.replace("%%OWNER%%", business_config.OWNER_NAME)
    _frank_html_cache = html
    return html
