// Kit-card A-frame chalet: the snap test print (2026-11-25). Scott picked the A-frame chalet
// (2026-11-17) for the free MakerWorld kit-card pilot; the joint is proven before the chalet
// is built round it (mechanism handbook section 7; numbers in snap_budget.py).
//
// An arrow tab on a panel's edge goes through a slot and springs open under the far face. The
// tab's two prongs are the Pocket Top's beam (1.3 thick, 12 long), cut free inside the panel
// and lying in its plane: the panel prints flat, so they bend along the layers.
//
// The plate: a base strip with three slots (printed floor down, skirt up; in use the skirt
// stands on the table and the prongs' nubs sit inside it), and three panel stubs, one per
// reach. Notches on a stub's top edge and on the skirt beside its slot: one 0.35, two 0.45,
// three 0.55. Any stub fits any slot; the slots are all the same.
//
//   part = plate | base | stub (with which = 0..2) | stubs | assembled (review)

part = "plate";
which = 1;
$fn = 48;

REACH = [0.35, 0.45, 0.55];
P = 2.4;           // panel thickness: the prongs' width
T = 1.3;           // prong thickness, in the bend
L = 12;            // prong length, root to the catch
GAP = 1.6;         // between the prongs: each closes by the reach, 0.55 leaves 0.5
SIDE = 0.8;        // the cut beside each prong, inside the panel
GRIP = 3.0;        // the floor the tab passes through (the chalet's base and roof)
CATCH_CL = 0.15;   // the catch starts this far below the floor's far face
CATCH = 50;        // the catch flank, from the insertion axis
RAMP = 30;         // the lead-in, from the insertion axis
CREST = 0.4;       // the nub's flat top
TIP = 2.0;         // the tab tip: each prong ends 1.2 wide (at 0.8 the gate read it as a sub-floor wall)
SLOT_CL = 0.15;    // slot clearance each side of the prongs
SLOT_T = 0.2;      // and each side of the panel's thickness
MOUTH = 0.4;       // the slot's mouth chamfer, on the base's show face

XO = GAP / 2 + T;                 // a prong's outer face, from the centre
XS = XO + SLOT_CL;                // the slot's half-width
SKIRT = 5.0;                      // under the floor: deeper than the tab below it
WALL = 2.0;
SW = 18; SH = 15;                 // a stub (22 x 18 with a 26 pitch sliced at 32 m: over the 30-minute limit)
PITCH = 22;
BL = 3 * PITCH; BW = 18;          // the base strip

// one prong's outline below the shoulder, right side, for reach r (mirrored for the left)
function prong(r) = let(
    yc = -(GRIP + CATCH_CL),
    yn = yc - (XS + r - XO) / tan(CATCH),              // the nub's crest begins
    yr = yn - CREST,                                    // and ends
    yt = yr - (XS + r - TIP) / tan(RAMP))               // the tip
    [[GAP / 2, 0.01], [XO, 0.01], [XO, yc], [XS + r, yn], [XS + r, yr], [TIP, yt], [GAP / 2, yt]];

module stub2d(i) difference() {
    union() {
        translate([-SW / 2, 0]) square([SW, SH]);
        for (m = [0, 1]) mirror([m, 0]) polygon(prong(REACH[i]));
    }
    // the prongs cut free inside the panel, round-ended at the root
    yr = -(GRIP + CATCH_CL) + L;
    for (cx = [0, -(XO + SIDE / 2), XO + SIDE / 2]) {
        w = cx == 0 ? GAP : SIDE;
        hull() { translate([cx - w / 2, -1]) square([w, 0.01]); translate([cx, yr - w / 2]) circle(d = w); }
    }
    // the variant's notches on the top edge
    for (k = [0 : i]) translate([(k - i / 2) * 3 - 0.6, SH - 1.2]) square([1.2, 2]);
}
module stub(i) linear_extrude(P) stub2d(i);

module slot() {
    translate([-XS, -P / 2 - SLOT_T, -1]) cube([2 * XS, P + 2 * SLOT_T, GRIP + 2]);
    // mouth chamfer on the show face (z = 0 as printed: the bed)
    hull() {
        translate([-XS - MOUTH, -P / 2 - SLOT_T - MOUTH, -0.01]) cube([2 * (XS + MOUTH), P + 2 * (SLOT_T + MOUTH), 0.01]);
        translate([-XS, -P / 2 - SLOT_T, MOUTH]) cube([2 * XS, P + 2 * SLOT_T, 0.01]);
    }
}
// printed show face down: the floor on the bed, the skirt rising from it
module base() difference() {
    union() {
        cube([BL, BW, GRIP]);
        difference() { cube([BL, BW, GRIP + SKIRT]); translate([WALL, WALL, GRIP - 0.01]) cube([BL - 2 * WALL, BW - 2 * WALL, SKIRT + 1]); }
    }
    for (i = [0 : 2]) {
        translate([PITCH / 2 + i * PITCH, BW / 2, 0]) slot();
        // the variant's notches on the skirt's top (the table side in use), beside the slot
        for (k = [0 : i]) translate([PITCH / 2 + i * PITCH + (k - i / 2) * 3 - 0.6, -1, GRIP + SKIRT - 1.2]) cube([1.2, WALL + 2, 2]);
    }
}

if (part == "base") base();
else if (part == "stub") stub(which);
else if (part == "stubs") for (i = [0 : 2]) translate([i * (SW + 6), 0, 0]) stub(i);
else if (part == "plate") {
    base();
    for (i = [0 : 2]) translate([PITCH / 2 + i * PITCH - SW / 2 - 2, BW + 14, 0]) translate([SW / 2, 0, 0]) stub(i);
}
else if (part == "assembled") {
    // in use: the base turned over (show face up), stubs standing in their slots, snapped home
    translate([0, BW, GRIP]) rotate([180, 0, 0]) color("#EDE8DC") base();
    for (i = [0 : 2]) color("#B5651D") translate([PITCH / 2 + i * PITCH, BW / 2, GRIP]) rotate([90, 0, 0]) translate([0, 0, -P / 2]) stub(i);
}
