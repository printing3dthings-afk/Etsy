// Victorian Bay Chocolate Shop (Valentine's 2027). Scott's brief, 2026-10-26;
// form 1 of five (../../concepts/shop_forms.jpg), picked with the Chocolate
// Box. A village building, made to stand with the Christmas Victorians.
//
// A brick shop on the village's snow base: a canted bay display window under
// a striped awning, the shelves of chocolates in it built into the back of its
// glass, so they show only when it is lit; CHOCOLATES in raised letters over
// the awning; a panelled door beside the bay; heart windows on the sides and
// back with Cupid's arrows in them, lit; arched upstairs windows with glazing
// bars; stone quoins; a slate mansard with a heart dormer and a chimney.
//
// One print, matte white, hollow and open underneath over a battery LED
// tealight. The parts below are colour only for the renders.

part = "all";       // body | roof | trim | accent | glass | art | all
EMB  = 0;           // for the gate's one-body union: parts sink this far into each other
SH   = 1.6;         // relief undersides climb 1.6 per 1 out (58 deg)
$fa = 4; $fs = 0.4;

W  = 52;            // the walls, outside: 48.4 x 46.4 clear inside, a 46 tealight goes under
D  = 50;
Z0 = 7;             // the base's top
H  = 72;            // the walls' top

include <../../../christmas_lanterns/lantern_scenes.scad>     // SW, glow_out, glow_clean
include <../../../christmas_village/relief_lib.scad>          // art_in
include <../../../brand/obc_mark.scad>
include <../shop_lib.scad>
include <../../valentine_scenes.scad>

// ---- the bay --------------------------------------------------------------------------------
BP = 7;             // out from the front wall
BB = 17;            // half its width at the wall
BF = 11;            // half its front's width
BT = 31;            // its top
YW = -D / 2;        // the front wall's face
module bay2d(o = 0) offset(delta = o) polygon([[-BB, YW + 0.01], [BB, YW + 0.01], [BF, YW - BP], [-BF, YW - BP]]);
// the bay's three faces: origin at the face's middle, its outward angle
// the sides' cant: the turn from the front face's direction to a side's, so
// atan2(BP, BB - BF). It was atan2(BB - BF, BP), 8.8 deg short: the side panes,
// frames and cuts stood off their walls, the panes poked into the bay and the
// slicer propped the pockets at both ends (2026-10-27)
BSA = atan2(BP, BB - BF);
BFACES = [[[0, YW - BP], 0, BF], [[(BB + BF) / 2, YW - BP / 2], BSA, norm([BB - BF, BP]) / 2],
          [[-(BB + BF) / 2, YW - BP / 2], -BSA, norm([BB - BF, BP]) / 2]];
module bface(i, w = 0) let (f = BFACES[i]) translate([f[0][0], f[0][1], 0]) rotate([0, 0, f[1]]) translate([0, -w, 0]) rotate([90, 0, 0]) children();
// the panes: the front one wide, the sides narrow, each inside its face by a post
BG = [Z0 + 4, BT - 3];
function bpane(i) = i == 0 ? [-BF + 2, BF - 2] : [-BFACES[i][2] + 1.8, BFACES[i][2] - 1.8];
module bpane2d(i) let (p = bpane(i)) translate([p[0], BG[0]]) square([p[1] - p[0], BG[1] - BG[0]]);
// The cut stops at the wall's inside face: running 1 mm on, as the plain
// walls' cuts do, it left a pocket at each back corner where the bay meets the
// shop's wall, its ceiling over air (2026-10-27)
module bay_cut(i) bface(i) {
    translate([0, 0, -T - 0.01]) linear_extrude(PANE + 0.02) bpane2d(i);
    translate([0, 0, -T + PANE]) shear_v() linear_extrude(T - PANE + 1) bpane2d(i);
}
module bay_glass() for (i = [0 : 2]) bface(i) translate([0, 0, -T]) linear_extrude(PANE) bpane2d(i);
// The bay's inside opens into the shop. Its ceiling rises 1.19 per 1 from
// the bay's front (just under its top) back through the wall, 50 deg, so it
// prints from the bay's front wall without support.
module bay_room() intersection() {
    union() {
        translate([0, 0, Z0 - 1]) linear_extrude(BT + 20) bay2d(-T);
        // through the front wall, from where bay2d(-T)'s back edge stops (T
        // in front of the wall: the first build left that strip standing and
        // the bay sat sealed off from the light)
        // only as wide as the bay is inside at the wall: wider, it undercut the
        // ends of the side panes
        translate([-11, YW - T - 0.1, Z0 - 1]) cube([22, 2 * T + 0.2, BT + 20]);
    }
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 1.19, 1, BT - 1 + 1.19 * (BP - T - YW)], [0, 0, 0, 1]]) translate([-100, -100, -200]) cube(200);
}
// The awning is the bay's roof: canvas from the wall over the bay and 3 past
// it, a valance round its front and sides, and under the overhang a cove
// rising SH per 1 out from the bay's top edge.
AO = 3; AV = 3.5; DR = 7;
ZF = BT + SH * AO;          // the valance's foot
ZT = ZF + AV + DR;          // the canvas's top, on the wall
module slab(z, h = 0.01) translate([0, 0, z]) linear_extrude(h) children();
module awning() {
    hull() { slab(BT - 0.01) bay2d(); slab(ZF) bay2d(AO); }
    slab(ZF, AV) bay2d(AO);
    hull() { slab(ZF + AV - 0.01) bay2d(AO); translate([-BB - AO, YW - 0.01, ZT - 0.01]) cube([2 * (BB + AO), 0.01, 0.01]); }
}
// raised ribs down the canvas's front face: its stripes, read on a white print
module awning_ribs() let (y0 = YW, y1 = YW - BP - AO, z0 = ZT, z1 = ZF + AV, n = 6)
    for (i = [0 : n - 1]) let (u = -BF + 1.4 + i * (2 * BF - 2.8) / (n - 1))
        hull() {
            translate([u - 0.9, y0 - 0.01, z0 - 0.01]) cube([1.8, 0.01, 0.61]);
            translate([u - 0.9, y1, z1 - 0.01]) cube([1.8, 0.01, 0.61]);
        }
// scallops on the valance's front
module awning_scallops() translate([0, YW - BP - AO, 0]) rotate([90, 0, 0]) translate([0, 0, -EMB]) glow_out(0.7, 2)
    intersection() {
        for (i = [0 : 6]) translate([-BF - 1.2 + (i + 0.5) * (2 * BF + 2.4) / 7, ZF + 0.6]) circle(1.6, $fn = 24);
        translate([-BF - 1.2, ZF]) square([2 * BF + 2.4, 2.2]);
    }

// ---- the walls' openings ----------------------------------------------------------------------
UW = [57, 66];              // the upstairs windows, sill and head: over the sign, under the ceiling
module arch2d(w, z0, z1) { translate([-w / 2, z0]) square([w, z1 - z0 - w / 2]); translate([0, z1 - w / 2]) circle(w / 2, $fn = 48); }
module upper2d(u) translate([u, 0]) arch2d(9, UW[0], UW[1]);
module upper_bars(u) translate([u, 0]) { translate([-0.55, UW[0]]) square([1.1, UW[1] - UW[0]]); translate([-5, (UW[0] + UW[1]) / 2 - 1.5]) square([10, 1.1]); }
HEARTW = 15;
module side_heart2d() heart_at(0, 30, HEARTW);
module back_heart2d() heart_at(0, 31, 17);
// ---- the roof ---------------------------------------------------------------------------------
// A mansard: from a soffit rising 1.6 per 1 out over the walls' top, a steep
// lower slope to RL, a gentle upper one to RT.
RL = 16; RT = 24; RO = 2;
module roof_outer() hull() {
    translate([-W / 2, -D / 2, H - 0.01]) cube([W, D, 0.01]);
    translate([-W / 2 - RO, -D / 2 - RO, H + SH * RO]) cube([W + 2 * RO, D + 2 * RO, 0.4]);
    translate([-(W / 2 + RO) * 0.62, -(D / 2 + RO) * 0.60, H + RL]) cube([(W + 2 * RO) * 0.62, (D + 2 * RO) * 0.60, 0.01]);
    translate([-(W / 2 + RO) * 0.30, -(D / 2 + RO) * 0.30, H + RT - 0.01]) cube([(W + 2 * RO) * 0.30, (D + 2 * RO) * 0.30, 0.01]);
}
// Inside, the hollow's ceiling is a hip at 50 deg from 6 under the walls'
// top: the mansard is too low over a 48 mm room for a ceiling from the
// walls' top itself, and the upstairs windows stop under it.
ZC = H - 6;
CR = (D / 2 - T) * 1.19;    // its rise to the ridge
module room() hull() {
    translate([-W / 2 + T, -D / 2 + T, Z0 - 1]) cube([W - 2 * T, D - 2 * T, ZC - Z0 + 1]);
    translate([-(W - D) / 2, 0, ZC + CR]) cube([W - D + 0.01, 0.01, 0.01], center = true);
}
// the heart dormer on the front's lower slope; its gable on top
DW = 14;
module dormer() let (yf = -D / 2 + 1, z0 = H + 4, z1 = H + 15) {
    translate([-DW / 2, yf, z0]) cube([DW, 12, z1 - z0]);
    // flush with its walls: a gable standing past them would hang
    hull() { translate([-DW / 2, yf, z1 - 0.01]) cube([DW, 12, 0.01]); translate([-0.01, yf, z1 + 6]) cube([0.02, 12, 0.01]); }
}
module dormer_heart() translate([0, -D / 2 + 1, 0]) rotate([90, 0, 0]) translate([0, 0, -EMB]) glow_out(0.9, 2) {
    difference() { heart_at(0, H + 9.8, 8.4); heart_at(0, H + 9.8, 5.0); }
    heart_at(0, H + 9.8, 2.6);
}
module chimney() {
    translate([10, 6, H + 4]) cube([7, 7, 26]);
    hull() { translate([10, 6, H + 29]) cube([7, 7, 0.01]); translate([9.2, 5.2, H + 30.3]) cube([8.6, 8.6, 1.5]); }
}

// ---- daylight relief on the walls -----------------------------------------------------------
module frames() {
    for (u = [-13, 13]) win_frame(0, emb = EMB) upper2d(u);
    for (a = [90, 270]) { win_frame(a, emb = EMB) side_heart2d(); win_frame(a, emb = EMB) upper2d(0); }
    win_frame(180, emb = EMB) back_heart2d(); win_frame(180, emb = EMB) upper2d(0);
    // the bay's posts and head, round its panes
    for (i = [0 : 2]) bface(i) translate([0, 0, -EMB]) glow_out(0.8, 2) frame_ring(1.2) bpane2d(i);
}
module bars() {
    for (u = [-13, 13]) win_bars(0, h = 0.8) { upper2d(u); upper_bars(u); }
    for (a = [90, 270, 180]) win_bars(a, h = 0.8) { upper2d(0); upper_bars(0); }
}
// stone quoins up the corners above the bay, alternating long and short
module quoins() for (a = [0 : 90 : 270]) for (k = [0 : 6]) let (z = BT + 3 + k * 5.4, q = k % 2 == 0 ? 5.0 : 3.2, e = fdist((a + 90) % 360))
    for (s = [-1, 1]) relief(a, 0.6, EMB) translate([s > 0 ? e - q : -e, z]) square([q, 4.2]);
// the door beside the bay: a raised panel in a frame, a heart on it
DU = 21.5;
module door() relief(0, 0.7, EMB) translate([DU, 0]) { arch2d(6.4, Z0, Z0 + 20); }
module door_frame() relief(0, 1.2, EMB) translate([DU, 0]) difference() { offset(delta = 1.2) arch2d(6.4, Z0, Z0 + 20); arch2d(6.4, Z0 - 1, Z0 + 20); }
module door_heart() face(0) translate([0, 0, 0.69 - 2 * EMB]) glow_out(0.6, 2) heart_at(DU, Z0 + 12.5, 3.2);
// the sign over the awning
SV = ZT + 4.8;
module sign() sign_board(0, SV, 40, 7.4, EMB);
module letters() sign_letters(0, "CHOCOLATES", SV, 3.7, 1.08, EMB);

// ---- the scenes in the glass ----------------------------------------------------------------
module art_all() {
    bface(0) translate([0, 0, -T + EMB]) art_in(ART_D, 4) glow_clean() translate([0, BG[0]]) display(2 * (BF - 2), BG[1] - BG[0]);
    for (a = [90, 270]) win_art(a, EMB) intersection() { offset(delta = -1.0) side_heart2d(); translate([0, 30]) cupid_arrow(HEARTW); }
}

// ---- parts ----------------------------------------------------------------------------------
DRIFTS = [[W / 2 + 1, 12, 4, 7, 3.0], [-W / 2 - 1, -8, 4, 6, 2.6], [-14, D / 2 + 1, 7, 3.5, 2.6], [16, D / 2 + 1, 6, 3.5, 2.4]];
module panes() { bay_glass(); for (u = [-13, 13]) win_pane(0) upper2d(u);
    for (a = [90, 270]) { win_pane(a) side_heart2d(); win_pane(a) upper2d(0); }
    win_pane(180) back_heart2d(); win_pane(180) upper2d(0); }
module cuts() { for (i = [0 : 2]) bay_cut(i); for (u = [-13, 13]) win_cut(0) upper2d(u);
    for (a = [90, 270]) { win_cut(a) side_heart2d(); win_cut(a) upper2d(0); }
    win_cut(180) back_heart2d(); win_cut(180) upper2d(0); }
module body_solid() { block(); translate([0, 0, Z0 - 0.01]) linear_extrude(BT - Z0 + 0.01) bay2d(); }
module roof_solid() { roof_outer(); dormer(); chimney(); }
module hollow() { room(); bay_room(); }

module p_glass() panes();
// the scenes stand in the room's air only: the display ran past its pane
// under the bay's posts and into the wall
module p_art() intersection() { difference() { art_all(); if (EMB == 0) panes(); } if (EMB == 0) hollow(); else union() { hollow(); panes(); } }
module p_accent() difference() { union() { awning(); awning_ribs(); letters(); door(); door_heart(); } if (EMB == 0) { panes(); art_all(); } hollow(); }
module p_trim() difference() {
    union() { base(DRIFTS) bay2d(AO + 1); frames(); bars(); sign(); quoins(); door_frame(); awning_scallops(); dormer_heart(); }
    if (EMB == 0) { panes(); art_all(); p_accent(); }
    hollow(); mark_cut();
}
module p_roof() difference() { roof_solid(); hollow(); if (EMB == 0) { p_trim(); p_accent(); } }
module p_body() difference() { body_solid(); hollow(); cuts(); if (EMB == 0) { p_roof(); p_trim(); p_accent(); } }

if (part == "body") p_body();
else if (part == "roof") p_roof();
else if (part == "trim") p_trim();
else if (part == "accent") p_accent();
else if (part == "glass") p_glass();
else if (part == "art") p_art();
else if (part == "all") {
    color("#A8483A") p_body(); color("#3B4048") p_roof(); color("#F4F1EA") p_trim();
    color("#C8314A") p_accent(); color("#F4F1EA") p_glass(); color("#5A2A20") p_art();
}
