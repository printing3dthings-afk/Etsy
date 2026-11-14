#!/usr/bin/env python3
"""Zero-gap joint test: the fit, on the exported parts (2026-11-14). For each turntable:
the rotor clears its ring (and its sleeve) as modelled, it can't lift out (it hits the
sleeve or the ring's V), and turned it touches nothing (it's round).

    python3 check_fit.py      (writes checks/fit.txt)
"""
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
PITCH = 34
NAMES = ["0.30 air, no sleeve", "0.45 sleeve, no air", "0.45 sleeve + 0.10 air"]


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def ov(a, b):
    return (man(a) ^ man(b)).volume()


def near(bodies, i):
    return [b for b in bodies if abs((b.bounds[0][0] + b.bounds[1][0]) / 2 - i * PITCH) < 3]


def main():
    pla = trimesh.load(HERE / "parts" / "pla.stl").split()
    sleeves = trimesh.load(HERE / "parts" / "sleeve.stl").split()
    out, fails = ["ZERO-GAP JOINT TEST: FIT (exported parts)"], []
    for i in range(3):
        grp = near(pla, i)
        rotor, ring = min(grp, key=lambda b: b.extents[0]), max(grp, key=lambda b: b.extents[0])
        sv = near(sleeves, i)
        lift = rotor.copy().apply_translation([0, 0, 0.5])
        turned = rotor.copy().apply_transform(trimesh.transformations.rotation_matrix(np.radians(37), [0, 0, 1], [i * PITCH, 0, 0]))
        clear = ov(rotor, ring)
        out.append(f"== turntable {i + 1} ({NAMES[i]})")
        out.append(f"  rotor/ring as modelled: {clear:.3f} mm3")
        ok = clear < 0.01
        held = ov(lift, ring)
        if sv:
            a, b = ov(sv[0], rotor), ov(sv[0], ring)
            out.append(f"  sleeve against rotor/ring: {a:.3f} / {b:.3f} mm3 (touching, not overlapping)")
            ok = ok and a < 0.05 and b < 0.05
            held += ov(lift, sv[0])
        out.append(f"  rotor lifted 0.5 hits the {'sleeve and ' if sv else ''}ring: {held:.1f} mm3 (held in)")
        spin = ov(turned, ring)
        out.append(f"  rotor turned 37 deg against the ring: {spin:.3f} mm3 (free)")
        if not (ok and held > 0.5 and spin < 0.01):
            fails.append(i + 1)
    out.append("PASS" if not fails else f"FAIL: turntables {fails}")
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
