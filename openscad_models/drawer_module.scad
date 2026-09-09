include <BOSL2/std.scad>

// ============================================================
// Stacking drawer module -- shell + drawer, two objects on one plate.
//
// WHY TWO OBJECTS AND NOT PRINT-IN-PLACE. The pitch was a print-in-place
// drawer. Measuring it killed that: a drawer's floor sits above the
// shell's floor across a LARGE HORIZONTAL gap, and at the 0.2mm that
// works everywhere else that is a ~5600 mm2 light weld -- not the tiny
// contact a ball joint gets away with (Technique 42/44). Every escape is
// worse: a bigger gap makes the drawer floor start in mid-air, and
// hanging it on rails so the floor bridges puts a 55mm bridge over the
// one surface that must stay flat. Meanwhile the standing rule already
// says things that separate in use ship as separate objects on one plate,
// and a drawer separates in use. So: two objects, each printing in its
// own ideal orientation, zero fusing risk.
//
// PRINT ORIENTATION IS THE WHOLE DESIGN HERE.
//   shell  -- on its BACK, opening UP. Every wall vertical, the cavity is
//             a blind hole opening upward, and both slide features run
//             along the build axis, so they are constant-section. Nothing
//             structural overhangs and nothing bridges; the only faces the
//             gate flags are the four end caps of the stacking rails
//             (17 mm2) and the engraved mark's own ceiling (27 mm2), both
//             sub-millimetre and the same benign class as the sauce tray's.
//   drawer -- as it sits in use, open side up. Flat on the bed.
// Both parts are exported already in these poses (see the part= branch);
// the default view is the assembled pose, which is the only pose the fit
// can be reasoned about in.
//
// use frame: X = width, Y = depth (0 = front face, D = back), Z = height.
// ============================================================

part = "all";   // "all" | "shell" | "drawer"

// Sized DOWN from a first pass at 96 x 78 x 48 / 2.4mm wall, which sliced
// at 10h15 and 123g for one module -- past the point a print pays for its
// own machine time. At these numbers it is 7h16 / 85g, in the same range
// as the snap box (6h30), which is a shipping product. The drawer still
// holds ~136 cm3. Wall is 4 extrusions exactly at 0.42, so the slicer
// lays whole perimeters with no gap fill.
W = 88;         // 88 : 71 : 44 -- D:H = 1.614, essentially golden; W:D = 1.24
D = 71;
H = 44;
wall  = 1.68;
out_r = 6;      // outer corner radius, r/H = 0.136

// Technique 43's universal constant, measured on three unrelated
// mechanisms. Lateral gets a little more: a slide binds on width, and
// nothing about this design needs a tight side fit.
clear     = 0.20;
clear_lat = 0.30;

cav_w = W - 2 * wall;      // 91.2
cav_h = H - 2 * wall;      // 43.2
cav_d = D - wall;          // 75.6 -- open at y = 0, back wall behind it
cav_z0 = wall;             // cavity floor
cav_r  = out_r - wall;     // 3.6, and constant wall BY CONSTRUCTION

// A squircle outer (Technique 30's G2 corners) was tried first and
// measured out: at every squareness its corners pull in far enough that a
// near-full-size cavity breaches the wall -- best case 0.73mm of material
// left, worst case negative. offset(r=-wall) on a plain rounded rect is
// the only shape here whose wall cannot silently go thin, so the design
// carries its character in the flutes and the drawer front instead.
module outer_2d() { offset(r = out_r) square([W - 2*out_r, H - 2*out_r], center = true); }
module cav_2d()   { offset(r = -wall) outer_2d(); }
module drw_2d()   { offset(r = -clear_lat) cav_2d(); }

// Extrude a profile (authored centred in its own XY) along world Y.
module along_depth(y0, y1) {
    translate([0, y1, H/2]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
}

// ---- slide ----------------------------------------------------------
// The drawer's floor plate is wider than its body and rides in a channel:
// it sits on two runners, and a rib above catches it so the drawer cannot
// tip out when pulled. Both are ribs running front-to-back -- i.e. along
// the shell's build axis -- so both are constant-section and print with
// no overhang at all. That is the reason for this orientation.
run_h  = 1.0;      // runner height, also the front lip the drawer face sits on
run_w  = 5;
run_x  = 28;
run_y0 = 0;        // runners reach the front face: the drawer's face plate
                   // rests on their front ends, at the same height the flange
                   // rides them, so the drawer sits on one plane. An earlier
                   // full-width front lip did the same job and cost an 81mm2
                   // downward step where it ended -- the only non-benign
                   // overhang in the part. Two runners carry the face fine.
cap_y0 = 8;        // capture ribs start behind the face, so its full-width
                   // wings never reach them

fl_z0 = cav_z0 + run_h;   // 3.4  flange underside, riding the runners
fl_t  = 3.0;
fl_z1 = fl_z0 + fl_t;     // 6.4  flange top -- the guiding surface

cap_proud = 3.0;                  // capture rib reach over the flange
cap_z0 = fl_z1 + clear;           // 6.6
cap_z1 = cap_z0 + 4.0;

// ---- flutes ---------------------------------------------------------
// Raised OUTWARD, never cut in (Technique 52: our shells are wall-limited,
// and a ridge standing proud costs nothing structurally). Sloping face is
// atan(proud/half-width) = 34.1 deg from the build axis -- inside the
// 40 deg a buyer-visible surface should stay under (Technique 35).
// A first pass used a sharp triangular tooth at 2.2mm proud on a 9.5mm
// pitch -- depth/pitch 0.23 against the reference corpus's 0.14 -- and it
// rendered as gear teeth, not fluting. A circular bulge at 1.5mm on a
// 10.5mm pitch matches the corpus and reads as a real flute. The arc is
// steepest where it meets the wall: atan(chord_half/centre_depth) =
// 36.9 deg from the build axis, inside the 40 deg a seen surface wants.
rib_n     = 6;
rib_proud = 1.5;
rib_R     = 7.5;    // chord half-width 4.5 -> 9.0mm wide flute
rib_bury  = 1.2;    // < wall, so the cutter never reaches the cavity
rib_pitch = 10.5;
rib_y0    = 10;
// The flank is dead flat between out_r and H-out_r, so deriving the band
// from out_r means the flutes always sit on real flat wall -- a hardcoded
// pair here would silently ride up onto the corner if H ever changed.
rib_z0    = out_r + 2;
rib_z1    = H - out_r - 2;

module rib_2d(yc, proud) {
    // The full circle would reach far past the wall and fill the cavity,
    // so it is clipped to a shallow buried band -- rib_bury must stay
    // under `wall` or this cutter eats the drawer's own space.
    intersection() {
        translate([W/2 - (rib_R - proud), yc]) circle(r = rib_R, $fn = 72);
        translate([W/2 - rib_bury + 10, yc]) square([20, 2*rib_R + 2], center = true);
    }
}
module rib(yc) {
    hull() {
        translate([0, 0, rib_z0 + 2]) linear_extrude(rib_z1 - rib_z0 - 4) rib_2d(yc, rib_proud);
        translate([0, 0, rib_z0])        linear_extrude(0.01) rib_2d(yc, 0.01);
        translate([0, 0, rib_z1 - 0.01]) linear_extrude(0.01) rib_2d(yc, 0.01);
    }
}
module flutes() {
    for (i = [0 : rib_n - 1]) {
        yc = rib_y0 + i * rib_pitch;
        rib(yc);
        mirror([1, 0, 0]) rib(yc);
    }
}

// ---- stacking -------------------------------------------------------
// Two rails front-to-back rather than a ring: a ring's end segments would
// be the only overhangs in the whole part, and two rails locate a stack
// just as well. Tongue is 0.2 SHORTER than the groove is deep so modules
// seat on the flat faces, never on the tongue (Technique 43: separate the
// locating feature from the seating datum).
stk_x  = 34;
grv_w  = 2.4;  grv_d = 2.0;  grv_y0 = 5;   grv_y1 = D - 5;
tng_w  = 2.0;  tng_h = 1.8;  tng_y0 = 6;   tng_y1 = D - 6;

module stack_grooves() {
    for (sx = [-1, 1]) translate([sx * stk_x, (grv_y0 + grv_y1)/2, H - grv_d/2 + 0.01])
        cube([grv_w, grv_y1 - grv_y0, grv_d + 0.02], center = true);
}
module stack_tongues() {
    for (sx = [-1, 1]) translate([sx * stk_x, (tng_y0 + tng_y1)/2, -tng_h/2])
        cube([tng_w, tng_y1 - tng_y0, tng_h], center = true);
}

// ---- maker's mark ---------------------------------------------------
// Bottom face, engraved, reusing Technique 4's confirmed pattern verbatim
// -- same translate+extrude+mirror([0,1,0]) shape Scott has physically
// confirmed reads correctly on a real print. Not re-derived for a new
// face, because chirality cannot be checked in-script.
// "OBC", not the wordmark: "OnBrandCraftz" measures 0.0mm of stroke at any
// size that fits a part like this. Sized to ~36% of the 96mm flat run.
mark_size  = 10.0;   // 31.7mm = 36% of the 88mm flat run it sits on
mark_depth = 0.7;
module brand_mark() {
    translate([0, D/2, -0.5])
        linear_extrude(mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OBC", size = mark_size, font = "Montserrat:style=Black",
                     halign = "center", valign = "center");
}

// ---- shell ----------------------------------------------------------
// Anything that lives INSIDE the cavity has to be unioned on AFTER the
// cavity is cut, never before -- putting the runners and capture ribs in
// the same union() as the body means the cavity subtraction deletes them,
// and it deletes them silently: the part stays watertight, one body, and
// passes every gate. It also makes the interference check against the
// drawer come back EMPTY for the wrong reason -- nothing there to
// interfere with (Technique 37). Measured, not assumed: with the features
// missing the shell's material at the capture height began at x=45.62,
// the bare cavity wall.
// Each one is sunk ~0.9mm into the surface it grows from rather than left
// coplanar, so the weld is unambiguous.
module slide_features() {
    for (sx = [-1, 1]) {
        translate([sx * run_x, (run_y0 + cav_d)/2, cav_z0 + run_h/2 - 0.45])
            cube([run_w, cav_d - run_y0, run_h + 0.9], center = true);
        translate([sx * (cav_w/2 - cap_proud/2 + 0.45), (cap_y0 + cav_d)/2, (cap_z0 + cap_z1)/2])
            cube([cap_proud + 0.9, cav_d - cap_y0, cap_z1 - cap_z0], center = true);
    }
}

module shell() {
    union() {
        difference() {
            union() {
                along_depth(0, D) outer_2d();
                flutes();
                stack_tongues();
            }
            along_depth(-1, cav_d) cav_2d();
            stack_grooves();
            brand_mark();
        }
        slide_features();
    }
}

// ---- drawer ---------------------------------------------------------
plate_t = 6.5;                                  // deep enough for the shelf pull
                                                // to have real material behind it
body_w  = cav_w - 2*cap_proud - 2*clear_lat;    // clears the capture ribs
body_wall = 1.68;
body_z1 = H - wall - 4.5;                       // headroom under the cavity roof
drw_y0  = plate_t;
drw_y1  = cav_d - clear;

// ---- finger pull: four interchangeable options ----------------------
// Every one of these has to work from the FRONT FACE ALONE. Modules stack,
// so a pull you reach over the top edge for -- the obvious handle-less
// answer, and a good one on a single unit -- is unreachable the moment
// anything sits on top of it. That constraint is what rules the field.
//
//   band   flush, nothing protrudes, but only 3mm of fingertip purchase.
//          The weakest grip of the four; it is the quietest to look at.
//   ledge  a proud shelf with a 45 deg underside, so it is self-supporting
//          along its whole length with no stems. Best grip by a distance.
//          Costs 10mm of depth, so the module footprint goes 71 -> 81mm.
//   slot   cut clean through: a whole fingertip goes in, nothing protrudes.
//          You can see into the drawer, which reads as either architectural
//          or as clutter depending on what is in it. Its top edge is a
//          56mm bridge over a 5mm wall -- routine, but it IS a bridge, the
//          only one anywhere in this design.
//   lip    a blind pocket with a flat, undercut roof, so there is a real
//          hook to pull on without protruding and without seeing in. Its
//          roof is a 4mm cantilever -- a small overhang, buried inside the
//          pocket where nobody looks.
//   shelf  lip, cut deeper and given a real floor -- entirely inside the
//          face, nothing protruding. The pocket goes from 3mm to 5mm deep
//          and its floor goes flat, so that floor IS the shelf a fingertip
//          sits on, with 5mm of lip above it to pull against. The two
//          things that made the shallow version feel bad were both the
//          floor: it was a 45 deg ramp, so the finger slid down and out,
//          and at 3mm there was barely anything to slide into.
//          Depth is limited by what is behind it, and there is more there
//          than the plate alone -- the drawer body's own front wall backs
//          the whole pull, so a 6.5mm plate gives 8.18mm of material and a
//          5mm pocket still leaves 3.18mm. The cost is the roof: it is a
//          flat 5mm cantilever, and it has to be, because an undercut IS
//          an overhang -- ramp it to make it self-supporting and the hook
//          is gone. It is 56mm of ledge facing down inside a pocket.
//   rail   Scott's pick: a second, deeper slot ABOVE the pocket. What
//          that really creates is the bar of material between the two --
//          and a bar is the strongest grip available on a flush face,
//          because fingers curl into the upper slot and pull the rail
//          rather than pressing on a back wall and hoping for friction.
//          Zone 3 on its own is only 7mm tall, nowhere near enough for a
//          usable slot plus a solid top margin, so the whole face is
//          rebalanced around the pair. The pull now occupies 26 of the
//          39mm face, which is a lot -- that is what two recesses on a
//          small face costs.
// Back to "shelf" 2026-09-09: Scott rejected the rail outright ("it's
// wrong"). The rail stays available as an option, but the single deep
// pocket is the live design again until he says otherwise.
pull = "shelf";  // "band" | "ledge" | "slot" | "lip" | "shelf" | "rail"

plate_top = H - wall - clear_lat;
pull_w = 56;
band_d = 3.0;
band_h = 9;      // 9 of the face's 39mm; at 12 it swallowed the top
                 // third of the front and read as a lid, not a pull.

module face_prism(pts, w) {
    rotate([90, 0, 90]) linear_extrude(w, center = true) polygon(pts);
}

module pull_cut() {
    if (pull == "band") {
        z1 = plate_top;  z0 = z1 - band_h;
        face_prism([[-1, z0 - band_d], [band_d, z0], [band_d, z1 + 2], [-1, z1 + 2]], W + 10);
    } else if (pull == "slot") {
        z1 = plate_top - 5;  z0 = z1 - 14;
        // Chamfered mouth funnelling into a straight through-cut. Both
        // halves are real 4-point rectangles: a 2-point polygon renders as
        // a non-manifold solid, and OpenSCAD only warns about it.
        hull() {
            face_prism([[-1, z0 - 2], [0.01, z0 - 2], [0.01, z1 + 2], [-1, z1 + 2]], pull_w + 4);
            face_prism([[2.0, z0], [2.2, z0], [2.2, z1], [2.0, z1]], pull_w);
        }
        face_prism([[2.0, z0], [plate_t + 1, z0], [plate_t + 1, z1], [2.0, z1]], pull_w);
    } else if (pull == "shelf") {
        // 1mm lead-in on the bottom edge so a fingertip is not dragged
        // across a sharp corner on its way in; the rest of the floor is
        // dead flat, which is the whole point of it.
        face_prism([[-1, shelf_z0 - 1], [1.0, shelf_z0], [shelf_d, shelf_z0],
                    [shelf_d, shelf_z1], [-1, shelf_z1]], pull_w);
    } else if (pull == "rail") {
        rail_slot(rail_up_z0, rail_up_z1, rail_up_d);
        rail_slot(rail_lo_z0, rail_lo_z1, rail_lo_d);
    } else if (pull == "lip") {
        // 3.0 deep, not 4.0: at 4 the pocket left only 1mm of plate behind
        // it, and that 1mm is what the undercut roof cantilevers off.
        z1 = plate_top - 4;  z0 = z1 - 16;
        face_prism([[-1, z0 - 4], [3.0, z0], [3.0, z1], [-1, z1]], pull_w);
    }
}

// ---- rail: upper slot + grip bar + lower pocket ----------------------
// Every z is derived down the stack from the plate's own top, so the whole
// arrangement stays put if the module is ever resized. Depths are limited
// by what is behind: plate 6.5 + the drawer body's own front wall 1.68 =
// 8.18mm, and the upper slot's top is held at 37.52 so it stays inside the
// band that wall actually covers (5.68..37.82) rather than running off the
// end of it into bare plate.
rail_top_solid = 4.5;
rail_up_h = 10;   rail_up_d = 5.5;   // the slot fingers go into
rail_bar_h = 5;                      // the bar they pull on
rail_lo_h = 11;   rail_lo_d = 5.0;
rail_up_z1 = plate_top - rail_top_solid;
rail_up_z0 = rail_up_z1 - rail_up_h;
rail_lo_z1 = rail_up_z0 - rail_bar_h;
rail_lo_z0 = rail_lo_z1 - rail_lo_h;

// 1mm lead-in on each slot's bottom edge so a fingertip is not dragged
// over a sharp corner; the rest of each floor stays dead flat.
module rail_slot(z0, z1, dep) {
    face_prism([[-1, z0 - 1], [1.0, z0], [dep, z0], [dep, z1], [-1, z1]], pull_w);
}

shelf_d  = 5.0;                  // pocket depth; 3.18mm of plate left behind
shelf_z1 = plate_top - 7;        // the lip you pull on
shelf_z0 = shelf_z1 - 13;        // the shelf your fingertip sits on

module pull_add() {
    if (pull == "ledge") {
        z1 = plate_top - 3;
        // embedded 1.5mm, PAST the 1.0mm face flutes -- at 0.5 the ledge
        // only met the lands between grooves and bridged the grooves with
        // gaps behind it
        face_prism([[1.5, z1], [-10, z1], [-10, z1 - 5], [1.5, z1 - 15]], pull_w);
    }
}

// Flutes on the face are CUT IN, not raised, so the drawer front stays
// flush in its opening -- the 5mm plate has the depth to spare, where the
// shell's 1.68mm wall does not (hence raised flutes there). Same pitch on
// both, so the two read as one system.
// With the rail pull, the two bands cut the face flutes into short stubs
// and the face reads busy -- set this false to let the pull be the design
// and leave the fluting to the shell's sides.
face_fluted = true;
fl_n = 8;  fl_depth = 1.0;  fl_R = 10.625;   // 9.0mm chord at 1.0mm deep
module face_flutes() {
    if (face_fluted) for (i = [0 : fl_n - 1]) {
        xc = (i - (fl_n - 1)/2) * rib_pitch;
        translate([xc, -(fl_R - fl_depth), 0]) cylinder(r = fl_R, h = H + 10, $fn = 96);
    }
}

module drawer() {
    difference() {
        union() {
            // face plate and flange are BOTH cut from the same clearance
            // envelope, so their corners follow the cavity's own fillet and
            // cannot foul it -- derived, not two numbers that have to agree
            intersection() {
                along_depth(0, plate_t) drw_2d();
                translate([0, D/2, (fl_z0 + H + 10)/2]) cube([W, D + 2, H + 10 - fl_z0], center = true);
            }
            intersection() {
                along_depth(drw_y0, drw_y1) drw_2d();
                translate([0, D/2, (fl_z0 + fl_z1)/2]) cube([W, D + 2, fl_t], center = true);
            }
            translate([0, (drw_y0 + drw_y1)/2, (fl_z1 + body_z1)/2])
                cube([body_w, drw_y1 - drw_y0, body_z1 - fl_z1], center = true);
        }
        // interior
        translate([0, (drw_y0 + body_wall + drw_y1 - body_wall)/2, (fl_z1 + body_z1 + 1)/2])
            cube([body_w - 2*body_wall, (drw_y1 - drw_y0) - 2*body_wall, body_z1 - fl_z1 + 1], center = true);
        face_flutes();
        pull_cut();
    }
}

module drawer_with_pull() { union() { drawer(); pull_add(); } }

// ---- output ---------------------------------------------------------
// Each part is exported in the pose it PRINTS in, not the pose it is
// modelled in. The shell rotates onto its back; the drawer only drops to
// the plate. Rotations, never a mirrored -z, which would flip every normal.
module shell_printed()  { translate([0, 0, D]) rotate([-90, 0, 0]) shell(); }
module drawer_printed() { translate([0, 0, -fl_z0]) drawer_with_pull(); }

// Explicit branches, no catch-all else: part="none" emits nothing, which
// is what lets another file include<> this one (the only way to override
// `pull`, since use<> imports modules but not variable overrides) without
// the assembled model landing in the output alongside whatever that file
// is actually trying to measure.
if (part == "shell")       shell_printed();
else if (part == "drawer") drawer_printed();
else if (part == "all")  { shell(); drawer_with_pull(); }
