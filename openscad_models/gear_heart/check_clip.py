#!/usr/bin/env python3
"""Gear Heart clips v2: the test print's fit, on the exported parts (2026-11-14).

For each of the three pins (barb 0.45, 0.55, 0.65):
- the pin seated in the base (head in its pocket) touches nothing;
- the gear on its washer, under the barb, touches nothing;
- the gear lifted 1.0 hits the barbs: it's held;
- the pin's head meets the pocket's roof within 0.6 of lift: it can't pull up through the plate;
- the gear turned 360 deg in 10 deg steps touches nothing: it spins free.

    python3 check_clip.py      (writes checks/fit_clip.txt)
"""
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
LIBS = HERE.parents[1] / "assets" / "openscad_libs"
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def scad(body, name):
    with tempfile.TemporaryDirectory() as td:
        src = Path(td) / "m.scad"
        stl = HERE / "parts" / "clip" / f"{name}.stl"
        src.write_text(f'include <{HERE / "pin_lib.scad"}>\n{body}\n')
        subprocess.run(["openscad", "-o", str(stl), str(src)], capture_output=True,
                       env={"OPENSCADPATH": str(LIBS), "PATH": "/usr/bin:/bin"}, timeout=1200)
        m = trimesh.load(stl)
        m.export(stl)          # binary (the repo's STLs are binary: test_stls_are_binary)
        return m


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def ov(a, b):
    return (man(a) ^ man(b)).volume()


def moved(m, dz=0.0, deg=0.0, x=0.0):
    t = trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1], [x, 0, 0])
    t[2, 3] = dz
    return m.copy().apply_transform(t)


def main():
    base = trimesh.load(HERE / "parts" / "clip" / "base.stl")
    out.append("GEAR HEART CLIPS V2: TEST PRINT FIT (exported parts)")
    for i, barb in enumerate((0.45, 0.55, 0.65)):
        x = i * 26
        pin = scad(f"translate([{x}, 0, 0]) pin_use(8, 6, {barb});", f"pin_use_{i}")
        gear = scad(f"translate([{x}, 0, 9]) gear(1.5, 12, 6, bore_d());", f"gear_use_{i}")
        out.append(f"== pin {i + 1} (barb {barb})")
        check(ov(pin, base) < 0.01, f"seated in the base: {ov(pin, base):.3f} mm3")
        check(ov(gear, pin) < 0.01 and ov(gear, base) < 0.01,
              f"gear on its washer: {ov(gear, pin):.3f} mm3 with the pin, {ov(gear, base):.3f} with the base")
        up = ov(moved(gear, 1.0), pin)
        check(up > 1.0, f"gear lifted 1.0 hits the barbs: {up:.1f} mm3 (held)")
        lo, hi = 0.0, 1.5      # the lift at which the head meets the pocket's roof
        for _ in range(12):
            mid = (lo + hi) / 2
            lo, hi = (lo, mid) if ov(moved(pin, mid), base) > 0.01 else (mid, hi)
        check(hi < 0.6, f"pin lifted {hi:.2f} meets the pocket's roof: it can't pull up through the plate "
                        f"(end play {hi:.2f}, gear end play {hi + 0.35:.2f})")
        spin = max(ov(moved(gear, deg=d, x=x), pin) for d in range(0, 360, 10))
        check(spin < 0.01, f"gear turned through 360 deg: at most {spin:.3f} mm3 (spins free)")
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_clip.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
