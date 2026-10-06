// Haunted Undertaker lantern -- building #5 of the Haunted Town series
// (../HAUNTED_TOWN.md). Picked by Scott on 2026-10-02 from four forms: tall
// and squeezed. A narrow three-storey house with a mansard top, squeezed
// between the bare gable ends of two neighbours that are no longer there. A
// hollow shell lit from inside by a battery LED tealight: open base, glazed
// through-cut windows.
//
// THE TOWN'S STYLE: a ridge that SAGS in the middle, a crooked chimney, steep
// roofs, walls / roof / trim / accent printed as separate AMS colours in one
// 3MF. Square plans.
// THE UNDERTAKER'S OWN FEATURES, from the town's variety plan (Scott,
// 2026-09-25): fish-scale shingled walls, coffin-shaped windows pointed at the
// top, a mansard roof, and a coffin standing against a porch post.
//
// COLOUR PARTS. Render one at a time with -D part="...":
//   body    the fish-scale front and back, the two bare gable walls and the
//           scars of the houses that stood against them, plinth, porch deck,
//           the dormer
//   roof    the mansard and its slate courses, the dormer's roof, the porch
//           roof, the crooked chimney
//   trim    window frames, bars and glass, the cornices, door and frame, the
//           porch arcade, the sign board, the cross on the coffin
//   accent  the coffin, the sign's carved letters
// Every part is built DISJOINT from the others; the part="chk_*" renders are
// the pairwise intersections and must come out empty.
//
// PRINTS WITH NO SUPPORTS: every downward face is 50 deg or steeper from
// horizontal. The mansard's lower slopes are 72 deg, its upper 55 deg with a
// LEVEL ridge inside; the cornices flare out at 58 deg; every raised relief
// (each fish scale too) has a sheared underside; the coffin windows' heads are
// 58 deg points and their sides narrow toward the head at 73 deg; the porch
// roof rests on its arcade at the front and rises to the wall at 55 deg or
// steeper. The gable walls' ragged tops are top surfaces only.
//
// TEALIGHT. Inside it is 50.0 x 48.6 mm, open at the base, clear from the
// plate to the wall top at 88 mm.

include <BOSL2/std.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ------------------------------------------------------------------------
W        = 56;              // along X, gable wall to gable wall
D        = 52;              // along Y, front (-Y) to back
pw       = 3.0;             // the gable walls' thickness
Wi       = W/2 - pw;        // half-width between them
pp       = 2;               // ...and how far they stand proud, front and back
wall     = 1.68;            // front and back walls, 4 x 0.42
H        = 88;              // front and back walls' top
plinth_h = 8;               // shared by every building in the town
plinth_o = 1.68;
SH       = 1.2;             // shear of every raised relief: 1.2 up per 1 out
t58      = tan(58);

// ---- mansard ------------------------------------------------------------------------
k_lo = tan(72);             // lower slopes
k_up = tan(55);             // upper slopes, at the gable walls
zb   = H + 1.5;             // where the lower slopes start, on the cornices
c_in = 7;                   // the lower slopes' run
zc   = zb + c_in * k_lo;    // the curb
yc   = D/2 - c_in;
sagM = 3;
function zr(x) = zc + yc * k_up - sagM * (1 - pow(x / Wi, 2));
tr   = 2.52;
k_mid = (zr(0) - zc) / yc;  // the upper slopes' pitch at mid-span
tv0  = tr / cos(atan(k_mid));
// The zone line: roof colour above, wall colour below, and the lantern's
// ceiling. It starts at the inside top corner of each wall, rises at 72 deg
// under the lower slope, then at 50+ deg to a LEVEL ridge.
y_wi = D/2 - wall;
z_ic = zc - 1.5;
y_ic = y_wi - (z_ic - H) / k_lo;
zi_r = zr(0) - tv0 - 0.3;
k_ui = (zi_r - z_ic) / y_ic;            // the ceiling's upper pitch
echo(str("UNDERTAKER zc=", zc, " ridge=", zr(0), " ceiling pitch=", atan(k_ui), " lower thickness=",
         ((D/2 - y_wi) + (zb - H) / k_lo) * sin(72)));
function stations(a, c, n) = [for (i = [0 : n]) a + (c - a) * i / n];
M_ST = stations(-Wi - 0.3, Wi + 0.3, 24);
module mansard_solid() skin([for (x = M_ST) [for (p = [
        [-D/2, H - 1], [D/2, H - 1], [D/2, zb], [yc, zc], [0, zr(x)], [-yc, zc], [-D/2, zb]]) [x, p[0], p[1]]]], slices = 0);
module zone2d() polygon([[-D/2 - 6, -10], [D/2 + 6, -10], [D/2 + 6, H], [y_wi, H], [y_ic, z_ic], [0, zi_r],
                         [-y_ic, z_ic], [-y_wi, H], [-D/2 - 6, H]]);
module zone_below(lift = 0) translate([0, 0, lift]) rotate([90, 0, 90]) linear_extrude(W + 20, center = true) zone2d();
module cavity() intersection() {
    translate([-Wi, -y_wi, -2]) cube([2 * Wi, 2 * y_wi, 400]);
    zone_below(0.3);
}

// The lower slopes' slate, as the town's walls do it: a REVERSED SAWTOOTH.
// Each course starts flush, ramps out 0.84 over 1 mm (62.7 deg from
// horizontal on a slope that leans back at 72) and steps back in at the next
// course on an upward-facing ledge.
sl_p = 4.2;  sl_d = 0.84;  sl_r = 1.0;
function y_lo(z) = D/2 - (z - zb) / k_lo;
function saw_pts() = let (n = floor((zc - 0.6 - zb) / sl_p)) concat(
    [[y_lo(zb) - 1.0, zb]],
    [for (k = [0 : n - 1], j = [0 : 2]) let (z0 = zb + k * sl_p,
         z = [z0 + 0.02, z0 + sl_r, z0 + sl_p][j], g = [0, sl_d, sl_d][j]) [y_lo(z) + g, z]],
    [[y_lo(zb + n * sl_p + 0.02), zb + n * sl_p + 0.02], [y_lo(zc - 0.6) - 1.0, zc - 0.6]]);
module courses() for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
    rotate([90, 0, 90]) linear_extrude(2 * Wi + 0.6, center = true) polygon(saw_pts());
module ridge_cap() skin([for (x = M_ST) let (z = zr(x)) [
        [x, 1.8, z - 1.8 * k_mid - 1.0], [x, 1.8, z - 1.8 * k_mid + 0.6], [x, 0, z + 1.6],
        [x, -1.8, z - 1.8 * k_mid + 0.6], [x, -1.8, z - 1.8 * k_mid - 1.0]]], slices = 0);

// ---- the gable walls: two bare ends, broken off at the top -------------------------
// Their ragged tops are only ever top surfaces: the outline climbs and falls
// but never doubles back over itself.
GABLE = [[-D/2 - pp, 0], [D/2 + pp, 0], [D/2 + pp, H + 30], [22, H + 38], [17, H + 36], [11, H + 50],
         [5, H + 55], [1, H + 61], [-3, H + 58], [-8, H + 62], [-12, H + 52], [-17, H + 50],
         [-22, H + 40], [-D/2 - pp, H + 31]];
module gable_walls() for (s = [-1, 1]) translate([s > 0 ? Wi : -W/2, 0, 0])
    rotate([90, 0, 90]) linear_extrude(pw) polygon(GABLE);

// Place children on a wall: local x along it as a viewer outside sees it,
// local y up, local z out.
//   face 0 = back (+Y), 1 = front (-Y), 2 = right gable (+X), 3 = left gable (-X)
module face_tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, D/2, z] : face == 1 ? [u, -D/2, z]
      : face == 2 ? [W/2, u, z] : [-W/2, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
module shear_up() multmatrix([[1, 0, 0, 0], [0, 1, SH, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up() translate([0, 0, a]) linear_extrude(b - a) translate([0, -SH * d0]) children();
}
module relief_up(d0, d1) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up() translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1) children(1);
    }
}

// The scars of the houses that stood here: the line of a lower roof, a floor
// and a chimney flue, raised on each gable's outer face.
module scars2d() {
    sc = 2.2;
    hull() { translate([-D/2 + 1, 58]) circle(d = sc, $fn = 12); translate([0, 84]) circle(d = sc, $fn = 12); }
    hull() { translate([D/2 - 1, 58]) circle(d = sc, $fn = 12); translate([0, 84]) circle(d = sc, $fn = 12); }
    translate([-D/2 + 1, 44]) square([D - 2, 2.2]);
    translate([-8, 46]) square([3.6, 36]);
}
module scars() for (f = [2, 3]) face_tf(f, 0, 0) relief_up(-0.4, 0.8) scars2d();

// ---- coffin windows ----------------------------------------------------------------------
// Narrow at the foot, widest at the shoulders, narrowing at 73 deg to the
// head and then a 58 deg point. A hole that widens as it rises needs nothing
// over it; only the head closes, and it closes steeply.
function coffin_pts(f, s, hs, h, hh) = [[-f, 0], [f, 0], [s, hs], [h, hh], [0, hh + h * t58], [-h, hh], [-s, hs]];
CW = coffin_pts(1.9, 3.2, 8, 2.0, 12);
module coffin2d(g = 0) offset(r = g) polygon(CW);
//   [face, u, sill z]
WINDOWS = [
    [1, -13, 22], [1, 13, 22], [1, -13, 64], [1, 13, 64],
    [0, -13, 22], [0, 13, 22], [0, -13, 64], [0, 13, 64],
];
fr_w = 1.7;
fr_t = 1.68;
fr_sill = 2.6;
module win_frame_outer() union() {
    offset(r = fr_w + 0.3) coffin2d();
    translate([-1.9 - fr_w - 0.3, -fr_w - 0.3 - fr_sill]) square([2 * (1.9 + fr_w + 0.3), fr_w + fr_sill + 1]);
}
// a cross in every window: it stands on the glass, its arms sheared like any relief
module win_cross() intersection() {
    // 1.6 wide: at 1.2 the bars measured under one bead
    union() { translate([-0.8, -1]) square([1.6, 20]); translate([-4, 7.2]) square([8, 1.6]); }
    coffin2d(0.6);
}

// ---- cornices, at the head of the front and back walls ------------------------------------
co_o = 2.4;                 // out from the wall
co_z = H - 4;               // the flare starts here
module cornices() for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
    translate([-Wi, 0, 0]) rotate([90, 0, 90]) linear_extrude(2 * Wi) polygon([
        [D/2 - 0.4, co_z], [D/2, co_z], [D/2 + co_o, co_z + co_o * t58], [D/2 + co_o, zb], [D/2 - 0.4, zb]]);

// ---- door, porch ----------------------------------------------------------------------------
door_a = 6;
door_h = 14;
function arch_head(a, hgt) = [[-a, 0], [a, 0], [a, hgt], [0, hgt + a * t58], [-a, hgt]];
module door_frame() face_tf(1, 0, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
    difference() {
        intersection() { offset(r = fr_w) polygon(arch_head(door_a, door_h)); translate([-20, 0]) square([40, 100]); }
        translate([0, -1]) polygon(arch_head(door_a, door_h + 1));
    }
module door_leaf() face_tf(1, 0, plinth_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
    difference() {
        polygon(arch_head(door_a, door_h));
        translate([0, 9]) polygon(coffin_pts(0.8, 1.4, 4, 0.9, 6));   // a coffin-shaped light
    }
P     = 7;
xp    = 20;
y_f   = -D/2 - P;
y_w   = -D/2;
ar_t  = 3.0;
z_uw  = 44;                 // the porch roof's underside at the wall; its top there is 49, under the sign
k_p   = tan(55);
zp_end = z_uw - P * k_p;
sag_p = 2;
function zp(x) = zp_end - sag_p * (1 - pow(x / xp, 2));
function kp(x) = (z_uw - zp(x)) / P;
function tvp(x) = tr / cos(atan(kp(x)));
function pu(x, y) = zp(x) + (y - y_f) * kp(x);
function pt(x, y) = pu(x, y) + tvp(x);
PORCH_ST = stations(-xp, xp, 24);
module porch_roof_slab() skin([for (x = PORCH_ST) [for (p = [
        [y_f, pu(x, y_f)], [y_w + 0.6, pu(x, y_w + 0.6)], [y_w + 0.6, pt(x, y_w + 0.6)], [y_f, pt(x, y_f)]])
        [x, p[0], p[1]]]], slices = 0);
module under_porch_mid() skin([for (x = PORCH_ST) [for (p = [
        [y_f, -5], [y_w + 0.6, -5], [y_w + 0.6, pu(x, y_w + 0.6) + 2], [y_f, pu(x, y_f) + 2]])
        [x, p[0], p[1]]]], slices = 0);
sh_t = 1.0;
PSH_U = [0, 3.4, P - 0.7];
module porch_courses() intersection() {
    union() for (k = [0 : len(PSH_U) - 2])
        let (u0 = PSH_U[k], u1 = min(PSH_U[k + 1] + 0.5, P - 0.7))
        skin([for (x = PORCH_ST) let (y0 = y_f + u0, y1 = y_f + u1)
              [[x, y1, pt(x, y1) - 1.0], [x, y1, pt(x, y1) + 0.05], [x, y0, pt(x, y0) + sh_t], [x, y0, pt(x, y0) - 1.0]]], slices = 0);
    translate([-xp, y_f - 1, 0]) cube([2 * xp, P + 1, 200]);
}
// one pointed arch over the step, a slit either side; [centre, half-width]
ARCHES = [[-14.5, 2.5], [0, 8], [14.5, 2.5]];
function arch_pts(c, a) = let (ap = zp(c) - 2.2) arch_head(a, ap - a * t58 - plinth_h);
// The roof is taken out of the arcade itself, and the arcade is cut to a
// surface inside the roof on the roof's own stations (the schoolhouse's
// lesson: cut to a separate skin, the two disagreed and left open edges).
module arcade() difference() {
    intersection() {
        difference() {
            translate([-xp, y_f, plinth_h - 0.01]) cube([2 * xp, ar_t, 60]);
            for (q = ARCHES) translate([q[0], y_f + ar_t + 1, plinth_h - 1]) rotate([90, 0, 0])
                linear_extrude(ar_t + 2) translate([0, 1]) polygon(arch_pts(q[0], q[1]));
        }
        under_porch_mid();
    }
    porch_roof_slab();
}
st_w = 18;  st_d = 6;  st_h = 4;
dk_f = 9;                   // the deck runs this far in front of the arcade, for the coffin
module deck() {
    translate([-xp - 1.2, y_f - dk_f, 0]) cube([2 * xp + 2.4, dk_f + P + wall, plinth_h]);
    translate([-st_w/2, y_f - dk_f - st_d, 0]) cube([st_w, st_d + 0.01, st_h]);
}

// ---- the coffin, standing against the right-hand post ---------------------------------------
cf_x = 17.6;                // centred in front of the post
cf_d = 3.8;                 // its depth
CF = [[-2.4, 0], [2.4, 0], [3.6, 15], [2.6, 22], [-2.6, 22], [-3.6, 15]];
module coffin() translate([cf_x, y_f + 0.3, plinth_h - 0.3]) rotate([90, 0, 0]) linear_extrude(cf_d + 0.3) polygon(CF);
// the cross on its lid
module coffin_cross() translate([cf_x, y_f - cf_d, plinth_h]) rotate([90, 0, 0])
    relief_up(-0.4, 0.8) union() { translate([-0.6, 5]) square([1.2, 13]); translate([-2.2, 13.4]) square([4.4, 1.2]); }

// ---- sign ------------------------------------------------------------------------------------
sg_z = 54;  sg_w = 46;  sg_h = 8;      // the lettering is 42.2 wide
sg_tilt = 2;                // hung crooked, left end low
module sign_board() face_tf(1, 0, sg_z) rotate([0, 0, sg_tilt])
    relief_up(-0.4, fr_t) translate([-sg_w/2, -sg_h/2]) square([sg_w, sg_h]);
// carved 0.6 into the board and lined with the accent (the bakery's method)
lt_open = 0.6;  lt_depth = 1.1;  lt_step = 0.2;  lt_k = tan(58);  lt_n = 8;
module sign_text() text("UNDERTAKER", size = 4.0, font = "Montserrat:style=Black",
                        halign = "center", valign = "center", spacing = 1.06);
module sign_at() face_tf(1, 0, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t]) children();
module sign_climb(h) intersection_for(j = [0 : ceil(h / lt_step)]) translate([0, -j * lt_step]) sign_text();
module sign_carve_local() for (i = [0 : lt_n - 1]) let (t0 = i * lt_open / lt_n, t1 = t0 + lt_open / lt_n)
    translate([0, 0, -t1]) linear_extrude(t1 - (i == 0 ? -0.01 : t0)) sign_climb(lt_k * t1);
module sign_carve() sign_at() sign_carve_local();
module sign_letters() difference() {
    sign_at() translate([0, 0, -lt_depth]) linear_extrude(lt_depth) sign_text();
    sign_carve();
}

// ---- the dormer: the front wall carried up through the mansard -----------------------------
dm_w  = 18;
dm_ez = H + 22.5;           // its eaves
dm_ap = dm_ez + dm_w/2 * t58;
dm_y1 = -6;
dm_sill = H + 4;
module dormer_block() rotate([90, 0, 0]) translate([0, 0, -dm_y1]) linear_extrude(D/2 + dm_y1)
    polygon([[-dm_w/2, H - 2], [dm_w/2, H - 2], [dm_w/2, dm_ez], [0, dm_ap], [-dm_w/2, dm_ez]]);
dm_cv = 1.6 / cos(58);
module dormer_cap() difference() { dormer_block(); translate([0, 0, -dm_cv]) dormer_block(); }
// Behind its glass, a channel back into the room: the glass sits above the
// ceiling here, which rises at 72 deg from the wall's top. Its head is the
// window's own 58 deg point; where it meets the 72 deg ceiling the corner is
// 54.8 deg on the diagonal.
module dm_channel() translate([0, -D/2 + wall - 0.3, dm_sill]) rotate([-90, 0, 0])
    linear_extrude(D/2 - wall + 0.3 - 17.5) mirror([0, 1, 0]) coffin2d(0);

// ---- chimney: crooked, on the back of the mansard ---------------------------------------------
ch = [-13, 9];
ch_w = 6;
ch_z = H + 52;
module ch_slice(c, z, g = 0) translate([c[0], c[1], z]) linear_extrude(0.01) square(ch_w + 2 * g, center = true);
module chimney() {
    c1 = ch + [-2.8, 0];
    translate([ch[0] - ch_w/2, ch[1] - ch_w/2, H + 20]) cube([ch_w, ch_w, ch_z - H - 20]);
    hull() { ch_slice(ch, ch_z - 0.01); ch_slice(c1, ch_z + 7); }
    translate([c1[0] - ch_w/2, c1[1] - ch_w/2, ch_z + 6.99]) cube([ch_w, ch_w, 4.02]);
    hull() { ch_slice(c1, ch_z + 10.99); ch_slice(c1, ch_z + 13, 1.2); }
    translate([c1[0], c1[1], ch_z + 14.2]) cube([ch_w + 2.4, ch_w + 2.4, 2.4], center = true);
    translate([c1[0], c1[1], ch_z + 15.3]) {
        cylinder(r = 2.2, h = 3.4, $fn = 40);
        translate([0, 0, 3.4]) cylinder(r1 = 2.2, r2 = 2.9, h = 0.9, $fn = 40);
        translate([0, 0, 4.3]) cylinder(r = 2.9, h = 0.7, $fn = 40);
    }
}

// ---- fish scales, on the front and back walls ---------------------------------------------
// Laid like the town's clapboard, a REVERSED SAWTOOTH, with every course's
// lower edge scalloped into a row of round butts (each row's half a scale
// over from the one below). A course starts flush with the wall on its
// scalloped line, ramps out 0.84 at 58 deg or steeper, runs flat, and steps
// back in on an upward-facing ledge at the next course's line, so the scales
// read as the ledges' scallops. Nothing faces down.
// First built as one raised relief per scale (the town's sheared relief): each
// scale's top was cut into arcs by the row above, the relief's flat top is
// clipped over 0.2 either side, and along every row the arcs left slivers 0.01
// to 0.3 mm thick -- 1.5% of the building under one bead.
fs_r  = 2.1;                // scale radius
fs_p  = 3.8;                // course height: 1.7 clear at the scallops' deepest overlap
fs_d  = 0.84;               // course depth
fs_rr = fs_d * t58;         // its ramp
fs_z0 = plinth_h + 0.6;
fs_top = co_z - 0.6;
// On the front they start just over the porch roof (its top meets the wall at
// 48.4 to 50 mm): run on under it, the roof's steep underside cut the courses
// into eight loose scales and sealed air pockets between them and the wall.
// Below that the front is nearly all porch, and stays plain.
fs_z0f = 50.6;
function fs_z0_(face) = face == 1 ? fs_z0f : fs_z0;
function fs_n_(face) = floor((fs_top - fs_z0_(face) - fs_r - fs_rr - 0.5) / fs_p);
fs_x  = Wi + 0.3;            // 0.3 into each gable wall, one body with it
function fs_scallop(dx) = let (m = dx - 2 * fs_r * floor((dx + fs_r) / (2 * fs_r))) fs_r - sqrt(max(0, fs_r * fs_r - m * m));
function fs_L(k, x, z0 = fs_z0) = z0 + k * fs_p + fs_scallop(x - (k % 2) * fs_r);
FS_ST = stations(-fs_x, fs_x, 260);
function fs_prof(x, z0, n) = concat(
    [[-0.4, fs_L(0, x, z0)]],
    [for (k = [0 : n - 1], j = [0 : 2]) [[0, fs_L(k, x, z0) + 0.02], [fs_d, fs_L(k, x, z0) + 0.02 + fs_rr], [fs_d, fs_L(k + 1, x, z0)]][j]],
    [[0, fs_L(n, x, z0) + 0.02], [fs_d, fs_L(n, x, z0) + 0.02 + fs_rr], [fs_d, fs_top], [-0.4, fs_top]]);
module fs_skin(face) skin([for (x = FS_ST) [for (p = fs_prof(x, fs_z0_(face), fs_n_(face)))
        face == 1 ? [x, -D/2 - p[0], p[1]] : [-x, D/2 + p[0], p[1]]]], slices = 0);
// The courses run on under the frames, the door, the sign and the porch roof,
// which the body loses to those parts anyway, so each joins them. Cut clear of
// them with a 0.8 gap, every course left a sliver along every cut edge.
module scales() for (f = [0, 1]) fs_skin(f);

// ---- trim and openings --------------------------------------------------------------------
module openings() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) coffin2d();
    face_tf(1, 0, dm_sill) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) coffin2d();
    face_tf(1, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(arch_head(door_a, door_h));
    dm_channel();
}
module frame_holes() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) coffin2d();
    face_tf(1, 0, dm_sill) relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) coffin2d();
}
module window_trim() {
    relief_up(-0.4, fr_t) { win_frame_outer(); offset(r = 0.3) coffin2d(); }
    relief_up(-0.4, fr_t - 0.5) win_cross();
    translate([0, 0, -wall]) linear_extrude(wall - 0.2) coffin2d(0.6);
}
module trim_raw() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) window_trim();
    face_tf(1, 0, dm_sill) window_trim();
    door_frame();
    door_leaf();
    arcade();
    cornices();
    sign_board();
    coffin_cross();
}
module accent_raw() {
    coffin();
    sign_letters();
}

// ---- mark ------------------------------------------------------------------------------
// Under the porch deck, read from below with the front toward you: flipped
// left-to-right (2026-09-27), spacing 1.16 at size 4.6.
module brand_mark() translate([-7, y_f - dk_f / 2, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black",
                           halign = "center", valign = "center", spacing = 1.16);

// ---- parts ------------------------------------------------------------------------------
module body_part() difference() {
    union() {
        intersection() {
            union() {
                translate([-Wi, -D/2, 0]) cube([2 * Wi, D, H]);
                for (s = [-1, 1]) translate([-Wi, s > 0 ? D/2 - 0.01 : -D/2 - plinth_o, 0]) cube([2 * Wi, plinth_o + 0.01, plinth_h]);
                mansard_solid();
            }
            zone_below();
        }
        gable_walls();
        scars();
        scales();
        deck();
        dormer_block();
    }
    cavity(); openings(); frame_holes(); trim_raw(); accent_raw(); brand_mark();
    porch_roof_slab(); porch_courses(); dormer_cap(); chimney(); sign_carve();
}
module roof_part() difference() {
    union() {
        difference() {
            union() { mansard_solid(); courses(); ridge_cap(); }
            zone_below();
            // exactly what the body keeps of the dormer (the schoolhouse's
            // lesson): taken out only above zone+0.3, the roof kept a 0.3 band
            // inside the dormer's own front wall and the two parts overlapped
            difference() { dormer_block(); cavity(); }
            // and the light channel: the 0.3 band of roof under the dormer
            // otherwise stood inside it as a loose sheet
            dm_channel();
        }
        difference() { chimney(); cavity(); zone_below(); }
        porch_roof_slab();
        porch_courses();
        difference() { dormer_cap(); zone_below(0.3); }
    }
    gable_walls(); trim_raw(); accent_raw();
}
module trim_part()   difference() { trim_raw(); accent_raw(); sign_carve(); }
module accent_part() accent_raw();

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
    color("#3F4A63") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#6B4429") accent_part();
}
