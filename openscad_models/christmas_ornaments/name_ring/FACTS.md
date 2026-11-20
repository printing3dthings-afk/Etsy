# FACTS: Openwork Name Ornament, v1

Every number comes from this folder. The source is on each line (STANDARDS 15).

## Version
- **v1**, 2026-11-18; boughs redrawn 2026-11-19 (four long needle pairs, Scott's ask). Scott's pick, form 1 of 5, to replace the domed Name Ornament.
  The dome's inlaid name printed lumpy on its curve ("Jessee 2026", 2026-11-18).
- **Not printed yet.** Scott's test print (sent 2026-11-18) has the earlier, shorter needles; everything else is the same. Every image is a
  design-review render, not a photo.

## What it is
- **A flat open ring** with the name and year raised on their own outline across the
  middle.
- **Above:** a star and two pine boughs. **Below:** holly with three berries. Small stars
  sit on the rim.
- **Open between,** so the tree's lights show through.
- **The OBC mark** is engraved on the back, reading when it's turned over on its loop.

## Numbers
| what | value | source |
|---|---|---|
| Size | 80 × 88 × 3.2 mm with the loop | `NAME_RING_PRINTING.md`; `name_ring_union.stl` |
| Hanging hole | 4.4 mm | `name_ring.scad` (LOOP_RI 2.2) |
| Name | Lobster, as large as fits 60 mm, at most 15 mm; raised 0.8 mm | `name_ring.scad` |
| Colours | 2: frame red `#C62F3A`, accent white `#F4F1EA` | `NAME_RING_PRINTING.md` |

## Print time and filament
- **Bambu Studio's own slice:** P1S 0.4, PLA Basic, 0.20 mm Standard, 3 walls, 15% infill,
  supports off.
- **`gcode/name_ring_two_colour.gcode.3mf`: 47 m, 11.8 g** (8.6 g red, 3.1 g white; 11.75 g in the slice). It
  opens in Bambu Handy.
- These are Claude's settings. Re-slice on Benson's profile when it's on main (OPEN row 20).

## Checks (`logs/`)
- **Product gate: PASS.**
- **Print fidelity:** 0 flagged.
- **Fragility:** 0 high, 0 watch.
- **Silhouette:** clean on the frame. Only twinning and clutter flags, which don't apply
  (`NAME_RING_PRINTING.md`).

## MakerWorld customizer
- **`pmm/name_ring_pmm.scad`.**
- **Checked here:** six names build and fit (Olivia, Jessee, Mia, Christopher, MARY-JO,
  Zoë).
- **Not checked:** PMM's generation speed. The profile needs **Auto Arrangement on**
  (`tools/pmm_build.py`, rule 3).

## Free or paid, per platform
- **Not decided.** Scott's call. Until his test print is checked, private only.

## Safe to say, word for word
- "A personalised name ornament: your name and year raised on a flat open ring, with a
  star, pine boughs and holly."
- "Two colours, printed flat, no supports."
- "80 mm across."

## Don't say
- That it's printed or tested. Not yet.
- A print time without its settings: 47 m is at 3 walls, 15% infill, 0.20 mm.

## Media
| file | shows | version |
|---|---|---|
| `images/name_ring_colour_top.png` | front, colour render, "Olivia 2026" | v1 |
| `images/name_ring_colour_three_quarter.png` | angle, render | v1 |
| `images/name_ring_as_printed_*.png` | rendered from the slice's toolpath | v1 |

## Light fit
- Not a light piece. It's open, so a tree light behind it shows through.
