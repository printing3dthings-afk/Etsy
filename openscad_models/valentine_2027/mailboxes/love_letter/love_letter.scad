// Giant Love Letter: a classroom Valentine mailbox (2026-10-30). Scott's pick 4
// of five: "a big standing envelope with a heart wax seal ... the flap lifts to
// empty it", for kids' school valentines. Kid- and school-friendly: no small or
// loose parts, no magnets, every edge rounded, and the slot takes a standard
// kids' valentine in its envelope.
//
// Two prints:
//   body  the envelope, a cup printed standing on its base. One face is the
//         address side (a stamp, a postmark, "To:" and the child's name), the
//         other the back of an envelope: its bottom flap, its top flap and a
//         heart wax seal where they meet.
//   lid   the top edge of the envelope, with the card slot. Printed upside
//         down on its top face; a spigot drops 10 mm into the body, so it
//         sits put but lifts straight off to empty the box.
//
//   part = body | body_red | body_white | body_dark | lid
//          body_print (body + its colours, merged, for the gate) | assembly
// NAME is the child's name; it scales to fit.

SH = 1.2;
include <../../../christmas_village/relief_lib.scad>
use <../../../brand/obc_mark.scad>
include <../name_text.scad>

NAME = "OLIVIA";
part = "assembly";
$fa = 2; $fs = 0.3;

W = 180; D = 62; R = 8;          // the envelope's face, its thickness, its corner radius
HB = 122;                        // the body's height; the lid adds LT on top
WALL = 2.4; FLOOR = 2.0;
LT = 2.4;                        // the lid's top plate
SP = 10; SPW = 2.0; CLR = 0.3;   // the lid's spigot: depth, wall, clearance all round
SLOT = [118, 11];                // the card slot: a 4" envelope with room, 11 for thick cards
FONT = "Fredoka:style=SemiBold";

module plan(o = 0) offset(r = R + o) square([W - 2 * R, D - 2 * R], center = true);

// ---------------- the body ----------------
module body_shell() difference() {
    // a 0.6 chamfer at the foot keeps the first layer from flaring
    union() {
        hull() { linear_extrude(0.01) plan(-0.6); translate([0, 0, 0.6]) linear_extrude(HB - 0.6) plan(); }
    }
    translate([0, 0, FLOOR]) linear_extrude(HB) plan(-WALL);
}

// Relief on the two big faces. front(): the address side, at -y, raised toward
// -y. back(): the flap side, at +y, raised toward +y, its 2D x as seen from
// behind. art_skirt puts a slope under every edge, so nothing overhangs.
module front(h, z0 = 0) translate([0, -D / 2 - z0, 0]) rotate([90, 0, 0]) art_skirt(h, 1) children();
module back(h, z0 = 0) translate([0, D / 2 + z0, 0]) rotate([90, 0, 180]) art_skirt(h, 1) children();

// the back of the envelope
TIP_B = 0.52 * HB;               // the bottom flap's point
TIP_T = 0.42 * HB;               // the top flap's point, below it: the top flap overlaps
module bottom_flap2d() offset(r = 3) offset(delta = -3)
    polygon([[-W / 2 + 4, 4], [W / 2 - 4, 4], [0, TIP_B]]);
module top_flap2d() offset(r = 3) offset(delta = -3)
    polygon([[-W / 2 + 4, HB - 0.4], [W / 2 - 4, HB - 0.4], [0, TIP_T]]);
SEAL_R = 15;
module seal2d() translate([0, TIP_T + 2]) union() {
    circle(SEAL_R - 1.5, $fn = 90);
    for (k = [0 : 11]) rotate(k * 30) translate([SEAL_R - 2.2, 0]) circle(2.6, $fn = 30);
}
module heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}

// the address side
STAMP = [30, 36]; STAMP_C = [W / 2 - 24, HB - 26];
module stamp2d() translate(STAMP_C) difference() {
    square(STAMP, center = true);
    // the perforated edge: half-round bites every 4 mm
    for (x = [-STAMP.x / 2 + 3 : 4 : STAMP.x / 2 - 2], s = [-1, 1]) translate([x, s * STAMP.y / 2]) circle(1.2, $fn = 20);
    for (y = [-STAMP.y / 2 + 3 : 4 : STAMP.y / 2 - 2], s = [-1, 1]) translate([s * STAMP.x / 2, y]) circle(1.2, $fn = 20);
}
module postmark2d() translate([STAMP_C.x - 36, STAMP_C.y]) {
    difference() { circle(13, $fn = 90); circle(11.2, $fn = 90); }
    for (k = [-1, 0, 1]) translate([-14, k * 6])
        for (i = [0 : 23]) let (x0 = -i * 2, x1 = x0 - 2)
            hull() { translate([x0, 1.2 * sin(x0 * 12)]) circle(0.9, $fn = 16); translate([x1, 1.2 * sin(x1 * 12)]) circle(0.9, $fn = 16); }
}
module name2d() translate([4, 50]) name_text(NAME, name_fit(NAME, 128, 20, 1.1), 1.1);
module to2d() translate([-W / 2 + 14, 70]) text("To:", size = 9, font = FONT, valign = "center");
module line2d() translate([4, 34]) square([126, 1.6], center = true);

// The seal rises from the wall itself, through both flaps: it straddles the top
// flap's point, so raised from the flap it would hang over the lower layers.
module seal() back(3.2) seal2d();
module body() difference() {
    union() {
        body_shell();
        back(0.6) bottom_flap2d();
        back(1.2) top_flap2d();
    }
    seal();
    obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
}
// the colours, each raised from where it sits
module body_red() {
    seal();
    back(0.8, 3.2) translate([0, TIP_T + 2]) heart2d(17);
    front(0.8, 1.0) translate(STAMP_C) heart2d(17);
    front(0.6) postmark2d();
}
module body_white() front(1.0) difference() { stamp2d(); }
module body_dark() {
    front(1.0) name2d();
    front(0.8) to2d();
    front(0.6) line2d();
}

// ---------------- the lid, in use: its underside at HB ----------------
module lid_use() difference() {
    union() {
        translate([0, 0, HB]) hull() {
            linear_extrude(LT - 1.0) plan();
            translate([0, 0, LT - 1.0]) linear_extrude(1.0) plan(-0.7);   // a 35 deg chamfer round the top edge
        }
        translate([0, 0, HB - SP]) linear_extrude(SP + 0.01) difference() { plan(-WALL - CLR); plan(-WALL - CLR - SPW); }
    }
    translate([0, 0, HB - 1]) linear_extrude(LT + 2) offset(r = SLOT.y / 2) square([SLOT.x - SLOT.y, 0.01], center = true);
}
module lid_print() translate([0, 0, HB + LT]) mirror([0, 0, 1]) lid_use();

module body_print() union() { body(); body_red(); body_white(); body_dark(); }

if      (part == "body")       body();
else if (part == "body_red")   body_red();
else if (part == "body_white") body_white();
else if (part == "body_dark")  body_dark();
else if (part == "body_print") body_print();
else if (part == "lid")        lid_print();
else if (part == "lid_use")    lid_use();
else {
    color("#F6A6C1") body();
    color("#D7263D") body_red();
    color("#F4F1EA") body_white();
    color("#3B2A3A") body_dark();
    color("#F6A6C1") lid_use();
}
