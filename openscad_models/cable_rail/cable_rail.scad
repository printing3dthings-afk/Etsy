// Desk Cable Rail (2026-11-12): v2 of the Cable Hook, form C of five (Scott picked it).
// Benson's thread, from Scott's look at the old hook: a chunky C on an oversized plate,
// two holes that don't explain themselves, a hook that doesn't read as a hook.
//
// A slim J-channel that screws (or tapes) under a desk's front or back edge. Cables
// drop in through the gap between the lip and the desk and lie in a row; three angled
// notches in the lip let a cable leave the rail wherever it needs to go down.
//
// The profile is drawn in the mounted frame: x across (0 = the channel's back wall,
// + toward the room), z up (0 = the desk's underside), the rail along y. It prints
// standing on its y = L end, the length going up, so every wall is upright; laid flat,
// either way, the J's curl would hang in the air. Up on the printer is mounted -y.
//
// No OBC mark: every face prints upright, and engraved letters on an upright face have
// ceilings the slicer props (the first draft's mark on the tab drew supports).
//
//   part = "rail" (as printed) | "mounted" (for renders)
//   L    = length, mm

part = "rail";
L = 60;
$fn = 48;

WALL   = 2.4;      // the channel's walls: 6 beads
FLANGE = 3.0;      // the screw tab
TAB    = 14;       // how far the tab runs behind the channel
CH_W   = 18;       // channel width, wall centre to wall centre
CH_D   = 26;       // from the desk down to the outside of the floor
LIP_Z  = -9;       // top of the front lip: a 9 mm gap to the desk for cables to drop in
HOLE   = 4.2;      // #6 or #8 pan-head wood screw
SLOPE  = 37;       // overhangs, deg from upright (the detail standard's)
NOTCH_D = 7;       // the drop notches: how far below the lip they reach
NOTCH_W = 7;       // and how long along the rail at their bottom

// ---------- the profile: a stroke of WALL along the J, plus the tab ----------
module seg(a, b, w) hull() { translate(a) circle(d = w); translate(b) circle(d = w); }
R = CH_W / 2;
X_BACK = WALL / 2; X_FRONT = X_BACK + CH_W; Z_FLOOR = -CH_D + WALL / 2;
ARC = [for (a = [180 : 10 : 360]) [X_BACK + R + R * cos(a), Z_FLOOR + R + R * sin(a)]];
module profile2d() union() {
    translate([-TAB, -FLANGE]) square([TAB + WALL, FLANGE]);         // tab, flush with the desk
    seg([X_BACK, -FLANGE / 2], [X_BACK, Z_FLOOR + R], WALL);           // back wall
    for (i = [0 : len(ARC) - 2]) seg(ARC[i], ARC[i + 1], WALL);         // the curl
    seg([X_FRONT, Z_FLOOR + R], [X_FRONT, LIP_Z - WALL / 2], WALL);     // front wall up to the lip
}

// screw holes through the tab: across the print. Each a teardrop pointing -y (up on
// the printer).
module hole(y) translate([-TAB / 2, y, -FLANGE - 1]) linear_extrude(FLANGE + 2) hull() {
    circle(d = HOLE);
    translate([0, -HOLE / 2 / sin(SLOPE)]) square(0.01, center = true);
}

// the drop notches, cut down from the lip. Local u runs along +y (down on the printer),
// v is the mounted z. The notch's upper side on the printer (small u) leans SLOPE from
// upright: it runs NOTCH_D / tan(SLOPE) along the rail for its NOTCH_D of depth. A first
// draft leaned the other side, at 53 deg, and the gate's slicer propped every notch.
NOTCH_RUN = NOTCH_D / tan(SLOPE);
module notch(y) translate([X_FRONT, y, 0]) rotate([90, 0, 90]) linear_extrude(WALL + 2, center = true)
    polygon([[0, LIP_Z + 1], [NOTCH_RUN, LIP_Z - NOTCH_D], [NOTCH_RUN + NOTCH_W, LIP_Z - NOTCH_D],
             [NOTCH_RUN + NOTCH_W, LIP_Z + 1]]);
NOTCHES = [for (f = [0.25, 0.5, 0.75]) L * f - (NOTCH_RUN + NOTCH_W) / 2];

module rail_mounted() difference() {
    rotate([90, 0, 0]) translate([0, 0, -L]) linear_extrude(L) profile2d();
    hole(10); hole(L - 10);
    for (y = NOTCHES) notch(y);
}

// as printed: standing on the y = L end
module rail_printed() rotate([-90, 0, 0]) translate([0, -L, 0]) rail_mounted();

// ---------- render props: a desk slab and three cables (not part of the product) ----------
module scene_desk() translate([-40, -30, 0]) cube([90, L + 60, 18]);
CABLES = [[6, 4.5], [11, 6.0], [16, 3.5]];          // [x, diameter]: USB-C, laptop, phone lead
module cable_run(p) cylinder(d = p[1], h = 1, $fn = 24);
module scene_cables() {
    for (c = CABLES) translate([c[0], -25, Z_FLOOR + R - R * 0.55 + c[1] / 2]) rotate([-90, 0, 0])
        cylinder(d = c[1], h = (c == CABLES[2] ? NOTCHES[1] + 25 + NOTCH_RUN + NOTCH_W / 2 : L + 50), $fn = 24);
    // the phone lead leaves through the middle notch and drops toward the floor
    let (c = CABLES[2], y = NOTCHES[1] + NOTCH_RUN + NOTCH_W / 2, z0 = Z_FLOOR + R - R * 0.55 + c[1] / 2) {
        hull() { translate([c[0], y, z0]) sphere(d = c[1], $fn = 24); translate([X_FRONT + 3, y, LIP_Z - NOTCH_D + c[1] / 2]) sphere(d = c[1], $fn = 24); }
        hull() { translate([X_FRONT + 3, y, LIP_Z - NOTCH_D + c[1] / 2]) sphere(d = c[1], $fn = 24); translate([X_FRONT + 8, y, -70]) sphere(d = c[1], $fn = 24); }
    }
}

if (part == "mounted") rail_mounted();
else if (part == "scene_desk") scene_desk();
else if (part == "scene_cables") scene_cables();
else rail_printed();
