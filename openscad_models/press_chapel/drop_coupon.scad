// Press-to-Light Chapel: the lift-and-drop test print (2026-11-17). Scott, 2026-11-14:
// lift-and-drop first, no spring. The steeple is lifted and let go; its weight drives a
// twisted star bar down through a short star nut in the spinner's hub, so the spinner
// turns, and just before the steeple lands the star leaves the nut through the bottom
// and the spinner coasts on a point pivot. Numbers in chapel_budget.py.
//
// Five parts: the base (the pivot point), the arch (the guide; it plugs into the base),
// the shaft, the steeple (a weight, pressed onto the shaft's square key) and three hubs,
// the same but for the nut's clearance (1, 2, 3 notches in the hub's flag).
//
// Everything is drawn in place at the LIFTED position. DROP (0 to TRAVEL) lowers the
// shaft and steeple and turns the hub by the helix, for the fit check's sweep.
//
//   part = "assembly" | "base" | "arch" | "shaft" | "steeple" | "hub" (with v) |
//          "moving" (shaft + steeple at DROP) | "hub_at" (hub v at DROP) | "frame" |
//          "print_*" (each laid on the bed for printing)

part = "assembly";
v = 1;               // hub variant: 1, 2, 3
DROP = 0;
SPIN = 0;            // extra hub turn (deg), for the check that it spins free at rest
$fn = 48;

LEAD = 24;           // mm of drop per turn. At 20 the nut's slots (r 3.55) leaned 48 deg and the
                     // gate's slicer propped them; at 24 every flank in the nut is at or under 45
R_OUT = 3.15; R_IN = 2.0; TW = 1.8; TEETH = 4;
CLEAR = [0.3, 0.4, 0.5];
NUT_H = 4; STAR_L = 20; TIP = 3;     // star 20 + nut 4 = one full driven turn at LEAD 24
// above the star, the star tapers to the rod's width over TAPER_H, twisted the same way: printed
// upside down it holds the star's end up (a flat end hung 1.5 mm off the rod), and every section
// lies inside the star's outline, so it passes the nut
TAPER_H = 5;
ROD_R = 1.6;          // the plain rod above the star: the nut turns freely round it
KEY = 4.6; KEY_C = 0.3;   // the square key, and its clearance in the guide

// heights (z up, the base's top at 3)
PLATE = 2.4;          // the base, a strip under the pivot and the two sockets
PIN_Z0 = 5; PIN_R = 2.5; PIN_HALF = 30;            // pin cone, half-angle
PIN_TIP = PIN_Z0 + PIN_R / tan(PIN_HALF);          // 9.33: where the hub sits
SOCK_HALF = 40;                                    // the hub's socket: wider, so it meets the pin only at the tip
PIN_TOP_R = 0.4;
HUB_Z0 = 6.5; HUB_R = 6.0;
BORE_R = R_OUT + 0.6; BORE_Z0 = PIN_TIP + 1.6;
NUT_Z0 = 40.5; NUT_Z1 = NUT_Z0 + NUT_H;            // the hub's top is the nut's top; under it, room for the 20 mm star at rest
FLAG_R = 17; FLAG_T = 1.6;
TRAVEL = STAR_L + TAPER_H + NUT_H + 1;              // 30: the star and its taper clear the nut by 1 at rest
// the shaft at the lifted position
STAR_Z0 = NUT_Z1; STAR_Z1 = STAR_Z0 + STAR_L;       // its tip in the nut, ready to drop
// the lift stop: a collar under the key. It never goes through the nut (at rest it is 1 above the
// hub), and its top is a 45 deg cone that seats in the tunnel's mouth: printed upside down it holds
// the collar up, and at 45 it can't wedge (friction's angle is 29 at worst). The taper had met the
// tunnel 1.2 above where it was meant to, at about 18 deg: a wedge that could hold the steeple up
COLLAR_R = 4.5; COLLAR_T = 1.2;     // its rim 1.2: at 0.6 it was under the gate's wall floor
STOP_HALF = 38;     // the cone's half-angle: 45 sat on the slicer's limit printed upside down; 38 is
                    // still wider than friction's 29, so it seats and lets go
C0 = NUT_Z1 + 1 + TRAVEL;                           // the collar's foot, lifted
KEY_Z0 = C0 + COLLAR_T;
TAPER_S = ROD_R / R_OUT;
// the guide: its underside 0.05 above where the collar's cone meets the tunnel's sides, lifted
GUIDE_Z0 = C0 + COLLAR_T + (COLLAR_R - (KEY / 2 + KEY_C)) / tan(STOP_HALF) + 0.05; GUIDE_Z1 = GUIDE_Z0 + 10;
SOCKET = 10;                                        // the key's length inside the steeple
KEY_Z1 = GUIDE_Z1 + TRAVEL + SOCKET;                // at rest the steeple sits on the guide
// the arch
LEG_X = 22; LEG_W = 4; LEG_T = 6; LEAN_Z = 40;   // the legs' inner faces at 22: the bosses at their feet clear the flag (17) by 2
PEG = 4; PEG_C = 0.15;

echo("taper print z", KEY_Z1 - STAR_Z1 - TAPER_H, KEY_Z1 - STAR_Z1, "tip print z", KEY_Z1 - STAR_Z0, KEY_Z1 - STAR_Z0 + TIP, "pin tip", PIN_TIP, "nut", NUT_Z0, NUT_Z1, "travel", TRAVEL, "guide", GUIDE_Z0, GUIDE_Z1, "key", KEY_Z0, KEY_Z1);

module star2d(c = 0) offset(delta = c) union() {
    circle(r = R_IN);
    for (i = [0 : TEETH - 1]) rotate(i * 360 / TEETH) translate([0, -TW / 2]) square([R_OUT, TW]);
}
// the helix: the star at height z is turned -360 z / LEAD, whatever piece it is in
module helix(z0, z1, c = 0) translate([0, 0, z0]) rotate(-360 * z0 / LEAD)
    linear_extrude(z1 - z0, twist = 360 * (z1 - z0) / LEAD, slices = ceil((z1 - z0) / 0.2), convexity = 6) star2d(c);

// ---- the moving parts, lifted ----
module shaft() {
    helix(STAR_Z0, STAR_Z1);
    // the tip: the star tapering to a quarter of its size, twisted the same way, so it finds the
    // nut on the way back up. A round cone here met the star's root circle on the same radius,
    // and the two polygons left slivers the wall check read as thin (2026-11-17)
    translate([0, 0, STAR_Z0 - TIP]) rotate(-360 * (STAR_Z0 - TIP) / LEAD)
        linear_extrude(TIP + 0.01, twist = 360 * (TIP + 0.01) / LEAD, scale = 4, slices = ceil(TIP / 0.2), convexity = 6) scale(0.25) star2d();
    translate([0, 0, STAR_Z1 - 0.01]) cylinder(r = ROD_R, h = KEY_Z0 - STAR_Z1 + 0.02);
    translate([0, 0, C0]) cylinder(r = COLLAR_R, h = COLLAR_T + 0.01);
    translate([0, 0, C0 + COLLAR_T]) cylinder(r1 = COLLAR_R, r2 = ROD_R, h = (COLLAR_R - ROD_R) / tan(STOP_HALF));   // the stop face
    translate([0, 0, STAR_Z1 - 0.01]) rotate(-360 * STAR_Z1 / LEAD)
        linear_extrude(TAPER_H, twist = 360 * TAPER_H / LEAD, scale = TAPER_S, slices = ceil(TAPER_H / 0.2), convexity = 6) star2d();
    // the key, turned 45 deg: printed flat, the arch's tunnel is then a diamond with 45 deg roofs
    translate([0, 0, KEY_Z0]) rotate(45) translate([-KEY / 2, -KEY / 2, 0]) cube([KEY, KEY, KEY_Z1 - KEY_Z0]);
}
module steeple() translate([0, 0, GUIDE_Z1 + TRAVEL]) difference() {
    union() {
        translate([-7, -7, 0]) cube([14, 14, 28]);
        translate([0, 0, 28]) rotate(45) cylinder(r1 = 7 * sqrt(2), r2 = 0, h = 18, $fn = 4);
    }
    // the key's socket, a press fit: 0.05 under the key all round
    rotate(45) translate([-KEY / 2 + 0.05, -KEY / 2 + 0.05, -1]) cube([KEY - 0.1, KEY - 0.1, SOCKET + 1]);
    translate([0, 0, -0.01]) rotate(45) linear_extrude(0.6, scale = (KEY - 0.1) / (KEY + 0.8)) square(KEY + 0.8, center = true);   // a lead-in chamfer
}

// ---- the hub: the nut at the top, a bore below it for the star at rest, the socket underneath ----
module hub(c) difference() {
    union() {
        translate([0, 0, HUB_Z0]) cylinder(r = HUB_R, h = NUT_Z1 - HUB_Z0);
        // the flag: a disc with three windows, so its turning shows; 1-3 notches name the clearance
        translate([0, 0, HUB_Z0]) difference() {
            cylinder(r = FLAG_R, h = FLAG_T);
            for (a = [0, 120, 240]) rotate(a) translate([11.5, 0, -1]) cylinder(r = 3.2, h = 4);
            for (k = [1 : v]) rotate(60 + (k - 2) * 12) translate([FLAG_R - 0.6, -0.7, -1]) cube([2, 1.4, 4]);
        }
    }
    helix(NUT_Z0 - 0.01, NUT_Z1 + 0.01, c);
    // the bore; under the nut, a cone 3 mm tall (26 deg from upright) for the nut teeth's
    // undersides, with the star's slots running straight down through it. A round cone alone
    // filled the slots and the shaft ran into it (the fit check); a star flared by scaling
    // tilted the teeth's sides past 45 and the gate's slicer propped the nut (2026-11-17)
    let (h = 3) {
        translate([0, 0, BORE_Z0]) cylinder(r = BORE_R, h = NUT_Z0 - h - BORE_Z0 + 0.01);
        translate([0, 0, NUT_Z0 - h]) cylinder(r1 = BORE_R, r2 = R_IN + c, h = h + 0.01);
        helix(NUT_Z0 - h - 0.01, NUT_Z0 + 0.01, c);
    }
    // the socket on the pin: a 40 deg cone, its apex at the pin's tip
    translate([0, 0, HUB_Z0 - 0.01]) cylinder(r1 = (PIN_TIP - HUB_Z0) * tan(SOCK_HALF), r2 = 0, h = PIN_TIP - HUB_Z0 + 0.01);
}

// ---- the frame ----
module base_outline() offset(r = 2) offset(delta = -2) union() {
    square([LEG_X * 2 + 16, 18], center = true);
    for (sx = [-1, 1]) translate([sx * (LEG_X + LEG_W / 2), -LEG_T / 2]) square([LEG_W + 6, LEG_T + 6], center = true);
}
// the bosses' sharp corners stood outside the plate's rounded ones and hung over air (the gate's slicer)
module base() {
    difference() {
        union() {
            linear_extrude(PLATE) base_outline();
            // the bosses, their corners rounded like the plate's: square ones stood out past its corners
            for (sx = [-1, 1]) translate([sx * (LEG_X + LEG_W / 2), -LEG_T / 2, PLATE - 0.01]) linear_extrude(6 + 0.02)
                offset(r = 2) offset(delta = -2) square([LEG_W + 6, LEG_T + 6], center = true);
        }
        for (sx = [-1, 1]) translate([sx * (LEG_X + LEG_W / 2), -LEG_T / 2, PLATE + 6 - PEG / 2 + 0.01])
            cube([LEG_W + 2 * PEG_C, LEG_T + 2 * PEG_C, PEG + 0.02], center = true);
        // a 0.4 chamfer at the foot (elephant's foot), in 0.1 steps: one 0.4 step is a ledge
        for (k = [0 : 3]) translate([0, 0, k * 0.1 - 0.01]) linear_extrude(0.11)
            difference() { offset(delta = 1) base_outline(); offset(delta = -(0.4 - k * 0.1)) base_outline(); }
    }
    translate([0, 0, PLATE - 0.01]) cylinder(r = PIN_R, h = PIN_Z0 - PLATE + 0.01);
    // the pin's top: a 0.4 radius flat, not a needle point (a point under a bead doesn't print;
    // the gate lost 0.27 of it). The hub's socket sits on its edge with its apex at PIN_TIP:
    // the friction radius is the budget's 0.4
    translate([0, 0, PIN_Z0 - 0.01]) cylinder(r1 = PIN_R, r2 = PIN_TOP_R, h = PIN_TIP - PIN_TOP_R / tan(SOCK_HALF) - PIN_Z0 + 0.01);
}
// the arch: two legs in the x-z plane (y -LEG_T to 0), leaning in above LEAN_Z to the guide
// block, 12 deep round its square tunnel. Legs and block share the back face (y = -LEG_T),
// the face it prints on.
GB_D = 2 * LEG_T;   // 12: centred on the axis
module arch2d() union() {
    for (s = [-1, 1]) {
        translate([s * (LEG_X + LEG_W / 2) - LEG_W / 2, PLATE + 6 - PEG]) square([LEG_W, LEAN_Z - (PLATE + 6 - PEG)]);
        hull() {   // printed flat on its face, so the lean is not an overhang
            translate([s * (LEG_X + LEG_W / 2) - LEG_W / 2, LEAN_Z - 0.01]) square([LEG_W, 0.01]);
            translate([s * 6 - LEG_W / 2, GUIDE_Z0]) square([LEG_W, GUIDE_Z1 - GUIDE_Z0]);
        }
    }
}
module arch() difference() {
    union() {
        rotate([90, 0, 0]) linear_extrude(LEG_T) arch2d();
        translate([-8, -LEG_T, GUIDE_Z0]) cube([16, GB_D, GUIDE_Z1 - GUIDE_Z0]);
    }
    // the tunnel the key slides in; the block's centre is the axis (y = 0)
    // printed flat (+y up), the diamond's roof was exactly 45 deg; peaked 1 mm higher it is 52
    translate([0, 0, GUIDE_Z0 - 1]) linear_extrude(GUIDE_Z1 - GUIDE_Z0 + 2) hull() {
        rotate(45) square(KEY + 2 * KEY_C, center = true);
        translate([0, (KEY / 2 + KEY_C) * sqrt(2) + 1]) circle(0.01);
    }
}

module moving() translate([0, 0, -DROP]) { shaft(); steeple(); }
module hub_at() rotate(-360 * DROP / LEAD + SPIN) hub(CLEAR[v - 1]);

if (part == "assembly") { base(); arch(); moving(); hub_at(); }
else if (part == "base") base();
else if (part == "arch") arch();
else if (part == "frame") { base(); arch(); }
else if (part == "shaft") shaft();
else if (part == "steeple") steeple();
else if (part == "hub") hub(CLEAR[v - 1]);
else if (part == "moving") moving();
else if (part == "hub_at") hub_at();
// laid on the bed
else if (part == "print_base") base();
else if (part == "print_arch") translate([0, 0, LEG_T]) rotate([90, 0, 0]) arch();             // flat on its back face
else if (part == "print_shaft") translate([0, 0, KEY_Z1]) rotate([180, 0, 0]) shaft();           // key on the bed, tip up
else if (part == "print_steeple") translate([0, 0, -(GUIDE_Z1 + TRAVEL)]) steeple();
else if (part == "print_hub") translate([0, 0, -HUB_Z0]) hub(CLEAR[v - 1]);
