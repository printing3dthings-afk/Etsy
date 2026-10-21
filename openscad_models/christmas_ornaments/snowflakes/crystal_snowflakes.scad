// Crystal snowflake ornaments (2026-10-21), a set of six. Scott picked the
// faceted-crystal form (8E) from five: thick bevelled arms that catch the light
// like ice, sturdier than a lace snowflake, which snaps.
//
// Every arm and branch is a gabled bar: a flat foot 1.6 mm tall, then two faces
// rising 45 deg to a ridge down its middle. Where bars cross, their faces meet
// in valleys, and the flake reads as cut crystal. The hub is a six-sided gem.
// One colour; a hanging loop at the top tip; the maker's mark engraved in the
// gem's back.
//
// Printed flat, back on the plate, as it sits in the file: every face slopes
// up from a vertical edge, so nothing overhangs.
//
// design = 1..6     part = "flake" (the one design) | "all" (preview)
include <../../brand/obc_mark.scad>

design = 1;
part = "flake";

$fn = 48;
R   = 38;          // arm tip radius: 76 mm across, the loop above
HE  = 1.6;         // the edge: every bar's vertical foot
K   = 1.0;         // ridge rise per mm out from the edge: 45 deg faces (at 39, on
                   // arms 6 wide, the facets barely caught the light: it read as flat lace)
RH  = 11;          // the hub gem's radius (to its corners)
TIPW = 1.6;        // the narrowest a bar ends: under two beads a tip prints rounded off

// a gabled bar from a to b (2D points), its foot w0 wide at a and w1 at b
module bar(a, b, w0, w1) let (d = b - a, L = norm(d), ang = atan2(d[1], d[0]))
    translate([a[0], a[1], 0]) rotate([0, 0, ang]) hull() {
        translate([0, -w0 / 2, 0]) cube([0.01, w0, HE]);
        translate([0, -0.005, 0]) cube([0.01, 0.01, HE + K * w0 / 2]);
        translate([L - 0.01, -w1 / 2, 0]) cube([0.01, w1, HE]);
        translate([L - 0.01, -0.005, 0]) cube([0.01, 0.01, HE + K * w1 / 2]);
    }

// a small six-sided gem standing on the plate, its point to the ridge
// cut like a stone: a crown of six faces up to a flat table half its width
module gem(p, r, rot = 0) translate([p[0], p[1], 0]) rotate([0, 0, rot]) {
    cylinder(r = r, h = HE, $fn = 6);
    translate([0, 0, HE - 0.01]) cylinder(r1 = r, r2 = r * 0.5, h = K * r * 0.5 * 0.866 + 0.01, $fn = 6);
}

function pol(r, a) = [r * cos(a), r * sin(a)];

// one arm along angle a: its bar, its branches, its tip
//   br: [[distance from centre, branch length, branch angle off the arm, branch foot width], ...]
//   tip: 0 point, 1 gem, 2 fork
module arm(a, w0, w1, br, tip) {
    bar(pol(RH * 0.6, a), pol(R, a), w0, max(w1, TIPW));
    for (b = br, s = [-1, 1]) let (p = pol(b[0], a))
        bar(p, p + pol(b[1], a + s * b[2]), b[3], TIPW);
    if (tip == 1) gem(pol(R - 3.2, a), 4.2, a);
    if (tip == 2) for (s = [-1, 1]) let (p = pol(R - 6, a)) bar(p, p + pol(6.5, a + s * 35), 3.6, TIPW);
}

// the six designs: [arm foot, arm tip, branches, tip, inner ring radius (0 none)]
// Arms 8-12 wide at the hub (at 5.4-8, 2026-10-21, they read as lace, not crystal)
DESIGNS = [
    [9.0, 4.0, [[18, 10, 60, 5.0], [28, 7, 60, 4.0]], 0, 0],                   // 1 fern: two pairs of branches
    [10.0, 5.0, [[22, 8, 60, 5.0]], 1, 0],                                     // 2 star: one pair, gem tips
    [8.0, 3.6, [[28, 8, 50, 4.4]], 2, 0],                                      // 3 spear: forked tips
    [9.0, 4.0, [[29, 6.5, 60, 4.2]], 0, 19],                                   // 4 plate: a hexagon ring joins the arms
    [8.0, 3.6, [[16, 8, 60, 4.4], [23.5, 8.5, 60, 4.4], [30.5, 6, 60, 3.6]], 0, 0], // 5 dendrite: three pairs
    [12.0, 5.0, [[21, 9, 45, 6.0]], 1, 0],                                     // 6 bold: wide arms, swept branches
];

LOOP_RO = 4.6; LOOP_RI = 2.2; LOOP_H = 3.0;   // the loop: a 4.4 mm hole for a hook or ribbon
module loop() let (c = [0, R + LOOP_RO - 1.2]) translate([c[0], c[1], 0]) difference() {
    cylinder(r = LOOP_RO, h = LOOP_H);
    translate([0, 0, -1]) cylinder(r = LOOP_RI, h = LOOP_H + 2);
}

module flake(n) let (D = DESIGNS[n - 1]) difference() {
    union() {
        for (k = [0 : 5]) arm(90 + 60 * k, D[0], D[1], D[2], D[3]);
        if (D[4] > 0) for (k = [0 : 5]) bar(pol(D[4], 90 + 60 * k), pol(D[4], 150 + 60 * k), 4.4, 4.4);
        gem([0, 0], RH, 30);
        loop();
    }
    obc_engrave(4.0);      // on the back, mirrored to read from behind
}

if (part == "flake") flake(design);
if (part == "all") for (n = [1 : 6]) translate([((n - 1) % 3 - 1) * 84, (floor((n - 1) / 3) - 0.5) * 92, 0]) flake(n);
