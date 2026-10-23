// Victorian village accessories: form studies (2026-10-13), placed round the
// Victorian cottage (at the origin, front to -y) for scale. Blockouts for
// choosing what to make, not print geometry.
// part = body (brick) | roof (slate, iron) | trim (white, snow) | accent (evergreen)
// item = "all" or one of lamp | trees | bridge | railing | stall | pond
part = "body";
item = "all";
COLS = [["body", "#A8483A"], ["roof", "#2E3440"], ["trim", "#F4F1EA"], ["accent", "#2F6B45"]];
COT = "../../victorian/cottage/victorian_cottage_";
$fn = 40;

module at(p, a = 0) translate(p) rotate([0, 0, a]) children();
module show(name) if (item == "all" || item == name) children();

// ---- lamp post ---------------------------------------------------------------------
module lamp() {
    if ($p == "roof") {
        cylinder(r1 = 7, r2 = 6, h = 3, $fn = 8); translate([0, 0, 3]) cylinder(r1 = 4, r2 = 2.4, h = 8, $fn = 8);
        cylinder(r = 1.6, h = 62);
        for (i = [0 : 5]) rotate(30 * i) translate([1.2, 0, 11]) cylinder(r = 0.6, h = 48, $fn = 8);   // flutes
        translate([0, 0, 50]) cylinder(r = 2.6, h = 2);
        for (s = [-1, 1]) translate([s * 6, 0, 54]) rotate([0, s * 90, 0]) cylinder(r = 0.7, h = 6, center = true);   // ladder arm
        translate([0, 0, 61]) cylinder(r1 = 2.4, r2 = 5.6, h = 3, $fn = 6);
        for (i = [0 : 5]) rotate(60 * i) translate([5.6, 0, 64]) cylinder(r = 0.7, h = 11, $fn = 8);
        translate([0, 0, 75]) cylinder(r1 = 7.6, r2 = 1, h = 7, $fn = 6);
        translate([0, 0, 82]) sphere(1.4);
    }
    if ($p == "trim") {
        translate([0, 0, 64]) cylinder(r = 5.2, h = 11, $fn = 6);            // the glass
        translate([0, 0, 78]) cylinder(r1 = 5.6, r2 = 1.6, h = 4.4, $fn = 6); // snow on the cap
        cylinder(r = 9, h = 1.2);
    }
    if ($p == "accent") translate([0, -2, 40]) rotate([90, 0, 0]) rotate_extrude($fn = 24) translate([3.2, 0]) circle(1.2);
}

// ---- fir trees -----------------------------------------------------------------------
module fir(h) {
    tiers = [[0.18, 0.42], [0.42, 0.33], [0.64, 0.24]];
    if ($p == "roof") cylinder(r = h * 0.05, h = h * 0.2);
    if ($p == "accent") for (t = tiers) translate([0, 0, h * t[0]]) cylinder(r1 = h * t[1], r2 = 0.5, h = h * (1 - t[0]) * 0.75, $fn = 9);
    if ($p == "trim") {
        cylinder(r = h * 0.38, h = 1.2);
        for (t = tiers) translate([0, 0, h * t[0]]) intersection() {
            cylinder(r1 = h * t[1] + 0.6, r2 = 1.1, h = h * (1 - t[0]) * 0.75 + 0.8, $fn = 9);
            translate([0, 0, h * (1 - t[0]) * 0.75 * 0.45]) cylinder(r = h, h = h);
        }
        translate([0, 0, h * 0.95]) sphere(h * 0.035);
    }
}
module trees() { fir(78); at([16, -24]) fir(54); at([-14, -20]) fir(40); }

// ---- stone bridge over a frozen stream ------------------------------------------------
BL = 104; BW = 30; BH = 26;
module arch2d() translate([0, -40 + 14]) circle(r = 40, $fn = 120);
module bridge() {
    if ($p == "body") difference() {
        union() {
            translate([-BL / 2, -BW / 2, 0]) cube([BL, BW, BH]);
            for (s = [-1, 1]) translate([-BL / 2, s * (BW / 2 - 1.6) - 1.6, BH]) cube([BL, 3.2, 7]);   // parapets
        }
        rotate([90, 0, 0]) linear_extrude(BW + 2, center = true) arch2d();
        for (s = [-1, 1]) translate([s * (BL / 2 + 26), 0, BH + 26]) rotate([90, 0, 0]) cylinder(r = 48, h = BW + 10, center = true, $fn = 120);
        for (k = [0 : 8]) translate([-BL / 2, -BW / 2 - 1, 2 + k * 3.2]) cube([BL, 0.7, 0.6]);       // courses
    }
    if ($p == "trim") {
        difference() {
            for (s = [-1, 1]) translate([-BL / 2, s * (BW / 2 - 1.6) - 2, BH + 7]) cube([BL, 4, 1.6]);
            for (s = [-1, 1]) translate([s * (BL / 2 + 26), 0, BH + 26]) rotate([90, 0, 0]) cylinder(r = 48, h = BW + 10, center = true, $fn = 120);
        }
        translate([-BL / 2 - 10, -BW / 2 - 14, 0]) cube([BL + 20, BW + 28, 1.2]);
    }
    if ($p == "roof") translate([0, 0, 1.2]) linear_extrude(0.6) scale([1, 1]) square([34, BW + 26], center = true);   // the ice
}

// ---- iron railing with brick piers and a gate --------------------------------------------
module railing(len = 90) {
    if ($p == "body") for (x = [-len / 2, -9, 9, len / 2]) translate([x - 4, -4, 0]) cube([8, 8, 30]);
    if ($p == "trim") {
        for (x = [-len / 2, -9, 9, len / 2]) translate([x - 5, -5, 30]) cube([10, 10, 3]);
        for (x = [-len / 2, -9, 9, len / 2]) translate([x, 0, 33]) scale([1, 1, 0.6]) sphere(5);
        translate([-len / 2 - 6, -8, 0]) cube([len + 12, 16, 1.2]);
    }
    if ($p == "roof") {
        for (seg = [[-len / 2 + 4, -13], [13, len / 2 - 4]]) {
            for (z = [5, 22]) translate([seg[0], -0.6, z]) cube([seg[1] - seg[0], 1.2, 1.2]);
            for (x = [seg[0] + 2 : 4 : seg[1] - 1]) translate([x, 0, 2]) { cylinder(r = 0.6, h = 22, $fn = 8); translate([0, 0, 22]) cylinder(r1 = 1.2, r2 = 0, h = 3, $fn = 8); }
        }
        // the gate, standing half open
        translate([-5, 0, 0]) rotate([0, 0, -35]) translate([0, -0.6, 3]) {
            for (z = [2, 20]) translate([0, 0, z]) cube([13, 1.2, 1.2]);
            for (x = [1 : 3 : 12]) translate([x, 0.6, 0]) cylinder(r = 0.6, h = 21, $fn = 8);
        }
    }
    if ($p == "accent") for (x = [-9, 9]) translate([x, -4.6, 22]) rotate([90, 0, 0]) rotate_extrude($fn = 24) translate([3, 0]) circle(1.1);
}

// ---- market stall ------------------------------------------------------------------------
module stall() {
    W = 46; D = 26;
    if ($p == "body") {
        translate([-W / 2, -D / 2, 0]) cube([W, D * 0.55, 18]);                                        // counter
        for (x = [-W / 2, W / 2 - 3], y = [-D / 2, D / 2 - 3]) translate([x, y, 0]) cube([3, 3, 44]);   // posts
        translate([-W / 2 - 3, -D / 2 - 6, 44]) rotate([20, 0, 0]) cube([W + 6, D + 8, 2.4]);           // roof boards
    }
    if ($p == "roof") for (i = [0 : 5]) translate([-W / 2 - 2 + i * (W + 4) / 6, -D / 2 - 3, 36]) rotate([-30, 0, 0])
        if (i % 2 == 0) cube([(W + 4) / 6, 1.2, 9]);                                                        // awning stripes
    if ($p == "trim") {
        for (i = [0 : 5]) translate([-W / 2 - 2 + i * (W + 4) / 6, -D / 2 - 3, 36]) rotate([-30, 0, 0]) if (i % 2 == 1) cube([(W + 4) / 6, 1.2, 9]);
        translate([-W / 2 - 3, -D / 2 - 6, 46.6]) rotate([20, 0, 0]) cube([W + 6, D + 8, 1.6]);         // snow on the roof
        translate([-W / 2 - 6, -D / 2 - 10, 0]) cube([W + 12, D + 16, 1.2]);
    }
    if ($p == "accent") {
        for (x = [-14, 0, 14]) translate([x, -D / 2 + 3, 18]) cylinder(r1 = 4, r2 = 0.3, h = 11, $fn = 9);   // little trees for sale
        for (x = [-W / 2 + 1.5, W / 2 - 1.5]) translate([x, -D / 2 - 0.6, 30]) rotate([90, 0, 0]) rotate_extrude($fn = 24) translate([3, 0]) circle(1.1);
    }
}

// ---- skating pond with a bench ------------------------------------------------------------
module pond() {
    rim = [[-44, 0], [-36, 22], [-8, 30], [24, 26], [44, 8], [38, -18], [10, -28], [-22, -26]];
    if ($p == "trim") difference() {
        linear_extrude(3) offset(r = 6) polygon(rim);
        translate([0, 0, 1.6]) linear_extrude(3) polygon(rim);
    }
    if ($p == "roof") {
        translate([0, 0, 1.4]) linear_extrude(0.6) polygon(rim);                    // the ice
        translate([-20, 34, 3]) {                                                   // the bench
            for (x = [-9, 9]) translate([x, 0, 0]) cube([1.6, 6, 6], center = false);
            translate([-10, 0, 6]) cube([21, 6, 1.4]);
            translate([-10, 5, 7]) cube([21, 1.2, 6]);
        }
    }
    if ($p == "accent") translate([30, 30, 3]) fir_simple(34);
}
module fir_simple(h) for (t = [[0, 0.4], [0.3, 0.32], [0.55, 0.24]]) translate([0, 0, h * t[0]]) cylinder(r1 = h * t[1], r2 = 0.5, h = h * (1 - t[0]) * 0.8, $fn = 9);

module scene() {
    show("lamp")    at([-46, -46]) lamp();
    show("trees")   at([62, 18]) trees();
    show("railing") at([0, -62]) railing();
    show("stall")   at([-104, -10], 20) stall();
    show("bridge")  at([40, -118], -8) bridge();
    show("pond")    at([-70, -118]) pond();
}
if (part == "all") for (q = COLS) let ($p = q[0]) color(q[1]) { scene(); import(str(COT, q[0], ".stl")); }
else let ($p = part) scene();
