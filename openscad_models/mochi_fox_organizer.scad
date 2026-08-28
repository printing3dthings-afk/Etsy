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

// ---- head + snout ----
// v1 built this as hull(2 spheres) -- a big round skull ball with a
// small round snout ball stuck on the front. Against a real reference
// photo (fetched and viewed directly, not worked from memory -- a red
// fox sitting portrait) that reads as generic-animal, not fox: a real
// fox head is a WEDGE that tapers continuously from a wide cheek/ruff
// area down to a narrow, distinctly elongated muzzle, not two blobs.
// v2 uses the same hull-CHAIN technique already proven on the tail
// (consecutive hull() pairs of shrinking spheres) run along the
// head-to-nose axis instead -- a continuous taper, still fully smooth
// (hull of spheres has no seams), much closer to the real silhouette.
head_pts = [
    [0,  2, 74, 20],   // back of skull, nestles into the body's front-top
    [0, 14, 76, 19],   // crown
    [0, 25, 71, 15.5], // cheek/ruff -- the widest part of the face
    [0, 34, 62,  9.5], // muzzle base, narrowing
    [0, 41, 57,  6],   // muzzle mid
    [0, 46, 54,  3.6], // nose base (the nose bump sits just past this)
];

// ---- ears ----
// v1: a single cylinder(r1,r2) cone -- correct silhouette direction but
// thin/spindly, and splayed wide (base x=+-10.5) further apart than a
// real fox's, which sit close together atop the crown. v2: hull() of a
// wide base sphere + small rounded tip sphere -- a softer, fuller taper
// (no perfectly sharp point, reads cuter and less spindly), moved onto
// the actual crown point (head_pts[1]) and closer together in X.
ear_base_r = 8.5; ear_tip_r = 2.2; ear_len = 21;
ear_root = [8, 13, 79];
ear_tilt = [12, 0, 16];   // splay outward + forward lean

// ---- tail (hull-chain of spheres, tapering, curling up the -X side) ----
// v1 tapered smoothly all the way to a fine point -- a real fox tail is
// bushiest at the TIP, not the root (a rounded "poof"), confirmed on the
// same reference photo. Reworked the last two points to widen slightly
// again instead of continuing to shrink.
tail_pts = [
    [-19, -35, 19, 13.5],
    [-33, -31, 33, 11.5],
    [-42, -19, 47, 9.5],
    [-41,  -3, 58, 8.0],
    [-32,   9, 64, 7.5],
    [-20,  15, 65, 7.0],   // poof: widens slightly instead of tapering to a point
];

// ---- feet ----
foot_r = 7.5; foot_scale = [1, 1, 0.55];
foot_x = 15; foot_y = 24; foot_z = base_h + 3;

// ---- face ----
// Two wrong guesses before this one, both from estimating the head
// hull-chain's real surface by eye instead of measuring it. y_face=33
// broke through the SIDE (a jagged tear in a real render). y_face=24
// (assuming the surface near head_pts[2] sits close to that control
// point's own y=25) was actually WORSE: intersection(head_shape(),
// eye()) came back as a single component with the tool's FULL bounding
// box -- meaning the cut was entirely BURIED inside the solid, never
// reaching open air at all, so it carved a hidden internal bubble
// instead of a visible recess (which is exactly why the exported STL
// showed a same-shaped disconnected component: the bubble's own inner
// shell, topologically separate from the outer one).
//
// Root cause: a hull() between two spheres offset in BOTH y and z (the
// head chain drops in z while advancing in y) bulges its "roof" surface
// (the high-z side) much further forward in y than either control
// point's own y suggests -- confirmed by directly querying the real
// exported mesh for the actual front-surface y at the target (x,z)
// rather than estimating from the sphere centers. Real measured values:
// (x=9,z=73) -> y=37.8; (x=13,z=62) -> y=30.2. Every position below
// uses a 2mm margin inside those measured numbers, not a guess.
eye_depth = 1.8;
eye_x = 9; eye_y_face = 36; eye_z = 73; eye_dia = 13;
nose_r = 3.6; nose_center = [0, 49, 53];
cheek_r = 4.2; cheek_depth = 0.8; cheek_x = 13; cheek_y_face = 28.5; cheek_z = 62;

// ---- v3 realism details (2026-08-28) ----
// Applying the v2 lesson before writing a single one of these: every
// CUT below was placed only after exporting the relevant shape alone
// and measuring its real front-surface y at the target (x,z) window
// (same technique as the eye fix), not estimated from head_pts. The
// ADDs (brow ridges, chest patch, phone-stand lip) skip that step on
// purpose -- an add can't create a hidden-buried-void defect the way a
// cut can, so the risk profile is different and a visual check after
// rendering is sufficient.
//
// Whisker dimples: measured real surface at (x=4-7,z=56-60)->y=45.06
// and (x=3-6,z=52-56)->y=47.37. Three per side, stepping down the
// muzzle, each cut-start 1.5mm inside its own measured surface.
whisker_dia = 2.2; whisker_depth = 1.0;
whisker_pts = [   // [x, y_face, z]
    [5.5, 43.5, 58],
    [6.3, 45.8, 55],
    [6.6, 47.0, 52],
];

// Mouth: measured real surface at (x=-1..1,z=48-51)->y=47.7. A small
// downward-arc groove (same dome-shape technique as eye_2d, just
// smaller and thinner) sitting just under the nose base.
mouth_y_face = 46.5; mouth_z = 48; mouth_dia = 7; mouth_depth = 1.0;

// Brow ridges: small raised arcs just above each eye -- an ADD, so
// placed by eye/embed-depth rather than measured (see note above).
brow_x = 9; brow_y = 37.5; brow_z = 80.5;

// Chest patch: a raised, gently domed patch on the lower-front body,
// suggesting the lighter belly-fur tuft real foxes have. An ADD, deeply
// embedded (only proud_frac of its own radius pokes out) -- generous
// embed depth applied from the start this time instead of discovered
// the hard way (see the stash-hatch and dish-cavity postmortems above).
chest_center = [0, 8, 48]; chest_scale = [1.3, 0.6, 1.0]; chest_r = 12;

// Phone-stand lip: a small raised nub at the base of the tail/body gap
// (near tail_pts[0], the tail's own thickest/lowest point) so a leaned
// phone has a real physical stop instead of just an open gap -- makes
// the stand function both more real and more visible.
lip_center = [-24, -28, 10]; lip_r = 5; lip_scale = [1, 1, 0.6];

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

// Cut, on purpose (2026-08-27, v2): the chest dish cut right at the
// seam where head_shape() and body_shape() overlap and union together
// -- isolated by disabling every other cut one at a time until only
// this one reproduced a large jagged tear visible in a real render.
// The head/body union boundary there isn't a simple sphere the way
// body_top_z() assumes, so a "safe" (x,y) for this cut isn't
// analytically tractable the same way pen_cavity's position is. Same
// call as the stash hatch: not worth chasing a precise fix for a
// secondary feature when dropping it removes the defect outright.

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
// Smoothness bump (2026-08-27, v2): v1 used $fn=24-64 across the board
// and the rendered result read as visibly faceted rather than smooth --
// a real, fair complaint, not just a rendering-angle issue. Every
// sphere/cylinder below now uses $fn=96 for the large character forms
// (body/head/ears) and 48-64 for smaller detail, instead of the mixed
// 24-64 range v1 used. Render time cost is real (a full --render goes
// from ~25s to ~60-90s) but this is the flagship piece -- worth it here.
$fn = 96;

module body_shape() {
    translate(body_center) scale(body_scale) sphere(r = body_r);
}

// Hull-CHAIN (same technique as tail() below) instead of v1's hull of
// just 2 spheres -- a continuous multi-point taper reads as an actual
// wedge-shaped fox muzzle instead of "ball with a smaller ball stuck on
// the front." See head_pts above for the real-photo-informed profile.
module head_shape() {
    for (i = [0 : len(head_pts) - 2]) {
        p0 = head_pts[i]; p1 = head_pts[i + 1];
        hull() {
            translate([p0[0], p0[1], p0[2]]) sphere(r = p0[3]);
            translate([p1[0], p1[1], p1[2]]) sphere(r = p1[3]);
        }
    }
}

// hull() of a wide-base sphere + small rounded-tip sphere -- a soft
// capsule taper, not a mathematically sharp cone (v1's cylinder(r1,r2)
// read thin/spindly). Rounded tip also sidesteps any single-point-apex
// faceting artifact a cone's tip can show at lower $fn.
module ear(mirror_x = false) {
    x = mirror_x ? -ear_root[0] : ear_root[0];
    tiltx = mirror_x ? -ear_tilt[0] : ear_tilt[0];
    translate([x, ear_root[1], ear_root[2]])
        rotate([tiltx, ear_tilt[1], mirror_x ? -ear_tilt[2] : ear_tilt[2]])
            hull() {
                sphere(r = ear_base_r);
                translate([0, 0, ear_len]) sphere(r = ear_tip_r);
            }
}

module tail() {
    for (i = [0 : len(tail_pts) - 2]) {
        p0 = tail_pts[i]; p1 = tail_pts[i + 1];
        hull() {
            translate([p0[0], p0[1], p0[2]]) sphere(r = p0[3]);
            translate([p1[0], p1[1], p1[2]]) sphere(r = p1[3]);
        }
    }
}

module foot(mirror_x = false) {
    x = mirror_x ? -foot_x : foot_x;
    translate([x, foot_y, foot_z]) scale(foot_scale) sphere(r = foot_r);
}

module base_plate() {
    cuboid([base_w, base_d, base_h], rounding = base_round, edges = "Z", anchor = BOTTOM);
}

// ---- face details ----
// Eyes/cheeks are cut as shallow planar recesses on the head's front
// hemisphere -- the same linear_extrude()+rotate() approach proven on
// every brand mark this session, valid here because eye_dia/cheek_r are
// small relative to the head chain's local sphere radius (a flat
// approximation of the local curve).
// First draft used intersection(circle, tall square) hoping for a
// crescent -- rendered as a near-invisible thin sliver instead, because
// the square only grazed a thin edge of the circle rather than keeping
// a real half. A plain upper-half-of-a-circle (dome) is unambiguous and
// bold: no thin-intersection risk, reads immediately as a closed eye.
module eye_2d() {
    intersection() {
        circle(r = eye_dia / 2, $fn = 64);
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
    translate([x, cheek_y_face, cheek_z])
        rotate([90, 0, 0])
            linear_extrude(height = cheek_depth + 0.5)
                circle(r = cheek_r, $fn = 48);
}
module nose() {
    translate(nose_center) sphere(r = nose_r);
}

// Small pinprick recesses, plain full circles (no dome-clipping needed
// at this size) -- see whisker_pts above for the measured positions.
module whisker(pt, mirror_x = false) {
    x = mirror_x ? -pt[0] : pt[0];
    translate([x, pt[1], pt[2]])
        rotate([90, 0, 0])
            linear_extrude(height = whisker_depth + 0.5)
                circle(r = whisker_dia / 2, $fn = 16);
}
module whiskers(mirror_x = false) {
    for (p = whisker_pts) whisker(p, mirror_x);
}

// Same dome-clip technique as eye_2d() -- upper half only, so it stays
// within the measured z>=48 material band instead of risking the empty
// space below the snout's underside (found empty during measurement).
module mouth_2d() {
    intersection() {
        circle(r = mouth_dia / 2, $fn = 32);
        translate([0, mouth_dia / 4]) square([mouth_dia * 1.2, mouth_dia / 2], center = true);
    }
}
module mouth() {
    translate([0, mouth_y_face, mouth_z])
        rotate([90, 0, 0])
            linear_extrude(height = mouth_depth + 0.5)
                mouth_2d();
}

// Brow ridges, chest patch, phone-stand lip -- all ADDs, not cuts, so
// none of them can create a hidden-buried-void defect the way a cut
// can; embed depth just needs to be generous enough to fuse, checked
// visually after render rather than pre-measured (see v3 note above).
module brow(mirror_x = false) {
    x = mirror_x ? -brow_x : brow_x;
    translate([x, brow_y, brow_z])
        scale([1.7, 1, 0.55])
            sphere(r = 3.4, $fn = 32);
}
module chest_patch() {
    translate(chest_center) scale(chest_scale) sphere(r = chest_r, $fn = 64);
}
module phone_lip() {
    translate(lip_center) scale(lip_scale) sphere(r = lip_r, $fn = 48);
}

// ---- functional cavities ----
module pen_cavity() { top_cut(pen_x, pen_y, pen_r, pen_depth); }

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
            brow(false);
            brow(true);
            chest_patch();
            phone_lip();
        }
        pen_cavity();
        eye(false);
        eye(true);
        cheek(false);
        cheek(true);
        whiskers(false);
        whiskers(true);
        mouth();
        brand_mark();
    }
}

fox_body();
