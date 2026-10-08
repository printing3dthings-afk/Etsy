// Gingerbread Cottage -- building #1 of the Gingerbread village, redrawn round
// (Scott, 2026-09-30: "Christmas village keeps a rounder shape ... Yes redo
// the cottages round too", and picked this layout from four). The square
// cottage, gated and finished, is in the recycle bin (data/trash,
// 20260930-003) and at commit 7de06df.
//
// A cupcake. A round gingerbread drum, fluted like a cupcake's paper, under a
// chocolate dome; icing piped round the dome's rim with drips running down
// the drum; gumdrops round the dome and one on top. A chocolate-bar door
// between two candy canes, four round peppermint windows, peppermints lying on
// the snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane.
//
// THE DOME. A room's ceiling must rise at 45 deg or more to print, and a
// half-sphere cannot cover a cone at 58 deg: its crown is too low. So the
// ceiling is the village's 58 deg cone and the dome is drawn over it, 39 mm
// tall on a 30.5 mm radius, with 5 mm of chocolate over the cone's point. It
// is solid between them; the slicer fills that with infill.
//
// The machinery is the round shop-house's and the turret house's; the square
// cottage's icing, canes and peppermints.
//
// COLOUR PARTS, ONE PRINT (gingerbread_cottage.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the drum and its flutes
//   roof    chocolate: the dome, the chocolate-bar door
//   trim    icing: snow base, the dome's rim and its drips, window frames,
//           panes and bars, the door frame and its beads, the canes' white,
//           the peppermints' white
//   accent  candy red: gumdrops, cane stripes, the windows' and peppermints'
//           stripes

include <BOSL2/std.scad>
include <../../relief_lib.scad>

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// ---- the plan -----------------------------------------------------------------------------
Rw       = 26;              // the drum's face (48.6 clear inside)
wall     = 1.68;
r_in     = Rw - wall;
plinth_h = 8;
SH       = 1.2;
fl_ang   = 52;
tp       = tan(58);

module sweep() rotate_extrude($fn = FN) children();
module stadium(r) circle(r = r, $fn = FN);

// ALONG THE OUTLINE (the shop-house's, round): s is the distance round the
// circle of radius R from the front, anticlockwise seen from above
function sper(R) = 2 * PI * R;
function spos(R, s) = let (t = s - floor(s / sper(R)) * sper(R), a = -90 + t / R * 180 / PI) [R * cos(a), R * sin(a), a];
function s_at(a, R) = let (t = (a + 90) / 180 * PI * R) t - floor(t / sper(R)) * sper(R);
module splace(R, s, z) let (p = spos(R, s)) translate([p[0], p[1], z]) rotate([0, 0, p[2] + 90]) rotate([90, 0, 0]) children();
module srelief(R, s, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    splace(R, s + uc, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }
module sclip(R, d) intersection() { children(); linear_extrude(300) stadium(R + d); }

// ---- relief (the cottage's) --------------------------------------------------------------
module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b, sh = SH) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up(sh) translate([0, 0, a]) linear_extrude(b - a) translate([0, -sh * d0]) children();
}
module relief_up(d0, d1, sh = SH) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1, sh) children(1);
    }
}

// ---- the dome -------------------------------------------------------------------------------
Hc    = 38;                 // the ceiling's eave line, at the wall's inside
Rr    = Rw + 4.5;           // the dome's rim, where it is widest
z_rim = Hc + 5;
z_top = 82;                 // 5.1 over the ceiling cone's point (76.9)
B     = z_top - z_rim;
kf    = Rw - 0.8;           // the flare's foot, inside the wall
zf    = z_rim - 1.0 - (Rr - kf) * tan(fl_ang);   // under the rim, rising 52 deg from the wall
function z_ceil(v) = Hc + (r_in - v) * tp;
function z_dome(v) = v >= Rr ? z_rim : z_rim + B * sqrt(1 - pow(v / Rr, 2));
function z_flare(v) = zf + (v - kf) * tan(fl_ang);
module dome2d() polygon(concat(
    [[0, z_ceil(0)], [r_in, z_ceil(r_in)], [kf, z_ceil(kf)], [kf, zf], [Rr, z_rim - 1.0], [Rr, z_rim]],
    [for (i = [1 : 60]) let (v = Rr * (1 - i / 60)) [v, z_dome(v)]]));
module dome() sweep() dome2d();
// THE RIM'S ICING: all the dome below a wavy line round it
function ic_z(a) = z_rim + 3.2 + 1.1 * sin(a * 9) + 0.6 * sin(a * 23 + 40);
module icing_zone() let (n = 216, P = concat(
        [for (i = [0 : n - 1]) let (a = 360 * i / n) [45 * cos(a), 45 * sin(a), 20]],
        [for (i = [0 : n - 1]) let (a = 360 * i / n) [45 * cos(a), 45 * sin(a), ic_z(a)]],
        [[0, 0, 20], [0, 0, z_rim + 3.2]]))
    polyhedron(P, concat(
        [for (i = [0 : n - 1]) let (j = (i + 1) % n) [n + i, n + j, j, i]],
        [for (i = [0 : n - 1]) let (j = (i + 1) % n) [i, j, 2 * n]],
        [for (i = [0 : n - 1]) let (j = (i + 1) % n) [n + j, n + i, 2 * n + 1]]));
module rim_icing() intersection() { dome(); icing_zone(); }
module chocolate() difference() { dome(); icing_zone(); }
module below_ceil() sweep() polygon([[0, -5], [45, -5], [45, z_ceil(45)], [0, z_ceil(0)]]);

// ---- the drum ----------------------------------------------------------------------------------
// its top 0.6 up into the dome: the ceiling line inside, the flare outside
module drum_wall() sweep() polygon([[r_in - 0.3, plinth_h - 0.5], [Rw, plinth_h - 0.5], [Rw, z_flare(Rw) + 0.6],
                                     [kf, z_flare(kf) + 0.6], [kf, z_ceil(kf) + 0.6], [r_in - 0.3, z_ceil(r_in - 0.3) + 0.6]]);
// FLUTES, like the pleats of a cupcake's paper: half-round ribs 0.9 proud,
// vertical, so nothing about them overhangs; stopped under the rim's flare
n_fl = 40;
module flutes() for (i = [0 : n_fl - 1]) rotate([0, 0, 360 * (i + 0.5) / n_fl])
    translate([Rw, 0, plinth_h - 0.5]) cylinder(r = 0.9, h = z_flare(Rw + 0.9) + 0.6 - plinth_h + 0.5, $fn = 16);

// ---- piped icing ----------------------------------------------------------------------------
bead_r  = 1.2;
bead_sp = 2.0;
function arch_path(a, hgt, o, sp, bottom = true) =
    let (A = a + o, b0 = bottom ? 2 * A : 0, b1 = b0 + hgt + o, b2 = b1 + PI * A, P = b2 + hgt + o,
         n = round(P / sp))
    [for (i = [0 : n - 1]) let (t = i * P / n)
        t < b0 ? [-A + t, -o] :
        t < b1 ? [A, -o + (t - b0)] :
        t < b2 ? let (q = (t - b1) / A * 180 / PI) [A * cos(q), hgt + A * sin(q)] :
                 [-A, hgt - (t - b2)]];
module beads(pts, r = bead_r) for (p = pts) translate(p) circle(r = r);
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9 + 0.9;           // frames stand clear of the flutes (0.9) by the cottage's 0.9

// ---- the round peppermint windows ------------------------------------------------------------------
// [s, sill, radius]: two at the front beside the canes, two at the back
WR = 4.8;
WINS = [[s_at(-52, Rw), 15, WR], [s_at(232, Rw), 15, WR], [s_at(38, Rw), 15, WR], [s_at(142, Rw), 15, WR]];
pr = WR + 3.2;              // the peppermint ring's outer radius
module w_outline(w) translate([0, w[2]]) circle(r = w[2], $fn = 64);
module w_bars(w) { translate([-mull/2, -3]) square([mull, 40]); translate([-20, w[2] - 1.1]) square([40, 2.2]); }
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
module w_ring(w) relief_up(-0.4, fr_t) { translate([0, w[2]]) circle(r = pr, $fn = 64); offset(r = 0.3) w_outline(w); }
module w_frames(red = false) sclip(Rw, fr_t) for (w = WINS) srelief(Rw, w[0], w[1], pr + 0.6)
    if (red) intersection() { w_ring(w); translate([0, w[2], -5]) linear_extrude(10) pepper_wedges(pr); }
    else w_ring(w);
module w_muntins() sclip(Rw, 0.4) for (w = WINS) srelief(Rw, w[0], w[1], w[2] + 1.2)
    relief_up(-0.4, 0.4) intersection() { offset(r = 0.6) w_outline(w); w_bars(w); }
module w_openings() for (w = WINS) splace(Rw, w[0], w[1]) translate([0, 0, -wall - 2]) linear_extrude(wall + 6) w_outline(w);
module w_holes() for (w = WINS) srelief(Rw, w[0], w[1], w[2] + 0.6) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) w_outline(w);
module w_glass() intersection() {
    for (w = WINS) splace(Rw, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) w_outline(w);
    linear_extrude(200) stadium(Rw - 0.2);
}

// ---- the door: a chocolate bar ---------------------------------------------------------------------
door_a = 4.4;
door_h = 12;
module rshell(r0, r1) difference() { linear_extrude(200) stadium(r1); translate([0, 0, -1]) linear_extrude(202) stadium(r0); }
// the leaf scored into squares by V grooves, their upper faces leaning 50 deg
module door_leaf() intersection() {
    splace(Rw, 0, plinth_h) difference() {
        translate([0, 0, -wall - 1]) linear_extrude(wall + 3)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
        translate([-0.5, -1, 0.9]) cube([1, door_h + door_a + 4, 3]);
        for (zg = [4.2, 8.4, 12.6]) hull() {
            translate([-door_a - 1, zg - 0.6, 1.4]) cube([2 * door_a + 2, 1.2, 2]);
            translate([-door_a - 1, zg - 0.01, 0.9]) cube([2 * door_a + 2, 0.02, 2.5]);
        }
    }
    rshell(r_in + 0.15, Rw + 1.2);
}
// the door's strips are set a quarter off its centre line: with one strip's
// edge on it, the cuts met the leaf's crown point along edges, non-manifold
module door_frame() sclip(Rw, fr_t) srelief(Rw, 0, plinth_h, door_a + fr_w + bead_r + 0.85) relief_up(-0.4, fr_t) {
    union() {
        intersection() { offset(r = fr_w) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
        intersection() { beads(arch_path(door_a, door_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
    }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
module door_opening() splace(Rw, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 6) polygon(arch_pts(door_a, door_h));
module door_hole() srelief(Rw, 0, plinth_h, door_a + 0.85) relief_hole(-0.4, -0.25, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));

// ---- candy canes either side of the door, crooks turned in over it -----------------------------------
cane_s = 10.8;  cane_w = 2.6;  cane_h = 18.5;  cane_R = 3;
module cane2d(dir) {
    translate([-cane_w/2, -0.5]) square([cane_w, cane_h + 0.5]);
    translate([dir * cane_R, cane_h]) intersection() {
        difference() { circle(r = cane_R + cane_w/2); circle(r = cane_R - cane_w/2); }
        translate([-10, 0]) square([20, 10]);
    }
    translate([2 * dir * cane_R - cane_w/2, cane_h - 1.8]) square([cane_w, 1.8]);
}
module stripes2d() for (i = [-12 : 12]) translate([0, i * 3.4]) rotate(35) translate([-20, 0]) square([40, 1.5]);
// the stripes are the cane's own solid cut to bands, in the same strips
module canes(stripes = false) sclip(Rw, fr_t + 0.5) for (s = [-1, 1]) srelief(Rw, s * cane_s, plinth_h, cane_R * 2 + cane_w + 0.6)
    if (stripes) intersection() { relief_up(-0.4, fr_t + 0.5) cane2d(-s); translate([0, 0, -5]) linear_extrude(10) stripes2d(); }
    else relief_up(-0.4, fr_t + 0.5) cane2d(-s);

// ---- drips from the rim, down the drum, clear of the door and canes ----------------------------------
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
d_s = cane_s + cane_R * 2 + 3;
DR = [for (i = [0 : 29]) let (s = d_s + i * (sper(Rw) - 2 * d_s) / 29) [s, 1.8 + 3.0 * rnd(i, 70), 2.2 + 0.5 * rnd(i, 110)]];
module drips() sclip(Rw, fr_t) for (d = DR) srelief(Rw, d[0], z_flare(Rw) + 1, 2.2) relief_up(-0.4, fr_t) drip2d(d[1], d[2]);

// ---- gumdrops: round the dome and one on top ----------------------------------------------------------
// a dome on a cone carried down into the chocolate, its foot 4 under the
// surface so its rim stays buried on the downhill side
gd_v = 12;                  // up where the dome is 29 deg: at 17 (41 deg) they stood up as pink bullets
GD = concat([for (k = [0 : 7]) let (a = 22.5 + 45 * k) [gd_v * cos(a), gd_v * sin(a)]], [[0, 0]]);
module gumdrops() difference() {
    for (p = GD) let (z = z_dome(norm(p))) hull() {
        translate([p[0], p[1], z + 1.2]) sphere(r = 2.8, $fn = 32);
        translate([p[0], p[1], z - 4.0]) cylinder(r = 3.6, h = 0.01, $fn = 32);
    }
    below_ceil();
}

// ---- rooms ---------------------------------------------------------------------------------------------
module room() sweep() polygon([[0, -2], [r_in, -2], [r_in, Hc], [0, z_ceil(0)]]);

// ---- the snow base ---------------------------------------------------------------------------------------
// 8.5 out: at 6.5 its rounded edge began at 30.7, under the peppermints
// (out to 32.4), and each hung over it and drew support from the table
module base2d() circle(r = Rw + 8.5, $fn = FN);
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[(Rw + 1.5) * cos(15), (Rw + 1.5) * sin(15), 6, 3.5, 3.0], [(Rw + 1.5) * cos(95), (Rw + 1.5) * sin(95), 7, 3.5, 2.8],
          [(Rw + 1.5) * cos(185), (Rw + 1.5) * sin(185), 5, 3.5, 2.4]];
// PEPPERMINTS lying on the snow either side of the door
PM = [[(Rw + 3.8) * cos(-62), (Rw + 3.8) * sin(-62), 2.6], [(Rw + 3.8) * cos(-121), (Rw + 3.8) * sin(-121), 2.2]];
module peppermints(stripes = false) for (p = PM) translate([p[0], p[1], plinth_h - 0.2]) linear_extrude(1.4)
    if (stripes) union() { intersection() { circle(r = p[2]); pepper_wedges(p[2]); } circle(r = 0.8); } else circle(r = p[2]);
module base() {
    base_slab();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.5]) intersection() {
            scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -2.4) base2d();
    }
}
// centred in the band between the room's opening (-24.3) and the base's edge (-32.5)
module brand_mark() translate([0, -28.4, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- parts ----------------------------------------------------------------------------------------------
module body_raw() { drum_wall(); flutes(); }
module roof_raw() {
    difference() { chocolate(); room(); }
    door_leaf();
}

// ---- RELIEF FOR A ONE-COLOUR PRINT (2026-10-08) -------------------------------------------------
// The canes', the peppermint windows' and the peppermints' stripes were colour
// alone, flush: a white print lost them. Each now stands out 0.3 on its relief's
// flat front, its lower edges climbing SH per 1 out, so nothing hangs.
module cane_stripes_up() sclip(Rw, fr_t + 0.81) for (s = [-1, 1]) srelief(Rw, s * cane_s, plinth_h, cane_R * 2 + cane_w + 0.6)
    translate([0, 0, fr_t + 0.5]) art_out(0.3, 2) intersection() { top_face(fr_t + 0.5) cane2d(-s); stripes2d(); }
module w_stripes_up() sclip(Rw, fr_t + 0.31) for (w = WINS) srelief(Rw, w[0], w[1], pr + 0.6)
    translate([0, 0, fr_t]) art_out(0.3, 2) intersection() {
        top_face(fr_t) difference() { translate([0, w[2]]) circle(r = pr, $fn = 64); offset(r = 0.3) w_outline(w); }
        translate([0, w[2]]) pepper_wedges(pr);
    }
module pepper_stripes_up() for (p = PM) translate([p[0], p[1], plinth_h + 1.19]) linear_extrude(0.31)
    intersection() { circle(r = p[2] - 0.3); pepper_wedges(p[2]); }

module accent_raw() {
    gumdrops();
    canes(true);
    peppermints(true);
    w_frames(true);
    cane_stripes_up();
    w_stripes_up();
    pepper_stripes_up();
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() { rim_icing(); room(); }
            drips();
            canes();
            peppermints();
            w_frames();
            w_muntins();
            door_frame();
        }
        room();
        brand_mark();
    }
    difference() { w_glass(); room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); w_openings(); w_holes(); door_opening(); door_hole();
        trim_raw(); accent_raw(); roof_raw();
    }
}

if      (part == "none")   ;
else if (part == "body")   body_part();
else if (part == "roof")   roof_part();
else if (part == "trim")   trim_part();
else if (part == "accent") accent_part();
else if (part == "union")  union() { body_part(); roof_part(); trim_part(); accent_part(); }
else if (part == "chk_body_roof")    intersection() { body_part(); roof_part(); }
else if (part == "chk_body_trim")    intersection() { body_part(); trim_part(); }
else if (part == "chk_body_accent")  intersection() { body_part(); accent_part(); }
else if (part == "chk_roof_trim")    intersection() { roof_part(); trim_part(); }
else if (part == "chk_roof_accent")  intersection() { roof_part(); accent_part(); }
else if (part == "chk_trim_accent")  intersection() { trim_part(); accent_part(); }
else {
    color("#C68642") body_part();
    color("#5A3825") roof_part();
    color("#F7F3EE") trim_part();
    color("#D7263D") accent_part();
}
