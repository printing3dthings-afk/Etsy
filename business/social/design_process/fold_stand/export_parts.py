#!/usr/bin/env python3
"""Export the Fold Stand's four versions for the design-process video, from their own sources.

  v1  fold_stand.scad          standing open at 36 deg, by render_stand.py's stance; pins split L/R
  v2  v2/fold_stand_v2.scad    the same, with its ratchet pins at rest and pressed
  v3  v3/fold_stand_v3.scad    base, plate and prop posed at 70 deg by the file's own pose() maths
  v4  v4/fold_stand_v4.scad    base, plate and prop in their print frames: the video turns them
                               about the file's own pivot and hinge axes (PIVOT_Z, PIVOT_IN, A,
                               HINGE_IN), at the angles prop_rho() gives for each notch
Meshes land in out/fold_stand/meshes/<version>/; v4's angles in out/fold_stand/meshes/v4/poses.json.
"""
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
import trimesh
from scipy.spatial import ConvexHull

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
FS = ROOT / "openscad_models" / "fold_stand"
OUT = HERE.parent / "out" / "fold_stand" / "meshes"
OPEN = 36.0                   # the opening render_stand.py shows


def scad(src, part, dst, extra="", defs=()):
    """Export one part; `extra` is appended to a temporary copy beside the source (its relative
    `use` paths stay valid), removed after."""
    src = Path(src)
    f = src
    if extra:
        f = src.with_name(f".anim_{src.stem}.scad")
        f.write_text(src.read_text() + "\n" + extra + "\n")
    try:
        args = ["openscad", "-o", str(dst), "-D", f'part="{part}"', *sum((["-D", d] for d in defs), []), str(f)]
        r = subprocess.run(args, capture_output=True, text=True)
    finally:
        if extra:
            f.unlink()
    if not Path(dst).exists():
        raise SystemExit(f"{src.name} part {part}: no mesh\n{r.stderr[-1500:]}")
    return r.stderr


def echoes(log):
    return {k: float(v) for k, v in re.findall(r'"(\w+)", (-?[0-9.]+)', log)}


def stance(front, back, AF):
    """render_stand.py's stance(): stand the A on the hull edge between its two feet."""
    pf, pb = front.vertices[:, 1:], back.vertices[:, 1:]
    pts = np.vstack([pf, pb])
    hull = ConvexHull(pts)
    axis = np.array([0.0, AF])
    best = None
    for (i, j), eq in zip(hull.simplices, hull.equations):
        if (i < len(pf)) == (j < len(pf)):
            continue
        dist = -(eq[:2] @ axis + eq[2])
        if best is None or dist > best[0]:
            best = (dist, eq[:2], pts[i])
    _, nrm, foot = best
    ang = math.atan2(nrm[1], nrm[0]) + math.pi / 2
    return trimesh.transformations.rotation_matrix(-ang, [1, 0, 0], [0, foot[0], foot[1]])


def a_frame(ver, src, pin_parts):
    d = OUT / ver
    d.mkdir(parents=True, exist_ok=True)
    log = scad(src, "front_use", d / "front_raw.stl")
    V = echoes(log)
    scad(src, "back_use0", d / "back_raw.stl")
    for p in pin_parts:
        scad(src, p, d / f"{p}_raw.stl")
    front, back = trimesh.load(d / "front_raw.stl"), trimesh.load(d / "back_raw.stl")
    back.apply_transform(trimesh.transformations.rotation_matrix(math.radians(OPEN), [1, 0, 0], [0, 0, V["AF"]]))
    M = stance(front, back, V["AF"])
    meshes = {"front": front, "back": back}
    for p in pin_parts:
        pins = trimesh.load(d / f"{p}_raw.stl").split(only_watertight=False)
        pins = sorted(pins, key=lambda m: m.centroid[0])
        meshes[f"{p}_l"], meshes[f"{p}_r"] = pins[0], pins[-1]
    for m in meshes.values():
        m.apply_transform(M)
    z0 = min(m.bounds[0][2] for k, m in meshes.items() if k in ("front", "back"))
    for k, m in meshes.items():
        m.apply_translation([0, 0, -z0])
        m.export(d / f"{k}.stl")
    for f in d.glob("*_raw.stl"):
        f.unlink()
    print(ver, "ok", {k: [round(v, 1) for v in m.bounds[1] - m.bounds[0]] for k, m in meshes.items()})


V3_POSE = """
if (part == "P_plate") translate([0, 0, PIVOT_Z]) rotate([angle, 0, 0]) translate([0, 0, -TONGUE_R]) plate();
if (part == "P_prop") let (fy = foot_y(angle), n = nose_at(angle), pa = atan2(n[1] - NOTCH_Z, n[0] - fy))
    translate([0, fy, NOTCH_Z]) rotate([pa, 0, 0]) rotate([90, 0, 90]) translate([0, 0, -PROP_W / 2]) prop();
"""
V4_ECHO = """
echo(V4POSE = [PIVOT_Z, PIVOT_IN, A, HINGE_IN, PASS, [for (i = [0 : 5]) prop_rho(ANGLES[i], NOTCH_Y[i])], ANGLES]);
"""


def v3():
    d = OUT / "v3"
    d.mkdir(parents=True, exist_ok=True)
    src = FS / "v3" / "fold_stand_v3.scad"
    scad(src, "base", d / "base.stl")
    scad(src, "P_plate", d / "plate.stl", V3_POSE, ["angle=70"])
    scad(src, "P_prop", d / "prop.stl", V3_POSE, ["angle=70"])
    print("v3 ok")


def v4():
    d = OUT / "v4"
    d.mkdir(parents=True, exist_ok=True)
    src = FS / "v4" / "fold_stand_v4.scad"
    scad(src, "base", d / "base.stl")
    scad(src, "plate_only", d / "plate.stl")
    log = scad(src, "prop_only", d / "prop.stl", V4_ECHO)
    m = re.search(r"V4POSE = \[(.*)\]", log)
    nums = json.loads("[" + m.group(1) + "]")
    pivot_z, pivot_in, a, hinge_in, pass_ang, rho, angles = nums
    (d / "poses.json").write_text(json.dumps(dict(pivot_z=pivot_z, pivot_in=pivot_in, a=a, hinge_in=hinge_in,
                                                  pass_angle=pass_ang, angles=angles, prop_rho=rho), indent=1))
    print("v4 ok", angles, [round(r, 1) for r in rho])


if __name__ == "__main__":
    import sys
    want = sys.argv[1:] or ["v1", "v2", "v3", "v4"]
    if "v1" in want:
        a_frame("v1", FS / "fold_stand.scad", ["pins_use"])
    if "v2" in want:
        a_frame("v2", FS / "v2" / "fold_stand_v2.scad", ["pins_use", "pins_pressed"])
    if "v3" in want:
        v3()
    if "v4" in want:
        v4()
