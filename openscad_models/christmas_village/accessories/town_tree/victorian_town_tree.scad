// Victorian town Christmas tree (2026-10-14), a village accessory from the
// second batch of studies (../concepts/accessories2_scene.jpg).
//
// The town's tree on an octagonal brick plinth with a stone cap: five tiers
// of boughs, snow along each tier's edge, red baubles, a white star on top,
// and presents in the snow round the plinth. On a soft blob of snow, the
// maker's mark under it.
//
// Printed upright with no support. Each tier's underside climbs TS per 1 out
// from the tier below it, so a tier stands out from the tree like a skirt; the
// baubles sit on the tiers' tops, sunk to less than half a ball; the star's lower
// points run down into a short funnel onto the tree's tip, and its side points'
// lower edges climb 38.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
MARK = [[0, 0], 5.0];         // the maker's mark: where on the base, its cap height
SH = 1.2;
TS = 1.3;                   // a tier's underside: 1.3 up per 1 out, so a facet's corner still climbs SH
C = 1 / cos(22.5);          // an octagon's corner, per 1 of its flat

zb = 3.2;                   // the snow's top
// ---- the plinth -----------------------------------------------------------------------------------
A_p = 11;                   // its flats
z_w = 8.0;                  // the brick's top
z_c = z_w + 0.8 * SH + 1.2; // the cap's top
module oct_rev() rotate([0, 0, 22.5]) rotate_extrude($fn = 8) children();
function cs(pts) = [for (p = pts) [p[0] * C, p[1]]];
ZG = [4.6, 6.6];            // at 5.0 and 6.8 the brick between was 1.16 tall
module plinth() oct_rev() polygon(cs(concat([[0, 2.4], [A_p, 2.4]],
    [for (z = ZG) each [[A_p, z], [A_p - 0.45, z], [A_p - 0.45, z + 0.1], [A_p, z + 0.1 + 0.45 * SH]]],
    [[A_p, z_w + 0.01], [0, z_w + 0.01]])));
module cap() oct_rev() polygon(cs([[0, z_w], [A_p, z_w], [A_p + 0.8, z_w + 0.8 * SH], [A_p + 0.8, z_c], [0, z_c]]));

// ---- the tree ---------------------------------------------------------------------------------------
// tier k: its underside leaves the tier below at r AI[k], climbing TS per 1 out
// to its edge R[k]; a lip LIP tall; its top slopes in TOPS per 1 to where the
// next tier leaves it. The bottom tier stands on the plinth's cap: grown from
// a trunk, its underside was a long cone and the tree read as a spinning top
// (2026-10-14). Twelve-sided, each tier turned 15 deg from the last.
LIP = 1.2;
TOPS = 1.3;                 // the tops' slope, up per 1 in
R = [16, 13, 10.5, 8, 5.5];
AI = [9, 10, 8, 6, 4];      // where each tier leaves the one below (r)
N = len(R);
TIP_R = 1.5;                // the tree's top, under the star
function zedge(k) = zstart(k) + TS * (R[k] - AI[k]);
function zstart(k) = k == 0 ? z_c : zedge(k - 1) + LIP + TOPS * (R[k - 1] - AI[k]);
function ztop(k, r) = zedge(k) + LIP + TOPS * (R[k] - r);     // tier k's top at r
Z_TIP = ztop(N - 1, TIP_R);
// A tier's foot sinks 0.5 into the tier below: turned 15 deg, its corners
// stand over the lower tier's flats, which lie 0.3 under the profile.
function zfoot(k) = zstart(k) - (k == 0 ? 0.01 : 0.5);
module tier(k) rotate([0, 0, 15 * k]) rotate_extrude($fn = 12) polygon(concat(
    [[0, zfoot(k)], [AI[k], zfoot(k)], [R[k], zedge(k)], [R[k], zedge(k) + LIP]],
    k < N - 1 ? [[AI[k + 1] - 0.01, zstart(k + 1) + 0.01], [0, zstart(k + 1) + 0.01]] : [[TIP_R, Z_TIP], [0, Z_TIP]]));
module tree() for (k = [0 : N - 1]) tier(k);

// snow along each tier's edge: 0.8 deep at the edge, nothing SW in. It sinks
// into the tier: lying on it, the two shared faces and the union came open.
SW = [2.5, 2.5, 2.0, 1.8, 1.6];
module snow() for (k = [0 : N - 1]) rotate([0, 0, 15 * k]) rotate_extrude($fn = 12)
    polygon([[R[k] - SW[k], ztop(k, R[k] - SW[k]) - 0.2], [R[k] - 0.2, zedge(k) + LIP - 0.1], [R[k], zedge(k) + LIP], [R[k], zedge(k) + LIP + 0.8]]);

// baubles: on each tier's top, at a facet's corner (where the top is the
// profile, not a flat cut inside it), sunk 0.25 so each is less than half a
// ball, and clear of the snow: one touching the snow's edge left CGAL an open
// edge in the red part (2026-10-14)
BR = [1.25, 1.1, 1.0, 0.95, 0.9];
BAUB = [[0, 0, 11.8], [0, 60, 12.0], [0, 120, 11.6], [0, 180, 12.0], [0, 240, 11.7], [0, 300, 11.9],
        [1, 30, 9.2], [1, 105, 9.3], [1, 165, 9.1], [1, 225, 9.3], [1, 300, 9.2],
        [2, 0, 7.0], [2, 90, 7.0], [2, 180, 7.0], [2, 270, 7.0],
        [3, 45, 5.1], [3, 165, 5.1], [3, 285, 5.1],
        [4, 105, 2.7], [4, 285, 2.7]];
module baubles() for (b = BAUB) let (k = b[0], a = round(b[1] / 30) * 30 + 15 * k, r = b[2])
    rotate([0, 0, a]) translate([r, 0, ztop(k, r) - 0.25]) sphere(BR[k], $fn = 20);

// the star: five fat points, inner ratio 0.6 so the side points' lower edges
// climb 38 deg; its lower points run into a funnel down onto the tree's tip
SR = 4.2;                   // the star's points
ST = 2.4;                   // its thickness, front to back
FW = 0.8;                   // the funnel's foot, half-width
FH = (0.588 * SR - FW) / tan(38);          // the funnel's height
SZ = Z_TIP + 0.6 + FH + 0.809 * SR;        // the star's centre
// its tips rounded 0.5: sharp, each was a sliver under one bead
module star2d() offset(r = 0.5, $fn = 16) offset(delta = -0.5)
    polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, r = i % 2 == 0 ? SR : 0.6 * SR) [r * cos(a), r * sin(a)]]);
// the funnel fills the notch between the lower points too: left open, it was a
// ceiling the slicer propped
module star() rotate([90, 0, 0]) translate([0, 0, -ST / 2]) linear_extrude(ST) {
    translate([0, SZ]) star2d();
    polygon([[-0.588 * SR, SZ - 0.809 * SR], [0, SZ], [0.588 * SR, SZ - 0.809 * SR],
             [FW, Z_TIP + 0.6], [-FW, Z_TIP + 0.6]]);
}
module stem() translate([0, 0, Z_TIP - 0.01]) cylinder(r = 1.5, h = 0.62, $fn = 20);

// ---- presents in the snow round the plinth --------------------------------------------------------
// [angle, r, w, d, h, part]; a ribbon each way, down to the snow, and a bow
GIFTS = [[-100, 17.2, 4.2, 4.2, 3.6, "body"], [-75, 17.6, 3.4, 3.0, 2.8, "accent"], [-123, 17.0, 3.0, 3.0, 4.4, "roof"],
         [40, 17.4, 4.0, 3.6, 3.2, "accent"], [150, 17.4, 3.6, 3.6, 3.0, "body"]];
RW = 0.9;
module gift(g) rotate([0, 0, g[0]]) translate([g[1], 0, zb - 0.3]) children();
module gift_box(g) gift(g) translate([-g[2] / 2, -g[3] / 2, 0]) cube([g[2], g[3], g[4] + 0.3]);
module ribbons(g) gift(g) {
    translate([-g[2] / 2 - 0.3, -RW / 2, 0]) cube([g[2] + 0.6, RW, g[4] + 0.6]);
    translate([-RW / 2, -g[3] / 2 - 0.3, 0]) cube([RW, g[3] + 0.6, g[4] + 0.6]);
    for (s = [-1, 1]) translate([s * 0.7, 0, g[4] + 0.55]) scale([1, 0.8, 0.7]) sphere(0.75, $fn = 16);
}

// ---- the snow -------------------------------------------------------------------------------------
module base2d() circle(r = 23, $fn = 96);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([-16, 10, zb], [4, 3, 1.0]); drift([13, -14, zb], [3.5, 3, 0.9]); } base2d_in(); }
    }
    brand_mark(MARK[0], MARK[1]);
}

module raw(p) {
    if (p == "body") { plinth(); baubles(); for (g = GIFTS) if (g[5] == "body") gift_box(g); }
    if (p == "roof") for (g = GIFTS) if (g[5] == "roof") gift_box(g);
    if (p == "trim") { base(); cap(); snow(); star(); stem(); for (g = GIFTS) ribbons(g); }
    if (p == "accent") { tree(); for (g = GIFTS) if (g[5] == "accent") gift_box(g); }
}
emit();
