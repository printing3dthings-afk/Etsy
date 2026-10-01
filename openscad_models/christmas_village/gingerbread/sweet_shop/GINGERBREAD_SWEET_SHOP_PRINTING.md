# Gingerbread Sweet Shop — printing notes

Building #3 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Layer-cake tower shop"), it is **a three-tier layer cake with a small
gingerbread shop standing out of its front**:

- a tall gingerbread bottom tier with two rows of arched windows and a band
  of white cream round its middle, SWEETS in red letters across its front;
- a chocolate middle tier with six arched windows;
- a gingerbread top tier with four round portholes;
- a frosting dome on top, with a red cherry and its stem;
- on every ledge, white frosting dripping down the tier below, a rope of
  piped icing round the foot of the next tier, and red berries;
- out of the cake's front, a square gingerbread shop under a chocolate gable
  of scallop tiles and icing:
  - a wide arched display window and a chocolate-bar door, both framed in
    piped icing beads, and a window in each side;
  - icing piped down its front corners and dripping off its eaves and rake;
  - a red-and-white lollipop sign in its gable;
- a soft snow base with a rounded edge, drifts and three peppermints.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The shop opens into the cake through its own room, so one light
fills both. It measures 67.0 × 77.5 × 113.9 mm, snow base and cherry
included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_sweet_shop.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the bottom and top tiers, the shop's walls | gingerbread `#C68642` |
| roof | the middle tier, the shop's roof and its tiles, the door, the cherry's stem | chocolate `#5A3825` |
| trim | snow base and drifts, the frosting on every ledge and the dome, the drips, the piped ropes, the cream band, window and door frames with their beads, panes and bars, the shop's corner beads, eaves, rake and roof icing, the lollipop and its stick, the peppermints' white | icing white `#F7F3EE` |
| accent | SWEETS, the berries, the cherry, the lollipop's swirl, the peppermints' stripes | candy red `#D7263D` |

**Every window is glazed.** Each has its pane, and its bars stand on the
pane. The tealight glows through the panes.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **5 h 28 m** | **40.6 cm³, about 50 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 50 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the cake and the shop;
- a 46.6 mm circle round the cake's centre is clear from the table to
  51.2 mm;
- a 38 mm tealight has room to 57.4 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of headroom).
The bottom tier is 54 mm tall for it: its room keeps its full width to
50.5 mm before the ceiling narrows to the tier above.

## Verified before shipping — on the real exported meshes

GATE_BLOCK

## What it took to print without supports

The shop is the candy cane chapel's nave, the cake's windows are laid round it
in strips like the chapel tower's, each with every fix in their notes. These
were this building's own, each found on the gate's slicer, its thin-wall scan
or a section through the model:

- **The cake's room narrows at 55° under each ledge.** Each tier's room is
  its own width, so under each ledge the ceiling closes in to the tier above
  at a printable slope; the top tier's ceiling is a cone under the dome.
- **The shop's ceiling region is sized to the shop.** Copied from the chapel
  at its fixed 40 mm width, on this low shop the outline crossed itself and
  came out empty: the shop had no room and no side walls.
- **Frames on the cake are plain, wider (2.4 mm), with a sill, and stand out
  only 1.0 mm.** A raised level part's front edge is its height less 1.2 mm
  (its underside slopes), and beads laid round the cake in strips were cut
  into slivers.
- **SWEETS is inlaid flush, not raised.** Raised, every level stroke came to
  a knife edge.
- **The chocolate tier's frames cut their sloped holes into it**, like the
  gingerbread tiers'. Without them each pane's 0.2 mm recess had a flat head,
  and the slicer propped all six.
- **The upper tiers' frames start inside the frosting**, clear of its top
  face. A frame's foot just above the frosting was a shelf over a one-layer
  gap; one meeting it almost exactly left zero-size slivers.
- **The berries are sunk 0.3 mm into the frosting**, and the cherry is cut
  by the room. Standing on the frosting's top face, each berry printed loose;
  the cherry's foot reached under the room's ceiling.
- **The peppermints lie on the base's flat top**, not over its rounded edge,
  and the door leaf is the wall's depth only.

## Honest weak points

- **The cherry's stem is thin** (1.6 mm). Fragility scores it below its watch
  level (above), but it is the part to handle with care.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, drips and the frosting's edges read as wedges from below.
- **The bottom tier is the tallest**, so the cake is not graded like a real
  one: it has to be for the tealight.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
