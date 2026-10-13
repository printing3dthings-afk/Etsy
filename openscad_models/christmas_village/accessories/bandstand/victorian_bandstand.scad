// Victorian bandstand (2026-10-13), a village accessory. Scott circled it
// from the second batch of studies (../concepts/accessories2_scene.jpg).
//
// An octagonal bandstand: a brick plinth with stone steps up at the front,
// eight white columns, iron railings pierced with pointed arches in every bay
// but the front, a white valance between the columns with a wreath and a red
// bow over each bay, and a slate roof, bell-cast, under snow, with a finial.
// On a soft blob of snow, the maker's mark under it.
//
// Drawn to print upright with no support. The roof spans the whole bandstand,
// so its inside is a cone climbing SH per 1 in from the valance, and the
// valance has no flat beam to bridge: each bay's opening closes in a point,
// its two edges climbing 50 degrees from the columns. Cornice and eave
// corbel out at SH.
//
// Octagons have their corners at 22.5 + 45 i, where the columns stand; their
// flats face 0, 45, ... 315 degrees, and the front (the steps) faces -y, 270.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
SH = 1.2;
C  = 1 / cos(22.5);         // an octagon's corner, per 1 of its flat

zb  = 3.2;                  // the snow's top
A_p = 24;                   // the plinth's flats
z_p = 9.4;                  // its top
z_f = z_p + 0.8 * SH + 1.2; // the stone floor's top, the cap flaring 0.8 out
A_c = 20.5;                 // the columns' centres, on these flats
RC  = 1.7;                  // a column
z_ct = z_f + 32;            // the columns' tops
L   = 2 * A_c * tan(22.5);  // a bay, column centre to centre
VT  = 1.6;                  // the valance's thickness
z_vt = z_ct + 1.5;          // its top
z_ap = z_vt - 6.0;          // each opening's point: a band over it for the wreath
HC  = L / 2 - 1.4;          // where an opening's edge leaves the column
z_sp = z_ap - HC * tan(50); // ... at this height, climbing 50 deg
a_in = A_c - VT / 2;        // the valance's inner face
a_out = A_c + VT / 2;
FRONT = 6;                  // the flat facing -y: no railing, the steps

module oct_rev() rotate([0, 0, 22.5]) rotate_extrude($fn = 8) children();
// profile points given at their flats; the revolve wants corners
function cs(pts) = [for (p = pts) [p[0] * C, p[1]]];
// on flat i, d out from the centre: 2D x along it, y up, z out of it
module flat_at(i, d) rotate([0, 0, 45 * i]) multmatrix([[0, 0, 1, d], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) children();
module on_flat(i, d0, d1) flat_at(i, d0) linear_extrude(d1 - d0) children();

// ---- the plinth: brick in courses, a stone cap, steps --------------------------------------------
// each course line a groove 0.45 deep whose ceiling climbs SH back out
ZG = [4.8, 6.6, 8.4];
module plinth() oct_rev() polygon(cs(concat([[0, 2.4], [A_p, 2.4]],
    [for (z = ZG) each [[A_p, z], [A_p - 0.45, z], [A_p - 0.45, z + 0.1], [A_p, z + 0.1 + 0.45 * SH]]],
    [[A_p, z_p + 0.01], [0, z_p + 0.01]])));
// the bricks' end joints, staggered course to course, clear of the corners,
// cut 0.45 in with their tops sloping down as they go in
module joints() for (i = [0 : 7]) if (i != FRONT) flat_at(i, A_p) engrave_in(0.45)
    for (k = [0 : 3]) let (z0 = k == 0 ? zb : ZG[k - 1] + 0.64, z1 = k == 3 ? z_p : ZG[k], off = k % 2 == 0 ? 0 : 2.0)
        for (x = [-8 + off : 4 : 8]) if (abs(x) < A_p * tan(22.5) - 1.2 && z1 - z0 > 0.8)
            translate([x - 0.25, z0 + 0.2]) square([0.5, z1 - z0 - 0.2]);
module brick() difference() { plinth(); joints(); }
module cap() oct_rev() polygon(cs([[0, z_p], [A_p, z_p], [A_p + 0.8, z_p + 0.8 * SH], [A_p + 0.8, z_f], [0, z_f]]));
NS = 3; SR = (z_f - zb) / NS; ST = 2.8; SW = 13;
module steps() for (k = [1 : NS]) translate([-SW / 2, -(A_p + 0.8 + (NS - k + 1) * ST), 2.4])
    cube([SW, (NS - k + 1) * ST + 2, zb + k * SR - 2.4]);

// ---- columns, railings, the valance -----------------------------------------------------------
module column() rotate_extrude($fn = 24) polygon([[0, z_f - 0.01], [2.4, z_f - 0.01], [2.4, z_f + 0.8], [RC, z_f + 0.8 + 0.7 * SH * 0.8],
    [RC, z_ct - 2.2], [RC + 0.8, z_ct - 2.2 + 0.8 * SH], [RC + 0.8, z_ct], [0, z_ct]]);
module columns() for (i = [0 : 7]) rotate([0, 0, 22.5 + 45 * i]) translate([A_c * C, 0, 0]) column();

// railings: 8.4 tall, three pointed openings in each
RH = 8.4;
module railing2d() difference() {
    translate([-L / 2, z_f - 0.01]) square([L, RH + 0.01]);
    for (x = [-4.2, 0, 4.2]) translate([x, z_f + 1.4]) parch2d(2.6, 1.4);
}
module railings() for (i = [0 : 7]) if (i != FRONT) on_flat(i, A_c - 0.7, A_c + 0.7) railing2d();

// the valance: a band between the column tops, each bay's opening closing in a
// point. Its ends run 0.34 past the column centres so the corners close outside.
module valance2d() difference() {
    translate([-L / 2 - 0.34, z_sp - 1]) square([L + 0.68, z_vt - z_sp + 1]);
    polygon([[-HC, z_sp - 1.1], [-HC, z_sp], [0, z_ap], [HC, z_sp], [HC, z_sp - 1.1]]);
}
module valance() for (i = [0 : 7]) on_flat(i, a_in, a_out) valance2d();

// a wreath over each bay, and a red bow on top of it
WZ = z_ap + 2.6;
module wreath2d() translate([0, WZ]) difference() { circle(2.1, $fn = 40); circle(0.6, $fn = 32); }
module bow2d() translate([0, WZ + 1.9]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.4, 0.4]) circle(0.75, $fn = 20); }
    circle(0.75, $fn = 20);
}

// ---- the canopy: a corbel and cornice in stone, the roof in slate ------------------------------
// inside, a cone climbing SH per 1 in from the valance's inner face at the
// openings' points; outside, a cornice out at SH, then the eave's soffit
z_cor = z_vt + 1.5 * SH + 0.8;          // the eave's foot
A_e  = a_out + 1.5 + 2.7;               // the eave
z_ee = z_cor + 2.7 * SH + 1.0;          // the eave's top edge
z_ci = z_ap + 0.3 + a_in * SH;          // the ceiling's apex
// the roof's top: bell-cast, 0.38 per 1 to r 14, then 0.8
function roof_z(r) = r >= 14 ? z_ee + (A_e - r) * 0.38 : z_ee + (A_e - 14) * 0.38 + (14 - r) * 0.8;
RT = 1.4;                               // the roof's flat top, under the finial
// The ceiling's foot runs on into the valance's middle, level, 0.3 above the
// openings' points: stopped at the face, the two shared it and the union came
// out of CGAL with open edges along it; run on down its slope, it hung 0.6
// below each point, an island the slicer propped (2026-10-13).
module canopy() oct_rev() polygon(cs([[0, z_ci], [a_in, z_ap + 0.3], [A_c, z_ap + 0.3], [A_c, z_vt - 0.01], [a_out, z_vt - 0.01],
    [a_out + 1.5, z_vt + 1.5 * SH], [a_out + 1.5, z_cor], [A_e, z_cor + 2.7 * SH], [A_e, z_ee],
    [14, roof_z(14)], [8, roof_z(8)], [RT, roof_z(RT)], [0, roof_z(RT)]]));
module stone_canopy() intersection() { canopy(); translate([0, 0, -1]) cylinder(r = 60, h = z_cor + 1); }
module slate_roof() intersection() { canopy(); translate([0, 0, z_cor]) cylinder(r = 60, h = 60); }
// snow over the upper roof: nothing at r 14, 1.0 deep from r 10 up, so the
// lower roof shows its slate
module roof_snow() difference() {
    oct_rev() polygon(cs([[0, roof_z(RT) + 1.0], [RT, roof_z(RT) + 1.0], [10, roof_z(10) + 1.0],
        [14, roof_z(14)], [14, roof_z(14) - 3], [0, roof_z(RT) - 3]]));
    canopy();
}
// the finial: a stem, a ball swelling at 38 deg, a point blunted to print
module finial() translate([0, 0, roof_z(RT) - 0.01]) rotate_extrude($fn = 32)
    polygon([[0, 0], [1.2, 0], [1.2, 1.4], [2.1, 2.6], [2.1, 3.4], [0.5, 5.8], [0, 5.8]]);

// ---- the snow ---------------------------------------------------------------------------------
module base2d() circle(r = 36, $fn = 96);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() {
            drift([-22, -22, zb], [7, 4.5, 1.1]); drift([26, -14, zb], [4.5, 7, 1.0]);
            drift([-12, 29, zb], [8, 3.5, 1.1]); drift([20, 22, zb], [6, 5, 0.9]);
        } base2d_in(); }
    }
    brand_mark([0, 0], 6.0);
}

module raw(p) {
    if (p == "body") { brick(); for (i = [0 : 7]) flat_at(i, a_out - 0.01) art_out(1.2, 1) bow2d(); }
    if (p == "trim") { base(); cap(); steps(); columns(); valance(); stone_canopy(); roof_snow(); }
    if (p == "roof") { railings(); slate_roof(); finial(); }
    if (p == "accent") for (i = [0 : 7]) flat_at(i, a_out - 0.01) art_out(1.0, 1) wreath2d();
}
emit();
