// Birch Log Tea-Light Trio (2026-11-15). Scott picked form 1: three upright cut logs, 60, 90
// and 120 mm tall, each with a well for a 38 mm LED tea light. LED tea lights only, never a
// candle: this is PLA.
//
// The bark texture is NOT modelled. It is Bambu Studio's Perlin fuzzy skin on the outer walls
// (measured on the texture sampler, data/knowledge_base/fdm_only_techniques.md section 1), set in
// make.sh. The model carries only what the slicer can't: the shape, the dark birch marks, the cut
// face's colour, its tree rings and drying cracks.
//
// Three colour parts per log, all in the print's own frame:
//   body  white bark and the log itself
//   marks dark lenticels (short level dashes) and one or two "eyes" (chevron scars)
//   top   the cut face, tan, 1.2 mm deep inside the bark ring
//
// The dark marks cost colour changes. Every dash sits in one of a few shared height bands, the
// same bands on all three logs, so one band is one set of changes for the whole plate. See
// FACTS.md for what the slice measured.
//
//   part = "body" | "marks" | "top" | "log" (all three parts of one log) | "gate" (one solid, for
//          the gates) | "all" (review)
//   which = 0, 1, 2 (short, middle, tall)

part = "all";
which = 0;

//           R    H    seed  eyes (each one's apex, from EYE_BANDS)
LOGS = [[35.5, 60, 11, [48.6]],
        [38.5, 90, 23, [27.4]],
        [41.5, 120, 37, [27.4, 48.6]]];
N = 180;                 // outline points
TAPER = 0.965;           // the top is 3.5 % narrower than the foot, as a log is
WALL = 2.0;              // the shell round the hollow (3.0 printed solid: 310 g for the trio)
BARK = 2.0;              // the bark ring seen on the cut face
TOP_T = 0.8;             // the cut face's colour, 4 layers (each layer of it is a colour change)
WELL_R = 20.25;          // 40.5 across: a 38 mm LED tea light drops in and tips out
WELL_D = 14;
FLOOR = 2.4;             // under the well
HOLE_R = 5;              // through the well floor: push the light out with a pencil; vents the hollow
CEIL = 37;               // the hollow's roof, degrees from upright (DETAIL_STANDARD rule 7)
MARK_D = 1.0;            // how deep the dark marks go into the bark
BAND_H = 1.6;            // a row of lenticels: 8 layers; each dash in it 0.8, 1.2 or 1.6 tall
BANDS = [8.0, 16.4, 35.6, 60.4, 79.6, 104.0];   // z of each row's foot
EYE_BANDS = [27.4, 48.6];   // eye apexes; an eye spans 4.2 below to 0.8 above its apex (25 layers)
// Every layer with black in it costs a colour change and its purge; how much black is in the
// layer costs nothing. So the marks are bold and many, but only inside these 6 x 8 + 2 x 25
// = 98 layers, the same ones on all three logs. (A first version spread thin dashes over 8
// two-row bands and 3 eye bands: 139 changes, 86 g into the prime tower. A second kept to
// 66 layers with 0.8 mm dashes and small eyes, and its render read as a white cylinder with
// a few hairlines, not birch.)
RING_W = 0.6;            // tree-ring grooves (DETAIL_STANDARD rule 5: >= 0.4 keeps its depth)
RING_D = 0.4;            // 2 layers
CRACK_D = 0.6;

function r_at(R, s, t) = R * (1 + 0.028 * cos(2 * t + s * 37) + 0.014 * cos(3 * t + s * 71)
                              + 0.008 * cos(5 * t + s * 13) + 0.005 * cos(7 * t + s * 29));
function outline(R, s, d = 0) = [for (i = [0 : N - 1]) let (t = 360 * i / N, r = r_at(R, s, t) - d)
                                 [r * cos(t), r * sin(t)]];

module solid(L, d = 0) linear_extrude(L[1], scale = TAPER) polygon(outline(L[0], L[2], d));

// The hollow keeps every wall WALL thick, so the log weighs what its shell weighs. It is a
// ring round a "tulip": a tube up the middle (the push-out hole runs through it, open at the
// foot), flaring at 37 deg into the sleeve that holds the well. The outer roof closes in at
// 37 deg onto that sleeve just under the cut face. Every downward face is at 37 deg or steeper;
// nothing is bridged. (A first version, one hollow under a cone roof, left the top third solid:
// 346 g and 13 h for the trio.)
SLEEVE = WELL_R + WALL;   // 23.25
TUBE = HOLE_R + 2.0;
module tulip(L) {
    H = L[1];
    z1 = H - WELL_D - FLOOR;                       // the flare reaches the sleeve under the well floor
    z0 = z1 - (SLEEVE - TUBE) / tan(CEIL);
    rotate_extrude($fn = 96) polygon([[0, -1], [TUBE, -1], [TUBE, z0], [SLEEVE, z1], [SLEEVE, H + 1], [0, H + 1]]);
}
module hollow(L) {
    H = L[1];
    zr1 = H - TOP_T - 2.0;                         // the cut face is 3.2 thick over the hollow
    zr0 = zr1 - (L[0] * 1.05 - WALL - SLEEVE) / tan(CEIL);
    difference() {
        hull() {
            translate([0, 0, -1]) linear_extrude(zr0 + 1) scale(TAPER) polygon(outline(L[0], L[2], WALL / TAPER));
            translate([0, 0, zr1 - 0.01]) cylinder(r = SLEEVE, h = 0.01, $fn = 96);
        }
        tulip(L);
    }
    translate([0, 0, -1]) cylinder(r = HOLE_R, h = H + 2, $fn = 48);   // the push-out hole, foot to well
}

module well(L) translate([0, 0, L[1] - WELL_D]) cylinder(r = WELL_R, h = WELL_D + 1, $fn = 120);

// the outer skin the marks live in
module skin(L) difference() { solid(L); translate([0, 0, -1]) scale([1, 1, (L[1] + 2) / L[1]]) solid(L, MARK_D + 0.3); }

// one lenticel: a lens, tapering to a point at each end the way birch's do (square-cut ends
// read as stuck-on tape), centred at angle t, foot at z, l long round the log, h tall. In
// print its height steps by layers, so it comes out as a stepped lens.
module dash(L, t, z, l, h) rotate(t) hull() {
    for (y = [-l / 2, l / 2]) translate([0, y, z + h / 2 - 0.2]) cube([L[0] * 1.2, 0.01, 0.4]);
    translate([0, -l / 4, z]) cube([L[0] * 1.2, l / 2, h]);
}

// a row of lenticels: n dashes, each 0.8, 1.2 or 1.6 tall, sitting anywhere in the row, so no
// two rows read alike. Some come in pairs, one just above the other, as birch's do.
module dash_row(L, z0, rowh, n, seed) {
    a = rands(0, 360, n, seed);
    ln = rands(4, 26, n, seed + 1);
    hh = rands(0, 2.99, n, seed + 2);
    up = rands(0, 1, n, seed + 3);
    for (k = [0 : n - 1]) let (h = 0.8 + 0.4 * floor(hh[k]), z = z0 + 0.4 * floor(up[k] * (rowh - h) / 0.4 + 0.5))
        dash(L, a[k], z, ln[k], h);
}

// a birch "eye": the dark chevron over a branch scar, two bars 14 long and 1.6 thick in a
// shallow inverted V, apex at z. (A block for the scar under it made the eye read as a
// little house with a roof, in the toolpath render.)
EYE_L = 14;
EYE_A = 14;
module eye(L, t, z) rotate(t) {
    for (sgn = [-1, 1]) translate([0, sgn * EYE_L / 2 * cos(EYE_A), z - EYE_L / 2 * sin(EYE_A)])
        rotate([sgn * -EYE_A, 0, 0]) translate([0, -EYE_L / 2, -0.8]) cube([L[0] * 1.2, EYE_L, 1.6]);
}

module mark_shapes(L) {
    s = L[2];
    per = round(2 * PI * L[0] / 40);            // about one dash per 40 mm round the log, per row
    for (b = [0 : len(BANDS) - 1]) if (BANDS[b] + BAND_H < L[1] - TOP_T - 3)
        dash_row(L, BANDS[b], BAND_H, per + round(rands(0, 2.99, 1, s * 100 + b)[0]), s * 7 + b * 11);
    // the eye bands' layers are paid for already: a row of dashes in each, eye or not
    for (b = [0 : len(EYE_BANDS) - 1]) if (EYE_BANDS[b] + 1 < L[1] - TOP_T - 3)
        dash_row(L, EYE_BANDS[b] - 4.2, 4.6, per, s * 41 + b * 11);
    // the eyes face the front (-y), where the listing photos look, one left of centre and one right
    for (e = [0 : len(L[3]) - 1]) eye(L, -90 + [-22, 28][e] + rands(-8, 8, 1, s * 31 + e)[0], L[3][e]);
}

module marks(L) intersection() { skin(L); mark_shapes(L); }

module top_face(L) {
    H = L[1];
    difference() {
        translate([0, 0, H - TOP_T]) intersection() {
            linear_extrude(TOP_T) scale(TAPER) polygon(outline(L[0], L[2], BARK / TAPER));
            translate([0, 0, -1]) cylinder(r = 99, h = 9);
        }
        well(L);
        rings(L);
        cracks(L);
    }
}

// growth rings: closed grooves following the log's own outline, off-centre like a real pith
module rings(L) {
    R = L[0] * TAPER;
    sp = rands(2.6, 3.8, 12, L[2] * 3);
    // The first ring starts 6 mm out: at 3.4, with the pith 1.9 off-centre and the outline's
    // lumps, one grazed the well and left a 0.3 mm sliver of tan (print_fidelity, tall log).
    translate([1.0, -0.7, L[1] - RING_D]) linear_extrude(RING_D + 1)
        for (k = [0 : 11]) let (rho = WELL_R + 6.0 + k * 3.1 + sp[k] - 3.2)
            if (rho * TAPER + 1.3 < R - BARK - 0.8)   // 1.3: the pith offset, so no ring runs into the bark
                difference() {
                    scale(TAPER) polygon(outline(rho, L[2] + k * 3));          // each ring wanders its own way
                    scale(TAPER) polygon(outline(rho - RING_W, L[2] + k * 3));
                }
}

// two drying cracks out from the well, widening toward the bark
module cracks(L) {
    R = L[0] * TAPER;
    ang = rands(0, 360, 2, L[2] * 5);
    for (k = [0 : 1]) rotate(ang[k] + k * 140) translate([0, 0, L[1] - CRACK_D])
        linear_extrude(CRACK_D + 1) polygon([[WELL_R - 1, -0.3], [R * 0.72, -0.55], [R * 0.72, 0.55], [WELL_R - 1, 0.3]]);
}

module body(L) difference() {
    solid(L);
    hollow(L);
    well(L);
    marks(L);
    translate([0, 0, L[1] - TOP_T]) linear_extrude(TOP_T + 1) scale(TAPER) polygon(outline(L[0], L[2], BARK / TAPER));
}

// the whole log as one solid, colours ignored: what the gates check (a union of the three
// colour parts kept their shared faces and read as open edges and 0.8 mm walls)
module gate(L) difference() {
    solid(L);
    hollow(L);
    well(L);
    translate([0, 0, 0]) rings(L);
    cracks(L);
}

module one(L, p) {
    if (p == "gate") gate(L);
    if (p == "body" || p == "log") color("#EDE8DC") body(L);
    if (p == "marks" || p == "log") color("#2B2A28") marks(L);
    if (p == "top" || p == "log") color("#C9A877") top_face(L);
}

if (part == "all") for (i = [0 : 2]) translate([[-95, 0, 95][i], 0, 0]) one(LOGS[i], "log");
else one(LOGS[which], part);
