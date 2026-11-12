# FACTS: Desk Cable Rail, v1 (v2 of the Cable Hook)

Every number is from this folder's checks; the source is on each line.

## Version
- **v1**, 2026-11-12. Replaces the Cable Hook (`openscad_models/cable_hook.*`), which
  stays where it is until Benson swaps the MakerWorld model (Private, untouched).
- **Not printed yet.** Every image is a render.

## What it is
A slim J-channel that fixes under a desk's front or back edge. Cables drop in through
the 9 mm gap between the lip and the desk and lie in a row; three angled notches in the
lip let a cable leave the rail and drop toward the floor wherever it needs to.

## Numbers
| what | value | source |
|---|---|---|
| Size | 60 mm long; 34.4 mm deep including the screw tab; hangs 26 mm below the desk | `cable_rail.scad` |
| Channel | 15.6 mm wide inside; the gap to drop cables in is 9 mm | `cable_rail.scad` |
| Drop notches | three, 7 mm deep, angled | `cable_rail.scad` |
| Fixing | two 4.2 mm holes for #6 or #8 pan-head wood screws, or strong double-sided mounting tape on the 14 mm tab | `cable_rail.scad` |
| Print | 28 m 26 s, 9.1 g; standing on one end; 300 layers, 0 support lines | `checks/slice.txt` |
| Settings | 0.2 mm layers, supports off, P1S 0.4 nozzle, Bambu PLA Basic profile | `checks/slice.txt` |
| Checks | product gate (0 support moves, 0 overhang perimeters, min wall 2.4), print fidelity (0 flags), fragility (0): all pass | `checks/` |

## Free or paid, per platform
**None decided.** The old Cable Hook is a Private MakerWorld model; Benson swaps it.

## Safe to say, word for word
- "A slim cable rail that screws or tapes under your desk edge."
- "Cables drop in from the side and lie in a row; three notches let any cable leave where it's needed."
- "Prints standing on its end, no supports, in about half an hour."

## Don't say
- That it's printed or tested (not yet).
- "Prints flat": it prints standing on its end. The old Cable Hook's page says flat.
- How many cables it holds: not measured. (The channel is 15.6 mm wide inside.)
- A weight rating: not tested.

## Media
| file (this folder) | shows | version |
|---|---|---|
| `images/cable_rail_under_desk.png` | under a desk slab with three cables, one leaving by a notch (render props) | v1 |
| `images/cable_rail_front.png`, `_three_quarter.png`, `_top.png` | the rail alone | v1 |

- **Missing:** a photo of a real one under a desk.
