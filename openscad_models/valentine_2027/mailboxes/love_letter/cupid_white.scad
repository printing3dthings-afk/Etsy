// Cupid, white: a flat cut-out charm (2026-11-03).
//
// Scott, on the first sculpted draft: "Make it all one piece and just make it a
// 3d part but flat on the bottom side. It doesn't look good." He then sent a
// gold cut-out Cupid pendant as the look he wants. What makes that pendant read
// is its silhouette: a flat face, crisp edges, and every detail shown as a gap
// cut right through (between the wing and the head, the arms and the chest, the
// legs), never as lines scratched into the face. The second draft scratched its
// detail in and looked scarred; this one cuts it through.
//
// Drawn fresh in that style, not traced: a chubby cherub side-on, flying, with
// a feathered wing, both hands on a small bow and a heart-tipped arrow.
//
// PREVIEW: nothing on the envelope uses this yet.
//
// Millimetres, him facing +x, y up, his feet at y 0.

$fn = 64;
THICK = 3.0;      // the charm's thickness, flat face and flat back
EDGE  = 0.4;      // the top edge's round-over; the pendant's edges are crisp
GAP   = 0.8;      // a cut-through gap: two beads wide, so it prints open
LINE  = 1.2;      // the thinnest member (bowstring, bow tips): three beads

module cap(a, b, ra, rb = -1) hull() { translate(a) circle(ra); translate(b) circle(rb < 0 ? ra : rb); }
module chain(pts, r) for (i = [0 : len(pts) - 2]) cap(pts[i], pts[i + 1], r[i], r[i + 1]);

// ---------- the parts ----------
HC = [27, 44]; HR = 8.6;                      // a big round head, a third of him
module head2d() union() {
    translate(HC) circle(HR);
    translate([36.9, 43.0]) circle(1.4);     // his nose
    translate([33.0, 38.9]) circle(3.6);     // a full cheek
    translate([30.0, 36.2]) circle(2.6);     // the chin
}
// three soft curls over the top and back of his head, and one at the front
module hair2d() union() {
    for (a = [82, 122, 162]) translate(HC + (HR - 1.2) * [cos(a), sin(a)]) circle(3.2);
    translate([33.0, 50.8]) circle(2.2);                              // a curl on his brow
    cap([33.6, 51.6], [36.2, 51.8], 1.2, 0.9);                        // flicked forward
}
// a chubby body leaning into the shot
module body2d() union() {
    translate([24, 25.5]) rotate(-18) scale([7.8, 10.2]) circle(1);
    translate([28.0, 22.8]) circle(5.8);      // the belly
}
// the wing, swept up and back from his shoulder: a smooth top edge, four
// feathers fanned under it with notches between their tips
// [root, its radius, tip, its radius]: the top one is the leading edge
FEATHERS = [[[20.0, 38.0], 3.4, [6.0, 50.2], 2.7],
            [[19.0, 36.0], 3.1, [2.6, 43.6], 2.4],
            [[19.2, 33.8], 2.8, [4.4, 35.8], 2.1]];
module wing2d() for (f = FEATHERS) cap(f[0], f[2], f[1], f[3]);
// both arms forward at the shoulder: the near one out to the bow's grip, the
// far one drawing the string back to his cheek
GRIP = [42.6, 31.0];
NOCK = [35.4, 32.2];
module arms2d() union() {
    chain([[26, 32.6], [33, 30.8], [GRIP.x - 1.6, GRIP.y]], [3.1, 2.3, 2.0]);
    translate([GRIP.x - 1.4, GRIP.y]) circle(2.4);                   // the bow hand
    chain([[27.5, 30.4], [32, 33.4], [NOCK.x - 0.6, NOCK.y]], [2.6, 2.3, 2.0]);
    translate([NOCK.x - 0.4, NOCK.y]) circle(2.1);                   // the drawing hand
}
// legs trailing as he flies: the near knee under his belly, its shin folded
// back and the foot pointed down; the far leg out behind, its knee bent the
// way a knee bends (shin rising), the foot pointed on past it. (The first cut
// bent the far knee the wrong way and turned the near foot back to front:
// Scott, "legs backwards".)
module legs2d() union() { legs2d_near(); legs2d_far(); }
module legs2d_far() union() {
    chain([[21.6, 15.6], [13.6, 11.2], [7.4, 11.4]], [4.4, 3.2, 2.3]);
    cap([7.4, 11.4], [3.8, 10.2], 2.2, 1.7);
}

// ---------- the bow, its string and the arrow ----------
BOW_H = 15.5;                 // half its height
BOW_S = 5.2;                  // how far the grip bows out past the tips
BOW_R = (BOW_H * BOW_H + BOW_S * BOW_S) / (2 * BOW_S);
BOW_C = [GRIP.x + 1.2 - BOW_R, GRIP.y];
BOW_A = asin(BOW_H / BOW_R);
function bow_pt(t) = BOW_C + BOW_R * [cos(t), sin(t)];
module bow2d() union() {
    for (i = [0 : 15]) let (t0 = -BOW_A + i * 2 * BOW_A / 16, t1 = t0 + 2 * BOW_A / 16,
            w0 = 1.1 + 0.45 * (1 - abs(t0) / BOW_A), w1 = 1.1 + 0.45 * (1 - abs(t1) / BOW_A))
        cap(bow_pt(t0), bow_pt(t1), w0, w1);
    // its tips curl forward, as a recurve's do
    for (s = [-1, 1]) let (p = bow_pt(s * BOW_A)) cap(p, p + [2.2, s * 0.9], 1.1, 0.9);
}
module string2d() for (s = [-1, 1]) cap(bow_pt(s * BOW_A), NOCK, LINE / 2);
module heart2d(w) scale(w / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 48);
}
ARROW_Y = NOCK.y - 0.6;
module arrow2d() union() {
    cap([NOCK.x, ARROW_Y], [55.0, ARROW_Y], 0.75);
    translate([57.4, ARROW_Y]) rotate(-90) heart2d(6.4);           // the heart leads
}

// ---------- the gaps ----------
// A gap is the thin band just outside one part, cut through whatever lies
// behind it, but only where a mask allows, so the part stays joined to him
// at its root (a gap all the way round would set it loose).
module band(g = GAP) difference() { offset(delta = g) children(); children(); }
module gaps2d() union() {
    // the wing from the back of his head
    intersection() { band() union() { head2d(); hair2d(); } translate([8, 36]) square([17, 14]); }
    // the near arm from his chest and belly, open at the armpit
    intersection() { band() arms2d(); translate([27.5, 20]) square([12, 10.2]); }
    // the near leg from his belly and the far leg
    intersection() { band() legs2d_near(); translate([18, 4]) square([9.4, 14.6]); }
}
module legs2d_near() union() {
    chain([[27.8, 18.5], [31.0, 10.6], [26.6, 4.6]], [5.0, 3.4, 2.4]);
    cap([26.6, 4.6], [25.4, 1.4], 2.2, 1.6);
}

// the whole outline: inside corners filled 0.7 so the parts run together,
// the gaps cut, then outside corners eased 0.3
// (closed 0.25 after the cut: a gap's mask could leave a speck of a hole where
// it ended, and the slicer wrapped perimeters round it and left a void in the
// head, 23.7 mm3, 2026-11-03)
module cupid2d() offset(r = 0.3) offset(r = -0.3) offset(r = -0.25) offset(r = 0.25) difference() {
    offset(r = -0.7) offset(r = 0.7) union() {
        head2d(); hair2d(); body2d(); wing2d(); arms2d(); legs2d();
        bow2d(); string2d(); arrow2d();
    }
    gaps2d();
}

// ---------- the charm ----------
// The string and the arrow's shaft are under 1.6 wide; rounded over they would
// be a single bead on top (the gate's min wall, 0.87, 2026-11-03), so they
// stay square-edged to the top.
module slender2d() intersection() { cupid2d(); union() { string2d(); cap([NOCK.x + 2, ARROW_Y], [55.0, ARROW_Y], 0.75); } }
// Flat back, flat face; only the face's edge rounds over, EDGE in, on the 0.2
// layer grid.
function rise(z) = EDGE * (1 - sqrt(max(0, 1 - pow((z - (THICK - EDGE)) / EDGE, 2))));
module cupid_white() union() {
    linear_extrude(THICK - EDGE + 0.01) cupid2d();
    for (z = [THICK - EDGE + 0.2 : 0.2 : THICK + 0.001])
        translate([0, 0, z - 0.21]) linear_extrude(0.21) union() { offset(delta = -rise(z)) cupid2d(); slender2d(); }
}
cupid_white();
