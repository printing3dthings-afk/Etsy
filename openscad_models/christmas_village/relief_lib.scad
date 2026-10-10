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
// Slabs are never deeper than 0.2 / SH, so each 0.2 mm step climbs SH per 1
// out (2026-10-08): with 0.2 mm slabs every step climbed 0.2 per 0.2, 45 deg,
// and the slicer propped the clock faces and the toy window.
function art_n(h, n, sh = SH) = max(n, ceil(h * sh / 0.2));
module art_out(h, n, sh = SH) let (m = art_n(h, n, sh)) for (i = [0 : m - 1]) let (t0 = i == 0 ? -0.01 : i * h / m - 0.01,
        k = ceil(sh * (i + 1) * h / m / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude((i + 1) * h / m - t0) intersection_for(j = [0 : k]) translate([0, j * 0.2]) children();

// Raised out of a face, h proud, full width at its front: the same climb as
// art_out, but built by adding a skirt under each line instead of trimming the
// line from below. art_out's outer slab keeps only what has line under it all
// the way down, so a 1.2 mm horizontal stroke 0.4 proud came out 0.6 to 1.0 mm
// tall: walls under the gate's floor, a toy window's worth (Santa's workshop,
// 2026-10-08). Here the front is the line as drawn and the skirt below it,
// SH up per 1 out, is the slope; gaps narrower than the skirt close at the root.
module art_skirt(h, n, sh = SH) let (m = art_n(h, n, sh)) for (i = [0 : m - 1]) let (t0 = i == 0 ? -0.01 : i * h / m - 0.01,
        t1 = (i + 1) * h / m, k = ceil(sh * (h - t1) / 0.2 - 0.05))
    translate([0, 0, t0]) linear_extrude(t1 - t0) offset(delta = 0.01) union() for (j = [0 : max(k, 0)]) translate([0, -j * 0.2]) children();

// Thickened into the back of a glazed pane, d deep in n slabs, toward -z. Lit
// from behind, thicker plastic passes less light, so the lines show dark on the
// glow, the way a lithophane works. Each line carries a fillet under it that
// shrinks with depth (SH up per 1 in), so its underside rises as it leaves the
// pane and prints without support; it reads as a soft shadow under each line.
module art_in(d, n) let (m = art_n(d, n)) for (i = [0 : m - 1]) let (t0 = i * d / m, t1 = (i + 1) * d / m,
        k = ceil(SH * (d - t0) / 0.2 - 0.05))
    // grown 0.01: the shifted copies met corner to corner, and the slab came out
    // of linear_extrude as a mesh CGAL would not close (Santa's workshop, 2026-10-08)
    translate([0, 0, -t1]) linear_extrude(t1 - t0 + 0.01) offset(delta = 0.01) union() for (j = [0 : k]) translate([0, -j * 0.2]) children();

// sh, where given, is the climb per 1 out. SH (1.2, 50 deg) is only 5 deg
// inside the slicer's 45 deg support threshold: on the turret house's columns,
// whose stripes tilt 28 deg, that margin went and the slicer propped them; a
// column sliced alone at 2 SH needed none (2026-10-08).

// The flat front of a relief built h proud with SH-sheared undersides: only
// there can art stand on it without hanging over the slope below.
// h is the relief's whole depth, back to where its climb starts: relief_up(-0.4,
// fr_t) climbs from -0.4, and its hole (relief_hole) is raised SH * (fr_t + 0.4)
// at the front. Given fr_t, the porthole's wedges ran 0.48 mm past the hole's
// raised top and the slicer propped them (the gingerbread workshop, 1,485
// moves); given fr_t + 0.4 they sliced clean (2026-10-08). A skirt (art_skirt)
// needs its own length on top: h + (skirt depth).
module top_face(h, sh = SH) intersection() { children(); translate([0, sh * h]) children(); }
