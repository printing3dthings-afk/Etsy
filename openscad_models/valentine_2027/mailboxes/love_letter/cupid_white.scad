// Cupid, white: a flat cut-out charm after the gold pendant Scott sent
// (2026-11-03).
//
// Scott, on the drafts: "Make it all one piece and just make it a 3d part but
// flat on the bottom side", then on two cut-out drafts "Too cluttered and legs
// backwards", "The bow is part of the face", "Match the gold one I uploaded."
// So this follows the pendant's pose and proportions: a big round head, a
// wing of long feathers swept up behind, both arms out level, the bow held well
// clear in front of his face, the near knee forward under his belly with its
// shin folded back, the far leg trailing, both feet pointed down and back.
// Its only detail is the pendant's: a few gaps cut through (the wing behind
// his head, under his arm, between the legs). Drawn with circles and hulls,
// not traced.
//
// PREVIEW: nothing on the envelope uses this yet.
//
// Laid out in the reference's own pixels, him facing +x; M() turns them into
// millimetres, y up, his toes at y 0.

$fn = 64;
S = 0.068;                                    // 900 px across: 61 mm
function M(p) = [(p.x - 20) * S, (965 - p.y) * S];
THICK = 3.0;      // flat face, flat back
EDGE  = 0.4;      // the face's edge rounds over this much; the pendant's are crisp
GAP   = 0.8;      // a cut-through gap: two beads, so it prints open
LINE  = 1.3;      // the bowstring: three beads and a margin (1.2 sat on the gate's floor)

module C(p, r) translate(M(p)) circle(r * S);
module cap(a, b, ra, rb = -1) hull() { C(a, ra); C(b, rb < 0 ? ra : rb); }
module chain(pts, r) for (i = [0 : len(pts) - 2]) cap(pts[i], pts[i + 1], r[i], r[i + 1]);

// ---------- him ----------
HC = [440, 272]; HR = 126;
// the face in profile: a round forehead, a small nose, a full cheek, the chin
module head2d() union() {
    C(HC, HR);
    C([530, 234], 58);                        // his forehead
    C([586, 320], 15);                        // his nose
    C([566, 352], 22);                        // his mouth
    C([540, 384], 26);                        // the chin
    C([350, 196], 38); C([318, 258], 30);     // soft curls at the back
    hull() { C([572, 184], 22); C([598, 168], 12); }   // a curl on his brow
}
// the wing: long feathers fanned up and back from behind his shoulder
W_ROOT = [325, 440];
// [tip, its radius, a point two-thirds out, its radius]: broad feathers
// narrowing to their tips
FEATHERS = [[[106, 202], 20, [180, 268], 40], [[100, 300], 24, [180, 334], 42],
            [[124, 382], 26, [196, 400], 42], [[176, 450], 26, [228, 452], 40],
            [[242, 494], 24, [278, 478], 38]];
module wing2d() for (f = FEATHERS) hull() { C(W_ROOT, 52); C(f[2], f[3]); C(f[0], f[1]); }
module body2d() union() {
    translate(M([345, 590])) scale([130 * S, 135 * S]) circle(1);
    C([420, 470], 62);                        // his chest, up to the shoulder
    C([470, 405], 46);                        // and his neck, under the chin
}
// the near arm from the shoulder down to the elbow and out to the bow's grip;
// the far arm level above it to the hand that draws the string
// The forearm runs 2 mm under the arrow, as the pendant's does; level with it
// the two closed into one bar (2026-11-03).
GRIP = [744, 534]; NOCK = [560, 462];
module near_arm2d() union() { chain([[372, 486], [500, 540], [712, 540]], [46, 36, 28]); C(GRIP + [-8, 0], 31); }
module far_arm2d() union() { chain([[430, 452], [540, 462]], [36, 32]); C(NOCK, 33); C([528, 494], 30); }
// chubby legs: a round thigh, the knee, a calf, the ankle, and a foot drawn
// from heel to toes, pointed down
module near_leg2d() union() {
    chain([[392, 664], [418, 764], [352, 822], [296, 866]], [70, 48, 40, 26]);
    hull() { C([296, 866], 26); C([262, 862], 22); C([302, 946], 17); }
}
module far_leg2d() union() {
    chain([[262, 688], [162, 760], [112, 778], [72, 796]], [60, 44, 36, 25]);
    hull() { C([72, 796], 25); C([50, 778], 21); C([36, 850], 17); }
}

// ---------- the bow, its string and the arrow ----------
// A D-shaped bow held by its grip, well out in front of his face: the upper
// tip is 7 mm clear of his nose and the string passes 2 mm under his chin.
B_TOP = [702, 264]; B_BOT = [690, 690]; B_SAG = 80;
B_MID = (B_TOP + B_BOT) / 2;
B_HALF = norm(B_BOT - B_TOP) / 2;
B_R = (B_HALF * B_HALF + B_SAG * B_SAG) / (2 * B_SAG);
B_C = B_MID + (B_SAG - B_R) * [1, 0];
B_A = asin(B_HALF / B_R);
function bow_pt(t) = B_C + B_R * [cos(t), sin(t)];
module bow2d() union() {
    for (i = [0 : 15]) let (t0 = -B_A + i * 2 * B_A / 16, t1 = t0 + 2 * B_A / 16) cap(bow_pt(t0), bow_pt(t1), 13);
    cap(bow_pt(-B_A), bow_pt(-B_A) + [20, -14], 13, 11);   // the tips curl forward
    cap(bow_pt(B_A), bow_pt(B_A) + [18, 12], 13, 11);
}
module string2d() for (t = [-B_A, B_A]) hull() { translate(M(bow_pt(t))) circle(LINE / 2); translate(M(NOCK)) circle(LINE / 2); }
module heart2d(w) scale(w / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 48);
}
module shaft2d() cap(NOCK, [850, 462], 10);
module arrow2d() union() { shaft2d(); translate(M([878, 462])) rotate(-90) heart2d(6.2); }

// ---------- the gaps ----------
// The thin band just outside one part, cut through whatever lies behind it,
// only inside a box, so the part stays joined at its root.
module band() difference() { offset(delta = GAP) children(); children(); }
module box(a, b) translate(M([a.x, b.y])) square([(b.x - a.x) * S, (b.y - a.y) * S]);
module gaps2d() union() {
    intersection() { band() head2d(); box([280, 300], [372, 420]); }       // the wing behind his head
    intersection() { band() near_arm2d(); box([336, 505], [530, 595]); }   // under the near arm
    intersection() { band() near_leg2d(); box([226, 690], [322, 790]); }   // the legs apart
}

// the outline: inside corners filled, the gaps cut, specks closed, outside
// corners eased
module cupid2d() offset(r = 0.3) offset(r = -0.3) offset(r = -0.25) offset(r = 0.25) difference() {
    offset(r = -0.6) offset(r = 0.6) union() {
        head2d(); wing2d(); body2d(); near_arm2d(); far_arm2d(); near_leg2d(); far_leg2d();
        bow2d(); string2d(); arrow2d();
    }
    gaps2d();
}

// ---------- the charm ----------
// The string and the arrow's shaft are under 1.6 wide; rounded over they would
// be a single bead on top (the gate's min wall, 0.87, 2026-11-03), so they
// stay square-edged to the top.
module slender2d() intersection() { cupid2d(); union() { string2d(); shaft2d(); } }
// Flat back, flat face; only the face's edge rounds over, EDGE in, on the 0.2
// layer grid.
function rise(z) = EDGE * (1 - sqrt(max(0, 1 - pow((z - (THICK - EDGE)) / EDGE, 2))));
module cupid_white() union() {
    linear_extrude(THICK - EDGE + 0.01) cupid2d();
    for (z = [THICK - EDGE + 0.2 : 0.2 : THICK + 0.001])
        translate([0, 0, z - 0.21]) linear_extrude(0.21) union() { offset(delta = -rise(z)) cupid2d(); slender2d(); }
}
cupid_white();
