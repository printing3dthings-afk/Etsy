# Victorian Townhouse — printing notes

Building #5 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-01 from four forms
("Bow-front townhouse"), it is **a tall, narrow three-storey brick house with
a round bow window up its whole front**. It is the village's first
three-storey house:

- a square brick house, white quoins at its corners and white string courses
  between the storeys;
- up the left of the front, a round brick bow running all three storeys,
  three sash windows on each, finishing over the cornice in a bell-flared
  slate cone with snow on its crown and a finial;
- on the right, a slate door with an evergreen wreath and a white bow, in a
  white surround with a glazed fanlight over it, up two brick steps between
  low brick cheek walls with white copings;
- segmental sash windows with white frames and keystones on every floor, an
  evergreen window box under the window over the door;
- over a deep white cornice, a mansard roof:
  - steep slate sides in courses, with a dormer over the door and two at the
    back;
  - a low slate pyramid above, capped with snow and a finial;
  - a tall brick chimney with two pots;
- icicles under the cornice, and a soft snow base with a rounded edge and
  drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The bow opens into the house through its whole height, and each
dormer through a passage under its own gable, so the one light fills all of
them. It measures 65.0 × 75.6 × 121.5 mm, snow base and finial included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_townhouse.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the house, the bow, the chimney, the steps and cheek walls | brick red `#A8483A` |
| roof | the mansard and its dormers, the bow's cone, the finials, the door | slate `#2E3440` |
| trim | snow base and drifts, quoins, string courses, the cornice, every window's frame, keystone, bars and pane, the door surround and fanlight, the copings, icicles, snow on the roofs, the wreath's bow | white `#F4F1EA` |
| accent | the wreath, the window box | evergreen `#2F6B45` |

**Every window is glazed,** the fanlight and dormers included. Each has its
pane, and its bars stand on the pane.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.
- It is 121.5 mm tall on a 65 × 76 mm base. The gate finds its centre of mass
  over the base; give the plate a clean first layer.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **8 h 03 m** | **59.6 cm³, about 74 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 74 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the house and the bow;
- a 46.6 mm circle round the house's centre is clear from the table to
  70.7 mm;
- a 38 mm tealight has room to 78.0 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom), with room to spare: the house is 52 mm square inside its walls.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.33 mm, median 2.73 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 20.25 cm² of bed contact;
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 19.1 mm³ of 96,861 mm³ is not printed; 0.4 mm³ printed that was
  not modelled; 0.3 mm³ printed in another colour. **5 flags:**
  - three inside the roof, out of sight (5.8, 1.9 and 1.0 mm³, two layers
    each at 91.2 mm): where each dormer's passage closes to a slit at the
    peak of its gable, under the solid slate. Nothing on the outside changes,
    and the gate's slicer finds no support or overhang there;
  - the edge of the snow on the bow's cone (0.15 mm³);
  - the edge of the door's wreath (0.2 mm wide, 0.07 mm³).
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The two
  finials score 3.6 and 3.2, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the snow base in front of
  the steps, the same mark as the other buildings, mirrored so it reads OBC
  with the house turned over, front toward you.

## What it took to print without supports

The block is the toy shop's (`../toy_shop`) and the bow is the church's apse
(`../church`) turned to the front and carried up three storeys, each with
every fix in their notes. These were this building's own, each found on the
gate's slicer, its thin-wall scan or a section through the model:

- **The house's ceiling inside the mansard is a pyramid at 60°, not 55°.** At
  55° its four hips ran at 45.3°, and the slicer propped the whole ceiling.
  It starts just over the top floor's windows so its point stays inside the
  roof.
- **Each dormer's window is lit through a passage under its own 60° gable.**
  The passages:
  - end on the plane of the house's ceiling, not upright. Ended upright, they
    left knife edges where they met it;
  - sit at 10 mm from the middle, not 12–14. Nearer the corners the ceiling
    there falls toward the wall, and it met each passage's gable in a level
    V the slicer propped;
  - have gables at 60°. At 55° the line where each crossed the ceiling ran at
    47.8° and was propped.
- **The bow opens through the wall and on back only above the ceiling's
  plane,** for the same reason: ended upright behind the wall, the solid
  over it came down to a knife edge.
- **The window panes reach forward to where each frame's sloped hole
  begins.** Short of it, each dormer pane left a level 0.2 mm ledge, and the
  slicer propped a column from the snow up through every window below.
- **The door's surround hole is cut from the brick as well as the white.**
  Cut from the white only, brick filled the fanlight's recess down to its
  head, a level 1 mm ledge.
- **The fanlight's bars fan out at 55° off level, and the door's panels are
  pointed.** At 45°, and square-headed, the slicer propped them.
- **The mansard's corners are rounded 2.4 mm.** Nearly square, they stood
  0.4 mm out past the cornice's rounded corners, over air.
- **The cornice's face is 1.2 mm tall and the dormers' ridges are flat on
  top,** each because the thinner first versions were the model's thinnest
  walls.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, keystones, string courses, the cornice and the window
  box read as wedges from below.
- **The roof is solid slate above the top floor.** The light reaches the
  dormers through their passages, but the mansard itself does not glow.
- **Icicles hang against the wall, not in the air.**
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
