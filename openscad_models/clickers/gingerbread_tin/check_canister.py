#!/usr/bin/env python3
"""The canister's fit with the clicker as its lid (2026-10-30), measured on the
exported prints: the clicker's tin, lid and cookie stood in the canister's seat
as they sit when assembled.

- at rest, the clicker touches the canister only where its foot rests on the
  seat's floor: no overlap
- the clicker can shift sideways a little in the seat (so it lifts off without
  binding) but not far enough to slide off the mouth
- the canister holds something: its inside volume

Also writes every part, moved into place, to logs/asm/ for the renders.

    python3 check_canister.py
"""
import re, sys
from pathlib import Path

import numpy as np
import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402


def num(src, name):
    return float(re.search(rf"^{name}\s*=\s*([\d.]+)", src, re.M).group(1))


def moved(m, x=0.0, z=0.0):
    return m.translate([x, 0, z])


def main():
    can_src = (HERE / "gingerbread_tin_canister.scad").read_text()
    H, SEAT_D, RIN, FLOOR = (num(can_src, k) for k in ("H", "SEAT_D", "RIN", "FLOOR"))
    # the clicker's own heights, as its .scad echoes them: tin top S, cookie rest CZ
    log = (HERE / "logs" / "tin_print.log").read_text()
    m = re.search(r"plate ([\d.]+)\s+cookie rest ([\d.]+)", log)
    P, CZ = float(m.group(1)), float(m.group(2))
    S = P - 1.5
    base = H - SEAT_D
    parts = HERE / "parts"
    can = load(str(parts / "canister_print.stl"))
    clicker = {
        "tin": moved(load(str(parts / "tin_print.stl")), z=base),
        "lid": moved(load(str(parts / "lid_print.stl")), z=base + S),
        "cookie": moved(load(str(parts / "cookie_print.stl")), z=base + CZ),
    }
    fails = []
    asm = HERE / "logs" / "asm_canister"
    asm.mkdir(parents=True, exist_ok=True)
    to_trimesh(can).export(asm / "canister.stl")
    for k, v in clicker.items():
        to_trimesh(v).export(asm / f"{k}.stl")
    for k in ("canister", "canister_snow"):
        p = parts / f"{k}.stl"
        if p.exists():
            to_trimesh(load(str(p))).export(asm / f"{k}.stl")

    print(f"Clicker stood in the seat: tin bottom at z {base:.1f}, canister lip at {H:.1f}")
    print("At rest, overlap with the canister (mm3):")
    for k, v in clicker.items():
        o = (can ^ v).volume()
        print(f"  {k}: {o:.3f}")
        if o > 0.01:
            fails.append(f"{k} overlaps the canister {o:.2f}")
    whole = mf.Manifold.batch_boolean(list(clicker.values()), mf.OpType.Add)
    zlo = whole.bounding_box()[2]
    print(f"  the clicker's lowest point {zlo - base:+.2f} from the seat floor")
    if abs(zlo - base) > 0.05:
        fails.append(f"clicker foot at {zlo - base:+.2f}, not on the seat")

    print("Side play in the seat (overlap after sliding the clicker sideways, mm3):")
    free = 0.0
    for d in np.arange(0.05, 1.21, 0.05):
        o = (can ^ moved(whole, x=d)).volume()
        if o > 0.01:
            break
        free = d
    print(f"  slides {free:.2f} mm before it meets the seat wall")
    lifted = (can ^ moved(whole, x=free + 0.1, z=0.0)).volume()
    print(f"  held: sliding further meets {lifted:.2f} mm3 of seat wall")
    if free < 0.2:
        fails.append(f"only {free:.2f} mm side play: it may bind")
    if free > 0.8:
        fails.append(f"{free:.2f} mm side play: it rattles")

    # what it holds: the space inside, up to the ledge the clicker's foot rests over
    inside = mf.Manifold.cylinder(base - FLOOR + 0.01, RIN, RIN, 240).translate([0, 0, FLOOR])
    vol = inside.volume() - (inside ^ can).volume()
    print(f"Holds {vol / 1000:.0f} cm3 (inside {2 * RIN:.1f} mm across, {base - FLOOR:.1f} mm deep)")
    if fails:
        print("FIT CHECK FAILED: " + "; ".join(fails))
        return 1
    print("FIT CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
