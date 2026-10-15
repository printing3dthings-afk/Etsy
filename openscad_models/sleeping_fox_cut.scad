// Sleeping Fox -- the CUT half. Blender built the curled organic form; the one
// DIMENSIONED feature is done here, where the boolean is reliable.
//
// Flat base at z = 7. The Blender form bottoms out at z = 2.6 on a curved
// underside, which is not a printable first layer; 4.4mm off the bottom of the
// tail ring gives a real flat footprint to start on.
fox = "openscad_models/sleeping_fox_shell.stl";
$fa = 3; $fs = 0.5;
difference() {
    import(fox, convexity = 10);
    translate([0, 0, 7 - 200]) cube([500, 500, 400], center = true);
}
