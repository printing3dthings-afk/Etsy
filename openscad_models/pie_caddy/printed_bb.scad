// Printed 6 mm balls for the Pie Caddy bearing test (2026-11-12, Scott: "I want to
// print the bb's"). Stand-ins for 6 mm airsoft BBs: the bearing's channel is 6.6 wide
// and 4 deep, and it needs 27 balls.
//
// A ball can't print round all the way down: the lowest layers of a sphere hang out
// past the one below. So each ball stands on a flat, FLAT deep. At 0.4 the flat is
// 3.0 mm across, and the first layers above it step out 0.30, 0.28, 0.16 mm, under one
// 0.42 bead each. At 0.2 the second layer steps out a full bead and sags.
// The flat costs roundness: a ball lying on its flat is 5.6 tall instead of 6.0, so it
// carries no load until it rolls off it. That's what the test will show.
//
//   part = "plate" (N balls) | "ball"

part = "plate";
BALL = 6.0;
FLAT = 0.4;        // depth of the flat it stands on
N = 30;            // 27 for the bearing, 3 spare
COLS = 6;
PITCH = 9;         // 3 mm between balls
$fn = 64;

module ball() translate([0, 0, -FLAT]) difference() {
    translate([0, 0, BALL / 2]) sphere(d = BALL);
    translate([0, 0, FLAT - 5]) cube([BALL + 2, BALL + 2, 10], center = true);   // everything below FLAT
}

if (part == "ball") ball();
else for (i = [0 : N - 1]) translate([(i % COLS) * PITCH, floor(i / COLS) * PITCH, 0]) ball();

echo("flat across", 2 * sqrt(FLAT * (BALL - FLAT)), "height", BALL - FLAT);
