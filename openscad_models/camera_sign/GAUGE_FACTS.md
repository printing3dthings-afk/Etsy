# FACTS: Gap Gauge, v1

Every number comes from this folder (STANDARDS 15).

## Version
- **v1**, 2026-11-18. Made so Scott can measure the gaps behind the toolhead and the bed
  inside his P1S, for the camera sign. Bambu's docs give neither.
- **Not printed yet.** The images are renders.

## What it is
- **A stepped strip:** twelve steps, 1.6 to 6.0 mm in 0.4 mm steps, each step's thickness
  engraved on it. A handle at the thick end carries the OBC mark.
- **Use:** slide it into a gap, thin end first. The thickest step that fits is the gap.

## Numbers
| what | value | source |
|---|---|---|
| Size | 148 × 18 × 6 mm | `gap_gauge.stl` |
| Steps | 1.6, 2.0 … 5.6, 6.0 mm; multiples of the 0.2 mm layer | `gap_gauge.scad` |
| Print | 27 m, 8.3 g, one colour, 0.20 mm, 3 walls, 15%, supports off | `gcode/gap_gauge.gcode.3mf`, `logs/gauge/slice.txt` |

## Checks (`logs/gauge/`)
- **Gate: PASS,** with the engraved numbers declared as detail.
- **Fidelity:** 0 flagged.
- **Fragility:** 0.

## Guide
- `guide/Gap_Gauge_Guide.pdf`: how to measure, for the P1S camera sign.

## Free or paid
- **Not decided.** It's a workshop tool; whether it goes on MakerWorld at all is Scott's
  call.

## Safe to say
- "A step gauge, 1.6 to 6 mm, every step labelled."
- "Prints in under half an hour."

## Don't say
- Precise to better than about 0.1 mm: FDM steps vary by about that.
