// Victorian pillar box (2026-10-13), a village accessory. Scott circled it
// from the second batch of studies (../concepts/accessories2_scene.jpg).
//
// The Penfold, the hexagonal box of the 1860s and 70s: a six-sided shaft on
// a plinth, a band under a flared cornice, a domed six-sided cap and a bud on
// top. The door stands out of the front with the letter slot cut through
// it; a wreath with a white bow hangs on the door; snow lies on the cap. On
// a small soft blob of snow, the maker's mark under it.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
SH = 1.2;

zb = 3.2;                   // the snow's top
A  = 5.4;                   // the shaft, across its flats from the centre
z1 = 6.0;                   // the shaft's foot
z2 = 20.2;                  // the band
z3 = 22.0;                  // the cornice's foot
AC = 7.4;                   // the cornice, out to
z4 = z3 + SH * (AC - (A + 0.4));   // ... reached here, climbing SH per 1 out
z5 = z4 + 1.0;              // the cap's foot
AT = 2.6;                   // the cap's crown
z6 = z5 + 3.6;

function cr(a) = a / cos(30);
module hex(a, h) cylinder(r = cr(a), h = h, $fn = 6);
module hexf(a0, a1, h) cylinder(r1 = cr(a0), r2 = cr(a1), h = h, $fn = 6);
// the front face: x along it, y up from the snow, z out of it
module front(a = A) translate([0, -a, 0]) rotate([90, 0, 0]) children();

module box() difference() {
    union() {
        translate([0, 0, 2.6]) hex(A + 1.0, z1 - 0.6 - 2.6);
        translate([0, 0, z1 - 0.6]) hexf(A + 1.0, A, 0.6);                  // plinth, bevelled
        hex(A, z3);                                                          // the shaft
        translate([0, 0, z2 - SH * 0.4]) hexf(A, A + 0.4, SH * 0.4);
        translate([0, 0, z2]) hex(A + 0.4, z3 - z2);                         // the band
        translate([0, 0, z3]) hexf(A + 0.4, AC, z4 - z3);                    // the cornice
        translate([0, 0, z4]) hex(AC, z5 - z4);
        translate([0, 0, z5]) hexf(AC, AT, z6 - z5);                         // the cap
        bud();
        door();
    }
    slot();
}
// a bud: a short stem, a swelling climbing 38 deg, a point
module bud() translate([0, 0, z6 - 0.01]) rotate_extrude($fn = 32)
    polygon([[0, 0], [1.3, 0], [1.3, 0.8], [2.1, 1.8], [2.1, 2.4], [0, 4.8]]);

// The door: a panel standing 0.6 out of the front, 0.6 clear of its corners,
// the slot cut through it. First drawn as an outline cut into the face, 6.2
// wide on a face 6.24 wide: it ran into the corners, slivers 0.15 thick, and
// the wreath bridged its groove (2026-10-13).
DW = 5.0;  DB = z1 + 1.4;  DT = z2 - 1.6;  DP = 0.6;
module door2d() offset(r = 0.6) offset(delta = -0.6) translate([-DW / 2, DB]) square([DW, DT - DB]);
module slot2d() translate([-1.7, DT - 3.0]) square([3.4, 1.3]);
module door() front() art_out(DP, 1) door2d();
module slot() front(A + DP) engrave_in(1.2) slot2d();

// the wreath, on the door below the slot, and its bow
WZ = DT - 6.4;
module wreath2d() translate([0, WZ]) difference() { circle(2.1, $fn = 40); circle(0.7, $fn = 32); }
module bow2d() translate([0, WZ - 1.9]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.45, 0.5]) circle(0.8, $fn = 20); }
    circle(0.8, $fn = 20);
}

// snow on the cap, its foot running out to nothing on the slope
module snow() difference() {
    intersection() {
        translate([0, 0, z5 + 0.9]) hexf(AC - 0.9 * (AC - AT) / (z6 - z5), AT + 0.9, z6 - z5 - 0.9 + 0.8);
        translate([0, 0, z5 + 0.9]) cylinder(r = 20, h = 10);
    }
    translate([0, 0, z5]) hexf(AC, AT, z6 - z5);
}

module base2d() circle(r = 10.5, $fn = 64);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([-5.5, -4.5, zb], [3.5, 2.6, 1.6]); drift([5.0, 5.5, zb], [3.0, 2.4, 1.3]); } base2d_in(); }
    }
    brand_mark([0, 0], 4.0);
}

module raw(p) {
    if (p == "body") box();
    // the reliefs start 0.01 inside the face, so the union welds them on
    if (p == "trim") { base(); snow(); front(A + DP) art_out(1.2, 1) bow2d(); }
    if (p == "accent") front(A + DP) art_out(1.0, 1) wreath2d();
}
emit();
