// Soft Frame drawer label: MakerWorld customizer (OnBrandCraftz, 2026-11-12).
// Type your own text; it is inlaid flush in a second colour and sized to fit the
// drawer's label window. The label is the shipped blank's exact size, 31.2 x 11.2 x
// 0.8 mm, so it slides into the same pocket. Print flat, text up, supports off,
// 0.2 mm layers.

/* [Your label] */
// The text on the label (one line; long text gets smaller, then narrower)
LABEL_TEXT = "Screws";

/* [Colours] */
// The label
LABEL_COLOUR = "#F4F1EA"; // color
// The text
TEXT_COLOUR = "#2E3440"; // color

/* [Hidden] */
// Why these numbers (Soft_Frame.scad):
// - The pocket is 32 x 12 x 1.5 and its front window 30 x 10. The label stays the
//   blank's 31.2 x 11.2 x 0.8, so the fit is unchanged.
// - The text is a flush inlay, the top two layers (0.4 mm), not raised: nothing
//   stands proud to catch the window's edge as the label slides down the pocket.
// - The text box is 26 x 7 mm, inside the window with 2 mm a side spare. It is
//   centred in the window even when the label sits 0.4 to one side of its pocket.
// - Montserrat Bold, which MakerWorld's Parametric Model Maker has: an unknown
//   font draws nothing and gives no error (the Name Ornament, 2026-11-05).
// - The width rule uses Montserrat Bold's own advances, measured in OpenSCAD
//   (PMM's build may not have textmetrics()). Down to cap height 3 mm the text
//   shrinks; past that it is narrowed, because thinner strokes stop printing
//   cleanly in two 0.4 mm-nozzle layers.
LABEL_W = 31.2; LABEL_H = 11.2; LABEL_T = 0.8; CORNER = 0.7;
INLAY = 0.4;
BOX_W = 26; BOX_H = 7;
FONT = "Montserrat:style=Bold";
SIZE_MAX = 5.0;   // cap height 4.9 mm; with descenders the line is 6.3 tall
SIZE_MIN = 3.0;
CHARS = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 -'.!&#/+:()";
ADV = [1.0389, 1.0376, 0.982, 1.1203, 0.9101, 0.8667, 1.0457, 1.0959, 0.4449, 0.7338, 1.0037, 0.8192, 1.2953,
       1.0959, 1.1447, 0.9793, 1.1447, 0.9969, 0.8653, 0.8382, 1.0688, 0.9711, 1.5367, 0.9142, 0.887, 0.9101,
       0.8369, 0.9359, 0.8016, 0.9386, 0.8558, 0.5249, 0.9494, 0.9372, 0.4083, 0.4435, 0.8884, 0.4083, 1.4228,
       0.9372, 0.8884, 0.9359, 0.9359, 0.5756, 0.7202, 0.59, 0.9318, 0.8111, 1.2709, 0.807, 0.8111, 0.7365,
       0.9209, 0.5317, 0.8002, 0.8029, 0.9345, 0.807, 0.864, 0.8409, 0.8952, 0.864, 0.3838, 0.5235, 0.3119,
       0.3554, 0.392, 0.9874, 0.9766, 0.5317, 0.8125, 0.3554, 0.4842, 0.4856];
function adv(c) = let (i = search(c, CHARS)) len(i) && i[0] != [] ? ADV[i[0]] : 1.0;
function txt_w(s, n) = n <= 0 ? 0 : txt_w(s, n - 1) + adv(s[n - 1]);
W1 = max(0.01, txt_w(LABEL_TEXT, len(LABEL_TEXT)));    // width at size 1
SIZE = max(SIZE_MIN, min(SIZE_MAX, BOX_W / W1, BOX_H / 1.29));
SQUEEZE = min(1, BOX_W / (W1 * SIZE));

module rounded_rect(w, h, r) offset(r = r, $fn = 24) square([w - 2 * r, h - 2 * r], center = true);
module words() scale([SQUEEZE, 1])
    text(LABEL_TEXT, size = SIZE, font = FONT, halign = "center", valign = "center", $fn = 32);
// the text, clipped to its box so nothing ever reaches the label's edge
module words_clipped() intersection() { words(); square([BOX_W + 1, BOX_H + 1], center = true); }

module label_body() difference() {
    linear_extrude(LABEL_T) rounded_rect(LABEL_W, LABEL_H, CORNER);
    translate([0, 0, LABEL_T - INLAY]) linear_extrude(1) words_clipped();
}
module label_text() translate([0, 0, LABEL_T - INLAY]) linear_extrude(INLAY) words_clipped();

// ---- what MakerWorld exports: two colours, centred on (0, 0) ----
color(LABEL_COLOUR) label_body();
color(TEXT_COLOUR) label_text();
