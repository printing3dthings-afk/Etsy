// Victorian steam train (2026-10-14), a village accessory from the second
// batch of studies (../concepts/accessories2_scene.jpg).
//
// A little tank engine and one carriage on a snowy track. The engine: a green
// boiler with white bands and dome, a slate smokebox with a wreath and red bow
// on its door, a chimney, a green cab with a slate roof, a bunker of coal, a
// red frame on six slate wheels. The carriage: red, four lit windows a side,
// a slate roof. Snow on both roofs; slate rails on red sleepers. On a long
// soft blob of snow, the maker's mark under it.
//
// Printed upright with no support. The boiler is sunk into the frame as far
// as the line where its curve turns 45 degrees; the wheels are discs on the
// frame's sides, sunk in the rails until their curve leaves them at 42; the
// frame and the roofs step out at SH; every window is cut in with a sloping
// head; the snow on a roof thickens towards its ridge.
//
// The engine faces +x.
//
// part = body | roof | trim | accent | all | union  (see ../accessory_lib.scad)
include <../../relief_lib.scad>
include <../accessory_lib.scad>

part = "all";
SH = 1.2;

zb = 3.2;                   // the snow's top
// ---- the track ----------------------------------------------------------------------------------
GY = 4.3;                   // the rails' centres
RLW = 1.4;                  // a rail's width
z_rt = zb + 1.0;            // the rails' top
XT0 = -40; XT1 = 19;        // the track's ends, before the base's edge trims them
// Everything standing on the snow starts at z0, on a layer line: from zb - 0.3,
// mid-layer, the layer split between white and the part's colour and the
// slicer dropped the white under all 15 (print_fidelity, 2026-10-14).
z0 = zb - 0.4;
module rails() for (s = [-1, 1]) translate([XT0, s * GY - RLW / 2, z0]) cube([XT1 - XT0, RLW, z_rt - z0]);
// inside the base's rounded ends: at x -40 the end one was clipped to a sliver
module sleepers() for (x = [-36 : 4 : 14]) translate([x, -5.6, z0]) cube([1.8, 11.2, 0.9]);

// ---- frames and wheels ---------------------------------------------------------------------------
FY = 3.8;                   // the frame's half-width, between the wheels
WT = 1.0;                   // a wheel's thickness: from FY out
WR = 2.6;                   // a wheel's radius
z_wc = z_rt + WR * 0.67;    // its centre: its curve leaves the rail 42 deg off upright
z_f = 9.5;                  // the footplate's top
FO = FY + WT;               // the footplate's half-width, stepped out over the wheels at SH
module frame(x0, x1) {
    translate([x0, -FY, z0]) cube([x1 - x0, 2 * FY, z_f - z0]);
    // its edge 0.8 thick: stepped out to a knife edge, the footplate along the
    // boiler was a sliver 0.1 thick
    hull() {
        translate([x0, -FY, z_f - 0.8 - (FO - FY) * SH]) cube([x1 - x0, 2 * FY, 0.01]);
        translate([x0, -FO, z_f - 0.8]) cube([x1 - x0, 2 * FO, 0.8]);
    }
}
// on a side face d out, toward -y (s = 1) or +y (s = -1): 2D x along x, y up, z out
module yface(s, d) mirror([0, s > 0 ? 0 : 1, 0]) translate([0, -d, 0]) rotate([90, 0, 0]) children();
// on an end face d out along +x: 2D x along y, y up, z out
module xface(d) translate([d, 0, 0]) rotate([90, 0, 90]) children();
module wheels(xs) for (s = [-1, 1], x = xs) yface(s, FY - 0.01) translate([x, z_wc]) cylinder(r = WR, h = WT + 0.01, $fn = 40);
module hubs(xs) for (s = [-1, 1], x = xs) yface(s, FO) art_skirt(0.4, 1) translate([x, z_wc]) circle(0.8, $fn = 20);

// ---- the engine ----------------------------------------------------------------------------------
EX0 = -13; EX1 = 16;        // its frame
EW = [9.5, 4.0, -1.5];      // its wheels
BR = 4.6;                   // the boiler
z_bc = z_f + BR * cos(45);  // its centre: its 45 deg line on the footplate
BX0 = 3; BX1 = 11;          // the boiler, cab to smokebox
SR = 4.9;                   // the smokebox
SX1 = 15;                   // its front
module xcyl(x0, x1, r) translate([x0, 0, z_bc]) rotate([0, 90, 0]) cylinder(r = r, h = x1 - x0, $fn = 48);
module boiler() xcyl(BX0 - 0.01, BX1 + 0.01, BR);
module bands() for (x = [BX0 + 2.4, BX0 + 5.4]) xcyl(x, x + 1.3, SR);   // 0.9 wide, their rims were under one bead
module smokebox() xcyl(BX1, SX1, SR);
// the chimney, its cap flaring at SH
CX = 13.0; z_ch = 23.0;
module chimney() translate([CX, 0, z_bc]) {
    cylinder(r = 1.5, h = z_ch - z_bc, $fn = 24);
    translate([0, 0, z_ch - z_bc - 0.01]) cylinder(r1 = 1.5, r2 = 2.3, h = 0.8 * SH, $fn = 24);
    translate([0, 0, z_ch - z_bc + 0.8 * SH - 0.02]) cylinder(r = 2.3, h = 1.2, $fn = 24);    // at 0.8 its rim was under one bead
}
module dome() translate([7.0, 0, z_bc + BR - 0.6]) sphere(2.0, $fn = 32);
// the cab: solid, its windows cut in; its roof stepping out 0.8 at SH all
// round, corners rounded so the corners climb SH too, then arched
CB0 = -6; CB1 = BX0;        // the cab
z_cab = 20.5;               // its walls' top
module rrect(x0, x1, y, r) translate([(x0 + x1) / 2, 0]) offset(r = r, $fn = 24) square([x1 - x0 - 2 * r, 2 * y - 2 * r], center = true);
module slab(z, h = 0.01) translate([0, 0, z]) linear_extrude(h) children();
module cab() difference() {
    translate([CB0, -FO, z_f - 0.01]) cube([CB1 - CB0, 2 * FO, z_cab - z_f + 0.01]);
    for (s = [-1, 1]) yface(s, FO) engrave_in(0.8) translate([-1.5, 14.6]) parch2d(2.2, 1.0);    // its crown 3.7 up
    xface(CB1) engrave_in(0.8) for (y = [-2.8, 2.8]) translate([y, 18.4]) tear2d(0.75);
}
// a roof: from the walls' outline at z0, out 0.8 at SH, an edge EE tall, then
// up to a ridge along x RH higher; at 0.4 the eave was under one bead
EE = 0.9;
module roof_over(x0, x1, y, z0, rh) hull() {
    slab(z0) rrect(x0, x1, y, 1.2);
    slab(z0 + 0.8 * SH, EE) rrect(x0 - 0.8, x1 + 0.8, y + 0.8, 2.0);
    translate([x0 - 0.8, -0.5, z0 + 0.8 * SH + EE + rh]) cube([x1 - x0 + 1.6, 1.0, 0.01]);
}
// snow on a roof: a tent from the roof's outline at z_s to its ridge, 0.8
// higher, so it thickens toward the ridge and faces up everywhere
module roof_snow(x0, x1, y, z0, rh, f) let (zs = z0 + 0.8 * SH + EE + rh * f, ys = (y + 0.8) * (1 - f))
    hull() {
        translate([x0 - 0.8 + 0.6, -ys, zs - 0.2]) cube([x1 - x0 + 0.4, 2 * ys, 0.01]);
        translate([x0 - 0.8 + 0.6, -0.5, z0 + 0.8 * SH + EE + rh + 0.8]) cube([x1 - x0 + 0.4, 1.0, 0.01]);
    }
// the bunker behind the cab, heaped with coal
module bunker() translate([EX0, -FO, z_f - 0.01]) cube([CB0 - EX0 + 0.01, 2 * FO, 5.0]);
module coal() for (i = [0 : 13]) let (x = EX0 + 1.0 + (i % 5) * 1.35, y = -3.2 + floor(i / 5) * 3.0 + 0.4 * jit(i, 1))
    translate([x, y, z_f + 5.0 - 0.3]) scale([1, 1, 0.6]) sphere(1.0, $fn = 12);
function jit(i, k) = (((i * 37 + k * 11) % 17) / 16 - 0.5);

// the wreath on the smokebox door, its bow red
WZ = z_bc - 0.2;
module wreath2d() translate([0, WZ]) difference() { circle(2.2, $fn = 40); circle(0.7, $fn = 32); }
module bow2d() translate([0, WZ + 2.0]) {
    for (m = [0, 1]) mirror([m, 0]) hull() { translate([0.4, 0]) circle(0.7, $fn = 20); translate([1.4, 0.4]) circle(0.75, $fn = 20); }
    circle(0.75, $fn = 20);
}

// ---- the carriage --------------------------------------------------------------------------------
KX0 = -36; KX1 = -14.5;     // its frame
KW = [-33, -17.5];          // its wheels
z_kt = 19.0;                // its walls' top
module carriage() difference() {
    translate([KX0, -FO, z_f - 0.01]) cube([KX1 - KX0, 2 * FO, z_kt - z_f + 0.01]);
    for (s = [-1, 1]) yface(s, FO) engrave_in(0.5) windows2d();
}
module windows2d() for (x = [KX0 + 3.4 : 4.9 : KX1 - 2]) translate([x, 12.2]) parch2d(2.4, 1.8);    // crowns 4.0 up
// the windows lit: white panes behind the cut
module panes() for (s = [-1, 1]) yface(s, FO - 0.5) translate([0, 0, -0.8]) linear_extrude(0.81) windows2d();

// ---- the snow -----------------------------------------------------------------------------------
BX = -10.5;                 // the base's middle
module base2d() hull() for (x = [BX - 19, BX + 19]) translate([x, 0]) circle(r = 13, $fn = 64);
module base2d_in() offset(delta = -2.4) base2d();
module base() difference() {
    union() {
        snow_base(zb) base2d();
        clip_to() { union() { drift([BX - 26, 9, zb], [4, 2.5, 0.9]); drift([BX + 22, -9, zb], [3.5, 2.5, 0.9]); } base2d_in(); }
    }
    brand_mark([BX, 0], 5.0);
}

RH_C = 2.2; RH_K = 2.4;     // the roofs' rise to their ridges
module raw(p) {
    if (p == "body") {
        frame(EX0, EX1); frame(KX0, KX1); carriage(); bunker();
        clip_to() { sleepers(); base2d_in(); }
        xface(SX1 - 0.01) art_skirt(1.0, 1) bow2d();
    }
    if (p == "roof") {
        wheels(EW); wheels(KW); smokebox(); chimney(); coal();
        roof_over(CB0, CB1, FO, z_cab, RH_C); roof_over(KX0, KX1, FO, z_kt, RH_K);
        clip_to() { rails(); base2d_in(); }
    }
    if (p == "trim") {
        base(); bands(); dome(); hubs(EW); hubs(KW); panes();
        roof_snow(CB0, CB1, FO, z_cab, RH_C, 0.45); roof_snow(KX0, KX1, FO, z_kt, RH_K, 0.45);
    }
    if (p == "accent") {
        boiler(); cab();
        difference() { xface(SX1 - 0.01) art_skirt(1.0, 1) wreath2d(); xface(SX1 - 0.01) art_skirt(1.0, 1) bow2d(); }
    }
}
emit();
