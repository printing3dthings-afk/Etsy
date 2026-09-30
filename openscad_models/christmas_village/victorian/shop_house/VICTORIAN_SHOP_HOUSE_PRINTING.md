# Victorian Shop-House — printing notes

The Dickens Victorian village's first building with "more shape" (Scott,
2026-09-30, picked from four shapes against the reference photos in
`../../references/`). It is a two-storey shop:

- a brick shop floor with a bay shop window, a panelled door under a
  fanlight, and a white-framed sash window;
- a white plaster upper storey in dark timber framing. It juts 4 mm out over
  the street, on a cove and four brackets;
- diamond-leaded casement windows, with evergreen window boxes under the two
  at the front;
- a steep 58° front gable with a dark scalloped bargeboard, a finial at each
  end, and a king post with V-struts round a small attic window;
- a slate roof with snow along the ridge;
- on the right slope, a gabled dormer and a tall stepped brick chimney with
  two pots, giving the roof a second height;
- a wreath on the door and a step in front of it, on a snow base with drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 71.0 × 71.0 × 129.6 mm, snow base and chimney pots
included. It is 14 mm taller than the first cottage.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_shop_house.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the brick shop floor, the bay's brick stall riser, the chimney and pots, the step | brick red `#A8483A` |
| roof | slate roof and dormer roof, all the dark timber (framing, the jetty's cove and brackets, window frames and diamond leading, bargeboards, finials, the dormer's verge board), the door | slate `#2E3440` |
| trim | snow base and drifts, the plaster upper storey and dormer walls, the flares under the eaves, snow on both roofs, every pane, the shop floor's window frames, keystones and bars, the door frame, transom and fanlight | white `#F4F1EA` |
| accent | the bay window's frame and bars, the wreath, the window boxes | evergreen `#2F6B45` |

**Every window is glazed.** Each has a 1.48 mm pane (1.68 mm upstairs and in the bay), and
its bars or leading stand on the pane. The tealight glows through the panes.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **8 h 6 m** | **58.9 cm³, about 73 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 73 g of model **+ purge** |

## The tealight

Measured on the exported model:

- 52.6 × 46.6 mm clear inside the shop floor, from the table up to 38 mm,
  and wider above that;
- a 46.6 mm circle round the centre is clear from the table to about 74 mm.

The series rule is at least 46 mm across and at least 50 mm of headroom.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.32 mm, median 3.25 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 20.03 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts:
  - closed, every edge shared by exactly two faces;
  - **4 zero-area triangles**, where the cottages had none: 1 in the roof,
    1 in the trim and 2 in the accent. Each is a needle along an edge where
    two features' edges meet, and slicers ignore them.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 20.0 mm³ of 73,213 mm³ not printed, and 8 flags of about 0.04 mm³
  each. Each flag is the front 0.5 mm of a cusp between two bargeboard
  scallops, 0.2 mm wide, four on each gable. That is under one extrusion
  wide, so the printer rounds it off; no scallop is lost. The largest
  unflagged misses are the wavy edges of the dormer's snow, under 0.5 mm deep.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The finials
  score 3.1, against a watch level of 4, the same as the cottage's.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base. It is the same mark as the cottages, mirrored so it reads OBC with
  the model turned over, front toward you.

## What it took to print without supports

The first full slice needed 13,057 support moves. Each fix below was found on
the gate's own slicer:

- **The diamond leading runs 38° from vertical**, so the diamonds are taller
  than they are wide. At 55° every bar needed support, because the slicer
  supports anything flatter than 45° from horizontal.
- **The upstairs panes sit flush with the wall's face.** Set back 0.2 mm like
  the shop windows' panes, each square window head was a flat ledge, and it
  shut in small air pockets.
- **The timbers keep level tops.** Drawn like the frames, every beam's top
  sloped up to a 0.18 mm knife edge. With level tops, the gable struts that
  fell from the king post to the tie beam at 34° hung in the air, so the
  struts now rise from the post's foot toward the rafters at 58°.
- **The dormer has flares under its eaves**, as the main roof does. Its roof
  slab continues the flare's slope to the tip. The overhang in front of its
  face, and its verge board, have undersides that slope up as they come
  forward.
- **The cove and brackets are cut by the rooms.** Where the bay opens the
  shop wall, the cove's buried foot hung in the air.
- **The eave is 4 mm higher than first drawn.** At 66 mm, the flare under the
  eave came down over the side windows' heads.
- **The passage from the shop into the bay goes all the way through.** Drawn
  1 mm short, the bay was sealed off as a hollow inside the wall.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. The frames, beams, window boxes and brackets read as wedges from
  below.
- **The jetty is 4 mm.** From the side and three-quarter views it reads as an
  overhang. Straight on, it reads as a dark band between the brick and the
  plaster.
- **The dormer's face is mostly dark frame and verge board.** Its white
  gable shows as a narrow band round the window.
- **The shop floor's windows are white on white:** frame, bars and pane are
  one colour. They read by their relief, and they glow when lit.
- **It shares its bay window with the toy shop** planned as building #2 in
  `../../CHRISTMAS_VILLAGE.md`. The toy shop should get a different front
  when it is built.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
