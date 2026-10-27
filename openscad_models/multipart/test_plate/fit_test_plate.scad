// Fit test plate for the multipart line (2026-10-27). Scott prints this once
// on his P1S; each product after it is drawn at the clearances that worked on
// his printer, not at a guess. Five mechanisms, each a mating pair in three
// clearances, the clearance engraved on a tab:
//
//   thread    Nesting Characters: 24 mm, pitch 3, 39 deg flanks; the nut
//             grown 0.2 / 0.3 / 0.4 mm all round
//   ball      Creature Kit: an 8 mm ball snapped into a split socket whose
//             mouth is 0.4 / 0.6 / 0.8 mm narrower than the ball
//   gears     Kinetic Toy: module 1.5, 20 and 10 teeth on pins, centres
//             22.5 mm apart plus 0 / 0.15 / 0.3
//   detent    Perpetual Calendar: a 12-notch wheel clicked by a spring arm
//             0.8 / 1.0 / 1.2 mm thick
//   bayonet   Candy Dispenser: a cap twisting into a ring, lugs and slots
//             0.2 / 0.3 / 0.4 mm apart
//
// Every part prints as drawn, flat face down, no supports. kind and idx pick
// one part (build.sh exports them all).

$fn = 64;

include <../thread_lib.scad>
use <MCAD/involute_gears.scad>

FONT = "DejaVu Sans:style=Bold";
module label(txt, h) translate([0, 0, h - 0.6]) linear_extrude(0.7)
    text(txt, size = 4, font = FONT, halign = "center", valign = "center");
// a tab off a part's foot carrying its clearance, engraved
module tab(txt, l = 16, w = 8, h = 2) difference() {
    translate([-l / 2, -w / 2, 0]) cube([l, w, h]);
    label(txt, h);
}

// ---- thread -------------------------------------------------------------------------------
TD = 24; TP = 3; TDEP = 0.8; TL = 7; TC = [0.2, 0.3, 0.4];
module screw(i) difference() {
    union() {
        cylinder(d = 30, h = 2);
        translate([0, 0, 2]) thread_chamfer(TD, TL, TDEP) thread_solid(TD, TP, TL, TDEP);
        translate([-21, 0, 0]) tab(str(TC[i]));
    }
    translate([0, 0, -1]) cylinder(d = 17, h = TL + 4);
}
module nut(i) let (c = TC[i]) difference() {
    union() { cylinder(d = 33, h = TL, $fn = 8); translate([-22, 0, 0]) tab(str(c)); }
    translate([0, 0, -0.01]) thread_solid(TD, TP, TL + 0.02, TDEP, c);
    // lead-ins at both mouths, at the flanks' angle
    for (z = [0, TL]) translate([0, 0, z]) mirror([0, 0, z > 0 ? 1 : 0])
        translate([0, 0, -0.01]) cylinder(d1 = TD + 2 * c + 1.2, d2 = TD - 2 * TDEP,
            h = THREAD_FLANK * (2 * TDEP + 1.2 + 2 * c) / 2);
}

// ---- ball joint -----------------------------------------------------------------------------
BR = 4; BI = [0.4, 0.6, 0.8]; BRC = BR + 0.1;      // the socket's hollow, a hair over the ball
BA = 40;
module ball(i) {
    cylinder(d = 16, h = 2);
    cylinder(d = 4.4, h = 9);
    // under the ball a cone BA off vertical down to the stem, so it prints (at
    // exactly 45 the slicer supports it): tangent to the ball BA below its
    // equator, it meets the stem's radius 2.2 at BR / sin(BA) - 2.2 / tan(BA)
    // under the centre. The ball is round from BA below its equator up, past
    // the socket's mouth.
    hull() { translate([0, 0, 12]) sphere(r = BR); translate([0, 0, 12 - BR / sin(BA) + 2.2 / tan(BA)]) cylinder(r = 2.2, h = 0.01); }
    translate([-13, 0, 0]) tab(str(BI[i]));
}
module socket(i) let (rm = BR - BI[i] / 2, hc = 2 + 0.8 + BRC, hm = sqrt(BRC * BRC - rm * rm)) difference() {
    union() {
        cylinder(d = 16, h = 2);
        cylinder(r = BRC + 2, h = hc + hm + 0.6);
        translate([-13, 0, 0]) tab(str(BI[i]));
    }
    translate([0, 0, hc]) sphere(r = BRC);
    // the mouth: a 45 deg lead-in above the narrowest point
    translate([0, 0, hc + hm]) cylinder(r1 = rm, r2 = rm + 0.7, h = 0.61);
    // four slits so the cup flexes over the ball
    for (a = [0 : 90 : 270]) rotate(a) translate([0, -0.4, hc - 1]) cube([BRC + 3, 0.8, 10]);
}

// ---- gears ----------------------------------------------------------------------------------
GCP = 270;                  // MCAD's circular pitch: module 1.5 x 180
GN = [20, 10]; GO = [0, 0.15, 0.3];
GCD = (GN[0] + GN[1]) * GCP / 360;      // 22.5
module spur(n) gear(number_of_teeth = n, circular_pitch = GCP, pressure_angle = 20, clearance = 0.2,
    gear_thickness = 5, rim_thickness = 5, rim_width = 3, hub_thickness = 5, hub_diameter = 10,
    bore_diameter = 5.4, circles = 0, backlash = 0.1);
module pin() { cylinder(d = 5, h = 7.5); translate([0, 0, 7.5]) cylinder(d1 = 5, d2 = 4, h = 0.5); }
module gear_base(i) let (cd = GCD + GO[i]) {
    hull() { cylinder(d = 38, h = 3); translate([cd, 0, 0]) cylinder(d = 24, h = 3); }
    translate([0, 0, 3]) pin();
    translate([cd, 0, 3]) pin();
    translate([cd / 2 - 3, -19, 0]) tab(str("+", GO[i]));
}

// ---- detent ---------------------------------------------------------------------------------
DT = [0.8, 1.0, 1.2]; DR = 15; DN = 12; DDEP = 1.0;
module detent_wheel() difference() {
    cylinder(r = DR, h = 5, $fn = 96);
    translate([0, 0, -1]) cylinder(d = 5.4, h = 7);
    for (k = [0 : DN - 1]) rotate(k * 360 / DN) translate([0, 0, -1]) linear_extrude(7)
        polygon([[DR - DDEP, 0], [DR + 1, -2.4], [DR + 1, 2.4]]);     // the bump sits in it with 0.03 to spare
    // a mark to count clicks by
    translate([DR - 4, 0, 4.4]) cylinder(d = 2, h = 1);
}
// the arm runs along x over the wheel, a bump on it riding the rim: it must
// bend 0.6 mm to pass from one notch to the next
module detent_base(i) let (t = DT[i], yb = DR + 0.6) {
    // the label goes in the plate's own top: a tab on the plate would bury it
    difference() { translate([-20, -18, 0]) cube([46, 40, 3]); translate([16, -12, 0]) label(str(t), 3); }
    translate([0, 0, 3]) pin();
    translate([-20, yb, 3]) cube([4, 4 + t, 5]);                     // the arm's root
    translate([-16, yb, 3]) cube([19, t, 5]);                         // the arm
    translate([0, yb, 3]) cylinder(r = 1.2, h = 5, $fn = 24);         // the bump
}

// ---- bayonet --------------------------------------------------------------------------------
// The ring's L slots and the cap's lugs slope at YS (39 deg off vertical), so
// the slot's ceiling and the lug's underside as printed need no support.
YC = [0.2, 0.3, 0.4];
YRI = 16;                   // the ring's bore
YLD = 1.4;                  // the slots' depth into the wall
YH = 10;                    // the ring's height
YZ = 3; YLH = 3;            // the turn slot: its floor, its height
YS = 1.25;                  // the slopes' rise over run
module bayonet_ring(i) difference() {
    union() { cylinder(r = YRI + 4, h = YH, $fn = 96); translate([-26, 0, 0]) tab(str(YC[i])); }
    translate([0, 0, -1]) cylinder(r = YRI, h = YH + 2, $fn = 96);
    for (k = [0 : 2]) rotate(k * 120) {
        // the way in, from the top down to the turn slot
        rotate(-6) rotate_extrude(angle = 12, $fn = 96) translate([YRI - 0.1, YZ]) square([YLD + 0.1, YH]);
        // the turn, 30 deg on, its ceiling at 45 deg
        rotate(-6) rotate_extrude(angle = 36, $fn = 96) translate([YRI - 0.1, YZ])
            polygon([[0, 0], [YLD + 0.1, 0], [YLD + 0.1, YLH], [0, YLH + YS * (YLD + 0.1)]]);
    }
}
module bayonet_cap(i) let (c = YC[i], ro = YRI - c) difference() {
    union() {
        cylinder(r = YRI + 4, h = 2, $fn = 96);                       // the flange, on the plate
        cylinder(r = ro, h = 2 + YH - YZ - 0.4, $fn = 96);            // the plug
        // the lugs, at the plug's far end, their faces toward the flange sloped;
        // c narrower each side than the 12 deg way in
        let (la = 12 - 2 * c / ro * 180 / PI)
        for (k = [0 : 2]) rotate(k * 120 - la / 2) rotate_extrude(angle = la, $fn = 96)
            translate([ro - 0.1, 2 + YH - YZ - 0.4 - (YLH - 2 * c)])
                polygon([[0, -YS * (YLD - c)], [YLD - c + 0.1, 0], [YLD - c + 0.1, YLH - 2 * c], [0, YLH - 2 * c]]);
        translate([-26, 0, 0]) tab(str(c));
    }
    translate([0, 0, -1]) cylinder(r = ro - 2, h = YH + 4, $fn = 96);
}

// ---- the parts -------------------------------------------------------------------------------
// Each exports on its own at the origin (build.sh); pack_plate.py lays them
// out on the P1S's plate.
KINDS = ["screw", "nut", "ball", "socket", "gear_base", "gear20", "gear10", "detent_base", "detent_wheel",
         "bayonet_ring", "bayonet_cap"];
module piece(kind, i) {
    if (kind == "screw") screw(i);
    else if (kind == "nut") nut(i);
    else if (kind == "ball") ball(i);
    else if (kind == "socket") socket(i);
    else if (kind == "gear_base") gear_base(i);
    else if (kind == "gear20") spur(GN[0]);
    else if (kind == "gear10") spur(GN[1]);
    else if (kind == "detent_base") detent_base(i);
    else if (kind == "detent_wheel") detent_wheel();
    else if (kind == "bayonet_ring") bayonet_ring(i);
    else if (kind == "bayonet_cap") bayonet_cap(i);
}
kind = "screw"; idx = 0;
piece(kind, idx);
