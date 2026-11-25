# FACTS: P1S Camera Sign, v1

Every number comes from this folder (STANDARDS 15).

## Version
- **v1**, built 2026-11-18; the slices were re-made 2026-11-25 with the current slicer tool.
- **Printed once, neon, in Lobster (Scott's photo, 2026-11-25): "Hard to read." Its timelapse
  is probably `real/neon_lobster_timelapse_cloud_short.mp4` (white base, blue letters; not yet confirmed).** Three
  neon font options are in `font_options/` (Nunito, Righteous, Courgette), not printed yet.
  Every image is a design-review render or flat view, not a photo.
- **For Scott's own printer.** Scott, 2026-11-25: upload it to his **Private** MakerWorld page
  tonight. It isn't public; whether it ever goes public is his call.

## What it is
- **A sign for the back wall inside the P1S:** "FOLLOW @onbrandcraftz2026". Anyone watching the
  chamber camera or a timelapse sees where to find the shop.
- **Two styles:**
  - **Neon:** the words in a bold script on their own raised outline;
  - **Plaque:** a rounded plate with a raised border, bold capitals.
- **No Instagram logo:** it's their trademark.

## Numbers
| what | value | source |
|---|---|---|
| Neon size | about 138 × 29 mm | `CAMERA_SIGN.md`, `camera_sign_neon_union.stl` |
| Plaque size | about 144 × 38 mm | `CAMERA_SIGN.md`, `camera_sign_plaque_union.stl` |
| Thickness off the wall | 2.4 mm (a 1.6 mm fallback is in `test_fit/`) | `camera_sign.scad` THICK; `test_fit/README.md` |
| Colours | 2: a near-black base `#1C1C1F` and orange lettering `#F28C28`; the AMS changes on the top four layers only | `CAMERA_SIGN.md` |
| Handle letters | about 8 mm tall (neon), 6 mm (plaque) | `CAMERA_SIGN.md` |

## Print time and filament (Bambu Studio's own slice: P1S 0.4, PLA Basic, 0.20 mm Standard, 3 walls, 15%, supports off)
| file | time | filament |
|---|---|---|
| `gcode/camera_sign_neon_two_colour.gcode.3mf` (2.4 mm) | 29 m 32 s | 7.3 g (5.9 black, 1.4 orange) |
| `gcode/camera_sign_plaque_two_colour.gcode.3mf` (2.4 mm) | 44 m 32 s | 13.2 g (11.5 black, 1.8 orange) |
| `test_fit/camera_sign_neon_1.6mm.gcode.3mf` | 25 m 35 s | 4.6 g |
| `test_fit/camera_sign_plaque_1.6mm.gcode.3mf` | 38 m 45 s | 7.8 g |

## Checks
- **2.4 mm (`logs/neon`, `logs/plaque`):** product gate PASS, print fidelity 0 flagged,
  fragility 0.
- **1.6 mm:** fails the gate's 1.2 mm wall floor (0.8 mm of plate under the letters,
  `test_fit/gate_*_1.6.txt`). It's a fallback for tight clearance only.

## Mounting
- **Where:** double-sided tape on the back wall, to one side of the lead screw's slot.
- **Before printing with it up:** check clearance with the printer idle
  (`test_fit/README.md`).

## Safe to say, word for word
- "A sign for inside your P1S, so your timelapses tell people where to find you."
- "Two colours, printed flat, no supports."

## Don't say
- That it fits every P1S, or any printer: the clearance isn't measured yet.
- That it's printed or tested.
- Any Instagram branding.

## Media (all renders)
| file | shows |
|---|---|
| `images/camera_sign_neon_colour_top.png`, `_front`, `_three_quarter` | neon, colour render |
| `images/camera_sign_plaque_colour_top.png`, `_front`, `_three_quarter` | plaque, colour render |
| `images/camera_sign_*_as_printed_*.png` | rendered from the slice's toolpath |
