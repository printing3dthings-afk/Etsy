// Village mini-lantern ornaments (2026-10-21), a set of six. Scott picked the
// mini-lantern form (4E) from five: a small hex carriage lantern, the shape of
// the shop's hex lantern, with a building from the Christmas village raised on
// its glass, so the ornaments match the village and the lanterns both.
//
// Solid, not a shade: white glass, a slate frame and pointed roof, snow on the
// roof's crown, a red bow, and a ring to hang it by. The front and back panels
// carry the design's building; the four between carry a snowflake and stars.
// The maker's mark is inlaid in the plinth's underside in the glass's white.
//
// Printed upright, as it sits in the file. The rail's underside and the roof
// lean back within the support angle (as on the hex lantern); the scenes stand
// out of the glass with their undersides climbing 1.6 per 1 out.
//
// design = 1..6   part = frame | glass | art | snow | bow | union | all
include <../../christmas_lanterns/lantern_scenes.scad>
include <../../christmas_village/relief_lib.scad>

design = 1;
part = "all";
EMB = 0;            // for the gate's union: sink each part this far into its neighbour
SH = 1.6;
$fa = 4; $fs = 0.3;

// ---- size --------------------------------------------------------------------------------
AP   = 15;                  // the glass's face, from the axis: 30 mm across the flats
z0   = 5;                   // the plinth's top
H    = 34;                  // the glass
zr   = z0 + H;
RO   = 2.2;                 // the rail and the roof's eave, out past the glass
zt   = zr + 3;              // the rail's top, the roof's foot
RA   = AP + RO;
RH   = 20;                  // the roof's height: faces lean back 41 deg
TH   = atan(RA / RH);
LF   = sqrt(RA * RA + RH * RH);
AC   = 3.2;                 // the roof stops here, under the collar
zc   = zt + RH * (1 - AC / RA);
AD   = 1.0;                 // the scenes, out of the glass
W    = 12;  HS = 31;        // a scene: inside the posts, under the rail

function cr(a) = a / cos(30);
module hex(a, h) cylinder(r = cr(a), h = h, $fn = 6);
module hex_frustum(a0, a1, h) cylinder(r1 = cr(a0), r2 = cr(a1), h = h, $fn = 6);
function fa(k) = 30 + 60 * k;        // faces point here; the front (k = 4) faces -y
module on_face(a, d, z = 0) rotate([0, 0, a]) translate([d, 0, z]) rotate([90, 0, 90]) children();
module on_roof(a) rotate([0, 0, a]) translate([RA, 0, zt]) rotate([0, -TH, 0]) rotate([90, 0, 90]) children();
// each face's snow runs 1 deg past the hip so the two weld: at this radius the
// hex lantern's 0.05 deg overlapped 0.01 mm and left the hips open (2026-10-21)
module sector(a) translate([0, 0, -1]) linear_extrude(200)
    polygon([[0, 0], 300 * [cos(a - 31), sin(a - 31)], 300 * [cos(a + 31), sin(a + 31)]]);

// ---- frame -------------------------------------------------------------------------------
module plinth() { hex(AP + 2.5, z0 - 1.5); translate([0, 0, z0 - 1.5]) hex_frustum(AP + 2.5, AP + 1.0, 1.5); }
module posts() for (k = [0 : 5]) rotate([0, 0, 60 * k]) translate([cr(AP) - 0.6, 0, z0 - 0.5]) cylinder(r = 1.8, h = H + 1, $fn = 24);
module rail() hull() { translate([0, 0, zr - SH * RO]) hex(AP, 0.01); translate([0, 0, zr]) hex(AP + RO, zt - zr); }
module roof() translate([0, 0, zt - 0.01]) hex_frustum(RA, AC, zc - zt + 0.01);
module hanging_ring() rotate([90, 0, 0]) linear_extrude(3.2, center = true) difference() {
    hull() { translate([-2.6, 0]) square([5.2, 0.1]); translate([0, 6.4]) circle(4.8); }
    translate([0, 6.4]) hull() { circle(2.3); translate([0, 2.3 * 2]) circle(0.01); }   // peaked at 60 deg
}
module crown() {
    translate([0, 0, zc - 0.01]) hex_frustum(AC, AC * 0.8, 1.6);
    translate([0, 0, zc + 1.4]) hanging_ring();
}
MARK_H = 4.4;
module frame() difference() { union() { plinth(); posts(); rail(); roof(); crown(); } brand_mark(0, MARK_H); if (EMB == 0) brand_inlay(0, MARK_H); }

// ---- glass and its scenes ----------------------------------------------------------------
module glass() {
    difference() { translate([0, 0, z0 - 0.5]) hex(AP, H + 1); if (EMB == 0) frame(); }
    brand_inlay(0, MARK_H);       // the mark prints in the glass's white
}
// the six buildings, each drawn to stand in a W x HS panel on a strip of snow
module building(n) {
    if (n == 1) translate([4.9, 2.4]) church(6.2, 8.2);       // its tower (4) to the left of x = 0: 10.2 wide, centred
    if (n == 2) translate([1.2, 2.4]) house(9.6, 9.5, 7.5);
    if (n == 3) translate([W / 2, 2.4]) clock_tower(6.4, 20);
    if (n == 4) translate([W / 2, 2.4]) { tree(23); translate([0, 23.2]) star(2.6, 1.3); }
    if (n == 5) translate([0.8, 2.4]) toy_shop();
    if (n == 6) translate([W / 2, 2.4]) well();
    ground(W, 2.4, 1.0, 2);
}
module clock_tower(w, h) difference() {
    union() {
        translate([-w / 2, 0]) square([w, h]);
        translate([0, h]) polygon([[-w / 2 - 1, 0], [w / 2 + 1, 0], [0, w * 1.1]]);
    }
    translate([0, h * 0.72]) difference() { circle(w * 0.3); circle(0.8); }
    translate([0, -0.1]) arch_hole(w * 0.38, h * 0.3);
}
module toy_shop() difference() {
    union() {
        house(6.6, 8, 5, false);
        translate([7.6, 0]) square([3.4, 13]);
        translate([7.6, 13]) polygon([[-0.7, 0], [4.1, 0], [1.7, 5.5]]);
    }
    translate([9.3, 7.5]) arch_hole(1.8, 3.4);
}
module well() {
    translate([-5, 0]) square([10, 6]);
    for (s = [-1, 1]) translate([s * 4 - SW / 2, 5]) square([SW, 9]);
    translate([0, 13.6]) polygon([[-6.4, 0], [6.4, 0], [0, 5.6]]);
}
module filler() { translate([W / 2, HS * 0.52]) flake(5.2); sky(W, HS, [[0.2, 0.9], [0.8, 0.84], [0.25, 0.16], [0.78, 0.2]], 1.9); }
module scene(k) intersection() {
    square([W, HS]);
    if (k == 4 || k == 1) building(design); else filler();
}
module art() for (k = [0 : 5]) on_face(fa(k), AP + 0.01 - EMB) translate([-W / 2, z0])
    glow_out(AD, 1) scene(k);

// ---- snow on the crown, a bow on the front ------------------------------------------------
V0 = LF * 0.42;
// the drips keep 3 mm in from the hips: where two faces' end drips met
// there, they touched along a line and left the snow open (2026-10-21)
module snow2d(k) let (wf = 2 * RA * tan(30) * (1 - V0 / LF), wv = wf + 6, n = 2) union() {
    translate([-wv / 2, V0]) square([wv, LF]);
    for (i = [0 : n]) let (u = -(wf - 6.5) / 2 + i * (wf - 6.5) / n, r = (i + k) % 2 == 0 ? 1.8 : 1.4)
        translate([u, V0]) circle(r, $fn = 24);
}
module snow() difference() {
    for (k = [0 : 5]) intersection() { sector(fa(k)); on_roof(fa(k)) translate([0, 0, 0.01 - EMB]) glow_out(1.0, 1) snow2d(k); }
    if (EMB == 0) frame();
    translate([0, 0, zc]) cylinder(r = 50, h = 50);
}
module bow2d() {
    for (m = [0, 1]) mirror([m, 0]) {
        hull() { translate([1.2, 0]) circle(1.2); translate([4.2, 1.7]) scale([1.3, 1]) circle(1.7); }
        polygon([[-0.9, -0.5], [1.4, -0.6], [3.6, -6.2], [2.3, -5.6], [1.6, -7]]);
    }
    circle(1.6);
}
module bow() on_roof(fa(4)) translate([0, LF * 0.18, 0.01 - EMB]) glow_out(1.0, 1) bow2d();

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
