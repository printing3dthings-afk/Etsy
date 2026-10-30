// Gift box lantern, v2: split by colour and snapped together (2026-10-30).
// Scott, from its MakerWorld page: "Is it possible to break this up into
// pieces so the different colors print separately and get assembled. Make
// easy snap pieces for connections so it does[n't] have to be glued."
// v1 (../gift_box_lantern.scad) is unchanged and stays the file to print with
// an AMS; this is the version for one filament at a time.
//
// Nine prints, three colours, no glue:
//   green  frame      the base, its floor, the band round it and the four
//                     corner posts, grooved for the glass; a snap pin on top
//                     of each post
//          top        the rail, the band the lid keys onto, and the posts'
//                     tops; it presses down onto the four pins and locks the
//                     glass in
//          lid        v1's lid, with a snap pin on top for the bow
//   white  panel_0..3 the glass, printed flat; each scene stands on it, green
//                     with an AMS or a filament swap at 1.2 mm, or white
//   red    ribbon     the ribbon, a cross over the lid with its four ends
//                     hanging down the sides; it lies on the lid
//          bow        snaps onto the lid's pin through the ribbon's middle,
//                     which holds the ribbon down
//
// Assembly: drop the four panels into the posts' grooves; press the top on
// until the four pins click; set the lid on, lay the ribbon over it and press
// the bow onto the pin. The lid lifts off for the tealight's switch, as on v1.
//
// The joints are split snap pins, two prongs with a barb, each in a socket
// with a narrow throat and a wider chamber. Every pin prints standing up, so
// its barb's catch is a 37 deg slope, not a ledge, and nothing needs support.
//
//   part = frame | top | lid | ribbon | bow | panel_0..3 | panel_art_0..3 |
//          panel_glass_0..3 (as printed) | <same>_use (in place) |
//          all (coloured preview) | plate_green | plate_white | plate_red
include <../../lantern_scenes.scad>
include <../../../christmas_village/relief_lib.scad>
use <../../../brand/obc_mark.scad>

part = "all";
SH = 1.2;
$fa = 4; $fs = 0.4;

// ---- v1's sizes ---------------------------------------------------------------------------
P    = 35;                  // the glass's outer face, from the centre
z0   = 6;                   // the base band's top
fl   = 2.4;                 // the floor
H    = 58;                  // the glass, as seen
zr   = z0 + H;              // the rail's top: the lid sits here
RO   = 2.8;                 // the base band, the rail and the lid, out past the glass
PR   = 3.4;                 // the corner posts' radius (3.2 on v1): room round the snap socket
W    = 60;  HS = 52;        // a scene: between the posts, under the rail
AD   = 1.6;                 // the scenes, out of the glass
LH   = 14;  LR = 3;         // the lid, and its corners' radius
BH   = 5;   CL = 0.25;      // the lid's band, and its clearance
// ---- v2 ----------------------------------------------------------------------------------
PT   = 1.2;                 // the glass: 1.3 on v1, here 6 whole layers, so the
                            // scene's colour starts on a layer (swap at 1.2)
PI_  = P - PT;              // its inner face, 33.8
PC   = P - PT / 2;          // the glass's middle plane, and the posts' centres
BI   = PI_ - 0.8;  BO = P + 0.2;
TOPZ = zr - SH * RO - 2;    // where the top starts: the rail's lowest edge, 58.64
GE   = 1.0;                 // a groove reaches this short of the post's centre
GW   = PT + 0.3;            // the groove: the glass and 0.15 each side
CH   = 2.0;                 // the channel in the base the glass stands in
PZ   = z0 - CH;             // the glass's foot, 4.0
PW   = 2 * (PC - GE - 0.2); // a panel's width, 66.4: 0.2 short of the groove each end
PH   = TOPZ - 0.2 - PZ;     // its height, 54.44: 0.2 under the top
LIP  = 1.2;                 // the base's floor stands this far inside the glass

module rsq(a, h, r = 0.01) linear_extrude(h) offset(r = r) square(2 * a - 2 * r, center = true);
function fa(k) = 90 * k;
module on_face(a, d) rotate([0, 0, a]) translate([d, 0, 0]) rotate([90, 0, 90]) children();
CORNERS = [for (x = [-1, 1], y = [-1, 1]) [x * PC, y * PC]];

// ---- the snap pin and its socket ----------------------------------------------------------
// A pin 3.0 across, split by a 1.0 slot that runs 2.0 down into what it stands
// on, so each prong flexes over about 4 mm. The barb stands 0.4 proud and
// squeezes 0.25 through the throat: 2.2% strain in PLA, a firm click.
SP_D = 3.0; SP_SLIT = 1.0; SP_SLIT_IN = 2.0; SP_B = 0.4;
// throat: the length of the narrow part of the socket the barb passes
module snap_pin(throat) let (r = SP_D / 2, c = throat + 0.1, f = SP_B / tan(37), top = c + f + 0.4 + 1.2)
    difference() {
        rotate_extrude($fn = 40) polygon([
            [0, -0.01], [r, -0.01], [r, c],      // the shaft
            [r + SP_B, c + f],                   // the barb's catch, 37 deg off upright
            [r + SP_B, c + f + 0.4],
            [r - 0.5, top],                      // the lead-in
            [0, top]]);
        translate([-SP_SLIT / 2, -5, -SP_SLIT_IN]) cube([SP_SLIT, 10, top + SP_SLIT_IN + 1]);
    }
function snap_top(throat) = throat + 0.1 + SP_B / tan(37) + 1.6;
// the slot the pin's prongs flex into, cut into what the pin stands on
module snap_slit() translate([-SP_SLIT / 2, -SP_D / 2, -SP_SLIT_IN]) cube([SP_SLIT, SP_D, SP_SLIT_IN + 0.01]);
// The socket: a throat the barb squeezes through, a chamber it opens into,
// and a roof at 37 deg. Printed upright from its mouth, the chamber's floor
// faces up, so the catch is a real edge.
SK_T = 0.15;                // throat clearance round the shaft
module snap_socket(throat) let (rt = SP_D / 2 + SK_T, rc = SP_D / 2 + SP_B + 0.2, ch = 1.0)
    rotate_extrude($fn = 40) polygon([
        [0, -0.01], [rt + 0.3, -0.01], [rt, 0.4], [rt, throat],
        [rc, throat], [rc, throat + ch], [0, throat + ch + rc / tan(37)]]);
function socket_top(throat) = throat + 1.0 + (SP_D / 2 + SP_B + 0.2) / tan(37);

// ---- the frame (green) --------------------------------------------------------------------
module base() difference() {
    union() { rsq(P + RO, z0 - 1.5, LR); translate([0, 0, z0 - 1.5]) hull() { rsq(P + RO, 0.01, LR); translate([0, 0, 1.5]) rsq(P + RO - 1.5, 0.01, LR); } }
    translate([0, 0, fl]) rsq(PI_ - LIP, z0);
}
// the glass's slot: down each post and along the base between them
module glass_slots() for (k = [0 : 3]) rotate([0, 0, fa(k)])
    translate([PC - GW / 2, -(PC - GE), PZ]) cube([GW, 2 * (PC - GE), TOPZ]);
FR_THROAT = 2.0;            // the top's socket: its throat
module frame() difference() {
    union() {
        base();
        for (c = CORNERS) translate(c) cylinder(r = PR, h = TOPZ, $fn = 32);
        for (c = CORNERS) translate([c.x, c.y, TOPZ - 0.01]) rotate([0, 0, 45]) snap_pin(FR_THROAT);
    }
    glass_slots();
    for (c = CORNERS) translate([c.x, c.y, TOPZ]) rotate([0, 0, 45]) snap_slit();
    translate([0, 0, 0]) obc_engrave(7, depth = 0.8, inset = 0.15, ridges = false);
}

// ---- the top (green), in place: it prints the way up it sits ------------------------------
module rail() difference() {
    hull() { translate([0, 0, TOPZ]) rsq(P, 0.01); translate([0, 0, zr - 2]) rsq(P + RO, 2, LR); }
    translate([0, 0, TOPZ - 1]) rsq(PI_, 10);
}
module band() difference() {
    union() { translate([0, 0, zr - SH * 0.8]) hull() { rsq(BO, 0.01); translate([0, 0, SH * 0.8]) rsq(BO, 0.01); }
              translate([0, 0, zr - 0.01]) rsq(BO, BH + 0.01); }
    hull() { translate([0, 0, zr - SH * 0.8 - 0.01]) rsq(PI_, 0.01); translate([0, 0, zr]) rsq(BI, BH + 1); }
}
module top() difference() {
    union() {
        rail(); band();
        for (c = CORNERS) translate([c.x, c.y, TOPZ]) cylinder(r = PR, h = zr - TOPZ, $fn = 32);
    }
    for (c = CORNERS) translate([c.x, c.y, TOPZ]) snap_socket(FR_THROAT);
}

// ---- the glass panels (white, the scenes green), drawn flat ---------------------------------
// x across, y up from the glass's foot, z out of the glass
module panel_glass(k) translate([-PW / 2, 0, 0]) cube([PW, PH, PT]);
// 0.2 above the base's bevel, which tops out at z0: on it, the ground line
// touched the frame (2026-10-30)
module panel_art(k) translate([-W / 2, z0 + 0.2 - PZ, PT - 0.01]) linear_extrude(AD + 0.01)
    glow_clean() intersection() { square([W, HS]); landscape(k, W, HS); }
module panel_use(k) on_face(fa(k), PI_) translate([0, PZ, 0]) children();

// ---- the lid (green), the ribbon and the bow (red) -----------------------------------------
LID_THROAT = 2.0;           // the bow's socket: its throat
RW = 10;  RT = 1.6;         // the ribbon: its width and thickness
module lid() difference() {
    union() {
        rsq(P + RO, LH, LR);
        translate([0, 0, LH - 0.01]) snap_pin(RT + LID_THROAT);
    }
    translate([0, 0, -1]) difference() { rsq(BO + CL, BH + 0.3 + 1); rsq(BI - CL, BH + 3); }
    translate([0, 0, LH]) snap_slit();
}
// in place on the lid (z = 0 at the lid's underside)
RC = 0.2;                   // the ribbon's ends clear the lid's sides by this
module ribbon() difference() {
    for (r = [0, 90]) rotate([0, 0, r]) difference() {
        translate([-RW / 2, -(P + RO + RC + RT), 0]) cube([RW, 2 * (P + RO + RC + RT), LH + RT]);
        translate([-RW, -(P + RO + RC), -1]) cube([2 * RW, 2 * (P + RO + RC), LH + 1]);
    }
    translate([0, 0, LH - 1]) cylinder(r = SP_D / 2 + 0.2, h = RT + 2, $fn = 32);
}
module bow_plate() rotate([90, 0, 0]) linear_extrude(3.4, center = true) {
    for (m = [0, 1]) mirror([m, 0]) difference() {
        hull() { translate([0, 0]) square([5, 0.1]); translate([8.2, 14]) circle(4.8); }
        translate([7.6, 13]) hull() { circle(2.0); translate([0, 4.0]) circle(0.01); }
    }
    translate([-4, 0]) square([8, 2]);
}
// standing on its own foot, as it prints and as it sits on the ribbon
module bow() difference() {
    scale(1.3) {
        for (r = [45, 135]) rotate([0, 0, r]) bow_plate();
        cylinder(r = 4.2, h = 6.5, $fn = 32);
        translate([0, 0, 6.5]) scale([1, 1, 0.6]) sphere(4.2, $fn = 32);
    }
    rotate([0, 0, 45]) snap_socket(LID_THROAT);
}
assert(socket_top(LID_THROAT) < 1.3 * 6.5 - 1.2, "the bow's socket breaks through its knot");
assert(socket_top(FR_THROAT) < zr - TOPZ + BH - 1.2, "the top's socket breaks through its band");

// ---- parts -----------------------------------------------------------------------------------
GREEN = "#2F6B45"; WHITE = "#F4F1EA"; RED = "#C62F3A";
module lid_use()    translate([0, 0, zr]) lid();
module ribbon_use() translate([0, 0, zr]) ribbon();
module bow_use()    translate([0, 0, zr + LH + RT]) bow();
// prints: the top stands on its rail's lowest edge; the ribbon lies upside
// down, its cross on the plate and its ends standing up
module top_print()    translate([0, 0, -TOPZ]) top();
module ribbon_print() translate([0, 0, LH + RT]) mirror([0, 0, 1]) ribbon();
module the(p) {
    if (p == "frame") frame();
    else if (p == "top") top_print();
    else if (p == "lid") lid();
    else if (p == "ribbon") ribbon_print();
    else if (p == "bow") bow();
    else if (p == "top_use") top();
    else if (p == "lid_use") lid_use();
    else if (p == "ribbon_use") ribbon_use();
    else if (p == "bow_use") bow_use();
    for (k = [0 : 3]) {
        if (p == str("panel_", k)) union() { panel_glass(k); panel_art(k); }
        if (p == str("panel_glass_", k)) panel_glass(k);
        if (p == str("panel_art_", k)) panel_art(k);
        if (p == str("panel_", k, "_use")) panel_use(k) union() { panel_glass(k); panel_art(k); }
        if (p == str("panel_glass_", k, "_use")) panel_use(k) panel_glass(k);
        if (p == str("panel_art_", k, "_use")) panel_use(k) panel_art(k);
    }
}
if (part == "all") {
    color(GREEN) { frame(); top(); lid_use(); }
    for (k = [0 : 3]) panel_use(k) { color(WHITE) panel_glass(k); color(GREEN) panel_art(k); }
    color(RED) { ribbon_use(); bow_use(); }
} else the(part);
