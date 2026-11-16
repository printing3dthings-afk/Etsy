# Gear Heart v2, FACTS (2026-11-16)

Fourteen gears round a heart-shaped plate and a knob gear in the middle, all turning
together. Scott's form 9A. Engineering: ENGINEERING.md (section 9 for v2).

## Status
- **v2 is designed and checked, not printed as a whole heart.**
- Its axle pin, boss, washer and gear are the clip test's. Scott printed that test
  (2026-11-16) and picked clip 3, the 0.65 barb: "Number 3 seems to feel the best."
- **v1** (`gear_heart_plate.3mf`, `gear_heart_gears.3mf`) has the snap posts, one of which
  snapped on Scott's print. Don't use v1 for anything new.

## The prints (Bambu Studio, P1S 0.4, PLA Basic, 0.20 Standard, textured PEI, no supports)
| file | what | time | filament |
|---|---|---|---|
| `gear_heart_plate_v2.3mf` | the heart plate: 15 bosses with pin holes | 1 h 54 m 51 s | 34.78 g |
| `gear_heart_gears_v2.3mf` | 15 gears and 15 axle pins | 2 h 19 m 48 s | 33.18 g |

- Sliced files: `checks/heart_plate_v2.gcode.3mf` and `checks/heart_gears_v2.gcode.3mf`.
- Guide: `Gear_Heart_v2_Guide.pdf`.
- Rebuild: `make_heart_v2.sh`, then `check_heart.py`, `make_heart_v2_images.py` and
  `make_heart_v2_guide.py`.

## What the checks say (details in ENGINEERING.md section 9)
- **Fit PASS** on the exported parts:
  - all fifteen gears turn together from the knob;
  - every pin seats in the plate touching nothing;
  - no gear rubs its pin;
  - each gear lifted 1 mm is held by its pin's barbs.
- **Product gate:** both prints pass, 0 support moves.
- **print_fidelity:** 0 flags on both.
- **Fragility:** 0 high and 0 watch on both.
- **Pins:** each goes in once, and comes out only for a repair: pinch the barbs together and
  push the pin down. The 0.65 barb's strain is inside the one-time limit, not the repeated one.

## Not known until a print
- Whether all fifteen pins click in and hold on the whole heart.
- Whether anything whitens.
- Whether the knob turns the full ring smoothly with the pins' end play.

## Images (`images/heart_v2_*.png`, design-review renders, not photos)
- `heart_v2_front.png`, `heart_v2_three_quarter.png`, `heart_v2_top.png`: assembled.
- `heart_v2_plate.png`: the plate print.
- `heart_v2_gears_plate.png`: the gears and pins print.
- `heart_v2_underside.png`: the pins' heads in their pockets.
- `heart_v2_plate_as_printed.png`, `heart_v2_gears_as_printed.png`: rendered from the
  toolpath of the checks' slices.

Not for children under 3: small parts.
