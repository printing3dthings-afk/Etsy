// Iris box coupon (2026-11-12): the critical joints at their real size, before the box is
// modelled (mechanism handbook section 7, step 5; Benson's brief: "one blade, its pivot,
// and a ring segment").
//
// Three parts per variant, all printed flat, no supports:
//   base   a slice of the box's floor: the blade's pivot pin, and an arc groove the ring
//          piece rides in (its ends stop the ring at open and closed, 48 deg apart)
//   blade  the real blade (from iris_budget.py), with its pivot hole and drive slot
//   ring   a slice of the twist ring: the drive pin underneath, at the real radius, and a
//          tongue that runs in the groove
// Put the blade on the pivot pin, the ring's tongue in the groove and its pin in the
// blade's slot, then slide the ring from one end of the groove to the other: the blade
// swings 48.6 deg, from tucked in the rim to across the middle.
//
// Two variants, one per print (both on one plate took 58 min), differing only in the clearance on the holes, slot and
// groove (each side): 0.40 (one notch) and 0.55 (two notches; the budget's worst case).
// The heights are the box's: 0.5 mm gaps, a 1.4 mm blade on the lowest of three levels.
//
//   part = "plate" (with variant: one variant per print, each under 30 min) | "assembled" (with variant and phi, ring angle in deg, for checks and
//          renders) | "base" | "blade" | "ring" (each with variant, in the assembled pose
//          at phi)

include <coupon_data.scad>

part = "plate";
variant = 0;
phi = -46;
$fn = 48;

GAPS = [0.40, 0.55];
BT = 2.4;            // base plate
G  = 0.5;            // level gap (budget: 0.30 open + 0.20 worst case)
BLADE_T = 1.4;      // at 1.2 the gate measured the blade at its 1.2 floor exactly
RING_T = 2.4;
R_T = 48.5;          // the groove's radius: outside the blade's reach (R_OUT 45.5)
TONGUE_W = 3.0; TONGUE_L = 6.0;   // across and along the groove
GROOVE_D = 1.0;      // leaves 1.4 under the groove
Z_BLADE = BT + G;                 // blade bottom
Z_RING = Z_BLADE + BLADE_T + G;   // ring underside
TONGUE_A = TONGUE_L / R_T * 180 / PI;   // the tongue's angular length

function gp(v) = GAPS[v];
// the blade's pose at ring angle p: pivot at (RP, 0), turned to point at the drive pin
function pin_xy(p) = [RD * cos(p), RD * sin(p)];
function beta(p) = let (d = pin_xy(p) - [RP, 0]) atan2(d[1], d[0]);

module arc2d(r0, r1, a0, a1) polygon(concat(
    [for (a = [a0 : (a1 - a0) / 48 : a1]) r1 * [cos(a), sin(a)]],
    [for (a = [a1 : -(a1 - a0) / 48 : a0]) r0 * [cos(a), sin(a)]]));

module base(v) difference() {
    union() {
        linear_extrude(BT) union() {
            polygon(SWEEP);
            arc2d(40, R_T + TONGUE_W / 2 + gp(v) + 2.4, PHI_OPEN - TONGUE_A - 6, PHI_OPEN + TWIST + TONGUE_A + 6);
        }
        // pivot pin, up to just under the ring (the ring may rest on it)
        translate([RP, 0, 0]) cylinder(d = PIN_D, h = Z_RING - 0.35);
    }
    // the groove: its ends stop the tongue at open and closed
    translate([0, 0, BT - GROOVE_D]) linear_extrude(GROOVE_D + 1)
        arc2d(R_T - TONGUE_W / 2 - gp(v), R_T + TONGUE_W / 2 + gp(v),
              PHI_OPEN - TONGUE_A / 2 - gp(v) / R_T * 180 / PI, PHI_OPEN + TWIST + TONGUE_A / 2 + gp(v) / R_T * 180 / PI);
    // variant notches on the outer edge, upright: 1 = 0.40, 2 = 0.55
    for (k = [0 : v]) rotate(PHI_OPEN + TWIST + TONGUE_A + 3 - k * 2.2) translate([R_T + TONGUE_W / 2 + gp(v) + 1.6, -0.6, -1]) cube([2, 1.2, BT + 2]);
}

// the blade in its own frame (pivot at the origin, the slot along +x)
module blade2d(v) difference() {
    polygon(BLADE);
    circle(d = PIN_D + 2 * gp(v));
    hull() for (s = SLOT) translate([s, 0]) circle(d = PIN_D + 2 * gp(v));
}
module blade(v) linear_extrude(BLADE_T) blade2d(v);

// the ring piece at angle 0: plate, drive pin below at (RD, 0), tongue below at R_T
module ring(v) {
    translate([0, 0, Z_RING]) linear_extrude(RING_T) arc2d(RD - 5, R_T + TONGUE_W / 2 + 2, -12, 12);
    translate([RD, 0, Z_BLADE - 0.25]) cylinder(d = PIN_D, h = Z_RING - Z_BLADE + 0.25 + 0.01);
    translate([0, 0, BT - GROOVE_D]) linear_extrude(Z_RING - BT + GROOVE_D + 0.01)
        arc2d(R_T - TONGUE_W / 2, R_T + TONGUE_W / 2, -TONGUE_A / 2, TONGUE_A / 2);
}

module assembled(v, p) {
    base(v);
    translate([RP, 0, Z_BLADE]) rotate(beta(p)) blade(v);
    rotate(p) ring(v);
}

// as printed: each part flat on the plate, the ring upside down (pin and tongue up)
module plate(v) {
    translate([-20, 0, 0]) base(v);
    translate([-60, 25, 0]) blade(v);
    translate([60, 10, Z_RING + RING_T]) rotate([180, 0, 0]) ring(v);
}

if (part == "assembled") assembled(variant, phi);
else if (part == "base") base(variant);
else if (part == "blade") translate([RP, 0, Z_BLADE]) rotate(beta(phi)) blade(variant);
else if (part == "ring") rotate(phi) ring(variant);
else plate(variant);
