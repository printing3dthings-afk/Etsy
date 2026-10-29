// Cookie Jar Peek-a-boo Clicker (2026-10-29), for MakerWorld's "Click Into
// Celebration". A gingerbread man pops out of a cookie jar, arms up; push him
// back in and a real MX switch clicks.
//
// Three prints and one plate-mount Cherry MX (or clone) switch:
//   the jar         the body, a cup; its open well takes the switch's body
//                   and pins
//   the top         shoulder, neck and rim; the switch plate is its floor,
//                   flat on the bed, under the neck
//   the gingerbread prints standing on his plunger, a disc that rides in the
//                   jar's neck, hides the switch and carries the socket
//
//   part = jar | jar_label | jar_letters | top | top_rim
//          gb | gb_icing | gb_red
//          jar_print | top_print | gb_print   (merged colours, for the gate)
//          assembly | pressed                 (preview, stand-in switch)
// The top exports standing on its own floor; everything else where it prints.
//
// The plunger is guided by the neck all the way down, so he goes down level
// wherever he is pushed: on the head, or on one raised hand.
//
// Colours: jar mint, rim and lettering red, label and icing white, gingerbread
// brown. Cheeks and buttons share the red: four filaments, one AMS.

SH = 1.2;
include <../../christmas_village/relief_lib.scad>
use <../../brand/obc_mark.scad>
include <../clicker_lib.scad>

part = "assembly";
$fa = 2; $fs = 0.3;

S      = 30.0;                  // the body's top face, where the top sits
P      = S + mx_plate_t;        // plate top
PT     = cav_h + cap_floor;     // plunger thickness, 6.2
CZ     = mx_cap_z(P);
RIM    = CZ + PT + 1.2;         // the plunger's top rests 1.2 under the rim, so
                                // the jar's inside shows round his feet and he
                                // drops 4 into it
PL_R   = 13.3;                  // plunger; 1.7 of wall at the cavity's corners
BORE_R = PL_R + 0.6;
JR     = 25.0;                  // jar body
NECK_R = 17.2;
LIP_R  = 18.6;
SHOULDER = [S + JOINT + 1.7, S + JOINT + 9.0];   // from 1.4 out of the spigot over 1.7 up: 40 deg
SPIG_R = JR - LIP_W - JOINT_CLR; // the top's spigot, inside the body's lip
FT     = 7.0;                   // the gingerbread's thickness
ICE    = 0.8;
ICE_W  = 0.85;

echo(str("plate ", P, "  plunger rest ", CZ, " pressed ", mx_cap_z_down(P),
         "  plunger top ", CZ + PT, "  rim ", RIM));

// ---------- the jar ----------
function shoulder_pts() = [for (k = [0 : 12]) let (t = k / 12)
    [NECK_R + (JR - NECK_R) * cos(90 * t), SHOULDER[0] + (SHOULDER[1] - SHOULDER[0]) * sin(90 * t)]];

// The body is a cup with a 1.2 lip round its top (0.6 failed the gate's wall
// floor). The top's spigot drops 2 mm inside it and curves back out into the
// shoulder, never steeper than 40 deg,
// leaving a groove at the seam. The lip at the rim flares under a 40 deg
// chamfer (1.4 out over 1.7 up), not a level step: the slicer needs nothing
// under either.
module body_solid() difference() {
    union() { cylinder(h = 0.61, r1 = JR - 0.6, r2 = JR, $fn = 240); translate([0, 0, 0.6]) cylinder(h = S + JOINT - 0.6, r = JR, $fn = 240); }
    translate([0, 0, S]) cylinder(h = JOINT + 1, r = JR - LIP_W, $fn = 240);
}
module top_solid() rotate_extrude($fn = 240) polygon(concat(
    [[0, S], [SPIG_R, S], [SPIG_R, S + JOINT]],
    shoulder_pts(),
    [[NECK_R, RIM - 3.2], [LIP_R, RIM - 1.5], [LIP_R, RIM - 0.7], [LIP_R - 0.7, RIM], [0, RIM]]));
module jar_solid() union() { body_solid(); top_solid(); }

LIP_Z = RIM - 3.4;
module rim_zone() translate([0, 0, LIP_Z]) cylinder(h = 10, r = 40);

// Label: a flush white panel round the front, the lettering raised on it.
LBL_W = 40; LBL_H = 10; LBL_Z = 15.5;
module label_prism() rotate([90, 0, 0]) linear_extrude(40) translate([0, LBL_Z])
    offset(r = 2) square([LBL_W - 4, LBL_H - 4], center = true);
module jar_label_raw() intersection() {
    label_prism();
    difference() { cylinder(h = RIM, r = JR + 0.01, $fn = 240); cylinder(h = RIM, r = JR - 0.6, $fn = 240); }
}

// Fredoka SemiBold, each letter set on its own tangent plane round the jar.
// Advances are the font's own (hmtx), scaled the way OpenSCAD sets size 5.6
// (an em of 7.78 mm, measured off a rendered O), plus 0.3 so no two letters
// touch: guessed ones ran the C into the O.
WORD = "COOKIES";
ADV  = [for (a = [0.643, 0.725, 0.725, 0.595, 0.232, 0.610, 0.546]) a * 7.78 + 0.3];
LT_SIZE = 5.6;
function adv_to(i) = i == 0 ? 0 : ADV[i - 1] / 2 + ADV[i] / 2 + adv_to(i - 1);
LT_SPAN = adv_to(len(ADV) - 1);
module letters_raw() for (i = [0 : len(WORD) - 1])
    let (a = (adv_to(i) - LT_SPAN / 2) / JR * 180 / PI)
    rotate([0, 0, -90 + a]) translate([JR - 0.15, 0, LBL_Z]) rotate([90, 0, 90])
        art_skirt(0.9, 1) text(WORD[i], size = LT_SIZE, font = "Fredoka:style=SemiBold", halign = "center", valign = "center");

module body_gross() difference() { body_solid(); mx_well_cut(S); obc_engrave(8, depth = 0.8, inset = 0.15, ridges = false); }
module top_gross() difference() {
    top_solid();
    translate([0, 0, P - 0.01]) cylinder(h = RIM, r = BORE_R, $fn = 160);
    mx_plate_cut(S);
}
module jar()         difference() { body_gross(); jar_label_raw(); }
module jar_label()   intersection() { body_gross(); jar_label_raw(); }
module jar_letters() difference() { letters_raw(); body_solid(); }
module top()         difference() { top_gross(); rim_zone(); }
module top_rim()     intersection() { top_gross(); rim_zone(); }

// ---------- the gingerbread, standing on his plunger ----------
// Drawn in x (across) and z (up, from the plunger's top). Arms raised 52 deg,
// so their undersides face 38 deg from straight up-and-down and print bare.
head_c = [0, 19.2]; head_r = 8.4;
sh_c = [5, 8.2]; hand_c = [14.5, 20.6]; limb_r = 3.0;

module gb_raw() offset(r = -1.5) offset(r = 1.5) union() {
    translate(head_c) circle(head_r);
    translate([0, 5.5]) offset(r = 3) square([10, 8], center = true);
    for (s = [-1, 1]) hull() { translate([s * sh_c.x, sh_c.y]) circle(limb_r); translate([s * hand_c.x, hand_c.y]) circle(limb_r); }
}
// The shoulders sit inside the torso and the arms leave its sides already
// climbing, so nothing bulges out over air. A morphological skirt under the
// whole silhouette was tried first (2026-10-29): offsetting each lowered copy
// inward makes a cone 46 deg from upright, flatter than the 40 allowed, so it
// never touched the bulging shoulders and the slicer propped them, 937 moves.
module gb2d() intersection() { gb_raw(); translate([-40, 0]) square([80, 60]); }

// icing, drawn in the same x-z frame
module band2d() intersection() {
    difference() { offset(delta = -1.0) gb2d(); offset(delta = -1.0 - ICE_W) gb2d(); }
    translate([-40, 3]) square([80, 60]);   // not along his bottom, which stands in the jar
}
module face2d() {
    for (s = [-1, 1]) translate([s * 3.0, 20.4]) circle(1.15);
    pipe2d([for (x = [-1.6 : 0.4 : 1.61]) [x, 16.9 + 0.18 * x * x]], ICE_W);
}
module wrists2d() for (s = [-1, 1]) scale([s, 1])
    pipe2d(zigzag(sh_c + 0.7 * (hand_c - sh_c), atan2(hand_c.y - sh_c.y, hand_c.x - sh_c.x), 1.5, 0.6, 3), 0.8);
module cheeks2d()  for (s = [-1, 1]) translate([s * 4.0, 17.0]) circle(1.0);
module buttons2d() for (z = [3.6, 7.8]) translate([0, z]) circle(1.3);

// on the front face (-y) or the back (+y), h proud, undersides skirted
module on_front(h) translate([0, -FT / 2, PT]) rotate([90, 0, 0]) art_skirt(h, 1) children();
module on_back(h)  translate([0,  FT / 2, PT]) rotate([90, 0, 180]) art_skirt(h, 1) children();

module plunger() difference() {
    union() {
        cylinder(h = PT - 0.6, r = PL_R, $fn = 160);
        translate([0, 0, PT - 0.6 - 0.01]) cylinder(h = 0.61, r1 = PL_R, r2 = PL_R - 0.6, $fn = 160);
        // two little round cookies at his feet, in the jar with him
        for (s = [-1, 1]) translate([s * 5.6, -7.6, PT - 0.01]) cylinder(h = 1.2, r = 2.8, $fn = 48);
    }
    mx_cap_cut();
}
module gb() union() {
    plunger();
    translate([0, FT / 2, PT - 0.01]) rotate([90, 0, 0]) linear_extrude(FT) gb2d();
}
module gb_icing() { on_front(ICE) union() { band2d(); face2d(); wrists2d(); } on_back(ICE) band2d(); }
module gb_red()   on_front(0.8) union() { cheeks2d(); buttons2d(); }

module assembly(press = 0) {
    color("#A9DCC8") jar();
    color("white") jar_label();
    color("#B3262E") jar_letters();
    color("#A9DCC8") top();
    color("#B3262E") top_rim();
    mx_mock(S, press);
    translate([0, 0, CZ - press]) {
        color("#9A5B2E") gb();
        color("white") gb_icing();
        color("#B3262E") gb_red();
    }
}

if      (part == "jar")         jar();
else if (part == "jar_label")   jar_label();
else if (part == "jar_letters") jar_letters();
else if (part == "top")         translate([0, 0, -S]) top();
else if (part == "top_rim")     translate([0, 0, -S]) top_rim();
else if (part == "gb")          gb();
else if (part == "gb_icing")    gb_icing();
else if (part == "gb_red")      gb_red();
else if (part == "jar_print")   union() { jar(); jar_label(); jar_letters(); }
else if (part == "top_print")   translate([0, 0, -S]) union() { top(); top_rim(); }
else if (part == "gb_print")    union() { gb(); gb_icing(); gb_red(); }
else if (part == "pressed")     assembly(mx_travel);
else                            assembly(0);
