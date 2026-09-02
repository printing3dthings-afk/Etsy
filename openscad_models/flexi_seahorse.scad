include <BOSL2/std.scad>

/*
  Flexi seahorse -- print-in-place articulated tail, no supports, no assembly.

  JOINTS ARE CARVED, NOT BUILT. The whole animal is sculpted as ONE continuous
  solid and each joint is a ring-shaped cutter subtracted from it. This is how
  the good flexi models are made and it is why they look sculpted rather than
  assembled: the skin is unbroken and the joint reads as a carved line, not a
  step between two beads. A first version of this model chained pre-made beads
  instead and every segment showed as a separate lump with the neck bare
  between them.

      cutter = cup(R + clear, phi_out) - cup(R, phi_in),  cup = sphere + fwd cone

  The sphere part gives a gap that is constant under rotation. The two cones
  differ by `delta`, so the gap grows linearly outward -- and that angular
  difference IS the swing, directly. Give both cones the same angle and the
  joint binds at about 4 degrees no matter how much clearance it has.

  Retention comes from the collar wrapping past the ball's equator: the throat
  is (R + clear) * sin(phi_out), so phi_out must stay under
  asin(R / (R + clear)) = 67 degrees or the ball is not captured at all.

  Verified on the real model: retention 0.33mm, swing 15 deg per joint.

  ORIENTATION IS STRUCTURAL. Printed flat, the bending stress at every joint
  runs along the layer plane, the strong direction. Standing it up would load
  the layer bonds in tension -- 4-5x weaker -- and the tail would snap at the
  first bend. So the tail curls in the print plane, which happens to be the
  plane a real seahorse curls in.
*/

part = "seahorse";   // seahorse | joint_test
pose = "flat";       // flat = as printed | curled = preview only
// Iterate at low $fn and finalise high -- the topology under test does not
// depend on facet count, and every boolean here is paid for per facet.
$fn  = 36;

// ── carved joint ────────────────────────────────────────────────────────
R        = 2.9;      // ball radius
clear    = 0.25;     // per side; 0.2-0.3 is the reliable band at a 0.4 nozzle
phi_in   = 37;       // cone bounding the ball's own side
delta    = 18;       // angular gap -> swing, degrees per joint (measured: swing == delta)
phi_out  = phi_in + delta;
// A protruding ring has only a narrow window between joints where neither
// carve can reach it. Joint i's cone clears a tubercle of outer radius 6.3 only
// past d = 6.3/tan(phi_out) = 4.4mm, and joint i+1's socket sphere reaches
// 3.15mm back from its centre. So the window is (4.4, pitch - 3.15) and the
// pitch has to be comfortably over 7.6mm for it to exist at all.
//
// This was not obvious and cost two builds. At pitch 7.5 there was no window
// and every tail tubercle came off as a floating sliver -- 20 components where
// 12 was right, and the slivers were 0.1-1.1mm, far too small to see in a
// render. At pitch 9 the window was 0.4mm wide and the ring's leading edge
// still caught. Pitch 10 gives a 2.4mm window, which is room to work in.
pitch    = 10.0;
n_joint  = 9;
ring_d   = 5.5;      // where a tail ring sits after its joint -- inside that window
curl     = (pose == "curled") ? -15 : 0;

z_squash = 0.80;     // body is deeper front-to-back than it is thick
z_flat   = R + clear + 0.8;
bed      = -z_flat;
sink     = 0.6;      // thin features drop below the trim so they get a real flat
function bed_z(r) = bed + r * z_squash - sink;

// The cone only has to run far enough to leave the tail -- it clears a 5.5mm
// radius by 3.9mm along. Running it to 70 (and then clipping it back with an
// intersection) made an unbounded thin conical sheet per joint and eleven extra
// booleans, and CGAL would not finish the model at all.
cone_len = 11;
module cup(rho, a) {
    union() {
        sphere(r = rho);
        rotate([0, 90, 0]) cylinder(h = cone_len, r1 = 0, r2 = cone_len * tan(a));
    }
}
module joint_cutter() { difference() { cup(R + clear, phi_out); cup(R, phi_in); } }

// ── the animal, as one path ─────────────────────────────────────────────
// Forward is -X. A seahorse reads by three things: a head set near a right
// angle to the body, a deep forward chest, and a tail curling the way the head
// faces.
snout_pts = [[-33.0, 55.0, 2.5], [-28.5, 55.8, 2.5], [-23.0, 56.8, 2.9],
             [-19.0, 57.6, 3.5]];
head_pts  = [[-19.0, 57.6, 3.5], [-16.0, 58.3, 5.4], [-12.6, 57.2, 6.6],
             [-9.8, 53.6, 6.3]];
trunk_pts = [[-9.8, 53.6, 6.3], [-8.0, 50.0, 6.3], [-5.0, 42.0, 7.4],
             [-1.0, 32.0, 8.6], [2.0, 21.0, 8.9], [3.0, 10.0, 7.9],
             [2.3, 1.5, 6.6], [2.0, -1.5, 5.9]];

tail_r0 = 5.55;      // at the first joint
tail_r1 = 4.80;      // at the last -- never below R + clear + 1.6 of collar
function tail_y(i) = -1.5 - i * pitch;
function tail_r(i) = tail_r0 + (tail_r1 - tail_r0) * (i / n_joint);

module fsphere(r) { scale([1, 1, z_squash]) sphere(r = r); }

module chain(p, on_bed = false) {
    for (j = [0 : len(p) - 2]) hull() {
        translate([p[j][0],   p[j][1],   on_bed ? bed_z(p[j][2])   : 0]) fsphere(p[j][2]);
        translate([p[j+1][0], p[j+1][1], on_bed ? bed_z(p[j+1][2]) : 0]) fsphere(p[j+1][2]);
    }
}

// ── tail: one continuous tapering solid, joints carved into it later ────
module tail_solid() {
    for (i = [0 : n_joint - 1]) hull() {
        translate([2.0, tail_y(i),     0]) sphere(r = tail_r(i));
        translate([2.0, tail_y(i + 1), 0]) sphere(r = tail_r(i + 1));
    }
    // solid tapered tip -- articulation stops before the tail gets too thin to
    // hold a joint, which is what every good flexi animal does. Shrinking the
    // joint to keep segmenting is how a tail tip becomes a fused stub.
    tip = [for (t = [0 : 0.08 : 1]) [2.0 + t * t * 6, tail_y(n_joint) - t * 18, 0]];
    for (j = [0 : len(tip) - 2]) hull() {
        translate(tip[j])     sphere(r = tail_r1 * (1 - 0.94 * (j / (len(tip) - 1))));
        translate(tip[j + 1]) sphere(r = tail_r1 * (1 - 0.94 * ((j + 1) / (len(tip) - 1))));
    }
}

// ── detail ──────────────────────────────────────────────────────────────
// A seahorse is armour: bony rings all the way down, with a tubercle at each
// ring's corners. That repetition is most of what makes one read as detailed.
module ring_at(p, q, r, w, proud, nub) {
    a = atan2(q[1] - p[1], q[0] - p[0]);
    translate([p[0], p[1], 0]) rotate([0, 0, a]) {
        rotate([0, 90, 0]) scale([z_squash, 1, 1])
            cyl(h = w, r = r + proud, rounding = min(0.9, w * 0.42));
        for (s = [-1, 1]) translate([0, s * (r + proud * 0.35), 0])
            scale([1.15, 1, 1.1]) sphere(r = nub, $fn = 14);
    }
}

module trunk_rings() {
    // resampled along the trunk so the rings are evenly spaced, not clustered
    // wherever the control points happened to fall
    // kept clear of the first joint's socket, which reaches up to y = +1.65
    steps = 9;
    for (k = [1 : steps]) {
        t  = 0.06 + (k / (steps + 1)) * 0.76;
        seg = t * (len(trunk_pts) - 1);
        j  = floor(seg); f = seg - j;
        p  = [trunk_pts[j][0] + (trunk_pts[j+1][0] - trunk_pts[j][0]) * f,
              trunk_pts[j][1] + (trunk_pts[j+1][1] - trunk_pts[j][1]) * f];
        r  = trunk_pts[j][2] + (trunk_pts[j+1][2] - trunk_pts[j][2]) * f;
        ring_at(p, [trunk_pts[j+1][0], trunk_pts[j+1][1]], r, 2.3, 0.55, 0.85);
    }
}

module tail_rings() {
    // one ring per segment, sat just behind each joint so the carve does not
    // eat it, tapering with the tail
    for (i = [0 : n_joint - 1]) {
        y = tail_y(i) - ring_d;
        r = tail_r(i + ring_d / pitch);
        ring_at([2.0, y], [2.0, y - 1], r, 1.8, 0.45, 0.72 - 0.02 * i);
    }
}

module coronet() {
    for (k = [0 : 4]) {
        a = -34 + k * 17;
        translate([-12.6, 61.8, bed + 2.2 - sink]) rotate([0, 0, a])
            translate([0, 0.4, 0]) rotate([-90, 0, 0])
                cylinder(h = 8.6 - abs(k - 2) * 1.5, r1 = 2.1, r2 = 0.5, $fn = 20);
    }
}

module head_spines() {
    // cheek spine and eye ridge -- the two the silhouette actually shows
    translate([-11.2, 54.6, 0]) rotate([0, 0, -58])
        rotate([-90, 0, 0]) cylinder(h = 5.2, r1 = 1.9, r2 = 0.5, $fn = 18);
    translate([-15.4, 59.4, 0]) rotate([0, 0, 28])
        rotate([-90, 0, 0]) cylinder(h = 4.0, r1 = 1.6, r2 = 0.45, $fn = 18);
}

module eye_sockets() {
    for (s = [-1, 1]) translate([-14.4, 57.9, s * 3.6]) scale([1.15, 1, 1]) sphere(r = 2.6);
}
module eye_pupils() {
    // Reaches inboard past the socket's inner boundary to bite into the head's
    // solid core. Sat almost concentric inside the socket it just floats -- a
    // loose ball in each eye, invisible in every render.
    for (s = [-1, 1]) translate([-14.5, 57.95, s * 2.3]) scale([1.05, 1, 1]) sphere(r = 2.1);
}
module gills() {
    for (s = [-1, 1]) translate([-10.4, 55.2, s * 4.0])
        scale([1, 1.5, 1]) sphere(r = 1.5);
}
module mouth() {
    translate([-33.2, 54.9, 0]) scale([1, 1, 0.55]) sphere(r = 1.5);
}

// Fins are the convex hull of outline points, each a sphere squashed flat in Z,
// then raised rays on top -- a real fan, lying in the print plane so it needs no
// support. Scaling a cut sphere (a first attempt) just gave a squashed ball.
module fin(pts, thick, rib = 0.9) {
    hull() for (q = pts) translate([q[0], q[1], bed + thick * rib - sink])
        scale([1, 1, thick]) sphere(r = rib);
}
module fin_rays(base, tips, thick, rib = 0.55) {
    for (q = tips) hull() {
        translate([base[0], base[1], bed + thick * rib * 2.1 - sink])
            scale([1, 1, thick * 0.8]) sphere(r = rib);
        translate([q[0], q[1], bed + thick * rib * 2.1 - sink])
            scale([1, 1, thick * 0.8]) sphere(r = rib * 0.8);
    }
}

dorsal_pts  = [[2.0, 15.0], [11.5, 19.0], [15.5, 26.5], [13.5, 34.5], [5.5, 38.0], [-0.5, 33.0]];
dorsal_base = [3.0, 26.0];
dorsal_tips = [[13.8, 20.5], [15.2, 26.0], [13.6, 31.5], [9.8, 35.6], [5.4, 36.4]];
pect_pts    = [[-8.8, 51.2], [-14.2, 47.0], [-12.0, 42.6], [-5.8, 46.4]];
pect_base   = [-8.0, 49.0];
pect_tips   = [[-13.4, 46.6], [-12.6, 43.6], [-9.6, 43.2]];

// ── OBC mark ────────────────────────────────────────────────────────────
// A raised medallion among the bony plates, with OBC standing on it.
//
// Two earlier attempts failed for the same underlying reason: the flank is
// curved, so nothing flat will sit on it. Engraving 0.65mm into that curve was
// unreadable, and raising letters that follow the curve made them lumpy and
// broken. Milling a flat facet instead does not help either -- the flank drops
// so fast that a facet cut deep enough to be 16mm wide would take 1.4mm off the
// body.
//
// So the badge is its own flat-topped disc standing proud of the flank, and the
// letters sit on that flat. Same reasoning as a coin: the device is proud, and
// the field it sits on is flat.
mark_at   = [0.8, 28.0];
badge_top = 7.6;     // above the flank's peak of ~6.9, so the disc reads as applied

module obc_badge() {
    translate([mark_at[0], mark_at[1], 0]) scale([1.58, 1, 1])
        cyl(h = badge_top * 2, r = 5.9, rounding = 1.1, $fn = 44);
}
module obc_letters() {
    translate([mark_at[0], mark_at[1] - 0.2, badge_top - 0.35]) rotate([0, 0, -6])
        linear_extrude(height = 1.35)
            text("OBC", size = 5.2, font = "Liberation Sans:style=Bold",
                 halign = "center", valign = "center", $fn = 24);
}

// ── assembly ────────────────────────────────────────────────────────────
module creature_solid() {
    chain(snout_pts, on_bed = true);
    chain(head_pts);
    chain(trunk_pts);
    tail_solid();
    trunk_rings();
    tail_rings();
    coronet();
    head_spines();
    fin(dorsal_pts, 1.7);
    fin_rays(dorsal_base, dorsal_tips, 1.7);
    fin(pect_pts, 1.3);
    fin_rays(pect_base, pect_tips, 1.3);
    obc_badge();
    obc_letters();
}

// Each joint is carved at its own place along the tail, and in the curled
// preview every joint downstream carries the accumulated rotation.
module carve(i) {
    if (i < n_joint) {
        translate([2.0, tail_y(i), 0]) rotate([0, 0, -90]) joint_cutter();
        translate([2.0, tail_y(i), 0]) rotate([0, 0, curl])
            translate([-2.0, -tail_y(i), 0]) carve(i + 1);
    }
}
module posed_solid(i) {
    if (i < n_joint) {
        translate([2.0, tail_y(i), 0]) rotate([0, 0, curl])
            translate([-2.0, -tail_y(i), 0]) posed_solid(i + 1);
    } else creature_solid();
}

module seahorse() {
    difference() {
        union() {
            difference() {
                // a ternary cannot stand in for a module CALL in OpenSCAD
                if (pose == "curled") posed_solid(0); else creature_solid();
                eye_sockets(); gills(); mouth();
            }
            eye_pupils();
        }
        carve(0);
        translate([0, 0, bed]) cube([500, 500, 500], anchor = TOP);
    }
}

test_ang = 0;
// Swing test on the real joint. Two things it has to get right, both learned
// the hard way: the test section must be bounded to about one pitch either side
// of the joint, and the cutter cones must be long enough to cover all of it.
// Running the model's own 11mm cones against the full tail left both pieces
// unassigned past d=11 and abutting there, which reported a collision at almost
// zero degrees on a joint that is actually fine.
module jt_cup(rho, a) {
    union() {
        sphere(r = rho);
        rotate([0, 90, 0]) cylinder(h = 40, r1 = 0, r2 = 40 * tan(a));
    }
}
module jt_tail() {
    hull() {
        translate([0,  9.0, 0]) sphere(r = tail_r(1));
        translate([0, -9.0, 0]) sphere(r = tail_r(2));
    }
}
module jt_A() { difference() { jt_tail(); rotate([0, 0, -90]) jt_cup(R + clear, phi_out); } }
module jt_B() { intersection() { jt_tail(); rotate([0, 0, -90]) jt_cup(R, phi_in); } }

if (part == "joint_test") {
    intersection() { jt_A(); rotate([0, 0, test_ang]) jt_B(); }
} else seahorse();
