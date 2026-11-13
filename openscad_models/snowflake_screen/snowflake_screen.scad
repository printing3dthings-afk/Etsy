// Snowflake Screen (2026-11-12): v2 of the Pleated Fan, a three-panel folding screen
// with snowflakes. Scott: "Yes" to redoing the Pleated Fan as a snowflake folding
// screen (his 2026-08-27 reference had a snowflake motif).
//
// Why it changed shape. The Pleated Fan printed standing up, so its hinge axis was
// vertical and every knuckle printed on top of the one below across a flat gap: the
// gate's slicer propped them (24,094 support moves), and its listing says supports
// off. A first v2 kept it upright with cone joints between the knuckles; the slopes
// were fine, but each knuckle's lowest ring still started over the gap (support_map),
// as any print-in-place hinge on a vertical axis must. So the panels now print FLAT:
//   - the snowflakes are on the top face, the best-printing surface, white inlaid
//     flush in the top three layers;
//   - the hinges run along the panels' edges, axis in the plate's plane: each
//     knuckle's cross-section is a circle whose lower sides are cut 37 deg from
//     upright down to a flat foot on the plate;
//   - the pin is a 90 mm length of 1.75 mm filament, pushed down through the
//     knuckles: the hole is open at the top and closed at the bottom.
// The pocket pebble case's hinge is assembled the same way, for the same reason.
//
// Millimetres. Printed: panels flat, side by side along X, hinge axes along Y at
// mid-thickness. Standing: Y is up and the top face (the snowflakes) is the front.
//
//   part = "blue" | "white" | "screen" (one colour, for the gates) | "coupon" |
//          "coupon_l" / "coupon_r" (with bore) | "posed_blue" / "posed_white"
//   bore = the pin hole's drawn diameter; the coupon tries COUPON_BORES

part = "screen";
bore = 2.0;    // Scott, 2026-11-13, from the hinge test: "Mark 1 felt better" (one notch = 2.0)
$fn = 64;

use <../brand/obc_mark.scad>

PANEL_W = 45;          // across
PANEL_H = 90;          // up, when standing
T       = 6.0;         // thick: at 5 the wall over the pin hole's point was 0.84
AXIS_Z  = 2.8;         // the hinge axis, under mid-thickness for the same reason
R_K     = T - AXIS_Z;  // knuckle radius: flush with the top; trimmed at the plate
SLOPE   = 37;          // the knuckle's lower sides and the bore's roof, deg from upright
KNUCKLES = 9;          // per hinge
K_GAP   = 0.5;         // between knuckles along the axis, and knuckle to the other panel
CLEAR   = 0.5;         // radially, the knuckle's sweep to the other panel's notch
SWEEP   = max(R_K, norm([k_foot(), AXIS_Z]));   // the knuckle's outline turns inside this
NOTCH_R = SWEEP + CLEAR;
FLOOR   = 1.2;         // the pin hole is closed this much at the bottom
WALL    = 1.2;         // the least wall over the pin hole's point (the gate's floor)
INLAY   = 0.6;         // the snowflakes: top three layers

// the knuckle's cross-section (x across the hinge, z up), centred on the axis
function k_foot() = let (m = tan(90 - SLOPE), c = AXIS_Z - R_K * sqrt(1 + m * m)) -c / m;
module knuckle2d() intersection() {
    hull() {
        translate([0, AXIS_Z]) circle(r = R_K);
        translate([-k_foot(), 0]) square([2 * k_foot(), 0.01]);
    }
    translate([-10, 0]) square([20, T]);
}
// the pin hole: a teardrop, its roof 37 deg from upright, to a point. A first draft
// cut the point flat under the top: the slicer printed that 0.9 mm bridge's edges
// as 20 overhang perimeters on the coupon.
module bore2d(d) let (r = d / 2) {
    assert(AXIS_Z + r / sin(SLOPE) <= T - WALL, "the pin hole's point is too near the top");
    hull() {
        translate([0, AXIS_Z]) circle(r = r, $fn = 32);
        translate([0, AXIS_Z + r / sin(SLOPE)]) square(0.01, center = true);
    }
}
// knuckle i of n along a hinge h long
function k_y0(i, n, h) = i * h / n + (i == 0 ? 0 : K_GAP / 2);
function k_y1(i, n, h) = (i + 1) * h / n - (i == n - 1 ? 0 : K_GAP / 2);
// along y from a to b
module along(a, b) translate([0, b, 0]) rotate([90, 0, 0]) linear_extrude(b - a) children();
// at hinge hx: owner "l" has the even knuckles, "r" the odd ones
function mine(who, n) = [for (i = [0 : n - 1]) if ((i % 2 == 0) == (who == "l")) i];
function theirs(who, n) = mine(who == "l" ? "r" : "l", n);
module knuckles(hx, who, n, h) translate([hx, 0, 0])
    for (i = mine(who, n)) along(k_y0(i, n, h), k_y1(i, n, h)) knuckle2d();
// what a part gives up round the other part's knuckles: full thickness, NOTCH_R
// either side of the axis, K_GAP past the knuckle's ends (that reaches exactly to
// the ends of this part's own knuckles beside it)
module notches(hx, who, n, h) translate([hx, 0, 0])
    for (i = theirs(who, n)) along(max(0, k_y0(i, n, h) - K_GAP), min(h, k_y1(i, n, h) + K_GAP))
        translate([-NOTCH_R, -1]) square([2 * NOTCH_R, T + 2]);
module pin_hole(hx, d, h) translate([hx, 0, 0]) along(FLOOR, h + 1) bore2d(d);

// ---------- snowflakes ----------
LINE = 1.6;
// [arm length, [[branch at (fraction of arm), branch length, angle], ...], centre ring r]
FLAKES = [
    [15, [[0.45, 5.5, 50], [0.75, 3.5, 50]], 3.0],
    [15, [[0.35, 4.0, 60], [0.62, 5.0, 40], [0.86, 2.6, 60]], 0],
    [15, [[0.55, 6.5, 45]], 4.5],
];
module seg(a, b, w) hull() { translate(a) circle(d = w, $fn = 16); translate(b) circle(d = w, $fn = 16); }
// Drawn smaller, the lines thin with the square root of the scale (never under 0.9,
// two beads) and the short branches drop out: at a full 1.6 the small flakes' arms
// ran together and printed as round blobs (first renders).
module flake2d(f, s = 1) let (L = f[0] * s, w = max(0.9, LINE * sqrt(s))) union() {
    for (k = [0 : 5]) rotate(k * 60 + 90) {
        seg([0, 0], [L, 0], w);
        for (b = f[1]) if (b[1] * s >= 1.6) let (p = [L * b[0], 0])
            for (q = [-1, 1]) seg(p, p + b[1] * s * [cos(q * b[2]), sin(q * b[2])], w);
    }
    if (f[2] * s >= 1.5) difference() { circle(r = f[2] * s + w / 2); circle(r = f[2] * s - w / 2); }
}
// each panel: a big flake and two small ones in the other panels' patterns
module panel_flakes2d(p) translate([p * PANEL_W, 0]) {
    translate([PANEL_W / 2, 58]) flake2d(FLAKES[p]);
    translate([PANEL_W / 2 + (p == 1 ? -9 : 9), 25]) flake2d(FLAKES[(p + 1) % 3], 0.42);
    translate([PANEL_W / 2 + (p == 1 ? 10 : -10), 13]) flake2d(FLAKES[(p + 2) % 3], 0.32);
}

// ---------- panels ----------
// the OBC mark on panel 0's back (the printed underside), inlaid white
MARK_AT = [PANEL_W / 2, 8, 0];
module panel_shape(p, d) difference() {
    union() {
        translate([p * PANEL_W, 0, 0]) cube([PANEL_W, PANEL_H, T]);
        if (p < 2) knuckles((p + 1) * PANEL_W, "l", KNUCKLES, PANEL_H);
        if (p > 0) knuckles(p * PANEL_W, "r", KNUCKLES, PANEL_H);
    }
    if (p < 2) { notches((p + 1) * PANEL_W, "l", KNUCKLES, PANEL_H); pin_hole((p + 1) * PANEL_W, d, PANEL_H); }
    if (p > 0) { notches(p * PANEL_W, "r", KNUCKLES, PANEL_H); pin_hole(p * PANEL_W, d, PANEL_H); }
}
module panel_blue(p, d) difference() {
    panel_shape(p, d);
    translate([0, 0, T - INLAY]) linear_extrude(1) panel_flakes2d(p);
    if (p == 0) translate(MARK_AT) obc_cut(4);
}
module panel_white(p, d) union() {
    intersection() { panel_shape(p, d); translate([0, 0, T - INLAY]) linear_extrude(INLAY) panel_flakes2d(p); }
    if (p == 0) translate(MARK_AT) obc_inlay(4);
}

// ---------- coupon: one hinge at the real size, three knuckles, two bores ----------
C_W = 16; C_H = 30; C_N = 3;
COUPON_BORES = [2.0, 2.3];
module coupon_leaf(who, d) difference() {
    union() {
        translate([who == "l" ? -C_W : 0, 0, 0]) cube([C_W, C_H, T]);
        knuckles(0, who, C_N, C_H);
    }
    notches(0, who, C_N, C_H);
    pin_hole(0, d, C_H);
}
// notches across the left leaf's outer end say which bore: 1 = 2.0, 2 = 2.3
module coupon() for (k = [0 : 1]) translate([0, k * (C_H + 6), 0]) difference() {
    union() { coupon_leaf("l", COUPON_BORES[k]); coupon_leaf("r", COUPON_BORES[k]); }
    for (j = [0 : k]) translate([-C_W + 3 + j * 2.6, -1, T - 1]) cube([1.2, 8, 2]);
}

// ---------- posed: the screen standing, both wings turned back, for renders ----------
FOLD = 40;   // deg each hinge turns from flat
module posed(c) {
    module draw(p) if (c == "blue") panel_blue(p, bore); else panel_white(p, bore);
    rotate([90, 0, 0]) {    // printed Y becomes up, the top face the front (-Y)
        draw(1);
        translate([PANEL_W, 0, AXIS_Z]) rotate([0, -FOLD, 0]) translate([-PANEL_W, 0, -AXIS_Z]) draw(0);
        translate([2 * PANEL_W, 0, AXIS_Z]) rotate([0, FOLD, 0]) translate([-2 * PANEL_W, 0, -AXIS_Z]) draw(2);
    }
}

// ---------- the pins, for the guide's pictures: 1.75 mm filament cut to length ----------
PIN_L = 88;     // the hole runs 88.8 from its floor to the top: the pin's end sits just under it
C_PIN_L = 28;
module pins(lift = 0) for (hx = [PANEL_W, 2 * PANEL_W])
    translate([hx, FLOOR + lift, AXIS_Z]) rotate([-90, 0, 0]) cylinder(d = 1.75, h = PIN_L, $fn = 24);
module pins_loose() for (k = [0 : 1]) translate([-8 - 5 * k, 0, 0.875]) rotate([-90, 0, 0]) cylinder(d = 1.75, h = PIN_L, $fn = 24);
module coupon_pins() for (k = [0 : 1])
    translate([0, k * (C_H + 6) + FLOOR, AXIS_Z]) rotate([-90, 0, 0]) cylinder(d = 1.75, h = C_PIN_L, $fn = 24);

if (part == "pins_loose") pins_loose();
else if (part == "pins_half") pins(46);
else if (part == "pins_in") pins();
else if (part == "coupon_pins") coupon_pins();
else if (part == "blue") for (p = [0 : 2]) panel_blue(p, bore);
else if (part == "white") for (p = [0 : 2]) panel_white(p, bore);
else if (part == "coupon") coupon();
else if (part == "coupon_l") coupon_leaf("l", bore);
else if (part == "coupon_r") coupon_leaf("r", bore);
else if (part == "posed_blue") posed("blue");
else if (part == "posed_white") posed("white");
else for (p = [0 : 2]) panel_shape(p, bore);
