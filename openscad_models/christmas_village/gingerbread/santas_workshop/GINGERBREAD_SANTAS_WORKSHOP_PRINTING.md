# Gingerbread Santa's Workshop — printing notes

Building #5 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Roundhouse workshop"), it is **a round gingerbread workshop under a steep
chocolate cone, with a square loading wing and a peppermint chimney**:

- a tall gingerbread drum with arched windows on two levels framed in icing,
  and a frosted ledge round its top with icing dripping down the wall;
- a steep chocolate cone of shingle courses over it:
  - red and white gumdrops in turn all round its foot;
  - a cap of icing on its point, with a big red gumdrop on top;
- out of its front, a square gingerbread loading wing under a chocolate
  gable of scallop tiles and icing:
  - big chocolate-bar double doors, scored into squares, framed in piped
    icing beads;
  - a round window in its gable, its frame striped like a peppermint;
  - gumdrops along its ridge, icing down its front corners and dripping off
    its eaves and rake, a window in each side;
- up the drum's back, a tall round white chimney with two red stripes
  winding up it like a peppermint stick;
- a soft snow base with a rounded edge, drifts and three peppermints.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The wing opens into the drum through its own room, so one light
fills both. It measures 67.0 × 80.9 × 94.1 mm, snow base and gumdrop
included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_santas_workshop.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the drum, the wing's walls | gingerbread `#C68642` |
| roof | the cone and its shingles, the wing's roof and its tiles, the doors | chocolate `#5A3825` |
| trim | snow base and drifts, the frosting and its drips, the cone's cap, every frame with its beads, panes and bars, the wing's corner beads, eaves, rake and roof icing, the chimney, the white gumdrops, the peppermints' white | icing white `#F7F3EE` |
| accent | the red gumdrops, the chimney's and the porthole's stripes, the peppermints' stripes | candy red `#D7263D` |

**Every window is glazed.** Each has its pane, and its bars stand on the
pane.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **5 h 32 m** | **38.1 cm³, about 47 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 47 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the drum and the wing;
- a 46.6 mm circle round the drum's centre is clear from the table to
  50.6 mm;
- a 38 mm tealight has room to 56.8 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom). The drum's room keeps its full width to 49.9 mm, then closes in
at 55° under the cone.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 4.28 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 21.16 cm² of bed contact;
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 13.3 mm³ of 53,281 mm³ is not printed; 0.1 mm³ printed that was
  not modelled; 0.2 mm³ printed in another colour. **0 flags.** The largest
  losses are 0.2 mm slivers of gingerbread where the chimney meets the drum,
  and the edges of the stripes there (each under 0.2 mm³).
- `fragility`: nothing slender enough to snap. 0 high, 0 watch, no slender
  runs.
- **OBC maker's mark:** engraved 0.8 mm deep under the snow base in front of
  the wing's doors, the same mark as the other buildings, mirrored so it
  reads OBC with the workshop turned over, front toward you.

## What it took to print without supports

The drum is the sweet shop's bottom tier and the wing its shop (the candy cane
chapel's nave), each with every fix in their notes. These were this
building's own, each found on the gate's slicer, its mesh checks, a section
through the model or the renders:

- **The gumdrops are domes on a cone at 50°** that sinks into whatever they
  stand on, so none has a flat underside over air. **The ones round the
  eave sit over the wall.** At 0.3 mm out, each one's point hung under the
  frosting's edge and the slicer propped all 22. They also stand 0.15 mm
  down in the frosting: standing exactly on its top, each met it in a ring of
  edges shared by more than two faces.
- **The chimney's crown flares out at 58°.** At 45° the slicer propped it.
- **The chimney's stripes are drawn as ring sectors clear of its axis.**
  Drawn as triangles from the axis, the twist made a broken mesh that the
  modeller dropped without stopping, and the chimney came out plain white.
  **They are cut back to the room:** the chimney sinks 0.33 mm past the drum's
  inner wall, and there the stripes hung in the room as winding slivers the
  slicer propped from the table (1,097 support moves).
- **The wing's walls run 0.3 mm up into its roof**, which takes them. Drawn on
  the same plane as the roof's underside, the two met in zero-thick sheets.
- **The icing cap and the shingles' undersides are 0.3 mm apart,** and the
  shingles' upper ends stand 0.3 mm over the cone: at 0.05 and face to face,
  they met in edges shared by more than two faces.
- **The wing is 32 mm wide,** so its ridge stays under the drum's frosting.

## Honest weak points

- **The chimney is the part to handle with care.** It is a 9.2 mm column
  standing 30 mm clear of the cone.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, drips and the frosting's edges read as wedges from
  below.
- **The cone is solid chocolate over the room's ceiling**, so the light comes
  out through the windows, not the roof.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
