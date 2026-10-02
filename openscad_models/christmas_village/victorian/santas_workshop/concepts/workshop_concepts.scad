// Victorian Santa's workshop -- LOOK STUDY for two forms (2026-10-02).
// Not a printable model: no hollow room, parts overlap, never gated.
// concept = 1  long one-storey brick workshop, three tall arched toy windows
// concept = 2  two-storey gable-window workshop with a hoist
// piece selects a filament colour: body (brick), roof (slate), trim (white),
// accent (evergreen), toys (slate outlines on the panes).
include <toys.scad>

concept = 1;
piece = "body";
$fn = 48;

base_h = 8;
recess = 4.0;          // pane depth behind the brick face

module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
module rr(w, d, r) offset(r = r) square([w - 2 * r, d - 2 * r], center = true);

module snow_base(w, d) {
    hull() for (k = [0 : 4]) let (a = 90 * k / 4)
        translate([0, 0, base_h - 3 + 3 * sin(a)]) linear_extrude(0.01) rr(w - 2 * 3 * (1 - cos(a)), d - 2 * 3 * (1 - cos(a)), 8);
    linear_extrude(base_h - 3) rr(w, d, 8);
}

// brick courses: shallow grooves round a block
module courses(w, d, z0, z1) for (z = [z0 + 2.4 : 2.4 : z1 - 1])
    translate([0, 0, z]) linear_extrude(0.45) difference() { square([w + 4, d + 4], center = true); square([w - 0.6, d - 0.6], center = true); }

module arch2d(a, h) union() { translate([-a, 0]) square([2 * a, h]); translate([0, h]) circle(r = a); }

// A deep-set toy window on the plane y = yf (wall face), facing -y.
// a half-width, h height of the straight part, z0 its sill.
// rows: list of [z_off, [[toy, x_off, scale], ...]]
module toy_window(piece, x, z0, a, h, yf, rows, fanbars = 5) translate([x, 0, z0]) {
    if (piece == "cut") xz(yf - 1, yf + recess) arch2d(a, h);
    if (piece == "pane") xz(yf + recess - 0.01, yf + recess + 1) offset(r = 0.5) arch2d(a, h);
    if (piece == "frame") {
        xz(yf - 1.2, yf + 0.2) difference() { offset(r = 1.8) arch2d(a, h); arch2d(a, h); }
        xz(yf - 1.6, yf + 0.2) translate([0, h + a + 0.4]) polygon([[-1.4, 0], [1.4, 0], [2.0, 3.2], [-2.0, 3.2]]);   // keystone
        xz(yf - 2.2, yf + 0.2) translate([-a - 2.6, -2.2]) square([2 * a + 5.2, 2.2]);   // sill
        // transom and fan bars, raised on the pane
        xz(yf + recess - 0.6, yf + recess + 0.2) {
            translate([-a, h - 0.4]) square([2 * a, 0.9]);
            translate([0, h]) intersection() {
                circle(r = a);
                union() {
                    for (i = [1 : fanbars - 1]) rotate(180 * i / fanbars) translate([0, -0.4]) square([a, 0.8]);
                    difference() { circle(r = a * 0.42); circle(r = a * 0.42 - 0.8); }
                }
            }
        }
    }
    if (piece == "toys") xz(yf + recess - 0.4, yf + recess + 0.2)
        for (r = rows) for (t = r[1]) translate([t[1], r[0]]) scale(t[2]) toy(t[0]);
    if (piece == "shelf") xz(yf + recess - 0.4, yf + recess + 0.2)
        for (r = rows) if (r[0] > 1) translate([-a, r[0] - 0.8]) square([2 * a, 0.8]);
}

module quoins(w, d, z0, z1, q = 4.6, s = 2.6) for (sx = [-1, 1], sy = [-1, 1], k = [0 : floor((z1 - z0) / 5) - 1])
    translate([sx * w / 2, sy * d / 2, z0 + 1 + k * 5]) let (L = k % 2 ? q : s)
        cube([2 * (k % 2 ? s : q), 2 * (k % 2 ? q : s), 4], center = false, $fn = 0) ;

module quoin_set(w, d, z0, z1) for (k = [0 : floor((z1 - z0) / 5) - 1]) let (z = z0 + 0.8 + k * 5, lx = k % 2 ? 6 : 3.4, ly = k % 2 ? 3.4 : 6)
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (w / 2 - lx / 2 + 0.6), sy * (d / 2 - ly / 2 + 0.6), z + 2]) cube([lx, ly, 4], center = true);

module wreath2d() difference() { circle(r = 2.8); circle(r = 1.4); }
module bow2d() { polygon([[0, 0], [-2, 1], [-2, -1]]); polygon([[0, 0], [2, 1], [2, -1]]); polygon([[0, 0], [-1, -2.4], [-0.3, -2.6]]); polygon([[0, 0], [1, -2.4], [0.3, -2.6]]); }

// ---------------------------------------------------------------- concept 1
W1 = 92; D1 = 54; E1 = 64; P1 = 50; ov1 = 3.5;
R1 = E1 + (D1 / 2 + ov1) * tan(P1) - ov1 * tan(P1);   // ridge height under slates
yf1 = -D1 / 2;
WIN1 = [   // x, rows
    [-27, [[0.8, [["teddy", -4.2, 1], ["ball", 5.0, 1]]], [13.6, [["boat", -4.0, 1], ["drum", 4.6, 1]]]]],
    [0,   [[0.8, [["horse", 0, 1.05]]], [13.6, [["soldier", -4.6, 1], ["soldier", 0, 1], ["soldier", 4.6, 1]]]]],
    [27,  [[0.8, [["train", 0, 1]]], [13.6, [["jack", -4.0, 1], ["teddy", 4.6, 0.95]]]]],
];
wa1 = 10; wh1 = 25; wz1 = base_h + 7;

module c1_gable2d() polygon([[-D1 / 2, E1 - 0.5], [0, E1 + D1 / 2 * tan(P1)], [D1 / 2, E1 - 0.5]]);
module c1_roof2d(t0, t1) let (a = P1, y0 = -D1 / 2 - ov1, z0 = E1 - ov1 * tan(a))
    intersection() {
        polygon(concat(
            [[y0 - t0 * sin(a), z0 + t0 * cos(a)]],
            [for (k = [0 : 18]) for (j = [0, 1]) let (s = k * 4.6 + j * 4.5, t = t1 - (t1 - t0) * j * 0.75)
                [y0 + s * cos(a) - t * sin(a), z0 + s * sin(a) + t * cos(a)]],
            [[y0 + 90 * cos(a), z0 + 90 * sin(a)], [y0, z0]]));
        translate([-80, 0]) square([80, 200]);
    }
module c1_roof3d(t0, t1) for (m = [0, 1]) mirror([0, m, 0]) yz(-W1 / 2 - ov1, W1 / 2 + ov1) c1_roof2d(t0, t1);

module c1_skylight(piece) for (x = [-27, 0, 27]) translate([x, -D1 / 2 - ov1, E1 - ov1 * tan(P1)]) rotate([P1, 0, 0]) translate([0, 24, 2.6]) {
    if (piece == "roof") difference() { translate([-6, -5, 0]) cube([12, 10, 1.8]); translate([-4.6, -3.6, 0.6]) cube([9.2, 7.2, 2]); }
    if (piece == "trim") { translate([-4.6, -3.6, 0.4]) cube([9.2, 7.2, 0.8]); translate([-5.6, 4.6, 0]) cube([11.2, 2.4, 2.2]); }   // glass + snow on the frame
}

module c1_chimney(piece) translate([W1 / 2 - 14, 8, 0]) {
    if (piece == "body") difference() { translate([-5, -5, E1]) cube([10, 10, R1 - E1 + 14]); for (z = [E1 + 4 : 2.4 : R1 + 12]) translate([-6, -6, z]) cube([12, 0.5, 0.45]); }
    if (piece == "trim") translate([-6, -6, R1 + 13]) cube([12, 12, 1.6]);
    if (piece == "roof") for (s = [-2.2, 2.2]) translate([s, 0, R1 + 14.6]) difference() { cylinder(r = 1.6, h = 4); cylinder(r = 0.8, h = 5); }
}
module c1_stovepipe(piece) translate([-W1 / 2 + 22, 12, 0]) if (piece == "roof") {
    cylinder(r = 2.2, h = R1 + 6);
    translate([0, 0, R1 + 6]) cylinder(r1 = 2.2, r2 = 4.2, h = 1.4);
    translate([0, 0, R1 + 7.4]) cylinder(r1 = 4.2, r2 = 0.6, h = 3);
}

module c1_door(piece) let (xf = -W1 / 2, a = 6.5, h = 16) translate([xf, 0, base_h]) rotate([0, 0, 90]) {
    if (piece == "cut") xz(-2, 2.0) arch2d(a, h);
    if (piece == "roof") xz(-0.2, 2.2) difference() { arch2d(a, h); for (u = [-3.2, 3.2]) translate([u - 2.2, 3]) square([4.4, 9]); }
    if (piece == "trim") { xz(-1.2, 0.2) difference() { offset(r = 1.8) arch2d(a, h); arch2d(a, h); } xz(-1.6, 0) translate([0, h + 5.2]) bow2d(); }
    if (piece == "accent") xz(-1.4, 0.4) translate([0, h - 1]) wreath2d();
}

module c1_sign(piece) translate([0, yf1, E1 - 10.6]) {
    if (piece == "roof") xz(-1.4, 0.2) offset(r = 0.8) square([66, 5.6], center = true);
    if (piece == "trim") xz(-2.0, -1) text("SANTA'S WORKSHOP", size = 3.9, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.04);
}

module c1(piece) {
    if (piece == "trim") { snow_base(W1 + 18, D1 + 20); quoin_set(W1, D1, base_h, E1); }
    if (piece == "body") difference() {
        union() { translate([-W1 / 2, -D1 / 2, base_h - 1]) cube([W1, D1, E1 - base_h + 1]); yz(-W1 / 2, W1 / 2) c1_gable2d(); }
        courses(W1, D1, base_h, E1 - 0.5);
        for (w = WIN1) toy_window("cut", w[0], wz1, wa1, wh1, yf1, w[1]);
        c1_door("cut");
    }
    if (piece == "roof") difference() { c1_roof3d(0, 2.6); translate([-W1, -40, R1 - 6]) cube([2 * W1, 80, 40]); }
    if (piece == "trim") intersection() { c1_roof3d(2.2, 4.4); translate([-W1, -40, R1 - 6.2]) cube([2 * W1, 80, 40]); }
    if (piece == "trim") for (x = [-W1 / 2 - ov1 + 4 : 9 : W1 / 2]) translate([x, yf1 - ov1 + 0.6, E1 - ov1 * tan(P1) - 0.6]) rotate([90, 0, 0]) linear_extrude(1) polygon([[-1.2, 0], [1.2, 0], [0, -3.6 - 2 * sin(x * 37)]]);
    for (w = WIN1) {
        if (piece == "trim") { toy_window("pane", w[0], wz1, wa1, wh1, yf1, w[1]); toy_window("frame", w[0], wz1, wa1, wh1, yf1, w[1]); }
        if (piece == "toys") { toy_window("toys", w[0], wz1, wa1, wh1, yf1, w[1]); toy_window("shelf", w[0], wz1, wa1, wh1, yf1, w[1]); }
    }
    c1_skylight(piece); c1_chimney(piece); c1_stovepipe(piece); c1_door(piece); c1_sign(piece);
    if (piece == "accent") for (x = [-W1 / 2 + 4, W1 / 2 - 4]) translate([x, yf1 - 2.4, base_h]) scale([1, 0.7, 1]) cylinder(r1 = 3.4, r2 = 0.3, h = 11, $fn = 8);   // small firs
}

// ---------------------------------------------------------------- concept 2
W2 = 62; D2 = 56; E2 = 66; P2 = 55; ov2 = 3.5;
Rg = E2 + W2 / 2 * tan(P2);
yf2 = -D2 / 2;
wa2 = 17; wh2 = 26; wz2 = 44;
ROWS2 = [[0.8, [["horse", -9.0, 1.05], ["teddy", 2.0, 1], ["drum", 10.0, 0.95]]],
         [13.4, [["soldier", -12.5, 1], ["boat", -5.0, 1], ["train", 6.0, 0.95], ["ball", 14.0, 0.9]]]];
SIDEW = [[-21.5, [[0.8, [["jack", 0, 1]]]]], [21.5, [[0.8, [["soldier", 0, 1]]]]]];

module c2_gable2d() polygon([[-W2 / 2, E2 - 0.5], [0, Rg], [W2 / 2, E2 - 0.5]]);
module c2_roof2d(t0, t1) let (a = P2, x0 = -W2 / 2 - ov2, z0 = E2 - ov2 * tan(a))
    intersection() {
        polygon(concat(
            [[x0 - t0 * sin(a), z0 + t0 * cos(a)]],
            [for (k = [0 : 16]) for (j = [0, 1]) let (s = k * 4.6 + j * 4.5, t = t1 - (t1 - t0) * j * 0.75)
                [x0 + s * cos(a) - t * sin(a), z0 + s * sin(a) + t * cos(a)]],
            [[x0 + 80 * cos(a), z0 + 80 * sin(a)], [x0, z0]]));
        translate([-80, 0]) square([80, 200]);
    }
module c2_roof3d(t0, t1) for (m = [0, 1]) mirror([m, 0, 0]) xz(-D2 / 2 - ov2, D2 / 2 + ov2) c2_roof2d(t0, t1);

module c2_doors(piece) let (a = 12, h = 20) translate([0, yf2, base_h]) {
    if (piece == "cut") xz(-1, 2) arch2d(a, h - 4);
    if (piece == "roof") xz(1.4, 2.2) difference() {
        arch2d(a, h - 4);
        translate([-0.3, -1]) square([0.6, 40]);
        for (s = [-1, 1], x = [3 : 3 : a - 1]) translate([s * x - 0.2, -1]) square([0.4, 40]);
    }
    if (piece == "trim") {
        xz(-1.2, 0.2) difference() { offset(r = 1.8) arch2d(a, h - 4); arch2d(a, h - 4); }
        for (s = [-1, 1], z = [4, 14]) xz(1.0, 1.6) translate([s * 7.5, z]) square([9, 1.2], center = true);   // strap hinges
    }
    if (piece == "accent") for (s = [-1, 1]) xz(0.8, 1.6) translate([s * 4.5, h + 1]) wreath2d();
}

module c2_sign(piece) translate([0, yf2, wz2 - 6.4]) {
    if (piece == "roof") xz(-1.4, 0.2) offset(r = 0.8) square([50, 5.4], center = true);
    if (piece == "trim") xz(-2.0, -1) text("SANTA'S WORKSHOP", size = 3.1, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.02);
}

module c2_hoist(piece) let (zb = Rg - 13, L = 15) {
    if (piece == "roof") {
        translate([-1.6, yf2 - L, zb]) cube([3.2, L + 2, 3.2]);
        translate([0, yf2 - L + 2.2, zb - 1.6]) rotate([0, 90, 0]) cylinder(r = 1.6, h = 2, center = true);
    }
    if (piece == "trim") translate([0, yf2 - L + 2.2, zb - 9]) cylinder(r = 0.5, h = 8);
    if (piece == "body") translate([0, yf2 - L + 2.2, zb - 12.5]) {   // the sack
        hull() { translate([0, 0, -1.2]) scale([1, 0.75, 0.8]) sphere(r = 3.6); translate([0, 0, 3.0]) sphere(r = 1.2); }
        translate([0, 0, 3.4]) cylinder(r1 = 0.9, r2 = 2.0, h = 1.8);
    }
}

module c2_chimney(piece) translate([W2 / 2 + 2.5, 10, 0]) {
    if (piece == "body") { translate([-4, -6, base_h]) cube([7, 12, Rg - base_h - 6]); translate([-4.5, -5.5, Rg - 14]) cube([8, 11, 8]); }
    if (piece == "trim") translate([-5, -6.5, Rg - 6]) cube([9, 13, 1.6]);
    if (piece == "roof") for (s = [-2.5, 2.5]) translate([-0.5, s, Rg - 4.4]) difference() { cylinder(r = 1.6, h = 4); cylinder(r = 0.8, h = 5); }
}

module c2_barge(piece) if (piece == "trim") for (yy = [yf2 - ov2 - 0.2, -yf2 + ov2 - 1.2]) translate([0, yy, 0])
    for (m = [0, 1]) mirror([m, 0, 0]) xz(0, 1.4) let (a = P2, x0 = -W2 / 2 - ov2, z0 = E2 - ov2 * tan(a)) intersection() {
        union() {
            polygon([[x0, z0], [x0 + 80 * cos(a), z0 + 80 * sin(a)], [x0 + 80 * cos(a) + 2.6 * sin(a), z0 + 80 * sin(a) - 2.6 * cos(a)], [x0 + 2.6 * sin(a), z0 - 2.6 * cos(a)]]);
            for (s = [3 : 4 : 42]) translate([x0 + s * cos(a) + 2.4 * sin(a), z0 + s * sin(a) - 2.4 * cos(a)]) circle(r = 1.4, $fn = 16);
        }
        translate([-80, 0]) square([80.001, 200]);
    }

module c2(piece) {
    if (piece == "trim") { snow_base(W2 + 20, D2 + 22); quoin_set(W2, D2, base_h, E2); }
    if (piece == "body") difference() {
        union() { translate([-W2 / 2, -D2 / 2, base_h - 1]) cube([W2, D2, E2 - base_h + 1]); xz(-D2 / 2, D2 / 2) c2_gable2d(); }
        courses(W2, D2, base_h, E2 - 0.5);
        for (z = [E2 + 2 : 2.4 : Rg - 4]) translate([0, yf2, z]) cube([W2, 0.9, 0.45], center = true);
        toy_window("cut", 0, wz2, wa2, wh2, yf2, ROWS2);
        for (w = SIDEW) toy_window("cut", w[0], 16, 5, 10, yf2, w[1]);
        c2_doors("cut");
    }
    if (piece == "body") translate([0, yf2, E2 - 1]) xz(-1.0, 0.2) square([W2 + 1, 1.6], center = true);
    if (piece == "trim") translate([0, yf2, E2 - 3]) xz(-1.4, 0.2) square([W2 + 2, 1.8], center = true);   // string course
    if (piece == "roof") difference() { c2_roof3d(0, 2.6); translate([-40, -60, Rg - 5]) cube([80, 120, 40]); }
    if (piece == "trim") intersection() { c2_roof3d(2.2, 4.4); translate([-40, -60, Rg - 5.2]) cube([80, 120, 40]); }
    if (piece == "trim") { toy_window("pane", 0, wz2, wa2, wh2, yf2, ROWS2, 7); toy_window("frame", 0, wz2, wa2, wh2, yf2, ROWS2, 7); }
    if (piece == "toys") { toy_window("toys", 0, wz2, wa2, wh2, yf2, ROWS2); toy_window("shelf", 0, wz2, wa2, wh2, yf2, ROWS2); }
    for (w = SIDEW) {
        if (piece == "trim") { toy_window("pane", w[0], 16, 5, 10, yf2, w[1], 3); toy_window("frame", w[0], 16, 5, 10, yf2, w[1], 3); }
        if (piece == "toys") toy_window("toys", w[0], 16, 5, 10, yf2, w[1]);
    }
    c2_doors(piece); c2_sign(piece); c2_hoist(piece); c2_chimney(piece); c2_barge(piece);
    if (piece == "roof") translate([0, yf2 - ov2 - 0.6, Rg + 1.2]) cylinder(r1 = 1.4, r2 = 0.3, h = 6);   // finial
}

if (concept == 1) c1(piece); else c2(piece);
