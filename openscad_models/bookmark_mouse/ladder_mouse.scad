// Ladder Mouse bookmark (2026-11-11). Scott picked form D of five: a mouse
// climbing a rope ladder that hangs down the page, its hands on the top rung
// over the edge of the book.
//
// One flat piece, printed face up. The ladder (1.6 mm, thin enough to close a
// book on) goes inside; the top rung sits on the page edge, and the mouse rises
// above it, 3.0 mm thick with a chamfered edge. Four colours: tan ladder, grey
// mouse, pink ears/nose/cheeks/hands, black eyes. Face colours are flush inlays,
// the top three layers.
//
// Millimetres, y up, the book's top edge at y = 0; the ladder runs down to
// y = -LADDER_LEN, the mouse sits above y = 0.
//
//   part = "tan" | "grey" | "pink" | "black" | "all" | "print" | "outline"

include <BOSL2/std.scad>
use <../brand/obc_mark.scad>

part = "all";
$fn = 72;

// ---------- ladder ----------
RAIL_X     = 10.4;   // rail centres
RAIL_W     = 3.2;
RUNG_H     = 2.6;
RUNG_PITCH = 13;
LADDER_LEN = 140;    // below the book's edge
TOP_RUNG   = [0, 3.2];          // y from, to: sits on the page edge
T_LADDER   = 1.6;               // inside the book
T_TOP      = 3.0;               // the top rung and the rails' tops, outside it: as thick as the mouse
TOP_ZONE   = -1.0;              // above this y the ladder is T_TOP thick
ROPE_W     = 0.5;               // rope twist grooves on the rails: DETAIL_STANDARD rule 5/6
ROPE_D     = 0.4;
ROPE_PITCH = 2.2;

// ---------- mouse ----------
T_MOUSE = 3.0;
T_PAW   = 3.6;                  // the hands stand on the rung, 0.6 (three layers) proud
CHAMFER = 0.6;                  // three 0.2 layers, each stepped 0.2 in
INLAY   = 0.6;                  // face colours: the top three layers
MOUTH_W = 0.5;                  // engraved mouth line
MOUTH_D = 0.4;

HEAD = [[0, 29], [7.5, 28], [12.6, 24], [14.4, 18.5], [13.8, 13.4], [10.6, 9.6],
        [5.2, 7.8], [0, 7.4], [-5.2, 7.8], [-10.6, 9.6], [-13.8, 13.4], [-14.4, 18.5],
        [-12.6, 24], [-7.5, 28]];
EAR_C   = [11.6, 27.6];  EAR_R   = 8.2;
INNER_C = [12.3, 28.3];  INNER_R = 5.2;
BODY_C  = [0, 6.2];      BODY_R  = [10.2, 6.4];
SHOULDER = [6.6, 7.2];
PAW_C   = [5.4, 1.4];    PAW_R   = 3.1;     // gripping the top rung, clear of the rails: where a hand crossed a rail's round top, or met the arm and rung top at one point, the weld pinched (open edges)
EYE_C   = [5.2, 18.6];   EYE_R   = [1.25, 1.55];
GLINT   = [0.55, 0.75];  GLINT_R = 0.5;     // 1.0 mm across: rule 11's 0.8 floor
NOSE_C  = [0, 14.6];     NOSE_R  = [1.5, 1.05];
CHEEK_C = [9.3, 13.6];   CHEEK_R = [1.8, 1.15];
TAIL    = [[8.6, 5.0], [14.6, 3.7], [19.8, 6.8], [21.3, 11.8], [19.4, 15.0],
           [16.9, 13.6]];
TAIL_W  = 2.4;
MARK_H  = 4.0;                  // OBC cap height, under the head
MARK_AT = [0, 18];

module oval(c, r) translate(c) scale(r) circle(1);
module both() { children(); mirror([1, 0]) children(); }

// ---------- 2D ----------
module tail2d() let (p = smooth_path(TAIL, splinesteps = 10))
    for (i = [0 : len(p) - 2]) hull() { translate(p[i]) circle(TAIL_W / 2); translate(p[i + 1]) circle(TAIL_W / 2); }
// The arm tapers into the hand so its edge crosses well inside the hand's circle:
// with a 2.4 end the arm's edge, the hand and the rung's top met at one point and
// left a pinhole (silhouette_check specks).
// fills the corner between his hip, the tail's root and the rung, where a
// 0.24 mm2 pocket was left closed in (silhouette_check gaps and specks)
module tail_root2d() hull() { translate([7.6, 4.4]) circle(1.6); translate([11.2, 3.9]) circle(1.2); }
module arms2d() both() hull() { translate(SHOULDER) circle(2.6); translate(PAW_C) circle(1.6); }
module paws2d() both() translate(PAW_C) circle(PAW_R);
// Layered front to back: hands, arms, the top rung, then head, body and tail.
// The rung crosses in front of his chest and he holds it, so he reads as
// climbing out of the book; with his body over the rung (the first draft) the
// rung vanished and two slivers of it were left loose between hands and body.
module back2d() difference() {
    union() { polygon(smooth_path(HEAD, closed = true, splinesteps = 10)); both() translate(EAR_C) circle(EAR_R); oval(BODY_C, BODY_R); tail2d(); tail_root2d(); }
    top_rung2d();
    translate([-RAIL_X, TOP_RUNG[1] - 20]) square([2 * RAIL_X, 20]);   // nothing of him below the rung's top
}
module mouse2d() union() { back2d(); arms2d(); paws2d(); }
module pink2d() union() {
    both() translate(INNER_C) circle(INNER_R);
    oval(NOSE_C, NOSE_R);
    both() oval(CHEEK_C, CHEEK_R);
}
module eyes2d() both() difference() { oval(EYE_C, EYE_R); translate(EYE_C + GLINT) circle(GLINT_R); }
module mouth2d() let (y = NOSE_C.y - NOSE_R.y - 1.1)
    both() translate([1.0, y]) difference() { circle(1.0 + MOUTH_W / 2); circle(1.0 - MOUTH_W / 2); translate([-2, 0]) square(4); }

function rung_ys() = [for (y = [TOP_RUNG[0] - RUNG_PITCH : -RUNG_PITCH : -LADDER_LEN + RUNG_H]) y];
module rails2d() both() hull() {
    translate([RAIL_X, TOP_RUNG[1] - RAIL_W / 2]) circle(RAIL_W / 2);
    translate([RAIL_X, -LADDER_LEN + RAIL_W / 2]) circle(RAIL_W / 2);
}
module top_rung2d() translate([-RAIL_X, TOP_RUNG[0]]) square([2 * RAIL_X, TOP_RUNG[1] - TOP_RUNG[0]]);
module rungs2d() union() {
    top_rung2d();
    for (y = rung_ys()) translate([-RAIL_X, y - RUNG_H]) square([2 * RAIL_X, RUNG_H]);
    translate([-RAIL_X, -LADDER_LEN + 0.6]) square([2 * RAIL_X, RUNG_H]);   // the bottom rung
}
module ladder2d() union() { rails2d(); rungs2d(); }

// the rope's twist: diagonal grooves across each rail, between the rungs only
// Inside the book only: above TOP_ZONE the rails are 3.0 thick and a groove cut
// from 1.2 up made 1.8 mm slots there, not texture (caught by the wall check).
module rope2d() intersection() {
    both() translate([RAIL_X - RAIL_W / 2, -LADDER_LEN]) square([RAIL_W, LADDER_LEN + TOP_ZONE]);
    difference() {
        for (k = [0 : ceil((LADDER_LEN + 20) / ROPE_PITCH)])
            translate([-20, -LADDER_LEN - 10 + k * ROPE_PITCH]) rotate(35) square([60, ROPE_W]);
        rungs2d();
        mouse2d();
    }
}

// ---------- 3D ----------
module slab(t) linear_extrude(t) children();
module chamfered(t, c) union() {
    slab(t - c) children();
    for (i = [0 : round(c / 0.2) - 1])
        translate([0, 0, t - c + 0.2 * i]) slab(0.2) offset(delta = -0.2 * (i + 1)) children();
}
module ladder3d() difference() {
    union() {
        slab(T_LADDER) ladder2d();
        intersection() { slab(T_TOP) ladder2d(); translate([-50, TOP_ZONE, 0]) cube([100, 50, 10]); }
    }
    translate([0, 0, T_LADDER - ROPE_D]) slab(5) rope2d();
}
module mouse3d() union() {
    chamfered(T_MOUSE, CHAMFER) union() { back2d(); arms2d(); }
    chamfered(T_PAW, CHAMFER) paws2d();
}
module face_cut() translate([0, 0, T_MOUSE - INLAY]) slab(5) children();
module mark_inlay() translate([MARK_AT.x, MARK_AT.y, 0]) obc_inlay(MARK_H);
module mark_cut() translate([MARK_AT.x, MARK_AT.y, 0]) obc_cut(MARK_H);

module tan_part() union() {
    difference() { ladder3d(); translate([0, 0, -1]) slab(12) mouse2d(); }   // the exact outline: a 0.01 margin left a hairline gap and the print came apart in three
    mark_inlay();
}
module grey_part() difference() {
    mouse3d();
    slab(10) paws2d();
    face_cut() pink2d();
    face_cut() eyes2d();
    translate([0, 0, T_MOUSE - MOUTH_D]) slab(5) mouth2d();
    mark_cut();
    mark_inlay();
}
module grey_glints() intersection() { mouse3d(); face_cut() both() translate(EYE_C + GLINT) circle(GLINT_R); }
module pink_part() union() {
    intersection() { mouse3d(); slab(10) paws2d(); }
    intersection() { mouse3d(); face_cut() pink2d(); }
}
module black_part() intersection() { mouse3d(); face_cut() eyes2d(); }

if (part == "tan") tan_part();
else if (part == "grey") union() { grey_part(); grey_glints(); }
else if (part == "pink") pink_part();
else if (part == "black") black_part();
else if (part == "print") union() { tan_part(); grey_part(); grey_glints(); pink_part(); black_part(); }   // the welded print, for the gates
// The rope's texture band, for the product gate's --wall-skip-part: the grooves
// cross each rail at 55 deg, so between them the top 0.4 mm ends in wedge tips
// that taper to nothing at the rail's edge. That is texture (print_fidelity checks
// it); the rail under it is a full 1.2 mm.
else if (part == "rope_band") translate([0, 0, T_LADDER - ROPE_D]) slab(ROPE_D) intersection() {
    both() translate([RAIL_X - RAIL_W / 2, -LADDER_LEN]) square([RAIL_W, LADDER_LEN + TOP_ZONE]);
    difference() { rails2d(); rungs2d(); }
}
else if (part == "outline") union() { ladder2d(); mouse2d(); }
else {
    color("#D2B48C") tan_part();
    color("#9A9AA2") grey_part();
    color("#9A9AA2") grey_glints();
    color("#F2A0B4") pink_part();
    color("#222222") black_part();
}
