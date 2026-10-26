// The Valentine's chocolate shops' common parts (2026-10-26): a square
// building on the village's snow base, open underneath over a battery LED
// tealight, its windows glazed thin so they glow. Every building that includes
// this sets W, D (the walls' outside), Z0 (the base's top, where the walls
// start), H (the walls' top) and SH before the include, and the scenes
// library (../valentine_scenes.scad) and relief_lib after it.
//
// Scott's rules for the drop (README): glow panes 0.9 mm; anything in a
// window is built on the back of its pane, thick, so it shows only lit;
// daylight detail (frames, sign, letters, awning) stands out of the wall. One
// colour, matte white: every detail is relief, none is colour alone.
//
// Faces: ang 0 the front (-y), 90 the right (+x), 180 the back, 270 the left.
// In a face's frame u runs left to right as seen from outside, v up, w out.

T     = 2.4;        // the walls: they glow a little too, as the village's do, but
                    // at 1.8 they glowed as bright as the 0.9 panes (render,
                    // 2026-10-26); at 2.4 the windows stand out. 47.2 clear inside.
PANE  = 0.9;        // the glass: two lines
ART_D = 2.0;        // a window's scene, into the back of its pane
LIP   = PANE * SH;  // the reveal's sill rises this far across the wall in front of the pane

function fdist(ang) = (ang % 180 == 0) ? D / 2 : W / 2;
module face(ang, w = 0) rotate([0, 0, ang]) translate([0, -fdist(ang) - w, 0]) rotate([90, 0, 0]) children();

module shell() difference() {
    translate([-W / 2, -D / 2, Z0 - 0.01]) cube([W, D, H - Z0 + 0.01]);
    translate([-W / 2 + T, -D / 2 + T, Z0 - 1]) cube([W - 2 * T, D - 2 * T, H - Z0 + 2]);
}

// ---- windows ----------------------------------------------------------------------------
// The pane sits at the wall's inside face. In front of it the opening is
// sheared up SH per 1 out, so its head slopes up away from the glass and
// nothing hangs over the reveal (the village's relief_hole, Technique 80).
module shear_v(sh = SH) multmatrix([[1, 0, 0, 0], [0, 1, sh, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) children();
module win_cut(ang) face(ang) {
    translate([0, 0, -T - 1]) linear_extrude(1 + PANE + 0.01) children();
    translate([0, 0, -T + PANE]) shear_v() linear_extrude(T - PANE + 1) children();
}
module win_pane(ang) face(ang) translate([0, 0, -T]) linear_extrude(PANE) children();
// the scene on the pane's back, hidden until lit
module win_art(ang, emb = 0) face(ang) translate([0, 0, -T + emb]) art_in(ART_D, 4) glow_clean() children();
// a raised frame round the opening, its underside sloped (glow_out)
module win_frame(ang, f = 1.4, h = 1.0, emb = 0) face(ang) translate([0, 0, -emb]) glow_out(h, 2) difference() { offset(delta = f) children(); children(); }
// bars on the glass, in front of it inside the reveal, thick enough to show
// dark when lit and in relief by day: children(0) the window, children(1) its
// bars
module win_bars(ang, h = 0.7) face(ang) translate([0, 0, -T + PANE - 0.01]) glow_out(h, 2) intersection() { children(0); children(1); }

// ---- daylight relief ------------------------------------------------------------------------
module relief(ang, h, emb = 0) face(ang) translate([0, 0, -emb]) glow_out(h, 2) children();
// a sign board with raised letters (the village's sign font)
SIGN_FONT = "Montserrat:style=Black";
module sign_board(ang, v, w, h, emb = 0) relief(ang, 1.2, emb) translate([0, v]) offset(r = 0.8) square([w - 1.6, h - 1.6], center = true);
module sign_letters(ang, txt, v, size, sp = 1.1) face(ang) translate([0, 0, 1.19]) glow_out(1.0, 2)
    translate([0, v]) text(txt, size = size, font = SIGN_FONT, halign = "center", valign = "center", spacing = sp);

// a profile in (w out, v up), extruded along u from u0 to u1, in a face's frame
module uprism(u0, u1) multmatrix([[0, 0, 1, u0], [0, 1, 0, 0], [1, 0, 0, 0], [0, 0, 0, 1]]) linear_extrude(u1 - u0) children();

// ---- awning ---------------------------------------------------------------------------------
// A striped awning along a face from u0 to u1, its top edge on the wall at zt:
// the canvas slopes down AO out over DR, a valance AV deep hangs at its front,
// and under it a cove rises SH per 1 out from the wall, so it prints with
// nothing under it. The stripes stand 0.6 proud of the canvas, every other
// one, so they read on a white print; the valance's edge is scalloped in
// relief.
module awning(ang, u0, u1, zt, AO = 10, DR = 7, AV = 3.5, n = 8) let (zf = zt - DR - AV, zw = zf - SH * AO, st = (u1 - u0) / n)
    face(ang) {
        uprism(u0, u1) polygon([[-0.01, zw], [AO, zf], [AO, zt - DR], [-0.01, zt]]);
        // raised stripes: on the canvas, every other one, stopping at its
        // front edge (past it they would hang over the valance)
        for (i = [0 : 2 : n - 1]) uprism(u0 + i * st, u0 + (i + 1) * st)
            polygon([[-0.01, zt - 0.01], [AO, zt - DR - 0.01], [AO, zt - DR + 0.6], [-0.01, zt + 0.6]]);
        // scallops on the valance's face
        translate([0, 0, AO - 0.01]) glow_out(0.7, 2) intersection() {
            for (i = [0 : n - 1]) translate([u0 + (i + 0.5) * st, zf + 0.6]) circle(st * 0.42, $fn = 32);
            translate([u0, zf]) square([u1 - u0, st * 0.42 + 0.6]);
        }
    }

// ---- base -----------------------------------------------------------------------------------
// The village's snow base (the toy shop's): a slab with a rounded top edge, a
// few drifts, open over the light. Its children add to the footprint (a bay).
BH = Z0;
module base2d() offset(r = 3, $fn = 48) offset(delta = -3) offset(r = 6.5, $fn = 48) union() { square([W, D], center = true); children(); }
module base_slab() {
    linear_extrude(BH - 1.8) base2d() children();
    for (i = [1 : 6]) let (a0 = 15 * (i - 1), a1 = 15 * i)
        translate([0, 0, BH - 1.8 + 1.8 * sin(a0)]) linear_extrude(1.8 * (sin(a1) - sin(a0)) + 0.01)
            offset(delta = -1.8 * (1 - cos(a1))) base2d() children();
}
module base(drifts) difference() {
    union() {
        base_slab() children();
        intersection() {
            for (d = drifts) translate([d[0], d[1], BH - 0.5]) intersection() {
                scale([d[2], d[3], d[4] + 0.5]) sphere(r = 1, $fn = 32);
                translate([-50, -50, 0]) cube(100);
            }
            linear_extrude(BH + 10) offset(delta = -2.4) base2d() children();
        }
    }
    translate([-W / 2 + T, -D / 2 + T, -1]) cube([W - 2 * T, D - 2 * T, BH + 20]);
}
// the maker's mark under the base's front, between the opening and the edge,
// read tipped back
module mark_cut() translate([0, -D / 2 - 2.35, 0]) obc_engrave(4.4, 0.8, 0.15, ridges = false);
