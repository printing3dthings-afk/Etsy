# Gingerbread Turret House — printing notes

The Gingerbread village's first building with "more shape" (Scott,
2026-09-30, picked from four shapes against the reference photos in
`../../references/`), drawn with no square corners ("Make them not do squared
if possible"). It is round:

- a gingerbread house on a stadium plan (two half-circles joined by 18 mm
  straights) under a round-ended bun of a chocolate roof. The roof swoops out
  all the way round into a curl of white icing, with drips under it and icing
  and three gumdrops along the ridge;
- a round turret on the front-left that leans a little. Two icing collars go
  round it, and it has three arched windows. Its bell cone of chocolate tiles
  carries a red-and-white candy-cane spire that bends over at the top;
- a half-round porch on two peppermint-stick columns under a half bell of
  chocolate, sheltering a chocolate-bar door;
- six arched windows round the house, every one with an icing-bead frame;
- a soft snow base with a rounded edge, three drifts and two peppermints.

Three roofs at three heights, all one swooping profile. It is a hollow
lantern with an open base, lit from inside by a battery LED tealight. It
measures DIMS mm, snow base and spire included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_turret_house.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the house, turret and porch walls | gingerbread `#C68642` |
| roof | the three chocolate roofs and their scallop tiles, the door | chocolate `#5A3825` |
| trim | snow base and drifts, the curled icing eaves and drips, icing on the ridge, the turret's collars, window frames, panes and bars, the porch columns, the spire, the peppermints' white | icing white `#F7F3EE` |
| accent | gumdrops, the stripes on the columns and spire, the peppermints' stripes | candy red `#D7263D` |

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
| **single colour** | **COST_T** | **COST_F** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | COST_G of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the house;
- a 46.6 mm circle round the centre is clear from the table to 41.5 mm;
- a 38 mm tealight has room to 48.9 mm.

**This is under the series rule** (at least 46 mm across and 50 mm of
headroom). The ceiling slopes up from a 42 mm eave line, so a 46.6 mm circle
meets it early. Check the height of the tealight you use, flame included,
against 48.9 mm.

## Verified before shipping — on the real exported meshes

GATE_BLOCK

## Honest weak points

- **The tealight headroom is short of the series rule**, above.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, collars and drips read as wedges from below.
- **The turret leans 0.05 (about 3°).** It is meant to, but the lean puts its
  windows' frames at a slight angle to the layers.
- **The spire is a chain of spheres.** It prints, and fragility scores it
  below the watch level, but it is the part to handle with care.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
