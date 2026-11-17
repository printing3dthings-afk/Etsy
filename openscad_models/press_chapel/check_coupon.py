#!/usr/bin/env python3
"""Press-to-Light Chapel drop test print: the fit, on the exported parts (2026-11-17).

- the whole drop: the shaft and steeple lowered in steps, each hub turned by the helix
  (-360 x drop / LEAD), and nothing may touch: not the hub, not the frame;
- at rest the star is clear of the nut, so the hub spins a full turn on its own;
- the stops: lifted, the star's top meets the guide; at rest the steeple sits on it;
- the masses and the hub's inertia, for the budget (checks/masses.json).

    python3 check_coupon.py      (writes checks/fit_coupon.txt)
"""
import json
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
TRAVEL, LEAD, CLEAR = 30.0, 24.0, [0.3, 0.4, 0.5]
PLA = 1.24e-3            # g/mm3
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


_cache = {}


def scad(part, **kw):
    key = (part, tuple(sorted(kw.items())))
    if key not in _cache:
        with tempfile.TemporaryDirectory() as td:
            stl = Path(td) / "m.stl"
            args = ["openscad", "-o", str(stl), "-D", f'part="{part}"']
            for k, v in kw.items():
                args += ["-D", f"{k}={v}"]
            subprocess.run(args + [str(HERE / "drop_coupon.scad")], capture_output=True, timeout=900, check=True)
            m = trimesh.load(stl)
        _cache[key] = (m, m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                                tri_verts=np.asarray(m.faces, np.uint32))))
    return _cache[key]


def touch(a, b):
    return (a[1] ^ b[1]).volume()


def main():
    out.append("PRESS-TO-LIGHT CHAPEL DROP TEST PRINT: FIT (exported geometry)")
    frame = scad("frame")
    drops = [0, 0.5, 1, 2, 3, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 25, 26, 27, 28, 28.5, 29, 29.5, 30]
    for v in (1, 2, 3):
        worst, at = 0.0, None
        worst_f = 0.0
        for d in drops:
            mv = scad("moving", DROP=d)
            hb = scad("hub_at", DROP=d, v=v)
            t = touch(mv, hb)
            if t > worst:
                worst, at = t, d
            worst_f = max(worst_f, touch(mv, frame), touch(hb, frame))
        check(worst < 1e-3 and worst_f < 1e-3,
              f"hub {v} (clearance {CLEAR[v - 1]}): through the whole drop, turned by the helix, the shaft never "
              f"touches it (largest overlap {worst:.4f} mm3{'' if at is None else f' at drop {at}'}); "
              f"nothing touches the frame ({worst_f:.4f} mm3)")
    # a wrong-handed helix would collide at once: the check must be able to fail
    mv = scad("moving", DROP=4)
    hb = scad("hub_at", DROP=4, v=1, SPIN=2 * 360 * 4 / LEAD)
    check(touch(mv, hb) > 0.01, f"control: the hub turned the wrong way at drop 4 does collide "
                                f"({touch(mv, hb):.2f} mm3), so the sweep can see a bad helix")
    # at rest the hub spins free
    rest = scad("moving", DROP=TRAVEL)
    worst = max(touch(rest, scad("hub_at", DROP=TRAVEL, v=1, SPIN=a)) for a in range(0, 360, 15))
    check(worst < 1e-3, f"at rest (drop {TRAVEL}) the star is out of the nut: hub 1 turns a full turn "
                        f"touching nothing (largest overlap {worst:.4f} mm3)")
    # the stops
    up = touch(scad("moving", DROP=-0.4), frame)
    down = touch(scad("moving", DROP=TRAVEL + 0.4), frame)
    check(up > 0.01, f"lift stop: 0.4 above the top, the collar is into the guide's mouth ({up:.2f} mm3)")
    check(down > 0.01, f"drop stop: 0.4 below rest, the steeple is into the guide's top ({down:.2f} mm3)")
    # masses and inertia
    shaft, steeple, hub = scad("shaft")[0], scad("steeple")[0], scad("hub", v=1)[0]
    hub.density = PLA * 0.85                      # walls and a little infill: most of a thin hub is wall
    I = hub.moment_inertia[2, 2] * 1e-9           # g mm2 -> kg m2
    masses = {"steeple_g": round(steeple.volume * PLA, 2), "shaft_g": round(shaft.volume * PLA, 2),
              "hub_g": round(hub.volume * PLA * 0.85, 2), "hub_I_kgm2": I}
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "masses.json").write_text(json.dumps(masses, indent=1) + "\n")
    out.append(f"MASSES (the steeple printed solid): steeple {masses['steeple_g']} g, shaft {masses['shaft_g']} g, "
               f"hub {masses['hub_g']} g, hub inertia {I:.2e} kg m2  -> checks/masses.json")
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_coupon.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
