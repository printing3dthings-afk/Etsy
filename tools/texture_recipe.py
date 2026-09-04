#!/usr/bin/env python3
"""Read a real model's surface texture back out as buildable NUMBERS.

`detail_probe.py` scores how textured a model is. This answers the next
question: textured HOW. Point it at a print whose surface looks right and
it reports the recipe -- how many flutes/lobes go around, how deep they
cut as a share of the body's own radius, and what that works out to as a
pitch in mm at the surface. Those three numbers drop straight into an
OpenSCAD profile function.

Method: take the outline at a series of heights, resample radius against
angle, and run an FFT around the ring. The dominant harmonic IS the flute
count; twice its amplitude is the peak-to-valley depth. Form (taper,
ovality, a door bump) lives in harmonics 0-2 and is discarded, so the
number that comes back is texture, not silhouette.

    python3 tools/texture_recipe.py model.stl
    python3 tools/texture_recipe.py dir/*.stl --csv recipes.csv

Written 2026-09-04 during the 1000-print visual-detail research pass.
"""
import argparse, csv, json, os, sys, warnings
import numpy as np
import trimesh

warnings.filterwarnings("ignore", category=DeprecationWarning)

# 0=size, 1=off-centre, 2=ovality, and 3/4/5 are triangular/square/pentagonal
# BODIES -- a rectangular tray's 4th harmonic is its own corners, and left in
# it swamped the ranking with boxes reporting "4 flutes, 175% deep". Texture
# starts above the range a primitive silhouette can occupy.
MIN_HARMONIC = 6
MAX_HARMONIC = 96
# A groove deeper than this is not surface relief, it is the form itself.
MAX_DEPTH_FRAC = 0.60


def ring_at(m, z, samples=720):
    """Radius sampled evenly in angle around the outline at height z."""
    origin = m.bounds[0] + (m.bounds[1] - m.bounds[0]) * 0.5
    origin[2] = z
    sec = m.section(plane_origin=origin, plane_normal=[0, 0, 1])
    if sec is None:
        return None
    planar, _ = sec.to_planar()
    polys = getattr(planar, "polygons_full", None)
    if not polys:
        return None
    poly = max(polys, key=lambda p: p.area)
    pts = np.asarray(poly.exterior.coords, dtype=np.float64)[:-1]
    if len(pts) < 32:
        return None
    cx, cy = pts[:, 0].mean(), pts[:, 1].mean()
    ang = np.degrees(np.arctan2(pts[:, 1] - cy, pts[:, 0] - cx)) % 360.0
    rad = np.hypot(pts[:, 0] - cx, pts[:, 1] - cy)
    order = np.argsort(ang)
    grid = np.linspace(0, 360, samples, endpoint=False)
    # wrap one point round each end so the interpolation closes cleanly
    a = np.concatenate([ang[order] - 360, ang[order], ang[order] + 360])
    r = np.concatenate([rad[order], rad[order], rad[order]])
    return grid, np.interp(grid, a, r)


def recipe(m, heights=14, samples=720):
    lo, hi = m.bounds[0][2], m.bounds[1][2]
    span = hi - lo
    if span <= 0:
        return {}
    counts, depths, radii = [], [], []
    for t in np.linspace(0.15, 0.85, heights):
        try:
            got = ring_at(m, lo + span * t, samples)
        except Exception:
            got = None
        if got is None:
            continue
        _, r = got
        mean_r = float(r.mean())
        if mean_r < 2.0:
            continue
        spec = np.abs(np.fft.rfft(r - r.mean())) / (samples / 2.0)
        band = spec[MIN_HARMONIC:MAX_HARMONIC + 1]
        if not len(band):
            continue
        k = int(np.argmax(band)) + MIN_HARMONIC
        amp = float(band[k - MIN_HARMONIC])
        if amp < mean_r * 0.004:      # below this it is mesh noise, not a flute
            continue
        if 2.0 * amp > mean_r * MAX_DEPTH_FRAC:
            continue
        counts.append(k)
        depths.append(2.0 * amp)      # peak-to-valley, the number you'd model
        radii.append(mean_r)
    if len(counts) < 4:
        return {}
    n = int(np.median(counts))
    d = float(np.median(depths))
    rr = float(np.median(radii))
    return {
        "flutes": n,
        "depth_mm": round(d, 3),
        "depth_pct_radius": round(100.0 * d / rr, 2),
        "pitch_mm": round(2 * np.pi * rr / n, 2),
        "mean_radius_mm": round(rr, 2),
        # how consistently the same harmonic wins up the whole body: high
        # means one clean repeating pattern, low means it changes with height
        "consistency": round(float((np.array(counts) == n).mean()), 2),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--csv")
    a = ap.parse_args()
    rows = []
    for p in a.paths:
        try:
            m = trimesh.load(p, force="mesh")
            if isinstance(m, trimesh.Scene):
                m = trimesh.util.concatenate(tuple(m.geometry.values()))
            r = recipe(m)
        except Exception as e:
            r = {"error": str(e)[:100]}
        r["label"] = os.path.basename(p)
        rows.append(r)
        print(json.dumps(r), flush=True)
    if a.csv:
        keys = sorted({k for r in rows for k in r})
        with open(a.csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(rows)
        print(f"wrote {a.csv} ({len(rows)} rows)", file=sys.stderr)


if __name__ == "__main__":
    main()
