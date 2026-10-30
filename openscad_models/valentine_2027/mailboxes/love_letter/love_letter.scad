// Giant Love Letter: a classroom Valentine mailbox (2026-10-30). Scott's pick 4
// of five: "a big standing envelope with a heart wax seal ... the flap lifts to
// empty it", for kids' school valentines. Kid- and school-friendly: no small or
// loose parts, no magnets, every edge rounded, and the slot takes a standard
// kids' valentine in its envelope.
//
// Made more fun (Scott, 2026-10-30, his picks 1 and 4 of five): a cartoon
// Cupid, his own print, sits in a pocket on the address side aiming his arrow
// at the name; and two-tone sticker hearts, raised in the envelope's own
// colours, front and back. Loose hearts would be small parts, so they're fixed.
//
// Three prints:
//   body  the envelope, a cup printed standing on its base. One face is the
//         address side (a stamp, a postmark, "To:" and the child's name), the
//         other the back of an envelope: its bottom flap, its top flap and a
//         heart wax seal where they meet.
//   lid   the top edge of the envelope, with the card slot. Printed upside
//         down on its top face; a spigot drops 10 mm into the body, so it
//         sits put but lifts straight off to empty the box.
//   cupid face up, four colours (cupid.scad); presses onto two pegs in his
//         pocket.
//
//   part = body | body_red | body_white | body_dark | lid
//          cupid | cupid_white | cupid_red | cupid_dark (as printed)
//          cupid_use, cupid_white_use, ... (in his pocket)
//          body_print, cupid_print (merged, for the gate) | assembly
// NAME is the child's name; it scales to fit.

SH = 1.2;
include <../../../christmas_village/relief_lib.scad>
use <../../../brand/obc_mark.scad>
include <../name_text.scad>
include <cupid.scad>

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
// The name block moves right to leave the lower left to Cupid.
// Kept 4 clear of x = 82, where the face turns into the rounded corner: a line
// run onto the curve hangs in the air (the slicer propped it, 2026-10-30).
module name2d() translate([34, 50]) name_text(NAME, name_fit(NAME, 88, 20, 1.1), 1.1);
module to2d() translate([-12, 72]) text("To:", size = 9, font = FONT, valign = "center");
module line2d() translate([34, 34]) square([92, 1.6], center = true);

// ---------- Cupid's pocket ----------
// on_front: x across, y up, z out of the envelope's face
module on_front(z = 0) translate([0, -D / 2, 0]) rotate([90, 0, 0]) translate([0, 0, z]) children();
CUPID_AT = [-52, 4];             // his frame's origin on the face: lower left, wings clear of the corner
POCKET_D = 1.0;                  // leaves 1.4 of the 2.4 wall behind him
POCKET_A = 37;
// The pocket is his outline 0.3 larger, straight down to its floor, except
// that every edge facing down is swept up at POCKET_A on its way out to the
// face: otherwise his pocket's top edge is a 1.0 ceiling on an upright wall.
// The sweep is a Minkowski sum with a thin wedge (at depth z, the outline
// stretched up by z / tan(POCKET_A)). Shearing the whole outline instead also
// lifted the pocket's bottom wall into his legs: 29.9 mm3 of overlap
// (2026-10-30).
module cupid_pocket() on_front(-POCKET_D) translate(CUPID_AT)
    minkowski() {
        translate([0, 0, -0.01]) linear_extrude(0.01) offset(r = 0.3) cupid_outline();
        hull() for (q = [[0, 0], [0, POCKET_D + 0.5], [(POCKET_D + 0.5) / tan(POCKET_A), POCKET_D + 0.5]])
            translate([-0.005, q[0], q[1]]) cube([0.01, 0.01, 0.01]);
    }
// each peg starts 0.3 inside the wall behind the pocket floor, so it is one
// body with it
module cupid_pegs() on_front(-POCKET_D) translate(CUPID_AT) for (p = PEGS) translate(peg_at(p)) union() {
    peg_shape();
    translate([-PEG_W / 2, -PEG_ROOT, -0.3]) cube([PEG_W, PEG_ROOT, 0.31]);
}
module at_pocket() on_front(-POCKET_D) translate(CUPID_AT) children();

// ---------- sticker hearts ----------
// [centre, size, turn, style]: style 0 a red heart on a white sticker, 1 a pink
// heart on a red one. The backing stands 0.6, the heart 0.6 on it.
FRONT_STICKERS = [[[-62, 98], 16, 12, 0], [[-44, 111], 10, -14, 1], [[70, 16], 14, -10, 1]];
// on the back: and the flap each sits on (its z0)
BACK_STICKERS  = [[[-64, 62], 16, -10, 0, 0], [[64, 58], 12, 14, 1, 0], [[40, 108], 13, -8, 0, 1.2], [[-40, 17], 11, 10, 1, 0.6]];
module sticker_heart(st) translate(st[0]) rotate(st[2]) heart2d(st[1]);
module sticker_back(st) translate(st[0]) rotate(st[2]) offset(r = 1.6) heart2d(st[1]);
// colour c (0 pink, 1 red, 2 white) of the stickers
module stickers(c) {
    for (st = FRONT_STICKERS) {
        if ((st[3] == 0 && c == 2) || (st[3] == 1 && c == 1)) front(0.6) sticker_back(st);
        if ((st[3] == 0 && c == 1) || (st[3] == 1 && c == 0)) front(0.6, 0.6) sticker_heart(st);
    }
    for (st = BACK_STICKERS) {
        if ((st[3] == 0 && c == 2) || (st[3] == 1 && c == 1)) back(0.6, st[4]) sticker_back(st);
        if ((st[3] == 0 && c == 1) || (st[3] == 1 && c == 0)) back(0.6, st[4] + 0.6) sticker_heart(st);
    }
}

// The seal rises from the wall itself, through both flaps: it straddles the top
// flap's point, so raised from the flap it would hang over the lower layers.
module seal() back(3.2) seal2d();
module body() union() {
    difference() {
        union() {
            body_shell();
            back(0.6) bottom_flap2d();
            back(1.2) top_flap2d();
            stickers(0);
        }
        seal();
        obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
        cupid_pocket();
    }
    cupid_pegs();
}
// the colours, each raised from where it sits
module body_red() {
    seal();
    back(0.8, 3.2) translate([0, TIP_T + 2]) heart2d(17);
    front(0.8, 1.0) translate(STAMP_C) heart2d(17);
    front(0.6) postmark2d();
    stickers(1);
}
module body_white() { front(1.0) stamp2d(); stickers(2); }
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
else if (part == "cupid")        cupid_skin();
else if (part == "cupid_white")  cupid_white();
else if (part == "cupid_red")    cupid_red();
else if (part == "cupid_dark")   cupid_dark();
else if (part == "cupid_print")  cupid_print();
else if (part == "cupid_use")       at_pocket() cupid_skin();
else if (part == "cupid_white_use") at_pocket() cupid_white();
else if (part == "cupid_red_use")   at_pocket() cupid_red();
else if (part == "cupid_dark_use")  at_pocket() cupid_dark();
else if (part == "cupid_print_use") at_pocket() cupid_print();
else {
    color("#F6A6C1") body();
    color("#D7263D") body_red();
    color("#F4F1EA") body_white();
    color("#3B2A3A") body_dark();
    color("#F6A6C1") lid_use();
    at_pocket() {
        color("#F9C9A6") cupid_skin();
        color("#F4F1EA") cupid_white();
        color("#D7263D") cupid_red();
        color("#3B2A3A") cupid_dark();
    }
}
