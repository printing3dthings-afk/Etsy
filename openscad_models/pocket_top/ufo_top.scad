// Pocket Top: the UFO (2026-11-15). Scott picked form 1 of five: a wide, low saucer with a
// little dome and a kawaii face, its mass at the rim. It's built on the snap Scott tested
// (snap_coupon.scad): pair 2, reach 0.45, "felt the best".
//
//   saucer  printed FLAT, top face up. The tested hub (hex hole, three spring beams in the
//           print plane), unchanged, inside a 38 mm saucer. Ten raised lights round its rim.
//   stem    printed UPSIDE DOWN, its dome's flat top on the bed. The dome (the twirl knob,
//           hollow, with the face), the tested hex and groove, and the spinning tip, all one
//           part. The dome's sides start at 37 deg from upright and steepen toward its rim,
//           so it prints inverted with no support. Only a small boss in its middle touches the
//           saucer, clear of the spring beams, as the coupon's grip did.
//
// Two parts where the brief allows three: the dome and the stem print as one, so there's one
// joint, the tested one. Not for children under 3: small parts.
//
//   part = "saucer" | "stem" | "plate" | "assembled" | "exploded" | "stem_in_use" (with lift)

use <snap_coupon.scad>
part = "assembled";
lift = 0;                   // for part = "stem_in_use": how far it is lifted off
$fn = 96;

D = snap_dims();
S = D[0]; A = D[1]; B = D[2]; NUB_H = D[3]; REACH = D[4]; PRELOAD = D[5]; FLANK = D[6];
P = 1;                      // the tested pair: reach 0.45

// ---- the saucer -------------------------------------------------------------------------
SAUCER_R = 17;              // 34 across: over the 31.7 mm small-parts cylinder. Each 0.5 mm
                            // of radius costs about 7 s of print (budget: 10 min, 5 g)
LIGHT_N = 9;                // the rim's lights: raised studs on the top face, outside the beams
LIGHT_R = 1.1;              // (they end at r 14.2). Studs, not a ring with portholes: the ring
LIGHT_H = 1.0;              // and its holes cost 1 min 50 s of print, the studs 14 s
LIGHT_AT = 15.0;
LIGHT_OFF = 10;             // degrees: 9 lights, 3 to each beam, all 1.7 clear of the slots
RIM_CH = 0.8;               // the rim's top edge, chamfered 45 deg: the saucer reads as a lens
FOOT = 0.4;                 // elephant's-foot chamfer

// ---- the stem, in its print position: the dome's top on the bed --------------------------
TOP_R = 3.2;                // the dome's flat top: the knob you twirl
TOP_CH = 0.5;
A0 = 37;                    // the dome's slope from upright at its top...
A1 = 22;                    // ...and at its rim
SLANT = 7.5;                // the dome's side, along its surface
CAB_WALL = 2.2;             // measured across (horizontally); 1.7 to 2.0 square to the surface
CAB_TOP = 1.4;              // the dome's top plate
COL_R = 3.0;                // the hex's column inside the dome
BOSS_R = 4.4;               // the shoulder ring that bears on the saucer (beams start at 4.75)
GAP = 0.4;                  // the dome's rim stands this far off the saucer
HEX_PAST = 1.0;             // the full hex runs this far past the saucer's underside
TIP_L = 4.6;                // then the tip: a cone to a 1 mm round end
TIP_R = 1.0;

kr = (A0 - A1) / SLANT * PI / 180;
function dome_r(s) = TOP_R + (cos(A0 - (A0 - A1) * s / SLANT) - cos(A0)) / kr;
function dome_z(s) = TOP_CH + (sin(A0) - sin(A0 - (A0 - A1) * s / SLANT)) / kr;
function dome_a(s) = A0 - (A0 - A1) * s / SLANT;
CAB_R = dome_r(SLANT);
CAB_H = dome_z(SLANT);
S0 = CAB_H + GAP;           // the shoulder: the saucer's top face sits here

// the dome's outline, from the bed up: chamfer, curved side, then down the inside
function dome_outer() = concat([[0, 0], [TOP_R - TOP_CH, 0]],
    [for (k = [0 : 24]) [dome_r(SLANT * k / 24), dome_z(SLANT * k / 24)]], [[0, CAB_H]]);

module dome() difference() {
    rotate_extrude($fn = 160) polygon(dome_outer());
    // the hollow: the outline moved in CAB_WALL, from the top plate up, round the column
    rotate_extrude($fn = 160) polygon(concat(
        [[COL_R, CAB_TOP]],
        [for (k = [0 : 24]) let (s = SLANT * k / 24, z = dome_z(s))
            if (z >= CAB_TOP) [max(dome_r(s) - CAB_WALL, COL_R), z]],
        [[CAB_R - CAB_WALL, CAB_H + 1], [COL_R, CAB_H + 1]]));
    face();
}

// ---- the face: eyes and a little mouth, engraved 0.5 square to the dome -------------------
FACE_S = 3.0;               // where on the dome's side (along it) the face is centred
EYE_DX = 2.2;               // each eye's centre, round the dome from the middle
EYE_W = 2.0;
EYE_H = 2.6;
MOUTH_DY = 2.5;             // the mouth, below the eyes (in use)
MOUTH_W = 1.6;
GROOVE = 0.5;
DEPTH = 0.5;

// a 2D shape in the face's frame (x round the dome, y down it in use), cut DEPTH into the dome
// and swept straight out, horizontally. Each shape comes to a point at its bottom (in use),
// the side that prints as a ceiling, so no ceiling hangs past 37 deg.
module face_cut(s, ang) {
    r = dome_r(s); z = dome_z(s); a = dome_a(s);
    n = [cos(a), 0, -sin(a)];                // outward normal, in the (x = radial, z) plane
    u = [sin(a), 0, cos(a)];                 // down the dome's side in use: up as it prints
    c = [r, 0, z] - DEPTH * n;
    rotate(ang) multmatrix([[u[0] * 0, u[0], 1, c[0]], [1, 0, 0, c[1]], [0, u[2], 0, c[2]], [0, 0, 0, 1]])
        linear_extrude(4) children();
}
module teardrop2d(w, h) hull() {
    translate([0, -h / 2 + w / 2]) circle(d = w, $fn = 32);
    translate([0, h / 2]) square([0.01, 0.01], center = true);
}
module vee2d(w, t) for (sx = [-1, 1]) hull() {
    translate([0, 0]) circle(d = t, $fn = 16);
    translate([sx * w / 2, -w / 2 * tan(55)]) circle(d = t, $fn = 16);
}
module face() {
    FRONT = -90;                             // faces -y, like every product's front
    for (sx = [-1, 1]) {
        s = FACE_S; r = dome_r(s);
        face_cut(s, FRONT + sx * EYE_DX / r * 180 / PI) teardrop2d(EYE_W, EYE_H);
    }
    face_cut(FACE_S + MOUTH_DY, FRONT) vee2d(MOUTH_W, GROOVE);
}

module stem() {
    rg = S / 2 - REACH[P] + PRELOAD;
    z0 = S0 + B - NUB_H - 0.15;
    z1 = S0 + B + 0.15;
    tip0 = S0 + B + HEX_PAST;
    difference() {
        union() {
            dome();
            // the column from the top plate to the shoulder, flaring at 37 deg to the boss
            cylinder(r = COL_R, h = S0 - (BOSS_R - COL_R) / tan(37));
            translate([0, 0, S0 - (BOSS_R - COL_R) / tan(37) - 0.01])
                cylinder(r1 = COL_R, r2 = BOSS_R, h = (BOSS_R - COL_R) / tan(37) + 0.01);
            // the tested hex, through the saucer, then the tip
            translate([0, 0, S0 - 0.01]) linear_extrude(tip0 - S0 + 0.01) hex2d(S);
            translate([0, 0, tip0 - 0.01]) hull() {
                linear_extrude(0.01) hex2d(S);
                translate([0, 0, TIP_L - TIP_R]) sphere(r = TIP_R, $fn = 32);
            }
        }
        // the tested groove: square at the shoulder end (it faces up as it prints), the catch
        // flank at 60 deg from horizontal
        rotate_extrude($fn = 96) polygon([[rg, z0], [S, z0], [S, z1 + (S - rg) * tan(FLANK)], [rg, z1]]);
    }
}

module saucer(nubs = true) difference() {
    union() {
        linear_extrude(B) difference() {
            circle(r = SAUCER_R, $fn = 192);
            hex2d(2 * A);
            for (k = [0 : 2]) rotate(120 * k) beam_cut();
        }
        if (nubs) linear_extrude(NUB_H) for (k = [0 : 2]) rotate(120 * k) nub(P);
        for (k = [0 : LIGHT_N - 1]) rotate(k * 360 / LIGHT_N + LIGHT_OFF) translate([LIGHT_AT, 0, B - 0.01]) hull() {
            cylinder(r = LIGHT_R, h = LIGHT_H - 0.4 + 0.01, $fn = 32);
            cylinder(r = LIGHT_R - 0.4, h = LIGHT_H + 0.01, $fn = 32);
        }
    }
    translate([0, 0, B - RIM_CH]) difference() {
        cylinder(r = SAUCER_R + 1, h = RIM_CH + 0.01, $fn = 192);
        cylinder(r1 = SAUCER_R, r2 = SAUCER_R - RIM_CH - 0.01, h = RIM_CH + 0.01, $fn = 192);
    }
    translate([0, 0, -0.01]) difference() {
        cylinder(r = SAUCER_R + 1, h = FOOT + 0.01, $fn = 192);
        cylinder(r1 = SAUCER_R - FOOT, r2 = SAUCER_R, h = FOOT + 0.01, $fn = 192);
    }
}

// in use: the stem turned over (about y, so its face stays at the front), its shoulder on the
// saucer's top face
module stem_in_use(lift = 0) translate([0, 0, B + S0 + lift]) rotate([0, 180, 0]) stem();
module assembled(lift = 0) { color("#9BD3C8") saucer(); color("#F2C6DA") stem_in_use(lift); }

if (part == "saucer") saucer();
else if (part == "stem") stem();
else if (part == "plate") { saucer(); translate([SAUCER_R + CAB_R + 4, 0, 0]) stem(); }
else if (part == "assembled") assembled();
else if (part == "exploded") assembled(14);
else if (part == "stem_in_use") stem_in_use(lift);
echo("dome", 2 * CAB_R, "across,", CAB_H, "tall; shoulder", S0, "; stem", S0 + B + HEX_PAST + TIP_L,
     "long; tip below the saucer", HEX_PAST + TIP_L, "; overall height", S0 + 2 * B + HEX_PAST + TIP_L - B);
