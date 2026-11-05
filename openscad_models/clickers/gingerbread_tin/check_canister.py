#!/usr/bin/env python3
"""The canister and its closed lid (2026-10-30), measured on the exported
prints, each moved to where it sits (positions from the .scad's echo):

- the lid screws on (2026-11-03): screwed down its guide ring rests on the
  shelf in the canister's mouth, touching nothing, and 0.1 lower it would be
  into the shelf; pulled straight up it hits the thread; turned back along the
  thread it touches nothing, and turned the wrong way while rising it collides
- the guide (2026-11-05): raised to where its teeth meet the canister's, the
  most the lid can tip before the ring meets the bore, against the tip it
  takes to start a whole tooth out (the pitch across the thread's diameter)
- the seam: the gap over the collar's flat outer edge, from its inner end to
  the outside wall, where the line shows (about 1.8; it was 3.4)
- the cookie and the lid at rest: no overlap, as on the clicker
- the switch in the pod: its body and its pins clear the pocket; the pod's foot
  is solid under the cutout. (The clips' hooks sit on the pocket's 45 deg
  chamfer just under the plate, by design: see the .scad.)
- what the canister holds, round the pod

Also writes every part, moved into place, to logs/asm_canister/ for the renders.

    python3 check_canister.py
"""
import math, re, sys
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
    # the thread, as gingerbread_tin_clicker.scad's TH_P: right hand, the lid rises
    # TH_P a turn as it turns anticlockwise seen from above
    CLK = (HERE / "gingerbread_tin_clicker.scad").read_text()
    TH_P, TH_H, TH_R = (float(re.search(rf"{k} = ([\d.]+)", CLK).group(1)) for k in ("TH_P", "TH_H", "TH_R"))
    for dz in (0.5, 1.0):
        v = (can ^ lid.translate([0, 0, dz])).volume()
        print(f"  pulled {dz} straight up: {v:.1f} mm3 (the thread holds it)")
        if v < 1.0:
            fails.append(f"the lid lifts {dz} without the thread holding it")
    for a in (30, 90, 180, 360, 540):
        v = (can ^ lid.rotate([0, 0, a]).translate([0, 0, a / 360 * TH_P])).volume()
        print(f"  unscrewed {a} deg along the thread: {v:.3f} mm3")
        if v > 0.05:
            fails.append(f"the lid binds unscrewing at {a} deg")
    v = (can ^ lid.rotate([0, 0, -30]).translate([0, 0, 30 / 360 * TH_P])).volume()
    print(f"  turned 30 deg the wrong way while rising: {v:.1f} mm3 (collides, so the zeros are the thread's path)")
    if v < 1.0:
        fails.append("the unscrew check would pass without a thread")
    # the guide: the lid raised along the thread until its teeth are just at the
    # canister's, then tipped about its floor's centre; the most it tips clear
    def tipped(t, dz):
        a = dz / TH_P * 360
        return lid.rotate([0, 0, a]).translate([0, 0, dz - (lid_s + dz)]).rotate([t, 0, 0]).translate([0, 0, lid_s + dz])
    dz0 = TH_H
    lo_t, hi_t = 0.0, 8.0
    if (can ^ tipped(0, dz0)).volume() > 0.05:
        fails.append("the lid touches the canister untipped where its teeth come in")
    for _ in range(14):
        m = (lo_t + hi_t) / 2
        if (can ^ tipped(m, dz0)).volume() > 0.05:
            hi_t = m
        else:
            lo_t = m
    skip = math.degrees(math.atan(TH_P / (2 * TH_R)))
    print(f"  where the teeth come in, the ring lets the lid tip {lo_t:.2f} deg; starting a tooth out takes {skip:.2f}")
    if lo_t > skip / 2:
        fails.append(f"the lid can tip {lo_t:.2f} deg, over half the {skip:.2f} that starts it a tooth out")
    # the seam over the collar: the lid's flare's underside over the collar's
    # sloped top, upright and square to the 39 deg slope they share, on the slope
    # (inside the collar's flat outer edge, TR - CFLAT); and how far it opens at
    # the outside, over the flat, by design (2026-11-05: the slope run out to the
    # wall was a knife edge)
    FL_A = float(re.search(r"FL_A = ([\d.]+)", CLK).group(1))
    TRc, CFLAT = num("TR"), num("CFLAT")
    def gap(r):
        # the collar's top at r, then the lid's underside directly above it (below
        # the collar's top the lid's thread teeth are in the probe's way)
        top = (can ^ mf.Manifold.cylinder(30, 0.002, 0.002, 8).translate([r, 0, lid_s])).bounding_box()[5]
        above = mf.Manifold.cylinder(20, 0.002, 0.002, 8).translate([r, 0, top + 0.001])
        return (lid ^ above).bounding_box()[2] - top
    # Inside the flat the collar's top is the thread's run-out (the groove and the
    # lead-in countersink cut it), so the seam is read over the flat: from its
    # inner end, where the lid's flare comes down to it, to the outside wall,
    # where the line shows.
    # (its inner end measured 0.15 out, past the groove's root at TR - CFLAT + 0.1)
    inner, edge = gap(TRc - CFLAT + 0.15), gap(TRc - 0.05)
    print(f"  seam over the collar's flat edge: {inner:.2f} at its inner end, {edge:.2f} at the outside (the line you see)")
    if inner > 0.6:
        fails.append(f"the lid's flare stands {inner:.2f} over the flat's inner end")
    if edge > 2.0:
        fails.append(f"the seam opens to {edge:.2f} at the outside")
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
