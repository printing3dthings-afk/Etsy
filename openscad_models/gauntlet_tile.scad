// =====================================================================
//  THE GAUNTLET -- OnBrandCraftz calibration tile
//
//  One plate that converts every number this shop measured off other
//  people's models into a fact about Scott's own P1S and filament.
//  Nothing here is decorative; every feature answers one open question.
//
//    joint chain     which socket clearance actually frees (5 values)
//    lattice hinge   does the measured 1.8/0.5/2.3 recipe survive folding
//    snap posts+clips  which barb interference clicks, which cracks
//    wall ladder     smallest wall this machine really produces
//    text block      smallest legible engraved and embossed lettering
//    dome pair       is $fa=2 visibly smoother than the $fa=12 default
//
//  Everything prints flat on the bed, no supports. The four movable
//  tests print as loose pieces beside the tile -- a moving part fused to
//  the tile cannot move, and a gap under a moving part cannot be printed
//  without support, so loose is the only honest option.
//
//  Ratios for the ball joint are the MEASURED ones (SKILL.md Technique
//  43), not invented: socket is a rounded rectangle in the swing plane,
//  the mouth is narrower than the ball and that is what retains it.
// =====================================================================

include <BOSL2/std.scad>

$fa = 4;                    // sane global; the dome pair overrides locally
$fs = 0.5;

part = "all";               // all | tile | chain | hinge | clips

// ---- tile -----------------------------------------------------------
tile_x    = 120;
tile_y    = 42;
tile_z    = 3;
tile_y0   = -40;            // tile spans y -40 .. +2
label_h   = 0.6;            // embossed label relief
engrave_d = 0.6;            // engraved label depth
mark_d    = 0.7;            // maker's mark depth (standing rule)

// ---- ball joint, from the measured standard --------------------------
D         = 4.8;                    // ball diameter -- the only free choice
sock_l    = 1.600  * D;             // 7.68  slot length, swing axis (X)
corner_r  = 0.3835 * D;             // 1.84  socket corner radius
mouth_w   = 0.833  * D;             // 4.00  opening toward the neighbour
neck_d    = 0.60   * D;             // 2.88  must pass the mouth freely
CLEAR     = [0.125, 0.150, 0.175, 0.200, 0.250];

link_l    = 11;             // block length along X
link_w    = 12;             // block width  along Y
link_h    = 9;              // block height
link_gap  = 1.2;            // visible dark band between links
ball_z    = 4.5;            // ball centre height -> ~1.9mm wall above and below
pitch     = link_l + link_gap;
chain_x0  = -12;            // chain lives x -12 .. +60, y +6 .. +18
chain_y   = 12;

// ---- lattice hinge, from the measured recipe -------------------------
lat_x     = 45;
lat_y     = 30;
lat_t     = 1.8;            // panel thickness == rib width, square in section
rib_w     = 1.8;
slot_w    = 0.5;
lat_pitch = rib_w + slot_w; // 2.30
n_slots   = 8;
bridge_l  = 4.5;
lat_x0    = -60;
lat_y0    = 6;

// ---- snap test -------------------------------------------------------
post_r      = 5.0;
post_h      = 12;
bead_z      = 7;
BEAD        = [0.45, 0.55, 0.65];   // -> 0.25 / 0.35 / 0.45mm interference
clip_clear  = 0.20;                 // the universal sliding clearance
clip_wall   = 2.3;
clip_h      = 8;
groove_extra = 0.20;                // groove deeper than the bead stands

// ---- thin wall ladder ------------------------------------------------
WALLS     = [0.4, 0.8, 1.2, 1.6, 2.0];
wall_len  = 10;
wall_hgt  = 10;

// ---- text ------------------------------------------------------------
SIZES     = [3, 4, 5, 6];
FONT      = "Liberation Sans:style=Bold";

// =====================================================================
//  helpers
// =====================================================================

module rrect(l, w, r) {
    hull() for (sx = [-1, 1], sy = [-1, 1])
        translate([sx * (l/2 - r), sy * (w/2 - r)]) circle(r = r);
}

// Label sitting ON a surface, raised. Kept to 4mm -- big enough that a
// failure to print it means something is very wrong, not that the label
// itself was the marginal feature.
module label(txt, size = 4) {
    linear_extrude(height = label_h)
        text(txt, size = size, font = FONT, halign = "center", valign = "center");
}

module label_cut(txt, size = 4, depth = engrave_d) {
    translate([0, 0, -depth])
        linear_extrude(height = depth + 0.02)
            text(txt, size = size, font = FONT, halign = "center", valign = "center");
}

// =====================================================================
//  1. JOINT CHAIN -- 6 links, 5 joints, one clearance each
//
//  Swing is in the PRINT PLANE (about Z), so every neck bends within a
//  layer rather than across layer bonds -- the 4-5x strong direction.
//  Socket therefore lies in XY and is extruded in Z with a real floor
//  and a real ceiling, so the ball cannot lift out either.
// =====================================================================

// Link i owns the socket that link i+1's ball sits in.
function link_x0(i) = chain_x0 + i * pitch;
function ball_x(i)  = link_x0(i) + link_l - sock_l / 2;   // ball of link i+1

module socket_void(clear) {
    sock_w = D + 2 * clear;                 // retention axis (Y)
    z0 = ball_z - sock_w / 2;
    z1 = ball_z + sock_w / 2;
    // pocket
    translate([0, 0, z0]) linear_extrude(height = z1 - z0)
        rrect(sock_l, sock_w, min(corner_r, sock_w / 2 - 0.01));
    // Mouth: a slot through the OWNING link's +X face, narrower than the
    // ball. It must stop inside the inter-link gap. Running it a full
    // link_l long (the first version) punched the same slot through the
    // NEXT link's body exactly where that link's neck welds on, so every
    // ball came out as a free-floating component with 0.56mm of air
    // around its own neck.
    mouth_len = sock_l / 2 + 0.5;
    translate([mouth_len / 2, 0, z0]) linear_extrude(height = z1 - z0)
        square([mouth_len, mouth_w], center = true);
}

module link_body(i) {
    translate([link_x0(i) + link_l / 2, chain_y, link_h / 2])
        cube([link_l, link_w, link_h], center = true);
}

// The ball belonging to link i (reaches BACKWARD into link i-1's socket)
module link_ball(i) {
    bx = ball_x(i - 1);
    translate([bx, chain_y, ball_z]) sphere(d = D);
    // Neck runs from the ball into this link's own body. Embed a real
    // 1.5mm, not a 0.01mm touch -- a coincident face is not a weld, and
    // the balls came out as free-floating components the first time.
    translate([bx, chain_y, ball_z]) rotate([0, 90, 0])
        cylinder(h = link_x0(i) - bx + 1.5, d = neck_d);
}

module chain() {
    // The sockets must be cut from the BODIES ONLY. Cutting them from a
    // union that already contains the balls deletes every ball -- the
    // socket void completely encloses the ball by construction. That
    // renders clean AND passes a component count (6 links, all separate
    // -- because nothing connects them any more), so neither check sees
    // it. Only plotting the sliced toolpaths showed the empty sockets.
    union() {
    for (i = [1 : 5]) link_ball(i);
    difference() {
        union() {
            for (i = [0 : 5]) link_body(i);
        }
        // each socket, positioned at its owning link's +X end
        for (i = [0 : 4])
            translate([ball_x(i), chain_y, 0]) socket_void(CLEAR[i]);
        // clearance value engraved on the link that OWNS that socket
        for (i = [0 : 4])
            translate([link_x0(i) + link_l / 2 - 1.5, chain_y, link_h])
                label_cut(str(CLEAR[i]), 3.2);
        translate([link_x0(5) + link_l / 2, chain_y, link_h])
            label_cut("OBC", 3.2);
    }
    }
}

// =====================================================================
//  2. LATTICE HINGE -- rib 1.8 / slot 0.5 / pitch 2.3, staggered bridges
//
//  Slots cut fully through a 1.8mm panel. Adjacent slots' bridges are
//  offset by half the bridge spacing so no straight tear path crosses
//  the hinge.
// =====================================================================

module lattice_strip() {
    zone_w = n_slots * lat_pitch;
    x_mid  = lat_x0 + lat_x / 2;
    y_mid  = lat_y0 + lat_y / 2;
    difference() {
        translate([x_mid, y_mid, lat_t / 2])
            cube([lat_x, lat_y, lat_t], center = true);
        for (s = [0 : n_slots - 1]) {
            sx = x_mid - zone_w / 2 + lat_pitch / 2 + s * lat_pitch;
            // one bridge per slot, staggered half a period between neighbours
            by = y_mid + (s % 2 == 0 ? -lat_y / 5 : lat_y / 5);
            difference() {
                translate([sx, y_mid, lat_t / 2])
                    cube([slot_w, lat_y + 1, lat_t + 1], center = true);
                translate([sx, by, lat_t / 2])
                    cube([slot_w + 1, bridge_l, lat_t + 1], center = true);
            }
        }
        // clear of the slot band -- an engraved label inside the hinge
        // zone would thin the very ribs under test
        translate([lat_x0 + 6.5, y_mid, lat_t]) rotate([0, 0, 90])
            label_cut("HINGE", 3.0);
    }
}

// =====================================================================
//  3. SNAP TEST -- fixed posts on the tile, loose clips beside them
//
//  Mirrors the real snap box: a skirt springing over a perimeter bead.
//  Interference = bead protrusion - the 0.2mm sliding clearance.
// =====================================================================

module snap_post(bead) {
    difference() {
        union() {
            cylinder(h = post_h, r = post_r);
            translate([0, 0, bead_z]) rotate_extrude()
                translate([post_r, 0]) circle(r = bead);
        }
        translate([0, 0, post_h]) label_cut(str(bead - 0.20), 3.0);
    }
}

module snap_clip(bead) {
    ir = post_r + clip_clear;
    difference() {
        cylinder(h = clip_h, r = ir + clip_wall);
        translate([0, 0, -0.5]) cylinder(h = clip_h + 1, r = ir);
        // internal groove, cut deeper than the bead stands so the clip
        // seats on its own rim rather than bottoming out on the bead
        translate([0, 0, bead_z - 1.0]) rotate_extrude()
            translate([ir, 0]) circle(r = bead + groove_extra);
        translate([0, 0, clip_h]) label_cut(str(bead - 0.20), 3.0);
    }
}

// =====================================================================
//  4/5/6. STATIC TESTS ON THE TILE
// =====================================================================

module wall_ladder() {
    for (i = [0 : len(WALLS) - 1]) {
        t = WALLS[i];
        translate([-52 + i * 11, -24, tile_z])
            cube([t, wall_len, wall_hgt], center = false);
        translate([-52 + i * 11 + 1, -27, tile_z])
            label(str(t), 3.2);
    }
}

// The whole point of this pair: same 18mm dome, two tessellation
// settings. If they feel and photograph identical, the $fa finding does
// not matter in plastic; if they do not, it is the cheapest quality win
// available.
module dome_pair() {
    translate([14, -8, tile_z]) {
        intersection() {
            sphere(r = 9, $fa = 12, $fs = 2);
            translate([0, 0, 9]) cube([20, 20, 18], center = true);
        }
    }
    translate([14, -19.5, tile_z]) label("fa12", 3.2);
    translate([40, -8, tile_z]) {
        intersection() {
            sphere(r = 9, $fa = 2, $fs = 0.4);
            translate([0, 0, 9]) cube([20, 20, 18], center = true);
        }
    }
    translate([40, -19.5, tile_z]) label("fa2", 3.2);
}

module text_block_raised() {
    for (i = [0 : len(SIZES) - 1])
        translate([-46 + i * 26, -32, tile_z]) label("OBC", SIZES[i]);
}

module text_block_engraved() {
    for (i = [0 : len(SIZES) - 1])
        translate([-46 + i * 26, -37.5, tile_z]) label_cut("OBC", SIZES[i]);
}

// Standing rule: every finished design carries the mark as a NEGATIVE
// cut on a face hidden in normal use -- here the underside, z=0, so the
// cutter must dip below zero to remove anything at all.
module makers_mark() {
    translate([0, -8, -0.5]) mirror([0, 1, 0])
        linear_extrude(height = mark_d + 0.5)
            text("OnBrandCraftz", size = 5.5, font = FONT,
                 halign = "center", valign = "center");
}

module tile() {
    difference() {
        union() {
            translate([0, tile_y0 + tile_y / 2, tile_z / 2])
                cube([tile_x, tile_y, tile_z], center = true);
            wall_ladder();
            dome_pair();
            text_block_raised();
            for (i = [0 : len(BEAD) - 1])
                translate([-50 + i * 16, -6, tile_z]) snap_post(BEAD[i]);
        }
        text_block_engraved();
        makers_mark();
        // right edge is the only run of tile with nothing standing on it
        translate([55, -20, tile_z]) rotate([0, 0, 90])
            label_cut("THE GAUNTLET", 3.6);
    }
}

module clips() {
    for (i = [0 : len(BEAD) - 1])
        translate([2 + i * 20, 31.5, 0]) snap_clip(BEAD[i]);
}

// =====================================================================

if (part == "tile")       tile();
else if (part == "chain") chain();
else if (part == "hinge") lattice_strip();
else if (part == "clips") clips();
else {
    tile();
    chain();
    lattice_strip();
    clips();
}
