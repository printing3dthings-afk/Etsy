// Faceted nativity set (2026-10-21). Scott picked the low-poly form (5A) from
// five: every figure cut from flat faces, like a carved gem or folded paper.
//
// Eleven prints: Mary, Joseph, the baby in the manger, three kings, a
// shepherd, an ox, a donkey, a sheep and the stable. Each figure stands about
// 60 mm; the stable is 170 mm across, open at the front under a pointed arch.
//
// Printed upright, each as it sits in the file, with no support. The faceting
// is what makes that possible:
//   robes narrow as they rise, so their faces lean in;
//   heads are double pyramids whose lower faces climb at 55 deg, where a round
//   head would overhang under the chin;
//   hands, gifts and the baby rest on wedges that climb 55 deg or sink into hay;
//   the animals lie down, so there are no legs to snap;
//   the stable is an open shell whose roof climbs 46 deg.
//   Staffs stand inside the robe up to the hand, so they are not free poles.
// The maker's mark is engraved in each piece's underside.
//
// piece = mary | joseph | baby | king1 | king2 | king3 | shepherd | ox |
//         donkey | sheep | stable
// part  = body | gold (crowns, gifts, the star) | union | all
include <../brand/obc_mark.scad>

piece = "mary";
part = "all";

$fn = 24;

// ---- faceted solids ------------------------------------------------------------------------------
// the hull of a set of points: every face flat
module pts(P) hull() for (p = P) translate(p) cube(0.01, center = true);
function ring(n, r, z, a0 = 0, jit = 0) = [for (i = [0 : n - 1]) let (a = a0 + 360 * i / n, rr = r * (1 + jit * ((i * 37 % 7) / 6 - 0.5)))
    [rr * cos(a), rr * sin(a), z]];

// a robe: a faceted frustum, rb at the foot, rs at the shoulders zs; it narrows, so its faces lean in
module robe(rb, rs, zs, n = 7, a0 = 0) pts(concat(ring(n, rb, 0, a0, 0.12), ring(n - 1, rs, zs, a0 + 13, 0.1)));
// a head: a six-sided double pyramid, its lower edges 51 deg from flat and its
// faces 55. (At 46 and 50 they sat on the slicer's 45 deg line and it propped
// one king's chin from his shoulders.) Its top is a small flat, not a point: a
// point is sliced away (printed heights came up short, 2026-10-21).
module head_at(c, r, a0 = 0) translate([c[0], c[1], 0]) pts(concat(ring(6, 0.6, c[2] + r, a0), ring(6, r, c[2] + 0.15 * r, a0), [[0, 0, c[2] - 1.1 * r]]));
// a hood or headscarf: the head grown 25% and drawn down into the shoulders,
// its foot inside the robe's top (0.6 outside it, it overhung all round and the
// slicer propped Mary's shoulders, 2026-10-21)
module hood(c, r, rs, zs, a0 = 0) translate([c[0], c[1], 0])
    pts(concat(ring(6, 1.2, c[2] + 1.18 * r, a0), ring(7, 1.25 * r, c[2] + 0.15 * r, a0), ring(7, 0.8 * rs, zs - 2, a0 + 10)));
// a block held out in front of the chest at height z, d out from the axis,
// carried on a wedge that climbs 55 deg back into the robe (45 sits on the
// slicer's own threshold)
module held(z, d, w, h, out) pts([[-w / 2, -d + 1, z - 1.43 * (out + 1)], [w / 2, -d + 1, z - 1.43 * (out + 1)],
    [-w / 2, -d - out, z], [w / 2, -d - out, z], [-w / 2, -d - out, z + h], [w / 2, -d - out, z + h],
    [-w / 2, -d + 1, z + h], [w / 2, -d + 1, z + h]]);
// a staff standing at (x, y), r thick, up to z
module staff(x, y, z, r = 2.0) translate([x, y, 0]) cylinder(r = r, h = z, $fn = 6);

// a cape from the shoulders to zh: it stands 1.5 out of the robe at its hem,
// whose underside climbs 55 deg back into the robe, 4 mm up. (As a flat ring
// 2 mm out it put 10,000 support moves under each king; climbing 48 deg, close
// to the slicer's 45, it still put 7,000, 2026-10-21.)
function rob(z, rb, rs, zs) = rb - (rb - rs) * z / zs;
module cape(zs, rb, rs, zh = 0) let (z1 = zh > 0 ? zh : zs * 0.45, r1 = rob(z1, rb, rs, zs))
    pts(concat(ring(7, rs * 0.9, zs + 0.5, 20), ring(7, r1 + 1.5, z1, 5), ring(7, r1 - 1.3, z1 - 4, 5)));

// ---- the figures ---------------------------------------------------------------------------------
// Mary, kneeling, hooded, hands together
module mary() {
    robe(13, 7, 26, 8, 8);
    hood([0, 0, 33], 5.6, 7, 26, 15);
    head_at([0, -0.8, 33], 5.0, 15);
    held(21, 7.2, 4.0, 6.0, 3.6);            // praying hands
}
// Joseph, standing with his staff
module joseph() {
    robe(12, 7.5, 42, 7, 5);
    head_at([0, 0, 49], 5.6, 0);
    // beard and neck, its foot inside the robe's top (1 mm above it, the slicer propped it)
    pts(concat(ring(6, 4.0, 41, 20), ring(6, 3.2, 50.5, 0), [[0, -2.6, 46], [0, -3.2, 41]]));
    staff(9.5, -1.0, 62, 2.0);
    held(34, 7.6, 7.0, 4.4, 2.0);            // the hand on the staff
}
// the baby, swaddled, on hay in the manger
module baby() {
    // the manger: a trough whose sides lean out 15 deg, filled level with hay
    pts([[-17, -7, 0], [17, -7, 0], [-17, 7, 0], [17, 7, 0], [-19.5, -9.5, 10], [19.5, -9.5, 10], [-19.5, 9.5, 10], [19.5, 9.5, 10]]);
    // block feet: square at the toe, then a 55 deg chamfer up into the trough.
    // As wedges they had knife edges at the toe and on top, which the gate
    // read as walls 0.01 to 0.14 thick (2026-10-21).
    for (s = [-1, 1]) pts([[s * 16, -9.6, 0], [s * 20.5, -9.6, 0], [s * 16, 9.6, 0], [s * 20.5, 9.6, 0],
                           [s * 16, -9.6, 1.5], [s * 20.5, -9.6, 1.5], [s * 16, 9.6, 1.5], [s * 20.5, 9.6, 1.5],
                           [s * 16, -9.6, 4.4], [s * 18.5, -9.6, 4.4], [s * 16, 9.6, 4.4], [s * 18.5, 9.6, 4.4]]);
    // the hay, a faceted mound over the rim
    pts(concat(ring(8, 17, 10, 0, 0.0) * 1, [[0, 0, 13]]) * [[1, 0, 0], [0, 0.5, 0], [0, 0, 1]]);
    // the baby: a swaddled bundle, its foot down in the hay (at 11.5 its corners
    // stood over the mound's falling edge and were propped), and its head
    pts([[-11, -4, 10.4], [9, -4, 10.4], [-11, 4, 10.4], [9, 4, 10.4], [-9, -3, 16.5], [7, -3, 16.5], [-9, 3, 16.5], [7, 3, 16.5]]);
    // the head, its chin sunk into the hay: at 10.8 its point came up through
    // the mound's surface as a sliver the slicer dropped (print_fidelity, 2026-10-21)
    translate([11.5, 0, 0]) pts(concat(ring(6, 0.8, 19.4, 0), ring(6, 4.0, 15.0, 0), [[0, 0, 9.8]]));
}
// a king: tall robe, crown, a gift held in front; style 1..3
module king(style) let (zs = [0, 44, 41, 43][style], hz = zs + 4.4, hr = 5.4) {
    robe(12.5, 7.4, zs, [0, 7, 8, 6][style], style * 17);
    head_at([0, 0, hz], hr, style * 10);
    cape(zs, 12.5, 7.4);
}
module king_gold(style) let (zs = [0, 44, 41, 43][style], hz = zs + 4.4, hr = 5.4, zc = hz + 0.15 * hr + 1.4,
        rc = 0.8 * hr * (1 - 1.4 / (0.85 * hr)), np = [0, 6, 5, 6][style], ph = [0, 3.4, 4.6, 2.6][style]) {
    // the crown: a band starting inside the head's top faces, flaring out 55 deg
    // and then straight up 1.2, so its rim is square (flaring to the top it was a
    // 60 deg knife edge; a lip 0.6 tall read as a 0.6 wall). Its points end in
    // flats 1.4 square (points are sliced away; 0.5 x 1.0 they were walls under
    // the gate's floor), their feet's corners inside the band's six flat sides:
    // 0.2 past them, the slicer propped them from the shoulders (2026-10-21).
    translate([0, 0, zc]) {
        rotate([0, 0, style * 10]) { cylinder(r1 = rc, r2 = rc + 1.0, h = 1.4, $fn = 6); translate([0, 0, 1.4]) cylinder(r = rc + 1.0, h = 1.2, $fn = 6); }
        for (i = [0 : np - 1]) rotate([0, 0, 360 * i / np + 30])
            pts([[rc - 1.0, -1.1, 2.5], [rc - 1.0, 1.1, 2.5], [rc + 0.2, -1.1, 2.5], [rc + 0.2, 1.1, 2.5],
                 [rc - 0.4, -0.75, 2.5 + ph], [rc - 0.4, 0.75, 2.5 + ph], [rc + 1.0, -0.75, 2.5 + ph], [rc + 1.0, 0.75, 2.5 + ph]]);
    }
    // the gift: a casket, a jar, a horn
    if (style == 1) held(28, 8.2, 8, 6, 3.2);
    // the jar rests on a cone that climbs 55 deg out of the cape (on a wedge to
    // one point, its front hung at 28 deg and was propped)
    if (style == 2) pts(concat(ring(6, 3.2, 27, 0) + [for (i = [0 : 5]) [0, -11, 0]], ring(6, 3.6, 34, 0) + [for (i = [0 : 5]) [0, -11, 0]],
        ring(6, 1.2, 20, 0) + [for (i = [0 : 5]) [0, -8.5, 0]]));
    if (style == 3) pts([[-2.6, -8.4, 25], [2.6, -8.4, 25], [-2.2, -8.2, 22], [2.2, -8.2, 22], [-1.4, -13.6, 34], [1.4, -13.6, 34], [0, -12.6, 36.5]]);
}
// the shepherd: a short robe, a headscarf, his staff
module shepherd() {
    robe(11.5, 7, 38, 7, 40);
    hood([0, 0, 45], 5.0, 6.6, 38, 22);
    head_at([0, -1.0, 45], 4.8, 22);
    staff(-9.5, -0.5, 58, 2.0);
    held(31, 7.2, 6.0, 4.0, 2.4);
}
// the animals lie down: bodies flat on the plate, heads resting forward
module ox() {
    pts([[-20, -9, 0], [16, -9, 0], [-20, 9, 0], [16, 9, 0], [-17, -7, 13], [12, -7, 15], [-17, 7, 13], [12, 7, 15], [-6, 0, 17]]);
    pts([[14, -6, 0], [14, 6, 0], [27, -4.5, 0], [27, 4.5, 0], [15, -5.5, 14], [15, 5.5, 14], [24, -4, 10], [24, 4, 10]]);   // head, chin down
    // horns: a foot inside the head climbing to a flat tip (out to 6.6 the
    // foot stood past the head's side and was propped)
    for (s = [-1, 1]) pts([[15.6, s * 2.6, 10], [18.0, s * 2.6, 10], [15.6, s * 4.8, 10], [18.0, s * 4.8, 10],
                           [16.3, s * 7.8, 18.5], [17.4, s * 7.8, 18.5], [16.3, s * 9.0, 18.5], [17.4, s * 9.0, 18.5]]);
}
module donkey() {
    pts([[-17, -7.5, 0], [14, -7.5, 0], [-17, 7.5, 0], [14, 7.5, 0], [-14, -6, 12], [10, -6, 13], [-14, 6, 12], [10, 6, 13]]);
    pts([[12, -4.6, 0], [12, 4.6, 0], [26, -3.4, 0], [26, 3.4, 0], [13, -4.2, 17], [13, 4.2, 17], [24, -3, 8.5], [24, 3, 8.5]]);   // head
    // long ears, 2.0 x 2.2 at the tip, their feet inside the head (from 12.4
    // they stood 0.4 behind it, a sliver the slicer propped). At 1.2 x 1.4 and
    // 27 high, tools/fragility.py watched them (slenderness 6.2, 2026-10-21).
    for (s = [-1, 1]) pts([[13.2, s * 1.4, 13], [15.8, s * 1.4, 13], [13.2, s * 3.8, 13], [15.8, s * 3.8, 13],
                           [13.4, s * 3.0, 25], [15.4, s * 3.0, 25], [13.4, s * 5.2, 25], [15.4, s * 5.2, 25]]);
}
module sheep() {
    pts(concat(ring(8, 9, 0, 0, 0.15), ring(7, 8, 7, 10, 0.2), [[0, 0, 11.5]]) * [[1.25, 0, 0], [0, 1, 0], [0, 0, 1]]);
    // the head, its crown flat for 2.5 mm before it slopes to the nose: sloping
    // straight from the back it met the back face in a 60 deg knife edge
    pts([[9, -3.6, 0], [9, 3.6, 0], [18, -2.4, 0], [18, 2.4, 0], [10, -3.2, 10.5], [10, 3.2, 10.5],
         [12.5, -3, 10.5], [12.5, 3, 10.5], [16.5, -2, 6], [16.5, 2, 6]]);
}
// the stable: a shell 3 mm thick, open at the front, its back, sides, roof and
// floor closed. The roof climbs 46 deg to its ridge, so its underside prints
// with no support; the figures stand inside under it. (Solid, with a pointed
// arch cut through, it was 606 cm3, about 750 g, 2026-10-21.)
SW = 150; SD = 70; SE = 55; SR = SE + 78;   // width, depth, eave height, ridge height
ST = 3;                                     // the shell
function gable(w, e, r) = [[-w / 2, 0], [w / 2, 0], [w / 2, e], [0, r], [-w / 2, e]];
module stable() translate([SW / 2, 0, 0]) difference() {
    rotate([90, 0, 0]) translate([0, 0, -SD]) linear_extrude(SD) polygon(gable(SW, SE, SR));
    // the hollow: the profile pulled in ST all round (its roof stays 46 deg), from the front to ST short of the back
    // the inside roof sits ST below the outside one measured square to it,
    // ST * sqrt(1 + k^2) straight down
    let (k = (SR - SE) / (SW / 2), v = ST * sqrt(1 + k * k), xi = SW / 2 - ST)
    translate([0, -1, 0]) rotate([90, 0, 0]) translate([0, 0, -(SD - ST + 1)]) linear_extrude(SD - ST + 1)
        polygon([[-xi, ST], [xi, ST], [xi, SE + k * ST - v], [0, SR - v], [-xi, SE + k * ST - v]]);
    translate([0, SD / 2, 0]) obc_engrave(8, 0.8, 0.15, ridges = false);
}
// the Star of Bethlehem stands on the ridge at the front: four short arms and a
// long tail down to the ridge. Every underside climbs 47 deg or more; a
// five-pointed star's side arms climb only 38 under their points and the
// slicer propped them (2026-10-21).
// Its top arm ends in a flat 1.8 wide: to a point, tools/fragility.py watched
// it (slenderness 4.3, 2026-10-21).
module bethlehem2d() polygon([[0.9, 34], [2.9, 24.6], [8.8, 22], [1.8, 14.4], [0, 0], [-1.8, 14.4], [-8.8, 22], [-2.9, 24.6], [-0.9, 34]]);
// as thick as the roof shell and over it: 4 thick it stood 0.5 out past the
// open front, over nothing, and the slicer propped it from the plate
module star_ridge() translate([SW / 2, ST / 2 + 0.2, SR - 3]) rotate([90, 0, 0]) linear_extrude(ST - 0.4, center = true) bethlehem2d();

// ---- parts -----------------------------------------------------------------------------------------
MARK_H = piece == "sheep" ? 4.4 : 5.0;
module mark() obc_engrave(MARK_H, 0.8, 0.15, ridges = false);
module body_of(p) {
    if (p == "mary") mary();
    if (p == "joseph") joseph();
    if (p == "baby") baby();
    if (p == "king1") king(1);
    if (p == "king2") king(2);
    if (p == "king3") king(3);
    if (p == "shepherd") shepherd();
    if (p == "ox") ox();
    if (p == "donkey") donkey();
    if (p == "sheep") sheep();
    if (p == "stable") stable();
}
module gold_of(p) {
    if (p == "king1") king_gold(1);
    if (p == "king2") king_gold(2);
    if (p == "king3") king_gold(3);
    if (p == "stable") star_ridge();
}
module body_part() difference() { body_of(piece); gold_of(piece); if (piece != "stable") mark(); }
module gold_part() difference() { gold_of(piece); if (piece != "stable") mark(); }
if (part == "body") body_part();
if (part == "gold") gold_part();
if (part == "union") union() { body_part(); gold_part(); }
if (part == "all") { color("#7A5C3F") body_part(); color("#C9A84C") gold_part(); }
