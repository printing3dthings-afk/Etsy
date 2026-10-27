// Christmas silhouette scenes for the glow lanterns (2026-10-13). Filled 2D
// shapes, origin bottom-left, mm, drawn at the size they print. Each lantern
// raises them out of its glass; lit from inside, the thicker plastic shows
// dark on the glow and every hole in a shape (a lit window, a bauble) stays
// bright.
//
// Drawn for a 0.4 mm nozzle: no stroke narrower than SW (1.3 mm) and no hole
// narrower than 1.6 mm. The concept scenes (concepts/scenes_lib.scad) had
// 0.25 mm reins and 0.55 mm legs; a slice keeps neither.
$fn = 32;
// the narrowest stroke: under 1.2 mm, product_gate counts it as a wall too thin
// to print (the hex lantern failed on 1.0 mm reins, rays and brims, 2026-10-13)
SW = 1.3;

// ---- pieces ------------------------------------------------------------------------------
module star(r, ri = 0) let (q = ri > 0 ? ri : r * 0.45)
    polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, rr = i % 2 == 0 ? r : q) [rr * cos(a), rr * sin(a)]]);
module moon(r) difference() { circle(r); translate([r * 0.42, r * 0.28]) circle(r * 0.82); }
module ring(r, t = 1.4) difference() { circle(r); circle(r - t); }
// six arms and one pair of branches each, the branches far enough out that the
// gaps between them stay open (0.8 mm) through glow_clean
module flake(r) for (i = [0 : 5]) rotate(60 * i) {
    translate([0, -SW / 2]) square([r, SW]);
    translate([r * 0.64, 0]) for (s = [-1, 1]) rotate(s * 38) translate([0, -SW / 2]) square([r * 0.34, SW]);
}
module tree(h, trunk = true) {
    if (trunk) translate([-h * 0.06 - 0.3, 0]) square([h * 0.12 + 0.6, h * 0.18]);
    for (i = [0 : 2]) let (b = h * (0.14 + 0.25 * i), w = h * (0.38 - 0.09 * i))
        translate([0, b]) polygon([[-w, 0], [w, 0], [0, h - b]]);
}
// a pointed-roof house; lit windows and door
module house(w, h, rh, chim = true) difference() {
    union() {
        square([w, h]);
        translate([0, h]) polygon([[-1.2, 0], [w + 1.2, 0], [w / 2, rh]]);
        if (chim) translate([w * 0.66, h + rh * 0.2]) square([max(w * 0.13, 1.6), rh * 0.75]);
    }
    for (x = [w * 0.16, w * 0.62]) translate([x, h * 0.42]) square([max(w * 0.2, 2), max(h * 0.3, 2.6)]);
    translate([w * 0.42, -0.1]) square([max(w * 0.16, 1.8), h * 0.36]);
}
// a church: nave, tower at its left with a tall spire, arched windows lit
module church(w, h) let (tw = max(w * 0.36, 4))
    difference() {
        union() {
            square([w, h]);
            translate([0, h]) polygon([[-1, 0], [w + 1, 0], [w / 2, h * 0.5]]);
            translate([-tw, 0]) square([tw + 0.1, h * 1.3]);
            translate([-tw, h * 1.3]) polygon([[-0.8, 0], [tw + 0.8, 0], [tw / 2, h * 1.2]]);
            translate([-tw / 2 - SW / 2, h * 2.5 - 0.2]) square([SW, 3.4]);
            translate([-tw / 2 - 1.7, h * 2.5 + 1.4]) square([3.4, SW]);
        }
        translate([-tw / 2, h * 0.92]) arch_hole(tw * 0.42, h * 0.22);
        for (x = [w * 0.28, w * 0.72]) translate([x, h * 0.35]) arch_hole(max(w * 0.17, 1.8), h * 0.38);
        translate([-tw / 2, -0.1]) arch_hole(tw * 0.38, h * 0.38);
    }
module arch_hole(w, h) translate([-w / 2, 0]) { square([w, h - w / 2]); translate([w / 2, h - w / 2]) circle(w / 2); }
module snowman(s) {
    circle(s); translate([0, s * 1.5]) circle(s * 0.72); translate([0, s * 2.55]) circle(s * 0.52);
    translate([-s * 0.5, s * 2.95]) square([s, max(s * 0.18, SW)]);
    translate([-s * 0.32, s * 3.05]) square([s * 0.64, s * 0.72]);
    for (m = [0, 1]) mirror([m, 0]) translate([s * 0.55, s * 1.55]) rotate(28) {
        square([s * 1.25, SW]);
        translate([s * 1.0, 0]) rotate(40) square([s * 0.35, SW]);
    }
    translate([s * 0.2, s * 2.15]) rotate(-20) square([s * 0.9, SW]);   // scarf end
}
// a reindeer, about 10 x 9.5 at s = 1; leaping or standing. Legs and antlers
// keep 1.3 mm at any size: thinner, glow_clean takes them off.
module deer(s = 1, leap = true) let (lw = max(0.72, 1.4 / s), aw = max(0.66, 1.4 / s), bw = max(0.6, 1.3 / s)) scale(s) {
    hull() { translate([2.2, 4.3]) circle(1.5); translate([6.4, 4.6]) circle(1.4); }
    hull() { translate([6.6, 5]) circle(0.8); translate([8.4, 7.4]) circle(0.62); }
    hull() { translate([8.4, 7.5]) circle(0.8); translate([10, 7.2]) circle(max(0.5, 0.7 / s)); }
    for (p = leap ? [[2, 3.6, -150], [2.6, 3.4, -125], [6, 3.8, -40], [6.6, 3.8, -60]]
                  : [[2, 3.4, -95], [2.9, 3.4, -85], [5.8, 3.6, -95], [6.7, 3.6, -85]])
        translate([p[0], p[1]]) rotate(p[2]) translate([0, -lw / 2]) square([3.7, lw]);
    for (a = [62, 104]) translate([8.2, 8]) rotate(a) { translate([0, -aw / 2]) square([3.0, aw]);
        translate([1.6, 0]) rotate(-52) translate([0, -bw / 2]) square([1.6, bw]); }
    translate([0.6, 4.6]) rotate(150) square([1.3, 0.7]);
}
module sleigh(s = 1) let (k = max(0.9, SW / s)) scale(s) {
    polygon([[0, 3], [2, 1.3], [8, 1.3], [10.5, 2.4], [10, 5], [7.5, 4.2], [3.5, 4.2], [2.2, 6.6], [0.6, 6.4]]);
    translate([-0.5, 0]) square([12, k]);
    translate([11.3, 0.45]) circle(0.9);
    for (x = [2.4, 7.8]) translate([x, 0.5]) square([k, 1.2]);
    translate([3.6, 4]) square([3.2, 3.4]);   // the sack
}
// sleigh and team, flying up to the right; n reindeer
module sleigh_team(s, n = 2, ds = 0.82, climb = 1.2) {
    sleigh(s);
    for (i = [0 : n - 1]) translate([s * (13 + i * 9.5), s * (1.5 + i * climb)]) deer(s * ds);
    hull() { translate([s * 11, s * 3.6]) circle(SW / 2); translate([s * (13 + (n - 1) * 9.5 + 6.5), s * (1.5 + (n - 1) * climb + 4.3)]) circle(SW / 2); }
}
// a wrapped gift: lit gaps either side of the ribbon
module gift(w, h) difference() {
    union() { square([w, h]); translate([0, h - 0.2]) square([w, max(h * 0.22, 1.4)]);
        translate([w / 2, h + h * 0.22]) for (s = [-1, 1]) rotate(s * 35) translate([-0.6, 0]) scale([1, 1.4]) circle(1.3); }
    for (s = [-1, 1]) translate([w / 2 + s * (w * 0.12 + 0.5) - 0.5, 0.9]) square([1.0, h - 1.8]);
}
// snow along the ground, its top in soft drifts
module ground(w, base = 3, amp = 1.6, n = 0) let (k = n > 0 ? n : max(2, round(w / 14)))
    translate([0, -0.5]) union() {
        square([w, base + 0.5]);
        for (i = [0 : k]) translate([i * w / k, base + 0.5]) scale([w / k * 0.62, amp]) circle(1, $fn = 24);
    }
module sky(w, h, pts, r = 3.0) for (p = pts) translate([w * p[0], h * p[1]]) star(r, r * 0.5);

// ---- portrait scenes, about 29 x 76 (the hex lantern's panels) --------------------------
module p_church(w, h) {
    translate([w * 0.5, 3]) church(w * 0.44, h * 0.18);
    translate([w * 0.1, 3]) tree(h * 0.16);
    translate([w * 0.3, h * 0.8]) moon(5);
    sky(w, h, [[0.75, 0.9], [0.62, 0.7], [0.18, 0.6], [0.85, 0.62]]);
    ground(w);
}
module p_sleigh(w, h) {
    // one reindeer leaping across the moon: a whole team is too fine at this width
    translate([w * 0.5, h * 0.66]) ring(w * 0.4);
    translate([w * 0.5 - 12.5, h * 0.66 - 9.5]) rotate(8) deer(2.3, true);
    translate([1.5, 3]) house(w * 0.36, 9, 7);
    translate([w * 0.56, 3]) house(w * 0.4, 12, 8);
    sky(w, h, [[0.2, 0.92], [0.85, 0.94], [0.15, 0.36], [0.9, 0.4]], 2.6);
    ground(w);
}
module p_nativity(w, h) {
    translate([w * 0.5, h * 0.84]) star(5, 2);
    for (a = [-62, -90, -118]) translate([w * 0.5, h * 0.84]) rotate(a) translate([5.5, -SW / 2]) square([h * 0.2, SW]);
    // the stable: a roof on two posts, its ends standing on them
    translate([0, 3]) polygon([[0.5, 24], [w / 2, 31], [w - 0.5, 24], [w - 0.5, 22], [w / 2, 28.6], [0.5, 22]]);
    for (x = [0.5, w - 2.0]) translate([x, 3]) square([1.5, 23]);
    // Mary kneeling, the manger, Joseph with his staff
    translate([w * 0.24, 6]) { hull() { circle(3.2); translate([0.8, 5.6]) circle(2.1); } translate([1.2, 9.2]) circle(1.9); }
    translate([w * 0.5, 3]) { polygon([[-3.6, 3.6], [3.6, 3.6], [2.2, 0], [-2.2, 0]]); translate([0, 4.6]) hull() { translate([-1.9, 0]) circle(1.1); translate([1.9, 0]) circle(1.1); } }
    translate([w * 0.76, 3]) { polygon([[-2.6, 0], [2.6, 0], [1.6, 11.5], [-1.6, 11.5]]); translate([0, 13.4]) circle(2); translate([3.0, 0]) square([SW, 17]); }
    sky(w, h, [[0.15, 0.62], [0.85, 0.66], [0.3, 0.95], [0.75, 0.97]], 2.6);
    ground(w);
}
module p_forest(w, h) {
    translate([w * 0.17, 3]) tree(28);
    translate([w - 1, 3.6]) mirror([1, 0]) deer(1.5, false);
    translate([w * 0.66, h * 0.8]) moon(4.5);
    sky(w, h, [[0.2, 0.92], [0.12, 0.7], [0.82, 0.6], [0.5, 0.66]]);
    ground(w);
}
module p_snowman(w, h) {
    translate([w * 0.5, 7.5]) snowman(4.6);
    translate([w * 0.12, 3]) tree(17); translate([w * 0.9, 3]) tree(14);
    for (p = [[0.27, 0.88, 4.8], [0.72, 0.75, 4.6], [0.3, 0.58, 4.4], [0.72, 0.44, 4.4]])
        translate([w * p[0], h * p[1]]) flake(p[2]);
    ground(w);
}
module p_tree(w, h) {
    difference() {
        translate([w * 0.5, 3]) scale([0.68, 1]) tree(h * 0.64);
        // baubles: lit holes
        for (p = [[-0.24, 0.17], [0.2, 0.2], [0.02, 0.3], [-0.14, 0.4], [0.14, 0.45], [0.0, 0.55], [-0.06, 0.66]])
            translate([w * 0.5 + h * 0.64 * p[0] * 0.6, 3 + h * 0.64 * p[1]]) circle(1.2);
    }
    translate([w * 0.5, 3 + h * 0.64 + 1.6]) star(4.2, 1.8);
    translate([w * 0.04, 3]) gift(6.4, 5.4); translate([w * 0.72, 3]) gift(6, 6);
    sky(w, h, [[0.15, 0.9], [0.85, 0.86], [0.12, 0.6], [0.88, 0.58]], 2.6);
    ground(w);
}
module portrait(k, w, h) {
    if (k == 0) p_church(w, h);
    else if (k == 1) p_sleigh(w, h);
    else if (k == 2) p_nativity(w, h);
    else if (k == 3) p_forest(w, h);
    else if (k == 4) p_snowman(w, h);
    else p_tree(w, h);
}

// relief_lib's art_out, each slab grown 0.01: the trimmed copies met corner to
// corner, and two of the hex lantern's slabs came out of linear_extrude as
// meshes CGAL would not close, so the scene lost those slabs without a word
// (2026-10-13). art_in carries the same fix for the same reason.
//
// The drawing is also cleaned first: gaps under 0.8 mm closed, slivers under
// 1.2 mm (SW) dropped. Where two outlines nearly touched (the snowman's waist, a
// 0.14 mm gap), every slab repeated the gap 0.2 mm higher, and the relief came
// out a comb of 0.1 mm teeth: 1.1% of the hex lantern under one bead, and
// nothing a slicer can lay down (2026-10-13). Every line here is drawn SW or
// wider, so the cleaning only touches what could not print anyway.
// Chamfered straight offsets, not rounded ones: rounding at the scenes' $fn = 32
// tripled the art's export time, and at $fn = 8 it turned the moon into an
// octagon; plain mitred ones left sharp corners the slicer propped (the hex
// lantern's stable roof, 2026-10-13).
module glow_clean() offset(delta = 0.4, chamfer = true) offset(delta = -1.0, chamfer = true) offset(delta = 0.6, chamfer = true) children();
// lettering (lc = true) gets a lighter clean: glow_clean's 0.6 grow closes
// any gap under 1.2 mm, and on the Valentine shops' signs it ran CHOCOLATES's
// C into its H and its E into its S (2026-10-27). letter_clean closes only
// gaps under 0.4 and drops only strokes under 0.4.
module letter_clean() offset(delta = 0.2, chamfer = true) offset(delta = -0.4, chamfer = true) offset(delta = 0.2, chamfer = true) children();
module glow_out(h, n, sh = SH, lc = false) let (m = art_n(h, n, sh)) for (i = [0 : m - 1]) let (t0 = i == 0 ? -0.01 : i * h / m - 0.01,
        k = ceil(sh * (i + 1) * h / m / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / m - t0) offset(delta = 0.01) intersection_for(j = [0 : k]) translate([0, j * 0.2])
        if (lc) letter_clean() children(); else glow_clean() children();

// ---- the drum's panorama, about 251 x 80, wrapping all the way round ---------------------
// Nothing crosses x = 0 / w except the ground, so the two ends meet cleanly.
module panorama(w, h) {
    // a village
    translate([5, 3]) house(15, 11, 8);
    translate([34, 3]) church(13, 15);
    translate([50, 3]) house(14, 14, 9);
    translate([68, 3]) house(12, 9, 7, false);
    translate([86, 3]) tree(20);
    // the village Christmas tree, its baubles lit
    translate([112, 3]) difference() {
        scale([0.8, 1]) tree(46);
        for (p = [[-7, 11], [6, 13], [-1, 18], [-5, 24], [4, 27], [0, 33]]) translate(p) circle(1.25);
    }
    translate([112, 50.6]) star(4.4, 1.9);
    // a forest with reindeer
    for (p = [[140, 30], [152, 22], [192, 34], [204, 24]]) translate([p[0], 3]) tree(p[1]);
    translate([158, 3.6]) deer(1.7, false);
    translate([186, 3.6]) mirror([1, 0]) deer(1.5, false);
    // a snowman between two trees
    translate([226, 8]) snowman(5);
    translate([214, 3]) tree(16); translate([241, 3]) tree(19);
    // the sky: the moon, Santa crossing it, stars and snow
    translate([172, h * 0.72]) ring(12.5);
    translate([132, h * 0.56]) rotate(9) sleigh_team(1.45, 2, 0.95, 0.9);
    translate([46, h * 0.8]) moon(6);
    for (p = [[14, 0.6], [26, 0.86], [62, 0.66], [80, 0.9], [96, 0.7], [126, 0.92], [205, 0.92], [216, 0.6], [246, 0.82]])
        translate([p[0], h * p[1]]) star(2.0);
    for (p = [[228, 0.76, 4.8], [241, 0.52, 4.4], [9, 0.88, 4.4]]) translate([p[0], h * p[1]]) flake(p[2]);
    // the snowy ground, all the way round
    ground(w, 3, 1.6, 18);
}

// ---- landscape scenes, about 60 x 52 (the gift box's four sides) ------------------------
module l_village(w, h) {
    translate([3, 3]) house(14, 11, 8);
    translate([w * 0.44, 3]) church(10, 13);
    translate([w * 0.72, 3]) house(10, 12, 7);
    translate([w * 0.95, 3]) tree(15);
    translate([w * 0.2, h * 0.74]) moon(5.5);
    sky(w, h, [[0.08, 0.92], [0.4, 0.86], [0.62, 0.92], [0.78, 0.72], [0.92, 0.88], [0.5, 0.66]]);
    ground(w);
}
module l_sleigh(w, h) {
    translate([w * 0.64, h * 0.64]) ring(13);
    translate([w * 0.0, h * 0.38]) rotate(10) sleigh_team(1.3, 2, 0.95, 1.0);
    translate([3, 3]) house(13, 10, 7); translate([w * 0.32, 3]) tree(15);
    translate([w * 0.66, 3]) house(15, 12, 8);
    sky(w, h, [[0.12, 0.88], [0.3, 0.74], [0.42, 0.95], [0.94, 0.94]]);
    ground(w);
}
module l_snowman(w, h) {
    translate([w * 0.5, 9]) snowman(6);
    translate([w * 0.14, 3]) tree(24); translate([w * 0.84, 3]) tree(20);
    for (p = [[0.16, 0.82, 4.8], [0.4, 0.7, 4.4], [0.66, 0.86, 4.8], [0.87, 0.6, 4.4]])
        translate([w * p[0], h * p[1]]) flake(p[2]);
    ground(w);
}
module l_tree(w, h) {
    difference() {
        translate([w * 0.5, 3]) scale([0.86, 1]) tree(h * 0.74);
        for (p = [[-7, 11], [6, 13], [-1, 18], [-5, 24], [4, 27], [0, 32]]) translate([w * 0.5 + p[0], 3 + p[1]]) circle(1.3);
    }
    translate([w * 0.5, 3 + h * 0.74 + 1.6]) star(4.6, 2);
    translate([w * 0.08, 3]) gift(8, 7); translate([w * 0.2, 3]) gift(6, 9);
    translate([w * 0.7, 3]) gift(7, 8); translate([w * 0.83, 3]) gift(8, 6);
    sky(w, h, [[0.12, 0.8], [0.25, 0.94], [0.8, 0.9], [0.9, 0.7]]);
    ground(w);
}
module landscape(k, w, h) {
    if (k == 0) l_village(w, h);
    else if (k == 1) l_sleigh(w, h);
    else if (k == 2) l_snowman(w, h);
    else l_tree(w, h);
}

// ---- the maker's mark ------------------------------------------------------------------------
// OBC inlaid 0.6 mm into the underside in the lantern's white, grooved like the
// logo (../brand/obc_mark.scad, 2026-10-14): brand_mark() cuts the letters from
// the frame, brand_inlay() is the white that fills them. Subtract both from the
// frame: the inlay stands 0.02 proud of its cut so the welded print closes,
// and the frame must give that up or the two parts overlap.
include <../brand/obc_mark.scad>
module brand_mark(y, h) translate([0, y, 0]) obc_cut(h);
module brand_inlay(y, h) translate([0, y, 0]) obc_inlay(h);
module brand_mark_inside(d, z, size, dp = 0.7) let (m = ceil(dp * SH / 0.2)) translate([0, -d, z]) rotate([90, 0, 180])
    for (i = [0 : m - 1]) let (t1 = dp * (i + 1) / m, k = ceil(SH * t1 / 0.2 - 0.05))
        translate([0, 0, -t1]) linear_extrude(t1 - dp * i / m + (i == 0 ? 0.6 : 0.01)) intersection_for(j = [0 : k]) translate([0, -j * 0.2])
            obc_solid2d(size);     // the logo's letters (2026-10-14); hidden, so engraved, not inlaid
