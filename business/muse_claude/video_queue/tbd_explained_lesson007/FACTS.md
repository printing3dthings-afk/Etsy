# Lesson 007 facts: every claim on screen and its source

Lesson: "The 0.2 mm rule". Every number comes from our own detail test coupon,
`openscad_models/detail_calibration/detail_coupon.scad`. It was re-sliced on 2026-11-20 at
0.20 mm layers by `tools/print_fidelity.py` (PrusaSlicer 2.7, Arachne walls, P1S 0.4 mm
profile) and measured by `measure_coupon.py`. The output is copied here as
`facts/measured_0.20.json`.

**What kind of number these are.** They are toolpath numbers: what the slicer tells the printer
to lay down. Bead rounding and ooze in real plastic aren't measured, because nobody has printed
the coupon yet. The screen says "measured on our test coupon's sliced toolpath, 0.20 mm layers".
Keep that line, or a line that says the same, wherever these numbers appear.

| Said or shown | Measured (json key) | Holds? |
|---|---|---|
| A 0.3 mm groove prints 0.4 | "groove, 0.6 deep: height", 0.3 → 0.4, 2 layers | yes |
| A 0.1 mm groove takes a full layer, 0.2 | same row, 0.1 → 0.2, 1 layer | yes |
| "Twice the size you drew" | 0.2 / 0.1 | yes |
| Our layers are 0.2 mm | Scott's production layer (CLAUDE.md, DETAIL_STANDARD rule 2) | yes |
| A 1 mm dome prints as 5 layers | "boss: diameter", 1.0 → layers_proud 5 | yes |
| Upright grooves 0.1–1.0 mm deep, all within 0.01 mm | "vertical groove 0.4 wide: depth" → 0.10, 0.19, 0.30, 0.39, 0.60, 0.79, 1.00 | yes, worst is 0.01 |
| "The nozzle places those sideways, not in steps" | an upright groove is set by the wall's XY path, which isn't rounded to layers | yes (how the measurement works) |
| "Fine detail: run it up the face" / "heights on the 0.2 mm grid" | DETAIL_STANDARD.md rules 1 and 2, approved by Scott 2026-10-30 | yes |

## Left out on purpose
- **Ridges.** DETAIL_STANDARD.md says a 0.3 mm square ridge prints 0.2. In today's re-slice the
  ridge rows read 1 layer but sum to odd heights (0.16, 0.36 for three layers). Until that's
  understood, no ridge numbers go in a post.
- **"Your printer can't"** or anything about real printed plastic. The numbers are about the
  toolpath.
- **Brand claims.** No slicer is named on screen. The coupon was sliced in PrusaSlicer for the
  measurement. Bambu Studio rounds to layers the same way, but we haven't measured it.

## Not for this lesson, but true and ours
Bambu Studio 3-wall slices of our own models are in each model's printing notes, if a later
lesson needs a time or a weight.
