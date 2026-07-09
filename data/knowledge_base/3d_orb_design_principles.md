# 3D Orb / Particle Brand-Mark Design Principles — July 2026

Research synthesis for the Frank HUD's animated orb (currently: a rotating extruded
letterform built from evenly-spaced beads along straight polygon edges, front+back faces
connected by corner rods, cyan glow on dark background — see `frank_hud_mockup.py` and
the 2026-07-08 ops_runbook entries for the full build history). Multi-source WebSearch
synthesis; a scripted 28-agent deep-research workflow was attempted first but hit a hard
account session-limit mid-run (0 usable output) — this doc is from direct, targeted
searches instead. Confidence noted per section; several areas have thin formal literature
and lean on the reference photo Scott provided (a beaded wire "A" sculpture) as the
primary source of truth over generic web results.

---

## 1. Precedents — how real AI-assistant orbs work

**High confidence.** Siri, ElevenLabs' Orb component (Three.js/React Three Fiber, used
across many voice-agent products), and similar "voice AI orb" implementations share a
consistent grammar:
- **Audio reactivity is the core mechanic, not decoration.** A real-time amplitude signal
  (mic input or TTS output level) drives glow intensity, motion, and sometimes particle
  behavior. States are typically named `idle`/`listening`/`thinking`/`talking`, each with
  a distinct but related visual treatment.
- **Glow + organic motion over sharp geometric motion.** Shader-based implementations use
  procedural noise for fluid, "breathing" movement rather than mechanical rotation alone.
- **Our orb already matches this pattern**: `speaking` state drives `amp` (amplitude) which
  scales glow blur, jitter, and rotation speed — this is the right foundational mechanic,
  validated against real precedent, not just improvised.

Sources: [ElevenLabs UI Orb docs](https://ui.elevenlabs.io/docs/components/orb), [Building a Voice Reactive Orb in React (Medium)](https://medium.com/@therealmilesjackson/building-a-voice-reactive-orb-in-react-audio-visualization-for-voice-assistants-2bee12797b93), [Siri Orb (SmoothUI)](https://smoothui.dev/docs/components/siri-orb)

---

## 2. Bead/wire sculpture typography — thin formal literature, lean on the reference

**Low-medium confidence from web search; the reference photo is the real source of truth
here.** Generic typography-as-art research surfaced beaded textile/sculptural letterforms
as an established fine-art technique (e.g. artist Jeffrey Gibson's beaded compositions),
confirming the *category* is legitimate design language, but no source gave concrete
spacing ratios or bead-to-gap guidance.

**What the reference photo itself teaches (higher confidence — direct observation):**
- Beads are spaced with **visible, roughly-equal gaps** — never touching, never so sparse
  the eye can't connect them into a line. The bead diameter looks like roughly 1/3 to 1/2
  of the gap between bead centers — a bead-forward, not gap-forward, ratio.
- Every polygon **vertex gets a bead**, and edges are **straight**, not curved — the
  letterform reads as faceted/angular even where the source glyph has curves. This matches
  our polygon-simplification approach (Douglas-Peucker) rather than a raw pixel-perimeter
  trace.
- The extrusion is a **single flat depth** (front face + back face, parallel), connected by
  **straight rods only at true corners** — not a rod at every bead. This is exactly the
  `struts` restricted to `vertexIndices` (not every point) already implemented.

Sources: [Typography as art examples (Creative Bloq)](https://www.creativebloq.com/typography/as-art-11135363), [Letterform (Graphic Design Thoughts)](https://graphicdesignthoughts.blog/courses/typography-ii/assignments-arts-081/archived-assignments-arts-081/letterform-1/letterform/)

---

## 3. Point-density and legibility

**Medium confidence — general point-cloud/dot-density findings, applied by analogy.**
- Dot-density visualizations lose legibility past a density threshold — single-pixel
  markers fail once point density exceeds roughly one point per pixel; sparse point clouds
  (low points-per-unit-area) only resolve coarse shape, while fine detail needs
  proportionally more.
- **Direct implication for the orb, confirmed empirically this session:** a single fixed
  bead-spacing value across the whole logo under-serves small elements (the "DESIGN"
  subtext consistently read as garbled at spacing tuned for the larger monogram/"LAYERED"
  wordmark) while over-serving large ones. **Actionable fix not yet implemented:** scale
  bead spacing per-loop, proportional to that loop's own bounding-box size, rather than one
  global spacing constant — small text loops should get a smaller spacing than the
  monogram, not the same one.

Sources: [Dot density (ArcGIS Pro docs)](https://pro.arcgis.com/en/pro-app/latest/help/mapping/layer-properties/dot-density.htm), [Point Cloud Density Explained (LinkedIn)](https://www.linkedin.com/pulse/point-cloud-density-explained-peter-jackson)

---

## 4. Glow/bloom/neon aesthetics — restraint is the rule

**High confidence, consistent across sources.**
- Glow should serve a **functional purpose** (state feedback) more than pure decoration —
  our speaking-state glow boost already does this correctly.
- **Oversaturation risk factors identified:** blur so heavy it reduces real contrast/detail
  (directly relevant — this is exactly what forced the shadowBlur-only-on-front-layer fix
  earlier this session, now confirmed as the *correct* call, not just a perf hack); glow
  applied uniformly at max intensity with no idle/active distinction; neon-on-black with
  insufficient underlying contrast causing eye strain over prolonged viewing.
- Current implementation already follows the "restraint" guidance: modest idle glow
  (shadowBlur 18), boosted only when speaking (up to 54), never applied to the dimmed back
  layer. No change needed here — validates rather than changes current tuning.

Sources: [Neon Mode: Building a new Dark UI (Codista)](https://www.codista.com/de/blog/neon-mode-building-new-dark-ui/), [Glow and Glass Effects in Dark Websites (Design Systems Collective)](https://www.designsystemscollective.com/building-glow-and-glass-ui-components-in-dark-themes-css-examples-ae402ade54d2)

---

## 5. Motion design for rotating 3D marks

**High confidence, specific numbers given.**
- **Rotation speed:** one full cycle in **5–8 seconds** reads as elegant; faster reads as
  gimmicky/dizzying, much slower reads as static/lifeless.
  - **Current orb math:** idle rotation increments `rot` by 0.010 rad/frame. At 60fps that's
    0.6 rad/sec → a full 2π rotation in **~10.5 seconds** — slightly slower than the 5–8s
    "elegant" range, but not by a wide margin. Not urgent, but a candidate tuning knob
    (`0.010` → ~`0.013-0.015`) if the orb ever feels too static.
- **Easing over constant velocity:** slow-in/slow-out reads as more deliberate/premium than
  perfectly linear rotation. **Current implementation uses constant angular velocity (no
  easing)** — a real, unimplemented gap. Low effort to add (modulate the rotation
  increment with a slow sinusoidal envelope) if worth the complexity trade-off.
- **Anchor at center of mass** so the mark spins cleanly, not around an off-center point —
  already true (`CX, CY` are the canvas center and all geometry is built symmetric around
  origin before rotation).

Sources: [How to Make a Rotating Logo (Logomentary)](https://logomentary.com/blog/how-to-make-a-rotating-logo-2d-animation-and-3d-rotation/), [3D Logo Animation best practices](https://www.tripo3d.ai/blog/explore/3d-rotating-logo-generator)

---

## 6. Formal design-system guidance (Apple HIG)

**High confidence — directly quotable, and surfaces a real accessibility gap.**
- **"Purposeful motion"**: motion should communicate state, not decorate — our
  state-tied glow/rotation-speed changes satisfy this.
- **"Avoid gratuitous animation"** — don't animate for animation's sake. Worth keeping in
  mind if further "make it more 3D / more dots" requests keep escalating visual complexity
  without a corresponding functional reason.
- **"Make motion optional"** — respect `prefers-reduced-motion`; minimize/eliminate
  animation when it's set. **This is a real, unimplemented gap**, and a notable one given
  the WCAG 2.2 AA accessibility pass shipped earlier the same day (2026-07-08, v115) did
  NOT cover this — the orb's continuous rotation currently runs unconditionally regardless
  of the visitor's OS-level reduced-motion preference. Concrete fix: check
  `window.matchMedia('(prefers-reduced-motion: reduce)').matches` and if true, either skip
  the idle rotation entirely (static frame) or drop to a much slower/subtler animation,
  while still allowing the click-to-talk interaction and speaking-state feedback to work.

Sources: [Apple HIG — Motion](https://developer.apple.com/design/human-interface-guidelines/motion), [Apple HIG — Loading](https://developer.apple.com/design/human-interface-guidelines/loading)

---

## Concrete takeaways — ranked by actionability

1. **Adaptive bead spacing per loop size** (not one global constant) — directly addresses
   the recurring "small text is garbled" issue seen across every density tuning pass this
   session. Highest-value unimplemented fix.
2. **`prefers-reduced-motion` support** — a real accessibility gap surfaced by this
   research, not by the earlier WCAG pass. Should be logged as a follow-up alongside the
   other deferred a11y items from the 2026-07-08 security/accessibility batch.
3. **Rotation speed** (0.010 → ~0.013 rad/frame) and **easing** (slow-in/slow-out instead
   of constant velocity) — minor, optional polish, not urgent.
4. **Everything else already matches researched best practice** (audio-reactive glow as
   the core mechanic, restrained/state-tied glow intensity, front/back extrusion with
   corner-only struts, center-anchored rotation) — this is a validation of decisions
   already made this session under live iteration with Scott, not new direction.
