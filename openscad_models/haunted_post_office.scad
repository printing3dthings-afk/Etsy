// Haunted Post Office lantern -- building #1 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). ONE story, BRICK, a SAGGING PARAPET and
// a flat roof that LIFTS OFF. A hollow shell lit from inside by a battery LED
// tealight: open base, true through-cut windows.
//
// Built to the town's variety plan (Scott, 2026-09-25): no two buildings
// share a wall texture, a window shape or a roof shape. This one is brick,
// gable-headed windows, flat roof. The relief, frame, muntin and inlay
// machinery is the bakery's (haunted_bakery.scad) and its WHY comments are
// there; what is new here is commented here.
//
// TWO PRINTS, ONE PLATE (haunted_post_office.3mf):
//   the house  body    brick walls, plinth, step, the lid's inner seat
//              trim    coping, window and door frames, muntins, door, sign
//                      board, the parcels' string
//              accent  the parcels, the POST OFFICE letters, the mail slot
//   the roof   lid     flat slab + leaning chimney + crooked vent pipe,
//                      printed flat, top up
// Every house part is built DISJOINT from the others. The part="chk_*"
// renders are each pairwise intersection and must come out empty.
//
// A FLAT ROOF CANNOT BE PRINTED ON A HOLLOW HOUSE: it is a flat ceiling. So
// the roof is its own print, a flat slab with its underside on the plate,
// and it rests on a 55-degree corbel inside the parapet. Lift it off to
// switch the tealight.
//
// TEALIGHT. The room is 72.6 x 50.6 mm clear from the plate to the lid seat
// at 58 mm; a 38 x 45 mm LED tealight drops in with room to spare.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ----------------------------------------------------------------
W        = 76;              // along X, the front's width
D        = 54;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
corner_r = 1;
plinth_h = 8;               // shared by every building in the town
SH       = 1.2;             // shear of every raised relief (see relief_up)
Wh = W/2;  Dh = D/2;

// ---- brick -----------------------------------------------------------------
// Each course is a V: it ramps OUT going up at 58 deg from horizontal, runs
// flat, and chamfers back IN at 45 deg to meet the next course at plan(0). The
// underside is the 58 deg ramp; the chamfer faces up. There is no horizontal
// step anywhere (the bakery's clapboard steps back over 0.02 mm, and a sign
// edge crossing that step left zero-area faces).
bd   = 0.6;                 // brick face, proud of plan(0)
bp   = 2.6;                 // course height
br   = bd * tan(58);        // underside ramp height
bl   = 7;                   // brick length, joint to joint
bj   = 0.6;                 // joint width
plinth_o = bd + 0.84;       // plinth face, 0.84 proud of the brick

// ---- parapet and lid ---------------------------------------------------------
z_s  = 58;                  // the lid's seat
cb   = 2.5;                 // the seat's corbel reaches 2.5 in from the wall, on a 55 deg underside
tr   = 2.52;                // lid thickness (6 extrusions)
// The parapet's top sags between the corners and is not level: the front
// left corner has slumped. Corner heights FL, FR, BR, BL; sag per face
// (back, front, right, left) at mid-wall.
// Each corner's coping underside, where it slopes through the corner fillet
// (its top line - c_h, less up to 0.48), must not span a brick valley
// (8 + 2.6k): where it did, at BR = 70.5, the two touched along a line and
// left a loose zero-volume shell.
PC   = [68.5, 71, 70.9, 70];
SAG  = [3, 4, 2.5, 2.5];
c_h  = 2.4;                 // coping depth

// ---- plan ----------------------------------------------------------------
module plan2d(g) { offset(r = g) offset(r = corner_r) square([W - 2*corner_r, D - 2*corner_r], center = true); }
function plan_pts(g, z) = [for (p = rrect_pts(W + 2*g, D + 2*g, corner_r + g, 5)) [p[0], p[1], z]];
function sq_pts(g, z) = [[Wh + g, Dh + g, z], [-Wh - g, Dh + g, z], [-Wh - g, -Dh - g, z], [Wh + g, -Dh - g, z]];
function stations(a, c, n) = [for (i = [0 : n]) a + (c - a) * i / n];

// Place children on a wall. Local x runs along the wall, local y is world
// up, local z is out from plan(0).
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
// For faces 2 and 3, u is WORLD y.
module face_tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module shear_up() multmatrix([[1, 0, 0, 0], [0, 1, SH, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// Raised relief: sheared underside, flat top, hole ceiling rising with depth.
// Every rule behind this shape is in haunted_bakery.scad's relief_up().
module relief_hole(d0, a, b) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up() translate([0, 0, a]) linear_extrude(b - a) translate([0, -SH * d0]) children();
}
module relief_up(d0, d1) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up() translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1) children(1);
    }
}

// ---- walls -------------------------------------------------------------------
z_top = 74;                 // walls run up to here; the parapet cut trims them
module brick_skin() {
    n = ceil((z_top - plinth_h) / bp);
    skin(concat(
        [plan_pts(0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = plinth_h + k * bp,
                 z  = [z0, z0 + br, z0 + bp - bd][j],
                 g  = [0, bd, bd][j])
            plan_pts(g, z)],
        [plan_pts(0, plinth_h + n * bp), plan_pts(0, z_top + 2)]), slices = 0);
}
// Vertical joints, staggered course to course. A joint is a whole course
// tall or it is left out: one stopped part-way up a course would have a flat
// ceiling. Joints are left out wholesale near corners, frames, the door, the
// sign and the parcels, so no sliver of brick is ever left beside a frame.
// The floor sits 0.05 BEHIND plan(0), so a joint cuts through a course's whole
// depth and its only edges land on the course lines. Floored 0.1 in front of
// plan(0), every joint met the course's sloped underside along the same
// horizontal line, and CGAL triangulated each course face through that row of
// collinear points: 22 zero-area faces. No joints in the bottom course, whose
// floor would lie flush with the plinth's top.
function wall_L(f) = f < 2 ? Wh : Dh;
function clear_of(f, u, z0, z1, boxes) =
    len([for (b = boxes) if (b[0] == f && u + bj/2 > b[1] && u - bj/2 < b[2] && z1 > b[3] && z0 < b[4]) 1]) == 0;
module brick_joints() {
    n = ceil((z_top - plinth_h) / bp);
    ko = keepouts();
    for (f = [0 : 3]) face_tf(f, 0, 0)
        for (k = [1 : n - 1]) let (z0 = plinth_h + k * bp, L = wall_L(f) - 2.5, s = (k % 2) * bl / 2)
            for (u = [-L + s : bl : L]) if (clear_of(f, u, z0, z0 + bp, ko))
                translate([u - bj/2, z0, -0.05]) cube([bj, bp, 2.1]);
}

// ---- parapet top ----------------------------------------------------------------
// Each wall's top: a straight line between its two corners, less a parabolic
// sag. Corners are shared, so the four walls meet at the same height.
function wall_ends(f) = f == 1 ? [PC[0], PC[1]] : f == 0 ? [PC[3], PC[2]]
                      : f == 2 ? [PC[1], PC[2]] : [PC[0], PC[3]];
function pz(f, u) = let (L = wall_L(f), c = max(-L, min(L, u)), e = wall_ends(f))
    e[0] + (e[1] - e[0]) * (c + L) / (2 * L) - SAG[f] * (1 - pow(c / L, 2));
// a point u along wall f, n out from its plan(0), in world x, y
function wall_xy(f, u, n) = f == 1 ? [u, -Dh - n] : f == 0 ? [u, Dh + n]
                          : f == 2 ? [Wh + n, u] : [-Wh - n, u];
module vstick(f, u, n, z0, z1) { p = wall_xy(f, u, n); translate([p[0], p[1], z0]) cube([0.001, 0.001, z1 - z0]); }
function wall_st(f) = stations(-wall_L(f) - 6, wall_L(f) + 6, 36);
// Everything above each wall's top line. Built as hulls between stations, so
// every piece is convex and needs no winding to be right.
module sky() {
    for (f = [0 : 3]) let (st = wall_st(f)) for (i = [0 : len(st) - 2])
        hull() for (u = [st[i], st[i + 1]], n = [-6, 6]) vstick(f, u, n, pz(f, u), 200);
}
// Coping: a cream band on the parapet's top, c_h deep, following the sag. Its
// underside rises 58 deg across the brick's depth, so wherever it crosses a
// course's valley it has no ledge to hang.
// The coping's underside, cut in two halves per wall.
//   - INSIDE the wall (n from -wall-0.3 to 0): flat, at the top line less
//     c_h, where it sits on brick. Clipped to the ROUNDED plan, and only as
//     deep as the wall itself. Six deep, one wall's cut ran into the next and
//     sealed joint pockets shut; clipped to a square it left the coping a flat
//     underside in the corner fillets, over air: 5,049 support moves.
//   - OUTSIDE (n from -0.3 out): rising 58 deg. Starting 0.3 behind the face,
//     it also shapes the corner fillets, where the coping's underside is then
//     the slope and never flat.
module coping_cut() {
    intersection() {
        for (f = [0 : 3]) let (st = wall_st(f)) for (i = [0 : len(st) - 2])
            hull() for (u = [st[i], st[i + 1]], n = [-wall - 0.3, 0]) vstick(f, u, n, -1, pz(f, u) - c_h);
        translate([0, 0, -2]) linear_extrude(200) plan2d(0);
    }
    for (f = [0 : 3]) let (st = wall_st(f)) for (i = [0 : len(st) - 2]) {
        hull() for (u = [st[i], st[i + 1]]) {
            vstick(f, u, -0.3, -1, pz(f, u) - c_h - 0.3 * tan(58));
            vstick(f, u, 3, -1, pz(f, u) - c_h + 3 * tan(58));
        }
    }
}
module coping() {
    difference() {
        // 0.1 fuller than the brick: flush, the brick's 5-segment corner and
        // the coping's finer arc crossed, and specks of brick poked through
        translate([0, 0, 58]) linear_extrude(z_top + 2 - 58) difference() { plan2d(bd + 0.1); plan2d(-wall); }
        coping_cut();
        sky();
    }
}

// ---- the lid's seat, and the lid ------------------------------------------------------
// A ring corbelled out of the walls: flat on top for the lid, 55 deg under,
// and a 1.5 mm vertical face at its inner edge. Run the slope all the way to
// the top and the ring ends in a knife edge, which the gate's wall check
// measured as sub-bead all round the room.
cb_v = 1.5;
module corbel() {
    s = 0.5;
    z_foot = z_s - cb_v - (cb + 0.3) * tan(55);
    difference() {
        // starts 0.3 below the slope's foot, inside the plug below it: started
        // lower, the ring kept a flat underside there
        translate([0, 0, z_foot - 0.3]) linear_extrude(z_s - z_foot + 0.3) plan2d(-wall + 0.3);
        skin([sq_pts(-wall + 0.3 + s, z_foot - s * tan(55)),
              sq_pts(-wall - cb - s, z_s - cb_v + s * tan(55))], slices = 0);
        translate([0, 0, z_s - cb_v - 1]) linear_extrude(cb_v + 2) plan2d(-wall - cb);
    }
}
module room() {
    difference() {
        translate([0, 0, -2]) linear_extrude(z_top + 10) plan2d(-wall);
        corbel();
    }
}
lid_gap = 0.3;
// The chimney leans away from the house's centre; the vent pipe leans the
// other way. Both stand on the lid, so the lid prints top-up with no support.
lc_xy = [-22, 12];
module lid_chimney() {
    ld = [9, 7];
    z0 = z_s + tr - 0.4;
    module sl(c, z, g = 0) translate([c[0], c[1], z]) linear_extrude(0.01) square(ld + [2*g, 2*g], center = true);
    translate([lc_xy[0] - ld[0]/2, lc_xy[1] - ld[1]/2, z0]) cube([ld[0], ld[1], 11]);
    // kink 20.6 deg from vertical, then straight, corbel, cap and pot
    hull() { sl(lc_xy, z0 + 10.99); sl(lc_xy + [-3, 0], z0 + 19); }
    translate([lc_xy[0] - 3 - ld[0]/2, lc_xy[1] - ld[1]/2, z0 + 18.99]) cube([ld[0], ld[1], 4.02]);
    hull() { sl(lc_xy + [-3, 0], z0 + 22.99); sl(lc_xy + [-3, 0], z0 + 25, 1.2); }
    translate([lc_xy[0] - 3, lc_xy[1], z0 + 26.2]) cube([ld[0] + 2.4, ld[1] + 2.4, 2.4], center = true);
    translate([lc_xy[0] - 3, lc_xy[1], z0 + 27.3]) {
        cylinder(r = 2.4, h = 3.6, $fn = 36);
        translate([0, 0, 3.6]) cylinder(r1 = 2.4, r2 = 3.1, h = 0.9, $fn = 36);   // 38 deg
        translate([0, 0, 4.5]) cylinder(r = 3.1, h = 0.8, $fn = 36);
    }
}
module lid_vent() {
    // A stove pipe tipped 12 deg, ending in a plain taper. A flared cap on a
    // tipped pipe drops to 35 deg on the low side. Sunk 0.8 so the tipped
    // foot never lifts clear of the lid.
    translate([20, -9, z_s + tr - 0.8]) rotate([0, 12, 0]) {
        cylinder(r = 1.8, h = 11, $fn = 28);
        translate([0, 0, 11]) cylinder(r1 = 1.8, r2 = 0.7, h = 2.2, $fn = 28);
    }
}
module lid() {
    translate([0, 0, z_s]) linear_extrude(tr) plan2d(-wall - lid_gap);
    lid_chimney();
    lid_vent();
}

// ---- openings ------------------------------------------------------------------
// GABLE-HEADED: straight sides under a 60 deg triangle. The post office's own
// window shape in the town plan; its apex is a 60 deg peak, steeper than the
// 58 every corner needs.
function gable_pts(a, hgt) = [[-a, 0], [-a, hgt], [0, hgt + a * tan(60)], [a, hgt], [a, 0]];
function gable_top(a, hgt) = hgt + a * tan(60);
mull = 1.68;
//   [face, u, z, a, hgt] -- u is world y on faces 2 and 3
WINDOWS = [
    [1,   0, 17, 6.5, 16],                                  // front, the counter
    [0, -18, 17, 5, 16],  [0, 18, 17, 5, 16],
    [2,   0, 17, 5, 16],  [3,   0, 17, 5, 16],
];
module win_outline(w) { polygon(gable_pts(w[3], w[4])); }
// A mullion and a CHEVRON transom at 50 deg, never a flat bar.
module win_bars(w) {
    translate([-mull/2, -1]) square([mull, gable_top(w[3], w[4]) + 2]);
    for (s = [-1, 1]) translate([0, w[4] * 0.62]) rotate(s < 0 ? -130 : -50)
        translate([0, -mull/2]) square([2 * w[3], mull]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module win_muntins_inner(w) {
    intersection() {
        win_bars(w);
        union() {
            offset(r = -0.25) win_outline(w);
            intersection() { offset(r = 0.3) win_outline(w); translate([-50, -5]) square([100, w[4] + 5]); }
        }
    }
}
fr_w = 1.7;
fr_t = bd + 0.84;           // frame face, 0.84 proud of the brick
fr_sill = 2.6;
module win_frame_outer(w) {
    union() {
        offset(r = fr_w + 0.3) win_outline(w);
        translate([-w[3] - fr_w - 0.3, -fr_w - 0.3 - fr_sill]) square([2 * (w[3] + fr_w + 0.3), fr_w + fr_sill + 1]);
    }
}
module frame_holes() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) win_outline(w);
}
module openings() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
    face_tf(1, door_x, plinth_h)
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(gable_pts(door_a, door_h));
}

// ---- door, step, parcels ---------------------------------------------------------
door_x = -24;
door_a = 6.5;
door_h = 22;
module door_leaf() {
    face_tf(1, door_x, plinth_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
        difference() {
            polygon(gable_pts(door_a, door_h));
            translate([0, 20]) polygon(gable_pts(2.4, 1.5));
        }
}
module door_frame() {
    face_tf(1, door_x, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
        difference() {
            intersection() { offset(r = fr_w) polygon(gable_pts(door_a, door_h));
                             translate([-20, 0]) square([40, 100]); }
            translate([0, -1]) polygon(gable_pts(door_a, door_h + 1));
        }
}
st_w = 22;  st_d = 9;
module step() { face_tf(1, door_x, 0) translate([-st_w/2, 0, 0]) cube([st_w, plinth_h, st_d]); }
// The mail slot: a brass plate inlaid FLUSH in the door, 0.8 deep.
module mail_slot() {
    face_tf(1, door_x, plinth_h + 9) translate([-3, 0, -1.0]) cube([6, 1.4, 0.8]);
}
// Parcels on the plate by the wall, each box inside the footprint of the one
// below and face to face with it; tied with string, a flush trim inlay that
// stays off the buried back face.
//   [width, height, depth out, twist deg]
PARCELS = [[10, 8, 9, 0], [8, 6, 7, 7], [5.5, 4.5, 5, -9]];
pc_u = 22;
pc_str = 1.0;
function pc_z(i) = i == 0 ? 0 : pc_z(i - 1) + PARCELS[i - 1][1];
module parcel_box(i) {
    q = PARCELS[i];
    face_tf(1, pc_u, pc_z(i)) translate([0, 0, PARCELS[0][2] / 2 - 0.4]) rotate([0, q[3], 0])
        translate([-q[0]/2, 0, -q[2]/2]) children();
}
module parcels_solid() {
    for (i = [0 : len(PARCELS) - 1]) let (q = PARCELS[i]) parcel_box(i) cube([q[0], q[1], q[2]]);
}
module parcels_string() {
    for (i = [0 : len(PARCELS) - 1]) let (q = PARCELS[i])
        parcel_box(i) difference() {
            intersection() {
                translate([0, 0, 1.0]) cube([q[0], q[1], q[2] - 1.0]);
                union() {
                    translate([q[0]/2 - pc_str/2, -1, -1]) cube([pc_str, q[1] + 2, q[2] + 2]);
                    translate([-1, -1, q[2]/2 - pc_str/2]) cube([q[0] + 2, q[1] + 2, pc_str]);
                }
            }
            translate([0.8, 0.8, 0.8]) cube([q[0] - 1.6, q[1] - 1.6, q[2] - 1.6]);
        }
}

// ---- sign --------------------------------------------------------------------------
// One line across the shopfront, hung crooked. 10.4 tall -- four courses --
// so its top and bottom edges share a phase, and both sit between brick
// valleys (8 + 2.6k): top 57.85..59.53, bottom 47.45..49.13.
sg_u = 2;   sg_z = 53.49;  sg_w = 48;  sg_h = 10.4;
sg_tilt = -2;               // right end low
module sign_board() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt])
        relief_up(-0.4, fr_t) translate([-sg_w/2, -sg_h/2]) square([sg_w, sg_h]);
}
module sign_letters() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t - 0.8])
        linear_extrude(0.8) text("POST OFFICE", size = 4.4, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.04);
}

// Brick joints stay out of these: [face, u0, u1, z0, z1], a frame's outline
// plus 1.5 all round.
function keepouts() = concat(
    [for (w = WINDOWS) let (h = w[3] + fr_w + 0.3 + 1.5)
        [w[0], w[1] * (w[0] == 3 ? -1 : 1) - h, w[1] * (w[0] == 3 ? -1 : 1) + h,
         w[2] - fr_w - 0.3 - fr_sill - 1.5, w[2] + gable_top(w[3], w[4]) + fr_w + 0.3 + 1.5]],
    [[1, door_x - door_a - fr_w - 1.5, door_x + door_a + fr_w + 1.5, 0, plinth_h + gable_top(door_a, door_h) + fr_w + 1.5],
     [1, sg_u - sg_w/2 - 2.5, sg_u + sg_w/2 + 2.5, sg_z - sg_h/2 - 2.5, sg_z + sg_h/2 + 2.5],
     [1, pc_u - 7, pc_u + 7, 0, 21]]);

// ---- mark ------------------------------------------------------------------------
module brand_mark() {
    translate([door_x, -Dh - st_d / 2, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- parts ---------------------------------------------------------------------------
module body_solid() {
    linear_extrude(plinth_h) plan2d(plinth_o);
    brick_skin();
    corbel();
    step();
}
module trim_raw() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) {
        relief_up(-0.4, fr_t) { win_frame_outer(w); offset(r = 0.3) win_outline(w); }
        translate([0, 0, -0.4]) linear_extrude(bd + 0.4) win_muntins(w, 0.6);
        translate([0, 0, -wall + 0.2]) linear_extrude(wall - 0.6 + 0.01) win_muntins_inner(w);
    }
    door_frame();
    door_leaf();
    sign_board();
    parcels_string();
    coping();
}
module accent_raw() {
    difference() { parcels_solid(); parcels_string(); }
    sign_letters();
    mail_slot();
}
module accent_part() { accent_raw(); }
module trim_part()   { difference() { trim_raw(); accent_raw(); } }
module body_part() {
    difference() {
        body_solid();
        room(); sky(); brick_joints();
        openings(); frame_holes(); trim_raw(); accent_raw(); brand_mark();
    }
}
module lid_part() { lid(); }
// the lid in its print pose: underside on the plate
module lid_print() { translate([0, 0, -z_s]) lid(); }

if      (part == "none")   ;
else if (part == "body")   body_part();
else if (part == "trim")   trim_part();
else if (part == "accent") accent_part();
else if (part == "lid")    lid_print();
else if (part == "house")  union() { body_part(); trim_part(); accent_part(); }
else if (part == "chk_body_trim")    intersection() { body_part(); trim_part(); }
else if (part == "chk_body_accent")  intersection() { body_part(); accent_part(); }
else if (part == "chk_trim_accent")  intersection() { trim_part(); accent_part(); }
else if (part == "chk_lid_house")    intersection() { lid_part(); union() { body_part(); trim_part(); } }
else {
    color("#7A3E33") body_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
    color("#2B2F38") lid_part();
}
