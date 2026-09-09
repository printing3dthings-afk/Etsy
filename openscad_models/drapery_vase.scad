// Drapery vase -- a morphing-flute decorative vessel.
//
// THIS MODEL IS SOLID ON PURPOSE, AND THAT IS THE WHOLE DESIGN. Technique 52
// measured 343 real meshes: our own spiral_fluted_vase cuts flutes 1.6% of its
// radius deep where real fluted vases cut 8-20%, and the reason is not
// carelessness -- we model the wall, so a groove deeper than the wall is a
// breach. Sectioning the corpus's top-scoring vessels returns NO interior ring
// at any height on any of them. They are solid; the slicer makes the wall; the
// groove depth is therefore unconstrained. This one is built the same way, so
// it can run the real 8-20% instead of 1.6%.
//
// Consequence, and it is not optional: THIS PRINTS IN VASE MODE (or with 0%
// infill and zero top layers). Slicing it solid with normal infill produces a
// 1.2kg paperweight. See DRAPERY_VASE_PRINTING.md.
//
// The flutes MORPH rather than repeat. Three harmonics -- 12, 24, 48 -- are
// crossfaded by height, so each broad lobe at the foot splits once through the
// belly and again toward the rim. Octaves are chosen deliberately: a
// non-harmonic morph beats against itself and reads as a mistake, where a
// doubling reads as fabric gathering.

$fa = 2;  $fs = 0.4;      // Technique 43: OpenSCAD's own defaults (12/2) measure
                          // 13.8 deg mean dihedral -- that IS the "blocky" look.

include <BOSL2/std.scad>

H          = 180;         // overall height
n_lo       = 12;          // foot harmonic
n_mid      = 24;          // belly
n_hi       = 48;          // rim
twist      = 70;          // total degrees of twist, foot to rim
depth_frac = 0.35;        // peak flute depth as a fraction of LOCAL radius.
env_floor  = 0.40;        // amplitude at foot and lip (see env()).
                          // Corpus p25/median/p75/p90 = 4.2 / 7.9 / 13.7 / 29.0
                          // percent; below ~4% it vanishes into layer lines.
                          // MEASURED BACK off the real mesh at this setting:
                          // 21.5% of radius, 8.84mm, depth:pitch 0.82 -- inside
                          // the corpus's real 0.69-1.20 band. The envelope and
                          // the harmonic crossfade both scale this down, which
                          // is why 0.35 here reads as 21.5% there; 0.17 measured
                          // back as only 9.2% and scored 1.32.
astep      = 0.5;         // angular sample. n_hi=48 needs >=10 samples/lobe;
                          // 0.5 deg gives 15, and a 0.52mm chord at the belly.

// A real ogee, proportioned off a measured reference (Technique 42's Spiral
// Vase No.2): belly low at ~20% of height, not at the middle, and a neck
// roughly 0.31 of the belly radius. A silhouette that is boring flat is boring
// round -- this is reviewed as a 2D profile before any 3D exists.
sil_ctrl = [
    [44,   0], [46,   8], [53,  24], [60,  42], [59,  58],
    [52,  82], [42, 105], [32, 126], [23, 145], [19, 158],
    [19.5,167], [22, 175], [24, 180],
];
sil = smooth_path(sil_ctrl, method = "corners", size = 7, splinesteps = 8);

// ---- the modulation -------------------------------------------------------

// Gaussian crossfade weight for one harmonic.
function gw(t, c, s) = exp(-((t - c) * (t - c)) / (2 * s * s));

// Detail must resolve at BOTH ends, never get chopped off at a boundary
// (Technique 42). Amplitude rises off the foot, peaks near the belly, and
// eases back toward the lip without going to zero -- the rim keeps its fine
// ribs, just quieter.
function env(t) = env_floor + (1 - env_floor) * sin(180 * pow(max(t, 0), 0.8));

// Smooth lobe. NOT abs(cos()): that has a cusp at every zero crossing and
// reads as sharp corrugation no matter how the amplitude is tuned
// (Technique 19). This one is C-infinity everywhere.
function lobe(a, n, ph) = 0.5 + 0.5 * cos(n * (a - ph));

// A slow secondary wobble over the primary count -- perfectly uniform flutes
// read as machined, not thrown (Technique 11).
//
// THE FREQUENCY MUST BE A WHOLE NUMBER OF CYCLES PER REVOLUTION. Technique 11's
// worked example uses 2.3, and 2.3 does not close: wobble(0) = 0.8867 against
// wobble(359.5) = 0.9838, which at the belly is a 1.90mm radial STEP -- a ridge
// running the vase's entire height, clearly visible in a shaded render and
// invisible in every numeric gate. 7 closes exactly and is coprime with 12, 24
// and 48, so it still never locks in phase with the flutes, which is the whole
// point of the term. (halloween_pumpkin.scad carries the same 2.3 and very
// likely the same seam.)
function wobble(a) = 0.86 + 0.14 * sin(a * 7 + 11);

function ring_r(r, z, a) =
    let(
        t   = z / H,
        ph  = twist * t,
        wa  = gw(t, 0.00, 0.30),
        wb  = gw(t, 0.50, 0.24),
        wc  = gw(t, 1.00, 0.30),
        m   = (wa * lobe(a, n_lo,  ph)
             + wb * lobe(a, n_mid, ph)
             + wc * lobe(a, n_hi,  ph)) / (wa + wb + wc),
        d   = depth_frac * r * env(t) * wobble(a)
    )
    r - d * m;

function ring(r, z) = [for (a = [0 : astep : 360 - astep])
    let(rr = ring_r(r, z, a)) [rr * cos(a), rr * sin(a)]];

module body() {
    skin([for (p = sil) ring(p.x, p.y)], z = [for (p = sil) p.y], slices = 0);
}

// ---- maker's mark ---------------------------------------------------------
// Standing rule: engraved NEGATIVE, on the hidden underside, sized to this
// model's own flat run rather than inherited from a sibling. The bottom
// contour runs r 43.1..44 here, so the real usable flat run is 2 * 43.1.
// "OBC" in Montserrat Black is 3.177mm wide per size unit (measured with
// glyph_probe); Caveat Bold measures 1.89 extrusions at mark scale and would
// print blank, which is why the whole catalogue moved off it.
mark_pad   = 2 * 43.1;
mark_size  = mark_pad * 0.40 / 3.177;
mark_depth = 0.7;

module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OBC", size = mark_size, font = "Montserrat:style=Black",
                     halign = "center", valign = "center");
}

difference() {
    body();
    brand_mark();
}
