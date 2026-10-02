// Victorian Townhouse -- building #5 of the Dickens Victorian village (Scott,
// 2026-10-01, picked from four: "Bow-front townhouse").
//
// A tall, narrow three-storey brick townhouse, square, white quoins at its
// corners and white string courses between the storeys. Up the left of its
// front a round brick bow runs all three storeys, three sash windows on each,
// and finishes above the cornice in a bell-flared slate cone. On the right a
// door with a white surround and a glazed fanlight stands up two brick steps
// between low cheek walls. Over a white cornice, a mansard roof: steep slate
// sides in courses with a dormer over the door and two at the back, then a
// low pyramid capped with snow, a finial and a tall chimney. On a soft blob of
// snow. The village's first three-storey house.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The bow opens into the house through
// its whole height, and each dormer through a passage under its own gable, so
// the one light fills all of them.
//
// THE BLOCK is the toy shop's (../toy_shop): brick skin, quoins, string course,
// windows and keystones, with their WHY comments there. THE BOW is the
// church's apse (../church), turned to the front and carried up three storeys.
// The mansard, dormers, door and steps are new. Drawn in world coordinates:
// the front at -y.
//
// COLOUR PARTS, ONE PRINT (victorian_townhouse.3mf), priority
// roof > accent > trim > body:
//   body    brick: the house, the bow, the chimney, the steps and cheek walls
//   roof    slate: the mansard, the dormers, the bow's cone, the finial, the
//           door
//   trim    white: snow base and drifts, quoins, string courses, the cornice,
//           every window's frame, keystone, bars and pane, the door surround,
//           the fanlight, the copings, icicles, snow on the roofs, the wreath's
//           bow
//   accent  evergreen: the wreath, the window box

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";

// =====================================================================================
// THE BLOCK
// =====================================================================================
W        = 52;              // across, x
D        = 52;              // front to back, y: the 46 mm tealight's circle fits inside both ways
wall     = 1.68;
corner_r = 1.5;
plinth_h = 8;
Wh = W/2;  Dh = D/2;
x_in = Wh - wall;
SH       = 1.2;

bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

H1 = 30;  H2 = 52;          // the string courses
H  = 74;                    // the wall's top, under the cornice
tp = tan(55);

// faces: 0 FRONT (-y), 1 right (+x), 2 back, 3 left; u runs left to right as
// seen from outside, so on the front it is the world's x
module nfw(f, u, z, off = 0) {
    p = [[u, -Dh - off], [Wh + off, u], [-u, Dh + off], [-Wh - off, -u]][f];
    translate([p[0], p[1], z]) rotate([90, 0, [0, 90, 180, -90][f]]) children();
}
module nf(f, u, z) nfw(f, u, z) children();

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

// ---- brick, quoins, string courses, cornice ---------------------------------------------------
function rpts(g, z, r = corner_r) = [for (p = rrect_pts(W + 2*g, D + 2*g, r + g, 5)) [p[0], p[1], z]];
// a solid prism in brick courses up to ztop
module brick_skin(ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop - 0.5) rpts(g, z)],
        [rpts(0, ztop)]), slices = 0);
}
module block_solid() brick_skin(H + 1.6);
q_long = 5.0;  q_short = 3.0;  q_off = 0.5;
nq     = 12;                // pairs of courses: up to zc(24) = 70.8, under the cornice
function q_len(j, side) = (j % 2 == 0) == side ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = min(zc(2 * j + 2), H - 2.8)) {
        translate([sx > 0 ? Wh - q_len(j, true) : -Wh - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0 - q_off]);
        translate([sx > 0 ? Wh - 0.5 : -Wh - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0 - q_off]);
    }
}
module quoins() intersection() { brick_skin(H); quoin_boxes(); }
sc_o = 0.9;
// the toy shop's string course: its foot 0.3 inside the wall, its underside
// rising at 55 deg as it comes out
module band(z, o = sc_o, top = 1.6) skin([rpts(-0.3, z - 2.4), rpts(bd + o, z - 2.4 + (bd + o + 0.3) * tp), rpts(bd + o, z + top)], slices = 0);
co = 1.5;                   // the cornice stands out further, and its face is
// 1.2 tall: at 0.6 its lip in front of the mansard measured 1.1 all round
c_top = 2.2;
mb = H + c_top;             // the mansard's foot
module cornice() band(H, co, c_top);

// =====================================================================================
// THE MANSARD
// =====================================================================================
mf  = bd + co - 0.6;        // its foot, 0.6 in from the cornice's edge
m_a = 74;                   // its lower slope
ml_h = 15;
mt  = mb + ml_h;            // the break
m_in = ml_h / tan(m_a);
hw_t = Wh + mf - m_in;      // its half-width at the break
apex = mt + hw_t;           // the upper slope at 45 deg, to a point
function m_off(z) = z <= mb ? mf : z <= mt ? mf - (z - mb) / tan(m_a) : mf - m_in - (z - mt);
// its corners rounded 2.4, shrinking to fit the narrow top: at 0.6 the foot's
// corners stood 0.4 out past the cornice's rounded corners, over air
mr = 2.4;
function mpts(g, z) = [for (p = rrect_pts(W + 2*g, D + 2*g, min(mr, Wh + g - 0.3), 5)) [p[0], p[1], z]];
// the slates in courses, each with a bevelled lower edge standing out 0.6: the
// bevel rises at 37 deg from upright, so no course's edge is a shelf
sl_c = 3.0;
function m_courses(z0, z1, g = 0.6, gh = 0.8) = [for (k = [0 : floor((z1 - z0) / sl_c) - 1], j = [0 : 1])
    let (z = z0 + k * sl_c + [0, gh][j]) [m_off(z) + [0, g][j], z]];
module mansard() {
    P = concat([[mf, H + 1.2]], m_courses(mb, mt), m_courses(mt, apex - 3), [[m_off(apex - 1.2), apex - 1.2]]);
    skin([for (q = P) mpts(q[0], q[1])], slices = 0);
}
// snow on the upper slope: a cap 1.4 over it, its edge wandering round
function wave(t) = 1.2 * sin(t * 3.0) + 0.8 * sin(t * 7.0 + 60);
function sq_r(a) = 1 / max(abs(cos(a)), abs(sin(a)));
module mansard_snow() intersection() {
    skin([mpts(mf - m_in + 1.4, mt), mpts(m_off(apex - 1.2) + 1.4, apex - 1.2)], slices = 0);
    translate([0, 0, mt]) linear_extrude(60) polygon([for (i = [0 : 179]) let (a = 2 * i) (14 + wave(a)) * sq_r(a) * [cos(a), sin(a)]]);
}
fin_z = apex - 3;
module finial() translate([0, 0, fin_z]) {
    translate([-1.3, -1.3, 0]) cube([2.6, 2.6, 7.4]);
    translate([0, 0, 7.4]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0.35, h = 1.3 * tan(60) * 1.2, $fn = 4);
}

// ---- dormers: [face, u] -----------------------------------------------------------------
// at u 10, not 12-14: nearer the corners the house's ceiling there is its side
// face, falling toward the wall, and it met each passage's gable in a level V
// the slicer propped
DORMERS = [[0, 10], [2, -10], [2, 10]];
dw = 5;  dd = 10;           // half-width, depth back into the mansard
dz0 = H + 1.2;  dz1 = H + 13;
d_ridge = dz1 + dw * tp;
// its ridge flattened 1.2 wide: drawn to a point it was a knife edge 0.36 thick
// the length of each dormer
module dormer2d() polygon([[-dw, dz0], [dw, dz0], [dw, dz1], [0.6, d_ridge - 0.6 * tp], [-0.6, d_ridge - 0.6 * tp], [-dw, dz1]]);
module dormers() for (d = DORMERS) nfw(d[0], d[1], 0, mf) translate([0, 0, -dd]) linear_extrude(dd) dormer2d();
// the passage behind each dormer's window, under a gable of its own at 55 deg,
// running in until the house's ceiling has risen above it
dpw = dw - wall;
module dormer_passage() for (d = DORMERS) nfw(d[0], d[1], 0, mf) intersection() {
    translate([0, 0, -30]) linear_extrude(30 - wall)
        // its floor 0.5 over the wall's top: at H - 1 the brick and cornice left
        // in front of it were 0.86 thick
        // its gable at 60 deg, its sides 1.4 under the dormer's eave: at 55 deg the
        // valley where it crossed the house's ceiling ran at 47.8 deg, propped
        polygon([[-dpw, H + 0.5], [dpw, H + 0.5], [dpw, dz1 - 1.4], [0, dz1 - 1.4 + dpw * tan(60)], [-dpw, dz1 - 1.4]]);
    // ending on the plane of the house's ceiling that faces this wall (the bow's
    // opening): ended upright, it left a knife edge where it met that ceiling
    translate([0, Hc, -mf - wall]) rotate([-(90 - rm_a), 0, 0]) translate([-100, -100, 0]) cube(200);
}
DW = [3, 2.8, 6];           // the dormers' windows: sill, a, straight height
d_fr = 2.4;                 // at 1.8 the frames' heads came to 0.7 at their front
function dw_w() = [0, 0, H + DW[0], DW[1], DW[2], "seg"];

// =====================================================================================
// WINDOWS
// =====================================================================================
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);

mull = 1.68;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.4;
// [face, u, z, a, straight height]
WINDOWS = concat(
    [[0, 14, 36, 4.0, 8], [0, 14, 58, 4.0, 8]],
    [for (z = [14, 36, 58], u = [-12, 12]) [2, u, z, z == 14 ? 4.6 : 4.0, z == 14 ? 10 : 8]],
    [for (z = [14, 36, 58], f = [1, 3]) [f, 0, z, z == 14 ? 4.6 : 4.0, z == 14 ? 10 : 8]]);
module win_outline(w) polygon(seg_pts(w[3], w[4]));
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, w[4] * 0.55]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_outer(w, fw = fr_w, se = 0.8) {
    offset(r = fw) win_outline(w);
    translate([-w[3] - fw - se, -sill]) square([2 * (w[3] + fw + se), sill + 1]);
}
module keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2]) polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
module blk_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module blk_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module blk_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
    relief_up(-0.4, fr_t + 0.5) keystone(w);
    relief_up(-0.4, bd) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
// the dormers' windows, in their slate faces
module dormer_openings() for (d = DORMERS) nfw(d[0], d[1], 0, mf) translate([0, 0, -wall - 2]) linear_extrude(wall + 4)
    translate([0, H + DW[0]]) win_outline(dw_w());
module dormer_windows() for (d = DORMERS) nfw(d[0], d[1], 0, mf) translate([0, H + DW[0]]) {
    relief_up(-0.4, 0.8) { offset(r = d_fr) win_outline(dw_w()); offset(r = 0.3) win_outline(dw_w()); }
    relief_up(-0.4, 0.2) win_muntins(dw_w(), 0.6);
    // the pane 0.1 past where the sloped hole begins (-0.2): to -0.4 it left a
    // 0.2 level ledge over each pane and the slicer propped all three; to -0.2
    // exactly it met the hole's start face to face, 420 edges of four faces
    translate([0, 0, -wall]) linear_extrude(wall - 0.1) offset(r = 0.6) win_outline(dw_w());
}
// the frames' holes in the slate face, sheared: cut straight, each window's
// head over its pane was a level 0.4 mm ledge, and the slicer propped a column
// for it from the snow, up through every window below
module dormer_frame_holes() for (d = DORMERS) nfw(d[0], d[1], 0, mf) translate([0, H + DW[0]])
    relief_hole(-0.4, -0.2, 0.8 + 2.4) offset(r = 0.4) win_outline(dw_w());
// a window box under the front window over the door
module box2d(w) {
    bw = w[3] + fr_w + 0.4;
    translate([-bw, -sill - 4.4]) square([2 * bw, 4.4 + 0.9]);
    for (i = [0 : 5]) let (x = -bw + 1.2 + i * (2 * bw - 2.4) / 5)
        translate([x, -sill + 0.7]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_box() let (w = WINDOWS[0]) nf(w[0], w[1], w[2]) relief_up(-0.4, bd + 1.4) box2d(w);

// =====================================================================================
// THE BOW, up the left of the front
// =====================================================================================
rb   = 11;
rbi  = rb - wall;
BC   = [-9.5, -Dh + 1.0];   // its centre, 1 inside the front wall's face
FNB  = 160;
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
// the cone's ceiling line 5 over the wall's top: its bell's underside then
// clears the cornice wrapped round the bow
zb   = H + 5;
tr   = 2.52;
RB   = [zb, rbi, tan(60), tr / cos(60), rb - 2.5, rb + 3, 35, rb + 3];
kv0b = rb - 0.8;
function zsb(v) = R_zs(RB, v);
module at_bc() translate([BC[0], BC[1], 0]) children();
module half() rotate([0, 0, 180]) rotate_extrude(angle = 180, $fn = FNB) children();
module full() rotate_extrude($fn = FNB) children();
function bbrick_prof(zt) = concat([[rbi - 0.3, plinth_h - 0.5], [rb, plinth_h - 0.5]],
    [for (k = [0 : nc(zt) - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < zt + 1) [rb + g, z]],
    [[rb, zt + 2], [rbi - 0.3, zt + 2]]);
module bow_walls() at_bc() intersection() {
    half() polygon(bbrick_prof(R_zc(RB, rbi - 0.3) + 1));
    half() polygon([[0, -5], [rb + 5, -5], [rb + 5, R_zc(RB, rb + 5) + 0.6], [0, R_zc(RB, 0) + 0.6]]);
}
// what the bow takes out of the block's front: its brick, bands and quoins
module bow_cut() at_bc() translate([0, 0, -1]) intersection() {
    cylinder(r = rb - 0.3, h = H + 2.6, $fn = FNB);
    translate([-50, -50, 0]) cube([100, 50, H + 2.6]);
}
// its room, and the opening through the front wall: the room's own section,
// straight to the cone and pointed at 60 deg into it
module arch2d() polygon([[-rbi, -2], [rbi, -2], [rbi, zb], [0, R_zc(RB, 0)], [-rbi, zb]]);
module bow_room() {
    at_bc() half() R_room(RB);
    // through the wall, then on back only above the house's ceiling plane, so
    // the two meet on that plane. Ended upright behind the wall, the solid
    // between its back and the 60 deg ceiling came down to a knife edge
    translate([BC[0], 0, 0]) xz(-Dh - 1, -x_in + 0.3) arch2d();
    intersection() {
        translate([BC[0], 0, 0]) xz(-Dh - 1, -5) arch2d();
        translate([0, -x_in, Hc]) rotate([rm_a, 0, 0]) translate([-100, -100, 0]) cube(200);
    }
}
// the cone runs right round: behind the wall's face it is buried in the mansard
module bow_cone() at_bc() intersection() { full() R_full(RB, kv0b); full() R_slate(RB, kv0b); }
module bow_curl() at_bc() intersection() { full() R_curl(RB, kv0b); translate([-50, -50, 0]) cube([100, 50, 200]); }
sh_c = 2.35;
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module bow_slates() at_bc() {
    ve = RB[5];
    nk = ceil((ve - 6.8) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 6.8))
        if (x0 > x1 + 0.3) full() course_band(RB, x0, x1);
}
module bow_snow() at_bc() intersection() {
    full() polygon([[0, zsb(0) - 1.0], [6, zsb(6) - 1.0], [6, zsb(6) + 1.8], [2, zsb(2) + 2.2], [0, zsb(0) + 2.4]]);
    translate([0, 0, H]) linear_extrude(60) polygon([for (i = [0 : 179]) let (a = 2 * i) (4.2 + wave(a)) * [cos(a), sin(a)]]);
}
b_fin = zsb(0) + 1.4;
module bow_finial() at_bc() translate([0, 0, b_fin - 2.4]) {
    translate([-1.1, -1.1, 0]) cube([2.2, 2.2, 6.0]);
    translate([0, 0, 6.0]) rotate([0, 0, 45]) cylinder(r1 = 1.1 * sqrt(2), r2 = 0.35, h = 1.1 * tan(60) * 1.0, $fn = 4);
}
// the string courses and the cornice carried round it
module bow_collar(z, o, top = 1.6) at_bc() half()
    polygon([[rb - 0.5, z - 2.7], [rb + bd + o, z - 2.7 + (bd + o + 0.5) * tp], [rb + bd + o, z + top], [rb - 0.5, z + top]]);
module bow_collars() { bow_collar(H1, sc_o); bow_collar(H2, sc_o); bow_collar(H, co, c_top); }

// its windows, laid round it in strips like the church's apse: three a floor
module bplace(r, th, z) translate([BC[0] + r * cos(th), BC[1] + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module bcyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    bplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module bclip(d) intersection() { children(); at_bc() cylinder(r = rb + d, h = 200, $fn = FNB); }
// [angle, sill, a, straight height]: 60 deg apart, their frames narrower than
// the block's so a floor's three fit round the bow's front with brick between
bfr_w = 2.0;
BW = [for (z = [14, 36, 58], th = [210, 270, 330]) [th, z, 2.4, z == 14 ? 10 : 8]];
function bw(w) = [0, 0, 0, w[2], w[3]];
function bframe_U(w) = w[2] + bfr_w + 1.4;
module bw_frames() bclip(fr_t + 0.5) for (w = BW) bcyl_relief(rb, w[0], w[1], bframe_U(w))
    relief_up(-0.4, fr_t) { frame_outer(bw(w), bfr_w, 0.3); offset(r = 0.3) win_outline(bw(w)); }
module bw_bars() bclip(bd) for (w = BW) bcyl_relief(rb, w[0], w[1], w[2] + 1) relief_up(-0.4, bd) win_muntins(bw(w), 0.6);
module bw_glass() intersection() {
    for (w = BW) bplace(rb, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(bw(w));
    at_bc() cylinder(r = rb - 0.2, h = 200, $fn = FNB);
}
module bw_openings() for (w = BW) bcyl_relief(rb, w[0], w[1], w[2] + 1) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(bw(w));
module bw_holes() for (w = BW) bcyl_relief(rb, w[0], w[1], bframe_U(w)) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(bw(w));

// =====================================================================================
// THE DOOR, up two steps, with a fanlight
// =====================================================================================
dr_u = 14;
zs   = plinth_h + 3.6;      // its sill, on the landing
dr_a = 4.0;  dr_h = 10;     // the leaf to dr_h, the fanlight's half-round over it
module door_outline() polygon(arch_pts(dr_a, dr_h));
module door_leaf() nf(0, dr_u, zs) difference() {
    translate([0, 0, -wall]) linear_extrude(wall + bd) translate([-dr_a - 0.25, -0.3]) square([2 * dr_a + 0.5, dr_h + 0.3]);
    translate([0, 0, bd - 0.4]) linear_extrude(2) for (s = [-1, 1])
        // low, clear of the wreath, and pointed at 60 deg: square-headed, each
        // panel's 0.4 recess had a level ceiling
        let (x0 = min(s * 0.9, s * 2.7)) polygon([[x0, 0.4], [x0 + 1.8, 0.4], [x0 + 1.8, 0.8], [x0 + 0.9, 0.8 + 0.9 * tan(60)], [x0, 0.8]]);
}
// the fanlight's pane, back in the opening, and its bars fanning out on it
module fan_pane() nf(0, dr_u, zs) translate([0, 0, -wall]) linear_extrude(wall - 0.4) intersection() {   // 1.28 thick, not 0.88
    offset(r = 0.4) door_outline(); translate([-10, dr_h]) square([20, 10]);
}
module fan_bars() nf(0, dr_u, zs) translate([0, 0, -0.5]) linear_extrude(0.6) intersection() {
    door_outline();
    union() {
        translate([-10, dr_h - 0.1]) square([20, 0.9]);
        // 55 deg off level, not 45: at 45 the slicer propped them
        for (a = [55, 90, 125]) translate([0, dr_h]) rotate(a) translate([0, -0.4]) square([10, 0.8]);
        translate([0, dr_h]) circle(r = 1.4, $fn = 24);
    }
}
module door_opening() nf(0, dr_u, zs) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
// the surround's sloped hole, cut from the brick too: cut from the surround
// only, brick filled it down to the fanlight's head, a level 1 mm ledge
module door_hole() nf(0, dr_u, zs) relief_hole(-0.4, -0.5, bd + 0.1) door_outline();
// the surround a flush white band at the bricks' face (the inn's door), its
// hole sheared so the fanlight's recess rises outward instead of a flat head
module door_surround() nf(0, dr_u, zs) difference() {
    translate([0, 0, -0.6]) linear_extrude(0.6 + bd) intersection() {
        offset(r = 2.4) door_outline(); translate([-30, -0.5]) square([60, 100]);
    }
    relief_hole(-0.4, -0.5, bd + 0.1) door_outline();
}
wr_z = zs + 5.6;
module wreath() nf(0, dr_u, wr_z) relief_up(-0.2, bd + 1.0) difference() { circle(r = 2.6, $fn = 40); circle(r = 1.3, $fn = 32); }
module bow2d() { polygon([[0, 0], [-1.9, 0.95], [-1.9, -0.95]]);  polygon([[0, 0], [1.9, 0.95], [1.9, -0.95]]);  circle(r = 0.75); }
module wreath_bow() nf(0, dr_u, wr_z - 2.4) relief_up(-0.2, bd + 1.4) bow2d();   // under it: over it, the bow ran into the fanlight
// the steps, and a low brick cheek wall each side with a white coping
st_w = 6.2;
module steps() {
    translate([dr_u - st_w, -Dh - 3.0, plinth_h - 0.5]) cube([2 * st_w, 3.2, zs - plinth_h + 0.5]);
    translate([dr_u - st_w, -Dh - 5.8, plinth_h - 0.5]) cube([2 * st_w, 6.0, zs - 1.8 - plinth_h + 0.5]);
}
cw_t = 1.6;
module cheek2d(top) polygon([[0.3, plinth_h - 0.5], [-6.6, plinth_h - 0.5], [-6.6, zs - 0.4 + top], [0.3, zs + 2.6 + top]]);
module cheek_walls() for (s = [-1, 1]) let (x = dr_u + s * (st_w + cw_t / 2)) translate([x - cw_t / 2, -Dh, 0]) yz(0, cw_t) cheek2d(0);
// the coping 0.3 down into the wall, which loses it, so the two never meet face to face
module copings() for (s = [-1, 1]) let (x = dr_u + s * (st_w + cw_t / 2)) translate([x - cw_t / 2, -Dh, 0]) yz(0, cw_t)
    polygon([[0.3, zs + 2.3], [-6.6, zs - 0.7], [-6.6, zs + 0.5], [0.3, zs + 3.5]]);

// ---- icicles under the cornice, clear of the windows, the bow and the dormers ---------------------
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 16]) [-Wh + 3 + i * (W - 6) / 16, 2.2 + 2.2 * rnd(i, 40), 1.8 + 0.6 * rnd(i, 80)]];
function ic_clear(f, u) = len([for (w = WINDOWS) if (w[0] == f && w[2] == 58 && abs(u - w[1]) < w[3] + fr_w + 2.2) 1]) == 0
                       && len([for (d = DORMERS) if (d[0] == f && abs(u - d[1]) < dw + 1.5) 1]) == 0
                       && !(f == 0 && u < BC[0] + rb + 5);
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [0 : 3], c = IC) if (ic_clear(f, c[0])) nf(f, c[0], H - 2.2) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

// ---- the chimney, rising from the mansard's right side ----------------------------------------------
ch = [15, 22, -3.5, 3.5];   // x0, x1, y0, y1
ch_top = apex - 2;
module chimney() difference() {
    union() {
        translate([ch[0], ch[2], H]) cube([ch[1] - ch[0], ch[3] - ch[2], ch_top - H]);
        hull() {
            translate([ch[0], ch[2], ch_top - 1.3]) cube([ch[1] - ch[0], ch[3] - ch[2], 0.01]);
            translate([ch[0] - 0.8, ch[2] - 0.8, ch_top]) cube([ch[1] - ch[0] + 1.6, ch[3] - ch[2] + 1.6, 1.6]);
        }
        for (y = [-2.1, 2.1]) translate([(ch[0] + ch[1]) / 2, y, ch_top + 1.4]) cylinder(d = 3.6, h = 4.0, $fn = 32);
    }
    for (y = [-2.1, 2.1]) translate([(ch[0] + ch[1]) / 2, y, ch_top + 3.4]) cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimney_col() translate([ch[0], ch[2], H]) cube([ch[1] - ch[0], ch[3] - ch[2], 80]);

// ---- brick joints ---------------------------------------------------------------------------------------
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, ztop, boxes) {
    L = Wh - q_long - 1;
    nf(f, 0, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}
function frame_box(w) = let (h = w[3] + fr_w + 2.5)
    [w[1] - h, w[1] + h, w[2] - sill - 2 - (w[0] == 0 && w[2] == 36 ? 5 : 0), w[2] + seg_top(w[3], w[4]) + fr_w + 4];
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(w)],
    [[-100, 100, H1 - 2.6, H1 + 2.2], [-100, 100, H2 - 2.6, H2 + 2.2]],
    f == 0 ? [[BC[0] - rb - 1.5, BC[0] + rb + 1.5, 0, 300], [dr_u - dr_a - 4, dr_u + dr_a + 4, 0, 300]] : []);
module joints() for (f = [0 : 3]) wall_joints(f, H - 3, face_boxes(f));

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() {
    translate([-Wh, -Dh]) square([W, D]);
    translate(BC) intersection() { circle(r = rb + bd, $fn = FNB); translate([-30, -30]) square([60, 30]); }
    translate([dr_u - st_w - cw_t, -Dh - 6.6]) square([2 * (st_w + cw_t), 7]);
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[Wh + 1, 10, 4, 7, 3.0], [-Wh - 1, -8, 4, 6, 2.6], [-12, Dh + 1, 7, 3.5, 2.8], [14, Dh + 1, 6, 3.5, 2.4],
          [BC[0] + (rb + 1) * cos(235), BC[1] + (rb + 1) * sin(235), 4, 4, 2.4]];
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
// under the steps, mirrored to read with the house turned over, front toward you
module brand_mark() translate([dr_u, -Dh - 8.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
// the house's room: straight up to just over the top floor's windows, then a
// pyramid at 60 deg. At 55 its hips ran at 45.3 deg and the slicer propped the
// whole ceiling; at 60 they run at 50.8, and it starts lower so its point stays
// 3.5 under the mansard's
rm_a = 60;
Hc   = apex - 3.5 - x_in * tan(rm_a);
module main_room() hull() {
    translate([-x_in, -x_in, -2]) cube([2 * x_in, 2 * x_in, Hc + 2]);
    translate([-0.01, -0.01, Hc + x_in * tan(rm_a)]) cube(0.02);
}
module room() { main_room(); bow_room(); dormer_passage(); }
module body_raw() {
    difference() { union() { block_solid(); chimney(); } bow_cut(); }
    bow_walls();
    steps();
    cheek_walls();
}
module roof_raw() {
    difference() {
        union() {
            difference() { union() { mansard(); dormers(); } chimney_col(); }
            bow_cone(); bow_slates();
        }
        room(); dormer_openings(); dormer_frame_holes();
    }
    finial();
    bow_finial();
    door_leaf();
}
module accent_raw() { wreath(); window_box(); }
module trim_raw() {
    difference() {
        union() {
            base();
            difference() {
                union() { quoins(); band(H1); band(H2); cornice(); blk_windows(); icicles(); }
                bow_cut();
            }
            bow_collars();
            bow_curl();
            bow_snow();
            difference() { mansard_snow(); chimney_col(); }
            bw_frames();
            bw_bars();
            dormer_windows();
            door_surround();
            fan_bars();
            wreath_bow();
            copings();
        }
        room();
        brand_mark();
    }
    difference() { union() { bw_glass(); fan_pane(); } room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room();
        blk_openings(); blk_frame_holes(); joints();
        bw_openings(); bw_holes();
        door_opening(); door_hole();
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
    color("#A8483A") { block_solid(); chimney(); bow_walls(); steps(); cheek_walls(); }
    color("#2E3440") { mansard(); dormers(); bow_cone(); bow_slates(); finial(); bow_finial(); door_leaf(); }
    color("#F4F1EA") { base(); quoins(); band(H1); band(H2); cornice(); blk_windows(); icicles(); bow_collars(); bow_curl();
                       bow_snow(); mansard_snow(); bw_frames(); dormer_windows(); door_surround(); fan_bars(); copings(); }
    color("#2F6B45") { wreath(); window_box(); }
}
else if (part == "all") {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
