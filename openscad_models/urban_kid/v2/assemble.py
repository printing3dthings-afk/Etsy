"""Urban Kid v2: the simulated clothes made solid and joined (2026-11-17).

cloth_garments.py leaves each garment as a bare surface draped on the
mannequin. Here, on one grid in v1's frame (mm, front -y, up +z):
  1. each cloth surface gets thickness: its distance field, from a dense sample
     of points on it, less half the cloth's thickness;
  2. everything inside the clothes is filled, so each print is solid (the
     space between a baggy leg and the leg inside it is closed off by the
     body and, at the cuffs, by the sneaker's top);
  3. the pieces cloth can't make are added as fields: the hood rolled down
     round the neck, the drawstrings, the kangaroo pocket over the hands, the
     ribbed hem and cuffs, the seat of the pants;
  4. split into prints at v1's joint planes (hoodie above the hem, pants
     between the sneakers' tops and the hem).

    python3 assemble.py SIM_DIR OUT_DIR [--step 0.25]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import trimesh
from scipy import ndimage
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2] / "tools"))
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import sdf_figure as sf  # noqa: E402
import mannequin  # noqa: E402
import kid  # noqa: E402
from kid import Z_NECK, Z_WAIST, groove, torus_z, v3  # noqa: E402

SHOE_TOP = 12.6         # the sneakers as cut for the cloth: the cuffs rest on this
CLOTH_T = 1.1           # cloth thickness


def shell_field(g, mesh, t, reach=2.0, spacing=0.06):
    """Signed-ish distance to a thickened open surface: |p - surface| - t/2."""
    n = int(mesh.area / spacing ** 2)
    pts, _ = trimesh.sample.sample_surface_even(mesh, n, radius=spacing * 0.7)
    pts = np.vstack([pts, mesh.vertices])
    tree = cKDTree(pts)
    P = np.stack([g.X.ravel(), g.Y.ravel(), g.Z.ravel()], axis=1)
    d, _ = tree.query(P, distance_upper_bound=reach, workers=-1)
    d = np.where(np.isfinite(d), d, reach).astype(np.float32)
    return d.reshape(g.X.shape) - t / 2


def hood_and_collar(g, neck_z):
    """The hood down: a thick roll round the neck, fuller at the back, the
    hood's bulk lying on the shoulders behind (v1's, re-fitted to the cloth)."""
    roll = torus_z(g, v3(0, 2.0, neck_z - 0.6), 9.6, 3.4, 1.0)
    hood = sf.ellipsoid(g, v3(0, 9.6, neck_z - 1.6), v3(11.0, 5.4, 6.2))
    return sf.smin(roll, hood, 2.5)


def front_y(g, d, x, z):
    """Where field d's surface is, seen from the front (-y), at (x, z)."""
    i = int(np.clip(np.searchsorted(g.axes[0], x), 0, len(g.axes[0]) - 1))
    k = int(np.clip(np.searchsorted(g.axes[2], z), 0, len(g.axes[2]) - 1))
    col = d[i, :, k]
    j = int(np.argmax(col < 0))
    return float(g.axes[1][j])


def pocket(g, hoodie, hem_z):
    """The kangaroo pocket: a panel of cloth stretched over his hands, 0.9
    proud of the hoodie (blurred, so taut where the body is folded), its sides
    slanting in to the openings his forearms go into."""
    top_z, bot_z = hem_z + 9.0, hem_z + 1.6
    x_edge = 7.2 + (top_z - g.Z) / (top_z - bot_z) * 4.6
    taut = ndimage.gaussian_filter(hoodie, 3.0 / g.step)
    panel = np.maximum(taut - 1.3, np.maximum(np.abs(g.X) - x_edge, np.maximum(g.Z - top_z, bot_z - g.Z)))
    return np.maximum(panel, g.Y + 2.0)                   # the front only


def sdf_of(occ, step):
    """A true signed distance (mm, inside negative) from an occupancy grid."""
    return ((ndimage.distance_transform_edt(~occ) - ndimage.distance_transform_edt(occ)) * step).astype(np.float32)


def fold_detail(g, shells, body, sigma=2.2, amp=0.8):
    """The folds of the simulated cloth on its own: its filled solid's distance
    field less a blurred copy of it (a high-pass), so what's left is the ridges
    and valleys, not the garment's shape. Added to another garment's field it
    presses those folds into that surface wherever the two lie close."""
    occ = (shells < 0) | (body < 0)
    occ[:, :, 0] = True
    occ = ndimage.binary_fill_holes(occ)
    occ[:, :, 0] = False
    d = sdf_of(occ, g.step)
    hp = d - ndimage.gaussian_filter(d, sigma / g.step)
    # the fill leaves pits where the cloth had gaps a voxel wide: a light blur takes them out
    hp = ndimage.gaussian_filter(hp, 0.5 / g.step)
    return np.clip(hp, -amp, amp), d


def v1_hoodie_unsupported(step, g):
    """v1's hoodie (kid.py) as drawn, before it's made printable: its shape,
    pocket, collar roll, drawstrings, seams and ribbed hem."""
    keep = kid.support_up, kid.trim_up, kid.foot
    kid.support_up = lambda g_, d: (d, 0.0)
    kid.trim_up = lambda g_, d, **k: (d, 0.0)
    kid.foot = lambda g_, d, z0, **k: d
    try:
        k = kid.Kid(step)
        k.G["hoodie"] = g
        return k.hoodie()
    finally:
        kid.support_up, kid.trim_up, kid.foot = keep


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sim")
    ap.add_argument("out")
    ap.add_argument("--step", type=float, default=0.25)
    a = ap.parse_args()
    sim, out = Path(a.sim), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    g = sf.Grid(np.array([-26.0, -19.0, SHOE_TOP]), np.array([26.0, 18.0, Z_NECK + 2.0]), a.step)
    print("grid", g.X.shape)

    cloth = {w: trimesh.load(sim / f"cloth_{w}.stl") for w in ("pants", "sleeves", "body")}
    for m in cloth.values():
        # the solver's finest wrinkles are a ring or two wide: spikes at this size, not folds
        trimesh.smoothing.filter_taubin(m, lamb=0.5, nu=-0.53, iterations=6)
    shells = {"pants": shell_field(g, cloth["pants"], CLOTH_T)}
    body = mannequin.body(a.step, g=g)[1]

    # ---- the hoodie: v1's, with the simulated cloth's folds pressed in ----
    # (cloth alone made a shapeless barrel of the body; v1 has the shape, the
    # pocket, collar, cords and seams, and no folds)
    gh = sf.Grid(np.array([-26.5, -17.5, Z_WAIST - 1.0]), np.array([26.5, 17.0, 74.0]), a.step)
    v1 = v1_hoodie_unsupported(a.step, gh)
    top = np.minimum(shell_field(gh, cloth["body"], CLOTH_T), shell_field(gh, cloth["sleeves"], CLOTH_T))
    detail, _ = fold_detail(gh, top, mannequin.body(a.step, g=gh)[1])
    w = np.clip(1.0 - np.abs(v1) / 2.0, 0.0, 1.0)
    # none where the chain lies flat on his chest, little on the taut pocket and the ribbed hem
    chain = (np.abs(gh.X) < 8.2) & (gh.Z > 49.0) & (gh.Z < 65.0) & (gh.Y < 0)
    w = np.where(chain, 0.0, w)
    w = np.where((np.abs(gh.X) < 11.5) & (gh.Z < 49.6) & (gh.Y < -4.0), 0.3 * w, w)
    w = np.where(gh.Z < Z_WAIST + 3.4, 0.3 * w, w)
    hoodie = v1 + detail * w
    hoodie = np.maximum(hoodie, Z_WAIST - gh.Z)
    hoodie = np.maximum(hoodie, gh.Z - 74.0)

    # ---- the pants: legs filled down to the sneakers' tops, the seat to the hem ----
    # the seat: the hips and the tops of the thighs, 2 mm of ease, down to the
    # crotch, where it tapers into the simulated legs (whose waist rings are
    # hidden inside it)
    seat = mannequin.body(a.step, ("torso", "legs"), g=g)[1] - 2.0
    seat = seat + 0.8 * np.maximum(29.5 - g.Z, 0.0)
    seat = np.maximum(seat, g.Z - (Z_WAIST + 1.5))
    low = sf.smin(shells["pants"], seat, 1.5)
    occ = (low < 0) | (body < 0)
    occ[:, :, 0] = True
    occ = ndimage.binary_fill_holes(occ)
    occ[:, :, 0] = False
    pants = np.where(occ, np.minimum(low, -0.01), np.maximum(low, 0.01))
    pants = np.maximum(pants, g.Z - Z_WAIST)
    pants = np.maximum(pants, SHOE_TOP - g.Z)

    for name, gg, d in (("hoodie", gh, hoodie), ("pants", g, pants)):
        m = sf.mesh(gg, d)
        bodies = m.split(only_watertight=False)
        m = max(bodies, key=lambda b: abs(b.volume))
        m.export(out / f"{name}.stl")
        print(f"  {name}: {m.volume:.0f} mm3, {len(bodies)} bodies, watertight {m.is_watertight}")


if __name__ == "__main__":
    main()
