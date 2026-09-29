// Gingerbread Cottage -- building #1 of the Gingerbread Christmas village
// (openscad_models/christmas_village/CHRISTMAS_VILLAGE.md). The cottage from
// the style study, rebuilt to print: smooth gingerbread walls with piped
// icing beads down every corner and round every window and the door, a steep
// roof of chocolate scallop tiles, icing on the ridge and dripping off the
// eaves and rakes, gumdrops along the ridge, a chocolate-bar door between two
// candy canes, a peppermint round window in each gable, peppermint candies on
// the snow.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed with a 1.48 mm pane that its bars stand on.
//
// Same frame as the Victorian cottage (victorian/cottage/victorian_cottage.scad)
// and so the chapel's machinery; its WHY comments are in those two files. What
// is new is commented here.
//
// COLOUR PARTS, ONE PRINT (gingerbread_cottage.3mf):
//   body    gingerbread walls, the kneelers
//   roof    chocolate slab and scallop tiles, the chocolate-bar door
//   trim    icing: snow base, corner beads, window and door frames and their
//           beads, panes and bars, eave soffit and drips, rake bands and
//           drips, icing on the roof, the candy canes' white, the
//           peppermints' white
//   accent  candy red: gumdrops, cane stripes, peppermint stripes
// Every part is built DISJOINT from the others (part="chk_*").
//
// TEALIGHT. 60.6 x 54.6 mm clear inside from the table to the 52 mm eave.

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";

// ---- walls ---------------------------------------------------------------------
W        = 64;
D        = 58;
wall     = 1.68;
corner_r = 2.5;             // softer than brick: a baked edge
plinth_h = 8;
Wh = W/2;  Dh = D/2;
SH       = 1.2;
bd       = 0;               // the walls are smooth: no brick face

// ---- roof --------------------------------------------------------------------------
H     = 52;
r_ang = 58;
tp    = tan(r_ang);
x_in  = Wh - wall;
tr    = 2.52;
tv    = tr / cos(r_ang);
e     = 2;
xe    = Wh + bd + e;
function z_ceil(x) = H + (x_in - abs(x)) * tp;
function z_out(x)  = z_ceil(x) + tv;
y_r   = Dh - wall;
cp_lo = -0.2;  cp_hi = 2.2;

// ---- placement ---------------------------------------------------------------------
module nf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, Dh, z] : face == 1 ? [u, -Dh, z]
      : face == 2 ? [Wh, u, z] : [-Wh, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
function loc(f, u) = (f == 0 || f == 3) ? -u : u;

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

// ---- nave regions -------------------------------------------------------------------------
module below_ceil() xz(-60, 60) polygon([[-40, -5], [40, -5], [40, z_ceil(40)], [0, z_ceil(0)], [-40, z_ceil(-40)]]);
module gable_keep() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0])
        xz(Dh - wall, Dh + 5) polygon([[-xe, -5], [xe, -5], [xe, z_out(xe) + 1], [0, z_out(0) + 1], [-xe, z_out(xe) + 1]]);
}
fl_ang = 52;
xf  = xe - 0.08;
zf0 = z_ceil(xf) - (xf - Wh) * tan(fl_ang);
fl_xe = z_ceil(xf) + (xe - xf) * tan(fl_ang);
module kneelers() {
    for (s = [-1, 1], m = [0, 1]) mirror([0, s < 0 ? 1 : 0, 0]) mirror([m, 0, 0])
        // started inside the corner's 2.5 mm rounding, so each is one piece
        // with its gable: from Wh - 0.3 they stood clear of it, loose
        xz(Dh - wall, Dh - 0.05) polygon([[Wh - corner_r - 0.3, z_ceil(Wh - corner_r - 0.3)], [xf, z_ceil(xf)], [xe, fl_xe],
                                        [xe, z_out(xe) + 1], [Wh - corner_r - 0.3, z_out(Wh - corner_r - 0.3) + 1]]);
}
// White: the iced soffit the drips hang from. Run 0.2 past the kneelers and
// topped 0.3 into slab and kneelers (see the Victorian cottage: drawn on the
// same planes, the parts left slivers along every eave).
module eave_flare() {
    for (m = [0, 1]) mirror([m, 0, 0]) xz(-Dh - 0.15, Dh + 0.15)
        polygon([[Wh - 1, zf0 - tan(fl_ang)], [xf, z_ceil(xf)], [xf, z_ceil(xf) + 0.3], [Wh - 1, z_ceil(Wh - 1) + 0.3]]);
}
module walls_solid() {
    intersection() {
        translate([0, 0, plinth_h - 0.5]) linear_extrude(200) rect([W, D], rounding = corner_r);
        union() { below_ceil(); gable_keep(); }
    }
    kneelers();
}
module room() {
    intersection() {
        translate([-x_in, -y_r, -2]) cube([2 * x_in, 2 * y_r, 200]);
        below_ceil();
    }
}

// ---- piped icing ----------------------------------------------------------------------------
// BEADS ALONG A PATH. Piped icing is a string of beads; drawn as overlapping
// circles on an outline and raised like every relief, so each bead's
// underside is sheared.
bead_r  = 1.2;
bead_sp = 2.0;
// the points of an arched outline offset by o, a bead every ~sp:
// along the bottom (if `bottom`), up the right side, over the arch, down the left
function arch_path(a, hgt, o, sp, bottom = true) =
    let (A = a + o, b0 = bottom ? 2 * A : 0, b1 = b0 + hgt + o, b2 = b1 + PI * A, P = b2 + hgt + o,
         n = round(P / sp))
    [for (i = [0 : n - 1]) let (t = i * P / n)
        t < b0 ? [-A + t, -o] :
        t < b1 ? [A, -o + (t - b0)] :
        t < b2 ? let (q = (t - b1) / A * 180 / PI) [A * cos(q), hgt + A * sin(q)] :
                 [-A, hgt - (t - b2)]];
function ring_path(r, sp) = let (n = round(2 * PI * r / sp)) [for (i = [0 : n - 1]) let (q = 360 * i / n) [r * cos(q), r * sin(q)]];
module beads(pts, r = bead_r) for (p = pts) translate(p) circle(r = r);

// CORNER BEADS. A column of piped beads down each corner, built as one
// solid of revolution: stacked spheres 1.7 apart at radius 1.3. The neck
// between two beads faces down at asin(0.85/1.3) = 41 deg from vertical, under
// the 45 limit, so the column prints without anything under it but itself.
cb_r = 1.3;  cb_sp = 1.7;
function bead_rad(z, n) = max([for (i = [0 : n]) let (d = z - i * cb_sp) abs(d) < cb_r ? sqrt(cb_r * cb_r - d * d) : 0]);
function bead_profile(n, k = 12) = let (z0 = -cb_r, z1 = n * cb_sp + cb_r, m = ceil((z1 - z0) / cb_sp * k))
    concat([[0, z0]], [for (j = [1 : m - 1]) let (z = z0 + (z1 - z0) * j / m) [bead_rad(z, n), z]], [[0, z1]]);
module corner_beads() {
    n = floor((zf0 - 1 - plinth_h) / cb_sp);
    for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * (Wh - corner_r + (corner_r + 0.35) / sqrt(2)), sy * (Dh - corner_r + (corner_r + 0.35) / sqrt(2)), plinth_h + 0.6])
            // the profile drawn as one outline touching the axis only at its two
            // ends: a union of circles cut at the axis gave rotate_extrude a
            // surface that was not closed, and CGAL dropped the whole column
            rotate_extrude($fn = 32) polygon(bead_profile(n));
}

// ---- openings ------------------------------------------------------------------------------
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9;                 // frame face out from the wall: shallow, so the
                            // shear leaves the heads a real front edge
//   [face, u, z, a, straight height, kind]   kind: "arch" or "round" (h unused)
WINDOWS = [
    [1, -21, 17, 5.0, 12, "arch"],  [1, 21, 17, 5.0, 12, "arch"],  [1, 0, 56, 5.4, 0, "round"],
    [0,   0, 17, 5.0, 12, "arch"],  [0, 0, 56, 5.4, 0, "round"],
    [2, -12, 17, 5.0, 12, "arch"],  [2, 12, 17, 5.0, 12, "arch"],
    [3, -12, 17, 5.0, 12, "arch"],  [3, 12, 17, 5.0, 12, "arch"],
];
function is_round(w) = w[5] == "round";
function w_top(w) = is_round(w) ? 2 * w[3] : w[4] + w[3];
module win_outline(w) { if (is_round(w)) translate([0, w[3]]) circle(r = w[3]); else polygon(arch_pts(w[3], w[4])); }
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, is_round(w) ? w[3] - 1.1 : w[4] * 0.6]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
// Arched windows: an icing band with beads piped along its outer edge,
// across the sill too. Round windows: a peppermint -- a ring of eight
// wedges, alternately icing and candy red.
module frame2d(w) {
    if (is_round(w)) translate([0, w[3]]) circle(r = w[3] + 3.2, $fn = 64);
    else {
        offset(r = fr_w) win_outline(w);
        beads(arch_path(w[3], w[4], fr_w - 0.1, bead_sp));
    }
}
module frame_relief(w) relief_up(-0.4, fr_t) { frame2d(w); offset(r = 0.3) win_outline(w); }
// joined by a small disc at the centre: four wedges meeting at a single
// point extrude to a surface that is not closed, and CGAL drops the object
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }
module frame_holes() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) win_outline(w);
    nf(1, 0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
}
door_a = 6.5;
door_h = 18;
module openings() {
    for (w = WINDOWS) nf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + 4) win_outline(w);
    nf(1, 0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(arch_pts(door_a, door_h));
}

// ---- door ------------------------------------------------------------------------------------
// A chocolate bar: the leaf scored into squares by V grooves. The horizontal
// grooves' upper faces lean 50 deg, never a flat ceiling.
module door_leaf() {
    // The Victorian cottage's leaf: filling the arch and 0.2 past it (a round
    // arch's crown is flat), sunk 0.3 into the snow, 0.2 proud of the wall
    // and stopped 0.15 short of the room.
    nf(1, 0, plinth_h) difference() {
        translate([0, 0, -wall + 0.15]) linear_extrude(wall + 0.05)
            translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
        // run out through the crown: stopped under it, the groove's end was a
        // flat ceiling 0.5 deep that drew support from the snow up
        translate([-0.5, -1, -0.3]) cube([1, door_h + door_a + 4, 1]);
        for (zg = [5.2, 10.4, 15.6]) hull() {
            translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
            translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
        }
    }
}
module door_frame() {
    nf(1, 0, plinth_h) relief_up(-0.4, fr_t) {
        union() {
            intersection() { offset(r = fr_w) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
            intersection() { beads(arch_path(door_a, door_h, fr_w - 0.1, bead_sp, false)); translate([-30, 0.6]) square([60, 100]); }
        }
        translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
    }
}

// ---- candy canes ------------------------------------------------------------------------------
// One either side of the door, standing on the snow, the crooks turned in
// toward the door. White (icing) with red stripes (accent): the same relief
// twice, the stripes being the cane cut to diagonal bands.
cane_x = 12.3;  cane_w = 2.6;  cane_h = 20;  cane_R = 3;
module cane2d(dir) {
    translate([-cane_w/2, -0.5]) square([cane_w, cane_h + 0.5]);
    translate([dir * cane_R, cane_h]) intersection() {
        difference() { circle(r = cane_R + cane_w/2); circle(r = cane_R - cane_w/2); }
        translate([-10, 0]) square([20, 10]);
    }
    translate([2 * dir * cane_R - cane_w/2, cane_h - 1.8]) square([cane_w, 1.8]);
}
module stripes2d() for (i = [-12 : 12]) translate([0, i * 3.4]) rotate(35) translate([-20, 0]) square([40, 1.5]);
// The stripes are the white cane's own solid cut by a prism of bands, not a
// relief of their own: a sheared relief of the bands' shapes is not the same
// solid as the cane cut into bands, and the two left slivers between them.
module cane_relief(s) nf(1, s * cane_x, plinth_h) relief_up(-0.4, fr_t + 0.5) cane2d(-s);
module canes(stripes = false) for (s = [-1, 1])
    if (stripes) intersection() { cane_relief(s); nf(1, s * cane_x, plinth_h) translate([0, 0, -5]) linear_extrude(10) stripes2d(); }
    else cane_relief(s);

// ---- eave drips and rake bands ------------------------------------------------------------------
// Icing running off the eaves: fat drips with round ends, hung from the
// soffit's foot on both side walls.
DR = [for (i = [0 : 14]) let (r = rands(0, 1, 2, 70 + i)) [-Dh + 3 + i * (D - 6) / 14, 1.6 + 3.6 * r[0], 2.2 + 0.5 * r[1]]];
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
module eave_drips() for (f = [2, 3], c = DR) nf(f, c[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(c[1], c[2]);
// The rakes: the chapel's coping, capped in icing, with a band down the
// gable face and drips hanging from it. The band's proud part is sheared at
// 58 deg like the coping's, so the drips' round ends rise as they come out.
rb_h = 3.2;                 // band depth below the roof's top line
rb_t = 1.2;
module gable_poly(lo, hi) polygon([[-xe, z_out(xe) + lo], [0, z_out(0) + lo], [xe, z_out(xe) + lo],
                                   [xe, z_out(xe) + hi], [0, z_out(0) + hi], [-xe, z_out(xe) + hi]]);
RD = [for (i = [0 : 13]) let (r = rands(0, 1, 2, 110 + i), x = 1.6 + i * 2.1) if (x < Wh - 2.4) [x, 1.2 + 3.2 * r[0], 2.0 + 0.4 * r[1]]];
module rake2d(ext) {
    X = Wh - 1;
    polygon([[-X, z_out(X) + cp_hi + ext], [0, z_out(0) + cp_hi + ext], [X, z_out(X) + cp_hi + ext],
             [X, z_out(X) - rb_h], [0, z_out(0) - rb_h], [-X, z_out(X) - rb_h]]);
    for (d = RD, s = [-1, 1]) let (x = s * d[0]) translate([x, z_out(x) - rb_h + 0.6]) drip2d(d[1] + 0.6, d[2]);
}
module rakes() {
    for (s = [-1, 1]) mirror([0, s < 0 ? 1 : 0, 0]) {
        xz(Dh - wall - 0.3, Dh - 0.05) gable_poly(cp_lo, cp_hi);
        // unsheared term run down to the table, as on the Victorian's
        // bargeboard: intersected with a plain copy, a sheared drip rose into
        // the band above it and left the band's flat underside between drips
        intersection() {
            xz(Dh - 0.1, Dh + rb_t) minkowski() { rake2d(0); translate([-0.01, -60]) square([0.02, 60]); }
            multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, tan(58), 1, -tan(58) * Dh], [0, 0, 0, 1]])
                xz(Dh - 1, Dh + 4) rake2d(10);
        }
    }
}

// ---- roof -----------------------------------------------------------------------------------------------
y_rr = y_r + 0.4;           // slab runs under the copings (see the Victorian)
module slab() xz(-y_rr, y_rr) polygon([[-xe, fl_xe], [-xf, z_ceil(xf)], [0, z_ceil(0)], [xf, z_ceil(xf)], [xe, fl_xe],
                                     [xe, z_out(xe)], [0, z_out(0)], [-xe, z_out(xe)]]);
// CHOCOLATE SCALLOP TILES. The chapel's slate courses, each course's butt
// cut into a row of rounded tiles. The butt is cut straight DOWN (the plan
// shape is extruded vertically), so a tile's rounded edge is a vertical face
// like a slate's, and hangs nothing. Rows stagger by half a tile. The lowest
// row is kept inside the eave edge.
tc = 2.6;                   // course, measured horizontally
sd = 1.3;                   // scallop bulge, horizontally
tw = 4.8;                   // tile width along the ridge
module tiles() {
    nk = ceil((xe - 0.6) / tc);
    for (m = [0, 1]) mirror([m, 0, 0]) for (k = [0 : nk - 1])
        let (x0 = xe - k * tc - sd, x0e = min(x0 + sd, xe), x1 = max(xe - (k + 1) * tc - sd - 0.5, 0.6))
        if (x0e > x1 + 0.3) intersection() {
            xz(-y_rr, y_rr) polygon([[x0e, z_out(x0e) - 1.0], [x0e, z_out(x0e) + 1.0], [x1, z_out(x1) + 0.05], [x1, z_out(x1) - 1.0]]);
            translate([0, 0, 30]) linear_extrude(100) intersection() {
                union() {
                    translate([-10, -y_rr - 1]) square([x0 + 10, 2 * y_rr + 2]);
                    for (j = [-8 : 8]) translate([x0, j * tw + (k % 2) * tw / 2]) scale([sd, tw / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                translate([-10, -y_rr - 1]) square([xe + 10, 2 * y_rr + 2]);
            }
        }
    xz(-y_rr, y_rr) polygon([[1.2, z_out(1.2) - 1.0], [1.2, z_out(1.2) + 1.0], [0, z_out(0) + 1.4], [-1.2, z_out(1.2) + 1.0], [-1.2, z_out(1.2) - 1.0]]);
}
// ICING on the upper roof, its lower edge cut straight down in a run of
// drips, the gumdrops along its crest.
ic_x = 9;
function ic_edge(y) = ic_x + 1.8 * sin(y * 23) + 1.2 * sin(y * 53 + 40);
module icing_roof() {
    intersection() {
        xz(-y_rr - 0.4, y_rr + 0.4) polygon([[-xe, z_out(xe) - 1.0], [0, z_out(0) - 1.0], [xe, z_out(xe) - 1.0],
                               [xe, z_out(xe) + 2.0], [3, z_out(3) + 2.0], [0, z_out(0) + 2.4], [-3, z_out(3) + 2.0], [-xe, z_out(xe) + 2.0]]);
        translate([0, 0, 40]) linear_extrude(100)
            polygon(concat([for (i = [0 : 60]) let (y = -Dh + 2 * Dh * i / 60) [ic_edge(y), y]],
                           [for (i = [60 : -1 : 0]) let (y = -Dh + 2 * Dh * i / 60) [-ic_edge(-y), y]]));
    }
}
// GUMDROPS: a dome on a steep cone (77 deg) carried down into the roof, so
// every visible face looks up.
GD = [-20, -10, 0, 10, 20];
// Cut off at the ceiling: the cones' feet reached 3 mm down into the room
// and hung there, and drew support from the table up the middle of the house.
module gumdrops() difference() {
    for (y = GD) hull() {
        translate([0, y, z_out(0) + 4.0]) sphere(r = 2.3, $fn = 32);
        // r 4.6, not 5: at 5 the neighbours' cones met tangent under the ridge
        translate([0, y, z_out(0) - 8]) cylinder(r = 4.6, h = 0.01, $fn = 32);
    }
    below_ceil();
}

// ---- snow base ------------------------------------------------------------------------------------------
module base2d() {
    offset(r = 2.5) offset(delta = -2.5) union() {
        translate([-Wh - 4.5, -Dh - 12]) square([W + 9, D + 16.5]);
        for (p = [[-Wh - 3, -Dh - 8, 4.5], [Wh + 3.5, -Dh - 2, 4], [Wh + 3, Dh - 6, 4.5], [-Wh - 3, Dh - 2, 3.5],
                  [-14, Dh + 3.5, 4], [18, Dh + 3.5, 3.5], [-Wh - 3.5, 4, 3.5], [Wh + 3.5, 12, 3.5]])
            translate([p[0], p[1]]) circle(r = p[2]);
    }
}
DRIFTS = [[Wh + 1, Dh - 10, 8, 4, 3.6], [-8, Dh + 1, 7, 3.5, 2.8], [-Wh - 1, Dh - 4, 5, 3.5, 2.4]];
// PEPPERMINTS lying on the snow either side of the path.
PM = [[-24, -Dh - 7.2, 3.4], [26, -Dh - 5.4, 2.8]];
module peppermints(stripes = false) for (p = PM) translate([p[0], p[1], plinth_h - 0.2]) linear_extrude(1.4)
    // with a red dot at the centre: the four wedges alone met at one point,
    // and that bow-tie outline extruded to a surface that was not closed
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

// ---- mark -----------------------------------------------------------------------------------------------
module brand_mark() {
    translate([0, -Dh - 6.2, -0.5]) linear_extrude(1.3)
        mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black",
                               halign = "center", valign = "center", spacing = 1.16);
}

// ---- parts ----------------------------------------------------------------------------------------------
module body_raw() walls_solid();
module roof_raw() {
    difference() { union() { slab(); tiles(); } room(); }
    door_leaf();
}
module accent_raw() {
    gumdrops();
    canes(true);
    peppermints(true);
    // the ring's own solid cut by a prism of wedges (see the canes)
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
            eave_flare();
            eave_drips();
            rakes();
            icing_roof();
            canes();
            peppermints();
            for (w = WINDOWS) nf(w[0], w[1], w[2]) {
                frame_relief(w);
                relief_up(-0.4, 0.4) win_muntins(w, 0.6);
                translate([0, 0, -wall]) linear_extrude(wall - 0.2) offset(r = 0.6) win_outline(w);
            }
            door_frame();
        }
        room();
        brand_mark();
    }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); openings(); frame_holes(); trim_raw(); accent_raw(); roof_raw();
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
