// Gingerbread Santa's Workshop -- building #5 of the Gingerbread village
// (Scott, 2026-10-01, picked from four: "Roundhouse workshop").
//
// A round gingerbread workshop: a tall drum with arched windows on two levels
// framed in icing, a frosted ledge dripping down its wall, and a steep
// chocolate cone of shingles over it, gumdrops all round its foot and a cap of
// icing with a big gumdrop on the point. Out of its front stands a square
// gingerbread loading wing under a chocolate gable of scallop tiles and icing,
// gumdrops along its ridge, big chocolate-bar double doors framed in piped
// beads and a round window in its gable framed like a peppermint. Up its back
// a tall round chimney striped like a peppermint, a smoking flue at its top.
// On a soft blob of snow with peppermints.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane. The wing opens into the drum through
// its own room, so the one light fills both.
//
// THE DRUM is the sweet shop's bottom tier (../sweet_shop) and THE WING its
// shop (the candy cane chapel's nave), each with its WHY comments there. The
// cone, gumdrops and chimney are new.
//
// COLOUR PARTS, ONE PRINT (gingerbread_santas_workshop.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the drum, the wing's walls
//   roof    chocolate: the cone and its shingles, the wing's roof and its
//           tiles, the doors
//   trim    icing white: snow base and drifts, the frosting and its drips, the
//           cone's cap, every frame with its beads, panes and bars, the wing's
//           corner beads, eaves, rake and roof icing, the chimney, the white
//           gumdrops, the peppermints' white
//   accent  candy red: the red gumdrops, the chimney's and the porthole's
//           stripes, the peppermints' stripes

include <BOSL2/std.scad>
include <../../relief_lib.scad>

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
// THE DRUM, round the origin
// =====================================================================================
// 182, not 180: with a facet corner exactly at the front (270 deg), the wing's
// ceiling ridge met the drum along it in an edge shared by four faces
FNC = 182;
MR  = 25.5;                 // the 46 mm tealight's circle stands 0.5 inside its wall
MRi = MR - wall;
TD  = 51.5;                 // its top, under the frosting
// the room keeps its full width to 49.9, then closes in at 55 deg under the
// cone, 4.4 under its outside all the way up: the circle's edge has 50.6
za  = 49.9;
module drum() translate([0, 0, plinth_h - 0.5]) cylinder(r = MR, h = TD - plinth_h + 0.5, $fn = FNC);
module drum_cut() translate([0, 0, -1]) cylinder(r = MR - 0.3, h = 300, $fn = FNC);
module drum_room() rotate_extrude($fn = FNC) polygon([[0, -2], [MRi, -2], [MRi, za], [0, za + MRi * tp55]]);

// THE FROSTING on the drum's top: its edge 0.9 proud, its underside at 50 deg
// into the wall (the sweet shop's ledges)
module frosting() rotate_extrude($fn = FNC)
    polygon([[MR - 2.0, TD - 0.5], [MR - 0.6, TD - 0.5], [MR - 0.6, TD - 2.5], [MR + 0.9, TD - 0.7], [MR + 0.9, TD + 0.3], [MR + 0.4, TD + 0.9], [MR - 2.0, TD + 0.9]]);

// THE CONE, from just inside the frosting's edge up at 55 deg, in shingle courses
cr0 = MR - 0.3;
cz0 = TD + 0.9;
function z_co(r) = cz0 + (cr0 - r) * tp55;
c_apex = z_co(0);
module cone() rotate_extrude($fn = FNC) polygon([[0, TD - 1], [cr0, TD - 1], [cr0, cz0], [0, c_apex]]);
sh_c = 2.6;
// each course's lower edge stands 1.0 proud on an upright face
// its upper end 0.3 over the cone, not 0.05: the feather edge met the cone in
// edges shared by more than two faces
module course_band(x0, x1) polygon([[x0, z_co(x0) - 1.0], [x0, z_co(x0) + 1.0], [x1, z_co(x1) + 0.3], [x1, z_co(x1) - 1.0]]);
module shingles() {
    nk = ceil((cr0 - 7.2) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = cr0 - k * sh_c, x1 = max(cr0 - (k + 1) * sh_c - 0.5, 7.2))
        if (x0 > x1 + 0.3) rotate_extrude($fn = FNC) course_band(x0, x1);
}
// a cap of icing on the point, its edge wandering round
function wave(t) = 1.2 * sin(t * 3.0) + 0.8 * sin(t * 7.0 + 60);
module cone_cap() intersection() {
    // its underside 0.7 into the cone, not 1.0 where the shingles' undersides are
    rotate_extrude($fn = FNC) polygon([[0, z_co(0) - 0.7], [8, z_co(8) - 0.7], [8, z_co(8) + 1.8], [2, z_co(2) + 2.2], [0, z_co(0) + 2.4]]);
    translate([0, 0, TD]) linear_extrude(60) polygon([for (i = [0 : 179]) let (a = 2 * i) (6.6 + wave(a)) * [cos(a), sin(a)]]);
}

// GUMDROPS: a dome on a short drum, and under it a cone at 50 deg that sinks
// into whatever it stands on, so no part of it is a flat underside over air
module gumdrop(r) rotate_extrude($fn = 32) polygon(concat([[0, -r * 1.2], [r, 0], [r, 0.45 * r]],
    [for (i = [1 : 8]) let (q = 90 * i / 8) [r * cos(q), 0.45 * r + r * sin(q)]]));
// round the cone's foot on the frosting, red and white in turn, clear of the
// chimney; [angle, red?]
CH_TH = 60;                 // the chimney's angle round the drum
GD = [for (i = [0 : 23]) let (th = 15 * i + 7.5) if (abs(th - CH_TH) > 14) [th, i % 2 == 0]];
gd_r = 1.9;
// their centres over the wall: at 0.3 out, each one's point hung 0.3 under the
// frosting's edge and the slicer propped all 22
// and 0.15 down: standing exactly on the frosting's top, each met it in a ring
// of edges shared by more than two faces
module gumdrops_ring(red) for (g = GD) if (g[1] == red) rotate(g[0]) translate([MR - 0.2, 0, cz0 - 0.15]) gumdrop(gd_r);
module apex_gumdrop() translate([0, 0, z_co(0) + 1.4]) gumdrop(3.0);

// ---- the drum's windows, laid round it in strips (the sweet shop's cake) -----------------------
module cplace(r, th, z) translate([r * cos(th), r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module cclip(r, d) intersection() { children(); cylinder(r = r + d, h = 300, $fn = FNC); }
// [angle, sill, a, straight height]; 270 is the front, where the wing stands
CW = concat([for (th = [20, 105, 150, 195, 340]) [th, 15, 3.4, 9]],
            [for (th = [0, 90, 130, 170, 210, 330]) [th, 34, 3.4, 8]]);
function cw(w) = [0, 0, 0, w[2], w[3], "arch"];
function cframe_U(w) = w[2] + 3.2;
module cframe2d(w) {
    offset(r = 2.4) win_outline(w);
    translate([-w[3] - 2.4, -3.4]) square([2 * w[3] + 4.8, 3.6]);
}
module c_frames() for (w = CW) cclip(MR, 1.0) cyl_relief(MR, w[0], w[1], cframe_U(w))
    relief_up(-0.4, 0.6) { cframe2d(cw(w)); offset(r = 0.3) win_outline(cw(w)); }
module c_bars() for (w = CW) cclip(MR, 0.4) cyl_relief(MR, w[0], w[1], w[2] + 1) relief_up(-0.4, 0.4) win_muntins(cw(w), 0.6);
module c_glass() for (w = CW) intersection() {
    cplace(MR, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(cw(w));
    cylinder(r = MR - 0.2, h = 300, $fn = FNC);
}
module c_openings() for (w = CW) cyl_relief(MR, w[0], w[1], w[2] + 1)
    translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(cw(w));
module c_holes() for (w = CW) cyl_relief(MR, w[0], w[1], cframe_U(w))
    relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(cw(w));
// DRIPS off the frosting, clear of the upper windows' heads, the wing's roof
// and the chimney
function ang_d(a, b) = abs((a - b + 540) % 360 - 180);
function dr_ok(th) = ang_d(th, 270) > 40 && ang_d(th, CH_TH) > 14
                     && len([for (w = CW) if (w[1] == 34 && ang_d(th, w[0]) < 16) 1]) == 0;
DRIPS = [for (i = [0 : 43]) let (th = 360 * i / 44) if (dr_ok(th)) [th, 1.4 + 3.4 * rnd(i, 70), 2.0 + 0.5 * rnd(i, 90)]];
module drips() for (d = DRIPS) cclip(MR, 1.2) cyl_relief(MR, d[0], TD - 2.6, 1.6) relief_up(-0.4, 1.2) drip2d(d[1] + 1.2, d[2]);

// ---- THE CHIMNEY up the drum's back, striped like a peppermint --------------------------------
ch_r = 4.6;
CHC  = (MR + 2.6) * [cos(CH_TH), sin(CH_TH)];
ch_top = 84;
module chimney() translate([CHC[0], CHC[1], 0]) difference() {
    union() {
        translate([0, 0, plinth_h - 0.5]) cylinder(r = ch_r, h = ch_top - plinth_h + 0.5, $fn = 64);
        // its crown flaring out at 58 deg: at 45 the slicer propped it
        translate([0, 0, ch_top - 1.6]) cylinder(r1 = ch_r, r2 = ch_r + 1.0, h = 1.6, $fn = 64);
        translate([0, 0, ch_top]) cylinder(r = ch_r + 1.0, h = 1.6, $fn = 64);
    }
    translate([0, 0, ch_top - 4]) cylinder(r = 2.4, h = 10, $fn = 48);
}
// two red stripes winding up it, flush, a turn every 30 mm
ch_pitch = 30;
module chimney_stripes() translate([CHC[0], CHC[1], 0]) intersection() {
    difference() { cylinder(r = ch_r + 0.01, h = ch_top - 1.2, $fn = 64); translate([0, 0, -1]) cylinder(r = ch_r - 0.6, h = 200, $fn = 64); }
    translate([0, 0, plinth_h]) linear_extrude(ch_top - plinth_h, twist = -360 * (ch_top - plinth_h) / ch_pitch, slices = 120, $fn = 64)
        // ring sectors clear of the axis: drawn as triangles from it, the twist
        // made a degenerate solid that CGAL dropped, and the chimney came out white
        for (s = [0, 180]) rotate(s) polygon([[3, 0], [8, 0], [8 * cos(50), 8 * sin(50)], [3 * cos(50), 3 * sin(50)]]);
}

// =====================================================================================
// THE WING: the sweet shop's shop (the chapel's nave), in its own frame
// =====================================================================================
SYc      = -25;             // its centre: front face at y -36, its back end inside the drum
module at_shop() translate([0, SYc, 0]) children();
// 32 wide: at 36 its ridge rose past the drum's frosting
W        = 32;
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
        polygon([[Wh - 1.1, zf0 - 1.1 * tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1.1, z_ceil(Wh - 1.1) + 0.3]]);
}
module walls_solid() {
    intersection() {
        translate([0, 0, plinth_h - 0.5]) linear_extrude(200) rect([W, D], rounding = corner_r);
        // the walls' top 0.3 up into the roof slab, which takes it: drawn on the
        // same plane as the slab's underside, the two met in zero-thick sheets
        union() { translate([0, 0, 0.3]) below_ceil(); gable_keep(); }
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

// [face, u, z, a, straight height, kind]: a round window in the front gable,
// framed like a peppermint, and a window in each side
WINDOWS = [[1, 0, 33.5, 3.0, 0, "round"], [2, -2, 13, 2.6, 7, "arch"], [3, -2, 13, 2.6, 7, "arch"]];
module shop_frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module shop_openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) win_outline(w);
module shop_windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    frame_relief(w);
    relief_up(-0.4, 0.4) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
// the porthole's frame striped red, flush in it
module porthole_stripes() let (w = WINDOWS[0]) intersection() {
    nf(w[0], w[1], w[2]) frame_relief(w);
    nf(w[0], w[1], w[2]) translate([0, w[3], -3]) linear_extrude(6) pepper_wedges(w[3] + 3);
}
// THE DOORS: two chocolate bars, scored into squares, under a round head
door_a = 6.0;  door_h = 12;
module door_leaf() nf(1, 0, plinth_h) difference() {
    // the wall's depth only (the cafe's door): deeper, its foot hung over the open base
    translate([0, 0, -wall]) linear_extrude(wall + 0.2) translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
    // the gap between the leaves, and grooves scoring each into squares, their
    // upper faces leaning 50 deg
    translate([-0.5, -1, -0.1]) cube([1, door_h + door_a + 4, 1]);
    for (xg = [-3.2, 3.2]) translate([xg - 0.3, -1, 0.0]) cube([0.6, door_h + door_a + 4, 1]);
    for (zg = [3.4, 6.8, 10.2, 13.6]) hull() {
        translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
        translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
    }
}
module door_opening() nf(1, 0, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(door_a, door_h));
module door_hole() nf(1, 0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
module door_frame() nf(1, 0, plinth_h) relief_up(-0.4, fr_t) {
    union() {
        intersection() { offset(r = fr_w) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
        intersection() { beads(arch_path(door_a, door_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
    }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
// gumdrops along the ridge, on the icing's crest, red and white in turn
RG = [[-8.6, true], [-4.8, false], [-1.0, true]];
module ridge_gumdrops(red) for (g = RG) if (g[1] == red) translate([0, g[0], ic_zc + ic_rc - 0.3]) gumdrop(1.7);

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
module footprint() {
    circle(r = MR, $fn = FNC);
    translate([-Wh, SYc - Dh]) square([W, D]);
    translate(CHC) circle(r = ch_r, $fn = 64);
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 8, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[-26, 8, 4, 7, 3.0], [26, -8, 4, 6, 2.6], [-8, 26, 7, 4, 2.8], [-22, -18, 5, 4, 2.4]];
// on the base's flat top: further out they hung over its rounded edge
PM = [[-12, SYc - Dh - 2.8, 2.2], [13, SYc - Dh - 2.8, 2.0], [-28.5, -6, 2.2]];
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
// under the wing's doors, between its wall and the base's edge, mirrored to
// read with the workshop turned over, front toward you
module brand_mark() translate([0, SYc - Dh - 3.8, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() { drum_room(); at_shop() shop_room(); }
module body_raw() {
    drum();
    difference() { at_shop() walls_solid(); drum_cut(); }
}
module roof_raw() {
    difference() { union() { cone(); shingles(); } room(); }
    difference() { at_shop() union() { slab(); tiles(); } room(); drum_cut(); }
    at_shop() door_leaf();
}

// ---- RELIEF FOR A ONE-COLOUR PRINT (2026-10-08) -------------------------------------------------
// The chimney's, the porthole's and the peppermints' stripes were colour
// alone, flush: a white print lost them. Each now stands out 0.3 in 0.15
// steps, its lower edge climbing SH per 1 out, so nothing hangs.
module ch_twist(dz) translate([0, 0, plinth_h + dz]) linear_extrude(ch_top - plinth_h, twist = -360 * (ch_top - plinth_h) / ch_pitch, slices = 120, $fn = 64)
    for (s = [0, 180]) rotate(s) polygon([[3, 0], [8, 0], [8 * cos(50), 8 * sin(50)], [3 * cos(50), 3 * sin(50)]]);
// up to the crown's flare, which takes the stripes' tops
module chimney_stripes_up() translate([CHC[0], CHC[1], 0]) for (k = [0 : 1]) intersection() {
    difference() {
        cylinder(r = ch_r + (k + 1) * 0.15, h = ch_top - 1.6, $fn = 64);
        translate([0, 0, -1]) cylinder(r = ch_r + k * 0.15 - 0.01, h = 200, $fn = 64);
    }
    ch_twist(0);
    // shifting the twist up turns it as well as lifting it; along the band's
    // lower edge both carry the edge up, by SH times the step or more
    ch_twist(SH * (k + 1) * 0.15);
}
// on the frame's flat front, back to where its climb starts (relief_lib)
module porthole_stripes_up() let (w = WINDOWS[0]) nf(w[0], w[1], w[2]) translate([0, 0, fr_t])
    art_out(0.3, 2) intersection() {
        top_face(fr_t + 0.4) translate([0, w[3]]) difference() { circle(r = w[3] + 2.0, $fn = 48); circle(r = w[3] + 0.3); }
        translate([0, w[3]]) pepper_wedges(w[3] + 3);
    }
module pepper_stripes_up() for (p = PM) translate([p[0], p[1], plinth_h + 1.19]) linear_extrude(0.31)
    intersection() { circle(r = p[2] - 0.3); pepper_wedges(p[2]); }

module accent_raw() {
    gumdrops_ring(true);
    apex_gumdrop();
    at_shop() ridge_gumdrops(true);
    // cut back to the room: the chimney sinks 0.33 mm past the drum's inner
    // wall, and the stripes there hung in the room as helical slivers the
    // slicer propped from the table (1,097 support moves, 2026-10-02)
    difference() { chimney_stripes(); room(); }
    at_shop() porthole_stripes();
    peppermints(true);
    difference() { chimney_stripes_up(); room(); }
    at_shop() porthole_stripes_up();
    pepper_stripes_up();
}
module trim_raw() {
    difference() {
        union() {
            base();
            frosting();
            drips();
            cone_cap();
            gumdrops_ring(false);
            at_shop() ridge_gumdrops(false);
            chimney();
            c_frames();
            c_bars();
            difference() {
                at_shop() union() { corner_beads(); eave_flare(); eave_drips(); rakes(); icing_roof(); shop_windows(); door_frame(); }
                drum_cut();
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
        c_openings(); c_holes();
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
