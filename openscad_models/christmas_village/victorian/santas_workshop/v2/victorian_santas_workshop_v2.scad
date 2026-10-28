// v2 (2026-10-24): the detail-print pilot (Scott, 2026-10-23). The same
// building as ../victorian_santas_workshop.scad, which stays the listed file,
// with detail added under the rules measured on
// ../../../../detail_calibration/ (DETAIL_STANDARD.md there): fine detail
// goes where the toolpath holds it -- across a face, not up it -- and every
// height sits on the 0.2 layer grid. Added: joints between the slates on the
// cones and the roofs, a bracketed corbel table under each cone, a stone
// cornice on dentils under the battlements, planked doors, voussoirs on the
// big windows' arches. Marked "v2:" where they are.
//
// Victorian Santa's Workshop -- the village's centrepiece (Scott, 2026-10-11:
// "It needs to be the center piece of the village. It needs to be bigger and
// more magical within the theme." From five shapes he asked for a mix of the
// workshop castle and the toy factory; of the two mixes he took A.)
//
// A toy factory that is also a castle. A brick hall under three sawtooth
// roofs, each tooth's tall upright face glazed with three lights, so the
// roofline glows from inside. Four round brick turrets wall its corners under
// slate cones, the back two taller. A crenellated gatehouse stands out of the
// front: chocolate-brown doors with wreaths, the SANTA'S WORKSHOP sign over
// them, a rose window above. Two brick chimney stacks climb out of the roof
// as the village's tallest points, garlanded. Seven big arched windows round
// the hall, each with its own scene of toys drawn on the glass. A candy-
// striped NORTH POLE stands at the front corner. On a soft blob of snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed. Each valley between two roof teeth stands on an inside wall, cut
// through by a tall pointed arch so the one light fills all three bays: a
// sawtooth valley over a hollow room otherwise hangs 68 mm over air.
//
// THE WINDOWS, toys, sign and relief helpers are the old workshop's
// (../santas_workshop_v1), with their WHY comments there.
//
// COLOUR PARTS, ONE PRINT (victorian_santas_workshop.3mf), priority
// roof > accent > trim > body:
//   body    brick: the hall, its gables and inside walls, the turrets, the
//           gatehouse, the chimney stacks, the pole's red stripe
//   roof    slate: the roofs and their slates, the turret cones, the doors,
//           the sign boards, the toys and lines drawn on the glass
//   trim    white: snow base and drifts, snow on the roofs and battlements,
//           every frame, sill, pane and bar, the copings, the icicles, the
//           letters, the pole's white stripe and its ball, the wreaths' bows
//   accent  evergreen: the wreaths and the chimney garlands

include <BOSL2/std.scad>
include <../../../../brand/obc_mark.scad>   // the OBC maker's mark
include <../../../../lattice_lib.scad>   // rrect_pts
include <../toys_lib.scad>
include <../../../relief_lib.scad>

$fa = 4;  $fs = 0.4;
part = "all";

wall     = 1.68;
plinth_h = 8;
SH       = 1.2;

// ---- the hall and its sawtooth ------------------------------------------------------------
L = 124;  D = 72;  Lh = L / 2;  Dh = D / 2;
EAVE  = 56;                 // the teeth's low edge
RISE  = 55;                 // each tooth's climb
RIDGE = EAVE + RISE;        // 111
NT    = 3;
// the teeth's runs: the middle one wide enough that a tealight stands in its
// bay with the village's 46 mm circle (48.3 inside), the end two steeper.
// Equal (41.3 each) every bay was 38.7 wide, and the inside walls under the
// valleys cannot open wider than a lancet whose crown stays under the
// valley; a bridged doorway instead printed its lintel's edges over air
// (2026-10-12). Pitches 56.4 / 47.2 / 56.4 deg, so every ceiling prints.
TWS   = [36.5, 51, 36.5];
function xi(i) = i <= 0 ? -Lh : xi(i - 1) + TWS[i - 1];
tr    = 2.5;                // the roof slab, square to its slope
function tvb(i) = tr / cos(atan(RISE / TWS[i]));   // its thickness measured upright
function bay(x) = x < xi(1) ? 0 : x < xi(2) ? 1 : 2;
function z_out(x)  = RIDGE - RISE * (x - xi(bay(x))) / TWS[bay(x)];
function z_ceil(x) = z_out(x) - tvb(bay(x));
// one bay's ceiling, carried past its ends: z_ceil at a valley reads the next bay
function zc_bay(i, x) = RIDGE - RISE * (x - xi(i)) / TWS[i] - tvb(i);
part_w = 1.0;               // the inside wall reaches this far left of its valley

module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

// the building's outline seen from the front: three teeth, each rising
// straight up at its left edge and sloping down to the right
function env_pts(dz = 0, ext = 6) = concat(
    [[-Lh - ext, -5], [Lh + ext, -5], [Lh + ext, EAVE + dz]],
    [for (i = [NT - 1 : -1 : 0]) each [[xi(i + 1), EAVE + dz], [xi(i), RIDGE + dz]]],
    [[-Lh - ext, RIDGE + dz]]);
module envelope(dz = 0) xz(-60, 60) polygon(env_pts(dz));

// ---- placing things on a face: local x across it, local y up, local z out --------------------
// 0 front (-y), 1 back (+y), 2 left end (-x), 3 right end (+x), 4 and 5 the
// upright faces of the second and third teeth (looking -x), 6 the gatehouse's front
GH_y = -Dh - 17 + 0.5;      // the gatehouse's front face (GC[1] - GD / 2)
module face_at(f, u, z) {
    ang = [0, 180, -90, 90, -90, -90, 0][f];
    d   = [Dh, Dh, Lh, Lh, -xi(1), -xi(2), -GH_y][f];
    rotate([0, 0, ang]) translate([u, -d, z]) rotate([90, 0, 0]) children();
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

// ---- brick ------------------------------------------------------------------------------------
bd = 0.6;  bp = 2.6;  br = bd * tan(58);
function zc(k) = plinth_h + 0.4 + k * bp;
function nc(zt) = ceil((zt - plinth_h - 0.4) / bp);
function rpts(w, d, g, z, r = 1.5) = [for (p = rrect_pts(w + 2*g, d + 2*g, r + g, 5)) [p[0], p[1], z]];
// a rounded box whose every course bulges bd out of its face under a 58 deg
// chamfer and over a 45 deg one
module brick_box(w, d, ztop) {
    n = nc(ztop);
    skin(concat([rpts(w, d, 0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
            if (z < ztop + 1) rpts(w, d, g, z)],
        [rpts(w, d, 0, ztop + 2)]), slices = 0);
}
// the same courses round a drum, as a profile to sweep
function brick_ring(R, ztop) = concat([[R - wall - 0.3, plinth_h - 0.5], [R, plinth_h - 0.5]],
    [for (k = [0 : nc(ztop) - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1), z = [z0, z0 + br, z1 - bd][j], g = [0, bd, bd][j])
        if (z < ztop - 0.5) [R + g, z]],
    [[R, ztop], [R - wall - 0.3, ztop]]);

// =====================================================================================
// TURRETS at the four corners
// =====================================================================================
TR   = 15;
TURS = [[-1, -1, 122], [1, -1, 122], [-1, 1, 138], [1, 1, 138]];   // [sx, sy, top of the brick]
cb_h = 4.0;                 // the corbel ring under each cone flares out 3 over 4: 37 deg
cb_o = 3.0;
cone_h = 36;  cone_r = TR + cb_o;
function tpos(t) = [t[0] * Lh, t[1] * Dh];
module turret_drum(t) translate(tpos(t)) rotate_extrude($fn = 96) polygon(brick_ring(TR, t[2] - cb_h));
module turret_corbel(t) translate([tpos(t)[0], tpos(t)[1], t[2] - cb_h]) {
    cylinder(r1 = TR, r2 = cone_r, h = cb_h, $fn = 96);
    corbel_brackets();
}
// v2: a corbel table. Twenty brackets stand 0.8 proud of the flared corbel,
// each starting as a tail on the drum and climbing the corbel's own 37 deg
// (3 out over 4 up) to a flat top at the cone's foot: nothing under them
// hangs, and the plain flare between them reads as the recess of a castle's
// corbelling. 1.8 wide: four beads, solid in the hand.
cbk_n = 20;  cbk_w = 1.8;  cbk_o = 0.8;
module corbel_brackets() let (zt = cb_h, z0 = -cbk_o * cb_h / cb_o - 0.4, a = cbk_w / (TR + 1.5) * 180 / PI)
    for (j = [0 : cbk_n - 1]) rotate(j * 360 / cbk_n - a / 2)
        rotate_extrude(angle = a, $fn = 96)
            polygon([[TR - 0.6, z0 - 0.3], [TR, z0], [cone_r + cbk_o, zt], [TR - 0.6, zt]]);
module turret_cone(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) cylinder(r1 = cone_r, r2 = 0.6, h = cone_h, $fn = 96);
// slates on the cone (the toy shop's courses): each ring's foot an upright
// face 0.9 high at its outer edge, standing on the ring below, the ring
// sloping back into the cone above it. As a flat step 0.9 proud each foot was
// a ledge and the slicer propped all four cones from the table; chamfered
// instead, every lip was a wedge with air under it (2026-10-12)
function r_cone(h) = cone_r * (1 - h / cone_h);
function z_cone(r) = cone_h * (1 - r / cone_r);
cs_n = 10;  cs_d = cone_r * 0.62 / cs_n;
module cone_slates(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) difference() {
    rotate_extrude($fn = 96) for (k = [0 : cs_n - 1]) let (ro = cone_r - k * cs_d, ri = ro - cs_d - 0.5)
        polygon([[ro, max(z_cone(ro) - 1.0, 0)], [ro, z_cone(ro) + 0.9], [ri, z_cone(ri) + 0.05], [ri, max(z_cone(ri) - 1.0, 0)]]);   // not below the cone's foot: there it hung past the corbel
    cone_slate_joints();
}
// v2: the joints between slates. Each ring's lip is cut by radial slots
// 0.5 wide, about 3.2 apart, staggered half a slate ring to ring, so the
// rings read as slates instead of bands. Upright slot walls have no ceiling,
// and a slot this wide keeps its full depth in the slice (the coupon's
// vertical grooves: 0.4 wide held to 0.01 at every layer height). The slots
// stop 0.1 off the cone, so they only ever cut slate.
sj_w = 0.5;
module cone_slate_joints() for (k = [0 : cs_n - 1]) let (ro = cone_r - k * cs_d, ri = ro - cs_d - 0.5,
        n = round(2 * PI * ro / 3.2), z0 = max(z_cone(ro) - 1.2, 0), z1 = z_cone(ri) + 0.3)
    difference() {
        for (j = [0 : n - 1]) rotate((j + (k % 2) / 2) * 360 / n)
            translate([ri - 0.5, -sj_w / 2, z0]) cube([ro - ri + 1.5, sj_w, z1 - z0]);
        translate([0, 0, -0.01]) cylinder(r1 = cone_r + 0.1, r2 = 0.7, h = cone_h + 0.05, $fn = 96);
    }
// snow on the cone's upper third, its foot in waves. The foot is an upright
// face standing on the cone: cut level by a cylinder and bitten from below,
// it was a ledge 1 mm proud all round, and the slicer propped it (2026-10-12).
// One polyhedron: per angle a profile foot -> upright face -> outer face -> top.
sn_A = cone_r + 1.6;  sn_H = cone_h + 1.2;
function r_snow(z) = sn_A * (1 - z / sn_H);
function sn_foot(q, ph) = cone_h * 0.6 + 1.2 + 1.1 * sin(6 * q + ph) + 0.6 * sin(13 * q + 2 * ph);
function z_snow(r) = sn_H * (1 - r / sn_A);
function sn_prof(q, ph) = let (hf = sn_foot(q, ph), rf = r_cone(hf))
    [[rf, hf], [rf, z_snow(rf)], [1.8, sn_H]];
module cone_snow(t) translate([tpos(t)[0], tpos(t)[1], t[2]]) {
    N = 96;  ph = 40 * t[0] + 70 * t[1];
    pts = concat(
        [for (i = [0 : N - 1], p = sn_prof(360 * i / N, ph)) [p[0] * cos(360 * i / N), p[0] * sin(360 * i / N), p[1]]],
        [[0, 0, cone_h * 0.6 - 6], [0, 0, sn_H]]);
    B = 3 * N;  T = B + 1;
    faces = concat(
        [for (i = [0 : N - 1], j = [0 : 1]) let (a = 3 * i + j, b = 3 * ((i + 1) % N) + j) [a, a + 1, b + 1, b]],
        [for (i = [0 : N - 1]) [B, 3 * i, 3 * ((i + 1) % N)]],
        [for (i = [0 : N - 1]) [T, 3 * ((i + 1) % N) + 2, 3 * i + 2]]);
    polyhedron(pts, faces, convexity = 4);
}
// the finial: a neck flaring 51 deg into a ball's upper half, so nothing hangs
module finial(p, z, r = 2.6) translate([p[0], p[1], z]) {
    // the neck climbs 51 deg: at 45 the gate's slicer propped every ball (2026-10-12)
    hn = (r - 0.9) * 1.25;
    cylinder(r1 = 0.9, r2 = r, h = hn);
    // sunk 0.3 into the neck: standing exactly on it, the ball came out a loose
    // second shell touching it in one face (2026-10-11)
    translate([0, 0, hn - 0.3]) intersection() { sphere(r = r, $fn = 32); translate([-r, -r, 0.3]) cube(2 * r); }
}
module turret_room(t) translate(tpos(t)) {
    translate([0, 0, -2]) cylinder(r = TR - wall, h = t[2] + 2, $fn = 96);
    // the cone's hollow: as wide as the room under it and parallel to the cone,
    // 4.7 of slate all the way up. Narrower than the room, it left a 0.6 ledge
    // round the top of every turret that the slicer propped (2026-10-12)
    translate([0, 0, t[2] - 0.01]) cylinder(r1 = TR - wall, r2 = 0.01, h = (TR - wall) * cone_h / cone_r, $fn = 96);
}

// =====================================================================================
// THE GATEHOUSE, crenellated, in the middle of the front
// =====================================================================================
GW = 36;  GD = 17;  GH = 86;  GWh = GW / 2;
GC = [0, -Dh - GD / 2 + 0.5];   // its centre
mer_h = 7;  mer_w = 5.2;
module gate_block() translate(GC) brick_box(GW, GD, GH - 2);   // brick_box runs 2 past its top
// merlons round its top: front and sides; the gaps cut square, the merlons'
// faces flush with the courses' roots
// rounded 1.5 like the brick block under it: square, its corners hung past the block's (2026-10-12)
module merlon2d() difference() { offset(r = 1.5, $fn = 24) square([GW - 3, GD - 3], center = true); square([GW - 2 * 3.0, GD - 2 * 3.0], center = true); }
module crenels() {
    for (i = [0 : 2]) translate([-GWh + 6.2 + i * 11.8 - 3.1, -GD / 2 - 1, 3.4]) cube([6.2 - 0.4, 4.2, 10]);
    // the side crenels centred on the 3 mm wall: centred on its outer face they
    // left a 0.9 sliver of merlon on the walk's side (2026-10-12)
    for (s = [-1, 1]) translate([s * (GWh - 1.5) - 2.1, -GD / 2 + 4.6, 3.4]) cube([4.2, 4.6, 10]);
}
module merlons() translate([GC[0], GC[1], GH]) difference() { linear_extrude(mer_h) merlon2d(); crenels(); }
// snow: a cap on each merlon and a layer in each crenel, flush with the stone.
// Widened 0.3 and run straight across the crenels, the caps hung over air
// (2026-10-12)
module merlon_snow() translate([GC[0], GC[1], GH]) {
    difference() { translate([0, 0, mer_h - 0.2]) linear_extrude(1.2) merlon2d(); crenels(); }
    translate([0, 0, 3.2]) linear_extrude(1.0) merlon2d();
}
// v2: a stone cornice under the battlements, on a course of dentils. The
// cornice climbs out 1.6 from the brick's root over 2.2 (36 deg) to a 2.0
// upright face; each dentil climbs out 1.4 over 2.0 (35 deg) and runs up into
// the cornice's chamfer. At exactly 45 deg, the slicer's threshold, the
// slice of the union put 29,332 support moves under them, from the plate up
// (2026-10-24). Every height is on the 0.2 grid (81.8, 84.0, 86.0; 79.6,
// 81.6): heights snap to whole layers in the slice, so off the grid they
// print up to half a layer off.
// Front and sides only: the band stops 1.0 short of the hall's face.
cn_z0 = GH - 4.2;  cn_z1 = GH - 2.0;  cn_g = 1.6;
dn_z0 = GH - 6.4;  dn_z1 = GH - 4.4;  dn_g = 1.4;  dn_w = 1.2;  dn_p = 2.6;
module gate_cornice() intersection() {
    translate(GC) skin([rpts(GW, GD, 0, cn_z0), rpts(GW, GD, cn_g, cn_z1), rpts(GW, GD, cn_g, GH)], slices = 0);
    translate([-100, -200, 0]) cube([200, 200 - Dh - 1.0, 200]);
}
module dentil(u) hull() {
    translate([u - dn_w / 2, dn_z0, -0.3]) cube([dn_w, 0.01, 0.3]);
    translate([u - dn_w / 2, dn_z1, -0.3]) cube([dn_w, cn_z1 - dn_z1, dn_g + 0.3]);
}
module gate_dentils() for (f = [6, 7, 8]) let (sp = f == 6 ? [-GWh + 2.6, GWh - 2.6] : jspan(f), lo = min(sp), hi = max(sp))
    jface(f) for (u = [lo : dn_p : hi]) dentil(u);
// its room: up to a pitched ceiling, ridge along y, 49 deg, open into the hall
gi = GWh - wall;
// It stops a wall short of the hall: run 3 into it, its ridge cut up through
// the hall's roof behind the gatehouse and left the gatehouse's back 0.5 thick
// above the hall's eave (2026-10-12). The pointed arch is the way through.
gr_y0 = GH_y + wall;  gr_y1 = -Dh - wall + 0.5;
module gate_room2() translate([GC[0], 0, 0]) intersection() {
    translate([-gi, gr_y0, -2]) cube([2 * gi, gr_y1 - gr_y0, 200]);
    xz(-80, 80) polygon([[-gi - 1, -5], [gi + 1, -5], [gi + 1, GH - 3 - (gi + 1) * 1.15], [0, GH - 3], [-gi - 1, GH - 3 - (gi + 1) * 1.15]]);
}
// the way through from the gatehouse into the hall: a pointed arch
// a lancet: each arc's radius 4x the half-span, its centre across the span,
// so the crown's two slopes meet at 48.6 deg. Equilateral (radius 2x), the
// crown met at 30 deg and the slicer propped it (2026-10-12)
module pointed2d(half, spring, k = 4) {
    R = k * half;  c = R - half;
    translate([-half, -5]) square([2 * half, spring + 5]);
    translate([0, spring]) intersection() {
        translate([c, 0]) circle(r = R, $fn = 192);
        translate([-c, 0]) circle(r = R, $fn = 192);
        translate([-half, 0]) square([2 * half, R]);
    }
}
module gate_way() translate([0, -Dh + wall + 0.5, 0]) rotate([90, 0, 0]) linear_extrude(wall + 2) translate([0, plinth_h]) pointed2d(12, 3, 6);   // crown 50.8, slopes 56 deg: at 48.6 the crown's last layers printed as overhang

// ---- the doors, wreaths, sign and rose window on the gatehouse ---------------------------------
function arch_pts(a, hgt, n = 36) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
dr_a = 8;  dr_h = 11;
module door_outline() polygon(arch_pts(dr_a, dr_h));
// v2: each strap starts just outside the first plank groove (2.85 to 7.4).
// From 1.8, the groove at 2.6 left a 0.55 strip of white strap at its inner
// end that the slice dropped: four flags (2026-10-24)
module hinges2d() for (s = [-1, 1], z = [3.4, 9.4]) translate([s * (2.85 + 7.4) / 2, z]) square([7.4 - 2.85, 1.2], center = true);
module door_leaf() face_at(6, 0, plinth_h) difference() {
    translate([0, 0, -wall]) linear_extrude(wall + bd) translate([0, -0.3]) offset(delta = 0.25) polygon(arch_pts(dr_a, dr_h + 0.3));
    translate([0, 0, bd - 0.5]) linear_extrude(2)
        polygon([[-0.4, -1], [0.4, -1], [0.4, dr_h + dr_a - 3], [0, dr_h + dr_a - 3 + 0.4 * tan(60)], [-0.4, dr_h + dr_a - 3]]);
    translate([0, 0, bd - 0.6]) linear_extrude(2) hinges2d();
    door_planks();
}
// v2: the leaves boarded: grooves 0.5 wide, 0.5 deep, either side of the
// meeting line, stopping 1.2 inside the arch. Upright, so the slice keeps
// them to the hundredth (the coupon's vertical grooves). Each ends in a 60
// deg point, like the meeting line: clipped to the arch instead, its top was
// a 0.5 ceiling as shallow as 22 deg near the crown, and the slice propped
// the door with 1,290 support moves (2026-10-24).
function plank_top(u) = dr_h + sqrt(pow(dr_a - 1.2, 2) - pow(abs(u) + 0.25, 2)) - 0.6;
module door_planks() translate([0, 0, bd - 0.5]) linear_extrude(2)
    for (s = [-1, 1], u = [2.6, 5.2]) let (c = s * u, t = plank_top(c))
        polygon([[c - 0.25, -1], [c + 0.25, -1], [c + 0.25, t], [c, t + 0.25 * tan(60)], [c - 0.25, t]]);
// v2: the planks run through the straps too. Stopped under them, each strap's
// underside bridged its groove: 8 overhang perimeters in the slice (2026-10-24)
module hinges() face_at(6, 0, plinth_h) difference() { translate([0, 0, bd - 0.6]) linear_extrude(0.6) hinges2d(); door_planks(); }
module door_opening() face_at(6, 0, plinth_h) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) door_outline();
module door_frame() face_at(6, 0, plinth_h) {
    translate([0, 0, -0.6]) linear_extrude(0.6 + bd) difference() {
        intersection() { offset(r = 1.8) door_outline(); translate([-30, -0.5]) square([60, 100]); }
        door_outline();
    }
    relief_up(-0.4, bd + 0.9) translate([0, dr_h + dr_a - 0.6]) polygon([[-1.3, 0], [1.3, 0], [1.9, 4.0], [-1.9, 4.0]]);
}
wr_z = plinth_h + dr_h + 2.4;
module wreaths() for (s = [-1, 1]) face_at(6, s * 4.0, wr_z) relief_up(-0.2, 0.2 + bd + 0.8) difference() { circle(r = 2.6, $fn = 40); circle(r = 1.3, $fn = 32); }
module bow2d() { polygon([[0, 0], [-1.9, 1.0], [-1.9, -1.0]]);  polygon([[0, 0], [1.9, 1.0], [1.9, -1.0]]); circle(r = 0.8); }
module wreath_bows() for (s = [-1, 1]) face_at(6, s * 4.0, wr_z - 2.6) relief_up(-0.2, 0.2 + bd + 1.2) bow2d();
module step() translate([-dr_a - 2.6, GH_y - 1.9, plinth_h - 0.7]) cube([2 * dr_a + 5.2, 2.0, 3.2]);

module letters_up(h, n) for (i = [0 : n - 1]) let (t0 = i == 0 ? -0.3 : i * h / n - 0.01,
        k = ceil(SH * (i + 1) * h / n / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / n - t0) intersection_for(j = [0 : k]) translate([0, j * 0.2]) children();
sg_z = 36.6;  sg_w = 33;  sg_h = 11.4;
module sign_board() face_at(6, 0, sg_z) relief_up(-0.4, 1.0) translate([-sg_w / 2, 0]) offset(r = 1.0) offset(delta = -1.0) square([sg_w, sg_h]);
module sign_text() face_at(6, 0, sg_z + sg_h / 2) translate([0, 0, 1.0]) letters_up(0.84, 5)
    for (l = [["SANTA'S", 2.6], ["WORKSHOP", -2.6]]) translate([0, l[1]])
        text(l[0], size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.0);

// the rose window: a round pane, its eight spokes and hub drawn on the glass
rose_z = 62;  rose_r = 7.2;
module rose_cut() face_at(6, 0, rose_z) {
    translate([0, 0, -gl_t - 0.2]) cylinder(r = rose_r, h = gl_t + 0.2 + bd + 2, $fn = 64);
    pocket(-gl_t - 0.2, -wall - 1.2) circle(r = rose_r, $fn = 64);
}
module rose_frame() face_at(6, 0, rose_z) relief_up(-0.4, bd + 0.6, 2 * SH) difference() { circle(r = rose_r + 2.4, $fn = 64); circle(r = rose_r - 0.3, $fn = 64); }
module rose_holes() face_at(6, 0, rose_z) relief_hole(-0.4, -0.25, bd + 3, 2 * SH) circle(r = rose_r + 0.1, $fn = 64);
module rose_pane() face_at(6, 0, rose_z) translate([0, 0, -gl_t - 0.2]) cylinder(r = rose_r + 0.6, h = gl_t, $fn = 64);
module rose2d() { circle(r = 1.6, $fn = 32); for (i = [0 : 7]) rotate(i * 45 + 22.5) translate([2.8, -tw / 2]) square([rose_r - 2.6, tw]); }
module rose_art() face_at(6, 0, rose_z) {
    translate([0, 0, -gl_t - 0.2]) linear_extrude(gl_t) intersection() { circle(r = rose_r + 0.6, $fn = 64); rose2d(); }
    // the spokes thickened behind the thin pane, as the toys' lines are
    translate([0, 0, -gl_t - 0.2]) art_in(wall - gl_t - 0.2, 4) intersection() { circle(r = rose_r - 0.1, $fn = 64); offset(r = 0.3) rose2d(); }
    translate([0, 0, -0.2]) art_skirt(0.4, 2) intersection() { circle(r = rose_r - 0.4, $fn = 64); offset(r = 0.2) rose2d(); }
}

// =====================================================================================
// THE BIG TOY WINDOWS: [face, u, sill z, half-width, straight height, scene]
// =====================================================================================
TOYW = [
    [0, -34, 16,  9, 22, 0], [0, 34, 16,  9, 22, 1],
    [1, -34, 16,  9, 22, 2], [1, 0, 16,  9, 22, 3], [1, 34, 16,  9, 22, 4],
    [2,   0, 16, 11, 22, 5], [3,   0, 11, 11, 20, 6],   // the right end's 3 lower: at 14 its head rose into the soffit (2026-10-12)
];
// [floor toys, shelf toys], each [name, x]
SCENES = [
    [[["horse", 0]], [["boat", -4.6], ["soldier", 4.6]]],
    [[["train", 0]], [["jack", -4.4], ["drum", 4.6]]],
    [[["teddy", -4.6], ["drum", 4.6]], [["soldier", -4.6], ["boat", 4.6]]],
    [[["horse", 0]], [["teddy", -4.6], ["jack", 4.4]]],
    [[["train", 0]], [["soldier", -4.6], ["teddy", 4.6]]],
    [[["teddy", -5.6], ["gift", 5.6]], [["boat", -5.6], ["drum", 5.6]]],
    [[["horse", 0]], [["gift", -5.6], ["soldier", 5.6]]],
];
// the panes 0.84 mm, two lines (Scott, 2026-10-28: the glow was weak; the
// line's thin-pane spec from the cocoa cafe v2). Each pane keeps its front
// face where it was, so nothing changes outside; the toys' lines stand art_d
// behind the thinner pane, 2.6 mm on a line against 0.84.
recess = 3.5;  pane_t = 0.84;  sh_r = 1.2;
gl_t = 0.84;   // the other panes (glazed teeth, turrets, rose): their front stays 0.2 behind the face
// From inside, the wall behind a thinned pane is a pocket. Its ceiling climbs
// SH per 1 inward, so it prints like the toy windows' sloped heads.
module pocket(z_glass, z_in) hull() {
    translate([0, 0, z_glass]) linear_extrude(0.01) children();
    translate([0, SH * (z_glass - z_in), z_in]) linear_extrude(0.01) children();
}
fr_w = 2.6;  fr_t = bd + 0.6;  sill = 3.4;
module w_outline(w) polygon(arch_pts(w[3], w[4]));
function w_rise(z) = sh_r * (z + recess);
module w_sec2d(w, z) hull() { w_outline(w); translate([0, w_rise(z)]) w_outline(w); }
module slice(z) translate([0, 0, z]) linear_extrude(0.01) children();
w_z1 = fr_t + 0.6;
module w_cut(w) { hull() { slice(-recess) w_outline(w); slice(w_z1) w_sec2d(w, w_z1); } translate([0, 0, w_z1]) linear_extrude(3) w_sec2d(w, w_z1); }
module w_hole(w) face_at(w[0], w[1], w[2]) w_cut(w);
module w_pane(w) face_at(w[0], w[1], w[2]) translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) offset(r = 1.0) w_outline(w);
w_cd = recess + pane_t;
module w_collar2d(w) union() {
    offset(r = 2.6) w_sec2d(w, fr_t);
    translate([-w[3] - 2.6, -w[2] + 1]) square([2 * (w[3] + 2.6), w[2] - 1 + w[4]]);
}
module w_collar(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd]) linear_extrude(w_cd - wall + 0.4) w_collar2d(w);
module w_collar_col(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd - 0.01]) linear_extrude(w_cd + 0.02) union() {
    w_collar2d(w);
    translate([-w[3] - 2.6, -w[2] - 3]) square([2 * (w[3] + 2.6), w[2] + w[4]]);
}
function w_ftop(w) = w[4] + w[3] + w_rise(fr_t);
module w_frame(w) face_at(w[0], w[1], w[2]) {
    difference() {
        relief_up(-0.4, fr_t) union() { offset(r = fr_w) w_sec2d(w, fr_t); translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]); }
        w_cut(w);
        voussoir_joints(w);
    }
    difference() {
        relief_up(-0.4, fr_t + 0.5) translate([0, w_ftop(w) - 0.2]) polygon([[-1.6, 0], [1.6, 0], [2.2, fr_w + 2.2], [-2.2, fr_w + 2.2]]);
        w_cut(w);
    }
}
// v2: the frame's arch cut into voussoirs: radial joints 0.45 wide, 0.4
// deep, every 15 deg from 22.5 to 157.5 except the keystone's. Sheared with
// the frame (relief_up's SH), so each joint keeps its depth up the face. The
// lowest ones are nearly level; at 22.5 deg a joint's roof is a 0.4 ledge,
// which the coupon's level grooves printed without supports.
module voussoir_joints(w) shear_up() translate([0, 0, fr_t - 0.4]) linear_extrude(1)
    translate([0, w[4] + w_rise(fr_t)]) for (q = [22.5 : 15 : 157.5]) if (abs(q - 90) > 10) rotate(q)
        translate([w[3] - 0.2, -0.225]) square([fr_w + 1.2, 0.45]);
shelf_y = 12.4;  trans_y = 24.0;
module pane_art2d(w) {
    sc = SCENES[w[5]];
    intersection() {
        offset(r = 1.0) w_outline(w);
        union() {
            for (t = sc[0]) translate([t[1], 0.4]) toy(t[0]);
            for (t = sc[1]) translate([t[1], shelf_y + 0.4]) toy(t[0]);
            translate([-30, shelf_y - tw / 2]) square([60, tw]);
            translate([-30, trans_y - tw / 2]) square([60, tw]);
            translate([0, trans_y]) intersection() {
                union() {
                    circle(r = 2.0, $fn = 40);
                    for (i = [1 : 5]) rotate(180 * i / 6) translate([3.2, -tw / 2]) square([30, tw]);
                }
                translate([-40, 0]) square([80, 40]);
            }
        }
    }
}
module w_art(w) face_at(w[0], w[1], w[2]) {
    translate([0, 0, -recess - pane_t]) linear_extrude(pane_t) pane_art2d(w);
    translate([0, 0, -recess]) art_skirt(0.4, 2) offset(r = 0.2) pane_art2d(w);
    translate([0, 0, -recess - pane_t]) art_in(art_d, 4) offset(r = 0.3) pane_art2d(w);
}
// The toys' lines stand art_d out of the back of the pane, so lit from inside
// they show dark on the glow in white plastic too (Scott, 2026-10-12): 3.3 mm
// of plastic on a line against the pane's 1.5. Until then they had never been
// printed at all: the room was cut out of the roof part, which the art is in,
// and it took the 0.8 mm the art stood out with it. w_glow_col keeps the room
// off that space; the lines are 1.4 wide there, over the 1.2 wall floor.
art_d = 1.8;
module w_glow_col(w) face_at(w[0], w[1], w[2]) translate([0, 0, -w_cd - art_d - 1]) linear_extrude(art_d + 1.02)
    hull() { offset(r = 1.3) w_outline(w); translate([0, -SH * art_d - 0.5]) offset(r = 1.3) w_outline(w); }

// =====================================================================================
// THE GLAZED TEETH and the turrets' little windows: segmental, bars on the pane
// [face, u, z, half-width, straight height]
// =====================================================================================
CLER = concat(
    [for (f = [4, 5], u = [-21, 0, 21]) [f, u, EAVE + 7, 5.4, 22]],
    [for (u = [-9.5, 9.5]) [2, u, EAVE + 9, 4.4, 20]]);
function seg_pts(a, hgt, n = 16) =
    let (s = 0.35 * a, R = (a * a + s * s) / (2 * s), zc0 = hgt + s - R, t = asin(a / R))
    concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = t - 2 * t * i / n) [R * sin(q), zc0 + R * cos(q)]]);
function seg_top(a, hgt) = hgt + 0.35 * a;
mull = 1.68;
module s_outline(w) polygon(seg_pts(w[3], w[4]));
module s_bars(w) { translate([-mull / 2, -3]) square([mull, 60]); translate([-20, w[4] * 0.5]) square([40, 2.2]); }
// its head raised by what relief_up's shear takes off it, so the band is fr_w
// deep at its face too: at 1.2 mm it was a wedge the wall check failed (2026-10-12)
module s_frame_outer(w) { hull() { offset(r = fr_w) s_outline(w); translate([0, SH * fr_t]) offset(r = fr_w) s_outline(w); } translate([-w[3] - fr_w - 0.8, -sill]) square([2 * (w[3] + fr_w + 0.8), sill + 1]); }
module s_keystone(w) translate([0, seg_top(w[3], w[4]) - 1.2 + SH * fr_t]) polygon([[-1.3, 0], [1.3, 0], [1.9, fr_w + 2.6], [-1.9, fr_w + 2.6]]);
module cler_holes() for (w = CLER) face_at(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) s_outline(w);
module cler_openings() for (w = CLER) face_at(w[0], w[1], w[2]) {
    translate([0, 0, -gl_t - 0.2]) linear_extrude(gl_t + 0.2 + bd + 2) s_outline(w);
    pocket(-gl_t - 0.2, -wall - 1.2) s_outline(w);
}
module cler_windows() for (w = CLER) face_at(w[0], w[1], w[2]) {
    relief_up(-0.4, fr_t) { s_frame_outer(w); offset(r = 0.3) s_outline(w); }
    relief_up(-0.4, fr_t + 0.5) s_keystone(w);
    relief_up(-0.4, bd) intersection() { offset(r = 0.6) s_outline(w); s_bars(w); }
    translate([0, 0, -gl_t - 0.2]) linear_extrude(gl_t) offset(r = 0.6) s_outline(w);
}
// on the turrets, facing out from the corner: [turret index, z, half-width, height]
TWIN = [for (k = [0 : 3], z = [72, 98]) [k, z + (TURS[k][1] > 0 ? 12 : 0), 3.6, 9]];
function t_ang(k) = atan2(TURS[k][1], TURS[k][0]);
module t_place(k, z) { p = tpos(TURS[k]); translate([p[0], p[1], z]) rotate([0, 0, t_ang(k) + 90]) rotate([90, 0, 0]) children(); }
module t_clip(k, r0, r1) intersection() { children(); translate(tpos(TURS[k])) difference() { cylinder(r = r1, h = 300, $fn = 96); translate([0, 0, -1]) cylinder(r = r0, h = 302, $fn = 96); } }
module tw_outline(w) polygon(seg_pts(w[2], w[3]));
module twin_openings() for (w = TWIN) t_place(w[0], w[1]) {
    translate([0, 0, TR - gl_t - 0.2]) linear_extrude(30) tw_outline(w);
    pocket(TR - gl_t - 0.2, TR - wall - 1.2) tw_outline(w);
}
module twin_holes() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + fr_t + 3) t_place(w[0], w[1]) translate([0, 0, TR]) relief_hole(-1.4, -1.2, fr_t + 2.4) offset(r = 0.4) tw_outline(w);
module twin_frames() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + fr_t) t_place(w[0], w[1]) translate([0, 0, TR]) {
    relief_up(-1.4, fr_t + 0.4) { union() { offset(r = 2.0) tw_outline(w); translate([-w[2] - 2.6, -sill]) square([2 * (w[2] + 2.6), sill + 1]); } offset(r = 0.3) tw_outline(w); }
}
module twin_glass() for (w = TWIN) t_clip(w[0], TR - gl_t - 0.2, TR - 0.2) t_place(w[0], w[1]) translate([0, 0, -2]) linear_extrude(TR + 4) offset(r = 0.6) tw_outline(w);
module twin_bars() for (w = TWIN) t_clip(w[0], TR - 0.4, TR + bd) t_place(w[0], w[1]) translate([0, 0, TR]) relief_up(-1.4, bd + 0.2) intersection() { offset(r = 0.6) tw_outline(w); translate([-mull / 2, -3]) square([mull, 40]); }

// =====================================================================================
// THE ROOF: three slate slopes with their slates and snow, copings on the teeth
// =====================================================================================
ov = 0;                     // past the front and back walls: flush with the mortar. Past it by
                            // 1.6, then by the bricks' 0.6, each slab's corner at a valley began in air (2026-10-12)
e  = 1.0;                   // past the right end's eave, over a white soffit
module slab(i) xz(-Dh - ov, Dh + ov) let (x0 = xi(i), x1 = xi(i + 1) + (i == NT - 1 ? e : 0), tv = tvb(i))
    polygon([[x0, RIDGE - tv], [x0, RIDGE + 0.01], [x1, RIDGE - RISE * (x1 - x0) / TWS[i]], [x1, RIDGE - RISE * (x1 - x0) / TWS[i] - tv]]);
sh_c = 2.35;
module slates(i) {
    x0 = xi(i);  run = TWS[i] + (i == NT - 1 ? e : 0);
    nk = ceil((run - 1.2) / sh_c);
    for (k = [0 : nk - 1]) let (a = run - k * sh_c, b = max(run - (k + 1) * sh_c - 0.5, 1.2))
        if (a > b + 0.3) difference() {
            xz(-Dh - ov, Dh + ov)
                polygon([[x0 + a, RIDGE - RISE * a / TWS[i] - 1.0], [x0 + a, RIDGE - RISE * a / TWS[i] + 0.9], [x0 + b, RIDGE - RISE * b / TWS[i] + 0.05], [x0 + b, RIDGE - RISE * b / TWS[i] - 1.0]]);
            roof_slate_joints(i, k, a, b);
        }
}
// v2: joints across each course, 0.5 wide, slates 3.4 long, staggered half a
// slate course to course; cut only above the slab's top face, as on the cones.
// None within 3 of a turret or a stack: where a turret's column trims a
// course to a point, a joint beside it cut off a shard 0.49 wide that the
// slice dropped (2026-10-24, at the front-left turret)
rs_p = 3.4;
module roof_slate_joints(i, k, a, b) let (x0 = xi(i))
    difference() { roof_slate_joints0(i, k, a, b);
        for (t = TURS) translate(tpos(t)) translate([0, 0, -1]) cylinder(r = TR + bd + 3, h = 300, $fn = 96);
        for (s = STACKS) translate([s[0], s[1], -1]) cylinder(r = s[2] + 0.8 + 3, h = 300, $fn = 72);
    }
module roof_slate_joints0(i, k, a, b) let (x0 = xi(i))
    intersection() {
        for (y = [-Dh - ov + 1.2 + (k % 2) * rs_p / 2 : rs_p : Dh + ov - 1.2])
            translate([x0 + b - 0.6, y - sj_w / 2, RIDGE - RISE * a / TWS[i] - 1.5]) cube([a - b + 1.2, sj_w, RISE * (a - b) / TWS[i] + 3]);
        xz(-Dh - ov - 1, Dh + ov + 1) polygon([[x0 + b - 1, RIDGE - RISE * (b - 1) / TWS[i] + 0.1], [x0 + a + 1, RIDGE - RISE * (a + 1) / TWS[i] + 0.1],
                                                [x0 + a + 1, RIDGE + 20], [x0 + b - 1, RIDGE + 20]]);
    }
// snow from each ridge down a wavy line
function sn_run(y, i) = 11 + 2.4 * sin(y * 13 + 70 * i) + 1.4 * sin(y * 37 + 30 * i);
module roof_snow(i) intersection() {
    x0 = xi(i);
    xz(-Dh - ov, Dh + ov) polygon([[x0 - 0.01, RIDGE - 1.0],   // flush with the slab's ends: 0.3 past them it hung (2026-10-12)
         [x0 - 0.01, RIDGE + 1.6], [x0 + 22, RIDGE - RISE * 22 / TWS[i] + 1.8], [x0 + 22, RIDGE - RISE * 22 / TWS[i] - 1.0]]);
    linear_extrude(200) polygon(concat([for (k = [0 : 40]) let (y = -Dh - 3 + (D + 6) * k / 40) [x0 + sn_run(y, i), y]], [[x0 - 1, Dh + 3], [x0 - 1, -Dh - 3]]));
}
// under the right end's eave, a white soffit from the wall out to the slab's
// lip at 45 deg: run out past the wall alone, the slab's lowest edge was its
// tip, and that printed in air (2026-10-12)
z_tip = RIDGE - RISE * (TWS[NT - 1] + e) / TWS[NT - 1] - tvb(NT - 1);      // the slab's underside at its lip
z_sof = z_tip - e * tan(55);                    // where the soffit meets the wall
module soffit() xz(-Dh - ov, Dh + ov) polygon([[Lh - 0.5, z_tip - (e + 0.5) * tan(55)], [Lh + e, z_tip], [Lh + e, z_tip + 2], [Lh - 0.5, z_tip + 3]]);   // 55: at 45 the slicer propped it
// a white coping along the top of each glazed tooth, over its slope's start
// its lip 0.6 over the upright face climbs 50 deg to it: as a square block the
// lip hung over the flat glazed face and the slicer propped it (2026-10-12)
module copings() for (i = [0 : NT - 1]) let (x0 = xi(i)) xz(-Dh - ov, Dh + ov)
    // its back edge sunk into the slope below it: level, it hung over the steep end teeth (2026-10-12)
    polygon([[x0 + wall + 0.8, RIDGE - RISE * (wall + 0.8) / TWS[i] - 0.5], [x0 + wall + 0.8, RIDGE + 1.6], [x0 - 0.6, RIDGE + 1.6], [x0 - 0.6, RIDGE - 0.1], [x0, RIDGE - 0.82]]);

// =====================================================================================
// CHIMNEY STACKS: round brick, a corbelled cap, an evergreen garland
// =====================================================================================
STACKS = [[-43.75, 8, 8, 176], [43.75, 8, 9, 192]];   // [x, y, r, top]
// one in the middle of each end bay. Until 2026-10-28 each ran down through
// the hall to the floor as a hollow brick flue: decoration only, and the two
// solid columns kept the light in the middle bay (Scott's print). The roof's
// slab carries a stack (its underside climbs 56 deg, and the stack's wall
// stands on it all round), so now the room takes everything under the
// ceiling and each stack starts there; its bore still opens into the hall.
module stack_body(s) translate([s[0], s[1], 0]) {
    rotate_extrude($fn = 72) polygon(brick_ring(s[2], s[3] - 7));
    // the cap's corbel flares 2.2 over 3.0 (36 deg): at 45 the gate's slicer propped it (2026-10-12)
    translate([0, 0, s[3] - 7]) cylinder(r1 = s[2], r2 = s[2] + 2.2, h = 3.0, $fn = 72);
    translate([0, 0, s[3] - 4.0]) cylinder(r = s[2] + 2.2, h = 4.0, $fn = 72);
}
module stack_bore(s) translate([s[0], s[1], -1]) cylinder(r = s[2] - 2.0, h = s[3] + 2, $fn = 48);
module stack_col(s) translate([s[0], s[1], -1]) cylinder(r = s[2] + 0.8, h = s[3], $fn = 72);
module stack_snow(s) translate([s[0], s[1], s[3] - 0.01]) difference() {
    cylinder(r1 = s[2] + 2.2, r2 = s[2] + 1.0, h = 1.6, $fn = 72);
    translate([0, 0, -1]) cylinder(r = s[2] - 1.2, h = 4, $fn = 48);
}
// the garland: a ring 1.6 proud, its underside climbing 52 deg from inside
// the brick, and a bobble
// every 30 deg on a cone under it. At 45 deg, with whole spheres for
// bobbles, the slicer propped the ring and every lower half (2026-10-12)
module bobble(r = 1.0) { translate([0, 0, -1.5]) cylinder(r1 = 0.05, r2 = r * 0.94, h = 1.5 - r * 0.34, $fn = 16); intersection() { sphere(r = r, $fn = 16); translate([-r, -r, -r * 0.34]) cube(2 * r); } }
module garland(s) translate([s[0], s[1], s[3] - 22]) difference() {
    union() {
        cylinder(r1 = s[2] - 0.3, r2 = s[2] + 1.6, h = 2.4, $fn = 72);
        translate([0, 0, 2.4]) cylinder(r = s[2] + 1.6, h = 2.0, $fn = 72);
        for (i = [0 : 11]) rotate(i * 30) translate([s[2] + 1.2, 0, 3.6]) bobble();
    }
    translate([0, 0, -1]) cylinder(r = s[2] - 0.2, h = 8, $fn = 72);
}

// =====================================================================================
// THE NORTH POLE: candy-striped, a ball on top, a sign on brackets
// =====================================================================================
NP = [-95, -55];  np_r = 5.2;  np_top = 104;
module np_spiral(half) translate([NP[0], NP[1], plinth_h - 1]) linear_extrude(np_top - plinth_h + 1, twist = -720, slices = 160)
    intersection() { circle(r = np_r, $fn = 48); rotate(half * 180) translate([-np_r, 0]) square([2 * np_r, np_r]); }
module np_ball() finial([NP[0], NP[1]], np_top - 0.01, 6.0);
nps_z = 76;  nps_w = 40;  nps_h = 10.2;
module np_board() translate([NP[0], NP[1] - np_r - 2.0, nps_z]) {
    translate([-nps_w / 2, 0, 0]) cube([nps_w, 3.0, nps_h]);
    // knee braces under each half: the hull of a strip sunk in the pole and the
    // board's end, so the underside climbs 50 deg from the pole and the whole
    // brace stands on it. Set in front of the board with their tips clear of
    // the pole, they started in air and left the board's back unpropped (2026-10-12)
    for (s = [-1, 1]) hull() {
        translate([-0.5, 2.0, -(nps_w / 2) * tan(50)]) cube([1.0, np_r, 0.01]);
        translate([-0.5, 0, -0.01]) cube([1.0, 3.0, 0.01]);
        translate([s * (nps_w / 2 - 0.005), 1.5, -0.005]) cube([0.01, 3.0, 0.01], center = true);
    }
}
module np_text() translate([NP[0], NP[1] - np_r - 2.0, nps_z + nps_h / 2]) rotate([90, 0, 0]) letters_up(0.84, 5)
    text("NORTH POLE", size = 3.4, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.02);

// =====================================================================================
// ICICLES under the right end's eave and the gatehouse's walk
// =====================================================================================
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
module icicle2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + 0.5]) circle(r = 0.5); }
// either side of the toy window, between its frame and the turrets. (Spread
// over the whole end, every one fell inside the window's keep-out and none
// was made, 2026-10-12.)
IC_R = [for (i = [0 : 3]) [[-19.4, -17.2, 17.2, 19.4][i], 2.2 + 2.2 * rnd(i, 7), 1.6 + 0.4 * rnd(i, 17)]];
module icicles() {
    for (c = IC_R) face_at(3, c[0], z_sof - 0.6) relief_up(-0.4, bd + 0.8) icicle2d(c[1], c[2]);
}

// =====================================================================================
// THE SNOW BASE
// =====================================================================================
module footprint() {
    square([L, D], center = true);
    for (t = TURS) translate(tpos(t)) circle(r = TR + 1);
    translate(GC) square([GW, GD], center = true);
    translate(NP) circle(r = 9);
    translate([NP[0], NP[1] - 3]) square([nps_w, 6], center = true);
}
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[-Lh - 2, 0, 3.5, 9, 2.8], [Lh + 2, 0, 3.5, 9, 2.4], [-48, Dh + 2, 7, 3.5, 2.6], [48, Dh + 2, 7, 3.5, 2.4],
          [-25, -Dh - 3, 3.0, 2.6, 2.2], [24, -Dh - 3, 3.0, 2.6, 2.2], [NP[0] + 8, NP[1] + 2, 4, 4, 2.6]];
module base() {
    base_slab();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.5]) intersection() {
            scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
            translate([-60, -60, 0]) cube(120);
        }
        linear_extrude(plinth_h + 10) offset(delta = -2.4) base2d();
    }
}
// at y -40 it came 0.2 from the base's edge, at x 40 0.7 from the turret's open floor (2026-10-12)
module brand_mark() translate([32, -Dh - 3.0, 0]) obc_cut(4.6);       // the letters, cut from the base
module brand_inlay() translate([32, -Dh - 3.0, 0]) obc_inlay(4.6);    // and filled in the roof's colour

// =====================================================================================
// THE ROOM: one space under the three teeth, the turrets and the gatehouse,
// less the inside walls under the valleys (each with its pointed arch), the
// windows' collars and the stacks
// =====================================================================================
module hall_room() for (i = [0 : NT - 1]) {
    x0 = xi(i) + wall;  x1 = xi(i + 1) - (i == NT - 1 ? wall : part_w);
    intersection() {
        translate([x0, -Dh + wall, -2]) cube([x1 - x0, D - 2 * wall, 200]);
        xz(-60, 60) polygon([[x0 - 1, -5], [x1 + 1, -5], [x1 + 1, zc_bay(i, x1 + 1)], [x0 - 1, zc_bay(i, x0 - 1)]]);
    }
}
// The openings through the inside walls (2026-10-28). Each inside wall
// carries a roof valley: the lower tooth's slab ends there along a level
// line 68 mm from the front wall to the back, and the next tooth's glazed
// face stands on it. With nothing under it that line prints in the air. Till
// now each wall had a 24 mm lancet, so one tealight lit the middle bay and
// little else (Scott's print). Now the opening is as wide as the room at the
// floor and closes to a point under the valley, its sides 38 deg from upright:
// what is left of each wall is two triangles hanging from the front and back
// walls, and they carry the valley line from the walls to the middle.
va_top = 50.6;                           // its point: 0.9 under the valley's ceiling (51.5)
va_hw  = Dh - wall;                      // as wide as the room
va_lo  = va_top - va_hw / tan(38);       // 6.7: where its sides reach the walls
module valley_arches() for (i = [1 : NT - 1]) translate([xi(i) + wall / 2, 0, 0]) rotate([90, 0, 90]) translate([0, 0, -6]) linear_extrude(12)
    polygon([[-va_hw, -5], [va_hw, -5], [va_hw, va_lo], [0, va_top], [-va_hw, va_lo]]);
// each inside wall's foot 0.3 thicker, up to the eave: at wall + part_w the
// window collars' columns stopped 0.1 short of it, a sealed hairline slit down
// the wall that print_fidelity flagged (2026-10-11). Thickened all the way up,
// it set the glazed teeth's windows 0.3 back from their inner face, under a
// flat head the slicer propped (2026-10-12)
module part_shims() for (i = [1 : NT - 1]) difference() {
    translate([xi(i) + wall - 0.01, -Dh, -5]) cube([0.31, D, EAVE + 5]);
    valley_arches();
}
// a lancet doorway from the hall into each turret, facing the hall's middle
module turret_door(t) translate(tpos(t)) rotate([0, 0, atan2(-t[1], -t[0])])
    translate([TR - wall - 1.5, 0, plinth_h]) rotate([90, 0, 90]) hull() {
        // jambs radial: parallel, they met the drum's face at 70 deg and left a
        // knife edge of wall along each (2026-10-12)
        linear_extrude(0.01) scale([(TR - wall - 1.5) / (TR + 1.5), 1]) pointed2d(5, 30, 6);
        translate([0, 0, wall + 3 - 0.01]) linear_extrude(0.01) pointed2d(5, 30, 6);
    }   // crown 54.6, its slopes 56 deg (steeper inside, where the jambs close in): cut
        // through the curved wall at 48.6 deg the slicer still propped it (2026-10-12)
module room() difference() {
    union() {
        // kept out of the turrets: where the hall's room ran into a turret it
        // took the turret's wall away up to the hall's ceiling, and the wall
        // above started in air along a near-level edge (2026-10-12)
        difference() { hall_room(); for (t = TURS) translate(tpos(t)) translate([0, 0, -5]) cylinder(r = TR, h = 300, $fn = 96); }
        for (t = TURS) turret_door(t);
        valley_arches();
        for (t = TURS) turret_room(t);
        gate_room2();
        gate_way();
    }
    for (w = TOYW) w_collar_col(w);
    part_shims();
}

// =====================================================================================
// BRICK BOND: Scott wanted the brick of the post office and chapel (2026-10-12).
// Courses alone read as clapboard. Upright joints, staggered half a brick
// course to course, each a whole course tall and floored 0.1 behind the
// course's root as on the post office, so nothing they leave has a ceiling.
// Left out near corners, turrets, frames, the door, the sign, the rose, the
// icicles, under every roof's edge and round the garlands.
// =====================================================================================
bl = 7;  bj = 0.6;  JM = 1.5;
// the upright faces of the second and third teeth were plain: courses on them
// too, between the roof below and 6 under the ridge (the slab's end above)
tk0 = ceil((EAVE + 2.5 - plinth_h - 0.4) / bp);
tk1 = floor((RIDGE - 6 - plinth_h - 0.4) / bp);
module tooth_courses() for (i = [1 : NT - 1]) translate([xi(i), 0, 0]) mirror([1, 0, 0]) xz(-Dh, Dh)
    polygon(concat([[-0.5, zc(tk0)]],
        [for (k = [tk0 : tk1 - 1], j = [0 : 2]) let (z0 = zc(k), z1 = zc(k + 1)) [[0, z0], [bd, z0 + br], [bd, z1 - bd]][j]],
        [[0, zc(tk1)], [-0.5, zc(tk1)]]));
// faces: 0-6 as face_at, 7 and 8 the gatehouse's +x and -x sides
module jface(f) if (f <= 6) face_at(f, 0, 0) children();
    else translate([(f == 7 ? 1 : -1) * GWh, 0, 0]) rotate([0, 0, f == 7 ? 90 : -90]) rotate([90, 0, 0]) children();
function jspan(f) = f <= 1 ? [-(Lh - TR - 3.1), Lh - TR - 3.1] : f <= 3 ? [-(Dh - TR - 3.1), Dh - TR - 3.1]
    : f <= 5 ? [-(Dh - 2.5), Dh - 2.5] : f == 6 ? [-(GWh - 2.5), GWh - 2.5]
    : f == 7 ? [GH_y + 2.5, -Dh - 3.1] : [Dh + 3.1, -GH_y - 2.5];
function jtop(f, u) = f == 0 ? min(z_ceil(u - 1.2), z_ceil(u + 1.2)) - 1
    : f == 1 ? min(z_ceil(-u - 1.2), z_ceil(-u + 1.2)) - 1
    : f == 2 ? RIDGE - tvb(0) - 1 : f == 3 ? z_sof - 7 : f <= 5 ? zc(tk1)
    : dn_z0 - 1.2;   // v2: the joints end a course under the dentils, so none runs up between them
function jbot(f) = (f == 4 || f == 5) ? zc(tk0) : 0;
function jkeep(f) = concat(
    [for (w = TOYW) if (w[0] == f) [w[1] - w[3] - fr_w - 0.8, w[1] + w[3] + fr_w + 0.8, w[2] - sill, w[2] + w_ftop(w) + 4.6]],
    [for (w = CLER) if (w[0] == f) [w[1] - w[3] - fr_w - 0.8, w[1] + w[3] + fr_w + 0.8, w[2] - sill, w[2] + seg_top(w[3], w[4]) + 5.6]],
    f == 0 ? [[-GWh - 0.6, GWh + 0.6, 0, 300]] : [],
    f == 6 ? [[-dr_a - 1.8, dr_a + 1.8, 0, plinth_h + dr_h + dr_a + 3.4], [-sg_w / 2, sg_w / 2, sg_z, sg_z + sg_h],
              [-rose_r - 2.4, rose_r + 2.4, rose_z - rose_r - 2.4, rose_z + rose_r + 2.4]] : []);
function jclear(u, z0, z1, ko) = len([for (b = ko) if (u + bj / 2 + JM > b[0] && u - bj / 2 - JM < b[1] && z1 + JM > b[2] && z0 - JM < b[3]) 1]) == 0;
function jus(f, k) = let (sp = jspan(f), z0 = zc(k), z1 = zc(k + 1), ko = jkeep(f))
    z0 < jbot(f) ? [] : [for (u = [sp[0] + (k % 2) * bl / 2 : bl : sp[1]]) if (z1 <= jtop(f, u) && jclear(u, z0, z1, ko)) u];
// one prism per face: every joint on it lies at the same depth
module face_joints(f) jface(f) translate([0, 0, -0.1]) linear_extrude(2.2)
    for (k = [1 : 45]) for (u = jus(f, k)) translate([u - bj / 2, zc(k)]) square([bj, bp]);
// round walls: radial joints, all of one drum's in one polyhedron (a few
// hundred separate boxes would each be a CGAL union)
function jbox(c, a, r0, r1, z0, z1) = let (ca = cos(a), sa = sin(a))
    [for (r = [r0, r1], t = [-bj / 2, bj / 2], z = [z0, z1]) [c[0] + r * ca - t * sa, c[1] + r * sa + t * ca, z]];
JF = [[0, 4, 6, 2], [1, 5, 4, 0], [3, 7, 5, 1], [5, 7, 6, 4], [7, 3, 2, 6], [3, 1, 0, 2]];
module boxes(B) if (len(B) > 0) polyhedron([for (b = B) each jbox(b[0], b[1], b[2], b[3], b[4], b[5])],
    [for (n = [0 : len(B) - 1], q = JF) [for (i = q) i + 8 * n]]);
function adiff(a, b) = abs(((a - b) % 360 + 540) % 360 - 180);
function t_exposed(p) = max(abs(p[0]) - Lh, abs(p[1]) - Dh) > 3.1;
function t_twin_clear(ti, a, z0, z1) = len([for (w = TWIN) if (w[0] == ti
    && adiff(a, t_ang(ti)) < (w[2] + 2.6 + JM + bj / 2) / TR * 180 / PI
    && z1 + JM > w[1] - sill && z0 - JM < w[1] + seg_top(w[2], w[3]) + 2.0) 1]) == 0;
function turret_jb(ti) = let (t = TURS[ti], c = tpos(t), n = 13)
    [for (k = [1 : 60], j = [0 : n - 1]) let (z0 = zc(k), z1 = zc(k + 1), a = t_ang(ti) + (j + (k % 2) / 2) * 360 / n,
         p = [c[0] + (TR + 0.3) * cos(a), c[1] + (TR + 0.3) * sin(a)])
        if (z1 <= t[2] - cb_h - 1 && t_exposed(p) && t_twin_clear(ti, a, z0, z1)) [c, a, TR - 0.1, TR + 2.1, z0, z1]];
function stack_jb(s) = let (n = round(2 * PI * s[2] / bl))
    [for (k = [1 : 75], j = [0 : n - 1]) let (z0 = zc(k), z1 = zc(k + 1), a = (j + (k % 2) / 2) * 360 / n,
         x = s[0] + (s[2] + 0.3) * cos(a))
        if (z0 >= max(z_out(x - 1.2), z_out(x + 1.2)) + 2.0 && z1 <= s[3] - 7.5 && (z1 < s[3] - 24 || z0 > s[3] - 16))
            // 0.05 up: flush with the courses, a joint's flat top met a ring of the
            // stack's 72-gon edge-on at 138.4 and 164.4, and the union exported two
            // edges shared by four faces (product_gate: not watertight, 2026-10-13)
            [[s[0], s[1]], a, s[2] - 0.1, s[2] + 2.1, z0 + 0.05, z1 + 0.05]];
module brick_joints() {
    for (f = [0 : 8]) face_joints(f);
    for (ti = [0 : 3]) boxes(turret_jb(ti));
    for (s = STACKS) boxes(stack_jb(s));
}

// =====================================================================================
// PARTS
// =====================================================================================
module hall_walls() intersection() { brick_box(L, D, RIDGE + 2); envelope(0.6); }
module body_raw() {
    hall_walls();
    tooth_courses();
    for (t = TURS) { turret_drum(t); turret_corbel(t); }
    gate_block();
    merlons();
    for (w = TOYW) w_collar(w);
    for (s = STACKS) stack_body(s);
    np_spiral(0);
    step();
}
module turret_cols() for (t = TURS) translate(tpos(t)) translate([0, 0, -1]) cylinder(r = TR + bd, h = 300, $fn = 96);
// the maker's mark is inlaid in the roof's colour (2026-10-14): ../../../brand/obc_mark.scad
module roof_raw() { roof_raw0(); brand_inlay(); }
module roof_raw0() {
    difference() {
        union() { for (i = [0 : NT - 1]) { slab(i); slates(i); } }
        for (s = STACKS) stack_col(s);
        turret_cols();
    }
    for (t = TURS) { turret_cone(t); cone_slates(t); }
    door_leaf();
    difference() { sign_board(); sign_text(); }
    difference() { np_board(); np_text(); }
    for (w = TOYW) w_art(w);
    rose_art();
}
module accent_raw() { wreaths(); for (s = STACKS) garland(s); }
// =====================================================================================
// THE FLOOR: three tealights (Scott, 2026-10-28: one never lit the building).
// The base is open and the lights stand on the table; three rings on the bed,
// tied to the base, set each one where it lights a bay. Lower the building
// over the lights and the rings' chamfers centre them. A row of three 46 mm
// bays needs 138 mm and the hall is 120.6 inside, its corners taken by the
// turrets; staggered, three circles fit at 42.4 at most, so the rings are
// 41.6 across (a 38 mm light with 0.6 to spare all round), the middle one to
// the front under the gatehouse, the end ones to the back.
// =====================================================================================
LIGHTS = [[-36.5, 9.5], [0, -13.1], [36.5, 9.5]];
lr_i = 19.6;  lr_t = 1.2;  lr_h = 1.6;  lr_w = 1.6;
module spoke(p, q) hull() { translate([p[0], p[1], 0]) cylinder(r = lr_w / 2, h = lr_h, $fn = 16); translate([q[0], q[1], 0]) cylinder(r = lr_w / 2, h = lr_h, $fn = 16); }
function toward(p, q, d) = p + d * (q - p) / norm(q - p);
module floor_rings() {
    ro = lr_i + lr_t;
    for (c = LIGHTS) translate([c[0], c[1], 0]) rotate_extrude($fn = 128)
        polygon([[lr_i, 0], [ro, 0], [ro, lr_h], [lr_i + 0.6, lr_h], [lr_i, lr_h - 0.6]]);
    for (sx = [-1, 1]) let (c = [sx * 36.5, 9.5]) {
        spoke([c[0] + sx * (ro - 0.3), c[1]], [sx * 59, c[1]]);          // into the end wall's foot
        spoke([c[0], c[1] + ro - 0.3], [c[0], 33]);                     // the back wall's
        spoke([c[0], c[1] - ro + 0.3], [c[0], -33]);                    // the front wall's
        spoke(toward(c, LIGHTS[1], ro - 0.3), toward(LIGHTS[1], c, ro - 0.3));   // to the middle ring
    }
    spoke([0, -13.1 + ro - 0.3], [0, 33]);
    for (sx = [-1, 1]) spoke([sx * 15, -13.1 - sqrt(ro * ro - 225) + 0.3], [sx * 15, -35]);
}
module trim_raw() {
    floor_rings();
    difference() {
        union() {
            base();
            difference() { union() { for (i = [0 : NT - 1]) roof_snow(i); copings(); soffit(); } for (s = STACKS) stack_col(s); turret_cols(); }
            for (t = TURS) { cone_snow(t); finial(tpos(t), t[2] + cone_h - 0.6); }
            merlon_snow();
            gate_cornice(); gate_dentils();   // v2
            for (s = STACKS) stack_snow(s);
            for (w = TOYW) { w_frame(w); w_pane(w); }
            cler_windows();
            twin_frames(); twin_glass(); twin_bars();
            rose_frame(); rose_pane();
            door_frame(); hinges(); wreath_bows();
            sign_text(); np_text();
            np_spiral(1); np_ball();
            icicles();
        }
        room();
        brand_mark();
    }
}
module roof_part()   difference() { roof_raw(); difference() { room(); for (w = TOYW) w_glow_col(w); } }
module accent_part() difference() { accent_raw(); roof_raw(); }
module trim_part()   difference() { trim_raw(); accent_raw(); roof_raw(); }
module body_part() {
    difference() {
        body_raw();
        room();
        for (s = STACKS) stack_bore(s);
        for (w = TOYW) w_hole(w);
        cler_openings(); cler_holes();
        twin_openings(); twin_holes();
        rose_cut(); rose_holes();
        door_opening();
        brick_joints();
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
else if (part == "all") {
    color("#A8483A") body_part();
    color("#2E3440") roof_part();
    color("#F4F1EA") trim_part();
    color("#2F6B45") accent_part();
}
