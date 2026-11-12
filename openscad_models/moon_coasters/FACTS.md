# FACTS: Moon Phase Coasters, v1

Every number is from this folder's checks; the source is on each line.

## Version
- **v1**, 2026-11-11. The first version; nothing replaced.
- **Not printed yet.** Every image is a render or a toolpath simulation.

## What it is
Four coasters showing the moon's phases (waxing crescent, first quarter, waxing
gibbous, full), and a rack: a navy base with four curved cradles, and a night-sky
arch panel with cream stars whose round window frames the front coaster's moon.

## Numbers
| what | value | source |
|---|---|---|
| Coaster | 92 mm across, 4.8 mm thick (a 0.8 mm rim around the face) | `moon_coasters.scad` |
| Rack | base 104 × 42 × 16 mm, arch panel 96 × 94 × 3 mm; stands about 98 mm tall | `moon_coasters.scad` |
| Gap between coasters in the rack | 3.2 mm | `checks/fit.txt` |
| Coasters, two per plate | about 2 h 2 m a plate; navy 33.8 g, cream 3.6-5.6 g, slate 1.7-3.6 g | `checks/slices.txt` |
| Rack | 2 h 2 m; navy 41.1 g, cream 3.2 g | `checks/slices.txt` |
| Whole set | about 6 h 7 m, 126 g | `checks/slices.txt` |
| Settings | 0.2 mm layers, supports off, P1S 0.4 nozzle, Bambu PLA Basic profile | `checks/slices.txt` |
| Checks | product gate, print fidelity (0 flags on all six), fragility (0), fit: all pass | `checks/` |

## Free or paid, per platform
**None decided.** Scott's call.

## Safe to say, word for word
- "Four coasters, four phases of the moon."
- "The rack's window frames whichever moon you put in front."
- "Three colours, all flush: no raised edges under your cup except the rim."
- "Printed flat, no supports."

## Don't say
- That it's printed or tested (not yet).
- "Waterproof" or "heat-proof": PLA softens near 60 °C, and nobody has put a hot mug
  on one yet.
- That the phases are astronomically exact: they're drawn for the eye (the crescent
  and gibbous use a terminator 0.55 of the moon's radius).

## Media
| file (this folder) | shows | version |
|---|---|---|
| `images/moon_set_front.png` | the set in its rack, from the front | v1 |
| `images/moon_set_three_quarter.png` | three-quarter | v1 |
| `images/moon_set_top.png` | from above | v1 |
| `images/moon_coasters_row.png` | the four coasters side by side, face up | v1 |
| `images/guide_parts.png` | the six prints as they come off the plate | v1 |
| `images/guide_panel.png`, `guide_coaster.png` | putting it together | v1 |
| `images/moon_coaster_*_as_printed.png` | rendered from the sliced toolpaths | v1 |
| `Moon_Phase_Coasters_Guide.pdf` | the printing and assembly guide | v1 |

- **Missing:** a real cup on one, and the set on a table. Only a print can show that.
