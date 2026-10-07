# Victorian Coaching Inn — printing notes

Building #4 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Long inn + carriage arch"), it is **a long two-storey inn with a pointed
carriage archway through its right end**. It is the widest building in the
village:

- a brick ground floor with white quoins at its corners:
  - six segmental windows with white frames, keystones and glazing bars;
  - a slate door with an evergreen wreath and a white bow, in a flush white
    frame, on a brick step;
  - a wall lantern with a white glass beside the archway;
- the carriage archway, a pointed arch right through the building, ringed
  front and back with white voussoirs and a keystone;
- a white plaster upper floor jettied out over the brick on a dark timber
  beam:
  - dark timbers inlaid flush in the plaster: a top plate, posts, and a tie
    beam, king post and struts in each gable;
  - fifteen casement windows with dark frames and bars, and a small evergreen
    wreath in each front one;
  - a brick-red INN sign over the door, its letters raised in white;
- a steep 55° slate roof, snow on its upper half, icicles under the long
  eaves, dark scalloped bargeboards and finials on both gables;
- two tall brick chimneys astride the ridge, each with two pots;
- a soft snow base with a rounded edge and drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The ground floor's room, left of the archway, opens into the upper
floor's, so one light fills both: it shows through the glazed ground-floor
windows and glows through the thin plaster between the timbers. It measures
97.0 × 69.0 × 111.4 mm, snow base and chimney pots included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_coaching_inn.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the brick ground floor and the archway's walls, the chimneys, the sign board, the step | brick red `#A8483A` |
| roof | the roof, the jetty beam, every timber, the upper windows' frames and bars, the bargeboards and finials, the door, the lantern | slate `#2E3440` |
| trim | snow base and drifts, quoins, the plaster upper floor, the eave soffit, icicles, snow on the roof, the ground windows' frames, keystones, bars and panes, the door frame and the wreath's bow, the archway's voussoirs, the lantern's glass, INN | white `#F4F1EA` |
| accent | the wreaths | evergreen `#2F6B45` |

**The ground floor's windows are glazed.** Each has its pane, and its bars
stand on the pane. The upper floor's casements are inlaid in the plaster.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **8 h 43 m** | **69.3 cm³, about 86 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 86 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the ground floor's room, left of the archway;
- a 46.6 mm circle round that room's centre is clear from the table to
  58.5 mm;
- a 38 mm tealight has room to 64.5 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom).

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 4.48 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 37.85 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts: closed, and every edge shared by
  exactly two faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer; re-run 2026-10-07 with the raised INN): 12.3 mm³ of 117,263 mm³ is
  not printed; 0.1 mm³ printed that was not modelled; 0.3 mm³ printed in
  another colour. **5 flags, the same as before, all cosmetic and none over
  0.07 mm³, none in the sign:**
  - the tips of the two gable finials (one layer each, 0.07 mm³);
  - a corner of the plaster where it meets the jetty beam (one layer,
    0.06 mm³);
  - the edges of the door's wreath (0.2 mm wide, 0.04 mm³ each side).
- `fragility` (re-run 2026-10-07): nothing slender enough to snap. 0 high,
  0 watch. The gable finials score 3.4, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the snow base in front of
  the door, the same mark as the other buildings, mirrored so it reads OBC
  with the inn turned over, front toward you.

## What it took to print without supports

The block is the toy shop's (`../toy_shop`), turned to stand long side to
the street, with every fix in its notes. These were this building's own, each
found on the gate's slicer, its thin-wall scan or a section through the model:

- **The upper floor's corners are all but square** (0.3 mm), the jetty beam's
  top with them. Rounded like the brick's, the eave flare ran on past them
  over air at all four corners, and the slicer propped each from the base.
- **The door frame is a flush white band at the bricks' face, and the leaf is
  flush with it.** Raised, the frame's head stood out over the recessed leaf
  and the slicer propped the whole doorway from the base. The door's panels
  sit low, under the wreath; above, the wreath left them slivers.
- **INN is raised 0.84 mm, not inlaid** (2026-10-07). Inlaid flush, it was
  colour alone and would vanish on a one-colour or painted print, as the
  haunted post office's first print showed. The letters are built as a climb
  in 0.2 mm steps, so only their undersides slope.
- **No icicle over the INN sign.** One's tip hung 0.2 mm over the sign's top.
- **On the gables the jetty beam stands out 0.8 mm**, over the bricks' bumps.
  Flush with the plaster there, the last course's bumps rose past it as a
  0.16 mm sliver along both gables: 92 of the thin-wall scan's spans.
- **The lantern's bars are 1.3 mm, its hook 1.3 mm,** and the chimney pots
  have 1.3 mm walls round their flues and stand apart. At 0.7 and 1.0 mm
  they were thin walls; the wider pots touching made open edges.
- **The archway's voussoirs reach into the passage, which cuts them back.**
  Ending exactly on the passage's line, their back face met the brick jamb in
  52 edges shared by more than two faces.
- **The maker's mark sits 1.5 mm further in.** By the base's edge, the wall
  outside it was 0.66 mm.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. Window frames, keystones, voussoirs, the sign and the lantern
  read as wedges from below.
- **The wreaths in the upper windows are small** (4 mm across).
- **Icicles hang against the wall, not in the air.**
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
