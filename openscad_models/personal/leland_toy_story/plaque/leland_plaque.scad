// LELAND name plaque, Toy Story style -- for Leland's 2nd birthday (Scott,
// 2026-10-24). PERSONAL, NOT FOR SALE (Toy Story is Disney/Pixar's).
//
// Sky-blue plate with Andy's-room white clouds; Buzz's white wings with red
// tips spread behind the name; LELAND in yellow with a red outline, the way
// the Toy Story logo letters; Woody's gold sheriff star above, SHERIFF cut
// into it.
//
// Prints face up, flat back on the plate: every raised part stands on the one
// under it, so there is nothing to hang and nothing to support. One solid
// piece, rounded corners, top edge chamfered, nothing that can come off --
// he's two. Hang it with Command strips or mounting tape on the flat back.
//
// PARTS by colour, priority yellow > red > white > blue:
//   blue    the plate          z 0   - 4.0
//   white   clouds             z 4.0 - 5.0   wings  z 4.0 - 6.0
//   red     wing tips          z 4.0 - 6.0   letter outline  z 4.0 - 7.6
//   yellow  letters            z 4.0 - 9.0   star   z 4.0 - 8.0
// Every height is on the 0.2 grid (detail_calibration/DETAIL_STANDARD.md).

$fa = 3;  $fs = 0.3;
part = "all";

W = 200;  H = 110;  R = 14;  T = 4.0;  cham = 0.8;
NAME = "LELAND";
n_font = "Fredoka:style=SemiBold";  n_size = 26;  n_y = -10;
n_fat = 0.6;  n_out = 2.6;            // letters fattened a little; the red outline's width

module plate2d() offset(r = R) square([W - 2 * R, H - 2 * R], center = true);
module name2d() translate([0, n_y]) offset(r = n_fat) text(NAME, size = n_size, font = n_font, halign = "center", valign = "center", spacing = 1.04);
module outline2d() offset(r = n_out) name2d();

// clouds: Andy's wallpaper, a few soft blobs scattered over the sky
CLOUDS = [[-70, 38, 0.9], [-36, 22, 0.6], [66, 38, 0.9], [76, -38, 0.8], [-74, -38, 0.8], [6, -42, 0.7]];
module cloud2d(s) scale(s) union() {
    translate([-9, 0]) circle(r = 6.5); translate([0, 3]) circle(r = 8.5); translate([10, 0]) circle(r = 6.5);
    translate([-12, -4]) square([24, 6]);
}
module clouds2d() intersection() { offset(delta = -4) plate2d(); for (c = CLOUDS) translate([c[0], c[1]]) cloud2d(c[2]); }

// Buzz's wings: one each side, swept up and out from behind the name, red tips
// swept up and out, so they show past the letters and above them
module wing2d() offset(r = 3) offset(delta = -3)
    polygon([[0, -8], [34, -6], [92, 18], [95, 30], [88, 36], [34, 18], [0, 16]]);
tip_x = 78;
module wings2d() for (s = [-1, 1]) scale([s, 1]) translate([0, n_y]) wing2d();
module tips2d()  intersection() { wings2d(); union() { translate([tip_x, -100]) square([100, 200]); translate([-tip_x - 100, -100]) square([100, 200]); } }

// Woody's sheriff star: six points, a ball on each, SHERIFF across it
st_c = [0, 31];  st_r = 15;
module star2d() translate(st_c) {
    polygon([for (i = [0 : 11]) let (a = 90 + i * 30, r = i % 2 == 0 ? st_r : st_r * 0.64) [r * cos(a), r * sin(a)]]);
    for (i = [0 : 5]) let (a = 90 + i * 60) translate([st_r * cos(a), st_r * sin(a)]) circle(r = 2.4);
    circle(r = st_r * 0.56);
}
module sheriff2d() translate(st_c) text("SHERIFF", size = 2.8, font = "Montserrat:style=Black", halign = "center", valign = "center");

// the plate, its top edge chamfered in two steps
module plate_raw() {
    linear_extrude(T - cham) plate2d();
    translate([0, 0, T - cham - 0.01]) linear_extrude(cham + 0.01) offset(delta = -cham) plate2d();
}
module rise(z0, z1) translate([0, 0, z0]) linear_extrude(z1 - z0) children();

module yellow_raw() difference() {
    union() { rise(T - 0.4, 9.0) name2d(); rise(T - 0.4, 8.0) star2d(); }
    rise(8.0 - 0.6, 9) sheriff2d();      // SHERIFF cut 0.6 into the star's face
}
module red_raw()   { rise(T - 0.4, 7.6) outline2d(); rise(T - 0.4, 6.0) tips2d(); }
module white_raw() { rise(T - 0.4, 6.0) wings2d(); rise(T - 0.4, 5.0) clouds2d(); }
module blue_raw()  plate_raw();

module yellow_part() yellow_raw();
module red_part()    difference() { red_raw(); yellow_raw(); }
module white_part()  difference() { white_raw(); red_raw(); yellow_raw(); }
module blue_part()   difference() { blue_raw(); white_raw(); red_raw(); yellow_raw(); }

if      (part == "yellow") yellow_part();
else if (part == "red")    red_part();
else if (part == "white")  white_part();
else if (part == "blue")   blue_part();
else if (part == "union")  union() { yellow_part(); red_part(); white_part(); blue_part(); }
else if (part == "all") {
    color("#2B5FA8") blue_part();
    color("#F4F1EA") white_part();
    color("#C8312B") red_part();
    color("#F2C230") yellow_part();
}
