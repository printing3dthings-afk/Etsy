// Fold Stand v4: v3's easel, as one folding object (2026-11-10).
// Scott tested v3's coupon: "It's good, but it needs to be 3 pieces that connect and stay
// together. I want people to be able to fold it down and store it." He chose the prop
// folding flush into the plate. Numbers in stand_v4_calc.py and ENGINEERING_v4.md.
//
//   base   prints flat. Two lugs hold the plate's pivot pins in bores whose slots rise
//          straight up, 3.6 wide; the pins (round 6) have flats 3.0 apart, tilted 35 deg
//          on the plate, so they pass only with the plate tipped to 145 deg: a twist-lock
//          that never lines up from folded (0) to the steepest notch (80).
//   plate  prints on its back WITH the prop in it: print-in-place. The prop lies in a
//          slot through the plate, hinged on two cones from the slot's walls into sockets
//          in its sides, 0.45 clear. It swings out behind the plate and folds back flush.
//
//   part = "base" | "plate" (plate + prop, one print) | "plate_only" | "prop_only"
//        | "coupon_base" | "coupon_plate"       the hinge test print: both joints, short
//        | "pose" (angle 55..80, or 0 folded)   assembled, for checks
part = "pose";
angle = 70;
COUPON = (part == "coupon_base" || part == "coupon_plate");

// ---- from stand_v4_calc.py ----
ANGLES = [80, 75, 70, 65, 60, 55];
NOTCH_Y = [19.52, 30.13, 40.51, 50.58, 60.29, 69.54];
PIVOT_Z = 10;
PIVOT_IN = 3.0;         // the pivot axis above the plate's back face (its print)
HINGE_IN = 4.0;         // the prop's hinge axis above it
A = COUPON ? 14 : 61;   // the prop's hinge along the plate
L = COUPON ? 22 : 65;   // hinge to foot, along the plate (the foot sits 1 lower)
W = COUPON ? 34 : 76;   // plate width
PLATE_T = 8;
PLATE_L = COUPON ? 44 : 135;
NOTCH_Z = 6;
BASE_T = 4;
BASE_FRONT = COUPON ? 8.5 : 8.5;   // just past the lugs: tipped to 145 to go on, the shelf passes in front of it
BASE_BACK = COUPON ? 22 : 140;

// ---- the pivot twist-lock ----
PIN_R = 3;              // round
PIN_FLAT = 3.0;         // across its flats
PSI = 35;               // the flats' tilt on the plate: the lower one prints at 35 deg
PIN_LEN = 4.5;          // out from the plate's side edge
LUG_GAP = 0.5;          // plate edge to lug
LUG_T = 5;
PIN_REACH = 3.38;       // the pin's flank corner (see pivot_pin)
BORE_R = PIN_REACH + 0.35;
LSLOT = PIN_FLAT + 0.6; // 3.6
PASS = 180 - PSI;       // the one plate angle at which the pins pass the slots: 145
LUG_TOP = PIVOT_Z + 7;
END_U = -3.5;           // the plate's bottom end

// ---- the prop and its print-in-place hinge ----
PROP_W = 20;
SLOT_W = PROP_W + 0.8;
R_HINGE = 4;            // the prop's hinge end
R_FOOT = 3;
CONE_R = 2.0;           // the cones on the slot's walls
CONE_A = 50;            // half-angle: the underside is 40 deg off vertical as it prints
CONE_GAP = 0.45;        // normal gap to the socket
SLOT_BELOW = COUPON ? 12 : 26;   // the slot's end below the hinge, from the hinge axis
FOOT_END = 3.5;         // the slot's end past the foot

// ---- clearances, notches ----
TROUGH_R = R_FOOT + 0.7;  // the foot's teardrop corners stand 0.37 out: 0.33 left
TD = 35;                  // teardrop flanks, off vertical

// ---- the phone shelf (as v3) ----
SHELF_U = 10; SHELF_H = 6; CASE_MAX = 13; CHIN_H = 3; CHIN_RISE = CHIN_H / tan(35); CHIN_T = 1.6;
CABLE_W = 16;
$fn = 72;

module rounded_slab(x0, x1, y0, y1, h, r) {
    hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y, 0]) cylinder(r = r, h = h);
}
module xbar(prof) rotate([90, 0, 90]) linear_extrude(height = 1, center = true) polygon(prof);
module yz(h) rotate([90, 0, 90]) linear_extrude(height = h, center = true) children();   // 2D (y, z), along x

// a circle whose underside is a teardrop down to the bed (z >= 0)
module teardrop2(r, cy, cz) intersection() {
    hull() { translate([cy, cz]) circle(r = r, $fn = 96); translate([cy, cz - r / sin(TD)]) square(0.01, center = true); }
    translate([-1000, 0]) square(2000);
}

// =========================== plate ===========================
// print frame: x across, y along the plate (0 at the pivot axis), z up from the back face
// The pivot pin, 2D in (y, z): round 6, flats 3.0 apart whose normal is PSI above +y.
// Its lowest point is the lower flat's corner (at -85 deg) on the bed; from there to the
// circle at -35 deg its underside would overhang up to 85 deg, so a straight flank at 35
// deg takes it (to 3.38 from the axis: PIN_REACH).
module pivot_pin() translate([0, PIVOT_IN]) intersection() {
    union() {
        circle(r = PIN_R, $fn = 96);
        polygon([[PIN_R * cos(-85), PIN_R * sin(-85)], [PIN_R * cos(-35) - (PIN_R * sin(-35) - PIN_R * sin(-85)) / tan(55), PIN_R * sin(-85)],
                 [PIN_R * cos(-35), PIN_R * sin(-35)], [0, 0]]);
    }
    rotate(PSI + 90) square([40, PIN_FLAT], center = true);
}
module plate_only() {
    difference() {
        union() {
            hull() {
                translate([0, PLATE_L / 2, 0]) rounded_slab(-W / 2, W / 2, 0, PLATE_L / 2, PLATE_T, COUPON ? 3 : 8);
                translate([-W / 2, END_U, 0]) cube([W, 1, PLATE_T]);
            }
            for (s = [-1, 1]) translate([s * (W / 2 + PIN_LEN / 2 - 0.5), 0, 0]) yz(PIN_LEN + 1) pivot_pin();
            if (!COUPON) scale([W, 1, 1]) xbar([[SHELF_U - SHELF_H, PLATE_T - 0.01], [SHELF_U, PLATE_T - 0.01],
                [SHELF_U, PLATE_T + CASE_MAX], [SHELF_U + CHIN_H, PLATE_T + CASE_MAX + CHIN_RISE],
                [SHELF_U + CHIN_H, PLATE_T + CASE_MAX + CHIN_RISE + CHIN_T], [SHELF_U - SHELF_H, PLATE_T + CASE_MAX + CHIN_RISE + CHIN_T]]);
        }
        if (!COUPON) translate([-CABLE_W / 2, SHELF_U - SHELF_H - 1, PLATE_T]) cube([CABLE_W, SHELF_H + CHIN_H + 2, CASE_MAX + CHIN_RISE + CHIN_T + 1]);
        // a 2 mm chamfer on the bottom end's front edge (the top edge as it prints): tipped
        // to 145 to go on, that corner dipped 0.1 into the base's floor
        translate([0, END_U, PLATE_T]) rotate([45, 0, 0]) cube([W + 20, 2.83, 2.83], center = true);
        // the prop's slot, right through. Below the hinge it runs on SLOT_BELOW: the hinge
        // is inside the plate's thickness, so at the steepest notch (the prop ~20 deg off
        // the plate) the prop's top side passes through the plate down to there
        translate([-SLOT_W / 2, A - SLOT_BELOW, -1]) cube([SLOT_W, SLOT_BELOW + L + FOOT_END, PLATE_T + 2]);
    }
    // the cones, from the slot's walls inward
    for (s = [-1, 1]) translate([s * SLOT_W / 2, A, HINGE_IN]) rotate([0, -s * 90, 0])
        cylinder(h = CONE_R / tan(CONE_A), r1 = CONE_R, r2 = 0, $fn = 64);
}

// the prop, folded in its slot (as it prints)
module prop_only() difference() {
    yz(PROP_W) hull() { teardrop2(R_HINGE, A, HINGE_IN); teardrop2(R_FOOT, A + L, R_FOOT); }
    // the sockets: the cones grown so their faces stand CONE_GAP off
    dr = CONE_GAP / cos(CONE_A);
    for (s = [-1, 1]) translate([s * SLOT_W / 2, A, HINGE_IN]) rotate([0, -s * 90, 0])
        translate([0, 0, -1]) cylinder(h = (CONE_R + dr) / tan(CONE_A) + 1, r1 = CONE_R + dr + tan(CONE_A), r2 = 0, $fn = 64);
}

// =========================== base ===========================
function hinge_at(th) = [A * cos(th) - (HINGE_IN - PIVOT_IN) * sin(th), PIVOT_Z + A * sin(th) + (HINGE_IN - PIVOT_IN) * cos(th)];
FOOT_D = sqrt(L * L + (HINGE_IN - R_FOOT) * (HINGE_IN - R_FOOT));

// in (y, z): the bore, the slot straight up, and 35 deg teardrop flanks from the bore to
// the slot's walls, so every surface prints with no support. The slot is the one way out.
// (Leaning the slot instead left the bore's roof printing over air: 1,907 support moves.)
module lug_cut() translate([0, PIVOT_Z]) {
    circle(r = BORE_R, $fn = 96);
    translate([-LSLOT / 2, 0]) square([LSLOT, 30]);
    for (s = [-1, 1]) let (tx = s * BORE_R * cos(35), tz = BORE_R * sin(35), up = (abs(tx) - LSLOT / 2) / tan(35))
        polygon([[0, 0], [tx, tz], [s * LSLOT / 2, tz + up], [0, tz + up]]);
}
module base() {
    BW = W + 2 * (LUG_GAP + LUG_T);
    difference() {
        union() {
            rounded_slab(-BW / 2, BW / 2, -BASE_FRONT, BASE_BACK, BASE_T, COUPON ? 3 : 8);
            for (s = [-1, 1]) translate([s * (W / 2 + LUG_GAP + LUG_T / 2), 0, 0]) yz(LUG_T)
                polygon([[-8, BASE_T - 0.01], [8, BASE_T - 0.01], [8, LUG_TOP - 3], [5, LUG_TOP], [-5, LUG_TOP], [-8, LUG_TOP - 3]]);
            if (!COUPON) {
                scale([PROP_W + 20, 1, 1]) xbar([[NOTCH_Y[0] - 7, BASE_T - 0.01], [NOTCH_Y[0] - 5.5, NOTCH_Z],
                    [NOTCH_Y[5] + 5.5, NOTCH_Z], [NOTCH_Y[5] + 7, BASE_T - 0.01]]);
                // a pad the folded plate lies on, near its far end
                translate([0, BASE_BACK - 14, 0]) scale([W - 10, 1, 1]) xbar([[-6, BASE_T - 0.01], [-4, PIVOT_Z - PIVOT_IN - 0.3],
                    [4, PIVOT_Z - PIVOT_IN - 0.3], [6, BASE_T - 0.01]]);
            }
        }
        for (s = [-1, 1]) translate([s * (W / 2 + LUG_GAP + LUG_T / 2), 0, 0]) yz(LUG_T + 2) lug_cut();
        if (!COUPON) {
            for (y = NOTCH_Y) translate([0, y, NOTCH_Z]) rotate([0, 90, 0]) cylinder(r = TROUGH_R, h = SLOT_W, center = true, $fn = 96);
            for (i = [0 : 5]) let (th = ANGLES[i], fy = NOTCH_Y[i], h = hinge_at(th))
                translate([0, fy, NOTCH_Z]) rotate([atan2(h[1] - NOTCH_Z, h[0] - fy), 0, 0]) rotate([90, 0, 90])
                    linear_extrude(height = SLOT_W, center = true) offset(r = 0.4) hull() { circle(r = R_FOOT + 0.4); translate([FOOT_D, 0]) circle(r = R_HINGE); }
            for (i = [0 : 5]) for (k = [0 : i])
                translate([PROP_W / 2 + 11 + k * 2.8, NOTCH_Y[i], BASE_T - 0.6]) cylinder(d = 2.0, h = 1, $fn = 24);
        }
    }
}

// =========================== poses ===========================
// the plate: its print frame turned about x by th, its pivot axis onto the lugs' bores
module plate_pose(th) translate([0, 0, PIVOT_Z]) rotate([th, 0, 0]) translate([0, 0, -PIVOT_IN]) children();
// the prop turned about its hinge by rho (in the plate's frame; negative swings it out behind)
function prop_rho(th, fy) = let (h = hinge_at(th), toward = atan2(NOTCH_Z - h[1], fy - h[0]) - th,
                                 folded = atan2(R_FOOT - HINGE_IN, L)) toward - folded;
module prop_pose(rho) translate([0, A, HINGE_IN]) rotate([rho, 0, 0]) translate([0, -A, -HINGE_IN]) prop_only();

if (part == "base" || part == "coupon_base") base();
else if (part == "plate" || part == "coupon_plate") { plate_only(); prop_only(); }
else if (part == "plate_only") plate_only();
else if (part == "prop_only") prop_only();
else if (part == "pose") {
    color("white") base();
    plate_pose(angle) { color("plum") plate_only();
        color("pink") if (angle == 0) prop_only(); else prop_pose(prop_rho(angle, NOTCH_Y[search(angle, ANGLES)[0]])); }
}
echo("NOTCH_Y", NOTCH_Y, "FOOT_D", FOOT_D, "W", W);
