# Victorian Cottage — printing notes

Building #1 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`), redrawn round (Scott, 2026-09-30:
"Christmas village keeps a rounder shape … Yes redo the cottages round too").
Picked from four layouts, it is **a round brick drum under a cone of slate,
with a small gable over the door**:

- a round brick drum, cut flat for 16 mm across the front;
- a steep 58° slate cone, snow on its crown, icicles under its eave;
- the flat front rising into a gable with a white scalloped bargeboard, a
  finial and a gothic lancet window;
- a slate round-arched door with an evergreen wreath, and an evergreen garland
  over it;
- four segmental sash windows with keystones round the drum, evergreen window
  boxes under the two at the front;
- a tall chimney with two pots at the back;
- a soft snow base with a rounded edge, drifts and a curved step.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 67.0 × 67.0 × 95.4 mm, snow base and chimney pots
included.

The square cottage it replaced passed every check too. It is in
`data/trash/` (`20260930-002`) and at commit a8eea51.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_cottage.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the brick drum and gable, the chimney and pots, the wreath's and garland's bows, the step | brick red `#A8483A` |
| roof | the slate cone and the gable's roof, the bargeboard and finial, the door | slate `#2E3440` |
| trim | snow base and drifts, the eave's soffit, snow on the roofs, icicles, every pane, the window and door frames, keystones and bars | white `#F4F1EA` |
| accent | the wreath, the garland, the window boxes | evergreen `#2F6B45` |

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
| **single colour** | **4 h 31 m** | **32.5 cm³, about 40 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 40 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the drum: 50.6 × 49.4 mm, flat at the front;
- a 46.6 mm circle round the centre is clear from the table to 47.2 mm;
- a 38 mm tealight has room to 54.1 mm.

**The 46 mm circle is 2.8 mm under the series rule** (50 mm of headroom). The
ceiling is a 58° cone from a 44 mm eave, so it closes in over the circle's
edge. A 38 mm tealight has 54 mm, room for a 45 mm-tall generic one.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 4.15 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 14.80 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts: closed. The body and the accent have
  every edge shared by exactly two faces. The roof and the trim carry 20 and
  80 edges shared by more than two, and two zero-area triangles each, all in
  the few square millimetres where the gable's ridge dives into the cone and
  its snow, roof and the cone meet. The merged model is watertight there and
  slices clean; Bambu Studio may offer to repair those two parts when the 3MF
  is opened.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): **0 flags**. 11.3 mm³ of 42,479 mm³ is not printed; 0.8 mm³ printed
  that was not modelled; 0.4 mm³ printed in the next colour. The largest miss
  is one layer at the tip of the gable's ridge (1.2 mm³, 0.42 mm deep).
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The chimney
  pots score 1.8 and the cone's tip 2.0, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base, in the band between the drum's opening and the base's edge. It is the
  same mark as the other buildings, mirrored so it reads OBC with the cottage
  turned over, front toward you.

## What it took to print without supports

The machinery is the round shop-house's, with every fix in its notes. These
were this building's own, each found on the gate's slicer or the mesh check:

- **The gable window's bar stands on the glass.** Made with the frame, it was
  cut away with the window's opening, all but a 0.6 mm stub above the point.
  The stub floated, and the slicer stood a column of support under it from the
  snow. That column was most of the 4,395 support moves the first round slice
  needed.
- **The gable window is sized to clear the bargeboard** (4 mm wide). Larger,
  its point rose into the bargeboard's scallops, which hung inside it in front
  of the glass.
- **The gable's inside is narrower and steeper than its roof** (70°, 3.2 mm
  either side of centre), like the shop-house's dormer, so where it meets the
  cone's ceiling it rises steeply enough to print.
- **No solids touch flush inside a part.** Three places left edges shared by
  more than two faces, which the slicer repairs but Bambu Studio flags:
  - the slate's colour cut shared its corner edge with the roof at the eave's
    foot: a zero-width ring of 236 edges;
  - the gable's snow started level with its roof's back face;
  - the window boxes' ends fell where two of their strips overlap.

## Honest weak points

- **The tealight headroom is short of the series rule**, above.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, keystones, window boxes and the garland read as wedges
  from below.
- **The wreath's and garland's bows are brick**, the wall's colour, so they
  read by their relief only. A fifth colour would have been needed for red.
- **Icicles hang against the wall, not in the air.**
- **The gable's snow shows as a small white block behind the finial**, where
  it runs back into the cone.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
