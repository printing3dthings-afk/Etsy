#!/usr/bin/env python3
"""Bayonet Jar v3: export every size and check each one's fit on the exported parts
(2026-11-10). One lid per diameter fits every height of that diameter.

For each size, with the lid posed as it really moves:
  - locked: nothing overlaps; lifted 0.3 mm the pins hit the channel ceilings (captured);
  - going on: lined up at the entry, the lid drops the full travel onto the rim untouched;
  - closing: from the entry it turns CLOCKWISE (seen from above) to locked untouched,
    its cap on the rim while the ramp closes the ceiling onto the pins;
  - the other way: from the entry, turned 8 deg counter-clockwise, the pins hit (so it
    can only close clockwise);
  - past locked: turned 8 deg further clockwise, the channel's end stops it.

    python3 build_sizes.py            (export + check every size)
    python3 build_sizes.py --check    (check the parts already exported)
"""
import math
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
SCAD = HERE / "bayonet_jar_v3.scad"
PARTS = HERE / "parts"
ROOT = HERE.parents[2]
DIAMETERS = (40, 50, 65, 80)
HEIGHTS = (30, 45, 70, 100)
SRC = SCAD.read_text()
V = {k: float(v) for k, v in re.findall(r"^(\w+)\s*= ([0-9.]+);", SRC, re.M)}
LOCK, TRAVEL, RAMP, MARGIN = V["lock_angle"], V["travel_v"], V["ramp_drop"], V["lock_stop_margin"]
TWIST = -1 if re.search(r"^twist = -1;", SRC, re.M) else 1


def export(part, d, h, out):
    env = dict(os.environ, OPENSCADPATH=str(ROOT / "assets" / "openscad_libs"))
    r = subprocess.run(["openscad", "-o", str(out), "-D", f'part="{part}"', "-D", f"D={d}", "-D", f"H={h}", str(SCAD)],
                       capture_output=True, text=True, env=env)
    if r.returncode or not out.exists():
        raise RuntimeError(f"{out.name}: {r.stderr[-400:]}")
    return out


def jobs():
    j = []
    for d in DIAMETERS:
        j.append(("lid", d, 45, PARTS / f"lid_D{d}.stl"))
        for h in HEIGHTS:
            j.append(("base", d, h, PARTS / f"base_D{d}_H{h}.stl"))
            j.append(("lid_assembled", d, h, PARTS / f"lidA_D{d}_H{h}.stl"))
    return j


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def pose(lid, turn, dz):
    """turn in degrees about +Z (counter-clockwise seen from above), relative to locked."""
    t = trimesh.transformations.rotation_matrix(math.radians(turn), [0, 0, 1])
    t[2, 3] = dz
    return man(lid.copy().apply_transform(t))


def check_size(d, h):
    base = man(trimesh.load(PARTS / f"base_D{d}_H{h}.stl"))
    lid = trimesh.load(PARTS / f"lidA_D{d}_H{h}.stl")
    ov = lambda turn, dz: (pose(lid, turn, dz) ^ base).volume()
    out = []
    # the entry, in the locked lid's frame: locked is at twist*LOCK, the entry at 0
    entry = -TWIST * LOCK
    # going on: lined up at the entry, the lid drops until its cap sits on the rim
    drop = max(ov(entry, 0.01 + z) for z in np.linspace(0, TRAVEL + 3, 12))
    out.append((drop < 0.01, f"drops on at the entry untouched ({drop:.3f} mm3)"))
    # closing: the cap stays on the rim while the channel ceiling closes 0.35 -> 0 on the pins
    turn = max(ov(entry * (1 - f), 0.01) for f in np.linspace(0, 1, 21))
    cw = TWIST < 0
    out.append((turn < 0.01, f"turns {'clockwise' if cw else 'counter-clockwise'} to locked untouched ({turn:.3f} mm3)"))
    locked = ov(0, 0)
    out.append((locked < 0.01, f"locked, nothing overlaps ({locked:.3f} mm3)"))
    lift = ov(0, 0.3)
    out.append((lift > 0.01, f"locked, lifted 0.3 the pins hit the channel ceilings ({lift:.2f} mm3): no free lift"))
    wrong = ov(entry - TWIST * 8, 0.01)
    out.append((wrong > 0.5, f"from the entry, turned 8 deg the wrong way it hits ({wrong:.1f} mm3)"))
    past = ov(TWIST * 8, 0.01)
    out.append((past > 0.5, f"8 deg past locked the channel's end stops it ({past:.1f} mm3)"))
    return out


def main():
    PARTS.mkdir(exist_ok=True)
    if "--check" not in sys.argv:
        with ThreadPoolExecutor(4) as ex:
            for p in ex.map(lambda a: export(*a), jobs()):
                print("  exported", p.name, flush=True)
    fails = []
    for d in DIAMETERS:
        for h in HEIGHTS:
            print(f"== D{d} H{h}")
            for ok, msg in check_size(d, h):
                print(("  ok   " if ok else "  FAIL ") + msg)
                if not ok:
                    fails.append(f"D{d} H{h}: {msg}")
    print("\nBAYONET JAR v3 " + ("FAILED:\n  " + "\n  ".join(fails) if fails else "OK, every size"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
