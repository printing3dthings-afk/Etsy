#!/usr/bin/env python3
"""The Shop Calendar's fits (2026-10-29), measured on the exported prints,
each moved to where it sits:

- every drum at every one of its positions: clear of the base (its spring's
  bump sits in a notch), of its neighbours, of the rod, the facade and the roof
- every drum half a step between positions: the only thing it meets is its
  own spring's bump, which is the click
- the rod in the walls, the facade on its pegs, the roof on its pegs

    python3 check_calendar.py

Overlaps are mm3. Positions come from the .scad itself (part=dims).
"""
import os, re, subprocess, sys
from pathlib import Path

import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load  # noqa: E402

SEAT = 0.01     # resting faces touch; the echoed positions are rounded
NAMES = ["day", "tens", "ones", "month"]
fails = []


def dims():
    env = dict(os.environ, OPENSCADPATH=str(HERE.parents[2] / "assets" / "openscad_libs"))
    out = HERE / "logs" / "dims.echo"
    subprocess.run(["openscad", "-o", str(out), "-D", 'part="dims"', str(HERE / "shop_calendar.scad")],
                   check=True, capture_output=True, env=env)
    n = [float(x) for x in re.findall(r"-?[\d.]+", out.read_text().split("DIMS =")[1])]
    za, y_fac, z_roof, in_w, wall, fac_t = n[:6]
    drums = [n[6 + 4 * i: 10 + 4 * i] for i in range(4)]       # x0, length, side, faces
    return dict(za=za, y_fac=y_fac, z_roof=z_roof, in_w=in_w, wall=wall, fac_t=fac_t, drums=drums)


def report(name, v, limit=0.01):
    ok = v <= limit
    print(f"  {'ok  ' if ok else 'FAIL'}  {name}: {v:.3f} mm3")
    if not ok:
        fails.append(name)


def placed(drum, d, i, turn):
    """A drum as printed (flange on the bed, axle z) moved onto the axle,
    turned `turn` degrees: the .scad's drum_placed."""
    x0, ln, side, _ = d["drums"][i]
    m = drum.rotate([0, 0, -turn])
    if side < 0:
        return m.rotate([0, 90, 0]).translate([x0, 0, d["za"]])
    return m.rotate([0, -90, 0]).translate([x0 + ln, 0, d["za"]])


def main():
    d = dims()
    p = lambda n: load(str(HERE / "parts" / f"{n}.stl"))
    base, roof = p("base"), p("roof").translate([0, 0, d["z_roof"] + SEAT])
    rod = p("rod").rotate([0, 90, 0]).translate([-d["wall"], 0, d["za"]])
    facade = p("facade").rotate([90, 0, 0]).translate([0, d["y_fac"] - SEAT, 0])
    drums = [p(f"drum_{n}_print") for n in NAMES]
    steps = [360 / dr[3] for dr in d["drums"]]

    print("the drums at every position")
    for i, n in enumerate(NAMES):
        worst = {"base": 0, "rod": 0, "facade": 0, "roof": 0}
        for k in range(int(d["drums"][i][3])):
            m = placed(drums[i], d, i, k * steps[i])
            worst["base"] = max(worst["base"], (m ^ base).volume())
            worst["rod"] = max(worst["rod"], (m ^ rod).volume())
            worst["facade"] = max(worst["facade"], (m ^ facade).volume())
            worst["roof"] = max(worst["roof"], (m ^ roof).volume())
        for what, v in worst.items():
            report(f"{n} drum vs {what}, worst position", v)

    print("neighbours, each at rest and half a step on")
    for i in range(3):
        for a in (0, 0.5):
            for b in (0, 0.5):
                v = (placed(drums[i], d, i, a * steps[i]) ^ placed(drums[i + 1], d, i + 1, b * steps[i + 1])).volume()
                report(f"{NAMES[i]} vs {NAMES[i + 1]}, turned {a} and {b} step", v)

    print("half a step: only the spring's bump")
    for i, n in enumerate(NAMES):
        hit = placed(drums[i], d, i, 0.5 * steps[i]) ^ base
        v = hit.volume()
        lo, hi = hit.bounding_box()[:3], hit.bounding_box()[3:]
        # the bump is behind the axle, at its height; anything else is a clash
        at_bump = v > 0 and lo[1] > 18 and abs((lo[2] + hi[2]) / 2 - d["za"]) < 2.5
        ok = at_bump and v < 20
        print(f"  {'ok  ' if ok else 'FAIL'}  {n}: the click, {v:.2f} mm3"
              f" at y {lo[1]:.1f}..{hi[1]:.1f}, z {lo[2]:.1f}..{hi[2]:.1f}")
        if not ok:
            fails.append(f"{n} click")

    print("every piece made it into the export")
    # CGAL drops a piece it can't close and only says so in its log: the
    # awning and the facade's pegs both went missing that way (2026-10-29)
    import trimesh
    tb = trimesh.load(HERE / "parts" / "base.stl", force="mesh")
    for x in (-d["wall"] / 2, d["in_w"] + d["wall"] / 2):
        for z in (12.5, d["z_roof"] - 9.5):
            got = bool(tb.contains([[x, d["y_fac"] - 0.4, z]])[0])
            print(f"  {'ok  ' if got else 'FAIL'}  facade peg at x {x:.1f}, z {z:.1f}")
            if not got:
                fails.append("facade peg missing")
        got = bool(tb.contains([[x, d["y_fac"] + 8, d["z_roof"] + 1]])[0])
        print(f"  {'ok  ' if got else 'FAIL'}  roof peg at x {x:.1f}")
        if not got:
            fails.append("roof peg missing")
    thick = trimesh.load(HERE / "parts" / "facade.stl", force="mesh").bounds[1][2]
    ok = thick > d["fac_t"] + 1.5
    print(f"  {'ok  ' if ok else 'FAIL'}  facade {thick:.2f} thick: the awning stands 1.6 proud")
    if not ok:
        fails.append("awning missing")

    print("the shop")
    report("rod vs base", (rod ^ base).volume())
    report("facade vs base", (facade ^ base).volume())
    report("roof vs base", (roof ^ base).volume())
    report("roof vs facade", (roof ^ facade).volume())

    print("FAILED: " + ", ".join(fails) if fails else "all fits clear")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
