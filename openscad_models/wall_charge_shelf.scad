// Wall charging shelf -- a phone shelf that mounts below a wall outlet.
//
// MOUNTING IS SCREWS, DELIBERATELY. Two keyhole slots for #6/#8 screws into
// studs or drywall anchors, plus one anti-lift screw at the bottom. The pitch
// for this design said "screw-to-wall or command-strip"; the adhesive half of
// that is withdrawn on purpose. A 65mm cantilever holding a phone loads an
// adhesive strip in PEEL at its top edge, which is the one direction those
// strips are worst at and which 3M's own guidance excludes shelves for. A
// mounting method that fails slowly and drops a phone is not something to
// ship to strangers. Likewise the shelf does NOT hang on the outlet's cover
// screw -- outlet plates vary and that screw holds a live electrical fixture.
//
// PRINTS BACK-FLAT, no supports. The back plate lies on the bed and the shelf
// grows upward, so world +Z here is DEPTH OUT FROM THE WALL and is also the
// build direction. Everything below is reasoned in that frame:
//
//     world X = along the wall (width)      -- a bed axis
//     world Y = up the wall (height)        -- a bed axis
//     world Z = out from the wall (depth)   -- the BUILD axis
//
// That orientation is what makes the whole thing support-free: the deck, the
// side panels and the back plate are all walls standing on the bed, and the
// bracket's concave free edge rises monotonically in Z, so its face is
// up-facing everywhere (see panel_2d). Only two features can overhang at all,
// and both are shaped for it -- the front lip's underside is a 39 deg ramp,
// and the deck's plug slot has a 45 deg peaked roof instead of a flat bridge.

$fa = 2;  $fs = 0.4;

part = "shelf";             // shelf | plate | panel | deck

// ---- overall ------------------------------------------------------------
W   = 120;                  // along the wall
H   = 90;                   // up the wall (back plate)
Dp  = 65;                   // out from the wall (deck depth)

plate_t = 2.52;             // 6 x 0.42. Whole extrusions, per the label bin's
deck_t  = 2.94;             // 7 -- a 1.6mm wall left 0.34mm of slow gap-fill
panel_t = 3.36;             // 8    and sliced 48 MINUTES slower on LESS material.

deck_y  = 0;                // deck TOP surface -- the datum everything hangs off
deck_b  = deck_y - deck_t;
plate_lo = -H/2;            // -45
plate_hi =  H/2;            //  45

rail_h  = 8;                // side rails and front lip, above the deck
lip_run = 10;               // ramp length, in depth, under the front lip.
                            // 8 up over 10 out = 38.7 deg from vertical in the
                            // print. The obvious lip (thin slab, 3mm of depth)
                            // would be a 73 deg overhang -- the ramp is not
                            // decoration, it is the only reason this prints.

corner_r = 6;
brd_p    = 3.36;            // solid frame left around the plate lattice
brd_s    = 2.52;            // and around the panel lattice (6 x 0.42) -- the
                            // panel has far less area to spend on a frame

// ---- lattice ------------------------------------------------------------
// Technique 46, rule 4: a bracket gusset is never a solid flat triangle --
// either taper the web to the load path or through-cut it as a hex lattice
// inside a solid perimeter frame. The load here is distributed along the deck
// and the bracket is meant to be seen, so this is the lattice version.
//
// The two lattices are NOT the same cell and that is on purpose. The back
// plate's cells are cut along the build axis, so they are plain vertical
// holes and can be regular hexagons. The side panels' cells are cut ACROSS
// the build axis, so each cell's roof is a real overhang: a regular pointy-up
// hexagon puts its top two edges at 60 deg from vertical, past the 55 deg the
// P1S holds. Stretching the cell along the build axis by 1.9 pulls those
// edges back to 42 deg. The two fields share a rib width and a similar
// across-flats pitch so they read as one family; you never see both from a
// single position at the wall anyway.
rib      = 1.68;            // 4 x 0.42
cellR_p  = 4.5;             // back plate, regular (no roof to worry about)
cellR_s  = 3.8;             // side panels
lat_cham = 0.6;             // lead-in on the plate lattice's room-facing face
stretch  = 1.5;             // along the build axis, panels only. Sized to the
                            // real 55 deg limit with margin, not to 45: 1.5
                            // puts the cell roof at 49.1 deg (measured) and
                            // keeps the cell at 1.7:1 instead of the 2.2:1 that
                            // a 1.9 stretch produced, which read as squashed.

// ---- mounting -----------------------------------------------------------
// Keyhole: a Ø9 slot recessed from the WALL side takes the screw head, a Ø4.6
// slot through a 2.8mm front skin takes the shank, and the step between them
// is a 45 deg cone instead of a flat ledge so the transition needs no bridge.
// The bosses stand proud on the FRONT only -- the back face stays dead flat
// against the wall.
boss_w   = 22;  boss_h = 30;  boss_t = 6.0;
boss_cy  = 29;              // boss spans y 14..44 -- inside the 45 plate edge
key_x    = 38;  key_y  = 34;    // y of the round (head) end of the keyhole
key_head = 9.0;             // screw head clearance
key_shaft= 4.6;             // #6/#8 shank clearance
key_drop = 9;               // how far the shelf drops onto the screws
key_deep = 3.2;             // head recess from the wall face -> 2.8mm of skin
                            // left in front for the head to bear on

foot_w   = 24;  foot_t = 5.0;   foot_y = -32;   // anti-lift screw at the bottom

// ---- deck plug slot ------------------------------------------------------
// A charging plug on a phone's bottom port has to pass THROUGH the deck. The
// slot's far end is a 45 deg peak, not a flat roof: in this orientation the
// far end is the top of a 24mm horizontal hole, and a flat one would be a
// 24mm bridge.
slot_w  = 24;
slot_z0 = 8;                // keep the deck's root at the wall intact -- that
slot_z1 = 32;               // is where the bending moment is highest
slot_r  = 3;

// ---- phone toe stops -----------------------------------------------------
// Two low pads the phone's bottom edge sits behind, so it is CAPTURED between
// them and the backrest instead of merely balanced against it. A standing
// phone on a vertical backrest cannot be raked backwards -- its back is
// already flush against the wall plane, there is nothing to lean into -- so
// the fix is not a rake, it is a stop. With the pads at z=22 the phone's base
// sits about 16mm out and its back rests on the mounting bosses, which stand
// 3.48mm proud: a bare ~10mm phone ends up about 7 deg off vertical, a thick
// cased one about 2 deg, and neither can tip forward.
//
// Two pads, not one ridge across the deck: they sit OUTBOARD of the plug slot
// in x, so the slot keeps its full length and the middle of the tray stays
// flat. A phone spans about +/-37mm and lands on both.
//
// The low-z face is a 48 deg ramp, not a wall. It is the print's only
// downward-facing surface here, and it doubles as the stop -- the phone's
// bottom edge butts into it.
toe_x    = 28;
toe_len  = 24;
toe_h    = 4;
toe_z    = 22;              // the stop line: phone base sits behind this
toe_ramp = 4;

module toe_stops() {
    for (sx = [-1, 1])
        translate([sx * toe_x + toe_len/2, 0, 0]) extrude_zy(toe_len)
            polygon([[toe_z - toe_ramp, -0.5], [toe_z, toe_h],
                     [toe_z + 4, toe_h], [toe_z + 4, -0.5]]);
}

// ---- maker's mark --------------------------------------------------------
// Front face of the lip, which is the TOP surface as printed -- the crispest
// engraving this part can carry, and the face you actually look at on a wall.
// Sized to the 10.94mm face rather than 40% of the 120mm run: the face's short
// dimension binds first, and 40% of 120 would need an 11mm cap height that
// does not fit. Measured 2.27mm / 5.39 extrusions on the thinnest stroke.
mark_size = 7.0;
mark_deep = 0.6;

// Shared geometry -- extrude helpers, polygon predicates and the whole-cell
// hex lattice -- lives in lattice_lib.scad, which the outlet shelf also uses.
// It must be included BEFORE this file's own parameters: include<> inlines,
// and last assignment wins, so an override placed above it silently loses.
include <lattice_lib.scad>

// =========================================================================
// back plate  (2D in world X,Y -- extruded along the build axis)
// =========================================================================
module plate_2d() { offset(r = corner_r) square([W - 2*corner_r, H - 2*corner_r], center = true); }

module boss_2d(x, y, w, h) { translate([x, y]) offset(r = 4) square([w - 8, h - 8], center = true); }

module bosses_2d() {
    boss_2d(-key_x, boss_cy, boss_w, boss_h);
    boss_2d( key_x, boss_cy, boss_w, boss_h);
}

// What the lattice must stay clear of: the plate's own outline, the band
// around the deck junction (that is where the deck's moment lands), and each
// mounting boss.
function plate_keepouts() = [
    rect_pts(0, -1.5, W + 2, 13),
    rect_pts(-key_x, boss_cy, boss_w, boss_h),
    rect_pts( key_x, boss_cy, boss_w, boss_h),
    rect_pts(0, foot_y, foot_w, foot_w)];

module back_plate() {
    difference() {
        union() {
            linear_extrude(plate_t) plate_2d();
            linear_extrude(boss_t)  bosses_2d();
            linear_extrude(foot_t)  boss_2d(0, foot_y, foot_w, foot_w);
        }
        lattice_cut(rrect_pts(W, H, corner_r), plate_keepouts(),
                    cellR_p, 1, brd_p, rib, plate_t, lat_cham);
    }
}

// =========================================================================
// side panel  (2D in world Z,Y -- one continuous wall: rail on top, bracket
// below, concave free edge)
// =========================================================================
// The free edge is a circular arc sagging INWARD from the chord between the
// bottom of the back plate and the front of the deck. It stays monotonic in
// both axes, so its surface normal keeps a positive Z component the whole way
// -- an up-facing face in the print, never an overhang. A convex bulge would
// not be, which is why the sag is subtracted from the chord and not added.
arc_sag = 7;
fascia  = 2;                // the side wall returns 2mm below the deck at the
                            // front. Landing it EXACTLY on the deck's own
                            // bottom-front edge made two collinear zero-area
                            // faces there -- mesh_gate caught them; the render
                            // and the watertight check did not.
function panel_pts() = concat(
    [[0, rail_h], [Dp, rail_h], [Dp, deck_b - fascia]],
    [for (i = [1 : 24]) arc_pt(1 - i/24)],
    [[0, plate_lo]]);

function arc_pt(t) =
    let (z0 = plate_t, y0 = plate_lo, z1 = Dp, y1 = deck_b - fascia,
         mz = (z0+z1)/2, my = (y0+y1)/2,
         dz = z1-z0, dy = y1-y0, L = sqrt(dz*dz + dy*dy),
         nz = -dy/L, ny = dz/L)                       // unit normal, toward the inside corner
    [ z0 + dz*t + 4*arc_sag*t*(1-t)*nz,
      y0 + dy*t + 4*arc_sag*t*(1-t)*ny ];

module panel_2d() { polygon(panel_pts()); }

module panels() {
    for (s = [-1, 1]) translate([s > 0 ? W/2 : -W/2 + panel_t, 0, 0])
        extrude_zy(panel_t)
            difference() {
                panel_2d();
                lattice(panel_pts(), [], cellR_s, stretch, brd_s, rib, 90);
            }
}

// =========================================================================
// deck + lip
// =========================================================================
module deck_2d() { square([W, Dp], center = false); }   // drawn as (x, z)

module deck() {
    translate([-W/2, deck_b, 0]) extrude_xz(deck_t) deck_2d();
}

// slot drawn as (x, z); peak apex 45 deg so the roof of a 24mm horizontal
// hole never becomes a flat bridge
module plug_slot_2d() {
    a = slot_w / 2;
    // The whole outline is convex, so ONE hull gets it exactly: rounded bottom
    // corners, vertical sides tangent to them at x = +/-a, then the 45 deg peak.
    // Unioning a rounded rect with a separate peak does not work -- whichever
    // shape is wider at the join leaves a flat horizontal ledge there, which is
    // the flat roof the peak exists to remove, plus zero-area slivers.
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

// =========================================================================
// mounting cuts
// =========================================================================
module keyhole(x) {
    step = (key_head - key_shaft) / 2;
    translate([x, 0, 0]) {
        // head recess, open to the bed
        translate([0, 0, -0.5]) linear_extrude(key_deep + 0.5)
            slot2d(0, key_y, 0, key_y - key_drop, key_head);
        // 45 deg loft up to the shank slot instead of a flat annular ledge
        hull() {
            translate([0, 0, key_deep]) linear_extrude(0.01)
                slot2d(0, key_y, 0, key_y - key_drop, key_head);
            translate([0, 0, key_deep + step]) linear_extrude(0.01)
                slot2d(0, key_y, 0, key_y - key_drop, key_shaft);
        }
        translate([0, 0, -1]) linear_extrude(boss_t + 2)
            slot2d(0, key_y, 0, key_y - key_drop, key_shaft);
    }
}

module foot_hole() {
    translate([0, foot_y, -1]) cylinder(h = foot_t + 2, d = key_shaft);
    // countersink opens upward -> an up-facing cone, no overhang
    translate([0, foot_y, foot_t - 2.45])
        cylinder(h = 2.45, d1 = key_shaft, d2 = key_shaft + 4.9);
}

module brand_mark() {
    translate([0, deck_y + rail_h/2 - 1.2, Dp - mark_deep]) linear_extrude(mark_deep + 1)
        text("OBC", size = mark_size, font = "Montserrat:style=Black",
             halign = "center", valign = "center");
}

// =========================================================================
// ORDER MATTERS. Every solid is unioned before any cut is taken, and no
// solid is added after -- the drawer module and the label bin both lost
// features to unioning them after the cavity was cut, and both still
// rendered and still gated watertight.
// =========================================================================
module shelf() {
    difference() {
        union() { back_plate(); deck(); panels(); front_lip(); toe_stops(); }
        plug_slot();
        keyhole(-key_x);
        keyhole( key_x);
        foot_hole();
        brand_mark();
    }
}

if      (part == "plate") back_plate();
else if (part == "panel") panels();
else if (part == "deck")  deck();
else                      shelf();
