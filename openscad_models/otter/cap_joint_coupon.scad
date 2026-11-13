// Capped joint test (2026-11-13): the otter's joint with the cap that hides it
// (cap_joint.scad), at its real size, before the otter is built round it (mechanism
// handbook section 7, step 5).
//
// Two pairs on one plate. Each is two segment ends cut the way the otter's will be:
// the front one owns the C-ring, a disc round the joint and the body behind it; the
// back one owns the pin, its fin and the cap, and the body in front of it. V cuts at
// the sides let them swing. The joint under the cap is the tested 0.30 one in both;
// only the cap's cone gap differs:
//   one notch on the back block = 0.30 (the same as the joint's own cones)
//   two notches                 = 0.40
//
//   part = "plate" | "front" | "back" (with variant, as printed) | "swung" (variant, ang)

include <cap_joint.scad>

part = "plate";
variant = 0;
ang = 0;
$fn = 72;

CAP_GAPS = [0.30, 0.40];
HALF_W = 13;          // the blocks are 26 wide
LEN    = 14;          // and reach this far either side of the joint (24 took 53 min)
V_HALF = 12;
PITCH  = 34;

module wedge(a0, a1) polygon(concat([[0, 0]], [for (a = [a0 : (a1 - a0) / 24 : a1]) 60 * [cos(a), sin(a)]]));
module block2d(x0, x1) translate([x0, -HALF_W]) square([x1 - x0, 2 * HALF_W]);

module front(v) difference() {
    linear_extrude(TOP) intersection() {
        block2d(-LEN, R + 1);
        union() { wedge(90 + V_HALF, 270 - V_HALF); circle(r = R); }
    }
    bore(CAP_GAPS[v]);
    slot();
    disc_trim(CAP_GAPS[v], V_HALF);
}
module back(v) difference() {
    union() {
        linear_extrude(TOP) intersection() {
            block2d(-R - 1, LEN);
            difference() { wedge(-90 + V_HALF, 90 - V_HALF); circle(r = R + GAP_B); }
        }
        pin_parts();
    }
    // notches across the back block's top: 1 = 0.30, 2 = 0.40
    for (k = [0 : v]) translate([LEN - 4 - k * 2.4, -HALF_W - 1, TOP - 0.8]) cube([1.0, 2 * HALF_W + 2, 2]);
}

if (part == "front") translate([0, variant * PITCH, 0]) front(variant);
else if (part == "back") translate([0, variant * PITCH, 0]) back(variant);
else if (part == "swung") translate([0, variant * PITCH, 0]) { front(variant); rotate(ang) back(variant); }
else for (v = [0 : 1]) translate([0, v * PITCH, 0]) { front(v); back(v); }
echo("TOP", TOP, "CAP_R", CAP_R, "cap cone", CAP_CONE);
