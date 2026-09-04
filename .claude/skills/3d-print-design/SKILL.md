---
name: 3d-print-design
description: "Real technique for designing genuinely printable 3D models in OpenSCAD -- both functional/practical parts (organizers, brackets, holders) and decorative/organic parts (vases, bowls, shades) -- grounded in this shop's real Bambu Lab P1S constraints and in specific OpenSCAD/CGAL pitfalls found and fixed while building the first real models. Load this whenever writing a .scad script for render_openscad_model / tools/openscad_render.py. For general DfAM judgment and Bambu Studio slicer settings (calibration, per-material presets, strength/wall settings, tolerances, orientation), see data/knowledge_base/3d_printing_expertise.md alongside this skill."
---

# 3D Print Design — OpenSCAD, For Real Printable Models

**Before starting a genuinely new class of model** (first real mechanical
part, first print-in-place joint, first time a design might need Blender),
also read `.claude/skills/3d-print-design/ENGINEERING_REFERENCE.md` — a
separate, sourced theory/technique doc (BOSL2's gear/hinge/thread/snap-fit
modules, real FDM tolerance numbers, organic-surface tools beyond what's
used below, the OpenSCAD-vs-Blender tool-choice verdict). This file stays
what it's always been: a log of real bugs found while building this shop's
actual models, not a textbook.

## Why this exists (2026-08-21)

Before this skill, `render_openscad_model` could render *any* valid OpenSCAD
script, but nothing in this codebase captured what makes a script produce a
model that's actually good — printable without supports where avoidable,
structurally sound, and visually correct rather than subtly broken in a way
that only shows up when you actually look at the render. Four real,
non-obvious bugs were found and fixed building the first real test models
(a hollow vase, a desk organizer, and a follow-up pass adding decorative/
functional detail to both) before this was written down:

1. A raw `polygon()` through straight-line control points, revolved with
   `rotate_extrude()`, produces visible faceted "ring" bands on the surface
   — not a smooth curve, even at high `$fn`. Fixed with BOSL2's
   `smooth_path()`.
2. Hollowing a revolved vessel by running 2D `offset(delta=-wall)` on the
   *whole* closed profile — including the points that sit on the rotation
   axis (r=0), which represent the vessel closing to a point at top/bottom
   — produces a self-intersecting/degenerate polygon wherever the local
   radius is thinner than the wall. CGAL does not raise a clean error for
   this; it silently resolves the self-intersection into a spike/artifact
   *inside* the model. The render "succeeds" and looks fine from most
   camera angles.
3. A vessel profile whose last point sits at `[0, height]` (back on the
   axis) revolves into a **closed, capped** vessel, not an open-mouthed
   one — regardless of how correctly the cavity is hollowed. This one is
   easy to miss because the *hollowing* can be perfectly correct and the
   model will still be structurally wrong.
4. (Found 2026-08-21, adding decorative/functional detail to the first two
   models) BOSL2's `cuboid(..., rounding=r)` silently produces **empty
   geometry** — not an error, not a warning printed to the render result,
   just nothing — when `r` is too large relative to the shape's own
   thinnest dimension (confirmed: a 1.6mm-thick rib box with a requested
   1.3mm rounding radius vanished entirely; `openscad --render` on its own
   showed the real cause via TRACE lines through an internal `if` check in
   `BOSL2/shapes3d.scad`, but a plain PNG render gave no clue beyond "the
   whole model came out blank"). Small decorative/functional details (ribs,
   grooves, thin fins) usually don't need rounding at all — skip it rather
   than fight the minimum-size constraint.

None of the first three produced an OpenSCAD error, and #4 only became
legible by re-running the exact failing piece directly through `openscad
--render` on the command line (not through the PNG pipeline) and reading
its TRACE output. All four were only caught by actually rendering and
looking at the result — which didn't even work in this container until the
headless-rendering fix below shipped. The discipline this skill exists to
enforce: **never call a 3D model done from reading the .scad source.
Render a PNG and look at it, the same "verify before reporting success"
rule this shop already applies to AI photos and Etsy mutations.**

## Setup — what's already wired up, use it

- **BOSL2** (Belfry OpenSCAD Library v2, BSD-2-Clause) is vendored at
  `assets/openscad_libs/BOSL2/` and is *always* on the include path for
  every render `tools/openscad_render.py` runs (`OPENSCADPATH` is set
  automatically). Just write `include <BOSL2/std.scad>` at the top of any
  script — real rounding/filleting, `smooth_path()`, `attachable()`
  positioning, thread/gear generators, `cuboid()`/`cyl()` with named
  rounding, all available with no path wrangling.
- **PNG preview rendering actually works headless now.**
  `render_scad(src, out.png, fmt="png")` runs it through `xvfb-run` +
  Mesa's software rasterizer automatically. Default framing is
  `--autocenter --viewall`, which reliably shows the whole model without
  you having to guess a camera position (an earlier hand-picked
  `--camera=...` argument cropped the first test renders). Use this on
  every real model before calling it done.
- **A top-down or orthogonal second view is a cheap sanity check.** If an
  angled preview shows odd diagonal shading bands on a shape that's
  radially symmetric (any `rotate_extrude()` result), that's very likely
  a Gouraud/Phong lighting artifact from the preview renderer's facet
  triangulation under a single directional light at an oblique angle —
  not real geometry. Confirmed this directly: a vase that looked like it
  had diagonal creases from an angled view showed perfect concentric
  circles from directly above (`--camera=0,0,60,0,0,0,400`). Don't chase
  a "bug" that's actually just the preview's lighting — but do check,
  don't assume.
- **A headless Blender studio render is available for design review**
  (`tools/blender_render.py`, added 2026-09-01 — system binary, `apt-get
  install -y blender`, ~25MB). OpenSCAD's own PNG preview (above) is flat,
  unlit and single-material — it has repeatedly hidden real defects in
  this project (Technique 33's seam, the overhang droop in Technique 35)
  because nothing about it resembles how the printed part will actually
  look. `render_review(mesh_path, out.png)` imports the STL, centers it on
  a floor plane, lights it with real three-point area lighting, gives it a
  matte-plastic material in a color you choose, and renders through Cycles
  (~50-90s at the defaults — denoising is forced OFF because this
  container's Blender build has no OpenImageDenoiser and errors if you try
  to enable it). Use this as the last check before calling a model done,
  the same way an AI-generated listing photo gets looked at before
  shipping. It is a REVIEW tool only — OpenSCAD stays the only place
  geometry gets authored, and this never substitutes for the AI-photo
  pipeline CLAUDE.md requires for actual Etsy listings. It also has no
  3MF importer in this container (confirmed live) — feed it STL/OBJ/PLY.
- **Real vendored fonts are available to `text()` for engraved branding.**
  This repo's existing font sets (`fonts/`, `assets/fonts/` — already used
  for cover art/listing images) are auto-registered with fontconfig the
  first time `render_scad()` runs in a process (`_ensure_fonts_registered()`
  copies them to `~/.fonts` + `fc-cache`, idempotent, never blocks a render
  if it fails). Reference a font by family name, e.g.
  `text("...", font="Dancing Script:style=Bold")` — cursive/script options
  include Dancing Script and Great Vibes, elegant serif options include
  Cinzel/Cinzel Decorated/Playfair Display. **An unregistered or misspelled
  font family silently renders empty text geometry — no error** (confirmed
  live before this was wired up automatically), so if engraved text isn't
  showing up, check `fc-list | grep -i '<family>'` before assuming the
  boolean/positioning is wrong.

## Bambu P1S constraints — design within these, don't guess

**Load `data/knowledge_base/3d_printing_expertise.md` alongside this
skill for anything beyond writing the .scad itself** — general DfAM
judgment (tolerances, hole/contour compensation, anisotropy/orientation
strategy, snap-fit/living-hinge/thread design, infill pattern selection)
and the actual Bambu Studio slicer-settings knowledge (calibration order,
per-material presets, strength/wall settings, ironing/seam tuning, the
P1S's specific no-chamber-sensor quirk). This skill stays focused on the
OpenSCAD-code-level bugs and techniques found building real models here;
that doc is the broader reference for judging a design's printability and
advising Scott on how to actually print it well.

Real printer specs (full detail in the root `CLAUDE.md`'s "3D Printer —
Bambu Lab P1S" section):

| Constraint | Value | Design implication |
|---|---|---|
| Build volume | 256×256×256mm | Hard ceiling on any single-piece dimension |
| Max overhang without supports (STRUCTURAL limit) | 55° from vertical | Steeper collapses/needs supports. **This is not the surface-quality limit — see Technique 35.** For any free surface a customer will see, design to ≤40° instead; reserve up to 55° for hidden/internal geometry only. |
| Layer heights | 0.05 / 0.1 / 0.2mm | 0.2mm is standard production; 0.1mm for visible fine detail (organic surfaces, small text) |
| Nozzle | 0.4mm stock brass (PLA/PETG/TPU); hardened steel only for CF/GF filaments | Minimum realistic single-wall thickness ≈ nozzle width; **use 2× nozzle width (≈0.8mm) as the practical minimum wall for anything structural**, more for anything handled/stressed |
| Bed plates | Textured PEI (PETG/ABS/ASA/PA), Smooth PEI (PLA/Silk PLA) | Doesn't change the model, but matters when telling Scott what to print it on |

**Wall/floor thickness used in this skill's worked examples:** 2.4mm side
walls (3× nozzle width, safely structural for a functional part or a
vessel that gets picked up/filled with water), 3mm floor. Thinner is
possible for purely decorative, unhandled pieces — never go below ~1.2mm
(3 perimeters at 0.4mm) for anything that will be lifted, gripped, or
hold liquid/weight.

**Overhangs in practice:**
- A rounded/filleted **vertical edge** (fillet axis parallel to Z) has
  **zero** overhang — the fillet lies entirely in the XY plane, so every
  printed layer is just a rounded-rectangle slice. This is the safe,
  always-fine way to round a functional part's corners.
- A rounded/filleted **top edge** (fillet curving over from a vertical
  wall to a horizontal top face) *does* have overhang, up to 90° at the
  very top of the curve. Small radii (a few mm) are fine in practice —
  the P1S handles them natively per its "up to 55° without supports"
  spec covering typical fillets — but don't round a *bottom* edge that
  sits on the print bed; keep the base flat for reliable first-layer
  adhesion. See the desk-organizer example below (`edges="Z"` — rounds
  only the four vertical corner edges, never the top/bottom faces).
- A revolved organic profile (vase/bowl/shade) is naturally overhang-safe
  as long as the profile's tangent never exceeds the 55° limit at any
  height — a profile that bulges outward faster than it rises can still
  violate this even though it "looks smooth." For a wide bulge, check the
  local slope, not just that the curve looks pleasant.

**Tolerances and orientation for functional parts (full detail in
`3d_printing_expertise.md`, summarized here for quick reference while
writing code):**
- A hole in a design prints slightly SMALLER than modeled, and an outer
  contour prints slightly LARGER — if a part needs a snug fit (a peg
  into a hole, a lid onto a rim), model in ~0.2-0.3mm of clearance rather
  than an exact nominal fit; Bambu Studio's own XY Hole/Contour
  Compensation can correct further after a real test print, but starting
  with zero clearance in the model guarantees a first-print failure.
- FDM parts are 4-5× weaker across layers (Z) than within a layer (XY) —
  when a design has an actual load path (a stand's neck, a bracket's
  arm), model/orient it so that stress runs parallel to the layers, not
  perpendicular. This matters more than infill % for anything genuinely
  load-bearing.
- Snap-fit clearance for FDM: ~0.5mm between hook and catch — tighter
  reads as "should work" in CAD and fails on a real print due to normal
  FDM variance.

## Technique 1 — Organic/decorative: hollow bodies of revolution

**Use `rotate_extrude()` for anything rotationally symmetric** (vases,
bowls, lamp shades, planters) — this is the primitive that actually
produces smooth organic curves in OpenSCAD; don't try to sculpt freeform
organic shapes by hand, OpenSCAD's CSG model genuinely can't do that well.

**The correct way to build a hollow vessel: one closed cross-section
profile, revolved once — never two separate revolved solids differenced
together.** The naive approach (`difference() { rotate_extrude() polygon(outer); rotate_extrude() offset(delta=-wall) polygon(outer); }`)
is the version that produces the self-intersection spike described above,
because `offset()` on a profile touching the rotation axis is invalid
there. Build the actual solid cross-section instead — trace up the
outside, across the rim thickness, down the inside, across the floor,
close:

```openscad
include <BOSL2/std.scad>

// Outer profile: base-edge to rim-edge, OFF-axis at both ends. A point
// at x=0 here would weld the vessel shut at that end (see bug #3 above)
// -- the base is allowed to be a real disk (start point can be [0,0] if
// you want a solid puck base), but the RIM must end at a real radius if
// the vessel should be open.
outer_ctrl = [
    [38, 0], [42, 15], [40, 35], [30, 55],
    [26, 75], [30, 95], [22, 110], [22, 120],
];
outer = smooth_path(outer_ctrl, method="corners", size=6, splinesteps=12);

wall = 2.4;
floor_h = 3;
rim = outer[len(outer) - 1];

// Cavity wall = outer profile shrunk radially by `wall`, floored at 0,
// restricted to points above the floor -- never a 2D offset() of the
// whole closed shape.
inner_from_top = [for (p = outer) if (p.y >= floor_h) [max(p.x - wall, 0), p.y]];
inner_down = [for (i = [len(inner_from_top) - 1 : -1 : 0]) inner_from_top[i]];

profile = concat(
    outer,                          // up the outside, base -> rim
    [[rim.x - wall, rim.y]],        // across the rim thickness
    inner_down,                     // down the inside, rim -> floor
    [[0, floor_h], [0, 0]]          // across the floor, close to axis
);

rotate_extrude($fn=140) polygon(profile);
```

Checklist for any revolved vessel:
- [ ] Profile built as ONE closed cross-section (outside → rim → inside →
      floor → close), never `difference()` of two separate revolves
- [ ] Control points run through `smooth_path()` before use — a raw
      `polygon()` on hand-picked points shows visible facet rings
- [ ] If the vessel should be open, its rim point is off-axis (x > 0)
- [ ] Rendered to PNG and actually looked at — angled AND top-down — not
      just STL-exported on faith
- [ ] `$fn` high enough for the smallest feature (120–160 is a reasonable
      default for a ~250mm-scale piece; too low shows visible facets on
      the outer silhouette)

## Technique 2 — Functional/practical: BOSL2 rounded solids

**Use BOSL2's `cuboid()`/`cyl()` rounding parameters, not manual
`minkowski()` or hand-built fillets** — they're correct, fast, and let you
target specific edges by name.

```openscad
include <BOSL2/std.scad>

// Multi-compartment desk organizer -- validates FDM-safe rounding and
// correct wall/floor thickness for a real functional part.
size = [120, 80, 40];   // W x D x H (mm) -- named vars, never magic numbers
wall = 2.4;              // 3x 0.4mm nozzle passes
floor = 3;
corner_r = 4;
n_bays = 3;

module outer_shell() {
    // edges="Z" rounds ONLY the four vertical corner edges -- this fillet
    // lies flat in the XY plane, so it has ZERO print overhang. Rounding
    // the BOTTOM face's edges instead would create an overhang right at
    // the bed contact line and risk first-layer adhesion -- don't do that.
    cuboid(size, rounding=corner_r, edges="Z", anchor=BOTTOM);
}

bay_w = (size.x - wall * (n_bays + 1)) / n_bays;
bay_d = size.y - wall * 2;
bay_r = max(corner_r - wall, 1);

difference() {
    outer_shell();
    for (i = [0 : n_bays - 1]) {
        bx = -size.x / 2 + wall + bay_w / 2 + i * (bay_w + wall);
        translate([bx, 0, floor])
            cuboid([bay_w, bay_d, size.z], rounding=bay_r, edges="Z", anchor=BOTTOM);
    }
}
```

Checklist for any functional solid:
- [ ] Every dimension is a named variable (`size`, `wall`, `corner_r`,
      ...) — never a bare number baked into the geometry, so a future
      `-D` override actually works (this is CLAUDE.md's own OpenSCAD
      design rule, not new here)
- [ ] Wall thickness ≥ ~0.8mm absolute minimum, ≥2.4mm for anything
      handled/structural
- [ ] Rounded edges are chosen by axis (`edges="Z"`, or BOSL2's other
      edge-selector syntax) so bed-contact edges stay flat — never round
      every edge indiscriminately on a part that sits on the build plate
- [ ] Any angle steeper than 55° from vertical is either supported,
      reoriented, or redesigned — don't assume "OpenSCAD rendered it
      fine" means "prints fine"
- [ ] Rendered to PNG and actually looked at before calling it done

## Reference: real MakerWorld designs (2026-08-21)

Before iterating further on a design, it's worth checking what actually
works for other makers — searching MakerWorld (or Printables) surfaces
real, popular, battle-tested design patterns instead of guessing at what
"looks nice." Two searches done for this shop's vase/organizer models
turned up concrete, reusable ideas:

- **Asanoha Kumiko Pen Holder** (6,900+ downloads, 18,500+ likes) — wraps a
  hexagonal pen holder shell in a hemp-leaf geometric lattice surface
  pattern, and slants every compartment's opening toward the user for
  one-handed retrieval. Both ideas translate directly: a repeating raised
  diamond-trellis texture (Technique 3 below), and validation that a
  scooped/slanted compartment opening (already in Technique 3's wedge-cut
  example) is a real, popular ergonomic pattern, not a novelty.
- **Voronoi/organic-lattice vases** — open cellular surface patterns that
  catch light and shadow, popular for their visual depth. A true Voronoi
  tessellation needs real cell-graph math this codebase doesn't have, but
  a **crossed double-helix** (the helical-rib technique below, run twice
  with opposite twist direction) gets a comparable woven-lattice look for
  free, since it reuses the exact same proven `path_sweep()` approach.

**Relief depth only reads correctly from an angled view.** Verifying a
raised surface texture (ribs, the diamond trellis) against a straight-on
orthographic render is misleading — a flat-topped raised feature has the
*same surface normal* as the surrounding wall, so head-on/axial lighting
shows zero shading difference between them no matter how deep the relief
actually is; only the feature's *side* walls (facing away from an axial
light) go dark, so a straight-on render of a real, correctly-raised
texture can still look like a flat dark silhouette. This isn't a bug to
chase — it's a property of single-directional-light preview rendering
under head-on lighting, and it matches how relief generally photographs
(carvings, embossing, coins all need raking light to read). Always verify
relief texture from an angled view, matching how it'll actually be seen
or photographed — a straight-on check can make correct geometry look
broken and send you chasing a bug that isn't there. Separately, a
shallow-but-real bump (0.3mm proud, tried first on the organizer) still
reads as too subtle even at an angle — 0.7–0.9mm proud was the difference
between "barely visible" and "genuinely bold" texture in direct
side-by-side renders; don't assume any nonzero relief is enough without
actually comparing depths.

**Don't reuse an OpenSCAD builtin name as your own variable, even with
different intent, even in a different scope.** This shop's own scripts
already use `floor` as a variable name (tray/vessel floor thickness) —
`floor` is also OpenSCAD's builtin `floor()` function. A module written
with `ny = floor((panel_h - floor - 4) / cell)` (the outer `floor(...)`
being the intended builtin call, the inner bare `floor` intended as the
outer script's floor-thickness variable) happened to work in-context only
because the outer variable was in scope with a compatible value — copying
that same module into a different file with no such variable defined
produced **silently empty geometry** (bare `floor` resolved to `undef`,
`floor(undef)` propagated, the for-loop range collapsed to nothing, zero
errors). Rewrite to avoid the name entirely (a plain numeric margin, or a
differently-named variable) rather than relying on it resolving
correctly by scope-capture accident.

## Technique 3 — Adding character (2026-08-21, real worked examples)

A structurally-correct model can still look generic. Two proven ways to add
real character without compromising printability, both built and verified
on the vase/organizer above:

**Spiral/decorative ribs on a revolved body — reuse the silhouette's own
sample points, don't recompute a radius function.** A helical rib that
follows a vessel's existing bulge/waist (rather than a plain constant-
radius spiral) looks intentional, not bolted-on, and is free because
`smooth_path()`'s output already has the sample points you need:

```openscad
// outer = the same smooth_path() silhouette used to build the vessel.
// Winds the SAME points around `turns` full revolutions instead of one --
// the rib automatically follows the vase's own bulge/waist because it's
// built from the vase's own profile, not a separately-computed curve.
turns = 3.5;
rib_r = 0.9;
n = len(outer);
trim = 6;   // skip first/last few samples so the swept tube's flat end
            // caps land buried mid-wall, not poking out at the base/rim
            // seam (a real cosmetic artifact seen on the first attempt)
helix_pts = [for (i = [trim : n - 1 - trim])
    let(p = outer[i], ang = i * turns * 360 / (n - 1), rr = p.x + rib_r * 0.35)
    [rr * cos(ang), rr * sin(ang), p.y]
];
rib_profile = [for (a = [0:30:359]) [rib_r * cos(a), rib_r * sin(a)]];
union() {
    rotate_extrude($fn=140) polygon(profile);   // the verified hollow vessel
    path_sweep(rib_profile, helix_pts, closed=false);
}
```

A shallow continuous helix like this has no overhang problem — it's the
same "gradual angle change, no sudden step" reasoning that already makes
vase-mode single-wall printing reliable. Set `rr` (the rib's radial offset
from the surface) so the tube overlaps the wall by less than its own
radius — enough to weld on union, not so much it disappears inside. Verify
with `openscad --render`'s own CGAL stats: `Simple: yes` confirms a valid
non-self-intersecting mesh; a top-down render is also worth a look since a
lighting-artifact diagonal band (see Setup above) is easy to mistake for a
sweep defect on a piece that now has real surface detail to get confused by.

**Ergonomic/decorative cuts via `hull()` of a handful of points — not a
manually rotated box.** A rotated `cuboid()` positioned by hand-derived
trig is exactly the kind of thing that either misses its target or (worse)
oversizes and silently eats the whole model in a `difference()` — this
happened building the organizer's pen-access scoop: a first attempt with
`rotate([25,0,0])` on a guessed-size box rendered to a **completely blank
model**, no error, because the rotated box's true bounding extent was far
larger than intended and the subtraction consumed everything. `hull()` of
explicit corner points is fully deterministic — every coordinate is a real
X/Y/Z you chose on purpose, no rotation math to get wrong, and `hull()`
always produces a valid convex solid:

```openscad
// A wedge-shaped cut sloping the top-front of a wall down to
// `scoop_min_wall` mm above the floor -- e.g. so pens/markers in a
// compartment can be grabbed without reaching straight down.
scoop_depth = 26;
scoop_min_wall = 14;   // NEVER cut below this -- keep real structural wall
x0 = bay_left; x1 = bay_right;             // the cut's width, in real X
y_front = size.y / 2 + 1;                  // 1mm past the outer face -- clean cut through
y_back = y_front - scoop_depth;
z_top = size.z + 5;                        // well above the model -- clean cut from above
z_low = floor + scoop_min_wall;
pts = [
    [x0, y_back, z_top], [x0, y_front, z_top], [x0, y_front, z_low],
    [x1, y_back, z_top], [x1, y_front, z_top], [x1, y_front, z_low],
];
hull() for (p = pts) translate(p) sphere(r=0.01, $fn=6);
```

Build and look at any `hull()`-based cut **in isolation** before
subtracting it from the real model (exactly how the scoop above was
debugged) — it's a five-second render and it turns "why did my model
vanish" into "here's the wedge, here's why it's wrong" immediately, instead
of debugging through a `difference()` of a dozen other shapes.

## Technique 4 — Engraved branding/text (2026-08-21)

A maker's mark or product name engraved into the underside is a real,
common convention (matches "printed by / made with" marks seen on
MakerWorld models) — printable with zero extra risk since it's a shallow
recess in the flat, bed-facing bottom face, not an overhang.

**Whether bottom-engraved text reads correctly or backwards is a genuine
trap — this session got the VERIFICATION METHOD wrong twice before landing
on a reliable one, even though the actual fix (`mirror([0,1,0])` on this
exact `translate`+`linear_extrude` pattern) was right the whole time.**
Timeline, because the false starts are as instructive as the answer:
1. Shipped `brand_mark()` with no mirror. Scott asked "Is it backwards?"
2. Built a self-styled verification test (an asymmetric "R", the whole
   OBJECT rotated 180° about X to simulate picking it up, rendered with a
   hand-picked `--camera=...`), concluded `mirror([0,1,0])` was needed,
   shipped it.
3. Scott opened the actual STL in a real phone 3D viewer and reported it
   still looked backwards, alongside a second image that read as
   confirming the *original unmirrored* version instead — reverted to no
   mirror on that basis.
4. Scott reported the reverted (unmirrored) version was ALSO backwards.
   Net: both a real per-Scott check on Round 2 *and* Round 3 came back
   "backwards" — an apparent contradiction with no single mirror axis
   satisfying both reports.
5. Rather than guess a third time, built a multi-candidate STL: several
   plates side by side, one per candidate transform (no mirror /
   mirror-X / mirror-Y / mirror-both), each plate a **different, obvious
   size** (20/30/40/50mm) so Scott could identify the correct one
   unambiguously over chat without any position- or marker-based
   confusion (a first attempt used tiny raised dots as identifiers —
   too small to see in the viewer; size was the fix). Scott checked in
   his real viewer and confirmed: the 40mm plate (`mirror([0,1,0])`)
   reads correctly. Re-applied that exact transform to the real vase and
   Scott confirmed it correct there too.
6. The Round-3 "revert" was very likely a misreading of ambiguous
   feedback, not a real signal that the mirror was wrong — the size-coded
   multi-candidate test is what finally produced an answer Scott could
   confirm with zero ambiguity, and it matched the ORIGINAL Round-2 fix
   all along.

**Two separate lessons here, don't conflate them:**
- **Don't trust an in-script rotation or hand-picked camera trick to
  verify chirality/mirroring.** Rotating the whole OBJECT 180° while
  leaving the render camera fixed does NOT correctly simulate how a real
  viewer shows the underside (a real viewer orbits the CAMERA around a
  stationary object — physically flipping an object and rotating a camera
  around a fixed one are different transforms). A separate attempt to
  verify via hand-picked `--camera=` elevation angles also failed
  immediately with an unrelated wrong view. This codebase does not have a
  reliable in-script way to check this — don't invent one.
- **When asking a human to identify one of several candidates over chat,
  make the identifying feature impossible to misread or lose in
  translation.** Position ("the third one") depends on an unstated
  left/right convention in the viewer that may not match the file's
  authoring order. Small markers (a few raised dots) can be too tiny to
  see. A large, unmistakable, independently-verifiable property — plate
  SIZE, checkable with the viewer's own ruler tool — removed all
  ambiguity in one shot. Design the disambiguator to survive being
  described back to you in a single short reply.

```openscad
// Engraves into the ACTUAL bottom face (z=0, the face touching the print
// bed) -- reads as a maker's mark when the piece is picked up or tipped.
// mirror([0,1,0]) is REQUIRED for this exact translate+extrude pattern --
// confirmed correct on the real, assembled vase by Scott checking the
// generated STL in a real phone 3D viewer (see the saga above for how
// many wrong turns it took to get an unambiguous answer). Don't treat
// this axis as generalizable to a different placement/orientation
// pattern without re-running the size-coded multi-candidate test below.
logo_depth = 0.8;
module brand_mark() {
    // z spans -0.5 to logo_depth -- MUST dip below the surface (z<0) for
    // the boolean to actually overlap the solid. A cutter placed to only
    // touch z=0 with no negative overlap removes nothing (confirmed live:
    // an off-by-a-hair version of this, cutting from z=3.01 upward on a
    // z:[0,3] solid, rendered a flawless-looking but completely
    // UNENGRAVED disk -- Simple: yes, zero errors, wrong result).
    translate([0, 3, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("Brand Name", size=9, font="Dancing Script:style=Bold",
                     halign="center", valign="center");
}
difference() {
    /* the vessel/part */;
    brand_mark();
}
```

**The size-coded multi-candidate verification pattern** (reusable
whenever chirality is in question and a human needs to confirm which of
N transforms is right):

```openscad
// One plate per candidate transform, each a distinct, obvious SIZE so
// the human reporting back can name the answer unambiguously ("the
// 40mm one") -- no shared position/marker convention needed.
gap = 70;
module plate_candidate(idx, size, mirror_x, mirror_y) {
    translate([idx * gap, 0, 0]) difference() {
        cube([size, size, 3]);
        translate([size/2, size/2, -0.5])
            linear_extrude(height=2) {
                if (mirror_x && mirror_y) mirror([1,0,0]) mirror([0,1,0])
                    text("R", size=size*0.45, halign="center", valign="center");
                else if (mirror_x) mirror([1,0,0])
                    text("R", size=size*0.45, halign="center", valign="center");
                else if (mirror_y) mirror([0,1,0])
                    text("R", size=size*0.45, halign="center", valign="center");
                else text("R", size=size*0.45, halign="center", valign="center");
            }
    }
}
plate_candidate(0, 20, false, false);  // no transform
plate_candidate(1, 30, true, false);   // mirror X
plate_candidate(2, 40, false, true);   // mirror Y
plate_candidate(3, 50, true, true);    // mirror both
```

Checklist for engraved branding:
- [ ] Orientation confirmed via a real human checking the actual generated
      file in a real STL viewer — never an in-script rotation/camera
      trick. If more than one transform is plausible, use the size-coded
      multi-candidate pattern above rather than describing candidates by
      position or small markers
- [ ] Font family confirmed real via `fc-list | grep -i '<family>'` — an
      unregistered/misspelled family renders **empty text geometry, no
      error** (see Setup above for the auto-registration this repo now
      does; still worth confirming on a new/unusual family)
- [ ] Cutter's Z-range actually dips *below* the surface being engraved,
      not just touches it — verify by checking the numbers, not just that
      the render succeeded (this exact off-by-a-hair mistake produced a
      perfectly valid, completely unengraved model on the first attempt)
- [ ] Text + any underline/rule sized to fit inside the actual available
      flat area (e.g. within the base radius of a round vessel) — check
      against the real profile's base dimension, not a guess
- [ ] Positioning/sizing (does the text fit, is the underline in the right
      place, is the depth right) is fine to check with a normal render on
      the assembled model — that part of "render and look" is reliable.
      Orientation/mirroring specifically is not (see above) — check that
      part in a real viewer, separately

## Technique 5 — Non-axisymmetric textured bodies: `skin()`, not a segment union (2026-08-21)

`rotate_extrude()` only works for a cross-section that's constant around
the full 360° — it can't do vertical fluting, faceting, or any texture
that varies by ANGLE as well as height. For that, loft a series of 2D
ring profiles (one per height sample) using BOSL2's `skin()`:

```openscad
function flute_pts(r) = [for (a = [0:5:355])
    // radius dips near each flute's center, absolute mm depth --
    // NEVER a fraction of r (see the real bug below)
    let(rr = r - flute_depth * (1 - abs(cos(a * n_flutes / 2))))
    [rr * cos(a), rr * sin(a)]
];
outer_profiles = [for (p = outer) flute_pts(p.x)];  // `outer` = the usual
outer_z = [for (p = outer) p.y];                    // smooth_path silhouette
skin(outer_profiles, z=outer_z, slices=0);
```

Hollow it by `skin()`-ing a SECOND, smaller set of profiles (radius minus
wall thickness) and subtracting — since neither shell touches the
rotation axis (both are just rings of points, no axis-degenerate case),
this never hits the 2D-`offset()` self-intersection pitfall from
Technique 1 at all; a plain `difference()` of two independent skins is
sufficient and safe.

**A real, confirmed performance trap: don't build this as a `union()` of
many separate per-segment `linear_extrude(scale=...)` pieces — it times
out.** A first attempt lofted the silhouette by looping over every
`smooth_path` sample and emitting one `linear_extrude(height=h,
scale=r1/r0)` per segment (~90 segments × 2 shells). CGAL has to compute
a pairwise boolean for every one of those ~180 separate solids just to
union/subtract them — this hung past a 150s timeout. Switching to a
single `skin()` call per shell (one mesh via triangulation, not a boolean
union of many solids) rendered the exact same silhouette+texture in under
45 seconds. If a loft is timing out, this is the first thing to check —
look for an implicit union of many small extrudes and replace it with one
`skin()` call. (Also worth knowing: OpenSCAD 2021.01 does NOT support
passing a `function()` literal as a module argument to pick between ring
shapes at each step — that syntax parses in newer dev snapshots but not
this version. Use a plain boolean flag and a ternary/if inside the loop
instead, confirmed working.)

**A real, confirmed geometry bug: texture depth must be an ABSOLUTE
value, never a fraction of the local radius.** A first attempt at the
flute depth above used `r * flute_depth_frac` (a percentage of the local
radius) — looked fine at the wide base, but at the vase's narrow waist
(~22mm radius) the groove depth scaled down too, except the WALL
THICKNESS didn't scale with it, and the flutes punched clean through to
the interior — confirmed visually, holes clearly visible through to the
hollow cavity. Fixed by making the depth a fixed mm value, sized well
under the wall thickness (0.7mm groove on a 2.4mm wall) so it stays a
safe margin under the wall at every point on the silhouette, not just the
widest one. Whenever a texture's depth is expressed relative to
something local (radius, segment length), check it against the SMALLEST
value that variable takes anywhere on the model, not the value where you
happened to eyeball it.

**Straight flutes → spiral/barley-twist flutes is a one-parameter change,
not a new technique.** Give `flute_pts()` a `phase` argument and shift
each ring's pattern by an amount that grows with height:
`rr = r - flute_depth * (1 - abs(cos((a - phase) * n_flutes / 2)))`, with
`phase = p.y / vase_height * total_twist` (e.g. `total_twist = 300`
degrees base-to-rim for a visible but not extreme twist). Same `skin()`
call, same hollowing approach, same wall-thickness-margin rule above
still applies unchanged.

## Technique 6 — Floating disconnected geometry from an overlapping cut (2026-08-21, real Scott catch)

**A texture/detail feature that's welded onto a wall (a rib, a lattice
diamond, a boss) can be silently ORPHANED if a later `difference()`
removes the wall material it was embedded into — the model still renders
clean, but the printed part has loose disconnected pieces.** Not
hypothetical: the organizer's Kumiko diamond trellis (Technique 3) is
welded onto the front wall by embedding half of each diamond into the
wall surface. The ergonomic scoop cut (also Technique 3) removes a wedge
of the SAME front wall in the wide bay's region — and several diamonds
sat inside that wedge's footprint. The scoop removed their embedded half,
leaving the outer (proud) half floating with nothing connecting it to the
shell. Scott caught it on the physical/visual result ("There were
floating parts. We can't have that on 3d prints") — a completely valid,
correct call; a disconnected fragment either falls off mid-print, gets
lost inside a support structure, or never bonds to the layer below it.

**How this was actually found and fixed — trace it in the code, don't
just stare at a render.** The floating pieces were visible in earlier
renders (small disconnected dots near the top of the wide bay) but had
been misread as "the back wall's texture, visible through the open bay
top due to perspective" — a plausible-sounding explanation that was
never actually verified and turned out to be wrong. The reliable fix
came from reading the two modules' real numeric ranges side by side: the
lattice module's diamond Z-positions (`pz = 2 + cell/2 + iy*cell` for
each row) and the scoop module's Z/X range (`z_low` to `z_top`, `x0` to
`x1`) — once both are visible as plain numbers, the overlap is obvious
without needing to render anything.

**The fix: give the texture placer the SAME footprint the cut uses, and
skip placement inside it — with a margin.**

```openscad
// Expose the cut's footprint as plain values the placer can check
// against, not just buried inside the cut module.
scoop_x0 = bay_start(0);
scoop_x1 = bay_start(0) + bay_w[0];
scoop_z_min = floor + scoop_min_wall;

module kumiko_wall(panel_w, panel_h, proud, is_front) {
    ...
    // margin = d_size/2 so a diamond whose EDGE (not just center) would
    // reach into the cut's footprint is also excluded -- a partially
    // clipped diamond is still a floating-connection risk.
    in_scoop = is_front
        && px > scoop_x0 - d_size/2 && px < scoop_x1 + d_size/2
        && pz > scoop_z_min - d_size/2;
    if (abs(px) < panel_w/2 - d_size/2 && !in_scoop) {
        translate([px, 0, pz]) rotate([90,0,45]) cuboid([d_size, d_size, proud*2]);
    }
    ...
}
```

**A genuinely useful corroborating check for this specific bug class:
compare CGAL's `Volumes` count before and after, on the SAME model.**
`openscad --render`'s stats report a `Volumes` count for the Nef
polyhedron. In isolation this number is NOT reliably interpretable (a
single correct hollow vessel can report 2 or 3 depending on how CGAL
counts the interior cavity — don't try to derive meaning from one
snapshot, that's exactly the mistake that led to a wrong conclusion
during this session's engraved-vase-mirror investigation). But comparing
the SAME model's count before and after a fix is a real, cheap signal:
the buggy organizer reported `Volumes: 11` (many small disconnected
diamond fragments each counting as their own volume); the fixed version
reports `Volumes: 2` (solid + hollow interior, matching every other
known-good model in this skill). A large before/after drop like that is
worth treating as real evidence; a single absolute number is not.

## Technique 7 — When a render looks wrong but the geometry is provably right (2026-08-21)

Built a honeycomb-textured wall (same weld pattern as the Kumiko diamonds
in Technique 3, hexagons instead) and the render showed only a thin,
sparse-looking line of texture near the top of the wall — nothing like
the full multi-row coverage the diamond version showed at the same
`proud` depth. Spent real effort chasing this as a bug: checked hexagon
orientation, checked a single hex against axis markers, boosted `proud`
from 0.9 to 1.3mm, boosted cell size from `hex_r=4.2` to `6.0` — the
render never meaningfully improved.

**Before accepting "the render looks sparse" as evidence of a bug, parse
the actual STL and check the numbers directly** — this is what actually
resolved it, not another render attempt. Three checks in increasing
specificity, all on the real generated file:

```python
import re
verts = re.findall(r'vertex\s+([-\d.eE]+)\s+([-\d.eE]+)\s+([-\d.eE]+)', open(path).read())
pts = [(float(x),float(y),float(z)) for x,y,z in verts]
# 1. Do proud (raised) vertices exist at all, and what's their range?
proud = [p for p in pts if p[1] > wall_surface_y]  # e.g. > 42.6 for a wall at y=42.5
print(min(p[0] for p in proud), max(p[0] for p in proud))  # X spread
print(min(p[2] for p in proud), max(p[2] for p in proud))  # Z spread
# 2. Are they spread across the WHOLE wall, or clustered somewhere?
from collections import Counter
print(Counter(round(p[2] / row_step) for p in proud))     # per-row vertex counts
```

This proved the texture was complete and correctly distributed — every
expected row had real vertex counts, X/Z spread covered nearly the full
panel — while every render kept showing only the top rows clearly. The
render wasn't lying about geometry that didn't exist; it just couldn't
show it at the default camera/lighting combination, for reasons not
fully diagnosed (denser/smaller hex cells at tighter row spacing than
the diamond version, at the same oblique default camera angle, apparently
compress into an unreadable band — changing `proud` or cell size didn't
fix it, so it isn't simply "too shallow" the way the earlier diamond
relief issue was).

**The actionable lesson: when a render's visual read and a direct
numeric check of the same STL disagree, trust the numbers, not another
render attempt.** Guessing at a fourth or fifth camera angle to try to
*make* a correct model look correct is a waste of effort once the
geometry is already proven — and this session's own history (the
engraved-vase mirror saga) already established that this codebase's
render pipeline is not always a reliable arbiter of visual questions.
Direct STL inspection is slower to set up than another render call but
gives an unambiguous, arithmetic answer instead of one more subjective
image to squint at.

## Technique 8 — Market research before design research (2026-08-21)

Before searching MakerWorld for design *ideas*, it's worth checking what
actually *sells* — MakerWorld's own like/download counts measure "makers
who like this design," not "buyers who pay for it." For a genuinely new
product (not iterating on an existing one), search broadly for real
best-selling-on-Etsy data first (e.g. "best selling 3D printed items on
Etsy 2026"), THEN go to MakerWorld for design specifics on whatever
category that research surfaces. Two independent searches for this shop
both put phone stands at the top — "lead the pack," universal appeal,
low material cost, high margin — which is a stronger signal than any
single MakerWorld collection's like count, since it's about what people
actually buy, not what other makers find interesting to look at.

**A safe pattern for composing a functional part from several distinct
solid pieces (a base + an angled wall + a lip, not a single lofted
shape):** anchor each piece so its local origin sits at the specific
edge/corner where it should meet the base (`anchor=BOTTOM+FRONT` etc.,
BOSL2 supports compound anchors), position it with a plain `translate()`,
and — deliberately, not as an afterthought — embed it a small amount
(~1mm) *below* the surface it's welded onto, not flush with it. A
flush/coincident join can render fine and still be a fragile edge case;
a small forced overlap costs nothing (it's inside the part, invisible)
and removes any doubt. Getting this wrong is easy: swapping an anchor
from `BOTTOM` to `TOP` without re-deriving the whole position chain
produced a completely different, wrong shape on the first attempt here —
change one variable in a position chain, re-render immediately, don't
assume the rest of the logic still applies with the new anchor.

## Technique 9 — Carving a through-cut face into a curved body (2026-08-21)

Building a jack-o'-lantern's carved face (real through-holes, like an
actually-carved pumpkin) needed several distinct small cuts — two eyes, a
nose, a jagged mouth — into an already-ribbed, curved outer wall. Using
`rotate()` + `linear_extrude()` for these (the pattern used for engraved
text) means re-deriving a rotation sign for every new feature shape and
placement, which this session has gotten wrong on the first attempt
enough times to treat as a real risk, not a one-off.

**Safer for this case: extend the hull()-prism technique from the
organizer's scoop cut to ALL face features.** Every cutter is built from
plain 2D points in the XZ plane, each placed at two real Y depths and
hulled into a prism — no `rotate()`, no sign to get right or wrong:

```openscad
y0 = 25; y1 = 50;  // chosen with margin past both the inner cavity AND
                    // the outer rib surface at every feature's height —
                    // checked against the silhouette's real radius, not
                    // guessed
module prism_xz(pts2d) {
    hull() {
        for (p = pts2d) {
            translate([p[0], y0, p[1]]) sphere(r=0.01, $fn=6);
            translate([p[0], y1, p[1]]) sphere(r=0.01, $fn=6);
        }
    }
}
eye_pts = [[-6,0],[6,0],[0,11]];
translate([-16, 0, 34]) prism_xz(eye_pts);   // convex shape -- hull()
                                              // preserves it correctly
```

**This only works for a CONVEX 2D shape** (a triangle, a rectangle) —
`hull()` of two copies of a concave/non-convex shape (like one continuous
zigzag mouth with teeth) fills in the concave notches, destroying the
jagged silhouette. For the jack-o'-lantern's toothy grin, decompose it
into several small convex pieces (a row of separate rectangular mouth
openings) with gaps of uncut material left BETWEEN them — the gaps read
as the teeth, without ever needing a concave hull.

**When several small cuts sit close together, a render can make them
look like one big merged hole even when they aren't — verify by
checking for real material in the gaps, not by trusting the shading.**
The finished jack-o'-lantern face rendered as one solid dark blob with no
visible separation between the eyes/nose/mouth — looked exactly like the
cuts had merged into one opening. Checking the STL directly (are there
still real outer-surface vertices, at the expected radius, in the bridge-
of-nose gap between the eyes, and in each gap between mouth segments?)
confirmed distinct material remained everywhere it should. Same lesson
as Technique 7, a different flavor of it: several deep, closely-spaced
cuts under this renderer's single-directional lighting flatten into one
dark silhouette with no internal shading gradient — that's expected for
this renderer on this kind of geometry, not evidence the cuts merged.

## Technique 10 — Bigger/bolder geometry does NOT fix a render-visibility problem, and how to actually prove a carved feature to a human who already pushed back (2026-08-21)

Direct follow-up to Technique 9. Scott's feedback on the delivered pumpkin
was blunt on two points: "I want a jack o lantern face" (the small,
close-together cuts weren't reading at all) and "I the stem does not look
good" (the original 2-segment cone). Two different fix shapes were needed —
worth separating clearly, because only one of them turned out to be a real
geometry problem.

**The stem was a real design problem, fixed with a proven technique used
elsewhere in this skill.** A flat 2-segment cone has no personality. Chained
`translate()+rotate()` cylinder segments (the same nested-local-frame
pattern used for other multi-segment shapes) with tapering radius and
cumulative rotation per segment produces a real pronounced curl/hook —
confirmed as a decisive visual improvement by direct render inspection, no
ambiguity, no numeric-verification detour needed:

```openscad
module stem() {
    translate([0, 0, 61]) cylinder(h=9, r1=10, r2=8.5, $fn=32);
    translate([0, 0, 70]) rotate([0, -14, 0]) union() {
        cylinder(h=9, r1=8.5, r2=7, $fn=32);
        translate([0, 0, 9]) rotate([0, -22, 0]) union() {
            cylinder(h=8, r1=7, r2=5.3, $fn=32);
            translate([0, 0, 8]) rotate([0, -29, 0])
                cylinder(h=7, r1=5.3, r2=3.2, $fn=32);
        }
    }
}
```
Each segment's rotation is applied INSIDE the previous segment's already-
translated+rotated frame, so the angles are cumulative and the curl
compounds naturally — no manual trig to re-derive per segment.

**The face was NOT a real geometry problem — it was proven correct twice
(Technique 9, and again here on a bigger/bolder version) — but "the
geometry is provably right" was not, by itself, an acceptable answer to
give Scott a second time.** Making the eyes/nose/mouth larger and more
widely spaced (bigger triangles, 3 bold teeth instead of 5 small ones) did
NOT change how the render looked — it was still one dark blob at every
camera angle tried, including an isolated body+face-only render with the
stem removed specifically to rule out the stem's bounding box confusing
`--autocenter --viewall`. This confirms the render limitation is really
about deep/close cuts on a curved surface under single-directional
lighting (Technique 7's lesson), not fixable by making the cuts bigger —
don't burn another render-iteration cycle assuming "bigger will surely show
up" once this pattern is already established.

**The fix that actually worked: render the cutter geometry ALONE, as solid
positive shapes, with no body around it.** This sidesteps the whole
rendering-limitation problem instead of fighting it — a solid triangle/
rectangle sitting on a plain background has full ordinary shading and reads
instantly, with zero ambiguity, even though the SAME shapes as negative
cuts on the curved ribbed body still render as one blob:

```openscad
// Same exact point data used as face_cuts() -- but linear_extrude()'d as
// solid positive shapes, not subtracted from anything. No hull()-prism
// depth needed here since there's no body to cut through.
module solid_face_preview() {
    translate([-21, 0, 35]) linear_extrude(height=6) polygon(eye_pts);
    translate([21, 0, 35]) linear_extrude(height=6) polygon(eye_pts);
    translate([0, 0, 23]) linear_extrude(height=6) polygon(nose_pts);
    for (i = [0:n_gaps-1]) { ... }  // same tooth loop as face_cuts()
}
```

This rendered as 5 unmistakably separate solids — two triangle eyes, one
triangle nose, three rectangular teeth, laid out in the exact classic
jack-o'-lantern arrangement — genuinely legible in one glance, no
explanation required. Paired with the numeric STL check from Technique 9
(confirming the SAME point data survives as real material once actually
cut into the body), this gives two independent, mutually-reinforcing forms
of proof instead of one contested render.

**The actionable lesson: when a render-visibility limitation has already
cost you credibility once (a human directly said "I want to see it," not
"tell me it's there"), don't re-run the same failing verification method
hoping a bigger version will finally show up, and don't just repeat the
same numeric-proof explanation that didn't land the first time. Find a
genuinely different presentation of the SAME underlying data that sidesteps
the specific rendering limitation** — here, showing the cutter shapes as
solids instead of as cuts. This is a more convincing, faster, and more
honest resolution than either "trust me" or a fourth guessed camera angle.

## Technique 11 — Making a preview render actually look natural: color() and organic irregularity (2026-08-21)

Scott asked directly whether the pumpkin could "look natural," pointing at
real references. Two independent fixes, found by checking a real reference
search (myminifactory/cults3d/printables jack-o-lantern listings) against
what this model's renders were actually missing:

**1. Color is the single biggest lever, and `render_scad(fmt="png")` cannot
show it — this is a real, confirmed tool limitation, not a script bug.**
Every prior render in this whole pumpkin build was OpenSCAD's default flat
teal ("Tomorrow" colorscheme's object color), which reads as generic
plastic no matter how good the geometry is. Real jack-o-lantern references
are unanimous: vivid orange body, brown/woody stem. Adding `color([0.93,
0.42, 0.08])` / `color([0.40, 0.28, 0.12])` around the body/stem in the
.scad source is correct and does nothing to the STL (color is a preview-
only concept; the printed color comes from filament) — but confirmed live:
`render_scad(..., fmt="png")` always adds `--render` (forces the full CGAL/
Nef-polyhedron boolean evaluation), and OpenSCAD does not reliably carry
per-object `color()` through that path once a `union()`/`difference()`
combines differently-colored children — the PNG comes out in the flat
default color regardless of what the script says. **The fix: render the
PNG WITHOUT `--render`** (plain OpenCSG preview mode, `openscad -o out.png
--imgsize W,H --colorscheme Tomorrow --autocenter --viewall in.scad`, no
`--render` flag) — colors show up exactly as written. `render_scad()`
itself hardcodes `--render` for `fmt="png"` (reasonable default — CGAL mode
is the more "correct" full boolean evaluation, useful when checking
geometry), so a colored preview currently needs a direct `openscad` CLI
call (same `xvfb-run -a --server-args="-screen 0 1024x768x24"` +
`LIBGL_ALWAYS_SOFTWARE=1` + `OPENSCADPATH=assets/openscad_libs` wrapping
`render_scad()` already does) rather than going through the wrapper
function for this specific need. Worth knowing next time a model needs a
natural-looking preview, not just a geometry check.

**2. Perfect uniformity reads as fake — a real pumpkin's ribs are never
identical.** Added a slow, non-integer-frequency modulation on top of the
existing per-rib depth function so it varies smoothly around the
circumference instead of repeating identically on every rib:
```openscad
function rib_pts(r) = [for (a = [0:5:355])
    let(rr = r - rib_depth * (1 - abs(cos(a * n_ribs / 2))) * (0.82 + 0.18 * sin(a * 2.3 + 11)))
    [rr * cos(a), rr * sin(a)]
];
```
The `2.3` frequency is deliberately non-integer relative to `n_ribs` so the
irregularity doesn't fall into its own repeating pattern (which would just
look like a *different* kind of mechanical uniformity). This is additive
and low-risk: it only scales the SAME depth term that was already proven
safely under the wall-thickness margin (Technique 5's lesson), so it can't
introduce a new punch-through — confirmed by re-checking `Simple: yes`/
`Volumes: 2`/zero warnings after the change, identical to every prior
version.

**Net result:** the exact same body+face+stem geometry, unchanged in every
way that matters for printing, immediately read as "a real pumpkin" once
given real color and slightly irregular ribs — geometry alone was never
going to fix "doesn't look natural." When a human says a model doesn't
look natural/real and references are available, check color/materials
handling in the render pipeline before assuming it's a shape problem.

## Technique 12 — A stacked-segment stem still reads as fake; a single continuous `path_sweep()` is the fix (2026-08-21)

Even after Technique 11's color fix, Scott said the stem specifically was
"still off" and needed to be genuinely better, not tweaked. The Technique-
9-era stem (nested `translate()+rotate()` tapered cylinder segments — see
the stem module before this fix) LOOKED like an improvement over the flat
2-segment cone in isolation, but under real color it was obviously a stack
of distinct barrel segments with visible seam rings at every joint — a
robot-arm look, not a woody curled stem. The chained-cylinder technique is
still correct and useful elsewhere in this skill (bent/curled shapes where
a segment-by-segment approach is the only option), but for a stem
specifically, a smoothly curving natural form needs ONE continuous swept
mesh, not discrete joints.

**The fix: BOSL2's `path_sweep()` — one ridged cross-section, swept along a
smooth curved spline, tapered continuously via the `scale` parameter.** No
joints, no seams, because it's genuinely one mesh, not a union of several:

```openscad
// Curl the path in 2D (X = horizontal curl, Z = height), THEN smooth it --
// smooth_path() on the CONTROL points (not a hand-sampled curve) is what
// gives the swept stem a continuously accelerating curl instead of visible
// kinks at each control point.
stem_ctrl = [
    [0, 0], [0, 10], [-1, 18], [-4, 24], [-9, 29], [-15, 32], [-20, 33],
];
stem_path2d = smooth_path(stem_ctrl, method="corners", size=3, splinesteps=8);
stem_path3d = [for (p = stem_path2d) [p.x, 0, p.y]];  // lift into 3D (Y=0 plane)

// A real pumpkin stem's cross-section is angular/ridged (5 longitudinal
// ridges is typical), not a plain circle -- reuses the exact same
// "absolute-mm-depth cosine dip" technique as the body's ribs (Technique 5),
// just applied to a small stem-scale radius instead of the body radius.
n_ridge = 5;
ridge_depth = 1.1;
function ridge_pts(r) = [for (a = [0:15:345])
    let(rr = r - ridge_depth * (1 - abs(cos(a * n_ridge / 2))))
    [rr * cos(a), rr * sin(a)]
];

module stem() {
    translate([0, 0, 59])  // embeds ~2mm into the body top for a clean weld
        path_sweep(ridge_pts(9), stem_path3d, scale=0.22, twist=30, $fn=32);
}
```

`scale=0.22` tapers the cross-section down to 22% of its base size by the
tip — one parameter, continuously interpolated along the whole sweep
(`scale_by_length=true` is the default), instead of manually shrinking
`r1`/`r2` on every separate segment. `twist=30` adds a gentle 30° spiral
to the ridges along the length — a small, cheap touch that reads as an
organic growth pattern rather than a machined part. Confirmed clean:
`Simple: yes`, `Volumes: 2` (body+stem, no floating pieces), unchanged
from every prior version — the only stderr line is an advisory `PolySet
has nonplanar faces. Attempting alternate construction`, OpenSCAD's own
automatic fallback triangulation for a curved swept mesh, non-fatal and
still produced a simple/manifold result.

**The actionable lesson: when a chained-segment approach is "good enough"
but a human says a curved organic part still looks wrong, check whether
the segments themselves are visible as segments (seam rings, faceted
joints) before assuming the curve shape or color is the problem.** A
smoothed control-point path fed into a single `path_sweep()` (reusing the
same `smooth_path()` this skill already uses for the body silhouette, plus
BOSL2's built-in taper/twist parameters) removes the visible-joints problem
entirely, for less code than the segment-chain version it replaces.

## Technique 13 — Real-viewer confirmation resolves what this pipeline's own render never could, and use it to fix PROPORTIONS not just prove geometry (2026-08-21)

Scott opened the actual STL in a real mobile viewer (screenshot, front
view) after the previous round's "trust the numbers + here's the cutter
shapes in isolation" explanation. Two outcomes from that single screenshot,
worth separating:

**1. It settled the render-vs-geometry question for good, in this
model's favor.** The real viewer's face reads perfectly clearly — genuine
depth shading, correctly separated eyes/nose/mouth, no blob. This confirms
what Technique 9/10/12's numeric STL checks already established
(real material in every gap) was correct the whole time — this codebase's
own `render_scad(fmt="png")` pipeline (both `--render` CGAL mode AND plain
OpenCSG preview mode, both tried) is simply not a reliable way to
photograph a deep multi-cut carved face at this camera/lighting
combination, full stop. Stop trying to fix this pipeline's rendering of
that specific feature class going forward — a numeric STL check plus
pointing Scott at a real viewer (or this screenshot pattern) is the correct
resolution, not another camera-angle guess.

**2. But it ALSO surfaced a real, separate defect a render could never
have caught: PROPORTIONS.** "The face needs a lot of work" wasn't about
visibility — the geometry was always genuinely a face — it was that the
eyes/nose/mouth were small and bunched up near the stem, leaving a large
dead blank band of plain ribbed surface below with no feature on it. This
is a design-judgment defect, invisible to any geometry-correctness check
(the cuts WERE separated, WERE real, and STILL looked wrong to a human
because they were badly placed and undersized). **Numeric verification
proves cuts don't merge/leak — it does not, and cannot, prove the
features are well-proportioned or well-placed.** Those are two genuinely
different questions; don't let a passing numeric check stand in for the
second one.

**The fix: compute the body's real radius-by-height profile instead of
eyeballing placement, and size features against the widest usable band.**
Linearly interpolating `body_ctrl`'s own control points (the same data
already driving the loft) shows the outer radius stays large (43-46mm)
from about z=8 to z=35, then tapers toward the stem above that — a ~27mm-
tall prime "canvas" that the original face placement (eyes at z=35, already
past the widest point and shrinking) never used. Moved the whole face
down onto that band and scaled every feature up substantially:

```openscad
// Eyes: z=30 (was 35), x=±20, 26x22mm triangles (was ~18x15mm)
eye_pts = [[-13, 0], [13, 0], [0, 22]];
translate([-20, 0, 30]) prism_xz(eye_pts);
translate([20, 0, 30]) prism_xz(eye_pts);

// Nose: z=15 (was 23), 20x16mm (was ~14x12mm)
nose_pts = [[-10, 0], [10, 0], [0, 16]];
translate([0, 0, 15]) prism_xz(nose_pts);

// Mouth: wider span (66mm vs 56mm), taller teeth (22mm vs 12mm),
// trapezoid shape (wider at the base) instead of plain rectangles --
// still a convex quad, so the hull()-prism technique (Technique 9) still
// applies unchanged.
mouth_w = 66; top_w = seg_w * 0.65;
pts = [[-top_w/2, 25], [top_w/2, 25], [seg_w/2, 3], [-seg_w/2, 3]];
```

Re-verified the SAME way as every prior face iteration (Technique 9/10's
numeric gap-check, re-run against the new bigger coordinates) before
shipping — bigger cuts closer together are a real risk of actually merging
this time, so the check isn't optional just because it passed before at a
smaller size.

**The actionable lesson: when a human reports a carved/cut feature "needs
work" after already confirming via a real viewer that it exists and is
visible, the next round of feedback is almost certainly about
composition (size, placement, balance on the available surface), not
about proving existence again.** Go compute where the good real estate on
the model actually is (don't re-guess placement a second time either) and
resize/reposition against that, rather than re-running the same
existence-proof techniques that already succeeded.

## Technique 14 — Matching real reference photos exactly: a continuous mouth cavity with solid tooth remnants, not separate tooth blocks with uncut gaps (2026-08-21)

Scott sent two real reference photos of classic commercial jack-o-lantern
lithophane designs after the previous round still wasn't right. Comparing
those photos directly against the actual model exposed two concrete, fixable
mistakes — not vague "make it better" feedback:

**1. The eyes and nose had almost no vertical gap and read as one merged
shape.** Eye base at z=30, nose apex at z=31 — 1mm apart, nothing near
enough separation once combined with the render's own flattening tendency.
Every feature now gets a real multi-mm gap to its neighbors, checked
numerically (not eyeballed) before rendering anything.

**2. The mouth's whole structure was backwards from a real jack-o-lantern.**
The prior version had 3 separate solid tooth-blocks with big UNCUT gaps
between them (only the "teeth" were cut; everything between them was left
as solid, uncut pumpkin material). Comparing to the reference photos: a
real carved mouth is the OPPOSITE — ONE continuous cut cavity spanning
nearly the whole mouth width, with just two or three SMALL SOLID remnants
left uncut within it to form teeth. The visual difference is large: the
old version reads as 3 isolated notches in an otherwise-intact wall; the
correct version reads as one dark grin with small light-catching teeth
inside it.

**The fix: build the cut as a `difference()` of (cut region) minus (teeth
to keep solid), nested inside the outer body-carving `difference()`.**
Each piece is still a simple convex quad through the proven `prism_xz()`
hull-of-two-Y-depths technique (Technique 9) — the trick is in how they
combine, not in inventing new cutting geometry:

```openscad
module mouth_cutter() {
    difference() {
        union() {
            // the whole mouth cavity -- wide flat base + taller "risers"
            // at each corner so the mouth silhouette isn't a flat slab
            translate([0, 0, 2]) prism_xz([[-30,0],[30,0],[30,11],[-30,11]]);
            translate([0, 0, 2]) prism_xz([[-30,0],[-19,0],[-19,17],[-30,17]]);
            translate([0, 0, 2]) prism_xz([[19,0],[30,0],[30,17],[19,17]]);
        }
        union() {
            // small "keep-solid" rectangles -- subtracted FROM the cutter
            // itself, so these two spots are excluded from what gets
            // removed from the body and remain real material (teeth)
            translate([0, 0, 2]) prism_xz([[-6,0],[-1,0],[-1,7],[-6,7]]);
            translate([0, 0, 2]) prism_xz([[1,0],[6,0],[6,7],[1,7]]);
        }
    }
}
```

Because `mouth_cutter()` is itself subtracted from the body in the outer
`difference()`, subtracting the "keep-solid" zones from the CUTTER (not
from the body) inverts correctly: those two zones never get removed, so
they stay as solid teeth poking up into an otherwise fully-open cavity.

**Verification had to go further than prior rounds, because this is more
complex CSG (a difference nested inside a difference nested inside a
difference) — more nesting means more chances for a subtle sign/logic
mistake to produce something that LOOKS plausible on a naive spot-check
but is actually wrong.** The check that caught this reliably: render a
SECOND reference STL of the exact same body with `face_cuts()` disabled,
then for every target coordinate, look up the real uncut-surface vertex
from that reference file and check whether that EXACT vertex still exists
in the cut mesh. This is stronger than a generic "radius > threshold"
heuristic — a naive radius check false-flagged the cut cavity's own wall-
boundary vertices (right at the cutter's near-Y-plane) as "surviving
material" near the corners on a first pass, which would have produced a
false PASS on a real defect. Comparing against the exact known-good vertex
from an uncut reference eliminates that ambiguity. A fine-resolution sweep
across the whole mouth width at a fixed height (checking cut/solid/cut/
solid/cut in sequence) additionally confirmed the cavity is genuinely
continuous around both teeth, not accidentally left uncut somewhere it
shouldn't be.

**The actionable lesson: when a human sends real reference photos after
multiple rounds of "still not right," the fix is comparison, not more
guessing.** Look at exactly what differs structurally between the
reference and the current model (not just "make it bigger" again) — here,
the real structural error was CUT vs. UNCUT being backwards for the mouth,
not a sizing problem at all. And treat each round's growing CSG complexity
as a reason to strengthen verification (reference-file vertex lookup, not
just a radius heuristic), not to skip it because "it passed numeric checks
last time too."

## Technique 15 — A revolve profile touching the axis at ONE point renders fine in preview but fails EVERY boolean op (2026-08-21, real ghost-build catch)

Building a kawaii ghost (columnar body + domed top, `rotate_extrude()` of a
`smooth_path()` silhouette that closes to a point at the top: `[..., [14,
62], [0, 68]]`) — every preview PNG render looked completely correct
through several iterations of hem-scallop and face work. The first attempt
to actually render an STL (which requires a real CGAL boolean for the
`difference()` that carves the hem/face) failed outright:

```
ERROR: The given mesh is not closed! Unable to convert to CGAL_Nef_Polyhedron.
Current top level object is empty.
```

**Root cause, confirmed by isolated repro (not guessed):** a `rotate_extrude()`
profile whose top point sits exactly ON the rotation axis (`x=0`) closes to
a single vertex there, not an edge — OpenSCAD's raw polygon closure handles
this fine for a plain PolySet export (a bare, un-differenced `rotate_extrude()`
exports to STL with zero complaints), but the moment ANY boolean op
(`difference()`, even one subtracted sphere) forces a CGAL Nef-polyhedron
conversion, that single-point axis contact is a degenerate/non-manifold cap
CGAL rejects outright. Reproduced across `$fn` 16–140 (rules out a
resolution fluke) and with a minimal 3-point profile — confirming this is a
structural property of the profile, not a resolution or library issue.

**The fix is a one-character nudge: never let a revolve profile's pole sit
at exactly `x=0` if the result will ever go through a boolean.** Change
`[0, 68]` to `[0.5, 68]` (or any small positive value) — visually
indistinguishable in any render (the top still rounds to what looks like a
point through `smooth_path()`'s own corner smoothing), but now the profile
closes across a tiny real disk instead of a single degenerate vertex, and
every subsequent boolean op succeeds cleanly (confirmed: `Simple: yes`,
clean `Volumes: 2`, zero warnings, immediately after the fix).

**The actionable lesson, and why this is more dangerous than most bugs in
this skill: PNG preview rendering (`fmt="png"`, no `--render` OR with
`--render`) does NOT exercise the same code path as an actual boolean/STL
export, so a model can preview perfectly through many iterations of design
work and still be completely un-exportable.** Every technique in this
skill up to now has been caught by "render a PNG and look at it" — this
one specifically could NOT be, because the preview succeeded regardless of
the bug. **The real guard: render an actual STL (via a real `difference()`,
not just the bare shape) as an early sanity step on any revolve-based
design, before investing further iteration in face/texture/hem details on
top of it** — don't wait until the very end to discover the base shape was
never exportable. Any `rotate_extrude()` profile with a point at `x=0` that
will be differenced against anything should get this nudge as a matter of
course, the same reflexive way Technique 1's vessel profiles already keep
their rim off-axis when the vessel needs to be open.

## Technique 16 — A scalloped/wavy hem via a ring of overlapping sphere cutters (2026-08-21)

For a ghost's classic wavy "draped fabric" bottom edge (or any silhouette
that needs a repeating wave/scallop around a revolved body's rim), the
reliable technique is a ring of N overlapping sphere cutters subtracted
from the body — no `rotate()` sign risk, no concave-hull problem, and it
reads correctly from any angle since it's genuinely 3D, not a flat relief:

```openscad
n_legs = 6;
scallop_r = 12.5;
module scallop_cutters() {
    for (i = [0:n_legs-1]) {
        a = i * 360 / n_legs;
        translate([17 * cos(a), 17 * sin(a), 3])
            sphere(r = scallop_r, $fn = 40);
    }
}
```

N cutters placed evenly around the circumference carve N gaps, which
leaves N rounded points ("legs") of solid material hanging between them —
cutter count directly equals leg count, no separate accounting needed.
Tuning notes from getting this right: the cutter's radial position
(`17` above, versus the body's own rim radius of ~24-27) and its own
radius (`scallop_r`) both need to be generous enough to bite deep dips —
an early attempt with cutters barely overlapping the rim produced a
barely-visible wave, not a real scalloped hem; pulling the cutters further
IN (smaller radial position, so more of the sphere overlaps the body) and
using a bigger `scallop_r` produced dramatically better, more clearly
"legged" results, confirmed via a direct before/after render comparison.
Real reference photos (classic ghost lithophane designs) show 5-7 gentle
lobes, not 3-4 — matching that count mattered for the design reading as
"a ghost" rather than "a cut sphere."

## Technique 17 — Simple face features via shallow dimples, not through-cuts, and a hull()-chain for a smooth curved line (2026-08-21)

For a SOLID decorative figurine (not a lit/hollow luminary like the
pumpkin), face features don't need the hull()-of-two-Y-depths prism
technique (Technique 9) at all — that technique exists specifically to cut
all the way through a shell wall. A shallow dimple is much simpler and has
zero rotation/orientation risk: position a sphere so it intersects the
outer surface by only 2-3mm (sphere center placed just inside the nominal
surface radius, sphere radius large relative to that overlap so it reads
as a shallow round dimple, not a crater):

```openscad
// Oval almond eye -- a sphere scaled taller than wide, same shallow-dimple
// principle, just non-uniformly scaled first.
translate([-8, eye_r_body - 2.3, eye_z])
    scale([1, 1, 1.5]) sphere(r = 3.6, $fn = 24);
```

**A row of separate spheres for a curved line (like a smile) reads as a
beaded chain of bumps, not a smooth line — even when each dimple is
individually correct.** First attempt at a smile used 5 independent
spheres along a gentle arc; even with radius/spacing tuned so they
technically overlapped, the render showed 5 distinct rounded bumps, not
one continuous groove. **Fix: `hull()` each ADJACENT PAIR of points along
the path, and union all those hulls** — this produces a genuinely
continuous rounded tube instead of a series of spheres that merely touch:

```openscad
smile_pts = [for (i = [-2, -1, 0, 1, 2])
    [i * 2.5, eye_r_body - 1.8, eye_z - 11 + abs(i) * 1.3]];
for (k = [0:len(smile_pts) - 2])
    hull() {
        translate(smile_pts[k]) sphere(r = 2.6, $fn = 20);
        translate(smile_pts[k + 1]) sphere(r = 2.6, $fn = 20);
    }
```

This is the same `hull()`-of-two-points primitive used throughout this
skill (the organizer's scoop cut, the pumpkin's face prisms), just walked
along a chain instead of used once — confirming it generalizes cleanly to
"smooth curved line through N points," a genuinely reusable pattern
whenever a feature needs to read as one continuous stroke rather than a
row of dots.

**A real sign-flip bug worth flagging even though it's obvious in
hindsight: a "curls up at the corners" smile needs the OUTER points at
HIGHER z than the center, not lower.** First attempt used
`eye_z - 11 - abs(i) * 1.8` (outer points subtract MORE, ending up lower)
— this draws a frown, not a smile, and it wasn't obvious from the numbers
alone; it took an actual render to notice the mouth curved the wrong way.
Fixed by flipping the sign to `+`. Small reminder that "which direction is
up" sign errors are common enough in this kind of coordinate math that
even a simple 5-point curve is worth an actual visual check, not just
"the CSG rendered without error."

## Technique 18 — Height-varying angular texture (draped fabric folds) via skin(), depth as a function of both angle AND z (2026-08-21)

Scott's feedback after the first working ghost was direct: "needs more
detail... don't forget the reference photos." Comparing again against the
reference photos found the real gap — the classic ghost lithophane
references all show visible vertical fold/drape lines running down the
body (a "sheet draped over something" look), and the shipped version was
a completely smooth column. This is a genuinely different texture need
than anything else in this skill: Technique 5's rib/flute texture varies
depth by ANGLE only (constant depth at every height); this needed depth
to vary by BOTH angle and height — deep folds near the hem where fabric
would puddle, fading to smooth by the dome top where a sheet would pull
taut.

**The fix: make the existing angular-modulation formula's depth term a
function of z, not a constant, and switch the body from `rotate_extrude()`
to `skin()`** (required because `rotate_extrude()` can only revolve ONE
constant cross-section — any per-height variation needs a loft of
per-height profiles, same reasoning as Technique 5):

```openscad
function fold_depth(z) = fold_depth_min + (fold_depth_max - fold_depth_min)
    * max(0, min(1, 1 - z / 48));   // 1.0 near the hem (z=0), fades to 0 by z=48

function fold_pts(r, z) = [for (a = [0:5:355])
    let(
        d = fold_depth(z),
        rr = r - d * (1 - abs(cos(a * n_folds / 2))) * (0.78 + 0.22 * sin(a * 1.7 + 4))
    )
    [rr * cos(a), rr * sin(a)]
];
outer_profiles = [for (p = body) fold_pts(p.x, p.y)];   // p.y is height here
skin(outer_profiles, z = [for (p = body) p.y], slices = 0);
```

The `(0.78 + 0.22*sin(a*1.7+4))` term is Technique 11's organic-
irregularity trick (a slow, non-integer-frequency wobble layered on top of
the primary fold count) carried over unchanged — still matters here for
the same reason: perfectly uniform folds would read as a mechanical
pattern, not real fabric.

**Verification had to confirm the height-fade genuinely works, not just
that folds exist somewhere.** Sampling real surface-vertex radii around
the circumference at several different heights and comparing the actual
measured spread against `fold_depth(z)`'s predicted value at each height
matched to 3 decimal places (e.g. z≈5: measured 1.707mm spread, predicted
1.718mm; z≈65: measured 0.150mm, predicted 0.150mm) — strong, specific
confirmation that the height-dependent formula is doing exactly what it's
supposed to, not just "some texture exists."

**The actionable lesson, tying back to Technique 13's earlier finding:
"needs more detail" after a design already passed numeric verification
almost always means a missing STRUCTURAL feature visible in the reference
photos, not a request to polish something already present.** The fix
here wasn't tuning an existing parameter — it was recognizing the
references had an entire texture dimension (folds varying by both angle
and height) that the shipped design never attempted. Go back to the
reference photos specifically named in the feedback and look for what
kind of surface variation exists that the current model doesn't have at
all, rather than adjusting existing knobs further.

## Technique 19 — Sharp corrugation vs. soft ripple is a formula-shape choice, not an amplitude tweak; and phase-align repeating features so they read as ONE thing (2026-08-21)

Two more rounds of ghost feedback, both resolved by comparing directly
against the same reference photo rather than guessing at parameters:

**"Smoother surface, put the ripples in like the reference photos"** —
Technique 18's fold formula used `abs(cos(a*n/2))`, which has a hard,
non-smooth cusp (kink) at every zero-crossing — this reads as sharp
pleats/corrugation, not soft draped fabric, no matter how the amplitude
is tuned. The fix is a different formula SHAPE, not a smaller number:
drop the `abs()` entirely and use a plain `(0.5 + 0.5*cos(a*n))` term —
mathematically smooth (C-infinity, no kinks) everywhere. Paired with
fewer waves (6 broad folds instead of 9 narrow ones, matching what the
reference photos actually show) and roughly half the amplitude. Verified
numerically that the new spread scaled proportionally with the amplitude
ratio (measured 0.578mm vs. predicted ~0.58mm from the 1.1/1.9 depth
ratio) and that per-step radius change was gradual (no spike), confirming
"smooth" quantitatively and not just by eye.

**Phase-align a repeating cut pattern with a repeating texture pattern so
they read as ONE cohesive feature, not two unrelated layers.** The
reference photos show each fold flowing continuously down into one
rounded hem point — the fold ridges and the hem legs are the SAME
visual element, not independent decorations. Getting the math right for
"put a ridge at the same angle as a leg center" is easy to get
subtly wrong: `cos(n*a - phase) = -1` solves to `a = (180+phase)/n`, and
a first attempt claimed `phase=180` gives leg-center alignment when it
actually doesn't — `(180+180)/6 = 60`, landing ridges exactly on the CUT
NOTCHES instead (30 degrees off, the opposite of the stated intent).
**This was caught by numeric verification (sampling real STL surface
radius around the circumference and finding the true maxima angles),
not by eye or by re-checking the algebra harder** — the render at this
scale/lighting didn't make a 30-degree phase error visually obvious. The
actual fix was almost embarrassingly simple: no phase term needed at all
(`cos(n*a)` alone already puts the first ridge at `180/n`, which for
n=6 is exactly 30 degrees, i.e. the leg center) — the bug was an
unnecessary added term, not a missing one.

**The general lesson: whenever two repeating features (a cut pattern, a
texture pattern) are meant to visually align, verify the alignment
numerically against the real mesh — don't trust hand-solved trig or a
code comment's own claim about what it does.** A comment asserting
"phase=180 aligns ridges to leg centers" was simply wrong arithmetic that
looked plausible on the page; only checking the actual rendered geometry
caught it.

## Technique 20 — Print-in-place ball-and-socket joints, chained across multiple segments (2026-08-26)

First multi-joint articulated build in this shop (a 4-segment creature —
head/body1/body2/tail — connected by 3 ball-and-socket joints). An
isolated single-joint test (ball and socket both centered at the same
origin, trivially coincident) passed cleanly, but wiring the SAME
mechanism into a real multi-segment chain surfaced two real, independent
defects — both invisible in a preview render, both caught only by
reconstructing the STL's actual connected components from shared
vertices/edges (not by trusting CGAL's `Volumes` count, which conflates
the ambient region and doesn't distinguish "3 genuinely separate solids"
from "1 fused solid + 2 orphaned junk shells").

**Defect 1 — a rod that points away from its own ball.** The intended
shape: `ball_rod(ball_r, rod_r, rod_len)` should place the ball at local
`z = -rod_len` (hanging below the segment's own bottom face) and a rod
connecting that ball UP to the segment's own origin at `z = 0`. The first
attempt got the ball right but wrote the rod as a bare
`cylinder(h=rod_len, r=rod_r)` — which defaults to spanning `z=0` to
`z=+rod_len`, i.e. growing AWAY from the ball, into the segment's own
already-solid interior, never touching the ball at all. The ball ended up
a fully-formed, correctly-sized, correctly-clearanced sphere — and a
completely disconnected island, floating in space with zero material
connecting it to anything:

```openscad
// WRONG -- rod extends away from the ball, never reaches it
module ball_rod(ball_r, rod_r, rod_len) {
    translate([0, 0, -rod_len]) sphere(r = ball_r);
    cylinder(h = rod_len, r = rod_r);              // spans z:[0, rod_len]
}
// RIGHT -- rod spans the SAME range the ball sits in
module ball_rod(ball_r, rod_r, rod_len) {
    translate([0, 0, -rod_len]) sphere(r = ball_r);
    translate([0, 0, -rod_len]) cylinder(h = rod_len, r = rod_r);  // z:[-rod_len, 0]
}
```

**Defect 2 — matching end-radii (or even just touching ends) weld the
whole chain solid, independent of the joints.** Segments were built as
`hull()` capsules (a proven safe technique elsewhere in this skill), each
one a `hull()` of a bottom sphere and a top sphere. Two problems compound
here: (a) adjacent segments were stacked with literally the SAME radius
at the touching end (e.g. `head_t = body1_b = 12`) at zero gap — two
capsules whose meeting end-spheres are identical in position and radius
fuse into one continuous smooth solid, full stop, regardless of what
joints exist elsewhere; (b) independent of matching radii, a
`hull(sphere, sphere)` capsule's rounded end bulges PAST its own nominal
height along the central axis — `hull()` of a sphere of radius `r` at
`z=h` reaches up to `z = h + r` at the very top, not just `z = h` — so
even *mismatched* end radii can still physically overlap into the next
segment's supposed empty space if you only account for the nominal
stacking height and not the actual bulge extent.

**The fix has two parts, and both matter:**
1. **Flat (not rounded) joint-facing ends.** Give `capsule()` a
   `flat_bottom`/`flat_top` option that swaps the rounding sphere for a
   flush `cylinder(h=0.02)` disc at whichever end sits at a joint — this
   caps the segment at EXACTLY its nominal height, no bulge past it.
   Free ends (the head's own bottom, the tail's own tip) keep the normal
   rounded sphere cap.
2. **A real air gap between every segment pair**, bridged by nothing but
   the thin rod. `rod_len` has to grow to cover the full gap PLUS the
   reach down to the lower segment's embedded socket:
   `rod_len_for(h, gap) = (h - embed_z(h)) + gap`. Verified directly: with
   a 2–3mm gap and flat ends, ray-casting a point in the gap region
   off-axis (away from the rod) returns genuinely empty space, while a
   point on the rod's own axis returns solid — confirming the two
   segments are connected ONLY by the rod, nothing else.

**Verification method that actually caught both defects — reconstruct
real connected components from the mesh, don't read CGAL's summary
number.** `Volumes: 5` was reported for BOTH the broken v1 (1 fused
backbone + 3 disconnected junk shells = 4 real components) and the fixed
v2 (4 real independent segments = 4 real components) — the CGAL stat
alone cannot tell these two totally different, one-broken-one-working
structures apart, because it counts the ambient region the same way in
both cases and doesn't care whether the "extra" volumes are meaningfully
attached to anything. The check that actually distinguishes them: union-
find over every triangle's vertices in the real exported STL, then read
off (a) how many disjoint components exist, (b) each component's real
world-Z bounding range (a fused chain shows ONE component spanning the
entire assembly height; a working chain shows 4 components each spanning
only its own segment), and (c) which component each joint's ball and
socket actually belong to (a working joint's ball belongs to the segment
ABOVE it; its socket cavity boundary belongs to the segment BELOW it —
they must be in DIFFERENT components, never fused into one).

**The actionable lesson: a mechanism proven correct in isolation
(Technique-9-style, single joint, both parts trivially centered on the
same point) does NOT prove the mechanism survives being embedded at a
real hand-derived offset in a real multi-part assembly.** The placement
algebra itself (`embed_z`, `rod_len_for`) was accurate to within
0.001–0.1mm once both defects were fixed — the algebra was never the
problem. The problem was two structural assumptions (rod direction,
segment-end geometry) that a single-joint isolated test has no way to
exercise, because an isolated test has no neighboring segment to
accidentally fuse with and no reason to get the rod's direction wrong
when the ball is the only other thing in the file. Chaining a proven
mechanism into a real assembly is a genuinely different verification
task, not a formality — budget for a real connected-component check, not
just "the render still looks fine."

## Technique 21 — Competitive benchmarking when the reference site blocks automated access: what actually separates a "solid decorative shape" from a "top-tier design" (2026-08-26)

Scott asked for a direct quality benchmark against MakerWorld's top items —
"see how you can get better." MakerWorld sits behind Cloudflare bot
protection (a legitimate anti-automation measure, not a bug to route
around — confirmed via direct `curl`: a clean `403` with a Cloudflare
managed-challenge page, same result whether via plain `curl` or a real
headless Chromium through this session's proxy). **Don't try to defeat
that protection** (spoofing more convincing headers, solving the
challenge, etc.) — it exists on purpose. Two working alternatives instead:

1. **Text-based research via web search still works and is genuinely
   useful** — search result snippets and cached page descriptions surface
   real, specific quality signals (e.g. "hollowed-out eyes designed to
   glow with an internal light source," from real product descriptions)
   even when the source page itself can't be screenshotted.
2. **Other top-tier platforms in the same category (Printables, Cults3D,
   Thingiverse, MyMiniFactory) may not share the same bot-wall** — worth
   checking each individually (a plain `curl` HEAD-equivalent check, not
   a full browser) before assuming the whole research approach is
   blocked. Two of these were reachable in this session even when
   MakerWorld and Printables both 403'd.

**The concrete finding this research produced: the ghost design's real
quality gap was structural, not cosmetic.** Every prior round of ghost
feedback (Techniques 16-19) improved shape, texture, and proportion on a
model that was completely SOLID with 2mm surface dimples for eyes.
Research into what actually makes top Halloween lantern/lithophane
designs read as high-quality surfaced a concrete, specific pattern this
design was missing entirely: **real ones are hollow lantern shells with
an open base for a tealight/LED, and the "eyes" are true through-cuts
that let light escape** — not a decorative shape with shallow surface
markings. This matches what the reference photo itself already showed
(genuinely lit, glowing eyes) — a detail that had been visually matched
in spirit (dark ovals) but never structurally built.

**Converting a solid shape into a hollow lantern shell, safely, reuses
Technique 5's existing hollowing pattern exactly — the only new
discipline is computing the inner offset from the FLAT base silhouette,
never the textured outer radius:**

```openscad
wall = 3;
outer_profiles = [for (p = body) fold_pts(p.x, p.y)];   // textured/rippled
inner_profiles = [for (p = body) circle_pts(max(p.x - wall, 0.1))];  // plain offset from p.x, NOT from fold_pts(p.x,...)
module shell() {
    difference() {
        skin(outer_profiles, z=outer_z, slices=0);
        skin(inner_profiles, z=inner_z, slices=0);
    }
}
```

If the inner profile were instead computed by subtracting `wall` from the
ALREADY-textured outer radius, local wall thickness at a fold valley
would be `wall - fold_depth` — for this design's `fold_depth_max=1.1` and
`wall=3`, that's still safely positive (1.9mm), but it's a real trap for
a texture with more amplitude: always compute the inner offset from the
untextured base silhouette, matching Technique 5's original wall-margin
lesson (check against the smallest value a variable takes, not the
typical one).

**No new floor/opening logic was needed for the open base** — BOSL2's
`skin()` caps both ends by default (confirmed by reading the library
source directly rather than assuming), so outer and inner are each
independently closed solids; subtracting one fully-capped solid from
another naturally leaves only a thin wall-thickness RING at the base
(where outer's bottom cap extends past inner's smaller bottom cap) with
the rest of the interior open above it — exactly the "open base with a
stable contact rim" shape a real tealight lantern needs, for free, from
the exact same technique already used to hollow the body at all.

**Verification for a hollow-plus-through-cut redesign needs to check
things that never mattered on a solid model** — wall thickness at the
thinnest point (not just "it rendered"), whether a "through-cut" really
reaches the interior (not just a deep-looking dimple), and whether the
base is genuinely open (not accidentally capped). A useful corroborating
signal here: CGAL's own `Volumes` count on the WHOLE model (not per-
region) told a real story once compared against a known control — a
genuinely sealed hollow shape (`difference(){sphere(20);sphere(17);}`)
reports `Volumes: 3` (exterior + shell + one sealed interior cavity);
this ghost reported `Volumes: 2`, meaning CGAL itself sees no separate
enclosed cavity — independent confirmation that the interior really is
open to the outside (through the eyes and the base), not sealed. Pair
that whole-model signal with targeted ray-casting/point-containment
checks at the specific eye and base coordinates for a result that's
verified two different ways, not one.


## Technique 20 — No live visual browsing of MakerWorld/Printables; the real research workflow (2026-08-27)

Scott asked directly whether past "MakerWorld research" in this skill was
visual (actually looking at the site) or code-driven (text search only).
Honest answer, confirmed by testing live rather than assuming: **every
prior MakerWorld/Printables reference in this skill came from `WebSearch`
text snippets — titles, descriptions, like/download counts — never an
actual screenshot of the site.** Tested whether that could be fixed with
a real browser in this environment and found two separate, real blockers,
worth recording so a future session doesn't re-discover them the hard way:

1. **MakerWorld and Printables return HTTP 403 through this environment's
   outbound proxy** — a genuine organizational policy denial (confirmed
   via direct `curl` through the proxy, not a tool bug). Per this
   environment's own hard rule, a 403/407 policy denial is reported, not
   retried or routed around.
2. **Independent of that, Playwright/Chromium in this container currently
   cannot complete ANY proxied HTTPS navigation** — even a plain,
   fully-permitted test page (`example.com`, confirmed reachable via
   `curl` through the same proxy at the same moment) fails with
   `net::ERR_CONNECTION_RESET` from the browser specifically. This is a
   browser/proxy integration gap in this container, not a per-site block —
   don't waste time trying more sites or more Chromium flags (`--no-sandbox`,
   `--disable-quic`, `ignore_https_errors` were all tried) before checking
   whether this has been fixed at the environment level first.

**The agreed real workflow going forward (mixed, per Scott's explicit
choice 2026-08-27), given visual site browsing isn't available:**

- **Default: propose from text research, then build.** Use `WebSearch`
  for market/popularity signals (Etsy bestseller trends, MakerWorld/
  Printables/Thingiverse search snippets, r/functionalprint discussion) —
  same as Technique 8's "market research before design research," just
  more explicit about citing what was actually found vs. inferred. Present
  concrete named candidates with real evidence before building, not vague
  categories.
- **Scott supplies real reference photos when a design needs visual
  grounding or isn't landing right** — proven highly effective twice this
  session (the pumpkin's face proportions, the ghost's fold texture and
  hem shape) specifically BECAUSE Scott sent real photos and this skill's
  existing discipline (Technique 13/19: compare directly against the
  photo, verify numerically, don't just trust a render) already handles
  that case well. Ask for photos proactively when a design category is
  visually unfamiliar or a first attempt doesn't match expectations,
  rather than guessing repeatedly.
- **For genuinely mechanical/functional designs** (hinges, latches,
  adjustable joints, snap-fits, gears), load `data/knowledge_base/
  3d_printing_expertise.md` (DfAM rules, real FDM tolerances, slicer
  settings) and `.claude/skills/3d-print-design/ENGINEERING_REFERENCE.md`
  (BOSL2 mechanical/organic tooling) alongside this skill — those are
  real, sourced, text-researched knowledge (same "no visual browsing"
  caveat applies to how they were built) that directly inform whether a
  mechanism will actually function once printed, not just whether the
  mesh is valid.
- **Always finish with a real visual comparison pass before calling a
  design done** — against Scott's reference photos when supplied, or at
  minimum an honest self-critique against what the text research actually
  described, using this skill's own render+numeric-verification
  discipline (Technique 7, 9, 13) as the check that replaces "browse and
  compare" when browsing isn't available.

## Technique 21 — Real honeycomb lattice (open through-cuts), not raised relief: build it on FLAT faces, not a curved surface (2026-08-27)

Technique 7's "honeycomb" was raised bump RELIEF on a flat panel wall
(decorative texture). A genuinely different need came up: a honeycomb pen/
planter holder where the hexagons are real OPEN CELLS you can see through
— the defining feature of an actual honeycomb lattice, not a texture.

**The reliable way to cut a true hex lattice: make the body's outer shape
a polygon prism with FLAT faces (a `cylinder($fn=6, ...)` IS a hexagonal
prism — free, no extra code), then cut each flat face's hex grid with
plain straight-through cutters in that face's own local frame, rotated
into world position per face.** This sidesteps the curved-surface cutting
risk entirely (no hull()-prism depth range needed, no rotate() sign
ambiguity beyond a single well-understood per-face rotation):

```openscad
apothem = R * cos(180 / n_sides);      // center-to-face distance
module hex_cell() {
    rotate([90, 0, 0])                  // axis along local +y, THROUGH the wall
        cylinder(r = hex_r, h = wall + 4, $fn = 6, center = true);
}
module face_honeycomb() {
    // lay out a grid in this face's local (x, z), each cell at
    // translate([x, apothem, z]) so it sits exactly on the flat face
    for (row = ...) for (col = ...)
        translate([x, apothem, z]) hex_cell();
}
module all_faces() {
    for (i = [0:n_sides-1]) rotate([0, 0, i * 360/n_sides]) face_honeycomb();
}
```

**A real first-attempt bug worth flagging: getting only ONE column of
cells per face instead of a full lattice.** `n_cols = floor(usable_width /
pitch)` silently evaluates to 1 when `hex_r` is sized too large relative
to the face width — the render looked like a single zigzag column of
hexagons down the middle of each face, not a mistake in the loop logic at
all, just cell size vs. available space. Fixed by shrinking `hex_r`
substantially (6.5mm → 2.8mm) and enlarging the body (R 42→50, H 90→100)
— always sanity-check `n_cols`/`n_rows` come out as more-than-one before
assuming a grid-generation bug when a render shows too few repeats.

**Keep an uncut rim margin on every edge** (top, bottom, AND the vertical
seams between faces) — `rim_h` in Z and `rim_h/2` inset in X — so the
lattice band never perforates the load-bearing edges/corners of the
prism. Verified via point-in-mesh testing (ray-casting, not raw vertex
presence — a flat cap can be triangulated with zero interior vertices at
a test point even though it's genuinely solid there) that the rim bands
and corner seams stayed solid while the lattice band itself was real
open cells with a genuine hollow interior behind them.

## Technique 22 — A real working print-in-place hinge: stepped shaft + trapped sleeves (2026-08-27)

First genuinely mechanical (not just decorative) moving-part design this
shop has built: a barrel hinge that prints already assembled, rotates
freely, and can't be pulled apart. The standard, correct technique (many
"print in place hinge" designs on MakerWorld/Thingiverse use this exact
shape, confirmed by reasoning through the mechanics, not by copying code):

**Part A ("the shaft") is ONE continuous piece: a thin rod running the
full hinge length, with periodic FAT COLLARS fused onto it at alternating
slots.** Part B ("the sleeves") are hollow tube segments that ride on the
THIN sections between A's collars — trapped axially because their own
inner bore is smaller than A's collar radius on both sides, but free to
spin because there's real radial clearance around the thin rod:

```openscad
pin_r = 2.0; clearance = 0.4; knuckle_r = 3.5;
slot_len = 4; slot_gap = 0.4;            // axial gap so faces don't touch either
pitch = slot_len + slot_gap;

module a_shaft() {                        // part A -- fuse this to the base body
    rotate([0,90,0]) cylinder(r=pin_r, h=total_len, $fn=32);      // full-length thin rod
    for (i = [0,2,4])                                              // fat collars, even slots
        translate([i*pitch,0,0]) rotate([0,90,0])
            cylinder(r=knuckle_r, h=slot_len, $fn=32);
}
module b_sleeves() {                      // part B -- fuse this to the lid body
    for (i = [1,3])                                                // sleeves, odd slots (the gaps)
        translate([i*pitch,0,0]) rotate([0,90,0])
            difference() {
                cylinder(r=knuckle_r, h=slot_len, $fn=32);
                cylinder(r=pin_r+clearance, h=slot_len+1, $fn=32, center=true);
            }
}
```

Both parts share one continuous OpenSCAD file/`union()` for STL export
(a single file can legitimately contain two disconnected-but-interlocked
solids — CGAL reports this as `Simple: yes` with a `Volumes` count that
just reflects two independent closed manifolds, not a defect, the same
"Volumes:2 is normal for a single real object" caveat noted elsewhere in
this skill). Verified independently: A and B never share any solid
volume (confirmed via mesh containment testing, not just "the render
looks right") — an actual positive ~0.4mm radial gap exists everywhere,
matching the coded `clearance`, meaning the two pieces would truly rotate
freely once printed rather than fusing solid. This is this shop's first
genuinely mechanical (not just aesthetic) OpenSCAD design — build and
verify the mechanism ALONE, isolated from whatever product it's going
into, before adding product-specific geometry around it (matching this
skill's long-standing "test the complex cut in isolation first" discipline
from Technique 3's scoop-cut lesson, now applied to a moving mechanism).

## Technique 23 — Physically-computed geometry (not hardcoded angles) for a "unique" design, and how to verify math that isn't visually obvious (2026-08-27)

A digital sundial (displays the hour as dot-matrix digits, lit only when
the real sun aligns with a canted tube drilled through a flat plate) is a
genuinely different design class from everything else in this skill: the
geometry comes from real astronomical trigonometry, not from a hand-tuned
aesthetic curve. Two lessons specific to this class of design:

**Compute the physics as real OpenSCAD functions with named parameters
(latitude, hour), never hardcode pre-computed angles.** This is what
makes the design honestly "gnomon-adjustable" (matching the real
reference product) — changing `latitude` recomputes every tube's aim
correctly, the same "no magic numbers" rule this skill already applies
to physical dimensions, just applied to physics-derived values:

```openscad
function solar_altitude(hour) = asin(cos(latitude) * cos(15 * (hour - 12)));
function sun_dir(hour) = let(alt = solar_altitude(hour), az = solar_azimuth(hour))
    [cos(alt) * sin(az), cos(alt) * cos(az), sin(alt)];
```

**Aim each tube via `hull()` of two points along the computed direction
vector — never `rotate()` to point something at an arbitrary 3D
direction.** This generalizes Technique 9's "hull of two Y-depths" trick
from a fixed axis to a truly arbitrary direction, and sidesteps rotation-
sign risk completely for what would otherwise be one of the hardest
rotate() calls to get right in this entire skill (aiming at a computed,
non-axis-aligned vector):

```openscad
module sun_tube(px, py, dir, tube_r) {
    p0 = [px, py, -2];
    p1 = [px + dir.x*40, py + dir.y*40, -2 + dir.z*40];
    hull() { translate(p0) sphere(r=tube_r); translate(p1) sphere(r=tube_r); }
}
```

**A real coordinate bug caught only by checking the render, not the
math:** `cuboid(anchor=BOTTOM)` already centers X/Y at the origin — adding
an extra `translate([-w/2, -d/2, 0])` on top of that double-shifted the
whole plate, so the digit holes (correctly positioned near world origin)
ended up looking like they were punched near the plate's edge instead of
centered. The math for WHERE to put the holes was right the whole time;
the bug was in the unrelated plate-positioning code. Lesson: when a
render looks wrong, check the simple placement/anchor code before
re-deriving the complex math again.

**A render showing "every hour's holes overlaid at once" looks like a
scattered mess and is NOT a bug** — a static render necessarily shows all
physically-drilled holes for all 7 hours simultaneously (since a render
has no sun to selectively illuminate just one hour's set), so of course
it looks like nothing readable. **The correct verification is to isolate
ONE hour's active subset** (comment out/parametrize to render just that
hour's tubes) and confirm THAT reads as a clean digit — matching this
skill's repeated lesson (Technique 7, 9, 13) that the right verification
method depends on what's actually being checked, not on trusting whatever
the default full render happens to show.

## Technique 24 — Sundial finished: verified solar-azimuth formula, and multi-hour cell layout with numeric collision checking (2026-08-27)

Technique 23 documented the sundial's core physics/aiming approach but the
design itself was never finished/saved before that session ended (a real
instance of the "save as you go" lesson below — the work existed only in
that session's memory). Finished here: `openscad_models/sundial.scad` /
`.stl` — a 248×50×6mm plate, 7 side-by-side cells (hours 9,10,11,12,1,2,3
at latitude 35), each cell a 3×5-dot-matrix digit made of parallel
`sun_tube()` through-holes all aimed at that hour's real sun direction.

**The exact azimuth formula, verified numerically against known sun
positions (not just algebra) before trusting it in OpenSCAD:**

```openscad
function solar_altitude(lat, hour) = asin(cos(lat) * cos(15 * (hour - 12)));
function solar_azimuth(lat, hour) =
    let(H = 15 * (hour - 12), sin_az = -sin(H), cos_az = -sin(lat) * cos(H))
    atan2(sin_az, cos_az);
function sun_dir(lat, hour) =
    let(alt = solar_altitude(lat, hour), az = solar_azimuth(lat, hour))
    [cos(alt) * sin(az), cos(alt) * cos(az), sin(alt)];
```

Verified in Python first, against real known sun positions at latitude 35:
noon → altitude 55° (=90−lat, correct), azimuth 180° (due south, correct);
6am/6pm → altitude ≈0°, azimuth 90°/270° (due east/west, correct). This is
the actual fix for the "azimuth 180-degree bug" the prior session found —
a naive `cos(az) = ...` formula without the `atan2` two-argument form
flips sign ambiguously and puts the sun on the wrong side of the sky at
exactly the kind of moment (which quadrant) that's easy to get backwards
and hard to notice from a render. **Verify solar/astronomical formulas
against known reference positions numerically before trusting them in
geometry** — the same "check the math independently of the render"
discipline as Technique 23, just applied one level earlier (verify the
physics function itself, not just its geometric consequence).

**Multi-cell layout: lay hour-cells out side-by-side in SEPARATE
non-overlapping regions, never let two different hours' tube clusters
share a footprint.** Each hour's tubes are canted at a different angle
(different sun direction), so even though all cells sit on one flat
plate, a shallow-angle hour's tubes drift substantially in X/Y over the
plate's 6mm thickness — real measured drift at this design's shallowest
hours (9am/3pm, ~35° altitude) was **7.3mm horizontal** over just 6mm of
material. Putting every hour in its own dedicated cell (34mm wide here)
with real margin sidesteps the risk of one hour's canted tube drifting
into a neighboring hour's cell and cutting through its dots entirely —
confirmed via numeric check (computing each tube's real x/y at both the
top and bottom face, not just its nominal drill-center position) that
every hour keeps 3.7mm+ clearance to its neighbors' footprints even in
the worst case.

**A dot-matrix digit design should be visually verified in true top-down
orthographic projection, isolated to one hour, before trusting the full
assembly's numeric checks.** Rendering all 7 hours' tubes at once (the
only thing a default render shows) looks like scattered noise — expected
per Technique 23, not a bug. But before spending effort on a full
numeric verification pass, a cheap `--camera=0,0,0,0,0,0,300
--projection=ortho` top-down render of ONE isolated hour's cell
confirmed the digit genuinely reads as "12" (or whichever hour) — catching
a font/layout bug at this stage is far cheaper than finding it only after
a full collision/through-hole verification pass on the whole assembly.

## Standing rule — pitch the concept and get a yes BEFORE modelling anything (2026-08-28)

Scott, verbatim: *"Before you start building another print, I want to know
what it's going to be."*

**Do not open a `.scad` for a NEW design until the concept is approved.**
Pitch first, in a few lines — not a document:

- **What it is**, concretely enough to picture (not "a desk organizer" —
  "a 3-compartment caddy with horizontal corrugated ribs, ~120mm wide").
- **Who buys it**, and why it fits this shop (kawaii/pastel, or the
  functional-print side).
- **Rough size and proportion**, as real numbers — the same
  state-the-ratio discipline as Technique 31.
- **How it prints**: how many parts, what orientation, whether it needs
  supports, roughly how long.
- **Why it's worth making** over the alternatives on the table.

Then wait. A design that gets modelled before the concept is agreed can
be perfectly executed and still be the wrong object — and the modelling
is the expensive part, as this session's twelve-correction cap
demonstrated at length.

**Scope of the rule:** it covers the *concept*, not the *execution*.
Iterating on an already-approved design (fixing a shape, adding the
maker's mark, re-proportioning after feedback) does not need a fresh
approval — that's the work Scott already said yes to. A genuinely new
object does.

**Ideas already on the table**, both from Scott's own reference material
rather than invented (see Technique 29's reference-ideas section for the
full notes): a pleated folding fan with a print-in-place hinge and a
snowflake motif, and a ribbed 3-compartment desk caddy. Pitch from real
candidates like these before reaching for something new.

## Standing rule — one home for every STL, and hand it to Scott (2026-08-28)

**`openscad_models/` in this repo is the single canonical home for every
`.scad` and its exported `.stl`.** Do not scatter finished models into
scratch directories, per-product folders, or Frank's volume as their
primary location. One folder, committed, so the whole set can be pulled
or browsed at
`github.com/printing3dthings-afk/etsy/tree/main/openscad_models`.

**Sessions run in an ephemeral cloud container, not on Scott's machine.**
There is no desktop here, no `~/Desktop`, and nothing written to local
disk survives the container being reclaimed. So "put it on my desktop"
cannot be done literally — say so plainly rather than writing a folder
somewhere that will silently vanish. What actually delivers:

1. Commit the `.scad` and `.stl` to `openscad_models/` (the durable copy).
2. Hand Scott the file itself so it lands on his own machine. **Prefer
   3MF over STL for the file you actually send** (added 2026-09-01):
   `render_scad(src, out.3mf, fmt="3mf")` produces the identical geometry
   at roughly 1/13th the file size on a real comparison (Mushie: 27.3MB
   STL vs. 2.1MB 3MF) and embeds real millimeter units, so Bambu Studio
   can't misread the scale the way it can with a bare STL. Keep the `.stl`
   as the repo's committed analysis copy (`stl_components.py` and every
   numeric verification in this skill reads STL) and export a `.3mf`
   alongside it purely for delivery. A zip of the folder still works when
   Scott wants the whole set.
3. Verify before sending: `unzip -tq` on the archive, and md5 a couple of
   members against the repo originals. An archive that is truncated or
   built from a stale copy looks perfectly fine from the outside.

## Standing rule — save real, finished work immediately, not at the end of a session (2026-08-27)

A previous attempt at this exact sundial design was lost — built,
partially verified, discussed in detail — because nothing was committed
to git or saved to Frank's volume before that session's container ended.
The design existed only in that session's own memory and conversation
history, both of which are gone once the container cycles. This cost
real, duplicated effort: the whole design had to be rebuilt from scratch
using only the technique documentation that happened to survive in this
skill file, and even that reconstruction risked colliding with a
DIFFERENT concurrent session independently rebuilding the same design at
the same time (this genuinely happened — caught only by a screenshot
showing the other session's live progress).

**The fix, now a standing rule for every physical design in this
pipeline:** the moment a design is rendered, verified (numerically, not
just visually), and confirmed correct, save it — `git add`/`commit`/
`push` for the `.scad` source and skill documentation, plus
`POST /api/files/upload` (verified by re-downloading and comparing MD5)
for the `.stl`/`.scad` on Frank's volume — before moving on to the next
piece of work, and regardless of whether the overall task or session
feels "done." Do not batch saves until a natural stopping point; there
often isn't one, and the cost of losing verified work is much higher than
the cost of committing slightly more often than strictly necessary.

**Also check for concurrent work before starting, not just before
finishing.** Multiple sessions can run against this same repo/branch at
once. Before starting a nontrivial physical design, `git fetch` the real
branch tip and check whether the thing about to be built already exists
or is already in progress — a stale local checkout (this session was
once ~30 commits behind `origin` without realizing it) can make finished
work look like a gap that needs re-doing.

## Standing rule — every finished physical design gets an OnBrandCraftz maker's mark, as a negative (engraved) cut (2026-08-27)

Scott's explicit, durable instruction: don't forget to add the OnBrandCraftz
mark, and it must be a NEGATIVE part (an engraved/recessed cut into the
model), never a raised/positive add-on. This reuses the exact
confirmed-correct technique from Technique 4 (verified on a real physical
print) — don't re-derive the mirror axis, don't invent a new placement
convention:

```openscad
logo_depth = 0.7;
module brand_mark() {
    translate([x, y, -0.5])              // pick a flat face, well clear of
        linear_extrude(height = logo_depth + 0.5)   // any functional cut/cavity
            mirror([0, 1, 0])             // REQUIRED for this exact pattern
                text("OnBrandCraftz", size = 5-7, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}
// subtract brand_mark() inside the model's own top-level difference()
```

Checklist before calling any product done:
- [ ] Placed on a flat, hidden-in-normal-use face (a bottom/underside is
      ideal — matches the phone stand and vase precedent) — never on a
      visible/functional surface
- [ ] Positioned with real clearance from every functional cut, cavity, or
      mechanism in the design (verify numerically, not by eye — a mark
      that overlaps a hex cell, a hinge knuckle, or a sun-tube's entry
      point is a real defect, not just cosmetic)
- [ ] Cutter Z-range genuinely dips below the surface (`translate` z<0)
      — the exact off-by-a-hair mistake documented in Technique 4 (a
      cutter touching but not crossing the surface engraves nothing,
      renders clean, reports no error) is easy to reintroduce by copying
      this pattern carelessly
- [ ] Remaining material above/behind the mark is still comfortably solid
      (engrave depth well under the local wall/floor thickness)
- [ ] **`size` is fitted to THIS model's actual available flat area, not
      copied verbatim from a differently-scaled model or from the "5-7"
      example above** (Scott's real feedback, 2026-08-27: the mark on a
      46mm-long cable clip at size=4.5 measured 35.47mm wide — 77% of the
      part's entire length, dominating a face meant to hold a small
      hidden mark). Compute the real footprint from the model's actual
      STL, the same z-range vertex-extraction technique used throughout
      this skill (filter exported vertices to the engraving's z-range and
      the mark's approximate x/y placement, then take max-min), and
      target a width comfortably under half of the available flat run —
      roughly 35-45% is a reasonable default, tighter for a small part.
      **Don't trust a linear projection from a single measured data
      point either** — re-measure after applying a new `size`, since a
      first measurement can itself be an artifact of how it was filtered/
      bounded (confirmed on the cable clip: a naive projection from one
      real 35.47mm-at-size-4.5 measurement predicted ~20mm at size=2.5;
      the real re-measured value was 27.91mm — two DIFFERENT smaller
      sizes then agreed with each other exactly, confirming the original
      widely-scaled measurement was the unreliable one, not the physics).
      This generalizes beyond just the maker's mark: **any parametric
      feature sized by a formula or a fixed constant should be verified
      against the model's own real dimensions after rendering, not
      assumed correct because the number "looks reasonable" or matches
      an earlier model** — a fixed absolute size is only ever right by
      coincidence once the model's own scale changes.
      **A second real trap, found fixing the SAME mark on the sundial
      right after: the z-range vertex filter that isolated the mark
      cleanly on the cable clip does NOT automatically transfer to a
      different model.** The sundial's hour-digit tubes pass near the
      same z-band as the mark's shallow recess, so a naive z-range filter
      counted digit-hole surface points as part of the mark — and the
      giveaway was that the measured "width" came back IDENTICAL
      (212.56mm) at two very different `size` values (5 and 2.4), which
      should have been treated as immediate proof the filter was broken,
      not evidence the font doesn't scale. **A real measurement always
      moves when the parameter driving it moves; if it doesn't, the
      measurement method is wrong, not the model.** The fix that actually
      worked: instead of filtering by a z-RANGE, isolate the mark's
      recess FLOOR specifically — a flat plane at exactly the cutter's
      known overlap depth (here, `z == -2.3` to within float tolerance) —
      then confirm those isolated points cluster tightly at the mark's
      intended x/y placement before trusting the resulting number. A
      z-range filter is a decent first guess for a model with nothing
      else nearby in that band (true for the cable clip); a model with
      other deep/tall features sharing the same z-band (true for the
      sundial's tubes) needs a tighter, feature-specific isolation, not
      the same filter copied over.

This is a standing requirement going forward, not a one-off — apply it to
every new physical product design in this pipeline (SS-Series, 3D-print
functional pieces, decorative pieces), the same way AI-disclosure text is
a standing requirement on every digital listing.

## Technique 25 — A print-in-place hinge+latch box is a genuinely harder verification problem than a bare hinge, and CGAL's Volumes count fails at it repeatedly (2026-08-27)

Building a cable clip (base + hinge + lid + latch — a real functional part,
not decorative) surfaced four distinct, real bugs, three of them never
caught by CGAL's own `Simple: yes` / `Volumes: N` summary at all. This
session's own STL connected-component union-find (already this skill's
established practice from Technique 20) caught the first three; the
fourth needed a stronger test still, described below. Worth internalizing
as a set, since they compound on any print-in-place hinge+latch design,
not just this one part.

**Bug 1 — a latch's intentional interference fit is fatal in the CLOSED
export pose, if base and lid share one `union()`.** A friction latch
(Technique 17's bump/dimple pattern: a sphere fused onto one leaf,
slightly larger than a matching sphere subtracted from the other) needs a
few tenths of a millimeter of real geometric overlap to create the
click/friction — correct for a real, physically-closed, hand-assembled
pair of parts, but fatal for a **print-in-place** single-file export: if
both leaves are exported via one top-level `union()` in the CLOSED pose,
that intentional overlap becomes a permanent structural weld, exactly
like the notch/knuckle bugs below but from the opposite direction (an
overlap that's supposed to exist, not one that was supposed to be
avoided). **The fix, which is also the standard real-world convention for
this exact part class: export the assembly in the OPEN pose.** Rotate
only the lid's entire module about the physical hinge axis (translate the
axis point to origin, `rotate([angle,0,0])` for an axis running along
world X, translate back) before unioning with the fixed base. This is
mechanically sound regardless of `open_angle` for a completely different
reason than "it just avoids the latch": any point that sits exactly ON
the rotation axis is invariant under rotation, and a barrel hinge's
sleeve bore centers are deliberately placed exactly on that axis (Technique
22's own construction) — so rotating the lid never misaligns the hinge
itself, only moves the rest of the leaf's material away from the base.

**Bug 2 — the sleeve's bore cutter must span the SAME (non-centered)
range as the outer knuckle, not a centered range of the same nominal
height.** This is a direct bug in this skill's OWN Technique 22 worked
example, copied faithfully and only caught here: the outer knuckle is
built as `cylinder(r=knuckle_r, h=slot_len)`, spanning local z:[0,
slot_len] — NOT centered. The bore cutter in that same example uses
`center=true`, which spans z:[-slot_len/2, +slot_len/2] — overlapping the
outer's real [0, slot_len] range for only HALF its length. The far half
of the sleeve is left solid, silently blocking the rod. Confirmed by
directly comparing the outer cylinder's declared range against the bore
cutter's actual range as plain numbers (the same discipline Technique 19
already established: don't trust an existing pattern's own comment about
what it does — check the literal ranges). Fix: translate the (still
non-centered) bore cutter to `[-margin, slot_len+margin]` so it fully
spans the outer knuckle with real margin on both ends, matching the exact
non-centered convention the outer cylinder already uses.

**Bug 3 — a box that spans all the way to the hinge axis is invariant
there under ANY rotation, so "cut a clearance notch per slot" is not
sufficient outside the slot band.** A first fix used clearance notches
(cut circular voids into each leaf's box specifically at the OTHER leaf's
knuckle slots) while leaving the box's plain edge running flush to
`y=hinge_y` everywhere else. This looked completely correct in every
render and passed `Simple: yes / Volumes: 2` — but the two leaves' boxes
are `total_len` wide while the actual knuckle band (`hinge_len`) is
narrower, leaving margin at both ends where NEITHER leaf has any notch at
all, and the box still reaches the exact axis line there. Since
`y=hinge_y, z=hinge_z` (for any x) is the rotation axis itself, that
specific line is invariant under `rotate()` regardless of angle — so
base's and lid's edges stay permanently coincident along that whole
margin, for every possible `open_angle`, not just the closed pose. The
"prints already assembled, opens fine" intuition doesn't help here
because the defect isn't in the hinge mechanism at all — it's in the
plain box shape surrounding it. **Never let a leaf's flat, otherwise-
uninvolved geometry reach all the way to a rotation axis it doesn't need
to touch, even outside the region where the actual mechanism lives.**

**Bug 4 (the subtle one) — a UNIFORM inset that clears the OTHER leaf's
knuckle radius also clears your OWN leaf's matching knuckle, since
they're geometrically identical (same radius, same axis).** The fix for
Bug 3 was to inset both boxes uniformly away from the axis by enough to
clear a full knuckle radius (`knuckle_r + clearance`) everywhere. This
correctly stops the boxes from ever touching the OTHER leaf's knuckle —
but a collar and a sleeve share the exact same outer radius and axis by
design (that's what makes them interlock at all), so the same inset that
protects against the other leaf's knuckle ALSO leaves a gap between the
box and this leaf's OWN matching knuckle, which no longer reaches the
box at all. **Verification method that actually caught this, and is now
the recommended check for any print-in-place mechanism going forward:**
render `intersection() { base_part(); <the same transform used in the
real assembly, applied to> lid_part(); }` directly. A correct design
renders this to **"Current top level object is empty"** — any non-empty
result is definitive, exact proof of real geometric overlap, and openscad
prints its actual vertex coordinates so the offending feature can be
identified directly (in this case, the overlap vertices' radius from the
hinge axis matched `knuckle_r` exactly, immediately pointing at the
inset-vs-knuckle mismatch rather than requiring more guessing). This is
stronger than the STL-vertex-distance heuristic used earlier in the same
session, which produced a **false negative** — comparing vertices from
two SEPARATELY-rendered STLs can never see an intersection surface that
only gets computed by CGAL when the two solids are actually unioned
together in one pass; a real overlap between two coarse ($fn=24) curved
surfaces can exist well inside the gap between either mesh's own nearest
vertices. **`intersection()` is a direct, authoritative overlap test;
comparing separately-exported vertex sets is not — use `intersection()`
first for any two parts that are supposed to stay separate.**

**The actual fix, which generalizes to any interlocking two-part
mechanism:** inset BOTH leaves' boxes far enough to clear the FULL
knuckle radius of either type (not favoring "your own" radius), then add
a small explicit "root bridge" — a plain block, NOT part of the box
itself — at ONLY that leaf's own matching slot positions, spanning from
the axis back out past the box's inset edge with real overlap margin.
This root bridge needs its OWN bore cut for the rod, with the identical
margin-based non-centered pattern from Bug 2 — a bridge placed at a
SLEEVE slot must let the (base-owned, continuous) rod pass through it
untouched, exactly like the sleeve itself does; forgetting this bore on
the bridge (even after fixing it on the sleeve) reintroduces the same
class of collision one level up, and this too only showed up under the
`intersection()` test, not under any render or the Volumes count.

## Reference ideas from Scott (2026-08-27) — real Bambu Handy screen recordings

Two real designs Scott found and shared (screen recordings of the Bambu
Handy app's 3D Preview, not text descriptions) — good concrete references
for future builds in the "unique"/"fun" categories:

1. **A pleated/fluted folding fan with a print-in-place hinge along one
   edge and a snowflake motif engraved on the fluted face.** The hinge is
   a row of interleaved round knuckles (same family as Technique 22's
   barrel hinge, likely simpler — a single continuous knuckle strip rather
   than a stepped-shaft+sleeve pair) connecting a fan of fluted/pleated
   panels that spread open. Seasonal (winter/snowflake) decorative angle.
2. **A compact ribbed 3-compartment desk organizer/caddy** with horizontal
   corrugated ridges running around the full exterior (a texture family
   related to Technique 5's flute/rib technique, just wrapped around a
   multi-compartment holder body instead of a single vessel).

Not yet built — recorded here as concrete design references (the same
role reference photos play for the pumpkin/ghost) for when either
category comes up again.

## Technique 26 — Chaining a proven hinge across multiple panels: axis remap, cuboid's silent X/Y centering, and rotate-direction sign errors compound fast (2026-08-27)

Building an accordion-fold pleated fan (3 panels, 2 barrel hinges, chaining
the cable clip's already-debugged hinge mechanism instead of inventing a
new one) surfaced three more real bugs on top of everything already fixed
for the cable clip and bayonet jar — worth internalizing together, since
they compounded: fixing one revealed the next only once it was resolved.

**Bug 1 — a coordinate double-offset when reusing a parameterized hinge
helper across multiple axis positions.** `hinge_root_bridges(hx, ...,
x_lo, x_hi, ...)` wrapped everything in `translate([hx,0,z0])` internally,
but the CALLER passed `x_lo`/`x_hi` as if already-absolute world
coordinates (e.g. `hinge_x[0] - knuckle_r - 1`). The module then added
`hx` a second time, placing every bridge roughly `hx` millimeters away
from where it belonged (confirmed directly: bridges intended near x=45
and x=90 landed at x=175-184 — hx added twice, not a rounding error).
**Fix: make helper parameters consistently RELATIVE to the position the
module itself already translates by** (matching how `hinge_collars()`/
`hinge_sleeves()` in the same file only ever used relative `0` offsets
internally, which is exactly why THEY didn't have this bug and the newer
bridge helper did) — collapsed to a plain `is_left` boolean with two
fixed relative offsets, removing the chance of passing an
already-absolute value by mistake a second time.

**Bug 2 — `cuboid(..., anchor=BOTTOM)` only anchors the axis you name;
every other axis stays centered, silently.** `panel_box(n)` computed an
intended EDGE position (`panel_x0(n)`, `panel_y_lo(n)`) and passed it
straight into `translate()` before a `cuboid(..., anchor=BOTTOM)` —
`anchor=BOTTOM` only pins Z to start at 0; X and Y remain centered on the
cuboid's own local origin regardless. Every panel ended up shifted by
HALF its own width/thickness from where it belonged, causing each panel
to overlap roughly half of its neighbor's intended space. This produced
spectacular, confusing symptoms (24 fragmented STL components, tiny
floating debris cubes visible in the preview render) that looked like
they might be several unrelated bugs — bisecting with `intersection()`
down to "collar cylinder vs panel2's plain box" and computing panel2's
REAL vs. intended Y-range from first principles is what actually
resolved it, not guessing from the STL fragment list alone. **The
general lesson, already true for the cable clip's `base_box()`/
`lid_box()` (which got this right by explicitly computing `depth/2 -
box_depth/2` as the center) but re-broken here on a new model: whenever
a value is meant to be an EDGE of a `cuboid()`/similar primitive, check
whether that primitive centers on the axes you're not explicitly
anchoring, and convert edge-to-center explicitly** (`edge + size/2`) —
never assume a translate lands where a box's corner should be just
because that's what was intended.

**Bug 3 — `rotate([90,0,0])` sends an extrusion in ONE specific
direction; a second use of the identical rotate on a differently-facing
surface needs the opposite sign, and this is NOT visually obvious from a
render.** Two engraved marks on this same model both used
`rotate([90,0,0])` after a `linear_extrude()`, matching Technique 4's
established bottom-face pattern superficially — but one mark (the
snowflake, cut from a panel's FAR/outer surface) worked correctly, while
the other (the brand mark, cut from a panel's NEAR/inner surface, same Y
side of the same panel type) engraved nothing at all: zero recess-floor
vertices found anywhere, confirmed by the same numeric floor-isolation
check this skill already established. The fix wasn't a mirror axis this
time (Technique 4's territory) — it was the ROTATION SIGN, which needed
to flip because the two marks approach their respective surfaces from
opposite directions even though both cuts are described by the "same"
`rotate([90,0,0])` pattern. **A rotate that's correct for cutting into
one face is not automatically correct for cutting into a different,
non-parallel or oppositely-approached face, even using the identical
euler angles — verify each new engraving placement's OWN cut direction
numerically (does the recess floor exist, at the expected depth, inside
real material?) rather than assuming a working pattern transfers by
visual analogy.**

**The meta-lesson tying all three together:** reusing a proven mechanism
(the hinge) was the right call and avoided re-deriving new mechanical
risk from scratch — but the ADAPTATION work (remapping axes, wiring the
helper into a new geometry, placing new decorative cuts) introduced
three fresh, unrelated bugs of its own. "Reuse what's proven" reduces
mechanism risk; it does not remove the need to verify the NEW plumbing
around it with the same rigor (`intersection()` tests, connected-
component counts, recess-floor isolation) applied to a brand-new design.

## Technique 27 — Mochi Fox desk organizer (character piece + functional cavities)

2026-08-27, built as a deliberate "best effort" flagship piece: a seated
chibi fox (hulled-sphere body/head/snout, tapered hull-chain tail, cone
ears) with a pen cup and shallow dish cut into its back, fitted brand
mark on the base. Four real findings, one of them a mid-build feature
cut, not a bug fix.

**Finding 1 — a font referenced by name for months was never a real
font file.** `fonts/DancingScript-Bold.ttf` is a saved GitHub HTML page
(`file` reports "HTML document", not TrueType) and was never registered
with fontconfig regardless (`fc-list | grep -i dancing` returns nothing).
Every prior brand mark in this shop's OpenSCAD history requesting
`font="Dancing Script:style=Bold"` silently fell back to OpenSCAD's
default font — `text()` never errors on an unresolvable font name, it
just substitutes, so this went undetected across every design built so
far. **Verify a font actually resolves (`file` on the path, `fc-scan`
after registering) before trusting any `text()` render — a font name
that "looks right" in the source is not evidence it rendered.**
`assets/fonts/Caveat-Bold.ttf` is a real TTF; copying it to `~/.fonts`
and running `fc-cache -f ~/.fonts` makes `font="Caveat:style=Bold"`
resolve cleanly, confirmed via `fc-scan` before use.

**Finding 2 — an analytic surface-height function is far more reliable
than guessing a Z coordinate, but only for the ONE primitive it actually
models.** `body_top_z(x,y)` solves the body ellipsoid's own top surface
in closed form and made the pen-cup/dish cavity placement trivially
correct on the first real attempt (previous designs guessed absolute Z
values by eye and got them wrong — see Technique 25/26). But the same
function is blind to anything unioned on TOP of that ellipsoid: a
belly-hatch mount placed at a point the formula called "safe" still
collided with the head and ears, because `body_top_z()` only ever knew
about `body_shape()`, never `head_shape()`/`ear()`. **An analytic
placement helper is only as complete as the geometry it models — verify
new placements against `intersection()` with the ACTUAL neighboring
features, not just the one primitive a formula covers.** Also: a first
pen-cup draft used `pen_r=17, pen_depth=44` on a body whose own radius
is 30 — a cutter comparable to the whole body's diameter, confirmed
blowing out the top and toward the head in a real back-top render before
being scaled down to a real pen-cup proportion (`pen_r=9, depth=20`).

**Finding 3 — a proven mechanism can pass every interference test and
still be the wrong call, and only a render catches that.** A small
bayonet-lock stash hatch (reusing bayonet_jar.scad's exact mechanism)
was built into this fox's belly/hip and went through three real,
sequential bugs before it mechanically worked: (a) the lock slots/pins
were placed at an inner bore radius while the door's skirt was sized to
clear that same inner number, instead of the boss's real OUTER radius —
a large, unmissable overlap once tested, fixed by putting both
consistently at `boss_r`; (b) the door's hollow "ring" section was only
tall enough to cover the pin's travel distance, not to actually clear
past the boss's own top face, so the door's solid cap started
UNDERNEATH the boss — found by testing the boss+socket+door in total
isolation (`intersection()` with nothing else in the scene) and reading
off exactly which native-Z band was involved; (c) the chosen mount
position, picked to be "safe" from an incomplete geometry model (see
Finding 2), needed the boss pushed taller and taller (5mm proud → 16mm)
to clear a persistent residual overlap that turned out to be the EAR,
not the body surface. At proud=16 every mechanical test passed clean —
and the hero render showed a tall spike poking out of the fox's
shoulder, an obvious look-and-feel defect no interference test could
ever flag, because "does it overlap" and "does it look right" are
different questions. **The fix here wasn't a smaller bug fix — it was
cutting the feature.** This body (~30mm radius) was already carrying a
head, two ears, a tail, and two cavities; a systematic obstacle-clearance
search (real Python distance checks against every existing feature, not
eyeballing) came back with zero fully-clear positions large enough for
the mechanism, and the "best available" spots all needed enough proud
height to create the same visual problem. **Passing every mechanical
check is necessary, not sufficient — render and actually look before
calling a feature done, and be willing to drop a feature entirely when a
crowded host shape can't fit it without compromising the silhouette,**
rather than continuing to chase the interference test to zero on a
position that was never going to look right.

**Finding 4 — a CLI flag immediately followed by the input filename can
silently swallow that filename as its own argument.** `openscad -o
out.stl --render model.scad` fails with a bare usage dump — this
OpenSCAD build's `--render` takes an optional argument, and with nothing
else after it, `model.scad` gets consumed as `--render`'s value, leaving
no positional file argument at all. Every working `--render` call this
session had `--camera=...` or another flag after it, which never
triggered this. Fix: `--render=true` explicitly, or put `--render`
somewhere `--camera`/`--imgsize` follows it, not immediately before the
filename.

## Technique 28 — Mochi Fox v2: real reference photos, and a cut buried entirely inside the solid

2026-08-27, same session as Technique 27, reworked after real feedback
("the detail is not there, I can't tell what it is"). Two changes, one
new and important bug class.

**Fetch and actually view a real reference photo before styling a
character piece — don't work from memory of what an animal "generally"
looks like.** `curl`-ing a real red fox photo (Wikimedia Commons —
`upload.wikimedia.org` rate-limits aggressively without a real
User-Agent and via bare filenames; `commons.wikimedia.org/wiki/
Special:FilePath/<title>.jpg` redirects reliably and dodges both) and
viewing it directly showed the v1 head (two hulled spheres — a big
skull ball with a small snout ball stuck on front) reads as a generic
round animal, not a fox. A real fox head is a continuous WEDGE: wide at
the cheek/ruff, tapering the whole way to a narrow, distinctly elongated
muzzle. Rebuilt as a hull-CHAIN (same technique as this file's tail) of
5-6 spheres shrinking from skull to nose tip — smooth (hull has no
seams) and unmistakably fox-shaped, confirmed by direct visual
comparison against the reference photo, not by assuming a "kawaii
fox" prompt-description was enough on its own.

**A shallow flat-bottomed cut can end up ENTIRELY BURIED inside a solid
without ever reaching the surface — and the symptom looks exactly like
a floating disconnected fragment, not an obviously-missing recess.**
After moving the eyes onto what looked like the head chain's widest
point, `stl_components.py`'s union-find reported a real disconnected
component whose bounding box was an EXACT match for the eye cutting
tool's own dimensions. The reflex reading of that ("recess merged
strangely with the surface, maybe a CGAL sliver") was wrong. The actual
cause, confirmed with `intersection(head_shape(), eye())`: the cutting
tool's ENTIRE volume was inside real material, none of it reaching open
air — subtracting it just hollowed out a sealed internal bubble, and a
bubble's own inner shell is topologically a separate component from the
outer shell, which is exactly what the connectivity checker reported.
**When a connected-component check reports a fragment whose bounding
box matches a cutting tool's own dimensions almost exactly, suspect a
fully-buried cut before suspecting a boolean/precision bug** —
`intersection(host_shape(), the_cutting_tool())` on the plain host alone
answers it directly (full tool bounding box back out = buried; a
partial/clipped shape = the cut is actually reaching the surface).

**Root cause of *why* it was buried:** `hull()` between two spheres
offset in BOTH Y and Z (this head chain drops in Z while advancing in Y,
following a real snout's downward taper) bulges its blended "roof"
surface — the side staying closer to the taller sphere's own Z — much
farther forward in Y than either control point's own Y coordinate
suggests. Guessing a cut position from a control point's (x,y,z,r)
tuple assumes the local cross-section is close to that one sphere;
for a hull segment sloping in more than one axis, it can be very wrong.
**Measure the real surface instead of estimating it**: export the host
shape alone, then for the intended cut's (x,z) window, find the actual
maximum Y among vertices in that window (`v[1]` in a filtered vertex
scan) and place the cut relative to that measured number, not the
nearest control point's coordinates. Every position in the corrected
version came from exactly this kind of direct measurement.

**Isolate a visible defect by disabling one cut at a time, not by
guessing which one from the picture.** A separate real defect (a large
jagged tear visible in a hero-angle render) turned out to be the chest
"dish" cavity, not the eyes — found by copying the file, commenting out
each `difference()` child one at a time (`// pen_cavity();`, etc.), and
re-rendering the identical camera angle after each change until the
tear disappeared and reappeared with a single specific cut. The dish sat
right at the seam where `head_shape()` and `body_shape()` overlap and
union together — not a simple sphere surface the way `body_top_z()`
assumes, so the analytic-placement technique from Technique 27 doesn't
cover it. Cut the feature (same call as the stash hatch in Technique
27) rather than chase an exact-fit position on a union seam that isn't
analytically tractable the same way a single primitive's surface is.

**Iterate at low `$fn`, finalize at high `$fn` — don't debug at
production resolution.** Raising `$fn` from the 24-64 range to 96 for
visible smoothness (a real, valid complaint — the v1 renders were
noticeably faceted) turned a ~25-30s full `--render` into ~7 minutes.
Every fix in this technique was found and verified against a `$fn=32`
copy of the same file (`sed` one line to override the global `$fn`) in
under 35 seconds per iteration, then re-verified once at the real `$fn`
only at the end. Debugging placement/connectivity bugs at full print
resolution wastes minutes per iteration for zero additional diagnostic
value — the geometry topology being tested doesn't depend on facet count.

## Technique 29 — A proven mechanism (bayonet lock) reused deliberately, and a real mechanism taxonomy from 200-print visual research (2026-08-28)

Building "Mushie" (a two-part mushroom night light around the real Bambu
Lab LED Lamp Kit-001 hardware — a D59×H18mm disc puck), Scott asked for
the cap to lock onto the stem "like the container you made," pointing
directly at `openscad_models/bayonet_jar.scad`'s existing push-down-then-
twist bayonet lock rather than asking for a new mechanism invented from
scratch. **Reused, not reinvented:** `bayonet_jar.scad`'s `one_slot()` /
`lid_pins()` pattern (a vertical entry cube + a `rotate_extrude(angle=)`
horizontal lock channel on the stem side, matched by pin spheres on the
cap positioned at `entry_angle + lock_angle` so the default render already
shows the LOCKED pose) was copied onto the mushroom lamp's stem collar /
cap skirt almost verbatim — same `n_pins`, same `angle_margin` margin
past `lock_angle` to fully clear the pin's own angular footprint, same
two-check verification (an `intersection()` against the solid stem must
be EMPTY; an `intersection()` against the slot's own cut volume must be
NON-EMPTY). **The one new risk a direct copy doesn't catch for free:**
the new lock channel's Z-height and the collar_slots' default angular
offsets can silently collide with an unrelated pre-existing cut on the
same part (here, `cable_notch()`, added earlier in the same file for the
LED puck's power cable) — caught by reasoning about both cuts' Z-ranges
and angles BEFORE rendering (moved `cable_notch` lower, offset
`collar_slots()` by +60° off the notch's own axis), not by a failed
render. **Lesson: adapting a proven mechanism from elsewhere in this
shop's own model library is the right default over inventing a new one**
— but still re-derive every dimension against the NEW part's own other
cuts, don't just paste coordinates from the source file.

Scott also asked to keep deepening real design understanding via broader
visual research (200 more real reference prints, following up on an
earlier 100-print MakerWorld-adjacent benchmarking pass — see Technique
21 above). That research (full log: session scratchpad
`research200/notes.md`) surfaced a genuine, reusable **four-way printable
mechanism taxonomy**, built from real photos across lamps, planters/
vases, hinges/locks, kawaii figures, and phone stands — worth checking
any new mechanical design idea against before modeling starts, the same
way Mushie's own lock was scoped directly against `bayonet_jar.scad`:

1. **Interleaved-knuckle hinge** (e.g. MyMiniFactory 3552) — two flat
   plates end in alternating cylindrical knuckle segments around one
   shared pivot axis. Moving surfaces touch **during printing itself**,
   with a designed clearance gap — the print head can't assemble this
   after the fact, so the gap has to be baked into one STL from the
   start. One fixed rotation axis only.
2. **Bayonet / multi-start-thread quick-lock** (this shop's own
   `bayonet_jar.scad` and Mushie; real precedent in a 4-start "quarter-
   turn" threaded storage-jar lid, MyMiniFactory 96731) — moving surfaces
   only touch **after a manual assembly step**, so each part can be a
   separate STL with zero print-time clearance concerns. Built for
   infrequent, fast lock/unlock. Bayonet = simple `rotate_extrude(angle=)`
   arc, no true helix math; multi-start thread = stronger, fully
   circumferential engagement, but needs real helical sweep geometry.
   Both beat a realistic FINE machine-screw thread on FDM, which is a
   known pain point (confirmed twice independently — a threaded-jar
   listing's own instructions say to "screw it back and forth to grind
   the thread in").
3. **Ball-chain print-in-place joint** (MyMiniFactory 471925, a kawaii
   flexi octopus) — like the hinge, surfaces touch DURING printing, but
   chains many small ball-and-socket joints in series (each joint a
   small-diameter self-supporting dome, safe under normal FDM overhang
   limits — the same "small radius = safe overhang" principle as this
   skill's own dome/skirt work, just applied to a bead chain instead of
   one big shell) for continuous multi-axis flex instead of one fixed
   axis.
4. **Coarse acme leadscrew** (MyMiniFactory 152514) — a thick, square-cut
   screw thread (deliberately much coarser pitch than a real machine
   screw) turned by hand for TRUE continuous, infinite-position
   adjustment; the thread's own friction self-locks any chosen position
   with no separate latch. The only one of the four giving continuous
   rather than discrete positioning.

Two more standalone reusable findings from the same research, outside the
mechanism taxonomy: **a rolled/curled 2D profile (a scroll cross-section,
extruded straight) is both structurally stronger than a flat sheet of the
same thickness AND can supply its own foot/stand geometry for free** —
the curl's own lowest point becomes the ground contact, no separate leg
needed, and the curl's own tangent angle never overhangs unsafely (real
example: MyMiniFactory 122279's phone stand). And **a diffusion strategy
for a lit/lamp shell should be picked deliberately, not defaulted to
discrete holes** — three real lamps used three different approaches for
three different aesthetic goals: sparse discrete holes for localized
accent spots (Mushie's own spore-pattern dots), a lithophane relief shell
on a gently curved surface for a genuine photographic image, and a full
Voronoi/organic lattice mesh (no large solid faces anywhere) for uniform
ambient glow with zero hot spots.

## Technique 30 — Continuous-curvature (G2) surfacing: the real, provable difference between "blocky CAD" and "professionally designed" (2026-08-28)

Scott's feedback, stated directly: prints look too blocky, not enough
"real" designer look, wants genuine depth here rather than incremental
polish. Researched what actually separates amateur-looking CAD from
professional product design (Dieter Rams's principles, real industrial-
design surfacing theory), and the single most concrete, provable,
directly-actionable finding is about **edge continuity class**, not a
vague aesthetic instinct:

- **G0 (positional)** — two surfaces just touch. A flat top meeting a
  vertical wall at a sharp corner. Reads as raw/unfinished.
- **G1 (tangent)** — the surfaces touch and share a tangent direction at
  the join — this is what `cyl(rounding=)` / `cuboid(rounding=)` give
  you: a plain circular-arc fillet. It's smooth in the sense of "no
  crease," but the *curvature* still jumps abruptly at both ends of the
  fillet (flat → suddenly curved → suddenly flat again).
- **G2 (curvature-continuous)** — curvature itself also matches at the
  join, no jump anywhere. This is the one that actually reads as
  "premium": light striking a G1 fillet shows **two** distinct highlight
  lines (one at each tangent-departure point, where curvature jumps);
  light striking a G2 blend shows **one** soft highlight that migrates
  smoothly across the whole surface as the viewing angle changes — the
  same reason a bar of soap or an Apple product edge reads as "flows,"
  while a cuboid with a filleted corner reads as "a box with the corners
  knocked off," even at an identical corner radius.

**Every design this shop has built so far uses G1 fillets exclusively**
(`cyl()`/`cuboid()`'s `rounding=`) — this is very likely the single
biggest concrete contributor to the "blocky" complaint, not proportion or
color or texture. The fix isn't a new tool to install — **BOSL2 (already
vendored) has real G2 continuous-curvature primitives that have gone
unused this entire time:**

- **`rounded_prism(bottom, height=, joint_top=, joint_bot=, joint_sides=, k=)`**
  — builds a whole 3D prism with true Bezier-based continuous-curvature
  rounding on the top edges, bottom edges, AND vertical side edges *at
  once*, from one call. `k` (default 0.5) controls how gradual the
  transition is; BOSL2's own docs are explicit that `k=0.92` merely
  *approximates* a circle and **shows visible seams** where it does —
  i.e. even this tool can accidentally degrade back to a G1-looking
  result if `k` is pushed too high. Keep `k` around 0.3–0.6 for a
  genuinely soft result.
- **`squircle(size, squareness=, style="superellipse")`** — a 2D
  superellipse/Fernández-Guasti corner shape (the literal iOS-icon corner
  language), continuously-varying curvature all the way around instead
  of "flat edge → sudden constant-radius arc → flat edge." Use as a
  footprint for `linear_extrude()` or as the polygon fed into
  `rounded_prism()`.
- **`offset_sweep(path, height=, top=os_teardrop(r=), bottom=os_circle(r=))`**
  — for an edge that also needs to stay 3D-printable: `os_teardrop()` is
  a circular arc for the first ~45° then a straight 45° chamfer for the
  rest, so a rounded top edge **never exceeds a safe overhang angle** no
  matter how generous the radius, while a plain large `rounding=` fillet
  on the same edge either needs supports past ~45-55° or — confirmed by
  direct render comparison — silently consumes the entire flat top into
  a dome, losing whatever flat functional surface was supposed to be
  there. `os_smooth()` is the plain G2 profile (no chamfer) for an edge
  that isn't overhang-constrained.

**Verified empirically before writing this down, not asserted from
theory** (three real side-by-side renders, same session):
1. A `cuboid(rounding=14, edges="Z")` rounded rectangle (this shop's
   own base-plate pattern, used on Cloudy and others) next to a
   `rounded_prism()` version at the same nominal footprint/height — the
   `cuboid` version shows an unmistakable hard edge line where the flat
   top meets the rounded sides; the `rounded_prism()` version shows zero
   seam anywhere, reading as one continuously flowing surface.
2. The same `rounded_prism()` technique hollowed into a real functional
   shell (`difference()` of a bigger and smaller `rounded_prism()`, same
   "outer minus independently-dimensioned inner" principle as this
   shop's existing vessel technique) renders clean (`Simple: yes`,
   `Volumes: 2`) and looks like a real ceramic/soap-dish tray, not a
   Tupperware container — confirming this generalizes to functional
   hollow parts, not just solid decorative blocks.
3. A plain `rounding2=9` fillet on a cylinder's top edge vs.
   `os_teardrop(r=9)` at the same nominal radius — the plain fillet
   consumes the ENTIRE flat top into a rounded dome (and passes through
   a real unsafe-overhang region on the way there); the teardrop version
   keeps a proper flat top intact with a soft, safe, supports-free
   rounded edge around it. This is the both-functional-and-practical
   case Scott asked for specifically — the "professional" choice here is
   also the more printable one, not a tradeoff against it.

**When to use which, concretely:**
- Any primarily-*visible*, hero-angle surface on a decorative or
  semi-decorative piece (a base plate, an organizer's outer shell, a
  lamp's dome/skirt, a stand's body) → `rounded_prism()` or
  `offset_sweep()`+`os_smooth()`/`os_teardrop()`, not `cyl()`/`cuboid()`'s
  plain `rounding=`, as the new default first choice.
- A genuinely hidden or purely mechanical edge (inside a cavity no one
  sees, a hinge knuckle, a bore for a fastener) → the plain G1
  `rounding=` is still completely fine — spending Bezier-patch complexity
  on a surface nobody will ever look at or photograph is wasted effort,
  not "more professional."
- A shape that's **already rounded, or has many points** (a
  `smooth_path()`-derived organic silhouette, a many-sided polygon) →
  BOSL2's own docs warn `rounded_prism()` is not well suited here —
  further rounding an already-curved input generates tiny interfering
  Bezier patches and risks an invalid polyhedron. Reach for
  `offset_sweep()` on the primary profile itself instead, or accept the
  existing organic curvature as already doing the job G2 rounding would
  do on a sharp-cornered primitive.
- A top edge with a real overhang constraint (has to print supports-free,
  or must keep a genuine flat functional face) → `os_teardrop()`, not a
  plain large `rounding=`/`joint_top=` value — verify the specific
  radius doesn't consume the flat face the same way this technique's own
  test #3 did, by checking the numbers (fillet radius vs. remaining flat
  width), not by eye.

## Technique 31 — Silhouette-first design judgment: what to decide before modeling, not after (2026-08-28)

Surfacing technique (Technique 30) is necessary but not sufficient — a
G2-rounded box is still just a rounded box. The other half of "looks
designed, not blocky" is a set of judgment calls that have to happen
**before** the first `cuboid()`/`sphere()` is typed, grounded in Dieter
Rams's "less, but better" framing (aesthetic quality isn't a coat of
paint applied at the end — it's integral to how the form is conceived) —
concrete, checkable questions, not a vague "make it nicer" pass:

1. **Decide the hero angle first, model toward it second.** Every piece
   in this shop's history so far has been modeled primitive-by-primitive
   (base, then body, then features) with the eventual photograph/render
   angle decided only once it's time to verify. Real product design
   works backwards from a primary viewing angle — decide up front
   whether this piece is meant to be seen from a 3/4 desk-level angle, a
   straight-on shelf view, or held in-hand, and let that decide which
   silhouette lines actually matter (the profile that reads at the hero
   angle) versus which are structural-only and don't need aesthetic
   investment.
2. **Silhouette test.** Render the piece as a flat black silhouette
   (a single un-lit color against a plain background, or just squint at
   a normal render) at the intended hero angle. A silhouette that's
   mostly a rectangle-with-rounded-corners reads as blocky regardless of
   how good the surfacing is — a genuinely interesting silhouette has
   at least one deliberate asymmetry, taper, or proportion break (the
   mushroom lamp's flared cap vs. its narrow stem is a real example
   already in this shop's own work; Cloudy's five-lobe cloud silhouette
   is another). If the silhouette alone is a plain primitive outline,
   the surfacing pass won't save it.
3. **Proportion, stated as a number, not eyeballed.** Pick and write
   down an actual ratio between a piece's dominant dimensions (e.g. a
   1:1.6-ish "golden-ish" ratio between a base's width and height reads
   more intentional than a round-number 1:1 or 1:2 chosen because it was
   convenient) before finalizing sizes — matches this skill's existing
   "no magic numbers, name every dimension" rule, just applied to the
   *relationships between* dimensions, not just the dimensions
   themselves.
4. **Count the negative space, don't just fill it.** A design that packs
   every available surface with texture/holes/features (this shop's own
   early tendency — see the honeycomb/lattice techniques) reads as busy;
   a design that leaves deliberate plain, unbroken surface between
   features reads as considered. When adding a decorative feature, ask
   whether the surface AROUND it is also doing something (framing it,
   giving it room) or just incidentally left over.
5. **One "hero" material/color moment, not several competing ones.**
   Where a design has 2+ colors or textures available (AMS multi-color,
   a texture-vs-smooth split like the planter research in Technique 29's
   own batch findings), let ONE of them carry the visual interest and
   keep the rest quiet/supporting, rather than treating every added
   color or texture as equally important — the same "restraint" Rams's
   principles emphasize directly ("less, but better").

These are judgment calls, not a mechanical checklist to satisfy — but
they're concrete enough to actually apply before modeling starts, the
same way this skill's own mechanism taxonomy (Technique 29) gets checked
against a new mechanical design before code gets written. Pair this with
Technique 30's surfacing tools for the execution, and with real reference
photos (this skill's established discipline, Technique 20/21) whenever a
design category is unfamiliar enough that these judgment calls need
grounding in a real example rather than instinct alone.

## Technique 32 — Decoupling a mechanical clearance from the visible silhouette (and a camera-angle trap that hid the real fix from view) (2026-08-28)

Mushie's cap flare (Technique 29's bayonet cap) needed a second real pass:
Scott marked up a render directly, circling a genuinely flat, near-vertical
band sitting right under the dome before the flare opened out — "It's
still to dramatic of a hard slope. It's not like a mushroom."

**The wrong assumption that cost the most time: that the flat band was a
curve-family problem.** The band existed because the bayonet pin (a small
sphere on the cap, meant to fuse into the cap's own skirt wall) only
overlaps that wall when the wall's OUTER radius at the pin's exact height
stays under a hard bound (`collar_r + wall_t + pin_r`) — and the dome's
own geometry fixes the flare's starting radius so close to that bound
that any curve satisfying it has to grow very slowly for a real stretch
right at the start. Three different curve families were tried against
this same constraint — plain `t^2`, `t^4`, and a literal quarter-ellipse
(chosen specifically to match the dome's own spherical family — flat
tangent at the join, steep at the rim) — and **all three rendered as
visually the same flat-drum silhouette**, confirmed by directly
differentiating each formula: every one of them has `dr/dt=0` at `t=0`
by construction (a power `t^p` for `p>1`, and the ellipse, both hit zero
slope at their start on purpose). The exponent never mattered; the
zero-slope start was the actual defect, and it was shared by every
curve tried up to that point.

**The real fix: stop making the OUTER (visible) surface responsible for
the pin's mechanical clearance at all.** Give the pin its own small
support POST — a plain radial cylinder from inside the pin sphere out to
a fixed depth safely inside the shell's wall thickness (verified to stay
below the curve's own hard-minimum radius everywhere, so it can never
poke through the visible surface) — and let the outer curve be picked
for looks alone. Once mechanical and visual concerns are cleanly
separated like this, the actual visual fix was simple: use a curve with
a real, nonzero initial slope (a linear/quadratic blend), so the surface
visibly leans outward starting immediately at the join, rather than
forcing a flat-tangent match with the dome that a viewer reads as "still
vertical." This is a generalizable move, not a one-off: whenever a
mechanical feature (a lock pin, a boss, a magnet pocket) forces an
unwanted constraint onto a visible surface, check whether the feature can
get its own small dedicated connector instead of bending the whole
surface's shape around it.

**A second, purely-verification lesson from the same session, worth its
own warning: a near-top-down camera angle can hide a real curvature fix
from your own eyes.** After the post/curve fix, three separate renders
(all genuinely different geometry, confirmed by different STL md5sums)
looked visually IDENTICAL at `--camera=...,80,0,...` (rotate-X=80°, i.e.
almost bird's-eye) — a flared/tapered profile is foreshortened hardest
from nearly directly above, so a real change in how fast a cone opens up
can be almost invisible from that angle. Switching to a level product-
shot angle (rotate-X≈65°, closer to how the piece would actually be
photographed) immediately revealed the fix was working — the same
geometry that looked like an unchanged flat drum from 80° read as an
obviously continuous, gently bulging mushroom cap from 65°. When a
render doesn't seem to reflect an edit you're sure you made, checking the
camera angle is a real, non-obvious debugging step, not "recheck it just
in case" — verify with a level, close-to-final-presentation angle before
trusting what a render appears to show, and when in doubt, extract the
raw 2D profile curve directly (`echo()` the control points, or plot the
polygon flat with reference lines) rather than trying to eyeball a subtle
curvature difference off a small 3D render.

## Technique 33 — A crease at a SEAM cannot be fixed by tuning either surface; and never read an STL a render is still writing (2026-08-28)

Direct follow-up to Technique 32, and the correction that finally landed.
Twelve consecutive attempts at Mushie's cap treated "it doesn't look like
a mushroom" as a curve-shape problem and re-tuned the flare profile —
`t^2`, `t^4`, a quarter-ellipse, a linear/quadratic blend, each verified,
rendered, and rejected. **All twelve were fixing the wrong object.** The
cap was a spherical DOME `union()`ed onto a separately-profiled SKIRT.
Two surfaces meeting at one radius with mismatched tangents leave a
shoulder crease that is not present in *either* profile — it exists only
at the seam between them — so no achievable change to either curve could
ever have removed it.

**The generalizable rule: when a visual defect sits exactly where two
primitives meet, stop tuning the primitives.** Check first whether the
feature can be ONE surface instead of two. Rebuilt as a single ellipsoid
from apex to rim, the crease was gone on the first render, and the shape
was better for a second reason — "nearly flat near the apex, tangent
going vertical at the rim" (what the reference photos show, and what every
power curve had been hand-fitting toward) is literally an ellipse's own
behaviour, available for free by using one. The same file's stem had the
identical disease (three stacked `cyl()` primitives) and got the identical
fix. This is the same lesson as Technique 12's stacked-segment stem, but
stronger: there, the seams were visible as seams; here the seam read as a
*shape* problem and sent twelve rounds of work to the wrong place.

**A mechanical constraint that distorts a visible surface belongs on a
hidden part instead.** The bayonet pins had forced the cap's outer radius
into a narrow band (Technique 32's postmortem). Moving the whole mechanism
onto an internal cylindrical SLEEVE at a fixed radius — invisible from
outside, printing from the same bed as the rest — retired that constraint
permanently and let the outer surface be judged on looks alone. Bonus: the
annulus between sleeve and shell is exactly where a real mushroom's gills
go, so the decorative gills double as the ribs tying sleeve to shell, and
one feature paid for two.

**Two verification traps hit in the same session, both worth guarding:**

1. **Never read an exported STL while the render that writes it is still
   running.** A connectivity check on a half-written file reported *12
   connected components* — 2 real parts plus 10 convincing "floating
   fragments" whose bounding boxes matched the wart spheres almost
   exactly. That is an extremely persuasive false positive: it looks
   precisely like the real, documented floating-geometry bug class
   (Technique 6, 20, 28), and it burned three separate isolation renders
   and two numeric sweeps chasing a defect that did not exist. The
   completed file was 2 clean components. **Gate the check on the process
   actually having exited, not on the file merely existing** — and treat a
   fragment count that changes between runs of the same file as evidence
   of a truncated read, not of nondeterministic geometry.
2. **An overhang check must exclude geometry that sits inside another
   solid.** The rebuilt stem's steepest segment measured 76° — apparently
   a hard fail against the 55° limit — but it sat at z=2.7, entirely
   inside the base plate, with solid material beneath it. Above the plate
   the true worst was 53.1°. Filter the profile to the part that is
   actually a free surface before judging printability, or a supported
   fillet will read as an unprintable overhang.

**And a real bug the same pass exposed, unrelated to looks: the stem had
never been printable.** Its neck flared r=15 → 39.5 over 14mm — a
60.3-degree outward wall, well past the P1S's 55-degree limit — and no
prior session had checked, because every check had been about connectivity
and interference, never about wall angle. **Add the overhang sweep to the
standard pass for any revolved or lofted profile**, not just to designs
that look risky; it is three lines of arithmetic over the control points
and it caught a defect that had survived a dozen rounds of review.

## Technique 34 — Rebuilding one part silently breaks features on the OTHER part; and a service route must admit the biggest thing that travels it (2026-08-28)

Two findings from adding real cable routing to Mushie, both generalizable
beyond this model.

**A rebuild invalidates features on parts you did not touch.** Mushie's
`cable_notch()` cut an exit slot through the stem's collar wall, and had
been correct for a year of iterations. Rebuilding the CAP (Technique 33)
put a new internal sleeve at bore 40.1 directly around the collar's 39.5
outer radius, across exactly the height band the notch exits at — so the
cable now had nowhere to go, blocked by solid cap material. Nothing
errored. Connectivity was clean, the interference check passed (the notch
is a void, not a solid), and every render looked right, because a blocked
*service route* is invisible to every check this skill had been running.
**After redesigning any part of a multi-part assembly, re-check every
feature on the other parts whose correctness depended on the old
geometry** — especially voids, clearances and routes, which no
solid-vs-solid interference test can see. A cheap, direct test:
render the route's own cut geometry alone and confirm it is ONE connected
component whose bounding box reaches both endpoints it is supposed to
connect (here: up into the puck cavity, and out past the base's rim).
That catches a severed or blocked route immediately.

**Size a service route for the largest object that must travel it, not
for the thing that ends up living in it.** The obvious sizing input is the
cable's ~3.5mm diameter; the binding one is the USB-A plug on its end
(12 × 4.5mm), because the cable is captive to the LED puck, so the plug
has to pass through the entire route during assembly. A channel sized to
the wire renders beautifully and is physically impossible to thread. The
same reasoning applies to any route a connector, knot, strain relief or
fastener head has to pass. Where a route genuinely cannot be widened,
the alternative is to make it OPEN along its length (a groove rather than
a tunnel) so the part can be laid in sideways instead of threaded — which
is also what lets the base groove here double as the flush wire seat.

**Addendum (2026-09-01): this rule bit the exact same model a second
time, because "the largest object" was still guessed rather than
measured.** The route was widened to 13mm for the USB-A plug and that felt
like the answer. It was not: the kit's inline on/off switch is moulded onto
the same captive cord, Scott measured it at **21mm across**, and it has to
make the identical trip. So the honest procedure is not "size it for the
plug" — it is **enumerate every object permanently attached to the cord and
take the max**: connector, inline switch, strain relief, moulded ferrite,
knot. Ask for the measurement rather than inferring it from a product
photo. And when only one dimension of the route needs to grow that far,
grow it *locally*: here the vertical channel went to 23mm and the base
groove stayed at wire width (13mm), with a short 23mm drop-out box only
where the channel meets the underside — so the switch leaves the lamp
straight downward at the centre, the wire is laid into the narrow groove
from below afterwards, and the base's underside never has to bridge a
23mm flat span.

**Design note worth reusing: an underside groove is the right answer for
a lamp/appliance base.** Running the wire down the middle and out a groove
milled into the base's underside keeps the base sitting flush on a desk
(no rocking, no wire pinched under a rim) and hides the route completely.
Budget the plate thickness for it up front — the groove must be deeper
than the cable so it fully recesses, and still leave a real roof above it
(here 9mm plate, 4.2mm groove, 4.8mm roof).

## Technique 35 — 55 degrees is the STRUCTURAL overhang limit, not the surface-quality one; and the first real printed part is the only honest reviewer (2026-09-01)

Scott printed the mushroom lamp's stem and sent photos. The flare came out
visibly rough — "it was dropping too much filament and making it very rough
looking." That flare had been verified, on this project, at **53.1 degrees
from vertical**, deliberately placed under the P1S's documented 55-degree
unsupported-wall limit. It passed the check and still printed badly.

**The 55-degree number answers "will the wall stand up at all." It does not
answer "will the wall look good."** Those are different thresholds and this
skill had been conflating them.

The number that actually predicts surface quality is **unsupported width per
layer**:

```
overhang_per_layer = layer_height * tan(angle_from_vertical)
```

At a 0.2mm layer height and a 0.4mm nozzle:

| Angle from vertical | Overhang per layer | Fraction of the extrusion hanging over air | Result |
|---|---|---|---|
| 30 deg | 0.115 mm | 29% | clean |
| 38 deg | 0.156 mm | 39% | clean |
| 45 deg | 0.200 mm | 50% | acceptable, slight texture |
| 50 deg | 0.238 mm | 60% | visible banding |
| 53 deg | 0.265 mm | 66% | droops — what Scott photographed |
| 55 deg | 0.286 mm | 71% | stands up, looks bad |

**Rule: for any free outward surface a customer will see, target 40 degrees
or shallower — not 55.** Reserve 45–55 for internal, hidden, or
support-touching geometry where only "does it survive" matters. On a
product listing photo, "it printed" is not the bar.

Two consequences that showed up immediately when applying it:

1. **A shallower flare costs height, and that height has to come from
   somewhere.** Covering the same radius gain at 38 instead of 53 needs
   `dr/tan(38)` instead of `dr/tan(53)` — roughly **1.7x more vertical
   travel**. Ask for it explicitly: Scott's own answer here was "if need be,
   you can make the base taller," which is exactly the trade to surface
   before spending an hour trying to keep the original height.

2. **Check how much of the new, longer flare the design still hides.** On a
   two-part assembly the amount of hidden height is often fixed by the
   mechanism, not free — here it was
   `(stem_top - cavity_depth) - cap_rim = travel_v + pin_local_z - cavity_h`,
   a constant 12mm no matter how tall the stem got. So the flare could not
   be hidden by making the part taller; more of it necessarily became
   visible. Compute that budget before re-cutting the profile, or the fix
   silently changes the silhouette Scott already approved.
   (It turned out fine here — a 38-degree flare reads as a gentle trumpet,
   which is closer to the real mushroom shape than the 53-degree version
   Scott had earlier rejected as "too dramatic of a hard slope." Worth
   noticing: the printability fix and the aesthetic fix pointed the same way.)

**And the meta-lesson.** Every check this project runs — connectivity,
interference, wall thickness, overhang angle — is a check against a *model
of reality*, and each one is only as good as the threshold baked into it.
The 55-degree threshold had been in this skill from the start, unquestioned,
and no amount of re-running the check would ever have found it wrong. It
took a physical print. **When Scott sends a photo of a real part, that photo
outranks every green check in this file.** Read it as evidence that a
threshold is wrong, not just that this one model is wrong.

## Technique 36 — A studio-lit render sees defects a flat CAD preview cannot; 3MF beats STL for delivery (2026-09-01)

Scott reposted a collage of AI/3D-print tooling and asked which parts we'd
benefit from. Most of it was either not applicable (GUI modeling tools
that don't fit this shop's scripted-and-verified pipeline) or a genuine
security no (a third-party repo under PolyForm Noncommercial — unusable
for a commercial shop; two other repos this session had no access to read
at all, scoped out by this repo's own GitHub permissions). Two things in
it were real and got built the same session:

**1. Headless Blender as a design-review step (`tools/blender_render.py`).**
Not for modeling — OpenSCAD stays the only place geometry gets authored.
The value is purely in *seeing* a finished model the way a photo would
show it: real area lights, a floor plane for contact shadows, a matte
plastic material, rendered through Cycles. OpenSCAD's own PNG preview
(`--colorscheme=Tomorrow`, flat ambient-ish shading, no shadows) has
repeatedly been the reason a real defect survived multiple "verified"
renders in this project — Technique 33's cap seam and Technique 35's
overhang droop were BOTH invisible in that flat preview and only became
obvious once real light and shadow were in the picture. A quick sanity
check confirms this isn't hypothetical: the very first Blender render of
the ribbed desk caddy, at a soft three-quarter lighting angle, showed the
1.5mm-amplitude flutes reading as almost flat — much fainter than they
look in the flat OpenSCAD preview's harder single-directional shading.
That is a genuine, previously-invisible signal: shallow relief that reads
fine under CAD's synthetic lighting can wash out under realistic soft
light, which is closer to how a customer's own photos will look. Treat a
washed-out Blender render as a cue to deepen relief texture, not as a
tool quirk.

Practical notes from getting it running in this container: Blender's apt
build (4.0.2) ships with **no OpenImageDenoiser** — enabling
`cycles.use_denoising` throws `RuntimeError: Build without
OpenImageDenoiser` and aborts the render entirely, confirmed live. Leave
it off and compensate with more samples (96 was enough to be clean at
1200×1200 in ~50-90s per render, no GPU). It also has **no bundled 3MF
importer** — `bpy.ops` has no `*_3mf` operator and `addon_utils` lists
none — so this tool takes STL/OBJ/PLY only; it doesn't need to read 3MF
since OpenSCAD's own STL export already exists for every model here.

**2. 3MF over STL as the delivery format.** `openscad_render.py` already
supported `fmt="3mf"` — nothing new to build, just a real comparison run
that had never been done: Mushie's full STL is 27.3MB; the identical
geometry as 3MF is 2.1MB, roughly 1/13th the size, and the 3MF carries a
real `unit="millimeter"` attribute a bare STL has no field for at all.
CLAUDE.md already called 3MF "the gold standard" for the SS-series sign
packs for exactly this reason (pre-assembled color layers, no unit
ambiguity) — this just extends the same reasoning to every printed part's
*delivery* copy. The repo's own `.stl` stays the analysis copy (every
numeric verification in this skill — `stl_components.py`, overhang
sweeps, wall-thickness checks — reads STL, and rewriting that pipeline
for 3MF wasn't the ask); export a `.3mf` alongside it specifically for
handing to Scott.

## Technique 37 — BOSL2 cuboid()'s default CENTER anchor silently defeats a "back edge fixed, cutter reaches the front face" translate (2026-09-01)

Building the Glow Stand headphone lamp's front window (a recess cut into a
panel so a translucent insert shows through), the cutter was positioned
as `translate([riser_front_x - window_recess_d, 0, ...]) cuboid([...])`
-- the clear intent being "place the recess's BACK edge at this X, so its
FRONT edge reaches all the way to riser_front_x." It compiled, rendered
without error, and the very first preview PNG *looked* right (an assembled
mockup with the insert drawn at its intended position visually lined up
with a shadowed area on the shell). It was wrong: `cuboid()`'s default
anchor is CENTER, so that translate placed the cutter's CENTER at
`riser_front_x - window_recess_d`, not its back edge -- the recess ended
up 3.5-4mm short of the panel's real outer face on every side. It was a
fully sealed blind pocket, invisible from outside, and would have shipped
completely unnoticed: the interference check (insert vs. shell) reported
EMPTY -- correctly, since nothing was there to interfere with -- and the
render looked plausible because the render draws the insert at its
*intended* location regardless of whether the shell actually has room for
it there.

**Two lessons, not one bug fix:**

1. **A cuboid()/cyl() call authored by computing a translate for one
   specific edge, corner, or face is a translate/anchor mismatch waiting
   to happen** unless the anchor is stated explicitly to match. Either
   pass BOSL2's own `anchor=` parameter for the edge you mean (`anchor=
   FRONT+BOTTOM`, etc.) so the translate target IS that edge, or -- often
   more readable when reasoning in raw min/max coordinates like this file
   already does everywhere else -- use plain `cube()`/`cylinder()`, whose
   native corner-anchor makes "translate to the corner you mean" literally
   correct with no anchor keyword to get wrong. This file mixed both
   styles already (native cube() for the cable groove, cuboid() for
   rounded panels) -- the bug was specifically in a cuboid() call using
   center-anchor math without realizing it.

2. **"The render looks right" and "the interference check is empty" are
   BOTH insufficient on their own for a cutter/insert pair -- verify the
   cutter's OWN bounding box independent of anything else.** Render
   `window_cut()` (or whatever the cutter module is called) completely
   alone, with nothing else in the scene, and read its literal min/max
   extents off the exported mesh. That single check catches this exact
   bug in seconds; guessing from an assembled visual or from an
   interference-being-empty result does not, because both of those can
   look/read correct for the WRONG reason (nothing there to intersect
   with is not the same as something there that correctly doesn't
   intersect). Found here specifically by point-probing a grid of X
   values with `intersection(shell, tiny_cube_at_x)` and reading which
   ones came back empty vs. solid -- a fast, unambiguous per-point
   ground truth that doesn't depend on interpreting a render's shading.

## Technique 38 — An outward-flaring overhang's surface normal points DOWN, not up; get this sign backwards and an overhang scanner silently finds nothing (2026-09-01)

Writing a script to measure the Glow Stand's transition-zone overhang
angle from the real exported mesh (not just the hand-computed 35 degrees
from the design's control dimensions), the first version filtered for
faces with `nz > 0` on the theory that an "overhang wall looks up at the
sky, so its outward normal should point up." That filter matched exactly
zero faces in the transition zone -- not because there was no overhang
(there obviously was, by construction), but because the sign convention
was backwards. **A surface that flares outward as height increases -- the
overhang case -- has its outward-facing normal pointing DOWN, not up**:
picture the underside of a mushroom cap or a roof eave, where standing
underneath and looking up at the surface, you are looking at its
downward-facing outer side. `nz < 0` (with a real horizontal component)
is the correct filter for "this is a wall that needs the overhang check";
`nz > 0` on a similarly-shaped face is just the INSIDE of a cavity or a
completely different, unrelated upward-facing surface, not an overhang at
all. Confirmed by hand on the actual output: every real transition-zone
overhang face in the mesh had a normal like `(0.79, -0.16, -0.59)` --
negative Z -- and the angle from vertical is simply
`degrees(asin(abs(nz)))` once the sign filter is right, which matched the
independently hand-computed 35.0 degrees to within 1.2 degrees (36.2,
the small difference being real corner-rounding effect, not measurement
error). **When a numeric verification script reports "zero matches" for a
condition you can SEE is true in a render, suspect the check's own sign
convention before suspecting the geometry.**

## The one rule that matters most

**A clean OpenSCAD render (no errors, non-zero output size) is not proof
the model is correct.** Every bug this skill documents rendered without
error — including one that rendered a **completely empty model** with exit
code 0. The only way any of them were caught was generating a real PNG
(`fmt="png"` — works headless now, see Setup above) and looking at it
from more than one angle. Do that for every new model before describing it
to Scott as ready.

## Technique 39 — Flush multi-colour logo inlays: face-down printing, SVG import, and a wall budget that must be derived (2026-09-02)

Scott asked for the brand logo on a print "as a flat svg file in a different
colour so I can print the lid face down and it be a smooth surface." That is a
specific, correct manufacturing instruction, not a styling preference, and it
drives the whole design. Built as `openscad_models/snap_box.scad`. Six findings,
four of them real defects that rendered clean.

**The inlay itself.** The logo is neither engraved nor embossed. It is a
separate solid body occupying the top `inlay_h` (0.8mm = 4 layers) of the lid,
exactly filling a matching void in the lid body, so the printed face is dead
flat and the logo is purely a filament change in the first few layers. Because
the lid's top face is flat where the logo sits, the two are exact complements
by construction:

```openscad
module logo_prism(which) { /* extrude from lid_h - inlay_h upward, past the top */ }
module lid_body_part()   { difference()   { lid_shell(); logo_all(); } }
module lid_script_part() { intersection() { lid_shell(); logo_prism("script"); } }
```

Verify all three ways, not one: each pair's `intersection()` must be EMPTY, and
`difference(lid_shell, body, script, swash)` must ALSO be empty. Non-overlapping
is not the same as gap-free, and only the second check catches a void the inlay
fails to fill.

**A studio render is the proof, and it looks like a failure.** The Blender
review render of the finished lid shows *no logo at all* — under real area
lighting a zero-relief inlay casts no shadow, so there is nothing to see. That
is the design working. Do not read a blank studio render here as a missing
feature; read it as confirmation, and use a flat colour preview to show the
logo.

**os_teardrop is what makes a face-down lid printable.** Printed inverted, the
lid's top edge becomes a flare rising off the plate, and a plain fillet there
starts at 90 degrees of overhang. `os_teardrop(r=)` is a circular arc for the
shallow part and a straight 45-degree run exactly where a fillet would go
unprintable — so the same edge that reads soft right-side-up prints
support-free upside-down. Confirmed by scanning real face normals on the
rotated mesh: worst case 45 degrees except for the snap groove's own 0.75mm
radius.

**Bug 1 — negating Z to simulate a flip is a MIRROR, and inverts every
normal.** The first overhang scan of the face-down lid mapped `(x,y,z) ->
(x,y,-z)`. That is a reflection, not a rotation: it flips triangle winding, so
every computed normal points the wrong way and the scan reports nonsense.
Rotate: `(x,y,z) -> (x,-y,-z)`. Related to Technique 38's sign lesson and just
as silent.

**Bug 2 — scan the part AS PRINTED, not the part in isolation.** Even with the
rotation fixed, `lid_body` alone reported 5,152 faces at a full 90 degrees.
Those are the logo pocket's floor — which in the real print is supported by the
inlay material sitting in it. Scanning the union of body+script+swash, which is
what actually goes on the plate, they vanish. A part that is one object in the
slicer must be one object in the check.

**Bug 3 — a wall budget that is guessed instead of derived produces a floating
part.** The base's locating plug steps inward from the outer face by
`(lid_wall + clear)` to clear the lid skirt, so it only lands on real base
material while `base_wall > lid_wall + clear`. A first pass had `base_wall =
2.4` against a 2.65mm step: the plug hung 0.25mm clear of the cavity wall on
every side, a completely detached ring. It rendered clean, exported clean, and
reported `Simple: yes`. `intersection(base_shell, base_plug)` coming back EMPTY
is what exposed it. A second pass at 3.2 reattached it but left a 1.0mm
unsupported internal ledge. **The fix is not a better number, it is removing the
number**: `base_wall = lid_wall + clear + plug_wall` puts the plug's inner face
flush with the cavity wall, fully supported, zero ledge — and the constraint can
never silently drift again. Whenever two parts' clearances feed a third
dimension, derive that dimension from them.

**Bug 4 — mirror() before centring destroys the centring.** The maker's mark
used `translate(centre) scale(s) mirror([0,1,0]) import(...)`. The mirror is
applied to the raw import, which sits at Y 550..807 in its own units, so
mirroring sends it to -807..-550 and the centring offset then pushes it further
the same way — the mark landed ~23mm off the part and engraved *nothing*. It
still rendered and exported clean, because a cutter that misses removes nothing.
Mirror the ALREADY-CENTRED shape: `translate([0,0,-0.5]) mirror([0,1,0])
translate(centre) scale(s) linear_extrude(...) import(...)`. Chirality is
unchanged by the reorder, so Technique 4's confirmed axis still applies. Catch
it by isolating the recess-floor plane (`abs(z - mark_depth) < 1e-3`) and
checking it exists at all before checking its width.

### Using a real SVG logo in OpenSCAD

**This OpenSCAD build imports SVG.** Confirmed live against all five of this
shop's vendor wordmarks plus a fresh potrace output — `import("file.svg")`
inside `linear_extrude()` just works, groups and `transform="scale(1,-1)"`
included. Measure the result's bounds from a real import+export; the viewBox
carries padding the ink never reaches.

**But the brand logo is not vector.** `static/brand/onbrandcraftz-wordmark.svg`
is an SVG wrapper around a base64 PNG — no geometry in it. The
`static/vendor/wordmark/` files ARE real outlines but they are HUD font
pairings, not the brand mark. `tools/vectorize_brand_logo.py` traces the real
one into `assets/brand_vector/`, split by hue into the charcoal script and the
gold swash so each can take its own filament.

**import() over-tessellates and ignores $fs/$fa.** The traced script came in at
391,576 facets, and a single boolean against it ran past eight minutes without
finishing. `$fs=5` changed nothing — identical facet count. Coarsening the trace
barely helped (`-O 0.2 -> 2.0`, `-a 1.0 -> 1.334`: 305k -> 299k). The lever that
works is flattening the beziers to straight segments up front, so import() has
nothing left to subdivide: `tools/flatten_svg_paths.py` took it to 19,596 facets
and 15 seconds, with the same bounding box to within 0.001 units. Flatten any
traced SVG before booleaning against it.

**Two masks traced from one image will overlap where they touch, and clipping
them in OpenSCAD does not fix it.** The gold swash passes under the script's
descenders, so both masks share a boundary and potrace does not put the two
outlines on the same sub-pixel line. `intersection(script, swash)` came back
with 50 volumes. Subtracting the script from the swash in OpenSCAD made *those*
two parts manifold but left razor-thin slivers along the same boundary, and any
boolean involving both was still `Simple: no`. **Open a real gap in the bitmap,
before tracing** — cut the second mask back from a dilated first mask (8px at 4x
upsample, ~0.15mm). It only removes ink adjacent to the other colour, so the
swash keeps full width everywhere else.

**Minimum size is set by the thinnest stroke, and it is a hard floor.** Measure
it off the source bitmap with an erosion-depth pass rather than guessing: this
script's thin connectors run ~8px against a 1232px logo, so at anything under
about 70mm wide they fall below one 0.4mm extrusion and the slicer drops
them — the wordmark breaks into disconnected blobs. That number drove the box's
whole footprint (92x62 up to 106x72). A logo that will not fit is a reason to
use a simpler mark, never to shrink this one.

## Technique 40 — Print-in-place flexi joints: what actually governs strength, retention and swing (2026-09-02)

First articulated *animal* in this shop (`openscad_models/flexi_seahorse.scad`).
The research and the build disagreed with each other in useful ways.

### What the sources actually say

Reachable, and worth citing: JLC3DP's articulated-animal design guide, which is
unusually specific. MakerWorld, Printables, MyMiniFactory and Cults3D all 403
through this environment's proxy (unchanged from Technique 20). WebFetch's own
allowlist is *narrower* than the proxy's — several domains that WebFetch refuses
return 200 to a plain `curl`, so fetch the HTML directly and strip it rather
than reporting the source unavailable.

Real numbers, all for a 0.4mm nozzle:

| | Value |
|---|---|
| Moving-surface clearance | **0.2–0.3mm per side** (0.4–0.6 total) |
| More forgiving | 0.3–0.5mm per side |
| Wall, general structure | 1.2–1.6mm |
| Wall, repeatedly stressed joint | **1.6–2.0mm+** |
| Smallest reliable feature | 1.0–1.2mm |

Three rules that matter more than the numbers:

1. **Never scale a functional clearance.** A 0.6mm gap at 50% is 0.3mm and the
   joints fuse, even though every proportion is still "correct". Scale the
   decoration, hold the clearance.
2. **Strength comes from connector diameter, fillets and perimeter count —
   not infill.** Filling a thin leg with more infill does nothing; widening the
   connector fixes it.
3. **Check clearance around the whole rotation path**, not at one spot. A joint
   with a 0.3mm gap at its widest can still close to zero somewhere else in its
   travel.

### What the reference photos teach that text does not

A photo of four production flexi animals side by side (dragon, shark, gecko,
axolotl) settles several design questions at once:

* **Heads and legs are always rigid.** Only the spine articulates. The fragile
  appendages are never joints — that is where the strength comes from.
* **Undersides are completely flat.** Toes, gills and fins all lie in the bed
  plane, not on the body's centreline.
* **Articulation stops before the tail gets thin.** The gecko's tail tip is a
  solid taper. Shrinking a joint to keep segmenting a tapering tail is how a
  tip becomes a fused stub or a snapped one.
* **Partial articulation is a legitimate choice.** The shark is one rigid body
  with four tail segments — rigid where the silhouette matters, flexi where the
  movement does.

### Orientation is structural

Printed flat, each neck's bending stress runs along the layer plane — the
strong direction. A neck standing up in Z loads the layer bonds in tension,
4–5× weaker, and that is the documented way these snap. So a flat-printed
flexi animal must articulate **in the print plane**. Pick an animal whose
natural motion is in that plane and nothing is compromised for it.

### The geometry, and the trade nobody writes down

Ball-and-collar: each segment ends in a ball on a neck; the next segment's
collar is a cup of `R + clear` that runs `lip` past the ball's centre and traps
it. Retention is `R - throat`, where the **throat is the collar's narrowest
inner radius** — and the throat is set by *two* surfaces fighting:

```
throat = min over x in [0, lip] of max( sqrt(Rc^2 - x^2),  neck_r + clear + x*tan(mouth) )
                                        cup closing in      mouth cone opening out
```

Neither surface tells you the answer alone. Widen the mouth for swing and the
throat opens and the tail pulls apart; narrow it for grip and the tail stiffens.
Sweep this in Python before touching OpenSCAD — the whole retention landscape
costs a second, where each CGAL swing test costs a minute.

**Swing is governed by pitch/R, not by the mouth angle.** The limit is the
collar rim striking the next segment's flank. At pitch/R = 3.0 it is 16–18°; at
2.5 the identical joint drops to 12°. Change the spacing and the swing changes.

**A two-stage mouth relief buys both.** One cone cannot be narrow at the ball
(for the throat) and wide at the rim (for swing). Split it: keep the shallow
cone through the throat, then flare hard past it to chamfer the rim. On the
finished seahorse segment a single 22° cone gave **6°** of swing; adding a 45°
flare starting just past the throat took it to **14°** with retention only
dropping 0.42 → 0.34.

Final: `R 2.9, clear 0.25, neck dia 2.9, mouth 22°, pitch 8.7, wall 1.6` →
bead dia 9.5, retention 0.42mm, swing 14°/joint on the real decorated segment.

### Verification that actually catches things

* **Component count is the primary check.** N segments must be N+1 components
  (body + each segment). The seahorse's first build had 15 where 13 was right —
  the two extras were the eye pupils, sitting almost concentric inside their
  own sockets and touching nothing. Loose balls in each eye, invisible in every
  render.
* **The body must CUP the first ball, not swallow it.** A trunk that simply
  overlaps the first ball fuses the top joint solid, and it looks identical to
  a working one in any render. Give the body the same cup, mouth relief and rim
  trim every bead gets.
* **Re-test swing on the FINISHED segment**, decoration and belly trim included.
  The bare joint measured 16°; the decorated one 14°. Anything added to a bead
  can eat into the swing.
* **Run the overhang scan and read where it points.** On the seahorse it
  flagged 90° at the snout tip: the snout, fins and coronet were all thinner
  than the belly trim plane and would have printed hanging 1–2mm above the
  plate with nothing under them. Thin features must be placed ON the bed
  (`z = bed + r*squash`), not on the body's centreline — which is exactly what
  the reference photos' flat undersides were showing all along.

### Choosing the animal

Pick one whose real anatomy is already segmented and whose natural pose is a
curl in one plane, and the articulation stops looking imposed. A seahorse's
body is genuinely bony rings and its signature pose is a curled prehensile
tail — so the joints are the animal, not a mechanism bolted through it.

---

## Technique 41 — What 253 real, selling 3D prints look like, and the design standard that comes out of it (2026-09-02)

Scott, on the flexi seahorse: *"Not bad, can definitely be better. Do more real
visual research looking at how and the exact model structures of 200 different
3d prints."* This is that research and the standard it produced. It supersedes
nothing above — it is the pass to run BEFORE Technique 30's surfacing work,
because it governs *what to build*, not *how to smooth it*.

### The corpus (reproducible)

1,556 unique thumbnail URLs harvested from Cults3D across 20 category queries
(flexi articulated animal · print in place dragon · articulated fish · flexi
keychain · print in place hinge box · snap fit storage box · desk organizer ·
pen holder · vase spiral · planter pot · lamp shade · phone stand · headphone
stand · cable clip · kawaii figurine · cute animal figurine · multicolor sign ·
fidget toy · puzzle box · articulated lizard), sampled evenly to 260, 258
downloaded, **253 valid images reviewed** as 8 numbered contact sheets.

**Network reality worth recording:** WebFetch's allowlist is *narrower* than the
agent proxy's — several hosts WebFetch refuses return 200 to plain `curl`.
Printables, MakerWorld, stlfinder, all3dp = 403 to everything. Cults3D, Thangs,
Sketchfab, Thingiverse, pinshape, grabcad, Bing, DuckDuckGo = 200. Cults3D is
the workable thumbnail source; go straight there next time.

### The ten structural findings

1. **Almost nothing has a large plain smooth surface.** Across 253 images, plain
   surfaces are rare enough to be notable. Fluting, scales, knurl, Voronoi
   lattice, basket weave, faceting, perforation, twisted ribs — surface
   treatment is the *product* in whole categories (lamp shades, vases, pen cups,
   fidget keychains). A smooth panel reads as unfinished, not as minimal.
2. **Winning silhouettes are ONE swept profile, not stacked masses.** Every
   selling vase is an ogee — convex belly into concave neck into a small lip
   flare — revolved and twisted. The good headphone stands are a single
   cantilevered arc whose cross-section changes as it sweeps. Stacked primitives
   are what "blocky" actually means, and no amount of edge rounding fixes it.
3. **Detail density is 5–10× what a first pass produces.** An armored-lizard
   flexi carries ~50 discrete spikes plus a full scale field; dragon flexis
   carry layered scales on *every* segment. Nine rings with five tubercles each
   is a sketch of detail, not detail.
4. **The head carries the value on any creature.** The clearest pattern in the
   flexi category: a rigid, highly expressive HEAD plus a *short* articulated
   body — the "Bendy Buddies" shape, chunky cartoon animal, 2–4 joints total.
   Nine identical tail joints is effort spent where buyers do not look.
5. **Top articulated animals articulate LIMBS, not just a spine.** Geckos,
   lizards and character figures all put joints at shoulders and hips.
   Spine-only articulation is the easy version.
6. **Sets sell; single models are the exception.** "10 PREMIUM STL MODELS", six
   colorways of one sign as one listing, four lizards on one plate, a rack of
   textured keychains. Design a parametric *family* from the outset — one
   `.scad` emitting N variants from a top-level parameter.
7. **Multicolor is mostly geometric, not painted.** The strongest two-colour
   work is either a **layered 2D offset stack** (glyph → `offset(delta)` backing
   → optional second offset; the entire multicolor-sign category is this one
   construction) or a **contrasting inner body seen through slots cut in the
   outer** (twisted flute vases, spinner tops). Both print on a plain 2-colour
   AMS with no painting step.
8. **The marketing pose is part of the model.** Flexis are photographed curled,
   gripping a board edge, wrapped round a tube — never straight. That means the
   model must have enough total curl to actually grip (>360°) and a `pose`
   parameter is a real deliverable, not a render convenience.
9. **"PRINT IN PLACE — NO SUPPORTS" is a headline, not a constraint.** It is
   printed on half these listings. Design toward it and state it.
10. **Small wins on plate economics.** Sets are small models, 4–8 to a plate.
    A 180mm one-per-plate model is a long print and a weak set.

### The standard — run this on every model from now on

Before geometry:
- [ ] **Reference pass first.** Pull real images of this specific object class
      and name its structural language out loud before writing a line of code.
- [ ] **Silhouette as a named point list**, reviewed as a 2D profile, before any
      3D exists. If the profile is not interesting flat, the model will not be
      interesting round.
- [ ] **State the surface treatment explicitly** as a design decision, and
      implement it as a periodic modulation of the profile — never decals
      unioned onto a finished body.
- [ ] **State a detail budget as a number** (discrete features per major
      surface) and generate them procedurally with per-instance variation.
- [ ] **Decide set-or-single.** If a family is plausible, parameterise for it
      now; retrofitting a family onto a bespoke model does not work.
- [ ] **Size for the plate**: can 4–8 fit on 256×256?

During geometry:
- [ ] **Every junction between two masses gets an explicit blend** — `hull()` of
      overlapping spheres, or a BOSL2 rounding — and the blend is *verified* on
      an oblique render, not assumed. Head-on renders hide relief entirely
      (learned the hard way on the OBC medallion: flat-topped relief shows
      identical normals from straight down).
- [ ] **On a creature, ~half the modelling effort goes to the head.**
- [ ] **Multicolor by geometry** — layered offset, or an inner body through
      slots — before reaching for anything else.

Verification (unchanged, still the part that catches real bugs):
- [ ] Connected-component count over STL vertices — the primary check.
- [ ] `intersection()` tests for anything that must touch (and must NOT touch).
- [ ] Overhang scan **in print orientation** (rotate, never negate z alone).
- [ ] Joint throat/retention/swing measured on the *finished, decorated*
      segment.

---

## Technique 42 — Reading real models' GEOMETRY: the measured anatomy of top print-in-place designs (2026-09-02)

Scott: *"I need you to truly see how they are built and structured so you can
get better."* Technique 41 came from marketing thumbnails, which teach almost
nothing about construction. This one comes from **downloading real mesh files
and cutting them open.** Every number below is measured off actual geometry,
not read off a page.

### How to get real geometry (works today, save the trouble of rediscovering)

Printables' GraphQL API at `https://api.printables.com/graphql/` answers
**unauthenticated**. Introspection is off and `prints(...)` search returns
empty, but `print(id: N)` works, and **GraphQL aliases batch it**: 200 ids in
one POST, ~85% of ids live. That makes a keyword+likes scan over the whole id
space cheap (64k ids ≈ 3 minutes at 10 threads).

```
{ p1: print(id:1){id name likesCount downloadCount}  p2: print(id:2){...} ... }
```

Valid `stls{}` subfields: `id name fileSize filePreviewPath note created folder`.
There is **no download field** — but for prints below id ≈ 900000 the preview
path is `.../<lowercased file name>_preview.png` in the file's own directory,
so the real file is `https://files.printables.com/<dirname>/<name.lower()>`.
Verified byte-exact against `fileSize`. Above id ≈ 900000 previews became
opaque uuids and this no longer derives — **scan the 200000–880000 band.**

Dead ends, so they are not retried: `www.printables.com` is behind a Cloudflare
challenge (403 to curl AND to headless Chromium through the agent proxy —
`ERR_CONNECTION_RESET`); Thingiverse is a JS SPA with a token-gated API; Bing
image search returns unrelated junk for technical queries.

### The tools this produced

* `tools/mesh_anatomy.py` — cross-sections along any axis, silhouette
  envelope, dihedral-angle distribution, component count, and `--joints`
  (real clearance + least-squares ball radius between components). Validated
  by pointing it at my own seahorse: it recovered `clear = 0.25` and
  `R = 2.9` from the mesh alone.
* `tools/quick_render.py` — numpy z-buffer render. Blender in this container
  takes >15s to answer `--version`, which kills the look-at-it-now loop.

### THE STANDARD PRINT-IN-PLACE BALL JOINT — measured, and it is not what I built

Measured on two unrelated designers' models (Centibug/Trilospike, and a
goldfish carp flexi). **Normalised by ball diameter D, they are identical to
three decimal places** — this is a shared standard, not a coincidence:

| | goldfish D=3.06 | goldfish D=3.60 | trilobite/centipede D=4.80 | **ratio** |
|---|---|---|---|---|
| socket width (swing axis) | 4.903 | 5.768 | 7.690 | **1.600 × D** |
| socket height (retention) | 3.283 | 3.863 | 5.150 | **1.073 × D** |
| clearance, tight direction | 0.126 | 0.149 | 0.198 | **0.0413 × D** |
| clearance, swing direction | 0.929 | 1.089 | 1.457 | **0.303 × D** |
| flat ceiling bridge | 2.55 | 3.00 | 4.00 | **0.833 × D** |

Read what that actually says:

* **The socket is a flat-topped capsule slot, not a sphere.** The ball is
  round (roundness 1.000) but the pocket is 1.6 D long and only 1.07 D tall.
* **Swing comes from slot length**, not from cone angles. 0.30 D of free run
  fore and aft. My cone-angle scheme (Technique 40) is a more fragile way to
  buy the same motion.
* **Retention is structural and absolute.** Socket height is only 7% more than
  the ball, and the pocket is fully enclosed — the ball physically cannot
  leave. No "retention distance" to compute, no pop-off.
* **The flat ceiling is the printability trick.** 0.833 D of flat bridge
  directly over the ball instead of a spherical dome overhang.
* **They DO scale clearance with ball size** — a constant 4.13% of D. This
  contradicts the "never scale a functional clearance" rule for *this* joint,
  and at D=3.06 it lands at 0.126mm, well under one 0.4mm extrusion. That is
  deliberate: the joint **prints lightly fused and is freed by the first
  flex.** It is why their joints feel tight and mine (0.25mm) would rattle.

### Segment proportions — the number that explains "too blocky / tubular"

| | pitch/girth | segment length ÷ pitch (overlap) | girth taper |
|---|---|---|---|
| trilobite | 0.21 | 3.61 | 73% |
| goldfish carp | 0.39 | 2.43 | 93% |
| **my seahorse** | **1.20** | **1.67** | **~0%** |

* **Segments must be 2.5–5× wider than they are long** (pitch ≈ 0.2–0.4 ×
  girth). Mine were longer than wide, which is exactly why the body reads as a
  tube of beads instead of an animal with plates.
* **Each segment overlaps 2.4–3.6 pitches of its neighbours.** The lap is what
  hides the joint line — that is why good flexis look continuous.
* **Girth tapers 70–93% head to tail.** Mine barely tapers at all.
* And the joint gap is a **design feature**: on the real models it is a deep,
  wide, dark band that stripes the body rhythmically. Mine were hairlines.

### Surface quality, as a number

Dihedral angle between adjacent faces, and `profile_kink` (2nd derivative of
the silhouette envelope) separate the three real design languages cleanly:

| | mean dihedral | p95 | hard edges >45° | kink mean | tris |
|---|---|---|---|---|---|
| centipede (sculpted smooth) | 1.77° | 2.9° | 0.52% | — | 3.93 M |
| goldfish (sculpted smooth) | 1.89° | 2.8° | 0.69% | — | 1.21 M |
| spiral vase (smooth swept) | 3.76° | 8.5° | 1.46% | 0.174 | 268 k |
| *low-poly vase (deliberate)* | 45.5° | 108.8° | 59.0% | 7.17 | 6.8 k |
| **my seahorse** | **12.9°** | **76.5°** | **9.7%** | **6.55** | **60 k** |
| **my snap box lid** | **27.1°** | **90.0°** | **28.3%** | **1.91** | **27 k** |
| **my mushroom lamp** | **11.2°** | **90.0°** | **11.0%** | **6.64** | **145 k** |

**My organic models sit in the dead zone** — too faceted to read as smooth,
too smooth to read as intentional low-poly. That is precisely what "not enough
real look to them" means, and now it has a threshold:

* **Smooth organic target: mean dihedral < 4°, p95 < 9°, hard edges < 1.5%,
  profile kink mean < 0.2.** Reaching it needs BOTH a genuinely continuous
  profile AND real tessellation — 1–4 M triangles is normal for these, against
  my 60 k. `$fn`/`$fs` must go up accordingly; a smooth surface cannot be
  faked with a coarse mesh.
* **Deliberate low-poly is the other valid answer** — but then commit: mean
  dihedral 28–45° applied uniformly to the whole body, and very few triangles.
* Never land in between.

### Vessel proportions, measured (Spiral Vase No.2)

* Silhouette is a true ogee: foot r=33, **widest at z=25 of 133 — the belly
  sits at 19% height, not the middle**, r=44; waist r=13.5 at z=115; small lip
  flare to r=17.
* **neck ÷ belly radius = 0.31.**
* The repeating surface unit is **not a sine wave** — it is an asymmetric
  comma/teardrop lobe with an undercut hook on the leading edge. That
  asymmetry is what makes it read as carved rather than corrugated.
* **The detail breathes**: lobe amplitude starts shallow at the foot, grows
  through the belly, and collapses back to nearly circular at the lip. Detail
  is resolved at both ends, never chopped off at a boundary.

### What to do differently, concretely

1. Use the **flat-topped capsule socket** above, sized off D, instead of the
   sphere+cone cutter. Enclose the ball fully.
2. Clearance = **0.041 × D**, accepting a lightly-fused joint freed by the
   first flex — not a 0.25mm "guaranteed free" gap.
3. **pitch ≈ 0.3 × girth**, segments overlapping ~2.5 pitches, girth tapering
   ~80% along the body.
4. Raise tessellation until mean dihedral < 4°, or commit to low-poly.
5. Make the joint gap a deliberate, readable dark band.
6. Give every segment its own secondary form (the trilobite's three lobes and
   per-plate crown) — a plain segment with a few tubercles is not detail.

---

## Technique 43 — Mechanisms and DFAM statistics, measured off 88 real models (2026-09-02)

Technique 42 dissected articulated creatures and vases. This round went after
everything I had never actually measured: snap fits, hinges, four-bar linkages,
multi-colour interfaces, wall thickness, support need — plus a calibration of
OpenSCAD's own tessellation against the smoothness numbers real models hit.

Tool added: `tools/dfam_probe.py` — wall thickness by ray-casting into the
solid, overhang distribution in print orientation, bed contact, edge radii,
plate footprint. Validated by pointing it at my own snap box: it recovered the
2.0mm wall (p01 1.999, p05 2.003) with no access to the source.

### 0.2mm per side is a universal constant

Three unrelated mechanisms, three unrelated designers, same number:

| mechanism | measured clearance |
|---|---|
| print-in-place ball joint (centipede/trilobite) | 0.198 mm |
| tongue-and-groove case lid (parametric case) | 0.195 mm |
| my own snap box, lid skirt over base plug | 0.190 mm |

Anywhere two printed surfaces must slide or seat against each other, 0.2mm per
side is the answer. Do not re-derive it per project.

### The ball joint, corrected and VALIDATED in OpenSCAD

Technique 42 got the socket proportions right but read the 0.833 D feature as a
"flat ceiling". Slicing an isolated pair of segments both ways shows what it
actually is: **the mouth** — the opening on the neighbour-facing face, through
which the neck passes. It is narrower than the ball, and that is the retention.

```
D       = ball diameter, the only design choice
sock_l  = 1.600  * D     socket length, swing axis
sock_h  = 1.073  * D     socket height  -> 0.0365 D clearance per side
corner  = 0.3835 * D     socket corner radius (falls out of mouth width)
mouth   = 0.833  * D     opening toward the neighbour -- NARROWER than the ball
neck_d  <= 0.60  * D     must pass the mouth freely
```

The socket is a **rounded rectangle in the swing plane, swept across the body
width** — not a sphere, not a capsule. Swing comes from the 0.30 D of free run
along the slot. Retention is the ball having to spread the mouth by **0.167 D**
(0.8mm at D=4.8) to escape — firm and positive, unlike a cone-relief cup.

Built it in OpenSCAD from these ratios alone and measured it: **two free
components, 0.181mm surface-to-surface gap** against the reference's 0.198.
The recipe reproduces. Two mistakes made on the way, both worth avoiding:
the socket block must extend PAST its own pocket (otherwise the pocket cuts the
front face away and there is no retaining wall left, and it still renders
happily), and the mouth slot must be cut in the same sweep as the pocket.

### Snap versus locate — they are different joints and I had been conflating them

The parametric case lid is a **locator**, not a snap: groove 1.21mm wide × 1.0mm
deep, tongue 0.82mm wide × 0.8mm tall, 0.195mm clearance on BOTH sides and
0.2mm of bottom relief. No barb, no interference. It positions the lid; friction
or fasteners hold it.

My snap box is a real **snap**: 0.19mm sliding clearance on the plain wall, and
the bead crest stands 0.54mm proud into a 0.76mm groove, giving 0.35mm of
interference per side that the skirt must spring over. Measured seated, the bead
sits in the groove with 0.41mm to spare, so it never bottoms out. That checks
out — the box is sound.

Rule: **a locate is 0.2mm clearance; a snap is 0.2mm clearance PLUS deliberate
interference on the barb only.**

And one principle I had not been applying — **separate the locating feature from
the seating datum.** The reference tongue is 0.2mm shorter than its groove is
deep, so the lid seats on the wide flat rim faces and the tongue only locates it
laterally. A feature that tries to do both does neither accurately.

### Lattice (living) hinge, fully measured

From a book box that folds flat. Panel 1.8mm thick, slots cut all the way
through:

```
rib width      1.74-1.83 mm   (~= panel thickness; square in section)
slot width     0.50 mm        (one clean nozzle-width void)
pitch          2.30 mm        12 slots across a 27.9mm hinge zone
bridge length  4.5 mm
bridge spacing 27.7 mm along the hinge axis
stagger        adjacent slots' bridges offset by HALF the spacing
```

Flexibility comes from the long unbridged spans twisting; strength comes from
the staggered bridges, which leave no straight tear path across the hinge.
Ratios: slot/pitch = 0.22, bridge/spacing = 0.16.

### Print-in-place four-bar hinge (SD card box)

Six components in one printed part: body, lid, and two mirrored pairs of links.
Each side runs body—long link—lid and body—short link—lid.

```
pin diameter        ~4 mm
clearance at body pivots   0.149-0.150 mm
clearance at lid pivots    0.200-0.204 mm
lid-to-body parting gap    0.596 mm   (they never touch; the linkage carries it)
link volume                0.07-0.14 cm3
```

Note the deliberate asymmetry: tighter at the body (the datum), looser at the
moving end.

### Multi-colour parts overlap slightly — they are not exact complements

Measured on a dual-colour print-in-place truck: each colour is **its own
watertight solid**, they share a coincident boundary surface, and about **2% of
one part's vertices sit strictly inside the other**. That small deliberate
interpenetration is what guarantees no hairline gap at the colour boundary.

My snap box lid inlay is exactly complementary — `difference()` and
`intersection()` against the same prism, zero overlap. It works, but giving the
inlay ~0.05mm of interference into the body would be strictly safer.

### THE tessellation finding — OpenSCAD's defaults ARE the "blocky" problem

Measured mean dihedral angle on a hemisphere rendered at various settings:

| setting | mean dihedral | p95 | triangles (r=40) |
|---|---|---|---|
| `$fa=12; $fs=2;` (**OpenSCAD default**) | 13.8° | 107.9° | 472 |
| `$fa=6;  $fs=0.8;` | 7.2° | 6.0° | 1 788 |
| `$fa=4;  $fs=0.5;` | 5.2° | 4.0° | 3 772 |
| **`$fa=2;  $fs=0.4;`** | **2.7°** | **2.0°** | **14 388** |

Real sculpted models measure 1.8–1.9°; the smooth swept vase 3.8°; **my
seahorse 12.9° and my mushroom lamp 11.2° — which is exactly OpenSCAD default
territory.** The "not enough real look" was never a modelling-talent problem in
the first place; it was a two-line settings problem.

`$fn` is a *count*, so its facet angle depends on feature size — a 5mm boss and
a 200mm body at the same `$fn` are not equally smooth. `$fa`/`$fs` are an angle
and a length, and they hold ~2.5–2.7° across a 8× size range. **Put
`$fa = 2; $fs = 0.4;` at the top of every organic model.** Keep defaults for
flat functional parts — real ones measure 604–2 014 triangles and do not need
more.

### DFAM statistics — 88 real models, measured not asserted

|  | p10 | median | p90 |
|---|---|---|---|
| min feature (wall p05) | 0.73 mm | **1.45 mm** | 3.00 mm |
| typical wall (median) | 1.40 mm | **3.21 mm** | 10.99 mm |
| smallest edge radius | 0.11 mm | **0.41 mm** | 1.08 mm |
| tallness, h / max(w,d) | 0.12 | **0.38** | 1.48 |
| longest bbox edge | 40 mm | **113 mm** | 236 mm |
| copies per 256×256 plate | 1.6 | **11** | 135 |
| triangles | 7 556 | **27 708** | 162 368 |
| **% of downward area needing support** | 0% | **5.5%** | 38% |

Read the last row carefully: **real models are designed to print essentially
support-free.** The median part has 5.5% of its downward-facing area steeper
than 55° and off the bed. That is a design constraint being honoured, not luck.

Also: parts are **wide and low** (tallness 0.38) and **small enough to batch**
(11 per plate). And useful individual walls seen: 1.6mm uniform throughout a
stackable bottle holder, 1.2mm on a tool holder, 0.8mm minimum on a case,
0.2mm single-wall on an ultralight glider.

### A trap in my own tooling, now fixed

`probe_joints()` measures vertex-to-vertex distance, which is only accurate on
dense meshes. On the coarse OpenSCAD prototype (1 620 triangles) a real 0.18mm
gap measured as **4.0mm** — the nearest vertices were nowhere near the nearest
surfaces. `surface_gap()` in `mesh_anatomy.py` does the honest measurement;
use it on anything not densely tessellated.

And: **STL files ship in DESIGN orientation, not print orientation.** Both the
reference case lid and my own snap box lid store rim-down with almost no bed
contact. Never infer print orientation from a file — and never trust a
bed-contact number without checking the part is actually posed for printing.

---

## Technique 44 — SLICE IT. A mesh that passes every geometric check can still print as one solid lump (2026-09-02)

The most important thing found in three rounds of research, and it invalidates
part of Technique 40.

`tools/gcode_probe.py` (new) rasterises the real extrusion moves of a sliced
layer and counts connected islands of material — the toolpath equivalent of a
connected-component check on a mesh. **If two parts that should be free come out
as one island, the model prints fused, whatever the geometry says.**
PrusaSlicer 2.7 is installable here (`apt-get install -y prusa-slicer`) and has
a CLI; `p1s.ini`-style config with `nozzle_diameter=0.4`, `layer_height=0.2`,
`extrusion_width=0.42` approximates the P1S closely enough for this question.

### The finding

**The flexi seahorse prints as a solid stick.** Sliced at 0.2mm layers with a
0.4mm nozzle, the entire tail is **one connected island** through every layer
from z=2.6 to z=5.8 — the band containing every ball.

Everything else had passed:
* mesh splits into exactly 10 components ✓
* measured gap exactly 0.25mm everywhere ✓
* overhang scan clean, renders correct ✓

None of it mattered. The defect exists only in the toolpaths.

### Why — it is the socket SHAPE, not the clearance

Control test, two cubes at a measured gap, sliced and island-counted:

| modelled gap | islands |
|---|---|
| 0.15 mm | **1 (fused)** |
| 0.20 mm | 2 |
| 0.25 mm | 2 |
| 0.40 mm | 2 |

So 0.2mm resolves fine between *flat* walls. But a **sphere inside a spherical
cup** leaves a crescent-shaped void that is thinner than one extrusion
everywhere except the single tangent point — the slicer bridges straight across
it. Re-slicing with `--gap-fill-enabled=0 --thin-walls=0` changes **nothing**:
this is geometry, not a setting, and therefore not fixable by telling a
customer to change their slicer profile.

The measured standard slot socket (Technique 43) sliced at the same settings:

| model | modelled clearance | islands per layer |
|---|---|---|
| reference centipede joint pair | 0.198 mm | **2** (4 at the ball height) |
| my rounded-rect slot prototype | **0.175 mm** | **2** (4 at the ball height) |
| my seahorse, spherical cup | 0.250 mm | **1 — fused** |

**A slot socket at a SMALLER clearance separates cleanly; a spherical cup at a
larger one does not.** This is why every real designer uses the slot: it is not
a style choice, it is the only socket shape that survives slicing. The 1.46mm
of swing-direction relief measured in Technique 42 is not generosity — it is
the part of the void that is wide enough for the slicer to see.

It also explains, retroactively, the advice in the seahorse print guide that
0.25mm was "near the reliable floor". That was the wrong diagnosis: the number
was compensating for a shape that does not work at any clearance.

### The rule

**Slicing is now a mandatory verification step for anything with a moving
joint, a thin slot, or two surfaces that must stay separate.** Mesh component
count proves the SOLIDS are separate; only an island count on the toolpaths
proves the PRINT will be. Run both.

```
prusa-slicer --load p1s.ini -g -o out.gcode model.stl
python3 tools/gcode_probe.py out.gcode --scan          # islands per layer
python3 tools/gcode_probe.py out.gcode --layer-z 3.4 --plot paths.png
```

### Correction (2026-09-04): the flat-wall control-test numbers above were wrong

Extending this research to gears (Technique 46) needed the island-count check
again, on a mesh gap of 0.15mm — and it came back fused. That contradicted the
control table above, which said 0.15mm resolves. Chasing the contradiction
found a real bug in `gcode_probe.py` itself, not in either print.

**The rasterizer's dilation, at its default `px=0.15`, closes real gaps up to
about 0.3mm** — comparable to the gap sizes this whole technique is built on
measuring. Sweeping the same layer across `px` from 0.15 down to 0.02 on the
original two-cube control does not converge smoothly; it flips between 1 and 2
islands non-monotonically until `px` reaches about 0.06–0.04mm, where it
stabilizes. That instability is the signature of a check operating at its own
resolution limit, not a real physical effect — confirmed by measuring the
actual toolpath centerlines directly (no rasterization at all): a modeled
0.15mm gap prints with a real 0.57mm gap between bead centerlines, because
each bead's own extrusion width (0.42mm here) holds the nozzle back from the
true surface on both sides. There was never a physical reason for it to fuse.

Re-swept the flat-wall control properly at `px=0.04` (now the tool's default,
down from 0.15) with the true toolpath-gap cross-check added:

| modelled gap | islands | true printed gap |
|---|---|---|
| 0.05 mm | 1 (fused) | 0.78 mm (merged into one wide bead) |
| 0.08 mm | 1 (fused) | 0.78 mm |
| **0.10 mm** | **2** | 0.52 mm |
| 0.15 mm | 2 | 0.57 mm |
| 0.20 mm | 2 | 0.62 mm |
| 0.40 mm | 2 | 0.82 mm |

**The real flat-wall fusion threshold for a 0.4mm nozzle at these settings is
between 0.08mm and 0.10mm — not 0.15–0.20mm as first reported.** Once resolved,
the true printed gap tracks `modelled_gap + one_extrusion_width` almost
exactly (0.15 + 0.42 = 0.57, matched). Below the threshold the slicer doesn't
leave a sliver at all; it merges the two beads into one deposit roughly
`2 x extrusion_width` wide.

**What this does and does not change.** Every real joint validated in
Technique 42–44 — the reference centipede joint (0.198mm) and the rounded-rect
slot prototype (0.175mm) — was re-checked at the corrected resolution and
gives the identical island count it gave before, because both clearances sit
comfortably above the corrected ~0.10mm threshold. The seahorse's spherical
cup also still fails at the corrected resolution — more informatively than
before: instead of one clean fused blob it fragments into 6 disconnected
slivers (84.9/68.7/64.5/8.5/1.7/1.7 mm²), which is the fine-grained signature
of a crescent void that's sub-bead-width almost everywhere except one tangent
point. **Nothing about which sockets work changes.** What changes is that
0.15–0.2mm clearances were never as close to the edge as this file claimed —
there is more real margin in the measured ball-joint standard than reported.

**The standing rule this adds to Technique 44's "slice it" rule: when an
island count is close to 1 vs 2, or the finding is new, sweep `--px` down
until the count stops changing before trusting it.** A single reading at
whatever the tool's default happens to be is exactly the kind of unverified
number this shop's rules exist to catch. `gcode_probe.py`'s default is now
`px=0.06` (was 0.15) and `--px` is exposed on the CLI for exactly this sweep.

### Free bonus: real print time and cost, which we never had

Sliced at 0.2mm / 3 walls / 15% gyroid, PLA at $20/kg:

| model | time | filament | cost |
|---|---|---|---|
| flexi seahorse | 1h 47m | 13 g | $0.26 |
| snap box base | 3h 59m | 48 g | $0.96 |
| snap box lid | 2h 19m | 25 g | $0.50 |
| **snap box, complete set** | **~6h 30m** | **~75 g** | **~$1.50** |
| mushroom lamp | 12h 24m | 159 g | $3.18 |
| glow headphone stand | **24h 00m** | 331 g | $6.63 |

Filament is nearly free; **printer time is the entire cost**. A 24-hour part
caps the shop at one unit per day and cannot carry a sellable margin. Check the
sliced time BEFORE committing to a physical product, not after — and treat
roughly 4 hours per sellable unit as the ceiling worth designing toward.

---

## Technique 45 — Geometry does not predict popularity. A negative result worth keeping (2026-09-02)

The question: across real published models, do measurable geometry properties
track how well a design does? If they did, we could aim at them.

**They do not.** Recording this so it is not re-investigated.

### Method

107 models, **stratified across five likes bands** (1–10, 10–40, 40–150,
150–600, 600+; ~22 each, sampled at random within band from a pool of 3,734
downloadable prints). Stratification matters: the first attempt reused the
earlier corpus, where every model already had ≥780 likes — a truncated sample
that can only produce nonsense. Each model measured with `dfam_probe.py`, then
Spearman rank correlation against likes.

### Result

| property | Spearman vs likes |
|---|---|
| support fraction | **−0.210** (weak) |
| triangle count | +0.189 |
| longest bbox edge | +0.156 |
| component count | +0.124 |
| smallest edge radius | −0.117 |
| wall thickness, plate area, copies per plate, tallness, thin fraction, min feature, bed fraction | **all \|r\| < 0.10 — noise** |

Print time and filament mass, sliced for **104 of the 107**: **+0.015 and
+0.041. No signal whatsoever.** Band medians run 193 / 91 / 157 / 318 / 182
minutes from lowest to highest likes — no trend, and not even monotone.

This number moved twice while the slicing batch was still running: +0.13 at
n=33, −0.03 at n=83, +0.015 at n=104. The conclusion ("no signal") was right
every time, but the intermediate values were reported as though the batch had
finished when it had not. **Check that a background job has actually exited
before quoting its output** — `wc -l` on a file that is still being appended to
is not a finished result.

### The one signal, and the one that evaporated

**Support fraction survives.** Median % of downward area needing support, by
likes band: 12.5 → 10.5 → 2.3 → 5.8 → **0.54**. Controlling for category it
holds strongly among decorative items (21.8% for the low-likes group vs
**0.0%** for the high-likes group) and weakly for boxes/organizers (7.2 → 5.5).
Support-free printing is a real quality marker.

**Triangle count does NOT survive.** It looked like a monotone rise across
bands (12.4k → 21.9k), but controlling for category it *reverses* for
decorative items (29.1k low-likes vs 9.3k high-likes). It was a category
artefact. Do not use mesh density as a quality proxy.

Category mix was checked and is stable across bands (boxes/organizers dominate
every band at 10–14 of ~22), so the band comparisons are not a mix effect.

### What this means for choosing what to build

**You cannot pick a winner from geometry metrics.** Size, wall thickness,
plate efficiency, part count, tallness, minimum feature, print time and
filament cost all predict nothing. What separates a 5-like model from a
5,000-like model is subject and execution, and neither is in the mesh.

The one actionable half: **design it to print without supports.** That is the
only measurable property that tracks, and it is a craft discipline rather than
a dimension to tune.

Caveats stated plainly: n=107 for geometry, n=104 for print time; within-category
cells are 2–14 models, so the support finding is suggestive, not proven. Likes
also confound age, author following and thumbnail quality — none of which are
measurable here.

---

## Technique 46 — Gears, brackets, threads and cosplay armor: real geometry from 500+ more prints (2026-09-04)

Scott: *"Look at 500 different prints visually and make sure to get how they
are designed and the details... I need you to be able to design prints with
great detail and quality."* This round went after mechanism classes never
touched before — gears, brackets, threads, cosplay armor, jewelry — using the
same method as Technique 42–45: real preview images at scale plus real
downloaded geometry, not marketing photos.

### The corpus

Cults3D is now behind a Cloudflare challenge (403 to everything, unlike
earlier sessions) — noted so it isn't retried. Pivoted entirely to
Printables, which is still fully open. Two moves that made this fast:

1. **Re-filtered 8,457 print records already cached from prior sessions**
   against 13 new category keywords (gear, thread, bracket, cosplay/armor,
   miniature, jewelry, chess, RC, phone case, keycap, coaster, watch/tool) —
   zero new API calls, 585 real matches instantly.
2. **A fresh 224,021-id GraphQL scan** (ids 900,000–1,200,000, the band the
   original scan never reached) against the same keyword set found 3,819
   more, at up to 6,400 likes — much higher quality than the first pass.

**Corrected a wrong assumption from Technique 42 while doing this:** the
"preview path only derives below id ≈ 900,000" limitation is real for
*reconstructing a download URL from a filename*, but the preview PNG path
itself is always returned directly in `filePreviewPath` regardless of era —
no derivation needed for images, only for guessing an undisclosed STL URL.
That single fix is what made a 1,015-image visual pass (316 + 699) possible
in this session, on top of Technique 41's earlier 253 — over 1,500 real
prints visually reviewed across the two sessions combined.

### A tool bug found and fixed while extending Technique 44 to gears

Slicing a real 0.15mm gear-mesh gap for a fresh check came back fused —
contradicting Technique 44's own control table, which said 0.15mm resolves.
That contradiction turned out to be real: `gcode_probe.py`'s default
rasterization (`px=0.15`) closes gaps up to ~0.3mm, aliasing right at the
range this whole technique measures. Full correction, control-table fix, and
the new "sweep px to convergence" rule are recorded under Technique 44 above,
not repeated here. The fix (`px=0.06` default, `--px` exposed) is what made
every gear-mesh measurement below trustworthy.

### Gears — real involute proportions, and a genuinely different "gear" shape

Downloaded a complete real planetary gear set (sun, planet ×1, ring, carrier
— separate parts, not print-in-place) and measured tooth geometry directly
off the mesh by sectioning perpendicular to the rotation axis and finding
radius peaks/troughs around the circumference:

| part | teeth | r_max | r_min | pitch r (est) | module (est) |
|---|---|---|---|---|---|
| sun | 26 | 29.00 | 24.66 | 26.83 | **2.06** |
| planet | 11 | 14.60 | 10.26 | 12.43 | **2.26** |
| ring (internal) | ~48–50 | — | — | ~52.4 | (2.0 implied) |

Both gears land on **module 2** within measurement noise, as they must to
mesh — and the classic planetary formula holds: `Z_ring = Z_sun + 2·Z_planet`
= 26 + 22 = 48, matching the ~48–50 measured. **This is the check to run on
any new gear train**: pick a module, and every meshing gear's tooth count
must satisfy this relationship or it won't fit.

**A "gear" is not always a spur gear.** A real drill-driven gear pump's
"Gear.stl" turned out to be a 6-lobe gerotor/rotor profile — broad rounded
lobes (radius swinging 9.88↔23.78mm, a 2.4× ratio no involute tooth ever
has), not fine teeth. For a pumping/rotary-displacement mechanism, model a
lobed rotor, not a toothed gear — they solve a different problem
(displacement vs. torque transfer) and look nothing alike up close even
though both get called "gears."

**Print-in-place planetary gear mesh clearance measured at 0.15–0.16mm** —
tighter than the 0.2mm ball-joint/snap standard from Technique 43, and
correctly so: a gear tooth only needs to clear its mating tooth's flank, not
a full ball escaping a socket. Verified real at the corrected slicing
resolution (`--px 0.04`): the mesh checked as 2–6 genuinely separate islands
depending on layer height (more at the tooth band, fewer where the carrier
plate legitimately fuses the planets together by design) — confirmed
correct, not the false single-island reading the uncorrected tool gave at
its old default.

### Brackets — two real gusset-weight-reduction strategies, neither a solid triangle

Measured a "corner bracket, optimized for 3D printing" (6,649 likes) by
computing the true silhouette (min/max Z per X bin across all Y, not a
single planar section — the shape isn't a pure extrusion). It is NOT a solid
flat gusset triangle: web thickness varies from a full 16mm at the flange
roots down to **2.5mm in the low-stress middle of the diagonal**, with a
genuine lightening hole cut through the thinnest region. Material sits where
the load path needs it and is removed everywhere else — a real
topology-optimized profile, not hand-drawn.

A second real bracket (a "Honeycomb Shelf Bracket," 531 likes) solves the
same problem a different way: a **solid perimeter frame carrying the load
path around the triangle's edge, with the entire interior gusset area
through-cut as a genuine hex lattice** — the exact Technique 21 hex-lattice
construction, confirmed here as a real structural gusset strategy, not only
a decorative vase/planter texture. Measured: 1.6mm min wall, 8.0mm median,
and only 9.6% of its downward area needs support despite the lattice —
consistent with the "design to print support-free" standard from
Technique 45.

**Both approaches soundly beat a solid flat triangle**, and they are not
interchangeable style choices — pick the topology-optimized variable-web
version when the load is genuinely concentrated along a known path (a
diagonal brace under one direction of load), and the perimeter-frame +
lattice version when the load is more evenly distributed and the *visual*
lightness matters as much as the weight (a shelf bracket meant to be seen).

Every bracket sampled shares the same skeleton regardless of gusset
strategy: two flat mounting flanges at 90°, each with 1–2 round or slotted
holes, joined by *some* form of a lightened diagonal web — never a solid
right-angle wedge.

### Cosplay/armor — always a segmented shell, never one hollow piece

Every wearable helmet or armor panel in the sample (dozens, from Spartan
helmets to sci-fi pauldrons) is split into **multiple curved shell panels
along visible seam lines** — never printed as one large hollow shell. This
is a real build constraint, not a style choice: a wearable helmet exceeds
the P1S's 256mm build volume in at least one dimension, and a single-shell
print of that size has no good print orientation (every face is a
compound curve, so any orientation puts large regions past a safe overhang
angle). Segmenting into panels solves both problems at once: each panel fits
the plate and can be oriented so its outer (visible) face prints support-free
against the direction of least curvature. Several panels show a locating
tab/pin pattern at the seam edge for glue-up alignment — the same
locate-vs-snap distinction from Technique 43 applied to a glued assembly
rather than a moving one.

### What to do differently, concretely

1. **Pick a module and verify tooth counts against the meshing formula**
   before modeling any gear train — `Z_ring = Z_sun + 2·Z_planet` for a
   planetary set, or the plain `pitch_dia = module × teeth` relationship for
   a simple pair. Don't guess proportions by eye.
2. **A rotary-displacement pump needs a lobed rotor profile, not gear
   teeth** — different mechanism, different shape.
3. **Gear-mesh clearance: 0.15mm**, not the 0.2mm ball-joint standard —
   confirmed at the corrected slicing resolution.
4. **Never model a bracket gusset as a solid flat triangle.** Either taper
   the web thickness to the real load path (thick at the flange roots, thin
   in the low-stress middle, optionally a lightening hole) or through-cut
   the interior as a hex lattice inside a solid perimeter frame. Pick based
   on whether the load is concentrated or distributed.
5. **Any wearable piece that could exceed ~200mm in a dimension gets
   segmented into shell panels along real seam lines**, each with its own
   safe print orientation, before modeling starts — not decided after
   discovering the first attempt doesn't fit the plate.

## Technique 47 — Fidget clickers: three real mechanism families, not one (2026-09-04)

Scott's follow-up to Technique 46: *"Research clickers also."* Fidget
clickers are their own real design niche on Printables (a "clicker" keyword
scan of ids 1,200,000–1,340,000 — the newest band, almost entirely
undownloadable per Technique 42's era limit — turned up 90 real candidates
after dedup). No full mesh geometry was downloadable for the true fidget-toy
examples (all in the non-derivable modern era, confirmed with direct probes
on five separate candidates, all 404), so this technique leans on two things
instead: real preview-image geometry at scale (90 images, both whole-print
thumbnails and, valuably, individual per-STL-file previews for multi-part
prints — Printables exposes a `filePreviewPath` per file, not just per
print, so a multi-file print's *internal mechanism parts* render separately
and are visible even when the print's outer shell isn't), and a real
industry engineering reference on snap-dome switches
(metal-domes.com's design guide, fetched and read in full). Facts below are
tagged by source; nothing here is asserted from a downloaded, measured mesh
the way Technique 46's gears were — that's the honest limit of what this
round could verify.

### The corpus

Same scan method as Technique 46 (GraphQL id sweep + keyword filter), one
new band: ids 1,200,000–1,340,000, filtered for "clicker"/"fidget click".
90 real, distinct prints survived dedup, likes ranging from 5 to 1,312.
Sorted by popularity, the top of the list is itself a finding — real working
titles, not invented categories:

| id | likes | name |
|---|---|---|
| 1282820 | 1,312 | Fidget Clicker Wheel 3.0 |
| 1212184 | 871 | spiky clicky stim toy |
| 1244780 | 813 | Cute Cat Paw Clicker – No Keyboard Switch Required |
| 1308207 | 782 | Fidget Toggle Switch Clicker – Print in Place |
| 1227432 | 513 | Cactus Fidget Clicker |
| 1264787 | 477 | Mario Mushroom Fidget Clicker |

Below the top few, the corpus splits cleanly into three mechanically
distinct families — not variations on one idea.

### Family 1 — bistable dome/membrane (snap-through buckling)

The largest visual family: a decorative body (flower, animal, food) hides a
thin curved shell that buckles between two stable states, giving the
"click" as elastic snap-through, not a moving part. Confirmed visually
across many independent designs (Cactus, Mario Mushroom, Tulip Clicker,
Capybara, Toucan, Wasabi, Easter Egg). Two real dome-shape variants both
appear in the corpus, not just one:

- **Scalloped/petaled rim** (the dominant variant) — the dome's edge is cut
  into a flower-like petal pattern rather than a plain circle. This reads as
  decoration but is very likely functional: a large, thin FDM shell needs
  more edge compliance than a small stamped-metal dome does to buckle
  reliably, and scalloping gives that flex while also constraining the
  buckle to a repeatable direction. Disguising the spring element as a
  flower/petal shape is why so many of these toys are flower- or
  plant-themed — the theme follows the mechanism, not the other way round.
- **Plain oblong/stadium dome** — also present (a clean thin curved
  stadium-shaped shell, no scalloping), matching the "oblong" shape
  metal-domes.com's guide lists as one of the four common real dome
  profiles (round, triangle, oblong, four-leg). Seen paired with a
  **socket ring carrying 3–4 short pillar legs** around its rim in a
  separate mechanism-part preview (from "Print-in-Place Fidget Clicky
  Gear," 1246751) — a printed analog of a real membrane-switch retention
  ring, holding the dome captive from beneath while leaving its center free
  to flex down. A flat hex plate with a small central boss (seen in another
  multi-part print) is the matching **mounting base** half of the same
  captured-dome subassembly — base plate + retention ring + free-flexing
  membrane, all three parts visible separately across different real prints.

**Sourced engineering framing (metal-domes.com, real industry guide, not
inferred):** a snap dome's key spec is **click ratio** = tactile drop ÷
total travel, with 40–60% called "balanced" (their worked example: 1.2mm
travel, 0.6mm drop = 50%). Common failure modes they name: misalignment,
wrong actuation force, incorrect spacing, skipping physical prototypes.
**Their numbers are for stamped stainless steel (SUS301/304) at
sub-millimeter scale and do not transfer directly to FDM plastic** — real
printed clicker domes run far larger (40–60mm) than any metal dome, because
a thick, stiff FDM wall needs a much bigger radius-to-thickness ratio to
buckle elastically at all without cracking. Treat "click ratio" as the right
*concept* to design around (how much of the travel is felt as a snap versus
soft compression), not the literal metal-dome dimensions.

### Family 2 — cantilever finger/comb spring array

A second, mechanically different family: instead of one buckling dome, a row
of **parallel flexible cantilever fingers** (a comb), each one flexing and
releasing independently. Directly confirmed on "Fidget Toggle Switch
Clicker – Print in Place" (1308207, 782 likes) — its preview shows an
interlocking comb of fingers, not a dome. The same rib/comb motif recurs
repeatedly as internal housing geometry across several other, unrelated
clicker prints (vertical fin arrays inside box housings) — this looks like a
generically reusable spring element for a printed switch, not a one-off.
Mechanically this is closer to a row of small cantilever snap-fit fingers
(Technique 43's cantilever math applies directly — beam length, thickness,
and material modulus set the flex force) than to true bistable buckling: a
comb gives a ratchet-like *series* of small clicks as fingers release in
sequence, where a dome gives one sharp bistable snap.

### Family 3 — sawtooth ratchet + spring pawl (the classic click-pen mechanism)

The single most popular design in the whole corpus (1282820, "Fidget
Clicker Wheel 3.0," 1,312 likes — nearly 1.5× the next entry) is neither a
dome nor a finger comb. Its main part preview is unambiguous: a wheel with
**sawtooth ratchet teeth cut around its full outer rim**, meant to spin
inside a two-piece case (`Case_M`/`Case_F`) against a spring pawl mounted on
a separate `InnerFrame` part — the exact kinematic of a retractable
ballpoint pen's click mechanism (rotating notched cam + flexing pawl), not a
push-button dome at all. This is not an isolated example: at least four more
independently-named designs in the same corpus use the identical
notch-and-pawl principle — "Fidget Clicker (Ratchet) – Simple and
Satisfying!" (1278237, explicitly named "Ratchet"), "Fidget Clicky Gear
{PRINT IN PLACE}" (958862), "Clicky Gear Fidget Toy [FAST PRINT]" (1020773),
and "CN3D Gear Clicker Key Tag" (996183) — four separate, popular, real
prints converging on the same non-dome, non-comb mechanism.

**A real design-practice finding worth copying directly:** the top design's
own file list ships **two versions of the moving wheel part at different
fits** — `Wheel_v3.0.stl` and `Wheel_tolerance0.1mm_v3.0.stl` — letting the
buyer pick based on how their own printer's tolerance runs. This is the same
principle behind this shop's own Gauntlet calibration tile (a swept ladder
of clearances so a buyer/printer finds their own working fit) converged on
independently by one of the most-liked designers on the platform — real
outside confirmation that "ship a tolerance ladder, don't guess one number"
is a sound practice, not just an internal habit.

### What to do differently, concretely

1. **"Clicker" is not one mechanism — pick a family deliberately.** Bistable
   dome (single sharp snap, quietest, best for a small toy), cantilever comb
   (a rippling series of smaller clicks, good for a wider/flatter form
   factor), or sawtooth ratchet + pawl (loudest, most mechanical-feeling,
   the only one of the three that naturally supports many clicks per
   rotation from one part). Choose based on the felt experience wanted, not
   by defaulting to whichever is easiest to model.
2. **A bistable dome for FDM needs a scalloped/petaled rim, not a plain
   circle**, unless it's built oversized (40mm+) as a plain oblong/stadium
   shape — a small plain-circle dome in stiff FDM plastic is unlikely to
   buckle reliably at hobby wall thickness.
3. **Build a captured-dome subassembly as three real parts**, matching what
   the corpus actually ships: a base plate with a central boss, a
   retention ring with 3–4 short pillar legs holding the dome's rim
   captive, and the free-flexing dome/membrane itself — don't try to mold
   the dome directly into a single-piece housing.
4. **For a ratchet mechanism, ship the moving part at more than one
   clearance** (a ~0.1mm spread, matching the top design's own two-file
   pattern) rather than committing to one dimension and hoping it fits every
   printer.
5. **This round's real limit:** every genuinely new fidget-clicker candidate
   sits in the non-derivable id era (Technique 42) — none of the actual
   toy meshes could be downloaded and measured directly, only their preview
   renders. The three-family split above is well-supported by many
   independent images and real product names, but treat exact tooth counts,
   wall thickness, and dome radius-to-height ratios for this category as
   still unverified against real geometry — a good target the next time a
   Printables session cookie or an older-era equivalent becomes available.

## Technique 48 — Real technique upgrades this shop hasn't used yet: fuzzy skin, TPMS infill, layered-color painting, embedded hardware, and a print-in-place gear-train mechanism (2026-09-04)

Scott: *"figure out if there's any new ways to print stuff that haven't been
done... structurally strong, makes sense, and very usable... very good at
details so that way our prints will look phenomenal."* This is a genuine
technique/process research pass (what the printer and slicer can DO), not
another geometry-corpus pass like Technique 41–47 — sourced from real,
citable research and Bambu/community documentation, verified against what
this shop's specific hardware (Bambu P1S, single hardened/brass 0.4mm
nozzle, AMS 4-slot) can actually run today. Every item below is flagged as
either **usable now, zero new hardware** or **out of reach on this printer**
— don't let "novel" read as "buy new equipment."

### Usable now — genuinely new to this shop, zero new hardware

**1. Layered-colour "filament painting" for true photographic/logo detail
(HueForge-style) — the single biggest "phenomenal detail" win available.**
A standalone free/paid tool (HueForge) takes a flat image and computes,
per-pixel, which stack of translucent filament layers and layer heights
reproduce its color and value using a CMYK-style optical-mixing model —
the same physical principle as a lithophane, generalized to full color
instead of grayscale. Output is a real, sliceable file with height-mapped
color-change instructions. **Confirmed compatible with this exact
hardware class**: HueForge's own 3MF Export Plugin reads the target
printer's AMS/CFS slot count directly from the imported profile and
inserts either an automatic AMS swap (when the printer has enough slots)
or a manual pause-and-swap prompt only for colors beyond the physical
slot count — so a 4-slot P1S AMS handles up to 4-colour photographic
prints **fully automatically**, no operator intervention mid-print. This
is a real, different-in-kind capability from anything in this shop's
current pipeline: a genuinely photorealistic image (a pet portrait, a
logo, a landscape) rendered as a flat backlit panel or a bas-relief
lithophane, using filament this shop already stocks. Where to apply it:
a backlit nightlight panel (pairs directly with the existing Mushie
lamp-shell work), a customer-photo memorial/pet portrait plaque, or a
logo medallion with real photographic shading instead of a flat engraved
mark.

**2. Fuzzy skin for texture and grip — a two-setting slicer change, not a
new model.** Bambu Studio's Fuzzy Skin (outer-wall-only, or walls+top)
randomly jitters the outer wall's toolpath within a small band, producing
a fine matte/grippy texture that also hides layer lines. Real, current
community use split into two clear categories worth applying deliberately
rather than as a novelty toggle: **functional** — extra grip on a handle,
knob, or phone-stand contact surface — and **material-mimicry** — an
uneven, slightly randomized surface reads as fur, bark, stone, or raw
metal far better than a smooth wall does, confirmed on real published
examples (ice-cream/plant-pot decorative prints, faux-metal enclosures).
**Directly relevant to this shop's own Technique 47 finding**: one of the
top-liked real keychains in this session's own corpus is explicitly named
"Bic Lighter Case Keychain ... Fuzzy Skin" — independent confirmation
this is a real, marketed differentiator buyers respond to, not an
internal guess. Apply per-surface (Bambu Studio supports painting fuzzy
skin onto specific faces via the same paint-tool UI as seam painting) —
never blanket the whole model, since a fuzzy-skin flat top loses the
crisp G2 surfacing this skill already invests in elsewhere (Technique 30).

**3. TPMS/gyroid infill as a genuine structural choice, not a default
percentage.** Real 2024–2026 mechanical testing (cited below) confirms
gyroid infill is the most **isotropic** common infill pattern — it
distributes load roughly evenly across all three axes because its
surface has no flat parallel planes to concentrate stress the way grid/
line infill does, while a simple grid is strongest along its own two
printed axes and comparatively weak on a diagonal/twisting load. Cubic
infill can still edge out gyroid on raw compressive tensile strength at
very high density (~80%) in some published tests, so gyroid is not
universally "the strongest" — its real advantage is **not caring which
direction the load comes from**, which matters specifically for a part
handled/dropped/twisted in unpredictable ways (a toy, a keychain, a
carried tool) rather than a part loaded in one known, fixed direction
(a bracket, per Technique 46, where a directional web/lattice beats
uniform infill anyway). **Recommended default going forward for anything
without a single dominant, known load direction: gyroid, 20–35%, 4 walls,
5 top/bottom layers** — matching the real published recommendation, and a
real change from this shop's prior unstated default.

**4. Embedded hardware, with real numbers instead of guessed clearances.**
Two techniques already conceptually known in this shop (mentioned in
passing) but never given real design numbers — worth having on hand:
- **Heat-set threaded inserts**: bore a straight (not tapered) blind
  hole, sized to the specific insert (never guessed), roughly 1mm deeper
  than the insert's own length, no chamfer at the hole mouth. Press in
  with a heated tip (a soldering iron at low heat, or a purpose tip) —
  never a soldering-iron-hot embed near an already-placed magnet in the
  same part (next point).
- **Embedded magnets**: cavity = magnet diameter/thickness **+0.2–0.4mm**
  for a snug press fit, **1–2mm minimum wall** around the pocket to keep
  it structurally sound, and — a real, easy-to-miss trap — never heat-set
  an insert near an already-embedded magnet in the same print: a
  soldering iron's tip runs well past 200°C, comfortably above the
  demagnetization threshold of a standard neodymium magnet. Sequence
  magnet-then-insert operations by which one goes in last, or keep them
  physically far apart in the design.

### A genuinely new mechanism family for THIS shop, confirmed via real geometry

Extending Technique 47's clicker-family research to the broader toy/
fidget corpus (see Technique 49 below for the full toy/keychain pass)
turned up a fourth real mechanism family that Techniques 20/22/29/40/43's
existing taxonomy (hinge, bayonet, ball-joint, leadscrew) doesn't cover:
**a captive print-in-place planetary or idler gear train, sized as a
handheld spinner/fidget rather than a functional drivetrain.** Two real
examples measured visually: "Fidget Gear Ring" (5,097 likes) — a torus
with a full ring of small meshing gear teeth captive inside its bore,
grip dimples on the outer face — and "Planetary Gear Fidget Toy" (2,568
likes) — a coin-disc with a real sun+4-planet+ring gear train visible
through cutouts in the front face, knurled rim for grip. Mechanically
this reuses Technique 46's real planetary-gear math (`Z_ring = Z_sun +
2·Z_planet`, module chosen once and held for every meshing gear) and
Technique 44's corrected 0.15mm gear-mesh print-in-place clearance
exactly — the novelty here is entirely in the USE CASE (a satisfying
"watch it spin" toy/keychain, not a torque-transferring drivetrain), so
no new mechanical technique needs inventing, just a new application of
what Technique 46 already measured. Worth pitching as a future keychain/
fidget concept specifically because it's a real, popular, structurally-
proven mechanism this shop has the exact math for and has never applied
to a small handheld form factor.

### Out of reach on this printer — real, but not a false promise to Scott

**Non-planar / conformal slicing** (varying Z height across a single
layer to follow a curved surface instead of flat planes) is real, active
research with strong, well-documented results — one framework reports up
to 6.35× strength increases by aligning filament paths with the direction
of greatest stress, and non-planar top surfaces measurably reduce the
staircase effect and improve surface finish at shallow inclination angles
(≤25°, with benefits continuing up to 55°). **None of this is available
in Bambu Studio today.** The published implementations are custom
slicing frameworks/multi-axis or 5-axis printer setups, not a toggle in
a standard slicer profile — flag this honestly as "real, tracked,
currently unusable on the P1S's standard 3-axis motion + Bambu Studio,"
not as something to promise a customer or build toward without a real
hardware/software path. Worth re-checking again in a future research pass
if Bambu Studio ever ships a non-planar mode, but don't spend build time
chasing it now.

### What to do differently, concretely

1. **Pitch a HueForge-style layered-colour panel as a real new product
   concept** (per the standing "pitch before modeling" rule) — this is
   the one finding in this pass most directly answering "make our prints
   look phenomenal," and it needs zero new printer hardware.
2. **Default new models without a single dominant load direction to
   gyroid infill, 20–35%, 4 walls, 5 top/bottom layers** — a real,
   sourced upgrade over an unstated default.
3. **Apply fuzzy skin per-surface via Bambu Studio's paint tool**, on
   grip/handle surfaces or material-mimicry surfaces specifically — never
   as a blanket setting, and never on a surface this skill's G2 surfacing
   work (Technique 30) is already carrying.
4. **Use the real embedded-hardware numbers above** (insert bore = insert
   length + 1mm, straight/no chamfer; magnet pocket = magnet size +
   0.2–0.4mm, 1–2mm wall) instead of guessing on the next design that
   needs a fastener or a magnetic catch.
5. **A captive gear-train spinner (ring or coin form factor) is a real,
   proven, structurally-solved keychain/fidget concept** ready to pitch —
   reuses Technique 46's gear math and Technique 44's corrected mesh
   clearance directly, nothing new to derive.

Sources for the sourced (not visually-inferred) claims above: gyroid/TPMS
comparative strength — [Zbotic infill comparison](https://zbotic.in/slicer-infill-patterns-compared-which-is-strongest-and-fastest/),
[PMC TPMS gyroid optimization study](https://pmc.ncbi.nlm.nih.gov/articles/PMC11053662/),
[ScienceDirect FDM infill mechanical properties](https://www.sciencedirect.com/science/article/pii/S0142941822001787);
non-planar printing — [3D Printing Industry, 6.35x strength framework](https://3dprintingindustry.com/news/researchers-achieve-6-35x-part-strength-increases-with-new-non-planar-fdm-framework-175248/),
[ScienceDirect non-planar surface quality study](https://www.sciencedirect.com/science/article/pii/S2590123025043178);
fuzzy skin — [How-To Geek](https://www.howtogeek.com/fuzzy-skin-best-3d-printing-trick/),
[Bambu Lab forum, fuzzy skin textures](https://forum.bambulab.com/t/new-fuzzy-skin-textures-for-2-5-3/249218);
HueForge/AMS — [HueForge 3MF Export Plugin](https://shop.thehueforge.com/pages/3mf-export-how-it-works),
[About HueForge](https://shop.thehueforge.com/pages/about-hueforge);
embedded hardware — [Hackaday, embedding magnets](https://hackaday.com/2026/06/04/ways-to-embed-magnets-in-3d-prints-and-not-ruin-printers/),
[CNC Kitchen, heat-set inserts](https://www.cnckitchen.com/blog/tipps-amp-tricks-fr-gewindeeinstze-im-3d-druck-3awey).

## Technique 49 — Kids' toys and keychains: real safety rules and real design conventions from 49 measured/visual real prints (2026-09-04)

Same session, second half of Scott's request: *"research how to 3-D print
toys fun things for kids and keychain."* Two distinct bodies of evidence:
sourced safety standards (real, citable, non-negotiable), and a fresh
49-print visual pass across this shop's own 12,276-record Printables
corpus (Technique 46's cache, filtered for zero new API calls) plus
individual preview images for the mechanically-interesting ones.

### Kids' toys — the safety rules are real regulatory standards, not style guidance

Two real standards bodies govern this, cited directly rather than
paraphrased from memory:

- **ASTM F963 / CPSIA (US)** and **EN 71-1/-2 (EU)** both regulate small
  parts, sharp edges/points, and flammability. The relevant mechanical
  test for choking hazard is the **US CPSC small-parts cylinder, 16 CFR
  Part 1501** — a real, checkable physical test fixture, not a vague
  "make it big enough" rule.
- **The FDM-specific risk is layer adhesion, not just part size.** A
  print that passes a size check can still shed a sharp, brittle
  fragment along a weak Z-layer bond if bitten, dropped, or repeatedly
  flexed — this is a materials/process risk a resin or injection-molded
  toy doesn't share, and it means a toy aimed at a child under 3 needs
  **zero small or detachable parts, full stop** (no glued-on eyes, no
  separate small props, nothing that can snap off along a layer line and
  present a fresh sharp edge).
- **Concrete design rule for this shop's own age-3+ audience**: round
  every exposed edge/corner (this skill's own G1/G2 surfacing work from
  Technique 30 already does this for aesthetic reasons — it is now ALSO
  a safety requirement, not just a look), avoid any single feature
  thinner than roughly 3–4 perimeter-widths (~1.2–1.6mm) in a load path a
  child might flex or chew, and treat any part smaller than the CPSC
  cylinder test as a hard no regardless of how it's attached.
- **Filament choice**: PLA/PETG are the standard non-toxic choices for
  this category — already this shop's default material, no change
  needed — but "the filament is non-toxic" and "the finished PRINT is
  age-safe" are two different claims; the second depends on the specific
  design (thickness, part count, edges), not just the material spec
  sheet.

### Toys and keychains, from real measured/visual geometry (49 prints, this session)

Filtered this shop's existing 12,276-record Printables cache (zero new
API calls) for toy and keychain keywords: **844 toy matches, 604
keychain matches.** Reviewed the top ~50 by likes as full preview images
(both whole-print thumbnails and, for the mechanically interesting ones,
individual close-ups) — real, popular, currently-selling designs, not
invented categories.

**1. Flexi articulated creatures are not just a toy category — they are
THE dominant keychain form factor.** Of the top real keychains by likes,
a large majority are articulated print-in-place creatures (bone dragon,
forest dragon, Tardigrade, baby bull dragon, articulated dragon, flexi
platypus, articulated octopus) — directly confirming this shop's own
Technique 40/41/42 flexi-joint research is not academic: it is the exact
mechanism the keychain market already runs on. **A keychain is one of
the best-fit products for everything already measured in this skill's
ball-and-socket joint work** — no new mechanism needed, just a smaller,
keychain-scaled application of Technique 43's corrected slot-socket
standard (`sock_l=1.6D, sock_h=1.073D, mouth=0.833D, clearance=0.0413D`)
with a real attachment loop added (next point).

**2. Keychain attachment loop — real, sourced numbers, not a guess.**
For a standard split-ring: **hole diameter ≈ 4–5mm**, **≥3mm of solid
wall around the hole** (the loop is the single weakest point on almost
every keychain design, and under-building it is the #1 real failure
mode). The underlying rule, worth deriving rather than memorizing:
`hole_diameter = (strands_through_hole × wire_thickness) + ~1mm
clearance` — a standard split ring is a DOUBLED loop of wire (two
strands occupy the hole, not one), which is exactly why a 3mm hole feels
tight and 4mm is the real minimum that "just works."

**3. A genuinely new-to-this-shop mechanism family, confirmed via real
geometry: captive gear-train spinners.** "Fidget Gear Ring" (5,097
likes) and "Planetary Gear Fidget Toy" (2,568 likes) — full writeup and
sourcing under Technique 48 above, cross-referenced here because it
surfaced from this same toy/keychain pass, not the process-research half.

**4. Functional (non-toy) keychains are a real, distinct, high-like
sub-category worth keeping separate from character/fidget pieces**:
"KeyCarry EDC Key Organizer" (1,878 likes, M3-screw-compatible multi-key
holder), "Mini Bit Driver Keychain" (1,944 likes), "Würth keychain
screwdriver" (1,908 likes), "Blood Type Keychain with NFC Tag" (1,101
likes — a real embedded-electronics keychain, pairing directly with this
shop's own embedded-hardware numbers above). These sell on genuine
day-to-day utility, not cuteness — a different value proposition from
the flexi-creature category, worth having at least one candidate in each
bucket rather than only building character pieces.

**5. Ball-joint chibi proportions hold outside the flexi-spine category
too.** "Mini Articulated Robot" (2,228 likes) uses the exact chibi
proportion rule already in this skill (Technique 40's "head-to-body 1.5–2:1,
oversized round head") on a fully ball-jointed multi-limb figure rather
than a flexi spine — confirms the proportion rule generalizes across
articulation mechanism, not just to the flexi-spine creatures it was
originally measured from.

**6. Market-side confirmation, sourced**: keychains carry **80–90% profit
margins** on $0.20–$1 material cost against $3–$12 typical sale price —
among the best margin categories this shop could add, and personalization
(name plates, custom text) and licensed/character fidget designs
(Pokemon evolutions, anime keychains) are the two named 2026 trend
buckets, alongside practical items (phone stands, organizational tools)
consistent with finding #4 above.

### What to do differently, concretely

1. **Any toy aimed at under-3 gets zero small/detachable parts** — this
   is a hard CPSC/ASTM rule, not a style preference; check every design
   against the small-parts cylinder test conceptually before pitching it.
2. **Build the next keychain on Technique 43's slot-socket ball-joint
   standard, scaled down**, with a real 4–5mm split-ring hole and ≥3mm of
   wall around it — don't re-derive either number from scratch.
3. **Pitch at least one functional (non-character) keychain concept**
   alongside any character/fidget pitch — EDC organizer, bit driver, or
   a small embedded-magnet catch (Technique 48's numbers) are all real,
   proven, higher-utility alternatives to another flexi animal.
4. **The captive gear-ring spinner is a real, doubly-confirmed concept**
   (popular on Printables, mechanically solved by this shop's own
   Technique 44/46 gear-mesh math) — a strong candidate for the next
   concept pitch under the standing "propose before modeling" rule.

Sources: [ASTM/CPSIA/EN71 toy safety overview, Polymaker](https://wiki.polymaker.com/polymaker-products/more-about-our-products/safety-in-3d-printing/child-and-toy-safety),
[3D printing toy safety materials](https://www.aoseed.com/blogs/aoseed-sale/3d-printing-safety-materials-safe-for-childrens-toys-explained-6),
[Custom3DToys safety guide](https://custom3dtoys.com/blogs/news/safety-of-3d-printed-toys);
keychain hole sizing — [QIDI keychain hole guide](https://qidi3d.com/blogs/guides/add-hole-to-3d-model-keychain),
[Siraya Tech keychain guide](https://siraya.tech/blogs/news/3d-printed-keychain);
market/margin data — [eufyMake best-selling 3D print items 2026](https://www.eufymake.com/blogs/business-ideas/best-3d-print-sell-profitable-items).

## Technique 50 — Miniature figure anatomy: fairies, gnomes, and real human proportion, and which of the three is actually buildable in OpenSCAD (2026-09-04)

Scott: *"Research miniature figures... fairies, gnomes, actual people get
their body structures down... understand exactly how to detail design
them."* Combines a real proportion-canon research pass (sourced, for real
human anatomy and real gnome/fairy design conventions) with a 26-image
visual pass across this shop's own Printables corpus, and — the most
load-bearing finding — an honest read of which of the resulting styles
this shop's actual toolchain (OpenSCAD + BOSL2 CSG) can build well versus
which one needs the not-yet-built Blender handoff already scoped in
`ENGINEERING_REFERENCE.md` §1.

### Three real, distinct commercial figure styles — not one "miniature figure" category

Visual review of 26 real figures/statues (chess pieces, movie-license
minis, garden gnomes, modern decor sculpture) sorts cleanly into three
families that use different geometry and different skill:

1. **Chibi / "soft clay" whimsical** — Mini Vader (1,741 likes), Mini
   Mandalorian (867), Yoda (642), Mini Stormtrooper (628), Grumpy Cat
   Figurine (1,937), and the garden gnome family below. A dominant
   oversized head or hat, a single unbroken torso blob with no visible
   waist, short stubby non-articulated limbs, minimal separate finger/
   joint detail. **This is exactly this shop's existing hull()-chain
   toolkit** — the same technique already used for the fox (Technique
   27/28) and seahorse (Technique 40): a handful of hulled spheres for
   the body, one dominant sphere/cone for the head or hat, stub cylinders
   for limbs. Nothing new to invent here; it's the shop's strongest
   existing style, confirmed independently popular across 5 unrelated
   real licensed-character lines.
2. **Realistic / dynamic-pose action figure** — Samurai Warrior Figurine
   (995 likes), Vyke Elden Ring Statue (131). Real human proportions
   (roughly the classical 7–8 head-unit canon, not chibi), an asymmetric
   dramatic pose, flowing cape/scarf cloth, fine armor-plate and
   musculature surface detail. **This is a mesh-sculpting problem, not a
   CSG problem** — see the tool-choice verdict below.
3. **Minimalist / geometric sculptural** — ANGEL Figurine (687, smooth
   continuous draped-robe abstraction with no facial detail), Modern
   Black Cat Figurine (1,116, sleek continuous-curve silhouette), Modern
   Elephant Figurine (1,213), Geometric HORSE Figurine (1,427, deliberate
   low-poly faceted planes mid-gallop). **This is squarely within
   OpenSCAD's existing swept/lofted-profile toolkit** — `path_sweep()`/
   `skin()` for the smooth-abstraction sub-style (this shop's ghost/
   pumpkin/seahorse work already proves this out), or a handful of
   explicit `polyhedron()` facets for the deliberate low-poly sub-style
   (a genuinely different, currently strong, decor-market trend — sells
   on silhouette and finish, not anatomical fidelity, so it doesn't need
   fine detail work at all, just a confident, well-chosen facet count).

### The real proportion math, sourced, for whichever style needs it

**Classical human canon (Loomis / Polykleitos head-unit system, sourced):**
the "head" (crown to chin) is the base unit; an idealized heroic adult
figure is **8 head-units tall** — a real, citable canon used for
centuries specifically to make a figure read as noble/elevated rather
than naturalistic. Sub-divisions from the same tradition worth having on
hand for a style-2 (realistic) figure: eye-line sits at the head's own
vertical center: use these only if a genuinely realistic human figure is
attempted (style 2) — a chibi/gnome figure (styles 1) deliberately
violates every one of them on purpose.

**Chibi ratio, already in this skill (Technique 27/29/40), now cross-
confirmed by an unrelated real corpus**: head:body roughly 1.5–2:1 for a
"cute collectible" chibi. **The garden gnome sub-style pushes this
further** — visual review of the "Whimsical Clay Style" garden gnome
family (5 real, currently-listed designs, ids 1322038/1323089/1323040/
1322121/1324223, 30–126 likes) shows a torso-to-hat ratio closer to
**1:1 or the hat even dominating** — the conical hat alone is often
taller than the entire body beneath it, with the body itself a single
rounded blob with no visible waist or neck. This is a visual estimate
(these ids are all in Technique 42's non-derivable modern era, so no
real mesh measurement was possible this round) but is consistent across
all 5 independently-posed family members, which is a decent signal on
its own.

**Real, sourced garden gnome design convention (not invented, not a
generic "gnome" guess):** the modern garden gnome's visual language
traces directly to Rien Poortvliet's 1976 illustrated book *Gnomes*
(with Wil Huygen) — a real, hugely influential source (#1 New York Times
bestseller for over a year) that fixed the now-standard look: **tall red
conical cap, blue tunic, brown belt, grey boots, white beard** — tracing
even further back to a 470 AD description of "a miniature person who
wore a red cap and blue shirt and had a white beard." **Building a
garden gnome without this palette/silhouette is building something
buyers won't recognize as a gnome at all** — the red hat + white beard +
belted tunic combination is the actual product, not an arbitrary style
choice, the same way this shop's own kawaii palette rules (CLAUDE.md's
Color Design System) are non-negotiable brand language, not decoration.

**Fairy anatomy, sourced framework (no single canonical proportion the
way gnomes/humans have one — fairies are deliberately more license-able):**
real convention across sourced fairy-design guides is **human-like
slender proportions with deliberately elongated limbs** for grace, and
**wings attached from the upper back, just below the shoulder blades**
(not the shoulders themselves) — mechanically the right place to model
a wing root in a swept/lofted OpenSCAD body, matching the same "give a
mechanical/structural feature its own dedicated attachment, don't distort
the body around it" principle already established in Technique 32.
**Wing silhouette is a real, sourced characterization tool, not just
decoration** — soft/rounded wings read as innocent/kind, sharp/angular
wings read as dark/villainous, elongated wings read as royal/ethereal,
tattered/asymmetric wings read as aged or battle-worn. Pick the wing
shape to match the character brief before modeling, the same way this
skill already treats silhouette as a design decision (Technique 31) —
don't default to one generic butterfly-wing shape regardless of the
character.

### Tool-choice verdict for this category, stated plainly

This skill's own `ENGINEERING_REFERENCE.md` §1 already settled this in
general terms ("freeform sculpted asymmetry... is fundamentally a
mesh-sculpting problem" for Blender, not CSG) — this research confirms
it specifically for miniature figures:
- **Chibi and geometric/minimalist styles: stay in OpenSCAD.** Both are
  well inside the hull-chain / swept-profile toolkit this shop already
  has proven working examples of.
- **A genuinely realistic human figure with real musculature, cloth-fold
  detail, and an asymmetric dynamic pose (style 2 above) is NOT a good
  CSG target.** Don't attempt to hand-build a samurai's flowing cape or
  a face with real anatomical detail as OpenSCAD primitives — that is
  exactly the class of problem `ENGINEERING_REFERENCE.md` already flags
  for the (not-yet-built) OpenSCAD-block-out → Blender-Subdivision-
  Surface → re-export pipeline. If a style-2 figure is ever actually
  wanted, build that pipeline first rather than fighting CSG for months
  to approximate it badly.

### What to do differently, concretely

1. **Default new "cute figure" pitches to style 1 (chibi) or style 3
   (geometric/minimalist)** — both are provably buildable at this shop's
   current skill level and both are independently confirmed popular by
   real, unrelated products.
2. **Any garden gnome design must hit the real Poortvliet palette/
   silhouette** (red cap, blue tunic, brown belt, grey boots, white
   beard) to read as a gnome at all — treat this as fixed brand language
   for the character, not a style option.
3. **Build one parametric gnome base, not five bespoke models** — the
   real family (Chubby/Elderly/Explorer/Bearded, 5 named variants from
   one designer) is exactly this skill's own Technique 41 "sets sell,
   parameterize for the family from the outset" finding applied to this
   category: one hull-chain body + swappable head/prop/pose parameters.
4. **A fairy needs its wing style chosen deliberately per the character
   brief** (soft/round = innocent, sharp/angular = dark, elongated =
   ethereal/royal) and attached as its own dedicated feature at the
   upper back below the shoulder blades — not bolted onto wherever looks
   convenient after the body is finished.
5. **Never attempt a realistic style-2 human figure in pure OpenSCAD
   CSG** — if that style is ever greenlit, build the Blender-handoff
   pipeline first (per `ENGINEERING_REFERENCE.md` §1), rather than
   spending build time re-discovering that CSG can't do it.

Sources: [Anatomy4Sculptors, human proportions](https://anatomy4sculptors.com/blog/about-human-proportions-calculator/),
[Sculpture Atelier, canon of proportions](https://www.sculptureatelier.com/blog/canon-of-proportions-sculpture),
[Wikipedia, body proportions / 8-head canon](https://en.wikipedia.org/wiki/Body_proportions);
gnome history — [Wikipedia, Rien Poortvliet](https://en.wikipedia.org/wiki/Rien_Poortvliet),
[Wikipedia, Gnomes (book)](https://en.wikipedia.org/wiki/Gnomes_(book)),
[The Garden History Blog, origins of garden gnomes](https://thegardenhistory.blog/2022/03/05/the-origins-of-garden-gnomes/);
fairy design — [Unvale, designing a fairy OC](https://blog.unvale.io/tips-for-designing-a-fairy-oc/),
[Foxsy, fairy proportions and poses](https://foxsy.com/courses/introduction-to-drawing-fairies-proportions-and-poses/).

## Technique 51 — Garden accessories and statues: what's actually evergreen, and the material constraint that changes everything (2026-09-04)

Second half of the same request: *"research garden accessories, as far as
statues, things that we can sell, that will be popular, that will never go
away."* Two real findings, one of them a hard material constraint this
shop's entire existing product line has never had to deal with.

### The real evergreen categories, sourced

Cross-referencing real bestseller-tracking sources (Amazon/Home Depot/
Wayfair garden-statue bestseller categories) rather than guessing:

- **Classic nature/animal motifs, not novelty**: frog statues (family
  sets, and stacked-frog designs with solar-lit eyes as the modern
  update), turtle and butterfly statuary, geese, roosters, peacocks.
  These are described directly as evergreen specifically **because**
  they're classic animal/nature motifs on durable, weather-resistant
  finishes — the design itself doesn't chase seasonal trends, only the
  finish/material needs to be genuinely durable (next section).
- **The garden gnome itself is the single most durable archetype in this
  entire category** — a 50-year-old illustrated book (Technique 50's
  Poortvliet source) still defines what "garden gnome" means to a buyer
  today. This is about as close to a proven-evergreen SKU as this
  research turned up anywhere in either research pass this session.
- **A light/solar element is the real "modern update" pattern, not a
  redesign of the classic form** — real bestsellers pair a traditional
  animal/gnome silhouette with a **solar light or LED accent** (solar
  peacocks, solar-lit stacked frogs) rather than reinventing the
  silhouette. This is a genuine, low-risk way to differentiate a classic
  design without abandoning the archetype that makes it sell.
- **Fairy-garden micro-accessories are a real, distinct, currently
  strong sub-niche this shop has not touched at all**: toadstool/
  mushroom houses (confirmed in this shop's own corpus — "Mushroom
  house / toadstool jewelry organizer," 114 likes — a real, currently
  popular motif already being reused across product categories),
  miniature fairy doors, tiny furniture, and stone-circle/miniature-
  henge props (this shop's own corpus: "Fairy Circle / Stone Henge
  Miniature," 217 likes). These are small, fast, low-material-cost
  prints — a strong complement to this shop's existing digital-planner
  economics (low COGS, high margin) rather than a competing large-format
  product line.

### The hard constraint this category adds: material, not geometry

**Every design this shop has built so far (Mushie, the flexi creatures,
the snap box, the ball-joint chain) has been implicitly indoor-only, in
PLA.** A garden accessory changes that assumption completely, and it's a
real, sourced, non-negotiable constraint, not a style preference:

| Material | Outdoor UV/weather performance |
|---|---|
| **PLA** | Not viable outdoors at all — this shop's current default material has no place in this product category |
| **PETG** | Moderate UV stability; **noticeably degrades within about a year** of real outdoor sun exposure |
| **ASA** | The real right answer — **maintains structural integrity, color, and surface quality after 12 months of full UV exposure**, in conditions where PETG has already visibly degraded |

**Concretely: any garden/outdoor product this shop builds must be
specified and quoted in ASA, never PLA, and the listing/product notes
need to say so explicitly** — this is a genuine "never lie to the
customer" issue (per this codebase's top-priority rule) if a garden
statue were ever accidentally printed and sold in PLA and failed outdoors
within weeks. The P1S's full enclosure (already in this shop's hardware,
per the root CLAUDE.md printer spec) is exactly what ASA needs to print
well — no new hardware required, just a real material-selection
discipline that doesn't exist yet for any current product.

**Outdoor-specific geometry rules, beyond material** (general DfAM
knowledge, applied to this category specifically): design in real
drainage wherever a horizontal surface could hold rainwater (a gnome's
hat brim, a base plate, a birdbath bowl's own rim) — trapped water that
freezes can crack a part regardless of material, and a small drain hole
is nearly free to add and never optional for an outdoor part with any
flat-ish upward face. A base thick enough to resist wind-tip (a real
outdoor failure mode indoor decor never faces) is also worth checking
explicitly — model the base as its own named dimension (per this skill's
"no magic numbers" rule), sized to the piece's real height/wind-catching
silhouette, not copied from an indoor piece's base proportions.

### What to do differently, concretely

1. **Any garden-category pitch is quoted and printed in ASA, never
   PLA** — a hard, sourced material rule specific to this product
   category, distinct from every indoor product this shop has built so
   far.
2. **Lead with a classic animal/nature motif or the gnome archetype**,
   not a novel silhouette — the evidence says the archetype itself is
   what's evergreen, not any particular designer's reinterpretation of it.
3. **Add a solar-light or LED accent as the differentiator**, reusing
   this shop's own real lamp/lighting work (Mushie's diffusion-strategy
   research, Technique 29) rather than redesigning the classic silhouette.
4. **Pitch the fairy-garden micro-accessory line as a real, low-risk
   complement to the existing digital-product economics** — small,
   fast, cheap prints (toadstool houses, fairy doors, miniature henge
   props) rather than one large-format statue as the first garden SKU.
5. **Design real drainage into every outdoor-facing horizontal surface**,
   and size the base against the piece's own real height/silhouette
   rather than reusing an indoor piece's base proportions.

Sources: [Sagebrook Home, best garden statues 2026](https://sagebrookhome.com/blogs/best-garden-statues-buy/),
[ASINsight, best-selling garden statues by real sales](https://www.asinsight.com/report/US/garden-statues);
material — [MatterHackers, best filament for outdoor use](https://www.matterhackers.com/articles/the-best-3d-printing-filament-for-outdoor-use),
[Sovol3D, ASA vs PETG vs ABS outdoor comparison](https://www.sovol3d.com/blogs/news/best-filament-for-outdoor-3d-prints-asa-vs-petg-vs-abs),
[MakeLab, PETG vs ASA](https://www.makelab.com/compare/petg-vs-asa).
