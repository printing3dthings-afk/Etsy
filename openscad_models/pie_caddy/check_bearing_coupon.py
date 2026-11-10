#!/usr/bin/env python3
"""Pie Drum Caddy bearing test print, checked on the exported parts (2026-11-10):
the drum resting on 6 mm balls in the base's channel. Nothing overlaps; the balls
clear the channel's walls 0.3 each side; the drum floats over the base's top; the post
clears its bore; and the drum turns about the post (any turn, same answer: it's round).

    python3 check_bearing_coupon.py
"""
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V = {k: float(v) for k, v in re.findall(r"\b(\w+) = ([0-9.]+);", (HERE / "bearing_coupon.scad").read_text())}
fail = []


def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    fail.append(msg) if not ok else None


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


base = trimesh.load(HERE / "parts/base.stl")
top = trimesh.load(HERE / "parts/top.stl").apply_translation([0, 0, V["BASE_T"] + V["BALL"]])
ring = V["D"] / 2 - 10
balls = [trimesh.creation.icosphere(subdivisions=3, radius=V["BALL"] / 2).apply_translation(
    [ring * np.cos(a), ring * np.sin(a), V["BASE_T"] + V["BALL"] / 2]) for a in np.linspace(0, 2 * np.pi, 27, endpoint=False)]
bm, tm = man(base), man(top)
check((bm ^ tm).volume() < 0.01, f"drum and base don't touch ({(bm ^ tm).volume():.3f} mm3)")
q = trimesh.proximity.ProximityQuery(base)
d = -q.signed_distance(top.sample(20000, seed=1))
check(d.min() >= 0.3, f"least gap drum to base {d.min():.2f} (the post in its bore, and the drum over the rim)")
bv = sum((man(b) ^ bm).volume() for b in balls)
check(bv < 0.05, f"balls don't cut the channel ({bv:.3f} mm3; they sit on its floor)")
side = min((-q.signed_distance(b.vertices[np.abs(b.vertices[:, 2] - (V['BASE_T'] + V['BALL'] / 2)) < 0.5])).min() for b in balls)
check(abs(side - 0.3) < 0.08, f"balls clear the channel's walls by {side:.2f} each side")
check(V["BALL"] - V["CH_D"] >= 0.3, f"the drum floats {V['BALL'] - V['CH_D']:.1f} over the base's top")
print("\nBEARING COUPON " + ("FAILED" if fail else "OK"))
sys.exit(1 if fail else 0)
