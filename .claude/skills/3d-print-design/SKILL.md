---
name: 3d-print-design
description: "Real technique for designing genuinely printable 3D models in OpenSCAD -- both functional/practical parts (organizers, brackets, holders) and decorative/organic parts (vases, bowls, shades) -- grounded in this shop's real Bambu Lab P1S constraints and in specific OpenSCAD/CGAL pitfalls found and fixed while building the first real models. Load this whenever writing a .scad script for render_openscad_model / tools/openscad_render.py."
---

# 3D Print Design — OpenSCAD, For Real Printable Models

## Why this exists (2026-08-21)

Before this skill, `render_openscad_model` could render *any* valid OpenSCAD
script, but nothing in this codebase captured what makes a script produce a
model that's actually good — printable without supports where avoidable,
structurally sound, and visually correct rather than subtly broken in a way
that only shows up when you actually look at the render. Three real,
non-obvious bugs were found and fixed building the first two real test
models (a hollow vase, a desk organizer) before this was written down:

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

None of these three produced an OpenSCAD error. All three were only caught
by actually rendering a PNG and looking at it — which didn't even work in
this container until the headless-rendering fix below shipped. The
discipline this skill exists to enforce: **never call a 3D model done from
reading the .scad source. Render a PNG and look at it, the same
"verify before reporting success" rule this shop already applies to AI
photos and Etsy mutations.**

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

## Bambu P1S constraints — design within these, don't guess

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

## The one rule that matters most

**A clean OpenSCAD render (no errors, non-zero output size) is not proof
the model is correct.** All three bugs this skill documents rendered
without error. The only way any of them were caught was generating a real
PNG (`fmt="png"` — works headless now, see Setup above) and looking at it
from more than one angle. Do that for every new model before describing it
to Scott as ready.
