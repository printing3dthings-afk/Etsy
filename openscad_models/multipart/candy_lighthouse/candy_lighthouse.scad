// Candy Lighthouse (2026-10-29): a lighthouse helter-skelter that dispenses
// M&Ms or Skittles. Candy fills the clear lantern room; each click of the red
// roof drops one candy through the gallery floor into a chute inside the tower,
// out onto a slide that winds once round the tower to the tray at its foot.
// Scott's pick, form 5 of the candy dispenser forms.
//
// Prints, each in the pose it prints in, no supports:
//   tower    base tray, striped tower, slide, gallery: one print, upright
//   wheel    the dispensing disc and its shaft, disc down
//   lantern  the clear hopper, UPSIDE DOWN (roof end on the bed), so the
//            baffle inside it is corbelled from the wall
//   roof     the knob, upright
//   head     optional: the gallery top alone, a puck to sit on a mug and try
//            the dispenser with real candy before printing the tall tower
//
//   part = tower | tower_red | tower_blue | wheel | lantern | roof | head
//          tower_print (all the tower's colours) | assembly | section
//
// The candy is an envelope, not a measurement: nothing published gave the size
// of an M&M or a Skittle (2026-10-29), so CANDY_D x CANDY_T is a guess that
// holds either, and every pocket, hole and channel is sized from it.

SH = 1.2;
include <../../christmas_village/relief_lib.scad>
use <../../brand/obc_mark.scad>

part = "assembly";
SHOW_SLIDE = true;
$fa = 2; $fs = 0.4;

CANDY_D = 14.0;              // across
CANDY_T = 8.0;               // thick

// ---------- the slide ----------
TR       = 18;               // tower radius
SL_W     = CANDY_D + 2;      // clear tread, tower wall to rail
RAIL_T   = 1.6;
RAIL_H   = CANDY_T + 1;      // a lentil hitting the rail at speed stays in
TREAD_T  = 2.4;
RAIL_IN  = TR + SL_W;        // 34
RAIL_OUT = RAIL_IN + RAIL_T;
R_C      = TR + SL_W / 2;    // the line the slope is set on
// Flat candy slides rather than rolls, so the slide is steep: 38 deg at its
// centre line, 31 at the rail, where a candy actually runs (the turn throws it
// outward). Whether candy slides on a given PLA at 31 deg is a physical test;
// the notes say how to check before printing the tower.
SLOPE    = 38;
PITCH    = 2 * PI * R_C * tan(SLOPE);   // drop per turn, 127.6
A0       = 195;              // where the slide starts, degrees
TRAY_Z   = 4;                // tray floor
Z_END    = TRAY_Z + 2;       // tread at the slide's foot
function z_at(a) = Z_END + PITCH * (A0 + 360 - a) / 360;

// ---------- the dispenser ----------
R_P      = 15;               // pocket circle
POCKET_R = (CANDY_D + 1) / 2;
DISC_R   = 25.8;
DISC_T   = CANDY_T + 1;      // one candy lying flat; two stacked do not fit
GAP      = 1.6;              // disc top to baffle: the click lifts it 1.0
NUB_R    = 1.2;
NUB_AT   = 3.6;              // detent nubs, inside the pocket ring
SHAFT_D  = 11;
SHAFT_FLAT = 4.0;            // D flat, from the axis

// ---------- the chute: outlet under the 180 deg pocket, down inside the tower ----------
// It never breaks the tower's surface except at one arched door in the
// upright wall, 32 deg along from the slide's head, sill just above the tread.
// The first version ran out through the gallery's corbel; any opening cut
// through an overhanging face leaves corners the slicer has to prop, and it
// propped them with a column from the tray: 18,965 support moves, and no
// reshaping of that opening got it to zero (2026-10-29). Inside:
//   outlet  upright, under the pocket, through the gallery floor
//   jog     falls inward at 50 deg to the shaft, so it stays 1.2 inside the
//           corbel all the way down (the corbel is 40 deg from upright)
//   shaft   upright, 1.27 inside the tower wall
//   ramp    the shaft's floor, falling 50 deg out through the door
GAL_R    = 33;
GAL_T    = 4;
CH_R     = 8;
DOOR_A   = A0 + 32;              // the door's middle, degrees
CH_TOP   = [R_P * cos(180), R_P * sin(180)];
CH_SHAFT = (TR - 1.27 - CH_R) * [cos(DOOR_A), sin(DOOR_A)];
DOOR_W   = CANDY_D + 2.4;
DOOR_SIDE = CANDY_T + 3;       // a flat 8 lying on the 50 deg ramp stands 12.4 at the sill
DOOR_Z   = z_at(A0) + 0.4;       // sill: over the tread at the door's upslope edge
DOOR_TOP = DOOR_Z + DOOR_SIDE + DOOR_W / 2 * 1.2;
ZC       = DOOR_TOP + 2.2;       // the corbel's foot
JOG      = norm(CH_TOP - CH_SHAFT) * tan(50);
JOG_TOP  = ZC + 12.8;            // the outlet's foot: low enough and the jog cuts the corbel
ZG       = ZC + GAL_T + (GAL_R - TR) / tan(40);   // gallery floor's top

// ---------- gallery, lantern, roof ----------
PAR_IN   = 31.4;
PAR_H    = 8;
LAN_IN   = 26.4;
LAN_OUT  = 28.4;
LAN_H    = 50;
GROOVE_D = 1.2;
ROOF_R   = 30.5;
ROOF_SEAT = 2.5;             // the lantern's rim goes this far into the roof

LAN_Z    = ZG - GROOVE_D;                 // lantern bottom, assembled
ROOF_Z   = LAN_Z + LAN_H - ROOF_SEAT;     // roof bottom, assembled
SHAFT_TOP = ROOF_Z + 10 - 1.5;            // 1.5 under the socket's end: the click
                                          // lifts the wheel 1.0
BAFFLE_A = 55;               // half-width of the baffle, degrees, round 180
BAFFLE_Z = ZG + DISC_T + GAP - LAN_Z;     // baffle's underside, lantern frame

echo(str("pitch ", PITCH, "  slide top ", z_at(A0), "  gallery ", ZG,
         "  lantern top ", LAN_Z + LAN_H, "  roof bottom ", ROOF_Z,
         "  shaft ", SHAFT_TOP - ZG - DISC_T, " long"));

// ---------- helper: sweep a section along the helix ----------
function sec_ring(sec, a, dz) = [for (p = sec) [p[0] * cos(a), p[0] * sin(a), p[1] + dz]];
module helix_sweep(sec, a0, a1, steps) let (n = len(sec), m = steps + 1,
        pts = [for (i = [0 : steps]) let (a = a0 + (a1 - a0) * i / steps) each sec_ring(sec, a, z_at(a))])
    polyhedron(pts, concat(
        [[for (j = [0 : n - 1]) j]],
        [[for (j = [n - 1 : -1 : 0]) (m - 1) * n + j]],
        [for (i = [0 : m - 2], j = [0 : n - 1]) each
            let (a = i * n + j, b = i * n + (j + 1) % n, c = (i + 1) * n + (j + 1) % n, d = (i + 1) * n + j)
            [[a, d, c], [a, c, b]]]));

// tread on top, rail at the edge, and underneath a corbel down to the tower
// wall at 40 deg from upright (the helix's own slope makes it steeper still)
SLIDE_SEC = [[TR - 0.5, 0], [RAIL_IN, 0], [RAIL_IN, RAIL_H], [RAIL_OUT, RAIL_H],
             [RAIL_OUT, -TREAD_T], [TR - 0.5, -TREAD_T - (RAIL_OUT - TR + 0.5) / tan(40)]];
module slide() intersection() {
    helix_sweep(SLIDE_SEC, A0, A0 + 360, 180);
    translate([0, 0, TRAY_Z - 0.01]) cylinder(h = 400, r = 60);
}

module chute() intersection() {
    union() {
        hull() {
            translate(concat(CH_TOP, [JOG_TOP])) cylinder(h = ZG + 1 - JOG_TOP, r = CH_R, $fn = 96);
            translate(concat(CH_SHAFT, [JOG_TOP - JOG])) cylinder(h = ZG - JOG_TOP, r = CH_R, $fn = 96);
        }
        translate(concat(CH_SHAFT, [DOOR_Z - 1])) cylinder(h = JOG_TOP - JOG - DOOR_Z + 2, r = CH_R, $fn = 96);
        // the door: a pointed arch, straight through the wall
        rotate([0, 0, DOOR_A]) translate([norm(CH_SHAFT) - 1, 0, DOOR_Z - 1]) rotate([90, 0, 90])
            linear_extrude(TR + 2 - norm(CH_SHAFT)) arch2d(DOOR_W, DOOR_SIDE + 1, DOOR_W / 2 * 1.2);
    }
    // the floor: a ramp falling 50 deg out to the sill
    rotate([0, 0, DOOR_A]) translate([TR, 0, DOOR_Z]) rotate([0, -50, 0]) translate([-100, -50, 0]) cube([200, 100, 200]);
}

// ---------- tower ----------
BASE_R   = 50;
RIM_W    = 3.5;
RIM_H    = 12;
BANDS    = [[30, 42], [78, 90], [126, 138]];   // red, from z to z

module arch2d(w, h, apex) polygon([[-w / 2, 0], [w / 2, 0], [w / 2, h], [0, h + apex], [-w / 2, h]]);
// recessed 1.0 into the tower at angle a, sill at z; the arch's top climbs
// 1.2 per 1 out from the middle, so the recess's head prints
module window(a, z, w = 6, h = 8) rotate([0, 0, a]) translate([TR - 1.0, 0, z]) rotate([90, 0, 90])
    linear_extrude(3) arch2d(w, h, w / 2 * 1.2);
WINDOWS = [[270, 40], [270, 124], [90, 66], [90, 110], [0, 30], [180, 92]];

module tower_gross() difference() {
    union() {
        // tray: floor and rim
        cylinder(h = TRAY_Z, r = BASE_R, $fn = 200);
        difference() { cylinder(h = RIM_H, r = BASE_R, $fn = 200); translate([0, 0, -1]) cylinder(h = RIM_H + 2, r = BASE_R - RIM_W, $fn = 200); }
        cylinder(h = ZG - GAL_T, r = TR, $fn = 120);
        if (SHOW_SLIDE) slide();
        // gallery: a corbel out at 40 deg from upright, the floor, the parapet
        translate([0, 0, ZG - GAL_T - (GAL_R - TR) / tan(40)])
            cylinder(h = (GAL_R - TR) / tan(40) + 0.01, r1 = TR, r2 = GAL_R, $fn = 160);
        translate([0, 0, ZG - GAL_T]) cylinder(h = GAL_T, r = GAL_R, $fn = 160);
        gallery_top(ZG);
    }
    gallery_cuts(ZG);
    chute();
    for (w = WINDOWS) window(w[0], w[1]);
    window(270, TRAY_Z, 9, 15);        // the door
    translate([0, 0, 0]) obc_engrave(8, depth = 0.8, inset = 0.15, ridges = false);
}

// the gallery's top: parapet with baluster slots, the lantern's seat, the
// detent nubs. Shared with the head-test puck.
module gallery_top(z) {
    difference() {
        translate([0, 0, z - 0.01]) cylinder(h = PAR_H + 0.01, r = GAL_R, $fn = 160);
        translate([0, 0, z - 1]) cylinder(h = PAR_H + 2, r = PAR_IN, $fn = 160);
        // slots: upright, 1.4 wide, with pointed tops. Flat, each top was a
        // 1.4 bridge the slicer propped, and its support spread out past the
        // gallery's edge and ran down to the tray: 115,851 support moves round
        // the whole tower (2026-10-29). The point is 1.4 tall, not 0.9: at
        // 0.9 it printed clean on the head puck and was propped on the tower,
        // whose gallery sits at a different place in the 0.2 mm layers.
        for (i = [0 : 23]) rotate([0, 0, i * 15 + 7.5]) translate([PAR_IN - 1, 0, z + 1.5]) rotate([90, 0, 90])
            linear_extrude(GAL_R - PAR_IN + 2) arch2d(1.4, PAR_H - 4.5, 1.4);
    }
    for (k = [0 : 3]) rotate([0, 0, 45 + 90 * k]) translate([NUB_AT, 0, z - 0.2]) sphere(NUB_R, $fn = 24);
}
module gallery_cuts(z) {
    // the lantern's seat: a groove, with a notch at 0 deg for its key
    translate([0, 0, z - GROOVE_D]) difference() {
        cylinder(h = GROOVE_D + 1, r = LAN_OUT + 0.2, $fn = 160);
        translate([0, 0, -1]) cylinder(h = GROOVE_D + 3, r = LAN_IN - 0.2, $fn = 160);
    }
    translate([LAN_OUT - 1, -1.7, z - GROOVE_D - 0.2]) cube([2.6, 3.4, GROOVE_D + 1.2]);
    // the outlet under the 180 deg pocket
    translate(concat(CH_TOP, [z - GAL_T - 1])) cylinder(h = GAL_T + 2, r = CH_R);
}

// colours: the bands and the parapet red, the tray blue, the rest white
module red_zone() {
    for (b = BANDS) translate([0, 0, b[0]]) cylinder(h = b[1] - b[0], r = TR + 0.01, $fn = 120);
    translate([0, 0, ZG + 0.001]) difference() { cylinder(h = PAR_H + 1, r = GAL_R + 1); cylinder(h = PAR_H + 1, r = PAR_IN - 0.5); }
}
module blue_zone() {
    translate([0, 0, -1]) cylinder(h = TRAY_Z + 1, r = BASE_R + 1, $fn = 200);
    translate([0, 0, -1]) difference() { cylinder(h = RIM_H + 2, r = BASE_R + 1, $fn = 200); cylinder(h = RIM_H + 2, r = BASE_R - RIM_W - 0.01, $fn = 200); }
}
module tower()      difference() { tower_gross(); red_zone(); blue_zone(); }
module tower_red()  intersection() { tower_gross(); red_zone(); }
module tower_blue() intersection() { tower_gross(); blue_zone(); }

// ---------- wheel: the dispensing disc and its shaft ----------
module d_shape(d, flat) intersection() { circle(d = d, $fn = 48); translate([-d, -d]) square([d + flat, 2 * d]); }
module wheel() difference() {
    union() {
        cylinder(h = DISC_T, r = DISC_R, $fn = 120);
        // the shaft, with a 0.6 chamfer on its top
        intersection() {
            linear_extrude(SHAFT_TOP - ZG) d_shape(SHAFT_D, SHAFT_FLAT);
            union() {
                cylinder(h = SHAFT_TOP - ZG - 0.6, r = SHAFT_D);
                translate([0, 0, SHAFT_TOP - ZG - 0.6 - 0.01]) cylinder(h = 0.61, r1 = SHAFT_D / 2 + 0.05, r2 = SHAFT_D / 2 - 0.6);
            }
        }
    }
    for (k = [0 : 3]) rotate([0, 0, 90 * k]) translate([R_P, 0, -1]) {
        cylinder(h = DISC_T + 2, r = POCKET_R);
        // the pocket's mouth opens 0.8 so a candy finds it
        translate([0, 0, DISC_T + 1 - 0.8]) cylinder(h = 0.81, r1 = POCKET_R, r2 = POCKET_R + 0.8);
    }
    // the detent: cones, not spheres, so their tops print over the bed
    for (k = [0 : 3]) rotate([0, 0, 45 + 90 * k]) translate([NUB_AT, 0, -0.01])
        cylinder(h = (NUB_R + 0.2) * 1.2, r1 = NUB_R + 0.2, r2 = 0, $fn = 24);
}

// ---------- lantern: the clear hopper, with its baffle ----------
// The baffle covers the pocket over the outlet, so a pocket that has reached
// the outlet drops what it carried and no more: the pile above it is shut off.
// It covers +-55 deg round 180, which at r 15 keeps a pocket covered from
// before any opening wide enough for a candy forms. Its underside is GAP over
// the wheel; its top climbs to the wall at 50 deg from level (a funnel for the
// candy above it). Both its leading edges are bevelled 45 deg underneath, so a
// candy standing on edge in a pocket is tipped down into it, either way round.
module baffle() intersection() {
    difference() {
        rotate_extrude($fn = 160) polygon([[6, BAFFLE_Z], [LAN_IN + 0.5, BAFFLE_Z],
            [LAN_IN + 0.5, BAFFLE_Z + 3 + (LAN_IN + 0.5 - 6) * tan(50)], [6, BAFFLE_Z + 3]]);
        for (s = [-1, 1]) rotate([0, 0, 180 + s * BAFFLE_A]) scale([1, s > 0 ? 1 : -1, 1])
            rotate([90, 0, 90]) linear_extrude(40) polygon([[0.1, BAFFLE_Z - 0.1], [-4, BAFFLE_Z - 0.1], [0.1, BAFFLE_Z + 4]]);
    }
    rotate([0, 0, 180 - BAFFLE_A]) rotate_extrude(angle = 2 * BAFFLE_A, $fn = 160) square([40, 100]);
}
module lantern() {
    difference() { cylinder(h = LAN_H, r = LAN_OUT, $fn = 160); translate([0, 0, -1]) cylinder(h = LAN_H + 2, r = LAN_IN, $fn = 160); }
    // the key, into the gallery's notch
    // Key and glazing bars stand 1.0 proud, and the lantern prints upside
    // down, so their upper ends are sloped: printed, those are undersides.
    translate([0, 1.4, 0]) rotate([90, 0, 0]) linear_extrude(2.8)
        polygon([[LAN_OUT - 0.5, 0], [LAN_OUT + 1, 0], [LAN_OUT, GROOVE_D], [LAN_OUT - 0.5, GROOVE_D]]);
    for (i = [0 : 7]) rotate([0, 0, i * 45 + 22.5]) translate([0, 1, 0]) rotate([90, 0, 0]) linear_extrude(2)
        let (z0 = GROOVE_D + 2, z1 = LAN_H - ROOF_SEAT - 1.5)
            polygon([[LAN_OUT - 0.4, z0], [LAN_OUT + 1, z0], [LAN_OUT + 1, z1 - 2.0], [LAN_OUT - 0.4, z1]]);
    baffle();
}

// ---------- roof: the knob ----------
ROOF_BASE = 4.5;
module roof() difference() {
    union() {
        cylinder(h = ROOF_BASE, r = ROOF_R, $fn = 160);
        translate([0, 0, ROOF_BASE - 0.01]) cylinder(h = 14, r1 = ROOF_R, r2 = 5, $fn = 160);
        translate([0, 0, ROOF_BASE + 15.5]) sphere(4.5, $fn = 48);                       // the vent ball
        translate([0, 0, ROOF_BASE + 19]) cylinder(h = 6, r1 = 1.4, r2 = 0.5, $fn = 24);   // finial
    }
    // grip: notches round the eave, open at the top so none has a ceiling
    for (i = [0 : 29]) rotate([0, 0, i * 12]) translate([ROOF_R - 0.6, -0.8, -1]) cube([2, 1.6, ROOF_BASE + 2]);
    // The roof prints upright, so the lantern's seat and the shaft's socket
    // are both cut from below: each is peaked at 50 deg over its full depth.
    // Flat, the seat's ring was a 2.5 wide bridge the slicer propped.
    let (w = LAN_OUT - LAN_IN + 0.5, rm = (LAN_OUT + LAN_IN) / 2)
        rotate_extrude($fn = 160) polygon([[rm - w / 2, -1], [rm + w / 2, -1], [rm + w / 2, ROOF_SEAT], [rm, ROOF_SEAT + w / 2 * 1.2], [rm - w / 2, ROOF_SEAT]]);
    translate([0, 0, -1]) linear_extrude(11) offset(delta = 0.2) d_shape(SHAFT_D, SHAFT_FLAT);
    translate([0, 0, 10 - 0.01]) linear_extrude(SHAFT_D / 2 * 1.2, scale = 0) offset(delta = 0.2) d_shape(SHAFT_D, SHAFT_FLAT);
}

// ---------- head test: the gallery top as a puck, on a mug ----------
module head() let (z = 6) difference() {
    union() { cylinder(h = z, r = GAL_R, $fn = 160); gallery_top(z); }
    gallery_cuts(z);
    translate(concat(CH_TOP, [-1])) cylinder(h = z + 2, r = CH_R);
}

module assembly(cut = false) {
    module body() {
        color("#F4F1EA") tower();
        color("#C8312B") tower_red();
        color("#3A6EA5") tower_blue();
        color("#F4F1EA") translate([0, 0, ZG]) wheel();
        color("#CFE8F0", 0.45) translate([0, 0, LAN_Z]) lantern();
        color("#C8312B") translate([0, 0, ROOF_Z]) roof();
    }
    if (cut) difference() { body(); translate([0, 0, -1]) cube([200, 200, 400]); } else body();
}

if      (part == "tower")       tower();
else if (part == "tower_red")   tower_red();
else if (part == "tower_blue")  tower_blue();
else if (part == "tower_print") tower_gross();
else if (part == "wheel")       wheel();
else if (part == "lantern")     translate([0, 0, LAN_H]) mirror([0, 0, 1]) lantern();   // as printed, upside down
else if (part == "lantern_up")  lantern();
else if (part == "roof")        roof();
else if (part == "head")        head();
else if (part == "section")     assembly(true);
else if (part == "dims")        echo(DIMS = [ZG, LAN_Z, ROOF_Z, JOG_TOP, JOG, DOOR_Z, DOOR_A, CH_TOP, CH_SHAFT, SHAFT_TOP]);
else                            assembly();
