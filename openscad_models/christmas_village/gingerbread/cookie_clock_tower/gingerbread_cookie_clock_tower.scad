// Gingerbread Cookie Clock Tower -- building #6 of the Gingerbread village
// (Scott, 2026-10-02, picked from four: "Stacked cookie tower").
//
// A round gingerbread tower stacked from three thick cookie discs, each with a
// bevelled rim, a band of icing between each pair dripping down the disc
// below. On the front of the tall top disc a big scalloped cookie clock, piped
// round with icing dots: its frosting face carries chocolate hour dots and
// candy-red hands. Frosting round the top, a chocolate cone of shingles with
// red and white gumdrops round its foot, a cap of icing on its point and a
// candy cane rising from it, its crook leaning over. Arched windows framed in
// icing round the discs, a chocolate door at the foot. On a soft blob of snow
// with peppermints.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed. The clock's face is glazed too, so lit it glows; its dots and hands
// run through the frosting glass and show dark against it.
//
// THE TOWER is the gingerbread Santa's workshop's drum (../santas_workshop)
// stacked into discs: its frosting, cone, shingles, gumdrops, windows, drips
// and base, with every fix in its notes. THE DOOR is the toy shop's tower door
// (../../victorian/toy_shop); THE CANE and its crook are the candy cane
// chapel's (../candy_cane_chapel).
//
// COLOUR PARTS, ONE PRINT (gingerbread_cookie_clock_tower.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the cookie discs, the clock's cookie
//   roof    chocolate: the cone and its shingles, the door, the clock's hour dots
//   trim    icing white: snow base and drifts, the icing bands and their drips,
//           the top's frosting and drips, the cone's cap, the window frames,
//           panes and bars, the door's piped frame, the clock's piped dots and
//           its face, the white gumdrops, the cane, the peppermints' white
//   accent  candy red: the clock's hands, the red gumdrops, the cane's
//           stripes, the peppermints' stripes

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// the wall is 2.2: the discs' rims set in 1.0 still leave 1.2 at their feet.
// At 1.68 with rims set in 1.4, the wall there was 0.28 (1st percentile 0.40)
wall     = 2.2;
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
module win_outline(w) polygon(arch_pts(w[3], w[4]));
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, w[4] * 0.6]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }

// =====================================================================================
// THE TOWER: three cookie discs and the icing between them
// =====================================================================================
// 182, not 180 (the workshop): a facet corner exactly at the front met the
// door's strips along it
FNC = 182;
MR  = 26;                   // the discs' face
MRi = MR - wall;            // the room: the 46.6 mm tealight's circle stands 0.5 inside
// [foot, top] of each disc; the icing band sits between, 3.6 tall: at 3 its lip
// over the bevel was 0.6 tall, the gate's thinnest walls
DISCS = [[plinth_h, 24], [27.6, 43.6], [47.2, 81]];
TD  = DISCS[2][1];          // the top disc's top, under the frosting
// each disc's rim: in 1.4 at its foot, out to the face (MR) at 50 deg,
// upright, and (all but the top one) rounded back in 1.4 at its top. The face
// is MR exactly, so the windows, door and clock laid on MR stand proud of it
ri = 1.0;
// the upper discs' feet 0.3 down into the band under them, which takes it (at
// 0.01 the two left open edges)
module disc2d(d, last = false) let (z0 = d[0], z1 = d[1], rt = 1.6, zf = z0 == plinth_h ? z0 - 0.5 : z0 - 0.3,
        top = last ? [[MR, z1 + 0.5]]
                   : [for (i = [0 : 8]) let (q = 90 * i / 8) [MR - ri + ri * cos(q), z1 - rt + rt * sin(q)]])
    polygon(concat([[MRi - 0.3, zf], [MR - ri, zf], [MR, z0 + ri * tan(50)]],
                   top,
                   [[MRi - 0.3, last ? z1 + 0.5 : z1 + 0.01]]));
module discs() rotate_extrude($fn = FNC) {
    for (i = [0 : 2]) disc2d(DISCS[i], i == 2);
    // the core behind the icing bands
    for (i = [0 : 1]) translate([MRi - 0.3, DISCS[i][1]]) square([MR - ri - MRi + 0.3, DISCS[i + 1][0] - DISCS[i][1]]);
}
// THE ICING BANDS: in from the core, out to 0.7 proud at 50 deg, flat on top
// for the next disc's foot
module bands() rotate_extrude($fn = FNC) for (i = [0 : 1]) let (z0 = DISCS[i][1], z1 = DISCS[i + 1][0])
    // its bevel starting 0.25 under the disc's top, inside its rounding: from
    // the very point where the rounding ends, the two shared an edge ring and
    // the drips under it left open edges
    polygon([[MR - ri - 0.4, z0 - 0.25], [MR - ri - 0.3, z0 - 0.25], [MR + 0.7, z0 - 0.25 + (ri + 1.0) * tan(50)], [MR + 0.7, z1], [MR - ri - 0.4, z1]]);

// the room keeps its full width to za, then closes in at 55 deg under the cone
za  = TD - 1.6;
module tower_room() rotate_extrude($fn = FNC) polygon([[0, -2], [MRi, -2], [MRi, za], [0, za + MRi * tp55]]);

// THE FROSTING on the top: its edge 0.9 proud, its underside at 50 deg (the workshop's)
module frosting() rotate_extrude($fn = FNC)
    polygon([[MR - 2.0, TD - 0.5], [MR - 0.6, TD - 0.5], [MR - 0.6, TD - 2.5], [MR + 0.9, TD - 0.7], [MR + 0.9, TD + 0.3], [MR + 0.4, TD + 0.9], [MR - 2.0, TD + 0.9]]);

// THE CONE (the workshop's), from just inside the frosting's edge up at 55 deg
cr0 = MR - 0.3;
cz0 = TD + 0.9;
function z_co(r) = cz0 + (cr0 - r) * tp55;
c_apex = z_co(0);
module cone() rotate_extrude($fn = FNC) polygon([[0, TD - 1], [cr0, TD - 1], [cr0, cz0], [0, c_apex]]);
sh_c = 2.6;
module course_band(x0, x1) polygon([[x0, z_co(x0) - 1.0], [x0, z_co(x0) + 1.0], [x1, z_co(x1) + 0.3], [x1, z_co(x1) - 1.0]]);
module shingles() {
    nk = ceil((cr0 - 7.2) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = cr0 - k * sh_c, x1 = max(cr0 - (k + 1) * sh_c - 0.5, 7.2))
        if (x0 > x1 + 0.3) rotate_extrude($fn = FNC) course_band(x0, x1);
}
function wave(t) = 1.2 * sin(t * 3.0) + 0.8 * sin(t * 7.0 + 60);
module cone_cap() intersection() {
    rotate_extrude($fn = FNC) polygon([[0, z_co(0) - 0.7], [8, z_co(8) - 0.7], [8, z_co(8) + 1.8], [2, z_co(2) + 2.2], [0, z_co(0) + 2.4]]);
    translate([0, 0, TD]) linear_extrude(60) polygon([for (i = [0 : 179]) let (a = 2 * i) (6.6 + wave(a)) * [cos(a), sin(a)]]);
}
module gumdrop(r) rotate_extrude($fn = 32) polygon(concat([[0, -r * 1.2], [r, 0], [r, 0.45 * r]],
    [for (i = [1 : 8]) let (q = 90 * i / 8) [r * cos(q), 0.45 * r + r * sin(q)]]));
GD = [for (i = [0 : 23]) [15 * i + 7.5, i % 2 == 0]];
gd_r = 1.9;
module gumdrops_ring(red) for (g = GD) if (g[1] == red) rotate(g[0]) translate([MR - 0.2, 0, cz0 - 0.15]) gumdrop(gd_r);

// THE CANE (the chapel's crook) from the cap: a white rod up out of the point,
// bending over sideways to 40 deg at its end; red stripes across it
cn_z0 = z_co(0) + 1.2;
cn_h  = 8;
cr_n = 12;  cr_L = 11;
function cr_ang(i) = 40 * pow(i / cr_n, 2);
function cr_pts(i) = i == 0 ? [0, 0] : let (p = cr_pts(i - 1)) [p[0] + cr_L / cr_n * sin(cr_ang(i)), p[1] + cr_L / cr_n * cos(cr_ang(i))];
function cr_r(i) = 1.9 - 0.5 * i / cr_n;
cr_z0 = cn_z0 + cn_h;
module cr_at(i) let (p = cr_pts(i)) translate([p[0], 0, cr_z0 + p[1]]) sphere(r = cr_r(i), $fn = 24);
module cane() {
    translate([0, 0, z_co(0) - 3]) cylinder(r = 1.9, h = cn_z0 + cn_h - z_co(0) + 3, $fn = 24);
    for (i = [0 : cr_n - 1]) hull() { cr_at(i); cr_at(i + 1); }
}
module cane_stripes() intersection() {
    cane();
    for (z = [cn_z0 + 1.0 : 2.4 : cr_z0 + cr_L + 2]) translate([0, 0, z]) rotate([0, -28, 0]) cube([20, 20, 1.0], center = true);
}

// ---- laid round the wall in strips ------------------------------------------------------------
module cplace(r, th, z) translate([r * cos(th), r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module cyl_relief(r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module cclip(r, d) intersection() { children(); cylinder(r = r + d, h = 300, $fn = FNC); }

// THE WINDOWS: [angle, sill, a, straight height]; 270 is the front
// each frame wholly on its disc's upright face, between the foot's bevel and
// the top's rounding: its sill starting on the bevel (the middle disc's at
// 28.2), the sill's foot stood one layer out over the band and the slicer
// propped it; its head in the rounding, the two met in walls under 0.5 mm
CW = concat([for (th = [30, 150, 210, 330]) [th, 12.8, 3.2, 3.6]],
            [for (th = [0, 90, 180, 225, 315]) [th, 32.4, 3.2, 3.6]],
            [for (th = [20, 90, 160]) [th, 56, 3.2, 8]]);
function cw(w) = [0, 0, 0, w[2], w[3]];
function cframe_U(w) = w[2] + 3.2;
module cframe2d(w) {
    offset(r = 2.4) win_outline(w);
    translate([-w[3] - 2.4, -3.4]) square([2 * w[3] + 4.8, 3.6]);
}
// the series' relief from 0.4 in, and behind it a plain plate 1.2 into the
// wall for where a disc's rim is set in. Sheared from 1.2 in, each frame's
// opening rose 2.2 by its face, more than the frame is wide, and every head
// came to a knife edge
module back_plate(z0) translate([0, 0, z0]) linear_extrude(-0.4 - z0 + 0.01) children();
module c_frames() for (w = CW) cclip(MR, 1.0) cyl_relief(MR, w[0], w[1], cframe_U(w)) {
    relief_up(-0.4, 0.6) { cframe2d(cw(w)); offset(r = 0.3) win_outline(cw(w)); }
    back_plate(-1.2) difference() { cframe2d(cw(w)); offset(r = 0.3) win_outline(cw(w)); }
}
module c_bars() for (w = CW) cclip(MR, 0.4) cyl_relief(MR, w[0], w[1], w[2] + 1) relief_up(-0.4, 0.4) win_muntins(cw(w), 0.6);
module c_glass() for (w = CW) intersection() {
    cplace(MR, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) win_outline(cw(w));
    cylinder(r = MR - 0.2, h = 300, $fn = FNC);
}
module c_openings() for (w = CW) cyl_relief(MR, w[0], w[1], w[2] + 1)
    translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(cw(w));
module c_holes() for (w = CW) cyl_relief(MR, w[0], w[1], cframe_U(w))
    relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(cw(w));

// THE CLOCK on the front of the top disc: a scalloped cookie raised 1.6, piped
// round with icing dots; its face the frosting glass in the wall, its hour dots
// and hands running right through it, every line and gap 0.8 or more
ck_th = 270;
ck_z  = 63.2;              // the cookie's top under the frosting's underside
ck_r  = 10;                 // the face: the cookie round it 4 wide, more than its opening rises
ck_R  = 14.0;               // the cookie, to its scallops' roots: 15.5 to their tips
module cookie2d() {
    circle(r = ck_R, $fn = 96);
    for (i = [0 : 17]) rotate(20 * i) translate([ck_R, 0]) circle(r = 1.5, $fn = 24);
}
// its back 1.2 into the wall: its lowest scallops sit on the disc's foot, where
// the rim is set in
module ck_cookie() cclip(MR, 1.6) cyl_relief(MR, ck_th, ck_z, ck_R + 1.6) {
    relief_up(-0.4, 1.6) { cookie2d(); offset(r = 0.3) circle(r = ck_r, $fn = 96); }
    back_plate(-1.2) difference() { cookie2d(); offset(r = 0.3) circle(r = ck_r, $fn = 96); }
}
// each dot placed on its own, square to the wall where it sits: laid in the
// cookie's strips, or in strips of their own, the dots met the cookie on
// shared strip planes and left open edges
ck_br = ck_r + 3.0;
module ck_beads() cclip(MR, 2.4) for (i = [0 : 23]) let (q = 15 * i, u = ck_br * cos(q), v = ck_br * sin(q))
    cplace(MR, ck_th + u / MR * 180 / PI, ck_z + v) relief_up(-0.4, 2.4) circle(r = 0.8, $fn = 20);
module ck_opening() cyl_relief(MR, ck_th, ck_z, ck_r + 1) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) circle(r = ck_r, $fn = 96);
module ck_hole() cyl_relief(MR, ck_th, ck_z, ck_r + 1.8) relief_hole(-0.4, -0.2, 2.4 + 2.4) offset(r = 0.4) circle(r = ck_r, $fn = 96);
module ck_glass() intersection() {
    cyl_relief(MR, ck_th, ck_z, ck_r + 1.2) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) circle(r = ck_r, $fn = 96);
    cylinder(r = MR - 0.2, h = 300, $fn = FNC);
}
module seg2(a, b, w) hull() { translate(a) circle(d = w, $fn = 12); translate(b) circle(d = w, $fn = 12); }
module ck_dots2d() for (i = [0 : 11]) rotate(90 - 30 * i) translate([7.6, 0]) circle(r = i % 3 == 0 ? 1.2 : 0.85, $fn = 20);
module ck_hands2d() {
    seg2([0, 0], 4.2 * [cos(150), sin(150)], 1.6);     // hour hand, to 10
    seg2([0, 0], 5.2 * [cos(30), sin(30)], 1.2);       // minute hand, to 2
    circle(r = 1.4, $fn = 24);
}
module ck_inlay() intersection() {
    cyl_relief(MR, ck_th, ck_z, ck_r + 1.2) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) children();
    cylinder(r = MR - 0.2, h = 300, $fn = FNC);
}

// THE DOOR at the front of the bottom disc (the toy shop's tower door), framed
// in piped icing
dr_a = 5.0;  dr_h = 7.4;
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() difference() {
    intersection() {
        cplace(MR, ck_th, plinth_h) translate([0, 0, -wall - 1]) linear_extrude(wall + 2)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(dr_a, dr_h + 0.3));
        difference() { cylinder(r = MR + 0.2, h = 100, $fn = FNC); translate([0, 0, -1]) cylinder(r = MRi + 0.15, h = 102, $fn = FNC); }
    }
    cyl_relief(MR + 0.2, ck_th, plinth_h, dr_a + 0.6) translate([0, 0, -0.3]) linear_extrude(2) {
        panel2d(-3.6, -0.7, 1.4, 5.0);  panel2d(0.7, 3.6, 1.4, 5.0);
    }
}
module door_opening() cplace(MR, ck_th, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(arch_pts(dr_a, dr_h));
module door_hole() cyl_relief(MR, ck_th, plinth_h, dr_a + 2.4) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(dr_a, dr_h));
module door_frame2d() union() {
    intersection() { offset(r = fr_w) polygon(arch_pts(dr_a, dr_h)); translate([-30, -0.5]) square([60, 100]); }
    intersection() { beads(arch_path(dr_a, dr_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
}
module door_hole2d() translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(dr_a, dr_h + 1));
module door_frame() cclip(MR, fr_t + 0.6) cyl_relief(MR, ck_th, plinth_h, dr_a + 3.4) {
    relief_up(-0.4, fr_t) { door_frame2d(); door_hole2d(); }
    back_plate(-1.2) difference() { door_frame2d(); door_hole2d(); }
}

// DRIPS off the bands and the frosting, clear of every window's head, the
// door and the clock
function ang_d(a, b) = abs((a - b + 540) % 360 - 180);
function dr_ok(th, zt) = ang_d(th, ck_th) > (zt > 60 ? 38 : 16)
    && len([for (w = CW) if (abs(w[1] + w[3] + w[2] + 4 - zt) < 8 && ang_d(th, w[0]) < 16) 1]) == 0;
DRIP_Z = [DISCS[0][1], DISCS[1][1], TD - 0.7];
DRIPS = [for (k = [0 : 2], i = [0 : 35]) let (th = 360 * i / 36 + 5 * k, zt = DRIP_Z[k]) if (dr_ok(th, zt))
            [th, zt, 1.4 + 3.0 * rnd(i, 70 + k), 2.0 + 0.5 * rnd(i, 90 + k)]];
// their backs 1.6 into the wall, behind the discs' rounded tops
module drips() for (d = DRIPS) cclip(MR, 1.2) cyl_relief(MR, d[0], d[1], 1.6) relief_up(-1.6, 1.2) drip2d(d[2] + 1.2, d[3]);

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module base2d() offset(r = 7.5, $fn = 48) circle(r = MR, $fn = FNC);
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[(MR + 1) * cos(-20), (MR + 1) * sin(-20), 7, 4, 3.0], [(MR + 1) * cos(110), (MR + 1) * sin(110), 7, 3.5, 2.8],
          [(MR + 1) * cos(200), (MR + 1) * sin(200), 5, 3.5, 2.4]];
// on the base's flat top: further out they hung over its rounded edge
PM = [[-12, -26.8, 2.2], [13, -26.4, 2.0], [28, 8, 2.2]];
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
// under the door, between the room's opening (-23.8) and the base's edge (-33.5)
module brand_mark() translate([0, -28.6, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() tower_room();
module body_raw() {
    discs();
    ck_cookie();
}
module roof_raw() {
    difference() { union() { cone(); shingles(); } room(); }
    door_leaf();
    // stopped at the room, like the glass: 0.6 into it, their lower edges hung
    // there and the slicer propped them from the table
    difference() { ck_inlay() ck_dots2d(); room(); }
}
module accent_raw() {
    gumdrops_ring(true);
    cane_stripes();
    difference() { ck_inlay() ck_hands2d(); room(); }
    peppermints(true);
}
module trim_raw() {
    difference() {
        union() {
            base();
            bands();
            frosting();
            drips();
            cone_cap();
            gumdrops_ring(false);
            cane();
            c_frames();
            c_bars();
            door_frame();
            ck_beads();
            peppermints();
        }
        room();
        brand_mark();
    }
    difference() { union() { c_glass(); ck_glass(); } room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room();
        c_openings(); c_holes();
        ck_opening(); ck_hole();
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
else if (part == "all") {
    color("#C68642") body_part();
    color("#5A3825") roof_part();
    color("#F7F3EE") trim_part();
    color("#D7263D") accent_part();
}
