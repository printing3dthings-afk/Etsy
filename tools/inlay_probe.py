#!/usr/bin/env python3
"""Will a flush multi-colour inlay actually PRINT in its own colour?

A four-colour face can pass every geometric check in Technique 39 -- the
parts disjoint, their union exactly the gross body, every mesh watertight --
and still come off the printer as a plain bun. The slicer, not the geometry,
decides whether a colour survives: on each LAYER it has to lay down a bead
of that filament, and a bead is one extrusion wide. Anywhere the inlay's
region on a layer is narrower than that, the slicer has nothing it can
print and merges the region into the body. The colour silently vanishes.

This measures that directly. For each part it slices at real layer heights,
and for each layer reports the region's mean width as 2*area/perimeter --
the width of the equivalent strip, which is what an extrusion has to fit
inside.

    python3 tools/inlay_probe.py eyes.stl blush.stl --layer 0.16 --extrusion 0.42

Read the output like this:

  frac_thin   THE number. Share of layers whose region is under one
              extrusion. Under ~5% is fine; those layers are the top and
              bottom caps of a curved inlay and merging them changes
              nothing a person can see.
  vol_thin    Share of the part's VOLUME in those layers. Keep this near
              zero -- it is the amount of colour actually at risk.
  min_width   Deliberately NOT the headline. The minimum layer width of any
              curved inlay is always near zero, because its first and last
              layers are slivers by geometry. A near-zero minimum is not a
              defect and cannot be designed away.

The other failure this catches is a gap BETWEEN two inlays: pass --near
with a second part and it reports the closest approach between them. Two
colours that come within one extrusion of each other leave a sliver of
body colour too thin to print, which reads as a notch bitten out of the
edge of whichever colour is darker.

Written 2026-09-05, after a highlight on the dumpling clicker was enlarged
"to make it print better" and did the opposite -- it added sliver layers of
its own AND closed to 0.24mm of the eye it sits inside.
"""
import argparse, json, os, warnings
import numpy as np
import trimesh

warnings.filterwarnings("ignore", category=DeprecationWarning)


def load(path):
    m = trimesh.load(path, force="mesh")
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    return m


def layer_widths(m, layer_h):
    """(z, mean strip width, area) for every printed layer of the part."""
    lo, hi = float(m.bounds[0][2]), float(m.bounds[1][2])
    out = []
    # Sample at each layer's mid-height: that is the cross-section the
    # slicer's own perimeter generator sees for that layer.
    z = lo + layer_h * 0.5
    while z < hi:
        try:
            sec = m.section(plane_origin=[0, 0, z], plane_normal=[0, 0, 1])
            planar = sec.to_planar()[0] if sec is not None else None
        except Exception:
            planar = None
        polys = getattr(planar, "polygons_full", None) if planar is not None else None
        if polys:
            for poly in polys:
                per = float(poly.exterior.length) + sum(
                    float(r.length) for r in poly.interiors)
                area = float(poly.area)
                if per > 1e-9 and area > 1e-9:
                    out.append((z, 2.0 * area / per, area))
        z += layer_h
    return out


def probe(path, layer_h, extrusion):
    m = load(path)
    rows = layer_widths(m, layer_h)
    r = {"label": os.path.basename(path),
         "bbox_mm": [round(float(v), 2) for v in m.bounding_box.extents]}
    if not rows:
        r["error"] = "no printable layers"
        return r, m
    w = np.array([x[1] for x in rows])
    a = np.array([x[2] for x in rows])
    thin = w < extrusion
    r.update({
        "layers": len(rows),
        "thin_layers": int(thin.sum()),
        "frac_thin": round(float(thin.mean()), 4),
        "vol_thin": round(float(a[thin].sum() / a.sum()), 4) if a.sum() else None,
        "min_width": round(float(w.min()), 3),
        "median_width": round(float(np.median(w)), 3),
        "max_width": round(float(w.max()), 3),
    })
    return r, m


def closest_approach(a, b, samples=4000):
    pa = a.sample(samples)
    return float(trimesh.proximity.closest_point(b, pa)[1].min())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--layer", type=float, default=0.16,
                    help="layer height in mm (0.16 = Bambu 0.4mm standard)")
    ap.add_argument("--extrusion", type=float, default=0.42,
                    help="extrusion width in mm (0.42 on a 0.4mm nozzle)")
    ap.add_argument("--near", action="store_true",
                    help="also report closest approach between every pair")
    a = ap.parse_args()

    meshes = {}
    for p in a.paths:
        try:
            r, m = probe(p, a.layer, a.extrusion)
            meshes[r["label"]] = m
        except Exception as e:
            r = {"label": os.path.basename(p), "error": str(e)[:120]}
        print(json.dumps(r), flush=True)

    if a.near and len(meshes) > 1:
        names = list(meshes)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                d = closest_approach(meshes[names[i]], meshes[names[j]])
                print(json.dumps({
                    "pair": [names[i], names[j]],
                    "closest_mm": round(d, 3),
                    "verdict": "OK" if d >= a.extrusion or d < 1e-3
                               else "sliver of body colour too thin to print",
                }), flush=True)


if __name__ == "__main__":
    main()
