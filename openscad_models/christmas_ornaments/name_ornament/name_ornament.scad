// Personalised name ornament (2026-10-21). Scott picked the domed half-bauble
// (1E) from five: a smooth dome, flat behind, with the buyer's name and the
// year inlaid flush into its face in a second colour, the same way the OBC
// mark is inlaid under the village. A star above the name; the maker's mark
// inlaid in the back in the same second colour, so it costs no extra change.
//
// Printed flat, back on the plate, dome up: every face is a top surface or a
// vertical edge, so nothing overhangs.
//
//   NAME, YEAR     the personalisation; NAME up to about 11 letters
//   part = body | inlay | union | all
include <../../brand/obc_mark.scad>

NAME = "Olivia";
YEAR = "2026";
part = "all";

$fn = 160;
RD   = 40;          // the ornament's radius: 80 mm across
RIM  = 3.0;         // the vertical band round its edge
HD   = 10;          // the dome's rise above the band
RS   = (RD * RD + HD * HD) / (2 * HD);   // the sphere the dome is cut from
DEEP = 0.6;         // the inlay's depth: three layers

NAME_FONT = "Dancing Script:style=Bold";
YEAR_FONT = "Montserrat:style=ExtraBold";
// the name's size: as big as fits 60 mm across, at most 13 (Dancing Script
// Bold runs about 0.55 of its size per letter)
NAME_SIZE = min(13, 60 / (0.55 * len(NAME)));

module dome() {
    cylinder(r = RD, h = RIM);
    intersection() {
        translate([0, 0, RIM + HD - RS]) sphere(r = RS, $fn = 240);
        cylinder(r = RD, h = RIM + HD + 1);
    }
}
// the dome's skin DEEP thick, measured straight down: what the inlay may fill
module skin() difference() { dome(); translate([0, 0, -DEEP]) dome(); }

// cleaned as a nozzle draws (as the OBC mark): gaps under 0.85 closed,
// strokes under a bead opened
module clean() offset(r = 0.21, $fn = 12) offset(delta = -0.21) offset(r = -0.425, $fn = 12) offset(delta = 0.425) children();

module star2d(r) polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, rr = i % 2 ? r * 0.45 : r) [rr * cos(a), rr * sin(a)]]);
module face2d() clean() {
    translate([0, 1.5]) text(NAME, size = NAME_SIZE, font = NAME_FONT, halign = "center", valign = "center");
    translate([0, -15]) text(YEAR, size = 5.5, font = YEAR_FONT, halign = "center", valign = "center", spacing = 1.15);
    translate([0, 19]) star2d(4.2);
}

// the loop at the top: a 4.4 mm hole for a hook or ribbon
LOOP_RO = 4.8; LOOP_RI = 2.2;
module loop() translate([0, RD + LOOP_RO - 1.6, 0]) difference() {
    cylinder(r = LOOP_RO, h = RIM, $fn = 48);
    translate([0, 0, -1]) cylinder(r = LOOP_RI, h = RIM + 2, $fn = 48);
}

MARK_H = 5.0;       // the maker's mark's cap height, in the middle of the back
module inlay() {
    intersection() { skin(); linear_extrude(RIM + HD + 2) face2d(); }
    obc_inlay(MARK_H);
}
module body() difference() { union() { dome(); loop(); } inlay(); obc_cut(MARK_H); }

if (part == "body") body();
if (part == "inlay") inlay();
if (part == "union") union() { body(); inlay(); }
if (part == "all") { color("#C62F3A") body(); color("#F4F1EA") inlay(); }
