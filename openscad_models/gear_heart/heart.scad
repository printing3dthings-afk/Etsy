// Gear Heart (2026-11-13): Scott's form 9A, "the heart's outline is made of meshing
// gears, all of them turning together from a knob in the middle."
//
// Fourteen gears ring a heart-shaped backplate, each meshing with its neighbours, and
// a sixteenth-tooth centre gear carries a heart-shaped knob and drives the ring through
// the top gear. The gears press onto split snap posts, the ones on the test print:
// +0.20 mm on every centre distance, Scott's pick ("Number 1", 2026-11-13).
//
// The layout (layout.json, from gear_budget.py): the heart curve is scaled until the
// loop of meshing distances closes, and the bottom gear sits 1.59 mm up the axis so
// the loop's TEETH close too (at the curve's own point they were 2.10 mm off, and the
// ring would have locked). Each gear's phase is the angle of one tooth with every mesh
// centred; heart_data.scad carries them.
//
// Prints in two parts:
//   part = "plate"  the backplate with its posts, flat
//          "gears"  all fifteen gears, flat, laid out on one plate
//          "assembled" (with turn, deg of the knob gear) for renders and the fit check
//          "plate_only" / "gear" (with idx, in its assembled pose at turn) for the check

include <gear_lib.scad>
include <heart_data.scad>

part = "assembled";
turn = 0;
idx = 0;
$fn = 64;

GEAR_T  = 6.0;
PLATE_T = 8.0;     // the posts rise from pockets 6.5 deep (gear_budget.py)
BASE_T  = 3.0;     // the plate between the bosses
BOSS_R  = bore_d() / 2 + 2.6;   // under each gear: carries the washer and the post's pocket
RIM_IN  = 1.2;     // the rim stands this far outside the loop gears' tips
RIM_W   = 2.4;
RIM_H   = 2.5;     // above the base: well under the gears (their undersides are at 9)

function g(i) = GEARS[i];
function name(i) = g(i)[0];
function zt(i) = g(i)[1];
function at(i) = g(i)[2];
function ph(i) = g(i)[3];
KNOB = len(GEARS) - 1;
// every gear turns with the knob, at its ratio and the opposite way to each neighbour
// round the loop: the knob turns the top gear, which turns the ring
function sign_of(i) = i == KNOB ? 1 : (search(i, LOOP)[0] % 2 == 0 ? -1 : 1);
function spin(i, t) = sign_of(i) * t * zt(KNOB) / zt(i);

// ---- the backplate ----
module outline2d() offset(r = 3) offset(r = -3) union() {
    polygon([for (k = LOOP) at(k)]);
    for (k = LOOP) translate(at(k)) circle(r = g_ra(MOD, zt(k)) + RIM_IN + RIM_W);
}
module plate() difference() {
    union() {
        linear_extrude(BASE_T) outline2d();
        // a low rim round the edge, outside every gear's tips
        linear_extrude(BASE_T + RIM_H) difference() {
            outline2d();
            offset(delta = -RIM_W) outline2d();
        }
        for (i = [0 : len(GEARS) - 1]) translate(at(i)) {
            cylinder(r = BOSS_R, h = PLATE_T);
            post(PLATE_T, GEAR_T);
            washer(PLATE_T);
        }
    }
    for (i = [0 : len(GEARS) - 1]) translate(at(i)) difference() { post_pocket(PLATE_T); post(PLATE_T, GEAR_T); }
}

// ---- the gears ----
// a small heart, pointing down (-y), w across
module heart2d(w) scale(w / 20) translate([0, 2]) union() {
    for (s = [-1, 1]) translate([s * 5, 2]) circle(r = 5.4);
    polygon([[-10.2, 0.6], [10.2, 0.6], [0, -12]]);
}
// the top gear (20 teeth) has room for heart cut-outs in its web; the 16s and 12s don't
// (gear_lib's rule: a 2 mm web each side of a hole)
module heart_gear(z) {
    if (z >= 20) difference() {
        gear(MOD, z, GEAR_T, bore_d(), holes = 0);
        // each heart's cusp left a thin spike of web between its lobes (gate 0.83): closed off
        for (k = [0 : 3]) rotate(45 + k * 90) translate([0, 8.6, -1]) rotate(180) linear_extrude(GEAR_T + 2)
            offset(r = -0.9) offset(r = 0.9) heart2d(5.6);
    }
    else gear(MOD, z, GEAR_T, bore_d());
}
// The knob: a round, ribbed grip on the centre gear with a raised heart on its top.
// It has to clear the post's head, which stands POST_TOP above the gear: a 10.7 mm hole
// in a 17 mm heart broke through its narrow lower half (gate min wall 0.83). So the
// grip is round, 18 across (inside the 9.5 the top gear's tips leave), the hole ends in
// a 37 deg pointed roof (no bridge), and the heart sits on the solid top.
// 2026-11-13. The top gear's tips come to 10.7 from the knob's centre, level with the
// knob's underside: a 24 mm heart knob swept over them.
KNOB_R = 9.0;
HOLE_R = bore_d() / 2 + BARB + 0.6;               // round the post's barb
POST_TOP = let (zc = WASHER + AX_PLAY, rb = bore_d() / 2 + BARB, zb = zc + BARB / tan(UNDER))
           zb + (rb - (X_OUT - 0.2)) / tan(LEAD) - WASHER;   // the post's top above the gear's top
ROOF = HOLE_R / tan(37);
KNOB_H = POST_TOP + 0.6 + ROOF + 1.6;
RIBS = 16;
module knob() translate([0, 0, GEAR_T - 0.01]) difference() {
    union() {
        cylinder(r = KNOB_R, h = KNOB_H, $fn = 96);
        translate([0, 0, KNOB_H - 0.01]) linear_extrude(1.4) heart2d(13);      // the heart on top
    }
    // the post's room: up past its head, then a pointed roof
    translate([0, 0, -1]) cylinder(r = HOLE_R, h = POST_TOP + 0.6 + 1, $fn = 64);
    translate([0, 0, POST_TOP + 0.6 - 0.01]) cylinder(r1 = HOLE_R, r2 = 0, h = ROOF, $fn = 64);
    // grip ribs: grooves 0.8 wide round the side, run out through the top (stopped short,
    // each groove's flat top was a ceiling the gate's slicer propped: 6,124 support moves)
    for (k = [0 : RIBS - 1]) rotate(k * 360 / RIBS) translate([KNOB_R - 0.6, -0.4, 0.8]) cube([2, 0.8, KNOB_H + 2]);
}
module gear_part(i) { heart_gear(zt(i)); if (i == KNOB) knob(); }

module gear_posed(i, t) translate([at(i)[0], at(i)[1], PLATE_T + WASHER]) rotate(ph(i) + spin(i, t)) gear_part(i);

// all fifteen gears, flat, for printing (a 4 x 4 grid)
module gears_plate() for (i = [0 : len(GEARS) - 1])
    translate([(i % 4) * 36, floor(i / 4) * 36, 0]) gear_part(i);

if (part == "plate" || part == "plate_only") plate();
else if (part == "gears") gears_plate();
else if (part == "gear") gear_posed(idx, turn);
else if (part == "gear_local") gear_part(idx);
else if (part == "gears_posed") for (i = [0 : len(GEARS) - 1]) gear_posed(i, turn);
else { plate(); for (i = [0 : len(GEARS) - 1]) gear_posed(i, turn); }
