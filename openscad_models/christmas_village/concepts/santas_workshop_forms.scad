// Santa's Workshop centrepiece: five massing studies, ~190 mm tall.
// Blockouts for choosing a form, not print geometry.
// form = 1 grand hall + clock tower, 2 cross plan, 3 rotunda,
//        4 workshop castle, 5 toy factory
// part = body | roof | trim | accent
form = 1;
part = "body";
$fn = 48;

H_TOTAL = 190;
WIN_PROUD = 0.8;          // glass sits proud of the wall so it reads in a render

module arch2d(w, h) {     // round-headed window outline
    translate([-w/2, 0]) square([w, h - w/2]);
    translate([0, h - w/2]) circle(d = w);
}
// a window on a wall facing -Y at x, sill height z
module glass_y(x, y, z, w, h) {
    translate([x, y - WIN_PROUD, z]) rotate([90, 0, 0]) mirror([0,0,1])
        linear_extrude(WIN_PROUD * 2) arch2d(w, h);
}
module glass_x(x, y, z, w, h) {   // facing -X
    translate([x - WIN_PROUD, y, z]) rotate([90, 0, 90]) mirror([0,0,1])
        linear_extrude(WIN_PROUD * 2) arch2d(w, h);
}
// gable roof along X over a w (x) by d (y) box, eave height z, ridge rise r
module gable_x(w, d, z, r, over = 4) {
    translate([-w/2 - over, 0, z]) rotate([90, 0, 90])
        linear_extrude(w + 2*over)
            polygon([[-d/2 - over, 0], [d/2 + over, 0], [0, r]]);
}
module gable_y(w, d, z, r, over = 4) {
    rotate([0, 0, 90]) gable_x(d, w, z, r, over);
}
module pyramid(s, z, h) { translate([0, 0, z]) linear_extrude(h, scale = 0.02) square(s, center = true); }
module cone(r, z, h) { translate([0, 0, z]) cylinder(r1 = r, r2 = 0.4, h = h); }

// North Pole: striped post, sign board, ball on top
module pole(x, y, h = 110) {
    n = 11; seg = h / n;
    for (i = [0 : n - 1])
        if ((part == "accent" && i % 2 == 0) || (part == "trim" && i % 2 == 1))
            translate([x, y, i * seg]) cylinder(d = 6, h = seg);
    if (part == "trim") translate([x, y, h]) sphere(d = 10);
}
module sign(x, y, z, w = 54, h = 12) {   // board facing -Y
    if (part == "accent") translate([x - w/2, y - 3, z]) cube([w, 3, h]);
}

// ---------------------------------------------------------------- 1 grand hall
module form1() {
    L = 128; D = 66; WALL = 70;
    if (part == "body") {
        translate([-L/2, -D/2, 0]) cube([L, D, WALL]);
        translate([-22, -D/2 - 10, 0]) cube([44, 44, 128]);          // tower
    }
    if (part == "roof") {
        gable_x(L, D, WALL, 40);
        pyramid(52, 128, 34);
    }
    if (part == "trim") {
        for (sx = [-1, 1]) for (k = [0, 1]) {
            glass_y(sx * (30 + k * 20), -D/2, 14, 16, 42);
            mirror([0,1,0]) glass_y(sx * (30 + k * 20), -D/2, 14, 16, 42);
        }
        glass_y(0, -D/2 - 10, 72, 26, 34);                           // clock face slot
        for (sx = [-1, 1]) translate([sx * L/2, 0, 0]) glass_x(0, 0, 18, 30, 48);
        translate([0, 0, 162]) sphere(d = 14);                       // finial
    }
    if (part == "accent") translate([-10, -D/2 - 12, 0]) cube([20, 3, 34]);   // door
    pole(L/2 + 10, -D/2 - 12); sign(0, -D/2 - 10, 44);
}

// ---------------------------------------------------------------- 2 cross plan
module form2() {
    T = 48; WL = 46; WW = 42; WALL = 60;
    if (part == "body") {
        translate([-T/2, -T/2, 0]) cube([T, T, 140]);
        for (a = [0 : 90 : 270]) rotate(a) translate([T/2 - 2, -WW/2, 0]) cube([WL, WW, WALL]);
    }
    if (part == "roof") {
        pyramid(T + 8, 140, 50);
        for (a = [0 : 90 : 270]) rotate(a) translate([T/2 + WL/2 - 2, 0, 0]) gable_x(WL, WW, WALL, 30, 3);
    }
    if (part == "trim") for (a = [0 : 90 : 270]) rotate(a) {
        translate([T/2 + WL - 2, 0, 0]) glass_x(0, 0, 12, 28, 52);
        translate([0, -T/2, 0]) glass_y(0, 0, 92, 22, 36);
    }
    if (part == "accent") rotate(-90) translate([T/2 + WL - 1, -9, 0]) cube([3, 18, 30]);
    pole(T/2 + 8, -T/2 - 8, 120); sign(0, -(T/2 + WL) - 1, 64, 40);
}

// ---------------------------------------------------------------- 3 rotunda
module form3() {
    R = 60; WALL = 74;
    if (part == "body") {
        cylinder(r = R, h = WALL, $fn = 96);
        translate([0, 0, WALL]) cylinder(r = 30, h = 46);           // lantern drum
        translate([-20, -R - 14, 0]) cube([40, 20, 44]);             // porch
    }
    if (part == "roof") {
        translate([0, 0, WALL]) cylinder(r1 = R + 6, r2 = 30, h = 26, $fn = 96);
        cone(34, WALL + 46, 70);
        translate([0, -R - 8, 44]) gable_x(46, 30, 0, 18, 3);
    }
    if (part == "trim") {
        for (a = [15 : 36 : 359]) rotate(a) translate([0, -R, 0]) glass_y(0, 0, 14, 20, 46);
        for (a = [0 : 60 : 359]) rotate(a) translate([0, -30, 0]) glass_y(0, 0, WALL + 10, 10, 24);
        translate([0, 0, WALL + 46 + 70]) sphere(d = 12);
    }
    if (part == "accent") translate([-10, -R - 16, 0]) cube([20, 3, 32]);
    pole(R + 4, -R + 10, 120); sign(0, -R - 14, 52, 46);
}

// ---------------------------------------------------------------- 4 workshop castle
module form4() {
    K = 76; WALL = 96;
    T = [[-1, -1, 120], [1, -1, 150], [-1, 1, 136], [1, 1, 104]];
    if (part == "body") {
        translate([-K/2, -K/2, 0]) cube([K, K, WALL]);
        for (t = T) translate([t[0] * K/2, t[1] * K/2, 0]) cylinder(r = 17, h = t[2]);
        translate([-17, -K/2 - 14, 0]) cube([34, 18, 62]);           // gatehouse
    }
    if (part == "roof") {
        translate([0, 0, WALL]) linear_extrude(8)
            difference() { square(K, center = true); square(K - 10, center = true); }
        pyramid(K - 10, WALL, 44);
        for (t = T) translate([t[0] * K/2, t[1] * K/2, 0]) cone(21, t[2], t[2] == 150 ? 40 : 30);
        translate([0, -K/2 - 5, 62]) gable_x(40, 22, 0, 16, 2);
    }
    if (part == "trim") {
        for (a = [0 : 90 : 270]) rotate(a) for (sx = [-1, 1]) glass_y(sx * 14, -K/2, 40, 16, 42);
        for (t = T) translate([t[0] * K/2, t[1] * K/2 - 17, 0]) glass_y(0, 0, t[2] - 46, 10, 24);
    }
    if (part == "accent") translate([-9, -K/2 - 16, 0]) cube([18, 3, 34]);
    pole(-K/2 - 22, -K/2 - 16, 112); sign(0, -K/2 - 14, 46, 36);
}

// ---------------------------------------------------------------- 5 toy factory
module form5() {
    L = 132; D = 74; WALL = 62; n = 3; tw = L / n;
    if (part == "body") {
        translate([-L/2, -D/2, 0]) cube([L, D, WALL]);
        for (i = [0 : n - 1]) translate([-L/2 + i * tw, -D/2, WALL])   // sawtooth uprights
            cube([tw * 0.12, D, 30]);
    }
    if (part == "roof")
        for (i = [0 : n - 1]) translate([-L/2 + i * tw, D/2, WALL]) rotate([90, 0, 0])
            linear_extrude(D) polygon([[tw * 0.12, 30], [tw, 0], [tw * 0.12, 0]]);
    if (part == "trim") {
        for (i = [0 : n - 1]) translate([-L/2 + i * tw + tw * 0.12, 0, WALL + 2]) rotate([0, 0, 0])
            translate([-WIN_PROUD, -D/2 + 6, 0]) cube([WIN_PROUD * 2, D - 12, 25]);   // glowing skylights
        for (k = [-2 : 2]) glass_y(k * 25, -D/2, 10, 18, 40);
        mirror([0, 1, 0]) for (k = [-2 : 2]) glass_y(k * 25, -D/2, 10, 18, 40);
        translate([L/2, 0, 0]) glass_x(0, 0, 14, 40, 40);
    }
    // three chimney stacks of different heights, the tallest reaching the 190 mark
    stacks = [[-40, 12, 150], [8, 18, 190], [46, 6, 128]];
    for (s = stacks) {
        if (part == "body") translate([s[0], s[1], 0]) cylinder(d = 16, h = s[2] - 10);
        if (part == "accent") translate([s[0], s[1], s[2] - 10]) cylinder(d1 = 20, d2 = 16, h = 10);
    }
    if (part == "accent") translate([-12, -D/2 - 2, 0]) cube([24, 3, 36]);
    pole(-L/2 - 10, -D/2 - 10, 110); sign(0, -D/2, 48, 60);
}

if (form == 1) form1();
if (form == 2) form2();
if (form == 3) form3();
if (form == 4) form4();
if (form == 5) form5();
