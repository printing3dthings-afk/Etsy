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
| Max overhang without supports | 55° from vertical | Steeper than that either needs supports (extra post-processing, worse surface) or a redesigned angle/orientation |
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

## The one rule that matters most

**A clean OpenSCAD render (no errors, non-zero output size) is not proof
the model is correct.** Every bug this skill documents rendered without
error — including one that rendered a **completely empty model** with exit
code 0. The only way any of them were caught was generating a real PNG
(`fmt="png"` — works headless now, see Setup above) and looking at it
from more than one angle. Do that for every new model before describing it
to Scott as ready.
