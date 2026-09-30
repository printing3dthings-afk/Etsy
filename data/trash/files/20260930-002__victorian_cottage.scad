// Victorian Cottage -- building #1 of the Dickens Victorian Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: brick walls with white quoins, a steep
// slate gable under snow, a pierced white bargeboard with a finial on both
// gables, segmental-arched sash windows with keystones, gothic lancets in the
// gables, a round-arched black door with a wreath and a garland, window boxes,
// icicles under the eaves, a chimney with two pots, on a snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on (the chapel's first print,
// 2026-09-27: free-standing bars snap).
//
// The machinery -- V-course walls, sheared reliefs, the eave flare, kneelers,
// the coping over the gables, frames and panes -- is the Haunted Town chapel's
// (haunted_town/chapel/haunted_chapel.scad), proven on Scott's printer, and
// its WHY comments are there. What is new here is commented here.
//
// COLOUR PARTS, ONE PRINT (victorian_cottage.3mf):
//   body    brick walls, chimney and pots, the kneelers, the bows
//   roof    slate slab and courses, the front door
//   trim    snow base and drifts, quoins, bargeboards and finials, window and
//           door frames, sills, keystones, panes and bars, the eave soffit and
//           icicles, the snow on the roof
//   accent  evergreen: the wreath, the garland, the window boxes
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave; the
// 58 deg ceiling is 60 mm up at the edge of a 46 mm circle round the centre.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts; lives in openscad_models/

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;              // along X, the front gable's width
D        = 58;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
plinth_h = 8;               // the snow base; the walls stand on it
Wh = W/2;  Dh = D/2;
SH       = 1.2;             // relief shear (see relief_up)

// ---- brick -----------------------------------------------------------------------
// The post office's brick: V courses ramping out at 58 deg, flat, chamfered
// back in at 45; stretcher bond.
bd    = 0.6;                // brick face, proud of plan(0)
bp    = 2.6;                // course height
br    = bd * tan(58);
bj    = 0.6;                // joint width
bl    = 7;                  // brick length, joint to joint
// The first groove sits 0.4 above the snow: exactly on the base's top it left
// a zero-thickness sheet of brick along the front wall where the two met.
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- roof --------------------------------------------------------------------------
// A 58 deg gable: the chapel's roof at the post office's steepest safe angle.
// Its inside is the lantern's ceiling.
H     = 52;
r_ang = 58;
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

// ---- placement ---------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
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

// ---- brick walls ---------------------------------------------------------------------
function rpts(w, d, g, z) = [for (p = rrect_pts(w + 2*g, d + 2*g, corner_r + g, 5)) [p[0], p[1], z]];
module brick_skin(ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(W, D, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(W, D, g, z)],
        [rpts(W, D, 0, ztop + 2)]), slices = 0);
}

// QUOINS. White corner stones, two courses tall, alternating long and short
// up each corner, and interlocking: where the front shows a long stone the
// side shows a short one. They are the brick skin itself, recoloured: each is
// the skin inside a box cut exactly on course lines, so a quoin's edges are
// the course grooves and it needs no underside of its own.
q_long = 6.2;  q_short = 3.6;
// Each quoin's top and bottom cut 0.2 up the course's ramp, not on the
// groove line: there the box's face ran through the skin's own ring of
// vertices and left zero-area faces round every corner.
q_off  = 0.5;
nq     = 6;                 // pairs of courses: up to zc(12) = 39.2
function q_len(j, gable) = (j % 2 == 0) == gable ? q_long : q_short;
module quoin_boxes() {
    for (j = [0 : nq - 1], sx = [-1, 1], sy = [-1, 1]) let (z0 = zc(2 * j), z1 = zc(2 * j + 2)) {
        // on the gable faces (front, back)
        translate([sx > 0 ? Wh - q_len(j, true) : -Wh - 3, sy > 0 ? Dh - 0.5 : -Dh - 3, z0 + q_off])
            cube([q_len(j, true) + 3, 3.5, z1 - z0]);
        // on the side faces
        translate([sx > 0 ? Wh - 0.5 : -Wh - 3, sy > 0 ? Dh - q_len(j, false) : -Dh - 3, z0 + q_off])
            cube([3.5, q_len(j, false) + 3, z1 - z0]);
    }
}
module quoins() intersection() { brick_skin(zc(2 * nq) + 2); quoin_boxes(); }

// Vertical joints, stretcher bond, a whole course tall and floored 0.05
// behind plan(0) (the post office's measured rule). None within the quoins'
// reach of a corner.
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, ztop, boxes) {
    L = (f < 2 ? Wh : Dh) - q_long - 1;
    nf(f, 0, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            // and none reaching up under a bargeboard, whose foot would
            // bridge the slot
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes) && (f >= 2 || z1 < z_out(abs(u) + 1) - bb_h - 1.5))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}

// ---- nave regions (the chapel's) --------------------------------------------------------
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
// The eave flare carries the eaves, as on the chapel. Here it is WHITE: it
// reads as the snow-covered soffit, and the icicles hang from its foot.
// It runs 0.2 past the kneelers' outer faces: ending on the same plane as
// the (brick) kneeler, the two faces differed by a rounding error and left a
// sliver along the eave; stopped short of it, the kneeler's corner hung over
// the eave with nothing under it and drew support from the table.
module eave_flare() {
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh - 0.15, Dh + 0.15)
        // topped 0.3 above the ceiling line, into the slab and the kneelers,
        // which it cuts or which cut it: drawn on the kneelers' own bottom
        // line, the two planes differed by a rounding error and left a sheet
        // along each eave
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
module walls_solid() {
    intersection() {
        brick_skin(z_out(0) + cp_hi + 1);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}
module room() {
    intersection() {
        translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
        below_ceil();
    }
}

// ---- openings ------------------------------------------------------------------------------
// SEGMENTAL ARCH: straight sides under a shallow arc rising 0.35 of the half
// width. Its flat crown is safe only because nothing hangs from it: the pane
// fills the opening behind, and the frame's inner edge is sheared like every
// relief here.
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
// the chapel's lancet
function lancet_pts(a, hgt, ang = 58, n = 12) =
    let (R = 2 * a, t1 = 90 - ang, xt = a - R + R * cos(t1), zt = hgt + R * sin(t1), ap = zt + xt * tan(ang))
    concat([[-a, 0], [a, 0]],
           [for (i = [0 : n]) let (t = t1 * i / n) [a - R + R * cos(t), hgt + R * sin(t)]],
           [[0, ap]],
           [for (i = [n : -1 : 0]) let (t = t1 * i / n) [-(a - R + R * cos(t)), hgt + R * sin(t)]]);
function lancet_top(a, hgt, ang = 58) =
    let (R = 2 * a, t1 = 90 - ang) hgt + R * sin(t1) + (a - R + R * cos(t1)) * tan(ang);
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);

mull = 1.68;
// Frames 2.6 wide standing 0.6 off the brick: at 2.2 and 0.84, the shear
// rose 2.2 across the frame's depth and left the heads' front edges 0.04 mm
// tall -- a knife edge the wall check read as sub-bead all round every head.
fr_w = 2.6;
fr_t = bd + 0.6;            // frame face, 0.6 proud of the brick
sill = 3.4;                 // the sill runs this far below the opening
//   [face, u, z, a, straight height, kind]   kind: "seg" sash window, "lancet" gothic gable window
WINDOWS = [
    [1, -17, 18, 5.2, 13, "seg"],  [1, 17, 18, 5.2, 13, "seg"],  [1, 0, 60.4, 4.0, 11, "lancet"],
    [0,   0, 18, 5.2, 13, "seg"],  [0, 0, 60.4, 4.0, 11, "lancet"],
    [2, -12, 18, 5.2, 13, "seg"],  [2, 12, 18, 5.2, 13, "seg"],
    [3, -12, 18, 5.2, 13, "seg"],  [3, 12, 18, 5.2, 13, "seg"],
];
function is_seg(w) = w[5] == "seg";
function w_top(w) = is_seg(w) ? seg_top(w[3], w[4]) : lancet_top(w[3], w[4]);
module win_outline(w) { polygon(is_seg(w) ? seg_pts(w[3], w[4]) : lancet_pts(w[3], w[4])); }
// A sash window: mullion and a meeting rail. The rail is a flat bar only
// where it is on the pane; its underside is sheared like the frames.
// A lancet: mullion forking at the spring into a Y at 62 deg.
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, is_seg(w) ? 40 : w[4] + mull + 3]);
    if (is_seg(w)) translate([-20, w[4] * 0.55]) square([40, 2.2]);
    else for (s = [-1, 1]) translate([0, w[4]]) rotate(s < 0 ? 180 - 62 : 62)
        translate([0, -mull/2]) square([3 * w[3], mull]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_outer(w) {
    offset(r = fr_w) win_outline(w);
    if (is_seg(w)) translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]);
}
module keystone(w) {
    translate([0, seg_top(w[3], w[4]) - 1.2])
        polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
}
module frame_holes() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
    nf(1, 0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
}

door_a = 6.5;
door_h = 18;
module openings() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
    nf(1, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(arch_pts(door_a, door_h));
}

// ---- door ------------------------------------------------------------------------------------
// A black door: the slate filament. Two tall panels, their heads pointed at
// 60 deg so no recess has a flat ceiling.
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() {
    // 1.73 thick, standing 0.2 proud of the plan: at 1.48, the panels left
    // 1.08 mm of door, under the 1.2 floor. Its back stops 0.15 short of the
    // room: flush with it, its corners fell on the line where the snow base
    // meets the wall inside and left zero-area faces along it.
    nf(1, 0, plinth_h) translate([0, 0, -wall + 0.15]) difference() {
        linear_extrude(wall + 0.05) union() {
            // sunk 0.3 into the snow: standing on it, its foot met the base's
            // top along the room's edge and left zero-area faces. It fills the
            // whole arch and 0.2 past it into the wall: the chapel's leaf
            // stopped 0.2 short of a lancet's head, but a round arch's crown is
            // flat, and over that gap it was an overhang the width of the door;
            // cut exactly to the arch, its edges and the wall's met in slivers.
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
        }
        translate([0, 0, wall - 0.35]) linear_extrude(1) {
            panel2d(-4.6, -1.0, 1.8, 6.2);  panel2d(1.0, 4.6, 1.8, 6.2);
        }
    }
}
module door_frame() {
    nf(1, 0, plinth_h) relief_up(-0.4, fr_t) {
        intersection() { offset(r = 1.8) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
        translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
    }
}
// The wreath hangs on the door above the panels: a ring, standing 1.4 off the
// leaf, and a red bow (the brick filament) at its foot.
wr_z = plinth_h + door_h - 1;
module wreath() nf(1, 0, wr_z) relief_up(-0.4, bd + 0.6) { circle(r = 4.3); circle(r = 2.3); }
module bow2d() {
    polygon([[0, 0], [-2.6, 1.3], [-2.6, -1.3]]);  polygon([[0, 0], [2.6, 1.3], [2.6, -1.3]]);
    circle(r = 0.9);
    polygon([[-0.4, 0], [-1.4, -2.2], [-0.5, -2.2], [0.1, -0.6]]);
    polygon([[0.4, 0], [1.4, -2.2], [0.5, -2.2], [-0.1, -0.6]]);
}
// on the leaf, not on the wreath: stood off the wreath's face, the tails
// below the ring had only air behind them
module wreath_bow() nf(1, 0, wr_z - 4.3) relief_up(-0.4, bd + 1.0) bow2d();

// ---- the garland over the door -----------------------------------------------------------------
// A swag dipping 3 mm between two bows, on the brick between the door's arch
// and the gable window.
gz = plinth_h + door_h + door_a + 8;
g_half = 12;
function g_y(x) = -3 * (1 - pow(x / g_half, 2));
module garland2d() {
    polygon(concat([for (i = [0 : 24]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) + 1.6]],
                   [for (i = [24 : -1 : 0]) let (x = -g_half + 2 * g_half * i / 24) [x, g_y(x) - 1.6]]));
    for (s = [-1, 1]) translate([s * g_half, 0]) circle(r = 2.4);
}
module garland() nf(1, 0, gz) relief_up(-0.4, bd + 1.0) garland2d();
// Raised from the wall like every relief, not stood on the garland's face:
// the garland's own sheared underside falls away behind them, and stood on it
// the bows hung over air and drew a column of support from the snow up.
module garland_bows() for (s = [-1, 1]) nf(1, s * g_half, gz + 0.4) relief_up(-0.4, bd + 1.6) scale(0.8) bow2d();

// ---- window boxes -------------------------------------------------------------------------------
// Under the two front windows: an evergreen box with sprigs standing up along
// its top, hung below the sill.
module box2d(w) {
    bw = w[3] + fr_w + 0.4;
    // 0.9 up behind the sill, the sprigs standing in front of it: stopped at
    // the sill's foot, the sill's sheared underside left a chip of brick
    // loose between every pair of sprigs
    translate([-bw, -sill - 4.4]) square([2 * bw, 4.4 + 0.9]);
    for (i = [0 : 5]) let (x = -bw + 1.2 + i * (2 * bw - 2.4) / 5)
        translate([x, -sill + 0.7]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_boxes() for (w = WINDOWS) if (w[0] == 1 && is_seg(w)) nf(w[0], w[1], w[2]) relief_up(-0.4, bd + 1.4) box2d(w);

// ---- icicles ---------------------------------------------------------------------------------------
// Hung from the eave soffit's foot on both side walls: raised on the brick,
// sheared underneath like every relief, tips rounded to 0.5 mm so they print.
IC = [for (i = [0 : 16]) let (r = rands(0, 1, 2, 40 + i)) [-Dh + 2.4 + i * (D - 4.8) / 16, 2.8 + 2.6 * r[0], 1.8 + 0.6 * r[1]]];
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
module icicles() for (f = [2, 3], c = IC) nf(f, c[0], zf0 + 1) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);

// ---- bargeboards -------------------------------------------------------------------------------------
// The chapel's coping over each gable, grown into a Victorian bargeboard: a
// board down the rake on the gable face, its hem a row of scallops, and a
// finial at the peak. The proud part's underside rises 58 deg outward (the
// chapel's coping shear), and so do the scallops' bottoms. It was pierced
// with diamonds as well; their sheared edges left slivers of board 0.4 mm
// thick above every hole, and they went.
bb_h  = 6.2;                // board depth below the roof's top line, vertically
bb_t  = 1.3;                // board face, proud of the brick
sc_r  = 1.9;
sc_ds = 4.3;                // scallop spacing along the slope
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
function sc_pts() = [for (i = [1 : 20]) let (s = i * sc_ds, x = s * cos(r_ang)) if (x < Wh - 2.6) x];
module board2d(ext) {
    X = Wh - 1;
    // topped 0.3 under the coping's cap: level with it, the board's end met
    // the cap's top edge and left zero-area faces
    T = cp_hi - 0.3 + ext;
    polygon([[-X, z_out(X) + T], [0, z_out(0) + T], [X, z_out(X) + T],
             [X, z_out(X) - bb_h + sc_r], [0, z_out(0) - bb_h + sc_r], [-X, z_out(X) - bb_h + sc_r]]);
    for (x = concat([0], sc_pts(), [for (x = sc_pts()) -x])) translate([x, z_out(x) - bb_h + sc_r]) circle(r = sc_r);
}
module bargeboards() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0]) {
        // 0.3 in past the wall's inner face, over the roof (which cuts it)
        // and into the snow: ended on the wall's own face, the two planes
        // differed by a rounding error and the brick left slivers along it
        xz(Dh - wall - 0.3, Dh - 0.05) gable_poly(cp_lo, cp_hi);
        // The chapel's coping intersected the board with a sheared copy of
        // itself. With scallops that fails: the sheared copy of a scallop
        // rises into the unsheared band above it, and their overlap has the
        // band's FLAT underside (a 0.66 mm notch, 29,000 support moves). So
        // the unsheared term is the board run down to the table, as relief_up
        // does: only the sheared copy has an underside.
        intersection() {
            xz(Dh - 0.1, Dh + bd + bb_t) minkowski() { board2d(0); translate([-0.01, -60]) square([0.02, 60]); }
            multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
                xz(Dh - 1, Dh + 4) board2d(10);
        }
    }
}
// Finial: a square post standing on each gable's peak, pointed at 60 deg.
fin_z = z_out(0) + cp_hi;
module finials() {
    // footed 2.8 down: at 1.4 the post's corners stood over the coping's
    // slopes, which fall 2.1 in the post's half-width
    for (s = [-1, 1]) translate([0, s * (Dh - 0.2), fin_z - 2.8]) {
        translate([-1.3, -1.3, 0]) cube([2.6, 2.6, 7.8]);
        translate([0, 0, 7.8]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0, h = 1.3 * tan(60) * 1.2, $fn = 4);
    }
}

// ---- roof -----------------------------------------------------------------------------------------------
// The slab and slates run 0.4 into the gables' copings, under them: ended on
// the coping's face, the snow between them was cut to zero-thickness sheets
// where the two planes differed by a rounding error.
y_rr = y_r + 0.4;
module slab() xz(-y_rr, y_rr) polygon([[-xe, fl_xe], [-xf, z_ceil(xf)], [0, z_ceil(0)], [xf, z_ceil(xf)], [xe, fl_xe],
                                     [xe, z_out(xe)], [0, z_out(0)], [-xe, z_out(xe)]]);
sh_c = 2.35;
function sh_d(k) = min(k * sh_c, xe - 0.6);
module slates() {
    nk = ceil((xe - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (x0 = s * (xe - sh_d(k)), x1 = s * (xe - min(sh_d(k + 1) + 0.5, xe - 0.6)))
        xz(-y_rr, y_rr) polygon([[x0, z_out(x0) - 1.0], [x0, z_out(x0) + 1.0], [x1, z_out(x1) + 0.05], [x1, z_out(x1) - 1.0]]);
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0) + 1.4], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
// SNOW on the upper roof, down to a wavy line about 40% of the way to the
// eaves: a blanket 1 mm over the slate butts, thickest at the ridge. Its
// lower edge is vertical -- cut straight down -- so nothing about it hangs.
sn_x = 13.5;
function sn_edge(y) = sn_x + 2.2 * sin(y * 17) + 1.3 * sin(y * 41 + 60);
module snow_roof() {
    intersection() {
        // past the slab's end, inside the coping: ended with the slab, the two
        // cut planes differed by a rounding error and left sheets
        xz(-y_rr - 0.4, y_rr + 0.4) polygon([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                               [xe, z_out(xe) + 2.0], [3, z_out(3) + 2.0], [0, z_out(0) + 2.4], [-3, z_out(3) + 2.0], [-xe, z_out(xe) + 2.0]]);
        translate([0, 0, 40]) linear_extrude(100)
            polygon(concat([for (i = [0 : 40]) let (y = -Dh + 2 * Dh * i / 40) [sn_edge(y), y]],
                           [for (i = [40 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 40) [-sn_edge(-y), y]]));
    }
}

// ---- chimney --------------------------------------------------------------------------------------------
// Back left, rising from the slope. It starts at the ceiling plane, which
// prints like the rest of the roof's underside.
ch = [-19.5, -10, 8, 15];   // x0, x1, y0, y1
ch_top = 96;
module chimney() {
    difference() {
        union() {
            translate([ch[0], ch[2], 40]) cube([ch[1] - ch[0], ch[3] - ch[2], ch_top - 40]);
            // the cap: out 0.8 on a 58 deg underside, then 1.6 straight
            hull() {
                translate([ch[0], ch[2], ch_top - 1.3]) cube([ch[1] - ch[0], ch[3] - ch[2], 0.01]);
                translate([ch[0] - 0.8, ch[2] - 0.8, ch_top]) cube([ch[1] - ch[0] + 1.6, ch[3] - ch[2] + 1.6, 1.6]);
            }
            for (x = [ch[0] + 2.4, ch[1] - 2.4]) translate([x, (ch[2] + ch[3]) / 2, ch_top + 1.6 - 0.2])
                cylinder(d = 3.4, h = 4.6, $fn = 32);
        }
        below_ceil();
        for (x = [ch[0] + 2.4, ch[1] - 2.4]) translate([x, (ch[2] + ch[3]) / 2, ch_top + 4]) cylinder(d = 1.8, h = 5, $fn = 24);
    }
}
module chimney_col() translate([ch[0], ch[2], 40]) cube([ch[1] - ch[0], ch[3] - ch[2], 80]);

// ---- snow base ------------------------------------------------------------------------------------------
// The 8 mm street plinth, as snow: a rounded apron, deepest in front of the
// door, with drifts banked against the walls.
module base2d() {
    offset(r = 2.5) offset(delta = -2.5) union() {
        translate([-Wh - 4.5, -Dh - 12]) square([W + 9, D + 16.5]);
        for (p = [[-Wh - 3, -Dh - 8, 4.5], [Wh + 3.5, -Dh - 2, 4], [Wh + 3, Dh - 6, 4.5], [-Wh - 3, Dh - 2, 3.5],
                  [-14, Dh + 3.5, 4], [18, Dh + 3.5, 3.5], [-Wh - 3.5, 4, 3.5], [Wh + 3.5, 12, 3.5]])
            translate([p[0], p[1]]) circle(r = p[2]);
    }
}
DRIFTS = [[-Wh - 1, -Dh + 7, 7, 4, 3.2], [Wh + 1, Dh - 10, 8, 4, 3.6], [-8, Dh + 1, 7, 3.5, 2.8],
          [Wh + 1, -Dh + 1, 5, 4, 2.6], [-Wh - 1, Dh - 4, 5, 3.5, 2.4]];
module base() {
    linear_extrude(plinth_h) base2d();
    // kept inside the base's outline: run past its edge, a drift's side hung
    // over the table and drew support from the bed up
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.01]) intersection() {
            scale([d[2], d[3], d[4]]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -0.6) base2d();
    }
}

// ---- mark -----------------------------------------------------------------------------------------------
module brand_mark() {
    translate([0, -Dh - 6.2, -0.5]) linear_extrude(1.3)
        mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black",
                               halign = "center", valign = "center", spacing = 1.16);
}

// ---- joints ---------------------------------------------------------------------------------------------
function frame_box(f, w) = let (lu = loc(f, w[1]), h = w[3] + fr_w + 2.5)
    [lu - h, lu + h, w[2] - sill - 5, w[2] + w_top(w) + fr_w + 4];
function face_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    f >= 2 ? [[-100, 100, zf0 - 6, 300]] : [],
    f == 1 ? [[-door_a - 3.5, door_a + 3.5, 0, plinth_h + door_h + door_a + 3.5],
              [-g_half - 3, g_half + 3, gz - 5, gz + 4]] : []);
module joints() {
    for (f = [0 : 3]) wall_joints(f, f < 2 ? z_out(0) + cp_hi : H + 2, face_boxes(f));
}

// ---- parts ----------------------------------------------------------------------------------------------
module body_raw() { walls_solid(); chimney(); wreath_bow(); garland_bows(); }
module roof_raw() {
    difference() { union() { slab(); slates(); } room(); chimney_col(); }
    door_leaf();
}
module accent_raw() { wreath(); garland(); window_boxes(); }
module trim_raw() {
    difference() {
        union() {
            base();
            quoins();
            eave_flare();
            icicles();
            bargeboards();
            finials();
            difference() { snow_roof(); chimney_col(); }
            for (w = WINDOWS) nf(w[0], w[1], w[2]) {
                relief_up(-0.4, fr_t) { frame_outer(w); offset(r = 0.3) win_outline(w); }
                if (is_seg(w)) relief_up(-0.4, fr_t + 0.5) keystone(w);
                relief_up(-0.4, bd) win_muntins(w, 0.6);
                translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
            }
            door_frame();
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
        room(); openings(); frame_holes(); joints(); trim_raw(); accent_raw(); roof_raw();
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
else {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
