// Cupid for the Giant Love Letter (2026-10-30). Scott: "make it a little more
// fun ... a cartoony Cupid that is a separate print that has a slight divot in
// the front of the envelope that it would set in"; he picked that and heart
// stickers. A chubby cherub with curls, small white wings and a white wrap
// (school-appropriate), drawing a red bow with a heart-tipped arrow, aimed up
// at the child's name.
//
// He prints face up, his back flat on the bed. He is a stepped cut-out: each
// shape stands at its own height in its own colour, the nearer ones taller, so
// every level edge is on the 0.2 layer grid and the colours change only where
// the shapes meet. Four filaments: skin, white, red, dark.
//
// He sits in a pocket 1.0 deep in the envelope's front and presses onto two
// diamond pegs standing in it. His holes have crush ribs, so the fit is snug
// whatever the printer's hole shrinkage; a drop of glue makes it permanent.
// About 55 x 62, far over the small-parts size.
//
// Local frame: x across (he faces +x), y up, z out of the envelope.


// ---------- his shapes, in 2D ----------
HEAD = [2, 41]; HEAD_R = 11.5;
TORSO = [0, 20];
AIM = 22;                        // the bow and arrow tilt up toward the name
PIV = [4, 26];                   // ...about his chest
module aimed() translate(PIV) rotate(AIM) translate(-PIV) children();
function aimp(p) = PIV + [[cos(AIM), -sin(AIM)], [sin(AIM), cos(AIM)]] * (p - PIV);
module capsule(a, b, r) hull() { translate(a) circle(r, $fn = 40); translate(b) circle(r, $fn = 40); }
module ellipse(c, rx, ry, a = 0) translate(c) rotate(a) scale([rx, ry]) circle(1, $fn = 72);

module c_head() translate(HEAD) circle(HEAD_R, $fn = 96);
// curls round the top and back of his head, and one on his forehead
CURLS = [for (a = [72 : 26 : 202]) [HEAD + 10.6 * [cos(a), sin(a)], 3.6]];
module c_hair() union() {
    for (c = CURLS) translate(c[0]) circle(c[1], $fn = 40);
    intersection() { translate(HEAD) circle(HEAD_R + 0.2, $fn = 96); translate(HEAD + [-5.5, 7.5]) circle(9.0, $fn = 80); }
    translate(HEAD + [4.8, 10.2]) circle(2.6, $fn = 36);
}
module c_torso() ellipse(TORSO, 9.8, 11, 0);
module c_wrap() intersection() {        // his white wrap, round his middle
    offset(delta = 0.01) c_torso();
    translate([-20, -10]) square([40, TORSO.y - 2.5 + 10]);
}
module c_legs() { ellipse([-4.8, 8.2], 4.2, 5.4, -12); ellipse([5.0, 7.8], 4.2, 5.4, 14); }
// wings on his back: three feathers each, the upper wing then the lower
module c_wings() union() {
    for (f = [[[-9, 31], [-21, 41], 3.6], [[-9, 28], [-24, 33], 3.4], [[-9, 25], [-22, 25], 3.2]]) capsule(f[0], f[1], f[2]);
}
module c_wing_lines() for (f = [[[-12, 33.2], [-19, 38.6]], [[-12, 29.6], [-21, 32.0]], [[-12, 26.4], [-20, 25.8]]]) capsule(f[0], f[1], 0.45);
// the bow hand holds the bow out in front; the other hand draws the string
BOW_HAND = [19.5, 27]; DRAW_HAND = [4.5, 27.5];
module c_arms() aimed() { capsule([5.5, 25], BOW_HAND, 2.4); capsule([-3, 25.5], DRAW_HAND, 2.5); }
BOW_C = [7, 27]; BOW_R = 13.2; BOW_A = 58;
module c_bow() aimed() difference() {
    translate(BOW_C) intersection() {
        difference() { circle(BOW_R + 0.9, $fn = 120); circle(BOW_R - 0.9, $fn = 120); }
        polygon([[0, 0], [40 * cos(BOW_A), -40 * sin(BOW_A)], [40, 0], [40 * cos(BOW_A), 40 * sin(BOW_A)]]);
    }
}
function bow_tip(s) = BOW_C + BOW_R * [cos(BOW_A), s * sin(BOW_A)];
module c_string() aimed() { capsule(bow_tip(1), DRAW_HAND, 0.6); capsule(bow_tip(-1), DRAW_HAND, 0.6); }
module c_heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
ARROW_TIP = [33, 27];
module c_shaft() aimed() capsule([0.5, 27.5], ARROW_TIP - [3, 0], 0.8);
module c_arrowhead() aimed() translate(ARROW_TIP) rotate(-90) c_heart2d(8.5);
module c_fletch() aimed() for (s = [-1, 1]) polygon([[-1.8, 27.5], [2.4, 27.5], [-0.6, 27.5 + s * 3.0], [-3.4, 27.5 + s * 3.0]]);
// his face looks along the arrow: eyes, a smile, rosy cheeks
module c_eyes() for (e = [[4.2, -0.6], [9.6, -0.4]]) ellipse(HEAD + e, 1.3, 1.8);
module c_shine() for (e = [[4.6, 0.3], [10.0, 0.5]]) translate(HEAD + e) circle(0.45, $fn = 20);
module c_smile() for (i = [0 : 7]) let (t0 = -30 + i * 10, t1 = t0 + 10)
    capsule(HEAD + [7, -3.4] + 3.2 * [sin(t0), -cos(t0) * 0.6], HEAD + [7, -3.4] + 3.2 * [sin(t1), -cos(t1) * 0.6], 0.45);
module c_wrap_heart() translate(TORSO + [1.5, -5.5]) c_heart2d(4.6);
module c_cheeks() { translate(HEAD + [10.4, -4.4]) circle(1.5, $fn = 30); translate(HEAD + [1.0, -4.8]) circle(1.6, $fn = 30); }

// ---------- the stack: shape, height, colour (0 skin, 1 white, 2 red, 3 dark) ----------
// a point's column is the colour of the tallest shape over it, at that height
//         wings bow  str  legs torso wrap arms fletch shaft head head eyes smile shine cheeks hair wrap-heart
C_H   = [3.0,  3.6, 2.6, 4.6, 5.2,  5.6, 5.8, 6.2,   6.0,  6.0, 6.2, 6.4, 6.4,  6.4,  6.4,   6.8, 6.0];
C_COL = [1,    3,   3,   0,   0,    1,   0,   2,     3,    2,   0,   3,   3,    1,    2,     3,   2];
module c_item(i) {
    if      (i == 0)  c_wings();
    else if (i == 1)  c_bow();
    else if (i == 2)  c_string();
    else if (i == 3)  c_legs();
    else if (i == 4)  c_torso();
    else if (i == 5)  c_wrap();
    else if (i == 6)  c_arms();
    else if (i == 7)  c_fletch();
    else if (i == 8)  c_shaft();
    else if (i == 9)  c_arrowhead();
    else if (i == 10) c_head();
    else if (i == 11) c_eyes();
    else if (i == 12) c_smile();
    else if (i == 13) c_shine();
    else if (i == 14) c_cheeks();
    else if (i == 15) c_hair();
    else if (i == 16) c_wrap_heart();
}
module c_column(i) difference() {
    c_item(i);
    for (j = [0 : len(C_H) - 1]) if (j != i && (C_H[j] > C_H[i] || (C_H[j] == C_H[i] && j > i))) c_item(j);
}
module cupid_outline() union() for (i = [0 : len(C_H) - 1]) c_item(i);
// the feathers' lines are grooves 0.4 deep, 0.9 wide, cut into the wings' top
module wing_grooves() translate([0, 0, C_H[0] - 0.4]) linear_extrude(1) c_wing_lines();
// his holes take the envelope's pegs; under his head and his middle, where he
// is thickest
PEGS = [HEAD + [-2, -1], TORSO + [-1, -2]];
PEG = [2.4, 3.2];                // the peg's diamond: across, up. Its faces are
                                 // 37 deg off upright, so it prints on the wall
PEG_L = 2.2;                     // how far it stands from the pocket floor
module diamond(d) polygon([[-d.x / 2, 0], [0, d.y / 2], [d.x / 2, 0], [0, -d.y / 2]]);
HOLE_C = 0.25;                   // clearance round the peg; the ribs take it up
RIB_R = 0.35; RIB_IN = 0.1;      // a rib on each face reaches 0.1 into the peg
module hole2d() difference() {
    offset(delta = HOLE_C) diamond(PEG);
    for (sx = [-1, 1], sy = [-1, 1]) let (n = [sx * PEG.y, sy * PEG.x] / norm(PEG))
        translate([sx * PEG.x / 4, sy * PEG.y / 4] + n * (RIB_R - RIB_IN)) circle(RIB_R, $fn = 16);
}
module cupid_hole() {
    linear_extrude(PEG_L + 0.3) hole2d();
    // the roof closes at 36 deg instead of a flat ceiling
    translate([0, 0, PEG_L + 0.3 - 0.01]) linear_extrude(1.6, scale = 0.02) offset(delta = HOLE_C) diamond(PEG);
    // the mouth opens 0.3 against the first layer's squash
    hull() { linear_extrude(0.01) offset(delta = HOLE_C + 0.3) diamond(PEG); translate([0, 0, 0.4]) linear_extrude(0.01) offset(delta = HOLE_C) diamond(PEG); }
}

// ---------- the colour parts, as printed ----------
module cupid_colour(c) difference() {
    union() for (i = [0 : len(C_H) - 1]) if (C_COL[i] == c) linear_extrude(C_H[i]) c_column(i);
    for (p = PEGS) translate(p) cupid_hole();
    wing_grooves();
}
module cupid_skin()  cupid_colour(0);
module cupid_white() cupid_colour(1);
module cupid_red()   cupid_colour(2);
module cupid_dark()  cupid_colour(3);
// merged, for the gate: every shape at full height overlaps the next, so the
// union closes
module cupid_print() difference() {
    union() for (i = [0 : len(C_H) - 1]) linear_extrude(C_H[i]) c_item(i);
    for (p = PEGS) translate(p) cupid_hole();
    wing_grooves();
}
