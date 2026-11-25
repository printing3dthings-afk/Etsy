// "Trophy Rack" medallion, v3 (2026-11-25), beside v2 (../trophy_rack.scad, unchanged).
// Scott printed v2: "the nipples need to be way shorter so they don't break off. Make sure the
// ring for the keychain is really strong. I need this to be a very high quality product." So:
//   - each tip is a low rounded nub blended into its dome (v2: a 3.2 mm peg standing 4.2 off it);
//   - the keychain tab is the rim's full height, 5.0 (v2: 3.0), its ring 3.2 wide round the
//     hole (v2: 2.0), its neck to the shield wider, and the hole's edges chamfered.
//
// The original v2 note follows.
// "Trophy Rack" medallion (2026-11-14): Scott's photos of a Mardi Gras bead pendant, to
// be reproduced as close to it as printing allows. A badge-shaped shield with a black rim
// and a hanging tab, a yellow field, two domes with red tips, and a white banner across
// the bottom reading TROPHY RACK, its letters laid along the banner's curve
// (banner_data.scad, from make_banner.py).
//
// Prints flat on its back, everything facing up, no supports. Four colours, one part
// each, none overlapping:
//   part = "black" (rim, back, tab, lettering) | "yellow" | "skin" (domes and tips) | "white" | "all"
// The tips are skin colour, not red: Scott's pick (2026-11-14), so it fits one 4-slot AMS.

include <banner_data.scad>

part = "all";
$fn = 96;

RIM_W   = 2.4;      // the black rim's width
RIM_TOP = 5.0;      // the rim's top
BACK    = 1.6;      // black under the field
FIELD   = 3.6;      // the yellow field's top
BANNER_TOP = 10.6;  // the front band's top: above the domes where it crosses them. The domes
                    // rise 7.0 over the band's footprint (computed); at 8.0 and 9.5 the right
                    // dome showed a cut face above the band
BAND_ROUND = 1.2;   // its top edges rounded over
TAIL_TOP = 5.4;     // the tails, folded behind the band, stand lower
LETTER_H = 0.8;     // lettering raised above the banner
TAB_T   = 5.0;      // the hanging tab: the rim's full height (v2 3.0). A pull loads it in the
                    // print plane, the strong way; out of plane it is 4.6x stiffer than v2's
HOLE_R  = 2.25;     // 4.5 across: a split ring or a jump ring threads it
RING_W  = 3.2;      // plastic round the hole: eight beads (v2 2.0: 6 mm2 at the ring's top
                    // was the part's thinnest section, fragility.py; now 3.2 x 5.0 = 16 mm2)
HOLE_CH = 0.6;      // the hole's edges chamfered: no sharp edge for the ring to bear on
DOME_R  = 12.2;     // each dome's base radius
DOME_H  = 10.6;     // its height above the field
DOME_X  = 12.0;     // centres at +/- this
DOME_Y  = 4.5;
TIP_R   = 1.9;      // the tip's rounded top
TIP_OUT = 1.6;      // how far it stands off the dome (v2: 4.2, and they broke off)
TIP_BASE = 3.2;     // its foot, sunk into the dome: the nub flares out into it
TIP_TILT = 25;      // the tips point down the badge a little, as on the photo (25 deg off vertical prints)
DOME_SAG = 0.08;    // the domes lean down the badge: their tops sit 0.8 mm low

// the shield: a badge with raised top corners, a notch in each side, a pointed bottom
function qbez(a, b, c, n) = [for (i = [0 : n]) let (t = i / n) (1 - t) * (1 - t) * a + 2 * (1 - t) * t * b + t * t * c];
RIGHT = concat(
    [[0, 27.6], [6, 27.3], [14, 26.6], [22, 26.8], [28, 28.2], [32.2, 30.6], [31.2, 24.0], [31.0, 17.6],
     [29.2, 15.9], [29.8, 13.6]],
    qbez([29.8, 13.6], [30.4, -21.0], [0, -32.0], 24));
SHIELD = concat(RIGHT, [for (i = [len(RIGHT) - 2 : -1 : 1]) [-RIGHT[i][0], RIGHT[i][1]]]);
module shield2d() polygon(SHIELD);
module inner2d() offset(r = -RIM_W) shield2d();
module banner2d() polygon(BANNER);
// the swallowtails' points rounded to 0.8: sharp, they ran to nothing (gate min_wall 0.00)
module tails2d() for (t = TAILS) offset(r = 0.8) offset(delta = -0.8) polygon(t);
module ribbon2d() { banner2d(); tails2d(); }

// a rounded tab on the top edge, as on the photo; v3 a wider, thicker neck into the shield
HOLE_Y = 32.0;
TAB_R = HOLE_R + RING_W;
module tab2d() hull() { translate([0, HOLE_Y]) circle(r = TAB_R); translate([-8, 24]) square([16, 1]); }
module hole_cut() translate([0, HOLE_Y, 0]) {
    translate([0, 0, -1]) cylinder(r = HOLE_R, h = TAB_T + 2);
    // the bed-side chamfer overhangs the hole as it narrows: 40 deg, not 45 (the gate fails at 45)
    translate([0, 0, -0.01]) cylinder(r1 = HOLE_R + HOLE_CH, r2 = HOLE_R, h = HOLE_CH * 1.2);
    translate([0, 0, TAB_T - HOLE_CH + 0.01]) cylinder(r1 = HOLE_R, r2 = HOLE_R + HOLE_CH, h = HOLE_CH);
}
module tab() difference() { linear_extrude(TAB_T) tab2d(); hole_cut(); }
module banner_prism() translate([0, 0, -1]) linear_extrude(BANNER_TOP + 30) ribbon2d();

module domes() for (s = [-1, 1]) translate([s * DOME_X, DOME_Y, FIELD])
    intersection() {
        multmatrix([[1, 0, 0, 0], [0, 1, -DOME_SAG, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
            scale([1, 1, DOME_H / DOME_R]) sphere(r = DOME_R);
        translate([-DOME_R, -DOME_R, 0]) cube([2 * DOME_R, 2 * DOME_R, DOME_R]);
    }
// each tip a short rounded peg standing straight up from just below the dome's top
// set a little low and toward the middle, as on the photo
TIP_DX = 1.2; TIP_DY = 1.8;
// (the dome's surface there, before the sag moves it down the badge with height)
TIP_ZL = DOME_H * sqrt(1 - (TIP_DX * TIP_DX + TIP_DY * TIP_DY) / (DOME_R * DOME_R));
module tips() for (s = [-1, 1])
    translate([s * (DOME_X - TIP_DX), DOME_Y - TIP_DY - DOME_SAG * TIP_ZL, FIELD + TIP_ZL]) rotate([TIP_TILT, 0, 0])
        hull() {
            translate([0, 0, -1.6]) cylinder(r = TIP_BASE, h = 0.01, $fn = 64);   // the foot, inside the dome
            translate([0, 0, TIP_OUT - TIP_R]) sphere(r = TIP_R, $fn = 64);       // the rounded top
        }

// Strokes grown 0.22 a side: Playfair's hairlines and serifs, 0.2-0.28 mm here, were thinner
// than one bead and the slice dropped them (print fidelity, 2026-11-14). The photo's letters
// are chunky anyway.
LETTER_GROW = 0.22;
module letters2d() offset(r = LETTER_GROW) for (L = LETTERS) translate([L[1], L[2]]) rotate(L[3]) scale([XSCALE, 1])
    text(L[0], size = SIZE, font = FONT, halign = "center", valign = "baseline");

module black() {
    difference() {
        union() {
            linear_extrude(RIM_TOP) shield2d();
            tab();
        }
        translate([0, 0, BACK]) linear_extrude(RIM_TOP) inner2d();
        hole_cut();
        banner_prism();
    }
    // on the band's flat top only, clear of its rounded edges
    translate([0, 0, BANNER_TOP]) linear_extrude(LETTER_H) intersection() { letters2d(); offset(delta = -BAND_ROUND) banner2d(); }
}
module yellow() difference() {
    translate([0, 0, BACK]) linear_extrude(FIELD - BACK) inner2d();
    banner_prism();
}
module skin() difference() { union() { domes(); tips(); } banner_prism(); }
// the front band, its top edges rounded over in steps (0.2 mm layers can't show finer)
module band() for (k = [0 : 6]) let (a = 90 * k / 6)
    linear_extrude(BANNER_TOP - BAND_ROUND + BAND_ROUND * sin(a)) offset(delta = -BAND_ROUND * (1 - cos(a))) banner2d();
module white() { band(); linear_extrude(TAIL_TOP) tails2d(); }

if (part == "black") black();
else if (part == "yellow") yellow();
else if (part == "skin") skin();
else if (part == "white") white();
// the raised lettering alone: declared to the gate's wall check as detail (print_fidelity checks it)
else if (part == "letters") translate([0, 0, BANNER_TOP]) linear_extrude(LETTER_H) intersection() { letters2d(); offset(delta = -BAND_ROUND) banner2d(); }
else if (part == "union") union() { black(); yellow(); skin(); white(); }   // one solid, for the product gate
else {
    color("#1A1A1A") black();
    color("#E8C21A") yellow();
    color("#E7A976") skin();
    color("#F2EDE2") white();
}
