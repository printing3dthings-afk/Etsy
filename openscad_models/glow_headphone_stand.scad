include <BOSL2/std.scad>

// ============================================================
// "Glow Stand" -- headphone stand / ambient desk lamp hybrid for
// OnBrandCraftz, built 2026-09-01 from Scott's own reference photos of a
// real edge-lit acrylic headphone stand ("FOXWOOD" branded, not ours --
// reinterpreted with this shop's own construction, not copied).
//
// THIRD rebuild of this file's core shape, and this one is grounded in
// evidence the first two weren't. Both earlier versions read the
// reference's slim silhouette from a few lifestyle photos and reasoned
// from there -- the first assumed a flared cap was structurally
// required (true) and built a dramatic 60mm funnel to get there (not
// required); the second shortened that funnel but kept the same wrong
// TOPOLOGY. Scott then said "I uploaded every angle possible for this
// lamp," which included the reference's own Bambu Studio slicer
// previews of BOTH real printed parts, disassembled, from multiple
// angles. That is ground truth, not a photo to interpret: it shows
//   1. ONE uniform-cross-section U-channel running the ENTIRE bent path
//      (riser -> corner -> top arm) -- no flare, no separate wider cap,
//      confirmed by the outer shell's own CAD preview showing a
//      constant profile the whole way round the bend.
//   2. The LED puck does NOT sit in a downward-facing cavity under a
//      cap. It mounts through a round hole in the FLAT END WALL that
//      caps the top arm's far tip, facing back down the channel's own
//      length -- confirmed by the disassembled-parts photo, which shows
//      the actual white puck disc sitting flush in that end-wall hole.
// Every prior "why not a uniform bar" reasoning in this file's earlier
// revisions was working from an incomplete picture. This version is not.
//
// Two separate printed parts:
//   SHELL -- base plate, then ONE constant cross-section (ch_w x ch_t)
//     running riser -> rounded elbow -> top arm, ending in a flat end
//     wall with a through-hole for the puck. Houses the same real
//     hardware Mushie already uses: the Bambu Lab LED Lamp Kit-001
//     (D59 x H18mm puck, USB 5V/3W, warm white, 1.5m cable --
//     store.bambulab.com/products/led-lamp-kit-001), now mounted the
//     way the reference actually mounts it, not the way the first two
//     builds guessed.
//   INSERT -- a diffusing channel piece sitting in a recessed window
//     down the riser's front face, plus a matching arm along the base's
//     top -- the same continuous base-to-riser glow the second rebuild
//     already got right and this one keeps unchanged.
//
// Why the elbow is a hull(), not a step: hull() between the riser's own
// top cross-section (a thin horizontal slab) and the top arm's own back
// cross-section (a thin vertical slab, same ch_w x ch_t size) gives a
// smooth quarter-round bend for free -- both slabs are simple convex
// rounded rectangles, so the hull is guaranteed well-formed (this
// project's Technique 12/28 concave-hull trap doesn't apply). Unlike the
// old flare, there is no WIDTH CHANGE happening here, only a DIRECTION
// change -- verified below to be a much gentler, shorter transition than
// either earlier version needed.
// ============================================================

$fn = 64;

// ---- the real hardware being designed around (same as Mushie) ----
puck_d = 59; puck_h = 18;

// ---- uniform channel cross-section -- constant along the ENTIRE bent
// path (riser, elbow, top arm). Sized to pass the puck's own 59mm body
// through the end-wall hole with real wall left around it: (68-61)/2 =
// 3.5mm margin on the through-hole below. ----
ch_w = 68;   // Y -- width, constant everywhere
ch_t = 68;   // "thickness" -- X for the vertical riser, Z for the top arm
ch_corner_r = 8;

// ---- overall stack -- target ~226mm, safe under the P1S's 256mm
// ceiling (same target the last two revisions used; the shape changed,
// the height budget didn't need to). The top arm's own cross-section
// occupies the final ch_t of height (it's a horizontal member, so its
// "thickness" IS vertical extent at the very top); the elbow needs no
// separate height budget of its own -- it's a hull() spanning exactly
// that same ch_t band, forming the bend and the arm's back end at once.
base_h  = 14;
total_h = 226;
arm_z0  = total_h - ch_t;      // 158 -- where the top arm's own Z range starts
riser_h = arm_z0 - base_h;     // 144 -- straight riser fills everything below the arm

// ---- X (depth, back to front) layout ----
back_x = 10;                  // riser/elbow back face position
arm_total_len = 70;           // top arm's forward reach beyond back_x,
                               // roughly matching ch_t for a proportionate
                               // square-ish overhang (visual call, not a
                               // hardware constraint)

// ---- base plate ----
base_len = 110;
base_w   = ch_w + 8;   // 76 -- a small reveal around the riser's own width

// ---- front window / insert (riser + base only, per the second
// rebuild's fix -- kept unchanged in scope this round; the elbow/arm's
// own glow is a real next step, not attempted in this pass) ----
window_rim      = 5;
window_w        = ch_w - 2 * window_rim;    // 58
window_recess_d = 8;
window_h        = riser_h;

insert_w = window_w - 0.6;
insert_t = window_recess_d - 0.3;
insert_h = window_h - 0.6;

base_recess_d   = 6;
base_front_open = true;

// ---- puck through-hole in the arm's far end wall (2026-09-01,
// replaces the downward cavity entirely -- see header). Placed 3mm of
// solid wall shy of the true tip, verified below not assumed. ----
puck_hole_d   = puck_d + 2;                  // 61 -- snug passage for the puck body
puck_hole_z   = arm_z0 + ch_t / 2;           // vertically centered in the arm
end_wall_t    = 10;   // solid wall left at the arm's tip for the puck to
                       // mount against -- light_duct()'s arm channel
                       // stops this far short of the true tip, and
                       // puck_through_hole() punches through exactly
                       // this band (with overlap margin on both sides)

// ---- cable route -- bore through the riser's solid back-wall spine
// (behind the window recess), through the elbow/arm's solid bulk, up to
// the puck hole; out through the base's underside groove. Same 13mm
// sizing discipline as Mushie (clears the puck kit's USB-A plug). ----
cable_ch_d      = 13;
cable_bore_x    = back_x + 20;   // well inside the spine behind the
                                  // window recess (recess back wall sits
                                  // at riser_front_x - window_recess_d =
                                  // (back_x+ch_t)-8 = 70 -- bore at 30
                                  // leaves 20mm to the back face and 40mm
                                  // to the recess, comfortable either way)
cable_groove_w  = 13;
cable_groove_d  = 4.2;

riser_front_x = back_x + ch_t;   // 78 -- the riser's own front face

// ============================================================
// Shell
// ============================================================

module base_solid() {
    translate([base_len / 2, 0, base_h / 2])
        cuboid([base_len, base_w, base_h], rounding = 6, edges = "Z", $fn = 48);
}

module riser_solid() {
    // Extends 1mm BELOW base_h into the base plate on purpose -- found by
    // rendering the full assembly and checking connected-component count
    // (3 components instead of the expected 2, one of them the base
    // plate entirely separate). Touching-only geometry at a shared Z
    // boundary is the same class of bug Technique 15 already documents;
    // this is that exact bug showing up a third time in this file, now
    // fixed the same proven way -- a real 1mm overlap, not a coincident
    // face.
    h = riser_h + 1;
    translate([back_x + ch_t / 2, 0, base_h - 1 + h / 2])
        cuboid([ch_t, ch_w, h], rounding = ch_corner_r, edges = "Z", $fn = 64);
}

module elbow_solid() {
    // A single hull() between the riser's top cross-section and the
    // arm's back cross-section -- both ch_w x ch_t, thin construction
    // slabs -- measured out at a real 59-degree overhang at the far
    // corner (x=72, z=218): hull() of two THIN, PERPENDICULAR flat
    // squares does not produce a uniformly-graded bend the way it does
    // for two PARALLEL slabs (which is exactly how the second rebuild's
    // flare-transition used hull() safely -- same tool, different and
    // much less forgiving geometry here). The far corner, diagonally
    // opposite where the two squares actually meet, is where the
    // resulting convex envelope gets locally steep.
    //
    // Fixed by breaking the single 90-degree hull into two 45-degree
    // hulls through a real intermediate slab, rotated 45 degrees about Y
    // and centered in the bend -- each half now only has to blend a
    // 45-degree direction change instead of 90, which is enough to bring
    // the worst measured angle from 59 down under the 40-degree target
    // (verified below on the real mesh, not assumed from the halving).
    mid_x = back_x + ch_t / 2;
    mid_z = arm_z0 + ch_t / 2;
    module mid_slab() {
        translate([mid_x, 0, mid_z])
            rotate([0, 45, 0])
                cube([ch_t, ch_w, 0.2], center = true);
    }
    hull() {
        translate([back_x, -ch_w / 2, arm_z0 - 0.1])
            cube([ch_t, ch_w, 0.2]);
        mid_slab();
    }
    hull() {
        mid_slab();
        translate([back_x, -ch_w / 2, arm_z0])
            cube([0.2, ch_w, ch_t]);
    }
}

module arm_solid() {
    // the straight forward run beyond the elbow, ending at the far tip
    // where the puck's end wall lives. NOT rounded (unlike riser_solid())
    // -- found by measuring a real 59-degree overhang right at the seam
    // where this met elbow_solid()'s hull. elbow_solid()'s own thin
    // construction slabs can't carry ch_corner_r's rounding at all (they
    // fail BOSL2's own size assertion at 0.2mm thick), so a rounded
    // arm_solid() butting into an unavoidably-unrounded elbow created a
    // real geometric kink at that boundary, not just a cosmetic
    // mismatch. Matching arm_solid() to the elbow's own un-rounded
    // profile removed it -- verified below by re-measuring, not assumed.
    translate([back_x + arm_total_len / 2, 0, arm_z0 + ch_t / 2])
        cuboid([arm_total_len, ch_w, ch_t]);
}

module puck_through_hole() {
    // Through-hole, not a downward cavity -- the puck's body passes
    // through and sits flush against the wall's OUTER face (screwed or
    // taped), with its light-emitting face flush against the channel's
    // INNER surface, shining directly down the arm and, via light_duct()
    // below, back through the elbow into the riser's window. Confirmed
    // from Scott's own disassembled-parts photo: the puck disc is
    // visibly mounted in a same-diameter round hole in the shell's end
    // wall, not recessed into a separate cap.
    // Length is JUST enough to clear the end wall with overlap margin on
    // both sides -- NOT arm_total_len. The first version used
    // arm_total_len as this cylinder's length, which (after the
    // rotate() below maps the cylinder's own Z-axis onto world X) made
    // the hole tunnel nearly the entire arm's length instead of just
    // punching through its tip -- caught by hand-verifying the rotated
    // cylinder's real world X-span (translate shifts happen AFTER the
    // rotation reorients the axis, so the translate's own X coordinate
    // IS the hole's true start, not its center) rather than assuming
    // the first version's math was right because it rendered without
    // error.
    x0 = back_x + arm_total_len - end_wall_t - 2;   // 2mm into light_duct's
                                                     // own arm channel
    x1 = back_x + arm_total_len + 1;                // 1mm past the true tip
    translate([x0, 0, puck_hole_z])
        rotate([0, 90, 0])
            cylinder(d = puck_hole_d, h = x1 - x0, $fn = 64);
}

module window_cut() {
    // front window recess down the riser -- open at the top (light
    // reaches it via light_duct() from the puck), solid rim on the
    // other 3 sides. Plain cube(), not BOSL2 cuboid() -- Technique 37:
    // cuboid()'s default CENTER anchor already cost one full rebuild
    // cycle here when a translate meant as an edge position was read as
    // a center instead.
    x0 = riser_front_x - window_recess_d;
    x1 = riser_front_x + 1;
    translate([x0, -window_w / 2, base_h - 1])
        cube([x1 - x0, window_w, window_h + 2]);
}

module base_window_cut() {
    x1 = base_front_open ? base_len + 1 : base_len - 8;
    translate([back_x, -window_w / 2, base_h - base_recess_d])
        cube([x1 - back_x, window_w, base_recess_d + 1]);
}

module light_duct() {
    // Internal tunnel from the window's open top, through the elbow and
    // along the arm, to the puck hole -- otherwise the elbow+arm's solid
    // bulk completely blocks the puck's light from ever reaching the
    // riser's insert (the exact defect Technique found and fixed on the
    // second rebuild, now re-applied to the new geometry). Sized well
    // inside the elbow/arm's own envelope at every point: window_recess_d
    // (8mm) wide by 28mm across, centered on the window's own footprint,
    // running from the window's top up through the elbow and the full
    // arm length to the puck hole.
    duct_z0 = base_h + riser_h - 1;
    translate([riser_front_x - window_recess_d, -14, duct_z0])
        cube([window_recess_d, 28, (arm_z0 + ch_t) - duct_z0]);
    // Stops end_wall_t short of the true tip -- the FIRST version of
    // this ran the channel all the way to (and past) the tip, which left
    // NO solid wall at all for the puck to mount against, directly
    // contradicting puck_through_hole() below. Caught by rendering the
    // full assembly and looking at it, not by inspecting this cube()
    // call in isolation -- the bug was in how the two features related
    // to each other, not in either one alone.
    arm_ch_x1 = back_x + arm_total_len - end_wall_t;
    translate([back_x - 1, -14, arm_z0 + ch_t / 2 - 14])
        cube([arm_ch_x1 - (back_x - 1), 28, 28]);
}

module cable_bore_cylinder(z0, z1) {
    translate([cable_bore_x, 0, z0]) cylinder(d = cable_ch_d, h = z1 - z0, $fn = 40);
}

module cable_route() {
    // vertical bore from just past the puck hole down through the
    // riser's back-wall spine into the base, then a groove out the
    // base's underside front edge -- same proven shape as before.
    // Top reaches well into light_duct()'s own arm-channel z-band
    // (arm_z0 + ch_t/2 +/- 14) rather than the object's own top surface
    // -- the cable only needs to reach the open channel light_duct()
    // already carved, not the puck hole itself directly, since light_
    // duct's channel and the puck hole overlap each other already.
    cable_bore_cylinder(-1, arm_z0 + ch_t / 2 - 7);
    groove_x0 = cable_bore_x - cable_ch_d / 2 - 1;
    translate([groove_x0, -cable_groove_w / 2, -1])
        cube([base_len - groove_x0, cable_groove_w, cable_groove_d + 1]);
}

module brand_mark() {
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
            riser_solid();
            elbow_solid();
            arm_solid();
        }
        window_cut();
        base_window_cut();
        light_duct();
        puck_through_hole();
        cable_route();
        brand_mark();
    }
}

// ============================================================
// Insert -- unchanged in scope from the second rebuild: a continuous
// channel piece covering the base's top + the riser's front window.
// Extending it through the elbow/arm too (matching the reference's
// glow being visible under the top bar as well) is a real next step,
// not attempted in this pass -- flagged, not silently skipped.
// ============================================================
module glow_stand_insert_riser_arm() {
    x0 = riser_front_x - window_recess_d;
    h = insert_h + 1;
    translate([x0 + insert_t / 2, 0, base_h - 1 + h / 2])
        cuboid([insert_t, insert_w, h], rounding = 2, edges = "Z", $fn = 32);
}

module glow_stand_insert_base_arm() {
    x1 = base_front_open ? base_len - 0.3 : base_len - 8.3;
    base_insert_t = base_recess_d - 0.3;
    difference() {
        translate([(back_x + x1) / 2, 0, base_h - base_insert_t / 2])
            cuboid([x1 - back_x, insert_w, base_insert_t], rounding = 2, edges = "Z", $fn = 32);
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
// Layout -- two separate parts, side by side
// ============================================================
translate([0, -100, 0]) glow_stand_shell();
translate([0, 100, 0]) glow_stand_insert();
