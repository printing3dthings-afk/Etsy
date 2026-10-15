// Victorian frozen fountain (2026-10-14), a village accessory from the second
// batch of studies (../concepts/accessories2_scene.jpg).
//
// A twelve-sided brick basin with a stone coping, frozen over; a column rises
// from the ice to a bowl, a smaller bowl above it, and a jet frozen in the air
// on top. The water froze as it fell: columns of ice run from each bowl's rim
// down to the ice below, which is what lets the bowls print. A wreath with a
// red bow hangs on the basin's front, snow lies on the ice. On a soft blob of
// snow, the maker's mark under it.
//
// The study had icicles hanging from the bowl's rim. Hanging, each tip is an
// island in the air the slicer must prop; run down to the ice, they are columns
// the bowl stands on.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
MARK = [[0, 0], 5.0];         // the maker's mark: where on the base, its cap height
SH = 1.2;
C = 1 / cos(15);            // a twelve-gon's corner, per 1 of its flat

zb = 3.2;                   // the snow's top
A_o = 21;                   // the basin's outer flats
A_i = 18;                   // its inner flats
z_w = 9.0;                  // the wall's top
z_i = 6.4;                  // the ice
z_c = z_w + 0.8 * SH + 1.4; // the coping's top: its lip 1.4, at 1.0 it read under one bead

module dodec_rev() rotate([0, 0, 15]) rotate_extrude($fn = 12) children();
function cs(pts) = [for (p = pts) [p[0] * C, p[1]]];

// the basin: brick, two course lines cut round it, the ice inside
ZG = [5.0, 7.2];
module basin() dodec_rev() polygon(cs(concat([[A_i, 2.4], [A_o, 2.4]],
    [for (z = ZG) each [[A_o, z], [A_o - 0.45, z], [A_o - 0.45, z + 0.1], [A_o, z + 0.1 + 0.45 * SH]]],
    [[A_o, z_w + 0.01], [A_i, z_w + 0.01]])));
module coping() dodec_rev() polygon(cs([[A_i, z_w], [A_o, z_w], [A_o + 0.8, z_w + 0.8 * SH], [A_o + 0.8, z_c], [A_i, z_c]]));
module ice() dodec_rev() polygon(cs([[0, 2.4], [A_i + 0.01, 2.4], [A_i + 0.01, z_i], [0, z_i]]));

// the column and the bowls: every underside climbs SH per 1 in
R_col = 3.0;
z_b1 = 26.0;                // the big bowl's rim
R_b1 = 11.0;
z_b2 = 35.0;                // the small bowl's rim
R_b2 = 5.6;
module column() rotate_extrude($fn = 48) polygon([
    [0, z_i - 0.5], [5.0, z_i - 0.5], [5.0, z_i + 0.8], [R_col, z_i + 0.8 + 2.0 * SH],      // its foot, stepping in
    [R_col, z_b1 - (R_b1 - R_col) * SH], [R_b1, z_b1], [R_b1, z_b1 + 1.4],                // the big bowl, lip 1.4
    [R_b1 - 1.2, z_b1 + 1.4], [R_b1 - 1.2, z_b1 + 0.4], [2.2, z_b1 + 0.4],              // its ice, below the lip
    [2.2, z_b2 - (R_b2 - 2.2) * SH], [R_b2, z_b2], [R_b2, z_b2 + 1.4],                   // the small bowl, lip 1.4
    [R_b2 - 1.2, z_b2 + 1.4], [R_b2 - 1.2, z_b2 + 0.4], [0, z_b2 + 0.4]]);
// the bowls' ice, slate like the basin's
module bowl_ice() {
    translate([0, 0, z_b1 - 0.1]) cylinder(r = (R_b1 - 1.2) * 0.999, h = 0.6, $fn = 48);
    translate([0, 0, z_b2 - 0.1]) cylinder(r = (R_b2 - 1.2) * 0.999, h = 0.6, $fn = 48);
}
// the jet, frozen as it splashed: a crown of spikes, each leaning out 25 deg
module jet() translate([0, 0, z_b2 + 0.3]) {
    cylinder(r1 = 1.7, r2 = 1.2, h = 1.2, $fn = 24);
    hull() { cylinder(r = 1.0, h = 1.2, $fn = 16); translate([0, 0, 7.0]) sphere(0.62, $fn = 12); }
    for (i = [0 : 4]) rotate([0, 0, 72 * i]) hull() {
        translate([0.6, 0, 0.6]) cylinder(r = 0.9, h = 0.6, $fn = 12);
        translate([0.6 + 4.2 * tan(25), 0, 4.8]) sphere(0.62, $fn = 12);   // tips 1.2 across
    }
}
// The water froze as it spilled: streams of ice pour over each bowl's lip,
// narrow as they fall the way icicles do, and land in a frozen splash on the
// ice below, so each one stands on something. Uneven widths and spacing keep
// them from reading as a ring of posts, which is what the study's even, round
// falls looked like; a fluted veil all round read as a cake (2026-10-14).
// Each stream's sides lean under 6 deg, so they print.
function jit(i, k) = (((i * 37 + k * 11) % 17) / 16 - 0.5);       // a fixed scatter, -0.5..0.5
// A stream narrows and swells as it falls, the way an icicle does, through
// four knots: a smooth taper read as a rod. Each knot's width changes slowly
// enough over its drop that no side leans past 6 deg.
module knot(r, z, t, w, h) translate([r, 0, z]) scale([t / 2, w / 2, h]) sphere(1, $fn = 16);
module stream(r0, z0, r1, z1, wt, wb, t, k) {
    F = [0, 0.3, 0.62, 1];                                      // how far down
    W = [wt, wt * (0.72 + 0.1 * jit(k, 5)), wt * (0.86 + 0.1 * jit(k, 6)), wb];
    for (i = [0 : 2]) hull() {
        knot(r0 + (r1 - r0) * F[i], z0 + (z1 - z0) * F[i], t * (i == 0 ? 1 : 0.95), W[i], 0.7);
        knot(r0 + (r1 - r0) * F[i + 1], z0 + (z1 - z0) * F[i + 1], t * 0.95, W[i + 1], i == 2 ? 0.05 : 0.7);
    }
}
module splash(r, z, w) translate([r, 0, z - 0.3]) scale([w * 0.6, w * 0.75, 0.55]) intersection() {
    sphere(1, $fn = 20); translate([-2, -2, 0]) cube(4);
}
module falls(n, R, ztop, zlow, wt) for (i = [0 : n - 1]) let (a = 360 * i / n + 14 * jit(i, 1), w = wt * (1 + 0.7 * jit(i, 2)),
        zl = zlow) rotate([0, 0, a]) {
    stream(R - 0.1, ztop, R + 1.0, zl + 0.2, w, max(1.4, w * 0.6), 1.8, i);
    splash(R + 1.0, zl, w * 1.1);
}
// Nine falls round the big bowl and five round the small: sixteen and seven
// read as a birdcage. Icicles lying along the bowls' undersides between the
// falls were tried and need support: a ridge on a surface that already climbs
// SH leans past it (2026-10-14).
module all_falls() {
    falls(9, R_b1 + 0.2, z_b1 + 1.2, z_i, 2.8);
    falls(5, R_b2 + 0.2, z_b2 + 1.2, z_b1 + 0.4, 2.1);
}

// snow on the basin's ice and the big bowl's
module ice_snow() clip_to() {
    union() { drift([-9, 8, z_i], [5, 3, 0.9]); drift([10, -7, z_i], [4, 3.5, 0.8]); drift([4, 12, z_i], [3, 2, 0.7]); }
    dodec2d(A_i - 0.4);
}
module dodec2d(a) rotate(15) circle(r = a * C, $fn = 12);

// the wreath on the front flat (-y), on the bricks
WZ = 6.2;
module front(a) translate([0, -a, 0]) rotate([90, 0, 0]) children();
module wreath2d() translate([0, WZ]) difference() { circle(2.3, $fn = 40); circle(0.8, $fn = 32); }
module bow2d() translate([0, WZ + 2.1]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.5, 0.4]) circle(0.8, $fn = 20); }
    circle(0.8, $fn = 20);
}

module base2d() circle(r = 28, $fn = 96);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([-17, -19, zb], [5, 3, 1.1]); drift([20, 15, zb], [4, 5, 1.0]); } base2d_in(); }
    }
    brand_mark(MARK[0], MARK[1]);
}

module raw(p) {
    // the wreath starts at the course lines' depth, so it does not bridge them
    if (p == "body") { basin(); column(); front(A_o - 0.5) art_out(1.5, 1) bow2d(); }
    if (p == "roof") { ice(); bowl_ice(); }
    if (p == "trim") { base(); coping(); all_falls(); jet(); ice_snow(); }
    if (p == "accent") front(A_o - 0.5) art_out(1.5, 1) wreath2d();
}
emit();
