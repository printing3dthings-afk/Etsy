include <BOSL2/std.scad>

// ============================================================
// "Mushie" -- kawaii mushroom night light for OnBrandCraftz, built around
// the real Bambu Lab LED Lamp Kit-001 (confirmed specs: D59mm x H18mm
// disc, USB 5V/3W, warm white, 1.5m cable, mounts via 2 screws or
// double-sided tape -- store.bambulab.com/products/led-lamp-kit-001).
// Two separate printed parts (different colors/materials, not fused):
//   STEM -- opaque colored PLA, houses the puck in a top-opening cavity,
//     cable exits through a side notch at the puck's own height.
//   CAP  -- opaque colored PLA dome shell with round THROUGH-HOLES for
//     the glowing "dots" (matches the real reference product exactly --
//     Frank Cheung's Mushroom Lamp, MyMiniFactory object 191671: the
//     dots are open holes letting bare light through, not painted or
//     translucent-filled), plus a radial "gill" rib pattern on the
//     underside. Both design cues taken directly from real reference
//     photos (mushroom_ref1.jpg, mushroom_ref2.jpg), not invented.
//     Cap and stem lock together via a 3-pin bayonet twist-lock (push
//     down, twist to lock), adapted from this shop's own proven
//     openscad_models/bayonet_jar.scad.
//   "Adult mushroom" pass (2026-08-28): the skirt below the dome was
//     originally a plain constant-radius drum. It's now ONE smoothly-
//     interpolated profile (smooth_path()+rotate_extrude(), no hard
//     seams) that stays narrow near the dome (where it sheaths the
//     stem's collar and houses the lock pins) and opens into a genuinely
//     wide flared rim -- a real open-umbrella mushroom-cap silhouette,
//     not a jar lid. Small proud "warts" scattered on the dome add the
//     classic spotted-toadstool texture. See the numbered corrections
//     inline below for the real mechanical/visual dead-ends hit getting
//     here, and Technique 29 in .claude/skills/3d-print-design/SKILL.md.
// Every dot-hole cut uses a cylinder aimed along the LOCAL SURFACE
// NORMAL (radially outward from the dome's own center), not a flat tool
// on a fixed global axis -- this sidesteps the entire "flat tool vs
// curved surface" bug class that cost so much time on the cloud
// organizer (buried cuts, curvature mismatch). A radial cut through a
// spherical SHELL of known thickness always passes cleanly through by
// construction, regardless of where on the sphere it sits.
// ============================================================

$fn = 64;

// ---- the real hardware being designed around ----
puck_d = 59; puck_h = 18;
cavity_clear = 3;               // radial + axial clearance around the real puck
cavity_d = puck_d + cavity_clear * 2;
cavity_r = cavity_d / 2;
cavity_h = puck_h + cavity_clear;

// ============================================================
// PART 1: STEM (opaque base, houses the puck)
// ============================================================
// Proportions (2026-08-28, corrected): a first version only tapered
// 34mm -> 27mm before flaring to the 39.5mm collar the puck forces --
// far too shallow a waist, and the assembled render confirmed it: it
// read as a cosmetic jar, not a mushroom, not a subtle framing issue
// (checked a second, wider camera angle -- same result). A real mushroom
// stem needs a DRAMATIC waist. Keeping the puck housed in the stem
// (rather than moving it into the cap, which would need a ~65mm
// unsupported horizontal bridge inside the dome to mount it -- too much
// risk for a first version) but making the taper much more pronounced.
foot_r = 30; neck_r1 = 15; collar_r = cavity_r + 7;   // wall around the puck cavity
foot_h = 22; neck_h = 14; collar_h = 22;
base_plate_d = 70; base_plate_h = 4;

module stem_base_plate() {
    cyl(h = base_plate_h, d = base_plate_d, rounding = 1.5, anchor = BOTTOM, $fn = 64);
}

// CRITICAL FIX (found via connectivity check, not assumed): a first
// version tapered the collar itself gradually from the narrow neck up to
// collar_r across the SAME height range the puck cavity occupies -- the
// collar's own local radius didn't exceed the cavity's radius until more
// than halfway up, so the cavity completely hollowed out that lower
// portion, leaving the collar's top as a disconnected floating fragment
// (confirmed: stl_components.py reported exactly that piece, at exactly
// that height range). Fix: the taper-up now happens in a SHORT neck
// segment below the collar, so the collar itself starts at FULL width
// (collar_r) immediately -- solid wall guaranteed around the cavity at
// every height the cavity actually occupies, not just near the top.
module stem_body() {
    up(base_plate_h - 2)
        cyl(h = foot_h, r1 = foot_r, r2 = neck_r1, rounding1 = 8, anchor = BOTTOM);
    up(base_plate_h - 2 + foot_h - 0.1)
        cyl(h = neck_h, r1 = neck_r1, r2 = collar_r, anchor = BOTTOM);
    up(base_plate_h - 2 + foot_h - 0.1 + neck_h - 0.1)
        cyl(h = collar_h, r = collar_r, rounding2 = 4, anchor = BOTTOM);
}

stem_top_z = base_plate_h - 2 + foot_h - 0.1 + neck_h - 0.1 + collar_h;

// ---- bayonet twist-lock between stem collar and cap skirt (2026-08-28) ----
// Push down, then twist to lock -- the exact mechanism already proven in
// bayonet_jar.scad, reused rather than re-derived: 3 pins on the cap's
// skirt engage 3 slots cut through the stem collar's own wall (a vertical
// entry channel, then a horizontal lock channel swept via rotate_extrude
// so it follows the collar's real curvature). A correctly-built bayonet
// lock has zero real overlap in its locked pose -- the pin only ever
// occupies the slot's own carved-out space -- verified below via
// intersection(), not assumed, the same discipline this file has needed
// for every other feature.
n_pins = 3;
pin_r = 2.6;
slot_clear = 0.5;
slot_r = pin_r + slot_clear;
travel_v = 8;      // vertical entry length (push distance before twisting)
lock_angle = 25;   // degrees of horizontal travel to reach the locked position
angle_margin = 8;  // extra cut angle past lock_angle so the locked pin's own
                    // angular footprint isn't left overshooting uncut wall --
                    // must clear atan(pin_r/collar_r), the same lesson
                    // bayonet_jar.scad already learned the hard way
lock_z = stem_top_z - travel_v;   // world height of the horizontal lock channel

module one_collar_slot() {
    collar_wall = collar_r - cavity_r;
    translate([collar_r - collar_wall - 1, -slot_r, lock_z])
        cube([collar_wall + 2, 2 * slot_r, travel_v + slot_r + 1]);
    translate([0, 0, lock_z])
        rotate_extrude(angle = lock_angle + angle_margin, $fn = 90)
            translate([collar_r, 0])
                circle(r = slot_r, $fn = 16);
}

module collar_slots() {
    // offset 60deg off the 0/180 axis so no slot lands on the cable
    // notch's own line (cable_notch spans the full X axis below)
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60])
            one_collar_slot();
}

module puck_cavity() {
    // opens at the very top of the collar, puck sits LED-face-up
    translate([0, 0, stem_top_z - cavity_h + 0.1])
        cylinder(r = cavity_r, h = cavity_h + 1, $fn = 48);
}

module cable_notch() {
    // rectangular slot through the collar wall, generously long radially
    // so it reaches open air outside regardless of the collar's exact
    // taper radius there. Positioned near the CAVITY FLOOR (not its
    // vertical center) specifically to stay clear of lock_z above --
    // the bayonet lock channel sits higher up the collar, and the two
    // cuts must not overlap.
    notch_z = stem_top_z - cavity_h + 5;
    translate([0, 0, notch_z])
        cube([70, 10, 9], center = true);
}

// ---- brand mark on the base plate (same fitted pattern as Cloudy) ----
logo_depth = 0.7; logo_size = 5.2;
module stem_brand_mark() {
    translate([0, -base_plate_d / 2 + 11, -0.5])
        linear_extrude(height = logo_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = logo_size, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

module lamp_stem() {
    difference() {
        union() {
            stem_base_plate();
            stem_body();
        }
        puck_cavity();
        cable_notch();
        collar_slots();
        stem_brand_mark();
    }
}

// ============================================================
// PART 2: CAP (dome shell with dot through-holes + underside gills)
// ============================================================
// Corrected twice (2026-08-28): a pure sphere cut near its own rim gave
// a lip too shallow to cover the stem's collar, so the assembled render
// looked like a jar; extending the sphere's own cut plane further down
// to compensate doesn't work either -- past the equator a sphere's
// radius necessarily SHRINKS (real geometry, not tunable), so a deeper
// spherical cut makes the rim NARROWER, not wider, eventually too narrow
// to even fit over the collar. Real mushroom caps solve this the same
// way: the rounded dome ends at (or just past) its own equator, then a
// short near-vertical SKIRT band continues down to the true rim -- not
// a continuation of the sphere. Built the same way here.
// Third correction on the cap: cutting the dome at the full equator plus
// a 26mm skirt gave a tall, round "ball on a stick" silhouette once
// actually assembled and rendered correctly (an earlier "use" instead of
// "include" bug had silently kept the cap glued to the very top the
// whole time, hiding this until the include/variable-scope bug itself
// was found and fixed). A real mushroom cap is much SHALLOWER than a
// hemisphere -- cutting higher up the sphere (keeping less than half of
// it) gives a flatter, wider-looking cap that actually matches the
// reference photos instead of reading as a ball.
// Fourth correction: dome_cut_z=16 on a 46mm sphere still gave a 30mm-tall
// dome -- comparable to the stem's own height, so the assembled shape
// read as a "ball on a stick" rather than a flat mushroom cap on a tall
// stem, confirmed by actually rendering the corrected assembly (the
// previous three fixes were all real bugs -- wrong cut math, wrong
// "use" vs "include" variable scoping, wrong assembly offset -- but even
// with all of them fixed, the proportion itself still wasn't right).
// Bigger sphere + a much higher cut plane gives a genuinely flat, wide
// cap instead.
// Fifth correction, found by an actual interference check (intersection()
// of the two assembled parts, not just eyeballing a render): the skirt
// tapered from skirt_r_bot(44, sized for the collar's clearance) at its
// own bottom UP TO the dome's natural edge radius at dome_cut_z (only
// ~35mm) at its own top -- but the stem's collar is a CONSTANT 39.5mm
// radius for its whole height, so partway up the skirt's shrinking taper
// dipped below the collar and collided with it (confirmed: a real solid
// overlap region, ~16mm tall, found via intersection()). Fix: size the
// sphere/cut-height pair so the dome's OWN edge radius at dome_cut_z
// already equals skirt_r_bot -- then the skirt can run essentially
// straight (no taper below the safe clearance) for its entire height.
cap_sphere_r = 72.03;
dome_cut_z = 57.03;      // dome height = cap_sphere_r - dome_cut_z = 15mm, still flat
// Sixth-ninth corrections (2026-08-28, "adult mushroom" pass), condensed:
// the skirt was a near-constant-radius cylinder (44mm the whole way down)
// -- structurally safe, but reads as a drum/jar lid, not a MATURE
// mushroom cap's broad flared "umbrella". Two hard-learned constraints,
// found via intersection() checks and real renders, not guessed:
//   (a) The bayonet lock pin's height is ALWAYS exactly (collar_h -
//       travel_v) = 14mm above wherever the cap's assembly-reference
//       point sits, by construction of cap_assembly_offset -- so a big
//       flare placed too close to that reference point puts the pins in
//       open air instead of a solid wall (caught by intersection(),
//       Sixth correction). The reference point needs ~44mm-radius
//       material for real coverage around it -- roughly collar_h (22mm)
//       of it, matching the original, already-proven design.
//   (b) A wide flare needs real vertical room to open without dropping
//       so low it visually swallows the stem's own foot/neck taper from
//       every outside angle (caught only by an actual render, Seventh
//       correction -- both intersection() checks pass regardless of how
//       bad this looks, since it's a proportion problem, not a collision).
//   Two flat/cyl()-stacked bands satisfying both constraints (Eighth
//   correction) still LOOKED like stacked hat brims -- a hard tangent
//   discontinuity where a straight vertical wall meets a straight
//   tapered wall at the same radius, and BOSL2's cyl(rounding=) on a
//   two-piece union pinches inward into a visible gap rather than
//   blending them (confirmed by rendering it, Ninth correction: a
//   visible slit opened up right at the seam).
// The actual fix: build the ENTIRE skirt as ONE smoothly-interpolated
// profile via smooth_path() + rotate_extrude() -- this shop's own proven
// hollow-vessel technique (see the 3d-print-design skill's Technique 1),
// just for an annulus open at BOTH ends (dome side and true rim) instead
// of a vessel with a floor. A single continuous curve can satisfy both
// constraints (a) and (b) at once -- near-flat ~44mm radius for real
// height around the lock reference point, curving out to a modest flare
// only in the lower portion, close to the rim -- with no hard seam
// anywhere by construction.
cap_shell_t = 2.4;
cap_dot_r = 6.5;
skirt_r_top = sqrt(cap_sphere_r ^ 2 - dome_cut_z ^ 2);   // = 44.0, matches the dome's own edge exactly
// Eleventh correction (2026-08-28, real reference photos this time):
// Scott's own words: "yours is a hard flare and doesn't look natural on
// its curvature... see how it is filled in and sloped." Comparing
// against real cartoon/kawaii mushroom references, every one of them
// has ONE continuously bulging underside curve, slow near the top and
// visibly ACCELERATING toward the rim -- exactly a sphere/ellipse
// section's own shape (near a pole the surface is nearly flat; near the
// equator the tangent goes vertical), not a uniform-slope cone.
// A first attempt at this fix kept the OLD assembly-offset strategy
// (align the skirt's own "safe for the collar" reference point S to the
// stem's collar base) and just swapped in a quadratic radius curve --
// but that strategy has flare_len and world-rim-height WELDED together
// by construction (world_rim = 37.8 - flare_len, always, independent of
// curve shape), so a longer/gentler flare unavoidably drops the rim
// lower, right back toward the Seventh correction's "swallows the
// stem" failure. Realized this offset choice was never a real mechanical
// requirement in the first place -- the ONLY hard constraint is that the
// pin lines up with the lock slot at world height lock_z; nothing
// requires the skirt's own internal reference point to land at the
// collar base specifically. Switched the anchor to what the VERY FIRST
// version of this file did: align the DOME EDGE itself to the stem's
// collar TOP (world stem_top_z). This makes cap_assembly_offset a FIXED
// constant (2.77, independent of the skirt's shape entirely) and the
// pin's local height a fixed 8mm below the dome edge -- so flare_len and
// world-rim-height are now fully DECOUPLED: a much longer, gentler flare
// (20mm vs the previous 12mm) no longer costs any extra rim drop at all.
// Verified numerically before touching OpenSCAD (not by eye): pin lands
// on exactly 44.0mm local radius (inner 41.6mm, 2.1mm clearance over
// collar_r=39.5 -- identical to the original always-proven design,
// since the anchor point is now the same one that design used), profile
// radius is monotonic non-increasing as height increases (still safe to
// print rim-down regardless of steepness), and world_rim lands at 25.8mm
// -- matching the Seventh/Eighth correction's own already-confirmed
// "doesn't swallow the stem" proportion.
// Twelfth correction (2026-08-28): Scott marked up the render directly --
// a real ~14mm dead-FLAT vertical band was still sitting right under the
// dome (the Eleventh correction's "near44_len" zone, both its endpoints
// pinned to the exact same radius on purpose) before the flare began.
// Real mushroom caps have no such feature anywhere -- confirmed against
// the reference photos Scott pointed at directly: the whole cap, dome
// to rim, is ONE uninterrupted curve. There is no separate "collar band"
// visible on a real mushroom because there's no reason there should be
// one -- that band existed here only as a leftover of needing ~44mm
// radius for the pin, modeled as a literal flat plateau instead of just
// checking whether the constraint holds.
// First attempt at "one continuous curve, no flat zone" used a plain t^2
// power -- broke the bayonet lock (stl_components.py found 3 floating
// pins, not the expected 2 solid parts). Root-caused by extracting real
// vertices from the exported STL, not by re-guessing the math: the pin
// is a SPHERE (center at radius collar_r=39.5, radius pin_r=2.6), so the
// real embedding test isn't "is the shell's radius close to 44" -- it's
// "does the pin's widest cross-section (its own equator, at the pin's
// exact height) reach past the shell's INNER radius there." That
// requires shell outer radius at the pin's height to stay under
// collar_r + cap_shell_t + pin_r = 39.5 + 2.4 + 2.6 = 44.5mm -- a
// tighter, and different-shaped, bound than "clearance over collar_r"
// (an earlier, backwards version of this same check that had been
// silently wrong all along -- it computed inner_radius - collar_r and
// treated a positive number as safe margin, when the real requirement is
// inner_radius < collar_r + pin_r, the opposite direction). A plain t^2
// curve overshoots 44.5mm at the pin's fixed height (44.89mm, verified
// against the real exported mesh) -- BUT a full-sphere overlap isn't
// actually required either: since the pin is one solid sphere, any real
// overlap anywhere in its volume (even just through its own equator,
// not its poles) is enough to fuse it into the shell as one connected
// solid -- confirmed against the ORIGINAL always-working flat-zone
// design, which itself only ever had positive margin at the pin's own
// center height (+0.5mm there), not across its whole vertical span.
// So the real, sufficient test is just: shell radius at the pin's exact
// center height must clear 44.5mm, with enough margin to survive
// $fn=90 mesh discretization. A plain t^2 curve grows too fast near the
// dome edge to clear it (t^2 term dominates immediately); a higher power
// (t^4) stays far flatter for longer near t=0 -- which is also the
// CORRECT visual direction per the reference photos (mushroom caps grow
// slowly near the top and visibly accelerate toward the rim, so a curve
// that's flatter near the dome and steeper near the rim is more natural,
// not less) -- and is still perfectly C-infinity smooth everywhere, so
// there is no corner/discontinuity anywhere on the curve, unlike the
// flat-band-plus-corner shape this correction is replacing.
// First real fix attempt used a t^4 power curve on the OUTER profile
// (staying flatter than t^2 for longer, since that's what clearing
// 44.5mm at the pin's fixed t=0.235 required). It rendered mechanically
// sound (verified: pins fuse into the shell, stl_components.py reports
// the expected 2 parts) -- but a real render of the assembled piece
// showed the SAME visual defect this correction exists to fix: a power
// curve that's forced flat enough near t=0 to satisfy a mechanical bound
// at t=0.235 is *necessarily* still barely rising by t=0.5 (r=45.0mm --
// only an eighth of the total 16mm rise halfway up the curve), which
// reads as the same near-vertical "drum" silhouette Scott rejected, just
// smoothed at the derivative level instead of having an actual corner.
// Smoothness alone doesn't fix a visual complaint about *shape*.
// Second attempt swapped in a quarter-ellipse (flat tangent at the dome
// edge, matching the dome's own sphere family) -- mathematically the
// "right" shape per the Eleventh correction's reference-photo research,
// but a real zoomed render (view15_zoom.png) showed it STILL reads as a
// flat drum for a clearly visible stretch right under the dome.
// Third attempt: a plain t^2 (the very first thing tried, before the
// pin-support-post fix existed to decouple it from mechanical margin) --
// re-rendered (view16_zoom.png) and STILL visually indistinguishable
// from the ellipse version. Root cause, found by actually differentiating
// both formulas rather than trusting "t^2 looks less flat than t^4 in a
// spreadsheet": EVERY power t^p for p>1 has dr/dt=0 exactly at t=0, and
// so does the quarter-ellipse (derived that way on purpose) -- all three
// curves tried so far share the exact same defect, a perfectly flat
// starting TANGENT at the dome edge, just with different how-fast-it-
// stops-being-flat rates. That's why they all rendered the same: the
// zero-slope start, not the exponent, is what reads as "drum."
// The actual fix: give the curve a real, nonzero initial slope at the
// dome edge instead of a flat one -- blend a genuine linear term into
// the quadratic so the surface visibly leans outward immediately, still
// curving progressively steeper toward the rim (keeping the
// "accelerating toward the rim" character the reference photos showed)
// rather than opening at one constant cone angle the whole way (the
// original, separately-rejected "uniform-slope cone" look).
// Mechanical clearance no longer depends on this curve at all -- the pin
// support POST in cap_pins() below handles that independently -- so this
// choice is free to be judged on appearance alone.
skirt_len = 34;      // dome edge to true rim, ALL of it one continuous curve now
skirt_r_rim = 60;    // the TRUE open rim
cap_rim_z = dome_cut_z - skirt_len;   // the TRUE open rim plane

// Profile control points, LOCAL height measured up from the true rim
// (z=0) -- fed through smooth_path() so every segment blends with no
// hard corner, then rotate_extrude()'d as an annular (both-ends-open)
// shell, matching this shop's own proven vessel-hollowing pattern
// (outer profile, inner = outer minus wall, polygon()'s own implicit
// last-to-first closing edge providing the rim and dome-side
// wall-thickness caps for free -- no floor logic needed, since neither
// end is closed here).
// t=1 (rim) down to t=0 (dome edge) -- ordered so z comes out ASCENDING
// (rim=0 first, dome edge=skirt_len last), matching the polygon's
// required rim-to-dome winding. Getting this order backwards silently
// produces a self-intersecting garbled profile with no error (confirmed
// by reasoning through it numerically before ever rendering, not
// discovered by trial and error).
// blend fraction: real, nonzero initial slope (the actual fix -- see
// correction notes above) plus enough quadratic weight that the curve
// visibly accelerates toward the rim rather than reading as a straight
// cone frustum -- confirmed by rendering both: a 0.6 blend (mostly
// linear) looked like a plain cone (view17_level_zoom2.png); dropping to
// 0.35 keeps the same real lean right off the dome edge while giving
// the lower half of the flare noticeably more outward bulge, closer to
// the reference photos' "accelerating toward the rim" curvature.
skirt_lean = 0.35;
skirt_outer_ctrl = [for (t = [1.0, 0.85, 0.7, 0.55, 0.4, 0.25, 0.1, 0])
    [skirt_r_top + (skirt_r_rim - skirt_r_top) * (skirt_lean * t + (1 - skirt_lean) * t * t),
     skirt_len - t * skirt_len]
];
skirt_outer_pts = smooth_path(skirt_outer_ctrl, method = "corners", size = 2, splinesteps = 8);

// Real spherical-shell cuts: aim each hole's cylinder from OUTSIDE the
// shell to INSIDE it, along the exact radial direction at that point --
// guarantees a clean through-hole on any sphere regardless of position,
// no curvature/flat-tool mismatch possible.
// phi must stay under acos(dome_cut_z/cap_sphere_r) = acos(46/58) = 37.5deg
// -- the dome only exists above that; anything beyond it is now the
// skirt (a different, non-spherical shape the sphere-based radial-cut
// math below doesn't apply to). Kept a safe margin under that limit.
dot_dirs = [   // [theta (deg, around Z), phi (deg, down from top pole)]
    [ 0,  12],
    [ 130, 20],
    [ -110, 22],
    [ 55, 30],
    [ -60, 28],
];
function dot_vec(theta, phi) = [
    sin(phi) * cos(theta),
    sin(phi) * sin(theta),
    cos(phi),
];

module dot_hole(theta, phi) {
    dir = dot_vec(theta, phi);
    // cylinder default points +Z; rot(from=,to=) reorients it to point
    // radially outward along dir, then push it out from the sphere
    // center so it spans just outside the shell to well inside it.
    rot(from = UP, to = dir)
        translate([0, 0, cap_sphere_r - cap_shell_t - 3])
            cylinder(r = cap_dot_r, h = cap_shell_t + 8, $fn = 40);
}

module cap_dome_only() {
    // keep the sphere shell from z=dome_cut_z upward -- a cube 400 tall
    // with its BOTTOM face at exactly dome_cut_z (not centered there --
    // a cube centered at the cut plane barely cuts anything off a 46mm
    // sphere, which is exactly the bug an earlier version had: it
    // rendered as a near-complete sphere with almost no dome cut at all,
    // caught by actually looking at the render).
    intersection() {
        difference() {
            sphere(r = cap_sphere_r);
            sphere(r = cap_sphere_r - cap_shell_t);
        }
        translate([0, 0, dome_cut_z + 200]) cube([200, 200, 400], center = true);
    }
}

module cap_skirt_only() {
    // One continuous annular shell (both ends open -- dome side and true
    // rim -- neither end closes to a point, so no floor/apex logic
    // needed): outer profile up from the rim, inner = outer minus wall,
    // reversed back down -- polygon()'s own implicit last-point-to-
    // first-point closing edge supplies both the rim's and the dome
    // side's wall-thickness cap for free, exactly like this shop's
    // proven open-vessel technique.
    inner_pts = [for (p = skirt_outer_pts) [max(p.x - cap_shell_t, 1), p.y]];
    inner_rev = [for (i = [len(inner_pts) - 1 : -1 : 0]) inner_pts[i]];
    profile = concat(skirt_outer_pts, inner_rev);
    translate([0, 0, cap_rim_z])
        rotate_extrude($fn = 90) polygon(profile);
}

// ---- decorative surface warts (2026-08-28, "adult mushroom" pass) ----
// Small proud bumps scattered across the dome -- the classic spotted-
// toadstool look (Amanita muscaria and kin), and genuine extra surface
// detail distinct from the dot-hole light vents. Reuses dot_vec()'s
// exact radial-surface-point math (same proven technique as the holes),
// just UNIONS a small sphere centered ON the outer surface instead of
// cutting through it. Positions verified numerically (not eyeballed)
// against every dot_dirs hole AND against each other, so no wart
// overlaps a light-hole or another wart -- see the angular-distance
// check run before finalizing these coordinates. phi stays under the
// same ~37.5deg dome-region limit dot_dirs already respects.
wart_r = 2.2;
wart_dirs = [
    [ 48,  9], [ 95, 15], [165, 10], [-155, 18], [-25, 24],
    [ 85, 28], [-95, 14], [160, 26], [ -5, 34], [ 10, 25],
];
module wart(theta, phi) {
    dir = dot_vec(theta, phi);
    translate(dir * cap_sphere_r) sphere(r = wart_r, $fn = 20);
}
module cap_warts() {
    for (d = wart_dirs) wart(d[0], d[1]);
}

module cap_shell_raw() {
    union() {
        cap_dome_only();
        cap_skirt_only();
    }
}

// Underside gills: thin radial ribs hanging from the shell's own inner
// surface near the open rim, matching the fan/ridge pattern visible in
// the real reference photos. Purely decorative -- built from small
// wedges so they stay thin and printable (rim-side layers first when the
// cap prints opening-down, dome-up -- the standard safe bowl orientation,
// no overhangs).
// Gill count/length bumped up along with the flared rim (2026-08-28) --
// the underside is a much bigger disc now (rim radius 44 -> 64), so the
// original 28x13mm gills would look sparse and short under it; scaled
// both up to stay visually proportional to the new rim.
gill_count = 34;
gill_len = 34;   // sized for the Eleventh-correction rim (60mm, rim_r_inner=57.6) -- comfortably under it
gill_t = 1.0;
module gill(theta) {
    // a thin radial fin sitting just inside the rim, hanging down from
    // the skirt's own inner surface toward the true open edge (z=cap_rim_z,
    // the skirt's own bottom -- a constant, known radius, not the sphere
    // formula, since the rim now sits in the flare band below the dome,
    // not on the sphere itself)
    rim_r_inner = skirt_r_rim - cap_shell_t;
    rotate([0, 0, theta])
        translate([rim_r_inner - gill_len, -gill_t / 2, cap_rim_z])
            cube([gill_len, gill_t, 7]);
}

module cap_gills() {
    for (i = [0 : gill_count - 1])
        gill(i * 360 / gill_count);
}

// ---- bayonet lock pins, matching collar_slots() above ----
// The cap is defined in its OWN local coordinates, then translated by
// cap_assembly_offset when actually assembled onto the stem. Assembly
// aligns the DOME EDGE (local z=dome_cut_z) to the stem's collar TOP
// (world stem_top_z) -- see the Eleventh correction above for why this
// anchor (not the collar base, not the rim) is the right one: it's a
// FIXED constant independent of the skirt's own shape, which is exactly
// what decouples flare length from how far the rim drops. A pin at
// LOCAL z must sit at (lock_z - cap_assembly_offset) so that once
// translated, it lands at the real WORLD height of the lock channel.
cap_assembly_offset = stem_top_z - dome_cut_z;
pin_local_z = lock_z - cap_assembly_offset;
// Each pin gets its own short support POST fusing it to the skirt's
// inner wall -- added once the aesthetic curve (the quarter-ellipse
// above) was freed to do whatever a real mushroom cap's silhouette
// needs, independent of the pin's own mechanical clearance. Without
// this, the pin sphere's own overlap with the wall shrinks to a hair
// (confirmed: as little as 0.05mm with the ellipse curve at this pin's
// exact height, since skirt_r_top=44.0 is a hard geometric floor the
// dome forces regardless of curve shape) -- workable in theory but too
// thin to trust against $fn mesh discretization or print tolerance.
// The post is a plain radial cylinder from inside the pin sphere
// (post_r0=collar_r-1, well inside the sphere's own [36.9,42.1] extent
// so it fuses with zero gap) out to post_r0+post_len=43.3 -- comfortably
// past the inner wall at this height (~42mm) but a real margin short of
// skirt_r_top=44.0, the curve's own hard minimum everywhere -- so the
// post can never poke through the visible outer surface regardless of
// which exact point on the curve it lands under.
pin_post_r = 1.8;
pin_post_len = 4.8;
module cap_pins() {
    // positioned at the LOCKED angle (slot's own start angle + lock_angle)
    // -- this model shows the mechanism already twisted shut, same
    // convention as bayonet_jar.scad.
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60 + lock_angle]) {
            translate([collar_r, 0, pin_local_z])
                sphere(r = pin_r, $fn = 20);
            translate([collar_r - 1, 0, pin_local_z])
                rotate([0, 90, 0])
                    cylinder(r = pin_post_r, h = pin_post_len, $fn = 20);
        }
}

module lamp_cap() {
    difference() {
        union() {
            cap_shell_raw();
            intersection() {
                cap_gills();
                cap_shell_raw();   // keep gills confined to the shell's own interior, never poking outside it
            }
            cap_pins();
            cap_warts();
        }
        for (d = dot_dirs) dot_hole(d[0], d[1]);
    }
}

// ============================================================
// Layout -- two separate parts, side by side (a genuine 2-piece kit,
// not meant to fuse -- 2 disconnected components in the combined STL is
// the CORRECT outcome here, not a bug, unlike every single-part build
// earlier in this project).
// ============================================================
translate([-70, 0, 0]) lamp_stem();
translate([70, 0, 0]) lamp_cap();
