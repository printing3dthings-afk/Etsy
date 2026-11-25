"""Hole Shrink Ladder: base plate 148x76x5 with through-holes and matching
solid bosses/pegs at O2,3,4,5,6,8,10 mm, each labelled with its designed size."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textgeom as tg

DIAMS = [2, 3, 4, 5, 6, 8, 10]
PITCH = 20.0
plate = tg.box(148, 76, 5)
tools = []
for i, d in enumerate(DIAMS):
    x = (i - 3) * PITCH
    tools.append(tg.cyl(d / 2.0, 7, cx=x, cy=19, zbot=-1))          # through-hole
    plate = tg.union([plate, tg.cyl(d / 2.0, 8, cx=x, cy=-19, zbot=5)])  # boss/peg
plate = tg.difference(plate, tools)
for i, d in enumerate(DIAMS):
    x = (i - 3) * PITCH
    plate = tg.engrave(plate, str(d), 6.0, x, 5.5, 5.0)    # hole label
    plate = tg.engrave(plate, str(d), 6.0, x, -5.5, 5.0)   # peg label
tg.check(plate, 'HoleShrinkLadder')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'HoleShrinkLadder.stl')
plate.export(out)
print('wrote', out)
