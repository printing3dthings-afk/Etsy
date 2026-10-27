// Chocolate Box Shop (Valentine's 2027). Scott's brief, 2026-10-26; form 2 of
// five (../../concepts/shop_forms.jpg), picked with the Victorian Bay. A
// village building, made to stand with the Christmas Gingerbreads.
//
// A gingerbread shop that is a box of chocolates: piped icing on every edge
// with drips under the top, heart windows in icing frames, a lid that
// overhangs on a cove, tied with a ribbon that runs down three walls, and a
// bow on top. CHOCOLATES in raised letters over an arched door. Lit, the front
// windows show truffles and a heart box on shelves, the sides Cupid's arrows,
// the back a heart in each heart.
//
// The bow sits on the lid, not standing up as in the concept: upright, its
// loops' undersides and the tops of their holes hang in the air. On the lid
// it is a puffed bow, loops and knot rising straight up and rounded over.
//
// One print, matte white, hollow and open underneath over a battery LED
// tealight. The parts below are colour only for the renders.

part = "all";       // body | roof | trim | accent | glass | art | all
EMB  = 0;           // for the gate's one-body union: parts sink this far into each other
SH   = 1.6;         // relief undersides climb 1.6 per 1 out (58 deg)
$fa = 4; $fs = 0.4;

W  = 54;            // the walls, outside: 49.2 clear inside
D  = 54;
Z0 = 7;             // the base's top
H  = 52;            // the walls' top, under the lid

include <../../../christmas_lanterns/lantern_scenes.scad>     // SW, glow_out, glow_clean
include <../../../christmas_village/relief_lib.scad>          // art_in
include <../../../brand/obc_mark.scad>
include <../shop_lib.scad>
include <../../valentine_scenes.scad>

// ---- the lid --------------------------------------------------------------------------------
LO = 2.5;           // its overhang
LH = 11;            // its height above the walls
LT = H + LH;        // its top
module lid() hull() {
    translate([-W / 2, -D / 2, H - 0.01]) cube([W, D, 0.01]);
    translate([-W / 2 - LO, -D / 2 - LO, H + SH * LO]) cube([W + 2 * LO, D + 2 * LO, LT - H - SH * LO]);
}
// Inside, the hollow's ceiling is a pyramid at 50 deg from ZC up to under the
// lid's top: over a 49 mm room it needs 29 of rise, more than the lid has,
// so it starts down in the walls and the windows stop under it.
CR = (W / 2 - T) * 1.19;
ZC = LT - 1.6 - CR;
module room() hull() {
    translate([-W / 2 + T, -D / 2 + T, Z0 - 1]) cube([W - 2 * T, D - 2 * T, ZC - Z0 + 1]);
    translate([0, 0, ZC + CR]) cube(0.01, center = true);
}

// ---- windows ---------------------------------------------------------------------------------
HW = 12;            // the heart windows' width
HZ = 22;            // their centre
WU = 14;            // and their distance either side of a face's middle: clear of the door's frame
module heart_win(u) heart_at(u, HZ, HW);
FACES_WIN = [0, 90, 180, 270];
module panes() for (a = FACES_WIN, u = [-WU, WU]) win_pane(a) heart_win(u);
module cuts() for (a = FACES_WIN, u = [-WU, WU]) win_cut(a) heart_win(u);
module frames() for (a = FACES_WIN, u = [-WU, WU]) win_frame(a, 1.5, 1.0, EMB) heart_win(u);
// the scenes in the glass: truffles and a heart box at the front, Cupid's
// arrows at the sides, a heart in each heart at the back
module art_all() for (a = FACES_WIN, u = [-WU, WU]) win_art(a, EMB) intersection() {
    offset(delta = -0.8) heart_win(u);
    if (a == 0) translate([u, HZ - HW * 0.42]) display(HW * 0.82, HW * 0.9);
    else if (a == 180) heart_at(u, HZ + 0.4, HW * 0.40);
    else translate([u, HZ]) cupid_arrow(HW);
}

// ---- icing ----------------------------------------------------------------------------------
// piping: a bead up every corner, a band round the walls' foot and top, drips
// hanging from the top band, all standing out of the walls with sloped
// undersides
module piping() {
    for (sx = [-1, 1], sy = [-1, 1]) translate([sx * W / 2, sy * D / 2, Z0 - 0.01]) cylinder(r = 1.7, h = H - Z0 + 0.01, $fn = 24);
    for (a = FACES_WIN) relief(a, 1.2, EMB) {
        translate([-fdist((a + 90) % 360), Z0]) square([2 * fdist((a + 90) % 360), 2.2]);
        translate([-fdist((a + 90) % 360), H - 2.6]) square([2 * fdist((a + 90) % 360), 2.6]);
    }
}
module drips() for (a = FACES_WIN) let (L = 2 * fdist((a + 90) % 360), n = 9)
    relief(a, 0.9, EMB) for (i = [0 : n - 1]) let (u = -L / 2 + (i + 0.5) * L / n, dl = [4.5, 3.0, 5.5, 3.6][i % 4])
        if (a == 0 || abs(u) > RW / 2 + 1.5) hull() { translate([u, H - 2.5]) circle(1.4, $fn = 20); translate([u, H - 2.5 - dl]) circle(1.2, $fn = 20); }

// ---- the ribbon, the bow ---------------------------------------------------------------------
RW = 7;
module ribbon() {
    // across the lid's top, both ways
    translate([-RW / 2, -D / 2 - LO, LT - 0.01]) cube([RW, D + 2 * LO, 0.9]);
    translate([-W / 2 - LO, -RW / 2, LT - 0.01]) cube([W + 2 * LO, RW, 0.9]);
    // down the lid's sides, and on down the walls but the front's
    for (a = FACES_WIN) face(a, LO) translate([0, 0, -EMB]) glow_out(0.9, 2) translate([-RW / 2, H + SH * LO]) square([RW, LT - H - SH * LO + 0.9]);
    for (a = [90, 180, 270]) relief(a, 1.0, EMB) translate([-RW / 2, Z0 + 2.2]) square([RW, H - 2.6 - Z0 - 2.2]);
}
// A puffed bow on the lid: two loops and a knot, each a 2D outline raised
// straight up and rounded over in 0.2 mm steps (every step inset, so nothing
// hangs), and two tails lying on the lid.
module puff(h, r = 1.6) {
    linear_extrude(h - r) children();
    for (i = [1 : round(r / 0.2)]) let (t = i * 0.2) translate([0, 0, h - r + t - 0.2]) linear_extrude(0.2) offset(delta = -(r - sqrt(r * r - t * t))) children();
}
module loop2d(s) rotate(s * 22) translate([s * 10, 0]) difference() { scale([10, 6.2]) circle(1, $fn = 64); scale([5.6, 2.6]) circle(1, $fn = 48); }
// It stands on the lid itself, not on the ribbon: its loops run past the
// ribbon's edges, and stood 0.9 up on it they would hang that far over the lid.
module bow() translate([0, 0, LT - 0.01]) {
    for (s = [-1, 1]) puff(5.9) loop2d(s);
    puff(6.9) scale([4.2, 4.8]) circle(1, $fn = 48);
    for (s = [-1, 1]) linear_extrude(1.5) polygon([[s * 1.5, -2], [s * 9, -13], [s * 6.5, -14.5], [s * 4.5, -12], [s * 0.2, -3]]);
}

// ---- the front: door, sign -------------------------------------------------------------------
module arch2d(w, z0, z1) { translate([-w / 2, z0]) square([w, z1 - z0 - w / 2]); translate([0, z1 - w / 2]) circle(w / 2, $fn = 48); }
DZ = Z0 + 2.2;
module door() relief(0, 0.7, EMB) arch2d(10, DZ, DZ + 19);
module door_frame() relief(0, 1.2, EMB) difference() { offset(delta = 1.4) arch2d(10, DZ, DZ + 19); arch2d(10, DZ - 1, DZ + 19); }
module door_heart() face(0) translate([0, 0, 0.69 - 2 * EMB]) glow_out(0.6, 2) heart_at(0, DZ + 12, 4.0);
SV = 38.5;
module sign() sign_board(0, SV, 38, 7.0, EMB);
module letters() sign_letters(0, "CHOCOLATES", SV, 3.6, 1.06, EMB);

// ---- parts ----------------------------------------------------------------------------------
DRIFTS = [[W / 2 + 1, -10, 4, 7, 3.0], [-W / 2 - 1, 12, 4, 6, 2.6], [-15, D / 2 + 1, 7, 3.5, 2.6], [17, -D / 2 - 1, 6, 3.5, 2.4]];
module hollow() room();
module p_glass() panes();
module p_art() intersection() { difference() { art_all(); if (EMB == 0) panes(); } if (EMB == 0) hollow(); else union() { hollow(); panes(); } }
module p_accent() difference() { union() { ribbon(); bow(); letters(); door_heart(); } if (EMB == 0) { panes(); art_all(); } hollow(); }
module p_trim() difference() {
    union() { base(DRIFTS); frames(); piping(); drips(); sign(); door_frame(); }
    if (EMB == 0) { panes(); art_all(); p_accent(); }
    hollow(); mark_cut();
}
module p_roof() difference() { union() { lid(); door(); } hollow(); if (EMB == 0) { p_trim(); p_accent(); } }
module p_body() difference() { block(); hollow(); cuts(); if (EMB == 0) { p_roof(); p_trim(); p_accent(); } }

if (part == "body") p_body();
else if (part == "roof") p_roof();
else if (part == "trim") p_trim();
else if (part == "accent") p_accent();
else if (part == "glass") p_glass();
else if (part == "art") p_art();
else if (part == "all") {
    color("#B9783F") p_body(); color("#5A3825") p_roof(); color("#F4F1EA") p_trim();
    color("#C8314A") p_accent(); color("#F4F1EA") p_glass(); color("#4A2A1A") p_art();
}
