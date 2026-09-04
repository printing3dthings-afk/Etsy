#!/usr/bin/env python3
"""Measure how VISUALLY DETAILED a model's surface actually is.

`mesh_anatomy.py` answers "how is this constructed" and `dfam_probe.py`
answers "will this print". Neither answers the question Scott kept asking
in different words: *why does their print look better than ours*. This
does, in one number:

  rugosity      cross-section perimeter divided by its own convex hull's.
                1.00 means a geometrically bare surface; the 343-mesh
                reference corpus runs p25 1.00, median 1.07, p75 1.25,
                p90 1.58 (SKILL.md Technique 52)

plus the usual descriptive stats -- triangle density normalised by real
surface area, and the same dihedral smoothness numbers Technique 42/43
used, so figures stay comparable across research passes.

Once a model scores low, `texture_recipe.py` says what to do about it: it
reads a reference print's flute count, depth and pitch back out as numbers
that drop straight into an OpenSCAD profile.

    python3 tools/detail_probe.py model.stl
    python3 tools/detail_probe.py dir/*.stl --csv out.csv

Written 2026-09-04 during the 1000-print visual-detail research pass.
"""
import argparse, json, sys, os, warnings
import numpy as np
import trimesh

warnings.filterwarnings("ignore", category=DeprecationWarning)


def load(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    return m


def detail_metrics(m):
    area_cm2 = float(m.area) / 100.0
    out = {
        "triangles": int(len(m.faces)),
        "area_cm2": round(area_cm2, 2),
        "tris_per_cm2": round(len(m.faces) / area_cm2, 1) if area_cm2 > 0 else None,
        "bbox_mm": [round(float(v), 1) for v in m.bounding_box.extents],
    }

    # Surface smoothness, same definition as Technique 42/43 so numbers
    # stay comparable across every research pass this shop has run.
    try:
        adj = m.face_adjacency_angles
        if len(adj):
            deg = np.degrees(adj)
            out["mean_dihedral"] = round(float(deg.mean()), 2)
            out["p95_dihedral"] = round(float(np.percentile(deg, 95)), 2)
            out["hard_edge_frac"] = round(float((deg > 45).mean()), 4)
    except Exception:
        pass

    # Two hard limits on what rugosity can honestly say, both found by
    # checking the tool's own verdicts against models whose construction is
    # known from their .scad source:
    #
    #  - It sees VERTICAL texture only. A body whose relief runs horizontally
    #    (stacked ridges, corrugation, banding) slices to a plain outline and
    #    scores 1.000 while genuinely being textured. `ribbed_organizer` --
    #    6 real 1.5mm corrugations -- scores exactly 1.000. 1.000 means "no
    #    vertical relief", never "no relief".
    #  - It is meaningless on a plate. A 0.8mm-tall engraved lid has no body
    #    to take a cross-section of, and the engraving's own outline becomes
    #    the contour: `snap_box_lid_script` scored 1.784, higher than any
    #    real vase in the reference corpus, on a flat sheet of text.
    ext = m.bounding_box.extents
    footprint = float(max(ext[0], ext[1]))
    aspect = float(ext[2]) / footprint if footprint > 0 else 0.0
    out["h_over_footprint"] = round(aspect, 2)
    if aspect < 0.5:
        out["rugosity_na"] = "plate-like (h/footprint < 0.5); cross-section is not a body"
        return out
    rug = contour_rugosity(m, axis=2)
    if rug is not None:
        out["rugosity"] = round(rug, 4)
    return out


def contour_rugosity(m, axis=2, slices=24, min_pts=24):
    """Cross-section perimeter divided by its own convex-hull perimeter.

    THE metric. A smooth body -- round, oval, tapered, boxy, whatever --
    slices to a convex-ish outline whose perimeter nearly equals its hull's,
    so it scores ~1.0. A fluted, scaled, knurled, faceted or carved body
    slices to a wiggly outline that is much longer than the hull wrapped
    around it, so it scores 1.2-1.6. It is scale-free, and -- the property
    the four earlier attempts all lacked -- completely blind to overall
    FORM: taper, flare, ovality and asymmetry change the hull and the
    contour by the same amount and cancel out.

    Four other approaches were tried first and rejected, each caught by
    testing against known-plain vs known-carved real models rather than by
    reasoning:
      - Laplacian-smoothing displacement: measured thin-shell collapse,
        not texture. A plain hollow PC case scored higher (39.4%) than a
        genuinely carved pineapple-crown planter (30.2%).
      - Local normal spread at a fixed radius: read coarse FACETING as
        texture. This shop's own low-poly fairy house out-scored every
        real carved planter in the corpus.
      - Local plane-fit residual: neighbourhoods straddling a hard edge
        gave huge residuals, so a smooth functional spool holder scored
        0.702mm of "relief".
      - Radial spread within a height band: measured departure from
        rotational symmetry, i.e. form again. The fairy house topped the
        whole set at 52.65% purely because a mushroom's stem and cap have
        wildly different radii.
    """
    try:
        from shapely.geometry import MultiPoint
        lo, hi = m.bounds[0][axis], m.bounds[1][axis]
        span = hi - lo
        if span <= 0:
            return None
        normal = [0.0, 0.0, 0.0]
        normal[axis] = 1.0
        ratios = []
        for t in np.linspace(0.12, 0.88, slices):
            origin = m.bounds[0] + (m.bounds[1] - m.bounds[0]) * 0.5
            origin[axis] = lo + span * t
            try:
                sec = m.section(plane_origin=origin, plane_normal=normal)
                if sec is None:
                    continue
                planar, _ = sec.to_planar()
            except Exception:
                continue
            polys = getattr(planar, "polygons_full", None)
            if not polys:
                continue
            # Largest loop only: the inner loop of a hollow shell, and any
            # separate island (a handle, a spout), are not this contour.
            poly = max(polys, key=lambda p: p.area)
            ext = poly.exterior
            if len(ext.coords) < min_pts:
                continue
            hull = MultiPoint(list(ext.coords)).convex_hull
            hl = getattr(hull, "length", 0.0)
            if hl <= 1e-6:
                continue
            ratios.append(float(ext.length) / float(hl))
        if len(ratios) < 6:
            return None
        return float(np.median(ratios))
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--csv")
    ap.add_argument("--quiet", action="store_true")
    a = ap.parse_args()

    rows = []
    for p in a.paths:
        try:
            m = load(p)
            r = detail_metrics(m)
        except Exception as e:
            r = {"error": str(e)[:100]}
        r["label"] = os.path.basename(p)
        rows.append(r)
        if not a.quiet:
            print(json.dumps(r), flush=True)

    if a.csv:
        import csv
        keys = sorted({k for r in rows for k in r})
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {a.csv} ({len(rows)} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
