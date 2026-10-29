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
//   part = tin | tin_snow | lid | lid_holly | lid_snow
//          cookie | cookie_icing | cookie_red | cookie_green
//          tin_print | lid_print | cookie_print   (merged colours, for the gate)
//          assembly | pressed                     (preview, stand-in switch)
// The lid exports standing on its own floor; everything else where it prints.
//
// The nest is the cookie's outline 0.6 larger, as deep as the cookie ever
// travels, so the cookie is guided all the way down: press his head or a foot
// and he still goes down level instead of tipping off the stem.
//
// Colours: tin red, icing and snowflakes white, cookie brown, holly and
// gumdrops green. The red gumdrop, bow, cheeks and berries share the tin's
// red, and the pupils the cookie's brown: four filaments, one AMS.

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
ICE_W  = 1.2;                   // a piped line: three beads at its foot

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

// A piped line is round on top, not flat: each 0.2 layer of it is drawn in by
// a half-ellipse hw wide and h tall, read at the layer's middle so the top
// layer keeps a bead's width (a 1.2 line tops out at 0.58). Detail standard:
// level heights snap to the 0.2 layer, so heights are drawn in 0.2 steps.
module piped(h, hw = 0.6) let (n = round(h / 0.2)) for (k = [0 : n - 1])
    translate([0, 0, k * 0.2 - (k == 0 ? 0.01 : 0)])
        linear_extrude(0.2 + (k == 0 ? 0.02 : 0.01))
            offset(delta = -hw * (1 - sqrt(1 - pow((k + 0.5) / n, 2)))) children();

// A baked edge: the top rolls over through a quarter circle of 1.4, in 0.2
// steps. (1.0 read as a cut-out shape rather than a cookie.)
EDGE_R = 1.4;
module cookie_gross() {
    difference() {
        union() {
            linear_extrude(CT - EDGE_R) gb_outline();
            for (k = [0 : round(EDGE_R / 0.2) - 1]) let (z = CT - EDGE_R + k * 0.2,
                    // max(0): at the top layer 7 x 0.2 is 1.4000000000000001,
                    // the root went NaN, offset() drew nothing, and the icing
                    // floated 0.2 over a cookie with no top (2026-10-29)
                    d = EDGE_R - sqrt(max(0, pow(EDGE_R, 2) - pow((k + 1) * 0.2, 2))))
                translate([0, 0, z - 0.01]) linear_extrude(0.21) offset(delta = -max(d, 0.02)) gb_outline();
        }
        mx_cap_cut();
    }
}

// ---------- icing, on the cookie's flat top ----------
// Every gap between two pieces of icing is at least two beads, measured from
// the drawing: eye to cheek 1.11, cheek to smile 1.05, cheek to the outline
// 0.98, bow to the top gumdrop 0.95, the last gumdrop to the outline 1.15.
module outline_band() difference() { offset(delta = -1.6) gb_outline(); offset(delta = -1.6 - ICE_W) gb_outline(); }
module eyes2d() for (s = [-1, 1]) translate([s * 3.4, 15.0]) circle(1.6);
module smile2d() pipe2d([for (x = [-1.7 : 0.425 : 1.71]) [x, 10.0 + 0.2 * x * x]], 1.1);
function limb_dir(a, b) = atan2(b.y - a.y, b.x - a.x);
module zigzags2d() for (s = [-1, 1]) {
    // wrists and ankles, the way gingerbread is piped: across each limb near
    // its end, meeting the outline band on both sides
    scale([s, 1]) let (c = arm_a + 0.72 * (arm_b - arm_a))
        pipe2d(zigzag(c, limb_dir(arm_a, arm_b), 2.3, 0.75, 4), 1.0);
    scale([s, 1]) let (c = leg_a + 0.70 * (leg_b - leg_a))
        pipe2d(zigzag(c, limb_dir(leg_a, leg_b), 2.5, 0.75, 4), 1.0);
}
module icing2d() union() { outline_band(); eyes2d(); smile2d(); zigzags2d(); }
module cheeks2d() for (s = [-1, 1]) translate([s * 4.3, 11.3]) circle(1.1);
// a bow tie at the neck: two rounded wings and a knot
module bow2d() translate([0, 5.2]) {
    offset(r = 0.4) for (s = [-1, 1]) polygon([[s * 0.5, 0], [s * 2.9, 0.95], [s * 2.9, -0.95]]);
    circle(0.8);
}

module on_top(h, z = CT) translate([0, 0, z]) piped(h) children();
module cookie_icing() on_top(ICE) icing2d();
// brown pupils, standing on the white of each eye in the cookie's own colour,
// well off centre (down and inward), so each eye reads as looking at the smile.
// Centred, at r 0.8, 1.05 and 1.25, they left an even white margin and read as
// rings, spectacles rather than eyes (renders, 2026-10-29). The white is whole
// underneath, so however thin it shows beside the pupil, it prints as white
// top layers, not a sub-bead ring.
module pupils() for (s = [-1, 1]) translate([s * (3.4 - 0.4), 15.0 - 0.45, CT + ICE - 0.01])
    rotate_extrude($fn = 32) polygon([[0, 0], [0.85, 0], [0.78, 0.2], [0.55, 0.38], [0, 0.44]]);
btn_y = [1.0, -2.5, -6.0];
// a gumdrop's shoulders, not a dome: wide foot, sloping sides, round top
module gumdrop(y) translate([0, y, CT - 0.01]) rotate_extrude($fn = 40)
    polygon([[0, 0], [1.55, 0], [1.45, 0.6], [1.2, 1.15], [0.8, 1.5], [0, 1.65]]);
module cookie_red()   { on_top(0.6) cheeks2d(); on_top(ICE) bow2d(); gumdrop(btn_y[1]); }
module cookie_green() { gumdrop(btn_y[0]); gumdrop(btn_y[2]); }
module cookie() { cookie_gross(); pupils(); }

// ---------- the tin and its lid ----------
// The tin is a cup with a 1.2 lip round its top (0.6 failed the gate's wall
// floor); the lid's spigot drops 2 mm inside the lip, then flares out to the
// lid band at 40 deg (2.0 out over 2.4 up): a square step would be a level
// ledge all round. A real tin's rolled beads run round its foot and its top
// edge; the top one climbs out at 40 deg (0.5 over 0.6), the foot one stands
// on the bed.
module tin_solid() rotate_extrude($fn = 240) polygon([
    [0, 0], [TR + 0.5, 0], [TR + 0.5, 0.8], [TR, 1.4], [TR, S - 0.6], [TR + 0.5, S],
    [TR + 0.5, S + JOINT], [TR - LIP_W, S + JOINT], [TR - LIP_W, S], [0, S]]);
module lid_solid() rotate_extrude($fn = 240) polygon(concat(
    [[0, S], [SPIG_R, S], [SPIG_R, S + JOINT], [LID_R, S + JOINT + 2.4]],
    [for (k = [0 : 4]) let (z = RIM - 0.8 + (k + 1) * 0.16) [LID_R - 0.8 + sqrt(max(0, 0.64 - pow(z - (RIM - 0.8), 2))), z]],
    [[0, RIM]]));

module snowflake2d(arm = 3.6) {
    circle(0.9, $fn = 20);
    for (k = [0 : 5]) rotate(k * 60) {
        pipe2d([[0, 0], [0, arm]], 0.9);
        for (s = [-1, 1]) pipe2d([[0, arm * 0.58], [s * arm * 0.29, arm * 0.875]], 0.85);
    }
}
SNOW_N = 10;
SNOW_ARM = 3.2;
// Clear of both beads, skirt and all: the foot bead tops out at 1.4, the skirt
// reaches 1.05 under the lowest arm, the top bead starts at S - 0.6. At arm 3.6
// the bottom arms ran into the foot bead and were shaved to slivers: 35
// fidelity flags at z 1.4-2.0 (2026-10-29).
SNOW_Z = 1.4 + 1.05 + SNOW_ARM + 0.45;
// Raised flat on a tangent plane, 0.35 inside the wall: across a 7.3 mm flake
// the wall curves away 0.22, so it meets the wall all round and stands 0.7
// proud at its middle. The skirt under every stroke climbs SH, so none of it overhangs.
// A dot between each pair, above and below centre, as on a printed tin.
module on_wall(a, z, h) rotate([0, 0, a]) translate([TR - 0.35, 0, z]) rotate([90, 0, 90]) art_skirt(h, 1) children();
module tin_snow_raw() for (i = [0 : SNOW_N - 1]) let (a = 90 + i * 360 / SNOW_N) {
    on_wall(a, SNOW_Z, 1.05) rotate(i % 2 * 30) snowflake2d(SNOW_ARM);
    for (z = [SNOW_Z - 2.25, SNOW_Z + 2.25]) on_wall(a + 180 / SNOW_N, z, 1.0) circle(0.95, $fn = 24);
}

// ---------- the lid's top, round the cookie ----------
// Holly in the two corners between his head and his arms, little snowflakes at
// his head, his feet and beside his legs. Each was placed against the nest's
// drawn outline: no piece comes within 0.45 of the nest or of the rolled edge.
HOLLY = [15.2, 19.8];
module holly_leaf() offset(r = 0.35) offset(r = -0.35) difference() {
    scale([3.5, 1.7]) circle(1, $fn = 48);
    for (i = [-1, 0, 1], s = [-1, 1]) translate([i * 2.05, s * 2.15]) circle(0.95, $fn = 24);
}
function dir(a) = [cos(a), sin(a)];
module sprig2d(berries = false) for (m = [0, 1]) mirror([m, 0]) let (t = atan2(HOLLY.y, HOLLY.x) - 90)
    if (berries) for (b = [[0, 0], [-1.0, 1.15], [1.15, 0.75]]) translate(HOLLY + b) circle(1.0, $fn = 24);
    else for (u = [t + 15, t + 165]) translate(HOLLY + 3.9 * dir(u)) rotate(u) holly_leaf();
LID_FLAKES = [[0, 26.2], [0, -24.2], [21, -9.5], [-21, -9.5]];
module lid_holly() translate([0, 0, RIM]) difference() { piped(0.8) sprig2d(); translate([0, 0, -1]) linear_extrude(3) sprig2d(true); }
module lid_berries() translate([0, 0, RIM]) for (m = [0, 1]) mirror([m, 0, 0])
    for (b = [[0, 0], [-1.0, 1.15], [1.15, 0.75]]) translate(concat(HOLLY + b, [-0.01]))
        rotate_extrude($fn = 32) polygon([[0, 0], [1.0, 0], [0.95, 0.6], [0.7, 1.15], [0.35, 1.4], [0, 1.45]]);
module lid_snow() translate([0, 0, RIM]) piped(0.6) for (c = LID_FLAKES) translate(c) rotate(30) snowflake2d(2.1);

// the nest's top edge is broken by a 0.4 chamfer, in two 0.2 steps
module nest() {
    translate([0, 0, P - 0.01]) linear_extrude(RIM - P + 1) offset(delta = NEST) gb_outline();
    for (k = [1, 2]) translate([0, 0, RIM - 0.6 + k * 0.2]) linear_extrude(1) offset(delta = NEST + k * 0.2) gb_outline();
}
// tipped back to look underneath, OBC reads with the cookie's feet toward you.
// Inset 0.15: the walls the letters leave between them grow from 0.95 to 1.25,
// over the gate's 1.2 floor, as on the nativity.
module tin_mark() translate([0, -19, 0]) obc_engrave(6, depth = 0.8, inset = 0.15, ridges = false);

module tin() difference() { tin_solid(); mx_well_cut(S); tin_mark(); }
module tin_snow() difference() { tin_snow_raw(); tin_solid(); }
module lid() union() { difference() { lid_solid(); nest(); mx_plate_cut(S); } lid_berries(); }

module assembly(press = 0) {
    color("#B3262E") tin();
    color("white") tin_snow();
    color("#B3262E") lid();
    color("#3E8E4A") lid_holly();
    color("white") lid_snow();
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
else if (part == "lid_holly")    translate([0, 0, -S]) lid_holly();
else if (part == "lid_snow")     translate([0, 0, -S]) lid_snow();
else if (part == "lid_print")    translate([0, 0, -S]) union() { lid(); lid_holly(); lid_snow(); }
else if (part == "cookie")       cookie();
else if (part == "cookie_icing") cookie_icing();
else if (part == "cookie_red")   cookie_red();
else if (part == "cookie_green") cookie_green();
else if (part == "tin_print")    union() { tin(); tin_snow(); }
else if (part == "cookie_print") union() { cookie(); cookie_icing(); cookie_red(); cookie_green(); }
else if (part == "pressed")      assembly(mx_travel);
else                             assembly(0);
