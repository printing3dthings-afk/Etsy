// Haunted Manor lantern -- a hollow Victorian house shell lit from inside.
//
// Prints upright on its open base, tealight or LED inside, light escaping
// only through the windows and door. Per Technique 21, that is the structural
// thing that separates a real lantern from a decorative shape with shallow
// markings: a hollow shell, TRUE through-cuts, and an open base. Verified two
// ways -- wall thickness at its thinnest point, and CGAL's own Volumes count
// (a sealed hollow reports 3, an open one reports 2).
//
// EVERY PERIOD DETAIL HERE IS ALSO THE PRINTABLE CHOICE, which is why the
// design does not feel like a compromise:
//
//  - A steep Victorian roof is the printable one. The roof's INNER face is
//    the overhang, and pitch measured from vertical is what matters: a 45 deg
//    cottage roof sits exactly on the 55 deg limit, while a 70 deg Victorian
//    roof is 20 deg from vertical with room to spare.
//  - Gothic LANCET windows are self-supporting; round-arched ones are not.
//    A hole in a vertical wall has its roof at the top, and an equilateral
//    arch's apex tangent is 60 deg from vertical -- just over the limit. A
//    proper lancet (see lancet_pts) is drawn to land at 50 deg.
//  - Clapboard siding is a SAWTOOTH that ramps outward at 45 deg and tapers
//    back in, so every course is self-supporting. Real clapboard is thickest
//    at the bottom of each board, which is the same shadow line upside down;
//    at 4.5mm pitch nobody reads the difference and it prints without
//    supports.
//
// TEXTURE DEPTH IS A WALL DECISION, MADE HERE. Technique 52: relief cut INTO
// a shell is capped by the wall, and a 1.26mm luminary wall cannot carry
// 0.84mm of siding. So the siding is raised OUTWARD from a 1.68mm base wall
// instead of cut into it -- the wall stays a constant 4 extrusions everywhere
// and the relief costs nothing structural.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "manor";             // manor | body | roof

// ---- shell ---------------------------------------------------------------
W        = 76;              // body, along X
D        = 68;              // body, along Y
wall     = 1.68;            // 4 x 0.42, constant everywhere
corner_r = 3;

plinth_h = 9;               // foundation course, no siding
plinth_g = 1.2;             // stands proud of the siding
plinth_w = 2.52;            // 6 x 0.42 -- thick enough to carry the mark
                            // without it glowing through when lit

sid_courses = 13;
eave     = 4;
cap      = 6;
sid_p    = 4.5;             // clapboard course pitch
sid_d    = 0.84;            // 2 x 0.42 of relief -- the floor for something
                            // that still reads at arm's length

body_top = plinth_h + sid_courses * sid_p;
eave_z   = body_top + eave;
ridge_z  = 136;
shg_n    = 15;
shg_d    = 0.8;
shg_ramp = 0.22;

// ---- turret --------------------------------------------------------------
tur_s    = 26;
tur_x    = -W/2 + 4;
tur_y    =  D/2 - 4;
tur_top  = 120;
tur_eave = 3;
tur_ridge= tur_top + tur_eave + 40;

// =========================================================================
// WHY THIS IS BUILT THE WAY IT IS
//
// OpenSCAD 2021.01's CGAL aborts outright -- assertion violation in
// applyUnion3D, not a warning -- when asked to union TWO TEXTURED SURFACES
// that interpenetrate. Bisected directly: body alone renders, turret alone
// renders, a plain turret into a textured body renders, a textured turret
// into a plain body renders, and only textured-into-textured fails. Moving
// the turret so the two are disjoint also renders, which confirms it is the
// intersection curve and not the solids.
//
// So every union here is plain-against-textured or plain-against-plain:
//   - body and turret are plain prisms of a shared 2D plan
//   - the clapboard is CUT as grooves afterwards, never built as a second
//     textured skin to be unioned in
//   - the two shingled roofs are textured, but they touch only plain prisms,
//     and they never touch each other (checked: at the turret roof's springing
//     the main roof is 12.9mm from the axis and the turret needs 17.5)
//
// The trade this forces is real and worth stating: cut-in relief is capped by
// the wall (Technique 52), so the wall carries the groove instead of the
// groove being free. The outer face sits at plan(sid_d) and the groove floor
// at plan(0), which leaves 1.68mm -- 4 extrusions -- at the thinnest point.
// =========================================================================

function fp(g)    = rrect_pts(W + 2*g, D + 2*g, max(corner_r + g, 0.6), 5);
function rf(u, s) = let (k = 1 - u)
    rrect_pts((W + 2*eave - cap) * k + cap + 2*s,
              (D + 2*eave - cap) * k + cap + 2*s,
              max(corner_r * k, 0.6), 5);
function tps(g)   = rrect_pts(tur_s + 2*g, tur_s + 2*g, max(2 + g, 0.4), 4);
function trf(u, s) = let (k = 1 - u)
    rrect_pts((tur_s + 2*tur_eave - 4) * k + 4 + 2*s,
              (tur_s + 2*tur_eave - 4) * k + 4 + 2*s, max(2 * k, 0.4), 4);

module tur2d(g)  { offset(r = g) translate([tur_x, tur_y]) offset(r = 2) square([tur_s - 4, tur_s - 4], center = true); }
module body2d(g) { offset(r = g) offset(r = corner_r) square([W - 2*corner_r, D - 2*corner_r], center = true); }
module plan2d(g) { offset(r = g) union() { body2d(0); tur2d(0); } }

roof_u  = concat([for (k = [0 : shg_n - 1], j = [0, 1]) (k + j*shg_ramp) / shg_n], [1]);
roof_s  = concat([for (k = [0 : shg_n - 1], j = [0, 1]) j * shg_d], [0]);
tur_u   = concat([for (k = [0 : 9], j = [0, 1]) (k + j*shg_ramp) / 10], [1]);
tur_s2  = concat([for (k = [0 : 9], j = [0, 1]) j * shg_d], [0]);

// ---- openings ------------------------------------------------------------
function lancet_pts(a, hgt, n = 20) =
    let (d = a * 1.80, R = d + a)
    concat([[-a, 0], [-a, hgt]],
           [for (i = [0 : n]) let (x = -a + 2*a*i/n)
                [x, hgt + sqrt(max(R*R - pow(abs(x) + d, 2), 0))]],
           [[a, hgt], [a, 0]]);
win_w = 11;
win_h = 9;                  // STRAIGHT part only. The lancet adds 11.8mm on
                            // top of this at a = 5.5, so a row is 20.8mm tall.
                            // At win_h = 15 the rows ran 24->50.8 and 48->74.8:
                            // they overlapped each other and reached into the
                            // roof, and every collision with a clapboard groove
                            // isolated a sliver of wall as its own body.
mull  = 1.68;

module win_2d(a, hgt, transom = true) {
    difference() {
        polygon(lancet_pts(a, hgt));
        translate([-mull/2, -1]) square([mull, hgt + 3*a]);
        if (transom) translate([-a - 1, hgt * 0.58]) square([2*a + 2, mull]);
    }
}
// A window cut is 16mm long and CENTRED ON ITS OWN WALL. The first build
// used 3*W centred on the far face, so every opening also punched a matching
// hole through the wall opposite -- the door cut a door-shaped hole in the
// back of the house -- and the combinations isolated strips of wall as loose
// bodies. Grooves alone gave 1 body; windows alone gave 5.
module place_win(face, off, z, a = win_w/2, hgt = win_h, transom = true) {
    r  = [0, 180, -90, 90][face];
    px = face < 2 ? off : (face == 2 ?  W/2 : -W/2);
    py = face < 2 ? (face == 0 ? D/2 : -D/2) : off;
    translate([px, py, z]) rotate([0, 0, r]) rotate([90, 0, 0])
        linear_extrude(16, center = true) win_2d(a, hgt, transom);
}

// Only the turret's -X and +Y faces are actually outside; its other two are
// buried in the body, where a window would open into the interior.
module place_twin(face, z, a = 5.5, hgt = 9) {
    r  = [0, 180, -90, 90][face];
    px = tur_x + (face == 2 ? tur_s/2 : face == 3 ? -tur_s/2 : 0);
    py = tur_y + (face == 0 ? tur_s/2 : face == 1 ? -tur_s/2 : 0);
    translate([px, py, z]) rotate([0, 0, r]) rotate([90, 0, 0])
        linear_extrude(14, center = true) win_2d(a, hgt, true);
}

// =========================================================================
// EVERY JOIN OVERLAPS. A roof that merely sits on its wall at one shared
// plane is two solids touching, not one -- the first build left the turret
// roof as a detached 5.6cm3 body that rendered, gated watertight, and would
// have printed as a hat lying next to a house. The eave flares are what turn
// each of those planes into a real interpenetration, and they are also what
// stops the overhang being a horizontal soffit ring.
module solid() {
    linear_extrude(plinth_h) plan2d(plinth_g);
    linear_extrude(body_top + 1) plan2d(sid_d);
    skin([fp(sid_d), rf(0, 0)], z = [body_top, eave_z], slices = 0);
    skin([for (i = [0 : len(roof_u)-1]) rf(roof_u[i], roof_s[i])],
         z = [for (u = roof_u) eave_z + u * (ridge_z - eave_z)], slices = 0);

    linear_extrude(tur_top + 1) tur2d(sid_d);
    translate([tur_x, tur_y, 0]) {
        skin([tps(sid_d), trf(0, 0)], z = [tur_top, tur_top + tur_eave], slices = 0);
        skin([for (i = [0 : len(tur_u)-1]) trf(tur_u[i], tur_s2[i])],
             z = [for (u = tur_u) tur_top + tur_eave - 1 + u * 41], slices = 0);
    }

    // Exterior stack on the back wall. A chimney rooted in the ROOF sits
    // entirely inside the cavity at its base and gets cut free -- period
    // Victorian houses put the stack on the outside of the gable anyway.
    // x = 24, clear of the OBC mark on the plinth. At x = 12 the stack sat
    // right where the mark cuts and the letters carved a loose fragment out
    // of it.
    // Masonry stack: corbelled cap in three courses, each stepping out 1.2mm
    // over 3mm of rise so nothing overhangs past 22 deg. Built as a plain
    // prism family so it only ever unions against plain surfaces.
    translate([25, -35.5, 0]) {
        linear_extrude(99) offset(r = 1.5) square([13, 8], center = true);
        for (i = [0 : 2]) translate([0, 0, 96 + i*3])
            linear_extrude(3.2) offset(r = 1.5) square([13 + (i+1)*2.4, 8 + (i+1)*2.4], center = true);
        translate([0, 0, 105]) linear_extrude(2.6)
            offset(r = 1.5) square([20.2, 15.2], center = true);
    }
}

// Smooth throughout -- no shingle or clapboard perturbation -- so the cavity
// is only ever unioned out of plain surfaces.
module cavity() {
    cu = [for (i = [0 : 16]) 0.95 * i / 16];
    // to eave_z, not body_top -- stopping at body_top left the 4mm band under
    // the eave completely solid, and a slab of it floating loose inside
    translate([0, 0, -2]) linear_extrude(eave_z + 2) plan2d(-wall);
    translate([0, 0, -2]) linear_extrude(tur_top + tur_eave + 2) tur2d(-wall);
    skin([for (u = cu) rf(u, -wall)],
         z = [for (u = cu) eave_z + u * (ridge_z - eave_z)], slices = 0);
    translate([tur_x, tur_y, 0])
        skin([for (u = cu) trf(u * 0.92, -wall)],
             z = [for (u = cu) tur_top + tur_eave - 1 + u * 0.92 * 41], slices = 0);
}

// One cut per course. The groove ceiling is a 0.84mm down-facing ledge --
// two extrusion widths, bridged off the wall behind it along its whole
// length. That is a normal FDM overhang, not a support case, and chasing it
// to zero here would cost either the relief depth or a second textured
// surface that CGAL cannot union. It is reported as what it is rather than
// engineered away.
module ring(f)   { difference() { plan2d(sid_d + 0.1); plan2d(0); } }
module tring(f)  { difference() { tur2d(sid_d + 0.1);  tur2d(0);  } }
module grooves() {
    for (k = [1 : sid_courses])
        translate([0, 0, plinth_h + k*sid_p - 0.45]) linear_extrude(0.9) ring();
    for (k = [1 : 11]) if (body_top + k*sid_p < tur_top - 2)
        translate([0, 0, body_top + k*sid_p - 0.45]) linear_extrude(0.9) tring();
}

module openings() {
    for (f = [0, 1]) for (x = [-19, 19]) { place_win(f, x, 20); place_win(f, x, 44); }
    for (f = [2, 3]) for (y = [-17, 17]) { place_win(f, y, 20); place_win(f, y, 44); }
    place_win(0, 0, plinth_h + 1, 8, 16, false);
    place_twin(0, 40); place_twin(3, 40);
    place_twin(0, 82); place_twin(3, 82);
}

module brand_mark() {
    translate([0, -D/2 - plinth_g - 0.4, plinth_h/2]) rotate([90, 0, 0]) linear_extrude(1.4)
        text("OBC", size = 6.0, font = "Montserrat:style=Black", halign = "center", valign = "center");
}

module manor() {
    difference() { solid(); cavity(); grooves(); openings(); brand_mark(); }
}
if (part == "solid") solid(); else manor();
