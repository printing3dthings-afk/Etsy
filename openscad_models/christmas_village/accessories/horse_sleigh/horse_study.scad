// Study (2026-10-13): can a draught horse stand and print with no support and
// still look like a horse? Scott: "If the horse and carriage can't look better
// then leave them out." Faces +x. Second pass: a rounder barrel, a longer
// arched neck, a solid head with a cheek and jaw, a continuous mane.
//
// Every underside is a tube whose axis leans no more than 40 deg from upright,
// or a slab hulled to a smaller one below it. The legs splay a little fore and
// aft, so the gap between them closes in a point under the belly, and the head
// is tucked like a chess knight's, the jaw carried down into the chest.
include <../accessory_lib.scad>
part = "all";
SH = 1.2;
zb = 3.2;

ZK = 8.0;                   // where the legs meet the body
LT = 5.2; LB = 8.2;         // a leg's top and foot, fore or aft of the middle
LY = 2.3; LR = 1.6;         // its side offset and radius
module ball(p, r) translate(p) sphere(r, $fn = 32);
module leg(sx, sy) hull() {
    translate([sx * LT, sy * LY, ZK - 0.01]) cylinder(r = LR + 0.2, h = 0.6, $fn = 24);
    translate([sx * LB, sy * LY, zb - 0.8]) cylinder(r = LR, h = 0.01, $fn = 24);
}
module legs() for (sx = [-1, 1], sy = [-1, 1]) leg(sx, sy);
// feathers round each hoof, narrowing up the leg
module feathers() for (sx = [-1, 1], sy = [-1, 1]) translate([sx * (LB - 0.3), sy * LY, zb - 0.8])
    cylinder(r1 = LR + 0.9, r2 = LR + 0.1, h = 3.4, $fn = 24);

module slab(z, pts) translate([0, 0, z]) linear_extrude(0.01) hull() for (p = pts) translate(p) circle(p[2], $fn = 32);
// the barrel: the legs' tops hulled to a row of balls along the body's middle,
// which round its flanks and back
BAR = [[-8.2, 15.4, 3.8], [11.0, 15.8, 2.4], [-4, 15.6, 4.6], [1, 15.6, 4.7], [5.6, 15.4, 4.3], [8.4, 15.8, 3.4],
       [-7.4, 18.3, 3.4], [-1.5, 18.0, 3.6], [5.2, 19.0, 3.0]];
module body() difference() {
    hull() {
        slab(ZK, [for (sx = [-1, 1], sy = [-1, 1]) [sx * LT, sy * LY, LR + 0.2]]);
        for (b = BAR) ball([b[0], 0, b[1]], b[2]);
    }
    // between fore and hind legs, a point at 40 deg; between left and right
    let (g = LT - LR - 0.2) rotate([90, 0, 0]) linear_extrude(20, center = true)
        polygon([[-g, 0], [-g, ZK], [0, ZK + g / tan(40)], [g, ZK], [g, 0]]);
    let (g = LY - LR - 0.2) rotate([90, 0, 90]) linear_extrude(30, center = true)
        polygon([[-g, 0], [-g, ZK], [0, ZK + g / tan(40)], [g, ZK], [g, 0]]);
}
// the neck: an arch of balls from the chest to the poll, each pair a tube
// leaning no more than 38 deg
NECK = [[7.6, 16.4, 3.6], [10.0, 20.0, 3.0], [11.6, 23.6, 2.6], [12.6, 27.0, 2.3]];
module neck() for (i = [0 : len(NECK) - 2]) hull() { ball([NECK[i][0], 0, NECK[i][1]], NECK[i][2]); ball([NECK[i + 1][0], 0, NECK[i + 1][1]], NECK[i + 1][2]); }
// the head: poll, forehead, cheek, muzzle; the throat fills from the jaw to the
// chest, so no part of it hangs in the air
module head() {
    hull() { ball([12.6, 0, 27.0], 2.3); ball([14.4, 0, 28.0], 1.9); ball([13.8, 0, 24.6], 2.4);   // poll, forehead, cheek
             ball([16.1, 0, 24.1], 1.5); ball([16.8, 0, 21.8], 1.35); }                            // face, muzzle
    hull() { ball([16.8, 0, 21.8], 1.35); ball([13.8, 0, 24.6], 2.4); ball([11.0, 0, 15.8], 2.4); ball([10.0, 0, 20.0], 3.0); }
    for (s = [-1, 1]) hull() { ball([12.9, s * 1.0, 29.2], 0.65); translate([12.4, s * 1.05, 31.2]) sphere(0.25, $fn = 12); }   // ears
}
// a continuous mane along the crest: on each of the neck's balls, up and back
function crest(b) = [b[0] - 0.55 * b[2], 0, b[1] + 0.75 * b[2]];
module mane() for (i = [0 : len(NECK) - 2]) hull() { ball(crest(NECK[i + 1]), 0.9); ball(crest(NECK[i]), 0.9); }
module blaze() hull() { ball([15.0, 0, 28.0], 0.7); ball([17.3, 0, 22.4], 0.75); }
// a short tail, tied up, from the croup down the rump
module tail() { hull() { ball([-10.2, 0, 19.0], 1.4); ball([-11.4, 0, 16.0], 1.3); ball([-10.8, 0, 13.6], 1.0); } }
// the collar: the neck's foot, 0.25 proud, between two planes across the neck
module collar() intersection() {
    hull() { ball([7.6, 0, 16.4], 3.85); ball([10.0, 0, 20.0], 3.25); }
    translate([7.6, 0, 16.4]) rotate([0, 34, 0]) translate([-10, -10, 1.4]) cube([20, 20, 1.8]);
}
// eyes, cut in: teardrops pointing up, so their tops slope
module eyes() for (s = [-1, 1]) translate([14.6, s * 2.2, 26.0]) rotate([90, 0, 0]) linear_extrude(1.4, center = true) tear2d(0.45);

module raw(p) {
    if (p == "body") difference() { union() { legs(); body(); neck(); head(); } eyes(); }
    if (p == "roof") { mane(); tail(); }
    if (p == "trim") { feathers(); blaze(); linear_extrude(zb) square([32, 14], center = true); }
    if (p == "accent") collar();
}
emit();
