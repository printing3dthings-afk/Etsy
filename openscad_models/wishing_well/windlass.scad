// Stone Wishing Well: the windlass, and its test print (2026-11-15).
// Numbers: windlass_budget.py (checks/windlass_budget.txt). Engineering: ENGINEERING.md.
//
// Parts, each in its own print orientation:
//   post(e, pawl)  printed FLAT, outer face up. A snap cradle at the top: the journal presses
//                  down between two fingers that bend in the print plane. The crank-side post
//                  carries the pawl's T-headed pin on its outer face.
//   axle()         printed UPRIGHT, far end down: journal B, the drum, journal A, a collar,
//                  then the Pocket Top hex with its groove.
//   wheel()        printed FLAT, inner face down: ratchet teeth round the rim, the Pocket Top
//                  hub (three in-plane beams) round the hex hole, a handle peg on the outer face.
//   pawl()         printed FLAT. Hangs on the pin; gravity drops it into the teeth.
//   bucket()       printed upright; the twine bail threads down through its two ears.
//
// Viewed from outside the crank side (the posts' and the wheel's print-top view), the pawl
// blocks clockwise turns. The bucket's twine leaves the drum on the side that makes the
// bucket pull clockwise: see checks/fit_windlass.txt and the guide.
//
//   part = "coupon" (the test plate) | "posts" | "axle" | "wheel" | "pawl" | "bucket" | "base" |
//          "post" (one, by e and pawl) | "assembled" (review) | "none"

part = "coupon";
e_sel = 0.55;            // for part = "post"
pawl_sel = true;
$fn = 64;

// ---- the journal and its cradle -------------------------------------------------------
R_J = 3.0;               // journal radius
C = 0.25;                // cradle radius over the journal: both drawn in XY
RC = R_J + C;
FT = 8;                  // post thickness (print Z): the fingers' width
G = 0.8;                 // slot width; slot ends round, r 0.4
T_F = 1.3;               // finger thickness in the bend
ROOT = 8;                // fingers' root below the axle centre: finger 10.1 long to the catch
SAD = RC + 1.2;          // the saddle under the journal, half width
U_IN = SAD + G;          // finger inner edge
U_OUT = U_IN + T_F;      // finger outer edge
U_SLOT = U_OUT + G;      // outer slot's outer edge
HEAD = U_SLOT + 1.65;    // the head's half width: 9.0
TOP = 5;                 // head top above the axle centre
POST_W = 10;
TEN_W = 8;               // tenon width, into the base or the well's coping
TEN_H = 5;

// ---- the pawl, ratchet and crank -------------------------------------------------------
WHEEL_R = 17;
TOOTH_H = 1.6;
TEETH = 24;              // 15 deg a click (32, with tips sharp enough to print, left the pawl's tip
                         // and the teeth's tips under 1.2 mm)
RAMP_DEG = 45;           // the ramp's angle from the tangent (handbook: 30-45; at 35, with the
                         // tip land, the gap left the pawl's tip 0.6 thick)
P = [11, 20.5];          // pawl pivot from the axle centre; the load line passes under it, so
                         // a loaded tooth drives the pawl deeper, not out (fit check)
PIN_R = 1.5;
BOSS_H = 3.6;            // spacer under the pawl: puts it in the wheel's plane (WHEEL_W0 + 0.2)
PAWL_T = 3.0;
HEAD_L = 5.6;            // T-head bar, vertical: the pawl goes on only when lifted 78 deg
HEAD_W = 3.0;
COLLAR_G = 0.2;          // axial play each side of a post
COLLAR_CONE = 2.0;
COLLAR_FLAT = 1.2;       // the rim over the cone: at 0.6 its edge was a 0.6 mm knife
WHEEL_W0 = COLLAR_G + COLLAR_CONE + COLLAR_FLAT;     // wheel's inner face past the post's outer face
WHEEL_T = 3.4;           // the Pocket Top hub thickness
PEG_R = 2.4;
PEG_AT = [0, 12.5];      // on the wheel, between two of the hub's beams
PEG_L = 12;

// ---- the Pocket Top hub joint (openscad_models/pocket_top/snap_coupon.scad, pair 2) -----
S_HEX = 5.0;
H_CLR = 0.15;
H_A = S_HEX / 2 + H_CLR;
H_WALL = 1.3;
H_G = 0.8;
H_T = 1.3;
H_L = 12.0;
NUB_W = 1.4;
NUB_H = 1.6;
WIN = 0.3;
REACH = 0.45;
PRELOAD = 0.05;
FLANK = 60;
CH = 0.8;

// ---- the drum ----------------------------------------------------------------------------
R_DRUM = 5.0;
TIE_R = 0.8;             // twine hole through the drum, along the axis
TIE_AT = 3.2;

// ---- 2D helpers ---------------------------------------------------------------------------
module slot2d(x0, x1, y0, y1) hull() {          // a slot with round ends, G wide
    w = x1 - x0;
    translate([x0, y0 + w / 2]) square([w, max(0.01, y1 - y0 - w / 2)]);
    translate([(x0 + x1) / 2, y0 + w / 2]) circle(d = w, $fn = 24);
}

// The post, in its own plane: u across, v up, the axle centre at (0, hc). v = 0 is the tenon's foot.
module post2d(e, hc, pawl) {
    mouth = R_J - e;
    difference() {
        union() {
            translate([-TEN_W / 2, 0]) square([TEN_W, TEN_H + 0.01]);
            translate([-POST_W / 2, TEN_H]) square([POST_W, hc - ROOT - 5 - TEN_H + 0.01]);
            hull() {
                translate([-POST_W / 2, hc - ROOT - 5]) square([POST_W, 0.01]);
                translate([-HEAD, hc - ROOT - 2]) square([2 * HEAD, 0.01]);
            }
            translate([-HEAD, hc - ROOT - 2]) square([2 * HEAD, ROOT + 2 + TOP]);   // square: rounded
                                                  // corners left 0.01 mm slivers against the neck
            if (pawl) hull() {                    // the arm that carries the pawl pin
                translate([U_SLOT + 0.25, hc - ROOT - 2]) square([HEAD - U_SLOT - 0.25, ROOT + 2 + TOP]);
                translate([P[0], hc + P[1]]) circle(r = 4.6, $fn = 48);
            }
        }
        // the variant's mark: 1, 2 or 3 notches in the post's left edge for a catch of 0.40, 0.55
        // or 0.70 (upright cuts through the thickness: they hang over nothing)
        for (k = [0 : round((e - 0.25) / 0.15) - 1]) translate([-POST_W / 2 - 0.01, TEN_H + 2.5 + k * 2.2]) square([1.0, 0.9]);
        // the journal's seat, and the slots that free the fingers
        translate([0, hc]) circle(r = RC, $fn = 96);
        for (s = [-1, 1]) {
            // inner slot: finger from saddle, root to just above the axle centre
            mirror([s < 0 ? 1 : 0, 0]) {
                slot2d(SAD, U_IN, hc - ROOT, hc + G);
                translate([0, hc]) square([U_IN, G]);       // opens into the seat
                slot2d(U_OUT, U_SLOT, hc - ROOT, hc + TOP + 1);
            }
        }
        // the mouth: narrower than the journal by e each side, then a 30 deg lead-in
        translate([-mouth, hc]) square([2 * mouth, TOP + 1]);
        lead = TOP - 3;
        translate([0, hc + 3]) polygon([[-mouth, 0], [mouth, 0], [mouth + (lead + 1) * tan(30), lead + 1],
                                        [-mouth - (lead + 1) * tan(30), lead + 1]]);
    }
}

module post(e, hc, pawl) {
    linear_extrude(FT) post2d(e, hc, pawl);
    if (pawl) translate([P[0], hc + P[1], FT]) pawl_pin();
}

// the pawl's pin, upright on the post's outer face: a spacer, the pin, and a T-head whose
// underside slopes at 37 deg (it prints with no support)
module pawl_pin() {
    cylinder(r = 3.0, h = BOSS_H, $fn = 48);
    cylinder(r = PIN_R, h = BOSS_H + PAWL_T + 0.3 + 0.01, $fn = 32);
    translate([0, 0, BOSS_H + PAWL_T + 0.3]) hull() {
        cylinder(r = PIN_R, h = 0.01, $fn = 32);
        translate([0, 0, (HEAD_L / 2 - PIN_R) / tan(37)]) linear_extrude(0.6) offset(r = 0.5) offset(delta = -0.5)
            square([HEAD_W, HEAD_L], center = true);
    }
}

// ---- ratchet wheel --------------------------------------------------------------------------
// tooth i: its locking face is radial at angle i*pitch, facing clockwise; its ramp climbs at
// RAMP_DEG from the root just counter-clockwise of the next face. Turning the wheel clockwise
// drives a locking face into the pawl; counter-clockwise, the ramps lift it.
LAND = 1.0;              // a flat on each tooth's tip: sharp tips read as 0.4 mm walls
function tooth_pts(i) = let (p = 360 / TEETH, a = i * p, rr = WHEEL_R - TOOTH_H,
                             land = LAND / WHEEL_R * 180 / PI,
                             ramp = TOOTH_H / tan(RAMP_DEG) / WHEEL_R * 180 / PI)
    [[WHEEL_R * cos(a), WHEEL_R * sin(a)],
     for (k = [0 : 6]) let (t = a + land + ramp * k / 6, r = WHEEL_R - TOOTH_H * k / 6) [r * cos(t), r * sin(t)],
     [rr * cos(a + p), rr * sin(a + p)]];
module wheel2d() polygon([for (i = [0 : TEETH - 1]) each tooth_pts(i)]);

module hex2d(af) rotate(30) circle(d = af / cos(30), $fn = 6);
module beam_cut() {
    x0 = H_A + H_WALL;
    for (cx = [x0 + H_G / 2, x0 + H_G + H_T + H_G / 2])
        hull() { translate([cx - H_G / 2, -NUB_W / 2 - H_G]) square([H_G, 0.01]); translate([cx, H_L]) circle(d = H_G, $fn = 24); }
    translate([x0, -NUB_W / 2 - H_G]) square([2 * H_G + H_T, H_G]);
    translate([H_A - 1, -NUB_W / 2 - WIN]) square([H_WALL + 1.01, NUB_W + 2 * WIN]);
}
module nub2d() translate([S_HEX / 2 - REACH, -NUB_W / 2]) square([H_A + H_WALL + H_G - (S_HEX / 2 - REACH) + 0.01, NUB_W]);

module wheel(nubs = true) {
    difference() {
        linear_extrude(WHEEL_T) difference() {
            wheel2d();
            hex2d(2 * H_A);
            for (k = [0 : 2]) rotate(120 * k) beam_cut();
        }
    }
    if (nubs) linear_extrude(NUB_H) for (k = [0 : 2]) rotate(120 * k) nub2d();
    // the handle: a peg with a rounded knob, on the outer face between two beams
    translate([PEG_AT[0], PEG_AT[1], WHEEL_T - 0.01]) {
        cylinder(r = PEG_R, h = PEG_L - PEG_R + 0.01, $fn = 40);
        translate([0, 0, PEG_L - PEG_R]) cylinder(r1 = PEG_R, r2 = PEG_R * 0.45, h = PEG_R * 0.75, $fn = 40);
    }
}

// ---- axle -----------------------------------------------------------------------------------
// z from the far end. span = the posts' inner faces apart. Returns its landmarks too.
function ax_drum0() = 1.0 + FT;
function ax_drum1(span) = ax_drum0() + span - 2 * COLLAR_G;
function ax_collar0(span) = ax_drum1(span) + COLLAR_G + FT + COLLAR_G;
function ax_collar1(span) = ax_collar0(span) + COLLAR_CONE + COLLAR_FLAT;

module axle(span) {
    d0 = ax_drum0(); d1 = ax_drum1(span); c0 = ax_collar0(span); c1 = ax_collar1(span);
    hex_top = c1 + WHEEL_T + 0.6 + CH;
    difference() {
        union() {
            cylinder(r = R_J, h = c0 + 0.01);     // no bevel at the foot: it faced down at 45 deg
            // the drum: a 37 deg cone up from journal B (its underside faces down), flat above
            translate([0, 0, d0]) cylinder(r1 = R_J, r2 = R_DRUM, h = (R_DRUM - R_J) / tan(37));
            translate([0, 0, d0 + (R_DRUM - R_J) / tan(37) - 0.01]) cylinder(r = R_DRUM, h = d1 - d0 - (R_DRUM - R_J) / tan(37) + 0.01, $fn = 80);
            // the collar the wheel sits on
            translate([0, 0, c0]) cylinder(r1 = R_J, r2 = 4.5, h = COLLAR_CONE);
            translate([0, 0, c0 + COLLAR_CONE - 0.01]) cylinder(r = 4.5, h = COLLAR_FLAT + 0.01);
            // the hex, with a 45 deg lead-in
            hull() {
                translate([0, 0, c1 - 0.01]) linear_extrude(hex_top - CH - c1 + 0.01) hex2d(S_HEX);
                translate([0, 0, hex_top - CH]) linear_extrude(CH) hex2d(S_HEX - 2 * CH);
            }
        }
        // the groove the hub's nubs sit in: from the collar's top to just past the nubs; its
        // far flank rises at 60 deg from horizontal (it faces down as it prints)
        rg = S_HEX / 2 - REACH + PRELOAD;
        z1 = c1 + NUB_H + 0.15;
        rotate_extrude($fn = 96) polygon([[rg, c1], [S_HEX, c1], [S_HEX, z1 + (S_HEX - rg) * tan(FLANK)], [rg, z1]]);
        // the twine's hole across the drum, a third of the way from the crank side: a teardrop,
        // so its roof prints (along the axis, it broke out through the journal's bearing face)
        translate([0, 0, d1 - (d1 - d0) / 3]) rotate([90, 0, 0]) linear_extrude(2 * R_DRUM + 2, center = true)
            hull() { circle(r = TIE_R + 0.1, $fn = 20); translate([0, (TIE_R + 0.1) / sin(37)]) circle(r = 0.01); }
    }
}

// ---- pawl -----------------------------------------------------------------------------------
// Drawn seated: the pivot at P (from the axle centre), the tip in the gap just clockwise of
// the tooth whose locking face is at TIP_A, with 0.2 clearance to the wheel.
TIP_A = 96;
PITCH = 360 / TEETH;
TIP_SEAT = TIP_A - round(TIP_A / PITCH) * PITCH;     // where the nearest face actually is
module pawl2d() {
    a = round(TIP_A / PITCH) * PITCH;          // the locking face the tip sits against
    difference() {
        union() {
            // the body stays clear of the teeth (its underside 17.4 from the axle centre)
            hull() {
                translate(P) circle(r = 4.9, $fn = 48);   // 4.3 left 0.9 by the key slot
                rotate(a - 5.5) translate([WHEEL_R + 2.3, 0]) circle(r = 1.6, $fn = 24);
            }
            // only the tip drops into a gap, its face against the locking face (the body stops
            // short of the tooth's tip: over it, the wheel's clearance cut left a 0.1 sliver)
            hull() {
                rotate(a - 5.5) translate([WHEEL_R + 2.3, 0]) circle(r = 1.6, $fn = 24);
                // the tip stops 0.35 over the root: engagement 1.25 (budget: >= 1.15)
                rotate(a - 0.6) translate([WHEEL_R - TOOTH_H + 0.75, 0]) circle(r = 0.4, $fn = 12);
                rotate(a - 5.0) translate([WHEEL_R - TOOTH_H + 0.75, 0]) circle(r = 0.4, $fn = 12);
            }
        }
        offset(r = 0.2) wheel2d();
        translate(P) circle(r = PIN_R + 0.25, $fn = 32);
        // the key slot: lines up with the T-head only with the pawl lifted 78 deg
        translate(P) rotate(atan2(-P[1] + WHEEL_R, -P[0])) square([HEAD_L + 0.3, HEAD_W + 0.3], center = true);
    }
}
module pawl() linear_extrude(PAWL_T) pawl2d();

// ---- bucket ---------------------------------------------------------------------------------
B_R = 7.5;
B_H = 12;
module bucket() {
    rb = B_R - 0.8;                                      // the foot's radius; B_R at the rim
    difference() {
        union() {
            difference() {
                cylinder(r1 = rb, r2 = B_R, h = B_H, $fn = 64);
                // two hoops, as recessed bands 1.0 tall with 37 deg tops (raised, their lips read
                // as 0.8 mm walls; square-topped, they needed support)
                for (z = [2.4, B_H - 3.4]) let (r = rb + 0.8 * z / B_H)
                    rotate_extrude($fn = 64) polygon([[r - 0.35, z], [r + 2, z], [r + 2, z + 1 + 2.35 / tan(37)],
                                                      [r - 0.35, z + 1]]);
                // (stave grooves were tried: on a 15 mm bucket they hardly show, and every groove
                // edge read as a 0.03 mm wall)
            }
            for (s = [-1, 1]) translate([s * (rb + 1.4), 0, 0]) cylinder(r = 2.2, h = B_H, $fn = 32);   // the ears: 1.4 round the hole
        }
        translate([0, 0, 1.4]) cylinder(r1 = rb - 1.8, r2 = B_R - 1.8, h = B_H, $fn = 64);   // walls 1.8: the
                                                  // bands take 0.35 off them
        for (s = [-1, 1]) translate([s * (rb + 1.4), 0, -1]) cylinder(r = 0.8, h = B_H + 2, $fn = 16);
    }
}

// ---- the test base ----------------------------------------------------------------------------
SPAN_C = 12;             // the coupon's posts, inner faces apart (the well's will be wider; 24 put the
                         // test print at 1 h 16 min)
HC_C = 26;               // the coupon's axle centre above the tenon foot (22 put the wheel's
                         // rim on the base)
BASE_T = TEN_H;
module base(span = SPAN_C) {
    xs = span / 2 + FT / 2;
    difference() {
        union() {
            translate([-xs - 6, -5, 0]) cube([2 * xs + 12, 10, BASE_T]);
            for (s = [-1, 1]) translate([s * xs - 6, -18, 0]) cube([12, 36, BASE_T]);
        }
        for (s = [-1, 1]) translate([s * xs - FT / 2 - 0.15, -TEN_W / 2 - 0.15, -1]) cube([FT + 0.3, TEN_W + 0.3, BASE_T + 2]);
    }
}

// ---- the coupon: everything for one windlass, plus a second far-side post ---------------------
// Posts: crank side 0.55 (the design value); far side 0.40 and 0.70 to try. Scott presses the
// axle into each.
module coupon() {
    translate([0, 0, 0]) post(0.55, HC_C, true);
    translate([30, 0, 0]) post(0.40, HC_C, false);
    translate([52, 0, 0]) post(0.70, HC_C, false);
    translate([80, 22, 0]) axle(SPAN_C);
    translate([-30, 70, 0]) wheel();
    translate([-14, 40, 0]) rotate(0) pawl();
    translate([95, 50, 0]) bucket();
    translate([30, 80, 0]) base();
}

// ---- review: assembled on its base, in use ---------------------------------------------------
module assembled(span = SPAN_C, e_far = 0.55) {
    xs = span / 2 + FT / 2;
    color("tan") base(span);
    // posts stand on the base: plane (u, v) -> (Y, Z); thickness along X
    color("burlywood") translate([span / 2, 0, 0]) rotate([90, 0, 90]) post(0.55, HC_C, true);
    color("burlywood") translate([-span / 2, 0, 0]) mirror([1, 0, 0]) rotate([90, 0, 90]) post(e_far, HC_C, false);
    // axle: print z -> +X, far end at the far post's outer face less 1.0
    color("peru") translate([-span / 2 - FT - 1.0 + COLLAR_G, 0, HC_C]) rotate([0, 90, 0]) rotate(90) axle(span);   // turned so its hex meets the wheel's
    color("sienna") translate([span / 2 + FT + WHEEL_W0, 0, HC_C]) rotate([90, 0, 90]) wheel();
    color("saddlebrown") translate([span / 2 + FT + WHEEL_W0 + 0.2, 0, HC_C]) rotate([90, 0, 90]) pawl();
}

if (part == "coupon") coupon();
else if (part == "posts") { post(0.55, HC_C, true); translate([30, 0, 0]) post(0.40, HC_C, false); translate([52, 0, 0]) post(0.70, HC_C, false); }
else if (part == "post") post(e_sel, HC_C, pawl_sel);
else if (part == "axle") axle(SPAN_C);
else if (part == "wheel") wheel();
else if (part == "pawl") pawl();
else if (part == "bucket") bucket();
else if (part == "base") base();
else if (part == "assembled") assembled();
