#!/usr/bin/env python3
"""Find slender parts of a model that will print but snap in the hand.

    python3 tools/fragility.py part1.stl part2.stl ...     # all parts of one model

Scott's first haunted chapel printed with every exterior detail right, and its
window bars broke: bars 1.2 mm square standing free across the openings. The
slicer made them perfectly -- tools/print_fidelity.py would have passed them --
and a render shows them as crisp as the walls. Nothing checked whether a
feature is strong enough to be handled, packed and shipped.

How it finds them: cut the model with planes across each of X, Y and Z. A
bar crossing a plane cuts to a small, compact island of its own, while a wall
cuts to a long strip joined to everything around it. Islands that repeat on
consecutive planes, one after another, are a slender member running across
them; its length is how many planes it crosses, its thickness the island's
size. A bar resting on a pane, or joined along its length to a wall, never
leaves an island of its own, so it is not reported -- which is exactly the
difference between the chapel as printed and as fixed.

Slenderness = length / sqrt(cross-section area). A cone's tip crosses a few
planes with a shrinking island and scores low; a free bar scores high. FLAG
is calibrated on the chapel as printed (bars that snapped) against the same
chapel glazed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import shapely
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import print_fidelity as pf  # noqa: E402

STEP = 0.4          # mm between cutting planes
MAX_DIM = 4.0       # mm: an island longer than this across is a strip, not a bar
MAX_AREA = 8.0      # mm2: bigger than this is not slender at any length
FLAG_SLENDER = 4.0  # length / sqrt(area) at or above which a member is flagged
MIN_LENGTH = 3.0    # mm: shorter runs are nubs and tips


def _to_z(axis):
    """Transform that turns `axis` into +Z."""
    if axis == "z":
        return np.eye(4)
    if axis == "x":
        return trimesh.transformations.rotation_matrix(-np.pi / 2, [0, 1, 0])
    return trimesh.transformations.rotation_matrix(np.pi / 2, [1, 0, 0])


def islands(mesh, axis, step=STEP):
    """Small compact islands on planes across `axis`: (plane, polygon, area)."""
    T = _to_z(axis)
    m = mesh.copy()
    m.apply_transform(T)
    lo, hi = m.bounds[0][2], m.bounds[1][2]
    out = []
    for z in np.arange(lo + step / 2, hi, step):
        sec = pf.section(m, z)
        parts = pf._parts(sec)
        for i, p in enumerate(parts):
            if p.area > MAX_AREA or p.area < 1e-3:
                continue
            # Touching is joined: a section can return polygons that share an
            # edge, and those print as one piece. (The chapel tower's inside
            # corner post is NOT one of these -- it stands 9 mm clear of the
            # nave for about 15 mm and is flagged correctly.)
            if any(p.distance(q) < 0.05 for k, q in enumerate(parts) if k != i):
                continue
            rect = p.minimum_rotated_rectangle
            xs, ys = rect.exterior.coords.xy
            d = max(np.hypot(np.diff(xs), np.diff(ys)))
            if d <= MAX_DIM:
                out.append((z, p))
    return out, np.linalg.inv(T)


def members(mesh, axis, step=STEP):
    """Chain islands on consecutive planes into members."""
    isl, back = islands(mesh, axis, step)
    by_plane = {}
    for z, p in isl:
        by_plane.setdefault(round(z, 4), []).append(p)
    runs, prev, last_z = [], [], None
    for z in sorted(by_plane):
        # Only runs that ended on the plane just below can continue here.
        cont = prev if last_z is not None and abs(z - last_z - step) < 1e-3 else []
        now = []
        for p in by_plane[z]:
            r = next((r for r in cont if r["last"].buffer(0.2).intersects(p)), None)
            if r is None:
                r = {"z0": z, "z1": z, "areas": [], "cs": []}
                runs.append(r)
            else:
                cont.remove(r)
            r["z1"], r["last"] = z, p
            r["areas"].append(p.area)
            r["cs"].append((p.centroid.x, p.centroid.y, z))
            now.append(r)
        prev, last_z = now, z
    out = []
    for r in runs:
        length = r["z1"] - r["z0"] + step
        a = float(np.median(r["areas"]))
        if length < MIN_LENGTH:
            continue
        c = np.mean(r["cs"], axis=0)
        world = trimesh.transform_points([c], back)[0]
        out.append({
            "axis": axis, "length_mm": round(length, 1),
            "section_mm2": round(a, 2), "thinnest_mm2": round(min(r["areas"]), 2),
            "slenderness": round(length / np.sqrt(a), 1),
            "at": [round(v, 1) for v in world],
        })
    return out


def check(paths, step=STEP, log=print):
    ms = [pf._load(p) for p in paths]
    mesh = trimesh.util.concatenate(ms)
    found = []
    for axis in ("x", "y", "z"):
        found += members(mesh, axis, step)
        log(f"  {axis}: {sum(1 for f in found if f['axis'] == axis)} slender run(s)")
    for f in found:
        f["flag"] = f["slenderness"] >= FLAG_SLENDER
    found.sort(key=lambda f: -f["slenderness"])
    return found


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("parts", nargs="+", help="every part of one model, as printed together")
    ap.add_argument("--step", type=float, default=STEP)
    a = ap.parse_args(argv)
    found = check(a.parts, a.step)
    flagged = [f for f in found if f["flag"]]
    print(f"\nFRAGILITY  {len(flagged)} flagged (slenderness >= {FLAG_SLENDER}), {len(found)} slender runs")
    for f in found[:25]:
        print(f"  {'FLAG ' if f['flag'] else '     '}along {f['axis']}  {f['length_mm']:5.1f} mm long  "
              f"~{f['section_mm2']} mm2 (thinnest {f['thinnest_mm2']})  slenderness {f['slenderness']}  at {f['at']}")
    return found


if __name__ == "__main__":
    main()
