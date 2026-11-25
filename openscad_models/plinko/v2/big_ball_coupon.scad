// Plinko: bigger print-in-place balls (2026-11-25). Numbers: big_ball_budget.py.
//
// v1's 5 mm teardrops broke loose during the print. Scott: "The whole thing might need to be
// bigger so the balls have a chance to print correct", and he asked to test that alongside the
// 6 mm BB test. Three pockets under the v1 cage, two 10 mm teardrop balls in each, each ball
// standing on a neck to the floor:
//   one notch    neck 1.6
//   two notches  neck 2.0
//   three        neck 2.4
// After the print, push a toothpick through the cage onto each ball's side to snap its neck.
//
// Printed lying on its back, cage up, as v1. Each ball's point faces the back, so once free it
// rolls about that axis as a true 10 mm circle; the snapped stub stays on the point, off it.
//
//   part = coupon | balls (review)

part = "coupon";
$fn = 64;

R = 5;
TIP = R * sqrt(2);        // the 45 deg point below the ball's centre
NECKS = [1.6, 2.0, 2.4];
NECK_H = 1.0;             // the neck's height above the floor
FLOOR = 1.4;
LAT_T = 1.4; LAT_BAR = 1.4; LAT_OPEN = 3.0; LAT_GAP = 0.8;   // the v1 cage, one layer thicker: at 1.2 the gate
                                                             // read its 1st percentile just under its 1.2 floor
WALL = 1.6;
PW = 26; PH = 13;         // a pocket, inside: two balls 3 apart, 1.5 from the walls
BALL_X = [-6.5, 6.5];
RIBS = [-9.75, -3.25, 3.25, 9.75];

function zc(d) = FLOOR + NECK_H + TIP - d / 2;              // the ball's centre, per neck
D = zc(NECKS[0]) + R + LAT_GAP - FLOOR;                    // inside depth: the tallest ball + gap
Z_TOP = FLOOR + D + LAT_T;
OW = PW + 2 * WALL; OH = 3 * PH + 4 * WALL;
function py(i) = -OH / 2 + WALL + PH / 2 + i * (PH + WALL);   // pocket i's centre y

module ball(d) {
    z = zc(d);
    translate([0, 0, z]) sphere(r = R);
    // the 45 deg cone from the sphere's tangent circle down to the neck
    hull() {
        translate([0, 0, z - R / sqrt(2)]) cylinder(r = R / sqrt(2), h = 0.01);
        translate([0, 0, z - TIP + d / 2]) cylinder(r = d / 2, h = 0.01);
    }
    translate([0, 0, FLOOR - 0.01]) cylinder(d = d, h = NECK_H + 0.02 + 0.01);
}
module pocket2d() square([PW, PH], center = true);
module open2d() difference() {
    intersection() {
        pocket2d();
        for (k = [-3 : 3]) translate([0, k * (LAT_BAR + LAT_OPEN)]) square([200, LAT_OPEN], center = true);
    }
    for (x = RIBS) translate([x, 0]) square([LAT_BAR, 200], center = true);
}
module board() difference() {
    translate([-OW / 2, -OH / 2, 0]) cube([OW, OH, Z_TOP]);
    for (i = [0 : 2]) translate([0, py(i), 0]) {
        translate([0, 0, FLOOR]) linear_extrude(D) pocket2d();
        translate([0, 0, FLOOR + D - 0.01]) linear_extrude(LAT_T + 1) open2d();
        // the variant's notches in the left wall's top edge
        for (k = [0 : i]) translate([-OW / 2 - 1, (k - i / 2) * 3 - 0.6, Z_TOP - 1.2]) cube([WALL + 1.2, 1.2, 2]);
    }
}
module balls() for (i = [0 : 2]) for (x = BALL_X) translate([x, py(i), 0]) ball(NECKS[i]);

if (part == "coupon") union() { board(); balls(); }
else if (part == "balls") balls();
else if (part == "board") board();
echo(D = D, Z_TOP = Z_TOP, OW = OW, OH = OH);
