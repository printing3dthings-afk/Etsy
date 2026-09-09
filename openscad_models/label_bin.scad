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

part  = "all";              // all | bin | label
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
floor_t = 2.0;
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
pad_len = 10;
stk_clr = 0.25;
pkt_d   = tng_h + 0.3;
tng_c   = (wall + pad_d) / 2;   // tongue centred across wall+pad

// ---- label plate ---------------------------------------------------------
plate_w     = min(W - 24, 76);
plate_h     = 20;
plate_r     = 3;
plate_proud = 1.6;          // raised, not recessed: keeps the wall at full
                            // thickness behind the text (Technique 52's
                            // "raise it outward instead of cutting in")
plate_zc    = floor_t + plate_h/2 + 6;
inlay_d     = 1.0;
label_size  = 11;           // "PARTS" measures ~58mm at this size; a longer
                            // word needs this reduced -- re-run glyph_probe.
label_font  = "Montserrat:style=Black";

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
        for (sy = [-1, 1])
            translate([col_x(c), sy * (D/2 - inset), z]) cube([l, t, h], center = true);
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
module plate_2d(k) {
    offset(r = -k) offset(r = plate_r)
        square([plate_w - 2*plate_r, plate_h - 2*plate_r], center = true);
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
// Extrudes along world -Y (outward) so the glyphs stay upright; starting at
// the pocket's back plane and running past the face covers the full depth.
module label_body(extra) {
    translate([0, -D/2 - plate_proud + inlay_d, plate_zc]) rotate([90, 0, 0])
        linear_extrude(inlay_d + extra) label_2d();
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
        label_body(0.5);
        brand_mark();
    }
}
module label_inlay() { label_body(0); }

if      (part == "bin")   bin();
else if (part == "label") label_inlay();
else if (part == "all") { bin(); label_inlay(); }
