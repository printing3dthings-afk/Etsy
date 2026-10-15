// WORK IN PROGRESS -- NOT a replacement for mochi_fox_organizer yet.
// The TECHNIQUES here are proven and gate clean (110 x 107 x 114mm, 232 cm3,
// one body, watertight, zero degenerate faces). The PROPORTIONS are not there:
// the ears read too tall and spiky, the tail is a stub rather than a bushy
// curl, and the eyes are too round. v2 is still the better OBJECT; this file
// is the better METHOD, and the two have not met yet.
//
// Mochi Fox v4 -- rebuilt on the BOSL2 subsystems this shop had never used.
// v2's proportions, three techniques replaced:
//
//  1. FILLETED JOINS (join_prism). v2 used hull() for every limb, and hull()
//     is a CONVEX hull, so the muzzle, ears, legs and tail all swelled OUTWARD
//     where they met the body. I told Scott only Blender could fix that. Wrong.
//     THE IDIOM MATTERS: join_prism roots its prism where the +Z axis meets the
//     ORIGIN-CENTRED base, so you aim a limb with rot(from=UP,to=dir) around
//     the base -- NOT with attach(), which applies the placement a second time
//     and blew the first attempt out to 123mm with four loose bodies.
//
//  2. FEATURES BY ANCHOR VECTOR (attach). An arbitrary direction vector lands
//     the child on the parent's real surface, oriented to its normal. v2 needed
//     three attempts and a measured mesh export to place one eye.
//
//  FILLET SIZING, learned the hard way: a fillet must stay small relative to
//  the limb it is filleting. Raising the leg fillet to 5.0 on an 18mm leg and
//  the ear fillet to 4.0 on a 14mm ear produced a mesh with ZERO VOLUME and 8
//  zero-area faces -- BOSL2 warns the fillet is bounded by the curvature it has
//  to fit into, and past that bound join_prism still exports something. Keep it
//  under about a quarter of the prism length.
//
//  3. PARENT/CHILD CUTS (diff + tag), which BOSL2's docs introduce as handling
//     "differences between a parent and child object, something that is
//     impossible with the native difference()".
include <BOSL2/std.scad>
include <BOSL2/rounding.scad>
$fa = 4; $fs = 0.8;

base_w = 110; base_d = 78; base_h = 6; base_round = 32;
body_r = 31.5;  body_z = base_h + body_r;
head_r = 20;    head_c = [0, 9, 33];      // relative to the body centre

module limb(dir, prof_d, len, fil, base_r, sc = 1)
    rot(from = UP, to = dir)
        join_prism(circle(d = prof_d, $fn = 36), base = "sphere", base_r = base_r,
                   length = len, fillet = fil, scale = sc, n = 8);

diff("cut")
union() {
    cuboid([base_w, base_d, base_h], rounding = base_round, edges = "Z", anchor = BOT);
    translate([0, 0, body_z]) {
        // ---- body, and everything filleted into it ------------------------
        sphere(r = body_r);
        for (sx = [1, -1], sy = [1, -1])
            limb([sx*0.40, sy*0.34, -0.86], 14, 18, 3.0, body_r);       // legs
        limb([-0.62, -0.66, 0.42], 27, 42, 6, body_r, 0.58);           // tail

        // ---- head, and everything filleted into IT ------------------------
        translate(head_c) {
            // attach() MUST be a CHILD of the attachable parent -- as a sibling
            // it asserts '$parent_geom != undef'. The eye cutters therefore
            // live inside the sphere's own braces; the limbs, which position
            // themselves against an origin-centred base, stay outside them.
            sphere(r = head_r) {
                for (sx = [1, -1]) {
                    tag("cut") attach([sx*0.46, 0.80, 0.30], BOT, overlap = 1.8)
                        cyl(d = 11, h = 3, rounding = 1.4, $fn = 36);
                    tag("cut") attach([sx*0.76, 0.54, -0.26], BOT, overlap = 0.9)
                        cyl(d = 8, h = 2, rounding = 1.0, $fn = 36);
                }
            }
            limb([0, 0.93, -0.22], 20, 24, 5.0, head_r, 0.46);         // muzzle
            for (sx = [1, -1])
                limb([sx*0.34, 0.02, 0.94], 16, 16, 2.5, head_r, 0.32); // ears
        }
    }
}
