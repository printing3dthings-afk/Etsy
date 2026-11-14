# Trophy Rack medallion: printing

2026-11-14. Scott's photos of a Mardi Gras bead pendant, reproduced as closely as printing
allows. For Scott's own use; not a shop product, so it has no listing and no viewer entry.

## What it is

- **Shield:** a black rim with a hanging tab (2 mm hole, for a jump ring) and a yellow
  field.
- **Domes:** two domes with tips, all in skin colour. Scott's pick: no red, so it fits one
  4-slot AMS.
- **Banner:** a cream ribbon across the bottom, with tails folded behind its ends and
  notched tips. "TROPHY RACK" is raised in black and follows the banner's curve.
- **Size:** 63 mm wide, 89 mm across the ribbon tips, 18 mm thick at the tips.

`make_banner.py` writes the banner's shape and letter positions to `banner_data.scad`.
`trophy_rack.scad` is the model.

## Printing

Bambu Studio, P1S 0.4, PLA Basic, 0.20 mm Standard, Textured PEI at 55 °C, no supports.
It prints flat on its back.

| file | what |
|---|---|
| `checks/trophy_rack.gcode.3mf` | printer-ready: 2 h 54 min, about 47 g |
| `trophy_rack.3mf` | the model, to slice yourself |

| AMS slot | colour | filament |
|---|---|---|
| 1 | black `#1A1A1A` | 9.4 g |
| 2 | yellow `#E8C21A` | 4.9 g |
| 3 | skin `#E7A976` | 12.2 g |
| 4 | cream `#F2EDE2` | 20.4 g |

## Checks (`checks/`)

- **Product gate: PASS.** The raised lettering (0.8 mm above the banner) is declared as
  detail to the wall check.
- **Print fidelity: 0 flags.** Playfair Display's hairline serifs were 0.2–0.28 mm wide
  and the slice dropped them, so every stroke is grown 0.22 mm a side. The thinnest are now
  about 0.65.
- **Fragility:** 0 high, 0 watch.
- **No two colour parts overlap.**

Fixes on the way:
- The banner is 10.6 mm tall. The domes rise 7.0 mm above the field where the banner
  crosses them, and at 8.0 and 9.5 a cut face of the right dome showed above it.
- The swallowtail points are rounded to 0.8; sharp, they ran to nothing.
