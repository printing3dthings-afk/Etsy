# Victorian Cottage — printing notes

Building #1 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`). The cottage from the style study, rebuilt to
print:

- a brick house with white corner quoins;
- a steep 58° slate roof, its upper half under snow;
- a white scalloped bargeboard and a finial on both gables;
- segmental-arched sash windows with keystones and sills;
- gothic lancet windows in the gables;
- a black round-arched door with an evergreen wreath and a red bow;
- an evergreen garland over the door, and evergreen window boxes under the
  two front windows;
- icicles under the eaves;
- a chimney with two pots;
- all of it standing on a snow base with drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 79.0 × 78.0 × 115.6 mm, snow base and finials included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_cottage.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | brick walls, chimney and pots, the red bows on the wreath and garland | brick red `#A8483A` |
| roof | slate roof and courses, the front door | slate `#2E3440` |
| trim | snow base and drifts, quoins, bargeboards and finials, window and door frames, sills, keystones, panes and bars, the white soffit and icicles under the eaves, the snow on the roof | white `#F4F1EA` |
| accent | wreath, garland, window boxes | evergreen `#2F6B45` |

**Every window is glazed** with a 1.48 mm pane at the back of the opening,
and the window bars stand on the pane. This is the chapel's rule since its
first print, where bars left standing free snapped. The tealight glows
through the panes like frosted glass.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.** Every underside is
  designed for this orientation only.
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **7 h 52 m** | **58.5 cm³, about 73 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 73 g of model **+ purge** |

## The tealight

Measured on the exported model:

- 60.6 × 54.6 mm clear inside, from the table up to the 52 mm eave;
- a 46 mm circle round the centre is clear from the table to above 62 mm.

The series rule is ≥ 46 mm across and ≥ 50 mm of headroom. The base is open,
so the cottage lifts off to switch the light on and off.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.40 mm, median 3.37 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 21.96 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - closed;
  - every edge shared by exactly two faces;
  - 0 zero-area faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 13.9 mm³ of 76,383 mm³ not printed, and 4 flags. All four are the
  same 0.04 mm³ sliver, one either side of each gable's peak: the front 0.5 mm
  of the scallops beside the finial, 0.2 mm wide. It is under one extrusion
  wide, so the printer rounds it off; no scallop is lost.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The finials
  score 3.1, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base. It is the Haunted Town mark (Montserrat Black, size 4.6, letter
  spacing 1.16), mirrored so it reads OBC with the cottage turned over, front
  toward you.

## What it took to print without supports

The first full slice needed 34,524 support moves. Each fix below was found on
the gate's own slicer.

- **The bargeboard's scallops.** The chapel's coping gets its sloped
  underside by intersecting the board with a sheared copy of itself. With a
  scalloped edge that fails: each scallop's sheared copy rises into the
  plain band above it, and where they overlap the band's underside stays
  flat. That flat strip between scallops caused 29,000 of the moves. The
  board is now built the way every other raised detail is: run down to the
  table, then cut by the sheared copy.
- **The drifts stay on the base.** Where a drift ran past the edge of the
  snow base, its side hung over the table.
- **The door fills its arch.** The chapel's door stops just short of its
  pointed head. Here the arch is round, and its flat crown over that gap was
  an overhang the width of the door.
- **The garland's bows are raised from the wall.** Set on the garland's face,
  they hung over air where the garland's own underside falls away behind
  them.
- **The finials are sunk 2.8 mm into the coping**, so their corners don't
  stand over its slopes.
- **No brick joints under the bargeboards.** The board's foot would have
  bridged each slot.

## Honest weak points

- **The bargeboard is scalloped but not pierced.** The style study's
  diamond piercings went: their sloped edges left slivers of board 0.4 mm
  thick above every hole, under what the printer lays down reliably.
- **Raised details have sloped undersides.** That is how they print without
  supports. It means the frames, sills, window boxes and garland read as
  wedges from below, and their bottom edges look softer than their tops.
- **Icicles hang against the wall, not in the air.** Free-hanging icicles
  would each start printing in mid-air. These are raised on the brick under
  the eave.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
