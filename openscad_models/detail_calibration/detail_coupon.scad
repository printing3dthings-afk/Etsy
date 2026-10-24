// Fine-detail calibration coupon for the 0.4 mm nozzle (2026-10-24).
//
// Technique 78 measured what survives on a TOP face and as a vertical rib.
// Village detail lives on WALLS -- string courses, sills, hood moulds, mortar,
// rivets -- and none of that had been measured. Each row grades one variable
// across seven features; tools/print_fidelity.py on this coupon at 0.20, 0.12
// and 0.08 mm layers says which sizes the printer keeps, and
// measure_coupon.py turns its report into the table in DETAIL_STANDARD.md.
//
// The wall's front face is y = 0; everything stands out toward -y.

W = 90;          // coupon width
H = 46;          // coupon height
T = 6;           // wall thickness
pitch = 12;      // feature spacing in x
fw = 8;          // width of a horizontal feature
x0 = 9;          // first feature's centre

sizes_h  = [0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.2];   // rows 1-3: feature height
sizes_p  = [0.1, 0.15, 0.2, 0.3, 0.4, 0.6, 1.0];  // row 4: how far proud
sizes_d  = [0.6, 0.8, 1.0, 1.2, 1.6, 2.0, 2.6];   // row 5: boss diameter
sizes_g  = [0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1.0];   // row 6: groove depth
sizes_w  = [0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0];   // row 7: rib width

P = 0.6;         // how far rows 1, 2 and 7 stand proud, and row 3's depth
row_z = [3, 9, 15, 21, 27, 33, 39];

function cx(i) = x0 + i * pitch;

// Square-edged ridge: its underside is a 90 degree ledge P deep.
module ridge_square(i, h) {
    translate([cx(i) - fw / 2, -P, row_z[0]]) cube([fw, P + 0.01, h]);
}

// The same ridge with a 45 degree chamfer under it, as the village draws sills.
module ridge_chamfer(i, h, p = P, z = row_z[1]) {
    translate([cx(i) - fw / 2, 0, z])
        rotate([90, 0, 90]) linear_extrude(fw)
            polygon([[0.01, -p], [-p, 0], [-p, h], [0.01, h]]);
}

module groove(i, h) {
    translate([cx(i) - fw / 2, -0.01, row_z[2]]) cube([fw, P + 0.01, h]);
}

module boss(i, d) {
    translate([cx(i), 0, row_z[4] + 1.5]) scale([1, 1, 1])
        intersection() {
            sphere(d = d, $fn = 48);
            translate([-d, -d, -d]) cube([2 * d, d, 2 * d]);
        }
}

module vgroove(i, g) {
    translate([cx(i) - 0.2, -0.01, row_z[5]]) cube([0.4, g + 0.01, 4]);
}

module rib(i, w) {
    translate([cx(i) - w / 2, -P, row_z[6]]) cube([w, P + 0.01, 5]);
}

difference() {
    union() {
        cube([W, T, H]);
        for (i = [0:6]) ridge_square(i, sizes_h[i]);
        for (i = [0:6]) ridge_chamfer(i, sizes_h[i]);
        for (i = [0:6]) ridge_chamfer(i, 1.0, sizes_p[i], row_z[3]);
        for (i = [0:6]) boss(i, sizes_d[i]);
        for (i = [0:6]) rib(i, sizes_w[i]);
    }
    for (i = [0:6]) groove(i, sizes_h[i]);
    for (i = [0:6]) vgroove(i, sizes_g[i]);
}
