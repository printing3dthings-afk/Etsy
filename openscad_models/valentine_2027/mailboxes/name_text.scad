// A child's name in Fredoka SemiBold, laid out one letter at a time
// (2026-10-30). Fredoka draws "IV" as a single ligature glyph, so text("OLIVIA")
// rendered "OLMIA" whatever its spacing, and a zero-width non-joiner between the
// letters does not stop it. One text() per letter can't form a ligature. The
// advances below were measured with OpenSCAD's textmetrics() (per unit size),
// written out so this works in OpenSCAD 2021 too, which has no textmetrics.
//
//   name_text(s, size, spacing)   centred on the origin, both ways
//   name_width(s, spacing)        its advance at size 1

NAME_FONT = "Fredoka:style=SemiBold";
NAME_CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -'.!&";
NAME_ADV = [0.9847, 0.8597, 0.8931, 0.9264, 0.8472, 0.8597, 0.9931, 0.9194, 0.3222, 0.7444, 0.8264, 0.7847, 1.1306, 0.9486, 1.007, 0.8292, 1.1, 0.8486, 0.7583, 0.9, 0.9556, 1.0097, 1.3236, 0.9597, 0.8861, 0.8194, 0.7819, 0.7819, 0.7014, 0.7847, 0.7458, 0.5625, 0.7667, 0.7694, 0.3361, 0.3278, 0.7, 0.4181, 1.1153, 0.7819, 0.7764, 0.7667, 0.7653, 0.5875, 0.6361, 0.5708, 0.7778, 0.7833, 1.0361, 0.7264, 0.7764, 0.75, 0.7944, 0.5319, 0.8014, 0.7944, 0.7625, 0.6958, 0.7306, 0.7403, 0.7597, 0.7306, 0.3347, 0.5708, 0.2625, 0.3014, 0.3361, 0.975];

function name_adv(c) = let (i = search(c, NAME_CHARS)) len(i) && i[0] != [] ? NAME_ADV[i[0]] : 0.8;
function name_pre(s, sp, n) = n <= 0 ? 0 : name_pre(s, sp, n - 1) + name_adv(s[n - 1]) * sp;
function name_width(s, spacing = 1) = name_pre(s, spacing, len(s));
// the size that fits the name in w across and h high
function name_fit(s, w, h, spacing = 1) = min(h, w / name_width(s, spacing));

module name_text(s, size, spacing = 1)
    translate([-name_width(s, spacing) * size / 2, 0])
        for (i = [0 : len(s) - 1])
            translate([name_pre(s, spacing, i) * size, 0])
                text(s[i], size = size, font = NAME_FONT, valign = "center");
