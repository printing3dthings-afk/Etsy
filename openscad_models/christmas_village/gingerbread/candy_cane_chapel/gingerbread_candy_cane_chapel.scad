// Gingerbread Candy Cane Chapel -- building #2 of the Gingerbread village, and
// its first to join round and square (Scott, 2026-09-30: "I want to incorporate
// round and square together on some buildings ... Do all different shapes and
// stories of the buildings", and picked this form from four).
//
// A one-storey square gingerbread nave under a steep chocolate gable, icing
// piped down its corners and dripping off its eaves and rakes, gumdrops along
// the ridge, three tall arched windows down each side and a peppermint window
// in the back gable. At its front a round tower stands half out of the gable:
// white icing striped red in a spiral all the way up, like a candy cane, under
// a spire striped the same way whose tip curls over like a cane's crook. The
// chocolate-bar door is at the tower's foot, candy canes stand either side on
// the nave's front, peppermints lie on the snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The tower opens into the nave through
// a pointed doorway, and its white walls glow with the stripes dark on them.
//
// THE NAVE is the first gingerbread cottage's (data/trash 20260930-003, commit
// 7de06df), in its own frame: gables on +-y, the front at -y. THE TOWER is the
// Victorian toy shop's (../../victorian/toy_shop): the round wall, the
// partition where it runs through the nave, windows laid round it in strips.
//
// COLOUR PARTS, ONE PRINT (gingerbread_candy_cane_chapel.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the nave's walls, the kneelers
//   roof    chocolate: the nave's roof and its scallop tiles, the door
//   trim    icing: snow base, corner beads, eave soffit and drips, rakes and
//           their drips, icing on the ridge, window and door frames with their
//           beads, panes and bars, the tower, the spire and its crook, the
//           canes' and peppermints' white
//   accent  candy red: gumdrops, the tower's, spire's and crook's stripes, the
//           canes' and peppermints' stripes, the round window's wedges

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// =====================================================================================
// THE NAVE
// =====================================================================================
W        = 52;              // across, x
D        = 58;              // front to back, y
wall     = 1.68;
corner_r = 2.5;
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;

// H puts a 46 mm circle's edge 50.5 mm up under the ceiling: the series' tealight rule
H     = 49;
r_ang = 55;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.2;

module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}

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
        xz(Dh - wall, Dh - 0.05) polygon([[Wh - corner_r - 0.3, z_ceil(Wh - corner_r - 0.3)], [xf, z_ceil(xf)], [xe, fl_xe],
                                        [xe, z_out(xe) + 1], [Wh - corner_r - 0.3, z_out(Wh - corner_r - 0.3) + 1]]);
}
module eave_flare() {
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh - 0.15, Dh + 0.15)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
module walls_solid() {
    intersection() {
        translate([0, 0, plinth_h - 0.5]) linear_extrude(200) rect([W, D], rounding = corner_r);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}
module nave_room() intersection() {
    translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
    below_ceil();
}

// ---- piped icing ----------------------------------------------------------------------------
bead_r  = 1.2;
bead_sp = 2.0;
function arch_path(a, hgt, o, sp, bottom = true) =
    let (A = a + o, b0 = bottom ? 2 * A : 0, b1 = b0 + hgt + o, b2 = b1 + PI * A, P = b2 + hgt + o,
         n = round(P / sp))
    [for (i = [0 : n - 1]) let (t = i * P / n)
        t < b0 ? [-A + t, -o] :
        t < b1 ? [A, -o + (t - b0)] :
        t < b2 ? let (q = (t - b1) / A * 180 / PI) [A * cos(q), hgt + A * sin(q)] :
                 [-A, hgt - (t - b2)]];
module beads(pts, r = bead_r) for (p = pts) translate(p) circle(r = r);
cb_r = 1.3;  cb_sp = 1.7;
function bead_rad(z, n) = max([for (i = [0 : n]) let (d = z - i * cb_sp) abs(d) < cb_r ? sqrt(cb_r * cb_r - d * d) : 0]);
function bead_profile(n, k = 12) = let (z0 = -cb_r, z1 = n * cb_sp + cb_r, m = ceil((z1 - z0) / cb_sp * k))
    concat([[0, z0]], [for (j = [1 : m - 1]) let (z = z0 + (z1 - z0) * j / m) [bead_rad(z, n), z]], [[0, z1]]);
module corner_beads() {
    n = floor((zf0 - 1 - plinth_h) / cb_sp);
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * (Wh - corner_r + (corner_r + 0.35) / sqrt(2)), sy * (Dh - corner_r + (corner_r + 0.35) / sqrt(2)), plinth_h + 0.6])
            rotate_extrude($fn = 32) polygon(bead_profile(n));
}

// ---- the nave's windows ---------------------------------------------------------------------
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9;
// [face, u, z, a, straight height, kind]: tall arched windows down each side,
// one in the back and a peppermint high in the back gable
WINDOWS = [
    [2, -16, 14, 4.0, 13, "arch"], [2, 2, 14, 4.0, 13, "arch"], [2, 20, 14, 4.0, 13, "arch"],
    [3, -16, 14, 4.0, 13, "arch"], [3, 2, 14, 4.0, 13, "arch"], [3, 20, 14, 4.0, 13, "arch"],
    [0,   0, 14, 4.0, 13, "arch"], [0, 0, 58, 5.4, 0, "round"],
];
function is_round(w) = w[5] == "round";
function w_top(w) = is_round(w) ? 2 * w[3] : w[4] + w[3];
module win_outline(w) { if (is_round(w)) translate([0, w[3]]) circle(r = w[3]); else polygon(arch_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, is_round(w) ? w[3] - 1.1 : w[4] * 0.6]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame2d(w) {
    if (is_round(w)) translate([0, w[3]]) circle(r = w[3] + 3.2, $fn = 64);
    else {
        offset(r = fr_w) win_outline(w);
        beads(arch_path(w[3], w[4], fr_w - 0.1, bead_sp));
    }
}
module frame_relief(w) relief_up(-0.4, fr_t) { frame2d(w); offset(r = 0.3) win_outline(w); }
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
module nave_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module nave_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) win_outline(w);
module nave_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    frame_relief(w);
    relief_up(-0.4, 0.4) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
module round_wedges() for (w = WINDOWS) if (is_round(w)) nf(w[0], w[1], w[2]) intersection() {
    frame_relief(w);
    translate([0, w[3], -5]) linear_extrude(10) pepper_wedges(w[3] + 3.2);
}

// ---- candy canes on the front, either side of the tower, crooks turned out ------------------------
cane_x = 17.5;  cane_w = 2.6;  cane_h = 22;  cane_R = 3;
module cane2d(dir) {
    translate([-cane_w/2, -0.5]) square([cane_w, cane_h + 0.5]);
    translate([dir * cane_R, cane_h]) intersection() {
        difference() { circle(r = cane_R + cane_w/2); circle(r = cane_R - cane_w/2); }
        translate([-10, 0]) square([20, 10]);
    }
    translate([2 * dir * cane_R - cane_w/2, cane_h - 1.8]) square([cane_w, 1.8]);
}
module stripes2d() for (i = [-12 : 12]) translate([0, i * 3.4]) rotate(35) translate([-20, 0]) square([40, 1.5]);
// face 1's local x runs to -x in the world, so a crook turned out at world
// +x points to local -x
module cane_relief(s) nf(1, s * cane_x, plinth_h) relief_up(-0.4, fr_t + 0.5) cane2d(-s);
module canes(stripes = false) for (s = [-1, 1])
    if (stripes) intersection() { cane_relief(s); nf(1, s * cane_x, plinth_h) translate([0, 0, -5]) linear_extrude(10) stripes2d(); }
    else cane_relief(s);

// ---- eave drips, clear of the windows' heads; rakes ------------------------------------------------
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
DR = [for (i = [0 : 16]) [-Dh + 3 + i * (D - 6) / 16, 1.6 + 3.4 * rnd(i, 70), 2.2 + 0.5 * rnd(i, 90)]];
function dr_clear(f, u) = len([for (w = WINDOWS) if (w[0] == f && abs(u - w[1]) < w[3] + fr_w + bead_r + 1.6) 1]) == 0;
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
module eave_drips() for (f = [2, 3], c = DR) if (dr_clear(f, c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(c[1], c[2]);
rb_h = 3.2;  rb_t = 1.2;
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
RD = [for (i = [0 : 13]) let (x = 1.6 + i * 2.1) if (x < Wh - 2.4) [x, 1.2 + 3.2 * rnd(i, 110), 2.0 + 0.4 * rnd(i, 130)]];
module rake2d(ext) {
    X = Wh - 1;
    polygon([[-X, z_out(X) + cp_hi + ext], [0, z_out(0) + cp_hi + ext], [X, z_out(X) + cp_hi + ext],
             [X, z_out(X) - rb_h], [0, z_out(0) - rb_h], [-X, z_out(X) - rb_h]]);
    for (d = RD, s = [-1, 1]) let (x = s * d[0]) translate([x, z_out(x) - rb_h + 0.6]) drip2d(d[1] + 0.6, d[2]);
}
module rakes() for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0]) {
    xz(Dh - wall - 0.3, Dh - 0.05) gable_poly(cp_lo, cp_hi);
    intersection() {
        xz(Dh - 0.1, Dh + rb_t) minkowski() { rake2d(0); translate([-0.01, -60]) square([0.02, 60]); }
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
            xz(Dh - 1, Dh + 4) rake2d(10);
    }
}

// ---- the nave's roof ----------------------------------------------------------------------------------
y_rr = y_r + 0.4;
module slab() xz(-y_rr, y_rr) polygon([[-xe, fl_xe], [-xf, z_ceil(xf)], [0, z_ceil(0)], [xf, z_ceil(xf)], [xe, fl_xe],
                                     [xe, z_out(xe)], [0, z_out(0)], [-xe, z_out(xe)]]);
tc = 2.6;  sd = 1.3;  tw = 4.8;
module tiles() {
    nk = ceil((xe - 0.6) / tc);
    for (m = [0, 1]) mirror([m, 0, 0]) for (k = [0 : nk - 1])
        let (x0 = xe - k * tc - sd, x0e = min(x0 + sd, xe), x1 = max(xe - (k + 1) * tc - sd - 0.5, 0.6))
        if (x0e > x1 + 0.3) intersection() {
            xz(-y_rr, y_rr) polygon([[x0e, z_out(x0e) - 1.0], [x0e, z_out(x0e) + 1.0], [x1, z_out(x1) + 0.05], [x1, z_out(x1) - 1.0]]);
            translate([0, 0, 30]) linear_extrude(100) intersection() {
                union() {
                    translate([-10, -y_rr - 1]) square([x0 + 10, 2 * y_rr + 2]);
                    for (j = [-8 : 8]) translate([x0, j * tw + (k % 2) * tw / 2]) scale([sd, tw / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                translate([-10, -y_rr - 1]) square([xe + 10, 2 * y_rr + 2]);
            }
        }
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0) + 1.4], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
ic_x = 9;
function ic_edge(y) = ic_x + 1.8 * sin(y * 23) + 1.2 * sin(y * 53 + 40);
module icing_roof() intersection() {
    xz(-y_rr - 0.4, y_rr + 0.4) polygon([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                           [xe, z_out(xe) + 2.0], [3, z_out(3) + 2.0], [0, z_out(0) + 2.4], [-3, z_out(3) + 2.0], [-xe, z_out(xe) + 2.0]]);
    translate([0, 0, 40]) linear_extrude(100)
        polygon(concat([for (i = [0 : 60]) let (y = -Dh + 2 * Dh * i / 60) [ic_edge(y), y]],
                       [for (i = [60 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 60) [-ic_edge(-y), y]]));
}
GD = [-10, 2, 14, 25];
module gumdrops() difference() {
    for (y = GD) hull() {
        translate([0, y, z_out(0) + 1.2]) sphere(r = 2.9, $fn = 32);
        translate([0, y, z_out(0) - 1.43 * 4.2 - 0.5]) cylinder(r = 4.2, h = 0.01, $fn = 32);
    }
    below_ceil();
}

// =====================================================================================
// THE TOWER, standing half out of the front gable
// =====================================================================================
rt   = 11.5;
rti  = rt - wall;
TC   = [0, -Dh - 4];
FNT  = 160;
// its spire: the village's swept profile, steep (68 deg) and white
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang);
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
module R_full(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
module R_room(R) polygon([[0, -2], [R[1], -2], [R[1], R[0]], [0, R_zc(R, 0)]]);
z_tw = 92;                  // the spire's eave line
RS   = [z_tw, rti, tan(68), tr / cos(68), rt - 3, rt + 2.6, 40, rt + 2.6];
kv0s = rt - 0.8;
module at_tc() translate([TC[0], TC[1], 0]) children();
module turret_cut() at_tc() translate([0, 0, -1]) cylinder(r = rt - 0.3, h = 200, $fn = FNT);
module tower_walls() at_tc() rotate_extrude($fn = FNT)
    polygon([[rti - 0.3, plinth_h - 0.5], [rt, plinth_h - 0.5], [rt, R_zc(RS, rt) + 0.6], [rti - 0.3, R_zc(RS, rti - 0.3) + 0.6]]);
module tower_room() at_tc() rotate_extrude($fn = FNT) R_room(RS);
// THE PARTITION: where the tower's wall runs through the nave it is kept down
// to a pointed doorway, its sides falling 52 deg on the outer face from 66 mm
// on the line to the nave's centre (see the toy shop)
pt_a = 66;
pt_k = 0.235;
module turret_partition() let (r0 = rti - 0.5, r1 = rt + 0.2, n = 180, top = 140,
        P = [for (i = [0 : n]) let (th = i, zb = pt_a - pt_k * abs(th - 90))
                 each [[r0 * cos(th), r0 * sin(th), zb], [r1 * cos(th), r1 * sin(th), zb],
                       [r1 * cos(th), r1 * sin(th), top], [r0 * cos(th), r0 * sin(th), top]]])
    at_tc() polyhedron(P, concat(
        [for (i = [0 : n - 1], j = [0 : 3]) [4 * i + (j + 1) % 4, 4 * (i + 1) + (j + 1) % 4, 4 * (i + 1) + j, 4 * i + j]],
        [[3, 2, 1, 0], [4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3]]));
module spire() at_tc() rotate_extrude($fn = FNT) R_full(RS, kv0s);

// THE STRIPES: three red bands winding up at 35 deg from level, the tower's and
// the spire's solid cut by a twisted wedge
st_n = 3;                   // stripes
st_f = 0.36;                // each one's share of its turn
st_P = 2 * PI * rt * tan(35) / 1;   // rise per turn round the tower
module helix(z0, z1) at_tc() translate([0, 0, z0]) for (k = [0 : st_n - 1]) rotate(k * 360 / st_n)
    linear_extrude(z1 - z0, twist = -360 * (z1 - z0) / st_P, slices = ceil((z1 - z0) / st_P * 90), $fn = 60)
        polygon(concat([[0, 0]], [for (i = [0 : 12]) let (a = 360 / st_n * st_f * i / 12) 40 * [cos(a), sin(a)]]));

// THE CROOK: a candy-cane rod from the spire's tip, bending over toward the
// street to 40 deg at its end, the most a rod can lean and print over nothing
cr_n = 12;  cr_L = 11;
function cr_ang(i) = 40 * pow(i / cr_n, 2);
function cr_pts(i) = i == 0 ? [0, 0] : let (p = cr_pts(i - 1)) [p[0] + cr_L / cr_n * sin(cr_ang(i)), p[1] + cr_L / cr_n * cos(cr_ang(i))];
function cr_r(i) = 1.9 - 0.5 * i / cr_n;
cr_z0 = R_top(RS, 0) - 2.5;
module cr_at(i) let (p = cr_pts(i)) translate([TC[0], TC[1] - p[0], cr_z0 + p[1]]) sphere(r = cr_r(i), $fn = 24);
module crook() for (i = [0 : cr_n - 1]) hull() { cr_at(i); cr_at(i + 1); }
module crook_stripes() for (z = [cr_z0 + 1 : 2.4 : cr_z0 + cr_L + 2])
    translate([TC[0], TC[1], z]) rotate([28, 0, 0]) cube([20, 20, 1.0], center = true);

// ---- the tower's windows and door ---------------------------------------------------------------
module cplace(r, th, z) translate([TC[0] + r * cos(th), TC[1] + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module tclip(d) intersection() { children(); at_tc() cylinder(r = rt + d, h = 200, $fn = FNT); }
// [angle, sill, a, straight height]; the tower's outside is where sin < 0.34
TW = [[205, 32, 2.8, 7], [335, 32, 2.8, 7], [270, 44, 3.0, 8], [270, 66, 3.0, 8], [215, 74, 2.6, 6], [325, 74, 2.6, 6]];
function tw(w) = [0, 0, 0, w[2], w[3], "arch"];
function tframe_U(w) = w[2] + fr_w + bead_r + 1.2;
module tw_frames() tclip(fr_t + 0.4) for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) frame_relief(tw(w));
module tw_bars() tclip(0.4) for (w = TW) cyl_relief(rt, w[0], w[1], w[2] + 1) relief_up(-0.4, 0.4) win_muntins(tw(w), 0.6);
module tw_glass() intersection() {
    for (w = TW) cplace(rt, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(tw(w));
    at_tc() cylinder(r = rt - 0.2, h = 200, $fn = FNT);
}
module tw_openings() for (w = TW) cplace(rt, w[0], w[1]) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(tw(w));
module tw_holes() for (w = TW) cyl_relief(rt, w[0], w[1], tframe_U(w)) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(tw(w));

// THE DOOR: a chocolate bar, at the tower's foot facing the street
dth = 270;
door_a = 4.4;  door_h = 13;
module door_leaf() difference() {
    intersection() {
        cplace(rt, dth, plinth_h) translate([0, 0, -wall - 1]) linear_extrude(wall + 2)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
        at_tc() difference() { cylinder(r = rt + 0.2, h = 100, $fn = FNT); translate([0, 0, -1]) cylinder(r = rti + 0.15, h = 102, $fn = FNT); }
    }
    // scored into squares by V grooves, their upper faces leaning 50 deg, run
    // out through the crown; in strips, so they follow the curve
    cyl_relief(rt + 0.2, dth, plinth_h, door_a + 0.8) {
        translate([-0.5, -1, -0.3]) cube([1, door_h + door_a + 4, 1]);
        for (zg = [4.2, 8.4, 12.6]) hull() {
            translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
            translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
        }
    }
}
module door_opening() cplace(rt, dth, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(door_a, door_h));
module door_hole() cyl_relief(rt, dth, plinth_h, door_a + 2.4) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
module door_frame() tclip(fr_t + 0.4) cyl_relief(rt, dth, plinth_h, door_a + fr_w + bead_r + 1.2) relief_up(-0.4, fr_t) {
    union() {
        intersection() { offset(r = fr_w) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
        intersection() { beads(arch_path(door_a, door_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
    }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() { translate([-Wh, -Dh]) square([W, D]); translate(TC) circle(r = rt, $fn = FNT); }
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 8, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[Wh + 1, Dh - 10, 4, 8, 3.4], [-8, Dh + 1, 7, 3.5, 2.8], [-Wh - 1, 6, 4, 6, 2.6]];
PM = [[-21, -Dh - 3.6, 2.6], [22, -Dh - 4.4, 2.2]];
module peppermints(stripes = false) for (p = PM) translate([p[0], p[1], plinth_h - 0.2]) linear_extrude(1.4)
    if (stripes) union() { intersection() { circle(r = p[2]); pepper_wedges(p[2]); } circle(r = 0.8); } else circle(r = p[2]);
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
// under the tower, between its room's opening and the base's edge
module brand_mark() translate([TC[0], TC[1] - rti - 5.2, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() { difference() { nave_room(); turret_partition(); } tower_room(); }
module tower_solid() { tower_walls(); spire(); }
module body_raw() difference() { walls_solid(); turret_cut(); }
module roof_raw() {
    difference() { union() { slab(); tiles(); } nave_room(); turret_cut(); }
    door_leaf();
}
module accent_raw() {
    gumdrops();
    canes(true);
    peppermints(true);
    round_wedges();
    difference() { intersection() { tower_solid(); helix(plinth_h - 1, R_top(RS, 0) + 1); } room(); }
    intersection() { crook(); crook_stripes(); }
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() {
                union() { corner_beads(); eave_flare(); eave_drips(); rakes(); icing_roof(); canes(); nave_windows(); }
                turret_cut();
            }
            tower_solid();
            crook();
            tw_frames();
            tw_bars();
            door_frame();
            peppermints();
        }
        room();
        nave_openings();
        tw_openings();
        brand_mark();
    }
    difference() { tw_glass(); room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); nave_openings(); nave_frame_holes();
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
else if (part == "preview") {
    color("#C68642") walls_solid();
    color("#5A3825") { slab(); door_leaf(); }
    color("#F7F3EE") { base(); icing_roof(); tower_solid(); crook(); }
    color("#D7263D") { gumdrops(); intersection() { at_tc() rotate_extrude($fn = FNT) polygon([[rt - 0.3, plinth_h - 0.5], [rt + 0.05, plinth_h - 0.5], [rt + 0.05, 150], [rt - 0.3, 150]]); helix(plinth_h - 1, R_top(RS, 0) + 1); } }
}
else if (part == "all") {
    color("#C68642") body_part();
    color("#5A3825") roof_part();
    color("#F7F3EE") trim_part();
    color("#D7263D") accent_part();
}
