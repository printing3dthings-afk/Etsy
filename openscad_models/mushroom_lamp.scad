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
//   Cap architecture (2026-08-28, thirteenth correction -- see PART 2
//     below for the full postmortem): the cap is ONE ellipsoid, apex to
//     rim, with no dome/skirt split and no union seam on any visible
//     surface. Twelve earlier versions built it as a spherical dome
//     unioned onto a separately-profiled skirt and then tried to fix the
//     resulting shoulder crease by re-tuning the skirt's curve; the
//     crease was the seam between the two surfaces, not a flaw in either
//     curve, so no amount of profile tuning could ever have removed it.
//     The whole bayonet mechanism moved onto a hidden internal sleeve at
//     a fixed radius, which is what freed the outer surface to be shaped
//     for looks alone. Small proud "warts" scattered on the dome add the
//     classic spotted-toadstool texture.
// Every dot-hole cut uses a cylinder aimed along the TRUE LOCAL SURFACE
// NORMAL of the ellipsoid, not a flat tool on a fixed global axis and
// not the radial-from-centre direction a sphere would give -- on a cap
// this flattened those two differ by tens of degrees. This sidesteps the
// entire "flat tool vs curved surface" bug class that cost so much time
// on the cloud organizer (buried cuts, curvature mismatch): a cut along
// the real normal through a shell of known thickness passes cleanly
// through by construction, wherever on the surface it sits.
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
// The puck stays housed in the STEM, not the cap -- mounting it in the
// cap would need a ~65mm unsupported horizontal bridge inside the dome.
// Stem rebuilt as ONE smooth revolve (2026-08-28), for two independent
// reasons found together. The visual one: it was three stacked cyl()
// primitives (foot cone, neck cone, collar), and a stacked-primitive
// stem reads as stacked primitives -- the same architectural mistake the
// cap had, and the same fix (see Technique 12's path_sweep lesson: a
// curved organic form needs one continuous surface, not visible joints).
// The mechanical one, and it was a real defect nobody had checked: the
// old neck flared r=15 -> 39.5 over just 14mm of height, a 60.3-degree
// outward wall -- well past the P1S's 55-degree unsupported limit, so
// the stem as shipped could not actually print cleanly base-down.
//
// Re-cut again 2026-09-01, and this one came from a REAL PRINTED PART,
// not a calculation. The 53.1-degree rebuild passed the 55-degree limit
// and still printed visibly rough through the whole flare -- Scott's
// photos show the droop. 55 degrees is the STRUCTURAL limit (will the
// wall stand up at all); it is nowhere near the SURFACE-QUALITY limit.
// The number that actually matters is unsupported width per layer:
// 0.2 * tan(angle). At 53 degrees that is 0.265mm of a 0.4mm extrusion
// hanging over air every single layer -- 66% unsupported, which droops
// and leaves exactly the rough banding in the photo. At 38 degrees it is
// 0.156mm, under 40%, which the previous layer carries cleanly. So the
// whole flare now runs at a constant 37.95 degrees (verified on the
// SMOOTHED path, not just the control segments -- smoothing can only
// interpolate between neighbouring slopes here, never exceed the
// steepest one, and the measured worst case matches the design value
// exactly).
//
// A shallower flare needs more height to cover the same radius, which is
// why stem_top_z moved 60 -> 70 (Scott: "you can make the base taller to
// help with the overhang issue"). The cap's own rim rides up with it, so
// the hidden/visible split below is preserved rather than accidentally
// exposing the puck housing.
//
// Shape intent: the wide part is placed so the CAP HIDES IT. The puck is
// 59mm across and forces ~79mm of stem width to house it, which is not a
// mushroom-stem proportion at any angle -- so the flare that gets there
// happens above the cap's rim line, and what stays visible is the
// bulbous foot tapering to a 34mm waist under a 120mm cap (28% of the
// cap's width -- a real mushroom ratio, stated as a number per Technique
// 31 rather than eyeballed) and then the first 16mm of the flare -- which at
// 38 degrees reads as a gentle trumpet rather than the "hard flare, not like
// a mushroom" Scott rejected at 53.
stem_top_z = 72;
collar_r = cavity_r + 7;        // wall around the puck cavity
base_plate_d = 78; base_plate_h = 9;   // 9 not 4: the underside cable groove needs a real roof

// (r, z) control points, base to top; closed back down the axis at 0.4
// rather than 0 -- a revolve profile touching x=0 exactly renders fine
// in preview but fails EVERY boolean op it is later used in (Technique 15).
stem_ctrl = [
    [0.4, 4], [27, 4], [26.5, 9], [23, 14], [19.5, 18.5],
    [17, 23],                                       // waist -- 5.5mm of wall
                                                    // around the 23mm channel
    [20.9, 28], [24.8, 33], [28.7, 38], [32.6, 43], [36.5, 48],  // 37.95 deg
    [38.9, 53], [39.5, 59], [39.5, stem_top_z],
    [0.4, stem_top_z],
];
// $fn=96 / splinesteps=5 chosen against real print resolution, not by
// eye: at r=60 that is a 0.032mm sagitta, six times finer than the 0.2mm
// layer height, so nothing is lost on the printed part -- and it keeps
// the exported mesh a third of the size a denser setting produced.
stem_pts = smooth_path(stem_ctrl, method = "corners", size = 2.2, splinesteps = 5);

module stem_base_plate() {
    cyl(h = base_plate_h, d = base_plate_d, rounding = 1.5, anchor = BOTTOM, $fn = 96);
}

module stem_body() {
    rotate_extrude($fn = 96) polygon(stem_pts);
}


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
    // $fn=360 on the sweep and 32 on the section are both real numbers, not
    // habit (2026-09-01). At $fn=90 a 33-degree sweep is only ~8 facets, and
    // an INSCRIBED polygonal sweep sits up to r*(1-cos(2deg)) = 0.024mm
    // inside the true circle -- so the carved channel came out fractionally
    // narrower than designed and the cap pin's own faceted hull clipped it by
    // 0.11mm radially. Not a print-relevant amount, but it made the assembled
    // interference check report a non-empty result, and a verification test
    // that cries wolf stops being a verification test. These values put the
    // faceting error at 0.0015mm, well under any real tolerance.
    translate([0, 0, lock_z])
        rotate_extrude(angle = lock_angle + angle_margin, $fn = 360)
            translate([collar_r, 0])
                circle(r = slot_r, $fn = 32);
}

module collar_slots() {
    // offset 60deg off the 0/180 axis so no slot lands on the cable
    // route's own line (cable_route runs out along +X below)
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60])
            one_collar_slot();
}

module puck_cavity() {
    // opens at the very top of the collar, puck sits LED-face-up
    translate([0, 0, stem_top_z - cavity_h + 0.1])
        cylinder(r = cavity_r, h = cavity_h + 1, $fn = 48);
}

// ---- cable routing (2026-08-28) ----
// Replaces cable_notch(), which cut a slot out through the COLLAR WALL --
// a real bug once the cap was rebuilt: the cap's sleeve now wraps that
// exact band (bore 40.1 against the collar's 39.5, over world z 27..63),
// so a cable leaving there is blocked by solid cap. And even unblocked it
// would have exited INSIDE the cap with nowhere to go.
//
// The route now runs down the middle of the stem and out a groove in the
// UNDERSIDE of the base, so the wire lies flat under the lamp and the
// base still sits flush on a desk.
//
// Everything on the path is sized for the biggest thing that has to
// TRAVEL it, not for the wire. First pass sized it to the USB-A plug
// (12 x 4.5mm) and 13mm cleared that fine -- but the plug was never the
// binding constraint: the kit's inline switch is moulded onto the same
// cord, Scott measured it at 21mm across, and it has to make the identical
// trip during assembly. 23mm gives it 1mm of clearance. This is the same
// class of miss as Technique 34's -- a service route is only as big as the
// largest object that must pass through it, and the largest object is
// rarely the one you were picturing.
cable_ch_d = 23;        // vertical channel -- 1mm clearance on the 21mm switch
cable_groove_w = 13;    // the bare wire alone lies here -- see cable_drop_w
cable_drop_w = 23;      // local widening directly under the channel
cable_drop_len = 27;
cable_groove_d = 4.2;   // deeper than the ~3.5mm cable, so it sits fully recessed
cable_relief_w = 6;     // shallow relief across the cavity floor, under the puck

module cable_route() {
    // 1. relief across the puck cavity's floor, so the cable can leave the
    //    puck at its back OR its edge and still reach the centre. Stops at
    //    r=26 -- it sits under the 59mm puck either way, and running it
    //    further would break out through the stem's own side wall, which is
    //    only ~33mm in radius down at this height.
    translate([0, 0, stem_top_z - cavity_h - 1.6])
        cube([52, cable_relief_w, 3.2], center = true);

    // 2. vertical channel down the stem's axis into the base
    translate([0, 0, cable_groove_d - 0.5])
        cylinder(d = cable_ch_d, h = stem_top_z - cavity_h - cable_groove_d + 1.5, $fn = 64);
    // flared mouth so the cable turns into the channel over a radius
    // rather than kinking on a sharp lip. Kept to +4mm over 3.5mm (29.7 deg)
    // rather than the +6 it was: at 23mm bore the wider flare put a 40.6-deg
    // overhang on the mouth's own ceiling.
    translate([0, 0, stem_top_z - cavity_h - 3.4])
        cylinder(d1 = cable_ch_d, d2 = cable_ch_d + 4, h = 3.5, $fn = 64);

    // 3a. drop-out zone: the channel's full 23mm carried straight out through
    //     the base's underside, so the switch leaves the lamp DOWNWARD at the
    //     centre instead of having to slide the whole length of the groove.
    //     That is what lets 3b stay wire-width. It is deliberately short, so
    //     the only flat spans the base's underside has to bridge are the few
    //     millimetres between the round bore and this box's own corners --
    //     never a 23mm flat roof.
    translate([-cable_ch_d / 2 - 1, -cable_drop_w / 2, -1])
        cube([cable_drop_len, cable_drop_w, cable_groove_d + 1]);

    // 3b. the wire's own groove, open downward and running out through the
    //     rim. Sized for the ~3.5mm cable, not the switch -- the switch is
    //     already outside the lamp by the time the wire is pressed up into
    //     this (the groove is open along its whole underside, so the cable is
    //     laid in from below, never threaded along it).
    translate([-cable_ch_d / 2 - 1, -cable_groove_w / 2, -1])
        cube([base_plate_d, cable_groove_w, cable_groove_d + 1]);
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
        cable_route();
        collar_slots();
        stem_brand_mark();
    }
}

// ============================================================
// PART 2: CAP -- ONE continuous ellipsoid dome + a hidden inner sleeve
// ============================================================
// Thirteenth correction (2026-08-28), and the first one that addresses
// the actual cause. Twelve prior attempts all read "the cap doesn't look
// like a mushroom" as a CURVE-SHAPE problem and kept re-tuning the flare
// profile -- plain t^2, t^4, a quarter-ellipse, a linear/quadratic blend
// (see Technique 32 in .claude/skills/3d-print-design/SKILL.md for that
// dead end in full). It was never the curve. It was the ARCHITECTURE:
// the cap was a spherical DOME unioned with a separately-profiled
// SKIRT. Two surfaces meeting at one radius with mismatched tangents
// leave a visible shoulder crease that no amount of profile tuning can
// remove, because the crease is not IN either profile -- it is the seam
// BETWEEN them. A real mushroom cap has no such seam anywhere: apex to
// rim is one uninterrupted convex surface.
//
// Rebuilt as exactly that -- ONE ellipsoid, no dome/skirt split, no
// union seam anywhere on the visible surface. An ellipsoid is also the
// right shape on its own merits, not just the simplest: "nearly flat
// near the apex, tangent going vertical at the rim" (what the reference
// photos actually show, and what every previous correction was trying
// to hand-fit with a power curve) is literally an ellipse's own
// behaviour. It is also monotonically non-increasing in radius as
// height rises, so it prints rim-down with zero overhang at any
// steepness -- verified numerically over 420 samples, not assumed.
//
// The mechanical half moves INSIDE, where it cannot distort the
// silhouette: the bayonet pins now sit on a plain cylindrical SLEEVE
// hanging inside the dome at a fixed radius, not on the visible outer
// wall. That permanently retires the pin-clearance-versus-shape tension
// behind corrections six through twelve -- the sleeve bore is a constant
// 40.1mm no matter what the outer curve does, so the pin gets a
// guaranteed 2.0mm of real embedment (collar_r + pin_r - bore, verified
// before modelling) and the outer surface is free to be judged on looks
// alone. The annulus between sleeve and dome is exactly where a real
// mushroom's gills sit, so the gills double as the ribs tying sleeve to
// shell; sleeve, gills and dome rim all start on the print bed, so the
// whole cap still prints in one rim-down orientation with no supports.
cap_A = 60;             // max radius -- the cap's widest point
cap_shoulder_z = 6;     // height of that widest point above the rim edge
cap_B = 45;             // apex height above the shoulder
cap_H = cap_shoulder_z + cap_B;     // total cap height, rim edge to apex
cap_rim_r = 56.5;       // radius at the rim EDGE -- smaller than cap_A on purpose
cap_shell_t = 2.4;

// The cap's local z=0 IS its rim edge (and its print-bed plane). This is
// where that plane sits in world coordinates once assembled -- chosen
// deliberately, not inherited from another feature's height: it hides the
// stem's unavoidable 79mm-wide puck housing while leaving the narrow part
// of the stem visible, and puts the whole piece at 120mm wide x 90mm tall
// = 1.33:1. Moved 27 -> 39 on 2026-09-01 in lockstep with stem_top_z's
// 60 -> 72, chosen by that constraint rather than picked: it keeps
// pin_local_z (= lock_z - this) at exactly 25, so the entire cap --
// dome, sleeve, gills, pins, dots, warts -- is bit-for-bit unchanged by
// the stem's overhang fix.
cap_assembly_offset = 39;

// A plain ellipsoid's tangent is exactly vertical where it meets the rim
// plane, so cutting it there leaves a hard sawn-off vertical edge -- the
// silhouette test (Technique 31) on the first rebuild showed exactly that,
// reading as a lampshade with a cut edge rather than a mushroom margin.
// Real caps curl UNDER at the margin, so the widest point sits slightly
// ABOVE the rim edge and the last few millimetres tuck inward. That also
// stays printable rim-down: the outward growth from cap_rim_r to cap_A
// over cap_shoulder_z is 30.3 degrees from vertical, well inside the P1S's
// 55-degree limit, and everything above the shoulder only narrows.
function cap_r_out(z) = cap_A * sqrt(max(1 - pow((max(z, cap_shoulder_z) - cap_shoulder_z) / cap_B, 2), 0));

// True outward surface normal at local height z and azimuth theta. Above
// the shoulder the surface is the ellipse r^2/A^2 + (z-shoulder)^2/B^2 = 1,
// whose gradient -- and so whose normal -- is (r/A^2, (z-shoulder)/B^2).
// This is NOT the radial-from-centre direction a sphere would give, and on
// a cap this flattened the two differ by tens of degrees. Every dot hole
// and wart is placed along this real normal, so holes cut squarely through
// the wall and read as round from outside instead of skewing to ellipses.
function cap_normal(theta, z) =
    let (r = cap_r_out(z), nr = r / (cap_A * cap_A), nz = (z - cap_shoulder_z) / (cap_B * cap_B))
    unit([nr * cos(theta), nr * sin(theta), nz]);
function cap_surface_pt(theta, z) =
    let (r = cap_r_out(z)) [r * cos(theta), r * sin(theta), z];

// Outer profile, rim edge -> apex. Every point above the shoulder lies
// exactly ON the ellipse the placement functions above use, so dot/wart
// positions are exact rather than approximate; only the two points below
// the shoulder describe the under-curl.
// Sampled by ANGLE around the ellipse, not by height. Sampling uniformly
// in z looks equivalent but is not: near the apex the ellipse's own
// tangent goes horizontal, so equal z-steps there span an ever-larger arc
// and the last sample lands ~20mm of radius short of the tip -- which
// smooth_path then corners off into a visible conical POINT at the apex
// (confirmed in a render before this fix). Uniform angular steps keep the
// sample spacing even all the way round, giving the properly rounded apex
// a real mushroom cap has.
cap_outer_ctrl = concat(
    [[cap_rim_r, 0], [cap_A - 0.55, cap_shoulder_z * 0.5]],
    [for (a = [0 : 5 : 85]) [cap_A * cos(a), cap_shoulder_z + cap_B * sin(a)]],
    [[0.5, cap_H]]
);
cap_outer_pts = smooth_path(cap_outer_ctrl, method = "corners", size = 2.5, splinesteps = 5);

// Inner surface = the same curve scaled about the origin, one factor
// radially and another vertically -- exactly the relationship a pair of
// concentric ellipsoids already has, so it is guaranteed smooth and
// self-intersection-free. A naive 2D offset() of this profile would be
// invalid near the apex where it approaches the rotation axis (Technique
// 1's documented failure), and a naive constant radial subtraction would
// give near-zero wall thickness there for the same reason.
cap_inner_pts = [for (p = cap_outer_pts)
    [max(p.x * (cap_A - cap_shell_t) / cap_A, 0.4), p.y * (cap_H - cap_shell_t) / cap_H]];

module cap_dome_solid() {
    rotate_extrude($fn = 96) polygon(concat(cap_outer_pts, [[0.4, 0]]));
}
module cap_dome_shell() {
    // Outer up, inner back down; polygon()'s own closing edge supplies the
    // flat rim annulus for free, leaving the cap open at the rim as it must
    // be. Neither end sits on the axis (0.4 minimum, per Technique 15).
    rotate_extrude($fn = 96)
        polygon(concat(cap_outer_pts, reverse(cap_inner_pts)));
}

// ---- inner sleeve: the entire bayonet mechanism, hidden ----
// Bore = collar_r + 0.6mm twist clearance. sleeve_h runs just past the
// height where the dome's own inner surface closes down to sleeve_ro
// (26.73mm, solved numerically) so the two merge into one solid there
// rather than meeting at a tangent.
sleeve_ri = collar_r + 0.6;
sleeve_ro = sleeve_ri + 2.4;
sleeve_h = 36;   // past the z where the dome's inner surface closes to sleeve_ro (34.7)
module cap_sleeve() {
    difference() {
        cylinder(r = sleeve_ro, h = sleeve_h, $fn = 96);
        translate([0, 0, -1]) cylinder(r = sleeve_ri, h = sleeve_h + 2, $fn = 96);
    }
}

// ---- gills: real radial fins in the sleeve-to-shell annulus ----
// Structural as well as decorative -- these are what tie the sleeve to
// the dome down at rim level. Each fin starts 1mm inside sleeve_ro (so
// it welds into the sleeve, not merely touches it) and runs outward past
// the shell's inner wall, clipped by the dome SOLID rather than by the
// cavity: clipping to the cavity would leave the fin's outer edge exactly
// coincident with the shell's inner surface, a tangential contact that
// may not weld robustly. Clipping to the solid lets each fin run on into
// the wall itself, where it merges properly and adds nothing outside.
gill_count = 36;
gill_t = 1.1;
gill_h = 13;
module cap_gills() {
    intersection() {
        for (i = [0 : gill_count - 1])
            rotate([0, 0, i * 360 / gill_count])
                translate([sleeve_ro - 1, -gill_t / 2, 0])
                    cube([cap_A, gill_t, gill_h]);
        cap_dome_solid();
    }
}

// ---- spore dots: real through-holes for the light ----
// Placed by [azimuth, local height] and cut along the true ellipsoid
// normal. All of them sit ABOVE the sleeve's own top (z=28): below that
// the interior is the gill annulus, which the solid sleeve shades from
// the LED -- a hole there would be a dark spot, not a lit one. Verified
// numerically that no cutter reaches the sleeve ring or another dot.
cap_dot_r = 6.0;
dot_dirs = [   // [theta (deg around Z), z (local height above the rim plane)]
    [    0, 36.5], [  128, 31.0], [ -104, 33.0],
    [   62, 29.0], [  -58, 30.0], [  176, 28.5],
];
module dot_hole(theta, z) {
    n = cap_normal(theta, z);
    translate(cap_surface_pt(theta, z) - n * 4)
        rot(from = UP, to = n)
            cylinder(r = cap_dot_r, h = 16, $fn = 40);
}

// ---- warts: the spotted-toadstool texture ----
// Same normal math as the dots, unioned instead of cut. Positions were
// checked numerically against every dot AND against each other for real
// 3D separation -- not eyeballed off a render.
wart_r = 2.4;
wart_dirs = [
    [  40, 38.5], [  95, 35.5], [ 155, 36.0], [ -150, 34.0], [ -20, 32.0],
    [  85, 26.5], [ -80, 27.5], [ 152, 24.0], [  -8, 24.5], [  20, 30.0],
    [ -128, 24.0], [ 108, 20.0],
];
module cap_warts() {
    for (d = wart_dirs)
        translate(cap_surface_pt(d[0], d[1])) sphere(r = wart_r, $fn = 20);
}

// ---- bayonet pins, matching collar_slots() on the stem ----
// The pin rides on the SLEEVE's bore, at a fixed radius -- so unlike
// every previous version its embedment does not depend on the visible
// curve at all. Each pin is hulled back into the sleeve wall and DOWN,
// giving its underside a ~40-degrees-from-vertical ramp instead of the
// bare horizontal overhang a lone inward-facing sphere presents when the
// cap prints rim-down. The ramp lives entirely at r >= collar_r, outside
// the stem collar's own surface, so it never fouls the twist.
pin_local_z = lock_z - cap_assembly_offset;
// 2.6, not the 3.2 it was (2026-09-01). At 3.2 the hull's lower tangent
// surface reaches its minimum at world z = 60.90 near r = 39.4 -- which is
// EXACTLY the lock channel's own floor (lock_z - slot_r). Solving the hull's
// tangent-line family by hand rather than eyeballing a render showed the two
// were tangent, not overlapping: real clearance was zero at that one point,
// so every faceted render produced a sub-0.1mm interference sliver and the
// assembled interference check could never come back clean. Dropping to 2.6
// lifts that minimum to 61.19 and buys 0.29mm of genuine clearance, which
// survives faceting. Costs nothing: the ramp's underside is still 58 degrees
// from horizontal, and it is inside the cap where nobody sees it.
pin_ramp_drop = 2.6;
module cap_pins() {
    for (i = [0 : n_pins - 1])
        rotate([0, 0, i * 360 / n_pins + 60 + lock_angle])
            hull() {
                translate([collar_r, 0, pin_local_z]) sphere(r = pin_r, $fn = 24);
                translate([sleeve_ri + 1.0, 0, pin_local_z - pin_ramp_drop])
                    sphere(r = 0.9, $fn = 16);
            }
}

module lamp_cap() {
    difference() {
        union() {
            cap_dome_shell();
            cap_sleeve();
            cap_gills();
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
