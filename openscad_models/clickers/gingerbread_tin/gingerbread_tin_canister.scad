// Gingerbread Tin Canister (2026-10-30). Scott: "design it so the tin is
// actually able to hold things and the lid itself be the clicker, so it has
// multipurpose", then "make it to where the square opening in the bottom of
// the lid is filled in".
//
// Two prints, and the clicker's own cookie and switch move over unchanged:
//   the canister     the clicker's red tin made tall and hollow, with the same
//                    threaded collar at its mouth, so the lid screws on as on
//                    the tin
//   the closed lid   the clicker's lid with a pod under its plate: the switch's
//                    body and pins sit in a closed pocket, so nothing in the
//                    canister reaches the switch and the square isn't open
//
// The lid screws on (Scott, 2026-11-03: "the gingerbread big tin needs the
// screw on top like the little one"). Same thread as the clicker's tin; the
// lid screws down until its pod's cone meets a matching cone in the canister's
// mouth. A flat ring inside the mouth for the lid's floor to stop on made the
// pod 2.2 narrower than the lid, and the lid, printed on its pod, hung its
// floor over air: 9,349 support moves (2026-11-03).
//
// The guide ring (Scott, 2026-11-05: the threads would break if the lid went on
// crooked). Under the lid a smooth ring, as tall as the pod, drops into a smooth
// bore in the mouth, 0.15 clear all round, and is in it the whole way before the
// lid's teeth reach the canister's: on a 57 mm lid only a long guide holds it
// square, as a short one tips across its own diameter. Screwed down, the ring
// stands on a shelf at the foot of the bore: that is the lid's stop now, and the
// pod no longer touches the mouth. The thread is deeper and coarser (see the
// clicker's file) and the collar's top follows the lid's flare, 0.2 under it.
//
//   part = canister | canister_snow | canister_print
//          lid_closed | lid_closed_holly | lid_closed_snow | lid_closed_print
//          assembly
// The closed lid exports standing on its pod, which is how it prints.
//
// The pod's underside is a cone 40 deg from vertical, so the lid prints on the
// pod's flat foot with nothing hanging. At 45 deg, the slicer's own threshold,
// the cone and the pocket's chamfer drew 11,524 support moves (2026-10-30).
// The pocket is square, as the switch is, and closes in at the same slope to the
// cutout just under the plate, where the clips catch. A round pocket clearing
// the switch's corners (the tin's well, r 12) leaves a 5 mm ceiling under the
// plate, which the slicer propped (clicker_lib.scad's note); a flat 1.0 ledge
// round the cutout drew 12,196 moves.

SH = 1.2;
include <../../christmas_village/relief_lib.scad>
use <../../brand/obc_mark.scad>
include <../clicker_lib.scad>
use <gingerbread_tin_clicker.scad>

part = "assembly";
$fa = 2; $fs = 0.3;

// the clicker's numbers, as gingerbread_tin_clicker.scad sets them
S      = 1.6 + well_h;            // the lid's underside, in the clicker's frame
P      = S + mx_plate_t;
CZ     = mx_cap_z(P);
TR     = 30.5;
// and its thread (2026-10-30)
TH_H = 4.4; TH_R = 29.1; TH_D = 1.2; TH_C = 0.2;
BORE = TH_R - TH_D + TH_C - 0.1;   // 28.0, the collar's bore

// the pod under the lid
PA     = 40;                      // its slopes, from vertical
CH_H   = 1.0;                     // the pocket's chamfer up to the cutout
POCKET = mx_cutout + 2 * CH_H * tan(PA);   // 15.7 square: room for the clips under the plate
PDEEP  = well_h;                  // the switch's body and pins, and 0.6 spare
// 1.3, so the pod lifts the lid a whole 51 layers. At 1.2 (10.1) every detail on
// top fell half a layer off where the clicker's lid prints it, and the white
// snowflakes' tips dropped out: 25 fidelity flags to the lid's 0 (2026-10-30).
PFLOOR = 1.3;
POD_H  = PDEEP + PFLOOR;          // 10.2
POD_TOP = TH_R - TH_D;            // 27.9: the pod's cone runs right up to the lid's edge
POD_R  = POD_TOP - POD_H * tan(PA);  // 19.3: from under the lid down to the foot

// the canister
T      = 46;                      // the face the lid's floor sits on
RIN    = 27.6;                    // inside: 2.4 of wall below the collar
FLOOR  = 1.6;
FIL    = 3;                       // the inside's foot is rounded, so a finger scoops it clean
LID_S  = T;                       // screwed down, its ring on the shelf
// the guide ring under the lid, and the bore and shelf in the mouth it runs in
RING_O = BORE - 0.15;             // 27.85: 0.15 clear of the bore and the thread's crests
RING_T = 1.6;
RING_H = POD_H;                   // to the pod's foot, so the lid still prints on the bed
SHELF_R = RING_O - RING_T - 0.25; // 26.0: the ring stands on 1.35 of shelf
echo(str("CANISTER lid underside ", LID_S, " cookie rest ", LID_S - S + CZ,
         " pod foot ", LID_S - POD_H, " top ", T + TH_H));

module canister_solid() rotate_extrude($fn = 240) polygon(concat(
    // the collar carries the thread, its top following the lid's flare; under it
    // the mouth is a smooth bore down to the shelf the ring stops on, whose
    // underside slopes back to the wall at PA
    [[0, 0], [TR + 0.5, 0], [TR + 0.5, 0.8], [TR, 1.4], [TR, collar_top(TR, T)],
     [BORE, collar_top(BORE, T)], [BORE, T - RING_H], [SHELF_R, T - RING_H],
     [RIN, T - RING_H - (RIN - SHELF_R) / tan(PA)]],
    [for (k = [0 : 12]) let (a = 90 * k / 12) [RIN - FIL + FIL * cos(a), FLOOR + FIL - FIL * sin(a)]],
    [[0, FLOOR]]));

// snowflakes raised on the wall as on the tin: three staggered rows of ten,
// clear of the foot bead with their skirts (it tops out at 1.4) and of the
// collar's thread above T
ROWS = [11.5, 23.5, 35.5];
ARM  = 3.4;
module on_cwall(a, z, h) rotate([0, 0, a]) translate([TR - 0.35, 0, z]) rotate([90, 0, 90]) art_skirt(h, 1) children();
module canister_snow_raw() for (r = [0 : len(ROWS) - 1], i = [0 : 9]) let (a = 90 + (i + r % 2 / 2) * 36)
    on_cwall(a, ROWS[r], 1.05) rotate((i + r) % 2 * 30) snowflake2d(ARM);

module canister_mark() translate([0, -19, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
module canister() difference() { canister_solid(); canister_mark(); translate([0, 0, T - S]) tin_thread_cut(); }
module canister_snow() difference() { canister_snow_raw(); canister_solid(); }

// the closed lid, in the clicker's frame (its underside at S)
// The pocket's top CH_H closes in at PA to the cutout's own 14 at the plate.
// Flat, that 1.0 ledge under the plate was a ceiling round the cutout: 12,196
// support moves in the slicer (2026-10-30). The clips' hooks catch on its edge,
// where the plate is the 1.5 they expect.
module pocket() {
    translate([-POCKET / 2, -POCKET / 2, S - PDEEP]) cube([POCKET, POCKET, PDEEP - CH_H + 0.01]);
    // carried 0.3 past the plate's underside on the same slope, so it meets the
    // cutout exactly at S
    translate([0, 0, S - CH_H]) linear_extrude(CH_H + 0.3, scale = (mx_cutout - 0.6 * tan(PA)) / POCKET)
        square(POCKET, center = true);
}
// the cone ends at the lid's underside, r POD_TOP at S, so the two only share a face
module pod() difference() {
    translate([0, 0, S - POD_H]) cylinder(h = POD_H, r1 = POD_R, r2 = POD_TOP, $fn = 240);
    pocket();
}
// the guide ring, its top in the lid's floor
module ring() translate([0, 0, S - RING_H]) difference() {
    cylinder(h = RING_H + 0.01, r = RING_O, $fn = 240);
    translate([0, 0, -0.01]) cylinder(h = RING_H + 0.1, r = RING_O - RING_T, $fn = 240);
}
// the clicker's threaded lid with the pod and the guide ring under it
module lid_closed() union() { lid(); pod(); ring(); }

module at_lid() translate([0, 0, LID_S - S]) children();
module print_frame() translate([0, 0, POD_H - S]) children();

if      (part == "canister")         canister();
else if (part == "canister_snow")    canister_snow();
else if (part == "canister_print")   union() { canister(); canister_snow_raw(); }   // the raw flakes overlap the wall, so the merge closes
else if (part == "lid_closed")       print_frame() lid_closed();
else if (part == "lid_closed_holly") print_frame() lid_holly();
else if (part == "lid_closed_snow")  print_frame() lid_snow();
else if (part == "lid_closed_print") print_frame() union() { lid_closed(); lid_holly(); lid_snow(); }
else {
    color("#B3262E") canister();
    color("white") canister_snow();
    at_lid() {
        color("#B3262E") lid_closed();
        color("#3E8E4A") lid_holly();
        color("white") lid_snow();
        mx_mock(S);
    }
}
