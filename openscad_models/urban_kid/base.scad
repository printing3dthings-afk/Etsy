// Urban Kid: the base (2026-11-17). A round plinth, printed flat; the OBC mark
// engraved under it, reading from below. The pegs the sneakers sit on are added
// by kid.py, exactly, with the rest of the joints.
use <../brand/obc_mark.scad>

R = 28;          // radius
H = 5;           // height: the sneakers stand on its top
CH = 1.0;        // the top edge's chamfer
FOOT = 0.4;      // the bottom edge's chamfer (elephant's foot)
MARK_H = 7;      // the mark's cap height

$fn = 160;
difference() {
    rotate_extrude() polygon([[0, 0], [R - FOOT, 0], [R, FOOT], [R, H - CH], [R - CH, H], [0, H]]);
    obc_engrave(MARK_H, depth = 0.8, ridges = false);
}
