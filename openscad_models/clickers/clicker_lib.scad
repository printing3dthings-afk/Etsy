// Shared Cherry MX interface for the "Click Into Celebration" clickers
// (2026-10-29). Every switch dimension is the one dumpling_clicker.scad took
// from Cherry's MX1A datasheet and keycap slot spec, where it was measured on
// the exported mesh; copied here, not re-guessed.
//
// Every base is two prints, split at the plate. The upper one has the switch
// plate as its floor, printed flat on the bed; the lower one is a cup whose
// open well takes the switch's body and pins. A plate printed over its own
// well, as the dumpling basket's is, is a ceiling the slicer props: run
// through product_gate (2026-10-29) the basket needs 10,122 support moves, the
// first version of the tin 2,168, all under the plate.
//
// Placed from S, the top face of the lower print; the plate's top is
// P = S + mx_plate_t. A cap is modelled with its underside at z = 0 and sits
// at mx_cap_z(P).
//
//   mx_plate_cut(S)   subtract from the upper print: the 14 mm cutout
//   mx_well_cut(S)    subtract from the lower print: room for the body, its
//                     clips and its pins, in any of the four orientations
//   mx_cap_cut()      subtract from a cap: the cavity that swallows the
//                     housing through the whole travel, leaving the socket
//                     post, and the cross socket in it

mx_housing  = 15.6;     // top housing, square, rests on the plate
mx_cutout   = 14.0;     // plate cutout
mx_plate_t  = 1.5;      // plate the clips expect
mx_below    = 5.0;      // body below the plate
mx_pins     = 3.3;      // pins below the body
mx_above    = 6.6;      // housing above the plate
mx_stem_h   = 3.6;      // cross proud of the housing
mx_travel   = 4.0;

// An FDM hole prints under size, so the 4.1 x 1.17 keycap cross is opened by
// sock_fit. The loose cap is the same file at -D sock_fit=0.22, the two-step
// ladder the dumpling clicker and the best-selling Printables clicker ship.
sock_fit    = 0.12;
sock_span   = 4.10 + sock_fit;
sock_arm    = 1.17 + sock_fit;
sock_depth  = 3.4;      // of the 3.6 mm cross

well_r      = 12.0;     // clears the body's 9.83 half-diagonal, its clips and pins
well_h      = mx_below + mx_pins + 0.6;
JOINT       = 2.0;      // the upper print's spigot drops this far into the lower's lip
JOINT_CLR   = 0.2;      // radial
LIP_W       = 1.2;      // the lower print's lip: the gate's wall floor

function mx_housing_top(P) = P + mx_above;
function mx_cap_z(P)       = P + mx_above + mx_stem_h - sock_depth;   // P + 6.8
function mx_cap_z_down(P)  = mx_cap_z(P) - mx_travel;                 // P + 2.8

// The cap's underside. The housing reaches 3.8 into the cap at full press, so
// the cavity is 4.4 deep. Square and aligned with the cross, because the cross
// keys the cap to the housing in all four orientations and a square 16.4 cavity
// needs 3.4 mm less cap round it than the 22.06 circle the housing's corners
// sweep. Its ceiling is a 5.4 mm bridge from the walls to the post.
cav_w       = mx_housing + 0.8;
cav_h       = 4.4;
// 5.6 across like a moulded MX keycap's stem: it rides down into the housing's
// stem opening. 0.594 mm of wall at the cross's arm tips, measured on the
// dumpling's mesh; a 9.8k-download FDM keycap measures 0.628.
post_r      = 2.80;
cap_floor   = 1.8;      // above the cavity: nine layers over the bridge

module mx_cap_cut() {
    difference() {
        translate([-cav_w / 2, -cav_w / 2, -0.4]) cube([cav_w, cav_w, cav_h + 0.4]);
        translate([0, 0, -1]) cylinder(h = cav_h + 2, r = post_r, $fn = 64);
    }
    // dips below the mouth so the cut overlaps (Technique 4's buried cut)
    translate([0, 0, -0.4]) linear_extrude(sock_depth + 0.4) {
        square([sock_span, sock_arm], center = true);
        square([sock_arm, sock_span], center = true);
    }
    // Each arm's ceiling is a gable at 60 deg, not flat. Flat, it is a cross of
    // 1.3 mm slots the slicer filled with support, inside the socket, where it
    // could never be cleaned out; at 50 deg it still propped one arm. The stem
    // still stops at sock_depth: its edges sit 0.06 inside the slot, where the
    // gable is 0.1 up.
    for (r = [0, 90]) rotate([0, 0, r]) hull() {
        translate([-sock_span / 2, -sock_arm / 2, sock_depth - 0.01]) cube([sock_span, sock_arm, 0.01]);
        translate([-sock_span / 2, 0, sock_depth + sock_arm / 2 * tan(60)]) rotate([0, 90, 0]) cylinder(h = sock_span, r = 0.01, $fn = 4);
    }
}

module mx_plate_cut(S) translate([-mx_cutout / 2, -mx_cutout / 2, S - 1]) cube([mx_cutout, mx_cutout, mx_plate_t + 1.02]);
module mx_well_cut(S)  translate([0, 0, S - well_h]) cylinder(h = well_h + 1, r = well_r, $fn = 128);

// A stand-in for the switch, never exported: the fit is seen, not assumed.
module mx_mock(S, press = 0) let (P = S + mx_plate_t) {
    color("gray") {
        translate([-6.95, -6.95, P - mx_plate_t - mx_below]) cube([13.9, 13.9, mx_below + mx_plate_t]);
        translate([-mx_housing / 2, -mx_housing / 2, P]) cube([mx_housing, mx_housing, mx_above]);
    }
    color("dodgerblue") translate([0, 0, mx_housing_top(P) - press]) linear_extrude(mx_stem_h) {
        square([4.10, 1.17], center = true);
        square([1.17, 4.10], center = true);
    }
}

// A stroke of round-ended segments through points, for piped icing.
module pipe2d(pts, w) for (k = [0 : len(pts) - 2]) hull() {
    translate(pts[k]) circle(d = w, $fn = 16);
    translate(pts[k + 1]) circle(d = w, $fn = 16);
}
// a zigzag across a limb: centre c, along direction a (deg), half-span s
function zigzag(c, a, s, amp, n) = [for (i = [0 : n])
    let (t = -s + 2 * s * i / n, u = (i % 2 == 0 ? -amp : amp))
    c + [cos(a), sin(a)] * u + [-sin(a), cos(a)] * t];
