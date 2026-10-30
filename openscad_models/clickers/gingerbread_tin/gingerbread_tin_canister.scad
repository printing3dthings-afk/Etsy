// Gingerbread Tin Canister (2026-10-30). Scott: "design it so the tin is
// actually able to hold things and the lid itself be the clicker, so it has
// multipurpose", then "make it to where the square opening in the bottom of
// the lid is filled in".
//
// Two prints, and the clicker's own cookie and switch move over unchanged:
//   the canister     the clicker's red tin made tall and hollow, with the same
//                    lip at its mouth, so the lid sits on it as on the tin
//   the closed lid   the clicker's lid with a pod under its plate: the switch's
//                    body and pins sit in a closed pocket, so nothing in the
//                    canister reaches the switch and the square isn't open
//
//   part = canister | canister_snow | canister_print
//          lid_closed | lid_closed_holly | lid_closed_snow | lid_closed_print
//          assembly
// The closed lid exports standing on its pod, which is how it prints.
//
// The pod's underside is a 45 deg cone, so the lid prints on the pod's flat
// foot with nothing hanging. The pocket is square and straight-walled: the
// switch is square, and a straight wall leaves only a 1.0 ledge under the
// plate for its clips to catch on. A round pocket clearing the switch's corners
// (the tin's well, r 12) leaves a 5 mm ceiling there, which the slicer propped
// (clicker_lib.scad's note). The lid seats on a 45 deg ring inside the mouth.

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
TR     = 30.0;
SPIG_R = TR - LIP_W - JOINT_CLR;  // 28.6

// the pod under the lid
POCKET = mx_cutout + 2 * 1.0;     // 16 square: 1.0 round the cutout for the clips
PDEEP  = well_h;                  // the switch's body and pins, and 0.6 spare
PFLOOR = 1.2;
POD_H  = PDEEP + PFLOOR;          // 10.1
POD_R  = SPIG_R - POD_H;          // 18.5: 45 deg from the spigot down to the foot

// the canister
T      = 46;                      // the face the lid's spigot stands over
LIP_H  = 1.7;                     // 0.3 under the spigot's 2.0, so the lid's flare clears it
RIN    = 27.6;                    // inside: 2.4 of wall below the seat
SEAT   = TR - LIP_W;              // 28.8, the lip's inside
FLOOR  = 1.6;
FIL    = 3;                       // the inside's foot is rounded, so a finger scoops it clean
// The lid's cone (r SPIG_R at its underside) meets the seat's cone (r SEAT at
// T) when its underside is SEAT - SPIG_R = 0.2 below T.
LID_S  = T - (SEAT - SPIG_R);
echo(str("CANISTER lid underside ", LID_S, " cookie rest ", LID_S - S + CZ,
         " pod foot ", LID_S - POD_H, " top ", T + LIP_H));

module canister_solid() rotate_extrude($fn = 240) polygon(concat(
    [[0, 0], [TR + 0.5, 0], [TR + 0.5, 0.8], [TR, 1.4], [TR, T - 0.6], [TR + 0.5, T],
     [TR + 0.5, T + LIP_H], [SEAT, T + LIP_H], [SEAT, T], [RIN, T - (SEAT - RIN)]],
    [for (k = [0 : 12]) let (a = 90 * k / 12) [RIN - FIL + FIL * cos(a), FLOOR + FIL - FIL * sin(a)]],
    [[0, FLOOR]]));

// snowflakes raised on the wall as on the tin: three staggered rows of ten,
// clear of both beads with their skirts (foot bead tops out at 1.4, top bead
// starts at T - 0.6)
ROWS = [11.5, 23.5, 35.5];
ARM  = 3.4;
module on_cwall(a, z, h) rotate([0, 0, a]) translate([TR - 0.35, 0, z]) rotate([90, 0, 90]) art_skirt(h, 1) children();
module canister_snow_raw() for (r = [0 : len(ROWS) - 1], i = [0 : 9]) let (a = 90 + (i + r % 2 / 2) * 36)
    on_cwall(a, ROWS[r], 1.05) rotate((i + r) % 2 * 30) snowflake2d(ARM);

module canister_mark() translate([0, -19, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
module canister() difference() { canister_solid(); canister_mark(); }
module canister_snow() difference() { canister_snow_raw(); canister_solid(); }

// the closed lid, in the clicker's frame (its underside at S)
// The pocket's top 1.0 closes in at 45 deg to the cutout's own 14 at the plate.
// Flat, that 1.0 ledge under the plate was a ceiling round the cutout: 12,196
// support moves in the slicer (2026-10-30). The clips' hooks catch on its edge,
// where the plate is the 1.5 they expect.
module pocket() {
    translate([-POCKET / 2, -POCKET / 2, S - PDEEP]) cube([POCKET, POCKET, PDEEP - 1.0 + 0.01]);
    translate([0, 0, S - 1.0]) linear_extrude(1.3, scale = (POCKET - 2.6) / POCKET) square(POCKET, center = true);
}
// the cone ends at the lid's underside, r SPIG_R at S, so the two only share a face
module pod() difference() {
    translate([0, 0, S - POD_H]) cylinder(h = POD_H, r1 = POD_R, r2 = SPIG_R, $fn = 240);
    pocket();
}
module lid_closed() union() { lid(); pod(); }

module at_lid() translate([0, 0, LID_S - S]) children();
module print_frame() translate([0, 0, POD_H - S]) children();

if      (part == "canister")         canister();
else if (part == "canister_snow")    canister_snow();
else if (part == "canister_print")   union() { canister(); canister_snow(); }
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
