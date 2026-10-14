// Victorian horse sleigh (2026-10-13), third attempt at the horse. Scott: "Try
// the horse again. See if there is a way you haven't seen yet."
//
// Three printed pieces: the horse in two halves, and the sleigh on its snow.
//
// Printed standing, a horse has to tuck its muzzle into its chest and close
// its belly into a point, and it stops looking like a horse (two studies,
// horse_study.scad). So this one is not printed standing. It is split down its
// spine and each half printed lying on its cut face, then the halves glued
// on two 1.75 mm filament dowels. Lying flat, each half is a relief: every
// surface faces up or out, so the muzzle, slim legs, the open belly and a
// tail hanging free all print with no support.
//
// The one rule the split brings: along any line across the horse (in y), the
// solid must run unbroken from the spine plane out. So the legs reach the
// spine plane through a thin inner edge (from the front, a V between each
// pair), the forelock fills between the ears, and the harness lies on the
// body.
//
// The sleigh stands on the snow and prints upright like the other accessories:
// a red cutter with a swan-neck dash, slate runners that sweep up at the front
// to meet the horse's traces, a green cushion and presents in the tub. A drift
// under it carries its floor. The horse stands in shallow sockets in the snow
// in front of it, glued.
//
// part  = body | roof | trim | accent | union | all
// piece = horse (whole, standing, for renders) | near | far (the halves, lying
//         flat on their cut faces) | sleigh (the sleigh on its snow) | scene
part = "all";
piece = "scene";
half = piece == "near" ? 1 : piece == "far" ? -1 : 0;
SH = 1.2;
zb = 3.2;                   // the snow's top, where the hooves stand
$fn = 30;                   // 4k + 2: a sphere then has a ring on its equator, so the cut face is square

module ball(p, r) translate(p) sphere(r);
module egg(p, s) translate(p) scale(s) sphere(1);

// ---- the horse, standing, facing +x -------------------------------------------------------------
module barrel() hull() {
    egg([8.2, 0, 14.6], [4.0, 3.9, 4.6]);       // chest
    egg([1.5, 0, 14.4], [5.6, 4.7, 4.9]);       // belly
    egg([-6.6, 0, 15.0], [4.8, 4.5, 4.8]);      // flank
    ball([-8.4, 0, 17.2], 3.9);                 // rump
    ball([5.8, 0, 18.0], 3.0);                  // withers
    egg([-1.0, 0, 18.2], [5.0, 3.6, 2.0]);      // back
}
NECK = [[7.8, 16.0, 3.7], [10.4, 20.6, 2.9], [12.2, 24.2, 2.4], [13.4, 26.6, 2.1]];
module neck() {
    for (i = [0 : len(NECK) - 2]) hull() { ball([NECK[i][0], 0, NECK[i][1]], NECK[i][2]); ball([NECK[i + 1][0], 0, NECK[i + 1][1]], NECK[i + 1][2]); }
    hull() { ball([7.2, 0, 18.4], 2.8); ball([10.6, 0, 23.4], 2.2); ball([13.0, 0, 26.8], 1.9); }   // the crest's arch
}
module head() {
    hull() {
        ball([13.6, 0, 26.6], 2.0);             // poll
        egg([15.6, 0, 26.2], [1.9, 1.7, 1.8]);  // forehead
        egg([14.6, 0, 23.9], [2.2, 1.8, 2.1]);  // cheek
        egg([18.6, 0, 23.4], [1.6, 1.25, 1.4]); // face
        egg([19.9, 0, 22.4], [1.3, 1.3, 1.25]); // muzzle
    }
    // ears, joined at the spine plane all the way up: a gap between them
    // would float in the print. The forelock runs forward from them.
    hull() for (s = [-1, 1]) { ball([13.4, s * 0.8, 28.2], 0.75); translate([13.0, s * 0.7, 30.2]) sphere(0.62, $fn = 16); }
    hull() { ball([13.6, 0, 28.0], 0.8); ball([14.9, 0, 27.6], 0.6); }
}
// a leg: joints [x, z, r]; its tube at y = s * LY, carried to the spine plane
// by an inner edge 1.2 wide (front view: a V between each pair), and kept to
// its own side. Touching the plane at a line, each leg stood on a hairline in
// the print and left zero-width slivers in the other half (2026-10-13).
LY = 1.45;
module own(s) intersection() { children(); side(s); }
module leg(J, s) own(s) for (i = [0 : len(J) - 2]) hull() for (j = [J[i], J[i + 1]]) {
    ball([j[0], s * LY, j[1]], j[2]);
    ball([j[0], 0, j[1]], 0.6);
}
// stride: the near foreleg reaches forward, the far one is under him; the
// near hind leg pushes back. Hooves end flat at the snow.
FORE_N = [[8.6, 12.0, 1.7], [9.6, 6.8, 1.15], [10.6, 4.4, 0.95], [11.0, zb + 0.9, 1.0]];
FORE_F = [[7.8, 12.0, 1.7], [7.9, 6.8, 1.15], [8.0, 4.4, 0.95], [8.1, zb + 0.9, 1.0]];
HIND_N = [[-7.4, 12.8, 2.3], [-9.2, 7.8, 1.2], [-9.6, 4.4, 0.95], [-10.0, zb + 0.9, 1.0]];
HIND_F = [[-6.8, 12.8, 2.3], [-7.6, 7.8, 1.2], [-7.0, 4.4, 0.95], [-6.8, zb + 0.9, 1.0]];
LEGS = [[FORE_N, 1], [FORE_F, -1], [HIND_N, 1], [HIND_F, -1]];
// each half carries only its own legs: the far ones touch the spine plane and
// left zero-thickness sheets in it
function mine(s) = half == 0 || s == half;
module legs() for (l = LEGS) if (mine(l[1])) leg(l[0], l[1]);
// hooves and their white feathers: a skirt from the fetlock to the snow
SK = 0.6;                   // the hooves stand this deep in their sockets
module hoof2d(J, s) let (f = J[len(J) - 1]) intersection() {
    hull() { translate([f[0], s * LY]) circle(1.45); translate([f[0], 0]) circle(0.6); }
    translate([-50, s > 0 ? 0 : -100]) square(100);
}
module hoof(J, s) let (f = J[len(J) - 1]) own(s) hull() {
    translate([f[0], s * LY, zb - SK]) cylinder(r = 1.45, h = 0.7 + SK);
    translate([f[0], 0, zb - SK]) cylinder(r = 0.6, h = 0.7 + SK);
}
module feather(J, s) let (f = J[len(J) - 1], k = J[len(J) - 2]) own(s) hull() {
    translate([f[0], s * LY, zb + 0.6]) cylinder(r1 = 1.7, r2 = 1.2, h = 1.6);
    translate([k[0], s * LY, k[1] - 0.4]) sphere(1.05);
    translate([f[0], 0, zb + 0.6]) cylinder(r = 0.6, h = 1.6);
    translate([k[0], 0, k[1] - 0.4]) sphere(0.6);
}
module tail() {
    hull() { ball([-11.2, 0, 18.4], 1.3); ball([-12.6, 0, 15.6], 1.25); }
    hull() { ball([-12.6, 0, 15.6], 1.25); ball([-12.9, 0, 11.4], 1.05); ball([-12.5, 0, 9.6], 0.9); }
}
module mane() for (i = [0 : len(NECK) - 2]) hull() for (b = [NECK[i], NECK[i + 1]])
    egg([b[0] - 0.7 * b[2], 0, b[1] + 0.72 * b[2]], [0.9, 0.7, 0.9]);
module blaze() hull() { egg([16.2, 0, 27.4], [0.8, 0.65, 0.8]); egg([20.5, 0, 23.0], [0.8, 0.65, 0.8]); }

// harness: a collar round the neck's foot, a strap over the back, traces
// along each flank
module collar() translate([9.0, 0, 18.2]) rotate([0, 36, 0]) scale([1, 1, 0.9]) rotate_extrude($fn = 40) translate([3.15, 0]) circle(1.1, $fn = 20);
// both scaled about the barrel's middle, so they stand evenly proud of it all
// round: scaled about the origin, the girth ran out to a knife edge under the
// belly (2026-10-13)
module proud(k) translate([1.0, 0, 14.6]) scale(k) translate([-1.0, 0, -14.6]) barrel();
module saddle() intersection() {
    proud(1.07);
    translate([-1.6, -10, 0]) cube([3.0, 20, 40]);
}
module traces() for (s = [-1, 1]) intersection() {
    proud(1.06);
    translate([-14, s > 0 ? 0 : -20, 12.9]) cube([24, 20, 1.4]);
}

module horse(p) {
    if (p == "roof") { barrel(); neck(); head(); legs(); tail(); mane(); for (l = LEGS) if (mine(l[1])) hoof(l[0], l[1]); }
    if (p == "trim") { blaze(); for (l = LEGS) if (mine(l[1])) feather(l[0], l[1]); }
    if (p == "accent") collar();
    if (p == "body") { saddle(); traces(); }
}

// ---- the halves ---------------------------------------------------------------------------------
// dowel holes, 1.95 mm for 1.75 mm filament, 2.4 deep into each half
DOWELS = [[-3.0, 14.4], [5.0, 15.0]];
module dowels() for (d = DOWELS) translate([d[0], 0, d[1]]) rotate([90, 0, 0]) cylinder(r = 0.975, h = 4.8, center = true, $fn = 20);
module side(s) translate([-50, s > 0 ? 0 : -100, -50]) cube(100);
module lay(s) if (s > 0) rotate([90, 0, 0]) children(); else rotate([-90, 0, 0]) children();

// ---- the sleigh, on its snow, behind the horse ---------------------------------------------------
include <../accessory_lib.scad>
// side profile (x, z) of the body: a low tub, the dash curling up at the front,
// the seat's back at the rear. Every face that looks down leans no more than
// 32 deg off upright, and the front stands upright until the sides' flare
// ends: leaning over the flare, the two slopes added up past 45 (2026-10-14).
XF = -14.2;                 // the dash's front, clear of the tail
BODY = [[-39.4, 6.0], [-16.4, 6.0], [-16.4, 8.4], [-15.4, 10.0], [-14.6, 12.6], [XF, 15.6], [-14.4, 18.0], [-15.3, 19.0],
        [-16.4, 18.6], [-17.1, 15.6], [-17.6, 11.4], [-20.5, 10.6], [-27.5, 10.0], [-33.5, 11.4], [-37.0, 15.0],
        [-38.4, 16.6], [-39.6, 16.6], [-40.2, 15.2], [-40.4, 9.0]];
BW = 6.4;                   // the body's half-width above its flare
FL = 2.0;                   // the flare, out from the drift's top at 40 deg
module body_front2d() polygon([[-(BW - FL), 6.0], [BW - FL, 6.0], [BW, 6.0 + FL * SH], [BW, 30], [-BW, 30], [-BW, 6.0 + FL * SH]]);
module xslab(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
module yslab(t) rotate([90, 0, 0]) linear_extrude(t, center = true) children();
module tub() difference() {
    intersection() { yslab(2 * BW + 1) polygon(BODY); xslab(-41, -13) body_front2d(); }
    xslab(-38.4, -17.8) offset(delta = -1.4) body_front2d();   // walls 1.4: at 1.2 they measured a hair under
}
// the rim: the body's top edge in white, 0.8 deep, flush
module rim() intersection() { tub(); difference() { yslab(2 * BW + 2) polygon(BODY); translate([0, 0, -0.8]) yslab(2 * BW + 3) polygon(BODY); } }
// runners: a bar along the snow, sweeping up at 18 deg to the traces' ends
RY0 = 4.95; RY1 = 6.65;     // inner and outer faces; the traces end at y 4.85. 1.7 thick:
                            // at 1.4 the sweeps, free at the top, were fragility's "watch" (2026-10-14)
RUN = [[-38.0, 2.4], [-15.2, 2.4], [-11.4, 12.6], [-11.0, 14.3], [-11.6, 15.0], [-12.6, 14.8], [-14.0, 13.0],
       [-17.4, 4.0], [-37.6, 4.0], [-38.4, 3.4]];   // the tails kept on the snow: past it, where the oval narrows, they hung off its edge
module runners() for (m = [0, 1]) mirror([0, m, 0]) translate([0, RY0, 0]) rotate([90, 0, 0]) mirror([0, 0, 1]) linear_extrude(RY1 - RY0) polygon(RUN);
// posts from the runners up under the body's flare
module posts() for (m = [0, 1], x = [-37, -29, -21]) mirror([0, m, 0]) translate([x, (RY0 + RY1) / 2, 3.9]) cylinder(r = 0.75, h = 4.3);
// snow banked under the sleigh, carrying its floor
module bank() hull() {
    translate([-39.0, -(BW - FL) - 1.4, zb - 0.3]) cube([23.6, 2 * (BW - FL) + 2.8, 0.01]);   // off the base's rounded edge
    translate([-39.4, -(BW - FL), 6.0 - 0.01]) cube([23.0, 2 * (BW - FL), 0.02]);
}
// the cushion, green, against the seat's back
module cushion() {
    // flush with the tub's back wall: 0.1 into it, the wall kept a red sliver
    // a layer thick that the printer dropped (2026-10-14)
    translate([-38.4, -5.1, FLOOR]) cube([6.1, 10.2, 2.8]);
    translate([-38.4, -5.1, 9.8]) cube([1.5, 10.2, 4.2]);
}
// presents: [x, y, size, height, box colour, ribbon colour]
GIFTS = [[-24.6, -1.6, 5.0, 5.0, "trim", "accent"], [-20.6, 2.3, 3.8, 3.8, "accent", "trim"],
         [-29.0, 2.4, 3.6, 3.2, "roof", "body"], [-24.6, -1.6, 3.0, 2.4, "accent", "trim"]];
// they stand on a layer line inside the tub's floor (7.4): set over it they
// floated, and set at 7.3 they split the 7.2-7.4 layer between red and green,
// and the slicer dropped the red (2026-10-14)
FLOOR = 7.2;
function gz(i) = i == 3 ? FLOOR + GIFTS[0][3] : FLOOR;
module gift(i) let (g = GIFTS[i]) translate([g[0], g[1], gz(i)]) translate([-g[2] / 2, -g[2] / 2, 0]) cube([g[2], g[2], g[3]]);
module ribbon(i) let (g = GIFTS[i], w = 1.3, t = 0.25) translate([g[0], g[1], gz(i)]) {
    translate([-g[2] / 2 - t, -w / 2, 0]) cube([g[2] + 2 * t, w, g[3] + t]);
    translate([-w / 2, -g[2] / 2 - t, 0]) cube([w, g[2] + 2 * t, g[3] + t]);
    // the bow: two loops standing on the lid, kept 0.1 inside its edge. Set on
    // the ribbon, 0.25 up, and out past the edge, they hung over both (2026-10-14)
    let (c = min(1.1, g[2] / 2 - 0.8)) for (m = [0, 1]) mirror([m, 0, 0]) hull() {
        translate([0.3, 0, g[3] - 0.01]) cylinder(r = 0.65, h = 1.05, $fn = 14); translate([c, 0, g[3] - 0.01]) cylinder(r = 0.7, h = 1.25, $fn = 14); }
}
module gifts(c) for (i = [0 : len(GIFTS) - 1]) { if (GIFTS[i][4] == c) gift(i); if (GIFTS[i][5] == c) ribbon(i); }
// the snow: an oval round both, the hooves' sockets in front, the mark under
module base2d() translate([-9.6, 0]) scale([1, 12.4 / 35]) circle(r = 35, $fn = 120);
module base2d_in() offset(delta = -2.4) base2d();
module snow() difference() {
    union() {
        snow_base(zb) base2d();
        bank();
        clip_to() { union() { drift([-34, -9.4, zb], [5, 2.2, 1.0]); drift([16, 8.6, zb], [5, 2.0, 0.9]); } base2d_in(); }
    }
    for (l = LEGS) translate([0, 0, zb - SK]) linear_extrude(SK + 1) offset(delta = 0.15) hoof2d(l[0], l[1]);
    brand_mark([-12, 0], 5.0);
}
module sleigh(p) {
    if (p == "body") tub();
    if (p == "roof") { runners(); posts(); gifts("roof"); }
    if (p == "trim") { snow(); rim(); gifts("trim"); }
    if (p == "accent") { cushion(); gifts("accent"); }
    if (p == "body") gifts("body");
}

module raw(p) {
    if (piece == "horse") horse(p);
    else if (piece == "sleigh") sleigh(p);
    else if (piece == "scene") { horse(p); sleigh(p); }
    else lay(half) difference() {
        intersection() { horse(p); side(half); }
        if (p == "roof") dowels();
    }
}
emit();
