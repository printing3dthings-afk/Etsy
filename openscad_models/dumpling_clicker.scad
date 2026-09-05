include <BOSL2/std.scad>

// ============================================================
// Dumpling Clicker Keychain
// A kawaii bao bun keycap pressing a real Cherry MX switch, seated in a
// bamboo steamer basket with a keyring tab. Two printed parts plus one
// off-the-shelf MX switch (not printed, not included in these files).
//
//   part = "bao" | "basket" | "both"
//
// Every MX dimension below comes from Cherry's OWN datasheet drawing
// (MX1A series) or Cherry's published keycap slot spec. Guessing any of
// them means the switch does not seat or the bun falls off, so they are
// named constants and the whole Z stack is DERIVED from them -- there is
// not a single eyeballed height in this file.
// ============================================================

part = "both";

$fa = 2;      // Technique 43: OpenSCAD's 12/2 defaults ARE the "blocky"
$fs = 0.4;    // look. These two lines buy the smooth organic surface.

// ---------- Cherry MX interface (datasheet; do not guess) ----------
mx_housing  = 15.6;                 // top housing, square, rests ON the plate
mx_hous_dia = mx_housing * sqrt(2); // 22.06 -- the CORNERS are what collide
mx_cutout   = 14.0;                 // standard plate cutout
mx_plate_t  = 1.5;                  // plate thickness the clips expect
mx_below    = 5.0;                  // body below the plate
mx_pins     = 3.3;                  // pins below the body
mx_above    = 6.6;                  // housing above plate (11.6 - 5.0)
mx_stem_h   = 3.6;                  // cross proud of the housing top
mx_travel   = 4.0;                  // full travel

// Cherry's keycap slot spec is a 4.1mm cross with 1.17mm arms. An FDM hole
// prints UNDER size, so it is opened by sock_fit. Technique 47: the
// best-selling real clicker ships two tolerances instead of betting on
// one -- so does this (see dumpling_clicker_bao_loose.scad).
sock_fit    = 0.12;
sock_span   = 4.10 + sock_fit;
sock_arm    = 1.17 + sock_fit;
sock_depth  = 3.4;                  // engages 3.4 of the 3.6mm stem

// ---------- derived Z stack (nothing below here is eyeballed) ----------
bk_floor    = 1.6;
well_z0     = bk_floor;
well_h      = mx_below + mx_pins + 0.6;
plate_z0    = well_z0 + well_h;             // 10.5  plate underside
plate_z1    = plate_z0 + mx_plate_t;        // 12.0  plate top; housing sits here
housing_top = plate_z1 + mx_above;          // 18.6
stem_top    = housing_top + mx_stem_h;      // 22.2
bao_rim_z   = stem_top - sock_depth;        // 18.8  cap rim at rest
rim_pressed = bao_rim_z - mx_travel;        // 14.8  cap rim fully pressed

// ---------- steamer basket ----------
bk_r        = 17.6;                 // outer radius at the slat valleys
bk_bore     = 15.5;                 // upper bore -- the bun nests INTO this
bk_well     = 12.0;                 // lower well, clears the 11.03 half-diag
// A real bamboo steamer is a smooth drum with MANY fine scribed lines and a
// distinct proud collar at the rim -- not a stack of fat rings. The first
// pass used 4 deep cosine swells and read as a screw thread; counted off the
// reference photo, the real thing has 8 shallow incised grooves between a
// plain base band and that collar.
n_slat      = 8;
slat_depth  = 0.45;                 // incised INWARD, narrow -- a scribed line
slat_w      = 0.9;                  // groove width at the surface
band_lo     = 3.6;                  // plain base band below the slats
band_hi     = 14.4;                 // slats stop here; collar starts
collar_r    = 18.35;                // the rim stands proud of the drum
collar_z    = 15.2;                 // top of the 40deg flare up to the collar

// The rim sits 0.6mm under the bun's own rim at rest, so the bun visually
// NESTS in the steamer instead of perching on it with the grey switch
// showing through the gap. It can go this high because the bun descends
// INSIDE the bore -- the only real floor is the plate, and the bun's rim
// only ever reaches rim_pressed, which is 2.8mm above it.
bk_h        = bao_rim_z - 0.6;

// ---------- bao ----------
bao_r       = 14.6;                 // rim radius; peak 15.0 at the belly
bao_h       = 16.6;                 // 30.0 wide x 16.6 tall = 1.81:1. A real
                                    // bao is a squat dome, not a ball --
                                    // Technique 31: state the ratio, don't
                                    // eyeball it.
n_pleat     = 14;
pleat_amp   = 1.50;                 // 10% of radius: Technique 52's 8-20% band.
                                    // RAISED outward, never cut in, so no wall
                                    // is ever thinned (Technique 52's "we model
                                    // the wall, they don't" finding).

echo(str("plate_top=", plate_z1, " housing_top=", housing_top,
         " stem_top=", stem_top, " bao_rim=", bao_rim_z,
         " pressed=", rim_pressed, " basket_rim=", bk_h,
         " | cap clears plate by ", rim_pressed - plate_z1,
         " | housing reaches bao-local ", housing_top - rim_pressed));

// ---------- keyring tab (Technique 49: the loop is the #1 failure point) ----------
ring_hole   = 4.2;                  // a split ring is a DOUBLED wire: 4-5mm
ring_wall   = 3.0;                  // >=3mm of solid around it
ring_t      = 4.0;

// ============================================================
// BAO -- lofted dome, gathered pleats, hollow underside, MX socket
// ============================================================

// Silhouette. Final point is off-axis (0.9, never 0) -- Technique 15: a
// profile touching x=0 closes to a degenerate vertex that previews fine
// and fails EVERY boolean afterwards.
bao_ctrl = [
    [bao_r,  0],
    [15.0,   2.6],
    [14.6,   6.4],
    [13.0,  10.0],
    [9.6,   13.2],
    [5.0,   15.4],
    [1.2,   bao_h],
];
bao_prof = smooth_path(bao_ctrl, method="corners", size=2.6, splinesteps=14);

// Pleats gather at the crown and vanish by the rim -- Technique 18's
// height-varying texture. A real bao's folds are pinched at the twist and
// smooth on the belly; constant-depth fluting reads as a machined part.
// This fade is also what keeps the widest pleats out of the basket bore.
// Exponent 1.15, not 1.4. At 1.4 the folds collapsed to nothing below the
// equator and the whole lower body measured bare (rugosity driven only by
// the crown). 1.15 carries them further down, matching the reference photo,
// while still keeping the widest pleat inside the basket bore: the bun only
// sinks 2.7mm into the bore at full press, and at z=2.7 the fold is 0.20mm
// on a 15.0 radius -- 0.30mm of clearance in a 15.5 bore.
function pleat_at(z) = pleat_amp * pow(max(0, min(1, z / bao_h)), 1.15);

// Smooth cosine, NOT abs(cos) -- Technique 19: abs() puts a cusp at every
// zero crossing and reads as sharp corrugation instead of soft dough.
function bao_ring(r, z) = [for (a = [0 : 3 : 357])
    let(rr = r + pleat_at(z) * pow(0.5 + 0.5 * cos(a * n_pleat), 1.7))
    [rr * cos(a), rr * sin(a)]
];

module bao_solid() {
    skin([for (p = bao_prof) bao_ring(p.x, p.y)],
         z = [for (p = bao_prof) p.y], slices = 0);
}

// The underside cavity has to swallow the switch HOUSING through the whole
// 4mm of travel -- and it is the housing's 22.06mm CORNER diagonal that
// collides, not its 15.6mm face. Radius stays >=11.5 until bao-local 4.4,
// which is past the 3.8 the housing ever reaches.
// It tapers hard the moment it is past the housing's reach. A first pass
// held 12mm of radius up to z=6.6 "to be safe" and the eye dimples punched
// straight through into it -- visible as real holes in the render. The
// cavity only has to be wide where the housing actually is (bao-local 3.8);
// every millimetre of width above that is wall thickness thrown away.
cav_ctrl = [[12.2, 0], [12.0, 4.0], [10.4, 5.4], [8.4, 7.2],
            [6.4, 9.4], [5.0, 11.6], [4.9, 12.0]];

module cavity_solid() {
    rotate_extrude($fn = 128)
        polygon(concat(cav_ctrl, [[0, 12.0], [0, 0]]));
}

// The socket post must descend INTO the switch housing's own stem opening
// as the cap travels, so its lower section is slender (5.6mm dia, the same
// as a real injection-moulded MX keycap) and only as long as the travel
// needs. It thickens immediately above that, so the thin section is short.
post_r_lo   = 2.80;                 // 0.69mm wall at the cross arm tips
post_r_hi   = 5.20;
post_lo_h   = 5.0;
post_cone_h = 2.2;

module socket_post() {
    cylinder(h = post_lo_h, r = post_r_lo, $fn = 64);
    translate([0, 0, post_lo_h])
        cylinder(h = post_cone_h, r1 = post_r_lo, r2 = post_r_hi, $fn = 64);
    translate([0, 0, post_lo_h + post_cone_h])
        cylinder(h = 12.0 - post_lo_h - post_cone_h + 0.6, r = post_r_hi, $fn = 64);
}

module mx_socket() {
    // Dips 0.4 BELOW the mouth so the boolean genuinely overlaps -- a
    // cutter that only touches its surface removes nothing and renders
    // perfectly clean (Technique 4's buried-cut trap).
    translate([0, 0, -0.4]) linear_extrude(height = sock_depth + 0.4) {
        square([sock_span, sock_arm], center = true);
        square([sock_arm, sock_span], center = true);
    }
}

// Real surface radius at a height, read off the silhouette itself. The
// first attempt placed the eyes on a guessed chord (all at one Y), so the
// outer features sat at a different depth than the inner ones and the cut
// depth varied across the face. Placing radially fixes that by construction.
function bao_r_at(z) =
    let(i = [for (k = [0 : len(bao_prof) - 2])
                if (bao_prof[k].y <= z && bao_prof[k + 1].y >= z) k])
    len(i) == 0 ? bao_prof[0].x
    : let(a = bao_prof[i[0]], b = bao_prof[i[0] + 1],
          t = (z - a.y) / max(b.y - a.y, 1e-6))
      a.x + t * (b.x - a.x);

// Place a cutter on the surface at a given azimuth (0 = facing -Y) and
// height, sunk `bite` mm in from the real surface.
function face_pos(az, z, bite) =
    let(r = bao_r_at(z) - bite)
    [r * sin(az), -r * cos(az), z];

// ---------- kawaii face (Technique 17: shallow dimples, never through-cuts) ----------
eye_z  = 8.6;   // 52% of the bun's height. Also has to clear the 2.7mm of
                // skirt that hides inside the basket at full press --
                // a face detail below that line is invisible when clicked.

module eye_cut() {
    // Cut depth is (sphere r - bite), and it has to be ordered on purpose:
    // eyes deepest, smile mid, blush barely a dish. The first attempt had
    // the blush cutting 1.55mm against the eyes' 1.3mm -- the shallowest
    // feature was the deepest one, which is why the face read as five
    // unrelated blobs rather than a face.
    for (s = [-1, 1])                                   // eyes, 1.35mm deep
        translate(face_pos(s * 17, eye_z, 1.35))
            scale([1, 1, 1.35]) sphere(r = 2.60);

    // Smile as a hull() chain, not a row of spheres -- Technique 17 found a
    // row reads as a beaded chain. Outer points sit HIGHER than the centre;
    // the same sign drew a frown on the first attempt there.
    // A PARABOLIC rise (i*i), not abs(i). abs() puts a corner at the centre
    // and the mouth came out as a hard boomerang chevron -- the same cusp
    // problem Technique 19 hit on the ghost's folds, in a different place.
    smile = [for (i = [-3 : 3])                          // smile, 0.70mm deep
        face_pos(i * 3.5, eye_z - 4.3 + 0.13 * i * i, 0.25)];
    for (k = [0 : len(smile) - 2])
        hull() {
            translate(smile[k])     sphere(r = 0.95);
            translate(smile[k + 1]) sphere(r = 0.95);
        }

}

// Blush is its own colour part. It MUST NOT share volume with the eyes or
// both printed parts would claim the same space -- and at 33 degrees against
// the eyes' 17 it genuinely did: intersection(eyes, blush) came back with
// real geometry, which no render would have shown. Rather than hunt for an
// angle that happens to clear, the eye is subtracted from it, so they are
// disjoint by construction at any placement. The blush tucking behind the
// eye is also how the reference photo actually looks.
module blush_raw() {
    for (s = [-1, 1])
        translate(face_pos(s * 34, eye_z - 3.0, 1.35))
            rotate([0, 0, s * 34]) scale([1.25, 1, 0.9]) sphere(r = 1.95);
}
module blush_cut() { difference() { blush_raw(); eye_cut(); } }

// The catchlight. Sits INSIDE the eye, so it is subtracted from the eye part
// as well as from the body -- otherwise the eye and the highlight would both
// own it. On a cream bun this can simply be assigned the body filament and
// costs no extra AMS slot; on the blue bun it wants white.
module shine_cut() {
    for (s = [-1, 1])
        translate(face_pos(s * 17 - s * 5.0, eye_z + 1.25, 0.50))
            sphere(r = 1.15);
}

// Everything the bun is, before any colour split -- the shell, the cavity,
// the socket post and its bore. All four colour parts are carved out of THIS,
// so together they reconstitute it exactly (Technique 39).
module bao_gross() {
    difference() {
        union() {
            difference() {
                bao_solid();
                difference() { cavity_solid(); socket_post(); }
            }
            socket_post();
        }
        mx_socket();
    }
}

module bao_body()  { difference()  { bao_gross(); eye_cut(); blush_raw(); shine_cut(); } }
module bao_eyes()  { intersection() { bao_gross(); difference() { eye_cut(); shine_cut(); } } }
module bao_blush() { intersection() { bao_gross(); blush_cut(); } }
module bao_shine() { intersection() { bao_gross(); shine_cut(); } }



// ============================================================
// BASKET -- bamboo courses, switch plate, nesting bore, keyring tab
// ============================================================

function ring_pts(r) = [for (a = [0 : 3 : 357]) [r * cos(a), r * sin(a)]];

// Outer profile, revolved. Explicit V-notches rather than a cosine: a cosine
// has no flat between its dips, so the drum never reads as a smooth barrel
// with lines scribed on it -- it reads as corrugation, which is exactly what
// went wrong the first time.
slat_pitch = (band_hi - band_lo) / (n_slat - 1);

function slat_profile() = concat(
    [[0, 0], [bk_r, 0], [bk_r, band_lo]],
    [for (i = [0 : n_slat - 1], k = [0 : 2])
        let(gz = band_lo + i * slat_pitch)
        k == 0 ? [bk_r, gz - slat_w / 2]
      : k == 1 ? [bk_r - slat_depth, gz]
      :          [bk_r, gz + slat_w / 2]],
    // 40deg flare out to the proud rim collar -- a square step here would be
    // a horizontal overhang all the way round
    [[bk_r, band_hi + 0.4], [collar_r, collar_z], [collar_r, bk_h], [0, bk_h]]
);

module basket_outer() {
    rotate_extrude($fn = 180) polygon(slat_profile());
}

// Radiating woven slats on the visible floor of the basket (reference
// photo 4). Raised ribs, not cuts -- same reasoning as the bun's pleats.
// Ribs stand ON the plate, not flush IN it -- the first pass set them to
// plate_z1 - 0.3 with a 0.6 height, so they ended level with the plate top
// and vanished. They also start outside the housing's 11.03mm CORNER
// radius: a rib under the switch would stop it seating flat on the plate,
// which is the one surface the whole mechanism references from.
weave_r0 = 11.6;
weave_r1 = bk_bore - 0.3;
weave_h  = 0.55;
module floor_weave() {
    for (i = [0 : 23])
        rotate([0, 0, i * 360 / 24])
            translate([(weave_r0 + weave_r1) / 2, 0, plate_z1 + weave_h / 2])
                cube([weave_r1 - weave_r0, 1.0, weave_h], center = true);
}

module ring_tab() {
    tab_x = bk_r + ring_hole / 2 + ring_wall - 2.6;
    hull() {
        translate([bk_r - 2.0, 0, bk_h - ring_t / 2 - 1.6])
            rotate([90, 0, 0]) cylinder(h = ring_t, r = 3.4, center = true, $fn = 40);
        translate([tab_x, 0, bk_h - ring_t / 2 - 1.6])
            rotate([90, 0, 0])
                cylinder(h = ring_t, r = ring_hole / 2 + ring_wall, center = true, $fn = 56);
    }
}

module ring_bore() {
    tab_x = bk_r + ring_hole / 2 + ring_wall - 2.6;
    translate([tab_x, 0, bk_h - ring_t / 2 - 1.6])
        rotate([90, 0, 0])
            cylinder(h = ring_t + 2, r = ring_hole / 2, center = true, $fn = 48);
}

logo_depth = 0.6;
logo_size  = 7.4;   // fitted to THIS part's real 35mm base and re-measured
                    // off the exported mesh -- never copied from another model
module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OBC", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

module basket() {
    union() {
        difference() {
            union() { basket_outer(); ring_tab(); }
            translate([0, 0, well_z0])
                cylinder(h = well_h + 0.01, r = bk_well, $fn = 128);
            translate([0, 0, plate_z1])
                cylinder(h = bk_h - plate_z1 + 1, r = bk_bore, $fn = 160);
            translate([-mx_cutout/2, -mx_cutout/2, plate_z0 - 0.02])
                cube([mx_cutout, mx_cutout, mx_plate_t + 0.04]);
            ring_bore();
            brand_mark();
        }
        // added AFTER the bore is cut, or the bore shaves them off again
        floor_weave();
    }
}

// ============================================================

// A stand-in for the real Cherry MX switch. PREVIEW ONLY -- it is never
// part of an exported part, it exists so the fit can be seen and checked
// rather than taken on trust from the derived numbers alone.
module mx_mock() {
    color("gray") {
        translate([0, 0, plate_z1 - mx_below])
            cube([13.9, 13.9, mx_below + 0.1], center = true, $fn = 4);
        translate([0, 0, plate_z1 + mx_above/2])
            cube([mx_housing, mx_housing, mx_above], center = true);
    }
    color("dodgerblue") translate([0, 0, housing_top])
        linear_extrude(height = mx_stem_h) {
            square([4.10, 1.17], center = true);
            square([1.17, 4.10], center = true);
        }
}

module assembly(press = 0) {
    basket();
    mx_mock();
    translate([0, 0, bao_rim_z - press]) {
        color("wheat")     bao_body();
        color("#141414")   bao_eyes();
        color("#F49AC1")   bao_blush();
        color("white")     bao_shine();
    }
}

// "bao" IS the body. Printed on its own in one filament the face reads as
// recessed dimples; printed alongside the three inlays it is the bun colour
// and the face is real colour, flush with the surface.
if      (part == "bao")        bao_body();
else if (part == "bao_eyes")   bao_eyes();
else if (part == "bao_blush")  bao_blush();
else if (part == "bao_shine")  bao_shine();
else if (part == "basket")     basket();
else if (part == "assembly")   assembly(0);
else if (part == "pressed")    assembly(mx_travel);
// the two tests that matter for a multi-colour split: no two colour parts may
// share volume, and together they must leave nothing behind
else if (part == "chk_overlap") intersection() { bao_eyes(); bao_blush(); }
else if (part == "chk_gap")     difference() { bao_gross(); bao_body(); bao_eyes(); bao_blush(); bao_shine(); }
else {
    translate([-24, 0, 0]) basket();
    translate([ 24, 0, 0]) bao();
}
