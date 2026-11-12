# Moon Phase Coasters

Scott, 2026-11-11, picked form D of five for the coaster set: "the four coasters show
the moon's phases and stand in an arched night-sky rack."

- **Four coasters,** 92 mm, 4.8 mm thick:
  - waxing crescent, first quarter, waxing gibbous, full;
  - a navy sky, the lit moon in cream, its dark side and craters in slate, cream stars;
  - every colour a flush inlay in the top three layers of the face;
  - a rim 0.8 mm proud keeps drips on the coaster;
  - the OBC mark inlaid in cream underneath.
- **The rack is two flat prints.**
  - **The base:** four curved cradles, each 0.4 mm bigger than a coaster, so the coasters
    stand one behind another, 3.2 mm apart.
  - **The arch panel:** navy with cream stars. It stands in a groove at the front and its
    window frames the front coaster's moon.
  - **Why the panel prints flat:** printed upright, the window's top would have been a
    68 mm arc in mid-air. Flat, it needs nothing.
- **Not printed yet.**

## Printing (`checks/slices.txt`)
| file | what | time | filament |
|---|---|---|---|
| `moon_coasters_crescent_quarter.3mf` | two coasters | 2 h 2 m | navy 33.8 g, cream 3.6 g, slate 3.6 g |
| `moon_coasters_gibbous_full.3mf` | two coasters | 2 h 3 m | navy 33.8 g, cream 5.6 g, slate 1.7 g |
| `moon_coaster_rack.3mf` | base + panel | 2 h 2 m | navy 41.1 g, cream 3.2 g |

All face up, 0.2 mm layers, supports off. Smooth PEI for PLA.

**Two coasters to a plate, not four:** a 2 × 2 plate is 190 mm square and leaves
little room for the colour-change prime tower.

## Checks (`checks/`)
- **Product gate:** pass on the coaster, the base and the panel.
- **Print fidelity:** 0 flags on all four coasters, the base and the panel.
- **Fragility:** nothing slender on any of them.
- **Fit (`check_fit.py`, exported parts):**
  - each coaster, dropped 0.4 mm, rests on its cradle without overlapping it;
  - each lifts straight out;
  - 3.2 mm between neighbours, and between the front coaster and the panel;
  - pushed forward, the front coaster meets the panel instead of passing the window.

## Traps hit on the way (all fixed)
- **`BACK` is BOSL2's.** Naming the back wall `BACK = 3.0` broke every BOSL2 anchor
  ("Invalid points list"). It's `BACK_W` now.
- **An inlay cut 0.01 mm tall stands 0.01 mm proud.** The moon's weld pinched where its
  circle meets the terminator. Inlays are now exactly the top three layers, and only the
  pockets in the navy run past the face.
- **A union of flush inlays can leave touching, unmerged walls.** The gate checks the
  uncut coaster shape instead, which is the same solid; print fidelity checks the
  colour parts.
- **Stars placed by eye ran off the arch.** They're placed by rule now, midway between the
  window and the edge.

## Files
- `moon_coasters.scad`: the model. `part` = `coaster_navy`, `coaster_cream`,
  `coaster_slate` (with `phase` 0-3), `base`, `base_mark`, `panel_navy`, `panel_cream`,
  the `*_print` welds, and poses for renders and the guide.
- `check_fit.py`, `render_guide.py`, `make_guide.py`.
- `Moon_Phase_Coasters_Guide.pdf`: printing and putting it together.
- `FACTS.md`: the fact sheet for posts and listings.
