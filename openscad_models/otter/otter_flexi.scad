// Flexi Otter (2026-11-13): Scott's form A of four, "classic flexi". An otter lying on
// its back, holding a shell on its tummy, in nine segments on eight print-in-place
// joints. It curls side to side, about +/-20 deg a joint.
//
// Every joint is the joint test's number 1, the one Scott picked ("Number 1 was
// best", 2026-11-13): a spinning-top pin in a C-ring with a 0.30 mm gap, 4.0 mm
// waist, 1.5 mm bulge, 37 deg cones, 41.2 deg slot (joint_coupon.scad, variant 0;
// joint_budget.py). Only what's round the joint is new:
//   - each joint is the centre of a disc, radius R, on the front segment; the back
//     segment stops GAP_B outside it, so the two slide past each other on arcs;
//   - beyond that, the segments meet along radial lines with a V between them,
//     V_HALF a side, so their outer edges don't collide when it bends;
//   - the joints are at least 2R + GAP_B + the bore apart, so every segment keeps a
//     real wall between its front arc and its back bore.
// Printed flat on its back, face up. Head at -x, tail at +x. The body is 13 mm tall
// and domed; each joint sits 3 mm down in a round pit, at the test's own 10 mm.
//
//   part = "otter" | "segment" (with seg = 0..8, as printed) | "posed" (with bend)

part = "otter";
seg = 0;
bend = 0;          // deg at every joint, for the posed part
$fn = 72;

// ---- the joint, from the joint test (variant 0) ----
H      = 10.0;
SLOPE  = 37;
BULGE  = 1.5;
CONE_H = BULGE / tan(SLOPE);
FOOT   = 0.45;
FOOT_H = 0.6;
FIN    = 3.2;
GAP    = 0.30;
WAIST  = 4.0;
SLOT   = 41.2;     // the C slot's half-angle
Z1     = (H - 2 * CONE_H - 2.0) / 2;
RO     = WAIST + BULGE + GAP + 2.0;   // the ring's outside, 7.8

// ---- round the joint ----
R      = RO + 0.5;    // the front segment's disc
GAP_B  = 0.5;         // between the disc and the back segment's arc (upright walls)
V_HALF = 12;          // deg, each side of the V between segments: the joint swings ~20
JOINTS = [18, 48, 72, 94, 112, 130, 148, 166];   // x of each joint; the chest is long for the shell
H_BODY = 13.0;        // the body stands 3 mm above the joints, which sit in round pits
TOP_R  = 4.5;         // the top edge of the outline rounded over this radius

// ---- the outline, seen from above ----
module outline() union() {
    circle(r = 15.5);                                                     // head
    for (sg = [-1, 1]) translate([4.5, sg * 9]) scale([1, 0.85]) circle(r = 8.5);  // cheek puffs
    for (sg = [-1, 1]) translate([-7, sg * 13.5]) circle(r = 4);          // ears, low on the sides
    hull() { translate([26, 0]) circle(r = 15); translate([60, 0]) circle(r = 22.5); }
    hull() { translate([60, 0]) circle(r = 22.5); translate([84, 0]) circle(r = 17); }
    for (sg = [-1, 1]) hull() { translate([84, sg * 14]) circle(r = 5); translate([87, sg * 23]) circle(r = 6.5); }   // hind feet
    hull() { translate([98, 0]) circle(r = 12.5); translate([181, 0]) circle(r = 5.5); }   // tail
    for (j = JOINTS) translate([j, 0]) circle(r = R + 1.5);              // every joint inside the body
}
ROUND = 2.0;      // each segment's corners rounded, so they read as soft plates

// a wedge of the plane round point c, from angle a0 to a1
module wedge(c, a0, a1) translate([c, 0])
    polygon(concat([[0, 0]], [for (a = [a0 : (a1 - a0) / 24 : a1]) 300 * [cos(a), sin(a)]]));

module seg2d(s) offset(r = ROUND) offset(r = -ROUND) intersection() {
    outline();
    if (s > 0) difference() { wedge(JOINTS[s - 1], -90 + V_HALF, 90 - V_HALF);
                               translate([JOINTS[s - 1], 0]) circle(r = R + GAP_B); }
    if (s < 8) union() { wedge(JOINTS[s], 90 + V_HALF, 270 - V_HALF); translate([JOINTS[s], 0]) circle(r = R); }
}

// The outline's top edge rounded over TOP_R, in steps, so each segment reads as a soft
// pebble rather than a cut-out. The joints stand full height inside it: rounding
// them would lower the ring's lip and change the joint Scott tested.
module slab() union() {
    linear_extrude(H_BODY - TOP_R) outline();
    for (i = [0 : 9]) let (z0 = H_BODY - TOP_R + i * TOP_R / 10, z1 = z0 + TOP_R / 10,
                           inset = TOP_R - sqrt(TOP_R * TOP_R - pow(z1 - (H_BODY - TOP_R), 2)))
        translate([0, 0, z0]) linear_extrude(TOP_R / 10 + 0.001) offset(delta = -inset) outline();
    for (j = JOINTS) translate([j, 0, 0]) cylinder(r = RO + 0.6, h = H);
}

// ---- the joint's parts (joint_coupon.scad) ----
function pin_prof(ra) = let (rb = ra + BULGE)
    [[0, 0], [ra, 0], [ra, Z1], [rb, Z1 + CONE_H], [rb, Z1 + CONE_H + 2.0],
     [ra, Z1 + 2 * CONE_H + 2.0], [ra, H], [0, H]];
module pin_solid() difference() {
    rotate_extrude() polygon(pin_prof(WAIST));
    rotate_extrude() polygon([[WAIST - FOOT, -0.01], [WAIST + 1, -0.01], [WAIST + 1, FOOT_H], [WAIST, FOOT_H]]);
}
module bore() union() {
    rotate_extrude() intersection() { offset(delta = GAP) polygon(pin_prof(WAIST)); translate([0, -5]) square([50, H + 10]); }
    rotate_extrude() polygon([[0, -1], [WAIST + GAP + FOOT, -1], [WAIST + GAP + FOOT, 0], [WAIST + GAP, FOOT_H], [0, FOOT_H]]);
    translate([0, 0, H - 0.01]) cylinder(r = WAIST + GAP, h = 2);
}
// the C's slot, opening toward the back segment (+x)
module slot() translate([0, 0, -1]) linear_extrude(H + 2)
    polygon([[0, 0], [30 * cos(-SLOT), 30 * sin(-SLOT)], [30, 0], [30 * cos(SLOT), 30 * sin(SLOT)]]);

// ---- face and details, on the top ----
ENG = 0.8;    // engraving depth
module engrave2d() {
    // eyes, each with a 1.0 mm highlight left standing (the standard's 0.8 floor)
    for (sg = [-1, 1]) translate([-2.5, sg * 6]) difference() { circle(d = 4.4); translate([-0.8, 0.6 * sg]) circle(d = 1.2); }
    translate([3.5, 0]) offset(r = 0.7) polygon([[-1.4, -1.9], [-1.4, 1.9], [1.1, 0]]);        // nose
    for (sg = [-1, 1]) translate([6.4, sg * 1.5]) difference() { circle(r = 1.7); circle(r = 0.9); translate([-3, -3]) square([3, 6]); }   // mouth
    for (sg = [-1, 1]) for (k = [0 : 2]) translate([3.5 + 1.7 * k, sg * (8.2 + 0.8 * k)]) circle(d = 1.1);   // whisker dots
    for (sg = [-1, 1]) translate([-7, sg * 13.5]) circle(r = 1.8);       // inner ears
    for (sg = [-1, 1]) for (k = [-1 : 1]) translate([87 + 2.0 * k, sg * 24]) circle(d = 1.4);     // toe pads
}
// the shell: a scallop held on the chest, opening toward the head, the arms round it
SHELL = [37, 0];
module shell2d() translate(SHELL) rotate(180) difference() {
    union() {
        intersection() { circle(r = 8); translate([-1.5, -10]) square([20, 20]); }   // the fan
        translate([-1.2, 0]) square([2.6, 5.5], center = true);                     // the hinge
    }
    for (a = [-56 : 28 : 56]) rotate(a) translate([2.6, -0.3]) square([4.6, 0.6]);   // ribs
}
// arms: from the chest's sides, curling in over the shell's sides
module paws2d() for (sg = [-1, 1]) translate([SHELL[0] - 2, sg * 7.6]) scale([1, 0.85]) circle(r = 2.6);
RELIEF = 1.0;

module segment(s) difference() {
    union() {
        intersection() { linear_extrude(H_BODY) seg2d(s); slab(); }
        if (s > 0) translate([JOINTS[s - 1], 0, 0]) {
            pin_solid();
            translate([0, -FIN / 2, 0]) cube([R + GAP_B + 1, FIN, H]);
        }
        if (s == 1) translate([0, 0, H_BODY - 0.01]) linear_extrude(RELIEF) union() { shell2d(); paws2d(); }
    }
    if (s < 8) translate([JOINTS[s], 0, 0]) { bore(); intersection() { slot(); cylinder(r = R + 1, h = 3 * H, center = true); } }
    translate([0, 0, H_BODY - ENG]) linear_extrude(5) engrave2d();
    // the pits the joints sit in: the ring and pin stay at the tested 10 mm
    for (j = JOINTS) translate([j, 0, H]) cylinder(r = R + GAP_B, h = 10);
    if (s == 1) for (sg = [-1, 1]) translate([SHELL[0] - 2, sg * 7.6, H_BODY + RELIEF - 0.5]) linear_extrude(1)
        for (k = [-1, 1]) translate([-1.0, k * 0.9]) square([2.0, 0.5], center = true);     // paw toes
}

// posed: each joint bent by `bend`, for renders and the fit check
module posed(s, b) {
    if (s == 0) segment(0);
    else translate([JOINTS[0], 0, 0]) rotate(b) translate([-JOINTS[0], 0, 0]) posed_from(s, 1, b);
}
module posed_from(s, k, b) {
    if (k == s) segment(s);
    else translate([JOINTS[k], 0, 0]) rotate(b) translate([-JOINTS[k], 0, 0]) posed_from(s, k + 1, b);
}

if (part == "segment") segment(seg);
else if (part == "posed") for (s = [0 : 8]) posed(s, bend);
else for (s = [0 : 8]) segment(s);
echo("joint across", 2 * RO, "disc", R, "segment walls (front arc to back bore):",
     [for (i = [0 : 6]) JOINTS[i + 1] - JOINTS[i] - (R + GAP_B) - (WAIST + BULGE + GAP)]);
