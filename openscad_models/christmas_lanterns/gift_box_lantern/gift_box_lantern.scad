// Gift box lantern (2026-10-13). Scott picked it from five lantern forms
// (../concepts/lantern_forms.jpg). A present with glass sides, a Christmas
// scene standing out of each, and a lid tied with a red ribbon and bow.
//
// Two pieces, both printed upright. The box has a floor; a battery LED
// tealight stands in it and the lid lifts off to reach the switch. The lid
// keys onto the box: a band round the box's mouth fits a groove under the lid,
// so it sits square and cannot slide off. Each scene stands 1.6 mm out of
// 1.3 mm glass; lit, the thicker plastic shows dark on the glow, so the scenes
// read even printed all in white.
//
// part = frame | glass | art | lid | ribbon | all (coloured preview, lid on) |
//        plate (preview, the two pieces side by side as printed)
include <../lantern_scenes.scad>
include <../../christmas_village/relief_lib.scad>

part = "all";
// for the gate's one-body unions: the art sinks into the glass, the glass
// keeps its overlap with the frame and the ribbon sinks into the lid, so
// manifold3d welds them (hex lantern, 2026-10-13)
EMB = 0;
SH = 1.2;
$fa = 4; $fs = 0.4;

P    = 35;                  // the glass's outer face, from the centre
pane = 1.3;
PI_  = P - pane;            // 67.4 inside
AD   = 1.6;                 // the scenes, out of the glass
z0   = 6;                   // the base band's top
fl   = 2.4;                 // the floor
H    = 58;                  // the glass
zr   = z0 + H;              // the rail's top: the lid sits here
RO   = 2.8;                 // the base band, the rail and the lid, out past the glass
PR   = 3.2;                 // the corner posts' radius
W    = 60;  HS = 52;        // a scene: between the posts, under the rail

// the band round the box's mouth, and the lid's groove that takes it
BI   = PI_ - 0.8;  BO = P + 0.2;  BH = 5;
CL   = 0.25;                // clearance each side of the band
LH   = 14;                  // the lid
LR   = 3;                   // its corners' radius

module rsq(a, h, r = 0.01) linear_extrude(h) offset(r = r) square(2 * a - 2 * r, center = true);
function fa(k) = 90 * k;    // faces at 0, 90, 180, 270; the front (k = 3) faces -y
module on_face(a, d) rotate([0, 0, a]) translate([d, 0, 0]) rotate([90, 0, 90]) children();

// ---- the box -----------------------------------------------------------------------------
module base() difference() {
    union() { rsq(P + RO, z0 - 1.5, LR); translate([0, 0, z0 - 1.5]) hull() { rsq(P + RO, 0.01, LR); translate([0, 0, 1.5]) rsq(P + RO - 1.5, 0.01, LR); } }
    translate([0, 0, fl]) rsq(PI_, z0);
}
// down to the plate: started at the glass's foot, each corner hung over the
// base's bevel and the slicer propped it (2026-10-13)
module posts() for (x = [-1, 1], y = [-1, 1]) translate([x * (P - pane / 2), y * (P - pane / 2), 0])
    cylinder(r = PR, h = zr, $fn = 24);
// the rail: out RO past the glass, its underside sloped in, SH up per 1 out
module rail() difference() {
    hull() { translate([0, 0, zr - SH * RO - 2]) rsq(P, 0.01); translate([0, 0, zr - 2]) rsq(P + RO, 2, LR); }
    translate([0, 0, zr - SH * RO - 3]) rsq(PI_, 10);
}
// the band the lid keys onto; its inner face sloped where it steps in past the glass
module band() difference() {
    union() { translate([0, 0, zr - SH * 0.8]) hull() { rsq(BO, 0.01); translate([0, 0, SH * 0.8]) rsq(BO, 0.01); }
              translate([0, 0, zr - 0.01]) rsq(BO, BH + 0.01); }
    hull() { translate([0, 0, zr - SH * 0.8 - 0.01]) rsq(PI_, 0.01); translate([0, 0, zr]) rsq(BI, BH + 1); }
}
// the maker's mark under the middle of the floor
module frame() difference() { union() { base(); posts(); rail(); band(); } brand_mark(0, 7); brand_inlay(0, 7); }
module glass() { glass0(); brand_inlay(0, 7); }   // the maker's mark prints in the glass's white
module glass0() difference() {
    translate([0, 0, z0 - 0.5]) difference() { rsq(P, H); translate([0, 0, -1]) rsq(PI_, H + 2); }
    if (EMB == 0) frame();
}
module art() for (k = [0 : 3]) on_face(fa(k), P + 0.01 - EMB) translate([-W / 2, z0])
    glow_out(AD, 1) intersection() { square([W, HS]); landscape(k, W, HS); }

// ---- the lid, built standing on the plate (z = 0 is its underside) --------------------------
module lid() difference() {
    rsq(P + RO, LH, LR);
    translate([0, 0, -1]) difference() { rsq(BO + CL, BH + 0.3 + 1); rsq(BI - CL, BH + 3); }
}
RW = 10;                    // the ribbon's width
RT = 1.2;                   // and how far it stands off the lid
module ribbon() {
    // round the lid's sides and over its top; on the sides it runs down to the
    // plate, so nothing overhangs
    for (r = [0, 90]) rotate([0, 0, r]) difference() {
        translate([-RW / 2, -(P + RO + RT), 0]) cube([RW, 2 * (P + RO + RT), LH + RT]);
        translate([-RW, -(P + RO) + EMB, -1]) cube([2 * RW, 2 * (P + RO) - 2 * EMB, LH + 1 - EMB]);
    }
    translate([0, 0, LH + RT - 0.01 - EMB]) bow();
}
// the bow: two standing loops-and-knot plates, crossed, so four loops show
// from above. The loops climb steeply enough that their undersides print, and
// their holes peak at 60 deg.
// Each loop rises from a flat foot, not a round one: a round foot curled under
// itself at the plate, and the slicer propped every loop (2026-10-13).
module bow_plate() rotate([90, 0, 0]) linear_extrude(3.4, center = true) {
    for (m = [0, 1]) mirror([m, 0]) difference() {
        hull() { translate([0, 0]) square([5, 0.1]); translate([8.2, 14]) circle(4.8); }
        translate([7.6, 13]) hull() { circle(2.0); translate([0, 4.0]) circle(0.01); }
    }
    translate([-4, 0]) square([8, 2]);
}
module bow() scale(1.3) {
    for (r = [45, 135]) rotate([0, 0, r]) bow_plate();
    cylinder(r = 4.2, h = 6.5, $fn = 32);
    translate([0, 0, 6.5]) scale([1, 1, 0.6]) sphere(4.2, $fn = 32);
}

// ---- parts ---------------------------------------------------------------------------------
module the(p) {
    if (p == "frame") frame();
    else if (p == "glass") glass();
    else if (p == "art") art();
    else if (p == "lid") lid();
    else if (p == "ribbon") ribbon();
}
GREEN = "#2F6B45"; WHITE = "#F4F1EA"; RED = "#C62F3A";
if (part == "all") {
    color(GREEN) frame(); color(WHITE) glass(); color(GREEN) art();
    translate([0, 0, zr]) { color(GREEN) lid(); color(RED) ribbon(); }
} else if (part == "plate") {
    color(GREEN) frame(); color(WHITE) glass(); color(GREEN) art();
    translate([2 * (P + RO) + 12, 0, 0]) { color(GREEN) lid(); color(RED) ribbon(); }
} else the(part);
