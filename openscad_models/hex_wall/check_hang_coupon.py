#!/usr/bin/env python3
"""Hex Wall Tiles hang test print, checked on the exported parts (2026-11-10): each
module hung on the tile's rail. Hung, nothing overlaps; pulled straight off the wall
1 mm it hits the rail's lips (the dovetail holds it); lifted 6 mm it still can't come
off forward; lifted clear of the rail it comes off.

    python3 check_hang_coupon.py
"""
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (HERE / "hang_coupon.scad").read_text())}
fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    fail.append(msg) if not ok else None


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


tile = trimesh.load(HERE / "parts/tile.stl")
tm = man(tile)
y_hung = V["RAIL_Y0"] + V["RAIL_L"] - V["SLOT_LEN"]
for C in (0.2, 0.3):
    mod = trimesh.load(HERE / f"parts/module_{C}.stl")
    at = lambda dy, dz: man(mod.copy().apply_translation([0, y_hung + dy, V["T"] + dz]))
    print(f"== module with {C} clearance")
    hung = (at(0, 0) ^ tm).volume()
    check(hung < 0.01, f"hung on the rail: overlap {hung:.3f} mm3")
    m = mod.copy().apply_translation([0, y_hung, V["T"]])
    # the back lies on the tile's face and the slot's top end on the rail's: designed
    # contacts. The gap that matters is at the dovetail's flanks, mid-depth
    pts = m.sample(60000, seed=1)
    band = pts[(pts[:, 2] > V["T"] + 0.5) & (pts[:, 2] < V["T"] + V["RAIL_H"] - 0.5) & (np.abs(pts[:, 0]) < 12)
               & (pts[:, 1] < y_hung + V["SLOT_LEN"] - 0.5)]
    d = -trimesh.proximity.ProximityQuery(tile).signed_distance(band)
    check(d.min() > 0.1, f"gap at the dovetail's flanks {d.min():.2f} (C cos 30 = {C * np.cos(np.radians(30)):.2f}); "
          "the back on the tile's face and the slot's end on the rail's are the designed contacts")
    off = (at(0, 1.0) ^ tm).volume()
    check(off > 1, f"pulled 1 mm straight off the wall it hits the rail's lips ({off:.1f} mm3)")
    up = (at(6, 1.0) ^ tm).volume()
    check(up > 1, f"lifted 6 mm, it still can't come off forward ({up:.1f} mm3)")
    clear = (at(V["RAIL_L"] + 1, 5) ^ tm).volume()
    check(clear < 0.01, f"lifted clear of the rail it comes off ({clear:.3f} mm3)")
print("\nHANG COUPON " + ("FAILED" if fail else "OK"))
sys.exit(1 if fail else 0)
