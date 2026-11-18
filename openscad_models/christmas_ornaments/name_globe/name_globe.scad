// Snow Globe Name Ornament (2026-11-18). Scott picked form 5 of five after the
// domed name ornament's inlaid name printed lumpy on its curve ("Jessee",
// 2026-11-18): a flat snow globe on its base, a snowy village scene on the glass,
// and the name and year raised on the base.
//
// Printed flat, back on the plate, nothing overhangs. Three colours, by height:
//   frame  the globe's rim, the loop and the base (0-2.4 mm)
//   glass  the disc inside the rim (0-1.2 mm): a night-sky blue, so the white
//          snow stands out; or a translucent filament
//   snow   the scene on the glass (1.2-2.4 mm), and the name and year raised
//          0.8 mm on the base (2.4-3.2 mm)
// The AMS changes colour only on the twelve layers below 2.4 mm.
//
// The maker's mark is engraved in the back of the base, turned to read when the
// ornament is turned over on its loop (the domed one's read upside down that way,
// Scott's print, 2026-11-18).
//
//   NAME, YEAR   the personalisation (YEAR = "" leaves it off)
//   part = frame | glass | snow | union | all
include <../../brand/obc_mark.scad>

NAME = "Olivia";
YEAR = "2026";
part = "all";

$fn = 96;
GR    = 31;            // the globe's radius
GW    = 3.2;           // its rim's width
GRI   = GR - GW;
GY    = 12;            // its centre, above the base's middle
T     = 2.4;           // the frame's thickness
GLASS = 1.2;           // the glass: six layers, the 1.2 mm wall floor
RAISE = 0.8;           // the name and year stand this far above the base

// the base: a plinth with a lip under the globe
BASE_W0 = 62;          // across its foot
BASE_W1 = 50;          // across its top
BASE_H  = 28;
BASE_Y0 = GY - GR - BASE_H + 5;   // the globe sinks 5 mm into it
LIP_W   = 54; LIP_H = 3.0;

NAME_FONT = "Lobster:style=Regular";
YEAR_FONT = "Montserrat:style=ExtraBold";
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -'.!&";
NAME_ADV = [0.9278, 0.8903, 0.6903, 0.9208, 0.6375, 0.6375, 0.8028, 0.9236, 0.5208, 0.7444, 0.8347, 0.5264, 1.0931, 0.9278, 0.9236, 0.7958, 0.9236, 0.8347, 0.7917, 0.6681, 0.9944, 0.8542, 1.3361, 0.8611, 0.8611, 0.7528, 0.6486, 0.6167, 0.4736, 0.6611, 0.5083, 0.3708, 0.6667, 0.6292, 0.2903, 0.2958, 0.6556, 0.2875, 0.9736, 0.6306, 0.6764, 0.65, 0.675, 0.5222, 0.4389, 0.3833, 0.6375, 0.575, 0.9181, 0.6945, 0.6389, 0.5944, 0.7583, 0.4403, 0.6833, 0.7139, 0.6611, 0.7181, 0.6945, 0.6444, 0.6931, 0.6792, 0.3014, 0.4028, 0.2722, 0.3653, 0.3569, 0.9472];
function name_adv(c) = let (i = search(c, NAME_CHARS)) len(i) && i[0] != [] ? NAME_ADV[i[0]] : 0.7;
function name_w(s, n) = n <= 0 ? 0 : name_w(s, n - 1) + name_adv(s[n - 1]);
NAME_W    = 46;
NAME_SIZE = len(NAME) == 0 ? 11 : min(11, NAME_W / name_w(NAME, len(NAME)));
YEAR_SIZE = 6.0;
NAME_Y    = BASE_Y0 + BASE_H - LIP_H - 7.3 - (len(YEAR) ? 0 : 4.5);
YEAR_Y    = BASE_Y0 + 5.0;

module clean() offset(r = 0.21, $fn = 12) offset(delta = -0.21) offset(r = -0.425, $fn = 12) offset(delta = 0.425) children();
module words2d() clean() {
    translate([0, NAME_Y]) text(NAME, size = NAME_SIZE, font = NAME_FONT, halign = "center", valign = "center");
    if (len(YEAR)) translate([0, YEAR_Y]) text(YEAR, size = YEAR_SIZE, font = YEAR_FONT, halign = "center", valign = "center", spacing = 1.12);
}

module base2d() {
    translate([0, BASE_Y0]) polygon([[-BASE_W0 / 2, 0], [BASE_W0 / 2, 0], [BASE_W1 / 2, BASE_H - LIP_H], [-BASE_W1 / 2, BASE_H - LIP_H]]);
    translate([-LIP_W / 2, BASE_Y0 + BASE_H - LIP_H]) square([LIP_W, LIP_H]);
}
LOOP_RO = 4.6; LOOP_RI = 2.2;
// inside corners filled to a 1.2 mm radius: where the rim meets the base's lip
// they made a wedge of air too thin to print open (silhouette check, 2026-11-18)
// The glass's hole is cut after, so the frame's inner edge, the glass and the
// scene's edge are one circle: a filleted copy of it left hairline slivers.
module frame2d() difference() {
    offset(r = -1.2, $fn = 24) offset(delta = 1.2) {
        translate([0, GY]) circle(r = GR, $fn = 192);
        translate([0, GY + GR + LOOP_RO - 1.6]) circle(r = LOOP_RO, $fn = 48);
        base2d();
    }
    translate([0, GY]) circle(r = GRI, $fn = 192);
    translate([0, GY + GR + LOOP_RO - 1.6]) circle(r = LOOP_RI, $fn = 48);
}
module glass2d() translate([0, GY]) circle(r = GRI, $fn = 192);

// anything narrower than 1.2 mm (two beads) taken off, and sharp tips rounded at
// 0.6 mm: a star's point or a holly spike otherwise runs down to nothing
module open12() offset(r = 0.6, $fn = 16) offset(delta = -0.6) children();
module star2d(r, k = 0.47) polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, rr = i % 2 ? r * k : r) [rr * cos(a), rr * sin(a)]]);
// the scene, in globe coordinates (0, 0 = the globe's centre)
module cottage2d() difference() {
    union() {
        translate([-8, -9]) square([16, 14]);                                   // walls, down into the drift
        polygon([[-11, 4], [11, 4], [0, 13.5]]);                                // roof
        translate([4.2, 7]) square([3.2, 7]);                                   // chimney
    }
    translate([-1.6, -6.1]) square([3.2, 5.6]);                                 // door
    for (x = [-6, 3.2]) translate([x, -0.6]) square([2.8, 2.8]);                // windows
    translate([-1.3, 6.4]) square([2.6, 2.6]);                                  // the gable's window
}
module tree2d(h = 24) {
    for (i = [0 : 2]) let (w = [15, 12, 8.5][i], y = h * [0, 0.3, 0.56][i]) translate([0, y]) polygon([[-w / 2, 0], [w / 2, 0], [0, h * 0.44]]);
    translate([0, h + 0.4]) star2d(3.2);                                        // on the tip, no gap under it
}
// the snow on the ground: a soft drift across the bottom of the glass
module drift2d() polygon(concat([[GRI, -GRI], [-GRI, -GRI]],
    [for (i = [0 : 40]) let (x = -GRI + 2 * GRI * i / 40) [x, -15 + 2.6 * sin(1.3 * x * 6) + 1.6 * cos(x * 11)]]));
SNOW = [[-21, 10], [-6, 21], [2, 24], [9, 19], [-20, 1], [-11, 9], [-3, 15], [21, 5], [3, 8],
        [-23, -6], [22, -4], [-8, 23.5], [16, 17], [6, 14], [-17, 17]];
module scene2d() open12() intersection() {
    circle(r = GRI, $fn = 192);      // the rim's own inner edge: 0.01 short left a gap
    union() {
        drift2d();
        translate([-6.5, -11.2]) cottage2d();
        translate([12.5, -16.2]) tree2d();   // its lowest tier sunk into the drift
        for (p = SNOW) translate(p) circle(r = 1.1, $fn = 20);
        translate([-13.5, 17.5]) difference() { circle(r = 4.5, $fn = 48); translate([2.2, 1.3]) circle(r = 4.1, $fn = 48); }   // the moon
    }
}

module frame() linear_extrude(T) frame2d();
module glass() linear_extrude(GLASS) glass2d();
module snow() {
    translate([0, GY, GLASS]) linear_extrude(T - GLASS) scene2d();
    translate([0, 0, T]) linear_extrude(RAISE) words2d();
}
MARK_H = 5.0;
// turned 180 from obc_mark's (which reads when tipped back, as under a building)
module frame_marked() difference() { frame(); translate([0, BASE_Y0 + BASE_H / 2 - 1, 0]) rotate([0, 0, 180]) obc_engrave(MARK_H); }

if (part == "frame") frame_marked();
else if (part == "glass") glass();
else if (part == "snow") snow();
else if (part == "union") union() { frame_marked(); glass(); snow(); }
else { color("#C62F3A") frame_marked(); color("#2F4B7C") glass(); color("#F4F1EA") snow(); }
