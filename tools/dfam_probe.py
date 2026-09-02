#!/usr/bin/env python3
"""Measure a mesh the way a printer experiences it.

mesh_anatomy.py answers "how was this built". This answers "what will it do on
the plate": real wall thickness, overhang distribution in print orientation,
bed contact area, bridge spans and the smallest features present.

    python3 tools/dfam_probe.py model.stl [--samples 6000] [--nozzle 0.4]

Written 2026-09-02. Everything here is measured off geometry -- no assumptions
about how the model was authored.
"""
import argparse, json, math, sys
import numpy as np
import trimesh


def sample_surface(m, n):
    pts, fidx = trimesh.sample.sample_surface(m, n)
    return pts, m.face_normals[fidx]


def wall_thickness(m, n=6000, eps=1e-3):
    """Shoot each sample point straight into the solid; first exit = wall.

    This is the honest measurement: a nominal 'wall = 2mm' parameter says
    nothing about what a boolean actually left behind at a corner or a blend.
    """
    pts, nrm = sample_surface(m, n)
    origins = pts - nrm * eps
    dirs = -nrm
    loc, ray_i, _ = m.ray.intersects_location(origins, dirs, multiple_hits=False)
    if len(ray_i) == 0:
        return None
    d = np.linalg.norm(loc - origins[ray_i], axis=1)
    d = d[(d > 1e-4) & (d < 1e4)]
    if not len(d):
        return None
    return {
        "n": int(len(d)),
        "p01": round(float(np.percentile(d, 1)), 3),
        "p05": round(float(np.percentile(d, 5)), 3),
        "median": round(float(np.median(d)), 3),
        "p95": round(float(np.percentile(d, 95)), 3),
        "frac_under_0p8mm": round(float((d < 0.8).mean()), 4),
        "frac_under_1p2mm": round(float((d < 1.2).mean()), 4),
    }


def overhangs(m):
    """Angle FROM VERTICAL of every downward-facing face, in print orientation.

    Sign matters and has bitten me before: a downward face has nz < 0. 90 deg
    here means a flat ceiling (a bridge); 0 deg means a vertical wall.
    """
    n = m.face_normals
    a = m.area_faces
    down = n[:, 2] < -1e-6
    if not down.any():
        return {"downward_area_mm2": 0.0}
    ang = np.degrees(np.arcsin(np.clip(-n[down, 2], 0, 1)))
    ar = a[down]
    bins = [0, 25, 35, 45, 55, 65, 80, 90.001]
    hist = {}
    for i in range(len(bins) - 1):
        s = ((ang >= bins[i]) & (ang < bins[i + 1]))
        hist[f"{bins[i]:g}-{bins[i+1]:g}"] = round(float(ar[s].sum()), 1)
    zmin = m.bounds[0][2]
    on_bed = ar[(ang > 89.0) & (np.abs(m.triangles_center[down][:, 2] - zmin) < 0.05)].sum()
    return {
        "downward_area_mm2": round(float(ar.sum()), 1),
        "area_over_55deg_mm2": round(float(ar[ang > 55].sum()), 1),
        "unsupported_ceiling_mm2": round(float(ar[ang > 80].sum() - on_bed), 1),
        "bed_contact_mm2": round(float(on_bed), 1),
        "by_angle_from_vertical": hist,
    }


def local_radius(m):
    """Rough radius of curvature per shared edge: r = (edge midpoint span) / angle.

    Convex hard edges show up as radius ~0. A model that has been properly
    filleted has almost no zero-radius convex edges on its visible surfaces.
    """
    adj = m.face_adjacency
    n = m.face_normals
    cos = np.clip((n[adj[:, 0]] * n[adj[:, 1]]).sum(1), -1, 1)
    ang = np.arccos(cos)
    c = m.triangles_center
    span = np.linalg.norm(c[adj[:, 0]] - c[adj[:, 1]], axis=1)
    ok = ang > np.radians(0.5)
    r = span[ok] / ang[ok]
    return {
        "sharp_edges_gt45deg": int((np.degrees(ang) > 45).sum()),
        "radius_p05_mm": round(float(np.percentile(r, 5)), 3) if len(r) else None,
        "radius_median_mm": round(float(np.median(r)), 3) if len(r) else None,
    }


def footprint(m):
    z = m.bounds[0][2]
    ext = m.bounding_box.extents
    return {
        "bbox_mm": [round(float(v), 2) for v in ext],
        "plate_area_mm2": round(float(ext[0] * ext[1]), 1),
        "per_256_plate": round(float((256 * 256) / max(ext[0] * ext[1], 1e-9)), 2),
        "aspect_tallness": round(float(ext[2] / max(ext[0], ext[1])), 3),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh")
    ap.add_argument("--samples", type=int, default=6000)
    ap.add_argument("--label", default=None)
    a = ap.parse_args()
    m = trimesh.load(a.mesh, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    rep = {
        "label": a.label or a.mesh.split("/")[-1],
        "triangles": int(len(m.faces)),
        "components": int(len(m.split(only_watertight=False))),
        "footprint": footprint(m),
        "overhangs": overhangs(m),
        "curvature": local_radius(m),
        "wall_mm": wall_thickness(m, a.samples),
    }
    print(json.dumps(rep))


if __name__ == "__main__":
    main()
