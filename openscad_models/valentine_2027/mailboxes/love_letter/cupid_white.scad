// Cupid, white, after Scott's reference (2026-11-03): the classic cherub
// archer in profile, mid-flight, back leg kicked out, wing swept up behind, a
// tall bow held out at arm's length with the string drawn to his cheek. Drawn
// fresh in that pose, not traced: one filament, white, and sculpted, so the
// face's profile, his curls and the feathers read by their shape and shadow.
//
// PREVIEW: nothing on the envelope uses this yet.
//
// Laid out on a 0.081 mm grid (the pose was blocked out at that scale), x
// across with him facing +x, y up; every shape rises from his flat back
// (col()), and the whole is clipped at the bed.

$fn = 40;
S = 0.081;
function M(p) = [(p.x - 80) * S, (1360 - p.y) * S];          // grid to mm
function M3(p, z) = [(p.x - 80) * S, (1360 - p.y) * S, z];
module col() hull() { children(); linear_extrude(0.01) projection() children(); }
module ell(c, r) translate(c) scale(r) sphere(1, $fn = 48);
module rod(a, b, ra, rb = -1) hull() { translate(a) sphere(ra); translate(b) sphere(rb < 0 ? ra : rb); }
module pillow(h, rr) for (z = [0.2 : 0.2 : h + 0.001]) let (u = z - (h - rr), inset = u <= 0 ? 0 : rr - sqrt(max(0, rr * rr - u * u)))
    translate([0, 0, -0.01]) linear_extrude(z + 0.01) offset(delta = -inset) children();
module blob2d(p, r) translate(M(p)) circle(r * S);

// ---------- the head, in profile ----------
HC = [420, 768]; HR = 108;       // grid: a big cherub head, near the body's width
HZ0 = 1.0; HRZ = 7.4;
function head_z(p) = let (d = norm(p - M(HC)) / (HR * S)) HZ0 + HRZ * sqrt(max(0, 1 - d * d));
module head() union() {
    col() ell(M3(HC, HZ0), [HR * S, HR * S, HRZ]);
    // the face's profile: brow, a button nose, a round cheek, a chin
    col() ell(M3([505, 785], 3.0), [2.0, 2.2, 3.4]);                    // brow
    col() ell(M3([522, 820], 2.6), [1.9, 1.6, 2.8]);                    // nose
    col() ell(M3([478, 845], 3.4), [4.0, 3.4, 4.2]);                    // cheek
    col() ell(M3([470, 868], 2.2), [2.6, 1.9, 3.0]);                    // chin
}
// curls over the top and back of his head, and down behind his ear
// (the front of his head stays bare, so his face's profile reads)
CURLS = [[318, 800], [312, 742], [342, 698], [388, 672], [438, 664], [482, 680],
         [338, 848], [366, 742], [410, 712]];
module hair() for (c = CURLS) let (m = M(c)) col() ell([m.x, m.y, head_z(m) - 0.4], [3.4, 3.4, 2.6]);
module ear() let (m = M([392, 812])) col() ell([m.x, m.y, head_z(m) - 0.5], [1.6, 2.0, 1.2]);

// ---------- the wing: swept up and back, three rounded feather lobes ----------
// Each lobe is a pillow, the nearer standing higher, so each lies over the one
// behind it; the upper wing at his shoulder stands highest.
module wing() union() {
    pillow(1.8, 1.0) hull() { blob2d([192, 895], 32); blob2d([292, 905], 42); }
    pillow(2.2, 1.1) hull() { blob2d([148, 818], 34); blob2d([268, 862], 44); }
    pillow(2.6, 1.2) hull() { blob2d([125, 735], 28); blob2d([250, 818], 42); }
    pillow(3.4, 1.6) hull() { blob2d([300, 865], 46); blob2d([250, 790], 30); blob2d([195, 752], 20); }
}

// ---------- his body ----------
module torso() col() ell(M3([330, 1010], 0), [10.0, 10.4, 7.2]);
module belly() col() ell(M3([370, 1040], 0), [6.8, 6.4, 7.6]);
module legs() {
    // the back leg, kicked out behind him
    col() rod(M3([270, 1110], 1.0), M3([165, 1165], 1.0), 4.4, 3.8);
    col() rod(M3([165, 1165], 1.0), M3([105, 1215], 0.8), 3.4, 2.6);
    col() ell(M3([98, 1228], 0.6), [2.4, 2.6, 2.2]);
    // the front leg, bent under him
    col() rod(M3([360, 1110], 1.4), M3([395, 1225], 1.2), 5.0, 3.8);
    col() rod(M3([395, 1225], 1.2), M3([375, 1300], 1.0), 3.6, 2.8);
    col() rod(M3([370, 1318], 0.8), M3([440, 1335], 0.6), 2.4, 1.8);
}
module arms() {
    // the bow arm, held out level
    col() rod(M3([420, 945], 4.4), M3([700, 945], 3.2), 2.4, 1.8);
    col() ell(M3([712, 942], 3.2), [2.3, 2.6, 2.2]);                    // the bow hand
    // the drawing arm, its hand at his cheek
    col() rod(M3([420, 918], 5.6), M3([498, 895], 6.0), 2.5, 2.1);
    col() ell(M3([505, 893], 6.0), [2.3, 2.1, 2.2]);                    // the drawing hand
}

// ---------- the bow and the arrow ----------
BOW_C = [370, 915]; BOW_R = 350; BOW_A = 45.6;   // grid: an arc through both tips
function bow_pt(t) = M(BOW_C + BOW_R * [cos(t), sin(t)]);
module bow() for (i = [0 : 11]) let (t0 = -BOW_A + i * 2 * BOW_A / 12, t1 = t0 + 2 * BOW_A / 12,
        r0 = 1.2 - 0.3 * abs(t0) / BOW_A, r1 = 1.2 - 0.3 * abs(t1) / BOW_A)
    col() rod(concat(bow_pt(t0), 1.4), concat(bow_pt(t1), 1.4), r0, r1);
module bow_tips() for (s = [-1, 1]) col() ell(concat(bow_pt(s * BOW_A), 1.4), [1.3, 1.3, 1.6]);
module string() for (s = [-1, 1]) col() rod(concat(bow_pt(s * BOW_A), 1.0), M3([505, 890], 1.0), 0.6);
module arrow() union() {
    col() rod(M3([495, 890], 7.0), M3([765, 890], 3.4), 0.8);
    // its head, a raised triangle
    let (a = M([770, 855]), b = M([770, 925]), c = M([845, 890]))
        hull() { linear_extrude(3.2) polygon([a, b, c]); translate([0, 0, 0]) linear_extrude(4.2) offset(delta = -1.0) polygon([a, b, c]); }
}

module cupid_white() intersection() {
    union() { wing(); legs(); torso(); belly(); arms(); head(); hair(); ear(); bow(); bow_tips(); string(); arrow(); }
    translate([-50, -50, 0]) cube([200, 200, 40]);       // nothing below his back
}
cupid_white();
