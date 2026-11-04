// The pegs that hold the white Cupid charm in his pocket on the Giant Love
// Letter, and the matching holes in his back (2026-11-04). Shared by
// cupid_white.scad (the holes) and love_letter.scad (the pegs), so the two
// can never drift apart. No BOSL2 here: love_letter.scad has its own front()
// and back(), which BOSL2's would replace.
//
// The charm is 3.0 thick and sits in a pocket 1.0 deep, so the pegs are short:
// 1.4 out of the pocket floor into holes 1.65 deep, leaving 1.35 of white over
// each hole. (The sculpted Cupid before him was 10 thick and took 2.2 pegs.)
//
// Frame: x across, y up, z out of the pocket floor (his back at z = 0).

// under his head and his middle, where he is widest, clear of every gap
PEGS = [[28.6, 47.1], [22.1, 25.5]];
// A peg is a wedge standing out of the upright wall: flat on top, its
// underside climbing from the wall at 37 deg, so it grows out of the wall
// layer by layer. A diamond peg began each one as a sliver in mid-air at its
// lower point, and the slicer propped both from the bed (2026-10-30).
PEG_W = 2.4;                     // across
PEG_L = 1.4;                     // how far it stands from the pocket floor
PEG_TIP = 1.6;                   // its height at the tip
PEG_ROOT = PEG_TIP + PEG_L / tan(37);   // and at the wall, 3.5
module peg_shape(c = 0) hull() {
    translate([-PEG_W / 2 - c, -PEG_ROOT - c, 0]) cube([PEG_W + 2 * c, PEG_ROOT + 2 * c, 0.01]);
    translate([-PEG_W / 2 - c, -PEG_TIP - c, PEG_L + c - 0.01]) cube([PEG_W + 2 * c, PEG_TIP + 2 * c, 0.01]);
}
// where a peg's top edge sits, for a peg centred on p
function peg_at(p) = p + [0, PEG_ROOT / 2];

HOLE_C = 0.25;                   // clearance round the peg; the ribs take it up
RIB_R = 0.35; RIB_IN = 0.1;      // ribs on the side walls reach 0.1 into the peg
// The hole is the peg's full root height all the way in, straight-walled: the
// wedge's 37 deg underside would be 53 deg in him, printed face up. Its
// ceiling is flat, a 2.9 bridge: the hipped roof the 10-thick Cupid's holes
// had rises 1.9 and would come out through a 3.0 charm.
HOLE = [PEG_W + 2 * HOLE_C, PEG_ROOT + 2 * HOLE_C];
HOLE_D = PEG_L + HOLE_C;
module cupid_hole() translate([0, HOLE_C - HOLE.y / 2, 0]) difference() {
    union() {
        translate([-HOLE.x / 2, -HOLE.y / 2, -0.01]) cube([HOLE.x, HOLE.y, HOLE_D + 0.01]);
        // the mouth opens 0.3 against the first layer's squash
        hull() {
            translate([-HOLE.x / 2 - 0.3, -HOLE.y / 2 - 0.3, -0.01]) cube([HOLE.x + 0.6, HOLE.y + 0.6, 0.01]);
            translate([-HOLE.x / 2, -HOLE.y / 2, 0.4]) cube([HOLE.x, HOLE.y, 0.01]);
        }
    }
    // crush ribs, two on each side wall, reaching RIB_IN into the peg
    for (sx = [-1, 1], y = [HOLE.y / 2 - HOLE_C - PEG_TIP * 0.3, HOLE.y / 2 - HOLE_C - PEG_TIP * 0.8])
        translate([sx * (PEG_W / 2 + RIB_R - RIB_IN), y, -1]) cylinder(r = RIB_R, h = HOLE_D + 2, $fn = 16);
}
module cupid_holes() for (p = PEGS) translate(peg_at(p)) cupid_hole();
