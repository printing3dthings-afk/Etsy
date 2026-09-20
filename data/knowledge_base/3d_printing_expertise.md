# 3D Printing Expertise — Design + Slicer Settings — 2026-08-21

Built at Scott's explicit request ("make Frank and yourself experts... from
the actual 3D design to the slicer settings") via targeted multi-source
WebSearch across both halves of the discipline. This doc is the **slicer
settings + general design-for-manufacturing (DfAM) reference** — practical
knowledge for advising Scott on any print, judging whether a model will
actually print well, and tuning Bambu Studio for a specific part/material.

**Parts 3 and 4 were added 2026-09-20**, again at Scott's request ("learn more
about the physics... and how new ways of doing things are possible"). Part 3
is the mechanism underneath Parts 1-2 — reptation and the fourth-root healing
law, residual-stress warping, melt compliance, bridge tension — so a failure
can be predicted instead of discovered one printed part at a time. Part 4 is
the opposite question: what additive can do that no mould or mill can, which
is the set of forms a buyer cannot get anywhere else.

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

## Part 3 — The physics underneath (added 2026-09-20)

Parts 1-2 above, and all 66 techniques in `3d-print-design/SKILL.md`, are
**phenomenology**: "this failed, here is the number." That is worth more than
theory whenever the two disagree, and nothing in this Part overrides a real
measurement taken in this shop.

What it adds is the ability to **predict a failure before printing it**, and
to tell which knob addresses a cause rather than a symptom. Every section
below ends with what it predicts that the corresponding empirical rule does
not.

### 3.1 Why Z is weak: an interface that never finished healing

Extrusion does not glue layers together, it **welds** them. When hot polymer
meets the layer below, chains diffuse across the interface — reptation, the
snake-like motion of a chain through the entanglements of its neighbours.
That only happens while the interface is above the temperature where chains
are mobile (Tg for an amorphous polymer like PLA/PETG/ABS, the melt point for
a semi-crystalline one). The moment it drops below, diffusion stops and
whatever weld exists at that instant is the weld forever.

The degree of healing follows a **fourth-root law**:

```
DOH = σ / σ∞ = [ ∫ dt / t_w(T) ]^(1/4)
```

and the welding time `t_w` is Arrhenius-like — exponential in temperature.
(The PEEK study's experimentally fitted form: `t_w = (144.1·exp(3810/T))^4`.)

Those two facts together are the whole story of Z strength:

- **Time buys almost nothing.** Doubling the time spent above the mobility
  threshold multiplies bond strength by 2^0.25 = **1.19** — 19%.
- **Temperature buys a lot**, because it moves an exponential. In the PEEK
  work, dropping nozzle temperature 20°C cut the number of fully-healed
  layers by 47%.

Measured outcomes, consistent across the literature: XY tensile strength is
typically **4–5× the Z value**. One solid-PLA study measured a 33% drop from
UTS_X to UTS_Z, rising to 52% once the infill was sparse. FDM reaches roughly
70–90% of injection-moulded strength in XY, but only 40–75% in Z. Holding the
previous layer just below PLA's crystallization temperature raised tensile
strength ~23%.

**What this predicts that "Z is 4–5× weaker" does not:**

1. **The Z penalty is a thermal history, not a material constant** — so it is
   partly under the designer's control, and it changes with what else is on
   the plate. A short layer time keeps the interface hot and the weld strong.
   Printing six copies of a small part at once lengthens each layer's cycle
   to six times as long, so every copy cools further before the next layer
   lands. **Batching copies on one plate makes each one weaker in Z than the
   same part printed alone.** Relevant directly: this shop prints multiples
   to sell. For a decorative piece it does not matter; for a keychain, a
   clip, or anything with a load path, it does.
2. **Part cooling fan is a direct trade against Z strength.** The fan exists
   to freeze overhangs and bridges fast (3.4) — which is the same as saying
   it exists to end healing early. A part that needs both a crisp overhang
   and a strong weld at the same height is a *design* problem, not a settings
   problem.
3. **Infill percentage cannot fix a load path that crosses layers.** Infill
   adds material in XY. Only re-orientation, a hotter nozzle, slower cooling,
   or a geometric fix (interlocking features, a dovetail, Z-pinning) touches
   the weld itself. This is the mechanism behind §1.4's orientation rule.

Source: [Heat Transfer-Based Non-isothermal Healing Model for Interfacial
Bonding Strength in FFF (PMC)](https://pmc.ncbi.nlm.nih.gov/articles/PMC8827803/),
[Influence of Temperature on Interlayer Adhesion in Material Extrusion — review
(MDPI JMMP 9(6) 196)](https://www.mdpi.com/2504-4494/9/6/196),
[Advances in interlayer bonding in FDM — review (Virtual and Physical
Prototyping)](https://www.tandfonline.com/doi/full/10.1080/17452759.2025.2522951),
[Part orientation and strength (Protolabs
Network)](https://www.hubs.com/knowledge-base/how-does-part-orientation-affect-3d-print/)

### 3.2 Warping is a bending moment assembled one layer at a time

Each road is laid hot and immediately constrained by the solid material under
it. The contraction it *wants* to do as it cools cannot happen freely, so it
becomes locked-in tensile stress instead. Stack that layer on layer and the
upper region ends up in tension relative to the lower one — a bending moment
across the whole part, pulling the ends up. It lifts the moment that moment
exceeds bed adhesion. Corners go first: they lose heat from two directions
and have the least surrounding material restraining them.

The material term is the temperature drop from Tg down to room temperature,
because that is the range over which strain gets locked in:

| Material | Tg | Drop from Tg to 22°C | Warping behaviour |
|---|---|---|---|
| PLA | 55–60°C | ~35°C | Barely warps |
| PETG | 80–85°C | ~60°C | Mild |
| ABS / ASA | 100–110°C | ~85°C | Warps badly without an enclosure |

**What this predicts:**

- **Warping scales with footprint length and layer count, not with mass.** A
  long flat part warps; a tall narrow part of identical volume does not,
  because the moment arm is short and each layer's contraction is restrained
  by a small cross-section. For this shop that ranks the geometries directly:
  a flat sign or nameplate is the worst case, a vase or lantern is the best.
- **The P1S's passive ~40°C chamber halves the problem, it does not remove
  it.** For ABS it takes the locked-in range from ~85°C down to ~65°C. That is
  why CLAUDE.md's ABS protocol (preheat the bed to 100°C with the enclosure
  shut for 15–20 min before starting) matters: it is buying chamber
  temperature the machine has no sensor to regulate.
- **Mouse ears and a small outward flare at the base work because they add
  adhesion exactly where the moment is largest**, not because they add
  adhesion generally. Putting them anywhere but the corners is wasted.

### 3.3 The numbers, and which of them are contested

| Quantity | Value | Confidence |
|---|---|---|
| Tg — PLA / PETG / ABS | 55–60 / 80–85 / 100–110 °C | Solid, agrees across sources |
| Z vs XY tensile | Z is 20–60% of XY (commonly quoted 4–5× weaker) | Solid, wide range because it is process-dependent |
| Shrinkage — PLA | 0.2–0.5% (amorphous) | Reasonable |
| Shrinkage — PETG | ~0.2–0.6% | Reasonable |
| Shrinkage — semi-crystalline (nylon, PP) | 1–3% | Reasonable |
| Shrinkage — ABS | **"up to 11%" — do not quote this** | **Contested.** One widely-copied blog gives 11%; typical *linear* mould shrink for ABS is 0.4–0.8%. 11% is almost certainly volumetric, or an unconstrained-mould figure, not the linear shrink of a printed part. The same page's own "amorphous 0.2–0.5%, semi-crystalline 1–3%" framing contradicts it. |
| Bridge span, no visible sag | ~20 mm | Practical consensus |
| Bridge span, sag that closes after 2 solid layers | 20–50 mm | Practical consensus |
| PLA fatigue limit | ≈10% of yield strength | Indicative only — one reported figure, not a datasheet value |

**Most filament datasheets publish no shrinkage figure at all.** If a real
dimension depends on it, print a 100 mm test bar in that exact filament and
measure it — the same discipline already applied to hole/contour compensation
in §1.2. Never hand Scott a number sourced from a blog for something a
caliper can settle in ten minutes.

Source: [Glass transition temperatures of PLA, PETG & ABS
(All3DP)](https://all3dp.com/2/pla-petg-glass-transition-temperature-3d-printing/),
[PLA, ABS and PETG shrinkage
(3DSourced)](https://www.3dsourced.com/guides/3d-print-shrinkage-pla-abs-petg/),
[Shrinkage Compensation for FFF Printing (conference
paper, PDF)](https://ieworldconference.org/content/WP2021/Papers/GDRKMCC_21_35.pdf)

### 3.4 The melt is a compressible spring — which is all pressure advance corrects

The extruder pushes filament in; the molten polymer in the hotend is
compliant, so the flow coming *out* of the nozzle lags the command going in.
The standard model is Hooke's law — the extra filament that must be advanced
is proportional to the pressure, which is proportional to flow rate. Pressure
advance (Klipper) / linear advance (Marlin) pre-compensates: push a little
extra before acceleration, pull a little back before deceleration.

Typical PA values run **0.050–1.000**, the high end essentially only on bowden
extruders. Under-tuned shows as blobs at corners; over-tuned shows as rounded
corners and visible under-extrusion. Klipper's own guidance is to tune at high
flow — high speed (~100 mm/s) and a coarse layer height (~75% of nozzle
diameter) — because that is where the pressure swing is largest.

The second-order effect worth knowing: polymer melts are **shear-thinning**.
Apparent viscosity falls as shear rate rises, so pressure and flow are not
linearly related across the whole speed range. A single PA constant is a
linearisation.

**What this predicts:**

- **PA is a property of extruder + nozzle + filament, never of the printer
  alone.** A different brand of the same material can need a different value.
  This is the actual reason CLAUDE.md's production table says "Flow Dynamics
  calibration — run per filament."
- **PA only ever fixes defects at speed changes.** A part printed at constant
  speed shows none of it. A part made of many small corners — engraved text,
  fine surface relief, ribs, a lattice — shows all of it. That is precisely the
  geometry this shop keeps building (Technique 52's detail metric, Technique
  59's relief, Technique 62's engraved faces), so PA matters here more than the
  part count would suggest.
- **"Outer wall 50 mm/s or lower," CLAUDE.md's single most important
  production rule, works partly through this mechanism** — a slower outer wall
  means a smaller pressure swing at every corner, not just less vibration.
- A single PA value tuned at high flow is deliberately *not* optimal at low
  flow, because shear-thinning moved the curve. Expect the compromise; don't
  chase it with a second calibration.

Source: [Klipper — Pressure Advance](https://www.klipper3d.org/Pressure_Advance.html),
[Marlin — Linear Advance](https://marlinfw.org/docs/features/lin_advance.html),
[Investigating pressure advance algorithms for filament-based melt extrusion
(Rapid Prototyping Journal)](https://www.emerald.com/rpj/article/25/5/830/363878/Investigating-pressure-advance-algorithms-for)

### 3.5 Bridging is tension plus a race against gravity

A bridge is not held up by surface tension or by the melt's own stiffness. The
strand is anchored at both ends, **drawn taut by the head's own motion**, and
has to solidify before gravity wins. That is the entire mechanism, and every
consequence follows from it.

Practical spans on a well-tuned machine: **~20 mm with no visible sag; 20–50 mm
with slight sag that disappears under two solid layers; 50–80 mm achievable;
>100 mm only on setups tuned specifically for it.** The four settings that
actually decide the outcome are bridge speed, bridge flow ratio, part cooling
fan, and layer height.

**What this predicts:**

- **The anchors matter more than the span.** A bridge landing on a rounded or
  sloped surface has nothing solid to pull against and will sag at a span that
  is trivial between two square walls. Technique 60 records that you cannot
  reason about a bridge span from your own geometry — this is *why*: the
  geometry that decides it is the anchor, and the model does not make the
  anchor obvious.
- **Fan speed is the dominant bridge lever and the direct enemy of Z strength
  (3.1).** They are opposed by construction. Recognise a part that wants both
  as a design problem.
- **It explains why `mesh_gate.py` reports overhang and never fails on it.**
  The recurring false positive is the 0.7 mm-deep ceiling of the engraved
  maker's mark on a part's underside — a sub-millimetre bridge between two
  fully anchored walls, an order of magnitude inside even the no-sag span.
  Angle alone cannot distinguish that from a real unsupported overhang, which
  is exactly the judgement the tool refuses to make for you.

Source: [Investigation on Bridging Defects in 3D-Printed PLA Beams Using FFF
(PMC)](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12845589/),
[FDM design rules — bridging (Layer X)](https://layerx3d.in/blog/fdm-design-rules-wall-thickness-overhangs-bridging-tolerances)

---

## Part 4 — What additive does that nothing else can (added 2026-09-20)

Part 3 is about avoiding failure. This Part is about the opposite question:
what is *only* possible because the process builds up in layers instead of
cutting away or filling a mould.

This matters for a specific, honest reason. Everything this shop's gate checks
— `mesh_gate.py`, `product_gate.py` — asks "will it print." Nothing asks "is
this a shape that could only exist because it was printed." A vase with a
pattern on it is a shape that a mould could have made. The list below is the
set of things a mould, a lathe and a mill genuinely cannot do, which is the
same as saying it is the set of things a buyer cannot get anywhere else.

### 4.1 Part consolidation and print-in-place assemblies

No draft angle, no mould release, no assembly step, no fasteners. The
clearance *is* the assembly: two bodies modelled with a gap between them come
off the plate already articulated. Already in use here (the cable clip's
print-in-place hinge, the flexi work) and the reason `mesh_gate.py` takes a
`-c N` expected-body-count flag at all.

The failure mode this shop has already hit twice is the same one every time:
the modelled gap is not the printed gap. Technique 57 measured beads eating
over half of it; the seahorse's spherical cup left a crescent void thinner
than one extrusion and fused solid. **A print-in-place gap is verified by
slicing it and counting islands per layer, not by counting mesh components.**

### 4.2 Compliant mechanisms — motion from deflection, not from joints

A flexure produces motion by bending elastically. No pins, no bearings, no
backlash, no friction, no wear surface, no assembly. It is the single largest
untapped category on this list for a shop that sells small desk objects.

Real design numbers:

- **Film/living hinge thickness: 0.18–0.38 mm** for a thin hinge meant to bend
  repeatedly; **0.5–1.2 mm** for a typical printed industrial hinge where
  stiffness matters more than cycle count.
- **Hinge length ≥ 2–3× its thickness**, so strain spreads instead of
  concentrating at one line.
- **Layers must run parallel to the hinge axis**, so continuous extruded
  strands carry the bending load. A hinge whose layers run across the axis is
  asking the weld from 3.1 to do the work, and it will crack on the first or
  second cycle. This is the clearest case anywhere of orientation being a
  functional requirement rather than a quality preference.
- **PLA's fatigue limit is around 10% of its yield strength.** A PLA flexure
  meant to cycle thousands of times has to stay inside that band, which in
  practice means a long, thin, low-strain hinge. For real repeated use, PETG,
  TPU or nylon.
- **Bistable** compliant mechanisms give a genuine snap/click from geometry
  alone — no spring, no detent part. Technique 47 already catalogued clicker
  mechanism families; this is the physics that makes the monolithic version
  possible.

Source: [Living hinge design for 3D printing —
checklist](https://vprint3d.com.hk/resources/living-hinge-design-for-3d-printing-the-2026-engineers-checklist/),
[A one-piece 3D printed flexure translation stage (arXiv
1509.05394)](https://arxiv.org/pdf/1509.05394),
[Design of 3D-printed compliant mechanisms (ESMATS)](https://esmats.eu/amspapers/pastpapers/pdfs/2014/merriam.pdf)

### 4.3 Geometry with no mould release path

Internal voids, undercuts, captive parts, a chain whose links were never
open, a ball inside a cage. This is the most legible "could not be made any
other way" category to a buyer, and the only one on this list that reads at
thumbnail size — which is exactly the bar Scott set for retail products
(CLAUDE.md, 2026-09-13: the silhouette has to read at 200 px).

The constraint is that a fully enclosed void must either be drainable or be
deliberately sealed — Technique 63's sealed-void class is this capability's
own failure mode, not an unrelated bug.

### 4.4 Lattices and metamaterials

A **TPMS** (triply periodic minimal surface — gyroid, schwarz-D) is a
double-curved surface that is self-supporting everywhere by construction: it
has no unsupported overhang to fail on, which is the real reason gyroid works
as an infill and why a gyroid *wall* is printable at all.

An **auxetic** lattice — re-entrant honeycomb being the standard form — has a
negative Poisson's ratio: compress it and it gets *narrower* instead of
bulging. That is why it absorbs more energy than a conventional hexagonal
honeycomb of the same mass, and why it has variable stiffness and better
fracture toughness.

For this shop the interesting property is not energy absorption — nothing here
gets crashed into. It is **feel and light**: a gyroid or auxetic wall is a
periodic double-curved screen that throws a moiré shadow and compresses with
an unexpected, springy hand-feel. Both are things a photograph can sell and a
moulded object cannot do. A gyroid-walled lantern or a squeezable auxetic
coaster are products, not experiments.

Source: [Energy absorption of FDM-printed auxetic re-entrant structures —
review (J. Mater. Eng.
Perform.)](https://link.springer.com/article/10.1007/s11665-023-08243-3),
[On the internal architecture of lightweight auxetic metastructures — review
(arXiv 2505.07385)](https://arxiv.org/pdf/2505.07385)

### 4.5 Deliberate anisotropy

Part 3.1 treats the weak Z weld as a defect to mitigate. Inverted, it is a
design input: orient the part so it is stiff along the load path and
*compliant* in exactly the axis that should flex. A hinge that works because
it is weak in the right direction is a better hinge than one that fights the
process. Nothing subtractive has this property at all — a milled part is the
same material in every direction.

### 4.6 Vase mode (spiralize)

A single continuous extrusion spiralling upward: no layer changes, therefore
**no Z-seam anywhere on the part**. It is simultaneously the weakest thing the
machine can produce (one extrusion thick, no infill, no top) and one of the
best-looking, because the seam artifact that every other mode fights simply
does not exist. The constraint is absolute: exactly one closed contour per
layer, constant wall thickness, no top surface. A form that satisfies it gets
a surface quality no other process reaches; a form that does not cannot be
coaxed into it.

### 4.7 Multi-material (AMS) — variable stiffness inside one part

A rigid frame with a soft grip, printed as one object. The hard constraint is
that **dissimilar polymers do not bond well**: PLA↔TPU interfaces are weak
because the two materials differ in thermal and mechanical behaviour. Bambu
Studio's **"Use Beam Interlocking"** preset addresses this by generating
mechanical interlock at the interface instead of relying on adhesion — which
is the correct fix, since it stops asking chemistry to do the work.

Bambu's own TDS shows **TPU-for-AMS with roughly half the Z adhesion of
everything else** in their lineup. Design consequence, stated plainly: never
put a PLA/TPU interface in tension across the joint. Make it a mechanical
capture — a dovetail, a through-hole the soft material fills, an interlocking
beam — and let the geometry carry the load.

Source: [Bambu Lab Wiki — soft and hard filament multi-material printing
guide](https://wiki.bambulab.com/en/h2/manual/soft-and-hard-filament-multi-material-printing-guide)

### 4.8 Mass customisation at zero tooling cost

The one item on this list that is already fully available here and costs
nothing to exploit. A mould amortises over thousands of identical units; a
`.scad` script amortises over *variants*. One script with real named variables
is N SKUs — sizes, name-engraved personalisations, colourways, themed
variants — with no retooling and no minimum order.

This is exactly why CLAUDE.md's OpenSCAD design rule insists on named
variables and forbids magic numbers: `-D size=40` is the product line. A model
that bakes its dimensions into the geometry has thrown away the cheapest
advantage additive has.

### What this means for the next product

Every capability above is a decision made **before** either gate runs.
`product_gate.py` can tell you a form is printable; nothing in this codebase
can tell you a form was worth printing. That judgement belongs in step 1 of
Scott's standing process — the 4–5 genuinely different formal approaches
presented before any code — and this Part is the vocabulary for making those
five actually different from each other instead of five variations on a
primitive with a pattern applied.

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
| Printing several copies of a load-bearing part at once? | Expect each one weaker in Z than a single print — longer layer time means a colder, less-healed weld (§3.1). Print structural parts alone or accept the penalty knowingly. |
| Need both a crisp overhang and a strong weld at the same height? | That is a design problem, not a settings problem — part cooling fan is the main lever for both and they pull opposite ways (§3.1, §3.5). Change the geometry. |
| Part must flex repeatedly (hinge, clip, catch)? | Layers parallel to the bend axis, hinge length ≥2-3× thickness, and PLA only if strain stays near 10% of yield — otherwise PETG/TPU/nylon (§4.2). |
| Asked for a shrinkage number for a real dimension? | Print a 100mm bar in that exact filament and measure it. Do not quote a blog figure — the widely-copied "ABS shrinks 11%" is almost certainly volumetric, not linear (§3.3). |
| Long flat part warping, short tall part fine? | Expected — warping scales with footprint length and layer count, not mass (§3.2). Mouse ears/base flare belong at the corners, nowhere else. |
| Choosing a form for a new product? | Ask whether a mould could have made it. Print-in-place articulation, captive geometry, compliant flexures, TPMS/auxetic walls and vase mode are the things only this process can do (Part 4). |
