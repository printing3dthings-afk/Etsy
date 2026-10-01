# Victorian Toy Shop — printing notes

Building #2 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`), and the first to join round and square (Scott,
2026-09-30: "I want to incorporate round and square together on some
buildings … Do all different shapes and stories of the buildings"). Picked
from four layouts, it is **a square two-storey brick shop with a round tower
on its front corner**:

- a square brick shop under a steep 55° slate gable running side to side,
  white quoins at its corners and a white string course between the storeys;
- on the front, a canted evergreen bay shop window with TOYS on its fascia,
  under its own small slate roof;
- upstairs, segmental sash windows with keystones and evergreen window boxes;
  a gothic lancet in each gable, under a white scalloped bargeboard and finial;
- snow on the upper half of the roof, with a rounded ridge, and icicles under
  the eaves;
- on the front-left corner a round brick tower rising past the ridge to a
  flared slate cone with snow on its crown and a finial. The door, with an
  evergreen wreath, is at its foot, and it has windows on four levels;
- a tall chimney at the back right;
- a soft snow base with a rounded edge.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The tower opens into the shop through a pointed doorway, so one
light fills both. It measures 81.1 × 75.1 × 125.8 mm, snow base and finial included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_toy_shop.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the shop and the tower, the kneelers, the chimney, the wreath's bow, the step | brick red `#A8483A` |
| roof | the gable roof, the bay's roof, the cone and its finial, the door | slate `#2E3440` |
| trim | snow base and drifts, quoins, the string course and the tower's collars, eave soffits, icicles, bargeboards and gable finials, snow on the roofs, every window's frame, keystone, bars and pane, the door frame, the bay's glass, the letters TOYS | white `#F4F1EA` |
| accent | the bay shopfront, the window boxes, the wreath | evergreen `#2F6B45` |

**Every window is glazed.** Each has its pane, and its bars stand on the
pane. The tealight glows through the panes and the bay's glass.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **8 h 21 m** | **60.7 cm³, about 75 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 75 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the shop, and the tower opens into it;
- a 46.6 mm circle round the shop's centre is clear from the table to
  58.2 mm;
- a 38 mm tealight has room to 64.2 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom): the square shop has two full storeys of wall under its gable.

## Verified before shipping — on the real exported meshes

GATE_BLOCK

## What it took to print without supports

The block is the first square Victorian cottage's, the tower the gingerbread
turret house's, each with every fix in their notes. These were this
building's own, each found on the gate's slicer or a section through the
model:

- **Panes are never cut by the openings.** The white part held the frames
  and the panes together; cut by the window openings, every pane went and
  every frame's head was left as a bridge over nothing.
- **The tower's openings do not cut the white part either.** They trimmed
  the frames' heads into flat 1.2 mm ledges the slicer propped.
- **The bay is hollow to the shop.** Its room is cut through to the ceiling,
  its glass is exactly the wall's thickness, and only its front panes carry
  transoms: on the canted sides a transom's ends met the corner posts in
  edges shared by more than two faces.
- **The window boxes are cut by the bay's room.** A fin of one reached inside
  the bay and hung there, and the slicer stood 1,349 moves of support under
  it.
- **The cone's slate courses stop under the snow cap**, and the finial's
  point is blunted to 0.35 mm: sharp, its last 0.33 mm never printed.
- **The snow's ridge is rounded**, 2.2 mm across, and the white string
  course's upright face is 1.4 mm tall. Drawn to a point and 0.6 mm tall,
  they were the thinnest walls in the model.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, keystones, the string course, window boxes and the bay's
  fascia read as wedges from below.
- **The wreath's bow is brick**, the wall's colour, so it reads by its relief
  only.
- **Icicles hang against the wall, not in the air.**
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
