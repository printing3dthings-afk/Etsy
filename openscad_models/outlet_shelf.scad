// Outlet shelf -- replaces a receptacle's cover plate with a shelf.
//
// Same family as wall_charge_shelf.scad and prints the same way: back-flat,
// so world +Z is depth out from the wall AND the build direction, +Y is up
// the wall, +X along it. Y = 0 is the CENTRE OF THE RECEPTACLE, because every
// standard dimension below is quoted from there.
//
// ---- read this before printing one ----------------------------------------
// This replaces a listed electrical component. Two things follow from that
// and neither is negotiable:
//
// 1. MATERIAL. Real wall plates carry a UL 94 V-2 flammability rating. PLA
//    and PETG have no flame rating at all, and PLA softens around 55-60 C
//    while an outlet under sustained load runs warm -- it will creep. Print
//    this in a flame-rated filament (Bambu PC FR is UL 94 V-0, 260-280 C
//    nozzle, 90-110 C bed; the P1S is enclosed and reaches both, though 100 C
//    is the bottom of that bed range). A printed plate is not UL listed as an
//    assembly whatever it is made of, and that is worth saying out loud
//    rather than implying otherwise.
//
// 2. LOAD PATH. The cover screw is designed to retain a ~15g plastic plate,
//    not to carry a cantilever. It does not carry one here either: the back
//    of this part bears flat against the wall for 104mm below the screw, so
//    the shelf's moment resolves as a couple -- compression into the wall low
//    down, and only tension at the screw. A 300g load 40mm out works out at
//    about 1.1 N on the screw, roughly 110 grams of pull. That is the whole
//    reason the plate region runs the full standard height instead of
//    stopping at the device: the bearing area IS the structure.
//
// Dimensions are ANSI/NEMA WD-6 standard, checked against real published
// figures rather than recalled: 1-gang plate 2.75 x 4.5in, device face
// 1.31 x 2.62in, duplex openings 1-1/8 x 1-11/32in, duplex plate fixed by one
// central 6-32, Decora/GFCI plate by two 6-32 at 3-13/16in centres.

include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part   = "shelf";           // shelf | plate | panel
device = "duplex";          // duplex | decora

// ---- the standard, in mm -------------------------------------------------
PLATE_W_STD = 69.85;        // 2.75in   -- must be covered
PLATE_H_STD = 114.30;       // 4.5in    -- must be covered
DUP_OP_W    = 34.13;        // 1-11/32in
DUP_OP_H    = 28.58;        // 1-1/8in
DUP_OP_DY   = 18.98;        // socket centres, above/below plate centre
DEC_OP_W    = 33.30;        // 1.31in device face
DEC_OP_H    = 66.70;        // 2.62in
DEC_SCREW_DY = 48.42;       // 3-13/16in / 2
op_clr      = 0.4;          // never let the plate foul the device
scr_clear   = 3.8;          // #6 shank clearance
scr_head    = 7.0;          // 6-32 oval head

// ---- overall -------------------------------------------------------------
PW      = 74;               // plate zone width -- covers the 69.85 standard
W       = 120;              // shelf width
Dp      = 65;               // depth out from the wall

plate_hi = PLATE_H_STD/2;   //  57.15
plate_lo = -PLATE_H_STD/2;  // -57.15
deck_y   = -64;             // deck TOP. A compact charger in the LOWER socket
                            // reaches about y = -39, so this leaves 25mm of
                            // clear air above the deck. Anything shallower
                            // and the shelf stops being usable while the
                            // outlet is actually in use, which is the one
                            // thing this product exists to avoid.
bottom_y = -104;
flare_y  = -38;             // plate zone narrows above here. The flare has to
                            // FINISH at the rail line, not at the deck: the
                            // side rails run back to the wall, so anywhere the
                            // body is still narrowing they stick out past it
                            // with nothing behind them and bear straight on
                            // the drywall.

plate_t = 3.36;             // 8 x 0.42. Thicker than the 2.52 the wall shelf
                            // uses because the screw countersink eats 1.84mm
                            // of it and the rest has to still be a plate.
deck_t  = 2.94;
panel_t = 3.36;
rib     = 1.68;

rail_h  = 8;
lip_run = 10;
deck_b  = deck_y - deck_t;

assert(PW >= PLATE_W_STD, "plate zone too narrow to cover a standard plate");
assert(plate_hi - plate_lo >= PLATE_H_STD, "plate zone too short to cover a standard plate");
assert(deck_y < -DUP_OP_DY - DUP_OP_H/2, "deck would cover the lower socket");

// ---- lattice -------------------------------------------------------------
// The plate zone is NOT latticed. It is a cover plate; the ring left around
// the device opening is only ~20mm wide, and perforating a part whose job is
// covering an electrical box to make it 3 grams lighter is the wrong trade.
cellR_p  = 4.5;
cellR_s  = 3.8;
stretch  = 1.5;
brd_p    = 3.36;
brd_s    = 2.52;
lat_cham = 0.6;

// ---- outline -------------------------------------------------------------
function body_pts() = [
    [-PW/2, plate_hi], [ PW/2, plate_hi],
    [ PW/2, flare_y ], [ W/2, deck_y + rail_h ],
    [ W/2, bottom_y ], [-W/2, bottom_y ],
    [-W/2, deck_y + rail_h], [-PW/2, flare_y]];

module body_2d() { offset(r = 2) offset(r = -2) polygon(body_pts()); }

// ---- device opening ------------------------------------------------------
module stadium(w, h) { hull() for (s = [-1,1]) translate([s*(w-h)/2, 0]) circle(d = h); }

module device_opening_2d() {
    if (device == "duplex")
        for (s = [-1,1]) translate([0, s*DUP_OP_DY]) stadium(DUP_OP_W + op_clr, DUP_OP_H + op_clr);
    else
        offset(r = 3) square([DEC_OP_W + op_clr - 6, DEC_OP_H + op_clr - 6], center = true);
}

function screw_ys() = device == "duplex" ? [0] : [-DEC_SCREW_DY, DEC_SCREW_DY];

// Countersink opens toward the ROOM, so it is an up-facing cone in the print
// and needs no bridge. 82 deg included, which is what a 6-32 oval head wants.
module screw_holes() {
    cs = (scr_head - scr_clear) / 2 / tan(41);
    for (y = screw_ys()) translate([0, y, 0]) {
        translate([0, 0, -1]) cylinder(h = plate_t + 2, d = scr_clear);
        translate([0, 0, plate_t - cs]) cylinder(h = cs + 0.01, d1 = scr_clear, d2 = scr_head);
    }
}

// Keep the lattice off the plate zone entirely, off the deck junction, and
// clear of every screw.
function body_keepouts() = concat(
    [rect_pts(0, (plate_hi + flare_y)/2 + 6, W + 4, plate_hi - flare_y + 12),
     rect_pts(0, deck_y + 4, W + 4, 16)],
    [for (y = screw_ys()) rect_pts(0, y, 26, 26)]);

module back_plate() {
    difference() {
        linear_extrude(plate_t) body_2d();
        // NOT center=true. Centring a plate_t+2 extrude on z=0 spans -2.68
        // to +2.68, which leaves the top 0.68mm of a 3.36mm plate intact as a
        // membrane right across the device opening -- 16-22 cm2 of flat
        // 90 deg overhang that renders, gates watertight and slices.
        translate([0, 0, -1]) linear_extrude(plate_t + 2) device_opening_2d();
        screw_holes();
        lattice_cut(body_pts(), body_keepouts(), cellR_p, 1, brd_p, rib, plate_t, lat_cham);
    }
}

// ---- side panels ---------------------------------------------------------
arc_sag = 7;
fascia  = 2;
panel_foot = 2.5;           // the panels stop 2.5mm ABOVE the body's bottom
                            // edge. Landing flush on it makes the panel's
                            // boundary collinear with the plate's along
                            // y = bottom_y, and the shared edge tessellates
                            // into zero-area slivers -- the wall shelf hit the
                            // same thing at its deck's front edge. The wall
                            // shelf gets away with a flush panel only because
                            // its 6mm corner rounding pulls the plate's bottom
                            // edge inboard of the panels entirely.
function arc_pt(t) =
    let (z0 = plate_t, y0 = bottom_y + panel_foot, z1 = Dp, y1 = deck_b - fascia,
         dz = z1-z0, dy = y1-y0, L = sqrt(dz*dz + dy*dy),
         nz = -dy/L, ny = dz/L)
    [z0 + dz*t + 4*arc_sag*t*(1-t)*nz, y0 + dy*t + 4*arc_sag*t*(1-t)*ny];

function panel_pts() = concat(
    [[0, deck_y + rail_h], [Dp, deck_y + rail_h], [Dp, deck_b - fascia]],
    [for (i = [1 : 24]) arc_pt(1 - i/24)],
    [[0, bottom_y + panel_foot]]);

module panels() {
    for (s = [-1, 1]) translate([s > 0 ? W/2 : -W/2 + panel_t, 0, 0])
        extrude_zy(panel_t)
            difference() {
                polygon(panel_pts());
                lattice(panel_pts(), [], cellR_s, stretch, brd_s, rib, 90);
            }
}

// ---- deck, lip, cable slot, toe stops ------------------------------------
slot_w = 24;  slot_z0 = 8;  slot_z1 = 32;  slot_r = 3;
toe_x  = 28;  toe_len = 24; toe_h = 4;  toe_z = 22;  toe_ramp = 4;

module deck() { translate([-W/2, deck_b, 0]) extrude_xz(deck_t) square([W, Dp]); }

module plug_slot_2d() {
    a = slot_w / 2;
    hull() {
        translate([-(a - slot_r), slot_z0 + slot_r]) circle(r = slot_r);
        translate([  a - slot_r,  slot_z0 + slot_r]) circle(r = slot_r);
        polygon([[-a, slot_z1], [a, slot_z1], [0, slot_z1 + a]]);
    }
}
module plug_slot() { translate([0, deck_b - 1, 0]) extrude_xz(deck_t + 2) plug_slot_2d(); }

module front_lip() {
    translate([W/2, 0, 0]) rotate([0, -90, 0]) linear_extrude(W)
        polygon([[Dp - lip_run, deck_y], [Dp, deck_y], [Dp, deck_y + rail_h]]);
}

module toe_stops() {
    for (sx = [-1, 1])
        translate([sx * toe_x + toe_len/2, 0, 0]) extrude_zy(toe_len)
            polygon([[toe_z - toe_ramp, deck_y - 0.5], [toe_z, deck_y + toe_h],
                     [toe_z + 4, deck_y + toe_h], [toe_z + 4, deck_y - 0.5]]);
}

mark_size = 7.0;
mark_deep = 0.6;
module brand_mark() {
    translate([0, deck_y + rail_h/2 - 1.2, Dp - mark_deep]) linear_extrude(mark_deep + 1)
        text("OBC", size = mark_size, font = "Montserrat:style=Black",
             halign = "center", valign = "center");
}

// Every solid unioned before any cut, nothing added after.
module shelf() {
    difference() {
        union() { back_plate(); deck(); panels(); front_lip(); toe_stops(); }
        plug_slot();
        brand_mark();
    }
}

if      (part == "plate") back_plate();
else if (part == "panel") panels();
else                      shelf();
