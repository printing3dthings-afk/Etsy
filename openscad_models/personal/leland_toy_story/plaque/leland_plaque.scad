// LELAND name plaque: Buzz Lightyear's open wings -- for Leland's 2nd
// birthday (Scott, 2026-10-24). PERSONAL, NOT FOR SALE (Toy Story is
// Disney/Pixar's).
//
// v2, from Scott's reference photo of the toy's back (2026-10-24): the first
// plaque's swept white wings with red tips "do not look like Buzz
// Lightyear's". The real ones are straight and level, purple, with a band of
// red-and-white diagonal stripes along the top edge over a thin green line,
// two panels a side (the outer a little smaller), and rounded green end caps,
// the left one with a red light. Here the wings ARE the plaque: LELAND
// across them in yellow with a red outline, Woody's sheriff star above on
// the white-and-green jetpack.
//
// Prints face up, flat back on the plate: every raised part stands on the one
// under it, nothing to support. One solid piece, rounded corners, nothing
// that can come off. Hang it with Command strips on the flat back.
//
// FIVE COLOURS ON A FOUR-SLOT AMS, ONE SWAP: purple is only ever the bottom
// 4.0 mm (the wings' face), white only ever above it. Both are slot 1: pause
// after the layer at 4.0 and swap the purple spool for white.
//   slot 1  purple   z 0   - 4.0   the wings
//           white    z 4.0 - 5.6   stripes, the jetpack's panel
//   slot 2  green    z 0   - 6.0   end caps, jetpack, the line under the stripes (z 4.0 - 5.2)
//   slot 3  red      z 4.0 - 7.6   stripes, the letters' outline, the left cap's light
//   slot 4  yellow   z 0   - 9.0   letters (z 4.0 - 9.0), the star (from the plate up)
// priority yellow > red > green > slot 1. Heights on the 0.2 grid.

$fa = 3;  $fs = 0.3;
part = "all";

T = 4.0;                              // the wings' face: purple below, white above (the swap)
NAME = "LELAND";
n_font = "Fredoka:style=SemiBold";  n_size = 25;  n_y = -8;
n_fat = 0.6;  n_out = 2.6;

// ---- the wings: two panels a side, from Scott's photo (0.2 mm per pixel at 210 mm span) ---------
IN  = [0, 61, -26, 24];               // inner panel [x0, x1, y0, y1], right side
OUT = [61.8, 100, -23, 20];             // outer panel: a little lower on top, a little higher underneath
band = 13;                            // the stripe band down from each panel's top
module rrect(x0, x1, y0, y1, r) translate([x0 + r, y0 + r]) offset(r = r) square([x1 - x0 - 2 * r, y1 - y0 - 2 * r]);
module panel(p, r = 2) rrect(p[0], p[1], p[2], p[3], r);
module both() { children(); mirror([1, 0]) children(); }
module wings2d() both() { panel(IN); panel(OUT); }
// the seam between the panels: a real 0.8 gap, the panels joined under it up
// to 0.6 below the face. Cut as a groove across overlapping panels it left
// 0.35 slivers of purple at the corners (print_fidelity, 2026-10-24)
module bridge2d() both() translate([60.4, OUT[2] + 1]) square([2, OUT[3] - OUT[2] - 2]);
// the band: red and white diagonal stripes, 6 wide, leaning 30 deg, and the
// thin green line under them
st_w = 6;
// clipped to the panel's own rounded outline: drawn square, the band's
// corners hung past the panels' rounded ones and the slicer propped them
// (1,014 support moves, 2026-10-24)
module band2d(p) intersection() { panel(p); translate([p[0], p[3] - band]) square([p[1] - p[0], band]); }
module bands2d() both() { band2d(IN); band2d(OUT); }
module red_stripes2d() intersection() { bands2d(); both() for (i = [-4 : 2 : 30]) translate([i * st_w, 0]) multmatrix([[1, tan(30), 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]) translate([0, -40]) square([st_w, 80]); }
module white_stripes2d() difference() { bands2d(); red_stripes2d(); }
module line2d() both() for (p = [IN, OUT]) intersection() { panel(p); translate([p[0], p[3] - band - 1.4]) square([p[1] - p[0], 1.4]); }

// end caps: rounded green tabs beyond the outer panels, reaching above and below them
CAP = [99, 109, -27, 16];
module caps2d() both() rrect(CAP[0], CAP[1], CAP[2], CAP[3], 4);
module light2d() mirror([1, 0]) intersection() { rrect(CAP[0], CAP[1], CAP[2], CAP[3], 4); translate([CAP[0] - 1, CAP[3] - 8]) square([20, 20]); }   // the left cap's red top

// ---- the jetpack: green, rising above the wings to carry the star; a white panel down its middle --------
module jet2d() rrect(-27, 27, -30, 38, 9);
// above the name only: run down behind it, the panel left white slivers round
// the letters' outline (print_fidelity: 19.9 mm3 printed white there)
module jet_panel2d() rrect(-17, 17, 7, 32, 6);

// ---- Woody's sheriff star, above the jetpack: six points, a ball on each ---------------------------
st_c = [0, 42];  st_r = 14;
module star2d() translate(st_c) {
    polygon([for (i = [0 : 11]) let (a = 90 + i * 30, r = i % 2 == 0 ? st_r : st_r * 0.64) [r * cos(a), r * sin(a)]]);
    for (i = [0 : 5]) let (a = 90 + i * 60) translate([st_r * cos(a), st_r * sin(a)]) circle(r = 2.4);
    circle(r = st_r * 0.56);
}
// No SHERIFF lettering: at 2.8, 3.6 and 4.2 high a stroke of it dropped in
// the slice every time (print_fidelity, 2026-10-24); the six-point star with
// its balls reads as Woody's badge without it.

module name2d() translate([0, n_y]) offset(r = n_fat) text(NAME, size = n_size, font = n_font, halign = "center", valign = "center", spacing = 1.04);
module outline2d() offset(r = n_out) name2d();

module rise(z0, z1) translate([0, 0, z0]) linear_extrude(z1 - z0) children();

// ---- parts ---------------------------------------------------------------------------------------
module yellow_raw() { rise(T - 0.01, 9.0) name2d(); rise(0, 8.0) star2d(); }
module red_raw()   { rise(T - 0.01, 7.6) outline2d(); rise(T - 0.01, 5.2) red_stripes2d(); rise(T - 0.01, 6.0) light2d(); }
module green_raw() { rise(0, 6.0) caps2d(); rise(0, T) jet2d(); rise(T - 0.01, 5.2) line2d(); }
module white_raw() { rise(T, 5.2) white_stripes2d(); rise(T, 5.6) jet_panel2d(); }
// the wings' base also runs under the whole letter outline: the end letters'
// outline reached past the inner panels over the seam gap and printed into air
// (2026-10-24)
module purple_raw() { rise(0, T) { wings2d(); offset(r = 0.4) outline2d(); } rise(0, T - 0.6) bridge2d(); }

// slot 1 is one part: purple below the swap, white above it
module slot1_raw() { purple_raw(); white_raw(); }
module yellow_part() yellow_raw();
module red_part()    difference() { red_raw(); yellow_raw(); }
module green_part()  difference() { green_raw(); red_raw(); yellow_raw(); }
module slot1_part()  difference() { slot1_raw(); green_raw(); red_raw(); yellow_raw(); }

if      (part == "yellow") yellow_part();
else if (part == "red")    red_part();
else if (part == "green")  green_part();
else if (part == "slot1")  slot1_part();
else if (part == "union")  union() { yellow_part(); red_part(); green_part(); slot1_part(); }
else if (part == "all") {
    color("#6A3FB0") difference() { slot1_part(); rise(T + 0.1, 20) square(400, center = true); }
    color("#F4F1EA") intersection() { slot1_part(); rise(T + 0.1, 20) square(400, center = true); }
    color("#5DBB3F") green_part();
    color("#C8312B") red_part();
    color("#F2C230") yellow_part();
}
