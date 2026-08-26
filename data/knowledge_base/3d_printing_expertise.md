# 3D Printing Expertise — Design + Slicer Settings — 2026-08-21

Built at Scott's explicit request ("make Frank and yourself experts... from
the actual 3D design to the slicer settings") via targeted multi-source
WebSearch across both halves of the discipline. This doc is the **slicer
settings + general design-for-manufacturing (DfAM) reference** — practical
knowledge for advising Scott on any print, judging whether a model will
actually print well, and tuning Bambu Studio for a specific part/material.

**This is a different doc than `.claude/skills/3d-print-design/SKILL.md`.**
That skill is the hard-won, bug-specific playbook for *writing OpenSCAD
code* (real CGAL pitfalls, BOSL2 technique, verified working patterns) —
load it before writing a `.scad` script. This doc is the broader
knowledge: what makes a design printable in general, and how to actually
slice/print it well once it's a mesh, on Scott's real machine. The two
are meant to be read together — this doc for judgment and slicer settings,
that skill for the actual code.

Printer hardware specs (P1S, AMS 2 Pro, materials, nozzles) are already
fully documented in root `CLAUDE.md`'s "3D Printer — Bambu Lab P1S"
section — not repeated here except where a specific number changes a
setting recommendation.

---

## Part 1 — Design for 3D Printing (DfAM)

### 1.1 Wall thickness

- **Rule of thumb: design walls at 2-3× the nozzle diameter** for
  continuous extrusion and strong layer bonding. At the shop's stock
  0.4mm nozzle, that's **0.8-1.2mm minimum** for anything structural —
  matches this shop's own existing convention (2.4mm = 3× nozzle,
  documented in the design skill) for handled/stressed parts, with
  thinner (down to ~0.8mm) acceptable for purely decorative, unhandled
  pieces.
- **Minimum for snaps/fasteners/protrusions specifically: >1.5mm** — these
  concentrate stress at a small cross-section, so the general minimum
  isn't enough.
- **Fillet wall-to-base transitions with ≥1mm radius.** Sharp internal
  corners concentrate stress AND are physically hard for the nozzle to
  trace cleanly — a real print-quality issue, not just a strength one.
- Post-processing (sanding, machining, coatings) adds/removes real
  material — design functional-fit walls with that margin already in mind
  if the piece will be finished afterward.

Source: [BigRep — Designing Wall Thickness](https://bigrep.com/posts/designing-wall-thickness-for-3d-printing/), [JLC3DP Design Guidelines](https://jlc3dp.com/help/article/3d-printing-design-guideline)

### 1.2 Tolerances, shrinkage, and hole/contour compensation

- **Base FDM tolerance is roughly ±0.05–0.50mm** depending on feature size
  and calibration quality; a commonly-cited practical figure for a
  well-tuned printer is **±0.3mm**.
- **Material shrinkage (design-time compensation target):** PLA
  0.3–0.5%, PETG ~0.5%, ABS 0.7–0.8%, ASA/Nylon 1.5–2.0%, PEEK 1.2–1.5%.
  A part with tight-fit features in ABS/ASA needs more compensation
  margin than the same part in PLA — don't reuse a PLA-tuned tolerance
  when switching material.
- **Holes print smaller than designed** (the nozzle drags material toward
  the hole's center on the XY plane) — **contours print slightly larger**
  than designed for the same reason (outward drag on an outer perimeter).
  Bambu Studio has a real feature for this: **XY Hole/Contour
  Compensation** (Print Settings → Advanced). Positive hole compensation
  = holes print bigger; positive contour compensation = shrinks the outer
  contour. Dial this in with Bambu Studio's own calibration test model
  (search MakerWorld "XY Hole and Contour Calibration") rather than
  guessing — measure a printed test piece, compute the correction, apply,
  reprint to confirm.
- **Practical snap-fit/moving-part clearance for FDM: ~0.5mm** between a
  hook and its catch — tighter clearances are unreliable because FDM part
  variance (warping, over-extrusion, layer inconsistency) eats a
  meaningfully tight tolerance. Don't design snap-fits assuming
  machining-level (~0.1mm) precision.

Sources: [FDM Accuracy — Craftcloud](https://support.craftcloud3d.com/en/articles/31-fdm-3d-printing-accuracy-tolerances-wall-thickness-and-limitations), [Bambu Wiki — XY Hole/Contour Compensation](https://wiki.bambulab.com/en/software/bambu-studio/xy-hole-contour-compensation), [UnionFab — Snap Fit Guide](https://www.unionfab.com/blog/2025/06/3d-print-snap-fit)

### 1.3 Overhangs, bridging, and supports

- **The 45° rule is the baseline heuristic** (anything steeper than 45°
  from vertical needs support) — but modern cooling and thin layers do
  better: **0.1mm layers can often manage 55-60° overhangs cleanly with
  no support**. This shop's production settings already default to
  0.2mm for most work and 0.1mm for fine detail (per CLAUDE.md) — knowing
  the finer layer height also buys steeper unsupported overhangs is a
  real, usable lever when a design has a borderline overhang and adding
  supports would hurt surface quality more than tightening the layer
  height would.
- **Bridging is NOT the same physics as an overhang** — a bridge spans
  between two anchored points in tension (pulled straight), not
  cantilevered and drooping. **FDM can bridge 50–80mm cleanly** with good
  bridging settings (higher fan, sometimes a slight speed reduction);
  spans beyond that typically need support regardless of settings.
- **Tree (organic) supports vs. normal (grid) supports — pick by
  geometry, not by habit:**
  - **Tree supports**: figurines, organic/curved shapes. Uses 30-50% less
    material, easier removal, less scarring, better surface finish where
    contact is minimal. This is the right default for anything like the
    pumpkin/ghost/vase work in this shop's catalog.
  - **Normal/grid supports**: mechanical parts with large FLAT
    horizontal overhangs (e.g. the underside of a shelf) — a uniform grid
    with a real support interface layer gives more even, predictable
    support across the whole flat area than tree supports would.
  - **Always enable support interface** (0.20–0.25mm gap is the common
    default) regardless of which type — this is what actually controls
    how easily supports separate cleanly vs. tearing the surface.
  - Consider raising the slicer's overhang-support threshold from the
    45° default to **50°** to avoid over-supporting shallow overhangs
    that don't actually need it.

Sources: [Wevolver — Overhangs Guide](https://www.wevolver.com/article/3d-print-overhang), [printpal — Supports Guide](https://printpal.io/wiki/supports-guide)

### 1.4 Anisotropy — FDM parts are NOT uniformly strong

- **XY-plane strength is typically 4-5× higher than Z-axis strength.**
  This isn't a defect to work around case-by-case — it's a real material
  property of every FDM print, because layer-to-layer bonds are
  inherently weaker than the continuous filament path within a layer.
- **Design/orientation rule: align the load path with the layers, not
  across them.** A bracket that will be pulled or flexed should be
  oriented so that force runs parallel to the print layers (in-plane),
  not perpendicular (trying to pull layers apart). Laying a load-bearing
  part flat instead of printing it standing up is very often the single
  biggest strength lever available, more than infill % or wall count.
- This directly informs orientation choices for this shop's functional
  physical prints (phone stand, organizers, hooks/brackets if ever
  built) — always ask "which direction will this actually be
  stressed?" before deciding print orientation, not just "which
  orientation looks best" or "which needs the least support."

Source: [MLC CAD — Why FDM Prints Are Weaker on Z](https://www.mlc-cad.com/resources/3d-printing/why-fdm-3d-prints-are-weaker-on-the-z-axis-anisotropy-explained/), [RapidMade — Isotropic vs Anisotropic](https://rapidmade.com/isotropic-vs-anisotropic-strength-in-3d-printing/)

### 1.5 Snap-fits, living hinges, threads

- **Snap-fit clearance**: ~0.5mm between hook and catch (see 1.2). Three
  types: cantilever (most common, simplest), annular (ring/cap-style),
  torsion (twist-to-lock). The deflecting arm's own wall thickness
  should sit in the same 1.5-2.5mm band as a living hinge beam (below) —
  thin enough to flex, thick enough not to snap on the first cycle.
- **Living hinges**: beam thickness **1.5-2.5mm** for FDM. Orient the
  hinge so it flexes **parallel to the print layers**, not across them
  (a hinge that flexes across layers is flexing across the weak
  anisotropic axis and will crack fast). PLA hinges work for a limited
  cycle count before brittleness kills them — PP, Nylon, or TPU are the
  real choices for anything meant to flex repeatedly. This shop doesn't
  currently print PP/Nylon; if a living-hinge product idea ever comes
  up, that's a real material gap to flag before committing to the design.
- **Threads**: three real options for FDM — (a) print threads directly
  (works for coarse/low-precision threads, e.g. a jar lid, needs a
  generous pitch and some tolerance built in), (b) heat-set brass
  inserts (melted into a plain printed hole with a soldering iron — the
  standard approach for anything that needs real mechanical thread
  strength, e.g. a lid that gets tightened repeatedly), (c) tap threads
  directly into a slightly-undersized printed hole (works in tougher
  materials like PETG/ABS, less reliable in PLA which can crack).

Sources: [RapidMade — Snap Fits & Living Hinges for MJF](https://rapidmade.com/designing-snap-fits-and-living-hinges-for-mjf-3d-printing-a-complete-guide-for-pa11-pa12-and-pp/), [Mandarin3D — Snap-Fit Design](https://mandarin3d.com/blog/how-to-design-parts-that-snap-fit-together), [Mandarin3D — Living Hinges](https://mandarin3d.com/blog/designing-living-hinges-for-flexible-3d-prints)

### 1.6 Infill — pattern and density by actual purpose

- **Gyroid = the default "strong per gram" choice.** Distributes stress
  isotropically across all three axes (unlike grid/lines patterns, which
  are directionally strong), prints about as fast as cubic, much faster
  than honeycomb. This should be the default infill pattern for any
  functional (not purely decorative) print in this shop's catalog unless
  a specific reason points elsewhere.
- **Cubic** is the other real isotropic-strength option, similar
  properties to gyroid.
- **Honeycomb** trades print speed for a genuinely different strength
  profile — best Young's modulus (stiffness) in some studies, and
  specifically strong under impact/ballistic-style loading — worth
  knowing about but not a default; use it only if a part specifically
  needs impact resistance over general strength.
- **Practical density guidance**: "3-4 walls with 30% gyroid/cubic infill"
  consistently outperforms "2 walls with 80% infill" for real-world
  strength — **wall count matters more than infill % once infill is
  already in a reasonable range.** For this shop's own default (per
  CLAUDE.md's Production Quality Settings), that means: don't reach for
  "just increase infill %" as the first fix for a part that feels weak —
  check wall count first.
- **By use case**: decorative/display-only → low infill (10-15%) is
  fine, it's invisible; general utility → medium (15-25%); genuine
  structural load → 25%+ AND prioritize wall count and gyroid/cubic
  pattern over just cranking density further.

Sources: [FlashForge — Best Infill Pattern Guide](https://www.flashforge.com/blogs/news/best-infill-pattern-for-3d-printing), [Sovol — Infill Patterns Explained](https://www.sovol3d.com/blogs/news/infill-patterns-explained-strength-vs-material-efficiency)

---

## Part 2 — Bambu Studio Slicer Settings (this shop's actual slicer)

### 2.1 Where to start

**0.20mm Standard process profile is the sensible default for a first
print on almost any material** — this matches CLAUDE.md's own existing
convention (0.2mm standard production, 0.1mm for fine detail). From
there, tune per-part rather than reinventing settings from scratch each
time.

**Adaptive Layer Height** (Quality → Layer Height → Adaptive) is worth
turning on for organic/curved models specifically — it gives roughly
0.12mm-equivalent surface smoothness in about the print-time budget of a
flat 0.20mm print, by only using finer layers where the geometry's slope
actually needs it (steep curved sections) and coarser layers on flat
runs. Good default-on for anything like the pumpkin/ghost/vase organic
shapes; less relevant for boxy functional parts (organizer, phone stand)
where the whole part is already flat-walled.

### 2.2 The real calibration order (do NOT skip steps or reorder)

Doing these out of order produces misleading results — later
calibrations assume earlier ones are already correct:

1. **Vibration/noise calibration** (mechanical, printer-level, rarely
   needs redoing once set).
2. **Temperature tower** — for a new filament, test a range (e.g.
   190-220°C in 5°C steps for a generic PLA) and pick the temp that gives
   the cleanest layers/least stringing. Print temperature affects melt
   viscosity, which affects every calibration after this — always first
   for a genuinely new filament.
3. **Flow rate calibration** — must happen before pressure advance, or
   over/under-extrusion will mask and distort the PA calibration results.
   Bambu Studio has a built-in flow rate calibration test print per
   filament.
4. **Flow Dynamics / Pressure Advance (K value)** — Calibration →
   Pressure Advance in Bambu Studio; it auto-analyzes a printed test and
   suggests a K value (correcting for the lag between extrusion
   start/stop and actual nozzle pressure change — fixes blobs at corners,
   inconsistent wall thickness, "zit" seam artifacts).

**When to redo:** a genuinely new filament (even a new color/batch of an
otherwise-known material can shift flow rate slightly) or after a
firmware update that touches the extrusion system. Not something to redo
per print.

Sources: [Bambu Wiki — Strength Advance Settings](https://wiki.bambulab.com/en/software/bambu-studio/parameter/strength-advance-settings), [ADP Industries — Pressure Advance Guide](https://adpindustries.com/blog/bambu-lab-pressure-advance-guide/), [BabaBuilds — Flow Dynamics K-Value](https://bababuilds.com/blog/bambu-lab-flow-dynamics-calibration-k-value/)

### 2.3 Per-material settings (P1S-specific where it matters)

| Material | Nozzle | Bed | Fan | Notes for THIS printer (P1S) |
|---|---|---|---|---|
| **PLA/PLA+** | 190-220°C (210°C is a solid default) | 35-55°C | Default cooling is fine | Easiest, no enclosure needed |
| **PETG** | Standard PETG range | 70-85°C | Start 30-50%, up to 70% on overhangs/bridges | **Never run full 100% fan on PETG in an enclosed printer** — full fan can cause layer delamination. Slightly increased retraction vs. PLA (0.8-1.2mm with the stock Bambu extruder) helps stringing |
| **ABS** | 260-280°C | 85-100°C (community sources cite up to 100-110°C for hard cases) | Low | **Enclosure required — the P1S's passive chamber genuinely matters here** (see 2.4) |
| **ASA** | 245-260°C | 100-110°C | Low | Same enclosure requirement as ABS, slightly more UV/outdoor stable |
| **TPU** | ~230°C is a reliable start for 95A | ~45°C | Light only | Keep speed LOW (20-40mm/s) — TPU is flexible enough that fast direction changes cause blobbing/poor definition regardless of how good every other setting is |

Bed plate reminder (already in CLAUDE.md, repeated because it interacts
directly with these settings): **Textured PEI for PETG/ABS/ASA/PA**,
**Smooth PEI for PLA/Silk PLA**. Avoid the Cool Plate for ABS/ASA
specifically — doesn't hold enough heat, real warping risk. **Bambu
officially recommends glue stick for engineering materials** (ABS/ASA/PA)
— boosts adhesion AND acts as a release layer, don't skip it thinking
it's optional for these materials the way it might be for PLA.

Sources: [Bambu Wiki — ABS/ASA/PC Guide](https://wiki.bambulab.com/en/filament/abs_asa_pc), [Digitmakers — ASA/ABS on P1S Without Warping](https://www.digitmakers.ca/blogs/news/how-to-print-asa-and-abs-on-the-bambu-lab-p1s-or-x1c-without-warping), [Siraya Tech — Bambu Filament Guide](https://siraya.tech/blogs/news/bambu-lab-filament-guide)

### 2.4 P1S-specific quirk: passive chamber, no sensor, real warm-up protocol

**The P1S has NO chamber temperature sensor — only the X-series does.**
This means Bambu Studio can't show or target a real chamber temperature
number on this printer; "chamber temp" for the P1S is an emergent result
of bed heat + enclosure retention, not a directly controlled variable.
Community-measured real numbers: **the P1S's passive enclosure reaches
roughly 40-50°C chamber temp during ABS printing** — enough for most
parts, but large flat parts with sharp corners want closer to 60°C,
which the passive P1S chamber may not reach on its own in a cold room.

**Real, actionable warm-up protocol for ABS/ASA on the P1S** (this
directly extends CLAUDE.md's existing filament-drying guidance — drying
the filament isn't enough on its own for engineering materials):
1. Heat the bed to 100°C and let the enclosure sit closed for **15-20
   minutes before starting the actual print** — this preheats the
   passive chamber air, not just the bed.
2. Keep every enclosure access point closed for the whole print — this
   matches CLAUDE.md's existing "close all panel access points" note,
   now with the concrete reasoning: the P1S has no active/regulated
   heating, so panel leaks are a bigger deal here than on a printer with
   real chamber temp control (like the X-series or the newer P2S, which
   CLAUDE.md notes has an "actively regulated 50°C chamber" specifically
   because this exact P1S limitation is a known gap Bambu addressed in
   the successor).
3. **Known failure mode on tall ABS parts (200mm+)**: the chamber is
   still ramping up during the first 30-60 minutes, so a tall print's
   base layers (printed early, while the chamber is coolest) can show
   layer separation that the rest of the print (printed once the chamber
   has caught up) doesn't. If a tall ABS/ASA part ever shows this, the
   fix is the preheat protocol above, not a slicer setting — the chamber
   needs to already be warm before layer 1, not warming up during it.

Source: (synthesized from the P1S/ASA/ABS results above, cross-checked against CLAUDE.md's own printer section for the P1S-vs-P2S chamber distinction already documented there)

### 2.5 Strength settings — walls and shells (Bambu Studio's "Strength" tab)

- **Wall loops**: for a genuinely functional part, 4-5 loops (not the
  2-3 default) — thick walls carry load far better than dense infill
  does. This is the single highest-leverage strength lever in the whole
  slicer, ahead of infill %.
- **Top/bottom shell layers**: 5 layers at 0.2mm = a full 1mm of solid
  material top and bottom — a thin top shell (the default is often
  fewer) is a common, easy-to-miss weak point on anything that gets
  pressed on or stacked.
- **"Only one wall on top surfaces"**: a cosmetic option — when enabled,
  flat top surfaces get just one wall regardless of the Strength tab's
  wall-loop count, for a cleaner look on a model with a big flat top.
  Disable it if that flat top actually needs to be as strong as the
  rest of the walls (e.g. a lid that gets stepped on), keep it enabled
  for purely decorative flat tops where a clean wall-line-free look
  matters more.

Source: [Bambu Wiki — Quality Advanced Settings](https://wiki.bambulab.com/en/software/bambu-studio/parameter/quality-advance-settings), [printpal — 10 Tips for Stronger Prints](https://blog.printpal.io/10-bambu-studio-tips-for-stronger-3d-prints/)

### 2.6 Ironing and seams (extends CLAUDE.md's existing "Ironing on flat tops" rule)

- **Ironing only works on FLAT top surfaces.** On a curved top (like the
  pumpkin/vase/ghost work), ironing can't smooth layer lines the same
  way and just adds print time for little/no visible benefit — reserve
  it for genuinely flat tops (a sign's face, a box lid, a nameplate).
- **Ironing Flow is the single most impactful setting for ironing
  quality** — this is the % of normal extrusion laid down during the
  ironing pass. Too low and it doesn't fill the gaps between layer
  lines (visibly does nothing); too high and it over-extrudes a bump.
  **15-20% is where most PLA filaments land as the smoothest result** —
  a real starting point, worth a quick test print rather than guessing
  higher.
- **Ironing speed**: 30-80mm/s practical range for PLA; **40mm/s is a
  reliable middle-ground starting point.**
- **Seam placement**: "Random" scatters the seam to a different spot
  each layer — less visually obvious as one continuous line, but can
  introduce small "zit" blobs at each seam transition point. "Aligned"
  keeps the seam in one consistent spot — more visible as a line but
  more predictable, easier to hide deliberately (e.g. always facing the
  back of a display piece) than random placement's scattered zits.
  For this shop's kawaii display pieces, aligned + a deliberately
  hidden-side placement is usually the better call than random.

Source: [3DBite — Ironing Settings Guide](https://3dbite.com/bambu-studio-ironing-settings-guide/), [Bambu Wiki — Seam Settings](https://wiki.bambulab.com/en/software/bambu-studio/Seam)

---

## Quick-reference decision table

| Question | Answer |
|---|---|
| New filament, first print? | Temp tower → flow rate → pressure advance, in that order. Don't skip to PA. |
| Part will be handled/stressed? | 4-5 wall loops, gyroid/cubic infill 25%+, orient so load runs parallel to layers not across them. |
| Part is purely decorative? | 2-3 walls, 10-15% infill is fine, prioritize surface quality settings (ironing if flat-topped, 0.1mm layers or Adaptive if organic/curved). |
| Steep overhang, no support wanted? | Try 0.1mm layers first (buys up to ~55-60° clean) before reaching for supports. |
| Organic/figurine shape needs support? | Tree supports. |
| Mechanical part with a big flat overhang? | Normal/grid supports + interface layer. |
| Printing ABS/ASA on the P1S? | Preheat bed 100°C + closed enclosure 15-20min BEFORE starting, glue stick on textured PEI, expect ~40-50°C passive chamber (not directly controllable — no sensor on P-series). |
| Snap-fit or moving part? | ~0.5mm clearance, don't assume machining-tight tolerances will work. |
| Hole printing undersized / contour oversized? | Bambu Studio's XY Hole/Contour Compensation — measure, calculate, dial in, don't guess. |
| Flat-top part needs a mirror finish? | Ironing, Topmost surface only, 15-20% flow, ~40mm/s. |
| Curved-top part (vase/organic)? | Skip ironing — it won't help and costs print time. |
