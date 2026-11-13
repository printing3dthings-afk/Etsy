# Snowflake Screen (v2 of the Pleated Fan)

Scott, 2026-11-12: "Yes" to redoing the Pleated Fan as a snowflake folding screen,
with a corrected MakerWorld title and description.

- **Three panels,** 45 × 90 × 6 mm, ice blue:
  - a white snowflake inlaid flush in each face, plus two small ones in the other
    panels' patterns (the top three layers);
  - the OBC mark inlaid white under the left panel.
- **Two hinges,** 9 knuckles each, pinned with 1.75 mm filament cut to 88 mm.
- **It prints flat, in one go,** the knuckles interleaved. The pins, pushed in
  afterwards, hold the panels together.
- **Not printed yet.** The hinge has a test print; try that first.

## Why it's flat now
The Pleated Fan stood upright on the plate, so its hinge axis was vertical and each
knuckle printed on top of the one below, across a gap: its underside was in mid-air.
The product gate's slicer propped it with 24,094 support moves, and the fan's
MakerWorld page says supports off. A first redesign kept it upright with cone-shaped
knuckle joints; every slope printed, but each knuckle's first ring still started over
the gap. On a vertical axis that can't be designed away.

Laid flat, the axis runs along the plate:
- the knuckles' lower sides are 37° from upright down to a flat foot;
- the pin hole is a teardrop with a pointed roof. A flat-roofed hole printed its
  0.9 mm bridge as 20 overhang perimeters on the first test.
- The panels are 6 mm thick and the axis 2.8 mm up, so 1.2 mm of wall stays over the
  hole's point. At 5 mm thick it was 0.84.

The cost of the flat layout: the pins go in by hand, as on the pocket pebble case.

## Printing
| file | what | time | filament |
|---|---|---|---|
| `snowflake_hinge_test.3mf` | the hinge at full size, two hole sizes | 24 m | 7.5 g |
| `snowflake_screen.3mf` | the screen | 2 h 10 m | blue 40.7 g, white 2.1 g |

Face up, 0.2 mm layers, supports off, Smooth PEI. Times and grams are from Bambu
Studio's own slice (`checks/slice_*.txt`).

## The hinge test
- **Two hinges, side by side:** one notch on the leaf for a 2.0 mm hole, two for
  2.3 mm.
- **Pins:** two 28 mm pieces of 1.75 mm filament.
- **What to report:**
  - Which one he prefers: a hinge that holds its angle, or one that swings freely.
  - Whether either pin wouldn't go in.
  - Whether either hinge printed stuck.
- **Scott's pick, 2026-11-13: the 2.0 mm hole** ("Mark 1 felt better"). The screen
  was drawn at 2.15 between the two while it waited; it is 2.0 now, re-checked and
  re-sliced (gate, fit, fidelity, fragility all pass; 2 h 10 m, 40.7 g blue, 2.1 g white).

## Checks (`checks/`)
- **Product gate:** pass on the screen and on the test. 0 support moves, 0 overhang
  perimeters, min wall 1.73 (1st percentile).
- **Print fidelity:** 0 flags. The only misses are specks under 0.3 mm between
  snowflake branches.
- **Fragility:** nothing slender.
- **Hinge fit (`check_hinge.py`, the test's exported leaves):**
  - clear at rest, 0.5 mm closest;
  - turns 108° one way and 101° the other;
  - a 1.9 mm pin clears both hole sizes;
  - the hole is closed at the bottom.
- **The screen (`check_screen.py`, exported print):**
  - the three panels are clear of each other;
  - each wing turns 101° and 108°;
  - both pins clear;
  - with the wings back 40°, the panels are clear and the centre of mass is
    12.9 mm inside the footprint.
- **Toolpaths (`check_slice.py`, the test's slice):** the two leaves print apart on
  all 30 layers, at both hole sizes. A control of the same test at a 0.05 mm gap is
  caught as fused on every layer.

## MakerWorld
The corrected title and description are in `MAKERWORLD.md`.
