include <BOSL2/std.scad>

/* ============================================================
   OB-CLIP-01 -- print-in-place hinged cable clip
   Base + hinged lid fully enclose a cable channel; a friction
   peg/socket latch (front) holds the lid shut, a print-in-place
   barrel hinge (back, Technique 22) lets it swing open, and two
   screw-mount ears (one at each end) let it be fixed to a
   desk/wall. Prints already assembled -- no post-print parts to
   snap together besides the hinge/latch, which are already
   interlocked in the same print.
   ============================================================ */

// ---- cable + channel ----
cable_d    = 6.0;                      // target cable diameter (generic USB/charge cable)
clearance  = 0.35;                     // radial clearance around the cable
channel_r  = cable_d / 2 + clearance;  // 3.35

// ---- body ----
clip_len   = 26;                        // length of the enclosed channel (X)
wall       = 2.4;                       // front-band wall + floor/ceiling thickness
back_wall  = 6.0;                       // back-band wall -- MUST be big enough that the
                                         // hinge's clearance channel (radius knuckle_r +
                                         // hinge_clear, see below) doesn't bleed into the
                                         // cable channel's own bore. A first version used
                                         // the same 2.4mm on both bands and the two voids
                                         // overlapped by ~1mm -- caught only by comparing
                                         // the two channels' real Y-extents on paper, not
                                         // by rendering (the render looked completely fine;
                                         // CGAL just quietly merged the two voids).
base_depth = channel_r * 2 + wall + back_wall;  // Y depth of the channel-bearing section
base_h     = channel_r + wall;          // base slab height, floor -> channel centerline
lid_h      = channel_r + wall;          // lid slab height, channel centerline -> top
corner_r   = 1.5;                       // cosmetic vertical-edge rounding (edges="Z" only)

// ---- mounting ears (screw-down, one at each end) ----
ear_w        = 10;
screw_d      = 3.6;                     // M3 clearance hole
screw_head_d = 6.6;                     // countersink diameter (flat-head M3)
screw_head_h = 1.8;                     // countersink depth
total_len    = clip_len + ear_w * 2;

// ---- print-in-place barrel hinge (back edge, y = base_depth), Technique 22 ----
pin_r       = 1.5;
hinge_clear = 0.4;
knuckle_r   = 3.0;
slot_len    = 4;
slot_gap    = 0.4;
pitch       = slot_len + slot_gap;
n_slots     = 5;                        // 3 fixed to base (even idx), 2 to lid (odd idx)
hinge_span  = n_slots * pitch - slot_gap;   // 21.6 -- MUST stay well under clip_len (26)
                                             // so the back-band recess (below) has real
                                             // margin on both sides of the hinge to cut --
                                             // a first version used slot_len=5 (span 26.6,
                                             // LARGER than clip_len) which silently zeroed
                                             // out BOTH recess pieces and welded base+lid
                                             // solid across the whole back band. Caught by
                                             // a real connected-component check, not the
                                             // (clean, error-free) render.
hinge_x0    = ear_w + (clip_len - hinge_span) / 2;
pocket_r    = knuckle_r + hinge_clear;      // radius of the clearance channel cut into
                                             // base for the whole hinge span (below)

// ---- friction peg/socket latch (front edge, y = 0) ----
latch_peg_r   = 1.6;
latch_fit     = 0.15;                   // socket radius = peg radius + latch_fit -- light push-fit
latch_peg_len = 3.0;
latch_x       = ear_w + clip_len / 2;

// ---- air-gap recess so base/lid don't weld flat everywhere they touch ----
// (see Technique 20 -- two solids sharing a flat coincident face fuse solid
// on union(); only the hinge knuckles and the latch peg should bridge it)
air_gap = 0.4;
recess_margin = 0.6;   // rod-channel span extension only (see lid_hinge_clearance())
pocket_margin = 0.15;  // per-slot pocket window margin -- MUST stay well under
                        // slot_gap (0.4) or one slot's pocket bleeds into the
                        // NEXT slot's own x-range. A first version reused
                        // recess_margin (0.6) here too -- collar 0's pocket
                        // window [hinge_x0-0.6, hinge_x0+slot_len+0.6] then
                        // reached to x=16.8, INSIDE sleeve 1's own span
                        // [16.6,20.6], leaving that 0.2mm sliver of the
                        // sleeve sitting in an oversized void with an
                        // inconsistent boolean boundary against the
                        // adjacent pocket cut -- caught only by a
                        // ray-casting point-in-mesh check, not by any
                        // render or connected-component count.

// ---- maker's mark (bottom face, standing rule 2026-08-27) ----
mark_depth = 0.6;

module a_shaft(len) {
    // Technique 22 -- continuous thin rod + fat collars at EVEN slots. Fused
    // to BASE. The rod runs the full hinge span unbroken (including through
    // the sleeve-clearance pockets base_hinge_clearance() cuts at ODD
    // slots) -- it stays structurally connected to base via the collars at
    // EVEN slots, exactly like Technique 22's original design.
    rotate([0, 90, 0]) cylinder(r = pin_r, h = len, $fn = 24);
    for (i = [0 : 2 : n_slots - 1])
        translate([i * pitch, 0, 0])
            rotate([0, 90, 0]) cylinder(r = knuckle_r, h = slot_len, $fn = 28);
}

module b_sleeves() {
    // Technique 22 -- hollow tubes riding the thin rod at ODD slots. Fused to LID.
    //
    // The bore is shifted along Z -- its OWN length axis BEFORE the
    // rotate([0,90,0]) below -- by +slot_len/2, so its span [-(slot_len+1)/2,
    // +(slot_len+1)/2] (from center=true) becomes [-0.5, slot_len+0.5],
    // aligned with the un-centered outer tube's own [0,slot_len] span (with
    // 0.5mm clearance past each end for a clean through-cut).
    //
    // A first attempt shifted along LOCAL X instead of Z -- easy mistake:
    // a bare cylinder()'s own length axis is Z (radial in X/Y) BEFORE any
    // rotate, so translate([-0.5,0,0]) shifts it RADIALLY, not along its
    // length. rotate([0,90,0]) maps local (x,y,z) -> world (z,y,-x), so
    // that radial X-shift of -0.5 became a WORLD Z-shift of +0.5 -- moving
    // the whole bore 0.5mm off the hinge axis instead of realigning it
    // along X. This produced a bore that looked "roughly right" in every
    // render (same radius, same rough location) but was actually centered
    // 0.5mm above the hinge axis -- confirmed only by solving the exact
    // circumcircle of a suspicious vertex cluster from a ray-casting
    // point-in-mesh check, not by any visual inspection.
    for (i = [1 : 2 : n_slots - 1])
        translate([i * pitch, 0, 0])
            rotate([0, 90, 0])
                difference() {
                    cylinder(r = knuckle_r, h = slot_len, $fn = 28);
                    translate([0, 0, slot_len / 2])
                        cylinder(r = pin_r + hinge_clear, h = slot_len + 1, center = true, $fn = 24);
                }
}

module base_hinge_clearance() {
    // Deep pocket_r clearance, ONLY at ODD-slot (sleeve) x-positions -- so
    // LID's sleeve (outer radius knuckle_r, riding the rod) never overlaps
    // base's solid bulk there. EVEN-slot (collar) positions get NO cut on
    // base at all: the collar there simply IS base's own material, added
    // back via union() -- it needs to connect directly to base, not have
    // room cleared out from under it.
    //
    // A first version cut ONE uniform pocket the whole hinge_span length
    // from BOTH base and lid -- this left a_shaft's collar (radius
    // knuckle_r=3.0) and b_sleeves (also radius knuckle_r) each floating
    // inside a void that was uniformly BIGGER than either one at every
    // point along the joint (pocket_r = knuckle_r + hinge_clear is bigger
    // than knuckle_r everywhere, at every z), so neither ever touched real
    // material to fuse to. Caught only by rendering base_part() and
    // lid_part() ALONE and finding each split into 2 disconnected
    // components internally -- a clean combined render, and even each
    // part's own "Simple: yes" CGAL stats, gave zero indication.
    for (i = [1 : 2 : n_slots - 1])
        translate([hinge_x0 + i * pitch - pocket_margin, base_depth, base_h])
            rotate([0, 90, 0]) cylinder(r = pocket_r, h = slot_len + 2 * pocket_margin, $fn = 32);
}

module lid_hinge_clearance() {
    // Mirror image of base_hinge_clearance(): deep pocket_r clearance ONLY
    // at EVEN-slot (collar) x-positions, so base's collar never overlaps
    // lid's solid bulk. ODD-slot (sleeve) positions get no pocket cut --
    // the sleeve there IS lid's own material (added back via union).
    for (i = [0 : 2 : n_slots - 1])
        translate([hinge_x0 + i * pitch - pocket_margin, base_depth, base_h])
            rotate([0, 90, 0]) cylinder(r = pocket_r, h = slot_len + 2 * pocket_margin, $fn = 32);
    // PLUS a small pilot bore for the ROD across the WHOLE hinge span --
    // the rod (base's material, continuous end to end) must never touch
    // lid anywhere, including at sleeve positions. Skipping this and
    // relying on b_sleeves()'s OWN internal bore is not enough: union() of
    // lid's uncut solid box and a hollow sleeve tube in the same space has
    // NO hole where the box is solid -- the box's own material fills
    // exactly what the sleeve's bore left open. Confirmed by tracing the
    // actual CSG semantics, not assumed.
    translate([hinge_x0 - recess_margin, base_depth, base_h])
        rotate([0, 90, 0]) cylinder(r = pin_r + hinge_clear, h = hinge_span + 2 * recess_margin, $fn = 24);
}

module mount_hole() {
    // through-hole + top countersink for a flat-head M3 screw
    translate([0, 0, -1]) cylinder(d = screw_d, h = base_h + 2, $fn = 24);
    translate([0, 0, base_h - screw_head_h])
        cylinder(d1 = screw_d, d2 = screw_head_d, h = screw_head_h + 0.5, $fn = 24);
}

module recess_band(y0, y1) {
    // Shallow (air_gap-deep) skin recess across the FULL clip_len band
    // [y0,y1] -- deliberately uniform, no exclusion zone. Safe to apply
    // everywhere because base_part() (below) now applies this recess (and
    // every other cut) ONLY to the plain cuboid, and adds a_shaft/the peg
    // back via a union() OUTSIDE that difference() entirely -- so there is
    // no cut left in the tree that could touch them, no matter where they
    // sit. An earlier version tried to protect them with per-mechanism
    // exclusion zones on the cuts (skip_x0/skip_x1 windows) instead of
    // restructuring the CSG tree -- that only works if every exclusion
    // window exactly matches the mechanism's true footprint, which is easy
    // to get wrong (a 0.6mm margin mismatch on the hinge, and a rectangular
    // exclusion window around a circular peg, both silently welded base+lid
    // solid somewhere else). Restructuring so nothing downstream of
    // a_shaft/peg can cut them at all removes the whole class of bug.
    translate([ear_w, y0, base_h - air_gap]) cube([clip_len, y1 - y0, air_gap + 0.05]);
}

module brand_mark() {
    // negative engraved mark, bottom face (z=0) -- standing rule 2026-08-27.
    // mirror([0,1,0]) confirmed correct for this exact translate+extrude
    // pattern (Technique 4) -- reused verbatim, not re-derived.
    translate([total_len / 2, base_depth / 2, -0.5])
        linear_extrude(height = mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 3.2, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

module base_part() {
    union() {
        difference() {
            cuboid([total_len, base_depth, base_h], rounding = corner_r, edges = "Z",
                   anchor = BOTTOM + FRONT + LEFT);
            base_hinge_clearance();
            // cable channel groove -- cut into the top face only, clip_len region
            translate([ear_w, wall + channel_r, base_h])
                rotate([0, 90, 0]) cylinder(r = channel_r, h = clip_len, $fn = 56);
            // mounting holes, centered in each ear
            translate([ear_w / 2, base_depth / 2, 0]) mount_hole();
            translate([total_len - ear_w / 2, base_depth / 2, 0]) mount_hole();
            // shallow skin recess, both bands, full width -- see recess_band()
            recess_band(wall + 2 * channel_r, base_depth);
            recess_band(0, wall);
            brand_mark();
        }
        // a_shaft + peg added HERE, outside any further difference() --
        // nothing downstream can cut them (see recess_band()'s comment).
        translate([hinge_x0, base_depth, base_h]) a_shaft(hinge_span);
        // peg embedded 1mm BELOW the surface (not flush at z=base_h) so it has
        // real volumetric overlap with the base bulk, not just coincident-face
        // touching -- a flush start here left the peg a disconnected floating
        // island in the exported mesh (Technique 8's exact warning), confirmed
        // by a real connected-component check on the STL.
        translate([latch_x, wall / 2, base_h - 1.0])
            cylinder(r = latch_peg_r, h = latch_peg_len + 1.0, $fn = 24);
    }
}

lid_trim = 0.3;   // lid's own block is trimmed this much shorter than the
                   // channel band at EACH end (see lid_part()'s comment)

module lid_part() {
    union() {
        difference() {
            // Trimmed clip_len - 2*lid_trim wide, NOT the full clip_len --
            // a first version made lid exactly clip_len wide (same as
            // base's channel-groove span), and both parts' channel-notch
            // cross-section at that shared boundary (x=ear_w and
            // x=ear_w+clip_len, y=wall/wall+2*channel_r, z=base_h) landed
            // on EXACTLY the same 4 points -- a cylinder's cross-section is
            // constant along its own axis, so lengthening the CUT past that
            // boundary (tried first) does nothing to change it; only moving
            // the LID's own solid edge away from that boundary does.
            translate([ear_w + lid_trim, 0, base_h])
                cuboid([clip_len - 2 * lid_trim, base_depth, lid_h], rounding = corner_r, edges = "Z",
                       anchor = BOTTOM + FRONT + LEFT);
            // SAME clearance channel cut as base_part() -- a first version
            // only cut this from base, leaving lid's plain box solid across
            // the WHOLE back band including the even-slot collar zones.
            // base's collars (fused to base, reaching up to z=base_h+
            // knuckle_r) then genuinely overlapped lid's own uncut box
            // volume there -- a REAL 3D interference, not just a flat
            // touch, confirmed by a real connected-component check on the
            // combined union (each part alone was fine; only the union
            // fused into one solid, which only happens from either an
            // actual volumetric overlap or an exact zero-gap face contact,
            // and it wasn't the latter here -- neither standalone mesh
            // even shared a vertex with the other).
            lid_hinge_clearance();
            // matching channel groove cut into the lid's underside
            translate([ear_w, wall + channel_r, base_h])
                rotate([0, 90, 0]) cylinder(r = channel_r, h = clip_len, $fn = 56);
            // blind socket for the latch peg
            translate([latch_x, wall / 2, base_h])
                cylinder(r = latch_peg_r + latch_fit, h = latch_peg_len + 0.6, $fn = 24);
        }
        // b_sleeves added OUTSIDE any further cut, same reasoning as
        // a_shaft/peg in base_part().
        translate([hinge_x0, base_depth, base_h]) b_sleeves();
    }
}

union() {
    base_part();
    lid_part();
}
