// Victorian Clock Tower -- building #7 of the Dickens Victorian village (Scott,
// 2026-10-02, picked from four: "Square tower on a round base").
//
// A round one-storey brick drum under a slate cone, arched sash windows round
// it and a door with a wreath. Out of the cone rises a square brick tower with
// white quoins, a white string course, and on each side a big white clock face
// in a raised white ring, under a white cornice and a steep slate pyramid with
// snow on its point and a finial. Icicles under the drum's eave. On a soft blob
// of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed. The clock faces are glazed too, the tower's inside open to the room
// below, so lit they glow like a station clock; their hour marks and hands run
// through the white glass in slate and show dark against it.
//
// THE DRUM is the round cottage's (../cottage) without its gable: the same
// roof profile, brick courses, windows laid round the wall in strips, icicles
// and base, with every fix recorded there. THE DOOR is the toy shop's tower
// door (../toy_shop). THE TOWER is new: square courses like the inn's, the
// townhouse's bands for the string course and cornice, and its mansard's
// courses turned into a pyramid.
//
// COLOUR PARTS, ONE PRINT (victorian_clock_tower.3mf), priority
// roof > accent > trim > body:
//   body    brick: the drum, the tower, the step
//   roof    slate: the cone, the pyramid, the finial, the door, the clocks'
//           hour marks and hands
//   trim    white: snow base and drifts, the eave's soffit, snow on both roofs,
//           icicles, quoins, the string course and cornice, every window's
//           frame, keystone, bars and pane, the clock faces and their rings,
//           the door frame, the wreath's bow
//   accent  evergreen: the wreath

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// =====================================================================================
// THE DRUM (the round cottage's)
// =====================================================================================
Rw       = 27;              // the brick's face (50.6 clear inside)
wall     = 1.68;
plinth_h = 8;
SH       = 1.2;
fl_ang   = 52;
L0       = 0;

module sweep() rotate_extrude($fn = FN) children();
module stadium(r) circle(r = r, $fn = FN);
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

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

// ---- the cone's profile (the shop-house's) -----------------------------------------------
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
module R_choc(R, kv0) polygon([[0, -10], [kv0 - 0.01, -10], [kv0 - 0.01, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_below(R) polygon([[0, -5], [R[1] + 20, -5], [R[1] + 20, R_zc(R, R[1] + 20)], [0, R_zc(R, 0)]]);

// the eave at 48: the 46.6 mm tealight's circle reaches 23.3 out, where the
// cone's ceiling stands at 51
H   = 48;
tp  = tan(58);
tv  = 2.52 / cos(58);
RV  = [H, Rw - wall, tp, tv, Rw - 3, Rw + 3.5, 35, Rw + 3.5];
kv0 = Rw - 0.8;
zfu = R_fl(RV, Rw);
function zs(v) = R_zs(RV, v);
module below_ceil() sweep() R_below(RV);

// ---- the drum's brick ------------------------------------------------------------------------
bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);
z_wt = R_zc(RV, Rw) + 0.6;
nb = ceil((z_wt + 30 - plinth_h - 0.4) / bp);
function brick_prof(ztop) = concat([[Rw - wall - 0.3, plinth_h - 0.5], [Rw, plinth_h - 0.5]],
    [for (k = [0 : nb - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < ztop - 0.5) [Rw + g, z]],
    [[Rw, ztop], [Rw - wall - 0.3, ztop]]);
module drum() sweep() polygon(concat([for (p = brick_prof(z_wt)) if (p[1] < z_wt - 0.01) p],
                                     [[Rw, z_wt], [Rw - wall - 0.3, R_zc(RV, Rw - wall - 0.3) + 0.6]]));

// ---- the drum's windows, laid round it in strips --------------------------------------------
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.3;
// [s, z, a, h]: two either side of the door, two at the back
SW = [[s_at(-35, Rw), 16, 4.6, 13], [s_at(215, Rw), 16, 4.6, 13], [s_at(40, Rw), 16, 4.6, 13], [s_at(140, Rw), 16, 4.6, 13]];
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

// ---- THE DOOR, at the front (the toy shop's tower door) ----------------------------------------
dth = -90;
dr_a = 4.4;  dr_h = 13;
module cplace(r, th, z) translate([r * cos(th), r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module tclip(d) intersection() { children(); cylinder(r = Rw + d, h = 200, $fn = FN); }
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() difference() {
    intersection() {
        cplace(Rw, dth, plinth_h) translate([0, 0, -wall - 1]) linear_extrude(wall + 2)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(dr_a, dr_h + 0.3));
        difference() { cylinder(r = Rw + 0.2, h = 100, $fn = FN); translate([0, 0, -1]) cylinder(r = Rw - wall + 0.15, h = 102, $fn = FN); }
    }
    cyl_relief(Rw + 0.2, dth, plinth_h, dr_a + 0.6) translate([0, 0, -0.3]) linear_extrude(2) {
        // low, clear of the wreath's bow: up to 5.8 their heads ran into it
        panel2d(-3.2, -0.6, 1.2, 3.6);  panel2d(0.6, 3.2, 1.2, 3.6);
    }
}
module door_opening() cplace(Rw, dth, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(dr_a, dr_h));
module door_hole() cyl_relief(Rw, dth, plinth_h, dr_a + 2.4) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(dr_a, dr_h));
module door_frame() tclip(fr_t) cyl_relief(Rw, dth, plinth_h, dr_a + 3) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.8) polygon(arch_pts(dr_a, dr_h)); translate([-30, -0.5]) square([60, 100]); }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(dr_a, dr_h + 1));
}
wr_z = plinth_h + dr_h - 1.5;
module wreath() tclip(bd + 0.8) cyl_relief(Rw, dth, wr_z, 4.2) relief_up(-0.4, bd + 0.8) difference() { circle(r = 3.2, $fn = 40); circle(r = 1.7, $fn = 32); }
module bow2d() {
    polygon([[0, 0], [-2.2, 1.1], [-2.2, -1.1]]);  polygon([[0, 0], [2.2, 1.1], [2.2, -1.1]]);
    circle(r = 0.8);
    polygon([[-0.4, 0], [-1.2, -1.9], [-0.4, -1.9], [0.1, -0.5]]);
    polygon([[0.4, 0], [1.2, -1.9], [0.4, -1.9], [-0.1, -0.5]]);
}
module wreath_bow() tclip(bd + 1.2) cyl_relief(Rw, dth, wr_z - 3.2, 2.8) relief_up(-0.4, bd + 1.2) bow2d();
module step() intersection() {
    translate([0, 0, plinth_h - 0.5]) difference() { cylinder(r = Rw + 3.4, h = 1.9, $fn = FN); translate([0, 0, -1]) cylinder(r = Rw - 0.5, h = 4, $fn = FN); }
    rotate([0, 0, dth - 12]) rotate_extrude(angle = 24, $fn = FN) square([60, 20]);
}

// ---- icicles under the eave, clear of the door ------------------------------------------------
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 41]) let (s = i * sper(Rw) / 42) [s, 1.4 + 1.8 * rnd(i, 70), 1.8 + 0.4 * rnd(i, 110)]];
module icicles() for (d = IC) splace(Rw, d[0], zfu + 1) relief_up(-0.4, 1.2) drip2d(d[1], d[2]);

// ---- the cone ------------------------------------------------------------------------------------
module roof_slate() intersection() { sweep() R_full(RV, kv0); sweep() R_choc(RV, kv0); }
module soffit() sweep() R_curl(RV, kv0);
sh_c = 2.35;
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module slates() {
    ve = RV[5];
    nk = ceil((ve - 0.6) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 0.6))
        if (x0 > x1 + 0.3) sweep() course_band(RV, x0, x1);
}
// snow on the cone's upper part, round the tower's foot, its edge in waves
function wave(t) = 2.2 * sin(t * 1.7) + 1.3 * sin(t * 4.1 + 60);
module snow_cone() intersection() {
    sweep() polygon([[0, zs(0) - 1.0], [RV[4], zs(RV[4]) - 1.0], [RV[4], zs(RV[4]) + 2.0], [0, zs(0) + 2.0]]);
    translate([0, 0, 40]) linear_extrude(100) polygon([for (i = [0 : 199]) let (a = 360 * i / 200) (21.5 + wave(i * 3.3)) * [cos(a), sin(a)]]);
}

// =====================================================================================
// THE TOWER, square, out of the cone
// =====================================================================================
T   = 16;                   // half-width at the brick's face
Ti  = T - wall;
corner_r = 1.0;
function sq_pts(h, z, r = corner_r) = [for (p = rrect_pts(2 * h, 2 * h, max(min(r, h - 0.05), 0.05), 5)) [p[0], p[1], z]];
// square courses bulging bd out of the face (the inn's brick skin)
module tower_skin(ztop) {
    n = nc(ztop);
    skin(concat(
        [sq_pts(T, 30)],
        [for (k = [nc(30) : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) sq_pts(T + g, z, corner_r + g)],
        [sq_pts(T, ztop + 2)]), slices = 0);
}
// where the cone is cut for the tower: 0.3 inside its face, so the cone runs into
// the brick and no pocket opens between the courses' bumps at the tower's foot
// rounded like the tower's corners (r - 0.3): cut square, its corners met the
// tower's rounded ones tangentially and left zero-thick slivers (11 bodies)
module tower_col() translate([0, 0, -1]) linear_extrude(302) polygon([for (p = sq_pts(T - 0.3, 0, corner_r - 0.3)) [p[0], p[1]]]);

// heights
z_sc  = 78;                 // the string course, under the clock stage
z_ck  = 93.2;               // the clocks' centres: the rings 0.7 over the string course
rc    = 10.5;               // the dial's radius
ck_w  = 2.4;                // the ring round it
z_cn  = 108.5;              // the cornice: its foot 0.4 over the rings
c_top = 2.2;
zb    = z_cn + c_top;       // the pyramid's foot
// the tower: its walls stand on the cone's ceiling (the chimney's way), so they
// rise from a 58 deg slope, not a ledge, and run 1 up into the pyramid
// Under the cone (outside its cut, T - 0.3) they stop 0.3 over the ceiling, in
// the cone, which takes it: down to the ceiling there, their foot lay on the
// cone's underside and the two met in open edges
module tower_walls() difference() {
    tower_skin(zb + 1);
    below_ceil();
    difference() { sweep() R_below([H + 0.3, RV[1], RV[2]]); tower_col(); }
}

// QUOINS on the four corners, from over the cone (63) up to the string course:
// from inside the cone, they met it and the tower in open edges
q_long = 5.0;  q_short = 2.8;  q_off = 0.5;
module quoin_boxes() for (k = [nc(63) : nc(z_sc - 3) - 1], sx = [-1, 1], sy = [-1, 1])
    let (z0 = zc(k), z1 = zc(k + 1), L = k % 2 ? q_long : q_short, M = k % 2 ? q_short : q_long) {
        translate([sx > 0 ? T - L : -T - 3, sy > 0 ? T - 0.5 : -T - 3, z0 + q_off]) cube([L + 3, 3.5, z1 - z0 - q_off]);
        translate([sx > 0 ? T - 0.5 : -T - 3, sy > 0 ? T - M : -T - 3, z0 + q_off]) cube([3.5, M + 3, z1 - z0 - q_off]);
    }
module quoins() difference() { intersection() { tower_skin(z_sc); quoin_boxes(); } below_ceil(); }

// BANDS (the townhouse's): rising at 55 deg as they come out
bt = tan(55);
// their corners rounded with the offset (r + g), so a corner stands out no
// further than a face: square, the cornice's corners leaned out at 45 deg and
// the slicer propped all four from the table
function bpts(g, z) = sq_pts(T + g, z, corner_r + g);
module band(z, o, top = 1.6) skin([bpts(-0.3, z - 2.4), bpts(bd + o, z - 2.4 + (bd + o + 0.3) * bt), bpts(bd + o, z + top)], slices = 0);
co = 1.5;
module string_course() band(z_sc, 0.9);
module cornice() band(z_cn, co, c_top);

// ---- THE CLOCKS, one on each face ----------------------------------------------------------------
// on the face f (0 front -y, 1 right +x, 2 back +y, 3 left -x), 2D x along it
// as seen from outside, local z out of the wall
module tf(f, z) rotate([0, 0, 90 * f]) translate([0, -T, z]) rotate([90, 0, 0]) children();
module ck_outline() circle(r = rc, $fn = 96);
module ck_openings() for (f = [0 : 3]) tf(f, z_ck) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) ck_outline();
module ck_holes() for (f = [0 : 3]) tf(f, z_ck) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) ck_outline();
module ck_rings() for (f = [0 : 3]) tf(f, z_ck) relief_up(-0.4, fr_t) { circle(r = rc + ck_w, $fn = 96); offset(r = 0.3) ck_outline(); }
// the dial: the white glass in the wall, as every window's
module ck_glass() for (f = [0 : 3]) tf(f, z_ck) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) ck_outline();
// the hour marks and hands, slate, run right through the glass: 0.8 wide or
// more, every gap 0.8 or more. Ten past ten.
module seg2(a, b, w) hull() { translate(a) circle(d = w, $fn = 12); translate(b) circle(d = w, $fn = 12); }
module dial2d() {
    for (i = [0 : 11]) rotate(90 - 30 * i) translate([i % 3 == 0 ? 6.8 : 7.6, -(i % 3 == 0 ? 0.6 : 0.4)])
        square([i % 3 == 0 ? 2.8 : 2.0, i % 3 == 0 ? 1.2 : 0.8]);
    seg2([0, 0], 5.0 * [cos(150), sin(150)], 1.4);     // hour hand, to 10
    seg2([0, 0], 6.2 * [cos(30), sin(30)], 1.0);       // minute hand, to 2
    circle(r = 1.3, $fn = 24);
}
module ck_hands() for (f = [0 : 3]) tf(f, z_ck) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) dial2d();

// =====================================================================================
// THE PYRAMID, its slate courses, snow on its point, a finial
// =====================================================================================
p_a  = 68;                  // its faces: the hips run at 60 deg
Tp   = T + bd + co - 0.6;   // its foot, 0.6 in from the cornice's edge
apex = zb + Tp * tan(p_a);
function p_off(z) = Tp - (z - zb) / tan(p_a);
// the courses each with a bevelled lower edge standing out 0.6 over 1.0: the
// bevel is 31 deg from upright on a face and 40 at a hip, never a shelf
pc = 3.0;
function p_courses(z0, z1, g = 0.6, gh = 1.0) = [for (k = [0 : floor((z1 - z0) / pc) - 1], j = [0 : 1])
    let (z = z0 + k * pc + [0, gh][j]) [p_off(z) + [0, g][j], z]];
z_pt = apex - 2.4;          // the point blunted to take the finial
// its corners rounded with the cornice's (r + offset), shrinking up the hips:
// nearly square (0.3), its foot's corners stood 0.3 out past the cornice's
// rounded ones and the slicer propped all four from the cone
function p_r(h) = max(0.3, corner_r + h - T);
module pyramid() let (P = concat([[Tp, zb]], p_courses(zb + 1.0, z_pt - 2), [[p_off(z_pt), z_pt]]))
    skin([for (q = P) sq_pts(q[0], q[1], p_r(q[0]))], slices = 0);
// the tower's room under it, its ceiling the pyramid's face moved in 2.52
tvp = 2.52 / cos(p_a);
module tower_room() intersection() {
    translate([-Ti, -Ti, -2]) cube([2 * Ti, 2 * Ti, 300]);
    union() {
        translate([0, 0, -2]) linear_extrude(zb - tvp + 2) square(2 * Tp, center = true);
        translate([0, 0, zb - tvp]) linear_extrude(Tp * tan(p_a), scale = 0) square(2 * Tp, center = true);
    }
}
// snow on its point, the cap 1.4 over the slates, its edge wandering
function sq_r(a) = 1 / max(abs(cos(a)), abs(sin(a)));
function pw(t) = 0.9 * sin(t * 3.0) + 0.6 * sin(t * 7.0 + 60);
module pyramid_snow() intersection() {
    skin([sq_pts(p_off(zb + 20) + 1.4, zb + 20, 0.3), sq_pts(p_off(z_pt) + 1.4, z_pt, 0.3)], slices = 0);
    translate([0, 0, zb]) linear_extrude(80) polygon([for (i = [0 : 179]) let (a = 2 * i) (6.5 + pw(a)) * sq_r(a) * [cos(a), sin(a)]]);
}
fin_z = z_pt - 0.6;
module finial() translate([0, 0, fin_z]) {
    translate([-1.3, -1.3, 0]) cube([2.6, 2.6, 6.4]);
    translate([0, 0, 6.4]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0.35, h = 1.3 * tan(60) * 1.2, $fn = 4);
}

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
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
// in the band between the room's opening (-25.3) and the base's edge (-33.5),
// clear of the step
module brand_mark() translate([0, -29.6, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- the drum's brick joints, clear of every opening ----------------------------------------------
function box_s(s0, s1, z0, z1) = [s0, s1, z0, z1];
OPEN = concat(
    [box_s(s_at(dth, Rw) - dr_a - 6, s_at(dth, Rw) + dr_a + 6, 0, 200)],
    [box_s(sper(Rw) - 4, sper(Rw) + 100, 0, 200)],
    [for (w = SW) box_s(w[0] - w[2] - fr_w - 3, w[0] + w[2] + fr_w + 3, w[1] - sill - 6, w[1] + seg_top(w[2], w[3]) + fr_w + 4)]);
function clear_at(s, z0, z1) = len([for (b = OPEN) if (s + bj > b[0] && s - bj < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
nj = floor(sper(Rw) / bl);
module joints() for (k = [1 : nb - 1]) let (z0 = zc(k), z1 = zc(k + 1)) if (z1 < zfu - 0.5)
    for (j = [0 : nj - 1]) let (s = (j + (k % 2) / 2) * sper(Rw) / nj) if (clear_at(s, z0, z1))
        splace(Rw, s, z0) translate([-bj / 2, 0, -0.05]) cube([bj, z1 - z0, 2.1]);

// =====================================================================================
// PARTS
// =====================================================================================
module room() { sweep() polygon([[0, -2], [Rw - wall, -2], [Rw - wall, H], [0, R_zc(RV, 0)]]); tower_room(); }
module body_raw() {
    drum();
    tower_walls();
    step();
}
module roof_raw() {
    difference() { union() { roof_slate(); slates(); } room(); tower_col(); }
    difference() { pyramid(); room(); }
    finial();
    door_leaf();
    difference() { ck_hands(); room(); }
}
module accent_raw() wreath();
module trim_raw() {
    difference() {
        union() {
            base();
            soffit();
            difference() { snow_cone(); tower_col(); }
            icicles();
            sw_frames();
            door_frame();
            wreath_bow();
            quoins();
            string_course();
            cornice();
            ck_rings();
            pyramid_snow();
        }
        room();
        brand_mark();
    }
    // the glass goes back in after the rooms and openings are cut, and stops at
    // the room: 0.2 and 0.6 into it, the windows' and clocks' glass hung its
    // lower edges in the room and the slicer propped them from the table
    difference() { union() { sw_glass(); ck_glass(); } room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); sw_openings(); sw_holes(); joints();
        door_opening(); door_hole();
        ck_openings(); ck_holes();
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
else if (part == "dial")   dial2d();
else {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
