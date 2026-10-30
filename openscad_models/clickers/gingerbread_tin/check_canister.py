#!/usr/bin/env python3
"""The canister and its closed lid (2026-10-30), measured on the exported
prints, each moved to where it sits (positions from the .scad's echo):

- the lid rests on the seat inside the canister's mouth: it touches, and
  pressed 0.1 lower it would be inside the canister, so it can't drop in
- the cookie and the lid at rest: no overlap, as on the clicker
- the switch in the pod: its body and its pins clear the pocket; the pod's foot
  is solid under the cutout. (The clips' hooks sit on the pocket's 45 deg
  chamfer just under the plate, by design: see the .scad.)
- what the canister holds, round the pod

Also writes every part, moved into place, to logs/asm_canister/ for the renders.

    python3 check_canister.py
"""
import re, sys
from pathlib import Path

import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402

SRC = (HERE / "gingerbread_tin_canister.scad").read_text()


def num(name):
    return float(re.search(rf"^{name}\s*=\s*([\d.]+)", SRC, re.M).group(1))


def box(w, z0, z1):
    return mf.Manifold.cube([w, w, z1 - z0]).translate([-w / 2, -w / 2, z0])


def main():
    e = re.search(r"CANISTER lid underside ([\d.]+) cookie rest ([\d.]+) pod foot ([\d.]+)",
                  (HERE / "logs" / "lid_closed_print.log").read_text())
    lid_s, cookie_z, foot_z = (float(x) for x in e.groups())
    T, RIN, FLOOR, PFLOOR = num("T"), num("RIN"), num("FLOOR"), num("PFLOOR")
    pod_h = lid_s - foot_z
    parts = HERE / "parts"
    can = load(str(parts / "canister_print.stl"))
    lid_raw = load(str(parts / "lid_closed_print.stl"))
    lid = lid_raw.translate([0, 0, foot_z])
    cookie = load(str(parts / "cookie_print.stl")).translate([0, 0, cookie_z])
    fails = []

    asm = HERE / "logs" / "asm_canister"
    asm.mkdir(parents=True, exist_ok=True)
    for k in ("canister", "canister_snow"):
        to_trimesh(load(str(parts / f"{k}.stl"))).export(asm / f"{k}.stl")
    for k in ("lid_closed", "lid_closed_holly", "lid_closed_snow"):
        to_trimesh(load(str(parts / f"{k}.stl")).translate([0, 0, foot_z])).export(asm / f"{k}.stl")
    for k in ("cookie", "cookie_icing", "cookie_red", "cookie_green"):
        to_trimesh(load(str(parts / f"{k}.stl")).translate([0, 0, cookie_z])).export(asm / f"{k}.stl")

    print(f"The lid's underside sits at z {lid_s:.1f}, the pod's foot at {foot_z:.1f}, the cookie at {cookie_z:.1f}")
    rest = (can ^ lid).volume()
    low = (can ^ lid.translate([0, 0, -0.1])).volume()
    print(f"  lid / canister at rest: {rest:.3f} mm3; 0.1 lower: {low:.1f} mm3")
    if rest > 0.05:
        fails.append(f"lid overlaps the canister {rest:.2f} mm3")
    if low < 1.0:
        fails.append("nothing holds the lid up: it drops into the canister")
    lifted_side = (can ^ lid.translate([0.15, 0, 0.3])).volume()
    print(f"  lifted 0.3 and slid 0.15: {lifted_side:.3f} mm3 (it lifts off without binding)")
    if lifted_side > 0.05:
        fails.append("the lid binds in the lip")
    c = (cookie ^ lid).volume()
    print(f"  cookie / lid: {c:.3f} mm3")
    if c > 0.01:
        fails.append(f"cookie overlaps the lid {c:.2f}")

    # the switch, in the lid's print frame: the plate's underside at pod_h
    body = box(13.9, pod_h - 5.0, pod_h)                     # the body below the plate
    pins = box(13.9, pod_h - 5.0 - 3.3, pod_h - 5.0)          # every pin and the centre post, generously
    for lab, m in (("body", body), ("pins", pins)):
        o = (lid_raw ^ m).volume()
        print(f"  switch {lab} / pod: {o:.3f} mm3")
        if o > 0.01:
            fails.append(f"switch {lab} meets the pod {o:.2f}")
    under = box(14.0, 0, PFLOOR)
    shut = (lid_raw ^ under).volume() / under.volume()
    print(f"  the pod's foot under the cutout: {100 * shut:.1f}% solid")
    if shut < 0.999:
        fails.append("the pod is open under the switch")

    inside = mf.Manifold.cylinder(T - FLOOR, RIN, RIN, 240).translate([0, 0, FLOOR])
    vol = inside.volume() - (inside ^ can).volume() - (inside ^ lid).volume()
    print(f"Holds {vol / 1000:.0f} cm3 round the pod ({2 * RIN:.1f} mm across, {T - FLOOR:.1f} mm deep at the side,"
          f" {foot_z - FLOOR:.1f} under the pod)")
    if fails:
        print("FIT CHECK FAILED: " + "; ".join(fails))
        return 1
    print("FIT CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
