// Victorian carolers (2026-10-13), a village accessory. Scott circled them
// from the second batch of studies (../concepts/accessories2_scene.jpg).
//
// Four carolers on a patch of snow, facing the street: a gentleman in a top
// hat and a long coat, a lady in a bonnet and a long skirt, a child in a cap,
// each holding an open songbook up to sing from, and a second gentleman at the
// end holding a lantern on a staff. Scarves at every neck.
//
// Drawn to print standing up with no support: every coat and skirt narrows as
// it rises or flares out no faster than it climbs, scarves and heads swell
// out at 40 degrees or less before they round over, hat brims and bonnets grow
// out of the head at 40, and arms are a straight upper arm down the side of
// the coat and a forearm that climbs to the book at 39. A book leans its top
// away from the singer, pages up at him, its cover facing down at 40.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
MARK = [[-1.5, 0], 4.4];         // the maker's mark: where on the base, its cap height
SH = 1.2;
zb = 3.0;                   // the snow's top

// ---- a figure, standing at the origin, facing -y ---------------------------------------------
// coat: [radius, height] up the profile, foot to neck
COAT_MAN   = [[4.0, 0], [3.2, 7.0], [3.4, 11.0], [3.7, 13.4], [3.0, 14.6], [1.3, 15.4]];
COAT_LADY  = [[5.0, 0], [3.0, 9.0], [3.3, 11.2], [3.6, 13.4], [2.9, 14.6], [1.3, 15.4]];
module coat(prof) rotate_extrude($fn = 40) polygon(concat([[0, 0]], prof, [[0, prof[len(prof) - 1][1]]]));
// the scarf: out of the coat at 40 deg, round, in to the chin
module scarf(z) translate([0, 0, z]) rotate_extrude($fn = 40) polygon([[0, 0], [1.3, 0], [2.4, 1.1 * SH], [2.4, 1.6], [1.6, 2.0], [0, 2.0]]);
// the head: out of the scarf at 39 deg, then a dome
HEAD = [[1.6, 0], [2.4, 1.0], [2.35, 1.8], [2.1, 2.6], [1.6, 3.3], [0.9, 3.8], [0, 4.0]];
module head(z) translate([0, 0, z]) rotate_extrude($fn = 40) polygon(concat([[0, 0]], HEAD));
// hats, from the head at its 2.6 mm ring
module top_hat(z) translate([0, 0, z]) rotate_extrude($fn = 40)
    polygon([[0, 2.4], [2.0, 2.4], [3.1, 2.4 + SH * 1.1], [3.1, 2.4 + SH * 1.1 + 1.2], [1.95, 2.4 + SH * 1.1 + 1.2], [1.95, 7.6], [0, 7.6]]);
module cap(z) translate([0, 0, z]) rotate_extrude($fn = 40)
    polygon([[0, 2.4], [2.1, 2.4], [2.75, 2.4 + SH * 0.65], [2.65, 3.6], [1.6, 4.3], [0, 4.5]]);
// a poke bonnet: round the back of the head, a shell 1.0 thick, open over
// the face. The head is not cut out of it here: trim outranks body, so the
// exported bonnet loses the head anyway, and cutting it here as well left
// the two coincident and the union with open edges (2026-10-13).
module bonnet(z) translate([0, 0, z]) difference() {
    rotate_extrude($fn = 40) polygon([[0, 0.8], [1.9, 0.8], [3.4, 0.8 + SH * 1.5], [3.4, 3.1], [3.0, 4.4], [2.0, 5.4], [0, 5.7]]);
    translate([-5, -10, -1]) cube([10, 8.6, 10]);          // the face, open to the front
}
// a limb: a disc at a hulled to a cone at b, pointing down at 34 deg. Where
// the lower end comes out of the coat, its point is an island in mid-air
// that the slicer props, so every elbow and hand that hangs sits inside the
// coat (2026-10-13).
module limb(a, b, r = 0.8) hull() { translate(a) cylinder(r = r, h = 0.01, $fn = 16); translate(b) cylinder(r1 = 0.01, r2 = r, h = 1.5 * r, $fn = 16); }
// both arms up to a book held at chest height
module arms_book(sh, el, ha) for (m = [0, 1]) mirror([m, 0, 0]) { limb(sh, el); limb(el + [0, 0, 0.8], ha); }
// The book: a board whose top leans 40 deg away from the singer, so its pages
// face up at him and its cover faces down at 40 deg. Its foot is cut back to
// a line climbing 55 deg: square, the foot faced the plate at 50 and the
// slicer propped every book (2026-10-13). Section in (y, z), extruded across.
BK = 40;                                       // the lean
function bk_d() = [-sin(BK), cos(BK)];         // up the board
function bk_n() = [cos(BK), sin(BK)];          // out of its pages
module board(o, t, h, w, s) multmatrix([[0, 0, 1, -w / 2], [1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1]]) linear_extrude(w)
    let (d = bk_d(), n = bk_n()) polygon([o, o + h * d, o + h * d + t * n, o + t * n + s * d]);
module book(ha, w = 4.2, h = 3.0, t = 1.2) board([ha[1] + 0.2, ha[2] - 0.6], t, h, w, 0.25);
// the open pages, standing 0.4 off the board toward the singer
module pages(ha, w = 4.2, h = 3.0, t = 1.2) let (d = bk_d(), n = bk_n())
    board([ha[1] + 0.2, ha[2] - 0.6] + (t - 0.01) * n + 0.5 * d, 0.41, h - 0.8, w - 0.7, 0.12);

// a singer: coat colour, hat, scale
module singer(coat_p, coat_c, scarf_c, hat, hat_c, s = 1) scale(s) {
    zs = COAT_MAN[len(COAT_MAN) - 1][1] - 0.8;
    SH0 = [2.9, -0.3, 13.6]; EL = [2.3, -0.8, 8.8]; HA = [1.7, -2.6, 12.4];
    if ($p == coat_c) { coat(coat_p); arms_book(SH0, EL, HA); }
    if ($p == scarf_c) scarf(zs);
    if ($p == "trim") { head(zs + 2.0); pages(HA); }
    if ($p == "roof") book(HA);
    if ($p == hat_c) {
        if (hat == "top") top_hat(zs + 2.0);
        if (hat == "cap") cap(zs + 2.0);
        if (hat == "bonnet") bonnet(zs + 2.0);
    }
}
// the lantern bearer: no book; his right hand holds a staff with a lantern on it
LX = -4.0;                  // the staff, left of him and into his coat, so it is held all the way down
LZ = 21.0;                  // the lantern's foot
module bearer(coat_c, scarf_c) {
    zs = COAT_MAN[len(COAT_MAN) - 1][1] - 0.8;
    if ($p == coat_c) {
        coat(COAT_MAN);
        // his left arm hangs; his right reaches out and up to the staff
        limb([2.9, 0, 13.6], [2.3, -0.2, 8.4]);
        limb([-2.9, 0, 13.6], [-2.3, -0.3, 10.0]);
        limb([-2.6, -0.3, 10.8], [LX + 0.6, -0.3, 12.6]);
    }
    if ($p == scarf_c) scarf(zs);
    if ($p == "trim") head(zs + 2.0);
    if ($p == "roof") { top_hat(zs + 2.0); staff(); lantern_iron(); }
    if ($p == "trim") lantern_glass();
}
// the staff, from the snow to the lantern's foot
module staff() translate([LX, -0.3, -zb + 0.5]) cylinder(r = 1.0, h = LZ + zb - 0.5 + 0.1, $fn = 20);
// The lantern: an iron collar flaring at 40 deg from the staff, a six-sided
// glass with an iron post at each corner, a roof with a flared eave, a bud.
LC = 2.5;                   // the collar, out to
LG = 2.2;                   // the glass
LH = 3.4;                   // its height
LR = 2.8;                   // the eave
z_g = (LC / cos(30) - 1.0) * SH;   // the glass's foot, above LZ: its corners climb 40 deg
z_r = z_g + LH;             // the roof's
module lantern_iron() translate([LX, -0.3, LZ]) {
    cylinder(r1 = 1.0, r2 = LC / cos(30), h = z_g, $fn = 6);
    for (i = [0 : 5]) rotate([0, 0, 60 * i]) translate([LG / cos(30) - 0.3, 0, z_g - 0.01]) cylinder(r = 0.6, h = LH + 0.02, $fn = 12);
    translate([0, 0, z_r]) {
        cylinder(r1 = LG / cos(30), r2 = LR / cos(30), h = (LR - LG) * SH, $fn = 6);
        translate([0, 0, (LR - LG) * SH - 0.01]) cylinder(r = LR / cos(30), h = 1.2, $fn = 6);
        translate([0, 0, (LR - LG) * SH + 1.19]) cylinder(r1 = LR / cos(30), r2 = 0.4, h = 2.2, $fn = 6);
        translate([0, 0, (LR - LG) * SH + 3.3]) rotate_extrude($fn = 24) polygon([[0, 0], [0.5, 0], [0.5, 0.4], [0.9, 0.9], [0.9, 1.3], [0.45, 2.0], [0, 2.0]]);
    }
}
// its glass, lit
module lantern_glass() translate([LX, -0.3, LZ + z_g - 0.01]) cylinder(r = LG / cos(30), h = LH + 0.02, $fn = 6);

// ---- the group on its snow ---------------------------------------------------------------------
module group() {
    translate([-12.0, 1.6, zb]) bearer("body", "accent");
    translate([-3.4, 2.4, zb]) singer(COAT_MAN, "roof", "body", "top", "roof");
    translate([4.6, -0.2, zb]) singer(COAT_LADY, "accent", "body", "bonnet", "body");
    translate([11.6, -2.0, zb]) singer(COAT_MAN, "body", "accent", "cap", "roof", 0.78);
}
module base2d() translate([-1.5, 0]) scale([1, 0.62]) circle(r = 20, $fn = 80);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([-15.5, -6.5, zb], [3.5, 2.4, 1.3]); drift([14.5, 5.0, zb], [3.4, 2.2, 1.2]); } base2d_in(); }
    }
    brand_mark(MARK[0], MARK[1]);
}

module raw(p) let ($p = p) {
    group();
    if (p == "trim") base();
}
emit();
