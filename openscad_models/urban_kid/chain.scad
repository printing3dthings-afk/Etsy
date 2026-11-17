// Urban Kid: the chain and OBC nameplate (2026-11-17). Printed flat on its back,
// gold. Drawn in the figure's front plane: x across him, y up (his z), so it
// lies on his flat chest with x and y unchanged. kid.py places it.
//
// A nameplate, not a round medallion: OBC at the 3 mm the detail standard sets
// for lettering is 11 mm wide, and on a 10 mm disc it hung off the edge, where
// the slicer propped it (2026-11-17).
use <../brand/obc_mark.scad>

PART = "all";         // "all"; "detail": the letters, link ridges and rim lip, declared to the gate's wall check
T = 1.6;              // the chain's thickness
W = 2.0;              // its width
LINK = 1.4;           // a groove across it every LINK mm: a curb chain
GROOVE = 0.45;        // the grooves' width (DETAIL_STANDARD: >= 0.4)
G_DEEP = 0.35;        // ... and depth: 1.25 left under each, over the 1.2 wall floor
P_W = 13.8;           // the nameplate
P_H = 7.0;
P_R = 2.0;            // its corners
P_T = 2.0;            // its thickness
RIM = 1.2;            // its rim's width (the 1.2 wall floor)
RIM_H = 0.5;          // ... and height
LET_H = 3.0;          // OBC's cap height (DETAIL_STANDARD: >= 3)
LET_UP = 0.6;         // the letters, raised
P_C = [0, 54.0];      // the nameplate's centre
BAIL = [0, 60.6];     // where the chain meets it
ENDS = [[-6.0, 62.3], [6.0, 62.3]];   // under the support cone the collar roll stands on (fit check)

$fn = 64;
module seg2d(a, b, w) hull() { translate(a) circle(d = w); translate(b) circle(d = w); }
module plate2d(inset = 0) offset(r = P_R - inset) square([P_W - 2 * P_R, P_H - 2 * P_R], center = true);
module chain() {
    for (e = ENDS) {
        L = norm(e - BAIL);
        ang = atan2(e[1] - BAIL[1], e[0] - BAIL[0]);
        difference() {
            linear_extrude(T) seg2d(BAIL, e, W);
            // grooves across the top face, kept inside the band's straight part
            for (i = [1 : floor(L / LINK) - 1])
                translate(BAIL + i * LINK * [cos(ang), sin(ang)]) rotate(ang + 90)
                    translate([-GROOVE / 2, -(W / 2 - 0.3), T - G_DEEP]) cube([GROOVE, W - 0.6, 1]);
        }
    }
}
module letters() translate(P_C) translate([0, 0, P_T - 0.01]) linear_extrude(LET_UP + 0.01) obc_solid2d(LET_H);
module nameplate() {
    translate(P_C) {
        linear_extrude(P_T) plate2d();
        linear_extrude(P_T + RIM_H) difference() { plate2d(); plate2d(RIM); }
    }
    letters();
    // the bail: a ring joining it to the chain
    translate([0, (P_C[1] + P_H / 2 + BAIL[1]) / 2]) cylinder(r = 1.6, h = T);
}
module detail() {
    letters();
    for (e = ENDS) translate([0, 0, T - G_DEEP - 0.05]) linear_extrude(G_DEEP + 0.1) seg2d(BAIL, e, W + 0.2);
    translate(P_C) translate([0, 0, P_T - 0.05]) linear_extrude(RIM_H + 0.1) offset(delta = 0.1) plate2d();
}
if (PART == "letters") letters();
else if (PART == "detail") detail();
else { chain(); nameplate(); }
