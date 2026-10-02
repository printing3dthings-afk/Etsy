# Victorian Clock Tower — printing notes

Building #7 of the Dickens Victorian Christmas village
(`../../CHRISTMAS_VILLAGE.md`). Picked by Scott on 2026-10-02 from four forms
("Square tower on a round base"), it is **a square brick clock tower rising
out of a round brick drum**:

- a round one-storey brick drum:
  - four segmental sash windows with white frames, keystones and bars;
  - a slate door with two panels, an evergreen wreath and a white bow, in a
    white frame, on a brick step;
  - a slate cone over it, snow round the tower's foot, icicles under the eave;
- out of the cone, a square brick tower:
  - white quoins at its corners and a white string course;
  - on each of its four sides a big white clock face in a raised white ring,
    its hour marks and hands in slate, set at ten past ten;
  - a white cornice, and over it a steep slate pyramid in courses with snow on
    its point and a finial;
- a soft snow base with a rounded edge and drifts.

It is a hollow lantern with an open base, lit from inside by a battery LED
tealight. The tower's inside is open to the drum's room, and the clock faces
are glazed like the windows, so lit they glow: the hour marks and hands run
through the white glass and show dark against it. It measures 67.0 × 67.0 ×
160.1 mm, snow base and finial included.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `victorian_clock_tower.3mf`. It is one object with four
parts, already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | the drum, the tower, the step | brick red `#A8483A` |
| roof | the cone and the pyramid with their slates, the finial, the door, the clocks' hour marks and hands | slate `#2E3440` |
| trim | snow base and drifts, the eave's soffit, snow on the cone and the pyramid, icicles, quoins, the string course and cornice, every window's frame, keystone, bars and glass, the clock faces and their rings, the door frame, the wreath's bow | white `#F4F1EA` |
| accent | the wreath | evergreen `#2F6B45` |

**Every window is glazed,** the four clock faces too.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.
- It is 160 mm tall on a 67 mm base. The gate finds its centre of mass over
  the base; give the plate a clean first layer.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** | **6 h 10 m** | **46.4 cm³, about 57 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 57 g of model **+ purge** |

## The tealight

Measured on the exported model:

- the base is open under the drum and the tower;
- a 46.6 mm circle round the drum's centre is clear from the table to
  51.2 mm;
- a 38 mm tealight has room to 58.1 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of
headroom). The drum's eave is at 48 mm so its cone's ceiling stands at 51
over the circle's edge; inside the tower the room runs on up to the pyramid.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 2.95 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height;
  - 14.68 cm² of bed contact;
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 26.8 mm³ of 58,548 mm³ is not printed; 1.3 mm³ printed that was
  not modelled; 0.4 mm³ printed in another colour. **10 flags, all the same
  and cosmetic:** the last slivers of the tower's brick courses where they
  run into the slate cone, 0.2 to 0.5 mm wide (0.27 to 0.45 mm³ each), too
  thin to lay. The courses end a hair short at the roof line.
- **The clocks print as drawn:** their marks and hands lose nothing the
  comparison flags.
- `fragility`: nothing slender enough to snap. 0 high, 0 watch. The finial
  scores 3.2, against a watch level of 4.
- **OBC maker's mark:** engraved 0.8 mm deep under the snow base in front of
  the door, the same mark as the other buildings, mirrored so it reads OBC
  with the tower turned over, front toward you.

## What it took to print without supports

The drum is the round cottage's (`../cottage`) without its gable, and the
door the toy shop's tower door (`../toy_shop`), each with every fix in their
notes. These were this building's own, each found on the gate's slicer or its
mesh checks:

- **The tower stands on the cone's ceiling,** like a chimney: its walls rise
  from the 58° slope, not from a ledge. Under the cone, outside where the
  cone is cut for it, they stop 0.3 mm over the ceiling, inside the cone:
  down to the ceiling there, their foot lay on the cone's underside and the
  two met in open edges.
- **The cone is cut for the tower 0.3 mm inside its face, with corners
  rounded like the tower's.** Cut square, its corners met the tower's rounded
  ones tangentially and left zero-thick slivers (11 bodies).
- **The cornice's corners are rounded with its offset,** so a corner stands
  out no further than a face. Square, they leaned out at 45° and the slicer
  propped all four from the cone.
- **The pyramid's foot is rounded like the cornice,** its corners shrinking
  up the hips. Nearly square, they stood 0.3 mm out past the cornice's
  rounded corners and the slicer propped all four.
- **The pyramid's faces are at 68°,** so its hips run at 60°.
- **The glass stops at the room.** Running 0.2 mm (the windows) and 0.6 mm
  (the clocks) into it, the glass and the clocks' hands hung their lower
  edges in the room and the slicer propped them from the table.
- **The quoins start over the cone,** at 63 mm. From inside it, they met the
  cone and the tower in open edges.
- **The door's panels are low,** clear of the wreath's bow, which their heads
  ran into.

## Honest weak points

- **The clocks' hands and marks are 0.8 to 1.4 mm wide.** They read from
  across a room and lit from inside; they are not fine watch hands.
- **Raised details have sloped undersides.** That is how they print without
  supports. Frames, keystones, the string course, the cornice and the clock
  rings read as wedges from below.
- **The roofs are solid slate,** so the light comes out through the windows
  and the clocks, not the roofs.
- **It is tall and narrow** above the drum. It stands on its own centre of
  mass, but handle it by the drum, not the spire.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
