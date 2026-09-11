// Personalized tombstone -- a weathered granite headstone on a socle base.
//
// ONE FILE, TWO PERSONALIZATION MODES (Scott's call, 2026-09-11):
//   style = "carved"  the inscription is incised straight into the stone.
//                     One seamless piece, no seam anywhere, but every order
//                     is a fresh render, slice and full print.
//   style = "plate"   the stone carries a blank recess and the inscription
//                     lives on a separate plaque that seats in it. Batch the
//                     stones as stock; print a plaque per order. An inset
//                     plaque is a real monument detail, so the reveal around
//                     it reads as intentional rather than as a seam.
//
// AND TWO TEXT LAYOUTS, from the same three-row geometry (also Scott's call):
//   text_set = "gag"       R.I.P. / HERE LIES / <name>   -- the Halloween buy
//   text_set = "memorial"  <name> / <dates> / <line>     -- year-round, no
//                          seasonal cliff, higher price tolerance
//
// PRINTS UPRIGHT, AND THAT IS THE POINT. The tablet is a 2D outline extruded
// through the thickness, and the outline only ever NARROWS going up, so every
// face on it is either vertical or up-facing: zero overhang, no supports, no
// brim. Printed this way the layer lines run horizontally across the face,
// which on a gravestone reads as sedimentary strata -- the orientation most
// prints fight is the one that flatters this one.

include <BOSL2/std.scad>
$fa = 2;  $fs = 0.4;

part     = "all";        // all | stone | plate
style    = "plate";      // carved | plate
text_set = "gag";        // gag | memorial

// ---- stone ---------------------------------------------------------------
st_w   = 72;             // width at the shoulder
st_h   = 106;            // height above its own base
st_t   = 12;             // thickness
sh_in  = 5;              // shoulder step-in per side
sh_z   = 62;             // shoulder height
nw2    = st_w/2 - sh_in; // half width of the upper tablet = 31
arc_c  = st_h - nw2;     // the round top is a true semicircle of radius nw2

// ---- socle ---------------------------------------------------------------
so_w   = 88;  so_d = 28;  so_h = 18;
so_cham= 2.6;            // top chamfer: 2.6 in over 2.6 up = 45 deg from
                         // vertical, and up-facing, so it self-supports
sink   = 6;              // how far the stone is sunk into the socle
st_z0  = so_h - sink;    // stone's own z origin in world coords

// ---- inscription ---------------------------------------------------------
// Noto Serif Bold, NOT the Trajan-style face this started with. Cinzel
// Decorative is the historically right look for a cut monument -- a
// Trajan-derived Roman caps face -- and it is unprintable at these sizes:
// measured on the real cutter, 13-34% of its strokes fall under one 0.42mm
// extrusion, and a recess narrower than one bead is not cut at all, so it
// comes out as broken scratches. Noto Serif Bold measures 0.0% under a bead
// at every size used here, lower quartile 1.3-2.6 extrusions. A serif that
// prints beats a better serif that does not.
//
// Whatever family is named here, check it with fc-list first: an unregistered
// or misspelled family renders EMPTY text geometry and raises no error.
ins_font  = "Noto Serif:style=Bold";
ins_depth = 1.2;            // incised, on the stone
plq_proud = 1.0;            // RAISED, on the plaque -- see plate()
mark_font = "Montserrat:style=Black";

// AUTO-FIT, because this is a personalized product and the name is whatever
// the customer types. OpenSCAD 2021.01 has no textmetrics(), so the font's own
// per-character advances are baked in below, straight out of its hmtx table.
// OpenSCAD renders text() at a stable 1.34x the advance sum (measured across
// five strings, ratio 1.337-1.341), so 1.36 is that with a little margin.
//
// A row is [string, nominal size, z]. The nominal size is a CEILING: a short
// name gets it, a long one shrinks to fit. Below about size 6 the strokes stop
// being reliably printable, which sets a real limit of roughly 8 characters at
// the default plaque width -- stated in the printing notes rather than left
// for someone to discover.
ADV = [
    0.2600, 0.3820, 0.5080, 0.5590, 0.5590, 0.9060, 0.8010, 0.2900, 0.4000, 0.4000,
    0.5020, 0.5590, 0.2940, 0.3100, 0.2940, 0.2880, 0.5590, 0.5590, 0.5590, 0.5590,
    0.5590, 0.5590, 0.5590, 0.5590, 0.5590, 0.5590, 0.3040, 0.3040, 0.5590, 0.5590,
    0.5590, 0.5500, 0.9210, 0.7530, 0.6720, 0.6680, 0.7670, 0.6530, 0.6210, 0.7690,
    0.8190, 0.4010, 0.3970, 0.7340, 0.6540, 0.9520, 0.7880, 0.7870, 0.6380, 0.7870,
    0.7070, 0.5860, 0.6530, 0.7470, 0.6980, 1.0670, 0.7320, 0.6930, 0.6660, 0.4140,
    0.2880, 0.4140, 0.5590, 0.4590, 0.3340, 0.5990, 0.6490, 0.5270, 0.6490, 0.5710,
    0.4070, 0.5600, 0.6670, 0.3520, 0.3450, 0.6360, 0.3520, 0.9860, 0.6670, 0.6130,
    0.6450, 0.6480, 0.5230, 0.4880, 0.4050, 0.6670, 0.6060, 0.8560, 0.6460, 0.5790,
    0.5290, 0.4420, 0.5590, 0.4420, 0.5590
];
K_ADV = 1.36;
function adv_sum(s) = len(s) == 0 ? 0 :
    [for (i = [0 : len(s)-1]) ADV[max(0, min(94, ord(s[i]) - 32))]]
    * [for (i = [0 : len(s)-1]) 1];
function fit_size(s, nominal, max_w) =
    min(nominal, max_w / (K_ADV * max(adv_sum(s), 0.001)));

// rows are [string, size, z] in the panel's own frame, z measured from the
// panel centre. One geometry, either content.
rows_gag = [["R.I.P.",      13.0,  12.5],
            ["HERE LIES",    6.6,  -1.0],
            ["BARNABY",     10.0, -13.0]];
rows_mem = [["MITTENS",     10.5,  12.5],
            ["2011 - 2026",  6.4,  -1.0],
            ["REST WELL",    6.0, -13.0]];
function rows() = text_set == "memorial" ? rows_mem : rows_gag;

// ---- plaque --------------------------------------------------------------
pl_w  = 58;  pl_h = 42;  pl_d = 3.2;   // recess in the stone face
pl_r  = 2;                             // recess corner radius
pl_z  = 40;                            // recess centre, stone-local. Kept
                                       // wholly BELOW the shoulder at 62, so
                                       // the pocket sits in full-width stone
                                       // with 7mm of margin each side rather
                                       // than 1mm up in the neck.
// 0.2mm per side. Technique 43 measured this same number on a real
// tongue-and-groove case lid (0.195) and on this shop's own snap box (0.190)
// -- it is the standard slip fit for two SEPARATELY printed parts, and it is
// not the same question as a print-in-place gap.
pl_clr = 0.2;

module rr(w, d, r) { offset(r = r) square([w - 2*r, d - 2*r], center = true); }

// =========================================================================
// The tablet outline: up the side, round the shoulder, up the neck, over a
// true semicircular head. Built as a half and mirrored, so the two sides can
// never drift apart.
function tab_half(n = 30) = concat(
    [[-st_w/2, 0]],
    [for (i = [0 : 8]) let (a = 180 - 90*i/8)
        [-nw2 + sh_in*cos(a), sh_z + sh_in*sin(a)]],
    [[-nw2, arc_c]],
    [for (i = [0 : n]) let (a = 180 - 90*i/n)
        [nw2*cos(a), arc_c + nw2*sin(a)]]);

function tab_pts() = let (h = tab_half())
    concat(h, [for (i = [len(h)-2 : -1 : 0]) [-h[i][0], h[i][1]]]);

module tablet_2d() { polygon(tab_pts()); }

module stone_solid() {
    translate([0, 0, st_z0]) rotate([90, 0, 0])
        linear_extrude(st_t, center = true) tablet_2d();
}

module socle() {
    hull() {
        linear_extrude(0.01) rr(so_w, so_d, 3);
        translate([0, 0, so_h - so_cham]) linear_extrude(0.01) rr(so_w, so_d, 3);
        translate([0, 0, so_h]) linear_extrude(0.01)
            rr(so_w - 2*so_cham, so_d - 2*so_cham, 3);
    }
}

// =========================================================================
// WEATHERING. Technique 52 measured this shop's entire catalogue at 1.0-1.086
// rugosity against a reference corpus median of 1.061 -- we have been shipping
// the right shapes with no surface on them. A gravestone is the one object
// where the weathering IS the product, so it is modelled rather than implied.
// Every seed is fixed, so the "random" chipping is identical on every render.
//
// REBUILT 2026-09-11 (Scott: "it looks like a cheese style cut out"). Every
// scar on the first version was ONE SPHERE, and a sphere pushed into a flat
// face can only ever make a circular rim around an evenly curved bowl. Thirty
// eight of those, every one of them biting the same fraction of its own
// radius, is a wheel of cheese -- the regularity is the tell, not the size.
// This section is the only part of the model that changed.
//
// THE PRIMITIVE IS A SPALL, NOT A BALL. Each scar is the convex hull of six
// spheres of DIFFERENT radii at scattered offsets, so its surface is a
// patchwork of caps joined by the flat bridges between them: the rim it cuts
// is a ragged polygon and its floor is tilted and stepped rather than dished.
// It is then squashed along one in-plane axis and spun to a random heading, so
// nothing is round in plan and no two scars share a profile.
//
// FOUR THINGS ARE RANDOMISED SEPARATELY, and that is the point -- one shared
// "size" parameter is what made the first version look stamped:
//   R  how big the scar is
//   d  how deep it actually bites, INDEPENDENT of how big it is
//   e  how elongated it is in plan
//   a  which way that elongation points
// A broad shallow flake and a small deep gouge are different events on a real
// stone; tying depth to radius made every scar the same event at five sizes.
//
// AND THEY CLUSTER. Around a third carry one or two smaller satellites
// overlapping them. Real spalling is not a Poisson scatter of isolated dots --
// one flake takes its neighbours with it, and the compound scar that leaves,
// with a floor at two or three levels, is the single biggest difference
// between this and the sphere version.
// THE CUTTER IS A FACETED FLAKE, AND THAT IS FROM THE LITERATURE, NOT TASTE
// (rebuilt 2026-09-11, second pass -- Scott: "still too rounded looking").
// The first rebuild made the scars irregular but kept hulling SPHERES, so
// every rim was still a smooth curve. Checked against how stone actually
// breaks rather than guessing twice:
//
//   Rock & Gem, on conchoidal fracture: "Unlike the JAGGED BREAKS OF COMMON
//   GRANITE, a conchoidal break produces a surface that catches light in a
//   series of shimmering, curved arcs." Granite -- which is what a headstone
//   is -- does not break in smooth curves at all. Curved scars were modelling
//   obsidian.
//
//   ICOMOS-ISCS Illustrated Glossary on Stone Deterioration Patterns, the
//   standard reference for this vocabulary:
//     FRAGMENTATION  "into portions of variable dimensions that are irregular
//                    in form, thickness and volume", with the substrate sound
//                    "on both sides of the DETACHMENT PLANE"
//     Splintering    "detachment of SHARP, SLENDER pieces of stone"
//                    (Fr. "aux ARETES VIVES" -- live edges)
//     Chipping       "breaking off of pieces ... FROM THE EDGES of a block"
//     Scaling        detaching "PARALLEL TO THE STONE SURFACE", thickness
//                    "negligeable compared to its surface dimension"
//     Rounding       "preferential erosion of ORIGINALLY ANGULAR stone"
//
// Every one of those says the same thing geometrically: the floor of a scar
// is a PLANE, its rim is a straight-edged polygon, and rounding is what
// happens to that LATER -- it is a separate decay pattern, not the default.
//
// So the cutter is the convex hull of a point cloud held near two parallel
// planes. Hulling tiny cubes is how you take the convex hull of a point set
// in OpenSCAD; 0.05mm of cube is slop too small to round an edge. The result
// has a planar floor (the detachment plane), planar side facets meeting it at
// hard angles (the rim), and no curved surface anywhere on it. It is also
// CHEAPER than the sphere version -- 8 vertices per point instead of ~100.
//
// e stretches it in plane; f flattens it into the face. f well under 1 is a
// scale -- thin, broad, parallel to the surface, exactly as defined above.
sp_n = 7;
module spall(sd, R, e = 1, f = 1) {
    ax = rands(-R, R, sp_n, sd);
    az = rands(-R, R, sp_n, sd + 101);
    bx = rands(-R, R, sp_n, sd + 211);
    bz = rands(-R, R, sp_n, sd + 307);
    jy = rands(-0.12*R, 0.12*R, 2*sp_n, sd + 401);
    scale([e, f, 1])
        hull() {
            for (i = [0 : sp_n - 1])
                translate([ax[i], -R + jy[i], az[i]]) cube(0.05, center = true);
            for (i = [0 : sp_n - 1])
                translate([bx[i],  R + jy[sp_n + i], bz[i]]) cube(0.05, center = true);
        }
}

// One scar against a face whose outward normal is +Y (side = 1) or -Y (-1).
// The spall's half-extent is about R, so seating its centre at face + R - d
// makes it bite d deep; its own lumpiness then varies that by roughly +/-20%
// across the scar, which is the irregularity a sphere cannot give at any size.
//
// Rotation is about Y only, deliberately: a Y-rotation leaves the y-extent
// untouched, so the bite depth stays exactly d whatever the heading. Tumbling
// the spall on all three axes would look no better and would make every depth
// a guess.
// THE DEPTH CLAMP IS LOAD-BEARING, not defensive tidiness. Seating the spall
// at face + R*f - d bites d deep -- but if d exceeds the cutter's own y
// half-extent, the centre sinks BELOW the face, and a small enough cutter then
// sits entirely inside the stone. That is not a shallow scar, it is a sealed
// void: the mesh still gates watertight and single-bodied, and the only thing
// that sees it is CGAL reporting Volumes: 4 instead of 2. It happened here the
// first time the flattened grain layer ran (f ~ 0.3 makes R*f small) and again
// on cluster satellites, whose radius is a fraction of the parent's while
// their depth was drawn from a fixed range.
//
// Clamping d to 0.8 * R*f keeps the centre outside the face by construction,
// for every scar, at every size, which is a guarantee rather than a range that
// happens to work. A scar that wanted to be deeper than its cutter is wide was
// never going to look like what it was asking for anyway.
function bite(R, f, d) = min(d, 0.8 * R * f);

module scar(sd, side, x, z, R, d, e, a, sat = 0, f = 1) {
    translate([x, side * (st_t/2 + R*f - bite(R, f, d)), z + st_z0])
        rotate([0, a, 0]) spall(sd, R, e, f);
    // A SATELLITE MUST GENUINELY OVERLAP ITS PARENT, not merely land near it.
    // At +/-1.15R with radii from 0.38R the two solids could meet along a
    // sliver, and where that happened at the stone's own silhouette it left a
    // rind of stone 0.30 x 0.12 x 0.41mm standing free -- 0.0015 cubic
    // millimetres, smaller than one extrusion bead in every dimension, and a
    // separate body as far as the mesh is concerned. Isolating it took one
    // render per cutter group: chips, grain and flanks were each clean alone,
    // the crown clusters were not, and re-seeding the other two (twice) never
    // moved it, which is the tell that a seed was never the cause.
    //
    // At +/-0.85R with radii from 0.45R the overlap is at least 0.6R by
    // construction, so there is no sliver to leave behind. Tighter compound
    // scars read better too -- a cluster should look like one event that took
    // its neighbours with it, not three dots that happen to touch.
    if (sat > 0) {
        ux = rands(-0.85*R, 0.85*R, sat, sd + 401);
        uz = rands(-0.85*R, 0.85*R, sat, sd + 503);
        uR = rands( 0.45*R, 0.75*R, sat, sd + 601);
        ud = rands( 0.45,   1.40,   sat, sd + 701);
        for (k = [0 : sat - 1])
            translate([x + ux[k],
                       side * (st_t/2 + uR[k]*f - bite(uR[k], f, ud[k])),
                       z + uz[k] + st_z0])
                rotate([0, a + 55*(k + 1), 0])
                    spall(sd + 811 + k, uR[k], 1 + 0.5*(e - 1), f);
    }
}

// Chips bite the outline itself, which is what actually reads at arm's length
// -- a perfect arc is the tell that something was printed rather than carved.
chip_n = 10;
function chip_u() = rands(0.04, 0.96, chip_n, 20260911);
function chip_r() = rands(1.5,  4.0,  chip_n, 7731);
function chip_y() = rands(-st_t/2 - 1, st_t/2 + 1, chip_n, 313);

// Two things here are not incidental.
//
// The centre is interpolated ALONG a segment and then pushed out along that
// segment's own outward normal. Snapping it to an outline VERTEX instead put
// the cutter's surface exactly through the point where two facets meet, and
// CGAL emitted a zero-area facet at three of the ten -- the same tangency
// class as Technique 60's roof-against-tower, and it moves if you move a
// number. Pushing out by 0.3r also makes each chip a nick in the edge rather
// than a hemisphere scooped out of it, which is what erosion actually does.
//
// And a chip is only placed where the outline is EXPOSED. One landing on the
// stone's bottom corners sits entirely inside the socle, and a cut with no
// path to open air is not a chip -- it is a sealed bubble whose inner shell
// counts as its own body.
//
// The cutter is a spall now, tumbled about Z so the nick runs across the edge
// at a slant instead of taking a clean round bite out of it. This is the one
// place a spall rotates about something other than Y: an edge has no face to
// hold a depth against, so there is no depth to lose.
module chips() {
    tb = tab_pts();  u = chip_u();  r = chip_r();  y = chip_y();
    ca = rands(0, 360, chip_n, 4409);
    ce = rands(1.2, 1.8, chip_n, 5519);
    m = len(tb) - 1;
    for (i = [0 : chip_n - 1]) {
        f = u[i] * m;  k = floor(f);  t = f - k;
        a = tb[k];  b = tb[min(k + 1, m)];
        p = a + (b - a) * t;
        d = b - a;
        nv = norm(d) > 1e-6 ? [-d[1], d[0]] / norm(d) : [1, 0];
        if (p[1] > sink + r[i] + 1)
            translate([p[0] + nv[0]*0.3*r[i], y[i], p[1] + nv[1]*0.3*r[i] + st_z0])
                rotate([0, 0, ca[i]]) spall(6100 + 23*i, r[i], ce[i]);
    }
}

// Front-face scarring, placed by ZONE rather than by one scatter with a fence.
//
// The scatter-plus-fence version put nearly every scar in the crown and left
// the bottom two thirds of the face bare, which reads as "the top weathered
// and the rest is new". The panel is 42 tall in the middle of a 106 stone, so
// a uniform scatter loses half its candidates to the fence and the survivors
// are almost all above it. Three explicit zones instead, each sized to the
// room it actually has:
//
//   crown   z 63-96, full width        the exposed top, so the big scars
//   sill    z  7-17, full width        the band between socle and panel
//   flanks  |x| 29.5-34.5, z 20-60     the 7mm margins either side of the
//                                      panel: small scars only, and they are
//                                      allowed to run off the edge
//
// The flanks are what matter for the read. They are the only scars level with
// the inscription, and without them the middle of the stone is a blank
// rectangle with a plaque sitting on it. Nothing is placed ON the panel -- a
// pit through an inscription reads as a misprint, not as age -- and the zones
// are what enforce that now, instead of a fence that also had to guess at how
// far a cluster's satellites reach.
module zone_scars(n, sd, x0, x1, z0, z1, R0, R1, d0, d1, e1, cl) {
    px = rands(x0, x1, n, sd);
    pz = rands(z0, z1, n, sd + 1301);
    pR = rands(R0, R1, n, sd + 1409);
    pd = rands(d0, d1, n, sd + 1511);
    pe = rands(1.05, e1, n, sd + 1613);
    pa = rands(0, 360, n, sd + 1721);
    pc = rands(0, 1,   n, sd + 1823);
    ps = rands(0, 1,   n, sd + 1931);
    for (i = [0 : n - 1])
        scar(sd + 37*i, 1,
             px[i] * (ps[i] < 0.5 ? 1 : -1), pz[i],
             pR[i], pd[i], pe[i], pa[i],
             pc[i] < cl*0.45 ? 2 : (pc[i] < cl ? 1 : 0));
}

module pits() {
    zone_scars(11, 3100,  0.0, 30.0, 63, 96,  1.6, 3.6, 0.5, 2.2, 1.8, 0.32);
    zone_scars( 8, 3700,  0.0, 31.0,  7, 17,  1.4, 2.9, 0.5, 1.8, 1.7, 0.30);
    zone_scars(12, 4300, 29.5, 34.5, 20, 60,  1.1, 2.3, 0.5, 1.6, 1.6, 0.22);
    grain(48, 5900,  1, true);
}

// GRAIN. The discrete scars above are the events; this is the surface they
// happened to. Without it the stone between the chips is glass-smooth, and
// under real light that one fact reads as plastic no matter how good the chips
// are -- confirmed on a lit render before this existed. These are the same
// spall, flattened hard (f ~ 0.4) so each is a broad shallow scallop 0.4-0.9mm
// deep rather than a hole: worn-away surface, not damage.
//
// 0.4mm is the floor on purpose. At 0.2mm layers that is two layers of relief,
// which shows; anything shallower is under a layer and the slicer simply does
// not cut it, so it would cost render time and print time to produce nothing.
//
// Placement is a straight scatter with one rejection test: nothing may land on
// the inscription panel, checked against the scar's own in-plane reach rather
// than a fixed margin, since these vary in size. `side` lets the back reuse it
// unchanged -- the back has no panel, so pl_keep is passed false there.
module grain(n, sd, side, pl_keep) {
    px = rands(-st_w/2 + 2, st_w/2 - 2, n, sd);
    pz = rands(6, st_h - 5, n, sd + 2111);
    pR = rands(1.6, 3.0, n, sd + 2221);
    pd = rands(0.35, 0.70, n, sd + 2333);
    pe = rands(1.05, 1.75, n, sd + 2447);
    pf = rands(0.34, 0.58, n, sd + 2551);
    pa = rands(0, 360, n, sd + 2663);
    for (i = [0 : n - 1]) {
        reach = pR[i] * pe[i] + 1.5;
        clear = !pl_keep
             || abs(px[i]) - reach > pl_w/2
             || abs(pz[i] - pl_z) - reach > pl_h/2;
        if (clear)
            scar(sd + 41*i, side, px[i], pz[i], pR[i], pd[i], pe[i], pa[i], 0, pf[i]);
    }
}

// The back gets its own scarring, and it is not decoration for its own sake:
// rendered without it the stone reads as two different objects joined at the
// edge -- a weathered front and a moulded plastic back. It carries no crack
// (one is enough, and the same crack on both faces reads as a crack straight
// THROUGH the stone), and it fences the maker's mark the way the front zones
// fence the panel. One scatter is fine here because there is no panel taking
// the middle of the face out of play.
bpit_n = 15;
module back_pits() {
    px = rands(-st_w/2 + 6, st_w/2 - 6, bpit_n, 2029);
    pz = rands(8, st_h - 9, bpit_n, 8837);
    pR = rands(1.5, 3.9, bpit_n, 6151);
    pd = rands(0.45, 2.1, bpit_n, 9931);
    pe = rands(1.05, 1.8, bpit_n, 1451);
    pa = rands(0, 360, bpit_n, 3571);
    pc = rands(0, 1, bpit_n, 6229);
    for (i = [0 : bpit_n - 1])
        if (abs(px[i]) > 19 || abs(pz[i] - 15) > 11)
            scar(4700 + 31*i, -1, px[i], pz[i], pR[i], pd[i], pe[i], pa[i],
                 pc[i] < 0.30 ? 1 : 0);
    grain(30, 7300, -1, false);
}

// The socle weathers too. A crisp moulded base under a chewed-up stone reads
// as two different materials bolted together -- and the base is the part that
// actually sits in dirt, so if anything it should be the rougher of the two.
// Grain only, no chips: the socle's edges are what the print stands on and
// what the eye uses to read it as level, and nibbling them buys nothing.
//
// Nothing is cut below z = 4.5. The first few millimetres are the bed-contact
// region and the part of the base a viewer reads as the ground line; a scar
// there costs first-layer adhesion and gains no appearance.
module socle_wear() {
    n = 7;
    fx = rands(-so_w/2 + 6, so_w/2 - 6, n, 1213);
    fz = rands(4.5, so_h - 3.5, n, 1327);
    fR = rands(1.6, 3.0, n, 1439);
    fd = rands(0.40, 0.85, n, 1553);
    fe = rands(1.10, 1.80, n, 1667);
    ff = rands(0.34, 0.55, n, 1789);
    fa = rands(0, 360, n, 1861);
    fs = rands(0, 1, n, 1973);
    for (i = [0 : n - 1])
        translate([fx[i],
                   (fs[i] < 0.5 ? 1 : -1) * (so_d/2 + fR[i]*ff[i] - bite(fR[i], ff[i], fd[i])),
                   fz[i]])
            rotate([0, fa[i], 0]) spall(9100 + 43*i, fR[i], fe[i], ff[i]);

    // The two ends. rotate([0,0,90]) swaps the spall's own stretch and flatten
    // axes into world Y and X, so the same primitive works against a face whose
    // normal is X without needing a second version of it.
    m = 4;
    ey = rands(-so_d/2 + 5, so_d/2 - 5, m, 2141);
    ez = rands(4.5, so_h - 3.5, m, 2251);
    eR = rands(1.6, 3.0, m, 2371);
    ed = rands(0.40, 0.80, m, 2477);
    ef = rands(0.34, 0.55, m, 2591);
    es = rands(0, 1, m, 2683);
    for (i = [0 : m - 1])
        translate([(es[i] < 0.5 ? 1 : -1) * (so_w/2 + eR[i]*ef[i] - bite(eR[i], ef[i], ed[i])),
                   ey[i], ez[i]])
            rotate([0, 0, 90]) spall(9700 + 47*i, eR[i], 1.4, ef[i]);
}

// One crack, hull-chained so it is a continuous groove rather than a row of
// beads -- the same lesson as Technique 17's smile.
//
// TWO THINGS HERE WERE WRONG IN THE FIRST PASS AND ARE WORTH THE COMMENT.
//
// It faded out by shrinking the sphere while leaving its centre 0.7mm PROUD of
// the face, so the cut depth was r - 0.7: it started at 0.45mm, and the last
// two links cut 0.06mm and nothing at all. A 0.06mm kiss is not a shallow
// crack, it is a surface tangency -- the exact generator of zero-area facets
// this file has already been bitten by twice -- and 0.45mm is under three
// layers, which at arm's length is not a crack, it is nothing. The centre now
// sits 0.25mm proud and the radii run 1.35 down to 0.6, so every link cuts
// between 1.1 and 0.35mm and nothing comes near tangency.
//
// And it used to run down to z=55, which is INSIDE the inscription panel
// (top edge 61) -- a crack through the customer's name is the same defect the
// zones above keep scars away from. It stops at 66, clear of both styles.
//
// The path is denser and no longer monotonic (2026-09-11, same pass as the
// spalls): a four-point chain of steadily shrinking spheres tapers smoothly,
// which is the one thing a fracture never does. The radii now wander up as
// well as down along the run, and two short branches split off and die -- a
// real crack forks where it meets a hard grain and one fork stops.
crack_pts = [[-26, 100], [-24.5, 95], [-21.5, 89], [-23, 83],
             [-24.5, 77], [-21, 72], [-19.5, 66]];
crack_r   = [1.35, 1.05, 1.25, 0.9, 1.15, 0.8, 0.6];
crack_br  = [[2, [-27.5, 84.5], 0.7], [4, [-20.5, 74.5], 0.62]];
crack_y   = st_t/2 + 0.25;
module crack_link(p0, r0, p1, r1) {
    hull() {
        translate([p0[0], crack_y, p0[1] + st_z0]) sphere(r = r0);
        translate([p1[0], crack_y, p1[1] + st_z0]) sphere(r = r1);
    }
}
module crack() {
    for (i = [0 : len(crack_pts) - 2])
        crack_link(crack_pts[i], crack_r[i], crack_pts[i+1], crack_r[i+1]);
    for (b = crack_br)
        crack_link(crack_pts[b[0]], crack_r[b[0]] * 0.8, b[1], b[2]);
}
// =========================================================================
// TEXT HANDEDNESS, MEASURED RATHER THAN REASONED. Every face-mounted string
// in this file goes through rotate([90,0,180]) on the FRONT (+Y) face and
// rotate([90,0,0]) on the BACK. That is the opposite of what the matrix
// algebra looked like it said, and the algebra was wrong: extruding a big
// asymmetric glyph on its own and photographing it from the front settled it
// in one render. rotate([90,0,0]) sends local +Z to world -Y, so the readable
// side of the text faces AWAY from a front viewer and the whole string comes
// out mirrored -- and an incised cut shows the same mirror its cutter has.
// rotate([90,0,180]) sends local +Z to +Y, so the extrude runs out through
// the front face toward the reader and the string reads left to right; the
// translate then has to START the extrude inside the stone and run outward,
// which is why every front-face translate below subtracts its own depth.
//
// This is exactly why Technique 58 exists: a 1.2mm engraving is invisible in
// a flat head-on render (confirmed again here -- the whole test plate came
// back as three flat colours), so verifying the cut in place proves nothing.
// Render the CUTTER as a solid, look at it from where the customer stands.
//
// KNOWN, MEASURED, AND HARMLESS: in "carved" style some strings leave CGAL
// emitting a handful of zero-area facets. Located rather than guessed at --
// all ten of them, in the memorial set, sat at ONE z on the y=6 plane, spanning
// the exact width of the bottom row, because every letter in a row shares a
// baseline and that puts 42 collinear vertices in a straight line through a
// single huge planar face. That is a constrained-triangulation sliver, not
// geometry: the mesh is still watertight, still one body, still Euler 2, its
// volume is right to 0.1%, and PrusaSlicer takes it with zero warnings or
// repairs. It is NOT worth nudging a number to make disappear -- the string is
// whatever the customer types, so any number that happens to satisfy CGAL for
// "REST WELL" says nothing about the next name. mesh_gate.py flags it and
// should keep flagging it; the printing notes say what it is.
//
// ALL ROWS AS ONE 2D UNION, then a single extrude -- not one difference per
// row. Cut separately, "BARNABY" was clean on its own and produced two
// zero-area facets in combination with any other row: a CGAL interaction
// between successive differences, not a defect in any glyph. Unioning the
// rows in 2D first removes the interaction entirely, and is the way to write
// it anyway when every row is cut to the same depth from the same face.
module inscription_2d(max_w) {
    for (r = rows())
        translate([0, r[2]])
            text(r[0], size = fit_size(r[0], r[1], max_w), font = ins_font,
                 halign = "center", valign = "center");
}

module inscription_cut(face_y, max_w) {
    translate([0, face_y - ins_depth, pl_z + st_z0]) rotate([90, 0, 180])
        linear_extrude(ins_depth + 0.4) inscription_2d(max_w);
}

module inscription() { inscription_cut(st_t/2, st_w - 12); }

// Starts 0.5mm OUTSIDE the face and cuts inward to exactly pl_d. Placed to
// END at the right depth instead, it began at y = 2.8 and finished at -1.4 --
// entirely inside the stone, never reaching the face. That is not a recess,
// it is a sealed -10.4cm3 cavity, and the mesh still gated watertight;
// component_count and CGAL's Volumes: 3 were the only things that saw it.
module plate_pocket() {
    translate([0, st_t/2 + 0.5, pl_z + st_z0]) rotate([90, 0, 0])
        linear_extrude(pl_d + 0.5) rr(pl_w, pl_h, pl_r);
}

// The standing maker's-mark rule, on the back of the stone where it is hidden
// in normal use. "OBC" rather than the full wordmark: at the same footprint
// every stroke is 3.4x thicker, which is the difference between a mark that
// prints and one the slicer drops entirely.
//
// The back face is the one case that takes the OTHER rotation: a reader of the
// back stands at -Y, so the handedness that reads correctly there is the one
// that reads mirrored on the front. rotate([90,0,0]) runs the extrude from
// inside the stone out through the back face, and the mark reads left to
// right to someone looking at it. Same character-map check as the front.
mark_depth = 0.8;
module back_mark() {
    translate([0, -st_t/2 + mark_depth, 15 + st_z0]) rotate([90, 0, 0])
        linear_extrude(mark_depth + 0.4)
            text("OBC", size = 7.5, font = mark_font, halign = "center", valign = "center");
}

// =========================================================================
module stone() {
    difference() {
        union() { socle(); stone_solid(); }
        chips();
        pits();
        back_pits();
        socle_wear();
        crack();
        back_mark();
        if (style == "plate") plate_pocket(); else inscription();
    }
}

// THE PLAQUE IS MODELLED SEATED AND FLIPPED ONLY ON EXPORT -- authored facing
// the way it sits in the stone, which is the only pose its fit can be reasoned
// about in, with plate_for_print() turning it face-up for the bed
// (Technique 55d). Every number here is therefore directly comparable to the
// pocket's: the slab's outer face lands at y = 5.8, 0.2mm below the stone's,
// and the letters run from there out to 6.8.
//
// ITS LETTERS ARE RAISED, where the stone's are incised, and that is a
// material decision rather than a style one. A cut stone is incised; a plaque
// set into one is cast, and cast letters stand proud. It is also the more
// printable of the two: an incised stroke narrower than one 0.42mm bead is
// simply not cut, while a raised stroke that narrow still prints as a single
// bead ridge. And printed face-up the letters are the last thing laid down on
// a flat top surface, which is the best an FDM machine does.
module plate_letters() {
    translate([0, st_t/2 - 0.5, pl_z + st_z0]) rotate([90, 0, 180])
        linear_extrude(plq_proud + 0.3) inscription_2d(pl_w - 8);
}

// Pits are cut from the slab AND letters together -- one difference over one
// union -- not from the slab before the letters go on. That ordering is worth
// keeping for its own sake (it is what the shape actually means: a pitted
// plaque, not a pitted slab that letters were added to afterwards), but be
// honest about what fixed what. This construction was arrived at while
// chasing two zero-area facets that appeared for some names and not others,
// and it did NOT clear them: BARNABY and MITTENS still produced two each,
// ELEANOR and OZYMANDIAS none. What actually cleared them, on every name
// tested, was changing where the letter extrusion starts and which way it
// runs -- the handedness fix above, made for an unrelated reason. A boolean
// artifact that moves when a neighbouring extrusion moves was never inherent;
// "CGAL just does this" is a conclusion to hold loosely while anything else
// in the same region is still changing.
module plate() {
    difference() {
        union() {
            translate([0, st_t/2 - pl_d, pl_z + st_z0]) rotate([-90, 0, 0])
                linear_extrude(pl_d - 0.2)
                    rr(pl_w - 2*pl_clr, pl_h - 2*pl_clr, pl_r - pl_clr);
            plate_letters();
        }
        plate_pits();
    }
}

// The plaque carries the stone's weathering too, at half depth and kept to the
// margins -- a pristine flat plaque on a chipped stone reads as two objects
// rather than one.
module plate_pits() {
    n = 10;
    px = rands(-pl_w/2 + 3.5, pl_w/2 - 3.5, n, 5501);
    pz = rands(-pl_h/2 + 3.5, pl_h/2 - 3.5, n, 6607);
    pR = rands(1.4, 2.8, n, 7703);
    pd = rands(0.40, 0.80, n, 8807);
    pe = rands(1.05, 1.70, n, 9013);
    pf = rands(0.34, 0.58, n, 9203);
    pa = rands(0, 360, n, 9403);
    fy = st_t/2 - 0.2;
    for (i = [0 : n - 1])
        if (abs(px[i]) > pl_w/2 - 5.5 || abs(pz[i]) > pl_h/2 - 4.5)
            translate([px[i],
                       fy + pR[i]*pf[i] - bite(pR[i], pf[i], pd[i]),
                       pl_z + pz[i] + st_z0])
                rotate([0, pa[i], 0]) spall(8300 + 53*i, pR[i], pe[i], pf[i]);
}

// Face up, back on the bed: the raised inscription is the final top surface
// and the part has no overhang at all.
module plate_for_print() {
    translate([0, pl_z + st_z0, -(st_t/2 - pl_d)]) rotate([90, 0, 0]) plate();
}

if (part == "stone")      stone();
else if (part == "plate") plate_for_print();
else { stone(); if (style == "plate") plate(); }
