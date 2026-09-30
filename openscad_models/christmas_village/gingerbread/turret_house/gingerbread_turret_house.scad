// Gingerbread Turret House -- the Gingerbread village's first building with
// "more shape" (Scott, 2026-09-30, picked from four shapes against his
// reference photos in ../../references/). A gingerbread house whose roofs
// swoop out into curls of white icing at three heights: the main roof, a
// little front-gabled porch on two peppermint-stick columns, and a round
// turret at the front corner that leans a little, under a bell-shaped
// chocolate cone and a candy-cane spire that bends over at the top.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane.
//
// The machinery is the gingerbread cottage's (../cottage/), itself the
// chapel's, with every trap in .claude/skills/3d-print-design/SKILL.md
// Techniques 79 and 80 applied from the start. What is new is commented here.
//
// COLOUR PARTS, ONE PRINT (gingerbread_turret_house.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the house, the turret and the porch walls
//   roof    chocolate: the three roofs and their scallop tiles, the door
//   trim    icing: snow base, the roofs' curled icing eaves, rakes and
//           drips, corner beads, window frames, panes and bars, the porch
//           columns, the spire, the peppermints' white
//   accent  candy red: gumdrops, the stripes on the columns and the spire,
//           the peppermints' stripes
//
// FRAMES. The main house is centred on the origin, ridge along x, so its
// swooping eaves face front (-y) and back. The turret stands on the
// front-left corner; lean() tips everything of it outward. The porch is on
// the front, right of centre.

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// ---- the main house ----------------------------------------------------------------
W        = 58;
D        = 50;              // 46.6 clear inside: the tealight's 46 mm circle
Wh = W/2;  Dh = D/2;
wall     = 1.68;
corner_r = 2.5;
plinth_h = 8;
SH       = 1.2;
H        = 42;              // the main ceiling's eave line
r_ang    = 58;
tp       = tan(r_ang);
y_in     = Dh - wall;
tr       = 2.52;
tv       = tr / cos(r_ang);
fl_ang   = 52;
cp_lo = -0.2;  cp_hi = 2.2;
xs       = Wh - wall + 0.4; // the roof slab's ends, 0.4 into the gables
function zc(v) = H + (y_in - abs(v)) * tp;    // ceiling, v across the ridge
function zs(v) = zc(v) + tv;                  // the straight roof's top
// THE SWOOP. All three roofs are one profile, R = [eave line, inner half-width,
// ceiling slope, slab depth, swoop start, tip, tip angle, chocolate edge],
// across v (distance from the ridge, or radius on the turret). The ceiling
// stays straight; the top eases from the roof's pitch to ka and kicks out
// past the wall, so the tip stands well above where a straight roof would
// end. Under the eave the profile rises at 52 deg from the wall to the tip,
// so every layer stands on the one below. Chocolate to the edge vw; past it,
// and in a band along the underside, icing.
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang);
sb = 1.8;                   // the icing band under the eave, measured up
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
// the whole roof, ceiling to top, across the ridge (both halves); kv0 is where
// the underside's 52 deg line runs in to, inside the wall
module R_full(R, kv0) polygon(concat([[-R[5], R_tipb(R)]], R_curve(R, -R[5], R[5], 80),
    [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)], [kv0, R_zc(R, kv0)], [0, R_zc(R, 0)], [-kv0, R_zc(R, kv0)], [-kv0, R_fl(R, kv0)]]));
// what of it is chocolate
module R_choc(R, kv0) polygon([[-R[7], R_fl(R, R[7]) + sb], [-kv0, R_fl(R, kv0) + sb], [-kv0, -10], [kv0, -10],
    [kv0, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [-R[7], 300]]);
// the icing eave, one side
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
// the same for a radius (the turret): half profiles, r >= 0
module R_full_r(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
module R_choc_r(R, kv0) polygon([[0, -10], [kv0, -10], [kv0, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);

RM = [H, y_in, tp, tv, Dh - 6, Dh + 6, 20, Dh + 4];
kv0 = Dh - corner_r - 0.3;  // so at the rounded corners the eave still stands on the wall
function ztop(v) = R_top(RM, v);
zf0 = R_fl(RM, Dh);         // where the eave's underside meets the wall

// ---- placement and relief (the cottage's) ------------------------------------------------
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
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
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// ---- the turret ---------------------------------------------------------------------------
tx = -Wh + 4;  ty = -Dh + 4;
rt   = 10.5;
rti  = rt - wall;
z_tw = 86;                  // its cone's eave line
tpc  = tan(60);
tvc  = tr / cos(60);
function zcc(r) = z_tw + (rti - r) * tpc;
function zcs(r) = zcc(r) + tvc;
RC = [z_tw, rti, tpc, tvc, 6.5, rt + 3.5, 20, rt + 1.7];
kv0c = rti + 0.3;
// THE LEAN. The turret tips outward, away from the house, 0.05 mm per mm
// (2.9 deg): a shear, so every layer is still a circle, 0.035 mm further out
// than the one below.
lean_k = 0.05;
module lean() multmatrix([[1, 0, -lean_k / sqrt(2), lean_k / sqrt(2) * plinth_h],
                          [0, 1, -lean_k / sqrt(2), lean_k / sqrt(2) * plinth_h], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// on the turret's face at angle th: local z out, y up
module tplace(th, z, r = rt) translate([tx + r * cos(th), ty + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
module turret_cut() lean() translate([tx, ty, -1]) cylinder(r = rt - 0.3, h = 200);

// ---- the porch -----------------------------------------------------------------------------
pc  = 6;                    // centre, x
pw  = 8;                    // half-width to the side walls' faces
pwi = pw - wall;
pd  = 8;
y_pf = -Dh - pd;            // its front
// Hp puts the porch eave's underside, at kv0p, above the columns' capitals
// (spring + 0.6): lower, it hung beside the round shafts
Hp  = 26;
function zpc(u) = Hp + (pwi - abs(u)) * tp;
function zps(u) = zpc(u) + tv;
RP = [Hp, pwi, tp, tv, pw - 2, pw + 3, 20, pw + 1.4];
kv0p = pw - 0.3;
spring = 20;                // the front arch springs from the columns here
col_r  = 2.1;
col_c  = [pc - 6, pc + 6];  // the columns' x
col_y  = y_pf + col_r;
ar_a   = 6 - col_r;         // the arch's half-span

// ---- rooms --------------------------------------------------------------------------------
module below_ceil() yz(-60, 60) polygon([[-40, -5], [40, -5], [40, zc(40)], [0, zc(0)], [-40, zc(40)]]);
module main_room() intersection() {
    translate([-(Wh - wall), -y_in, -2]) cube([2 * (Wh - wall), 2 * y_in, 200]);
    below_ceil();
}
module turret_room() lean() translate([tx, ty, 0]) rotate_extrude($fn = 96)
    polygon([[0, -2], [rti, -2], [rti, z_tw], [0, zcc(0)]]);
module room() { main_room(); turret_room(); }
module porch_below_ceil() translate([pc, 0, 0]) xz(y_pf - 1, -Dh + 1) polygon([[-20, -5], [20, -5], [20, zpc(20)], [0, zpc(0)], [-20, zpc(20)]]);
// the porch's inside, open at the front through the arch; it stops short of
// the house wall, where the door's frame stands
module porch_room() difference() {
    intersection() {
        translate([pc - pwi, y_pf + wall, plinth_h]) cube([2 * pwi, -Dh - 1.2 - y_pf - wall, 60]);
        porch_below_ceil();
    }
    // clear of the columns: cut by it, their stripes were left standing loose
    for (c = col_c) translate([c - col_r - 0.01, y_pf - 1, 0]) cube([2 * col_r + 0.02, col_y + col_r - y_pf + 1.01, spring + 1]);
}

// ---- walls ----------------------------------------------------------------------------------
// The gables rise to the roof's top (1 over it, under the coping) as far as
// kv0; past that the icing eave is the gable's end.
module gable_keep() for (m = [0, 1]) mirror([m, 0, 0])
    yz(Wh - wall, Wh + 5) polygon(concat([[-kv0, -5], [kv0, -5]], [for (p = R_curve(RM, kv0, -kv0, 40)) [p[0], p[1] + 1]]));
module main_walls() intersection() {
    translate([0, 0, plinth_h - 0.5]) linear_extrude(200) rect([W, D], rounding = corner_r);
    union() { below_ceil(); gable_keep(); }
}
// a ring, stopping 0.3 inside the room: drawn solid to the apex, its top was
// the room's own cone, and the two left a sheet of zero thickness there
module turret_walls() lean() translate([tx, ty, 0]) rotate_extrude($fn = 128)
    polygon([[rti - 0.3, plinth_h - 0.5], [rt, plinth_h - 0.5], [rt, zcc(rt)], [rti - 0.3, zcc(rti - 0.3)]]);
// Porch: two side walls up to its ceiling, and a front gable wall, the
// pointed arch cut through it, up to the roof's top as far as kv0p.
module porch_walls() {
    translate([pc, 0, 0]) for (m = [0, 1]) mirror([m, 0, 0]) intersection() {
        translate([pwi, y_pf, plinth_h - 0.5]) cube([wall, -Dh + 0.4 - y_pf, 60]);
        translate([-pc, 0, 0]) porch_below_ceil();
    }
    translate([pc, 0, 0]) xz(y_pf, y_pf + wall)
        polygon(concat([[-pw, plinth_h - 0.5], [pw, plinth_h - 0.5]], [for (p = R_curve(RP, pw, -pw, 30)) [p[0], p[1] + 1]]));
}
module arch2d() polygon([[-ar_a, plinth_h - 1], [ar_a, plinth_h - 1], [ar_a, spring], [0, spring + ar_a * tp], [-ar_a, spring]]);
module porch_arch() translate([pc, 0, 0]) xz(y_pf - 1, y_pf + wall + 1) arch2d();
// below the spring, the columns stand free: the walls are cut back round them
module col_box(c) translate([c - col_r, y_pf - 0.1, plinth_h]) cube([2 * col_r, col_y + col_r - 0.7 - y_pf + 0.1, spring - plinth_h]);

// ---- the swooping roofs ------------------------------------------------------------------------
// MAIN. Chocolate (roof_main) and icing eaves (main_curls), from one profile.
module roof_main() intersection() { yz(-xs, xs) R_full(RM, kv0); yz(-xs - 1, xs + 1) R_choc(RM, kv0); }
module main_curls() for (m = [0, 1]) mirror([0, m, 0]) yz(-Wh, Wh) R_curl(RM, kv0);
// scallop tiles (the cottage's), their courses running along x, down to
// the chocolate's edge and following the swoop
tc = 2.6;  sd = 1.3;  tw = 4.8;
module tile_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module tiles() {
    vw = RM[7];
    nk = ceil((vw - 0.6) / tc);
    for (m = [0, 1]) mirror([0, m, 0]) for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.6))
        if (x0e > x1 + 0.3) intersection() {
            yz(-xs, xs) tile_band(RM, x0e, x1);
            translate([0, 0, 20]) linear_extrude(100) intersection() {
                union() {
                    translate([-xs - 1, -10]) square([2 * xs + 2, x0 + 10]);
                    for (j = [-8 : 8]) translate([j * tw + (k % 2) * tw / 2, x0]) scale([tw / 2 - 0.25, sd]) circle(r = 1, $fn = 24);
                }
                translate([-xs - 1, -10]) square([2 * xs + 2, vw + 10]);
            }
        }
    yz(-xs, xs) polygon([[1.2, zs(1.2) - 1.0], [1.2, zs(1.2) + 1.0], [0, zs(0) + 1.4], [-1.2, zs(1.2) + 1.0], [-1.2, zs(1.2) - 1.0]]);
}
// icing along the ridge, its edge cut straight down in waves
vk = RM[4];
function ic_edge(x) = 8 + 1.8 * sin(x * 23) + 1.2 * sin(x * 53 + 40);
module icing_roof() intersection() {
    yz(-xs - 0.4, xs + 0.4) polygon([[-vk, zs(vk) - 1.0], [0, zs(0) - 1.0], [vk, zs(vk) - 1.0],
        [vk, zs(vk) + 2.0], [3, zs(3) + 2.0], [0, zs(0) + 2.4], [-3, zs(3) + 2.0], [-vk, zs(vk) + 2.0]]);
    translate([0, 0, 40]) linear_extrude(100)
        polygon(concat([for (i = [0 : 60]) let (x = -xs - 0.4 + 2 * (xs + 0.4) * i / 60) [x, ic_edge(x)]],
                       [for (i = [60 : -1 : 0]) let (x = -xs - 0.4 + 2 * (xs + 0.4) * i / 60) [x, -ic_edge(-x)]]));
}
GD = [-4, 8, 20];
module gumdrops() difference() {
    for (x = GD) hull() {
        translate([x, 0, zs(0) + 2.4]) sphere(r = 2.8, $fn = 32);
        translate([x, 0, zs(0) - 1.6 * 4.2 - 0.5]) cylinder(r = 4.2, h = 0.01, $fn = 32);
    }
    below_ceil();
}
// THE GABLES. A coping of icing along the whole edge, tapering to nothing at
// the eave's tip; the cottage's band and drips down the face only where the
// roof is straight (on the swoop, the band's lower edge would be a shallow
// underside).
rb_h = 3.2;  rb_t = 1.2;
function cp_h(R, v) = let (a = abs(v)) a <= R[4] ? cp_hi : cp_hi * max(0, (R[5] - a) / (R[5] - R[4]));
module coping2d(R) polygon(concat([for (p = R_curve(R, -R[5], R[5], 60)) [p[0], p[1] + cp_lo]],
                                  [for (p = R_curve(R, R[5], -R[5], 60)) [p[0], p[1] + max(cp_h(R, p[0]), 0.05)]]));
function drip_pts(n, x0, x1, seed) = [for (i = [0 : n - 1]) let (r = rands(0, 1, 2, seed + i)) [x0 + i * (x1 - x0) / (n - 1), 1.4 + 2.2 * r[0], 2.0 + 0.4 * r[1]]];
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
module band2d(R, ext, drips) {
    X = R[4] - 0.5;
    polygon([[-X, R_zs(R, X) + cp_hi + ext], [0, R_zs(R, 0) + cp_hi + ext], [X, R_zs(R, X) + cp_hi + ext],
             [X, R_zs(R, X) - rb_h], [0, R_zs(R, 0) - rb_h], [-X, R_zs(R, X) - rb_h]]);
    for (d = drips, s = [-1, 1]) let (v = s * d[0]) translate([v, R_zs(R, v) - rb_h + 0.6]) drip2d(d[1] + 0.6, d[2]);
}
RD = [for (i = [0 : 10]) let (r = rands(0, 1, 2, 110 + i), x = 1.6 + i * 2.1) if (x < vk - 2.4) [x, 1.2 + 3.2 * r[0], 2.0 + 0.4 * r[1]]];
module rakes() for (m = [0, 1]) mirror([m, 0, 0]) {
    yz(Wh - wall - 0.3, Wh - 0.05) coping2d(RM);
    intersection() {
        yz(Wh - 0.1, Wh + rb_t) minkowski() { band2d(RM, 0, RD); translate([-0.01, -60]) square([0.02, 60]); }
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [tan(58), 0, 1, -tan(58) * Wh], [0, 0, 0, 1]])
            yz(Wh - 1, Wh + 4) band2d(RM, 10, RD);
    }
}
// drips under the eave on the front and back walls, clear of the turret and
// the porch, short over the windows
FRONT_DR = [for (d = drip_pts(24, -13, 27, 70)) if (d[0] < -12 || d[0] > 15.5) d];
BACK_DR  = drip_pts(24, -26, 26, 170);
module eave_drips() {
    for (d = FRONT_DR) nf(1, d[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(d[1], d[2]);
    for (d = BACK_DR)  nf(0, d[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(d[1], d[2]);
}

// PORCH ROOF: the same swoop in small, its ridge running back into the main
// wall under the main eave.
module porch_x(y0, y1) translate([pc, 0, 0]) xz(y0, y1) children();
module porch_roof() intersection() { porch_x(y_pf + wall - 0.4, -Dh + 0.4) R_full(RP, kv0p); porch_x(y_pf - 1, -Dh + 1) R_choc(RP, kv0p); }
module porch_curls() for (m = [0, 1]) translate([pc, 0, 0]) mirror([m, 0, 0]) translate([-pc, 0, 0]) porch_x(y_pf, -Dh + 0.4) R_curl(RP, kv0p);
module porch_tiles() {
    vw = RP[7];
    nk = ceil((vw - 0.6) / tc);
    translate([pc, 0, 0]) for (m = [0, 1]) mirror([m, 0, 0]) for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.6))
        if (x0e > x1 + 0.3) intersection() {
            xz(y_pf + wall - 0.4, -Dh + 0.4) tile_band(RP, x0e, x1);
            translate([0, 0, 10]) linear_extrude(50) intersection() {
                union() {
                    translate([-10, y_pf - 1]) square([x0 + 10, pd + 2]);
                    for (j = [-2 : 2]) translate([x0, -Dh - pd / 2 + j * tw + (k % 2) * tw / 2]) scale([sd, tw / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                translate([-10, y_pf - 1]) square([vw + 10, pd + 2]);
            }
        }
    porch_x(y_pf + wall - 0.4, -Dh + 0.4)
        polygon([[1.2, R_zs(RP, 1.2) - 1.0], [1.2, R_zs(RP, 1.2) + 1.0], [0, R_zs(RP, 0) + 1.4], [-1.2, R_zs(RP, 1.2) + 1.0], [-1.2, R_zs(RP, 1.2) - 1.0]]);
}
// the porch's front gable: coping and a band, no drips (they would hang
// over the arch)
module porch_rake() translate([pc, 0, 0]) mirror([0, 1, 0]) {
    xz(-y_pf - wall - 0.3, -y_pf - 0.05) coping2d(RP);
    intersection() {
        xz(-y_pf - 0.1, -y_pf + rb_t) minkowski() { band2d(RP, 0, []); translate([-0.01, -60]) square([0.02, 60]); }
        multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, tan(58) * y_pf], [0, 0, 0, 1]])
            xz(-y_pf - 1, -y_pf + 4) band2d(RP, 10, []);
    }
}
PDR = drip_pts(4, -Dh - 1.5, y_pf + 1.8, 230);
module porch_drips() for (m = [0, 1], d = PDR)
    translate([pc + (m == 0 ? 1 : -1) * pw, d[0], R_fl(RP, pw) + 1]) rotate([0, 0, m == 0 ? 90 : -90]) rotate([90, 0, 0])
        relief_up(-0.4, 1.2) drip2d(min(d[1], 2.4), d[2]);

// TURRET CONE: the same swoop, turned: a bell.
module cone_roof() translate([tx, ty, 0]) intersection() {
    rotate_extrude($fn = 128) R_full_r(RC, kv0c);
    rotate_extrude($fn = 128) R_choc_r(RC, kv0c);
}
module cone_curl() translate([tx, ty, 0]) rotate_extrude($fn = 128) R_curl(RC, kv0c);
// the scallop tiles in rings
module cone_tiles() translate([tx, ty, 0]) {
    vw = RC[7];
    nk = ceil((vw - 1.2) / tc);
    for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.8),
             n = max(4, round(2 * PI * x0 / tw)))
        if (x0e > x1 + 0.3) intersection() {
            rotate_extrude($fn = 128) tile_band(RC, x0e, x1);
            translate([0, 0, 60]) linear_extrude(60) intersection() {
                union() {
                    circle(r = x0, $fn = 128);
                    for (j = [0 : n - 1]) rotate(360 * (j + (k % 2) / 2) / n) translate([x0, 0])
                        scale([sd, 2 * PI * x0 / n / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                circle(r = vw, $fn = 128);
            }
        }
}
TDR = [for (i = [0 : 17]) let (r = rands(0, 1, 2, 300 + i)) [i * 20 + 7 * r[1], 1.4 + 2.4 * r[0], 2.2]];
module turret_drips() for (d = TDR) tplace(d[0], R_fl(RC, rt) + 1) relief_up(-0.6, 1.2) drip2d(d[1], d[2]);
// ICING COLLARS round the turret: a rounded band whose underside rises at 54 deg
TCOL = [35, 74];
module collars() translate([tx, ty, 0]) for (z = TCOL) rotate_extrude($fn = 128)
    polygon([[rt - 0.5, z - 2.4], [rt + 1.2, z - 0.1], [rt + 1.2, z + 0.5], [rt + 0.6, z + 1.3], [rt - 0.5, z + 1.3]]);

// THE SPIRE: a candy-cane rod rising from the cone's tip and bending over, away
// from the house, to 40 deg at its end: the most a rod can lean and print
// with nothing under it. A chain of balls, hulled in pairs.
sp_n = 10;  sp_L = 8;
function sp_ang(i) = 40 * pow(i / sp_n, 2);
function sp_pts(i) = i == 0 ? [0, 0] : let (p = sp_pts(i - 1)) [p[0] + sp_L / sp_n * sin(sp_ang(i)), p[1] + sp_L / sp_n * cos(sp_ang(i))];
function sp_r(i) = 1.8 - 0.6 * i / sp_n;
sp_z0 = R_top(RC, 0) - 2.5;
module sp_at(i) let (p = sp_pts(i)) translate([tx - p[0] / sqrt(2), ty - p[0] / sqrt(2), sp_z0 + p[1]]) sphere(r = sp_r(i), $fn = 24);
module spire() for (i = [0 : sp_n - 1]) hull() { sp_at(i); sp_at(i + 1); }
// stripes: the rod cut by slabs tilted across it
module stripe_slabs(c, z0, z1, pitch, t, tilt) for (z = [z0 : pitch : z1])
    translate([c[0], c[1], z]) rotate([tilt, 0, 45]) cube([20, 20, t], center = true);

// ---- the porch columns ----------------------------------------------------------------------
// Peppermint sticks: white shafts with red stripes, each flaring at the top
// into a square capital the arch and the walls stand on (a round shaft under
// a square wall left its corners hanging).
module column(c) {
    translate([c, col_y, plinth_h - 0.5]) cylinder(r = col_r, h = spring - 2.4 - plinth_h + 0.5, $fn = 40);
    hull() {
        translate([c, col_y, spring - 2.4]) cylinder(r = col_r, h = 0.01, $fn = 40);
        translate([c - col_r, y_pf, spring - 0.01]) cube([2 * col_r, 2 * col_r, 0.61]);
    }
}
module column_stripes(c) intersection() {
    translate([c, col_y, plinth_h - 0.5]) cylinder(r = col_r, h = spring - 2.4 - plinth_h + 0.5, $fn = 40);
    stripe_slabs([c, col_y], plinth_h + 1, spring - 3, 2.4, 1.0, 28);
}

// ---- windows and the door (the cottage's) -------------------------------------------------------
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
cb_r = 1.3;  cb_sp = 1.7;
function bead_rad(z, n) = max([for (i = [0 : n]) let (d = z - i * cb_sp) abs(d) < cb_r ? sqrt(cb_r * cb_r - d * d) : 0]);
function bead_profile(n, k = 12) = let (z0 = -cb_r, z1 = n * cb_sp + cb_r, m = ceil((z1 - z0) / cb_sp * k))
    concat([[0, z0]], [for (j = [1 : m - 1]) let (z = z0 + (z1 - z0) * j / m) [bead_rad(z, n), z]], [[0, z1]]);
// three corners: the fourth is inside the turret
module corner_beads() {
    n = floor((zf0 - 1 - plinth_h) / cb_sp);
    for (c = [[1, 1], [-1, 1], [1, -1]])
        translate([c[0] * (Wh - corner_r + (corner_r + 0.35) / sqrt(2)), c[1] * (Dh - corner_r + (corner_r + 0.35) / sqrt(2)), plinth_h + 0.6])
            rotate_extrude($fn = 32) polygon(bead_profile(n));
}
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9;
//   [face, u, z, a, straight height, kind]
WINDOWS = [
    [1, -8.3, 14, 3.2, 8, "arch"],  [1, 21, 14, 3.2, 8, "arch"],
    [0, -12, 14, 4.0, 9, "arch"],   [0, 12, 14, 4.0, 9, "arch"],
    [2, -11, 14, 4.0, 9, "arch"],   [2, 11, 14, 4.0, 9, "arch"],  [2, 0, 50, 5.4, 0, "round"],
    [3, 11, 14, 4.0, 9, "arch"],    [3, 5, 50, 5.4, 0, "round"],
];
function is_round(w) = w[5] == "round";
module win_outline(w) { if (is_round(w)) translate([0, w[3]]) circle(r = w[3]); else polygon(arch_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, is_round(w) ? w[3] - 1.1 : w[4] * 0.6]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame2d(w) {
    if (is_round(w)) translate([0, w[3]]) circle(r = w[3] + 3.2, $fn = 64);
    else {
        offset(r = fr_w) win_outline(w);
        beads(arch_path(w[3], w[4], fr_w - 0.1, bead_sp));
    }
}
module frame_relief(w) relief_up(-0.4, fr_t) { frame2d(w); offset(r = 0.3) win_outline(w); }
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
// the turret's windows: [angle, z, a, straight height]. A frame 11 mm wide on
// a 10.5 mm radius stands 1.5 off the wall at its edges if drawn flat, and
// sunk that deep its sheared opening rose 2.6 mm at the face and cut the arch
// away. So each frame is laid round the turret in 1 mm strips, every strip a
// flat relief tangent at its own angle.
TWIN = [[-110, 17, 3, 7], [-100, 50, 2.4, 5], [-35, 60, 2.4, 5]];
function tw_w(t) = [0, 0, 0, t[2], t[3], "arch"];
module cyl_relief(th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    tplace(th + uc / rt * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -50, -10]) cube([du + 0.3, 100, 20]);
    }
module turret_frames() for (t = TWIN) cyl_relief(t[0], t[1], t[2] + fr_w + bead_r + 0.6)
    relief_up(-0.4, fr_t) { frame2d(tw_w(t)); offset(r = 0.3) win_outline(tw_w(t)); }
module turret_glass() {
    intersection() {
        for (t = TWIN) tplace(t[0], t[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.6) offset(r = 0.6) win_outline(tw_w(t));
        translate([tx, ty, 0]) cylinder(r = rt, h = 200, $fn = 128);
    }
    intersection() {
        for (t = TWIN) tplace(t[0], t[1]) relief_up(-1.0, 0.4) win_muntins(tw_w(t), 0.6);
        translate([tx, ty, 0]) cylinder(r = rt + 0.4, h = 200, $fn = 128);
    }
}
module turret_openings() for (t = TWIN) tplace(t[0], t[1]) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline(tw_w(t));
// from 0.4 deep, as on the flat walls: from 1.2 the sheared cut ran down behind
// each sill and sealed a pocket of air there
module turret_frame_holes() for (t = TWIN) tplace(t[0], t[1]) relief_hole(-0.4, -0.4, fr_t + 2.4) offset(r = 0.4) win_outline(tw_w(t));

door_a = 3.2;
door_h = 9;
module openings() {
    for (w = WINDOWS) nf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) win_outline(w);
    nf(1, pc, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(arch_pts(door_a, door_h));
}
module frame_holes() {
    for (w = WINDOWS) nf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
    nf(1, pc, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
}
// A chocolate-bar door (the cottage's), inside the porch.
module door_leaf() nf(1, pc, plinth_h) difference() {
    translate([0, 0, -wall + 0.15]) linear_extrude(wall + 0.05)
        translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
    translate([-0.5, -1, -0.3]) cube([1, door_h + door_a + 4, 1]);
    for (zg = [3.4, 6.8, 10.2]) hull() {
        translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
        translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
    }
}
module door_frame() nf(1, pc, plinth_h) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.2) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
// a peppermint on the porch's gable, over the arch
pp_z = 31.5;  pp_r = 2.4;
module porch_mint() translate([pc, y_pf, pp_z]) rotate([90, 0, 0]) relief_up(-0.4, 1.0) circle(r = pp_r, $fn = 48);
module porch_mint_wedges() intersection() {
    porch_mint();
    translate([pc, y_pf, pp_z]) rotate([90, 0, 0]) translate([0, 0, -5]) linear_extrude(10) pepper_wedges(pp_r);
}

// ---- snow base ------------------------------------------------------------------------------------
module base2d() offset(r = 2.5) offset(delta = -2.5) union() {
    translate([-Wh - 4.5, -Dh - 8]) square([W + 9, D + 12.5]);
    translate([tx, ty]) circle(r = rt + 4.5);
    translate([pc - 12, y_pf - 5]) square([24, pd + 6]);
    for (p = [[Wh + 3.5, -Dh - 3, 4], [Wh + 3, Dh - 6, 4.5], [-Wh - 3, Dh - 2, 3.5], [-14, Dh + 3.5, 4], [18, Dh + 3.5, 3.5], [Wh + 3.5, 12, 3.5]])
        translate([p[0], p[1]]) circle(r = p[2]);
}
DRIFTS = [[Wh + 1, 8, 7, 4, 3.2], [-10, Dh + 1, 7, 3.5, 2.8], [Wh + 1, -Dh + 4, 5, 3.5, 2.4]];
PM = [[22, -Dh - 4.8, 2.6], [-18, Dh + 2.2, 2.0]];   // inside the base's edge
module peppermints(stripes = false) for (p = PM) translate([p[0], p[1], plinth_h - 0.2]) linear_extrude(1.4)
    if (stripes) union() { intersection() { circle(r = p[2]); pepper_wedges(p[2]); } circle(r = 0.8); } else circle(r = p[2]);
module base() {
    linear_extrude(plinth_h) base2d();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.01]) intersection() {
            scale([d[2], d[3], d[4]]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -0.6) base2d();
    }
}
module brand_mark() translate([pc, y_pf + 3.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- parts ----------------------------------------------------------------------------------------------
module body_raw() {
    difference() { main_walls(); turret_cut(); }
    turret_walls();
    difference() {
        porch_walls();
        porch_arch();
        for (c = col_c) col_box(c);
    }
}
module roof_raw() {
    difference() {
        union() { roof_main(); tiles(); }
        room(); turret_cut();
    }
    difference() { union() { porch_roof(); porch_tiles(); } room(); }
    difference() { lean() union() { cone_roof(); cone_tiles(); } room(); }
    door_leaf();
}
module accent_raw() {
    gumdrops();
    for (c = col_c) column_stripes(c);
    intersection() { lean() spire(); lean() stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28); }
    peppermints(true);
    porch_mint_wedges();
    for (w = WINDOWS) if (is_round(w)) nf(w[0], w[1], w[2]) intersection() {
        frame_relief(w);
        translate([0, w[3], -5]) linear_extrude(10) pepper_wedges(w[3] + 3.2);
    }
}
module trim_raw() {
    difference() {
        union() {
            base();
            corner_beads();
            difference() { union() { main_curls(); eave_drips(); rakes(); icing_roof(); } turret_cut(); }
            porch_curls();
            porch_drips();
            porch_rake();
            porch_mint();
            for (c = col_c) column(c);
            lean() { cone_curl(); turret_drips(); turret_frames(); spire(); collars(); }
            for (w = WINDOWS) nf(w[0], w[1], w[2]) {
                frame_relief(w);
                relief_up(-0.4, 0.4) win_muntins(w, 0.6);
                translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
            }
            door_frame();
            peppermints();
        }
        room();
        porch_room();
        brand_mark();
    }
    // the turret's panes go back in after its room is cut (flush with its face)
    difference() { lean() turret_glass(); lean() translate([tx, ty, -1]) cylinder(r = rti - 0.01, h = 200, $fn = 96); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); porch_room(); openings(); frame_holes(); lean() { turret_openings(); turret_frame_holes(); }
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
