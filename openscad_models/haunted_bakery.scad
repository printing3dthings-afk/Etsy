// Haunted Bakery lantern -- building #6 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md). A hollow shell lit from inside by a
// battery LED tealight: open base, true through-cut windows.
//
// THE STYLE, SHARED BY EVERY BUILDING IN THE TOWN: a ridge that SAGS in the
// middle while the eaves stay straight, a crooked chimney, steep roofs, and
// walls / roof / trim / accent printed as separate AMS colours in one 3MF.
// THE BAKERY'S OWN FEATURES: a round shop window framed by a crimped pie
// crust and cut into slices, a lattice pie cooling on a crate beside it, and
// a BAKERY sign hung crooked.
//
// COLOUR PARTS. Render one at a time with -D part="...":
//   body    walls, plinth, gables and their battens, eave flare, step
//   roof    roof slab, shingles, ridge cap, chimney
//   trim    window and door frames, muntins, door, corner boards, sign board,
//           the crate
//   accent  the pie-crust window frame, the pie, the sign's letters
// Every part is built DISJOINT from the others -- a later part is subtracted
// from an earlier one rather than trusting the slicer with an overlap. The
// part="chk_*" renders are each pairwise intersection and must come out empty.
//
// PRINTS WITH NO SUPPORTS, AND THAT DROVE MOST OF THE DETAIL. tools/
// product_gate.py fails a model on a single support move or overhang
// perimeter, sliced at a 45 deg threshold. The first build had supports
// almost everywhere: a 45 deg eave flare, flat groove ceilings under every
// clapboard and every shingle course, the bottom edge of every raised frame,
// a round window's crown, a shelf on 46 deg brackets, and lancets whose apex
// was only 40 deg from horizontal. Every downward-facing surface here is now
// at least 50 deg from horizontal:
//   - clapboard is a REVERSED sawtooth: each board ramps OUT going up at 40
//     deg from vertical, and steps back in on an upward-facing ledge;
//   - shingle courses are ADDED, not cut: each course's butt is a vertical
//     face and its top slopes gently up, so nothing faces down;
//   - every raised relief has a SHEARED underside that rises 1.2 mm for each
//     1 mm it stands out -- 40 deg -- and a flat top (see relief_up);
//   - every window is round with its crown replaced by two 58 deg lines (a
//     round crown is flat at the top), and the door's head is the same;
//   - where two overhanging faces meet at an outside corner they must BOTH be
//     58 deg or steeper: measured on the gate's slicer, a corner of two 50 deg
//     faces drew 54,002 support moves and one of two 58 deg faces drew none.
//
// TEALIGHT. The inside is 80.6 x 52.6 mm clear from the plate up to 78 mm,
// and the open base is the same size, so a 38 mm LED tealight (the biggest
// common size is 38 x 45 mm) drops in with more than 7 mm to spare on every
// side. The switch is under the light, so the house lifts off to switch it.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ----------------------------------------------------------------
W        = 84;              // along X, the front's width
D        = 56;              // along Y, front (-Y) to back
wall     = 1.68;            // 4 x 0.42
sid_d    = 0.84;            // clapboard stands 2 extrusions proud of plan(0)
corner_r = 1;
H        = 78;              // top of the side walls, where the eave flare begins
plinth_h = 8;               // shared by every building in the town
plinth_o = sid_d + 0.84;    // plinth face, 0.84 proud of the siding
sid_p    = 4.5;             // clapboard course
sid_r    = sid_d * tan(58); // height of each board's outward ramp: 58 deg from
                            // horizontal. 50 was enough for the ramp alone, but
                            // where a ramp crosses a window's crown the two meet
                            // at a corner, and corners need 58 (see the roof note below).

SH       = 1.2;             // shear of every raised relief: 1.2 up per 1 out,
                            // so its underside sits 40 deg from vertical

// ---- roof ----------------------------------------------------------------
e        = 5;               // eave projection
er       = e / tan(40);     // ...carried on a flare 40 deg from vertical
f        = 4;               // fascia height
b        = D/2 + sid_d;
be       = b + e;           // eave edge, half-depth
zf       = H + er + f;      // top of the fascia, where the slope starts
tr       = 2.52;            // slab thickness, normal to the slope (6 extr.)
// NO RAKE OVERHANG, and that is a measured decision. Past a gable the roof's
// underside rises inward at ~50 deg while the rake has to grow outward, and at
// the corner where those meet the outline moves diagonally -- root 2 faster
// than either face. Measured on the gate's own slicer: two 50 deg faces
// meeting at a corner drew 54,002 support moves, 55 deg drew 46,966, and only
// 58 deg or steeper came out clean. No rake angle rescues a 50 deg roof, so
// the roof stops 0.3 mm short of each gable face (distinct surfaces, never
// coplanar) and the gable's top edge shows as a small reveal.
Xw       = W/2 + sid_d;     // gable face
Xr       = Xw;              // roof end
R_end    = 136;             // ridge at the gable ends
sag      = 9;               // ...and 9 mm lower in the middle
// Pitch runs 54.6 deg at the ends to 49.6 deg mid-span. The roof's underside
// -- the lantern's ceiling -- is the flattest downward face in the model, and
// it is still 49 deg from horizontal where the ridge sags most.

function Rz(x)  = R_end - sag * (1 - pow(x / Xr, 2));
function alp(x) = atan((Rz(x) - zf) / be);
function tv(x)  = tr / cos(alp(x));                   // slab, measured vertically
function top_z(x, y) = zf + (Rz(x) - zf) * (be - abs(y)) / be;
function flare_z(y) = H + (abs(y) - b) * er / e;
// The inner line is the ceiling of the inside AND the boundary between roof
// colour and wall colour, so the slab sits directly on the lantern's hollow.
//   - Its eave end sits 0.03 ABOVE the flare's outer edge. 0.3 below it, the
//     fascia started lower than the flare could reach and hung a 0.24 mm
//     ledge along both eaves; ON the edge, the surfaces coincided.
//   - Its apex is LEVEL, not sagging with the outside. Measured on the gate's
//     slicer with a plain test box: an inside ridge sagging 9 mm drew 12,789
//     support moves, the same ridge level drew none -- a sagging ridge closes
//     from the middle outward and the closing tip is an overhang. So the
//     outside sags and the inside does not, and the slab thickens toward the
//     gables where nobody sees it.
zi_0 = H + er + 0.03;
zi_1 = Rz(0) - tv(0) - 0.3;
function zi(x, y) = zi_1 - (zi_1 - zi_0) * abs(y) / be;

// ---- plan ----------------------------------------------------------------
module plan2d(g) { offset(r = g) offset(r = corner_r) square([W - 2*corner_r, D - 2*corner_r], center = true); }
function plan_pts(g, z) = [for (p = rrect_pts(W + 2*g, D + 2*g, corner_r + g, 5)) [p[0], p[1], z]];

// Place children on a wall. Local x runs along the wall as a viewer outside
// sees it (left to right), local y is world up, local z is out from plan(0).
//   face 0 = back (+Y), 1 = front (-Y), 2 = right gable (+X), 3 = left gable (-X)
module face_tf(face, u, z) {
    r = [180, 0, 90, -90][face];
    p = face == 0 ? [u, D/2, z] : face == 1 ? [u, -D/2, z]
      : face == 2 ? [W/2, u, z] : [-W/2, u, z];
    translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
}
// In face coordinates: lift everything by SH per mm it stands out.
module shear_up() multmatrix([[1, 0, 0, 0], [0, 1, SH, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
// A raised relief of `outer` (with `hole` taken out), from depth d0 to d1 out
// of the wall: its UNDERSIDE sheared, its top flat. Shearing the whole relief
// leaned its top forward into a 40 deg knife edge along every frame, sign and
// letter, and the gate's wall check measured those edges as sub-bead
// material. The intersection keeps the higher of the two bottoms and the
// lower of the two tops.
//   - The flat piece is the outline SWEPT DOWN, and 0.2 wider each side, so
//     only its upper edge is ever used. Unswept, the crust's crimp bumps kept
//     their flat undersides down both sides of the disc, and the two pieces'
//     side faces coincided on every frame (110 zero-area faces, and support
//     columns from the plate to the crust).
//   - The hole's CEILING rises with depth like every other underside; its
//     floor stays flat. With the hole cut from the flat piece only, each
//     lancet's tip closed straight across and drew a support column; sheared
//     from d0 = -0.4 its floor dropped half a millimetre inside the wall and
//     left slivers against the inner muntins' feet. So the sheared hole is
//     lifted to meet the flat one at d0 and only ever rises from there.
module relief_hole(d0, a, b) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up() translate([0, 0, a]) linear_extrude(b - a) translate([0, -SH * d0]) children();
}
module relief_up(d0, d1) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up() translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1) children(1);
    }
}

// ---- walls: reversed-sawtooth clapboard ------------------------------------
// One skin up the whole wall. Each course starts at plan(0), ramps out to
// plan(sid_d) over sid_r (32 deg from vertical), runs flat, and steps back to
// plan(0) at the next course over 0.02 mm -- an upward-facing ledge, which
// needs nothing under it.
module siding_wall() {
    n = ceil((H - plinth_h) / sid_p);
    skin(concat(
        [plan_pts(0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = plinth_h + k * sid_p,
                 z  = [z0 + 0.02, z0 + sid_r, z0 + sid_p][j],
                 g  = [0, sid_d, sid_d][j])
            if (z < H + 0.4) plan_pts(g, z)],
        [plan_pts(sid_d, H + 0.5)]), slices = 0);
}

// ---- roof sections -------------------------------------------------------
// ROOF = ONE SLAB + A CORE UNDER IT. The slab runs the full length and is
// the only thing whose top is the roof surface; the core (gable
// triangles and eave flare) stops INSIDE it. A full-height main roof
// overlapping a separate rake slab put two identical top surfaces on each
// other and left 19 zero-area faces along both gables.
// Every section here is counter-clockwise in (y, z), which is what skin()
// needs to face its surfaces outward.
// The flare stops 0.08 short of the fascia face. 0.2 short left a 0.24 mm
// ledge the slicer printed as an overhang along both eaves; 0.05 past it left
// a knife lip the wall check measured as sub-bead; exactly on it, its edge lay
// in the fascia's plane and gave 152 zero-area faces; 0.01 short still gave
// 144. 0.08 leaves a 0.13 mm step, under the slicer's 0.185 mm allowance.
function core_prof(x) = [for (p = [
        [-b, H - 1], [b, H - 1], [b, H], [be - 0.08, flare_z(be - 0.08)],
        [be - 1, top_z(x, be - 1) - tv(x)/2], [0, Rz(x) - tv(x)/2],
        [-(be - 1), top_z(x, be - 1) - tv(x)/2], [-(be - 0.08), flare_z(be - 0.08)],
        [-b, H]]) [x, p[0], p[1]]];
// The slab's underside is drawn 0.3 mm BELOW the zone line so the zone clips
// it; drawn on the line, the two surfaces were coincident.
function slab_prof(x) = [for (p = [
        [be, zi_0 - 0.3], [be, zf], [0, Rz(x)], [-be, zf], [-be, zi_0 - 0.3],
        [0, zi_1 - 0.3]]) [x, p[0], p[1]]];
function zone_prof(x) = [for (p = [
        [-be - 3, zi(x, be + 3)], [0, zi(x, 0)], [be + 3, zi(x, be + 3)],
        [be + 3, 400], [-be - 3, 400]]) [x, p[0], p[1]]];
// The hollow reaches 0.3 mm INTO the roof zone rather than stopping on it.
// The two are sampled at different stations along the sag, and their
// straight-line spans differ by fractions of a millimetre -- enough to leave
// twelve lens-shaped slivers of wall floating inside the roof.
function cav_prof(x) = let (bi = D/2 - wall) [for (p = [
        [-bi, H - 1], [bi, H - 1], [bi, zi(x, bi) + 0.3], [0, zi(x, 0) + 0.3],
        [-bi, zi(x, bi) + 0.3]]) [x, p[0], p[1]]];

function stations(a, c, n) = [for (i = [0 : n]) a + (c - a) * i / n];
// The slab, the zone and the shingles share ONE set of stations, so the
// straight spans between stations stay parallel and every 0.3 mm margin
// between them holds everywhere, not just at the stations.
// 48 spans, not 16. With the sag, each span between stations is a slightly
// twisted quad, and two skins with different vertices triangulate that twist
// differently -- by up to 0.6 mm near the gables at 16 spans, which is more
// than the 0.3 mm margins below, and left 29 sealed voids between the
// shingles and the slab. At 48 spans the disagreement is under 0.2 mm.
ROOF_ST = stations(-Xr - 1, Xr + 1, 48);

module core_roof() { skin([for (x = stations(-Xw, Xw, 42)) core_prof(x)], slices = 0); }
module zone()      { skin([for (x = ROOF_ST) zone_prof(x)], slices = 0); }
module slab()      { skin([for (x = ROOF_ST) slab_prof(x)], slices = 0); }
module cavity() {
    translate([0, 0, -2]) linear_extrude(H + 1) plan2d(-wall);
    skin([for (x = stations(-(W/2 - wall), W/2 - wall, 42)) cav_prof(x)], slices = 0);
}

module roof_end_clip() { cube([2 * (Xw - 0.3), 2 * be + 20, 600], center = true); }

// SHINGLES, BY ADDITION. Course k runs up-slope from u_k (distance in from
// the eave) to u_k+1. It starts 1.0 mm proud of the slab -- the butt, a
// vertical face -- and thins to 0.05 at its upper end, which runs 0.5 mm on
// under the next course's butt. That butt is vertical too, so no face in the
// roof points down. Courses run parallel to the eave; because the ridge sags
// and the eave does not, every butt line bows.
sh_t  = 1.0;
sh_c  = 3.4;
SH_U  = concat([for (k = [0 : floor((be - 1.2) / sh_c)]) k * sh_c], [be - 0.7]);
module shingles() {
    for (s = [-1, 1], k = [0 : len(SH_U) - 2])
        let (u0 = SH_U[k], u1 = min(SH_U[k + 1] + 0.5, be - 0.7))
        skin([for (x = ROOF_ST) let (y0 = s * (be - u0), y1 = s * (be - u1),
                  q = [[x, y0, top_z(x, y0) - 1.0], [x, y0, top_z(x, y0) + sh_t],
                       [x, y1, top_z(x, y1) + 0.05], [x, y1, top_z(x, y1) - 1.0]])
              s > 0 ? q : [for (i = [3 : -1 : 0]) q[i]]], slices = 0);
}
// ridge cap, astride both top courses; its flanks are steeper than the roof
module ridge_cap() {
    skin([for (x = ROOF_ST) [
        [x, 1.8, top_z(x, 1.8) - 1.0], [x, 1.8, top_z(x, 1.8) + 0.6], [x, 0, Rz(x) + 1.6],
        [x, -1.8, top_z(x, 1.8) + 0.6], [x, -1.8, top_z(x, 1.8) - 1.0]]], slices = 0);
}

// ---- chimney: crooked, on the right gable ------------------------------------
ch_y  = 17.5;               // 0.5 mm clear of the corner board at y 24.5
ch_x0 = W/2 - 1;            // 1 mm into the 2.52 mm gable wall, clear of the hollow
ch_dx = 9.84;
ch_w  = 13;
ch_z  = 124;                // straight stack to here, clear of the roof
module ch_slice(cx, z, gx = 0, gy = 0)
    translate([cx, ch_y, z]) linear_extrude(0.01)
        square([ch_dx + 2*gx, ch_w + 2*gy], center = true);
module chimney() {
    c0 = ch_x0 + ch_dx/2;
    translate([ch_x0, ch_y - ch_w/2, 0]) cube([ch_dx, ch_w, ch_z]);
    // The kink leans AWAY from the roof at 20.6 deg from vertical, then rises
    // straight. It used to lean back again, and the outward knife-ridge that
    // made was measured as sub-bead material by the gate's wall check.
    hull() { ch_slice(c0, ch_z - 0.01); ch_slice(c0 + 3, ch_z + 8); }
    translate([c0 + 3 - ch_dx/2, ch_y - ch_w/2, ch_z + 7.99]) cube([ch_dx, ch_w, 6.02]);
    hull() { ch_slice(c0 + 3, ch_z + 13.99); ch_slice(c0 + 3, ch_z + 16, 1.2, 1.2); }  // 31 deg corbel
    translate([c0 + 3, ch_y, ch_z + 17.2]) cube([ch_dx + 2.4, ch_w + 2.4, 2.4], center = true);
    translate([c0 + 3, ch_y, ch_z + 18.3]) {
        cylinder(r = 3, h = 4.7, $fn = 40);
        translate([0, 0, 4.7]) cylinder(r1 = 3, r2 = 3.8, h = 1.0, $fn = 40);   // 38.7 deg
        translate([0, 0, 5.7]) cylinder(r = 3.8, h = 0.8, $fn = 40);
    }
}

// ---- openings ------------------------------------------------------------------
// A circle whose crown is replaced by its two 58 deg tangents -- a teardrop.
// The tangents leave the circle at 32 and 148 deg and meet r/sin(32) above
// its centre.
function drop_pts(r, n = 64) = concat(
    [for (i = [0 : n]) let (t = 148 + 244 * i / n) [r * cos(t), r + r * sin(t)]],
    [[0, r + r / sin(32)]]);
function drop_top(r) = r + r / sin(32);
// The door: straight sides under the same crown -- a half circle whose top
// is replaced by its two 58 deg tangents.
function round_head_pts(a, hgt, n = 16) = concat(
    [[-a, 0], [-a, hgt]],
    [for (i = [1 : n]) let (t = 180 - 32 * i / n) [a * cos(t), hgt + a * sin(t)]],
    [[0, hgt + a / sin(32)]],
    [for (i = [0 : n - 1]) let (t = 32 - 32 * i / n) [a * cos(t), hgt + a * sin(t)]],
    [[a, hgt], [a, 0]]);
mull = 1.68;

// Every window is described once, in this table, and every part that needs
// it -- the cut in the wall, the frame, the muntins -- reads the same row.
//   [face, u, z, kind, r]
//   Every window is ROUND WITH A POINTED CROWN (the town's variety plan,
//   2026-09-25: pointed lancets belong to the chapel now). kind "S" is the
//   shop window in its pie-crust frame; kind "R" the rest, in plain frames.
WINDOWS = [
    [1,   4, 19, "S", 7],
    [1, -30, 54, "R", 4.5], [1, 30, 54, "R", 4.5],   // 4.5: at 5 the frame met the sign
    [0, -20, 16, "R", 6.5], [0, 20, 16, "R", 6.5],
    [0, -20, 54, "R", 5],   [0, 20, 54, "R", 5],
    [3,   0, 16, "R", 6.5], [3, 0, 54, "R", 6], [3, 0, 90, "R", 3.5],
    // right gable: kept to the front half, the chimney owns y 11..24
    [2, -13, 16, "R", 6],   [2, -13, 52, "R", 6], [2, -8, 90, "R", 3.5],
];

module win_outline(w) { polygon(drop_pts(w[4])); }
// Every window: three bars through its centre at 90, 55 and 125 deg, which
// cut it into six slices -- the bakery's pies; every bar's underside is at
// least 55 deg.
module win_bars(w) {
    translate([0, w[4]]) for (a = [90, 55, 125]) rotate(a) square([6 * w[4], mull], center = true);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
fr_w = 1.7;
fr_t = sid_d + 0.84;        // frame face, 0.84 proud of the siding
// The frame starts 0.3 OUTSIDE the opening, leaving a hairline of wall
// between them. With the frame's edge on the opening itself the wall's cut
// face and the frame's face were one polygon, and every muntin crossing it
// left non-manifold edges; a lip inside the opening fixed that but was a
// 0.3 mm fin.
// The frame's bottom bar runs 2.6 mm deeper than its sides -- a proper sill.
// Its underside is sheared, so at the frame's face the bar has lost 2.5 mm of
// height; a 1.7 mm bar shrank to a knife edge there.
fr_sill = 2.6;
module win_frame_outer(w) {
    union() {
        offset(r = fr_w + 0.3) win_outline(w);
        translate([-w[4] - fr_w - 0.3, -fr_w - 0.3 - fr_sill]) square([2 * (w[4] + fr_w + 0.3), fr_w + fr_sill + 1]);
    }
}

// The shop window's frame is a pie crust: a disc crimped round its edge.
crust_r = 15.5;
module crust_outer(w) {
    translate([0, w[4]]) union() {
        circle(r = crust_r, $fn = 96);
        for (i = [0 : 17]) rotate(i * 20) translate([crust_r, 0]) circle(r = 1.3, $fn = 20);
    }
}

// Inside every frame's hole the clapboard is cut back to 0.2 into the wall.
// Left standing, the siding above each lancet's tip was walled in by the
// frame and the mullion and came out as three loose 0.05 mm3 slivers.
// 0.1 wider than the hole, reaching into the frame: cut exactly to the hole,
// its edge met the clapboard's where the round window is widest and left 32
// non-manifold edges.
module frame_holes() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) win_outline(w);
}
module openings() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + sid_d + 4) win_outline(w);
    face_tf(1, door_x, plinth_h)
        translate([0, 0, -wall - 2]) linear_extrude(wall + sid_d + 4)
            polygon(round_head_pts(door_a, door_h));
}

// ---- door, step, crate ----------------------------------------------------------
door_x = -24;
door_a = 6.5;
door_h = 25;                // straight sides; the crown adds a / sin(32)
module door_leaf() {
    // Set back from the siding so it reads as a recess, with a small round
    // light so the door glows as well. It stops 0.2 short of the frame's back
    // plane so the two never meet on a bare edge inside one part.
    face_tf(1, door_x, plinth_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
        difference() {
            polygon(round_head_pts(door_a, door_h));
            translate([0, 22]) polygon(drop_pts(2.2));
        }
}
// Unsheared on purpose: the door frame's feet stand on the plinth, and its
// only downward face is the doorway's own crown.
module door_frame() {
    // Clip to the threshold FIRST, then take out a doorway that runs 1 mm
    // below it. Cutting the frame's foot off with a square whose top edge sat
    // exactly on the doorway's bottom edge left a zero-width sliver, and CGAL
    // refused the whole trim part: "The given mesh is not closed".
    face_tf(1, door_x, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
        difference() {
            intersection() { offset(r = fr_w) polygon(round_head_pts(door_a, door_h));
                             translate([-20, 0]) square([40, 100]); }
            translate([0, -1]) polygon(round_head_pts(door_a, door_h + 1));
        }
}
st_w = 22;  st_d = 9;
module step() { face_tf(1, door_x, 0) translate([-st_w/2, 0, 0]) cube([st_w, plinth_h, st_d]); }

// The crate stands on the plate, so the pie needs no shelf, no bracket and
// no support. Vertical plank joints only -- a horizontal groove would have a
// ceiling.
cr_u = 29;  cr_w = 12;  cr_d = 12.5;  cr_h = 13;
module crate() {
    face_tf(1, cr_u, 0) difference() {
        translate([-cr_w/2, 0, -0.4]) cube([cr_w, cr_h, cr_d + 0.4]);
        for (x = [-2, 2]) translate([x - 0.35, -1, cr_d - 0.5]) cube([0.7, cr_h + 2, 1]);
    }
}
module pie() {
    // sunk 0.3 into the crate so the two parts overlap rather than touch
    face_tf(1, cr_u, cr_h - 0.3) translate([0, 0, 6.4]) rotate([-90, 0, 0]) {
        // the pan widens as it rises (27 deg) into a plain rim, so there is no
        // ledge under it. A crimped rim of 0.75 mm bumps was measured as
        // sub-bead material and is too small to print as bumps anyway.
        cylinder(r1 = 4.8, r2 = 5.95, h = 2.2, $fn = 48);
        translate([0, 0, 2.2]) cylinder(r = 5.95, h = 1.1, $fn = 48);
        translate([0, 0, 3.3]) scale([1, 1, 0.32]) sphere(r = 5.0, $fn = 48);
        // lattice strips following the dome, 0.5 mm proud of it
        intersection() {
            translate([0, 0, 3.8]) scale([1, 1, 0.32]) sphere(r = 5.0, $fn = 48);
            translate([0, 0, 3.3]) cylinder(r = 4.6, h = 2.4, $fn = 48);
            for (a = [0, 90], i = [-1, 0, 1]) rotate(a) translate([-6, i * 2.6 - 0.45, 3.3]) cube([12, 0.9, 2.2]);
        }
    }
}

// ---- sign --------------------------------------------------------------------------
sg_u = 4;   sg_z = 51;    sg_w = 38;  sg_h = 9;
sg_tilt = -3;               // hung crooked, right end low
module sign_board() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt])
        relief_up(-0.4, fr_t) translate([-sg_w/2, -sg_h/2]) square([sg_w, sg_h]);
}
// The letters are a FLUSH inlay in the board's face, in the accent colour --
// no relief. Raised 1 mm, every horizontal stroke was a sub-bead slab with
// an underside; inlaid, the colour does the work and the face stays flat.
module sign_letters() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t - 0.8])
        linear_extrude(0.8) text("BAKERY", size = 5.2, font = "Montserrat:style=Black",
                                 halign = "center", valign = "center", spacing = 1.06);
}

// ---- trim that is not a window ------------------------------------------------------
module corner_boards() {
    translate([0, 0, plinth_h]) linear_extrude(H - plinth_h)
        intersection() {
            // 0.4 into the wall, past the siding's deepest point
            difference() { plan2d(fr_t); plan2d(-0.4); }
            for (sx = [-1, 1], sy = [-1, 1])
                translate([sx * (W/2 - 0.25), sy * (D/2 - 0.25)]) square([6.5, 6.5], center = true);
        }
}

// ---- gables: board and batten ----------------------------------------------------
// Above the wall head the gables carry vertical battens instead of clapboard.
// Their bottoms are sheared like every other relief; their tops are cut by the
// roof zone, so they run up under the slab.
bat_w = 1.68;
module battens() {
    // The cut-outs are sheared WITH the battens. Cut square, every batten that
    // resumed above a window started on a flat underside, and the slicer ran
    // support columns from the plate up to each one.
    for (face = [2, 3]) face_tf(face, 0, H - 0.2) shear_up()
        difference() {
            for (u = [-24 : 6 : 24])
                translate([u - bat_w/2, 0, sid_d - 0.4]) cube([bat_w, 70, 0.84 + 0.4]);
            // Clear of the gable windows and, on the right, the chimney. In
            // this frame local x is +y on the right gable and -y on the left.
            for (w = WINDOWS) if (w[0] == face)
                translate([(face == 2 ? w[1] : -w[1]) - w[4] - 3.5, w[2] - (H - 0.2) - 3.5 - fr_sill - 2, -5])
                    cube([2 * w[4] + 7, drop_top(w[4]) + 9 + fr_sill, 10]);
            if (face == 2) translate([ch_y - ch_w/2 - 1.5, -5, -5]) cube([ch_w + 3, 100, 10]);
        }
}

// ---- mark ------------------------------------------------------------------------
// Under the step, read from below. The plinth ring is too narrow to carry it,
// and a mark engraved into a wall has ceilings.
module brand_mark() {
    // 0.8 deep: at 1.2 the slivers left between the letters' strokes were
    // measured as sub-bead walls.
    translate([door_x, -D/2 - st_d / 2, -0.5]) linear_extrude(1.3)
        mirror([0, 1, 0]) text("OBC", size = 5.0, font = "Montserrat:style=Black",
                               halign = "center", valign = "center");
}

// ---- parts ---------------------------------------------------------------------------
module body_solid() {
    linear_extrude(plinth_h) plan2d(plinth_o);
    siding_wall();
    core_roof();
    step();
    battens();
}
module trim_raw() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) {
        if (w[3] == "R") relief_up(-0.4, fr_t) { win_frame_outer(w); offset(r = 0.3) win_outline(w); }
        // Muntins in two depths. Where they meet the FRAME they run 0.6 past
        // the opening, into it -- a real overlap. They are NOT sheared: a
        // mullion is vertical and every other bar is 50 deg or steeper.
        // Inside the wall they stop 0.25 SHORT of it: every way of making a
        // bar end meet the wall (flush, or notched in) left T-junctions and
        // zero-area faces round the round windows.
        // The shop window's spokes start 0.2 deeper than the crust: level
        // with its back they shared a plane and left zero-area faces.
        translate([0, 0, w[3] == "S" ? -0.6 : -0.4])
            linear_extrude(sid_d + 0.4 + (w[3] == "S" ? 0.84 + 0.2 : 0)) win_muntins(w, 0.6);
        // No second depth inside the wall: spokes anchor in the frame and
        // the wall. Let into a round window's CURVED sill as well, the shop
        // window's spokes left 32 non-manifold edges where the parts meet.
    }
    door_frame();
    door_leaf();
    corner_boards();
    crate();
    sign_board();
}
module accent_raw() {
    face_tf(1, WINDOWS[0][1], WINDOWS[0][2])
        relief_up(-0.4, fr_t + 0.84) { crust_outer(WINDOWS[0]); offset(r = 0.3) win_outline(WINDOWS[0]); }
    pie();
    sign_letters();
}
module accent_part() { accent_raw(); }
module trim_part()   { difference() { trim_raw(); accent_raw(); } }
module roof_part() {
    union() {
        difference() {
            intersection() {
                union() {
                    intersection() { slab(); roof_end_clip(); }
                    core_roof();
                    intersection() { union() { shingles(); ridge_cap(); } roof_end_clip(); }
                }
                zone();
            }
            chimney();
        }
        chimney();
    }
}
module body_part() {
    difference() {
        body_solid();
        cavity(); zone(); openings(); frame_holes(); chimney(); trim_raw(); accent_raw(); brand_mark();
    }
}

if      (part == "none")   ;
else if (part == "body")   body_part();
else if (part == "roof")   roof_part();
else if (part == "trim")   trim_part();
else if (part == "accent") accent_part();
else if (part == "union")  union() { body_part(); roof_part(); trim_part(); accent_part(); }
else if (part == "chk_body_roof")    intersection() { body_part(); roof_part(); }
else if (part == "chk_body_trim")    intersection() { body_part(); trim_part(); }
else if (part == "chk_body_accent")  intersection() { body_part(); accent_part(); }
else if (part == "chk_roof_trim")    intersection() { roof_part(); trim_part(); }
else if (part == "chk_roof_accent")  intersection() { roof_part(); accent_part(); }
else if (part == "chk_trim_accent")  intersection() { trim_part(); accent_part(); }
else {
    color("#5B4A5E") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
}
