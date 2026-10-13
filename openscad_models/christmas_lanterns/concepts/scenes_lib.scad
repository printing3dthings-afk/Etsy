// Christmas silhouette scenes for the lantern concepts (2026-10-13).
// Filled shapes, origin bottom-left, mm. Lit from behind they are what goes
// dark on the glow; any hole in them (a lit window) stays bright.
$fn = 32;

module star2d(r, ri = 0) let (q = ri > 0 ? ri : r * 0.42)
    polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, rr = i % 2 == 0 ? r : q) [rr * cos(a), rr * sin(a)]]);
module moon2d(r) difference() { circle(r); translate([r * 0.45, r * 0.25]) circle(r * 0.85); }
module tree2d(h) {
    translate([-h * 0.06, 0]) square([h * 0.12, h * 0.16]);
    for (i = [0 : 2]) let (b = h * (0.12 + 0.27 * i), w = h * (0.42 - 0.1 * i))
        translate([0, b]) polygon([[-w, 0], [w, 0], [0, h - b]]);
}
module house2d(w, h, rh, chim = true, win = true) difference() {
    union() {
        square([w, h]);
        translate([0, h]) polygon([[-1.2, 0], [w + 1.2, 0], [w / 2, rh]]);
        if (chim) translate([w * 0.68, h + rh * 0.25]) square([w * 0.12, rh * 0.75]);
    }
    if (win) for (x = [w * 0.22, w * 0.62]) translate([x, h * 0.45]) square([w * 0.16, h * 0.28]);
    translate([w * 0.42, -0.1]) square([w * 0.16, h * 0.35]);
}
module church2d(w, h) difference() {
    union() {
        square([w, h]);
        translate([0, h]) polygon([[-1, 0], [w + 1, 0], [w / 2, h * 0.45]]);
        translate([-w * 0.32, 0]) square([w * 0.34, h * 1.25]);
        translate([-w * 0.32, h * 1.25]) polygon([[-0.6, 0], [w * 0.34 + 0.6, 0], [w * 0.17 - 0.3, h * 0.95]]);
    }
    translate([-w * 0.24, h * 0.9]) union() { square([w * 0.18, w * 0.2]); translate([w * 0.09, w * 0.2]) circle(w * 0.09); }
    translate([w * 0.4, h * 0.3]) union() { square([w * 0.2, h * 0.35]); translate([w * 0.1, h * 0.35]) circle(w * 0.1); }
}
module snowman2d(s) {
    circle(s); translate([0, s * 1.55]) circle(s * 0.7); translate([0, s * 2.6]) circle(s * 0.5);
    translate([-s * 0.45, s * 3.0]) square([s * 0.9, s * 0.15]); translate([-s * 0.3, s * 3.1]) square([s * 0.6, s * 0.7]);
    for (m = [0, 1]) mirror([m, 0]) translate([s * 0.6, s * 1.6]) rotate(25) square([s * 1.2, s * 0.12]);
}
// a reindeer leaping right, about 10 x 8 at s = 1
module deer2d(s = 1, leap = true) scale(s) {
    hull() { translate([2.2, 4.3]) circle(1.5); translate([6.4, 4.6]) circle(1.4); }
    hull() { translate([6.6, 5]) circle(0.8); translate([8.4, 7.4]) circle(0.6); }
    hull() { translate([8.4, 7.5]) circle(0.8); translate([10, 7.2]) circle(0.45); }
    for (p = leap ? [[2, 3.6, -150], [2.6, 3.4, -125], [6, 3.8, -40], [6.6, 3.8, -60]]
                  : [[2, 3.4, -95], [2.8, 3.4, -85], [5.8, 3.6, -95], [6.6, 3.6, -85]])
        translate([p[0], p[1]]) rotate(p[2]) square([3.6, 0.55]);
    for (a = [60, 100]) translate([8.2, 8]) rotate(a) { square([2.4, 0.4]); translate([1.4, 0]) rotate(-50) square([1.1, 0.35]); }
    translate([0.6, 4.6]) rotate(150) square([1.2, 0.6]);
}
module sleigh2d(s = 1) scale(s) {
    polygon([[0, 3], [2, 1.2], [8, 1.2], [10.5, 2.4], [10, 5], [7.5, 4.2], [3.5, 4.2], [2.2, 6.6], [0.6, 6.4]]);
    translate([-0.5, 0]) square([12, 0.55]);
    translate([11.3, 0.3]) circle(0.7);
    for (x = [2.5, 8]) translate([x, 0.4]) square([0.5, 1]);
    translate([3.6, 4]) square([3.2, 3.4]);   // the sack
}
module sleigh_team(s = 1) {
    sleigh2d(s);
    for (i = [0 : 2]) translate([s * (13 + i * 9.5), s * (1.5 + i * 1.2)]) deer2d(s * 0.82);
    for (i = [0 : 2]) translate([s * 11, s * 3.6]) rotate(atan2(1.2 * 2, 9.5 * 2)) square([s * (2 + 9.5 * i + 5), s * 0.25]);
}
module skyline(w, h) {
    tree2d(18); translate([8, 0]) house2d(16, 12, 9);
    translate([28, 0]) church2d(14, 20);
    translate([48, 0]) house2d(14, 15, 8); translate([66, 0]) tree2d(14); translate([72, 0]) house2d(12, 10, 7);
    for (i = [0 : floor(w / 90)]) translate([90 * i, 0]) children();
    translate([w * 0.78, h * 0.78]) moon2d(7);
    for (p = [[10, 0.8], [30, 0.62], [55, 0.9], [62, 0.6], [45, 0.72]]) translate([p[0], h * p[1]]) star2d(1.6);
    translate([0, -0.5]) square([w, 3]);
}
module nativity(w, h) {
    // the stable
    translate([w * 0.5, h * 0.92]) star2d(4.5, 1.6);
    for (a = [-60, -90, -120]) translate([w * 0.5, h * 0.92]) rotate(a) translate([5, -0.25]) square([h * 0.18, 0.5]);
    difference() {
        translate([w * 0.12, 0]) union() {
            polygon([[-3, h * 0.48], [w * 0.38, h * 0.68], [w * 0.79, h * 0.48], [w * 0.79, h * 0.44], [w * 0.38, h * 0.62], [-3, h * 0.44]]);
            square([1.6, h * 0.46]); translate([w * 0.74, 0]) square([1.6, h * 0.46]);
        }
    }
    // Mary kneeling, the manger, Joseph with his staff
    translate([w * 0.3, 4]) { hull() { circle(4); translate([1, 7]) circle(2.6); } translate([1.4, 11]) circle(2.2); }
    translate([w * 0.5, 0]) { polygon([[-5, 5], [5, 5], [3, 0], [-3, 0]]); translate([0, 6]) hull() { translate([-2.6, 0]) circle(1.3); translate([2.6, 0]) circle(1.3); } }
    translate([w * 0.7, 0]) { polygon([[-3.5, 0], [3.5, 0], [2, 15], [-2, 15]]); translate([0, 17.4]) circle(2.4); translate([4.2, 0]) square([0.9, 22]); }
    translate([0, -0.5]) square([w, 3]);
}
module forest(w, h) {
    for (p = [[4, 22], [14, 30], [26, 18], [52, 26], [64, 20], [w - 6, 24]]) translate([p[0], 0]) tree2d(p[1]);
    translate([33, 0]) deer2d(1.1, false);
    translate([w * 0.2, h * 0.8]) moon2d(5);
    for (p = [[40, 0.85], [56, 0.7], [20, 0.62]]) translate([p[0], h * p[1]]) star2d(1.4);
    translate([0, -0.5]) square([w, 3]);
}
module sleigh_moon(w, h) {
    // the moon stays bright (no plastic), only its rim is drawn; the team crosses it
    translate([w * 0.55, h * 0.62]) difference() { circle(h * 0.27); circle(h * 0.27 - 1.2); }
    translate([w * 0.12, h * 0.5]) rotate(8) sleigh_team(0.85);
    translate([2, 0]) house2d(14, 10, 8); translate([w - 18, 0]) house2d(16, 12, 9); translate([w * 0.42, 0]) tree2d(16);
    translate([0, -0.5]) square([w, 3]);
}
module snowman_scene(w, h) {
    translate([w * 0.5, 7]) snowman2d(5.5);
    translate([6, 0]) tree2d(24); translate([w - 12, 0]) tree2d(20);
    for (p = [[0.2, 0.8], [0.5, 0.9], [0.8, 0.75], [0.35, 0.6], [0.7, 0.55]]) translate([w * p[0], h * p[1]]) star2d(1.5);
    translate([0, -0.5]) square([w, 3]);
}
module snowflake2d(r) for (i = [0 : 5]) rotate(60 * i) {
    translate([0, -0.4]) square([r, 0.8]);
    for (t = [0.45, 0.72]) translate([r * t, 0]) for (s = [-1, 1]) rotate(s * 45) translate([0, -0.3]) square([r * 0.28, 0.6]);
}
