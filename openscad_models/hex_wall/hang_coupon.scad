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
RAIL_H = 3.5;               // its height off the face (3.5 so the blunted lips keep 4x the stack)
FL = 30;                    // flank angle off the wall's normal
RAIL_W = RAIL_N + 2 * (RAIL_H - 0.8) * tan(FL);     // its widest, 15.12
RAIL_L = 34;
TILE = [44, 56];
RAIL_Y0 = 14;               // the rail runs from here to the tile's top edge minus 4
SCREW_D = 4.5; SCREW_HEAD = 9;

M_T = 4;                    // module plate, behind the slot ceiling
M = [30, 58];                // the slot runs 0..SLOT_LEN; the hook roots above it
SLOT_LEN = 40;              // from the module's bottom edge
MV = 1.2;                   // the slot's mouth rises straight this far
$fn = 64;

// The flanks stop BLUNT short of the top and stand straight for it: run to the top they
// met it at a 60 deg edge the gate read at 0.13 (2026-11-10)
BLUNT = 0.8;
module dovetail(n, h, len) rotate([90, 0, 0])
    linear_extrude(height = len) polygon([[-n / 2, 0], [n / 2, 0], [n / 2 + (h - BLUNT) * tan(FL), h - BLUNT],
        [n / 2 + (h - BLUNT) * tan(FL), h], [-n / 2 - (h - BLUNT) * tan(FL), h], [-n / 2 - (h - BLUNT) * tan(FL), h - BLUNT]]);

module tile() difference() {
    union() {
        translate([-TILE[0] / 2, 0, 0]) cube([TILE[0], TILE[1], T]);
        translate([0, RAIL_Y0 + RAIL_L, T - 0.01]) dovetail(RAIL_N, RAIL_H + 0.01, RAIL_L);
    }
    // one countersunk screw hole below the rail
    translate([0, 7, -1]) cylinder(h = T + 2, d = SCREW_D);
    translate([0, 7, T - (SCREW_HEAD - SCREW_D) / 2]) cylinder(h = (SCREW_HEAD - SCREW_D) / 2 + 0.01, d1 = SCREW_D, d2 = SCREW_HEAD);
}

// The module, printed on its back: the slot is the rail grown by C, a window through
// it; the hook rises from its front above the window, 40 deg off vertical (as printed)
module module_(C, notches) difference() {
    union() {
        translate([-M[0] / 2, 0, 0]) cube([M[0], M[1], RAIL_H + M_T]);
        // the hook: out from the plate and up, as a 6 mm round bar; a round tip
        // its root sunk 2.4 into the plate: at 0.5 the bar's tilted end stood 1.75 proud
        // on its low side, a 50 deg ledge the slicer propped up
        translate([0, SLOT_LEN + 7, RAIL_H + M_T - 2.4]) rotate([-40, 0, 0]) {
            cylinder(h = 30, d = 7);
            translate([0, 0, 30]) sphere(d = 7);
        }
    }
    // the slot runs right through the module, a window from its back to its front: the
    // dovetail's flanks lean out from the back face, then stand straight to the front.
    // With a ceiling over it (a slot only in the back) the bridge's free edge at the open
    // end printed as overhang perimeters however it was shaped (2026-11-10); with none,
    // nothing prints over air. The mouth rises straight for MV first (see MV).
    let (n = RAIL_N + 2 * C, hf = RAIL_H + C - BLUNT, w = n / 2 + hf * tan(FL), wm = n / 2 + MV * tan(FL))
        translate([0, SLOT_LEN, -0.01]) rotate([90, 0, 0]) linear_extrude(height = SLOT_LEN + 1)
            polygon([[-wm, 0], [wm, 0], [wm, MV], [w, hf], [w, RAIL_H + M_T + 1], [-w, RAIL_H + M_T + 1], [-w, hf], [-wm, MV]]);
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
