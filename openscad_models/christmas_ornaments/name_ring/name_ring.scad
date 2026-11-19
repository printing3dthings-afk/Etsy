// Openwork Name Ornament (2026-11-18). Scott picked form 1 of five after the domed
// name ornament's inlaid name printed lumpy on its curve ("Jessee", 2026-11-18): a
// flat open ring with the name across the middle on its own outline, held to the
// rim by a bar, a star, pine sprigs and a berry swag, so the tree's lights show
// through. Our own motifs (star, pine, berries), not the snowflakes of the
// ornaments Scott showed for reference.
//
// Printed flat, back on the plate, nothing overhangs. Two colours, by height:
//   frame   the ring, the loop, the name's outline and bar (0-2.4 mm), and the
//           star, sprigs and swag up to 1.6 mm
//   accent  the tops of the star, sprigs, swag and berries (1.6-2.4 mm), and the
//           name and year, raised 0.8 mm on their outline (2.4-3.2 mm)
// The AMS changes colour only on the four layers from 1.6 to 2.4 mm.
//
// The maker's mark is engraved in the back of the name's outline, turned to read
// when the ornament is turned over on its loop, as an ornament is (the domed one's
// read upside down that way, Scott's print, 2026-11-18).
//
//   NAME, YEAR   the personalisation (YEAR = "" leaves it off)
//   part = frame | accent | union | all
include <../../brand/obc_mark.scad>

NAME = "Olivia";
YEAR = "2026";
part = "all";

$fn = 96;
RO   = 40;            // 80 mm across
RW   = 3.6;           // the ring's width
RI   = RO - RW;
T    = 2.4;           // the frame's thickness
CAP  = 0.8;           // the accent tops of the motifs: four layers
RAISE = 0.8;          // the name and year stand this far above their outline

NAME_FONT = "Lobster:style=Regular";
YEAR_FONT = "Montserrat:style=ExtraBold";
// Lobster's advance per unit size, measured with textmetrics (see pmm/build_pmm.py)
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -'.!&";
NAME_ADV = [0.9278, 0.8903, 0.6903, 0.9208, 0.6375, 0.6375, 0.8028, 0.9236, 0.5208, 0.7444, 0.8347, 0.5264, 1.0931, 0.9278, 0.9236, 0.7958, 0.9236, 0.8347, 0.7917, 0.6681, 0.9944, 0.8542, 1.3361, 0.8611, 0.8611, 0.7528, 0.6486, 0.6167, 0.4736, 0.6611, 0.5083, 0.3708, 0.6667, 0.6292, 0.2903, 0.2958, 0.6556, 0.2875, 0.9736, 0.6306, 0.6764, 0.65, 0.675, 0.5222, 0.4389, 0.3833, 0.6375, 0.575, 0.9181, 0.6945, 0.6389, 0.5944, 0.7583, 0.4403, 0.6833, 0.7139, 0.6611, 0.7181, 0.6945, 0.6444, 0.6931, 0.6792, 0.3014, 0.4028, 0.2722, 0.3653, 0.3569, 0.9472];
function name_adv(c) = let (i = search(c, NAME_CHARS)) len(i) && i[0] != [] ? NAME_ADV[i[0]] : 0.7;
function name_w(s, n) = n <= 0 ? 0 : name_w(s, n - 1) + name_adv(s[n - 1]);
NAME_W    = 60;       // the widest the name may run
NAME_SIZE = len(NAME) == 0 ? 15 : min(15, NAME_W / name_w(NAME, len(NAME)));
NAME_Y    = 3;
YEAR_SIZE = 6.5;      // strokes over 1 mm: the 5.5 mm year on the dome lost a stroke
YEAR_Y    = NAME_Y - 0.55 * NAME_SIZE - 6;
OUTLINE   = 1.8;      // the name's outline, past its letters

// cleaned as a nozzle draws: gaps under 0.85 closed, strokes under a bead opened
module clean() offset(r = 0.21, $fn = 12) offset(delta = -0.21) offset(r = -0.425, $fn = 12) offset(delta = 0.425) children();

module name2d() clean() translate([0, NAME_Y]) text(NAME, size = NAME_SIZE, font = NAME_FONT, halign = "center", valign = "center");
module year2d() if (len(YEAR)) clean() translate([0, YEAR_Y]) text(YEAR, size = YEAR_SIZE, font = YEAR_FONT, halign = "center", valign = "center", spacing = 1.12);
module words2d() { name2d(); year2d(); }

// the outline: every letter, dot and the year merged into one piece, and a bar
// across the middle out to the ring on both sides, so any name holds together
module outline2d() {
    offset(r = OUTLINE) offset(r = 1.2) offset(delta = -1.2) offset(r = 1.2) words2d();   // gaps under 2.4 closed
    intersection() {
        translate([-RO, NAME_Y - 0.12 * NAME_SIZE - 1.7]) square([2 * RO, 3.4]);   // 3.4: at 2.8 the fragility check put it on watch
        circle(r = RI + 1);
    }
}

module ring2d() difference() { circle(r = RO, $fn = 192); circle(r = RI, $fn = 192); }
LOOP_RO = 4.8; LOOP_RI = 2.2;
module loop2d() translate([0, RO + LOOP_RO - 1.6]) difference() { circle(r = LOOP_RO, $fn = 48); circle(r = LOOP_RI, $fn = 48); }

module star2d(r, k = 0.47) polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, rr = i % 2 ? r * k : r) [rr * cos(a), rr * sin(a)]]);
module seg(a, b, w) hull() { translate(a) circle(d = w, $fn = 16); translate(b) circle(d = w, $fn = 16); }
function bez(p, t) = (1 - t) * (1 - t) * p[0] + 2 * (1 - t) * t * p[1] + t * t * p[2];
function unit(v) = v / norm(v);
// a pine sprig along a curve: a stem, and needle pairs reaching toward its tip
module sprig(p, n = 9, len_ = 4.6, w = 1.3, stem = 1.7, t0 = 0.12, t1 = 0.94) {
    for (i = [0 : 15]) seg(bez(p, i / 16), bez(p, (i + 1) / 16), stem);
    for (i = [0 : n - 1]) let (t = t0 + (t1 - t0) * i / (n - 1), c = bez(p, t),
                               d = unit(bez(p, t + 0.01) - bez(p, t - 0.01)), nn = [-d[1], d[0]])
        for (s = [-1, 1]) let (v = 0.7 * d + 0.71 * s * nn,
                               // needles on the inside of the curve, toward the ornament's
                               // middle, fan together; shorter there, so the air between
                               // them stays wide enough to print (2026-11-18)
                               inner = v * c < 0 ? 0.6 : 1)
            seg(c, c + len_ * inner * v * (1 - 0.3 * t), w);
}
// anything narrower than 1.2 mm (two beads) taken off, and sharp tips rounded at
// 0.6 mm: a star's point or a holly spike otherwise runs down to nothing
module open12() offset(r = 0.6, $fn = 16) offset(delta = -0.6) children();
// and the roots of the V's where a needle, a stem or a star's arm meet filled to
// 0.45 mm: narrower than 0.8 they print closed anyway, as a ragged wedge
module close09() offset(r = -0.45, $fn = 16) offset(delta = 0.45) children();
STAR_R = 8.5;
// the boughs reach down to the name's ends: a short name (Mia, Zoë) left them
// hanging in the air at a fixed 23 mm (2026-11-18)
BOUGH_X = min(23, max(13, NAME_SIZE * name_w(NAME, len(NAME)) / 2 - 1));
// its top point runs 3.2 mm into the ring: rounding the point (open12) takes ~1.9 off
STAR_Y = RI - STAR_R + 3.2;
// a holly leaf from the origin along +x: a pointed oval with spiked edges
module holly2d(L = 15, W = 7.5, k = 3)
    polygon(concat(
        [for (i = [0 : 2 * k]) let (s = i / (2 * k), w = (i % 2 ? 0.62 : 1) * W / 2 * sin(180 * s)) [L * s, w]],
        [for (i = [2 * k - 1 : -1 : 1]) let (s = i / (2 * k), w = (i % 2 ? 0.62 : 1) * W / 2 * sin(180 * s)) [L * s, -w]]));
HOLLY_Y = YEAR_Y - 9.2;      // the top berry runs into the year's outline
module motifs2d() open12() close09() {
    // the star, and two pine boughs from it down to the name: a tree's canopy
    translate([0, STAR_Y]) star2d(STAR_R);
    for (m = [0, 1]) mirror([m, 0]) {
        // four long needle pairs (Scott, 2026-11-19: fewer, so they read as pine, not a
        // garland of stubs); at eight the needles stood 0.47 mm apart and printed webbed
        sprig([[-0.5, STAR_Y - 1], [-0.6 * BOUGH_X, STAR_Y - 1], [-BOUGH_X, NAME_Y + 0.35 * NAME_SIZE]], n = 4, len_ = 8.5, w = 1.6, stem = 2.2, t0 = 0.24, t1 = 0.72);   // needles clear of the star and the name
        // small stars caught on the ring, either side
        for (a = [148, 212]) translate([RI * cos(a), RI * sin(a)] * 0.96) rotate(a - 90) star2d(3.8, 0.5);
    }
    // holly under the year: three leaves and three berries, the bottom leaf
    // running into the ring
    translate([0, HOLLY_Y]) {
        for (a = [-160, -20, -90]) rotate(a) translate([1.5, 0]) holly2d(a == -90 ? RI + HOLLY_Y + 1.5 : 17.5, 9);
        for (p = [[0, 3.4], [-3.6, 0.9], [3.6, 0.9]]) translate(p) circle(r = 2.8, $fn = 32);
    }
}
// the holly's veins, cut through the accent so the frame colour shows
module veins2d() translate([0, HOLLY_Y]) for (a = [-160, -20, -90]) rotate(a)
    translate([5.5, -0.5]) square([a == -90 ? RI + HOLLY_Y - 7 : 10, 1.0]);

module frame2d() union() { ring2d(); loop2d(); outline2d(); }

module frame() {
    linear_extrude(T) frame2d();
    linear_extrude(T - CAP) motifs2d();
}
module accent() {
    translate([0, 0, T - CAP]) linear_extrude(CAP) difference() { motifs2d(); frame2d(); veins2d(); }
    translate([0, 0, T]) linear_extrude(RAISE) words2d();
}
MARK_H = 4.5;
// the mark turned 180 from obc_mark's (which reads when tipped back, as under a
// building): an ornament is turned over on its loop, side to side
module frame_marked() difference() { frame(); translate([0, NAME_Y - 0.12 * NAME_SIZE, 0]) rotate([0, 0, 180]) obc_engrave(MARK_H); }

if (part == "frame") frame_marked();
else if (part == "accent") accent();
else if (part == "union") union() { frame_marked(); accent(); }
else { color("#C62F3A") frame_marked(); color("#F4F1EA") accent(); }
