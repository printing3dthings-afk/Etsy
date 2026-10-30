// Hungry Love Monster: a classroom Valentine mailbox (2026-10-30). Scott's pick
// 2 of five: "a round, chubby monster whose wide grinning mouth is the card slot
// ('Feed me valentines!'), with stubby arms hugging a heart." Kid- and
// school-friendly: no small or loose parts, no glue, no magnets, rounded where
// hands go, and the mouth takes a standard kids' valentine in its envelope.
//
// Three prints:
//   body   an open-fronted box, printed lying on its back: every wall stands
//          upright, nothing hangs. Grooves down its front take the face.
//   face   the monster's face, printed flat, face up: big eyes, a toothy grin
//          cut right through it for the cards, stubby arms hugging a heart
//          with the child's name. It slides down into the body's grooves.
//   fur    a furry cap with a scalloped fringe, printed upside down on its
//          top. It sits over the top and holds the face in; lift it off to
//          empty the box.
//
// WHY THE FACE IS ITS OWN PRINT. A card-wide mouth cut through an upright wall
// cannot print without support: a straight top is a 110 mm bridge, and a row of
// teeth along the top starts every tooth tip in mid-air. The first version, in
// one piece, needed 7,962 support moves under its eight tooth tips
// (2026-10-30). Printed flat, the mouth is just a hole in a plate, and the
// face's detail and colours land on a top surface, where small detail prints
// best (detail_calibration/FINE_DETAIL_RESEARCH.md).
//
//   part = body | face | face_white | face_red | face_dark | fur   (as printed)
//          body_use | face_use | face_white_use | face_red_use | face_dark_use
//          fur_use (in place) | face_print (merged, for the gate) | assembly
// NAME is the child's name; it scales to fit the heart.

use <../../../brand/obc_mark.scad>
include <../name_text.scad>

NAME = "LIAM";
part = "assembly";
$fa = 2; $fs = 0.3;
FONT = "Fredoka:style=SemiBold";

W = 160; D = 120; HB = 146;      // the body: across, deep, tall
WALL = 2.4; FLOOR = 2.4;
RF = 6;                          // the front corners' radius: at 10 the wall beside the
                                 // face's groove thinned to 0.9
CH = [10, 12];                   // the back corners' chamfer, across x and along y:
                                 // lying on its back it climbs 12 for every 10 out,
                                 // 40 deg off upright
// the front: a lip, the face's groove, a rib behind it
LIPT = 4.4; LO = 2.5;            // the lip's depth and how far it laps the face: after its
                                 // 1.4 land it tapers 2.5 over 3.0, 40 deg
PT = 3.0; C = 0.3;               // the face's thickness; clearance each side
RO = 3.0;                        // how far the rib behind the face stands in
Y0 = -D / 2;                     // the front
YF = Y0 + LIPT + C;              // the face's front, in use
FT = 2.4; FS = 22; FCLR = 0.4; FW = 2.4; FRINGE = 10;   // the fur cap

// ---------------- the plan ----------------
function arc(c, r, a0, a1, n = 12) = [for (i = [0 : n]) let (a = a0 + (a1 - a0) * i / n) c + r * [cos(a), sin(a)]];
PLAN = concat(
    [[-W / 2 + CH.x, D / 2], [W / 2 - CH.x, D / 2], [W / 2, D / 2 - CH.y]],
    arc([W / 2 - RF, Y0 + RF], RF, 0, -90),
    arc([-W / 2 + RF, Y0 + RF], RF, -90, -180),
    [[-W / 2, D / 2 - CH.y]]);
module plan(o = 0) offset(r = o) polygon(PLAN);

// points evenly spaced round the outline, with outward normals (for the fur)
PL = len(PLAN);
SEG = [for (i = [0 : PL - 1]) norm(PLAN[(i + 1) % PL] - PLAN[i])];
CUM = [for (i = 0, s = 0; i < PL; s = s + SEG[i], i = i + 1) s];
PER = CUM[PL - 1] + SEG[PL - 1];
function seg_at(L) = max([for (i = [0 : PL - 1]) if (CUM[i] <= L) i]);
function pt_at(L) = let (i = seg_at(L), t = (L - CUM[i]) / SEG[i]) PLAN[i] + t * (PLAN[(i + 1) % PL] - PLAN[i]);
function nrm_at(L) = let (i = seg_at(L), d = PLAN[(i + 1) % PL] - PLAN[i]) [d.y, -d.x] / norm(d);
function along(n) = [for (k = [0 : n - 1]) (k + 0.5) * PER / n];

// ---------------- the body, in use ----------------
WIN_X = W / 2 - WALL - LO;       // the window the face shows through, between the lips
WIN_Z = FLOOR + LO;
YR = YF + PT + C;                // the rib's face, against the face's back
module body_use() difference() {
    union() {
        difference() {
            linear_extrude(HB) plan();
            // the inside, open at the front and the top. Its front corners are
            // squared back past the rib: rounded, the inner wall curved in by up
            // to 0.4 where the groove crosses it, and the lip began as a flat ledge
            // over the groove that the slicer propped (7,333 moves, 2026-10-30).
            translate([0, 0, FLOOR]) linear_extrude(HB) plan(-WALL);
            translate([-W / 2 + WALL, Y0 - 1, FLOOR]) cube([W - 2 * WALL, YR + LAND + RO / tan(40) + 2 - Y0, HB]);
        }
        intersection() { union() { lips(); ribs(); } linear_extrude(HB) plan(); }
    }
    // the groove the face slides down
    translate([-W / 2 + WALL - 0.01, Y0 + LIPT, FLOOR]) cube([W - 2 * WALL + 0.02, PT + 2 * C, HB]);
    // the window
    translate([-WIN_X, Y0 - 1, WIN_Z]) cube([2 * WIN_X, LIPT + 2, HB]);
    // the maker's mark, engraved into the back, which prints on the bed
    translate([0, D / 2, HB / 2]) rotate([90, 0, 0]) mirror([1, 0, 0]) obc_engrave(10, depth = 0.8, inset = 0.15, ridges = false);
}
// Lip and rib as wedges: each grows out of the wall over its depth on the side
// away from the bed, when the body lies on its back.
// Each keeps its full depth w0 for LAND before it tapers: a wedge that tapers
// straight from its face ends in a knife edge, and the gate measured it at
// 0.92 (1st pct) against a 1.2 floor (2026-10-30).
LAND = 1.4;
module wedge_x(s, y0, y1, w0, w1) hull() {     // on a side wall, s = -1 or 1; w = how far in
    for (y = [y0, y0 + LAND - 0.01]) translate([s > 0 ? W / 2 - WALL - w0 : -W / 2 + WALL - 0.01, y, FLOOR - 0.01]) cube([w0 + 0.01, 0.01, HB - FLOOR + 0.01]);
    translate([s > 0 ? W / 2 - WALL - w1 : -W / 2 + WALL - 0.01, y1 - 0.01, FLOOR - 0.01]) cube([w1 + 0.01, 0.01, HB - FLOOR + 0.01]);
}
module wedge_z(y0, y1, w0, w1) hull() {        // on the floor
    for (y = [y0, y0 + LAND - 0.01]) translate([-W / 2 + WALL - 0.01, y, FLOOR - 0.01]) cube([W - 2 * WALL + 0.02, 0.01, w0 + 0.01]);
    translate([-W / 2 + WALL - 0.01, y1 - 0.01, FLOOR - 0.01]) cube([W - 2 * WALL + 0.02, 0.01, w1 + 0.01]);
}
module lips() {
    for (s = [-1, 1]) wedge_x(s, Y0, Y0 + LIPT, LO, 0);
    wedge_z(Y0, Y0 + LIPT, LO, 0);
}
module ribs() {
    for (s = [-1, 1]) wedge_x(s, YR, YR + LAND + RO / tan(40), RO, 0);
    wedge_z(YR, YR + LAND + RO / tan(40), RO, 0);
}

// ---------------- the face, drawn flat: x across, z up, relief toward +e ----------------
FX = W / 2 - WALL - C;           // the face plate's half width
module face_outline() translate([-FX, FLOOR]) square([2 * FX, HB - FLOOR]);

// the mouth: a smile, its top a row of rounded teeth. Printed flat, a tooth can
// be any shape: the tips are rounded 1.2 for small fingers.
MW = 112; MZ = 50; SMILE = 3; CLEAR = 15; NT = 8; TA = 55;
function lip(x) = MZ + SMILE * pow(x / (MW / 2), 2);
TW = MW / NT;
TH = TW / 2 * tan(TA);
module mouth2d() offset(r = -1.2) offset(delta = 1.2) offset(r = 1.5) offset(delta = -1.5) polygon(concat(
    [for (i = [0 : 24]) let (x = -MW / 2 + MW * i / 24) [x, lip(x)]],
    // right to left: a peak at each tooth boundary, a tip between each pair
    [for (k = [NT : -1 : 0]) each let (x = -MW / 2 + k * TW)
        k == NT ? [[x, lip(x) + CLEAR + TH]] :
        [[x + TW / 2, lip(x + TW / 2) + CLEAR], [x, lip(x) + CLEAR + TH]]]));
// Stopped 1.5 short of the mouth's ends: there the band met the rounded end
// peaks in white slivers 0.2 wide, which print_fidelity flagged as dropped.
// (Opening it with offset() instead threw a spike 90 mm up, 2026-10-30.)
module teeth2d() intersection() {
    translate([-MW / 2 + 1.5, 0]) square([MW - 3, 200]);
    difference() {
    polygon(concat([for (i = [0 : 24]) let (x = -MW / 2 + MW * i / 24) [x, lip(x) + CLEAR - 3]],
                   [for (i = [24 : -1 : 0]) let (x = -MW / 2 + MW * i / 24) [x, lip(x) + CLEAR + TH]]));
    mouth2d();
    }
}
// eyes, below the fur's fringe (it hangs to HB - FS - FRINGE = 114)
EZ = 95; EX = 25; ER = 13;
module eyes2d() for (s = [-1, 1]) translate([s * EX, EZ]) scale([1, 1.12]) circle(ER, $fn = 120);
module pupils2d() for (s = [-1, 1]) translate([s * EX - s * 3, EZ - 2.6]) scale([1, 1.12]) circle(6.4, $fn = 80);
module shine2d() for (s = [-1, 1]) translate([s * EX - s * 3 + 2.2, EZ + 0.8]) circle(2.0, $fn = 40);
// the heart, hugged by two stubby arms, and feet at the foot
HZ = 31; HS = 40;
module heart2d(s) scale(s / 20) translate([0, -2]) union() {
    rotate(45) square(12, center = true);
    for (sx = [-1, 1]) translate([sx * 4.25, 4.25]) circle(6, $fn = 60);
}
module heart_big2d() translate([0, HZ]) heart2d(HS);
module arms2d() for (s = [-1, 1]) hull() {
    translate([s * 58, 40]) circle(9, $fn = 60);
    translate([s * 26, 26]) circle(8, $fn = 60);
}
module feet2d() for (s = [-1, 1]) translate([s * 34, WIN_Z + 1]) intersection() {
    scale([1.6, 1]) circle(11, $fn = 90);
    translate([-30, 0]) square([60, 20]);
}
module name2d() translate([0, HZ + 1]) name_text(NAME, name_fit(NAME, HS * 0.76, 10, 1.08), 1.08);

// Relief raised out of the face, h proud. Printed face up these are plain
// prisms: nothing to slope. Each colour is cut from the ones in front of it, so
// no two parts overlap: the pupils and the name stand 0.8 proud of the eyes and
// the heart, and the hands hug the heart from in front.
module up(h, z0 = 0, e = 0) translate([0, 0, PT + z0 - e]) linear_extrude(h + e) children();
module mouth_through() translate([0, 0, -1]) linear_extrude(PT + 10) mouth2d();
module face_dark() { up(2.4) pupils2d(); up(2.4) name2d(); }
module face_white() difference() {
    union() { up(1.6) eyes2d(); up(1.0) teeth2d(); up(0.6, 2.4) shine2d(); }
    up(2.4) pupils2d();
    mouth_through();
}
module face_red() difference() { up(1.6) heart_big2d(); up(2.4) arms2d(); up(2.4) name2d(); }
module face() difference() {
    union() { linear_extrude(PT) face_outline(); up(2.4) arms2d(); up(2.0) feet2d(); }
    mouth_through();
}
// the face in use: its back against the rib, its front at YF, facing -y
module to_use() translate([0, YF + PT, 0]) rotate([90, 0, 0]) children();

// ---------------- the fur cap, in use ----------------
NSC = 34; NGR = 140;
module fur_use() difference() {
    union() {
        translate([0, 0, HB]) hull() {
            linear_extrude(FT - 1.0) plan(FCLR + FW);
            translate([0, 0, FT - 1.0]) linear_extrude(1.0) plan(FCLR + FW - 0.7);
        }
        translate([0, 0, HB - FS]) linear_extrude(FS + 0.01) difference() { plan(FCLR + FW); plan(FCLR); }
        // the fringe: scallops hanging below the skirt all round
        intersection() {
            translate([0, 0, HB - FS - FRINGE]) linear_extrude(FRINGE + 0.02) difference() { plan(FCLR + FW); plan(FCLR); }
            union() for (L = along(NSC)) let (p = pt_at(L), n = nrm_at(L))
                translate([p.x, p.y, HB - FS]) rotate([0, 0, atan2(n.y, n.x) + 90]) rotate([90, 0, 0])
                    linear_extrude(40, center = true) scale([1, FRINGE / 6.5]) circle(6.5, $fn = 48);
        }
    }
    // fur: grooves up the skirt, 0.6 deep, 0.8 wide, evenly round the outline
    for (L = along(NGR)) let (n = nrm_at(L), p = pt_at(L) + (FCLR + FW) * n)
        translate([p.x, p.y, HB - FS - FRINGE - 1]) rotate([0, 0, atan2(n.y, n.x)])
            translate([-0.6, -0.4, 0]) cube([1.2, 0.8, FS + FRINGE - 3]);
}

// ---------------- as printed ----------------
module body_print() translate([0, 0, D / 2]) rotate([-90, 0, 0]) body_use();   // on its back
module fur_print() translate([0, 0, HB + FT]) mirror([0, 0, 1]) fur_use();      // on its top
// The merged face for the gate, from overlapping pieces: colour parts that only
// touch fuse with open edges (the one-piece body's merge did, 2026-10-30).
module face_print() difference() {
    union() {
        linear_extrude(PT) face_outline();
        up(2.4, 0, 0.01) { arms2d(); pupils2d(); name2d(); }
        up(2.0, 0, 0.01) feet2d();
        up(1.6, 0, 0.01) { eyes2d(); heart_big2d(); }
        up(1.0, 0, 0.01) teeth2d();
        up(0.6, 2.4, 0.01) shine2d();
    }
    mouth_through();
}

if      (part == "body")           body_print();
else if (part == "face")           face();
else if (part == "face_white")     face_white();
else if (part == "face_red")       face_red();
else if (part == "face_dark")      face_dark();
else if (part == "face_print")     face_print();
else if (part == "fur")            fur_print();
else if (part == "body_use")       body_use();
else if (part == "face_use")       to_use() face();
else if (part == "face_white_use") to_use() face_white();
else if (part == "face_red_use")   to_use() face_red();
else if (part == "face_dark_use")  to_use() face_dark();
else if (part == "fur_use")        fur_use();
else {
    color("#B79CE0") body_use();
    to_use() {
        color("#B79CE0") face();
        color("#F4F1EA") face_white();
        color("#D7263D") face_red();
        color("#2B2433") face_dark();
    }
    color("#F58CB4") fur_use();
}
