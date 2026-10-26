// Swan Crown Love Lantern (Valentine's 2027). Scott's brief, 2026-10-26;
// form 3 of five (../concepts/lantern_forms.jpg), picked with the Standing
// Heart.
//
// A glowing drum over a battery LED tealight, a pond at night built into the
// inside of its glass: unlit the drum is plain, lit two swans glide to meet
// under a heart, among reeds, under a crescent moon. A lid sits on top, and on
// the lid two swans whose necks draw a heart. The names and date stand out of
// the plinth's front.
//
// Three prints, side by side on one plate, single colour (matte white):
//   drum   upright, open at both ends: it lifts off over the light
//   lid    flat, sits in the collar on the drum's rim, hearts cut through it
//          so the light shows above
//   crown  flat on its face, and pushed into the slot in the lid's boss. Stood
//          up as it is shown, its bowed heads and the inside of its notch would
//          hang in the air with nothing under them; flat, every line is on the
//          plate.
//
// OpenSCAD cannot bend geometry, so the pond and the names are built flat here
// (art_flat, text_flat) and wrapped round the drum by build.sh (part_mesh wrap).

// ===== PERSONALISE: edit these two lines per order =========================
NAMES = "Emma & James";
DATE  = "02.14.2027";
// ============================================================================
FONT  = "Playfair Display";
FAT   = 0.25;       // every letter grown this much: Playfair's hairlines are under a bead at 6 mm

part = "all";       // frame | glass | art_flat | text_flat | lid | crown | crown_shown | all
EMB  = 0;           // for the gate's one-body union: parts sink this far into each other
SH   = 1.6;         // relief undersides climb 1.6 per 1 (58 deg)
$fa = 3; $fs = 0.4;
FN   = 240;         // round enough that the wrapped art meets the glass

include <../../christmas_lanterns/lantern_scenes.scad>    // SW, glow_out, glow_clean
include <../../christmas_village/relief_lib.scad>         // art_in
include <../../brand/obc_mark.scad>
include <../valentine_scenes.scad>

// ---- the drum ------------------------------------------------------------------------------
R     = 40;         // the glass's outer face
PANE  = 0.9;        // the glass: two lines, so it glows
RI    = R - PANE;   // 78 inside: a 46 mm tealight drops through with room
ART_D = 2.0;        // the pond, out of the back of the glass: 2.9 mm in all
RP    = R + 4;      // the plinth
ZP    = 17;         // its height: the names' band
RF    = 34;         // a foot inside the plinth, for the maker's mark
H     = 64;         // the glass
ZG    = ZP + H;     // the rim's underside meets the glass here
RO    = 3;          // the rim, out past the glass
RH    = 4;          // its height above ZG
CO    = 1.6;        // the collar round the rim's top, holding the lid
CH    = 2.4;        // its height
ZT    = ZG + RH;    // the rim's top, where the lid sits
HS    = 58;         // the pond's height on the glass
ZA    = ZP + 3;     // its foot
LI    = 2 * PI * RI;    // the pond's length, round the inside of the glass
LP    = 2 * PI * RP;    // the plinth's face, unrolled

// ---- frame: plinth and rim -----------------------------------------------------------------
module plinth() difference() {
    union() { cylinder(r = RP, h = ZP - 2, $fn = FN); translate([0, 0, ZP - 2]) cylinder(r1 = RP, r2 = R + 1.5, h = 2, $fn = FN); }
    translate([0, 0, -1]) cylinder(r = RF, h = ZP + 2, $fn = FN);
    translate([0, 0, 1.6]) cylinder(r = RI, h = ZP + 2, $fn = FN);
}
// out RO past the glass, its underside sloped in, SH up per 1 out; a collar
// round its top for the lid
module rim() difference() {
    union() {
        translate([0, 0, ZG - SH * RO]) cylinder(r1 = R, r2 = R + RO, h = SH * RO, $fn = FN);
        translate([0, 0, ZG]) cylinder(r = R + RO, h = RH, $fn = FN);
        translate([0, 0, ZT - 0.01]) difference() { cylinder(r = R + RO, h = CH + 0.01, $fn = FN); translate([0, 0, -1]) cylinder(r = R + RO - CO, h = CH + 2, $fn = FN); }
    }
    translate([0, 0, ZG - SH * RO - 1]) cylinder(r = RI, h = RH + SH * RO + 2, $fn = FN);
}
// the maker's mark under the plinth's front, read tipped back, centred on the
// plinth's 10 mm underside: on the foot's inner half it came within 0.35 mm
// of the edge and the slicer propped the letters
MARK_Y = -(RF + RP) / 2;
module frame() difference() { union() { plinth(); rim(); } translate([0, MARK_Y, 0]) obc_engrave(4.4, 0.8, 0.15, ridges = false); }
module glass() difference() {
    translate([0, 0, ZP - 0.5]) difference() { cylinder(r = R, h = H + 1, $fn = FN); translate([0, 0, -1]) cylinder(r = RI, h = H + 3, $fn = FN); }
    if (EMB == 0) frame();
}

// ---- flat parts for the wrap: x along the face, y up, z out -----------------------------------
// The pond, into the back of the glass (toward -z), centred on the front (-y)
// once wrapped. Its seam is at the back, under the reeds.
module art_flat() translate([-PI / 2 * RI, 0, 0]) art_in(ART_D, 4) glow_clean()
    intersection() { translate([-LI / 2 + 0.025, 0]) square([LI - 0.05, HS]); pond_panorama(LI, HS); }
// The names fitted to the plinth's front: NW of arc reads from in front.
// Playfair Bold, grown FAT, runs about 0.82 of its size a letter, figures and
// stops about 0.7 (measured on the Standing Heart). A pair too long for 3.6 mm
// letters on one line breaks after the "&" onto two.
NW = 56;
function sub(s, a, b) = b < a ? "" : chr([for (i = [a : b]) ord(s[i])]);
AMP = search("&", NAMES);
ONE = min(6.0, NW / (len(NAMES) * 0.82));
TWO = len(AMP) > 0 && ONE < 3.6;
N1 = TWO ? sub(NAMES, 0, AMP[0]) : NAMES;
N2 = TWO ? sub(NAMES, AMP[0] + 2, len(NAMES) - 1) : "";
NSZ = TWO ? min(4.6, NW / (max(len(N1), len(N2)) * 0.82)) : ONE;
DSZ = min(TWO ? 3.0 : 3.8, (NW - 12) / (len(DATE) * 0.7));
module names2d() {
    module line(t, y, sz, sp = 1) translate([0, y]) offset(r = FAT)
        text(t, size = sz, font = FONT, halign = "center", valign = "baseline", spacing = sp);
    if (TWO) { line(N1, 10.4, NSZ); line(N2, 5.4, NSZ); line(DATE, 1.6, DSZ, 1.08); }
    else { line(NAMES, 8.0, NSZ); line(DATE, 2.4, DSZ, 1.08); }
}
module text_flat() translate([-PI / 2 * RP, 0, 0]) glow_out(1.0, 2) names2d();

// ---- lid ------------------------------------------------------------------------------------
RL  = R + RO - CO - 0.3;    // inside the collar with 0.3 to spare
LT  = 3;                    // its thickness
BR  = 13; BT = 3;           // the boss on top, holding the crown
CT  = 4.0;                  // the crown's thickness
TW  = 18; TD = 5.0;         // the crown's tab: width, depth into the boss and lid
FIT = 0.2;                  // the slot over the tab, each way: a push fit on a P1S
module heart_vents() for (i = [0 : 5]) rotate(i * 60 + 30) translate([0, 27.5]) rotate(180) heart_at(0, 0, 8);
module lid() difference() {
    union() { cylinder(r = RL, h = LT, $fn = FN); cylinder(r = BR, h = LT + BT, $fn = 120); }
    translate([0, 0, -1]) linear_extrude(LT + 2) heart_vents();
    translate([-(TW + FIT) / 2, -(CT + FIT) / 2, LT + BT - TD]) cube([TW + FIT, CT + FIT, TD + 1]);
}

// ---- crown: two swans, necks a heart -------------------------------------------------------
CW = 86; CHH = 80;          // the crown's drawing: width, height
NECK = 3.0;                 // its necks: a free-standing piece wants more than a pane's line
module crown2d() {
    // the swans' waterline at y = 0, the tab under it
    translate([0, -CHH * 0.24 + 1.0]) swans_heart(CW, CHH, nw = NECK, water = false, wing = true, bh = CW * 0.12);
    translate([-TW / 2, -TD]) square([TW, TD + 1.0]);
}
// its top edges stepped in, a layer at a time, so it reads carved, not cut
module crown() { linear_extrude(CT - 0.6) crown2d(); for (i = [1 : 3]) translate([0, 0, CT - 0.8 + 0.2 * i]) linear_extrude(0.2) offset(delta = -0.25 * i) crown2d(); }
// as it stands in the lid, for the renders and the fit check
module crown_shown() translate([0, CT / 2, ZT + LT + BT - TD]) rotate([90, 0, 0]) translate([0, TD, 0]) crown();

if (part == "frame") frame();
else if (part == "glass") glass();
else if (part == "art_flat") art_flat();
else if (part == "text_flat") text_flat();
else if (part == "lid") lid();
else if (part == "crown") crown();
else if (part == "crown_shown") crown_shown();
else if (part == "all") {
    color("#B8323F") frame(); color("#F4F1EA") glass();
    color("#B8323F") translate([0, 0, ZT]) lid(); color("#D4A64A") crown_shown();
}
