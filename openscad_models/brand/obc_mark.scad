// The OBC maker's mark (2026-10-14), from the logo Scott chose: OBC in a heavy
// geometric face, struck through with horizontal stripes. One drawing for
// every model, so every print carries the same mark.
//
// It goes on the underside as an INLAY: the letters cut 0.6 mm in and filled
// in a contrasting colour, flush with the base. On a white base that reads as
// crisp dark letters straight off the bed; engraved white on white, the old
// mark barely showed. The logo's stripes become grooves one layer deep across
// the letters' face: each catches a shadow, like the ridges on the gold logo,
// and the letters stay whole in colour above them, so they read at any size.
//
// Struck right through the letters, as in the logo, the stripes failed both
// ways (2026-10-14): in plastic a stripe cannot be finer than two beads, so at
// 4-6 mm one stripe took out the B's middle bar and it stopped reading as a B,
// and at 8-10 mm the stripes were as wide as the letter between them and OBC
// broke up like a barcode.
//
//   obc_inlay(h)     the coloured part, h = cap height in mm: give it to the
//                    contrasting colour
//   obc_cut(h)       what to subtract from the base: the whole letters, so
//                    the grooves are open, not left in the base's colour
//   obc_engrave(h)   the same as a cutter, for a one-colour model
//   obc_mark_width(h)
// Both are mirrored to read from below, sit on z = 0 and are centred on the
// origin; translate them to the spot on the base.
//
// The letters are Montserrat ExtraBold, the logo's face, set 0.95 apart (the
// logo's are almost touching; in plastic every gap needs two beads, 0.9). The
// drawing is cleaned the way a nozzle draws, so what it shows is what prints.

OBC_FONT = "Montserrat:style=ExtraBold";
OBC_GAP = 0.95;             // between letters, and each groove's width
OBC_BAND = 1.1;             // letter face left between two grooves
OBC_INLAY = 0.6;            // the inlay's depth: three layers at 0.2
OBC_GROOVE = 0.2;           // the grooves' depth: the first layer

// glyph boxes at size 10, measured: [letter, ink start, ink width] (2026-10-14)
OBC_GLYPHS = [["O", 0.48, 10.79], ["B", 0.98, 9.24], ["C", 0.48, 9.52]];
function obc_u(h) = h / 9.72;                       // text size per mm of cap height
function obc_mark_width(h) = 29.55 * obc_u(h) + 2 * OBC_GAP;
function obc_grooves(h) = max(0, floor((h + OBC_GAP) / (OBC_BAND + OBC_GAP)) - 1);

module obc_letters(h) let (u = obc_u(h), x0 = -obc_mark_width(h) / 2) {
    for (i = [0 : 2]) let (g = OBC_GLYPHS[i],
            start = x0 + (i == 0 ? 0 : i == 1 ? 10.79 * u + OBC_GAP : (10.79 + 9.24) * u + 2 * OBC_GAP))
        translate([start - g[1] * u, -h / 2]) text(g[0], size = 10 * u, font = OBC_FONT, halign = "left", valign = "baseline");
}
module obc_grooves2d(h) let (n = obc_grooves(h), b = (h - n * OBC_GAP) / (n + 1))
    for (k = [1 : n]) translate([-50, -h / 2 + k * b + (k - 1) * OBC_GAP]) square([100, OBC_GAP]);

// cleaned as a nozzle draws: gaps under 0.85 closed, strokes under a bead opened
module obc_clean() offset(r = 0.21, $fn = 12) offset(delta = -0.21) offset(r = -0.425, $fn = 12) offset(delta = 0.425) children();

module obc_solid2d(h) obc_clean() obc_letters(h);                                   // the letters
module obc_face2d(h) obc_clean() difference() { obc_solid2d(h); obc_grooves2d(h); } // their face: the bands between grooves

// the coloured part: the face in the first layer, the whole letters above it.
// It stands 0.02 proud of its cut: exactly on it, the inlay's outline and the
// cut's met at near-coincident faces and the welded print had open edges
// round the letters (2026-10-14). Split into colours, the inlay takes the
// overlap, so the colour boundary does not move.
module obc_inlay(h, depth = OBC_INLAY) mirror([1, 0, 0]) {
    linear_extrude(OBC_GROOVE + 0.01) offset(delta = 0.02) obc_face2d(h);
    translate([0, 0, OBC_GROOVE]) linear_extrude(depth - OBC_GROOVE) offset(delta = 0.02) obc_solid2d(h);
}
module obc_cut(h, depth = OBC_INLAY) mirror([1, 0, 0]) translate([0, 0, -0.5]) linear_extrude(depth + 0.5) obc_solid2d(h);
// as a cutter: the letters, less the bands, which stay at the face as ridges
module obc_engrave(h, depth = 0.8) mirror([1, 0, 0]) difference() {
    translate([0, 0, -0.5]) linear_extrude(depth + 0.5) obc_solid2d(h);
    translate([0, 0, -1]) linear_extrude(1 + OBC_GROOVE) difference() { obc_solid2d(h); obc_face2d(h); }
}
