// Cupid for the Giant Love Letter (2026-10-30). Scott: "make it a little more
// fun ... a cartoony Cupid that is a separate print that has a slight divot in
// the front of the envelope that it would set in"; then, on the first one, a
// flat stepped cut-out: "I want the Cupid to have depth to it. Make its
// features stick out ... Fix the wings also and make him look better."
//
// So he is sculpted relief: a domed head and belly, round arms and legs,
// puffy curls, cheeks, a nose and an ear on the curve of his face, and a
// feathered wing, a rounded upper wing with four long feathers fanning back
// from it. He draws a bow with a heart-tipped arrow, aimed up at the name,
// and wears a white wrap (school-appropriate) with a little heart on it.
//
// He prints face up, his back flat on the bed. Every shape that reaches his
// outline rises straight from the bed to its dome (col()), and every small
// feature sits on the curve of what is under it, so nothing hangs over air.
// Four filaments: skin, white, red, dark. Each colour is its shapes minus
// the shapes in front of them, so the colour parts never overlap.
//
// He sits in a pocket 1.0 deep in the envelope's front and presses onto two
// wedge pegs standing in it; his holes have crush ribs. About 55 x 60 and
// 10 tall, far over the small-parts size.
//
// Local frame: x across (he faces +x), y up, z out of the envelope.

$fn = 36;
HEAD = [2, 41]; HEAD_R = 11.5; HEAD_Z0 = 2.0; HEAD_RZ = 7.6;   // the head: top at 9.6
TORSO = [0, 20];
AIM = 22;                        // the bow and arrow tilt up toward the name
PIV = [4, 26];                   // ...about his chest
function aimp(p) = PIV + [[cos(AIM), -sin(AIM)], [sin(AIM), cos(AIM)]] * (p - PIV);
function p3(p, z) = [p.x, p.y, z];

// ---------- building blocks ----------
// a shape and everything under it down to the bed: a dome on a straight
// column, so it never overhangs. Children must be convex.
module col() hull() { children(); linear_extrude(0.01) projection() children(); }
module ell(c, r) translate(c) scale(r) sphere(1, $fn = 48);           // an ellipsoid
module caps(a, b, ra, rb = -1) hull() {                               // a rounded rod
    translate(a) sphere(ra);
    translate(b) sphere(rb < 0 ? ra : rb);
}
// the head's surface height over a point, for things set on the face
function head_z(p) = let (d = norm(p - HEAD) / HEAD_R) HEAD_Z0 + HEAD_RZ * sqrt(max(0, 1 - d * d));

// ---------- the wing: three rows of flat, overlapping feathers ----------
// Each feather is a pillow: its outline at full height with softly rounded
// edges, terraced on the 0.2 layer grid, so it prints as drawn. Where two
// feathers meet their rounded edges leave a crease between them. Back to
// front: long flight feathers, shorter ones over their roots, then the
// scalloped upper wing, the tallest. (Round rods read as fingers, 2026-10-30.)
module pillow(h, rr) for (z = [0.2 : 0.2 : h + 0.001]) let (u = z - (h - rr), inset = u <= 0 ? 0 : rr - sqrt(max(0, rr * rr - u * u)))
    translate([0, 0, -0.01]) linear_extrude(z + 0.01) offset(delta = -inset) children();
module feather2d(a, b, ra, rb) hull() { translate(a) circle(ra); translate(b) circle(rb); }
FLIGHT = [   // root, tip, root radius, tip radius: tips touching, as on a real wing
    [[-12, 36], [-26.5, 40.5], 3.2, 2.6],
    [[-13, 32.5], [-28.5, 35.2], 3.2, 2.7],
    [[-13, 29], [-28, 29.6], 3.1, 2.7],
    [[-12, 26], [-25.5, 24.0], 3.0, 2.6],
    [[-9.5, 24], [-21, 18.8], 2.9, 2.5]];
SECONDARY = [
    [[-9, 36], [-19.5, 39.6], 3.2, 2.5],
    [[-9.5, 32.5], [-21, 34.0], 3.2, 2.6],
    [[-9.5, 29], [-20.5, 28.8], 3.1, 2.5],
    [[-8.5, 26], [-18, 23.6], 3.0, 2.4]];
// the wing sweeps up and back from his shoulder, a cherub's wing
WING_AT = [-6, 32]; WING_TILT = -32;
module wing() translate(WING_AT) rotate(WING_TILT) translate(-WING_AT) union() {
    for (f = FLIGHT) pillow(1.6, 1.0) feather2d(f[0], f[1], f[2], f[3]);
    for (f = SECONDARY) pillow(2.4, 1.2) feather2d(f[0], f[1], f[2], f[3]);
    // the upper wing: a rounded shoulder with a scalloped lower edge
    pillow(3.4, 1.6) union() {
        hull() { translate([-6.5, 33]) circle(5.0); translate([-12.5, 38.5]) circle(4.2); translate([-17.5, 40.5]) circle(2.8); translate([-11.5, 31]) circle(4.0); }
        for (c = [[-17, 36.6], [-15, 32.4], [-12, 28.4], [-8.5, 27.5]]) translate(c) circle(2.4);
    }
}

// ---------- his body ----------
// chubby legs, the front one kicked forward, with little feet
module legs() {
    col() caps([-4.4, 11.0, 1.2], [-5.4, 6.4, 1.0], 4.4, 3.8);
    col() ell([-6.2, 3.6, 1.0], [3.4, 2.4, 2.4]);
    col() caps([4.8, 10.6, 1.2], [8.4, 6.8, 1.0], 4.4, 3.8);
    col() ell([10.6, 4.8, 1.0], [3.4, 2.4, 2.4]);
}
module torso() col() ell(p3(TORSO, 0), [9.8, 11, 6.6]);
// the wrap: the belly's dome 0.5 proud, round his lower half
module wrap() intersection() {
    col() ell(p3(TORSO, 0), [10.3, 11.5, 7.1]);
    translate([-20, -10, -1]) cube([40, TORSO.y - 2.5 + 10, 20]);
}
BOW_HAND = [19.5, 27]; DRAW_HAND = [4.5, 27.5];
module arms() {
    col() caps(p3(aimp([5.5, 25]), 5.6), p3(aimp(BOW_HAND), 4.6), 2.7, 2.4);
    col() ell(p3(aimp(BOW_HAND), 4.6), [2.9, 2.9, 2.6]);           // the bow hand
    col() caps(p3(aimp([-3, 25.5]), 5.8), p3(aimp(DRAW_HAND), 6.0), 2.8, 2.6);
    col() ell(p3(aimp(DRAW_HAND), 6.0), [3.0, 3.0, 2.6]);          // the drawing hand
}
module head() col() ell(p3(HEAD, HEAD_Z0), [HEAD_R, HEAD_R, HEAD_RZ]);
// the ear, at the back of his face, half under his hair
module ear() ell(p3(HEAD + [-6.6, -1.6], head_z(HEAD + [-6.6, -1.6]) - 0.4), [2.4, 3.0, 1.5]);
// a round nose at the front of his face
module nose() ell(p3(HEAD + [5.0, -2.2], head_z(HEAD + [5.0, -2.2]) - 0.3), [1.7, 1.4, 1.4]);
// hair: puffy curls in two rows over the top and back of his head
CURLS = concat([for (a = [62 : 22 : 216]) HEAD + 10.2 * [cos(a), sin(a)]],
               [for (a = [86 : 26 : 190]) HEAD + 6.0 * [cos(a), sin(a)]]);
module hair() union() {
    for (c = CURLS) col() ell(p3(c, head_z(c) - 0.5), [3.6, 3.6, 2.4]);
    col() ell(p3(HEAD + [4.0, 9.8], head_z(HEAD + [4.0, 9.8]) - 0.5), [3.0, 2.8, 2.2]);   // the forelock
}

// ---------- his face, on the curve of his head ----------
EYES = [HEAD + [2.0, 1.0], HEAD + [7.6, 1.2]];
module eyes() for (e = EYES) ell(p3(e, head_z(e) - 0.5), [1.4, 1.9, 1.2]);
module shine() for (e = EYES) ell(p3(e + [0.45, 0.7], head_z(e) + 0.55), [0.5, 0.5, 0.35]);
module cheeks() for (c = [HEAD + [-0.6, -4.0], HEAD + [9.4, -3.2]]) ell(p3(c, head_z(c) - 0.3), [1.9, 1.5, 0.9]);
module smile() for (i = [0 : 7]) let (t0 = -32 + i * 9, t1 = t0 + 9,
        a = HEAD + [4.8, -4.6] + 2.8 * [sin(t0), -cos(t0) * 0.6], b = HEAD + [4.8, -4.6] + 2.8 * [sin(t1), -cos(t1) * 0.6])
    caps(p3(a, head_z(a) - 0.2), p3(b, head_z(b) - 0.2), 0.5);

// ---------- the bow and the arrow ----------
BOW_C = [7, 27]; BOW_R = 13.2; BOW_A = 58;
function bow_pt(t) = aimp(BOW_C + BOW_R * [cos(t), sin(t)]);
function bow_tip(s) = bow_pt(s * BOW_A);
// the bow, a round rod bent in an arc, thicker at its grip
module bow() for (i = [0 : 11]) let (t0 = -BOW_A + i * 2 * BOW_A / 12, t1 = t0 + 2 * BOW_A / 12,
        r0 = 1.25 - 0.35 * abs(t0) / BOW_A, r1 = 1.25 - 0.35 * abs(t1) / BOW_A)
    col() caps(p3(bow_pt(t0), 1.6), p3(bow_pt(t1), 1.6), r0, r1);
module string() for (s = [-1, 1]) col() caps(p3(bow_tip(s), 1.0), p3(aimp(DRAW_HAND), 1.0), 0.6);
// the arrow lies along his hands, from behind the drawing hand out past the
// bow, dipping to the heart at its tip
ARROW_TAIL = [-1.5, 27.5]; ARROW_TIP = [33, 27];
module shaft() col() caps(p3(aimp(ARROW_TAIL), 8.0), p3(aimp(ARROW_TIP - [3, 0]), 3.6), 0.9);
module c_heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
// the heart point: a puffy heart, domed 1.6 over a 3.0 column
module arrowhead() translate(p3(aimp(ARROW_TIP), 0)) rotate(AIM + 90) intersection() {   // its point leads
    linear_extrude(10) c_heart2d(8.5);
    hull() { linear_extrude(3.0) offset(r = -1.2) c_heart2d(8.5); linear_extrude(0.01) c_heart2d(8.5); translate([0, 0, 4.6]) linear_extrude(0.01) offset(r = -3.0) c_heart2d(8.5); }
}
// the fletching: two feathers off the shaft's tail, on his chest
module fletch() for (s = [-1, 1]) col() scale([1, 1, 1]) caps(p3(aimp(ARROW_TAIL + [0.5, 0]), 8.2), p3(aimp(ARROW_TAIL + [-2.4, s * 3.0]), 8.0), 1.0, 0.8);
// a little heart on the wrap, 0.6 proud of its curve
module wrap_heart() intersection() {
    translate(p3(TORSO + [1.8, -6.0], -1)) linear_extrude(20) c_heart2d(5.0);
    translate([0, 0, 0.6]) intersection() {
        col() ell(p3(TORSO, 0), [10.3, 11.5, 7.1]);
        translate([-20, -10, -1]) cube([40, TORSO.y - 2.5 + 10, 20]);
    }
}

// ---------- the stack: shape and colour (0 skin, 1 white, 2 red, 3 dark) ----------
// in drawing order: each shape's colour part is itself minus everything after
// it, so the nearer shape keeps the overlap
C_COL = [1,    3,   3,    0,   0,    1,   0,    0,   0,   0,   3,   2,     3,    1,     0,   3,     3,     2,     2,     2];
//       wing  bow  str   legs torso wrap arms  head ear  nose hair cheeks eyes  shine  -    smile  shaft  fletch arrow  wrap-heart
module c_item(i) {
    if      (i == 0)  wing();
    else if (i == 1)  bow();
    else if (i == 2)  string();
    else if (i == 3)  legs();
    else if (i == 4)  torso();
    else if (i == 5)  wrap();
    else if (i == 6)  arms();
    else if (i == 7)  head();
    else if (i == 8)  ear();
    else if (i == 9)  nose();
    else if (i == 10) hair();
    else if (i == 11) cheeks();
    else if (i == 12) eyes();
    else if (i == 13) shine();
    else if (i == 15) smile();
    else if (i == 16) shaft();
    else if (i == 18) arrowhead();
    else if (i == 19) wrap_heart();
}
N_ITEMS = len(C_COL);
module c_part(i) difference() { c_item(i); for (j = [i + 1 : N_ITEMS - 1]) c_item(j); }
module cupid_body() union() for (i = [0 : N_ITEMS - 1]) c_item(i);
module cupid_outline() projection() cupid_body();

// his holes take the envelope's pegs; under his head and his middle, where he
// is thickest
PEGS = [HEAD + [-2, -1], TORSO + [-1, -5]];
// A peg is a wedge standing out of the upright wall: flat on top, its
// underside climbing from the wall at 37 deg, so it grows out of the wall
// layer by layer. A diamond peg began each one as a sliver in mid-air at its
// lower point, and the slicer propped both from the bed (2026-10-30).
PEG_W = 2.4;                     // across
PEG_L = 2.2;                     // how far it stands from the pocket floor
PEG_TIP = 1.6;                   // its height at the tip
PEG_ROOT = PEG_TIP + PEG_L / tan(37);   // and at the wall, 4.5
// the peg in his frame: x across, y up (top at y = 0), z out from the floor
module peg_shape(c = 0) hull() {
    translate([-PEG_W / 2 - c, -PEG_ROOT - c, 0]) cube([PEG_W + 2 * c, PEG_ROOT + 2 * c, 0.01]);
    translate([-PEG_W / 2 - c, -PEG_TIP - c, PEG_L + c - 0.01]) cube([PEG_W + 2 * c, PEG_TIP + 2 * c, 0.01]);
}
// where a peg's top edge sits, for a peg centred on p
function peg_at(p) = p + [0, PEG_ROOT / 2];
HOLE_C = 0.25;                   // clearance round the peg; the ribs take it up
RIB_R = 0.35; RIB_IN = 0.1;      // ribs on the side walls reach 0.1 into the peg
// His hole is the peg's full root height all the way in, straight-walled:
// the wedge's 37 deg underside is 53 deg in him, printed face up, and copying
// it drew 330 support moves (2026-10-30). The peg still sits on the hole's
// sides (the ribs), its top and its root.
HOLE = [PEG_W + 2 * HOLE_C, PEG_ROOT + 2 * HOLE_C];
HOLE_D = PEG_L + HOLE_C;
ROOF = (HOLE.x / 2) / tan(37);   // a hipped roof at 37 deg on every side
module cupid_hole() translate([0, HOLE_C - HOLE.y / 2, 0]) difference() {
    union() {
        translate([-HOLE.x / 2, -HOLE.y / 2, -0.01]) cube([HOLE.x, HOLE.y, HOLE_D + 0.01]);
        translate([0, 0, HOLE_D - 0.01]) hull() {
            translate([-HOLE.x / 2, -HOLE.y / 2, 0]) cube([HOLE.x, HOLE.y, 0.01]);
            translate([-0.01, -(HOLE.y / 2 - HOLE.x / 2), ROOF]) cube([0.02, HOLE.y - HOLE.x, 0.01]);
        }
        // the mouth opens 0.3 against the first layer's squash
        hull() {
            translate([-HOLE.x / 2 - 0.3, -HOLE.y / 2 - 0.3, -0.01]) cube([HOLE.x + 0.6, HOLE.y + 0.6, 0.01]);
            translate([-HOLE.x / 2, -HOLE.y / 2, 0.4]) cube([HOLE.x, HOLE.y, 0.01]);
        }
    }
    // crush ribs, two on each side wall, reaching RIB_IN into the peg
    for (sx = [-1, 1], y = [HOLE.y / 2 - HOLE_C - PEG_TIP * 0.3, HOLE.y / 2 - HOLE_C - PEG_TIP * 0.8])
        translate([sx * (PEG_W / 2 + RIB_R - RIB_IN), y, -1]) cylinder(r = RIB_R, h = HOLE_D + ROOF + 2, $fn = 16);
}


// ---------- the colour parts, as printed ----------
module cupid_colour(c) difference() {
    union() for (i = [0 : N_ITEMS - 1]) if (C_COL[i] == c && i != 14) c_part(i);
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
}
module cupid_skin()  cupid_colour(0);
module cupid_white() cupid_colour(1);
module cupid_red()   cupid_colour(2);
module cupid_dark()  cupid_colour(3);
// merged, for the gate
module cupid_print() difference() {
    cupid_body();
    for (p = PEGS) translate(peg_at(p)) cupid_hole();
}
