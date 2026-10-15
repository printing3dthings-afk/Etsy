// Shared by the Victorian village's accessories (2026-10-13): the snow base,
// drifts, the maker's mark and the colour-part convention. Included
// textually, after the piece sets `part`.
//
// COLOUR PARTS, as the village's buildings, priority roof > accent > trim > body:
//   body    brick red  #A8483A
//   roof    slate      #2E3440
//   trim    white      #F4F1EA  (snow, stone, columns, faces)
//   accent  evergreen  #2F6B45
// A piece defines raw(p) for each part; overlaps between parts are fine,
// because each exported part is its raw shape less every part above it, and
// part = "union" is all of them together (the mesh product_gate checks).

$fa = 4; $fs = 0.3;

PRIORITY = ["roof", "accent", "trim", "body"];
function above(p) = p == "roof" ? [] : p == "accent" ? ["roof"] : p == "trim" ? ["roof", "accent"] : ["roof", "accent", "trim"];

// A piece sets MARK = [[x, y], cap height] for its maker's mark, and may set
// MARK_PART to the colour the inlay prints in (slate, "roof", by default).
// base() cuts the letters out of the snow with brand_mark(MARK[0], MARK[1]);
// the inlay is added to MARK_PART here, so no piece's raw() has to know of it.
function mark_on(p) = !is_undef(MARK) && p == (is_undef(MARK_PART) ? "roof" : MARK_PART);
module mark_inlay() translate([MARK[0][0], MARK[0][1], 0]) obc_inlay(MARK[1]);
module raw_marked(p) { raw(p); if (mark_on(p)) mark_inlay(); }
module part_out(p) difference() {
    raw_marked(p);
    for (q = above(p)) raw_marked(q);
}
module emit() {
    if (part == "union") union() for (p = PRIORITY) raw_marked(p);
    else if (part == "all") {
        color("#2E3440") part_out("roof"); color("#2F6B45") part_out("accent");
        color("#F4F1EA") part_out("trim"); color("#A8483A") part_out("body");
    } else part_out(part);
}

// ---- the snow base: a soft slab, its top edge rounded ----------------------------------------
// children(): its 2D outline
module snow_base(h = 3.2, r = 1.6) {
    linear_extrude(h - r) children();
    for (i = [1 : 5]) let (a0 = 18 * (i - 1), a1 = 18 * i)
        translate([0, 0, h - r + r * sin(a0)]) linear_extrude(r * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -r * (1 - cos(a1))) children();
}
// children(0), kept inside the 2D outline children(1): drifts kept off the
// base's rounded edge (pass the outline pulled in 2.4), where they hang over it
module clip_to() intersection() { children(0); linear_extrude(60) children(1); }
// a drift: the top of an ellipsoid standing on the base
module drift(p, s) translate([p[0], p[1], p[2] - 0.3]) intersection() {
    scale(s) sphere(r = 1, $fn = 32);
    translate([-50, -50, 0]) cube(100);
}

// ---- the maker's mark ------------------------------------------------------------------------
// OBC inlaid 0.6 mm into the underside in a contrasting colour, grooved like
// the logo (../../brand/obc_mark.scad, 2026-10-14). This cuts the letters out
// of the snow; emit() adds the coloured inlay. Engraved white on white, the
// old mark barely showed.
include <../../brand/obc_mark.scad>
module brand_mark(p, h = 5.0, a = 0) translate([p[0], p[1], 0]) rotate([0, 0, a]) obc_cut(max(h, 4.0));

// ---- shapes that print without support -------------------------------------------------------
// a hole whose crown peaks at 60 deg
module tear2d(r) hull() { circle(r); translate([0, 2 * r]) circle(0.01); }
// a lancet w wide, h to its springing: arcs of radius 3w (six times the
// half-span, as the village's arches), so the crown climbs at 56 deg; an
// equilateral arch's crown climbs at only 30 and the slicer props it
module parch2d(w, h) let (c = 2.5 * w, r = 3 * w) union() {
    translate([-w / 2, 0]) square([w, h + 0.01]);
    translate([0, h]) intersection() { translate([c, 0]) circle(r, $fn = 360); translate([-c, 0]) circle(r, $fn = 360);
        translate([-w / 2, 0]) square([w, 2 * w]); }
}

// ---- reliefs on a flat face: 2D x along it, y up, z out ----------------------------------------
// Raised h out of the face: relief_lib's art_out (undersides climb SH per 1 out).
// Cut d into the face: each step in, the drawing's top comes down SH per 1,
// so every ceiling slopes and prints, the way the village's relief_hole does.
module engrave_in(d, sh = SH) let (m = max(1, ceil(d * sh / 0.2))) for (i = [0 : m - 1]) let (t0 = i * d / m, t1 = (i + 1) * d / m,
        k = ceil(sh * t1 / 0.2 - 0.05))
    translate([0, 0, -t1]) linear_extrude(t1 - t0 + (i == 0 ? 0.5 : 0.01)) intersection_for(j = [0 : k]) translate([0, -j * 0.2]) children();
