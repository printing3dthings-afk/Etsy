// Victorian Shop-House -- the Dickens Victorian village's first building with
// "more shape" (Scott, 2026-09-30, picked from four shapes against his
// reference photos in ../../references/). A two-storey shop: a brick shop floor
// with a bay window and a panelled door; above it a white plaster storey with
// dark timbers that JUTS OUT over the street on brackets; a steep front gable
// with a scalloped bargeboard and a finial; a tall stepped chimney stack. On a
// snow base.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// The machinery is the first Victorian cottage's (../cottage/victorian_cottage
// .scad), itself the chapel's; every trap it met is written up in
// .claude/skills/3d-print-design/SKILL.md Technique 79 and applied here from
// the start: parts overlap and are cut by priority, never abut; reliefs rise
// from the wall plane; nothing reaches below a ceiling.
//
// COLOUR PARTS, ONE PRINT (victorian_shop_house.3mf), priority roof > accent >
// trim > body:
//   body    brick shop floor, the bay's stall riser, the chimney, the step
//   roof    slate roof, and the "timber": the jetty's beam, cove and
//           brackets, the upper storey's framing, window frames and lattice,
//           the door
//   trim    snow base and drifts, the upper storey's plaster walls, soffits,
//           kneelers, bargeboards and finials, snow on the roof, every pane,
//           the shop floor's window and door frames
//   accent  evergreen: the bay window's frame and bars, the wreath, the
//           window boxes
//
// FRAMES. The shop floor is the brick box, centred on the origin. The upper
// storey and roof are the cottage's roof machinery in their own frame, moved
// forward by the jetty: upper() puts a child there.

include <BOSL2/std.scad>
include <../../../lattice_lib.scad>   // rrect_pts

$fa = 4;  $fs = 0.4;
part = "all";

// ---- the shop floor --------------------------------------------------------------
W        = 56;              // across the front, both storeys
Wh       = W/2;
Dg       = 50;              // shop floor depth
Dgh      = Dg/2;
wall     = 1.68;
corner_r = 1;
plinth_h = 8;
H1       = 38;              // top of the shop floor; the jetty starts here
SH       = 1.2;

// ---- brick -----------------------------------------------------------------------
bd    = 0.6;
bp    = 2.6;
br    = bd * tan(58);
bj    = 0.6;
bl    = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);

// ---- the upper storey and roof -------------------------------------------------------
J     = 4;                  // the jetty: the upper storey stands this far out in front
Du    = Dgh + J/2;          // its half-depth ...
yc    = -J/2;               // ... about this centre
H     = 70;                 // its eave (the side windows' heads clear the eave's flare)
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + e;             // plaster: no brick face
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Du - wall;
y_rr  = y_r + 0.4;
cp_lo = -0.2;  cp_hi = 2.6;
module upper() translate([0, yc, 0]) children();

// ---- placement -------------------------------------------------------------------------
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module ftf(cy, hy, face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, cy + hy, z] : face == 1 ? [u, cy - hy, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module nf(face, u, z) ftf(0, Dgh, face, u, z) children();      // shop floor
module uf(face, u, z) ftf(yc, Du, face, u, z) children();      // upper storey
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
// relief_up's straight term is smeared 60 down, so anything standing above a
// member lifts that member's top with the shear too. For framing, where the
// top plate stands over everything, that left every beam's top a sloping
// knife edge 0.18 thick; here the straight term is only widened sideways.
module relief_flat(d0, d1, sh = SH) intersection() {
    translate([0, 0, d0]) linear_extrude(d1 - d0) minkowski() { children(); translate([-0.2, -0.01]) square([0.4, 0.01]); }
    shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children();
}
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// ---- the shop floor's brick ---------------------------------------------------------------
function rpts(w, d, g, z) = [for (p = rrect_pts(w + 2*g, d + 2*g, corner_r + g, 5)) [p[0], p[1], z]];
module brick_skin(ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(W, Dg, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(W, Dg, g, z)],
        [rpts(W, Dg, 0, ztop + 2)]), slices = 0);
}
// run 2 past H1, into the upper storey, which cuts it
module shop_walls() intersection() { brick_skin(H1 + 2); translate([-50, -50, 0]) cube([100, 100, H1 + 2]); }

function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
module wall_joints(f, boxes) {
    L = (f < 2 ? Wh : Dgh) - 3;
    nf(f, 0, 0)
        for (k = [1 : nc(H1) - 1]) let (z0 = zc(k), z1 = zc(k + 1), s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(u, z0, z1, boxes))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}

// ---- the upper storey: the cottage's roof machinery, in upper() -----------------------------
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Du - wall, Du + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module kneelers() {
    for (s = [-1, 1], m = [0, 1]) mirror([0, s < 0 ? 1 : 0, 0]) mirror([m, 0, 0])
        xz(Du - wall, Du - 0.05) polygon([[Wh - 0.3, z_ceil(Wh - 0.3)], [xf, z_ceil(xf)], [xe, fl_xe],
                                        [xe, z_out(xe) + 1], [Wh - 0.3, z_out(Wh - 0.3) + 1]]);
}
module eave_flare() {
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Du - 0.15, Du + 0.15)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
module upper_walls() {
    intersection() {
        translate([0, 0, H1]) linear_extrude(200) rect([W, 2 * Du], rounding = corner_r);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
    eave_flare();
}

// ---- rooms --------------------------------------------------------------------------------
module shop_room() translate([-x_in, -(Dgh - wall), -2]) cube([2 * x_in, 2 * (Dgh - wall), H1 + 4]);
module upper_room() upper() intersection() {
    translate([-x_in, -y_r, H1]) cube([2 * x_in, 2 * y_r, 200]);
    below_ceil();
}
module room() { shop_room(); upper_room(); upper() dm_room(); }

// ---- the jetty ------------------------------------------------------------------------------
// The upper storey's front stands J out over the street. Under it a cove
// rises from the brick at 62 deg to the jetty's face, and five brackets at
// 50 deg stand under the beam. Both run 0.4 into the brick and 0.3 up into
// the plaster, which they cut: overlapping, never abutting.
cv_ang = 62;
cv_z0  = H1 - J * tan(cv_ang);     // the cove's foot on the brick
module cove() yz(-Wh, Wh) polygon([[-Dgh + 0.45, cv_z0 - 0.45 * tan(cv_ang)], [-Dgh + 0.45, H1 + 0.3],
                                   [-(Dgh + J), H1 + 0.3], [-(Dgh + J), H1]]);
BRK = [-26, -1.8, 13, 26];         // clear of the bay, the door and the window, and off the corner posts' edges
bk_ang = 50;
module brackets() for (x = BRK) yz(x - 1.2, x + 1.2)
    polygon([[-Dgh + 0.4, H1 - (J + 1.0) * tan(bk_ang)], [-Dgh + 0.4, H1 + 1.6], [-(Dgh + J + 0.6), H1 + 1.6],
             [-(Dgh + J + 0.6), H1 - 0.01]]);

// ---- window shapes --------------------------------------------------------------------------
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
function rect_pts(a, hgt) = [[-a, 0], [a, 0], [a, hgt], [-a, hgt]];
mull = 1.68;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.3;                 // 3.4 put the sills' feet exactly on a brick course

// SHOP FLOOR windows: segmental sashes in white frames with keystones.
//   [face, u, z, a, h]
SWIN = [ [1, 19.6, 16, 3.6, 11],
         [0, 0, 17, 5.2, 13],  [2, 0, 17, 5.2, 13],  [3, 0, 17, 5.2, 13] ];
module swin_outline(w) polygon(seg_pts(w[3], w[4]));
module swin_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, w[4] * 0.55]) square([40, 2.2]);
}
module sframe_outer(w) {
    offset(r = fr_w) swin_outline(w);
    translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]);
}
module keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2])
    polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);

// UPPER STOREY windows: square-headed casements with diamond leading, in
// timber frames. The leading is bars at 38 deg from vertical: tall
// diamonds, and steep enough to print (at 55 deg every bar needed support).
//   [face, u, z, a, h]    u on the side faces is world y
// The front windows' boxes sit on the jetty's sill beam, clear of the bay.
UWIN = [ [1, -12, H1 + 9, 5, 12],  [1, 12, H1 + 9, 5, 12],  [1, 0, 82, 3.5, 8],
         [0, 0, H1 + 9, 5, 12],  [0, 0, 82, 3.5, 8],
         [2, yc, H1 + 9, 5, 11.2],  [3, yc, H1 + 9, 5, 11.2] ];
uf_w = 2.2;                 // timber frame width
tb_t = 0.8;                 // timbers stand this far off the plaster
module uwin_outline(w) polygon(rect_pts(w[3], w[4]));
module lattice(w) {
    for (i = [-5 : 5], s = [-1, 1]) translate([i * 4.2, 0]) rotate(s * 38) translate([-0.5, -30]) square([1.0, 60]);
    translate([-0.9, -3]) square([1.8, 40]);
}

// ---- timber framing on the upper storey --------------------------------------------------------
// Posts at the corners and the centre, a sill beam along the jetty's foot, a
// top plate under the eave, and braces. The framing's own outline is drawn
// per face in that face's (u, z); windows sit in the gaps.
module timbers_face(f) {
    L = f < 2 ? Wh : Du;
    hw = L - 0.6;
    union() {
        translate([-hw, H1]) square([2 * hw, 2.4]);                  // sill beam
        translate([-hw, H - 2.2]) square([2 * hw, 2.2]);             // top plate / tie beam
        for (s = [-1, 1]) translate([s * hw - (s > 0 ? 2.4 : 0), H1]) square([2.4, H - H1]);   // corner posts
        if (f < 2) {
            translate([-1.2, H1]) square([2.4, H - H1]);             // centre post
            // braces in the outer bays: from the sill beam by the window up
            // to the top plate by the corner post, 74 deg
            for (s = [-1, 1]) hull() {
                translate([s * 19.6, H1 + 2.2]) square([1.8, 0.1], center = true);
                translate([s * (hw - 3.3), H - 2.1]) square([1.8, 0.1], center = true);
            }
            // the gable: a king post, and two struts rising from its foot
            // toward the rafters at 58 deg. Struts falling from the post to the
            // tie beam ran at 34 deg: their undersides needed support.
            translate([-1.2, H - 1]) square([2.4, z_ceil(0) - H - 3]);
            for (s = [-1, 1]) hull() {
                translate([s * 2, H + 0.6]) square([1.8, 1.8], center = true);
                translate([s * 12, H + 0.6 + 10 * tan(58)]) square([1.8, 1.8], center = true);
            }
        } else {
            for (s = [-1, 1]) hull() {
                translate([s * 8.5, H1 + 2.2]) square([1.8, 0.1], center = true);
                translate([s * (hw - 3.3), H - 2.1]) square([1.8, 0.1], center = true);
            }
        }
    }
}
// The framing on each face, cut back from the windows and kept inside the
// gable: a timber reaching past the plaster would hang.
module timbers() {
    for (f = [0 : 3]) uf(f, f < 2 ? 0 : yc, 0) relief_flat(-0.4, tb_t) difference() {
        intersection() {
            timbers_face(f);
            // below the roof's top line (and the bargeboard, which covers it)
            if (f < 2) polygon([[-xe, -5], [xe, -5], [xe, z_ceil(xe) - 0.5], [0, z_ceil(0) - 0.5], [-xe, z_ceil(xe) - 0.5]]);
            else translate([-100, -5]) square([200, H + 5]);
        }
        for (w = UWIN) if (w[0] == f) translate([loc(f, w[1] - (f < 2 ? 0 : yc)), w[2]]) offset(r = uf_w + 0.6) uwin_outline(w);
    }
}

// ---- the shop floor's front: bay window and door ---------------------------------------------------
// THE BAY. Canted sides, standing J out under the jetty, so its fascia runs
// straight up into the cove. A brick stall riser, then an evergreen frame
// with a big glazed front and a fascia over it.
BAY = [[-24, -Dgh + 0.5], [-4, -Dgh + 0.5], [-7, -Dgh - J], [-21, -Dgh - J]];
by_riser = 15;              // top of the brick stall riser
by_win   = [by_riser + 1.4, 29.4];   // glazing, z0..z1
bw_a     = 5.2;             // glazing half-width, on the bay's front face
bw_u     = -14;             // ... and centre
module bay_solid() translate([0, 0, plinth_h - 0.5]) linear_extrude(H1 + 0.3 - plinth_h + 0.5) polygon(BAY);
// The bay's inside, open to the shop. Its ceiling rises at 55 deg from the
// front glazing's head into the room, so it and the wall's head behind the
// bay are slopes, not a bridge.
by_ceil0 = by_win[1] + 1.2;
module bay_room() intersection() {
    translate([0, 0, plinth_h]) linear_extrude(60) union() {
        offset(delta = -wall) polygon(BAY);
        // through the shop wall into the bay: a short one sealed the bay off,
        // a wide one shaved its canted walls to 0.6
        translate([-20.8, -Dgh - 1.4]) square([13.6, 5.2]);
    }
    yz(-30, 0) polygon([[-40, -5], [-40, by_ceil0 - (40 - (Dgh + J - wall)) * tan(55)],
                        [-18, by_ceil0 + (Dgh + J - wall - 18) * tan(55)], [-18, -5]]);
}
module bay_face() translate([bw_u, -Dgh - J, by_win[0]]) rotate([90, 0, 0]) children();
module bay_win_outline() polygon(rect_pts(bw_a, by_win[1] - by_win[0]));
module bay_bars() {
    for (x = [-bw_a / 3, bw_a / 3]) translate([x - 0.8, -3]) square([1.6, 40]);
    translate([-10, (by_win[1] - by_win[0]) * 0.56]) square([20, 2.0]);
}

// THE DOOR: square-headed, with a fanlight over it, under the cove.
dr_u = 4;  dr_a = 4.6;  dr_h = 16;  dr_f = 2.6;       // leaf 16 high, fanlight 2.6 over it
dr_top = plinth_h + dr_h + 0.6 + dr_f;
module door_outline() polygon(rect_pts(dr_a, dr_h + 0.6 + dr_f));
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module door_leaf() nf(1, dr_u, plinth_h) difference() {
    translate([0, 0, -wall + 0.15]) linear_extrude(wall + 0.05)
        translate([-dr_a - 0.2, -0.3]) square([2 * dr_a + 0.4, dr_h + 0.3]);
    translate([0, 0, -0.2]) linear_extrude(1) {
        panel2d(-3.4, -0.8, 1.6, 6.4);  panel2d(0.8, 3.4, 1.6, 6.4);
        panel2d(-3.4, -0.8, 9.4, 12.4); panel2d(0.8, 3.4, 9.4, 12.4);
    }
}
module door_frame() nf(1, dr_u, plinth_h) relief_up(-0.4, fr_t) {
    union() {
        translate([-dr_a - 1.8, -0.5]) square([2 * dr_a + 3.6, dr_h + 0.6 + dr_f + 1.8 + 0.5 + SH * (fr_t + 0.4)]);
    }
    translate([-dr_a + 0.3, -1]) square([2 * dr_a - 0.6, dr_h + 0.6 + dr_f + 0.7]);
}
// the fanlight's glazing and the transom bar between it and the door
module fanlight() nf(1, dr_u, plinth_h + dr_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
    translate([-dr_a - 0.6, 0]) square([2 * dr_a + 1.2, 0.6 + dr_f + 0.6]);
module transom() nf(1, dr_u, plinth_h + dr_h) relief_up(-0.4, fr_t) translate([-dr_a, 0]) square([2 * dr_a, 0.8]);
wr_z = plinth_h + 10.5;
module wreath() nf(1, dr_u, wr_z) relief_up(-0.4, bd + 0.6) { circle(r = 3.3); circle(r = 1.7); }
module step() translate([dr_u - dr_a - 1.4, -Dgh - 3.2, plinth_h - 0.5]) cube([2 * dr_a + 2.8, 3.2 + 0.5, 1.9]);

// ---- window boxes under the upper front windows ---------------------------------------------
module box2d(a) {
    bw = a + uf_w + 0.4;        // short of the timbers' cut-back, not on it
    translate([-bw, -uf_w - 4.2]) square([2 * bw, 4.2 + uf_w]);
    for (i = [0 : 4]) let (x = -bw + 1.3 + i * (2 * bw - 2.6) / 4)
        translate([x, -0.4]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_boxes() for (w = UWIN) if (w[0] == 1 && w[2] < H) uf(1, w[1], w[2]) relief_up(-0.4, tb_t + 1.2) box2d(w[3]);

// ---- openings ------------------------------------------------------------------------------------
module shop_openings() {
    for (w = SWIN) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) swin_outline(w);
    nf(1, dr_u, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) door_outline();
}
module shop_frame_holes() {
    for (w = SWIN) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) swin_outline(w);
    nf(1, dr_u, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) door_outline();
}
module upper_openings() for (w = UWIN) uf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 5) uwin_outline(w);

// ---- bargeboards and finials (the cottage's), in upper() ---------------------------------------------
bb_h  = 6.2;
bb_t  = 1.3;
sc_r  = 1.9;
sc_ds = 4.3;
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
        xz(Du - wall - 0.3, Du - 0.05) gable_poly(cp_lo, cp_hi);
        intersection() {
            xz(Du - 0.1, Du + bb_t) minkowski() { board2d(0); translate([-0.01, -60]) square([0.02, 60]); }
            multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Du], [0, 0, 0, 1]])
                xz(Du - 1, Du + 4) board2d(10);
        }
    }
}
fin_z = z_out(0) + cp_hi;
module finials() for (s = [-1, 1]) translate([0, s * (Du - 0.2), fin_z - 2.8]) {
    translate([-1.3, -1.3, 0]) cube([2.6, 2.6, 7.8]);
    translate([0, 0, 7.8]) rotate([0, 0, 45]) cylinder(r1 = 1.3 * sqrt(2), r2 = 0, h = 1.3 * tan(60) * 1.2, $fn = 4);
}

// ---- roof (the cottage's), in upper() ------------------------------------------------------------------
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
sn_x = 13;
function sn_edge(y) = sn_x + 2.2 * sin(y * 17) + 1.3 * sin(y * 41 + 60);
module snow_roof() intersection() {
    xz(-y_rr - 0.4, y_rr + 0.4) polygon([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                           [xe, z_out(xe) + 2.0], [3, z_out(3) + 2.0], [0, z_out(0) + 2.4], [-3, z_out(3) + 2.0], [-xe, z_out(xe) + 2.0]]);
    translate([0, 0, 40]) linear_extrude(120)
        polygon(concat([for (i = [0 : 40]) let (y = -Du + 2 * Du * i / 40) [sn_edge(y), y]],
                       [for (i = [40 : -1 : 0]) let (y = -Du + 2 * Du * i / 40) [-sn_edge(-y), y]]));
}

// ---- the chimney ------------------------------------------------------------------------------------
// A tall stack through the right slope, behind the ridge's middle: a wide
// lower stack, a 60 deg weathering, a narrower upper stack, a corbelled cap
// and three pots. Its foot is the ceiling plane, cut there.
ch0 = [9, 19, 6, 14];       // x0, x1, y0, y1 of the lower stack (upper frame)
ch1 = [10.2, 17.8, 7, 13];  // ... of the upper stack
ch_w = 108;                 // weathering starts
ch_top = 124;
module chimney() difference() {
    union() {
        translate([ch0[0], ch0[2], 60]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], ch_w - 60]);
        hull() {
            translate([ch0[0], ch0[2], ch_w - 0.01]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 0.01]);
            translate([ch1[0], ch1[2], ch_w + 1.2 * tan(60)]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
        }
        translate([ch1[0], ch1[2], ch_w]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], ch_top - ch_w]);
        hull() {
            translate([ch1[0], ch1[2], ch_top - 1.3]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
            translate([ch1[0] - 0.8, ch1[2] - 0.8, ch_top]) cube([ch1[1] - ch1[0] + 1.6, ch1[3] - ch1[2] + 1.6, 1.6]);
        }
        for (x = [ch1[0] + 1.8, ch1[1] - 1.8]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 1.4])
            cylinder(d = 3.4, h = 4.2, $fn = 32);
    }
    below_ceil();
    for (x = [ch1[0] + 1.8, ch1[1] - 1.8]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 3.4])
        cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimney_col() translate([ch0[0], ch0[2], 60]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 80]);

// ---- the dormer (upper frame) -------------------------------------------------------------------------
// A gabled dormer on the right slope, in front of the chimney: the roof's
// second height. Its roof has the main roof's pitch, so its ceiling and the
// valleys where that meets the main ceiling are all 58 deg slopes. Its walls
// start at the main ceiling and its roof slab is cut there too: nothing of it
// hangs in the room.
dm_c  = -8;                 // centre, y
dm_w  = 7;                  // half-width to the wall's face
dm_in = dm_w - wall;
dm_x  = 21.5;               // front face
dm_x0 = 1;                  // back end, buried in the main roof
dm_e  = 1;                  // its roof's overhang
dm_ze = 98.5;               // its eave (inside the wall)
function dz_ceil(y) = dm_ze + (dm_in - abs(y - dm_c)) * tp;
function dz_out(y)  = dz_ceil(y) + tv;
DMW = [3, 87.4, 8];           // window: half-width, sill, height
dm_fw = 2.0;                // its frame's width
// A frame's head and foot rails thin toward the front (its opening's head
// rises with the shear, and so does its own foot); both are drawn this much
// deeper so they keep a bead there.
hd = SH * (tb_t + 0.4);
module dmf(z) translate([dm_x, dm_c, z]) rotate([0, 0, 90]) rotate([90, 0, 0]) children();
module dm_below(dz) yz(dm_x0 - 1, dm_x + dm_e + 1)
    polygon([[dm_c - 20, 60], [dm_c + 20, 60], [dm_c + 20, dz_ceil(dm_c + 20) + dz], [dm_c, dz_ceil(dm_c) + dz],
             [dm_c - 20, dz_ceil(dm_c - 20) + dz]]);
module dm_room() intersection() {
    translate([dm_x0 - 1, dm_c - dm_in, 60]) cube([dm_x - wall - dm_x0 + 1, 2 * dm_in, 60]);
    dm_below(0);
}
// where the dormer stands: its walls' footprint, up to its roof's top
module dm_env() intersection() {
    translate([dm_x0 - 1, dm_c - dm_w, 60]) cube([dm_x - dm_x0 + 1, 2 * dm_w, 60]);
    dm_below(tv);
}
module dm_walls() difference() {
    intersection() {
        translate([dm_x0, dm_c - dm_w, 60]) cube([dm_x - dm_x0, 2 * dm_w, 60]);
        dm_below(0.4);
    }
    below_ceil();
}
dm_E = dm_w + dm_e;
// Whatever stands forward of the dormer's face has its underside rising at
// SH as it comes forward, like every relief: cut level, the front overhang,
// the verge board and the eaves' ends would each start printing in mid-air.
module dm_front_cut(up = 60) intersection() {
    children();
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [SH, 0, 1, -SH * dm_x], [0, 0, 0, 1]])
        minkowski() { children(); cylinder(r = 0.01, h = up, $fn = 4); }
}
// under each side eave a 52 deg flare from the wall, as under the main eaves:
// cut level, the eave's lowest edge is a line in the air. The slab's own last
// 0.08 continues the flare's slope, as the main slab does (fl_xe): dropping
// to the ceiling line, its tip was a strip starting in mid-air.
dm_yf = dm_E - 0.08;
dm_tip = dz_ceil(dm_c + dm_yf) + (dm_E - dm_yf) * tan(fl_ang);
module dm_slab() difference() {
    dm_front_cut() yz(dm_x0, dm_x + dm_e) polygon([[dm_c - dm_E, dm_tip], [dm_c - dm_yf, dz_ceil(dm_c - dm_yf)], [dm_c, dz_ceil(dm_c)],
                                    [dm_c + dm_yf, dz_ceil(dm_c + dm_yf)], [dm_c + dm_E, dm_tip],
                                    [dm_c + dm_E, dz_out(dm_c + dm_E)], [dm_c, dz_out(dm_c)], [dm_c - dm_E, dz_out(dm_c - dm_E)]]);
    below_ceil();
}
// The flare and the verge board reach this far up into the slab: the slab's
// own underside rises up to SH * dm_e in front of the face, and at 0.3 there
// was an air gap under it.
dm_up = 0.3 + SH * (dm_e + 0.2) + 0.2;
module dm_flare() difference() {
    dm_front_cut() for (m = [0, 1]) translate([0, dm_c, 0]) mirror([0, m, 0]) yz(dm_x0, dm_x + dm_e)
        polygon([[dm_w - 0.3, dz_ceil(dm_c + dm_yf) - (dm_yf - dm_w + 0.3) * tan(fl_ang)], [dm_yf, dz_ceil(dm_c + dm_yf)],
                 [dm_yf, dz_ceil(dm_c + dm_yf) + dm_up], [dm_w - 0.3, dz_ceil(dm_c + dm_w - 0.3) + dm_up]]);
    below_ceil();
}
module dm_slates() difference() {
    nk = ceil((dm_E - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (y0 = s * (dm_E - sh_d(k)), y1 = s * (dm_E - min(sh_d(k + 1) + 0.5, dm_E - 0.6)))
        yz(dm_x0, dm_x + dm_e) translate([dm_c, 0])
            polygon([[y0, dz_out(dm_c + y0) - 1.0], [y0, dz_out(dm_c + y0) + 1.0], [y1, dz_out(dm_c + y1) + 0.05], [y1, dz_out(dm_c + y1) - 1.0]]);
    below_ceil();
}
// a dark verge board under the overhang, round the white gable; it stops at
// the walls' faces, where its ends stand on them
module dm_board() difference() {
    dm_front_cut() yz(dm_x - 0.3, dm_x + dm_e + 0.2) polygon([[dm_c - dm_w, dz_ceil(dm_c - dm_w) - 2.2], [dm_c, dz_ceil(dm_c) - 2.2],
        [dm_c + dm_w, dz_ceil(dm_c + dm_w) - 2.2], [dm_c + dm_w, dz_ceil(dm_c + dm_w) + dm_up], [dm_c, dz_ceil(dm_c) + dm_up],
        [dm_c - dm_w, dz_ceil(dm_c - dm_w) + dm_up]]);
    dm_room();
}
module dm_snow() difference() {
    intersection() {
        // underside follows the roof: a straight one showed flat under the overhang
        yz(dm_x0, dm_x + dm_e) polygon([[dm_c - 5, dz_out(dm_c - 5) - 1.0], [dm_c, dz_out(dm_c) - 1.0], [dm_c + 5, dz_out(dm_c + 5) - 1.0],
            [dm_c + 5, dz_out(dm_c + 5) + 1.8], [dm_c + 1.5, dz_out(dm_c + 1.5) + 2.8], [dm_c - 1.5, dz_out(dm_c + 1.5) + 2.8],
            [dm_c - 5, dz_out(dm_c - 5) + 1.8]]);
        translate([0, 0, 80]) linear_extrude(40) polygon(concat(
            [for (i = [0 : 30]) let (x = dm_x0 + (dm_x + dm_e - dm_x0) * i / 30) [x, dm_c + 3.4 + 0.9 * sin(x * 47)]],
            [for (i = [30 : -1 : 0]) let (x = dm_x0 + (dm_x + dm_e - dm_x0) * i / 30) [x, dm_c - 3.4 - 0.9 * sin(x * 53 + 40)]]));
    }
    below_ceil();
}
module dm_opening() dmf(DMW[1]) translate([0, 0, -wall - 2]) linear_extrude(wall + 5) polygon(rect_pts(DMW[0], DMW[2]));

// ---- snow base -----------------------------------------------------------------------------------------
module base2d() {
    offset(r = 2.5) offset(delta = -2.5) union() {
        translate([-Wh - 4.5, -Dgh - 13]) square([W + 9, Dg + 17.5]);
        for (p = [[-Wh - 3, -Dgh - 9, 4.5], [Wh + 3.5, -Dgh - 3, 4], [Wh + 3, Dgh - 6, 4.5], [-Wh - 3, Dgh - 2, 3.5],
                  [-14, Dgh + 3.5, 4], [18, Dgh + 3.5, 3.5], [-Wh - 3.5, 4, 3.5], [Wh + 3.5, 12, 3.5]])
            translate([p[0], p[1]]) circle(r = p[2]);
    }
}
DRIFTS = [[Wh + 1, Dgh - 10, 8, 4, 3.6], [-8, Dgh + 1, 7, 3.5, 2.8], [-Wh - 1, Dgh - 4, 5, 3.5, 2.4],
          [Wh + 1, -Dgh + 2, 5, 4, 2.6]];
module base() {
    linear_extrude(plinth_h) base2d();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.01]) intersection() {
            scale([d[2], d[3], d[4]]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -0.6) base2d();
    }
}
module brand_mark() translate([0, -Dgh - 8.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- joints ------------------------------------------------------------------------------------------------
function sframe_box(f, w) = let (lu = loc(f, w[1]), h = w[3] + fr_w + 2.5)
    [lu - h, lu + h, w[2] - sill - 5, w[2] + seg_top(w[3], w[4]) + fr_w + 4];
function face_boxes(f) = concat(
    [for (w = SWIN) if (w[0] == f) sframe_box(f, w)],
    f == 1 ? [[-25, -3, 0, 100], [dr_u - dr_a - 3.5, dr_u + dr_a + 3.5, 0, dr_top + 4], [-100, 100, cv_z0 - 4, 100]] : []);
module joints() for (f = [0 : 3]) wall_joints(f, face_boxes(f));

// ---- parts ----------------------------------------------------------------------------------------------------
module body_raw() {
    shop_walls();
    intersection() { bay_solid(); translate([-50, -50, 0]) cube([100, 100, by_riser]); }
    upper() chimney();
    step();
}
module roof_raw() {
    difference() { upper() union() { slab(); difference() { slates(); dm_env(); } } room(); upper() chimney_col(); }
    upper() {
        difference() { union() { dm_slab(); dm_slates(); } dm_room(); }
        dm_board();
        dmf(DMW[1]) {
            relief_up(-0.4, tb_t) { offset(r = dm_fw) translate([0, -hd]) polygon(rect_pts(DMW[0], DMW[2] + 2 * hd)); offset(r = 0.3) polygon(rect_pts(DMW[0], DMW[2])); }
            relief_up(-0.4, 0.4) intersection() { offset(r = 0.6) polygon(rect_pts(DMW[0], DMW[2])); lattice(DMW); }
        }
        bargeboards();
        finials();
    }
    // cut by the rooms: where the bay opens the shop wall, the cove's buried foot
    // would hang in the air
    difference() { union() { cove(); brackets(); } room(); bay_room(); }
    timbers();
    for (w = UWIN) uf(w[0], w[1], w[2]) {
        relief_up(-0.4, tb_t) { offset(r = uf_w) translate([0, -hd]) polygon(rect_pts(w[3], w[4] + 2 * hd)); offset(r = 0.3) uwin_outline(w); }
        relief_up(-0.4, 0.4) intersection() { offset(r = 0.6) uwin_outline(w); lattice(w); }
    }
    door_leaf();
}
module accent_raw() {
    difference() {
        intersection() { bay_solid(); translate([-50, -50, by_riser]) cube([100, 100, 100]); }
        bay_room();
        bay_face() translate([0, 0, -wall - 2]) linear_extrude(wall + 4) bay_win_outline();
    }
    bay_face() relief_up(-0.4, 0.6) intersection() { offset(r = 0.6) bay_win_outline(); bay_bars(); }
    wreath();
    window_boxes();
}
module trim_raw() {
    difference() {
        union() {
            base();
            upper() {
                upper_walls();
                dm_walls();
                dm_flare();
                difference() { snow_roof(); chimney_col(); dm_env(); }
                dm_snow();
            }
            for (w = SWIN) nf(w[0], w[1], w[2]) {
                relief_up(-0.4, fr_t) { sframe_outer(w); offset(r = 0.3) swin_outline(w); }
                relief_up(-0.4, fr_t + 0.5) keystone(w);
                relief_up(-0.4, bd) intersection() { offset(r = 0.6) swin_outline(w); swin_bars(w); }
                translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) swin_outline(w);
            }
            bay_face() translate([0, 0, -wall]) linear_extrude(wall) offset(r = 0.6) bay_win_outline();
            door_frame();
            transom();
            fanlight();
        }
        room();
        bay_room();
        upper_openings_cut();
        brand_mark();
    }
    // the panes go back in after the openings are cut
    // Flush with the wall's face: set 0.2 back like the shop windows', the
    // square heads above them were flat ledges and shut in air pockets.
    for (w = UWIN) uf(w[0], w[1], w[2]) translate([0, 0, -wall]) linear_extrude(wall) offset(r = 0.6) uwin_outline(w);
    upper() dmf(DMW[1]) translate([0, 0, -wall]) linear_extrude(wall) offset(r = 0.6) polygon(rect_pts(DMW[0], DMW[2]));
}
// The upper storey's openings cut its plaster only down to the panes' plane:
// every pane is added back after.
module upper_openings_cut() { upper_openings(); upper() dm_opening(); }
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); bay_room(); shop_openings(); shop_frame_holes(); joints(); trim_raw(); accent_raw(); roof_raw();
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
