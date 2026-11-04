#!/usr/bin/env python3
"""Day Pods' fits (2026-11-04), on the exported parts:

- every print sits on the bed as exported
- a lid shut in its pod touches nothing; lifted 0.5, pushed 0.5 sideways or
  back, it hits the pod, so the grooves hold it
- slid 1.0 forward its ridge meets the front wall: the click, so it stays shut
  in a bag; slid 6 forward the ridge is past the wall and the lid slides free
- a pod on the stand touches nothing and rests on the base; pulled 0.5 forward
  or pushed 0.5 sideways it hits its rail, so the dovetail holds it; lifted
  past the rail's top, it is off
- neighbouring pods on the stand do not touch

    python3 check_pods.py
"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from part_mesh import load  # noqa: E402

LOG = (HERE / "logs" / "pod.log").read_text()
V = {k: float(v) for k, v in re.findall(r'"(\w+)", ([0-9.]+)', LOG)}
SCAD = (HERE / "day_pods.scad").read_text()


def const(name):
    return float(re.search(rf"\b{name} = ([0-9.]+);", SCAD).group(1))


FLOOR, IN_H, BASE_T, SPINE_H = const("FLOOR"), const("IN_H"), const("BASE_T"), const("SPINE_H")
LB = FLOOR + IN_H
PITCH, H = V["PITCH"], V["H"]
fails = []


def part(name):
    return load(str(HERE / "parts" / f"{name}.stl"))


def ov(a, b):
    return (a ^ b).volume()


def say(ok, text, fail=None):
    print(f"  {'ok  ' if ok else 'FAIL'}  {text}")
    if not ok:
        fails.append(fail or text)


def none(name, v):
    say(v <= 0.05, f"{name}: {v:.3f} mm3", name)


def hits(name, v, need=0.05):
    say(v >= need, f"{name}: {v:.2f} mm3", name)


print("== on the bed")
for p in ["pod", "stand", "coupon"] + [f"lid_{k}" for k in range(7)]:
    z = part(p).bounding_box()[2]
    say(abs(z) < 0.01, f"{p}: lowest point z {z:+.3f}", f"{p} off the bed")

pod, lid = part("pod"), part("lid_use").translate([0, 0, LB])
print("== the lid in its pod")
none("lid shut", ov(pod, lid))
hits("lid lifted 0.5 hits the walls' caps", ov(pod, lid.translate([0, 0, 0.5])))
hits("lid pushed 0.5 sideways hits its groove", ov(pod, lid.translate([0.5, 0, 0])))
hits("lid pushed 0.5 back hits the back wall", ov(pod, lid.translate([0, 0.5, 0])))
hits("lid slid 1.0 forward: its ridge meets the front wall (the click)", ov(pod, lid.translate([0, -1.0, 0])))
none("lid slid 6 forward: past the click, it slides free", ov(pod, lid.translate([0, -6.0, 0])))

stand = part("stand")
print("== pods on the stand")
pods = [pod.translate([(i - 3) * PITCH, 0, BASE_T]) for i in range(7)]
none("seven pods on the stand", sum(ov(p, stand) for p in pods))
hits("a pod 0.1 lower is into the base: it rests on it", ov(pods[0].translate([0, 0, -0.1]), stand))
hits("a pod pulled 0.5 forward: the dovetail holds it", ov(pods[3].translate([0, -0.5, 0]), stand))
hits("a pod pushed 0.5 sideways hits its rail", ov(pods[3].translate([0.5, 0, 0]), stand))
none("a pod lifted the rail's height comes off", ov(pods[3].translate([0, 0, SPINE_H + 0.5]), stand))
none("neighbouring pods do not touch", sum(ov(pods[i], pods[i + 1]) for i in range(6)))

print("FIT CHECK OK" if not fails else "FIT CHECK FAILED: " + "; ".join(fails))
sys.exit(1 if fails else 0)
