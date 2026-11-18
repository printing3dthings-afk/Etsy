# FACTS: Snow Globe Name Ornament, v1

Every number comes from this folder. The source is on each line (STANDARDS 15).

## Version
- **v1**, 2026-11-18. Scott's pick, form 5 of 5, to replace the domed Name Ornament.
- **Not printed yet.** Scott is test printing it (2026-11-18). Every image is a
  design-review render, not a photo.

## What it is
- **A flat snow globe on its base.**
- **On night-blue glass:** a village cottage, a tree with a star, a moon, falling snow and
  a drift.
- **On the base:** the name and year, raised.
- **The OBC mark** is engraved on the back, reading when it's turned over on its loop.

## Numbers
| what | value | source |
|---|---|---|
| Size | 62 × 93 × 3.2 mm with the loop | `NAME_GLOBE_PRINTING.md`; `name_globe_union.stl` |
| Hanging hole | 4.4 mm | `name_globe.scad` (LOOP_RI 2.2) |
| Name | Lobster, as large as fits 46 mm, at most 11 mm; raised 0.8 mm | `name_globe.scad` |
| Colours | 3: frame red `#C62F3A`, glass night blue `#2F4B7C`, snow white `#F4F1EA` | `NAME_GLOBE_PRINTING.md` |

## Print time and filament
- **Bambu Studio's own slice:** P1S 0.4, PLA Basic, 0.20 mm Standard, 3 walls, 15% infill,
  supports off.
- **`gcode/name_globe_three_colour.gcode.3mf`: 1 h 4 m, 17.1 g** (8.3 g red, 4.5 g blue,
  4.3 g white). It opens in Bambu Handy.
- These are Claude's settings. Re-slice on Benson's profile when it's on main (OPEN row 20).

## Checks (`logs/`)
- **Product gate: PASS.**
- **Print fidelity:** 0 flagged.
- **Fragility:** 0 high, 0 watch.
- **Silhouette:** clean on the frame (`NAME_GLOBE_PRINTING.md`).

## MakerWorld customizer
- **`pmm/name_globe_pmm.scad`.**
- **Checked here:** six names build and fit on the base.
- **Not checked:** PMM's speed. The profile needs **Auto Arrangement on**.

## Free or paid, per platform
- **Not decided.** Scott's call. Until his test print is checked, private only.

## Safe to say, word for word
- "A personalised snow globe ornament: a snowy village scene on the glass, your name and
  year on the base."
- "Three colours, printed flat, no supports."

## Don't say
- That it's printed or tested. Not yet.
- That the glass is clear or see-through: it's an opaque blue disc. A translucent filament
  is an option for the buyer, untested.

## Media
| file | shows | version |
|---|---|---|
| `images/name_globe_colour_top.png` | front, colour render, "Olivia 2026" | v1 |
| `images/name_globe_colour_three_quarter.png` | angle, render | v1 |
| `images/name_globe_as_printed_*.png` | rendered from the slice's toolpath | v1 |

## Light fit
- Not a light piece.
