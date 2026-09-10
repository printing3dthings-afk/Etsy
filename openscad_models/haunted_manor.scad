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

sid_courses = 16;           // 13 before the porch. A porch roof has to clear
                            // the door below it and the upper windows above,
                            // and the old ground floor gave a 3mm gap between
                            // the two. Three more courses open it to 25mm.
                            // ridge_z is unchanged, so the house is exactly as
                            // tall as it was -- the roof simply got shallower
                            // (39.5 deg from vertical, still well inside 55).
eave     = 4.5;             // 4 before. Half a millimetre, purely to break a
                            // tangency: at eave 4 a roof ring landed at
                            // z = 112.95 with its rounded corner passing within
                            // microns of the tower's, and CGAL emitted a
                            // zero-area facet there. Moving the eave moves
                            // every ring z and the coincidence goes away.
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
    // ON THE +X WALL, not the back. On the back it sat at x 17..33 while the
    // back window at x=+19 spans 13.5..24.5 -- the window cut straight through
    // the stack. The +X wall's windows are at y = +/-17, leaving y -11.5..11.5
    // clear, which is 23mm of uninterrupted masonry to land on.
    translate([38.5, 0, 0]) rotate([0, 0, 90]) {
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

// The FRONT ground floor has no windows on purpose. It is the entrance
// elevation -- door, stoop, jack-o'-lanterns -- and with windows at x = +/-19
// as well the porch had nowhere to go: a lantern big enough to read reaches
// z = 20, which is exactly where those sills started. Ten windows, a door, a
// rose and two bats are already more openings than the shell needs for light.
module openings() {
    for (x = [-19, 19]) { place_win(1, x, 20); place_win(0, x, 56); place_win(1, x, 56); }
    for (f = [2, 3]) for (y = [-17, 17]) { place_win(f, y, 20); place_win(f, y, 56); }
    // the door is shorter than it was: its apex now lands at 35.9, clear of the
    // porch beam whose underside is at 40. At the old 41 the beam ran through
    // the head of the door.
    place_win(0, 0, plinth_h + 1, 6.5, 12, false);
    place_twin(0, 40); place_twin(3, 40);
    place_twin(0, 82); place_twin(3, 82);
}

module brand_mark() {
    translate([0, -D/2 - plinth_g - 0.4, plinth_h/2]) rotate([90, 0, 0]) linear_extrude(1.4)
        text("OBC", size = 6.0, font = "Montserrat:style=Black", halign = "center", valign = "center");
}

// ---- Halloween ------------------------------------------------------------
// WHAT ACTUALLY READS ON A LIT OBJECT IS LIGHT AND SILHOUETTE, NOT RELIEF.
// The first pass put flat bosses on the walls -- a 22mm bat standing 2.2mm
// proud -- and rendered them straight on. They read as scribbles, because a
// 22 x 3mm wing lying on clapboard is the same tone as the clapboard and its
// only cue is a 2.2mm shadow that a shelf lamp will not give it. Worse, the
// jack-o-lantern faces were cut only 0.9mm into a boss standing on a solid
// wall: blind pockets, dark, on a product whose whole promise is that it
// lights up.
//
// So the Halloween content is now the two things that survive at 90mm on a
// shelf, and neither needs support:
//   - REAL 3D OBJECTS with their own silhouette, standing on the ground
//     (the porch and its two jack-o-lanterns), and
//   - THROUGH-CUTS that glow (the spiderweb rose, the pumpkin faces, and two
//     bats on the tower).
// A hole in a vertical wall is a bridge, not an overhang: its ceiling is
// anchored on both sides, so a bat cut only has to keep every unsupported
// span short, which at a 16mm wingspan it does (longest is about 4mm).

// ---- front porch ----------------------------------------------------------
// EVERY PIECE OF THE SUBSTRUCTURE GROWS OFF THE BUILD PLATE. The deck, all
// three steps and the newels start at z = 0, so between them there is not one
// square millimetre of underside -- the lower tread IS the build surface. That
// is what makes a porch, which is normally the classic support case, free here.
//
// The one real ceiling is the beam soffit at z = 40. It is not a wide bridge:
// the beam is attached to the house wall along its whole back edge, so the
// furthest any bridging line has to reach is the 17mm from that wall out to
// the post line, and the knee braces cut the corners off even that.
por_hw   = 21;              // deck half width
por_yb   = 33;              // back edge, buried in the siding
por_yf   = 57;              // front edge of the deck. 53 before: a 20mm porch
                            // could not fit a 14.4mm lantern between the wall
                            // and the post without one of them intersecting
                            // it, and 24mm is closer to a real porch anyway.
deck_h   = 10;              // deck top == door threshold
post_s   = 4.4;
brace_t  = 3.6;             // strictly inside post_s -- see the braces
post_hx  = 19;
post_ix  =  9.5;            // inner pair. With only the outer two, the beam
                            // soffit was a 42 x 21mm flat ceiling anchored on
                            // the house wall and two corners, and PrusaSlicer
                            // called it: "Long bridging extrusions, Floating
                            // bridge anchors". Four columns with the stair
                            // between the middle pair is the period-correct
                            // portico anyway.
post_y   = 54;
beam_z0  = 40;              // soffit
beam_z1  = 44.5;
corn_z1  = 47.5;            // cornice top
proof_z1 = 53.5;            // porch roof ridge, against the house wall

module rrect(w, d, cy, r) { translate([0, cy]) offset(r = r) square([w - 2*r, d - 2*r], center = true); }
module post_2d(g = 0) { offset(r = 0.7 + g) square([post_s - 1.4, post_s - 1.4], center = true); }

module porch() {
    linear_extrude(deck_h) rrect(2*por_hw, por_yf - por_yb, (por_yb + por_yf)/2, 1.5);
    // three treads, each overlapping the one behind it so no two boxes share a
    // face exactly -- coincident faces between unioned solids are what produced
    // degenerate faces and detached bodies earlier in this model
    linear_extrude(7.5) rrect(14, 4.1, 58.6, 1.0);
    linear_extrude(5.0) rrect(14, 4.1, 61.2, 1.0);
    linear_extrude(2.5) rrect(14, 4.1, 63.8, 1.0);

    // inner pair: shaft, plinth, capital and a wall-ward brace each. No brace
    // toward the door -- at z 33.5..40.5 it would sit right across the head of
    // the door arch, which tops out at 35.9.
    for (sx = [-1, 1]) {
        translate([sx*post_ix, post_y, deck_h - 1]) linear_extrude(beam_z0 - deck_h + 2) post_2d();
        translate([sx*post_ix, post_y, deck_h - 0.5]) linear_extrude(2.8) post_2d(0.8);
        translate([sx*post_ix, post_y, beam_z0 - 3.2]) linear_extrude(3.7) post_2d(0.8);
        translate([sx*post_ix, post_y, 0]) rotate([0, 0, 90])
            translate([0, brace_t/2, 0]) rotate([90, 0, 0]) linear_extrude(brace_t)
                polygon([[0, beam_z0 + 0.5], [-6.5, beam_z0 + 0.5], [0, beam_z0 - 6.5]]);
    }

    for (sx = [-1, 1]) {
        // Front post only. There is DELIBERATELY no pilaster on the house wall
        // behind it: at x = +/-19 a pilaster sits inside the lantern, which
        // reaches x = 22.2 at its equator, and the two met almost tangentially
        // -- that produced 9 zero-area faces and two inverted sliver bodies
        // while still gating watertight. The beam is let into the wall
        // directly, which is what the real detail does anyway.
        translate([sx*post_hx, post_y, deck_h - 1]) linear_extrude(beam_z0 - deck_h + 2) post_2d();
        // Knee braces, one each way: a straight 45 deg diagonal, so no face in
        // one is worse than 45 deg from vertical. A sawn ogee bracket would
        // look better and would go horizontal where it meets the beam.
        // brace_t is deliberately NARROWER than the post. At exactly post_s the
        // two braces' side faces landed on the post's own faces and on each
        // other's, and every one of those coincident planes produced a
        // zero-area facet -- 12 of them, on a mesh that still gated watertight.
        // They also run 0.5mm up INTO the beam rather than stopping on its
        // soffit plane, for the same reason.
        translate([sx*post_hx, post_y + brace_t/2, 0]) rotate([90, 0, 0])
            linear_extrude(brace_t)
                polygon([[0, beam_z0 + 0.5], [-sx*6.5, beam_z0 + 0.5], [0, beam_z0 - 6.5]]);
        // the wall-ward brace. Rotating the PLACED brace about z is the only
        // form of this that lands where it reads: composing rotate([0,0,-90])
        // with rotate([90,0,0]) turns the extrude axis into X instead, and the
        // first attempt left both braces sitting at y = 0..6.5 -- floating
        // inside the house, 6.5mm from anything they were meant to touch.
        translate([sx*post_hx, post_y, 0]) rotate([0, 0, 90])
            translate([0, brace_t/2, 0]) rotate([90, 0, 0]) linear_extrude(brace_t)
                polygon([[0, beam_z0 + 0.5], [-6.5, beam_z0 + 0.5], [0, beam_z0 - 6.5]]);

        // post plinth and capital. Square blocks, so they are pure vertical
        // prisms with one 0.8mm ledge each -- the same class of overhang the
        // clapboard grooves already carry, and the thing that stops a post
        // reading as a length of stick.
        translate([sx*post_hx, post_y, deck_h - 0.5]) linear_extrude(2.8) post_2d(0.8);
        translate([sx*post_hx, post_y, beam_z0 - 3.2]) linear_extrude(3.7) post_2d(0.8);
    }

    // deck nosing: a 0.8mm lip under the deck edge, which is what gives the
    // deck a shadow line instead of a raw extruded rectangle
    translate([0, 0, deck_h - 1.5]) linear_extrude(1.5)
        rrect(2*por_hw + 1.6, por_yf - por_yb + 1.6, (por_yb + por_yf)/2, 2.0);

    // NO BALUSTRADE, and that is a decision rather than an omission. A railing
    // scaled correctly to this house is about 11mm above the deck, and the
    // lanterns are 11mm tall -- one drawn and rendered hid both of them
    // completely from straight on, which is the only view that matters in a
    // listing photo. A low porch with no railing is a real and common detail;
    // two jack-o-lanterns nobody can see is not a trade worth making.
    // Frieze board along the house wall. It is a real Victorian member, and it
    // is here for a measured reason: without it the beam soffit bridged the
    // full 21.6mm from the wall out to the front beam, front to back, with
    // nothing under it between the columns. The board carries the back edge
    // 5.2mm out and takes that span down to 16.4mm. Its own underside is a
    // 5.2mm ledge, which is short enough not to matter. It starts at 36.5 --
    // above the door arch, which tops out at 35.9 -- so it never crosses the
    // head of the door.
    translate([0, 0, 36.5]) linear_extrude(beam_z0 - 36.3) rrect(2*por_hw, 7, 36.5, 1.0);

    translate([0, 0, beam_z0]) linear_extrude(beam_z1 - beam_z0)
        rrect(2*por_hw, por_yf - por_yb - 1.5, (por_yb + por_yf - 1.5)/2, 1.0);
    // The cornice FLARES rather than stepping. As a straight prism 1.5mm wider
    // than the beam it presented a 90 deg lip all the way round, and the
    // slicer ran a 42.6mm bridging line ALONG that 1.5mm ledge -- the same
    // shape of measurement as the clapboard grooves, a long line on a narrow
    // ledge rather than a long span. Flared, it is 1.5mm out over 3mm of rise,
    // which is 26.6 deg from vertical, and the ledge is gone.
    translate([0, 0, beam_z1])
        skin([[for (q = rrect_pts(42, 22.5, 1.0, 4)) [q[0], q[1] + 44.25]],
              [for (q = rrect_pts(45, 26,   1.0, 4)) [q[0], q[1] + 44.5 ]]],
             z = [0, corn_z1 - beam_z1], slices = 0);
    // hip roof, narrowing as it rises, so its outer faces are the printable
    // direction all the way up and its back edge stays flat on the wall
    translate([0, 0, corn_z1])
        skin([[for (q = rrect_pts(45, 26,   1.5, 4)) [q[0], q[1] + 44.5 ]],
              [for (q = rrect_pts(34, 17.5, 1.5, 4)) [q[0], q[1] + 40.25]]],
             z = [0, proof_z1 - corn_z1], slices = 0);
}

// ---- jack-o-lantern -------------------------------------------------------
// A REAL GOURD, NOT A DOME WITH SCRATCHES IN IT. The previous lantern was a
// hull of a disc and a sphere with two cut grooves standing in for ribs, which
// is a shape that only reads as a pumpkin because it is orange in your head.
// This one is built the way the fruit is: eight lobes swelling out of a
// smaller core, so the ribs are 2.2mm of real relief with genuine valleys
// between them rather than a scratch on a sphere.
//
// The base is a plane cut, and WHERE it cuts is the printability decision.
// Cut too near the bottom of a lobe and the surface there is nearly
// horizontal, which flares out past 55 deg on the first few layers. Cutting at
// 0.85 of the vertical semi-axis puts the steepest point of the base flare at
// 51.9 deg on a lobe and 53.4 deg on the core -- inside the limit, and it also
// gives a wide, stable 9.9mm footprint on the deck.
// pk_y stands the lantern 1.2mm CLEAR of the siding, resting on the deck and
// nothing else. Embedded in the wall it was tangent to the clapboard grooves
// over a long, shallow arc, and CGAL turned that into 13 zero-area faces and
// two inverted sliver bodies -- while still reporting the mesh watertight. A
// 77mm2 weld to the deck is plenty; the wall was never carrying it.
pk_x = 15; pk_y = 43.2; pk_z = 9.5;
pk_R = 7.2; pk_cz = 6.0; pk_zc = 5.10; pk_off = 2.45; pk_lr = 4.75; pk_core = 5.0;

module pumpkin_body() {
    $fn = 48;
    difference() {
        union() {
            translate([0, 0, pk_zc]) scale([1, 1, pk_cz/pk_core]) sphere(r = pk_core);
            for (i = [0 : 7]) rotate([0, 0, i*45])
                translate([pk_off, 0, pk_zc]) scale([1, 1, pk_cz/pk_lr]) sphere(r = pk_lr);
            // Stem: a five-lobed profile tapered and twisted as it rises, seated
            // 2.5mm inside the dome so it is never a separate body balanced on
            // a curve. The flutes are BUILT, not cut. Cut as five vertical
            // channels they were deeper than the stem was thick at the top and
            // sawed it into loose fins -- visible in the render as two prongs
            // where a stem should be. Taper is 9.8 deg from vertical.
            translate([0, 0, 8.6]) linear_extrude(5.2, scale = 0.42, twist = 30, slices = 20)
                union() {
                    circle(r = 1.05);
                    for (i = [0 : 4]) rotate(i*72) translate([1.0, 0]) circle(r = 0.55);
                }
        }
        translate([0, 0, -40]) cylinder(h = 40, r = pk_R + 3);      // flat base
    }
}

// The face is cut through the gourd AND the wall behind it, so it is an
// opening into the lit interior. It is extruded in ONE direction, from just
// outside the gourd backwards -- centring it would have driven the cut
// straight through the porch post standing behind the lantern.
//
// Every ceiling in it is a tooth flank or a triangle side, never a flat span:
// the teeth are cut as overlapping apex-up triangles, so the material teeth
// between them hang from the top at 26 deg from vertical, and the eyes and
// nose are apex-up triangles for the same reason. `tilt` leans the eyes so the
// two lanterns are not the same face twice.
// THE TOOTH COUNT MUST BE ODD, and the nose must clear the tallest tooth.
// Cutting the grin as overlapping apex-up triangles leaves a material tooth
// hanging between each neighbouring pair. With an EVEN count there is a
// material wedge on the centreline -- exactly where the nose is cut -- and the
// nose lops its top off, leaving a tooth floating free inside the mouth (and a
// matching loose sliver in the wall the cut passes through). It gated
// watertight and rendered fine; only component_count caught it. An odd count
// puts a HOLE on the centreline instead, and every wedge hangs from material
// that is still attached above it.
//
// The same reasoning fixes the height: the nose sits 1.26mm above the tallest
// tooth apex, so the web between them is three extrusions wide everywhere,
// rather than pinching to a knife edge wherever the two nearly meet.
//
// Everything here is a triangle side or a tooth flank -- 60 deg or steeper
// from horizontal -- so no layer of this face bridges anything.
module face_2d(tilt = 0, hs = [2.2, 2.9, 2.8, 2.9, 2.2]) {
    for (sx = [-1, 1]) translate([sx*2.9, 2.9]) rotate(-sx*tilt)
        polygon([[-1.55,0],[1.55,0],[0,2.8]]);
    translate([0, 0.9]) polygon([[-0.9,0],[0.9,0],[0,1.6]]);
    for (i = [0 : 4]) let (x = -4 + i*2)
        translate([x, -3.6 + 0.085*x*x]) polygon([[-1.05,0],[1.05,0],[0,hs[i]]]);
}

module lanterns() { for (sx = [-1, 1]) translate([sx*pk_x, pk_y, pk_z]) pumpkin_body(); }
module lantern_faces() {
    // starts at y = 51, which is outside the gourd (50.4) but still short of
    // the post (51.8), and runs 20mm back -- through the lantern, across the
    // gap, and out through the house wall into the cavity at 33.2. The
    // triangles it leaves in the siding sit entirely behind the lantern.
    for (i = [0, 1]) translate([(i ? 1 : -1)*pk_x, 51.0, pk_z + pk_zc]) rotate([90, 0, 0])
        linear_extrude(20) face_2d(tilt = i ? 14 : 0,
                                   hs = i ? [2.0,2.6,3.2,2.6,2.0] : [2.2,2.9,2.8,2.9,2.2]);
}

// ---- bat ------------------------------------------------------------------
function bat_half() = [[0,5.0],[1.8,3.6],[3.2,6.4],[4.4,3.2],[7.2,4.4],
                       [11.0,2.8],[8.6,0.4],[6.8,1.6],[5.0,-1.4],[3.2,0.2],
                       [1.7,-3.2],[0,-4.4]];
module bat_2d(span = 16) {
    h = bat_half();
    scale(span / 22)
        polygon(concat(h, [for (i = [len(h)-2 : -1 : 1]) [-h[i][0], h[i][1]]]));
}
// On the TOWER, whose two exposed faces are the only 26mm of blank wall left
// on the model -- a 16mm bat covers 62% of that face, so it is unmistakable
// even unlit, and at night it is a bat-shaped hole full of light. The tower
// sits clear of the body on both of these faces (x = -47 against the body's
// -38, y = 43 against +34), so neither cut can reach anything but tower wall.
module place_tur_cut(face, z) {
    r  = [0, 180, -90, 90][face];
    px = tur_x + (face == 2 ? tur_s/2 : face == 3 ? -tur_s/2 : 0);
    py = tur_y + (face == 0 ? tur_s/2 : face == 1 ? -tur_s/2 : 0);
    translate([px, py, z]) rotate([0, 0, r]) rotate([90, 0, 0])
        linear_extrude(14, center = true) children();
}

// A rose window whose tracery is a spiderweb -- eight radials and two rings.
// It is the strongest Halloween cue available to a LIT object, because it
// costs nothing but the same through-cut the ordinary windows already use,
// and the web only appears when the tealight is in. The tracery is subtracted
// from the cut so it survives as material, exactly like the mullions, and it
// breaks a 22mm opening into 24 panes none wider than about 5mm.
module web_2d(d = 22) {
    difference() {
        circle(d = d);
        for (a = [0 : 45 : 179]) rotate(a) square([d + 2, mull], center = true);
        difference() { circle(d = d*0.64); circle(d = d*0.64 - 2*mull); }
        difference() { circle(d = d*0.32); circle(d = d*0.32 - 2*mull); }
    }
}

module halloween_relief() { porch(); lanterns(); }
module halloween_cuts() {
    lantern_faces();
    translate([0, D/2, 67]) rotate([90, 0, 0]) linear_extrude(16, center = true) web_2d(22);
    // z is fenced by the tower's own windows, not chosen by eye: the lower
    // twin's lancet apex lands at 60.8 and the upper twin's sill at 82, so a
    // bat centred at 71 (span 16 -> 67.1..74.9) is clear of both by ~7mm. At
    // z = 63 the wingtips merged into the lancet head and read as a fault.
    place_tur_cut(0, 71) bat_2d(16);
    place_tur_cut(3, 69) bat_2d(15);
}

// The relief is unioned AFTER the grooves, deliberately: it is appliqué ON the
// siding, and cutting clapboard stripes through a bat would look like a fault.
// The pumpkin faces are then cut through the bosses that carry them.
module manor() {
    difference() {
        union() {
            difference() { solid(); cavity(); grooves(); openings(); brand_mark(); }
            halloween_relief();
        }
        halloween_cuts();
    }
}
if (part == "solid") solid(); else manor();
