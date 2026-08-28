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

// Reworked after comparing against a real, popular kawaii pen holder
// (Puff Puff Pastries' "Cat Pen Holder," MyMiniFactory -- fetched and
// viewed directly, not worked from memory) that reads instantly as a
// face from across a room: every element there is BOLD and FILLED
// (solid black eye, solid pink blush circles, thick brow/mouth lines),
// tightly clustered, and sized large relative to the surface it sits
// on. The first draft here used a thin dome-shaped crescent for the
// eyes -- geometrically a true semicircle, not a sliver, but a thin
// arc riding a curved surface recedes out of view from most angles
// (only the flat base of the dome stays visible face-on), which is
// exactly why it read as scattered thin marks rather than a face. Eyes
// are now flattened FILLED OVALS instead -- a solid shape has a real
// silhouette from any angle, the same reason the cheeks (already solid
// circles) were the one part of v1's face that actually read fine.
// Also added a mouth (missing before) and moved everything closer
// together into one compact cluster instead of spreading toward the
// lobe's edges.
// ---- CRITICAL FIX #2 (found by re-deriving the direction of the bug after
// fix #1 made the cheek WORSE, not better -- re-verified against the
// exported mesh again rather than trusting the first correction by eye):
// a cut's extrusion cap is FLAT, the sphere surface it lands on is CURVED,
// and front_y is MAXIMIZED at the pole (dx=dz=0) and falls off outward. The
// hardest point for a flat tool to clear is therefore the point in the
// footprint CLOSEST to the pole (highest local surface bulge) -- NOT the
// farthest corner. Fix #1 used the farthest corner, which pushed the tool
// even deeper inside the solid and made the cheek's cut fully buried
// (confirmed: stl_components.py reported a new sealed fragment whose bbox
// exactly matched the cheek tool). Corrected: `near_pole_front_y` finds the
// footprint's own closest-to-pole point (the true hardest constraint) and
// `poke` is added on top of THAT, guaranteeing the tool clears the surface
// everywhere in its footprint, with more clearance (deeper cut) toward the
// far side where the surface naturally recedes -- expected and fine for a
// small cosmetic dimple, not a bug. Also pulled every mark closer to the
// pole (bigger offsets = more curvature spread = harder to cut cleanly with
// a flat tool) -- a tighter, more centered cluster both reads better as a
// face (per the reference image) and keeps this math well-behaved.
function clamp_toward_zero(v0, h) = (v0 > h) ? v0 - h : (v0 < -h) ? v0 + h : 0;
function near_pole_front_y(dx0, dz0, hw, hh) =
    front_y(clamp_toward_zero(dx0, hw), clamp_toward_zero(dz0, hh));
poke = 0.35;   // guaranteed clearance past the true curved surface at the footprint's hardest point

// Composition fix #2 (found by comparing against a second, more relevant
// real reference: an actual rainbow-painted wood cloud pen holder, not just
// the cat-pen-holder used for the earlier "make marks bold" fix). That real
// competing cloud product's face is much smaller and lower-proportioned
// than what was here -- two small dot eyes, two small blush dots, a simple
// smile, and NO nose at all. Its real "top design" quality comes almost
// entirely from a rainbow paint job on a deliberately simple shape, not
// from a bigger/busier face. Shrunk every mark down and dropped the nose to
// match that real minimal proportion -- still non-overlapping (verified
// same way as fix #1: z-ranges kept disjoint between eye/cheek/mouth).
eye_dx = 4; eye_dz = 2; eye_w = 4.2; eye_h = 2.6; eye_cut_extrude = 3.0;
eye_y_face = near_pole_front_y(eye_dx, eye_dz, eye_w / 2, eye_h / 2) + poke;
eye_z = center_z + eye_dz;

cheek_dx = 8; cheek_dz = -3.5; cheek_r = 2.4; cheek_cut_extrude = 3.0;
cheek_y_face = near_pole_front_y(cheek_dx, cheek_dz, cheek_r, cheek_r) + poke;
cheek_z = center_z + cheek_dz;

mouth_dz = -7; mouth_w = 5; mouth_h = 2; mouth_cut_extrude = 2.2;
// mouth's own footprint only extends AWAY from the pole in z (a crescent
// hanging below its reference line), so the reference point itself (not a
// clamped corner) is already the closest-to-pole point -- no clamp needed.
mouth_y_face = front_y(0, mouth_dz) + poke;
mouth_z = center_z + mouth_dz;

module eye(mirror_x = false) {
    x = mirror_x ? -eye_dx : eye_dx;
    translate([x, eye_y_face, eye_z])
        rotate([90, 0, 0])
            linear_extrude(height = eye_cut_extrude)
                scale([eye_w / eye_h, 1])
                    circle(r = eye_h / 2, $fn = 40);
}
module cheek(mirror_x = false) {
    x = mirror_x ? -cheek_dx : cheek_dx;
    translate([x, cheek_y_face, cheek_z])
        rotate([90, 0, 0])
            linear_extrude(height = cheek_cut_extrude)
                circle(r = cheek_r, $fn = 32);
}
// Same flattened-oval technique as the eyes, kept slightly thinner and
// a touch curved (bottom-half of an ellipse) for a soft closed smile.
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
        }
        pen_cavity();
        eye(false);
        eye(true);
        cheek(false);
        cheek(true);
        mouth();
        brand_mark();
    }
}

cloud_organizer();
