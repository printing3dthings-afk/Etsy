# Victorian Santa's Workshop — printing notes

Building #6 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`), built before the clock tower. Scott asked on
2026-10-02 for "a Santa workshop … big windows with toys outlined on the
windows sunk in so it looks like they are inside." From two look studies
(`concepts/`) he picked a mix: the long workshop, one big window, the loading
doors with wreaths, the skylights and white scalloped bargeboards. It is **a
long one-storey brick workshop with one big round-arched toy window**:

- a brick front with white quoins:
  - the big window, its white glass set 3.5 mm deep in the wall behind a
    splayed brick reveal, in a raised white frame with a keystone and sill;
  - on the glass, drawn in dark lines: a rocking horse and a teddy on the
    floor, a shelf with a sailboat, a toy soldier and a jack-in-the-box, and a
    fanlight of rays over them;
  - arched slate loading doors, a wreath with a white bow on each leaf, white
    strap hinges, in a flush white frame with a keystone, on a brick step;
  - over the doors a slate sign, SANTA'S / WORKSHOP inlaid in white;
- three glazed windows in the back and one in each gable;
- a steep 55° slate roof:
  - three skylights in its front slope;
  - snow on its upper half, icicles under the long eaves;
  - white scalloped bargeboards and slate finials on both gables;
  - a tall brick chimney astride the ridge with two pots;
- a soft snow base with a rounded edge and drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The toys' lines run right through the white glass, so with the
light on they show dark against it, like toys standing inside the workshop.
It measures 99.0 × 69.0 × 121.4 mm, snow base and chimney pots included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_santas_workshop.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the walls and gables, the brick behind the big window, the chimney, the step | brick red `#A8483A` |
| roof | the roof, the skylights' frames, the finials, the doors, the sign board, the toys and fanlight on the glass | slate `#2E3440` |
| trim | snow base and drifts, quoins, the eave flare, icicles, snow on the roof, the bargeboards, every window's frame, keystone, sill and glass, the back windows' bars, the door frame, hinges and bows, the skylights' glass, the sign's letters | white `#F4F1EA` |
| accent | the two wreaths | evergreen `#2F6B45` |

**Every window is glazed.** The big window's toys are part of its glass; the
other windows have their bars on the glass.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **9 h 32 m** | **72.5 cm³, about 90 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 90 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the whole room;
- a 46.6 mm circle in the room's middle is clear from the table to 65.7 mm;
- a 38 mm tealight has room to 71.7 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom). The brick behind the big window stands 5 mm into the room from
the front wall, and the room is 56 mm deep so the circle still fits behind it.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 3.29 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 25.10 cm² of bed contact;
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 19.7 mm³ of 95,557 mm³ is not printed; 0.2 mm³ printed that was
  not modelled; 0.2 mm³ printed in another colour. **4 flags, all cosmetic
  and none over 0.07 mm³:**
  - the edges of the two wreaths (0.2 mm wide, 0.07 mm³ each);
  - the tips of the two gable finials (one layer each, 0.07 mm³).
- **The toys print as drawn.** Under 0.1 mm³ of the big window's glass and
  toys is lost in the slice, every piece of it under 0.1 mm wide; the sign's
  letters likewise.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The finials
  score 3.4, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the snow base in front of
  the doors, the same mark as the other buildings, mirrored so it reads OBC
  with the workshop turned over, front toward you.

## What it took to print without supports

The block is the coaching inn's (`../coaching_inn`), all brick and without
the jetty, with every fix in its notes. These were this building's own, each
found on the gate's slicer or its mesh checks:

- **The big window's opening splays outward.** One opening runs through the
  frame, the brick and the reveal. It is the arch at the glass, and its head
  rises 1.2 per 1 toward the frame's face over a level floor, so its lowest
  edge is the glass's, which holds each layer up. Two earlier versions were
  propped from the window's floor:
  - a head rising inward left the arch at the frame's face as the lowest
    edge: the top of a round arch, near level across 20 mm, with nothing
    behind it;
  - a frame opening rising outward over a reveal rising inward met it in a
    near-level downward crease round the arch's head.
- **That opening is one hull, and the brick, frame and keystone are all cut
  by the same one.** As a straight copy joined to a sheared one it broke into
  slivers (four bodies); cut by two copies on the same slope with different
  ends, the brick and the frame met in open edges.
- **The brick behind the window stands on the base.** Stopped 1 mm above the
  table, the base under it was cut away and the slicer propped its foot.
- **The toys and the fanlight run through the glass, flush,** not raised on
  it: nothing about them hangs over air.
- **The skylights have upright sides,** not sides square to the roof (a
  lower side square to a 55° roof leans out over air), and their frames sink
  2 mm into the roof. In pockets they came out as three loose pieces.
- **The doors have one groove,** the meeting line, pointed under the crown.
  Plank grooves running up into the arch and across the hinges left small
  ceilings the slicer propped.
- **The eave is at 64 mm** so the window's keystone stays under the eave
  flare.
- **The sign's letters are 3.4 mm, on a 33 mm board,** the most room between
  the window's frame and the quoins. At 4.2 mm, WORKSHOP was 38.7 mm wide and
  the board cut it to "VORKSHO" in the renders.

## Honest weak points

- **The toys are line drawings 0.8 mm wide.** They read clearly from the
  front and lit from inside; small details (the teddy's eyes, the horse's
  saddle) are at the limit of what a 0.4 mm nozzle draws.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, keystones, the sign and the wreaths read as wedges from
  below.
- **The roof is solid slate,** so the light comes out through the windows,
  not the roof.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
