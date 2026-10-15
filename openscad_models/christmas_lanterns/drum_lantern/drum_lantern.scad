// Panorama drum lantern (2026-10-13). Scott picked it from five lantern forms
// (../concepts/lantern_forms.jpg). One unbroken Christmas Eve wraps all the way
// round a glass drum: a village and its church, the village tree, a forest with
// reindeer, a snowman, and Santa's sleigh crossing the moon. Snow lies on the
// rim and hangs over its edge.
//
// Printed in one piece, upright: a hollow shade over a battery LED tealight,
// open at both ends, so it lifts off and goes back down over the light. The
// scene stands 1.6 mm out of 1.3 mm glass; lit, the thicker plastic shows dark
// on the glow, so it reads even printed all in white.
//
// OpenSCAD cannot bend geometry, so the panorama and the snow's drape are
// built flat here (art_flat, drape_flat) and wrapped round the drum by
// wrap_drum.py, which also writes the finished part meshes. Build with
// build.sh.
//
// part = frame | glass | bead | art_flat | drape_flat | all (preview, flat art
//        shown unwrapped behind)
include <../lantern_scenes.scad>
include <../../christmas_village/relief_lib.scad>

part = "all";
// for the gate's one-body union: the bead sinks into the rim and the glass
// keeps its overlap with the rings, so manifold3d welds them (hex lantern,
// 2026-10-13: parts that only touched came out as separate shells)
EMB = 0;
SH = 1.6;           // 58 deg: the hex lantern at 1.2 drew supports (see hex_lantern.scad)
FN = 240;                   // round enough that the wrapped art meets the glass

R    = 40;                  // the glass's outer face
pane = 1.3;
RI   = R - pane;            // 77.4 inside: a 46 mm tealight drops through
AD   = 1.6;                 // the scene, out of the glass
z0   = 7;                   // the base ring's top
H    = 88;                  // the glass
zr   = z0 + H;              // where the rim overhangs the glass
RO   = 3.5;                 // the rim, out past the glass
zt   = zr + 6;              // the rim's top
W    = 2 * PI * R;          // the panorama's length, measured on the glass
HS   = 80;                  // its height
WR   = 2 * PI * (R + RO);   // the rim's outer face, unrolled
DR   = 1.4;                 // the drape, out of the rim

// ---- frame -------------------------------------------------------------------------------
// A low foot inside the ring, 1.6 tall, widens its underside to 10.5 mm for
// the maker's mark: on the ring's own 5.8 mm, and on its curved inside face,
// the slicer propped the letters (2026-10-13). 68 mm stays clear inside.
RF = 34;
module base_ring() difference() {
    union() { cylinder(r = R + 4.5, h = z0 - 2, $fn = FN); translate([0, 0, z0 - 2]) cylinder(r1 = R + 4.5, r2 = R + 2.5, h = 2, $fn = FN); }
    translate([0, 0, -1]) cylinder(r = RF, h = z0 + 2, $fn = FN);
    translate([0, 0, 1.6]) cylinder(r = RI, h = z0 + 2, $fn = FN);
}
// the rim: out RO past the glass, its underside sloped in, SH up per 1 out
module rim() difference() {
    union() {
        translate([0, 0, zr - SH * RO]) cylinder(r1 = R, r2 = R + RO, h = SH * RO, $fn = FN);
        translate([0, 0, zr]) cylinder(r = R + RO, h = zt - zr, $fn = FN);
    }
    translate([0, 0, zr - SH * RO - 1]) cylinder(r = RI, h = zt - zr + SH * RO + 2, $fn = FN);
}
// the maker's mark under the base ring's front, on the foot
// the frame gives up the inlay's 0.02 skin only as a colour part; for the
// gate's union it keeps it, or the two meet face to face and the weld leaves
// zero-volume slivers round the letters (35 extra bodies, 2026-10-15)
module frame() difference() { union() { base_ring(); rim(); } brand_mark(-(RF + R + 4.5) / 2, 4.4); if (EMB == 0) brand_inlay(-(RF + R + 4.5) / 2, 4.4); }
module glass() { glass0(); brand_inlay(-(RF + R + 4.5) / 2, 4.4); }   // the maker's mark prints in the glass's white
module glass0() difference() {
    translate([0, 0, z0 - 0.5]) difference() { cylinder(r = R, h = H + 1, $fn = FN); translate([0, 0, -1]) cylinder(r = RI, h = H + 3, $fn = FN); }
    if (EMB == 0) frame();
}
// a soft roll of snow along the rim's top, out over the drape
module bead() translate([0, 0, zt - EMB]) rotate_extrude($fn = FN) intersection() {
    translate([(RI + R + RO + DR) / 2, 0]) scale([(R + RO + DR - RI) / 2 - 0.2, 2.4]) circle(1, $fn = 48);
    translate([0, 0]) square([R + 10, 5]);
}

// ---- flat parts for wrap_drum.py: x along the face, y up, z out --------------------------
module art_flat() translate([0, 0, 0]) glow_out(AD, 1) intersection() { translate([0.025, 0]) square([W - 0.05, HS]); panorama(W, HS); }
// snow hanging over the rim's edge: a band at its top, scalloped below
module drape2d() let (n = round(WR / 4.6)) intersection() {
    translate([0.025, 0]) square([WR - 0.05, zt - zr]);
    union() {
        translate([0, zt - zr - 2.4]) square([WR, 3]);
        for (i = [0 : n - 1]) let (r = i % 3 == 0 ? 2.4 : i % 3 == 1 ? 1.7 : 2.0)
            translate([(i + 0.5) * WR / n, zt - zr - 2.4]) circle(r, $fn = 24);
    }
}
module drape_flat() glow_out(DR, 1) drape2d();

if (part == "frame") frame();
else if (part == "glass") glass();
else if (part == "bead") bead();
else if (part == "art_flat") art_flat();
else if (part == "drape_flat") drape_flat();
else if (part == "all") {
    color("#2E3440") frame(); color("#F4F1EA") glass(); color("#F4F1EA") bead();
    color("#2E3440") translate([-W / 2, 70, z0]) rotate([90, 0, 0]) art_flat();
}
