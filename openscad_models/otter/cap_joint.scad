// The otter's joint with a cap over it (2026-11-13). Scott, after the first flexi
// draft showed every joint on top as a ring in a pit: hide the joints, and more
// cartoony-realistic detail.
//
// Below CAP_Z it is the joint Scott tested and picked, unchanged: the spinning-top pin
// in a C-ring, 0.30 mm gap, 4.0 mm waist, 1.5 mm bulge, 37 deg cones, 41.2 deg slot
// (joint_coupon.scad variant 0, "Number 1 was best"). Above it the pin carries on up
// into a cap that covers the joint. The cap's underside is a cone at 37 deg from
// upright, widening as it rises, over a matching countersink in the ring's segment,
// CAP_GAP apart. That is the same kind of interface as the pin's own bulge cones,
// which printed free at 0.30. Above the cone the cap is an upright cylinder, CAP_R,
// in a round hole SIDE_GAP bigger. From above, the joint is a thin circle.
//
// Used by cap_joint_coupon.scad (the test print) and the otter.

H      = 10.0;     // the tested joint's height
SLOPE  = 37;
BULGE  = 1.5;
CONE_H = BULGE / tan(SLOPE);
FOOT   = 0.45;
FOOT_H = 0.6;
FIN    = 3.2;
GAP    = 0.30;
WAIST  = 4.0;
SLOT   = 41.2;
Z1     = (H - 2 * CONE_H - 2.0) / 2;
RO     = WAIST + BULGE + GAP + 2.0;      // the ring's outside, 7.8
R      = RO + 0.5;                       // the front segment's disc, 8.3
GAP_B  = 0.5;                            // disc to the back segment's arc, upright walls

CAP_R    = 9.6;                          // covers the disc, the arc gap and the slot (cut to R + 1)
CAP_Z    = H;                            // where the cap starts: the tested joint's top
CAP_CONE = (CAP_R - WAIST) / tan(SLOPE); // 7.43 tall
CAP_TOP  = 1.2;                          // solid above the cone
TOP      = CAP_Z + CAP_CONE + CAP_TOP;   // the body's height round a joint, 18.6
SIDE_GAP = 0.5;                          // round the cap's upright part

function pin_prof(ra) = let (rb = ra + BULGE)
    [[0, 0], [ra, 0], [ra, Z1], [rb, Z1 + CONE_H], [rb, Z1 + CONE_H + 2.0],
     [ra, Z1 + 2 * CONE_H + 2.0], [ra, H], [0, H]];

module pin_solid() difference() {
    rotate_extrude() polygon(pin_prof(WAIST));
    rotate_extrude() polygon([[WAIST - FOOT, -0.01], [WAIST + 1, -0.01], [WAIST + 1, FOOT_H], [WAIST, FOOT_H]]);
}
// the cap, in (r, z): from the pin's top, out along the cone, up to TOP
CAP_PROF = [[0, CAP_Z - 0.01], [WAIST, CAP_Z - 0.01], [CAP_R, CAP_Z + CAP_CONE], [CAP_R, TOP], [0, TOP]];
module cap_solid() rotate_extrude() polygon(CAP_PROF);

// what the ring's segment gives up: the tested bore, then the cap grown by its gaps
module bore(cap_gap = GAP) union() {
    rotate_extrude() intersection() { offset(delta = GAP) polygon(pin_prof(WAIST)); translate([0, -5]) square([50, H + 10]); }
    rotate_extrude() polygon([[0, -1], [WAIST + GAP + FOOT, -1], [WAIST + GAP + FOOT, 0], [WAIST + GAP, FOOT_H], [0, FOOT_H]]);
    // the countersink: the cone grown by cap_gap normal to it, and the hole round
    // the cap's upright part SIDE_GAP wider (clipped at the axis)
    rotate_extrude() intersection() {
        union() {
            offset(delta = cap_gap) polygon([[0, CAP_Z - 1], [WAIST, CAP_Z - 1], [WAIST, CAP_Z], [CAP_R, CAP_Z + CAP_CONE], [CAP_R, TOP + 5], [0, TOP + 5]]);
            translate([0, CAP_Z + CAP_CONE]) square([CAP_R + SIDE_GAP, 10]);
        }
        translate([0, CAP_Z - 1]) square([50, 30]);
    }
}
// the C's slot, opening toward the back segment (+x), cut up through the cap's zone so
// nothing roofs the fin flat (a flat roof over a moving part could fuse)
module slot() translate([0, 0, -1]) linear_extrude(TOP + 2)
    intersection() {
        polygon([[0, 0], [30 * cos(-SLOT), 30 * sin(-SLOT)], [30, 0], [30 * cos(SLOT), 30 * sin(SLOT)]]);
        circle(r = R + 1, $fn = 72);
    }
// the back segment's joint parts: pin, fin out to its body, and the cap
module pin_parts() { pin_solid(); translate([0, -FIN / 2, 0]) cube([R + GAP_B + 1, FIN, H]); cap_solid(); }

// The ring's disc keeps a lip between the countersink and its edge (R). Going up the
// cone that lip thins to nothing, and the product gate read 0.88 mm (2026-11-13). Above
// the height where it would be under WALL_MIN, cut it away wherever the disc stands
// alone (not where it runs into the front segment's own body, round the back half).
// The cap's cone then hangs over air there, the same as it does over the slot.
WALL_MIN = 1.2;
function trim_z(cap_gap) = CAP_Z + (R - WALL_MIN - cap_gap / cos(SLOPE) - WAIST) / tan(SLOPE);
module disc_trim(cap_gap, v_half) translate([0, 0, trim_z(cap_gap)]) linear_extrude(TOP)
    intersection() {
        circle(r = R + 0.01, $fn = 72);
        polygon(concat([[0, 0]], [for (a = [-(90 + v_half) : 6 : 90 + v_half]) 30 * [cos(a), sin(a)]]));
    }
