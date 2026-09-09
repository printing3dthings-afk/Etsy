include <BOSL2/std.scad>

// ============================================================
// Bayonet twist-lock storage jar -- base + lid.
//
// v2 (2026-09-09), after Scott printed v1 and reported three real
// defects. Each fix below is anchored to the measurement that proved
// the defect, not to a guess:
//
//  1. "The bottom part where the lid locks is pretty flimsy."
//     The lock channel spanned r 22.5..27.5 through a wall spanning
//     22.6..25 -- a THROUGH-CUT. The neck was severed circumferentially
//     over 3 x 33 deg and held together only by the thin webs between
//     slots. Fixed with an internal collar (see collar_r_in): the lock
//     features are now grooves with 1.75mm (4.2 extrusions) of material
//     behind them, and the collar itself is an uncut 360 deg hoop.
//
//  2. "The lid rattles when locked."
//     Nothing seated. The lid cap underside sat 7mm ABOVE the jar rim;
//     the whole lid hung on 3 spheres in oversized channels. Fixed two
//     ways: lid_skirt_h is now DERIVED so the cap lands flat on the rim,
//     and the lock channel descends ramp_drop over lock_angle so
//     twisting pulls the lid down onto that seat and preloads it.
//
//  3. "The tolerances also need to be slightly tight."
//     Split into two numbers instead of one, because the two interfaces
//     want opposite things: the vertical entry only has to accept the
//     pin (loose, entry_clear) while the lock channel carries the load
//     and sets the rattle (tight, lock_clear).
//
//  4. "Make the brand the OBC due to size restrictions."
//     v1's "OnBrandCraftz" in Dancing Script at 1.8 measured 0.0mm
//     typical stroke with 100% of the glyph lost to a single bead --
//     it could not print at all, at any depth. "OBC" in Montserrat
//     Black at 6.0 measures 1.66mm = 3.95 extrusions, 0.09% lost.
//     Verify with: python3 tools/glyph_probe.py "OBC" --font
//     "Montserrat:style=Black" --size 6
// ============================================================

part = "all";   // "all" | "base" | "lid"   (-D part=\"base\")

base_r = 25;
base_h = 45;
wall   = 2.4;
floor  = 3;

n_pins = 3;
pin_r  = 2.0;

// Two clearances, deliberately different -- see note 3 above.
lock_clear  = 0.25;   // load-bearing, sets the rattle. Tighter than the
                      // 0.40 proven for a CONTINUOUSLY rotating hinge,
                      // which is affordable here: this is a sphere in a
                      // round channel making one 25 deg turn, and the
                      // sphere self-centres.
entry_clear = 0.45;   // drop-in only, nothing locks here. Kept loose so
                      // a slightly undersized printed bore can never
                      // stop the lid going on.
lock_r  = pin_r + lock_clear;    // 2.25
entry_r = pin_r + entry_clear;   // 2.45

travel_v      = 8;    // push distance before twisting
lock_angle    = 25;   // twist to reach locked
slot_top_z    = base_h;
slot_bottom_z = base_h - travel_v;   // channel height at the entry (angle 0)

// Channel descends toward the locked end so the twist DRAGS the lid down
// onto the rim. 0.25 of this takes up the pin's own vertical slop
// (lock_r - pin_r); the remaining 0.10 is real preload held by flex in
// the 2.4mm skirt. Deliberately small -- more would risk a lid that
// won't turn, or splitting the neck.
ramp_drop    = 0.35;
// + lock_clear is NOT cosmetic: it puts the pin against the channel
// CEILING at the instant the cap touches the rim, so the lid is captured
// between the two with ZERO free lift. Sitting the pin on the channel
// centreline instead (the obvious-looking choice) leaves exactly
// lock_clear of vertical play -- i.e. it still rattles, just less. Note
// this is TANGENT contact, not interference: through the twist the
// ceiling closes 0.350 -> 0.000 against a pin that never touches the
// channel floor, so the cap is drawn down and never levered back up,
// and the locked assembly still has zero solid overlap. Real
// interference here (~0.1mm across stiff PLA at three points) risks a
// lid that won't turn or a sheared pin.
pin_z_locked = slot_bottom_z - ramp_drop + lock_clear;

// Channel stops just past where the locked pin's own angular footprint
// ends (atan(pin_r/base_r) = 4.57 deg), giving a defined tactile stop
// instead of v1's 8 deg of free over-rotation.
lock_stop_margin = 6;

// ---- Internal lock collar -------------------------------------------
// Thickens the neck inward across the whole lock zone so the slots
// become grooves. Its underside is a 45 deg cone (radial step == vertical
// step) so it is self-supporting -- a flat ledge here would be a 90 deg
// overhang printing into open air.
collar_r_in = 21.0;
collar_z1   = 33.0;                                  // full thickness from here up
collar_z0   = collar_z1 - ((base_r - wall) - collar_r_in);   // taper starts here (31.4)

// ---- Base ------------------------------------------------------------

// Bore as one solid of revolution rather than stacked cylinders: no
// coplanar union seams, so no zero-area CGAL slivers.
module bore() {
    rotate_extrude($fn = 96)
        polygon([
            [0,               floor],
            [base_r - wall,   floor],
            [base_r - wall,   collar_z0],
            [collar_r_in,     collar_z1],
            [collar_r_in,     base_h + 1],
            [0,               base_h + 1],
        ]);
}

// The channel is swept by the PIN ITSELF (a sphere of lock_r), as a chain
// of hulled sphere pairs along the helix. This is exactly the pin's swept
// envelope, so clearance is lock_clear everywhere -- including at the
// ends, which a rotate_extrude cannot do and which is also why this
// isn't a union of per-angle extrudes (Technique 5: those time out).
module lock_channel() {
    a_end = lock_angle + lock_stop_margin;
    steps = 16;
    for (i = [0 : steps - 1]) {
        a0 = a_end * i / steps;
        a1 = a_end * (i + 1) / steps;
        hull() {
            rotate([0, 0, a0])
                translate([base_r, 0, slot_bottom_z - ramp_drop * a0 / lock_angle])
                    sphere(r = lock_r, $fn = 24);
            rotate([0, 0, a1])
                translate([base_r, 0, slot_bottom_z - ramp_drop * a1 / lock_angle])
                    sphere(r = lock_r, $fn = 24);
        }
    }
}

module one_slot() {
    // Vertical entry: radial box spanning only the channel's own radial
    // footprint, NOT the full collar. Cutting it deeper would slot the
    // collar three times and undo the stiffness this whole fix adds.
    translate([base_r - entry_r, -entry_r, slot_bottom_z])
        cube([2 * entry_r + 1, 2 * entry_r, travel_v + entry_r + 1]);
    lock_channel();
}

module all_slots() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins])
            one_slot();
}

logo_depth = 0.6;
logo_size  = 6.0;   // 19.1mm wide on a 50mm bottom = 38% of the flat run,
                    // inside the 35-45% maker's-mark rule.
module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OBC", size = logo_size, font = "Montserrat:style=Black",
                     halign = "center", valign = "center");
}

module base_body() {
    difference() {
        cylinder(r = base_r, h = base_h, $fn = 96);
        bore();
        all_slots();
        brand_mark();
    }
}

// ---- Lid -------------------------------------------------------------

lid_skirt_clear    = 0.25;                    // static sliding fit (0.2-0.3 band)
lid_skirt_r_in     = base_r + lid_skirt_clear;
lid_wall           = 2.4;
lid_cap_h          = 6;
lid_skirt_bottom_z = 32;                      // 5mm of skirt below the lock channel
// DERIVED, not chosen: this is what makes the cap underside land exactly
// on the jar rim. v1 hardcoded 20 here, which is why the lid floated 7mm
// clear of the rim and rattled.
lid_skirt_h        = base_h - lid_skirt_bottom_z;

module lid_pins() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + lock_angle])
            translate([base_r, 0, pin_z_locked])
                sphere(r = pin_r, $fn = 24);
}

module lid() {
    outer_r = lid_skirt_r_in + lid_wall;
    union() {
        difference() {
            translate([0, 0, lid_skirt_bottom_z])
                cylinder(r = outer_r, h = lid_skirt_h + lid_cap_h, $fn = 96);
            translate([0, 0, lid_skirt_bottom_z - 1])
                cylinder(r = lid_skirt_r_in, h = lid_skirt_h + 1, $fn = 96);
        }
        lid_pins();
    }
}

// The lid is modelled in the assembled pose (skirt down, cap up) because
// that is the pose the fit has to be correct in. It PRINTS cap-down --
// flat first layer on the plate, skirt rising as a plain tube -- so the
// exported part is flipped. Without this the exported STL asks the
// slicer to start a 20 cm2 disc in mid-air.
module lid_print_oriented() {
    translate([0, 0, lid_skirt_h + lid_cap_h])
        rotate([180, 0, 0])
            translate([0, 0, -lid_skirt_bottom_z])
                lid();
}

if (part == "base") base_body();
else if (part == "lid") lid_print_oriented();
else { base_body(); lid(); }
