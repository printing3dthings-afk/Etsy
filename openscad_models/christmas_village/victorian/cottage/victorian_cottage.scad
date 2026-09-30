// Victorian Cottage -- building #1 of the Dickens Victorian village, redrawn
// round (Scott, 2026-09-30: "Christmas village keeps a rounder shape ... Yes
// redo the cottages round too", and picked this layout from four). The square
// cottage, gated and finished, is in the recycle bin (data/trash,
// 20260930-002) and at commit a8eea51.
//
// A round brick drum under a cone of slate. Across its front the drum is cut
// flat, 16 mm wide, and that flat face rises into a gable with a scalloped
// bargeboard and a finial: the door, its wreath and the garland are on it, and
// a lancet window in the gable. Segmental sash windows with keystones round
// the drum, evergreen boxes under the two at the front, icicles under the
// eave, snow on the crown, a chimney at the back. On a soft blob of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane.
//
// The machinery is the round shop-house's (victorian/shop_house): the same
// roof profile, relief, strip placement round the wall and the fixes recorded
// there, which apply here unchanged.
//
// COLOUR PARTS, ONE PRINT (victorian_cottage.3mf), priority
// roof > accent > trim > body:
//   body    brick: the drum, the gable, the chimney, the wreath's and the
//           garland's red bows, the step
//   roof    slate: the roof and the gable's, the bargeboard and finial, the door
//   trim    white: snow base, the eave's soffit, snow on the roofs, icicles,
//           every pane, the window and door frames, keystones and bars
//   accent  evergreen: the wreath, the garland, the window boxes

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// ---- the plan: a circle, cut flat across the front --------------------------------------
Rw       = 27;              // the brick's face (50.6 clear inside)
wall     = 1.68;
plinth_h = 8;
SH       = 1.2;
fl_ang   = 52;
fw       = 8;               // the flat front's half-width
yf       = sqrt(Rw * Rw - fw * fw);     // its face, 25.79 in front of the centre
L0       = 0;               // the shop-house's stadium, with no straights
EC       = [[0, 0], [0, 0]];

module sweep() rotate_extrude($fn = FN) children();
module stadium(r) circle(r = r, $fn = FN);
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
// the half-space behind the flat front, pulled in by d
module behind(d = 0) translate([-100, -yf + d, -10]) cube([200, 200, 300]);

// ALONG THE OUTLINE (the shop-house's, with L0 = 0): s is the distance round
// the circle of radius R from the front, anticlockwise seen from above.
function sper(R) = 2 * L0 + 2 * PI * R;
function spos(R, s) = let (P = sper(R), t = s - floor(s / P) * P, a = -90 + t / R * 180 / PI) [R * cos(a), R * sin(a), a];
function s_at(a, R) = let (t = (a + 90) / 180 * PI * R) t - floor(t / sper(R)) * sper(R);
module splace(R, s, z) let (p = spos(R, s)) translate([p[0], p[1], z]) rotate([0, 0, p[2] + 90]) rotate([90, 0, 0]) children();
module srelief(R, s, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    splace(R, s + uc, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module sclip(R, d) intersection() { children(); linear_extrude(300) stadium(R + d); }

// ---- relief (the cottage's) --------------------------------------------------------------
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

// ---- the roof: one profile (the shop-house's) --------------------------------------------------
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang);
sb = 1.8;
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
module R_full(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
module R_choc(R, kv0) polygon([[0, -10], [kv0, -10], [kv0, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_below(R) polygon([[0, -5], [R[1] + 20, -5], [R[1] + 20, R_zc(R, R[1] + 20)], [0, R_zc(R, 0)]]);

H   = 44;                   // the cone's eave line, at the wall's inside
tp  = tan(58);              // the square cottage's pitch
tv  = 2.52 / cos(58);
RV  = [H, Rw - wall, tp, tv, Rw - 3, Rw + 3.5, 35, Rw + 3.5];
kv0 = Rw - 0.8;
zfu = R_fl(RV, Rw);         // where the soffit meets the brick
function zs(v) = R_zs(RV, v);

// ---- rooms -------------------------------------------------------------------------------------
module room2d() polygon([[0, -2], [Rw - wall, -2], [Rw - wall, H], [0, R_zc(RV, 0)]]);
module main_room() intersection() { sweep() room2d(); behind(wall); }
module below_ceil() sweep() R_below(RV);

// ---- the brick -----------------------------------------------------------------------------------
bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
z_wt = R_zc(RV, Rw) + 0.6;  // the wall's top at its face, 0.6 up into the roof
nb = ceil((z_wt + 30 - plinth_h - 0.4) / bp);
// the wall's section: each course bulges bd out of the face, under a 58 deg
// chamfer and over a 45 deg one; ztop caps it
function brick_prof(ztop) = concat([[Rw - wall - 0.3, plinth_h - 0.5], [Rw, plinth_h - 0.5]],
    [for (k = [0 : nb - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < ztop - 0.5) [Rw + g, z]],
    [[Rw, ztop], [Rw - wall - 0.3, ztop]]);
// the drum, its top 0.6 up into the roof, stopped at the flat front
module drum() intersection() {
    sweep() polygon(concat([for (p = brick_prof(z_wt)) if (p[1] < z_wt - 0.01) p],
                           [[Rw, z_wt], [Rw - wall - 0.3, R_zc(RV, Rw - wall - 0.3) + 0.6]]));
    behind();
}
// the flat front: the same courses on a plane, run up into the gable
module front_wall() intersection() {
    yz(-fw - 1, fw + 1) translate([Rw - yf, 0]) mirror([1, 0]) polygon(brick_prof(80));
    translate([0, 0, -1]) cylinder(r = Rw + bd, h = 100, $fn = FN);
    union() { translate([0, 0, 0.6]) below_ceil(); dmw() dm_below(0.4); }
}

// ---- windows round the drum --------------------------------------------------------------------
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
function rect_pts(a, hgt) = [[-a, 0], [a, 0], [a, hgt], [-a, hgt]];
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.3;
// [s, z, a, h]: two at the front either side of the flat, two at the back
// either side of the chimney
SW = [[s_at(-55, Rw), 16, 4.6, 12], [s_at(235, Rw), 16, 4.6, 12], [s_at(40, Rw), 16, 4.6, 12], [s_at(140, Rw), 16, 4.6, 12]];
module sw_outline(w) polygon(seg_pts(w[2], w[3]));
module sw_bars(w) { translate([-0.84, -3]) square([1.68, 40]); translate([-20, w[3] * 0.55]) square([40, 2.2]); }
module sw_frames() {
    sclip(Rw, fr_t) for (w = SW) srelief(Rw, w[0], w[1], w[2] + fr_w + 1.2)
        relief_up(-0.4, fr_t) {
            union() {
                offset(r = fr_w) sw_outline(w);
                translate([-w[2] - fr_w - 0.8, -sill]) square([2 * (w[2] + fr_w + 0.8), sill + 1]);
            }
            offset(r = 0.3) sw_outline(w);
        }
    sclip(Rw, fr_t + 0.5) for (w = SW) srelief(Rw, w[0], w[1], 2.4)
        relief_up(-0.4, fr_t + 0.5) translate([0, seg_top(w[2], w[3]) - 1.2]) polygon([[-1.3, 0], [1.3, 0], [1.8, fr_w + 1.8], [-1.8, fr_w + 1.8]]);
    sclip(Rw, bd) for (w = SW) srelief(Rw, w[0], w[1], w[2] + 1.2)
        relief_up(-0.4, bd) intersection() { offset(r = 0.6) sw_outline(w); sw_bars(w); }
}
module sw_openings() for (w = SW) splace(Rw, w[0], w[1]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) sw_outline(w);
module sw_holes() for (w = SW) srelief(Rw, w[0], w[1], w[2] + 0.6) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) sw_outline(w);
module sw_glass() intersection() {
    for (w = SW) splace(Rw, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) sw_outline(w);
    linear_extrude(200) stadium(Rw - 0.2);
}
// evergreen boxes under the two front windows, hung below the sill
module box2d(w) {
    bw = w[2] + fr_w + 0.4;
    translate([-bw, -sill - 4.4]) square([2 * bw, 4.4 + 0.9]);
    for (i = [0 : 5]) let (x = -bw + 1.2 + i * (2 * bw - 2.4) / 5)
        translate([x, -sill + 0.7]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_boxes() sclip(Rw, bd + 1.4) for (w = [SW[0], SW[1]]) srelief(Rw, w[0], w[1], w[2] + fr_w + 1.4) relief_up(-0.4, bd + 1.4) box2d(w);

// ---- icicles under the eave, clear of the gable -----------------------------------------------------
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
g_s = fw + 4;               // the gable's reach round the outline, either side of the front
IC = [for (i = [0 : 39]) let (s = g_s + i * (sper(Rw) - 2 * g_s) / 39) [s, 1.4 + 1.8 * rnd(i, 70), 1.8 + 0.4 * rnd(i, 110)]];
module icicles() for (d = IC) splace(Rw, d[0], zfu + 1) relief_up(-0.4, 1.2) drip2d(d[1], d[2]);

// ---- the roof ------------------------------------------------------------------------------------------
module roof_slate() intersection() { sweep() R_full(RV, kv0); sweep() R_choc(RV, kv0); }
module soffit() sweep() R_curl(RV, kv0);
sh_c = 2.35;
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module slates() {
    ve = RV[5];
    nk = ceil((ve - 0.6) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 0.6))
        if (x0 > x1 + 0.3) sweep() course_band(RV, x0, x1);
    sweep() polygon([[0, zs(0) - 1.0], [1.2, zs(1.2) - 1.0], [1.2, zs(1.2) + 1.0], [0, zs(0) + 1.4]]);
}
// SNOW on the crown, its edge cut straight down in waves
function wave(t) = 2.2 * sin(t * 1.7) + 1.3 * sin(t * 4.1 + 60);
module snow_roof() intersection() {
    sweep() polygon([[0, zs(0) - 1.0], [RV[4], zs(RV[4]) - 1.0], [RV[4], zs(RV[4]) + 2.0], [3, zs(3) + 2.0], [0, zs(0) + 2.4]]);
    translate([0, 0, 40]) linear_extrude(100) polygon([for (i = [0 : 199]) let (a = 360 * i / 200) (11 + wave(i * 3.3)) * [cos(a), sin(a)]]);
}

// ---- the chimney, at the back --------------------------------------------------------------------------
ch0 = [-4, 4, 12, 20];
ch1 = [-2.8, 2.8, 13, 19];
ch_w = 80;
ch_top = 90;
module chimney() difference() {
    union() {
        translate([ch0[0], ch0[2], 40]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], ch_w - 40]);
        hull() {
            translate([ch0[0], ch0[2], ch_w - 0.01]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 0.01]);
            translate([ch1[0], ch1[2], ch_w + 1.2 * tan(60)]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
        }
        translate([ch1[0], ch1[2], ch_w]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], ch_top - ch_w]);
        hull() {
            translate([ch1[0], ch1[2], ch_top - 1.3]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
            translate([ch1[0] - 0.8, ch1[2] - 0.8, ch_top]) cube([ch1[1] - ch1[0] + 1.6, ch1[3] - ch1[2] + 1.6, 1.6]);
        }
        for (x = [ch1[0] + 1.3, ch1[1] - 1.3]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 1.4]) cylinder(d = 2.4, h = 4.0, $fn = 32);
    }
    below_ceil();
    for (x = [ch1[0] + 1.3, ch1[1] - 1.3]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 3.4]) cylinder(d = 0.8, h = 5, $fn = 20);
}
module chimney_col() translate([ch0[0], ch0[2], 40]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 80]);

// ---- the gable (the shop-house's dormer, moved out to the flat front) ----------------------------------------
// Built in its own frame -- x out from the centre toward the front, y across --
// and turned into place by dmw(): x runs to -y. Its face is the flat front.
// The cone's ceiling is the same in any frame, so below_ceil() serves here.
module dmw() rotate([0, 0, -90]) children();
dm_c  = 0;
dm_w  = fw;
dm_in = dm_w - wall;
dm_x  = yf;
dm_x0 = 17;                 // its ridge dives into the cone at 19: well inside
dm_e  = 1;
dm_ze = H;                  // its eave: the cone's
function dz_ceil(y) = dm_ze + (dm_in - abs(y - dm_c)) * tp;
function dz_out(y)  = dz_ceil(y) + tv;
module dmf(z) translate([dm_x, dm_c, z]) rotate([0, 0, 90]) rotate([90, 0, 0]) children();
// 12 either side, past the gable's 9: at the shop-house's 20, this low gable's
// slopes fell below the outline's own floor at 30, it crossed itself, and CGAL
// dropped everything built from it as "not closed"
module dm_below(dz, x1 = dm_x + dm_e + 1) yz(dm_x0 - 1, x1)
    polygon([[dm_c - 12, 30], [dm_c + 12, 30], [dm_c + 12, dz_ceil(dm_c + 12) + dz], [dm_c, dz_ceil(dm_c) + dz], [dm_c - 12, dz_ceil(dm_c - 12) + dz]]);
// its inside, narrower and steeper than its roof (the shop-house's dormer,
// 51.7 deg groins): at 70 deg the groins with the cone's 58 deg ceiling rise
// 54 deg; 3.2 wide it clears the lancet (2.4), and the slab over its ridge
// keeps 1.5 mm
dmr_in = 3.2;
dmr_ze = 47.2;
function dzr(y) = dmr_ze + (dmr_in - abs(y - dm_c)) * tan(70);
module dm_room() intersection() {
    translate([dm_x0 - 1, dm_c - dmr_in, 30]) cube([dm_x - wall - dm_x0 + 1, 2 * dmr_in, 60]);
    yz(dm_x0 - 1, dm_x + dm_e + 1) polygon([[dm_c - dmr_in, 30], [dm_c + dmr_in, 30], [dm_c + dmr_in, dmr_ze], [dm_c, dzr(dm_c)], [dm_c - dmr_in, dmr_ze]]);
}
// everything of the cone in the gable's way: from inside the gable out past
// the eave's tip, below the gable's own roof
// out past the eave's tip (Rw + 3.5): stopped at the gable's face, it left the
// cone's eave running across the gable's foot and hid the lancet
module gable_cut() dmw() intersection() {
    translate([dm_x0 - 1, dm_c - dm_w, 30]) cube([Rw + 6 - dm_x0 + 1, 2 * dm_w, 60]);
    dm_below(tv, Rw + 7);
}
module dm_walls() difference() {
    intersection() { translate([dm_x0, dm_c - dm_w, 30]) cube([dm_x - dm_x0, 2 * dm_w, 60]); dm_below(0.4); }
    below_ceil();
}
dm_E = dm_w + dm_e;
module dm_front_cut(up = 60, x0 = dm_x) intersection() {
    children();
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [SH, 0, 1, -SH * x0], [0, 0, 0, 1]])
        minkowski() { children(); cylinder(r = 0.01, h = up, $fn = 4); }
}
dm_yf = dm_E - 0.08;
dm_tip = dz_ceil(dm_c + dm_yf) + (dm_E - dm_yf) * tan(fl_ang);
module dm_slab() difference() {
    dm_front_cut() yz(dm_x0, dm_x + dm_e) polygon([[dm_c - dm_E, dm_tip], [dm_c - dm_yf, dz_ceil(dm_c - dm_yf)], [dm_c, dz_ceil(dm_c)],
        [dm_c + dm_yf, dz_ceil(dm_c + dm_yf)], [dm_c + dm_E, dm_tip], [dm_c + dm_E, dz_out(dm_c + dm_E)], [dm_c, dz_out(dm_c)], [dm_c - dm_E, dz_out(dm_c - dm_E)]]);
    below_ceil();
}
dm_up = 0.3 + SH * (dm_e + 0.2) + 0.2;
module dm_flare() difference() {
    dm_front_cut() for (m = [0, 1]) translate([0, dm_c, 0]) mirror([0, m, 0]) yz(dm_x0, dm_x + dm_e)
        polygon([[dm_w - 0.3, dz_ceil(dm_c + dm_yf) - (dm_yf - dm_w + 0.3) * tan(fl_ang)], [dm_yf, dz_ceil(dm_c + dm_yf)],
                 [dm_yf, dz_ceil(dm_c + dm_yf) + dm_up], [dm_w - 0.3, dz_ceil(dm_c + dm_w - 0.3) + dm_up]]);
    below_ceil();
}
function sh_d(k, X) = min(k * sh_c, X - 0.6);
module dm_slates() difference() {
    nk = ceil((dm_E - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (y0 = s * (dm_E - sh_d(k, dm_E)), y1 = s * (dm_E - min(sh_d(k + 1, dm_E) + 0.5, dm_E - 0.6)))
        yz(dm_x0, dm_x + dm_e) translate([dm_c, 0])
            polygon([[y0, dz_out(dm_c + y0) - 1.0], [y0, dz_out(dm_c + y0) + 1.0], [y1, dz_out(dm_c + y1) + 0.05], [y1, dz_out(dm_c + y1) - 1.0]]);
    below_ceil();
}
// THE BARGEBOARD, drawn as one lower edge, the lowest of its scallops at each
// point (the shop-house's: as circles each hung over the next one down)
bs_r = 1.1;
bs_y = [for (i = [-6 : 6]) dm_c + i * 1.26];
function bs_cz(y) = dz_ceil(y) - 2.2 + bs_r;
function bs_low(y) = min(concat([bs_cz(y)],
    [for (c = bs_y) if (abs(y - c) < bs_r) bs_cz(c) - sqrt(bs_r * bs_r - (y - c) * (y - c))]));
module board2d() let (n = 320, Y = [for (i = [0 : n]) dm_c - dm_w + 2 * dm_w * i / n])
    polygon(concat([for (y = Y) [y, bs_low(y)]],
        [[dm_c + dm_w, dz_ceil(dm_c + dm_w) + dm_up], [dm_c, dz_ceil(dm_c) + dm_up], [dm_c - dm_w, dz_ceil(dm_c - dm_w) + dm_up]]));
module dm_board() difference() {
    dm_front_cut(x0 = dm_x - 0.15) yz(dm_x - 0.3, dm_x + dm_e + 0.2) board2d();
    dm_room();
}
module dm_finial() translate([dm_x + dm_e - 1.3, dm_c, dz_out(dm_c) - 2.6]) {
    translate([-1.1, -1.1, 0]) cube([2.2, 2.2, 6.4]);
    translate([0, 0, 6.4]) rotate([0, 0, 45]) cylinder(r1 = 1.1 * sqrt(2), r2 = 0, h = 1.1 * tan(60) * 1.2, $fn = 4);
}
module dm_snow() difference() {
    intersection() {
        yz(dm_x0, dm_x + dm_e) polygon([[dm_c - 5.5, dz_out(dm_c - 5.5) - 1.0], [dm_c, dz_out(dm_c) - 1.0], [dm_c + 5.5, dz_out(dm_c + 5.5) - 1.0],
            [dm_c + 5.5, dz_out(dm_c + 5.5) + 1.8], [dm_c + 1.5, dz_out(dm_c + 1.5) + 2.8], [dm_c - 1.5, dz_out(dm_c + 1.5) + 2.8], [dm_c - 5.5, dz_out(dm_c - 5.5) + 1.8]]);
        translate([0, 0, 30]) linear_extrude(60) polygon(concat(
            [for (i = [0 : 30]) let (x = dm_x0 + (dm_x + dm_e - 1.8 - dm_x0) * i / 30) [x, dm_c + 3.6 + 0.8 * sin(x * 47)]],
            [for (i = [30 : -1 : 0]) let (x = dm_x0 + (dm_x + dm_e - 1.8 - dm_x0) * i / 30) [x, dm_c - 3.6 - 0.8 * sin(x * 53 + 40)]]));
    }
    below_ceil();
}

// ---- on the flat front: the lancet, the door, the wreath and the garland --------------------------------------
// the chapel's lancet, for the gable
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
LW  = [2.4, 6];             // the lancet: half-width, straight height
lw_z = 36.5;                // its sill
lf_w = 1.8;
module lw_outline() polygon(lancet_pts(LW[0], LW[1]));
module lw_bars() {
    translate([-mull/2, -3]) square([mull, LW[1] + mull + 3]);
    for (s = [-1, 1]) translate([0, LW[1]]) rotate(s < 0 ? 180 - 62 : 62) translate([0, -mull/2]) square([3 * LW[0], mull]);
}
module lancet() dmf(lw_z) {
    relief_up(-0.4, fr_t) {
        union() { offset(r = lf_w) lw_outline(); translate([-LW[0] - lf_w - 0.6, -2.6]) square([2 * (LW[0] + lf_w + 0.6), 3.4]); }
        offset(r = 0.3) lw_outline();
    }
    relief_up(-0.4, bd) intersection() { offset(r = 0.6) lw_outline(); lw_bars(); }
}
module lw_opening() dmf(lw_z) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) lw_outline();
module lw_hole() dmf(lw_z) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) lw_outline();
module lw_glass() dmf(lw_z) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) lw_outline();

// THE DOOR: round-arched, black (the slate filament), two panels with pointed
// heads so no recess has a flat ceiling
door_a = 4.2;
door_h = 13;
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() dmf(plinth_h) translate([0, 0, -wall + 0.15]) difference() {
    linear_extrude(wall + 0.05) translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
    translate([0, 0, wall - 0.35]) linear_extrude(1) { panel2d(-3.1, -0.7, 1.6, 5.6); panel2d(0.7, 3.1, 1.6, 5.6); }
}
module door_frame() dmf(plinth_h) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.8) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
module door_opening() dmf(plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(arch_pts(door_a, door_h));
module door_hole() dmf(plinth_h) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
// the wreath on the leaf above the panels, and its red bow (the brick) at its
// foot, raised from the leaf rather than the wreath's face
wr_z = plinth_h + door_h - 1;
module wreath() dmf(wr_z) relief_up(-0.4, bd + 0.6) { circle(r = 3.2); circle(r = 1.7); }
module bow2d() {
    polygon([[0, 0], [-2.6, 1.3], [-2.6, -1.3]]);  polygon([[0, 0], [2.6, 1.3], [2.6, -1.3]]);
    circle(r = 0.9);
    polygon([[-0.4, 0], [-1.4, -2.2], [-0.5, -2.2], [0.1, -0.6]]);
    polygon([[0.4, 0], [1.4, -2.2], [0.5, -2.2], [-0.1, -0.6]]);
}
module wreath_bow() dmf(wr_z - 3.2) relief_up(-0.4, bd + 1.0) scale(0.8) bow2d();
// the garland: a swag between two bows, over the door's arch
gz = plinth_h + door_h + door_a + 5.2;
g_half = 5.4;
function g_y(x) = -2.2 * (1 - pow(x / g_half, 2));
module garland2d() {
    polygon(concat([for (i = [0 : 24]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) + 1.4]],
                   [for (i = [24 : -1 : 0]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) - 1.4]]));
    for (s = [-1, 1]) translate([s * g_half, 0]) circle(r = 2.0);
}
module garland() dmf(gz) relief_up(-0.4, bd + 1.0) garland2d();
module garland_bows() for (s = [-1, 1]) dmf(gz + 0.4) translate([s * g_half, 0]) relief_up(-0.4, bd + 1.6) scale(0.65) bow2d();
// a step in front of the door
module step() translate([0, -yf - 1.4, plinth_h - 0.5]) hull() for (s = [-1, 1]) translate([s * 4.6, 0, 0]) cylinder(r = 1.8, h = 1.9, $fn = 40);

// ---- rooms, all together ---------------------------------------------------------------------------------
module room() { main_room(); dmw() dm_room(); }

// ---- the snow base: a soft blob with a rounded edge --------------------------------------------------------
module base2d() offset(r = 6.5, $fn = 48) circle(r = Rw, $fn = FN);
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[(Rw + 1) * cos(-20), (Rw + 1) * sin(-20), 7, 4, 3.2], [(Rw + 1) * cos(100), (Rw + 1) * sin(100), 7, 3.5, 2.8],
          [(Rw + 1) * cos(190), (Rw + 1) * sin(190), 5, 3.5, 2.4]];
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
// centred in the band between the room's opening (-24.1) and the base's edge (-33.5)
module brand_mark() translate([0, -28.8, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- brick joints ------------------------------------------------------------------------------------------
// vertical mortar joints, staggered by course, round the drum; none near an
// opening or on the flat front
function box_s(s0, s1, z0, z1) = [s0, s1, z0, z1];
OPEN = concat(
    [box_s(-100, g_s, 0, 200), box_s(sper(Rw) - g_s, sper(Rw) + 100, 0, 200)],
    [for (w = SW) box_s(w[0] - w[2] - fr_w - 3, w[0] + w[2] + fr_w + 3, w[1] - sill - 6, w[1] + seg_top(w[2], w[3]) + fr_w + 4)]);
function clear_at(s, z0, z1) = len([for (b = OPEN) if (s + bj > b[0] && s - bj < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
nj = floor(sper(Rw) / bl);
module joints() for (k = [1 : nb - 1]) let (z0 = zc(k), z1 = zc(k + 1)) if (z1 < zfu - 0.5)
    for (j = [0 : nj - 1]) let (s = (j + (k % 2) / 2) * sper(Rw) / nj) if (clear_at(s, z0, z1))
        splace(Rw, s, z0) translate([-bj / 2, 0, -0.05]) cube([bj, z1 - z0, 2.1]);

// ---- parts ------------------------------------------------------------------------------------------------
module body_raw() {
    drum();
    front_wall();
    dmw() dm_walls();
    chimney();
    step();
    wreath_bow();
    garland_bows();
}
module roof_raw() {
    difference() { roof_slate(); room(); chimney_col(); gable_cut(); }
    difference() { slates(); room(); chimney_col(); gable_cut(); }
    door_leaf();
    dmw() {
        difference() { union() { dm_slab(); dm_slates(); } dm_room(); }
        dm_board();
        dm_finial();
    }
}
module accent_raw() {
    wreath();
    garland();
    window_boxes();
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() { union() { soffit(); snow_roof(); } chimney_col(); gable_cut(); }
            icicles();
            dmw() { dm_flare(); dm_snow(); lancet(); door_frame(); }
            sw_frames();
        }
        room();
        dmw() lw_opening();
        brand_mark();
    }
    // the glass goes back in after the rooms and openings are cut
    difference() { union() { sw_glass(); dmw() lw_glass(); } main_room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); sw_openings(); sw_holes(); joints();
        dmw() { door_opening(); door_hole(); lw_opening(); lw_hole(); }
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
else {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
