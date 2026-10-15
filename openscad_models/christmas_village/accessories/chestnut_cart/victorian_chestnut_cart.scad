// Victorian hot chestnut cart (2026-10-14), a village accessory from the
// second batch of studies (../concepts/accessories2_scene.jpg).
//
// A chestnut seller's barrow parked in the snow: a red box on two slate
// wheels with white spokes, two handles resting on the snow behind, and on
// top an iron brazier with glowing vents, a pan of chestnuts and a tall
// chimney with a cap. A white rim trims the box, a wreath hangs on its front
// end, snow lies on its lid. On a soft blob of snow, the maker's mark under it.
//
// Printed upright with no support: the box's hopper stands on a drift of
// snow, the wheels are sunk in it until their curve leaves the snow at 42, the
// handles slope to the snow at 38, and every vent and rim steps out at SH.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
MARK = [[-4, 0], 5.0];         // the maker's mark: where on the base, its cap height
SH = 1.2;

zb = 3.2;                   // the snow's top
BX = 11;                    // the box: half-length
BY = 6.6;                   //          half-width
Z0 = 8.0;                   //          bottom
Z1 = 16.0;                  //          top
WR = 7.0;                   // a wheel's radius
WT = 1.6;                   //           thickness
WY = BY + 1.2;              //           inner face
WZ = zb + WR * 0.67;        //           centre: its curve leaves the snow 42 deg off upright

// the box, its corners rounded 2.5, and a white rim round its top, 2 tall,
// flaring out 0.6 at SH; below it a hopper, tapering in at SH to a drift of
// snow. Rounded, a corner climbs SH like the sides do; square, its diagonal
// stepped out 1.4 times as far and the slicer propped the hopper's and the
// rim's corners. At 0.8 tall the rim's lip was under one bead (2026-10-14).
RIM = 2.0;
HD = 3.0;                   // the hopper's depth
HI = HD / SH;               // and how far it steps in
module core2d() square([2 * (BX - HI), 2 * (BY - HI)], center = true);
module box2d() offset(r = HI, $fn = 32) core2d();
module slab(z, h = 0.01) translate([0, 0, z]) linear_extrude(h) children();
module box() {
    slab(Z0, Z1 - Z0 - RIM + 0.01) box2d();
    hull() { slab(Z0 - HD) core2d(); slab(Z0 - 0.01, 0.02) box2d(); }
}
module rim() hull() { slab(Z1 - RIM) box2d(); slab(Z1 - RIM + 0.6 * SH, RIM - 0.6 * SH) offset(r = 0.6, $fn = 32) box2d(); }

// wheels: slate discs, white spokes, rim and hub standing out of the outside
module side(s) mirror([0, s > 0 ? 1 : 0, 0]) translate([0, -WY, 0]) rotate([90, 0, 0]) children();
module wheels() for (s = [-1, 1]) side(s) translate([0, WZ, 0]) cylinder(r = WR, h = WT, $fn = 64);
module spokes2d() translate([0, WZ]) {
    difference() { circle(WR - 0.1, $fn = 64); circle(WR - 1.6, $fn = 64); }
    circle(1.8, $fn = 32);
    for (a = [0 : 45 : 135]) rotate(a) square([2 * WR - 1.4, 1.5], center = true);
}
// skirted, not trimmed: art_out left the level spoke 0.9 tall (2026-10-14)
module spokes() for (s = [-1, 1]) side(s) translate([0, 0, WT - 0.01]) art_skirt(0.8, 1) intersection() {
    spokes2d(); translate([-50, zb + 0.2]) square(100);      // nothing below the snow
}
// the axles run into the hopper, each on a web that climbs from the wheel's
// inner face at SH: alone it spanned 2 mm of air from wheel to hopper
AY = BY - (Z0 - (WZ - 0.8)) / SH;          // the hopper's face at the axle's underside
AZ = WZ - 0.8 - (WY - AY) * SH;            // the web's foot on the wheel
module axles() for (s = [-1, 1]) mirror([0, s > 0 ? 1 : 0, 0]) hull() {
    translate([0, -WY + 0.01, WZ]) rotate([90, 0, 0]) cylinder(r = 0.8, h = 0.01, $fn = 20);
    translate([0, -AY + 0.05, WZ]) rotate([90, 0, 0]) cylinder(r = 0.8, h = 0.01, $fn = 20);
    translate([-0.8, -WY + 0.01, AZ]) cube([1.6, 0.01, 0.01]);
}

// snow drifted under the hopper, carrying it; the wheels stand in the snow
// on their own, their arcs leaving it at 42 deg
module bank() hull() {
    translate([0, 0, zb - 0.3]) scale([BX + 0.5, BY + 0.6, 1]) cylinder(r = 1, h = 0.01, $fn = 48);
    slab(Z0 - HD - 0.01, 0.02) core2d();
}

// handles: two bars from the box's back, sloping 38 deg off upright to the snow
module handles() for (y = [-4.6, 4.6]) hull() {
    translate([-BX + 0.5, y, Z1 - 3.0]) sphere(0.8, $fn = 16);
    translate([-BX - 7.5, y, zb - 0.2]) cylinder(r = 0.8, h = 0.6, $fn = 16);
}

// the brazier: an iron drum with pointed vents glowing red, a pan of chestnuts
BR = 5.4;                   // the drum
BZ1 = Z1 + 5.6;             // its top
BXC = 2.0;                  // set forward of centre, the chimney behind it
module drum() translate([BXC, 0, Z1 - 0.01]) {
    cylinder(r = BR, h = BZ1 - Z1, $fn = 48);
    translate([0, 0, BZ1 - Z1 - 0.01]) cylinder(r1 = BR, r2 = BR + 0.7, h = 0.7 * SH, $fn = 48);     // the pan's rim
    translate([0, 0, BZ1 - Z1 + 0.7 * SH - 0.02]) difference() {
        cylinder(r = BR + 0.7, h = 1.2, $fn = 48); translate([0, 0, 0.4]) cylinder(r = BR - 0.6, h = 2, $fn = 48); }
}
module vents() translate([BXC, 0, Z1]) for (i = [0 : 7]) rotate([0, 0, 45 * i + 22.5]) translate([BR - 0.7, 0, 1.4])
    rotate([90, 0, 90]) linear_extrude(1.4) tear2d(0.8);
module embers() translate([BXC, 0, Z1]) cylinder(r = BR - 0.69, h = 4.2, $fn = 48);
module chestnuts() translate([BXC, 0, BZ1 + 0.7 * SH + 0.3]) for (i = [0 : 12]) let (a = 137.5 * i, r = 0.7 + 3.7 * sqrt(i / 12))
    translate([r * cos(a), r * sin(a), 0]) scale([1, 0.85, 0.75]) sphere(0.9, $fn = 16);
// the chimney: a pipe from the drum's back, a cap flaring at 40 deg
CH = 40;
module chimney() translate([BXC - BR + 0.6, 0, Z1 - 0.01]) {
    cylinder(r = 1.6, h = CH - Z1, $fn = 24);
    translate([0, 0, CH - Z1 - 0.01]) cylinder(r1 = 1.6, r2 = 2.5, h = 0.9 * SH, $fn = 24);
    translate([0, 0, CH - Z1 + 0.9 * SH - 0.02]) cylinder(r1 = 2.5, r2 = 0.8, h = 1.8, $fn = 24);
}

// the wreath on the box's front end, under the rim, its bow red
WRZ = Z0 + 3.3;             // its skirt clear of the hopper, its bow under the rim
module front_end(a) translate([a, 0, 0]) rotate([90, 0, 90]) children();
module wreath2d() translate([0, WRZ]) difference() { circle(1.9, $fn = 40); circle(0.6, $fn = 32); }
module bow2d() translate([0, WRZ + 1.8]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.4, 0.4]) circle(0.75, $fn = 20); }
    circle(0.75, $fn = 20);
}

module base2d() translate([-4, 0]) scale([1, 15 / 26]) circle(r = 26, $fn = 96);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        bank();
        clip_to() { union() { drift([12, 8, zb], [5, 3, 1.0]); drift([-22, -6, zb], [4, 3, 0.9]); } base2d_in(); }
        // snow on the box's lid, in front of the brazier
        translate([BX - 2.6, 0, Z1 - 0.3]) scale([2.2, 5.6, 1.0]) intersection() { sphere(1, $fn = 32); translate([-2, -2, 0]) cube(4); }
    }
    brand_mark(MARK[0], MARK[1]);
}

module raw(p) {
    if (p == "body") { box(); front_end(BX - 0.01) art_skirt(1.0, 1) bow2d(); embers(); chestnuts(); }
    if (p == "roof") difference() { union() { wheels(); axles(); handles(); drum(); chimney(); } vents(); }
    if (p == "trim") { base(); rim(); spokes(); }
    if (p == "accent") difference() { front_end(BX - 0.01) art_skirt(1.0, 1) wreath2d(); front_end(BX - 0.01) art_skirt(1.0, 1) bow2d(); }
}
emit();
