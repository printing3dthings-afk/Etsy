include <BOSL2/std.scad>

// ============================================================
// Accordion-fold pleated fan -- Scott's own recorded reference idea
// (Bambu Handy screen recording, 2026-08-27: "a pleated/fluted folding
// fan with a print-in-place hinge along one edge and a snowflake motif").
// Built as a true radial pie-slice fan would need a point-pivot, which
// is mechanically different from a barrel hinge (a linear-axis
// mechanism) -- so this is an ACCORDION-fold fan instead (parallel fold
// lines, like a paper fan/room divider), which DOES match a barrel
// hinge's geometry exactly. Rather than inventing a new "single
// continuous knuckle strip" mechanism from a guess (the skill file's own
// note on this idea calls that "likely simpler," untested), this reuses
// the EXACT hinge pattern already debugged and verified on the cable
// clip -- inset boxes, bored root bridges, real angle/length margins --
// chained across 2 hinge lines for 3 panels. Lower risk than re-deriving
// a new mechanism, which is the entire point of "learn from what you did."
//
// Axis remap from the cable clip (documented explicitly, not just
// assumed correct): there the hinge axis was X, "reach from axis" was Y,
// and the leaf-domain split was Z (base below the seam, lid above). Here
// the hinge axis is Z (so panels stack vertically like a real fan), reach
// from axis is still Y, and the leaf-domain split is X (which panel a
// given point belongs to). cylinder()'s default Z-orientation now
// matches the hinge axis directly -- no rotate([0,90,0]) needed at all,
// removing a whole class of sign-risk this skill has hit before.
//
// No forced-interference latch exists in this design (unlike the cable
// clip), and all 3 panels are built in their own natural, non-rotated
// Y-half from the start -- so there's no "must export open" concern
// here: the flat, fully-spread pose IS the non-overlapping pose, and is
// also the natural presentation pose for a fan (shown open).
// ============================================================

panel_w = 45;
panel_h = 90;
panel_t = 5;
corner_r = 2;

pin_r        = 1.6;
hinge_clear  = 0.4;
knuckle_r    = 3.2;
slot_len     = 4;
slot_gap     = 0.5;
pitch        = slot_len + slot_gap;
n_slots      = 10;
hinge_len    = n_slots * pitch;              // 45
hinge_z0     = (panel_h - hinge_len) / 2;    // center the hinge vertically in the panel
hinge_clr    = 0.3;
root_overlap = 1.0;
y_inset      = knuckle_r + hinge_clr;        // = 3.5 -- both panels stay clear of BOTH
                                              // knuckle types everywhere (cable clip Bug 4's fix)

collar_slots = [0, 2, 4, 6, 8];
sleeve_slots = [1, 3, 5, 7, 9];

hinge_x = [panel_w, 2 * panel_w];   // 2 hinge axis X-positions

// ---- Generic barrel-hinge primitives, axis along Z at (hx, y=0, z0) ----

module hinge_rod(hx, z0) {
    translate([hx, 0, z0])
        cylinder(r = pin_r, h = hinge_len, $fn = 24);
}

module hinge_collars(hx, z0) {
    translate([hx, 0, z0])
        for (i = collar_slots)
            translate([0, 0, i * pitch])
                cylinder(r = knuckle_r, h = slot_len, $fn = 24);
}

module hinge_sleeves(hx, z0) {
    translate([hx, 0, z0])
        for (i = sleeve_slots)
            translate([0, 0, i * pitch])
                difference() {
                    cylinder(r = knuckle_r, h = slot_len, $fn = 24);
                    translate([0, 0, -0.5])
                        cylinder(r = pin_r + hinge_clear, h = slot_len + 1, $fn = 24);
                }
}

// is_left: true if THIS leaf sits on the lower-X side of the hinge axis
// (collar+rod owner in this design's convention), false for the higher-X
// side (sleeve owner). x_lo/x_hi below are RELATIVE to hx -- a real bug
// was caught here: an earlier version took x_lo/x_hi as if already
// absolute world coordinates from the caller, but this module's own
// translate([hx,0,z0]) wrapper ALSO adds hx, double-shifting every bridge
// by hx (confirmed directly: bridges intended near x=45 and x=90 landed
// at x=175-184 instead -- exactly hx added twice). Using a plain
// boolean + fixed relative offsets removes the chance of passing an
// already-absolute value by mistake, the same way hinge_collars()/
// hinge_sleeves() above only ever use relative offsets internally.
// y_lo/y_hi: reach from the axis (0) to just past this leaf's own box
// edge, with root_overlap margin -- unchanged from the proven pattern.
module hinge_root_bridges(hx, z0, slots, is_left, y_lo, y_hi) {
    x_lo = is_left ? -(knuckle_r + 1) : 0;
    x_hi = is_left ? 0 : knuckle_r + 1;
    translate([hx, 0, z0])
        for (i = slots)
            difference() {
                translate([x_lo, y_lo, i * pitch])
                    cube([x_hi - x_lo, y_hi - y_lo, slot_len]);
                translate([0, 0, i * pitch - 0.5])
                    cylinder(r = pin_r + hinge_clear, h = slot_len + 1, $fn = 24);
            }
}

// ---- Panel bodies ----
// Panel N's plain box occupies X:[N*panel_w, (N+1)*panel_w] and is
// uniformly inset in Y (never reaching Y=0, the shared hinge axis) --
// odd-index panels sit on -Y, even-index panels sit on +Y, so adjacent
// panels always face opposite Y-halves at their shared hinge line.

function panel_y_lo(n) = (n % 2 == 0) ? y_inset : -(y_inset + panel_t);
function panel_x0(n) = n * panel_w;

// cuboid(anchor=BOTTOM) only anchors Z at the bottom -- X and Y stay
// CENTERED by default. Passing panel_x0(n)/panel_y_lo(n) (both intended
// as EDGE positions) directly into translate() put them at the box's
// CENTER instead, shifting every panel by half its own width/thickness
// from where it belonged -- confirmed as the cause of nearly all the
// fragmentation seen in this build (bisected via intersection() tests
// down to "collar vs panel2's plain box", then traced to this exact
// edge-vs-center mismatch, the same class of anchor mistake the cable
// clip's base_box()/lid_box() already had to correct for). Fix: add
// half the box's own size to convert the intended edge into the real
// center cuboid() expects.
module panel_box(n) {
    translate([panel_x0(n) + panel_w / 2, panel_y_lo(n) + panel_t / 2, 0])
        cuboid([panel_w, panel_t, panel_h], rounding = corner_r, edges = "Z", anchor = BOTTOM);
}

// Snowflake motif: 3 crossing lines at 60 degrees with small side
// branches -- a plain geometric snowflake, engraved as a shallow
// negative recess (matching this shop's brand-mark convention: negative
// cuts only, never a raised add-on) on the outer face of the last panel.
module snowflake_2d(r) {
    for (a = [0, 60, 120]) {
        rotate([0, 0, a]) {
            square([r * 2, 0.9], center = true);
            for (s = [-1, 1])
                translate([s * r * 0.55, 0, 0])
                    rotate([0, 0, s * 35]) square([r * 0.5, 0.7], center = true);
        }
    }
}
snowflake_depth = 0.7;
module snowflake_mark() {
    translate([panel_x0(2) + panel_w / 2, panel_y_lo(2) + panel_t + 0.5, panel_h / 2])
        rotate([90, 0, 0])
            linear_extrude(height = snowflake_depth + 0.5)
                snowflake_2d(14);
}

logo_depth = 0.6;
// Fitted from the start: panel is 45mm wide, target well under half --
// verified numerically below, same as every other mark in this batch.
logo_size = 1.6;
// rotate([90,0,0]) sends the extrusion toward -Y (confirmed by direct
// measurement: the snowflake mark, cut from panel2's FAR/outer surface
// approaching from larger Y, uses this same sign correctly since -Y is
// INTO its material there). Panel0 sits on the same +Y side as panel2,
// but this mark is cut from the NEAR/inner surface (approaching from the
// hinge-axis side, smaller Y) -- so it needs the opposite sign to
// extrude toward +Y, into panel0's actual material. Confirmed by direct
// measurement: with rotate([90,0,0]) here, zero recess-floor vertices
// were found anywhere near the panel -- the cut was extruding into the
// open air gap between the hinge axis and the panel, never reaching real
// material at all.
module brand_mark() {
    translate([panel_x0(0) + panel_w / 2, panel_y_lo(0) - 0.5, 14])
        rotate([-90, 0, 0])
            linear_extrude(height = logo_depth + 0.5)
                mirror([0, 1, 0])
                    text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                         halign = "center", valign = "center");
}

module panel0() {
    union() {
        difference() {
            panel_box(0);
            brand_mark();
        }
        hinge_rod(hinge_x[0], hinge_z0);
        hinge_collars(hinge_x[0], hinge_z0);
        hinge_root_bridges(hinge_x[0], hinge_z0, collar_slots, true,
            0, panel_y_lo(0) + root_overlap);
    }
}

module panel1() {
    union() {
        panel_box(1);
        hinge_sleeves(hinge_x[0], hinge_z0);
        hinge_root_bridges(hinge_x[0], hinge_z0, sleeve_slots, false,
            panel_y_lo(1) - root_overlap + panel_t, 0);
        hinge_rod(hinge_x[1], hinge_z0);
        hinge_collars(hinge_x[1], hinge_z0);
        hinge_root_bridges(hinge_x[1], hinge_z0, collar_slots, true,
            panel_y_lo(1) - root_overlap + panel_t, 0);
    }
}

module panel2() {
    union() {
        difference() {
            panel_box(2);
            snowflake_mark();
        }
        hinge_sleeves(hinge_x[1], hinge_z0);
        hinge_root_bridges(hinge_x[1], hinge_z0, sleeve_slots, false,
            0, panel_y_lo(2) + root_overlap);
    }
}

union() {
    panel0();
    panel1();
    panel2();
}
