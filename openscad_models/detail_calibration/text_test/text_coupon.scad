// Text and tiny-shape coupon (2026-10-30): how small raised lettering and dots
// survive the toolpath, on a 0.4 and a 0.2 mm nozzle. measure_text.py reads it.
// A floor with six rows of raised text on top (printed face up), and a wall
// with the same six rows raised on its front face (printed upright), each row
// "OBC 8 Sg" at one size, plus a row of dots 0.4-1.6 across.
SIZES = [1.0, 1.5, 2.0, 2.5, 3.0, 4.0];   // OpenSCAD text size (about cap height + a little)
PROUD = 0.4;
FONT = "DejaVu Sans:style=Bold";
ROWY = function (i) 4 + i * 6;
DOTS = [0.4, 0.6, 0.8, 1.0, 1.2, 1.6];
module row(i) text("OBC 8 Sg", size = SIZES[i], font = FONT, valign = "center");
module dots() for (k = [0 : len(DOTS) - 1]) translate([2 + k * 4, 0]) circle(d = DOTS[k], $fn = 32);
// the floor, 60 x 44 x 2, text on top
translate([0, 0, 0]) {
    cube([60, 44, 2]);
    for (i = [0 : 5]) translate([3, ROWY(i), 2]) linear_extrude(PROUD) row(i);
    translate([36, 40, 2]) linear_extrude(PROUD) dots();
}
// the wall, 60 long x 3 thick x 44 tall, standing behind; text on its -y face
translate([0, 60, 0]) {
    cube([60, 3, 44]);
    for (i = [0 : 5]) translate([3, 0, ROWY(i)]) rotate([90, 0, 0]) linear_extrude(PROUD) row(i);
    translate([36, 0, 40]) rotate([90, 0, 0]) linear_extrude(PROUD) dots();
}
