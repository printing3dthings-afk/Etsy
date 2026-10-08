// Victorian Coaching Inn -- building #4 of the Dickens Victorian village (Scott,
// 2026-10-01, picked from four: "Long inn + carriage arch").
//
// A long two-storey inn, the widest building in the village. A brick ground
// floor with white quoins, segmental windows with keystones and a door with a
// wreath; over it a white plaster upper floor jettied out on a dark timber
// beam, its timbers, window frames and glazing bars inlaid dark and flush, a
// small wreath in each front window and a red INN sign over the door. A
// pointed carriage archway runs through the right end under the jetty, a wall
// lantern beside it. A steep slate roof with snow, icicles, dark bargeboards
// and two tall chimneys. On a soft blob of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, the ground
// floor's windows glazed with their bars on the pane, and the plaster upper
// floor thin enough to glow between its dark timbers.
//
// THE BLOCK is the toy shop's (../toy_shop): brick skin, quoins, gables,
// kneelers, eave flare, bargeboards, slates and snow, windows and keystones,
// all with their WHY comments there. It is drawn in the toy shop's frame,
// gables on +-y, and turned into place by blk(): local x is the world's y
// (front at -x), local y is minus the world's x.
//
// COLOUR PARTS, ONE PRINT (victorian_coaching_inn.3mf), priority
// roof > accent > trim > body:
//   body    brick: the ground floor and the archway's walls, the chimneys,
//           the sign board, the step
//   roof    slate: the roof, the jetty beam, every timber, the upper windows'
//           frames and bars, the bargeboards and finials, the door, the lantern
//   trim    white: snow base and drifts, quoins, the plaster upper floor, the
//           eave soffit, icicles, snow on the roof, the ground windows' frames,
//           keystones, bars and panes, the door frame and the wreath's bow, the
//           archway's voussoirs, the lantern's glass, INN
//   accent  evergreen: the wreaths

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts
include <../../relief_lib.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// =====================================================================================
// THE BLOCK, in the toy shop's frame
// =====================================================================================
W        = 56;              // local x, the upper floor: the world's depth
W_lo     = 52;              // the ground floor, 2 in under the jetty front and back
D        = 84;              // local y: the world's width
wall     = 1.68;
corner_r = 1.5;
plinth_h = 8;
Wh = W/2;  Wl = W_lo/2;  Dh = D/2;
SH       = 1.2;
module blk() rotate([0, 0, 90]) children();

bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

H1    = 32;                 // the jetty: the upper floor's foot
jet   = Wh - Wl;
cz0   = H1 - (jet + 0.2) * tan(55);   // the jetty beam's foot on the brick
// the eave line at 54: the 46 mm tealight's circle stands 1 mm inside the
// ground floor's wall, under the roof's ceiling at 58
H     = 54;
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

// faces: 0 = the world's left gable, 1 = its right, 2 = back, 3 = FRONT; u
// along the face is local y on the long faces (u = minus the world's x), local
// x on the gables. nf on the upper floor's faces, nfl on the ground floor's.
module nfw(face, u, z, wx) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [wx, u, z] : [-wx, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module nf(face, u, z)  nfw(face, u, z, Wh) children();
module nfl(face, u, z) nfw(face, u, z, Wl) children();
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

// ---- the ground floor's brick and quoins ------------------------------------------------------
function rpts(w, d, g, z, r = corner_r) = [for (p = rrect_pts(w + 2*g, d + 2*g, r + g, 5)) [p[0], p[1], z]];
module brick_skin(w, d, ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(w, d, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(w, d, g, z)],
        [rpts(w, d, 0, ztop + 2)]), slices = 0);
}
module ground_walls() intersection() {
    brick_skin(W_lo, D, H1);
    translate([-50, -50, 0]) cube([100, 100, H1 + 0.5]);
}
// QUOINS on all four corners, short ones: the archway is near the right end
q_long = 5.2;  q_short = 3.0;  q_off = 0.5;
nq     = 4;                 // pairs of courses: up to zc(8) = 29.2, under the jetty beam
function q_len(j, gable) = (j % 2 == 0) == gable ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = min(zc(2 * j + 2), cz0 - 0.4)) {
        translate([sx > 0 ? Wl - q_len(j, true) : -Wl - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0 - q_off]);
        translate([sx > 0 ? Wl - 0.5 : -Wl - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0 - q_off]);
    }
}
module quoins() intersection() { brick_skin(W_lo, D, zc(2 * nq) + 2); quoin_boxes(); }

// THE JETTY BEAM: the upper floor stands 2 out front and back on a dark beam
// whose underside rises at 55 deg from the brick. The upper floor's corners are
// all but square (up_r): rounded like the brick's, the eave flare ran on past
// them over air at all four corners and the slicer propped it
up_r = 0.3;
// On the gables it stands out over the bricks' bumps (bd): flush with the
// plaster there, the bumps' last course rose past it as a 0.16 mm sliver
function bpts(z) = [for (p = rrect_pts(W, D + 2 * (bd + 0.2), up_r, 5)) [p[0], p[1], z]];
module jetty_beam() skin([rpts(W_lo, D, -0.2, cz0), bpts(H1), bpts(H1 + 1.4)], slices = 0);

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
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh, Dh)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
// the plaster upper floor and its gables
module plaster() {
    intersection() {
        translate([0, 0, H1]) linear_extrude(100) polygon(rrect_pts(W, D, up_r, 5));
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}

// ---- THE CARRIAGE ARCHWAY through the right end -----------------------------------------------
pa_y = -26.5;               // its centre, local y (world x 26.5)
pa_a = 7;  pa_h = 5;        // half-width, straight sides: its point at 28.2, under the beam
module pa_outline() polygon(lancet_pts(pa_a, pa_h));
module passage() translate([0, pa_y, plinth_h]) yz(-Wh - 5, Wh + 5) pa_outline();
module passage_walls() translate([0, pa_y, plinth_h - 2]) yz(-Wh - 5, Wh + 5) offset(r = wall) translate([0, 2]) pa_outline();
// the voussoirs round it, front and back, and a keystone
module pa_band() for (f = [2, 3]) nfl(f, pa_y, plinth_h) relief_up(-0.4, fr_t) {
    union() {
        intersection() { offset(r = 2.6) pa_outline(); translate([-30, -0.5]) square([60, 100]); }
        translate([0, lancet_top(pa_a, pa_h) - 1.0]) polygon([[-1.4, 0], [1.4, 0], [2.0, 4.2], [-2.0, 4.2]]);
    }
    // inside the passage, which cuts it back: on the passage's own line its back
    // face met the brick jamb in 52 edges of more than two faces
    offset(delta = -0.3) pa_outline();
}

// ---- the rooms ----------------------------------------------------------------------------------
// the ground floor's, left of the archway; the upper floor's, over all of it
// and 2 wider (its floor a ledge on the brick); the archway's walls kept
lo_y0 = pa_y + pa_a + wall;
module ground_room() difference() {
    translate([-Wl + wall, lo_y0, -2]) cube([2 * (Wl - wall), Dh - wall - lo_y0, H1 + 2.01]);
    passage_walls();
}
module upper_room() intersection() {
    translate([-x_in, -y_r, H1]) cube([2 * x_in, 2 * y_r, 200]);
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

mull = 1.68;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.4;
// THE GROUND FLOOR'S WINDOWS, glazed: [face, u, z, a, straight height]
WINDOWS = [
    [3, 28.5, 14, 4.0, 9], [3, -3, 14, 4.0, 9],
    [2, 28.5, 14, 4.0, 9], [2, 10, 14, 4.0, 9], [2, -8, 14, 4.0, 9],
    [0, 0, 14, 4.0, 9],
];
module win_outline(w) polygon(seg_pts(w[3], w[4]));
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, w[4] * 0.55]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_outer(w) {
    offset(r = fr_w) win_outline(w);
    translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]);
}
module keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2]) polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
module low_frame_holes() for (w = WINDOWS) nfl(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module low_openings() for (w = WINDOWS) nfl(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module low_windows() for (w = WINDOWS) nfl(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
    relief_up(-0.4, fr_t + 0.5) keystone(w);
    relief_up(-0.4, bd) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}

// THE UPPER FLOOR'S WINDOWS: casements in the plaster, their frames and bars
// dark and flush, not raised: [face, u, sill, half-width, height]. Not UP:
// BOSL2's own up vector is UP, and redefining it broke BOSL2
UWZ = 35.5;
UPW = concat(
    [for (u = [36, 24, 0, -12, -26.5]) [3, u, UWZ, 3.6, 6.5]],
    [for (u = [36, 24, 12, 0, -12, -26.5]) [2, u, UWZ, 3.6, 6.5]],
    [for (f = [0, 1], u = [-12, 12]) [f, u, UWZ, 3.6, 6.5]]);
uf_w = 1.3;
module case2d(w) {
    difference() { translate([-w[3] - uf_w, -uf_w]) square([2 * (w[3] + uf_w), w[4] + 2 * uf_w]); translate([-w[3], 0]) square([2 * w[3], w[4]]); }
    translate([-0.45, 0]) square([0.9, w[4]]);
    translate([-w[3], w[4] * 0.5 - 0.45]) square([2 * w[3], 0.9]);
}
// TIMBERS on the plaster, flush: a top plate under the eave, posts at the
// corners and where the windows leave room, a tie beam, king post and struts
// in each gable
function up_u(f) = [for (w = UPW) if (w[0] == f) w[1]];
// drawn at nf(f, 0, 0), whose 2D x runs as loc(): on the front and the left
// gable that is minus u
module long_timbers(f) {
    translate([-Dh - 1, zf0 - 2.2]) square([D + 2, 2.2]);
    for (u = [Dh - 1.2, -Dh + 1.2, -19.25]) translate([loc(f, u) - 0.6, H1]) square([1.2, zf0 - H1]);
    for (w = UPW) if (w[0] == f) translate([loc(f, w[1]), w[2]]) case2d(w);
}
// each gable piece extruded on its own: unioned flat first, the pattern came out
// of linear_extrude as a mesh CGAL would not take ("not closed")
module gable_piece(f, i) let (tb = zf0 - 2.2) {
    if (i == 0) translate([-Wh - 1, tb]) square([W + 2, 2.2]);
    if (i == 1) for (u = [Wh - 1.2, -Wh + 1.2]) translate([u - 0.6, H1]) square([1.2, tb - H1]);
    if (i == 2) translate([-0.6, tb]) square([1.2, 60]);
    if (i == 3 || i == 4) let (s = i == 3 ? -1 : 1) hull() { translate([s * 13, tb + 1]) circle(r = 0.6, $fn = 12); translate([0, tb + 13 * 1.1]) circle(r = 0.6, $fn = 12); }
    if (i == 5 || i == 6) let (ws = [for (w = UPW) if (w[0] == f) w]) if (len(ws) > i - 5) let (w = ws[i - 5]) translate([loc(f, w[1]), w[2]]) case2d(w);
}
module timbers() intersection() {
    plaster();
    union() {
        for (f = [2, 3]) nf(f, 0, 0) translate([0, 0, -wall - 1]) linear_extrude(wall + 2) long_timbers(f);
        for (f = [0, 1], i = [0 : 6]) nf(f, 0, 0) translate([0, 0, -wall - 1]) linear_extrude(wall + 2) gable_piece(f, i);
    }
}
// Flush, the timbers and the casements were colour alone: a white print lost
// them, and lit, the thin plaster glowed evenly (2026-10-08). They stand 0.4
// proud of the plaster, for daylight and a painter's brush, and thicken 0.8 into
// the room so they show dark on the glow. Clipped to the walls' faces, so none
// stands out past a corner or over a gable's edge.
// Outside, each face's timbers stop where its flat ends (2026-10-08): the top
// rails ran on past the corners, and their ends stood 0.4 out over the next
// face with no wall under them to climb from; the slicer propped all four.
// And they start SH * 0.4 above the jetty line (2026-10-08): the relief is cut
// flat at H1, and the posts' skirts (art_skirt) ended there in a 0.4 mm ledge
// over the jetty beam's slope; the slicer propped every post (6,764 moves).
module face_span(hw) intersection() { children(); translate([-hw + up_r, H1 + SH * 0.4]) square([2 * (hw - up_r), 200]); }
// Raised full width and 0.15 wider each side (2026-10-08): trimmed from below
// as they climbed (art_out), the 1.2 mm timbers and 0.9 mm casement bars came
// out under a bead at the front, and the gate's 1st percentile sat at 1.06.
module timber_art(i) {
    for (f = [2, 3]) nf(f, 0, 0) if (i == 0) art_skirt(0.4, 2) face_span(Dh) offset(delta = 0.15) long_timbers(f); else translate([0, 0, -wall]) art_in(0.8, 4) long_timbers(f);
    for (f = [0, 1], g = [0 : 6]) nf(f, 0, 0) if (i == 0) art_skirt(0.4, 2) face_span(Wh) offset(delta = 0.15) gable_piece(f, g); else translate([0, 0, -wall]) art_in(0.8, 4) gable_piece(f, g);
}
module timbers_relief() {
    intersection() {
        translate([0, 0, H1]) linear_extrude(100) offset(r = 0.45) polygon(rrect_pts(W, D, up_r, 5));
        union() { below_ceil(); gable_keep(); }
        difference() { timber_art(0); plaster(); }
    }
    // 0.05 into the walls (2026-10-08): clipped at their face, the thickening only
    // touched them, the union kept the face between, and the gate read wall and
    // thickening each as a 0.8 mm skin
    intersection() { plaster_core(0.05); timber_art(1); }
}
// inside the plaster's walls, under its ceiling and gables; g reaches into them
module plaster_core(g = 0) intersection() {
    translate([0, 0, H1]) linear_extrude(100) polygon(rrect_pts(W - 2 * wall + 2 * g, D - 2 * wall + 2 * g, up_r, 5));
    union() { below_ceil(); gable_keep(); }
}

// ---- the door, its wreath; the INN sign; the wreaths in the upper windows -------------------
dr_u = 12;                  // world x -12
dr_a = 4.0;  dr_h = 12;
module door_outline() polygon(seg_pts(dr_a, dr_h));
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() nfl(3, dr_u, plinth_h) difference() {
    translate([0, 0, -wall]) linear_extrude(wall + bd) translate([0, -0.3]) offset(delta = 0.25) polygon(seg_pts(dr_a, dr_h + 0.3));
    translate([0, 0, bd - 0.4]) linear_extrude(2) for (s = [-1, 1]) panel2d(min(s * 0.8, s * 3.2), max(s * 0.8, s * 3.2), 1.0, 2.4);   // under the wreath, which left them slivers
}
// out through the bricks' bumps (the church: through the wall only, the
// courses' ridges ran across the door)
module door_opening() nfl(3, dr_u, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
// the frame a flush white band at the bricks' face, the leaf flush with it:
// raised, the frame's head stood out over the leaf and the slicer propped the
// whole doorway from the base
module door_frame() nfl(3, dr_u, plinth_h) translate([0, 0, -0.6]) linear_extrude(0.6 + bd) difference() {
    intersection() { offset(r = 1.8) door_outline(); translate([-30, -0.5]) square([60, 100]); }
    door_outline();
}
wr_z = plinth_h + dr_h - 4.4;
module wreath() nfl(3, dr_u, wr_z) relief_up(-0.2, 0.2 + bd + 0.8) difference() { circle(r = 2.8, $fn = 40); circle(r = 1.4, $fn = 32); }
module bow2d() {
    polygon([[0, 0], [-2.0, 1.0], [-2.0, -1.0]]);  polygon([[0, 0], [2.0, 1.0], [2.0, -1.0]]);
    circle(r = 0.8);
}
// white: as brick, the door's opening would cut it away (the church)
module wreath_bow() nfl(3, dr_u, wr_z + 2.8) relief_up(-0.2, 0.2 + bd + 1.2) bow2d();
module step() nfl(3, dr_u, plinth_h - 0.5) translate([-dr_a - 2.6, 0, -0.2]) cube([2 * dr_a + 5.2, 1.9, 3.2]);
// the sign: a brick-red board on the plaster, INN raised in white
// 13.6 wide, the most between the windows' frames, the letters 1.0 apart with a
// margin: at 12, INN ran to the board's edges and at an angle read "NN"
sg_z = 35.2;  sg_w = 13.6;  sg_h = 7.6;
module sign_board() nf(3, dr_u, sg_z) relief_up(-0.4, 1.0) translate([-sg_w / 2, 0]) offset(r = 1.0) offset(delta = -1.0) square([sg_w, sg_h]);
// Raised letters (2026-10-07): a flush inlay is colour alone and vanishes on a
// one-colour or painted print (the haunted post office's first print). Each slab
// keeps only what has letter under it all the way down its climb, SH up per 1
// out in 0.2 mm steps (the layers'), so only the undersides slope and the
// counters and tops stay as drawn (Technique 81).
module letters_up(h, n) for (i = [0 : n - 1]) let (t0 = i == 0 ? -0.3 : i * h / n - 0.01,
        k = ceil(SH * (i + 1) * h / n / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / n - t0) intersection_for(j = [0 : k]) translate([0, j * 0.2]) children();
module sign_text() nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 1.0]) letters_up(0.84, 5)
    text("INN", size = 4.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);
// a small wreath in each front upper window, on its bars
module window_wreaths() for (w = UPW) if (w[0] == 3) nf(3, w[1], w[2] + w[4] * 0.5) relief_up(-0.4, 0.9)
    difference() { circle(r = 2.0, $fn = 32); circle(r = 0.8, $fn = 20); }

// ---- THE LANTERN beside the archway ------------------------------------------------------
ln_u = -14.5;  ln_z = 17;
module lantern_frame() nfl(3, ln_u, ln_z) relief_up(-0.4, 2.2) {
    union() {
        polygon([[-2.3, 7.2], [2.3, 7.2], [1.0, 8.8], [-1.0, 8.8]]);
        translate([-0.65, 8.6]) square([1.3, 2.0]);
        polygon([[-2.3, 1.4], [2.3, 1.4], [0, -1.0]]);
        difference() { translate([-2.3, 1.2]) square([4.6, 6.2]); translate([-1.0, 2.2]) square([2.0, 4.2]); }   // 1.3 bars, not 0.7
    }
}
module lantern_glass() nfl(3, ln_u, ln_z) relief_up(-0.4, 1.8) translate([-1.2, 2.0]) square([2.4, 4.6]);

// ---- icicles under the long eaves, clear of the upper windows -----------------------------------
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 26]) [-Dh + 2.4 + i * (D - 4.8) / 26, 2.4 + 2.4 * rnd(i, 40), 1.8 + 0.6 * rnd(i, 80)]];
// clear of the upper windows and of the INN sign, whose top an icicle's tip
// hung 0.2 over
function ic_clear(f, u) = len([for (w = UPW) if (w[0] == f && abs(u - w[1]) < w[3] + uf_w + 2.0) 1]) == 0
                       && !(f == 3 && abs(u - dr_u) < sg_w / 2 + 2.0);
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [2, 3], c = IC) if (ic_clear(f, c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

// ---- bargeboards and finials, dark ----------------------------------------------------------
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

// ---- the roof ------------------------------------------------------------------------------------
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
        polygon(concat([for (i = [0 : 50]) let (y = -Dh + 2 * Dh * i / 50) [sn_edge(y), y]],
                       [for (i = [50 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 50) [-sn_edge(-y), y]]));
}

// ---- two chimneys, astride the ridge near each end ------------------------------------------------
CH_Y = [30, -30];
ch_s = 7.2;
ch_top = z_out(0) + 10;
module chimney(y) difference() {
    union() {
        translate([-ch_s / 2, y - ch_s / 2, 40]) cube([ch_s, ch_s, ch_top - 40]);
        hull() {
            translate([-ch_s / 2, y - ch_s / 2, ch_top - 1.3]) cube([ch_s, ch_s, 0.01]);
            translate([-ch_s / 2 - 0.8, y - ch_s / 2 - 0.8, ch_top]) cube([ch_s + 1.6, ch_s + 1.6, 1.6]);
        }
        for (x = [-2.1, 2.1]) translate([x, y, ch_top + 1.4]) cylinder(d = 3.6, h = 4.0, $fn = 32);   // 1.3 walls round the flue
    }
    below_ceil();
    for (x = [-2.1, 2.1]) translate([x, y, ch_top + 3.4]) cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimneys() for (y = CH_Y) chimney(y);
module chimney_cols() for (y = CH_Y) translate([-ch_s / 2, y - ch_s / 2, 40]) cube([ch_s, ch_s, 80]);

// ---- brick joints on the ground floor ---------------------------------------------------------------
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, ztop, boxes) {
    L = (f < 2 ? Wl : Dh) - q_long - 1;
    nfl(f, 0, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}
function frame_box(f, w) = let (lu = loc(f, w[1]), h = w[3] + fr_w + 2.5)
    [lu - h, lu + h, w[2] - sill - 2, w[2] + seg_top(w[3], w[4]) + fr_w + 4];
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    f >= 2 ? [let (lu = loc(f, pa_y)) [lu - pa_a - 5, lu + pa_a + 5, 0, 300]] : [],
    f == 3 ? [let (lu = loc(f, dr_u)) [lu - dr_a - 4, lu + dr_a + 4, 0, 300],
              let (lu = loc(f, ln_u)) [lu - 4, lu + 4, 0, 300]] : [],
    // the right gable is the archway's pier, the left has its window
    []);
module joints() for (f = [0 : 3]) wall_joints(f, cz0 - 1.5, face_boxes(f));

// =====================================================================================
// THE SNOW BASE, in the world's frame
// =====================================================================================
module footprint() square([D, W], center = true);
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[-Dh - 1, 10, 4, 7, 3.0], [Dh + 1, -6, 4, 7, 2.6], [-30, Wh + 1, 7, 3.5, 2.8], [6, Wh + 1, 6, 3.5, 2.4],
          [-34, -Wh - 1, 5, 3.0, 2.4], [8, -Wh - 1, 4, 3.0, 2.2]];
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
// under the front, between the door's step and the base's edge (world frame)
module brand_mark() translate([-dr_u, -Wh - 1.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
module room() { ground_room(); upper_room(); }
module body_raw() blk() {
    ground_walls();
    chimneys();
    sign_board();
    step();
}
module roof_raw() blk() {
    difference() { union() { slab(); slates(); } upper_room(); chimney_cols(); }
    difference() { jetty_beam(); room(); }
    difference() { timbers(); room(); }
    timbers_relief();
    bargeboards();
    finials();
    door_leaf();
    lantern_frame();
}
module accent_raw() blk() { wreath(); window_wreaths(); }
module trim_raw() {
    difference() {
        union() {
            base();
            blk() {
                difference() { plaster(); room(); }
                quoins();
                eave_flare();
                icicles();
                difference() { snow_roof(); chimney_cols(); }
                low_windows();
                pa_band();
                door_frame();
                wreath_bow();
                sign_text();
                lantern_glass();
            }
        }
        blk() { room(); passage(); }
        brand_mark();
    }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        blk() {
            room(); passage();
            low_openings(); low_frame_holes();
            door_opening();
            joints();
        }
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
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
