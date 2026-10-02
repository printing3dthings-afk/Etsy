// Victorian Santa's Workshop -- building #6 of the Dickens Victorian village
// (Scott, 2026-10-02: "Add a Santa workshop to the Victorian village. Make it
// have big windows with toys outlined on the windows sunk in so it looks like
// they are inside." Built before the clock tower. From two look studies he
// asked for a mix: concept 1's long workshop with ONE big window, concept 2's
// loading doors with wreaths and scalloped bargeboards, concept 1's skylights.)
//
// A long one-storey brick workshop under a steep slate roof. Across its front,
// one big round-arched window whose white pane is set 4 mm deep in the wall,
// toys drawn on it in dark lines: a rocking horse and a teddy on the floor, a
// sailboat, a toy soldier and a jack-in-the-box on a shelf, a fanlight over
// them. Beside it, arched loading double doors with a wreath on each leaf,
// under a SANTA'S WORKSHOP sign. Three skylights in the roof, scalloped white
// bargeboards on both gables, a tall chimney, snow and icicles. On a soft blob
// of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed. In the big window the toys' lines run right through the white pane,
// so with the light on they show dark against it, like toys inside.
//
// THE BLOCK is the coaching inn's (../coaching_inn), all brick with no jetty:
// brick skin, quoins, gables, kneelers, eave flare, slates and snow, windows,
// keystones, icicles, bargeboards, chimney, base, all with their WHY comments
// there. Drawn in the inn's frame, gables on +-y, turned into place by blk():
// local x is the world's y (front at -x), local y is minus the world's x.
//
// COLOUR PARTS, ONE PRINT (victorian_santas_workshop.3mf), priority
// roof > accent > trim > body:
//   body    brick: the walls and gables, the window's deep reveal, the
//           chimney, the step
//   roof    slate: the roof, the skylights' frames, the finials, the doors,
//           the sign board, the toys and the fanlight's lines on the pane
//   trim    white: snow base and drifts, quoins, the eave flare, icicles, snow
//           on the roof, the bargeboards, every window's frame, keystone,
//           sill and pane, the back windows' bars, the door frame and its
//           keystone, the hinges, the wreaths' bows, the skylights' glass,
//           the sign's letters
//   accent  evergreen: the wreaths

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts
include <toys_lib.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// =====================================================================================
// THE BLOCK, in the inn's frame
// =====================================================================================
W        = 56;              // local x: the world's depth
D        = 86;              // local y: the world's width
wall     = 1.68;
corner_r = 1.5;
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;
module blk() rotate([0, 0, 90]) children();

bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// the eave at 64: tall enough that the big window's keystone stays under the
// eave flare's foot (zf0, 54.8)
H     = 64;
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

// faces: 0 = the world's left gable, 1 = its right, 2 = back, 3 = FRONT
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

// ---- the brick walls and gables, and quoins ------------------------------------------------
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
module walls() {
    intersection() { brick_skin(W, D, z_out(0) + 2); union() { below_ceil(); gable_keep(); } }
    kneelers();
}
q_long = 5.2;  q_short = 3.0;  q_off = 0.5;
nq     = 8;                 // pairs of courses: up to zc(16) = 50, under the eave flare's foot
function q_len(j, gable) = (j % 2 == 0) == gable ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = min(zc(2 * j + 2), zf0 - 1.4)) {
        translate([sx > 0 ? Wh - q_len(j, true) : -Wh - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0 - q_off]);
        translate([sx > 0 ? Wh - 0.5 : -Wh - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0 - q_off]);
    }
}
module quoins() intersection() { brick_skin(W, D, zc(2 * nq) + 2); quoin_boxes(); }

// =====================================================================================
// THE BIG WINDOW, its pane 4 mm deep, toys on it
// =====================================================================================
BW_u = 16;                  // world x -16
BW_z = 12;                  // its sill, at the glass
bw_a = 14;  bw_h = 17;      // half-width, straight sides: the glass's crown at 43
recess = 3.5;               // the pane's face behind the wall's face
pane_t = 1.48;
sh_r   = 1.2;               // the splay: the head rises 1.2 per 1 outward, 50 deg
function arch_pts(a, hgt, n = 36) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
module bw_outline() polygon(arch_pts(bw_a, bw_h));
// ONE OPENING through frame, brick and reveal, SPLAYED: the arch at the glass,
// its head rising 1.2 per 1 outward to the frame's face, its floor level. Its
// lowest edge is the glass's, which holds it up. Two earlier tries, both propped
// by the gate's slicer from the window's floor: the head rising INWARD left the
// arch at the frame's face as the lowest edge, a round arch near level over
// 20 mm with nothing behind it; a frame rising outward over a reveal rising
// inward met it in a near-level downward crease. Drawn first as a straight
// copy unioned with a sheared one, it also met itself in broken slivers
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.4;
module slice(z) translate([0, 0, z]) linear_extrude(0.01) children();
function bw_rise(z) = sh_r * (z + recess);
module bw_sec2d(z) hull() { bw_outline(); translate([0, bw_rise(z)]) bw_outline(); }
module bw_hull(z1) hull() { slice(-recess) bw_outline(); slice(z1) bw_sec2d(z1); }
module bw_hole() nf(3, BW_u, BW_z) {
    bw_hull(fr_t);
    translate([0, 0, fr_t]) linear_extrude(3) bw_sec2d(fr_t);
}
module bw_pane() nf(3, BW_u, BW_z) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) offset(r = 1.0) bw_outline();
// brick round the reveal and the pane, inside the room, down to the base
bw_cd = recess + pane_t;    // its back face
module bw_collar2d() union() {
    offset(r = 2.6) bw_sec2d(fr_t);
    translate([-bw_a - 2.6, -BW_z + 1]) square([2 * (bw_a + 2.6), BW_z - 1 + bw_h]);
}
module bw_collar() nf(3, BW_u, BW_z) translate([0, 0, -bw_cd]) linear_extrude(bw_cd - wall + 0.4) bw_collar2d();
// the room leaves it right down below the table: stopped at 1 mm, the base under
// it was cut away and the slicer propped the reveal's foot
module bw_collar_col() nf(3, BW_u, BW_z) translate([0, 0, -bw_cd - 0.01]) linear_extrude(bw_cd + 0.02) union() {
    bw_collar2d();
    translate([-bw_a - 2.6, -BW_z - 3]) square([2 * (bw_a + 2.6), BW_z + bw_h]);
}
// the frame: raised white round the opening at the face, a keystone and a sill
bw_ftop = bw_h + bw_a + bw_rise(fr_t);   // the opening's crown at the frame's face
module bw_frame() nf(3, BW_u, BW_z) {
    difference() {
        relief_up(-0.4, fr_t) union() { offset(r = fr_w) bw_sec2d(fr_t); translate([-bw_a - fr_w - 0.8, -sill]) square([2 * (bw_a + fr_w + 0.8), sill + 1]); }
        bw_hull(fr_t + 0.6);
    }
    difference() {
        relief_up(-0.4, fr_t + 0.5) translate([0, bw_ftop - 0.2]) polygon([[-1.6, 0], [1.6, 0], [2.2, fr_w + 2.2], [-2.2, fr_w + 2.2]]);
        bw_hull(fr_t + 0.6);
    }
}

// what is drawn on the pane, in its own 2D frame (origin at the sill's centre).
// Every line is 0.8 wide, every gap at least 0.8.
shelf_y = 13.6;  trans_y = 26.2;
TOYS = [["horse", -5.3, 0.4], ["teddy", 8.3, 1.2],
        ["boat", -8.0, shelf_y + 0.4], ["soldier", 0, shelf_y + 0.4], ["jack", 8.5, shelf_y + 0.4]];
module pane_art2d() {
    intersection() {
        offset(r = 1.0) bw_outline();
        union() {
            for (t = TOYS) translate([t[1], t[2]]) toy(t[0]);
            translate([-30, shelf_y - tw / 2]) square([60, tw]);
            translate([-30, trans_y - tw / 2]) square([60, tw]);
            // the fanlight: a hub and five rays, the rays starting 1.2 clear of
            // it so they never meet closer than their own width
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
module bw_art() nf(3, BW_u, BW_z) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) pane_art2d();

// =====================================================================================
// THE LOADING DOORS, arched, a wreath on each leaf, and the sign over them
// =====================================================================================
dr_u = -21;                 // world x 21
dr_a = 9;  dr_h = 12;       // crown at 29
module door_outline() polygon(arch_pts(dr_a, dr_h));
// the leaves flush with the frame at the bricks' face (the inn: raised, the
// frame's head stood over the leaf and the slicer propped the doorway)
module hinges2d() for (s = [-1, 1], z = [3.4, 9.0]) translate([s * (dr_a - 3.6), z]) square([6.0, 1.2], center = true);
module door_leaf() nf(3, dr_u, plinth_h) difference() {
    translate([0, 0, -wall]) linear_extrude(wall + bd) translate([0, -0.3]) offset(delta = 0.25) polygon(arch_pts(dr_a, dr_h + 0.3));
    // the meeting line, a groove pointed at 60 deg under the crown. Plank grooves
    // run up into the arch and across the hinges left little ceilings the
    // slicer propped
    translate([0, 0, bd - 0.5]) linear_extrude(2)
        polygon([[-0.4, -1], [0.4, -1], [0.4, dr_h + dr_a - 3], [0, dr_h + dr_a - 3 + 0.4 * tan(60)], [-0.4, dr_h + dr_a - 3]]);
    translate([0, 0, bd - 0.6]) linear_extrude(2) hinges2d();
}
module hinges() nf(3, dr_u, plinth_h) translate([0, 0, bd - 0.6]) linear_extrude(0.6) hinges2d();
module door_opening() nf(3, dr_u, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
module door_frame() nf(3, dr_u, plinth_h) {
    translate([0, 0, -0.6]) linear_extrude(0.6 + bd) difference() {
        intersection() { offset(r = 1.8) door_outline(); translate([-30, -0.5]) square([60, 100]); }
        door_outline();
    }
    relief_up(-0.4, bd + 0.9) translate([0, dr_h + dr_a - 0.6]) polygon([[-1.3, 0], [1.3, 0], [1.9, 4.0], [-1.9, 4.0]]);
}
wr_z = plinth_h + dr_h + 2.2;
module wreaths() for (s = [-1, 1]) nf(3, dr_u + s * 4.5, wr_z) relief_up(-0.2, 0.2 + bd + 0.8) difference() { circle(r = 2.6, $fn = 40); circle(r = 1.3, $fn = 32); }
module bow2d() {
    polygon([[0, 0], [-1.9, 1.0], [-1.9, -1.0]]);  polygon([[0, 0], [1.9, 1.0], [1.9, -1.0]]);
    circle(r = 0.8);
}
module wreath_bows() for (s = [-1, 1]) nf(3, dr_u + s * 4.5, wr_z - 2.6) relief_up(-0.2, 0.2 + bd + 1.2) bow2d();
module step() nf(3, dr_u, plinth_h - 0.5) translate([-dr_a - 2.6, 0, -0.2]) cube([2 * dr_a + 5.2, 1.9, 3.2]);

// the sign: a slate board, SANTA'S / WORKSHOP inlaid white and flush
sg_z = 35.8;  sg_w = 31;  sg_h = 13.2;
module sign_board() nf(3, dr_u, sg_z) relief_up(-0.4, 1.0) translate([-sg_w / 2, 0]) offset(r = 1.0) offset(delta = -1.0) square([sg_w, sg_h]);
module sign_text() intersection() {
    sign_board();
    nf(3, dr_u, sg_z + sg_h / 2) translate([0, 0, 0.2]) linear_extrude(2)
        for (l = [["SANTA'S", 3.0], ["WORKSHOP", -3.0]]) translate([0, l[1]])
            text(l[0], size = 4.2, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.04);
}

// =====================================================================================
// THE OTHER WINDOWS: segmental, glazed, the bars on the pane [face, u, z, a, h]
// =====================================================================================
WINDOWS = [
    [2, 26, 16, 4.0, 10], [2, 0, 16, 4.0, 10], [2, -26, 16, 4.0, 10],
    [0, 0, 16, 4.0, 10], [1, 0, 16, 4.0, 10],
];
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
mull = 1.68;
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
module frame_holes() for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
module openings() for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
module windows() for (w = WINDOWS) nf(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
    relief_up(-0.4, fr_t + 0.5) keystone(w);
    relief_up(-0.4, bd) win_muntins(w, 0.6);
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
}

// =====================================================================================
// ICICLES under the long eaves, clear of the big window and the sign
// =====================================================================================
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 27]) [-Dh + 2.4 + i * (D - 4.8) / 27, 2.4 + 2.4 * rnd(i, 40), 1.8 + 0.6 * rnd(i, 80)]];
function ic_clear(f, u) = !(f == 3 && abs(u - BW_u) < bw_a + fr_w + 2.6)
                       && !(f == 3 && abs(u - dr_u) < sg_w / 2 + 2.0);
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [2, 3], c = IC) if (ic_clear(f, c[0])) nf(f, c[0], zf0 + 1) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

// =====================================================================================
// BARGEBOARDS, white and scalloped; finials, slate
// =====================================================================================
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

// =====================================================================================
// THE ROOF, its snow, three skylights
// =====================================================================================
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
sn_x = 11;
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
// SKYLIGHTS on the front slope: upright-sided boxes, not boxes square to the
// roof (square to it, each one's lower face would lean out 55 deg over air),
// the glass 0.8 under the frame's top
SKY_Y = [26, 0, -26];       // world x -26, 0, 26
sk_x0 = -24.5;  sk_x1 = -17.0;  sk_w = 4.6;  sk_f = 1.3;
module sky_band(lo, hi) xz(-y_rr, y_rr) polygon([[sk_x0 - 2, z_out(sk_x0 - 2) + lo], [sk_x1 + 2, z_out(sk_x1 + 2) + lo],
                                               [sk_x1 + 2, z_out(sk_x1 + 2) + hi], [sk_x0 - 2, z_out(sk_x0 - 2) + hi]]);
module sky_box(g) for (y = SKY_Y) translate([sk_x0 + g, y - sk_w + g, 0]) cube([sk_x1 - sk_x0 - 2 * g, 2 * (sk_w - g), 200]);
// the frames sink 2 into the roof and join it; only the glass sits in a pocket
// (in pockets, frames and all, they came out as three loose pieces)
module skylight_frames() intersection() { sky_band(-2.0, 2.6); difference() { sky_box(0); sky_box(sk_f); } }
module skylight_glass() intersection() { sky_band(-1.5, 1.8); sky_box(sk_f); }
module skylight_cols() intersection() { sky_band(-1.2, 3); sky_box(sk_f); }

// THE CHIMNEY astride the ridge near the right end
CH_Y = -31;                 // world x 31
ch_s = 7.2;
ch_top = z_out(0) + 10;
module chimney() difference() {
    union() {
        translate([-ch_s / 2, CH_Y - ch_s / 2, 40]) cube([ch_s, ch_s, ch_top - 40]);
        hull() {
            translate([-ch_s / 2, CH_Y - ch_s / 2, ch_top - 1.3]) cube([ch_s, ch_s, 0.01]);
            translate([-ch_s / 2 - 0.8, CH_Y - ch_s / 2 - 0.8, ch_top]) cube([ch_s + 1.6, ch_s + 1.6, 1.6]);
        }
        for (x = [-2.1, 2.1]) translate([x, CH_Y, ch_top + 1.4]) cylinder(d = 3.6, h = 4.0, $fn = 32);
    }
    below_ceil();
    for (x = [-2.1, 2.1]) translate([x, CH_Y, ch_top + 3.4]) cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimney_col() translate([-ch_s / 2, CH_Y - ch_s / 2, 40]) cube([ch_s, ch_s, 80]);

// ---- brick joints ---------------------------------------------------------------------------------
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, ztop, boxes) {
    L = (f < 2 ? Wh : Dh) - q_long - 1;
    nf(f, 0, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}
function frame_box(f, w) = let (lu = loc(f, w[1]), h = w[3] + fr_w + 2.5)
    [lu - h, lu + h, w[2] - sill - 2, w[2] + seg_top(w[3], w[4]) + fr_w + 4];
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    f == 3 ? [let (lu = loc(f, BW_u)) [lu - bw_a - fr_w - 2.5, lu + bw_a + fr_w + 2.5, 0, 300],
              let (lu = loc(f, dr_u)) [lu - sg_w / 2 - 2, lu + sg_w / 2 + 2, 0, 300]] : []);
module joints() for (f = [0 : 3]) wall_joints(f, zf0 - 1.5, face_boxes(f));

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
// against the walls, clear of the window's sill and the step
DRIFTS = [[-Dh - 1, 10, 4, 7, 3.0], [Dh + 1, -6, 4, 7, 2.6], [-30, Wh + 1, 7, 3.5, 2.8], [8, Wh + 1, 6, 3.5, 2.4],
          [-39, -Wh - 1, 3.5, 3.0, 2.4], [5.8, -Wh - 1, 2.4, 3.0, 2.2]];
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
// under the front, in front of the doors (world frame)
module brand_mark() translate([-dr_u, -Wh - 1.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// =====================================================================================
// PARTS
// =====================================================================================
// the room: straight up to the roof's ceiling, open underneath, less the big
// window's reveal, which stands on the base inside the front wall
module room() difference() {
    intersection() { translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]); below_ceil(); }
    bw_collar_col();
}
module body_raw() blk() {
    walls();
    bw_collar();
    chimney();
    step();
}
module roof_raw() blk() {
    difference() { union() { slab(); slates(); } room(); chimney_col(); skylight_cols(); }
    skylight_frames();
    finials();
    door_leaf();
    difference() { sign_board(); sign_text(); }
    bw_art();
}
module accent_raw() blk() wreaths();
module trim_raw() {
    difference() {
        union() {
            base();
            blk() {
                quoins();
                eave_flare();
                icicles();
                difference() { snow_roof(); chimney_col(); skylight_cols(); }
                bargeboards();
                skylight_glass();
                windows();
                bw_frame();
                bw_pane();
                door_frame();
                hinges();
                wreath_bows();
                sign_text();
            }
        }
        blk() room();
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
            room();
            openings(); frame_holes();
            bw_hole();
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
else if (part == "art")    pane_art2d();
else if (part == "all") {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
