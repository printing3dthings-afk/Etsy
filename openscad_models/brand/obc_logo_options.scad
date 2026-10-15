// Five candidate OBC marks (2026-10-14), each drawn at the smallest size it
// engraves cleanly under a print, 16 to 22 mm across. The same 2D shape is the
// logo and the cutter, so what the preview shows is what the printer gets.
//
// design = 1..5; each is 2D, centred on the origin, in mm.
//   1 stamp    OBC in a heavy sans inside a rounded frame, a maker's stamp
//   2 scallop  OBC in rounded letters inside a scalloped badge, like a sticker
//   3 ribbon   OBC knocked out of a ribbon banner
//   4 face     a round O with a kawaii face, then BC
//   5 toolpath OBC in one even line with round ends, as the nozzle draws it
design = 1;

// a stroke this wide is two beads on the 0.4 mm nozzle: the floor for every
// line, and for every wall left between two cuts
B2 = 0.9;

module ring(od, w) difference() { circle(d = od, $fn = 96); circle(d = od - 2 * w, $fn = 96); }

// Every stroke is opened by a bead: offset in by half a bead, back out. What
// a 0.4 mm nozzle cannot draw is taken out of the drawing, so the logo and the
// print agree.
module printable() offset(r = 0.21, $fn = 12) offset(delta = -0.21) children();
// and every gap between strokes closed if it is narrower than a wall
module closed() offset(r = -B2 / 2, $fn = 12) offset(delta = B2 / 2) children();

// the frame clears the letters by 1.1 everywhere, a wall two beads and more
module stamp() {
    text("OBC", size = 3.8, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
    translate([-0.04, 0.04]) difference() {
        offset(r = 2.1, $fn = 32) square([12.6, 3.7], center = true);
        offset(r = 1.2, $fn = 32) square([12.6, 3.7], center = true);
    }
}

// the badge: a disc with fourteen scallops round it, its edge a band two
// beads wide that follows the scallops; the letters rounded, like a sticker
module badge2d() { circle(r = 7.0, $fn = 96); for (i = [0 : 13]) rotate(360 * i / 14) translate([7.0, 0]) circle(r = 1.6, $fn = 32); }
module scallop() {
    text("OBC", size = 3.9, font = "Fredoka:style=SemiBold", halign = "center", valign = "center", spacing = 1.16);
    closed() difference() { badge2d(); offset(r = -B2, $fn = 32) badge2d(); }    // cusps between scallops rounded, as they print
}

// OBC knocked out of a ribbon: the band is cut, the letters are what stays,
// so the letters are walls and need two beads, which Montserrat Black has.
// Each tail drops behind the band, a fold line two beads wide between them, and
// ends in a V. (Layer lines through OBC were tried here first: at a size that
// fits under a print, any line through the B runs through its counters.)
RBW = 15.4; RBH = 6.2;
module ribbon() printable() {
    difference() {
        offset(r = 0.4, $fn = 16) square([RBW - 0.8, RBH - 0.8], center = true);
        text("OBC", size = 3.8, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.08);
    }
    for (s = [-1, 1]) mirror([s > 0 ? 0 : 1, 0]) translate([RBW / 2 + B2, -1.0])
        polygon([[0, -RBH / 2 + 0.6], [2.6, -RBH / 2 + 0.6], [1.5, 0], [2.6, RBH / 2 - 0.6], [0, RBH / 2 - 0.6]]);
}

// the eyes clear the ring and the smile by two beads; BC clears the O by two
module face() {
    translate([-3.0, 0]) {
        ring(7.6, 1.05);
        for (s = [-1, 1]) translate([s * 0.95, 0.9]) circle(d = 1.1, $fn = 32);
        intersection() {
            translate([0, 0.1]) ring(2.9, B2);
            translate([-3, -3]) square([6, 2.45]);
        }
    }
    translate([5.45, -0.05]) text("BC", size = 4.3, font = "Fredoka:style=SemiBold", halign = "center", valign = "center", spacing = 1.12);
}

// OBC in one even line with round ends, the way the nozzle draws: every
// stroke W wide, every counter and gap 0.9 or more. (A joined script was tried
// here first: at any size that fits under a print the b's loop closes.)
W = 1.0; H = 5.6;
function arc(c, r, a0, a1, n = 24) = [for (i = [0 : n]) let (a = a0 + (a1 - a0) * i / n) [c[0] + r * cos(a), c[1] + r * sin(a)]];
module stroke(pts) for (i = [0 : len(pts) - 2]) hull() { translate(pts[i]) circle(d = W, $fn = 24); translate(pts[i + 1]) circle(d = W, $fn = 24); }
module toolpath() translate([-4.95, -H / 2]) {
    yt = H - W / 2; yb = W / 2; ym = 2.8;
    rU = (yt - ym) / 2; rL = (ym - yb) / 2;
    stroke(arc([0, H / 2], H / 2 - W / 2, 0, 360, 48));                                         // O
    xb = 4.2;                                                                                   // B
    stroke(concat([[xb, yb], [xb, yt], [xb + 0.9, yt]], arc([xb + 0.9, ym + rU], rU, 90, -90),
                  [[xb, ym], [xb + 1.2, ym]], arc([xb + 1.2, yb + rL], rL, 90, -90), [[xb, yb]]));
    stroke(arc([10.65, H / 2], H / 2 - W / 2, 45, 315, 40));                                   // C
}

// the mark printed today, for reference
module current() text("OBC", size = 5.0, font = "Montserrat:style=Black", halign = "center", valign = "center", spacing = 1.16);

module logo(d) {
    if (d == 0) current();
    if (d == 1) stamp();
    if (d == 2) scallop();
    if (d == 3) ribbon();
    if (d == 4) face();
    if (d == 5) toolpath();
}
linear_extrude(2) logo(design);
