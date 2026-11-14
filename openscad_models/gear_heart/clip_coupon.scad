// Gear Heart clips v2: the test print (2026-11-14, Brief E). Scott printed the whole heart
// and one of its snap posts snapped. These are the new axle pins, at the heart's real size,
// to print and test before the heart is rebuilt round them (mechanism handbook, section 7).
//
// A bar with three bosses (the heart plate's: 8 tall, a washer, a hole, a pocket for the
// pin's head underneath), three pins and three of the heart's 12-tooth gears, all on one
// plate. The pins differ only in how far their barbs catch over the gear:
//   1 notch 0.45 mm, 2 notches 0.55 (the design value), 3 notches 0.65.
// Strain, push-on force and engagement for each: clip_budget.py.
//
//   part = "all" (the print plate) | "base" | "pins" | "gears" | "assembled" (review)
//          | "gate_skip" (the gate's skip region, not printed)

include <pin_lib.scad>

part = "all";
$fn = 64;

MOD = 1.5;
Z = 12;
GEAR_T = 6.0;
PLATE_T = 8.0;
BASE_T = 3.0;
BOSS_R = 7.0;           // the heart's bosses go to 7.0 too: the head's pocket needs it
BARBS = [0.45, 0.55, 0.65];
PITCH = 26;             // 12-tooth tips are 21 across: the gears don't mesh here
BAR_W = 2 * BOSS_R + 2;

module base() difference() {
    union() {
        hull() for (i = [0, 2]) translate([i * PITCH, 0, 0]) cylinder(r = BAR_W / 2, h = BASE_T);
        for (i = [0 : 2]) translate([i * PITCH, 0, 0]) { cylinder(r = BOSS_R, h = PLATE_T); pin_washer(PLATE_T); }
    }
    for (i = [0 : 2]) translate([i * PITCH, 0, 0]) pin_hole(PLATE_T);
    // the variant marks: 1, 2, 3 upright grooves in the bar's front edge, under each boss
    // (on the bar's top beside a boss, the third set fell off the bar's end). 0.6 deep, they
    // stop 0.8 short of the boss's own wall, and an upright groove hangs over nothing.
    for (i = [0 : 2]) for (k = [0 : i]) translate([i * PITCH + (k - i / 2) * 1.6 - 0.45, -BAR_W / 2 - 1, -1]) cube([0.9, 1.6, BASE_T + 2]);
}

// a pin with its variant marked: 1, 2 or 3 dimples in the head's top flat (the face that
// prints on top), along its length
module test_pin(i) difference() {
    pin_use(PLATE_T, GEAR_T, BARBS[i]);
    for (k = [0 : i]) translate([-3.5 + k * 2.0, PIN_FLAT - 0.6, 1.2]) rotate([-90, 0, 0]) cylinder(d = 1.2, h = 2, $fn = 24);
}
module pins() for (i = [0 : 2]) translate([i * 12, -30, PIN_FLAT]) rotate([90, 0, 0]) test_pin(i);
// product_gate's --wall-skip-part region (not printed): the pins' bed and top faces, 0.3
// deep. The pin is a D (a 3.5 round with flats 4.8 apart), so where the round meets a flat
// the prong is only 1.0-1.35 across, and the gate's horizontal rays skimming that face read
// it as a thin wall. It is the first and last layer of a 2.3-thick prong, not a wall; the
// slice prints it in full (print_fidelity: 0 flags, 0.08 mm3 dropped, all at the dimples,
// which this band also covers: they are 0.6 deep marks, not walls).
module gate_skip() for (k = [0, 1]) translate([-8, -50, k ? 2 * PIN_FLAT - 0.3 : -0.01]) cube([2 * 12 + 16, 30, 0.31]);
module gears() for (i = [0 : 2]) translate([i * PITCH, 30, 0]) gear(MOD, Z, GEAR_T, bore_d());

module assembled() {
    base();
    for (i = [0 : 2]) translate([i * PITCH, 0, 0]) {
        color("gold") test_pin(i);
        color("silver") translate([0, 0, PLATE_T + WASHER]) gear(MOD, Z, GEAR_T, bore_d());
    }
}

if (part == "base") base();
else if (part == "pins") pins();
else if (part == "gears") gears();
else if (part == "gate_skip") gate_skip();
else if (part == "assembled") assembled();
else { base(); pins(); gears(); }
echo("pin top above plate", pin_top(PLATE_T, GEAR_T, 0.55) - PLATE_T, "catch", pin_zc(PLATE_T, GEAR_T));
