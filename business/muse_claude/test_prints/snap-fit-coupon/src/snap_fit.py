"""Snap-Fit Coupon: base plate + back rail, five cantilever arms printed flat
(flexing in the layer plane), each tip hook printed ENGAGED in a notch in a
catch block beside the tip (0.3 mm gaps, not fused). The hook penetrates the
notch by PEN = 1.3 mm, so the tip must deflect 1.3 mm sideways to release.
Arm strain by the prismatic formula eps = 1.5*h*y/L^2 (h = root thickness in
the bend direction, y = 1.3, L = arm length). Arms taper to 55% at the tip;
root fillets r = 0.6*h (>= the 0.5t rule). Strain ladder 0.8 / 1.2 / 1.6 /
2.0 / 2.5 % — PLA repeated-use limit 1.2%, single-snap limit 2.0%."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, trimesh
from shapely.geometry import Polygon
import textgeom as tg

PEN = 1.3            # hook penetration into the notch = release deflection
GAP = 0.3            # printed clearance: arm face<->block face, hook in notch
ARM_Z = (4.0, 10.0)  # arms/rail/blocks stand on the 4 mm plate, 6 mm tall
RAIL_Y = 14.0        # rail front face; arms extend toward -Y from here

# (label, L mm, h mm root thickness) -> strain %
ARMS = [('L22 0.8%', 22.0, 2.0),
        ('L18 1.2%', 18.0, 2.0),
        ('L15 1.6%', 15.0, 1.8),
        ('L14 2.0%', 14.0, 2.0),
        ('L13 2.5%', 13.0, 2.2)]
PITCH = 31.0

def strain_pct(h, L):
    return 100.0 * 1.5 * h * PEN / (L * L)

def half_w(h, L, y):
    """Arm half width at station coordinate y (y=RAIL_Y at the root)."""
    frac = (RAIL_Y - y) / L
    return (h / 2.0) * (1.0 - 0.45 * frac)   # taper to 55% at tip

def station_dims(xc, L, h):
    tip_y = RAIL_Y - L
    hw_tip = half_w(h, L, tip_y)
    hw_max = half_w(h, L, min(tip_y + 9.0, RAIL_Y))  # widest arm point beside block
    bx0 = xc + hw_max + GAP                          # catch block inner face
    hook_outer = bx0 + PEN                           # hook reaches PEN into notch
    return tip_y, hw_tip, bx0, hook_outer

def arm_mesh(xc, L, h):
    tip_y, hw_tip, bx0, hook_outer = station_dims(xc, L, h)
    hook_top_y = tip_y + 4.0
    hw_hook = half_w(h, L, hook_top_y)
    pts = [(xc - h / 2.0, RAIL_Y + 0.6),          # root left (embedded in rail)
           (xc - hw_tip, tip_y),                   # tip left
           (hook_outer, tip_y),                    # hook outer, tip face
           (hook_outer, hook_top_y),               # hook outer, top
           (xc + hw_hook, hook_top_y),             # hook step back to arm face
           (xc + h / 2.0, RAIL_Y + 0.6)]           # root right
    m = trimesh.creation.extrude_polygon(Polygon(pts), height=ARM_Z[1] - ARM_Z[0])
    m.apply_translation([0, 0, ARM_Z[0]])
    r = max(0.6 * h, 1.0)                          # root fillet >= 0.5t
    fils = [tg.cyl(r, ARM_Z[1] - ARM_Z[0], cx=xc + sx * h / 2.0, cy=RAIL_Y,
                   zbot=ARM_Z[0], sections=36) for sx in (-1, 1)]
    return tg.union([m] + fils)

def pocket_mesh(xc, L, h):
    """Catch block; notch on its -X face holds the hook with GAP to spare."""
    tip_y, hw_tip, bx0, hook_outer = station_dims(xc, L, h)
    bx1 = bx0 + 7.0
    by0, by1 = tip_y - 5.0, tip_y + 9.0
    block = tg.box(bx1 - bx0, by1 - by0, ARM_Z[1] - ARM_Z[0],
                   cx=(bx0 + bx1) / 2.0, cy=(by0 + by1) / 2.0, zbot=ARM_Z[0])
    nw = PEN + GAP + 0.02                          # notch depth into the block
    notch = tg.box(nw, 4.0 + 2 * GAP, ARM_Z[1] - ARM_Z[0] + 2,
                   cx=bx0 - 0.01 + nw / 2.0, cy=tip_y + 2.0, zbot=ARM_Z[0] - 1)
    return tg.difference(block, [notch])

parts = [tg.box(168, 62, 4)]                                   # base plate
parts.append(tg.box(168, 13.5, ARM_Z[1] - ARM_Z[0], cx=0, cy=RAIL_Y + 6.5, zbot=ARM_Z[0]))  # rail
labels = []
for i, (label, L, h) in enumerate(ARMS):
    xc = (i - 2) * PITCH
    eps = strain_pct(h, L)
    want = float(label.split()[-1].rstrip('%'))
    print('%s: L=%.0f h=%.1f strain=%.2f%% (label %.1f%%)' % (label, L, h, eps, want))
    assert abs(eps - want) < 0.06, label
    parts.append(arm_mesh(xc, L, h))
    parts.append(pocket_mesh(xc, L, h))
    labels.append((label, xc))
plate = tg.union(parts)
for label, xc in labels:
    plate = tg.engrave(plate, label, 4.2, xc, -22.0, 4.0)
tg.check(plate, 'SnapFitCoupon')
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'SnapFitCoupon.stl')
plate.export(out)
print('wrote', out)
