// Otter joint coupon (2026-11-11): the critical joint at its real size, three
// gaps on one plate, for Scott to print and test before the otter is built
// around it (mechanism handbook section 7, step 5).
//
// A "spinning-top" pin in a C-ring. The pin (left part) is narrow at its foot and
// head and widest in the middle; the ring (right part) wraps it with a bore that
// follows the same profile, a gap all round. Every slope is 37 deg from upright
// and both parts rise from the plate: nothing bridges, no gap hangs over air.
// The bulge holds the pin in vertically; the C's slot, narrower than the pin's
// waist, holds it sideways; the fin through the slot joins the pin to its block
// and stops the swing at the slot's sides.
//
// The sizes come from joint_budget.py (checks/budget.txt): one 4.0 mm waist for
// every variant, so only the gap changes; the wedge slot's angle lets the fin swing
// 15 deg, and the sideways retention is about twice the 3 x RSS rule. Notches on the pin block: 1 = 0.30, 2 = 0.35, 3 = 0.45.
//
//   part = "all" | "pin" | "ring"     (with variant = 0..2 for pin/ring)

part = "all";
variant = 0;
$fn = 96;

H      = 10.0;           // 50 layers
SLOPE  = 37;             // deg from upright, every cone
BULGE  = 1.5;
CONE_H = BULGE / tan(SLOPE);     // 1.99
FOOT   = 0.45;           // chamfer at the pin's foot and flare at the bore's foot, 0.6 tall
FOOT_H = 0.6;
WALL   = 2.0;
FIN    = 3.2;
//          gap   waist r  slot half-angle (deg)   (joint_budget.py)
VARIANTS = [[0.30, 4.0, 41.2], [0.35, 4.0, 41.6], [0.45, 4.0, 42.4]];
TAB_L  = 7;              // the blocks you hold
TAB_W  = 14;
PITCH  = 24;             // between pairs on the plate
Z1     = (H - 2 * CONE_H - 2.0) / 2;   // waist below the lower cone; the bulge is 2.0 tall

function v(i) = VARIANTS[i];
function r_out(i) = v(i)[1] + BULGE + v(i)[0] + WALL;

// the pin's profile in (r, z), without its foot chamfer
function pin_prof(ra) = let (rb = ra + BULGE)
    [[0, 0], [ra, 0], [ra, Z1], [rb, Z1 + CONE_H], [rb, Z1 + CONE_H + 2.0],
     [ra, Z1 + 2 * CONE_H + 2.0], [ra, H], [0, H]];

module pin_solid(ra) difference() {
    rotate_extrude() polygon(pin_prof(ra));
    // foot chamfer: FOOT in over FOOT_H (37 deg), so the first layer's gap is not
    // closed by elephant's foot
    rotate_extrude() polygon([[ra - FOOT, -0.01], [ra + 1, -0.01], [ra + 1, FOOT_H], [ra, FOOT_H]]);
}
module bore(ra, g) union() {
    // the gap grown round the pin's profile, clipped at the axis: unclipped, the
    // offset crosses to negative radius and rotate_extrude drops the whole bore
    // (the ring then printed solid round the pin)
    rotate_extrude() intersection() { offset(delta = g) polygon(pin_prof(ra)); translate([0, -5]) square([50, H + 10]); }
    // the bore's foot flares out FOOT over FOOT_H, mirroring the pin's chamfer
    rotate_extrude() polygon([[0, -1], [ra + g + FOOT, -1], [ra + g + FOOT, 0], [ra + g, FOOT_H], [0, FOOT_H]]);
    translate([0, 0, H - 0.01]) cylinder(r = ra + g, h = 2);
}
// the pin, its fin through the slot, and the block you hold (the left part)
module pin_side(i) let (g = v(i)[0], ra = v(i)[1], ro = r_out(i)) difference() {
    union() {
        pin_solid(ra);
        translate([-ro - 1.0, -FIN / 2, 0]) cube([ro + 1.0, FIN, H]);
        translate([-ro - 1.0 - TAB_L, -TAB_W / 2, 0]) cube([TAB_L, TAB_W, H]);
    }
    // notches across the block's top, one per variant number: 1, 2 or 3
    for (k = [0 : i]) translate([-ro - 1.0 - TAB_L + 1.6 + k * 2.2, -TAB_W / 2 - 1, H - 1.0]) cube([1.0, TAB_W + 2, 2]);
}
// the C-ring and its block (the right part)
module ring_side(i) let (g = v(i)[0], ra = v(i)[1], th = v(i)[2], ro = r_out(i)) difference() {
    union() {
        cylinder(r = ro, h = H);
        translate([ro - 1.5, -TAB_W / 2, 0]) cube([TAB_L + 1.5, TAB_W, H]);
    }
    bore(ra, g);
    // The C's slot, toward the pin's block: a wedge with radial sides. They meet the
    // bore square-on; the first draft's parallel-sided slot met it at 39 deg and left
    // a thin wedge at each lip (product gate min wall 0.86).
    translate([0, 0, -1]) linear_extrude(H + 2) polygon([[0, 0], [30 * cos(180 - th), 30 * sin(180 - th)],
                                                         [-30, 0], [30 * cos(180 + th), 30 * sin(180 + th)]]);
}

module pair(i) translate([0, i * PITCH, 0]) { pin_side(i); ring_side(i); }

if (part == "pin") translate([0, variant * PITCH, 0]) pin_side(variant);
else if (part == "ring") translate([0, variant * PITCH, 0]) ring_side(variant);
else for (i = [0 : 2]) pair(i);
