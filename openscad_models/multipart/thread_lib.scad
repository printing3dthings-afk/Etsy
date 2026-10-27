// Printed threads for the multipart line (2026-10-27). The vendored BOSL2 is
// a subset without threading.scad, so a thread is built here directly: a
// cylinder whose surface radius at each angle and height follows the thread's
// profile along a helix, written out as one closed polyhedron.
//
// The profile is a trapezoid whose flanks rise THREAD_FLANK times their
// depth: 39 deg off vertical, so on an upright part no flank of the screw or
// the nut needs support. Exactly 45 deg is not enough: Bambu Studio puts
// support under a 45 deg thread (sliced 2026-10-27, 3849 support moves on the
// first screw). ISO and ACME flanks hang at 60 and 75 deg. The flanks take
// 2 x THREAD_FLANK x depth of each pitch, so depth must stay under
// pitch / (2 x THREAD_FLANK).
//
// thread_solid(d, pitch, len, depth, clear) is the screw's solid: d its major
// (outside) diameter, depth the tooth's height. A nut is a cylinder minus
// thread_solid(..., clear = c): the same thread grown c all round.

THREAD_FN = 96;     // facets round
THREAD_ZN = 16;     // rows a pitch
THREAD_FLANK = 1.25;

// the tooth's height over the root at phase u (0..1 of a pitch): a flank up,
// the crest, a flank down, the root
function thread_f(u, pitch, depth) = let (fl = THREAD_FLANK * depth / pitch, rest = (1 - 2 * fl) / 2, v = u - floor(u))
    v < rest ? 0 : v < rest + fl ? (v - rest) / fl : v < 2 * rest + fl ? 1 : v < 2 * rest + 2 * fl ? 1 - (v - 2 * rest - fl) / fl : 0;
function thread_r(a, z, d, pitch, depth, clear) = d / 2 - depth + clear + depth * thread_f(z / pitch - a / 360, pitch, depth);

module thread_solid(d, pitch, len, depth, clear = 0) {
    n = THREAD_FN; m = ceil(len / pitch * THREAD_ZN);
    pts = concat(
        [for (k = [0 : m], j = [0 : n - 1]) let (a = 360 * j / n, z = len * k / m, r = thread_r(a, z, d, pitch, depth, clear))
            [r * cos(a), r * sin(a), z]],
        [[0, 0, 0], [0, 0, len]]);
    p = function (k, j) k * n + (j % n);
    b = (m + 1) * n; t = b + 1;
    faces = concat(
        [for (k = [0 : m - 1], j = [0 : n - 1]) each [[p(k, j), p(k + 1, j), p(k + 1, j + 1)], [p(k, j), p(k + 1, j + 1), p(k, j + 1)]]],
        [for (j = [0 : n - 1]) [b, p(0, j), p(0, j + 1)]],
        [for (j = [0 : n - 1]) [t, p(m, j + 1), p(m, j)]]);
    polyhedron(pts, faces, convexity = 6);
}

// a lead-in on both ends: the thread cut back to its root by a cone at the
// flanks' angle, so it starts clean instead of on a sharp tooth
module thread_chamfer(d, len, depth) let (h = 2 * len + depth) intersection() {
    children();
    cylinder(d1 = d - 2 * depth, d2 = d - 2 * depth + 2 * h / THREAD_FLANK, h = h, $fn = THREAD_FN);
    translate([0, 0, len]) mirror([0, 0, 1])
        cylinder(d1 = d - 2 * depth, d2 = d - 2 * depth + 2 * h / THREAD_FLANK, h = h, $fn = THREAD_FN);
}
