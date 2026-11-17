"""Urban Kid v2: the face, sculpted in code on the CC0 realistic head (2026-11-17).

The base head (Blender Studio Human Base Meshes, 'Head (Sculpting) - Realistic',
CC0) has true anatomy and a neutral face. This adds his expression and the detail
Scott's references have, stroke by stroke with tools/mesh_sculpt.py:
  - a confident smirk on his left, the cheek lifted and the fold deepened there;
  - heavy upper lids, brows drawn down at the inner ends;
  - eyelid folds, lower-lid lines, the furrows between the brows;
  - nasolabial folds, the lip line, the philtrum, nostrils, the chin crease;
  - irises and pupils cut into the eyeballs.

Units are the base mesh's metres; the face spans ~0.21 m chin to crown and
prints ~30 mm, so 1 mm printed is ~7 mm here: nothing finer than 0.003 here.

    python3 sculpt_face.py head_dense.ply out.ply
"""
import sys
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "tools"))
from mesh_sculpt import Sculpt  # noqa: E402

CX = 1.7857                      # the face's centre plane
EYES = {+1: np.array([1.8179, -0.1242, 0.7658]), -1: np.array([1.7536, -0.1242, 0.7658])}
EYE_R = 0.0118


def main(src, dst):
    m = trimesh.load(src, process=False)
    parts = m.split(only_watertight=False)
    head = max(parts, key=lambda p: len(p.vertices))
    s = Sculpt(m)
    lab = np.zeros(len(m.vertices), bool)
    # which vertices are the head (not the eyeballs): the eyeballs are spheres
    for c in EYES.values():
        lab |= np.linalg.norm(s.V - c, axis=1) < EYE_R * 1.05
    head_mask = ~lab
    s.active = head_mask
    F = s.front

    def X(side, dx):                  # x for a feature dx from the centre on a side
        return CX + side * dx

    # ---- expression: grab strokes ----
    # the smirk: his left mouth corner (+x) up and out; his right barely
    s.move(F(1.810, 0.6935), 0.013, (0.0020, 0.0006, 0.0034))
    s.move(F(1.762, 0.6935), 0.010, (-0.0004, 0.0, 0.0006))
    s.move(F(1.833, 0.713), 0.020, (0.0006, -0.0012, 0.0022))            # cheek lifted on that side
    # heavy upper lids: pulled well down over the eyeballs and a little forward
    for side in (1, -1):
        ex = EYES[side][0]
        # grabbed at the lid's edge, not above it: from above, the edge barely moved
        s.move(F(ex, 0.7752), 0.0110, (0, -0.0014, -0.0030))
        s.move(F(ex, 0.7708), 0.0085, (0, -0.0012, -0.0034), sharp=0.7)
        s.move(F(ex + 0.004 * side, 0.7705), 0.0070, (0, -0.0004, -0.0012))    # heavier at the outer corner
    # brows: inner ends drawn down and in, the smirk side's outer end lifted
    s.move(F(X(1, 0.012), 0.787), 0.012, (-0.0008, -0.0010, -0.0026), mirror_x=CX)
    s.move(F(1.832, 0.789), 0.012, (0, -0.0004, 0.0012))
    s.stroke([F(X(1, 0.008), 0.786), F(X(1, 0.022), 0.789), F(X(1, 0.040), 0.786)], 0.0065, 0.0018, mirror_x=CX)

    # ---- detail: soft folds (a valley with the flesh bulging beside it), and
    # sharp lines only where real skin makes a sharp line (lid rims, lip line) ----
    for side in (1, -1):
        ex = EYES[side][0]
        # the upper lid's rim, a cord along its edge, and the fold above it
        s.stroke([F(ex - 0.011, 0.7695), F(ex, 0.7700), F(ex + 0.011, 0.7685)], 0.0022, 0.0007)
        s.crease([F(ex - 0.013, 0.7755), F(ex - 0.005, 0.7780), F(ex + 0.005, 0.7780), F(ex + 0.013, 0.7750)],
                 0.0040, 0.0008, pinch=0.25)
        # under the eye: a soft tear-trough, not a line
        s.stroke([F(ex - 0.010, 0.7585), F(ex, 0.7555), F(ex + 0.012, 0.7580)], 0.0045, -0.0005)
    # a single soft furrow between the brows (he's frowning a little)
    s.stroke([F(CX + 0.003, 0.7805), F(CX + 0.0035, 0.7880)], 0.0030, -0.0006)
    # nasolabial: a soft valley, the cheek bulging above it; marked on the smirk side
    for side, d, bulge in ((1, 0.0016, 0.0014), (-1, 0.0007, 0.0005)):
        path = [F(X(side, 0.017), 0.7255), F(X(side, 0.024), 0.7105), F(X(side, 0.029), 0.6965), F(X(side, 0.030), 0.6870)]
        s.stroke(path, 0.0060, -d)
        s.stroke([p + np.array([side * 0.0055, 0, 0.0035]) for p in path[:3]], 0.0070, bulge)
    # lips: the line between them (sharp), the upper lip's border, a fuller lower lip
    s.crease([F(1.7630, 0.6937), F(1.7740, 0.6930), F(CX, 0.6928), F(1.7990, 0.6940), F(1.8120, 0.6980)],
             0.0022, 0.0011, pinch=0.5)
    s.stroke([F(1.7660, 0.6980), F(1.7790, 0.7005), F(CX, 0.6990), F(1.7930, 0.7005), F(1.8070, 0.7010)], 0.0016, 0.0005)
    s.draw(F(CX + 0.002, 0.6870), 0.0090, 0.0010)
    # philtrum ridges, nostrils, the soft crease under the lower lip, a chin dimple
    s.stroke([F(X(1, 0.0035), 0.7165), F(X(1, 0.0042), 0.7015)], 0.0022, 0.0006, mirror_x=CX)
    for side in (1, -1):
        s.draw(F(X(side, 0.0095), 0.7210), 0.0042, -0.0024)
    s.stroke([F(1.774, 0.6795), F(CX, 0.6770), F(1.798, 0.6795)], 0.0040, -0.0008)
    s.draw(F(CX, 0.6600), 0.006, -0.0006)

    # ---- eyes: iris ring and pupil cut into each eyeball, looking ahead ----
    s.active = lab
    for side, c in EYES.items():
        front = c + np.array([0, -EYE_R, 0])
        ring = [front + 0.0052 * np.array([np.cos(a), 0, np.sin(a)]) for a in np.linspace(0, 2 * np.pi, 41)]
        s.crease(ring, 0.0018, 0.0008, pinch=0.2)
        s.draw(front, 0.0050, -0.0008)          # the iris dished
        s.dots([front], 0.0032, 0.0040)          # the pupil, drilled deep as on a statue: it reads dark
    s.active = None
    out = s.mesh()
    out.export(dst)
    print("sculpted", dst, len(out.vertices))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
