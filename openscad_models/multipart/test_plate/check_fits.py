#!/usr/bin/env python3
"""Assemble each pair on the fit test plate as it is used and measure where
the parts overlap (2026-10-27). Zero means the parts clear; the detent is the
one pair meant to overlap, between notches, by the arm's 0.6 mm of travel.

    python3 check_fits.py <dir with the exported parts>

Reads <kind>_<i>.stl as build.sh writes them. Numbers are mm3.
"""
import sys
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh

D = Path(sys.argv[1] if len(sys.argv) > 1 else "parts")


def load(name):
    t = trimesh.load(D / f"{name}.stl", force="mesh")
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(t.vertices, np.float32), tri_verts=np.asarray(t.faces, np.uint32)))


def ov(a, b):
    return (a ^ b).volume()


# the plate's own numbers (fit_test_plate.scad)
GCD, GO = 22.5, [0, 0.15, 0.3]
BRC, HC = 4.1, 2 + 0.8 + 4.1
YH, YZ = 10, 3
bad = 0
for i in range(3):
    # thread: the screw's thread starts 2 up, on its flange; the nut sits there
    s = ov(load(f"screw_{i}"), load(f"nut_{i}").translate([0, 0, 2]))
    # ball: turned over and pushed home, its centre on the hollow's; and held
    # at the mouth, where it must be wider than the way in or nothing snaps
    sock = load(f"socket_{i}")
    b = load(f"ball_{i}").rotate([180, 0, 0]).translate([0, 0, 12 + HC])
    bl = ov(b, sock)
    rm = 4 - [0.4, 0.6, 0.8][i] / 2
    snap = ov(b.translate([0, 0, (BRC * BRC - rm * rm) ** 0.5]), sock)
    # gears: meshed, through a whole tooth of the small gear
    g20, g10 = load(f"gear20_{i}"), load(f"gear10_{i}")
    gm = max(ov(g20.rotate([0, 0, a]), g10.rotate([0, 0, 18 - 2 * a]).translate([GCD + GO[i], 0, 0]))
             for a in np.linspace(0, 18, 7))
    # detent: in a notch (the bump at +y, notches every 30 deg from +x), and
    # half way between two
    base, wheel = load(f"detent_base_{i}"), load(f"detent_wheel_{i}").translate([0, 0, 3])
    d_in = ov(base, wheel.rotate([0, 0, 0]))
    d_mid = ov(base, wheel.rotate([0, 0, 15]))
    # bayonet: the cap turned over, lugs over the way in, lowered from clear
    # of the ring onto it, then turned the 24 deg to the slot's end
    cap = load(f"bayonet_cap_{i}").rotate([180, 0, 0]).translate([0, 0, YH + 2])
    ring = load(f"bayonet_ring_{i}")
    y_in = max(ov(ring, cap.translate([0, 0, z])) for z in np.linspace(0, YH - YZ, 8))
    y_lock = max(ov(ring, cap.rotate([0, 0, a])) for a in np.linspace(0, 24, 9))
    print(f"clearance set {i}: thread {s:.3f}  ball {bl:.3f} (at the mouth {snap:.3f})  gears {gm:.3f}  "
          f"detent in notch {d_in:.3f} / between {d_mid:.3f}  bayonet in {y_in:.3f} / locked {y_lock:.3f}")
    bad += (s > 1e-3) + (bl > 1e-3) + (snap < 1e-3) + (gm > 1e-3) + (d_in > 1e-3) + (d_mid < 1e-3) + (y_in > 1e-3) + (y_lock > 1e-3)
print("FITS OK" if not bad else f"FITS: {bad} problem(s)")
sys.exit(1 if bad else 0)
