// Snowfall Plinko (hourglass, Scott's form 4): the test print (2026-11-16). It tests the one
// risky part, before the board is designed round it: balls that print loose inside a closed
// board, under a lattice front, and roll free (plinko_budget.py, ENGINEERING.md).
//
// How each ball meets the floor is the variant, marked by notches in the outside wall:
//   1 notch   the ball's point hangs 0.2 (one layer of air) above the floor   (top pocket)
//   2 notches 0.4 (two layers)                                              (the hourglass)
//   3 notches the point printed onto the floor through a 0.6 neck, snapped with a toothpick
//             (bottom pocket)
// The hourglass is a small working one: a neck, two rows of pegs each side and three bins at
// each end, so the flow and the gaps get tested too. The pockets only hold four balls each.
// (Three hourglasses sliced at 35 min, over the handbook's 30.)
//
// Printed lying on its back: the bed face is the board's back, the lattice is its front.
// In use it stands up (+y up), the balls' points facing the back, so each rolls in the
// board's plane as a true 5 mm circle.
//
//   part = "coupon" | "body" (without its balls) | "balls" | "variant" (with v) | "gate_skip"

part = "coupon";
v = 0;
$fn = 48;

BALL = 5.0;
TIP = BALL / 2 * sqrt(2);          // the 45 deg point, below the ball's centre
FLOATS = [0.2, 0.4, 0];            // 0: printed onto the floor through NECK
NECK = 0.6;
FLOOR = 1.2;
LAT_GAP = 0.6;
D = 0.4 + BALL / 2 + TIP + LAT_GAP;   // inside depth: the tallest ball plus the lattice gap (7.04)
LAT_T = 1.0;
LAT_BAR = 1.2;
LAT_OPEN = 3.2;
WALL = 1.6;

// the hourglass, inside. Every gap a ball meets is a pass (>= 6.5, square to the surfaces)
// or a stop (<= 3.5): the fit check measures them
W = 26; H = 46.6;
NECK_W = 7; NECK_L = 2;            // the neck: half-length NECK_L either side of the middle
TAPER_END = 14;                    // the taper runs from the neck to |y| = 14, then full width
PEG_R = 1.2;
PEGS = [[0, 10.3], [-4.9, 17.8], [4.9, 17.8]];   // each half, mirrored for -y; the second
                                                  // row's pegs head the bin dividers
BALLS_HG = [[0, -20], [-9.25, -20], [9.25, -20], [-7, -12]];   // as printed, in the lower bins
// the pockets: four balls each
P = 13.6;
BALLS_P = [[-3.4, -3.4], [3.4, -3.4], [-3.4, 3.4], [3.4, 3.4]];

HG_W = W + 2 * WALL; HG_H = H + 2 * WALL;
P_X = HG_W / 2 - WALL / 2 + P / 2 + WALL;          // the pockets' centre x
P_Y = [HG_H / 2 - WALL - P / 2, -HG_H / 2 + WALL + P / 2];   // top pocket (variant 1), bottom (3)
Z_TOP = FLOOR + D + LAT_T;

module hg_void2d() {
    hw = W / 2;
    polygon([[-NECK_W / 2, -NECK_L], [-hw, -TAPER_END], [-hw, -H / 2], [hw, -H / 2], [hw, -TAPER_END],
             [NECK_W / 2, -NECK_L], [NECK_W / 2, NECK_L], [hw, TAPER_END], [hw, H / 2], [-hw, H / 2],
             [-hw, TAPER_END], [-NECK_W / 2, NECK_L]]);
}
module hg_posts2d() for (s = [-1, 1]) {
    for (p = PEGS) translate([p[0], s * p[1]]) circle(r = PEG_R, $fn = 32);
    for (x = [-4.9, 4.9]) translate([x - PEG_R, s > 0 ? 17.8 : -H / 2 - 0.01]) square([2 * PEG_R, H / 2 - 17.8 + 0.01]);
}
module outline2d() union() {
    square([HG_W, HG_H], center = true);
    for (y = P_Y) translate([P_X, y]) square([P + 2 * WALL, P + 2 * WALL], center = true);
}
module voids2d() { hg_void2d(); for (y = P_Y) translate([P_X, y]) square([P, P], center = true); }
// bars across each void (level in use), P or W long, resting on the walls, pegs and tapers
module lattice_open2d() intersection() {
    voids2d();
    for (k = [-7 : 7]) translate([0, k * (LAT_BAR + LAT_OPEN)]) square([200, LAT_OPEN], center = true);
}

module body() difference() {
    union() {
        difference() {
            linear_extrude(FLOOR + D) outline2d();
            translate([0, 0, FLOOR]) linear_extrude(D + 1) voids2d();
        }
        translate([0, 0, FLOOR - 0.01]) linear_extrude(D + 0.02) hg_posts2d();
        translate([0, 0, FLOOR + D - 0.01]) linear_extrude(LAT_T + 0.01) difference() { outline2d(); lattice_open2d(); }
    }
    // the variants' notches: upright grooves in the outside walls, beside each
    for (k = [0 : 1]) translate([(k - 0.5) * 2 - 0.45, -HG_H / 2 - 1, -1]) cube([0.9, 1.6, Z_TOP + 2]);   // hourglass: 2
    for (n = [1, 3]) let (y = n == 1 ? P_Y[0] : P_Y[1])
        for (k = [0 : n - 1]) translate([P_X + P / 2 + WALL - 0.6, y + (k - (n - 1) / 2) * 2 - 0.45, -1]) cube([1.6, 0.9, Z_TOP + 2]);
    // a 0.4 chamfer at the foot (elephant's foot)
    // (in 0.1 steps: the outline is an L, so a scaled extrusion can't make it)
    for (k = [0 : 3]) translate([0, 0, k * 0.1 - 0.01]) linear_extrude(0.11)
        difference() { offset(delta = 1) outline2d(); offset(delta = -(0.4 - k * 0.1)) outline2d(); }
}

// a teardrop ball, its centre at height c above the bed; f = 0 prints its point onto the floor
module ball(f) {
    c = f > 0 ? FLOOR + f + TIP : FLOOR + TIP - NECK / 2;
    hull() {
        translate([0, 0, c]) sphere(d = BALL, $fn = 48);
        if (f > 0) translate([0, 0, c - TIP]) cylinder(r = 0.01, h = 0.01);
        else translate([0, 0, FLOOR - 0.01]) cylinder(r = NECK / 2, h = 0.01);
    }
}
module balls_of(i) {
    if (i == 1) for (b = BALLS_HG) translate([b[0], b[1], 0]) ball(FLOATS[1]);
    else for (b = BALLS_P) translate([P_X + b[0], (i == 0 ? P_Y[0] : P_Y[1]) + b[1], 0]) ball(FLOATS[i]);
}

// product_gate's skip region (not printed): variant 3's necks, 0.6 across by design
module gate_skip() for (b = BALLS_P) translate([P_X + b[0], P_Y[1] + b[1], FLOOR - 0.5]) cylinder(r = 1.5, h = 2.2);

if (part == "coupon") { body(); for (i = [0 : 2]) balls_of(i); }
else if (part == "body") body();
else if (part == "balls") for (i = [0 : 2]) balls_of(i);
else if (part == "variant") balls_of(v);
else if (part == "gate_skip") gate_skip();
echo("inside depth", D, "height", Z_TOP, "hourglass outside", HG_W, HG_H, "pockets at x", P_X);
