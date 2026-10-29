// Gingerbread Tin Clicker (2026-10-29), for MakerWorld's "Click Into
// Celebration". An iced gingerbread cookie lies in its own cookie-shaped nest
// in a round Christmas tin; press his tummy and a real MX switch clicks.
//
// Three prints and one plate-mount Cherry MX (or clone) switch:
//   the tin     a cup; its open well takes the switch's body and pins
//   the lid     sits on the tin; the switch plate is its floor, flat on the
//               bed, and the cookie's nest is cut down to it
//   the cookie  prints face up; its underside hides the switch housing and
//               carries the socket, so nothing hangs in the air
//
//   part = tin | tin_snow | lid | cookie | cookie_icing | cookie_red | cookie_green
//          tin_print | lid_print | cookie_print   (merged colours, for the gate)
//          assembly | pressed                     (preview, stand-in switch)
// The lid exports standing on its own floor; everything else where it prints.
//
// The nest is the cookie's outline 0.6 larger, as deep as the cookie ever
// travels, so the cookie is guided all the way down: press his head or a foot
// and he still goes down level instead of tipping off the stem.
//
// Colours: tin red, icing and snowflakes white, cookie brown, gumdrop green.
// The red gumdrops and cheeks share the tin's red: four filaments, one AMS.

SH = 1.2;
include <../../christmas_village/relief_lib.scad>
use <../../brand/obc_mark.scad>
include <../clicker_lib.scad>

part = "assembly";
$fa = 2; $fs = 0.3;

S      = 1.6 + well_h;          // the tin's top face, 10.5: a 1.6 floor under the well
P      = S + mx_plate_t;        // plate top, 12.0
CZ     = mx_cap_z(P);           // cookie underside at rest, 15.5
CT     = cav_h + cap_floor;     // cookie thickness, 6.2
RIM    = CZ + CT - 2.2;         // the tin's lid: the cookie stands 2.2 proud
                                // at rest and sits 1.8 below it pressed
TR     = 30.0;                  // tin radius
LID_R  = TR + 0.6;              // the lid band stands 0.6 proud
SPIG_R = TR - LIP_W - JOINT_CLR; // the lid's spigot, inside the tin's lip
NEST   = 0.6;                   // clearance round the cookie
ICE    = 0.8;                   // icing proud of the cookie: four layers
ICE_W  = 0.9;                   // a piped line: two beads

echo(str("plate ", P, "  cookie rest ", CZ, " pressed ", mx_cap_z_down(P),
         "  rim ", RIM, "  cookie top ", CZ + CT, "  clears plate pressed by ",
         mx_cap_z_down(P) - P));

// ---------- the cookie's outline, belly on the switch ----------
arm_a = [8, 4.5];  arm_b = [18.5, 8.2];     // shoulder, hand (x mirrored)
leg_a = [5.6, -8]; leg_b = [9.2, -19.8];    // hip, foot
head_c = [0, 13];  head_r = 9.5;

module gb_outline() offset(r = -2) offset(r = 2) union() {
    translate(head_c) circle(head_r);
    // the core is the cavity plus 1.8 of wall, so the cookie always closes
    // round the switch housing, by construction rather than by luck
    offset(r = 1.8) square(cav_w, center = true);
    hull() for (s = [-1, 1]) translate([s * 5.5, -7]) circle(4.5);
    for (s = [-1, 1]) {
        hull() { translate([s * arm_a.x, arm_a.y]) circle(4.4); translate([s * arm_b.x, arm_b.y]) circle(4.2); }
        hull() { translate([s * leg_a.x, leg_a.y]) circle(4.6); translate([s * leg_b.x, leg_b.y]) circle(4.8); }
    }
}

// Rounded top edge in layer-height steps, a quarter circle of 1.0: a level
// detail snaps to the 0.2 layer, so it is drawn in 0.2 steps.
module cookie_gross() {
    difference() {
        union() {
            linear_extrude(CT - 1.0) gb_outline();
            for (k = [0 : 4]) let (z = CT - 1.0 + k * 0.2, d = 1.0 - sqrt(1 - pow((k + 1) * 0.2, 2)))
                translate([0, 0, z - 0.01]) linear_extrude(0.21) offset(delta = -max(d, 0.02)) gb_outline();
        }
        mx_cap_cut();
    }
}

// ---------- icing, on the cookie's flat top ----------
module outline_band() difference() { offset(delta = -1.3) gb_outline(); offset(delta = -1.3 - ICE_W) gb_outline(); }
module eyes2d() for (s = [-1, 1]) translate([s * 3.3, 14.8]) circle(1.25);
module smile2d() pipe2d([for (x = [-2.2 : 0.55 : 2.21]) [x, 9.9 + 0.2 * x * x]], ICE_W);
function limb_dir(a, b) = atan2(b.y - a.y, b.x - a.x);
module zigzags2d() for (s = [-1, 1]) {
    // wrists and ankles, the way gingerbread is piped: across each limb near
    // its end, meeting the outline band on both sides
    scale([s, 1]) let (c = arm_a + 0.72 * (arm_b - arm_a))
        pipe2d(zigzag(c, limb_dir(arm_a, arm_b), 2.4, 0.75, 4), 0.85);
    scale([s, 1]) let (c = leg_a + 0.70 * (leg_b - leg_a))
        pipe2d(zigzag(c, limb_dir(leg_a, leg_b), 2.6, 0.75, 4), 0.85);
}
module icing2d() union() { outline_band(); eyes2d(); smile2d(); zigzags2d(); }
// cheeks clear of the eyes, smile and band by at least two beads
module cheeks2d() for (s = [-1, 1]) translate([s * 4.8, 10.9]) circle(1.2);

module on_top(h) translate([0, 0, CT - 0.01]) linear_extrude(h + 0.01) children();
module cookie_icing() on_top(ICE) icing2d();
module cookie_cheeks() on_top(0.6) cheeks2d();
btn_y = [2.0, -2.2, -6.4];
module gumdrop(y) translate([0, y, CT - 0.01]) intersection() {
    scale([1, 1, 1.4 / 1.7]) sphere(1.7, $fn = 32);
    translate([-2, -2, 0]) cube([4, 4, 2]);
}
module cookie_red()   { cookie_cheeks(); gumdrop(btn_y[0]); gumdrop(btn_y[2]); }
module cookie_green() gumdrop(btn_y[1]);
module cookie() cookie_gross();

// ---------- the tin and its lid ----------
// The tin is a cup with a 1.2 lip round its top (0.6 failed the gate's wall
// floor); the lid's spigot drops 2 mm inside the lip, then flares out to the
// lid band at 40 deg (2.0 out over 2.4 up): a square step would be a level ledge all round. The groove left
// between the lip and the flare is the seam a real tin has there.
module tin_solid() difference() {
    cylinder(h = S + JOINT, r = TR, $fn = 240);
    translate([0, 0, S]) cylinder(h = JOINT + 1, r = TR - LIP_W, $fn = 240);
}
module lid_solid() rotate_extrude($fn = 240) polygon(concat(
    [[0, S], [SPIG_R, S], [SPIG_R, S + JOINT], [LID_R, S + JOINT + 2.4]],
    [for (k = [0 : 4]) let (z = RIM - 0.8 + (k + 1) * 0.16) [LID_R - 0.8 + sqrt(max(0, 0.64 - pow(z - (RIM - 0.8), 2))), z]],
    [[0, RIM]]));

module snowflake2d() {
    circle(0.9, $fn = 20);
    for (k = [0 : 5]) rotate(k * 60) {
        pipe2d([[0, 0], [0, 4.1]], 0.9);
        for (s = [-1, 1]) pipe2d([[0, 2.4], [s * 1.25, 3.65]], 0.85);
    }
}
SNOW_N = 10;
SNOW_Z = 6.4;
// Raised flat on a tangent plane, 0.4 inside the wall: across a 9 mm flake the
// wall curves away 0.35, so it meets the wall all round and stands 0.7 proud at
// its middle. The skirt under every stroke climbs SH, so none of it overhangs.
module tin_snow_raw() for (i = [0 : SNOW_N - 1]) rotate([0, 0, 90 + i * 360 / SNOW_N])
    translate([TR - 0.4, 0, SNOW_Z]) rotate([90, 0, 90]) art_skirt(1.1, 1) rotate(i % 2 * 30) snowflake2d();

module nest() translate([0, 0, P - 0.01]) linear_extrude(RIM - P + 1) offset(delta = NEST) gb_outline();
// tipped back to look underneath, OBC reads with the cookie's feet toward you.
// Inset 0.15: the walls the letters leave between them grow from 0.95 to 1.25,
// over the gate's 1.2 floor, as on the nativity.
module tin_mark() translate([0, -19, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);

module tin() difference() { tin_solid(); mx_well_cut(S); tin_mark(); }
module tin_snow() difference() { tin_snow_raw(); tin_solid(); }
module lid() difference() { lid_solid(); nest(); mx_plate_cut(S); }

module assembly(press = 0) {
    color("#B3262E") tin();
    color("white") tin_snow();
    color("#B3262E") lid();
    mx_mock(S, press);
    translate([0, 0, CZ - press]) {
        color("#9A5B2E") cookie();
        color("white") cookie_icing();
        color("#B3262E") cookie_red();
        color("#3E8E4A") cookie_green();
    }
}

if      (part == "tin")          tin();
else if (part == "tin_snow")     tin_snow();
else if (part == "lid")          translate([0, 0, -S]) lid();
else if (part == "lid_print")    translate([0, 0, -S]) lid();
else if (part == "cookie")       cookie();
else if (part == "cookie_icing") cookie_icing();
else if (part == "cookie_red")   cookie_red();
else if (part == "cookie_green") cookie_green();
else if (part == "tin_print")    union() { tin(); tin_snow(); }
else if (part == "cookie_print") union() { cookie(); cookie_icing(); cookie_red(); cookie_green(); }
else if (part == "pressed")      assembly(mx_travel);
else                             assembly(0);
