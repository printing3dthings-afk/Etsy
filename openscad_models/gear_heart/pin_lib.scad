// Gear Heart clips v2 (2026-11-14, Brief E): the axle pin that replaces the snap post.
//
// Scott printed the whole heart and one of the old posts SNAPPED. Its prongs stood up out
// of the plate, printed upright, so pushing a gear over the barb bent them ACROSS the
// layers: 1.19 % strain against about 0.77 % that PLA holds that way (clip_budget.py).
// This pin prints lying on its side, so its prongs bend in the print plane, along the
// layers, where the same PLA holds 1.4 %.
//
// In use (this file's frame): the pin stands on z, its head under the plate (in a pocket
// in the plate's bed face, z = 0 to PIN_HEAD_T), its shank up through the plate, the
// washer and the gear, and two prongs (+x and -x of a slot) with barbs that catch the
// gear's top. The faces it prints on are the two flats at y = +/-PIN_FLAT.
//   pin_use(plate_t, gear_t, barb)   the pin, standing in a plate whose top is at plate_t
//   pin_print(...)                   the same, lying on its side for printing
//   pin_hole(plate_t)                what to cut out of the plate for it
// gear_lib.scad's bore_d() (7.7) and WASHER are unchanged: the gears don't change.

include <gear_lib.scad>

PIN_R = 3.5;             // the shank: 0.35 a side in the gear's 7.7 bore, as the old post
PIN_FLAT = 2.4;          // flats 4.8 apart: the faces it prints on (prong width 4.8). At 2.6 the
                         // round sides met the bed face at 48 deg, past 45 (the gate propped them)
PIN_HEAD = [10.5, 4.8, 2.4];   // the head: a bar under the plate (10.5 long: its pocket fits in a 7.0 boss)
HEAD_CLR = 0.25;         // the head's pocket, each side
SLOT_ROOT = 2.4;         // the slot between the prongs: 2.4 at its rounded root,
SLOT_TIP = 3.2;          //   3.2 at the tip, so the prongs taper 2.3 -> 1.9
SLOT_Z0 = 1.2;           // the root's bottom, inside the head
PIN_LAND = 0.4;          // the barb's straight band above its catch
PIN_LEAD = 30;           // the lead-in, deg from the axis
PIN_TIP_R = 3.5;         // the shank's: smaller, the tip cone met the bed face past 45 deg; at
                         // 2.2 against a 3.8 slot the prong tip was 0.3 thick
// The barb's catch is square: the pin prints on its side, so it hangs over nothing. It
// self-locks against a pull (clip_budget.py).

function pin_zc(plate_t, gear_t) = plate_t + WASHER + gear_t + AX_PLAY;   // the catch
function pin_top(plate_t, gear_t, barb) =
    pin_zc(plate_t, gear_t) + PIN_LAND + (bore_d() / 2 + barb - PIN_TIP_R) / tan(PIN_LEAD);

module pin_use(plate_t, gear_t, barb) {
    zc = pin_zc(plate_t, gear_t);
    rb = bore_d() / 2 + barb;
    zt = pin_top(plate_t, gear_t, barb);
    difference() {
        intersection() {
            union() {
                // head
                translate([-PIN_HEAD[0] / 2, -PIN_HEAD[1] / 2, 0]) cube(PIN_HEAD);
                // shank, barb and lead-in, as one turned profile
                rotate_extrude($fn = 96) polygon([[0, 0], [PIN_R, 0], [PIN_R, zc], [rb, zc],
                                                  [rb, zc + PIN_LAND], [PIN_TIP_R, zt], [0, zt]]);
            }
            // the flats
            translate([-50, -PIN_FLAT, -1]) cube([100, 2 * PIN_FLAT, zt + 2]);
        }
        // the slot: rounded at its root, widening to the tip
        rotate([90, 0, 0]) linear_extrude(2 * PIN_FLAT + 2, center = true)
            hull() {
                translate([0, SLOT_Z0 + SLOT_ROOT / 2]) circle(d = SLOT_ROOT, $fn = 48);
                translate([-SLOT_TIP / 2, zt]) square([SLOT_TIP, 1]);
            }
    }
}
// lying on its side: the flat at y = -PIN_FLAT on the bed, the axis along -y of the plate
module pin_print(plate_t, gear_t, barb) translate([0, 0, PIN_FLAT]) rotate([90, 0, 0]) pin_use(plate_t, gear_t, barb);

// the plate's cut: the through hole, and the head's pocket in the bed face. The pocket's
// roof is pitched at 55 deg from its long edges: flat, the slicer propped it (1,165 support
// moves), and at 45 and 50 the gate's slicer still did; 55, 60 and 70 drew none (2026-11-14).
// 55 keeps the ridge 1.6 under the boss top. The head's top edges reach the slopes about
// 0.4 above its seat: that is the pin's end play (check_clip.py measures it).
module pin_hole(plate_t) {
    translate([0, 0, -1]) cylinder(r = bore_d() / 2, h = plate_t + 2, $fn = 64);
    w = PIN_HEAD[1] / 2 + HEAD_CLR;
    translate([-PIN_HEAD[0] / 2 - HEAD_CLR, 0, 0]) rotate([90, 0, 90]) linear_extrude(PIN_HEAD[0] + 2 * HEAD_CLR)
        polygon([[-w, -1], [w, -1], [w, PIN_HEAD[2] + 0.05], [0, PIN_HEAD[2] + 0.05 + w * tan(55)], [-w, PIN_HEAD[2] + 0.05]]);
}
// the washer ring on the boss, now round a hole
module pin_washer(plate_t) translate([0, 0, plate_t - 0.01]) difference() {
    cylinder(r = bore_d() / 2 + 2.2, h = WASHER + 0.01, $fn = 64);
    translate([0, 0, -1]) cylinder(r = bore_d() / 2, h = 5, $fn = 64);
}
