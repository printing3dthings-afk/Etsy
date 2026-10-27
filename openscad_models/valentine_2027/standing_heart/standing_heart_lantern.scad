// Standing Heart Love Lantern (Valentine's 2027). Scott's brief, 2026-10-26;
// form 1 of five (../concepts/lantern_forms.jpg), picked with the Swan Crown.
//
// A heart standing in a pedestal over a battery LED tealight. Its front and
// back are thin glowing panes; the couple under the lamppost is built on the
// back of the front pane, the two swans on the back of the back pane, so unlit
// the heart is plain and lit the scenes show dark on the glow (Scott,
// 2026-10-26). The names and date are raised on the pedestal's front, where
// they read in daylight.
//
// Printed in one piece, upright, no supports, single colour (matte white).
// The base is open: it lifts off and goes back down over the light.

// ===== PERSONALISE: edit these two lines per order =========================
NAMES = "Emma & James";
DATE  = "02.14.2027";
// ============================================================================
FONT  = "Playfair Display";
FAT   = 0.25;       // every letter grown this much: Playfair's hairlines are under a bead at 6 mm

part = "all";       // frame | glass | art | lip | text | all | union
EMB  = 0;           // for the gate's one-body union: parts sink this far into each other
SH   = 1.6;         // relief undersides climb 1.6 per 1 out (58 deg); see the hex lantern
$fa = 3; $fs = 0.4;

include <../../christmas_lanterns/lantern_scenes.scad>    // SW, glow_out, glow_clean
include <../../christmas_village/relief_lib.scad>         // art_in
include <../../brand/obc_mark.scad>
include <../valentine_scenes.scad>

// ---- size ------------------------------------------------------------------------------------
HW   = 104;         // the heart's width
ZT   = 20;          // its point's height; the pedestal swallows the point
D    = 26;          // half its depth: 52 front to back
PANE = 0.9;         // the glowing panes: two lines
RIM  = 3.0;         // the heart's side wall
LIP  = 1.0;         // the outline standing out of front and back, read in daylight
LIPW = 2.4;
ART_D = 2.0;        // the scenes, out of the back of the pane: 2.9 mm in all
PW = 58; PD = 60;   // the pedestal's foot: 53 x 55 inside, 48 behind the ledge
PS = 18;            // its upright band, where the names go
ZH = 38;            // its shoulders meet the heart here: their insides lean 41 deg
PT = 2.4;           // its walls
LEDGE = 7;          // a shelf inside its front, on the plate, for the maker's mark

HR = HW * 0.28;  HC = HW / 2 - HR;  HZ = ZT + HW * 0.68;    // the heart's lobes: radius, centres
RI = HR - RIM;

module heart_outer() translate([0, ZT]) heart2(HW);
// The hollow's ceiling is one tent, its peak at the notch, its sides rising TS
// per 1 (58 deg) from the heart's side walls. A tent per lobe looked better on paper and was not printable:
// the two met in a valley under the notch that ran pane to pane in mid-air,
// and the slicer could only prop it up or bridge it (2026-10-26). One peak
// has no valley: every part of the ceiling leans down to a wall. The outside
// stays round; slots (below) keep the panes thin above the tent.
TS = 1.6;
CZ = HZ + sqrt(RI * RI - HC * HC);    // the notch, inside
module tents() polygon([[-300, CZ - 300 * TS], [0, CZ], [300, CZ - 300 * TS]]);
module inner2d() offset(delta = -RIM) heart_outer();
module cavity2d() intersection() { inner2d(); tents(); }
// Above the tent the hollow carries on only as slots behind each pane, each
// SHC up per 1 in, so the panes stay thin right up to the lobes' curve (a
// heart lit everywhere, not an M): the first version stopped the hollow at
// the tent and the lobes' tops showed dark (2026-10-26). Where a slot's
// ceiling meets the tent the two make a crease shallower than either; at
// 50 deg tent and 63 deg slots it ran at 39 deg and the slicer propped it up.
// 58 and 72 keep every crease over 50.
SHC = 3.0;
module cap2d() difference() { inner2d(); cavity2d(); }
// One exact solid per side: the cap, less what lies within SHC per 1 in of
// its top, measured in from the pane (a shear in z), so no stack of slices.
// SLOT deep at most: that is enough for the flame to see every point of the
// panes, and slots any deeper met in the middle in a ridge too shallow to
// print (the slicer propped up everything above it).
SLOT = 12;
module slots() for (sd = [-1, 1]) intersection() {
    xz(sd < 0 ? -(D - PANE) : D - PANE - SLOT, sd < 0 ? -(D - PANE) + SLOT : D - PANE) cap2d();
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, sd * SHC, 1, -SHC * (D - PANE)], [0, 0, 0, 1]]) xz(-D - 40, D + 40) cap2d();
}

// a 2D shape in (x, z) as a prism through the heart's depth
module xz(h0, h1) translate([0, h1, 0]) rotate([90, 0, 0]) linear_extrude(h1 - h0) children();
// on the front face: (u, v) -> (x, z), local z out of the face (-y)
module on_front(d = D) translate([0, -d, 0]) rotate([90, 0, 0]) children();
module on_back(d = D) translate([0, d, 0]) rotate([90, 0, 180]) children();
module above(z) intersection() { children(); translate([-300, z]) square([600, 300]); }

// ---- the pedestal --------------------------------------------------------------------------
module rrect(w, d, r) offset(r = r) square([w - 2 * r, d - 2 * r], center = true);
module slice(z) intersection() { children(); translate([-200, -200, z]) cube([400, 400, 0.01]); }
module ped_outer() hull() { linear_extrude(PS) rrect(PW, PD, 6); slice(ZH) xz(-D, D) heart_outer(); }
module ped_inner() hull() {
    translate([0, 0, -1]) linear_extrude(PS + 1) rrect(PW - 2 * PT, PD - 2 * PT, 6 - PT);
    slice(ZH) xz(-D + PANE, D - PANE) cavity2d();
}

// ---- frame ---------------------------------------------------------------------------------
module hollow() { ped_inner(); intersection() { xz(-D + PANE, D - PANE) cavity2d(); translate([-200, -200, ZH - 0.01]) cube(400); } slots(); }
module heart_shell() difference() { intersection() { xz(-D, D) heart_outer(); translate([-200, -200, ZH - 0.5]) cube(400); } hollow(); }
module ledge() translate([-14, -PD / 2 + PT - 0.5, 0]) cube([28, LEDGE + 0.5, PT]);
module frame_raw() { difference() { ped_outer(); hollow(); } heart_shell(); ledge(); }
module frame() difference() {
    frame_raw();
    glass_region();
    // the maker's mark under the ledge, read tipped back (obc_mark.scad)
    translate([0, -PD / 2 + PT + LEDGE / 2, 0]) obc_engrave(4.4, 0.8, 0.15, ridges = false);
}
// the panes: where the hollow comes within PANE of the faces
module glass_region() intersection() { heart_shell(); xz(-D - 1, D + 1) above(ZH) inner2d(); }
module glass() glass_region();

// ---- inside the panes: the scenes, hidden until lit ---------------------------------------
PANE_IN = 1.0;      // scenes stay this far inside the pane's edge
module front_scene() intersection() { offset(delta = -PANE_IN) above(ZH) inner2d(); translate([0, ZH + 4]) couple_lamppost(64, 62); }
module back_scene()  intersection() { offset(delta = -PANE_IN) above(ZH) inner2d(); translate([0, ZH + 14]) swans_heart(78, 60); }
module art() {
    on_front() translate([0, 0, -PANE + EMB]) art_in(ART_D, 4) glow_clean() front_scene();
    on_back() translate([0, 0, -PANE + EMB]) art_in(ART_D, 4) glow_clean() mirror([1, 0]) back_scene();
}

// ---- outside: the outline lip and the names -------------------------------------------------
module lip2d() above(ZH + 0.5) difference() { heart_outer(); offset(delta = -LIPW) heart_outer(); }
module lip() { on_front() translate([0, 0, -EMB]) glow_out(LIP, 2) lip2d(); on_back() translate([0, 0, -EMB]) glow_out(LIP, 2) lip2d(); }
// The names fitted to the flat of the front, NW wide between its rounded
// corners. Playfair Bold, grown FAT, runs about 0.82 of its size a letter
// (measured: "Emma & James" at 6 came out 58 wide, not the 40 first assumed,
// and ran round the corners); figures and stops about 0.7. A pair too long
// for 3.6 mm letters on one line breaks after the "&" onto two.
// The names are spaced 1.08 and the date 1.25 and cleaned with letter_clean
// (2026-10-27): glow_clean's 0.6 grow filled every counter and ran the date
// into one shape. Per letter 0.82 became 0.87, and per figure 0.7 became 0.8,
// for the wider spacing.
NW = PW - 2 * 6 - 4;
function sub(s, a, b) = b < a ? "" : chr([for (i = [a : b]) ord(s[i])]);
AMP = search("&", NAMES);
ONE = min(6.0, NW / (len(NAMES) * 0.87));
TWO = len(AMP) > 0 && ONE < 3.6;
N1 = TWO ? sub(NAMES, 0, AMP[0]) : NAMES;
N2 = TWO ? sub(NAMES, AMP[0] + 2, len(NAMES) - 1) : "";
NSZ = TWO ? min(4.6, NW / (max(len(N1), len(N2)) * 0.87)) : ONE;
DSZ = min(TWO ? 3.0 : 3.8, (NW - 8) / (len(DATE) * 0.8));
module names2d() {
    module line(t, y, sz, sp = 1.08) translate([0, y]) offset(r = FAT)
        text(t, size = sz, font = FONT, halign = "center", valign = "baseline", spacing = sp);
    if (TWO) { line(N1, 12.0, NSZ); line(N2, 6.8, NSZ); line(DATE, 2.4, DSZ, 1.25); }
    else { line(NAMES, 9.6, NSZ); line(DATE, 3.6, DSZ, 1.25); }
}
module text_part() on_front(PD / 2) translate([0, 0, -EMB]) glow_out(1.0, 2, lc = true) names2d();

// ---- parts ---------------------------------------------------------------------------------
// The colour parts stand clear of the body, so the parts check sees them
// disjoint; for the gate's union (EMB > 0) they sink in instead.
module clear() if (EMB > 0) children(); else difference() { children(); frame_raw(); glass_region(); }
module the(p) {
    if (p == "frame") frame();
    else if (p == "glass") glass();
    else if (p == "art") clear() art();
    else if (p == "lip") clear() lip();
    else if (p == "text") clear() text_part();
}
PARTS = ["frame", "glass", "art", "lip", "text"];
COLS  = ["#B8323F", "#F4F1EA", "#7A1F2B", "#F4F1EA", "#D4A64A"];
if (part == "all") for (i = [0 : len(PARTS) - 1]) color(COLS[i]) the(PARTS[i]);
else if (part == "union") union() for (p = PARTS) the(p);
else the(part);
