// Victorian signpost (2026-10-13), a village accessory: Scott's circle round
// the bandstand on the second batch of studies (../concepts/accessories2_scene.jpg)
// took in the signpost too.
//
// A cast-iron fingerpost: a round post on a fluted foot, a collar and an acorn
// finial with snow on it, and three white arms pointing three ways. Each arm
// stands on an iron bracket, a triangle pierced with diamonds, whose sloping
// edge is what lets the arm print: an arm out on its own would be a ledge 11
// mm long over nothing. On a small soft blob of snow, the maker's mark under it.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
MARK = [[0, 0], 4.0];         // the maker's mark: where on the base, its cap height
SH = 1.2;

zb = 3.2;                   // the snow's top
RP = 2.0;                   // the post
ZT = 38;                    // its top
AL = 11;                    // an arm, out from the post's middle
AH = 4.0;                   // its depth
AT = 1.6;                   // its thickness
BT = AT;                    // a bracket's: as the arm's, so no edge of the arm hangs past it
ARMS = [[33, 10], [28, 170], [23, 305]];   // [the arm's foot, the way it points]

// the post: a fluted foot, the shaft, a collar, an acorn
module post() rotate_extrude($fn = 48) polygon([
    [0, 2.4], [3.8, 2.4], [3.8, zb + 0.6], [2.6, zb + 3.2], [2.6, zb + 4.0], [RP, zb + 5.0],
    [RP, ZT], [RP + 0.6, ZT + SH * 0.6], [RP + 0.6, ZT + 2.0], [1.7, ZT + 2.0],
    [1.7, ZT + 2.4], [2.4, ZT + 2.4 + 0.85], [2.4, ZT + 4.0], [0, ZT + 6.2]]);
module flutes() for (i = [0 : 7]) rotate([0, 0, 45 * i]) translate([3.15, 0, zb + 0.4]) cylinder(r = 0.7, h = 2.4, $fn = 12);

module board2d() polygon([[0, 0], [AL, 0], [AL + 1.6, AH / 2], [AL, AH], [0, AH]]);
// The bracket: a triangle from the post out to under the arm's point, its
// edge falling 39 deg from upright, pierced with two diamonds whose sides
// climb at 59 and 58 deg. An open knee brace looked lighter, but the arm then had to
// bridge from the post to the strut, and the slicer would not take that as a
// bridge: 6,762 support moves (2026-10-13).
module bracket2d() let (x0 = RP - 0.5, x1 = AL) difference() {
    polygon([[x0, -11.5], [x1, 0.01], [x0, 0.01]]);
    translate([4.4, -3.3]) polygon([[0, 1.95], [1.2, 0], [0, -1.95], [-1.2, 0]]);
    translate([7.0, -1.8]) polygon([[0, 1.1], [0.7, 0], [0, -1.1], [-0.7, 0]]);   // 1.2 clear of the edge and the first
}
module in_plane(a, z, t) rotate([0, 0, a]) translate([0, 0, z]) rotate([90, 0, 0]) linear_extrude(t, center = true) children();
module arms() for (r = ARMS) in_plane(r[1], r[0], AT) board2d();
module brackets() for (r = ARMS) in_plane(r[1], r[0] + 0.01, BT) bracket2d();

// snow: a cap on the acorn, and a soft heap round the post's foot
module finial_snow() difference() {
    translate([0, 0, ZT + 3.6]) rotate_extrude($fn = 48) polygon([[0, 0], [2.4, 0], [2.6, 0.4], [2.3, 1.3], [1.4, 2.0], [0, 2.3]]);
    post();
}
module heap() translate([0, 0, zb - 0.3]) rotate_extrude($fn = 48) polygon([[0, 0], [6.2, 0], [4.6, 0.9], [3.0, 1.6], [0, 1.6]]);

module base2d() scale([1, 0.92]) circle(r = 10, $fn = 64);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { drift([-5.6, 4.2, zb], [3.0, 2.4, 1.3]); base2d_in(); }
        heap();
    }
    brand_mark(MARK[0], MARK[1]);
}

module raw(p) {
    if (p == "roof") { post(); flutes(); brackets(); }
    if (p == "trim") { base(); arms(); finial_snow(); }
}
emit();
