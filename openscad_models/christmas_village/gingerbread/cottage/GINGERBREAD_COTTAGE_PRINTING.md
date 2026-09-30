# Gingerbread Cottage — printing notes

Building #1 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`), redrawn round (Scott, 2026-09-30:
"Christmas village keeps a rounder shape … Yes redo the cottages round too").
Picked from four layouts, it is **a cupcake**:

- a round gingerbread drum, fluted all round like a cupcake's paper (40
  half-round ribs);
- a chocolate dome over it, widest just past the drum;
- a wavy band of white icing piped round the dome's rim, with 30 drips
  running down the drum;
- eight red gumdrops round the dome and one on top;
- four round peppermint windows, red and white;
- a chocolate-bar door between two striped candy canes, crooks turned in
  over it;
- a soft snow base with a rounded edge, three drifts and two peppermints lying
  in front.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. It measures 69.0 × 69.0 × 86.0 mm, snow base and top gumdrop
included.

The square cottage it replaced passed every check too. It is in
`data/trash/` (`20260930-003`) and at commit 7de06df.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_cottage.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the drum and its flutes | gingerbread `#C68642` |
| roof | the chocolate dome, the chocolate-bar door | chocolate `#5A3825` |
| trim | snow base and drifts, the rim's icing and drips, the windows' rings, panes and bars, the door frame and its beads, the canes' white, the peppermints' white | icing white `#F7F3EE` |
| accent | gumdrops, cane stripes, the windows' and peppermints' stripes | candy red `#D7263D` |

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
| **single colour** | **4 h 52 m** | **39.3 cm³, about 49 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 49 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the drum: a 48.6 mm circle;
- a 46.6 mm circle round the centre is clear from the table to 39.6 mm;
- a 38 mm tealight has room to 46.5 mm.

**This is under the series rule** (at least 46 mm across and 50 mm of
headroom). The ceiling is a 58° cone from a 38 mm eave, so it closes in
early. Bambu's own LED tealight (37.2 × 36.6 mm) fits with 10 mm to spare. A
45 mm-tall generic one has 1.5 mm.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.38 mm, median 9.22 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 18.37 cm² of bed contact;
  - centre of mass over the base.
- `mesh_gate` on each of the four parts: closed, every edge shared by
  exactly two faces. Zero-area triangles: 20 in the body, 1 in the trim, none
  in the roof or accent. Each is a needle where two features' edges meet, and
  slicers ignore them.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 11.0 mm³ of 92,881 mm³ is not printed; 0.9 mm³ printed that was not
  modelled; 0.2 mm³ printed in the next colour. **4 flags, all cosmetic:**
  - three flute tops (0.13–0.15 mm³ each, at 35 mm). Each flute stops under
    the rim's flare, and its last half-millimetre tapers to a sliver the
    printer rounds off. It shows on 3 of the 40 flutes;
  - one layer at the edge of the front-right window's icing ring
    (0.04 mm³).
- `fragility`: nothing slender at all. 0 high, 0 watch, 0 slender runs.
- **OBC maker's mark:** engraved 0.8 mm deep under the front of the snow
  base, in the band between the drum's opening and the base's edge. It is the
  same mark as the other buildings, mirrored so it reads OBC with the cottage
  turned over, front toward you.

## What it took to print without supports

- **The dome is drawn over a cone.** A room's ceiling must rise at 45° or
  more to print, and a half-sphere's crown is too flat. So the ceiling is the
  village's 58° cone, and the dome sits over it with 5 mm of chocolate over
  the cone's point. It is solid between them; the slicer fills that with
  infill.
- **The gumdrops sit where the dome is 29°.** Higher up (41°), with the dome
  falling away under them, they stood up as tall bullets.
- **The snow base reaches 8.5 mm past the drum.** At 6.5 its rounded edge
  began under the peppermints, which hung over it and drew support from the
  table.
- **The frames stand 1.8 mm proud**, clear of the flutes, so nothing of a
  frame hangs off a flute's side.

## Honest weak points

- **The tealight headroom is short of the series rule**, above.
- **The dome is solid chocolate.** No light comes through the top, and it is
  most of the filament (the roof part is 55 cm³ of the model's 93).
- **The layer seam shows on the smooth dome.** The as-printed render has it
  as a vertical line up the front of the chocolate. In Bambu Studio, paint the
  seam onto the back of the dome before slicing.
- **Raised icing has sloped undersides.** That is how it prints without
  supports. From below, the drips and window rings read as wedges.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
