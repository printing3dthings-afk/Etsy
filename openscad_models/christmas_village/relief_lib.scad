// Relief that keeps colour-only detail visible on a one-colour print
// (2026-10-08). Included textually, so SH is the including building's own.
//
// Lines drawn flush in a part (toys on glass, clock hands, stripes, outlines)
// exist only as colour: a white print loses them, lit or not, and a painter has
// no edge to follow (the haunted post office's carved sign came back painted as
// "POST OFFKE"). Both helpers build in 0.2 mm steps, the layers', each slab
// nested in the one before it, so nothing closes over a pocket (Technique 81).

// Raised out of a face, h proud in n slabs. Each slab keeps only what has line
// under it all the way down its climb, SH up per 1 out: only the undersides
// slope; tops, gaps and counters stay as drawn.
module art_out(h, n) for (i = [0 : n - 1]) let (t0 = i == 0 ? -0.01 : i * h / n - 0.01,
        k = ceil(SH * (i + 1) * h / n / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / n - t0) intersection_for(j = [0 : k]) translate([0, j * 0.2]) children();

// Thickened into the back of a glazed pane, d deep in n slabs, toward -z. Lit
// from behind, thicker plastic passes less light, so the lines show dark on the
// glow, the way a lithophane works. Each line carries a fillet under it that
// shrinks with depth (SH up per 1 in), so its underside rises as it leaves the
// pane and prints without support; it reads as a soft shadow under each line.
module art_in(d, n) for (i = [0 : n - 1]) let (t0 = i * d / n, t1 = (i + 1) * d / n,
        k = ceil(SH * (d - t0) / 0.2 - 0.05))
    translate([0, 0, -t1]) linear_extrude(t1 - t0 + 0.01) for (j = [0 : k]) translate([0, -j * 0.2]) children();

// The flat front of a relief built h proud with SH-sheared undersides: only
// there can art stand on it without hanging over the slope below.
module top_face(h) intersection() { children(); translate([0, SH * h]) children(); }
