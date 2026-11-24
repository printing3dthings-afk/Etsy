// Modular desk organizer: butterfly-key joint coupon (2026-11-24).
// Scott picked butterfly keys (2026-11-24) from the five in OPTIONS.md. Before any module is
// built, this sets the key's fit (ENGINEERING.md, handbook section 7: the joint first).
//
// Print: two copies of `block` (the second turned round so the pockets face) and three keys,
// one per clearance, marked by notches in the key's top: one notch 0.2, two 0.25, three 0.3.
// The block is one grid unit (40 mm) of a module's 2.0 wall, with the pocket's boss exactly as
// every module will carry it.
//
//   part = block | key_0.2 | key_0.25 | key_0.3 | plate (all five, laid out) | joined (preview)

part = "plate";
U = 40;            // the grid unit
BH = 10;           // the coupon block's height: the pocket and a 2 mm floor under it
WALL = 2.0;        // five beads
FLOOR = 1.6;
R = 4;
// the key: a bow-tie, waist at the joint. The flanks run 25 deg off the key's length:
// play along the joint is clearance / sin(flank) at each pocket, so a steep flank keeps the
// modules tight (17 deg in the concept sketch gave 3.3 x clearance a pocket; 25 deg gives 2.4 x)
KEY_L = 16;        // across the joint: 8 into each module
KEY_W = 12;        // the wings' width
KEY_N = 4.5;       // the waist
KEY_D = 8;         // the pocket's depth: 16 on a real module; the fit is the same at 8, and
                   // at 16 the coupon plate sliced at 42 m, over the 30-minute limit
KEY_PROUD = 1.5;   // the key stands this far above the rim: a fingernail lifts it out
BOSS = 3.2;        // wall round the pocket, eight beads
$fn = 48;

module rbox(w, d, h, r = R) linear_extrude(h) offset(r) offset(-r) square([w, d]);
module key2d(cl = 0) offset(delta = cl) polygon([[-KEY_L / 2, -KEY_W / 2], [-KEY_L / 2, KEY_W / 2], [0, KEY_N / 2],
                                                 [KEY_L / 2, KEY_W / 2], [KEY_L / 2, -KEY_W / 2], [0, -KEY_N / 2]]);

// one grid unit's wall, the pocket on its +x face at the unit's middle: the module's wall and
// the boss exactly as a module carries them, without the rest of the bin (a whole 40 x 40 bin
// pair sliced at 1 h 22 m, over the 30-minute coupon limit). Two 10 mm returns keep it standing.
module block() difference() {
    union() {
        translate([U - WALL, 0, 0]) cube([WALL, U, BH]);
        for (y = [0, U - WALL]) translate([U - 10, y, 0]) cube([10, WALL, BH]);
        translate([U - KEY_L / 2 - BOSS, U / 2 - KEY_W / 2 - BOSS, 0]) cube([KEY_L / 2 + BOSS, KEY_W + 2 * BOSS, BH]);
    }
    translate([U, U / 2, BH - KEY_D]) linear_extrude(KEY_D + 1) key2d(0);   // cut at nominal: the key carries the clearance
}

// the key, shrunk by its clearance all round; notches in its top say which
module key(cl) difference() {
    linear_extrude(KEY_D + KEY_PROUD - 0.2) key2d(-cl);
    n = round((cl - 0.15) / 0.05);
    for (k = [1 : n]) translate([-KEY_L / 2 - 1, (k - (n + 1) / 2) * 2.2 - 0.4, KEY_D + KEY_PROUD - 0.8]) cube([3, 0.8, 1]);
}

if      (part == "block") block();
else if (part == "key_0.2") key(0.2);
else if (part == "key_0.25") key(0.25);
else if (part == "key_0.3") key(0.3);
else if (part == "plate") {
    block();
    translate([2 * U + 10, U, 0]) rotate(180) block();
    for (i = [0 : 2]) translate([U + 5, -12 - 16 * i, 0]) key([0.2, 0.25, 0.3][i]);
}
else if (part == "joined") {
    color("#EDE8DC") block();
    color("#9EB898") translate([2 * U, U, 0]) rotate(180) block();
    color("#C83238") translate([U, U / 2, BH - KEY_D + 0.2]) key(0.25);
}
