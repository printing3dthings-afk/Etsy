// Gingerbread Tin Canister (2026-10-30). Scott: "design it so the tin is
// actually able to hold things and the lid itself be the clicker, so it has
// multipurpose".
//
// The whole clicker (tin, lid, cookie, switch) is unchanged, and becomes the
// canister's lid: its flat foot drops into a seat round the canister's mouth.
// So a clicker already printed needs only this canister to become a tin that
// holds sweets, clips or a gift card under a lid you can still click.
//
//   part = canister | canister_snow | canister_print (merged, for the gate)
//          assembly (preview: canister + the clicker as its lid)
//
// The canister is the clicker's red tin made tall: the same rolled beads at its
// foot and lip, the same raised snowflakes, in staggered rows.

SH = 1.2;
include <../../christmas_village/relief_lib.scad>
use <../../brand/obc_mark.scad>
include <../clicker_lib.scad>
use <gingerbread_tin_clicker.scad>

part = "canister";
$fa = 2; $fs = 0.3;

LIDR   = 30.5;          // the clicker's foot bead, which drops into the seat
SEAT_R = LIDR + 0.4;    // 0.4 all round: lifts off freely
SEAT_D = 1.6;           // deep enough to keep the lid from sliding, below its snowflakes
CR     = SEAT_R + 1.3;  // the canister's wall: 1.3 outside the seat
H      = 46;            // its height to the lip
FLOOR  = 1.6;
RIN    = 28.6;          // inside: a 2.3 ledge under the lid's foot
FIL    = 3;             // the inside's foot is rounded, so a finger scoops it clean

// the canister: beads at the foot and the lip as on the tin (the lip's climbs out
// at 40 deg, 0.5 over 0.6), the seat cut into the top, a rounded inside floor
module canister_solid() rotate_extrude($fn = 240) polygon(concat(
    [[0, 0], [CR + 0.5, 0], [CR + 0.5, 0.8], [CR, 1.4], [CR, H - 0.6], [CR + 0.5, H],
     [SEAT_R, H], [SEAT_R, H - SEAT_D], [RIN, H - SEAT_D]],
    [for (k = [0 : 12]) let (a = 90 * k / 12) [RIN - FIL + FIL * cos(a), FLOOR + FIL - FIL * sin(a)]],
    [[0, FLOOR]]));

// snowflakes raised on the wall as on the tin: three staggered rows of ten,
// clear of both beads with their skirts (foot bead tops out at 1.4, lip bead
// starts at H - 0.6)
ROWS = [11.5, 23.5, 35.5];
ARM  = 3.4;
module on_cwall(a, z, h) rotate([0, 0, a]) translate([CR - 0.35, 0, z]) rotate([90, 0, 90]) art_skirt(h, 1) children();
module canister_snow_raw() for (r = [0 : len(ROWS) - 1], i = [0 : 9]) let (a = 90 + (i + r % 2 / 2) * 36)
    on_cwall(a, ROWS[r], 1.05) rotate((i + r) % 2 * 30) snowflake2d(ARM);

module canister_mark() translate([0, -19, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
module canister() difference() { canister_solid(); canister_mark(); }
module canister_snow() difference() { canister_snow_raw(); canister_solid(); }

if      (part == "canister")       canister();
else if (part == "canister_snow")  canister_snow();
else if (part == "canister_print") union() { canister(); canister_snow(); }
else {
    color("#B3262E") canister();
    color("white") canister_snow();
}
