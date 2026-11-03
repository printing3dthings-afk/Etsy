// Cupid, white: a flat cut-out charm in the style of the gold pendant Scott
// sent (2026-11-03).
//
// Scott, on the drafts: "Make it all one piece and just make it a 3d part but
// flat on the bottom side"; on the cut-out drafts "Too cluttered and legs
// backwards", "The bow is part of the face"; then, choosing our own drawing over
// a copy of the pendant, "it has to be better with how you do it."
//
// So every part is now one smooth outline drawn through a few points
// (BOSL2's smooth_path), the way vector art is drawn, not circles hulled
// together, which left lumps and knuckles wherever two met. Same pose as the
// pendant: a big round head in profile, a wing of five feathers swept up
// behind, both arms out level, the bow held well clear of his face, the near
// knee forward with its shin folded back, the far leg trailing, both feet
// pointed down. The only detail is three gaps cut through: the wing behind his
// head, under his arm, between his legs. Our own drawing, not traced.
//
// PREVIEW: nothing on the envelope uses this yet.
//
// Drawn on a 900 px grid, y down as on paper, him facing +x; M() turns it into
// millimetres, y up, his toes at y 0.

include <BOSL2/std.scad>

$fn = 64;
S = 0.068;                                    // 900 px across: 61 mm
function M(p) = [(p.x - 20) * S, (965 - p.y) * S];
function Mp(ps) = [for (p = ps) M(p)];
THICK = 3.0;      // flat face, flat back
EDGE  = 0.4;      // the face's edge rounds over this much; the pendant's are crisp
GAP   = 0.8;      // a cut-through gap: two beads, so it prints open
LINE  = 1.3;      // the bowstring: three beads and a margin (1.2 sat on the gate's floor)

// a closed outline drawn smoothly through its points
module shape(pts) polygon(smooth_path(Mp(pts), closed = true, splinesteps = 12));
module C(p, r) translate(M(p)) circle(r * S);

// ---------- him ----------
// the head in profile: crown, forehead, a dip at the eye, a button nose, lips,
// a round chin, then under the jaw and round the back of the skull
HEAD = [[448, 148], [520, 160], [570, 200], [592, 250], [584, 292], [600, 318],
        [584, 340], [570, 382], [536, 406], [490, 412],
        [420, 404], [350, 368], [312, 300], [318, 228], [362, 172]];
// two curls on the back of his head and one rolled forward over his brow
module hair2d() union() {
    C([344, 200], 34); C([316, 262], 26);
    shape([[528, 178], [562, 158], [594, 160], [606, 176], [592, 190], [560, 196]]);
}
TORSO = [[360, 412], [440, 420], [500, 470], [508, 560], [482, 640], [420, 690],
         [320, 712], [240, 690], [212, 620], [228, 540], [280, 466]];
// the near arm from the shoulder down to the elbow and out to his fist on the
// bow's grip; it runs 2 mm under the arrow, as the pendant's forearm does
NEAR_ARM = [[372, 468], [450, 498], [530, 512], [640, 514], [720, 504], [754, 506],
            [774, 526], [760, 550], [728, 558], [640, 554], [540, 566], [470, 560],
            [400, 530]];
// the far arm level above it, to the fist that holds the arrow on the string
NOCK = [560, 462];
FAR_ARM = [[430, 426], [500, 430], [548, 436], [580, 446], [594, 466], [588, 494],
           [566, 512], [532, 516], [500, 500], [455, 470]];
// legs: a round thigh, the knee, the shin folded back, a pointed foot
NEAR_LEG = [[462, 604], [492, 680], [482, 752], [456, 798], [392, 842], [334, 880],
            [326, 906], [324, 948], [306, 962], [286, 950], [270, 914], [256, 876],
            [274, 852], [322, 814], [362, 784], [372, 736], [356, 690], [384, 636]];
FAR_LEG = [[272, 664], [204, 700], [152, 726], [106, 752], [72, 768], [48, 770],
           [32, 792], [28, 830], [38, 858], [58, 850], [72, 826], [94, 812],
           [132, 804], [172, 794], [232, 772], [300, 760], [362, 770], [384, 724], [352, 690]];
// the wing: five feathers fanned from behind his shoulder, each full in the
// middle and tapering to a soft point, so the trailing edge scallops
W_ROOT = [330, 432];
// The leading feather is the broadest; the four under it are slimmer, so the
// notches between their rounded tips run a third of the way in.
FEATHERS = [[[104, 196], 46], [[94, 292], 32], [[116, 378], 30], [[168, 446], 28], [[238, 494], 26]];
module feather(tip, w) let (d = unit(tip - W_ROOT), n = [-d.y, d.x], m = W_ROOT + (tip - W_ROOT) * 0.5)
    shape([W_ROOT + n * w, m + n * w, tip - d * 6 + n * w * 0.55, tip + d * 14, tip - d * 6 - n * w * 0.55,
           m - n * w, W_ROOT - n * w, W_ROOT - d * w * 0.8]);
module wing2d() for (f = FEATHERS) feather(f[0], f[1]);

// ---------- the bow, its string and the arrow ----------
// A D-shaped bow held by its grip, well clear in front of his face: the upper
// tip is 7 mm from his nose and the string passes under his chin.
B_TOP = [702, 264]; B_BOT = [690, 690]; B_SAG = 80;
B_MID = (B_TOP + B_BOT) / 2;
B_HALF = norm(B_BOT - B_TOP) / 2;
B_R = (B_HALF * B_HALF + B_SAG * B_SAG) / (2 * B_SAG);
B_C = B_MID + (B_SAG - B_R) * [1, 0];
B_A = asin(B_HALF / B_R);
function bow_pt(t) = B_C + B_R * [cos(t), sin(t)];
// the limb thickest at the grip, its tips flicking forward as a recurve's do
module bow2d() let (n = 24, w = function (t) 15 - 4 * abs(t) / B_A) union() {
    for (i = [0 : n - 1]) let (t0 = -B_A + i * 2 * B_A / n, t1 = t0 + 2 * B_A / n)
        hull() { C(bow_pt(t0), w(t0)); C(bow_pt(t1), w(t1)); }
    for (s = [-1, 1]) let (p = bow_pt(s * B_A))
        hull() { C(p, 11); C(p + [14, s * 12], 9.5); }
}
module string2d() for (t = [-B_A, B_A]) hull() { translate(M(bow_pt(t))) circle(LINE / 2); translate(M(NOCK)) circle(LINE / 2); }
module heart2d(w) scale(w / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 48);
}
module shaft2d() hull() { C(NOCK, 10); C([850, 462], 10); }
module arrow2d() union() { shaft2d(); translate(M([878, 462])) rotate(-90) heart2d(6.2); }

// ---------- the gaps ----------
// The thin band just outside one part, cut through whatever lies behind it,
// only inside a box, so the part stays joined at its root.
module band() difference() { offset(delta = GAP) children(); children(); }
module box(a, b) translate(M([a.x, b.y])) square([(b.x - a.x) * S, (b.y - a.y) * S]);
module gaps2d() union() {
    intersection() { band() shape(HEAD); box([290, 300], [384, 420]); }         // the wing behind his head
    intersection() { band() shape(NEAR_ARM); box([380, 528], [560, 600]); }     // under his arm
    intersection() { band() shape(NEAR_LEG); box([296, 680], [384, 800]); }     // his legs apart
}

// the outline: where parts meet, filled 0.5 so they flow into each other; the
// gaps cut; specks closed; outside corners eased 0.3
module cupid2d() offset(r = 0.3) offset(r = -0.3) offset(r = -0.25) offset(r = 0.25) difference() {
    offset(r = -0.5) offset(r = 0.5) union() {
        shape(HEAD); hair2d(); shape(TORSO); wing2d();
        shape(NEAR_ARM); shape(FAR_ARM); shape(NEAR_LEG); shape(FAR_LEG);
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
