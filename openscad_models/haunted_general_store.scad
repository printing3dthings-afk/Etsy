// Haunted General Store lantern -- building #3 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). BOARD-AND-BATTEN walls, TALL DIAMOND
// windows, and a FALSE FRONT that has tipped forward and sideways, shored up
// by two timber props, over a steep shed roof. A hollow shell lit from inside
// by a battery LED tealight: open base, true through-cut windows.
//
// The town's variety plan (Scott, 2026-09-25) gives every building its own
// walls, windows and roof; this is the general store's set. The relief and
// inlay machinery is the bakery's (haunted_bakery.scad) and the WHY behind it
// is there.
//
// COLOUR PARTS, ONE PRINT (haunted_general_store.3mf):
//   body    walls, false front, plinth, step, battens
//   roof    shed roof with its tin ribs, the stovepipe, the barrels' hoops
//   trim    window and door frames, muntins, doors, sign board, corner
//           boards, the false front's cap
//   accent  the barrels, the MERCANTILE letters, the two props
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// THE ROOF PRINTS IN ONE PIECE because it is steep: its inside is a 50 deg
// ceiling falling from behind the false front to a 51 mm back wall, the same
// slope as the bakery's ceiling. A shallower shed would be a ceiling the
// printer cannot make.
//
// THE LEAN. The whole storefront -- the false front, its door, windows and
// sign -- is sheared 2.5 deg forward and 3 deg to the right, from the plate
// up. The side walls stay plumb and run forward to meet it. Its reliefs are
// sheared a little harder than the bakery's (SH 1.4, 35.5 deg from vertical)
// so that, tipped forward, their undersides are still 38 deg from vertical.
//
// TEALIGHT. The room is 68.6 x 48.6 mm clear; its ceiling is 50.7 mm up even
// at the back edge of a 46 mm circle round the centre.

include <BOSL2/std.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ----------------------------------------------------------------
W        = 72;              // side wall to side wall
D        = 52;              // front (-Y) to back
wall     = 1.68;            // 4 x 0.42
plinth_h = 8;               // shared by every building in the town
Wh = W/2;  Dh = D/2;
SH       = 1.4;             // relief shear, harder than the bakery's for the lean

// ---- battens ----------------------------------------------------------------
bd    = 0.84;               // batten depth, proud of the boards
bat_w = 1.68;
bat_p = 6;                  // batten spacing
plinth_o = bd + 0.84;

// ---- roof ------------------------------------------------------------------
z_back = 51;                // roof top at the back wall's face
r_ang  = 50;                // shed pitch -- and the ceiling's, 50 deg
tr     = 2.52;
tv     = tr / cos(r_ang);   // slab, measured vertically
function z_top(y) = z_back + (Dh - y) * tan(r_ang);

// ---- the false front ---------------------------------------------------------
Hf  = 124;                  // its top, before the lean
fx0 = -42;  fx1 = 38;       // its ends at the plate: 6 past the left wall, 2
                            // past the right, so after sliding right it still
                            // covers the left wall all the way up the roof
lean_f = 2.5;               // forward, deg
lean_s = 3;                 // to the right, deg
kx = tan(lean_s);  ky = tan(lean_f);
module lean() multmatrix([[1, 0, kx, 0], [0, 1, -ky, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
function leaned(p) = [p[0] + kx * p[2], p[1] - ky * p[2], p[2]];

// Place children on a wall. Local x runs along the wall, local y is world
// up, local z is out from the wall's face. For faces 0, 2 and 3, u is the
// WORLD coordinate along the wall (x on 0, y on 2 and 3); face 1 is the false
// front, and everything on it goes through lean().
//   face 0 = back (+Y), 1 = front (-Y), 2 = right (+X), 3 = left (-X)
module face_tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module on_face(face, u, z) {
    if (face == 1) lean() face_tf(1, u, z) children();
    else face_tf(face, u, z) children();
}
// a world coordinate along face f, in that face's local x
function loc_u(f, u) = (f == 0 || f == 3) ? -u : u;
module shear_up() multmatrix([[1, 0, 0, 0], [0, 1, SH, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
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

// ---- regions ----------------------------------------------------------------
// Everything below a plane parallel to the roof, `drop` under its top.
module below_roof(drop = 0) {
    rotate([90, 0, 90]) translate([0, 0, -100]) linear_extrude(200)
        polygon([[-Dh - 30, -5], [Dh + 20, -5], [Dh + 20, z_top(Dh + 20) - drop], [-Dh - 30, z_top(-Dh - 30) - drop]]);
}
// Behind the false front's outer face, or its inner face.
module behind_front(inner = false) {
    lean() translate([-300, -Dh + (inner ? wall : 0), -10]) cube([600, 400, 400]);
}

// ---- walls -----------------------------------------------------------------------
module front_slab() { lean() translate([fx0, -Dh, 0]) cube([fx1 - fx0, wall, Hf]); }
// Side and back walls run forward past the false front and are cut at its
// face, so they meet it however far it has tipped.
module u_walls() {
    intersection() {
        difference() {
            translate([-Wh, -Dh - 12, 0]) cube([W, D + 12, 200]);
            translate([-Wh + wall, -Dh - 13, -1]) cube([W - 2 * wall, D + 13 - wall, 202]);
        }
        behind_front();
        below_roof();
    }
}
module room() {
    intersection() {
        translate([-Wh + wall, -Dh - 20, -2]) cube([W - 2 * wall, D + 20 - wall, 300]);
        behind_front(true);
        below_roof(tv);
    }
}
module plinth() {
    linear_extrude(plinth_h) offset(delta = plinth_o) union() {
        translate([-Wh, -Dh]) square([W, D]);
        translate([fx0, -Dh - 1]) square([fx1 - fx0 + kx * plinth_h + 1, wall + 1]);
    }
}

// ---- openings -----------------------------------------------------------------
// TALL DIAMONDS, the general store's window in the town plan. Their edges are
// 62 deg from horizontal, so after the 3 deg lean they are 59 at worst,
// still above the 58 a corner needs.
d_ang = 62;
function diamond_pts(a) = [[0, 0], [a, a * tan(d_ang)], [0, 2 * a * tan(d_ang)], [-a, a * tan(d_ang)]];
function diamond_h(a) = 2 * a * tan(d_ang);
mull = 1.68;
//   [face, u, z, a]
WINDOWS = [
    [1, -24, 16, 6],   [1, 20, 16, 6],               // the display windows
    [1, -24, 62, 4],   [1, 20, 62, 4],               // the storeroom above
    [0, -16, 16, 5],   [0, 16, 16, 5],
    [2,  -6, 16, 5],   [2, -10, 58, 4],
    [3,  -6, 16, 5],   [3, -10, 58, 4],
];
module win_outline(w) { polygon(diamond_pts(w[3])); }
// Two bars through the centre, parallel to the edges: four small diamonds,
// every bar at 62 deg.
module win_bars(w) {
    translate([0, w[3] * tan(d_ang)]) for (s = [-1, 1]) rotate(s * d_ang)
        square([6 * w[3], mull], center = true);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
fr_w = 1.7;
fr_t = bd + 0.84;
// Diamond frames are 3.2 wide, not the bakery's 1.7. A relief's underside --
// and its hole's ceiling -- is sheared back 2.9 mm at its face, and a 62 deg
// arm 1.7 wide is only 3.6 mm tall: every arm, above and below, was left
// about 0.7 mm thick at the front and the gate measured it as sub-bead round
// every window. At 3.2 an arm is 6.8 tall and keeps 3.9.
fr_wd = 3.2;
module win_frame_outer(w) { offset(r = fr_wd + 0.3) win_outline(w); }
module frame_holes() {
    for (w = WINDOWS) on_face(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) win_outline(w);
}
module openings() {
    for (w = WINDOWS) on_face(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) win_outline(w);
    on_face(1, door_x, plinth_h)
        translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) polygon(door_pts(door_a, door_h));
}

// ---- door, step --------------------------------------------------------------------
// A double door: straight sides under a 62 deg peak, two leaves split by an
// engraved line, each with a small diamond light.
function door_pts(a, hgt) = [[-a, 0], [-a, hgt], [0, hgt + a * tan(d_ang)], [a, hgt], [a, 0]];
door_x = -2;
door_a = 8;
door_h = 22;
module door_leaf() {
    on_face(1, door_x, plinth_h) translate([0, 0, -wall]) difference() {
        // The leaf's HEAD sits 0.2 inside the doorway's (the frame laps over
        // the gap); below the spring it fills the doorway and stands on the
        // threshold. Cut to the doorway itself, the two heads met at one tip
        // on the wall's inner face and, sheared by the lean, left 16
        // non-manifold edges there.
        linear_extrude(wall - 0.2) difference() {
            union() {
                intersection() { polygon(door_pts(door_a, door_h)); translate([-20, -1]) square([40, door_h + 1]); }
                offset(delta = -0.2) polygon(door_pts(door_a, door_h));
            }
            for (s = [-1, 1]) translate([s * 4, 21]) polygon(diamond_pts(1.8));
        }
        // the split between the leaves stops below the head, in a 62 deg
        // point: run into the head's own point, it met the frame and both
        // leaves on one edge
        translate([0, 0, wall - 0.9]) linear_extrude(1)
            polygon([[-0.3, -1], [-0.3, door_h + 5], [0, door_h + 5 + 0.3 * tan(d_ang)], [0.3, door_h + 5], [0.3, -1]]);
    }
}
module door_frame() {
    on_face(1, door_x, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
        difference() {
            intersection() { offset(r = fr_w) polygon(door_pts(door_a, door_h));
                             translate([-30, 0]) square([60, 100]); }
            // 0.3 INSIDE the doorway, lapping the leaf. Cut exactly to the
            // doorway, its head lay on the leaf's own head edges; under the
            // lean's shear the two no longer met exactly and left
            // non-manifold edges.
            translate([0, -1]) offset(delta = -0.3) polygon(door_pts(door_a, door_h + 1));
        }
}
st_w = 22;  st_d = 8;
module step() { translate([door_x - st_w/2, -Dh - st_d, 0]) cube([st_w, st_d + 0.5, plinth_h]); }

// ---- sign ------------------------------------------------------------------------------
// 12 tall: its sheared underside loses 2.9 mm at the face, and the letters'
// bottoms must stay above that.
sg_u = -2;  sg_z = 94;  sg_w = 56;  sg_h = 12;
sg_tilt = -3;               // against the lean, so it reads as hung crooked
module sign_board() {
    on_face(1, sg_u, sg_z) rotate([0, 0, sg_tilt])
        relief_up(-0.4, fr_t) translate([-sg_w/2, -sg_h/2]) square([sg_w, sg_h]);
}
module sign_letters() {
    on_face(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0.3, fr_t - 0.8])
        linear_extrude(0.8) text("MERCANTILE", size = 5.2, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.04);
}
// The false front's cap: a band 3 tall across its top, sheared under.
module front_cap() {
    on_face(1, (fx0 + fx1) / 2, Hf - 3)
        relief_up(-0.4, bd + 0.1) translate([-(fx1 - fx0) / 2, 0]) square([fx1 - fx0, 3]);
}

// ---- battens -------------------------------------------------------------------------------
// Vertical strips standing on the plinth. Above a window, door or sign they
// resume on a sheared underside: the cut-outs are sheared with them.
function wall_span(f) = f == 1 ? [fx0 + 3, fx1 - 3] : f == 0 ? [-Wh + 5, Wh - 5]
                      : f == 2 ? [-Dh + 3, Dh - 7] : [-Dh + 7, Dh - 3];   // clear of the corner boards
function keepouts(f) = concat(
    [for (w = WINDOWS) if (w[0] == f) let (h = w[3] + fr_wd + 0.3 + 1.5)
        [loc_u(f, w[1]) - h, loc_u(f, w[1]) + h, w[2] - fr_wd - 0.3 - 2, w[2] + diamond_h(w[3]) + fr_wd + 0.3 + 1.5]],
    f == 1 ? [[door_x - door_a - fr_w - 1.5, door_x + door_a + fr_w + 1.5, 0, plinth_h + door_h + door_a * tan(d_ang) + fr_w + 1.5],
              [sg_u - sg_w/2 - 3, sg_u + sg_w/2 + 3, sg_z - sg_h/2 - 4, sg_z + sg_h/2 + 4]] : []);
module battens(f) {
    sp = wall_span(f);
    on_face(f, 0, 0) shear_up() difference() {
        for (u = [sp[0] : bat_p : sp[1]]) translate([u - bat_w/2, plinth_h, -0.4]) cube([bat_w, 200, bd + 0.4]);
        for (k = keepouts(f)) translate([k[0], k[2], -5]) cube([k[1] - k[0], k[3] - k[2], 10]);
    }
}
module all_battens() {
    intersection() { battens(1); lean() translate([-200, -200, 0]) cube([400, 400, Hf]); }
    intersection() { union() { battens(0); battens(2); battens(3); } below_roof(); }
}
module corner_boards() {
    intersection() {
        translate([0, 0, plinth_h]) linear_extrude(200) difference() {
            for (sx = [-1, 1]) translate([sx * (Wh - 0.25) - 3.25, Dh - 5.5]) square([6.5, 5.5 + fr_t]);
            translate([-Wh + 0.4, -Dh]) square([W - 0.8, D - 0.4]);
        }
        linear_extrude(200) offset(delta = fr_t) translate([-Wh, -Dh]) square([W, D]);
        below_roof();
    }
}

// ---- roof -------------------------------------------------------------------------------------
module roof_slab() {
    intersection() {
        difference() { below_roof(); below_roof(tv); }
        translate([-Wh, -Dh - 20, 0]) cube([W, D + 20, 300]);
        behind_front(true);
    }
}
// Tin ribs running down the slope: vertical sides and a top parallel to the
// roof, so no face of them points down.
module ribs() {
    intersection() {
        for (x = [-Wh + 3 : 5 : Wh - 3]) hull() for (y = [-Dh - 8, Dh])
            translate([x - 0.72, y - 0.005, z_top(y) - 0.6]) cube([1.44, 0.01, 1.5]);
        behind_front(true);
        translate([-Wh, -Dh - 20, 0]) cube([W, D + 20, 300]);
    }
}
// A stovepipe tipped 8 deg toward the back, ending in a plain taper.
module stovepipe() {
    translate([16, 10, z_top(10) - 6]) rotate([-8, 0, 0]) {
        cylinder(r = 2.2, h = 20, $fn = 32);
        translate([0, 0, 20]) cylinder(r1 = 2.2, r2 = 0.8, h = 2.6, $fn = 32);
    }
}

// ---- barrels ------------------------------------------------------------------------------------
// Standing on the plate against the plinth, sunk 0.4 into it. The bulge
// widens 0.6 over half the height, 10 deg from vertical. Hoops are flush
// inlays in the roof's colour.
//   [x, height, base radius]
BARRELS = [[16, 11, 4.2], [25, 9, 3.8]];     // clear of the door step
b_bulge = 0.6;
function b_r(q, z) = q[2] + b_bulge * sin(180 * z / q[1]);
function b_y(q) = -Dh - plinth_o - q[2] - b_bulge + 0.4;
module barrel_body(q, g = 0) {
    translate([q[0], b_y(q), 0]) rotate_extrude($fn = 48)
        polygon(concat([[0, 0]], [for (i = [0 : 12]) let (z = q[1] * i / 12) [b_r(q, z) - g, z]], [[0, q[1]]]));
}
module hoops() {
    for (q = BARRELS) difference() {
        intersection() {
            barrel_body(q);
            for (z0 = [1.2, q[1] - 2.2]) translate([q[0] - 10, b_y(q) - 10, z0]) cube([20, 20, 1.0]);
        }
        barrel_body(q, 0.6);
    }
}
module barrels() { for (q = BARRELS) barrel_body(q); }

// ---- props -------------------------------------------------------------------------------------
// Two timbers from the street up to the false front, where they are let 1 mm
// into its face. 80 deg from horizontal; a pad under each foot.
PROPS = [[-39, 96], [35, 96]];      // [x at the facade, height]
pr_s = 2.6;
module props() {
    for (p = PROPS) let (top = leaned([p[0], -Dh, p[1]]) + [0, 1.0, 0], foot = [p[0] - 2, -Dh - 20, 0]) {
        hull() {
            translate(foot + [-pr_s/2, -pr_s/2, 1.2]) cube([pr_s, pr_s, 0.01]);
            translate(top + [-pr_s/2, -pr_s/2, 0]) cube([pr_s, pr_s, 0.01]);
        }
        translate(foot + [-2.5, -2.5, 0]) cube([5, 5, 1.21]);
    }
}

// ---- mark ------------------------------------------------------------------------------------------
module brand_mark() {
    translate([door_x, -Dh - st_d / 2, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- parts ---------------------------------------------------------------------------------------------
module body_solid() {
    plinth();
    front_slab();
    u_walls();
    all_battens();
    step();
}
module trim_raw() {
    for (w = WINDOWS) on_face(w[0], w[1], w[2]) {
        relief_up(-0.4, fr_t) { win_frame_outer(w); offset(r = 0.3) win_outline(w); }
        translate([0, 0, -0.4]) linear_extrude(bd + 0.4) win_muntins(w, 0.6);
    }
    door_frame();
    door_leaf();
    sign_board();
    corner_boards();
    front_cap();
}
module accent_raw() {
    difference() { barrels(); hoops(); }
    sign_letters();
    props();
}
module roof_raw() {
    difference() {
        union() { roof_slab(); ribs(); stovepipe(); }
        room(); front_slab();
    }
    hoops();
}
module roof_part()   { roof_raw(); }
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_solid();
        room(); openings(); frame_holes(); trim_raw(); accent_raw(); roof_raw(); brand_mark();
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
    color("#5E6B57") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
}
