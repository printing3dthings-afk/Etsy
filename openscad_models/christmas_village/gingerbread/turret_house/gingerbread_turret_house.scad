// Gingerbread Turret House -- the Gingerbread village's first building with
// "more shape" (Scott, 2026-09-30, picked from four shapes against his
// reference photos in ../../references/), and then "not squared" (Scott,
// same day: not the boxy shape, not the sharp edges, not the square base).
//
// So nothing here is a box. The house is a stadium in plan, a straight front
// and back between two round ends, under a round-ended bun of a roof that
// swoops out all the way round into a curl of white icing. A half-round porch
// on two peppermint-stick columns wears a half bell. A round turret on the
// front-left leans a little, under a bell cone and a candy-cane spire that
// bends over at the top. Three roofs, three heights, one swooping profile.
// It all stands on a soft blob of snow with a rounded edge.
//
// A hollow lantern lit by a battery LED tealight: open base, every window
// glazed, its bars standing on the pane.
//
// The machinery is the gingerbread cottage's (../cottage/), itself the
// chapel's, with every trap in .claude/skills/3d-print-design/SKILL.md
// Techniques 79 and 80 applied from the start. What is new is commented here.
//
// COLOUR PARTS, ONE PRINT (gingerbread_turret_house.3mf), priority
// roof > accent > trim > body:
//   body    gingerbread: the house, the turret and the porch walls
//   roof    chocolate: the three roofs and their scallop tiles, the door
//   trim    icing: snow base, the roofs' curled icing eaves and drips, icing
//           on the ridge, collars, window frames, panes and bars, the porch
//           columns, the spire, the peppermints' white
//   accent  candy red: gumdrops, the stripes on the columns and the spire,
//           the peppermints' stripes

include <BOSL2/std.scad>

$fa = 4;  $fs = 0.4;
part = "all";
FN = 128;                   // round walls and roofs

// ---- the main house: a stadium ----------------------------------------------------------
L0       = 18;              // the straight front and back
Dh       = 25;              // half-depth = the round ends' radius (46.6 clear inside)
wall     = 1.68;
plinth_h = 8;
SH       = 1.2;
H        = 42;              // the main ceiling's eave line
tp       = tan(58);
y_in     = Dh - wall;
tr       = 2.52;
tv       = tr / cos(58);
fl_ang   = 52;
EC       = [[-L0 / 2, 0], [L0 / 2, 0]];     // the ends' centres

// SWEEP. Every roof and wall of the house is a profile in (v, z), v the
// distance in from... out from the ridge line, swept round the stadium: along
// the straight front and back, and turned half round each end.
module sweep(L = L0) {
    yz(-L / 2 - 0.01, L / 2 + 0.01) union() { children(); mirror([1, 0, 0]) children(); }
    for (s = [-1, 1]) translate([s * L / 2, 0, 0]) rotate([0, 0, s > 0 ? -90 : 90]) rotate_extrude(angle = 180, $fn = FN) children();
}
module stadium(r) hull() for (c = EC) translate(c) circle(r = r, $fn = FN);

// THE SWOOP. All three roofs are one profile, R = [eave line, inner half-width,
// ceiling slope, slab depth, swoop start, tip, tip angle, chocolate edge].
// The ceiling stays straight; the top eases from the roof's pitch to R[6] and
// kicks out past the wall, so the tip stands well above where a straight roof
// would end. Under the eave the profile rises at 52 deg from the wall to the
// tip, so every layer stands on the one below. Chocolate to R[7]; past it,
// and in a band along the underside, icing.
function R_zc(R, v) = R[0] + (R[1] - abs(v)) * R[2];
function R_zs(R, v) = R_zc(R, v) + R[3];
function R_kc(R) = (R[2] - tan(R[6])) / (2 * (R[5] - R[4]));
function R_top(R, v) = abs(v) <= R[4] ? R_zs(R, v)
    : let (u = abs(v) - R[4]) R_zs(R, R[4]) - (R[2] * u - R_kc(R) * u * u);
function R_tipb(R) = R_top(R, R[5]) - 1.2;
function R_fl(R, v) = R_tipb(R) - (R[5] - abs(v)) * tan(fl_ang);
sb = 1.8;                   // the icing band under the eave, measured up
function R_curve(R, v0, v1, n) = [for (i = [0 : n]) let (v = v0 + (v1 - v0) * i / n) [v, R_top(R, v)]];
// half profiles, v >= 0: the whole roof, what of it is chocolate, the icing eave
module R_full(R, kv0) polygon(concat([[0, R_zc(R, 0)], [kv0, R_zc(R, kv0)], [kv0, R_fl(R, kv0)], [R[5], R_tipb(R)]],
    R_curve(R, R[5], 0, 60)));
module R_choc(R, kv0) polygon([[0, -10], [kv0, -10], [kv0, R_fl(R, kv0) + sb], [R[7], R_fl(R, R[7]) + sb], [R[7], 300], [0, 300]]);
module R_curl(R, kv0) polygon(concat(R_curve(R, kv0, R[5], 24), [[R[5], R_tipb(R)], [kv0, R_fl(R, kv0)]]));
module R_room(R) polygon([[0, -2], [R[1], -2], [R[1], R[0]], [0, R_zc(R, 0)]]);
module R_below(R) polygon([[0, -5], [R[1] + 20, -5], [R[1] + 20, R_zc(R, R[1] + 20)], [0, R_zc(R, 0)]]);
// its top runs 0.6 up into the roof: drawn to the ceiling line it met the slab
// face to face, and the union was non-manifold in a ring round every eave
module R_wall(R, r_out, z0) polygon([[R[1] - 0.3, z0], [r_out, z0], [r_out, R_zc(R, r_out) + 0.6], [R[1] - 0.3, R_zc(R, R[1] - 0.3) + 0.6]]);

RM = [H, y_in, tp, tv, Dh - 6, Dh + 6, 20, Dh + 4];
kv0 = Dh - 0.8;             // the eave's foot, inside the wall
zf0 = R_fl(RM, Dh);         // where the eave's underside meets the wall
function zs(v) = R_zs(RM, v);

// ---- placement and relief (the cottage's) ------------------------------------------------
module shear_up(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module relief_hole(d0, a, b, sh = SH) {
    translate([0, 0, a]) linear_extrude(b - a) children();
    shear_up(sh) translate([0, 0, a]) linear_extrude(b - a) translate([0, -sh * d0]) children();
}
module relief_up(d0, d1, sh = SH) {
    difference() {
        intersection() {
            translate([0, 0, d0]) linear_extrude(d1 - d0)
                minkowski() { children(0); translate([-0.2, -60]) square([0.4, 60]); }
            shear_up(sh) translate([0, 0, d0]) linear_extrude(d1 - d0) children(0);
        }
        if ($children > 1) relief_hole(d0, d0 - 0.1, d1 + 0.1, sh) children(1);
    }
}
module xz(y0, y1) translate([0, y1, 0]) rotate([90, 0, 0]) linear_extrude(y1 - y0) children();
module yz(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();
// on a round face (centre c, radius r) at angle th: local z out, y up
module cplace(c, r, th, z) translate([c[0] + r * cos(th), c[1] + r * sin(th), z]) rotate([0, 0, th + 90]) rotate([90, 0, 0]) children();
// on the flat back wall at x = u
module bplace(u, z) translate([u, Dh, z]) rotate([0, 0, 180]) rotate([90, 0, 0]) children();
// A flat relief laid round a curved face in 1 mm strips, each tangent at its
// own angle: drawn flat, a frame 14 mm wide stands off a round wall at its
// edges, and sunk that deep its sheared opening lifts and cuts its own arch.
module cyl_relief(c, r, th, z, U, du = 1.0) for (i = [0 : ceil(2 * U / du) - 1]) let (u = -U + i * du, uc = u + du / 2)
    cplace(c, r, th + uc / r * 180 / PI, z) translate([-uc, 0, 0]) intersection() {
        children();
        translate([u - 0.15, -50, -10]) cube([du + 0.3, 100, 20]);
    }

// ---- the turret ---------------------------------------------------------------------------
// on the left end, 45 deg round toward the front, 4 mm inside the wall line
tc_ang = 225;
tx = EC[0][0] + (Dh - 4) * cos(tc_ang);
ty = EC[0][1] + (Dh - 4) * sin(tc_ang);
TC   = [tx, ty];
rt   = 10.5;
rti  = rt - wall;
z_tw = 86;                  // its cone's eave line
tpc  = tan(60);
tvc  = tr / cos(60);
RC = [z_tw, rti, tpc, tvc, 6.5, rt + 3.5, 20, rt + 1.7];
kv0c = rti + 0.3;
function zcc(r) = R_zc(RC, r);
// THE LEAN. The turret tips outward, away from the house, 0.05 mm per mm
// (2.9 deg): a shear, so every layer is still a circle, 0.035 mm further out
// than the one below.
lean_k = 0.05;
module lean() multmatrix([[1, 0, lean_k * cos(tc_ang), -lean_k * cos(tc_ang) * plinth_h],
                          [0, 1, lean_k * sin(tc_ang), -lean_k * sin(tc_ang) * plinth_h], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module tplace(th, z) cplace(TC, rt, th, z) children();
module turret_cut() lean() translate([tx, ty, -1]) cylinder(r = rt - 0.3, h = 200, $fn = FN);

// ---- the porch: a half-round, on the front ----------------------------------------------------
PC  = [0, -Dh];             // its centre, on the house's face
rp  = 10;
rpi = rp - wall;
// Hp puts the porch eave's underside above the columns' capitals and the
// arch's apex: lower, the eave hung beside the round shafts
Hp  = 30.5;
RP = [Hp, rpi, tp, tv, rp - 2, rp + 3, 20, rp + 1.4];
kv0p = rp - 0.3;
spring = 18;                // the front arch springs from the columns here
col_r  = 2.1;
col_R  = rp - col_r + 0.1;  // the columns' radius from PC: flush with its face
COL = [for (a = [-140, -40]) [PC[0] + col_R * cos(a), PC[1] + col_R * sin(a)]];
ar_a   = COL[1][0] - col_r; // the arch's half-span
cap_r  = col_r + 1.2;       // the capital, and the clearance round the shaft
// swept round the porch's front half and 8 deg on into the house's wall and
// roof: cut at the wall, the half bell showed its section above the roof
module psweep() translate([PC[0], PC[1], 0]) rotate([0, 0, 172]) rotate_extrude(angle = 196, $fn = FN) children();

// ---- rooms --------------------------------------------------------------------------------
module below_ceil() sweep() R_below(RM);
module main_room() sweep() R_room(RM);
module turret_room() lean() translate([tx, ty, 0]) rotate_extrude($fn = FN) R_room(RC);
// THE PARTITION. Where the turret's wall runs through the main room, the room
// took it away up to the main ceiling, and the ceiling along the ring rises to
// a round, flat-topped hump (55.5 mm): the wall's underside was an arch 8 mm
// across with a level crown, and the slicer propped it from the floor. The
// wall is kept below the ceiling now, down to a pointed doorway whose sides
// fall 0.235 mm per degree of ring (52 deg on the outer face, 58 inside)
// from 54.5 mm on the line to the house's centre to the house wall.
pt_a = 54.5;
pt_k = 0.235;
module turret_partition() let (r0 = rti - 0.5, r1 = rt + 0.2, n = 180, top = 120,
        P = [for (i = [0 : n]) let (th = -45 + i, zb = pt_a - pt_k * abs(th - 45))
                 each [[r0 * cos(th), r0 * sin(th), zb], [r1 * cos(th), r1 * sin(th), zb],
                       [r1 * cos(th), r1 * sin(th), top], [r0 * cos(th), r0 * sin(th), top]]])
    lean() translate([tx, ty, 0]) polyhedron(P, concat(
        [for (i = [0 : n - 1], j = [0 : 3]) [4 * i + (j + 1) % 4, 4 * (i + 1) + (j + 1) % 4, 4 * (i + 1) + j, 4 * i + j]],
        [[3, 2, 1, 0], [4 * n, 4 * n + 1, 4 * n + 2, 4 * n + 3]]));
module room() { difference() { main_room(); turret_partition(); } turret_room(); }
// the porch's inside, open at the front through the arch; it stops short of
// the house wall, where the door's frame stands, and clear of the columns
module porch_room() difference() {
    intersection() {
        translate([PC[0], PC[1], 0]) rotate([0, 0, 180]) rotate_extrude(angle = 180, $fn = FN) R_room(RP);
        translate([-50, -100, plinth_h]) cube([100, 100 - Dh - 1.2, 100]);
    }
    for (c = COL) translate([c[0], c[1], 0]) cylinder(r = cap_r + 0.01, h = spring + 1, $fn = 48);
}

// ---- walls ----------------------------------------------------------------------------------
module main_walls() sweep() R_wall(RM, Dh, plinth_h - 0.5);
module turret_walls() lean() translate([tx, ty, 0]) rotate_extrude($fn = FN) R_wall(RC, rt, plinth_h - 0.5);
module porch_walls() intersection() {
    psweep() R_wall(RP, rp, plinth_h - 0.5);
    translate([-50, -100, 0]) cube([100, 100 - Dh + 0.4, 100]);
}
// the pointed arch through the porch's front, between the columns
module porch_arch() translate([PC[0], 0, 0]) xz(-Dh - rp - 2, -Dh - 1.5)
    polygon([[-ar_a, plinth_h - 1], [ar_a, plinth_h - 1], [ar_a, spring], [0, spring + ar_a * tp], [-ar_a, spring]]);
// below the spring the columns stand free
// ...and the wall between them goes too: cut only by the arch and the rings
// round the shafts, it left a 1 mm2 sliver 10 mm tall beside each column
module col_clear() {
    for (c = COL) translate([c[0], c[1], plinth_h]) cylinder(r = cap_r, h = spring - plinth_h, $fn = 48);
    translate([-COL[1][0], PC[1] - rp - 2, plinth_h]) cube([2 * COL[1][0], rp - 1, spring - plinth_h]);
}

// ---- the roofs ------------------------------------------------------------------------------------
// MAIN: chocolate and icing eave from the one profile, swept round
module roof_main() intersection() { sweep() R_full(RM, kv0); sweep() R_choc(RM, kv0); }
module main_curl() sweep() R_curl(RM, kv0);
// SCALLOP TILES (the cottage's): each course a band of the roof's top, its
// butt cut straight down into a row of rounded tiles, down to the chocolate's
// edge. The rows run round the stadium.
tc = 2.6;  sd = 1.3;  tw = 4.8;
module tile_band(R, x0e, x1) polygon([[x0e, R_top(R, x0e) - 1.0], [x0e, R_top(R, x0e) + 1.0], [x1, R_top(R, x1) + 0.05], [x1, R_top(R, x1) - 1.0]]);
// bumps along the stadium outline at distance x0 from the ridge, staggered by course
module stadium_bumps(x0, k) {
    n = max(1, round(L0 / tw));
    for (s = [-1, 1], j = [0 : n]) translate([-L0 / 2 + (j + (k % 2) / 2) * L0 / n, s * x0]) scale([tw / 2 - 0.25, sd]) circle(r = 1, $fn = 24);
    m = max(2, round(PI * x0 / tw));
    for (c = [0, 1], j = [0 : m]) let (a = (c == 0 ? 90 : -90) + (j + (k % 2) / 2) * 180 / m)
        translate(EC[c]) rotate(a) translate([x0, 0]) scale([sd, PI * x0 / m / 2 - 0.25]) circle(r = 1, $fn = 24);
}
module tiles() {
    vw = RM[7];
    nk = ceil((vw - 0.6) / tc);
    for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.6))
        if (x0e > x1 + 0.3) intersection() {
            sweep() tile_band(RM, x0e, x1);
            translate([0, 0, 20]) linear_extrude(100) intersection() {
                union() { stadium(x0); stadium_bumps(x0, k); }
                stadium(vw);
            }
        }
    sweep() polygon([[0, zs(0) - 1.0], [1.2, zs(1.2) - 1.0], [1.2, zs(1.2) + 1.0], [0, zs(0) + 1.4]]);
}
// ICING on the crown of the roof, its edge cut straight down in waves
function wave(t) = 1.8 * sin(t * 2.3) + 1.2 * sin(t * 5.3 + 40);
function stad_pt(r, t) =            // t in [0, 4): right end, back, left end, front
    t < 1 ? let (a = -90 + 180 * t) [EC[1][0] + r * cos(a), r * sin(a)] :
    t < 2 ? [L0 / 2 - L0 * (t - 1), r] :
    t < 3 ? let (a = 90 + 180 * (t - 2)) [EC[0][0] + r * cos(a), r * sin(a)] :
            [-L0 / 2 + L0 * (t - 3), -r];
module icing_roof() intersection() {
    sweep() polygon([[0, zs(0) - 1.0], [RM[4], zs(RM[4]) - 1.0], [RM[4], zs(RM[4]) + 2.0], [3, zs(3) + 2.0], [0, zs(0) + 2.4]]);
    translate([0, 0, 40]) linear_extrude(100) polygon([for (i = [0 : 199]) let (t = 4 * i / 200) stad_pt(8 + wave(i * 3.3), t)]);
}
GD = [-8, 0, 8];
module gumdrops() difference() {
    for (x = GD) hull() {
        // 1.2 over the ridge: at 2.4, above the roof falling away each side,
        // they stood up as tall pink bullets (the first cottage's trouble)
        translate([x, 0, zs(0) + 1.2]) sphere(r = 2.9, $fn = 32);
        translate([x, 0, zs(0) - 1.6 * 4.2 - 0.5]) cylinder(r = 4.2, h = 0.01, $fn = 32);
    }
    below_ceil();
}
// DRIPS of icing on the walls under the eave, all round (the turret and the
// porch cut their own out)
module drip2d(len, w) hull() { translate([-w/2, 0]) square([w, 1.2]); translate([0, -len + w/2 - 0.2]) circle(r = w/2 - 0.2); }
function rnd(i, s) = rands(0, 1, 1, s + i)[0];
DR_END = [for (i = [0 : 16]) [-84 + i * 10.5 + 3 * rnd(i, 70), 1.4 + 2.0 * rnd(i, 90)]];
module eave_drips() {
    for (c = [0, 1], d = DR_END) cplace(EC[c], Dh, (c == 0 ? 180 : 0) + d[0], zf0 + 1) relief_up(-0.4, 1.2) drip2d(d[1], 2.2);
    for (i = [0 : 4]) bplace(-8 + i * 4, zf0 + 1) relief_up(-0.4, 1.2) drip2d(1.4 + 2.0 * rnd(i, 170), 2.2);
}

// PORCH ROOF: the same swoop, a half bell, its top running into the house
module porch_roof() intersection() { psweep() R_full(RP, kv0p); psweep() R_choc(RP, kv0p); }
module porch_curl() psweep() R_curl(RP, kv0p);
module porch_tiles() {
    vw = RP[7];
    nk = ceil((vw - 1.2) / tc);
    for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.8),
             n = max(4, round(2 * PI * x0 / tw)))
        if (x0e > x1 + 0.3) intersection() {
            psweep() tile_band(RP, x0e, x1);
            translate([PC[0], PC[1], 10]) linear_extrude(60) intersection() {
                union() {
                    circle(r = x0, $fn = FN);
                    for (j = [0 : n - 1]) rotate(360 * (j + (k % 2) / 2) / n) translate([x0, 0])
                        scale([sd, 2 * PI * x0 / n / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                circle(r = vw, $fn = FN);
            }
        }
}
PDR = [196, 206, 334, 344];
module porch_drips() for (a = PDR) cplace(PC, rp, a, R_fl(RP, rp) + 1) relief_up(-0.4, 1.2) drip2d(1.4 + 1.0 * rnd(a, 230), 2.2);

// TURRET CONE: the same swoop, turned: a bell.
module cone_roof() translate([tx, ty, 0]) intersection() {
    rotate_extrude($fn = FN) R_full(RC, kv0c);
    rotate_extrude($fn = FN) R_choc(RC, kv0c);
}
module cone_curl() translate([tx, ty, 0]) rotate_extrude($fn = FN) R_curl(RC, kv0c);
module cone_tiles() translate([tx, ty, 0]) {
    vw = RC[7];
    nk = ceil((vw - 1.2) / tc);
    for (k = [0 : nk - 1])
        let (x0 = vw - k * tc - sd, x0e = min(x0 + sd, vw), x1 = max(vw - (k + 1) * tc - sd - 0.5, 0.8),
             n = max(4, round(2 * PI * x0 / tw)))
        if (x0e > x1 + 0.3) intersection() {
            rotate_extrude($fn = FN) tile_band(RC, x0e, x1);
            translate([0, 0, 60]) linear_extrude(60) intersection() {
                union() {
                    circle(r = x0, $fn = FN);
                    for (j = [0 : n - 1]) rotate(360 * (j + (k % 2) / 2) / n) translate([x0, 0])
                        scale([sd, 2 * PI * x0 / n / 2 - 0.25]) circle(r = 1, $fn = 24);
                }
                circle(r = vw, $fn = FN);
            }
        }
}
module turret_drips() for (i = [0 : 17]) tplace(i * 20 + 7 * rnd(i, 300), R_fl(RC, rt) + 1) relief_up(-0.6, 1.2) drip2d(1.4 + 2.4 * rnd(i, 320), 2.2);
// ICING COLLARS round the turret: a rounded band whose underside rises at 54 deg
TCOL = [35, 74];
module collars() translate([tx, ty, 0]) for (z = TCOL) rotate_extrude($fn = FN)
    polygon([[rt - 0.5, z - 2.4], [rt + 1.2, z - 0.1], [rt + 1.2, z + 0.5], [rt + 0.6, z + 1.3], [rt - 0.5, z + 1.3]]);

// THE SPIRE: a candy-cane rod rising from the cone's tip and bending over, away
// from the house, to 40 deg at its end: the most a rod can lean and print
// with nothing under it. A chain of balls, hulled in pairs.
sp_n = 10;  sp_L = 8;
function sp_ang(i) = 40 * pow(i / sp_n, 2);
function sp_pts(i) = i == 0 ? [0, 0] : let (p = sp_pts(i - 1)) [p[0] + sp_L / sp_n * sin(sp_ang(i)), p[1] + sp_L / sp_n * cos(sp_ang(i))];
function sp_r(i) = 1.8 - 0.6 * i / sp_n;
sp_z0 = R_top(RC, 0) - 2.5;
module sp_at(i) let (p = sp_pts(i)) translate([tx + p[0] * cos(tc_ang), ty + p[0] * sin(tc_ang), sp_z0 + p[1]]) sphere(r = sp_r(i), $fn = 24);
module spire() for (i = [0 : sp_n - 1]) hull() { sp_at(i); sp_at(i + 1); }
// stripes: a rod cut by slabs tilted across it
module stripe_slabs(c, z0, z1, pitch, t, tilt) for (z = [z0 : pitch : z1])
    translate([c[0], c[1], z]) rotate([tilt, 0, 45]) cube([20, 20, t], center = true);

// ---- the porch columns ----------------------------------------------------------------------
// Peppermint sticks: white shafts with red stripes, each flaring at the top
// into a round capital the porch wall stands on.
// THE IMPOST. The round capital carries the porch wall only from 4.5 mm out,
// so each capital also flares, at 49.6 deg or steeper, under the wall out to
// 0.3 mm past the arch's edge: the arch springs from it. Without it the wall
// beside the arch stood on a 1 mm2 sliver of itself, 10 mm tall, and with the
// sliver cleared it hung flat.
module column(c) let (sx = sign(c[0]), x0 = sx * (ar_a - 0.3)) {
    translate([c[0], c[1], plinth_h - 0.5]) cylinder(r = col_r, h = spring - 2.4 - plinth_h + 0.5, $fn = 40);
    hull() {
        translate([c[0], c[1], spring - 2.4]) cylinder(r = col_r, h = 0.01, $fn = 40);
        translate([c[0], c[1], spring - 0.01]) cylinder(r = cap_r, h = 0.61, $fn = 48);
    }
    hull() {
        translate([c[0], c[1], spring - 3.2]) cylinder(r = col_r, h = 0.01, $fn = 40);
        translate([0, 0, spring - 0.01]) linear_extrude(0.61) intersection() {
            translate([PC[0], PC[1]]) difference() { circle(r = rp, $fn = FN); circle(r = rpi - 0.2, $fn = FN); }
            translate([min(x0, c[0]), PC[1] - rp - 1]) square([abs(c[0] - x0), rp]);
        }
    }
}
module column_stripes(c) intersection() {
    translate([c[0], c[1], plinth_h - 0.5]) cylinder(r = col_r, h = spring - 2.4 - plinth_h + 0.5, $fn = 40);
    stripe_slabs(c, plinth_h + 1, spring - 3, 2.4, 1.0, 28);
}

// ---- windows and the door -------------------------------------------------------------------------
bead_r  = 1.2;
bead_sp = 2.0;
function arch_path(a, hgt, o, sp, bottom = true) =
    let (A = a + o, b0 = bottom ? 2 * A : 0, b1 = b0 + hgt + o, b2 = b1 + PI * A, P = b2 + hgt + o,
         n = round(P / sp))
    [for (i = [0 : n - 1]) let (t = i * P / n)
        t < b0 ? [-A + t, -o] :
        t < b1 ? [A, -o + (t - b0)] :
        t < b2 ? let (q = (t - b1) / A * 180 / PI) [A * cos(q), hgt + A * sin(q)] :
                 [-A, hgt - (t - b2)]];
module beads(pts, r = bead_r) for (p = pts) translate(p) circle(r = r);
function arch_pts(a, hgt, n = 24) = concat([[-a, 0], [a, 0]], [for (i = [0 : n]) let (q = 180 * i / n) [a * cos(q), hgt + a * sin(q)]]);
mull = 1.68;
fr_w = 1.8;
fr_t = 0.9;
module win_outline(w) polygon(arch_pts(w[0], w[1]));      // w = [a, straight height]
module win_bars(w) {
    translate([-mull/2, -3]) square([mull, 40]);
    translate([-20, w[1] * 0.6]) square([40, 2.2]);
}
module win_muntins(w, g) { intersection() { offset(r = g) win_outline(w); win_bars(w); } }
module frame2d(w) { offset(r = fr_w) win_outline(w); beads(arch_path(w[0], w[1], fr_w - 0.1, bead_sp)); }
function frame_U(w) = w[0] + fr_w + bead_r + 0.6;
// Every window is on a round face: [centre, radius, angle, z, a, h].
// The back wall is flat; its window sits on a circle too big to curve.
WINS = [
    [EC[1], Dh, -40, 14, 3.6, 8], [EC[1], Dh, 0, 14, 3.6, 8], [EC[1], Dh, 40, 14, 3.6, 8],
    [EC[0], Dh, 170, 14, 3.6, 8], [EC[0], Dh, 125, 14, 3.6, 8],
    [[0, Dh - 5000], 5000, 90, 14, 4.0, 9],
    [TC, rt, -110, 17, 3, 7], [TC, rt, -150, 50, 2.4, 5], [TC, rt, -95, 60, 2.4, 5],
];
function in_turret(W) = W[1] == rt;
module wplace(W) cplace(W[0], W[1], W[2], W[3]) children();
module in_lean(W) if (in_turret(W)) lean() children(); else children();
// trimmed to the true curve at the frame's front: each 1 mm strip's flat front
// stands 0.008 mm proud of its neighbour's where they overlap, and every joint
// left a step the wall check reads as a wall that thin (the flat back is exempt:
// a 5000 mm circle faceted 512 times would cut the frame, not trim it)
module win_frames(turret) for (W = WINS) if (in_turret(W) == turret) let (w = [W[4], W[5]]) intersection() {
    cyl_relief(W[0], W[1], W[2], W[3], frame_U(w)) relief_up(-0.4, fr_t) { frame2d(w); offset(r = 0.3) win_outline(w); }
    if (W[1] < 1000) translate([W[0][0], W[0][1], 0]) cylinder(r = W[1] + fr_t, h = 200, $fn = FN);
    else translate([-500, -500, 0]) cube(1000);
}
// glass flush with the face, bars on it, both clipped to the round face
module win_glass(turret) for (W = WINS) if (in_turret(W) == turret) let (w = [W[4], W[5]]) {
    intersection() {
        wplace(W) translate([0, 0, -wall - 0.6]) linear_extrude(wall + 0.6) offset(r = 0.6) win_outline(w);
        translate([W[0][0], W[0][1], 0]) cylinder(r = W[1], h = 200, $fn = W[1] > 1000 ? 512 : FN);
    }
    intersection() {
        wplace(W) relief_up(-1.0, 0.4) win_muntins(w, 0.6);
        translate([W[0][0], W[0][1], 0]) cylinder(r = W[1] + 0.4, h = 200, $fn = W[1] > 1000 ? 512 : FN);
    }
}
module win_openings(turret) for (W = WINS) if (in_turret(W) == turret)
    wplace(W) translate([0, 0, -wall - 3]) linear_extrude(wall + 6) win_outline([W[4], W[5]]);
module win_frame_holes(turret) for (W = WINS) if (in_turret(W) == turret)
    wplace(W) relief_hole(-0.4, -0.4, fr_t + 2.4) offset(r = 0.4) win_outline([W[4], W[5]]);

// THE DOOR: a chocolate bar (the cottage's), on the house's face inside the porch
door_a = 3.2;
door_h = 9;
module fplace(u, z) translate([u, -Dh, z]) rotate([90, 0, 0]) children();
module door_opening() fplace(0, plinth_h) translate([0, 0, -wall - 2]) linear_extrude(wall + 4) polygon(arch_pts(door_a, door_h));
module door_hole() fplace(0, plinth_h) relief_hole(-0.4, -0.2, fr_t + 2.4) offset(r = 0.4) polygon(arch_pts(door_a, door_h));
module door_leaf() fplace(0, plinth_h) difference() {
    translate([0, 0, -wall + 0.15]) linear_extrude(wall + 0.05)
        translate([0, -0.3]) offset(delta = 0.2) polygon(arch_pts(door_a, door_h + 0.3));
    translate([-0.5, -1, -0.3]) cube([1, door_h + door_a + 4, 1]);
    for (zg = [3.4, 6.8, 10.2]) hull() {
        translate([-door_a - 1, zg - 0.6, 0.2]) cube([2 * door_a + 2, 1.2, 0.2]);
        translate([-door_a - 1, zg - 0.01, -0.3]) cube([2 * door_a + 2, 0.02, 0.7]);
    }
}
module door_frame() fplace(0, plinth_h) relief_up(-0.4, fr_t) {
    intersection() { offset(r = 1.2) polygon(arch_pts(door_a, door_h)); translate([-30, -0.5]) square([60, 100]); }
    translate([0, -1]) offset(delta = -0.3) polygon(arch_pts(door_a, door_h + 1));
}
module pepper_wedges(r) { for (i = [0 : 3]) rotate(i * 90 + 22.5) polygon([[0, 0], [r * 2, 0], [r * 2 * cos(45), r * 2 * sin(45)]]); circle(r = 0.5); }

// ---- the snow base: a soft blob with a rounded edge ------------------------------------------------
module footprint() { stadium(Dh); translate(TC) circle(r = rt, $fn = FN); translate(PC) circle(r = rp, $fn = FN); }
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) footprint();
// the top edge rounded over 1.8 mm, in steps that each sit inside the one below
module base_slab() {
    linear_extrude(plinth_h - 1.8) base2d();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, plinth_h - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d();
}
DRIFTS = [[EC[1][0] + (Dh + 1) * cos(20), (Dh + 1) * sin(20), 7, 4, 3.2], [-4, Dh + 1, 7, 3.5, 2.8],
          [EC[0][0] + (Dh + 1) * cos(150), (Dh + 1) * sin(150), 5, 3.5, 2.4]];
PM = [[EC[1][0] + 28.2 * cos(-60), 28.2 * sin(-60), 2.2], [EC[0][0] + 28.2 * cos(115), 28.2 * sin(115), 2.2]];
module peppermints(stripes = false) for (p = PM) translate([p[0], p[1], plinth_h - 0.2]) linear_extrude(1.4)
    if (stripes) union() { intersection() { circle(r = p[2]); pepper_wedges(p[2]); } circle(r = 0.8); } else circle(r = p[2]);
module base() {
    base_slab();
    intersection() {
        for (d = DRIFTS) translate([d[0], d[1], plinth_h - 0.5]) intersection() {
            scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
            translate([-50, -50, 0]) cube(100);
        }
        linear_extrude(plinth_h + 10) offset(delta = -2.4) base2d();
    }
}
// in the solid band between the room's opening and the porch's lobe: at the
// lobe's foot (-Dh - rp - 3.5) the letters broke out through its curved edge
module brand_mark() translate([0, -Dh - 7.5, -0.5]) linear_extrude(1.3)
    mirror([1, 0, 0]) text("OBC", size = 4.6, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

// ---- parts ----------------------------------------------------------------------------------------------
module body_raw() {
    difference() { main_walls(); turret_cut(); }
    turret_walls();
    difference() { porch_walls(); porch_arch(); col_clear(); }
}
module roof_raw() {
    difference() { union() { roof_main(); tiles(); } room(); turret_cut(); }
    difference() { union() { porch_roof(); porch_tiles(); } room(); }
    difference() { lean() union() { cone_roof(); cone_tiles(); } room(); }
    door_leaf();
}
module accent_raw() {
    gumdrops();
    for (c = COL) column_stripes(c);
    intersection() { lean() spire(); lean() stripe_slabs([tx, ty], sp_z0 + 1, sp_z0 + 12, 2.2, 0.9, 28); }
    peppermints(true);
}
module trim_raw() {
    difference() {
        union() {
            base();
            difference() { union() { main_curl(); eave_drips(); icing_roof(); } turret_cut(); }
            porch_curl();
            porch_drips();
            for (c = COL) column(c);
            lean() { cone_curl(); turret_drips(); spire(); collars(); win_frames(true); }
            win_frames(false);
            door_frame();
            peppermints();
        }
        room();
        porch_room();
        brand_mark();
    }
    // the glass goes back in after the rooms are cut, flush with the face
    difference() { win_glass(false); main_room(); }
    difference() { lean() win_glass(true); turret_room(); }
}
module roof_part()   roof_raw();
module accent_part() { difference() { accent_raw(); roof_raw(); } }
module trim_part()   { difference() { trim_raw(); accent_raw(); roof_raw(); } }
module body_part() {
    difference() {
        body_raw();
        room(); porch_room(); door_opening(); door_hole();
        win_openings(false); win_frame_holes(false); lean() { win_openings(true); win_frame_holes(true); }
        trim_raw(); accent_raw(); roof_raw();
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
    color("#C68642") body_part();
    color("#5A3825") roof_part();
    color("#F7F3EE") trim_part();
    color("#D7263D") accent_part();
}
