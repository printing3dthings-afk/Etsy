// Pocket Top: the snap test print (2026-11-14). The top's form isn't chosen yet; this tests
// only the joint every form will use: a hex stem through a hub, held by three spring beams.
// Numbers: snap_budget.py (checks/snap_budget.txt). Scott snaps each pair 20 times.
//
// The hub prints flat. Round its hex hole, three straight beams lie in the hub's plane, each
// with a nub at its free end that reaches through a window in the hole's wall into a groove
// round the stem. The beams bend in the print plane, along the layers (the Gear Heart's posts
// bent across them and snapped). The stem prints upright on its grip, so its hex and groove
// are drawn in the plane and come out true; it doesn't flex. The hex drives the spin; the
// three nubs, held 0.05 into the groove, centre the stem.
//
// Three pairs, differing only in how far the nubs reach into the groove (snap_budget.py):
//   1 mark 0.35 mm, 2 marks 0.45 (the design value), 3 marks 0.55.
// The groove is a ring, so a stem goes in any way round; the hub's top faces the grip.
// A hub with 1, 2 or 3 notches goes with the stem with as many flats on its grip.
//
//   part = "all" (the print plate) | "hubs" | "stems" | "stem" (one, by which) | "hub_body" (a hub without its nubs,
//          for the fit check) | "assembled" (review)

part = "all";
which = 0;                // for part = "stem": which stem, 0 to 2
$fn = 64;

REACH = [0.35, 0.45, 0.55];
S = 5.0;                 // the stem's hex, across its flats
CLR = 0.15;              // the hole's hex, each side (a hole drawn in XY prints small)
A = S / 2 + CLR;         // the hole's face distance
B = 3.4;                 // hub thickness: the beams' width
WALL = 1.3;              // the hole's wall, between the hex and the beams
G = 0.8;                 // the gaps round each beam: their ends are round, r 0.4, the root fillet
T = 1.3;                 // beam thickness, in the bend (1.2 sat exactly on the gate's floor)
L = 12.0;                // beam length, root to nub
NUB_W = 1.4;             // the nub, along the beam (at 1.2 it was the gate's thinnest span)
NUB_H = 1.6;             // the nub's height: the hub's bed-side 1.6. Above it the hole's hex
                         // drives the stem's full hex
WIN = 0.3;               // the nub's window, each side
PRELOAD = 0.05;          // the nub stays this far bent in the groove
HUB_R = 15.5;            // the coupon only (16 sliced at 34 min); 15 left 1.0 of rim past the slots
GRIP_R = 5;
GRIP_H = 2.4;
SHAFT = 8;               // the hex above the grip
FLANK = 60;              // the groove's catch flank, from horizontal: at 45 it faced down on
                         // the upright stem and the gate's slicer propped it
CH = 0.8;                // the stem end's lead-in chamfer, 45 deg

function nub_x(i) = S / 2 - REACH[i];     // where the nub's tip sits, free

// a hex with flats facing 0, 60, 120 ... deg (circle($fn = 6) puts a corner at 0)
module hex2d(af) rotate(30) circle(d = af / cos(30), $fn = 6);

// one beam's cut, in its frame (the hole's face normal along +x, nub at y = 0)
module beam_cut() {
    x0 = A + WALL;
    for (cx = [x0 + G / 2, x0 + G + T + G / 2])
        hull() { translate([cx - G / 2, -NUB_W / 2 - G]) square([G, 0.01]); translate([cx, L]) circle(d = G, $fn = 24); }
    translate([x0, -NUB_W / 2 - G]) square([2 * G + T, G]);                  // round the free end
    translate([A - 1, -NUB_W / 2 - WIN]) square([WALL + 1.01, NUB_W + 2 * WIN]);  // the nub's window
}
module nub(i) translate([nub_x(i), -NUB_W / 2]) square([A + WALL + G - nub_x(i) + 0.01, NUB_W]);

module hub2d() difference() {
    circle(r = HUB_R, $fn = 128);
    hex2d(2 * A);
    for (k = [0 : 2]) rotate(120 * k) beam_cut();
}
module hub(i, nubs = true) difference() {
    union() {
        linear_extrude(B) hub2d();
        if (nubs) linear_extrude(NUB_H) for (k = [0 : 2]) rotate(120 * k) nub(i);
    }
    // the variant's notches in the rim (upright grooves: they hang over nothing)
    for (k = [0 : i]) rotate(-90 + (k - i / 2) * 10) translate([HUB_R - 0.6, -0.45, -1]) cube([2, 0.9, B + 2]);
}

module stem(i) {
    rg = S / 2 - REACH[i] + PRELOAD;          // the groove's floor: the nubs stay bent PRELOAD
    difference() {
        union() {
            cylinder(r = GRIP_R, h = GRIP_H, $fn = 96);
            // the hex, with a 45 deg lead-in at its end
            hull() {
                translate([0, 0, GRIP_H - 0.01]) linear_extrude(SHAFT - CH + 0.01) hex2d(S);
                translate([0, 0, GRIP_H + SHAFT - CH]) linear_extrude(CH) hex2d(S - 2 * CH);
            }
        }
        // the groove: a ring, so the stem goes in any way round. In use the hub's top (its
        // drive band) is against the grip and its nubs are furthest from it, so the groove
        // runs from z0 to z1 with 0.15 to spare each end. Its catch flank, the far one, rises
        // at FLANK from horizontal; the near end is square (it faces up as it prints).
        z0 = GRIP_H + B - NUB_H - 0.15;
        z1 = GRIP_H + B + 0.15;
        rotate_extrude($fn = 96) polygon([[rg, z0], [S, z0], [S, z1 + (S - rg) * tan(FLANK)], [rg, z1]]);
        // the variant's mark: 1, 2 or 3 flats on the grip, 60 deg apart (notches here left
        // thin fins and rim corners that the gate read as walls under 1.2)
        for (k = [0 : i]) rotate(-90 + (k - i / 2) * 60) translate([GRIP_R - 0.8, -GRIP_R, -1]) cube([2, 2 * GRIP_R, GRIP_H + 2]);
    }
}

module hubs(nubs = true) for (i = [0 : 2]) translate([i * 36, 0, 0]) hub(i, nubs);
module stems() for (i = [0 : 2]) translate([i * 36, -26, 0]) stem(i);

// in use: the stem's grip on top, the hub against its shoulder (the stem turned over)
module assembled() for (i = [0 : 2]) translate([i * 36, 0, 0]) {
    color("teal") hub(i);
    color("gold") translate([0, 0, B + GRIP_H]) mirror([0, 0, 1]) stem(i);
}

if (part == "hubs") hubs();
else if (part == "hub_body") hubs(false);
else if (part == "stems") stems();
else if (part == "stem") translate([which * 36, -26, 0]) stem(which);
else if (part == "assembled") assembled();
else if (part == "all") { hubs(); stems(); }

// the joint's numbers, for designs that `use` this file (2026-11-15): use<> brings in modules
// and functions, not variables
function snap_dims() = [S, A, B, NUB_H, REACH, PRELOAD, FLANK];
