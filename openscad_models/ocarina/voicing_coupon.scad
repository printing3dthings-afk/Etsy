// Ocarina voicing whistle (2026-11-12): the test print before the ocarina (Scott's form
// A, a 12-hole Alto C). The labium edge and windway decide whether an ocarina sounds at
// all, and they are what the printer is most likely to spoil; two constants in the
// tuning (ocarina_budget.py) can only be measured on a real print. So this whistle has
// the instrument's real voicing and two finger holes. Blow it with a tuner: the three
// notes (closed, the small hole open, both open) give the window term and the hole end
// correction, and the full ocarina's hole sizes come from them.
//
// How it prints, and so how the ocarina will: lying on its side, the air flowing along
// the plate (+x), the windway an upright slot 8 mm tall.
//   - The labium edge stands upright and builds bead on bead, its ramp an upright face.
//     Stood on its mouthpiece (the first draft), the edge's first layer was an 8 mm
//     sliver across the window, and the gate's slicer propped it from the plate, up
//     through the windway itself.
//   - The windway's roof is its 1 mm width, not a bridge.
//   - The chamber's roof is a gable 37 deg from upright, so nothing inside needs support.
//   - Finger holes go through upright walls, so they are teardrops pointing up; the
//     ocarina's will be too, so what this measures carries over.
//
// Two whistles, differing only in the windway's height (here its thickness in y): one
// notch = 1.0 mm, two = 1.3 mm.
//   part = "both" | "whistle" (with variant 0/1)
// Millimetres; x the air's way, y toward the front (the window side), z up.

part = "both";
variant = 0;
$fn = 48;

WW   = 8.0;               // windway width (upright here)
WHS  = [1.0, 1.3];        // windway height (across, in y), the variable
WL   = 20;                // windway length = the mouthpiece
WIN_PRINT = 4.0;          // window as printed: windway exit to labium edge
EDGE_LOSS = 0.9;          // the wedge's tip, thinner than a bead, doesn't print: the print
                          // fidelity check measured 0.9 mm of it dropped along the air's line
WIN  = WIN_PRINT - EDGE_LOSS;   // so the model's edge is drawn that much early
LAB  = 22;                // labium wedge angle: the ramp leans this far off the air's line
OFF  = 0.2;               // labium edge this much inside the windway's centre line
T    = 2.4;               // walls (Benson's spec)
ROOF = 37;                // the chamber's roof and the holes' points, deg from upright
CL = 24; CD = 14; CH = 16;  // chamber inside: along the air, deep (y), tall to the eaves (z)
                            // (30 x 16 x 24 took 1 h 10 m for the pair: smaller, the voicing unchanged)
Z0 = T;                     // chamber floor
ZC = Z0 + CH / 2;           // window and windway centre height
WIN_TOP = ZC + WW / 2 + WIN / tan(ROOF);   // the window's top at the labium edge
HOLES = [[5.0, 15, 1], [8.0, 9, -1]];   // [diameter, x past the labium, face +y/-y]: the small one
                                         // on the front past the ramp, the big one on the back

function wh(v) = WHS[v];
// a w x h rectangle centred on the origin with a 37 deg point on top (in 2D, up = +y)
module pointed(wh_) hull() { square(wh_, center = true); translate([0, wh_[1] / 2 + (wh_[0] / 2) / tan(ROOF)]) square(0.01, center = true); }
module teardrop2d(d) hull() { circle(d = d); translate([0, d / 2 / sin(ROOF)]) square(0.01, center = true); }
// the chamber's cross-section (y, z): a box with a gable roof
module prof() polygon([[-CD, Z0], [0, Z0], [0, Z0 + CH], [-CD / 2, Z0 + CH + (CD / 2) / tan(ROOF)], [-CD, Z0 + CH]]);
module along(x0, x1) translate([x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(x1 - x0) children();

module whistle(v) difference() {
    // the body: the chamber's section grown by T, from the mouthpiece to the far end
    along(0, WL + CL + T) offset(delta = T) prof();
    along(WL, WL + CL) prof();
    // windway: an upright slot from the mouthpiece end to the window, its top pointed
    // (37 deg): a flat 1.3 mm roof drew support up the slot itself
    along(-1, WL + 0.01) translate([OFF, ZC]) pointed([wh(v), WW]);
    // Window and labium cut together. Their top is one pointed arch peaking over the
    // labium edge: the window's top rises 37 deg from upright toward the edge and the ramp
    // cut's top falls away from it. Each a flat top, or the two sloping toward each other,
    // left a dip at the edge where the wall above began as one bead over air, and the
    // gate's slicer propped it from the plate, up through the windway. The window is so
    // taller at the edge (WIN_TOP) than the 8 mm jet: that only adds to the window term
    // the whistle measures, and the ocarina copies this voicing exactly.
    union() {
        // window: through the front wall, open to the chamber behind
        translate([0, T + 1, 0]) rotate([90, 0, 0]) linear_extrude(T + 2)
            polygon([[WL, ZC - WW / 2], [WL + WIN, ZC - WW / 2], [WL + WIN, WIN_TOP], [WL, ZC + WW / 2]]);
        // labium: past the window the front wall's inside face is the line y = 0, and its
        // outside is cut back so the wall thickens from nothing at the edge, LAB deg off
        // the air's line
        intersection() {
            translate([WL + WIN, 0, ZC - WW / 2]) linear_extrude(WW + 30)
                // starting 0.3 inside the window: sharing its face left the mesh non-manifold
                polygon([[-0.3, -1], [0, 0], [(T + 1) / tan(LAB), T + 1], [-0.3, T + 1]]);
            translate([WL + WIN, -10, WIN_TOP]) rotate([0, 90 - ROOF, 0]) translate([-50, 0, -100]) cube([150, 20, 100]);
        }
    }
    // finger holes through the front and back walls, across the print
    for (h = HOLES) translate([WL + WIN + h[1], h[2] > 0 ? T / 2 : -CD - T / 2, ZC])
        rotate([90, 0, 0]) linear_extrude(T + 2, center = true) teardrop2d(h[0]);
    // variant notches across the far end, 0.8 deep (at 1.4 they left a 1.0 wall), upright
    // grooves with pointed tops: one = 1.0 mm
    // windway, two = 1.3
    for (k = [0 : v]) translate([WL + CL + T + 1.2, -CD + 3 + k * 2.4, Z0 + 3]) rotate([90, 0, -90])
        linear_extrude(2) hull() { translate([-0.6, 0]) square([1.2, 12]); translate([0, 12 + 0.6 / tan(ROOF)]) square(0.01, center = true); }
}

// the labium wedge, declared to the gate as deliberately thin (the sound edge itself),
// for both whistles as laid out in "both"
module labium_zone() for (v = [0 : 1]) translate([0, v * (CD + 2 * T + 6), 0])
    translate([WL + WIN - 0.5, -0.5, ZC - WW / 2 - 0.5]) cube([(T + 1) / tan(LAB) + 1, T + 1, WIN_TOP - ZC + WW / 2 + 1]);

if (part == "whistle") whistle(variant);
else if (part == "labium_zone") labium_zone();
else for (v = [0 : 1]) translate([0, v * (CD + 2 * T + 6), 0]) whistle(v);
