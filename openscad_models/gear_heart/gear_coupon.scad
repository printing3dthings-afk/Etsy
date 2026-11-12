// Gear heart coupon (2026-11-11): the critical parts at their real size, for Scott
// to print and test before the heart is built around them (mechanism handbook
// section 7, step 5).
//
// Two bars, each with two snap posts, and one pair of the heart's outline gears
// (16 and 12 teeth, module 1.5), printed flat beside them. Press the gears onto
// one bar and turn them, pull them off, then press them onto the other: the bars
// differ only in how far apart the posts are, the mesh's backlash. One notch: +0.20 mm on the centre distance; two: +0.40.
// The heart is designed at +0.30, between them.
//
//   part = "all" | "bars" | "gears" | "bar" (with variant) | "posted" (assembled, review)

include <gear_lib.scad>

part = "all";
variant = 0;
$fn = 64;

MOD = 1.5;
Z_A = 16; Z_B = 12;
GEAR_T = 6.0;
PLATE_T = 8.0;      // the posts rise from pockets 6.5 deep (gear_budget.py)
DCS = [0.20, 0.40];
BAR_W = 14;
PITCH_Y = 34;

function cd(i) = MOD * (Z_A + Z_B) / 2 + DCS[i];
module bar(i) let (c = cd(i)) translate([0, i * PITCH_Y, 0]) difference() {
    union() {
        hull() { cylinder(d = BAR_W, h = PLATE_T); translate([c, 0, 0]) cylinder(d = BAR_W, h = PLATE_T); }
        for (x = [0, c]) translate([x, 0, 0]) { post(PLATE_T, GEAR_T); washer(PLATE_T); }
    }
    for (x = [0, c]) translate([x, 0, 0]) difference() { post_pocket(PLATE_T); post(PLATE_T, GEAR_T); }
    // notches on the bar's end: 1 = +0.20, 2 = +0.40
    for (k = [0 : i]) translate([c / 2 - 2 + k * 2.4, -BAR_W, PLATE_T - 1.0]) cube([1.2, 2 * BAR_W, 2]);
}
// the gears, printed flat beside the bars, a pair for each bar
// one pair, tested on one bar, pulled off once (that tests the pull-off) and pressed
// onto the other: two pairs made the plate 44 min, over the 30 min a coupon should be
module gears() translate([cd(1) / 2, PITCH_Y / 2, 0]) {
    translate([cd(1) / 2 + 22, 0, 0]) gear(MOD, Z_A, GEAR_T, bore_d());
    translate([cd(1) / 2 + 22 + g_ra(MOD, Z_A) + g_ra(MOD, Z_B) + 4, 0, 0]) gear(MOD, Z_B, GEAR_T, bore_d());
}
// review: the gears pressed on, as they will sit (on the washer, under the barb)
module posted() for (i = [0 : 1]) {
    bar(i);
    translate([0, i * PITCH_Y, PLATE_T + WASHER]) gear(MOD, Z_A, GEAR_T, bore_d());
    translate([cd(i), i * PITCH_Y, PLATE_T + WASHER]) rotate(180 / Z_B) gear(MOD, Z_B, GEAR_T, bore_d());
}

// single parts in the assembled pose, for check_gears.py
if (part == "pos_a") translate([0, variant * PITCH_Y, PLATE_T + WASHER]) gear(MOD, Z_A, GEAR_T, bore_d());
else if (part == "pos_b") translate([cd(variant), variant * PITCH_Y, PLATE_T + WASHER]) rotate(180 / Z_B) gear(MOD, Z_B, GEAR_T, bore_d());
else if (part == "bars") for (i = [0 : 1]) bar(i);
else if (part == "bar") bar(variant);
else if (part == "gears") gears();
else if (part == "posted") posted();
else { for (i = [0 : 1]) bar(i); gears(); }
