// Hungry Love Monster: a classroom Valentine mailbox (2026-10-30). Scott's pick
// 2 of five: "a round, chubby monster whose wide grinning mouth is the card slot
// ('Feed me valentines!'), with stubby arms hugging a heart." Kid- and
// school-friendly: no small or loose parts, no magnets, rounded everywhere a
// hand goes, and the mouth takes a standard kids' valentine in its envelope.
//
// Two prints:
//   body  the monster, a cup printed standing on its feet: big eyes, a toothy
//         grin cut right through the wall for the cards to go in, stubby arms
//         hugging a heart with the child's name on it.
//   fur   a furry cap with a scalloped fringe that sits over the top. Printed
//         upside down on its top; lift it off to empty the box.
//
// The mouth is a hole through an upright wall, so its top edge is a row of
// teeth: every edge of a tooth climbs at 55 deg, and the hole needs no support
// anywhere. A straight-topped slot would be a 110 mm bridge.
//
//   part = body | body_white | body_red | body_dark | fur
//          body_print (merged, for the gate) | fur_use | assembly
// NAME is the child's name; it scales to fit the heart.

SH = 1.2;
include <../../../christmas_village/relief_lib.scad>
use <../../../brand/obc_mark.scad>

NAME = "LIAM";
part = "assembly";
$fa = 2; $fs = 0.3;
FONT = "Fredoka:style=SemiBold";

A = 80; B = 60; N = 8;           // the body's plan: a superellipse 160 x 120, soft corners
HB = 140;                        // the body's height
WALL = 2.4; FLOOR = 2.0;
FT = 2.4; FS = 22; FCLR = 0.4;   // the fur cap: top, skirt height, clearance over the body
FW = 2.4;                        // its skirt's wall
FRINGE = 10;                     // how far its scallops hang below the skirt

function se(t, a, b, n) = [a * sign(cos(t)) * pow(abs(cos(t)), 2 / n), b * sign(sin(t)) * pow(abs(sin(t)), 2 / n)];
module plan(o = 0) offset(r = o) polygon([for (i = [0 : 359]) se(i, A, B, N)]);

// Points evenly spaced along the outline, by arc length: a superellipse's own
// angle bunches them at the corners and leaves the flat faces bare (the first
// fringe hung in clumps, 2026-10-30).
OUT = [for (i = [0 : 1439]) se(i / 4, A, B, N)];
CUM = [for (i = 0, s = 0; i < len(OUT); s = s + norm(OUT[(i + 1) % len(OUT)] - OUT[i]), i = i + 1) s];
PER = CUM[len(CUM) - 1] + norm(OUT[0] - OUT[len(OUT) - 1]);
function at_len(L) = let (d = [for (c = CUM) abs(c - L)], i = search(min(d), d)[0]) i;
function nrm_at(i) = let (q = OUT[i], g = [sign(q.x) * pow(abs(q.x), N - 1) / pow(A, N), sign(q.y) * pow(abs(q.y), N - 1) / pow(B, N)]) g / norm(g);
// evenly round the outline, starting at the front's middle
function along(n) = [for (k = [0 : n - 1]) at_len((CUM[1080] + k * PER / n) % PER)];

// ---------------- the body ----------------
module body_shell() difference() {
    hull() { linear_extrude(0.01) plan(-0.6); translate([0, 0, 0.6]) linear_extrude(HB - 0.6) plan(); }
    translate([0, 0, FLOOR]) linear_extrude(HB) plan(-WALL);
}

// Relief on the front. The front is flat to within 0.9 mm across the mouth
// (the superellipse at |x| = 56), so art stands on a plane BURY inside the
// wall at y = -B + BURY and comes out h proud at the middle.
BURY = 3.5;
// Clipped at the bed: the skirts under the feet and the heart's point ran 6.4 mm
// below z = 0, and the slicer stood the whole body on them (30,182 support
// moves, 0.1% of the base on the plate, 2026-10-30).
module face(h, z0 = 0) intersection() {
    translate([0, -B + BURY - z0, 0]) rotate([90, 0, 0]) art_skirt(h + BURY, 1) children();
    translate([-500, -500, 0]) cube(1000);
}
module face_on(h, z0) translate([0, -B - z0, 0]) rotate([90, 0, 0]) art_skirt(h, 1) children();

// the mouth: a smile, its top a row of teeth
MW = 112;                        // across
MZ = 50;                         // its lowest point, at the middle
SMILE = 3;                       // the corners sit this much higher
CLEAR = 15;                      // floor to tooth tips: the straight gap a card needs is 12.4
NT = 8;                          // teeth
TA = 55;                         // their edges climb this steep
function lip(x) = MZ + SMILE * pow(x / (MW / 2), 2);
TW = MW / NT;
TH = TW / 2 * tan(TA);
// the tooth tips rounded 0.8, for small fingers
module mouth2d() offset(r = -0.8) offset(delta = 0.8) polygon(concat(
    [for (i = [0 : 24]) let (x = -MW / 2 + MW * i / 24) [x, lip(x)]],
    // right to left: a peak at each tooth boundary, a tip between each pair.
    // (Tips only between inner peaks lost the rightmost tooth, 2026-10-30.)
    [for (k = [NT : -1 : 0]) each let (x = -MW / 2 + k * TW)
        k == NT ? [[x, lip(x) + CLEAR + TH]] :
        [[x + TW / 2, lip(x + TW / 2) + CLEAR], [x, lip(x) + CLEAR + TH]]]));
// the teeth themselves, white: the band from the tooth tips up to the peaks
// between them, less the mouth
module teeth2d() difference() {
    polygon(concat([for (i = [0 : 24]) let (x = -MW / 2 + MW * i / 24) [x, lip(x) + CLEAR - 0.01]],
                   [for (i = [24 : -1 : 0]) let (x = -MW / 2 + MW * i / 24) [x, lip(x) + CLEAR + TH]]));
    mouth2d();
}
module mouth_cut() rotate([90, 0, 0]) translate([0, 0, B - 20]) linear_extrude(30) mouth2d();

// eyes, peeking out under the fringe
EZ = 92; EX = 24; ER = 13;      // the fur's fringe hangs to HB - FS - FRINGE = 108
module eyes_white2d() for (s = [-1, 1]) translate([s * EX, EZ]) scale([1, 1.12]) circle(ER, $fn = 120);
module pupils2d() for (s = [-1, 1]) translate([s * EX + s * -3, EZ - 2.6]) scale([1, 1.12]) circle(6.4, $fn = 80);
module shine2d() for (s = [-1, 1]) translate([s * EX + s * -3 + 2.2, EZ + 0.8]) circle(2.0, $fn = 40);

// the heart, hugged by two stubby arms, and feet at the foot
HZ = 28;
module heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
HS = 46;                         // the heart's width
module heart_big2d() translate([0, HZ]) heart2d(HS);
module arms2d() for (s = [-1, 1]) hull() {
    // the shoulders stay inside |x| = 67, where the wall is within 2 mm of the
    // face's plane: further out the relief would stand off the curving wall
    translate([s * 58, 40]) circle(9, $fn = 60);
    translate([s * 30, 24]) circle(8, $fn = 60);
}
module feet2d() for (s = [-1, 1]) translate([s * 34, 0]) intersection() {
    scale([1.6, 1]) circle(12, $fn = 90);
    translate([-30, 0]) square([60, 20]);
}
function fit_size(s, w, h) = min(h, w / (0.66 * len(s)));
module name2d() translate([0, HZ + 1]) text(NAME, size = fit_size(NAME, HS * 0.62, 11), font = FONT,
    halign = "center", valign = "center", spacing = 1.08);

// Each colour is cut from the ones behind it, so no two parts overlap: the
// pupils and the name (dark) stand 0.8 proud of the eyes and the heart; the
// hands hug the heart from in front.
module arms() face(2.4) arms2d();
module dark() { face(2.4) pupils2d(); face(2.4) name2d(); }
module white_main() difference() {
    union() { face(1.6) eyes_white2d(); face(1.0) teeth2d(); }
    dark();
    mouth_cut();
}
module red() difference() { face(1.6) heart_big2d(); arms(); dark(); }
module body() difference() {
    union() {
        body_shell();
        arms();
        face(2.0) feet2d();
    }
    mouth_cut();
    white_main();
    red();
    dark();
    obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);
}
module body_white() { white_main(); face_on(0.6, 2.4) shine2d(); }
module body_red() red();
module body_dark() dark();

// ---------------- the fur cap, in use: it sits on the body's rim at HB ----------------
NSC = 36;                        // scallops round the fringe, about 15 mm apart
NGR = 144;                       // fur grooves, about 3.8 mm apart
module fur_use() difference() {
    union() {
        translate([0, 0, HB]) hull() {
            linear_extrude(FT - 1.0) plan(FCLR + FW);
            translate([0, 0, FT - 1.0]) linear_extrude(1.0) plan(FCLR + FW - 0.7);
        }
        translate([0, 0, HB - FS]) linear_extrude(FS + 0.01) difference() { plan(FCLR + FW); plan(FCLR); }
        // the fringe: scallops hanging below the skirt all round
        intersection() {
            translate([0, 0, HB - FS - FRINGE]) linear_extrude(FRINGE + 0.02) difference() { plan(FCLR + FW); plan(FCLR); }
            union() for (i = along(NSC)) let (p = OUT[i], n = nrm_at(i))
                translate([p.x, p.y, HB - FS]) rotate([0, 0, atan2(n.y, n.x) + 90]) rotate([90, 0, 0])
                    linear_extrude(40, center = true) scale([1, FRINGE / 6.5]) circle(6.5, $fn = 48);
        }
    }
    // fur: grooves up the skirt, 0.6 deep, 0.8 wide, every 4.5 deg of the outline,
    // placed on the real offset outline along its normal
    for (i = along(NGR)) let (nrm = nrm_at(i), p = OUT[i] + (FCLR + FW) * nrm)
        translate([p.x, p.y, HB - FS - FRINGE - 1]) rotate([0, 0, atan2(nrm.y, nrm.x)])
            translate([-0.6, -0.4, 0]) cube([1.2, 0.8, FS + FRINGE - 3]);
}
module fur_print() translate([0, 0, HB + FT]) mirror([0, 0, 1]) fur_use();
module body_print() union() { body(); body_white(); body_red(); body_dark(); }

if      (part == "body")       body();
else if (part == "body_white") body_white();
else if (part == "body_red")   body_red();
else if (part == "body_dark")  body_dark();
else if (part == "body_print") body_print();
else if (part == "fur")        fur_print();
else if (part == "fur_use")    fur_use();
else {
    color("#B79CE0") body();
    color("#F4F1EA") body_white();
    color("#D7263D") body_red();
    color("#2B2433") body_dark();
    color("#F58CB4") fur_use();
}
