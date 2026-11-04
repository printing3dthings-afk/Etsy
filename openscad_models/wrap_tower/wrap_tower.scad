// Wrap-Around Tower: a four-in-a-row game round a tower (2026-11-04).
// Scott's pick, form 2 of five: "the columns run round the outside of a
// cylinder, so lines can wrap all the way round".
//
// The rules of four-in-a-row are free to use; the classic upright blue grid
// with red and yellow discs is a brand's look, so this keeps away from it: a
// round cream tower, pink and lilac pieces.
//
// Eight tubes round the tower, six pieces high: 48 cells, 24 pieces a
// player. Drop a piece in at the top; a slot down the front of each tube
// shows the stack. Rows wrap round, so a line can run from tube 8 into tube 1.
// Lift the tower off its tray and the pieces drop out; all 48 store back in
// the tubes.
//
// Three prints, one colour each, no supports:
//   tower  upright, the tubes open top and bottom. The slots run open to the
//          top, so nothing hangs: the rim is crenellated, like a castle.
//   tray   a dish with a recess the tower sits in, which closes the tubes'
//          bottoms while you play.
//   puck   a piece. Pink pieces carry a heart pressed into the top, lilac a
//          star, so the two players are told apart by shape as well as colour.
//
//   part = tower | tray | puck_heart | puck_star | assembly
//          plate_hearts | plate_stars (24 pieces, for printing)

use <../brand/obc_mark.scad>

part = "assembly";

N = 8;                    // tubes round the tower
ROWS = 6;
PUCK_D = 16;              // a piece
PUCK_H = 7;
PUCK_CH = 0.6;            // the chamfer round each face
CLR = 1.0;                // across a tube: a piece drops freely, and can't turn
                          // on edge (its diagonal, 17.5, is longer than the bore)
BORE = PUCK_D + CLR;      // 17
WALL = 1.6;               // tube wall outside the bore (four beads)
// least wall between two bores. At 1.6, two 1.5 mm funnels met over it and
// left a knife edge between the tubes' mouths (min wall 0.60, 2026-11-04)
WEB = 3.0;
// the tubes' centre radius: two bores WEB apart at their closest
R_C = ceil(((BORE + WEB) / (2 * sin(180 / N))) * 2) / 2;      // 26.5
R_OUT = R_C + BORE / 2 + WALL;                                 // 36.6
STACK = ROWS * PUCK_H;    // 42
H = STACK + 6;            // the tower: the full stack, then a 6 mm rim
FUNNEL = 0.8;             // a chamfer at each tube's mouth: the web keeps 1.7 between them
SLOT_W = 8;               // the window down each tube: narrower than a piece
SLOT_Z0 = 3;              // so the bottom piece can't slip out
TOP_CH = 1.0;             // chamfer round the tower's top edge

TRAY_R = 56;              // the tray
TRAY_FLOOR = 2.4;
TRAY_WALL = 2.4;
TRAY_H = 10;
SEAT_CLR = 0.4;           // the tower in its recess
SEAT_D = 1.6;             // the recess's depth

$fn = 96;

// ---------- the tower ----------
module tower() difference() {
    // a cylinder chamfered at the top edge only; the bottom stays square on the plate
    rotate_extrude() polygon([[0, 0], [R_OUT, 0], [R_OUT, H - TOP_CH], [R_OUT - TOP_CH, H], [0, H]]);
    for (i = [0 : N - 1]) rotate(i * 360 / N) {
        // the bore, open top and bottom, with a funnel at its mouth
        translate([R_C, 0, -0.5]) cylinder(d = BORE, h = H + 1);
        translate([R_C, 0, H - FUNNEL]) cylinder(d1 = BORE, d2 = BORE + 2 * FUNNEL + 0.02, h = FUNNEL + 0.01);
        // the window, open to the top
        translate([R_C, -SLOT_W / 2, SLOT_Z0]) cube([R_OUT, SLOT_W, H]);
    }
}

// ---------- the tray ----------
module tray() difference() {
    union() {
        cylinder(r = TRAY_R, h = TRAY_FLOOR);
        // the rim, its top edge rounded
        rotate_extrude() translate([TRAY_R - TRAY_WALL, 0])
            hull() { square([TRAY_WALL, TRAY_H - TRAY_WALL / 2]); translate([TRAY_WALL / 2, TRAY_H - TRAY_WALL / 2]) circle(d = TRAY_WALL, $fn = 32); }
        // a raised seat under the tower, so its recess has floor to cut into
        cylinder(r = R_OUT + SEAT_CLR + 3, h = TRAY_FLOOR + SEAT_D);
    }
    translate([0, 0, TRAY_FLOOR]) cylinder(r = R_OUT + SEAT_CLR, h = SEAT_D + 1);
    // the maker's mark under the tray
    obc_engrave(8);
}

// ---------- a piece ----------
module puck_body() rotate_extrude() polygon([[0, 0], [PUCK_D / 2 - PUCK_CH, 0], [PUCK_D / 2, PUCK_CH],
    [PUCK_D / 2, PUCK_H - PUCK_CH], [PUCK_D / 2 - PUCK_CH, PUCK_H], [0, PUCK_H]]);
SYMBOL_D = 0.6;           // pressed into the top face: three layers
module heart2d(w) {       // two circles and a point, 9 mm across at w = 9
    r = w / 4;
    translate([0, -w * 0.12]) union() {
        for (s = [-1, 1]) translate([s * r * 0.92, r * 0.55]) circle(r = r, $fn = 48);
        polygon([[-(r * 0.92 + r * 0.8), r * 0.2], [r * 0.92 + r * 0.8, r * 0.2], [0, -w * 0.48]]);
    }
}
module star2d(w) {        // five points, w across the points
    polygon([for (k = [0 : 9]) let (a = 90 + k * 36, rr = (k % 2 == 0) ? w / 2 : w * 0.21) [rr * cos(a), rr * sin(a)]]);
}
module puck(sym) difference() {
    puck_body();
    translate([0, 0, PUCK_H - SYMBOL_D]) linear_extrude(SYMBOL_D + 0.5)
        if (sym == "heart") heart2d(9); else star2d(10);
}
// 24 pieces in a 6 x 4 grid, 4 mm apart
module plate(sym) for (i = [0 : 5], j = [0 : 3]) translate([(i - 2.5) * (PUCK_D + 4), (j - 1.5) * (PUCK_D + 4), 0]) puck(sym);

// ---------- the set, as it is played ----------
module assembly() {
    color("#E8D3F0") tray();
    color("#F4F1EA") translate([0, 0, TRAY_FLOOR]) tower();
    // a game in progress
    for (i = [0 : N - 1], r = [0 : (i * 5 + 3) % 6])
        color(((i * 3 + r) % 2 == 0) ? "#F6A6C1" : "#B79CE0")
            rotate(i * 360 / N) translate([R_C, 0, TRAY_FLOOR + r * PUCK_H]) puck(((i * 3 + r) % 2 == 0) ? "heart" : "star");
}

// for renders: the tower on its tray, and the pieces of a game in progress
module game(pink) for (i = [0 : N - 1], r = [0 : (i * 5 + 3) % 6])
    if ((((i * 3 + r) % 2) == 0) == pink)
        rotate(i * 360 / N) translate([R_C, 0, TRAY_FLOOR + r * PUCK_H]) puck(pink ? "heart" : "star");

if      (part == "tower_use")    translate([0, 0, TRAY_FLOOR]) tower();
else if (part == "game_pink")    game(true);
else if (part == "game_lilac")   game(false);
else if (part == "tower")        tower();
else if (part == "tray")         tray();
else if (part == "puck_heart")   puck("heart");
else if (part == "puck_star")    puck("star");
else if (part == "plate_hearts") plate("heart");
else if (part == "plate_stars")  plate("star");
else assembly();
echo("R_C", R_C, "R_OUT", R_OUT, "H", H);
