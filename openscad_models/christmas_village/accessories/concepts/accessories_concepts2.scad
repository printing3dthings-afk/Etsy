// Victorian village accessories, second batch (2026-10-13): form studies
// placed round the Victorian cottage (at the origin, front to -y) for scale.
// Scott: "do more village accessories". Blockouts for choosing what to make,
// not print geometry.
// part = body (brick red) | roof (slate, iron) | trim (white, snow) | accent (evergreen)
// item = "all" or one of bandstand | town_tree | pillar_box | fountain |
//        horse_sleigh | train | well | signpost | carolers | chestnut_cart
part = "body";
item = "all";
COLS = [["body", "#A8483A"], ["roof", "#2E3440"], ["trim", "#F4F1EA"], ["accent", "#2F6B45"]];
COT = "../../victorian/cottage/victorian_cottage_";
$fn = 40;

module at(p, a = 0) translate(p) rotate([0, 0, a]) children();
module show(name) if (item == "all" || item == name) children();
module snowbase(r, h = 1.2) if ($p == "trim") cylinder(r = r, h = h);
module fir(h) {
    if ($p == "roof") cylinder(r = h * 0.05, h = h * 0.2);
    if ($p == "accent") for (t = [[0.18, 0.4], [0.42, 0.31], [0.64, 0.22]]) translate([0, 0, h * t[0]]) cylinder(r1 = h * t[1], r2 = 0.5, h = h * (1 - t[0]) * 0.75, $fn = 9);
    if ($p == "trim") translate([0, 0, h * 0.95]) sphere(h * 0.035);
}

// ---- bandstand -----------------------------------------------------------------------------
module bandstand() {
    R = 26;
    if ($p == "body") cylinder(r = R, h = 6, $fn = 8);                                         // brick plinth
    if ($p == "trim") {
        translate([0, 0, 6]) cylinder(r = R + 0.8, h = 1.4, $fn = 8);
        for (i = [0 : 7]) rotate(22.5 + 45 * i) translate([R - 2, 0, 7]) cylinder(r = 1.3, h = 30, $fn = 12);   // white columns
        translate([0, 0, 37]) cylinder(r = R + 1, h = 2.4, $fn = 8);
        translate([0, 0, 44]) cylinder(r1 = R - 2, r2 = 6, h = 9, $fn = 8);                                   // snow on the roof
        translate([0, 0, 58]) sphere(2.4);
    }
    if ($p == "roof") {
        translate([0, 0, 39.4]) cylinder(r1 = R + 3, r2 = 2, h = 18, $fn = 8);
        for (i = [0 : 7]) if (i != 6) rotate(45 * i) translate([(R - 2) * cos(22.5) - 0.6, -(R - 2) * sin(22.5), 7]) cube([1.2, 2 * (R - 2) * sin(22.5), 8]);   // railings, open at the steps
    }
    if ($p == "accent") for (i = [0 : 7]) rotate(22.5 + 45 * i) translate([R + 0.6, 0, 33]) rotate([90, 0, 90]) rotate_extrude($fn = 20) translate([2.6, 0]) circle(0.9);   // wreaths
    snowbase(R + 6);
}

// ---- the town Christmas tree ---------------------------------------------------------------
module town_tree() {
    h = 96;
    if ($p == "body") { cylinder(r = 16, h = 8, $fn = 8); for (i = [0 : 5]) rotate(60 * i) translate([19, 0, 1.2]) cube([7, 7, 6], center = true); }   // plinth, presents
    if ($p == "trim") { translate([0, 0, 8]) cylinder(r = 17, h = 1.4, $fn = 8); for (i = [0 : 5]) rotate(60 * i) translate([19, 0, 4.4]) cube([7.4, 1.6, 0.8], center = true); snowbase(28); }
    if ($p == "accent") translate([0, 0, 9]) for (t = [[0.1, 0.36], [0.35, 0.28], [0.58, 0.2], [0.78, 0.12]]) translate([0, 0, h * t[0]]) cylinder(r1 = h * t[1], r2 = 0.8, h = h * (1 - t[0]) * 0.55, $fn = 11);
    if ($p == "body") translate([0, 0, 9]) for (k = [0 : 22]) let (z = 14 + k * 3.8, r = 0.36 * h * (1 - (z - 4) / (h * 0.95)) + 1.6) rotate(k * 137.5) translate([r, 0, z]) sphere(1.8);   // baubles
    if ($p == "trim") translate([0, 0, 9 + h * 0.98]) rotate([90, 0, 0]) linear_extrude(3, center = true) polygon([for (i = [0 : 9]) let (a = 90 + 36 * i, r = i % 2 == 0 ? 7 : 3) [r * cos(a), r * sin(a)]]);
}

// ---- Victorian pillar box ---------------------------------------------------------------------
module pillar_box() {
    if ($p == "body") { cylinder(r = 6.4, h = 4); translate([0, 0, 4]) cylinder(r = 5.6, h = 20); translate([0, 0, 24]) cylinder(r1 = 6.6, r2 = 6.6, h = 2.4); translate([0, 0, 26.4]) scale([1, 1, 0.55]) sphere(6.2); }
    if ($p == "roof") translate([0, -5.4, 18]) cube([6, 1, 1.2], center = true);                           // the slot
    if ($p == "trim") { translate([0, 0, 28]) scale([1, 1, 0.42]) sphere(5.4); snowbase(10); }
}

// ---- frozen fountain -----------------------------------------------------------------------
module fountain() {
    if ($p == "body") difference() { cylinder(r = 24, h = 9, $fn = 12); translate([0, 0, 2]) cylinder(r = 21, h = 9, $fn = 12); }
    if ($p == "roof") translate([0, 0, 5.6]) cylinder(r = 21.2, h = 0.8, $fn = 12);                          // the ice
    if ($p == "body") { cylinder(r = 4, h = 24); translate([0, 0, 22]) cylinder(r1 = 4, r2 = 12, h = 5); translate([0, 0, 27]) cylinder(r = 3, h = 10); translate([0, 0, 35]) cylinder(r1 = 2.6, r2 = 6.4, h = 3); }
    if ($p == "trim") {
        translate([0, 0, 9]) difference() { cylinder(r = 24.6, h = 1.4, $fn = 12); translate([0, 0, -1]) cylinder(r = 20.6, h = 4, $fn = 12); }
        for (i = [0 : 11]) rotate(30 * i) translate([11.4, 0, 18]) cylinder(r1 = 0.3, r2 = 1.2, h = 9);   // icicles off the bowl
        for (i = [0 : 7]) rotate(45 * i + 10) translate([6, 0, 32]) cylinder(r1 = 0.2, r2 = 0.9, h = 6);
        translate([0, 0, 38]) scale([1, 1, 0.5]) sphere(6.4);
        snowbase(30);
    }
}

// ---- horse-drawn sleigh ------------------------------------------------------------------------
module horse() {
    if ($p == "roof") {
        translate([0, 0, 22]) scale([1.9, 0.75, 0.9]) sphere(7);                                      // body
        for (x = [-9, 9], y = [-3, 3]) translate([x, y, 0]) cylinder(r = 1.4, h = 22);              // legs
        translate([11, 0, 26]) rotate([0, 35, 0]) cylinder(r1 = 3.6, r2 = 2.6, h = 11);              // neck
        translate([17, 0, 33]) rotate([0, 128, 0]) scale([1, 0.75, 1]) cylinder(r1 = 3, r2 = 2, h = 9);   // head
        translate([-13, 0, 24]) rotate([0, -150, 0]) cylinder(r1 = 1.8, r2 = 1, h = 10);             // tail
    }
    if ($p == "body") translate([0, 0, 22]) difference() { scale([1.95, 0.8, 0.95]) sphere(7); translate([-20, -10, -2]) cube([40, 20, 20]); translate([-20, -10, -20]) cube([40, 20, 14]); }   // the red blanket
    if ($p == "accent") translate([13, 0, 28]) rotate([0, 35, 0]) rotate_extrude($fn = 20) translate([4.4, 0]) circle(1.2);   // holly collar
}
module sleigh() {
    if ($p == "body") hull() { translate([-14, -9, 6]) cube([24, 18, 8]); translate([-16, -9, 10]) cube([4, 18, 14]); }
    if ($p == "roof") for (y = [-8, 8]) { translate([-18, y - 0.8, 0]) cube([30, 1.6, 1.6]); translate([12, y, 4]) rotate([90, 0, 0]) rotate_extrude(angle = 180, $fn = 20) translate([4, 0]) circle(0.8); for (x = [-12, 4]) translate([x, y - 0.6, 0]) cube([1.2, 1.2, 7]); }
    if ($p == "trim") translate([-12, -8, 14]) cube([20, 16, 1.2]);                                    // a white rug
    if ($p == "accent") translate([-6, 0, 15]) cube([8, 9, 7], center = false);                         // a sack
}
module horse_sleigh() { at([18, 0]) horse(); at([-20, 0]) sleigh(); if ($p == "roof") for (y = [-6, 6]) translate([-8, y, 9]) rotate([0, -12, 0]) cube([22, 0.8, 0.8]); snowbase(0); }

// ---- steam train ---------------------------------------------------------------------------
module wheel(r) rotate([90, 0, 0]) cylinder(r = r, h = 2, center = true);
module train() {
    if ($p == "roof") {
        translate([-60, -7, 0]) cube([120, 14, 1.2]);                                                  // track bed
        translate([6, 0, 10]) rotate([0, 90, 0]) cylinder(r = 7, h = 26);                              // boiler
        translate([-6, -8, 4]) cube([14, 16, 24]);                                                     // cab
        translate([26, 0, 15]) cylinder(r1 = 2.6, r2 = 4.2, h = 13);                                    // chimney
        for (x = [10, 20], y = [-7, 7]) translate([x, y, 6]) wheel(5);
        for (x = [-2, 4], y = [-7, 7]) translate([x, y, 4.4]) wheel(3.6);
        for (x = [-50, -22], y = [-7, 7]) translate([x, y, 4.4]) wheel(3.6);
    }
    if ($p == "body") { translate([-8, -9, 27]) cube([18, 18, 2.4]); translate([-56, -8, 5]) cube([38, 16, 18]); translate([31, -7, 3]) cube([3, 14, 6]); }   // cab roof, carriage, buffer beam
    if ($p == "trim") { translate([-58, -9.5, 23]) cube([42, 19, 2.4]); translate([20, 0, 16]) sphere(3.2); for (x = [-52 : 8 : -26]) translate([x, -8.4, 12]) cube([5, 1, 6]); }   // snow on the carriage roof, dome, lit windows
    if ($p == "accent") translate([33.4, 0, 12]) rotate([0, 90, 0]) rotate_extrude($fn = 20) translate([4, 0]) circle(1.2);   // wreath on the smokebox
}

// ---- village well ---------------------------------------------------------------------------
module well() {
    if ($p == "body") difference() { cylinder(r = 12, h = 12); translate([0, 0, 2]) cylinder(r = 9, h = 12); }
    if ($p == "roof") {
        for (x = [-10.5, 10.5]) translate([x, 0, 0]) cylinder(r = 1.2, h = 32);
        translate([-12, 0, 24]) rotate([0, 90, 0]) cylinder(r = 0.8, h = 24);                        // windlass
        translate([0, 0, 31]) rotate([90, 0, 0]) linear_extrude(26, center = true) polygon([[-15, 0], [15, 0], [0, 11]]);   // roof
        translate([0, 0, 14]) cylinder(r1 = 2.4, r2 = 3, h = 4);                                       // bucket
    }
    if ($p == "trim") { translate([0, 0, 12]) difference() { cylinder(r = 12.4, h = 1.2); translate([0, 0, -1]) cylinder(r = 8.6, h = 4); } translate([0, 0, 31.6]) rotate([90, 0, 0]) linear_extrude(26.4, center = true) polygon([[-12, 2], [12, 2], [0, 11.6]]); snowbase(18); }
    if ($p == "accent") translate([0, -13, 26]) rotate([90, 0, 0]) rotate_extrude($fn = 20) translate([3, 0]) circle(1.1);
}

// ---- signpost -------------------------------------------------------------------------------
module signpost() {
    if ($p == "roof") cylinder(r = 1.6, h = 46);
    if ($p == "body") for (s = [[40, 20, 0], [33, 160, 3], [26, 60, 0]]) translate([0, 0, s[0]]) rotate([0, 0, s[1]]) translate([1, -0.8, 0]) linear_extrude(4.6) polygon([[0, 0], [17, 0], [20, 2.3], [17, 4.6], [0, 4.6]]);
    if ($p == "trim") { translate([0, 0, 46]) scale([1, 1, 0.7]) sphere(2.4); for (s = [[40, 20], [33, 160], [26, 60]]) translate([0, 0, s[0] + 4.6]) rotate([0, 0, s[1]]) translate([1, -0.9, 0]) cube([17, 1.8, 0.9]); snowbase(9); translate([0, 0, 0]) scale([1, 1, 0.5]) sphere(7); }
}

// ---- carolers ---------------------------------------------------------------------------------
module caroler(coat, hat) {
    if ($p == coat) cylinder(r1 = 4.6, r2 = 2.4, h = 13);
    if ($p == "trim") { translate([0, 0, 15]) sphere(2.6); translate([0, 0, 12.6]) cylinder(r = 2.8, h = 1.2); }   // face, white scarf
    if ($p == "roof") { if (hat == 1) translate([0, 0, 16.6]) { cylinder(r = 3.4, h = 0.6); cylinder(r = 2.2, h = 4.6); } else translate([0, 0, 15.6]) scale([1, 1, 0.8]) sphere(3); translate([1.4, -3, 10]) rotate([-30, 0, 0]) cube([4, 0.6, 3], center = true); }   // hat or bonnet, songbook
}
module carolers() {
    at([-9, 2], 10) caroler("body", 1); at([0, -2], 0) caroler("accent", 0); at([9, 2], -10) caroler("roof", 1); at([1, 8], 0) caroler("body", 0);
    if ($p == "roof") at([-16, -2]) { cylinder(r = 0.8, h = 26); translate([0, 0, 26]) cylinder(r1 = 2.2, r2 = 0.6, h = 5, $fn = 6); }
    if ($p == "trim") at([-16, -2]) translate([0, 0, 21]) cylinder(r = 2, h = 5, $fn = 6);
    snowbase(20);
}

// ---- hot chestnut cart -----------------------------------------------------------------------
module chestnut_cart() {
    if ($p == "body") { translate([-12, -8, 10]) cube([24, 16, 10]); translate([-16, -0.8, 12]) cube([4, 1.6, 1.6]); }
    if ($p == "roof") {
        for (y = [-9.4, 9.4]) translate([0, y, 9]) rotate([90, 0, 0]) difference() { cylinder(r = 9, h = 1.6, center = true); cylinder(r = 7.4, h = 3, center = true); }
        for (y = [-9.4, 9.4]) translate([0, y, 9]) for (a = [0 : 45 : 135]) rotate([90, 0, 0]) rotate([0, 0, a]) cube([15, 1, 1.4], center = true);
        translate([2, 0, 20]) cylinder(r1 = 7, r2 = 6, h = 6);                                         // brazier
        translate([2, 0, 26]) cylinder(r = 1.6, h = 18);                                               // its chimney
        translate([-20, -0.8, 0]) cube([1.6, 1.6, 12]);                                                // prop leg
    }
    if ($p == "trim") { translate([2, 0, 44]) cylinder(r1 = 2.6, r2 = 1, h = 2.4); translate([-12, -8, 20]) cube([6, 16, 1]); snowbase(18); }
    if ($p == "accent") translate([-12.6, 0, 15]) rotate([0, 90, 0]) rotate_extrude($fn = 20) translate([3, 0]) circle(1);
}

module scene() {
    show("bandstand")     at([-110, 40]) bandstand();
    show("town_tree")     at([40, 110]) town_tree();
    show("pillar_box")    at([40, -40]) pillar_box();
    show("fountain")      at([-70, -60]) fountain();
    show("horse_sleigh")  at([100, -70], 15) horse_sleigh();
    show("train")         at([0, -150]) train();
    show("well")          at([80, 30]) well();
    show("signpost")      at([-30, -45]) signpost();
    show("carolers")      at([-120, -40]) carolers();
    show("chestnut_cart") at([130, 50], -20) chestnut_cart();
}
if (part == "all") for (q = COLS) let ($p = q[0]) color(q[1]) { scene(); import(str(COT, q[0], ".stl")); }
else let ($p = part) scene();
