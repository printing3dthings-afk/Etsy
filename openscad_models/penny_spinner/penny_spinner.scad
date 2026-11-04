// Penny Spinner: a spinning top weighted with pennies (2026-11-04).
// Scott's pick, form 4 of five: "a low, heavy-rimmed desk top with snap-in
// pockets round the rim for US pennies. The extra weight at the edge makes it
// spin for longer."
//
// Eight round petals round the rim, each a pocket for two pennies; a window in
// each petal's top shows its copper. The pennies are the weight, and they sit
// as far out as the top goes, where weight does the most for a spin.
//
// Three prints, one colour each, no supports, no glue:
//   crown  the petals and their pockets, the right way up. The pockets open
//          underneath and narrow at 34 deg into the windows, so the pennies
//          sit in a bevelled setting and cannot come out of the top.
//   base   closes the pockets from below and carries the tip. It prints upside
//          down, so the tip is the last thing printed. The OBC mark is on a flat
//          ring underneath.
//   stem   the grip you twirl, on a hex shaft that drops through a hex hole in
//          the crown and snaps into the base. The hex keys both to it, so a
//          twirl turns the whole top. It prints standing on its grip.
// To change the pennies, hold the base and pull the stem out.
//
// The first version joined crown and base with a printed threaded stud. A
// stud that small is nearly all thread, and every tooth's crest is under the
// gate's 1.2 mm wall (2026-11-04). The snap pin is the gift box's, which
// passes: ../multipart/snap_lib.scad.
//
//   part = crown | base | stem (as printed) | crown_use | base_use | stem_use |
//          coins (16 pennies, in place) | all
include <../multipart/snap_lib.scad>
// The stem's one pin is bigger than the gift box's: 4.4 across, so each prong
// is 1.7 thick, with a 4.5 slot to keep the click as soft (about 1.6% strain).
// At 3.4 the prongs were most of the small stem and 1.7% of its walls read
// under 1.2, failing the gate (2026-11-04). These override the library's.
SP_D = 4.4; SP_SLIT_IN = 4.5;
use <../brand/obc_mark.scad>

part = "all";
$fn = 96;

// ---- a US penny (US Mint: 0.750 in across, 1.52 mm thick, 2.5 g since 1982) ---------------------
COIN_D = 19.05; COIN_T = 1.52; STACK = 2;
// ---- the pockets -----------------------------------------------------------------------------
N    = 8;                   // pockets, one per petal
PK_R = COIN_D / 2 + 0.3;    // 9.825: a printed hole comes out a little small
PK_H = 3.2;                 // two pennies (3.04) and 0.16 to spare
WIN_R = 7.5;                // the window: 2 mm of lip over the penny's edge
CONE_H = 3.4;               // the pocket narrows to the window over this: 34 deg off upright
WIN_W = 1.2;                // then the window runs straight up this far: run to the top face,
                            // the bevel ended in a knife edge round the window (2026-11-04)
WEB  = 1.6;                 // least wall between two pockets
WALL = 2.0;                 // round each pocket's outer side: the rim takes the knocks
R_P  = ceil(((2 * PK_R + WEB) / (2 * sin(180 / N))) * 10) / 10;   // 27.8, the pockets' centres
PET_R = PK_R + WALL;        // a petal's radius
R_OUT = R_P + PET_R;        // 39.6
T_C  = PK_H + CONE_H + WIN_W; // the crown's rim, 7.8
HUB_R0 = 16; HUB_R1 = 7; HUB_H = 4;     // a low cone from the petals up to the stem
HUB_Z = T_C + HUB_H;                    // the hub's top, where the stem's collar sits
// ---- the stem --------------------------------------------------------------------------------
HX = 8;                     // the shaft, across its flats
HX_C = 0.15;                // clearance all round, in the crown's hole and the base's
COL_R = HUB_R1; COL_H = 1.4;            // the collar on the hub: at 1.0 its rim read as a 1.0 wall
GRIP = 9; GRIP_H = 16;                  // the grip, a hex across its flats
KEY_D = 2.4;                // how far the shaft goes into the base
FR_R = SP_D / 2 + SK_T + 0.3;          // the shaft tapers to the socket's mouth, 2.15
FR_D = (HX / sqrt(3) - FR_R) / tan(37); // over this: its corners 37 deg off upright
THROAT = 1.6;               // the base's socket: the length of its throat
// ---- the base ---------------------------------------------------------------------------------
BAND = 2.0;                 // the base's edge, under the petals
FLAT_R0 = 7; FLAT_R1 = 21; FLAT_Z = -7; // a flat ring underneath, for the mark
TIP_Z = -16; TIP_R = 1.0;   // the tip: a 1 mm round end
PIN_Z = -KEY_D - FR_D;      // where the snap pin starts: the socket's mouth

// the outline: eight petals round a centre, the notches between them rounded
module outline() offset(r = -3) offset(r = 3) union() {
    circle(r = R_P);
    for (i = [0 : N - 1]) rotate(i * 360 / N) translate([R_P, 0]) circle(r = PET_R);
}
// a prism of the outline with its top edge stepped in 0.2 a layer: a chamfer
// on the layer grid prints as drawn
module stepped(h, steps = 4) {
    linear_extrude(h - 0.2 * steps) outline();
    for (s = [1 : steps]) translate([0, 0, h - 0.2 * (steps - s + 1)]) linear_extrude(0.2) offset(delta = -0.2 * s) outline();
}
module hex(af, h) linear_extrude(h) circle(r = af / sqrt(3), $fn = 6);
// the hex shaft's lower end and its taper to the pin, from z = 0 down: across
// flats af, the taper ending at radius r (40 sides, the socket's own)
module key(af, r) {
    translate([0, 0, -KEY_D]) hex(af, KEY_D + 0.01);
    hull() {
        translate([0, 0, -KEY_D]) hex(af, 0.01);
        translate([0, 0, PIN_Z]) cylinder(r = r, h = 0.01, $fn = 40);
    }
}

// ---- the crown, in place: its underside on the base at z = 0 ---------------------------------
module pocket() {
    translate([0, 0, -0.01]) cylinder(r = PK_R, h = PK_H + 0.01);
    translate([0, 0, PK_H - 0.01]) cylinder(r1 = PK_R, r2 = WIN_R, h = CONE_H + 0.02);
    translate([0, 0, PK_H + CONE_H]) cylinder(r = WIN_R, h = WIN_W + 0.01);
}
module crown_use() difference() {
    union() {
        stepped(T_C);
        translate([0, 0, T_C - 0.01]) cylinder(r1 = HUB_R0, r2 = HUB_R1, h = HUB_H + 0.01);
    }
    for (i = [0 : N - 1]) rotate(i * 360 / N) translate([R_P, 0, 0]) pocket();
    translate([0, 0, -1]) hex(HX + 2 * HX_C, HUB_Z + 2);
}

// ---- the base, in place: its top under the crown at z = 0 -------------------------------------
module base_use() difference() {
    difference() {
        intersection() {
            translate([0, 0, TIP_Z - 1]) linear_extrude(-TIP_Z + 1) outline();
            union() {
                rotate_extrude() polygon([[0, 0], [R_OUT + 1, 0], [R_OUT + 1, -BAND], [R_OUT, -BAND],
                                          [FLAT_R1, FLAT_Z], [0, FLAT_Z]]);
                hull() {
                    translate([0, 0, FLAT_Z - 0.01]) cylinder(r = FLAT_R0, h = 0.02);
                    translate([0, 0, TIP_Z + TIP_R]) sphere(r = TIP_R, $fn = 48);
                }
            }
        }
        translate([0, 0, 0.01]) key(HX + 2 * HX_C, FR_R - 0.05);
        translate([0, 0, PIN_Z]) rotate([180, 0, 0]) snap_socket(THROAT);
        // the socket's mouth overlaps the key's end: only touching, the socket
        // came out a sealed void, which clean_parts.py then filled back in as
        // a second body, and the pin sat in solid base (2026-11-04). Its sides
        // step out, never in: a 96-sided end on the socket's 40 put a ring
        // just past 44 deg, and the slicer propped it.
        translate([0, 0, PIN_Z - 0.1]) cylinder(r = FR_R - 0.05, h = 0.2, $fn = 40);
    }
    translate([0, -(FLAT_R0 + FLAT_R1) / 2, FLAT_Z]) obc_engrave(5, depth = 0.6, inset = 0.15, ridges = false);
}

// ---- the stem, in place: its collar on the hub, its shaft down into the base --------------------
module stem_use() difference() {
    union() {
        translate([0, 0, HUB_Z]) cylinder(r = COL_R, h = COL_H);
        // the collar tapers into the grip at 37 deg, so it prints over the grip
        translate([0, 0, HUB_Z + COL_H - 0.01]) hull() {
            cylinder(r = COL_R, h = 0.01);
            translate([0, 0, (COL_R - GRIP / 2) / tan(37)]) hex(GRIP, 0.01);   // 37 deg across the flats
        }
        // the grip, its top chamfered 0.6 at 37 deg (it is the face on the plate)
        translate([0, 0, HUB_Z + COL_H]) hex(GRIP, GRIP_H - 0.8);
        translate([0, 0, HUB_Z + COL_H + GRIP_H - 0.81]) hull() {
            hex(GRIP, 0.01);
            translate([0, 0, 0.8]) hex(GRIP - 1.2, 0.01);
        }
        hex(HX, HUB_Z + 0.01);
        key(HX, FR_R - 0.2);
        translate([0, 0, PIN_Z + 0.01]) rotate([180, 0, 0]) snap_pin(THROAT);
    }
    // the slot runs right through the key's lower end: the library's slot is
    // only the pin's width, and the taper round it left 0.25 slivers bridging
    // the slot's ends, thin walls that also braced the prongs. It runs flat to
    // flat across the hex: at 45 deg it left thin wedges where it met the
    // flats (2026-11-04).
    translate([0, 0, PIN_Z]) rotate([180, 0, 0]) translate([-SP_SLIT / 2, -10, -SP_SLIT_IN]) cube([SP_SLIT, 20, SP_SLIT_IN + 0.01]);
}
STEM_TOP = HUB_Z + COL_H + GRIP_H;

// ---- 16 pennies, in place: two in each pocket, on the base -----------------------------------
module coins() for (i = [0 : N - 1], k = [0 : STACK - 1]) rotate(i * 360 / N)
    translate([R_P, 0, k * COIN_T]) cylinder(d = COIN_D, h = COIN_T);

assert(PIN_Z - socket_top(THROAT) > TIP_Z + 3, "the base's socket comes too near the tip");
assert(STACK * COIN_T < PK_H, "the pennies do not fit their pockets");

TEAL = "#3B8E8A"; CREAM = "#F4F1EA"; COPPER = "#B87333";
if (part == "crown") crown_use();
else if (part == "base") mirror([0, 0, 1]) base_use();
else if (part == "stem") translate([0, 0, STEM_TOP]) mirror([0, 0, 1]) stem_use();
else if (part == "crown_use") crown_use();
else if (part == "base_use") base_use();
else if (part == "stem_use") stem_use();
else if (part == "coins") coins();
else if (part == "all") {
    color(TEAL) crown_use();
    color(CREAM) { base_use(); stem_use(); }
    color(COPPER) coins();
}
echo("R_P", R_P, "R_OUT", R_OUT, "T_C", T_C, "FR_D", FR_D, "PIN_Z", PIN_Z, "STEM_TOP", STEM_TOP);
