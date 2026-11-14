// Zero-gap joint test (2026-11-14). Every print-in-place joint we make needs 0.3-0.45 mm of
// air so its two parts don't fuse, and that air is the wobble. Here the gap is filled
// instead with a one-bead sleeve of Bambu Support For PLA, which is made not to bond to
// PLA: if it doesn't bond on its sides either, the rotor turns with no play at all.
// data/knowledge_base/fdm_only_techniques.md section 3.
//
// Three turntables: a PLA rotor in a PLA ring, captured by a V ridge with 50 deg flanks (it prints
// both ways without support).
//   1 dot: the control, 0.30 mm of air, no sleeve (what we do today)
//   2 dots: a 0.45 mm sleeve of support material, no air: zero gap
//   3 dots: the sleeve plus 0.10 mm of air
//   part = "pla" (rings and rotors) | "sleeve" (support material) | "all"

part = "all";
$fn = 120;

H = 4.0;            // height
R = 9.0;            // rotor radius at the bed
RIDGE = 1.2;        // the V ridge's depth, centred at mid height
RING_W = 3.0;       // the ring's wall beyond the ridge
SLEEVE = 0.45;      // one bead
AIR = [0.30, 0, 0.10];
HAS_SLEEVE = [false, true, true];
PITCH = 34;

FLANK = 50;         // the ridge flanks, from horizontal: at 45 the gate's slicer propped them
function ridge(z) = max(0, RIDGE - abs(z - H / 2) / tan(FLANK));
// a ring between radius r0(z) + a and r0(z) + b, as a turned profile
module band(a, b, steps = 48) rotate_extrude() polygon(concat(
    [for (k = [0 : steps]) let(z = H * k / steps) [R + ridge(z) + a, z]],
    [for (k = [steps : -1 : 0]) let(z = H * k / steps) [R + ridge(z) + b, z]]));

// band(-R, ...) alone starts at radius ridge(z), not 0: it left a sealed diamond void at the
// rotor's centre and a needle in the ring's cut (seen in the cut-away render), so the centre
// is filled with a plain cylinder
module rotor(i) difference() {
    union() { band(-R + 1, 0); cylinder(r = R - 0.5, h = H); }
    // a slot to turn it with a coin or a screwdriver, and i + 1 dots
    translate([-4, -0.8, H - 1.2]) cube([8, 1.6, 2]);
    for (k = [0 : i]) rotate(90 + (k - i / 2) * 25) translate([5.5, 0, H - 0.6]) cylinder(d = 1.2, h = 1, $fn = 24);
}
module sleeve(i) if (HAS_SLEEVE[i]) band(AIR[i] > 0 ? AIR[i] / 2 : 0, (AIR[i] > 0 ? AIR[i] / 2 : 0) + SLEEVE);
module ring(i) let(g = AIR[i] + (HAS_SLEEVE[i] ? SLEEVE : 0)) difference() {
    cylinder(r = R + RIDGE + g + RING_W, h = H);
    translate([0, 0, -0.01]) scale([1, 1, 1.006]) union() { band(-R + 1, g, 48); cylinder(r = R - 0.5, h = H); }
    for (k = [0 : i]) rotate(-90 + (k - i / 2) * 12) translate([R + RIDGE + g + RING_W - 0.5, 0, H - 0.6]) cylinder(d = 1.2, h = 1, $fn = 24);
}

module pla() for (i = [0 : 2]) translate([i * PITCH, 0, 0]) { rotor(i); ring(i); }
module sleeves() for (i = [0 : 2]) translate([i * PITCH, 0, 0]) sleeve(i);

if (part == "pla") pla();
else if (part == "sleeve") sleeves();
else if (part == "all") { color("white") pla(); color("orange") sleeves(); }
