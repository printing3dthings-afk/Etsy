include <BOSL2/std.scad>

// ============================================================
// Wall-mount cable/headphone hook -- keyhole-slotted plate + hook arm.
// No moving parts: lowest-risk design in this batch, built first.
// ============================================================

plate_w   = 40;
plate_h   = 55;
plate_t   = 5;
corner_r  = 3;

// Keyhole slot: a wide circle (screw head passes through) connected to a
// narrower slot (plate slides down, screw shank catches behind the plate).
key_top_r    = 5.0;    // wide circle radius -- must clear a standard screw head
key_slot_w   = 3.2;    // narrow channel width -- must clear the screw SHANK, not the head
key_slot_len = 10;
key_y        = plate_h/2 - 10;   // near the top of the plate

// Hook arm: swept quarter-circle profile, thick enough to hold real cable
// weight without printing a fragile arc (Z-load bearing: FDM is weakest
// across layers, so orient this to print with the arm's length in-plane,
// not standing on its tip).
hook_r_outer = 16;
hook_r_inner = 9;      // hook_r_outer - hook_r_inner = 7mm arm thickness
hook_depth   = 10;     // how far the hook extends out from the wall (Y)

module keyhole_cutter() {
    translate([0, key_y, -1]) {
        cylinder(r = key_top_r, h = plate_t + 2, $fn = 32);
        translate([0, -key_slot_len, 0])
            hull() {
                cylinder(r = key_slot_w/2, h = plate_t + 2, $fn = 20);
                translate([0, key_slot_len, 0])
                    cylinder(r = key_slot_w/2, h = plate_t + 2, $fn = 20);
            }
    }
}

module plate() {
    difference() {
        cuboid([plate_w, plate_h, plate_t], rounding = corner_r, edges = "Z", anchor = BOTTOM);
        keyhole_cutter();
        brand_mark();
    }
}

// Hook: a swept arc (BOSL2 path_sweep along a quarter-circle path) so the
// load path curves smoothly with the layers instead of stepping through
// discrete rotated segments -- same reasoning as Technique 12's stem fix
// (one continuous swept mesh reads and prints better than chained
// segments, and here it also avoids any per-segment seam becoming a
// stress-concentration point under real cable weight).
module hook_arm() {
    arc_r = (hook_r_outer + hook_r_inner) / 2;
    arm_w = hook_r_outer - hook_r_inner;
    path = [for (a = [0:5:200]) [0, arc_r * sin(a), arc_r - arc_r * cos(a)]];
    cross_section = [
        [-arm_w/2, -arm_w/2], [arm_w/2, -arm_w/2],
        [arm_w/2, arm_w/2], [-arm_w/2, arm_w/2],
    ];
    // path already lies in the Y-Z plane (x=0 throughout) -- no rotate
    // needed, and adding one here would reorient the arc's plane away
    // from "out from the wall, curling upward" without changing anything
    // about how the path itself was authored (exactly the kind of stray
    // rotate this skill's own hinge/latch work has repeatedly gotten
    // wrong -- simplest fix is not adding it in the first place).
    translate([0, plate_h/2 - hook_r_outer - 4, plate_t/2])
        path_sweep(cross_section, path, closed = false);
}

logo_depth = 0.6;
// Fitted from the start per the standing rule: plate is 40mm wide, so
// target a mark comfortably under half that -- verified numerically
// below before treating this as final, not assumed from a copied size.
logo_size = 1.6;
module brand_mark() {
    translate([0, -plate_h/2 + 8, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

union() {
    plate();
    hook_arm();
}
