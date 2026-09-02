#!/usr/bin/env python3
"""Dissect a mesh to see how it is CONSTRUCTED, not how it looks.

A render shows the styled result. This shows the structure underneath: where
the walls are, whether the body is one swept profile or a stack of masses,
how many separate pieces it is, and how smooth the surface actually is.

    python3 tools/mesh_anatomy.py model.stl -o outdir

Written 2026-09-02 after a round of visual research where marketing thumbnails
turned out to teach almost nothing about construction (Technique 41).
"""
import argparse, os, sys, math, json
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def load(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    return m


def basics(m):
    ext = m.bounding_box.extents
    comps = m.split(only_watertight=False)
    return {
        "triangles": int(len(m.faces)),
        "vertices": int(len(m.vertices)),
        "bbox_mm": [round(float(v), 2) for v in ext],
        "volume_cm3": round(float(m.volume) / 1000.0, 2) if m.is_volume else None,
        "watertight": bool(m.is_watertight),
        "components": int(len(comps)),
        "component_volumes_cm3": sorted(
            [round(float(abs(c.volume)) / 1000.0, 3) for c in comps], reverse=True)[:15],
    }


def dihedral_stats(m):
    """How smooth is the surface really? Angle between adjacent face normals.

    A swept/lofted organic surface is nearly all sub-5-degree steps. A stack of
    primitives shows a spike of hard edges near 90.
    """
    adj = m.face_adjacency
    n = m.face_normals
    d = np.degrees(np.arccos(np.clip((n[adj[:, 0]] * n[adj[:, 1]]).sum(1), -1, 1)))
    bins = [0, 1, 3, 5, 10, 20, 45, 80, 100, 181]
    hist, _ = np.histogram(d, bins=bins)
    return {
        "mean_deg": round(float(d.mean()), 2),
        "p95_deg": round(float(np.percentile(d, 95)), 2),
        "frac_hard_edges_gt45": round(float((d > 45).mean()), 4),
        "hist": {f"{bins[i]}-{bins[i+1]}": int(hist[i]) for i in range(len(hist))},
    }


def radial_profile(m, n=200):
    """Max radius from the vertical centroid axis at each height.

    One smooth curve = a swept profile. Stair-steps or abrupt jumps = stacked
    masses, which is what 'blocky' actually looks like numerically.
    """
    v = m.vertices
    cx, cy = v[:, 0].mean(), v[:, 1].mean()
    r = np.hypot(v[:, 0] - cx, v[:, 1] - cy)
    z = v[:, 2]
    lo, hi = z.min(), z.max()
    edges = np.linspace(lo, hi, n + 1)
    idx = np.clip(np.digitize(z, edges) - 1, 0, n - 1)
    prof = np.zeros(n)
    for i in range(n):
        sel = r[idx == i]
        prof[i] = sel.max() if len(sel) else np.nan
    zc = (edges[:-1] + edges[1:]) / 2
    ok = ~np.isnan(prof)
    # second derivative magnitude = how "kinked" the silhouette is
    p = prof[ok]
    d2 = np.abs(np.diff(p, 2)) if len(p) > 3 else np.array([0.0])
    return zc[ok], p, {
        "profile_kink_p99": round(float(np.percentile(d2, 99)), 4),
        "profile_kink_mean": round(float(d2.mean()), 4),
    }


def section_sheet(m, out, axis=2, n=12, label=""):
    """The single most revealing view: real cross-sections through the solid."""
    lo, hi = m.bounds[0][axis], m.bounds[1][axis]
    span = hi - lo
    heights = [lo + span * (i + 0.5) / n for i in range(n)]
    normal = [0, 0, 0]; normal[axis] = 1
    cols = 4; rows = (n + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 3.0, rows * 3.0))
    axes = np.atleast_1d(axes).ravel()
    # common extents so sections are comparable at a glance
    keep = [i for i in range(3) if i != axis]
    xlim = (m.bounds[0][keep[0]], m.bounds[1][keep[0]])
    ylim = (m.bounds[0][keep[1]], m.bounds[1][keep[1]])
    for k, h in enumerate(heights):
        ax = axes[k]
        org = [0, 0, 0]; org[axis] = h
        try:
            sec = m.section(plane_origin=org, plane_normal=normal)
            if sec is not None:
                planar, _ = sec.to_planar()
                for poly in planar.polygons_full:
                    xs, ys = poly.exterior.xy
                    ax.fill(xs, ys, facecolor="#2b6cb0", edgecolor="#0b2545", linewidth=0.8)
                    for ring in poly.interiors:
                        xs, ys = ring.xy
                        ax.fill(xs, ys, facecolor="white", edgecolor="#0b2545", linewidth=0.8)
        except Exception as e:
            # Never let a real failure (a missing optional dep, a degenerate
            # plane) read as "this model has nothing here" -- that is how a
            # broken tool gets mistaken for a finding.
            ax.text(0.5, 0.5, "SECTION FAILED", ha="center", color="red",
                    transform=ax.transAxes, fontsize=8)
            print(f"  !! section at {'XYZ'[axis]}={h:.2f} failed: {type(e).__name__}: {e}",
                  file=sys.stderr)
        ax.set_title(f"{'XYZ'[axis]}={h:.1f}", fontsize=8)
        ax.set_aspect("equal"); ax.axis("off")
    for k in range(len(heights), len(axes)):
        axes[k].axis("off")
    fig.suptitle(f"{label}  cross-sections along {'XYZ'[axis]}", fontsize=11)
    fig.tight_layout()
    fig.savefig(out, dpi=105)
    plt.close(fig)


def profile_plot(m, out, label=""):
    zc, p, stats = radial_profile(m)
    fig, ax = plt.subplots(figsize=(4.2, 6.4))
    ax.plot(p, zc, lw=2, color="#0b2545")
    ax.plot(-p, zc, lw=2, color="#0b2545")
    ax.fill_betweenx(zc, -p, p, color="#2b6cb0", alpha=0.25)
    ax.set_aspect("equal"); ax.set_xlabel("max radius (mm)"); ax.set_ylabel("z (mm)")
    ax.set_title(f"{label}\nsilhouette envelope", fontsize=10)
    ax.grid(alpha=0.3)
    fig.tight_layout(); fig.savefig(out, dpi=110); plt.close(fig)
    return stats


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mesh")
    ap.add_argument("-o", "--out", default="anatomy")
    ap.add_argument("--sections", type=int, default=12)
    ap.add_argument("--axis", default="z", choices=["x", "y", "z"])
    ap.add_argument("--joints", action="store_true",
                    help="probe articulation: real clearance and ball radius between components")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.mesh))[0]
    m = load(a.mesh)
    rep = basics(m)
    rep["surface"] = dihedral_stats(m)
    ax = "xyz".index(a.axis)
    section_sheet(m, os.path.join(a.out, f"{name}_sections_{a.axis}.png"), ax, a.sections, name)
    rep["silhouette"] = profile_plot(m, os.path.join(a.out, f"{name}_profile.png"), name)
    if a.joints:
        comps, pairs = probe_joints(m)
        from scipy.spatial import cKDTree
        for pr in pairs[:40]:
            ca = comps[pr["a"]]
            at = np.array(pr["at"])
            near = ca.vertices[np.linalg.norm(ca.vertices - at, axis=1) < 4.0]
            if len(near) > 60:
                _, r, resid = fit_sphere(near)
                pr["ball_radius_fit_mm"] = round(float(r), 2)
                pr["fit_residual_mm"] = round(resid, 3)
        gaps = [p["gap_mm"] for p in pairs]
        rep["joints"] = {
            "pairs": len(pairs),
            "clearance_min_mm": round(min(gaps), 3) if gaps else None,
            "clearance_median_mm": round(float(np.median(gaps)), 3) if gaps else None,
            "detail": pairs[:40],
        }
    print(json.dumps({name: rep}, indent=1))
    with open(os.path.join(a.out, f"{name}.json"), "w") as f:
        json.dump({name: rep}, f, indent=1)




# ---------------------------------------------------------------------------
# Joint probing for print-in-place / articulated models.
#
# The whole point: on a downloaded model you cannot read the designer's
# parameters, but the geometry still carries them. The real clearance is the
# minimum vertex-to-vertex distance between two neighbouring components, and
# the real ball radius is a least-squares sphere fit to the socket wall.
# ---------------------------------------------------------------------------
def probe_joints(m, max_gap=1.5):
    from scipy.spatial import cKDTree
    comps = m.split(only_watertight=False)
    comps = [c for c in comps if len(c.vertices) > 50]
    cents = np.array([c.vertices.mean(axis=0) for c in comps])
    trees = [cKDTree(c.vertices) for c in comps]
    pairs = []
    for i in range(len(comps)):
        for j in range(i + 1, len(comps)):
            if np.linalg.norm(cents[i] - cents[j]) > 60:
                continue
            d, _ = trees[j].query(comps[i].vertices, k=1)
            g = float(d.min())
            if g <= max_gap:
                k = int(np.argmin(d))
                pairs.append({"a": i, "b": j, "gap_mm": round(g, 3),
                              "at": [round(float(x), 2) for x in comps[i].vertices[k]]})
    return comps, pairs


def fit_sphere(pts):
    """Least-squares sphere through a patch of vertices -> the real ball radius."""
    A = np.hstack([2 * pts, np.ones((len(pts), 1))])
    b = (pts ** 2).sum(1)
    sol, *_ = np.linalg.lstsq(A, b, rcond=None)
    c = sol[:3]
    r = math.sqrt(max(sol[3] + (c ** 2).sum(), 0))
    resid = float(np.abs(np.linalg.norm(pts - c, axis=1) - r).mean())
    return c, r, resid


if __name__ == "__main__":
    main()
