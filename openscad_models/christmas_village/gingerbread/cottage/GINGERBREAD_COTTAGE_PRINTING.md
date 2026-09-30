# Gingerbread Cottage — printing notes

Building #1 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`). The cottage from the style study, rebuilt to
print:

- smooth gingerbread walls, with piped icing beads down every corner;
- beads round every window and the door;
- a steep 58° roof of chocolate scallop tiles;
- icing on the ridge, dripping off the eaves and down both rakes;
- five red gumdrops along the ridge;
- a chocolate-bar door between two striped candy canes;
- a peppermint round window in each gable;
- two peppermint candies lying on the snow base.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 79.0 × 78.0 × 110.5 mm, snow base and gumdrops included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print. On the smooth walls of the
colour renders, faint streaks fan out from the windows. They come from the
renderer's triangles, which tilt by up to 0.03 mm near the rounded corners.
The printer can't show that, and the as-printed renders don't have them.

**Print this:** `gingerbread_cottage.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | gingerbread walls | gingerbread `#C68642` |
| roof | chocolate roof and scallop tiles, the chocolate-bar door | chocolate `#5A3825` |
| trim | the icing: snow base, corner beads, window and door frames and their beads, panes and bars, eave soffit and drips, rake bands and drips, icing on the roof, the white of the canes and peppermints | icing white `#F7F3EE` |
| accent | gumdrops, cane stripes, peppermint stripes | candy red `#D7263D` |

**Every window is glazed** with a 1.48 mm pane at the back of the opening,
and the window bars stand on the pane. The tealight glows through the panes.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **6 h 54 m** | **52.5 cm³, about 65 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 65 g of model **+ purge** |

## The tealight

Measured on the exported model:

- 60.6 × 54.6 mm clear inside, from the table up to the 52 mm eave;
- a 46 mm circle round the centre is clear from the table to above 62 mm.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 3.35 mm, against the 1.2 mm floor;
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
  layer): 25.4 mm³ of 70,102 mm³ not printed, and **0 flags**. The largest
  misses are one-layer slivers, under 0.4 mm deep, along one row of the
  chocolate tiles on the right slope.
- `fragility`: nothing slender at all. 0 high, 0 watch, 0 slender runs.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base. It is the same mark as the Victorian cottage, mirrored so it reads OBC
  with the cottage turned over, front toward you.

## What it took to print without supports

It inherited every fix the Victorian cottage needed (see its notes). Those
include the rake band's drips, which fail the same way as the Victorian's
scallops. Three more were its own:

- **The gumdrops stop at the ceiling.** Their anchoring cones reached 3 mm
  down through the roof into the lantern, and hung there over the room.
- **The door's groove runs out through the top of the arch.** Stopped just
  under it, the groove's end was a small flat ceiling.
- **Two outlines touched themselves at a single point**: the corner-bead
  columns (circles cut at the axis) and the peppermints' four wedges. That
  makes a surface OpenSCAD can't close, and it silently drops the whole
  object. The bead columns are now drawn as one outline, and the wedges are
  joined by a small dot at the centre.

## Honest weak points

- **Raised icing has sloped undersides.** That is how it prints without
  supports. From below, the beads and drips read as wedges, and their
  bottom edges look softer than their tops.
- **The scallop tiles read as rows of small bumps** from a distance rather
  than crisp scallops. Each tile's rounded edge stands 1.3 mm out.
- **The gumdrops read as teardrops from the side.** Each one needs a foot
  running down both slopes of the ridge, under the roof, so nothing overhangs.
  Seen along the ridge they are round; from the side they look taller than a
  real gumdrop. A flatter one would hang off the slopes and need support.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
