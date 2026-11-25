// Camera sign (2026-11-18): a sign stuck on the back wall inside Scott's P1S, so the
// chamber camera, his timelapses and anyone watching see where to find him. Scott:
// "something that sends people to my instagram ... that I can hang in the circle
// area". He picked forms 1 and 5 of five:
//   style = "neon"    the handle in a bold script on its own raised outline, FOLLOW
//                      small above: the shape is the letters, nothing else
//   style = "plaque"  a rounded plate with a raised border and bold handle text
//
// The back wall is inside the printer's moving space: the bed rises to just under the
// nozzle close to the wall, and the toolhead comes back to it. So THICK is set from
// Scott's two measured gaps (behind the toolhead at the back, behind the bed at the
// top), less a margin, and the sign keeps clear of the back lead screw's slot in the
// middle of the wall. Until he measures, THICK is a placeholder.
//
// Printed flat, face up, back on the plate: the back is flat for double-sided tape.
// Two colours, by height: the base to THICK - RAISE, the letters (and the plaque's
// border) the last RAISE. The AMS changes colour only on those top layers.
//
// No Instagram logo: it's their trademark. "FOLLOW" says what the handle is for.
//
//   part = base | letters | union | all
include <../brand/obc_mark.scad>

HANDLE = "@onbrandcraftz2026";
CALL   = "FOLLOW";
style  = "neon";
part   = "all";

THICK  = 2.4;          // PLACEHOLDER until Scott's gaps: total thickness off the wall
RAISE  = 0.8;          // the letters stand this far above the base: four layers
WIDE   = 130;          // the handle's width; the sign is about this plus its margin

// The neon's handle face. Scott printed Lobster (2026-11-25): "Hard to read. Try 3 different
// fonts in the style not the plaque". Its joined letters run together at 8 mm. The three
// alternatives keep the neon outline and change only the handle's face:
//   lobster    the original, joined script
//   nunito     rounded heavy sans: open counters, the most legible
//   righteous  retro display, the look of a neon sign, letters stand apart
//   courgette  a script whose letters stay separate, thickened a little to print
// Each row: name, font, the handle's width at size 10 (measured by exporting it, 2026-11-25),
// an outward offset that thickens thin strokes to a printable relief, and a face for the "@"
// alone ("" for the row's own). Righteous's own "@" has counters too narrow for a nozzle:
// clean() closed them and it printed as a solid blob, so it borrows Nunito's. At size 10 that
// "@" is 11.98 wide, then a 0.8 gap, then Righteous's "onbrandcraftz2026", 123.72 wide.
AT_W = 1.198; AT_GAP = 0.08; REST_W = 12.372;   // per unit of size
FONTS = [
    ["lobster",   "Lobster:style=Regular",   11.32, 0,    ""],
    ["nunito",    "Nunito:style=Black",      13.72, 0,    ""],
    ["righteous", "Righteous:style=Regular", AT_W + AT_GAP + REST_W, 0, "Nunito:style=Black"],
    ["courgette", "Courgette:style=Regular", 12.72, 0.25, ""],
];
hfont = "lobster";
FROW = FONTS[search([hfont], FONTS)[0]];
SCRIPT = FROW[1];
BOLD   = "Montserrat:style=ExtraBold";
// The handle's width per unit of text size, measured by exporting it at size 10
// (2026-11-18: Lobster 113.2 mm, Montserrat ExtraBold 150.1 mm). Re-measure if the
// handle changes: a width table guessed for the bold face ran it off the plaque.
W_SCRIPT = FROW[2];
W_BOLD   = 15.01;
THICKEN  = FROW[3];
AT_FONT  = FROW[4];
H_SIZE = WIDE / W_SCRIPT;                                   // the neon's handle size
C_SIZE = 0.42 * WIDE / 11.32;   // FOLLOW, the size it printed at (it read well), whatever the handle's face

// cleaned as a nozzle draws: gaps under 0.85 closed, strokes under a bead opened
module clean() offset(r = 0.21, $fn = 12) offset(delta = -0.21) offset(r = -0.425, $fn = 12) offset(delta = 0.425) children();

module handle2d(font, w = WIDE) clean() offset(delta = font == BOLD ? 0 : THICKEN)
    if (font != BOLD && AT_FONT != "") {
        sz = w / W_SCRIPT;
        // the "@" and the rest, side by side, centred together. valign = "baseline" on both, then
        // lifted by half the rest's x-height-ish centre, so the two faces share one baseline
        translate([-w / 2, 0]) {
            translate([-0.064 * sz, -0.33 * sz]) text("@", size = sz, font = AT_FONT, valign = "baseline");
            translate([(AT_W + AT_GAP - 0.031) * sz, -0.33 * sz]) text(substr1(HANDLE), size = sz, font = font, valign = "baseline");
        }
    } else text(HANDLE, size = w / (font == BOLD ? W_BOLD : W_SCRIPT), font = font, halign = "center", valign = "center");
// the handle without its first character
function substr1(t) = chr([for (i = [1 : len(t) - 1]) ord(t[i])]);
module call2d(y) clean() translate([0, y]) text(CALL, size = C_SIZE, font = BOLD, halign = "center", valign = "center", spacing = 1.25);

// ---- form 1: neon ----
CALL_Y_N = 0.95 * H_SIZE + (C_SIZE - 0.42 * H_SIZE);
module neon_words2d() { handle2d(SCRIPT); call2d(CALL_Y_N); }
OUTLINE = 2.2;
module neon_base2d() offset(r = OUTLINE, $fn = 24) offset(r = 1.6, $fn = 16) offset(delta = -1.6) offset(r = 1.6, $fn = 16) neon_words2d();

// ---- form 5: plaque ----
PW = WIDE + 14; P_SIZE = (WIDE - 6) / W_BOLD; PH = 3.2 * P_SIZE + 12; PR = 5; BORDER = 1.6; INSET = 3;
module plaque_words2d() { translate([0, -0.45 * P_SIZE]) handle2d(BOLD, WIDE - 6); clean() translate([0, 0.95 * P_SIZE]) text(CALL, size = 0.55 * P_SIZE, font = BOLD, halign = "center", valign = "center", spacing = 1.25); }
module plate2d() offset(r = PR, $fn = 32) square([PW - 2 * PR, PH - 2 * PR], center = true);
module border2d() difference() { offset(delta = -INSET) plate2d(); offset(delta = -INSET - BORDER) plate2d(); }

module base() linear_extrude(THICK - RAISE) if (style == "neon") neon_base2d(); else plate2d();
module letters() translate([0, 0, THICK - RAISE]) linear_extrude(RAISE)
    if (style == "neon") neon_words2d(); else { plaque_words2d(); border2d(); }

if (part == "base") base();
else if (part == "letters") letters();
else if (part == "union") union() { base(); letters(); }
else { color("#1C1C1F") base(); color("#F28C28") letters(); }
