"""Folds sculpted into a distance field, the way figure sculptors place them
(2026-11-17).

Simulated cloth gave the pants real drape, but pressed into the hoodie it read
as rock or mush (research/NOTES.md). The sculptors behind Scott's references
don't copy physics fold for fold: they place a few bold folds of the known
kinds (compression folds stacked inside a bent elbow, tension folds running
from the shoulder to where the hands pull the front down, gathers above a tight
hem, long hanging folds down the back) and let the rest of the cloth be plain.
This places those folds as strokes on a signed-distance field:

  stroke(g, d, path, r, h)   a soft ridge (h > 0) or valley (h < 0) along a
                             polyline lying on the surface, falloff (1 - t^2)^3

Paths are given roughly; on_surface() drops each point onto the zero set.

Grids: an sf.Grid, or a DesignGrid (a final-size grid seen in the design's
units, as kid.Scaled, that also knows how to find its own samples).
"""
import numpy as np
from scipy.ndimage import map_coordinates


class DesignGrid:
    """A grid g at final size, seen from the design frame scaled 1/s about
    pivot (kid.Scaled, plus what's needed to sample it)."""

    def __init__(self, g, pivot, s):
        self.g, self.pivot, self.s = g, np.asarray(pivot, float), float(s)
        self.step = g.step / s
        self.axes = [(a - p) / s + p for a, p in zip(g.axes, self.pivot)]
        self.X = (g.X - pivot[0]) / s + pivot[0]
        self.Y = (g.Y - pivot[1]) / s + pivot[1]
        self.Z = (g.Z - pivot[2]) / s + pivot[2]

    def local(self, centre, R=None):
        import sdf_figure as sf
        return sf.Grid.local(self, centre, R)


def design_axes(g):
    return g.axes if not isinstance(g, DesignGrid) else g.axes


def sample(g, d, pts):
    """Trilinear samples of field d (on grid g) at design-frame points pts."""
    ax = design_axes(g)
    pts = np.atleast_2d(np.asarray(pts, float))
    idx = [(pts[:, k] - ax[k][0]) / (ax[k][1] - ax[k][0]) for k in range(3)]
    return map_coordinates(d, idx, order=1, mode="nearest")


def on_surface(g, d, p, direction, reach=5.0, n=201):
    """The point where d crosses zero on the line p + t*direction, |t| <= reach,
    nearest p. direction points outward (from inside to outside)."""
    u = np.asarray(direction, float)
    u = u / np.linalg.norm(u)
    t = np.linspace(-reach, reach, n)
    P = np.asarray(p, float)[None, :] + t[:, None] * u[None, :]
    v = sample(g, d, P)
    cross = np.where((v[:-1] < 0) & (v[1:] >= 0))[0]
    if not len(cross):
        return np.asarray(p, float)
    i = cross[np.argmin(np.abs(t[cross]))]
    f = v[i] / (v[i] - v[i + 1])
    return P[i] + f * (P[i + 1] - P[i])


def _box(g, lo, hi):
    """Index slices of g covering the design-frame box lo..hi."""
    ax = design_axes(g)
    sl = []
    for k in range(3):
        a = ax[k]
        i0 = max(int(np.searchsorted(a, lo[k])) - 1, 0)
        i1 = min(int(np.searchsorted(a, hi[k])) + 1, len(a))
        sl.append(slice(i0, i1))
    return tuple(sl)


def seg_dist(X, Y, Z, a, b):
    ba = b - a
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / max(float(ba @ ba), 1e-12), 0.0, 1.0)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz)


def stroke(g, d, path, r, h, taper=True):
    """d with a ridge (h > 0, outward) or valley (h < 0) along the polyline,
    width r. taper: the stroke fades in and out over its ends, as a real fold
    does, rather than stopping square."""
    path = np.asarray(path, float)
    lo, hi = path.min(0) - r, path.max(0) + r
    sl = _box(g, lo, hi)
    X, Y, Z = g.X[sl], g.Y[sl], g.Z[sl]
    best = np.full(X.shape, np.inf, np.float32)
    along = np.zeros(X.shape, np.float32)
    seglen = np.linalg.norm(np.diff(path, axis=0), axis=1)
    cum = np.concatenate([[0.0], np.cumsum(seglen)])
    for i, (a, b) in enumerate(zip(path[:-1], path[1:])):
        dist = seg_dist(X, Y, Z, a, b)
        better = dist < best
        best = np.where(better, dist, best)
        ba = b - a
        t = np.clip(((X - a[0]) * ba[0] + (Y - a[1]) * ba[1] + (Z - a[2]) * ba[2]) / max(float(ba @ ba), 1e-12), 0, 1)
        along = np.where(better, (cum[i] + t * seglen[i]) / cum[-1], along)
    w = (1.0 - np.clip(best / r, 0.0, 1.0) ** 2) ** 3
    if taper:
        w = w * np.sin(np.pi * np.clip(along, 0.0, 1.0)) ** 0.6
    out = d.copy()
    out[sl] = d[sl] - h * w
    return out


BOLD = 2.2      # scales every fold's depth: at 1, half-millimetre folds didn't read at all
WIDE = 1.5      # ... and its width


def fold(g, d, path, r, h, out_dir, ridge=True, gap=None, max_jump=1.6):
    """A sculptor's fold: a valley, and beside it (on the side given by the
    path's left, if ridge) the bulge of cloth pushed up by it. Path points are
    first dropped onto the surface along out_dir (one direction, or one per
    point); a point whose surface is more than max_jump from where it was
    asked for has fallen into a gap (between arm and body) and is dropped."""
    out_dir = np.asarray(out_dir, float)
    r, h = r * WIDE, h * BOLD
    pts, dirs = [], []
    for i, p in enumerate(path):
        u = out_dir if out_dir.ndim == 1 else out_dir[i]
        q = on_surface(g, d, p, u)
        if np.linalg.norm(q - np.asarray(p, float)) <= max_jump:
            pts.append(q)
            dirs.append(u)
    if len(pts) < 2:
        return d
    out_dir = np.asarray(dirs) if out_dir.ndim == 2 else out_dir
    d = stroke(g, d, pts, r, -abs(h))
    if ridge:
        pts = np.asarray(pts)
        tang = np.gradient(pts, axis=0)
        n = out_dir if out_dir.ndim == 2 else np.repeat(out_dir[None], len(pts), 0)
        side = np.cross(n, tang)
        side /= np.maximum(np.linalg.norm(side, axis=1, keepdims=True), 1e-9)
        off = pts + side * (gap or r * 0.9)
        d = stroke(g, d, off, r * 0.9, abs(h) * 0.7)
    return d
