"""Bridging Span Test: two rows of posts on a base plate; horizontal bars
(5 wide x 3 thick) bridge gaps of 10/30/50 mm (front row) and 20/40/60 mm
(back row). Span labelled on the base in front of each gap."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textgeom as tg

POST_W, POST_D, POST_H, BAR_T, BAR_W = 6.0, 12.0, 11.0, 3.0, 5.0
part = tg.box(158, 66, 3)
rows = [(17.0, -57.0, [10, 30, 50], 29.5), (-17.0, -69.0, [20, 40, 60], -29.5)]
for y, x_start, gaps, label_y in rows:
    faces = [x_start]
    for g in gaps:
        faces.append(faces[-1] + POST_W + g)
    centres = []
    for fx in faces:
        cx = fx + POST_W / 2.0
        centres.append(cx)
        part = tg.union([part, tg.box(POST_W, POST_D, POST_H, cx=cx, cy=y, zbot=3)])
    for i, g in enumerate(gaps):
        c0, c1 = centres[i], centres[i + 1]
        part = tg.union([part, tg.box(c1 - c0, BAR_W, BAR_T, cx=(c0 + c1) / 2.0, cy=y, zbot=3 + POST_H)])
        part = tg.engrave(part, str(g), 6.0, (c0 + c1) / 2.0, label_y, 3.0)
tg.check(part, 'BridgingSpanTest')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'BridgingSpanTest.stl')
part.export(out)
print('wrote', out)
