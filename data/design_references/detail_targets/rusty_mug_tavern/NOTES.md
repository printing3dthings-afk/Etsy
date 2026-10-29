# Detail target: "The Rusty Mug" tavern (Scott, 2026-10-29)

Scott: "Example of the very high detail we need to work towards."
`reference.png` is the image as he sent it (814 × 1086). Its source and how it
was made (printer, resin or FDM, or a render) are not known. Nothing here
assumes either.

## What it does that our buildings do not yet

Measured against our current Christmas Village and Haunted Town models:

- **Every stone is its own shape.** Irregular blocks of different sizes, each
  with softened, chipped edges, set in a random bond; the chimneys too. Ours
  are regular courses with straight joints.
- **Every roof tile is its own piece.** Staggered rows, ragged lower edges,
  slight tilt from tile to tile, a ridge of capping tiles. Ours are even rows
  with a straight groove between them.
- **Timber reads as wood.** Half-timbering with braces, wood grain along each
  member, posts with chamfered ends. We have no timber framing.
- **Signage is a feature, not a label.** A raised octagonal board with a
  border, serif letters standing proud.
- **The scene comes with it.** Tables, benches, barrels with hoops, crates,
  tankards and bottles, a lantern, flagstone steps and a cobbled base, all in
  one print. Ours carry snow drifts.
- **Windows are many small panes**, with mullions, sills and lintels, some
  under arches of their own stones.
- **Nothing is perfectly straight.** The irregularity is what makes it read
  as hand-made at full size.

## What the print side says (from ../../../openscad_models/detail_calibration/DETAIL_STANDARD.md)

On the 0.4 mm nozzle, detail running up a face (joints between stones, wood
grain on posts, gaps between tiles) prints to ±0.01 mm. Level detail snaps
to the layer, so at 0.2 mm layers a level groove is 0.2 or 0.4, nothing between.
The finest items in the image (bottle necks, tankard handles, tile chips)
are below what a 0.4 mm nozzle can draw. They need either 0.08–0.12 mm layers
or a 0.2 mm nozzle; neither has been measured on a real print here yet.
