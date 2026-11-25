"""Light Transmission Wedge: six steps 22 wide x 44 deep at thicknesses
0.8/1.2/1.6/2.0/2.4/3.0 mm, each tread labelled. Slide across a phone
flashlight or tea light and compare backlight brightness per thickness."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textgeom as tg

THICK = [0.8, 1.2, 1.6, 2.0, 2.4, 3.0]
W, D = 22.0, 44.0
parts = []
for i, t in enumerate(THICK):
    cx = -66 + W / 2 + i * W
    parts.append(tg.box(W, D, t, cx=cx, cy=0, zbot=0))
wedge = tg.union(parts)
for i, t in enumerate(THICK):
    cx = -66 + W / 2 + i * W
    wedge = tg.engrave(wedge, str(t), 5.5, cx, 0, t, depth=0.45)
tg.check(wedge, 'LightTransmissionWedge')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'LightTransmissionWedge.stl')
wedge.export(out)
print('wrote', out)
