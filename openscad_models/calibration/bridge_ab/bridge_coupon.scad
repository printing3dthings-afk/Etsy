// Bridge A/B coupon (2026-11-24).
// Scott, on a bridge test from elsewhere: "Good for the smallest one. The rest have stringing
// slightly on the underside. Is there a better way to achieve these". The same pattern as the
// ironing test that settled our ironing: one part, printed four times on one plate, each copy
// sliced with different bridge settings (see README.md), a raised letter on each to tell them
// apart.
//
// One strip: square pillars on a slab, with bridges of 20, 30, 40 and 50 mm between them.
// Each deck is DECK thick: one slice layer bridges, the rest is solid on top of it, as on a real
// part. The pillars are square walls, so every bridge has a solid anchor at both ends (an anchor
// on a curve sags at a span that's trivial between walls: knowledge base 3.5).
//
//   label = "A" .. "D"

label = "A";
SPANS = [20, 30, 40, 50];   // Scott's test was already good at the smallest span; 10 mm is dropped
P = 8;        // pillar, square
PH = 4;       // pillar height above the slab: room enough to see a strand hang
W = 6;        // the strip's width: pillars and decks
DECK = 1.2;   // six layers at 0.2
SLAB = 1.0;

function xs(i) = i == 0 ? 0 : xs(i - 1) + P + SPANS[i - 1];
L = xs(len(SPANS)) + P;   // overall length

module strip() union() {
    cube([L + 14, W, SLAB]);                                        // the slab, 14 longer for the label
    for (i = [0 : len(SPANS)]) translate([14 + xs(i), 0, SLAB - 0.01]) cube([P, W, PH + DECK + 0.01]);
    for (i = [0 : len(SPANS) - 1]) translate([14 + xs(i) + P - 0.01, 0, SLAB + PH]) cube([SPANS[i] + 0.02, W, DECK]);
    translate([7, W / 2, SLAB - 0.01]) linear_extrude(0.81)
        text(label, size = 5, font = "Liberation Sans:style=Bold", halign = "center", valign = "center");
}
strip();
