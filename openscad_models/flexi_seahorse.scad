include <BOSL2/std.scad>

/*
  Flexi seahorse -- print-in-place articulated tail, no supports, no assembly.

  Joint geometry was designed and verified on its own before any of the animal
  was sculpted, which is the order the reference material insists on: movement,
  then joint clearance, then body. Every number below came out of that study:

    ball R 2.9    clearance 0.25/side    neck dia 2.9    mouth relief 22 deg
    pitch 8.7     collar wall 1.6        bead dia 9.5
    -> retention 0.42mm, swing 16 deg per joint, 12 joints = 192 deg of curl

  Retention and swing pull against each other and both are set by the collar's
  narrowest inner radius -- the "throat" -- which is where the cup sphere
  closing in meets the mouth cone opening out. Widen the mouth for swing and
  the throat opens and the tail pulls apart; narrow it for grip and the tail
  goes stiff. Neither surface tells you the answer on its own.

  Swing is governed by pitch/R, NOT by the mouth angle: the limit is the collar
  rim striking the next segment's flank. At pitch/R = 3.0 it is 16-18 deg; at
  2.5 it drops to 12. Change the pitch and the swing changes even though the
  joint is identical.

  ORIENTATION IS STRUCTURAL, not a convenience. Printed flat, every neck's
  fibre stress runs along the layer plane, which is the strong direction. A
  neck standing up in Z would load the layer bonds in tension, and that is how
  these snap. The tail therefore curls in the print plane -- which is also the
  plane a real seahorse curls in, so nothing is compromised for it.
*/

part = "seahorse";   // seahorse | joint_test
pose = "flat";       // flat = as printed (straight tail) | curled = preview only
$fn  = 48;

// ── verified joint ──────────────────────────────────────────────────────
R       = 2.9;
clear   = 0.25;
neck_r  = 1.45;
mouth   = 22;
pitch   = 8.7;
wall    = 1.6;
n_tail  = 11;

Rc      = R + clear;
bead_r  = Rc + wall;
lip     = R * 0.78;
// Negative = forward, toward the belly, which is the way a seahorse actually
// grips. Preview only: the printed file is always the straight pose.
curl    = (pose == "curled") ? -14 : 0;

// Belly is trimmed flat: a fully round body printed flat runs past 45 degrees
// of overhang through its whole lower quadrant, and every reference model
// flattens it. The plane sits 0.8mm below the deepest cup so no joint is ever
// broken open by the trim.
z_flat  = Rc + 0.8;

// ── tail ────────────────────────────────────────────────────────────────
module tail_ball_neck() {
    sphere(r = R);
    hull() {
        sphere(r = neck_r);
        translate([pitch * 0.5, 0, 0]) sphere(r = neck_r * 1.05);
    }
}

module tail_bead() {
    // Two stages. The bead starts swelling as soon as it clears the previous
    // collar's rim, then runs as a barrel into its own collar. Starting the
    // swell late (the first attempt) left ~4mm of bare neck showing at every
    // joint and the tail read as beads on a string; starting it at mid-pitch
    // instead makes every segment an arrowhead. The earliest it may start is
    // set by the previous segment's mouth relief, which at the rim allows
    // neck_r + clear + lip*tan(mouth) = 2.61mm.
    hull() {
        translate([pitch * 0.46, 0, 0]) sphere(r = 1.95);
        translate([pitch * 0.79, 0, 0]) sphere(r = bead_r * 0.96);
    }
    hull() {
        translate([pitch * 0.79, 0, 0]) sphere(r = bead_r * 0.96);
        translate([pitch, 0, 0]) sphere(r = bead_r);
    }
}

// A seahorse's tail is four rows of bony plates, so each bead gets a raised
// ring at its equator and a dorsal crest. Both sit on the collar, pointing
// away from the neighbour, so neither eats into the swing -- re-checked after
// they were added rather than assumed.
module tail_detail(i) {
    t = i / (n_tail - 1);
    translate([pitch, 0, 0]) {
        rotate([0, 90, 0]) cyl(h = 2.6, r = bead_r + 0.35, rounding = 1.1);
        translate([0, 0, bead_r - 0.5]) scale([1.9, 1.1, 1])
            sphere(r = 1.25 - 0.3 * t);
        for (s = [-1, 1]) translate([0, s * (bead_r - 0.5), 0])
            scale([1.7, 1, 1.1]) sphere(r = 1.0 - 0.22 * t);
    }
}

// Two stages, and the second one is the whole trick. A single cone has to
// serve two jobs that fight: stay narrow near the ball so the throat grips,
// and be wide at the rim so the next segment can swing. Splitting it lets the
// narrow cone set the throat and a 45-degree flare chamfer the rim. With one
// 22-degree cone the real decorated segment could only manage 6 degrees --
// the square rim was catching the next bead almost immediately.
flare_d = 1.75;      // where the rim chamfer starts, just past the throat
module mouth_relief() { translate([pitch, 0, 0]) mouth_cone(); }
module mouth_cone() {
    L = bead_r + 4;
    rotate([0, 90, 0]) {
        cylinder(h = L, r1 = neck_r + clear,
                 r2 = neck_r + clear + L * tan(mouth), $fn = 48);
        translate([0, 0, flare_d])
            cylinder(h = L, r1 = neck_r + clear + flare_d * tan(mouth),
                     r2 = neck_r + clear + flare_d * tan(mouth) + L, $fn = 48);
    }
}

// The trunk has to act as segment zero: cup the first ball, relieve its mouth,
// and stop at the same rim distance every bead does. Without this the body
// simply engulfs that ball and the top joint prints solid -- one dead joint
// that looks identical to a working one in any render.
module body_socket() {
    sphere(r = Rc);
    mouth_cone();
    translate([lip, 0, 0]) cube([120, 120, 120], anchor = LEFT);
}

module tail_segment(i) {
    difference() {
        union() { tail_ball_neck(); tail_bead(); tail_detail(i); }
        translate([pitch, 0, 0]) sphere(r = Rc);
        mouth_relief();
        translate([pitch + lip, 0, 0]) cube([60, 60, 60], anchor = LEFT);
    }
}

// The last joint carries a solid tapered tip instead of another bead. Real
// flexi animals stop articulating before the tail gets too thin to hold a
// joint -- shrinking the joint to keep segmenting is what turns a tail tip
// into a fused stub or a snapped one.
module tail_tip() {
    hull() { sphere(r = R); translate([2.4, 0, 0]) sphere(r = bead_r * 0.92); }
    tip = [for (t = [0 : 0.1 : 1])
        [2.4 + t * 21, -t * t * 5.5, 0]];
    for (j = [0 : len(tip) - 2]) hull() {
        translate(tip[j])     sphere(r = bead_r * 0.92 - 3.6 * (j / (len(tip) - 1)));
        translate(tip[j + 1]) sphere(r = bead_r * 0.92 - 3.6 * ((j + 1) / (len(tip) - 1)));
    }
}

module tail_chain(i) {
    if (i < n_tail) {
        tail_segment(i);
        translate([pitch, 0, 0]) rotate([0, 0, curl]) tail_chain(i + 1);
    } else {
        tail_tip();
    }
}

// ── body ────────────────────────────────────────────────────────────────
// Hull-chains of spheres along hand-picked paths: one continuous blended
// surface, no stacked-primitive seams.
// A seahorse reads by three things and nothing else: a head set nearly at a
// right angle to the body, a deep forward chest, and a tail that curls the
// same way the head faces. Forward is -X.
z_squash  = 0.80;    // body is deeper front-to-back than it is thick

trunk_pts = [[2.0, -2, 5.5], [2.4, 4, 6.6], [3.0, 10, 7.8], [2.0, 21, 8.8], [-1.0, 32, 8.4],
             [-5.0, 42, 7.2], [-8.0, 50, 6.0]];
head_pts  = [[-9.6, 53.5, 6.0], [-12.6, 57.0, 6.3], [-16.4, 58.2, 5.2]];
snout_pts = [[-19.5, 57.6, 3.4], [-24.5, 56.6, 2.7], [-29.5, 55.6, 2.4],
             [-32.5, 55.1, 2.7]];

// Spheres are squashed in Z individually, never the whole chain -- scaling the
// chain would drag every path point toward the plane too.
//
// bed_z(): anything thinner than the belly trim would otherwise hang in mid
// air. The trunk, head and tail beads are all fatter than 2*z_flat so the trim
// gives them a flat underside; the snout, fins and coronet are not, and left on
// the centreline they float 1-2mm above the plate with nothing under them. An
// overhang scan reported a 90-degree face at the snout tip for exactly this
// reason. Every reference flexi animal is flat underneath for the same reason,
// so thin features are dropped to sit ON the bed rather than centred.
bed      = -z_flat;
sink     = 0.6;      // push thin features just below the trim plane

// Resting a thin feature exactly ON the plane leaves it tangent to the bed --
// a contact line, not a face, with a 90-degree wall rising straight off it.
// Sinking it `sink` below and letting the belly trim cut through gives a real
// flat contact and drops the snout's steepest underside from 90 to about 51.
function bed_z(r) = bed + r * z_squash - sink;

module chain_pts(p, on_bed = false) {
    for (j = [0 : len(p) - 2]) hull() {
        translate([p[j][0],   p[j][1],   on_bed ? bed_z(p[j][2])   : 0])
            scale([1, 1, z_squash]) sphere(r = p[j][2]);
        translate([p[j+1][0], p[j+1][1], on_bed ? bed_z(p[j+1][2]) : 0])
            scale([1, 1, z_squash]) sphere(r = p[j+1][2]);
    }
}

module bony_rings() {
    // Raised ring plates across the trunk, spaced along its own path.
    for (j = [1 : len(trunk_pts) - 2]) {
        p = trunk_pts[j]; q = trunk_pts[j + 1];
        a = atan2(q[1] - p[1], q[0] - p[0]);
        translate([p[0], p[1], 0]) rotate([0, 0, a]) rotate([0, 90, 0])
            scale([z_squash, 1, 1])
                cyl(h = 2.2, r = p[2] + 1.05, rounding = 0.95);
    }
}

module coronet() {
    // The crown spikes a seahorse is named for.
    for (k = [0 : 3]) {
        a = -30 + k * 21;
        translate([-12.4, 61.6, bed + 2.2 - sink]) rotate([0, 0, a])
            translate([0, 0.6, 0]) rotate([-90, 0, 0])
                cylinder(h = 8.2 - abs(k - 1.5) * 1.6, r1 = 2.2, r2 = 0.55);
    }
}

// Sockets are cut, pupils are added. A single module used as the cutter took
// the pupil out with the socket and left a bare hole -- the eye rendered as an
// open orange pit rather than an eye.
module eye_sockets() {
    for (s = [-1, 1]) translate([-14.2, 57.8, s * 3.5])
        scale([1.15, 1, 1]) sphere(r = 2.5);
}
// The pupil has to reach INBOARD past the socket's inner boundary to bite into
// the head's solid core. Sitting it almost concentric inside the socket (the
// first attempt) left it floating in the cavity -- a loose ball in each eye,
// invisible in every render and caught only by the component count coming back
// 15 instead of 13.
module eye_pupils() {
    for (s = [-1, 1]) translate([-14.3, 57.85, s * 2.3])
        scale([1.05, 1, 1]) sphere(r = 2.05);
}

// Fins are the convex hull of a handful of outline points, each a sphere
// squashed flat in Z -- a real fan shape with soft edges, lying in the print
// plane so it needs no support. Scaling a cut sphere (the first attempt) just
// produced a squashed ball on the back.
module fin(pts, thick, rib = 0.9) {
    hull() for (q = pts) translate([q[0], q[1], bed + thick * rib - sink])
        scale([1, 1, thick]) sphere(r = rib);
}

module body() {
    union() {
        chain_pts(trunk_pts);
        chain_pts(head_pts);
        chain_pts(snout_pts, on_bed = true);
        bony_rings();
        coronet();
        // dorsal: a tall fan down the back, widest at mid-body
        fin([[2.0, 16], [11.0, 20], [14.5, 27], [13.0, 34], [6.0, 38], [0.0, 34]], 1.5);
        // pectoral: the little paddle just behind the cheek
        fin([[-8.6, 51.0], [-13.5, 46.5], [-11.5, 42.5], [-5.5, 46.0]], 1.2);
    }
}

// ── assembly ────────────────────────────────────────────────────────────
tail_at = [2.0, -1.5, 0];

module seahorse() {
    difference() {
        union() {
            difference() {
                body();
                eye_sockets();
                translate(tail_at) rotate([0, 0, -90]) body_socket();
            }
            eye_pupils();
            // tail runs downward from the trunk's base
            translate(tail_at) rotate([0, 0, -90]) tail_chain(0);
        }
        translate([0, 0, -z_flat]) cube([400, 400, 400], anchor = TOP);
    }
}

// Swing is re-checked on the REAL segment, decoration and belly trim included,
// not on the bare joint study -- anything added to a bead can eat into it.
test_ang = 0;
module trimmed(m) {
    difference() { children(); translate([0, 0, -z_flat]) cube([400,400,400], anchor = TOP); }
}
if (part == "joint_test") {
    intersection() {
        trimmed() tail_segment(0);
        translate([pitch, 0, 0]) rotate([0, 0, test_ang]) trimmed() tail_segment(1);
    }
} else seahorse();
