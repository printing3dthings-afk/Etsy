#!/usr/bin/env python3
"""Fit check for the whole Gear Heart, on the exported gears (parts/heart_gear/g*.stl,
each in its own frame) placed as heart.scad places them, and the exported plate:

  loop     the teeth close round the ring (layout.json's phase error)
  turn     the knob turned through two of its teeth in 1 deg steps, every gear turning
           at its ratio: no meshing pair overlaps at any step, and the smallest gap
           between their teeth (cross-sections at mid-gear)
  engaged  each mesh, turned back past its backlash, does collide: it really meshes
  clear    gears that don't mesh never come within 1 mm, at any step
  knob     the knob (above the centre gear) never touches the top gear, in 3D
  plate    no gear touches the plate, the posts or the washers' rims, at rest

    python3 check_heart.py      (writes checks/fit_heart.txt)
"""
import json
import math
from pathlib import Path

import manifold3d as mf
import numpy as np
import trimesh
from shapely import affinity
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent
PLATE_T, WASHER, GEAR_T = 8.0, 1.0, 6.0


def M(m):
    return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                               tri_verts=np.asarray(m.faces, np.uint32)))


def section(mesh, z):
    s = mesh.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
    p2, to3 = s.to_2D()
    return affinity.translate(unary_union(list(p2.polygons_full)), to3[0, 3], to3[1, 3])


def main():
    d = json.loads((HERE / "layout.json").read_text())
    gears = d["gears"]
    n = len(gears)
    names = [g["name"] for g in gears]
    per = max(int(x[5:]) for x in names if x.startswith("right"))
    loop = ["top"] + [f"right{i}" for i in range(1, per + 1)] + ["bottom"] + [f"left{i}" for i in range(per, 0, -1)]
    knob = names.index("knob")
    # the direction each turns: the knob +, the top gear -, then alternating round the loop
    sign = {knob: 1}
    for k, nm in enumerate(loop):
        sign[names.index(nm)] = -1 if k % 2 == 0 else 1
    meshes = {frozenset((names.index(a), names.index(b))) for a, b in
              [("top", "right1"), ("top", "left1"), ("knob", "top")] +
              [(f"right{i}", f"right{i + 1}") for i in range(1, per)] + [(f"left{i}", f"left{i + 1}") for i in range(1, per)] +
              [(f"right{per}", "bottom"), (f"left{per}", "bottom")]}
    meshes_l = sorted(tuple(sorted(m)) for m in meshes)
    local = [trimesh.load(HERE / "parts" / "heart_gear" / f"g{i}.stl") for i in range(n)]
    sec = [section(m, GEAR_T / 2) for m in local]
    zk = gears[knob]["z"]

    def placed(i, t):
        a = gears[i]["phase"] + sign[i] * t * zk / gears[i]["z"]
        return affinity.translate(affinity.rotate(sec[i], a, origin=(0, 0)), *gears[i]["at"])

    out = ["GEAR HEART: FIT CHECK (exported gears and plate)"]
    ok = abs(d["phase_error_mm"]) < 0.02
    out.append(f"loop: the ring's teeth close with a phase error of {d['phase_error_mm']:+.4f} mm "
               f"(the bottom gear {d['bottom_dy']:+.2f} mm up the axis) -> {'ok' if ok else 'FAIL'}")
    worst_ov, min_gap, worst_clear = 0.0, {m: 9.0 for m in meshes_l}, 99.0
    for t in np.arange(0, 2 * 360 / zk + 0.01, 1.0):
        P = [placed(i, t) for i in range(n)]
        for a, b in meshes_l:
            ov = P[a].intersection(P[b]).area
            worst_ov = max(worst_ov, ov)
            min_gap[(a, b)] = min(min_gap[(a, b)], P[a].distance(P[b]))
        for a in range(n):
            for b in range(a + 1, n):
                if (a, b) not in meshes:
                    if frozenset((a, b)) not in meshes:
                        worst_clear = min(worst_clear, P[a].distance(P[b]))
    turn_ok = worst_ov < 1e-3
    ok &= turn_ok
    out.append(f"turn: knob through {2 * 360 / zk:.1f} deg in 1 deg steps, all {n} gears at their ratios: "
               f"largest overlap between meshing gears {worst_ov:.4f} mm2 -> {'ok' if turn_ok else 'FAIL'}")
    out.append(f"  smallest gap between meshing teeth through the turn: {min(min_gap.values()):.3f} mm "
               f"(largest {max(min_gap.values()):.3f})")
    # engaged: hold one gear of each mesh and turn the other back past its backlash
    eng_bad = []
    for a, b in meshes_l:
        Pa = placed(a, 0)
        hit = False
        for back in (1.5, -1.5):
            Pb = affinity.rotate(placed(b, 0), back, origin=tuple(gears[b]["at"]))
            if Pa.intersection(Pb).area > 1e-3:
                hit = True
        if not hit:
            eng_bad.append((names[a], names[b]))
    ok &= not eng_bad
    out.append(f"engaged: each of {len(meshes_l)} meshes collides when one gear is turned 1.5 deg either way against "
               f"the other -> {'ok' if not eng_bad else 'FAIL ' + str(eng_bad)}")
    ok &= worst_clear >= 1.0
    out.append(f"clear: gears that don't mesh stay {worst_clear:.2f} mm apart at the closest, through the turn "
               f"-> {'ok' if worst_clear >= 1.0 else 'FAIL'}")
    # knob vs the top gear, in 3D, through the turn
    top = names.index("top")

    def posed3d(i, t):
        a = gears[i]["phase"] + sign[i] * t * zk / gears[i]["z"]
        x, y = gears[i]["at"]
        return M(local[i]).rotate([0, 0, a]).translate([x, y, PLATE_T + WASHER])
    knob_hit = max((posed3d(knob, t) ^ posed3d(top, t)).volume() for t in np.arange(0, 2 * 360 / zk + 0.01, 3.0))
    ok &= knob_hit < 1e-3
    out.append(f"knob: knob gear and its heart against the top gear in 3D, through the turn: overlap "
               f"{knob_hit:.4f} mm3 -> {'ok' if knob_hit < 1e-3 else 'FAIL'}")
    plate = M(trimesh.load(HERE / "parts" / "heart_plate.stl"))
    pl = sum((plate ^ posed3d(i, 0)).volume() for i in range(n))
    ok &= pl < 1e-3
    out.append(f"plate: all gears against the plate, posts and washers at rest: overlap {pl:.4f} mm3 "
               f"-> {'ok' if pl < 1e-3 else 'FAIL'}")
    out.append("PASS" if ok else "FAIL")
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_heart.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
