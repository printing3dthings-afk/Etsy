// Victorian Toy Shop -- building #2 of the Dickens Victorian village, and the
// first to join round and square (Scott, 2026-09-30: "I want to incorporate
// round and square together on some buildings ... Do all different shapes and
// stories of the buildings", and picked this form from four).
//
// A two-storey square brick shop under a slate gable that runs side to side,
// white quoins at its corners, a string course between the storeys. On its
// front a canted evergreen bay shop window with TOYS on its fascia, under a
// small hipped slate roof; upstairs two sash windows with window boxes. On the
// front-left corner a round brick tower rises past the ridge to a bell-flared
// slate cone with snow on its crown and a finial; the door is at its foot, and
// it has windows on four levels. On a soft blob of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The tower opens into the shop through
// a pointed doorway, so the one light fills both.
//
// THE BLOCK is the first Victorian cottage's (data/trash 20260930-002, commit
// a8eea51): brick skin, quoins, gables, kneelers, eave flare, bargeboards,
// slates and snow, windows and keystones, all with their WHY comments there.
// It is drawn in the cottage's own frame, gables on +-y, and turned into place
// by blk(): local x is the world's y (front to back), local y is minus the
// world's x. THE TOWER is the gingerbread turret house's (round wall, swept
// cone, the partition where it runs through the shop, windows laid round it in
// strips); THE BAY and everything else is drawn in world coordinates.
//
// COLOUR PARTS, ONE PRINT (victorian_toy_shop.3mf), priority
// roof > accent > trim > body:
//   body    brick: the shop, the tower, the kneelers, the chimney, the wreath's
//           bow, the step
//   roof    slate: the gable roof, the bay's roof, the cone, the finial, the door
//   trim    white: snow base and drifts, quoins, string course and collars,
//           eave soffits, icicles, bargeboards and gable finials, snow on the
//           roofs, every window's frame, keystone, bars and pane, the door
//           frame, the bay's glass, the letters TOYS
//   accent  evergreen: the bay shopfront, the window boxes, the wreath

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// =====================================================================================
// THE BLOCK, in the cottage's frame
// =====================================================================================
W        = 50;              // local x: the world's depth, front to back
D        = 56;              // local y: the world's width
wall     = 1.68;
corner_r = 1.5;
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;
module blk() rotate([0, 0, 90]) children();

bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

H1    = 30;                 // the string course: top of the shop floor
H     = 58;                 // the gable roof's eave line, at the wall's inside
r_ang = 55;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.6;

module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b, sh = SH) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up(sh) translate([0, 0, a]) linear_extrude(b - a) translate([0, -sh * d0]) children();
}
module relief_up(d0, d1, sh = SH) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1, sh) children(1);
    }
}
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// ---- brick walls ---------------------------------------------------------------------
function rpts(w, d, g, z) = [for (p = rrect_pts(w + 2*g, d + 2*g, corner_r + g, 5)) [p[0], p[1], z]];
module brick_skin(ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(W, D, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(W, D, g, z)],
        [rpts(W, D, 0, ztop + 2)]), slices = 0);
}
// QUOINS on the three corners the tower leaves free
q_long = 6.2;  q_short = 3.6;  q_off = 0.5;
nq     = 8;                 // pairs of courses: up to zc(16) = 50
function q_len(j, gable) = (j % 2 == 0) == gable ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) if (!(sx < 0 && sy > 0)) let (z0 = zc(2 * j), z1 = zc(2 * j + 2)) {
        translate([sx > 0 ? Wh - q_len(j, true) : -Wh - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0]);
        translate([sx > 0 ? Wh - 0.5 : -Wh - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0]);
    }
}
module quoins() intersection() { brick_skin(zc(2 * nq) + 2); quoin_boxes(); }

// THE STRING COURSE: a white band round the block at the first floor, its
// underside rising at 55 deg as it comes out
sc_o = 0.9;                 // proud of the brick
// its foot 0.3 inside the wall's plane: started 0.2 inside the brick's face it
// stood 0.21 proud of the course groove under it, a ledge the slicer propped
// its foot at H1 - 2.4 so its upright face is 1.4 tall: from H1 - 1.6 that face
// was 0.6, a lip the gate measured at 0.84 all round the block
module string_course() skin([rpts(W, D, -0.3, H1 - 2.4), rpts(W, D, bd + sc_o, H1 - 2.4 + (bd + sc_o + 0.3) * tan(55)),
                             rpts(W, D, bd + sc_o, H1 + 1.6)], slices = 0);

// ---- regions ---------------------------------------------------------------------------
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Dh - wall, Dh + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module kneelers() {
    for (s = [-1, 1], m = [0, 1]) mirror([0, s < 0 ? 1 : 0, 0]) mirror([m, 0, 0])
        xz(Dh - wall, Dh - 0.05) polygon([[Wh - 0.3, z_ceil(Wh - 0.3)], [xf, z_ceil(xf)], [xe, fl_xe],
                                        [xe, z_out(xe) + 1], [Wh - 0.3, z_out(Wh - 0.3) + 1]]);
}
module eave_flare() {
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh - 0.15, Dh + 0.15)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
module walls_solid() {
    intersection() {
        brick_skin(z_out(0) + cp_hi + 1);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}
module blk_room() intersection() {
    translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
    below_ceil();
}

// ---- windows ---------------------------------------------------------------------------
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
function lancet_pts(a, hgt, ang = 58, n = 12) =
    let (R = 2 * a, t1 = 90 - ang, xt = a - R + R * cos(t1), zt = hgt + R * sin(t1), ap = zt + xt * tan(ang))
    concat([[-a, 0], [a, 0]],
           [for (i = [0 : n]) let (t = t1 * i / n) [a - R + R * cos(t), hgt + R * sin(t)]],
           [[0, ap]],
           [for (i = [n : -1 : 0]) let (t = t1 * i / n) [-(a - R + R * cos(t)), hgt + R * sin(t)]]);
function lancet_top(a, hgt, ang = 58) =
    let (R = 2 * a, t1 = 90 - ang) hgt + R * sin(t1) + (a - R + R * cos(t1)) * tan(ang);
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);

mull = 1.68;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.4;
// [face, u, z, a, straight height, kind]. Faces in the cottage's frame:
// 0 = world left gable, 1 = right gable, 2 = back, 3 = FRONT (u = -world x).
UZ = H1 + 5;                // the upper floor's windows
WINDOWS = [
    [3,   0, UZ, 4.0, 8, "seg"],  [3, -16, UZ, 4.0, 8, "seg"],
    [2,  10, 14, 4.6, 10, "seg"], [2, -12, 14, 4.6, 10, "seg"], [2, 10, UZ, 4.0, 8, "seg"], [2, -12, UZ, 4.0, 8, "seg"],
    [1,   0, 14, 4.6, 10, "seg"], [1, 0, UZ, 4.0, 8, "seg"], [1, 0, 64, 3.6, 10, "lancet"],
    [0,   8, 14, 4.6, 10, "seg"], [0, 8, UZ, 4.0, 8, "seg"], [0, 0, 64, 3.6, 10, "lancet"],
];
function is_seg(w) = w[5] == "seg";
function w_top(w) = is_seg(w) ? seg_top(w[3], w[4]) : lancet_top(w[3], w[4]);
module win_outline(w) { polygon(is_seg(w) ? seg_pts(w[3], w[4]) : lancet_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, is_seg(w) ? 40 : w[4] + mull + 3]);
    if (is_seg(w)) translate([-20, w[4] * 0.55]) square([40, 2.2]);
    else for (s = [-1, 1]) translate([0, w[4]]) rotate(s < 0 ? 180 - 62 : 62)
        translate([0, -mull/2]) square([3 * w[3], mull]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_outer(w) {
    offset(r = fr_w) win_outline(w);
    if (is_seg(w)) translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]);
}
module keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2]) polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
module blk_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module blk_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module blk_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
    if (is_seg(w)) relief_up(-0.4, fr_t + 0.5) keystone(w);
    relief_up(-0.4, bd) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
// window boxes under the two upstairs front windows
module box2d(w) {
    bw = w[3] + fr_w + 0.4;
    translate([-bw, -sill - 4.4]) square([2 * bw, 4.4 + 0.9]);
    for (i = [0 : 5]) let (x = -bw + 1.2 + i * (2 * bw - 2.4) / 5)
        translate([x, -sill + 0.7]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_boxes() for (w = WINDOWS) if (w[0] == 3) nf(w[0], w[1], w[2]) relief_up(-0.4, bd + 1.4) box2d(w);

// ---- icicles under the front and back eaves, clear of the tower and the windows' heads ----
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 18]) [-Dh + 2.4 + i * (D - 4.8) / 18, 2.4 + 2.4 * rnd(i, 40), 1.8 + 0.6 * rnd(i, 80)]];
function ic_clear(f, u) = len([for (w = WINDOWS) if (w[0] == f && w[2] == UZ && abs(u - w[1]) < w[3] + fr_w + 2.2) 1]) == 0
                          && !(f == 3 && u > Dh - 13.5);
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [2, 3], c = IC) if (ic_clear(f, f == 3 ? c[0] : -c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

// ---- bargeboards and finials on the two gables -------------------------------------------------
bb_h  = 6.2;  bb_t = 1.3;  sc_r = 1.9;  sc_ds = 4.3;
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
function sc_pts() = [for (i = [1 : 20]) let (s = i * sc_ds, x = s * cos(r_ang)) if (x < Wh - 2.6) x];
module board2d(ext) {
    X = Wh - 1;
    T = cp_hi - 0.3 + ext;
    polygon([[-X, z_out(X) + T], [0, z_out(0) + T], [X, z_out(X) + T],
             [X, z_out(X) - bb_h + sc_r], [0, z_out(0) - bb_h + sc_r], [-X, z_out(X) - bb_h + sc_r]]);
    for (x = concat([0], sc_pts(), [for (x = sc_pts()) -x])) translate([x, z_out(x) - bb_h + sc_r]) circle(r = sc_r);
}
module bargeboards() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0]) {
        xz(Dh - wall - 0.3, Dh - 0.05) gable_poly(cp_lo, cp_hi);
        intersection() {
            xz(Dh - 0.1, Dh + bd + bb_t) minkowski() { board2d(0); translate([-0.01, -60]) square([0.02, 60]); }
            multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
                xz(Dh - 1, Dh + 4) board2d(10);
        }
    }
}
fin_z = z_out(0) + cp_hi;
module finials() for (s = [-1, 1]) translate([0, s * (Dh - 0.2), fin_z - 2.8]) {
    translate([-1.3, -1.3, 0]) cube([2.6, 2.6, 7.8]);
    translate([0, 0, 7.8]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0, h = 1.3 * tan(60) * 1.2, $fn = 4);
}

// ---- the gable roof --------------------------------------------------------------------------------
y_rr = y_r + 0.4;
module slab() xz(-y_rr, y_rr) polygon([[-xe, fl_xe], [-xf, z_ceil(xf)], [0, z_ceil(0)], [xf, z_ceil(xf)], [xe, fl_xe],
                                     [xe, z_out(xe)], [0, z_out(0)], [-xe, z_out(xe)]]);
sh_c = 2.35;
function sh_d(k) = min(k * sh_c, xe - 0.6);
module slates() {
    nk = ceil((xe - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (x0 = s * (xe - sh_d(k)), x1 = s * (xe - min(sh_d(k + 1) + 0.5, xe - 0.6)))
        xz(-y_rr, y_rr) polygon([[x0, z_out(x0) - 1.0], [x0, z_out(x0) + 1.0], [x1, z_out(x1) + 0.05], [x1, z_out(x1) - 1.0]]);
    // the ridge bead's peak level with the slates' ridge, under the snow's rounded crest
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0)], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
sn_x = 12;
function sn_edge(y) = sn_x + 2.2 * sin(y * 17) + 1.3 * sin(y * 41 + 60);
// the crest rounded (radius sn_rc, tangent to both slopes): drawn to a point it
// was a knife edge the length of the ridge, the thinnest wall in the model
sn_rc = 2.2;
sn_zc = z_out(0) + 2.0 - sn_rc / cos(r_ang);
module snow_roof() intersection() {
    xz(-y_rr - 0.4, y_rr + 0.4) polygon(concat([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                           [xe, z_out(xe) + 2.0]],
                           [for (a = [r_ang : -5 : -r_ang]) [sn_rc * sin(a), sn_zc + sn_rc * cos(a)]],
                           [[-xe, z_out(xe) + 2.0]]));
    translate([0, 0, 40]) linear_extrude(100)
        polygon(concat([for (i = [0 : 40]) let (y = -Dh + 2 * Dh * i / 40) [sn_edge(y), y]],
                       [for (i = [40 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 40) [-sn_edge(-y), y]]));
}

// ---- the chimney, back right -------------------------------------------------------------------------
ch = [5, 12, -20, -13];     // local x0, x1, y0, y1: world x 13..20, y 5..12
ch_top = 104;
module chimney() difference() {
    union() {
        translate([ch[0], ch[2], 40]) cube([ch[1] - ch[0], ch[3] - ch[2], ch_top - 40]);
        hull() {
            translate([ch[0], ch[2], ch_top - 1.3]) cube([ch[1] - ch[0], ch[3] - ch[2], 0.01]);
            translate([ch[0] - 0.8, ch[2] - 0.8, ch_top]) cube([ch[1] - ch[0] + 1.6, ch[3] - ch[2] + 1.6, 1.6]);
        }
        for (y = [ch[2] + 2.0, ch[3] - 2.0]) translate([(ch[0] + ch[1]) / 2, y, ch_top + 1.4]) cylinder(d = 3.4, h = 4.2, $fn = 32);
    }
    below_ceil();
    for (y = [ch[2] + 2.0, ch[3] - 2.0]) translate([(ch[0] + ch[1]) / 2, y, ch_top + 3.4]) cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimney_col() translate([ch[0], ch[2], 40]) cube([ch[1] - ch[0], ch[3] - ch[2], 80]);

// ---- brick joints ---------------------------------------------------------------------------------------
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, ztop, boxes) {
    L = (f < 2 ? Wh : Dh) - q_long - 1;
    nf(f, 0, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes) && (f >= 2 || z1 < z_out(abs(u) + 1) - bb_h - 1.5))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}
function frame_box(f, w) = let (lu = loc(f, w[1]), h = w[3] + fr_w + 2.5)
    [lu - h, lu + h, w[2] - sill - 5 - (w[0] == 3 ? 5 : 0), w[2] + w_top(w) + fr_w + 4];
// in each face's joint coordinate (loc): on the front and the left gable it is
// the world's x and y, and the tower and the bay's roof keep joints away
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    [[-100, 100, H1 - 2.2, H1 + 2.2]],
    f >= 2 ? [[-100, 100, zf0 - 6, 300]] : [],
    f == 3 ? [[-100, -14.5, 0, 300], [-9, 21.5, 0, 34]] : [],
    f == 0 ? [[11.5, 100, 0, 300]] : []);
module joints() for (f = [0 : 3]) wall_joints(f, f < 2 ? z_out(0) + cp_hi : H + 2, face_boxes(f));

// =====================================================================================
// THE TOWER, in world coordinates, on the block's front-left corner
// =====================================================================================
TC   = [-Dh, -Wh];          // the corner itself: world x -28, y -25
rt   = 11.5;
rti  = rt - wall;
FNT  = 160;
fl_ang_t = 52;
// THE SWEPT PROFILE (the shop-house's), turned: a cone at 60 deg that eases to
// 35 deg at the eave and kicks out into a bell
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang_t);
sb = 1.8;
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
module R_full(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
// its corner 0.01 inside the eave's foot: on it the two outlines share the
// foot's edge and leave a zero-width ring (the round cottage, 236 edges)
module R_slate(R, kv0) polygon([[0, -10], [kv0 - 0.01, -10], [kv0 - 0.01, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_room(R) polygon([[0, -2], [R[1], -2], [R[1], R[0]], [0, R_zc(R, 0)]]);

z_tw = 96;                  // the cone's eave line: level with the gable's ridge
RC   = [z_tw, rti, tan(60), tr / cos(60), rt - 2.5, rt + 3, 35, rt + 3];
kv0c = rt - 0.8;
function zst(v) = R_zs(RC, v);
module at_tc() translate([TC[0], TC[1], 0]) children();
module turret_cut() at_tc() translate([0, 0, -1]) cylinder(r = rt - 0.3, h = 200, $fn = FNT);

// the brick wall: courses bulging out bd, from the snow into the cone
function tbrick_prof(zt) = concat([[rti - 0.3, plinth_h - 0.5], [rt, plinth_h - 0.5]],
    [for (k = [0 : nc(zt) - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < zt + 1) [rt + g, z]],
    [[rt, zt + 2], [rti - 0.3, zt + 2]]);
module tower_walls() at_tc() intersection() {
    rotate_extrude($fn = FNT) polygon(tbrick_prof(R_zc(RC, rti - 0.3) + 1));
    // its top 0.6 up into the cone, on the ceiling's line
    rotate_extrude($fn = FNT) polygon([[0, -5], [rt + 5, -5], [rt + 5, R_zc(RC, rt + 5) + 0.6], [0, R_zc(RC, 0) + 0.6]]);
}
module tower_room() at_tc() rotate_extrude($fn = FNT) R_room(RC);
// THE PARTITION (the turret house's). Where the tower's wall runs through the
// shop, the shop's room would take it away up to the gable's ceiling, leaving
// an arch with a level crown hanging over the floor. The wall is kept down to
// a pointed doorway instead, its sides falling 0.235 mm per degree of ring
// (52 deg on the outer face) from 57 mm on the line to the shop's centre.
pt_a = 57;
pt_k = 0.235;
module turret_partition() let (r0 = rti - 0.5, r1 = rt + 0.2, n = 180, top = 140,
        P = [for (i = [0 : n]) let (th = -45 + i, zb = pt_a - pt_k * abs(th - 45))
                 each [[r0 * cos(th), r0 * sin(th), zb], [r1 * cos(th), r1 * sin(th), zb],
                       [r1 * cos(th), r1 * sin(th), top], [r0 * cos(th), r0 * sin(th), top]]])
    at_tc() polyhedron(P, concat(
        [for (i = [0 : n - 1], j = [0 : 3]) [4 * i + (j + 1) % 4, 4 * (i + 1) + (j + 1) % 4, 4 * (i + 1) + j, 4 * i + j]],
        [[3, 2, 1, 0], [4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3]]));

// the cone, its slate courses, its white soffit, snow on its crown, a finial
module cone_roof() at_tc() intersection() {
    rotate_extrude($fn = FNT) R_full(RC, kv0c);
    rotate_extrude($fn = FNT) R_slate(RC, kv0c);
}
module cone_curl() at_tc() rotate_extrude($fn = FNT) R_curl(RC, kv0c);
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module cone_slates() at_tc() {
    ve = RC[5];
    // stopped under the snow cap (out to 6.2): run up to the tip, every
    // course's step cut the cap's edge into slivers under 1 mm
    nk = ceil((ve - 6.8) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 6.8))
        if (x0 > x1 + 0.3) rotate_extrude($fn = FNT) course_band(RC, x0, x1);
}
function wave(t) = 1.2 * sin(t * 3.0) + 0.8 * sin(t * 7.0 + 60);
module cone_snow() at_tc() intersection() {
    rotate_extrude($fn = FNT) polygon([[0, zst(0) - 1.0], [6, zst(6) - 1.0], [6, zst(6) + 1.8], [2, zst(2) + 2.2], [0, zst(0) + 2.4]]);
    translate([0, 0, 80]) linear_extrude(60) polygon([for (i = [0 : 179]) let (a = 2 * i) (4.2 + wave(a)) * [cos(a), sin(a)]]);
}
t_fin = zst(0) + 1.6;
module tower_finial() at_tc() translate([0, 0, t_fin - 2.4]) {
    translate([-1.1, -1.1, 0]) cube([2.2, 2.2, 6.6]);
    // its point blunted to 0.35: sharp, its last 0.33 mm never printed
    translate([0, 0, 6.6]) rotate([0, 0, 45]) cylinder(r1 = 1.1 * sqrt(2), r2 = 0.35, h = 1.1 * tan(60) * 1.0, $fn = 4);
}
// COLLARS: the string course carried round the tower, and one where it clears
// the gable's eave
TCOL = [H1, 70];
module collars() at_tc() for (z = TCOL) rotate_extrude($fn = FNT)
    // foot 2.7 down, so the slope reaches the face at z + 0.16 like the block's band;
    // from z - 0.5 it overshot the band's top and the outline crossed itself
    polygon([[rt - 0.5, z - 2.7], [rt + bd + sc_o, z - 2.7 + (bd + sc_o + 0.5) * tan(55)], [rt + bd + sc_o, z + 1.6], [rt - 0.5, z + 1.6]]);

// ---- the tower's windows and door, laid round it -----------------------------------------------
module cplace(r, th, z) translate([TC[0] + r * cos(th), TC[1] + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module tclip(d) intersection() { children(); at_tc() cylinder(r = rt + d, h = 200, $fn = FNT); }
// [angle, sill, a, straight height, kind]; 0 deg runs along the shop's front,
// 90 along its left gable: the tower's outside is 90..360
TW = [[180, 14, 3.4, 9, "seg"], [215, 40, 3.4, 9, "seg"], [290, 40, 3.4, 9, "seg"],
      [250, 62, 3.4, 9, "seg"], [160, 62, 3.4, 9, "seg"],
      [225, 78, 2.8, 7, "lancet"], [135, 78, 2.8, 7, "lancet"], [315, 78, 2.8, 7, "lancet"]];
function tw(w) = [0, 0, 0, w[2], w[3], w[4]];      // as a block window, for the outline helpers
function tframe_U(w) = w[2] + fr_w + 1.4;
module tw_frames() tclip(fr_t + 0.5) for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) {
    relief_up(-0.4, fr_t) { frame_outer(tw(w)); offset(r = 0.3) win_outline(tw(w)); }
    if (is_seg(tw(w))) relief_up(-0.4, fr_t + 0.5) keystone(tw(w));
}
module tw_bars() tclip(bd) for (w = TW) cyl_relief(rt, w[0], w[1], w[2] + 1) relief_up(-0.4, bd) win_muntins(tw(w), 0.6);
module tw_glass() intersection() {
    for (w = TW) cplace(rt, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(tw(w));
    at_tc() cylinder(r = rt - 0.2, h = 200, $fn = FNT);
}
// in strips like the holes: cut flat, on this curve the opening and the holes
// left slivers of brick beside every window, each its own loose body
module tw_openings() for (w = TW) cyl_relief(rt, w[0], w[1], w[2] + 1) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(tw(w));
// the holes in strips, like the frames: cut flat on this curve they cross the
// frames' strips (the turret house: edges in the wall)
module tw_holes() for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(tw(w));

// THE DOOR at the tower's foot, facing the street and the corner
dth = 247;
dr_a = 4.0;  dr_h = 12;
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() difference() {
    intersection() {
        cplace(rt, dth, plinth_h) translate([0, 0, -wall - 1]) linear_extrude(wall + 2)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(dr_a, dr_h + 0.3));
        at_tc() difference() { cylinder(r = rt + 0.2, h = 100, $fn = FNT); translate([0, 0, -1]) cylinder(r = rti + 0.15, h = 102, $fn = FNT); }
    }
    // panels sunk 0.3 into its face, in strips so the depth follows the curve
    cyl_relief(rt + 0.2, dth, plinth_h, dr_a + 0.6) translate([0, 0, -0.3]) linear_extrude(2) {
        panel2d(-2.9, -0.6, 1.6, 5.8);  panel2d(0.6, 2.9, 1.6, 5.8);
    }
}
module door_opening() cplace(rt, dth, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(dr_a, dr_h));
module door_hole() cyl_relief(rt, dth, plinth_h, dr_a + 2.4) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(dr_a, dr_h));
module door_frame() tclip(fr_t) cyl_relief(rt, dth, plinth_h, dr_a + 3) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.8) polygon(arch_pts(dr_a, dr_h)); translate([-30, -0.5]) square([60, 100]); }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(dr_a, dr_h + 1));
}
wr_z = plinth_h + dr_h - 1.5;
module wreath() tclip(bd + 0.8) cyl_relief(rt, dth, wr_z, 4.2) relief_up(-0.4, bd + 0.8) difference() { circle(r = 3.2, $fn = 40); circle(r = 1.7, $fn = 32); }
module bow2d() {
    polygon([[0, 0], [-2.2, 1.1], [-2.2, -1.1]]);  polygon([[0, 0], [2.2, 1.1], [2.2, -1.1]]);
    circle(r = 0.8);
    polygon([[-0.4, 0], [-1.2, -1.9], [-0.4, -1.9], [0.1, -0.5]]);
    polygon([[0.4, 0], [1.2, -1.9], [0.4, -1.9], [-0.1, -0.5]]);
}
module wreath_bow() tclip(bd + 1.2) cyl_relief(rt, dth, wr_z - 3.2, 2.8) relief_up(-0.4, bd + 1.2) bow2d();
module step() intersection() {
    at_tc() translate([0, 0, plinth_h - 0.5]) difference() { cylinder(r = rt + 3.4, h = 1.9, $fn = FNT); translate([0, 0, -1]) cylinder(r = rt - 0.5, h = 4, $fn = FNT); }
    at_tc() rotate([0, 0, dth - 12]) rotate_extrude(angle = 24, $fn = FNT) square([60, 20]);
}

// =====================================================================================
// THE BAY SHOP WINDOW, on the front
// =====================================================================================
BX  = 6;                    // its centre, world x
BP  = 4.5;                  // how far it stands out from the wall
BF  = 9;                    // the front face's half-width
yw  = -Wh;                  // the wall's face
BPOLY = [[BX - BF - BP, yw + 1.2], [BX - BF - BP, yw], [BX - BF, yw - BP], [BX + BF, yw - BP], [BX + BF + BP, yw], [BX + BF + BP, yw + 1.2]];
by_g = [13, 22];            // the glazing
by_t = 26.5;                // its top; the fascia is between
// its three faces: [centre, outward normal angle, half-length]
BFACES = [[[BX - BF - BP / 2, yw - BP / 2], 225, BP * sqrt(2) / 2], [[BX, yw - BP], -90, BF], [[BX + BF + BP / 2, yw - BP / 2], -45, BP * sqrt(2) / 2]];
module bplace(i, z) let (f = BFACES[i]) translate([f[0][0], f[0][1], z]) rotate([0, 0, f[1] + 90]) rotate([90, 0, 0]) children();
// the panes: on the front two, split by a mullion; one on each side
// the side panes stop 1.6 short of each end: at 1.0 the pane's end fell in
// the corner post, and the post met the next face's wall along edges
function bpanes(i) = i == 1 ? [[-BF + 1.2, -0.7], [0.7, BF - 1.2]] : [[-BFACES[i][2] + 1.6, BFACES[i][2] - 1.6]];
module bay_solid() translate([0, 0, plinth_h - 0.5]) linear_extrude(by_t - plinth_h + 0.5) polygon(BPOLY);
// its inside, open to the shop; the ceiling rises at 55 deg from the glazing's
// head into the shop, so it is a slope, not a bridge
by_c0 = by_g[1] + 1.2;
yb_in = yw - BP + wall;
module bay_room() intersection() {
    translate([0, 0, -2]) linear_extrude(60) union() {
        offset(delta = -wall) polygon(BPOLY);
        translate([BX - BF - BP + wall + 0.3, yw - 0.5]) square([2 * (BF + BP) - 2 * wall - 0.6, 3.5]);
    }
    // a profile in (y, z), so swept along x: drawn with xz() it lay in (x, z)
    // and the bay's inside came out solid, its panes sealed voids in it
    yz(-60, 60) polygon([[yb_in - 5, -5], [yb_in - 5, by_c0], [yb_in, by_c0], [yw + 10, by_c0 + (yw + 10 - yb_in) * tan(55)], [yw + 10, -5]]);
}
module bay_openings() for (i = [0 : 2], p = bpanes(i)) bplace(i, by_g[0]) translate([p[0], 0, -wall - 0.3]) cube([p[1] - p[0], by_g[1] - by_g[0], wall + 0.6]);
// the glass fills each opening through the wall's thickness, so the head of
// the opening rests on it
// exactly the wall's thickness: 0.3 into the bay, its ends met the openings'
// ends and the side walls' inner faces along edges shared by four faces
// the side panes stand 0.3 back from both faces: those walls are at 45 deg, and
// their faces (an offset outline) and the glass's (a rotation) never quite
// agree, so a flush pane left zero-width walls along its ends, six edges each
// shared by four faces. And they run 0.4 into the wall at each end: the trim
// part loses what the bay's wall owns, so their ends are cut by the opening's
// own faces. Ending exactly at the opening, the two rotated boxes' faces did
// not meet and the panes came out as loose bodies
module bay_glass() for (i = [0 : 2], p = bpanes(i)) let (k = i == 1 ? 0 : 0.3, x = i == 1 ? 0 : 0.4)
    bplace(i, by_g[0]) translate([p[0] - x, 0, -wall + k]) cube([p[1] - p[0] + 2 * x, by_g[1] - by_g[0], wall - 2 * k]);
// a transom bar across each front pane, on the glass. Not on the side panes:
// 3.2 wide, at 45 deg, their bars' ends met the panes' ends and the posts along
// edges shared by four faces
module bay_transoms() for (i = [1], p = bpanes(i)) bplace(i, by_g[0] + 6) relief_up(-0.4, 0.6) translate([p[0] - 0.3, 0]) square([p[1] - p[0] + 0.6, 1.2]);
// the hipped roof: from the bay's top edges up into the wall at 45 deg
module bay_roof() hull() {
    translate([0, 0, by_t - 0.01]) linear_extrude(0.01) polygon(BPOLY);
    translate([BX - BF - BP, yw + 0.4, by_t + BP]) cube([2 * (BF + BP), 0.8, 0.01]);
}
// the letters, raised on the fascia
module toys() bplace(1, (by_g[1] + by_t) / 2 + 0.2) relief_up(-0.4, 0.6)
    text("TOYS", size = 4.2, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.12);

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() {
    translate([-Dh, -Wh]) square([D, W]);
    translate(TC) circle(r = rt + bd, $fn = FNT);
    polygon(BPOLY);
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[Dh + 1, 10, 4, 7, 3.2], [-Dh - 1, 14, 4, 6, 2.6], [-12, Wh + 1, 7, 3.5, 2.8], [18, Wh + 1, 6, 3.5, 2.4],
          [TC[0] + (rt + 1) * cos(170), TC[1] + (rt + 1) * sin(170), 4, 4, 2.4]];
module base() {
    base_slab();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.5]) intersection() {
            scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -2.4) base2d();
    }
}
// under the bay, between its opening and the base's edge
module brand_mark() translate([BX, yw - BP - 3.2, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() {
    difference() { blk() blk_room(); turret_partition(); }
    tower_room();
    bay_room();
}
module body_raw() {
    difference() { blk() { walls_solid(); chimney(); } turret_cut(); }
    tower_walls();
    intersection() { bay_solid(); translate([-60, -60, 0]) cube([120, 120, by_g[0] - 1.6]); }
    wreath_bow();
    step();
}
module roof_raw() {
    difference() { blk() difference() { union() { slab(); slates(); } blk_room(); chimney_col(); } turret_cut(); }
    difference() { union() { cone_roof(); cone_slates(); } tower_room(); }
    tower_finial();
    // cut by the room: where it runs back into the wall over the bay's opening
    // into the shop, it hung over the shop
    difference() { bay_roof(); room(); }
    door_leaf();
}
module accent_raw() {
    difference() {
        intersection() { bay_solid(); translate([-60, -60, by_g[0] - 1.6]) cube([120, 120, 60]); }
        bay_room();
        bay_openings();
    }
    bay_transoms();
    // cut by the room: the left box's back runs 0.4 into the wall, and over
    // the bay's opening into the shop that left it hanging as a fin
    difference() { blk() window_boxes(); turret_cut(); room(); }
    wreath();
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() {
                blk() union() {
                    quoins();
                    string_course();
                    eave_flare();
                    icicles();
                    bargeboards();
                    finials();
                    difference() { snow_roof(); chimney_col(); }
                    blk_windows();
                }
                turret_cut();
            }
            collars();
            cone_curl();
            cone_snow();
            tw_frames();
            tw_bars();
            door_frame();
            toys();
        }
        // no openings: the panes sit in them, and the frames' heads have their
        // own sheared holes. Cut by the tower's openings, every frame head was
        // trimmed to the window's own flat-topped outline: a 1.2 mm ledge
        room();
        brand_mark();
    }
    // the glass goes back in after the rooms and openings are cut
    difference() { union() { tw_glass(); bay_glass(); } room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        // the bay's panes reach back into the wall: without these, brick stood
        // loose inside each side pane
        room(); bay_room(); bay_openings();
        blk() { blk_openings(); blk_frame_holes(); joints(); }
        tw_openings(); tw_holes(); door_opening(); door_hole();
        trim_raw(); accent_raw(); roof_raw();
    }
}

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
// a quick look without the cuts, for the preview renderer
else if (part == "preview") {
    color("#A8483A") { blk() { walls_solid(); chimney(); } tower_walls(); bay_solid(); }
    color("#2E3440") { blk() { slab(); slates(); } cone_roof(); cone_slates(); tower_finial(); bay_roof(); door_leaf(); }
    color("#F4F1EA") { base(); blk() { quoins(); string_course(); eave_flare(); icicles(); bargeboards(); finials(); snow_roof(); blk_windows(); }
                       collars(); cone_curl(); cone_snow(); tw_frames(); door_frame(); toys(); }
    color("#2F6B45") { blk() window_boxes(); wreath(); }
}
else if (part == "all") {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
