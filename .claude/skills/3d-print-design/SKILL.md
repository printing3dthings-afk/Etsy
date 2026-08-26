---
name: 3d-print-design
description: "Real technique for designing genuinely printable 3D models in OpenSCAD -- both functional/practical parts (organizers, brackets, holders) and decorative/organic parts (vases, bowls, shades) -- grounded in this shop's real Bambu Lab P1S constraints and in specific OpenSCAD/CGAL pitfalls found and fixed while building the first real models. Load this whenever writing a .scad script for render_openscad_model / tools/openscad_render.py. For general DfAM judgment and Bambu Studio slicer settings (calibration, per-material presets, strength/wall settings, tolerances, orientation), see data/knowledge_base/3d_printing_expertise.md alongside this skill."
---

# 3D Print Design — OpenSCAD, For Real Printable Models

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

## The one rule that matters most

**A clean OpenSCAD render (no errors, non-zero output size) is not proof
the model is correct.** Every bug this skill documents rendered without
error — including one that rendered a **completely empty model** with exit
code 0. The only way any of them were caught was generating a real PNG
(`fmt="png"` — works headless now, see Setup above) and looking at it
from more than one angle. Do that for every new model before describing it
to Scott as ready.
