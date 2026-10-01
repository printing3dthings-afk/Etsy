// Gingerbread Sweet Shop -- building #3 of the Gingerbread village (Scott,
// 2026-10-01, picked from four: "Layer-cake tower shop").
//
// A layer cake three tiers tall: a gingerbread bottom tier with two rows of
// arched windows and a band of cream round its middle, a chocolate middle
// tier, a gingerbread top tier with round portholes, under a frosting dome
// with a cherry on top. Each tier's ledge is frosted, the frosting dripping
// down the tier below, a rope of piped icing round the foot of the next tier
// and red berries round the ledge. SWEETS in red letters round the front of the
// bottom tier. Out of its front stands a small square gingerbread shop under a
// chocolate gable of scallop tiles and icing: a wide display window, a
// chocolate-bar door, a red-and-white lollipop sign in its gable. On a soft
// blob of snow with peppermints.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The shop opens into the cake through
// its own room's pointed section, so the one light fills both.
//
// THE SHOP is the candy cane chapel's nave (../candy_cane_chapel), in its own
// frame (gables on +-y, front at -y) and set in front of the cake by at_shop().
// THE CAKE's windows are laid round it in strips, like the chapel's tower's.
//
// COLOUR PARTS, ONE PRINT (gingerbread_sweet_shop.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the bottom and top tiers, the shop's walls
//   roof    chocolate: the middle tier, the shop's roof and its tiles, the
//           door, the cherry's stem
//   trim    icing: snow base, the frosting on every ledge and the dome, the
//           drips, the piped ropes, the cream band, window and door frames with
//           their beads, panes and bars, the shop's corner beads, eaves, rakes
//           and roof icing, the lollipop and its stick, the peppermints' white
//   accent  candy red: SWEETS, the berries, the cherry, the lollipop's swirl,
//           the peppermints' stripes

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

wall     = 1.68;
plinth_h = 8;
SH       = 1.2;
tp55     = tan(55);

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
function rnd(i, s) = rands(0, 1, 1, s + i)[0];

// ---- piped icing, windows: the chapel's ----------------------------------------------------
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
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9;
function is_round(w) = w[5] == "round";
function w_top(w) = is_round(w) ? 2 * w[3] : w[4] + w[3];
module win_outline(w) { if (is_round(w)) translate([0, w[3]]) circle(r = w[3]); else polygon(arch_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, is_round(w) ? w[3] - mull/2 : w[4] * 0.6]) square([40, is_round(w) ? mull : 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame2d(w, bead = true) {
    if (is_round(w)) translate([0, w[3]]) circle(r = w[3] + 2.0, $fn = 48);
    else {
        offset(r = fr_w) win_outline(w);
        if (bead) beads(arch_path(w[3], w[4], fr_w - 0.1, bead_sp));
    }
}
module frame_relief(w, bead = true) relief_up(-0.4, fr_t) { frame2d(w, bead); offset(r = 0.3) win_outline(w); }
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }

// =====================================================================================
// THE CAKE, round the origin
// =====================================================================================
FNC = 180;
// [outer radius, foot, top]. The bottom tier's top at 62: its room keeps its
// full width to 50.5 and the 46 mm tealight's circle, 0.5 inside it, has 51.2
TIERS = [[25.5, plinth_h - 0.5, 62], [18.5, 62 - 0.6, 86], [10.5, 86 - 0.6, 100]];
function T(k) = TIERS[k];
function Ti(k) = T(k)[0] - wall;
z_d  = 108.5;               // the dome's crown
// the room: each tier's own width, narrowing at 55 deg under each ledge to the
// next; the top tier's ceiling a cone at 55 deg under the dome
za3 = 94;
function zb(k) = T(k)[2] - 1.5;
function za(k) = zb(k) - (Ti(k) - Ti(k + 1)) * tp55;
module cake_room() rotate_extrude($fn = FNC) polygon([
    [0, -2], [Ti(0), -2], [Ti(0), za(0)], [Ti(1), zb(0)], [Ti(1), za(1)], [Ti(2), zb(1)], [Ti(2), za3], [0, za3 + Ti(2) * tp55]]);
module tier(k) translate([0, 0, T(k)[1]]) cylinder(r = T(k)[0], h = T(k)[2] - T(k)[1], $fn = FNC);
module cake_cut() translate([0, 0, -1]) cylinder(r = T(0)[0] - 0.3, h = 300, $fn = FNC);

// FROSTING on each ledge: its edge 0.9 proud, its underside at 50 deg into the
// tier's wall; and the dome
module frost(k) rotate_extrude($fn = FNC) let (r = T(k)[0], z = T(k)[2], ri = T(k + 1)[0] - 0.5)
    polygon([[ri, z - 0.5], [r - 0.6, z - 0.5], [r - 0.6, z - 2.5], [r + 0.9, z - 0.7], [r + 0.9, z + 0.3], [r + 0.4, z + 0.9], [ri, z + 0.9]]);
module dome() rotate_extrude($fn = FNC) let (r = T(2)[0], z = T(2)[2], R = r + 0.9)
    polygon(concat([[0, z - 0.5], [r - 0.6, z - 0.5], [r - 0.6, z - 2.5], [R, z - 0.7], [R, z + 0.3]],
                   [for (i = [1 : 24]) let (q = 90 * i / 24) [R * cos(q), z + 0.3 + (z_d - z - 0.3) * sin(q)]]));
// a rope of piped beads round each upper tier's foot, half sunk in the frosting
module ropes() for (k = [0, 1]) let (r = T(k + 1)[0] + 0.8, n = round(2 * PI * r / 2.0))
    for (i = [0 : n - 1]) rotate(360 * i / n) translate([r, 0, T(k)[2] + 0.9]) sphere(r = 1.1, $fn = 16);
// berries on each ledge, domes standing on the frosting
module berries() for (k = [0, 1]) let (r = (T(k)[0] + T(k + 1)[0]) / 2 + 0.9, n = k == 0 ? 14 : 10)
    // sunk 0.3: standing on the frosting's top face, each printed loose
    for (i = [0 : n - 1]) rotate(360 * i / n + 9) translate([r, 0, T(k)[2] + 0.9 - 0.3]) intersection() {
        sphere(r = 1.7, $fn = 24);
        translate([-2, -2, 0]) cube(4);
    }
// the cherry, sunk to below its widest in the dome, and its stem
module cherry() translate([0, 0, z_d - 1.2]) sphere(r = 3.2, $fn = 40);
module stem() hull() {
    translate([0, 0, z_d + 1.4]) sphere(r = 0.8, $fn = 16);
    translate([1.6, 0, z_d + 4.6]) sphere(r = 0.8, $fn = 16);
}
// a band of cream round the bottom tier's middle, flush
module cream() difference() {
    translate([0, 0, 30.6]) cylinder(r = T(0)[0] + 0.01, h = 1.6, $fn = FNC);
    translate([0, 0, 29]) cylinder(r = T(0)[0] - 0.6, h = 5, $fn = FNC);
}

// ---- laid round the cake in strips --------------------------------------------------------------
module cplace(r, th, z) translate([r * cos(th), r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module cclip(r, d) intersection() { children(); cylinder(r = r + d, h = 300, $fn = FNC); }
// [tier, angle, sill, a, straight height, kind]; 270 is the front, the shop
// takes 225..315 on the bottom tier
CW = concat(
    [for (th = [22.5, 67.5, 112.5, 157.5, 202.5, 337.5]) [0, th, 15, 3.4, 9, "arch"]],
    [for (th = [0, 45, 90, 135, 180, 225, 315]) [0, th, 34, 3.4, 8, "arch"]],
    // the upper tiers' frames start just inside the frosting: 0.2 and 0.6 above
    // it, each frame's foot was a shelf over a one-layer gap the slicer propped
    [for (th = [30, 90, 150, 210, 270, 330]) [1, th, 65.5, 2.8, 4, "arch"]],
    [for (th = [45, 135, 225, 315]) [2, th, 88.2, 2.2, 0, "round"]]);
function cw(w) = [0, 0, 0, w[3], w[4], w[5]];
function cr(w) = T(w[0])[0];
function cframe_U(w) = w[3] + (is_round(w) ? 3.0 : 3.2);
// the cake's frames: a wider band (2.4), a sill under each, a shallower relief
// (1.0): every raised level part's front is its height less 1.2 (the sloped
// underside), and at 1.8 tall the frames' feet and crowns came to 0.24 mm
module cframe2d(w) {
    if (is_round(w)) translate([0, w[3]]) circle(r = w[3] + 2.6, $fn = 48);
    else {
        offset(r = 2.4) win_outline(w);
        // 3.4 deep: at 3.0 the middle tier's sills met the wall 0.08 above the
        // frosting's top and the near-miss left 30 zero-size bodies
        translate([-w[3] - 2.4, -3.4]) square([2 * w[3] + 4.8, 3.6]);
    }
}
// plain on the cake, no beads: laid round in 1 mm strips, the outermost beads
// were cut into slivers down to 0.02 mm, 170 of the thinnest spans in the model
module c_frames() for (w = CW) cclip(cr(w), 1.0) cyl_relief(cr(w), w[1], w[2], cframe_U(w))
    relief_up(-0.4, 0.6) { cframe2d(cw(w)); offset(r = 0.3) win_outline(cw(w)); }
module c_bars() for (w = CW) cclip(cr(w), 0.4) cyl_relief(cr(w), w[1], w[2], w[3] + 1) relief_up(-0.4, 0.4) win_muntins(cw(w), 0.6);
module c_glass() for (w = CW) intersection() {
    cplace(cr(w), w[1], w[2]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(cw(w));
    cylinder(r = cr(w) - 0.2, h = 300, $fn = FNC);
}
// in strips, like the holes: cut flat on a curve they leave slivers beside
// every window (the toy shop)
module c_openings(k) for (w = CW) if (w[0] == k) cyl_relief(cr(w), w[1], w[2], w[3] + 1)
    translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(cw(w));
module c_holes(k) for (w = CW) if (w[0] == k) cyl_relief(cr(w), w[1], w[2], cframe_U(w))
    relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(cw(w));
// SWEETS round the front, over the shop's ridge, inlaid flush: raised, every
// level stroke (the E's arms, the T's bar) came to a knife edge under its
// sloped underside, down to 0.01 mm
module sweets() intersection() {
    difference() { cylinder(r = T(0)[0] + 0.01, h = 100, $fn = FNC); cylinder(r = T(0)[0] - 0.6, h = 100, $fn = FNC); }
    cyl_relief(T(0)[0], 270, 56.2, 12.5, 0.6) translate([0, 0, -1.5]) linear_extrude(2)
        text("SWEETS", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
}
// DRIPS off each ledge and the dome, clear of the windows' heads and SWEETS
function cw_near(k, th, d) = len([for (w = CW) if (w[0] == k && abs((th - w[1] + 540) % 360 - 180) < d) 1]) > 0;
function dr_ok(k, th) = k == 0 ? abs(th - 270) > 32
                      : k == 1 ? !cw_near(1, th, 16)
                               : !cw_near(2, th, 40);
DRIPS = [for (k = [0 : 2], i = [0 : [44, 32, 18][k] - 1]) let (th = 360 * i / [44, 32, 18][k] + 4 * k)
            if (dr_ok(k, th)) [k, th, 1.4 + 3.4 * rnd(i, 70 + k), 2.0 + 0.5 * rnd(i, 90 + k)]];
module c_drips() for (d = DRIPS) cclip(T(d[0])[0], 1.2) cyl_relief(T(d[0])[0], d[1], T(d[0])[2] - 2.6, 1.6)
    relief_up(-0.4, 1.2) drip2d(d[2] + 1.2, d[3]);

// =====================================================================================
// THE SHOP: the chapel's nave, in its own frame
// =====================================================================================
SYc      = -25;             // its centre: front face at y -36
module at_shop() translate([0, SYc, 0]) children();
W        = 36;
D        = 22;
corner_r = 2.5;
Wh = W/2;  Dh = D/2;
H     = 24;
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
// out to xe + 2, not the chapel's 40: on this low shop the ceiling's line is
// under the floor by x = 40, the outline crossed itself and came out empty, and
// the shop lost its room and its side walls
module below_ceil() let (X = xe + 2) xz(-60, 60) polygon([[-X, -5], [X, -5], [X, z_ceil(X)], [0, z_ceil(0)], [-X, z_ceil(-X)]]);
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
module shop_room() intersection() {
    translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
    below_ceil();
}
cb_r = 1.3;  cb_sp = 1.7;
function bead_rad(z, n) = max([for (i = [0 : n]) let (d = z - i * cb_sp) abs(d) < cb_r ? sqrt(cb_r * cb_r - d * d) : 0]);
function bead_profile(n, k = 12) = let (z0 = -cb_r, z1 = n * cb_sp + cb_r, m = ceil((z1 - z0) / cb_sp * k))
    concat([[0, z0]], [for (j = [1 : m - 1]) let (z = z0 + (z1 - z0) * j / m) [bead_rad(z, n), z]], [[0, z1]]);
module corner_beads() {
    n = floor((zf0 - 1 - plinth_h) / cb_sp);
    for (sx = [-1, 1])
        translate([sx * (Wh - corner_r + (corner_r + 0.35) / sqrt(2)), -(Dh - corner_r + (corner_r + 0.35) / sqrt(2)), plinth_h + 0.6])
            rotate_extrude($fn = 32) polygon(bead_profile(n));
}
// [face, u, z, a, straight height, kind]: a wide display window, a window in
// each side
WINDOWS = [[1, 6.5, 13, 5.2, 8, "arch"], [2, -2, 13, 2.6, 7, "arch"], [3, -2, 13, 2.6, 7, "arch"]];
module shop_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module shop_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) win_outline(w);
module shop_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    frame_relief(w);
    relief_up(-0.4, 0.4) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
// THE DOOR, a chocolate bar, left of the window
du_ = -10;
door_a = 3.2;  door_h = 10;
module door_leaf() nf(1, du_, plinth_h) difference() {
    // the wall's depth only: 1 deeper, its foot hung over the open base
    translate([0, 0, -wall]) linear_extrude(wall + 0.2) translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
    // scored into squares by V grooves, their upper faces leaning 50 deg
    translate([-0.5, -1, -0.1]) cube([1, door_h + door_a + 4, 1]);
    for (zg = [3.4, 6.8, 10.2]) hull() {
        translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
        translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
    }
}
module door_opening() nf(1, du_, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(door_a, door_h));
module door_hole() nf(1, du_, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
module door_frame() nf(1, du_, plinth_h) relief_up(-0.4, fr_t) {
    union() {
        intersection() { offset(r = fr_w) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
        intersection() { beads(arch_path(door_a, door_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
    }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
// THE LOLLIPOP sign in the gable, on a stick down between door and window
lp_z = 38;  lp_r = 5.5;
module swirl2d() for (s = [0, 180]) rotate(s)
    for (i = [0 : 35]) let (a0 = 20 * i, a1 = 20 * (i + 1), r0 = 0.5 + lp_r * a0 / 760, r1 = 0.5 + lp_r * a1 / 760)
        if (r1 < lp_r - 0.3) hull() { rotate(a0) translate([r0, 0]) circle(r = 0.55, $fn = 12); rotate(a1) translate([r1, 0]) circle(r = 0.55, $fn = 12); }
module lollipop() {
    nf(1, 0, lp_z) relief_up(-0.4, 1.3) circle(r = lp_r, $fn = 48);
    nf(1, 0, 29.6) relief_up(-0.4, 0.9) translate([-0.9, 0]) square([1.8, lp_z - 29.6]);
}
module lollipop_swirl() intersection() {
    nf(1, 0, lp_z) relief_up(-0.4, 1.3) circle(r = lp_r, $fn = 48);
    nf(1, 0, lp_z) translate([0, 0, -5]) linear_extrude(10) swirl2d();
}
// drips off the side eaves, clear of the windows; rakes on the gables
DR = [for (i = [0 : 12]) [-Dh + 2.6 + i * (D - 5.2) / 12, 1.6 + 3.4 * rnd(i, 70), 2.2 + 0.5 * rnd(i, 90)]];
function dr_clear(f, u) = len([for (w = WINDOWS) if (w[0] == f && abs(u - w[1]) < w[3] + fr_w + bead_r + 1.6) 1]) == 0;
module eave_drips() for (f = [2, 3], c = DR) if (dr_clear(f, c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(c[1], c[2]);
rb_h = 3.2;  rb_t = 1.2;
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
RD = [for (i = [1 : 13]) let (x = 1.6 + i * 2.1) if (x < Wh - 2.4) [x, 1.2 + 3.2 * rnd(i, 110), 2.0 + 0.4 * rnd(i, 130)]];
module rake2d(ext) {
    X = Wh - 1;
    polygon([[-X, z_out(X) + cp_hi + ext], [0, z_out(0) + cp_hi + ext], [X, z_out(X) + cp_hi + ext],
             [X, z_out(X) - rb_h], [0, z_out(0) - rb_h], [-X, z_out(X) - rb_h]]);
    for (d = RD, s = [-1, 1]) let (x = s * d[0]) translate([x, z_out(x) - rb_h + 0.6]) drip2d(d[1] + 0.6, d[2]);
}
module rakes() mirror([0, 1, 0]) {
    xz(Dh - wall - 0.3, Dh - 0.05) gable_poly(cp_lo, cp_hi);
    intersection() {
        xz(Dh - 0.1, Dh + rb_t) minkowski() { rake2d(0); translate([-0.01, -60]) square([0.02, 60]); }
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
            xz(Dh - 1, Dh + 4) rake2d(10);
    }
}
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
            translate([0, 0, 20]) linear_extrude(100) intersection() {
                union() {
                    translate([-10, -y_rr - 1]) square([x0 + 10, 2 * y_rr + 2]);
                    for (j = [-8 : 8]) translate([x0, j * tw + (k % 2) * tw / 2]) scale([sd, tw / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                translate([-10, -y_rr - 1]) square([xe + 10, 2 * y_rr + 2]);
            }
        }
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0)], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
ic_x = 8;
function ic_edge(y) = ic_x + 1.8 * sin(y * 23) + 1.2 * sin(y * 53 + 40);
ic_rc = 2.2;
ic_zc = z_out(0) + 2.0 - ic_rc / cos(r_ang);
module icing_roof() intersection() {
    xz(-y_rr - 0.4, y_rr + 0.4) polygon(concat([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                           [xe, z_out(xe) + 2.0]],
                           [for (a = [r_ang : -5 : -r_ang]) [ic_rc * sin(a), ic_zc + ic_rc * cos(a)]],
                           [[-xe, z_out(xe) + 2.0]]));
    translate([0, 0, 20]) linear_extrude(100)
        polygon(concat([for (i = [0 : 40]) let (y = -Dh + 2 * Dh * i / 40) [ic_edge(y), y]],
                       [for (i = [40 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 40) [-ic_edge(-y), y]]));
}

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() { circle(r = T(0)[0], $fn = FNC); translate([-Wh, SYc - Dh]) square([W, D]); }
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 8, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[26, 8, 4, 7, 3.0], [-26, -6, 4, 6, 2.6], [8, 26, 7, 4, 2.8], [-14, 22, 5, 4, 2.4]];
// on the base's flat top: further out they hung over its rounded edge
PM = [[-14, SYc - Dh - 2.8, 2.2], [17, SYc - Dh - 2.8, 2.0], [24.5, -14.4, 2.2]];
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
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
// under the shop's front, between its wall and the base's edge
module brand_mark() translate([4, SYc - Dh - 4.8, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() { cake_room(); at_shop() shop_room(); }
module body_raw() {
    tier(0);
    tier(2);
    difference() { at_shop() walls_solid(); cake_cut(); }
}
module roof_raw() {
    // its frames' holes too, though the frames lose to this part anyway: without
    // them each pane's 0.2 recess had a flat head and the slicer propped all six
    difference() { tier(1); cake_room(); c_openings(1); c_holes(1); }
    difference() { at_shop() union() { slab(); tiles(); } room(); cake_cut(); }
    at_shop() door_leaf();
    stem();
}
module accent_raw() {
    sweets();
    berries();
    // cut by the room: sunk 1.2 into the dome its foot reached under the room's
    // ceiling and hung there
    difference() { cherry(); room(); }
    at_shop() lollipop_swirl();
    peppermints(true);
}
module trim_raw() {
    difference() {
        union() {
            base();
            frost(0); frost(1); dome();
            ropes();
            cream();
            c_drips();
            c_frames();
            c_bars();
            difference() {
                at_shop() union() { corner_beads(); eave_flare(); eave_drips(); rakes(); icing_roof(); shop_windows(); lollipop(); door_frame(); }
                cake_cut();
            }
            peppermints();
        }
        room();
        brand_mark();
    }
    difference() { c_glass(); room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room();
        c_openings(0); c_openings(2); c_holes(0); c_holes(2);
        at_shop() { shop_openings(); shop_frame_holes(); door_opening(); door_hole(); }
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
else if (part == "all") {
    color("#C68642") body_part();
    color("#5A3825") roof_part();
    color("#F7F3EE") trim_part();
    color("#D7263D") accent_part();
}
