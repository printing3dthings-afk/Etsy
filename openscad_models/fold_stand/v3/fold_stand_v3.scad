// Fold Stand v3: an easel. Three flat parts, no pins, nothing that bends (2026-11-10).
// The numbers are in stand_v3_calc.py and ENGINEERING_v3.md; NOTCH_Y is pasted from
// `python3 stand_v3_calc.py --scad`. World frame for the base and the poses: y runs back
// from the pivot, z up, x across.
//   part = "base" | "plate" | "prop"            the prints, as they lie on the bed
//   part = "coupon_base" | "coupon_plate"       the joint test: the same joints, narrow and short
//   part = "pose"  angle = 55..80               all three parts assembled (for checks)
part = "pose";
angle = 70;
W = 76;                 // overall width
COUPON = (part == "coupon_base" || part == "coupon_plate");
WW = COUPON ? 30 : W;   // the width actually built

// ---- from stand_v3_calc.py ----
ANGLES = [80, 75, 70, 65, 60, 55];
NOTCH_Y = [27.19, 38.28, 49.05, 59.43, 69.36, 78.76];
PIVOT_Z = 7;            // tongue axis above the table
TONGUE_R = 3;
PLATE_T = 5;            // back face 3 behind the pivot line, front face 2 in front
PLATE_L = COUPON ? 72 : 120;
A_SOCKET = 65;          // nose centre along the plate
NOSE_R = 2;
NOSE_IN = 0.6;          // nose centre inside the back face
PROP_L = 66;
FOOT_R = 3;
NOTCH_Z = 6;
BASE_T = 4;
BASE_FRONT = COUPON ? 10 : 45;
BASE_BACK = COUPON ? 88 : 120;

// ---- clearances: 0.4 everywhere something moves (process minimum open gap 0.3) ----
CL = 0.4;
GROOVE_R = TONGUE_R + 0.7;  // 0.7, not 0.4: the tongue's teardrop underside (it prints on it)
                             // stands 0.38 outside its circle
TROUGH_R = FOOT_R + CL;
PROP_W = 20;
SLOT_W = PROP_W + 2 * CL;

// ---- the phone shelf ----
SHELF_U = 10;           // the phone's bottom edge rests here
SHELF_H = 6;            // shelf thickness along the plate
CASE_MAX = 13;          // deepest phone + case the shelf takes
CHIN_H = 3;             // the chin leans out over the phone's front edge by this, 35 deg off vertical
CHIN_RISE = CHIN_H / tan(35);
CHIN_T = 1.6;           // the chin's thickness at its top
CABLE_W = 16;           // cable gap through the shelf

$fn = 72;

// =========================== base ===========================
module rounded_slab(x0, x1, y0, y1, h, r) {
    hull() for (x = [x0 + r, x1 - r], y = [y0 + r, y1 - r]) translate([x, y, 0]) cylinder(r = r, h = h);
}

module xbar(prof) {       // a 2D (y, z) profile, extruded across x (width ww)
    rotate([90, 0, 90]) linear_extrude(height = 1, center = true) polygon(prof);
}

function nose_at(th) = [A_SOCKET * cos(th) + (TONGUE_R - NOSE_IN) * sin(th),
                        PIVOT_Z + A_SOCKET * sin(th) - (TONGUE_R - NOSE_IN) * cos(th)];

module base() {
    difference() {
        union() {
            rounded_slab(-WW / 2, WW / 2, -BASE_FRONT, BASE_BACK, BASE_T, COUPON ? 3 : 8);
            // pivot block: the front wall stands to the tongue's axis, the rear rim stops
            // at 45 deg below it so the plate's back clears down to 55 deg
            rr = GROOVE_R * cos(45);
            scale([WW, 1, 1]) xbar([[-7.5, BASE_T - 0.01], [-7.5, PIVOT_Z - 0.8], [-6.7, PIVOT_Z],
                                    [0, PIVOT_Z], [0, PIVOT_Z - rr], [8, PIVOT_Z - rr], [9, BASE_T - 0.01]]);
            // the notch bar
            scale([min(WW, PROP_W + 20), 1, 1])
                xbar([[NOTCH_Y[0] - 7, BASE_T - 0.01], [NOTCH_Y[0] - 5.5, NOTCH_Z],
                      [NOTCH_Y[5] + 5.5, NOTCH_Z], [NOTCH_Y[5] + 7, BASE_T - 0.01]]);
        }
        translate([0, 0, PIVOT_Z]) rotate([0, 90, 0]) cylinder(r = GROOVE_R, h = WW + 2, center = true, $fn = 120);
        for (y = NOTCH_Y) translate([0, y, NOTCH_Z]) rotate([0, 90, 0]) cylinder(r = TROUGH_R, h = SLOT_W, center = true, $fn = 96);
        // ... and the prop's own path out of each notch, CL clear: its side leaves the foot
        // tangentially, so it passes closer to the trough's front rim than the foot does
        for (i = [0 : 5]) let (th = ANGLES[i], fy = NOTCH_Y[i], n = nose_at(th))
            translate([0, fy, NOTCH_Z]) rotate([atan2(n[1] - NOTCH_Z, n[0] - fy), 0, 0]) rotate([90, 0, 90])
                linear_extrude(height = SLOT_W, center = true) offset(r = CL) prop_profile();
        // angle marks beside each notch: one dot for the steepest, then two... (0.6 deep)
        // the coupon saves time with a window between the pivot and the notches
        if (COUPON) translate([-WW / 2 + 4, 10, -1]) cube([WW - 8, NOTCH_Y[0] - 19, BASE_T + 2]);
        if (!COUPON) for (i = [0 : 5]) for (k = [0 : i])
            translate([PROP_W / 2 + 11 + k * 2.8, NOTCH_Y[i], BASE_T - 0.6]) cylinder(d = 2.0, h = 1, $fn = 24);
    }
}

// =========================== plate ===========================
// Print frame: x across, y along the plate (0 at the tongue's axis), z out of the back face.
module plate() {
    difference() {
        union() {
            hull() {
                translate([0, PLATE_L / 2, 0]) rounded_slab(-WW / 2, WW / 2, 0, PLATE_L / 2, PLATE_T, COUPON ? 3 : 8);
                translate([-WW / 2, 0, 0]) cube([WW, 1, PLATE_T]);
            }
            // the tongue: round where it bears (within 10 deg of its end at every angle),
            // a teardrop underneath, 35 deg off vertical, where it meets the bed (the
            // slicer wants support under 45)
            rotate([90, 0, 90]) linear_extrude(height = WW, center = true) hull() {
                translate([0, TONGUE_R]) circle(r = TONGUE_R, $fn = 96);
                d = TONGUE_R * cos(35) - TONGUE_R * (1 - sin(35)) * tan(35);
                translate([-d, 0]) square([2 * d, 0.01]);
            }
            // the shelf and its chin; the phone's back lies on the front face (z = PLATE_T)
            // (y, z) profile: the shelf face at y = SHELF_U up to the deepest case, then the
            // chin leans out at 45 deg so it prints without support
            scale([WW, 1, 1]) xbar([[SHELF_U - SHELF_H, PLATE_T - 0.01], [SHELF_U, PLATE_T - 0.01],
                [SHELF_U, PLATE_T + CASE_MAX], [SHELF_U + CHIN_H, PLATE_T + CASE_MAX + CHIN_RISE],
                [SHELF_U + CHIN_H, PLATE_T + CASE_MAX + CHIN_RISE + CHIN_T], [SHELF_U - SHELF_H, PLATE_T + CASE_MAX + CHIN_RISE + CHIN_T]]);
        }
        if (COUPON) translate([-WW / 2 + 4, 22, -1]) cube([WW - 8, A_SOCKET - 12 - 22, PLATE_T + 2]);
        translate([-CABLE_W / 2, SHELF_U - SHELF_H - 1, PLATE_T]) cube([CABLE_W, SHELF_H + CHIN_H + 2, CASE_MAX + CHIN_RISE + CHIN_T + 1]);
        // the socket: the nose sits in the pocket's top corner (ceiling and upper wall);
        // the lower end ramps out at 35 deg off vertical (it prints on the bed face) and clears the prop
        // at 80 deg, where it lies 22 deg off the plate
        D = NOSE_IN + NOSE_R;
        top = A_SOCKET + NOSE_R;
        rotate([90, 0, 90]) linear_extrude(height = SLOT_W, center = true)
            polygon([[A_SOCKET - 8.6, -1], [A_SOCKET - 8.6, 0], [A_SOCKET - 8.6 + D * tan(35), D], [top, D], [top, -1]]);
    }
}

// =========================== prop ===========================
// Print frame: lies on its side; its profile in XY, 20 tall. Foot at the origin, nose on +x.
module prop_profile() {
    hull() {
        circle(r = FOOT_R, $fn = 96);
        translate([PROP_L, 0]) circle(r = NOSE_R, $fn = 96);
    }
}
module prop() { linear_extrude(height = PROP_W) prop_profile(); }

// =========================== poses ===========================
function foot_y(th) = NOTCH_Y[search(th, ANGLES)[0]];
module pose(th) {
    ny = nose_at(th)[0];
    nz = nose_at(th)[1];
    fy = foot_y(th);
    color("white") base();
    // plate: print frame -> world. Its y (along the plate) goes to (cos, sin) and its z
    // (back face -> front face) to the front normal (-sin, cos): a turn about x by th.
    color("plum") translate([0, 0, PIVOT_Z]) rotate([th, 0, 0]) translate([0, 0, -TONGUE_R]) plate();
    // prop: profile x (foot -> nose) goes from (fy, NOTCH_Z) toward the nose
    pa = atan2(nz - NOTCH_Z, ny - fy);
    color("pink") translate([0, fy, NOTCH_Z]) rotate([pa, 0, 0]) rotate([90, 0, 90]) translate([0, 0, -PROP_W / 2]) prop();
}

if (part == "base" || part == "coupon_base") base();
else if (part == "plate" || part == "coupon_plate") plate();
else if (part == "prop") prop();
else if (part == "pose") pose(angle);
echo("NOTCH_Y", NOTCH_Y, "BASE", -BASE_FRONT, BASE_BACK, "WW", WW);
