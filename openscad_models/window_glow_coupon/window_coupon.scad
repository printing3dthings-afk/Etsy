// Window glow coupon, for Explained Lesson 005 "Why our windows are 0.8 mm thin" (2026-11-20).
// The lesson has been held since Nov 11 for one real photo: three windows at 0.8 / 1.6 / 2.4 mm
// lit from behind by one tea light. This prints them side by side, standing up the way our house
// walls do, so the pane's thickness is laid down by the wall's perimeters, as on a real house.
// Print in white PLA. Stand it on the table with the tea light behind the windows.

PANES  = [0.8, 1.6, 2.4];   // pane thickness, mm: two, four and six 0.4 mm lines
WALL   = 3.2;               // the frame around the windows
WIN_W  = 24;                // each window opening
WIN_H  = 32;
GAP    = 8;                 // frame between windows
SIDE   = 8;
TOP    = 8;
SILL   = 10;                // frame below the windows, above the foot
FOOT_D = 34;                // foot depth, so it stands on its own
FOOT_H = 3;
LABEL  = 0.8;               // label height, raised on the foot (4 layers)

n = len(PANES);
W = 2 * SIDE + n * WIN_W + (n - 1) * GAP;
H = FOOT_H + SILL + WIN_H + TOP;
function wx(i) = SIDE + i * (WIN_W + GAP);

module wall() {
    difference() {
        cube([W, WALL, H]);
        // each window is a pocket from the back, leaving the pane at the front face. The
        // pocket's ceiling slopes up toward the back, about 63 deg from flat: a flat one is a 24 mm bridge.
        for (i = [0 : n - 1]) pocket(i);
    }
}

module pocket(i) {
    d = WALL - PANES[i];
    z0 = FOOT_H + SILL;
    // the pocket's section in Y-Z, extruded along X across the window
    translate([wx(i), 0, 0]) rotate([90, 0, 90]) linear_extrude(WIN_W)
        polygon([[PANES[i], z0], [WALL + 0.01, z0], [WALL + 0.01, z0 + WIN_H + 2 * d], [PANES[i], z0 + WIN_H]]);
}

// the panes alone, declared to the gate as the thin feature under test
module panes() {
    for (i = [0 : n - 1]) translate([wx(i) - 1, -0.01, FOOT_H + SILL - 1]) cube([WIN_W + 2, PANES[i] + 0.02, WIN_H + 2]);
}

module foot() {
    // centred under the wall, so the coupon stands without tipping
    translate([0, -(FOOT_D - WALL) / 2, 0]) cube([W, FOOT_D, FOOT_H]);
}

module labels() {
    for (i = [0 : n - 1])
        translate([wx(i) + WIN_W / 2, -(FOOT_D - WALL) / 2 + 6, FOOT_H])
            linear_extrude(LABEL)
                text(str(PANES[i]), size = 6.5, font = "Montserrat:style=Bold", halign = "center", valign = "center");
}

module obc() {
    // maker's mark on the back of the foot
    translate([W - 14, WALL + (FOOT_D - WALL) / 2 - 5, FOOT_H])
        linear_extrude(LABEL) text("OBC", size = 4.5, font = "Montserrat:style=Bold", halign = "center", valign = "center");
}

part = "all";
if (part == "body" || part == "all") { wall(); foot(); obc(); }
if (part == "labels" || part == "all") labels();
if (part == "panes") panes();
