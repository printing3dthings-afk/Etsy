// Urban Kid v3: the OBC nameplate, in its own frame: centred on the origin, back face on z = 0,
// front facing +z. build.py places it on the chest over the blank tag Benson's mesh has.
// The sizes are v1's (chain.scad), set for print at this scale: v1's own nameplate.
use <../../brand/obc_mark.scad>

PART = "all";       // "all", or "letters" (the raised detail, declared to the gate's wall check)
P_W = 13.8;
P_H = 7.0;
P_R = 2.0;
P_T = 2.0;          // 0.8 of it sinks into the hoodie (build.py)
BACK = 2.5;         // a block behind the plate, hidden in the hoodie, so the curved chest never leaves a gap
RIM = 1.2;
RIM_H = 0.5;
LET_H = 3.0;        // DETAIL_STANDARD: lettering >= 3 mm
LET_UP = 0.6;
$fn = 64;

module plate2d(inset = 0) offset(r = P_R - inset) square([P_W - 2 * P_R, P_H - 2 * P_R], center = true);
module letters() translate([0, 0, P_T - 0.01]) linear_extrude(LET_UP + 0.01) obc_solid2d(LET_H);

if (PART == "letters") letters();
else union() {
    translate([0, 0, -BACK]) linear_extrude(P_T + BACK) plate2d();
    translate([0, 0, P_T - 0.01]) linear_extrude(RIM_H + 0.01) difference() { plate2d(); plate2d(RIM); }
    letters();
}
