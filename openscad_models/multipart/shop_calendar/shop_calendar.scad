// Shop Calendar (2026-10-29): a perpetual desk calendar built as a little shop
// front. Its three shop windows show the DAY, the DATE and the MONTH, each
// on a drum that clicks round on a printed spring. Scott's pick, form 2 of the
// Perpetual Desk Calendar forms.
//
// Prints, each in the pose it prints in, no supports:
//   base     floor, side walls and the four springs, upright
//   facade   the shop front, face up, so its sign and frames are top relief
//   roof     flat
//   rod      the axle, standing on its head
//   drum_day, drum_tens, drum_ones, drum_month   each on its flange
//   (drum_*_text is the lettering, for a second colour; it is the same print)
//
// The back is open: the drums are rolled from behind.
//
// The spring is the test plate's detent turned upright: the same 1.0 mm arm,
// 5 mm wide, 16 mm from its root to the bump, a 1.2 mm bump that must move
// 0.6 mm to pass from one notch to the next. Its thickness is ARM_T: set it to
// whichever value of the test plate's three clicked best.

include <../../christmas_village/relief_lib.scad>   // art_skirt's step logic
SH = 1.2;

part = "assembly";
$fa = 2; $fs = 0.4;

// ---------- the detent, from the test plate ----------
ARM_T  = 1.0;          // spring thickness: 0.8 / 1.0 / 1.2 on the test plate
ARM_W  = 5;
ARM_L  = 16;           // root to bump
DDEP   = 1.0;          // notch depth
BUMP_R = 1.2;
PRELOAD = 0.6;         // how far the bump is pushed back between notches

// ---------- drums ----------
APO    = 19;           // axle to every drum's face: all four fronts in one plane
DR     = 23;           // flange radius, past every drum's corners
FT     = 3;            // flange thickness
ROD_D  = 8;
CLR    = 0.3;          // running clearance, radial
GAP    = 0.6;          // between drums, and drum to wall
TXT_H  = 0.8;          // lettering, proud of the face
FONT   = "Poppins:style=Bold";
// Poppins on the sign too: every serif face measured (Playfair, DejaVu Serif,
// Fraunces, Charter, Caladea) had a quarter of its strokes under the 1.2 mm
// wall floor at this size, and Playfair's serifs dropped out of the slice.
SIGN_FONT = "Poppins:style=Bold";

DAYS   = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"];
MONTHS = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"];
// name, labels, body length, flange side (-1 its left end, +1 its right), text size
DRUMS = [
    ["day",   DAYS,                                     24, -1, 6.4],
    ["tens",  ["0", "1", "2", "3", "0", "1", "2", "3"], 11, -1, 8.8],
    ["ones",  ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"], 11, 1, 8.8],
    ["month", MONTHS,                                   24,  1, 6.4],
];
function d_len(i) = DRUMS[i][2] + FT;
// the drums' left ends along the axle, from the left wall's inside face
function d_x0(i) = GAP + (i == 0 ? 0 : d_x0(i - 1) + d_len(i - 1));
IN_W   = d_x0(3) + d_len(3) + GAP;              // between the side walls
function d_body0(i) = d_x0(i) + (DRUMS[i][3] < 0 ? FT : 0);
function d_flange_x(i) = d_x0(i) + (DRUMS[i][3] < 0 ? FT / 2 : DRUMS[i][2] + FT / 2);

// ---------- the shop ----------
FLOOR  = 3;
WALL   = 4;
ZA     = FLOOR + DR + 1;                        // the axle
Y_FAC  = -(DR + 0.8);                           // the facade's back face, 0.8 off the flanges
FAC_T  = 3;
Y_SIDEWALK = Y_FAC - FAC_T - 4.5;
Y_ARM  = DR + PRELOAD;                          // the arms' front faces
Y_BACK = Y_ARM + ARM_T + 4;
Z_ROOF = ZA + DR + 1.5;                         // the walls' tops, the roof's underside
ROOF_T = 2.5;
FAC_TOP = Z_ROOF + ROOF_T + 10;
OUT_W  = IN_W + 2 * WALL;
PEG_Z  = [12, Z_ROOF - 10];

echo(str("inside ", IN_W, "  outside ", OUT_W, " x ", Y_BACK - Y_SIDEWALK, " x ", FAC_TOP, " mm  axle at z ", ZA));

// ---------- a drum, as printed: flange on the bed, axle up ----------
// The lettering stands 0.8 proud of an upright face, so every stroke's
// underside would hang in the air; art_skirt's skirt slopes it 50 deg (SH),
// the shop's support-free relief (relief_lib.scad).
module skirt_along(h, dirx) let (m = art_n(h, 1)) for (i = [0 : m - 1])
    let (t0 = i == 0 ? -0.01 : i * h / m - 0.01, t1 = (i + 1) * h / m, k = ceil(SH * (h - t1) / 0.2 - 0.05))
        translate([0, 0, t0]) linear_extrude(t1 - t0) offset(delta = 0.01) union()
            for (j = [0 : max(k, 0)]) translate([dirx * j * 0.2, 0]) children();

function step(i) = 360 / len(DRUMS[i][1]);
module drum_text(i) let (d = DRUMS[i], s = d[3], zc = FT + d[2] / 2)
    for (k = [0 : len(d[1]) - 1]) rotate([0, 0, k * step(i)])
        // 2D x reads along the axle, 2D y is the letters' up, 2D z is out of the
        // face; on the bed the axle is z, so "down" in print is 2D x times s
        multmatrix([[0, s, 0, 0], [0, 0, -1, -APO + 0.15], [-s, 0, 0, zc], [0, 0, 0, 1]])
            skirt_along(TXT_H + 0.15, s) text(d[1][k], size = d[4], font = FONT, halign = "center", valign = "center");

module drum_body(i) let (d = DRUMS[i], n = len(d[1])) difference() {
    union() {
        cylinder(r = DR, h = FT, $fn = 144);
        // face k's middle points at -y, then k steps round
        translate([0, 0, FT - 0.01]) rotate([0, 0, -90 - 180 / n]) cylinder(r = APO / cos(180 / n), h = d[2] + 0.01, $fn = n);
    }
    // the notches, opposite each face: face k at the front puts notch k at the
    // back, where the spring is
    for (k = [0 : n - 1]) rotate([0, 0, 90 + k * step(i)]) translate([0, 0, -1]) linear_extrude(FT + 2)
        polygon([[DR - DDEP, 0], [DR + 1, -2.4], [DR + 1, 2.4]]);
    translate([0, 0, -1]) cylinder(d = ROD_D + 2 * CLR, h = d[2] + FT + 2, $fn = 64);
    // the bore's mouth on the bed, so the first layer's squash can't close it
    translate([0, 0, -0.01]) cylinder(d1 = ROD_D + 2 * CLR + 1, d2 = ROD_D + 2 * CLR, h = 0.5, $fn = 64);
}
module drum(i) union() { drum_body(i); drum_text(i); }

// as assembled: axle along x, face 0 at the front
module drum_placed(i, turn = 0) let (d = DRUMS[i])
    translate([d[3] < 0 ? d_x0(i) : d_x0(i) + d_len(i), 0, ZA])
        rotate([0, d[3] < 0 ? 90 : -90, 0]) rotate([0, 0, -turn]) children();

// ---------- base: floor, side walls, springs ----------
// peaked at 52 deg, not 45: the slicer supports exactly 45 (the test plate
// found the same in Bambu Studio)
module teardrop_hole(d) hull() { circle(d = d, $fn = 48); translate([0, d / 2 / cos(52)]) square(0.01, center = true); }

module spring(xc) translate([xc - ARM_W / 2, 0, 0]) {
    translate([0, Y_ARM, FLOOR - 0.01]) cube([ARM_W, ARM_T + 4, ZA - ARM_L - FLOOR + 0.01]);   // root
    translate([0, Y_ARM, ZA - ARM_L - 0.01]) cube([ARM_W, ARM_T, ARM_L + 3 + 0.01]);          // arm
    // the bump: round on top, and its underside sloped SH so it prints
    translate([0, 0, 0]) rotate([90, 0, 90]) linear_extrude(ARM_W) union() {
        intersection() { translate([Y_ARM, ZA]) circle(r = BUMP_R, $fn = 48); translate([Y_ARM - BUMP_R, ZA]) square(BUMP_R + 0.01); }
        polygon([[Y_ARM + 0.01, ZA], [Y_ARM - BUMP_R, ZA], [Y_ARM + 0.01, ZA - BUMP_R * SH]]);
    }
}

module base() difference() {
    union() {
        translate([-WALL, Y_SIDEWALK, 0]) cube([OUT_W, Y_BACK - Y_SIDEWALK, FLOOR]);
        for (x = [-WALL, IN_W]) translate([x, Y_FAC, 0]) cube([WALL, Y_BACK - Y_FAC, Z_ROOF]);
        for (i = [0 : 3]) spring(d_flange_x(i));
        // the facade's pegs, out of the walls' front edges
        // Fins, 1.6 wide, their undersides climbing SH as they leave the wall.
        // Square to the wall, a peg's lowest edge started in the air; as a
        // diamond, its point began as slivers too thin to extrude. The slicer
        // propped both (2026-10-29).
        for (x = [-WALL / 2, IN_W + WALL / 2], z = PEG_Z) translate([x - 0.8, 0, 0]) rotate([90, 0, 90])
            linear_extrude(1.6) polygon([[Y_FAC + 0.01, z - 3], [Y_FAC + 0.01, z + 3], [Y_FAC - FAC_T + 0.9, z + 3],
                                         [Y_FAC - FAC_T + 0.9, z - 3 + (FAC_T - 0.9) * SH]]);
        // the roof's pegs, up out of the walls' tops
        for (x = [-WALL / 2, IN_W + WALL / 2], y = [Y_FAC + 8, Y_BACK - 6])
            translate([x, y, Z_ROOF - 0.01]) cylinder(d = 2.4, h = ROOF_T - 0.5, $fn = 24);
    }
    // the rod: through the left wall, its head in a counterbore; blind in the right
    translate([-WALL - 1, 0, ZA]) rotate([90, 0, 90]) linear_extrude(WALL + 2) teardrop_hole(ROD_D + 0.2);
    translate([-WALL - 0.01, 0, ZA]) rotate([90, 0, 90]) linear_extrude(1.6) teardrop_hole(ROD_D + 4.6);
    translate([IN_W - 0.01, 0, ZA]) rotate([90, 0, 90]) linear_extrude(WALL - 1) teardrop_hole(ROD_D + 0.2);
}

// ---------- rod ----------
// head to tip: through the left wall, across, and 2.5 into the right wall's
// 3 deep blind hole
ROD_L = WALL + IN_W + 2.5;
module rod() union() {
    cylinder(d = ROD_D + 4, h = 1.5, $fn = 64);
    cylinder(d = ROD_D, h = ROD_L - 0.6, $fn = 64);
    translate([0, 0, ROD_L - 0.6 - 0.01]) cylinder(d1 = ROD_D, d2 = ROD_D - 1.2, h = 0.61, $fn = 64);
}

// ---------- facade: drawn in its own plane, x across, y up from the floor ----------
// Printed face up; turned upright at y = Y_FAC when placed.
FAC_X0 = -WALL - 1;
FAC_W  = OUT_W + 2;
function win(i0, i1) = [d_body0(i0), d_body0(i1) + DRUMS[i1][2]];
WINDOWS = [[win(0, 0), 10], [win(1, 2), 12], [win(3, 3), 10]];   // x range, height
// The window openings splay out 45 deg through the facade, top and bottom,
// SPLAY taller at its front: square, a 10 mm window 10 mm deep hid the top half
// of each word from a desk's eye height (the first renders, 2026-10-29).
// Printed face up, a splay is an upward bevel and needs nothing under it. The
// sides stay square, so the 3.6 mm mullions between windows keep their width,
// and the first 1.4 mm is straight, so no window has a knife edge on the bed.
SPLAY  = FAC_T - 1.4;
FRAME  = 1.8;
WIN_TOP = ZA + 6 + SPLAY + FRAME;                // the date window's frame's top
AWN_Z  = [WIN_TOP + 1.2, WIN_TOP + 7.7];
SIGN_Z = [AWN_Z[1] + 1, FAC_TOP - 5];
module win2d(w, g = 0, gy) let (h = is_undef(gy) ? g : gy)
    translate([w[0][0] - g, ZA - w[1] / 2 - h]) square([w[0][1] - w[0][0] + 2 * g, w[1] + 2 * h]);

module facade_relief() {
    // pilasters
    for (x = [FAC_X0, FAC_X0 + FAC_W - 6]) translate([x, FLOOR]) square([6, FAC_TOP - FLOOR]);
    // window frames and sills
    for (w = WINDOWS) {
        difference() { win2d(w, FRAME, SPLAY + FRAME); win2d(w, 0, SPLAY); }
        translate([w[0][0] - FRAME - 1, ZA - w[1] / 2 - SPLAY - FRAME - 2]) square([w[0][1] - w[0][0] + 2 * (FRAME + 1), 2]);
    }
    // stall riser panels under the windows
    for (w = WINDOWS) let (top = ZA - w[1] / 2 - SPLAY - FRAME - 3) difference() {
        translate([w[0][0] - 1, FLOOR + 3]) square([w[0][1] - w[0][0] + 2, top - FLOOR - 3]);
        translate([w[0][0] + 0.6, FLOOR + 4.6]) square([w[0][1] - w[0][0] - 1.2, top - FLOOR - 6.2]);
    }
    // the sign's frame
    difference() {
        translate([FAC_X0 + 9, SIGN_Z[0]]) square([FAC_W - 18, SIGN_Z[1] - SIGN_Z[0]]);
        translate([FAC_X0 + 10.6, SIGN_Z[0] + 1.6]) square([FAC_W - 21.2, SIGN_Z[1] - SIGN_Z[0] - 3.2]);
    }
    // cornice
    translate([FAC_X0, FAC_TOP - 3]) square([FAC_W, 3]);
}
module awning() let (n = 13, w = (FAC_W - 12) / n, x0 = FAC_X0 + 6) {
    // stripes: every other one stands proud, and the hem is scalloped
    for (k = [0 : n - 1]) if (k % 2 == 0) translate([x0 + k * w, AWN_Z[0] + 1.6]) square([w, AWN_Z[1] - AWN_Z[0] - 1.6]);
    // each scallop 0.4 short of its neighbour: touching, CGAL dropped the awning
    for (k = [0 : n - 1]) translate([x0 + (k + 0.5) * w, AWN_Z[0] + 1.6]) circle(d = w - 0.4, $fn = 32);
    translate([x0, AWN_Z[1] - 1.6]) square([n * w, 1.6]);
}
module facade_holes() for (x = [-WALL / 2, IN_W + WALL / 2], z = PEG_Z) translate([x - 1.1, z - 3.2]) square([2.2, 6.4]);

module facade_flat() difference() {
    union() {
        translate([FAC_X0, FLOOR]) linear_extrude(FAC_T) square([FAC_W, FAC_TOP - FLOOR]);
        translate([0, 0, FAC_T - 0.01]) linear_extrude(1.2) facade_relief();
        translate([0, 0, FAC_T - 0.01]) linear_extrude(1.6) awning();
        translate([OUT_W / 2 - WALL, (SIGN_Z[0] + SIGN_Z[1]) / 2, FAC_T - 0.01]) linear_extrude(1.2)
            text("TODAY", size = 6.8, font = SIGN_FONT, halign = "center", valign = "center", spacing = 1.15);
    }
    for (w = WINDOWS) {
        translate([0, 0, -1]) linear_extrude(2.4) win2d(w);
        hull() {
            translate([0, 0, 1.4 - 0.01]) linear_extrude(0.01) win2d(w);
            translate([0, 0, FAC_T]) linear_extrude(0.01) win2d(w, 0, SPLAY);
        }
        translate([0, 0, FAC_T - 0.01]) linear_extrude(3) win2d(w, 0, SPLAY);
    }
    // the pegs' holes stop under the pilasters' relief, so they don't show
    translate([0, 0, -1]) linear_extrude(FAC_T + 1 - 0.4) facade_holes();
}
module facade_placed() translate([0, Y_FAC, 0]) rotate([90, 0, 0]) children();

// ---------- roof ----------
// 1.5 of eave each side: flush with the walls, the pegs' holes left 0.6 of roof
module roof() difference() {
    translate([-WALL - 1.5, Y_FAC, 0]) cube([OUT_W + 3, Y_BACK - Y_FAC, ROOF_T]);
    for (x = [-WALL / 2, IN_W + WALL / 2], y = [Y_FAC + 8, Y_BACK - 6])
        translate([x, y, -1]) cylinder(d = 2.8, h = ROOF_T + 2, $fn = 24);
}

module assembly(turn = [0, 0, 0, 0]) {
    color("#B85C47") base();
    color("#A9DCC8") facade_placed() facade_flat();
    color("#5A5F66") translate([0, 0, Z_ROOF]) roof();
    color("#F4F1EA") translate([-WALL, 0, ZA]) rotate([0, 90, 0]) rod();
    for (i = [0 : 3]) {
        color("#F4F1EA") drum_placed(i, turn[i] * step(i)) drum_body(i);
        color("#2B3A55") drum_placed(i, turn[i] * step(i)) drum_text(i);
    }
}
// drum_<name> is a drum without its lettering, drum_<name>_text the lettering,
// drum_<name>_print both (the one print)
DRUM_PARTS = [for (i = [0 : 3]) each [str("drum_", DRUMS[i][0]), str("drum_", DRUMS[i][0], "_text"), str("drum_", DRUMS[i][0], "_print")]];
if      (part == "base")   base();
else if (part == "facade") facade_flat();
else if (part == "roof")   roof();
else if (part == "rod")    rod();
else if (part == "dims")   echo(DIMS = [ZA, Y_FAC, Z_ROOF, IN_W, WALL, FAC_T,
                                       [for (i = [0 : 3]) [d_x0(i), d_len(i), DRUMS[i][3], len(DRUMS[i][1])]]]);
else if (len(search([part], DRUM_PARTS)) > 0 && search([part], DRUM_PARTS)[0] != []) let (k = search([part], DRUM_PARTS)[0], i = floor(k / 3)) {
    if (k % 3 == 0) drum_body(i); else if (k % 3 == 1) drum_text(i); else drum(i);
}
else assembly([3, 2, 9, 9]);      // THU 29 OCT, the day it was drawn
