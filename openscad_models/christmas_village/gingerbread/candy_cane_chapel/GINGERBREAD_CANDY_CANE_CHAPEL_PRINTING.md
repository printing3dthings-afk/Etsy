# Gingerbread Candy Cane Chapel — printing notes

Building #2 of the Gingerbread Christmas village
(`../../CHRISTMAS_VILLAGE.md`), and its first to join round and square
(Scott, 2026-09-30: "I want to incorporate round and square together on some
buildings … Do all different shapes and stories of the buildings"). Picked
from four layouts, it is **a square gingerbread nave with a round candy-cane
tower at its front**:

- a one-storey gingerbread nave under a steep 55° chocolate gable of scallop
  tiles, icing piped down its corners and dripping off its eaves and rakes;
- icing along the ridge, rounded over the top, with four gumdrops on it;
- three tall arched windows down each side and one in the back wall, each
  with a frame of icing beads, and a peppermint round window in the back
  gable;
- at the front a round tower standing half out of the gable: white icing
  striped red in a spiral all the way up, like a candy cane, under a steep
  spire striped the same way, whose tip curls over like a cane's crook;
- arched windows round the tower, and a chocolate-bar door at its foot;
- a candy cane standing either side of the tower on the nave's front;
- a soft snow base with a rounded edge and two peppermints lying on it.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The tower opens into the nave through a pointed doorway, so one
light fills both, and the tower's white walls glow with the stripes dark on
them. It measures 68.0 × 83.8 × 132.3 mm, snow base and crook included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `gingerbread_candy_cane_chapel.3mf`. It is one object with
four parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the nave's walls, the kneelers | gingerbread `#C68642` |
| roof | the nave's roof and its scallop tiles, the door | chocolate `#5A3825` |
| trim | snow base, corner beads, eave soffit and drips, rakes and their drips, icing on the ridge, window and door frames with their beads, panes and bars, the tower, the spire and its crook, the canes' and peppermints' white | icing white `#F7F3EE` |
| accent | gumdrops, the stripes on the tower, spire and crook, the canes' and peppermints' stripes, the round window's wedges | candy red `#D7263D` |

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
| **single colour** | **6 h 36 m** | **49.3 cm³, about 61 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 61 g of model **+ purge** |

The red stripes run the tower's whole height, so the AMS changes colour on
almost every layer from the plinth to the crook. Expect the four-colour
print to take much longer and purge much more than the single-colour time
suggests.

## The tealight

Measured on the exported model:

- the base is open under the nave, and the tower opens into it;
- a 46.6 mm circle round the nave's centre is clear from the table to
  50.6 mm;
- a 38 mm tealight has room to 56.6 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of headroom),
by 0.6 mm. The steep gable comes down to a 49 mm eave, so the circle's edge
is where the room is lowest.

## Verified before shipping — on the real exported meshes

GATE_BLOCK

## What it took to print without supports

The nave is the first square gingerbread cottage's, the tower the toy
shop's, each with every fix in their notes. These were this building's own,
each found on the gate's slicer or a section through the model:

- **Panes are never cut by the openings.** The white part held the frames
  and the panes together; cut by the window openings, every pane went and
  every frame's head was left as a bridge over nothing.
- **The tower's openings do not cut the white part either.** They trimmed
  the beaded frames' heads into flat ledges the slicer propped.
- **The tower is centred on the nave's inner face.** Centred 5.7 mm in front
  of it, its inner wall met that face at 55° and left a knife edge of wall
  the height of the doorway, the thinnest 1% of the whole model.
- **The stripes are cut from the tower and the spire themselves** (a twisted
  wedge intersected with each), so they are flush with the white, not laid
  on it, and nothing overhangs at their edges.
- **The crook bends sideways, not forwards**, so its curl leans over the
  spire rather than out over air.
- **No drips at the rakes' peak**, where two met in a sliver.
- **The icing's ridge is rounded**, 2.2 mm across. Drawn to a point it was a
  knife edge the length of the ridge, measured at 0.61 mm.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, beads and drips read as wedges from below.
- **The crook is the most fragile part.** It prints, and fragility scores it
  FRAG_CROOK, but handle it with care.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
