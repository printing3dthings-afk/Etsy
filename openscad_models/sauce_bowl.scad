// Six-well sauce bowl — OnBrandCraftz
//
// The closed sibling of sauce_tray.scad. Same six-petal flower plan, but the
// wells are real cup-shaped CAVITIES sunk into a solid flared bowl instead of
// through-bores, so the whole piece is one enclosed vessel with nothing passing
// through it.
//
// WHY THE CAVITY IS THE SHAPE IT IS. Each cavity follows the actual 2oz
// portion cup's taper — 60.3mm rim, 0.2762mm of radius lost per mm of depth,
// measured from two suppliers. A real cup drops in, sits flat on the floor and
// stands 10.6mm proud so it can be pinched back out.
//
// IT DOES NOT GRIP THE WALL, and an earlier version of this comment said it
// did. Measured 2026-09-08: cav_top_r was set so the cup's RIM (30.15) clears
// the MOUTH (30.55), but the rim sits 10.6mm ABOVE the mouth — at the mouth the
// cup is only 27.22. The gap is a constant 3.33mm of radius, 6.7mm across, the
// entire way up. The cup is held by being 18mm down a well, not by contact.
// Making it actually nest means cav_top_r = 27.62 (a 55.2mm mouth, not 61.1),
// which visibly shrinks every well and wants ring_r re-solved with it — a look
// change, not a tweak, so it is Scott's call and has not been made.
//
// That is a deliberate choice, not a coincidence. FDM layer lines are porous
// and the P1S runs a stock BRASS nozzle, which sheds trace lead, so a dish
// sold to be poured into directly is a food-contact claim this shop cannot
// defend (CLAUDE.md's top rule). Dimensioning the cavity to the real cup keeps
// the piece honestly sellable as a holder while looking and behaving exactly
// like a bowl. Do not re-cut these cavities to an arbitrary size without
// re-opening that question.

$fa = 2;  $fs = 0.4;        // Technique 43: the 12/2 defaults ARE the blocky look

include <BOSL2/std.scad>

part = "bowl";              // bowl | preview | cavity | mark

// ---------- the cup this is built around (measured, sourced) ----------
cup_rim_d   = 60.30;        // identical across both suppliers checked
cup_base_d  = 44.50;
cup_h       = 28.60;
cup_taper_r = (cup_rim_d - cup_base_d) / 2 / cup_h;   // radius lost per mm

// ---------- cavities ----------
n_wells     = 6;
cav_fit     = 0.80;
cav_depth   = 18.00;        // shallower than the cup on purpose: 10.6mm proud
cav_top_r   = (cup_rim_d + cav_fit) / 2;
// THE FLOOR IS A FLAT DISC MEETING THE WALL AT 45 DEGREES, NOT A TANGENT
// FILLET (2026-09-08, from the first real printed part). A tangent fillet is
// horizontal where it meets the floor, so its FIRST layer steps sideways by
// sqrt(2*R*layer - layer^2) all at once: 1.40mm at R=5, i.e. 3.3 extrusions,
// which reads as a hard ring in the bottom of every well. Scott saw it on the
// print. The step shrinks with radius, but a fillet small enough to hide it
// (R <= 0.54mm) is not a rounded floor any more. A constant 45-degree run
// steps exactly one layer height -- 0.20mm, half a bead -- the whole way, and
// that is the floor of what FDM can do. The flat disc is one clean top
// surface and irons smooth.
// No chamfer at the MOUTH, deliberately. One was tried and it cost 1mm of
// radius on each of two neighbouring wells: the web between mouths fell 4.90
// -> 2.90mm, and 4.90 was itself chosen over a 1.9mm "sliver that reads as a
// mistake" (below). A nicer edge is not worth re-opening a margin someone
// already decided.
// The cavity overshoots the top face instead of ending flush with it. Ending
// flush put the cavity's own mouth lid exactly coplanar with the body's top
// plane, and CGAL left a zero-area sliver where each mouth circle crosses y=0
// -- two of them, caught by mesh_gate's degenerate-face check. Carrying the
// taper 1mm into the air above the face removes the coincidence entirely.
cav_over    = 1.00;
cav_cham    = 2.50;         // 45 deg: horizontal run == vertical rise
cav_floor_r = cav_top_r - cav_cham - cup_taper_r * (cav_depth - cav_cham);

// Adjacent centres are exactly ring_r apart for six around. On the through-
// bore tray the binding clearance was the cup RIM (60.3) against a 53mm mouth,
// which 63 satisfied. Here the cavity mouth IS the cup rim plus fit (61.1), so
// 63 left a 1.9mm web between neighbouring mouths -- printable, but a sliver
// that reads as a mistake. 66 gives a real 4.9mm web.
ring_r      = 66.00;

// ---------- bowl body ----------
// THE TOP FACE IS FLAT. It was a shallow paraboloid (19.5 at the axis rising
// to 25 at the rim) and the first real print came out ringed across its whole
// face: 27 concentric terraces, a 36.2mm flat disc in the middle, then rings
// tightening outward. No slicer setting fixes that. The face rose 5.50mm over
// 95mm of radius, so its steepest slope anywhere was 6.6 degrees -- a 1.73mm
// terrace, 4 beads wide. Hiding a 0.2mm step needs slope >= 0.48, which this
// face would only reach at r=391mm. Ironing smooths WITHIN a terrace and
// cannot fill a vertical step; adaptive layers help at the rim and do nothing
// at the axis, because a paraboloid's slope goes to zero at its apex --
// thinner layers just make more, finer rings. A flat face is one top surface
// with no steps at all. The cost is the rim scallop the dish gave for free;
// the flower still reads from the petal outline in plan, which is what the
// eye actually picks up.
floor_min   = 4.15;         // material under every cavity -- unchanged budget
bowl_h      = floor_min + cav_depth;
// The 61mm cavity mouth is far bigger than the tray's 53mm bore, and it does
// NOT fit inside the tray's outline: a numeric sweep of every (angle, height)
// pair found the cavity coming within 0.09mm of breaching the exterior near
// the petal shoulders, which no render showed. rim_r and petal_amp were solved
// against that sweep, not chosen by eye -- this pair clears by 3.08mm.
rim_r       = 95.00;        // base radius at the rim
foot_r      = 87.00;        // base radius at the bed
n_petals    = 6;
petal_amp   = 12.00;
petal_foot  = 0.60;         // petals are 60% developed at the foot, 100% at the
                            // rim: the flower opens as it rises, and the foot
                            // stays broad enough that the flare never exceeds
                            // the overhang limit
flare_ease  = 1.20;         // >1 keeps the lower body near-vertical and puts
                            // the flare up top, which is the printable
                            // direction. A real bowl flares hardest at the
                            // BOTTOM, which is the unprintable one.
                            // Was 1.50. Flattening the top took the body from
                            // 25mm to 22.15mm, so the same 8mm of radius change
                            // now happens over less height and 1.50 pushed the
                            // steepest flare to 40.1 deg -- exactly Technique
                            // 35's ceiling for a surface a buyer can see, with
                            // no margin. 1.20 gives 34.4 deg. Re-measure this
                            // if bowl_h ever moves again; it is a function of
                            // height, not a free style knob.

// dish_lo is set by the floor budget, not picked: dish_z(ring_r) - cav_depth
// = 4.15mm of material under every cavity.
top_cham_h  = 1.20;
top_cham_r  = 1.00;

// ---------- maker's mark ----------
// Sized against THIS model's own flat run: the centre pad bounded by the cavities,
// 2 * (ring_r - cav_top_r). mark_size is DERIVED from it so a -D variant on
// a smaller footprint cannot inherit an oversized mark -- which is exactly what
// the 1oz tray did on the sibling model.
//
// THE MARK IS "OBC", NOT THE FULL WORDMARK, AND THAT IS A PRINTABILITY
// DECISION. The standing rule sizes a mark by its WIDTH against the flat run,
// and says nothing about stroke width -- but stroke width is what decides
// whether it survives the printer. Measured on the real cutter cross-sections:
// "OnBrandCraftz" in Caveat Bold has thinnest strokes of 0.45 / 0.40 / 0.34 /
// 0.20mm on the four variants at 50% of pad, i.e. 1.08 / 0.94 / 0.81 / 0.48 of
// a single 0.42mm extrusion. Three of the four cannot print at all and the
// fourth is one bead wide. "OBC" is 3.43x shorter per unit of size, so at the
// same overall width it gets 3.43x the size and the same multiple of stroke:
// 1.2-1.8mm, or 2.6-3.8 extrusions, on every variant including the smallest.
//
// If the full wordmark is ever wanted back, it needs a pad roughly 3.4x wider
// or a much heavier font -- re-measure, do not assume.
mark_text     = "OBC";
mark_per_size = 2.089;      // mm of width per unit of size, MEASURED for this
                            // exact string and font. Changing either invalidates
                            // it; re-measure via part="mark", which renders the
                            // cutter alone in about a second.
mark_frac     = 0.45;       // top of the 35-45% standing range
mark_pad      = 2 * (ring_r - cav_top_r);
mark_size     = mark_pad * mark_frac / mark_per_size;
mark_depth  = 0.70;


// ============================================================
// EXTERIOR
// ============================================================

function ease(z) = pow(z / bowl_h, flare_ease);

function edge_trim(z) = (z > bowl_h - top_cham_h)
    ? top_cham_r * (z - (bowl_h - top_cham_h)) / top_cham_h : 0;

function bowl_r(a, z) =
    let(t = ease(z))
      foot_r + (rim_r - foot_r) * t
    + petal_amp * (petal_foot + (1 - petal_foot) * t) * cos(n_petals * a)
    - edge_trim(z);

function ring(z) = [for (a = [0 : 1 : 359]) [bowl_r(a,z) * cos(a),
                                             bowl_r(a,z) * sin(a)]];

// Derived from bowl_h, never a literal list -- a hardcoded one on the tray
// silently kept the body 3mm taller than the source said.
z_samples = concat(
    [for (i = [0 : 10]) (bowl_h - top_cham_h) * i / 10],
    [bowl_h - top_cham_h * 0.66, bowl_h - top_cham_h * 0.33, bowl_h]
);

module bowl_solid() { skin([for (z = z_samples) ring(z)], z = z_samples, slices = 0); }

// ============================================================
// CAVITY — follows the real cup's taper, flat floor, filleted corner
// ============================================================

module cup_cavity() {
    rotate_extrude($fn = 160)
        polygon([
            [0, 0],
            [cav_floor_r, 0],                        // flat floor, one top surface
            [cav_floor_r + cav_cham, cav_cham],      // 45 deg, 0.20mm steps
            [cav_top_r + cup_taper_r * cav_over,     // the real cup's own taper,
             cav_depth + cav_over],                  // carried past the top face
            [0, cav_depth + cav_over]
        ]);
}

module cavities() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells])
            translate([ring_r, 0, bowl_h - cav_depth])
                cup_cavity();
}


// ============================================================
// MAKER'S MARK — negative cut into the underside
// ============================================================

module brand_mark() {
    translate([0, 0, -0.5])                 // MUST dip below z=0; a cutter that
        linear_extrude(height = mark_depth + 0.5)   // only touches removes nothing
            mirror([0, 1, 0])               // confirmed axis, Technique 4
                text(mark_text, size = mark_size,
                     font = "Caveat:style=Bold", halign = "center", valign = "center");
}


// ============================================================
// PREVIEW ONLY
// ============================================================

module cup_mock() {
    translate([0, 0, bowl_h - cav_depth + 0.4])
        cylinder(h = cup_h, d1 = cup_base_d, d2 = cup_rim_d);
}
module cups() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells]) translate([ring_r, 0, 0]) cup_mock();
}

module bowl() { difference() { bowl_solid(); cavities(); brand_mark(); } }

if      (part == "bowl")    bowl();
else if (part == "cavity")  cavities();      // check a cutter's own extents alone
else if (part == "mark")    brand_mark();
else if (part == "preview") { color("#E8DFD2") bowl(); color("#C0392B", 0.5) cups(); }
