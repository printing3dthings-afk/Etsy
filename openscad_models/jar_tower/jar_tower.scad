// Stacking Jar Tower (2026-11-13): Scott's pick 1A, jars that screw into one another to
// make one column, with a cap on top and a foot below. The thread and seat are the test
// print's, unchanged (jar_tower_coupon.scad): 4 mm pitch, 1.2 deep, 35 deg flanks, a
// 35 deg seat cone that stops each jar and closes the seam. Clearance 0.2 mm, Scott's
// pick from the test ("Number 1 again is the best").
//
// Each jar is the coupon's spigot at the bottom and its mouth at the top, with a closed
// floor and a 2.4 mm wall between. It prints standing on its own teeth, as the spigot
// did. The cap is a spigot with a closed top: it prints upside down, top on the bed, so
// its teeth and cone point up and nothing hangs over air. The foot is a mouth on a
// flared base.
//
//   part = "jar" | "cap" (as printed: upside down) | "cap_up" | "foot" | "tower" (with N)

include <jar_tower_coupon.scad>

part = "tower";
CL = 0.2;           // radial clearance, Scott's pick
N = 4;              // jars in the tower
H_JAR = 64;         // a jar's full height, teeth to rim
WALL = 2.4;
FLOOR = 1.6;
R_IN = R_OUT - WALL;                       // 33.6
CREST = TH_R - TH_D + CL;                  // the mouth's thread crests, 32.8
MOUTH_Z = H_JAR - H_MOUTH;                 // where the mouth's 12 mm starts
CAP_BODY = 8;
FOOT_FLOOR = 3;
FOOT_FLARE = 5;     // the foot's skirt reaches 5 mm past the jars at the bed
CAP_GRIP = 24;      // grooves round the cap's side

// the jar's inside, as a profile: up the spigot's bore from the floor, out along a 35 deg
// cone that keeps 2.4 from the spigot's seat cone, up the wall, then in along another
// cone to the mouth's crests (an inward step there would be a ledge over air)
Z_OUT0 = SEAT_Z - TH_D / TA;               // the seat cone's foot, outside
Z1 = Z_OUT0 + (WALL - 2.0) / TA;           // the inner cone's foot: 2.4 across from it
Z2 = Z1 + (R_IN - SP_IN) / TA;
Z3 = MOUTH_Z - 1 - (R_IN - CREST) / TA;
module cavity() rotate_extrude() polygon([[0, FLOOR], [SP_IN, FLOOR], [SP_IN, Z1], [R_IN, Z2], [R_IN, Z3],
                                          [CREST, MOUTH_Z - 1 + 0.01], [0, MOUTH_Z - 1 + 0.01]]);

// the spigot's outside: the teeth with their lead-in (thread() is solid from the axis),
// the seat cone. A root cylinder 0.01 off the thread's own root made sliver faces and
// an open mesh (2026-11-13).
module spigot_outside(top) union() {
    intersection() {
        thread(TH_R, TH_H);
        cylinder(h = TH_H, r1 = TH_R - TH_D + 0.01, r2 = TH_R - TH_D + TH_H * TA);
    }
    rotate_extrude() polygon([[0, Z_OUT0 - 0.01], [TH_R - TH_D, Z_OUT0], [R_OUT, CONE_TOP], [R_OUT, top], [0, top]]);
}
// the mouth's cuts at the top of a part whose rim is at h (the coupon's, moved up)
module mouth_cuts(h) translate([0, 0, h - H_MOUTH]) {
    translate([0, 0, -1]) cylinder(h = H_MOUTH + 2, r = TH_R - TH_D + CL);
    translate([0, 0, H_MOUTH - CS_DEPTH_C - TH_H - TH_P]) thread(TH_R + CL, TH_H + TH_P + 0.01);
    translate([0, 0, H_MOUTH - CS_DEPTH_C - TH_D / TA]) cylinder(h = CS_DEPTH_C + TH_D / TA + 0.01, r1 = TH_R - TH_D + CL, r2 = CS_R);
}
CS_DEPTH_C = (CS_R - (TH_R + CL)) / TA;

module jar() difference() {
    spigot_outside(H_JAR);
    cavity();
    mouth_cuts(H_JAR);
}

// the cap, upright: a spigot, the cone, CAP_BODY of grip, a closed top. The spigot's
// bore stays open below (it's inside the jar) and stops 1.6 under the top.
CAP_H = CONE_TOP + CAP_BODY;
module cap_up() difference() {
    spigot_outside(CAP_H);
    translate([0, 0, -1]) cylinder(r = SP_IN, h = CAP_H - FLOOR + 1);
    for (k = [0 : CAP_GRIP - 1]) rotate(k * 360 / CAP_GRIP)
        translate([R_OUT - 0.6, -0.5, CONE_TOP + 1.2]) cube([2, 1.0, CAP_BODY]);       // grip grooves, open at the top
}
module cap_print() translate([0, 0, CAP_H]) rotate([180, 0, 0]) cap_up();

// the foot: a mouth on a flared skirt (the skirt widens downward: nothing overhangs)
FOOT_H = FOOT_FLOOR + H_MOUTH;
module foot() difference() {
    rotate_extrude() polygon([[0, 0], [R_OUT + FOOT_FLARE, 0], [R_OUT + FOOT_FLARE, 1.2], [R_OUT, 1.2 + FOOT_FLARE / TA],
                              [R_OUT, FOOT_H], [0, FOOT_H]]);
    mouth_cuts(FOOT_H);
}

// ---- the tower, assembled: each part seated on the one below, its thread's phase
// following, as the coupon's seated() places a spigot in a mouth
SEAT_C = H_MOUTH - CS_DEPTH_C - CL / TA - SEAT_Z;      // spigot base above a mouth's start
Z0_C = H_MOUTH - CS_DEPTH_C - TH_H - TH_P;
TURN = 360 * (SEAT_C - Z0_C) / TH_P;
function base_z(k) = (FOOT_H - H_MOUTH) + SEAT_C + k * (MOUTH_Z + SEAT_C);   // jar k's bottom (k = 0 lowest)
module tower() {
    color("white") foot();
    for (k = [0 : N - 1]) translate([0, 0, base_z(k)]) rotate((k + 1) * TURN) jar();
    translate([0, 0, base_z(N)]) rotate((N + 1) * TURN) cap_up();
}

if (part == "jar") jar();
else if (part == "cap") cap_print();
else if (part == "cap_up") cap_up();
else if (part == "foot") foot();
else if (part == "tower") tower();
echo("H_JAR", H_JAR, "CAP_H", CAP_H, "FOOT_H", FOOT_H, "tower height", base_z(N) + CAP_H,
     "jar volume ml approx", PI * R_IN * R_IN * (Z3 - Z2) / 1000 + PI * SP_IN * SP_IN * (Z1 - FLOOR) / 1000);
