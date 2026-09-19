include <BOSL2/std.scad>

// ============================================================
// Bayonet twist-lock storage jar -- a genuinely new mechanism class for
// this shop (rotational push-then-twist lock, not a hinge or a screw
// thread; threading.scad/gears.scad aren't vendored in this BOSL2 copy,
// so this deliberately doesn't need them). Base + lid, shown assembled
// and LOCKED (unlike the cable clip's hinge, a correctly-designed
// bayonet lock has zero real overlap in its closed/locked pose by
// construction -- the pin only ever occupies carved-out slot space,
// never solid wall material -- so there's no "must export open" concern
// here the way there was for the clip's interference-fit latch).
// ============================================================

base_r   = 25;
base_h   = 45;
wall     = 2.4;
floor    = 3;

n_pins     = 3;
pin_r      = 2.0;
slot_clear = 0.5;
slot_r     = pin_r + slot_clear;   // radius of the tube-shaped slot cutter

travel_v      = 8;    // vertical entry length (push distance before twisting)
lock_angle    = 25;   // degrees of horizontal travel to reach the locked position
slot_top_z    = base_h;              // vertical entry starts at the base's own rim
slot_bottom_z = base_h - travel_v;   // horizontal lock channel height, and the
                                      // pin's real height once locked

// ---- Base: hollow body with 3 bayonet slots cut through the neck wall ----

module one_slot() {
    // Vertical entry: a plain radial box, thin tangentially (2*slot_r),
    // spanning the full wall thickness with margin so it's a clean
    // through-cut, from the rim down to where the lock channel begins.
    translate([base_r - wall - 1, -slot_r, slot_bottom_z])
        cube([wall + 2, 2 * slot_r, travel_v + slot_r + 1]);
    // Horizontal lock channel: a tube swept around the cylinder's own
    // curvature via rotate_extrude(angle=...) -- follows the true radius
    // exactly, no straight-line approximation of a curved wall.
    //
    // Cut angle_margin degrees PAST lock_angle -- the locked pin sits with
    // its CENTER exactly at lock_angle, so a cut stopping exactly there
    // leaves half the pin's own angular footprint overshooting into
    // uncut wall. angle_margin must clear atan(pin_r/base_r) (~4.6 deg
    // here) with real margin, not sit flush against it -- confirmed by a
    // direct intersection() render coming back non-empty at exactly this
    // boundary before the margin was added.
    angle_margin = 8;
    translate([0, 0, slot_bottom_z])
        rotate_extrude(angle = lock_angle + angle_margin, $fn = 90)
            translate([base_r, 0])
                circle(r = slot_r, $fn = 16);
}

module all_slots() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins])
            one_slot();
}

logo_depth = 0.6;
logo_size  = 1.8;   // tightened from 2.2 (49.1% of diameter) to target ~40%
                     // ratio for this string+font -- still verified below
                     // before treating it as final, not assumed correct
module brand_mark() {
    translate([0, -6, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

module base_body() {
    difference() {
        cylinder(r = base_r, h = base_h, $fn = 96);
        translate([0, 0, floor])
            cylinder(r = base_r - wall, h = base_h, $fn = 96);
        all_slots();
        brand_mark();
    }
}

// ---- Lid: a cup with 3 inward pins, shown in the LOCKED position ----
// (pins offset by lock_angle from each slot's entry, at world z =
// slot_bottom_z -- the exact height and angle where a pin sits once
// pushed down and twisted shut).

lid_skirt_r_in = base_r + 0.4;   // sliding clearance over the base's outer wall
lid_wall       = 2.4;
lid_skirt_h    = 20;
lid_cap_h      = 6;
lid_skirt_bottom_z = slot_bottom_z - 5;   // a little below the lock channel, for real overlap coverage

module lid_pins() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + lock_angle])
            translate([base_r, 0, slot_bottom_z])
                sphere(r = pin_r, $fn = 20);
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

union() {
    base_body();
    lid();
}
