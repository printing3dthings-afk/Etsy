# Haunted Undertaker — printing notes

Building #5 of the Haunted Town series (`../HAUNTED_TOWN.md`). A tall, narrow
three-storey house squeezed between the bare gable ends of two neighbours
that are no longer there:

- the two gable walls stand up past its roof, their tops broken off ragged,
  and on their outer faces are the scars of the houses that leaned on them: a
  lower roofline, a floor and a chimney flue;
- the front and back are fish-scale shingles;
- coffin-shaped windows, pointed at the top, each with a cross in it;
- a mansard roof whose ridge sags, a coffin window in a dormer on its front,
  and a crooked chimney behind;
- an UNDERTAKER sign hung crooked over a pointed-arch porch, and **a coffin
  standing on end against the porch post**, a cross on its lid.

Like the others, it is a hollow lantern with an open base, lit from inside by
a battery LED tealight. It is the tallest and narrowest building in the town:
57.6 × 76.4 × 160.3 mm, porch and chimney included.

Built 2026-10-02 to Scott's variety plan (2026-09-25): fish-scale shingles,
coffin-shaped windows, a mansard. It shares none of these with any other
building in the town. Scott chose "tall and squeezed" from four forms.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `haunted_undertaker.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the fish-scale front and back, the two gable walls and their scars, plinth, porch deck and step, the dormer | dusk blue `#3F4A63` |
| roof | the mansard and its slate courses, ridge cap, the dormer's roof, the porch roof and its courses, the crooked chimney | slate `#2B2F38` |
| trim | window frames, crosses and glass, the cornices, door and frame, the porch arcade, the sign board, the cross on the coffin | cream `#EFE6D2` |
| accent | the coffin, the sign's carved letters | coffin wood `#6B4429` |

**Every window is glazed,** the dormer's too.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **9 h 16 m** | **70.8 cm³, about 88 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 88 g of model **+ purge** |

A listing must say which version the buyer gets.

## The tealight

Measured on the exported model:

- the base is open under the whole room, 50.0 × 48.6 mm;
- a 46.6 mm circle round its centre is clear from the table to 91.4 mm;
- a 38 mm tealight has room to 104.4 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of headroom)
with room to spare. The room is tall: most of the light comes out of the
ground and first floor windows.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.21 mm, median 3.00 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (160.3 mm);
  - 13.44 cm² of bed contact (30.5% of the footprint);
  - centre of mass over the base.
- CHECKS_PENDING

## What it took to print without supports

Every one of these was found on the gate's slicer or its thin-wall scan and
fixed in the model:

- **The fish scales are the town's clapboard, scalloped.** Each course
  starts flush with the wall along a line of round butts, ramps out 0.84 mm at
  58° or steeper, and steps back in on an upward ledge at the next course's
  line, so the scales read as the ledges' scallops and nothing faces down.
  First built as one raised relief per scale, the scales' tops were cut into
  arcs by the row above; the town's relief clips its flat top over 0.2 mm
  either side, and along every row the arcs left slivers 0.01 to 0.3 mm thick
  (1.5% of the building under one bead).
- **The courses run on under the frames, the sign and the door,** which take
  them over, and 0.3 mm into each gable wall. Cut clear of them with a gap,
  every course left a sliver along every cut edge.
- **On the front, the scales start just above the porch roof.** Run on under
  it, the porch roof's steep underside cut the courses into eight loose scales
  and sealed air pockets behind them. Below that line the front is nearly all
  porch, and stays plain.
- **The dormer's coffin window has a light channel behind it.** The glass
  sits above the ceiling there, which rises at 72° from the wall's top, so a
  channel with the window's own 58° head runs back to the room. Where it meets
  the 72° ceiling the corner is 54.8° on the diagonal. The 0.3 mm band of roof
  under the dormer is cut out of the channel too: left in, it stood inside as
  a loose sheet.
- **The mansard's ceiling has a level ridge.** Outside, the upper slopes are
  55° with a 3 mm sag; inside, the ceiling rises at 50.8° to a level ridge.
- **The lower slopes are slate in the same reversed sawtooth,** ramping out
  0.84 mm over 1 mm on a slope that leans back at 72°: 62.7° from horizontal.
- **The sign's lettering is 42.2 mm wide on a 46 mm board.** At 4.2 mm the
  letters ran past the board's ends and left open edges and two support
  spots.
- **The windows' crosses are 1.6 mm bars.** At 1.2 they measured under one
  bead.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. The frames, crosses, sign and cornices read as wedges from below.
- **The walls are at the floor, not above it.** The 1st-percentile wall is
  1.21 mm against the 1.2 mm floor: the scales' course ends and the sign's
  letters are the thinnest parts.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
