// Pie Drum Caddy: the bearing test print (2026-11-10).
// A thrust bearing on 6 mm airsoft BBs. The balls run in a channel in the base,
// on its floor (a top surface: iron it) and under the drum's underside (its bed face:
// as smooth as anything the printer makes). A post in the middle keeps the drum
// centred; nothing holds it down, so it lifts off.
// The coupon is the real channel and post at an 80 mm size; the caddy uses 120.
//   part = "base" | "top" | "plate" | "seated"
part = "plate";
D = 80;                     // outside diameter
BALL = 6.0;                 // airsoft BB (6 mm, 0.20-0.25 g)
RING_R = D / 2 - 10;        // the ball circle
CH_W = BALL + 0.6;          // channel: 0.3 each side
BASE_T = 3;                 // under the channel floor
CH_D = 4;                   // channel depth: the balls stand 2 proud
RIM = BASE_T + CH_D;        // the base's top
POST_R = 8;
POST_GAP = 0.4;
HOLE_COMP = 0.15;           // vertical holes print this much small on the radius
TOP_T = 4;
BOSS_H = 6;
LIFT = BALL - CH_D;         // the drum's underside above the base's top
$fn = 160;

module base() {
    difference() {
        union() {
            cylinder(h = RIM, r = D / 2);
            cylinder(h = RIM + LIFT + TOP_T + BOSS_H - 1, r = POST_R);            // the post
        }
        translate([0, 0, BASE_T]) difference() {
            cylinder(h = CH_D + 1, r = RING_R + CH_W / 2);
            translate([0, 0, -1]) cylinder(h = CH_D + 3, r = RING_R - CH_W / 2);
        }
        // hollow inside the channel's inner wall, down to a 1.6 floor, round the post:
        // it carries nothing and was a third of the print (open on top: no overhang)
        translate([0, 0, 1.6]) difference() {
            cylinder(h = RIM, r = RING_R - CH_W / 2 - 2);
            cylinder(h = RIM, r = POST_R + 2);
        }
        // a chamfer on the post's top so the drum finds it
        translate([0, 0, RIM + LIFT + TOP_T + BOSS_H - 2]) difference() {
            cylinder(h = 2, r = POST_R + 1);
            cylinder(h = 2, r1 = POST_R, r2 = POST_R - 1.5);
        }
    }
}

module top() difference() {
    union() {
        cylinder(h = TOP_T, r = D / 2);
        cylinder(h = TOP_T + BOSS_H, r = POST_R + POST_GAP + 3);
    }
    translate([0, 0, -1]) cylinder(h = 50, r = POST_R + POST_GAP + HOLE_COMP);
    // a finger notch so it lifts off
    for (a = [0, 180]) rotate(a) translate([D / 2, 0, TOP_T]) rotate([0, 90, 0]) cylinder(h = 12, r = 2.5, center = true);
}

module balls() for (i = [0 : 26]) rotate(i * 360 / 27) translate([RING_R, 0, BASE_T + BALL / 2]) sphere(d = BALL, $fn = 32);

if (part == "base") base();
else if (part == "top") top();
else if (part == "seated") { base(); translate([0, 0, BASE_T + BALL]) top(); color("gold") balls(); }
else if (part == "plate") { base(); translate([D + 6, 0, 0]) top(); }
echo("RIM", RIM, "LIFT", LIFT, "drum underside", BASE_T + BALL, "post top", RIM + LIFT + TOP_T + BOSS_H - 1, "boss top", BASE_T + BALL + TOP_T + BOSS_H);
