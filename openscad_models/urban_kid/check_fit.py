#!/usr/bin/env python3
"""Do the Urban Kid's prints go together? (2026-11-17)

From the exported parts in assembly coordinates (parts/assembled/, the same
meshes the print-pose STLs were turned from):

  - each print is one closed body;
  - no two parts occupy the same space (every gap is CLR or more, so an
    overlap is a modelling error, not a tight fit), the cap's pin included,
    set in its two sockets;
  - each joint seats: the part above stands on the part below at its plane;
  - each peg is engaged: its volume inside the mating part's hull;
  - the chain's back lies on his chest.

    python3 check_fit.py [parts_dir]      (writes checks/fit.txt)
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1] / "tools"))
import kid as K  # noqa: E402
import sdf_figure as sf  # noqa: E402

lines, fails = [], []


def say(ok, text):
    lines.append(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    print(lines[-1])
    if not ok:
        fails.append(text)


def pin_assembled():
    """The pin, stood in its sockets: axis up through (0, 1), centred on Z_CAP."""
    m = sf.from_manifold(K.pin_solid())
    T = np.eye(4)
    T[2, 3] = -K.PIN["r"] * K.PIN["flat"]
    m.apply_transform(T)
    T = np.eye(4)
    T[:3, :3] = sf.rot("y", -90)
    m.apply_transform(T)                       # back to the axis along z, the flat on +x
    lo = m.bounds[0]
    m.apply_translation([0, 1.0, K.Z_CAP - K.PIN["half"] - lo[2]])
    return m


def main():
    parts = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "parts"
    names = ["base", "shoe_r", "shoe_l", "pants", "hoodie", "head", "cap", "chain"]
    mesh, M = {}, {}
    for n in names:
        m = trimesh.load(parts / "assembled" / f"{n}.stl", force="mesh")
        b = len(m.split(only_watertight=False))
        say(m.is_watertight and b == 1, f"{n}: one closed body ({b}), {m.volume:.0f} mm3")
        mesh[n], M[n] = m, sf.to_manifold(m)
    pin = pin_assembled()
    mesh["pin"], M["pin"] = pin, sf.to_manifold(pin)
    say(abs(pin.bounds[0][2] + K.PIN["half"] - K.Z_CAP) < 0.01, f"pin stood in its sockets, {pin.volume:.0f} mm3")
    names.append("pin")
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = (M[a] ^ M[b]).volume()
            say(v < 0.05, f"{a} and {b} overlap {v:.3f} mm3")

    # seating: the upper part's lowest point at the joint plane, and the lower part reaching it
    for lower, upper, z in (("base", "shoe_r", K.Z_BASE), ("base", "shoe_l", K.Z_BASE),
                            ("shoe_r", "pants", K.Z_ANKLE), ("pants", "hoodie", K.Z_WAIST),
                            ("hoodie", "head", K.Z_NECK), ("head", "cap", K.Z_CAP)):
        up_lo = mesh[upper].bounds[0][2]
        # the lower part's top face at the plane: its area within 0.05 of z
        sec = mesh[lower].section(plane_origin=[0, 0, z - 0.05], plane_normal=[0, 0, 1])
        area = sec.to_planar()[0].area if sec is not None else 0.0
        say(abs(up_lo - z) < 0.06 and area > 20, f"{upper} stands on {lower} at z {z:.2f}: its bottom {up_lo:.2f}, "
            f"{lower}'s section there {area:.0f} mm2")

    # pegs engaged: the added peg solids inside the mating part's hull
    add, _ = K.joints()
    pairs = {"base": ["shoe_r", "shoe_l"], "shoe_r": ["pants"], "shoe_l": ["pants"], "pants": ["hoodie"], "hoodie": ["head"]}
    for part, solids in add.items():
        for j, sol in enumerate(solids):
            v = sol.volume()
            hold = max((sol ^ sf.to_manifold(mesh[o].convex_hull)).volume() for o in pairs[part])
            # the peg starts 1 mm inside its own part: what stands above the plane
            say(hold > 0.6 * v, f"{part} peg {j + 1}: {hold:.0f} of {v:.0f} mm3 inside the part it holds")
    hold = (M["pin"] ^ sf.to_manifold(mesh["head"].convex_hull)).volume()
    hold2 = (M["pin"] ^ sf.to_manifold(mesh["cap"].convex_hull)).volume()
    say(hold > 0.4 * pin.volume and hold2 > 0.4 * pin.volume, f"pin: {hold:.0f} mm3 in the head, {hold2:.0f} in the cap")

    # the chain lies on his chest: its back within 0.2 mm of the hoodie
    ch = mesh["chain"]
    pts, fi = trimesh.sample.sample_surface(ch, 20000, seed=3)
    back = ch.face_normals[fi][:, 1] > 0.9
    _, dist, _ = trimesh.proximity.ProximityQuery(mesh["hoodie"]).on_surface(pts[back])
    near = (dist < 0.2).mean()
    say(near > 0.8, f"the chain's back on his chest: {100 * near:.0f}% within 0.2 mm (glue face)")
    lines.append(f"RESULT: {'PASS' if not fails else 'FAIL'}")
    print(lines[-1])
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "fit.txt").write_text("\n".join(lines) + "\n")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
