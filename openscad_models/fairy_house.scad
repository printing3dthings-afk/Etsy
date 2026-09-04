// Fairy House — a toadstool cottage with a hanging wood sign over the door.
// OnBrandCraftz — built per Scott's request 2026-09-04.
//
// Design notes (see .claude/skills/3d-print-design/SKILL.md for the
// techniques this reuses):
//   - Body is a toadstool: hollow planked "stem" house + a solid mushroom
//     cap roof, built as ONE continuous smooth_path() profile through the
//     flare-to-apex transition (Technique 33 — a seam between two glued
//     domes reads as a crease no curve-tuning fixes; one surface avoids it
//     entirely).
//   - Door and window are hull()-prism cuts through the stem shell
//     (Technique 9), each filled back in with a raised/recessed insert.
//   - The hanging sign is its own welded sub-assembly above the door
//     (bracket + two chain loops + a plank), engraved with real text
//     (Technique 4's confirmed mirror([0,1,0]) pattern).
//   - Maker's mark engraved into the underside per the shop standing rule.
include <BOSL2/std.scad>
$fa = 4; $fs = 0.5;

// ---------------------------------------------------------------------
// Named dimensions — nothing baked in as a bare number in the geometry.
// ---------------------------------------------------------------------
floor_h      = 3;         // solid base disc
stem_base_r  = 26;        // stem radius at the floor
stem_top_r   = 24.5;      // stem radius where the cap begins -- kept close
                          // to stem_base_r on purpose: a flat door/window
                          // insert has to sit flush against this surface,
                          // and a bigger taper than ~1.5mm over the stem's
                          // height makes a single flat y-position wrong at
                          // one end or the other (found rendering v1)
stem_h       = 42;        // floor top -> cap start, absolute z
wall         = 2.2;       // stem shell thickness

cap_flare_r  = 34;        // cap's widest point (the eave overhang)
cap_flare_z  = 58;        // z of the cap's widest point
cap_apex_z   = 90;        // z of the cap's rounded tip

n_planks     = 14;        // vertical plank-board count around the stem
plank_depth  = 0.85;      // absolute mm groove depth (Technique 5 rule) --
                          // deepened from 0.65 and given a crisper profile
                          // (see plank_pts()) for better-defined boards

door_w       = 12;        // door width at its base
door_wall_h  = 13;        // door's straight-sided height before the arch
door_z0      = 6;         // door's own base height above the floor
door_frame_d = 0.6;       // shallow surrounding frame reveal depth
door_recess  = 1.3;       // deeper inner pocket depth where the leaf sits
                          // -- both well under `wall` (2.2), so the door
                          // is a relief in the solid wall, never a hole
                          // through to the hollow interior (outdoor piece
                          // -- no openings that let water reach inside)

win_r        = 6.5;       // window radius
win_z        = 24;        // window center height
win_ang      = 46;        // window's angular position (door sits at 0)
win_recess   = 1.4;       // same "shallow relief, never a through-hole"
                          // rule as the door -- under `wall` (2.2)

sign_w       = 17;        // hanging sign plank width
sign_h       = 10;        // hanging sign plank height
sign_t       = 2.2;       // hanging sign plank thickness
sign_gap     = 5.5;       // vertical gap, top of door arch -> bottom of sign

chim_r       = 4;         // chimney radius
chim_h       = 13;        // chimney height above the cap surface

// ---------------------------------------------------------------------
// The stem+cap silhouette, ONE continuous profile (Technique 33).
// Points are (radius, z). Passed through smooth_path() so the flare's
// widest point and the dome above it are one smooth curve, not a kink.
// ---------------------------------------------------------------------
house_ctrl = [
    [stem_base_r + 1.5, 0],          // tiny root-flare at the very foot
    [stem_base_r,       4],
    [stem_base_r - 0.7, 20],
    [stem_top_r,        stem_h],     // stem meets the cap here -- gentle,
                                      // near-constant taper the whole way
    [cap_flare_r,        cap_flare_z],   // widest point of the cap (the eave)
    [cap_flare_r - 6,    cap_flare_z + 10],
    [16,                 cap_flare_z + 22],
    [6,                  cap_flare_z + 30],
    [0.6,                cap_apex_z],    // nudged off-axis -- Technique 15
];
house_profile = smooth_path(house_ctrl, method = "corners", size = 4, splinesteps = 10);

// Real wall radius at a given z, piecewise-linear off the RAW control
// points (monotonic between them, so this is safe for min/margin math
// even though the rendered surface is the smoothed spline) -- every
// applied feature below (door, window, sign) positions itself against
// this instead of a flat stem_base_r, so nothing floats past the
// house's own real tapered surface.
function stem_r_at(z) = lookup(z, [for (p = house_ctrl) [p.y, p.x]]);

// Split the profile into the STEM band (z <= stem_h) and the CAP band
// (z >= stem_h) -- the stem gets a hollow planked shell, the cap is solid.
stem_profile = [for (p = house_profile) if (p.y <= stem_h + 0.01) p];
cap_profile  = [for (p = house_profile) if (p.y >= stem_h - 0.01) p];

// ---------------------------------------------------------------------
// Plank texture -- vertical boards, angle-only groove (Technique 5).
// Absolute-mm depth, margin-checked against the wall thickness below.
// Refined from the original plain cosine dip: raising it to a power
// sharpens the groove into a narrow reveal with flatter board FACES
// between grooves (a real plank wall reads as flat boards with a crisp
// seam, not a continuous corrugated wave), and a slow secondary wobble
// (Technique 11's organic-irregularity trick) keeps the boards from
// looking machine-uniform.
// ---------------------------------------------------------------------
function plank_pts(r) = [for (a = [0:6:354])
    let(
        base   = 1 - abs(cos(a * n_planks / 2)),
        sharp  = pow(base, 2.4),
        wobble = 0.82 + 0.18 * sin(a * 2.3 + 7),
        rr     = r - plank_depth * sharp * wobble
    )
    [rr * cos(a), rr * sin(a)]
];

module stem_outer() {
    outer_profiles = [for (p = stem_profile) plank_pts(p.x)];
    skin(outer_profiles, z = [for (p = stem_profile) p.y], slices = 0);
}
module stem_inner() {
    // Offset from the UNTEXTURED radius, never the textured one --
    // Technique 5's wall-margin rule.
    inner_profiles = [for (p = stem_profile) circle_pts(max(p.x - wall, 0.3))];
    skin(inner_profiles, z = [for (p = stem_profile) p.y], slices = 0);
}
function circle_pts(r) = [for (a = [0:6:354]) [r * cos(a), r * sin(a)]];

module stem_shell() {
    difference() {
        stem_outer();
        translate([0, 0, 0.5]) stem_inner();   // 0.5mm embed keeps a floor seam
    }
}

module floor_disc() {
    cylinder(h = floor_h + 0.01, r = stem_base_r + 1.5, $fn = 96);
}

// ---------------------------------------------------------------------
// Cap -- one solid rotate_extrude() of the smoothed silhouette (safe:
// the apex is nudged off-axis per Technique 15 before any boolean runs).
// ---------------------------------------------------------------------
module cap_solid() {
    rotate_extrude($fn = 120) polygon(cap_profile);
}

// Warty toadstool dimples: shallow sphere-cuts placed using the cap
// profile's OWN sample points (Technique 3's "reuse the silhouette's own
// samples" pattern), skipping the lowest band (the underside eave, which
// should stay smooth) and the very tip.
module cap_dimples() {
    // Fewer, sparser rings than the first pass: that version stepped every
    // 3rd profile sample with ~6 dimples per ring, ~90 total, and read as
    // dense connected chains rather than scattered warts (and cost most
    // of this file's render time as ~90 separate CGAL sphere subtractions).
    // Coarser step + a per-ring skip roll gives a natural scatter instead.
    n = len(cap_profile);
    lo = floor(n * 0.30);
    hi = floor(n * 0.84);
    for (i = [lo : 7 : hi]) {
        p = cap_profile[i];
        n_at_height = max(3, round(p.x / 9));
        phase = i * 53;                 // decorrelate ring-to-ring, Technique 11
        for (k = [0 : n_at_height - 1]) {
            a = k * 360 / n_at_height + phase;
            translate([p.x * cos(a), p.x * sin(a), p.y])
                sphere(r = 2.4, $fn = 14);
        }
    }
}

chim_ang  = 200;
chim_p    = cap_profile[round(len(cap_profile) * 0.42)];
chim_base = [chim_p.x * cos(chim_ang) * 0.72, chim_p.x * sin(chim_ang) * 0.72, chim_p.y - 4];

module chimney() {
    // Placed on the flare band, opposite the door, tilted slightly outward
    // so it reads from the hero (door-facing) angle.
    translate(chim_base)
        rotate([0, -8, 0]) {
            cylinder(h = chim_h, r1 = chim_r + 0.6, r2 = chim_r, $fn = 28);
            translate([0, 0, chim_h])
                cylinder(h = 1.6, r1 = chim_r + 1.6, r2 = chim_r + 0.8, $fn = 28);
        }
}

// A thin curling wisp of smoke off the chimney cap -- path_sweep of a
// shrinking circular cross-section along a loosening spiral (Technique
// 12's "one continuous swept mesh" pattern, radius/height driven by
// named functions instead of hand-placed segments). Purely decorative,
// welds by starting well inside the chimney cap's own solid material.
module chimney_smoke() {
    n = 40;
    path = [for (i = [0 : n])
        let(t = i / n, ang = t * 620, rise = t * 22, wander = sin(t * 300) * (1.5 + t * 3))
        [wander * cos(ang) * 0.4, wander * sin(ang) * 0.4, rise]
    ];
    // scale= tapers the cross-section continuously along the path
    // (Technique 12's proven pattern) instead of chaining segments.
    translate(chim_base + [0, 0, chim_h + 0.8])
        rotate([0, -8, 0])
            path_sweep(circle(r = 1.7, $fn = 10), path, scale = 0.2, closed = false);
}

// ---------------------------------------------------------------------
// Climbing vine + leaves -- one continuous swept stem winding up the
// BACK of the house (angle 75-300, deliberately leaving the front third
// clear of the door/window/sign per Technique 31's "negative space"
// principle -- a house wrapped in vine on every side reads as busy, one
// side climbing toward the roof reads as a real cottage detail).
// ---------------------------------------------------------------------
vine_ang0 = 75;
vine_ang1 = 300;
vine_z0   = 4;
vine_z1   = 50;
vine_n    = 60;
function vine_pt(t) =
    let(
        ang = vine_ang0 + (vine_ang1 - vine_ang0) * t + 10 * sin(t * 540),
        z   = vine_z0 + (vine_z1 - vine_z0) * t,
        // sits proud of the real tapered wall surface at this height,
        // embedding ~0.5mm in so the tube has real overlap to weld to
        r   = stem_r_at(min(z, stem_h)) + 0.9
    )
    [r * cos(ang), r * sin(ang), z];
vine_path = [for (i = [0 : vine_n]) vine_pt(i / vine_n)];

module climbing_vine() {
    path_sweep(circle(r = 1.4, $fn = 10), vine_path, closed = false);
    // small oval leaves budding off the vine at intervals, alternating
    // sides -- each a scaled sphere (Technique 17's shallow-dimple
    // convexity, used here as a raised blob instead of a cut) positioned
    // to overlap the vine tube by a real margin
    for (i = [4 : 4 : vine_n - 4]) {
        t = i / vine_n;
        p = vine_pt(t);
        side = (i % 8 == 0) ? 1 : -1;
        outward = [p.x, p.y, 0] / norm([p.x, p.y, 0]);
        leaf_center = p + outward * 2.4 + [0, 0, 1.2] * side;
        translate(leaf_center)
            rotate([0, 0, atan2(p.y, p.x)])
                rotate([90, 0, 0])
                    scale([1.7, 0.9, 0.4])
                        sphere(r = 2.3, $fn = 14);
    }
}

// ---------------------------------------------------------------------
// Gill fringe / eave trim -- a ring of small overlapping petal bumps
// right at the ROOFLINE (where the planked stem meets the cap), not at
// the cap's own widest point further up. Moved here specifically to fix
// "the roof looks like it's floating": the first version sat at the
// cap's eave (16mm above the roofline), leaving a bald band of plain cap
// material between the end of the siding and the first roof detail --
// exactly the gap that reads as "the roof isn't attached." Sitting right
// on the seam, this now doubles as a real fascia/trim board: siding
// visibly runs right up to it, the roof visibly rests on it.
// ---------------------------------------------------------------------
module gill_fringe() {
    // First cap_profile sample at/above the roofline, not the profile's
    // own radius maximum (Technique 3's "reuse the silhouette's own
    // samples" pattern, just anchored to the seam instead of the eave).
    trim_i = [for (i = [0 : len(cap_profile) - 1]) if (cap_profile[i].y >= stem_h - 0.01) i][0];
    trim = cap_profile[trim_i];
    n_petals = 30;
    for (k = [0 : n_petals - 1]) {
        a = k * 360 / n_petals;
        translate([trim.x * cos(a), trim.x * sin(a), trim.y - 0.6])
            rotate([0, 0, a])
                scale([1.0, 1.5, 0.5])
                    sphere(r = 2.2, $fn = 12);
    }
}

// ---------------------------------------------------------------------
// Root tendrils -- curling roots at the foot of the house, hull-chains
// of shrinking spheres (this shop's proven fox-tail/hull-chain pattern)
// running from inside the stem's base out across the floor.
// ---------------------------------------------------------------------
module root_tendril(ang, curl) {
    r0 = stem_r_at(2) - 2.5;   // starts embedded in the stem's base
    // z tracks bead_r + a fixed 0.2mm margin, not an independent height
    // curve -- a separately-chosen z formula let the SPHERE (center +/-
    // its own radius) dip to z=-0.4 even though the center itself never
    // went negative (found via a real bed-contact check after the first
    // render: bed_contact_mm2 collapsed to 47 from 2325, and the mesh's
    // true z-min was -0.366). Tying z to the radius directly guarantees
    // every sphere's own lowest point stays above the floor.
    pts = [for (i = [0:5])
        let(t = i / 5, rr = r0 + t * 13, a = ang + curl * t * t, bead_r = 2.6 - t * 2.0)
        [rr * cos(a), rr * sin(a), bead_r + 0.2, bead_r]
    ];
    for (i = [0 : len(pts) - 2])
        hull() {
            translate([pts[i].x, pts[i].y, pts[i].z]) sphere(r = max(0.5, pts[i][3]), $fn = 12);
            translate([pts[i+1].x, pts[i+1].y, pts[i+1].z]) sphere(r = max(0.5, pts[i+1][3]), $fn = 12);
        }
}
module root_tendrils() {
    root_tendril(20, 22);
    root_tendril(150, -18);
    root_tendril(215, 16);
    root_tendril(330, -20);
}

// ---------------------------------------------------------------------
// Baby companion mushroom -- a small toadstool growing against the
// house's own foot, off to the side of the door. Its stem plugs into the
// house wall with real overlap (same "embed, don't touch" rule as every
// other applied feature in this file); its cap is its own small dome.
// ---------------------------------------------------------------------
baby_ang = -58;
baby_r0  = stem_r_at(2) - 3.5;
module baby_mushroom() {
    translate([baby_r0 * cos(baby_ang), baby_r0 * sin(baby_ang), 0]) {
        cylinder(h = 9, r1 = 3.0, r2 = 2.3, $fn = 20);
        translate([0, 0, 8.5])
            scale([1, 1, 0.6])
                sphere(r = 5.2, $fn = 24);
        // two small dimples so it reads as the same toadstool family as
        // the main roof, at a glance
        translate([1.6, 0, 10.3]) sphere(r = 1.0, $fn = 10);
        translate([-1.3, 1.2, 10.1]) sphere(r = 0.9, $fn = 10);
    }
}

// ---------------------------------------------------------------------
// Door -- a shallow two-stage recess (Technique 9's hull()-prism, extended
// to a stadium/arch shape) cut into the SOLID wall thickness only -- never
// through it. This is a hard requirement for an outdoor piece: no cut may
// reach the hollow interior, or rain finds a seam straight into the
// cavity. A wide shallow "frame reveal" plus a narrower, deeper "pocket"
// gives a real recessed-door-in-a-frame look; the leaf sits in the
// pocket, its own oversized edges biting into the frame reveal's
// remaining (uncut-to-full-depth) material for the weld.
// ---------------------------------------------------------------------
door_top_z = door_z0 + door_wall_h + door_w/2;
// Midpoint radius, not min/max of the endpoints -- the taper across the
// door's own height is under 1mm, so a single flat reference plane stays
// inside the wall band at both ends (verified numerically after v1).
door_mid_r = stem_r_at((door_z0 + door_top_z) / 2);

function door_arch_pts(dw = door_w, dwh = door_wall_h, base_drop = 0) = concat(
    [[-dw/2, -base_drop], [dw/2, -base_drop]],
    [for (a = [0:20:180]) [ (dw/2) * cos(a), dwh + (dw/2) * sin(a) ]]
);

module door_cutter() {
    // Frame reveal: wider, shallow (door_frame_d deep).
    translate([0, 0, door_z0])
        hull() for (p = door_arch_pts(door_w + 3, door_wall_h + 1.5, base_drop = 0.8))
            for (yy = [door_mid_r - door_frame_d, door_mid_r + 1.0])
                translate([p.x, yy, p.y]) sphere(r = 0.01, $fn = 6);
    // Inner pocket: the door's own footprint, deeper (door_recess).
    translate([0, 0, door_z0])
        hull() for (p = door_arch_pts(door_w, door_wall_h, base_drop = 0.5))
            for (yy = [door_mid_r - door_recess, door_mid_r + 1.0])
                translate([p.x, yy, p.y]) sphere(r = 0.01, $fn = 6);
}

// A thin raised architrave trim around the frame reveal was tried here
// and cut: in isolation it rendered clean, but unioned into the full
// assembly it produced a real degenerate sliver (a near-zero-volume,
// 2-face fragment right at the frame reveal's own boundary -- a CGAL
// precision artifact from two surfaces sitting suspiciously close
// together, caught by re-checking watertightness on the full model, not
// by eye). The frame reveal + deeper pocket + hinges + knob + plank
// ridges already carry the "better door" detail on their own; this one
// extra flourish wasn't worth reintroducing a real manifold risk for.

module door_leaf() {
    // Front face sits well inside the pocket (recessed, per Scott's
    // request -- never proud), back face reaches past the frame reveal's
    // own cut depth into its still-solid backing for a real weld.
    y_face = door_mid_r - 0.3;
    leaf_t = 1.3;
    leaf_pts = door_arch_pts(door_w, door_wall_h, base_drop = 0.5);
    union() {
        translate([0, y_face, door_z0])
            rotate([90, 0, 0])
                linear_extrude(height = leaf_t)
                    polygon(leaf_pts);
        // round knob, offset toward one side like a real door
        translate([door_w/2 - 3.2, y_face + 0.4, door_z0 + door_wall_h * 0.55])
            rotate([90, 0, 0]) sphere(r = 1.0, $fn = 16);
        // plank lines as RAISED ridges, not cut grooves -- a subtracted
        // groove here produced real disconnected slivers in v1 (caught
        // by a connected-component check on the exported STL, not by
        // eye). A proud ridge is a plain union with the leaf, so it
        // cannot detach the same way.
        for (gx = [-door_w/2 + 2.2 : (door_w - 4.4)/4 : door_w/2 - 2.2])
            translate([gx, y_face + 0.01, door_z0])
                rotate([90, 0, 0])
                    linear_extrude(height = 0.45)
                        square([0.6, door_wall_h + door_w/2 - 1.5], center = false);
        // two strap hinges on the side opposite the knob -- thin tapered
        // straps with small rivet bumps, reaching from the leaf onto the
        // surrounding frame reveal so they read as real applied hardware
        // bridging door and frame, not just leaf decoration.
        // mounted at -door_w/2-0.2 (not further out) so the strap's own
        // outer edge stays inside the frame reveal's cut footprint --
        // reaching past it would touch the plain (uncut) wall surface
        // exactly flush, the same "coincident face" risk flagged
        // throughout this file wherever two pieces are meant to weld.
        for (hz = [door_z0 + 3.5, door_z0 + door_wall_h - 1])
            translate([-door_w/2 - 0.2, y_face + 0.3, hz])
                rotate([90, 0, 0]) {
                    hull() {
                        translate([0, 0, 0]) cylinder(h = 0.7, r = 1.1, $fn = 12);
                        translate([4.6, 0, 0]) cylinder(h = 0.7, r = 0.7, $fn = 12);
                    }
                    translate([-0.3, 0, 0.75]) sphere(r = 0.55, $fn = 10);
                    translate([2.6, 0, 0.75]) sphere(r = 0.5, $fn = 10);
                }
    }
}

// ---------------------------------------------------------------------
// Window -- round cutter, recessed pane + raised cross mullions, and a
// small flower-box ledge underneath.
// ---------------------------------------------------------------------
module window_cutter() {
    // A shallow round POCKET, not a through-hole -- capped at win_recess
    // deep, well under the 2.2mm wall, so the window never opens into
    // the hollow interior (this piece lives outdoors; no seam anywhere
    // may reach the cavity). Oversized radius (win_r+1.5) gives a visible
    // reveal ring around the actual window opening.
    wr = stem_r_at(win_z);
    translate([0, 0, 0])
        rotate([0, 0, win_ang])
            translate([0, wr + 0.5, win_z])
                rotate([90, 0, 0])
                    cylinder(h = win_recess + 0.5, r = win_r + 1.5, $fn = 40);
}

module window_insert() {
    // Real wall radius at the window's own height -- NOT stem_base_r,
    // which would float the whole assembly past the true tapered surface.
    wr = stem_r_at(win_z);
    rotate([0, 0, win_ang]) {
        // ONE solid disc filling the pocket -- the same proven pattern
        // this window used in v1 (a separate frame+pane+mullion at three
        // slightly different Y-depths produced real disconnected slivers
        // there, caught by a connected-component check). Repositioned
        // here to sit RECESSED (front face behind wr) instead of proud,
        // per Scott's "recess into the siding, not stick out" request.
        // Outer radius (win_r+1.0) stays under the cutter's own radius
        // (win_r+1.5), leaving a real 0.5mm lip of untouched original
        // wall as a visible reveal around the recess. Back face embeds
        // 0.3mm past the pocket's own cut floor into the still-solid
        // backing for the weld -- never reaching the hollow interior
        // (wall is 2.2mm; win_recess+0.3 stays well under that).
        pane_y_front = wr - 0.5;
        pane_y_back  = wr - win_recess - 0.3;
        translate([0, pane_y_front, win_z])
            rotate([90, 0, 0])
                cylinder(h = pane_y_front - pane_y_back, r = win_r + 1.0, $fn = 40);
        // cross mullions, proud of the disc's own front face but capped
        // at wr-0.2 (their outer/max-Y bound, since these cubes are
        // center=true: translate_y +/- 0.5) -- 0.2mm recessed from the
        // main wall surface, never sticking out past it.
        translate([0, wr - 0.7, win_z])
            rotate([90, 0, 0]) {
                cube([win_r * 2 - 1, 0.9, 1.0], center = true);
                cube([0.9, win_r * 2 - 1, 1.0], center = true);
            }
        // Little flower-box ledge under the sill -- a REAL 3D box (two
        // distinct Y depths, not a flat single-Y hull, which would be a
        // zero-volume face). Starts inside the wall (box_y0) and ends
        // proud of it (box_y1), so it welds the same way the frame does.
        box_y0 = wr - 3.2;
        box_y1 = wr - 0.6;
        box_z0 = win_z - win_r - 3.0;
        box_z1 = win_z - win_r - 1.6;
        translate([0, (box_y0 + box_y1) / 2, (box_z0 + box_z1) / 2])
            cube([win_r * 2 + 2, box_y1 - box_y0, box_z1 - box_z0], center = true);
        // flowers sit on top of the box, overlapping down into it by a
        // real margin (0.6mm) so they're not a hairline/marginal weld.
        for (fx = [-win_r + 1.5 : (win_r * 2 - 3) / 3 : win_r - 1.5])
            translate([fx, box_y1 - 0.5, box_z1 + 0.5])
                color([0.9, 0.4, 0.55]) sphere(r = 1.1, $fn = 12);
    }
}

// ---------------------------------------------------------------------
// Hanging sign -- bracket arm welded into the stem wall, two small chain
// loops, and the plank itself with "Jessee's House" engraved two-line.
// Sits directly above the door arch (door faces +Y, angle 0).
// ---------------------------------------------------------------------
sign_center_z = door_z0 + door_wall_h + door_w/2 + sign_gap + sign_h/2;
sign_attach_z = sign_center_z + sign_h/2 + 3;   // bracket/chain top height
// Real wall radius at each attachment height -- the sign sits in the
// flare band (z > stem_h), where radius is already growing outward
// again, so stem_base_r would badly misplace it.
wall_r_sign   = stem_r_at(sign_center_z);
wall_r_attach = stem_r_at(sign_attach_z);
sign_y        = wall_r_sign + 3.0;   // plank's own front-face Y (proud of wall)

// A single short arm centered above the door, embedded into the wall and
// projecting out to roughly where the sign hangs.
module sign_bracket() {
    hull() {
        translate([0, wall_r_attach - 3, sign_attach_z]) sphere(r = 1.3, $fn = 16);
        translate([0, sign_y - 0.5, sign_attach_z]) sphere(r = 1.0, $fn = 16);
    }
}

// Two thin support rods, each a hull() between a point embedded in the
// wall and the plank's own top-left/top-right corner -- guarantees real
// contact at both ends (Technique 9/23's "hull of two points" pattern),
// instead of separate rings that can end up floating with no real weld.
module sign_chains() {
    for (sx = [-sign_w/2 + 2.2, sign_w/2 - 2.2])
        hull() {
            translate([sx, wall_r_attach - 2, sign_attach_z]) sphere(r = 1.0, $fn = 14);
            translate([sx, sign_y - 0.3, sign_center_z + sign_h/2 - 0.5]) sphere(r = 1.0, $fn = 14);
        }
}

module sign_plank() {
    translate([0, sign_y, sign_center_z])
        rotate([90, 0, 0])
            linear_extrude(height = sign_t)
                offset(r = 0.8) offset(delta = -0.8)
                    square([sign_w, sign_h], center = true);
}

sign_engrave = 0.9;
module sign_text() {
    // Must actually CROSS the plank's front face (y = sign_y), not stop
    // short of it -- a cutter buried entirely inside the plank engraves
    // nothing and still renders clean (Technique 4/28's exact trap).
    // mirror axis verified with a real 4-candidate "TEST" render viewed
    // from a front camera at (0,+Y,z) looking toward -Y (the direction a
    // customer actually views the sign from): for THIS transform chain
    // (translate -> rotate([90,0,0]) -> extrude -> mirror -> text),
    // mirror([1,0,0]) is the one that reads correctly -- NOT the
    // mirror([0,1,0]) used for Technique 4's bottom-engraved mark, which
    // is a different rotate chain. Confirmed: do not assume that axis
    // carries over to a new placement pattern (Technique 4's own warning).
    // translate's Y IS the cutter's outer (max-Y) bound here, since the
    // extrude then walks INWARD (decreasing Y) by `height` -- the earlier
    // version pre-subtracted sign_engrave from this translate too, which
    // double-counted the depth and left the whole cutter buried short of
    // the front face (Technique 28's exact "buried cut" trap, confirmed
    // by deriving the real world-Y range by hand rather than trusting
    // the render).
    translate([0, sign_y + 0.05, sign_center_z])
        rotate([90, 0, 0])
            linear_extrude(height = sign_engrave + 0.05)
                mirror([1, 0, 0]) {
                    translate([0, 1.8]) text("Jessee's", size = 3.4, font = "Caveat:style=Bold",
                        halign = "center", valign = "center");
                    translate([0, -2.2]) text("House", size = 3.4, font = "Caveat:style=Bold",
                        halign = "center", valign = "center");
                }
}

module sign_assembly() {
    sign_bracket();
    sign_chains();
    difference() {
        sign_plank();
        sign_text();   // already carries its own real-world placement
    }
}

// ---------------------------------------------------------------------
// Maker's mark -- engraved into the underside of the floor.
// ---------------------------------------------------------------------
module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = 1.2)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = 3.0, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

// ---------------------------------------------------------------------
// Assembly.
// ---------------------------------------------------------------------
module house_body() {
    difference() {
        union() {
            floor_disc();
            translate([0, 0, 0]) stem_shell();
            cap_solid();
            chimney();
        }
        cap_dimples();
        door_cutter();
        window_cutter();
        translate([0, 0, -0.01]) brand_mark();
    }
}

module house() {
    union() {
        house_body();
        door_leaf();
        window_insert();
        sign_assembly();
        chimney_smoke();
        climbing_vine();
        gill_fringe();
        root_tendrils();
        baby_mushroom();
    }
}

house();
