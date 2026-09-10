// Wall charging shelf -- a phone shelf that mounts below a wall outlet.
//
// MOUNTING IS SCREWS, DELIBERATELY. Two keyhole slots for #6/#8 screws into
// studs or drywall anchors, plus one anti-lift screw at the bottom. The pitch
// for this design said "screw-to-wall or command-strip"; the adhesive half of
// that is withdrawn on purpose. A 65mm cantilever holding a phone loads an
// adhesive strip in PEEL at its top edge, which is the one direction those
// strips are worst at and which 3M's own guidance excludes shelves for. A
// mounting method that fails slowly and drops a phone is not something to
// ship to strangers. Likewise the shelf does NOT hang on the outlet's cover
// screw -- outlet plates vary and that screw holds a live electrical fixture.
//
// PRINTS BACK-FLAT, no supports. The back plate lies on the bed and the shelf
// grows upward, so world +Z here is DEPTH OUT FROM THE WALL and is also the
// build direction. Everything below is reasoned in that frame:
//
//     world X = along the wall (width)      -- a bed axis
//     world Y = up the wall (height)        -- a bed axis
//     world Z = out from the wall (depth)   -- the BUILD axis
//
// That orientation is what makes the whole thing support-free: the deck, the
// side panels and the back plate are all walls standing on the bed, and the
// bracket's concave free edge rises monotonically in Z, so its face is
// up-facing everywhere (see panel_2d). Only two features can overhang at all,
// and both are shaped for it -- the front lip's underside is a 39 deg ramp,
// and the deck's plug slot has a 45 deg peaked roof instead of a flat bridge.

$fa = 2;  $fs = 0.4;

part = "shelf";             // shelf | plate | panel | deck

// ---- overall ------------------------------------------------------------
W   = 120;                  // along the wall
H   = 90;                   // up the wall (back plate)
Dp  = 65;                   // out from the wall (deck depth)

plate_t = 2.52;             // 6 x 0.42. Whole extrusions, per the label bin's
deck_t  = 2.94;             // 7 -- a 1.6mm wall left 0.34mm of slow gap-fill
panel_t = 3.36;             // 8    and sliced 48 MINUTES slower on LESS material.

deck_y  = 0;                // deck TOP surface -- the datum everything hangs off
deck_b  = deck_y - deck_t;
plate_lo = -H/2;            // -45
plate_hi =  H/2;            //  45

rail_h  = 8;                // side rails and front lip, above the deck
lip_run = 10;               // ramp length, in depth, under the front lip.
                            // 8 up over 10 out = 38.7 deg from vertical in the
                            // print. The obvious lip (thin slab, 3mm of depth)
                            // would be a 73 deg overhang -- the ramp is not
                            // decoration, it is the only reason this prints.

corner_r = 6;
brd_p    = 3.36;            // solid frame left around the plate lattice
brd_s    = 2.52;            // and around the panel lattice (6 x 0.42) -- the
                            // panel has far less area to spend on a frame

// ---- lattice ------------------------------------------------------------
// Technique 46, rule 4: a bracket gusset is never a solid flat triangle --
// either taper the web to the load path or through-cut it as a hex lattice
// inside a solid perimeter frame. The load here is distributed along the deck
// and the bracket is meant to be seen, so this is the lattice version.
//
// The two lattices are NOT the same cell and that is on purpose. The back
// plate's cells are cut along the build axis, so they are plain vertical
// holes and can be regular hexagons. The side panels' cells are cut ACROSS
// the build axis, so each cell's roof is a real overhang: a regular pointy-up
// hexagon puts its top two edges at 60 deg from vertical, past the 55 deg the
// P1S holds. Stretching the cell along the build axis by 1.9 pulls those
// edges back to 42 deg. The two fields share a rib width and a similar
// across-flats pitch so they read as one family; you never see both from a
// single position at the wall anyway.
rib      = 1.68;            // 4 x 0.42
cellR_p  = 4.5;             // back plate, regular (no roof to worry about)
cellR_s  = 3.8;             // side panels
lat_cham = 0.6;             // lead-in on the plate lattice's room-facing face
stretch  = 1.5;             // along the build axis, panels only. Sized to the
                            // real 55 deg limit with margin, not to 45: 1.5
                            // puts the cell roof at 49.1 deg (measured) and
                            // keeps the cell at 1.7:1 instead of the 2.2:1 that
                            // a 1.9 stretch produced, which read as squashed.

// ---- mounting -----------------------------------------------------------
// Keyhole: a Ø9 slot recessed from the WALL side takes the screw head, a Ø4.6
// slot through a 2.8mm front skin takes the shank, and the step between them
// is a 45 deg cone instead of a flat ledge so the transition needs no bridge.
// The bosses stand proud on the FRONT only -- the back face stays dead flat
// against the wall.
boss_w   = 22;  boss_h = 30;  boss_t = 6.0;
boss_cy  = 29;              // boss spans y 14..44 -- inside the 45 plate edge
key_x    = 38;  key_y  = 34;    // y of the round (head) end of the keyhole
key_head = 9.0;             // screw head clearance
key_shaft= 4.6;             // #6/#8 shank clearance
key_drop = 9;               // how far the shelf drops onto the screws
key_deep = 3.2;             // head recess from the wall face -> 2.8mm of skin
                            // left in front for the head to bear on

foot_w   = 24;  foot_t = 5.0;   foot_y = -32;   // anti-lift screw at the bottom

// ---- deck plug slot ------------------------------------------------------
// A charging plug on a phone's bottom port has to pass THROUGH the deck. The
// slot's far end is a 45 deg peak, not a flat roof: in this orientation the
// far end is the top of a 24mm horizontal hole, and a flat one would be a
// 24mm bridge.
slot_w  = 24;
slot_z0 = 8;                // keep the deck's root at the wall intact -- that
slot_z1 = 32;               // is where the bending moment is highest
slot_r  = 3;

// ---- maker's mark --------------------------------------------------------
// Front face of the lip, which is the TOP surface as printed -- the crispest
// engraving this part can carry, and the face you actually look at on a wall.
// Sized to the 10.94mm face rather than 40% of the 120mm run: the face's short
// dimension binds first, and 40% of 120 would need an 11mm cap height that
// does not fit. Measured 2.27mm / 5.39 extrusions on the thinnest stroke.
mark_size = 7.0;
mark_deep = 0.6;

// =========================================================================
// helpers
// =========================================================================

// child 2D is drawn as (x, z); result spans y in [0, thk]
module extrude_xz(thk) { rotate([90,0,0]) translate([0,0,-thk]) linear_extrude(thk) children(); }

// child 2D is drawn as (z, y); result spans x in [-thk, 0].
// rotate([0,90,0]) is the trap here and it renders, gates watertight and
// slices: it sends the profile's x to world MINUS z, so the whole shelf came
// out mirrored into negative depth (bounds z -65..65 instead of 0..65) while
// every other check passed. rotate([0,-90,0]) is the one that puts depth
// where depth belongs.
module extrude_zy(thk) { rotate([0,-90,0]) linear_extrude(thk) children(); }

// ---- lattice placement ---------------------------------------------------
// Cells are PLACED ONLY IF THEY FIT WHOLE. The obvious construction --
// intersect an infinite hex field with the region -- renders, gates and slices
// fine, and looks wrong: a cell clipped by the region boundary leaves a
// tapering needle of material between it and its neighbour. Measured on the
// first build, those needles were 1.26-1.68mm wide, so nothing flagged them --
// they are perfectly printable, they just read as a modelling mistake on the
// face of a product whose whole point is being seen. Testing each cell's six
// real vertices against the outline costs ~60 lines and removes them entirely,
// and the solid frame is then whatever is left over rather than a separate
// inset shape.
function rot2(p, a) = [p.x*cos(a) - p.y*sin(a), p.x*sin(a) + p.y*cos(a)];

function pip(p, pts) =
    (len([for (i = [0 : len(pts)-1])
        let (a = pts[i], b = pts[(i+1) % len(pts)])
        if (((a.y > p.y) != (b.y > p.y)) &&
            (p.x < (b.x-a.x) * (p.y-a.y) / (b.y-a.y) + a.x)) 1]) % 2) == 1;

function seg_d(p, a, b) =
    let (v = b - a, w = p - a, L2 = v*v,
         t = L2 == 0 ? 0 : max(0, min(1, (w*v) / L2)))
    norm(p - (a + t*v));

function edge_d(p, pts) =
    min([for (i = [0 : len(pts)-1]) seg_d(p, pts[i], pts[(i+1) % len(pts)])]);

function far_in(p, pts, d)  =  pip(p, pts) && edge_d(p, pts) >= d;
function far_out(p, pts, d) = !pip(p, pts) && edge_d(p, pts) >= d;

function cell_fits(c, vs, outline, keepouts, d) =
    len([for (v = vs) if (!far_in(c + v, outline, d)) 1]) == 0 &&
    len([for (k = keepouts) for (v = vs) if (!far_out(c + v, k, d)) 1]) == 0;

function rrect_pts(w, h, r, seg = 6) =
    [for (q = [0 : 3], i = [0 : seg])
        let (cx = (q == 0 || q == 3 ? 1 : -1) * (w/2 - r),
             cy = (q < 2 ? 1 : -1) * (h/2 - r),
             a  = (q == 0 ? 0 : q == 1 ? 90 : q == 2 ? 180 : 270) + 90 * i / seg)
        [cx + r*cos(a), cy + r*sin(a)]];

function rect_pts(cx, cy, w, h) =
    [[cx-w/2, cy-h/2], [cx+w/2, cy-h/2], [cx+w/2, cy+h/2], [cx-w/2, cy+h/2]];

module cell_2d(R, k) { offset(r = -rib/2) scale([1, k]) rotate(30) circle(r = R, $fn = 6); }

module lattice(outline, keepouts, R, k, brd, turn = 0, reach = 130) {
    px = sqrt(3) * R;
    py = 1.5 * R * k;
    vs = [for (j = [0:5]) rot2([R*cos(30 + 60*j), k*R*sin(30 + 60*j)], turn)];
    for (j = [-ceil(reach/py) : ceil(reach/py)], i = [-ceil(reach/px) : ceil(reach/px)])
        let (c = rot2([(i + (j % 2 == 0 ? 0 : 0.5)) * px, j * py], turn))
            if (cell_fits(c, vs, outline, keepouts, brd))
                translate(c) rotate(turn) cell_2d(R, k);
}

// The 3D version, for a lattice cut along the build axis. Every cell gets a
// 45 deg lead-in on the room-facing face: a phone narrower than ~55mm misses
// the mounting bosses and leans on the lattice itself, and a raw through-cut
// would present it fifty sharp edges. linear_extrude(scale=) is safe here
// only because each cell is already translated to its own origin inside the
// loop -- scaling the assembled union instead would fan the cells outward.
// The flare faces the room, so in the print it is a 45 deg downward face,
// inside the 55 deg limit. It is a hull between the plain cell and an
// offset() one, NOT linear_extrude(scale=): scale ramps over the whole
// extrude height, so a 0.6mm chamfer asked for that way only delivered
// 0.22mm inside a 2.52mm plate -- measured, not assumed.
module lattice_cut(outline, keepouts, R, k, brd, h, cham, turn = 0, reach = 130) {
    px = sqrt(3) * R;
    py = 1.5 * R * k;
    vs = [for (j = [0:5]) rot2([R*cos(30 + 60*j), k*R*sin(30 + 60*j)], turn)];
    for (j = [-ceil(reach/py) : ceil(reach/py)], i = [-ceil(reach/px) : ceil(reach/px)])
        let (c = rot2([(i + (j % 2 == 0 ? 0 : 0.5)) * px, j * py], turn))
            if (cell_fits(c, vs, outline, keepouts, brd))
                translate(c) rotate(turn) {
                    translate([0, 0, -1]) linear_extrude(h + 2) cell_2d(R, k);
                    hull() {
                        translate([0, 0, h - cham]) linear_extrude(0.01) cell_2d(R, k);
                        translate([0, 0, h + 0.5]) linear_extrude(0.01)
                            offset(r = cham + 0.5) cell_2d(R, k);
                    }
                }
}

// rounded slot between two points, in 2D
module slot2d(x0, y0, x1, y1, d) { hull() { translate([x0,y0]) circle(d=d); translate([x1,y1]) circle(d=d); } }

// =========================================================================
// back plate  (2D in world X,Y -- extruded along the build axis)
// =========================================================================
module plate_2d() { offset(r = corner_r) square([W - 2*corner_r, H - 2*corner_r], center = true); }

module boss_2d(x, y, w, h) { translate([x, y]) offset(r = 4) square([w - 8, h - 8], center = true); }

module bosses_2d() {
    boss_2d(-key_x, boss_cy, boss_w, boss_h);
    boss_2d( key_x, boss_cy, boss_w, boss_h);
}

// What the lattice must stay clear of: the plate's own outline, the band
// around the deck junction (that is where the deck's moment lands), and each
// mounting boss.
function plate_keepouts() = [
    rect_pts(0, -1.5, W + 2, 13),
    rect_pts(-key_x, boss_cy, boss_w, boss_h),
    rect_pts( key_x, boss_cy, boss_w, boss_h),
    rect_pts(0, foot_y, foot_w, foot_w)];

module back_plate() {
    difference() {
        union() {
            linear_extrude(plate_t) plate_2d();
            linear_extrude(boss_t)  bosses_2d();
            linear_extrude(foot_t)  boss_2d(0, foot_y, foot_w, foot_w);
        }
        lattice_cut(rrect_pts(W, H, corner_r), plate_keepouts(),
                    cellR_p, 1, brd_p, plate_t, lat_cham);
    }
}

// =========================================================================
// side panel  (2D in world Z,Y -- one continuous wall: rail on top, bracket
// below, concave free edge)
// =========================================================================
// The free edge is a circular arc sagging INWARD from the chord between the
// bottom of the back plate and the front of the deck. It stays monotonic in
// both axes, so its surface normal keeps a positive Z component the whole way
// -- an up-facing face in the print, never an overhang. A convex bulge would
// not be, which is why the sag is subtracted from the chord and not added.
arc_sag = 7;
fascia  = 2;                // the side wall returns 2mm below the deck at the
                            // front. Landing it EXACTLY on the deck's own
                            // bottom-front edge made two collinear zero-area
                            // faces there -- mesh_gate caught them; the render
                            // and the watertight check did not.
function panel_pts() = concat(
    [[0, rail_h], [Dp, rail_h], [Dp, deck_b - fascia]],
    [for (i = [1 : 24]) arc_pt(1 - i/24)],
    [[0, plate_lo]]);

function arc_pt(t) =
    let (z0 = plate_t, y0 = plate_lo, z1 = Dp, y1 = deck_b - fascia,
         mz = (z0+z1)/2, my = (y0+y1)/2,
         dz = z1-z0, dy = y1-y0, L = sqrt(dz*dz + dy*dy),
         nz = -dy/L, ny = dz/L)                       // unit normal, toward the inside corner
    [ z0 + dz*t + 4*arc_sag*t*(1-t)*nz,
      y0 + dy*t + 4*arc_sag*t*(1-t)*ny ];

module panel_2d() { polygon(panel_pts()); }

module panels() {
    for (s = [-1, 1]) translate([s > 0 ? W/2 : -W/2 + panel_t, 0, 0])
        extrude_zy(panel_t)
            difference() {
                panel_2d();
                lattice(panel_pts(), [], cellR_s, stretch, brd_s, 90);
            }
}

// =========================================================================
// deck + lip
// =========================================================================
module deck_2d() { square([W, Dp], center = false); }   // drawn as (x, z)

module deck() {
    translate([-W/2, deck_b, 0]) extrude_xz(deck_t) deck_2d();
}

// slot drawn as (x, z); peak apex 45 deg so the roof of a 24mm horizontal
// hole never becomes a flat bridge
module plug_slot_2d() {
    a = slot_w / 2;
    // The whole outline is convex, so ONE hull gets it exactly: rounded bottom
    // corners, vertical sides tangent to them at x = +/-a, then the 45 deg peak.
    // Unioning a rounded rect with a separate peak does not work -- whichever
    // shape is wider at the join leaves a flat horizontal ledge there, which is
    // the flat roof the peak exists to remove, plus zero-area slivers.
    hull() {
        translate([-(a - slot_r), slot_z0 + slot_r]) circle(r = slot_r);
        translate([  a - slot_r,  slot_z0 + slot_r]) circle(r = slot_r);
        polygon([[-a, slot_z1], [a, slot_z1], [0, slot_z1 + a]]);
    }
}

module plug_slot() { translate([0, deck_b - 1, 0]) extrude_xz(deck_t + 2) plug_slot_2d(); }

module front_lip() {
    translate([W/2, 0, 0]) rotate([0, -90, 0]) linear_extrude(W)
        polygon([[Dp - lip_run, deck_y], [Dp, deck_y], [Dp, deck_y + rail_h]]);
}

// =========================================================================
// mounting cuts
// =========================================================================
module keyhole(x) {
    step = (key_head - key_shaft) / 2;
    translate([x, 0, 0]) {
        // head recess, open to the bed
        translate([0, 0, -0.5]) linear_extrude(key_deep + 0.5)
            slot2d(0, key_y, 0, key_y - key_drop, key_head);
        // 45 deg loft up to the shank slot instead of a flat annular ledge
        hull() {
            translate([0, 0, key_deep]) linear_extrude(0.01)
                slot2d(0, key_y, 0, key_y - key_drop, key_head);
            translate([0, 0, key_deep + step]) linear_extrude(0.01)
                slot2d(0, key_y, 0, key_y - key_drop, key_shaft);
        }
        translate([0, 0, -1]) linear_extrude(boss_t + 2)
            slot2d(0, key_y, 0, key_y - key_drop, key_shaft);
    }
}

module foot_hole() {
    translate([0, foot_y, -1]) cylinder(h = foot_t + 2, d = key_shaft);
    // countersink opens upward -> an up-facing cone, no overhang
    translate([0, foot_y, foot_t - 2.45])
        cylinder(h = 2.45, d1 = key_shaft, d2 = key_shaft + 4.9);
}

module brand_mark() {
    translate([0, deck_y + rail_h/2 - 1.2, Dp - mark_deep]) linear_extrude(mark_deep + 1)
        text("OBC", size = mark_size, font = "Montserrat:style=Black",
             halign = "center", valign = "center");
}

// =========================================================================
// ORDER MATTERS. Every solid is unioned before any cut is taken, and no
// solid is added after -- the drawer module and the label bin both lost
// features to unioning them after the cavity was cut, and both still
// rendered and still gated watertight.
// =========================================================================
module shelf() {
    difference() {
        union() { back_plate(); deck(); panels(); front_lip(); }
        plug_slot();
        keyhole(-key_x);
        keyhole( key_x);
        foot_hole();
        brand_mark();
    }
}

if      (part == "plate") back_plate();
else if (part == "panel") panels();
else if (part == "deck")  deck();
else                      shelf();
