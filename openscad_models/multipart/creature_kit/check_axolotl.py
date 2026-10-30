#!/usr/bin/env python3
"""The Chubby Axolotl's fits (2026-10-30), measured on the exported prints,
each moved to where it sits in the creature (positions from the .scad,
part="echo"):

- at rest, no two parts overlap, except the eyes on their crush ribs
- every foot stands on the desk (z = 0) and nothing else goes below it
- each spine joint: the whole creature behind it turned about the ball's
  centre, side to side and up and down, 1 degree at a time, until it meets
  the part in front. That is the joint's real range.
- each leg turned about its ball the same way, until it meets the body
- each ball pulled straight out of its socket, and the legs' also tipped 35 deg
  toward the open roof and away: how much plastic is in the way is the snap
  (the test plate's coupons measured 1.4 / 2.9 / 4.6 mm3)

Also writes every part, moved into place, to logs/asm/ for the renders.

    python3 check_axolotl.py
"""
import os, re, subprocess, sys
from pathlib import Path

import numpy as np
import manifold3d as mf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
from part_mesh import load, to_trimesh  # noqa: E402

SPINE = ["head", "s1", "s2", "s3", "s4", "tail"]
LEGS = {"leg_front_l": "front_l", "leg_front_r": "front_r", "leg_rear_l": "rear_l", "leg_rear_r": "rear_r"}
ON = {"s1": ["leg_front_l", "leg_front_r"], "s3": ["leg_rear_l", "leg_rear_r"], "head": ["gills", "eye_l", "eye_r"]}
R = np.array([[0, 0, 1], [1, 0, 0], [0, 1, 0]], float)     # print (x, y, z) -> creature (y, z, x)
fails = []


def echo():
    env = dict(os.environ, OPENSCADPATH=str(HERE.parents[2] / "assets" / "openscad_libs"))
    out = HERE / "logs" / "echo.echo"
    out.parent.mkdir(exist_ok=True)
    subprocess.run(["openscad", "-o", str(out), "-D", 'part="echo"', str(HERE / "chubby_axolotl.scad")],
                   check=True, capture_output=True, env=env)
    t = out.read_text()
    vec = lambda s: np.array([float(x) for x in s.split(",")])
    place = {m[0]: vec(m[1]) for m in re.findall(r"PLACE (\S+) \[([^\]]+)\]", t)}
    sock = {m[0]: (vec(m[1]), vec(m[2])) for m in re.findall(r"SOCKET (\S+) \[([^\]]+)\] \[([^\]]+)\]", t)}
    lb = re.search(r"LEGBALL front \[([^\]]+)\] rear \[([^\]]+)\]", t)
    zc = float(re.search(r"ZC ([\d.]+)", t).group(1))
    return place, sock, {"front": vec(lb.group(1)), "rear": vec(lb.group(2))}, zc


def mat(rot, t):
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = rot, t
    return m


def about(p, axis, deg):
    a = np.radians(deg)
    k = np.array(axis, float) / np.linalg.norm(axis)
    K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    rot = np.eye(3) + np.sin(a) * K + (1 - np.cos(a)) * K @ K
    return mat(np.eye(3), p) @ mat(rot, 0) @ mat(np.eye(3), -p)


def moved(m, T):
    return m.transform(T[:3, :].tolist())


def overlap(a, b):
    return (a ^ b).volume()


def main():
    place, sock, legball, zc = echo()
    raw = {p: load(str(HERE / "parts" / f"{p}.stl")) for p in SPINE + ["gills", "eye"] + list(LEGS)}
    T = {p: mat(R, place[p]) for p in SPINE + ["gills"]}
    T["eye_l"], T["eye_r"] = mat(R, place["eye_l"]), mat(R, place["eye_r"])
    for leg, s in LEGS.items():
        b = legball["front" if "front" in leg else "rear"].copy()
        if leg.endswith("_r"):
            b[1] = -b[1]
        T[leg] = mat(np.eye(3), sock[s][0] - b)
    parts = {p: moved(raw["eye" if p.startswith("eye") else p], T[p]) for p in T}

    asm = HERE / "logs" / "asm"
    asm.mkdir(parents=True, exist_ok=True)
    for p, m in parts.items():
        to_trimesh(m).export(asm / f"{p}.stl")

    print("At rest, overlap between parts (mm3):")
    names = list(parts)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            v = overlap(parts[a], parts[b])
            if v > 0.01:
                ok = {a, b} <= {"head", "eye_l", "eye_r"}
                print(f"  {a} / {b}: {v:.2f}" + ("  (crush ribs, intended)" if ok else "  OVERLAP"))
                if not ok:
                    fails.append(f"{a}/{b} overlap {v:.2f}")
    print("Standing:")
    for p, m in parts.items():
        z0 = m.bounding_box()[2]
        if p in LEGS:
            print(f"  {p}: lowest point {z0:+.2f} mm")
            if abs(z0) > 0.05:
                fails.append(f"{p} foot at {z0:.2f}")
        elif z0 < 0.5:
            fails.append(f"{p} reaches {z0:.2f}, below the feet")
    print(f"  lowest body part: {min(m.bounding_box()[2] for p, m in parts.items() if p not in LEGS):.1f} mm off the desk")

    print("Spine joints, range before two parts touch (deg):")
    for j in range(len(SPINE) - 1):
        f, back = SPINE[j], SPINE[j + 1:]
        front = [p for p in SPINE[:j + 1]] + sum((ON.get(p, []) for p in SPINE[:j + 1]), [])
        rear = list(back) + sum((ON.get(p, []) for p in back), [])
        fu = mf.Manifold.batch_boolean([parts[p] for p in front], mf.OpType.Add)
        ru = mf.Manifold.batch_boolean([parts[p] for p in rear], mf.OpType.Add)
        rear_face_x = place[f][0] if f != "head" else 0.0
        c = np.array([rear_face_x + zc, 0, place[f][2]])
        res = []
        for label, axis, sign in [("left", [0, 0, 1], 1), ("right", [0, 0, 1], -1), ("up", [0, 1, 0], -1), ("down", [0, 1, 0], 1)]:
            lim = 0
            for d in range(1, 46):
                if overlap(fu, moved(ru, about(c, axis, sign * d))) > 0.05:
                    break
                lim = d
            res.append(f"{label} {lim}")
        print(f"  {f} / {SPINE[j + 1]}: " + ", ".join(res))
    print("Legs, range about the ball before the leg meets the body (deg):")
    for leg, s in LEGS.items():
        seg = "s1" if "front" in leg else "s3"
        body = mf.Manifold.batch_boolean([parts[p] for p in SPINE], mf.OpType.Add)
        c = sock[s][0]
        res = []
        for label, axis, sign in [("fwd", [0, 1, 0], 1), ("back", [0, 1, 0], -1), ("out", [1, 0, 0], 1 if s.endswith("_l") else -1), ("in", [1, 0, 0], -1 if s.endswith("_l") else 1)]:
            lim = 0
            for d in range(1, 61):
                if overlap(body, moved(parts[leg], about(c, axis, sign * d))) > 0.05:
                    break
                lim = d
            res.append(f"{label} {lim}")
        print(f"  {leg} (in {seg}): " + ", ".join(res))
    print("Snap: the most plastic in the way as a ball is pulled straight out (mm3; 0 = it falls out):")
    pulls = [("s1 from head", ["head"], ["s1"], np.array([-1.0, 0, 0]))]
    for leg, s in LEGS.items():
        a_ = sock[s][1]
        seg = "s1" if "front" in leg else "s3"
        for tilt, lab in [(0, "straight"), (35, "tipped forward"), (-35, "tipped back")]:
            d = a_ * np.cos(np.radians(tilt)) + np.array([1.0, 0, 0]) * np.sin(np.radians(tilt))
            pulls.append((f"{leg} {lab}", [seg], [leg], d / np.linalg.norm(d)))
    for lab, fixed, mov, d in pulls:
        fu = mf.Manifold.batch_boolean([parts[p] for p in fixed], mf.OpType.Add)
        mu = mf.Manifold.batch_boolean([parts[p] for p in mov], mf.OpType.Add)
        worst = max(overlap(fu, moved(mu, mat(np.eye(3), d * t))) for t in np.arange(0.25, 8.01, 0.25))
        print(f"  {lab}: {worst:.1f}")
        if worst < 1.0:
            fails.append(f"{lab} has no snap ({worst:.2f} mm3)")
    if fails:
        print("FIT CHECK FAILED: " + "; ".join(fails))
        return 1
    print("FIT CHECK OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
