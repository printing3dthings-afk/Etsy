# Haunted Schoolhouse — printing notes

Building #4 of the Haunted Town series (`../HAUNTED_TOWN.md`). A long, low,
one-room schoolhouse:

- half-timbered walls: dark beams on ochre plaster, braced either side of
  each post;
- pairs of narrow windows with pointed heads;
- a steep hip roof whose ridge sags in the middle;
- a bell cupola on the ridge, with a bell standing in its open belfry;
- a crooked chimney on the back slope;
- across the front, a porch on an arcade of pointed arches, under a porch roof
  that sags along its front edge;
- above the porch, an **oversized clock, stopped at 11:47**, in a gablet that
  carries the front wall up through the eave.

Like the others, it is a hollow lantern with an open base, lit from inside by
a battery LED tealight. The clock's face is glass, so it glows when lit: its
marks and hands run through the glass and show dark against it. It measures
102.0 × 74.2 × 154.4 mm, step and finial included.

Built 2026-10-02 to Scott's variety plan (2026-09-25): half-timbered walls,
paired narrow pointed windows, a hip roof with a bell cupola. It shares none
of these with any other building in the town. Scott chose the one-room school
from four forms.

`images/` holds renders of this model: `*_colour_*` in the four filament
colours, and `*_as_printed_*` rendered from the sliced toolpath itself, so
they show what the printer makes. Each has front, three-quarter and top
views. They are renders, not photos of a print.

**Print this:** `haunted_schoolhouse.3mf`. It is one object with four parts,
already aligned. Assign a filament to each part.

| part | what it is | colour in the file |
|---|---|---|
| body | plastered walls, plinth and porch deck, the clock gablet, the cupola's base | ochre `#A8814A` |
| roof | hip roof, slate courses, ridge and hip caps, crooked chimney, porch roof, the gablet's roof, the cupola's cap | slate `#2B2F38` |
| trim | window frames and glass, door and frame, the porch arcade, the clock's glass, the gablet's bargeboard, the belfry | cream `#EFE6D2` |
| accent | the half-timbering, the clock's ring, marks and hands, the bell, the finial | timber `#2E2219` |

The walls are ochre, not red: the post office is already brick red, and the
town's variety plan gives every building its own wall colour.

**Every window is glazed,** the clock too.

## Settings that are not optional

- **Supports OFF.** Verified: the gate's slicer reports 0 support moves and
  0 overhang perimeters.
- **Print it standing up, as it sits in the file.**
- 0.2 mm layers.

## Cost — sliced, not estimated

| version | time | filament |
|---|---|---|
| **single colour** (e.g. for Jessee to paint) | **10 h 55 m** | **81.1 cm³, about 101 g of PLA** |
| **four colour, AMS** | slice in Bambu Studio for the real time and purge | about 101 g of model **+ purge** |

A listing must say which version the buyer gets.

## The tealight

Measured on the exported model:

- the base is open under the whole room, 88.6 × 48.6 mm;
- a 46.6 mm circle round its centre is clear from the table to 79.6 mm;
- a 38 mm tealight has room to 84.7 mm.

**This meets the series rule** (at least 46 mm across and 50 mm of headroom)
with room to spare.

## Verified before shipping — on the real exported meshes

- `product_gate` **PASSED** on the union of the four parts:
  - watertight, one body;
  - 1st-percentile wall 1.48 mm, median 3.52 mm, against the 1.2 mm floor;
  - 0 supports, 0 overhang perimeters;
  - printed height equals modelled height (154.4 mm);
  - 15.55 cm² of bed contact (20.6% of the footprint);
  - centre of mass over the base.
- Each of the four parts is closed, with every edge shared by exactly two
  faces.
- **The parts are disjoint.** All six pairwise intersections render empty.
- `print_fidelity` (the four-colour slice compared with the model, layer by
  layer): 12.6 mm³ of 108,966 mm³ is not printed; 1.0 mm³ printed that was
  not modelled; nothing printed in another colour. **3 flags, none of them
  visible detail:**
  - the knife-edge tip of the ridge cap, 0.22 mm wide, at two points along
    the sagging ridge (0.28 mm³ each), too thin to lay;
  - one layer at the very top of the inside ceiling (1.4 mm³), where the
    room's level ridge closes, inside the roof where nobody sees it.
- **The clock prints as drawn:** its ring, marks and hands lose nothing the
  comparison flags.
- `fragility`: nothing slender enough to snap. 0 high, 1 watch: the finial,
  8 mm tall, slenderness 5.0 against a watch level of 4 and the 17.5 of the
  chapel bar that snapped. The belfry's 3.4 mm corner posts do not register.
- **OBC maker's mark:** engraved 0.8 mm deep under the porch deck, the same
  mark as the other buildings, mirrored so it reads OBC with the building
  turned over, front toward you.

## What it took to print without supports

Every one of these was found on the gate's slicer and fixed in the model:

- **The eave flare turns the corners as a cone.** The hip roof's eave runs all
  the way round, so its 58° flare turns four outside corners. Flared out to a
  square corner, the corner edge ran at 46.9° (the diagonal is √2 longer) and
  the slicer propped all four. The eave line is now the plan offset by the
  eave, rounded at the corners, so each corner is as steep as the sides.
- **The ceiling has a level ridge.** The roof is 55° with a sagging ridge
  outside; inside, the ceiling rises at 50.7° to a ridge that does not sag. A
  sagging inside ridge closes from the middle outward and drew supports on the
  bakery.
- **The clock sits low enough that the room is right behind its glass.** A
  first version set it higher, with a light channel behind it. Where that
  channel met the ceiling, a 58° face and a 50.7° face made a corner too flat
  on the diagonal, and the slicer propped the whole corner. The walls went up
  6 mm (to 62 mm) and the channel went.
- **The clock's glass and marks are flush with the wall's face.** Set back
  0.2 mm like the windows' glass, the shallow recess round the dial's lower
  rim drew a cluster of support.
- **The gablet's slate cap is cut to the ceiling where it runs back over the
  room.** Uncut, its 30° underside hung there. The roof behind the gablet is
  taken out exactly where the gablet itself stays. Taken out whole, it left
  the roof resting on the gablet's 30° top where the gablet had been cut
  away; taken out only above the ceiling, it overlapped the gablet's own
  front wall.
- **The arcade is cut inside the porch roof, on the porch roof's own
  stations,** and the porch roof is then taken out of it, so the arcade's top
  is the porch roof's underside exactly. Cut to a separate underside, the two
  surfaces disagreed and left open edges along the front; taken out only in
  the trim part, the roof lost 2 mm of its own front edge and the slicer
  propped the gap.
- **The hip caps' feet reach 4.4 mm under the slope.** The roof falls away
  under a cap's corner end faster than the cap does, and with shallow feet the
  cap's end hung in the air.
- **The bell stands on the belfry floor, 0.3 mm into it.** It narrows all the
  way up from its lip, so nothing on it faces down. Standing exactly on the
  floor, it came out as a loose second body.
- **The finial's tip is 1 mm across.** A sharp point was lost in the last
  layers, and the printed height came out 0.8 mm short.
- **The belfry is two pointed tunnels crossing,** each with 58° heads, which
  leaves four corner posts and a cross vault with 58° groins.

## Honest weak points

- **Raised details have sloped undersides.** That is how they print without
  supports. The timbers, frames, the clock's ring and the porch roof read as
  wedges from below.
- **The finial is the one slender part** (a "watch", not a risk). Lift the
  building by its walls, not its cupola.
- **It has not been printed yet.** Everything above was measured on the
  model and its slice.
