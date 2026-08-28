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
    cuboid([base_w, base_d, base_h], rounding = base_round, edges = "Z", anchor = BOTTOM);
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

eye_r = 2.3; eye_dx = 4.2; eye_dz = 2.5; eye_cut_extrude = 3.2;
eye_y_face = near_pole_front_y(eye_dx, eye_dz, eye_r, eye_r) + poke;
eye_z = center_z + eye_dz;
module eye(mirror_x = false) {
    x = mirror_x ? -eye_dx : eye_dx;
    translate([x, eye_y_face, eye_z])
        rotate([90, 0, 0])
            linear_extrude(height = eye_cut_extrude)
                circle(r = eye_r, $fn = 40);
}

mouth_dz = -7; mouth_w = 5; mouth_h = 2; mouth_cut_extrude = 2.5;
// mouth's own footprint only extends AWAY from the pole in z (a crescent
// hanging below its reference line), so the reference point itself (not a
// clamped corner) is already the closest-to-pole point -- no clamp needed.
mouth_y_face = front_y(0, mouth_dz) + poke;
mouth_z = center_z + mouth_dz;
module mouth() {
    translate([0, mouth_y_face, mouth_z])
        rotate([90, 0, 0])
            linear_extrude(height = mouth_cut_extrude)
                intersection() {
                    scale([mouth_w / mouth_h, 1]) circle(r = mouth_h / 2, $fn = 40);
                    translate([0, -mouth_h / 4]) square([mouth_w * 1.2, mouth_h / 2], center = true);
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
