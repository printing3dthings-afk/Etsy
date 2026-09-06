// Six-well sauce bowl — OnBrandCraftz
//
// The closed sibling of sauce_tray.scad. Same six-petal flower plan, but the
// wells are real cup-shaped CAVITIES sunk into a solid flared bowl instead of
// through-bores, so the whole piece is one enclosed vessel with nothing passing
// through it.
//
// WHY THE CAVITY IS THE SHAPE IT IS. Each cavity follows the actual 2oz
// portion cup's taper — 60.3mm rim, 0.2762mm of radius lost per mm of depth,
// measured from two suppliers — plus 0.8mm of fit. A real cup drops in and
// nests against the wall down its whole length, standing 10.6mm proud so it
// can still be pinched out.
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
cav_fillet  = 5.00;         // rounded floor — wipes clean, reads as a bowl
cav_flat_r  = cav_top_r - cup_taper_r * (cav_depth - cav_fillet) - cav_fillet;
// Adjacent centres are exactly ring_r apart for six around. On the through-
// bore tray the binding clearance was the cup RIM (60.3) against a 53mm mouth,
// which 63 satisfied. Here the cavity mouth IS the cup rim plus fit (61.1), so
// 63 left a 1.9mm web between neighbouring mouths -- printable, but a sliver
// that reads as a mistake. 66 gives a real 4.9mm web.
ring_r      = 66.00;

// ---------- bowl body ----------
bowl_h      = 25.00;        // rim height
dish_lo     = 19.50;        // top face at the axis -- set by the floor budget
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
flare_ease  = 1.50;         // >1 keeps the lower body near-vertical and puts
                            // the flare up top, which is the printable
                            // direction. A real bowl flares hardest at the
                            // BOTTOM, which is the unprintable one.

// dish_lo is set by the floor budget, not picked: dish_z(ring_r) - cav_depth
// = 4.15mm of material under every cavity.
top_cham_h  = 1.20;
top_cham_r  = 1.00;

// ---------- maker's mark ----------
// 35-45% of the 70.9mm centre pad bounded by the cavities = 24.8-31.9mm.
// Measure it on the exported mesh; a linear projection has been wrong before.
mark_size   = 3.60;
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

// Top face: a shallow paraboloid, low at the axis and rising to the rim. It
// also makes the rim scallop for free -- at a petal the body reaches rim_r and
// keeps full height, at a valley it stops short and the dish has already cut
// it down.
function dish_z(r) = dish_lo + (bowl_h - dish_lo) * pow(r / rim_r, 2);
dish_far = rim_r * 1.5;
module dish_cut() {
    rotate_extrude($fn = 240)
        polygon(concat([for (i = [0 : 48]) let(r = dish_far * i / 48) [r, dish_z(r)]],
                       [[dish_far, bowl_h + 30], [0, bowl_h + 30]]));
}


// ============================================================
// CAVITY — follows the real cup's taper, flat floor, filleted corner
// ============================================================

module cup_cavity() {
    rotate_extrude($fn = 160)
        polygon(concat(
            [[0, 0], [cav_flat_r, 0]],
            [for (i = [0 : 12]) let(th = -90 + 90 * i / 12)
                [cav_flat_r + cav_fillet * cos(th), cav_fillet + cav_fillet * sin(th)]],
            [[cav_top_r, cav_depth], [0, cav_depth]]
        ));
}

module cavities() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells])
            translate([ring_r, 0, dish_z(ring_r) - cav_depth])
                // extend the open top well past the dished surface so the
                // cavity mouth is cut by the real top face, not by its own
                // flat lid
                union() { cup_cavity();
                          translate([0, 0, cav_depth])
                              cylinder(h = bowl_h, r = cav_top_r); }
}


// ============================================================
// MAKER'S MARK — negative cut into the underside
// ============================================================

module brand_mark() {
    translate([0, 0, -0.5])                 // MUST dip below z=0; a cutter that
        linear_extrude(height = mark_depth + 0.5)   // only touches removes nothing
            mirror([0, 1, 0])               // confirmed axis, Technique 4
                text("OnBrandCraftz", size = mark_size,
                     font = "Caveat:style=Bold", halign = "center", valign = "center");
}


// ============================================================
// PREVIEW ONLY
// ============================================================

module cup_mock() {
    translate([0, 0, dish_z(ring_r) - cav_depth + 0.4])
        cylinder(h = cup_h, d1 = cup_base_d, d2 = cup_rim_d);
}
module cups() {
    for (i = [0 : n_wells - 1])
        rotate([0, 0, i * 360 / n_wells]) translate([ring_r, 0, 0]) cup_mock();
}

module bowl() { difference() { bowl_solid(); dish_cut(); cavities(); brand_mark(); } }

if      (part == "bowl")    bowl();
else if (part == "cavity")  cavities();      // check a cutter's own extents alone
else if (part == "mark")    brand_mark();
else if (part == "preview") { color("#E8DFD2") bowl(); color("#C0392B", 0.5) cups(); }
