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
// the sphere's surface exactly through the point where two facets meet, and
// CGAL emitted a zero-area facet at three of the ten -- the same tangency
// class as Technique 60's roof-against-tower, and it moves if you move a
// number. Pushing out by 0.3r also makes each chip a nick in the edge rather
// than a hemisphere scooped out of it, which is what erosion actually does.
//
// And a chip is only placed where the outline is EXPOSED. One landing on the
// stone's bottom corners sits entirely inside the socle, and a cut with no
// path to open air is not a chip -- it is a sealed bubble whose inner shell
// counts as its own body.
module chips() {
    tb = tab_pts();  u = chip_u();  r = chip_r();  y = chip_y();
    m = len(tb) - 1;
    for (i = [0 : chip_n - 1]) {
        f = u[i] * m;  k = floor(f);  t = f - k;
        a = tb[k];  b = tb[min(k + 1, m)];
        p = a + (b - a) * t;
        d = b - a;
        nv = norm(d) > 1e-6 ? [-d[1], d[0]] / norm(d) : [1, 0];
        if (p[1] > sink + r[i] + 1)
            translate([p[0] + nv[0]*0.3*r[i], y[i], p[1] + nv[1]*0.3*r[i] + st_z0])
                sphere(r = r[i]);
    }
}

// Pitting: shallow spherical caps, 0.6-1.3mm deep. Deliberately kept off the
// panel -- a pit through an inscription reads as a misprint, not as age.
//
// The test is vertical only, on purpose. The obvious companion clause -- allow
// a pit that clears the panel SIDEWAYS -- can never fire: the panel is 58 wide
// inside a 72 stone, so the side margin is 7mm total, and a pit centre is held
// 7mm off the edge already. There is no sideways case to allow, so there is no
// clause for one rather than a clause that reads live and is not.
pit_n = 16;
module pits() {
    px = rands(-st_w/2 + 7, st_w/2 - 7, pit_n, 991);
    pz = rands(7, st_h - 9, pit_n, 1237);
    pr = rands(1.9, 3.8, pit_n, 4471);
    for (i = [0 : pit_n - 1])
        if (abs(pz[i] - pl_z) > pl_h/2 + 4)
            translate([px[i], st_t/2 + pr[i]*0.66, pz[i] + st_z0]) sphere(r = pr[i]);
}

// The back gets its own pitting, and it is not decoration for its own sake:
// rendered without it the stone reads as two different objects joined at the
// edge -- a weathered front and a moulded plastic back. It carries no crack
// (one is enough, and a crack that appears on both faces reads as a crack
// straight THROUGH the stone), and it fences the maker's mark the same way
// the front fences the inscription panel.
bpit_n = 12;
module back_pits() {
    px = rands(-st_w/2 + 7, st_w/2 - 7, bpit_n, 2029);
    pz = rands(8, st_h - 9, bpit_n, 8837);
    pr = rands(1.8, 3.6, bpit_n, 6151);
    for (i = [0 : bpit_n - 1])
        if (abs(px[i]) > 17 || abs(pz[i] - 15) > 9)
            translate([px[i], -st_t/2 - pr[i]*0.66, pz[i] + st_z0]) sphere(r = pr[i]);
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
// sits 0.25mm proud and the chain runs 1.35 -> 0.8mm radius, so every link
// cuts between 1.1 and 0.55mm deep and the shallowest is still two full
// layers. Nothing in the chain comes near tangency.
//
// And it used to run down to z=55, which is INSIDE the inscription panel
// (top edge 61) -- a crack through the customer's name is the same defect the
// pits above are fenced away from. It now stops at 66, clear of both styles.
crack_pts = [[-26, 100], [-22, 88], [-24, 76], [-19, 66]];
crack_y   = st_t/2 + 0.25;
module crack() {
    n = len(crack_pts);
    for (i = [0 : n - 2]) hull() {
        translate([crack_pts[i][0],   crack_y, crack_pts[i][1]   + st_z0])
            sphere(r = 1.35 - 0.183*i);
        translate([crack_pts[i+1][0], crack_y, crack_pts[i+1][1] + st_z0])
            sphere(r = 1.35 - 0.183*(i+1));
    }
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
    n = 8;
    px = rands(-pl_w/2 + 3.5, pl_w/2 - 3.5, n, 5501);
    pz = rands(-pl_h/2 + 3.5, pl_h/2 - 3.5, n, 6607);
    pr = rands(1.3, 2.4, n, 7703);
    for (i = [0 : n - 1])
        if (abs(px[i]) > pl_w/2 - 5.5 || abs(pz[i]) > pl_h/2 - 4.5)
            translate([px[i], st_t/2 - 0.2 + pr[i]*0.80, pl_z + pz[i] + st_z0])
                sphere(r = pr[i]);
}

// Face up, back on the bed: the raised inscription is the final top surface
// and the part has no overhang at all.
module plate_for_print() {
    translate([0, pl_z + st_z0, -(st_t/2 - pl_d)]) rotate([90, 0, 0]) plate();
}

if (part == "stone")      stone();
else if (part == "plate") plate_for_print();
else { stone(); if (style == "plate") plate(); }
