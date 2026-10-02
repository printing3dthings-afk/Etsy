# Gingerbread Cookie Clock Tower — printing notes

Building #6 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-02 from four forms
("Stacked cookie tower"), it is **a round gingerbread tower stacked from
three thick cookie discs, with a big frosted-cookie clock on its front**:

- three gingerbread cookie discs, each with a bevelled foot and (the lower
  two) a rounded top, an icing band between each pair dripping down the disc
  below;
- on the front of the tall top disc, a big scalloped gingerbread cookie piped
  round with icing dots; its frosting-white face carries chocolate hour dots
  and candy-red hands, set at ten past ten;
- arched windows framed in icing round all three discs, and a chocolate door
  with two pointed panels in a piped icing frame;
- frosting round the top, dripping down, and a chocolate cone of shingles
  with red and white gumdrops round its foot;
- a cap of icing on the point, and out of it a white candy cane striped red,
  its crook leaning over;
- a soft snow base with a rounded edge, drifts and three peppermints.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The clock's face is glazed like the windows, so lit it glows: its
dots and hands run through the white glass and show dark against it. It
measures 67.0 × 67.0 × 140.6 mm, snow base and cane included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_cookie_clock_tower.3mf`. It is one object with
four parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the cookie discs, the clock's cookie | gingerbread `#C68642` |
| roof | the cone and its shingles, the door, the clock's hour dots | chocolate `#5A3825` |
| trim | snow base and drifts, the icing bands and their drips, the top's frosting and drips, the cone's cap, the window frames, glass and bars, the door's piped frame, the clock's piped dots and its face, the white gumdrops, the cane, the peppermints' white | icing white `#F7F3EE` |
| accent | the clock's hands, the red gumdrops, the cane's stripes, the peppermints' stripes | candy red `#D7263D` |

**Every window is glazed,** the clock's face too.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **5 h 02 m** | **40.2 cm³, about 50 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 50 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the whole tower;
- a 46.6 mm circle round its centre is clear from the table to 81.1 mm;
- a 38 mm tealight has room to 87.3 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom), with room to spare: the room keeps its full width up the three
discs to the cone.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.57 mm, median 3.60 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 17.02 cm² of bed contact;
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- CHECKS_PENDING

## What it took to print without supports

The tower is the gingerbread Santa's workshop's drum (`../santas_workshop`)
stacked into discs, the door the toy shop's tower door
(`../../victorian/toy_shop`) and the cane the candy cane chapel's crook
(`../candy_cane_chapel`), each with every fix in their notes. These were this
building's own, each found on the gate's slicer, its thin-wall scan or a
section through the model:

- **The wall is 2.2 mm and the discs' rims are set in 1.0.** At 1.68 with
  rims set in 1.4, the wall at each disc's foot and top was 0.28 mm.
- **The icing bands are 3.6 tall, 0.7 proud, their bevels starting 0.25 mm
  under the disc's top, inside its rounding,** and each upper disc's foot sits
  0.3 mm down in the band. At 3 mm their lip over the bevel was 0.6 tall, the
  thinnest walls; starting at the very point the rounding ended, band and
  disc shared an edge ring and the drips under it left open edges.
- **Every window frame sits wholly on its disc's upright face,** between the
  bevelled foot and the rounded top. A sill starting on the middle disc's
  foot stood one layer out over the band and was propped; a head in the
  rounding met it in walls under 0.5 mm.
- **The frames, the door's frame and the clock's cookie are the series'
  relief from 0.4 mm in, with a plain plate behind them 1.2 mm into the
  wall** for where a rim is set in. Sheared from 1.2 mm in, each opening rose
  more than its frame is wide and every head came to a knife edge.
- **The clock's face is 18 mm across in a 28 mm cookie,** so the cookie
  round it is wider than its opening rises, with room left for the piped
  dots; and the cookie's lowest scallop stands 0.2 mm over the top disc's
  foot. Reaching the foot, it stood out over the band.
- **The piped dots round the clock are placed one by one,** square to the
  wall, each a rod sheared exactly as the cookie is, from 0.3 mm in the wall
  to 0.6 mm proud of the cookie's face. Laid in strips, theirs or the
  cookie's, they met the cookie on shared strip planes and left open edges;
  clipped like the other reliefs, a dot this small closed before it reached
  the face and all 24 were hidden inside the cookie. Their ring follows the
  cookie as it is at its face, where the shear moves it up.
- **The door's piped beads start 1.6 mm up,** on the upright face: from
  0.6 mm their cut feet stood over the bottom disc's bevelled foot.
- **The glass, the hour dots and the hands stop at the room.** 0.6 mm into it,
  their lower edges hung there and the slicer propped them from the table.

## Honest weak points

- **The clock's dots and hands are 1.2 to 2.4 mm across.** They read from
  across a room and lit from inside; they are not fine watch hands.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, the cookie, the dots and the drips read as wedges from
  below.
- **The cone is solid chocolate over the room's ceiling,** so the light comes
  out through the windows and the clock, not the roof.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
