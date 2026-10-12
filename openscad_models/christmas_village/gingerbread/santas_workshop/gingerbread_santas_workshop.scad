// Gingerbread Santa's Workshop -- the village's centrepiece (Scott, 2026-10-11:
// "It needs to be the center piece of the village. It needs to be bigger and
// more magical within the theme." The same shape as the Victorian one, which
// he picked from five: a toy factory that is also a castle.)
//
// A gingerbread hall under three chocolate sawtooth roofs, each tooth's tall
// upright face glazed in icing with three lights, so the roofline glows from
// inside. Four round gingerbread turrets wall its corners, each under a
// frosted ledge and a chocolate cone of shingles with icing and a gumdrop on
// its point. A gatehouse with iced battlements stands out of the front:
// chocolate-bar doors with peppermints, the SANTA'S WORKSHOP sign, a rose
// window. Two candy-cane chimney stacks climb out of the roof as the
// village's tallest points. Seven big arched windows round the hall, each
// with its own scene of toys drawn on the icing glass. A red-and-white
// NORTH POLE stands at the front corner. On a soft blob of snow, gumdrops in it.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed. Each valley between two roof teeth stands on an inside wall, cut
// through by a tall pointed arch so the one light fills all three bays.
//
// THE LAYOUT is the Victorian workshop's (../../victorian/santas_workshop),
// with its WHY comments there; here only the skin differs.
//
// COLOUR PARTS, ONE PRINT (gingerbread_santas_workshop.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the hall, its gables and inside walls, the turrets,
//           the gatehouse
//   roof    chocolate: the roofs and their shingles, the turret cones, the
//           doors, the sign boards, the toys and lines drawn on the glass
//   trim    icing white: snow base and drifts, icing on the roofs, ledges and
//           battlements, every frame, sill, pane and bar, the copings, the
//           drips, the letters, the chimneys, the pole's white stripe and its
//           ball, the white gumdrops and the peppermints' white
//   accent  candy red: the chimneys' and the pole's stripes, the red gumdrops,
//           the peppermints' stripes

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts
include <../../victorian/santas_workshop/toys_lib.scad>
include <../../relief_lib.scad>

$fa = 4;  $fs = 0.4;
part = "all";

wall     = 1.68;
plinth_h = 8;
SH       = 1.2;

// ---- the hall and its sawtooth ------------------------------------------------------------
L = 124;  D = 72;  Lh = L / 2;  Dh = D / 2;
EAVE  = 56;                 // the teeth's low edge
RISE  = 55;                 // each tooth's climb
RIDGE = EAVE + RISE;        // 111
NT    = 3;
// the teeth's runs: the middle one wide enough that a tealight stands in its
// bay with the village's 46 mm circle (48.3 inside), the end two steeper.
// Equal (41.3 each) every bay was 38.7 wide, and the inside walls under the
// valleys cannot open wider than a lancet whose crown stays under the
// valley; a bridged doorway instead printed its lintel's edges over air
// (2026-10-12). Pitches 56.4 / 47.2 / 56.4 deg, so every ceiling prints.
TWS   = [36.5, 51, 36.5];
function xi(i) = i <= 0 ? -Lh : xi(i - 1) + TWS[i - 1];
tr    = 2.5;                // the roof slab, square to its slope
function tvb(i) = tr / cos(atan(RISE / TWS[i]));   // its thickness measured upright
function bay(x) = x < xi(1) ? 0 : x < xi(2) ? 1 : 2;
function z_out(x)  = RIDGE - RISE * (x - xi(bay(x))) / TWS[bay(x)];
function z_ceil(x) = z_out(x) - tvb(bay(x));
// one bay's ceiling, carried past its ends: z_ceil at a valley reads the next bay
function zc_bay(i, x) = RIDGE - RISE * (x - xi(i)) / TWS[i] - tvb(i);
part_w = 1.0;               // the inside wall reaches this far left of its valley

module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// the building's outline seen from the front: three teeth, each rising
// straight up at its left edge and sloping down to the right
function env_pts(dz = 0, ext = 6) = concat(
    [[-Lh - ext, -5], [Lh + ext, -5], [Lh + ext, EAVE + dz]],
    [for (i = [NT - 1 : -1 : 0]) each [[xi(i + 1), EAVE + dz], [xi(i), RIDGE + dz]]],
    [[-Lh - ext, RIDGE + dz]]);
module envelope(dz = 0) xz(-60, 60) polygon(env_pts(dz));

// ---- placing things on a face: local x across it, local y up, local z out --------------------
// 0 front (-y), 1 back (+y), 2 left end (-x), 3 right end (+x), 4 and 5 the
// upright faces of the second and third teeth (looking -x), 6 the gatehouse's front
GH_y = -Dh - 17 + 0.5;      // the gatehouse's front face (GC[1] - GD / 2)
module face_at(f, u, z) {
    ang = [0, 180, -90, 90, -90, -90, 0][f];
    d   = [Dh, Dh, Lh, Lh, -xi(1), -xi(2), -GH_y][f];
    rotate([0, 0, ang]) translate([u, -d, z]) rotate([90, 0, 0]) children();
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

// ---- brick ------------------------------------------------------------------------------------
bd = 0.6;  bp = 2.6;  br = bd * tan(58);
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);
function rpts(w, d, g, z, r = 1.5) = [for (p = rrect_pts(w + 2*g, d + 2*g, r + g, 5)) [p[0], p[1], z]];
// gingerbread is smooth: the old brick box's outline, without its courses
module brick_box(w, d, ztop) translate([0, 0, plinth_h - 0.5]) linear_extrude(ztop + 2.5 - plinth_h)
    polygon(rrect_pts(w, d, 1.5, 5));
function brick_ring(R, ztop) = [[R - wall - 0.3, plinth_h - 0.5], [R, plinth_h - 0.5], [R, ztop], [R - wall - 0.3, ztop]];

// =====================================================================================
// TURRETS at the four corners
// =====================================================================================
TR   = 15;
TURS = [[-1, -1, 122], [1, -1, 122], [-1, 1, 138], [1, 1, 138]];   // [sx, sy, top of the brick]
cb_h = 4.0;                 // the corbel ring under each cone flares out 3 over 4: 37 deg
cb_o = 3.0;
cone_h = 36;  cone_r = TR + cb_o;
function tpos(t) = [t[0] * Lh, t[1] * Dh];
module turret_drum(t) translate(tpos(t)) rotate_extrude($fn = 96) polygon(brick_ring(TR, t[2] - cb_h));
module turret_corbel(t) translate([tpos(t)[0], tpos(t)[1], t[2] - cb_h]) {
    cylinder(r1 = TR, r2 = cone_r, h = cb_h, $fn = 96);
}
module turret_cone(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) cylinder(r1 = cone_r, r2 = 0.6, h = cone_h, $fn = 96);
// slates on the cone (the toy shop's courses): each ring's foot an upright
// face 0.9 high at its outer edge, standing on the ring below, the ring
// sloping back into the cone above it. As a flat step 0.9 proud each foot was
// a ledge and the slicer propped all four cones from the table; chamfered
// instead, every lip was a wedge with air under it (2026-10-12)
function r_cone(h) = cone_r * (1 - h / cone_h);
function z_cone(r) = cone_h * (1 - r / cone_r);
module cone_slates(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) {
    n = 10;  d = cone_r * 0.62 / n;
    rotate_extrude($fn = 96) for (k = [0 : n - 1]) let (ro = cone_r - k * d, ri = ro - d - 0.5)
        polygon([[ro, max(z_cone(ro) - 1.0, 0)], [ro, z_cone(ro) + 0.9], [ri, z_cone(ri) + 0.05], [ri, max(z_cone(ri) - 1.0, 0)]]);   // not below the cone's foot: there it hung past the corbel
}
// icing on the cone's upper third, its foot in waves. The foot is an upright
// face standing on the cone: cut level by a cylinder and bitten from below,
// it was a ledge 1 mm proud all round, and the slicer propped it (2026-10-12).
// One polyhedron: per angle a profile foot -> upright face -> outer face -> top.
sn_A = cone_r + 1.6;  sn_H = cone_h + 1.2;
function r_snow(z) = sn_A * (1 - z / sn_H);
function sn_foot(q, ph) = cone_h * 0.6 + 1.2 + 1.1 * sin(6 * q + ph) + 0.6 * sin(13 * q + 2 * ph);
function z_snow(r) = sn_H * (1 - r / sn_A);
function sn_prof(q, ph) = let (hf = sn_foot(q, ph), rf = r_cone(hf))
    [[rf, hf], [rf, z_snow(rf)], [1.8, sn_H]];
module cone_snow(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) {
    N = 96;  ph = 40 * t[0] + 70 * t[1];
    pts = concat(
        [for (i = [0 : N - 1], p = sn_prof(360 * i / N, ph)) [p[0] * cos(360 * i / N), p[0] * sin(360 * i / N), p[1]]],
        [[0, 0, cone_h * 0.6 - 6], [0, 0, sn_H]]);
    B = 3 * N;  T = B + 1;
    faces = concat(
        [for (i = [0 : N - 1], j = [0 : 1]) let (a = 3 * i + j, b = 3 * ((i + 1) % N) + j) [a, a + 1, b + 1, b]],
        [for (i = [0 : N - 1]) [B, 3 * i, 3 * ((i + 1) % N)]],
        [for (i = [0 : N - 1]) [T, 3 * ((i + 1) % N) + 2, 3 * i + 2]]);
    polyhedron(pts, faces, convexity = 4);
}
// GUMDROPS (the gingerbread workshop's): a dome on a short drum, and under it a
// cone at 50 deg that sinks into whatever it stands on, so nothing hangs
module gumdrop(r) rotate_extrude($fn = 32) polygon(concat([[0, -r * 1.2], [r, 0], [r, 0.45 * r]],
    [for (i = [1 : 8]) let (q = 90 * i / 8) [r * cos(q), 0.45 * r + r * sin(q)]]));
// the pole's ball: a neck flaring 51 deg into a ball's upper half, so nothing hangs
module finial(p, z, r = 2.6) translate([p[0], p[1], z]) {
    // the neck climbs 51 deg: at 45 the gate's slicer propped every ball (2026-10-12)
    hn = (r - 0.9) * 1.25;
    cylinder(r1 = 0.9, r2 = r, h = hn);
    // sunk 0.3 into the neck: standing exactly on it, the ball came out a loose
    // second shell touching it in one face (2026-10-11)
    translate([0, 0, hn - 0.3]) intersection() { sphere(r = r, $fn = 32); translate([-r, -r, 0.3]) cube(2 * r); }
}
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
// drips down each turret under its ledge, clear of the hall
module turret_drips(k) let (t = TURS[k], a0 = atan2(t[1], t[0]))
    for (i = [0 : 13]) let (th = a0 - 105 + 15 * i, p = tpos(t))
        translate([p[0] + TR * cos(th), p[1] + TR * sin(th), t[2] - cb_h + 0.4]) rotate([0, 0, th + 90]) rotate([90, 0, 0])
            relief_up(-0.6, 1.0) drip2d(1.6 + 3.0 * rnd(i + 7 * k, 3), 2.2);
module turret_room(t) translate(tpos(t)) {
    translate([0, 0, -2]) cylinder(r = TR - wall, h = t[2] + 2, $fn = 96);
    // the cone's hollow: as wide as the room under it and parallel to the cone,
    // 4.7 of slate all the way up. Narrower than the room, it left a 0.6 ledge
    // round the top of every turret that the slicer propped (2026-10-12)
    translate([0, 0, t[2] - 0.01]) cylinder(r1 = TR - wall, r2 = 0.01, h = (TR - wall) * cone_h / cone_r, $fn = 96);
}

// =====================================================================================
// THE GATEHOUSE, crenellated, in the middle of the front
// =====================================================================================
GW = 36;  GD = 17;  GH = 86;  GWh = GW / 2;
GC = [0, -Dh - GD / 2 + 0.5];   // its centre
mer_h = 7;  mer_w = 5.2;
module gate_block() translate(GC) brick_box(GW, GD, GH - 2);   // brick_box runs 2 past its top
// merlons round its top: front and sides; the gaps cut square, the merlons'
// faces flush with the courses' roots
// rounded 1.5 like the brick block under it: square, its corners hung past the block's (2026-10-12)
module merlon2d() difference() { offset(r = 1.5, $fn = 24) square([GW - 3, GD - 3], center = true); square([GW - 2 * 3.0, GD - 2 * 3.0], center = true); }
module crenels() {
    for (i = [0 : 2]) translate([-GWh + 6.2 + i * 11.8 - 3.1, -GD / 2 - 1, 3.4]) cube([6.2 - 0.4, 4.2, 10]);
    // the side crenels centred on the 3 mm wall: centred on its outer face they
    // left a 0.9 sliver of merlon on the walk's side (2026-10-12)
    for (s = [-1, 1]) translate([s * (GWh - 1.5) - 2.1, -GD / 2 + 4.6, 3.4]) cube([4.2, 4.6, 10]);
}
module merlons() translate([GC[0], GC[1], GH]) difference() { linear_extrude(mer_h) merlon2d(); crenels(); }
// snow: a cap on each merlon and a layer in each crenel, flush with the stone.
// Widened 0.3 and run straight across the crenels, the caps hung over air
// (2026-10-12)
module merlon_snow() translate([GC[0], GC[1], GH]) {
    difference() { translate([0, 0, mer_h - 0.2]) linear_extrude(1.2) merlon2d(); crenels(); }
    translate([0, 0, 3.2]) linear_extrude(1.0) merlon2d();
}
// its room: up to a pitched ceiling, ridge along y, 49 deg, open into the hall
gi = GWh - wall;
// It stops a wall short of the hall: run 3 into it, its ridge cut up through
// the hall's roof behind the gatehouse and left the gatehouse's back 0.5 thick
// above the hall's eave (2026-10-12). The pointed arch is the way through.
gr_y0 = GH_y + wall;  gr_y1 = -Dh - wall + 0.5;
module gate_room2() translate([GC[0], 0, 0]) intersection() {
    translate([-gi, gr_y0, -2]) cube([2 * gi, gr_y1 - gr_y0, 200]);
    xz(-80, 80) polygon([[-gi - 1, -5], [gi + 1, -5], [gi + 1, GH - 3 - (gi + 1) * 1.15], [0, GH - 3], [-gi - 1, GH - 3 - (gi + 1) * 1.15]]);
}
// the way through from the gatehouse into the hall: a pointed arch
// a lancet: each arc's radius 4x the half-span, its centre across the span,
// so the crown's two slopes meet at 48.6 deg. Equilateral (radius 2x), the
// crown met at 30 deg and the slicer propped it (2026-10-12)
module pointed2d(half, spring, k = 4) {
    R = k * half;  c = R - half;
    translate([-half, -5]) square([2 * half, spring + 5]);
    translate([0, spring]) intersection() {
        translate([c, 0]) circle(r = R, $fn = 192);
        translate([-c, 0]) circle(r = R, $fn = 192);
        translate([-half, 0]) square([2 * half, R]);
    }
}
module gate_way() translate([0, -Dh + wall + 0.5, 0]) rotate([90, 0, 0]) linear_extrude(wall + 2) translate([0, plinth_h]) pointed2d(12, 3, 6);   // crown 50.8, slopes 56 deg: at 48.6 the crown's last layers printed as overhang

// ---- the doors, wreaths, sign and rose window on the gatehouse ---------------------------------
function arch_pts(a, hgt, n = 36) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
dr_a = 8;  dr_h = 11;
module door_outline() polygon(arch_pts(dr_a, dr_h));
module hinges2d() for (s = [-1, 1], z = [3.4, 9.4]) translate([s * (dr_a - 3.4), z]) square([5.6, 1.2], center = true);
module door_leaf() face_at(6, 0, plinth_h) difference() {
    translate([0, 0, -wall]) linear_extrude(wall + bd) translate([0, -0.3]) offset(delta = 0.25) polygon(arch_pts(dr_a, dr_h + 0.3));
    translate([0, 0, bd - 0.5]) linear_extrude(2)
        polygon([[-0.4, -1], [0.4, -1], [0.4, dr_h + dr_a - 3], [0, dr_h + dr_a - 3 + 0.4 * tan(60)], [-0.4, dr_h + dr_a - 3]]);
    // the bar's two upright scores stop short of the arch under pointed tops: run
    // up into it, the white frame hung over their ends (2026-10-12)
    for (xg = [-4.2, 4.2]) let (yt = dr_h + sqrt(dr_a * dr_a - xg * xg) - 1.5) translate([xg, 0, bd - 0.4]) linear_extrude(1)
        polygon([[-0.3, -1], [0.3, -1], [0.3, yt], [0, yt + 0.3 * tan(60)], [-0.3, yt]]);
    for (zg = [3.6, 7.2, 10.8, 14.4]) hull() {
        translate([-dr_a - 1, zg - 0.6, bd - 0.02]) cube([2 * dr_a + 2, 1.2, 0.02]);   // a 0.2 deep mouth left a level lip
        translate([-dr_a - 1, zg - 0.25, bd - 0.7]) cube([2 * dr_a + 2, 0.02, 0.7]);   // root low, so the upper flank climbs 50 deg: at 40 the slicer propped it (2026-10-12)
    }
}
module hinges() ;
module door_opening() face_at(6, 0, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
module door_frame() face_at(6, 0, plinth_h) {
    translate([0, 0, -0.6]) linear_extrude(0.6 + bd) difference() {
        intersection() { offset(r = 1.8) door_outline(); translate([-30, -0.5]) square([60, 100]); }
        door_outline();
    }
    relief_up(-0.4, bd + 0.9) translate([0, dr_h + dr_a - 0.6]) polygon([[-1.3, 0], [1.3, 0], [1.9, 4.0], [-1.9, 4.0]]);
}
wr_z = plinth_h + dr_h + 2.4;
// a peppermint on each leaf: a white disc, red wedges flush in it
module pepper_wedges(r) for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0.5, 0], [r, 0], [r * cos(45), r * sin(45)], [0.5 * cos(45), 0.5 * sin(45)]]);
module pepper_discs() for (s = [-1, 1]) face_at(6, s * 4.0, wr_z) relief_up(-0.2, 0.2 + bd + 0.8) circle(r = 2.7, $fn = 40);
module wreaths() intersection() { pepper_discs(); for (s = [-1, 1]) face_at(6, s * 4.0, wr_z) translate([0, 0, -2]) linear_extrude(6) pepper_wedges(3.0); }
module bow2d() { polygon([[0, 0], [-1.9, 1.0], [-1.9, -1.0]]);  polygon([[0, 0], [1.9, 1.0], [1.9, -1.0]]); circle(r = 0.8); }
module wreath_bows() pepper_discs();
module step() translate([-dr_a - 2.6, GH_y - 1.9, plinth_h - 0.7]) cube([2 * dr_a + 5.2, 2.0, 3.2]);

module letters_up(h, n) for (i = [0 : n - 1]) let (t0 = i == 0 ? -0.3 : i * h / n - 0.01,
        k = ceil(SH * (i + 1) * h / n / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / n - t0) intersection_for(j = [0 : k]) translate([0, j * 0.2]) children();
sg_z = 36.6;  sg_w = 33;  sg_h = 11.4;
module sign_board() face_at(6, 0, sg_z) relief_up(-0.4, 1.0) translate([-sg_w / 2, 0]) offset(r = 1.0) offset(delta = -1.0) square([sg_w, sg_h]);
module sign_text() face_at(6, 0, sg_z + sg_h / 2) translate([0, 0, 1.0]) letters_up(0.84, 5)
    for (l = [["SANTA'S", 2.6], ["WORKSHOP", -2.6]]) translate([0, l[1]])
        text(l[0], size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);

// the rose window: a round pane, its eight spokes and hub drawn on the glass
rose_z = 62;  rose_r = 7.2;
module rose_cut() face_at(6, 0, rose_z) translate([0, 0, -wall - 2]) cylinder(r = rose_r, h = wall + bd + 4, $fn = 64);
module rose_frame() face_at(6, 0, rose_z) relief_up(-0.4, bd + 0.6, 2 * SH) difference() { circle(r = rose_r + 2.4, $fn = 64); circle(r = rose_r - 0.3, $fn = 64); }
module rose_holes() face_at(6, 0, rose_z) relief_hole(-0.4, -0.25, bd + 3, 2 * SH) circle(r = rose_r + 0.1, $fn = 64);
module rose_pane() face_at(6, 0, rose_z) translate([0, 0, -wall]) cylinder(r = rose_r + 0.6, h = wall - 0.2, $fn = 64);
module rose2d() { circle(r = 1.6, $fn = 32); for (i = [0 : 7]) rotate(i * 45 + 22.5) translate([2.8, -tw / 2]) square([rose_r - 2.6, tw]); }
module rose_art() face_at(6, 0, rose_z) {
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) intersection() { circle(r = rose_r + 0.6, $fn = 64); rose2d(); }
    translate([0, 0, -0.2]) art_skirt(0.4, 2) intersection() { circle(r = rose_r - 0.4, $fn = 64); offset(r = 0.2) rose2d(); }
}

// =====================================================================================
// THE BIG TOY WINDOWS: [face, u, sill z, half-width, straight height, scene]
// =====================================================================================
TOYW = [
    [0, -34, 16,  9, 22, 0], [0, 34, 16,  9, 22, 1],
    [1, -34, 16,  9, 22, 2], [1, 0, 16,  9, 22, 3], [1, 34, 16,  9, 22, 4],
    [2,   0, 16, 11, 22, 5], [3,   0, 11, 11, 20, 6],   // the right end's 3 lower: at 14 its head rose into the soffit (2026-10-12)
];
// [floor toys, shelf toys], each [name, x]
SCENES = [
    [[["horse", 0]], [["boat", -4.6], ["soldier", 4.6]]],
    [[["train", 0]], [["jack", -4.4], ["drum", 4.6]]],
    [[["teddy", -4.6], ["drum", 4.6]], [["soldier", -4.6], ["boat", 4.6]]],
    [[["horse", 0]], [["teddy", -4.6], ["jack", 4.4]]],
    [[["train", 0]], [["soldier", -4.6], ["teddy", 4.6]]],
    [[["teddy", -5.6], ["gift", 5.6]], [["boat", -5.6], ["drum", 5.6]]],
    [[["horse", 0]], [["gift", -5.6], ["soldier", 5.6]]],
];
recess = 3.5;  pane_t = 1.48;  sh_r = 1.2;
fr_w = 2.6;  fr_t = bd + 0.6;  sill = 3.4;
module w_outline(w) polygon(arch_pts(w[3], w[4]));
function w_rise(z) = sh_r * (z + recess);
module w_sec2d(w, z) hull() { w_outline(w); translate([0, w_rise(z)]) w_outline(w); }
module slice(z) translate([0, 0, z]) linear_extrude(0.01) children();
w_z1 = fr_t + 0.6;
module w_cut(w) { hull() { slice(-recess) w_outline(w); slice(w_z1) w_sec2d(w, w_z1); } translate([0, 0, w_z1]) linear_extrude(3) w_sec2d(w, w_z1); }
module w_hole(w) face_at(w[0], w[1], w[2]) w_cut(w);
module w_pane(w) face_at(w[0], w[1], w[2]) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) offset(r = 1.0) w_outline(w);
w_cd = recess + pane_t;
module w_collar2d(w) union() {
    offset(r = 2.6) w_sec2d(w, fr_t);
    translate([-w[3] - 2.6, -w[2] + 1]) square([2 * (w[3] + 2.6), w[2] - 1 + w[4]]);
}
module w_collar(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd]) linear_extrude(w_cd - wall + 0.4) w_collar2d(w);
module w_collar_col(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd - 0.01]) linear_extrude(w_cd + 0.02) union() {
    w_collar2d(w);
    translate([-w[3] - 2.6, -w[2] - 3]) square([2 * (w[3] + 2.6), w[2] + w[4]]);
}
function w_ftop(w) = w[4] + w[3] + w_rise(fr_t);
module w_frame(w) face_at(w[0], w[1], w[2]) {
    difference() {
        relief_up(-0.4, fr_t) union() { offset(r = fr_w) w_sec2d(w, fr_t); translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]); }
        w_cut(w);
    }
    difference() {
        relief_up(-0.4, fr_t + 0.5) translate([0, w_ftop(w) - 0.2]) polygon([[-1.6, 0], [1.6, 0], [2.2, fr_w + 2.2], [-2.2, fr_w + 2.2]]);
        w_cut(w);
    }
}
shelf_y = 12.4;  trans_y = 24.0;
module pane_art2d(w) {
    sc = SCENES[w[5]];
    intersection() {
        offset(r = 1.0) w_outline(w);
        union() {
            for (t = sc[0]) translate([t[1], 0.4]) toy(t[0]);
            for (t = sc[1]) translate([t[1], shelf_y + 0.4]) toy(t[0]);
            translate([-30, shelf_y - tw / 2]) square([60, tw]);
            translate([-30, trans_y - tw / 2]) square([60, tw]);
            translate([0, trans_y]) intersection() {
                union() {
                    circle(r = 2.0, $fn = 40);
                    for (i = [1 : 5]) rotate(180 * i / 6) translate([3.2, -tw / 2]) square([30, tw]);
                }
                translate([-40, 0]) square([80, 40]);
            }
        }
    }
}
module w_art(w) face_at(w[0], w[1], w[2]) {
    translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) pane_art2d(w);
    translate([0, 0, -recess]) art_skirt(0.4, 2) offset(r = 0.2) pane_art2d(w);
    translate([0, 0, -recess - pane_t]) art_in(art_d, 4) offset(r = 0.3) pane_art2d(w);
}
// The toys' lines stand art_d out of the back of the pane, so lit from inside
// they show dark on the glow in white plastic too (Scott, 2026-10-12): 3.3 mm
// of plastic on a line against the pane's 1.5. Until then they had never been
// printed at all: the room was cut out of the roof part, which the art is in,
// and it took the 0.8 mm the art stood out with it. w_glow_col keeps the room
// off that space; the lines are 1.4 wide there, over the 1.2 wall floor.
art_d = 1.8;
module w_glow_col(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd - art_d - 1]) linear_extrude(art_d + 1.02)
    hull() { offset(r = 1.3) w_outline(w); translate([0, -SH * art_d - 0.5]) offset(r = 1.3) w_outline(w); }

// =====================================================================================
// THE GLAZED TEETH and the turrets' little windows: segmental, bars on the pane
// [face, u, z, half-width, straight height]
// =====================================================================================
CLER = concat(
    [for (f = [4, 5], u = [-21, 0, 21]) [f, u, EAVE + 7, 5.4, 22]],
    [for (u = [-9.5, 9.5]) [2, u, EAVE + 9, 4.4, 20]]);
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
mull = 1.68;
module s_outline(w) polygon(seg_pts(w[3], w[4]));
module s_bars(w) { translate([-mull / 2, -3]) square([mull, 60]); translate([-20, w[4] * 0.5]) square([40, 2.2]); }
// its head raised by what relief_up's shear takes off it, so the band is fr_w
// deep at its face too: at 1.2 mm it was a wedge the wall check failed (2026-10-12)
module s_frame_outer(w) { hull() { offset(r = fr_w) s_outline(w); translate([0, SH * fr_t]) offset(r = fr_w) s_outline(w); } translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]); }
module s_keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2 + SH * fr_t]) polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
module cler_holes() for (w = CLER) face_at(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) s_outline(w);
module cler_openings() for (w = CLER) face_at(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) s_outline(w);
module cler_windows() for (w = CLER) face_at(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { s_frame_outer(w); offset(r = 0.3) s_outline(w); }
    relief_up(-0.4, fr_t + 0.5) s_keystone(w);
    relief_up(-0.4, bd) intersection() { offset(r = 0.6) s_outline(w); s_bars(w); }
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) s_outline(w);
}
// on the turrets, facing out from the corner: [turret index, z, half-width, height]
TWIN = [for (k = [0 : 3], z = [72, 98]) [k, z + (TURS[k][1] > 0 ? 12 : 0), 3.6, 9]];
function t_ang(k) = atan2(TURS[k][1], TURS[k][0]);
module t_place(k, z) { p = tpos(TURS[k]); translate([p[0], p[1], z]) rotate([0, 0, t_ang(k) + 90]) rotate([90, 0, 0]) children(); }
module t_clip(k, r0, r1) intersection() { children(); translate(tpos(TURS[k])) difference() { cylinder(r = r1, h = 300, $fn = 96); translate([0, 0, -1]) cylinder(r = r0, h = 302, $fn = 96); } }
module tw_outline(w) polygon(seg_pts(w[2], w[3]));
module twin_openings() for (w = TWIN) t_place(w[0], w[1]) translate([0, 0, -12]) linear_extrude(30) tw_outline(w);
module twin_holes() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + fr_t + 3) t_place(w[0], w[1]) translate([0, 0, TR]) relief_hole(-1.4, -1.2, fr_t + 2.4) offset(r = 0.4) tw_outline(w);
module twin_frames() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + fr_t) t_place(w[0], w[1]) translate([0, 0, TR]) {
    relief_up(-1.4, fr_t + 0.4) { union() { offset(r = 2.0) tw_outline(w); translate([-w[2] - 2.6, -sill]) square([2 * (w[2] + 2.6), sill + 1]); } offset(r = 0.3) tw_outline(w); }
}
module twin_glass() for (w = TWIN) t_clip(w[0], TR - wall + 0.1, TR - 0.2) t_place(w[0], w[1]) translate([0, 0, -2]) linear_extrude(TR + 4) offset(r = 0.6) tw_outline(w);
module twin_bars() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + bd) t_place(w[0], w[1]) translate([0, 0, TR]) relief_up(-1.4, bd + 0.2) intersection() { offset(r = 0.6) tw_outline(w); translate([-mull / 2, -3]) square([mull, 40]); }

// =====================================================================================
// THE ROOF: three slate slopes with their slates and snow, copings on the teeth
// =====================================================================================
ov = 0;                     // flush with the smooth walls: past them, each slab's corner at a
                            // valley began in air (2026-10-12)
e  = 1.0;                   // past the right end's eave, over a white soffit
module slab(i) xz(-Dh - ov, Dh + ov) let (x0 = xi(i), x1 = xi(i + 1) + (i == NT - 1 ? e : 0), tv = tvb(i))
    polygon([[x0, RIDGE - tv], [x0, RIDGE + 0.01], [x1, RIDGE - RISE * (x1 - x0) / TWS[i]], [x1, RIDGE - RISE * (x1 - x0) / TWS[i] - tv]]);
sh_c = 2.35;
module slates(i) {
    x0 = xi(i);  run = TWS[i] + (i == NT - 1 ? e : 0);
    nk = ceil((run - 1.2) / sh_c);
    for (k = [0 : nk - 1]) let (a = run - k * sh_c, b = max(run - (k + 1) * sh_c - 0.5, 1.2))
        if (a > b + 0.3) xz(-Dh - ov, Dh + ov)
            polygon([[x0 + a, RIDGE - RISE * a / TWS[i] - 1.0], [x0 + a, RIDGE - RISE * a / TWS[i] + 0.9], [x0 + b, RIDGE - RISE * b / TWS[i] + 0.05], [x0 + b, RIDGE - RISE * b / TWS[i] - 1.0]]);
}
// snow from each ridge down a wavy line
function sn_run(y, i) = 11 + 2.4 * sin(y * 13 + 70 * i) + 1.4 * sin(y * 37 + 30 * i);
module roof_snow(i) intersection() {
    x0 = xi(i);
    xz(-Dh - ov, Dh + ov) polygon([[x0 - 0.01, RIDGE - 1.0],   // flush with the slab's ends: 0.3 past them it hung (2026-10-12)
         [x0 - 0.01, RIDGE + 1.6], [x0 + 22, RIDGE - RISE * 22 / TWS[i] + 1.8], [x0 + 22, RIDGE - RISE * 22 / TWS[i] - 1.0]]);
    linear_extrude(200) polygon(concat([for (k = [0 : 40]) let (y = -Dh - 3 + (D + 6) * k / 40) [x0 + sn_run(y, i), y]], [[x0 - 1, Dh + 3], [x0 - 1, -Dh - 3]]));
}
// under the right end's eave, a white soffit from the wall out to the slab's
// lip at 45 deg: run out past the wall alone, the slab's lowest edge was its
// tip, and that printed in air (2026-10-12)
z_tip = RIDGE - RISE * (TWS[NT - 1] + e) / TWS[NT - 1] - tvb(NT - 1);      // the slab's underside at its lip
z_sof = z_tip - e * tan(55);                    // where the soffit meets the wall
module soffit() xz(-Dh - ov, Dh + ov) polygon([[Lh - 0.5, z_tip - (e + 0.5) * tan(55)], [Lh + e, z_tip], [Lh + e, z_tip + 2], [Lh - 0.5, z_tip + 3]]);   // 55: at 45 the slicer propped it
// a white coping along the top of each glazed tooth, over its slope's start
// its lip 0.6 over the upright face climbs 50 deg to it: as a square block the
// lip hung over the flat glazed face and the slicer propped it (2026-10-12)
module copings() for (i = [0 : NT - 1]) let (x0 = xi(i)) xz(-Dh - ov, Dh + ov)
    // its back edge sunk into the slope below it: level, it hung over the steep end teeth (2026-10-12)
    polygon([[x0 + wall + 0.8, RIDGE - RISE * (wall + 0.8) / TWS[i] - 0.5], [x0 + wall + 0.8, RIDGE + 1.6], [x0 - 0.6, RIDGE + 1.6], [x0 - 0.6, RIDGE - 0.1], [x0, RIDGE - 0.82]]);

// =====================================================================================
// CHIMNEY STACKS: candy canes, a flared crown
// =====================================================================================
STACKS = [[-43.75, 8, 8, 176], [43.75, 8, 9, 192]];   // [x, y, r, top]
// flues from the floor, one in the middle of each end bay: clear of the
// tealight's circle in the middle bay and of every window's collar (2026-10-12)
// the cane's outline, grown by g: the body, and (grown 0.01) what the stripes
// are cut to
module stack_shape(s, g = 0) translate([s[0], s[1], plinth_h - 0.5]) {
    cylinder(r = s[2] + g, h = s[3] - 6.8 - plinth_h + 0.51, $fn = 72);
    // its crown flaring out 2.0 over 2.8 (36 deg): at 45 the gate's slicer propped it (2026-10-12)
    translate([0, 0, s[3] - 6.8 - plinth_h + 0.5]) cylinder(r1 = s[2] + g, r2 = s[2] + 2.0 + g, h = 2.8, $fn = 72);
    translate([0, 0, s[3] - 4 - plinth_h + 0.5]) cylinder(r = s[2] + 2.0 + g, h = 4.0 + g, $fn = 72);
}
module stack_body(s) stack_shape(s);
module stack_bore(s) translate([s[0], s[1], -1]) cylinder(r = s[2] - 2.0, h = s[3] + 2, $fn = 48);
module stack_col(s) translate([s[0], s[1], -1]) cylinder(r = s[2] + 0.8, h = s[3], $fn = 72);
// two red stripes winding up it, flush, a turn every 40 mm; ring sectors clear
// of the axis (drawn from it, the twist made a solid CGAL dropped). Cut to
// the cane's own outline: cut to a ring 2 wider, they stood out of the shaft
// as helical ribs, every underside an overhang (2026-10-12)
module stack_stripes(s) translate([s[0], s[1], 0]) intersection() {
    difference() { translate([-s[0], -s[1], 0]) stack_shape(s, 0.01); translate([0, 0, -1]) cylinder(r = s[2] - 0.6, h = 300, $fn = 72); }
    translate([0, 0, plinth_h]) linear_extrude(s[3] - plinth_h + 1, twist = -360 * (s[3] - plinth_h) / 40, slices = 240, $fn = 72)
        for (q = [0, 180]) rotate(q) polygon([[s[2] - 3, 0], [s[2] + 6, 0], [(s[2] + 6) * cos(50), (s[2] + 6) * sin(50)], [(s[2] - 3) * cos(50), (s[2] - 3) * sin(50)]]);
}

// =====================================================================================
// THE NORTH POLE: candy-striped, a ball on top, a sign on brackets
// =====================================================================================
NP = [-95, -55];  np_r = 5.2;  np_top = 104;
module np_spiral(half) translate([NP[0], NP[1], plinth_h - 1]) linear_extrude(np_top - plinth_h + 1, twist = -720, slices = 160)
    intersection() { circle(r = np_r, $fn = 48); rotate(half * 180) translate([-np_r, 0]) square([2 * np_r, np_r]); }
module np_ball() finial([NP[0], NP[1]], np_top - 0.01, 6.0);
nps_z = 76;  nps_w = 40;  nps_h = 10.2;
module np_board() translate([NP[0], NP[1] - np_r - 2.0, nps_z]) {
    translate([-nps_w / 2, 0, 0]) cube([nps_w, 3.0, nps_h]);
    // knee braces under each half: the hull of a strip sunk in the pole and the
    // board's end, so the underside climbs 50 deg from the pole and the whole
    // brace stands on it. Set in front of the board with their tips clear of
    // the pole, they started in air and left the board's back unpropped (2026-10-12)
    for (s = [-1, 1]) hull() {
        translate([-0.5, 2.0, -(nps_w / 2) * tan(50)]) cube([1.0, np_r, 0.01]);
        translate([-0.5, 0, -0.01]) cube([1.0, 3.0, 0.01]);
        translate([s * (nps_w / 2 - 0.005), 1.5, -0.005]) cube([0.01, 3.0, 0.01], center = true);
    }
}
module np_text() translate([NP[0], NP[1] - np_r - 2.0, nps_z + nps_h / 2]) rotate([90, 0, 0]) letters_up(0.84, 5)
    text("NORTH POLE", size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.02);

// =====================================================================================
// ICICLES under the right end's eave and the gatehouse's walk
// =====================================================================================
module icicle2d(len, w) drip2d(len + 0.6, w + 0.4);   // icing drips, not icicles
// either side of the toy window, between its frame and the turrets. (Spread
// over the whole end, every one fell inside the window's keep-out and none
// was made, 2026-10-12.)
IC_R = [for (i = [0 : 3]) [[-19.4, -17.2, 17.2, 19.4][i], 2.2 + 2.2 * rnd(i, 7), 1.6 + 0.4 * rnd(i, 17)]];
module icicles() {
    for (c = IC_R) face_at(3, c[0], z_sof - 0.6) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);
}

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() {
    square([L, D], center = true);
    for (t = TURS) translate(tpos(t)) circle(r = TR + 1);
    translate(GC) square([GW, GD], center = true);
    translate(NP) circle(r = 9);
    translate([NP[0], NP[1] - 3]) square([nps_w, 6], center = true);
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[-Lh - 2, 0, 3.5, 9, 2.8], [Lh + 2, 0, 3.5, 9, 2.4], [-48, Dh + 2, 7, 3.5, 2.6], [48, Dh + 2, 7, 3.5, 2.4],
          [-25, -Dh - 3, 3.0, 2.6, 2.2], [24, -Dh - 3, 3.0, 2.6, 2.2], [NP[0] + 8, NP[1] + 2, 4, 4, 2.6]];
module base() {
    base_slab();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.5]) intersection() {
            scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
            translate([-60, -60, 0]) cube(120);
        }
        linear_extrude(plinth_h + 10) offset(delta = -2.4) base2d();
    }
}
// every one at least its own width inside the base's edge: five of them stood
// past it and hung in air (2026-10-12)
GUMS = [[-Lh - 3.5, -14, 1], [-Lh - 3.5, 14, 0], [Lh + 3.5, -17, 0], [Lh + 3.5, 17, 1], [-6, Dh + 3.5, 1], [26, Dh + 3.5, 0],
        [-30, -Dh - 3.5, 0], [30, -Dh - 3.5, 1], [NP[0] + 12, NP[1] + 8, 1]];
module base_gumdrops(red) for (g = GUMS) if (g[2] == (red ? 1 : 0)) translate([g[0], g[1], plinth_h + 0.2]) gumdrop(2.4);
module merlon_gumdrops(red) for (i = [0 : 3]) if ((i % 2 == 0) == red)
    translate([GC[0] - GWh + 1.5 + (i < 2 ? 0 : GW - 3.0), GC[1] - GD / 2 + 1.5 + (i % 2) * (GD - 3.0), GH + mer_h + 1.4]) gumdrop(1.4);
module brand_mark() translate([32, -Dh - 3.0, -0.5]) linear_extrude(1.3)   // at y -40 it came 0.2 from the base's edge, at x 40 0.7 from the turret's open floor (2026-10-12)
   
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// THE ROOM: one space under the three teeth, the turrets and the gatehouse,
// less the inside walls under the valleys (each with its pointed arch), the
// windows' collars and the stacks
// =====================================================================================
module hall_room() for (i = [0 : NT - 1]) {
    x0 = xi(i) + wall;  x1 = xi(i + 1) - (i == NT - 1 ? wall : part_w);
    intersection() {
        translate([x0, -Dh + wall, -2]) cube([x1 - x0, D - 2 * wall, 200]);
        xz(-60, 60) polygon([[x0 - 1, -5], [x1 + 1, -5], [x1 + 1, zc_bay(i, x1 + 1)], [x0 - 1, zc_bay(i, x0 - 1)]]);
    }
}
// the arches through the inside walls: lancets, 24 wide, slopes 56 deg at the crown
module valley_arches() for (i = [1 : NT - 1]) translate([xi(i) + wall / 2, 0, plinth_h]) rotate([90, 0, 90]) translate([0, 0, -6]) linear_extrude(12) pointed2d(12, 2, 6);   // crown 49.8, under both valleys' ceilings
// each inside wall's foot 0.3 thicker, up to the eave: at wall + part_w the
// window collars' columns stopped 0.1 short of it, a sealed hairline slit down
// the wall that print_fidelity flagged (2026-10-11). Thickened all the way up,
// it set the glazed teeth's windows 0.3 back from their inner face, under a
// flat head the slicer propped (2026-10-12)
module part_shims() for (i = [1 : NT - 1]) difference() {
    translate([xi(i) + wall - 0.01, -Dh, -5]) cube([0.31, D, EAVE + 5]);
    valley_arches();
}
// a lancet doorway from the hall into each turret, facing the hall's middle
module turret_door(t) translate(tpos(t)) rotate([0, 0, atan2(-t[1], -t[0])])
    translate([TR - wall - 1.5, 0, plinth_h]) rotate([90, 0, 90]) hull() {
        // jambs radial: parallel, they met the drum's face at 70 deg and left a
        // knife edge of wall along each (2026-10-12)
        linear_extrude(0.01) scale([(TR - wall - 1.5) / (TR + 1.5), 1]) pointed2d(5, 30, 6);
        translate([0, 0, wall + 3 - 0.01]) linear_extrude(0.01) pointed2d(5, 30, 6);
    }   // crown 54.6, its slopes 56 deg (steeper inside, where the jambs close in): cut
        // through the curved wall at 48.6 deg the slicer still propped it (2026-10-12)
module room() difference() {
    union() {
        // kept out of the turrets: where the hall's room ran into a turret it
        // took the turret's wall away up to the hall's ceiling, and the wall
        // above started in air along a near-level edge (2026-10-12)
        difference() { hall_room(); for (t = TURS) translate(tpos(t)) translate([0, 0, -5]) cylinder(r = TR, h = 300, $fn = 96); }
        for (t = TURS) turret_door(t);
        valley_arches();
        for (t = TURS) turret_room(t);
        gate_room2();
        gate_way();
    }
    for (w = TOYW) w_collar_col(w);
    for (s = STACKS) stack_col(s);
    part_shims();
}

// =====================================================================================
// PARTS
// =====================================================================================
module hall_walls() intersection() { brick_box(L, D, RIDGE + 2); envelope(0.6); }
module body_raw() {
    hall_walls();
    for (t = TURS) turret_drum(t);
    gate_block();
    merlons();
    for (w = TOYW) w_collar(w);
    step();
}
module turret_cols() for (t = TURS) translate(tpos(t)) translate([0, 0, -1]) cylinder(r = TR + bd, h = 300, $fn = 96);
module roof_raw() {
    difference() {
        union() { for (i = [0 : NT - 1]) { slab(i); slates(i); } }
        for (s = STACKS) stack_col(s);
        turret_cols();
    }
    for (t = TURS) { turret_cone(t); cone_slates(t); }
    door_leaf();
    difference() { sign_board(); sign_text(); }
    difference() { np_board(); np_text(); }
    for (w = TOYW) w_art(w);
    rose_art();
}
module accent_raw() { wreaths(); for (s = STACKS) stack_stripes(s); np_spiral(0); base_gumdrops(true); merlon_gumdrops(true); for (t = TURS) translate([tpos(t)[0], tpos(t)[1], t[2] + cone_h + 0.4]) gumdrop(2.6); }
module trim_raw() {
    difference() {
        union() {
            base();
            difference() { union() { for (i = [0 : NT - 1]) roof_snow(i); copings(); soffit(); } for (s = STACKS) stack_col(s); turret_cols(); }
            for (t = TURS) { cone_snow(t); turret_corbel(t); }
            for (k = [0 : 3]) turret_drips(k);
            merlon_snow();
            for (s = STACKS) stack_body(s);
            base_gumdrops(false); merlon_gumdrops(false);
            for (w = TOYW) { w_frame(w); w_pane(w); }
            cler_windows();
            twin_frames(); twin_glass(); twin_bars();
            rose_frame(); rose_pane();
            door_frame(); hinges(); wreath_bows();
            sign_text(); np_text();
            np_spiral(1); np_ball();
            icicles();
        }
        room();
        for (s = STACKS) stack_bore(s);
        brand_mark();
    }
}
module roof_part()   difference() { roof_raw(); difference() { room(); for (w = TOYW) w_glow_col(w); } }
module accent_part() difference() { accent_raw(); roof_raw(); }
module trim_part()   difference() { trim_raw(); accent_raw(); roof_raw(); }
module body_part() {
    difference() {
        body_raw();
        room();
        for (w = TOYW) w_hole(w);
        cler_openings(); cler_holes();
        twin_openings(); twin_holes();
        rose_cut(); rose_holes();
        door_opening();
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
