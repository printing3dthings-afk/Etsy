# FACTS: Snowflake Screen, v1 (v2 of the Pleated Fan)

Every number is from this folder's checks; the source is on each line.

## Version
- **v1**, 2026-11-12. Replaces the Pleated Fan (`openscad_models/pleated_fan.*`),
  which stays where it is: it fails the product gate (24,094 support moves, min wall
  1.19) and its MakerWorld page says "supports off".
- **Not printed yet.** Every image is a render.
- **The hinge test is done:** Scott printed it and picked the 2.0 mm hole (2026-11-13). The screen uses it.

## What it is
A three-panel folding screen for a desk or shelf: ice-blue panels, each with a white
snowflake inlaid flush in the face, and two smaller ones in the other panels'
patterns. Two hinges, each pinned with a length of 1.75 mm filament. It stands
with the side panels turned back.

## Numbers
| what | value | source |
|---|---|---|
| Panels | three, 45 × 90 × 6 mm; 135 × 90 mm laid flat | `snowflake_screen.scad` |
| Hinges | 9 knuckles each, 0.5 mm gaps; 2.0 mm pin holes; pins 1.75 mm filament, 88 mm long | `snowflake_screen.scad` |
| Hinge swing | 101° one way, 108° the other, from flat | `checks/fit_screen.txt` |
| Standing | wings at 40°, centre of mass 12.9 mm inside the footprint | `checks/fit_screen.txt` |
| Print | 2 h 10 m; blue 40.7 g, white 2.1 g; 30 layers, 0 support lines | `checks/slice_screen.txt` |
| Hinge test | 24 m, 7.5 g; two hole sizes, 2.0 and 2.3 mm | `checks/slice_coupon.txt` |
| Settings | 0.2 mm layers, supports off, P1S 0.4 nozzle, Bambu PLA Basic profile | `checks/slice_screen.txt` |
| Checks | product gate, print fidelity (0 flags), fragility (0), fit, toolpath separation: all pass | `checks/` |

## Free or paid, per platform
**None decided.** Scott's call. It would go on the existing private MakerWorld page
as an update to the Pleated Fan, if he wants.

## Safe to say, word for word
- "A three-panel folding screen with inlaid snowflakes."
- "Prints flat in one go, no supports. The hinges are pinned with 1.75 mm filament."
- "The snowflakes are inlaid flush: the face is smooth."
- "Fits any Bambu Lab printer's plate." (135 × 90 mm)

## Don't say
- That it's printed or tested (not yet).
- That it folds flat: the hinges stop at about 100° each way.
- "Works across the full Bambu Lab printer range": it was sliced for the P1S only.
- An "Optimized 0.16 mm" profile: none was sliced.
- That it's print-in-place: the pins go in after printing.

## Media
| file (this folder) | shows | version |
|---|---|---|
| `images/snowflake_screen_front.png` | standing, wings back, from the front | v1 |
| `images/snowflake_screen_three_quarter.png` | three-quarter | v1 |
| `images/snowflake_screen_top.png` | from above | v1 |
| `images/guide_parts.png`, `guide_pin.png`, `guide_coupon.png` | the guide's steps | v1 |
| `Snowflake_Screen_Guide.pdf` | printing, pinning and the hinge test | v1 |

- **Missing:** a photo of a real print.
