// Pocket Pebble: a smooth pebble that opens on a hinge, for rings, earrings or a day's
// pills (2026-11-04). Scott's pick, form D of four: "a smooth pocket pebble shape for
// rings, earrings or pills; opens with one thumb."
//
// Practice in a box hinge and a snap latch. Two shells meet at a seam: the base prints
// the right way up and the lid upside down, each rising from a flat face at no more
// than 37 deg off upright and turning upright at the seam, so the two meet in one
// smooth curve. At the back a hinge of three knuckles turns on two pins pushed in from
// the ends, keyed by their teardrop section in the base's knuckles. At the front a
// tongue hangs from inside the lid; a bump on it snaps under a lip inside the base, so
// it clicks shut and stays shut in a pocket, and a thumb in the scoop under the lid's
// front edge flicks it open.
//
//   part = base | lid (as printed) | pin (as printed) | base_use | lid_use(at ANG) |
//          pins_use | all
use <../brand/obc_mark.scad>

part = "all";
ANG = 0;                    // the lid's opening in lid_use and all
$fn = 96;

// ---- the pebble -------------------------------------------------------------------------------
A = 29; B = 20;             // half its length and width at the seam: 58 x 40
EXP = 2.5;                  // the plan's superellipse: rounder than a box, flatter at the back
                            // than an ellipse, so the hinge has a straight run to sit on
HB = 12; HL = 10;           // the base and lid heights: 22 closed
SHRINK = 0.16;              // the flat faces are (1 - SHRINK) of the seam's plan: the walls
                            // lean in at most 31 deg (base) and 36 deg (lid), turning upright
                            // at the seam
WALL = 1.7;                 // across, so 1.3 normal to the wall where it leans most
FLOOR = 2.0;                // the base's floor and the lid's top: 1.4 under the mark
NS = 24;                    // slices up each shell
// ---- the hinge --------------------------------------------------------------------------------
PR = 1.75;                  // a pin's radius
CLR_KEY = 0.05;             // a pin in the base's knuckles: a press fit
CLR_RUN = 0.15;             // and in the lid's: it turns
RK = 4.6;                   // a knuckle's radius: 1.4 of wall past the bore's teardrop point
AY = B + 0.6;               // the axis: on the seam, just behind the back, so the lid's back
                            // swings up and out, clear of the base
K0 = 4.0;                   // the lid's knuckle: x -K0..K0
XG = 0.4;                   // between knuckles
K1 = 12;                    // the base's knuckles: x K0+XG..K1, each side
NCLR = 0.4;                 // round each knuckle, in the other shell
// ---- the latch --------------------------------------------------------------------------------
PAD_X = 8;                  // the base's front wall is thickened inside, x -PAD_X..PAD_X,
YP = -B + 3.6;              // to this face: room for the thumb scoop outside
LIP = 0.9;                  // the lip on the pad's face, under which the bump catches
LIP_TOP = HB - 1.5;
TONGUE_W = 10; TONGUE_T = 1.6;
TGAP = 0.2;                 // the lip's tip to the tongue
BUMP = 0.8;                 // the bump on the tongue's front, under the lip when shut
CATCH = 0.25;               // the bump's catch face, this far under the lip's underside
TIP_Z = 7.0;                // the tongue's tip
SCOOP = [9, 1.6, 5];        // the thumb scoop's half-sizes: x, depth, z

// ---- the plan ---------------------------------------------------------------------------------
function sgnp(v, e) = v < 0 ? -pow(-v, e) : pow(v, e);
module plan2d(s = 1) scale([s, s])
    polygon([for (i = [0 : 179]) let (t = i * 2) [A * sgnp(cos(t), 2 / EXP), B * sgnp(sin(t), 2 / EXP)]]);
// the plan's scale up each shell, z measured from the seam: the base below, the lid above
function sb(z) = 1 - SHRINK + SHRINK * sin(90 * (HB + z) / HB);     // z in -HB..0
function sl(z) = 1 - SHRINK * (1 - cos(90 * z / HL));               // z in 0..HL
module slice(z, s, o = 0) translate([0, 0, z]) linear_extrude(0.01) offset(delta = -o) plan2d(s);

// ---- the shells, in place: the seam at z = HB ---------------------------------------------------
module base_outer() hull() for (i = [0 : NS]) let (z = -HB + HB * i / NS) slice(HB + z - (i == NS ? 0.01 : 0), sb(z));
module base_cavity() hull() {
    for (i = [0 : NS]) let (z = -HB + FLOOR + (HB - FLOOR) * i / NS) slice(HB + z, sb(z), WALL);
    slice(HB + 1, 1, WALL);
}
module lid_outer() hull() for (i = [0 : NS]) let (z = HL * i / NS) slice(HB + z - (i == NS ? 0.01 : 0), sl(z));
module lid_cavity() hull() {
    slice(HB - 1, 1, WALL);
    for (i = [0 : NS]) let (z = (HL - FLOOR) * i / NS) slice(HB + z, sl(z), WALL);
}

// ---- the hinge ---------------------------------------------------------------------------------
// a teardrop in (y, z), its point up (+z): the knuckles' gussets and the bores
module tear2d(r) hull() { circle(r = r); translate([0, r / sin(37)]) circle(r = 0.01); }
module along_x(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
module on_axis() translate([0, AY, HB]) children();
// a knuckle, and a buttress under it to its own shell's flat face, so it prints standing
// on the bed: the base's down to its foot, the lid's up to its top (its bed). The
// buttress's outer face is the 36 deg tangent to the knuckle; its foot reaches back in
// under the shell. A teardrop under the knuckle first left its point hanging in the air
// 2.4 out from the shell, which leans in below the seam faster than 37 deg allows
// (2026-11-04)
BUTT = 36;
module knuckle(x0, x1, up) let (zf = up ? HB + HL - 0.01 : 0, h = up ? HL : HB)
    along_x(x0, x1) hull() {
        translate([AY, HB]) circle(r = RK);
        translate([AY - RK - 1.5, zf]) square([RK + 1.5 + RK / cos(BUTT) - h * tan(BUTT), 0.01]);
    }
// the bores, their points up as each part prints: the base's up, the lid's down
module bore(x0, x1, r, up) on_axis() along_x(x0, x1) rotate(up ? 0 : 180) tear2d(r);
module notch(x0, x1) on_axis() along_x(x0, x1) circle(r = RK + NCLR);

// ---- the latch ---------------------------------------------------------------------------------
YT = YP + LIP + TGAP;       // the tongue's front face
LIP_LO = LIP_TOP - LIP - LIP / tan(37);     // the lip's underside meets the pad here
// the lip in (y, z): a 45 deg lead-in on top, its underside 37 deg off upright
module lip2d() polygon([[YP - 0.01, LIP_TOP], [YP + LIP, LIP_TOP - LIP], [YP - 0.01, LIP_LO]]);
// the bump in (y, z): its catch face parallel to the lip's underside, CATCH under it;
// then a short upright tip and a 45 deg face back to the tongue
function under_lip(y) = LIP_TOP - LIP + (y - (YP + LIP)) * (LIP / tan(37)) / LIP - CATCH;
module bump2d() let (y1 = YT - BUMP, zt = under_lip(y1))
    polygon([[YT + 0.01, under_lip(YT)], [y1, zt], [y1, zt - 0.4], [YT + 0.01, zt - 0.4 - BUMP]]);
module tongue() {
    translate([-TONGUE_W / 2, YT, TIP_Z]) cube([TONGUE_W, TONGUE_T, HB + HL - FLOOR - TIP_Z + 0.5]);
    along_x(-TONGUE_W / 2, TONGUE_W / 2) bump2d();
}

// ---- the parts, in place -------------------------------------------------------------------------
module base_use() difference() {
    union() {
        difference() {
            base_outer();
            difference() {
                base_cavity();
                // the pad behind the scoop
                translate([-PAD_X, -B - 1, 0]) cube([2 * PAD_X, YP + B + 1, HB + 2]);
            }
            notch(-K0 - XG, K0 + XG);
            // the thumb scoop, under the lid's front edge
            translate([0, -B, HB]) scale(SCOOP) sphere(r = 1, $fn = 64);
        }
        for (s = [-1, 1]) knuckle(s > 0 ? K0 + XG : -K1, s > 0 ? K1 : -K0 - XG, false);
        intersection() {
            along_x(-PAD_X, PAD_X) lip2d();
            base_outer();
        }
    }
    bore(-K1 - 1, -K0 - XG + 0.01, PR + CLR_KEY, true);
    bore(K0 + XG - 0.01, K1 + 1, PR + CLR_KEY, true);
    // the mark on the floor inside, which prints facing up. The library draws it to read
    // from below; mirrored back in y it reads from above, the hinge at the top
    translate([0, -1, FLOOR]) mirror([0, 0, 1]) mirror([0, 1, 0]) obc_engrave(6, depth = 0.6, inset = 0.15, ridges = false);
}
module lid_closed() difference() {
    union() {
        difference() {
            lid_outer();
            lid_cavity();
            for (s = [-1, 1]) notch(s > 0 ? K0 : -K1 - 1, s > 0 ? K1 + 1 : -K0);
        }
        knuckle(-K0, K0, true);
        tongue();
    }
    bore(-K0 - 1, K0 + 1, PR + CLR_RUN, false);
}
// open by a about the axis: the front lifts
module lid_use(a = ANG) translate([0, AY, HB]) rotate([-a, 0, 0]) translate([0, -AY, -HB]) lid_closed();

// ---- a pin: a teardrop key in a base knuckle, round in the lid's. No head: a head
// outside the knuckle ran into the shell walls, which curve in past the hinge. Pushed in
// from the knuckle's outer end, flush, it stops where the key's end meets the lid's
// knuckle across the gap, its point against the face round the lid's bore ----------------
PIN_KEY = K1 - (K0 + XG) + 0.1;         // to 0.1 into the gap: clear of the lid's bore
PIN_RUN = K0 + XG - 0.1 - 0.2;          // and round to 0.2 short of the middle
// the key's point capped where it narrows to 1.2: a sharp point is under one bead. The pin
// prints standing, so the cap is a wall, not a roof
KEY_CAP = PR / sin(37) - 0.6 / tan(37);
module key2d() intersection() { tear2d(PR); translate([-PR, -PR]) square([2 * PR, PR + KEY_CAP]); }
module pin_x() {            // along +x from its outer end at x = 0
    rotate([90, 0, 90]) linear_extrude(PIN_KEY) key2d();
    translate([PIN_KEY, 0, 0]) rotate([90, 0, 90]) linear_extrude(PIN_RUN) circle(r = PR);
}
module pins_use() on_axis() {
    translate([-K1, 0, 0]) pin_x();
    translate([K1, 0, 0]) mirror([1, 0, 0]) pin_x();
}

// ---- as printed -------------------------------------------------------------------------------
module lid_print() translate([0, 0, HB + HL]) rotate([180, 0, 0]) lid_closed();
module pin_print() rotate([0, -90, 0]) pin_x();      // standing on its keyed end

assert(RK - (PR + CLR_RUN) / sin(37) >= 1.2, "the knuckle's wall over the bore's point is under 1.2");
assert(YT + TONGUE_T < -B + 3.6 + 6, "the tongue is not near the front");

WHITE = "#F4F1EA"; LILAC = "#B79CE0"; PINK = "#F6A6C1";
if (part == "base" || part == "base_use") base_use();
else if (part == "lid") lid_print();
else if (part == "lid_use") lid_use(ANG);
else if (part == "lid_use0") lid_use(0);
else if (part == "pin") pin_print();
else if (part == "pins_use") pins_use();
else if (part == "all") { color(WHITE) base_use(); color(LILAC) lid_use(ANG); color(PINK) pins_use(); }
echo("AY", AY, "HB", HB, "HL", HL, "YP", YP, "YT", YT, "LIP_TOP", LIP_TOP, "LIP_LO", LIP_LO, "TIP_Z", TIP_Z, "PIN_KEY", PIN_KEY, "PIN_RUN", PIN_RUN);
