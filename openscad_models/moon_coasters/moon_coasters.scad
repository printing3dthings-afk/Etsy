// Moon Phase Coasters (2026-11-11). Scott picked form D of five for the coaster
// set: "the four coasters show the moon's phases and stand in an arched night-sky
// rack."
//
// Four coasters: waxing crescent, first quarter, waxing gibbous, full. Navy sky,
// the lit moon cream, its dark side slate, cream stars: all flush inlays in the
// top three layers, inside a rim 0.8 mm proud that keeps drips on the coaster.
// The OBC mark is inlaid in cream underneath.
//
// The rack is two flat prints: a navy base whose curved cradles hold the
// coasters upright one behind another, and an arched navy panel with cream stars
// that slides into a groove at the front. Its round window frames the front
// coaster's moon. Printed flat, the window has no bridge; printed upright, its top
// would have been an 68 mm arc in mid-air.
//
// Millimetres. Coaster: face up, centre on the origin. Base: x across, y front to
// back (front at y = 0), z up. Panel: printed flat, its front face up.
//
//   part = coaster_navy | coaster_cream | coaster_slate   (with phase = 0..3)
//          base | panel_navy | panel_cream
//          coaster_print | panel_print   (welded, for the gates)
//          assembly (preview)

include <BOSL2/std.scad>
use <../brand/obc_mark.scad>

part  = "assembly";
phase = 3;                 // 0 crescent, 1 first quarter, 2 gibbous, 3 full
$fn = 128;

// ---------- coaster ----------
D        = 92;
R        = D / 2;
T_FACE   = 4.0;            // the face the cup sits on
RIM_W    = 2.4;            // three beads and a margin
RIM_H    = 0.8;            // four layers proud
T        = T_FACE + RIM_H;
EDGE     = 0.6;            // outer top edge, three 0.2 steps in
INLAY    = 0.6;            // face colours: the top three layers of the face
MOON_R   = 29;
TERM     = [0.55, 0, 0.55, 0];   // terminator ellipse, as a fraction of MOON_R
MARK_H   = 7;
PHASE_NAME = ["waxing crescent", "first quarter", "waxing gibbous", "full moon"];

// stars: [x, y, size]; rounded so no point is finer than two beads (0.8 mm)
STARS = [[-36, 6, 3.2], [-31, -19, 2.4], [-21, 31, 2.8], [-8, -37, 2.2],
         [14, 35, 2.4], [31, 21, 2.0], [35, -14, 3.0], [21, -32, 2.6],
         [-37, -6, 1.8], [2, 39, 1.8]];

module star2d(s) offset(r = 0.4) offset(delta = -0.4)
    polygon([for (i = [0 : 7]) let (a = 90 + i * 45, r = i % 2 ? s * 0.38 : s) [r * cos(a), r * sin(a)]]);
module stars2d(list) for (p = list) translate([p[0], p[1]]) star2d(p[2]);

// The lit part. Waxing: the right side is lit. The terminator is a half-ellipse
// of semi-axis TERM * MOON_R: subtracted from the lit half for a crescent, added
// for a gibbous.
module lit2d(ph) let (a = max(TERM[ph] * MOON_R, 0.01))
    if (ph == 3) circle(MOON_R);
    else if (ph == 1) intersection() { circle(MOON_R); translate([0, -MOON_R]) square([MOON_R, 2 * MOON_R]); }
    else if (ph == 0) difference() {
        intersection() { circle(MOON_R); translate([0, -MOON_R]) square([MOON_R, 2 * MOON_R]); }
        scale([a, MOON_R]) circle(1);
    }
    else union() {
        intersection() { circle(MOON_R); translate([0, -MOON_R]) square([MOON_R, 2 * MOON_R]); }
        scale([a, MOON_R]) circle(1);
    }
// Craters: slate patches on the lit side only, so a plain cream disc reads as the
// moon. [x, y, rx, ry]; every one is wider than 0.8 mm (rule 11) wherever the
// terminator clips it, or it is dropped by the 1.2 mm opening below.
CRATERS = [[10, 12, 5.0, 4.0], [17, -6, 3.4, 3.0], [4, -14, 4.2, 3.4], [-9, 6, 3.6, 3.0],
           [21, 9, 2.4, 2.0], [-14, -12, 3.0, 2.6], [8, 22, 2.2, 1.8]];
module craters2d(ph) offset(r = 0.6) offset(r = -0.6) intersection() {
    offset(delta = -1.2) lit2d(ph);
    for (c = CRATERS) translate([c[0], c[1]]) scale([c[2], c[3]]) circle(1);
}
module dark2d(ph) difference() { circle(MOON_R); lit2d(ph); }

module slab(t) linear_extrude(t) children();
module coaster_body() union() {
    // body to the face, the top edge stepped in on the rim
    slab(T - EDGE) circle(R);
    for (i = [0 : round(EDGE / 0.2) - 1])
        translate([0, 0, T - EDGE + 0.2 * i]) slab(0.2) difference() { circle(R - 0.2 * (i + 1)); circle(R - RIM_W); }
}
module coaster_shape() difference() {
    coaster_body();
    translate([0, 0, T_FACE]) slab(5) circle(R - RIM_W);
}
// An inlay is exactly the top three layers, flush with the face. Only the pocket
// in the navy runs past the face: an inlay cut 0.01 taller stood 0.01 proud, and
// the weld pinched where the moon's circle meets the terminator (open edges).
module face_cut() translate([0, 0, T_FACE - INLAY]) slab(INLAY) children();
module face_pocket() translate([0, 0, T_FACE - INLAY]) slab(INLAY + 2) children();

module coaster_cream(ph) union() {
    face_cut() difference() { lit2d(ph); craters2d(ph); }
    face_cut() stars2d(STARS);
    obc_inlay(MARK_H);
}
module coaster_slate(ph) face_cut() union() { dark2d(ph); craters2d(ph); }
module coaster_navy(ph) difference() {
    coaster_shape();
    face_pocket() circle(MOON_R);
    face_pocket() stars2d(STARS);
    obc_cut(MARK_H);
    obc_inlay(MARK_H);
}

// ---------- rack ----------
CLEAR   = 0.4;                     // each side of a coaster in its slot
SLOT_W  = T + 2 * CLEAR;           // 5.6
WALL    = 2.4;
N       = 4;
P_T     = 3.0;                     // the arch panel's thickness
GROOVE  = P_T + 2 * CLEAR;         // 3.8
LIP     = 3.0;                     // in front of the groove
BACK_W  = 3.0;                     // not BACK: that is BOSL2's direction, and overriding it broke every anchor
B_H     = 16;                      // base height
CRADLE  = 4;                       // a coaster's lowest point sits this high
B_W     = D + 2 * 6;               // 104
B_D     = LIP + GROOVE + WALL + N * SLOT_W + (N - 1) * WALL + BACK_W;
GROOVE_DEPTH = B_H - CRADLE;
function slot_y(i) = LIP + GROOVE + WALL + i * (SLOT_W + WALL);

// a curved cradle: the coaster's own circle, grown by the clearance
module cradle(y, w) translate([0, y, CRADLE + R]) rotate([-90, 0, 0]) cylinder(r = R + CLEAR, h = w);

module base_part() difference() {
    cuboid([B_W, B_D, B_H], rounding = 3, edges = "Z", anchor = FRONT + LEFT + BOTTOM, $fn = 32);
    for (i = [0 : N - 1]) translate([B_W / 2, 0, 0]) cradle(slot_y(i), SLOT_W);
    // the groove for the arch panel: as wide as the panel's foot, CRADLE deep from the floor
    translate([B_W / 2 - (P_FOOT_W / 2 + CLEAR), LIP, CRADLE]) cube([P_FOOT_W + 2 * CLEAR, GROOVE, 50]);
    translate([B_W / 2, B_D / 2, 0]) obc_cut(10);
}
module base_mark() translate([B_W / 2, B_D / 2, 0]) obc_inlay(10);

// The arch panel, drawn in x (across) and y (up), y = 0 at its foot. Its foot
// stands in the groove; the window's centre sits at the coasters' centre height.
P_FOOT_W = B_W - 8;               // 96: the groove leaves 4 mm of base each side
P_R      = P_FOOT_W / 2;
WIN_C    = R;                     // coaster centre above the groove floor (CRADLE + R - CRADLE)
WIN_R    = MOON_R + 5;            // frames the moon with a ring of sky
// Stars on the arch's band, midway between the window and the edge (each star at
// least 1.5 mm clear of both), and four in the lower corners above the base's top.
// The first list, placed by eye, put two stars over the arch's edge.
P_BAND   = (WIN_R + P_R) / 2;
P_STARS  = concat(
    [for (k = [0 : 6]) let (a = [12, 38, 62, 90, 118, 142, 168][k], s = [2.6, 2.0, 3.0, 2.2, 3.0, 2.0, 2.6][k])
        [P_BAND * cos(a), WIN_C + P_BAND * sin(a), s]],
    [[-42, 30, 2.4], [42, 32, 2.0], [-41, 18, 2.0], [41, 19, 2.6]]);
module panel2d() intersection() {
    union() { translate([-P_R, 0]) square([P_FOOT_W, WIN_C]); translate([0, WIN_C]) circle(P_R); }
    translate([-P_R, 0]) square([P_FOOT_W, 200]);      // the arch's circle runs below the foot
}
module panel_navy() difference() {
    slab(P_T) difference() { panel2d(); translate([0, WIN_C]) circle(WIN_R); }
    translate([0, 0, P_T - INLAY]) slab(1) stars2d(P_STARS);
}
module panel_cream() translate([0, 0, P_T - INLAY]) slab(INLAY) stars2d(P_STARS);

// ---------- preview ----------
module coaster_colours(ph) {
    color("#1F2A4A") coaster_navy(ph);
    color("#F2E6C8") coaster_cream(ph);
    color("#5C6680") coaster_slate(ph);
}
module assembly() {
    color("#1F2A4A") base_part();
    color("#F2E6C8") base_mark();
    // rotate([90, 0, 0]) turns the coaster's face (+z) to the front (-y)
    for (i = [0 : N - 1]) translate([B_W / 2, slot_y(i) + CLEAR + T, CRADLE + R]) rotate([90, 0, 0])
        coaster_colours(N - 1 - i);
    translate([B_W / 2, LIP + CLEAR + P_T, CRADLE]) rotate([90, 0, 0]) { color("#1F2A4A") panel_navy(); color("#F2E6C8") panel_cream(); }
}

// the set as it stands on a table, one colour per part, for review renders
module place_coaster(i) translate([B_W / 2, slot_y(i) + CLEAR + T, CRADLE + R]) rotate([90, 0, 0]) children();
module place_panel() translate([B_W / 2, LIP + CLEAR + P_T, CRADLE]) rotate([90, 0, 0]) children();
module asm(c)
    if (c == "navy") union() { base_part(); for (i = [0 : N - 1]) place_coaster(i) coaster_navy(N - 1 - i); place_panel() panel_navy(); }
    else if (c == "cream") union() { base_mark(); for (i = [0 : N - 1]) place_coaster(i) coaster_cream(N - 1 - i); place_panel() panel_cream(); }
    else for (i = [0 : N - 1]) place_coaster(i) coaster_slate(N - 1 - i);

// poses for the PDF guide: the prints flat as they come off the plate, the panel
// above its groove, the last coaster above its cradle
module flat(c)
    if (c == "navy") union() { for (k = [0 : 3]) translate([k * (D + 8), 0, 0]) coaster_navy(k);
        translate([-R, -R - 60, 0]) base_part(); translate([B_W - R + 70, -R - 104, 0]) panel_navy(); }
    else if (c == "cream") union() { for (k = [0 : 3]) translate([k * (D + 8), 0, 0]) coaster_cream(k);
        translate([-R, -R - 60, 0]) base_mark(); translate([B_W - R + 70, -R - 104, 0]) panel_cream(); }
    else for (k = [0 : 3]) translate([k * (D + 8), 0, 0]) coaster_slate(k);
module step(c, lift_panel, coasters, lift_first)
    if (c == "navy") union() { base_part(); translate([0, 0, lift_panel]) place_panel() panel_navy();
        if (coasters) for (i = [0 : N - 1]) translate([0, 0, i == 0 ? lift_first : 0]) place_coaster(i) coaster_navy(N - 1 - i); }
    else if (c == "cream") union() { base_mark(); translate([0, 0, lift_panel]) place_panel() panel_cream();
        if (coasters) for (i = [0 : N - 1]) translate([0, 0, i == 0 ? lift_first : 0]) place_coaster(i) coaster_cream(N - 1 - i); }
    else if (coasters) for (i = [0 : N - 1]) translate([0, 0, i == 0 ? lift_first : 0]) place_coaster(i) coaster_slate(N - 1 - i);
colour = "navy";
slot = 0;
if (part == "flat") flat(colour);
else if (part == "step_panel") step(colour, 40, false, 0);     // the panel 40 above its groove
else if (part == "step_coaster") step(colour, 0, true, 55);    // the front coaster coming down into its cradle
else if (part == "placed_coaster") place_coaster(slot) coaster_shape();
else if (part == "placed_panel") place_panel() union() { panel_navy(); panel_cream(); }
else if (part == "asm_navy") asm("navy");
else if (part == "asm_cream") asm("cream");
else if (part == "asm_slate") asm("slate");
// the four coasters side by side, face up, for a review render
else if (part == "row_navy") for (k = [0 : 3]) translate([k * (D + 6), 0, 0]) coaster_navy(k);
else if (part == "row_cream") for (k = [0 : 3]) translate([k * (D + 6), 0, 0]) coaster_cream(k);
else if (part == "row_slate") for (k = [0 : 3]) translate([k * (D + 6), 0, 0]) coaster_slate(k);
else if (part == "coaster_navy") coaster_navy(phase);
else if (part == "coaster_cream") coaster_cream(phase);
else if (part == "coaster_slate") coaster_slate(phase);
// The inlays fill their pockets exactly, so the welded coaster is the uncut shape.
// A union of the colour parts left the moon's rim as touching, unmerged walls.
else if (part == "coaster_print") coaster_shape();
else if (part == "base") base_part();
else if (part == "base_mark") base_mark();
else if (part == "base_print") union() { base_part(); base_mark(); }
else if (part == "panel_navy") panel_navy();
else if (part == "panel_cream") panel_cream();
else if (part == "panel_print") union() { panel_navy(); panel_cream(); }
else assembly();
