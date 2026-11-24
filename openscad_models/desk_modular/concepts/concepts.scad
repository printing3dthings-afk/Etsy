// Modular desktop organizer: five connection concepts, sketch level (2026-11-24).
// Benson's brief (business/muse_claude/threads/2026-11-24_modular-organizer-brief.md on main):
// our own modular system with a defined interface for future attachments, "a different
// connection method" from the puzzle interlock, strength from walls not infill. Scott picks
// one of these; only then is anything designed for real. These are review sketches: walls and
// fits are indicative, not checked.
//
//   part = <option>_<piece>, e.g. dovetail_a, dovetail_b; see the table at the bottom
//   Each option's pieces share one frame, posed partly apart so the joint shows.

part = "dovetail_a";
U = 40;          // the grid unit: every module is a whole number of units across
H = 60;          // a bin's height in these sketches
WALL = 2.0;      // five beads at 0.4
R = 4;           // vertical corners
$fn = 48;

module rbox(w, d, h, r = R) linear_extrude(h) offset(r) offset(-r) square([w, d]);
module bin(w, d, h) difference() {
    rbox(w, d, h);
    translate([WALL, WALL, WALL]) rbox(w - 2 * WALL, d - 2 * WALL, h, R - WALL / 2);
}

// ---- 1. drop-in dovetail: tails on +x, sockets on -x; the next module drops down onto them --
DT_W = 8; DT_N = 5; DT_D = 3.5; DT_CL = 0.25;
module tail2d(cl = 0) polygon([[-cl, -DT_N / 2 - cl], [DT_D + cl, -DT_W / 2 - cl], [DT_D + cl, DT_W / 2 + cl], [-cl, DT_N / 2 + cl]]);
module dovetail_a() bin(U * 2, U * 2, H);
module dovetail_tails() for (y = [U / 2, U * 1.5]) translate([U * 2 - 0.01, y, 4]) linear_extrude(H - 4) tail2d();
module dovetail_b() translate([U * 2 + 30, 0, 24]) difference() {   // shown lifted off its seat, and aside
    union() {
        bin(U, U * 2, H - 10);
        for (y = [U / 2, U * 1.5]) translate([-0.01, y, 0]) linear_extrude(H - 10) translate([0, -(DT_W + 6) / 2]) square([DT_D + 3, DT_W + 6]);
    }
    for (y = [U / 2, U * 1.5]) translate([-0.01, y, 4]) linear_extrude(H) tail2d(DT_CL);
}

// ---- 2. butterfly key: the same half-pocket at every unit on every side; a key joins two ------
KEY_L = 16; KEY_W = 10; KEY_N = 5; KEY_H = 16;
module key2d(cl = 0) offset(delta = cl) polygon([[-KEY_L / 2, -KEY_W / 2], [-KEY_L / 2, KEY_W / 2], [0, KEY_N / 2], [KEY_L / 2, KEY_W / 2],
                                                 [KEY_L / 2, -KEY_W / 2], [0, -KEY_N / 2]]);
module keyed(w, d, h) difference() {
    union() {
        bin(w, d, h);
        // thickened wall round each pocket, inside the bin
        for (y = [U / 2 : U : d]) for (x = [0, w]) translate([x, y, 0]) linear_extrude(h) square([KEY_L + 6, KEY_W + 6], center = true);
    }
    for (y = [U / 2 : U : d]) for (x = [0, w]) translate([x, y, h - KEY_H]) linear_extrude(KEY_H + 1) key2d(0.2);
    // trim the thickening back to the box
    translate([-50, -1, -1]) cube([50, d + 2, h + 2]);
    translate([w, -1, -1]) cube([50, d + 2, h + 2]);
}
module butterfly_a() keyed(U * 2, U * 2, H);
module butterfly_b() translate([U * 2, 0, 0]) keyed(U, U * 2, H);
module butterfly_key() for (y = [U / 2, U * 1.5]) translate([U * 2, y, H - KEY_H + (y < U ? 0 : 14)]) linear_extrude(KEY_H - 0.3) key2d();

// ---- 3. base grid: a plate of shallow sockets; every module stands in it on locating feet ----
module grid_plate() difference() {
    rbox(U * 4, U * 2, 4);
    for (i = [0 : 3], j = [0 : 1]) translate([i * U + 2, j * U + 2, 1.6]) rbox(U - 4, U - 4, 5, 3);
}
module grid_foot(w, d) for (i = [0 : w / U - 1], j = [0 : d / U - 1]) translate([i * U + 2.3, j * U + 2.3, 0]) rbox(U - 4.6, U - 4.6, 2.6, 2.8);
module grid_a() translate([0, 0, 1.6]) union() { translate([0, 0, 2.6]) bin(U * 2, U * 2, H); grid_foot(U * 2, U * 2); }
module grid_b() translate([U * 2, 0, 22]) union() { translate([0, 0, 2.6]) bin(U * 2, U, H - 20); grid_foot(U * 2, U); }

// ---- 4. back rail: one dovetail rail on the desk; modules slide on along it from the end -----
RAIL_L = U * 4; RAIL_W = 14; RAIL_H = 6;
module rail2d(cl = 0) polygon([[-RAIL_W / 2 + 2 - cl, -cl], [RAIL_W / 2 - 2 + cl, -cl], [RAIL_W / 2 + cl, RAIL_H + cl], [-RAIL_W / 2 - cl, RAIL_H + cl]]);
module rail_rail() translate([0, U * 2 + RAIL_W / 2 - 2, 0]) union() {
    rotate([90, 0, 90]) linear_extrude(RAIL_L) translate([0, 0]) polygon([[-RAIL_W / 2 - 4, 0], [RAIL_W / 2 + 4, 0], [RAIL_W / 2 + 4, 1.6], [-RAIL_W / 2 - 4, 1.6]]);
    translate([0, 0, 1.59]) rotate([90, 0, 90]) linear_extrude(RAIL_L) rail2d();
}
module railed(x, w, h, lift = 0) translate([x, 0, lift]) difference() {
    union() { bin(w, U * 2, h); translate([0, U * 2 - 2, 0]) cube([w, RAIL_W + 4, h]); }
    translate([-1, U * 2 + RAIL_W / 2 - 2, -0.01]) rotate([90, 0, 90]) linear_extrude(w + 2) rail2d(0.25);
    translate([-1, U * 2 + RAIL_W / 2 - 2, -0.01]) rotate([90, 0, 90]) linear_extrude(w + 2) translate([0, 0.8]) square([RAIL_W + 9, 1.65], center = true);
}
module rail_a() railed(0, U, H + 20);
module rail_b() railed(U + 0.5, U * 2, H - 15);
module rail_c() railed(U * 3 + 26, U, H, 0);   // sliding on from the end

// ---- 5. magnets: 6 x 3 discs pressed into pockets behind a 0.6 skin, every unit, every side ---
MAG_D = 6; MAG_T = 3;
module magnet_bin(w, d, h) difference() {
    union() {
        bin(w, d, h);
        for (y = [U / 2 : U : d]) for (x = [WALL, w - WALL]) for (z = [12, h - 12]) translate([x, y, z]) rotate([0, 90, 0]) cylinder(h = 2 * (MAG_T + 0.6), r = MAG_D / 2 + 1.6, center = true);
    }
    translate([-50, -1, -1]) cube([50, d + 2, h + 2]);
    translate([w, -1, -1]) cube([50, d + 2, h + 2]);
}
module magnet_a() magnet_bin(U * 2, U * 2, H);
module magnet_b() translate([U * 2 + 10, 0, 0]) magnet_bin(U, U * 2, H);
module magnet_discs() for (o = [0, U * 2 + 10]) for (x = [0.6, U * (o ? 1 : 2) - 0.6 - MAG_T]) for (y = [U / 2, U * 1.5]) for (z = [12, H - 12])
    translate([o + x, y, z]) rotate([0, 90, 0]) cylinder(h = MAG_T, r = MAG_D / 2);

if      (part == "dovetail_a") dovetail_a();
else if (part == "dovetail_b") dovetail_b();
else if (part == "dovetail_tails") dovetail_tails();
else if (part == "butterfly_a") butterfly_a();
else if (part == "butterfly_b") butterfly_b();
else if (part == "butterfly_key") butterfly_key();
else if (part == "grid_plate") grid_plate();
else if (part == "grid_a") grid_a();
else if (part == "grid_b") grid_b();
else if (part == "rail_rail") rail_rail();
else if (part == "rail_a") rail_a();
else if (part == "rail_b") rail_b();
else if (part == "rail_c") rail_c();
else if (part == "magnet_a") magnet_a();
else if (part == "magnet_b") magnet_b();
else if (part == "magnet_discs") magnet_discs();
