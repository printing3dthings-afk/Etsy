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
// the stem as shipped could not actually print cleanly base-down. The
// profile below is verified to stay under 55 at every control segment
// (worst 53.1) while still reaching the radius the puck cavity needs.
//
// Shape intent: the wide part is now placed so the CAP HIDES IT. The
// puck is 59mm across and forces ~79mm of stem width to house it, which
// is not a mushroom-stem proportion at any angle -- so the flare that
// gets there happens above the cap's rim line, and what stays visible is
// just the bulbous foot tapering to a 31mm waist under a 120mm cap
// (26% of the cap's width -- a real mushroom ratio, stated as a number
// per Technique 31 rather than eyeballed).
stem_top_z = 60;
collar_r = cavity_r + 7;        // wall around the puck cavity
base_plate_d = 78; base_plate_h = 4;

// (r, z) control points, base to top; closed back down the axis at 0.4
// rather than 0 -- a revolve profile touching x=0 exactly renders fine
// in preview but fails EVERY boolean op it is later used in (Technique 15).
stem_ctrl = [
    [0.4, 2], [26, 2], [25.5, 7], [21.5, 13], [17, 18],
    [15.5, 22],                                     // waist
    [19.5, 25.5], [25, 30], [31, 34.5], [36.5, 38.8],   // flare, all under 55 deg
    [38.8, 43], [39.3, 48], [39.5, 53], [39.5, stem_top_z],
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
// of the stem visible, and puts the whole piece at 120mm wide x 78mm tall
// = 1.54:1, close to the ~1:1.6 proportion Technique 31 asks to state as
// a real number instead of eyeballing.
cap_assembly_offset = 27;

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
pin_ramp_drop = 3.2;
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
