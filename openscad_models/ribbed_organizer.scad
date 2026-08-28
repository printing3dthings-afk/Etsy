include <BOSL2/std.scad>

// ============================================================
// Ribbed 3-compartment desk caddy -- Scott's own recorded reference idea
// (Bambu Handy screen recording, 2026-08-27): horizontal corrugated
// ridges wrapping the exterior of a multi-compartment holder.
// One printed part, no moving parts, prints upright with no supports.
//
// Rebuilt 2026-08-28 (concept re-approved by Scott, 3 equal bays kept).
// The first version was a plain rounded box with shallow grooves scratched
// into its four FLAT faces, and it had four real problems:
//   1. The grooves were cut per-face and stopped dead at every rounded
//      corner, so the "wrapping" texture visibly broke four times.
//   2. At 0.8mm deep they read as fine lines, not corrugation -- this
//      skill's own Technique 3 already measured that boundary: 0.3mm is
//      invisible, 0.7-0.9mm proud was the difference between "barely
//      visible" and "genuinely bold", and that was on a much smaller face
//      than this 145mm one.
//   3. The mark used font "Dancing Script:style=Bold", which does not
//      exist on this machine -- confirmed by fc-list, and already
//      documented in Technique 27 as a saved HTML page rather than a real
//      TTF. text() silently substitutes a default font rather than
//      erroring, so this shipped wrong and looked fine in every render.
//   4. No $fn was set anywhere, leaving the corner rounding visibly
//      faceted (the whole model exported as 630 facets).
//
// The fix for (1) and (2) is architectural, not a bigger number: the body
// is now ONE lofted surface (skin() over a stack of per-height profiles,
// this skill's Technique 5) whose whole cross-section breathes in and out
// with height. The ridges are the body, not something cut into it, so they
// wrap the corners continuously by construction -- there is no per-face
// special case left to break.
// ============================================================

$fn = 96;

// ---- overall form ----
// The flute band is an exact whole number of pitches (6 x 12mm) so it both
// starts and ends on a full ridge rather than slicing one off mid-curve.
// Overall footprint-to-height is 148:88 = 1.68, close to the ~1:1.6
// proportion Technique 31 asks to state as a real number rather than
// eyeball. Outer dimensions are 148 x 73mm (the plinth/rim/crest width);
// `size` below is the flute VALLEY, which every wall thickness is measured
// from.
size      = [145, 70, 88];   // valley footprint W x D, and total height
wall      = 2.4;             // wall at a rib VALLEY -- the thinnest point
floor_t   = 3;
n_bays    = 3;
squareness = 0.72;           // superellipse corners: continuous-curvature
                             // (G2) for free, no rounded_prism() needed --
                             // see Technique 30 on why a plain circular-arc
                             // fillet reads harder than a squircle corner

// ---- corrugation ----
// Smooth cosine, NOT abs(cos). Technique 19 found that out the hard way on
// the ghost: abs() puts a non-differentiable cusp at every zero crossing,
// which reads as sharp pleating rather than a soft rolled ridge, and no
// amount of amplitude tuning fixes a formula-shape problem.
//
// The ribs are a defined BAND, not the whole wall. A first pass ran them
// edge to edge over the full height and the front elevation was decisive:
// with every millimetre of surface rippling it read as corrugated cardboard,
// and the top and bottom edges came out scalloped rather than crisp. That is
// Technique 31's fourth point exactly -- "a design that packs every available
// surface with texture reads as busy; one that leaves deliberate plain,
// unbroken surface reads as considered". A plain plinth and a plain rim now
// frame the band, which also gives the base a clean flat contact edge.
//
// The plain bands sit at the CREST width and the ribs dip INWARD from them,
// so the ridges are flutes cut into a smooth body rather than rings stacked
// onto it. The band is a whole number of pitches (6 x 12mm) and the cosine
// starts and ends at a crest, so it meets the plain bands with matching
// position AND matching slope -- no step and no crease at either join.
rib_a     = 1.5;             // how far each flute dips in from the plain wall
rib_p     = 12;              // pitch (mm of height per flute)
rib_steps = 10;              // z samples per pitch -- too few aliases the
                             // cosine into a triangle wave
plinth_h  = 10;              // plain band at the base
rim_h     = 6;               // plain band at the rim

rib_lo = plinth_h;
rib_hi = size.z - rim_h;

function rib_d(z) = (z <= rib_lo || z >= rib_hi)
    ? rib_a
    : rib_a * (0.5 + 0.5 * cos(360 * (z - rib_lo) / rib_p));

// Sample densely inside the flute band and sparsely across the plain bands,
// with an exact sample landing on each join so the loft cannot round the
// corner between them.
rib_zs = concat(
    [0, rib_lo],
    [for (i = [1 : round((rib_hi - rib_lo) / rib_p) * rib_steps - 1])
        rib_lo + i * (rib_hi - rib_lo) / (round((rib_hi - rib_lo) / rib_p) * rib_steps)],
    [rib_hi, size.z]
);

// Each ring is a squircle at the base size PLUS twice the local rib offset.
// Generating each ring from squircle() directly (rather than offset()-ing
// one base path) matters for a non-obvious reason: skin() requires every
// profile to have the SAME point count, and 2D offset() is free to add or
// drop vertices as it resolves corners. squircle() at any size returns
// exactly $fn points, so the loft is guaranteed well-formed.
module caddy_body() {
    skin([for (z = rib_zs)
              squircle([size.x + 2 * rib_d(z), size.y + 2 * rib_d(z)],
                       squareness = squareness)],
         z = rib_zs, slices = 0);
}

// ---- 3 equal bays ----
// The cavity is ONE squircle inset from the VALLEY footprint, divided by two
// thin walls -- not three separate rounded-rect pockets.
//
// That is a correctness fix, not a tidiness one. Three rect pockets sized to
// the valley's bounding box looked right in every check that had been run --
// 1 connected component, "Simple: yes", correct bounding box -- but a rect
// corner reaches much further out than a squircle's does at the same
// nominal width, and the outer bays' corners punched 12.19mm clean through
// the wall. No connectivity or manifold check can see that, because a hole
// through a wall disconnects nothing; it showed up only as four small bright
// spots in a render, which is exactly the kind of thing easy to wave off as
// a facet artifact. Verified by solving the squircle's own implicit equation
// at the bay corner's real angle rather than by eye.
//
// Insetting a squircle from a squircle keeps the wall between 2.40 and
// 3.25mm the whole way round -- never below the target, by construction.
// The inset is taken from the VALLEY profile, never the crest, so the flutes
// cannot thin the wall either (the trap Technique 5 documents).
cavity_sq = [size.x - 2 * wall, size.y - 2 * wall];
bay_w = (cavity_sq.x - (n_bays - 1) * wall) / n_bays;

module bay_voids() {
    // Subtracting (cavity MINUS dividers) leaves the dividers standing as
    // solid walls -- the same inversion Technique 14 used to leave teeth
    // inside a carved mouth.
    difference() {
        translate([0, 0, floor_t])
            linear_extrude(height = size.z)
                squircle(cavity_sq, squareness = squareness);
        for (i = [1 : n_bays - 1])
            translate([-cavity_sq.x / 2 + i * (bay_w + wall) - wall / 2, 0, floor_t - 1])
                linear_extrude(height = size.z + 2)
                    square([wall, size.y + 10], center = true);
    }
}

// ---- maker's mark (standing rule: engraved negative, hidden face) ----
// Caveat, because it is a real registered TTF here -- verified with
// fc-list rather than assumed, after the previous version shipped with a
// font name that silently fell back to the default. Size fitted to this
// model's own bottom face and then re-measured from the exported mesh,
// per the standing rule's "a fixed absolute size is only ever right by
// coincidence once the model's scale changes".
logo_depth = 0.7;
logo_size  = 9;
module brand_mark() {
    translate([0, 0, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

difference() {
    caddy_body();
    bay_voids();
    brand_mark();
}
