include <BOSL2/std.scad>

// ============================================================
// "Cloudy" desk organizer -- deliberately simple, on-brand kawaii
// pastel piece for OnBrandCraftz's own physical-product line. Built
// after the Mochi Fox spent most of its budget on bugs caused by
// TAPERING geometry (a hull-chain that drops in Z while advancing in Y
// bulges its surface in ways that aren't analytically obvious -- see
// mochi_fox_organizer.scad's Technique 28 postmortem). This design
// avoids that whole bug class on purpose:
//   - The cloud body is a plain union() of overlapping spheres, all
//     centered on the SAME y=0 plane -- no hull(), no tapering axis,
//     so every front-surface cut is a single sphere's own equation,
//     solvable exactly by hand (no "measure the mesh first" step
//     needed the way the fox's tapered muzzle required).
//   - The face sits entirely on ONE sphere (the center lobe) -- not
//     spread across a multi-point chain the way the fox's eyes/cheek
//     had to hunt for a safe segment.
// One printed part. Function: a pen/pencil cup cut into the top of the
// center lobe, sized for real desk use (not a cavernous pit -- see the
// fox's own pen-cup postmortem on getting that proportion wrong first).
// ============================================================

$fn = 64;   // smooth without the fox's ~90s-per-render cost at fn=96

// ---- base plate ----
base_w = 104; base_d = 62; base_h = 6; base_round = 26;

// ---- cloud lobes: union of spheres, all at y=0, embedded base_h-2 ----
// (x, r) pairs -- z is derived so every lobe's bottom sits base_h-2
// (2mm embed into the base plate, matching the base_plate's own
// verified-safe embed depth from the fox build).
lobe_embed = 2;
function lobe_z(r) = base_h - lobe_embed + r;
lobes = [   // [x, r]
    [-24, 13],
    [-11, 19],
    [  0, 23],   // center -- carries the face and the pen cup
    [ 11, 19],
    [ 24, 13],
];

// Smooth transitions between lobes (2026-08-28) -- a real engineering
// dead-end worth recording so it isn't re-attempted blind next time:
//   1. hull() between adjacent pairs -- WRONG. A full hull between two
//      whole spheres is their convex hull, filling the entire concave
//      valley between them, not just the crease -- erased the lobed
//      "cloud" silhouette into one plain dome (confirmed by rendering).
//   2. minkowski(union, ball) -- also wrong, caught from the math before
//      wasting render time: Minkowski sum distributes over union,
//      (A union B) + ball = (A+ball) union (B+ball), so it only produces
//      bigger spheres with the exact same crease, never smooths it.
//   3. A small fillet sphere positioned at the midpoint between adjacent
//      lobe centers -- had ZERO visible effect (confirmed: identical
//      triangle/facet count before and after adding it). Root cause,
//      found by directly measuring the exported mesh: the seam is a
//      NORMAL discontinuity, not a height gap -- the union boundary's
//      height is already continuous (verified by scanning real STL
//      vertices across the seam, monotonic, no dip to fill), so a bump
//      placed in "the gap" was geometrically redundant with the existing
//      union the whole time. An added bump can only fix a height gap; it
//      cannot fix a normal/tangent discontinuity.
//   4. BOSL2's round3d() -- the actually-correct tool (proper 3D
//      rounding of both convex and concave edges), but its own docs
//      warn "I cannot emphasize enough just how slow it is" -- confirmed
//      firsthand: didn't finish in 90s even at $fn=12 or a tiny radius.
//      Not usable in this project's iteration loop.
// Real, practical fix: there is no cheap true smooth-blend tool available
// here (no metaballs in this vendored BOSL2, and the correct CSG rounding
// op is too slow to render). Deepened the lobe overlap substantially
// (spacing 17mm -> 11mm) instead -- a plain union() still has a technical
// crease, but a deep enough overlap makes its intersection angle shallow
// enough that it reads as a soft rounded fold rather than a hard seam
// (confirmed by rendering multiple overlap depths and comparing). This
// keeps the exact same per-sphere geometry the face-cut math depends on,
// so center_r and every eye/mouth calc below are untouched.
module cloud_body() {
    for (l = lobes)
        translate([l[0], 0, lobe_z(l[1])]) sphere(r = l[1]);
}

module base_plate() {
    // Continuous-curvature (G2) base instead of a plain circular-arc
    // fillet (2026-08-28, see 3d-print-design skill Technique 30 for the
    // full before/after comparison this was verified against) --
    // joint_bot=0 keeps the BOTTOM edge sharp and flat on purpose (this
    // skill's own standing rule: never round the bed-contact edge, it
    // costs first-layer adhesion). joint_top gets a small real round
    // since base_h=6 doesn't leave much room to work with. base_round is
    // no longer used here (kept as the informal target for joint_sides'
    // visual footprint, not passed to rounded_prism directly -- BOSL2's
    // joint distance and a circular radius aren't the same quantity).
    footprint = rect([base_w, base_d]);
    rounded_prism(footprint, height = base_h, joint_top = 2, joint_bot = 0,
                   joint_sides = base_round + 4, k = 0.4, splinesteps = 24, anchor = BOTTOM);
}

// ---- face (all on the center lobe -- x=0, z=lobe_z(23), r=23) ----
// Every position below is computed directly from that one sphere's own
// equation (front_y = sqrt(r^2 - dx^2 - dz^2)), not measured from an
// export -- valid here specifically because it's a single untapered
// sphere, unlike the fox's hull-chain muzzle.
center_r = 23;
center_z = lobe_z(center_r);
function front_y(dx, dz) = sqrt(max(center_r * center_r - dx * dx - dz * dz, 1));

// ---- Eyes + mouth as NEGATIVE (recessed) cuts (2026-08-28). Cheeks
// removed per direct request. The recessed-cut technique on this curved
// sphere was already proven correct earlier in this file's history (see
// git log: near_pole_front_y finds the footprint's own closest-to-pole
// point -- the true hardest point for a flat tool to clear -- and `poke`
// guarantees it breaks through everywhere; verified single connected
// component, no buried cuts) -- reusing that exact math rather than
// re-deriving it.
function clamp_toward_zero(v0, h) = (v0 > h) ? v0 - h : (v0 < -h) ? v0 + h : 0;
function near_pole_front_y(dx0, dz0, hw, hh) =
    front_y(clamp_toward_zero(dx0, hw), clamp_toward_zero(dz0, hh));
poke = 0.35;   // guaranteed clearance past the true curved surface at the footprint's hardest point

// Face pass (2026-08-28): Scott's direct feedback -- "the cloud needs
// work on its face" -- the eyes were tiny (r=2.3 on a 23mm-radius lobe,
// ~10% of the face) and the mouth was a barely-visible 5x2mm crescent.
// This shop's own kawaii standard (CLAUDE.md's Chibi/Kawaii Character
// Proportions) calls for OVERSIZED eyes (40-50% of face height) -- the
// old size was nowhere close. Nearly doubled the eye radius and widened
// the spacing to match (bigger circles need more room to stay clear of
// each other), and rebuilt the mouth as a genuine curved smile using
// this skill's own proven hull-chain-of-spheres technique (Technique 17
// in .claude/skills/3d-print-design/SKILL.md) instead of a single
// stretched, barely-curved crescent -- a chain of small hulled spheres
// along a real quadratic curve reads as one continuous smiling stroke,
// not a row of dots (that skill's own documented lesson from the exact
// same mistake on a different face).
eye_r = 4.2; eye_dx = 7.2; eye_dz = 2.5; eye_cut_extrude = 3.6;
eye_y_face = near_pole_front_y(eye_dx, eye_dz, eye_r, eye_r) + poke;
eye_z = center_z + eye_dz;
module eye(mirror_x = false) {
    x = mirror_x ? -eye_dx : eye_dx;
    translate([x, eye_y_face, eye_z])
        rotate([90, 0, 0])
            linear_extrude(height = eye_cut_extrude)
                circle(r = eye_r, $fn = 40);
}

// Smile: 5 points across a real quadratic curve (center lowest, corners
// curling UP -- outer points get a HIGHER z than the center; this exact
// sign is called out in Technique 17 because getting it backwards draws
// a frown, not a smile, and it isn't obvious from the numbers alone).
mouth_dz = -7; mouth_hw = 6.5; mouth_curl = 2.8; mouth_r = 1.7;
// 9 points, not 5 -- each hull() segment is a straight chord of the true
// curve, so too few points reads as an angular "V" instead of a smooth
// "U" (confirmed by rendering the 5-point version first: a visible sharp
// kink right at the center). More points shortens each chord until the
// whole thing reads as one continuous rounded stroke.
mouth_pts_dx = [for (i = [0 : 8]) -mouth_hw + i * (2 * mouth_hw / 8)];
function mouth_dz_at(dx) = mouth_dz + mouth_curl * (dx / mouth_hw) * (dx / mouth_hw);
module mouth() {
    for (i = [0 : len(mouth_pts_dx) - 2]) {
        dx0 = mouth_pts_dx[i]; dx1 = mouth_pts_dx[i + 1];
        dz0 = mouth_dz_at(dx0); dz1 = mouth_dz_at(dx1);
        y0 = near_pole_front_y(dx0, dz0, mouth_r, mouth_r) + poke;
        y1 = near_pole_front_y(dx1, dz1, mouth_r, mouth_r) + poke;
        hull() {
            translate([dx0, y0, center_z + dz0]) sphere(r = mouth_r, $fn = 20);
            translate([dx1, y1, center_z + dz1]) sphere(r = mouth_r, $fn = 20);
        }
    }
}
// ---- pen cup: straight-down cut into the center lobe's own top ----
// Enlarged per direct request from the original 20mm-diameter cup to
// 29mm -- still well clear of the lobe's own 46mm diameter (8mm of solid
// wall remains at the widest point), just a real, noticeably bigger
// pen/pencil capacity.
pen_r = 14.5; pen_depth = 24;
module pen_cavity() {
    top_z = center_z + center_r;
    translate([0, 0, top_z - pen_depth + 2])
        cylinder(r = pen_r, h = pen_depth + 3, $fn = 48);
}

// ---- brand mark (fitted per the standing rule) ----
logo_depth = 0.7;
logo_size = 6.0;   // verified against base footprint below
module brand_mark() {
    translate([0, -base_d / 2 + 12, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

// ============================================================
// Assembled body -- single printed part
// ============================================================
module cloud_organizer() {
    difference() {
        union() {
            base_plate();
            cloud_body();
        }
        pen_cavity();
        eye(false);
        eye(true);
        mouth();
        brand_mark();
    }
}

cloud_organizer();
