include <BOSL2/std.scad>

/* ============================================================
   OB-FIDGET-01 -- print-in-place multi-mechanism fidget card, v1
   A chunky rounded "card" body with THREE genuinely different,
   independently-verified moving mechanisms, all printed already
   assembled:
     1. Edge-mounted knurled ROLLER WHEEL (thumb scroll wheel)
     2. Top-face SLIDE SWITCH (T-slot captured slider)
     3. Vertical PRESS BUTTON (captured plunger, no spring/detent
        in v1 -- press down, pull back up by the exposed lip)
   Scoped down from a 12-mechanism reference (joystick, spinner
   disc, rocker switch, multiple dials) to 3 mechanisms built and
   verified properly -- each moving part gets the same rigorous
   render + connected-component + ray-cast overlap check as the
   cable clip hinge (Technique 24). More mechanisms are a natural
   v2 once this base is confirmed good.
   ============================================================ */

// ---- card body ----
card_w   = 90;    // X
card_d   = 55;    // Y
card_h   = 14;    // Z
corner_r = 5;      // cosmetic vertical-edge rounding (edges="Z")

// ---- keychain hole (front-right corner) ----
kc_r = 2.6;
kc_x = card_w - 10;
kc_y = 10;   // near the FRONT-right corner, not back-right -- a first
             // placement (card_d - 10) put it only 5.8mm from the button's
             // own center while their radii sum to 7.8mm, so the two
             // cuts visibly merged into one open eclipse-shaped hole
             // instead of two clean circular ones. Cuts overlapping is
             // harmless to the difference() itself (no interference bug),
             // but it compromises the button's own bore -- caught by
             // actually looking at a top-down render, not by any of the
             // structural (component/ray-cast) checks, which only cover
             // whether MOVING PARTS interpenetrate, not whether two
             // static cuts on the same body make sense next to each other.

// ---- Mechanism 1: edge roller wheel (front edge, y=0) ----
wheel_r     = 5;
wheel_w     = 14;
wheel_pin_r = 2;
wheel_clear = 0.4;
wheel_x     = 20;             // wheel center X
wheel_z     = card_h / 2;     // wheel center Z -- mid-height
wheel_end_gap    = 1;         // axial clearance, wheel <-> notch end wall
wheel_anchor_len = 4;         // axle embed depth into card beyond the notch
notch_r   = wheel_r + wheel_clear;
notch_len = wheel_w + 2 * wheel_end_gap;
axle_len  = notch_len + 2 * wheel_anchor_len;
n_knurl   = 20;
knurl_depth = 0.5;

// ---- Mechanism 2: top-face slide switch (T-slot) ----
slide_x       = 58;           // channel center X
slide_y0      = 8;            // channel start Y
slide_travel  = 10;           // how far the slider can move
slide_len_body = 10;          // slider's own length along Y
slide_channel_len = slide_travel + slide_len_body;
slide_neck_w  = 4;
slide_body_w  = 9;
slide_neck_depth = 2.2;
slide_body_depth = 4;
slide_clear   = 0.3;
slide_knob_protrude = 1.5;

// ---- Mechanism 3: press button (captured plunger) ----
btn_x = 75;
btn_y = 42;
btn_neck_r   = 3.2;
btn_neck_depth = 4;
btn_wide_r   = 5.2;
btn_floor    = 2.5;             // solid floor left under the cavity
btn_clear    = 0.4;
btn_travel   = btn_neck_depth - 0.5;  // plunger can travel down this far
                                        // before its flange bottoms out

// ---- grip texture strip (purely tactile, no moving parts) ----
grip_x0 = 30; grip_x1 = 46; grip_y = 44;
grip_n = 7; grip_depth = 0.6;

mark_depth = 0.6;

module brand_mark() {
    // negative engraved mark, bottom face -- standing rule 2026-08-27.
    // mirror([0,1,0]) confirmed correct for this exact pattern (Technique 4).
    translate([card_w / 2, card_d / 2, -0.5])
        linear_extrude(height = mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 4.5, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

// ============================================================
// Mechanism 1 -- roller wheel
// ============================================================

module wheel_notch() {
    // Cylindrical bite out of the front edge (y=0), radius bigger than the
    // wheel so it spins freely. Centered exactly AT y=0 so roughly half the
    // wheel sits outside the card body (reachable by a thumb) and half
    // inside (captured -- can't be pulled sideways out of the card).
    translate([wheel_x - notch_len / 2, 0, wheel_z])
        rotate([0, 90, 0]) cylinder(r = notch_r, h = notch_len, $fn = 40);
}

module wheel_axle() {
    // Continuous rod, embedded wheel_anchor_len into solid card material on
    // BOTH sides of the notch -- fused to the CARD, added back via union()
    // outside any further cut (Technique 24's lesson: nothing downstream
    // may touch this).
    translate([wheel_x - axle_len / 2, 0, wheel_z])
        rotate([0, 90, 0]) cylinder(r = wheel_pin_r, h = axle_len, $fn = 24);
}

function knurl_pts(r) = [for (a = [0 : 360 / (n_knurl * 6) : 359.999])
    let(rr = r - knurl_depth * (1 - abs(cos(a * n_knurl / 2))))
    [rr * cos(a), rr * sin(a)]
];

module wheel() {
    // A SEPARATE floating solid (not fused to anything) -- captured
    // between the axle (through its bore) and the notch's own end walls
    // (through its outer radius, smaller than the notch's own radius).
    translate([wheel_x - wheel_w / 2, 0, wheel_z])
        rotate([0, 90, 0])
            difference() {
                linear_extrude(height = wheel_w) polygon(knurl_pts(wheel_r));
                translate([0, 0, -1])
                    cylinder(r = wheel_pin_r + wheel_clear, h = wheel_w + 2, $fn = 28);
            }
}

// ============================================================
// Mechanism 2 -- slide switch (T-slot)
// ============================================================

// z=0 is the neck/body TRANSITION -- neck spans local z=[0,neck_up] (up
// toward the surface), body spans local z=[-body_d,0] (down into the
// card). Both callers below translate to the SAME world Z
// (card_h - slide_neck_depth) for this z=0 reference, so their
// transition points can never drift apart -- a first version gave the
// channel and slider each their own independently-computed "top of neck"
// offset (with the slider's offset trying to account for its knob
// protrusion by adding to the WRONG end of the calculation) and their
// transition points ended up 1.5mm apart, leaving the slider's wide body
// section reaching into a Z-range where the card only had the narrow
// neck cut -- a real interference, confirmed by a connected-component
// check (each part alone was just the card silently swallowing the
// slider and plunger whole).
// Profile's local y is NEGATED for "up" (neck) and POSITIVE for "down"
// (body) -- NOT the more intuitive other way around. This is required by
// rotate([-90,0,0]) below: rotating -90 about X maps local (y,z) -> world
// (Y=z, Z=-y) -- confirmed empirically by rendering slide_channel() alone
// and reading its real bounding box off the STL, not by trusting hand-
// derived rotation matrices a second time this session (Technique 24's
// Bug 2 already burned time on exactly this kind of mistake once). A
// first attempt used rotate([90,0,0]) (the "obvious" sign) with this same
// profile and it put the ENTIRE channel at world Y=[-12,8] instead of the
// intended [8,28] -- the extrusion direction was reversed, not just the
// depth axis. Switching to rotate([-90,0,0]) fixed the Y direction but
// then flipped Z (world_Z = -local_y instead of +local_y), so the
// profile's own sign convention has to be flipped to compensate, which is
// what this ordering already does.
function tslot_profile(neck_w, body_w, neck_up, body_d) = [
    [-neck_w / 2, -neck_up], [neck_w / 2, -neck_up],
    [neck_w / 2, 0], [body_w / 2, 0],
    [body_w / 2, body_d], [-body_w / 2, body_d],
    [-body_w / 2, 0], [-neck_w / 2, 0],
];

module slide_channel() {
    // cut_extra extends the neck slightly ABOVE the surface for a clean
    // through-slot -- doesn't affect the transition point (z=0 stays at
    // world card_h - slide_neck_depth regardless of cut_extra).
    cut_extra = 1;
    profile = tslot_profile(slide_neck_w, slide_body_w, slide_neck_depth + cut_extra, slide_body_depth);
    translate([slide_x, slide_y0, card_h - slide_neck_depth])
        rotate([-90, 0, 0]) linear_extrude(height = slide_channel_len)
            polygon(profile);
}

module slider() {
    // SEPARATE floating solid, shorter than the channel by slide_travel --
    // its wide "body" section can't lift up through the channel's own
    // narrower neck opening, but is free to slide the remaining distance.
    // Neck extends slide_neck_depth (to reach the surface, matching the
    // channel's own transition) PLUS slide_knob_protrude (to poke above it).
    //
    // vgap shifts the slider's own transition point (shoulder) vgap below
    // the channel's own transition (shelf) -- both were otherwise landing
    // at the EXACT same world Z (card_h - slide_neck_depth), an exact
    // knife-edge coincidence between the card's cut boundary and the
    // slider's own solid boundary that the connected-component check
    // showed fusing the two together (real, not just a rendering
    // artifact -- confirmed the same way as every other interference in
    // this build, by checking for a genuinely separate component after
    // the fix). neck_up gets +vgap so the knob's world height above the
    // surface is unchanged; body depth is untouched since translate_z and
    // neck_up both shift by vgap and cancel out at the body's own floor.
    // body_d uses (slide_body_depth - slide_clear - vgap), NOT just
    // (- slide_clear) -- with only "- slide_clear", the transition-point
    // drop of vgap and the body-depth reduction of slide_clear numerically
    // canceled out (since vgap == slide_clear == 0.3 here), landing the
    // slider's own floor at EXACTLY the channel's floor Z with zero real
    // gap -- a hairline corner tangency at the two X-edges, confirmed by
    // ray-casting: real interior overlaps vote ~20/21 consistently across
    // random directions (see Technique 24's hinge bugs), this one voted
    // an exact coin-flip ~11/21, the signature of a point sitting ON a
    // boundary rather than genuinely inside or outside it.
    vgap = 0.3;
    profile = tslot_profile(slide_neck_w - 2 * slide_clear, slide_body_w - 2 * slide_clear,
                             slide_neck_depth + slide_knob_protrude + vgap, slide_body_depth - slide_clear - vgap);
    translate([slide_x, slide_y0 + slide_travel / 2, card_h - slide_neck_depth - vgap])
        rotate([-90, 0, 0]) linear_extrude(height = slide_len_body)
            polygon(profile);
}

// ============================================================
// Mechanism 3 -- press button (captured plunger)
// ============================================================

module btn_bore() {
    // Two-diameter bore: narrow neck at the top (surface opening), wider
    // cavity below -- the plunger's flange lives in the wide section and
    // cannot pull up through the narrow neck.
    translate([btn_x, btn_y, card_h - btn_neck_depth])
        cylinder(r = btn_neck_r, h = btn_neck_depth + 1, $fn = 32);
    translate([btn_x, btn_y, btn_floor])
        cylinder(r = btn_wide_r, h = card_h - btn_neck_depth - btn_floor, $fn = 32);
}

module plunger() {
    // SEPARATE floating solid: wide flange (captured in the wide cavity)
    // + narrow stem (rides in the neck, pokes above the surface for a
    // thumb to press/pull). Rest position: flange sitting most of the way
    // up the wide cavity, near the shoulder -- leaves btn_travel of real
    // downward press distance before the flange bottoms out on the floor.
    // flange_z (bottom of flange) is measured DOWN from the shoulder
    // (card_h - btn_neck_depth) by flange_h + a 0.3mm clearance margin --
    // a first version added the 0.3 instead of subtracting it, which
    // pushed the flange's TOP 0.3mm PAST the shoulder into the narrow
    // neck's own Z-range, where the wide flange (radius btn_wide_r-clear)
    // doesn't fit -- a real interference with the surrounding card
    // material, confirmed the same way as the slider bug above.
    flange_h = 3;
    flange_z = card_h - btn_neck_depth - flange_h - 0.3;   // just below the shoulder
    stem_top = card_h + 1;                                  // pokes 1mm proud
    translate([btn_x, btn_y, flange_z])
        cylinder(r = btn_wide_r - btn_clear, h = flange_h, $fn = 32);
    translate([btn_x, btn_y, flange_z])
        cylinder(r = btn_neck_r - btn_clear, h = stem_top - flange_z, $fn = 28);
}

// ============================================================
// Grip texture (no moving parts)
// ============================================================

module grip_texture() {
    for (i = [0 : grip_n - 1])
        translate([grip_x0 + i * (grip_x1 - grip_x0) / (grip_n - 1), grip_y - 6, card_h - grip_depth])
            cube([1.4, 12, grip_depth + 0.5]);
}

// ============================================================
// Card body
// ============================================================

module card_body() {
    union() {
        difference() {
            cuboid([card_w, card_d, card_h], rounding = corner_r, edges = "Z",
                   anchor = BOTTOM + FRONT + LEFT);
            wheel_notch();
            translate([kc_x, kc_y, -1]) cylinder(r = kc_r, h = card_h + 2, $fn = 24);
            slide_channel();
            btn_bore();
            grip_texture();
            brand_mark();
        }
        // axle fused to the card, added OUTSIDE the difference() above --
        // Technique 24: nothing downstream may cut it.
        wheel_axle();
    }
}

union() {
    card_body();
    wheel();
    slider();
    plunger();
}
