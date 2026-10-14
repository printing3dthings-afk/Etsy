// Victorian village well (2026-10-14), a village accessory from the second
// batch of studies (../concepts/accessories2_scene.jpg).
//
// A round brick well with a stone coping, its water frozen, under a steep
// slate roof on four white posts. A white valance runs between the posts,
// each bay's opening closing in a point; a wreath with a red bow hangs on the
// front gable, snow lies along the ridge, and a bucket stands on the rim. On
// a soft blob of snow, the maker's mark under it.
//
// Printed upright with no support. The roof is pitched at 55 degrees, so its
// underside climbs 35 off upright; the valances carry it, their openings
// closing in points that climb 50; the eaves stand out on a corbel that steps
// out at SH; the snow along the ridge thins to nothing as it goes down.
//
// Drawn with the ridge along x and the wreath's gable facing +x, then turned
// so the gable faces the front, -y.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
SH = 1.2;

zb = 3.2;                   // the snow's top
R_o = 10.0;                 // the well's outer wall
R_i = 7.0;                  //          inner
z_w = 13.0;                 //          top
z_ice = 9.0;                // the frozen water
z_c = z_w + 0.8 * SH + 1.4; // the coping's top, its lip 1.4

// the well: brick, two course lines cut round it, the coping flaring at SH
ZG = [6.4, 9.6];
module well() rotate_extrude($fn = 64) polygon(concat([[R_i, 2.4], [R_o, 2.4]],
    [for (z = ZG) each [[R_o, z], [R_o - 0.45, z], [R_o - 0.45, z + 0.1], [R_o, z + 0.1 + 0.45 * SH]]],
    [[R_o, z_w + 0.01], [R_i, z_w + 0.01]]));
module coping() rotate_extrude($fn = 64) polygon([[R_i, z_w], [R_o, z_w], [R_o + 0.8, z_w + 0.8 * SH], [R_o + 0.8, z_c], [R_i, z_c]]);
module water() cylinder(r = R_i + 0.01, h = z_ice, $fn = 64);

// four posts on the coping, a valance between them
P = 6.2;                    // the posts' centres
PW = 2.0;                   // a post
VT = 1.4;                   // the valance's thickness
z_e = 32.0;                 // the eaves: the valance's top
HC = P - PW / 2;            // an opening's half-span, post face to post face
z_ap = z_e - 2.4;           // its point, under the corbel's foot
z_sp = z_ap - HC * tan(50); // where its edges leave the posts, climbing 50 deg
module posts() for (x = [-P, P], y = [-P, P]) translate([x - PW / 2, y - PW / 2, z_c - 0.01]) cube([PW, PW, z_e - z_c + 0.01]);
module valance2d() difference() {
    translate([-P, z_sp - 1]) square([2 * P, z_e - z_sp + 1]);
    polygon([[-HC, z_sp - 1.1], [-HC, z_sp], [0, z_ap], [HC, z_sp], [HC, z_sp - 1.1]]);
}
// on the side at angle a, d out: 2D x along it, y up, z out of it
module face_at(a, d) rotate([0, 0, a]) multmatrix([[0, 0, 1, d], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) children();
module valances() for (a = [0, 90, 180, 270]) face_at(a, P - VT / 2) linear_extrude(VT) valance2d();

// the roof: pitched 55 deg, the ridge along x. Its eaves stand 1.8 out from
// the valance on a corbel stepping out at SH; inside, the valances' inner
// faces carry it, so the cavity's foot is there. Flush with the gables.
PITCH = 55;
YV = P + VT / 2;            // the valance's outer face
YE = YV + 1.8;              // the eave: at 1.0 the roof barely cleared the posts
XE = P + VT / 2;            // the gables' outer faces
function rz(y, y0) = z_e + (y0 - abs(y)) * tan(PITCH);
z_r = rz(0, YE);            // the ridge
module prism(pts) rotate([90, 0, 90]) translate([0, 0, -XE]) linear_extrude(2 * XE) polygon(pts);
module roof() difference() {
    prism([[-YE, z_e], [0, z_r], [YE, z_e]]);
    prism([[-YV + VT, z_e - 0.01], [0, rz(0, YV - VT)], [YV - VT, z_e - 0.01]]);
}
module corbels() for (s = [-1, 1]) mirror([0, s > 0 ? 0 : 1, 0])
    prism([[YV - 0.01, z_e - (YE - YV) * SH], [YE, z_e], [YV - 0.01, z_e + 0.01]]);
// the gables: the roof's ends filled to the eaves
module gables() for (s = [-1, 1]) translate([s > 0 ? P - VT / 2 : -P - VT / 2, 0, 0]) rotate([90, 0, 90])
    linear_extrude(VT) polygon([[-YE, z_e - 0.01], [0, z_r], [YE, z_e - 0.01]]);
// snow along the ridge: 1.0 deep there, thinning to nothing SD down the slope
SD = 6.0;
YS = SD * cos(PITCH);
module roof_snow() difference() {
    prism([[-YS, rz(YS, YE)], [0, z_r + 1.0], [YS, rz(YS, YE)]]);
    prism([[-YE, z_e], [0, z_r], [YE, z_e]]);
}

// the wreath on the front gable, the bow red
WZ = z_e + 3.4;
module wreath2d() translate([0, WZ]) difference() { circle(2.0, $fn = 40); circle(0.6, $fn = 32); }
module bow2d() translate([0, WZ + 1.9]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.4, 0.4]) circle(0.75, $fn = 20); }
    circle(0.75, $fn = 20);
}

// a bucket on the rim under the wreath, its sides flaring 10 deg, a white
// band round its top
BH = 2.8;
module bucket(z0, z1) translate([(R_i + R_o) / 2 + 0.2, 0, z_c - 0.01]) intersection() {
    cylinder(r1 = 1.4, r2 = 1.4 + BH * tan(10), h = BH, $fn = 24);
    translate([-5, -5, z0]) cube([10, 10, z1 - z0]);
}

module base2d() circle(r = 19, $fn = 96);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([-12, -11, zb], [4, 3, 1.0]); drift([13, 9, zb], [3.5, 4, 0.9]); } base2d_in(); }
    }
    brand_mark([0, 0], 5.0);
}

module raw(p) rotate([0, 0, -90]) {
    if (p == "body") { well(); face_at(0, XE - 0.01) art_skirt(1.0, 1) bow2d(); }
    if (p == "roof") { roof(); water(); bucket(0, BH - 0.8); }
    if (p == "trim") { rotate([0, 0, 90]) base(); coping(); posts(); valances(); corbels(); gables(); roof_snow(); bucket(BH - 0.8, BH + 1); }
    if (p == "accent") difference() { face_at(0, XE - 0.01) art_skirt(1.0, 1) wreath2d(); face_at(0, XE - 0.01) art_skirt(1.0, 1) bow2d(); }
}
emit();
