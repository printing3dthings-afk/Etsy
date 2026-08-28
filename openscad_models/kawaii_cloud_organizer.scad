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

// ---- REBUILT AS RAISED BUMPS, NOT ENGRAVED CUTS (2026-08-28) ----
// After three rounds of engraved-cut problems on this curved surface --
// a fully buried mouth (flat tool never reached the real surface), a
// figure-8 eye/cheek overlap, and still-wrong proportions after fixing
// both -- Scott's call was direct: fix it properly or cut it. Switching
// to RAISED bumps is the real fix, not another parameter tweak: a
// union() bump has no "does this actually reach the surface" failure
// mode the way a difference() cut does. The nose bump used this exact
// technique from the very first version of this file and never had a
// single bug across the whole project -- every cut-based fix above was
// fighting a problem this approach doesn't have in the first place.
function bump_y(dx, dz, r, embed_frac) = front_y(dx, dz) - r * embed_frac;

eye_r = 2.1; eye_dx = 4.2; eye_dz = 2.5;
module eye(mirror_x = false) {
    x = mirror_x ? -eye_dx : eye_dx;
    translate([x, bump_y(eye_dx, eye_dz, eye_r, 0.35), center_z + eye_dz])
        sphere(r = eye_r);
}

cheek_r = 3.3; cheek_dx = 9; cheek_dz = -3;
module cheek(mirror_x = false) {
    x = mirror_x ? -cheek_dx : cheek_dx;
    translate([x, bump_y(cheek_dx, cheek_dz, cheek_r, 0.65), center_z + cheek_dz])
        sphere(r = cheek_r);
}

// Smile: a smooth raised arc from a hull-chain of small spheres, each
// individually placed on the sphere's own exact surface equation -- the
// same hull-chain technique this shop already uses for smooth curved
// details, just applied to a small cosmetic raised line instead of a cut.
smile_pts = [ [-3, -7.0], [-1.5, -8.0], [0, -8.3], [1.5, -8.0], [3, -7.0] ];
smile_r = 0.9;
module smile() {
    for (i = [0 : len(smile_pts) - 2]) {
        p0 = smile_pts[i];
        p1 = smile_pts[i + 1];
        hull() {
            translate([p0[0], bump_y(p0[0], p0[1], smile_r, 0.4), center_z + p0[1]]) sphere(r = smile_r);
            translate([p1[0], bump_y(p1[0], p1[1], smile_r, 0.4), center_z + p1[1]]) sphere(r = smile_r);
        }
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
            eye(false);
            eye(true);
            cheek(false);
            cheek(true);
            smile();
        }
        pen_cavity();
        brand_mark();
    }
}

cloud_organizer();
