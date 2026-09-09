// Labeled stacking bin -- one parametric family, four sizes, two colours.
//
// The point of this design is the LABEL. A printed bin normally gets a
// peel-off sticker; this one carries its label as a second filament flush in
// a raised plate, so it cannot peel, smudge or fade. That is only safe to
// promise because tools/glyph_probe.py can measure the thinnest stroke the
// text actually produces -- "OnBrandCraftz" in Caveat Bold measured 0.48-1.08
// extrusions on a real part and printed BLANK on three of four sauce models,
// and nothing in the pipeline caught it. Every label here is checked against
// the 2-extrusion floor before it ships.
//
// FAMILY, not a model. Corpus finding: sets sell, and retrofitting a family
// onto a bespoke model does not work. One file, four sizes, on a 90mm grid so
// a 2-wide bin stacks across two 1-wide bins.
//
//     size = "S"   90 x 70 x 45      size = "L"   180 x 70 x 45
//     size = "M"   90 x 70 x 90      size = "XL"  180 x 70 x 90
//
// Prints open-side up, no supports anywhere. Every feature that would
// otherwise overhang is chamfered at 45: the label plate's underside, the
// stacking pockets' ceilings are short bridges, and the rim tongues face up.

$fa = 2;  $fs = 0.4;

include <BOSL2/std.scad>

part  = "all";              // all | bin | tile | tiletext
size  = "S";                // S | M | L | XL
label = "PARTS";

UNIT_W = 90;                // grid pitch -- the whole family stacks on this
D      = 70;
cols   = (size == "L" || size == "XL") ? 2 : 1;
Hgt    = (size == "M" || size == "XL") ? 90 : 45;
W      = cols * UNIT_W;

wall    = 1.68;             // EXACTLY 4 x 0.42 extrusions. 1.6 looks
                            // equivalent and is not: it leaves 0.34mm the
                            // slicer fills with slow gap-fill segments, and
                            // the same bin sliced 48 MINUTES SLOWER on LESS
                            // material. Wall thickness wants to be a whole
                            // number of extrusions. The first build used 2.4 with a
                            // 3.5 floor and printed in 4h00 -- over the 4h/unit
                            // ceiling, the wall alone being 34.6 of its 53.4
                            // cm3. A storage bin is a commodity and cannot cost
                            // four hours of printer time.
floor_t = 1.6;             // 8 layers. The scoop and the extra tongues it
                            // forced cost ~27 min; this and the shorter pads buy
                            // it back. Nothing structural sits on the floor but
                            // the contents.
out_r   = 6;

// ---- stacking: discrete tongues on local pads ----------------------------
// A CONTINUOUS LAP JOINT WAS TRIED AND IS WRONG HERE, twice over, and both
// failures are worth keeping:
//
//  1. It severs the floor. The base recess is as deep as the floor is thick,
//     so a ring-shaped recess removes the floor's outer edge for its full
//     thickness and the floor comes away from the wall all the way around.
//     Watertight check catches it; a render does not.
//  2. It does not fit. A lap needs skirt + gap + lip across the wall -- three
//     zones in 1.6mm is 0.5mm each, under two extrusions apiece.
//
// So: short tongues at four points, each sitting on a local PAD that thickens
// the wall to 4.6mm just there. The pads run full height (self-supporting, no
// chamfer to get wrong) and double as internal corner ribs. Four pads cost
// 5.4 cm3 against the 20 cm3 the leaner wall and floor give back.
tng_t   = 1.2;
tng_h   = 2.0;
tng_len = 10;
pad_d   = 2.4;              // pad depth into the cavity, past the wall
pad_len = 8;
stk_clr = 0.25;
pkt_d   = tng_h + 0.3;
tng_off = 30;               // front/back tongues sit OUTBOARD of the scoop.
                            // A single centred tongue is exactly where the
                            // scoop cuts, so the scoop would silently delete
                            // the front half of the stacking feature.
tng_c   = (wall + pad_d) / 2;   // tongue centred across wall+pad

// ---- label: a SLIDE-IN TILE, not a moulded-in inlay -----------------------
// The label was originally a two-colour inlay in this vertical face. That is
// the wrong construction and the reason is purge, not looks: the text spans 56
// layers, so a 2-colour print makes 112 tool changes, and at Bambu's default
// ~350mm3 flush that is 48.6 g thrown into the wipe tower -- MORE THAN THE
// 45 g BIN. Even a tuned 150mm3 flush costs 20.8 g.
//
// A separate tile printed FLAT, text face down on smooth PEI, puts the text in
// three layers: 6 tool changes, ~2.6 g, and a mirror-smooth face. It is also
// re-labelable, which is the actual point of a labelled storage system -- swap
// one tile instead of reprinting a four-hour bin.
//
// SLIDE-IN, NOT SNAP. A snap needs a spring-arm force calculation, fatigues,
// and fights you every time you change it. A slot has none of that and the
// tile drops in under gravity.
plate_w     = min(W - 24, 76);
plate_h     = 20;
plate_r     = 3;
plate_proud = 1.6;
plate_zc    = floor_t + plate_h/2 + 6;
label_size  = 11;           // "PARTS" measures 52.1 x 11.2mm at this size and
                            // must fit the tile's 63.6 x 16.6 window.
label_font  = "Montserrat:style=Black";

slot_w   = 64;              // tile window
lip_w    = 2.0;             // how far each retaining lip overhangs the tile
lip_t    = 0.6;             // lip thickness, at the front of the pocket
pocket_d = 2.0;             // total pocket depth. The plate is 1.6 proud on a
                            // 1.68 wall = 3.28mm of material, so this leaves
                            // 1.28mm behind the tile.
stop_h   = 1.5;             // plate left below the slot, so the tile lands on
                            // something instead of falling through
tile_t   = 1.2;             // 6 layers flat
tile_clr = 0.2;
text_d   = 0.6;             // 3 layers -- the whole purge budget

module outer_2d() { offset(r = out_r) square([W - 2*out_r, D - 2*out_r], center = true); }
module cav_2d()   { offset(r = -wall) outer_2d(); }

// Each column's centre on the 90mm grid, so a 2-wide bin's tongues land on
// the same coordinates two 1-wide bins present.
function col_x(c) = -W/2 + UNIT_W/2 + c * UNIT_W;

// One placement rule drives the pads, the tongues and the pockets, so they can
// never drift apart: `t` is the across-wall thickness, `l` the length along
// the wall, `h` the height, `z` the centre height, `inset` how far the feature
// centre sits from the outer face.
module wall_feature(t, l, h, z, inset) {
    for (c = [0 : cols - 1]) {
        for (sy = [-1, 1]) for (sx = [-1, 1])
            translate([col_x(c) + sx * tng_off, sy * (D/2 - inset), z])
                cube([l, t, h], center = true);
        if (c == 0)          translate([-W/2 + inset, 0, z]) cube([t, l, h], center = true);
        if (c == cols - 1)   translate([ W/2 - inset, 0, z]) cube([t, l, h], center = true);
    }
}
module stack_pads()   { wall_feature(wall + pad_d, pad_len, Hgt, Hgt/2, (wall + pad_d)/2); }
module rim_tongues()  { wall_feature(tng_t, tng_len, tng_h, Hgt + tng_h/2, tng_c); }
module base_pockets() { wall_feature(tng_t + 2*stk_clr, tng_len + 2*stk_clr,
                                     pkt_d, pkt_d/2 - 0.01, tng_c); }

// ---- label plate ---------------------------------------------------------
// Shrinking the profile by `k` chamfers all four edges at 45 when hulled
// against the unshrunk one -- the underside is the edge that matters, since
// a square-shouldered proud plate would print as a 1.6mm unsupported ledge.
// Shrinks the sides and the BOTTOM by k while leaving the TOP where it is, so
// hulling against the unshrunk profile chamfers the underside (the only edge
// that overhangs) and keeps the top square -- the top has to stay square or
// the chamfer narrows the slot's mouth and the tile will not go in.
module plate_2d(k) {
    offset(r = plate_r) offset(r = -plate_r)
        translate([0, k/2]) square([plate_w - 2*k, plate_h - k], center = true);
}
module plate_slice(k, y) {
    translate([0, y, plate_zc]) rotate([90, 0, 0])
        linear_extrude(0.02, center = true) plate_2d(k);
}
module label_plate() {
    hull() {
        plate_slice(0, -D/2 + 0.02);
        plate_slice(plate_proud, -D/2 - plate_proud);
    }
}

module label_2d() {
    text(label, size = label_size, font = label_font,
         halign = "center", valign = "center");
}

// The slot: a T in horizontal section. A narrow mouth between the two lips at
// the front, a full-width cavity behind them, both running out through the top
// so the tile slides down in.
module label_slot() {
    yf = -D/2 - plate_proud;
    zt = plate_zc + plate_h/2 + 0.1;
    zb = plate_zc - plate_h/2 + stop_h;
    translate([0, yf + lip_t/2 - 0.25, (zb + zt)/2])
        cube([slot_w - 2*lip_w, lip_t + 0.5, zt - zb], center = true);
    translate([0, yf + lip_t + (pocket_d - lip_t)/2, (zb + zt)/2])
        cube([slot_w, pocket_d - lip_t, zt - zb], center = true);
}

// ---- the tile, printed FLAT, text face down ------------------------------
tile_w = slot_w - 2 * tile_clr;
tile_h = plate_h - stop_h - 2 * tile_clr;
module tile_2d() {
    offset(r = plate_r - 0.5) offset(r = -(plate_r - 0.5))
        square([tile_w, tile_h], center = true);
}
module label_tile()      { difference() { linear_extrude(tile_t) tile_2d();
                                          translate([0,0,-0.01])
                                              linear_extrude(text_d + 0.01) label_2d(); } }
module label_tile_text() { linear_extrude(text_d) label_2d(); }

// ---- front scoop ---------------------------------------------------------
// A plain-fronted box is a box; a bin you can see into and reach into is a
// bin. Built as a hull() of explicit corner points at two Y depths -- never a
// rotated cuboid, which is how this shop has twice produced a cutter whose
// real bounding extent quietly ate the whole model.
//
// The profile is deliberately CONVEX so hull() reproduces it exactly. It also
// stops well above the label plate (plate tops out at z=28, the scoop bottoms
// at 30) so it can never orphan the plate off the wall.
sc_w        = 26;           // half-width; tongues sit at 30, outboard of it
sc_low      = 30;
sc_shoulder = 38;
module prism_xz(pts, y0, y1) {
    hull() for (q = pts) for (y = [y0, y1])
        translate([q[0], y, q[1]]) sphere(r = 0.01, $fn = 6);
}
// ONE SCOOP PER COLUMN, not one wide one. A single scoop scaled to a 180mm
// bin spans +/-52 and swallows the inner tongues at +/-15; keeping it per
// column puts every scoop between its own column's two tongues by
// construction, at any width the family grows to.
module front_scoop() {
    for (c = [0 : cols - 1]) translate([col_x(c), 0, 0])
        prism_xz([[-sc_w, Hgt + 6], [sc_w, Hgt + 6],
                  [sc_w, sc_shoulder], [sc_w * 0.55, sc_low],
                  [-sc_w * 0.55, sc_low], [-sc_w, sc_shoulder]],
                 -D/2 - plate_proud - 2, -D/2 + wall + 1);
}

// ---- maker's mark --------------------------------------------------------
// Bottom face, engraved negative, Technique 4's confirmed pattern verbatim.
// Sized to ~40% of the 70mm short run, not inherited from a sibling model.
mark_size  = 70 * 0.40 / 3.177;
mark_depth = 0.7;
module brand_mark() {
    translate([0, 0, -0.5]) linear_extrude(mark_depth + 0.5)
        mirror([0, 1, 0])
            text("OBC", size = mark_size, font = label_font,
                 halign = "center", valign = "center");
}

// ORDER MATTERS AND IT IS NOT COSMETIC. The pads and tongues live INSIDE the
// cavity's footprint, so unioning them before the cavity is cut deletes them
// silently -- the model still renders, still gates watertight, and is simply
// 2mm shorter with no stacking feature at all. Same trap the drawer module
// documents; reproduced here anyway. Cavity first, then the features that sit
// in it, then the cuts that go into those features.
module bin() {
    difference() {
        union() {
            difference() {
                union() { linear_extrude(Hgt) outer_2d(); label_plate(); }
                translate([0, 0, floor_t]) linear_extrude(Hgt + tng_h + 1) cav_2d();
            }
            stack_pads();
            rim_tongues();
        }
        base_pockets();
        front_scoop();
        label_slot();
        brand_mark();
    }
}
if      (part == "bin")      bin();
else if (part == "tile")     label_tile();
else if (part == "tiletext") label_tile_text();
else if (part == "all")    { bin(); }
