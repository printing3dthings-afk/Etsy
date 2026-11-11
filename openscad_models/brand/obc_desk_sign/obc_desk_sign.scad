// OBC desk sign: Scott's OBC logo, unchanged, in gold on a black plaque that
// stands in a black base. Scott, 2026-11-11: "I want a 3d print designed of my
// logo so I can print a real one" -- the gold OBC, as a desk sign on a base.
//
// The letter outlines are traced from the logo itself (trace_obc.py), not set in
// a font: Montserrat at its best weight and spacing only overlaps the logo 85%.
// The stripes are measured from the same image: three groups, each one faint
// line and three strong ones. Strong lines are cut through the gold, so the black
// plaque shows in them, as the logo's dark lines; the faint ones are shallow and
// read as a shadow.
//
// The plaque prints flat, face up: black to the top of the plaque, gold above
// (one filament change, or an AMS). The base prints on its own, in black.
//
//   part = "plaque" | "letters" | "base" | "assembled"

include <BOSL2/std.scad>
include <stripes.scad>
include <letters_2d.scad>

part = "assembled";

logo_w   = 150;                    // letters, left to right; the gold shapes are made at this
assert(logo_w == letters_2d_logo_w, "re-run trace_obc.py with LOGO_W set to logo_w");
logo_h   = logo_w * logo_h_over_w; // 56.2 at 150
gold_h   = 2.4;                    // letters stand 12 layers proud of the plaque
faint_d  = 0.4;                    // the faint lines: 2 layers deep

plaque_t      = 5.0;               // 25 layers; the colour change is at its top
side_margin   = 16;
top_margin    = 12;
slot_depth    = 10;                // how far the plaque sits in the base
bottom_margin = slot_depth + 10;   // so 10 mm of black shows under the letters
plaque_w = logo_w + 2 * side_margin;
plaque_h = logo_h + top_margin + bottom_margin;
plaque_r = 6;                      // corner radius, seen face on
edge_ch  = 0.8;                    // chamfer round the plaque's front edge

base_w   = plaque_w + 14;
base_d   = 46;
base_h   = slot_depth + 4;         // 4 mm floor under the slot
base_ch  = 1.6;                    // chamfer on the base's top edges
slot_gap = 0.5;                    // total clearance across the slot
slot_end = 0.6;                    // and along it
lean     = 8;                      // the slot leans back this far; the gap adds about 2.9 more
slot_y   = -4;                     // slot centre, from the base's centre (+y is the back)

// ---- the plaque, lying face up: x across, y up the face, z out of it ----

letters_y = plaque_h / 2 - top_margin - logo_h / 2;  // letters' centre, from the plaque's centre

// The gold, as two flat shapes made by trace_obc.py at the sign's real size:
// gold_deep() is the letters less the strong stripes, gold_top() less the faint ones
// too, both with anything narrower than 1.2 mm removed (it stands 2.4 proud, so 3
// beads). They're stacked: the faint lines are the top faint_d of gold missing.
module letters() {
    translate([0, letters_y, plaque_t]) {
        linear_extrude(gold_h - faint_d) gold_deep();
        translate([0, 0, gold_h - faint_d]) linear_extrude(faint_d) gold_top();
    }
}

module plaque() {
    hull() {
        linear_extrude(plaque_t - edge_ch) rect([plaque_w, plaque_h], rounding = plaque_r);
        linear_extrude(plaque_t) rect([plaque_w - 2 * edge_ch, plaque_h - 2 * edge_ch], rounding = plaque_r - edge_ch);
    }
}

// ---- the base, as printed: z up, +y to the back ----

module base() {
    difference() {
        hull() {
            linear_extrude(base_h - base_ch) rect([base_w, base_d], rounding = 4);
            linear_extrude(base_h) rect([base_w - 2 * base_ch, base_d - 2 * base_ch], rounding = 4 - base_ch);
        }
        // the slot: the plaque's thickness plus the gap, leaning back, floor at z = 4
        translate([0, slot_y, base_h - slot_depth]) rotate([-lean, 0, 0])
            translate([0, 0, slot_depth + 2]) cube([plaque_w + slot_end, plaque_t + slot_gap, 2 * slot_depth + 4], center = true);
    }
}

// ---- standing, for renders and checks: plaque face to -y, resting on the slot floor ----

module standing(which) {
    // rotate([90,0,0]) turns the face (+z) to the front (-y) and the plaque's height
    // to z; then centre its thickness on the slot, stand it on the slot floor, lean it
    translate([0, slot_y, base_h - slot_depth]) rotate([-lean, 0, 0])
        translate([0, plaque_t / 2, plaque_h / 2]) rotate([90, 0, 0]) {
            if (which == "plaque") plaque();
            if (which == "letters") letters();
        }
}

if (part == "plaque") plaque();
if (part == "letters") letters();
if (part == "sign") union() { plaque(); letters(); }  // the plaque as printed, for the gates
if (part == "base") base();
if (part == "standing_plaque") standing("plaque");
if (part == "standing_letters") standing("letters");
if (part == "assembled") { base(); standing("plaque"); standing("letters"); }
