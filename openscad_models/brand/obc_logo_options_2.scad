// Five more OBC marks (2026-10-14), asked for as "more professional and also
// fun": one clean geometric face, Poppins Bold, and one playful detail each.
// Drawn at the smallest size each engraves cleanly; the same 2D shape is the
// logo and the cutter.
//
// design = 6..10, part = "engrave" | "accent"
//   engrave  what is cut into the print, one colour
//   accent   the playful detail's second colour, for screens and the shop
//            icon only; never cut, so it is not part of the engraving
//   6 heart    the O's counter is a heart
//   7 smile    OBC smiling: a gentle arc under the word
//   8 tiles    O, B and C knocked out of three tiles, a star in the fourth
//   9 cat      the O wears two cat ears
//  10 sparkle  a sparkle at the C's shoulder
design = 6;
part = "engrave";

B2 = 0.9;                   // two beads: the floor for every stroke and every wall
P = 5.2;                    // the letters' size: strokes 1.2 mm, 2.9 beads
SP = 1.14;                  // letter spacing: Poppins' own left 0.78 mm between letters
module word(s, sz = P, sp = SP) text(s, size = sz, font = "Poppins:style=Bold", halign = "center", valign = "center", spacing = sp);
module printable() offset(r = 0.21, $fn = 12) offset(delta = -0.21) children();
module closed() offset(r = -B2 / 2, $fn = 12) offset(delta = B2 / 2) children();

// a ring the weight of Poppins' O, and BC set after it: B starts 0.45 into its
// box, so the gap is 0.95, two beads
OR = P / 2;                 // the O's outer radius
OW = 1.2;                   // its stroke
module o_ring() difference() { circle(r = OR, $fn = 96); circle(r = OR - OW, $fn = 96); }
module bc_after_o() translate([OR + 0.5, 0]) text("BC", size = P, font = "Poppins:style=Bold", halign = "left", valign = "center", spacing = SP);

// ---- 6: heart --------------------------------------------------------------------------------
// the O filled, less a heart; the heart's tip blunted to a 0.45 round, since
// the heart is plastic left standing and a sharp tip would not print
module heart2d() for (s = [-1, 1]) hull() { translate([s * 0.62, 0.34]) circle(r = 0.8, $fn = 32); translate([0, -0.95]) circle(r = 0.4, $fn = 24); }   // a hull per lobe: one hull over both filled the notch and read as a shield
module heart() {
    difference() { circle(r = OR, $fn = 96); heart2d(); }
    bc_after_o();
}

// ---- 7: smile --------------------------------------------------------------------------------
// an arc under the word, one stroke wide, sagging 1 mm over 13: every point of
// it two beads and more below the letters
function arc(c, r, a0, a1, n = 32) = [for (i = [0 : n]) let (a = a0 + (a1 - a0) * i / n) [c[0] + r * cos(a), c[1] + r * sin(a)]];
module stroke(pts, w) for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) circle(d = w, $fn = 24); translate(pts[i + 1]) circle(d = w, $fn = 24); }
SR = 21.6; SY = -4.0;       // the smile's radius, and the height of its ends
module smile_arc() let (a = asin(6.5 / SR)) stroke(arc([0, SY - 1.0 + SR], SR, 270 - a, 270 + a), 1.0);
module smile() { word("OBC"); smile_arc(); }

// ---- 8: tiles --------------------------------------------------------------------------------
// four rounded tiles cut in, a wall two beads and more between them; the
// letters and the star are what is left standing, so they are walls too
T = 6.6; TG = 1.0;
module tile(i, j) translate([(i - 0.5) * (T + TG), (0.5 - j) * (T + TG)]) offset(r = 1.2, $fn = 24) square(T - 2.4, center = true);
module at(i, j) translate([(i - 0.5) * (T + TG), (0.5 - j) * (T + TG)]) children();
module star2d(r, k) offset(r = 0.3, $fn = 12) offset(delta = -0.3)
    polygon([for (n = [0 : 9]) let (a = 90 + 36 * n, rr = n % 2 == 0 ? r : r * k) [rr * cos(a), rr * sin(a)]]);
module tiles() printable() difference() {
    union() { tile(0, 0); tile(1, 0); tile(0, 1); tile(1, 1); }
    at(0, 0) word("O", 4.4); at(1, 0) word("B", 4.4); at(0, 1) word("C", 4.4);
    at(1, 1) translate([0, -0.2]) star2d(2.4, 0.5);
}
module tiles_accent() difference() { tile(1, 1); at(1, 1) translate([0, -0.2]) star2d(2.4, 0.5); }

// ---- 9: cat ----------------------------------------------------------------------------------
// two rounded ears on the O, leaning out 25 deg; the inner ear is the accent
module ear(s) rotate(s * 28) translate([0, OR - 0.6]) offset(r = 0.35, $fn = 16) offset(delta = -0.35)
    polygon([[-1.15, 0], [1.15, 0], [0.1 * s, 2.3]]);
module cat() { o_ring(); for (s = [-1, 1]) ear(s); bc_after_o(); }
module cat_accent() for (s = [-1, 1]) rotate(s * 28) translate([0, OR - 0.6]) offset(delta = -0.45) polygon([[-1.15, 0.1], [1.15, 0.1], [0.1 * s, 2.3]]);

// ---- 10: sparkle -----------------------------------------------------------------------------
// a four-point sparkle off the C's shoulder, its points rounded so they print
module sparkle2d() offset(r = 0.28, $fn = 12) offset(delta = -0.28)
    polygon([for (n = [0 : 7]) let (a = 90 + 45 * n, rr = n % 2 == 0 ? 2.1 : 0.62) [rr * cos(a), rr * sin(a)]]);
SPX = 9.6; SPY = 2.9;
module sparkle() { word("OBC"); translate([SPX, SPY]) sparkle2d(); }
module sparkle_accent() translate([SPX, SPY]) sparkle2d();

module logo(d) {
    if (d == 6) heart();
    if (d == 7) smile();
    if (d == 8) tiles();
    if (d == 9) cat();
    if (d == 10) sparkle();
}
module accent(d) {
    if (d == 6) heart2d();
    if (d == 7) smile_arc();
    if (d == 8) tiles_accent();
    if (d == 9) cat_accent();
    if (d == 10) sparkle_accent();
}
linear_extrude(2) { if (part == "engrave") logo(design); else accent(design); }
