// Haunted Schoolhouse lantern -- building #4 of the Haunted Town series
// (../HAUNTED_TOWN.md). Picked by Scott on 2026-10-02 from four forms: the
// one-room school. A hollow shell lit from inside by a battery LED tealight:
// open base, glazed through-cut windows.
//
// THE TOWN'S STYLE: a ridge that SAGS in the middle, a crooked chimney, steep
// roofs, walls / roof / trim / accent printed as separate AMS colours in one
// 3MF. Square plans (the Christmas village went round; the town stays square).
// THE SCHOOLHOUSE'S OWN FEATURES, from the town's variety plan (Scott,
// 2026-09-25): half-timbered walls, paired narrow windows with pointed heads,
// a hip roof with a bell cupola on the ridge, a sagging porch roof along the
// front, and an oversized stopped clock in a gablet above the porch.
//
// COLOUR PARTS. Render one at a time with -D part="...":
//   body    plastered walls, plinth and porch deck, the clock gablet, the
//           cupola's base
//   roof    hip roof, shingles, ridge and hip caps, crooked chimney, the porch
//           roof, the gablet's roof, the cupola's cap
//   trim    window frames and panes, door and frame, the porch arcade, the
//           clock's glass, the belfry
//   accent  the half-timbering, the clock's ring, marks and hands, the bell,
//           the finial
// Every part is built DISJOINT from the others; the part="chk_*" renders are
// the pairwise intersections and must come out empty.
//
// PRINTS WITH NO SUPPORTS. Every downward face is 50 deg or steeper from
// horizontal, and every outside corner of two downward faces 58 deg (the
// bakery's measured rule):
//   - the hip roof is 55 deg, its eave flare 58 deg all round (the flare turns
//     four outside corners); the inside ceiling is 50.7 deg with a LEVEL ridge
//     (a sagging inside ridge closes from the middle outward and drew
//     supports on the bakery);
//   - every raised relief has a sheared underside (relief_up);
//   - the windows, door and arcade arches have 58 deg pointed heads;
//   - the porch roof's underside rises to the wall at 55 to 60 deg and rests
//     on the arcade at its front edge, so it never spans free;
//   - the clock's gablet is the front wall carried up through the eave; its
//     glass sits low enough that the room is right behind it. A light channel
//     behind a higher clock met the ceiling in a corner of a 58 deg and a
//     50.7 deg face, and the slicer propped the whole corner;
//   - the gablet's slate cap is cut to the room's ceiling where it runs back
//     over the room; uncut, its 30 deg underside hung there.
//
// TEALIGHT. The inside is 88.6 x 48.6 mm, open at the base, clear from the
// plate to the wall top at 62 mm and higher inward.

include <BOSL2/std.scad>
include <../../lattice_lib.scad>   // shared, lives in openscad_models/

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ------------------------------------------------------------------------
W        = 92;              // along X, the front's width
D        = 52;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
H        = 62;              // wall top, where the eave flare begins
plinth_h = 8;               // shared by every building in the town
plinth_o = 1.68;            // plinth face, proud of the plaster
SH       = 1.2;             // shear of every raised relief: 1.2 up per 1 out
t58      = tan(58);

// ---- roof --------------------------------------------------------------------------
e    = 5;                   // eave projection, all four sides
er   = e * t58;             // ...carried on a 58 deg flare
f    = 3;                   // fascia height
zf   = H + er + f;          // top of the fascia, where the slopes start
be   = D/2 + e;             // eave line, half-depth
ae   = W/2 + e;             // eave line, half-width
xr   = ae - be;             // ridge half-length
k_e  = tan(55);             // pitch of the hips and of the long faces at the ridge's ends
R_end = zf + be * k_e;      // ridge at its ends
sag  = 5;                   // ...and 5 mm lower in the middle
tr   = 2.52;                // slab thickness, normal to the slope

function Rz(x) = abs(x) >= xr ? R_end : R_end - sag * (1 - pow(x / xr, 2));
function top_z(x, y) = zf + (Rz(x) - zf) * (be - abs(y)) / be;
function hip_z(x) = zf + (ae - abs(x)) * k_e;
k0   = (Rz(0) - zf) / be;   // the long faces' pitch at mid-span, 51.7 deg
tv0  = tr / cos(atan(k0));
// The zone line: the boundary between wall colour and roof colour, and the
// lantern's ceiling. Its eave end sits 0.03 above the flare's top, its ridge
// is level.
zi_0 = H + er + 0.03;
zi_1 = Rz(0) - tv0 - 0.3;
k_i  = (zi_1 - zi_0) / be;

// ---- plan --------------------------------------------------------------------------
module plan2d(g) { offset(r = g) offset(r = corner_r) square([W - 2*corner_r, D - 2*corner_r], center = true); }

// Place children on a wall. Local x runs along the wall as a viewer outside
// sees it, local y is world up, local z is out from the wall.
//   face 0 = back (+Y), 1 = front (-Y), 2 = right end (+X), 3 = left end (-X)
module face_tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, D/2, z] : face == 1 ? [u, -D/2, z]
      : face == 2 ? [W/2, u, z] : [-W/2, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module shear_up() multmatrix([[1, 0, 0, 0], [0, 1, SH, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// The bakery's relief: underside sheared, top flat, a hole whose ceiling rises
// with depth.
module relief_hole(d0, a, b) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up() translate([0, 0, a]) linear_extrude(b - a) translate([0, -SH * d0]) children();
}
module relief_up(d0, d1) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up() translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1) children(1);
    }
}

// ---- the roof's solids ---------------------------------------------------------
function stations(a, c, n) = [for (i = [0 : n]) a + (c - a) * i / n];
ROOF_ST = stations(-ae - 1, ae + 1, 64);
// Under the top surface: the sagging gable, cut by the two hip planes.
module gable_solid() skin([for (x = ROOF_ST) [for (p = [
        [-be, H - 1], [be, H - 1], [be, zf], [0, Rz(x)], [-be, zf]]) [x, p[0], p[1]]]], slices = 0);
module hip_tent() rotate([90, 0, 0]) linear_extrude(2 * be + 20, center = true)
    polygon([[-ae, -10], [ae, -10], [ae, zf], [0, zf + ae * k_e], [-ae, zf]]);
module top_solid() intersection() { gable_solid(); hip_tent(); }
// The eave flare: the wall's plan at the wall top widening at 58 deg to the
// eave line, which is the plan offset by e -- ROUNDED at the corners, so each
// corner of the flare is a cone as steep as the sides. Flared out to a square
// corner, the corner edge ran at 46.9 deg (the diagonal is root 2 longer) and
// the slicer propped all four.
module eave2d() plan2d(e);
module flare_up() {
    hull() {
        translate([0, 0, H]) linear_extrude(0.01) plan2d(0);
        translate([0, 0, H + er - 0.01]) linear_extrude(0.01) eave2d();
    }
    translate([0, 0, H + er - 0.02]) linear_extrude(200) eave2d();
}
// the roof's own add-ons stop at the eave line too
module eave_clip() linear_extrude(400) eave2d();
module roof_volume() intersection() { top_solid(); flare_up(); }
// Everything below the zone line: a hip with a level ridge, its slopes
// carried 3 mm past the eave so its edges never meet the roof's.
module zone_below(lift = 0) translate([0, 0, lift]) hull() {
    translate([-ae - 3, -be - 3, -10]) cube([2 * (ae + 3), 2 * (be + 3), 0.01]);
    translate([-ae - 3, -be - 3, zi_0 - 3 * k_i]) cube([2 * (ae + 3), 2 * (be + 3), 0.01]);
    translate([-xr, -0.005, zi_1]) cube([2 * xr, 0.01, 0.01]);
}
module cavity() intersection() {
    translate([0, 0, -2]) linear_extrude(400) plan2d(-wall);
    zone_below(0.3);
}

// ---- shingles, by addition (the bakery's), on all four slopes -----------------
// Each course's butt is a vertical face 1.0 proud of the slab; it thins to
// 0.05 where it runs 0.5 under the next course. The long faces' courses
// follow the sag; the hip ends' are planar. Each slope's courses are clipped
// to its own part of the plan, so at a hip both slopes' courses meet on the
// hip line, where their butts are at the same height.
sh_t = 1.0;
sh_c = 3.4;
SH_U = concat([for (k = [0 : floor((be - 1.2) / sh_c)]) k * sh_c], [be - 0.7]);
module long_region(s) linear_extrude(400) polygon([[-xr, 0], [xr, 0], [ae + 3, s * (be + 3)], [-ae - 3, s * (be + 3)]]);
module end_region(s) linear_extrude(400) polygon([[s * xr, 0], [s * (ae + 3), be + 3], [s * (ae + 3), -be - 3]]);
module long_courses() for (s = [-1, 1]) intersection() {
    union() for (k = [0 : len(SH_U) - 2])
        let (u0 = SH_U[k], u1 = min(SH_U[k + 1] + 0.5, be - 0.7))
        skin([for (x = ROOF_ST) let (y0 = s * (be - u0), y1 = s * (be - u1),
                  q = [[x, y0, top_z(x, y0) - 1.0], [x, y0, top_z(x, y0) + sh_t],
                       [x, y1, top_z(x, y1) + 0.05], [x, y1, top_z(x, y1) - 1.0]])
              s > 0 ? q : [for (i = [3 : -1 : 0]) q[i]]], slices = 0);
    long_region(s);
}
module end_courses() for (s = [-1, 1]) intersection() {
    mirror([s < 0 ? 1 : 0, 0, 0]) rotate([90, 0, 0]) linear_extrude(2 * be + 6, center = true)
        for (k = [0 : len(SH_U) - 2])
            let (x0 = ae - SH_U[k], x1 = ae - min(SH_U[k + 1] + 0.5, be - 0.7))
            polygon([[x0, hip_z(x0) - 1.0], [x0, hip_z(x0) + sh_t], [x1, hip_z(x1) + 0.05], [x1, hip_z(x1) - 1.0]]);
    end_region(s);
}
module ridge_cap() intersection() {
    skin([for (x = ROOF_ST) [
        [x, 1.8, top_z(x, 1.8) - 1.0], [x, 1.8, top_z(x, 1.8) + 0.6], [x, 0, Rz(x) + 1.6],
        [x, -1.8, top_z(x, 1.8) + 0.6], [x, -1.8, top_z(x, 1.8) - 1.0]]], slices = 0);
    translate([-xr, -5, 0]) cube([2 * xr, 10, 400]);
}
// A cap astride each hip, from the ridge's end to 1.5 short of the eave corner.
// Its feet reach 4.4 under the surface: at 1.2, the roof fell away under the
// cap's corner end faster than the cap did, and left its foot hanging.
module hip_caps() for (sx = [-1, 1], sy = [-1, 1]) {
    a = [sx * xr, 0];  c = [sx * (ae - 1.5), sy * (be - 1.5)];
    hull() for (p = [a, c]) translate([p[0], p[1], (p == a ? R_end : hip_z(ae - 1.5)) + 0.6])
        rotate([0, 0, 45]) translate([0, 0, -1.6]) cube([2.0, 2.0, 5.6], center = true);
}

// ---- chimney: crooked, on the back slope at the left -----------------------------
ch = [-31, 12];             // centre
ch_w = 7;
ch_z = 108;                 // straight stack to here
module ch_slice(c, z, g = 0) translate([c[0], c[1], z]) linear_extrude(0.01) square(ch_w + 2 * g, center = true);
module chimney() {
    c1 = ch + [-3.2, 0];    // the kink leans out toward the end, 21.8 deg
    translate([ch[0] - ch_w/2, ch[1] - ch_w/2, 80]) cube([ch_w, ch_w, ch_z - 80]);
    hull() { ch_slice(ch, ch_z - 0.01); ch_slice(c1, ch_z + 8); }
    translate([c1[0] - ch_w/2, c1[1] - ch_w/2, ch_z + 7.99]) cube([ch_w, ch_w, 5.02]);
    hull() { ch_slice(c1, ch_z + 12.99); ch_slice(c1, ch_z + 15, 1.2); }     // 31 deg corbel
    translate([c1[0], c1[1], ch_z + 16.2]) cube([ch_w + 2.4, ch_w + 2.4, 2.4], center = true);
    translate([c1[0], c1[1], ch_z + 17.3]) {
        cylinder(r = 2.4, h = 3.6, $fn = 40);
        translate([0, 0, 3.6]) cylinder(r1 = 2.4, r2 = 3.1, h = 0.9, $fn = 40);
        translate([0, 0, 4.5]) cylinder(r = 3.1, h = 0.7, $fn = 40);
    }
}

// ---- openings: paired slits with pointed heads ----------------------------------
sl_a  = 2.0;                // half-width of one slit
sl_h  = 14;                 // its straight sides; the head adds sl_a * tan 58
sl_c  = 3.4;                // each slit's centre from the pair's centre
function slit_pts(a, hgt) = [[-a, 0], [a, 0], [a, hgt], [0, hgt + a * t58], [-a, hgt]];
module slit2d() polygon(slit_pts(sl_a, sl_h));
module pair2d(g = 0) for (s = [-1, 1]) translate([s * sl_c, 0]) offset(r = g) slit2d();
//   [face, u, sill z]
WINDOWS = [
    [0, -30, 22], [0, 0, 22], [0, 30, 22],
    [1, -19.5, 22], [1, 19.5, 22], [1, -36, 22], [1, 36, 22],
    [2, 0, 22], [3, 0, 22],
];
fr_w  = 1.7;
fr_t  = 1.68;               // frame face, 1.68 proud of the plaster
fr_sill = 2.6;
fr_half = sl_c + sl_a + fr_w + 0.3;
module win_frame_outer() union() {
    offset(r = fr_w + 0.3) pair2d();
    translate([-fr_half, -fr_w - 0.3 - fr_sill]) square([2 * fr_half, fr_w + fr_sill + 1]);
}

// ---- door, under the porch -------------------------------------------------------
door_a = 6;
door_h = 18;                // straight sides; the pointed head adds 9.6
function door_pts(a, hgt) = slit_pts(a, hgt);
module door_frame() face_tf(1, 0, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
    difference() {
        intersection() { offset(r = fr_w) polygon(door_pts(door_a, door_h)); translate([-20, 0]) square([40, 100]); }
        translate([0, -1]) polygon(door_pts(door_a, door_h + 1));
    }
module door_leaf() face_tf(1, 0, plinth_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
    difference() {
        polygon(door_pts(door_a, door_h));
        translate([0, 17]) polygon(slit_pts(1.4, 3));        // a slit light, so the door glows too
    }

// ---- the porch: a deck, an arcade of pointed arches, a sagging roof --------------
P     = 9;                  // depth in front of the wall
xp    = 28;                 // half-width
y_f   = -D/2 - P;           // its front
y_w   = -D/2;
ar_t  = 3.0;                // arcade thickness
z_uw  = 50;                 // the porch roof's underside where it meets the wall: its top
                            // there is 55, under the clock's ring
k_p   = tan(55);            // ...its pitch at the ends; the sag steepens the middle
zp_end = z_uw - P * k_p;
sag_p = 2.5;
function zp(x) = zp_end - sag_p * (1 - pow(x / xp, 2));
function kp(x) = (z_uw - zp(x)) / P;
function tvp(x) = tr / cos(atan(kp(x)));
function pu(x, y) = zp(x) + (y - y_f) * kp(x);              // underside
function pt(x, y) = pu(x, y) + tvp(x);                      // top
PORCH_ST = stations(-xp, xp, 32);
module porch_roof_slab() skin([for (x = PORCH_ST) [for (p = [
        [y_f, pu(x, y_f)], [y_w + 0.6, pu(x, y_w + 0.6)], [y_w + 0.6, pt(x, y_w + 0.6)], [y_f, pt(x, y_f)]])
        [x, p[0], p[1]]]], slices = 0);
// The arcade is cut to a surface 2 mm up INSIDE the porch roof, on the
// roof's own stations, and then the roof is taken out of it, so its top is the
// roof's underside exactly. Cut straight to a separate underside skin, the two
// triangulated the sag differently and left open edges along the front.
module under_porch_mid() skin([for (x = PORCH_ST) [for (p = [
        [y_f, -5], [y_w + 0.6, -5], [y_w + 0.6, pu(x, y_w + 0.6) + 2], [y_f, pu(x, y_f) + 2]])
        [x, p[0], p[1]]]], slices = 0);
PSH_U = [0, 3.4, 6.8, P - 0.7];
module porch_courses() intersection() {
    union() for (k = [0 : len(PSH_U) - 2])
        let (u0 = PSH_U[k], u1 = min(PSH_U[k + 1] + 0.5, P - 0.7))
        skin([for (x = PORCH_ST) let (y0 = y_f + u0, y1 = y_f + u1)
              [[x, y1, pt(x, y1) - 1.0], [x, y1, pt(x, y1) + 0.05], [x, y0, pt(x, y0) + sh_t], [x, y0, pt(x, y0) - 1.0]]], slices = 0);
    translate([-xp, y_f - 1, 0]) cube([2 * xp, P + 1, 200]);
}
// [centre, half-width]; each apex 2.2 under the porch roof's front edge
ARCHES = [[-18, 6], [0, 6.5], [18, 6]];
function arch_pts(c, a) = let (ap = zp(c) - 2.2) slit_pts(a, ap - a * t58 - plinth_h);
// The roof is taken out here, in the arcade itself: taken out only in the
// trim part, the roof part subtracted the uncut arcade and lost 2 mm of its
// own front edge, and the slicer propped the gap.
module arcade() difference() { intersection() {
    difference() {
        translate([-xp, y_f, plinth_h - 0.01]) cube([2 * xp, ar_t, 60]);
        for (q = ARCHES) translate([q[0], y_f + ar_t + 1, plinth_h - 1]) rotate([90, 0, 0])
            linear_extrude(ar_t + 2) translate([0, 1]) polygon(arch_pts(q[0], q[1]));
    }
    under_porch_mid();
} porch_roof_slab(); }
st_w = 20;  st_d = 7;  st_h = 4;
module deck() {
    translate([-xp - 1.2, y_f - 1.2, 0]) cube([2 * xp + 2.4, P + 1.2 + wall, plinth_h]);
    translate([-st_w/2, y_f - 1.2 - st_d, 0]) cube([st_w, st_d + 0.01, st_h]);
}

// ---- the clock gablet: the front wall carried up through the eave ---------------
// Its glass is the clock's face and glows when lit; the marks and hands run
// through the glass and show dark against it. The glass is set below the
// room's ceiling (78.2 at the wall), so the room is right behind it.
g_w  = 27;                  // gablet width
g_ez = 81.5;                // its eaves
g_pitch = 30;               // its little roof: top surfaces only, so any pitch prints
g_ap = g_ez + g_w/2 * tan(g_pitch);
g_y1 = -16;                 // it runs back to here, inside the main roof
ck_z = 68;  ck_r = 9.5;
module gablet_block() rotate([90, 0, 0]) translate([0, 0, -g_y1]) linear_extrude(D/2 + g_y1)
    polygon([[-g_w/2, H - 2], [g_w/2, H - 2], [g_w/2, g_ez], [0, g_ap], [-g_w/2, g_ez]]);
// the cut it makes through the main roof's eave, in front of it
module gablet_cut() translate([-g_w/2, -be - 6, H]) cube([g_w, be + 6 - D/2, 200]);
g_cap = 1.6;                // slate cap, normal to the gablet's slopes
g_cv  = g_cap / cos(g_pitch);
module gablet_cap() difference() { gablet_block(); translate([0, 0, -g_cv]) gablet_block(); }
// a cream bargeboard under the cap, up both slopes of the gable
g_bw  = 2.2 / cos(g_pitch);
module gablet_barge() face_tf(1, 0, 0) relief_up(-0.4, fr_t)
    polygon([[-g_w/2, g_ez - g_cv - g_bw], [0, g_ap - g_cv - g_bw], [g_w/2, g_ez - g_cv - g_bw],
             [g_w/2, g_ez - g_cv], [0, g_ap - g_cv], [-g_w/2, g_ez - g_cv]]);
module ck_dots2d() for (i = [0 : 11]) rotate(90 - 30 * i) translate([7.2, 0]) circle(r = i % 3 == 0 ? 1.1 : 0.8, $fn = 20);
module seg2(a, b, w) hull() { translate(a) circle(d = w, $fn = 12); translate(b) circle(d = w, $fn = 12); }
// stopped at 11:47
module ck_hands2d() {
    seg2([0, 0], 4.6 * [cos(96.5), sin(96.5)], 1.7);
    seg2([0, 0], 6.4 * [cos(168), sin(168)], 1.2);
    circle(r = 1.3, $fn = 24);
}
// The glass and its marks run the wall's whole depth, flush with its face:
// set 0.2 back like the windows' panes, the shallow recess round the dial's
// lower rim drew a cluster of support from the ring's top.
module ck_inlay() face_tf(1, 0, ck_z) translate([0, 0, -wall]) linear_extrude(wall)
    intersection() { union() { ck_dots2d(); ck_hands2d(); } circle(r = ck_r + 0.6, $fn = 96); }
module ck_glass() face_tf(1, 0, ck_z) translate([0, 0, -wall]) linear_extrude(wall) circle(r = ck_r + 0.6, $fn = 96);
module ck_ring() face_tf(1, 0, ck_z) relief_up(-0.4, fr_t) { circle(r = ck_r + 2.2, $fn = 96); circle(r = ck_r + 0.3, $fn = 96); }

// ---- the cupola -------------------------------------------------------------------------
cb_h  = 8;                  // base half-width
cb_z  = Rz(0) + 4.5;        // the belfry's floor
bf_h  = 7;                  // belfry half-width
bf_t  = 16;                 // belfry height
bf_a  = 3.6;                // arch half-width
cap_o = 1.2;                // the cap's cornice, out over the belfry at 58 deg
module cupola_base() translate([-cb_h, -cb_h, 85]) cube([2 * cb_h, 2 * cb_h, cb_z - 85]);
module belfry() difference() {
    translate([-bf_h, -bf_h, cb_z]) cube([2 * bf_h, 2 * bf_h, bf_t]);
    // two pointed tunnels crossing: four corner posts, a cross vault whose
    // groins are 58 deg
    for (r = [0, 90]) rotate([0, 0, r]) translate([0, bf_h + 1, cb_z - 0.01]) rotate([90, 0, 0])
        linear_extrude(2 * bf_h + 2) polygon(slit_pts(bf_a, bf_t - 2.2 - bf_a * t58));
}
cap_z = cb_z + bf_t;
module cupola_cap() {
    hull() {
        translate([-bf_h, -bf_h, cap_z - 0.01]) cube([2 * bf_h, 2 * bf_h, 0.01]);
        translate([-bf_h - cap_o, -bf_h - cap_o, cap_z + cap_o * t58]) cube([2 * (bf_h + cap_o), 2 * (bf_h + cap_o), 0.01]);
    }
    translate([0, 0, cap_z + cap_o * t58]) rotate([0, 0, 45])
        cylinder(r1 = (bf_h + cap_o) * sqrt(2), r2 = 0, h = (bf_h + cap_o) * tan(60), $fn = 4);
}
cap_top = cap_z + cap_o * t58 + (bf_h + cap_o) * tan(60);
// a spike rising out of the pyramid, narrower than the pyramid where it starts
// (a cone on a stalk hung its rim out over the stalk)
// its tip 1 mm across: a sharp point is lost in the last layers
module finial() translate([0, 0, cap_top - 2.5]) cylinder(r1 = 1.3, r2 = 0.5, h = 8, $fn = 24);
// The bell stands on the belfry floor. Every face of it looks up -- it
// narrows all the way from its lip -- so it needs nothing under it.
module bell() translate([0, 0, cb_z - 0.3]) {   // 0.3 into the floor, one body with it
    rotate_extrude($fn = 48) polygon([[0, 0], [3.0, 0], [3.0, 0.5], [2.3, 1.5], [1.9, 3.5], [1.8, 5.0], [1.2, 6.0], [0, 6.4]]);
    translate([0, 0, 6.2]) cylinder(r = 0.6, h = 1.2, $fn = 16);
}

// ---- half-timbering: dark beams on the plaster -------------------------------------------
tm_w = 2.4;
tm_t = 1.0;
hr_z = 46;                  // the head rail, above the windows
function face_len(face) = face < 2 ? W : D;
// per face: posts (u), and braces either side of a post ([u, side])
POSTS  = [[-15, 15], [-9.9, 9.9], [-14, 14], [-14, 14]];
BRACES = [[[-15, -1], [-15, 1], [15, -1], [15, 1]], [], [[-14, -1], [14, 1]], [[-14, -1], [14, 1]]];
module tm_bar(a, b) hull() { translate(a) square(tm_w, center = true); translate(b) square(tm_w, center = true); }
module timbers2d(face) {
    L = face_len(face);
    difference() {
        union() {
            translate([-L/2, plinth_h]) square([L, tm_w]);                    // sill beam
            translate([-L/2, hr_z]) square([L, tm_w]);                        // head rail
            for (u = POSTS[face]) translate([u - tm_w/2, plinth_h]) square([tm_w, (face == 1 ? hr_z : H - 0.4) - plinth_h]);
            for (b = BRACES[face]) let (u = b[0], s = b[1]) {
                tm_bar([u + s * 8, plinth_h + tm_w/2], [u, plinth_h + tm_w/2 + 8 * t58]);
                tm_bar([u, hr_z + tm_w/2 - 8 * t58], [u + s * 8, hr_z + tm_w/2]);
            }
        }
        // clear of every window frame, the door, the corners
        for (w = WINDOWS) if (w[0] == face) translate([w[1], w[2]]) offset(r = 0.8) win_frame_outer();
        if (face == 1) translate([0, plinth_h]) offset(r = fr_w + 0.8) polygon(door_pts(door_a, door_h));
        for (s = [-1, 1]) translate([s * L/2 - 3, 0]) square([6, 100]);
    }
}
module timbers() {
    for (face = [0 : 3]) face_tf(face, 0, 0) relief_up(-0.4, tm_t) timbers2d(face);
    // corner posts: the plan's corners, wrapped round
    translate([0, 0, plinth_h]) linear_extrude(H - 0.4 - plinth_h)
        intersection() {
            difference() { plan2d(tm_t); plan2d(-0.4); }
            for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (W/2 - 0.25), sy * (D/2 - 0.25)]) square([4.6, 4.6], center = true);
        }
}

// ---- trim and openings -----------------------------------------------------------
module openings() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) pair2d();
    face_tf(1, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(door_pts(door_a, door_h));
    face_tf(1, 0, ck_z) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) circle(r = ck_r, $fn = 96);
}
module frame_holes() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) pair2d();
}
module trim_raw() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) {
        relief_up(-0.4, fr_t) { win_frame_outer(); offset(r = 0.3) pair2d(); }
        // the glass behind both slits, 0.6 into the reveal all round
        translate([0, 0, -wall]) linear_extrude(wall - 0.2) pair2d(0.6);
    }
    door_frame();
    door_leaf();
    arcade();
    ck_glass();
    gablet_barge();
    belfry();
}
module accent_raw() {
    timbers();
    ck_ring();
    ck_inlay();
    bell();
    finial();
}

// ---- mark ------------------------------------------------------------------------------
// Under the porch deck, read from below with the front toward you: flipped
// left-to-right (2026-09-27, the chapel's lesson), spacing 1.16 at size 4.6.
module brand_mark() translate([0, (y_f + y_w) / 2, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black",
                           halign = "center", valign = "center", spacing = 1.16);

// ---- parts ------------------------------------------------------------------------------
module body_core() {
    linear_extrude(plinth_h) plan2d(plinth_o);
    translate([0, 0, plinth_h - 0.5]) linear_extrude(H - plinth_h + 0.5) plan2d(0);
    roof_volume();
}
module roof_raw() {
    difference() {
        union() {
            roof_volume();
            intersection() { union() { long_courses(); end_courses(); ridge_cap(); hip_caps(); } eave_clip(); }
        }
        zone_below();
        gablet_cut();
        // only where the gablet and the cupola's base stand above the room;
        // below that the roof keeps its own underside on the zone line. Taken
        // out whole, the gablet left the roof behind it resting on the
        // gablet's 30 deg top where the gablet itself had been cut away to
        // the ceiling, and that face hung over the room
        // exactly what the body keeps of the gablet: taken out only above
        // zone+0.3, the roof kept a 0.3 band inside the gablet's own front wall,
        // where there is no room under it, and the two parts overlapped there
        difference() { gablet_block(); cavity(); }
        difference() { cupola_base(); zone_below(0.3); }
    }
    difference() { chimney(); cavity(); zone_below(); }
    porch_roof_slab();
    porch_courses();
    difference() { gablet_cap(); zone_below(0.3); }
    difference() { cupola_cap(); finial(); }
}
module body_part() difference() {
    union() {
        difference() { intersection() { body_core(); zone_below(); } gablet_cut(); }
        deck();
        gablet_block();
        difference() { cupola_base(); zone_below(); }
    }
    cavity(); openings(); frame_holes(); trim_raw(); accent_raw(); brand_mark();
    porch_roof_slab(); porch_courses(); gablet_cap(); chimney();
}
module roof_part()   difference() { roof_raw(); trim_raw(); accent_raw(); }
module trim_part()   difference() { trim_raw(); accent_raw(); }
module accent_part() accent_raw();

if      (part == "none")   ;
else if (part == "body")   body_part();
else if (part == "roof")   roof_part();
else if (part == "trim")   trim_part();
else if (part == "accent") accent_part();
else if (part == "union")  union() { body_part(); roof_part(); trim_part(); accent_part(); }
else if (part == "chk_body_roof")    intersection() { body_part(); roof_part(); }
else if (part == "chk_body_trim")    intersection() { body_part(); trim_part(); }
else if (part == "chk_body_accent")  intersection() { body_part(); accent_part(); }
else if (part == "chk_roof_trim")    intersection() { roof_part(); trim_part(); }
else if (part == "chk_roof_accent")  intersection() { roof_part(); accent_part(); }
else if (part == "chk_trim_accent")  intersection() { trim_part(); accent_part(); }
else {
    color("#A8814A") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#2E2219") accent_part();
}
