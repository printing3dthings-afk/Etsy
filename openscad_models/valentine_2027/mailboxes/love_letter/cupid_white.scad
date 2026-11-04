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
// pendant: a big round head in profile, a wing of four feathers swept up
// behind, both arms out level, the bow held well clear of his face, the near
// knee forward with its shin folded back, the far leg trailing, both feet
// pointed down. The only detail is three gaps cut through: the wing behind his
// head, under his arm, between his legs. Our own drawing, not traced.
//
// Redone 2026-11-04 through the character workflow (3d-print-design skill,
// Technique 83): the legs are built from their joints, the wing's coverts bend
// at the wrist, the nose is a small button, and tools/silhouette_check.py
// passes it (knees and elbow bend the right way, the bow 1.87 mm clear of his
// face, no near-touches, nothing under 1.2 mm).
//
// He sits in a pocket on the Giant Love Letter's front, pressed onto two
// short pegs (cupid_peg.scad); he prints face up, one white filament.
//
// Drawn on a 900 px grid, y down as on paper, him facing +x; M() turns it into
// millimetres, y up, his toes at y 0.

include <BOSL2/std.scad>
include <cupid_peg.scad>

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
HEAD = [[448, 148], [520, 160], [570, 200], [592, 250], [584, 292], [595, 318],
        [584, 340], [570, 382], [536, 406], [490, 412],
        [420, 404], [350, 368], [312, 300], [318, 228], [362, 172]];
// two curls on the back of his head and one rolled forward over his brow
module hair2d() union() {
    C([344, 200], 34); C([316, 262], 26);
    shape([[528, 178], [562, 158], [594, 160], [606, 176], [592, 190], [560, 196]]);
}
// His back comes down close under the wing, then rounds out low into his
// bottom over the far thigh, as on the pendant. Scott circled this twice: a
// straight back read as a slab, and the first round bottom bulged out too far
// and too high (2026-11-03: 30-50 px wider than the pendant at y 490-590).
TORSO = [[360, 412], [440, 420], [500, 470], [508, 560], [482, 640], [420, 690],
         [320, 712], [252, 710], [212, 690], [204, 652], [214, 616], [244, 588],
         [282, 560], [304, 524], [310, 488]];
// the near arm from the shoulder down to the elbow and out to his fist on the
// bow's grip; it runs 2 mm under the arrow, as the pendant's forearm does
NEAR_ARM = [[372, 468], [450, 498], [530, 512], [640, 514], [720, 504], [754, 506],
            [774, 526], [760, 550], [728, 558], [640, 554], [540, 566], [470, 560],
            [400, 530]];
// the far arm level above it, to the fist that holds the arrow on the string
NOCK = [560, 462];
FAR_ARM = [[430, 426], [500, 430], [548, 436], [580, 446], [594, 466], [588, 494],
           [566, 512], [532, 516], [500, 500], [455, 470]];
// ---------- legs, built from their joints ----------
// Each leg is drawn from its skeleton (hip, knee, ankle, toe) rather than as
// free points, so the knee can only bend the way a knee does, and the draw
// follows the rule set against curve: the shin's front is straight, the calf
// bulges behind, the thigh is a teardrop from a round hip, and the foot points
// on past the ankle. Free-drawn legs folded a knee backwards twice in the
// drafts ("legs backwards", 2026-11-03); tools/silhouette_check.py checks the
// JOINT echoes below.
function unitv(v) = v / norm(v);
function lnorm(v) = let (u = unitv(v)) [-u.y, u.x];
function toward(n, ref) = n * ref >= 0 ? n : -n;
function lerp(a, b, t) = a + (b - a) * t;
// r = [hip, knee, calf, ankle, toe] radii, in grid px
function leg_pts(hip, knee, ankle, toe, r) =
    let (front = knee - (hip + ankle) / 2,
         nt = toward(lnorm(knee - hip), front), ns = toward(lnorm(ankle - knee), front),
         nk = unitv(nt + ns), ds = unitv(ankle - knee), df = unitv(toe - ankle),
         nf = toward(lnorm(toe - ankle), ns))
    [hip + nt * r[0], lerp(hip, knee, 0.55) + nt * r[0] * 0.8, knee + nk * r[1],
     lerp(knee, ankle, 0.5) + ns * (r[3] + r[1]) / 2, ankle + ns * r[3],
     toe + nf * r[4], toe + df * r[4], toe - nf * r[4], ankle - ns * r[3] - ds * r[3] * 0.3,
     // the crease behind the knee, kept shallow: at 0.85 r a sharply bent knee
     // folded into a hook (2026-11-04)
     lerp(knee, ankle, 0.4) - ns * r[2], knee - nk * r[1] * 1.5,
     lerp(hip, knee, 0.45) - nt * r[0] * 0.95, hip - nt * r[0]];
// the near leg: knee forward under his belly, shin folded back, foot pointed down
NEAR_HIP = [405, 665]; NEAR_KNEE = [440, 772]; NEAR_ANKLE = [318, 866]; NEAR_TOE = [300, 950];
// the far leg trailing behind, a gentle bend at the knee, foot pointed back
// Its hip sits low and right, under the near thigh: higher, its top edge ran
// straight on from his back and the round bottom was lost.
FAR_HIP = [300, 725]; FAR_KNEE = [168, 770]; FAR_ANKLE = [82, 796]; FAR_TOE = [36, 850];
module near_leg2d() shape(leg_pts(NEAR_HIP, NEAR_KNEE, NEAR_ANKLE, NEAR_TOE, [62, 40, 44, 22, 14]));
// with the round of its hip, which the near thigh overlaps: the gap cut along
// the near thigh's back shows against it
module far_leg2d() union() { shape(leg_pts(FAR_HIP, FAR_KNEE, FAR_ANKLE, FAR_TOE, [50, 38, 36, 22, 14])); C(FAR_HIP, 50); }
echo("JOINT", "near leg", "knee", M(NEAR_HIP), M(NEAR_KNEE), M(NEAR_ANKLE), 1);
echo("JOINT", "far leg", "knee", M(FAR_HIP), M(FAR_KNEE), M(FAR_ANKLE), 1);
echo("JOINT", "bow arm", "elbow", M([372, 476]), M([505, 542]), M([728, 532]), 1);
// the wing: four feathers fanned from behind his shoulder, each full in the
// middle and tapering to a soft point, so the trailing edge scallops; over
// their roots the coverts, whose leading edge bends out at the wrist, the cue
// that makes a wing read as a wing and not a fan (bird anatomy, research
// 2026-11-04)
W_ROOT = [330, 432];
// The leading feather is the broadest; the three under it are slimmer, so the
// notches between their rounded tips run a third of the way in.
// (A fifth, lowest feather ended on his back and left a kink there.)
FEATHERS = [[[104, 196], 46], [[94, 292], 32], [[116, 378], 30], [[176, 452], 30]];
module feather(tip, w) let (d = unit(tip - W_ROOT), n = [-d.y, d.x], m = W_ROOT + (tip - W_ROOT) * 0.5)
    shape([W_ROOT + n * w, m + n * w, tip - d * 6 + n * w * 0.55, tip + d * 14, tip - d * 6 - n * w * 0.55,
           m - n * w, W_ROOT - n * w, W_ROOT - d * w * 0.8]);
COVERTS = [[340, 420], [300, 350], [242, 290], [170, 236], [108, 196], [132, 252],
           [192, 318], [262, 398], [320, 450]];
module wing2d() union() { for (f = FEATHERS) feather(f[0], f[1]); shape(COVERTS); }

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
    intersection() { band() near_leg2d(); box([290, 680], [392, 800]); }        // his legs apart
}

// the outline: where parts meet, filled 0.5 so they flow into each other; the
// gaps cut; specks closed; outside corners eased 0.3
module cupid2d() offset(r = 0.3) offset(r = -0.3) offset(r = -0.25) offset(r = 0.25) difference() {
    offset(r = -0.5) offset(r = 0.5) union() {
        shape(HEAD); hair2d(); shape(TORSO); wing2d();
        shape(NEAR_ARM); shape(FAR_ARM); near_leg2d(); far_leg2d();
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
// with the two holes in his back for the envelope's pegs (cupid_peg.scad)
module cupid_white() difference() {
    union() {
        linear_extrude(THICK - EDGE + 0.01) cupid2d();
        for (z = [THICK - EDGE + 0.2 : 0.2 : THICK + 0.001])
            translate([0, 0, z - 0.21]) linear_extrude(0.21) union() { offset(delta = -rise(z)) cupid2d(); slender2d(); }
    }
    cupid_holes();
}
// part: "charm" to print; "outline", his 2D outline, which ship.sh exports
// as cupid_white_outline.svg for the envelope to cut his pocket from (the
// envelope cannot include this file: BOSL2's front() and back() would replace
// its own); "head" and "bow" for tools/silhouette_check.py's --apart check
// that the bow stays clear of his face
part = "charm";
if (part == "charm") cupid_white();
// the outline for his pocket is filled in round the bow: the openings inside
// it, cut into the pocket, left the envelope open-edged (2026-11-04)
else if (part == "outline") union() { cupid2d(); hull() { bow2d(); string2d(); } }
else if (part == "head") linear_extrude(THICK) union() { shape(HEAD); hair2d(); }
else if (part == "bow") linear_extrude(THICK) union() { bow2d(); string2d(); }
