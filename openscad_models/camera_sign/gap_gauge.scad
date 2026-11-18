// Gap gauge (2026-11-18): a stepped strip for measuring the two gaps the camera sign
// must clear inside Scott's P1S. Bambu's wiki, manual and store give neither, so Scott
// asked for a gauge rather than a ruler in the chamber:
//   - behind the toolhead, moved all the way back;
//   - behind the bed's back edge, raised to the top.
//
// Slide it in thin end first: the thickest step that goes in without forcing is the gap.
// Each step's thickness is engraved on it. The steps are multiples of the 0.2 mm layer,
// so each prints to its number (within the usual ~0.1 mm).
//
// Printed flat, bottom on the plate, steps up. One colour.
//
//   part = gauge | detail (the numbers' and mark's area, 1 mm round them, the top 0.4 mm:
//          declared to the gate's wall check, whose spans between engraved strokes are
//          lettering, not walls; print_fidelity checks it)
include <../brand/obc_mark.scad>

// From 1.6 mm: under the 1.6 step's engraved number that leaves 1.2, the wall floor. A
// gap under 1.6 can't take a sign anyway: the thinnest that prints in two colours is
// about 1.6, and it wants 1 mm to spare.
STEPS  = [1.6, 2.0, 2.4, 2.8, 3.2, 3.6, 4.0, 4.4, 4.8, 5.2, 5.6, 6.0];   // mm, thin to thick
STEP_L = 10;           // each step's length along the strip
W      = 18;           // the strip's width
HANDLE = 28;           // a 6 mm grip past the last step
ENGRAVE = 0.4;         // the numbers' depth: two layers
FONT   = "Montserrat:style=ExtraBold";
part   = "gauge";

$fn = 48;
N = len(STEPS);

module label(t) linear_extrude(ENGRAVE + 0.01)
    text(str(floor(t), ".", round((t - floor(t)) * 10)), size = 4.6, font = FONT, halign = "center", valign = "center");

module engraving() {
    for (i = [0 : N - 1]) translate([i * STEP_L + STEP_L / 2, W / 2, STEPS[i] - ENGRAVE])
        rotate([0, 0, 90]) label(STEPS[i]);
    translate([N * STEP_L + HANDLE / 2, W / 2, STEPS[N - 1] - 0.6]) rotate([0, 0, 90])
        linear_extrude(0.61) obc_solid2d(4.5);
}

module gauge() difference() {
    union() {
        for (i = [0 : N - 1]) translate([i * STEP_L, 0, 0]) cube([STEP_L + 0.01, W, STEPS[i]]);
        // the handle, rounded at its end, as thick as the last step
        translate([N * STEP_L, 0, 0]) hull() {
            cube([1, W, STEPS[N - 1]]);
            translate([HANDLE - W / 2, W / 2, 0]) cylinder(d = W, h = STEPS[N - 1]);
        }
    }
    // each step's thickness engraved into its top, and the maker's mark on the handle
    engraving();
}

module detail() {
    for (i = [0 : N - 1]) translate([i * STEP_L + STEP_L / 2, W / 2, STEPS[i] - ENGRAVE - 0.05])
        rotate([0, 0, 90]) linear_extrude(ENGRAVE + 0.2) offset(r = 1)
            text(str(floor(STEPS[i]), ".", round((STEPS[i] - floor(STEPS[i])) * 10)), size = 4.6, font = FONT, halign = "center", valign = "center");
    translate([N * STEP_L + HANDLE / 2, W / 2, STEPS[N - 1] - 0.65]) rotate([0, 0, 90])
        linear_extrude(0.8) offset(r = 1) obc_solid2d(4.5);
}

if (part == "detail") detail(); else gauge();
