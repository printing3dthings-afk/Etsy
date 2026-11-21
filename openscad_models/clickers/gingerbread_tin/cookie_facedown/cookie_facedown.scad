// Gingerbread Tin Clicker cookie, FACE DOWN (test piece, 2026-11-21).
//
// Scott: "We also need to start designing prints that are printed facedown so the image is
// flat and looks great. Can you make just the gingerbread man part of the tin clicker face
// down. I want it as a test piece."
//
// The same cookie as the clicker's (outline, size, switch socket, so it still drops into the
// lid's nest), turned over so its face is the first layer on the plate:
//   - the face is dead flat and takes the plate's finish (textured PEI: an even matte grain;
//     smooth PEI: gloss);
//   - the icing, cheeks, bow and gumdrops are no longer piped up from the top. They are set
//     flush into the face, INLAY deep, so every colour change happens in the first four
//     layers and the rest of the cookie prints in brown alone (far less purge than the
//     face-up cookie, whose colours run up its top);
//   - the face's edge is a small chamfer (0.4 in over 0.6 up), not the face-up cookie's rolled
//     edge: a rolled edge on the plate would start as a hanging lip. The chamfer prints clean and
//     hides elephant's foot;
//   - the switch socket, underneath on the face-up cookie, now opens upward: nothing hangs.
//
// It's built face up, the way the eye reads it, then turned over with a rotation, never a
// mirror, so the face reads the right way round when it's picked up off the plate.
//
//   part = body | icing | red | green | print (all four, merged, face down, for the gate)
//          all (preview, face up)

use <../gingerbread_tin_clicker.scad>
include <../../clicker_lib.scad>

part = "all";

CT     = cav_h + cap_floor;   // 6.2, the clicker's cookie thickness (same formula, same lib)
INLAY  = 0.8;                 // colour depth: four 0.2 layers, enough that brown can't show through white
CHAMF  = 0.6;                 // the face's edge: three layers tall ...
CH_IN  = 0.4;                 // ... and 0.4 in, 34 deg from upright. At exactly 45 deg (0.6 in) the gate's
                              // slicer hung support round the whole edge (725 moves, 2026-11-21)
BTN_Y  = [1.0, -2.5, -6.0];   // the clicker's gumdrop rows (btn_y there; `use` doesn't carry variables)
GUM_R  = 1.55;                // a gumdrop's foot, now its whole face
EYE_C  = [3.4, 15.0];         // the clicker's eyes2d()
EYE_R  = 1.6;
// Pupils: the face-up cookie stood them on top of the white, so the white under them could be
// any width. Inlaid, the white round a pupil is a printed ring and must stay a bead or more,
// so the pupil is smaller and nearer the eye's centre (still down and inward, at the smile).
PUP_R  = 0.75;
PUP_D  = [0.25, 0.3];

// the face-up colour regions, 2D
module white2d() difference() {
    icing2d();
    for (s = [-1, 1]) translate([s * (EYE_C.x - PUP_D.x), EYE_C.y - PUP_D.y]) circle(PUP_R, $fn = 32);
}
module red2d()   union() { cheeks2d(); bow2d(); translate([0, BTN_Y[1]]) circle(GUM_R, $fn = 40); }
module green2d() for (y = [BTN_Y[0], BTN_Y[2]]) translate([0, y]) circle(GUM_R, $fn = 40);
module colours2d() union() { white2d(); red2d(); green2d(); }

// face up: the face at z = CT, its edge chamfered in 0.2 steps
module blank() difference() {
    union() {
        linear_extrude(CT - CHAMF) gb_outline();
        for (k = [0 : round(CHAMF / 0.2) - 1])
            translate([0, 0, CT - CHAMF + k * 0.2 - 0.01]) linear_extrude(0.21) offset(delta = -(k + 1) * CH_IN / round(CHAMF / 0.2)) gb_outline();
    }
    mx_cap_cut();
}
module inlay(h = INLAY) translate([0, 0, CT - h]) linear_extrude(h + 0.01) children();

module body_up()  difference() { blank(); inlay(INLAY + 0.01) colours2d(); }
// each colour is trimmed to the blank, so a region that reaches the chamfer follows it in
module piece_up() intersection() { blank(); inlay() children(); }

// turned over: the face on the plate at z = 0
module face_down() translate([0, 0, CT]) rotate([180, 0, 0]) children();

if      (part == "body")  face_down() body_up();
else if (part == "icing") face_down() piece_up() white2d();
else if (part == "red")   face_down() piece_up() red2d();
else if (part == "green") face_down() piece_up() green2d();
else if (part == "print") face_down() blank();
else {
    color("#9A5B2E") body_up();
    color("white")   piece_up() white2d();
    color("#B3262E") piece_up() red2d();
    color("#3E8E4A") piece_up() green2d();
}
