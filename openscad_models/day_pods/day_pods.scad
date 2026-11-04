// Day Pods: a weekly pill box of seven pods (2026-11-04).
// Scott's pick, form B of four: "seven separate pods, each with a sliding lid,
// that slide into a stand in day order. You take one day's pod with you."
//
// Practice in sliding fits, the one mechanism the fit test plate doesn't
// cover. Two of them:
//   the lid   slides forward out of grooves along the top of the pod's side
//             walls. Its edges are bevelled 30 deg, so the wall over them
//             holds it down and prints without support. A ridge under its
//             front clicks over the pod's front wall: closed, it stays shut in
//             a bag.
//   the pod   slides down onto an upright dovetail rail on the stand's back
//             wall. Pulled forward it is held; lifted, it comes straight off.
//
// Prints, no supports, no glue:
//   pod      x7, upright, open at the top; the cavity's floor rounds up into
//            the walls, so no pill lodges in a corner
//   lid      x7, upside down: the day (MO TU WE TH FR SA SU) is engraved into
//            the face on the plate, and the ridge prints on top
//   stand    the base and its back wall with seven rails, upright
//   coupon   the lid's slide at three clearances, to tune CLR after one print
//
//   part = pod | lid_<0..6> | stand | coupon | pods_plate | lids_plate |
//          pod_use | lid_use | stand_use (in place) | all
use <../brand/obc_mark.scad>

part = "all";
$fn = 64;

CLR = 0.2;                  // the sliding clearance each side: tune with the coupon
// ---- a pod ----------------------------------------------------------------------------------------
IN_W = 26; IN_D = 28; IN_H = 17;        // the cavity
FLOOR = 1.6;
WALL_S = 3.0;               // the side walls: the lid's groove leaves 1.4 outside it
WALL_F = 1.6;               // the front wall, under the lid
BACK = 3.8;                 // the back wall: 1.4 between the lid's slide and the stand's groove
R_IN = 4;                   // the cavity's corners and its floor's round
R_OUT = 3;                  // the pod's upright corners
W_OUT = IN_W + 2 * WALL_S;  // 32
D_OUT = IN_D + WALL_F + BACK;           // 33.2
// ---- the lid ---------------------------------------------------------------------------------------
LT = 2.4; LV = 1.4;         // its thickness, and the upright band at its edge before the bevel:
                            // at 1.2 the band read as walls a hair under the 1.2 floor
E = 1.4;                    // how far each edge runs into the wall
BEV = (LT - LV) * tan(30);  // the bevel's inset: 30 deg off upright, 0.69
B = IN_W / 2 + E;           // the lid's half-width at its foot, 14.4
LB = FLOOR + IN_H;          // the lid's underside, 18.6
CAP = 1.2;                  // the walls stand this far over the groove: no knife edge
H = LB + LT + CLR + CAP;    // the pod's height, 23.4
OVER = 2.0;                 // the lid runs past the pod's front, to push it by
TUCK = 0;                   // into the back wall: at 1.0 it left 0.2 against the stand's groove;
                            // the side grooves hold the lid without it
RIDGE_H = 0.4; RIDGE_W = 2.0; RIDGE_L = 9;   // the click
// ---- the stand -----------------------------------------------------------------------------------
N = 7;
GAP = 1.2;                  // between pods
PITCH = W_OUT + GAP;
BASE_T = 3.0;
SPINE_T = 3.0; SPINE_H = 16;            // the back wall, over the base
SG = 0.3;                   // the pod's back to the spine's face
M = 6; G = 2.0;             // the dovetail's mouth and depth
DT = M + 2 * G * tan(30);   // its width inside, 8.31
STAND_L = N * PITCH + 4;
STAND_D = D_OUT + SG + SPINE_T + 1;
DAYS = ["MO", "TU", "WE", "TH", "FR", "SA", "SU"];

module rbox(w, d, h, r) linear_extrude(h) offset(r = r) square([w - 2 * r, d - 2 * r], center = true);

// the lid's section across the slide (x, z), from its underside at z = 0, grown by c
module lid2d(c = 0) offset(delta = c) polygon([[-B, 0], [B, 0], [B, LV], [B - BEV, LT], [-(B - BEV), LT], [-B, LV]]);
// the stand's rail in plan (x across, y out from the spine's face), grown by c
module dove2d(c = 0) offset(delta = c) polygon([[-M / 2, -0.01], [M / 2, -0.01], [DT / 2, G], [-DT / 2, G]]);

// ---- the pod, in place: its foot at z = 0, its front at -y ---------------------------------------------
module cavity() let (x = IN_W / 2 - R_IN, y0 = -D_OUT / 2 + WALL_F + R_IN, y1 = D_OUT / 2 - BACK - R_IN)
    hull() for (px = [-x, x], py = [y0, y1]) {
        translate([px, py, FLOOR + R_IN]) sphere(r = R_IN);
        translate([px, py, LB - 0.01]) cylinder(r = R_IN, h = 1);
    }
module pod_use() difference() {
    rbox(W_OUT, D_OUT, H, R_OUT);
    cavity();
    // the lid's slide: open at the front, into the back wall by TUCK
    translate([0, D_OUT / 2 - BACK + TUCK + CLR, LB]) rotate([90, 0, 0]) linear_extrude(D_OUT) lid2d(CLR);
    // over the lid: open between the walls' caps, which keep 1.2 over its bevel
    translate([0, -1, LB + LT]) linear_extrude(H) square([2 * (B - BEV + CLR), D_OUT + 2], center = true);
    // the front wall stops under the lid. Its top edge is left square: the
    // ridge is round and rides over it, and a chamfer there cut slivers into
    // the cavity's rounded corners (2026-11-04)
    translate([0, -D_OUT / 2 - 1, LB - CLR]) linear_extrude(H) square([2 * (B + CLR), 2 * (WALL_F + 1)], center = true);
    // the groove the stand's rail slides up into, the whole height of the back
    translate([0, D_OUT / 2, -1]) mirror([0, 1, 0]) linear_extrude(H + 2) dove2d(CLR);
}

// ---- a lid, in place over its pod: z = 0 at its underside, its back tucked in -------------------------
LID_L = IN_D + WALL_F + OVER + TUCK;
module lid_use(k) let (y0 = -D_OUT / 2 - OVER) difference() {
    union() {
        translate([0, y0, 0]) rotate([-90, 0, 0]) mirror([0, 1, 0]) linear_extrude(LID_L) lid2d();
        // the click: a low round ridge under the lid, just inside the front
        // wall when it is shut
        translate([-RIDGE_L / 2, -D_OUT / 2 + WALL_F + CLR + RIDGE_W / 2, 0]) rotate([90, 0, 90])
            linear_extrude(RIDGE_L) let (r = (RIDGE_W * RIDGE_W / 4 + RIDGE_H * RIDGE_H) / (2 * RIDGE_H))
                intersection() {
                    translate([0, r - RIDGE_H]) circle(r = r, $fn = 96);
                    translate([-RIDGE_W, -RIDGE_H - 0.01]) square([2 * RIDGE_W, RIDGE_H + 0.02]);
                }
    }
    // the day, engraved 0.6 into the top; any gap under 1.2 between strokes
    // closed, so no sliver of lid stands between them
    translate([0, 2, LT - 0.6]) linear_extrude(1) offset(r = -0.6) offset(r = 0.6)
        text(DAYS[k], size = 7, font = "Montserrat:style=ExtraBold", halign = "center", valign = "center");
    // three finger grooves at the front, for a thumb to push, 1.6 of lid between them
    for (i = [0 : 2]) translate([0, y0 + 1.6 + i * 2.4, LT - 0.4]) linear_extrude(1) square([14, 0.8], center = true);
}

// ---- the stand ---------------------------------------------------------------------------------------
function pod_x(i) = (i - (N - 1) / 2) * PITCH;
SPINE_Y = D_OUT / 2 + SG;   // the spine's face
module stand_use() difference() {
    union() {
        translate([0, (STAND_D) / 2 - D_OUT / 2 - 1, 0]) rbox(STAND_L, STAND_D, BASE_T, 3);
        translate([-STAND_L / 2, SPINE_Y, 0]) cube([STAND_L, SPINE_T, BASE_T + SPINE_H]);
        // each rail's dovetail starts at the pod's back, the same plane as its
        // groove's mouth, and a straight neck crosses the gap to the spine: from
        // the spine's face, the gap ate the dovetail's clearance
        for (i = [0 : N - 1]) translate([pod_x(i), 0, BASE_T - 0.01]) linear_extrude(SPINE_H + 0.01) {
            translate([0, D_OUT / 2]) mirror([0, 1]) dove2d();
            translate([-M / 2, D_OUT / 2 - 0.01]) square([M, SG + 0.02]);
        }
    }
    translate([0, 8, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
}

// ---- the coupon: the lid's slide at three clearances -------------------------------------------------
CPN = [0.1, 0.2, 0.3];
module coupon() for (j = [0 : 2]) translate([j * 38 - 38, 0, 0]) {
    // a block with the slide cut at its clearance, the number engraved on its front
    difference() {
        translate([0, 0, 0]) rbox(2 * B + 6, 20, LV + 2 + LT + CAP, 1);
        translate([0, 11, 2]) rotate([90, 0, 0]) linear_extrude(22) lid2d(CPN[j]);
        translate([0, -1, 2 + LT]) linear_extrude(10) square([2 * (B - BEV + CPN[j]), 24], center = true);
        // its clearance as dots on the cap, one per tenth of a millimetre
        for (d = [0 : j]) translate([B + 1.6, -6 + d * 3, LV + 2 + LT + CAP - 0.6]) cylinder(d = 1.6, h = 1);
    }
    // its lid stub, upside down beside it
    translate([0, 22, LT]) mirror([0, 0, 1]) rotate([90, 0, 0]) linear_extrude(18, center = true) lid2d();
}

// ---- plates ------------------------------------------------------------------------------------------
module pods_plate() for (i = [0 : N - 1]) translate([((i % 4) - 1.5) * (W_OUT + 6), (floor(i / 4) - 0.5) * (D_OUT + 6), 0]) pod_use();
module lid_print(k) translate([0, 0, LT]) mirror([0, 0, 1]) lid_use(k);
module lids_plate() for (k = [0 : N - 1]) translate([((k % 4) - 1.5) * (2 * B + 6), (floor(k / 4) - 0.5) * (LID_L + 6), 0]) lid_print(k);

assert(W_OUT / 2 - (B + CLR) >= 1.2, "the side wall outside the lid's groove is under 1.2");
assert(BACK - G - CLR - TUCK - CLR >= 1.2, "the back wall between the lid's slide and the rail's groove is under 1.2");
assert(STAND_L <= 250, "the stand is longer than the plate");

WHITE = "#F4F1EA"; LILAC = "#B79CE0";
if (part == "pod" || part == "pod_use") pod_use();
else if (part == "stand" || part == "stand_use") stand_use();
else if (part == "coupon") coupon();
else if (part == "pods_plate") pods_plate();
else if (part == "lids_plate") lids_plate();
else if (part == "lid_use") lid_use(0);
else if (part == "all") {
    color(WHITE) stand_use();
    for (i = [0 : N - 1]) translate([pod_x(i), 0, BASE_T]) {
        color(WHITE) pod_use();
        color(LILAC) translate([0, 0, LB]) lid_use(i);
    }
}
for (k = [0 : N - 1]) if (part == str("lid_", k)) lid_print(k);
echo("W_OUT", W_OUT, "D_OUT", D_OUT, "H", H, "STAND_L", STAND_L, "LID_L", LID_L, "PITCH", PITCH);
