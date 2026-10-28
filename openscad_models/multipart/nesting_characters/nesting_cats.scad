// Nesting Cats (2026-10-28): the multipart line's first product, form 1 of the
// five shown to Scott, drawn to match its concept render
// (concepts/form1_egg_cat.png; Scott: "I want it to look just like this").
// Five kawaii cats, 90 / 72 / 57 / 43 / 28 mm tall, each unscrewing at the
// belly to hide the next; the smallest is solid.
//
// As the concept: the same egg (a round belly and a round head), a thick
// round scarf with a hanging tail, oval paws, and raised eyes, nose and
// cheeks. Each is its own part, so with an AMS a cat prints in four colours:
// body, cream (scarf, tail, paws), dark (eyes, nose) and pink (cheeks). In one
// colour it all still reads, raised.
//
// Where it differs from the concept, and why:
//   the seam is at the belly, not under the scarf: each cat has to pass
//     through the opening of the one outside it, and only at the widest point
//     is that opening big enough for five sizes (Scott chose this, 2026-10-28)
//   the ears' outer edges lean 40 deg, not the concept's 68, so they print
//   the scarf's underside is a 50 deg cone, not a round tube's underside
//   the eyes, nose, cheeks and paws are flat-fronted, raised on 58 deg skirts
//
// Printing, both halves upright, no supports:
//   bottom  on its flat foot, open at the top, the male thread on its neck
//   top     on its rim, the female thread inside it; its hollow narrows at 40
//           deg to a small flat ceiling the printer bridges

include <../thread_lib.scad>
SH = 1.6;           // raised details' undersides climb 1.6 per 1 out (58 deg): at 50 the slicer propped the paws
include <../../christmas_village/relief_lib.scad>
include <../../brand/obc_mark.scad>

fig  = 0;           // 0 = largest .. 4 = smallest
part = "top";       // bottom | top | solid (each all colours), or top_<c> / solid_<c>, c = body | trim | dark | pink
                    // | all (assembled, the top screwed on)

HS   = [90, 72, 57, 43, 28];   // the two smallest were 45 and 32: with the concept's head, the 45's
                                // eyes met the 57's waist and the necks had 0.2 mm to spare; the
                                // smallest was 30 until the thread wall went to 1.45 (0.10 mm room)
CLR  = 0.3;         // the thread's clearance: provisional, from the fit test plate once printed
TP   = 3; TDEP = 0.8; TL = 5;     // thread pitch, depth, length (thread_lib: 39 deg flanks)
W    = 1.8;         // the walls
FL   = 1.8;         // the bottom's floor; 0.4 more put each inner cat's ears into the hollow
MD   = 0.5;         // the maker's mark's depth: at 0.8 it left 1.0 of floor (product gate, 43 mm cat)
WT   = 1.45;        // the least wall round the thread, either side: at 1.2 the egg's
                    // narrowing above the seam left 1.06 to 1.19 (product gate)
K    = 0.84;        // tan 40: the fastest a down-facing surface may run in per 1 up
N    = 240;         // profile samples up a figure

H    = HS[fig];
ZS   = 0.30 * H;    // the seam, at the belly
dz   = H / N;

// ---- the profile -----------------------------------------------------------------------------
function smax(a, b, p = 7) = pow(pow(max(a, 0), p) + pow(max(b, 0), p), 1 / p);
function ell(t, c, h, r) = abs(t - c) >= h ? 0 : r * sqrt(1 - pow((t - c) / h, 2));
// the concept's egg: a round belly and a round head. Its head never leans out
// past 17 deg, so it prints as drawn; only its foot, at 46, is eased: below the
// belly the radius may fall at most K per 1 down.
function egg(z) = let (t = z / H) H * smax(ell(t, 0.30, 0.40, 0.37), ell(t, 0.74, 0.26, 0.30));
function fill_k(k) = k * dz >= ZS ? egg(k * dz) : max(egg(k * dz), fill_k(k + 1) - K * dz);
RF = [for (k = [0 : N]) fill_k(k)];
// Read between samples, not at the nearest one: sampled again at another
// spacing, nearest-sample reads came out as a staircase whose steps ran at
// half and twice the slope in turn, and the slicer propped every steep one --
// the bottom's foot, the top's whole ceiling (2026-10-28).
function lerp(A, z) = let (x = min(max(z / dz, 0), N - 0.001), k = floor(x), f = x - k) A[k] * (1 - f) + A[k + 1] * f;
function rf(z) = lerp(RF, z);
RBELLY = egg(ZS);                // nothing stands out past the belly, or it would not pass the next neck

// ---- the thread ------------------------------------------------------------------------------
// The male thread's outer radius: the top's wall round the female thread is
// at least WT everywhere up the thread, where the egg already narrows.
RM = min([for (z = [ZS : 0.25 : ZS + TL + 0.5]) rf(z)]) - WT - CLR;
WN = 1.4;                       // the neck's wall: at 1.3 the gate read 1.17
RO = RM - TDEP - WN;            // the neck's bore: the next cat goes through this
ZF = ZS + TL + 0.4;             // the top of the female thread's cut

// The scarf: the concept's round tube about the waist, its underside a 50 deg
// cone so it prints; sunk SINK into the wall.
SZ = 0.555 * H; SA = 0.05 * H; SB = 0.045 * H; SR = egg(SZ) - 0.01 * H;
function scarf_r(z) = z >= SZ ? SR + SA * sqrt(max(0, 1 - pow((z - SZ) / SB, 2))) : SR + SA - (SZ - z) * K;
module scarf() difference() {
    revolve_band(function (z) scarf_r(z), SZ - (SA + 2) / K, SZ + SB);
    revolve_band(function (z) rf(z) - SINK, SZ - (SA + 2) / K - 1, SZ + SB + 1);
}

// ---- the hollows -----------------------------------------------------------------------------
// The top's: W inside the egg, narrowing up no faster than K (from the top
// down, it may widen at most K per 1 down), up to a flat ceiling RB across,
// which the printer bridges; and above the female thread it opens no faster
// than K out of the thread's cut. Closed to a point, the hollow had no room
// for the next cat's head and ears (check_cats, 2026-10-28).
RB = min(3, 0.05 * H);
// and ROOF under the top. Placed wherever the head was still wide enough, the
// roof over it came out 1 mm thick (product gate); at 2.3 the slicer propped
// the largest cat's ceiling, and at 3.5 it bridged it (2026-10-28).
ROOF = 3.5;
// The ceiling ends flat at the last sample under ZC. Read between samples past
// it, the hollow closed over one more sample instead, a cone 85 deg from
// upright; wherever that fell across a layer line the slicer met it as a ring
// with nothing in the middle and propped it (910 moves on the 57 mm top, none
// when the same ceiling sat 0.1 mm off the line, 2026-10-28).
ZC = min(max([for (k = [0 : N]) if (rf(k * dz) - W >= RB) k * dz]), H - ROOF);
// Inside the scarf the hollow follows the scarf's outside, not the waist under
// it: the next cat's head sits at this one's waist (check_cats, 2026-10-28).
function wall_out(z) = z >= SZ - SA / K && z <= SZ + SB ? max(rf(z), scarf_r(z)) : rf(z);
function cav_k(k) = k * dz > ZC ? -1 : k * dz > ZC - dz ? RB : min(wall_out(k * dz) - W, cav_k(k + 1) + K * dz);
CAV = [for (k = [0 : N]) cav_k(k)];
ZT = floor(ZC / dz) * dz;
function cav_top(z) = max(lerp(CAV, z), RM + CLR + 0.1 - K * (z - ZF));
// The bottom's: W inside the egg, closing to the neck's bore at the seam no
// faster than K.
function cav_bot(z) = min(rf(z) - W, RO + K * (ZS - z));

M = 120;
// a profile f(z) from z0 to z1, revolved; samples where f has closed to the
// axis are left out (a run of points on the axis made rotate_extrude write an
// open mesh where the top's hollow closes to its point, 2026-10-28)
module revolve_band(f, z0, z1) let (pts = [for (i = [0 : M]) let (z = z0 + (z1 - z0) * i / M) if (f(z) > 0.05) [f(z), z]])
    if (len(pts) > 1) rotate_extrude($fn = 180) polygon(concat([[0, pts[0][1]]], pts, [[0, pts[len(pts) - 1][1]]]));

// ---- the details -----------------------------------------------------------------------------
// The front is -y. Each raised detail stands on a plane laid against the
// surface at its own (xc, zc), turned to face out there, sunk SINK into the
// wall so its colour part is held in; its front is the shape as drawn, and a
// skirt under it climbs SH per 1 out so it prints. Cuts straight in from the
// front only grazed the cheeks round the curve (2026-10-28).
SINK = 0.6;
module raised(xc, zc, h, s = SINK) let (r = rf(zc)) rotate([0, 0, asin(xc / r)])
    translate([0, -r + s, 0]) rotate([90, 0, 0]) art_skirt(h + s, 2) translate([0, zc]) children();
// The face sits on the head's underside, which falls away below it to the
// waist: sunk SINK, the plane under a detail ended in the air below it, a lip
// the slicer propped (2,806 moves on the 72 mm top) and a sliver the gate read
// 0.05 mm thick. Sunk FS, its skirt always reaches the head, and it is cut off
// FIN inside the egg so it never reaches the hollow (2026-10-28).
FS = 3; FIN = W - 0.5;
module face(xc, zc, h) difference() {
    raised(xc, zc, h, FS) children();
    revolve_band(function (z) rf(z) - FIN, zc - 0.3 * H, zc + 0.1 * H);
}
PR = max(0.7, 0.011 * H);        // how far the face stands out
module oval(a, b) scale([a * H, b * H]) circle(1, $fn = 48);

// the concept's face, at its places
module eyes()   for (s = [-1, 1]) face(s * 0.10 * H, 0.73 * H, PR) oval(0.034, 0.046);
module nose()   face(0, 0.68 * H, PR * 0.8) oval(0.024, 0.016);
module cheeks() for (s = [-1, 1]) face(s * 0.17 * H, 0.67 * H, PR * 0.7) oval(0.04, 0.026);
// paws and the scarf's tail, held inside the belly (see RBELLY)
module paws()   for (s = [-1, 1]) raised(s * 0.12 * H, 0.40 * H, max(0.8, 0.012 * H)) oval(0.07, 0.05);
module tail()   raised(0.10 * H, 0.465 * H, max(0.8, 0.012 * H)) rotate(-12) oval(0.045, 0.10);

// ---- ears ------------------------------------------------------------------------------------
// At the concept's place on the head, leaning out as its do, but with the
// outer edge at 40 deg (the concept's lean 68 and would hang in the air):
// AT of tilt and AH of taper. Each base sits inside the head.
AT = 14; AH = 26; EL = 0.13 * H;   // 0.17 as the concept, the next cat's ear tips met this one's ceiling
module ears() for (s = [-1, 1]) let (th = 34, xb = s * 0.30 * H * sin(th) * 0.92, zb = (0.74 + 0.26 * cos(th) * 0.92) * H)
    translate([xb, 0, zb]) rotate([0, s * AT, 0]) hull() {
        translate([0, 0, -0.04 * H]) scale([EL * tan(AH), 0.05 * H, 1]) cylinder(r = 1, h = 0.01, $fn = 40);
        translate([0, 0, EL - 0.04 * H]) sphere(r = max(0.02 * H, 0.8), $fn = 24);
    }

// ---- the parts -------------------------------------------------------------------------------
MARK = H >= 40;                  // the maker's mark only where 4.4 mm letters fit the foot
module clip() intersection() { children(); cylinder(r = RBELLY, h = 2 * H, $fn = 180); }
module trim() clip() { scarf(); paws(); tail(); }
FACE = true;        // false only to test what the slicer props
module dark() if (FACE) clip() { eyes(); nose(); }
module pink() if (FACE) clip() cheeks();

module bottom() difference() {
    union() {
        revolve_band(function (z) rf(z), 0, ZS);
        // the neck, from inside the belly to the thread's top
        translate([0, 0, ZS - 1]) cylinder(r = RM - TDEP + 0.01, h = 1.01, $fn = 180);
        translate([0, 0, ZS]) thread_chamfer(2 * RM, TL, TDEP) thread_solid(2 * RM, TP, TL, TDEP);
    }
    revolve_band(function (z) cav_bot(z), FL, ZS);
    translate([0, 0, ZS - 1]) cylinder(r = RO, h = TL + 2, $fn = 180);
    if (MARK) obc_engrave(4.4, MD, 0.15, ridges = false);
}
module top_hollow() {
    // the female thread, grown CLR all round, and its lead-in at the rim, 0.1
    // past the thread: flush with its crest, the cone and the cut met in a
    // zero-volume sliver that read as non-manifold; wider, it thinned the rim
    translate([0, 0, ZS - 0.01]) thread_solid(2 * RM, TP, ZF - ZS + 0.01, TDEP, CLR);
    translate([0, 0, ZS - 0.01]) cylinder(r1 = RM + CLR + 0.1, r2 = RM - TDEP + CLR, h = (TDEP + 0.1) * THREAD_FLANK, $fn = 180);
    // and its lead-out under ZF, the same cone: cut off flat, the thread's last
    // tooth ended in a wedge the gate read down to 0.01 mm (the 43 mm top)
    translate([0, 0, ZF - (TDEP + 0.1) * THREAD_FLANK]) cylinder(r1 = RM - TDEP + CLR, r2 = RM + CLR + 0.1, h = (TDEP + 0.1) * THREAD_FLANK + 0.01, $fn = 180);
    revolve_band(function (z) cav_top(z), ZF - 0.01, ZT);
}
// one colour of the top (c), or all of it
module top(c = "all") difference() {
    if (c == "all") union() { revolve_band(function (z) rf(z), ZS, H); ears(); trim(); dark(); pink(); }
    else if (c == "body") difference() { union() { revolve_band(function (z) rf(z), ZS, H); ears(); } trim(); dark(); pink(); }
    else if (c == "trim") difference() { trim(); dark(); pink(); }
    else if (c == "dark") dark();
    else if (c == "pink") difference() { pink(); dark(); }
    top_hollow();
    // nothing below the seam: the smallest top's paw skirts reached under its rim
    translate([0, 0, ZS - H]) cylinder(r = H, h = H, $fn = 60);
}
module solid(c = "all") difference() {
    if (c == "all") union() { revolve_band(function (z) rf(z), 0, H); ears(); trim(); dark(); pink(); }
    else if (c == "body") difference() { union() { revolve_band(function (z) rf(z), 0, H); ears(); } trim(); dark(); pink(); }
    else if (c == "trim") difference() { trim(); dark(); pink(); }
    else if (c == "dark") dark();
    else if (c == "pink") difference() { pink(); dark(); }
    if (MARK) obc_engrave(4.4, MD, 0.15, ridges = false);
}

// printed: the top stands on its rim
if (part == "bottom") bottom();
else if (part == "top") translate([0, 0, -ZS]) top();
else if (len(part) > 4 && part[3] == "_") translate([0, 0, -ZS]) top(chr([for (i = [4 : len(part) - 1]) ord(part[i])]));
else if (part == "solid") solid();
else if (len(part) > 6 && part[5] == "_") solid(chr([for (i = [6 : len(part) - 1]) ord(part[i])]));
else if (part == "all") { if (fig == 4) solid(); else { bottom(); top(); } }
