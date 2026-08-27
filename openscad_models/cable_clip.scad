include <BOSL2/std.scad>

// ============================================================
// Cable Clip — hinged, latching, mountable cable-management clip.
// Rebuild after prior WIP was lost twice (see 3d-print-design SKILL.md
// standing rule: save real, finished work immediately). Base + hinge +
// lid + latch, matching the description of the lost prior attempt.
// ============================================================

// ---- Core dimensions ----
total_len   = 46;   // X: length of the clip (also the hinge axis direction)
depth       = 24;   // Y: front-to-back depth
base_h      = 9;    // Z: base block height
lid_h       = 9;    // Z: lid block height
corner_r    = 1.6;  // vertical-edge rounding (edges="Z" -- zero overhang, see Technique 2)
channel_r   = 4.0;  // cable channel radius -- fits cables/bundles up to ~7mm dia comfortably

// ---- Hinge (Technique 22: stepped shaft + trapped sleeves) ----
pin_r        = 1.6;
hinge_clear  = 0.4;
knuckle_r    = 3.2;
slot_len     = 4;
slot_gap     = 0.5;
pitch        = slot_len + slot_gap;      // 4.5
n_slots      = 8;
hinge_len    = n_slots * pitch;          // 36
hinge_y      = -depth / 2;               // back edge (the physical hinge axis line)
hinge_z      = base_h;                   // seam height
hinge_clr    = 0.3;                      // radial clearance past a knuckle's own radius
root_overlap = 1.0;                      // how far a root bridge reaches PAST the box's inset edge, for a real weld

// Both leaves' PLAIN boxes stop short of the hinge axis by knuckle_r+hinge_clr
// -- clear of BOTH a collar's AND a sleeve's full disk, at every X, since a
// plain box can't vary by X. (Two earlier approaches were tried and both
// failed a real STL connected-component check, not just CGAL's Simple:yes/
// Volumes:2, which caught neither: (1) cutting a per-slot clearance notch
// from a box that otherwise spanned all the way to the axis -- broke
// because OUTSIDE the hinge_len band the box still touched the axis line
// with no notch at all, and that line is the rotation axis itself, so it's
// invariant under open_angle and stayed permanently coincident between
// leaves; (2) insetting the box by only knuckle_r-embed -- that inset was
// LESS than a knuckle's own radius, so the box still overlapped the far
// side of the OTHER leaf's same-radius knuckle disk at every slot,
// confirmed by a direct intersection() render that came back non-empty.)
// The fix here: inset far enough to clear BOTH knuckle types everywhere,
// then weld each leaf's OWN knuckle back to its box with an explicit,
// narrow "root bridge" placed ONLY at that leaf's own matching slots (see
// hinge_root_bridges() below) -- never a uniform per-leaf inset amount.
box_back_y   = hinge_y + knuckle_r + hinge_clr;   // = -8.5

collar_slots = [0, 2, 4, 6];             // fused to base
sleeve_slots = [1, 3, 5, 7];             // fused to lid

// ---- Mounting holes (M3 clearance) ----
hole_r  = 1.7;
hole_x  = total_len / 2 - 8;             // = 15
hole_y  = depth / 2 - 4.2;               // = 7.8, clear of channel and hinge

// ---- Latch (Technique 17: shallow dimple/bump detent, not a cantilever --
// avoids unverifiable flex-fatigue geometry; a bump/pocket friction fit is
// simple, safe, and proven elsewhere in this skill) ----
latch_x       = 0;
latch_y       = depth / 2 - 3;           // = 9, near the front (opposite the hinge)
latch_bump_r  = 2.4;                     // fused to base, protrudes above the seam
latch_dimple_r = 2.2;                    // cut into lid, slightly smaller -> friction interference

// ---- Maker's mark (negative/engraved, per standing rule) ----
// Sized to the model, not copied verbatim from the skill's own example.
// "OnBrandCraftz" at the standing rule's example size=4.5 in Dancing
// Script:style=Bold measured a real 35.47mm wide on THIS clip's STL
// (via the same z-range vertex extraction used elsewhere in this skill)
// -- 77% of the clip's own 46mm length, confirmed too large by direct
// visual review. That single measurement turned out to be a misleading
// basis for scaling down, though: a naive linear projection from it
// (assuming ~7.88mm width per unit size) predicted ~20mm at size=2.5, but
// re-measuring at size=2.5 gave 27.91mm -- a different ratio entirely.
// Two clean re-measurements (size=1.4 -> 15.63mm, size=2.5 -> 27.91mm)
// agree with EACH OTHER exactly (11.16mm/unit both times), so the size=4.5
// figure was almost certainly clipped by the measurement's own x-range
// filter at that larger size, not a real non-linearity in the font. The
// actionable lesson: verify a projected/assumed scaling ratio with a
// SECOND real measurement before trusting it -- one data point can be an
// artifact of how it was measured, not the model.
logo_depth = 0.7;
logo_size  = 1.8;   // -> 20.09mm wide (43.7% of total_len), verified by re-measuring after setting it

// ============================================================
// Hinge primitives
// ============================================================

module hinge_rod() {
    translate([-hinge_len / 2, hinge_y, hinge_z])
        rotate([0, 90, 0])
            cylinder(r = pin_r, h = hinge_len, $fn = 24);
}

module hinge_collars() {
    translate([-hinge_len / 2, hinge_y, hinge_z])
        for (i = collar_slots)
            translate([i * pitch, 0, 0])
                rotate([0, 90, 0])
                    cylinder(r = knuckle_r, h = slot_len, $fn = 24);
}

module hinge_sleeves() {
    // Outer knuckle spans local z:[0, slot_len] (NOT centered). The bore
    // cutter must span that exact same range with margin on both ends --
    // using center=true here (as the skill file's own worked Technique 22
    // example does) leaves the bore centered on z:[-slot_len/2, slot_len/2],
    // which only overlaps the outer's actual [0, slot_len] range for HALF
    // its length, leaving the far half of the sleeve solid and blocking
    // the rod. Confirmed directly: this exact mismatch fused base and lid
    // into a single STL connected component (verified via union-find on
    // real STL vertices, not just CGAL's Volumes count, which stayed 2
    // throughout and never caught it).
    translate([-hinge_len / 2, hinge_y, hinge_z])
        for (i = sleeve_slots)
            translate([i * pitch, 0, 0])
                rotate([0, 90, 0])
                    difference() {
                        cylinder(r = knuckle_r, h = slot_len, $fn = 24);
                        translate([0, 0, -0.5])
                            cylinder(r = pin_r + hinge_clear, h = slot_len + 1, $fn = 24);
                    }
}

// Fills the gap between the axis and the box's inset edge, at ONLY the
// given slots' own X-ranges -- so a leaf's own knuckle gets a real,
// solid weld into its own box without the box needing to reach anywhere
// near the axis at slots belonging to the OTHER leaf. z_lo/z_hi select
// which half of the knuckle's Z-span to bridge (base only exists at
// z<=hinge_z, lid only at z>=hinge_z, so each leaf's bridge covers only
// its own half -- covering both would push material into the other
// leaf's space).
//
// Always bores a pin_r+hinge_clear hole through the bridge at the axis --
// required for a SLEEVE-slot bridge (the continuous rod, which belongs to
// base, must pass all the way through every sleeve slot; a solid bridge
// block there collides with the rod exactly where the sleeve needs
// clearance, confirmed by a direct intersection() render coming back
// non-empty at every sleeve slot's own end-cap boundary). Harmless at a
// COLLAR-slot bridge too -- the collar and rod are already fused parts of
// the same leaf there, so removing this thin cylinder of material changes
// nothing structurally, and boring both means one module handles both
// cases identically instead of risking the same omission again elsewhere.
module hinge_root_bridges(slots, z_lo, z_hi) {
    translate([-hinge_len / 2, hinge_y, 0])
        for (i = slots)
            difference() {
                translate([i * pitch, 0, z_lo])
                    cube([slot_len, (box_back_y - hinge_y) + root_overlap, z_hi - z_lo]);
                translate([i * pitch - 0.5, 0, hinge_z])
                    rotate([0, 90, 0])
                        cylinder(r = pin_r + hinge_clear, h = slot_len + 1, $fn = 24);
            }
}

// ============================================================
// Base (mounting plate + half the cable channel + hinge shaft/collars)
// ============================================================

// Inset from box_back_y (NOT hinge_y) up to the front at depth/2 -- see
// box_back_y's comment above for why this replaces a notch-based approach.
module base_box() {
    box_depth = depth / 2 - box_back_y;
    translate([0, depth / 2 - box_depth / 2, 0])
        cuboid([total_len, box_depth, base_h], rounding = corner_r, edges = "Z", anchor = BOTTOM);
}

module channel_cutter() {
    translate([0, 0, base_h])
        rotate([0, 90, 0])
            cylinder(r = channel_r, h = total_len + 4, center = true, $fn = 64);
}

module mount_holes() {
    for (sx = [-1, 1])
        translate([sx * hole_x, hole_y, -1])
            cylinder(r = hole_r, h = base_h + 2, $fn = 24);
}

module brand_mark() {
    translate([0, -3, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

module latch_bump() {
    translate([latch_x, latch_y, hinge_z_seam_base()])
        sphere(r = latch_bump_r, $fn = 24);
}
function hinge_z_seam_base() = base_h;

module base_part() {
    union() {
        difference() {
            base_box();
            channel_cutter();
            mount_holes();
            brand_mark();
        }
        hinge_rod();
        hinge_collars();
        hinge_root_bridges(collar_slots, hinge_z - knuckle_r, hinge_z);
        latch_bump();
    }
}

// ============================================================
// Lid (other half of the cable channel + hinge sleeves + latch dimple)
// ============================================================

module lid_box() {
    box_depth = depth / 2 - box_back_y;
    translate([0, depth / 2 - box_depth / 2, base_h])
        cuboid([total_len, box_depth, lid_h], rounding = corner_r, edges = "Z", anchor = BOTTOM);
}

module latch_dimple() {
    translate([latch_x, latch_y, hinge_z_seam_base()])
        sphere(r = latch_dimple_r, $fn = 24);
}

module lid_part() {
    union() {
        difference() {
            lid_box();
            channel_cutter();       // same cutter -- mirrors automatically since it's centered on the seam
            latch_dimple();
        }
        hinge_sleeves();
        hinge_root_bridges(sleeve_slots, hinge_z, hinge_z + knuckle_r);
    }
}

// ============================================================
// Assembly -- printed already assembled, shown OPEN.
//
// The latch (base's bump vs. lid's dimple) is a deliberate ~0.2mm
// interference fit -- correct for a real hand-closed latch, but fatal if
// exported in the CLOSED pose: base and lid share one union() for a
// single-file "prints already assembled" part, so any real geometric
// overlap between them gets permanently welded into one fused solid
// (confirmed directly: a closed-pose export of this exact file produced
// only 1 connected component via STL union-find, not the expected 2 --
// Volumes:2 from CGAL did NOT catch this, matching this skill's own
// Technique 20 warning that the Volumes count can't be trusted alone).
// Printing open avoids any base/lid overlap at print time; the user
// swings the lid closed by hand afterward, which is when the latch's
// interference actually engages -- the standard convention for
// print-in-place hinged+latched boxes.
//
// Rotating ONLY lid_part() about the physical hinge axis (the line
// y=hinge_y, z=hinge_z, running along X) keeps the hinge mechanically
// valid regardless of open_angle: the sleeves' bore centers sit exactly
// ON that axis in lid's local frame, so they're invariant under this
// rotation and stay perfectly aligned with base's still-fixed rod.
// ============================================================

open_angle = 100;

union() {
    base_part();
    translate([0, hinge_y, hinge_z])
        rotate([open_angle, 0, 0])
            translate([0, -hinge_y, -hinge_z])
                lid_part();
}
