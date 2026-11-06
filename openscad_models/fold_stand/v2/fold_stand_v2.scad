// Fold Stand v2: a ratchet hinge with release buttons (2026-11-06).
//
// v1 (../fold_stand.scad, 2026-11-04) printed, and Scott found "no click at
// all. Very loose pin falls out". Its ridge stood 0.35 into a 90 deg V on a
// 4 mm pin: too shallow to catch, and a V pushes the ridge out either way, so
// even a good click could only resist the legs spreading weakly. Its pins
// were a 0.05 press fit, which printed loose.
//
// v2 keeps the stand and its five angles and makes the hinge a one-way
// ratchet (Scott, 2026-11-06: "a gear system that clicks as you move it and it
// stays", with a release tab):
//   - each pin carries a ring of sawtooth notches, one per angle. The blade's
//     ridge has a flat top face: against a notch's radial face it LOCKS, so the
//     phone's weight can't spread the legs, however slick the table. Folding it
//     toward upright, the ridge rides up the notch's slope and clicks into the
//     next one;
//   - the pins' heads are buttons. Pinch both ends of the hinge: each pin slides
//     in about a millimetre, a cone on it lifts the ridge clear of the notches,
//     and the leg swings free. Let go and the blade, pressing on the cone,
//     pushes the pin back out and the ridge drops into the next notch;
//   - the pins can't fall out: past the notches each has a wall the ridge must
//     climb, about 7 N of pull. They slide in the front plate's barrel (keyed,
//     not pressed), so there's no press fit to print loose.
// It also locks folded, so it stays shut in a bag: pinch to open.
//
// Every part prints flat or upright with nothing hanging: the bores are
// teardrops in section, the pins print standing on their heads, and the
// tongues are upright blades cut free by upright slots.
//
//   part = front | back | pin (as printed) | front_use | back_use(at ANG) |
//          pins_use | all
use <../../brand/obc_mark.scad>

part = "all";
ANG = 36;                   // the opening shown in "all" and back_use
$fn = 96;

// ---- sizes -------------------------------------------------------------------------------------
CLR_KEY = 0.15;             // a pin in the front plate's barrel: keyed, and slides for the button.
                            // v1's 0.05 press fit printed loose and the pins fell out
CLR_RUN = 0.15;             // a pin in the back plate's barrel: it turns
W = 76;                     // the stand's width, along the hinge
T = 4;                      // the plates
LF = 105;                   // the front plate, hinge to foot
LR = LF;                    // the back plate (the leg), as long as the front: 10 shorter, the A
                            // leaned hard toward it when nearly closed (2026-11-04)
PR = 4;                     // a pin's radius
RK = ceil(((PR + CLR_RUN) / sin(37) + 1.25) * 10) / 10;   // the barrel's radius: 1.2 of wall over
                            // the bore's teardrop point, 8.2. Capped flat to keep the barrels
                            // small, the bores' 2.5 roofs counted as overhangs (2026-11-04)
AF = RK;                    // the hinge's axis over the front plate's inner face (its
                            // print bed): the barrel sits on the bed
AR = T + AF;                // and over the back plate's outer face: folded, the
                            // inner faces meet and the axes agree, 10
K1 = 14; K2 = W - 14;       // the front plate's barrels: x 0..K1 and K2..W
XG = 0.4;                   // between barrels
// ---- the clicks --------------------------------------------------------------------------------
STOPS = [0, 24, 36, 48, 60, 72];        // the openings it clicks at: folded, then five that
                                        // lean a phone at about 81, 75, 69, 63 and 57 deg. A
                                        // phone rests on the barrel, 7 deg steeper than the
                                        // plate: the stops were first set from the plate
// the pin's ratchet band: crests and roots of the notches, and the ridge's tip unbent,
// 0.1 below the roots so it seats with some preload
CREST = 3.4; ROOT = 2.95; R_FREE = 2.85;
// a 1.6 x 18 blade: bending out 1.15 to pass a pin going in is 30 MPa at the root, along
// the layers (PLA ~50); clicking over a crest is 0.55, 14 MPa. v1's 2.0 x 12 bent 0.35
BLADE_T = 1.6; TONGUE_L = 18; SLOT = 0.8;
RIDGE_L = 3;
// ---- the lip -----------------------------------------------------------------------------------
LIP_W = 8;                  // along the plate
LIP_H = 11;                 // out from it: a phone in a case is up to about 10.5 thick
CHIN = 1.6;                 // the lip's top leans out this far over the phone's edge
CABLE = 14;                 // a slot through the lip for a charging cable

// a teardrop in (y, z), its point up (+z), r its round part's radius
module tear2d(r) hull() { circle(r = r); translate([0, r / sin(37)]) circle(r = 0.01); }
// a barrel's section: round over the axis, square down to the print bed
module barrel2d(a) hull() { translate([0, a]) circle(r = RK); translate([-RK, 0]) square([2 * RK, 0.01]); }
// extrude a (y, z) section along x from x0 to x1
module along_x(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
// how far each plate is cut back round the other's barrels: their corners' sweep
CUT_F = sqrt(RK * RK + AR * AR) + 0.5;  // the back plate's barrel, from the front plate
CUT_R = sqrt(RK * RK + AF * AF) + 0.5;  // the front plate's barrels, from the back plate

// ---- the front plate, as printed: inner face on the bed, the hinge along x at (0, AF) ----------
module front() difference() {
    union() {
        // the plate, cut back from the back plate's barrel between the front's own
        translate([0, -LF, 0]) cube([W, LF - CUT_F, T]);
        for (r = [[0, K1], [K2, W]]) {
            translate([r[0], -LF, 0]) cube([r[1] - r[0], LF, T]);
            along_x(r[0], r[1]) barrel2d(AF);
        }
        // the lip at the foot: a face for the phone's edge, its top leaning out
        difference() {
            along_x(0, W) polygon([[-LF, T - 0.01], [-LF + LIP_W, T - 0.01], [-LF + LIP_W, T + LIP_H - CHIN / tan(37)],
                                   [-LF + LIP_W + CHIN, T + LIP_H], [-LF, T + LIP_H]]);
            translate([(W - CABLE) / 2, -LF - 1, T]) cube([CABLE, LIP_W + CHIN + 2, LIP_H + 1]);
        }
    }
    // the pins' bores, teardrops pointing up like the pins' own ends
    for (r = [[0, K1], [K2, W]]) translate([0, 0, AF]) along_x(r[0] - 1, r[1] + 1) tear2d(PR + CLR_KEY);
}

// ---- the back plate, as printed: outer face on the bed, the hinge along x at (0, AR) ----------
// A tongue is an upright blade beside the bore, on the side away from the plate: it
// stands in a window over the bore's outer half, freed along its length and across its
// free end, so it bends sideways and every cut prints as a wall. The first tongues lay
// under the bore over a 1 mm gap, and the slicer propped the gap's roof (2026-11-04).
RB = PR + CLR_RUN;          // the bore's radius, where the blade's inner face stands
module tongue_cut(x_fixed, dir) let (x_free = x_fixed + dir * TONGUE_L, x0 = min(x_fixed, x_free)) {
    // a window over the bore's outer half for the blade to stand in: a narrow slot
    // between blade and bore left knife-edged wedges where it met the round
    translate([x0, -0.01, -1]) cube([TONGUE_L, RB + 0.01, AR + RK + 2]);
    // outside the blade, nothing: a strip of barrel left there tapered to 0.02 where
    // the barrel's round met it (2026-11-04)
    translate([x0, RB + BLADE_T, -1]) cube([TONGUE_L, RK, AR + RK + 2]);
    translate([dir > 0 ? x_free - 0.01 : x_free - SLOT + 0.01, -0.01, -1]) cube([SLOT, RB + BLADE_T + 0.02, AR + RK + 2]);
}
// the ridge on the blade's inner face at the axis's height, its tip at R_FREE from the axis.
// Its top face is flat and lies along the radius: the ratchet's locking face. Its lower
// flank is 37 deg off upright, so it prints off the blade, and that is the slope the
// notches' ramps match
module ridge(x_fixed, dir) let (x_free = x_fixed + dir * TONGUE_L, lo = (RB - R_FREE) / tan(37))
    translate([dir > 0 ? x_free - RIDGE_L : x_free, 0, 0]) along_x(0, RIDGE_L)
        polygon([[RB + 0.5, AR - lo - 0.3], [RB, AR - lo], [R_FREE, AR], [RB + 0.5, AR]]);
XB0 = K1 + XG; XB1 = K2 - XG;           // the back plate's barrel
END = 1.2 + SLOT;           // a tongue's free end stops this short of the barrel's end: 1.2 of wall
module back() difference() {
    union() {
        translate([0, -LR, 0]) cube([W, LR - CUT_R, T]);
        translate([XB0, -LR, 0]) cube([XB1 - XB0, LR, T]);
        along_x(XB0, XB1) barrel2d(AR);
    }
    translate([0, 0, AR]) along_x(XB0 - 1, XB1 + 1) tear2d(PR + CLR_RUN);
    // a tongue from each end's middle toward that end, its ridge against that end's pin
    tongue_cut(XB0 + END + TONGUE_L, -1);
    tongue_cut(XB1 - END - TONGUE_L, 1);
    // the mark on the inner face, which prints facing up: engraved into the face on the
    // bed, its letters' roofs were bridges the slicer propped (2026-11-04). The library
    // draws it to read from below; mirrored back in y it reads from above, hinge at the top
    translate([W / 2, -LR / 2, T]) mirror([0, 0, 1]) mirror([0, 1, 0]) obc_engrave(7, depth = 0.8, inset = 0.15, ridges = false);
}
module back_ridges() { ridge(XB0 + END + TONGUE_L, -1); ridge(XB1 - END - TONGUE_L, 1); }
module back_full() union() { back(); back_ridges(); }

// ---- a pin -------------------------------------------------------------------------------------
// Drawn along its own z from the front plate's barrel end (z = 0) with the button PRESSED,
// its head against the barrel; its section's (x, y) are the front plate's (y, z). At rest
// it stands REST further out. Along it: the head (the button), the key (a teardrop, in the
// front plate's barrel), then round, in the back plate's barrel:
//   r = PR, then a cone down to CREST (the release ramp), the ratchet band (crest CREST with
//   a notch to ROOT at every stop), a wall back up to PR (keeps it in), and a chamfered tip.
// Printed standing on its head, so every narrowing going up is a free surface and every
// widening rises at 37 deg off upright.
HEAD = 2.4; HEAD_R = PR + 2.0;  // the button: the key's teardrop grown 2
PIN_KEY = K1 + 0.2;         // the keyed length, pressed: it stops 0.2 short of the back barrel
RX0 = XB0 + END;            // the ridge, along the hinge from the barrel's end (front frame)
CONE = 0.6;                 // the release ramp's rise per mm along the pin (31 deg): more than
                            // PLA's friction on PLA, so the blade pushes the pin back out
PRESS_R = 3.7;              // pressed, the ridge's edge sits this far out on the cone: 0.3 clear
                            // of the crests, and still on the slope, so it springs back
B0 = RX0 + (PRESS_R - CREST) / CONE;        // the ratchet band's start (pin frame)
RAMP_IN = (CREST - ROOT) / CONE;            // a notch's floor ramps in over this from B0
REST = B0 + RAMP_IN - RX0;  // how far the pin stands out at rest: the ridge on full-depth floor
B1 = B0 + RAMP_IN + RIDGE_L + 0.3;          // the band's end
WALL = (PR - CREST) / tan(37);              // the wall back up to PR, 37 deg off upright
CEIL = (PR - ROOT) / tan(37);               // a notch's top end climbs at 37 deg off upright all
                            // the way out to PR: stopped at the crest, it ended under the wall
                            // in a flat ceiling the slicer propped (1,216 moves, 2026-11-06)
TIP0 = B1 + WALL + 1.2;     // the round tip, then its chamfer
TIP = TIP0 + 1.0;
// a notch's section at stop a: the radial face at angle a, the floor at ROOT, the ramp back
// up to the crest along the ridge's flank (37 deg off the tangent)
module notch2d(a) rotate(a) polygon([[ROOT - 0.001, 0], [PR + 1, 0], [PR + 1, -(PR + 1 - ROOT) / tan(37)]]);
module pin_local() {
    translate([0, 0, -HEAD]) linear_extrude(HEAD) offset(r = HEAD_R - PR) tear2d(PR);
    linear_extrude(PIN_KEY) tear2d(PR);
    difference() {
        rotate_extrude($fn = 96) polygon([[0, PIN_KEY - 0.01], [PR, PIN_KEY - 0.01], [PR, B0 - (PR - CREST) / CONE],
            [CREST, B0], [CREST, B1], [PR, B1 + WALL], [PR, TIP0], [PR - 0.75, TIP], [0, TIP]]);
        // the notches: their angular profile, cut only where the floor envelope allows
        intersection() {
            translate([0, 0, B0 - 0.01]) linear_extrude(B1 + CEIL - B0 + 0.02) for (a = STOPS) notch2d(a);
            rotate_extrude($fn = 96) polygon([[CREST, B0], [ROOT, B0 + RAMP_IN], [ROOT, B1], [PR + 0.01, B1 + CEIL],
                                               [PR + 2, B1 + CEIL], [PR + 2, B0]]);
        }
    }
}
module pin_x(shift = 0) translate([shift, 0, 0]) rotate([90, 0, 90]) pin_local();
// The notches: at opening A the back plate's ridge points along (cos A, sin A) from the
// axis in the front plate's (y, z), its flat top face on the larger-angle side: opening
// (A growing) drives that face into the notch's radial face and stops; closing slides its
// flank up the notch's ramp. notch2d draws them in the pin's own section, whose (x, y) are
// the front plate's (y, z).

// ---- in place, in the front plate's frame ------------------------------------------------------
module front_use() front();
// the back plate: folded, its inner face on the front's inner face; open by a about the axis
module back_use(a = ANG) translate([0, 0, AF]) rotate([a, 0, 0]) translate([0, 0, -AR]) back_full();
// press = 0 at rest, 1 with both buttons pressed in
module pins_use(press = 0) translate([0, 0, AF]) {
    pin_x(-REST * (1 - press));
    translate([W, 0, 0]) mirror([1, 0, 0]) pin_x(-REST * (1 - press));
}

// ---- as printed --------------------------------------------------------------------------------
module pin_print() translate([0, 0, HEAD]) pin_local();

assert(AF - (PR + CLR_KEY) >= 1.2, "the wall under the front plate's bores is under 1.2");
assert(RK - (RB + BLADE_T + SLOT) >= 1.2, "the barrel's wall outside the blade is under 1.2");
assert(2 * TIP + 0.4 <= W, "the pins, pressed, are longer than the hinge");
assert(B0 - (PR - CREST) / CONE > PIN_KEY, "the release cone runs into the key");

FRONT_C = "#B79CE0"; BACK_C = "#F4F1EA"; PIN_C = "#F6A6C1";
if (part == "front") front();
else if (part == "back") back_full();
else if (part == "pin") pin_print();
else if (part == "front_use") front_use();
else if (part == "back_use") back_use(ANG);
else if (part == "back_use0") back_use(0);
else if (part == "pins_use") pins_use(0);
else if (part == "pins_pressed") pins_use(1);
else if (part == "all") { color(FRONT_C) front_use(); color(BACK_C) back_use(ANG); color(PIN_C) pins_use(); }
echo("RK", RK, "AF", AF, "AR", AR, "CUT_F", CUT_F, "CUT_R", CUT_R, "PIN_KEY", PIN_KEY, "LF", LF, "LR", LR,
     "REST", REST, "B0", B0, "B1", B1, "TIP", TIP, "RX0", RX0, "HEAD", HEAD, "CEIL", CEIL, "ROOT", ROOT);
