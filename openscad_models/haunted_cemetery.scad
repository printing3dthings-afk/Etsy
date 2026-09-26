// Haunted Cemetery -- scenery for the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). A graveyard HILL: a lumpy mound with
// seven headstones of different styles leaning every which way, a bare dead
// tree on the crest with a crow on a sawn-off branch, three jack-o'-lanterns,
// a skeleton hand reaching out of a grave, and an open grave with a dirt pile
// and a shovel. Scott chose the hill form, 2026-09-26.
//
// NOT A LANTERN. It is solid ground: the town's tealight rule (a 46 mm circle
// under 50 mm of headroom) would make the hill a mountain.
//
// COLOUR PARTS, ONE PRINT (haunted_cemetery.3mf), the town's palette with a
// moss-and-earth ground in place of a wall colour:
//   body    the hill, the grave mounds, the dirt pile, the pumpkins' stems
//   roof    the tree and the crow (slate), the epitaphs and the pumpkins'
//           faces as flush inlays
//   trim    the headstones, the skeleton hand (bone)
//   accent  the pumpkins, the shovel
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// Every downward face is 50 deg or steeper: the headstones' tops only ever
// face up, the cross's arms and the shovel's handle have 58 deg gussets, the
// pumpkins' lower halves draw in at 57 deg, and the tree and crow are hulls
// whose sides were checked for their slope.

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
    [  2, -15,  2.2, 4, 6],     // the mound the hand comes out of
    [-38, -20,  1.8, 4, 6],     // a grave mound in front of RIP
    [-18, -18,  1.8, 4, 6],     // and in front of BOO
];
function rho(x, y) = sqrt(pow(x / A, 2) + pow(y / B, 2));
function taper(r) = let (t = max(0, min(1, (1 - r) / 0.35))) t * t * (3 - 2 * t);
function hz(x, y) = base_h + taper(rho(x, y)) * (g(x, y, BUMPS[0]) + g(x, y, BUMPS[1]) + g(x, y, BUMPS[2])
                                               + g(x, y, BUMPS[3]) + g(x, y, BUMPS[4]) + g(x, y, BUMPS[5]));

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
    nb = 1 + NR * NA;           // first bottom-ring index
    nc = nb + NA;               // the bottom's centre
    faces = concat(
        [for (j = [0 : NA - 1]) [0, ri(1, j + 1), ri(1, j)]],
        [for (i = [1 : NR - 1], j = [0 : NA - 1]) [ri(i, j), ri(i, j + 1), ri(i + 1, j + 1), ri(i + 1, j)]],
        [for (j = [0 : NA - 1]) [ri(NR, j), ri(NR, j + 1), nb + (j + 1) % NA, nb + j]],
        [for (j = [0 : NA - 1]) [nc, nb + j, nb + (j + 1) % NA]]);
    polyhedron(pts, faces, convexity = 6);
}

// An extrusion of a polygon drawn in (x, z), across y0..y1.
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();

// ---- the open grave ------------------------------------------------------------------
pit_c = [24, -13.5];
pit_s = [8, 14];
pit_floor = 3.6;
module pit() translate([pit_c[0] - pit_s[0]/2, pit_c[1] - pit_s[1]/2, pit_floor]) cube([pit_s[0], pit_s[1], 40]);

// ---- headstones -----------------------------------------------------------------------
// Each is drawn in (x, z) with its foot at z = 0, thickness st_t across y,
// and planted by its own foot: sunk below the LOWEST ground under it by 2.5,
// then leaned, tipped and turned. A top only ever faces up, so any outline
// prints; only the cross's arms need care.
st_t = 3.0;
lt   = 0.8;                 // lettering inlay depth
//   [x, y, style, width, height above ground, text, text size, text z, turn, lean fwd, tip side]
STONES = [
    [-38, -14, "round",  14, 17, "RIP",  4.6, 9.5,  10,  6, -4],
    [-18, -12, "gothic", 15, 20, "BOO!", 4.2, 9.5,  -8, -5,  5],
    [  2,  -7, "broken", 15, 15, "BRB",  4.4, 7.5,   4,  8,  3],
    [ 24,  -3, "tablet", 15, 18, "NEXT", 3.9, 10,   -6,  3, -3],
    [ 28,  19, "round",  14, 15, "OOPS", 3.9, 8,    14,  9,  8],
    [-34,   8, "cross",  12, 21, "",     0,   0,    -4, -6,  0],
    [  4,  16, "obelisk", 7, 20, "",     0,   0,     8,  0,  4],
];
function lancet_pts(a, hgt, ang = 58, n = 12) =
    let (R = 2 * a, t1 = 90 - ang, xt = a - R + R * cos(t1), zt = hgt + R * sin(t1), ap = zt + xt * tan(ang))
    concat([[-a, 0], [a, 0]],
           [for (i = [0 : n]) let (t = t1 * i / n) [a - R + R * cos(t), hgt + R * sin(t)]],
           [[0, ap]],
           [for (i = [n : -1 : 0]) let (t = t1 * i / n) [-(a - R + R * cos(t)), hgt + R * sin(t)]]);
function lancet_top(a, hgt, ang = 58) =
    let (R = 2 * a, t1 = 90 - ang) hgt + R * sin(t1) + (a - R + R * cos(t1)) * tan(ang);
// the outline, total height H (foot to top)
module stone_2d(style, w, H) {
    if (style == "round") {
        translate([-w/2, 0]) square([w, H - w/2]);
        translate([0, H - w/2]) circle(d = w, $fn = 48);
    } else if (style == "gothic") {
        a = w / 2;
        polygon(lancet_pts(a, H - (lancet_top(a, 0) - 0)));
    } else if (style == "broken") {
        // snapped off: a jagged top falling to the right
        polygon([[-w/2, 0], [w/2, 0], [w/2, H - 5.5], [w/2 - 2.5, H - 3.2], [w/2 - 4.2, H - 4.4],
                 [w/2 - 6.5, H - 1.4], [w/2 - 8.4, H - 2.2], [-w/2 + 2.8, H], [-w/2, H - 1.2]]);
    } else if (style == "tablet") {
        // square shoulders cut back at 45 deg, and a low pediment
        polygon([[-w/2, 0], [w/2, 0], [w/2, H - 4], [w/2 - 1.5, H - 2.5], [0, H], [-w/2 + 1.5, H - 2.5], [-w/2, H - 4]]);
    } else if (style == "cross") {
        // post 3.4 wide; arms 12 across whose undersides rise 58 deg from
        // the post, so the arms are gussets, not ledges
        pw = 3.4;  ar = w / 2;  az = H - 7;  ah = 2.6;
        translate([-pw/2, 0]) square([pw, H]);
        polygon([[-pw/2, az - (ar - pw/2) * tan(58)], [pw/2, az - (ar - pw/2) * tan(58)],
                 [ar, az], [ar, az + ah], [-ar, az + ah], [-ar, az]]);
    }
}
function st_ground(s) = let (c = [s[0], s[1]], w = s[3] / 2 + 1, t = st_t)
    min([for (dx = [-w, 0, w], dy = [-t, 0, t]) hz(c[0] + dx, c[1] + dy)]);
module place_stone(s) {
    z0 = st_ground(s) - 2.5;
    translate([s[0], s[1], z0]) rotate([0, 0, s[8]]) rotate([s[9], s[10], 0]) children();
}
function st_total(s) = hz(s[0], s[1]) - st_ground(s) + 2.5 + s[4];
module stone_body(s) {
    H = st_total(s);
    if (s[2] == "obelisk") {
        // a stepped foot, then a shaft tapering 5.4 to 3.6, and a pyramidion
        translate([-4, -4, 0]) cube([8, 8, H - 17]);
        translate([0, 0, H - 17]) rotate([0, 0, 45])
            cylinder(r1 = 2.7 * sqrt(2), r2 = 1.8 * sqrt(2), h = 14, $fn = 4);
        translate([0, 0, H - 3]) rotate([0, 0, 45]) cylinder(r1 = 1.8 * sqrt(2), r2 = 0, h = 3, $fn = 4);
    } else {
        xz(-st_t/2, st_t/2) stone_2d(s[2], s[3], H);
    }
}
// letters sit so their baseline is s[7] above the ground at the stone's foot
module stone_text(s) {
    if (s[5] != "") {
        H0 = st_total(s) - s[4];
        translate([0, -st_t/2 + lt, H0 + s[7]]) rotate([90, 0, 0]) linear_extrude(lt + 0.01)
            text(s[5], size = s[6], font = "Montserrat:style=Black", halign = "center", valign = "center");
    }
}
module stones()      { for (s = STONES) place_stone(s) stone_body(s); }
module epitaphs()    { for (s = STONES) place_stone(s) intersection() { stone_body(s); stone_text(s); } }

// ---- skeleton hand -------------------------------------------------------------------------
// Out of the mound in front of BRB, reaching up. Every bone is a hull of two
// small squares, 1.3 across, never more than 35 deg off vertical.
hand_at = [2, -15.5];
module bone(p0, p1, s = 1.3) hull() { translate(p0) cube(s, center = true); translate(p1) cube(s, center = true); }
module hand() {
    translate([hand_at[0], hand_at[1], hz(hand_at[0], hand_at[1]) - 2.5]) rotate([0, 0, -10]) {
        bone([0, 0, 0], [0.4, 0, 6.5], 1.8);                    // forearm
        hull() { translate([0.4, 0, 6.5]) cube([2.2, 1.6, 0.1], center = true);
                 translate([0.4, 0, 9.4]) cube([4.4, 1.5, 0.1], center = true); }   // palm, flaring 20 deg
        for (f = [[-1.6, -14], [-0.5, -4], [0.6, 5], [1.7, 15]]) let (a = f[1], b = [f[0] + 0.4, 0, 9.4],
                c = b + [sin(a) * 3.2, 0, cos(a) * 3.2], d = c + [sin(a) * 1.4, -1.1, 1.6]) {
            bone(b, c); bone(c, d);                              // two joints, the tip curling forward
        }
        bone([-1.5, 0, 7.4], [-3.4, -0.4, 9.8]);                 // thumb, 38 deg out
    }
}

// ---- dead tree and crow ------------------------------------------------------------------------
tree_at = [-16, 10];
// segments: [from, to, r_from, r_to]. Each is a hull of two horizontal
// octagons; the lean of every one is <= 38 deg from vertical, and the taper
// makes its overhanging side steeper still.
TREE = [
    [[0, 0, 0],       [0.6, 0.2, 9],    3.0, 2.5],
    [[0.6, 0.2, 9],   [-0.4, 0.4, 16],  2.5, 2.1],
    [[-0.4, 0.4, 16], [0.5, 0, 21],     2.1, 1.8],
    [[-0.4, 0.4, 15], [-6, 1, 26],      1.6, 1.15],             // left
    [[-6, 1, 26],     [-10, 0, 33],     1.15, 0.75],
    [[-6, 1, 26],     [-7.8, 3.6, 31],  0.9, 0.7],
    [[0.5, 0, 21],    [5, -1, 30],      1.5, 1.1],              // right
    [[5, -1, 30],     [8, 0, 38],       1.1, 0.75],
    [[5, -1, 30],     [7.8, -2.4, 35],  0.9, 0.7],
    [[0.5, 0, 21],    [-1, 4, 31],      1.3, 0.9],              // back
    [[-1, 4, 31],     [1, 6, 39],       0.9, 0.7],
    [[0.6, 0.2, 11],  [5, -1.5, 17],    1.9, 1.7],              // the sawn-off stub
];
stub_top = [5, -1.5, 17];
module oct(p, r) translate(p) cylinder(r = r, h = 0.01, $fn = 10);
// The crow: one hull for body and head, one for the tail, facing +x on its
// keel. Hull vertices checked in order along the underside: keel to breast
// 54 deg, breast to chin 55, chin to beak 54 (the beak is raised -- a cawing
// crow -- because a level one would be a ledge), keel to rump 54, rump to
// tail 54.
module crow() {
    scale(1.25) {
        hull() {
            translate([-1.2, -0.7, 0]) cube([2.5, 1.4, 0.05]);
            translate([-2.2, -1.3, 1.4]) cube([4.5, 2.6, 0.05]);
            translate([-1.8, -1.0, 2.6]) cube([3.8, 2.0, 0.05]);
            translate([2.4, 0, 3.4]) sphere(r = 1.1, $fn = 12);
            translate([4.5, 0, 4.5]) cube([0.5, 0.5, 0.5], center = true);
        }
        hull() {
            translate([-2.2, -0.9, 1.4]) cube([1, 1.8, 1.2]);
            translate([-4.1, -0.5, 3.9]) cube([0.6, 1.0, 0.6]);
        }
    }
}
module tree() {
    translate([tree_at[0], tree_at[1], hz(tree_at[0], tree_at[1]) - 3]) {
        for (s = TREE) hull() { oct(s[0], s[2]); oct(s[1], s[3]); }
        translate(stub_top) rotate([0, 0, 200]) crow();
    }
}

// ---- jack-o'-lanterns ----------------------------------------------------------------------------
// Ribbed: the radius is modulated by 8 lobes. Below the equator the sides
// draw in at 57 deg to a foot sunk 1.2 into the ground; above it they round
// over to the stem. Faces are flush slate inlays, 0.8 deep.
//   [x, y, r, turn]
PUMPKINS = [[-40, -24, 5.5, -20], [-6, -27, 6.2, 5], [40, 8, 5.0, 35]];
function pk_r(r0, z, h) = let (ze = r0 * 0.45 * tan(57))
    z <= ze ? r0 * 0.55 + z / tan(57) : r0 * sqrt(max(0.02, 1 - pow((z - ze) / (h - ze), 2)));
function pk_ring(r0, z, h, g = 0) = [for (j = [0 : 47]) let (t = 360 * j / 48, r = pk_r(r0, z, h) * (1 + 0.07 * cos(8 * t)) - g)
    [r * cos(t), r * sin(t), z]];
function pk_h(r0) = r0 * 1.35;
module pumpkin_body(r0, g = 0) {
    h = pk_h(r0);
    skin([for (i = [0 : 24]) pk_ring(r0, g + (h - 2 * g) * i / 24, h, g)], slices = 0);
}
module pk_face_2d(r0) {
    k = r0 / 6;
    for (s = [-1, 1]) translate([s * 2.1 * k, 4.4 * k]) polygon([[-1.3 * k, 0], [1.3 * k, 0], [0, 1.9 * k]]);
    translate([0, 3.1 * k]) polygon([[-0.7 * k, 0], [0.7 * k, 0], [0, 1.1 * k]]);
    polygon([for (p = [[-3.6, 2.6], [-2.4, 1.6], [-1.5, 2.3], [-0.5, 1.4], [0.5, 2.3], [1.5, 1.4],
                       [2.4, 2.3], [3.6, 2.6], [2.6, 0.4], [1.2, 0.9], [0, 0.2], [-1.2, 0.9], [-2.6, 0.4]]) p * k]);
}
module place_pk(p) translate([p[0], p[1], hz(p[0], p[1]) - 1.2]) rotate([0, 0, p[3]]) children();
module pumpkins() { for (p = PUMPKINS) place_pk(p) pumpkin_body(p[2]); }
module pk_faces() {
    for (p = PUMPKINS) place_pk(p) difference() {
        intersection() {
            pumpkin_body(p[2]);
            translate([0, 0, 0.8]) rotate([90, 0, 0]) linear_extrude(20) pk_face_2d(p[2]);
        }
        pumpkin_body(p[2], lt);
    }
}
module pk_stems() {
    for (p = PUMPKINS) place_pk(p) translate([0, 0, pk_h(p[2]) - 0.6]) rotate([12, -8, 0])
        cylinder(r1 = 1.2, r2 = 0.9, h = 2.4, $fn = 10);
}

// ---- shovel ------------------------------------------------------------------------------------
// Stuck in the dirt pile, leaning back 18 deg. The T-grip's undersides rise
// 58 deg from the shaft.
shovel_at = [37, -12];
module shovel() {
    translate([shovel_at[0], shovel_at[1], hz(shovel_at[0], shovel_at[1]) - 3.5]) rotate([0, 0, 30]) rotate([-18, 0, 0]) {
        translate([-2.3, -0.6, 0]) cube([4.6, 1.2, 5.5]);                   // blade, mostly buried
        xz(-0.6, 0.6) polygon([[-2.3, 5.5], [2.3, 5.5], [0.75, 5.5 + 1.55 * tan(58)], [-0.75, 5.5 + 1.55 * tan(58)]]);
        translate([-0.75, -0.75, 7]) cube([1.5, 1.5, 12]);                  // shaft
        xz(-0.75, 0.75) polygon([[-0.75, 19 - 2.25 * tan(58)], [0.75, 19 - 2.25 * tan(58)],
                                 [3, 19], [3, 20.4], [-3, 20.4], [-3, 19]]);
    }
}

// ---- mark ------------------------------------------------------------------------------------
module brand_mark() {
    translate([0, 0, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- parts -----------------------------------------------------------------------------------
module roof_raw()   { tree(); epitaphs(); pk_faces(); }
module trim_raw()   { stones(); hand(); }
module accent_raw() { pumpkins(); shovel(); }
module roof_part()   { roof_raw(); }
module trim_part()   { difference() { trim_raw(); roof_raw(); } }
module accent_part() { difference() { accent_raw(); roof_raw(); trim_raw(); } }
module body_part() {
    difference() {
        union() { hill(); pk_stems(); }
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
