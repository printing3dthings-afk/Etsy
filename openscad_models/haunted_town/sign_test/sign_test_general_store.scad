// Test print of the general store's sign: its board and raised letters
// exactly as on the building -- the building's own modules, in their own
// place, tilt and lean -- on a plain slab of wall, standing on a foot.
// About 20 minutes; see SIGN_TEST.md.
include <../general_store/haunted_general_store.scad>
part = "none";
module frame() on_face(1, sg_u, sg_z) children();
st_z = sg_z - sg_h/2 - 3.5;           // the slab is cut flat here to stand on
module piece() intersection() {
    union() {
        // the slab's face stands where the wall's texture does
        frame() translate([-(sg_w/2 + 2), -(sg_h/2 + 5), -1.4]) cube([sg_w + 4, sg_h + 9, 1.4 + fr_t - 0.84]);
        sign_board(); sign_letters();
    }
    translate([-200, -200, st_z]) cube([400, 400, sg_h + 7]);
}
// Turned a quarter, letters to +x, so four sit side by side on the plate.
rotate([0, 0, 90]) translate([0, 0, 1.2 - st_z]) {
    piece();
    // a foot 1.2 thick, 4 mm out round the slab's footprint
    translate([0, 0, st_z - 1.2]) linear_extrude(1.21) offset(delta = 4) hull() projection(cut = true) translate([0, 0, -st_z - 0.05]) piece();
}
