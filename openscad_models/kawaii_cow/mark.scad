// The OBC maker's mark for the Kawaii Cow's base: cow.py exports both and
// inlays the letters in her black, mirrored to read from below.
use <../brand/obc_mark.scad>
H = 6;              // cap height, mm
part = "inlay";
if (part == "inlay") obc_inlay(H); else obc_cut(H);
