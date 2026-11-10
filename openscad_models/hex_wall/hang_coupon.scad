// Hex Wall Tiles: the hang-joint test print (2026-11-10).
// Each tile carries a dovetail rail; a module's back has the matching slot, open at
// the bottom and closed at the top. It slides down onto the rail and hangs on the
// rail's top end: its weight holds it down, the dovetail holds it to the wall.
// The flanks lean 30 deg off the wall's normal, so the rail prints on the tile
// (lying on its back) and the slot prints in the module (lying on its back) with no
// supports: the slot's ceiling is a 15 mm bridge.
// The coupon is a strip of tile with the real rail and a screw hole, and two modules
// with a 40 deg hook, their slots 0.2 and 0.3 clear (one and two notches).
//   part = "tile" | "module" (with C) | "plate" | "hung" (with C)
part = "plate";
C = 0.2;

T = 4;                      // tile plate thickness
RAIL_N = 12;                // the rail's width at the tile's face
RAIL_H = 3;                 // its height off the face
FL = 30;                    // flank angle off the wall's normal
RAIL_W = RAIL_N + 2 * RAIL_H * tan(FL);     // its width at the top, 15.46
RAIL_L = 34;
TILE = [44, 56];
RAIL_Y0 = 14;               // the rail runs from here to the tile's top edge minus 4
SCREW_D = 4.5; SCREW_HEAD = 9;

M_T = 4;                    // module plate, behind the slot ceiling
M = [30, 48];
SLOT_LEN = 40;              // from the module's bottom edge
$fn = 64;

module dovetail(n, h, len) rotate([90, 0, 0]) rotate([0, 0, 0])
    linear_extrude(height = len) polygon([[-n / 2, 0], [n / 2, 0], [n / 2 + h * tan(FL), h], [-n / 2 - h * tan(FL), h]]);

module tile() difference() {
    union() {
        translate([-TILE[0] / 2, 0, 0]) cube([TILE[0], TILE[1], T]);
        translate([0, RAIL_Y0 + RAIL_L, T - 0.01]) dovetail(RAIL_N, RAIL_H + 0.01, RAIL_L);
    }
    // one countersunk screw hole below the rail
    translate([0, 7, -1]) cylinder(h = T + 2, d = SCREW_D);
    translate([0, 7, T - (SCREW_HEAD - SCREW_D) / 2]) cylinder(h = (SCREW_HEAD - SCREW_D) / 2 + 0.01, d1 = SCREW_D, d2 = SCREW_HEAD);
}

// The module, printed on its back: the slot is the rail grown by C, cut up from the
// back face; the hook rises from its front at 40 deg off vertical (as printed)
module module_(C, notches) difference() {
    union() {
        translate([-M[0] / 2, 0, 0]) cube([M[0], M[1], RAIL_H + M_T]);
        // the hook: out from the plate and up, as a 6 mm round bar; a round tip
        translate([0, 10, RAIL_H + M_T - 0.5]) rotate([-40, 0, 0]) {
            cylinder(h = 30, d = 7);
            translate([0, 0, 30]) sphere(d = 7);
        }
    }
    // the slot: open at the bottom (y = 0), closed SLOT_LEN up; its mouth on the back
    // face is RAIL_N + 2C wide, and it is RAIL_H + C deep
    translate([0, SLOT_LEN, -0.01]) dovetail(RAIL_N + 2 * C, RAIL_H + C, SLOT_LEN + 1);
    for (k = [1 : notches]) translate([M[0] / 2, M[1] - 4 - 4 * k, (RAIL_H + M_T) / 2]) cube([1.6, 1.2, RAIL_H + M_T + 2], center = true);
}

if (part == "tile") tile();
else if (part == "module") module_(C, C < 0.25 ? 1 : 2);
else if (part == "plate") {
    tile();
    translate([42, 0, 0]) module_(0.2, 1);
    translate([42, 62, 0]) module_(0.3, 2);
}
else if (part == "hung") {
    // the module's back on the tile's face, its slot's top end resting on the rail's
    tile();
    translate([0, RAIL_Y0 + RAIL_L - SLOT_LEN, T]) module_(C, 1);
}
echo("RAIL_W", RAIL_W);
