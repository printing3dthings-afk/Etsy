// Christmas glow lanterns: five form studies (2026-10-13). Blockouts for
// choosing a form, not print geometry. Each holds a battery tealight on an
// open base. The scenes stand out of the glass; on the real build they
// would also stand out of its back, so lit they show dark on the glow.
// form = 1 hex carriage lantern, 2 panorama drum, 3 Christmas tree,
//        4 star, 5 gift box
// part = frame | glass | art | accent
include <scenes_lib.scad>
form = 1;
part = "frame";
$fn = 64;
AD = 0.9;                    // the art's depth out of the glass

// place 2D art on a face: u along it, v up, w out of it
module on_face(a, d) rotate([0, 0, a]) translate([d, 0, 0]) rotate([90, 0, 90]) children();
module win2d(w, h) translate([-w / 2, 0]) square([w, h]);
module scene(i, w, h) {
    k = i % 5;
    if (k == 0) skyline(w, h);
    else if (k == 1) sleigh_moon(w, h);
    else if (k == 2) nativity(w, h);
    else if (k == 3) forest(w, h);
    else snowman_scene(w, h);
}

// ---- 1: hex carriage lantern ------------------------------------------------------
module hex_lantern() {
    R = 36; ri = R * cos(30); H = 86; z0 = 8; s = R;
    hexp = [for (i = [0 : 5]) [R * cos(60 * i), R * sin(60 * i)]];
    if ($p == "frame") {
        linear_extrude(z0) offset(r = 2) polygon(hexp);                                   // plinth
        translate([0, 0, z0 + H]) linear_extrude(4) offset(r = 2) polygon(hexp);        // top rail
        translate([0, 0, z0]) linear_extrude(3) difference() { polygon(hexp); offset(-4) polygon(hexp); }
        for (p = hexp) translate([p[0], p[1], z0]) cylinder(r = 2.2, h = H, $fn = 16);  // posts
        translate([0, 0, z0 + H + 4]) cylinder(r1 = R + 2, r2 = 3, h = 30, $fn = 6);     // roof
        translate([0, 0, z0 + H + 34]) { cylinder(r = 3, h = 4); translate([0, 0, 10]) rotate([90, 0, 0]) rotate_extrude($fn = 32) translate([6, 0]) circle(1.6); }
    }
    if ($p == "glass") difference() {
        translate([0, 0, z0]) linear_extrude(H) difference() { polygon(hexp); offset(-1.6) polygon(hexp); }
        translate([0, 0, -1]) cylinder(r = 1, h = 1);
    }
    if ($p == "art") for (k = [0 : 5]) on_face(30 + 60 * k, ri) translate([0, z0 + 4, 0]) linear_extrude(AD)
        intersection() { win2d(s - 7, H - 8); translate([-(s - 7) / 2, 0]) scene(k, s - 7, H - 8); }
    if ($p == "accent") {   // snow on the roof and a holly bow at the top
        translate([0, 0, z0 + H + 4]) intersection() {
            cylinder(r1 = R + 3, r2 = 3.6, h = 30.3, $fn = 6);
            difference() { translate([0, 0, 12]) cylinder(r = R + 4, h = 30); cylinder(r1 = R + 1.5, r2 = 2.4, h = 30, $fn = 6); }
        }
        for (k = [0 : 5]) on_face(30 + 60 * k, ri + 1) translate([0, z0 + H - 3, 0]) linear_extrude(1.5)
            for (i = [-1, 1]) translate([i * 4, 0]) scale([1.6, 1]) circle(2.2);
    }
}

// ---- 2: panorama drum --------------------------------------------------------------
module drum_lantern() {
    R = 40; H = 92; z0 = 7; N = 96; W = 2 * PI * R;
    if ($p == "frame") {
        cylinder(r = R + 2.5, h = z0);
        translate([0, 0, z0 + H]) difference() { cylinder(r = R + 2.5, h = 5); translate([0, 0, -1]) cylinder(r = R - 2, h = 7); }
    }
    if ($p == "glass") translate([0, 0, z0]) difference() { cylinder(r = R, h = H); translate([0, 0, -1]) cylinder(r = R - 1.6, h = H + 2); }
    if ($p == "art") for (i = [0 : N - 1]) let (u = W * (i + 0.5) / N, w = W / N)
        on_face(360 * (i + 0.5) / N, R * cos(180 / N)) translate([0, z0, 0]) linear_extrude(AD)
            intersection() { translate([-w / 2 - 0.02, 0]) square([w + 0.04, H - 6]); translate([-u, 0]) panorama(W, H - 6); }
    if ($p == "accent") {   // snow along the top and a snowy base
        translate([0, 0, z0 + H + 5]) difference() {
            union() { cylinder(r = R + 2.5, h = 1.4); for (i = [0 : 23]) rotate(15 * i) translate([R + 1.5, 0, -2.5]) scale([1, 1.8, 1.4]) sphere(2.2, $fn = 16); }
            translate([0, 0, -6]) cylinder(r = R - 2, h = 10);
        }
        difference() { cylinder(r = R + 6, h = 3); translate([0, 0, -1]) cylinder(r = R - 2, h = 5); }
    }
}
module panorama(W, H) {
    skyline(W * 0.42, H * 0.6);
    translate([W * 0.45, 0]) forest(W * 0.3, H * 0.6);
    translate([W * 0.77, 0]) snowman_scene(W * 0.23, H * 0.6);
    translate([W * 0.62, H * 0.66]) difference() { circle(H * 0.14); circle(H * 0.14 - 1.2); }
    translate([W * 0.5, H * 0.58]) rotate(9) sleigh_team(1.1);
}

// ---- 3: Christmas tree -------------------------------------------------------------
TIERS = [[0, 44, 32, 46], [38, 36, 22, 40], [70, 28, 6, 40]];   // [z, r bottom, r top, h]
module tier(t, g = 0) translate([0, 0, 6 + t[0]]) cylinder(r1 = t[1] + g, r2 = t[2] + g, h = t[3]);
module tree_windows(t, d) for (j = [0 : 5]) let (a = 60 * j + (t[0] > 30 ? 30 : 0), zc = 6 + t[0] + t[3] * 0.4, rc = (t[1] + t[2]) / 2 + 4)
    rotate([0, 0, a]) translate([0, 0, zc]) rotate([90, 0, 90]) linear_extrude(rc + d) children(j % 2);
module tree_lantern() {
    if ($p == "frame") {
        cylinder(r = 30, h = 6);
        difference() {
            for (t = TIERS) tier(t);
            for (t = TIERS) tier(t, -1.8);
            for (t = TIERS) tree_windows(t, 10) { star2d(8, 3.6); circle(6); }
        }
        translate([0, 0, 6 + 96]) cylinder(r = 2.5, h = 10);
    }
    if ($p == "glass") intersection() {
        for (t = TIERS) difference() { tier(t, -1.2); tier(t, -1.8); }
        for (t = TIERS) tree_windows(t, 10) { star2d(8.8, 4); circle(6.8); }
    }
    if ($p == "art") for (t = TIERS) for (j = [0 : 5]) let (a = 60 * j + 30 + (t[0] > 30 ? 30 : 0), zc = 6 + t[0] + t[3] * 0.35)
        rotate([0, 0, a]) translate([(t[1] + t[2]) / 2 + 1.2, 0, zc]) sphere(2.6, $fn = 20);   // baubles
    if ($p == "accent") {
        translate([0, 0, 6 + 108]) rotate([90, 0, 0]) linear_extrude(5, center = true) star2d(11, 4.6);
        for (t = TIERS) translate([0, 0, 6 + t[0]]) difference() { cylinder(r1 = t[1] + 1.2, r2 = t[1] - 1, h = 3); translate([0, 0, -1]) cylinder(r = t[1] - 3, h = 6); }
    }
}

// ---- 4: star ----------------------------------------------------------------------
SR = 62; Sr = 31; SH = 56; sz0 = 5;
function spt(i) = let (a = 90 + 36 * i, r = i % 2 == 0 ? SR : Sr) [r * cos(a), r * sin(a)];
module star_poly(g = 0) offset(delta = g) polygon([for (i = [0 : 9]) spt(i)]);
module star_lantern() {
    if ($p == "frame") {
        linear_extrude(sz0) star_poly(2);
        translate([0, 0, sz0 + SH]) linear_extrude(4) difference() { star_poly(2); star_poly(-4); }
        for (i = [0 : 9]) translate([spt(i)[0], spt(i)[1], sz0]) cylinder(r = 2, h = SH, $fn = 12);
    }
    if ($p == "glass") translate([0, 0, sz0]) linear_extrude(SH) difference() { star_poly(); star_poly(-1.6); }
    if ($p == "art") for (i = [0 : 9]) let (p = spt(i), q = spt(i + 1), m = (p + q) / 2, d = q - p, n = [d[1], -d[0]] / norm(d))
        translate([m[0], m[1], sz0 + SH / 2]) rotate([0, 0, atan2(n[1], n[0])]) rotate([90, 0, 90]) linear_extrude(AD)
            if (i % 2 == 0) snowflake2d(13); else star2d(11, 4.4);
    if ($p == "accent") translate([0, 0, sz0 + SH + 4]) linear_extrude(2) difference() { star_poly(2); star_poly(-4); }
}

// ---- 5: gift box ------------------------------------------------------------------
module gift_lantern() {
    B = 74; H = 68; z0 = 4;
    if ($p == "frame") {
        translate([-B / 2 - 1.5, -B / 2 - 1.5, 0]) cube([B + 3, B + 3, z0]);
        for (x = [-1, 1], y = [-1, 1]) translate([x * B / 2 - 2.2, y * B / 2 - 2.2, z0]) cube([4.4, 4.4, H]);
        translate([-B / 2 - 3, -B / 2 - 3, z0 + H]) difference() { cube([B + 6, B + 6, 12]); translate([3 + 6, 3 + 6, -1]) cube([B - 12, B - 12, 20]); }
    }
    if ($p == "glass") translate([0, 0, z0]) linear_extrude(H) difference() { square(B, center = true); square(B - 3.2, center = true); }
    if ($p == "art") for (k = [0 : 3]) on_face(90 * k, B / 2) translate([0, z0 + 4, 0]) linear_extrude(AD)
        intersection() { win2d(B - 12, H - 8); translate([-(B - 12) / 2, 0]) scene(k + 1, B - 12, H - 8); }
    if ($p == "accent") {   // ribbon round the lid and a bow
        for (r = [0, 90]) rotate(r) translate([-5, -B / 2 - 3.6, z0 + H]) cube([10, B + 7.2, 12.6]);
        translate([0, 0, z0 + H + 12.6]) for (s = [-1, 1]) rotate([0, 0, 45]) translate([s * 9, 0, 6]) scale([1.6, 0.7, 1]) rotate([90, 0, 0]) rotate_extrude($fn = 32) translate([6, 0]) circle(2.2);
        translate([0, 0, z0 + H + 12.6]) sphere(4.2);
    }
}

module lantern(f) {
    if (f == 1) hex_lantern();
    else if (f == 2) drum_lantern();
    else if (f == 3) tree_lantern();
    else if (f == 4) star_lantern();
    else if (f == 5) gift_lantern();
}
// colours for the preview: [frame, glass, art, accent] per form
PAL = [[], ["#2E3440", "#F4F1EA", "#2E3440", "#F4F1EA"], ["#2E3440", "#F4F1EA", "#2E3440", "#F4F1EA"],
       ["#2F6B45", "#F4F1EA", "#C62F3A", "#D4A017"], ["#C62F3A", "#F4F1EA", "#2F6B45", "#D4A017"],
       ["#2F6B45", "#F4F1EA", "#2E3440", "#C62F3A"]];
if (part == "all") for (i = [0 : 3]) let ($p = ["frame", "glass", "art", "accent"][i]) color(PAL[form][i]) lantern(form);
else let ($p = part) lantern(form);
