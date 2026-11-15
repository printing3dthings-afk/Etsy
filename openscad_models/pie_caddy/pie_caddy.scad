// Pie Drum Caddy (2026-11-15). Scott's pick 4B: a round desk caddy split like a pie into wells
// of different heights, turning on a ball bearing. Engineering: ENGINEERING.md.
//
// The bearing is the one Scott tested (bearing_coupon.scad, 2026-11-15: "the test works"): 6 mm
// airsoft BBs in a channel 0.3 clear each side, the channel's floor (a top surface, ironed)
// under them and the drum's bed face over them. A post keeps the drum centred; nothing holds
// it down, so it lifts off for cleaning. Here the ball ring is 100 across (the test's was 60).
//
// The drum: six wedge wells round a centre well. Their heights climb 60 to 110 mm round the
// drum, a spiral staircase of slices. The centre well stands tallest.
//
//   part = "base" | "drum" | "plate" | "seated" | "gate_drum"

part = "seated";
$fn = 200;

// ---- the bearing (the test print's numbers) ----------------------------------------------
BALL = 6.0;
RING_R = 50;                // the ball circle: 46 balls (10 % of the ring left empty)
N_BALLS = 46;
CH_W = BALL + 0.6;          // 0.3 each side
BASE_T = 3;
CH_D = 4;
RIM = BASE_T + CH_D;
LIFT = BALL - CH_D;         // the drum's underside above the base's rim
BASE_R = 60;
POST_R = 8;
POST_GAP = 0.4;
HOLE_COMP = 0.15;           // vertical holes print this much small on the radius
BORE_R = POST_R + POST_GAP + HOLE_COMP;

// ---- the drum -----------------------------------------------------------------------------
DRUM_R = 75;
FLOOR = 3;                  // the drum's floor; its underside is the bed face the balls run on
WALL = 1.6;                 // outer wall and dividers: four beads
N_WELLS = 6;
HEIGHTS = [45, 59, 73, 87, 101, 115];   // each wedge's height, above the drum's underside: 14 a step
                                        // (10 a step read as a plain cylinder in the first render)
FLUTES = 48;                // the outer wall fluted like a pie dish: 48 scallops,
FLUTE_A = 1.2;              // 1.2 deep (vertical detail: it prints exactly)
HUB_R = 14;                 // the centre tube's outside
HUB_WALL = 2.4;
HUB_H = 122;
BORE_D = FLOOR + 9;         // the post goes 11 into the drum (the test's went 9)
POST_TOP = RIM + LIFT + BORE_D - 1;
WELL0 = BORE_D + BORE_R / tan(37) + 1.2;   // the centre well's floor: above the bore's 37 deg roof

module base() difference() {
    union() {
        linear_extrude(RIM) fluted2d(BASE_R);   // fluted to match the drum
        cylinder(h = POST_TOP, r = POST_R);
    }
    translate([0, 0, BASE_T]) difference() {
        cylinder(h = CH_D + 1, r = RING_R + CH_W / 2);
        translate([0, 0, -1]) cylinder(h = CH_D + 3, r = RING_R - CH_W / 2);
    }
    // hollow inside the channel, down to a 1.6 floor, round the post (as the test print)
    translate([0, 0, 1.6]) difference() {
        cylinder(h = RIM, r = RING_R - CH_W / 2 - 2);
        cylinder(h = RIM, r = POST_R + 2);
    }
    // the post's top: a chamfer so the drum finds it
    translate([0, 0, POST_TOP - 2]) difference() {
        cylinder(h = 2.01, r = POST_R + 1);
        cylinder(h = 2.01, r1 = POST_R, r2 = POST_R - 1.5);
    }
    // a 0.4 chamfer at the foot (elephant's foot)
    translate([0, 0, -0.01]) difference() {
        cylinder(h = 0.41, r = BASE_R + 1);
        linear_extrude(0.41, scale = BASE_R / (BASE_R - 0.4)) offset(delta = -0.4) fluted2d(BASE_R);
    }
}

// one wedge's footprint, angles a0..a1, from the hub to the drum's edge
module wedge2d(a0, a1, r0, r1) polygon(concat(
    [for (k = [0 : 24]) let (a = a0 + (a1 - a0) * k / 24) r1 * [cos(a), sin(a)]],
    [for (k = [24 : -1 : 0]) let (a = a0 + (a1 - a0) * k / 24) r0 * [cos(a), sin(a)]]));

// the fluted outline, and the wall inside it (a constant 1.6 all round the scallops)
module fluted2d(r) polygon([for (k = [0 : FLUTES * 12 - 1]) let (a = 360 * k / (FLUTES * 12))
    (r - FLUTE_A / 2 + FLUTE_A / 2 * cos(FLUTES * a)) * [cos(a), sin(a)]]);
module wall2d() difference() { fluted2d(DRUM_R); offset(delta = -WALL) fluted2d(DRUM_R); }
module sector2d(a0, a1) polygon(concat([[0, 0]], [for (k = [0 : 24]) let (a = a0 + (a1 - a0) * k / 24) 2 * DRUM_R * [cos(a), sin(a)]]));

module drum() {
    step = 360 / N_WELLS;
    difference() {
        union() {
            linear_extrude(FLOOR) fluted2d(DRUM_R);
            // the outer wall, each well's slice at its own height
            for (i = [0 : N_WELLS - 1]) linear_extrude(HEIGHTS[i])
                intersection() { wall2d(); sector2d(i * step, (i + 1) * step); }
            // dividers, each as tall as the taller well it parts
            for (i = [0 : N_WELLS - 1]) rotate(i * step)
                translate([HUB_R - 0.5, -WALL / 2, 0]) cube([DRUM_R - FLUTE_A - HUB_R, WALL, max(HEIGHTS[i], HEIGHTS[(i + N_WELLS - 1) % N_WELLS])]);
            cylinder(h = HUB_H, r = HUB_R);
        }
        // the centre well
        translate([0, 0, WELL0]) cylinder(h = HUB_H, r = HUB_R - HUB_WALL);
        // the post's bore, with a 37 deg roof (it prints with no support), and a 0.5 lead-in
        translate([0, 0, -0.01]) cylinder(h = BORE_D + 0.01, r = BORE_R);
        translate([0, 0, BORE_D - 0.01]) cylinder(h = BORE_R / tan(37), r1 = BORE_R, r2 = 0);
        translate([0, 0, -0.01]) cylinder(h = 0.51, r1 = BORE_R + 0.5, r2 = BORE_R);
        // a 0.4 chamfer at the drum's foot (elephant's foot)
        translate([0, 0, -0.01]) difference() {
            cylinder(h = 0.41, r = DRUM_R + 1);
            linear_extrude(0.41, scale = DRUM_R / (DRUM_R - 0.4)) offset(delta = -0.4) fluted2d(DRUM_R);
        }
    }
}

module balls() for (i = [0 : N_BALLS - 1]) rotate(i * 360 / N_BALLS) translate([RING_R, 0, BASE_T + BALL / 2]) sphere(d = BALL, $fn = 32);

if (part == "base") base();
else if (part == "drum" || part == "gate_drum") drum();
else if (part == "seated") { base(); translate([0, 0, BASE_T + BALL]) drum(); color("gold") balls(); }
else if (part == "plate") { base(); translate([BASE_R + DRUM_R + 6, 0, 0]) drum(); }
echo("RIM", RIM, "drum underside", BASE_T + BALL, "post top", POST_TOP, "bore top", BASE_T + BALL + BORE_D,
     "post into the drum", POST_TOP - (BASE_T + BALL), "centre well floor", WELL0);
