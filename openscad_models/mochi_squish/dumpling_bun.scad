include <BOSL2/std.scad>

// ============================================================
// Dumpling Bun squish (Scott's pick, 2026-11-28: form 1 of 5)
// A palm-size kawaii bao in TPU 95A that squeezes flat and springs back.
// The form is the Dumpling Clicker's bao (../dumpling_clicker.scad: same
// lofted dome, same gathered pleats, same face), scaled up and made SOLID:
// a TPU squish gets its squish from the slicer's walls and sparse infill,
// so the geometry stays one closed body and the feel is set in the profile.
//
//   part = "bun"     the squish, sitting on its flat base
//        | "coupon"  three small buns side by side, 1 / 2 / 3 dots on the base
//                    (each is sliced with its own walls / infill: see README)
// ============================================================

part = "bun";
size = 60;                 // base diameter, mm. Palm size: the clicker's bao is 30.4
coupon_scale = 0.6;        // the coupon's buns, 36 mm across
mark_depth = 0.6;          // the coupon's dots, cut into the bed face

$fa = 2;
$fs = 0.4;

// ---------- the body: the clicker's bao profile, at bun size ----------
// The clicker's silhouette (r 15.2, h 16.6: a squat 1.81:1 dome, Technique 31),
// scaled to `size`. Its pleats and face are NOT just scaled (2026-11-28, first
// render): on the clicker colour carries them, and in one colour of TPU the
// x1.97 copy read as a plain dome with panda patches. Here the folds are
// bolder and swirl up into a pinched knot, as a real bao's do, and the face is
// sized in real millimetres for this bun.
K = size / (2 * 15.20);
bao_ctrl = [[15.20, 0], [15.10, 2.8], [14.70, 6.4], [13.00, 10.0],
            [9.60, 13.2], [5.00, 15.4], [1.20, 16.6]] * K;
H = 16.6 * K;              // 32.8 at 60 mm
bao_prof = smooth_path(bao_ctrl, method="corners", size=2.6 * K, splinesteps=14);

n_pleat = 16;
pleat_amp = 4.0;           // mm, raised outward (never cut in: no wall thinned). 2.6 vanished below the crown, 3.4 faded too early
twist = 45;                // degrees the folds swirl from the belly to the knot
function smooth01(x) = let(t = max(0, min(1, x))) t * t * (3 - 2 * t);
// The folds start 18% up, grow nearly linearly, and fade out again under the knot
// (2026-11-28 gate: at full height they stood past the knot as thin fins, 0.7 mm
// walls and a 1.1 mm unsupported lip at the crown).
function pleat_at(z) = pleat_amp * pow(max(0, min(1, (z / H - 0.18) / 0.82)), 0.9)
                       * (1 - smooth01((z / H - 0.84) / 0.12));
function ring(r, z) = [for (a = [0 : 2 : 358])
    let(t = twist * pow(z / H, 1.4),
        rr = r + pleat_at(z) * pow(0.5 + 0.5 * cos((a - t) * n_pleat), 1.7))
    [rr * cos(a), rr * sin(a)]];
module body() skin([for (p = bao_prof) ring(p.x, p.y)], z = [for (p = bao_prof) p.y], slices = 0);

// the pinched knot at the crown, where the folds gather
knot_r = 5.0;
// Hulled down onto a wider foot inside the body, so its sides only ever taper
// inward going up: as a plain squashed sphere its underside overhung the crown
// by 1.9 mm (2026-11-28 gate: a 2.6 mm unsupported span at z 32).
module knot() hull() {
    translate([0, 0, H - 1.6]) scale([1, 1, 0.75]) sphere(r = knot_r);
    translate([0, 0, H - 7]) cylinder(r = knot_r + 2, h = 0.1);
}

function r_at(z) =
    let(i = [for (k = [0 : len(bao_prof) - 2]) if (bao_prof[k].y <= z && bao_prof[k + 1].y >= z) k])
    len(i) == 0 ? bao_prof[0].x
    : let(a = bao_prof[i[0]], b = bao_prof[i[0] + 1], t = (z - a.y) / max(b.y - a.y, 1e-6))
      a.x + t * (b.x - a.x);
// a point `out` mm outside the smooth surface (negative: inside), at azimuth az (0 = facing -Y)
function on_face(az, z, out) = let(r = r_at(z) + out) [r * sin(az), -r * cos(az), z];

// ---------- the face, in mm at bun size (dimples: one colour of TPU) ----------
// Depth ordered on purpose, as on the clicker: eyes deepest (2.1), smile 0.9,
// blush a 0.6 dish. Every width is at least 1.8 mm, over four extrusions.
eye_z = 0.50 * H;
// Every dimple is "hooded": its cutter is hulled with a copy moved out and up
// at 56 degrees, so each ceiling rises toward the opening and prints without
// support. As plain spheres, the eyes' and smile's ceilings drew 1,193 support
// moves from the bed up to z 18 (2026-11-28 gate, read off the support toolpath).
function out_dir(az) = [sin(az), -cos(az), 0];
// up 1.5 for every 1 out (56 degrees): at exactly 45 the smile still drew support moves
module hooded(az, d) hull() { children(); translate(out_dir(az) * d + [0, 0, 1.5 * d]) children(); }
module face_cut() {
    for (s = [-1, 1]) hooded(s * 15, 3.0) translate(on_face(s * 15, eye_z, 0.4)) scale([1, 1, 1.25]) sphere(r = 2.5);
    smile = [for (i = [-3 : 3]) on_face(i * 3.2, eye_z - 5.6 + 0.17 * i * i, 0)];
    for (k = [0 : len(smile) - 2]) hooded(k * 3.2 - 8, 1.2) hull() {
        translate(smile[k]) sphere(r = 0.9); translate(smile[k + 1]) sphere(r = 0.9); }
    // the blush is a 0.6 mm dish, but where it crosses a raised fold it left a
    // ceiling (the left one, 359 support moves at 4 mm folds), so it's hooded too
    for (s = [-1, 1]) hooded(s * 29, 1.0) translate(on_face(s * 29, eye_z - 3.6, 3.4))
        rotate([0, 0, s * 29]) scale([1.4, 1, 0.9]) sphere(r = 4.0);
}

module bun(k = 1) scale(k) difference() { union() { body(); knot(); } face_cut(); }

// n dots in the bed face, so each coupon bun says which setting it was sliced with
module marks(n, k) for (i = [0 : n - 1])
    translate([(i - (n - 1) / 2) * 5, 0, -0.01]) cylinder(r = 1.4, h = mark_depth + 0.01, $fn = 32);

echo(BUN = [size, H], COUPON = [size * coupon_scale, H * coupon_scale]);

if (part == "bun") bun();
else if (part == "coupon")
    for (n = [1 : 3]) translate([(n - 2) * (size * coupon_scale + 8), 0, 0])
        difference() { bun(coupon_scale); marks(n, coupon_scale); }
else if (part == "coupon_1" || part == "coupon_2" || part == "coupon_3")
    let(n = part == "coupon_1" ? 1 : part == "coupon_2" ? 2 : 3)
        difference() { bun(coupon_scale); marks(n, coupon_scale); }
