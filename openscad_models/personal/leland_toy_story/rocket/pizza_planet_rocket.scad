// Pizza Planet rocket night light -- for Leland's 2nd birthday (Scott,
// 2026-10-24). PERSONAL, NOT FOR SALE: Toy Story is Disney/Pixar's, so this
// never goes in the shop, the catalogue or the public viewer.
//
// A white rocket with white fins on a blue pedestal lettered PIZZA PLANET,
// red nose and bands, six portholes ringed by V-grooves, and a yellow ringed
// planet on the tip. A battery LED tealight inside lights it: the 1.6 mm
// white body glows evenly, and each groove glows a little brighter.
//
// FOR A TWO-YEAR-OLD:
//  * battery tealights run on a coin cell, which is dangerous swallowed. The
//    tealight stands on a base plate held by TWO SCREWS (M3 x 10 self-tapping,
//    or #4 x 3/8"), the way real toy battery doors are closed: nothing to
//    twist or pop off by hand.
//  * nothing thin sticks out: fins 6 mm, the planet's ring on a solid cone,
//    the portholes grooved into the body, nothing to pick at.
//  * a wide, low base (90 mm across for 197 mm of height) so it doesn't tip.
//
// Prints standing up, no supports: every underside climbs at 40 deg from
// upright or steeper (detail_calibration/DETAIL_STANDARD.md rule 7).
//
// PARTS (one print, four filaments) + the base plate (printed on its own):
//   white  the body and fins (red_fins = true makes the fins red: 24 h on the AMS, not 8)
//   red    nose, bands
//   blue   pedestal (blue_rims = true gives the portholes blue rings instead of grooves)
//   yellow letters, the planet and its ring
// priority yellow > blue > red > white

$fa = 3;  $fs = 0.4;
part = "all";

SH = 1.2;                            // undersides climb 1.2 up per 1 out: 40 deg from upright

// ---- pedestal and base plate ---------------------------------------------------------------------
PR = 45;  PH = 16;  pch = 1.6;       // radius, height, chamfer on its top edge
bore0 = 29;  bore1 = 27 - 1.6;          // the light's way up: wide at the bottom, the body's bore at PH
plate_t = 3;                         // the base plate under it
scr_r = 36;  scr_a = [0, 180];       // screw positions

// ---- body and nose ---------------------------------------------------------------------------------
wall = 1.6;                          // four beads: the whole body glows evenly
BZ0 = PH;  BZ1 = 136;  NZ1 = 182;
// bulges from 27 to 30.4, narrows to 25 under the nose; steepest 6 deg from upright
function rb(z) = let (t = (z - BZ0) / (BZ1 - BZ0)) 27 + 3.4 * sin(180 * min(1, 1.25 * t)) - 2.0 * max(0, t - 0.55) / 0.45;
// a pointed ogive, 2.4 at the tip for the planet's neck; steepest 36 deg
function rn(z) = let (t = (z - BZ1) / (NZ1 - BZ1)) (rb(BZ1) - 2.4) * (1 - pow(t, 1.5)) + 2.4;

function body_pts() = concat([[0, BZ0]], [for (z = [BZ0 : 1 : BZ1]) [rb(z), z]], [[0, BZ1]]);
function nose_pts() = concat([[0, BZ1 - 0.5], [rb(BZ1), BZ1 - 0.5]], [for (z = [BZ1 : 0.5 : NZ1]) [rn(z), z]], [[0, NZ1]]);
// the hollow, 2.4 in from the outside all the way up, its roof a 40 deg cone
cav_top = NZ1 - 8;
function cav_pts() = let (re = rn(cav_top) - wall) concat(
    [[0, -1], [bore0, -1], [bore0, 0.6], [bore1, PH]],
    [for (z = [PH : 1 : BZ1]) [rb(z) - wall, z]],
    [for (z = [BZ1 : 0.5 : cav_top]) [rn(z) - wall, z]],
    [[0, cav_top + re * SH]]);

module pedestal_raw() rotate_extrude($fn = 180) polygon([[0, 0], [PR, 0], [PR, PH - pch], [PR - pch, PH], [0, PH]]);
module body_raw() rotate_extrude($fn = 180) polygon(body_pts());
module nose_raw() rotate_extrude($fn = 180) polygon(nose_pts());
module cavity() {
    rotate_extrude($fn = 180) polygon(cav_pts());
    // pilot holes for the plate's screws, pointed tops
    for (a = scr_a) rotate(a) translate([scr_r, 0, -1]) { cylinder(d = 2.5, h = 11, $fn = 24); translate([0, 0, 11]) cylinder(d1 = 2.5, d2 = 0, h = 1.5, $fn = 24); }
}

// ---- fins: three, 6 thick, standing on the pedestal --------------------------------------------
fin_t = 6;  FIN_A = [90, 210, 330];  // the front (-y, 270) is clear for the big porthole
module fin2d() union() {
    offset(r = 2.5) offset(delta = -2.5) polygon([[20, PH], [PR - 3, PH], [PR - 3, PH + 14], [rb(80) - 1, 82], [20, 82]]);
    // the foot square: rounded, its outer corner was a small overhang on the pedestal
    translate([20, PH]) square([PR - 3 - 20, 4]);
}
module fins_raw() for (a = FIN_A) rotate(a) rotate([90, 0, 0]) translate([0, 0, -fin_t / 2]) linear_extrude(fin_t) fin2d();

// ---- red bands: 2.4 tall, 0.8 proud, each underside climbing 39 deg ----------------------------
BANDS = [36.0, 118.0];
module band(z) rotate_extrude($fn = 180)
    polygon([[rb(z) - 1, z - 1.0], [rb(z), z - 1.0], [rb(z) + 0.8, z], [rb(z) + 0.8, z + 2.4], [rb(z) - 1, z + 2.4]]);

// ---- placing on the body: local x across, local y up, local z out --------------------------------
module at_face(a, z) rotate(a) translate([rb(z) - 3, 0, z]) rotate([90, 0, 90]) children();
module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// the workshop's relief: each depth's outline shifted up by SH x depth, filled
// down behind, so no underside of it hangs (Christmas village, 2026-10-12)
module relief_up(d0, d1, sh = SH) difference() {
    intersection() {
        translate([0, 0, d0]) linear_extrude(d1 - d0) minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
        shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
    }
    if ($children > 1) {
        translate([0, 0, d0 - 0.1]) linear_extrude(d1 - d0 + 0.2) children(1);
        shear_up(sh) translate([0, 0, d0 - 0.1]) linear_extrude(d1 - d0 + 0.2) children(1);
    }
}
// the outside of the body pushed out by d, as a solid to clip against
module envelope(d) rotate_extrude($fn = 180) polygon(concat([[0, BZ0 - 2]], [for (z = [BZ0 - 2 : 1 : BZ1 + 2]) [rb(min(max(z, BZ0), BZ1)) + d, z]], [[0, BZ1 + 2]]));

// ---- portholes: [angle, z, radius] ---------------------------------------------------------------
PORTS = [[270, 96, 9.0], [30, 96, 7.0], [150, 96, 7.0], [270, 58, 6.0], [30, 58, 5.0], [150, 58, 5.0]];
rim_w = 3.2;  rim_d = 0.8;
// a blue ring 3.2 wide, inlaid 1.2 deep and flush with the body. Raised and
// built with relief_up, the shear (made for flat walls) slid each ring up off
// the curved body and left a crescent (2026-10-24); flush, there is no
// underside at all, and nothing for small fingers to pick at.
module rim(p) intersection() {
    at_face(p[0], p[1]) translate([0, 0, -1]) linear_extrude(10) difference() { circle(r = p[2] + rim_w, $fn = 96); circle(r = p[2], $fn = 96); }
    difference() { envelope(0.01); envelope(-rim_d); }
}
// the same ring cut into the white body as a V: straight in, the groove's
// ceiling (each ring's top, each porthole's bottom edge) hung flat 0.8 deep
// and the slicer propped all six from the plate (25,806 support moves,
// 2026-10-24). Each 0.05 of depth narrows the ring by rim_k x 0.05 on both
// edges, so the ceiling climbs at atan(1 / rim_k) = 34 deg from upright.
rim_k = 1.5;  rim_step = 0.05;
module rim_groove(p) for (i = [0 : round(rim_d / rim_step) - 1]) let (d0 = i * rim_step, d1 = d0 + rim_step) intersection() {
    at_face(p[0], p[1]) translate([0, 0, -1]) linear_extrude(10) difference() { circle(r = p[2] + rim_w - rim_k * d1, $fn = 96); circle(r = p[2] + rim_k * d1, $fn = 96); }
    difference() { envelope(0.01 - d0); envelope(-d1); }
}
// NOT USED (2026-10-24): the wall thinned to 1.0 behind each porthole. With
// a teardrop roof at 38.7 deg the slicer propped all six pockets from the
// plate (15,600 support moves); at 27 deg it still did, with columns ending at
// each pocket's circle top, and the cause was not found. The whole body is
// 1.6 thick instead, so it glows evenly and the blue rings frame the ports.
module glow_pocket(p) intersection() {
    at_face(p[0], p[1]) translate([0, 0, -6]) linear_extrude(12)
        hull() { circle(r = p[2] - 0.4, $fn = 64); translate([0, (p[2] - 0.4) * 2.2]) circle(r = 0.01); }
    envelope(-1.0);
}

// ---- lettering round the pedestal's front, raised 1.0, built as a climb ------------------------
txt = "PIZZA PLANET";  t_size = 8.0;  t_z = 7.6;
// each letter's advance as a fraction of the size (Fredoka SemiBold, by eye
// from its outlines); evenly spaced, the I sat in a gap
t_w = [0.66, 0.30, 0.62, 0.62, 0.72, 0.36, 0.66, 0.56, 0.72, 0.76, 0.62, 0.60];
t_gap = 1.4;   // mm between letters: at the outlines' own widths they ran together
function t_pos(i) = i == 0 ? 0 : t_pos(i - 1) + (t_w[i - 1] + t_w[i]) / 2 * t_size + t_gap;
t_len = t_pos(len(txt) - 1);
t_font = "Fredoka:style=SemiBold";
// Technique 81: raised letters on an upright face as a climb. Each fifth of
// the depth keeps only what has letter under it by l_sh x that depth (the
// Victorian workshop's letters_up). With its SH 1.2 in 0.2 steps the climb
// rounded to exactly 45 deg per slice and the slicer propped every letter:
// 5,686 support moves (2026-10-24). 1.5 in 0.1 steps is 34 deg.
// Built in steps, every step left a flat ledge 0.2 deep under the stroke,
// which the slicer reads layer by layer as 45 deg: still 5,686 moves with
// finer steps. A smooth shear instead, as relief_up: each stroke's underside
// one plane climbing 34 deg (the pedestal is 45 in radius, near flat across
// a letter).
l_sh = 1.5;
module letters_up(h, n) relief_up(-1.0, h, l_sh) children();
module letters_raw() for (i = [0 : len(txt) - 1]) if (txt[i] != " ")
    let (a = 270 + (t_pos(i) - t_len / 2) / PR * 180 / PI)
        rotate(a) translate([PR, 0, t_z]) rotate([90, 0, 90]) letters_up(1.0, 5)
            text(txt[i], size = t_size, font = t_font, halign = "center", valign = "center");

// ---- the planet on the tip: a ball over a ringed cone ----------------------------------------
PL = NZ1 + 6;
module planet_raw() {
    // neck and ring in one profile: the ring's underside climbs 34 deg out of the nose
    rotate_extrude($fn = 96) polygon([[0, NZ1 - 6], [2.6, NZ1 - 6], [10.5, PL - 0.4], [10.5, PL + 1.6], [5.0, PL + 2.4], [0, PL + 2.4]]);
    translate([0, 0, PL]) intersection() { sphere(r = 6, $fn = 64); translate([-6, -6, -1.5]) cube([12, 12, 12]); }
}

// ---- parts -------------------------------------------------------------------------------------
// the planet is the ring and the ball; the cone under them is the nose's tip
module yellow_raw() { letters_raw(); intersection() { planet_raw(); translate([-20, -20, PL - 2.6]) cube([40, 40, 20]); } }
// blue_rims = false cuts each porthole ring 0.8 into the white body instead:
// no colour change through the middle of the rocket, and the thinner wall in
// the groove glows brighter when lit
blue_rims = false;  // Scott, 2026-10-24: grooved ports (with white fins: 85 colour changes, not 611)
module blue_raw()   { pedestal_raw(); if (blue_rims) for (p = PORTS) rim(p); }
// red_fins = false prints the fins in the body's white: on the AMS, red fins
// beside a white body are a colour change on every layer from 16 to 82 mm
red_fins = false;   // Scott, 2026-10-24: white fins, 7h 53m instead of 24h on the AMS
module red_raw()    { nose_raw(); if (red_fins) fins_raw(); for (z = BANDS) band(z); planet_raw(); }
module white_raw()  { body_raw(); if (!red_fins) fins_raw(); }

module yellow_part() difference() { yellow_raw(); cavity(); }
module blue_part()   difference() { blue_raw(); yellow_raw(); cavity(); }
module red_part()    difference() { red_raw(); yellow_raw(); blue_raw(); cavity(); }
pockets = false;   // see glow_pocket: the porthole pockets propped the print; the thin wall glows instead
module white_part()  difference() { white_raw(); red_raw(); yellow_raw(); blue_raw(); cavity(); if (pockets) for (p = PORTS) glow_pocket(p); if (!blue_rims) for (p = PORTS) rim_groove(p); }

// the base plate: as wide as the pedestal, two countersunk screw holes, and a
// ring to seat the tealight (39.5 inside: standard tealights are 38-39)
module plate() difference() {
    union() {
        cylinder(r = PR, h = plate_t, $fn = 180);
        translate([0, 0, plate_t]) difference() { cylinder(r = 22.5, h = 2.0, $fn = 120); translate([0, 0, -1]) cylinder(d = 39.5, h = 4, $fn = 120); }
    }
    for (a = scr_a) rotate(a) translate([scr_r, 0, -1]) { cylinder(d = 3.4, h = 10, $fn = 24); cylinder(d1 = 7.4, d2 = 3.4, h = 2.0 + 1, $fn = 24); }
}

if      (part == "white")  white_part();
else if (part == "red")    red_part();
else if (part == "blue")   blue_part();
else if (part == "yellow") yellow_part();
else if (part == "plate")  plate();
else if (part == "union")  union() { white_part(); red_part(); blue_part(); yellow_part(); }
else if (part == "all") {
    color("#F4F1EA") white_part();
    color("#C8312B") red_part();
    color("#2B5FA8") blue_part();
    color("#F2C230") yellow_part();
    color("#2B5FA8") translate([0, 0, -plate_t - 6]) plate();
}
