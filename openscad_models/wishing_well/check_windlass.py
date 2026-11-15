#!/usr/bin/env python3
"""Wishing Well windlass coupon: the fit, on the exported parts, assembled (2026-11-15).

Coordinates in use: the axle along X, the crank side at +X; Y across, Z up. Seen from outside
the crank side (from +X), Y is to the right, so a turn that's clockwise from there is a
NEGATIVE rotation about +X.

Checks:
- seated, the axle touches neither post: the journals clear their cradles, the drum and
  collar clear the posts' faces;
- pressed down into a cradle, the journal meets the fingers' catch by the narrowing (0.40,
  0.55, 0.70): the snap really does snap;
- the wheel turned clockwise 2 deg drives a tooth into the pawl (blocked); turned
  counter-clockwise, the ramps lift the pawl, by how much at worst, and it drops back;
- which side of the drum the twine must leave from so the bucket pulls clockwise;
- the handle peg's whole sweep clears the pawl, its pin and the post;
- the wheel's hub clears the axle's hex; its nubs press the groove's floor by the preload.

    python3 check_windlass.py      (writes checks/fit_windlass.txt)
"""
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
OS = "/tmp/claude-0/-home-user-Etsy/d6e7a036-e991-5b99-8baf-18b52486dbea/scratchpad/oscad/squashfs-root/AppRun"
SPAN, FT, HC = 12.0, 8.0, 26.0
P = (11.0, 20.5)
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def scad(body):
    """the parts as assembled in use (the review module's own transforms)"""
    with tempfile.TemporaryDirectory() as td:
        src, stl = Path(td) / "m.scad", Path(td) / "m.stl"
        src.write_text(f'include <{HERE / "windlass.scad"}>\npart = "none";\nspan = SPAN_C;\n{body}\n')
        cmd = [OS, "--backend=manifold"] if Path(OS).exists() else ["openscad"]
        subprocess.run(cmd + ["-o", str(stl), str(src)], capture_output=True, timeout=900)
        return trimesh.load(stl)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32),
                                 tri_verts=np.asarray(m.faces, np.uint32)))


def ov(a, b):
    return max(0.0, (man(a) ^ man(b)).volume())


def rot_x(m, deg, y0, z0):
    t = trimesh.transformations.rotation_matrix(np.radians(deg), [1, 0, 0], [0, y0, z0])
    return m.copy().apply_transform(t)


def moved(m, dz=0.0):
    return m.copy().apply_translation([0, 0, dz])


def main():
    POST_A = "translate([span / 2, 0, 0]) rotate([90, 0, 90]) post({e}, HC_C, true);"
    POST_B = "translate([-span / 2, 0, 0]) mirror([1, 0, 0]) rotate([90, 0, 90]) post({e}, HC_C, false);"
    AXLE = "translate([-span / 2 - FT - 1.0 + COLLAR_G, 0, HC_C]) rotate([0, 90, 0]) rotate(90) axle(span);"
    WHEEL = "translate([span / 2 + FT + WHEEL_W0, 0, HC_C]) rotate([90, 0, 90]) wheel({n});"
    PAWL = "translate([span / 2 + FT + WHEEL_W0 + 0.2, 0, HC_C]) rotate([90, 0, 90]) pawl();"
    PEG = ("translate([span / 2 + FT + WHEEL_W0, 0, HC_C]) rotate([90, 0, 90]) "
           "translate([PEG_AT[0], PEG_AT[1], WHEEL_T - 0.01]) cylinder(r = PEG_R, h = PEG_L);")

    axle = scad(AXLE)
    post_a = scad(POST_A.format(e=0.55))
    wheel = scad(WHEEL.format(n="true"))
    hub = scad(WHEEL.format(n="false"))
    pawl = scad(PAWL)
    peg = scad(PEG)
    out.append("WISHING WELL WINDLASS COUPON: FIT (exported geometry, assembled as in use)")

    out.append("== the cradles")
    for e in (0.40, 0.55, 0.70):
        post_b = scad(POST_B.format(e=e))
        check(ov(axle, post_b) < 0.01, f"far post {e:.2f}: seated, the axle clears it ({ov(axle, post_b):.3f} mm3)")
        # lifted 2.4, the journal's top sits in the mouth: it meets the fingers' catch
        lift = ov(moved(axle, 2.4), post_b)
        check(lift > 0.2, f"far post {e:.2f}: the journal lifted 2.4 meets the catch ({lift:.2f} mm3): it snaps")
    check(ov(axle, post_a) < 0.01, f"crank post 0.55: seated, the axle clears it ({ov(axle, post_a):.3f} mm3)")

    out.append("== the hub on the hex")
    check(ov(axle, hub) < 0.01, f"the wheel's hub clears the hex and collar ({ov(axle, hub):.3f} mm3)")
    pre = ov(axle, wheel) - ov(axle, hub)
    check(0.03 < pre < 0.4, f"the nubs press the groove's floor by the preload ({pre:.2f} mm3)")

    out.append("== ratchet and pawl (seen from outside the crank side; clockwise = negative about +X)")
    check(ov(wheel, pawl) < 0.01, f"seated, the pawl clears the wheel ({ov(wheel, pawl):.3f} mm3)")
    check(ov(pawl, post_a) < 0.01, f"the pawl clears its post and pin ({ov(pawl, post_a):.3f} mm3)")
    blk = ov(rot_x(wheel, -2.0, 0, HC), pawl)
    check(blk > 0.5, f"the wheel turned 2 deg clockwise drives a tooth into the pawl: {blk:.2f} mm3 (blocked)")
    # self-locking: with a tooth pressed into the pawl, lifting the pawl must make the overlap
    # worse, not better, or a loaded tooth would push the pawl out
    w = rot_x(wheel, -0.8, 0, HC)
    o0, o2 = ov(w, pawl), ov(w, rot_x(pawl, -2.0, P[0], HC + P[1]))
    check(o2 > o0 > 0.02, f"self-locking: a tooth pressed 0.8 deg into the pawl overlaps {o0:.2f} mm3; with "
                          f"the pawl lifted 2 deg it overlaps more, {o2:.2f}: the load pulls the pawl in")
    worst = 0.0
    pitch = 360 / 24
    for k in range(1, 16):
        th = pitch * k / 15
        w = rot_x(wheel, th, 0, HC)
        need = None
        for lift in np.arange(0.0, 20.01, 0.5):
            # lifting the tip: the tip is left of the pivot, so it rises on a clockwise turn
            if ov(w, rot_x(pawl, -lift, P[0], HC + P[1])) < 0.01:
                need = lift
                break
        if need is None:
            check(False, f"turned {th:.1f} deg counter-clockwise the pawl can't lift clear")
            break
        worst = max(worst, need)
    check(0 < worst <= 12, f"counter-clockwise, the ramps lift the pawl at most {worst:.1f} deg, then it drops "
                           f"back into the next gap (clicks every {pitch:.2f} deg)")

    out.append("== which way the twine goes")
    out.append("  the pawl blocks clockwise; the bucket must pull clockwise (negative about +X):")
    out.append("  twine hanging from the drum's +Y side (right, seen from outside the crank side) pulls")
    out.append("  -R W about +X, clockwise: so tie the twine to leave the drum on the pawl's side,")
    out.append("  and wind it up counter-clockwise (the handle's top moving away from the pawl's side)")

    out.append("== the handle's sweep")
    hit = 0.0
    for a in range(0, 360, 10):
        p = rot_x(peg, a, 0, HC)
        hit = max(hit, ov(p, pawl), ov(p, post_a))
    check(hit < 0.01, f"the handle peg's whole turn clears the pawl, pin and post ({hit:.3f} mm3 worst)")

    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks").mkdir(exist_ok=True)
    (HERE / "checks" / "fit_windlass.txt").write_text(text + "\n")


if __name__ == "__main__":
    main()
