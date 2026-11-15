#!/usr/bin/env python3
"""Pocket Top UFO: the fit, the balance and a spin estimate, on the exported parts (2026-11-15).

The fit repeats check_snap.py's tests for the joint Scott tested (pair 2, reach 0.45), now in
the UFO's own parts, and adds the UFO's own:
- seated, the saucer (without its nubs) touches nothing: the dome's rim, its boss and the hex
  all clear it; the nubs press the groove's floor by the preload only;
- pushed 0.1 further, only the boss meets the saucer, inside r 4.4, so nothing bears on the
  spring beams (they start at r 4.75) and they flex freely as they snap;
- turned 6 deg it's free, 10 deg the hex drives; pulled 1.0 it hits the nubs; on the way in
  the tip and hex bend each nub out by its reach;
- the spinning top: its centre of mass on the axis, and how far it leans before the saucer's
  rim touches the table.

Then a spin-time ESTIMATE from a model (air drag on the saucer, friction at the tip, and the
spin below which a top stops "sleeping"), for a range of launch speeds. It is a model, not a
measurement: the brief's 30 s is a target, and only Scott's timed spin of a print counts.

    python3 check_ufo.py      (writes checks/fit_ufo.txt and checks/spin_estimate.txt)
"""
import json
import subprocess
import tempfile
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
REACH, NUB_H = 0.45, 1.6
out, fails = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)


def scad(body):
    with tempfile.TemporaryDirectory() as td:
        src, stl = Path(td) / "m.scad", Path(td) / "m.stl"
        src.write_text(f'use <{HERE / "snap_coupon.scad"}>\nuse <{HERE / "ufo_top.scad"}>\n{body}\n')
        subprocess.run(["openscad", "-o", str(stl), str(src)], capture_output=True, timeout=900)
        return trimesh.load(stl)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


def inter(a, b):
    return man(a) ^ man(b)


def ov(a, b):
    return inter(a, b).volume()


def moved(m, dz=0.0, deg=0.0):
    t = trimesh.transformations.rotation_matrix(np.radians(deg), [0, 0, 1])
    t[2, 3] = dz
    return m.copy().apply_transform(t)


def fit():
    out.append("POCKET TOP UFO: FIT (exported geometry, in use: saucer on the bed, stem from above)")
    saucer = trimesh.load(HERE / "parts" / "ufo_saucer.stl")
    stem = trimesh.load(HERE / "parts" / "ufo_stem_in_use.stl")
    body = scad("saucer(false);")
    nubs = scad(f"intersection() {{ saucer(); linear_extrude({NUB_H}) for (k = [0 : 2]) rotate(120 * k) nub(1); }}")
    nub0 = scad(f"intersection() {{ saucer(); linear_extrude({NUB_H}) nub(1); }}")
    check(ov(stem, body) < 0.01, f"seated, the saucer's body clear: {ov(stem, body):.3f} mm3")
    pre = ov(stem, nubs)
    check(0.05 < pre < 0.34, f"seated, the nubs press the groove's floor by the preload: {pre:.2f} mm3")
    g = inter(moved(stem, dz=-0.1), body).to_mesh()
    v = np.asarray(g.vert_properties)[:, :3]
    rmax = float(np.hypot(v[:, 0], v[:, 1]).max()) if len(v) else 0.0
    check(len(v) and rmax < 4.5, f"pushed 0.1 further, only the boss meets the saucer, out to r {rmax:.2f} "
                                 f"(the beams start at 4.75): it stops, and the beams stay free")
    free, drive = ov(moved(stem, deg=6), body), ov(moved(stem, deg=10), body)
    check(free < 0.01 and drive > 0.05, f"turned 6 deg it is still free ({free:.2f} mm3); turned 10 deg the hex "
                                        f"bears on the saucer: {drive:.2f} mm3 (it drives)")
    pull = ov(moved(stem, dz=+1.0), nubs)
    check(pull > pre + 0.5, f"pulled 1.0 out by its dome, it hits the nubs: {pull:.2f} mm3 (held)")
    dxs = []
    for dz in np.arange(1.0, 3.01, 0.2):        # on the way in: the tip and hex pass the nubs
        gm = inter(moved(stem, dz=dz), nub0).to_mesh()
        p = np.asarray(gm.vert_properties)
        dxs.append(0.0 if len(p) == 0 else float(np.ptp(p[:, 0])))
    dx = max(dxs)
    check(abs(dx - REACH) < 0.06, f"on the way in, the stem bends each nub out by up to {dx:.2f} (reach {REACH})")

    # the spinning top: balance and lean
    both = trimesh.util.concatenate([saucer, stem])
    com = (saucer.center_mass * saucer.volume + stem.center_mass * stem.volume) / (saucer.volume + stem.volume)
    off = float(np.hypot(com[0], com[1]))
    check(off < 0.05, f"centre of mass {off:.3f} mm off the spin axis (solid parts, the face's recesses included)")
    tip_z = float(both.bounds[0][2])
    edge = saucer.vertices[saucer.vertices[:, 2] < 0.05]
    r_edge = float(np.hypot(edge[:, 0], edge[:, 1]).max())
    lean = float(np.degrees(np.arctan2(-tip_z, r_edge)))
    out.append(f"  note the tip is {-tip_z:.1f} below the saucer: it leans {lean:.1f} deg before the rim touches")
    out.append(f"  note centre of mass {com[2] - tip_z:.1f} mm above the tip")
    out.append("PASS" if not fails else "FAIL: " + "; ".join(fails))
    text = "\n".join(out)
    print(text)
    (HERE / "checks" / "fit_ufo.txt").write_text(text + "\n")
    return saucer, stem, com[2] - tip_z


def sliced_mass(name):
    s = json.loads((HERE / "checks" / f"slice_{name}.json").read_text())
    return float(s["filament_g"])


def spin(saucer, stem, h_mm):
    """A spin-down model. Every input is named; none is measured on a print yet."""
    m_s, m_t = sliced_mass("saucer"), sliced_mass("stem")     # g, Bambu Studio's estimate
    # inertia: each part's solid shape, scaled to its sliced mass (sliced parts are walls and
    # sparse infill, so their real inertia sits a little higher than this: a cautious figure)
    iz = (saucer.moment_inertia[2, 2] / saucer.volume * m_s + stem.moment_inertia[2, 2] / stem.volume * m_t) * 1e-9
    m = (m_s + m_t) * 1e-3                                    # kg
    h = h_mm * 1e-3
    ix = iz / 2 + m * h * h                                   # about the tip, across the axis (thin-disc estimate)
    R = float(np.hypot(*saucer.vertices[:, :2].T).max()) * 1e-3
    rho, nu, g = 1.2, 1.5e-5, 9.81
    # Spinning below this, a top can't stay upright ("sleeping"): I3 w > sqrt(4 I1 m g h)
    # (the classical heavy symmetric top; Goldstein, Classical Mechanics, sec. 5.7)
    w_end = np.sqrt(4 * ix * m * g * h) / iz
    # The tip: a 1 mm ball on a hard table. Hertz contact radius a = (3 W R / 4 E*)^(1/3);
    # the friction torque of a contact spinning on itself is (3 pi / 16) mu W a.
    W = m * g
    E = 1 / ((1 - 0.35**2) / 3.5e9 + (1 - 0.3**2) / 10e9)   # PLA on a laminate/wood table
    a = (3 * W * 1e-3 / (4 * E)) ** (1 / 3)

    def run(w0, mu, drag):
        w, t, dt = w0, 0.0, 0.01
        while w > w_end and t < 600:
            re = w * R * R / nu
            tq_air = drag * 0.5 * rho * w * w * R**5 * 3.87 / np.sqrt(re)   # free disc, both faces, laminar
            tq_tip = 3 * np.pi / 16 * mu * W * a
            w -= (tq_air + tq_tip) / iz * dt
            t += dt
        return t

    lines = ["POCKET TOP UFO: SPIN ESTIMATE (a model, not a measurement)",
             f"  mass {m * 1e3:.2f} g (sliced: saucer {m_s:.2f}, stem {m_t:.2f}); spin inertia {iz * 1e9:.0f} g mm2",
             f"  centre of mass {h_mm:.1f} mm above the tip; it can't stay up below {w_end:.0f} rad/s "
             f"({w_end / 2 / np.pi:.1f} turns a second)",
             f"  the tip's contact patch about {a * 1e3 * 2:.3f} mm across",
             "  air drag: a free disc 34 mm across, laminar, both faces (Cochran's 3.87/sqrt(Re)); the",
             "  dome, the lights and the slots add drag the model leaves out, so it's run at 1x and 2x.",
             "",
             "  launch (turns/s)  tip friction mu  drag  -> spins for"]
    rows = []
    for rps in (10, 15, 20, 30):
        for mu, drag in ((0.2, 1.0), (0.4, 2.0)):
            t = run(2 * np.pi * rps, mu, drag)
            rows.append((rps, mu, drag, t))
            lines.append(f"  {rps:>16}  {mu:>15}  {drag:>4}x -> {t:5.0f} s")
    lo = min(t for r, _, _, t in rows if r == 15)
    hi = max(t for r, _, _, t in rows if r == 30)
    lines += ["",
              f"  A good finger twist (assumed 15 to 30 turns a second, not measured) gives about {lo:.0f} to {hi:.0f} s.",
              "  What limits it: air drag on the saucer for most of the spin; the 1 mm tip's friction near the end.",
              "  The brief's 30 s is reachable from a firm twist in this model. Scott's timed spin decides it."]
    text = "\n".join(lines)
    print(text)
    (HERE / "checks" / "spin_estimate.txt").write_text(text + "\n")


if __name__ == "__main__":
    s, t, h = fit()
    spin(s, t, h)
