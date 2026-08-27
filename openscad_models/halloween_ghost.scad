include <BOSL2/std.scad>

// Kawaii ghost v11 -- rebuilt as a genuinely hollow lantern shell after
// researching what actually separates top-tier Halloween lithophane/lantern
// designs from a solid decorative shape: real ones are hollow with an open
// base for a tealight/LED, and the eyes are true through-cuts so they
// actually glow -- not shallow surface dimples. The prior version (v9) was
// completely solid with 2mm eye dimples; this fixes both, following the
// exact same outer-minus-inner hollowing pattern already proven on the
// pumpkin (Technique 5): the inner shell uses a FLAT offset from the base
// silhouette radius (not the rippled outer radius), so wall thickness never
// varies with local fold depth and can't go thin at a fold valley.
body_ctrl = [
    [24, 0], [26, 4], [27, 20], [26, 40], [22, 52], [14, 62], [0.5, 68],
];
body = smooth_path(body_ctrl, method="corners", size=5, splinesteps=12);

n_legs = 6;
n_folds = n_legs;
fold_depth_max = 1.1;
fold_depth_min = 0.1;
function fold_depth(z) = fold_depth_min + (fold_depth_max - fold_depth_min) * max(0, min(1, 1 - z / 48));

function fold_pts(r, z) = [for (a = [0:3:359])
    let(
        d = fold_depth(z),
        rr = r - d * (0.5 + 0.5 * cos(n_folds * a)) * (0.85 + 0.15 * sin(a * 1.3 + 2))
    )
    [rr * cos(a), rr * sin(a)]
];
function circle_pts(r) = [for (a = [0:6:354]) [r * cos(a), r * sin(a)]];

wall = 3;
outer_profiles = [for (p = body) fold_pts(p.x, p.y)];
outer_z = [for (p = body) p.y];
inner_profiles = [for (p = body) circle_pts(max(p.x - wall, 0.1))];
inner_z = [for (p = body) p.y];

module shell() {
    difference() {
        skin(outer_profiles, z = outer_z, slices = 0);
        skin(inner_profiles, z = inner_z, slices = 0);
    }
}

scallop_r = 12.5;
module scallop_cutters() {
    for (i = [0:n_legs-1]) {
        a = i * 360 / n_legs;
        translate([17 * cos(a), 17 * sin(a), 3])
            sphere(r = scallop_r, $fn = 40);
    }
}

// Eyes are now TRUE through-cuts (light passes through to glow, matching
// what the reference photo actually showed) via the proven hull()-of-two-
// Y-depths prism technique -- y0/y1 span well past both the new inner
// cavity (~23mm radius here) and the outer surface (~26-27mm).
eye_z = 46;
y0 = 15; y1 = 34;
module prism_xz(pts2d) {
    hull() {
        for (p = pts2d) {
            translate([p[0], y0, p[1]]) sphere(r = 0.01, $fn = 6);
            translate([p[0], y1, p[1]]) sphere(r = 0.01, $fn = 6);
        }
    }
}
eye_pts = [for (a = [0:30:359]) [5.5 * cos(a), 8 * sin(a)]];  // true oval
module face() {
    translate([-8, 0, eye_z]) prism_xz(eye_pts);
    translate([8, 0, eye_z]) prism_xz(eye_pts);
}

color([0.85, 0.85, 0.9])
    rotate([12, 0, 180])
        difference() {
            shell();
            scallop_cutters();
            face();
        }
