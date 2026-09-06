// Six-well sauce cup tray -- OnBrandCraftz
//
// Holds six standard 2oz plastic portion cups in a ring. It holds the CUPS,
// never the sauce: FDM layer lines are porous and harbour bacteria, and this
// shop's P1S runs a stock BRASS nozzle, which sheds trace lead. A tray a
// customer pours sauce into is not a claim we can defend (CLAUDE.md's
// top-priority rule), and it is also why nearly every popular real design in
// this category holds a packet or a tub rather than the sauce itself.
//
// Cup dimensions are measured from two independent suppliers, not guessed:
//   Choice  2oz: top 2-3/8in (60.3) x bottom 1-3/4in (44.5) x 1-1/8in (28.6)
//   Dart 200PC : top 2-3/8in (60.3) x bottom 1-13/16in (46.0) x 1-3/16in (30.2)
// The TOP diameter agrees exactly across brands; bottom and height do not.
// So the well grips the cup's TAPER at a fixed bore -- the one dimension both
// brands share -- instead of matching a full cone that only fits one of them.

$fa = 2;  $fs = 0.4;        // Technique 43: OpenSCAD's 12/2 defaults ARE the
                            // "blocky" look. Every organic model gets these.

include <BOSL2/std.scad>

part = "tray";              // tray | preview | cutters | mark

// ---------- the cup this is built for (measured, sourced) ----------
cup_rim_d   = 60.30;
cup_base_d  = 44.50;        // Choice; Dart is 46.0 -- both clear well_bore_d
cup_h       = 28.60;

// ---------- wells ----------
n_wells     = 6;
well_bore_d = 47.00;        // the cup wedges where its taper reaches this.
                            // Below both brands' rim, above both their bases,
                            // so every brand seats -- only the depth varies.
well_mouth_d= 53.00;        // top of the entry chamfer. Kept SHORT on
                            // purpose: widen it and the cup stops on the
                            // chamfer's top edge instead of the bore, which
                            // seats it 20mm higher and hangs its base clean
                            // through the table.
// For n wells evenly spaced, adjacent CENTRES are exactly ring_r apart
// (2*ring_r*sin(180/6) = ring_r). The binding clearance is not the bore --
// it is the cup RIM, which is wider than the bore and flares out ABOVE the
// tray where no geometry constrains it. A first pass sized this against the
// bores at 52 and the rendered cups overlapped each other by 8.3mm: six cups
// that could not physically be inserted, in a model that rendered clean.
ring_r      = 63.00;        // cup_rim_d + 2.7 gap between neighbouring rims

// ---------- plate ----------
// A flat slab 10mm thick under 28.6mm cups rendered as a coaster with cups
// standing on it, not as a designed piece. The top face is a shallow
// paraboloid instead: low in the middle, rising to the rim. That single
// change also makes the rim SCALLOP for free -- at a petal the body reaches
// base_r and keeps full height, at a valley it stops short and the dish has
// already cut it down, so the edge rises and falls with the petals without
// any extra geometry.
bore_top    = 6.00;         // cup seats on the bore's top edge, here
chamfer_h   = 3.00;
plate_h     = 14.00;        // max height, at the rim
dish_lo     = 7.50;         // top face at the centre
base_r      = 88.00;

// ---------- silhouette: six petals, one per cup ----------
n_petals    = 6;
petal_amp   = 16.00;   // the hero form: one bold lobe per cup. Deep valleys
                       // are not only prettier, they remove real area -- and
                       // on a 200mm tray the whole print cost is layer AREA.

// ---------- surface: flutes carved INWARD, under the rim ----------
// Technique 52 measured this shop at rugosity 1.000-1.086 against a 157-mesh
// reference corpus whose p75 is 1.235, and concluded plain surfaces read as
// unfinished. Its own prescription is to raise texture OUTWARD rather than
// carve in -- but raising it here was wrong, and a three-way silhouette
// comparison in plan is what showed why: proud ridges become the outline, and
// 48 of them turned a clean six-petal flower into a ragged sawtooth. The
// petals are the hero form (Technique 31: spend boldness in one place), so
// the flutes are cut IN, below the rim, and never reach the rim's radius.
// The plan silhouette stays the petal curve; the skirt still gets real
// relief; and the rim now overhangs the fluted band, which is a shadow line
// rather than a defect. There is a real wall budget for this: even at a petal
// valley the nearest bore is 18mm away, so a 2.6mm groove costs nothing.
// OFF (depth 0). Two studio renders settled this empirically rather than by
// argument: at 2.6mm the flutes vanished under soft light, and at 3.4mm with
// deliberately raking light they STILL vanished -- because the rim sits at the
// full petal radius and overhangs them, so the fluted band is only visible
// from near floor level. On a tray that lives on a table, nobody ever sees it.
// The petal silhouette is the hero and carries the piece alone (Technique 31:
// spend boldness in one place); a feature no one can see is not texture, it is
// print time. Left parameterised, not deleted -- on a taller-skirted variant,
// or one without the overhanging rim, this would read fine.
n_flutes    = 36;
flute_depth = 0.00;
flute_rise  = 1.20;         // fade in off the bed: the first layer prints the
                            // full clean outline
flute_top   = 13.00;        // flutes are gone by here, so the rim is one
flute_fall  = 4.40;         // unbroken line. 3.4mm over 4.4mm of fade is
                            // 37.7 deg from vertical -- inside the 40 deg
                            // limit Technique 35 sets for a visible surface.
                            // Depth went 2.6 -> 3.4 because the STUDIO render
                            // showed the shallower cut washing out completely
                            // under soft light while looking fine in the flat
                            // CAD preview -- Technique 36's exact warning.

// ---------- top edge ----------
top_cham_h  = 1.20;
top_cham_r  = 1.00;         // radius shrinking as z rises = every layer sits
                            // on a wider one. Never chamfer the BOTTOM edge:
                            // it is the bed contact.

// No centre boss. The dish's own low middle is the negative space
// (Technique 31: leave deliberate plain surface, don't fill every face), and
// it is where a drip off a cup ends up rather than on the table.

// ---------- maker's mark ----------
// Sized against THIS model's own flat run, never copied from another model.
// The largest uninterrupted flat area on the underside is the centre pad
// bounded by the bores: radius ring_r - well_bore_d/2 = 39.5, so 79mm across.
//
// 2026-09-06, Scott: "make the branding a little bigger." This now runs at
// ~50% of that pad, deliberately above the 35-45% default the standing rule
// gives. That default came from Scott's own earlier correction on a cable clip
// whose mark hit 77% of the part; 50% is a considered middle, not a drift back
// to the old mistake. Do not "fix" this down to 45% without asking.
// Measured on the real exported mesh at 39.36mm -- re-measure after any change,
// a linear projection from one sample has been wrong here before.
// Measured: "OnBrandCraftz" in Caveat Bold renders 7.157mm of width per unit
// of size (checked at seven sizes, dead linear). Deriving mark_size from the
// pad instead of setting it means a -D variant on a smaller footprint cannot
// silently inherit an oversized mark -- which is exactly what happened to the
// 1oz tray, sitting at 50.8% of its pad while the 2oz sat at 39.9%.
// CHANGING THE TEXT OR FONT INVALIDATES 7.157 -- re-measure via part="mark".
mark_per_size = 7.157;
mark_frac     = 0.50;
mark_pad      = 2 * (ring_r - well_bore_d / 2);
mark_size     = mark_pad * mark_frac / mark_per_size;
mark_depth  = 0.70;


// ============================================================
// SILHOUETTE
// ============================================================

function flute_fade(z) = min(min(1, z / flute_rise),
                             max(0, min(1, (flute_top - z) / flute_fall)));

// Radius pulled IN near the top only. A chamfer here is safe; the same
// chamfer at z=0 would lift the bed contact off its own outline.
function edge_trim(z) = (z > plate_h - top_cham_h)
    ? top_cham_r * (z - (plate_h - top_cham_h)) / top_cham_h
    : 0;

// Technique 19: a smooth (0.5+0.5cos) groove reads as soft fluting; abs(cos)
// puts a cusp at every zero crossing and reads as sharp corrugation instead.
// Petals and flutes are both maxima at a=0, so the pattern lands the same way
// on every petal without any phase term -- the alignment bug Technique 19
// documents came from ADDING a phase that was not needed.
function skirt_r(a, z) =
      base_r
    + petal_amp * cos(n_petals * a)
    - flute_depth * (0.5 + 0.5 * cos(n_flutes * a)) * flute_fade(z)
    - edge_trim(z);

function ring(z) = [for (a = [0 : 1 : 359]) [skirt_r(a,z) * cos(a),
                                             skirt_r(a,z) * sin(a)]];

// DERIVED from plate_h, never a literal list. This was hardcoded ending at
// 17.0, and when plate_h was changed to 14 the body silently stayed 17mm tall
// -- the dish cut hid it in every render, and only measuring the exported
// mesh's bounding box caught it (16.1mm where 14 was intended). Same class of
// bug as any magic number: a -D override appears to work and does nothing.
// Dense near the bed for the flute fade-in and near the rim for the chamfer,
// coarse through the middle where nothing changes.
z_samples = concat(
    [0, 0.4, 0.8, 1.2, 1.6, 2.0],
    [for (i = [1 : 8]) 2.0 + (plate_h - top_cham_h - 2.0) * i / 8],
    [plate_h - top_cham_h * 0.66, plate_h - top_cham_h * 0.33, plate_h]
);

// One skin(), never a union of per-segment extrudes -- Technique 5 measured
// that as the difference between 45 seconds and a timeout.
module skirt_solid() {
    skin([for (z = z_samples) ring(z)], z = z_samples, slices = 0);
}

// Top face: z = dish_lo at the axis, rising to plate_h at base_r.
function dish_z(r) = dish_lo + (plate_h - dish_lo) * pow(r / base_r, 2);

// Everything ABOVE that surface, as a solid to subtract. Built as a
// rotate_extrude of an explicit arc rather than a huge sphere -- a sphere of
// the required radius (755mm) would carry an enormous facet count under this
// file's $fa/$fs. The profile spans a real segment of the axis, never closing
// to a single point on it (Technique 15).
dish_far    = base_r * 1.4;
module dish_cut() {
    rotate_extrude($fn = 240)
        polygon(concat(
            [for (i = [0 : 48]) let(r = dish_far * i / 48) [r, dish_z(r)]],
            [[dish_far, plate_h + 30], [0, plate_h + 30]]
        ));
}

module tray_gross() { skirt_solid(); }


// ============================================================
// WELLS
// ============================================================

module well_cutter() {
    // through-bore: the cup's base hangs in free air below the seat, and the
    // cup can be pushed out from underneath. No floor to bridge.
    translate([0, 0, -1])
        cylinder(h = bore_top + 1, d = well_bore_d);
    translate([0, 0, bore_top])
        cylinder(h = chamfer_h, d1 = well_bore_d, d2 = well_mouth_d);
    // straight above the chamfer, up through whatever height the dished top
    // face happens to have at this radius
    translate([0, 0, bore_top + chamfer_h])
        cylinder(h = plate_h + 5, d = well_mouth_d);
}

module wells() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells])
            translate([ring_r, 0, 0]) well_cutter();
}


// ============================================================
// MAKER'S MARK -- negative cut, underside, standing rule
// ============================================================

module brand_mark() {
    // Cutter dips BELOW z=0. A cutter that only touches the surface removes
    // nothing and renders perfectly clean (Technique 4).
    translate([0, 0, -0.5])
        linear_extrude(height = mark_depth + 0.5)
            mirror([0, 1, 0])
                text("OnBrandCraftz", size = mark_size,
                     font = "Caveat:style=Bold",
                     halign = "center", valign = "center");
}


// ============================================================
// PREVIEW ONLY -- never exported
// ============================================================

module cup_mock() {
    seat_t = (cup_rim_d - well_bore_d) * cup_h / (cup_rim_d - cup_base_d);
    translate([0, 0, bore_top - (cup_h - seat_t)])
        cylinder(h = cup_h, d1 = cup_base_d, d2 = cup_rim_d);
}

module cups() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells])
            translate([ring_r, 0, 0]) cup_mock();
}


module tray() {
    difference() { tray_gross(); dish_cut(); wells(); brand_mark(); }
}


if      (part == "tray")    tray();
else if (part == "cutters") { wells(); }          // Technique 37: check a
else if (part == "mark")    brand_mark();         // cutter's OWN extents alone
else if (part == "preview") {
    color("#E8DFD2") tray();
    color("#C0392B", 0.55) cups();
}
