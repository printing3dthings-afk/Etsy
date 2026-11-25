// Snowfall Plinko v2: the 6 mm BB test print (2026-11-25). Numbers: bb_budget.py.
//
// Scott's v1 release test: the bridged cage was great; the 5 mm print-in-place balls broke loose
// during the print. He picked 6 mm airsoft BBs. This tests what changes:
//   - the cage sized for a 6 mm BB (0.4 either side of it, front openings 3.0);
//   - two rows of pegs on the v1 gap rule scaled to 6 mm (every gap a pass >= 7.8 or a stop <= 4.2);
//   - a loading port through the top wall, closed by a snap-in plug: the chalet's arrow tab
//     (two in-plane prongs, 1.3 x 12) through a 3.0 wall. Three plugs, reach 0.35 / 0.45 / 0.55,
//     marked by one, two or three notches on the head.
//
// Printed lying on its back, front cage up, as v1 was. In use it stands up (+y up), port on top.
//
//   part = plate | board | plug (with which = 0..2) | assembled (review)

part = "plate";
which = 1;
$fn = 48;

BB = 6.0;
FLOOR = 1.4;           // the back (v1's)
D = BB + 0.8;          // inside depth: 0.4 either side of a BB
LAT_T = 1.2; LAT_BAR = 1.4; LAT_OPEN = 3.0;     // the cage Scott called great, as v1
WALL = 1.6;
TOPWALL = 3.0;         // the plug's grip (the chalet's)
W = 31.5;              // inside width
H = 34;                // inside height (42 sliced the plate at 45 m, over the 30-minute limit)
PEG_R = 1.5;
ROW1 = [[-6, 0], [6, 0]];                     // y from the top inside face, below
ROW2 = [[-11.5, 0], [0, 0], [11.5, 0]];
Y1 = 15; Y2 = 24;      // rows' depth below the top inside face: the plug's prongs reach ~7 in; row 2 leaves 8.5 to the floor (a pass)
PORT = 7.0;            // the port, across: a BB passes with 0.5 a side
RIBS = [-13, -6.5, 0, 6.5, 13];               // no bar spans more than ~6.5 (v1's rule)

// the plug: the chalet stub, with a head instead of a panel
REACH = [0.35, 0.45, 0.55];
PT = D - 0.4;          // plug thickness: 0.2 clear of the back and the cage
T = 1.3; L = 12; GAP = 4.0; SIDE = 0.8;
XS = PORT / 2;         // the port's half-width
XO = GAP / 2 + T;      // a prong's outer face (3.3: 0.2 inside the port)
CATCH_CL = 0.15; CATCH = 50; RAMP = 30; CREST = 0.4;
TIP = GAP / 2 + 1.2;   // each prong ends 1.2 wide (at 2.4 they came to 0.4, under the gate's wall floor)
HW = 16; HH = 14;      // the head: grip for a thumb and finger

Z_TOP = FLOOR + D + LAT_T;
OW = W + 2 * WALL; OH = H + WALL + TOPWALL;
function yt() = H / 2;          // the top inside face, board centred on the inside

module inside2d() translate([-W / 2, -H / 2]) square([W, H]);
module pegs2d() {
    for (p = ROW1) translate([p[0], yt() - Y1]) circle(r = PEG_R);
    for (p = ROW2) translate([p[0], yt() - Y2]) circle(r = PEG_R);
}
module lattice_open2d() difference() {
    intersection() {
        inside2d();
        for (k = [-10 : 10]) translate([0, k * (LAT_BAR + LAT_OPEN)]) square([200, LAT_OPEN], center = true);
    }
    for (x = RIBS) translate([x, 0]) square([LAT_BAR, 200], center = true);
    pegs2d();
}
module board() difference() {
    translate([-OW / 2, -H / 2 - WALL, 0]) cube([OW, OH, Z_TOP]);
    // the chamber, pegs left standing full depth (they hold the cage up too)
    translate([0, 0, FLOOR]) linear_extrude(D) difference() { inside2d(); pegs2d(); }
    // the cage's openings
    translate([0, 0, FLOOR + D - 0.01]) linear_extrude(LAT_T + 1) lattice_open2d();
    // the loading port through the top wall, the chamber's full depth
    translate([-XS, yt() - 0.01, FLOOR]) cube([PORT, TOPWALL + 1, D]);
}

// the plug's outline, its prongs pointing -y, the shoulder (head's underside) at y = 0
function prong(r) = let(
    yc = -(TOPWALL + CATCH_CL),
    yn = yc - (XS + r - XO) / tan(CATCH),
    yr = yn - CREST,
    yt = yr - (XS + r - TIP) / tan(RAMP))
    [[GAP / 2, 0.01], [XO, 0.01], [XO, yc], [XS + r, yn], [XS + r, yr], [TIP, yt], [GAP / 2, yt]];
module plug2d(i) difference() {
    union() {
        translate([-HW / 2, 0]) offset(r = 2) offset(delta = -2) square([HW, HH]);
        for (m = [0, 1]) mirror([m, 0]) polygon(prong(REACH[i]));
    }
    yr = -(TOPWALL + CATCH_CL) + L;
    for (cx = [0, -(XO + SIDE / 2), XO + SIDE / 2]) {
        w = cx == 0 ? GAP : SIDE;
        hull() { translate([cx - w / 2, -1]) square([w, 0.01]); translate([cx, yr - w / 2]) circle(d = w); }
    }
    for (k = [0 : i]) translate([(k - i / 2) * 3 - 0.6, HH - 1.2]) square([1.2, 2]);
}
module plug(i) linear_extrude(PT) plug2d(i);

if (part == "board") board();
else if (part == "plug") plug(which);
else if (part == "plate") {
    board();
    for (i = [0 : 2]) translate([OW / 2 + 14 + i * (HW + 5), -10, 0]) plug(i);
}
else if (part == "assembled") {
    color("#EDE8DC") board();
    color("#C83238") translate([0, yt() + TOPWALL, FLOOR + 0.2]) plug(which);
}
