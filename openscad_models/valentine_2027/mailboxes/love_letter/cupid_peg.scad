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
// One crush rib down each side of the peg, reaching RIB_IN into his hole's
// wall. A ridge, not a round: it lies along the peg, so on the upright
// envelope its underside climbs at 37 deg and its top is flat.
RIB_OUT = 0.45; RIB_IN = RIB_OUT - 0.25;   // 0.2 into the hole's wall (HOLE_C is 0.25)
RIB_Y = -1.2;                    // its foot, below the peg's flat top
module peg_shape(c = 0) union() {
    hull() {
        translate([-PEG_W / 2 - c, -PEG_ROOT - c, 0]) cube([PEG_W + 2 * c, PEG_ROOT + 2 * c, 0.01]);
        translate([-PEG_W / 2 - c, -PEG_TIP - c, PEG_L + c - 0.01]) cube([PEG_W + 2 * c, PEG_TIP + 2 * c, 0.01]);
    }
    for (sx = [-1, 1]) scale([sx, 1, 1]) translate([PEG_W / 2 - 0.01, 0, 0])
        linear_extrude(PEG_L) polygon([[0, RIB_Y], [RIB_OUT + 0.01, RIB_Y + RIB_OUT / tan(37)], [0, RIB_Y + RIB_OUT / tan(37)]]);
}
// where a peg's top edge sits, for a peg centred on p
function peg_at(p) = p + [0, PEG_ROOT / 2];

HOLE_C = 0.25;                   // clearance round the peg; its ribs take it up
// The hole is the peg's full root height all the way in, straight-walled: the
// wedge's 37 deg underside would be 53 deg in him, printed face up. Its
// ceiling is flat, a 2.9 bridge: the hipped roof the 10-thick Cupid's holes
// had rises 1.9 and would come out through a 3.0 charm. No ribs in the hole:
// in a 3 mm charm its 0.7 ribs were enough of him to fail the wall gate (1st
// percentile 1.01 against 1.2, 2026-11-04), so the ribs are on the peg.
HOLE = [PEG_W + 2 * HOLE_C, PEG_ROOT + 2 * HOLE_C];
HOLE_D = PEG_L + HOLE_C;
module cupid_hole() translate([0, HOLE_C - HOLE.y / 2, 0]) union() {
    translate([-HOLE.x / 2, -HOLE.y / 2, -0.01]) cube([HOLE.x, HOLE.y, HOLE_D + 0.01]);
    // the mouth opens 0.3 against the first layer's squash
    hull() {
        translate([-HOLE.x / 2 - 0.3, -HOLE.y / 2 - 0.3, -0.01]) cube([HOLE.x + 0.6, HOLE.y + 0.6, 0.01]);
        translate([-HOLE.x / 2, -HOLE.y / 2, 0.4]) cube([HOLE.x, HOLE.y, 0.01]);
    }
}
module cupid_holes() for (p = PEGS) translate(peg_at(p)) cupid_hole();
