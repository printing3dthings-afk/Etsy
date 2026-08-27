include <BOSL2/std.scad>

R = 50;
H = 100;
wall = 4;
floor_h = 4;
rim_h = 9;

module outer_shell() {
    cylinder(r = R, h = H, $fn = 6);
}
module inner_cavity() {
    translate([0, 0, floor_h])
        cylinder(r = R - wall, h = H, $fn = 6);
}

apothem = R * cos(180 / 6);
face_half = R * sin(180 / 6);
hex_r = 2.8;
hex_gap = 1.0;
pitch = 2 * hex_r * cos(30) + hex_gap;
row_step = pitch * sqrt(3) / 2;

module hex_cell() {
    rotate([90, 0, 0])
        cylinder(r = hex_r, h = wall + 4, $fn = 6, center = true);
}

module face_honeycomb() {
    usable_w = 2 * face_half - 2 * rim_h;
    usable_h = H - 2 * rim_h;
    n_cols = floor(usable_w / pitch);
    n_rows = floor(usable_h / row_step);
    for (row = [0:n_rows-1]) {
        y_off = (row % 2 == 0) ? 0 : pitch / 2;
        for (col = [0:n_cols-1]) {
            x = -usable_w/2 + pitch/2 + col * pitch + y_off;
            z = rim_h + row_step/2 + row * row_step;
            if (x > -face_half + rim_h/2 && x < face_half - rim_h/2 && z < H - rim_h)
                translate([x, apothem, z]) hex_cell();
        }
    }
}

module all_faces_honeycomb() {
    for (i = [0:5])
        rotate([0, 0, i * 60])
            face_honeycomb();
}

// Maker's mark, engraved (negative-space cut) into the underside of the
// solid floor -- reuses the confirmed-correct mirror([0,1,0]) technique
// from the phone stand (3d-print-design skill, Technique 4).
logo_depth = 0.7;
module brand_mark() {
    translate([0, 12, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 6, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

difference() {
    outer_shell();
    inner_cavity();
    all_faces_honeycomb();
    brand_mark();
}
