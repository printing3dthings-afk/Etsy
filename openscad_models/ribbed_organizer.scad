include <BOSL2/std.scad>

// ============================================================
// Ribbed 3-compartment desk organizer/caddy -- Scott's own recorded
// reference idea (Bambu Handy screen recording, 2026-08-27): horizontal
// corrugated ridges wrapping the exterior of a multi-compartment holder.
// No moving parts -- reuses Technique 2's proven rounded-solid pattern.
// ============================================================

size      = [130, 75, 55];   // outer W x D x H
wall      = 2.4;
floor     = 3;
corner_r  = 5;
n_bays    = 3;

// Ribs: horizontal grooves cut into the FLAT exterior walls. Since the
// walls are flat (not curved like the vase/pumpkin), this needs none of
// Technique 5's skin()-loft machinery -- a plain repeated groove cutter
// on each flat face is sufficient and far simpler.
rib_depth = 0.8;   // absolute mm, well under `wall` (2.4mm) at every point --
                    // same wall-thickness-margin discipline as Technique 5,
                    // just trivial to satisfy here since walls don't taper
rib_pitch = 6;
rib_h     = 3;      // groove height (Z)
rib_margin_top    = 8;   // keep ribs clear of the rim
rib_margin_bottom = 6;   // keep ribs clear of the floor

module outer_shell() {
    cuboid(size, rounding = corner_r, edges = "Z", anchor = BOTTOM);
}

// One shallow groove cutter PER FACE, at a given Z -- each cutter is a
// thin slab straddling just that one face's surface (1mm proud outside
// for a clean cut + rib_depth into the material), spanning only the
// FLAT run of that face (excluding the rounded corners, same "flat faces
// only" discipline Technique 21 established for hex lattices). A first
// draft here mistakenly used a cutter with FULL width on one axis and
// reduced width on the other, intending an "inset from front/back" belt
// -- that actually cuts a full slab through BOTH side walls at every rib
// height, nearly severing the whole shell, since a solid box removes
// everything inside its bounding volume, not just the outer skin. Fixed
// by keeping each face's cutter thin (rib_depth) in the direction
// PERPENDICULAR to that face and full-flat-width in the other two axes.
module rib_grooves() {
    n_ribs = floor((size.z - rib_margin_top - rib_margin_bottom) / rib_pitch);
    flat_x = size.x - 2 * corner_r;
    flat_y = size.y - 2 * corner_r;
    for (i = [0:n_ribs-1]) {
        z = rib_margin_bottom + i * rib_pitch;
        translate([-flat_x/2, size.y/2 - rib_depth, z])
            cube([flat_x, rib_depth + 1, rib_h]);                 // front
        translate([-flat_x/2, -size.y/2 - 1, z])
            cube([flat_x, rib_depth + 1, rib_h]);                 // back
        translate([size.x/2 - rib_depth, -flat_y/2, z])
            cube([rib_depth + 1, flat_y, rib_h]);                 // right
        translate([-size.x/2 - 1, -flat_y/2, z])
            cube([rib_depth + 1, flat_y, rib_h]);                 // left
    }
}

// Bay layout: 3 compartments, the LEFT one wider (matches the Kumiko
// pen-holder precedent's "slant/differentiate bays for real use," here
// simplified to "one wide bay for bulky items, two narrow for pens/clips").
bay_gap   = wall;
usable_w  = size.x - wall * 2;
wide_w    = usable_w * 0.42;
narrow_w  = (usable_w - wide_w - bay_gap * 2) / 2;
bay_d     = size.y - wall * 2;
bay_r     = max(corner_r - wall, 1.5);

function bay_x(i) =
    let(left_edge = -size.x/2 + wall)
    i == 0 ? left_edge + wide_w/2 :
    i == 1 ? left_edge + wide_w + bay_gap + narrow_w/2 :
             left_edge + wide_w + bay_gap*2 + narrow_w + narrow_w/2;
function bay_w(i) = i == 0 ? wide_w : narrow_w;

module bay_cutters() {
    for (i = [0:n_bays-1])
        translate([bay_x(i), 0, floor])
            cuboid([bay_w(i), bay_d, size.z], rounding = bay_r, edges = "Z", anchor = BOTTOM);
}

logo_depth = 0.6;
// Fitted from the start: bottom face is 130x75mm, target well under half
// the shorter usable run (~75mm) -- verified numerically below.
logo_size = 3.2;
module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

difference() {
    outer_shell();
    rib_grooves();
    bay_cutters();
    brand_mark();
}
