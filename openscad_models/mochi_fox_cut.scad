// Mochi Fox -- the CUT half of the hybrid. Blender built the organic shell and
// MEASURED its real surface; CGAL does the booleans, because that is the half
// Blender is documented to be unreliable at and proved to be here.
//
// Every y below is a raycast measurement off the finished shell, not an
// estimate. That matters: mochi_fox_organizer.scad records three failed
// attempts to place ONE eye recess by estimating a hull-chain's surface from
// its control points. The scan also CORRECTED v2's own numbers -- at (x=13,
// z=62) v2 cut a cheek, but on this shell z=62 is 15mm back, on the chest; the
// head surface at x=13 does not start until z=64. A guess cannot tell you that
// and a measurement cannot fail to.
//
//   x=0   nose tip   z50-54 -> y 52.3     x=9   eye line  z73 -> y 37.1
//   x=5   whiskers   z54-58 -> y 42-44    x=13  cheek     z68 -> y 32.7
shell = "openscad_models/mochi_fox_shell.stl";   // absolute: openscad_render.py renders from a temp copy, so a relative import() resolves against the wrong directory
$fa = 3; $fs = 0.5;

module recess(x, z, ysurf, r, depth, sc = [1, 1, 1])
    translate([x, ysurf + r - depth, z]) scale(sc) sphere(r = r);

difference() {
    import(shell, convexity = 12);
    for (sx = [1, -1]) {
        recess(sx * 9,  73, 37.1, 6.5, 1.8, [1, 0.55, 0.5]);   // eye
        recess(sx * 13, 68, 32.7, 4.2, 0.8);                    // cheek, corrected
        recess(sx * 5,  54, 42.0, 1.15, 0.9);                   // whisker dimples
        recess(sx * 5,  56, 44.1, 1.15, 0.9);
        recess(sx * 5,  58, 44.1, 1.15, 0.9);
    }
    recess(0, 51, 51.5, 3.5, 1.0, [1.5, 1, 0.7]);               // mouth
    // Pen well. v2's own numbers (x=10, y=-30, r=9, 20mm deep); the floor is
    // set absolutely rather than relative to a body-top function, because the
    // body top here is a measured surface, not an analytic ellipsoid.
    translate([10, -30, 41]) cylinder(r = 9, h = 80);
}
