// Haunted Cemetery -- scenery for the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). A graveyard HILL: a lumpy mound with
// seven headstones of different styles leaning every which way, a twisted dead
// tree on the crest with a crow on a sawn-off branch, three jack-o'-lanterns,
// a skeleton hand reaching out of a grave, an open grave with a dirt pile, a
// shovel and a skull, and a broken wrought-iron fence with a sagging gate
// across the front. Scott chose the hill form, 2026-09-26, and asked for
// better detail the same day: carved stones, textured ground, sculpted props
// and the fence.
//
// NOT A LANTERN. It is solid ground: the town's tealight rule (a 46 mm circle
// under 50 mm of headroom) would make the hill a mountain.
//
// COLOUR PARTS, ONE PRINT (haunted_cemetery.3mf), the town's palette with a
// moss-and-earth ground in place of a wall colour:
//   body    the hill, grave mounds, dirt pile, grass tufts, the pumpkins'
//           stems and tendrils
//   roof    (slate) the tree and crow, the fence and gate, stepping stones,
//           pebbles, and every flush inlay: epitaphs, carved motifs, cracks,
//           the pumpkins' faces, the skull's eyes
//   trim    (bone) the headstones and their bases, the grave's kerb, the
//           skeleton hand, the bones and the skull
//   accent  the pumpkins, the shovel
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// Every downward face is 50 deg or steeper. Things that stand on the ground
// are sunk below the LOWEST ground under them; things that lie on it (bones,
// pebbles, stepping stones) show only their upper halves.

include <BOSL2/std.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- the hill -------------------------------------------------------------------
A  = 52;                    // half-length of the oval base (x)
B  = 38;                    // half-depth (y); the front is -y
base_h = 3;                 // flat rim round the hill
function g(x, y, c) = c[2] * exp(-pow((x - c[0]) / c[3], 2) - pow((y - c[1]) / c[4], 2));
//   [x, y, height, sx, sy]
BUMPS = [
    [-14,   8, 24, 28, 22],     // the crest, back left, under the tree
    [ 20,   6, 10, 20, 18],     // a shoulder, right
    [ 37, -12,  6,  5,  5],     // the dirt pile beside the open grave
    [  5, -15,  2.2, 4, 6],     // the mound the hand comes out of
    [-38, -21,  1.8, 4, 5],     // a grave mound in front of RIP
    [-17, -21,  1.6, 3, 4.5],   // and inside BOO's kerb
];
function rho(x, y) = sqrt(pow(x / A, 2) + pow(y / B, 2));
function taper(r) = let (t = max(0, min(1, (1 - r) / 0.35))) t * t * (3 - 2 * t);
function hz(x, y) = base_h + taper(rho(x, y)) * (g(x, y, BUMPS[0]) + g(x, y, BUMPS[1]) + g(x, y, BUMPS[2])
                                               + g(x, y, BUMPS[3]) + g(x, y, BUMPS[4]) + g(x, y, BUMPS[5]));
// the lowest and highest ground over a rotated rectangle's corners, edges and centre
function gr(c, w, d, turn, f) = let (s = [for (i = [-1, -0.5, 0, 0.5, 1], j = [-1, 0, 1])
        let (u = i * w / 2, v = j * d / 2) hz(c[0] + u * cos(turn) - v * sin(turn), c[1] + u * sin(turn) + v * cos(turn))])
    f == "min" ? min(s) : max(s);

// A closed polyhedron: a fan at the centre, rings out to the oval's edge, a
// vertical rim down to the plate, and a flat bottom. Every face is listed
// clockwise seen from outside.
NR = 30;  NA = 96;
function rp(i, j) = let (r = i / NR, t = 360 * j / NA) [A * r * cos(t), B * r * sin(t)];
module hill() {
    top = concat([[0, 0, hz(0, 0)]],
                 [for (i = [1 : NR], j = [0 : NA - 1]) let (p = rp(i, j)) [p[0], p[1], hz(p[0], p[1])]]);
    bot = [for (j = [0 : NA - 1]) let (p = rp(NR, j)) [p[0], p[1], 0]];
    pts = concat(top, bot, [[0, 0, 0]]);
    function ri(i, j) = 1 + (i - 1) * NA + (j % NA);
    nb = 1 + NR * NA;
    nc = nb + NA;
    faces = concat(
        [for (j = [0 : NA - 1]) [0, ri(1, j + 1), ri(1, j)]],
        [for (i = [1 : NR - 1], j = [0 : NA - 1]) [ri(i, j), ri(i, j + 1), ri(i + 1, j + 1), ri(i + 1, j)]],
        [for (j = [0 : NA - 1]) [ri(NR, j), ri(NR, j + 1), nb + (j + 1) % NA, nb + j]],
        [for (j = [0 : NA - 1]) [nc, nb + j, nb + (j + 1) % NA]]);
    polyhedron(pts, faces, convexity = 6);
}

// An extrusion of a polygon drawn in (x, z), across y0..y1.
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
// A thick line through a list of 2D points, as hulls of circles.
module line2d(pts, w) for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) circle(d = w, $fn = 12); translate(pts[i + 1]) circle(d = w, $fn = 12); }

// ---- the open grave ------------------------------------------------------------------
pit_c = [27, -13.5];
pit_s = [8, 14];
pit_floor = 3.6;
module pit() translate([pit_c[0] - pit_s[0]/2, pit_c[1] - pit_s[1]/2, pit_floor]) cube([pit_s[0], pit_s[1], 40]);

// ---- headstones -----------------------------------------------------------------------
// Each stone stands on its own two-tier base, which is level and sunk below
// the lowest ground under it. The stone's foot is set 2 into the base, enough
// to cover the lift of its highest corner at the worst lean and tip (OOPS,
// 1.6). Its front edges are bevelled in three 0.3 steps; the outline's only
// downward edges are the buried foot and the cross's 58 deg gussets, so the
// steps only ever face up. Chips are cut by removing everything above a line,
// which leaves an upward face.
st_t = 3.0;
lt   = 0.8;                 // inlay depth
bev  = 0.3;                 // bevel step
//   [x, y, style, width, height above base, text, text size, text z, motif, motif z, turn, lean fwd, tip side]
// Widths are set by the words, measured with 1.12 letter spacing, inside the
// bevel. Every stroke survives a one-bead opening and every gap between
// letters survives a one-bead closing (offset pass on each word).
STONES = [
    [-38, -14, "round",  14, 16, "RIP",  4.6, 6.0,  "skull",     11.8,  10,  6, -4],
    [-17, -12, "gothic", 20, 23, "BOO",  4.4, 5.8,  "bat",       11.6,  -8, -5,  5],
    [  5,  -6, "broken", 17, 14, "BRB",  4.4, 5.6,  "",           0,     4,  8,  3],
    [ 27,  -3, "tablet", 19, 17, "NEXT", 3.9, 6.4,  "hourglass", 11.8,  -6,  3, -3],
    [ 28,  19, "round",  20, 16, "OOPS", 3.8, 5.6,  "",           0,    14,  9,  8],
    [-34,   8, "cross",  12, 20, "",     0,   0,    "",           0,    -4, -6,  0],
    [  4,  16, "obelisk", 7, 19, "",     0,   0,    "",           0,     8,  0,  0],
];
//   [stone index, points as [u, z above the base]] -- slate-filled cracks
CRACKS = [
    [1, [[1.2, 19.5], [2.2, 17.8], [1.4, 16.2], [2.4, 14.8]]],
    [2, [[1.6, 11.6], [2.5, 10.4], [1.8, 9.6]]],
    [4, [[4.4, 13.6], [3.4, 12.2], [4.2, 10.6], [3.0, 9.0]]],
];
function lancet_pts(a, hgt, ang = 58, n = 12) =
    let (R = 2 * a, t1 = 90 - ang, xt = a - R + R * cos(t1), zt = hgt + R * sin(t1), ap = zt + xt * tan(ang))
    concat([[-a, 0], [a, 0]],
           [for (i = [0 : n]) let (t = t1 * i / n) [a - R + R * cos(t), hgt + R * sin(t)]],
           [[0, ap]],
           [for (i = [n : -1 : 0]) let (t = t1 * i / n) [-(a - R + R * cos(t)), hgt + R * sin(t)]]);
function lancet_top(a, hgt, ang = 58) =
    let (R = 2 * a, t1 = 90 - ang) hgt + R * sin(t1) + (a - R + R * cos(t1)) * tan(ang);
// the outline, foot at z = -2 (inside the base), top at H
module stone_2d(style, w, H) {
    translate([0, -2]) {
        Ht = H + 2;
        if (style == "round") {
            translate([-w/2, 0]) square([w, Ht - w/2]);
            translate([0, Ht - w/2]) circle(d = w, $fn = 48);
        } else if (style == "gothic") {
            a = w / 2;
            polygon(lancet_pts(a, Ht - lancet_top(a, 0)));
        } else if (style == "broken") {
            polygon([[-w/2, 0], [w/2, 0], [w/2, Ht - 5.5], [w/2 - 2.5, Ht - 3.2], [w/2 - 4.2, Ht - 4.4],
                     [w/2 - 6.5, Ht - 1.4], [w/2 - 8.4, Ht - 2.2], [-w/2 + 2.8, Ht], [-w/2, Ht - 1.2]]);
        } else if (style == "tablet") {
            polygon([[-w/2, 0], [w/2, 0], [w/2, Ht - 4], [w/2 - 1.5, Ht - 2.5], [0, Ht], [-w/2 + 1.5, Ht - 2.5], [-w/2, Ht - 4]]);
        } else if (style == "cross") {
            // arms whose undersides rise 58 deg from the post: gussets, not ledges
            pw = 3.4;  ar = w / 2;  az = Ht - 7;  ah = 2.6;
            translate([-pw/2, 0]) square([pw, Ht]);
            polygon([[-pw/2, az - (ar - pw/2) * tan(58)], [pw/2, az - (ar - pw/2) * tan(58)],
                     [ar, az], [ar, az + ah], [-ar, az + ah], [-ar, az]]);
        }
    }
}
// chipped corners: everything above each line is removed
module chips(style, w, H) {
    if (style == "round")  polygon([[-w/2 - 1, H - 5.2], [-w/2 + 3.2, H + 1], [-w/2 - 1, H + 1]]);
    if (style == "gothic") polygon([[1.6, H - 3.0], [4, H + 1], [-2, H + 1], [-2, H - 0.6]]);
    if (style == "tablet") polygon([[w/2 + 1, H - 5.6], [w/2 - 3.2, H + 1], [w/2 + 1, H + 1]]);
}
module stone_face_2d(s, g = 0) {
    offset(delta = -g) difference() { stone_2d(s[2], s[3], s[4]); chips(s[2], s[3], s[4]); }
}
// base: [w, d] of the lower tier; the upper tier is 1.4 smaller each way
// 1.2 of base round the stone; at 1.5 RIP's base crossed BOO's and the rim
function base_wd(s) = s[2] == "obelisk" ? [10, 10] : [s[3] + 2.4, st_t + 2.4];
function base_top(s) = let (b = base_wd(s)) gr([s[0], s[1]], b[0], b[1], s[10], "max") + 1.1;
module stone_base(s) {
    b = base_wd(s);  zt = base_top(s);  zb = gr([s[0], s[1]], b[0], b[1], s[10], "min") - 1.5;
    translate([s[0], s[1], zb]) rotate([0, 0, s[10]]) {
        translate([-b[0]/2, -b[1]/2, 0]) cube([b[0], b[1], zt - zb - 0.7]);
        translate([-b[0]/2 + 0.7, -b[1]/2 + 0.7, 0]) cube([b[0] - 1.4, b[1] - 1.4, zt - zb]);
    }
}
module place_stone(s) translate([s[0], s[1], base_top(s)]) rotate([0, 0, s[10]]) rotate([s[11], s[12], 0]) children();
module stone_body(s) {
    if (s[2] == "obelisk") {
        // a shaft tapering 5.4 to 3.6 and a pyramidion, 2 into its base
        translate([0, 0, -2]) rotate([0, 0, 45]) cylinder(r1 = 2.7 * sqrt(2), r2 = 1.8 * sqrt(2), h = s[4] - 1, $fn = 4);
        translate([0, 0, s[4] - 3]) rotate([0, 0, 45]) cylinder(r1 = 1.8 * sqrt(2), r2 = 0, h = 3, $fn = 4);
    } else {
        xz(-st_t/2 + 3 * bev, st_t/2) stone_face_2d(s);
        for (k = [1 : 3]) xz(-st_t/2 + (3 - k) * bev, -st_t/2 + (4 - k) * bev + 0.01) stone_face_2d(s, k * bev);
    }
}
// ---- carved motifs, flush slate inlays -----------------------------------------------------
// Every slate stroke and every island of stone left inside one is >= 0.84.
module skull_2d() {
    difference() {
        union() { translate([0, 2.6]) circle(d = 4.8, $fn = 36); translate([-1.5, 0]) square([3, 2]); }
        for (s = [-1, 1]) translate([s * 0.95, 2.6]) circle(d = 1.0, $fn = 16);
        translate([0, 1.25]) polygon([[-0.5, 0], [0.5, 0], [0, 0.85]]);
    }
}
module bat_2d() {
    scale(1.1) {
        translate([0, 0.6]) scale([0.7, 1.2]) circle(d = 2, $fn = 24);
        for (s = [-1, 1]) scale([s, 1]) polygon([[0.4, 1.2], [2.4, 2.3], [4.3, 1.8], [3.6, 0.5], [2.8, 1.0], [2.0, 0.0], [1.3, 0.5], [0.4, 0.1]]);
        for (s = [-1, 1]) scale([s, 1]) polygon([[0.1, 1.7], [0.7, 1.7], [0.6, 2.6]]);
    }
}
module hourglass_2d() {
    translate([-2.2, 0]) square([4.4, 0.9]);
    translate([-2.2, 5.1]) square([4.4, 0.9]);
    polygon([[-1.6, 0.9], [1.6, 0.9], [0.45, 3.0], [1.6, 5.1], [-1.6, 5.1], [-0.45, 3.0]]);
}
module stone_inlay_2d(s) {
    if (s[5] != "")
        translate([0, s[7]]) text(s[5], size = s[6], font = "Montserrat:style=Black",
                                  halign = "center", valign = "center", spacing = 1.12, $fn = 16);
    translate([0, s[9]]) {
        if (s[8] == "skull")     translate([0, -2.4]) skull_2d();
        if (s[8] == "bat")       translate([0, -1.4]) bat_2d();
        if (s[8] == "hourglass") translate([0, -3.0]) hourglass_2d();
    }
    for (c = CRACKS) if (STONES[c[0]] == s) line2d(c[1], 0.9);
}
// Every inlay is cut from the PLACED stone, not placed after cutting: placed
// afterwards, its face against the stone came out of CGAL a rounding error off
// the stone's own face and left non-manifold edges round every word.
module stone_inlays() {
    for (s = STONES) intersection() {
        place_stone(s) stone_body(s);
        place_stone(s) translate([0, -st_t/2 + lt, 0]) rotate([90, 0, 0]) linear_extrude(lt + 0.01) stone_inlay_2d(s);
    }
}
// Clipped 0.6 above the plate: RIP, near the rim and tipped, once poked a
// corner 0.14 below it.
module stones() {
    intersection() {
        union() { for (s = STONES) { place_stone(s) stone_body(s); stone_base(s); } }
        translate([-200, -200, 0.6]) cube([400, 400, 200]);
    }
}
// BOO's grave: a stone kerb round a low mound
kerb_c = [-17, -21];  kerb_wd = [8, 10];
module kerb() {
    zt = gr(kerb_c, kerb_wd[0], kerb_wd[1], 0, "max") + 0.8;  zb = gr(kerb_c, kerb_wd[0], kerb_wd[1], 0, "min") - 1.5;
    translate([kerb_c[0], kerb_c[1], zb]) linear_extrude(zt - zb) difference() {
        square(kerb_wd, center = true);  square(kerb_wd - [2.4, 2.4], center = true);
    }
}

// ---- skeleton hand -------------------------------------------------------------------------
// Out of the mound in front of BRB. The palm's foot is narrower than the
// forearm, and it flares 34 deg so every finger root and the thumb's sit
// inside it: sticking out, their cube bottoms were flat ledges.
hand_at = [5, -15.5];
module bone(p0, p1, s = 1.3) hull() { translate(p0) cube(s, center = true); translate(p1) cube(s, center = true); }
module hand() {
    translate([hand_at[0], hand_at[1], hz(hand_at[0], hand_at[1]) - 2.5]) rotate([0, 0, -10]) {
        bone([0, 0, 0], [0.4, 0, 6.5], 1.8);
        hull() { translate([0.4, 0, 6.5]) cube([1.6, 1.6, 0.1], center = true);
                 translate([0.4, 0, 9.6]) cube([5.8, 1.6, 0.1], center = true); }
        for (f = [[-1.65, -14], [-0.55, -4], [0.55, 5], [1.65, 15]]) let (a = f[1], b = [f[0] + 0.4, 0, 9.4],
                c = b + [sin(a) * 3.0, 0, cos(a) * 3.0], d = c + [sin(a) * 1.0, -0.8, 1.7]) {
            bone(b, c); bone(c, d);
        }
        bone([-0.5, 0, 8.3], [-2.5, -0.3, 11.0]);
    }
}

// ---- bones and a skull on the ground --------------------------------------------------------
// Lying things show only their upper half: sunk to their axis at the LOWEST
// ground along them.
//   [x, y, turn, length]
BONES = [[15, -13, 25, 6.5], [-26, 1, -40, 6]];
module ground_bone(b) {
    zc = gr([b[0], b[1]], b[3] + 2, 2, b[2], "min");
    translate([b[0], b[1], zc]) rotate([0, 0, b[2]]) {
        hull() for (s = [-1, 1]) translate([s * b[3] / 2, 0, 0]) sphere(r = 0.75, $fn = 16);
        for (s = [-1, 1], t = [-1, 1]) translate([s * b[3] / 2, t * 0.6, 0]) sphere(r = 0.8, $fn = 16);
    }
}
skull_at = [40, -18];  skull_turn = -15;  skull_r = 2.6;
function skull_z() = gr(skull_at, 2 * skull_r, 2 * skull_r, 0, "min");
module place_skull() translate([skull_at[0], skull_at[1], skull_z()]) rotate([0, 0, skull_turn]) children();
module skull_dome() intersection() { sphere(r = skull_r, $fn = 40); translate([-5, -5, 0]) cube(10); }
module skull_face_2d() {
    for (s = [-1, 1]) translate([s * 0.95, 1.35]) circle(d = 1.05, $fn = 16);
    translate([0, 0.45]) polygon([[-0.45, 0], [0.45, 0], [0, 0.75]]);
}
module skull_eyes() {
    intersection() {
        place_skull() skull_dome();
        place_skull() translate([0, 0, 0]) rotate([90, 0, 0]) linear_extrude(10) skull_face_2d();
        place_skull() difference() { cube(20, center = true); sphere(r = skull_r - lt, $fn = 40); }
    }
}

// ---- dead tree and crow ------------------------------------------------------------------------
tree_at = [-16, 10];
function tree_z() = hz(tree_at[0], tree_at[1]) - 3;
// The trunk: a lobed outline extruded with a 45 deg twist, so its bark runs
// in spirals; the lobes lean 6 deg at most, and the taper only draws them in.
// A root flare and five roots, whose exposed parts only face up: each root is
// a hull whose lower points are all buried.
module trunk_2d(r) polygon([for (i = [0 : 41]) let (t = 360 * i / 42)
    (r * (1 + 0.12 * cos(7 * t) + 0.05 * cos(3 * t + 40))) * [cos(t), sin(t)]]);
module trunk() {
    translate([0, 0, 0]) linear_extrude(height = 21, twist = -45, scale = 0.62, slices = 24) trunk_2d(2.9);
    // flare: 4.1 across at the ground, drawn in to the trunk 4 mm up
    translate([0, 0, 0]) linear_extrude(height = 7, scale = 0.72, slices = 4) trunk_2d(4.1);
}
ROOTS = [20, 95, 160, 230, 300];
module roots() {
    for (a = ROOTS) let (d = [cos(a), sin(a)], far = 6.2 * d,
                         gz = hz(tree_at[0] + far[0], tree_at[1] + far[1]) - tree_z())
        hull() {
            translate([0.9 * d[0], 0.9 * d[1], 0]) cylinder(r = 1.2, h = 5.2, $fn = 10);
            translate([far[0], far[1], gz - 3]) cylinder(r = 0.6, h = 2.3, $fn = 8);
        }
}
// branches: [from, to, r_from, r_to]; hulls of two horizontal octagons, each
// leaning <= 38 deg from vertical, tips >= 1.3 across. The first segment of
// each limb starts ON the trunk's axis, low enough that its disc lies inside
// the twisted trunk even between the bark's lobes: started at the old offsets,
// the discs' flat undersides poked out between the lobes and the slicer
// propped every limb on a column.
TREE = [
    [[0, 0, 12],      [-6, 1, 26],      1.5, 1.15],             // left
    [[-6, 1, 26],     [-10, 0, 33],     1.15, 0.8],
    [[-10, 0, 33],    [-12, 1, 37],     0.8, 0.7],
    [[-6, 1, 26],     [-7.8, 3.6, 31],  0.9, 0.7],
    [[-6, 1, 26],     [-4, -1.5, 31.5], 0.8, 0.7],
    [[0, 0, 17],      [5, -1, 30],      1.3, 1.1],              // right
    [[5, -1, 30],     [8, 0, 38],       1.1, 0.8],
    [[8, 0, 38],      [10, -1, 41.5],   0.8, 0.7],
    [[5, -1, 30],     [7.8, -2.4, 35],  0.9, 0.7],
    [[5, -1, 30],     [3.5, -3.5, 35],  0.8, 0.7],
    [[0, 0, 17],      [-1, 4, 31],      1.2, 0.9],              // back
    [[-1, 4, 31],     [1, 6, 39],       0.9, 0.7],
    [[1, 6, 39],      [-0.2, 7.6, 42.5], 0.7, 0.7],
    [[0, 0, 8],       [5, -1.5, 17],    1.7, 1.7],              // the sawn-off stub
];
stub_top = [5, -1.5, 17];
module oct(p, r) translate(p) cylinder(r = r, h = 0.01, $fn = 10);
// The crow: one hull for body, head and the folded wings' tips, one for the
// tail, facing +x on its keel, which lies wholly inside the stub's cut top.
// This is the 1.25x box-bodied crow that passed the gate, with the wing tips
// added. A 1.5x crow with elliptical layers, checked at 59 deg underside by
// scipy, still drew 81 support lines when sliced alone on the same stub;
// this one draws none, sliced the same way. Trust the slicer, not the hull
// arithmetic. The beak is raised -- a cawing crow -- because a level one
// would be a ledge.
module crow() {
    scale(1.25) {
        hull() {
            translate([-1.0, -0.55, 0]) cube([2.1, 1.1, 0.05]);
            translate([-2.2, -1.3, 1.8]) cube([4.5, 2.6, 0.05]);
            translate([-1.8, -1.0, 3.0]) cube([3.8, 2.0, 0.05]);
            for (s = [-1, 1]) translate([-3.1, s * 0.9, 4.3]) cube(0.2, center = true);   // wing tips
            translate([2.4, 0, 3.9]) sphere(r = 1.1, $fn = 12);
            translate([4.3, 0, 5.2]) cube([0.5, 0.5, 0.5], center = true);
        }
        hull() {
            translate([-2.1, -0.9, 2.0]) cube([0.9, 1.8, 1.0]);
            translate([-3.9, -0.5, 4.3]) cube([0.6, 1.0, 0.6]);
        }
    }
}
module tree() {
    translate([tree_at[0], tree_at[1], tree_z()]) {
        trunk();
        roots();
        for (s = TREE) hull() { oct(s[0], s[2]); oct(s[1], s[3]); }
        // keel sunk 0.3 into the stub: set on its top, the two flat faces lay
        // 0.01 apart and CGAL left two zero-area faces between them
        translate(stub_top - [0, 0, 0.3]) rotate([0, 0, 200]) crow();
    }
}

// ---- wrought-iron fence and gate ----------------------------------------------------------------
// Across the front, on the oval at 0.9 of the rim. No flat rails: each rail's
// underside is a row of 58 deg gables between the pickets, so the fence prints
// like a row of little pointed windows. Leaning a panel about its own base
// only steepens those gables (their slope becomes arccos(cos 58 cos lean)).
// Broken: one panel has fallen out, two lean, one post is snapped.
fr = 0.9;
function fy(x) = -B * fr * sqrt(max(0, 1 - pow(x / (A * fr), 2)));
function fp(x) = [x, fy(x)];
pk_w = 1.3;  pk_s = 3.0;
s_lo = 1.6;  s_hi = 6.2;    // the two rails' springing heights above the panel's ground
function p_top(ang) = s_hi + (pk_s - pk_w) / 2 * tan(ang) + 1.0;
// one panel, drawn in (u, z) from u = 0 to L with its ground at z = 0: a
// slab with two rows of gable-topped openings between the pickets, and a
// spear point on every picket
module panel_2d(L, ang = 58) {
    n = floor((L - pk_w) / pk_s);  u0 = (L - n * pk_s) / 2;
    a = (pk_s - pk_w) / 2;  ha = a * tan(ang);  top = p_top(ang);
    difference() {
        translate([0, -2]) square([L, top + 2]);
        for (i = [0 : n - 1]) let (c = u0 + pk_s * (i + 0.5)) {
            polygon([[c - a, -5], [c + a, -5], [c + a, s_lo], [c, s_lo + ha], [c - a, s_lo]]);
            polygon([[c - a, s_lo + ha + 1.0], [c + a, s_lo + ha + 1.0], [c + a, s_hi], [c, s_hi + ha], [c - a, s_hi]]);
        }
    }
    for (i = [0 : n]) translate([u0 + pk_s * i - pk_w / 2, top - 0.1])
        polygon([[0, 0], [pk_w, 0], [pk_w, 1.4], [pk_w / 2, 2.7], [0, 1.4]]);
}
// a panel from world x0 to x1 along the fence, leaned `lean` deg outward
module panel(x0, x1, lean = 0, ang = 58) {
    a = fp(x0);  b = fp(x1);  L = norm(b - a);  t = atan2(b[1] - a[1], b[0] - a[0]);
    z = min([for (k = [0 : 4]) let (p = a + (b - a) * k / 4) hz(p[0], p[1])]) - 0.2;
    translate([a[0], a[1], z]) rotate([0, 0, t]) rotate([-lean, 0, 0])
        xz(-pk_w / 2, pk_w / 2) panel_2d(L, ang);
}
// posts: 1.8 square, a stepped cap and a pyramid finial; a snapped one stops short
module post(x, h = 11.5, snapped = false) {
    p = fp(x);  z = hz(p[0], p[1]);
    translate([p[0], p[1], z - 2.5]) rotate([0, 0, atan2(fy(x + 0.5) - fy(x - 0.5), 1)]) {
        translate([-0.9, -0.9, 0]) cube([1.8, 1.8, snapped ? 7.2 : h + 2.5]);
        if (snapped) translate([-0.9, -0.9, 7.2]) linear_extrude(0.9, scale = [0.4, 1]) square([1.8, 1.8]);
        else translate([0, 0, h + 2.5]) rotate([0, 0, 45]) cylinder(r1 = 0.9 * sqrt(2), r2 = 0, h = 2.2, $fn = 4);
    }
}
// lean > 0 tips a panel's top inward (+y), < 0 outward
FENCE_POSTS = [[-27, false], [-13, false], [-5, false], [5, false], [16, true], [27, false]];
// Clipped 0.6 above the plate: the gate's sagging free end reached 0.62 below it.
module fence() intersection() {
    fence_raw();
    translate([-200, -200, 0.6]) cube([400, 400, 200]);
}
module fence_raw() {
    for (p = FENCE_POSTS) post(p[0], p[0] == -13 || p[0] == -5 ? 13.5 : 11.5, p[1]);
    panel(-26.1, -13.9, 5);
    panel(-4.1, 4.1, 0);
    panel(5.9, 15.1, -7);
    // (16 to 27: the panel has fallen out, and that post has snapped)
    // The gate: one leaf, hinged on the left gate post and swung 110 deg into
    // the yard, clear of the path, sagging 5 deg at its free end. Its gables
    // are 64 deg so they stay above 58 after the sag. Sunk 1.2 at the hinge;
    // the ground rises under the rest of it.
    let (h = fp(-12.1), gz = hz(h[0], h[1]))
        translate([h[0], h[1], gz - 1.2]) rotate([0, 0, 110]) rotate([0, 5, 0])
            xz(-pk_w / 2, pk_w / 2) panel_2d(6.6, 64);
}

// ---- stepping stones and pebbles ------------------------------------------------------------------
// Tilted to the local slope, so each shows an even 0.4 above the ground.
function slope(p) = [hz(p[0] + 0.5, p[1]) - hz(p[0] - 0.5, p[1]), hz(p[0], p[1] + 0.5) - hz(p[0], p[1] - 0.5)];
PAVERS = [[-9, -29.5, 12], [-7.2, -26.2, -18], [-5.6, -23.0, 8], [-3.6, -20.0, -10]];
module pavers() {
    for (p = PAVERS) let (s = slope(p), c = [p[0], p[1]])
        translate([p[0], p[1], hz(p[0], p[1]) + 0.4]) rotate([atan(s[1]), -atan(s[0]), 0]) rotate([0, 0, p[2]])
            translate([0, 0, -1.4]) linear_extrude(1.4) offset(r = 0.6) square([2.4, 1.6], center = true);
}
PEBBLES = [[-31, -27, 1.5], [44, -4, 1.3], [-44, 12, 1.6], [-2, 30, 1.4], [-26, 24, 1.2], [18, 28, 1.5]];
module pebbles() {
    for (p = PEBBLES) translate([p[0], p[1], gr([p[0], p[1]], 2.6 * p[2], 2 * p[2], 0, "min")])
        scale([1.3, 1, 0.6]) sphere(r = p[2], $fn = 20);
}

// ---- grass tufts ----------------------------------------------------------------------------------
// Four stubby blades each, leaning out from the centre, 1.6 at the root and
// 1.4 at the tip, square to the axes: at 0.55 tips they were a third of every
// sub-bead span on the model, and the gate's 1st-percentile wall fell to 0.63.
TUFTS = [[-28, -3], [12, 4], [-46, -12], [44, -14], [-14, -27], [34, -24], [8, 30], [-32, 26], [26, 28], [46, 12], [-4, 22], [18, -24]];
module tufts() {
    for (t = TUFTS) let (z = gr(t, 3, 3, 0, "min"), zt = gr(t, 3, 3, 0, "max"))
        translate([t[0], t[1], 0]) for (i = [0 : 3]) let (a = 90 * i + 13 * t[0])
            hull() {
                translate([0.3 * cos(a), 0.3 * sin(a), z - 1]) cube([1.6, 1.6, 0.01], center = true);
                translate([1.2 * cos(a), 1.2 * sin(a), zt + 2.2]) cube([1.4, 1.4, 0.01], center = true);
            }
}

// ---- jack-o'-lanterns ----------------------------------------------------------------------------
// Deeply ribbed (8 lobes, 11%): below the equator the sides draw in at 57 deg
// to a foot sunk 0.8 below the lowest ground under it; the ribs only steepen
// that (to 62). Faces are flush slate inlays, cut only where the pumpkin
// faces forward -- cut straight through, the eyes also showed on its top.
// Each has a curling stem and a tendril lying on its top, in green.
//   [x, y, r, turn]
PUMPKINS = [[-45, -3, 5.5, -20], [10, -24, 6.2, 5], [40, 8, 5.0, 35]];
pk_rib = 0.11;
function pk_ze(r0) = r0 * 0.45 * tan(57);
function pk_r(r0, z, h) = let (ze = pk_ze(r0))
    z <= ze ? r0 * 0.55 + z / tan(57) : r0 * sqrt(max(0.02, 1 - pow((z - ze) / (h - ze), 2)));
function pk_k(t) = 1 + pk_rib * cos(8 * t);
function pk_ring(r0, z, h, g = 0) = [for (j = [0 : 63]) let (t = 360 * j / 64, r = pk_r(r0, z, h) * pk_k(t) - g)
    [r * cos(t), r * sin(t), z]];
function pk_h(r0) = r0 * 1.35;
// height of the top surface at radius rr, angle t
function pk_top(r0, rr, t) = let (ze = pk_ze(r0), h = pk_h(r0)) ze + (h - ze) * sqrt(max(0, 1 - pow(rr / (r0 * pk_k(t)), 2)));
module pumpkin_body(r0, g = 0) {
    h = pk_h(r0);
    skin([for (i = [0 : 24]) pk_ring(r0, g + (h - 2 * g) * i / 24, h, g)], slices = 0);
}
module pk_face_2d(r0) {
    k = r0 / 6;
    for (s = [-1, 1]) translate([s * 2.1 * k, 4.0 * k]) polygon([[-1.3 * k, 0], [1.3 * k, 0], [0, 1.9 * k]]);
    translate([0, 2.8 * k]) polygon([[-0.7 * k, 0], [0.7 * k, 0], [0, 1.1 * k]]);
    polygon([for (p = [[-3.6, 2.4], [-2.4, 1.4], [-1.5, 2.1], [-0.5, 1.2], [0.5, 2.1], [1.5, 1.2],
                       [2.4, 2.1], [3.6, 2.4], [2.6, 0.2], [1.2, 0.7], [0, 0.0], [-1.2, 0.7], [-2.6, 0.2]]) [p[0] * k, p[1] * k + 0.6]]);
}
function pk_ground(p) = let (r = p[2] * 0.6) min([for (t = [0 : 45 : 315]) hz(p[0] + r * cos(t), p[1] + r * sin(t))]);
module place_pk(p) translate([p[0], p[1], pk_ground(p) - 0.8]) rotate([0, 0, p[3]]) children();
module pumpkins() { for (p = PUMPKINS) place_pk(p) pumpkin_body(p[2]); }
module pk_faces() {
    for (p = PUMPKINS) difference() {
        intersection() {
            place_pk(p) pumpkin_body(p[2]);
            place_pk(p) translate([0, -p[2] * 0.4, 0.8]) rotate([90, 0, 0]) linear_extrude(20) pk_face_2d(p[2]);
        }
        place_pk(p) pumpkin_body(p[2], lt);
    }
}
// stem: two tapering segments, the upper bent 28 deg; tendril: a 0.9-wide
// ridge spiralling out from the stem along the top, vertical-sided and
// buried 2 into the pumpkin
module pk_stems() {
    for (p = PUMPKINS) place_pk(p) let (h = pk_h(p[2])) {
        translate([0, 0, h - 0.6]) {
            hull() { oct([0, 0, 0], 1.15); oct([0.3, 0, 1.6], 1.0); }
            hull() { oct([0.3, 0, 1.6], 1.0); oct([0.9, 0.2, 2.8], 0.8); }
        }
        let (pts = [for (i = [0 : 10]) let (t = 40 + 26 * i, rr = 1.6 + 0.12 * i)
                    [rr * cos(t), rr * sin(t), pk_top(p[2], rr, t)]])
            for (i = [0 : len(pts) - 2]) hull() for (q = [pts[i], pts[i + 1]])
                translate([q[0], q[1], q[2] - 2]) cylinder(d = 0.9, h = 2.6, $fn = 8);
    }
}

// ---- shovel ------------------------------------------------------------------------------------
// Stuck in the dirt pile, leaning back 18 deg, the spade's blade showing
// above the dirt. Its point's edges rise 54 deg; the T-grip's undersides 58.
shovel_at = [37, -12];
module shovel() {
    translate([shovel_at[0], shovel_at[1], hz(shovel_at[0], shovel_at[1]) - 2.2]) rotate([0, 0, 30]) rotate([-18, 0, 0]) {
        xz(-0.75, 0.75) polygon([[-2.4, 1.6], [-1.2, 0], [1.2, 0], [2.4, 1.6], [2.4, 6.5], [-2.4, 6.5]]);
        xz(-0.75, 0.75) polygon([[-2.4, 6.5], [2.4, 6.5], [0.75, 6.5 + 1.65 * tan(58)], [-0.75, 6.5 + 1.65 * tan(58)]]);
        translate([-0.75, -0.75, 8]) cube([1.5, 1.5, 12]);
        xz(-0.75, 0.75) polygon([[-0.75, 20 - 2.25 * tan(58)], [0.75, 20 - 2.25 * tan(58)],
                                 [3, 20], [3, 21.4], [-3, 21.4], [-3, 20]]);
    }
}

// ---- mark ------------------------------------------------------------------------------------
module brand_mark() {
    translate([0, 0, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- parts -----------------------------------------------------------------------------------
module roof_raw()   { tree(); fence(); pavers(); pebbles(); stone_inlays(); pk_faces(); skull_eyes(); }
module trim_raw()   { stones(); kerb(); hand(); for (b = BONES) ground_bone(b); place_skull() skull_dome(); }
module accent_raw() { pumpkins(); shovel(); }
module roof_part()   { roof_raw(); }
module trim_part()   { difference() { trim_raw(); roof_raw(); } }
module accent_part() { difference() { accent_raw(); roof_raw(); trim_raw(); } }
module body_part() {
    difference() {
        union() { hill(); pk_stems(); tufts(); }
        pit(); trim_raw(); accent_raw(); roof_raw(); brand_mark();
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
    color("#4A5140") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
}
