// Victorian Church -- building #3 of the Dickens Victorian village (Scott,
// 2026-10-01, picked from four: "Nave + square spire tower").
//
// A long brick nave under a steep slate gable that runs front to back, white
// quoins at its corners and a white sill course round it, three tall lancet
// windows down each side. On its front gable a round rose window over a
// pointed slate door, with a wreath on the door and a garland over it, and a
// lancet either side. On its front-left corner a square brick bell tower rises
// past the ridge to a louvred belfry and a white cornice, then a tall octagonal
// broach spire of slate with a white ball and cross. At the back a half-round
// apse under a half cone of slate. On a soft blob of snow. The tallest
// building in the village.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The tower opens into the nave through
// a pointed doorway and the apse through a pointed chancel arch, so the one
// light fills all three.
//
// THE NAVE is the toy shop's block (../toy_shop), its brick skin, quoins,
// gables, kneelers, eave flare, bargeboards, slates and snow, with all their
// WHY comments there, here in its own frame: gables on +-y, the front at -y.
// THE APSE is the toy shop's tower, halved: the round wall, the swept cone, the
// windows laid round it in strips. THE TOWER and its spire are new.
//
// COLOUR PARTS, ONE PRINT (victorian_church.3mf), priority
// roof > accent > trim > body:
//   body    brick: the nave, the tower, the apse, the kneelers, the
//           garland's bows, the step
//   roof    slate: the nave's roof, the spire, the apse's cone, the door
//   trim    white: snow base and drifts, quoins, sill course, the tower's bands
//           and cornice, eave soffits, icicles, bargeboards and finials, snow on
//           the roofs, every window's frame, tracery, bars and pane, the
//           belfry's louvres, the door frame, the wreath's bow, the ball and
//           cross
//   accent  evergreen: the wreath, the garland

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";

// =====================================================================================
// THE NAVE
// =====================================================================================
W        = 52;              // across, x
D        = 64;              // front to back, y
wall     = 1.68;
corner_r = 1.5;
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;

bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

H1    = 12;                 // the sill course
// the eave line at 50: a 46 mm tealight's circle reaches 1 mm from the wall,
// where the ceiling has only begun to rise, and needs 50 mm there
H     = 50;
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

// faces: 0 = back (+y), 1 = FRONT (-y), 2 = right (+x), 3 = left (-x); u runs
// along the face in world x (front, back) or world y (sides)
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
module brick_skin(w, d, ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(w, d, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(w, d, g, z)],
        [rpts(w, d, 0, ztop + 2)]), slices = 0);
}
// QUOINS on the three corners the tower leaves free
q_long = 6.2;  q_short = 3.6;  q_off = 0.5;
nq     = 6;                 // pairs of courses: up to zc(12) = 39.6, under the eave
function q_len(j, gable) = (j % 2 == 0) == gable ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) if (!(sx < 0 && sy < 0)) let (z0 = zc(2 * j), z1 = zc(2 * j + 2)) {
        translate([sx > 0 ? Wh - q_len(j, true) : -Wh - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0]);
        translate([sx > 0 ? Wh - 0.5 : -Wh - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0]);
    }
}
module quoins() intersection() { brick_skin(W, D, zc(2 * nq) + 2); quoin_boxes(); }

// THE SILL COURSE: the toy shop's string course, at the windows' sills
sc_o = 0.9;
module band(w, d, z) skin([rpts(w, d, -0.3, z - 2.4), rpts(w, d, bd + sc_o, z - 2.4 + (bd + sc_o + 0.3) * tan(55)),
                           rpts(w, d, bd + sc_o, z + 1.6)], slices = 0);

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
        brick_skin(W, D, z_out(0) + cp_hi + 1);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}
module nave_room() intersection() {
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
function circ_pts(a, n = 64) = [for (i = [0 : n - 1]) let (q = 360 * i / n) [a * sin(q), a - a * cos(q)]];

mull = 1.68;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.4;
// [face, u, z, a, straight height, kind]. A rose's z is its foot, a its radius.
WINDOWS = [
    [2, -6, 16, 3.4, 11, "lancet"], [2, 6.5, 16, 3.4, 11, "lancet"], [2, 19, 16, 3.4, 11, "lancet"],
    [3, -6, 16, 3.4, 11, "lancet"], [3, 6.5, 16, 3.4, 11, "lancet"], [3, 19, 16, 3.4, 11, "lancet"],
    [1, -15, 16, 3.4, 11, "lancet"], [1, 15, 16, 3.4, 11, "lancet"],
    [1, 0, 51.5, 8.5, 0, "rose"],
];
function w_top(w) = w[5] == "seg" ? seg_top(w[3], w[4]) : w[5] == "rose" ? 2 * w[3] : lancet_top(w[3], w[4]);
module win_outline(w) {
    if (w[5] == "seg") polygon(seg_pts(w[3], w[4]));
    else if (w[5] == "rose") polygon(circ_pts(w[3]));
    else polygon(lancet_pts(w[3], w[4]));
}
module win_bars(w) {
    if (w[5] == "seg") {
        translate([-mull/2, -3]) square([mull, 40]);
        translate([-20, w[4] * 0.55]) square([40, 2.2]);
    } else if (w[5] == "rose") translate([0, w[3]]) {
        // tracery: four bars through the hub, a ring, the hub. Every raised bar's
        // underside slopes up 1.2 per mm out, so a level bar's front is its
        // height less 1.2: no bar is level (turned 22.5), each 2.0 wide
        for (q = [22.5 : 45 : 157.5]) rotate(q) translate([-2 * w[3], -1.0]) square([4 * w[3], 2.0]);
        difference() { circle(r = 0.58 * w[3] + 1.0); circle(r = 0.58 * w[3] - 1.0); }
        circle(r = 1.7);
    } else if (w[5] == "louvre") {
        // three slats 2.2 tall: five 1.2 tall came to a knife edge at the front
        for (i = [0 : 2]) translate([-20, 0.8 + i * 3.4]) square([40, 2.2]);
    } else {
        translate([-mull/2, -3]) square([mull, w[4] + mull + 3]);
        for (s = [-1, 1]) translate([0, w[4]]) rotate(s < 0 ? 180 - 62 : 62)
            translate([0, -mull/2]) square([3 * w[3], mull]);
    }
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_outer(w) {
    offset(r = fr_w) win_outline(w);
    if (w[5] == "seg") translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]);
}
module win_relief(w) {
    relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
    relief_up(-0.4, bd) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
module nave_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module nave_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module nave_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) win_relief(w);

// ---- the door, its wreath, the garland over it --------------------------------------------------
dr_a = 4.5;  dr_h = 11;
dr_top = lancet_top(dr_a, dr_h);
module door_outline() polygon(lancet_pts(dr_a, dr_h));
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() nf(1, 0, plinth_h) difference() {
    // the wall's thickness only: 1 mm deeper, its foot hung over the open base
    // 0.05 under the frame's inner edge, so the two meet with no slot between
    translate([0, 0, -wall]) linear_extrude(wall + 0.2) translate([0, -0.3]) offset(delta = 0.25) polygon(lancet_pts(dr_a, dr_h + 0.3));
    // two leaves: a groove between them and two panels each, sunk 0.3
    translate([0, 0, -0.1]) linear_extrude(2) {
        translate([-0.3, -1]) square([0.6, 40]);
        // panels only below the wreath: sunk under it, the panels' corners and the
        // wreath left slivers that printed as four loose bodies
        // x0 < x1 on both sides: given as (-0.9, -3.4) the left panel's point turned down
        for (s = [-1, 1]) panel2d(min(s * 0.9, s * 3.4), max(s * 0.9, s * 3.4), 1.6, 6.4);
    }
}
// out through the bricks' bumps: cut only through the wall, the brick courses'
// 0.6 ridges ran on across the door and the slicer propped them
module door_opening() nf(1, 0, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
module door_frame() nf(1, 0, plinth_h) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.8) door_outline(); translate([-30, -0.5]) square([60, 100]); }
    // its inner edge on the leaf's: 0.3 over it the rim was propped up the whole
    // door, 0.3 outside it a 0.1 slot under the rim was propped instead
    translate([0, -1]) offset(delta = 0.2) polygon(lancet_pts(dr_a, dr_h + 1));
}
// the band is cut where the door's frame crosses it
module door_band_cut() nf(1, 0, plinth_h) translate([0, 0, -wall - 1]) linear_extrude(wall + 6) offset(r = 2.0) door_outline();
wr_z = plinth_h + dr_h + 0.5;
module wreath() nf(1, 0, wr_z) relief_up(-0.2, 0.2 + bd + 0.8) difference() { circle(r = 3.0, $fn = 40); circle(r = 1.6, $fn = 32); }
module bow2d() {
    polygon([[0, 0], [-2.2, 1.1], [-2.2, -1.1]]);  polygon([[0, 0], [2.2, 1.1], [2.2, -1.1]]);
    circle(r = 0.8);
    polygon([[-0.4, 0], [-1.2, -1.9], [-0.4, -1.9], [0.1, -0.5]]);
    polygon([[0.4, 0], [1.2, -1.9], [0.4, -1.9], [-0.1, -0.5]]);
}
// the bow at the wreath's top, clear of the panels
module wreath_bow() nf(1, 0, wr_z + 3.0) relief_up(-0.2, 0.2 + bd + 1.2) bow2d();
gz = plinth_h + dr_top + 6.2;
g_half = 6.6;
function g_y(x) = -2.2 * (1 - pow(x / g_half, 2));
module garland2d() {
    polygon(concat([for (i = [0 : 24]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) + 1.4]],
                   [for (i = [24 : -1 : 0]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) - 1.4]]));
    for (s = [-1, 1]) translate([s * g_half, 0]) circle(r = 2.0);
}
module garland() nf(1, 0, gz) relief_up(-0.4, bd + 1.0) garland2d();
module garland_bows() for (s = [-1, 1]) nf(1, 0, gz + 0.4) translate([s * g_half, 0]) relief_up(-0.4, bd + 1.6) scale(0.65) bow2d();
module step() nf(1, 0, plinth_h - 0.5) translate([-dr_a - 2.8, 0, -0.2]) cube([2 * dr_a + 5.6, 1.9, 3.2]);

// ---- icicles under the side eaves, clear of the windows' heads and the tower ----
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 20]) [-Dh + 2.4 + i * (D - 4.8) / 20, 2.4 + 2.4 * rnd(i, 40), 1.8 + 0.6 * rnd(i, 80)]];
function ic_clear(f, u) = len([for (w = WINDOWS) if (w[0] == f && abs(u - w[1]) < w[3] + fr_w + 2.2) 1]) == 0
                          && !(f == 3 && u < TB[3] + 2.5);
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [2, 3], c = IC) if (ic_clear(f, c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

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
    translate([0, 0, 7.8]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0.35, h = 1.3 * tan(60) * 1.2, $fn = 4);
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
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0)], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
sn_x = 13;
function sn_edge(y) = sn_x + 2.2 * sin(y * 17) + 1.3 * sin(y * 41 + 60);
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
    [lu - h, lu + h, w[2] - fr_w - 2.5, w[2] + w_top(w) + fr_w + 4];
// in each face's joint coordinate (loc): the tower, the apse, the door and its
// garland keep joints away
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    [[-100, 100, H1 - 3.0, H1 + 2.2]],
    f >= 2 ? [[-100, 100, zf0 - 6, 300]] : [],
    f == 1 ? [[-100, TB[1] + 2.5, 0, 300], [-g_half - 4, g_half + 4, 0, gz + 5]] : [],
    f == 0 ? [[-ra - 2, ra + 2, 0, 300]] : [],
    f == 3 ? [[-TB[3] - 2.5, 100, 0, 300]] : []);
module joints() for (f = [0 : 3]) wall_joints(f, f < 2 ? z_out(0) + cp_hi : H + 2, face_boxes(f));

// =====================================================================================
// THE TOWER, square, on the nave's front-left corner: its right wall is the
// nave's left wall, it stands 3 proud of the front
// =====================================================================================
tw_s  = 16;                                         // outside, square
TB    = [-Wh + wall - tw_s, -Wh + wall, -Dh - 3, -Dh - 3 + tw_s];   // x0, x1, y0, y1
TCc   = [(TB[0] + TB[1]) / 2, (TB[2] + TB[3]) / 2];
twh   = tw_s / 2;
twi   = twh - wall;                                 // its room's half-width
z_tw  = 112;                                        // the walls' top, the spire's foot
module at_tw() translate([TCc[0], TCc[1], 0]) children();
// 0.3 inside the tower's face, so the nave's walls run into it: cut at the face
// itself, the two met in zero-width slivers along the tower's front-right edge
module tower_cut() at_tw() translate([0, 0, -1]) linear_extrude(300) offset(delta = -0.3) polygon(rrect_pts(tw_s, tw_s, corner_r, 5));
// the ring of brick, up 0.6 into the spire
module tower_walls() at_tw() intersection() {
    brick_skin(tw_s, tw_s, z_tw + 1);
    translate([-30, -30, -1]) cube([60, 60, z_tw + 1.6]);
}
// faces: 0 = back, 1 = FRONT, 2 = right, 3 = left; u along the face as nf()
module tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [TCc[0] + u, TB[3], z] : face == 1 ? [TCc[0] + u, TB[2], z]
      : face == 2 ? [TB[1], TCc[1] + u, z] : [TB[0], TCc[1] + u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
TB_BANDS = [H1, H - 2, z_tw - 1.6];
module tower_bands() at_tw() for (z = TB_BANDS) band(tw_s, tw_s, z);
// its windows: a lancet low and high on the front, high on the left; a
// louvred belfry light in every face, over the nave's ridge
z_bel = 94;
TWIN = concat([[1, 0, 18, 3.0, 9, "lancet"], [1, 0, 58, 3.0, 9, "lancet"], [3, 0, 58, 3.0, 9, "lancet"]],
              [for (f = [0 : 3]) [f, 0, z_bel, 2.8, 6, "louvre"]]);
module tower_windows() for (w = TWIN) tf(w[0], w[1], w[2]) win_relief(w);
module tower_openings() for (w = TWIN) tf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module tower_frame_holes() for (w = TWIN) tf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
// its room: square, up into the spire, whose ceiling is the spire's inside
module tower_room() at_tw() intersection() {
    translate([-twi, -twi, -2]) cube([2 * twi, 2 * twi, 300]);
    union() {
        translate([-30, -30, -2]) cube([60, 60, z_tw + 2]);
        spire_inner();
    }
}
// THE DOORWAY into the nave, through the shared wall: pointed, its sides
// rising at 58 deg, so its head is no bridge
module tower_doorway() translate([TB[1] + 0.8, TCc[1], plinth_h - 0.5]) rotate([0, 0, 90]) rotate([90, 0, 0])
    translate([0, 0, -wall - 1.2]) linear_extrude(wall + 2.4) polygon(lancet_pts(4.8, 22));

// THE SPIRE: an octagon tapering at 81 deg, broached into the square tower by
// a pyramid at 60 deg on each corner; slate courses with 55 deg undersides
sp_R  = twh;                // the octagon's corner radius at its foot
sp_H  = 48;                 // to its virtual point
sp_tip = 0.9;               // blunted
sp_top = z_tw + sp_H * (1 - sp_tip / sp_R);
function sp_r(z) = sp_R * (1 - (z - z_tw) / sp_H);
module oct(r, h) rotate([0, 0, 22.5]) cylinder(r = r, h = h, $fn = 8);
module oct_frustum(r1, r2, h) rotate([0, 0, 22.5]) cylinder(r1 = r1, r2 = r2, h = h, $fn = 8);
sp_in = wall / sin(atan(sp_H / (sp_R * cos(22.5)))) / cos(22.5);   // inward on the corner radius
module spire_outer() {
    translate([0, 0, z_tw]) oct_frustum(sp_R, sp_tip, sp_top - z_tw);
    hull() {
        translate([-twh, -twh, z_tw]) cube([2 * twh, 2 * twh, 0.01]);
        translate([0, 0, z_tw + twh * tan(60)]) cube(0.01, center = true);
    }
}
module spire_inner() {
    translate([0, 0, z_tw - 0.01]) oct_frustum(sp_R - sp_in, 0, (sp_R - sp_in) / sp_R * sp_H);
    hull() {
        translate([-twi, -twi, z_tw - 0.01]) cube([2 * twi, 2 * twi, 0.01]);
        translate([0, 0, z_tw + twi * tan(60)]) cube(0.01, center = true);
    }
}
sp_c = 3.2;                 // a course
module spire_courses() for (zb = [z_tw + 3 : sp_c : sp_top - 8]) hull() {
    translate([0, 0, zb - 0.8]) oct(sp_r(zb - 0.8), 0.01);
    translate([0, 0, zb]) oct(sp_r(zb) + 0.6 / cos(22.5), 0.01);
    translate([0, 0, zb + sp_c]) oct(sp_r(zb + sp_c) + 0.05, 0.01);
}
module spire() at_tw() union() { spire_outer(); spire_courses(); }
// the ball and cross, white, its arms' undersides at 45 deg
module cross_ball() at_tw() translate([0, 0, sp_top]) {
    // the ball's underside a 57 deg cone from 0.5 down in the blunted tip: a
    // sphere's lower half hung out over it, and at 45 deg the slicer propped it.
    // Each piece starts inside the last, or they print as loose bodies
    translate([0, 0, -0.5]) cylinder(r1 = sp_tip * cos(22.5) - 0.05, r2 = 1.8, h = 1.9, $fn = 32);
    translate([0, 0, 1.3]) intersection() { sphere(r = 1.8, $fn = 32); translate([-2, -2, 0]) cube(4); }
    translate([-1, -1, 2.2]) cube([2, 2, 7.6]);
    hull() {
        translate([-2.9, -1, 6.4]) cube([5.8, 2, 1.8]);
        translate([-1, -1, 3.8]) cube([2, 2, 0.01]);
    }
}

// =====================================================================================
// THE APSE, half round at the back, under a half cone
// =====================================================================================
ra   = 13;
rai  = ra - wall;
AC   = [0, Dh - 1.0];       // its centre, 1 inside the back wall's face
FNA  = 160;
fl_ang_t = 52;
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
module R_slate(R, kv0) polygon([[0, -10], [kv0 - 0.01, -10], [kv0 - 0.01, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_room(R) polygon([[0, -2], [R[1], -2], [R[1], R[0]], [0, R_zc(R, 0)]]);
Ha   = 38;
RA   = [Ha, rai, tan(60), tr / cos(60), ra - 2.5, ra + 3, 35, ra + 3];
kv0a = ra - 0.8;
function zsa(v) = R_zs(RA, v);
module at_ac() translate([AC[0], AC[1], 0]) children();
module half() rotate_extrude(angle = 180, $fn = FNA) children();
function abrick_prof(zt) = concat([[rai - 0.3, plinth_h - 0.5], [ra, plinth_h - 0.5]],
    [for (k = [0 : nc(zt) - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < zt + 1) [ra + g, z]],
    [[ra, zt + 2], [rai - 0.3, zt + 2]]);
module apse_walls() at_ac() intersection() {
    half() polygon(abrick_prof(R_zc(RA, rai - 0.3) + 1));
    half() polygon([[0, -5], [ra + 5, -5], [ra + 5, R_zc(RA, ra + 5) + 0.6], [0, R_zc(RA, 0) + 0.6]]);
}
module apse_cut() at_ac() translate([0, 0, -1]) intersection() {
    cylinder(r = ra - 0.3, h = Ha, $fn = FNA);
    translate([-50, 0, 0]) cube([100, 50, Ha]);
}
// its room, and the chancel arch through the back wall: the room's own
// section, straight to the eave and pointed at 60 deg above it
module apse_room() {
    at_ac() half() R_room(RA);
    translate([0, Dh - wall - 1.5, 0]) rotate([90, 0, 0]) translate([0, 0, -3.0]) linear_extrude(3.2)
        polygon([[-rai, -2], [rai, -2], [rai, Ha], [0, R_zc(RA, 0)], [-rai, Ha]]);
}
module apse_cone() at_ac() intersection() {
    half() R_full(RA, kv0a);
    half() R_slate(RA, kv0a);
}
module apse_curl() at_ac() half() R_curl(RA, kv0a);
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module apse_slates() at_ac() {
    ve = RA[5];
    nk = ceil((ve - 6.8) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 6.8))
        if (x0 > x1 + 0.3) half() course_band(RA, x0, x1);
}
function wave(t) = 1.2 * sin(t * 3.0) + 0.8 * sin(t * 7.0 + 60);
module apse_snow() at_ac() intersection() {
    half() polygon([[0, zsa(0) - 1.0], [6, zsa(6) - 1.0], [6, zsa(6) + 1.8], [2, zsa(2) + 2.2], [0, zsa(0) + 2.4]]);
    translate([0, 0, 30]) linear_extrude(60) polygon([for (i = [0 : 90]) let (a = 2 * i) (4.2 + wave(a)) * [cos(a), sin(a)]]);
}
module apse_collar() at_ac() half()
    polygon([[ra - 0.5, H1 - 2.7], [ra + bd + sc_o, H1 - 2.7 + (bd + sc_o + 0.5) * tan(55)], [ra + bd + sc_o, H1 + 1.6], [ra - 0.5, H1 + 1.6]]);
// its windows, laid round it in strips like the toy shop's tower
module aplace(r, th, z) translate([AC[0] + r * cos(th), AC[1] + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module acyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    aplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module aclip(d) intersection() { children(); at_ac() cylinder(r = ra + d, h = 200, $fn = FNA); }
AW = [[40, 15, 2.8, 7, "lancet"], [90, 15, 2.8, 7, "lancet"], [140, 15, 2.8, 7, "lancet"]];
function aw(w) = [0, 0, 0, w[2], w[3], w[4]];
function aframe_U(w) = w[2] + fr_w + 1.4;
module aw_frames() aclip(fr_t + 0.5) for (w = AW) acyl_relief(ra, w[0], w[1], aframe_U(w))
    relief_up(-0.4, fr_t) { frame_outer(aw(w)); offset(r = 0.3) win_outline(aw(w)); }
module aw_bars() aclip(bd) for (w = AW) acyl_relief(ra, w[0], w[1], w[2] + 1) relief_up(-0.4, bd) win_muntins(aw(w), 0.6);
module aw_glass() intersection() {
    for (w = AW) aplace(ra, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(aw(w));
    at_ac() cylinder(r = ra - 0.2, h = 200, $fn = FNA);
}
module aw_openings() for (w = AW) acyl_relief(ra, w[0], w[1], w[2] + 1) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(aw(w));
module aw_holes() for (w = AW) acyl_relief(ra, w[0], w[1], aframe_U(w)) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(aw(w));

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() {
    translate([-Wh, -Dh]) square([W, D]);
    translate([TB[0], TB[2]]) square([tw_s, tw_s]);
    translate(AC) intersection() { circle(r = ra + bd, $fn = FNA); translate([-30, 0]) square([60, 30]); }
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[Wh + 1, -14, 4, 7, 3.0], [Wh + 1, 16, 4, 6, 2.6], [-Wh - 1, 8, 4, 7, 2.8], [TB[0] - 1, TCc[1] + 2, 4, 5, 2.4],
          [-18, -Dh - 1, 5, 3.5, 2.4], [18, -Dh - 1, 5, 3.5, 2.6], [ra * cos(60), AC[1] + ra * sin(60) + 1, 4, 4, 2.4]];
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
// under the front, between the door's step and the base's edge
module brand_mark() translate([0, -Dh - 3.0, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() {
    nave_room();
    tower_room();
    tower_doorway();
    apse_room();
}
module body_raw() {
    difference() { walls_solid(); tower_cut(); }
    tower_walls();
    apse_walls();
    garland_bows();
    step();
}
module roof_raw() {
    difference() { union() { slab(); slates(); } nave_room(); tower_cut(); }
    difference() { spire(); tower_room(); }
    difference() { union() { apse_cone(); apse_slates(); } apse_room(); }
    door_leaf();
}
module accent_raw() {
    wreath();
    garland();
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() {
                union() {
                    quoins();
                    difference() { band(W, D, H1); door_band_cut(); apse_cut(); }
                    eave_flare();
                    icicles();
                    bargeboards();
                    finials();
                    snow_roof();
                    nave_windows();
                }
                tower_cut();
            }
            tower_bands();
            tower_windows();
            cross_ball();
            apse_collar();
            apse_curl();
            apse_snow();
            aw_frames();
            aw_bars();
            door_frame();
            // white, not brick: the door's opening cuts the body, and took the bow with it
            wreath_bow();
        }
        room();
        brand_mark();
    }
    difference() { aw_glass(); room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room();
        nave_openings(); nave_frame_holes();
        tower_openings(); tower_frame_holes();
        aw_openings(); aw_holes();
        door_opening();
        joints();
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
    color("#A8483A") { difference() { walls_solid(); tower_cut(); } tower_walls(); apse_walls(); }
    color("#2E3440") { difference() { union() { slab(); slates(); } tower_cut(); } spire(); apse_cone(); apse_slates(); door_leaf(); }
    color("#F4F1EA") { base(); difference() { union() { quoins(); band(W, D, H1); eave_flare(); icicles(); bargeboards(); finials(); snow_roof(); nave_windows(); } tower_cut(); }
                       tower_bands(); tower_windows(); cross_ball(); apse_collar(); apse_curl(); apse_snow(); aw_frames(); door_frame(); }
    color("#2F6B45") { wreath(); garland(); }
}
else if (part == "all") {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
