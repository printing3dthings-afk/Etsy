include <BOSL2/std.scad>

body_ctrl = [
    [28, 0], [40, 8], [46, 20], [45, 32], [38, 45], [26, 55], [14, 62], [10, 65],
];
body = smooth_path(body_ctrl, method="corners", size=5, splinesteps=10);

wall = 4;
floor_h = 3;
n_ribs = 10;
rib_depth = 1.8;

function rib_pts(r) = [for (a = [0:5:355])
    let(rr = r - rib_depth * (1 - abs(cos(a * n_ribs / 2))) * (0.82 + 0.18 * sin(a * 2.3 + 11)))
    [rr * cos(a), rr * sin(a)]
];
function circle_pts(r) = [for (a = [0:10:350]) [r * cos(a), r * sin(a)]];

outer_profiles = [for (p = body) rib_pts(p.x)];
outer_z = [for (p = body) p.y];

inner_pts = [for (p = body) if (p.y >= floor_h) [max(p.x - wall, 0.1), p.y]];
inner_profiles = [for (p = inner_pts) circle_pts(p.x)];
inner_z = [for (p = inner_pts) p.y];

// Face cuts v4 -- matched against real classic jack-o-lantern reference
// photos, not guessed. Two real problems fixed from v3:
// 1. The nose had almost no vertical gap to the eyes (apex 31 vs eye base
//    30) -- they visually merged into one oversized triangle. Now each
//    feature has a real multi-mm gap to its neighbor.
// 2. The mouth was 3 separate solid teeth-blocks with big UNCUT gaps
//    between them -- backwards from a real jack-o-lantern, where the
//    mouth is ONE continuous cut cavity and the teeth are small SOLID
//    remnants left uncut within it. Fixed by cutting the whole mouth
//    region, then subtracting two small "keep-solid" rectangles from the
//    cutter itself (nested difference) so those two spots stay material.
y0 = 25; y1 = 50;
module prism_xz(pts2d) {
    hull() {
        for (p = pts2d) {
            translate([p[0], y0, p[1]]) sphere(r=0.01, $fn=6);
            translate([p[0], y1, p[1]]) sphere(r=0.01, $fn=6);
        }
    }
}

eye_pts = [[-11, 0], [11, 0], [0, 12]];
nose_pts = [[-6, 0], [6, 0], [0, 9]];

module mouth_cutter() {
    difference() {
        union() {
            translate([0, 0, 2]) prism_xz([[-30, 0], [30, 0], [30, 11], [-30, 11]]);
            translate([0, 0, 2]) prism_xz([[-30, 0], [-19, 0], [-19, 17], [-30, 17]]);
            translate([0, 0, 2]) prism_xz([[19, 0], [30, 0], [30, 17], [19, 17]]);
        }
        union() {
            translate([0, 0, 2]) prism_xz([[-6, 0], [-1, 0], [-1, 7], [-6, 7]]);
            translate([0, 0, 2]) prism_xz([[1, 0], [6, 0], [6, 7], [1, 7]]);
        }
    }
}

module face_cuts() {
    translate([-16, 0, 32]) prism_xz(eye_pts);
    translate([16, 0, 32]) prism_xz(eye_pts);
    translate([0, 0, 20]) prism_xz(nose_pts);
    mouth_cutter();
}

stem_ctrl = [
    [0, 0], [0, 10], [-1, 18], [-4, 24], [-9, 29], [-15, 32], [-20, 33],
];
stem_path2d = smooth_path(stem_ctrl, method="corners", size=3, splinesteps=8);
stem_path3d = [for (p = stem_path2d) [p.x, 0, p.y]];

n_ridge = 5;
ridge_depth = 1.1;
function ridge_pts(r) = [for (a = [0:15:345])
    let(rr = r - ridge_depth * (1 - abs(cos(a * n_ridge / 2))))
    [rr * cos(a), rr * sin(a)]
];
stem_r0 = 9;

module stem() {
    translate([0, 0, 59])
        path_sweep(ridge_pts(stem_r0), stem_path3d, scale=0.22, twist=30, $fn=32);
}

union() {
    color([0.93, 0.42, 0.08])
        difference() {
            skin(outer_profiles, z=outer_z, slices=0);
            skin(inner_profiles, z=inner_z, slices=0);
            face_cuts();
        }
    color([0.40, 0.28, 0.12])
        stem();
}
