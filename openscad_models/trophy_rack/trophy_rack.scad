// "Trophy Rack" medallion (2026-11-14): Scott's photos of a Mardi Gras bead pendant, to
// be reproduced as close to it as printing allows. A badge-shaped shield with a black rim
// and a hanging tab, a yellow field, two domes with red tips, and a white banner across
// the bottom reading TROPHY RACK, its letters laid along the banner's curve
// (banner_data.scad, from make_banner.py).
//
// Prints flat on its back, everything facing up, no supports. Five colours, one part
// each, none overlapping:
//   part = "black" (rim, back, tab, lettering) | "yellow" | "skin" | "red" | "white" | "all"

include <banner_data.scad>

part = "all";
$fn = 96;

RIM_W   = 2.4;      // the black rim's width
RIM_TOP = 5.0;      // the rim's top
BACK    = 1.6;      // black under the field
FIELD   = 3.6;      // the yellow field's top
BANNER_TOP = 8.0;   // the white banner's top: above the domes where it crosses them
LETTER_H = 0.8;     // lettering raised above the banner
TAB_T   = 3.0;      // the hanging tab's thickness
TAB_R   = 5.0;
HOLE_R  = 2.0;      // for a jump ring

DOME_R  = 12.2;     // each dome's base radius
DOME_H  = 10.6;     // its height above the field
DOME_X  = 11.7;     // centres at +/- this
DOME_Y  = 1.0;
TIP_R   = 1.6;      // the red tips
TIP_OUT = 3.6;      // how far a tip stands off the dome

// the shield: a badge with raised top corners, a notch in each side, a pointed bottom
function qbez(a, b, c, n) = [for (i = [0 : n]) let (t = i / n) (1 - t) * (1 - t) * a + 2 * (1 - t) * t * b + t * t * c];
RIGHT = concat(
    [[0, 27.0], [8, 26.5], [18, 26.6], [26, 27.4], [31.5, 28.6], [31.2, 17.0], [29.4, 15.4], [30.0, 13.0]],
    qbez([30.0, 13.0], [30.4, -21.0], [0, -32.0], 24));
SHIELD = concat(RIGHT, [for (i = [len(RIGHT) - 2 : -1 : 1]) [-RIGHT[i][0], RIGHT[i][1]]]);
module shield2d() polygon(SHIELD);
module inner2d() offset(r = -RIM_W) shield2d();
module banner2d() polygon(BANNER);

module tab() difference() {
    translate([0, 29.5, 0]) cylinder(r = TAB_R, h = TAB_T);
    translate([0, 31.0, -1]) cylinder(r = HOLE_R, h = TAB_T + 2);
}
module banner_prism() translate([0, 0, -1]) linear_extrude(BANNER_TOP + 30) banner2d();

module domes() for (s = [-1, 1]) translate([s * DOME_X, DOME_Y, FIELD])
    intersection() {
        scale([1, 1, DOME_H / DOME_R]) sphere(r = DOME_R);
        translate([-DOME_R, -DOME_R, 0]) cube([2 * DOME_R, 2 * DOME_R, DOME_R]);
    }
// each tip a short rounded peg standing straight up from just below the dome's top
// set a little low and toward the middle, as on the photo
TIP_DX = 1.2; TIP_DY = 1.8;
TIP_Z0 = FIELD + DOME_H * sqrt(1 - (TIP_DX * TIP_DX + TIP_DY * TIP_DY) / (DOME_R * DOME_R));
module tips() for (s = [-1, 1]) translate([s * (DOME_X - TIP_DX), DOME_Y - TIP_DY, TIP_Z0 - 1.0]) {
    cylinder(r = TIP_R, h = 1.0 + TIP_OUT - TIP_R, $fn = 48);
    translate([0, 0, 1.0 + TIP_OUT - TIP_R]) sphere(r = TIP_R, $fn = 48);
}

module letters2d() for (L = LETTERS) translate([L[1], L[2]]) rotate(L[3]) scale([XSCALE, 1])
    text(L[0], size = SIZE, font = FONT, halign = "center", valign = "baseline");

module black() {
    difference() {
        union() {
            linear_extrude(RIM_TOP) shield2d();
            tab();
        }
        translate([0, 0, BACK]) linear_extrude(RIM_TOP) inner2d();
        translate([0, 31.0, -1]) cylinder(r = HOLE_R, h = TAB_T + 2);
        banner_prism();
    }
    translate([0, 0, BANNER_TOP - 0.01]) linear_extrude(LETTER_H + 0.01) intersection() { letters2d(); banner2d(); }
}
module yellow() difference() {
    translate([0, 0, BACK]) linear_extrude(FIELD - BACK) inner2d();
    banner_prism();
}
module skin() difference() { domes(); banner_prism(); }
module red() difference() { tips(); domes(); }
module white() linear_extrude(BANNER_TOP) banner2d();

if (part == "black") black();
else if (part == "yellow") yellow();
else if (part == "skin") skin();
else if (part == "red") red();
else if (part == "white") white();
else {
    color("#1A1A1A") black();
    color("#E8C21A") yellow();
    color("#E7A976") skin();
    color("#C8314B") red();
    color("#F2EDE2") white();
}
