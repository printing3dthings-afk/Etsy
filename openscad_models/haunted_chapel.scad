// Haunted Chapel lantern -- building #2 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). STONE walls, pointed LANCET windows, a
// STEEP GABLE with coped stone parapets at both ends, and a square bell tower
// on the front-left corner that has CRACKED above the roofline and tipped
// away from the nave. A hollow shell lit from inside by a battery LED
// tealight: open base, true through-cut windows; the tower is hollow and open
// to the nave, so the belfry glows too.
//
// Built to the town's variety plan (Scott, 2026-09-25): no two buildings
// share a wall texture, a window shape or a roof shape. The relief, frame and
// inlay machinery is the bakery's (haunted_bakery.scad) and its WHY comments
// are there; the V-course walls are the post office's brick, re-cut as stone.
//
// COLOUR PARTS, ONE PRINT (haunted_chapel.3mf):
//   body    stone walls, tower, plinth, step, the gables' kneelers
//   roof    roof slab, slate courses, ridge cap, spire
//   trim    gable coping, window frames and tracery, door frame, the tower's
//           two string courses, the headstones
//   accent  the door, the cross
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// THE TIP. From the crack up (z_c, a course line above the roof), the tower
// -- walls, belfry, string courses, spire, cross -- is sheared 7 deg toward
// -X, away from the nave. Everything that sits on it was designed for that:
//   - the tower's stone courses ramp out at 66 deg, not the brick's 58, so the
//     left face's courses are still 60 deg after the tip;
//   - its openings have 65 deg heads (59.5 at worst after the tip);
//   - its string courses are sheared at 2.2 (65.6 deg), 60 after the tip.
//
// TEALIGHT. The nave is 52.6 mm clear across; its 62 deg ceiling is 52 mm up
// at the edge of a 46 mm circle round the centre.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- nave ------------------------------------------------------------------
W        = 56;              // along X, the front gable's width
D        = 74;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
plinth_h = 8;               // shared by every building in the town
Wh = W/2;  Dh = D/2;
SH       = 1.2;             // relief shear (see relief_up)

// ---- stone -------------------------------------------------------------------
// The post office's V-course, cut as stone: courses of mixed height, stones of
// mixed length, and quoins -- the stone at each corner alternates long and
// short course to course. Each course ramps OUT at 66 deg going up, runs flat,
// and chamfers back IN at 45 deg; nothing faces down more steeply than that.
bd    = 0.8;                // stone face, proud of plan(0)
s_ang = 66;
br    = bd * tan(s_ang);    // underside ramp height
bj    = 0.8;                // joint width
plinth_o = bd + 0.84;
CHP   = [4.4, 3.2, 5.0, 3.6, 4.6, 3.0, 5.2, 3.8];
function zc(k) = k == 0 ? plinth_h : zc(k - 1) + CHP[(k - 1) % len(CHP)];
function nc(zt, k = 0) = zc(k) >= zt ? k : nc(zt, k + 1);

// ---- roof ---------------------------------------------------------------------
// A 62 deg gable. Its inside is the lantern's ceiling: a plane through the
// inner wall face at H, so the slab rests on the walls and the eave's soffit
// is the same plane carried out 4 mm past the stone.
H     = 46;
r_ang = 62;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;               // slab, normal to the slope (6 extrusions)
tv    = tr / cos(r_ang);    // ...measured vertically
e     = 2;
xe    = Wh + bd + e;        // eave edge
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;          // the slab stops at the gables' inner faces
// COPED GABLES. Each gable wall rises through the roof as a parapet capped in
// cream, standing 2.6 above the slab. The roof butts against its inside face,
// so no slab end or rake is ever exposed -- the bakery found that no rake
// angle prints clean on a steep roof.
cp_lo = -0.2;  cp_hi = 2.6;

// ---- tower ---------------------------------------------------------------------
tx0 = -34;  tx1 = -12;      // 22 square, standing 4 proud of the front and 6
ty0 = -41;  ty1 = -19;      // past the left wall
tcx = (tx0 + tx1) / 2;  tcy = (ty0 + ty1) / 2;
th  = (tx1 - tx0) / 2;
z_c = zc(19);               // the crack: a course line, 7 mm above the roof
kt  = tan(7);
z_tt = 119;                 // top of the tower walls
hs   = 36;                  // spire height
t_ang = 65;                 // tower openings' heads
SHb  = 2.2;                 // the string courses' shear

// ---- placement ------------------------------------------------------------------
// Local x runs along the wall as seen from outside, local y is world up,
// local z is out from the face. u is the WORLD coordinate along the wall.
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module ftf(cx, cy, hx, hy, face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, cy + hy, z] : face == 1 ? [u, cy - hy, z]
      : face == 2 ? [cx + hx, u, z] : [cx - hx, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module nf(face, u, z) ftf(0, 0, Wh, Dh, face, u, z) children();
module tf(face, u, z) ftf(tcx, tcy, th, th, face, u, z) children();
// a world coordinate along face f as that face's local x
function loc(f, u, c) = (f == 0 || f == 3) ? -(u - c) : (u - c);
function t_mid(f) = f < 2 ? tcx : tcy;

module tipM() translate([0, 0, z_c]) multmatrix([[1, 0, -kt, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    translate([0, 0, -z_c]) children();
// The tower's shear, applied piecewise: identity below the crack. The two
// pieces meet exactly at z_c, where the shear is still the identity.
module tip() {
    intersection() { children(); translate([-500, -500, -50]) cube([1000, 1000, 50 + z_c]); }
    tipM() intersection() { children(); translate([-500, -500, z_c]) cube([1000, 1000, 500]); }
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

// An extrusion of a polygon drawn in (x, z), across y0..y1.
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

// ---- stone walls -------------------------------------------------------------------
function rpts(cx, cy, w, d, g, z) = [for (p = rrect_pts(w + 2*g, d + 2*g, corner_r + g, 5)) [cx + p[0], cy + p[1], z]];
module stone_skin(cx, cy, w, d, ztop) {
    n = nc(ztop);
    skin(concat(
        [rpts(cx, cy, w, d, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(cx, cy, w, d, g, z)],
        [rpts(cx, cy, w, d, 0, ztop + 2)]), slices = 0);
}
// Stone lengths from a fixed seed per course and face, so the wall is the
// same every render. The first stone off each corner alternates 8.5 / 4.5.
function s_lens(seed) = [for (r = rands(0, 1, 16, seed)) 5 + 7 * r];
function accum(v, i = 0, s = 0) = i >= len(v) ? [] : concat([s + v[i]], accum(v, i + 1, s + v[i]));
function joint_us(L, k, seed) = [for (p = accum(concat([k % 2 == 0 ? 8.5 : 4.5], s_lens(seed)))) if (p < 2 * L - 3) -L + p];
function clear_of(u, z0, z1, boxes) =
    len([for (b = boxes) if (u + bj/2 > b[0] && u - bj/2 < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
// A joint is a whole course tall or it is left out, and floored 0.05 behind
// plan(0) -- both measured on the post office's brick (Technique 71).
module wall_joints(cx, cy, hx, hy, f, ztop, seed0, boxes) {
    L = (f < 2 ? hx : hy) - 2.5;
    ftf(cx, cy, hx, hy, f, f < 2 ? cx : cy, 0)
        for (k = [1 : nc(ztop) - 1]) let (z0 = zc(k), z1 = zc(k + 1))
            for (u = joint_us(L, k, seed0 + 17 * k)) if (clear_of(u, z0, z1, boxes))
                translate([u - bj/2, z0, -0.05]) cube([bj, z1 - z0, 2.1]);
}

// ---- nave regions ----------------------------------------------------------------------
// x held to +-40: at +-60 the ceiling line falls below the polygon's floor
// and the outline crosses itself -- CGAL then drops the whole shape.
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module above_ceil_to(dz) xz(-60, 60) polygon([[-xe, z_ceil(xe)], [0, z_ceil(0)], [xe, z_ceil(xe)],
                                             [xe, z_out(xe) + dz], [0, z_out(0) + dz], [-xe, z_out(xe) + dz]]);
module gable_band(y0, y1, lo, hi) {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(y0, y1) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                            [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
}
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Dh - wall, Dh + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
// The gables carried out over the eaves: the parapet's end, a plain block
// whose underside is the soffit plane.
module kneelers() {
    for (s = [-1, 1], m = [0, 1]) mirror([0, s < 0 ? 1 : 0, 0]) mirror([m, 0, 0])
        // topped INSIDE the coping: topped level with it, the coping cut left
        // a zero-thickness sheet on each kneeler
        xz(Dh - wall, Dh - 0.05) polygon([[Wh - 0.3, z_ceil(Wh - 0.3)], [xf, z_ceil(xf)], [xe, fl_xe],
                                        [xe, z_out(xe) + 1], [Wh - 0.3, z_out(Wh - 0.3) + 1]]);
}
// THE EAVE FLARE. The soffit is the ceiling plane carried outward, so it
// FALLS toward the eave's edge, and the slab's lowest layers start there as
// islands: 44,654 support moves along both eaves on the first build. The
// flare fills under the soffit from the wall out, its underside rising 52 deg
// outward, and stops 0.08 short of the fascia (the bakery's measured margin:
// a 0.15 step, under the slicer's 0.185 allowance). It also carries the
// kneelers. e is 2, not 4: at 4 the flare's foot came down over the windows.
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);     // the flare's foot at plan(0)
module eave_flare() {
    // Only as long as the walls' plan(0): run on over the stone relief at
    // the gable ends, its foot hung past each rounded corner and drew
    // columns at all four.
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh + 0.05, Dh - 0.05)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [Wh - 1, z_ceil(Wh - 1)]]);
}
module nave_walls() {
    intersection() {
        stone_skin(0, 0, W, D, z_out(0) + cp_hi + 1);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
    eave_flare();
}
module nave_room() {
    intersection() {
        translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
        below_ceil();
    }
}

// ---- tower solids -------------------------------------------------------------------------
module tower_walls_plumb() { intersection() { stone_skin(tcx, tcy, 2*th, 2*th, z_tt + 1); translate([-100, -100, -1]) cube([200, 200, z_tt + 1]); } }
module tower_walls() tip() tower_walls_plumb();
module spire_plumb(g = 0) {
    translate([tcx, tcy, z_tt]) rotate([0, 0, 45]) cylinder(r1 = (th - g) * sqrt(2), r2 = 0, h = (th - g) * hs / th, $fn = 4);
}
sp_cut = 31;                // the spire is cut flat here for the cross
// The spire's base is 0.3 wider than the tower's plan(0) and sits on the
// string course's top: flush with plan(0), its edges fell exactly on the
// walls' top edges and left four-way edges round the whole base.
// It also starts 0.5 below the walls' top, so it fills the corners over the
// rounded wall corners: sat on the top, it sealed four tiny voids there.
module spire() tipM() intersection() {
    translate([0, 0, -0.5]) spire_plumb(-0.3);
    translate([-100, -100, 0]) cube([200, 200, z_tt + sp_cut]);
}
module tower_room() {
    tip() translate([tx0 + wall, ty0 + wall, -2]) cube([2 * (th - wall), 2 * (th - wall), z_tt + 2]);
    tipM() spire_plumb(wall);
}
module tower_outer() { tower_walls(); spire(); }
// THE TOWER'S INNER WALLS, carried to the ground. Where the tower stands in
// the nave its right wall used to start on the ceiling plane, which falls
// toward the tower's shaft: its lowest layer was a 14.6 mm strip over air at
// the shaft's edge. Both inner walls now run down to the plate, each pierced
// by a tall pointed arch so the tower stays open to the nave and the belfry
// still lights. Both stay outside a 46 mm circle round the nave's centre.
module screen() {
    intersection() {
        union() {
            translate([tx1 - wall, -y_r - 0.1, -1]) cube([wall, ty1 + y_r + 0.1, 200]);
            translate([-x_in - 0.1, ty1 - wall, -1]) cube([tx1 + x_in + 0.1, wall, 200]);
        }
        below_ceil();
    }
}
//   [face, u, a, straight height] -- from the plate, 58 deg heads
ARCHES = [[2, -27.8, 5.5, 50], [0, -20, 4.5, 44]];
module arches() {
    for (r = ARCHES) tf(r[0], r[1], -1)
        translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(lancet_pts(r[2], r[3] + 1));
}
module room() { difference() { nave_room(); screen(); } tower_room(); }

// ---- openings ----------------------------------------------------------------------------
// A LANCET: straight sides, then an arc of radius 2a curving in until it is
// `ang` from horizontal, then straight to the point. The nave's are 58 deg;
// the tower's 65, for the tip.
function lancet_pts(a, hgt, ang = 58, n = 12) =
    let (R = 2 * a, t1 = 90 - ang, xt = a - R + R * cos(t1), zt = hgt + R * sin(t1), ap = zt + xt * tan(ang))
    concat([[-a, 0], [a, 0]],
           [for (i = [0 : n]) let (t = t1 * i / n) [a - R + R * cos(t), hgt + R * sin(t)]],
           [[0, ap]],
           [for (i = [n : -1 : 0]) let (t = t1 * i / n) [-(a - R + R * cos(t)), hgt + R * sin(t)]]);
function lancet_top(a, hgt, ang = 58) =
    let (R = 2 * a, t1 = 90 - ang) hgt + R * sin(t1) + (a - R + R * cos(t1)) * tan(ang);

mull = 1.68;
fr_w = 2.4;                 // frame width. The shear eats 1.9 mm of a head
                            // arm's height at its face (Technique 72); a
                            // 58 deg arm 2.4 wide keeps 2.6, 1.4 normal.
fr_t = bd + 0.44;           // frame face, 0.44 proud of the stone
//   [face, u, z, a, straight height, tracery]   tracery 1 = mullion, 2 = Y
WINDOWS = [
    [1,   0, 45, 4.5, 20, 2],                    // the tall window over the door
    [0, -10, 13, 3.2, 12, 1],  [0, 10, 13, 3.2, 12, 1],  [0, 0, 52, 2.6, 10, 1],
    [2, -22, 12.5, 3.2, 12, 1],  [2,  0, 12.5, 3.2, 12, 1],  [2, 22, 12.5, 3.2, 12, 1],
    [3,   0, 12.5, 3.2, 12, 1],  [3, 22, 12.5, 3.2, 12, 1],
];
module win_outline(w) { polygon(lancet_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -1]) square([mull, w[5] == 2 ? w[4] + mull : 100]);
    // Y tracery: the mullion forks at the spring into two bars at 62 deg
    if (w[5] == 2) for (s = [-1, 1]) translate([0, w[4]]) rotate(s < 0 ? 180 - 62 : 62)
        translate([0, -mull/2]) square([3 * w[3], mull]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame_holes() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) win_outline(w);
}
//   [face, u, z, a, straight height] -- plain openings, no frames
TOPEN = [
    [1, tcx, 26, 1.8, 7],  [1, tcx, 60, 1.8, 7],
    [3, tcy, 36, 1.8, 7],  [3, tcy, 60, 1.8, 7],
    for (f = [0 : 3]) [f, t_mid(f), 98, 3.0, 7],  // the belfry
];
module tower_openings_plumb() {
    for (o = TOPEN) tf(o[0], o[1], o[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(lancet_pts(o[3], o[4], t_ang));
}
module openings() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
    nf(1, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(lancet_pts(door_a, door_h));
    tip() tower_openings_plumb();
    arches();
}

// ---- door, step --------------------------------------------------------------------------
door_a = 6;
door_h = 17;
module door_leaf() {
    nf(1, 0, plinth_h) translate([0, 0, -wall]) difference() {
        // The leaf's head sits 0.2 inside the doorway's and the frame laps the
        // gap (Technique 72: two heads meeting at one tip left non-manifold
        // edges).
        linear_extrude(wall - 0.2) union() {
            intersection() { polygon(lancet_pts(door_a, door_h)); translate([-20, -1]) square([40, door_h + 1]); }
            offset(delta = -0.2) polygon(lancet_pts(door_a, door_h));
        }
        translate([0, 0, wall - 0.9]) linear_extrude(1)
            polygon([[-0.3, -1], [-0.3, door_h + 4], [0, door_h + 4 + 0.3 * tan(62)], [0.3, door_h + 4], [0.3, -1]]);
    }
}
module door_frame() {
    nf(1, 0, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
        difference() {
            intersection() { offset(r = 1.7) polygon(lancet_pts(door_a, door_h));
                             translate([-30, 0]) square([60, 100]); }
            translate([0, -1]) offset(delta = -0.3) polygon(lancet_pts(door_a, door_h + 1));
        }
}
st_w = 20;  st_d = 8;
module step() { nf(1, 0, 0) translate([-st_w/2, 0, 0]) cube([st_w, plinth_h, st_d]); }

// ---- the crack ---------------------------------------------------------------------------
// Engraved 0.4 behind plan(0), zig-zagging across a face just under z_c.
// Every stretch of it is 62 deg or steeper: it is a chain of hulls between
// small diamonds whose own edges are 62 deg, so the groove never has a flatter
// ceiling. It tapers out at both ends.
module crack(f, u0, z0, dir, seed) {
    // A settlement crack running DOWN from the tip. It must fall the whole
    // way: a zig-zag that rises again leaves a downward point of stone above
    // each trough, and that point's first layer is an island -- the first
    // build's zig-zag cracks drew support columns under every tooth. Seven
    // steps, alternately 64 and 72 deg, tapering at both ends.
    n = 7;
    r = rands(0, 1, n + 1, seed);
    ws = [for (i = [0 : n - 1]) dir * (0.7 + 0.6 * r[i])];
    us = concat([u0], accum(ws, 0, u0));
    dz = [for (i = [0 : n - 1]) abs(ws[i]) * tan(i % 2 == 0 ? 64 : 72)];
    zs = concat([z0], accum([for (d = dz) -d], 0, z0));
    module dia(i) let (h = 0.45 * min(1, 0.4 + 0.6 * min(i, n - i) / 2))
        translate([us[i], zs[i]]) polygon([[-h, 0], [0, h * tan(62)], [h, 0], [0, -h * tan(62)]]);
    tf(f, t_mid(f), 0) translate([0, 0, -0.4]) linear_extrude(3)
        for (i = [0 : n - 1]) hull() { dia(i); dia(i + 1); }
}
module cracks() {
    tip() {
        crack(1, 6.5, z_c + 3, -1, 11);
        crack(3, -1.5, z_c + 3, -1, 23);
    }
}

// ---- string courses, spire, cross ------------------------------------------------------------
// Two cream bands round the tower, 3 tall, sheared at 2.2, MITRED at the
// corners, where the two 65.6 deg undersides meet in a keel. Run past the
// corner instead, each band's inner strip hung in the air beyond the next
// face with an underside only 0.88 above its foot, and drew support columns
// at all eight corners.
bfr_t = bd + 0.84;
BANDS = [91, z_tt - 3];
module bands_plumb() {
    for (zb = BANDS, f = [0 : 3]) intersection() {
        tf(f, t_mid(f), zb)
            relief_up(-0.4, bfr_t, SHb) translate([-(th + bfr_t), 0]) square([2 * (th + bfr_t), 3]);
        translate([tcx, tcy, 0]) rotate([0, 0, [90, -90, 0, 180][f]]) linear_extrude(300)
            polygon([[0, 0], [60, 60], [60, -60]]);
    }
}
// A cross on the cut top of the spire: a square post, and arms whose
// undersides rise 66 deg from the post -- 60 after the tip.
module cross_plumb() {
    translate([tcx, tcy, z_tt + sp_cut]) {
        translate([-0.9, -0.9, 0]) cube([1.8, 1.8, 12]);
        xz(-0.9, 0.9) polygon([[0.9, 2.9], [3.3, 2.9 + 2.4 * tan(66)], [3.3, 9.5], [-3.3, 9.5],
                                [-3.3, 2.9 + 2.4 * tan(66)], [-0.9, 2.9]]);
    }
}

// ---- roof ---------------------------------------------------------------------------------------
// Past the flare's tip the slab's underside carries on up the flare's 52 deg
// line to the fascia, instead of following the soffit plane down: stopped
// 0.08 short with the soffit still falling, the slab's corner hung 0.15 below
// the flare's tip and every eave drew a wall of support.
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module slab() xz(-y_r, y_r) polygon([[-xe, fl_xe], [-xf, z_ceil(xf)], [0, z_ceil(0)], [xf, z_ceil(xf)], [xe, fl_xe],
                                     [xe, z_out(xe)], [0, z_out(0)], [-xe, z_out(xe)]]);
// Slate courses, ADDED like the bakery's shingles: each butt is a vertical
// face 1.0 proud of the slab, each top slopes up to 0.05 under the next butt.
// 2.35, not 2.4: at 2.4 a course butt fell exactly on the tower's stone
// face (x = -11.2) and left a sliver face in the roof and the coping.
sh_c = 2.35;                // course, measured horizontally
function sh_d(k) = min(k * sh_c, xe - 0.6);
module slates() {
    nk = ceil((xe - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (x0 = s * (xe - sh_d(k)), x1 = s * (xe - min(sh_d(k + 1) + 0.5, xe - 0.6)))
        xz(-y_r, y_r) polygon([[x0, z_out(x0) - 1.0], [x0, z_out(x0) + 1.0], [x1, z_out(x1) + 0.05], [x1, z_out(x1) - 1.0]]);
}
module ridge_cap() {
    // flat-topped: brought to a point, the cap's apex read as sub-bead
    // material all along the ridge
    xz(-y_r, y_r) polygon([[2.4, z_out(2.4) - 1.0], [2.4, z_out(2.4) + 1.4], [0.7, z_out(0) + 2.4],
                           [-0.7, z_out(0) + 2.4], [-2.4, z_out(2.4) + 1.4], [-2.4, z_out(2.4) - 1.0]]);
}
// Proud of the stone across the gable, but only where the gable's face is
// straight (|x| <= Wh - 1): run on to the corner, its lowest end hung over the
// rounded corner stones. Past that, only as deep as the kneeler. The proud
// part's underside rises 58 deg outward from plan(0), like every relief here:
// flat on the 62 deg line, its lowest end still hung 0.9 over the stone
// valleys at each corner and drew a support column there.
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
module coping() {
    difference() {
        for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0]) {
            xz(Dh - wall, Dh - 0.05) gable_poly(cp_lo, cp_hi);
            intersection() {
                xz(Dh - 0.1, Dh + bd + 0.1) gable_poly(cp_lo, cp_hi);
                multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
                    xz(Dh - 1, Dh + 3) gable_poly(cp_lo, cp_hi + 10);
                translate([-Wh + 1, -100, 0]) cube([W - 2, 200, 300]);
            }
        }
        tower_outer();
    }
}

// ---- headstones -----------------------------------------------------------------------------------
// Two, against the plinth right of the door, sunk 0.4 into it and tipped
// sideways. Round tops face up; their tipped sides are 6-8 deg off vertical.
//   [x, width, height, tilt]
STONES = [[15, 6.4, 9.5, 6], [23, 5.6, 8, -8]];
module headstones() {
    for (s = STONES) intersection() {
        translate([s[0], -Dh - plinth_o + 0.4, 0]) rotate([0, s[3], 0]) translate([0, 0, -3])
            xz(-1.8, 0) union() {
                translate([-s[1]/2, 0]) square([s[1], s[2] + 3 - s[1]/2]);
                translate([0, s[2] + 3 - s[1]/2]) circle(d = s[1], $fn = 40);
            }
        translate([-100, -100, 0]) cube([200, 200, 50]);
    }
}

// ---- mark ------------------------------------------------------------------------------------------
module brand_mark() {
    translate([0, -Dh - st_d / 2, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- joints ------------------------------------------------------------------------------------------
function frame_box(f, w) = let (lu = loc(f, w[1], 0), h = w[3] + fr_w + 0.3 + 1.5)
    [lu - h, lu + h, w[2] - fr_w - 2, w[2] + lancet_top(w[3], w[4]) + fr_w + 1.5];
function nave_boxes(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) frame_box(f, w)],
    // a joint reaching into the flare would cut it a flat-roofed slot
    f >= 2 ? [[-100, 100, zf0, 300]] : [],
    f == 1 ? [[-door_a - 1.7 - 1.5, door_a + 1.7 + 1.5, 0, plinth_h + lancet_top(door_a, door_h) + 1.7 + 1.5]] : []);
function tower_boxes(f) = concat(
    [for (o = TOPEN) if (o[0] == f) let (lu = loc(f, o[1], t_mid(f)))
        [lu - o[3] - 1.5, lu + o[3] + 1.5, o[2] - 1.5, o[2] + lancet_top(o[3], o[4], t_ang) + 1.5]],
    [for (zb = BANDS) [-50, 50, zb - 1, zb + 4]],
    // no joints across the cracks
    f == 1 ? [[-1.5, 8, 72, 91]] : f == 3 ? [[-10, 0, 72, 91]] : []);
module joints() {
    difference() {
        for (f = [0 : 3]) wall_joints(0, 0, Wh, Dh, f, f < 2 ? z_out(0) + cp_hi : H + 2, 100 * f, nave_boxes(f));
        translate([tx0 - 2.5, ty0 - 2.5, -10]) cube([tx1 - tx0 + 5, ty1 - ty0 + 5, 300]);
    }
    difference() {
        tip() for (f = [0 : 3]) wall_joints(tcx, tcy, th, th, f, z_tt, 1000 + 100 * f, tower_boxes(f));
        // not where the tower stands in the nave, below the roof's top
        intersection() {
            translate([-Wh - bd - 2.2, -Dh - bd - 2.2, -10]) cube([W + 2 * bd + 4.4, D + 2 * bd + 4.4, 300]);
            xz(-60, 60) polygon([[-40, -20], [40, -20], [40, z_out(40) + cp_hi + 1], [0, z_out(0) + cp_hi + 1], [-40, z_out(-40) + cp_hi + 1]]);
        }
    }
}

// ---- parts ----------------------------------------------------------------------------------------------
module plinth() {
    linear_extrude(plinth_h) offset(delta = plinth_o) union() {
        translate([-Wh, -Dh]) square([W, D]);
        translate([tx0, ty0]) square([tx1 - tx0, ty1 - ty0]);
    }
}
module body_solid() {
    plinth();
    nave_walls();
    tower_walls();
    step();
}
module trim_raw() {
    coping();
    for (w = WINDOWS) nf(w[0], w[1], w[2]) {
        relief_up(-0.4, fr_t) { offset(r = fr_w) win_outline(w); offset(r = 0.3) win_outline(w); }
        translate([0, 0, -0.4]) linear_extrude(bd + 0.4) win_muntins(w, 0.6);
    }
    door_frame();
    tip() bands_plumb();
    headstones();
}
module accent_raw() {
    door_leaf();
    tipM() cross_plumb();
}
module roof_raw() {
    difference() {
        union() { slab(); slates(); ridge_cap(); }
        room(); tower_outer();
    }
    difference() { spire(); room(); }
}
module roof_part()   { roof_raw(); }
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_solid();
        room(); openings(); frame_holes(); joints(); cracks(); trim_raw(); accent_raw(); roof_raw(); brand_mark();
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
    color("#77716B") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
}
