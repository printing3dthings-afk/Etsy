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
plate_t = 5.0;                                  // was 6.5 -- the face plate was
                                                // 42% of the drawer's volume
body_w  = cav_w - 2*cap_proud - 2*clear_lat;    // clears the capture ribs
body_wall = 1.68;
body_z1 = H - wall - 4.5;                       // headroom under the cavity roof
drw_y0  = plate_t;
drw_y1  = cav_d - clear;

// Finger pull: the face's top band is recessed full width, rather than a
// pocket floating in the middle of a plain slab -- which is what the first
// version was, and it read as a mail slot. Open at the top, so there is no
// roof to bridge and no overhang at all; the 45 deg step at its bottom is
// the surface a fingertip actually pulls against.
plate_top = H - wall - clear_lat;
pull_d = 3.0;
pull_h = 9;      // 9 of the face's 39mm; at 12 it swallowed the top
                 // third of the front and read as a lid, not a pull.

module pull_recess() {
    z1 = plate_top;  z0 = z1 - pull_h;
    rotate([90, 0, 90]) linear_extrude(W + 10, center = true)
        polygon([[-1, z0 - pull_d], [pull_d, z0], [pull_d, z1 + 2], [-1, z1 + 2]]);
}

// Flutes on the face are CUT IN, not raised, so the drawer front stays
// flush in its opening -- the 5mm plate has the depth to spare, where the
// shell's 1.68mm wall does not (hence raised flutes there). Same pitch on
// both, so the two read as one system.
fl_n = 8;  fl_depth = 1.0;  fl_R = 10.625;   // 9.0mm chord at 1.0mm deep
module face_flutes() {
    for (i = [0 : fl_n - 1]) {
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
        pull_recess();
    }
}

// ---- output ---------------------------------------------------------
// Each part is exported in the pose it PRINTS in, not the pose it is
// modelled in. The shell rotates onto its back; the drawer only drops to
// the plate. Rotations, never a mirrored -z, which would flip every normal.
module shell_printed()  { translate([0, 0, D]) rotate([-90, 0, 0]) shell(); }
module drawer_printed() { translate([0, 0, -fl_z0]) drawer(); }

if (part == "shell")       shell_printed();
else if (part == "drawer") drawer_printed();
else { shell(); drawer(); }
