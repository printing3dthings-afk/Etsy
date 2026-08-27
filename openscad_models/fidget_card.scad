include <BOSL2/std.scad>

/* ============================================================
   OB-FIDGET-01 -- print-in-place multi-mechanism fidget card, v2
   Expanded from v1's 3 mechanisms per Scott's "not nearly enough on
   it" feedback. Now 8 interactive zones, built from 3 proven capture
   patterns (Technique 22 axle+sleeve, T-slot neck+body, and a
   flanged-bore capture used 3 different ways):
     1-2. Two edge-mounted knurled ROLLER WHEELS (front + back edges)
     3.   Top-face SLIDE SWITCH (T-slot captured slider)
     4.   Rotating DIAL knob (flanged disc, spins freely in place)
     5.   JOYSTICK (same flange capture as the dial, looser neck
          clearance for wiggle, ball-topped stem)
     6-8. Three captured PRESS BUTTONS (plunger, no spring in v1)
     Plus: a decorative zigzag MAZE groove and a grip texture strip
     (both purely tactile, no moving parts), and a keychain hole.
   Every position below was validated pairwise in a standalone Python
   bounding-box check BEFORE being written here (Technique 25's
   lesson: passing structural/overlap checks on MOVING PARTS doesn't
   catch a bad LAYOUT between static features either -- the keychain
   hole and one button visibly merged in v1 for exactly this reason).
   ============================================================ */

// ---- card body ----
card_w   = 105;   // X
card_d   = 65;    // Y
card_h   = 15;    // Z
corner_r = 5;      // cosmetic vertical-edge rounding (edges="Z")

// ---- keychain hole ----
kc_r = 2.6;
kc_x = 98;
kc_y = 8;

// ---- shared hinge-style rotation clearance (Technique 22/24 pattern) ----
pin_r       = 2;
hinge_clear = 0.4;

// ============================================================
// Mechanism: edge roller wheel (reusable at any Y edge)
// ============================================================
wheel_r     = 5;
wheel_w     = 14;
wheel_end_gap    = 1;
wheel_anchor_len = 4;
notch_r   = wheel_r + hinge_clear;
notch_len = wheel_w + 2 * wheel_end_gap;
axle_len  = notch_len + 2 * wheel_anchor_len;
n_knurl   = 20;
knurl_depth = 0.5;

wheel1_x = 25;  wheel1_y = 0;       wheel1_z = card_h / 2;
wheel2_x = 80;  wheel2_y = card_d;  wheel2_z = card_h / 2;

module wheel_notch(wx, wy, wz) {
    // Full cylinder centered exactly AT the edge (wy=0 or wy=card_d) so
    // roughly half the wheel sits outside the card (thumb-reachable) and
    // half inside (captured -- can't be pulled sideways out).
    translate([wx - notch_len / 2, wy, wz])
        rotate([0, 90, 0]) cylinder(r = notch_r, h = notch_len, $fn = 40);
}

module wheel_axle(wx, wy, wz) {
    translate([wx - axle_len / 2, wy, wz])
        rotate([0, 90, 0]) cylinder(r = pin_r, h = axle_len, $fn = 24);
}

function knurl_pts(r) = [for (a = [0 : 360 / (n_knurl * 6) : 359.999])
    let(rr = r - knurl_depth * (1 - abs(cos(a * n_knurl / 2))))
    [rr * cos(a), rr * sin(a)]
];

module wheel(wx, wy) {
    translate([wx - wheel_w / 2, wy, card_h / 2])
        rotate([0, 90, 0])
            difference() {
                linear_extrude(height = wheel_w) polygon(knurl_pts(wheel_r));
                translate([0, 0, -1])
                    cylinder(r = pin_r + hinge_clear, h = wheel_w + 2, $fn = 28);
            }
}

// ============================================================
// Mechanism: slide switch (T-slot) -- unchanged from v1
// ============================================================
slide_x       = 30;
slide_y0      = 8;
slide_travel  = 10;
slide_len_body = 10;
slide_channel_len = slide_travel + slide_len_body;
slide_neck_w  = 4;
slide_body_w  = 9;
slide_neck_depth = 2.2;
slide_body_depth = 4;
slide_clear   = 0.3;
slide_knob_protrude = 1.5;

// z=0 is the neck/body TRANSITION -- see fidget_card v1 history for why
// this shared-reference convention matters (a first version gave the
// channel and slider independently-computed transition offsets and they
// drifted 1.5mm apart, letting the slider's wide body reach into the
// card's narrow neck region).
function tslot_profile(neck_w, body_w, neck_up, body_d) = [
    [-neck_w / 2, -neck_up], [neck_w / 2, -neck_up],
    [neck_w / 2, 0], [body_w / 2, 0],
    [body_w / 2, body_d], [-body_w / 2, body_d],
    [-body_w / 2, 0], [-neck_w / 2, 0],
];

module slide_channel() {
    cut_extra = 1;
    profile = tslot_profile(slide_neck_w, slide_body_w, slide_neck_depth + cut_extra, slide_body_depth);
    translate([slide_x, slide_y0, card_h - slide_neck_depth])
        rotate([-90, 0, 0]) linear_extrude(height = slide_channel_len)
            polygon(profile);
}

module slider() {
    vgap = 0.3;
    profile = tslot_profile(slide_neck_w - 2 * slide_clear, slide_body_w - 2 * slide_clear,
                             slide_neck_depth + slide_knob_protrude + vgap, slide_body_depth - slide_clear - vgap);
    translate([slide_x, slide_y0 + slide_travel / 2, card_h - slide_neck_depth - vgap])
        rotate([-90, 0, 0]) linear_extrude(height = slide_len_body)
            polygon(profile);
}

// ============================================================
// Mechanism: press buttons (captured plunger) -- reusable at any (x,y)
// ============================================================
btn_neck_r   = 2.6;
btn_neck_depth = 4;
btn_wide_r   = 4.4;
btn_floor    = 2.5;
btn_clear    = 0.4;

btn1_x = 49; btn1_y = 48;
btn2_x = 62; btn2_y = 48;
btn3_x = 75; btn3_y = 48;

module btn_bore(bx, by) {
    translate([bx, by, card_h - btn_neck_depth])
        cylinder(r = btn_neck_r, h = btn_neck_depth + 1, $fn = 32);
    translate([bx, by, btn_floor])
        cylinder(r = btn_wide_r, h = card_h - btn_neck_depth - btn_floor, $fn = 32);
}

module plunger(bx, by) {
    // flange_z kept BELOW the shoulder by a real margin (a first version
    // added instead of subtracted this margin, pushing the flange PAST
    // the shoulder into the narrow neck's own space -- a real
    // interference, not just cosmetic).
    flange_h = 3;
    flange_z = card_h - btn_neck_depth - flange_h - 0.3;
    stem_top = card_h + 1;
    translate([bx, by, flange_z])
        cylinder(r = btn_wide_r - btn_clear, h = flange_h, $fn = 32);
    translate([bx, by, flange_z])
        cylinder(r = btn_neck_r - btn_clear, h = stem_top - flange_z, $fn = 28);
}

// ============================================================
// Mechanism: rotating dial knob (flanged disc, free 360 deg spin)
// Same flange-in-cavity capture as the button, but the flange simply
// RESTS on the cavity floor (no travel needed) and the whole assembly
// is sized for rotation clearance, not vertical clearance.
// ============================================================
dial_x = 15; dial_y = 48;
dial_neck_r = 3.5;
dial_neck_depth = 3;
dial_wide_r = 6.5;
dial_floor  = 3;         // solid material left under the cavity
dial_clear  = 0.4;
dial_flange_h = 3;
dial_knob_protrude = 2;

module dial_bore() {
    translate([dial_x, dial_y, card_h - dial_neck_depth])
        cylinder(r = dial_neck_r, h = dial_neck_depth + 1, $fn = 36);
    translate([dial_x, dial_y, dial_floor])
        cylinder(r = dial_wide_r, h = card_h - dial_neck_depth - dial_floor, $fn = 36);
}

module dial() {
    // flange floats mid-cavity with a real gap on BOTH ends (floor AND
    // shoulder) -- a first version started the flange exactly AT
    // dial_floor (the cavity's own floor Z), an exact coincidence that
    // the slide-switch slider already proved genuinely fuses two parts
    // in CGAL's union() (not just a boundary ray-cast artifact -- that
    // one was confirmed fused in the real connected-component check
    // before its own floor gap was added). Same fix here: a real
    // flange_gap on each side, not flush against either boundary.
    flange_gap = 0.4;
    cavity_h = (card_h - dial_neck_depth) - dial_floor;
    flange_h = cavity_h - 2 * flange_gap;
    flange_z0 = dial_floor + flange_gap;
    stem_top = card_h + dial_knob_protrude;
    difference() {
        union() {
            translate([dial_x, dial_y, flange_z0])
                cylinder(r = dial_wide_r - dial_clear, h = flange_h, $fn = 36);
            translate([dial_x, dial_y, flange_z0])
                linear_extrude(height = stem_top - flange_z0)
                    polygon(knurl_pts(dial_neck_r - dial_clear));
        }
        // a shallow pointer notch on the exposed top face -- purely
        // cosmetic, gives the knob a visible "rotation position" marker.
        translate([dial_x, dial_y + dial_neck_r - 1, stem_top - 0.6])
            cube([1.6, dial_neck_r, 1], center = true);
    }
}

// ============================================================
// Mechanism: joystick -- same flange capture as the dial, but with
// extra radial clearance in the neck (so the stem can wiggle side to
// side, not just spin) and a ball top instead of a knurled disc.
// ============================================================
joy_x = 33; joy_y = 48;
joy_neck_r = 3.2;          // bore neck radius -- generously bigger than
                            // the stem below, on purpose (wiggle room)
joy_stem_r = 2.2;
joy_neck_depth = 4;
joy_wide_r = 6;
joy_floor = 3;
joy_clear = 0.4;
joy_ball_r = 4;
joy_stick_len = 6;          // stem length above the flange, before the ball

module joy_bore() {
    translate([joy_x, joy_y, card_h - joy_neck_depth])
        cylinder(r = joy_neck_r, h = joy_neck_depth + 1, $fn = 32);
    translate([joy_x, joy_y, joy_floor])
        cylinder(r = joy_wide_r, h = card_h - joy_neck_depth - joy_floor, $fn = 32);
}

module joystick() {
    // Same floor-gap fix as dial() above -- flange floats with real
    // clearance on both ends instead of starting flush at joy_floor.
    flange_gap = 0.4;
    cavity_h = (card_h - joy_neck_depth) - joy_floor;
    flange_h = cavity_h - 2 * flange_gap;
    flange_z0 = joy_floor + flange_gap;
    stem_base_z = flange_z0 + flange_h;
    stem_top_z = card_h + joy_stick_len;
    translate([joy_x, joy_y, flange_z0])
        cylinder(r = joy_wide_r - joy_clear, h = flange_h, $fn = 32);
    translate([joy_x, joy_y, stem_base_z])
        cylinder(r = joy_stem_r, h = stem_top_z - stem_base_z, $fn = 24);
    translate([joy_x, joy_y, stem_top_z])
        sphere(r = joy_ball_r, $fn = 28);
}

// ============================================================
// Decorative-only features (no moving parts)
// ============================================================
maze_x0 = 60; maze_x1 = 80; maze_y = 19; maze_depth = 1.2; maze_w = 2.2;

module maze_groove() {
    // A continuous zigzag trench -- hull() of each ADJACENT point pair
    // (Technique 17's "smooth curved line through N points"), not
    // separate segments, so it reads as one continuous groove rather
    // than a beaded chain of disconnected cuts.
    pts = [
        [maze_x0, maze_y - 5], [maze_x0 + 5, maze_y + 5], [maze_x0 + 10, maze_y - 5],
        [maze_x0 + 15, maze_y + 5], [maze_x1, maze_y - 5],
    ];
    for (i = [0 : len(pts) - 2])
        hull() {
            translate([pts[i].x, pts[i].y, card_h - maze_depth])
                cylinder(r = maze_w / 2, h = maze_depth + 0.5, $fn = 16);
            translate([pts[i + 1].x, pts[i + 1].y, card_h - maze_depth])
                cylinder(r = maze_w / 2, h = maze_depth + 0.5, $fn = 16);
        }
}

grip_x = 94; grip_y0 = 17; grip_y1 = 33; grip_n = 6; grip_depth = 0.6;

module grip_texture() {
    for (i = [0 : grip_n - 1])
        translate([grip_x - 5 + i * 2, grip_y0, card_h - grip_depth])
            cube([1.2, grip_y1 - grip_y0, grip_depth + 0.5]);
}

mark_depth = 0.6;

module brand_mark() {
    translate([card_w / 2, card_d / 2, -0.5])
        linear_extrude(height = mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 4.5, font = "Dancing Script:style=Bold",
                     halign = "center", valign = "center");
}

// ============================================================
// Card body
// ============================================================

module card_body() {
    union() {
        difference() {
            cuboid([card_w, card_d, card_h], rounding = corner_r, edges = "Z",
                   anchor = BOTTOM + FRONT + LEFT);
            wheel_notch(wheel1_x, wheel1_y, wheel1_z);
            wheel_notch(wheel2_x, wheel2_y, wheel2_z);
            translate([kc_x, kc_y, -1]) cylinder(r = kc_r, h = card_h + 2, $fn = 24);
            slide_channel();
            btn_bore(btn1_x, btn1_y);
            btn_bore(btn2_x, btn2_y);
            btn_bore(btn3_x, btn3_y);
            dial_bore();
            joy_bore();
            maze_groove();
            grip_texture();
            brand_mark();
        }
        // axles fused to the card, added OUTSIDE the difference() above --
        // Technique 24: nothing downstream may cut them.
        wheel_axle(wheel1_x, wheel1_y, wheel1_z);
        wheel_axle(wheel2_x, wheel2_y, wheel2_z);
    }
}

union() {
    card_body();
    wheel(wheel1_x, wheel1_y);
    wheel(wheel2_x, wheel2_y);
    slider();
    plunger(btn1_x, btn1_y);
    plunger(btn2_x, btn2_y);
    plunger(btn3_x, btn3_y);
    dial();
    joystick();
}
