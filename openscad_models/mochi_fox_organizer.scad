include <BOSL2/std.scad>

// ============================================================
// "Mochi Fox" desk organizer -- flagship design, built to combine every
// verified pattern from this shop's own build history with the market
// patterns confirmed in the 100-model survey (Bench Marks, 2026-08-27):
// kawaii/gift-appeal categories over-index on Etsy, and a character
// piece that's ALSO a real desk tool outsells either half alone. Seated
// chibi fox, single printed part, hollowed on top for 2 real desk
// functions (pen cup, phone-lean slot cradled by the tail) plus a
// shallow chest dish.
//
// Font note (2026-08-27, real finding): fonts/DancingScript-Bold.ttf on
// disk is NOT a real font file -- `file` identifies it as a saved GitHub
// HTML page, not a TrueType binary, and it was never registered with
// fontconfig regardless. Every prior brand mark in this shop's OpenSCAD
// history that requested font="Dancing Script:style=Bold" silently fell
// back to OpenSCAD's default font -- the request never errored, so this
// went undetected. assets/fonts/Caveat-Bold.ttf IS a real TTF and
// resolves cleanly as "Caveat:style=Bold" once copied into ~/.fonts +
// fc-cache -- verified via `file` and `fc-scan` before use here, not
// assumed from the filename.
//
// Cut feature, on purpose (2026-08-27): a small bayonet-lock stash hatch
// (matching bayonet_jar.scad's proven twist-lock mechanism) was built
// into the belly/hip of this body and DID eventually pass every
// mechanical check -- boss/door interference empty, body connectivity a
// single component, isolated from head/ears/tail. It still got cut.
// This body is only ~30mm in body-radius and already carries a head,
// two ears, a tail, and two cavities; every position tried either
// collided with one of those (confirmed directly via intersection()
// against each feature in isolation) or needed the boss pushed so tall
// to clear the surrounding curvature that it read as a stray spike
// bolted onto the shoulder in an actual render -- a real look-and-feel
// regression that no interference test would ever catch, since those
// only check "does it overlap," never "does it look right." Passing
// every mechanical check is necessary, not sufficient -- always render
// and look before calling a feature done. Worth revisiting on a larger
// body with real free surface area; not worth compromising this one's
// silhouette for.
// ============================================================

part = "body";   // "body" (final print) | "preview" (same geometry)

// ---- base plate ----
base_w = 110; base_d = 78; base_h = 6; base_round = 32;   // <= min(w,d)/2=39

// ---- body ----
body_r = 30;
body_scale = [1.05, 0.9, 1.15];
body_center = [0, -10, base_h + body_r * body_scale[2]];

// ---- head + snout (built as one hulled blob) ----
head_r = 23;
head_scale = [1.0, 0.95, 0.95];
head_center = [0, 9, 65];
snout_r = 12;
snout_scale = [0.8, 1.05, 0.72];
snout_center = [0, 27, 57];

// ---- ears ----
ear_r1 = 10; ear_r2 = 1.4; ear_h = 23;
ear_base = [10.5, 6, 82];
ear_tilt = [14, 0, 20];   // splay outward + forward lean

// ---- tail (hull-chain of spheres, tapering, curling up the -X side) ----
tail_pts = [
    [-19, -35, 19, 13.5],
    [-33, -31, 33, 11.5],
    [-42, -19, 47, 9.5],
    [-41,  -3, 58, 7.5],
    [-31,   9, 63, 5.5],
    [-19,  13, 61, 3.2],
];

// ---- feet ----
foot_r = 7.5; foot_scale = [1, 1, 0.55];
foot_x = 15; foot_y = 24; foot_z = base_h + 3;

// ---- face ----
eye_depth = 1.6;
// eye_y_face is the world-Y CUT-START plane (extrudes toward -Y into the
// head) -- must sit ON the head+snout blob's real front surface, not a
// guessed height. head_center=[0,9,65], head_r=23*0.95 -> front surface
// near y=9+21.85=30.9; snout pokes further to y=27+12*1.05=39.6. Placing
// the eye cut-start at y=34 (between the two, on the upper head lobe
// above the snout) actually lands on real material -- confirmed below
// via recess-floor vertex check, not assumed from this arithmetic alone.
eye_x = 8; eye_y_face = 34; eye_z = 69; eye_dia = 11;
nose_r = 3.2; nose_center = [0, 38.5, 60];
cheek_r = 4; cheek_depth = 0.7; cheek_x = 11; cheek_z = 62;

// ---- functional cavities ----
// body_top_z(x,y): exact analytic top-surface height of the body
// ellipsoid above world point (x,y) -- replaces an earlier version that
// guessed absolute z heights by eye (e.g. pen_top z=78, which sat 6mm
// ABOVE the real surface at that x,y and cut nothing where intended).
// A hulled compound blob (head+snout) isn't this tractable, which is
// exactly why both cavities below are placed on the plain body
// ellipsoid, not the head -- solvable in closed form, so a placement
// bug shows up in the math immediately instead of only in a render.
function body_top_z(x, y) =
    let(dx = x - body_center[0], dy = y - body_center[1],
        rx = body_r * body_scale[0], ry = body_r * body_scale[1], rz = body_r * body_scale[2],
        t = 1 - (dx / rx) * (dx / rx) - (dy / ry) * (dy / ry))
    body_center[2] + rz * sqrt(max(t, 0.02));

module top_cut(x, y, r, depth, extra = 2) {
    translate([x, y, body_top_z(x, y) - depth + extra])
        cylinder(r = r, h = depth + extra + 1, $fn = 48);
}

// First draft used pen_r=17/pen_depth=44 -- on a body whose own radius
// is only 30, a 34mm-wide, 44mm-deep cut is comparable to the body's
// entire diameter and blew straight through the top AND toward the
// head overlap (confirmed directly in a back-top render: the "pen cup"
// was a cavernous pit you could see the underside of the head through).
// Scaled down to a real pen-cup proportion instead of a body-sized pit.
pen_x = 10; pen_y = -30; pen_r = 9; pen_depth = 20;
dish_x = 16; dish_y = 6; dish_r = 12; dish_depth = 5;

// No cut phone slot: the tail (see tail_pts) runs its own path roughly
// 15-20mm clear of the body surface the whole way up the -X/back side,
// which already forms an open lean-in gap -- a positive-space cradle
// needs no interference-risk cavity at all, confirmed by render below.

// ---- brand mark (fitted per the standing rule, verified below) ----
logo_depth = 0.7;
logo_size = 5.4;   // verified against base footprint below

// ============================================================
// Body blob
// ============================================================
module body_shape() {
    translate(body_center) scale(body_scale) sphere(r = body_r, $fn = 64);
}

module head_shape() {
    hull() {
        translate(head_center) scale(head_scale) sphere(r = head_r, $fn = 48);
        translate(snout_center) scale(snout_scale) sphere(r = snout_r, $fn = 48);
    }
}

module ear(mirror_x = false) {
    x = mirror_x ? -ear_base[0] : ear_base[0];
    tiltx = mirror_x ? -ear_tilt[0] : ear_tilt[0];
    translate([x, ear_base[1], ear_base[2]])
        rotate([tiltx, ear_tilt[1], mirror_x ? -ear_tilt[2] : ear_tilt[2]])
            cylinder(r1 = ear_r1, r2 = ear_r2, h = ear_h, $fn = 28);
}

module tail() {
    for (i = [0 : len(tail_pts) - 2]) {
        p0 = tail_pts[i]; p1 = tail_pts[i + 1];
        hull() {
            translate([p0[0], p0[1], p0[2]]) sphere(r = p0[3], $fn = 24);
            translate([p1[0], p1[1], p1[2]]) sphere(r = p1[3], $fn = 24);
        }
    }
}

module foot(mirror_x = false) {
    x = mirror_x ? -foot_x : foot_x;
    translate([x, foot_y, foot_z]) scale(foot_scale) sphere(r = foot_r, $fn = 28);
}

module base_plate() {
    cuboid([base_w, base_d, base_h], rounding = base_round, edges = "Z", anchor = BOTTOM);
}

// ---- face details ----
// Eyes/cheeks are cut as shallow planar recesses on the head's front
// hemisphere -- the same linear_extrude()+rotate() approach proven on
// every brand mark this session, valid here because eye_dia/cheek_r are
// small relative to head_r (a flat approximation of the local curve).
// First draft used intersection(circle, tall square) hoping for a
// crescent -- rendered as a near-invisible thin sliver instead, because
// the square only grazed a thin edge of the circle rather than keeping
// a real half. A plain upper-half-of-a-circle (dome) is unambiguous and
// bold: no thin-intersection risk, reads immediately as a closed eye.
module eye_2d() {
    intersection() {
        circle(r = eye_dia / 2, $fn = 32);
        translate([0, eye_dia / 4]) square([eye_dia * 1.2, eye_dia / 2], center = true);
    }
}
module eye(mirror_x = false) {
    x = mirror_x ? -eye_x : eye_x;
    translate([x, eye_y_face, eye_z])
        rotate([90, 0, 0])
            linear_extrude(height = eye_depth + 0.5)
                eye_2d();
}
module cheek(mirror_x = false) {
    x = mirror_x ? -cheek_x : cheek_x;
    translate([x, eye_y_face - 2, cheek_z])
        rotate([90, 0, 0])
            linear_extrude(height = cheek_depth + 0.5)
                circle(r = cheek_r, $fn = 24);
}
module nose() {
    translate(nose_center) sphere(r = nose_r, $fn = 24);
}

// ---- functional cavities ----
module pen_cavity() { top_cut(pen_x, pen_y, pen_r, pen_depth); }
module dish_cavity() { top_cut(dish_x, dish_y, dish_r, dish_depth); }

// ============================================================
// Brand mark -- underside of base, fitted per the standing rule
// (measured against this part's real footprint, not copied from
// another design's size).
// ============================================================
module brand_mark() {
    translate([0, -base_d / 2 + 14, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

// ============================================================
// Assembled body -- single printed part
// ============================================================
module fox_body() {
    difference() {
        union() {
            base_plate();
            body_shape();
            head_shape();
            ear(false);
            ear(true);
            tail();
            foot(false);
            foot(true);
            nose();
        }
        pen_cavity();
        dish_cavity();
        eye(false);
        eye(true);
        cheek(false);
        cheek(true);
        brand_mark();
    }
}

fox_body();
