// Monogram fidget keychain — print-in-place, three colours, A-Z from one file.
//
// FONT IS FREDOKA, AND THAT IS A MEASURED DECISION. tools/glyph_probe.py swept
// all 26 letters in six candidate faces. Cinzel Decorative's J has a 0.24mm
// stroke -- 0.57 of one extrusion -- and would print as nothing. Fredoka's
// weakest glyph loses 0.01% of its area to a one-bead opening and its typical
// stroke is 9.05 extrusions. The probe is validated against real ground truth:
// it FAILS "OnBrandCraftz" at the size that actually printed blank, and PASSES
// the "OBC" that replaced it.
//
// COLOUR SPLIT follows corpus finding 7 -- the strongest two-colour work is a
// layered offset stack, not painting -- and this repo's own dumpling clicker
// pattern: one body per colour, exported separately, assembled in the slicer.
//    part="ring"   frame + knurl + keyring lug   (colour A)
//    part="rotor"  the spinning disc             (colour B)
//    part="letter" the raised monogram           (colour C)

$fa = 2;  $fs = 0.4;

include <BOSL2/std.scad>

part      = "all";          // all | ring | rotor | letter
letter    = "J";
mark_text = "OBC";

T         = 9.0;            // frame thickness
Th        = 7.4;            // rotor thickness; the letter fills the rest
R         = 15.0;           // rotor core radius
bulge     = 1.5;            // captive rim
clear     = 0.40;           // PROVEN rotating clearance (Technique 22's hinge)
wall      = 5.0;
Ro        = R + bulge + clear + wall;

letter_h  = T - Th;         // letter top sits FLUSH with the frame, so the
                            // proudest feature is protected from pocket wear
letter_sz = 18.0;

bezel_r   = R - 3.0;        // a groove ringing the letter, for depth
bezel_w   = 1.0;
bezel_d   = 0.5;

knurl_n   = 44;             // corpus finding 1: a plain panel reads unfinished
knurl_d   = 0.9;
cham      = 0.7;

tab_out   = 8.5;
hole_r    = 2.6;

mark_pad  = 2 * R;
mark_size = mark_pad * 0.45 / 2.089;   // "OBC" is 2.089mm wide per size unit
mark_deep = 0.6;

// ---------------- rotor ----------------
function rotor_profile() = [[0,0], [R,0], [R+bulge, Th/2], [R,Th], [0,Th]];

module rotor() {
    difference() {
        rotate_extrude($fn = 220) polygon(rotor_profile());
        // bezel groove
        rotate_extrude($fn = 220)
            translate([bezel_r - bezel_w/2, Th - bezel_d]) square([bezel_w, bezel_d + 1]);
        // maker's mark, underside, standing rule
        translate([0, 0, -0.5])
            linear_extrude(mark_deep + 0.5)
                mirror([0,1,0])
                    text(mark_text, size = mark_size, font = "Caveat:style=Bold",
                         halign = "center", valign = "center");
    }
}

module letter_body() {
    translate([0, 0, Th])
        linear_extrude(letter_h)
            text(letter, size = letter_sz, font = "Fredoka:style=Regular",
                 halign = "center", valign = "center");
}

// ---------------- ring ----------------
// The bore is defined ONCE, here, and cut from the frame. Defining it twice
// left 40 zero-volume slivers where two near-coincident surfaces fought.
module rotor_envelope() {
    rotate_extrude($fn = 220)
        polygon([[0,-2], [R+clear,-2], [R+clear,0], [R+bulge+clear, Th/2],
                 [R+clear, Th], [R+clear, T+2], [0, T+2]]);
}

function trim(z) = (z < cham) ? (cham - z)
                 : (z > T - cham) ? (z - (T - cham)) : 0;
function knurl(a) = knurl_d * (0.5 + 0.5 * cos(knurl_n * a));
function frame_r(a, z) = Ro - knurl(a) - trim(z);
function frame_ring(z) = [for (a = [0 : 2 : 359])
                            [frame_r(a,z)*cos(a), frame_r(a,z)*sin(a)]];
zs = concat([0, cham*0.5, cham], [for (i=[1:6]) cham + (T-2*cham)*i/6],
            [T-cham*0.5, T]);

module ring() {
    difference() {
        union() {
            skin([for (z = zs) frame_ring(z)], z = zs, slices = 0);
            // FULL HEIGHT, sitting on the bed. Insetting it by `cham` at both
            // ends to match the frame's chamfer left the lug's whole underside
            // floating 0.7mm over nothing -- a 90-degree unsupported face that
            // mesh_gate flagged in the overhang line. Square edges on a keyring
            // tab are also simply stronger than chamfered ones.
            hull() {                                    // keyring lug
                translate([Ro - 4, 0, 0]) cylinder(h = T, r = 6.5);
                translate([Ro + tab_out, 0, 0]) cylinder(h = T, r = 4.8);
            }
        }
        rotor_envelope();
        translate([Ro + tab_out, 0, -1]) cylinder(h = T + 2, r = hole_r);
    }
}

if      (part == "ring")   ring();
else if (part == "rotor")  rotor();
else if (part == "letter") letter_body();
else if (part == "preview") {
    color("#2b2f38") ring();          // charcoal frame
    color("#f2f0e9") rotor();         // bone face
    color("#e0553d") letter_body();   // brand-adjacent accent
}
else { ring(); rotor(); letter_body(); }
