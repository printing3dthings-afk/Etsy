# Victorian Church — printing notes

Building #3 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Nave + square spire tower"), it is **a long brick nave, a square bell tower
with a tall spire, and a half-round apse**. It is the tallest building in the
village:

- a long brick nave under a steep 55° slate gable running front to back, with
  white quoins at its corners and a white sill course round it;
- three tall lancet windows down each side;
- on the front gable:
  - a round rose window with white tracery;
  - a pointed slate door, with an evergreen wreath and a white bow on it and
    an evergreen garland over it;
  - a lancet either side of the door;
- a white scalloped bargeboard and finial on both gables, snow on the upper
  half of the roof with a rounded ridge, and icicles under the side eaves;
- on the front-left corner, a square brick bell tower:
  - white bands at the sill course, at the nave's eave and a cornice at its
    top;
  - lancet windows on two levels, and a louvred belfry light in each face,
    above the nave's ridge;
  - a tall octagonal broach spire of slate in courses, topped by a white ball
    and cross;
- at the back, a half-round brick apse with three lancets, under a half cone
  of slate with snow on its crown;
- a soft snow base with a rounded edge and drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The tower opens into the nave through a pointed doorway, and the
apse through a pointed chancel arch, so one light fills all three. It
measures 79.3 × 92.6 × 164.4 mm, snow base and cross included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_church.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the nave, the tower and the apse, the kneelers, the garland's bows, the step | brick red `#A8483A` |
| roof | the nave's roof, the spire, the apse's cone, the door | slate `#2E3440` |
| trim | snow base and drifts, quoins, the sill course, the tower's bands and cornice, eave soffits, icicles, bargeboards and finials, snow on the roofs, every window's frame, tracery, bars and pane, the belfry's louvres, the door frame, the wreath's bow, the ball and cross | white `#F4F1EA` |
| accent | the wreath, the garland | evergreen `#2F6B45` |

**Every window is glazed.** Each has its pane, and its bars, tracery or
louvres stand on the pane. The tealight glows through the panes.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.
- It is 164 mm tall on a 79 × 93 mm base. The gate finds its centre of mass
  over the base, but the spire is its tallest, slimmest part: give the plate a
  clean first layer, and slow the last few millimetres if your printer shakes
  tall prints.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **9 h 02 m** | **65.3 cm³, about 81 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 81 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the nave, the tower and the apse;
- a 46.6 mm circle round the nave's centre is clear from the table to
  51.6 mm;
- a 38 mm tealight has room to 57.6 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom). The nave's eave line was set at 50 mm for it.

## Verified before shipping — on the real exported meshes

GATE_BLOCK

## What it took to print without supports

The nave is the toy shop's block, the apse its tower halved, each with every
fix in their notes. These were this building's own, each found on the gate's
slicer, its thin-wall scan or a section through the model:

- **No raised bar lies level.** A raised bar's underside slopes up 1.2 mm
  for every mm it stands out, so a level bar's front edge is its height less
  1.2:
  - the belfry's louvres are three slats 2.2 mm tall (five 1.2 mm slats came
    to a knife edge);
  - the rose window's tracery is turned 22.5°, so no bar is level, and is
    2.0 mm wide.
- **The ball under the cross has a cone under it at 57°.** A sphere's lower
  half hung out over the blunted tip, and at 45° the slicer still propped it.
  The ball, its cone and the cross each start inside the piece below, or they
  print as loose bodies.
- **The nave's walls run 0.3 mm into the tower.** Cut exactly at the tower's
  face, the two met in zero-width slivers up the tower's front-right edge.
- **The door:**
  - the leaf is the wall's depth only, so its foot doesn't hang over the
    open base;
  - its opening is cut out through the brick courses' bumps, which otherwise
    ran across the door as ridges;
  - the wreath's bow is white icing on the wreath; as brick, the door's
    opening cut it away;
  - the leaf runs 0.05 mm under the frame's inner edge, leaving no slot.
- **The tower's quoins were removed.** Skipped wherever a window or band
  was, they left isolated white squares.

## Honest weak points

- **It is tall and slim at the top.** The spire and cross are the parts to
  handle with care; fragility scores them below its watch level (above).
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, bands, the cornice and the tracery read as wedges from
  below.
- **The garland's bows are brick**, the wall's colour, so they read by their
  relief only.
- **Icicles hang against the wall, not in the air.**
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
