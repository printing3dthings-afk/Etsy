#!/usr/bin/env python3
"""The Candy Lighthouse's fits (2026-10-29), measured on the exported prints,
each moved to where it sits:

- the wheel on the gallery floor: clear of the tower seated in its detents,
  and lifted 1.0 (riding over the nubs) at every angle between them
- the wheel against the lantern's baffle, seated and lifted
- the shaft in the roof's socket, seated and lifted
- the lantern in the gallery's groove, the roof on the lantern
- the chute: a 15 mm disc fits flat at every height of the outlet, the jog and
  the shaft, and the door is open where the candy goes

    python3 check_lighthouse.py

Overlaps are mm3. Heights come from the .scad itself (part=dims).
"""
import math, re, subprocess, sys, os
from pathlib import Path

import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load  # noqa: E402

LIFT = 1.0
SEAT = 0.01     # resting faces touch; the echoed heights are rounded to 0.001
fails = []


def dims():
    env = dict(os.environ, OPENSCADPATH=str(HERE.parents[2] / "assets" / "openscad_libs"))
    out = HERE / "logs" / "dims.echo"
    subprocess.run(["openscad", "-o", str(out), "-D", 'part="dims"', str(HERE / "candy_lighthouse.scad")],
                   check=True, capture_output=True, env=env)
    nums = [float(x) for x in re.findall(r"-?[\d.]+", out.read_text().split("DIMS =")[1])]
    zg, lan_z, roof_z, jog_top, jog, door_z, door_a, tx, ty, sx, sy, shaft_top = nums
    return dict(zg=zg, lan_z=lan_z, roof_z=roof_z, jog_top=jog_top, jog=jog, door_z=door_z,
                door_a=door_a, top=(tx, ty), shaft=(sx, sy), shaft_top=shaft_top)


def report(name, v, limit=0.01):
    ok = v <= limit
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {v:.3f} mm3")
    if not ok:
        fails.append(name)


def disc(c, z, r=7.5, h=0.4):
    return mf.Manifold.cylinder(h, r, r, 96).translate([c[0], c[1], z])


def main():
    d = dims()
    p = lambda n: load(str(HERE / "parts" / f"{n}.stl"))
    tower, wheel, lantern, roof = p("tower_print"), p("wheel"), p("lantern_up"), p("roof")
    lantern = lantern.translate([0, 0, d["lan_z"] + SEAT])
    roof = roof.translate([0, 0, d["roof_z"] + 2 * SEAT])

    print("wheel on the gallery")
    for a in range(0, 90, 15):
        lift = 0.0 if a == 0 else LIFT
        w = wheel.rotate([0, 0, a]).translate([0, 0, d["zg"] + lift + SEAT])
        tag = "seated" if a == 0 else f"turned {a} deg, lifted {lift}"
        report(f"wheel vs tower, {tag}", (w ^ tower).volume())
        report(f"wheel vs lantern, {tag}", (w ^ lantern).volume())
        # the roof turns the wheel, so it turns with it
        report(f"shaft vs roof, {tag}", (w ^ roof.rotate([0, 0, a])).volume())

    print("stack")
    report("lantern vs tower", (lantern ^ tower).volume())
    report("roof vs lantern", (roof ^ lantern).volume())
    report("roof vs tower", (roof ^ tower).volume())

    print("chute: a 15 mm disc, flat, at each height")
    zg, jt, jog = d["zg"], d["jog_top"], d["jog"]
    top, sh = d["top"], d["shaft"]
    worst = 0.0
    for z in [zg - 2, zg - 6, jt + 2, jt]:
        worst = max(worst, (disc(top, z) ^ tower).volume())
    for k in range(1, 10):
        t = k / 10
        c = (top[0] + (sh[0] - top[0]) * t, top[1] + (sh[1] - top[1]) * t)
        worst = max(worst, (disc(c, jt - jog * t + 0.6) ^ tower).volume())
    # the shaft, down to where the ramp under it starts to rise
    rin = math.hypot(*sh) - 8
    ramp_top = d["door_z"] + (18 - rin) * math.tan(math.radians(50))
    for z in [jt - jog - 2, jt - jog - 6, ramp_top + 1]:
        worst = max(worst, (disc(sh, z) ^ tower).volume())
    report("candy disc vs tower, outlet / jog / shaft", worst)

    # the door: a box the size of a flat candy, centred in the opening, 0.5
    # over the sill and reaching from inside the wall to outside it
    door = (mf.Manifold.cube([6, 14, 8]).translate([15, -7, d["door_z"] + 0.5])
            .rotate([0, 0, d["door_a"]]))
    report("flat candy in the door", (door ^ tower).volume())

    print("FAILED: " + ", ".join(fails) if fails else "all fits clear")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
