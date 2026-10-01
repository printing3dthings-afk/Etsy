// Gingerbread Cocoa Cafe -- building #4 of the Gingerbread village (Scott,
// 2026-10-01, picked from four: "Cocoa-mug tower cafe").
//
// A round tower shaped like a white hot-cocoa mug: red stripes at its foot and
// under its rim, COCOA in red across its front, arched windows outlined in red,
// a chunky red handle on its side. In it, cocoa to just under the rim, a tall
// swirl of whipped cream, toasted marshmallows floating round it and a
// candy-cane stirrer leaning out. Out of its front stands a small square
// gingerbread cafe under a chocolate gable of scallop tiles and icing: a
// chocolate-bar door, an arched display window under a red-and-white striped
// awning, a piped heart in its gable. On a soft blob of snow with peppermints.
//
// A hollow lantern lit by a battery LED tealight: open base, the cafe's
// windows glazed with their bars on the pane, and the white mug thin enough to
// glow all round between its red lines.
//
// THE CAFE is the sweet shop's shop (../sweet_shop), the candy cane chapel's
// nave, in its own frame (gables on +-y, front at -y) and set in front of the
// mug by at_shop(). THE MUG is the sweet shop's bottom tier, its room narrowing
// at 55 deg into a cone under the cream.
//
// COLOUR PARTS, ONE PRINT (gingerbread_cocoa_cafe.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the cafe's walls, the toasted marshmallows
//   roof    chocolate: the cocoa, the cafe's roof and its tiles, the door
//   trim    icing: snow base and drifts, the mug, the whipped cream, the
//           stirrer, the awning's white, the cafe's frames with their beads,
//           panes and bars, corner beads, eaves, rake and roof icing, the heart,
//           the peppermints' white
//   accent  candy red: the mug's stripes, COCOA, its windows' outlines and bars,
//           the handle, the awning's and stirrer's stripes, the peppermints'
//           stripes

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
// THE MUG, round the origin
// =====================================================================================
FNC  = 180;
MR   = 25.5;                // its radius: the 46 mm tealight's circle, 0.5 inside it
MRi  = MR - wall;
M_rim = 63;
cocoa_z = 61;
// the room keeps its full width to 49.6, so the circle's edge has 50.3, then
// closes in at 55 deg to a point under the cream
za_m = 49.6;
module mug_room() rotate_extrude($fn = FNC) polygon([[0, -2], [MRi, -2], [MRi, za_m], [0, za_m + MRi * tp55]]);
module mug_cut() translate([0, 0, -1]) cylinder(r = MR - 0.3, h = 300, $fn = FNC);
module mug_solid() translate([0, 0, plinth_h - 0.5]) cylinder(r = MR, h = M_rim - plinth_h + 0.5, $fn = FNC);
module mug_shell() difference() {
    mug_solid();
    translate([0, 0, plinth_h - 2]) cylinder(r = MRi, h = 100, $fn = FNC);
}
// the cocoa, from under the room's ceiling to just under the rim
module cocoa() intersection() {
    translate([0, 0, 40]) cylinder(r = MRi + 0.3, h = cocoa_z - 40, $fn = FNC);
    mug_solid();
}
// THE CREAM: a soft-serve swirl, each coil leaning out at most 30 deg from
// upright, piled high enough to cover the room's cone everywhere
CRM = [[17.6, 60.6], [18.4, 62.2], [18.0, 63.4], [15.2, 65.6], [16.0, 67.0], [15.6, 68.2], [12.6, 70.6], [13.2, 71.9],
       [12.8, 73.0], [9.8, 75.6], [10.3, 76.8], [9.8, 77.9], [6.8, 80.5], [7.0, 81.6], [6.4, 82.6], [3.6, 85.0],
       [3.2, 86.4], [1.6, 88.0], [0, 88.6]];
module cream() rotate_extrude($fn = FNC) polygon(concat([[0, 59], [17.6, 59]], CRM));
// toasted marshmallows floating on the cocoa round the cream, sunk 0.8
MM = [[40, 20.6, 20], [125, 20.4, 55], [200, 20.8, 10], [300, 20.6, 35]];
module marshmallows() for (m = MM) rotate(m[0]) translate([m[1], 0, cocoa_z - 0.8]) rotate(m[2]) translate([-1.9, -1.9, 0]) cube([3.8, 3.8, 3.4]);
// THE STIRRER: a candy-cane rod out of the cream, leaning out from 18 deg to 40,
// the most a rod can lean and print over nothing (the chapel's crook)
st_th = 60;                 // which way it leans
st_n = 10;  st_L = 22;
function st_ang(i) = 18 + 22 * pow(i / st_n, 2);
function st_pts(i) = i == 0 ? [0, 0] : let (p = st_pts(i - 1)) [p[0] + st_L / st_n * sin(st_ang(i)), p[1] + st_L / st_n * cos(st_ang(i))];
st_r0 = 7.0;  st_z0 = 76;
module st_at(i) let (p = st_pts(i)) rotate(st_th) translate([st_r0 + p[0], 0, st_z0 + p[1]]) sphere(r = 1.9, $fn = 24);
module stirrer() for (i = [0 : st_n - 1]) hull() { st_at(i); st_at(i + 1); }
module stirrer_stripes() rotate(st_th) for (z = [st_z0 + 1 : 2.6 : st_z0 + st_L + 2])
    translate([st_r0, 0, z]) rotate([0, 28, 0]) cube([20, 20, 1.1], center = true);
// THE HANDLE on the side (world +x): a D whose hole's ceiling and underside
// both rise at more than 50 deg
HDL = [[24, 15.0], [25.5, 13.5], [34.2, 25.6], [35.2, 29.5], [35.2, 44], [33, 50], [25.5, 57.5], [24, 57.5]];
HDL_HOLE = [[25.6, 49.5], [29.8, 44.0], [31.0, 41], [31.0, 32], [29.8, 28.0], [25.6, 23.0]];
module handle() rotate([90, 0, 0]) translate([0, 0, -2.5]) linear_extrude(5) difference() { polygon(HDL); polygon(HDL_HOLE); }

// ---- laid on the mug, flush: red into the white -----------------------------------------
module cplace(r, th, z) translate([r * cos(th), r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
// a flat shape pressed through the wall at angle th: deep enough to reach the
// wall's inside at its ends, then cut to the wall so it sits flush
module press(th, z) intersection() {
    mug_shell();
    cplace(MR, th, z) translate([0, 0, -wall - 3]) linear_extrude(wall + 3.2) children();
}
module stripes() intersection() {
    mug_shell();
    for (z = [11.0, 59.0]) translate([0, 0, z]) cylinder(r = MR + 1, h = 1.6, $fn = FNC);
}
// the windows: red outlines and bars on the white, no openings (the mug is the
// glass); [angle, sill, half-width, straight height]
MW = concat([for (th = [30, 75, 120, 165, 205, 335]) [th, 15, 3.4, 9]],
            [for (th = [35, 85, 135, 185, 215, 325]) [th, 34, 3.4, 8]]);
module mw2d(w) {
    difference() { offset(r = 1.5) polygon(arch_pts(w[2], w[3])); polygon(arch_pts(w[2], w[3])); }
    translate([-0.5, 0]) square([1.0, w[3] + w[2]]);
    translate([-w[2], w[3] * 0.6 - 0.5]) square([2 * w[2], 1.0]);
}
module mug_windows() for (w = MW) press(w[0], w[1]) mw2d(w);
module cocoa_text() press(270, 55.8)
    text("COCOA", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);

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
WINDOWS = [[1, 6.5, 13, 4.5, 7, "arch"], [2, -2, 13, 2.6, 7, "arch"], [3, -2, 13, 2.6, 7, "arch"]];
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
// THE AWNING over the display window: a wedge whose underside rises at 50
// deg from the wall, striped red and white
aw_u = 6.5;  aw_L = 17;  aw_d = 4.5;
aw_z0 = 27.9;                                    // its foot on the wall, over the window's frame
aw_z1 = aw_z0 + aw_d * tan(50);                  // its valance's foot
aw_z2 = aw_z1 + 1.6;
aw_z3 = aw_z2 + aw_d * tan(20);                  // its top on the wall
module awning() nf(1, aw_u, 0) hull() {
    translate([-aw_L / 2, aw_z0, -0.5]) cube([aw_L, aw_z3 - aw_z0, 0.5]);
    translate([-aw_L / 2, aw_z1, aw_d - 0.01]) cube([aw_L, aw_z2 - aw_z1, 0.01]);
}
module awning_stripes() intersection() {
    awning();
    nf(1, aw_u, 0) for (i = [-4 : 4]) translate([i * 2.2 - 0.55, 0, -5]) cube([1.1, 60, 20]);
}
// a piped heart in the gable
module heart2d() { for (s = [-1, 1]) translate([s * 1.5, 0]) circle(r = 1.7, $fn = 32); polygon([[-3.1, -0.6], [3.1, -0.6], [0, -4.0]]); }
module heart() nf(1, 0, 42.5) relief_up(-0.4, 0.9) heart2d();
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
module footprint() { circle(r = MR, $fn = FNC); translate([-Wh, SYc - Dh]) square([W, D]); }
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
module room() { mug_room(); at_shop() shop_room(); }
module body_raw() {
    difference() { at_shop() walls_solid(); mug_cut(); }
    marshmallows();
}
module roof_raw() {
    difference() { cocoa(); mug_room(); }
    difference() { at_shop() union() { slab(); tiles(); } room(); mug_cut(); }
    at_shop() door_leaf();
}
module accent_raw() {
    difference() { stripes(); room(); }
    difference() { mug_windows(); room(); }
    difference() { cocoa_text(); room(); }
    handle();
    at_shop() awning_stripes();
    intersection() { stirrer(); stirrer_stripes(); }
    peppermints(true);
}
module trim_raw() {
    difference() {
        union() {
            base();
            mug_shell();
            cream();
            stirrer();
            difference() {
                at_shop() union() { corner_beads(); eave_flare(); eave_drips(); rakes(); icing_roof(); shop_windows(); door_frame(); awning(); heart(); }
                mug_cut();
            }
            peppermints();
        }
        room();
        brand_mark();
    }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room();
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
