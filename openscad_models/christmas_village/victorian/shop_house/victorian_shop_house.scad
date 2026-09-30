// Victorian Shop-House -- the Dickens Victorian village's first building with
// "more shape" (Scott, 2026-09-30, picked against his reference photos in
// ../../references/), and then "not squared" (Scott, same day: not the boxy
// shape, not the sharp edges, not the square base). The square version, gated
// and finished, is in the recycle bin (data/trash, 20260930-001) and at
// commit 16df111.
//
// So it is round now. A brick shop floor on a stadium plan (a straight front
// and back between two round ends) with a bow shop window and a panelled door;
// above it a white plaster storey in dark timber framing that juts out over
// the street all the way round on a cove and brackets; a hipped slate roof
// with round ends whose eave kicks out in a gentle bell, snow on its crown and
// icicles under it; a tall front dormer with a scalloped bargeboard and a
// finial; a stepped chimney. On a soft blob of snow with a rounded edge.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane.
//
// The machinery is the first Victorian cottage's and the gingerbread turret
// house's; every trap in .claude/skills/3d-print-design/SKILL.md Techniques 79
// and 80 applied from the start.
//
// COLOUR PARTS, ONE PRINT (victorian_shop_house.3mf), priority
// roof > accent > trim > body:
//   body    brick: the shop floor, the bow's riser, the chimney, the step
//   roof    slate: the roof and the dormer's; and the dark timber: cove,
//           brackets, beams, posts, braces, window frames and leading, the
//           bargeboard and finial, the door
//   trim    white: snow base, plaster, the eave's soffit, snow on the roofs,
//           icicles, every pane, the shop windows' frames and bars, the door
//           frame and fanlight
//   accent  evergreen: the bow window, the wreath, the window box

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;

// ---- the plan: a stadium --------------------------------------------------------------
L0       = 14;              // the straight front and back
Rg       = 25;              // the shop floor's radius (46.6 clear inside)
wall     = 1.68;
plinth_h = 8;
SH       = 1.2;
H1       = 36;              // top of the shop floor; the jetty starts here
J        = 3;               // the upper storey stands this far out, all round
Ru       = Rg + J;
EC       = [[-L0 / 2, 0], [L0 / 2, 0]];     // the ends' centres
fl_ang   = 52;

// SWEEP: a profile in (v, z), v the distance out from the centre line, swept
// along the straight front and back and turned half round each end.
module sweep(L = L0) {
    yz(-L / 2 - 0.01, L / 2 + 0.01) union() { children(); mirror([1, 0, 0]) children(); }
    for (s = [-1, 1]) translate([s * L / 2, 0, 0]) rotate([0, 0, s > 0 ? -90 : 90]) rotate_extrude(angle = 180, $fn = FN) children();
}
module stadium(r) hull() for (c = EC) translate(c) circle(r = r, $fn = FN);
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// ALONG THE OUTLINE. s is the distance round the stadium of radius R, from
// the front-left end of the straight front, anticlockwise. spos gives the
// point and its outward direction; splace puts a face frame there (local z
// out, x along s, y up). Windows, posts, brackets, drips and brick joints are
// all placed this way, on the straights and round the ends alike.
function sper(R) = 2 * L0 + 2 * PI * R;
function spos(R, s) = let (P = sper(R), t = s - floor(s / P) * P, P1 = L0, P2 = L0 + PI * R, P3 = 2 * L0 + PI * R)
    t < P1 ? [-L0 / 2 + t, -R, -90] :
    t < P2 ? let (a = -90 + (t - P1) / R * 180 / PI) [L0 / 2 + R * cos(a), R * sin(a), a] :
    t < P3 ? [L0 / 2 - (t - P2), R, 90] :
             let (a = 90 + (t - P3) / R * 180 / PI) [-L0 / 2 + R * cos(a), R * sin(a), a];
function s_front(x) = x + L0 / 2;
function s_right(a, R) = L0 + (a + 90) / 180 * PI * R;
function s_back(x, R) = L0 + PI * R + (L0 / 2 - x);
function s_left(a, R) = 2 * L0 + PI * R + (a - 90) / 180 * PI * R;
module splace(R, s, z) let (p = spos(R, s)) translate([p[0], p[1], z]) rotate([0, 0, p[2] + 90]) rotate([90, 0, 0]) children();
// a frame with x out along the normal, y along s, z up: for profiles in (v, z)
module nplace(R, s) let (p = spos(R, s)) translate([p[0], p[1], 0]) rotate([0, 0, p[2]]) children();
// A flat relief laid round the outline in 1 mm strips, each tangent at its own
// s: drawn flat, a wide frame stands off a round wall at its edges.
module srelief(R, s, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    splace(R, s + uc, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -60, -10]) cube([du + 0.3, 150, 20]);
    }

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
// for framing: the straight term widened only sideways, so a member's top
// stays level (Technique 80.2)
module relief_flat(d0, d1, sh = SH) intersection() {
    translate([0, 0, d0]) linear_extrude(d1 - d0) minkowski() { children(); translate([-0.2, -0.01]) square([0.4, 0.01]); }
    shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children();
}

// ---- the roof: one profile (the turret house's) -----------------------------------------------
// R = [eave line, inner half-width, ceiling slope, slab depth, bell start, tip,
// tip angle, slate edge]. The top eases from the pitch to R[6] past the wall;
// under the eave the profile rises at 52 deg from the wall to the tip.
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang);
sb = 1.8;                   // the white band along the eave's underside
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
module R_full(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
module R_choc(R, kv0) polygon([[0, -10], [kv0, -10], [kv0, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_below(R) polygon([[0, -5], [R[1] + 20, -5], [R[1] + 20, R_zc(R, R[1] + 20)], [0, R_zc(R, 0)]]);

H   = 64;                   // the roof's eave line, at the upper wall's inside
tp  = tan(55);
tv  = 2.52 / cos(55);
RV  = [H, Ru - wall, tp, tv, Ru - 3, Ru + 3.5, 35, Ru + 3.5];
kv0 = Ru - 0.8;
zfu = R_fl(RV, Ru);         // where the soffit meets the upper wall
function zs(v) = R_zs(RV, v);

// ---- rooms -------------------------------------------------------------------------------------
// the shop floor, then the wider upper storey from H1, up under the roof
module room2d() polygon([[0, -2], [Rg - wall, -2], [Rg - wall, H1], [Ru - wall, H1], [Ru - wall, H], [0, R_zc(RV, 0)]]);
module main_room() sweep() room2d();
module below_ceil() sweep() R_below(RV);

// ---- the bow window -------------------------------------------------------------------------------
// A shallow bow on the front, bulging 3 from the brick to the jetty's face:
// an arc of radius 7.5 on the 12-wide chord.
rb  = 7.5;
BC  = [0, -Ru + rb];
by_riser = 15;
by_win   = [16.4, 29.4];
by_a     = [-128, -52];     // the glazing's arc
module bow2d() intersection() { translate(BC) circle(r = rb, $fn = FN); translate([-20, -40]) square([40, 40 - Rg + 0.5]); }
module bow_solid() translate([0, 0, plinth_h - 0.5]) linear_extrude(H1 + 0.3 - plinth_h + 0.5) bow2d();
// its inside, open to the shop; its ceiling rises at 55 deg from the
// glazing's head into the room, so it is a slope, not a bridge
by_ceil0 = by_win[1] + 1.2;
module bow_room() intersection() {
    translate([BC[0], BC[1], plinth_h]) cylinder(r = rb - wall, h = 60, $fn = FN);
    translate([-20, -Rg + 3, 0]) mirror([0, 1, 0]) cube([40, 20, 100]);
    yz(-30, 30) polygon([[-40, -5], [-40, by_ceil0 - (40 - (Ru - wall)) * tan(55)],
                         [-15, by_ceil0 + (Ru - wall - 15) * tan(55)], [-15, -5]]);
}
module arc_ring(c, a0, a1, prof) translate([c[0], c[1], 0]) rotate([0, 0, a0]) rotate_extrude(angle = a1 - a0, $fn = FN) polygon(prof);
module bow_opening() arc_ring(BC, by_a[0], by_a[1], [[rb - wall - 2, by_win[0]], [rb + 2, by_win[0]], [rb + 2, by_win[1]], [rb - wall - 2, by_win[1]]]);
// the glass, flush with the bow's face
module bow_glass() arc_ring(BC, by_a[0] - 4.6, by_a[1] + 4.6, [[rb - wall, by_win[0] - 0.6], [rb, by_win[0] - 0.6], [rb, by_win[1] + 0.6], [rb - wall, by_win[1] + 0.6]]);
by_zt = by_win[0] + (by_win[1] - by_win[0]) * 0.56;
module bow_bars() {
    for (a = [-109, -90, -71]) translate([BC[0] + rb * cos(a), BC[1] + rb * sin(a), by_win[0] - 0.6]) rotate([0, 0, a + 90]) rotate([90, 0, 0])
        relief_up(-0.4, 0.6) translate([-0.8, 0]) square([1.6, by_win[1] - by_win[0] + 1.2]);
    arc_ring(BC, by_a[0] - 4.6, by_a[1] + 4.6, [[rb - 0.4, by_zt], [rb + 0.6, by_zt + 1.2], [rb + 0.6, by_zt + 2.0], [rb - 0.4, by_zt + 2.0]]);
}

// ---- the brick shop floor -----------------------------------------------------------------------------
bd = 0.6;  bp = 2.6;  br = bd * tan(58);  bj = 0.6;  bl = 7;
function zc(k) = plinth_h + 0.4 + k * bp;
nb = ceil((H1 + 2 - plinth_h - 0.4) / bp);
// the wall's section: each course bulges bd out of the face, under a 58 deg
// chamfer and over a 45 deg one
function brick_prof() = concat([[Rg - wall - 0.3, plinth_h - 0.5], [Rg, plinth_h - 0.5]],
    [for (k = [0 : nb - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < H1 + 1) [Rg + g, z]],
    [[Rg, H1 + 2], [Rg - wall - 0.3, H1 + 2]]);
module brick_walls() sweep() polygon(brick_prof());

// ---- the jetty ----------------------------------------------------------------------------------------
// A cove at 62 deg from the brick to the upper storey's face, all round, and
// brackets at 50 deg under it. Both run 0.45 into the brick and up into the
// plaster: overlapping, never abutting.
cv_z0 = H1 - J * tan(62);
cv_foot = cv_z0 - 0.45 * tan(62);
module cove() sweep() polygon([[Rg - 0.45, cv_foot], [Rg - 0.45, H1 + 0.3], [Ru, H1 + 0.3], [Ru, H1]]);
module bracket(s) nplace(Rg, s) rotate([90, 0, 0]) linear_extrude(2.4, center = true)
    polygon([[-0.4, H1 - (J + 1.0) * tan(50)], [-0.4, H1 + 1.6], [J + 0.6, H1 + 1.6], [J + 0.6, H1 - 0.01]]);

// ---- the upper storey ----------------------------------------------------------------------------------
tb_t = 0.8;                 // timbers stand this far off the plaster
uf_w = 2.2;
hd   = SH * (tb_t + 0.4);   // frames drawn this much deeper at head and foot (Technique 80.3)
module upper_walls() sweep() polygon([[Ru - wall - 0.3, H1], [Ru, H1], [Ru, R_zc(RV, Ru)], [Ru - wall - 0.3, R_zc(RV, Ru - wall - 0.3)]]);
// the sill beam: a ring whose underside rises at 50 deg as it comes out
module sill_beam() sweep() polygon([[Ru - 0.4, H1], [Ru + tb_t, H1 + SH * (tb_t + 0.4)], [Ru + tb_t, H1 + 2.4], [Ru - 0.4, H1 + 2.4]]);
// POSTS and BRACES, placed round the outline clear of the windows
POSTS = [sper(Ru) - 1.5, 15.5, 27, 50, 61, 84, 96, 120, 132, 157, 169, 190];
BRACES = [[15.5, 27], [50, 61], [84, 96], [120, 132], [157, 169], [190, sper(Ru) - 1.5]];
module posts() for (s = POSTS) splace(Ru, s, 0) relief_flat(-0.4, tb_t) translate([-1.2, H1]) square([2.4, zfu + 0.5 - H1]);
module braces() for (b = BRACES) let (m = (b[0] + b[1]) / 2, h = (b[1] - b[0]) / 2)
    srelief(Ru, m, 0, h + 1.5) relief_flat(-0.4, tb_t) hull() {
        translate([-h + 1.3, H1 + 2.2]) square([1.8, 0.1], center = true);
        translate([h - 1.3, zfu - 1.5]) square([1.8, 0.1], center = true);
    }
// UPPER WINDOWS: square-headed casements with diamond leading, in timber
// frames. [s, z, a, h]; h = 8 keeps the leading off the centre bar's edge at
// the head (Technique 80.5).
UW = [[s_front(0), H1 + 7, 3.6, 8], [s_right(-40, Ru), H1 + 7, 3.6, 8], [s_right(30, Ru), H1 + 7, 3.6, 8],
      [s_back(0, Ru), H1 + 7, 3.6, 8], [s_left(150, Ru), H1 + 7, 3.6, 8], [s_left(220, Ru), H1 + 7, 3.6, 8]];
function rect_pts(a, hgt) = [[-a, 0], [a, 0], [a, hgt], [-a, hgt]];
module lattice() {
    for (i = [-5 : 5], s = [-1, 1]) translate([i * 4.2, 0]) rotate(s * 38) translate([-0.5, -30]) square([1.0, 60]);
    translate([-0.9, -3]) square([1.8, 40]);
}
module uw_frames() for (w = UW) srelief(Ru, w[0], w[1], w[2] + uf_w + 0.6) {
    relief_up(-0.4, tb_t) { offset(r = uf_w) translate([0, -hd]) polygon(rect_pts(w[2], w[3] + 2 * hd)); offset(r = 0.3) polygon(rect_pts(w[2], w[3])); }
    relief_up(-0.4, 0.4) intersection() { offset(r = 0.6) polygon(rect_pts(w[2], w[3])); lattice(); }
}
module uw_openings() for (w = UW) splace(Ru, w[0], w[1]) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) polygon(rect_pts(w[2], w[3]));
module uw_glass() intersection() {
    for (w = UW) splace(Ru, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.6) offset(r = 0.6) polygon(rect_pts(w[2], w[3]));
    linear_extrude(200) stadium(Ru);
}
// a window box under the front window
module box2d(a) {
    bw = a + uf_w + 0.4;
    translate([-bw, -uf_w - 4.2]) square([2 * bw, 4.2 + uf_w]);
    for (i = [0 : 4]) let (x = -bw + 1.3 + i * (2 * bw - 2.6) / 4)
        translate([x, -0.4]) polygon([[-1.1, 0], [1.1, 0], [0, 1.9]]);
}
module window_box() let (w = UW[0]) splace(Ru, w[0], w[1]) relief_up(-0.4, tb_t + 1.2) box2d(w[2]);   // its foot 0.6 above the jetty

// ---- the shop floor's windows and door ---------------------------------------------------------------
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
fr_w = 2.6;
fr_t = bd + 0.6;
sill = 3.3;
// [s, z, a, h]: round the ends and the back; the bow and the door are the front
SW = [[s_left(235, Rg), 14, 4.2, 10], [s_right(45, Rg), 14, 4.2, 10], [s_back(0, Rg), 14, 4.2, 10], [s_left(145, Rg), 14, 4.2, 10]];
module sw_outline(w) polygon(seg_pts(w[2], w[3]));
module sw_bars(w) { translate([-0.84, -3]) square([1.68, 40]); translate([-20, w[3] * 0.55]) square([40, 2.2]); }
module sw_frames() for (w = SW) srelief(Rg, w[0], w[1], w[2] + fr_w + 1.2) {
    relief_up(-0.4, fr_t) {
        union() {
            offset(r = fr_w) sw_outline(w);
            translate([-w[2] - fr_w - 0.8, -sill]) square([2 * (w[2] + fr_w + 0.8), sill + 1]);
        }
        offset(r = 0.3) sw_outline(w);
    }
    relief_up(-0.4, fr_t + 0.5) translate([0, seg_top(w[2], w[3]) - 1.2]) polygon([[-1.3, 0], [1.3, 0], [1.8, fr_w + 1.8], [-1.8, fr_w + 1.8]]);
    relief_up(-0.4, bd) intersection() { offset(r = 0.6) sw_outline(w); sw_bars(w); }
}
module sw_openings() for (w = SW) splace(Rg, w[0], w[1]) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) sw_outline(w);
module sw_holes() for (w = SW) splace(Rg, w[0], w[1]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) sw_outline(w);
module sw_glass() intersection() {
    for (w = SW) splace(Rg, w[0], w[1]) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) offset(r = 0.6) sw_outline(w);
    linear_extrude(200) stadium(Rg - 0.2);
}
// THE DOOR, on the right end toward the front, with a fanlight over it
s_d  = s_right(-55, Rg);
dr_a = 4.2;  dr_h = 13;  dr_f = 2.4;
dr_top = plinth_h + dr_h + 0.6 + dr_f;
module door_outline() polygon(rect_pts(dr_a, dr_h + 0.6 + dr_f));
module panel2d(x0, x1, z0, z1) polygon([[x0, z0], [x1, z0], [x1, z1], [(x0 + x1)/2, z1 + (x1 - x0)/2 * tan(60)], [x0, z1]]);
module rshell(r0, r1) difference() { linear_extrude(200) stadium(r1); translate([0, 0, -1]) linear_extrude(202) stadium(r0); }
module door_leaf() intersection() {
    splace(Rg, s_d, plinth_h) difference() {
        translate([0, 0, -wall - 1]) linear_extrude(wall + 2)
            translate([-dr_a - 0.2, -0.3]) square([2 * dr_a + 0.4, dr_h + 0.3]);
        // panels sunk 0.3 into its face
        translate([0, 0, -0.1]) linear_extrude(3) {
            panel2d(-3.1, -0.7, 1.4, 5.4);  panel2d(0.7, 3.1, 1.4, 5.4);
            panel2d(-3.1, -0.7, 8.0, 10.6); panel2d(0.7, 3.1, 8.0, 10.6);
        }
    }
    rshell(Rg - wall + 0.15, Rg + 0.2);
}
module door_frame() srelief(Rg, s_d, plinth_h, dr_a + 2.4) relief_up(-0.4, fr_t) {
    translate([-dr_a - 1.8, -0.5]) square([2 * dr_a + 3.6, dr_h + 0.6 + dr_f + 1.8 + 0.5 + SH * (fr_t + 0.4)]);
    translate([-dr_a + 0.3, -1]) square([2 * dr_a - 0.6, dr_h + 0.6 + dr_f + 0.7]);
}
module transom() srelief(Rg, s_d, plinth_h + dr_h, dr_a + 0.6) relief_up(-0.4, fr_t) translate([-dr_a, 0]) square([2 * dr_a, 0.8]);
module fanlight() intersection() {
    splace(Rg, s_d, plinth_h + dr_h) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.4) translate([-dr_a - 0.6, 0]) square([2 * dr_a + 1.2, 0.6 + dr_f + 0.6]);
    linear_extrude(200) stadium(Rg - 0.2);
}
module door_opening() splace(Rg, s_d, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + bd + 4) door_outline();
module door_hole() splace(Rg, s_d, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) door_outline();
module wreath() srelief(Rg, s_d, plinth_h + 9.5, 3.8) relief_up(-0.4, bd + 0.6) difference() { circle(r = 3.0, $fn = 40); circle(r = 1.6, $fn = 32); }
// a curved step in front of the door
module step() intersection() {
    translate([EC[1][0], EC[1][1], plinth_h - 0.5]) difference() { cylinder(r = Rg + 3.0, h = 1.9, $fn = FN); translate([0, 0, -1]) cylinder(r = Rg - 0.5, h = 4, $fn = FN); }
    translate([EC[1][0], EC[1][1], 0]) rotate([0, 0, -55 - 12]) rotate_extrude(angle = 24, $fn = FN) square([60, 20]);
}

// ---- icicles under the eave, all round, clear of the dormer's window ---------------------------------
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
IC = [for (i = [0 : 47]) [i * sper(Ru) / 48 + 1.3 * rnd(i, 70), 1.4 + 1.8 * rnd(i, 90), 1.8 + 0.4 * rnd(i, 110)]];
module icicles() for (d = IC) splace(Ru, d[0], zfu + 1) relief_up(-0.4, 1.2) drip2d(d[1], d[2]);

// ---- the roof ------------------------------------------------------------------------------------------
module roof_slate() intersection() { sweep() R_full(RV, kv0); sweep() R_choc(RV, kv0); }
module soffit() sweep() R_curl(RV, kv0);
// slate courses: each a band of the roof's top, stepped
sh_c = 2.35;
module course_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
module slates() {
    ve = RV[5];
    nk = ceil((ve - 0.6) / sh_c);
    for (k = [0 : nk - 1]) let (x0 = ve - k * sh_c, x1 = max(ve - (k + 1) * sh_c - 0.5, 0.6))
        if (x0 > x1 + 0.3) sweep() course_band(RV, x0, x1);
    sweep() polygon([[0, zs(0) - 1.0], [1.2, zs(1.2) - 1.0], [1.2, zs(1.2) + 1.0], [0, zs(0) + 1.4]]);
}
// SNOW on the crown, its edge cut straight down in waves
function wave(t) = 2.2 * sin(t * 1.7) + 1.3 * sin(t * 4.1 + 60);
function stad_pt(r, t) =
    t < 1 ? let (a = -90 + 180 * t) [EC[1][0] + r * cos(a), r * sin(a)] :
    t < 2 ? [L0 / 2 - L0 * (t - 1), r] :
    t < 3 ? let (a = 90 + 180 * (t - 2)) [EC[0][0] + r * cos(a), r * sin(a)] :
            [-L0 / 2 + L0 * (t - 3), -r];
module snow_roof() intersection() {
    sweep() polygon([[0, zs(0) - 1.0], [RV[4], zs(RV[4]) - 1.0], [RV[4], zs(RV[4]) + 2.0], [3, zs(3) + 2.0], [0, zs(0) + 2.4]]);
    translate([0, 0, 40]) linear_extrude(100) polygon([for (i = [0 : 199]) let (t = 4 * i / 200) stad_pt(12 + wave(i * 3.3), t)]);
}

// ---- the chimney (the square version's), on the back right ---------------------------------------------
ch0 = [9, 17, 6, 14];
ch1 = [10.2, 15.8, 7, 13];
ch_w = 104;
ch_top = 116;
module chimney() difference() {
    union() {
        translate([ch0[0], ch0[2], 60]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], ch_w - 60]);
        hull() {
            translate([ch0[0], ch0[2], ch_w - 0.01]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 0.01]);
            translate([ch1[0], ch1[2], ch_w + 1.2 * tan(60)]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
        }
        translate([ch1[0], ch1[2], ch_w]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], ch_top - ch_w]);
        hull() {
            translate([ch1[0], ch1[2], ch_top - 1.3]) cube([ch1[1] - ch1[0], ch1[3] - ch1[2], 0.01]);
            translate([ch1[0] - 0.8, ch1[2] - 0.8, ch_top]) cube([ch1[1] - ch1[0] + 1.6, ch1[3] - ch1[2] + 1.6, 1.6]);
        }
        for (x = [ch1[0] + 1.8, ch1[1] - 1.8]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 1.4]) cylinder(d = 3.4, h = 4.2, $fn = 32);
    }
    below_ceil();
    for (x = [ch1[0] + 1.8, ch1[1] - 1.8]) translate([x, (ch1[2] + ch1[3]) / 2, ch_top + 3.4]) cylinder(d = 1.0, h = 5, $fn = 20);
}
module chimney_col() translate([ch0[0], ch0[2], 60]) cube([ch0[1] - ch0[0], ch0[3] - ch0[2], 80]);

// ---- the dormer (the square version's), on the front ------------------------------------------------------
// Built in its own frame -- x out from the ridge toward the front, y across --
// and turned into place by dmw(): x runs to -y. It sits on the straight front,
// where the roof's section is the same all along, so the main ceiling in its
// frame is R_zc(RV, x).
module dmw() rotate([0, 0, -90]) children();
module dm_main_below() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, R_zc(RV, 40)], [0, R_zc(RV, 0)], [-40, R_zc(RV, 40)]]);
dm_c  = 0;
dm_w  = 5.5;
dm_in = dm_w - wall;
dm_x  = 22;
dm_x0 = 1;
dm_e  = 1;
DMW   = [2.6, 79.5, 8];     // window: half-width, sill, height
dm_fw = 2.0;
dm_ze = 94.8;               // its eave: the verge board clears the window's frame
function dz_ceil(y) = dm_ze + (dm_in - abs(y - dm_c)) * tp;
function dz_out(y)  = dz_ceil(y) + tv;
module dmf(z) translate([dm_x, dm_c, z]) rotate([0, 0, 90]) rotate([90, 0, 0]) children();
module dm_below(dz) yz(dm_x0 - 1, dm_x + dm_e + 1)
    polygon([[dm_c - 20, 60], [dm_c + 20, 60], [dm_c + 20, dz_ceil(dm_c + 20) + dz], [dm_c, dz_ceil(dm_c) + dz], [dm_c - 20, dz_ceil(dm_c - 20) + dz]]);
module dm_room() intersection() {
    translate([dm_x0 - 1, dm_c - dm_in, 60]) cube([dm_x - wall - dm_x0 + 1, 2 * dm_in, 60]);
    dm_below(0);
}
module dm_env() intersection() {
    translate([dm_x0 - 1, dm_c - dm_w, 60]) cube([dm_x - dm_x0 + 1, 2 * dm_w, 60]);
    dm_below(tv);
}
module dm_walls() difference() {
    intersection() { translate([dm_x0, dm_c - dm_w, 60]) cube([dm_x - dm_x0, 2 * dm_w, 60]); dm_below(0.4); }
    dm_main_below();
}
dm_E = dm_w + dm_e;
module dm_front_cut(up = 60) intersection() {
    children();
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [SH, 0, 1, -SH * dm_x], [0, 0, 0, 1]])
        minkowski() { children(); cylinder(r = 0.01, h = up, $fn = 4); }
}
dm_yf = dm_E - 0.08;
dm_tip = dz_ceil(dm_c + dm_yf) + (dm_E - dm_yf) * tan(fl_ang);
module dm_slab() difference() {
    dm_front_cut() yz(dm_x0, dm_x + dm_e) polygon([[dm_c - dm_E, dm_tip], [dm_c - dm_yf, dz_ceil(dm_c - dm_yf)], [dm_c, dz_ceil(dm_c)],
        [dm_c + dm_yf, dz_ceil(dm_c + dm_yf)], [dm_c + dm_E, dm_tip], [dm_c + dm_E, dz_out(dm_c + dm_E)], [dm_c, dz_out(dm_c)], [dm_c - dm_E, dz_out(dm_c - dm_E)]]);
    dm_main_below();
}
dm_up = 0.3 + SH * (dm_e + 0.2) + 0.2;
module dm_flare() difference() {
    dm_front_cut() for (m = [0, 1]) translate([0, dm_c, 0]) mirror([0, m, 0]) yz(dm_x0, dm_x + dm_e)
        polygon([[dm_w - 0.3, dz_ceil(dm_c + dm_yf) - (dm_yf - dm_w + 0.3) * tan(fl_ang)], [dm_yf, dz_ceil(dm_c + dm_yf)],
                 [dm_yf, dz_ceil(dm_c + dm_yf) + dm_up], [dm_w - 0.3, dz_ceil(dm_c + dm_w - 0.3) + dm_up]]);
    dm_main_below();
}
function sh_d(k, X) = min(k * sh_c, X - 0.6);
module dm_slates() difference() {
    nk = ceil((dm_E - 0.6) / sh_c);
    for (s = [-1, 1], k = [0 : nk - 1]) let (y0 = s * (dm_E - sh_d(k, dm_E)), y1 = s * (dm_E - min(sh_d(k + 1, dm_E) + 0.5, dm_E - 0.6)))
        yz(dm_x0, dm_x + dm_e) translate([dm_c, 0])
            polygon([[y0, dz_out(dm_c + y0) - 1.0], [y0, dz_out(dm_c + y0) + 1.0], [y1, dz_out(dm_c + y1) + 0.05], [y1, dz_out(dm_c + y1) - 1.0]]);
    dm_main_below();
}
// THE BARGEBOARD: the verge board, its lower edge scalloped. Its ends stop at
// the walls' faces, where they stand on them.
bs_r = 1.1;
module board2d() {
    polygon([[dm_c - dm_w, dz_ceil(dm_c - dm_w) - 2.2 + bs_r], [dm_c, dz_ceil(dm_c) - 2.2 + bs_r], [dm_c + dm_w, dz_ceil(dm_c + dm_w) - 2.2 + bs_r],
             [dm_c + dm_w, dz_ceil(dm_c + dm_w) + dm_up], [dm_c, dz_ceil(dm_c) + dm_up], [dm_c - dm_w, dz_ceil(dm_c - dm_w) + dm_up]]);
    for (i = [-4 : 4]) let (y = dm_c + i * 1.3 * dm_w / 4 * 0.75) translate([y, dz_ceil(y) - 2.2 + bs_r]) circle(r = bs_r, $fn = 24);
}
module dm_board() difference() {
    dm_front_cut() yz(dm_x - 0.3, dm_x + dm_e + 0.2) board2d();
    dm_room();
}
module dm_finial() translate([dm_x + dm_e - 1.3, dm_c, dz_out(dm_c) - 2.6]) {
    translate([-1.1, -1.1, 0]) cube([2.2, 2.2, 6.4]);
    translate([0, 0, 6.4]) rotate([0, 0, 45]) cylinder(r1 = 1.1 * sqrt(2), r2 = 0, h = 1.1 * tan(60) * 1.2, $fn = 4);
}
module dm_snow() difference() {
    intersection() {
        yz(dm_x0, dm_x + dm_e) polygon([[dm_c - 4.5, dz_out(dm_c - 4.5) - 1.0], [dm_c, dz_out(dm_c) - 1.0], [dm_c + 4.5, dz_out(dm_c + 4.5) - 1.0],
            [dm_c + 4.5, dz_out(dm_c + 4.5) + 1.8], [dm_c + 1.5, dz_out(dm_c + 1.5) + 2.8], [dm_c - 1.5, dz_out(dm_c + 1.5) + 2.8], [dm_c - 4.5, dz_out(dm_c - 4.5) + 1.8]]);
        translate([0, 0, 80]) linear_extrude(40) polygon(concat(
            [for (i = [0 : 30]) let (x = dm_x0 + (dm_x + dm_e - 1.8 - dm_x0) * i / 30) [x, dm_c + 3.0 + 0.8 * sin(x * 47)]],
            [for (i = [30 : -1 : 0]) let (x = dm_x0 + (dm_x + dm_e - 1.8 - dm_x0) * i / 30) [x, dm_c - 3.0 - 0.8 * sin(x * 53 + 40)]]));
    }
    dm_main_below();
}
module dm_window() dmf(DMW[1]) {
    relief_up(-0.4, tb_t) { offset(r = dm_fw) translate([0, -hd]) polygon(rect_pts(DMW[0], DMW[2] + 2 * hd)); offset(r = 0.3) polygon(rect_pts(DMW[0], DMW[2])); }
    relief_up(-0.4, 0.4) intersection() { offset(r = 0.6) polygon(rect_pts(DMW[0], DMW[2])); lattice(); }
}
module dm_glass() dmf(DMW[1]) translate([0, 0, -wall]) linear_extrude(wall) offset(r = 0.6) polygon(rect_pts(DMW[0], DMW[2]));
module dm_opening() dmf(DMW[1]) translate([0, 0, -wall - 2]) linear_extrude(wall + 5) polygon(rect_pts(DMW[0], DMW[2]));

// ---- rooms, all together ---------------------------------------------------------------------------------
module room() { main_room(); dmw() dm_room(); }

// ---- the snow base: a soft blob with a rounded edge --------------------------------------------------------
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) stadium(Ru);
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[EC[1][0] + (Ru + 1) * cos(15), (Ru + 1) * sin(15), 7, 4, 3.2], [-4, Ru + 1, 7, 3.5, 2.8],
          [EC[0][0] + (Ru + 1) * cos(160), (Ru + 1) * sin(160), 5, 3.5, 2.4], [EC[0][0] + (Ru + 1) * cos(235), (Ru + 1) * sin(235), 4, 3, 2.2]];
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
module brand_mark() translate([0, -Ru - 3.4, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- brick joints ------------------------------------------------------------------------------------------
// vertical mortar joints, staggered by course, round the whole shop floor;
// none near an opening, and none in the courses the cove's foot sits on (the
// foot would bridge each slot)
function box_s(s0, s1, z0, z1) = [s0, s1, z0, z1];
OPEN = concat(
    [box_s(s_front(-8.5), s_front(8.5), 0, 100), box_s(s_d - dr_a - 5, s_d + dr_a + 5, 0, dr_top + 4)],
    [for (w = SW) box_s(w[0] - w[2] - fr_w - 3, w[0] + w[2] + fr_w + 3, w[1] - sill - 4, w[1] + seg_top(w[2], w[3]) + fr_w + 4)]);
function clear_at(s, z0, z1) = len([for (b = OPEN) if (s + bj > b[0] && s - bj < b[1] && z1 > b[2] && z0 < b[3]) 1]) == 0;
nj = floor(sper(Rg) / bl);
module joints() for (k = [1 : nb - 1]) let (z0 = zc(k), z1 = zc(k + 1)) if (z1 < cv_foot - 0.5)
    for (j = [0 : nj - 1]) let (s = (j + (k % 2) / 2) * sper(Rg) / nj) if (clear_at(s, z0, z1))
        splace(Rg, s, z0) translate([-bj / 2, 0, -0.05]) cube([bj, z1 - z0, 2.1]);

// ---- parts ------------------------------------------------------------------------------------------------
// the same point on the outline at another radius: straights keep their
// length, the ends their angle
function s_to(R0, R1, s) = let (t = s - floor(s / sper(R0)) * sper(R0))
    t < L0 ? t : t < L0 + PI * R0 ? L0 + (t - L0) * R1 / R0 :
    t < 2 * L0 + PI * R0 ? t - PI * R0 + PI * R1 : 2 * L0 + PI * R1 + (t - 2 * L0 - PI * R0) * R1 / R0;
BRK = [for (s = POSTS) s_to(Ru, Rg, s)];    // the brackets under the posts
module body_raw() {
    brick_walls();
    intersection() { bow_solid(); translate([-50, -50, 0]) cube([100, 100, by_riser]); }
    chimney();
    step();
}
module roof_raw() {
    difference() { roof_slate(); room(); chimney_col(); }
    difference() { slates(); room(); chimney_col(); dmw() dm_env(); }
    difference() { union() { cove(); for (s = BRK) if (clear_at(s, H1 - 6, H1)) bracket(s); } room(); bow_room(); }
    sill_beam();
    posts();
    braces();
    uw_frames();
    door_leaf();
    dmw() {
        difference() { union() { dm_slab(); dm_slates(); } dm_room(); }
        dm_board();
        dm_finial();
        dm_window();
    }
}
module accent_raw() {
    difference() {
        intersection() { bow_solid(); translate([-50, -50, by_riser]) cube([100, 100, 100]); }
        bow_room();
        bow_opening();
    }
    bow_bars();
    wreath();
    window_box();
}
module trim_raw() {
    difference() {
        union() {
            base();
            upper_walls();
            difference() { union() { soffit(); snow_roof(); } chimney_col(); dmw() dm_env(); }
            icicles();
            dmw() { dm_walls(); dm_flare(); dm_snow(); }
            sw_frames();
            door_frame();
            transom();
        }
        room();
        bow_room();
        uw_openings();
        dmw() dm_opening();
        brand_mark();
    }
    // the glass goes back in after the rooms and openings are cut
    difference() { union() { uw_glass(); sw_glass(); bow_glass(); fanlight(); dmw() dm_glass(); } main_room(); bow_room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); bow_room(); sw_openings(); sw_holes(); door_opening(); door_hole(); joints();
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
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
