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
    [-34, 13],
    [-17, 19],
    [  0, 23],   // center -- carries the face and the pen cup
    [ 17, 19],
    [ 34, 13],
];

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

// ---- MIXED FINISH (2026-08-28): eyes + mouth NEGATIVE (recessed), cheeks
// still RAISED bumps. Per direct request: drop the round raised "eyebrow"-
// looking eye dots and cut real eyes + a real mouth into the surface so
// they read with actual depth/shadow instead of a flat sticker-like bump.
// The recessed-cut technique on this curved sphere was already proven
// correct earlier in this file's history (see git log: near_pole_front_y
// finds the footprint's own closest-to-pole point -- the true hardest
// point for a flat tool to clear -- and `poke` guarantees it breaks
// through everywhere; verified single connected component, no buried
// cuts) -- reusing that exact math rather than re-deriving it. Cheeks stay
// as raised bumps (bump_y / union) since that half was never the problem.
function bump_y(dx, dz, r, embed_frac) = front_y(dx, dz) - r * embed_frac;
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

cheek_r = 3.3; cheek_dx = 9; cheek_dz = -3;
module cheek(mirror_x = false) {
    x = mirror_x ? -cheek_dx : cheek_dx;
    translate([x, bump_y(cheek_dx, cheek_dz, cheek_r, 0.65), center_z + cheek_dz])
        sphere(r = cheek_r);
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
// Same lesson the fox's first pen-cup draft learned the hard way: size
// it to the LOBE it's cut from, not to a generic "big pen cup" number.
// center_r=23 -> a 20mm-diameter, 22mm-deep cup is a real, comfortably
// proportioned cavity, nowhere near the lobe's own 46mm diameter.
pen_r = 10; pen_depth = 22;
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
            cheek(false);
            cheek(true);
        }
        pen_cavity();
        eye(false);
        eye(true);
        mouth();
        brand_mark();
    }
}

cloud_organizer();
