// Nesting Cats (2026-10-28): the multipart line's first product, form 1 of the
// five shown to Scott (concepts/form1_egg_cat.png). Five kawaii cats, 90 / 72 /
// 57 / 45 / 32 mm tall, each unscrewing at the belly to hide the next; the
// smallest is solid. One colour per figure: the face, scarf and paws are cut
// and raised, so any single-colour P1S makes the set.
//
// The seam is at the belly, not under the scarf as in the concept: each cat
// has to pass through the opening of the one outside it, and only at the
// widest point is that opening big enough (sizes worked out from the walls and
// the thread, 2026-10-28).
//
// Printing, both halves upright, no supports:
//   bottom  on its flat foot, open at the top, the male thread on its neck
//   top     on its rim, the female thread inside it; its hollow narrows to a
//           point at 40 deg, so its ceiling needs nothing under it
// Every surface that faces down is held to 40 deg off vertical or steeper:
// the outer profile's waist is filled to that slope, and the hollows narrow
// no faster.

include <../thread_lib.scad>
SH = 1.6;           // relief undersides climb 1.6 per 1 out (58 deg): at 50 the slicer propped the paws
include <../../christmas_village/relief_lib.scad>
include <../../brand/obc_mark.scad>

fig  = 0;           // 0 = largest .. 4 = smallest
part = "top";       // bottom | top | solid | all (assembled, the top screwed on)
FACE = true;        // the face cut in (false only for testing what the slicer props)

HS   = [90, 72, 57, 45, 32];
CLR  = 0.3;         // the thread's clearance: provisional, from the fit test plate once printed
TP   = 3; TDEP = 0.8; TL = 5;     // thread pitch, depth, length (thread_lib: 39 deg flanks)
W    = 1.8;         // the walls
FL   = 1.8;         // the bottom's floor
WT   = 1.2;         // the least wall round the thread, either side
K    = 0.84;        // tan 40: the fastest a down-facing surface may run in per 1 up
N    = 240;         // profile samples up a figure

H    = HS[fig];
ZS   = 0.30 * H;    // the seam, at the belly
dz   = H / N;

// ---- the profile -----------------------------------------------------------------------------
function smax(a, b, p = 7) = pow(pow(max(a, 0), p) + pow(max(b, 0), p), 1 / p);
function ell(t, c, h, r) = abs(t - c) >= h ? 0 : r * sqrt(1 - pow((t - c) / h, 2));
// the egg: a belly and a head, run into each other
function egg(z) = let (t = z / H) H * smax(ell(t, 0.30, 0.44, 0.37), ell(t, 0.74, 0.26, 0.30));
// the waist filled so the head's underside never overhangs past 40 deg: from
// the top down, the radius may fall at most K per 1 down
// KO, steeper than K: the face is cut into the head's underside, and at 40
// deg the slicer propped the front of it, under the mouth and cheeks (2026-10-28)
KO = 0.6;
function fill_k(k) = k >= N ? egg(H) : max(egg(k * dz), fill_k(k + 1) - KO * dz);
RF = [for (k = [0 : N]) fill_k(k)];
// Read between samples, not at the nearest one: sampled again at another
// spacing, nearest-sample reads came out as a staircase whose steps ran at
// half and twice the slope in turn, and the slicer propped every steep one --
// the bottom's foot, the top's whole ceiling (2026-10-28).
function lerp(A, z) = let (x = min(max(z / dz, 0), N - 0.001), k = floor(x), f = x - k) A[k] * (1 - f) + A[k + 1] * f;
function rf(z) = lerp(RF, z);

// the scarf: a band round the neck, its underside climbing at 50 deg
ZSC = 0.505 * H; SCP = min(1.6, 0.035 * H); SCH = 0.045 * H;
function scarf(z) = z < ZSC ? max(0, SCP - (ZSC - z) * K) : z < ZSC + SCH ? SCP : max(0, SCP - (z - ZSC - SCH));
function ro(z) = rf(z) + scarf(z);

// ---- the thread ------------------------------------------------------------------------------
// The male thread's outer radius: the top's wall round the female thread is
// at least WT everywhere up the thread, where the egg already narrows.
RM = min([for (z = [ZS : 0.25 : ZS + TL + 0.5]) rf(z)]) - WT - CLR;
WN = 1.3;                       // the neck's wall: at WT the gate read 1.2 on the nose
RO = RM - TDEP - WN;            // the neck's bore: the next cat goes through this
ZF = ZS + TL + 0.4;             // the top of the female thread's cut

// ---- the hollows -----------------------------------------------------------------------------
// The top's: W inside the filled egg, narrowing up no faster than K (from the
// top down, it may widen at most K per 1 down), up to a flat ceiling RB
// across, which the printer bridges; and above the female thread it opens no
// faster than K out of the thread's cut. Closed to a point, the hollow had no
// room for the next cat's head and ears (check_cats, 2026-10-28): the flat
// ceiling lifts the 40 deg cone's apex by RB / K.
RB = min(6, 0.1 * H);
ZC = max([for (k = [0 : N]) if (rf(k * dz) - W >= RB) k * dz]);
function cav_k(k) = k * dz > ZC ? -1 : k * dz > ZC - dz ? RB : min(rf(k * dz) - W, cav_k(k + 1) + K * dz);
CAV = [for (k = [0 : N]) cav_k(k)];
function cav_top(z) = max(lerp(CAV, z), RM + CLR - K * (z - ZF));
// The bottom's: W inside the egg, closing to the neck's bore at the seam no
// faster than K.
function cav_bot(z) = min(egg(z) - W, RO + K * (ZS - z));

M = 120;
// a profile f(z) from z0 to z1, revolved; samples where f has closed to the
// axis are left out (a run of points on the axis made rotate_extrude write an
// open mesh where the top's hollow closes to its point, 2026-10-28)
module revolve_band(f, z0, z1) let (pts = [for (i = [0 : M]) let (z = z0 + (z1 - z0) * i / M) if (f(z) > 0.05) [f(z), z]])
    if (len(pts) > 1) rotate_extrude($fn = 180) polygon(concat([[0, pts[0][1]]], pts, [[0, pts[len(pts) - 1][1]]]));

// ---- face and paws ---------------------------------------------------------------------------
// The front is -y. Every cut and raised detail is placed at its own spot on
// the curve, turned to face out there: cut straight in from the front, the
// cheeks (round the curve) only grazed the surface and came out as slashes.
// A cut goes in sheared down CSH per 1 in, so its ceiling slopes and prints.
function ang(xc, zc) = asin(xc / rf(zc));
// A cut's ceiling falls CSH per 1 in (58 deg), so the cut is open to the
// face at every layer, deepest at its foot. Climbing in instead, it left a
// pocket behind a lip thinner than a line, and the slicer propped every eye,
// cheek and mouth; sliced without the face, the smallest cat needed nothing
// (2026-10-28).
CSH = 1.6;
module cut_at(xc, zc, depth) let (r = rf(zc)) rotate([0, 0, ang(xc, zc)])
    multmatrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, -CSH, 1, -r * CSH], [0, 0, 0, 1]])
        translate([0, -r - 0.5, 0]) rotate([-90, 0, 0]) linear_extrude(depth + 0.5) mirror([0, 1, 0]) children();
EYE = [0.105, 0.70];             // x, z of each eye's centre (of H)
module eye2d() scale([0.034 * H, 0.046 * H]) circle(1, $fn = 40);
module nose2d() polygon([[-0.022 * H, 0.012 * H], [0.022 * H, 0.012 * H], [0, -0.012 * H]]);
// two arcs overlapping at the middle: drawn just touching, they met at a point
// and the cut came out an open mesh CGAL dropped, so the mouth went missing
module mouth2d() let (r = 0.02 * H, w = max(0.6, 0.012 * H)) for (s = [-1, 1]) translate([s * (r - w / 2), 0])
    difference() { circle(r, $fn = 40); circle(r - w, $fn = 40); translate([-r - 1, 0]) square(2 * r + 2); }
module cheek2d() scale([0.035 * H, 0.022 * H]) circle(1, $fn = 32);
// Each cut runs only its own depth in from the tangent plane at its centre:
// run 4.6 deep and held by a band round the profile, the steep ceilings
// climbed 7 mm into the waist and carved the scarf into 0.4 mm slivers on
// the smallest cat (2026-10-28).
module face_cuts() if (FACE) {
    for (s = [-1, 1]) cut_at(s * EYE[0] * H, EYE[1] * H, 0.6) translate([0, EYE[1] * H]) eye2d();
    cut_at(0, 0.66 * H, 0.5) translate([0, 0.66 * H]) nose2d();
    cut_at(0, 0.632 * H, 0.5) translate([0, 0.632 * H]) mouth2d();
    for (s = [-1, 1]) cut_at(s * 0.19 * H, 0.645 * H, 0.4) translate([0, 0.645 * H]) cheek2d();
}
// Raised on a plane laid against the surface at (xc, zc), turned to face out
// there, and sunk into the curve; the 2D shape is drawn centred on xc = 0.
module raised(xc, zc, h, sink) let (r = rf(zc)) rotate([0, 0, asin(xc / r)])
    translate([0, -r + sink, 0]) rotate([90, 0, 0]) art_skirt(h + sink, 2) children();
// toes and ear tips no smaller than 0.8 across... 1.6 mm: at 0.015 H the
// smallest cat's toes were under a millimetre
module paw2d() {
    scale([0.052 * H, 0.04 * H]) circle(1, $fn = 40);
    for (a = [-35, 0, 35]) rotate(a) translate([0, 0.04 * H]) circle(max(0.015 * H, 0.8), $fn = 24);
}
module tail2d() polygon([[-0.03 * H, 0], [0.03 * H, 0], [0.04 * H, -0.1 * H], [0.01 * H, -0.085 * H], [-0.02 * H, -0.1 * H]]);
// Paws held up at the chest and the scarf's tail at the side: on the belly,
// the next cat's paws and tail stood out past its belly and would not pass the
// neck it goes through (check_cats, 2026-10-28). Every detail is also held
// inside the belly's radius (RBELLY, in top() and solid()).
module paws() for (s = [-1, 1]) raised(s * 0.105 * H, 0.445 * H, 0.8, 1.4) translate([0, 0.445 * H]) paw2d();
module tail() raised(0.22 * H, ZSC - 0.05 * H, 0.8, 1.4) translate([0, ZSC]) tail2d();

// ---- ears ------------------------------------------------------------------------------------
// Each a triangle seen from the front, outer edge 40 deg off vertical: 28
// from its own taper, 12 from its tilt.
module ears() for (s = [-1, 1]) let (zb = 0.84 * H, xb = s * 0.165 * H)
    translate([xb, 0, zb]) rotate([0, s * 12, 0]) hull() {
        scale([0.09 * H, 0.055 * H, 1]) cylinder(r = 1, h = 0.01, $fn = 40);
        translate([0, 0, -0.08 * H]) scale([0.09 * H, 0.055 * H, 1]) cylinder(r = 1, h = 0.01, $fn = 40);
        translate([0, 0, 0.17 * H]) sphere(r = max(0.016 * H, 0.8), $fn = 24);
    }

// ---- the halves ------------------------------------------------------------------------------
MARK = H >= 40;                  // the maker's mark only where 4.4 mm letters fit the foot
RBELLY = egg(ZS);                // nothing stands out past the belly
module bottom() difference() {
    union() {
        revolve_band(function (z) ro(z), 0, ZS);
        // the neck, from inside the belly to the thread's top
        translate([0, 0, ZS - 1]) cylinder(r = RM - TDEP + 0.01, h = 1.01, $fn = 180);
        translate([0, 0, ZS]) thread_chamfer(2 * RM, TL, TDEP) thread_solid(2 * RM, TP, TL, TDEP);
    }
    revolve_band(function (z) cav_bot(z), FL, ZS);
    translate([0, 0, ZS - 1]) cylinder(r = RO, h = TL + 2, $fn = 180);
    if (MARK) obc_engrave(4.4, 0.8, 0.15, ridges = false);
}
module top() difference() {
    union() {
        intersection() {
            union() {
                revolve_band(function (z) ro(z), ZS, H);
                ears();
                intersection() { union() { paws(); tail(); } revolve_band(function (z) rf(z) + 3, ZS + 0.5, H); }
            }
            cylinder(r = RBELLY, h = 2 * H, $fn = 180);
        }
    }
    // the female thread, grown CLR all round, and its lead-in at the rim: no
    // wider than the thread, since a flare past it thinned the rim to 0.44 mm
    // and left the top 4% of its footprint to stand on
    translate([0, 0, ZS - 0.01]) thread_solid(2 * RM, TP, ZF - ZS + 0.01, TDEP, CLR);
    // (0.1 past it: flush with the thread's crest, the cone and the cut met in
    // a zero-volume sliver on the largest cat that read as non-manifold)
    translate([0, 0, ZS - 0.01]) cylinder(r1 = RM + CLR + 0.1, r2 = RM - TDEP + CLR, h = (TDEP + 0.1) * THREAD_FLANK, $fn = 180);
    revolve_band(function (z) cav_top(z), ZF - 0.01, H);
    face_cuts();
}
module solid() union() {
    difference() {
        intersection() {
            union() { revolve_band(function (z) ro(z), 0, H); ears(); intersection() { union() { paws(); tail(); } revolve_band(function (z) rf(z) + 3, 0.2 * H, H); } }
            cylinder(r = RBELLY, h = 2 * H, $fn = 180);
        }
        face_cuts();
        if (MARK) obc_engrave(4.4, 0.8, 0.15, ridges = false);
    }
}

// printed: the top stands on its rim
if (part == "bottom") bottom();
else if (part == "top") translate([0, 0, -ZS]) top();
else if (part == "solid") solid();
else if (part == "all") { if (fig == 4) solid(); else { bottom(); top(); } }
