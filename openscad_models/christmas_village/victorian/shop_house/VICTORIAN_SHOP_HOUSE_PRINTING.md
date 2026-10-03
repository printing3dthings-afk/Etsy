# Victorian Shop-House — printing notes

The Dickens Victorian village's first building with "more shape" (Scott,
2026-09-30, picked from four shapes against the reference photos in
`../../references/`). It was then redrawn with no square corners: "Make them
not do squared if possible". Scott picked all three of the building's boxy
shape, its sharp edges and its base. It is round:

- a round brick shop floor, a stadium in plan (two half-circles joined by
  14 mm straights). It has a green bow window at the front, four arched shop
  windows round the ends and back, and a panelled door with a wreath and a
  curved step;
- a white plaster upper storey in dark timber framing (posts, braces, a sill
  beam). It juts 3 mm out over the brick on a cove and brackets, all round;
- six diamond-leaded casement windows upstairs, with an evergreen window box
  under the front one;
- a round slate roof swept all the way round, with its eave curling out,
  icicles under it, and snow on the crown;
- a front dormer with a scalloped bargeboard and a finial, and a tall stepped
  brick chimney with two pots;
- a soft snow base with a rounded top edge and drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 83.0 × 69.0 × 121.6 mm, snow base and chimney pots
included.

The square version it replaced passed every check too. It is in
`data/trash/` (`20260930-001__victorian_shop_house.scad`) and at commit
16df111.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_shop_house.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the brick shop floor, the bow window's brick stall riser, the chimney and pots, the step | brick red `#A8483A` |
| roof | the slate roof and dormer roof, all the dark timber (sill beam, posts, braces, cove and brackets, window frames and leading), the bargeboard and finial, the door | slate `#2E3440` |
| trim | snow base and drifts, the plaster upper storey and dormer walls, the soffit under the eave's curl and the flares under the dormer's eaves, snow on both roofs, the icicles, every pane, the shop windows' frames, keystones and bars, the door frame, transom and fanlight | white `#F4F1EA` |
| accent | the bow window's frame and bars, the wreath, the window box | evergreen `#2F6B45` |

**Every window is glazed.** Each has its pane, and its bars or leading stand
on the pane. The tealight glows through the panes.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **6 h 41 m** | **49.9 cm³, about 62 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 62 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the shop floor: a stadium 60.6 × 46.6 mm;
- a 46.6 mm circle round the centre is clear from the table to 68 mm;
- a 38 mm tealight has room to 74 mm.

The series rule is at least 46 mm across and at least 50 mm of headroom.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.44 mm, median 4.05 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 23.00 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts: closed, every edge shared by
  exactly two faces.
  - Zero-area triangles: 61 in the roof, 3 in the trim, 3 in the accent,
    none in the body. Each is a needle where two features' edges meet, and
    slicers ignore them.
  - The body and the trim also carry 42 and 45 zero-volume specks where the
    parts were cut from each other. They have no volume to print.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): **0 flags**.
  - 12.3 mm³ of 72,462 mm³ is not printed; 0.7 mm³ printed that was not
    modelled; 0.6 mm³ printed in the next colour.
  - The largest misses are the wavy edges of the snow on the crown and the
    dormer, under 0.5 mm deep, and two green edges near the top of the bow window, under
    0.5 mm.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The dormer's
  finial scores 2.5, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base, in the band between the bow's opening and the base's edge. It is the
  same mark as the cottages, mirrored so it reads OBC with the model turned
  over, front toward you.

## What it took to print without supports

The first full slice of the round version needed 12,564 support moves, and
its walls failed the thickness check. Each fix below was found on the gate's
own slicer or its thickness rays:

- **The dormer's inside is narrower and steeper than its roof** (70°, 2.9 mm
  either side of centre). Pitched like the roof, its ridge crossed the main
  room's ceiling in two lines rising only 45.3°, and the slicer propped them
  from the floor. Now they rise 51.7°, and the roof over its ridge keeps
  1.42 mm.
- **The bargeboard is drawn as one lower edge**, the lowest of its scallops
  at each point. As circles on a straight edge, each scallop's underside hung
  over the next one down the slope. The undercut that slopes the board's
  underside only reaches the lowest surface in a column, so the upper
  scallops stayed flat, and 2,500 support moves stood on the roof to hold
  them. Its undercut is hinged 0.15 mm inside the dormer's face; hinged on
  it, the scallops' lowest points met the face along edges and left the
  model non-manifold there.
- **Everything laid round the wall is trimmed to the true curve.** Frames,
  posts, braces, the window box and the wreath are built from 1 mm flat
  strips, each tangent to the wall at its own point. Where two strips overlap,
  one front stands 0.008 mm proud of the other, and every joint left a step
  the thickness check read as a wall that thin.
- **The window and door holes are laid round the wall in strips too.** Cut
  flat, the backs of the holes stood 0.46 mm proud of the curved face at a
  window's sides. They left slivers of wall at the arch's springing hanging
  over the glass.
- **The upper wall's top runs 0.6 mm up into the roof.** Drawn to the
  ceiling line, it met the roof face to face and left slivers where the
  sweep's straights meet its round ends.
- **The dormer's ridge reaches into the main roof.** It stopped 0.07 mm
  short and left a sliver on the roof.

**The thickness check itself was corrected along the way.** On a round
building every frame's corner stands at an angle to the checker's rays. A ray
clipping a 90° corner near its tip read as a wall 0.0–0.3 mm thick: 226 of
the 279 thin readings were these clips. `tools/mesh_gate.py` now re-measures
such a span across its faces. Checked on 20 models, the only verdicts it
changed were this building's and the pleated fan's. The fan's hinge sleeves
are drawn exactly 1.2 mm and faceted, and now read 1.19 mm.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, beams, brackets and the wreath read as wedges from below.
- **The shop windows are white on white:** frame, bars and pane are one
  colour. They read by their relief, and they glow when lit.
- **The upper windows' leading is dark on a white pane**, 0.4 mm proud. It
  reads, but at 0.2 mm layers the diamonds are only a few layers of each
  colour across.
- **It shares its bay/bow window idea with the toy shop** planned as
  building #2 in `../../CHRISTMAS_VILLAGE.md`. The toy shop should get a
  different front when it is built.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
