"""Magnet Pocket Fit Test: 110 x 108 x 5 mm plate, blind pockets from the top.
Rows = magnet sizes (6x2, 6x3, 8x2, 10x2 round, 10x5x2 bar); columns = the
clearance ladder +0.2 / +0.3 / +0.4 / +0.5 mm added to the magnet's nominal
diameter (both dimensions for the bar). Pocket depth = magnet height + 0.2.
Row and column labels engraved on the plate. Magnets are NOT included -
Scott supplies his own; sizes are printed on the plate."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import textgeom as tg

PLATE = (110.0, 108.0, 5.0)
CLEARS = [0.2, 0.3, 0.4, 0.5]
COL_X = [-33.0, -11.0, 11.0, 33.0]
# (row label, kind, nominal dims, magnet height, row y)
ROWS = [('6X2', 'round', 6.0, 2.0, 40.0),
        ('6X3', 'round', 6.0, 3.0, 20.0),
        ('8X2', 'round', 8.0, 2.0, 0.0),
        ('10X2', 'round', 10.0, 2.0, -20.0),
        ('BAR', 'bar', (10.0, 5.0), 2.0, -40.0)]

plate = tg.box(*PLATE)
tools = []
for label, kind, dims, mh, ry in ROWS:
    depth = mh + 0.2
    for c, cx in zip(CLEARS, COL_X):
        if kind == 'round':
            tools.append(tg.cyl((dims + c) / 2.0, depth + 1.0, cx=cx, cy=ry,
                                zbot=PLATE[2] - depth, sections=72))
        else:
            tools.append(tg.box(dims[0] + c, dims[1] + c, depth + 1.0,
                                cx=cx, cy=ry, zbot=PLATE[2] - depth))
plate = tg.difference(plate, tools)
for label, kind, dims, mh, ry in ROWS:
    plate = tg.engrave(plate, label, 3.5, -46.0, ry, PLATE[2])
for c, cx in zip(CLEARS, COL_X):
    plate = tg.engrave(plate, '+%.1f' % c, 3.5, cx, -50.0, PLATE[2])
tg.check(plate, 'MagnetPocketFitTest')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'MagnetPocketFitTest.stl')
plate.export(out)
print('wrote', out)
