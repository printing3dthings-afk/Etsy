// Monogram fidget keychain — print-in-place, three colours, A-Z from one file.
//
// THE FONT IS A MEASURED DECISION, NOT A TASTE ONE. tools/glyph_probe.py swept
// all 26 letters in six candidate faces. Cinzel Decorative's J has a 0.24mm
// stroke -- 0.57 of one extrusion -- and would print as nothing. The shipped
// face is Dancing Script Bold, which only clears the 2.00-extrusion floor
// because letter_bold fattens it; see the table at letter_font. (This header
// read "FONT IS FREDOKA" until 2026-09-09 -- Fredoka was measured and lost to
// Scott's pick, and the comment was never corrected. Fredoka's numbers are
// still in that table, where they belong.) The probe is validated against real
// ground truth: it FAILS "OnBrandCraftz" at the size that actually printed
// blank, and PASSES the "OBC" that replaced it.
//
// COLOUR SPLIT follows corpus finding 7 -- the strongest two-colour work is a
// layered offset stack, not painting -- and this repo's own dumpling clicker
// pattern: one body per colour, exported separately, assembled in the slicer.
//    part="ring"   frame + knurl + keyring lug   (colour A)
//    part="rotor"  the spinning disc             (colour B)
//    part="letter" the raised monogram           (colour C)
//    part="mark"   the OBC maker's mark          (colour D -- white)
//
// THE MARK IS AN INLAY, NOT AN ENGRAVING (2026-09-09, from the printed J).
// Cut into the underside at the same colour it read as nothing: the rotor's
// bottom face is printed on the TEXTURED plate, and that stipple is deeper
// than any mark this size can afford to be. So the depth is not the signal --
// colour is. The pocket is filled by a body of its own, flush with the face,
// swapped to white in the first 3 layers. Two things fall out for free: the
// mark cannot wear off, being through-coloured rather than surface-deep, and
// the pocket's unsupported ceiling stops existing because something now
// physically holds it up.

$fa = 2;  $fs = 0.4;

include <BOSL2/std.scad>

part      = "all";          // all | ring | rotor | halo | letter | mark
letter    = "J";
mark_text = "OBC";

T         = 9.0;            // frame thickness
Th        = 7.4;            // rotor thickness; the letter fills the rest
R         = 15.0;           // rotor core radius
bulge     = 1.5;            // captive rim
// 0.40 was the hinge's proven number and IT FUSED HERE (printed 2026-09-09).
// A hinge is a short pin; this is a 7.4mm-tall journal facing the frame around
// its whole circumference -- ~700mm2 of facing surface, and ONE weld anywhere
// on it stops the part. The clearance is opened, but the clearance was never
// the whole story: see cham_b, which relieves the two layers where a
// print-in-place part actually welds.
clear     = 0.45;
cham_b    = 0.6;           // interface relief at the bed and at the rotor's
                           // top face. Elephant's foot spreads the first
                           // layers of BOTH bodies into a gap this size, and
                           // ironing drags melt off the rotor's top rim across
                           // it. Chamfering the rotor's outer edges (and
                           // flaring the frame's bore to match) opens those
                           // two layers to 0.45+2*0.6 = 1.65mm while leaving
                           // the load-bearing V untouched at 0.45.
wall      = 5.0;
Ro        = R + bulge + clear + wall;

letter_h  = T - Th;         // letter top sits FLUSH with the frame, so the
                            // proudest feature is protected from pocket wear
// THE SIZE IS SET BY THE WORST GLYPH, NOT BY 'J'. A monogram product ships 26
// letters and is only as good as its widest and its thinnest. Measured across
// all 26 at size 22, then scaled to fit inside the bezel (r=11.1 after the halo
// offset), the only faces that BOTH fit and print are:
//
//   Caveat Bold          size 14.7   3.87 extrusions
//   Bebas Neue           size 18.2   5.46
//   Fredoka              size 13.9   6.63
//   Dancing Script Bold  size 12.9   2.09  <- Scott's pick, and 2.09 against a
//                                             2.00 floor is not a margin
//   Cinzel Decorative    size  8.7   1.21  FAILS -- its Q is 47mm wide at 22,
//                                          decorative swashes, so fitting it
//                                          shrinks every stroke below a bead
//   Great Vibes          size  8.2   0.76  FAILS
//
// letter_bold is what makes Dancing Script safe rather than borderline. An
// offset fattens every stroke by 2*letter_bold while leaving the letterform
// alone, so the face still reads as the same script. Measured across all 26:
//   offset 0.00 -> size 12.85, worst stroke 2.09 extrusions
//   offset 0.15 -> size 12.71, worst stroke 2.48
//   offset 0.25 -> size 12.62, worst stroke 2.80   <- shipped
// The glyph barely shrinks paying for it. Re-measure with
// `glyph_probe.py --alphabet --offset` if the face or the face size changes.
letter_font = "Dancing Script:style=Bold";
letter_sz   = 12.6;
letter_bold = 0.25;
halo_off  = 0.9;            // offset backing behind the letter -- corpus
halo_h    = 0.6;            // finding 7's layered 2D offset stack, which is
                            // the whole multicolour-sign category in one move

bezel_r   = R - 3.0;        // a groove ringing the letter, for depth
bezel_w   = 1.0;
bezel_d   = 0.5;

knurl_n   = 44;             // corpus finding 1: a plain panel reads unfinished
knurl_d   = 0.9;
cham      = 0.7;

tab_out   = 8.5;
hole_r    = 2.6;

// Caveat Bold measured 1.89 extrusions here -- under the 2.00 floor, so the
// shipped mark was never printable at this size regardless of colour. The same
// probe that chose the monogram face rejects it:
//   Caveat Bold        1.89 extrusions   FAIL, and it shipped
//   Bebas Neue         2.38
//   Fredoka SemiBold   3.24
//   Montserrat Black   4.15              <- and the face the rest of the
//                                           catalogue's marks already use
mark_font = "Montserrat:style=Black";
mark_pad  = 2 * (R - cham_b);          // the real flat run, after the chamfer
mark_size = mark_pad * 0.42 / 3.177;   // "OBC" is 3.177mm wide per size unit
mark_deep = 0.6;                       // exactly 3 layers at 0.2

// ---------------- rotor ----------------
function rotor_profile() = [[0,0], [R-cham_b, 0], [R, cham_b],
                            [R+bulge, Th/2],
                            [R, Th-cham_b], [R-cham_b, Th], [0,Th]];

module rotor() {
    difference() {
        rotate_extrude($fn = 220) polygon(rotor_profile());
        // bezel groove
        rotate_extrude($fn = 220)
            translate([bezel_r - bezel_w/2, Th - bezel_d]) square([bezel_w, bezel_d + 1]);
        translate([0, 0, -0.5]) linear_extrude(mark_deep + 0.5) mark_2d();
    }
}

// mirror([0,1,0]) flipped the mark in Y, which reads as a 180-degree ROTATION
// from below, not as a mirror -- it printed backwards and unreadable. The
// underside is seen by turning the part about its vertical axis, so world +X
// maps to screen-left and X is the axis to pre-flip.
module mark_2d() {
    mirror([1,0,0])
        text(mark_text, size = mark_size, font = mark_font,
             halign = "center", valign = "center");
}

// Fills the pocket exactly. A coincident boundary is what multi-material wants
// -- no gap to leak through, no overlap for the slicer to arbitrate.
module mark_body() { linear_extrude(mark_deep) mark_2d(); }

module glyph_raw() {
    text(letter, size = letter_sz, font = letter_font,
         halign = "center", valign = "center");
}

// Every downstream feature offsets from the BOLDED glyph, so the halo sits a
// constant distance off the letter that actually prints.
module glyph() { offset(letter_bold) glyph_raw(); }

module letter_body() {
    translate([0, 0, Th]) linear_extrude(letter_h) glyph();
}

// A thin plate ringing the letter, one offset out. Reads as a struck monogram
// rather than a letter dropped on a disc, and costs one filament slot.
module halo_body() {
    translate([0, 0, Th])
        linear_extrude(halo_h)
            difference() { offset(halo_off) glyph(); glyph(); }
}

// ---------------- ring ----------------
// The bore is defined ONCE, here, and cut from the frame. Defining it twice
// left 40 zero-volume slivers where two near-coincident surfaces fought.
module rotor_envelope() {
    rotate_extrude($fn = 220)
        polygon([[0,-2], [R+clear+cham_b, -2], [R+clear+cham_b, 0],
                 [R+clear, cham_b],
                 [R+bulge+clear, Th/2],
                 [R+clear, Th], [R+clear+cham_b, Th+cham_b],
                 [R+clear+cham_b, T+2], [0, T+2]]);
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
else if (part == "halo")   halo_body();
else if (part == "letter") letter_body();
else if (part == "mark")   mark_body();
else if (part == "preview") {
    color("#2b2f38") ring();          // charcoal frame
    color("#f2f0e9") rotor();         // bone face
    color("#c9a84c") halo_body();     // struck-gold surround
    color("#e0553d") letter_body();   // brand-adjacent accent
    color("#ffffff") mark_body();     // maker's mark, flush inlay
}
else { ring(); rotor(); halo_body(); letter_body(); mark_body(); }
