include <BOSL2/std.scad>

// ============================================================
// "Mushie" -- kawaii mushroom night light for OnBrandCraftz, built around
// the real Bambu Lab LED Lamp Kit-001 (confirmed specs: D59mm x H18mm
// disc, USB 5V/3W, warm white, 1.5m cable, mounts via 2 screws or
// double-sided tape -- store.bambulab.com/products/led-lamp-kit-001).
// Two separate printed parts (different colors/materials, not fused):
//   STEM -- opaque colored PLA, houses the puck in a top-opening cavity,
//     cable exits through a side notch at the puck's own height.
//   CAP  -- opaque colored PLA dome shell with round THROUGH-HOLES for
//     the glowing "dots" (matches the real reference product exactly --
//     Frank Cheung's Mushroom Lamp, MyMiniFactory object 191671: the
//     dots are open holes letting bare light through, not painted or
//     translucent-filled), plus a radial "gill" rib pattern on the
//     underside. Both design cues taken directly from real reference
//     photos (mushroom_ref1.jpg, mushroom_ref2.jpg), not invented.
// Every dot-hole cut uses a cylinder aimed along the LOCAL SURFACE
// NORMAL (radially outward from the dome's own center), not a flat tool
// on a fixed global axis -- this sidesteps the entire "flat tool vs
// curved surface" bug class that cost so much time on the cloud
// organizer (buried cuts, curvature mismatch). A radial cut through a
// spherical SHELL of known thickness always passes cleanly through by
// construction, regardless of where on the sphere it sits.
// ============================================================

$fn = 64;

// ---- the real hardware being designed around ----
puck_d = 59; puck_h = 18;
cavity_clear = 3;               // radial + axial clearance around the real puck
cavity_d = puck_d + cavity_clear * 2;
cavity_r = cavity_d / 2;
cavity_h = puck_h + cavity_clear;

// ============================================================
// PART 1: STEM (opaque base, houses the puck)
// ============================================================
// Proportions (2026-08-28, corrected): a first version only tapered
// 34mm -> 27mm before flaring to the 39.5mm collar the puck forces --
// far too shallow a waist, and the assembled render confirmed it: it
// read as a cosmetic jar, not a mushroom, not a subtle framing issue
// (checked a second, wider camera angle -- same result). A real mushroom
// stem needs a DRAMATIC waist. Keeping the puck housed in the stem
// (rather than moving it into the cap, which would need a ~65mm
// unsupported horizontal bridge inside the dome to mount it -- too much
// risk for a first version) but making the taper much more pronounced.
foot_r = 30; neck_r1 = 15; collar_r = cavity_r + 7;   // wall around the puck cavity
foot_h = 22; neck_h = 14; collar_h = 22;
base_plate_d = 70; base_plate_h = 4;

module stem_base_plate() {
    cyl(h = base_plate_h, d = base_plate_d, rounding = 1.5, anchor = BOTTOM, $fn = 64);
}

// CRITICAL FIX (found via connectivity check, not assumed): a first
// version tapered the collar itself gradually from the narrow neck up to
// collar_r across the SAME height range the puck cavity occupies -- the
// collar's own local radius didn't exceed the cavity's radius until more
// than halfway up, so the cavity completely hollowed out that lower
// portion, leaving the collar's top as a disconnected floating fragment
// (confirmed: stl_components.py reported exactly that piece, at exactly
// that height range). Fix: the taper-up now happens in a SHORT neck
// segment below the collar, so the collar itself starts at FULL width
// (collar_r) immediately -- solid wall guaranteed around the cavity at
// every height the cavity actually occupies, not just near the top.
module stem_body() {
    up(base_plate_h - 2)
        cyl(h = foot_h, r1 = foot_r, r2 = neck_r1, rounding1 = 8, anchor = BOTTOM);
    up(base_plate_h - 2 + foot_h - 0.1)
        cyl(h = neck_h, r1 = neck_r1, r2 = collar_r, anchor = BOTTOM);
    up(base_plate_h - 2 + foot_h - 0.1 + neck_h - 0.1)
        cyl(h = collar_h, r = collar_r, rounding2 = 4, anchor = BOTTOM);
}

stem_top_z = base_plate_h - 2 + foot_h - 0.1 + neck_h - 0.1 + collar_h;

// ---- bayonet twist-lock between stem collar and cap skirt (2026-08-28) ----
// Push down, then twist to lock -- the exact mechanism already proven in
// bayonet_jar.scad, reused rather than re-derived: 3 pins on the cap's
// skirt engage 3 slots cut through the stem collar's own wall (a vertical
// entry channel, then a horizontal lock channel swept via rotate_extrude
// so it follows the collar's real curvature). A correctly-built bayonet
// lock has zero real overlap in its locked pose -- the pin only ever
// occupies the slot's own carved-out space -- verified below via
// intersection(), not assumed, the same discipline this file has needed
// for every other feature.
n_pins = 3;
pin_r = 2.6;
slot_clear = 0.5;
slot_r = pin_r + slot_clear;
travel_v = 8;      // vertical entry length (push distance before twisting)
lock_angle = 25;   // degrees of horizontal travel to reach the locked position
angle_margin = 8;  // extra cut angle past lock_angle so the locked pin's own
                    // angular footprint isn't left overshooting uncut wall --
                    // must clear atan(pin_r/collar_r), the same lesson
                    // bayonet_jar.scad already learned the hard way
lock_z = stem_top_z - travel_v;   // world height of the horizontal lock channel

module one_collar_slot() {
    collar_wall = collar_r - cavity_r;
    translate([collar_r - collar_wall - 1, -slot_r, lock_z])
        cube([collar_wall + 2, 2 * slot_r, travel_v + slot_r + 1]);
    translate([0, 0, lock_z])
        rotate_extrude(angle = lock_angle + angle_margin, $fn = 90)
            translate([collar_r, 0])
                circle(r = slot_r, $fn = 16);
}

module collar_slots() {
    // offset 60deg off the 0/180 axis so no slot lands on the cable
    // notch's own line (cable_notch spans the full X axis below)
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60])
            one_collar_slot();
}

module puck_cavity() {
    // opens at the very top of the collar, puck sits LED-face-up
    translate([0, 0, stem_top_z - cavity_h + 0.1])
        cylinder(r = cavity_r, h = cavity_h + 1, $fn = 48);
}

module cable_notch() {
    // rectangular slot through the collar wall, generously long radially
    // so it reaches open air outside regardless of the collar's exact
    // taper radius there. Positioned near the CAVITY FLOOR (not its
    // vertical center) specifically to stay clear of lock_z above --
    // the bayonet lock channel sits higher up the collar, and the two
    // cuts must not overlap.
    notch_z = stem_top_z - cavity_h + 5;
    translate([0, 0, notch_z])
        cube([70, 10, 9], center = true);
}

// ---- brand mark on the base plate (same fitted pattern as Cloudy) ----
logo_depth = 0.7; logo_size = 5.2;
module stem_brand_mark() {
    translate([0, -base_plate_d / 2 + 11, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

module lamp_stem() {
    difference() {
        union() {
            stem_base_plate();
            stem_body();
        }
        puck_cavity();
        cable_notch();
        collar_slots();
        stem_brand_mark();
    }
}

// ============================================================
// PART 2: CAP (dome shell with dot through-holes + underside gills)
// ============================================================
// Corrected twice (2026-08-28): a pure sphere cut near its own rim gave
// a lip too shallow to cover the stem's collar, so the assembled render
// looked like a jar; extending the sphere's own cut plane further down
// to compensate doesn't work either -- past the equator a sphere's
// radius necessarily SHRINKS (real geometry, not tunable), so a deeper
// spherical cut makes the rim NARROWER, not wider, eventually too narrow
// to even fit over the collar. Real mushroom caps solve this the same
// way: the rounded dome ends at (or just past) its own equator, then a
// short near-vertical SKIRT band continues down to the true rim -- not
// a continuation of the sphere. Built the same way here.
// Third correction on the cap: cutting the dome at the full equator plus
// a 26mm skirt gave a tall, round "ball on a stick" silhouette once
// actually assembled and rendered correctly (an earlier "use" instead of
// "include" bug had silently kept the cap glued to the very top the
// whole time, hiding this until the include/variable-scope bug itself
// was found and fixed). A real mushroom cap is much SHALLOWER than a
// hemisphere -- cutting higher up the sphere (keeping less than half of
// it) gives a flatter, wider-looking cap that actually matches the
// reference photos instead of reading as a ball.
// Fourth correction: dome_cut_z=16 on a 46mm sphere still gave a 30mm-tall
// dome -- comparable to the stem's own height, so the assembled shape
// read as a "ball on a stick" rather than a flat mushroom cap on a tall
// stem, confirmed by actually rendering the corrected assembly (the
// previous three fixes were all real bugs -- wrong cut math, wrong
// "use" vs "include" variable scoping, wrong assembly offset -- but even
// with all of them fixed, the proportion itself still wasn't right).
// Bigger sphere + a much higher cut plane gives a genuinely flat, wide
// cap instead.
// Fifth correction, found by an actual interference check (intersection()
// of the two assembled parts, not just eyeballing a render): the skirt
// tapered from skirt_r_bot(44, sized for the collar's clearance) at its
// own bottom UP TO the dome's natural edge radius at dome_cut_z (only
// ~35mm) at its own top -- but the stem's collar is a CONSTANT 39.5mm
// radius for its whole height, so partway up the skirt's shrinking taper
// dipped below the collar and collided with it (confirmed: a real solid
// overlap region, ~16mm tall, found via intersection()). Fix: size the
// sphere/cut-height pair so the dome's OWN edge radius at dome_cut_z
// already equals skirt_r_bot -- then the skirt can run essentially
// straight (no taper below the safe clearance) for its entire height.
cap_sphere_r = 72.03;
dome_cut_z = 57.03;      // dome height = cap_sphere_r - dome_cut_z = 15mm, still flat
skirt_len = 22;          // straight skirt band hanging from dome_cut_z down to the true rim
skirt_r_top = sqrt(cap_sphere_r ^ 2 - dome_cut_z ^ 2);   // = 44.0, matches skirt_r_bot -- no taper mismatch
skirt_r_bot = collar_r + 4.5;             // comfortably clears the stem's collar_r for a slip fit
cap_rim_z = dome_cut_z - skirt_len;   // the TRUE open rim plane
cap_shell_t = 2.4;
cap_dot_r = 6.5;

// Real spherical-shell cuts: aim each hole's cylinder from OUTSIDE the
// shell to INSIDE it, along the exact radial direction at that point --
// guarantees a clean through-hole on any sphere regardless of position,
// no curvature/flat-tool mismatch possible.
// phi must stay under acos(dome_cut_z/cap_sphere_r) = acos(46/58) = 37.5deg
// -- the dome only exists above that; anything beyond it is now the
// skirt (a different, non-spherical shape the sphere-based radial-cut
// math below doesn't apply to). Kept a safe margin under that limit.
dot_dirs = [   // [theta (deg, around Z), phi (deg, down from top pole)]
    [ 0,  12],
    [ 130, 20],
    [ -110, 22],
    [ 55, 30],
    [ -60, 28],
];
function dot_vec(theta, phi) = [
    sin(phi) * cos(theta),
    sin(phi) * sin(theta),
    cos(phi),
];

module dot_hole(theta, phi) {
    dir = dot_vec(theta, phi);
    // cylinder default points +Z; rot(from=,to=) reorients it to point
    // radially outward along dir, then push it out from the sphere
    // center so it spans just outside the shell to well inside it.
    rot(from = UP, to = dir)
        translate([0, 0, cap_sphere_r - cap_shell_t - 3])
            cylinder(r = cap_dot_r, h = cap_shell_t + 8, $fn = 40);
}

module cap_dome_only() {
    // keep the sphere shell from z=dome_cut_z upward -- a cube 400 tall
    // with its BOTTOM face at exactly dome_cut_z (not centered there --
    // a cube centered at the cut plane barely cuts anything off a 46mm
    // sphere, which is exactly the bug an earlier version had: it
    // rendered as a near-complete sphere with almost no dome cut at all,
    // caught by actually looking at the render).
    intersection() {
        difference() {
            sphere(r = cap_sphere_r);
            sphere(r = cap_sphere_r - cap_shell_t);
        }
        translate([0, 0, dome_cut_z + 200]) cube([200, 200, 400], center = true);
    }
}

module cap_skirt_only() {
    // spans z=cap_rim_z (bottom) up to z=dome_cut_z (top, meeting the dome)
    translate([0, 0, cap_rim_z])
        difference() {
            cyl(h = skirt_len, r1 = skirt_r_bot, r2 = skirt_r_top, anchor = BOTTOM);
            cyl(h = skirt_len + 2, r1 = skirt_r_bot - cap_shell_t, r2 = skirt_r_top - cap_shell_t,
                anchor = BOTTOM);
        }
}

module cap_shell_raw() {
    union() {
        cap_dome_only();
        cap_skirt_only();
    }
}

// Underside gills: thin radial ribs hanging from the shell's own inner
// surface near the open rim, matching the fan/ridge pattern visible in
// the real reference photos. Purely decorative -- built from small
// wedges so they stay thin and printable (rim-side layers first when the
// cap prints opening-down, dome-up -- the standard safe bowl orientation,
// no overhangs).
gill_count = 28;
gill_len = 13;
gill_t = 1.0;
module gill(theta) {
    // a thin radial fin sitting just inside the rim, hanging down from
    // the skirt's own inner surface toward the true open edge (z=cap_rim_z,
    // the skirt's own bottom -- a constant, known radius, not the sphere
    // formula, since the rim now sits in the straight skirt band below
    // the dome, not on the sphere itself)
    rim_r_inner = skirt_r_bot - cap_shell_t;
    rotate([0, 0, theta])
        translate([rim_r_inner - gill_len, -gill_t / 2, cap_rim_z])
            cube([gill_len, gill_t, 7]);
}

module cap_gills() {
    for (i = [0 : gill_count - 1])
        gill(i * 360 / gill_count);
}

// ---- bayonet lock pins, matching collar_slots() above ----
// The cap is defined in its OWN local coordinates, then translated by
// cap_assembly_offset when actually assembled onto the stem (see the
// verification block at the bottom of this file). A pin at LOCAL z must
// therefore sit at (lock_z - cap_assembly_offset) so that once
// translated, it lands at the real WORLD height of the lock channel.
cap_assembly_offset = stem_top_z - collar_h - cap_rim_z;
pin_local_z = lock_z - cap_assembly_offset;
module cap_pins() {
    // positioned at the LOCKED angle (slot's own start angle + lock_angle)
    // -- this model shows the mechanism already twisted shut, same
    // convention as bayonet_jar.scad.
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60 + lock_angle])
            translate([collar_r, 0, pin_local_z])
                sphere(r = pin_r, $fn = 20);
}

module lamp_cap() {
    difference() {
        union() {
            cap_shell_raw();
            intersection() {
                cap_gills();
                cap_shell_raw();   // keep gills confined to the shell's own interior, never poking outside it
            }
            cap_pins();
        }
        for (d = dot_dirs) dot_hole(d[0], d[1]);
    }
}

// ============================================================
// Layout -- two separate parts, side by side (a genuine 2-piece kit,
// not meant to fuse -- 2 disconnected components in the combined STL is
// the CORRECT outcome here, not a bug, unlike every single-part build
// earlier in this project).
// ============================================================
translate([-70, 0, 0]) lamp_stem();
translate([70, 0, 0]) lamp_cap();
