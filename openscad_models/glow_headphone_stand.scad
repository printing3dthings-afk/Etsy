include <BOSL2/std.scad>

// ============================================================
// "Glow Stand" -- headphone stand / ambient desk lamp hybrid for
// OnBrandCraftz, built 2026-09-01 from Scott's own reference photos of a
// real edge-lit acrylic headphone stand ("FOXWOOD" branded, not ours --
// reinterpreted with this shop's own construction, not copied). Pitched
// and approved before modelling per the standing rule in
// .claude/skills/3d-print-design/SKILL.md ("Standing rule -- pitch the
// concept and get a yes BEFORE writing any .scad").
//
// Two separate printed parts:
//   SHELL -- opaque structural body (base plate, vertical riser, flared
//     puck-housing cap). Houses the same real hardware Mushie already
//     uses: the Bambu Lab LED Lamp Kit-001 (D59 x H18mm puck, USB 5V/3W,
//     warm white, 1.5m cable -- store.bambulab.com/products/led-lamp-
//     kit-001). Reuses that same puck-cavity and cable-route knowledge
//     directly rather than re-deriving it.
//   INSERT -- an L-shaped channel piece (re-scoped 2026-09-01 after
//     re-checking Scott's reference photos more closely: the real
//     product's glow is CONTINUOUS from the base's front edge, across
//     the base's top, up the whole riser -- not a window confined to
//     just the riser, which the first version got wrong) that friction-
//     fits into a matching recessed channel running the same path and
//     diffuses the puck's light along its whole length. Print it in a
//     light/translucent color; the shell in an opaque one.
//
// Why this shape, not a uniform bent bar: an early plan tried a single
// constant cross-section swept around two 90-degree bends (like bent
// square tube) so the whole thing shared one profile. That fails on
// its own numbers before any geometry is written -- the puck is 59mm
// across, and a bar cross-section slim enough to look like a headphone-
// stand riser (~42mm) can't also swallow a 59mm disc. The reference
// photos actually show this too, on a second look: the top cap is
// visibly a distinct, wider block than the thin riser below it, not a
// continuation of the same bar -- three distinct forms (base plate,
// riser, cap), not one bent bar.
//
// Why a HULL()ed flare, not a stacked step: the cap has to be wider
// (68mm) and deeper (70mm) than the riser (42 x 28mm) to fit the puck,
// and the cap also has to project forward past the riser's own front
// face to give the headphone headband somewhere to hang. A flat step
// from riser to cap would leave the cap's forward overhang printing over
// open air with nothing under it. Instead the whole transition is a
// hull() between the riser's own top cross-section and the cap's own
// bottom cross-section -- two convex rounded boxes, so the hull is
// guaranteed well-formed with no self-intersection risk (unlike hulling
// concave shapes, this skill's Technique 12/28 trap). The back face is
// pinned flat at every height in this transition (both hulled boxes
// share the same back-face X) so only the FRONT grows forward -- keeps
// the back a clean flat surface and puts 100% of the flare where the
// headphone reach needs it.
//
// Verified per Technique 35 (55 degrees is the STRUCTURAL overhang
// limit, not the surface-quality one -- target <=40 for anything a
// customer will see): the transition's front face grows from x=38 to
// x=80 (42mm) over trans_h=60mm of height, a 35.0-degree wall from
// vertical. Comfortably under the 40-degree target, nowhere near
// Mushie's real 53-degree failure.
// ============================================================

$fn = 64;

// ---- the real hardware being designed around (same as Mushie) ----
puck_d = 59; puck_h = 18;
puck_clear = 2;
puck_cav_d = puck_d + puck_clear * 2;   // 63
puck_cav_h = puck_h + puck_clear;       // 20

// ---- overall stack (target ~226mm, safe under the P1S's 256mm ceiling) ----
base_h   = 14;
riser_h  = 128;   // straight riser section
trans_h  = 60;    // flare transition, riser cross-section -> cap cross-section
cap_h    = 24;
total_h  = base_h + riser_h + trans_h + cap_h;   // 226

// ---- X (depth, back to front) layout -- BACK face pinned at back_x for
// every segment; only the FRONT face moves as the shape flares ----
back_x     = 10;               // riser/cap back face position
riser_d    = 28;                // riser depth (back to front)
riser_front_x = back_x + riser_d;             // 38
cap_d      = 70;                // cap depth (back to front)
cap_front_x   = back_x + cap_d;               // 80

// ---- base plate ----
base_len = 110;   // X, back edge at x=0
base_w   = 50;    // Y, centered on y=0

// ---- riser (straight) cross-section ----
riser_w = 42;   // Y, centered on y=0
riser_corner_r = 4;

// ---- cap (puck housing) cross-section ----
cap_w = 68;   // Y, centered on y=0
cap_hook_fillet = 10;   // single rounding for the whole cap -- vertical
                        // corners AND every top edge, so the front-top
                        // edge (where the headband rests) is generously
                        // rounded along with everything else

// ---- front window / insert ----
// Re-scoped 2026-09-01 after re-checking Scott's own reference photos
// more carefully: the real product's glow is CONTINUOUS from the base's
// front edge, across its top, up the whole riser -- one bent channel and
// one bent insert, not an isolated window partway up the riser. The
// first version only covered the riser; this section and base_solid()/
// base_window_cut() below now cover the whole path.
window_rim   = 4;      // solid rim left around the window opening
window_w     = riser_w - 2 * window_rim;        // 34
window_recess_d = 8;    // how deep the window cuts in from the riser's front face
window_h     = riser_h;    // open at BOTH the top (light from the cap above)
                            // and the bottom (meets the base's own channel,
                            // window_bottom_rim retired -- there is no gap
                            // between them any more)

insert_w = window_w - 0.6;   // 0.3mm clearance/side for a real friction fit
insert_t = window_recess_d - 0.3;   // back flush against the recess floor
                                     // (acts as a reflector); front sits
                                     // 0.3mm shy of the true outer surface
insert_h = window_h - 0.6;

// ---- base channel (the base-plate half of the same continuous window) ----
base_recess_d = 6;      // depth cut into the base's TOP face (base_h=14,
                         // leaves an 8mm floor -- safe)
base_front_open = true; // the recess runs all the way to the base's own
                         // front face (x=base_len), matching the reference
                         // photos' glowing front edge, rather than stopping
                         // short with a solid lip

// ---- cable route (same sizing discipline as Mushie -- 13mm clears the
// USB-A plug on the puck's captive cable; widen later the same way if a
// different puck/kit needs it, per Technique 34's "size for what travels
// it" lesson) ----
cable_ch_d = 13;
cable_bore_x = back_x + 10;   // 20 -- centered in the solid back-wall spine
                              // left once the window recess is cut (spine
                              // spans back_x..riser_front_x-window_recess_d
                              // = 10..30, 20mm thick; bore at x=20 leaves
                              // 3.5mm clearance to each face after the
                              // d=13 bore -- verified below, not eyeballed)
cable_groove_w = 13;
cable_groove_d = 4.2;

// ============================================================
// Shell -- base, riser (with window), transition flare, cap (with puck
// cavity + cable route)
// ============================================================

module base_solid() {
    translate([base_len / 2, 0, base_h / 2])
        cuboid([base_len, base_w, base_h], rounding = 5, edges = "Z", $fn = 48);
}

module riser_slab(x0, x1, y_half, z, h) {
    // a thin rounded-rect slab spanning X in [x0,x1], Y in [-y_half,y_half],
    // at height z, thickness h -- the building block both the straight
    // riser and the hull()-transition are made from.
    translate([(x0 + x1) / 2, 0, z + h / 2])
        cuboid([x1 - x0, 2 * y_half, h], rounding = riser_corner_r, edges = "Z", $fn = 48);
}

module riser_straight_solid() {
    translate([(back_x + riser_front_x) / 2, 0, base_h + riser_h / 2])
        cuboid([riser_d, riser_w, riser_h], rounding = riser_corner_r, edges = "Z", $fn = 48);
}

module transition_solid() {
    // hull() between the riser's own top cross-section and the cap's own
    // bottom cross-section -- both convex rounded boxes, so this is a
    // guaranteed-well-formed flare with no self-intersection risk.
    hull() {
        riser_slab(back_x, riser_front_x, riser_w / 2, base_h + riser_h - 0.1, 0.2);
        riser_slab(back_x, cap_front_x, cap_w / 2, base_h + riser_h + trans_h - 0.1, 0.2);
    }
}

module cap_block_solid() {
    cap_z = base_h + riser_h + trans_h;
    translate([(back_x + cap_front_x) / 2, 0, cap_z + cap_h / 2])
        cuboid([cap_d, cap_w, cap_h], rounding = cap_hook_fillet,
               edges = ["Z", TOP], $fn = 48);
}

// z where the cap block begins -- shared by the cavity and cable route so
// the two stay in sync if the stack heights above ever change
cap_z = base_h + riser_h + trans_h;

// NOTE for the print job, not fixed in geometry: the cap's roof over this
// cavity is a 63mm-diameter unsupported bridge (puck_cav_d) when printed
// in this piece's natural upright orientation -- past the ~40-50mm safe
// bridge distance most FDM setups handle cleanly without sagging. Unlike
// every overhang elsewhere in this file, this one is deliberately NOT
// engineered around (no strut, no split into a 3rd part) because it is
// completely hidden inside the assembled cap once the puck is installed
// -- it fails Technique 35's "will a customer ever see this" test in the
// other direction: nobody ever will. Enable tree/normal supports for
// this one cavity in Bambu Studio; remove them before dropping the puck
// in. Documented here so the choice is explicit, not an oversight.
module puck_cavity() {
    // recessed into the cap's UNDERSIDE, opening downward onto the
    // transition/riser below -- puck sits LED-face-down. Starts 1mm
    // BELOW cap_z for a clean boolean subtraction and stops puck_cav_h
    // above it, leaving cap_h - puck_cav_h = 4mm of roof material on top.
    // (First version of this cavity started at cap_z + cap_h - puck_cav_h
    // and extended UPWARD by puck_cav_h + 1 -- which put the whole thing
    // ABOVE the cap's top surface instead of recessed into its underside.
    // Caught immediately in the first preview render, not assumed correct.)
    translate([back_x + cap_d / 2 + 4, 0, cap_z - 1])
        cylinder(d = puck_cav_d, h = puck_cav_h + 1, $fn = 64);
}

module window_cut() {
    // the front window recess -- open at the TOP (no rim there, so the
    // puck's light spills straight down onto the insert's top edge),
    // solid rim left/right/bottom.
    //
    // Plain cube(), not BOSL2 cuboid() -- found by direct point-probing
    // after the assembled render LOOKED right but was never actually
    // checked: cuboid()'s default anchor is CENTER, so translating to
    // x = riser_front_x - window_recess_d (intended as the recess's BACK
    // edge) put the cuboid CENTERED there instead, leaving the recess
    // spanning only [x-4.5, x+4.5] -- 3.5-4mm short of the riser's real
    // front face at riser_front_x. The recess never broke through to the
    // outside at all; it was a sealed blind pocket, invisible from
    // outside and never seen by the interference check because nothing
    // was there to interfere with. cube()'s corner anchor makes the
    // intended span explicit instead of relying on a center calculation.
    x0 = riser_front_x - window_recess_d;
    x1 = riser_front_x + 1;   // 1mm past the true front face for a clean cut
    translate([x0, -window_w / 2, base_h - 1])
        cube([x1 - x0, window_w, window_h + 2]);
}

module base_window_cut() {
    // the base-plate half of the same continuous channel -- a recess in
    // the base's TOP face, running the base's full length so the glow
    // reaches all the way to its front edge, matching the reference
    // photos (the base's front edge is visibly lit, not just its top).
    // x1 extends 1mm past base_len so this also breaks through the
    // base's own front face, the same "+1 past the true face" pattern
    // window_cut() already uses -- a plain corner-anchored cube(), no
    // BOSL2 center-anchor to get wrong (Technique 37).
    x1 = base_front_open ? base_len + 1 : base_len - 8;
    translate([back_x, -window_w / 2, base_h - base_recess_d])
        cube([x1 - back_x, window_w, base_recess_d + 1]);
}

module light_duct() {
    // Internal tunnel connecting the window's open top (base_h + riser_h,
    // the top of the straight riser) up through the solid transition zone
    // to the puck cavity's floor (cap_z). Found by checking the assembled
    // preview render, not assumed: the window is confined to the straight
    // riser only, so without this the ~60mm-tall transition zone above it
    // is solid, opaque PLA completely blocking the puck's light from ever
    // reaching the insert -- the render looked right (insert visible in
    // its recess) but the thing would print and light up completely dark.
    // Position matches the window's own recess footprint (back wall at
    // riser_front_x - window_recess_d, front at riser_front_x) so light
    // continues straight down with no step. Verified this stays inside
    // the transition's flaring envelope at every height in between: the
    // transition's Y half-width grows from riser_w/2=21 to cap_w/2=34
    // while this duct's own half-width is 14 (comfortably under 21, the
    // TIGHTEST point); the transition's front face grows from
    // riser_front_x=38 to cap_front_x=80 while the duct's own front stays
    // fixed at riser_front_x=38, so it only ever gets MORE margin as
    // height increases, never less.
    duct_z0 = base_h + riser_h - 1;   // 1mm below the window's own top
    duct_z1 = cap_z + 2;              // 2mm into the puck cavity's floor
    translate([riser_front_x - window_recess_d, -14, duct_z0])
        cube([window_recess_d, 28, duct_z1 - duct_z0]);
}

module cable_bore_cylinder(z0, z1) {
    // shared shape -- the SAME bore diameter/position, used to cut both
    // the shell (full height) and, separately, the insert's base-channel
    // arm (just the band where the two now overlap in footprint). Having
    // one module rather than two independent cylinder() calls means the
    // insert's notch can never silently drift out of alignment with the
    // shell's own bore if cable_bore_x/cable_ch_d ever change.
    translate([cable_bore_x, 0, z0]) cylinder(d = cable_ch_d, h = z1 - z0, $fn = 40);
}

module cable_route() {
    // 1. vertical bore from the puck cavity's floor down through the
    //    transition and riser's solid back-wall spine into the base.
    //    Runs from below the base up to 5mm INSIDE the puck cavity
    //    (cap_z + 5, well within the cavity's own z=[cap_z-1,cap_z+20]
    //    range) so the two definitely overlap and merge into one void --
    //    never just touching tangentially.
    cable_bore_cylinder(-1, cap_z + 5 + 1);
    // 2. groove in the base's underside, open downward, running from
    //    beneath the bore out through the base's front edge (identical
    //    proven pattern to Mushie's stem_base_plate groove). Length is
    //    base_len minus the groove's own start position, not base_len
    //    outright -- copying Mushie's cube([base_plate_d, ...]) literally
    //    would run this groove 12.5mm PAST the base's own front edge,
    //    since this design's base starts at x=0 rather than Mushie's
    //    centered-on-origin base. Harmless as a boolean (can't remove
    //    material that isn't there past the solid's own boundary) but
    //    caught and fixed for correctness before it could matter on a
    //    future dimension change.
    groove_x0 = cable_bore_x - cable_ch_d / 2 - 1;
    translate([groove_x0, -cable_groove_w / 2, -1])
        cube([base_len - groove_x0, cable_groove_w, cable_groove_d + 1]);
}

module brand_mark() {
    // moved to the base's UNDERSIDE (2026-09-01): the base's top face is
    // now the base_window_cut() glow channel for its whole length, so
    // there is no flat, unrecessed top-face area left to engrave into
    // near the front edge any more -- the underside is always safe from
    // whatever the top-face feature set does.
    translate([base_len - 16, 0, 0.5])
        mirror([0, 0, 1])
            linear_extrude(height = 1.2)
                text("OnBrandCraftz", size = 5.2, font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}

module glow_stand_shell() {
    difference() {
        union() {
            base_solid();
            riser_straight_solid();
            transition_solid();
            cap_block_solid();
        }
        window_cut();
        base_window_cut();
        light_duct();
        puck_cavity();
        cable_route();
        brand_mark();
    }
}

// ============================================================
// Insert -- the diffusing channel, now a single L-shaped piece running
// from the base's front edge, along the base's top, up the whole riser
// (2026-09-01, re-scoped after re-checking the reference photos: the
// real product's glow is continuous base-to-top, not an isolated window
// partway up the riser). Built as a union of two overlapping rounded
// boxes -- the riser arm and the base arm -- meeting at the corner where
// window_cut() and base_window_cut() themselves meet (z = base_h). Both
// cutters already overlap there by design, so the two insert arms do
// too; union() merges them into one printable, one-piece part with no
// separate mitre geometry needed.
// ============================================================
module glow_stand_insert_riser_arm() {
    // Extends 1mm BELOW base_h into the base arm's own z-range on purpose
    // -- the two arms would otherwise only share a boundary FACE (zero
    // volume overlap) where they meet, which is exactly the kind of
    // exact-touching geometry this project has been burned by before
    // (Technique 15's x=0 axis-touching case). A real 1mm overlap here
    // guarantees union() merges them into one manifold solid rather than
    // a coincident-face edge case that renders "fine" until it doesn't.
    x0 = riser_front_x - window_recess_d;
    h = insert_h + 1;
    translate([x0 + insert_t / 2, 0, base_h - 1 + h / 2])
        cuboid([insert_t, insert_w, h], rounding = 2, edges = "Z", $fn = 32);
}

module glow_stand_insert_base_arm() {
    x1 = base_front_open ? base_len - 0.3 : base_len - 8.3;
    base_insert_t = base_recess_d - 0.3;   // sits flush on the recess floor,
                                            // 0.3mm shy of the top opening
    difference() {
        translate([(back_x + x1) / 2, 0, base_h - base_insert_t / 2])
            cuboid([x1 - back_x, insert_w, base_insert_t], rounding = 2, edges = "Z", $fn = 32);
        // notch for the cable bore -- this arm's footprint fully covers
        // the bore's (x,y) position (Technique: found by checking the
        // actual footprints against each other, not assumed clear), so
        // without this cut the insert would physically block the one
        // path the puck's cable has to reach the base's underside groove.
        cable_bore_cylinder(base_h - base_insert_t - 1, base_h + 1);
    }
}

module glow_stand_insert() {
    union() {
        glow_stand_insert_riser_arm();
        glow_stand_insert_base_arm();
    }
}

// ============================================================
// Layout -- two separate parts, side by side (print separately, hand-
// assemble by sliding the insert into the shell's front window)
// ============================================================
translate([0, -80, 0]) glow_stand_shell();
translate([0, 80, 0]) glow_stand_insert();
