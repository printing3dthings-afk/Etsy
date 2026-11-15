#!/usr/bin/env python3
"""Pie Drum Caddy, checked on the exported parts (2026-11-15), as check_bearing_coupon.py
checked the test print Scott ran: the drum resting on 46 balls in the base's channel. Nothing
overlaps; the balls clear the channel's walls 0.3 each side; the drum floats over the base;
the post clears its bore, top and sides; and pushed sideways as far as the post lets it, the
drum still clears the base.

    python3 check_caddy.py      (writes checks/fit_caddy.txt)
"""
import re
import sys
from pathlib import Path

import manifold3d as m3d
import numpy as np
import trimesh

HERE = Path(__file__).resolve().parent
V = {k: float(v) for k, v in re.findall(r"^(\w+) = ([0-9.]+);", (HERE / "pie_caddy.scad").read_text(), re.M)}
out, fail = [], []


def check(ok, msg):
    out.append(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fail.append(msg)


def man(m):
    return m3d.Manifold(m3d.Mesh(vert_properties=np.asarray(m.vertices, np.float32), tri_verts=np.asarray(m.faces, np.uint32)))


z_drum = V["BASE_T"] + V["BALL"]
base = trimesh.load(HERE / "parts/pie_caddy_base.stl")
drum = trimesh.load(HERE / "parts/pie_caddy_drum.stl").apply_translation([0, 0, z_drum])
balls = [trimesh.creation.icosphere(subdivisions=3, radius=V["BALL"] / 2).apply_translation(
    [V["RING_R"] * np.cos(a), V["RING_R"] * np.sin(a), V["BASE_T"] + V["BALL"] / 2])
    for a in np.linspace(0, 2 * np.pi, int(V["N_BALLS"]), endpoint=False)]
out.append("PIE DRUM CADDY: FIT (exported parts, seated on 46 balls)")
bm, dm = man(base), man(drum)
check((bm ^ dm).volume() < 0.01, f"drum and base don't touch ({(bm ^ dm).volume():.3f} mm3)")
q = trimesh.proximity.ProximityQuery(base)
pts = drum.sample(6000, seed=1)
d = np.concatenate([-q.signed_distance(pts[k:k + 500]) for k in range(0, len(pts), 500)])
check(d.min() >= 0.3, f"least gap drum to base {d.min():.2f} (the post in its bore, the drum over the rim)")
bv = sum((man(b) ^ bm).volume() for b in balls)
check(bv < 0.05, f"balls don't cut the channel ({bv:.3f} mm3; they sit on its floor)")
side = min((-q.signed_distance(b.vertices[np.abs(b.vertices[:, 2] - (V['BASE_T'] + V['BALL'] / 2)) < 0.5])).min() for b in balls[::5])
check(abs(side - 0.3) < 0.08, f"balls clear the channel's walls by {side:.2f} each side (the test print's 0.29)")
check(V["BALL"] - V["CH_D"] >= 0.3, f"the drum floats {V['BALL'] - V['CH_D']:.1f} over the base's top")
# pushed sideways until the post meets the bore: the drum still clears everything else
gap = V["POST_GAP"] + V["HOLE_COMP"]       # BORE_R is a formula in the .scad
shifted = drum.copy().apply_translation([gap - 0.05, 0, 0])
check((bm ^ man(shifted)).volume() < 0.01, f"pushed {gap - 0.05:.2f} sideways (the post's play), the drum still clears the base")
check(V["RING_R"] + (V["BALL"] + 0.6) / 2 < V["DRUM_R"] - 10, "the ball ring lies well inside the drum's floor")
dr = trimesh.load(HERE / "parts/pie_caddy_drum.stl")
cog, mass = dr.center_mass, dr.volume * 1.24e-3
off = np.hypot(cog[0], cog[1])
# the worst load: the 1 kg the requirement allows, all in one well at 45 mm out
worst = (mass * off + 1000 * 45) / (mass + 1000)
check(worst < V["RING_R"] * 0.8, f"empty, the drum's centre of mass is {off:.1f} off the axis (its stepped walls; "
      f"no torque about a vertical axis, so it doesn't affect turning). With 1 kg in one well 45 out, "
      f"{worst:.0f}: inside the ball ring ({V['RING_R']:.0f}), so it can't tip off the balls")
out.append("PASS" if not fail else "FAIL: " + "; ".join(fail))
text = "\n".join(out)
print(text)
(HERE / "checks" / "fit_caddy.txt").write_text(text + "\n")
sys.exit(1 if fail else 0)
