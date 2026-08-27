include <BOSL2/std.scad>

// Print-in-place articulated axolotl -- v2, fixing 2 real defects found by
// numeric verification of v1:
//   1. ball_rod()'s rod cylinder ran from z=0 to z=+rod_len (away from the
//      ball, which sits at z=-rod_len) -- the ball was a disconnected
//      island, never actually attached to its own segment.
//   2. Adjacent capsules met at IDENTICAL end-sphere position+radius (zero
//      gap, matching radii) -- welding the whole backbone into one rigid
//      piece regardless of the joints. Independently, a hull(sphere,sphere)
//      capsule's rounded end bulges PAST its own nominal height along the
//      central axis (up to local z = h + end_r, not just z = h) -- so even
//      mismatched radii wouldn't have prevented overlap into the next
//      segment's space.
// Fix: jointed segment ends are FLAT discs (no bulge past z=h), and a real
// air gap separates every segment pair -- the ONLY thing bridging that gap
// is the thin rod, so the mechanism is what holds the chain together, not
// touching capsule material.

function embed_z(h) = h * 0.80;
// rod must span the full gap PLUS the distance from the upper segment's
// (now gapped) local bottom down to the lower segment's embedded socket.
function rod_len_for(h, gap) = (h - embed_z(h)) + gap;

module capsule(bottom_r, top_r, h, flat_bottom = false, flat_top = false) {
    hull() {
        if (flat_bottom) cylinder(r = bottom_r, h = 0.02, $fn = 40);
        else sphere(r = bottom_r, $fn = 40);
        translate([0, 0, h]) {
            if (flat_top) cylinder(r = top_r, h = 0.02, $fn = 40);
            else sphere(r = top_r, $fn = 40);
        }
    }
}

module socket_cavity(ball_r, clearance, wall, rod_r, reach) {
    cavity_r = ball_r + clearance;
    opening_r = rod_r + 1.0;
    sphere(r = cavity_r, $fn = 48);
    cylinder(h = reach, r = opening_r, $fn = 32);
}

// FIXED: cylinder now spans from local z=-rod_len (where the ball is) UP
// to local z=0 (this segment's own bottom face) -- genuinely connects the
// ball to the segment instead of extruding away from it into empty air.
module ball_rod(ball_r, rod_r, rod_len) {
    translate([0, 0, -rod_len]) sphere(r = ball_r, $fn = 48);
    translate([0, 0, -rod_len]) cylinder(h = rod_len, r = rod_r, $fn = 32);
}

// ---- segment body dimensions ----
head_h = 30;  head_b = 10; head_t = 12;
body1_h = 26; body1_b = 12; body1_t = 10;
body2_h = 24; body2_b = 10; body2_t = 7;
tail_h = 24;  tail_b = 7;  tail_t = 1.5;

// ---- joint parameters (per the spec) + real air gaps ----
j1_ball = 6; j1_clear = 0.45; j1_wall = 2.5; j1_rod = 2.4; j1_gap = 3.0;
j2_ball = 5; j2_clear = 0.45; j2_wall = 2.2; j2_rod = 2.0; j2_gap = 2.5;
j3_ball = 4; j3_clear = 0.45; j3_wall = 2.0; j3_rod = 1.6; j3_gap = 2.0;

j1_rodlen = rod_len_for(head_h, j1_gap);   // 6.0 + 3.0 = 9.0
j2_rodlen = rod_len_for(body1_h, j2_gap);  // 5.2 + 2.5 = 7.7
j3_rodlen = rod_len_for(body2_h, j3_gap);  // 4.8 + 2.0 = 6.8

// world-Z stacking offsets, WITH gaps between segments
z_body1 = head_h + j1_gap;
z_body2 = z_body1 + body1_h + j2_gap;
z_tail  = z_body2 + body2_h + j3_gap;

module head() {
    difference() {
        capsule(head_b, head_t, head_h, flat_bottom = false, flat_top = true);
        translate([0, 0, embed_z(head_h)])
            socket_cavity(j1_ball, j1_clear, j1_wall, j1_rod, head_h);
    }
}

module body1() {
    union() {
        difference() {
            capsule(body1_b, body1_t, body1_h, flat_bottom = true, flat_top = true);
            translate([0, 0, embed_z(body1_h)])
                socket_cavity(j2_ball, j2_clear, j2_wall, j2_rod, body1_h);
        }
        ball_rod(j1_ball, j1_rod, j1_rodlen);
    }
}

module body2() {
    union() {
        difference() {
            capsule(body2_b, body2_t, body2_h, flat_bottom = true, flat_top = true);
            translate([0, 0, embed_z(body2_h)])
                socket_cavity(j3_ball, j3_clear, j3_wall, j3_rod, body2_h);
        }
        ball_rod(j2_ball, j2_rod, j2_rodlen);
    }
}

module tail() {
    union() {
        capsule(tail_b, tail_t, tail_h, flat_bottom = true, flat_top = false);
        ball_rod(j3_ball, j3_rod, j3_rodlen);
    }
}

union() {
    head();
    translate([0, 0, z_body1]) body1();
    translate([0, 0, z_body2]) body2();
    translate([0, 0, z_tail]) tail();
}
