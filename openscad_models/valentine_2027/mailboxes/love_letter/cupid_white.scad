// Cupid, white, after Scott's reference (2026-11-03): the classic cherub
// archer in profile, mid-flight, back leg kicked out, wing swept up behind, a
// tall bow held out at arm's length with the string drawn to his cheek. Drawn
// fresh in that pose, not traced.
//
// One piece (Scott, on the first draft built from separate rounded parts: "Make
// it all one piece and just make it a 3d part but flat on the bottom side. It
// doesn't look good."), then in the style of a cut-out pendant he sent: a flat
// piece with crisp, softly rounded edges, its detail cut in as fine lines
// rather than modelled: where the wing, arm and legs lie on the body, the
// feathers, the hairline, the eye. A heart tips the arrow.
//
// PREVIEW: nothing on the envelope uses this yet.
//
// Laid out on a 0.081 mm grid, x across with him facing +x, y up.

$fn = 48;
S = 0.081;
function M(p) = [(p.x - 80) * S, (1360 - p.y) * S];          // grid to mm
module C(p, r) translate(M(p)) circle(r * S);                 // a circle on the grid
module cap(a, b, ra, rb = -1) hull() { C(a, ra); C(b, rb < 0 ? ra : rb); }
module ellg(p, rx, ry, a = 0) translate(M(p)) rotate(a) scale([rx * S, ry * S]) circle(1);

// ---------- his shapes, in 2D ----------
HC = [420, 768]; HR = 108;
CURLS = [[338, 808], [330, 745], [350, 700], [392, 672], [440, 664], [484, 680], [350, 852]];
FORELOCK = [512, 688];
module head2d() union() {
    C(HC, HR);
    C([528, 815], 20);                 // the nose
    C([480, 850], 42);                 // the cheek
    C([462, 878], 24);                 // the chin
}
module hair2d() union() {
    for (c = CURLS) C(c, 34);
    intersection() { C(HC, HR + 2); C([390, 735], 95); }
    hull() { C(FORELOCK, 20); C([540, 676], 9); }      // a curl flicked up over his brow
}
module torso2d() union() { ellg([335, 1005], 122, 128, -15); C([400, 1045], 72); }
WING_A = [[120, 742], 28, [245, 838], 40];
WING_B = [[148, 818], 34, [268, 862], 44];
WING_C = [[192, 895], 32, [292, 905], 42];
module lobe(w) hull() { C(w[0], w[1]); C(w[2], w[3]); }
// held clear of his curls: the wing meets his back below them, with a notch
module covert2d() hull() { C([300, 880], 44); C([250, 830], 30); C([190, 775], 18); }
module wing2d() union() { lobe(WING_A); lobe(WING_B); lobe(WING_C); covert2d(); }
module bow_arm2d() union() { cap([420, 945], [700, 945], 30, 23); C([712, 940], 28); }
module draw_arm2d() union() { cap([420, 915], [498, 893], 31, 27); C([505, 893], 27); }
module back_leg2d() union() { cap([270, 1110], [165, 1165], 54, 46); cap([165, 1165], [105, 1215], 42, 32); C([98, 1228], 30); }
module front_leg2d() union() { cap([360, 1110], [395, 1225], 62, 46); cap([395, 1225], [375, 1300], 46, 34); cap([370, 1318], [440, 1335], 30, 22); }
// the figure: every part in one outline, its inside corners filleted 2.0 and
// its outside ones rounded 1.2, so the parts run into each other
module figure2d() offset(r = 0.8) offset(r = -0.8) offset(r = -1.2) offset(r = 1.2) union() {
    head2d(); hair2d(); torso2d(); wing2d(); bow_arm2d(); draw_arm2d(); back_leg2d(); front_leg2d();
}
// the bow, its string and the arrow
BOW_C = [370, 915]; BOW_R = 350; BOW_A = 45.6;
function bow_pt(t) = BOW_C + BOW_R * [cos(t), sin(t)];
module bow2d() union() {
    for (i = [0 : 15]) let (t0 = -BOW_A + i * 2 * BOW_A / 16, t1 = t0 + 2 * BOW_A / 16,
            w0 = 15 - 4 * abs(t0) / BOW_A, w1 = 15 - 4 * abs(t1) / BOW_A)
        cap(bow_pt(t0), bow_pt(t1), w0, w1);
    for (s = [-1, 1]) C(bow_pt(s * BOW_A), 16);
}
module string2d() for (s = [-1, 1]) cap(bow_pt(s * BOW_A), [505, 890], 7.5);
// the arrow, a heart at its tip pointing on
module heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
module arrow2d() union() {
    cap([500, 890], [780, 890], 10);
    translate(M([800, 890])) rotate(90) heart2d(7.0);     // its point leads
}
module tackle2d() offset(r = 0.5) offset(r = -0.5) union() { bow2d(); string2d(); arrow2d(); }

// ---------- one shape: the outline inflated, flat behind ----------
// At height z the outline is drawn in by rise(z), a quarter round of radius rr
// rising to h; every level is on the 0.2 grid.
function rise(z, h, rr) = rr * (1 - sqrt(max(0, 1 - (z / h) * (z / h))));
module inflate(h, rr) for (z = [0.2 : 0.2 : h + 0.001])
    translate([0, 0, -0.01]) linear_extrude(z + 0.01) offset(delta = -rise(z, h, rr)) children();
FIG_H = 3.0; FIG_R = 0.8;        // a flat piece 3.0 thick, its top edge rounded over 0.8
TACK_H = 3.0; TACK_R = 0.6;      // the bow, string and arrow in the same plane
module body3d() union() {
    inflate(FIG_H, FIG_R) figure2d();
    inflate(TACK_H, TACK_R) tackle2d();
}

// ---------- the carved lines ----------
// A few strokes, placed by hand as an illustrator would: where the feathers
// lie on each other, the hairline and ear, the closed eye, the arm's edge on
// his chest and where his legs part. 0.8 wide, 0.6 into the surface wherever
// it runs. (Lines taken from every edge of every part made loops and scribbles.)
module stroke(pts, w = 4.6) for (i = [0 : len(pts) - 2]) cap(pts[i], pts[i + 1], w);
module lines2d() union() {
    // the wing: its edge on his back, and three cuts between its feathers
    stroke([[300, 905], [318, 870], [322, 830]]);
    stroke([[150, 790], [210, 810], [262, 832]]);
    stroke([[165, 852], [222, 862], [275, 870]]);
    stroke([[200, 912], [245, 902], [290, 895]]);
    stroke([[502, 700], [470, 724], [445, 765], [432, 812], [418, 858]]);   // the hairline
    for (i = [0 : 5]) let (t0 = 200 + i * 24, t1 = t0 + 24)       // a closed, smiling eye
        cap([494 + 15 * cos(t0), 784 + 9 * sin(t0)], [494 + 15 * cos(t1), 784 + 9 * sin(t1)], 4.5);
    stroke([[430, 978], [478, 972], [522, 966]]);                  // the bow arm's edge on his chest
    stroke([[425, 925], [470, 912], [500, 905]]);                  // the drawing arm's
    stroke([[352, 1112], [338, 1170], [340, 1235]]);               // where his legs part
    stroke([[300, 1120], [262, 1135]]);                            // the back leg's crease
}
module carved() difference() {
    body3d();
    difference() {
        translate([0, 0, -1]) linear_extrude(20) lines2d();
        translate([0, 0, -1.0]) body3d();     // cut 1.0 into the surface
    }
}

module cupid_white() intersection() {
    carved();
    translate([-50, -50, 0]) cube([200, 200, 40]);
}
cupid_white();
