// Stacking Jar Tower: the thread test print (2026-11-10).
// Each jar's bottom is a threaded spigot that screws into the mouth of the jar below;
// a 35 deg cone above the spigot seats on a matching countersink in the mouth, which
// stops it and closes the seam. This prints one spigot and three mouths at the real
// 72 mm size, the mouths cut with 0.2, 0.3 and 0.4 mm radial clearance (1, 2 and 3
// notches on their rims). Thread from the gingerbread tin: 4 mm pitch, 1.2 deep,
// flanks 35 deg off vertical, so neither side prints over air.
//   part = "spigot" | "mouth" (with C) | "plate"     the plate is all four, laid out
//   part = "seated" (with C)                        the spigot screwed home, for the check
part = "plate";
C = 0.3;

R_OUT = 36;                 // the jar's outside
TH_P = 4; TH_D = 1.2; TH_A = 35;
TH_R = 33.8;                // the spigot's thread crest; root TH_R - TH_D
TH_H = 7;                   // the spigot's teeth; the top 1.7 run into the seat cone
SP_IN = TH_R - TH_D - 2.0;  // the spigot's bore: 2.0 wall inside the thread root
TA = tan(TH_A);
H_MOUTH = 12;
CS = 1.3;                   // the flat rim left outside the countersink: at 1.0 the rim was 1.0 thick at its top
$fn = 180;

TH_F = TH_D / TA;
TH_FLAT = (TH_P - 2 * TH_F) / 2;
function th_r(R, u) = let (r0 = R - TH_D)
    u < TH_FLAT ? r0 :
    u < TH_FLAT + TH_F ? r0 + TH_D * (u - TH_FLAT) / TH_F :
    u < 2 * TH_FLAT + TH_F ? R :
    R - TH_D * (u - 2 * TH_FLAT - TH_F) / TH_F;
module thread(R, h) linear_extrude(h, twist = -360 * h / TH_P, slices = ceil(h / TH_P * 96), convexity = 4)
    polygon([for (i = [0 : 359]) let (t = i, u = t / 360 * TH_P) th_r(R, u) * [cos(t), sin(t)]]);

// ---- the spigot: teeth from the bed, a lead-in chamfer at their foot, then the seat
// cone flaring out at TH_A to the jar's wall
SEAT_Z = TH_H;                          // where the cone passes the thread's crest radius
CONE_TOP = SEAT_Z + (R_OUT - TH_R) / TA;
module spigot(body = 4) difference() {
    union() {
        intersection() {
            thread(TH_R, TH_H);
            cylinder(h = TH_H, r1 = TH_R - TH_D + 0.01, r2 = TH_R - TH_D + TH_H * TA);   // lead-in at the foot
        }
        rotate_extrude() polygon([[SP_IN, SEAT_Z - TH_D / TA - 0.01], [TH_R - TH_D, SEAT_Z - TH_D / TA],
            [R_OUT, CONE_TOP], [R_OUT, CONE_TOP + body], [SP_IN, CONE_TOP + body]]);
    }
    translate([0, 0, -1]) cylinder(h = 100, r = SP_IN);
}

// ---- a mouth: the jar's top. The thread is cut a whole pitch past where any tooth
// sits; the countersink at the rim is the seat, the same cone as the spigot's but C out
CS_R = R_OUT - CS;                      // the countersink's top edge
CS_DEPTH = (CS_R - (TH_R + C)) / TA;
module mouth(C, notches) difference() {
    cylinder(h = H_MOUTH, r = R_OUT);
    translate([0, 0, -1]) cylinder(h = H_MOUTH + 2, r = TH_R - TH_D + C);           // the crests
    translate([0, 0, H_MOUTH - CS_DEPTH - TH_H - TH_P]) thread(TH_R + C, TH_H + TH_P + 0.01);
    // the countersink runs on down at TH_A to the crests: the spigot's last turn blends
    // into its seat cone, so the mouth's top teeth are cut to the same cone, C out
    translate([0, 0, H_MOUTH - CS_DEPTH - TH_D / TA]) cylinder(h = CS_DEPTH + TH_D / TA + 0.01, r1 = TH_R - TH_D + C, r2 = CS_R);
    // 0.5 deep: at 0.8 they left 1.1 between a notch and the thread's groove (2026-11-10)
    for (k = [1 : notches]) rotate(k * 8) translate([R_OUT, 0, H_MOUTH - 3]) cube([1.0, 1.2, 7], center = true);
}

// seated: the spigot's cone lands on the countersink; its phase follows the thread
function seat_z(C) = H_MOUTH - CS_DEPTH - C / TA - SEAT_Z;
module seated(C) {
    color("lavender") mouth(C, 1);
    z = seat_z(C);
    z0 = H_MOUTH - CS_DEPTH - TH_H - TH_P;
    translate([0, 0, z]) rotate(360 * (z - z0) / TH_P) spigot();
}

if (part == "spigot") spigot();
else if (part == "mouth") mouth(C, C < 0.25 ? 1 : C < 0.35 ? 2 : 3);
else if (part == "seated") seated(C);
else if (part == "plate") {
    spigot();
    for (i = [0 : 2]) translate([[78, 0, 78][i], [0, 78, 78][i], 0]) mouth([0.2, 0.3, 0.4][i], i + 1);
}
echo("SEAT_Z", SEAT_Z, "CONE_TOP", CONE_TOP, "CS_DEPTH", CS_DEPTH, "seat_z", seat_z(C));
