// Hex carriage lantern (2026-10-13). Scott picked it from five lantern forms
// (../concepts/lantern_forms.jpg). Six glass panels between corner posts, a
// Christmas scene standing out of each, a pointed roof with snow on its crown,
// a red bow on the front slope and a hanging ring.
//
// Printed in one piece, upright. It is a hollow shade over a battery LED
// tealight: the base is open, so it lifts off and goes back down over the
// light. Every scene line stands 1.6 mm out of 1.3 mm glass; lit, the thicker
// plastic shows dark on the glow, so the scenes read even printed all in white.
//
// part = frame | glass | art | snow | bow | all (coloured preview) | union
include <../lantern_scenes.scad>
include <../../christmas_village/relief_lib.scad>

part = "all";
// for the gate's one-body union: each part sinks this far into the one it
// stands on, so manifold3d welds them instead of leaving touching shells
// (2026-10-13: the touching parts came out as 60 bodies)
EMB = 0;
SH = 1.2;          // relief undersides climb 1.2 per 1 out (relief_lib)
$fa = 4; $fs = 0.4;

// ---- size --------------------------------------------------------------------------------
AP   = 32;                  // the glass's outer face, from the axis
pane = 1.3;                 // the glass: thin enough to glow
API  = AP - pane;           // inside: 61.4 across the flats, a 46 mm tealight drops through
SIDE = 2 * AP * tan(30);
AD   = 1.6;                 // the scenes, out of the glass
z0   = 8;                   // the plinth's top
H    = 84;                  // the glass
zr   = z0 + H;              // where the top rail overhangs the glass
RO   = 3.5;                 // the rail and the roof's eave, out past the glass
zt   = zr + 5;              // the rail's top, the roof's foot
RA   = AP + RO;             // the roof at its foot
RH   = 44;                  // the roof's height
TH   = atan(RA / RH);       // its faces lean back this far: 38.5 deg, so the
                            // underside prints without support
LF   = sqrt(RA * RA + RH * RH);   // the roof's slope length, foot to apex
AC   = 5;                   // the roof stops here, under the collar
zc   = zt + RH * (1 - AC / RA);
W    = 29;  HS = 76;        // a scene: inside the posts, under the rail

function cr(a) = a / cos(30);   // a hexagon's corner radius from its apothem
module hex(a, h) cylinder(r = cr(a), h = h, $fn = 6);
module hex_frustum(a0, a1, h) cylinder(r1 = cr(a0), r2 = cr(a1), h = h, $fn = 6);
// faces point at 30 + 60k deg; the front (k = 4) faces -y
function fa(k) = 30 + 60 * k;
module on_face(a, d, z = 0) rotate([0, 0, a]) translate([d, 0, z]) rotate([90, 0, 90]) children();
// on a roof face: x along it, y up its slope from the foot, z out of it
module on_roof(a) rotate([0, 0, a]) translate([RA, 0, zt]) rotate([0, -TH, 0]) rotate([90, 0, 90]) children();
module sector(a) translate([0, 0, -1]) linear_extrude(400)
    polygon([[0, 0], 300 * [cos(a - 30), sin(a - 30)], 300 * [cos(a + 30), sin(a + 30)]]);

// ---- frame -------------------------------------------------------------------------------
module plinth() difference() {
    union() { hex(AP + 4.5, z0 - 2); translate([0, 0, z0 - 2]) hex_frustum(AP + 4.5, AP + 2.5, 2); }
    translate([0, 0, -1]) hex(API, z0 + 2);
}
// trimmed flush with the glass inside: whole, each post stood 2 mm into the
// hollow over the open base, and the slicer propped it from the plate
module posts() difference() {
    for (k = [0 : 5]) rotate([0, 0, 60 * k]) translate([cr(AP - pane / 2), 0, z0 - 0.5]) cylinder(r = 2.8, h = H + 1, $fn = 24);
    translate([0, 0, -1]) hex(API, zt + 2);
}
// the top rail: out RO past the glass, its underside sloped in, SH up per 1 out
module rail() difference() {
    hull() { translate([0, 0, zr - SH * RO]) hex(AP, 0.01); translate([0, 0, zr]) hex(AP + RO, zt - zr); }
    translate([0, 0, zr - SH * RO - 1]) hex(API, zt - zr + SH * RO + 2);
}
// a hollow pointed roof, its faces parallel inside and out (3.5 thick), open
// below into the lantern; cut flat under the collar
module roof() difference() {
    translate([0, 0, zt]) hex_frustum(RA, AC, zc - zt);
    translate([0, 0, zt - 0.01]) cylinder(r1 = cr(API), r2 = 0, h = API * RH / RA, $fn = 6);
}
// the collar: out 1.4 over the snow, its underside sloped; a cap; the ring
module crown() {
    translate([0, 0, zc - SH * 1.6]) hex_frustum(AC, AC + 1.6, SH * 1.6);
    translate([0, 0, zc]) hex_frustum(AC + 1.6, AC + 1.0, 2.6);
    // its top wide enough for the ring's foot to stand on whole
    translate([0, 0, zc + 2.6]) hex_frustum(AC + 1.0, 4.4, 2.0);
    translate([0, 0, zc + 4.4]) hanging_ring();
}
// a flat ring standing edge on, its hole peaked at 60 deg so its crown prints
module hanging_ring() rotate([90, 0, 0]) linear_extrude(4, center = true) difference() {
    hull() { translate([-3.2, 0]) square([6.4, 0.1]); translate([0, 9]) circle(7); }
    translate([0, 9]) hull() { circle(3.4); translate([0, 3.4 * 2]) circle(0.01); }
}
module frame() { plinth(); posts(); rail(); roof(); crown(); }

// ---- glass and its scenes ---------------------------------------------------------------
module glass() difference() {
    translate([0, 0, z0 - 0.5]) difference() { hex(AP, H + 1); translate([0, 0, -1]) hex(API, H + 3); }
    if (EMB == 0) frame();
}
module art() for (k = [0 : 5]) on_face(fa(k), AP + 0.01 - EMB) translate([-W / 2, z0])
    glow_out(AD, 1) intersection() { square([W, HS]); portrait(k, W, HS); }

// ---- snow on the crown, the bow on the front ---------------------------------------------
V0 = LF * 0.5;              // the snow's lower edge, up the slope
module snow2d(k) let (wv = SIDE * RA / AP * (1 - V0 / LF) + 8, n = round(wv / 5.2)) union() {
    translate([-wv / 2, V0]) square([wv, LF]);
    for (i = [0 : n]) let (u = -wv / 2 + i * wv / n, r = (i + k) % 3 == 0 ? 3.0 : (i + k) % 3 == 1 ? 2.2 : 1.6)
        translate([u, V0]) circle(r, $fn = 24);
}
module snow() difference() {
    for (k = [0 : 5]) intersection() { sector(fa(k)); on_roof(fa(k)) translate([0, 0, 0.01 - EMB]) glow_out(1.4, 1) snow2d(k); }
    if (EMB == 0) frame();
    translate([0, 0, zc]) cylinder(r = 50, h = 50);
}
module bow2d() {
    for (m = [0, 1]) mirror([m, 0]) {
        difference() {
            hull() { translate([1.6, 0]) circle(1.6); translate([6.4, 2.6]) scale([1.3, 1]) circle(2.6); }
            hull() { translate([3.6, 0.9]) circle(0.6); translate([6.2, 2.4]) scale([1.3, 1]) circle(1.0); }
        }
        polygon([[-1.2, -0.6], [1.8, -0.8], [5.2, -10], [3.4, -9.0], [2.4, -11]]);
    }
    circle(2.2);
}
module bow() on_roof(fa(4)) translate([0, LF * 0.27, 0.01 - EMB]) glow_out(1.4, 1) bow2d();

// ---- parts ---------------------------------------------------------------------------------
module the(p) {
    if (p == "frame") frame();
    else if (p == "glass") glass();
    else if (p == "art") art();
    else if (p == "snow") snow();
    else if (p == "bow") bow();
}
PARTS = ["frame", "glass", "art", "snow", "bow"];
COLS  = ["#2E3440", "#F4F1EA", "#2E3440", "#F4F1EA", "#C62F3A"];
if (part == "all") for (i = [0 : len(PARTS) - 1]) color(COLS[i]) the(PARTS[i]);
else if (part == "union") union() for (p = PARTS) the(p);
else the(part);

