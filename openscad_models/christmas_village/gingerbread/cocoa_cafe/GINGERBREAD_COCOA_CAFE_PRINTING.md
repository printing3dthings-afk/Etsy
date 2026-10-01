# Gingerbread Cocoa Café — printing notes

Building #4 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Cocoa-mug tower café"), it is **a round tower shaped like a hot-cocoa mug,
with a small gingerbread café standing out of its front**:

- a white mug:
  - red stripes round its foot and under its rim, COCOA in red across its
    front;
  - two rows of arched windows drawn in red on the white, with their bars;
  - a chunky red handle on its side;
- in the mug, cocoa to just under the rim, a tall swirl of whipped cream,
  four toasted marshmallows floating round it, and a red-and-white
  candy-cane stirrer leaning out;
- out of the mug's front, a square gingerbread café under a chocolate gable
  of scallop tiles and icing:
  - a wide arched display window under a red-and-white striped awning;
  - a chocolate-bar door, both framed in piped icing beads, and a window in
    each side;
  - icing piped down its front corners and dripping off its eaves and rake;
  - a piped white heart in its gable;
- a soft snow base with a rounded edge, drifts and three peppermints.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The café opens into the mug through its own room, so one light
fills both. The mug's windows are drawn on, not cut: the mug's wall is
1.68 mm of white and glows all round between its red lines, and the café's
windows are glazed. It measures 68.7 × 77.5 × 97.4 mm, snow base and cream
included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_cocoa_cafe.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the café's walls, the marshmallows | gingerbread `#C68642` |
| roof | the cocoa, the café's roof and its tiles, the door | chocolate `#5A3825` |
| trim | snow base and drifts, the mug, the whipped cream, the stirrer, the awning's white, the café's frames with their beads, panes and bars, corner beads, eaves, rake and roof icing, the heart, the peppermints' white | icing white `#F7F3EE` |
| accent | the mug's stripes, COCOA, its windows' outlines and bars, the handle, the awning's and stirrer's stripes, the peppermints' stripes | candy red `#D7263D` |

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **4 h 33 m** | **35.3 cm³, about 44 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 44 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the mug and the café;
- a 46.6 mm circle round the mug's centre is clear from the table to
  50.3 mm;
- a 38 mm tealight has room to 56.5 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of headroom).
The mug's radius (25.5 mm) was set for it: the 46.6 mm circle stands 0.5 mm
inside the wall, and the room keeps its full width to 49.6 mm before it closes
in at 55° under the cream.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.59 mm, median 4.56 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 20.05 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts: closed, and every edge shared by
  exactly two faces.
- CHECKS_PENDING

## What it took to print without supports

The café is the sweet shop's shop and the mug its bottom tier, each with every
fix in their notes. These were this building's own, each found on the gate's
slicer or a section through the model:

- **Everything on the mug is flush.** Stripes, COCOA and the window outlines
  are red pressed into the white wall to its own face, so nothing round the
  mug has an underside to print over.
- **The handle's foot starts inside the wall** and meets the mug's face 2 mm
  up. Begun at a point on the face, its first layers printed as a loose
  island, and the slicer propped them. Its outside and its hole both rise at
  more than 50°.
- **The cocoa stops at the café's room as well as the mug's.** Cut by the
  mug's room only, a 0.3 mm ring of it inside the wall hung flat over the
  café's opening into the mug.
- **The cream is a soft-serve swirl whose coils lean out no more than 30°**,
  piled high enough to cover the room's cone everywhere.
- **The stirrer leans out from 18° to 40°**, the most a rod can lean and
  print over nothing (the candy cane chapel's crook).
- **The awning is a wedge whose underside rises at 50° from the wall.**

## Honest weak points

- **The stirrer is the part to handle with care.** It is a 3.8 mm rod
  leaning out of the cream.
- **Raised details have sloped undersides.** That is how they print without
  supports. The café's frames, drips and the awning read as wedges from
  below.
- **The mug's windows are drawn, not open:** the light comes through the
  white wall, not through panes.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
