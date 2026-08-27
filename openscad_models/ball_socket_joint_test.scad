include <BOSL2/std.scad>

// Isolated ball-and-socket joint test -- print-in-place captured joint.
// Ball is centered at the origin; socket cavity is ALSO centered at the
// origin (by construction, not by hand-derived offset math) so ball and
// socket coincide trivially here. This isolated test exists to validate
// the MECHANISM (real clearance, no coincident vertices, channel actually
// breaches the housing) before reusing it at 3 hand-placed positions in
// the full multi-segment assembly, where coincidence is NOT free and
// needs real verification.
ball_r = 6;
clearance = 0.45;
wall = 2.5;
rod_r = 2.4;
opening_r = rod_r + 1.0;   // generous rotational clearance around the rod

cavity_r = ball_r + clearance;
outer_r = cavity_r + wall;

module socket_block() {
    difference() {
        cube([outer_r * 2 + 4, outer_r * 2 + 4, outer_r * 2 + 4], center = true);
        sphere(r = cavity_r, $fn = 48);
        // full-height channel through the whole block along Z -- deliberately
        // overshoots past the housing's own surface on both ends (Technique 4's
        // "off-by-a-hair leaves it unengraved" lesson, applied to a through-cut
        // instead of an engrave: better to overshoot than risk an uncut sliver).
        cylinder(h = outer_r * 4, r = opening_r, center = true, $fn = 32);
    }
}

module ball_rod() {
    sphere(r = ball_r, $fn = 48);
    translate([0, 0, ball_r])
        cylinder(h = outer_r * 2, r = rod_r, $fn = 32);
}

union() {
    socket_block();
    ball_rod();
}
