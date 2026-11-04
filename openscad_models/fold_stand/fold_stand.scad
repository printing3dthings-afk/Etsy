// Fold Stand: a phone stand that clicks to five angles and folds flat (2026-11-04).
// Scott's pick, form A of four: "two plates on a clicking hinge. It sets at
// five angles and folds flat for a bag or pocket."
//
// Practice in detent hinges. It stands as an A: the front plate carries the
// phone on a lip at its foot, the back plate is the leg, and they meet at a
// hinge barrel along the top. Two pins, one pushed in from each side, are
// keyed to the front plate; inside the back plate's barrel two tongues press
// a ridge each onto its pin, and the ridge clicks into a notch at each angle:
// folded, and five open. On a table an A is held by the friction under its
// feet; the clicks set the angle and hold it, and hold it folded in a bag.
//
// Every part prints flat or upright with nothing hanging: the bores are
// teardrops in section, the pins print standing on their heads, and the
// tongues are upright blades cut free by upright slots.
//
//   part = front | back | pin (as printed) | front_use | back_use(at ANG) |
//          pins_use | all
use <../brand/obc_mark.scad>

part = "all";
ANG = 25;                   // the opening shown in "all" and back_use
$fn = 96;

// ---- sizes -------------------------------------------------------------------------------------
CLR_KEY = 0.05;             // a pin in the front plate's barrel: a press fit
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
STOPS = [0, 13, 25, 37, 49, 61];        // the openings it clicks at: folded, then five that
                                        // lean a phone at about 80, 74, 68, 62 and 56 deg
NOTCH = 0.35;               // the notches' depth, 90 deg V: 10 deg wide on the pin, 12 apart
BLADE_T = 2.0; TONGUE_L = 12; SLOT = 0.8;
RIDGE_L = 4;
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
// the ridge on the blade's inner face at the axis's height, standing NOTCH into the
// bore; its lower flank 37 deg off upright so it prints off the wall
module ridge(x_fixed, dir) let (x_free = x_fixed + dir * TONGUE_L, lo = NOTCH / tan(37))
    translate([dir > 0 ? x_free - RIDGE_L : x_free, 0, 0]) along_x(0, RIDGE_L)
        polygon([[RB + 0.5, AR - lo - 0.3], [RB, AR - lo], [RB - NOTCH, AR], [RB, AR + NOTCH], [RB + 0.5, AR + NOTCH + 0.3]]);
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
    // bed, its letters' roofs were bridges the slicer propped (2026-11-04)
    translate([W / 2, -LR / 2, T]) mirror([0, 0, 1]) mirror([1, 0, 0]) obc_engrave(7, depth = 0.8, inset = 0.15, ridges = false);
}
module back_ridges() { ridge(XB0 + END + TONGUE_L, -1); ridge(XB1 - END - TONGUE_L, 1); }
module back_full() union() { back(); back_ridges(); }

// ---- a pin, in place in (y, z) about the axis: teardrop where the front plate holds it, round
// with a notch for every stop where the back plate turns on it ------------------------------------
HEAD = 2; HEAD_R = PR + 1.4;     // the head: the key's teardrop grown 1.4, so the key stands on it
PIN_KEY = K1 + 0.2;         // its keyed length, in the front plate's barrel
PIN_RUN = (W / 2 - 0.2) - PIN_KEY;      // and its round length, to the middle
module notch2d() for (a = STOPS) rotate(a) translate([PR, 0]) rotate(45) square(NOTCH * sqrt(2), center = true);
module pin_x() {            // along +x from its head at x = -HEAD
    translate([-HEAD, 0, 0]) rotate([90, 0, 90]) linear_extrude(HEAD) offset(r = HEAD_R - PR) tear2d(PR);
    rotate([90, 0, 90]) linear_extrude(PIN_KEY) tear2d(PR);
    translate([PIN_KEY, 0, 0]) rotate([90, 0, 90]) linear_extrude(PIN_RUN) difference() { circle(r = PR); notch2d(); }
}
// The notches: at opening A the back plate's ridge points along (cos A, sin A) from the
// axis in the front plate's (y, z): it faces +y in the back plate, turned A about x.
// notch2d draws them in the pin's own section, whose (x, y) are the front plate's (y, z).

// ---- in place, in the front plate's frame ------------------------------------------------------
module front_use() front();
// the back plate: folded, its inner face on the front's inner face; open by a about the axis
module back_use(a = ANG) translate([0, 0, AF]) rotate([a, 0, 0]) translate([0, 0, -AR]) back_full();
module pins_use() translate([0, 0, AF]) {
    pin_x();
    translate([W, 0, 0]) mirror([1, 0, 0]) pin_x();
}

// ---- as printed --------------------------------------------------------------------------------
module pin_print() translate([0, 0, HEAD]) rotate([0, -90, 0]) rotate([0, 0, 0]) pin_x();

assert(AF - (PR + CLR_KEY) >= 1.2, "the wall under the front plate's bores is under 1.2");
assert(RK - (RB + BLADE_T + SLOT) >= 1.2, "the barrel's wall outside the blade is under 1.2");
assert(2 * PIN_RUN + 0.4 + 2 * PIN_KEY <= W + 0.01, "the pins are longer than the hinge");

FRONT_C = "#B79CE0"; BACK_C = "#F4F1EA"; PIN_C = "#F6A6C1";
if (part == "front") front();
else if (part == "back") back_full();
else if (part == "pin") pin_print();
else if (part == "front_use") front_use();
else if (part == "back_use") back_use(ANG);
else if (part == "back_use0") back_use(0);
else if (part == "pins_use") pins_use();
else if (part == "all") { color(FRONT_C) front_use(); color(BACK_C) back_use(ANG); color(PIN_C) pins_use(); }
echo("RK", RK, "AF", AF, "AR", AR, "CUT_F", CUT_F, "CUT_R", CUT_R, "PIN_KEY", PIN_KEY, "PIN_RUN", PIN_RUN, "LF", LF, "LR", LR);
