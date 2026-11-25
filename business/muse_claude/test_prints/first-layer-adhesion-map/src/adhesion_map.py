"""First-Layer Adhesion Map: 10x10 grid of 20x20x0.6 mm squares at 24 mm
pitch covering the printable area of the 256 mm P1S plate. A thin rail
along the front edge and a hole in the front-left square mark orientation.
The front-left square is shifted +10 mm in X and the rail starts at plate
x=22 so nothing enters the P1S bed exclusion zone (18x28 mm, front-left) --
that corner physically cannot print, so the map starts beside it."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textgeom as tg

parts = []
centres = [-108 + 24 * i for i in range(10)]
for cx in centres:
    for cy in centres:
        x = cx + 10 if (cx == -108 and cy == -108) else cx  # clear exclusion zone
        parts.append(tg.box(20, 20, 0.6, cx=x, cy=cy, zbot=0))
parts.append(tg.box(224, 3, 0.6, cx=6, cy=-122, zbot=0))  # front rail, starts plate x=22
m = tg.union(parts)
m = tg.difference(m, [tg.cyl(4, 2.6, cx=-98, cy=-108, zbot=-1)])  # front-left marker hole
tg.check(m, 'FirstLayerAdhesionMap')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'FirstLayerAdhesionMap.stl')
m.export(out)
print('wrote', out)
