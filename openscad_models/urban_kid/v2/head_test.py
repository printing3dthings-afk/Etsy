"""Urban Kid v2: the sculpted head as a test print (2026-11-17).

Scott: "Send just the head as a print. I want to see how it turns out." The
face from research/sculpt_face_sty.py (the sly smile), at its 190 mm figure size,
about 55 mm chin to crown. It's a test of how the face's detail prints, so:

  - FACE UP, the back of the head cut flat on the plate (just behind the
    ears). Every part of the face is then a top surface, where FDM is sharpest.
    Printed upright, the nose, lids, brows and chin all hang over air and need
    support or cones that would fill the face.
  - Bald: the cap covers the crown on the figure; the test is the face.
  - The neck cut short under the jaw.

The sculpt is a surface mesh (the skin open at the neck, the eyeballs separate
pieces), so it's made solid on a voxel grid: the surface sampled densely onto
the grid, the cut planes added as walls, the inside filled, blurred a little and
meshed. Then self-supporting cones (kid.support_up) under anything
the face-up pose leaves overhanging (the ears' backs, under the jaw).

    python3 head_test.py SCULPT.ply OUT_DIR [--pitch 0.12]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
sys.path.insert(0, str(HERE.parent))
import sdf_figure as sf  # noqa: E402
import kid  # noqa: E402  (v1's cones and layer trim: what got its prints through the slicer)

HEAD_MM = 55.0              # chin to crown at 190 mm
CROWN_Z, CHIN_Z = 0.887, 0.590
BACK_CUT_Y = 0.030          # base-mesh units: just behind the ears
NECK_CUT_Z = 0.555          # under the jaw


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sculpt")
    ap.add_argument("out")
    ap.add_argument("--pitch", type=float, default=0.12)
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    S = HEAD_MM / (CROWN_Z - 0.5135)          # the base head's full height (neck included) to 55 mm
    S = HEAD_MM / (CROWN_Z - CHIN_Z) * 0.80   # ... chin to crown is 80 % of that span
    m = trimesh.load(a.sculpt, process=False)
    V = np.asarray(m.vertices, float).copy()
    # face up: the face (-y) turned to +z, the crown to +y; the back cut on z = 0
    c = np.array([2.083, BACK_CUT_Y, NECK_CUT_Z])
    P = (V - c) * S
    P = np.stack([P[:, 0], P[:, 2], -P[:, 1]], axis=1)       # x, up -> +y, face -> +z
    m = trimesh.Trimesh(P, m.faces, process=False)
    lo, hi = P.min(0) - 1.0, P.max(0) + 1.0
    lo[2] = -a.pitch * 2
    lo[1] = -a.pitch * 2
    g = sf.Grid(lo, hi, a.pitch)
    shape = g.X.shape
    print("scale", round(S, 1), "grid", shape)

    # the skin and eyes sampled onto the grid
    pts, _ = trimesh.sample.sample_surface_even(m, int(m.area / (a.pitch * 0.35) ** 2), radius=a.pitch * 0.3)
    pts = np.vstack([pts, m.vertices])
    idx = np.round((pts - g.origin) / a.pitch).astype(int)
    ok = np.all((idx >= 0) & (idx < np.array(shape)), axis=1)
    occ = np.zeros(shape, bool)
    occ[tuple(idx[ok].T)] = True
    occ = ndimage.binary_dilation(occ, iterations=1)
    # hairline gaps (eyeball to lid, the mouth's slit into its cavity) closed:
    # left open, the cavities behind them stayed hollow, walls 0.37 mm thick
    occ = ndimage.binary_closing(occ, iterations=2)
    # the cuts are walls while filling: the back on the plate, the neck below the jaw
    k0 = int(np.searchsorted(g.axes[2], 0.0))
    j0 = int(np.searchsorted(g.axes[1], 0.0))
    occ[:, :, :k0 + 1] = True
    occ[:, :j0 + 1, :] = True
    occ = ndimage.binary_fill_holes(occ)
    occ[:, :, :k0] = False
    occ[:, :j0, :] = False
    occ = ndimage.binary_erosion(occ, iterations=1) | (occ & (g.Z < a.pitch * 3)) | (occ & (g.Y < a.pitch * 3))
    # cracks inside the head (seams in the base mesh, where a ray found walls
    # 0.37 mm apart) sealed: anything more than 1.5 mm under a heavily closed
    # copy's surface is solid. The face's detail (lip line, pupils, iris ring)
    # is shallower than that, so it stays
    big = ndimage.binary_closing(occ, iterations=6)
    big[:, :, :k0 + 1] = True
    big[:, :j0 + 1, :] = True
    big = ndimage.binary_fill_holes(big)
    big[:, :, :k0] = False
    big[:, :j0, :] = False
    occ |= big & (ndimage.distance_transform_edt(big) * a.pitch > 1.5)
    # keep the head only (the walls left slabs outside it)
    lab, n = ndimage.label(occ)
    sizes = ndimage.sum(occ, lab, range(1, n + 1))
    occ = lab == (1 + int(np.argmax(sizes)))
    # trim the wall slabs back to the head's own outline on each cut plane
    inside = ndimage.binary_fill_holes(occ[:, :, k0 + 3])
    occ[:, :, :k0 + 3] &= inside[:, :, None]
    inside = ndimage.binary_fill_holes(occ[:, j0 + 3, :])
    occ[:, :j0 + 3, :] &= inside[:, None, :]

    # behind the ears, low on the plate: every column filled down to the plate.
    # The gap between ear and skull left cones ending in mid-air and the slicer
    # propped it (559 support moves); on the figure the cap and hair cover it
    ear_zone = (np.abs(g.X) > 11.0) & (g.Z < 12.0)
    below = np.flip(np.logical_or.accumulate(np.flip(occ, axis=2), axis=2), axis=2)
    # ... the fill's edge closed into the skull: cut square at |x| = 11 it left
    # slivers 0.1-0.2 mm wide where it met the skull's slope (print_fidelity
    # dropped them; product_gate read them as 0.5 mm walls)
    occ = occ | (below & ear_zone)
    occ = occ | (ndimage.binary_closing(occ, iterations=4) & ndimage.binary_dilation(ear_zone, iterations=8))
    d = ((ndimage.distance_transform_edt(~occ) - ndimage.distance_transform_edt(occ)) * a.pitch).astype(np.float32)
    d = ndimage.gaussian_filter(d, 0.7)            # a voxel's stair-steps out, not the detail (0.4 mm+)
    d = np.maximum(d, -g.Z)
    d = np.maximum(d, -g.Y)
    # cones at 28 deg and every layer trimmed to 31 deg of the one below: at the
    # 37 deg rule alone the slicer propped the ear lobes over the plate (1,422
    # interface moves), as it did v1's (kid.py, CONE and TRIM)
    d, added = kid.support_up(g, d)
    d = np.maximum(d, -g.Z)
    d = sf.base_prism(g, d)
    d, gone = kid.trim_up(g, d, z0=0.0)
    print(f"self-support grew {added:.0f} mm3, trim took {gone:.1f} mm3")
    head = sf.mesh(g, d)
    bodies = head.split(only_watertight=False)
    head = max(bodies, key=lambda b: abs(b.volume))
    head.apply_translation([0, 0, -head.bounds[0, 2]])
    head.export(out / "head_test.stl")
    print("head_test.stl", head.extents.round(1).tolist(), "mm,", round(head.volume), "mm3, watertight",
          head.is_watertight, "bodies", len(bodies))


if __name__ == "__main__":
    main()
