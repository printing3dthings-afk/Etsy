// Haunted Post Office lantern -- building #1 of the Haunted Town series
// (openscad_models/HAUNTED_TOWN.md), built on the bakery's proven parts
// (haunted_bakery.scad): same walls, roof, window frames, relief and every
// gate-tuned margin, so read that file for WHY each of those looks the way it
// does. A hollow shell lit from inside by a battery LED tealight: open base,
// true through-cut windows.
//
// THE POST OFFICE'S OWN FEATURES: an octagonal corner TURRET under a tall,
// leaning witch-hat spire; a crooked POST OFFICE sign; parcels tied with
// string stacked by the wall; a brass mail slot in the door.
//
// WHY OCTAGONAL. Every face of an octagon is flat, so the bakery's planar
// frames, muntins and clapboard carry onto the turret unchanged. On a round
// tower each of those would have had to be rebuilt on a curve.
//
// WHY THE SIGN IS ON THE WALL. A sign hanging from a bracket has a free bottom
// edge, which is an overhang no angle rescues. It is hung crooked instead.
//
// COLOUR PARTS. Render one at a time with -D part="...":
//   body    walls, plinth, turret walls, gables and battens, eave flare, step
//   roof    roof slab, shingles, ridge cap, chimney, turret spire and its eave
//   trim    window and door frames, muntins, door, corner boards, sign board,
//           the parcels' string
//   accent  the parcels, the sign's letters, the mail slot
// Every part is built DISJOINT from the others. The part="chk_*" renders are
// each pairwise intersection and must come out empty.
//
// TEALIGHT. The main room is 72.6 x 50.6 mm clear from the plate to the
// ceiling, and the base is open: a 38 mm LED tealight drops in with room to
// spare. The turret's hollow opens into it, so the turret glows too.

include <BOSL2/std.scad>
include <lattice_lib.scad>

$fa = 2;  $fs = 0.4;

part = "preview";

// ---- body ----------------------------------------------------------------
W        = 76;              // along X, the front's width
D        = 54;              // along Y, front (-Y) to back
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
R_end    = 135;             // ridge at the gable ends
sag      = 8;               // ...and 8 mm lower in the middle
// Pitch runs 55.1 deg at the ends to 49.9 deg mid-span, the bakery's to
// within a degree.

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

// ---- turret ------------------------------------------------------------------
// An octagon standing on the front-right corner, its centre 4 mm out from the
// block's corner on both axes so it reads as a tower rather than a bay. Its
// faces point every 45 deg from front (-Y).
tx      = W/2 + 4;
ty      = -D/2 - 4;
t_ap    = 13.86;            // apothem of plan(0): circumradius 15
// The wall top sits on a FLAT stretch of clapboard (course 23 runs flat from
// 112.84 to 116). On a ramp, the spire's eave would start wider than the wall
// below it and hang a ledge.
Ht      = 114.5;
t_et    = 3;                // spire eave projection...
t_eh    = t_et * tan(58);   // ...on a flare 58 deg from horizontal: an octagon's
                            // corners are convex, and corners need 58
t_fh    = 2.5;              // fascia
t_apc   = t_ap + sid_d + t_et;          // spire base apothem
zb      = Ht + t_eh + t_fh;             // spire base
sp_ang  = 62;               // spire faces, from horizontal
hs      = t_apc * tan(sp_ang);
lean    = [2.5, -2.5];      // apex pushed out, away from the house
// The spire's hollow is the spire moved DOWN, so every face keeps its slab
// thickness (tr, normal to the face) exactly.
sp_drop = tr / cos(sp_ang);
function oct_r(ap) = ap / cos(22.5);
module oct2d(ap) { rotate(22.5) circle(r = oct_r(ap), $fn = 8); }
function oct_pts(g, z) = [for (k = [0 : 7]) let (a = 22.5 + 45 * k, r = oct_r(t_ap + g))
                          [tx + r * cos(a), ty + r * sin(a), z]];
module t_slab(ap, z0, z1, c = [0, 0]) translate([tx + c[0], ty + c[1], z0]) linear_extrude(z1 - z0) oct2d(ap);
function sp_c(z) = lean * (z - zb) / hs;               // spire centre offset at height z
function sp_ap(z) = t_apc * (1 - (z - zb) / hs);        // spire apothem at height z

// Place children on a wall. Local x runs along the wall as a viewer outside
// sees it (left to right), local y is world up, local z is out from plan(0).
//   face 0 = back (+Y), 1 = front (-Y), 2 = right gable (+X), 3 = left gable (-X)
//   face 4 + k = turret face k, facing -90 + 45k deg (4 front, 5 front-right,
//   6 right, 7 back-right, 11 front-left)
module face_tf(face, u, z) {
    if (face >= 4) {
        th = -90 + 45 * (face - 4);
        translate([tx + t_ap * cos(th), ty + t_ap * sin(th), 0])
            rotate([0, 0, th + 90]) rotate([90, 0, 0]) translate([u, z, 0]) children();
    } else {
        r = [180, 0, 90, -90][face];
        p = face == 0 ? [u, D/2, z] : face == 1 ? [u, -D/2, z]
          : face == 2 ? [W/2, u, z] : [-W/2, u, z];
        translate(p) rotate([0, 0, r]) rotate([90, 0, 0]) children();
    }
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
//     only its upper edge is ever used. Unswept, the bakery crust's crimp bumps kept
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
// The turret's clapboard: the same courses, on the octagon.
module turret_siding() {
    n = ceil((Ht - plinth_h) / sid_p);
    skin(concat(
        [oct_pts(0, plinth_h - 0.5)],
        [for (k = [0 : n - 1], j = [0 : 2])
            let (z0 = plinth_h + k * sid_p,
                 z  = [z0 + 0.02, z0 + sid_r, z0 + sid_p][j],
                 g  = [0, sid_d, sid_d][j])
            if (z < Ht + 0.4) oct_pts(g, z)],
        [oct_pts(sid_d, Ht + 0.5)]), slices = 0);
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

// ---- chimney: crooked, on the LEFT gable -------------------------------------
// The turret owns the right-hand end, so the chimney moves to the left: the
// bakery's chimney, mirrored.
ch_y  = 16.5;               // 0.5 mm clear of the corner board at y 23.5
ch_x0 = W/2 - 1;            // 1 mm into the 2.52 mm gable wall, clear of the hollow
ch_dx = 9.84;
ch_w  = 13;
ch_z  = 124;                // straight stack to here, clear of the roof
module ch_slice(cx, z, gx = 0, gy = 0)
    translate([cx, ch_y, z]) linear_extrude(0.01)
        square([ch_dx + 2*gx, ch_w + 2*gy], center = true);
module chimney() mirror([1, 0, 0]) chimney_r();
module chimney_r() {
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

// ---- turret spire -----------------------------------------------------------------
// Eave flare, fascia, then an octagonal witch hat whose apex leans 3.5 mm out.
// Its faces are 62 deg from horizontal; leaning puts the back one at 57.5,
// and inside the hollow the shallowest line -- where two faces meet -- is
// still 55.8 deg, clear of the 50 the gate's slicer needs.
module spire_outer() hull() { t_slab(t_apc, zb - 0.01, zb); t_slab(0.05, zb + hs - 0.01, zb + hs, lean); }
// Shingles by addition, as on the roof. Course k's butt is a vertical octagon
// band from 1 mm inside the spire to sh_t proud of it; its top runs up to 0.5
// under the next course. Everything inside the hollow is cut off afterwards.
sp_c_z = 4.2;
module spire_shingles() {
    for (k = [0 : floor((hs - 8) / sp_c_z)]) let (z0 = zb + k * sp_c_z, z1 = z0 + sp_c_z + 0.5 * tan(sp_ang))
        hull() {
            t_slab(sp_ap(z0), z0 - 1, z0 + sh_t, sp_c(z0));
            t_slab(sp_ap(z1), z1 - 1, z1 + 0.05, sp_c(z1));
        }
}
module finial() {
    // a plain spike: every face of a cone narrowing upward faces up
    translate([tx + lean[0], ty + lean[1], zb + hs - 4])
        cylinder(r1 = 1.4, r2 = 0.6, h = 9, $fn = 16);      // a 0.2 tip did not print
}
module turret_cap() {
    hull() { t_slab(t_ap + sid_d, Ht, Ht + 0.01); t_slab(t_apc, Ht + t_eh - 0.01, Ht + t_eh); }
    t_slab(t_apc, Ht + t_eh, zb);
    spire_outer();
    spire_shingles();
    finial();
}
// The turret's hollow: its octagon, up into the spire. The spire's inside is
// the spire dropped by sp_drop, and below that the hollow is a plain column.
module turret_hollow() {
    intersection() {
        t_slab(t_ap - wall, -2, zb + hs);
        union() {
            t_slab(40, -2, zb - sp_drop + 0.5);
            translate([0, 0, -sp_drop]) spire_outer();
        }
    }
}
// Everything the turret occupies, as one solid: what the main roof must stay
// out of, and what the roof zone must not take from the turret's walls.
module turret_env() { t_slab(t_ap + sid_d, -2, Ht + 0.01); turret_cap(); }
// The room stops at the turret, whose wall stays WHOLE where it faces into the
// house. With the turret's hollow open to the room, it punched up through the
// room's sloping ceiling, and wherever the ceiling began at the hollow's edge
// its first layer had nothing under it or in front of it: 20,483 support
// moves. Against a solid wall the ceiling starts the way it does at every
// other wall. The light gets in through turret_arch().
module room() { difference() { cavity(); t_slab(t_ap + sid_d, -3, 300); } }
// Where the room would have run inside the turret, the turret is solid wall.
module room_fill() { intersection() { t_slab(t_ap + sid_d, 0, Ht); cavity(); } }
// A tall pointed arch through the turret's wall where it faces into the house
// (face 9, 135 deg): the tealight's way into the turret. Hidden from outside.
module turret_arch() {
    // 7 wide in an 11.5 mm face, so the turret keeps real posts at its corners
    face_tf(9, 0, -1) translate([0, 0, -4]) linear_extrude(6) polygon(lancet_pts(3.5, 36));
}

// ---- openings ------------------------------------------------------------------
// d = 5.6a puts the apex tangent at 58 deg from horizontal. The manor's
// d = 1.8a landed at 40 deg, which a 45 deg threshold catches outright; 50
// deg (d = 3.3a) was enough for the arch alone but not where a clapboard
// ramp crosses it and the two form a corner.
function lancet_pts(a, hgt, n = 24) =
    let (d = a * 5.6, R = d + a)
    concat([[-a, 0], [-a, hgt]],
           [for (i = [1 : n - 1]) let (x = -a + 2*a*i/n)
                [x, hgt + sqrt(max(R*R - pow(abs(x) + d, 2), 0))]],
           [[a, hgt], [a, 0]]);
function lancet_top(a, hgt) = hgt + a * sqrt(pow(6.6, 2) - pow(5.6, 2));
mull = 1.68;

// Every window is described once, in this table, and every part that needs
// it -- the cut in the wall, the frame, the muntins -- reads the same row.
//   [face, u, z, "L", a, hgt]  -- a lancet of half-width a, sides hgt tall
// Turret faces are 11.5 mm wide, so its lancets are a = 3 (frame 10 wide).
WINDOWS = [
    [1, -24, 54, "L", 4.5, 4],                              // front, over the door
    [1,   2, 16, "L", 6, 8],                                // front, the counter window
    [0, -20, 16, "L", 5.5, 9], [0, 20, 16, "L", 5.5, 9],
    [0, -20, 54, "L", 4.5, 4], [0, 20, 54, "L", 4.5, 4],
    // gables (u is world y): the turret owns the right end's front, the
    // chimney the left end's back
    [2,   6, 16, "L", 5, 9],  [2,   6, 52, "L", 5, 9],  [2,  2, 90, "L", 3.5, 3],
    [3, -12, 16, "L", 5, 9],  [3, -12, 52, "L", 5, 9],  [3, -4, 90, "L", 3.5, 3],
    // Turret: the front and right faces only, three storeys. On the diagonal
    // faces every bar sits at 45 deg to the gate's measuring rays, which read
    // each bar's corner as a sliver: 0.52 mm 1st-percentile wall, from bars
    // that are 1.24 x 1.68 mm. The diagonals keep plain clapboard.
    for (f = [4, 6]) each [[f, 0, 20, "L", 3, 7], [f, 0, 56, "L", 3, 7], [f, 0, 90, "L", 2.8, 5]],
];

module win_outline(w) { polygon(lancet_pts(w[4], w[5])); }
// A mullion and a CHEVRON transom at 50 deg, never a flat bar. The turret's
// narrow lancets (a < 4) keep the mullion only: their chevron ran down into
// the corner of sill and jamb and left non-manifold edges there.
module win_bars(w) {
    translate([-mull/2, -1]) square([mull, lancet_top(w[4], w[5]) + 2]);
    if (w[4] >= 4) for (s = [-1, 1]) translate([0, w[5] * 0.62]) rotate(s < 0 ? -130 : -50)
        translate([0, -mull/2]) square([2 * w[4], mull]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
// Inside the wall the bars stop 0.25 short of the opening -- but only ABOVE
// the spring line. Below it they run 0.3 INTO the sill and jambs, because a
// bar whose foot stops short of the sill hovers 0.25 mm over it, and the
// slicer printed every one of those feet as an overhang perimeter.
module win_muntins_inner(w) {
    split = w[5];
    intersection() {
        win_bars(w);
        union() {
            offset(r = -0.25) win_outline(w);
            intersection() { offset(r = 0.3) win_outline(w); translate([-50, -5]) square([100, split + 5]); }
        }
    }
}

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

// Inside every frame's hole the clapboard is cut back to 0.2 into the wall.
// Left standing, the siding above each lancet's tip was walled in by the
// frame and the mullion and came out as three loose 0.05 mm3 slivers.
// 0.1 wider than the hole, reaching into the frame: cut exactly to the hole,
// its edge met the clapboard's and left non-manifold edges on the bakery.
module frame_holes() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        relief_hole(-0.4, -0.2, fr_t + 1.84) offset(r = 0.4) win_outline(w);
}
module openings() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2])
        translate([0, 0, -wall - 2]) linear_extrude(wall + sid_d + 4) win_outline(w);
    face_tf(1, door_x, plinth_h)
        translate([0, 0, -wall - 2]) linear_extrude(wall + sid_d + 4)
            polygon(lancet_pts(door_a, door_h));
}

// ---- door, step, parcels ---------------------------------------------------------
door_x = -24;
door_a = 6.5;
door_h = 15;
module door_leaf() {
    // Set back from the siding so it reads as a recess, with a small lancet
    // light so the door glows as well. It stops 0.2 short of the frame's back
    // plane so the two never meet on a bare edge inside one part.
    face_tf(1, door_x, plinth_h) translate([0, 0, -wall]) linear_extrude(wall - 0.2)
        difference() {
            polygon(lancet_pts(door_a, door_h));
            translate([0, 14]) polygon(lancet_pts(2.4, 1.5));
        }
}
// Unsheared on purpose: the door frame's feet stand on the plinth, and its
// only downward face is the doorway's own lancet.
module door_frame() {
    // Clip to the threshold FIRST, then take out a doorway that runs 1 mm
    // below it. Cutting the frame's foot off with a square whose top edge sat
    // exactly on the doorway's bottom edge left a zero-width sliver, and CGAL
    // refused the whole trim part: "The given mesh is not closed".
    face_tf(1, door_x, plinth_h) translate([0, 0, -0.4]) linear_extrude(fr_t + 0.4)
        difference() {
            intersection() { offset(r = fr_w) polygon(lancet_pts(door_a, door_h));
                             translate([-20, 0]) square([40, 100]); }
            translate([0, -1]) polygon(lancet_pts(door_a, door_h + 1));
        }
}
st_w = 22;  st_d = 9;
module step() { face_tf(1, door_x, 0) translate([-st_w/2, 0, 0]) cube([st_w, plinth_h, st_d]); }
// The mail slot: a brass plate inlaid FLUSH in the door, 0.8 deep. A real slot
// would be a hole with a flat ceiling.
module mail_slot() {
    face_tf(1, door_x, plinth_h + 8) translate([-3, 0, -1.0]) cube([6, 1.4, 0.8]);
}

// Parcels stacked by the wall, on the plate: no shelf, no support. Each box
// sits inside the footprint of the one below, face to face -- they are one
// part, so they merge. Sunk 0.2 into each other, the top box cut into the
// middle one's string and left four-way edges. Each is tied with string -- a
// flush inlay in the trim colour, 1.0 wide.
//   [width, height, depth out, twist deg]
PARCELS = [[10, 8, 9, 0], [8, 6, 7, 7], [5.5, 4.5, 5, -9]];
pc_u = 19;
pc_str = 1.0;
function pc_z(i) = i == 0 ? 0 : pc_z(i - 1) + PARCELS[i - 1][1];
module parcel_box(i) {
    q = PARCELS[i];
    face_tf(1, pc_u, pc_z(i)) translate([0, 0, PARCELS[0][2] / 2 - 0.4]) rotate([0, q[3], 0])
        translate([-q[0]/2, 0, -q[2]/2]) children();
}
module parcels_solid() {
    for (i = [0 : len(PARCELS) - 1]) let (q = PARCELS[i])
        parcel_box(i) cube([q[0], q[1], q[2]]);
}
module parcels_string() {
    for (i = [0 : len(PARCELS) - 1]) let (q = PARCELS[i])
        parcel_box(i) difference() {
            intersection() {
                // not on the back face, which is buried in the wall: wrapped
                // round it, the string left zero-area faces there
                translate([0, 0, 1.0]) cube([q[0], q[1], q[2] - 1.0]);
                union() {
                    translate([q[0]/2 - pc_str/2, -1, -1]) cube([pc_str, q[1] + 2, q[2] + 2]);
                    translate([-1, -1, q[2]/2 - pc_str/2]) cube([q[0] + 2, q[1] + 2, pc_str]);
                }
            }
            translate([0.8, 0.8, 0.8]) cube([q[0] - 1.6, q[1] - 1.6, q[2] - 1.6]);
        }
}

// ---- sign --------------------------------------------------------------------------
// 17 tall: the board's underside is sheared, so at its face it has lost 2.5
// mm; at 15 the OFFICE line hung 0.85 below it and drew support columns.
// Placed so neither tilted edge crosses a clapboard step line (8 + 4.5k):
// the top runs 67.75..69.85 and the bottom 50.75..52.85. Where an edge
// crossed a step, the step's edge met the board's and left zero-area faces.
sg_u = 5;   sg_z = 60.3;  sg_w = 30;  sg_h = 17;
sg_tilt = 4;                // hung crooked, left end low
module sign_board() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt])
        relief_up(-0.4, fr_t) translate([-sg_w/2, -sg_h/2]) square([sg_w, sg_h]);
}
// The letters are a FLUSH inlay in the board's face, in the accent colour --
// no relief. Raised 1 mm, every horizontal stroke was a sub-bead slab with
// an underside; inlaid, the colour does the work and the face stays flat.
module sign_letters() {
    face_tf(1, sg_u, sg_z) rotate([0, 0, sg_tilt]) translate([0, 0, fr_t - 0.8])
        linear_extrude(0.8) for (l = [["POST", 3.6], ["OFFICE", -3.0]])
            translate([0, l[1]]) text(l[0], size = 4.8, font = "Montserrat:style=Black",
                                      halign = "center", valign = "center", spacing = 1.04);
}

// ---- trim that is not a window ------------------------------------------------------
module corner_boards() {
    translate([0, 0, plinth_h]) linear_extrude(H - plinth_h)
        intersection() {
            // 0.4 into the wall, past the siding's deepest point
            difference() { plan2d(fr_t); plan2d(-0.4); }
            // not the front-right corner: the turret stands on it
            for (sx = [-1, 1], sy = [-1, 1]) if (!(sx > 0 && sy < 0))
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
            // Clear of the gable windows, the chimney on the left and the
            // turret on the right. A gable window's u is WORLD y; in this
            // frame local x is +y on the right gable and -y on the left.
            for (w = WINDOWS) if (w[0] == face)
                translate([(face == 2 ? w[1] : -w[1]) - w[4] - 3.5, w[2] - (H - 0.2) - 3.5 - fr_sill - 2, -5])
                    cube([2 * w[4] + 7, lancet_top(w[4], w[5]) + 9 + fr_sill, 10]);
            if (face == 3) translate([-ch_y - ch_w/2 - 1.5, -5, -5]) cube([ch_w + 3, 100, 10]);
            if (face == 2) translate([-60, -5, -5]) cube([60 - 11, 100, 10]);
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
// The main roof's own material, wherever it runs.
module main_roof() {
    intersection() { slab(); roof_end_clip(); }
    core_roof();
    intersection() { union() { shingles(); ridge_cap(); } roof_end_clip(); }
}
module body_solid() {
    linear_extrude(plinth_h) union() { plan2d(plinth_o); translate([tx, ty]) oct2d(t_ap + plinth_o); }
    siding_wall();
    turret_siding();
    core_roof();
    step();
    battens();
    room_fill();
    // Where the main roof runs into the turret, that roof becomes turret wall.
    // Cut back to the turret's outer face instead, the roof left open slots in
    // every clapboard notch along the join.
    intersection() { t_slab(t_ap + sid_d, plinth_h, Ht); main_roof(); }
}
module trim_raw() {
    for (w = WINDOWS) face_tf(w[0], w[1], w[2]) {
        relief_up(-0.4, fr_t) { win_frame_outer(w); offset(r = 0.3) win_outline(w); }
        // Muntins in two depths. Where they meet the FRAME they run 0.6 past
        // the opening, into it -- a real overlap. They are NOT sheared: a
        // mullion is vertical and every other bar is 50 deg or steeper.
        translate([0, 0, -0.4]) linear_extrude(sid_d + 0.4) win_muntins(w, 0.6);
        // Their back stops 0.2 INSIDE the wall's inner face. Run 0.2 past it
        // into the hollow, every bar's foot hung in the air inside the house
        // and the slicer stood a support column under each one.
        translate([0, 0, -wall + 0.2]) linear_extrude(wall - 0.6 + 0.01) win_muntins_inner(w);
    }
    door_frame();
    door_leaf();
    corner_boards();
    sign_board();
    parcels_string();
}
module accent_raw() {
    difference() { parcels_solid(); parcels_string(); }
    sign_letters();
    mail_slot();
}
module accent_part() { accent_raw(); }
module trim_part()   { difference() { trim_raw(); accent_raw(); } }
module roof_part() {
    difference() {
        intersection() { main_roof(); zone(); }
        chimney(); turret_env();
    }
    chimney();
    difference() { turret_cap(); turret_hollow(); }
}
module body_part() {
    difference() {
        body_solid();
        room(); turret_hollow(); turret_arch();
        difference() { zone(); turret_env(); }
        turret_cap();
        openings(); frame_holes(); chimney(); trim_raw(); accent_raw(); brand_mark();
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
    color("#50666B") body_part();
    color("#2B2F38") roof_part();
    color("#EFE6D2") trim_part();
    color("#D4A96A") accent_part();
}
