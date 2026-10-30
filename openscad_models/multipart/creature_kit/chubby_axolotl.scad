// Chubby Axolotl: the first Creature Kit (2026-10-30). Scott picked form 2 of
// five: "a short, fat body in five segments with a big frilly-gilled head and
// four stubby jointed legs. It sits on a desk and looks back at you."
//
// Every joint is the test plate's ball joint: an 8 mm ball snapped into a cup
// split by slits, its mouth 0.6 mm narrower than the ball (the plate's middle
// value, until Scott's results say otherwise: change BI and rebuild).
//
// Each part prints in one colour, flat face down, no supports:
//   head, s1-s4, tail  stand on their REAR face. The socket opens on that face
//                      and its hollow is roofed by a 40 deg cone; the ball stands
//                      on top, on the part's front face.
//   leg_*              stand on the sole, the ball on top.
//   gills              a flat frill, pegged onto the back of the head.
//   eye                two, pressed into the face.
// The legs' sockets are in the belly of s1 and s3, sideways in the print, so
// every overhang in them is a teardrop pointing up the print (the creature's
// forward), 40 deg off upright.
//
// Print frame of the spine parts: +z is the creature's forward, +y its up, +x
// its left. part="echo" prints where every part sits in the creature.

include <../../brand/obc_mark.scad>

part = "s1";
$fn = 64;

// ---- the joint ----------------------------------------------------------------------------
BR   = 4;                   // the ball
BI   = 0.6;                 // how much narrower the mouth is: the test plate's middle value
BRC  = BR + 0.1;            // the hollow, a hair over the ball
RM   = BR - BI / 2;         // the mouth's radius
HM   = sqrt(BRC * BRC - RM * RM);   // mouth to centre, along the axis
ZM   = 0.7;                 // the lead-in, from the part's face to the mouth (35 deg)
ZC   = ZM + HM;             // the socket's centre, in from the face
RCUP = BRC + 2;             // the cup: a 2 mm wall, as on the plate
RREL = RCUP + 1.2;          // the gap round the cup, so its fingers flex
SLW  = 0.8;                 // the slits
TA   = 40;                  // every cone and roof: 40 deg off upright
TH   = 35;                  // a sideways hole's teardrop: steeper. At 40 the slicer propped the leg
                            // sockets' roofs, 4,272 support moves (2026-10-30), as it did the
                            // calendar's 45 deg holes until they went to 52 from level
GAP  = 2.0;                 // between two parts along the spine
HGAP = 4.0;                 // between the head and the chest: a longer neck, so the head turns
BALLZ = GAP + ZC;           // a ball's centre, in front of its part's front face
NECK = BR / sin(TA) - 2.2 / tan(TA);    // the cone under a ball meets its 2.2 stem this far down

// ---- the body -----------------------------------------------------------------------------
N    = 2.2;                 // squareness of every cross-section: round, a little full
K    = 96;
// [name, half-width, half-height, length]: rear to front of each, chest to hip
SEGS = [["s1", 19, 14.5, 22], ["s2", 19, 14.5, 20], ["s3", 17.5, 13.5, 21], ["s4", 13.5, 10.5, 17]];
S0   = 0.9;                 // a part's rear face, as a share of its full section
FL   = 4.5;                 // the flare from the rear face to the full section: 23 deg
SF   = 0.55;                // the front face, after the dome
LEGZ = 10;                  // the legs' sockets, up the print from the rear face. At 8.5 the cup
                            // hung over the rear flare, and the slicer propped it (249 moves)
LEGA = [0.25, -1];          // their axis, out of the belly (x, y): 14 deg off straight down
LEGO = 0.33;                // and where it starts, as a share of the half-width

HEAD = [25, 17, 32];        // half-width, half-height, length
HS0  = 0.88;
HSF  = 0.55;
EYE  = [8.3, 2.6];          // the eyes on the face
EYR  = 3.3;                 // an eye's stud; its dome is 0.5 wider and sits in a countersink
// the tail, tip to front: a tall, thin fin on smooth curves. Its height climbs
// at most 38 deg off upright from the tip (it prints standing on it), then eases
// down into the stub that carries the ball.
function tail_h(z) = z <= 24 ? 7 + 12 * sin(90 * z / 24) : 6.4 + 12.6 * cos(90 * (z - 24) / 20);
function tail_w(z) = z <= 20 ? 3.6 + 0.4 * z / 20 : z <= 38 ? 4 + 4 * sin(90 * (z - 20) / 18) : 5 + 3 * cos(90 * (z - 38) / 6);
TAIL = [for (z = [0 : 1 : 44]) [z, tail_w(z), tail_h(z)]];

LEG_BALL = 12;              // a leg's ball centre above its sole: short legs, the belly low
LEG_LEAN = 25;              // its column leans in toward the body
PEG  = [[15, 8.5], [-15, 8.5]];   // the gills' pegs into the back of the head: 2.6 from its edge

// ---- sections and lofts ---------------------------------------------------------------------
function sel(w, h, n = N, k = K) = [for (i = [0 : k - 1]) let (t = 360 * i / k, c = cos(t), s = sin(t))
    [w * sign(c) * pow(abs(c), 2 / n), h * sign(s) * pow(abs(s), 2 / n)]];
function ring(w, h, z, n = N, dx = 0, dy = 0) = [for (p = sel(w, h, n)) [p[0] + dx, p[1] + dy, z]];

// one solid through rings of K points each, bottom to top
module loft(rings) let (n = len(rings), k = len(rings[0])) polyhedron(
    [for (r = rings) each r],
    concat([[for (i = [0 : k - 1]) i]],
           [for (j = [0 : n - 2]) for (i = [0 : k - 1])
                [j * k + i, (j + 1) * k + i, (j + 1) * k + (i + 1) % k, j * k + (i + 1) % k]],
           [[for (i = [k - 1 : -1 : 0]) (n - 1) * k + i]]));

// a part's scale up its length: the rear flare, a straight run, a dome to the front face
function prof(l, s0, sf, hold) = concat([[0, s0], [FL, 1], [hold, 1]],
    [for (j = [1 : 10]) let (t = j / 10) [hold + (l - hold) * t, sf + (1 - sf) * sqrt(1 - t * t)]]);
module body(w, h, l, s0, sf, hold, n = N) loft([for (p = prof(l, s0, sf, hold)) ring(w * p[1], h * p[1], p[0], n)]);

// distance along a ray from o in direction d (2D, unit) to the section's edge
function hit(w, h, o, d, lo = 0, hi = 60, it = 30) = it == 0 ? lo : let (m = (lo + hi) / 2,
    p = o + m * d, v = pow(abs(p[0] / w), N) + pow(abs(p[1] / h), N))
    v < 1 ? hit(w, h, o, d, m, hi, it - 1) : hit(w, h, o, d, lo, m, it - 1);

// ---- the joint's halves ---------------------------------------------------------------------
// the ball, centre at the origin, on a stem from `base` below it
module ball(base) {
    hull() { sphere(r = BR); translate([0, 0, -NECK]) cylinder(r = 2.2, h = 0.01); }
    translate([0, 0, -base]) cylinder(r = 2.2, h = base - NECK + 0.01);
}
module tdrop(r) hull() { circle(r = r); translate([r / sin(TH), 0]) circle(r = 0.01); }   // its point toward +x

// a socket opening on a face at z = 0, the part above it (+z): the cutter
module socket_v() {
    translate([0, 0, -0.01]) cylinder(r1 = RM + 0.5, r2 = RM, h = ZM + 0.01);
    hull() { translate([0, 0, ZC]) sphere(r = BRC); translate([0, 0, ZC + BRC / sin(TA)]) sphere(r = 0.01); }
    rotate_extrude($fn = 96) polygon([[RCUP, -1], [RREL, -1], [RREL, ZC + 1], [RCUP, ZC + 1 + (RREL - RCUP) / tan(TA)]]);
    // four slits through the cup's wall, each topped with a 60 deg gable
    for (a = [45 : 90 : 315]) rotate(a) hull() {
        translate([0, -SLW / 2, -1]) cube([RCUP + 0.3, SLW, ZC + 2]);
        translate([0, -0.005, -1]) cube([RCUP + 0.3, 0.01, ZC + 2 + SLW / 2 / tan(30)]);
    }
}
// the same, lying on its side: the face at z = 0, the part toward +z, and +x
// up the print. The mouth, the hollow and the gap round the cup are teardrops
// pointing up; the cup's outside one pointing down.
module socket_h() {
    hull() {
        translate([0, 0, -0.01]) cylinder(r1 = RM + 0.5, r2 = RM, h = ZM + 0.01);
        translate([(RM + 0.5) / sin(TH), 0, -0.01]) cylinder(r = 0.01, h = ZM + 0.01);
    }
    // the hollow's roof runs out through the face as one peaked ridge. Peaked
    // over the centre only, its cone met the face in an edge the slicer
    // propped: 868 support moves in a test block, none this way (2026-10-30)
    hull() {
        translate([0, 0, ZC]) sphere(r = BRC);
        for (z = [ZC, -1]) translate([BRC / sin(TH), 0, z]) sphere(r = 0.01);
    }
    difference() {
        translate([0, 0, -12]) linear_extrude(12 + ZC + 1) tdrop(RREL);
        // the cup: peaked above as well, so its wall stays 2 mm round the hollow's
        // peak (round above, it feathered to 0.3 mm where they met)
        // Below, it points at 25 deg: at the slits' 30 its sides ran almost along
        // them and left a sliver of wall between
        translate([0, 0, -0.01]) linear_extrude(ZC + 1.03) { tdrop(RCUP); rotate(180) hull() { circle(r = RCUP); translate([RCUP / sin(25), 0]) circle(r = 0.01); } }
    }
    // two slits below, 30 deg either side of straight down; the open roof is the
    // third. Slits above cut slivers off the cup's shoulders that the slicer
    // propped: 1,023 support moves in a test block (2026-10-30)
    for (s = [-1, 1]) rotate(180 + s * 30) translate([0, -SLW / 2, -1]) cube([RCUP + 0.3, SLW, ZC + 2]);
}

// a leg socket on a segment: where it is and the frame that turns socket_h onto it
function leg_axis(side) = let (v = [side * LEGA[0], LEGA[1]]) v / norm(v);
function leg_face(w, h, side) = let (o = [side * LEGO * w, 0], d = leg_axis(side), r = hit(w, h, o, d))
    o + (r - 2.0) * d;      // the cup's face, 2.0 inside the surface: nearer, the gap round the cup
                            // left slivers of wall under the belly (gate, 2026-10-30)
function leg_centre(w, h, side) = let (f = leg_face(w, h, side), d = leg_axis(side)) [f[0] - ZC * d[0], f[1] - ZC * d[1], LEGZ];
module at_leg(w, h, side) let (f = leg_face(w, h, side), d = leg_axis(side),
        zl = [-d[0], -d[1], 0], xl = [0, 0, 1], yl = cross(zl, xl))
    multmatrix([[xl[0], yl[0], zl[0], f[0]], [xl[1], yl[1], zl[1], f[1]], [xl[2], yl[2], zl[2], LEGZ], [0, 0, 0, 1]])
        children();

// ---- the parts ------------------------------------------------------------------------------
function seg(name) = SEGS[search([name], SEGS)[0]];

module segment(name) let (s = seg(name), w = s[1], h = s[2], l = s[3], hold = 0.45 * l) difference() {
    union() {
        body(w, h, l, S0, SF, hold);
        let (b = (name == "s1" ? HGAP : GAP) + ZC) translate([0, 0, l + b]) ball(b + 0.5);
    }
    socket_v();
    if (name == "s1" || name == "s3") for (side = [-1, 1]) at_leg(w, h, side) socket_h();
}

module head() let (w = HEAD[0], h = HEAD[1], l = HEAD[2]) difference() {
    union() {
        body(w, h, l, HS0, HSF, 9, 2.3);
        // blush, raised on the face
        for (x = [-1, 1]) translate([x * 9.4, -3.4, l - 0.01]) scale([1, 0.6]) cylinder(r = 1.9, h = 0.61);
    }
    socket_v();
    // the gills' peg holes, roofed by a cone
    for (p = PEG) translate([p[0], p[1], -0.01]) { cylinder(r = 1.6, h = 4); translate([0, 0, 4 - 0.01]) cylinder(r1 = 1.6, r2 = 0, h = 1.6 / tan(TA)); }
    // the eyes' holes, with three crush ribs each, and a countersink the
    // eye's dome sits in, so no gap shows round it
    for (x = [-1, 1]) translate([x * EYE[0], EYE[1], l - 2.6]) {
        difference() {
            cylinder(r = EYR + 0.2, h = 3);
            for (a = [90, 210, 330]) rotate(a) translate([EYR - 0.1, -0.4, -0.1]) cube([1, 0.8, 3.2]);
        }
        translate([0, 0, 2.0]) cylinder(r1 = EYR + 0.2, r2 = EYR + 0.7, h = 0.6);
        translate([0, 0, 2.59]) cylinder(r = EYR + 0.7, h = 1);
    }
    // the smile: a small "w", 0.8 wide and 0.6 deep
    translate([0, -3.4, l - 0.6]) linear_extrude(1) for (x = [-1, 1]) translate([x * 2.0, 0])
        difference() { circle(r = 2.4, $fn = 48); circle(r = 1.6, $fn = 48); translate([-3, 0]) square(6); }
    // the maker's mark, under the gills' frill on the back of the head
    translate([0, -11.2, 0]) obc_engrave(5, 0.8, 0.15, ridges = false);
}

module tail() {
    loft([for (t = TAIL) ring(t[1], t[2], t[0], 2.2)]);
    translate([0, 0, TAIL[len(TAIL) - 1][0] + BALLZ]) ball(BALLZ + 0.5);
}

// the gills: three stalks a side, frond-edged, rising off a crescent that sits
// behind the head's rim. Top face (veins, pegs) toward the head.
GILLS = [[24, 14], [47, 17], [72, 15]];          // [angle off level at the root, length]
function rim(a) = let (w = HEAD[0] * HS0, h = HEAD[1] * HS0, c = cos(a), s = sin(a),
    r = pow(pow(abs(c / w), 2.5) + pow(abs(s / h), 2.5), -1 / 2.5)) [r * c, r * s];
module stalk2d(g, vein = false) let (o = rim(g[0]) * 0.97, a = g[0] + 15, d = [cos(a), sin(a)], p = [-d[1], d[0]], l = g[1])
    if (vein) hull() { translate(o + 2 * d) circle(r = 0.75, $fn = 16); translate(o + (l - 2) * d) circle(r = 0.75, $fn = 16); }
    else union() {
        hull() { translate(o) circle(r = 2.6, $fn = 32); translate(o + l * d) circle(r = 1.9, $fn = 32); }
        for (t = [4 : 2.6 : l - 1.5], sd = [-1, 1]) let (hw = 2.6 - 0.7 * t / l)
            translate(o + t * d + sd * (hw + 0.2) * p) circle(r = 1.25, $fn = 24);
    }
module gills2d(vein = false) for (m = [0, 1]) mirror([m, 0]) for (g = GILLS) stalk2d(g, vein);
module crescent2d() let (w = HEAD[0] * HS0, h = HEAD[1] * HS0) intersection() {
    difference() { offset(r = 3) polygon(sel(w, h, 2.5)); offset(delta = -6) polygon(sel(w, h, 2.5)); }
    // clear of the chest's face in the middle, so the head can nod
    difference() { translate([-50, 7]) square([100, 50]); translate([-12.5, -10]) square([25, 22]); }
}
module gills() {
    linear_extrude(2.4) union() { crescent2d(); gills2d(); }
    translate([0, 0, 2.39]) linear_extrude(0.61) gills2d(true);
    for (p = PEG) translate([p[0], p[1], 2.39]) { cylinder(r = 1.5, h = 3.2); translate([0, 0, 3.19]) cylinder(r1 = 1.5, r2 = 1.0, h = 0.5); }
}

// an eye: a stud into the hole, a 40 deg flange into the countersink, a dome
module eye() {
    cylinder(r = EYR, h = 2.01);
    translate([0, 0, 2]) cylinder(r1 = EYR, r2 = EYR + 0.5, h = 0.6);
    translate([0, 0, 2.59]) scale([1, 1, 0.45]) intersection() { sphere(r = EYR + 0.5); translate([-5, -5, 0]) cube(10); }
}

// a leg, standing on its sole; +x forward, +y away from the body (left legs; the right ones are mirrored)
function leg_col(hb) = hb - 4.6 - 1.4;        // the column's height, from the foot to its shoulder
function leg_off(hb) = tan(LEG_LEAN) * leg_col(hb);   // how far the ball sits in from the foot
module leg(toes, hb) {
    ang = toes == 4 ? [-40, -13, 13, 40] : [-52, -26, 0, 26, 52];
    module foot2d() union() {
        circle(r = 5.4, $fn = 48);
        for (a = ang) let (d = [cos(a + 8), sin(a + 8)]) hull() { translate(3.0 * d) circle(r = 1.9, $fn = 24); translate(7.6 * d) circle(r = 2.1, $fn = 24); }
    }
    linear_extrude(1.4) foot2d();
    translate([0, 0, 1.39]) linear_extrude(0.61) offset(delta = -0.5) foot2d();
    lean = tan(LEG_LEAN); hc = leg_col(hb); top = 1.4 + hc;
    loft([for (i = [0 : 12]) let (z = 1.4 + hc * i / 12, r = 5.0 - 1.1 * i / 12) ring(r, r, z, 2, 0, -lean * (z - 1.4))]);
    // the shoulder, narrowing at 40 deg from the column to the ball's stem
    translate([0, -lean * hc, 0]) hull() {
        translate([0, 0, top - 0.01]) cylinder(r = 3.9, h = 0.01);
        translate([0, 0, top + (3.9 - 2.2) / tan(TA)]) cylinder(r = 2.2, h = 0.01);
    }
    translate([0, -lean * hc, hb]) ball(hb - top + 0.5);
}

// ---- where everything sits in the creature (part="echo") ---------------------------------
// creature x = print z (forward), y = print x (left), z = print y (up), plus each part's offset
function seg_x0(i) = i < 0 ? 0 : seg_x0(i - 1) - (i == 0 ? HGAP : GAP) - SEGS[i][3];   // rear face of SEGS[i]
// the spine's height above the desk: the front feet flat on it, legs upright
SPINE = LEG_BALL - leg_centre(seg("s1")[1], seg("s1")[2], 1)[1];
REAR_BALL = SPINE + leg_centre(seg("s3")[1], seg("s3")[2], 1)[1];   // so the rear feet stand flat too
if (part == "echo") {
    echo(str("PLACE head ", [0, 0, SPINE]));
    echo(str("PLACE gills ", [-2.4, 0, SPINE]));
    for (x = [-1, 1]) echo(str("PLACE eye_", x < 0 ? "r" : "l", " ", [HEAD[2] - 2.6, EYE[0] * x, SPINE + EYE[1]]));
    for (i = [0 : len(SEGS) - 1]) echo(str("PLACE ", SEGS[i][0], " ", [seg_x0(i), 0, SPINE]));
    echo(str("PLACE tail ", [seg_x0(len(SEGS) - 1) - GAP - TAIL[len(TAIL) - 1][0], 0, SPINE]));
    for (s = [["s1", "front"], ["s3", "rear"]], side = [-1, 1]) let (i = search([s[0]], SEGS)[0], g = SEGS[i],
            c = leg_centre(g[1], g[2], side))
        echo(str("SOCKET ", s[1], side < 0 ? "_r" : "_l", " ", [seg_x0(i) + c[2], c[0], SPINE + c[1]],
                 " ", [0, side * LEGA[0], LEGA[1]] / norm(LEGA)));
    echo(str("LEGBALL front ", [0, -leg_off(LEG_BALL), LEG_BALL], " rear ", [0, -leg_off(REAR_BALL), REAR_BALL]));
    echo(str("BALLZ ", BALLZ, " ZC ", ZC, " RM ", RM, " BRC ", BRC));
}
else if (part == "head")   head();
else if (part == "gills")  gills();
else if (part == "eye")    eye();
else if (part == "tail")   tail();
else if (part == "leg_front_l") leg(4, LEG_BALL);
else if (part == "leg_front_r") mirror([0, 1, 0]) leg(4, LEG_BALL);
else if (part == "leg_rear_l")  leg(5, REAR_BALL);
else if (part == "leg_rear_r")  mirror([0, 1, 0]) leg(5, REAR_BALL);
else segment(part);

