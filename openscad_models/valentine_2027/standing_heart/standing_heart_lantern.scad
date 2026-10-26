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
ZT   = 16;          // its point's height; the pedestal swallows the point
D    = 26;          // half its depth: 52 front to back
PANE = 0.9;         // the glowing panes: two lines
RIM  = 3.0;         // the heart's side wall
LIP  = 1.0;         // the outline standing out of front and back, read in daylight
LIPW = 2.4;
ART_D = 2.0;        // the scenes, out of the back of the pane: 2.9 mm in all
PW = 58; PD = 60;   // the pedestal's foot: 53 x 55 inside, 48 behind the ledge
PS = 18;            // its upright band, where the names go
ZH = 34;            // its shoulders meet the heart here: their insides lean 42 deg
PT = 2.4;           // its walls
LEDGE = 7;          // a shelf inside its front, on the plate, for the maker's mark

HR = HW * 0.28;  HC = HW / 2 - HR;  HZ = ZT + HW * 0.68;    // the heart's lobes: radius, centres
RI = HR - RIM;

module heart_outer() translate([0, ZT]) heart2(HW);
// The hollow. Under each lobe its ceiling is the lobe's arc only below the
// lobe's sides; above, two 45 deg chords meet at the top of the arc, so the
// inside of the lobe prints without support. The outside stays round.
module tents() for (s = [-1, 1]) polygon([[s * HC - 300, HZ + RI - 300], [s * HC, HZ + RI], [s * HC + 300, HZ + RI - 300]]);
module inner2d() offset(delta = -RIM) heart_outer();
module cavity2d() intersection() { inner2d(); tents(); }
// Above the chords the hollow carries on only as slots behind each pane, each
// SHC up per 1 in, so the panes stay thin right up to the lobes' curve (a
// heart lit everywhere, not an M) while the wedge left between the slots
// leans 50 deg: the first version stopped the hollow at the chords and the
// lobes' tops showed dark (2026-10-26).
SHC = 1.2;
module cap2d() difference() { inner2d(); cavity2d(); }
// One exact solid per side: the cap, less what lies within SHC per 1 in of
// its top, measured in from the pane (a shear in z), so no stack of slices.
module slots() for (sd = [-1, 1]) intersection() {
    xz(-(D - PANE), D - PANE) cap2d();
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
// the names fitted to the band: Playfair's letters average about 0.56 of their size
NSZ = min(6.0, (PW - 16) / (len(NAMES) * 0.56));
DSZ = min(3.8, (PW - 30) / (len(DATE) * 0.6));
module names2d() {
    translate([0, 9.6]) offset(r = FAT) text(NAMES, size = NSZ, font = FONT, halign = "center", valign = "baseline");
    translate([0, 3.6]) offset(r = FAT) text(DATE, size = DSZ, font = FONT, halign = "center", valign = "baseline", spacing = 1.08);
}
module text_part() on_front(PD / 2) translate([0, 0, -EMB]) glow_out(1.0, 2) names2d();

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
