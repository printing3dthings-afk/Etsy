// Involute spur gears and the snap post, for the gear heart (2026-11-11).
// The vendored BOSL2 has no gears.scad, so the tooth is drawn here: the standard
// involute construction (pitch radius m z / 2, base radius r cos(pa), addendum m,
// dedendum 1.25 m). Sizes and the reasons for them: gear_budget.py.

GEAR_PA = 20;

function inv(a) = tan(a) - a * PI / 180;                 // involute function, a in degrees
function g_rp(m, z) = m * z / 2;
function g_rb(m, z) = g_rp(m, z) * cos(GEAR_PA);
function g_ra(m, z) = g_rp(m, z) + m;
function g_rf(m, z) = g_rp(m, z) - 1.25 * m;
// a flank's angle from the tooth's centre line at radius r, radians: half the
// tooth's angular thickness there. thin = how much each flank is pared back (mm at
// the pitch circle), on top of the backlash the centre distance gives.
function half_ang(m, z, r, thin) =
    let (rp = g_rp(m, z), rb = g_rb(m, z), a = acos(min(1, rb / max(r, rb))))
    PI / (2 * z) - thin / rp + inv(GEAR_PA) - inv(a);

module gear2d(m, z, thin = 0.05, steps = 8) {
    rb = g_rb(m, z); ra = g_ra(m, z); rf = g_rf(m, z);
    r0 = max(rb, rf);
    flank = [for (i = [0 : steps]) r0 + (ra - r0) * i / steps];
    tooth = concat(
        [for (k = [0 : 3]) let (a = -180 / z + k * (180 / z - half_ang(m, z, r0, thin) * 180 / PI) / 3) [rf * cos(a), rf * sin(a)]],
        [for (r = flank) let (a = -half_ang(m, z, r, thin) * 180 / PI) [r * cos(a), r * sin(a)]],
        [for (j = [steps : -1 : 0]) let (r = flank[j], a = half_ang(m, z, r, thin) * 180 / PI) [r * cos(a), r * sin(a)]],
        [for (k = [1 : 3]) let (a0 = half_ang(m, z, r0, thin) * 180 / PI, a = a0 + k * (180 / z - a0) / 3) [rf * cos(a), rf * sin(a)]]);
    polygon([for (t = [0 : z - 1]) for (p = tooth) let (c = cos(t * 360 / z), s = sin(t * 360 / z)) [p.x * c - p.y * s, p.x * s + p.y * c]]);
}

// A gear as printed: flat, a hub bore, and round lightening holes in the web when
// there's room for a 2 mm web each side.
module gear(m, z, t, bore, holes = 4) difference() {
    linear_extrude(t) gear2d(m, z);
    translate([0, 0, -1]) cylinder(d = bore, h = t + 2, $fn = 48);
    let (r_in = bore / 2 + 2.4, r_out = g_rf(m, z) - 2.0, hd = r_out - r_in)
        if (hd >= 2.4) for (k = [0 : holes - 1]) rotate(k * 360 / holes + 45)
            translate([(r_in + r_out) / 2, 0, -1]) cylinder(d = hd, h = t + 2, $fn = 32);
}

// The snap post, standing on a plate whose top is at z = plate_t: two rectangular
// prongs of constant section, their outer corners on a POST_R circle the gear's hub
// turns on. They rise from a pocket RELIEF deep, so they flex over 13.5 mm, not just
// their height above the plate. A washer ring lifts the gear WASHER off the plate.
// The barb's underside is 37 deg from upright (printable; holds by friction, about
// 14 N to pull off) and its top a 30 deg lead-in. Sizes: gear_budget.py.
//   A round post split by a slot left half-round prongs that tapered to an edge at
// the slot (gate min wall 0.58); drawn straight at 2.0 thick they strained 1.7 %
// going on, over PLA's 1.4. These are 1.6 x 4.0, at 1.19 %.
POST_R = 3.5; PRONG_W = 4.0; PRONG_T = 1.6; BARB = 0.9; BORE_GAP = 0.35;
X_OUT = sqrt(POST_R * POST_R - PRONG_W * PRONG_W / 4);
SLOT = 2 * (X_OUT - PRONG_T);
RELIEF = 6.5; RELIEF_GAP = 0.5; WASHER = 1.0; LEAD = 30;
UNDER = 37;   // the barb's underside, deg from upright: 45 drew 10,330 support moves
// Axial play 0.35, at the bore: the barb's slope reaches the bore's radius that far
// above the gear's top. The stack that could clamp a gear (its thickness, the washer,
// the barb, each +/-0.1) is 0.3 worst case.
AX_PLAY = 0.35;
function bore_d() = 2 * (POST_R + BORE_GAP);
// the two prongs' footprint
module prongs2d(out = X_OUT) for (sx = [-1, 1]) translate([sx > 0 ? SLOT / 2 : -out, -PRONG_W / 2]) square([out - SLOT / 2, PRONG_W]);
module post(plate_t, gear_t) {
    z0 = plate_t - RELIEF;                         // prong root
    rbore = bore_d() / 2;
    zc = plate_t + WASHER + gear_t + AX_PLAY;      // where the slope reaches the bore: the catch
    // The slope starts at the prong's flat face (X_OUT), not the post's circle: from
    // the circle it left a flat ledge 0.6 wide in mid-air where the barb began, and
    // the gate's slicer propped it (6,389 support moves).
    zs = zc - (rbore - X_OUT) / tan(UNDER);
    rb = rbore + BARB;                             // barb's outer radius
    zb = zc + BARB / tan(UNDER);
    zt = zb + (rb - (X_OUT - 0.2)) / tan(LEAD);     // ends 1.4 thick: at X_OUT - 0.4 the tip was 1.2, on the gate's floor
    // the prongs, flat-faced (1.6 thick, as gear_budget.py bends them), up to the
    // barb; the barb itself on a wider footprint, or the prongs' faces clip it off
    intersection() {
        translate([0, 0, z0]) linear_extrude(zs - z0 + 0.01) prongs2d();
        translate([0, 0, z0]) cylinder(r = POST_R, h = zs - z0 + 0.01, $fn = 64);
    }
    intersection() {
        translate([0, 0, zs]) linear_extrude(zt - zs) prongs2d(rb + 1);
        rotate_extrude($fn = 64) polygon([[0, zs], [X_OUT, zs], [rb, zb], [X_OUT - 0.2, zt], [0, zt]]);
    }
}
// what to cut out of the plate round a post: the pocket it rises from
module post_pocket(plate_t) translate([0, 0, plate_t - RELIEF]) cylinder(r = POST_R + RELIEF_GAP, h = RELIEF + 1, $fn = 64);
module washer(plate_t) translate([0, 0, plate_t - 0.01]) difference() {
    cylinder(r = bore_d() / 2 + 2.2, h = WASHER + 0.01, $fn = 64);
    translate([0, 0, -1]) cylinder(r = POST_R + RELIEF_GAP, h = 5, $fn = 64);
}
