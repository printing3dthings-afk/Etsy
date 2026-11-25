"""AMS Colour-Bleed Test strip: ONE object, TWO parts (dark / light),
120 x 26 x 5 mm. Layout along X:
- dark part: main block x -60..-16, plus a 12 mm island at x 26..38
  (the light part wraps the island, so every layer forces TWO
  dark->light transitions - the hardest case, twice per layer)
- light part: x -16..60 with the island cut out
The first 30 mm of light after the dark block carries shallow tick
grooves across the top every 5 mm, so the fade distance can be read off
in millimetres. "DARK" / "LIGHT" engraved on the top faces.
Exports the two part STLs + parts.json for the seed forge in the build
script (extruder 1 = dark, extruder 2 = light).
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
import textgeom as tg

H = 5.0
dark_main = tg.box(44, 26, H, cx=-38.0, cy=0.0, zbot=0.0)
dark_island = tg.box(12, 12, H, cx=32.0, cy=0.0, zbot=0.0)
dark = tg.union([dark_main, dark_island])
dark = tg.engrave(dark, 'DARK', 5.0, -38.0, 0.0, H, depth=0.6)
tg.check(dark, 'dark part')

light = tg.box(76, 26, H, cx=22.0, cy=0.0, zbot=0.0)
light = tg.difference(light, [tg.box(12.0, 12.0, H + 2, cx=32.0, cy=0.0, zbot=-1.0)])
# tick grooves across the top of the first 30 mm of light (x -16..14)
ticks = []
for i in range(7):
    x = -13.5 + 5.0 * i
    ticks.append(tg.box(0.8, 26.4, 0.5, cx=x, cy=0.0, zbot=H - 0.4))
light = tg.difference(light, ticks)
light = tg.engrave(light, 'LIGHT', 5.0, 50.0, 0.0, H, depth=0.6)
tg.check(light, 'light part')

here = os.path.dirname(os.path.abspath(__file__))
dark.export(os.path.join(here, 'PartDark.stl'))
light.export(os.path.join(here, 'PartLight.stl'))
json.dump({'parts': [{'name': 'DARK', 'extruder': 1, 'file': 'PartDark.stl'},
                     {'name': 'LIGHT', 'extruder': 2, 'file': 'PartLight.stl'}]},
          open(os.path.join(here, 'parts.json'), 'w'), indent=1)
print('wrote parts')
