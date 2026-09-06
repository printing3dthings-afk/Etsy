# Six-well sauce cup tray — printing notes

A flower-form tray that holds **six standard 2oz plastic portion cups** in a
ring. One part, no supports, no hardware.

| File | What it is |
|---|---|
| `sauce_tray` | the tray, sized for **2oz** cups (the standard dipping cup) |
| `sauce_tray_1oz` | same design, sized for **1oz** cups — smaller and much faster |

Each ships as both `.3mf` (use these — real mm units, a fraction of the size)
and `.stl`.

## It holds the CUPS. It is not a sauce dish.

This is a design constraint, not a disclaimer. FDM layer lines are porous and
trap food residue that washing does not clear, and this shop's P1S runs a
**stock brass nozzle**, which sheds trace lead into every print. A tray a
customer pours sauce directly into is not a claim we can defend, so the design
does not invite it — every well is a socket for a disposable cup.

It is also what the market already does: reviewing the real popular designs in
this category, nearly all of them hold a tub, a packet, or a cup rather than
the sauce itself.

## The one dimension every brand agrees on

Two suppliers' published dimensions, measured against each other rather than
assumed:

| | top dia | bottom dia | height |
|---|---|---|---|
| Choice 2oz | 60.3mm | 44.5mm | 28.6mm |
| Dart Solo 200PC 2oz | 60.3mm | **46.0mm** | **30.2mm** |

**The top diameter is identical; the other two are not.** So each well grips
the cup's *taper* at a fixed **47mm bore** — a diameter below every brand's rim
and above every brand's base, so any brand wedges. Only the seat depth changes:

| | seats this far below its own rim | base ends up at | proud of the tray |
|---|---|---|---|
| Choice | 24.07mm | z = 1.47mm | 19.2mm |
| Dart | 28.09mm | z = 3.89mm | 21.6mm |

Both clear the table with the cup hanging free in the through-bore, and both
stand well proud so you can pinch and lift them. The bore is open all the way
through, so a stuck cup pushes out from underneath.

## Print settings
- **PLA or PETG**, 0.2mm layers, 3 walls, 15% gyroid.
- **No supports.** Measured on the exported mesh in print orientation: **0.00%
  of downward-facing area is past 40°**, worst case 30°. The wells are
  countersinks — a hole that widens as it rises is self-supporting.
- Prints flat on its own underside. Full-area bed contact, no brim needed.
- Smooth PEI for PLA, textured PEI for PETG.

## Real print cost — sliced, not estimated

| | time | filament | cost @ $20/kg |
|---|---|---|---|
| 2oz tray — 208.0 × 184.6 × 14.0mm | **7h 34m** | 78.4 g | $1.57 |
| 1oz tray — 158.4 × 140.6 × 14.0mm | **4h 58m** | 52.0 g | $1.04 |

**Filament is nearly free; printer time is the entire cost.** At 7.5 hours the
2oz tray is well past the ~4h-per-sellable-unit ceiling this shop designs
toward — six 60mm cups in a ring is inherently a 200mm object, and on a tray
that size the cost is layer *area*, not volume. The 1oz tray is 58% of the
footprint and lands at 4h 57m, within reach of that ceiling.

Read that as a real business choice, not a defect: the 2oz cup is the standard
dipping size and the better product, and it costs roughly one printer-day per
unit. The 1oz gets close to two a day. Both are the same design.

## Verified before shipping — on the real exported mesh, not by eye
- Watertight, **1 connected component**, sits flat at z=0.
- **0.00% of downward area past 40°** (and past 55°); worst **0.1°** — the
  skirt is effectively vertical, so there is nothing for the printer to bridge.
- Cup seating verified in closed form for both brands, then against the mesh.
- **Adjacent cup rims clear by 2.70mm.** For six wells in a ring, adjacent
  centres are exactly `ring_r` apart — see the bug below.
- **Maker's mark 31.49mm wide** = 39.9% of the 79mm centre pad, inside the
  35–45% standing target. Measured by isolating the recess floor plane, not a
  z-range — the bores share that z band and poison a range filter.
- Material at the thinnest point between a petal valley and the nearest well:
  **9.5mm**.

## Real bugs caught during the build, for whoever touches this next
- **The cup RIMS collided and nothing flagged it.** Well spacing was sized
  against the 47mm bores, but the rims are 60.3mm and flare out *above* the
  tray where no geometry constrains them — an 8.3mm overlap. Six cups that
  could not physically be inserted, in a model that rendered clean, was
  watertight, and passed every mesh check. Caught only by rendering the cups
  themselves into the scene. **If a part holds an object, model the object.**
- **Raised texture destroyed the silhouette.** Technique 52 prescribes raising
  relief outward rather than carving in. Following it here put 48 proud ridges
  on the outline and turned a clean six-petal flower into a ragged sawtooth —
  a three-way plan-view comparison is what showed it. The flutes are now cut
  *inward, below the rim*, so the plan outline stays crisp and the rim
  overhangs the fluted band as a deliberate shadow line. A published rule is
  still a rule for the case it was measured on.
- **The tray was 16.1mm tall when the source said 14.** `z_samples` — the list
  of heights the body is lofted through — was a hardcoded literal ending at
  17.0. Changing `plate_h` silently did nothing; the dish cut hid it in every
  render. Only the exported mesh's bounding box caught it. It is derived from
  `plate_h` now, which is what makes the 1oz variant possible at all.
- **The fluted skirt was invisible and got cut.** Vertical flutes were carved
  into the skirt for surface interest. The first studio render showed them
  washing out completely under soft light while looking fine in the flat CAD
  preview — Technique 36's exact warning — so they were deepened 2.6 → 3.4mm
  and re-rendered with deliberately raking light. They were **still** invisible,
  and the cause was a decision made earlier in this same build: the rim sits at
  the full petal radius and OVERHANGS the fluted band, so it only shows from
  near floor level. On a tray that lives on a table, nobody ever sees it. Cut to
  zero (still parameterised — on a taller skirt without that overhang it would
  read). A feature no one can see is not texture, it is print time.
- **A flat slab reads as a coaster, not a tray.** The top face is a shallow
  paraboloid instead — which also makes the rim scallop for free, rising at
  each petal and dipping at each notch, with no extra geometry.

## Regenerating a variant
Every dimension is a named parameter and `z_samples` is derived, so a new cup
size is a set of `-D` overrides, not a new file. The 1oz variant is exactly:

```
-D cup_rim_d=44.5 -D cup_base_d=31.75 -D cup_h=31.75 \
-D well_bore_d=34 -D well_mouth_d=40 -D ring_r=48 \
-D base_r=67 -D petal_amp=12.2 -D bore_top=7 \
-D n_flutes=28 -D flute_depth=2.0
```

`part=` also accepts `preview` (tray with cup mock-ups), `cutters` and `mark`
for checking a cutter's own extents in isolation.
